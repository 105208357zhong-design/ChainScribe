"""
ChainScribe — 统一 API 服务
单一 FastAPI 入口，通过 Orchestrator 驱动所有 Agent 工作流
"""
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agent.orchestrator import ChainScribeOrchestrator, WorkflowType


# ─── 全局 Orchestrator ──────────────────────────────────

orchestrator = ChainScribeOrchestrator()


# ─── 请求模型 ────────────────────────────────────────────

class PublishRequest(BaseModel):
    topic: str = "Web3 创作者经济"
    content_type: str = "research_report"
    unlock_price: float = 0.01
    max_words: int = 3000

class NarrativeRequest(BaseModel):
    token_id: str = "1"
    title: str = "链上觉醒"
    genre: str = "sci-fi"
    total_chapters: int = 5
    interval_seconds: float = 0.5

class DAORequest(BaseModel):
    title: str = "DeFi 安全报告"
    goal: str = ""

class IPDerivativeRequest(BaseModel):
    ip_name: str = "CyberDragon"
    ip_style: str = "cyberpunk"
    derivative_types: list[str] = ["story", "script", "merch"]

class FullPipelineRequest(BaseModel):
    topic: str = "Web3 创作者经济"
    genre: str = "sci-fi"
    ip_style: str = "cyberpunk"

class UnlockRequest(BaseModel):
    token_id: int
    reader_address: str
    price_eth: float = 0.01


# ─── WebSocket 管理 ──────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, msg: dict):
        for ws in self.active:
            try:
                await ws.send_json(msg)
            except Exception:
                pass

ws_manager = ConnectionManager()


# ─── 进度回调 ────────────────────────────────────────────

async def ws_progress_callback(plan, step):
    """将执行进度广播到 WebSocket 客户端"""
    await ws_manager.broadcast({
        "type": "step_update",
        "step_name": getattr(step, 'name', str(step)),
        "step_status": step.status.value if hasattr(step, 'status') and hasattr(step.status, 'value') else str(getattr(step, 'status', 'unknown')),
        "retry_count": getattr(step, 'retry_count', 0),
        "self_corrections": len(getattr(step, 'self_correction_notes', [])),
    })


# ─── App ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 ChainScribe API 启动 — 统一编排器就绪")
    yield
    print("👋 ChainScribe API 关闭")

app = FastAPI(
    title="ChainScribe API",
    description="AI 自主链上出版与动态 NFT 平台 — 统一编排器",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 根路由 ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "ChainScribe",
        "version": "2.0.0",
        "description": "AI 自主链上出版与动态 NFT 平台",
        "workflows": {
            "publish": "POST /api/publish — 链上出版 Agent",
            "narrative": "POST /api/narrative — 动态 NFT 叙事引擎",
            "dao": "POST /api/dao — 创作者 DAO 协作",
            "ip_derivative": "POST /api/ip-derivative — IP 衍生内容",
            "full_pipeline": "POST /api/pipeline — 完整流水线",
        },
        "ws": "ws://localhost:8000/ws — 实时进度推送",
        "dashboard": "GET /dashboard — Agent 监控面板",
    }


# ─── 链上出版 ────────────────────────────────────────────

@app.post("/api/publish")
async def start_publishing(req: PublishRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]

    async def run():
        result = await orchestrator.execute(
            workflow=WorkflowType.PUBLISH,
            on_progress=ws_progress_callback,
            topic=req.topic,
            content_type=req.content_type,
            unlock_price=req.unlock_price,
            max_words=req.max_words,
        )
        await ws_manager.broadcast({
            "type": "workflow_complete",
            "task_id": task_id,
            "success": result.success,
            "time": result.total_time,
        })

    bg.add_task(run)
    return {"task_id": task_id, "workflow": "publish", "topic": req.topic}


# ─── 动态叙事 ────────────────────────────────────────────

@app.post("/api/narrative")
async def start_narrative(req: NarrativeRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]

    async def run():
        result = await orchestrator.execute(
            workflow=WorkflowType.NARRATIVE,
            on_progress=ws_progress_callback,
            token_id=req.token_id,
            title=req.title,
            genre=req.genre,
            total_chapters=req.total_chapters,
            interval_seconds=req.interval_seconds,
        )
        await ws_manager.broadcast({
            "type": "workflow_complete",
            "task_id": task_id,
            "success": result.success,
            "time": result.total_time,
        })

    bg.add_task(run)
    return {"task_id": task_id, "workflow": "narrative", "token_id": req.token_id}


# ─── DAO 协作 ────────────────────────────────────────────

@app.post("/api/dao")
async def start_dao(req: DAORequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    goal = req.goal or f"协作完成 {req.title} 的调研、撰写、设计、发布与推广"

    async def run():
        result = await orchestrator.execute(
            workflow=WorkflowType.DAO,
            on_progress=ws_progress_callback,
            title=req.title,
            goal=goal,
        )
        await ws_manager.broadcast({
            "type": "workflow_complete",
            "task_id": task_id,
            "success": result.success,
            "time": result.total_time,
        })

    bg.add_task(run)
    return {"task_id": task_id, "workflow": "dao", "title": req.title}


# ─── IP 衍生 ─────────────────────────────────────────────

@app.post("/api/ip-derivative")
async def start_ip_derivative(req: IPDerivativeRequest, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]

    async def run():
        result = await orchestrator.execute(
            workflow=WorkflowType.IP_DERIVATIVE,
            on_progress=ws_progress_callback,
            ip_name=req.ip_name,
            ip_style=req.ip_style,
            derivative_types=req.derivative_types,
        )
        await ws_manager.broadcast({
            "type": "workflow_complete",
            "task_id": task_id,
            "success": result.success,
            "time": result.total_time,
        })

    bg.add_task(run)
    return {"task_id": task_id, "workflow": "ip_derivative", "ip_name": req.ip_name}


# ─── 完整流水线 ──────────────────────────────────────────

@app.post("/api/pipeline")
async def start_full_pipeline(req: FullPipelineRequest, bg: BackgroundTasks):
    """完整流水线：出版 → 叙事 → DAO → 衍生"""
    task_id = str(uuid.uuid4())[:8]

    async def run():
        result = await orchestrator.execute(
            workflow=WorkflowType.FULL_PIPELINE,
            on_progress=ws_progress_callback,
            topic=req.topic,
            genre=req.genre,
            ip_style=req.ip_style,
        )
        await ws_manager.broadcast({
            "type": "workflow_complete",
            "task_id": task_id,
            "success": result.success,
            "time": result.total_time,
        })

    bg.add_task(run)
    return {"task_id": task_id, "workflow": "full_pipeline", "topic": req.topic}


# ─── 内容交互 ────────────────────────────────────────────

@app.post("/api/unlock")
async def unlock_content(req: UnlockRequest):
    return await orchestrator.blockchain.unlock_content(
        token_id=req.token_id,
        reader_address=req.reader_address,
        price_eth=req.price_eth,
    )


@app.get("/api/content/{token_id}")
async def get_content_meta(token_id: int):
    return await orchestrator.blockchain.get_content_meta(token_id)


# ─── 工作流状态 ──────────────────────────────────────────

@app.get("/api/workflows")
async def list_workflows():
    return orchestrator.list_workflows()


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    r = orchestrator.get_workflow(workflow_id)
    if not r:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": r.workflow_id,
        "type": r.workflow_type.value,
        "success": r.success,
        "time": r.total_time,
        "steps": f"{r.steps_completed}/{r.steps_total}",
        "errors": r.errors,
    }


# ─── WebSocket ───────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                cmd = json.loads(data)
                if cmd.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# ─── Dashboard ───────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChainScribe — Agent 监控面板</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'SF Mono', 'Fira Code', monospace; background: #0a0e27; color: #e0e6ff; min-height: 100vh; }
.header { background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 20px 40px; display: flex; align-items: center; justify-content: space-between; }
.header h1 { font-size: 24px; font-weight: 700; }
.header .badge { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; }
.container { max-width: 1400px; margin: 0 auto; padding: 30px 40px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 30px; }
.card { background: #111633; border: 1px solid #1e2a5a; border-radius: 12px; padding: 24px; }
.card h3 { color: #a78bfa; margin-bottom: 12px; font-size: 16px; }
.card p { color: #6b7db3; font-size: 14px; line-height: 1.6; margin-bottom: 12px; }
.btn { display: inline-block; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }
.btn-primary { background: #6366f1; color: white; }
.btn-primary:hover { background: #4f46e5; }
.btn-success { background: #10b981; color: white; }
.btn-warning { background: #f59e0b; color: white; }
.btn-danger { background: #ef4444; color: white; }
.btn-accent { background: linear-gradient(135deg, #6366f1, #ec4899); color: white; }
.input { width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e2a5a; background: #0a0e27; color: #e0e6ff; font-size: 14px; margin-bottom: 12px; }
.input:focus { outline: none; border-color: #6366f1; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px; }
.stat { background: #111633; border: 1px solid #1e2a5a; border-radius: 12px; padding: 20px; text-align: center; }
.stat .value { font-size: 32px; font-weight: 700; color: #a78bfa; }
.stat .label { font-size: 12px; color: #64748b; margin-top: 4px; }
.log { background: #060919; border: 1px solid #1e2a5a; border-radius: 8px; padding: 16px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.8; }
.log .event { color: #a78bfa; } .log .success { color: #10b981; } .log .error { color: #ef4444; } .log .info { color: #64748b; }
.section-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #e0e6ff; }
.pipeline-card { background: linear-gradient(135deg, #111633, #1a1040); border: 2px solid #6366f1; border-radius: 16px; padding: 30px; margin-bottom: 30px; text-align: center; }
.pipeline-card h3 { color: #c4b5fd; font-size: 20px; margin-bottom: 8px; }
.pipeline-card p { color: #8b7db3; margin-bottom: 16px; }
.pipeline-flow { display: flex; justify-content: center; gap: 8px; margin: 16px 0; flex-wrap: wrap; }
.pipeline-flow .step { background: #1e2a5a; padding: 8px 16px; border-radius: 8px; font-size: 13px; }
.pipeline-flow .arrow { color: #6366f1; font-size: 18px; line-height: 36px; }
</style>
</head>
<body>
<div class="header">
  <h1>⚡ ChainScribe</h1>
  <span class="badge">Web3 × Long-Horizon Task v2.0</span>
</div>

<div class="container">
  <div class="stats">
    <div class="stat"><div class="value" id="s-steps">0</div><div class="label">执行步骤</div></div>
    <div class="stat"><div class="value" id="s-retries">0</div><div class="label">自动重试</div></div>
    <div class="stat"><div class="value" id="s-corrections">0</div><div class="label">自我纠错</div></div>
    <div class="stat"><div class="value" id="s-published">0</div><div class="label">已完成</div></div>
  </div>

  <!-- 完整流水线 -->
  <div class="pipeline-card">
    <h3>🚀 完整流水线</h3>
    <p>出版 → 叙事 → DAO → 衍生 — 一键触发四模块协同</p>
    <div class="pipeline-flow">
      <span class="step">📝 出版</span><span class="arrow">→</span>
      <span class="step">📖 叙事</span><span class="arrow">→</span>
      <span class="step">🏛️ DAO</span><span class="arrow">→</span>
      <span class="step">🎨 衍生</span>
    </div>
    <input class="input" id="pipe-topic" placeholder="输入主题..." value="Web3 创作者经济" style="max-width:400px;margin:0 auto 12px">
    <button class="btn btn-accent" onclick="runPipeline()">🚀 启动完整流水线</button>
  </div>

  <!-- 单独工作流 -->
  <div class="grid">
    <div class="card">
      <h3>📝 链上出版 Agent</h3>
      <p>调研 → 撰写 → 质检 → 排版 → 上链</p>
      <input class="input" id="pub-topic" value="Web3 创作者经济">
      <button class="btn btn-primary" onclick="runWorkflow('publish')">🚀 开始出版</button>
    </div>
    <div class="card">
      <h3>📖 动态 NFT 叙事</h3>
      <p>链上事件驱动叙事演化与视觉更新</p>
      <input class="input" id="nar-title" value="链上觉醒">
      <button class="btn btn-success" onclick="runWorkflow('narrative')">🔄 启动叙事</button>
    </div>
    <div class="card">
      <h3>🏛️ DAO 协作</h3>
      <p>多 Agent 分工协作与自动分账</p>
      <input class="input" id="dao-title" value="DeFi 安全报告">
      <button class="btn btn-warning" onclick="runWorkflow('dao')">🤝 开始协作</button>
    </div>
    <div class="card">
      <h3>🎨 IP 衍生</h3>
      <p>基于链上 IP 生成风格一致的衍生内容</p>
      <input class="input" id="ip-name" value="CyberDragon">
      <button class="btn btn-danger" onclick="runWorkflow('ip')">✨ 生成衍生</button>
    </div>
  </div>

  <div class="section-title">📋 实时日志</div>
  <div class="log" id="log">
    <div class="info">[System] ChainScribe v2.0 统一编排器就绪</div>
  </div>
</div>

<script>
const API = 'http://localhost:8000';
let ws, steps=0, retries=0, corrections=0, published=0;

function connectWS() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'step_update') {
      steps++; document.getElementById('s-steps').textContent = steps;
      if (d.retry_count > 0) { retries = Math.max(retries, d.retry_count); document.getElementById('s-retries').textContent = retries; }
      if (d.self_corrections > 0) { corrections += d.self_corrections; document.getElementById('s-corrections').textContent = corrections; }
      addLog(d.step_name + ' → ' + d.step_status, d.step_status === 'success' ? 'success' : d.step_status === 'failed' ? 'error' : 'event');
    }
    if (d.type === 'workflow_complete') {
      published++; document.getElementById('s-published').textContent = published;
      addLog(`✅ 工作流完成 (${d.time}s)`, 'success');
    }
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
}
connectWS();

function addLog(msg, cls='info') {
  const log = document.getElementById('log');
  const t = new Date().toLocaleTimeString();
  log.innerHTML += `<div class="${cls}">[${t}] ${msg}</div>`;
  log.scrollTop = log.scrollHeight;
}

async function runWorkflow(type) {
  const endpoints = { publish: '/api/publish', narrative: '/api/narrative', dao: '/api/dao', ip: '/api/ip-derivative' };
  const bodies = {
    publish: { topic: document.getElementById('pub-topic').value },
    narrative: { title: document.getElementById('nar-title').value },
    dao: { title: document.getElementById('dao-title').value },
    ip: { ip_name: document.getElementById('ip-name').value },
  };
  addLog(`▶ 启动 ${type} 工作流...`, 'event');
  try {
    const res = await fetch(`${API}${endpoints[type]}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(bodies[type]) });
    const data = await res.json();
    addLog(`📋 任务已创建: ${data.task_id}`, 'info');
  } catch(e) { addLog(`❌ 启动失败: ${e}`, 'error'); }
}

async function runPipeline() {
  const topic = document.getElementById('pipe-topic').value;
  addLog('🚀 启动完整流水线...', 'event');
  try {
    const res = await fetch(`${API}/api/pipeline`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({topic}) });
    const data = await res.json();
    addLog(`📋 流水线任务: ${data.task_id}`, 'info');
  } catch(e) { addLog(`❌ 启动失败: ${e}`, 'error'); }
}
</script>
</body>
</html>"""


# ─── 健康检查 ────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "timestamp": time.time()}
