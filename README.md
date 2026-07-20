# slumcli

从零手写的终端 AI 编程 agent（Python）。模型是大脑，slumcli 是 harness（身体）——循环、工具、上下文、安全、可观测全部亲手实现。差异化方向：**crypto 场景 × 纵深安全 × 生产级健壮性**。

**文档入口** → **[docs/README.md](./docs/README.md)**

## 快速开始

```bash
pip install -e .
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
slumcli                # 或 slumcli -v
```

## 文档导航

完整索引见 **[docs/README.md](./docs/README.md)**（含进度看板）。

| 文档 | 说明 |
|------|------|
| [docs/01-overview.md](./docs/01-overview.md) | 项目总览：定位、差异化、功能清单 |
| [docs/02-pipeline.md](./docs/02-pipeline.md) | **全链路架构**（技术核心） |
| [docs/03-roadmap.md](./docs/03-roadmap.md) | 功能路线图（阶段 0-8，护城河早落地） |
| [docs/04-learning-plan.md](./docs/04-learning-plan.md) | 学习计划 + 怎么验证真懂了 |
| [docs/05-modules.md](./docs/05-modules.md) | 模块手册（代码地图） |
| [docs/06-development.md](./docs/06-development.md) | 开发协作：环境、Git、测试约定 |

个人原理笔记：`AI工程学习总手册.md`（可纳入 git）。`CLAUDE.md` / `.cursorrules` / `AGENTS.md` 为本地协作规则，**不提交**。

## 当前进度

阶段 0～2 主体已完成；**下一步：阶段 3 最小 Eval harness**。
完整进度看板见 **[docs/README.md](./docs/README.md)**（唯一事实来源）。
