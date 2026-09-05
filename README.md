# bridge-mcp-server · AI Foundation 生成能力（MCP 生成面）

把系列「AI 生成完整业务系统」的**确定性生成能力**按 MCP 规范暴露给任意符合 MCP 的壳（Claude Code / Hermes / 自研 app…）消费。目标是**需求 → 生成项目目录**的统一流程。

**只做生成面**：菜单 / 参数内省 / 确定性生成 / 结构化返回；治理链（桥 `check` 漂移、AI 维护契约）**不在此暴露**（一面一 server，见 [DESIGN §3.1/§10](docs/DESIGN.md)）。

## 能力（六生成工具 + 两资源 + 玩法）

| 链 | 工具 | 说明 |
|---|---|---|
| 单端（②-⑥ 直生成，零注册） | `list_templates` | 单端候选菜单（离线注册表过滤） |
| | `get_template_params` | clone 底座 → 读 params.json 两区（native/derived/selection） |
| | `generate_single` | git 地址 + 参数 + target_dir → copier 生成（无协议地址回退 copier.yml 内省） |
| 多端（① 纯 cli 消费桥） | `list_combos` | 组合菜单（units/edges + 合并 selection，经桥 `--json`） |
| | `get_combo_params` | 参数基线（params 可问 / internal 勿传 / derived 只读 / 共享参数标 `shared: true`） |
| | `generate_multi` | `combo + 参数 + target_dir` → shell-out 桥 `generate` |

- **Resources**：`templates://catalog`（单端注册表）、`combos://catalog`（桥内省视图）
- **Prompt / Skill**：`generate_project_guide`（MCP 玩法）+ 壳侧 [generate-project](skills/generate-project/SKILL.md)（canonical，玩法只引用工具不抄知识）

## 架构（双路径 × 双链）

```
单端：git 地址 → clone → 读协议(params.json 两区/回退 copier.yml) → spec 校验 → copier
多端：纯 cli shell-out 桥（generate + 内省 list-combos/show-combo），server 不直读 combos.yaml
```

设计定稿见 [docs/DESIGN.md](docs/DESIGN.md)；跨仓落地见 [docs/implementation-plan.md](docs/implementation-plan.md)（P0-P3 已完成并推送）。

## 目录结构

```
bridge_mcp/              共享胶水（无 MCP 面）：config / git / protocol / bridge_cli / selection
servers/generation/      生成面 MCP server（六工具 + resources + guide + templates.yaml）
servers/governance/      治理面占位（README，未实现）
skills/generate-project/ 壳侧玩法 skill（canonical）
tests/{unit,e2e}         单测 + MCP stdio / 生成 e2e
```

## 快速开始

```bash
uv sync                                        # 安装依赖（fastmcp / copier 9.17.1）
# 多端工具需要打包好的桥可执行（见 CLAUDE.md 开发前置）：
#   cd ~/project/fullstack-bridge && uv sync --dev && uv run pyinstaller bridge.spec --noconfirm
#   mkdir -p ~/.local/bin && cp dist/bridge ~/.local/bin/bridge
BRIDGE_EXE=/home/jeff/.local/bin/bridge uv run python -m servers.generation.server   # stdio 起 server
```

### 挂到 Claude Code

```bash
claude mcp add bridge-gen --transport stdio \
  -- uv run --directory /home/jeff/project/bridge-mcp-server python -m servers.generation.server
claude mcp list
```

然后直接说「帮我生成一个 **X** 项目」即可触发 `generate-project` skill / 六工具。

## 环境变量

| 变量 | 用途 | 默认 |
|---|---|---|
| `BRIDGE_EXE` | 桥可执行（dist/bridge，多端链） | 无（必配，否则多端工具报错） |
| `BRIDGE` | PATH 上的 bridge 命令（备选） | — |
| `BRIDGE_MCP_CACHE` | 单端克隆缓存根 | `~/.cache/bridge-mcp-server` |

> 只认可执行入口，不暴露源码 cli.py（BRIDGE_CLI 已移除）。

## 测试

```bash
uv run pytest tests/unit -q                 # 离线单测（mock 桥/copier）
BRIDGE_EXE=/home/jeff/.local/bin/bridge uv run pytest -q   # 全量（含 MCP stdio + 生成 e2e）
```

## 相关仓库

协议（params.json 两区 + gen-params）见 [fullstack-param-protocol](https://github.com/jianghua-developer/fullstack-param-protocol)；桥（组合治理/内省/生成执行）见 [fullstack-bridge](https://github.com/jianghua-developer/fullstack-bridge)；底座：react / vue / python-fastapi 模板。
