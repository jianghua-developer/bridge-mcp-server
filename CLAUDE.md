# bridge-mcp-server · 生成能力壳无关封装层

本项目是 AI Foundation 系列的**能力层 MCP 封装（生成面）**：把系列的确定性生成能力（单模板直生成 / 多端组合生成 / 参数内省 / 单端候选菜单）按 MCP 规范暴露成工具 + 资源 + 提示词，供任意符合 MCP 的壳（Claude Code / Hermes / OpenClaw / 自研应用等）消费。治理链（桥 check 漂移/对齐、AI 维护契约）**不入本 server**，见 DESIGN §10。

> 设计定稿（2026-09 评审收敛）见 [docs/DESIGN.md](docs/DESIGN.md)（双路径×双链 / 底座协议两区 / 单端候选注册表 / 工具契约 / L1-L3 选择策略 / 跨仓落地清单）。**P3 生成面 server 骨架已起（uv 项目 + `servers/generation/` 六工具 + `bridge_mcp/` 共享胶水），已 init git**；尚未建远端、governance 占位未实现。收敛要点：单端走底座协议（params.json 自述）直读、零注册；多端纯 cli 消费桥（含新增内省面）；selection 单一真源在底座 params.json `selection` 区，combos.yaml combo 段只放不可约事实；单端候选注册表 templates.yaml 由本仓维护（薄菜单，非生成门槛）。

系列元信息（系列目的 / 总体设计思路 / 当前状态 / 姊妹项目位置 / copier 位置）由下方共享文件导入，只需维护一份：

@../ai-foundation-memory/series-overview.md

## 关键架构约束（来自 DESIGN.md，开发时不得违背）

- **双路径 × 双链**：单端（②-⑥）= git 地址 + 底座协议（params.json）自述、零注册（`generate_single`），直读不进桥；多端（① N≥2）= combos.yaml 注册组合、**纯 cli** 消费桥生成面（`list_combos`/`get_combo_params`/`generate_multi`，均经桥 cli `--json`）。治理链桥 `check` 服务 CI workflow，不进 server。
- **薄封装**：server 不做语义匹配/需求理解（那是壳的活），只做给菜单、校验 spec、确定性执行、结构化返回。
- **不搬生成逻辑进 server；桥也不反向长单端逻辑**：多端只消费桥统一 CLI 生成面（generate / 内省 list-combos、show-combo）；`check` 属治理链服务 CI，非生成面。单端只做 clone→读协议→指 template/→copier copy 通用包装。搬进来等于再造一个壳；单端 list/generate 不进桥 = 桥端冗余链路。
- **selection 单一真源**：深选择事实（suited_for/tradeoffs）只在底座 params.json `selection` 区写一份；combos.yaml combo 段只放组合不可约事实；server templates.yaml 是薄指针菜单，不抄 selection。
- **注册表是菜单不是门槛**：单端 templates.yaml、多端 combos 都只服务引导选型；不在册的 git 地址照常可 `generate_single`（零注册不变）。
- **一管道一工具**：整条生成链 = 一个工具（`generate_single` / `generate_multi`），绝不分拆成各端一个。
- **spec 边界**：只收结构化 spec（git 地址或组合名 + 参数 + target_dir），不收自然语言；派生参数禁止传入。
- **L1/L2/L3 覆盖单端与多端**（目标流程统一：需求→生成）：L1 确定性过滤可进 server（单端滤 templates.yaml、多端透传桥）；L2 有界推荐 + L3 用户确认留壳；推理地基 = 底座 selection 区 / 桥合并 selection。
- **共享参数 = 全链一致契约约束（U1 定案）**：跨多 unit 同名合并的共享参数 = 全链单一决策、单值广播；**不引入逐端参数命名空间**（ui-bff-api「分段认证」诉求 = 各 edge/unit 私有参数表达，非拆共享参数成 `ui.auth_mode` 等）。需要逐端差异时由底座声明自身上下游策略参数（如 BFF `upstream_auth`）。命名空间仅在「同底座多实例需独立配置」才考虑，用同 source 不同 unit key 解决。

## 设计文档

- [docs/DESIGN.md](docs/DESIGN.md) — 设计定稿（本仓唯一事实源）。改代码前先过它；评审意见/变更先改 DESIGN.md 再动代码。

## 开发 / 测试前置（本机约束，仅本仓记，勿写进系列记忆 series-overview）

**多端链测试 / 跑 server 前，必须先自行打包 fullstack-bridge 的可执行**，本仓没有也不打算暴露源码 cli.py 路径：

```bash
# 打包（fullstack-bridge 仓内）
cd ~/project/fullstack-bridge && uv sync --dev && uv run pyinstaller bridge.spec --noconfirm
# 装到仓库外稳定位置
mkdir -p ~/.local/bin && cp dist/bridge ~/.local/bin/bridge && rm -rf build dist
# 测试/运行本仓 server 时注入
BRIDGE_EXE=/home/jeff/.local/bin/bridge uv run pytest   # 或跑 server
```

- 桥 cli 入口**只认可执行**：`BRIDGE_EXE`（dist/bridge）> `BRIDGE`（PATH 命令）；`BRIDGE_CLI`（源码 cli.py）已移除（不暴露）。均未设 → 明确报错。
- 规则仅本仓/本机相关（机器上要有个打好的 bridge），无通用性——勿写入被各仓导入的 series-overview.md。
