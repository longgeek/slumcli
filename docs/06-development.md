# 06 开发协作

[← 返回文档中心](./README.md)

---

## 1. 环境搭建

### 1.1 前置条件

- Python 3.11+
- git
- DeepSeek API Key（或任意 OpenAI 兼容 endpoint）

### 1.2 本地开发

```bash
# 远端仓库重建后：
# git clone https://github.com/longgeek/slumcli.git
cd slumcli

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
cp .env.example .env
# 编辑 .env：DEEPSEEK_API_KEY=sk-...
```

### 1.3 运行

```bash
slumcli              # REPL 模式
slumcli -v           # verbose：工具详情 → stderr

python -m slumcli.tracing   # tracing 模块自测
```

### 1.4 IDE

仓库含 `.vscode/launch.json`，可直接 F5 调试 `main.py`。

---

## 2. Git 规范

### 2.1 Commit Message

- **一律使用中文**
- 格式建议：`<类型>: <简述>`

| 类型 | 用途 | 示例 |
|------|------|------|
| feat | 新功能 | `feat: 将 tracing 挂入 main 真链路` |
| fix | 修复 | `fix: 修复路径校验绕过父目录的问题` |
| docs | 文档 | `docs: 补充全链路架构文档` |
| refactor | 重构 | `refactor: 抽取 run_tool 分发为 registry` |
| chore | 杂项 | `chore: 更新 .gitignore` |

### 2.2 谁提交

- **默认由作者自己执行** `git add` / `git commit` / `git push`
- Cursor 只在阶段结束时：提示该提交了、拟中文 message、说明 add 哪些文件
- 除非作者明确说「帮我提交」，否则 Cursor 不代执行 commit

### 2.3 作者信息

确认本地 git 配置是自己的身份（不是 Cursor / 工具默认）：

```bash
git config user.name    # 应为你的名字
git config user.email   # 应为你的邮箱
git log -1 --format='%an <%ae>'   # 提交后验证
```

### 2.4 分支策略（当前）

- `main`：稳定可跑版本（本地 `git init` 后默认分支）
- 功能开发可直接在 main 上小步提交（个人项目）
- 远端删除后需 `gh repo create` 重建再 `git push -u origin main`
- 后期可考虑 feature branch + PR（阶段 8 加 CI 时）

---

## 3. 协作铁律（人与 Cursor）

协作约定完整版见根目录 `CLAUDE.md` / `.cursorrules`（内容一致，**不纳入 git**）。要点：

1. **作者主导，AI 辅助**：核心逻辑作者自己写
2. **一次一小步**：讲 why → 确认懂 → 搭样板 / 写核心 → review → **预测/复述验证** → commit
3. **AI 直接写代码仅限**：样板代码，或作者明确说「这块你帮我写」；文档/规划这类元工作不受限
4. **卡住时**：先提示引导，不直接甩完整答案（除非说「直接告诉我答案」）
5. **学习验证**：不止复述——用「预测→真跑→对照」和「敌意 mock 面试连问 3 层 why」逼出夹生点
6. **拦逃避**：作者想重写能跑的代码 / 再开新文档时，提醒他这可能是「用规划代替行动」

---

## 4. 开发节奏（每个小步）

```
① Cursor 讲：这步做什么、why、和生产环境怎么对应
② 作者确认懂了
③ 搭样板 / 作者写核心逻辑
④ Cursor review
⑤ 作者预测→真跑→对照（或敌意 mock 连问 3 层 why）
⑥ 中文 commit（作者自己执行）
⑦ 下一小步
```

---

## 5. 文档维护

| 何时更新 | 更新什么 |
|----------|----------|
| 完成一个阶段 | `docs/README.md` 进度看板（**唯一进度来源**） |
| 新增模块 | `docs/05-modules.md` |
| 架构变化 | `docs/02-pipeline.md` |

**原则**：代码和文档同步更新，但不在同一 commit 里混 unrelated 改动。
**注意**：里程碑 A 交付前文档冻结，除进度看板 / README / 02-pipeline 外不新增、不重构文档。

---

## 6. 不要提交的文件

已在 `.gitignore` 中：

- `.env`（含 API Key）
- `CLAUDE.md`、`.cursorrules`（本地 AI 协作规则，不进库）
- `.venv/`
- `audit.log`
- `__pycache__/`
- `.DS_Store`

---

## 7. 测试约定

- **阶段 2 起**：给纯函数补 pytest（`trim_messages` 切分、路径沙箱、黑名单绕过），一个大谈质量的项目自己零测试会被面试官一眼看穿。
- **阶段 3 起**：eval 集作为核心路径的自动化回归，每阶段改完都跑一遍防"改坏掉分"。
- 辅助验证：手动 REPL + `python -m slumcli.tracing` 自测。

---

## 8. 发布清单（阶段 8）

- [ ] README（链到 docs/）
- [ ] LICENSE
- [ ] demo GIF / asciinema
- [ ] `pip install` 可安装
- [ ] GitHub 仓库描述 + topics
- [ ] 中文 commit 历史整理

---

**AI 协作规则（含学习方式）** → 根目录 `CLAUDE.md` / `.cursorrules`
