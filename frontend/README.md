# Pasal storefront

Run `npm ci` and `npm run dev` here after starting MongoDB, the FastAPI
recommendation service and Express backend. Open http://127.0.0.1:5173.
Vite proxies `/api` to the localhost backend on port 3000; the recommender
listens on port 8000. See the backend and recommendation service READMEs
for secrets and model artifact requirements. Never put server secrets in Vite
client variables. `npm test` runs UI checks; `npm run build` checks TypeScript
and creates the production bundle. Production hosting still requires a same-origin
API reverse proxy, HTTPS and deployment configuration.

The interface supports catalogue ID search/category filtering, item details,
accounts, optional personalization, history clearing, wishlists and a research
basket. Names, illustrations and availability are explicitly historical/anonymized;
there are no fabricated prices, checkout or actual orders. Recommendation reasons
currently come from the local strategy trace, not live generated text.

Browser checks on October 12, 2026 used the real local stack: item 16 search,
its detail dialog, guest basket-to-login transition, desktop layout and a
390 x 844 mobile viewport without horizontal overflow. Authentication and consent
were tested through the backend HTTP suite; the browser checks did not create
an account. Independent usability and accessibility audits remain outstanding.
