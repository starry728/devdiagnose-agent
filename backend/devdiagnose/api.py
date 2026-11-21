import hashlib
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import store
from .config import ROOT, model_ready
from .harness import POOL, execute
from .retrieval import retrieve
from .sample import QUESTION, SOURCES
from .schemas import DiagnosisCreate, SearchRequest, SourceCreate, WorkspaceCreate


@asynccontextmanager
async def lifespan(app):
    store.initialize()
    yield


app = FastAPI(title="DevDiagnose", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def require_workspace(workspace_id):
    if not store.workspace_exists(workspace_id):
        raise HTTPException(404, "工作区不存在")


def save_source(workspace_id, source):
    with store.db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM sources WHERE workspace_id=?", (workspace_id,)).fetchone()[
            0
        ]
        existing = conn.execute(
            "SELECT id FROM sources WHERE workspace_id=? AND path=? AND package=? AND version=?",
            (workspace_id, source.path, source.package, source.version),
        ).fetchone()
        if count >= 100 and not existing:
            raise HTTPException(400, "首版每个工作区最多100份资料")
        source_id = existing["id"] if existing else store.uid()
        conn.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(workspace_id,path,package,version) DO UPDATE SET content=excluded.content,kind=excluded.kind,sha256=excluded.sha256",
            (
                source_id,
                workspace_id,
                source.path,
                source.content,
                source.kind,
                source.package,
                source.version,
                hashlib.sha256(source.content.encode()).hexdigest(),
                store.now(),
            ),
        )
    return source_id


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_ready": model_ready(),
        "version": "0.1.0",
        "retrieval": "关键词基线（尚未接入向量检索）",
    }


@app.get("/api/workspaces")
def workspaces():
    with store.db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT w.*, (SELECT COUNT(*) FROM sources s WHERE s.workspace_id=w.id) source_count FROM workspaces w ORDER BY created_at DESC"
            )
        ]


@app.post("/api/workspaces", status_code=201)
def create_workspace(body: WorkspaceCreate):
    workspace_id = store.uid()
    with store.db() as conn:
        conn.execute("INSERT INTO workspaces VALUES (?,?,?)", (workspace_id, body.name, store.now()))
    return {"id": workspace_id, "name": body.name}


@app.get("/api/workspaces/{workspace_id}/sources")
def list_sources(workspace_id: str):
    require_workspace(workspace_id)
    return [{k: v for k, v in s.items() if k != "content"} for s in store.sources(workspace_id)]


@app.post("/api/workspaces/{workspace_id}/sources", status_code=201)
def create_source(workspace_id: str, body: SourceCreate):
    require_workspace(workspace_id)
    return {"id": save_source(workspace_id, body)}


@app.post("/api/workspaces/{workspace_id}/upload", status_code=201)
async def upload(workspace_id: str, files: list[UploadFile] = File(...)):
    require_workspace(workspace_id)
    if len(files) > 30:
        raise HTTPException(400, "每次最多上传30个文件")
    validated = []
    for file in files:
        raw = await file.read(200_001)
        if len(raw) > 200_000:
            raise HTTPException(400, f"{file.filename} 超过200KB限制")
        try:
            content = raw.decode("utf-8-sig")
            path = file.filename or "document.txt"
            suffix = Path(path).suffix.lower()
            kind = (
                "code"
                if suffix in {".py", ".ts", ".tsx", ".js", ".cpp", ".h"}
                else "log"
                if suffix == ".log"
                else "config"
                if suffix in {".toml", ".json", ".yaml", ".yml"} or Path(path).name == "requirements.txt"
                else "doc"
            )
            validated.append(SourceCreate(path=path, content=content, kind=kind))
        except Exception:
            raise HTTPException(400, "文件必须为支持的UTF-8文本，且不含敏感配置路径") from None
    return {"imported": len(validated), "ids": [save_source(workspace_id, s) for s in validated]}


@app.post("/api/workspaces/{workspace_id}/demo")
def demo(workspace_id: str):
    require_workspace(workspace_id)
    for item in SOURCES:
        save_source(workspace_id, SourceCreate(**item))
    return {"question": QUESTION, "imported": len(SOURCES), "synthetic": True}


@app.post("/api/workspaces/{workspace_id}/search")
def search(workspace_id: str, body: SearchRequest):
    require_workspace(workspace_id)
    return retrieve(store.sources(workspace_id), body.query, body.kind)


@app.post("/api/workspaces/{workspace_id}/tasks", status_code=202)
def create_task(workspace_id: str, body: DiagnosisCreate):
    require_workspace(workspace_id)
    if body.mode == "model" and not model_ready():
        raise HTTPException(409, "尚未配置 LLM_API_KEY 和 LLM_MODEL；请配置后重启服务")
    snapshot = store.sources(workspace_id)
    if not snapshot:
        raise HTTPException(400, "请先添加资料或加载演示案例")
    task_id, timestamp = store.uid(), store.now()
    with store.db() as conn:
        running = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('queued','running')").fetchone()[
            0
        ]
        if running >= 4:
            raise HTTPException(429, "当前任务较多，请等待已有任务完成")
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                task_id,
                workspace_id,
                body.question,
                body.mode,
                "queued",
                body.max_steps,
                json.dumps(snapshot, ensure_ascii=False),
                None,
                None,
                timestamp,
                timestamp,
            ),
        )
    POOL.submit(execute, task_id)
    return {"id": task_id}


@app.get("/api/workspaces/{workspace_id}/tasks")
def list_tasks(workspace_id: str):
    require_workspace(workspace_id)
    with store.db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT id,question,mode,status,created_at FROM tasks WHERE workspace_id=? ORDER BY created_at DESC LIMIT 40",
                (workspace_id,),
            )
        ]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    task = store.task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return task


@app.post("/api/tasks/{task_id}/resume", status_code=202)
def resume_task(task_id: str):
    task = get_task(task_id)
    if task["mode"] == "model" and not model_ready():
        raise HTTPException(409, "请先配置模型")
    with store.db() as conn:
        changed = conn.execute(
            "UPDATE tasks SET status='queued',error=NULL,updated_at=? WHERE id=? AND status IN ('failed','interrupted')",
            (store.now(), task_id),
        ).rowcount
    if not changed:
        raise HTTPException(409, "只有失败或中断的任务可以恢复")
    POOL.submit(execute, task_id)
    return {"id": task_id, "behavior": "本地模式从检查点恢复；模型模式基于原资料快照重新运行"}


@app.get("/api/tasks/{task_id}/report", response_class=PlainTextResponse)
def export_report(task_id: str):
    task = get_task(task_id)
    if not task["result"]:
        raise HTTPException(409, "报告尚未生成")
    return PlainTextResponse(
        task["result"]["markdown"],
        headers={"Content-Disposition": f'attachment; filename="diagnosis-{task_id[:8]}.md"'},
    )


dist = ROOT / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
