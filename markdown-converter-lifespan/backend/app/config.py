from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MC_", extra="ignore")
    frontend_dir: Path = ROOT / "frontend" / "dist"
    model_dir: Path = ROOT / ".models"
    max_pdf_bytes: int = Field(20 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    max_pdf_pages: int = Field(50, ge=1, le=200)
    max_web_bytes: int = Field(3 * 1024 * 1024, ge=1024)
    max_result_bytes: int = Field(2 * 1024 * 1024, ge=1024)
    max_text_chars: int = 100_000
    max_txt_bytes: int = 1024 * 1024
    pdf_timeout_seconds: int = 600
    website_timeout_seconds: int = 90
    pdf_enabled: bool = True
    def public(self):
        return {"max_pdf_bytes": self.max_pdf_bytes, "max_pdf_pages": self.max_pdf_pages,
                "max_text_chars": self.max_text_chars, "max_txt_bytes": self.max_txt_bytes,
                "pdf_available": self.pdf_enabled}
