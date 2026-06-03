# ⚡ ChainScribe — AI 自主链上出版与动态 NFT 平台

> **Web3 × Long-Horizon Task | Z.AI 赛道**
> 一个人 + 一个 Agent = 整个创作团队

## 🎯 项目定位

ChainScribe 是一个 AI 驱动的链上内容创作与发布平台，核心展示 **GLM-5.1 的长程自主任务执行能力**。Agent 不只是回答问题，而是能自主拆解复杂任务、制定多步骤计划、持续调用工具、迭代修复，并完成从需求到交付的完整 Web3 工作流。

## 🏗️ 系统架构

```
用户输入话题
    ↓
🎯 Orchestrator（统一编排器）— 共享 LLM/IPFS/Blockchain 基础设施
    ↓
┌─────────────────────────────────────────────────┐
│  📝 Publishing Agent    → 调研→撰写→排版→上链    │
│  📖 Narrative Engine    → 监听→叙事→视觉→回写    │
│  🏛️ Creator DAO         → 拆解→协作→发布→分账    │
│  🎨 IP Derivative Agent → 分析→衍生→铸造→上架    │
│  🔗 Full Pipeline       → 出版→叙事→衍生 全链路  │
└─────────────────────────────────────────────────┘
    ↓  （所有模块共享 LongHorizonEngine + GLM-5.1）
⛓️ Smart Contracts (ContentNFT + CreatorDAO)
    ↓
📦 IPFS/Arweave + Ethereum/Polygon
```

## 🚀 四大核心能力

### 1. 📝 链上出版 Agent
自主完成从调研到上链的完整内容生产链路：
- 🔍 资料收集与调研（多轮搜索、关键词迭代）
- 📋 生成内容大纲（自主拆解子主题）
- ✍️ 撰写完整内容（分段迭代、质量自检）
- 🎨 排版与格式化（Markdown/HTML/PDF）
- 📤 上链发布（IPFS 存储 + NFT 铸造）
- 💰 付费解锁（智能合约自动结算）

### 2. 📖 动态 NFT 叙事引擎
根据链上事件自动更新 NFT 视觉与元数据：
- 🔗 监听链上事件（交易、铸造、持仓变化）
- 🧠 模式识别（价格波动、社区投票、时间周期）
- 📖 叙事生成（每章对应一个链上里程碑）
- 🖼️ 视觉更新（SVG 动态生成，风格随叙事演变）
- ⛓️ 链上回写（更新 NFT 元数据与 tokenURI）

### 3. 🏛️ 创作者 DAO 协作系统
多 Agent 分工协作与自动分账：
- 📋 任务拆解与分配（Coordinator 自动分解）
- 🤖 7 个专业 Agent 并行执行（调研/写作/设计/发布/推广/财务）
- ✅ 质量整合与审查
- ⛓️ 链上发布与 NFT 铸造
- 💰 自动分账（按贡献比例分配收益）

### 4. 🎨 IP 衍生内容 Agent
基于链上 IP 自主生成风格一致的衍生内容：
- 🔬 IP 风格分析（提取核心元素、叙事模式、视觉特征）
- 📚 衍生故事生成（风格一致的续写/外传）
- 🎬 动画脚本生成（分镜、场景、对白）
- 🎁 周边资产生成（描述与视觉方案）
- ⛓️ 衍生 NFT 铸造

## 🧠 长程自主执行引擎（核心创新）

`LongHorizonEngine` 是整个系统的核心，它让 Agent 具备真正的长程执行能力：

| 能力 | 实现方式 |
|------|---------|
| **任务拆解** | 自动将复杂目标分解为有序步骤，支持依赖关系 |
| **多步执行** | 按依赖拓扑排序，逐步执行并记录结果 |
| **自我纠错** | 失败时自动分析错误类型，生成修复策略并重试 |
| **持续迭代** | 支持质量自检不通过时自动修订 |
| **工具调用** | 注册式工具系统，每步可调用不同工具 |
| **执行追踪** | 完整的执行日志、工具调用记录、时间统计 |

### 自我纠错示例

```
步骤: 撰写完整内容
  → 失败: 内容质量评分 65/100，低于阈值 80
  → 纠错策略: 质量不达标，扩展论述并补充数据支撑
  → 重试 1: 内容质量评分 82/100 ✅
```

## 📦 项目结构

```
chainscribe/
├── contracts/src/          # Solidity 智能合约
│   ├── ContentNFT.sol      # 内容 NFT（付费解锁+版税）
│   └── CreatorDAO.sol      # 创作者 DAO（协作+分账）
├── backend/
│   ├── core/
│   │   └── engine.py       # 长程自主执行引擎 ⭐
│   ├── agent/
│   │   ├── orchestrator.py # 统一编排器（整合四模块）⭐
│   │   ├── publishing.py   # 链上出版 Agent
│   │   ├── narrative.py    # 动态叙事引擎
│   │   ├── dao.py          # 创作者 DAO
│   │   ├── ip_derivative.py # IP 衍生 Agent
│   │   └── llm.py          # GLM-5.1 客户端
│   ├── services/
│   │   ├── ipfs.py         # IPFS 存储客户端
│   │   └── blockchain.py   # 区块链交互客户端
│   └── api/
│       └── main.py         # FastAPI 统一服务
├── frontend/src/
│   └── index.html          # 交互式前端
├── demo/
│   ├── run_demo.py         # 完整 Demo 运行脚本
│   └── output/             # Demo 输出文件
└── docs/
```

## 🏃 快速开始

### 运行完整 Demo

```bash
cd chainscribe
python3 demo/run_demo.py                  # 运行全部 Demo
python3 demo/run_demo.py --mode publish   # 仅链上出版
python3 demo/run_demo.py --mode narrative # 仅动态叙事
python3 demo/run_demo.py --mode dao       # 仅 DAO 协作
python3 demo/run_demo.py --mode ip        # 仅 IP 衍生
```

### 启动 API 服务

```bash
pip install -r backend/requirements.txt
cd backend && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动前端

```bash
cd frontend && npx serve src -l 3000
```

## 🔗 智能合约

### ContentNFT
- 铸造内容 NFT，设置付费解锁价格
- 读者支付 ETH 解锁完整内容
- 支持 ERC2981 版税标准
- 收益自动按比例分账

### CreatorDAO
- 多角色 Agent 注册与任务分配
- 项目创建与任务拆解
- 收益按贡献比例自动分配
- 支持提案与投票

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| AI 引擎 | GLM-5.1 + LongHorizonEngine |
| 后端 | Python + FastAPI + asyncio |
| 智能合约 | Solidity 0.8.20 + OpenZeppelin |
| 存储 | IPFS / Arweave |
| 区块链 | Ethereum / Polygon |
| 前端 | HTML/CSS/JS (原生) |

## 🎯 赛道契合度

### Web3 × Long-Horizon Task

✅ **长程执行** — Agent 自主拆解并执行 6-12 步复杂任务，不是一次性生成
✅ **自主决策** — 每步执行都由 Agent 自主判断，包括质量自检、策略调整
✅ **自我纠错** — 失败时自动分析原因、生成修复策略、重试执行
✅ **持续迭代** — 质量不达标时自动修订，直到满足标准
✅ **完整链路** — 从需求输入到链上交付，覆盖全流程
✅ **Web3 原生** — NFT 铸造、付费解锁、版税分账、链上叙事，不是硬凑

## 📄 License

MIT
