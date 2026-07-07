# 05 模块手册

[← 返回文档中心](./README.md)

> slumcli 代码地图：每个文件做什么、关键函数、谁依赖谁。

---

## 1. 目录结构

```
slumcli/
├── pyproject.toml          # 包定义、依赖、入口 slumcli = main:main
├── .env.example            # API Key 模板
├── .gitignore
├── docs/                   # 主文档（本目录）
├── slumcli/
│   ├── __init__.py
│   ├── main.py             # 入口、REPL、run_turn 内层循环
│   ├── client.py           # DeepSeek API 封装
│   ├── tools.py            # 工具 schema + 执行
│   ├── context.py          # 上下文滑窗裁剪
│   ├── security.py         # 确认、黑名单、审计
│   ├── prompts.py          # system prompt
│   └── tracing.py          # Trace/Span 可观测（待集成 main）
├── audit.log               # 运行时生成，工具审计日志
├── CLAUDE.md               # 本地：AI 协作规则（.gitignore）
├── .cursorrules            # 本地：同上，给 Cursor（.gitignore）
└── AI工程学习总手册.md      # 作者个人学习历程 + 开放问题清单
```

---

## 2. 依赖关系图

```
main.py
  ├── client.py      (chat_with_tools)
  ├── tools.py       (TOOLS, run_tool)
  ├── context.py     (trim_messages)
  ├── prompts.py     (SYSTEM_PROMPT)
  ├── security.py    (confirm_tool, audit_log)
  └── tracing.py     (计划集成，当前未引用)

tools.py
  └── security.py    (is_command_blocked)

tracing.py
  └── (无 slumcli 内部依赖，独立模块)
```

---

## 3. 模块详解

### 3.1 `main.py` — 入口与 Agent 循环

| 函数 | 签名 | 职责 |
|------|------|------|
| `main` | `() -> None` | REPL 外层循环 |
| `run_turn` | `(messages, verbose) -> str` | 单轮内层 tool loop |
| `vlog` | `(verbose, msg) -> None` | verbose 输出到 stderr |
| `parse_args` | `(argv) -> bool` | 解析 `-v` |

**常量 / 隐含配置**：

- 内层循环上限：`turn < 10`（硬编码，阶段 2 可配置化）
- 退出命令：`exit`（阶段 2 改为 `/q`）

**阶段 1d 改动点**：在 `run_turn` 和 REPL 层插入 tracing 调用。

---

### 3.2 `client.py` — LLM 客户端

| 函数 | 职责 |
|------|------|
| `get_client()` | 创建 OpenAI 兼容 client（DeepSeek endpoint） |
| `chat(messages)` | 简单对话（无工具，早期最小 agent 用） |
| `chat_with_tools(messages, tools)` | function calling 调用 |

**环境变量**：`DEEPSEEK_API_KEY`

**阶段 1e 改动点**：从 response 提取 `usage`（prompt_tokens, completion_tokens）记入 LLM span。

**阶段 2 改动点**：`stream=True` 变体。

**阶段 2 改动点**：API 重试 / 超时 / 限流退避（生产级健壮性）。
**阶段 8 改动点**：按路由结果选 model / base_url（可选）。

---

### 3.3 `tools.py` — 工具定义与执行

| 符号 | 类型 | 职责 |
|------|------|------|
| `ROOT_DIR` | `Path` | 项目根目录，路径沙盒边界 |
| `TOOLS` | `list[dict]` | OpenAI function calling schema |
| `run_tool(name, arguments)` | 函数 | 按名分发执行 |

**handler 模式**（当前）：`run_tool` 内 if/elif 按 name 分发。

**错误约定**：捕获异常，返回 `"Error: {msg}"` 字符串，不 raise。

**阶段 3 扩展**：新增 grep、glob_search、web_search、use_skill 等 handler。

---

### 3.4 `context.py` — 上下文管理

| 符号 | 职责 |
|------|------|
| `MAX_TURNS` | 保留最近 N 轮 user 对话（当前 = 2） |
| `trim_messages(messages)` | 原地裁剪 messages 列表 |

**行为**：保留开头连续 system 消息 + 最近 MAX_TURNS 个 user 轮次的所有消息。

**阶段 5 扩展**：三级压缩策略替换纯滑窗（token 预算 + 缓存友好）。

---

### 3.5 `security.py` — 安全层

| 符号 | 职责 |
|------|------|
| `DANGEROUS_TOOLS` | 需用户确认的工具列表 |
| `DANGEROUS_COMMANDS` | 命令黑名单子串 |
| `LOG` | audit.log 路径 |
| `confirm_tool(name, arguments)` | 危险工具 y/n 确认 |
| `is_command_blocked(command)` | 命令黑名单检查 |
| `audit_log(name, arguments, outcome)` | 追加审计记录 |

**outcome 分类**：`executed` / `blocked` / `error` / `denied`

**阶段 6 扩展**：确认前展示 diff、敏感路径 harness 层硬拦、沙箱、crypto 操作多重确认。

---

### 3.6 `prompts.py` — 系统提示词

| 符号 | 职责 |
|------|------|
| `SYSTEM_PROMPT` | 注入 messages 开头的 system 内容 |

**设计原则**：设定角色边界、安全约束、工具使用指引。裁剪时**绝不删除**。

---

### 3.7 `tracing.py` — 可观测

| 类型/函数 | 职责 |
|-----------|------|
| `Span` | 单个步骤（type, name, input, output, duration_ms, metadata） |
| `Trace` | 一次用户请求（trace_id, spans[], status, 时间戳） |
| `start_trace(user_input)` | 创建 Trace |
| `add_span(trace, type, name, input, **metadata)` | 开始一个 span，append 到 trace.spans |
| `end_span(span, output)` | 填 output 和 duration_ms |
| `finish_trace(trace, status)` | 标记 trace 结束 |
| `print_trace(trace)` | 终端可读输出 |
| `_truncate(text, limit=500)` | 防输出过长 |

**自测**：`python -m slumcli.tracing` 可跑 mock trace。

**阶段 1f**：`export_trace_json(trace) -> dict`

**阶段 1g**：Langfuse SDK 上报封装。

---

## 4. 计划新增模块（尚未创建）

| 文件 | 阶段 | 职责 |
|------|------|------|
| `eval/` | **3** | eval runner + 用例（回归基线，前移） |
| `crypto/` | **4** | 链上只读工具（差异化早落地） |
| `mcp_client.py` | **4** | 最小 MCP client（stdio） |
| `compress.py` | 5 | 三级上下文压缩 |
| `session.py` | 5 | 会话持久化读写 |
| `sandbox.py` | 6 | run_command 沙箱执行 |
| `loop.py` | 7 | /loop 三角色流水线 |
| `router.py` | 8 | 多 provider 两档路由（可选） |
| `ui.py` | 8 | Rich 终端渲染 |

---

## 5. 配置文件（计划）

| 路径 | 阶段 | 内容 |
|------|------|------|
| `.env` | 0 | API Key（不提交） |
| `evals/cases.jsonl` | 3 | eval 用例集 |
| `.slumcli/session/` | 5 | 会话 JSON |
| `.slumcli/loops/` | 7 | Loop 临时状态 |
| `.slumcli/providers.json` | 8 | 多 Provider 配置（可选） |

---

## 6. 运行时产物（不提交 git）

| 文件 | 产生者 | 说明 |
|------|--------|------|
| `audit.log` | `security.audit_log` | 工具调用审计 |
| `.venv/` | 本地开发 | Python 虚拟环境 |

---

## 7. 快速定位：我想改 X，去哪个文件？

| 需求 | 文件 |
|------|------|
| 加新工具 | `tools.py`（schema + handler）+ `security.py`（是否危险） |
| 改循环次数上限 | `main.py` run_turn |
| 改上下文保留轮数 | `context.py` MAX_TURNS |
| 改 system prompt | `prompts.py` |
| 加命令黑名单 | `security.py` DANGEROUS_COMMANDS |
| 换模型 / 加 streaming | `client.py` |
| 加 trace 插桩 | `main.py` + 可能 `client.py` |
| 加斜杠命令 | `main.py` REPL 层 |
| 终端美化 | 阶段 8 新建 `ui.py` |

---

**下一步**：[06-development.md](./06-development.md) 看环境与 Git 规范。
