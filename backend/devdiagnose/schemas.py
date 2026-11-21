from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SourceCreate(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=200_000)
    kind: Literal["doc", "code", "log", "config"] = "doc"
    package: str = Field(default="", max_length=80)
    version: str = Field(default="", max_length=100)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        value = value.replace("\\", "/")
        path = PurePosixPath(value)
        forbidden = {".git", ".conda", ".venv", "node_modules", ".aws", ".ssh"}
        if path.is_absolute() or ":" in value or ".." in path.parts:
            raise ValueError("请使用项目内相对路径，不支持绝对路径或 ..")
        if any(p.lower() in forbidden or p.lower().startswith(".env") for p in path.parts):
            raise ValueError("不能导入环境目录、密钥配置或 Git 元数据")
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".log",
            ".toml",
            ".json",
            ".yaml",
            ".yml",
            ".ts",
            ".tsx",
            ".js",
            ".cpp",
            ".h",
        }:
            raise ValueError("暂仅支持代码、Markdown、文本日志及配置文件")
        return str(path)


class DiagnosisCreate(BaseModel):
    question: str = Field(min_length=3, max_length=12_000)
    mode: Literal["local", "model"] = "local"
    max_steps: int = Field(default=20, ge=6, le=40)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=12_000)
    kind: Literal["all", "doc", "code"] = "all"
