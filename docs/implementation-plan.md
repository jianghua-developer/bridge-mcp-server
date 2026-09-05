# 跨仓落地实施计划（分项目 × 分阶段）

> 配套 [DESIGN.md](DESIGN.md) §13 的展开版。定稿架构：**单端走底座协议链（零注册）· 多端纯 cli 消费桥**；selection 单一真源在底座 params.json `selection` 区。本计划把跨仓改动拆成**阶段（依赖主线）**与**项目（各仓工作包）**两个视图，每项标仓、改动、理由、验收。来源：[series-overview 待办](../../../ai-foundation-memory/series-overview.md) 的「bridge-mcp-server 评审收敛 → 跨仓改动」。

## 1. 涉及项目与依赖

| 项目 | 角色 | 方向 |
|---|---|---|
| **P** fullstack-param-protocol | 协议仓：params.json 两区规范 + gen-params.py | 无前置，先行 |
| **B** 底座 ×N（react / vue / fastapi，未来 cli/nuxt 等） | 内容仓：补 selection 区策展 + CI | 依赖 P |
| **F** fullstack-bridge | 治理/执行：cli 内省面 + selection 合并 + combo 段纪律 | 依赖 P + 至少 1 个 B 有真实 selection 可测 |
| **S** bridge-mcp-server | 能力层：FastMCP 骨架 + templates.yaml + 工具 + 玩法 | 依赖 P/B/F 契约就绪（单端腿可提前 fixture 并行） |

```
P0 协议升版（P 仓）──► P1 底座接入（B 仓：示范→铺开）──► P2 桥内省面（F 仓）──► P3 能力层骨架（S 仓）
                             ▲                                   │
                             └── P2 可对「已有 selection 的底座」开发/测试 ──┘
```

## 2. 全局阶段总览（主线）

| 阶段 | 名称 | 涉及项目 | 出口标准（Gate） |
|---|---|---|---|
| P0 | 协议定基 | fullstack-param-protocol | SCHEMA 升版 + gen-params 双区支持 + 测试；旧 params.json（无 selection）向后兼容 |
| P1 | 底座接入（示范 → 铺开） | 底座仓 ×N | ≥1 底座（示范）selection 区落地且 CI 双区校验通过；其余底座铺开 |
| P2 | 桥内省面 + selection 合并 | fullstack-bridge | `list-combos`/`show-combo --json` 返回合并 selection；combo 段纪律生效；frozen bake 含 selection |
| P3 | 能力层骨架落地 | bridge-mcp-server | MCP server 起得来，六工具 + 两资源 + 玩法 Prompt 按 DESIGN §6 实现，单测 + e2e 过 |
| P4 | 配套与未来（可选） | 各仓 | 玩法打磨、壳侧快捷键、纯单端底座入册流程文档 |

## 3. 分阶段任务清单

### P0 · 协议定基 —— fullstack-param-protocol（先行，无前置）

- [ ] `SCHEMA.md` 升版（`schema_version`），定义 params.json **两区**：
  - `params` 区：copier 派生（原生/派生/choices/default），语义与 hash 基线**不变**；
  - `selection` 区：人工策展，字段 `suited_for: []` / `tradeoffs: []`，**schema 校验**、不与 copier.yml 对 hash；
  - 明确「无 selection 区 = 合法（向后兼容）」。
- [ ] `gen-params.py`：派生 params 区照旧；新增 **selection 区轮转保留**（regen 读回既有 selection 原样写回，缺失则留空/缺省）；`--verify` 拆两路：params↔copier.yml hash、selection 仅 schema。
- [ ] 协议仓测试：无 selection 旧文件能正常 regen/verify；有 selection 的文件 regen 后 selection 不被冲掉；非法 selection（非数组/类型错）verify 失败。
- **理由**：selection 是人工策展、copier 不可派生，须与自动派生区共存而不被 regen 冲掉；params.json 是单端直读 + 多端烘焙的共同载体，先定协议一切下游才有依据。
- **验收**：`gen-params.py --verify` 对一个不带 selection 的旧底座 params.json 通过；对一个带 selection 的手改文件，regen 后 selection 保留。

### P1 · 底座接入 —— 底座仓 ×N（示范 → 铺开）

- [ ] **示范底座先走**：选 `python-fastapi-template` 或 `vite-react-spa-template` 之一，跑通全流程并经 ai-foundation-review，锁定模式后再复制到其余底座。
- [ ] 每仓：同步 vendored `gen-params.py`（自协议仓）；补 `params.json selection` 区——**内容人工策展**：`suited_for`（适用场景，自然语言若干条）/ `tradeoffs`（相对同类底座取舍）。
- [ ] 每仓：CI `params-check.yml` 拆双区校验（params↔copier hash、selection schema）；pre-commit 重新生成。
- [ ] 未来纯单端底座（cli / nuxt+BFF）接入时同此流程（现无则不阻塞）。
- **理由**：选择事实单一真源在底座自述；单端 L2 直读、多端桥合并 selection 都依赖它，缺了则两链都无选择地基。
- **验收**：示范仓 params.json 双区齐备、CI 绿、评审零阻塞；其余底座铺开同标准。

### P2 · 桥内省面 + selection 合并 —— fullstack-bridge（依赖 P0 + ≥1 底座有真实 selection）

- [ ] cli 新增多端内省（`--json`）：
  - `list-combos [过滤…]` → `[{ combo, units, edges, stack, selection }]`，`selection` 为**合并完整值** = 各 unit 底座 selection 并集 + combo 段；
  - `show-combo <combo>` → 参数基线（原生/派生，复用现有 param_schema 数据源）+ 合并 selection。
  - 数据源复用现成机制：源码读缓存 clone 的 params.json，frozen 读烘焙 `bases_params/`（selection 随 params.json 自动进 bake，零新增机制）。
- [ ] combos.yaml：`combos.<name>.selection`（combo 段）语义收窄——只放组合不可约事实（拓扑 / 治理成熟度等），允许为空；顶部注释写明纪律。
- [ ] 结构校验：在 validate/check 侧（结合审查暂缓项 **R1/A2**：校验归属放 check 入口，一并落实）对 combo 段做结构 schema 校验；与底座 selection 重复仅 advisory lint。
- [ ] README/文档同步 cli 新增子命令；pytest 补 list-combos / show-combo（含 frozen 模式烘焙 selection）。
- **理由**：多端链「server 只消费 cli」需要菜单/参数/selection 内省面；server 不再直读 combos.yaml、不再 clone 底座内省。R1/A2 同批文件顺手归位，避免二次改动同一模块。
- **验收**：`cli.py list-combos --json` 输出含合并 selection；`show-combo` 双区信息齐；无 selection 的底座只出 params 不报错。

### P3 · 能力层骨架落地 —— bridge-mcp-server（依赖 P0-P2 契约就绪；单端腿可提前 fixture 并行）

- [ ] init git + `pyproject.toml`（uv，FastMCP，非发布型）+ **目录骨架（DESIGN §3.1）**：`bridge_mcp/` 共享胶水（config/bridge_cli/protocol/selection）+ `servers/generation/`（主线入口 + templates.yaml）+ `servers/governance/`（占位 README，不写代码）；server 配置桥 cli 入口（纯 env：`BRIDGE_EXE` > `BRIDGE` > `BRIDGE_CLI`，无默认路径）。
- [ ] `templates.yaml`（单端候选注册表，薄指针）：现可用单端底座（react/vue/fastapi，①③④形态）各一条 `name/git/kind/stack/forms`；纯单端（cli/nuxt）留位。**不抄 selection**。
- [ ] 工具（DESIGN §6，**六个生成面工具**，不含 check/治理）：
  - 单端：`list_templates`（读 templates.yaml 离线 L1 过滤）、`get_template_params`（clone → 读 params.json 两区；无协议地址回退 copier.yml）、`generate_single`（clone → 校验 → 指 template/ → copier）；
  - 多端：`list_combos` / `get_combo_params` / `generate_multi` —— 全部 shell-out 桥 cli `--json`（含 `--json` 契约解析，不直读 combos.yaml）。
  - **不暴露**：桥 `check`（漂移/对齐）属治理链服务 CI workflow，server 不消费不暴露（DESIGN §6/§10）；「AI 维护契约」同理（authoring 面）。
- [ ] Resources：`templates://`（自持）、`combos://`（桥内省物化，只读）；Prompts：`generate_project_guide`（引用注册表、不抄清单）。
- [ ] 严格校验：spec 结构化、派生参数禁止、`target_dir` 空/不存在、值类型/choices。
- [ ] 测试：单测 mock 掉 clone / 协议读 / copier / 桥 cli；e2e 起 server——`generate_single` 打真实 copier、`generate_multi` 打真实 `cli.py generate`，临时目录清理。
- [ ] **S3（P2 评审遗留，2026-09-05）**：selection 字段集单一真源对齐——把 `suited_for`/`tradeoffs` 字段集写进协议 `SCHEMA.md`（契约点）；能力层消费时对底座 selection 含桥未知字段**显式告警而非静默丢弃**（桥 `SELECTION_FIELDS` 随协议演进同步，防内省面比底座策展少）。
- **理由**：DESIGN 定稿落地；依赖 ①-③ 契约就绪，保证多端链只消费 cli 的契约可测。
- **验收**：stdio 起 server；六工具可调用；单端/多端各一条 e2e 生成出目录。（check 治理链不出现在工具面）

### P4 · 配套与未来（可选，非阻塞）

- [ ] 玩法 Prompt 打磨（双路径仪式、L2 输出结构化推荐样例）。
- [ ] 壳侧可选快捷键（如 Claude Code `generate-project` skill 只引用本 server 工具）。
- [ ] 纯单端底座入册流程文档（新增底座 = 协议自述 + templates.yaml 一行的 SOP）。
- [ ] 未来组合（python-vue / ui-bff-api 三单元链）就绪后：验证 combo 段「仅不可约」纪律是否够用，若不够回改 DESIGN §8。

## 4. 分项目任务总表（Rollup）

| 项目 | 涉及阶段 | 关键文件 / 模块 | 主要任务数 | 出口 Gate |
|---|---|---|---|---|
| fullstack-param-protocol | P0 | `SCHEMA.md`、`gen-params.py`、协议仓测试 | ~3 | 双区规范 + 轮转保留 + verify 双路 |
| 底座 ×N | P1 | 各底座 `params.json`、vendored gen-params、`.github/workflows/params-check.yml`、pre-commit | 每仓 ~3 | selection 区落地 + CI 双区绿 |
| fullstack-bridge | P2 | `cli.py`、`bridge/combos.py`、`combos.yaml`、`bases_params/` 烘焙、check/validate | ~4 | 内省两命令 + 合并 selection + combo 段纪律（含 R1/A2） |
| bridge-mcp-server | P3 | `pyproject.toml`、FastMCP 入口、`templates.yaml`、工具/资源/玩法、pytest | ~6 | server 可起、六工具过、单端/多端 e2e |

## 5. 里程碑与检查点

| 里程碑 | 内容 | Gate 判据 |
|---|---|---|
| M0 | P0 合入协议仓 | SCHEMA 升版 + gen-params 向后兼容测试绿 |
| M1 | P1 示范底座合入 | 示范仓双区 CI 绿 + ai-foundation-review 零阻塞 → 复制铺开 |
| M2 | P2 合入桥 | list-combos/show-combo 单测 + frozen bake 含 selection 绿；combos.yaml 纪律生效 |
| M3 | P3 合入能力层 | server 起得来 + 六工具 + 单端/多端 e2e 绿；Claude Code `add-mcp` 冒烟 |

**跨项目规则**：
- 每仓改动各自开分支，合入前走系列既有 **ai-foundation-review**（报告归档 `~/project/ai-foundation-review/reports/<项目>/…`）；
- 每个里程碑更新 [series-overview](../../../ai-foundation-memory/series-overview.md) 的「目前状态」行与待办勾选；
- 变更先改 [DESIGN.md](DESIGN.md) 再动代码（本仓唯一事实源）。

## 6. 风险与注意事项

- **selection 内容策展质量**（P1）：suited_for/tradeoffs 需真实业务语义，非抄模板；示范底座先锁文案再铺开，避免九仓八样。
- **向后兼容**（P0/P2）：无 selection 的旧 params.json、未接入协议的单端地址都不得报错——单端回退 copier.yml、多端只出 params。
- **frozen 烘焙**（P2）：`dist/bridge` 的 bases_params 在构建时生成——更新底座 selection 后需**重建可执行**，菜单才带新事实；README 注明。
- **并行窗口**（P1→P3）：P2 可对「已有 selection 的示范底座」先行开发；P3 单端腿可用 fixture 提前起，避免主线全串行拉长。
- **R1/A2 顺带归位**（P2）：桥结构校验归属已挂审查暂缓项，与本次改动同文件，勿重复返工。
- **combo 段纪律靠自觉+lint**：结构性 schema 强校验，与底座 selection 的语义重复只能 advisory；文案评审把关。

## 7. 验收命令样例（届时核对）

```bash
# P0
uv run gen-params.py --verify              # 双区各自校验

# P1（在示范底座仓）
uv run gen-params.py                       # regen 后 selection 保留
uv run pytest                              # CI 等价双区校验

# P2
uv run python cli.py list-combos --json    # selection = units 并集 + combo 段
uv run python cli.py show-combo python-react --json

# P3（本仓，起 server 后）
uv run pytest                              # 单测（mock 桥/copier）
# e2e：generate_single / generate_multi 打真实核心于临时目录
```
