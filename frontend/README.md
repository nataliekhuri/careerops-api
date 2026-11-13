# CareerOps frontend

React + TypeScript single-page app for [CareerOps](../README.md). It talks to the FastAPI
backend through a client whose types are generated from the backend's OpenAPI document.

```bash
npm install
npm run dev        # http://localhost:5173 (expects the API on http://127.0.0.1:8000)
npm test           # Vitest + Testing Library + MSW
npm run build      # production build in dist/
```

- `src/api/` — `schema.d.ts` (generated, do not edit), `client.ts` (fetch client, auth
  header, error handling), `hooks.ts` (TanStack Query hooks)
- `src/auth/` — token storage, `AuthProvider`, route guards
- `src/components/` — design system
- `src/pages/` — screens (`assistant/` is the AI assistant)
- `src/test/` — MSW server, fixtures and render helpers

Regenerate API types after a backend change:

```bash
python ../scripts/export_openapi.py && npm run gen:api
```

Configuration: `VITE_API_URL` (see `.env.example`). In development it defaults to `/api`,
which Vite proxies to the backend.

## Demo screenshots

`../docs/screenshots/` holds screenshots of a local demo account (fake data in a
throwaway database schema), captured with headless Edge at 2x:
landing, dashboard, board (including a drag in progress), interview calendar,
applications, application detail, companies, settings and mobile views.
