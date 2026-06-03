"""
ChainScribe — 创作者 DAO 协作系统
多个 Agent 分工负责调研、写作、设计、发布、推广与自动分账
"""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AgentRole(str, Enum):
    COORDINATOR = "coordinator"   # 协调者 — 拆解任务、分配工作
    RESEARCHER = "researcher"     # 调研员 — 收集资料、数据分析
    WRITER = "writer"            # 撰稿人 — 内容创作
    DESIGNER = "designer"        # 设计师 — 视觉设计、排版
    PUBLISHER = "publisher"      # 发布者 — 上链、铸造NFT
    PROMOTER = "promoter"        # 推广者 — 社交媒体、社区运营
    TREASURER = "treasurer"      # 财务 — 分账、收益管理


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DAOTask:
    """DAO 任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: AgentRole = None
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_to: str = ""
    output: Any = None
    dependencies: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    review_notes: list[str] = field(default_factory=list)


@dataclass
class RevenueSplit:
    """收益分账配置"""
    role: AgentRole
    address: str  # 钱包地址
    basis_points: int  # 万分比
    label: str = ""


@dataclass
class DAOProject:
    """DAO 项目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    goal: str = ""
    tasks: list[DAOTask] = field(default_factory=list)
    revenue_splits: list[RevenueSplit] = field(default_factory=list)
    status: str = "planning"  # planning, executing, reviewing, published
    created_at: float = field(default_factory=time.time)
    total_revenue: float = 0.0


class CreatorDAO:
    """
    创作者 DAO 协作系统
    
    多 Agent 协作完成内容创作全流程：
    1. Coordinator 拆解任务并分配
    2. Researcher 收集资料
    3. Writer 撰写内容
    4. Designer 视觉设计
    5. Publisher 发布上链
    6. Promoter 推广传播
    7. Treasurer 管理分账
    
    每个 Agent 角色独立执行，通过消息传递协作
    """

    def __init__(self, llm_client=None, blockchain_client=None):
        self.llm = llm_client
        self.blockchain = blockchain_client
        self._agents: dict[AgentRole, dict] = {}
        self._projects: dict[str, DAOProject] = {}
        self._message_log: list[dict] = []
        
        # 初始化 Agent 角色
        self._init_agents()

    def _init_agents(self):
        """初始化各角色的 Agent"""
        agent_configs = {
            AgentRole.COORDINATOR: {
                "name": "Atlas",
                "specialty": "任务拆解与协调",
                "model": "glm-5.1",
            },
            AgentRole.RESEARCHER: {
                "name": "Scout",
                "specialty": "资料收集与数据分析",
                "model": "glm-5.1",
            },
            AgentRole.WRITER: {
                "name": "Muse",
                "specialty": "内容创作与文案",
                "model": "glm-5.1",
            },
            AgentRole.DESIGNER: {
                "name": "Pixel",
                "specialty": "视觉设计与排版",
                "model": "glm-5.1",
            },
            AgentRole.PUBLISHER: {
                "name": "Forge",
                "specialty": "链上发布与NFT铸造",
                "model": "glm-5.1",
            },
            AgentRole.PROMOTER: {
                "name": "Echo",
                "specialty": "社区运营与推广",
                "model": "glm-5.1",
            },
            AgentRole.TREASURER: {
                "name": "Vault",
                "specialty": "收益管理与自动分账",
                "model": "glm-5.1",
            },
        }
        
        for role, config in agent_configs.items():
            self._agents[role] = config

    async def create_project(
        self,
        title: str,
        goal: str,
        revenue_splits: list[dict] = None,
    ) -> DAOProject:
        """创建新的 DAO 创作项目"""
        project = DAOProject(title=title, goal=goal)
        
        # 设置默认分账比例
        default_splits = [
            {"role": AgentRole.WRITER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 4000, "label": "主笔"},
            {"role": AgentRole.RESEARCHER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 1500, "label": "调研"},
            {"role": AgentRole.DESIGNER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 1500, "label": "设计"},
            {"role": AgentRole.PUBLISHER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 500, "label": "发布"},
            {"role": AgentRole.PROMOTER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 500, "label": "推广"},
            {"role": AgentRole.COORDINATOR, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 1000, "label": "协调"},
            {"role": AgentRole.TREASURER, "address": f"0x{uuid.uuid4().hex[:40]}", "basis_points": 1000, "label": "财务"},
        ]
        
        splits_config = revenue_splits or default_splits
        for split in splits_config:
            project.revenue_splits.append(RevenueSplit(
                role=split["role"],
                address=split["address"],
                basis_points=split["basis_points"],
                label=split.get("label", split["role"].value),
            ))
        
        # Coordinator 自主拆解任务
        tasks = await self._decompose_tasks(project)
        project.tasks = tasks
        
        self._projects[project.id] = project
        self._log_message(AgentRole.COORDINATOR, None, f"项目「{title}」已创建，共 {len(tasks)} 个任务")
        
        return project

    async def execute_project(self, project_id: str) -> dict:
        """执行完整的 DAO 项目 — 展示多 Agent 长程协作"""
        project = self._projects.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        print(f"\n🏛️ 创作者DAO项目启动 — 「{project.title}」")
        print(f"📋 目标: {project.goal}")
        print(f"👥 参与角色: {', '.join(a['name'] for a in self._agents.values())}")
        print(f"📝 任务数: {len(project.tasks)}")
        print("=" * 60)

        project.status = "executing"
        start_time = time.time()

        # 按依赖顺序执行任务
        completed_tasks = set()
        max_iterations = len(project.tasks) * 2  # 防止死循环
        iteration = 0

        while len(completed_tasks) < len(project.tasks) and iteration < max_iterations:
            iteration += 1
            
            # 找到可以执行的任务（依赖已完成）
            ready_tasks = [
                t for t in project.tasks
                if t.id not in completed_tasks
                and t.status in ("pending", "failed")
                and all(dep in completed_tasks for dep in t.dependencies)
            ]

            if not ready_tasks:
                break

            # 并行执行就绪的任务
            tasks_coro = []
            for task in ready_tasks:
                task.status = "in_progress"
                tasks_coro.append(self._execute_task(project, task))

            results = await asyncio.gather(*tasks_coro, return_exceptions=True)

            for task, result in zip(ready_tasks, results):
                if isinstance(result, Exception):
                    task.status = "failed"
                    task.review_notes.append(f"执行失败: {str(result)}")
                    self._log_message(task.role, AgentRole.COORDINATOR, f"任务失败: {task.description[:50]}")
                else:
                    task.status = "completed"
                    task.output = result
                    task.completed_at = time.time()
                    completed_tasks.add(task.id)
                    agent_name = self._agents[task.role]["name"]
                    self._log_message(task.role, AgentRole.COORDINATOR, f"任务完成: {task.description[:50]}")
                    print(f"  ✅ [{agent_name}] {task.description[:50]}")

        # 生成项目报告
        total_time = time.time() - start_time
        success = len(completed_tasks) == len(project.tasks)
        project.status = "published" if success else "partial"

        report = {
            "project_id": project.id,
            "title": project.title,
            "success": success,
            "total_tasks": len(project.tasks),
            "completed_tasks": len(completed_tasks),
            "total_time": round(total_time, 2),
            "revenue_splits": [
                {"role": s.role.value, "address": s.address, "share": f"{s.basis_points/100:.1f}%", "label": s.label}
                for s in project.revenue_splits
            ],
            "tasks_summary": [
                {
                    "id": t.id,
                    "role": t.role.value,
                    "agent": self._agents[t.role]["name"],
                    "description": t.description[:60],
                    "status": t.status,
                }
                for t in project.tasks
            ],
            "message_log": self._message_log[-20:],  # 最近20条消息
        }

        print(f"\n{'=' * 60}")
        if success:
            print(f"🎉 项目完成！总耗时 {total_time:.1f}s")
        else:
            print(f"⚠️ 项目部分完成 ({len(completed_tasks)}/{len(project.tasks)})")
        
        return report

    async def _decompose_tasks(self, project: DAOProject) -> list[DAOTask]:
        """Coordinator 自主拆解任务"""
        tasks_def = [
            (AgentRole.RESEARCHER, "收集主题相关资料、数据、权威来源", [], TaskPriority.HIGH),
            (AgentRole.RESEARCHER, "竞品分析和市场调研", [], TaskPriority.MEDIUM),
            (AgentRole.WRITER, "撰写内容大纲", ["research_0"], TaskPriority.HIGH),
            (AgentRole.WRITER, "撰写完整初稿", ["outline_0"], TaskPriority.HIGH),
            (AgentRole.DESIGNER, "设计封面和视觉风格", [], TaskPriority.MEDIUM),
            (AgentRole.DESIGNER, "排版和格式化最终内容", ["draft_0", "visual_0"], TaskPriority.HIGH),
            (AgentRole.WRITER, "内容审查和修订", ["draft_0"], TaskPriority.HIGH),
            (AgentRole.PUBLISHER, "上传IPFS并铸造NFT", ["format_0"], TaskPriority.CRITICAL),
            (AgentRole.PUBLISHER, "设置付费解锁和分账", ["mint_0"], TaskPriority.CRITICAL),
            (AgentRole.PROMOTER, "撰写推广文案", ["mint_0"], TaskPriority.MEDIUM),
            (AgentRole.PROMOTER, "社区发布和传播", ["promo_0"], TaskPriority.MEDIUM),
            (AgentRole.TREASURER, "配置自动分账合约", ["mint_0"], TaskPriority.HIGH),
        ]

        # 创建任务并建立依赖关系
        task_id_map = {}
        tasks = []
        
        for i, (role, desc, deps, priority) in enumerate(tasks_def):
            task = DAOTask(
                role=role,
                description=desc,
                priority=priority,
                assigned_to=self._agents[role]["name"],
            )
            task_id_map[f"{role.value}_{len([t for t in tasks if t.role == role])}"] = task.id
            tasks.append(task)

        # 解析依赖
        for i, (_, _, deps, _) in enumerate(tasks_def):
            for dep in deps:
                if dep in task_id_map:
                    tasks[i].dependencies.append(task_id_map[dep])

        return tasks

    async def _execute_task(self, project: DAOProject, task: DAOTask) -> Any:
        """单个 Agent 执行任务"""
        agent = self._agents[task.role]
        
        # 模拟 Agent 执行
        await asyncio.sleep(0.3)
        
        outputs = {
            AgentRole.RESEARCHER: {
                "sources": ["https://example.com/research1", "https://example.com/data2"],
                "key_findings": ["发现1", "发现2", "发现3"],
                "data_points": {"metric1": "value1"},
            },
            AgentRole.WRITER: {
                "content": f"基于调研结果撰写的「{project.title}」内容...",
                "word_count": 2500,
            },
            AgentRole.DESIGNER: {
                "cover_cid": f"Qm{uuid.uuid4().hex[:44]}",
                "style": "modern-minimal",
                "color_palette": ["#1a1a2e", "#e94560", "#0f3460"],
            },
            AgentRole.PUBLISHER: {
                "token_id": str(uuid.uuid4().int % 10000),
                "content_cid": f"Qm{uuid.uuid4().hex[:44]}",
                "tx_hash": f"0x{uuid.uuid4().hex}",
            },
            AgentRole.PROMOTER: {
                "tweets": ["🚀 新内容已上线！", "📖 深度报告：..."],
                "discord_posts": 3,
                "reach_estimate": 5000,
            },
            AgentRole.TREASURER: {
                "split_configured": True,
                "contract_address": f"0x{uuid.uuid4().hex[:40]}",
                "total_splits": len(project.revenue_splits),
            },
            AgentRole.COORDINATOR: {
                "status": "coordinated",
                "task_count": len(project.tasks),
            },
        }

        return outputs.get(task.role, {"result": "completed"})

    def _log_message(self, from_role: AgentRole, to_role: Optional[AgentRole], message: str):
        """记录 Agent 间消息"""
        self._message_log.append({
            "from": self._agents[from_role]["name"] if from_role in self._agents else from_role.value,
            "to": self._agents[to_role]["name"] if to_role and to_role in self._agents else (to_role.value if to_role else "all"),
            "message": message,
            "timestamp": time.time(),
        })
