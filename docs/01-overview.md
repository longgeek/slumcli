# 01 项目总览

[← 返回文档中心](./README.md)

---

## 1. slumcli 是什么

**slumcli** 是一个从零手写的**终端 AI 编程 agent**（命令行工具），形态类似"在终端里帮你读代码、改文件、跑命令的 AI 助手"。

- **语言**：Python 3.11+
- **默认模型**：DeepSeek API（OpenAI 兼容接口）
- **形态**：多模块 Python 包 + `pip install`

### 1.1 核心公式

```
Agent = LLM（大脑）+ Harness（身体）
```

| 组件 | 职责 | slumcli 中的实现 |
|------|------|------------------|
| 大脑 | 理解意图、决定调什么工具、生成回复 | `client.py` → DeepSeek API |
| 身体 | 循环节奏、工具执行、上下文、安全、可观测 | `main.py`、`tools.py`、`context.py`、`security.py`、`tracing.py` |

**关键认知**：同一模型，harness 做得好不好决定 agent 强不强。slumcli 的价值在于**亲手实现 harness 的每一环**。

### 1.2 差异化方向（护城河 = 别人抄不了的交叉）

> 排序按护城河优先，且分散在中前段落地（不堆最后）。详见 [03-roadmap](./03-roadmap.md)。

| 方向 | 说明 | 阶段 |
|------|------|------|
| **Crypto 工具** | 链上只读查询等金融场景工具（对口 AI×crypto 岗） | 4（早落地） |
| **纵深安全** | 从 baseline 做到"假设注入成功也限制破坏"（沙箱/隔离/最小权限） | 0 baseline → 6 做深 |
| **生产级健壮性** | 把十几年 DevOps 存量翻译成 agent 语境：重试/超时/容错/可观测 | 2 |
| **Eval** | 自动评估质量、防回归、注入用例 | 3（回归基线） |
| **可观测** | Trace/Span，看清 agent 里发生了什么 | 1 |
| **MCP** | 手搓工具层 + 接工业标准协议 | 4 |

**三张牌一起打**：crypto（领域）× 安全（招牌）× 生产化（存量）——这个交叉别人难复制。

---

## 2. 项目目标

### 2.1 作品目标

1. **有一个能演示的核**（里程碑 A，约第 6 周）：agent + tracing + eval + 一个 crypto 工具，端到端跑通、能录 demo。
2. **差异化加厚**：在这个核上做深 crypto、安全、上下文、Loop。
3. **能发布到 GitHub**：demo、架构图、博客，面试能讲 30 分钟。

### 2.2 求职叙事

> 从零手写的终端编程 agent，具备完整 harness 能力；差异化在 **crypto 场景、纵深安全、生产级健壮性**，并用 eval 给出真实质量数字。

**对口岗位**：Agent / Harness 工程岗；AI × crypto 交叉岗。

### 2.3 作者背景（决定文档讲解深度）

- 十几年后端 / 分布式 / DevOps（Python/Django），crypto / 金融经验。
- 系统学过 Agent 原理：LLM 生成、上下文工程、harness、循环控制、工具设计、AI 安全。
- **通用工程概念不啰嗦；AI/agent 的 why 讲透。**

---

## 3. 技术栈

| 层级 | 选型 | 阶段 |
|------|------|------|
| 语言 | Python 3.11+（类型注解、dataclass） | 0 |
| LLM SDK | openai（对接 DeepSeek） | 0 |
| 配置 | python-dotenv | 0 |
| 可观测 | 自研 Trace + Langfuse（后期） | 1 |
| Eval | 自研 runner（可选 Promptfoo/DeepEval） | 3 |
| 链上 | web3.py + 公共 RPC | 4 |
| 工具协议 | 最小 MCP client（stdio） | 4 |
| 沙箱 | Docker / macOS sandbox-exec | 6 |
| 终端美化 | Rich + prompt_toolkit | 8 |

---

## 4. 功能清单（验收标准）

### 4.1 主路径

| 能力 | 现状 | 阶段 |
|------|------|------|
| Agent 工具循环 | ✅ | 0 |
| read / write / edit / bash | ✅ | 0 |
| 路径沙盒 + 危险确认 | ✅ baseline | 0 |
| REPL 多轮对话 | ✅（仅 `exit`） | 2 增强 |
| Streaming + token 统计 | ❌ | 2 |
| 生产级健壮性（重试/超时/容错） | ❌ | 2 |
| 斜杠命令 + attempt_completion | ❌ | 2 |
| grep / glob 搜索 | ❌ | 4 |
| 智能上下文压缩（三级） | 滑窗 only | 5 |
| 会话持久化 | ❌ | 5 |
| Loop 工程（/loop） | ❌ | 7 |
| 多 Provider（可选） | DeepSeek only | 8 |

### 4.2 差异化

| 能力 | 现状 | 阶段 |
|------|------|------|
| Tracing 可观测 | 🔄 待挂 main | 1 |
| Eval 体系 | ❌ | **3（前移）** |
| Crypto 只读工具 | ❌ | **4（早落地）** |
| MCP client | ❌ | 4 |
| 纵深安全 | ✅ baseline | 0 → **6 做深** |

### 4.3 开源门面

| 能力 | 现状 | 阶段 |
|------|------|------|
| README + demo + 架构图 | ❌ | 增量 → 8 |
| 技术博客 | ❌ | 增量 → 8 |
| Rich 美化 | ❌ | 8 |

### 4.4 明确不做 / 降级

- 单文件零依赖形态（不对标）
- 全套多 provider 路由（降级为阶段 8 可选两档 demo）
- 思考框架代理（二期可选）

---

## 5. 快速上手

```bash
# 远端仓库重建后：git clone https://github.com/longgeek/slumcli.git
cd slumcli
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env      # 编辑 .env，填入 DEEPSEEK_API_KEY
slumcli                   # 或 slumcli -v（工具详情 → stderr）
```

输入 `exit` 退出 REPL。

---

## 6. 相关文档

- 全链路逐步拆解 → [02-pipeline.md](./02-pipeline.md)
- 功能计划与阶段详情 → [03-roadmap.md](./03-roadmap.md)
- 原理映射与"怎么验证真懂了" → [04-learning-plan.md](./04-learning-plan.md)
- 代码地图 → [05-modules.md](./05-modules.md)
- 环境、Git、测试约定 → [06-development.md](./06-development.md)
