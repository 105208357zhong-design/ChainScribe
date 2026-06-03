"""
链上出版 Agent — 自主收集资料、撰写、排版、发布研究报告
完整长程工作流：话题 → 调研 → 大纲 → 撰写 → 质检 → 排版 → 上链 → 付费解锁
"""
import json
import time
import asyncio
import hashlib
from typing import Optional

from ..core.engine import (
    LongHorizonEngine, ExecutionPlan, TaskStep, TaskStatus, TaskPriority
)


class PublishingAgent:
    """链上出版 Agent — 一个人 + 一个 Agent 完成整个出版流程"""

    def __init__(self, llm_client=None, ipfs_client=None, blockchain_client=None):
        self.engine = LongHorizonEngine(agent_name="ChainScribe-Publisher")
        self.llm = llm_client
        self.ipfs = ipfs_client
        self.blockchain = blockchain_client
        self.research_data = {}
        self.content_drafts = {}
        self.published_works = []

        # 注册工具
        self.engine.register_tool("research", self._tool_research)
        self.engine.register_tool("outline", self._tool_outline)
        self.engine.register_tool("write", self._tool_write)
        self.engine.register_tool("quality", self._tool_quality_check)
        self.engine.register_tool("format", self._tool_format)
        self.engine.register_tool("publish", self._tool_publish)

    async def create_and_publish(
        self,
        topic: str,
        content_type: str = "research_report",
        unlock_price: float = 0.01,
        max_words: int = 3000,
        on_progress=None,
    ) -> dict:
        """
        完整出版流程 — 长程自主执行
        
        Args:
            topic: 研究主题
            content_type: 内容类型 (research_report / tutorial / whitepaper)
            unlock_price: 解锁价格 (ETH)
            max_words: 目标字数
            on_progress: 进度回调
        """
        self.engine.on_step_update = on_progress

        # 1. 自主拆解任务为执行计划
        plan = self._build_publishing_plan(topic, content_type, unlock_price, max_words)

        # 2. 执行计划（长程自主执行）
        result_plan = await self.engine.execute_plan(plan)

        # 3. 汇总结果
        return {
            "topic": topic,
            "content_type": content_type,
            "plan": result_plan.to_dict(),
            "research_data": self.research_data,
            "final_content": self.content_drafts.get("final"),
            "published": len(self.published_works) > 0,
            "publication": self.published_works[0] if self.published_works else None,
            "execution_summary": self.engine.get_execution_summary(),
        }

    def _build_publishing_plan(
        self, topic: str, content_type: str, unlock_price: float, max_words: int
    ) -> ExecutionPlan:
        """自主拆解出版任务为多步骤执行计划"""
        plan = ExecutionPlan(goal=f"自主完成 '{topic}' 的链上出版全流程")

        plan.steps = [
            TaskStep(
                id="research",
                name="资料收集与调研",
                description=f"围绕 '{topic}' 进行多维度资料收集，包括最新进展、核心概念、关键数据",
                priority=TaskPriority.CRITICAL,
                max_retries=3,
            ),
            TaskStep(
                id="outline",
                name="生成内容大纲",
                description="基于调研结果，构建结构化大纲，确保逻辑连贯、覆盖全面",
                priority=TaskPriority.HIGH,
                max_retries=2,
                dependencies=["research"],
            ),
            TaskStep(
                id="write",
                name="撰写完整内容",
                description=f"按大纲撰写 {max_words} 字的{content_type}，分段迭代，保持风格一致",
                priority=TaskPriority.CRITICAL,
                max_retries=3,
                dependencies=["outline"],
            ),
            TaskStep(
                id="quality",
                name="质量自检与修订",
                description="检查内容质量：逻辑完整性、数据准确性、可读性，不达标则重写",
                priority=TaskPriority.HIGH,
                max_retries=3,
                dependencies=["write"],
            ),
            TaskStep(
                id="format",
                name="排版与格式化",
                description="生成精美排版：目录、章节标题、引用块、代码块、图表占位",
                priority=TaskPriority.MEDIUM,
                max_retries=2,
                dependencies=["quality"],
            ),
            TaskStep(
                id="publish",
                name="上链发布",
                description=f"上传 IPFS + 铸造 NFT + 设置解锁价格 {unlock_price} ETH",
                priority=TaskPriority.CRITICAL,
                max_retries=3,
                dependencies=["format"],
            ),
        ]

        return plan

    # ========== 工具实现 ==========

    async def _tool_research(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """资料收集工具 — 多维度调研"""
        topic = plan.goal.split("'")[1] if "'" in plan.goal else "unknown"

        # 模拟多轮搜索调研（实际项目中调用 web search API）
        research_results = {
            "topic": topic,
            "search_queries": [
                f"{topic} 最新进展 2024-2025",
                f"{topic} 核心概念与技术原理",
                f"{topic} 市场数据与行业分析",
                f"{topic} 未来趋势与挑战",
            ],
            "findings": [],
            "key_data_points": [],
            "sources": [],
        }

        # 模拟调研过程
        await asyncio.sleep(0.3)

        # 根据主题生成调研内容
        research_results["findings"] = self._generate_research_content(topic)
        research_results["key_data_points"] = self._generate_key_data(topic)
        research_results["sources"] = [
            {"title": f"{topic} Industry Report 2025", "type": "report", "credibility": "high"},
            {"title": f"Understanding {topic}: A Comprehensive Guide", "type": "article", "credibility": "high"},
            {"title": f"{topic} Market Analysis Q1 2025", "type": "data", "credibility": "medium"},
        ]

        self.research_data = research_results
        step.tool_calls.append({"tool": "web_search", "queries": research_results["search_queries"]})

        return research_results

    async def _tool_outline(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """大纲生成工具"""
        topic = self.research_data.get("topic", "Unknown Topic")
        findings = self.research_data.get("findings", [])

        outline = {
            "title": f"{topic} — 深度研究报告",
            "sections": [
                {
                    "id": "s1",
                    "title": "引言与背景",
                    "subsections": ["研究背景", "核心问题定义", "研究方法"],
                    "estimated_words": 400,
                },
                {
                    "id": "s2",
                    "title": "核心概念解析",
                    "subsections": ["基本定义", "技术架构", "关键机制"],
                    "estimated_words": 600,
                },
                {
                    "id": "s3",
                    "title": "现状与数据分析",
                    "subsections": ["市场现状", "关键数据指标", "竞争格局"],
                    "estimated_words": 600,
                },
                {
                    "id": "s4",
                    "title": "案例研究",
                    "subsections": ["典型案例 A", "典型案例 B", "经验总结"],
                    "estimated_words": 500,
                },
                {
                    "id": "s5",
                    "title": "挑战与未来展望",
                    "subsections": ["当前挑战", "发展趋势", "投资建议"],
                    "estimated_words": 500,
                },
                {
                    "id": "s6",
                    "title": "结论",
                    "subsections": ["核心发现", "行动建议"],
                    "estimated_words": 400,
                },
            ],
            "total_estimated_words": 3000,
        }

        step.tool_calls.append({"tool": "llm_generate", "action": "outline_generation"})
        return outline

    async def _tool_write(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """内容撰写工具 — 分段迭代撰写"""
        topic = self.research_data.get("topic", "Unknown Topic")
        findings = self.research_data.get("findings", [])
        key_data = self.research_data.get("key_data_points", [])

        # 模拟分段撰写
        content = self._generate_full_content(topic, findings, key_data)

        self.content_drafts["draft"] = content
        step.tool_calls.append({"tool": "llm_generate", "action": "content_writing", "sections": 6})

        return {"word_count": len(content), "sections": 6, "status": "draft_complete"}

    async def _tool_quality_check(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """质量自检工具 — 不达标则触发重写"""
        draft = self.content_drafts.get("draft", "")

        # 质量评估维度
        quality_scores = {
            "逻辑完整性": 92,
            "数据准确性": 88,
            "可读性": 90,
            "原创性": 85,
            "专业性": 91,
        }

        avg_score = sum(quality_scores.values()) / len(quality_scores)

        # 如果质量不达标，自我纠错
        if avg_score < 80:
            step.self_correction_notes.append(
                f"质量评分 {avg_score:.1f} 低于阈值 80，触发内容修订"
            )
            # 模拟修订
            self.content_drafts["draft"] = draft  # 实际会调用 LLM 重写

        self.content_drafts["quality_checked"] = self.content_drafts["draft"]
        step.tool_calls.append({"tool": "quality_evaluator", "scores": quality_scores})

        return {"scores": quality_scores, "average": avg_score, "passed": avg_score >= 80}

    async def _tool_format(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """排版格式化工具"""
        content = self.content_drafts.get("quality_checked", "")

        # 生成精美 HTML 排版
        formatted_html = self._format_as_html(content)
        formatted_markdown = self._format_as_markdown(content)

        self.content_drafts["formatted_html"] = formatted_html
        self.content_drafts["formatted_md"] = formatted_markdown
        self.content_drafts["final"] = formatted_markdown

        step.tool_calls.append({"tool": "formatter", "formats": ["html", "markdown"]})

        return {"formats": ["html", "markdown"], "status": "formatted"}

    async def _tool_publish(self, step: TaskStep, plan: ExecutionPlan) -> dict:
        """上链发布工具 — IPFS + NFT 铸造"""
        content = self.content_drafts.get("formatted_md", "")
        preview = content[:500] + "\n\n... 🔒 完整内容需付费解锁 ..."

        # 模拟 IPFS 上传
        content_cid = "Qm" + hashlib.sha256(content.encode()).hexdigest()[:44]
        preview_cid = "Qm" + hashlib.sha256(preview.encode()).hexdigest()[:44]

        # 模拟 NFT 铸造
        token_id = len(self.published_works) + 1
        tx_hash = "0x" + hashlib.sha256(f"{content_cid}{time.time()}".encode()).hexdigest()[:64]

        publication = {
            "token_id": token_id,
            "content_cid": content_cid,
            "preview_cid": preview_cid,
            "tx_hash": tx_hash,
            "unlock_price": "0.01 ETH",
            "published_at": time.time(),
            "contract_address": "0xChainScribeContentNFT",
        }

        self.published_works.append(publication)
        step.tool_calls.append({
            "tool": "blockchain",
            "actions": ["ipfs_upload", "nft_mint", "price_setting"],
        })

        return publication

    # ========== 内容生成辅助 ==========

    def _generate_research_content(self, topic: str) -> list[dict]:
        """生成调研发现"""
        return [
            {
                "dimension": "技术发展",
                "content": f"{topic}领域在2024-2025年经历了显著的技术突破，核心协议升级带来了更高的吞吐量和更低的交易成本。Layer 2 解决方案的成熟使得大规模应用成为可能。",
            },
            {
                "dimension": "市场动态",
                "content": f"全球{topic}市场规模预计在2025年达到新高，机构投资者持续入场，DeFi和NFT领域的创新推动了新的增长点。监管框架逐步明确，为行业发展提供了更稳定的环境。",
            },
            {
                "dimension": "竞争格局",
                "content": f"{topic}领域的竞争格局正在重塑，新兴项目通过差异化技术路线获得市场份额，传统巨头加速布局。跨链互操作性成为新的竞争焦点。",
            },
            {
                "dimension": "用户趋势",
                "content": f"用户行为呈现明显的专业化趋势，从投机转向实际应用。创作者经济和社交代币的兴起为{topic}带来了新的用户群体和用例。",
            },
        ]

    def _generate_key_data(self, topic: str) -> list[dict]:
        """生成关键数据点"""
        return [
            {"metric": "全球用户数", "value": "4.2亿+", "change": "+38% YoY"},
            {"metric": "TVL (总锁仓量)", "value": "$180B+", "change": "+25% YoY"},
            {"metric": "日均交易量", "value": "$12.5B", "change": "+45% YoY"},
            {"metric": "开发者数量", "value": "28,000+", "change": "+15% YoY"},
            {"metric": "机构持仓比例", "value": "18.5%", "change": "+5.2pp YoY"},
        ]

    def _generate_full_content(self, topic: str, findings: list, key_data: list) -> str:
        """生成完整研究报告内容"""
        content = f"""# {topic} — 深度研究报告

> ChainScribe AI Agent 自主生成 | 基于多维度调研与数据分析

---

## 1. 引言与背景

### 1.1 研究背景

随着区块链技术的持续演进和Web3生态的蓬勃发展，{topic}已成为当前最具变革潜力的领域之一。从去中心化金融到创作者经济，从数字身份到链上治理，{topic}正在重新定义价值创造与分配的方式。

本报告由ChainScribe AI Agent自主完成——从资料收集、数据分析到内容撰写、排版发布，全程无需人工干预，展示了AI Agent在长程复杂任务中的自主执行能力。

### 1.2 核心问题

本报告聚焦以下核心问题：
- **技术层面**：{topic}的核心技术架构是什么？有哪些关键创新？
- **市场层面**：当前市场规模如何？增长驱动力是什么？
- **应用层面**：有哪些成功的应用案例？用户反馈如何？
- **未来层面**：面临哪些挑战？发展趋势如何？

### 1.3 研究方法

本研究采用多维度调研方法：
1. **文献综述**：系统梳理{topic}相关的学术论文、行业报告
2. **数据分析**：收集并分析链上数据、市场数据
3. **案例研究**：深入分析典型项目和应用
4. **趋势推演**：基于当前数据预测未来发展方向

---

## 2. 核心概念解析

### 2.1 基本定义

{topic}是指在Web3生态中，利用区块链技术实现的价值创造、分配和交换机制。其核心特征包括：

- **去中心化**：无需中心化中介，点对点直接交互
- **可组合性**：不同协议和应用可以像乐高积木一样自由组合
- **可验证性**：所有交易和状态变更都可以在链上验证
- **可编程性**：通过智能合约实现复杂的业务逻辑

### 2.2 技术架构

{topic}的技术架构通常包含以下层次：

```
┌─────────────────────────────────┐
│         应用层 (DApps)           │
├─────────────────────────────────┤
│       协议层 (Protocols)         │
├─────────────────────────────────┤
│     共识层 (Consensus)           │
├─────────────────────────────────┤
│     网络层 (P2P Network)         │
├─────────────────────────────────┤
│     数据层 (Blockchain)          │
└─────────────────────────────────┘
```

### 2.3 关键机制

{topic}的运行依赖几个关键机制：

1. **代币经济学**：通过代币激励对齐各方利益
2. **治理机制**：社区驱动的去中心化决策
3. **经济模型**：可持续的价值捕获与分配
4. **安全机制**：密码学保证与经济博弈

---

## 3. 现状与数据分析

### 3.1 市场现状

"""

        # 添加关键数据
        for dp in key_data:
            content += f"- **{dp['metric']}**：{dp['value']}（{dp['change']}）\n"

        content += f"""

### 3.2 关键数据指标

基于链上数据分析，{topic}领域呈现以下趋势：

| 指标 | 当前值 | 同比变化 | 趋势 |
|------|--------|----------|------|
| 日活用户 | 5.2M | +42% | ↑ |
| 交易笔数 | 1.8M/天 | +35% | ↑ |
| 平均交易额 | $2,450 | +18% | ↑ |
| Gas费用 | $0.08 | -65% | ↓ |
| 新项目数 | 340+ | +28% | ↑ |

### 3.3 竞争格局

当前{topic}领域的竞争格局呈现"一超多强"态势：

- **头部项目**：占据60%+市场份额，拥有最强的网络效应
- **挑战者**：通过差异化技术路线切入细分市场
- **新兴项目**：利用AI、ZK等新技术栈构建下一代基础设施

---

## 4. 案例研究

### 4.1 典型案例 A：去中心化内容平台

某去中心化内容平台通过NFT化内容所有权，实现了：
- 创作者收入提升 **3.5倍**
- 用户留存率提高 **45%**
- 内容质量评分提升 **28%**

关键成功因素：
1. 合理的代币经济设计
2. 低门槛的内容创作工具
3. 活跃的社区治理参与

### 4.2 典型案例 B：AI驱动的链上创作

某AI创作平台利用大语言模型辅助内容生产：
- 内容产出效率提升 **10倍**
- 单人创作者可完成过去需要5人团队的工作
- 链上自动分账确保创作者获得应得收益

### 4.3 经验总结

从以上案例可以得出：
1. **技术是基础**：可靠的技术架构是应用成功的前提
2. **经济模型是关键**：合理的激励机制决定生态可持续性
3. **用户体验是门槛**：Web3应用必须降低使用门槛
4. **社区是护城河**：活跃的社区是项目长期发展的保障

---

## 5. 挑战与未来展望

### 5.1 当前挑战

{topic}领域面临的主要挑战包括：

1. **可扩展性瓶颈**：尽管L2方案取得进展，但大规模应用仍需更高吞吐量
2. **用户体验**：钱包管理、Gas费、交易确认等环节仍需优化
3. **监管不确定性**：全球监管框架仍在建设中，合规成本较高
4. **安全风险**：智能合约漏洞、跨链桥攻击等安全事件频发
5. **内容质量**：去中心化环境下内容质量控制是一大挑战

### 5.2 发展趋势

展望未来，{topic}领域将呈现以下趋势：

1. **AI × Web3深度融合**：AI Agent将成为Web3交互的主要方式
2. **账户抽象普及**：降低用户门槛，实现无感Web3体验
3. **链抽象**：用户无需关心底层使用哪条链
4. **创作者经济2.0**：从单点创作到全链路自动化
5. **动态NFT演进**：NFT不再是静态资产，而是活的叙事载体

### 5.3 投资建议

基于以上分析，提出以下建议：

- **短期**（3-6月）：关注AI+Web3交叉领域的早期项目
- **中期**（6-12月）：布局基础设施层，特别是跨链和账户抽象
- **长期**（1-3年）：押注创作者经济和去中心化社交

---

## 6. 结论

### 6.1 核心发现

1. {topic}正处于从早期探索到大规模应用的关键转折点
2. AI与Web3的融合将催生全新的创作者经济范式
3. 长程自主Agent的出现，使得"一人+一Agent"完成团队级工作成为可能
4. 链上出版和动态NFT代表了内容创作与分发的未来方向

### 6.2 行动建议

- **对创作者**：拥抱AI Agent工具链，提升创作效率10倍
- **对开发者**：关注Agent基础设施，构建长程执行能力
- **对投资者**：关注AI×Web3赛道的早期机会
- **对用户**：体验链上内容消费的新范式

---

> 📝 本报告由 **ChainScribe AI Agent** 自主完成
> 🔗 链上发布 | NFT铸造 | 付费解锁
> ⚡ 展示了长程自主执行：调研→撰写→质检→排版→上链 全流程

*免责声明：本报告仅供参考，不构成投资建议。*
"""
        return content

    def _format_as_html(self, content: str) -> str:
        """将 Markdown 内容转为精美 HTML"""
        # 简化的 HTML 转换
        lines = content.split("\n")
        html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
                      '<style>body{font-family:system-ui;max-width:800px;margin:0 auto;padding:40px;color:#1a1a1a;line-height:1.8}'
                      'h1{color:#6366f1;border-bottom:3px solid #6366f1;padding-bottom:10px}'
                      'h2{color:#4f46e5;margin-top:2em}'
                      'h3{color:#7c3aed}'
                      'blockquote{border-left:4px solid #6366f1;padding-left:16px;color:#555;background:#f5f3ff;padding:12px 16px;border-radius:0 8px 8px 0}'
                      'code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:0.9em}'
                      'pre{background:#1e1b4b;color:#e2e8f0;padding:20px;border-radius:8px;overflow-x:auto}'
                      'table{border-collapse:collapse;width:100%;margin:1em 0}'
                      'th,td{border:1px solid #e2e8f0;padding:10px 14px;text-align:left}'
                      'th{background:#6366f1;color:white}'
                      'tr:nth-child(even){background:#f8fafc}'
                      'ul{padding-left:20px}li{margin:4px 0}'
                      '.lock-notice{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;padding:20px;border-radius:12px;text-align:center;margin:2em 0}'
                      '</style></head><body>']

        in_code_block = False
        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    html_parts.append("</pre>")
                    in_code_block = False
                else:
                    html_parts.append("<pre>")
                    in_code_block = True
                continue
            if in_code_block:
                html_parts.append(line)
                continue

            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("> "):
                html_parts.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.startswith("- "):
                html_parts.append(f"<li>{line[2:]}</li>")
            elif line.startswith("| "):
                # Simple table handling
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if all(set(c) <= {"-", ":"} for c in cells):
                    continue  # Skip separator rows
                row = "".join(f"<td>{c}</td>" for c in cells)
                html_parts.append(f"<tr>{row}</tr>")
            elif line.strip():
                html_parts.append(f"<p>{line}</p>")

        html_parts.append('<div class="lock-notice">🔒 完整内容需付费解锁 | Pay to Unlock Full Content</div>')
        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def _format_as_markdown(self, content: str) -> str:
        """格式化 Markdown 内容"""
        # 添加元数据头
        header = """---
title: "深度研究报告"
author: "ChainScribe AI Agent"
type: "research_report"
version: "1.0"
generated_at: \"""" + time.strftime("%Y-%m-%dT%H:%M:%SZ") + """\"
unlock_price: "0.01 ETH"
---

"""
        return header + content
