# bridge-mcp-server 设计文档

> AI Foundation 系列 · 能力层壳无关封装（MCP）
> 状态：设计定稿（2026-09 评审收敛：双路径×双链、协议两区、单端候选注册表）。**P3 生成面 server 骨架已落地**（uv 项目，main 已推 origin）——目录见 §3.1；治理面（governance）为占位未实现；S3 协议 SCHEMA 契约点跨仓回写待办。

## 1. 定位

把系列的**生成能力**按 MCP 规范暴露成工具 / 资源 / 提示词，让**任意符合 MCP 的壳**都能消费：Claude Code、Hermes、OpenClaw、deepseek harness、自研应用……全都退化成「同一个 server 的不同客户端」。

**核心原则：能力是资产，壳是消费品；只认业界规范（MCP），不绑定任何壳。目标流程统一——用户给需求，server 侧收敛成 spec，生成项目目录。**

本 server 覆盖系列要生成的 6 类形态，归并成**两条路径 × 两条链**：

| 路径 | 形态 | 本质 | 生成链 |
|---|---|---|---|
| **单端直生成** | ② 纯前端全栈（Nuxt+BFF）③ 纯后端 ④ 纯前端 ⑤ 纯命令行 ⑥ 其它单模板 | **git 地址自述（协议直读），零注册** | clone 底座 → 读协议 → 指 `template/` → copier |
| **多端契约** | ① 前后端分离（前端可含 BFF，N≥2） | combos.yaml 注册组合 + 契约治理 | **纯 cli**：server 只消费桥 `cli.py`（含内省） |

两条链不同是**结构性正确**，不是实现欠账：多端背后有治理/注册（组合、version 基线、契约），值得一个确定性核心 + 注册表代 server 消化；单端背后只有「一个 git 地址」，底座自述即可，若让桥去代理单端 = 在桥端冗余一整条单端链路。**server 的每条腿消费各自的确定性核心，不追求单一接口。**

## 2. 设计由来（为什么不是 skill / agent）

- **skill / agent 是某个壳内的产物**：Claude Code 的 skill 只在 Claude Code 内可触发，agent 绑定主会话。把生成能力写成 skill = 知识又被锁进一个壳。
- 本系列要的是「一句话需求 → 生成项目目录」能力可被**多个壳 + 自研应用**驱动，因此能力必须下沉到壳外、以规范接口暴露。
- MCP 是跨厂商行业标准：工具面 + 资源 + 提示词三原语，恰好装下本能力的三层内容。
- 骨架生成完成后的「两端对照 CONTRACT.md 实现业务」属**多 agent 编排**（前端/后端实现 agent），是未来 A2A / 编排层的事，不在本 server 范围（见 §10）。

## 3. 架构分层（双路径 × 双链）

```
┌─ 壳层（各自的 agent loop / 交互 / 权限，无法也不必标准化）───┐
│  Claude Code · Hermes · OpenClaw · deepseek harness · 自研   │
└────────────────────────┬─────────────────────────────────────┘
                         │  MCP（stdio / streamable HTTP）
┌────────────────────────▼─────────────────────────────────────┐
│ MCP server（bridge-mcp-server）—— 薄封装 · 无业务逻辑          │
│   单端链（协议直读，零注册）           多端链（纯 cli 消费桥）  │
│     list_templates(注册表 L1)          list_combos             │
│     get_template_params(clone 读协议)  get_combo_params        │
│     generate_single                    generate_multi          │
│   Resources  templates 注册表(自持) · combos 注册表(cli 视图)  │
│   Prompts    generate_project_guide（玩法，引用注册表不抄内容）│
│   自持数据    templates.yaml（单端候选注册表 = 薄指针菜单）     │
└───────┬───────────────────────────┬───────────────────────────┘
  单端   │ clone → 协议 → copier      │ 多端：shell-out 桥 cli
┌────────▼──────────────────┐   ┌────▼───────────────────────────┐
│ 底座（git 地址自述，零注册） │   │ 确定性核心 / 治理（桥，多端）    │
│  template/ + copier.yml   │   │  cli.py generate/check/内省     │
│  根 params.json = 协议两区  │   │  combos.yaml（bases 注册表 +    │
│   params: 派生+hash 校验   │   │    combos(units≥2+edges+        │
│   selection: 策展+schema   │   │    combo 段 selection 仅不可约)  │
│   校验（底座 CI 自维护）     │   │  契约 combos/<combo>/copier.yml │
└───────────────────────────┘   └─────────────────────────────────┘
```

- **单端链不依赖桥 / combos.yaml**：给 git 地址就生成，底座用协议（params.json）自述参数与选择事实。
- **多端链依赖桥、且只消费桥的 cli（生成面）**：server 不读 combos.yaml、不 clone 底座内省——菜单 / 参数 / selection / 生成全经 `cli.py --json`。桥 `check`（漂移/对齐）属**治理链**（服务 bridge-gate / check-drift workflow），本 server **不消费、不暴露**（见 §10）。

### 3.1 仓库结构与多 server 边界（工程）

本仓可**同时维护生成面与治理面两类 MCP 能力**，但 **一面一个 server**，禁止杂糅在同一个 FastMCP 实例内（工具/资源/玩法命名空间互不串扰；也避免壳拿到它不该有的写治理操作面）。主线只实现**生成面 server**；治理面（check 链）未来需要时 = **本仓内另一个 server**（独立入口），不在生成 server 里加治理工具（§10）。共享仅限**无 MCP 面的薄胶水**（桥 cli shell-out / 协议读 / config），不含任何 tool/resource/prompt 注册。

```text
bridge-mcp-server/
├── docs/                        # DESIGN / implementation-plan / …
├── pyproject.toml               # uv 单项目（package=false）；dev: pytest
├── bridge_mcp/                  # 共享胶水（无 MCP 面）——仅供各 server 复用
│   ├── config.py                #   server 配置：桥 cli 可执行入口（env：BRIDGE_EXE > BRIDGE）
│   ├── bridge_cli.py            #   桥 cli shell-out client（--json，按 server 传子命令白名单）
│   ├── protocol.py              #   底座 params.json（两区）读取 / spec 校验
│   └── selection.py             #   selection 字段集（单一真源引用协议 SCHEMA，S3）
├── servers/
│   ├── generation/              # ⭐ P3 主线 · 生成面 MCP（stdio；六工具）
│   │   ├── server.py            #   FastMCP 组装 tools/resources/prompts
│   │   ├── tools_single.py      #   单端：list_templates / get_template_params / generate_single
│   │   ├── tools_multi.py       #   多端：list_combos / get_combo_params / generate_multi（纯 cli）
│   │   ├── resources.py         #   templates://  combos://
│   │   ├── guide.py             #   generate_project_guide（玩法，引用注册表不抄内容）
│   │   └── data/templates.yaml  #   单端候选注册表（薄指针）
│   └── governance/              # 未来车道 · 治理面 MCP（占位，见 series 后期待办）
│       └── README.md            #   边界与立项说明（不建 server.py）
└── tests/
    ├── unit/                    # 各 server 单测（mock 桥 cli / 协议 / copier）
    └── e2e/                     # 起 server：generate_single / generate_multi 真实核心
```

约束：一个进程只起**一个** server（`servers/<name>/server.py` 各自独立入口，无聚合 runner——避免把两面暴露进同一命名空间）；`templates.yaml` 归生成面 server 数据；governance 现仅占位文档，主线不写代码。

## 4. 边界不变量

1. **server 不自由思考、只执行**：不做语义匹配、不做需求理解——那是壳（agent）的智能胶水。server 只做：给菜单、校验 spec、确定性执行、结构化返回。（唯一例外：L1 确定性约束过滤，见 §8，规则非智能。）
2. **不搬生成逻辑进 server**：多端 shell-out 桥 `cli.py`；单端只做「clone → 读协议 → 指 template/ → copier copy」的通用包装。搬进来等于再造一个壳。**桥也不得反向长单端逻辑**——单端能力（列表 / 生成）不进桥。
3. **工具 = agent 能感知的一个完整意图**，不是内部函数。整条生成链 = 一个工具（`generate_single` / `generate_multi`），绝不分拆成「生成前端/后端/契约/README」各一个。
4. **spec 边界**：`generate_single` / `generate_multi` 只收**结构化 spec**（地址或组合名 + 参数 + target_dir），不收自然语言。模糊 → spec 留在壳里做；spec → 目录收在 server 里做。
5. **派生参数只读**：`when:false` 派生参数由 copier 自动算，agent 只填其输入，禁止直接传派生参数。
6. **生成 ≠ 治理**：单端是生成（地址自述、零注册）；治理（注册/基线/漂移）只属多端。单端 params 漂移由底座自己的协议 CI 兜，server/桥都不介入。
7. **底座协议 = 单一真源，两区不混写**：params.json 分 `params` 区（copier 派生、hash 校验）与 `selection` 区（人工策展、schema 校验、gen-params 轮转保留）。选择事实只在 `selection` 区写一份，不复制进任何注册表 / combos.yaml / server 数据。
8. **注册表是菜单、不是生成门槛**：单端 `templates.yaml`、多端 combos 注册表都只服务「引导选型」，**不在册的 git 地址照常可 `generate_single`**（零注册语义不变）；不在册的组合则不可 `generate_multi`（桥只认注册组合，治理面）。
9. **combo 段 selection 只放组合不可约事实**：凡能从 units 底座的 `selection` 区解析到的技术事实，禁止在 combos.yaml `combos.<name>.selection` 重复写（防双源漂移；桥 check 可 lint）。
10. **共享参数 = 全链一致契约约束（U1 定案）**：跨多 unit 同名合并为共享的参数，声明即承诺「该参数在整条链是单一决策」，桥/CLI 以单值广播到全链。**不引入逐端参数命名空间**——ui-bff-api 这类「分段认证（UI↔BFF opaque、BFF↔真后端 jwt）」的真实诉求不是「同一共享参数需分段取值」，而是**该参数不属于共享语义**：逐端差异应表达为对应 edge / unit 的私有参数（由底座自行声明对下游/上游策略），由逐跳契约各自承载。需要分段认证时 = 底座定义自己的上游/下游策略参数（如 BFF 的 `upstream_auth: passthrough|reissue`），而非把共享 auth_mode 拆成 `ui.auth_mode/bff.auth_mode/api.auth_mode`。命名空间只在「同一底座于同一 combo 出现多次需独立配置」（如双前端共用 react 底座）才值得考虑，而那用「同 source 不同 unit key」解决（每 unit 独立生成实例，天然独立取值）。（架构评审 T1/U1，2026-09-04 定案。）

## 5. 真源与运行形态

### 5.1 单端路径（零注册；底座 = git 地址自述）

| 真源 | 位置 | 角色 |
|---|---|---|
| 底座 git 地址 | 唯一身份输入 | 零注册——`template/ + copier.yml + 根 params.json` 自述 |
| params.json（协议两区） | 底座根目录 | 参数基线 + 选择事实的自述载体；底座 CI（gen-params + hash/schema 校验）自维护 |
| templates.yaml | **本 server 仓** | 单端候选注册表（薄指针菜单，见 §5.3），唯一不在底座侧的策展数据 |

**单端链（对任意底座相同，一个通用函数）**：
`clone <url> → 读根 params.json（两区：原生/派生参数 + suited_for/tradeoffs） → 校验 spec → 指 <repo>/template → copier copy → 底座自带 _tasks 装依赖`。
（copier 不能直接消费底座 git URL 根，因为 copier.yml 在 `template/` 子目录，故需 clone 后指向 template/。）

**base 兼容**：系列底座必带 params.json；非系列 / 未接入协议的裸地址（⑥ 其它）允许回退解析 `template/copier.yml` 拿参数（无 selection 区则只给参数）。

### 5.2 多端路径（治理真源在桥；server 只消费 cli）

| 真源 | 位置 | 角色 |
|---|---|---|
| combos.yaml | fullstack-bridge 根 | 多端治理真源：bases git 注册表 + combos（units≥2 + edges + combo 段 selection）+ version 基线 |
| 底座 params.json（两区） | 各底座 | 参数与选择事实的**底座侧真源**；桥 clone/烘焙之（`bases_params/` 进可执行，含 selection） |
| cli.py / dist/bridge | fullstack-bridge | 多端执行器 + **内省面**（见 §5.4），Click，`--json` 机器输出 |
| combos/\<组合\>/copier.yml | fullstack-bridge | 契约模板参数声明 |

server 配置需声明：桥 cli **可执行入口**（**纯 env 注入**，代码不内嵌默认路径）——解析链 `BRIDGE_EXE`（dist/bridge 可执行，首选）> `BRIDGE`（PATH 命令）；均未设则明确报错。**只认可执行，不暴露源码 cli.py 路径**（BRIDGE_CLI 已移除）；本地测试 = 打包桥的可执行再注入。server 对该入口之外桥的内部（combos.yaml、底座缓存）**零感知**。

**多端链（纯 cli，生成面）**：`list_combos` / `get_combo_params` → 桥内省；`generate_multi` → 桥 `generate`。桥已单模式、只收注册 combo。治理链（桥 `check`：漂移/对齐）服务 CI workflow，**本 server 不消费、不暴露**——生成面与治理面分开（§10）。

### 5.3 单端候选注册表 templates.yaml（薄指针，本 server 维护）

目标流程统一（用户需求 → 生成），单端也要「引导选底座」，故 server 需一份候选清单。它放 server 侧最合适：单端无桥可借，单端专属底座（⑤ CLI / ② Nuxt+BFF / ⑥ 其它，永不进多端 combos.yaml）只有这里能有机器可读归宿；也只有 server 能把「单端底座 ∪ 多端组合」汇成壳看到的统一目录（见 §9）。

```yaml
# templates.yaml —— 单端候选注册表（菜单/引导；不是生成门槛）
templates:
  vite-react-spa-template:     # 共享底座用与 combos.yaml bases 相同的裸名（同一身份）
    git: https://github.com/jianghua-developer/vite-react-spa-template.git
    kind: frontend             # 离线 L1 过滤（frontend/backend/cli/…）
    stack: [react, vite, typescript]
    forms: [④纯前端]            # 该底座可直生成的形态（②-⑥ 类型标签）
  python-fastapi-template:
    git: …
    kind: backend
    stack: [python, fastapi]
    forms: [③纯后端]
  my-cli-template:             # 纯单端底座：只在此注册，永不进桥
    git: …
    kind: cli
    stack: [python, click]
    forms: [⑤纯命令行]
```

**字段纪律**：表内只放**离线 L1 需要的身份/标签**（name/git/kind/stack/forms）。`suited_for / tradeoffs` 等深选择事实**不进这张表**——单一真源在底座 `selection` 区，避免双写漂移，也保证「不在册地址经协议自述」成立。深事实的按需读取走 `get_template_params`（§6.2，只对 L2/L3 短名单 clone）。

### 5.4 底座协议两区（params.json）与桥内省面（跨仓契约要求）

**params.json 两区**（fullstack-param-protocol 升版，底座 CI 配套）：

- `params` 区：copier 派生（原生/派生/choices/default），与 copier.yml **hash 校验**，机制不变；
- `selection` 区：人工策展（`suited_for: []` / `tradeoffs: []`），**schema 校验**、不与 copier.yml 对 hash；`gen-params.py` **轮转保留**（regen 时读回既有 selection 原样写回）；
- `schema_version` 升版；两区由底座 CI 各自校验。

**桥 cli 内省面**（多端，`--json`；为满足「server 只消费 cli」，桥需新增）：

- `list-combos [过滤…]` → `[{ combo, units, edges, stack, selection }]`（selection 为**合并完整值** = 各 unit 底座 `selection` 区并集 + combo 段；桥烘焙 `bases_params/` 已自带底座 selection，零新增机制）；
- `show-combo <combo>` → 参数基线（原生/派生）+ 合并 selection；
- `generate <combo> <project>` 已有；选项由各 unit params.json schema 数据驱动。（桥 `check` 属治理链、服务 CI workflow，非生成面内省——server 不暴露）

## 6. 工具契约

> 本 server 暴露**六个生成面工具**（单端 3 + 多端 3），不含治理链：桥 `check`（漂移/对齐）与「AI 维护契约」属治理/authoring 面，服务 CI workflow 与维护 agent，不在此暴露（§10）。

### 6.1 generate_single（单端，类型 ②-⑥）

- 入参（结构化，JSON）：
  ```jsonc
  {
    "template": "https://github.com/…/<base>.git",  // 底座 git 地址（唯一身份）
    "version": "<git-ref>",                          // 可选，缺省 latest
    "params": { … },                                  // 仅原生参数；派生参数禁止
    "target_dir": "/abs/path/to/app"
  }
  ```
- server 侧严格校验：`template` 为 git 地址；clone 后读其 params.json（无协议则回退 copier.yml）；`params` 键 ⊆ 原生参数集（派生 → 拒绝）；值类型/choices 合法；`target_dir` 为空或不存在。
- 执行：clone → 指 template/ → copier copy。
- 返回：`{ status, target_dir, structure, readme_path, 后续提示 }`。
- **零注册**：不在 templates.yaml 的地址同样可生成；注册表只是引导菜单（§4.8）。

### 6.2 get_template_params（单端参数内省 = 落参与选择地基）

- 入参：`git_url`
- 返回：clone 后读底座 params.json 两区——
  - **原生参数（要问的）**：`name / type / required / has_default / default / choices`
  - **派生参数（自动算的，只读）**：`name / derived: true / 由哪些输入算出`
  - **selection（选择地基）**：`suited_for / tradeoffs`（底座 `selection` 区；无协议底座缺省）
- 职责：单端 L2/L3 的**选择事实来源**（对短名单按需读）与落参前的参数集来源。**零注册**——协议自述，不查 templates.yaml 以外任何注册表。

### 6.3 list_templates（单端菜单，L1 候选集）

- 入参（可选约束过滤）：`kind` / `stack` / `form` 等用户显式偏好（技术栈/形态过滤）。
- 返回：`[{ name, git, kind, stack, forms }]`——**离线**，只读 templates.yaml（纯规则过滤，无网络）。
- 职责：单端 L1 候选集。深选择事实不在此返回（在底座 `selection` 区，L2 经 6.2 按需读）。

### 6.4 generate_multi（多端，类型 ①）

- 入参 spec（结构化，JSON）：`{ combo, params, target_dir }`。
- server 侧严格校验（经桥内省或桥自身）：`combo` 在注册表内；`params` ⊆ 该组合原生参数集；值类型/choices 合法；`target_dir` 为空或不存在。
- 执行：shell-out `cli.py generate <combo> <project>`（桥单模式、只收注册 combo）。
- 返回：`{ status, target_dir, structure, contract_path, readme_path, 后续提示 }`。

### 6.5 list_combos（多端菜单，L1 候选集；经桥）

- 入参（可选约束过滤，透传给桥）：`stack` / `frontend_kind` / `backend_kind` 等用户显式偏好（按技术栈/形态过滤；units key 是目录名不承载技术栈语义）。
- 返回：`[{ combo, units, edges, stack, selection }]`——`selection` 为桥合并的**完整值**（底座并集 + combo 段），供 L2 直接用。
- 职责：多端 L1 候选集 + L2 选择地基。**纯过滤/回传不是思考**，可放 server；L2 有界语义匹配 + L3 用户确认是壳的活（见 §8）。

### 6.6 get_combo_params（多端参数基线；经桥）

- 入参：`combo`
- 返回：经 `show-combo` 的参数清单（原生/派生分列）——桥读各 unit 底座 params.json，同源数据驱动 CLI 选项，不硬编码。
- **共享参数语义**：返回清单中标注 `shared: true` 的参数 = 全链一致单值（§4 不变量 10）——壳/agent 填一个值即广播全链；无逐端命名空间。agent 不需也不能为各端分别指定共享参数取值；需要逐端差异时用对应 unit 的私有参数（见 §4 不变量 10 决策）。

## 7. Resources / Prompts

- **Resources（只读真源）**：
  - `combos://` —— 多端注册表视图（数据经桥 `list-combos --json` 物化，只读）；
  - `templates://` —— 单端候选注册表（server 自持 templates.yaml，只读）。
  两族都不抄 selection 进自身之外的第二份（选择事实只在底座 `selection` 区）。
- **Prompts：`generate_project_guide`** —— 双路径玩法做成一份 MCP Prompt：先判定形态 → 单端走 `list_templates`（或用户直给地址）→ 多端走 `list_combos`；L1/L2/L3 仪式；何时反问、派生参数勿传、spec 校验规则。**内容引用注册表、不把清单抄进 Prompt**，避免玩法变第二真源。

## 8. 技术栈 / 形态选择策略（L1 过滤 / L2 有界推荐 / L3 确认）

**单端与多端都做选择**（目标流程统一）。候选空间 = 单端底座 ∪ 多端组合；先由壳判定形态（§9 步骤 2），再在各自候选集内走 L1→L2→L3。

- **L1 硬过滤（确定性，机器执行）**
  - 单端：`list_templates` 按 kind/stack/forms 过滤（读 templates.yaml，纯规则，无网络）；
  - 多端：`list_combos` 透传约束过滤（桥内）。
- **L2 有界推荐（LLM 在约束内推理，不自由发挥）**
  - 自由文本需求 → **只在 L1 过滤后的候选集内**做语义匹配；
  - 必须输出结构化推荐：`{ 候选, 推荐理由, 备选方案 }`；
  - 推理地基 = **人工策展的选择事实**：单端对同 kind 短名单经 `get_template_params` 读底座 `selection` 区（1-3 次 clone 可接受）；多端直接用 `list_combos` 返回的合并 selection。LLM 不背组合/底座知识、不被允许自由发挥；
  - 留在壳（agent 侧），被 L1 候选集 + 策展事实夹住。
- **L3 人为确认闸门（运行期，人拍板）**
  - L2 推荐带理由 + 备选呈现给用户 → 确认或改选 → 才进入落参（§9 步骤 3）；
  - 技术栈是开发者**个人取舍**（React vs Vue 主观），AI 不代用户定死；
  - guide Prompt 强制规定：「推荐必须先给用户确认，不得直接生成」。

**选择事实边界（单一真源纪律）**：

- **底座侧（params.json `selection` 区，主源）**——关于技术/底座的选择事实：`suited_for`（适用场景）、`tradeoffs`（相对同类底座的取舍）。一份写，单端多端同读；底座自述，随底座演进。
- **combo 段（combos.yaml `combos.<name>.selection`，叠加源，允许为空）**——组合级不可约事实：整体拓扑价值（如 ui-bff-api 三单元链）、契约治理成熟度等。凡可从 units 底座 `selection` 区解析到的，禁止重复写（§4.9）。
- **完整 combo selection = units 底座 selection 并集 + combo 段**（桥合并后经 cli 返回）。

## 9. 场景流程（双路径统一目标）

> 输入：「我现在有 ***** 需求，帮我生成一个项目」（多为模糊/缺失）

```
├─ 0 澄清 [壳]          仅当需求太糊 → 问判别性问题，不瞎猜
├─ 1 理解 + 归纳特征 [壳] → 产出 project_brief（结构化，见下）
├─ 2 判定形态 [壳]      —— 决定走哪条链：
│      多端(前后端分离需契约) → A；纯底座(纯前端/纯后端/CLI/单仓全栈) → B
│  A. 多端：L1 list_combos → L2（合并 selection）→ L3 确认
│     → get_combo_params 落参 → generate_multi(combo, spec)
│  B. 单端：用户已给/选定底座地址 → 直走落参；
│     未定 → L1 list_templates(注册表) → L2 get_template_params(短名单读 selection) → L3
│     → generate_single(git_url, spec)
└─ 返回结构 + 契约/README 位置（多端）；结构 + README（单端，底座自带）
```

**project_brief 结构草案**（壳产出，server 不强制，但应持久化——将来多端业务实现也吃它）：

```jsonc
{
  "summary": "一句话描述",
  "features": ["…"],          // 核心功能点
  "entities": ["…"],          // 数据实体（可选）
  "cross_cutting": {          // 横切需求（可选）
    "auth": "…", "db": bool, "child_apps": ["…"]
  }
}
```

## 10. 非目标 / 演进

- **不做**「骨架之后的两端业务实现」：那是对着生成的 CONTRACT.md 派前端/后端 agent 各自实现，属多 agent 编排 / A2A 层（本系列未来项），不进本 server。
- **治理/authoring 面不进本 server**：桥 `cli.py check`（漂移/对齐）服务 CI workflow（bridge-gate / check-drift）；「AI 维护契约」（drift issue → 改 `combos/<组合>/` + bump version，契约即 wiki 的 authoring loop）属维护 agent。两者若未来需跨壳稳定暴露，另行评估**独立的治理面 server**（可与生成 server **同仓并存**，各自独立入口，见 §3.1；series-overview 后期待办）——**生成 MCP 与治理/authoring 永不合一**。
- **不做**语义推荐进 server：server 只给菜单 + 数据（templates/combos/selection），L2 推理在壳。
- **单端生成保持零注册**：注册表（templates.yaml）只是引导菜单，不做「注册作为生成前提」；「常用底座快捷别名」属可选 UX。
- **桥不加单端能力**：单端的 list/generate 不进桥 cli——那是桥端冗余的单端链路。
- **扩展零改动（对 server 与 cli 代码）**：多端加组合 = 改桥 combos.yaml（+ combo 段可选）；单端加底座 = 底座自述（协议）+ templates.yaml 一行。两处都是数据，无代码改动。
- 壳侧可留**可选快捷键**：如 Claude Code 的 `generate-project` skill，SKILL.md 只引用本 server 工具，不重复造知识。

## 11. 技术选型（草案，待评审确认）

- **Python >= 3.11 + uv**（系列惯例，非发布型工具项目：`[tool.uv] package=false`）。
- **FastMCP**（构建于官方 `mcp` SDK 之上的薄封装）：装饰器式声明 tools/resources/prompts，内置 stdio 与 streamable HTTP。
- **传输**：stdio 为主（本机壳消费）；streamable HTTP 预留（远程 / 自研 app）。
- **测试**：pytest 单测（server 工具逻辑，mock 掉协议读 / copier / 桥 cli）+ e2e（起 server：generate_single 打真实 copier 于临时目录清理；generate_multi shell-out 真实 `cli.py generate` 于临时目录清理；list_templates / list_combos 契约冒烟）。

## 12. 参考

- [fullstack-bridge docs/generation-architecture.md](../../fullstack-bridge/docs/generation-architecture.md)（系列生成能力架构重构方案；已随重构归档，仅重构分支保留）
- fullstack-bridge：`combos.yaml`（bases/units/edges/combo 段 selection）/ `combos/<组合>/copier.yml` / `cli.py`（generate/check/内省）
- fullstack-param-protocol：`params.json` 协议（两区：params + selection）/ `SCHEMA.md` / `gen-params.py`
- 底座仓：`template/ + copier.yml + 根 params.json`（自述）
- `../ai-foundation-memory/series-overview.md`：系列元信息（目的 / 总体设计 / 状态）

## 13. 落地顺序与跨仓改动清单（评审收敛后）

本 DESIGN 是 bridge-mcp-server 的事实源，但收敛结论牵动三个上游仓（皆为**待办**，先于或并行于本仓骨架）：

| # | 仓 | 改动 |
|---|---|---|
| 1 | fullstack-param-protocol | `SCHEMA.md` 升版定义两区；`gen-params.py` 支持 `selection` 区轮转保留 + schema 校验 |
| 2 | 底座 ×N（react/vue/fastapi，及未来单端底座） | 每仓补 `selection` 区策展内容 + 升级 gen-params/CI（两区各自校验） |
| 3 | fullstack-bridge | cli 加多端内省 `list-combos` / `show-combo`（`--json`，合并完整 selection）；combos.yaml combo 段收窄为仅不可约；烘焙 `bases_params/` 自动带上底座 selection（零新增机制） |
| 4 | bridge-mcp-server（本仓） | 建 pyproject / FastMCP 骨架；templates.yaml 注册表；按 §6 实现工具；玩法 Prompt；§11 测试 |
