#!/usr/bin/env python3
"""
ChainScribe Demo v2 — 通过统一编排器展示完整长程自主执行能力

运行方式：
  python3 run_demo.py                  # 运行全部 Demo
  python3 run_demo.py --mode publish   # 仅运行链上出版
  python3 run_demo.py --mode narrative # 仅运行动态叙事
  python3 run_demo.py --mode dao       # 仅运行 DAO 协作
  python3 run_demo.py --mode ip        # 仅运行 IP 衍生
  python3 run_demo.py --mode pipeline  # 运行完整流水线
"""
import sys
import os
import json
import time
import asyncio

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.orchestrator import ChainScribeOrchestrator, WorkflowType


# ========== 彩色输出 ==========

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_header(text):
    print(f"\n{'='*70}")
    print(f"{Color.HEADER}{Color.BOLD}  {text}{Color.RESET}")
    print(f"{'='*70}\n")


def print_result(key, value):
    print(f"    {Color.CYAN}{key}:{Color.RESET} {value}")


# ========== 进度回调 ==========

_step_icons = {
    "research": "🔍", "outline": "📋", "write": "✍️",
    "quality": "✅", "format": "🎨", "publish": "📤",
    "monitor": "📡", "analyze": "🧠", "narrate": "📖",
    "visual": "🖼️", "onchain": "⛓️", "assign": "📋",
    "execute_parallel": "⚡", "integrate": "🔧",
    "publish_dao": "📤", "distribute": "💰",
    "analyze_ip": "🔬", "generate_story": "📚",
    "generate_script": "🎬", "generate_merch": "🎁",
    "mint_derivatives": "⛓️",
}

async def demo_progress_callback(plan, step):
    """Demo 专用进度回调"""
    step_id = getattr(step, 'id', '')
    icon = _step_icons.get(step_id, "⚙️")
    name = getattr(step, 'name', str(step))
    status = step.status.value if hasattr(step, 'status') and hasattr(step.status, 'value') else str(getattr(step, 'status', 'unknown'))
    
    status_colors = {"running": Color.CYAN, "success": Color.GREEN, "failed": Color.RED, "retrying": Color.YELLOW}
    color = status_colors.get(status, "")
    
    detail = ""
    if getattr(step, 'retry_count', 0) > 0:
        detail = f"(重试 {step.retry_count}/{step.max_retries})"
    if getattr(step, 'self_correction_notes', []):
        detail += f" [自我纠错: {step.self_correction_notes[-1][:30]}...]"
    
    print(f"  {icon} {Color.BOLD}{name}{Color.RESET} [{color}{status.upper()}{Color.RESET}] {Color.DIM}{detail}{Color.RESET}")


# ========== Demo 函数 ==========

async def demo_publish():
    """Demo 1: 链上出版 Agent"""
    print_header("📝 Demo 1: 链上出版 Agent — 自主完成从调研到上链的全流程")
    print(f"  {Color.DIM}展示能力：任务拆解 → 多步执行 → 质量自检 → 自我纠错 → 链上发布{Color.RESET}\n")

    orch = ChainScribeOrchestrator()
    result = await orch.execute(
        workflow=WorkflowType.PUBLISH,
        on_progress=demo_progress_callback,
        topic="Web3 创作者经济",
        content_type="research_report",
        unlock_price=0.01,
        max_words=3000,
    )

    print(f"\n  {Color.BOLD}📊 执行结果{Color.RESET}")
    print_result("工作流 ID", result.workflow_id)
    print_result("成功", "✅" if result.success else "⚠️")
    print_result("步骤", f"{result.steps_completed}/{result.steps_total}")
    print_result("耗时", f"{result.total_time}s")

    r = result.results
    plan = r.get("plan", {})
    if plan:
        print_result("自动重试", plan.get("total_retries", 0))
        print_result("自我纠错", plan.get("self_corrections", 0))

    pub = result.artifacts.get("nft_publication")
    if pub:
        print_result("NFT Token ID", pub.get("token_id"))
        print_result("交易哈希", pub.get("tx_hash", "")[:20] + "...")

    # 保存内容
    content = result.artifacts.get("published_content")
    if content:
        content_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(content_dir, exist_ok=True)
        with open(os.path.join(content_dir, "published_report.md"), "w") as f:
            f.write(content)
        print_result("内容已保存", "demo/output/published_report.md")

    return result


async def demo_narrative():
    """Demo 2: 动态 NFT 叙事引擎"""
    print_header("📖 Demo 2: 动态 NFT 叙事引擎 — 链上事件驱动的持续叙事")
    print(f"  {Color.DIM}展示能力：持续监听 → 模式识别 → 叙事生成 → 视觉更新 → 链上回写{Color.RESET}\n")

    orch = ChainScribeOrchestrator()
    result = await orch.execute(
        workflow=WorkflowType.NARRATIVE,
        on_progress=demo_progress_callback,
        token_id="1",
        title="链上觉醒",
        genre="sci-fi",
        total_chapters=5,
    )

    print(f"\n  {Color.BOLD}📊 叙事引擎结果{Color.RESET}")
    print_result("工作流 ID", result.workflow_id)
    print_result("成功", "✅" if result.success else "⚠️")
    print_result("步骤", f"{result.steps_completed}/{result.steps_total}")
    print_result("耗时", f"{result.total_time}s")

    chapters = result.artifacts.get("chapters", [])
    for ch_data in chapters:
        ch = ch_data.get("chapter", {})
        print(f"\n    {Color.CYAN}第 {ch.get('number', '?')} 章 — {ch.get('title', 'N/A')}{Color.RESET}")
        content = ch.get("content", "")
        print(f"    {Color.DIM}{content[:80]}...{Color.RESET}")

    # 保存
    content_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(content_dir, exist_ok=True)
    with open(os.path.join(content_dir, "narrative_history.json"), "w") as f:
        json.dump(result.artifacts, f, ensure_ascii=False, indent=2, default=str)
    print_result("叙事历史已保存", "demo/output/narrative_history.json")

    return result


async def demo_dao():
    """Demo 3: 创作者 DAO 协作系统"""
    print_header("🏛️ Demo 3: 创作者 DAO 协作 — 多 Agent 分工与自动分账")
    print(f"  {Color.DIM}展示能力：任务分配 → 并行执行 → 质量整合 → 链上发布 → 自动分账{Color.RESET}\n")

    orch = ChainScribeOrchestrator()
    result = await orch.execute(
        workflow=WorkflowType.DAO,
        on_progress=demo_progress_callback,
        title="DeFi 安全报告",
        goal="协作完成 DeFi 安全研究报告的调研、撰写、设计、发布与推广",
    )

    print(f"\n  {Color.BOLD}📊 DAO 协作结果{Color.RESET}")
    print_result("工作流 ID", result.workflow_id)
    print_result("成功", "✅" if result.success else "⚠️")
    print_result("步骤", f"{result.steps_completed}/{result.steps_total}")
    print_result("耗时", f"{result.total_time}s")

    r = result.results
    print_result("项目", r.get("title", "N/A"))
    
    for split in r.get("revenue_splits", []):
        print_result(f"  {split['label']}", f"{split['role']} | {split['share']}")

    for t in r.get("tasks_summary", []):
        icon = "✅" if t["status"] == "completed" else "⚠️"
        print(f"    {icon} [{t['agent']}] {t['description']}")

    # 保存
    content_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(content_dir, exist_ok=True)
    with open(os.path.join(content_dir, "dao_result.json"), "w") as f:
        json.dump(result.artifacts, f, ensure_ascii=False, indent=2, default=str)
    print_result("DAO 结果已保存", "demo/output/dao_result.json")

    return result


async def demo_ip_derivative():
    """Demo 4: IP 衍生内容 Agent"""
    print_header("🎨 Demo 4: IP 衍生内容 — 基于链上 IP 的风格一致衍生创作")
    print(f"  {Color.DIM}展示能力：IP 分析 → 风格提取 → 衍生故事 → 动画脚本 → 周边资产 → NFT 铸造{Color.RESET}\n")

    orch = ChainScribeOrchestrator()
    result = await orch.execute(
        workflow=WorkflowType.IP_DERIVATIVE,
        on_progress=demo_progress_callback,
        ip_name="CyberDragon",
        ip_style="cyberpunk",
        derivative_types=["story", "script", "merch"],
    )

    print(f"\n  {Color.BOLD}📊 IP 衍生结果{Color.RESET}")
    print_result("工作流 ID", result.workflow_id)
    print_result("成功", "✅" if result.success else "⚠️")
    print_result("步骤", f"{result.steps_completed}/{result.steps_total}")
    print_result("耗时", f"{result.total_time}s")

    for d in result.artifacts.get("derivatives", []):
        print(f"\n    {Color.CYAN}{d['type'].upper()}: {d['title']}{Color.RESET}")
        if d["type"] == "story":
            print(f"    {Color.DIM}{d['content'][:100]}...{Color.RESET}")
        elif d["type"] == "script":
            scenes = d.get("content", {}).get("scenes", []) if isinstance(d.get("content"), dict) else []
            print(f"    {Color.DIM}场景数: {len(scenes)}{Color.RESET}")
        elif d["type"] == "merch":
            items = d.get("content", {}).get("items", []) if isinstance(d.get("content"), dict) else []
            for item in items:
                print(f"    {Color.DIM}  - {item.get('name', 'N/A')} ({item.get('rarity', 'N/A')}){Color.RESET}")

    # 保存
    content_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(content_dir, exist_ok=True)
    with open(os.path.join(content_dir, "ip_derivatives.json"), "w") as f:
        json.dump(result.artifacts, f, ensure_ascii=False, indent=2, default=str)
    print_result("衍生内容已保存", "demo/output/ip_derivatives.json")

    return result


async def demo_full_pipeline():
    """Demo 5: 完整流水线"""
    print_header("🚀 Demo 5: 完整流水线 — 出版 → 叙事 → DAO → 衍生")
    print(f"  {Color.DIM}展示能力：四模块协同工作，共享基础设施，事件驱动{Color.RESET}\n")

    orch = ChainScribeOrchestrator()
    result = await orch.execute(
        workflow=WorkflowType.FULL_PIPELINE,
        on_progress=demo_progress_callback,
        topic="Web3 创作者经济",
        genre="sci-fi",
        ip_style="cyberpunk",
    )

    print(f"\n  {Color.BOLD}📊 完整流水线结果{Color.RESET}")
    print_result("工作流 ID", result.workflow_id)
    print_result("成功", "✅" if result.success else "⚠️")
    print_result("总步骤", f"{result.steps_completed}/{result.steps_total}")
    print_result("总耗时", f"{result.total_time}s")

    # 各模块结果摘要
    for key in ["publish", "narrative", "dao", "ip_derivative"]:
        if key in result.results:
            print_result(f"  {key}", "✅ 已完成")

    # 保存
    content_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(content_dir, exist_ok=True)
    with open(os.path.join(content_dir, "pipeline_result.json"), "w") as f:
        json.dump({
            "workflow_id": result.workflow_id,
            "success": result.success,
            "steps": f"{result.steps_completed}/{result.steps_total}",
            "time": result.total_time,
            "artifacts": {k: str(type(v).__name__) for k, v in result.artifacts.items()},
        }, f, ensure_ascii=False, indent=2)
    print_result("流水线结果已保存", "demo/output/pipeline_result.json")

    return result


# ========== 主函数 ==========

async def main():
    mode = "all"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║                                                            ║")
    print("  ║   ⚡ ChainScribe v2.0 — 统一编排器                        ║")
    print("  ║   AI 自主链上出版与动态 NFT 平台                          ║")
    print("  ║   Web3 × Long-Horizon Task | Z.AI 赛道                    ║")
    print("  ║                                                            ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print(f"{Color.RESET}")

    start_time = time.time()

    if mode in ("all", "publish"):
        await demo_publish()

    if mode in ("all", "narrative"):
        await demo_narrative()

    if mode in ("all", "dao"):
        await demo_dao()

    if mode in ("all", "ip"):
        await demo_ip_derivative()

    if mode == "pipeline":
        await demo_full_pipeline()

    elapsed = time.time() - start_time

    print(f"\n{'='*70}")
    print(f"{Color.GREEN}{Color.BOLD}  ✅ 全部 Demo 执行完成！{Color.RESET}")
    print(f"  ⏱️  总耗时: {elapsed:.2f}s")
    print(f"  📁 输出目录: demo/output/")
    print(f"{'='*70}\n")

    # 生成执行报告
    report = {
        "demo_completed": True,
        "version": "2.0",
        "mode": mode,
        "total_time": round(elapsed, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "architecture": "统一编排器 (Orchestrator) + 四模块 Agent",
        "features_demonstrated": [
            "长程自主执行 — Agent 自主拆解并执行多步骤复杂任务",
            "自我纠错 — 执行失败时自动分析原因并调整策略",
            "链上出版 — 从调研到上链的完整内容生产链路",
            "动态叙事 — 链上事件驱动的 NFT 叙事与视觉更新",
            "DAO 协作 — 多 Agent 分工协作与自动分账",
            "IP 衍生 — 风格一致的衍生内容生成",
            "统一编排 — 四模块共享基础设施、事件驱动协同",
        ],
    }

    content_dir = os.path.join(os.path.dirname(__file__), "output")
    with open(os.path.join(content_dir, "demo_report.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
