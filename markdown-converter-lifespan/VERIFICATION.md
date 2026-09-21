# Verification status

- Frontend: `npm run build` passed after connecting same-origin `/api` requests. `node tests/conversion.mjs` passed text, URL, multipart, job-result, expiry, and backend error checks. Vite's dev-server websocket emitted `EPERM` because listening on a port is restricted here; the conversion checks still passed.
- Python: `python -m compileall -q backend/app backend/scripts backend/tests` passed. Pytest was not run because package index connections are blocked in this workspace and dependencies could not be installed.
- PDF/OCR: model weights were not downloaded or processed here. The prepare script downloads Docling/RapidOCR weights and initializes the pipeline; the deployment build runs it. Startup requires the resulting readiness marker.
- Website: extraction and public IP/DNS validation are implemented. Live external fetches could not be tested because outbound DNS/network access is restricted here.
- Render: no deployment, memory sizing, or load check was performed.

Dependency folders, Python environments, and model weights are omitted from the archive. On a network-enabled machine, run `python -m pip install -r backend/requirements-dev.txt`, `python backend/scripts/prepare_models.py`, and `python -m pytest -q` before relying on PDF/OCR processing. The README gives local setup and single-instance Render instructions.
