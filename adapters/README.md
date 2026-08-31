# adapters/ — 跨平台适配层（Layer 0）

实现"一次安装，到处可用"的即插即用机制。

## 组成

| 模块 | 说明 |
|------|------|
| `zcode/` | Python 包：profile 加载、LLM Provider 抽象、CLI |
| `profiles/` | 本地模型能力声明（当前：`local-qwen3.6-35b.yaml`） |
| `platforms/` | 8 平台适配文档（技能目录路径 + 配置要点） |

## 安装

```bash
pip install -e .          # 安装 zcode 包（依赖 pyyaml）
zcode skills list         # 验证
```

## CLI 用法

```bash
zcode skills list                         # 列出技能
zcode --profile local-qwen3.6-35b info    # 查看 profile 能力
zcode platforms list                      # 8 平台技能目录支持状态
```

## 设计要点

- **Provider 抽象**：`providers/base.py` 定义统一 `chat()` 接口；`openai_compat.py` 对接 llama.cpp `/v1` 等 OpenAI 兼容端点。工具三层降级（L2 原生 / L1 提示词编码 / L0 无工具）已实装。
- **Profile**：能力声明驱动——上下文窗口、工具级别、JSON 可靠性决定技能版本（`SKILL.md` / `SKILL.local.md`）与记忆策略的加载。
- **记忆**：`memory.py` MemStore 统一接口（mem0 实现，`zcode memory add/search/list`）；自定义 `http_embedder.py` 对接 llama.cpp `/embedding` 端点（Qwen3-Embedding-8B）。
- **可选 NLP 增强**（BM25 词形还原 + 实体识别）：`pip install spacy && pip install en_core_web_sm-3.8.0-py3-none-any.whl`（模型经 gitproxy 代理下载，国内网络适用）。不装则自动降级为纯语义检索。
