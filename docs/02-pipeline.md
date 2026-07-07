# 02 全链路架构

[← 返回文档中心](./README.md)

> **本文档是 slumcli 的技术核心**：从用户敲回车，到终端打印回复，每一步发生了什么、在哪个文件、为什么这样设计。

---

## 1. 鸟瞰图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户（终端 REPL）                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ 输入一行
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  main.py :: main()                                               │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────────┐ │
│  │ 读用户输入   │ → │ 上下文裁剪    │ → │ run_turn() 单轮处理     │ │
│  └─────────────┘   │ context.py   │   └───────────┬────────────┘ │
│                    └──────────────┘               │              │
└───────────────────────────────────────────────────┼──────────────┘
                                                    │
                    ┌───────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  main.py :: run_turn()  ——  内层 Agent 循环（最多 10 轮 tool）    │
│                                                                  │
│   ① chat_with_tools()  ──→  client.py  ──→  DeepSeek API        │
│         │                                                        │
│         ├─ 无 tool_calls → 直接返回 assistant 文本               │
│         │                                                        │
│         └─ 有 tool_calls → ② 对每个 tool_call:                   │
│                confirm_tool()  security.py  危险操作确认          │
│                run_tool()      tools.py     真正执行               │
│                audit_log()   security.py  写审计日志              │
│                append tool message 到 messages                    │
│            ③ 再次 chat_with_tools() → 循环直到无 tool 或达上限     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 外层循环：REPL 多轮对话

**入口**：`slumcli/main.py` → `main()`

| 步骤 | 代码位置 | 做什么 | 为什么 |
|------|----------|--------|--------|
| 1 | `load_dotenv()` | 加载 `.env` 中的 API Key | 密钥不进代码库 |
| 2 | `messages = [system]` | 初始化消息列表，注入 system prompt | 模型需要角色设定 |
| 3 | `while True` | REPL 无限循环 | 终端 agent 的核心交互形态 |
| 4 | `input("You: ")` | 读用户输入 | 阻塞等待 |
| 5 | `== "exit"` | 退出 | 最简退出方式（阶段 2 改为 `/q`） |
| 6 | `messages.append(user)` | 用户消息入上下文 | OpenAI message 格式 |
| 7 | `trim_messages(messages)` | 滑窗裁剪 | 防上下文爆炸（见 §4） |
| 8 | `run_turn(messages, verbose)` | 处理本轮 | 内层 agent 循环 |
| 9 | `print(reply)` | 输出 assistant 最终回复 | 用户可见结果 |

**messages 的生命周期**：跨 REPL 轮次累积；每轮 `run_turn` 会 append assistant 消息和中间的 tool 消息。

---

## 3. 内层循环：Agent Tool Loop

**核心**：`slumcli/main.py` → `run_turn()`

这是 harness 的**心脏**：想 → 做 → 反馈 → 再想。

### 3.1 流程逐步拆解

```
run_turn(messages, verbose)
│
├─ [A] reply = chat_with_tools(messages, TOOLS)
│       └─ LLM 看到完整 messages + 工具 schema，决定：直接回复 or 调工具
│
├─ [B] if reply.tool_calls 为空
│       └─ 跳到 [F]，返回 reply.content
│
├─ [C] turn = 0; while reply.tool_calls and turn < 10
│       │
│       ├─ turn += 1
│       ├─ messages.append(reply.model_dump())   # assistant 带 tool_calls
│       │
│       ├─ for each tool_call:
│       │     ├─ confirm_tool(name, args)      # 安全：用户确认
│       │     ├─ run_tool(name, args)          # 执行工具
│       │     ├─ audit_log(...)                # 安全：审计
│       │     └─ messages.append(tool message) # 结果喂回 LLM
│       │
│       └─ reply = chat_with_tools(...)        # LLM 再看结果，决定下一步
│
└─ [F] messages.append(assistant content)
       return reply.content
```

### 3.2 关键设计决策

| 决策 | 选择 | 为什么 |
|------|------|--------|
| 循环上限 | `max_turns = 10` | 防死循环、控成本；阶段 2 结合 `attempt_completion` 优化 |
| tool 结果格式 | `role: tool` + `tool_call_id` | OpenAI function calling 协议要求 |
| 错误处理 | `run_tool` 返回 `"Error: ..."` 字符串 | 错误作为 observation 喂回 LLM，agent 可自我修正 |
| 用户拒绝 | `"Tool execution cancelled by user"` | 同样是 observation，LLM 知道被拦了 |
| verbose | `-v` 打 stderr | 不污染 stdout 的 assistant 回复 |

### 3.3 与 LLM 的交互

**文件**：`slumcli/client.py`

```
chat_with_tools(messages, tools)
  → OpenAI client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools          # function calling schema
    )
  → return response.choices[0].message   # 含 .content 和/或 .tool_calls
```

**messages 格式**（OpenAI 兼容）：

| role | 何时产生 | 内容 |
|------|----------|------|
| system | 启动时一次 | 系统提示词（`prompts.py`） |
| user | 每轮 REPL 输入 | 用户问题 |
| assistant | LLM 返回带 tool_calls 时 | 可能 content 为空，tool_calls 有值 |
| tool | 工具执行后 | 工具返回字符串 + tool_call_id |
| assistant | 最终回复 | 无 tool_calls 时的 content |

---

## 4. 上下文管理

**文件**：`slumcli/context.py`

**当前策略**：滑动窗口（按 user 轮次裁剪）

```
trim_messages(messages):
  1. 找所有 user 消息的 index
  2. 若 user 轮次 ≤ MAX_TURNS(2) → 不裁
  3. 否则：保留 system（开头的 system 消息）+ 最近 MAX_TURNS 轮 user 起的所有消息
  4. 删除中间段
```

**为什么保留 system**：system prompt 是安全策略和角色设定的载体，裁掉等于自废武功。

**阶段 5 升级方向**：三级智能压缩（micro 过期 tool 结果 → session 摘要 → fallback 硬裁）。

---

## 5. 工具执行链路

**定义**：`slumcli/tools.py` → `TOOLS` 列表（OpenAI function schema）

**调度**：`run_tool(name, arguments_json)` → 按 name 分发到具体 handler

### 5.1 当前 5 个工具

| 工具 | 危险级 | 做什么 | 安全点 |
|------|--------|--------|--------|
| `get_current_time` | 低 | 返回当前时间 | 无 |
| `read_file` | 低 | 读文件内容 | 路径校验（项目根内） |
| `write_file` | **高** | 写文件 | 路径校验 + 用户确认 |
| `search_replace` | **高** | 精确替换 | 路径校验 + 用户确认 |
| `run_command` | **高** | subprocess 跑命令 | 黑名单 + 用户确认 |

### 5.2 单次工具调用链路

```
LLM 输出 tool_call(name, arguments)
  → confirm_tool()     # DANGEROUS_TOOLS 需 y/n
  → run_tool()
       ├─ json.loads(arguments)
       ├─ 路径 resolve + 校验（ROOT_DIR 内）
       ├─ run_command 额外走 is_command_blocked()
       └─ 异常 → 返回 "Error: ..." 字符串（不 raise）
  → audit_log()        # 追加 audit.log
  → messages.append({role: tool, content: result})
```

---

## 6. 安全（当前 = baseline，纵深演进中）

**文件**：`slumcli/security.py`、`slumcli/prompts.py`

```
第 1 层：System Prompt（prompts.py）
         └─ 告诉模型边界、不做什么

第 2 层：路径沙盒（tools.py）
         └─ 文件操作限制在项目 ROOT_DIR 内

第 3 层：危险工具确认（security.py :: confirm_tool）
         └─ write / search_replace / run_command 需用户 y/n

第 4 层：命令黑名单（security.py :: is_command_blocked）⚠️ 玩具级
         └─ 当前仅 4 条子串（rm -fr〔注:漏了最常见的 rm -rf〕、mkfs、dd if、curl）
            易被 rm -r -f / 绝对路径 / 编码绕过；子串匹配本质是"检测坏内容"，与心法相悖

第 5 层：审计日志（security.py :: audit_log）
         └─ 所有工具调用记 audit.log（时间、工具、参数、结果分类）
```

**设计心法**（来自 AI 安全学习）：不赌「挡住所有注入」，赌「就算被攻破也死不了」—— 每层都不完全可靠，叠加才有意义。

> **诚实说明（面试别吹"5 层"）**：以上是当前 **baseline**，撑不起"纵深"话术——第 1 层 prompt 不是安全边界（可被注入覆盖）、第 4 层黑名单玩具级、读 `.env` 没有 harness 层硬拦。真正的纵深（确认前展示 diff、敏感路径硬拦、不可信内容隔离、沙箱）是 [阶段 6](./03-roadmap.md) 要做的。诚实叙述"这层真、那层薄"比排练漂亮话更能打动资深岗面试官。

---

## 7. 可观测（Tracing）—— 计划挂入点

**文件**：`slumcli/tracing.py`（已实现，**待集成 main.py**）

### 7.1 数据模型

```
Trace（一次用户 REPL 输入 = 一条 trace）
  ├── trace_id
  ├── user_input
  ├── started_at / ended_at
  ├── status
  └── spans[]          # 有序列表
        └── Span
              ├── type: "llm" | "tool" | ...
              ├── name
              ├── input / output（截断 500 字符）
              ├── duration_ms
              └── metadata
```

### 7.2 插桩地图（阶段 1d 要做的事）

```
用户输入
  → start_trace(user_input)                    # REPL 层
  → add_span("llm", "chat_with_tools", ...)    # 每次 API 调用前
  → end_span(span, response_preview)           # API 返回后
  → add_span("tool", tool_name, args)          # 每个 tool 执行前
  → end_span(span, result)                     # tool 返回后
  → finish_trace(trace)
  → print_trace(trace)                         # -v 或每轮结束
```

### 7.3 与 verbose / audit_log 的分工

| 机制 | 目的 | 输出 |
|------|------|------|
| `-v` verbose | 开发调试，实时看 | stderr 流式 |
| `audit_log` | 安全审计，持久化 | `audit.log` 文件 |
| `print_trace` | 结构化可观测，后续接 Langfuse | 终端 / JSON / 远端 |

三者**不互相替代**：verbose 给开发者看细节，audit 给安全追溯，trace 给 harness 分析和 eval。

---

## 8. 阶段 2+ 链路扩展预览

以下能力尚未实现，但在架构上预留位置：

| 能力 | 插入点 | 说明 |
|------|--------|------|
| Streaming | `client.py` | `stream=True`，逐 token 打印 |
| attempt_completion | `tools.py` + `run_turn` | 模型显式 signal 完成，harness 停止循环 |
| 斜杠命令 | `main.py` REPL 层 | `/q` `/n` `/c` `/h` 在 `run_turn` 之前拦截 |
| 模型路由（可选） | `client.py` 或 `router.py` | 阶段 8 两档 demo |
| `/loop` | `main.py` 外层 | Implementer → Verifier → Updater 流水线 |
| 会话持久化 | 新 `session.py` | `.slumcli/session/` JSON |
| Langfuse | `tracing.py` 扩展 | trace 上报远端 |

---

## 9. 消息流时序图（完整一轮含 2 次 tool）

```
用户          main.py        client.py       tools.py       security.py
 │               │               │               │               │
 │──"改 main"──→│               │               │               │
 │               │──trim────────│               │               │
 │               │──chat+tools─→│──API call────→│               │
 │               │←─tool_calls──│←──────────────│               │
 │               │               │               │               │
 │               │──confirm────────────────────────────────────→│
 │←──"y/n?"──────│               │               │               │
 │──"y"────────→│               │               │               │
 │               │──run_tool───────────────────→│               │
 │               │←─result──────────────────────│               │
 │               │──audit_log──────────────────────────────────→│
 │               │               │               │               │
 │               │──chat+tools─→│──API call────→│               │
 │               │←─tool_calls──│               │               │
 │               │  ... 第二次 tool ...           │               │
 │               │               │               │               │
 │               │──chat+tools─→│──API call────→│               │
 │               │←─content─────│  (无 tool)    │               │
 │←──打印回复────│               │               │               │
```

---

## 10. 自检清单（读懂全链路后应能回答）

- [ ] 外层 REPL 循环和内层 tool 循环分别解决什么问题？
- [ ] 为什么 tool 错误返回字符串而不是 raise？
- [ ] `messages` 里 assistant 消息有两种形态，分别什么时候出现？
- [ ] 滑窗裁剪为什么保留 system、按 user 轮次而不是按 token？
- [ ] 安全各层各防什么、为什么不靠单层？当前哪层是玩具级（见 §6 诚实说明）？
- [ ] trace 应该挂在哪几个点？和 verbose 有什么区别？

全部能答 → 可以开始写阶段 1d 的代码了。

**下一步**：[03-roadmap.md](./03-roadmap.md) 看每个阶段要加什么；[05-modules.md](./05-modules.md) 看每个文件细节。
