# Frontend

React, TypeScript, Vite, Tailwind CSS, CodeMirror, and react-markdown. This folder is served by the FastAPI backend from `dist/`.

```sh
npm ci
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Run `npm run build` after source changes and include the updated `dist/` in your upload. See the root README for local API setup and Render deployment.
