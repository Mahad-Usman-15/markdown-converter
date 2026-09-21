# Markdown Converter

React and FastAPI in one modular monolith. FastAPI serves the compiled frontend and conversion endpoints from the same origin. Deploy as one native Python service on Render. Docker is not used.

## Features

- Upload a text or scanned PDF. Docling extracts document structure and RapidOCR reads scanned pages.
- Convert one public webpage URL to Markdown. This first release extracts that page only. It does not crawl links or access login protected pages.
- Paste plain text or upload a .txt file. Formatting runs in the browser, preserving words and existing Markdown while cleaning excess whitespace.
- Edit the result, preview it, then copy or download Markdown.

## Run locally

Use Python 3.12 and Node.js 22.12 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Windows and Linux, install CPU PyTorch first:

```sh
python -m pip install torch==2.14.0+cpu torchvision==0.29.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

Then:

```sh
python -m pip install -r backend/requirements.txt
python backend/scripts/prepare_models.py
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

Open http://localhost:8000. Model setup downloads a large collection of weights. Allow time, storage, memory, and outbound access to model hosts. For site/text development without PDF models, set `MC_PDF_ENABLED=false` before running the server.

Frontend development uses a Vite proxy to the API:

```sh
cd frontend
npm ci
npm run dev
```

Run `npm run build` after frontend changes. FastAPI serves the resulting `frontend/dist/` folder. This project includes its current build.

## Render

1. Download and extract the ZIP. Upload the contents of `markdown-converter/` into a repository you control. Keep `backend/`, `frontend/`, `render.yaml`, and the root README in place.
2. Create a native Python Web Service or use the Blueprint file. Review the service tier and billing before deploying. OCR and layout models need substantial memory; start with several GB and measure with your PDFs.
3. Use the build and start commands in `render.yaml`. The build installs CPU inference dependencies, then downloads and initializes PDF models. It expects the frontend to be prebuilt in `frontend/dist/`.
4. Run exactly one instance and one worker. Job state lives in process memory and active work is interrupted by restart. The worker limit is one active conversion at a time.

The GitHub account previously connected to this chat was not the user's account. This project archive makes no repository changes and performs no deployment.

## API

| Route | Behavior |
| --- | --- |
| `GET /api/health` | Readiness and PDF capability |
| `GET /api/config` | Frontend limits and supported capabilities |
| `POST /api/conversions` | Multipart PDF upload or webpage URL. Returns a job ID. |
| `GET /api/conversions/{job_id}` | Job stage, result, or sanitized error |
| `GET /api/docs` | API reference |

PDF defaults: 20 MiB, 50 pages. Webpage fetch: 3 MiB. Output: 2 MiB. Job state expires on service restart; there is no persistent job history or database. Keep one Render worker.

## Safety and privacy

Website URLs are checked against DNS, private/reserved IP addresses are blocked, connections are pinned to a resolved public IP, redirects are rechecked, and TLS hostname verification is retained. Only standard HTTP(S) ports are accepted. Upload files are deleted when work completes or fails. Results are kept in process memory. No text or PDF data is sent to an LLM. Model setup downloads weights from upstream model hosts.

## Tests

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
cd frontend
node tests/conversion.mjs
npm run build
```
