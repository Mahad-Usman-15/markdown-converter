"""Isolated, time-limited conversion subprocess."""
import json, os, sys
from pathlib import Path
from app.config import Settings
from app.errors import ConversionError
from app.converters import pdf, website

def main(folder):
    folder=Path(folder)
    task=json.loads((folder/"request.json").read_text(encoding="utf-8"))
    settings=Settings.model_validate(task["settings"])
    def progress(stage):
        tmp=folder/"stage.tmp"; tmp.write_text(stage,encoding="utf-8"); os.replace(tmp,folder/"stage.txt")
    try:
        result=pdf(folder/"input.pdf",task["name"],settings,progress) if task["kind"]=="pdf" else website(task["name"],settings)
        if len(result["markdown"].encode("utf-8"))>settings.max_result_bytes:
            raise ConversionError("result_too_large","Extracted Markdown is too large. Try a smaller input.")
        payload={"ok":True,"result":result}
    except ConversionError as e: payload={"ok":False,"code":e.code,"message":e.message}
    except Exception: payload={"ok":False,"code":"conversion_failed","message":"Conversion failed. Try another input."}
    temp=folder/"result.tmp"; temp.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8"); os.replace(temp,folder/"result.json")

if __name__=="__main__": main(sys.argv[1])
