"""
IP 衍生内容 Agent — 基于链上 IP 自主生成风格一致的衍生内容
"""
import json
import time
import asyncio
import hashlib
import random
from typing import Optional
from datetime import datetime

from ..core.engine import (
    LongHorizonEngine, ExecutionPlan, TaskStep, TaskStatus, TaskPriority
)


class IPDerivativeAgent:
    """
    IP 衍生内容 Agent
    
    基于已有链上 IP，自主生成：
    - 衍生故事（风格一致的续写/外传）
    - 动画脚本
    - 周边资产描述
    """

    # IP 风格库
    STYLE_TEMPLATES = {
        "cyberpunk": {
            "tone": "冷峻而富有张力",
            "vocabulary": ["霓虹", "数据流", "义体", "赛博空间", "黑客", "矩阵"],
            "visual_style": "高对比度、霓虹色调、故障艺术",
        },
        "fantasy": {
            "tone": "宏大而神秘",
            "vocabulary": ["符文", "远古", "守护者", "圣殿", "预言", "觉醒"],
            "visual_style": "梦幻色彩、光效粒子、古典纹样",
        },
        "scifi": {
            "tone": "理性而深邃",
            "vocabulary": ["量子", "维度", "奇点", "意识", "跃迁", "熵"],
            "visual_style": "极简线条、全息投影、数据可视化",
        },
    }

    def __init__(self):
        self.engine = LongHorizonEngine(agent_name="ChainScribe-IP")
        self.derivatives = []

        self.engine.register_tool("analyze_ip", self._tool_analyze_ip)
        self.engine.register_tool("generate_story", self._tool_generate_story)
        self.engine.register_tool("generate_script", self._tool_generate_script)
        self.engine.register_tool("generate_merch", self._tool_generate_merch)
        self.engine.register_tool("mint_derivatives", self._tool_mint_derivatives)

    async def create_derivatives(
        self,
        ip_name: str,
        ip_style: str = "cyberpunk",
        derivative_types: list[str] = None,
        on_progress=None,
    ) -> dict:
        """
        基于 IP 生成衍生内容
        
        Args:
            ip_name: 原始 IP 名称
            ip_style: 风格 (cyberpunk / fantasy / scifi)
            derivative_types: 衍生类型列表
        """
        if derivative_types is None:
            derivative_types = ["story", "script", "merch"]

        self.engine.on_step_update = on_progress
        plan = self._build_derivative_plan(ip_name, ip_style, derivative_types)
        result_plan = await self.engine.execute_plan(plan)

        return {
            "ip_name": ip_name,
            "ip_style": ip_style,
            "plan": result_plan.to_dict(),
            "derivatives": self.derivatives,
            "execution_summary": self.engine.get_execution_summary(),
        }

    def _build_derivative_plan(self, ip_name: str, ip_style: str, derivative_types: list) -> ExecutionPlan:
        plan = ExecutionPlan(goal=f"基于 '{ip_name}' ({ip_style}) 生成衍生内容")

        steps = [
            TaskStep(
                id="analyze_ip",
                name="IP 风格分析",
                description=f"分析 {ip_name} 的核心风格元素、叙事模式、视觉特征",
                priority=TaskPriority.CRITICAL,
                max_retries=2,
            ),
        ]

        if "story" in derivative_types:
            steps.append(TaskStep(
                id="generate_story",
                name="衍生故事生成",
                description="生成风格一致的衍生故事章节",
                priority=TaskPriority.HIGH,
                max_retries=3,
                dependencies=["analyze_ip"],
            ))

        if "script" in derivative_types:
            steps.append(TaskStep(
                id="generate_script",
                name="动画脚本生成",
                description="生成动画分镜脚本",
                priority=TaskPriority.HIGH,
                max_retries=3,
                dependencies=["analyze_ip"],
            ))

        if "merch" in derivative_types:
            steps.append(TaskStep(
                id="generate_merch",
                name="周边资产生成",
                description="生成周边资产描述与视觉方案",
                priority=TaskPriority.MEDIUM,
                max_retries=2,
                dependencies=["analyze_ip"],
            ))

        steps.append(TaskStep(
            id="mint_derivatives",
            name="铸造衍生 NFT",
            description="将衍生内容铸造为 NFT 系列",
            priority=TaskPriority.CRITICAL,
            max_retries=3,
            dependencies=[s.id for s in steps[1:]],  # 依赖所有生成步骤
        ))

        plan.steps = steps
        return plan

    async def _tool_analyze_ip(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """分析 IP 风格"""
        await asyncio.sleep(0.1)
        ip_name = plan.goal.split("'")[1] if "'" in plan.goal else "Unknown"
        ip_style = plan.goal.split("(")[1].split(")")[0] if "(" in plan.goal else "cyberpunk"

        style = self.STYLE_TEMPLATES.get(ip_style, self.STYLE_TEMPLATES["cyberpunk"])

        analysis = {
            "ip_name": ip_name,
            "style": ip_style,
            "tone": style["tone"],
            "key_vocabulary": style["vocabulary"],
            "visual_style": style["visual_style"],
            "narrative_patterns": ["英雄之旅", "觉醒与蜕变", "对抗与和解"],
            "consistency_score": random.uniform(0.85, 0.98),
        }

        step.tool_calls.append({"tool": "ip_analyzer", "style": ip_style})
        return analysis

    async def _tool_generate_story(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """生成衍生故事"""
        await asyncio.sleep(0.2)
        ip_name = plan.goal.split("'")[1] if "'" in plan.goal else "Unknown"
        ip_style = plan.goal.split("(")[1].split(")")[0] if "(" in plan.goal else "cyberpunk"
        style = self.STYLE_TEMPLATES.get(ip_style, self.STYLE_TEMPLATES["cyberpunk"])

        vocab = style["vocabulary"]
        story = f"""# {ip_name}：{random.choice(['暗流', '觉醒', '裂隙', '回响'])}

## 第一章：{random.choice(vocab)}之影

在{ip_name}的世界深处，一股暗流正在涌动。{random.choice(vocab)}的痕迹出现在最不可能的地方，
而那些被遗忘的{random.choice(vocab)}开始重新苏醒。

"你感受到了吗？"守夜人低声问道，目光穿透{random.choice(vocab)}的迷雾。

远处的{random.choice(vocab)}发出低沉的共鸣，仿佛在回应某种古老的召唤。

## 第二章：{random.choice(vocab)}之约

三个陌生人，三个不同的{random.choice(vocab)}，却因为同一个{random.choice(vocab)}而命运交织。
他们不知道的是，这次相遇将改变{ip_name}世界的走向——

{random.choice(vocab)}的预言正在应验，而时间比任何人想象的都要紧迫。

## 第三章：{random.choice(vocab)}之战

当{random.choice(vocab)}的力量达到临界点，{ip_name}迎来了前所未有的挑战。
旧秩序崩塌，新规则尚未建立，一切都在{random.choice(vocab)}的边缘摇摇欲坠。

> "在{random.choice(vocab)}的尽头，我们终将找到答案——或者成为答案本身。"
"""

        derivative = {
            "type": "story",
            "title": f"{ip_name}：衍生故事",
            "content": story,
            "word_count": len(story),
            "style_consistency": random.uniform(0.88, 0.96),
        }

        self.derivatives.append(derivative)
        step.tool_calls.append({"tool": "story_generator", "chapters": 3})
        return derivative

    async def _tool_generate_script(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """生成动画脚本"""
        await asyncio.sleep(0.2)
        ip_name = plan.goal.split("'")[1] if "'" in plan.goal else "Unknown"

        script = {
            "type": "animation_script",
            "title": f"{ip_name} — 动画短片脚本",
            "duration": "3-5分钟",
            "scenes": [
                {
                    "scene": 1,
                    "setting": "开场 — 远景俯瞰",
                    "action": "镜头从高空缓缓下降，展现{ip_name}世界的全貌。{ip_name}的标志性建筑在晨光中闪耀。",
                    "dialogue": "（旁白）在这个世界的每一个角落，故事都在发生。",
                    "visual_note": "广角镜头，渐变色调，粒子效果",
                },
                {
                    "scene": 2,
                    "setting": "中景 — 主角登场",
                    "action": "主角从阴影中走出，目光坚定。背景是繁忙的{ip_name}街道。",
                    "dialogue": "主角：'是时候了。'",
                    "visual_note": "特写转中景，光影对比强烈",
                },
                {
                    "scene": 3,
                    "setting": "高潮 — 对决",
                    "action": "主角面对最终挑战，力量觉醒。特效全开，视觉冲击。",
                    "dialogue": "（无对白，纯动作与音乐）",
                    "visual_note": "快速剪辑，特效密集，色彩饱和度拉满",
                },
            ],
        }

        derivative = {
            "type": "script",
            "title": script["title"],
            "content": script,
            "scenes": len(script["scenes"]),
        }

        self.derivatives.append(derivative)
        step.tool_calls.append({"tool": "script_generator", "scenes": 3})
        return derivative

    async def _tool_generate_merch(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """生成周边资产"""
        await asyncio.sleep(0.15)
        ip_name = plan.goal.split("'")[1] if "'" in plan.goal else "Unknown"

        merch = {
            "type": "merchandise",
            "items": [
                {
                    "name": f"{ip_name} 限定徽章",
                    "description": "精铸金属徽章，镌刻{ip_name}核心图腾",
                    "rarity": "稀有",
                    "edition": 100,
                },
                {
                    "name": f"{ip_name} 角色立牌",
                    "description": "亚克力材质，全彩印刷，含专属底座",
                    "rarity": "普通",
                    "edition": 500,
                },
                {
                    "name": f"{ip_name} 原画集 NFT",
                    "description": "收录创作过程中的珍贵原画，含创作笔记",
                    "rarity": "传说",
                    "edition": 10,
                },
            ],
        }

        derivative = {
            "type": "merch",
            "title": f"{ip_name} 周边资产",
            "content": merch,
            "items": len(merch["items"]),
        }

        self.derivatives.append(derivative)
        step.tool_calls.append({"tool": "merch_generator", "items": len(merch["items"])})
        return derivative

    async def _tool_mint_derivatives(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """铸造衍生 NFT"""
        await asyncio.sleep(0.2)

        minted = []
        for i, d in enumerate(self.derivatives):
            nft = {
                "derivative_type": d["type"],
                "token_id": i + 1,
                "cid": "Qm" + hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:44],
                "tx_hash": "0x" + hashlib.sha256(f"{d['type']}{time.time()}{i}".encode()).hexdigest()[:64],
            }
            minted.append(nft)

        step.tool_calls.append({"tool": "nft_minter", "count": len(minted)})
        return {"minted": minted, "total": len(minted)}
