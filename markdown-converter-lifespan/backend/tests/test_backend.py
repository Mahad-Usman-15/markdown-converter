import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.errors import ConversionError
from app.security import validate_url,resolve
from app.converters import website

@pytest.fixture
def client():
    settings=Settings(pdf_enabled=False)
    with TestClient(create_app(settings)) as c: yield c

def test_api_and_frontend(client):
    assert client.get("/").status_code==200
    assert client.get("/api/health").json()["status"]=="ready"
    assert client.get("/api/config").json()["pdf_available"] is False
    assert client.get("/api/docs").status_code==200

def test_not_found(client):
    assert client.get("/missing").status_code==404
    assert client.get("/api/conversions/missing").status_code==404

def test_rejects_cross_origin(client):
    r=client.post("/api/conversions",headers={"origin":"https://attacker.example"},files={"kind":(None,"website")})
    assert r.status_code==403

@pytest.mark.parametrize("url",[
    "file:///etc/passwd","http://localhost","http://127.0.0.1","http://10.0.0.3",
    "https://user:pass@example.com","https://example.com:8443","http://example.com:0",
    "https://host.local/path","https://[::1]/"
])
def test_rejects_unsafe_urls(url):
    with pytest.raises(ConversionError): validate_url(url)

def test_accepts_and_normalizes_https():
    url,host,port=validate_url("https://Example.com/path#part")
    assert url=="https://example.com/path" and host=="example.com" and port==443

def test_article_and_links():
    source="""<html><head><title>Conversion Guide</title><base href='http://localhost'></head><body><nav>Home</nav><main><article><h1>Conversion Guide</h1><p>This practical guide explains how to prepare a readable document and preserve useful structure for Markdown conversion.</p><h2>Preparation</h2><p>Review the source before you start and make sure headings appear in the right order.</p><p>Read the <a href='/guide'>complete guide</a> for more examples.</p></article></main></body></html>"""
    from app.converters import html, trafilatura
    # Exercise the same public converter without making an external request.
    tree=html.fromstring(source,parser=html.HTMLParser(no_network=True))
    text=trafilatura.extract(tree,output_format="markdown",include_links=True,include_formatting=True)
    assert "Preparation" in text and "complete guide" in text

def test_pdf_rejected_when_disabled(client):
    r=client.post("/api/conversions",data={"kind":"pdf"},files={"file":("doc.pdf",b"%PDF-1.7")})
    assert r.status_code==503
