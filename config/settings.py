"""
配置管理模块
"""
import json
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any

from autogen_core.models import ModelFamily, ModelInfo
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent


class LLMConfig(BaseModel):
    """LLM 配置"""
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    api_base: str = Field(default_factory=lambda: os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))
    model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    model_info: Optional[ModelInfo] = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_INFO"))
    temperature: float = 0.0
    seed: int = 42

    @field_validator("model_info", mode="before")
    @classmethod
    def _parse_model_info(cls, value: Union[str, Dict[str, Any], None]) -> Optional[ModelInfo]:
        """
        解析环境变量提供的模型信息
        """
        if value in (None, "", b""):
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"OPENAI_MODEL_INFO 不是合法的 JSON: {exc}") from exc
        if isinstance(value, dict):
            family_value = value.get("family")
            if isinstance(family_value, str):
                # 优先通过枚举名称解析
                try:
                    value["family"] = ModelFamily[family_value]
                except KeyError:
                    # 再尝试直接通过枚举值解析
                    try:
                        value["family"] = ModelFamily(family_value)
                    except ValueError as exc:
                        raise ValueError(f"OPENAI_MODEL_INFO.family 无法解析为有效的 ModelFamily: {family_value}") from exc
            return value  # type: ignore[return-value]
        return value  # type: ignore[return-value]

    def get_effective_model_info(self) -> Optional[ModelInfo]:
        """
        获取生效的模型信息
        """
        if self.model_info is not None:
            return self.model_info

        # 针对常见的非官方模型名称提供内置模型信息
        if self.model in {"gemini-2.5-pro", "gemini-2.5-pro-preview"}:
            return {
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "family": ModelFamily.GEMINI_2_5_PRO,
                "structured_output": True,
                "multiple_system_messages": False,
            }

        # 为 gemini-2.5-flash 提供模型信息
        if self.model in {"gemini-2.5-flash", "gemini-2.5-flash-preview"}:
            return {
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "family": ModelFamily.GEMINI_2_5_FLASH,
                "structured_output": True,
                "multiple_system_messages": False,
            }

        return None


class PlaywrightConfig(BaseModel):
    """Playwright 配置"""
    headless: bool = Field(default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true")
    browser_timeout: int = Field(default_factory=lambda: int(os.getenv("BROWSER_TIMEOUT", "30000")))
    slow_mo: int = 100
    viewport_width: int = 1920
    viewport_height: int = 1080


class ProxyConfig(BaseModel):
    """代理配置"""
    http_proxy: Optional[str] = Field(default_factory=lambda: os.getenv("HTTP_PROXY"))
    https_proxy: Optional[str] = Field(default_factory=lambda: os.getenv("HTTPS_PROXY"))


class AppConfig(BaseModel):
    """应用配置"""
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    output_dir: Path = BASE_DIR / "output"
    screenshots_dir: Path = BASE_DIR / "output" / "screenshots"
    logs_dir: Path = BASE_DIR / "output" / "logs"
    reports_dir: Path = BASE_DIR / "output" / "reports"
    enable_autogen_patch: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_AUTOGEN_PATCH", "false").lower() == "true"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # 创建必要的目录
        self.output_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)


class Settings(BaseModel):
    """全局配置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    playwright: PlaywrightConfig = Field(default_factory=PlaywrightConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    app: AppConfig = Field(default_factory=AppConfig)


# 全局配置实例
settings = Settings()
