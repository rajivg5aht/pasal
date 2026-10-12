import test from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import session from 'express-session';
import {createApp} from '../src/app.js';

function fixture() {
  const users = new Map();
  const product = {_id: 7, title: 'Catalogue item 7', category: '9', available: true};
  let lastProfile;
  const repository = {
    createUser: async data => {const user = {...data, _id: String(users.size+1), personalization: false, selectedCategories: [], eventCount: 0, recentItems: [], seenItems: [], wishlist: [], cart: []}; users.set(user._id, user); return user;},
    findByEmail: async email => [...users.values()].find(u => u.email === email),
    getUser: async id => users.get(String(id)), product: async id => id === 7 ? product : null,
    productsByIds: async ids => ids.includes(7) ? [product] : [],
    setPrivacy: async (id, enabled, selectedCategories) => {const u = users.get(id); Object.assign(u, {personalization: enabled, selectedCategories: enabled ? selectedCategories : []}); if (!enabled) Object.assign(u, {eventCount: 0, recentItems: [], seenItems: []}); return u;},
    recordEvent: async (id, itemid) => {const u = users.get(id); if (!u.personalization) return null; u.eventCount++; u.recentItems=[itemid]; u.seenItems=[itemid]; return u;}
  };
  const app = createApp({repository, store: new session.MemoryStore(), sessionSecret: 'test-secret-with-more-than-thirty-two-characters',
    recommend: async profile => {lastProfile=profile; return {items: [{itemid:7, reason:'fixture'}], genai_used:false};}});
  return {app, users, profile: () => lastProfile};
}
const origin = 'http://127.0.0.1:5173';

test('requires trusted origin and authenticated session for private changes', async () => {
  const {app}=fixture();
  assert.equal((await request(app).put('/api/privacy').send({})).status,403);
  assert.equal((await request(app).put('/api/privacy').set('Origin',origin).send({})).status,401);
  assert.equal((await request(app).post('/api/auth/register').set('Origin',origin).send({email:'bad',password:'short',name:'Test'})).status,400);
});

test('registration, consent, recommendation profile and opt-out', async () => {
  const f=fixture(); const agent=request.agent(f.app);
  const signup=await agent.post('/api/auth/register').set('Origin',origin).send({email:'student@example.test',password:'safe-test-password',name:'Student'});
  assert.equal(signup.status,201); assert.equal(signup.body.user.passwordHash,undefined);
  assert.match(signup.headers['set-cookie'][0],/HttpOnly/);
  const event=() => agent.post('/api/events').set('Origin',origin).send({itemid:7,type:'view'});
  assert.equal((await event()).status,409);
  await agent.put('/api/privacy').set('Origin',origin).send({personalization:true,selectedCategories:['9']}).expect(200);
  await event().expect(204);
  await agent.get('/api/recommendations').expect(200);
  assert.equal(f.profile().event_count,1);
  await agent.put('/api/privacy').set('Origin',origin).send({personalization:false,selectedCategories:[]}).expect(200);
  await agent.get('/api/recommendations').expect(200);
  assert.equal(f.profile().event_count,0); assert.deepEqual(f.profile().seen_items,[]);
  assert.equal(f.users.get('1').eventCount,0);
  await agent.post('/api/auth/logout').set('Origin',origin).expect(204);
  await agent.get('/api/me').expect(401);
});

test('login checks password and protects stored password hash', async () => {
  const f=fixture(); const agent=request.agent(f.app);
  await agent.post('/api/auth/register').set('Origin',origin).send({email:'student@example.test',password:'safe-test-password',name:'Student'});
  assert.notEqual(f.users.get('1').passwordHash,'safe-test-password');
  await agent.post('/api/auth/logout').set('Origin',origin);
  await agent.post('/api/auth/login').set('Origin',origin).send({email:'student@example.test',password:'wrong-password-here'}).expect(401);
  await agent.post('/api/auth/login').set('Origin',origin).send({email:'student@example.test',password:'safe-test-password'}).expect(200);
});
