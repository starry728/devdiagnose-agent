"""Inspectable lexical baseline. This is not vector or hybrid retrieval."""

import math
import re
from collections import Counter

from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version


def terms(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*|\d+(?:\.\d+)+", text.lower())
    words += [p for w in words for p in w.split("_") if len(p) > 2]
    for phrase in re.findall(r"[\u4e00-\u9fff]+", text):
        words.extend(phrase[i : i + 2] for i in range(len(phrase) - 1))
    return words


def requirements(sources: list[dict]) -> dict:
    result = {}
    for source in sources:
        if source["path"].split("/")[-1].lower() not in {"requirements.txt", "requirements.lock"}:
            continue
        for line in source["content"].splitlines():
            try:
                req = Requirement(line.strip())
                if req.specifier:
                    result[req.name.lower().replace("_", "-")] = req.specifier
            except InvalidRequirement:
                continue
    return result


def retrieve(sources: list[dict], query: str, kind="all", limit=6) -> dict:
    specs = requirements(sources)
    excluded, chunks = [], []
    for source in sources:
        if kind == "doc" and source["kind"] != "doc":
            continue
        if kind == "code" and source["kind"] not in {"code", "config", "log"}:
            continue
        spec = specs.get(source.get("package", "").lower().replace("_", "-"))
        version_status = "未核验版本"
        if spec and source.get("version"):
            try:
                if not spec.contains(Version(source["version"]), prereleases=True):
                    excluded.append(
                        {
                            "path": source["path"],
                            "version": source["version"],
                            "reason": f"与声明依赖 {spec} 不匹配",
                        }
                    )
                    continue
                version_status = f"符合声明依赖 {spec}（不代表已核验运行环境）"
            except InvalidVersion:
                pass
        lines = source["content"].splitlines()
        for start in range(0, len(lines), 24):
            text = "\n".join(lines[start : start + 32])
            chunks.append(
                {
                    "source_id": source["id"],
                    "path": source["path"],
                    "kind": source["kind"],
                    "package": source.get("package", ""),
                    "version": source.get("version", ""),
                    "version_status": version_status,
                    "sha256": source["sha256"],
                    "line_start": start + 1,
                    "line_end": min(start + 32, len(lines)),
                    "content": text,
                }
            )
    tokens = [Counter(terms(c["content"] + " " + c["path"])) for c in chunks]
    document_frequency = Counter(t for token in tokens for t in token)
    query_terms = set(terms(query))
    for chunk, token in zip(chunks, tokens):
        chunk["score"] = round(
            sum(
                (1 + math.log(token[t])) * math.log(1 + (len(chunks) + 1) / (document_frequency[t] + 1))
                for t in query_terms
                if token[t]
            ),
            4,
        )
    hits = sorted((c for c in chunks if c["score"] > 0), key=lambda c: c["score"], reverse=True)[:limit]
    for i, hit in enumerate(hits, 1):
        hit["evidence_id"] = f"E{i}"
    return {
        "evidence": hits,
        "excluded": excluded,
        "declared_dependencies": {k: str(v) for k, v in specs.items()},
        "method": "lexical-tfidf-baseline",
    }
