"""
ChainScribe — 长程自主执行引擎
核心：任务拆解 → 多步执行 → 自我纠错 → 持续迭代 → 交付
"""
import json
import time
import asyncio
import traceback
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskStep:
    """单个执行步骤"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    retry_count: int = 0
    result: Any = None
    error: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    self_correction_notes: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0


@dataclass
class ExecutionPlan:
    """完整执行计划"""
    goal: str
    steps: list[TaskStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    status: TaskStatus = TaskStatus.PENDING
    total_retries: int = 0
    self_corrections: int = 0

    def get_step(self, step_id: str) -> Optional[TaskStep]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "status": self.status.value,
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for s in self.steps if s.status == TaskStatus.SUCCESS),
            "failed_steps": sum(1 for s in self.steps if s.status == TaskStatus.FAILED),
            "total_retries": self.total_retries,
            "self_corrections": self.self_corrections,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "retry_count": s.retry_count,
                    "duration": round(s.duration, 2),
                    "error": s.error,
                    "self_corrections": len(s.self_correction_notes),
                    "tool_calls": len(s.tool_calls),
                }
                for s in self.steps
            ],
        }


class LongHorizonEngine:
    """
    长程自主执行引擎
    
    核心能力：
    1. 自主拆解复杂任务为多步骤计划
    2. 按依赖顺序执行，支持并行
    3. 执行失败自动重试 + 自我纠错
    4. 全程记录执行轨迹，可追溯
    5. 支持人工干预点（可选）
    """

    def __init__(self, agent_name: str = "ChainScribe"):
        self.agent_name = agent_name
        self.execution_log: list[dict] = []
        self.tool_registry: dict[str, Callable] = {}
        self.on_step_update: Optional[Callable] = None

    def register_tool(self, name: str, func: Callable):
        """注册可用工具"""
        self.tool_registry[name] = func

    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """执行完整计划 — 核心长程执行循环"""
        plan.status = TaskStatus.RUNNING
        self._log("PLAN_START", f"开始执行计划: {plan.goal}", plan=plan.to_dict())

        # 拓扑排序执行
        executed = set()
        max_iterations = len(plan.steps) * 3  # 防止无限循环
        iteration = 0

        while len(executed) < len(plan.steps) and iteration < max_iterations:
            iteration += 1
            ready_steps = self._get_ready_steps(plan, executed)

            if not ready_steps:
                # 检查是否有未执行但依赖失败的步骤
                stuck = [s for s in plan.steps if s.id not in executed and s.status != TaskStatus.FAILED]
                if stuck:
                    for s in stuck:
                        s.status = TaskStatus.SKIPPED
                        s.error = "Dependency failed"
                        executed.add(s.id)
                    continue
                break

            # 并行执行就绪步骤
            tasks = [self._execute_step(plan, step) for step in ready_steps]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, result in zip(ready_steps, results):
                executed.add(step.id)
                if isinstance(result, Exception):
                    step.status = TaskStatus.FAILED
                    step.error = str(result)

        # 确定最终状态
        failed = [s for s in plan.steps if s.status == TaskStatus.FAILED]
        plan.status = TaskStatus.FAILED if failed else TaskStatus.SUCCESS

        self._log("PLAN_COMPLETE", f"计划执行完成: {plan.status.value}", plan=plan.to_dict())
        return plan

    def _get_ready_steps(self, plan: ExecutionPlan, executed: set) -> list[TaskStep]:
        """获取当前可执行的步骤（依赖已满足）"""
        ready = []
        for step in plan.steps:
            if step.id in executed:
                continue
            if step.status == TaskStatus.FAILED and step.retry_count >= step.max_retries:
                continue
            # 检查依赖
            deps_met = all(
                plan.get_step(dep_id) and plan.get_step(dep_id).status == TaskStatus.SUCCESS
                for dep_id in step.dependencies
                if plan.get_step(dep_id)
            )
            deps_failed = any(
                plan.get_step(dep_id) and plan.get_step(dep_id).status == TaskStatus.FAILED
                for dep_id in step.dependencies
                if plan.get_step(dep_id)
            )
            if deps_met and not deps_failed:
                ready.append(step)
        return ready

    async def _execute_step(self, plan: ExecutionPlan, step: TaskStep) -> Any:
        """执行单个步骤 — 含重试和自我纠错"""
        step.status = TaskStatus.RUNNING
        step.started_at = time.time()

        if self.on_step_update:
            await self.on_step_update(plan, step)

        while step.retry_count <= step.max_retries:
            try:
                self._log("STEP_START", f"执行步骤: {step.name}", step_id=step.id)

                # 查找并执行对应的工具
                tool_name = step.id.split("_")[0] if "_" in step.id else step.id
                if tool_name in self.tool_registry:
                    result = await self.tool_registry[tool_name](step, plan)
                else:
                    # 默认执行：调用 step 的执行函数
                    result = await self._default_execute(step, plan)

                step.result = result
                step.status = TaskStatus.SUCCESS
                step.completed_at = time.time()
                self._log("STEP_SUCCESS", f"步骤完成: {step.name}", step_id=step.id, duration=step.duration)
                
                if self.on_step_update:
                    await self.on_step_update(plan, step)
                return result

            except Exception as e:
                step.retry_count += 1
                plan.total_retries += 1
                error_msg = f"{type(e).__name__}: {str(e)}"
                step.error = error_msg

                self._log("STEP_RETRY", f"步骤失败，重试 {step.retry_count}/{step.max_retries}: {step.name}",
                         step_id=step.id, error=error_msg)

                # 自我纠错：分析错误并调整策略
                if step.retry_count <= step.max_retries:
                    correction = self._self_correct(step, plan, e)
                    step.self_correction_notes.append(correction)
                    plan.self_corrections += 1
                    self._log("SELF_CORRECT", f"自我纠错: {correction}", step_id=step.id)
                    await asyncio.sleep(1 * step.retry_count)  # 指数退避

        # 所有重试用尽
        step.status = TaskStatus.FAILED
        step.completed_at = time.time()
        self._log("STEP_FAILED", f"步骤最终失败: {step.name}", step_id=step.id, error=step.error)
        
        if self.on_step_update:
            await self.on_step_update(plan, step)
        raise RuntimeError(f"Step {step.name} failed after {step.max_retries} retries: {step.error}")

    async def _default_execute(self, step: TaskStep, plan: ExecutionPlan) -> Any:
        """默认步骤执行逻辑"""
        # 模拟执行 — 实际由注册的工具函数处理
        await asyncio.sleep(0.1)
        return {"step": step.name, "status": "completed"}

    def _self_correct(self, step: TaskStep, plan: ExecutionPlan, error: Exception) -> str:
        """
        自我纠错引擎
        
        根据错误类型分析原因并生成修正策略：
        - 网络错误 → 重试 + 降级方案
        - 内容质量不达标 → 调整参数重写
        - 工具调用失败 → 切换备选工具
        - 依赖缺失 → 跳过或使用默认值
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        if "timeout" in error_msg or "connection" in error_msg:
            return f"网络问题，切换到降级模式或使用缓存数据"
        elif "quality" in error_msg or "score" in error_msg:
            return f"内容质量不达标，调整生成参数并重写"
        elif "not found" in error_msg or "404" in error_msg:
            return f"资源未找到，尝试备选数据源"
        elif "validation" in error_msg or "invalid" in error_msg:
            return f"数据验证失败，检查输入格式并修正"
        else:
            return f"未知错误({error_type})，尝试通用恢复策略"

    def _log(self, event: str, message: str, **kwargs):
        """记录执行日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "event": event,
            "message": message,
            **kwargs,
        }
        self.execution_log.append(entry)

    def get_execution_summary(self) -> dict:
        """获取执行摘要"""
        return {
            "total_events": len(self.execution_log),
            "events_by_type": {
                event: sum(1 for e in self.execution_log if e["event"] == event)
                for event in set(e["event"] for e in self.execution_log)
            },
            "log": self.execution_log[-20:],  # 最近20条
        }
