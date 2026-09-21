from pathlib import Path
from urllib.parse import urljoin
import ipaddress, time, zlib
import certifi, urllib3
from lxml import html
import trafilatura
from app.errors import ConversionError
from app.security import validate_url, resolve

def fetch(url, limit):
    for _ in range(6):
        url, host, port = validate_url(url)
        address = resolve(host, port)
        target = urlsplit_path(url)
        timeout = urllib3.Timeout(connect=5, read=10)
        opts = dict(host=address, port=port, timeout=timeout, maxsize=1)
        pool = urllib3.HTTPSConnectionPool(**opts, server_hostname=host, assert_hostname=host,
            cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()) if url.startswith("https:") else urllib3.HTTPConnectionPool(**opts)
        res = None
        try:
            res = pool.urlopen("GET", target, headers={"Host":host,"User-Agent":"MarkdownConverter/1.0",
                "Accept":"text/html,application/xhtml+xml","Accept-Encoding":"gzip, deflate"},
                preload_content=False, redirect=False, retries=False, assert_same_host=False)
            if res.status in (301,302,303,307,308):
                loc=res.headers.get("Location")
                if not loc: raise ConversionError("bad_redirect","Invalid website redirect.")
                url=urljoin(url,loc); continue
            if res.status != 200: raise ConversionError("website_unavailable","The webpage could not be read.")
            enc=res.headers.get("Content-Encoding","identity").lower()
            if enc not in ("identity","gzip","deflate"): raise ConversionError("unsupported_encoding","Unsupported website encoding.")
            dec=zlib.decompressobj(16+zlib.MAX_WBITS if enc=="gzip" else zlib.MAX_WBITS) if enc!="identity" else None
            data=bytearray(); wire=0
            for chunk in res.stream(32768, decode_content=False):
                wire+=len(chunk)
                if wire>limit: raise ConversionError("too_large","The webpage exceeds the size limit.")
                data.extend(dec.decompress(chunk,limit+1-len(data)) if dec else chunk)
                if len(data)>limit: raise ConversionError("too_large","The webpage exceeds the size limit.")
            if dec and not dec.eof: raise ConversionError("invalid_response","The webpage response was incomplete.")
            return url,bytes(data),res.headers.get("Content-Type","")
        except (urllib3.exceptions.HTTPError,OSError,zlib.error):
            raise ConversionError("fetch_failed","Could not securely fetch the webpage.") from None
        finally:
            if res: res.close()
            pool.close()
    raise ConversionError("redirect_limit","The webpage redirected too many times.")

def urlsplit_path(url):
    from urllib.parse import urlsplit
    p=urlsplit(url); return p.path+("?"+p.query if p.query else "")

def website(url, settings):
    final,body,mime=fetch(url,settings.max_web_bytes)
    if mime.split(";",1)[0].lower() not in ("text/html","application/xhtml+xml"):
        raise ConversionError("not_html","That URL does not point to an HTML webpage.")
    tree=html.fromstring(body,parser=html.HTMLParser(no_network=True,recover=True))
    for b in tree.xpath("//base"): b.getparent().remove(b)
    for e in tree.xpath("//*[@href]"): e.set("href",urljoin(final,e.get("href","")))
    title=" ".join(tree.xpath("//title/text()"))[:200].strip() or "Webpage"
    md=trafilatura.extract(tree,url=final,output_format="markdown",include_formatting=True,include_links=True,include_tables=True,include_images=False,include_comments=False)
    if not md: raise ConversionError("empty_content","No readable main content was found.")
    warnings=["Images are not exported. Review any image dependent content."] if tree.xpath("//img") else []
    return {"markdown":md.strip()+"\n","title":title,"warnings":warnings}

def pdf(path,name,settings,progress):
    from pypdf import PdfReader
    try:
        reader=PdfReader(path)
        if reader.is_encrypted: raise ConversionError("encrypted_pdf","Unlock this PDF before uploading it.")
        if not reader.pages: raise ConversionError("empty_pdf","This PDF has no pages.")
        if len(reader.pages)>settings.max_pdf_pages: raise ConversionError("too_many_pages",f"The PDF exceeds {settings.max_pdf_pages} pages.")
        scanned=any(len((p.extract_text() or "").strip())<20 for p in reader.pages)
    except ConversionError: raise
    except Exception: raise ConversionError("invalid_pdf","This PDF could not be read.") from None
    progress("ocr" if scanned else "extracting")
    from docling.datamodel.base_models import InputFormat,ConversionStatus
    from docling.datamodel.pipeline_options import PdfPipelineOptions,RapidOcrOptions
    from docling.document_converter import DocumentConverter,PdfFormatOption
    opts=PdfPipelineOptions(artifacts_path=settings.model_dir,do_ocr=True,do_table_structure=True)
    opts.ocr_options=RapidOcrOptions(backend="onnxruntime",lang=["en"])
    opts.enable_remote_services=False
    converter=DocumentConverter(allowed_formats=[InputFormat.PDF],format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=opts)})
    result=converter.convert(path,max_num_pages=settings.max_pdf_pages,max_file_size=settings.max_pdf_bytes,raises_on_error=False)
    if result.status not in (ConversionStatus.SUCCESS,ConversionStatus.PARTIAL_SUCCESS):
        raise ConversionError("pdf_failed","This PDF could not be converted.")
    md=result.document.export_to_markdown().strip()
    if not md: raise ConversionError("empty_content","No readable content was found in this PDF.")
    warnings=[]
    if scanned: warnings.append("OCR was used. Review names, numbers, and tables against the source PDF.")
    if result.errors or result.status==ConversionStatus.PARTIAL_SUCCESS: warnings.append("Some content could not be extracted.")
    return {"markdown":md+"\n","title":name,"warnings":warnings}
