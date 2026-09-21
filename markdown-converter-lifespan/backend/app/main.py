import asyncio, json, secrets, shutil, tempfile, time, os, signal, subprocess, sys
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from app.config import Settings
from app.errors import ConversionError
from app.security import validate_url
from app.converters import website, pdf
from app.core.lifespan import lifespan

class BodyLimitExceeded(Exception): pass

class RequestBodyLimit:
    def __init__(self, app, limit): self.app=app; self.limit=limit
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope["method"]!="POST" or scope["path"]!="/api/conversions":
            return await self.app(scope,receive,send)
        seen=0
        async def limited_receive():
            nonlocal seen
            message=await receive(); seen+=len(message.get("body",b""))
            if seen>self.limit: raise BodyLimitExceeded()
            return message
        try: await self.app(scope,limited_receive,send)
        except BodyLimitExceeded:
            response=JSONResponse({"code":"input_too_large","message":"Upload exceeds the supported size."},413)
            await response(scope,receive,send)

def create_app(settings=None):
    settings=settings or Settings()
    app=FastAPI(title="Markdown Converter",version="1.0.0",docs_url="/api/docs",openapi_url="/api/openapi.json",lifespan=lifespan)
    jobs={}; lock=RLock(); submissions=[]; active=0; processes={}
    app.state.settings=settings
    app.state.processes=processes
    temp_root=None

    @app.middleware("http")
    async def secure_requests(request, call_next):
        if request.method=="POST" and request.url.path=="/api/conversions":
            origin=request.headers.get("origin")
            try: origin_ok=not origin or urlsplit(origin).netloc==request.headers.get("host")
            except ValueError: origin_ok=False
            if not origin_ok: return JSONResponse({"code":"forbidden_origin","message":"Submit conversions from this app."},403)
            try: size=int(request.headers.get("content-length","0"))
            except ValueError: size=settings.max_pdf_bytes+65537
            if size>settings.max_pdf_bytes+65536:
                return JSONResponse({"code":"input_too_large","message":"Upload exceeds the supported size."},413)
        response=await call_next(request)
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="no-referrer"
        response.headers["X-Frame-Options"]="DENY"
        if request.url.path.startswith("/api"): response.headers["Cache-Control"]="no-store"
        else: response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        return response

    app.add_middleware(RequestBodyLimit,limit=settings.max_pdf_bytes+65536)

    @app.get("/api/health")
    async def health(): return {"status":"ready","pdf_available":settings.pdf_enabled,"browser_fallback":False}
    @app.get("/api/config")
    async def config(): return settings.public()

    def run(jobid, folder, kind, name):
        nonlocal active
        started=time.monotonic()
        try:
            request={"kind":kind,"name":name,"settings":settings.model_dump(mode="json")}
            (folder/"request.json").write_text(json.dumps(request),encoding="utf-8")
            proc=subprocess.Popen([sys.executable,"-m","app.worker",str(folder)],cwd=Path(__file__).resolve().parents[1],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=(os.name=="posix"))
            with lock: processes[jobid]=proc
            timeout=settings.pdf_timeout_seconds if kind=="pdf" else settings.website_timeout_seconds
            while proc.poll() is None and time.monotonic()-started<timeout:
                stage=folder/"stage.txt"
                if stage.is_file() and stage.stat().st_size<100:
                    with lock: jobs[jobid].update(status="processing",stage=stage.read_text(encoding="utf-8"))
                time.sleep(.25)
            if proc.poll() is None:
                if os.name=="posix": os.killpg(proc.pid,signal.SIGKILL)
                else: proc.kill()
                proc.wait()
                with lock: jobs[jobid].update(status="failed",stage="failed",code="timeout",message="Conversion timed out. Try a smaller input.")
            else:
                result_path=folder/"result.json"
                if proc.returncode!=0 or not result_path.is_file() or result_path.stat().st_size>settings.max_result_bytes*2+65536:
                    raise ConversionError("worker_failed","Conversion stopped unexpectedly. Try a smaller input.")
                payload=json.loads(result_path.read_text(encoding="utf-8"))
                if payload.get("ok"):
                    result=payload["result"]
                    if not isinstance(result.get("markdown"),str) or not result["markdown"].strip(): raise ValueError()
                    with lock: jobs[jobid].update(status="completed",stage="complete",**result)
                else:
                    with lock: jobs[jobid].update(status="failed",stage="failed",code=payload.get("code","conversion_failed"),message=payload.get("message","Conversion failed."))
        except Exception:
            with lock: jobs[jobid].update(status="failed",stage="failed",code="conversion_failed",message="Conversion failed. Try another input.")
        finally:
            with lock: processes.pop(jobid,None)
            shutil.rmtree(folder,ignore_errors=True)
            with lock: active-=1

    @app.post("/api/conversions",status_code=202)
    async def submit(request:Request,background_tasks:BackgroundTasks):
        nonlocal active
        if not request.headers.get("content-type","").startswith("multipart/form-data"):
            return JSONResponse({"code":"invalid_content_type","message":"Submit form data."},415)
        with lock:
            now=time.monotonic()
            while submissions and now-submissions[0]>60: submissions.pop(0)
            if len(submissions)>=10: return JSONResponse({"code":"rate_limited","message":"Too many requests. Wait a minute."},429)
            if active>=1: return JSONResponse({"code":"busy","message":"The converter is busy. Try again shortly."},503)
            if len(jobs)>=32:
                for key in list(jobs):
                    if jobs[key].get("status") in ("completed","failed"): del jobs[key]
                    if len(jobs)<32: break
                if len(jobs)>=32: return JSONResponse({"code":"busy","message":"Temporary result storage is full."},503)
            active+=1; submissions.append(now)
        folder=Path(tempfile.mkdtemp(dir=temp_root))
        try:
            async with request.form(max_files=1,max_fields=2,max_part_size=8192) as form:
                if set(form.keys())-{"kind","file","url"} or len(form.multi_items())!=len(form): raise ConversionError("invalid_input","Submit one PDF or website URL.")
                kind=form.get("kind")
                if kind not in ("pdf","website"): raise ConversionError("invalid_kind","Choose PDF or Website.")
                if kind=="pdf":
                    if not settings.pdf_enabled: raise ConversionError("pdf_unavailable","PDF conversion is disabled.")
                    upload=form.get("file")
                    if not hasattr(upload,"read") or "url" in form: raise ConversionError("invalid_input","Choose one PDF.")
                    size=0; first=b""
                    with (folder/"input.pdf").open("wb") as out:
                        while chunk:=await upload.read(65536):
                            if not first:first=chunk[:1024]
                            size+=len(chunk)
                            if size>settings.max_pdf_bytes: raise ConversionError("input_too_large","PDF exceeds the upload limit.")
                            out.write(chunk)
                    if b"%PDF-" not in first: raise ConversionError("invalid_pdf","This file does not appear to be a PDF.")
                    name=(upload.filename or "Document.pdf").replace("\\","/").split("/")[-1][:200]
                else:
                    raw=form.get("url")
                    if not isinstance(raw,str) or "file" in form: raise ConversionError("invalid_input","Enter one public webpage URL.")
                    name=validate_url(raw.strip())[0]
            jobid=secrets.token_urlsafe(32)
            with lock: jobs[jobid]={"job_id":jobid,"status":"queued","stage":"queued"}
            background_tasks.add_task(run,jobid,folder,kind,name)
            return {"job_id":jobid}
        except ConversionError as e:
            with lock: active-=1
            shutil.rmtree(folder,ignore_errors=True)
            status=503 if e.code=="pdf_unavailable" else 413 if e.code=="input_too_large" else 422
            return JSONResponse({"code":e.code,"message":e.message},status)
        except Exception:
            with lock: active-=1
            shutil.rmtree(folder,ignore_errors=True)
            return JSONResponse({"code":"invalid_upload","message":"Submit one PDF or one webpage URL."},400)

    @app.get("/api/conversions/{jobid}")
    async def poll(jobid:str):
        with lock: job=jobs.get(jobid)
        if not job: return JSONResponse({"code":"job_not_found","message":"Conversion expired or was interrupted."},404)
        return job

    app.mount("/assets",StaticFiles(directory=settings.frontend_dir/"assets",check_dir=False),name="assets")
    @app.get("/favicon.svg")
    async def favicon(): return FileResponse(settings.frontend_dir/"favicon.svg",headers={"Cache-Control":"no-cache"})
    @app.get("/")
    async def index(): return FileResponse(settings.frontend_dir/"index.html",headers={"Cache-Control":"no-cache"})
    @app.exception_handler(HTTPException)
    async def http_error(request,exc): return JSONResponse({"code":"not_found","message":"Not found."},status_code=exc.status_code)
    return app

app=create_app()
