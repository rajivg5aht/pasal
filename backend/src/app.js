import express from 'express';
import session from 'express-session';
import helmet from 'helmet';
import {rateLimit} from 'express-rate-limit';
import {randomBytes, scrypt as rawScrypt, timingSafeEqual} from 'node:crypto';
import {promisify} from 'node:util';
import {z} from 'zod';

const scrypt = promisify(rawScrypt);
const credentials = z.object({email: z.email().max(254).transform(v => v.toLowerCase()), password: z.string().min(12).max(128)}).strict();
const signup = credentials.extend({name: z.string().trim().min(1).max(80)});
const privacy = z.object({personalization: z.boolean(), selectedCategories: z.array(z.string().regex(/^\d+$/).max(12)).max(30)}).strict();
const item = z.object({itemid: z.number().int().nonnegative()}).strict();
const publicUser = u => ({id: String(u._id), name: u.name, email: u.email,
  personalization: u.personalization, selectedCategories: u.selectedCategories, wishlist: u.wishlist, cart: u.cart});
const saveSession = req => new Promise((resolve, reject) => req.session.save(e => e ? reject(e) : resolve()));
const regenerate = req => new Promise((resolve, reject) => req.session.regenerate(e => e ? reject(e) : resolve()));

async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  return `${salt}:${(await scrypt(password, salt, 64)).toString('hex')}`;
}
async function verifyPassword(password, hash) {
  const [salt, stored] = hash.split(':');
  const actual = await scrypt(password, salt, 64);
  const expected = Buffer.from(stored, 'hex');
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

export function createApp({repository, store, sessionSecret, recommend, origins = ['http://127.0.0.1:5173', 'http://localhost:5173'], production = false}) {
  if (!sessionSecret || sessionSecret.length < 32 || !store) throw new Error('Persistent session store and strong secret required');
  const app = express();
  app.disable('x-powered-by');
  app.use(helmet());
  app.use(express.json({limit: '32kb'}));
  app.use(rateLimit({windowMs: 60_000, limit: 120, standardHeaders: 'draft-8', legacyHeaders: false}));
  app.use((req, res, next) => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method) && !origins.includes(req.get('Origin'))) return res.status(403).json({error: 'Untrusted request origin'});
    next();
  });
  app.use(session({name: 'pasal.sid', secret: sessionSecret, store, resave: false, saveUninitialized: false,
    cookie: {httpOnly: true, sameSite: 'lax', secure: production, maxAge: 24*60*60*1000}}));
  const authLimit = rateLimit({windowMs: 15*60_000, limit: 20, standardHeaders: 'draft-8', legacyHeaders: false});
  async function requireUser(req, res, next) {
    const user = req.session.userId && await repository.getUser(req.session.userId);
    if (!user) return res.status(401).json({error: 'Sign in to continue'});
    req.user = user; next();
  }
  app.get('/api/health', (req, res) => res.json({status: 'ready'}));
  app.post('/api/auth/register', authLimit, async (req, res) => {
    const input = signup.parse(req.body);
    const user = await repository.createUser({email: input.email, name: input.name, passwordHash: await hashPassword(input.password)});
    await regenerate(req); req.session.userId = String(user._id); await saveSession(req);
    res.status(201).json({user: publicUser(user)});
  });
  app.post('/api/auth/login', authLimit, async (req, res) => {
    const input = credentials.parse(req.body);
    const user = await repository.findByEmail(input.email);
    if (!user || !await verifyPassword(input.password, user.passwordHash)) return res.status(401).json({error: 'Invalid email or password'});
    await regenerate(req); req.session.userId = String(user._id); await saveSession(req);
    res.json({user: publicUser(user)});
  });
  app.post('/api/auth/logout', (req, res, next) => req.session.destroy(error => {
    if (error) return next(error); res.clearCookie('pasal.sid', {path: '/'}).status(204).end();
  }));
  app.get('/api/me', requireUser, (req, res) => res.json({user: publicUser(req.user)}));
  app.get('/api/products', async (req, res) => {
    const input = z.object({after: z.coerce.number().int().min(-1).default(-1), category: z.string().regex(/^\d+$/).optional(), query: z.string().trim().max(40).optional()}).strict().parse(req.query);
    const products = await repository.products(input);
    res.json({products, nextCursor: products.length === 24 ? products.at(-1)._id : null});
  });
  app.get('/api/categories', async (req, res) => res.json({categories: (await repository.categories()).filter(Boolean).sort((a,b) => Number(a)-Number(b))}));
  app.get('/api/products/:id', async (req, res) => {
    const id = z.coerce.number().int().nonnegative().parse(req.params.id);
    const product = await repository.product(id);
    if (!product) return res.status(404).json({error: 'Item unavailable'});
    res.json({product});
  });
  app.put('/api/privacy', requireUser, async (req, res) => {
    const input = privacy.parse(req.body);
    const user = await repository.setPrivacy(req.user._id, input.personalization, input.selectedCategories);
    res.json({user: publicUser(user)});
  });
  app.delete('/api/history', requireUser, async (req, res) => res.json({user: publicUser(await repository.resetProfile(req.user._id))}));
  app.post('/api/events', requireUser, async (req, res) => {
    const input = item.extend({type: z.enum(['view', 'addtocart'])}).parse(req.body);
    if (!await repository.product(input.itemid)) return res.status(404).json({error: 'Item unavailable'});
    const updated = await repository.recordEvent(req.user._id, input.itemid);
    if (!updated) return res.status(409).json({error: 'Personalization disabled or history capacity reached'});
    res.status(204).end();
  });
  for (const list of ['wishlist', 'cart']) for (const [method, add] of [['post', true], ['delete', false]]) {
    app[method](`/api/${list}`, requireUser, async (req, res) => {
      const {itemid} = item.parse(req.body);
      if (add && !await repository.product(itemid)) return res.status(404).json({error: 'Item unavailable'});
      const user = await repository.changeList(req.user._id, list, itemid, add);
      if (!user) return res.status(409).json({error: 'List capacity reached'});
      res.json({user: publicUser(user)});
    });
  }
  app.get('/api/recommendations', async (req, res) => {
    const user = req.session.userId ? await repository.getUser(req.session.userId) : null;
    const active = Boolean(user?.personalization);
    const profile = {personalization: active, event_count: active ? user.eventCount : 0,
      recent_items: active ? user.recentItems : [], seen_items: active ? user.seenItems : [],
      selected_categories: active ? user.selectedCategories : [], k: 10};
    const result = await recommend(profile);
    const products = await repository.productsByIds(result.items.map(i => i.itemid));
    const lookup = new Map(products.map(p => [p._id, p]));
    res.json({...result, items: result.items.filter(i => lookup.has(i.itemid)).map(i => ({...i, product: lookup.get(i.itemid)}))});
  });
  app.use((error, req, res, next) => {
    if (error instanceof z.ZodError) return res.status(400).json({error: 'Invalid request fields'});
    if (error?.code === 11000) return res.status(409).json({error: 'Account already exists'});
    if (error?.type === 'entity.too.large') return res.status(413).json({error: 'Request too large'});
    if (error?.type === 'entity.parse.failed') return res.status(400).json({error: 'Invalid JSON'});
    res.status(503).json({error: 'Service temporarily unavailable'});
  });
  return app;
}
