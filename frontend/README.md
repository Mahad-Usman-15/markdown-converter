# Markdown Converter frontend

React + TypeScript + Vite + Tailwind frontend based on Design.md. Intended hosting: Vercel. Conversion backend: FastAPI on Render, using BackgroundTasks.

## Run

Requires Node.js 22.12+ or a compatible newer LTS release.

```sh
npm ci
npm run dev
```

For production, run `npm run build`. Vercel uses `vercel.json` to build and serve `dist`.

## Implemented

- PDF selection, signature check, drag/drop, removal, and configured size validation.
- Public URL input and syntax validation.
- Plain text and TXT upload, conservative whitespace normalization in the browser.
- Keyboard-accessible input tabs and preserved drafts.
- Asynchronous API submission and polling with bounded retry, OCR stage, empty-output handling, interruption handling, and review notices.
- CodeMirror editing, live GitHub-flavored Markdown preview, copy, and MD download.
- Responsive result panes, accessible labels, and reduced motion.

Plain-text conversion preserves existing Markdown and source words. It does not infer headings from ambiguous unstructured text. Preview does not load remote images; it shows their alt text, while the Markdown export retains image syntax.

## Connect the backend

Set `VITE_API_BASE_URL` to the Render API origin in Vercel and redeploy. For local development, copy `.env.example` to `.env.local` and set the same value. This is a public origin, not a secret. Configure Render CORS to allow the Vercel origin.

Without this setting, plain text works locally. PDF and website inputs visibly explain that their service is not connected. No fake PDF or website conversions are returned. No backend, API credentials, or hosted deployment is included in this delivery.

### Expected API contract

`GET /config`, response:

```json
{"max_pdf_bytes":20971520,"max_txt_bytes":1048576,"max_text_chars":100000}
```

These are example backend values, not hardcoded frontend promises. The backend must enforce its own limits, validate uploads, and block private-network URL requests and redirects. Loading config must succeed before PDF selection is enabled on a configured installation.

`POST /conversions` accepts multipart form data:

- `kind`: `pdf` or `website`
- `file`: PDF bytes when kind is pdf
- `url`: webpage URL when kind is website

Return HTTP 202:

```json
{"job_id":"opaque-unguessable-id"}
```

`GET /conversions/{job_id}` returns one of:

```json
{"status":"processing","stage":"ocr"}
```

```json
{"status":"completed","markdown":"# Example\n\nContent","title":"Example","warnings":[]}
```

```json
{"status":"failed","message":"The webpage could not be read."}
```

Return 404 or 410 for interrupted/expired jobs. The frontend polls every 1.5 seconds, stops after 15 minutes, and tolerates up to four consecutive transient polling failures. Job data is held in browser memory only; refreshing clears the session. In-process FastAPI jobs can be lost on restart. Use unguessable job IDs and backend abuse controls before public launch.

## Deployment

1. Put this folder in your own repository or import it into an existing project.
2. Create a Vercel project using Vite, with this folder as the root.
3. Set `VITE_API_BASE_URL` when the Render backend is ready.
4. Build command: `npm run build`. Output directory: `dist`.

No Vercel deployment, Render resource, or repository commit has been made by this delivery.

## Verification

`npm run build` checks TypeScript and creates the production bundle.

`node tests/conversion.mjs` checks text preservation, URL validation, submission, successful output, expired jobs, empty extraction, and service errors using controlled API responses. These tests use mocks, not a live Render service.

Browser visual verification and live PDF/OCR conversions remain deployment checks. The production bundle includes a relatively large editor dependency; code splitting can be introduced later without changing the interaction model.

## File locations

The delivered ZIP contains source, configuration, this guide, the design reference, tests, and a prebuilt `dist` directory. Dependencies are installed locally for verification but are not included; restore them with `npm ci`.

The separate file inventory enumerates all project files, including temporary installed dependencies and build outputs, and identifies which files are packaged. This is a source handoff, not a claim that files have been written to your computer or committed to your repository.
