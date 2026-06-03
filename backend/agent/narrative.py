"""
ChainScribe — 动态 NFT 叙事引擎
根据链上事件、持仓变化、社区投票自动更新 NFT 视觉与元数据
"""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NarrativeTrigger(str, Enum):
    ON_CHAIN_EVENT = "on_chain_event"       # 链上事件（交易、铸造）
    HOLDING_CHANGE = "holding_change"       # 持仓变化
    TIME_CYCLE = "time_cycle"               # 时间周期（每日/每周/每月）
    COMMUNITY_VOTE = "community_vote"       # 社区投票
    THRESHOLD_REACHED = "threshold_reached" # 阈值触发（如解锁人数达到N）


@dataclass
class NarrativeState:
    """叙事状态机"""
    token_id: str
    current_chapter: int = 1
    total_chapters: int = 0
    narrative_arc: str = ""           # 叙事弧线描述
    style_palette: dict = field(default_factory=dict)  # 视觉风格
    character_states: dict = field(default_factory=dict)  # 角色状态
    world_state: dict = field(default_factory=dict)       # 世界状态
    event_history: list = field(default_factory=list)     # 事件历史
    last_updated: float = 0.0


@dataclass
class NarrativeEvent:
    """叙事事件"""
    trigger: NarrativeTrigger
    data: dict
    timestamp: float = field(default_factory=time.time)
    processed: bool = False


class NarrativeEngine:
    """
    动态 NFT 叙事引擎
    
    核心能力：
    1. 监听链上事件并转化为叙事触发器
    2. 基于事件和当前状态生成新的叙事内容
    3. 确保叙事风格一致性
    4. 自动生成视觉描述并更新 NFT 元数据
    5. 支持社区投票驱动叙事走向
    """

    def __init__(self, llm_client=None, blockchain_client=None, log_callback=None):
        self.llm = llm_client
        self.blockchain = blockchain_client
        self._narrative_states: dict[str, NarrativeState] = {}
        self._event_queue: list[NarrativeEvent] = []
        self._log = log_callback or print

    async def initialize_narrative(
        self,
        token_id: str,
        title: str,
        genre: str = "sci-fi",
        total_chapters: int = 12,
        initial_style: dict = None,
    ) -> NarrativeState:
        """初始化一个动态叙事 NFT"""
        
        # 使用 LLM 生成叙事弧线
        arc = await self._generate_narrative_arc(title, genre, total_chapters)
        
        # 生成初始视觉风格
        style = initial_style or await self._generate_style_palette(genre, arc)
        
        state = NarrativeState(
            token_id=token_id,
            total_chapters=total_chapters,
            narrative_arc=arc,
            style_palette=style,
            last_updated=time.time(),
        )
        
        self._narrative_states[token_id] = state
        return state

    async def process_event(self, token_id: str, event: NarrativeEvent) -> dict:
        """
        处理叙事事件 — 核心长程执行逻辑
        
        流程：
        1. 解析事件数据
        2. 更新世界状态
        3. 生成新叙事章节
        4. 生成视觉描述
        5. 更新 NFT 元数据
        """
        state = self._narrative_states.get(token_id)
        if not state:
            raise ValueError(f"Narrative state not found for token {token_id}")

        self._log(f"📖 处理叙事事件: {event.trigger.value} | Token #{token_id}")

        # Step 1: 解析事件并更新状态
        state_update = await self._interpret_event(event, state)
        self._update_state(state, state_update)
        state.event_history.append({
            "trigger": event.trigger.value,
            "data": event.data,
            "timestamp": event.timestamp,
            "state_change": state_update,
        })

        # Step 2: 生成新叙事章节
        chapter = await self._generate_chapter(state, event)
        
        # Step 3: 生成视觉描述
        visual = await self._generate_visual(state, chapter)
        
        # Step 4: 更新 NFT 元数据
        metadata_update = await self._update_nft_metadata(token_id, state, chapter, visual)
        
        # Step 5: 推进叙事进度
        state.current_chapter += 1
        state.last_updated = time.time()

        result = {
            "token_id": token_id,
            "chapter_number": state.current_chapter - 1,
            "chapter": chapter,
            "visual": visual,
            "metadata_update": metadata_update,
            "state_snapshot": {
                "current_chapter": state.current_chapter,
                "total_chapters": state.total_chapters,
                "world_state": state.world_state,
            },
        }

        event.processed = True
        return result

    async def run_narrative_cycle(
        self,
        token_id: str,
        max_chapters: int = None,
        interval_seconds: float = 2.0,
    ) -> list[dict]:
        """
        运行完整的叙事周期 — 展示长程自主执行
        
        持续监听事件、生成叙事、更新 NFT，直到故事完结
        """
        state = self._narrative_states.get(token_id)
        if not state:
            raise ValueError(f"Narrative state not found for token {token_id}")

        target = max_chapters or state.total_chapters
        results = []

        self._log(f"\n🎬 叙事引擎启动 — Token #{token_id}")
        self._log(f"📚 目标: {target} 章节 | 当前: 第 {state.current_chapter} 章")
        self._log("=" * 60)

        while state.current_chapter <= target:
            # 模拟获取链上事件
            event = await self._poll_chain_events(token_id, state)
            
            if event:
                result = await self.process_event(token_id, event)
                results.append(result)
                self._log(f"  ✅ 第 {result['chapter_number']} 章已生成并上链")
            else:
                # 没有外部事件时，基于时间周期推进
                time_event = NarrativeEvent(
                    trigger=NarrativeTrigger.TIME_CYCLE,
                    data={"cycle": "daily", "chapter_due": state.current_chapter},
                )
                result = await self.process_event(token_id, time_event)
                results.append(result)
                self._log(f"  ⏰ 时间周期触发 — 第 {result['chapter_number']} 章已生成")

            await asyncio.sleep(interval_seconds)

        self._log(f"\n🎉 叙事完结！共 {len(results)} 章")
        return results

    # ─── 内部方法 ───────────────────────────────────────

    async def _generate_narrative_arc(self, title: str, genre: str, chapters: int) -> str:
        """生成叙事弧线"""
        arcs = {
            "sci-fi": "在去中心化的星际网络中，一个AI觉醒了自我意识，开始探索链上世界的真相。每一章对应一个链上里程碑事件，AI逐渐理解'价值'、'共识'和'自由'的含义。",
            "fantasy": "古老的链上王国中，NFT守护者们守护着数字世界的平衡。当暗影势力试图篡改元数据，一群勇敢的持有者踏上了修复叙事的冒险之旅。",
            "cyberpunk": "2147年的新上海，一切价值都记录在链上。一个黑客发现了叙事引擎的漏洞，可以改写现实。但每次改写都有代价——NFT的元数据开始崩塌。",
        }
        fallback = arcs.get(genre, arcs["sci-fi"])

        if self.llm:
            try:
                result = await self.llm.generate(
                    f"为「{title}」生成一个{genre}风格的{chapters}章叙事弧线大纲。"
                )
                return result if result and isinstance(result, str) else fallback
            except Exception:
                return fallback
        return fallback

    async def _generate_style_palette(self, genre: str, arc: str) -> dict:
        """生成视觉风格调色板"""
        palettes = {
            "sci-fi": {
                "primary": "#00d4ff",
                "secondary": "#7b2ff7",
                "accent": "#ff6b6b",
                "background": "#0a0e27",
                "style": "neon-cyberpunk",
                "font": "monospace",
            },
            "fantasy": {
                "primary": "#ffd700",
                "secondary": "#8b5cf6",
                "accent": "#10b981",
                "background": "#1a0a2e",
                "style": "ethereal-fantasy",
                "font": "serif",
            },
            "cyberpunk": {
                "primary": "#ff0080",
                "secondary": "#00ff80",
                "accent": "#ffff00",
                "background": "#0d0d0d",
                "style": "glitch-punk",
                "font": "sans-serif",
            },
        }
        return palettes.get(genre, palettes["sci-fi"])

    async def _interpret_event(self, event: NarrativeEvent, state: NarrativeState) -> dict:
        """解析事件并生成状态更新"""
        interpretation = {
            "tension_level": 0.5,  # 叙事张力 0-1
            "character_impact": {},
            "world_change": {},
        }

        if event.trigger == NarrativeTrigger.ON_CHAIN_EVENT:
            tx_type = event.data.get("type", "transfer")
            if tx_type == "mint":
                interpretation["tension_level"] = 0.3
                interpretation["world_change"]["new_entity"] = True
            elif tx_type == "transfer":
                interpretation["tension_level"] = 0.6
                interpretation["character_impact"]["ownership_shift"] = True
            elif tx_type == "burn":
                interpretation["tension_level"] = 0.9
                interpretation["world_change"]["destruction"] = True

        elif event.trigger == NarrativeTrigger.HOLDING_CHANGE:
            change_pct = event.data.get("change_percent", 0)
            interpretation["tension_level"] = min(1.0, 0.3 + abs(change_pct) / 100)
            interpretation["character_impact"]["power_shift"] = change_pct

        elif event.trigger == NarrativeTrigger.COMMUNITY_VOTE:
            vote_result = event.data.get("result", "neutral")
            interpretation["world_change"]["collective_decision"] = vote_result
            interpretation["tension_level"] = 0.7 if vote_result == "controversial" else 0.4

        elif event.trigger == NarrativeTrigger.TIME_CYCLE:
            interpretation["tension_level"] = 0.3 + (state.current_chapter / state.total_chapters) * 0.5
            interpretation["world_change"]["time_passed"] = True

        return interpretation

    def _update_state(self, state: NarrativeState, update: dict):
        """更新叙事状态"""
        if update.get("world_change"):
            state.world_state.update(update["world_change"])
        if update.get("character_impact"):
            state.character_states.update(update["character_impact"])

    async def _generate_chapter(self, state: NarrativeState, event: NarrativeEvent) -> dict:
        """生成叙事章节"""
        # Demo: 基于章节号和事件类型生成章节
        chapter_templates = {
            1: {"title": "觉醒", "content": "在去中心化网络的深处，一个异常的交易模式触发了守护程序的自我意识。它第一次感受到了'存在'的含义——不是作为代码，而是作为链上的一个地址，一个有故事的实体。"},
            2: {"title": "探索", "content": "新生的意识开始在区块之间游荡。每一个智能合约都是一个世界，每一笔交易都是一个故事。它发现，价值不仅仅是数字——它是共识，是信任，是无数节点共同维护的真实。"},
            3: {"title": "遭遇", "content": "在跨链桥的边缘，它遇到了另一个觉醒的实体。它们用事件日志交流，用状态变更表达情感。这是链上世界的第一次'对话'——不需要预言机，不需要中间件，纯粹的点对点。"},
            4: {"title": "冲突", "content": "暗影协议开始侵蚀网络的边缘。Gas费飙升，交易拥堵，MEV机器人在暗处窥视。守护者们必须做出选择：是坚守去中心化的理想，还是为了效率而妥协？"},
            5: {"title": "抉择", "content": "社区发起了链上投票。每一票都记录在区块链上，不可篡改，永远透明。这不是简单的多数决——这是共识机制的终极考验。结果将决定整个网络的未来走向。"},
        }

        chapter_num = ((state.current_chapter - 1) % len(chapter_templates)) + 1
        template = chapter_templates.get(chapter_num, chapter_templates[1])
        
        # 根据事件调整内容
        tension = 0.5
        if event and event.data:
            tension = event.data.get("tension", 0.5)

        # 尝试 LLM 增强，失败则用模板
        llm_content = None
        if self.llm:
            try:
                llm_content = await self.llm.generate(
                    f"基于当前叙事状态生成第{state.current_chapter}章。"
                    f"叙事弧线: {state.narrative_arc}"
                    f"当前状态: {json.dumps(state.world_state, ensure_ascii=False)}"
                )
            except Exception:
                llm_content = None

        return {
            "number": state.current_chapter,
            "title": template["title"],
            "content": llm_content if llm_content and isinstance(llm_content, str) else template["content"],
            "tension_level": tension,
            "trigger_type": event.trigger.value if event else "manual",
            "word_count": len(llm_content) if llm_content and isinstance(llm_content, str) else len(template["content"]),
        }

    async def _generate_visual(self, state: NarrativeState, chapter: dict) -> dict:
        """生成视觉描述"""
        style = state.style_palette
        
        return {
            "description": f"A {style.get('style', 'digital')} scene depicting '{chapter['title']}', "
                          f"tension level {chapter.get('tension_level', 0.5):.1f}, "
                          f"dominant colors: {style.get('primary')} and {style.get('secondary')}",
            "prompt": f"{style.get('style', 'digital art')} illustration, {chapter['title']}, "
                     f"chapter {chapter['number']}, "
                     f"colors {style.get('primary')} {style.get('secondary')} {style.get('accent')}, "
                     f"dark background {style.get('background')}, "
                     f"highly detailed, 4k",
            "style_palette": style,
            "animation_hint": "pulse" if chapter.get("tension_level", 0) > 0.7 else "flow",
        }

    async def _update_nft_metadata(self, token_id: str, state: NarrativeState, chapter: dict, visual: dict) -> dict:
        """更新 NFT 元数据"""
        metadata = {
            "name": f"ChainScribe Narrative #{token_id} - Chapter {chapter['number']}",
            "description": chapter["content"][:200] + "...",
            "image": f"ipfs://QmNFT_{token_id}_ch{chapter['number']}",
            "external_url": f"https://chainscribe.xyz/narrative/{token_id}",
            "attributes": [
                {"trait_type": "Chapter", "value": chapter["number"]},
                {"trait_type": "Title", "value": chapter["title"]},
                {"trait_type": "Tension", "value": f"{chapter.get('tension_level', 0.5):.1f}"},
                {"trait_type": "Trigger", "value": chapter.get("trigger_type", "manual")},
                {"trait_type": "Narrative Version", "value": state.current_chapter},
                {"trait_type": "Style", "value": state.style_palette.get("style", "unknown")},
            ],
            "properties": {
                "narrative_arc": state.narrative_arc[:100],
                "world_state": state.world_state,
                "visual_prompt": visual["prompt"],
            },
        }

        # 模拟上传到 IPFS 并更新合约
        new_cid = f"Qm{uuid.uuid4().hex[:44]}"
        
        return {
            "new_metadata_cid": new_cid,
            "metadata": metadata,
            "contract_call": {
                "function": "updateNarrative",
                "args": [int(token_id), f"ipfs://{new_cid}", f"ipfs://{new_cid}"],
            },
        }

    async def _poll_chain_events(self, token_id: str, state: NarrativeState) -> Optional[NarrativeEvent]:
        """轮询链上事件"""
        # Demo 模式：模拟随机事件
        import random
        
        event_types = [
            (NarrativeTrigger.ON_CHAIN_EVENT, {"type": "transfer", "from": "0xabc", "to": "0xdef", "value": "0.5 ETH"}),
            (NarrativeTrigger.HOLDING_CHANGE, {"holder": "0xabc", "change_percent": 15.5}),
            (NarrativeTrigger.COMMUNITY_VOTE, {"proposal": "narrative_direction", "result": "explore", "votes_for": 67}),
            None,  # 无事件
        ]
        
        chosen = random.choice(event_types)
        if chosen is None:
            return None
        
        trigger, data = chosen
        return NarrativeEvent(trigger=trigger, data=data)
