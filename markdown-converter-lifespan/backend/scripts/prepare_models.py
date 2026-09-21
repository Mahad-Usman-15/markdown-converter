"""Download and initialize CPU models required by PDF extraction."""
import json, sys
from importlib.metadata import version
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions,RapidOcrOptions
from docling.document_converter import DocumentConverter,PdfFormatOption
from docling.utils.model_downloader import download_models

def main():
    settings=Settings()
    if not settings.pdf_enabled:
        print("PDF support disabled; skipping model setup."); return
    settings.model_dir.mkdir(parents=True,exist_ok=True)
    marker=settings.model_dir/"ready.json"; marker.unlink(missing_ok=True)
    download_models(output_dir=settings.model_dir,progress=True,with_code_formula=False,
        with_picture_classifier=False,rapidocr_models=["onnxruntime:en"])
    options=PdfPipelineOptions(artifacts_path=settings.model_dir,do_ocr=True,do_table_structure=True)
    options.ocr_options=RapidOcrOptions(backend="onnxruntime",lang=["en"])
    options.enable_remote_services=False
    converter=DocumentConverter(allowed_formats=[InputFormat.PDF],format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=options)})
    converter.initialize_pipeline(InputFormat.PDF)
    marker.write_text(json.dumps({"docling":version("docling"),"ocr":"rapidocr-onnxruntime-en"}),encoding="utf-8")
    print("PDF pipeline is ready.")

if __name__=="__main__": main()
