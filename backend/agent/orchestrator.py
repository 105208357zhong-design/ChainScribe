"""
ChainScribe — 统一 Agent 编排器
将四个 Agent 模块整合为一个可协同工作的系统
"""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from .publishing import PublishingAgent
from .narrative import NarrativeEngine
from .dao import CreatorDAO, AgentRole
from .ip_derivative import IPDerivativeAgent
from .llm import GLMClient
from ..services.ipfs import IPFSClient
from ..services.blockchain import BlockchainClient


class WorkflowType(str, Enum):
    PUBLISH = "publish"           # 链上出版
    NARRATIVE = "narrative"       # 动态叙事
    DAO = "dao"                   # DAO 协作
    IP_DERIVATIVE = "ip"          # IP 衍生
    FULL_PIPELINE = "full"        # 完整流水线：出版 → 叙事 → 衍生


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    workflow_type: WorkflowType
    success: bool
    total_time: float
    steps_completed: int
    steps_total: int
    results: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)  # 产出物


class ChainScribeOrchestrator:
    """
    ChainScribe 统一编排器
    
    整合四个 Agent 模块，提供：
    1. 统一入口 — 一个 API 调用即可启动任意工作流
    2. 流水线模式 — 出版 → 叙事 → 衍生 的完整链路
    3. 共享基础设施 — LLM、IPFS、Blockchain 客户端统一管理
    4. 事件驱动 — 模块间通过事件通信
    """

    def __init__(
        self,
        api_key: str = None,
        pinata_api_key: str = None,
        pinata_secret: str = None,
        rpc_url: str = None,
        contract_address: str = None,
    ):
        # 共享基础设施
        self.llm = GLMClient(api_key=api_key)
        self.ipfs = IPFSClient(pinata_api_key=pinata_api_key, pinata_secret=pinata_secret)
        self.blockchain = BlockchainClient(rpc_url=rpc_url, contract_address=contract_address)

        # 四个 Agent 模块 — 共享基础设施
        self.publisher = PublishingAgent(
            llm_client=self.llm,
            ipfs_client=self.ipfs,
            blockchain_client=self.blockchain,
        )
        self.narrative = NarrativeEngine(
            llm_client=self.llm,
            blockchain_client=self.blockchain,
        )
        self.dao = CreatorDAO()
        self.ip_agent = IPDerivativeAgent()

        # 工作流状态
        self._workflows: dict[str, WorkflowResult] = {}
        self._event_handlers: dict[str, list[Callable]] = {}

    # ─── 统一入口 ────────────────────────────────────────

    async def execute(
        self,
        workflow: WorkflowType,
        on_progress: Callable = None,
        **kwargs,
    ) -> WorkflowResult:
        """
        统一执行入口
        
        Args:
            workflow: 工作流类型
            on_progress: 进度回调
            **kwargs: 各工作流所需参数
        """
        workflow_id = str(uuid.uuid4())[:8]
        start = time.time()

        result = WorkflowResult(
            workflow_id=workflow_id,
            workflow_type=workflow,
            success=False,
            total_time=0,
            steps_completed=0,
            steps_total=0,
        )

        try:
            if workflow == WorkflowType.PUBLISH:
                r = await self._run_publish(on_progress, **kwargs)
            elif workflow == WorkflowType.NARRATIVE:
                r = await self._run_narrative(on_progress, **kwargs)
            elif workflow == WorkflowType.DAO:
                r = await self._run_dao(on_progress, **kwargs)
            elif workflow == WorkflowType.IP_DERIVATIVE:
                r = await self._run_ip_derivative(on_progress, **kwargs)
            elif workflow == WorkflowType.FULL_PIPELINE:
                r = await self._run_full_pipeline(on_progress, **kwargs)
            else:
                raise ValueError(f"Unknown workflow: {workflow}")

            result.results = r.get("results", {})
            result.artifacts = r.get("artifacts", {})
            result.steps_completed = r.get("steps_completed", 0)
            result.steps_total = r.get("steps_total", 0)
            result.success = r.get("success", True)

        except Exception as e:
            result.errors.append(str(e))
            result.success = False

        result.total_time = round(time.time() - start, 2)
        self._workflows[workflow_id] = result

        # 触发事件
        await self._emit("workflow_complete", result)

        return result

    # ─── 各工作流实现 ────────────────────────────────────

    async def _run_publish(self, on_progress, **kwargs) -> dict:
        """链上出版工作流"""
        topic = kwargs.get("topic", "Web3 创作者经济")
        content_type = kwargs.get("content_type", "research_report")
        unlock_price = kwargs.get("unlock_price", 0.01)
        max_words = kwargs.get("max_words", 3000)

        r = await self.publisher.create_and_publish(
            topic=topic,
            content_type=content_type,
            unlock_price=unlock_price,
            max_words=max_words,
            on_progress=on_progress,
        )

        plan = r.get("plan", {})
        artifacts = {}
        if r.get("final_content"):
            artifacts["published_content"] = r["final_content"]
        if r.get("publication"):
            artifacts["nft_publication"] = r["publication"]

        return {
            "results": r,
            "artifacts": artifacts,
            "steps_completed": plan.get("completed_steps", 0),
            "steps_total": plan.get("total_steps", 0),
            "success": plan.get("status") == "success",
        }

    async def _run_narrative(self, on_progress, **kwargs) -> dict:
        """动态叙事工作流"""
        token_id = kwargs.get("token_id", "1")
        title = kwargs.get("title", "链上觉醒")
        genre = kwargs.get("genre", "sci-fi")
        total_chapters = kwargs.get("total_chapters", 5)

        # 初始化
        state = await self.narrative.initialize_narrative(
            token_id=token_id,
            title=title,
            genre=genre,
            total_chapters=total_chapters,
        )

        # 运行叙事周期
        chapters = await self.narrative.run_narrative_cycle(
            token_id=token_id,
            max_chapters=total_chapters,
            interval_seconds=kwargs.get("interval_seconds", 0.5),
        )

        artifacts = {
            "narrative_state": {
                "token_id": token_id,
                "arc": state.narrative_arc,
                "style": state.style_palette,
            },
            "chapters": chapters,
        }

        return {
            "results": {"token_id": token_id, "chapters": chapters, "state": state},
            "artifacts": artifacts,
            "steps_completed": len(chapters),
            "steps_total": total_chapters,
            "success": len(chapters) > 0,
        }

    async def _run_dao(self, on_progress, **kwargs) -> dict:
        """DAO 协作工作流"""
        title = kwargs.get("title", "DeFi 安全报告")
        goal = kwargs.get("goal", f"协作完成 {title} 的调研、撰写、设计、发布与推广")

        project = await self.dao.create_project(title=title, goal=goal)
        r = await self.dao.execute_project(project.id)

        artifacts = {
            "dao_project": {
                "id": project.id,
                "title": r.get("title", title),
                "revenue_splits": r.get("revenue_splits", []),
            }
        }

        return {
            "results": r,
            "artifacts": artifacts,
            "steps_completed": r.get("completed_tasks", 0),
            "steps_total": r.get("total_tasks", 0),
            "success": r.get("success", False),
        }

    async def _run_ip_derivative(self, on_progress, **kwargs) -> dict:
        """IP 衍生工作流"""
        ip_name = kwargs.get("ip_name", "CyberDragon")
        ip_style = kwargs.get("ip_style", "cyberpunk")
        derivative_types = kwargs.get("derivative_types", ["story", "script", "merch"])

        r = await self.ip_agent.create_derivatives(
            ip_name=ip_name,
            ip_style=ip_style,
            derivative_types=derivative_types,
            on_progress=on_progress,
        )

        plan = r.get("plan", {})
        artifacts = {"derivatives": r.get("derivatives", [])}

        return {
            "results": r,
            "artifacts": artifacts,
            "steps_completed": plan.get("completed_steps", 0),
            "steps_total": plan.get("total_steps", 0),
            "success": plan.get("status") == "success",
        }

    async def _run_full_pipeline(self, on_progress, **kwargs) -> dict:
        """
        完整流水线：出版 → 叙事 → 衍生
        
        展示四个模块的协同工作：
        1. 先用 Publishing Agent 生成并发布内容
        2. 用 Narrative Engine 为发布的 NFT 创建动态叙事
        3. 用 DAO 组织团队协作
        4. 用 IP Agent 基于叙事生成衍生内容
        """
        topic = kwargs.get("topic", "Web3 创作者经济")
        all_results = {}
        all_artifacts = {}
        total_completed = 0
        total_steps = 0

        # Step 1: 链上出版
        if on_progress:
            await on_progress(None, type("Step", (), {"name": "🔄 [流水线] 阶段1: 链上出版", "status": type("S", (), {"value": "running"})})())
        
        pub_result = await self._run_publish(on_progress, topic=topic, **kwargs)
        all_results["publish"] = pub_result["results"]
        all_artifacts.update(pub_result["artifacts"])
        total_completed += pub_result["steps_completed"]
        total_steps += pub_result["steps_total"]

        # Step 2: 动态叙事（基于出版产出的 NFT）
        if on_progress:
            await on_progress(None, type("Step", (), {"name": "🔄 [流水线] 阶段2: 动态叙事", "status": type("S", (), {"value": "running"})})())

        token_id = "1"
        if pub_result.get("artifacts", {}).get("nft_publication"):
            token_id = str(pub_result["artifacts"]["nft_publication"].get("token_id", "1"))

        nar_result = await self._run_narrative(
            on_progress,
            token_id=token_id,
            title=topic,
            **kwargs,
        )
        all_results["narrative"] = nar_result["results"]
        all_artifacts.update(nar_result["artifacts"])
        total_completed += nar_result["steps_completed"]
        total_steps += nar_result["steps_total"]

        # Step 3: DAO 协作
        if on_progress:
            await on_progress(None, type("Step", (), {"name": "🔄 [流水线] 阶段3: DAO 协作", "status": type("S", (), {"value": "running"})})())

        dao_result = await self._run_dao(on_progress, title=topic, **kwargs)
        all_results["dao"] = dao_result["results"]
        all_artifacts.update(dao_result["artifacts"])
        total_completed += dao_result["steps_completed"]
        total_steps += dao_result["steps_total"]

        # Step 4: IP 衍生
        if on_progress:
            await on_progress(None, type("Step", (), {"name": "🔄 [流水线] 阶段4: IP 衍生", "status": type("S", (), {"value": "running"})})())

        ip_result = await self._run_ip_derivative(
            on_progress,
            ip_name=topic.split()[0] if topic else "ChainScribe",
            **kwargs,
        )
        all_results["ip_derivative"] = ip_result["results"]
        all_artifacts.update(ip_result["artifacts"])
        total_completed += ip_result["steps_completed"]
        total_steps += ip_result["steps_total"]

        return {
            "results": all_results,
            "artifacts": all_artifacts,
            "steps_completed": total_completed,
            "steps_total": total_steps,
            "success": True,
        }

    # ─── 事件系统 ────────────────────────────────────────

    def on(self, event: str, handler: Callable):
        """注册事件处理器"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _emit(self, event: str, data: Any = None):
        """触发事件"""
        for handler in self._event_handlers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception:
                pass

    # ─── 状态查询 ────────────────────────────────────────

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowResult]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[dict]:
        return [
            {
                "id": r.workflow_id,
                "type": r.workflow_type.value,
                "success": r.success,
                "time": r.total_time,
                "steps": f"{r.steps_completed}/{r.steps_total}",
            }
            for r in self._workflows.values()
        ]
