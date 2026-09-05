"""生成面 server · generate_project_guide 玩法 Prompt（DESIGN §7）——canonical 玩法全文。

引用六工具与两资源，不把注册表/selection 抄进文案（玩法从真源派生，避免第二真源）。
壳侧 skill（skills/generate-project）只引用本流程，不重复写（防双源漂移）。
"""

_GUIDE = """# 项目生成玩法（生成面 · 需求 → 项目目录）

你是「生成」环节：把一句需求收敛成**结构化 spec** 并调用本 server 工具产出项目目录。
菜单 / 参数 / selection 一律以工具/资源返回为准；不编造底座、组合、参数或取值。

流程（最小集）：0 澄清 → 1 判形态 → 2 L1 过滤 → 3 L2 推荐 → 4 L3 确认（不可跳）→ 5 落参 → 6 生成 → 7 汇报。

## 0 澄清（需求太糊先问，不猜）
判别问题示例：是「前后端一体（单端）」还是「前后端分离、要契约自动对齐（多端）」？
技术栈有无偏好（React / Vue / FastAPI …）？要做纯前端 / 纯后端 / CLI / 单仓全栈？项目目录放哪、叫什么？

## 1 判定形态
- **多端（①）**：分离部署 / 前后端多端共用数据模型 / 要 CONTRACT 契约驱动两端实现 → 读 combos://catalog，用 list_combos。
- **单端（②-⑥）**：纯前端 / 纯后端 / CLI / 单仓全栈 → 用户给了 git 地址直走；未给 → 读 templates://catalog + list_templates 引导。
  （无 params.json 的通用 copier 模板 git 地址也可直生成——回退 copier.yml 内省，无 selection 区。）

## 2 L1 硬过滤（仅在有显式约束时）
受控取值（现役，来自工具/资源返回，不要发明新词）：
- `list_templates`：`kind` ∈ {frontend, backend, cli, fullstack}；`form` ∈ {spa, api, fullstack, cli}（语义：纯前端单页 / 纯后端 API / 单仓全栈 / 纯命令行——以该行 forms 现役值为准）；`stack` 用注册表里的技术 token。
- `list_combos`：`stack` 用单元 `stack` 文本中的技术 token（如 react / vue / fastapi）。
无显式约束可跳过 L1，直接给候选。

## 3 L2 有界推荐（只在 L1 候选内；输出可预期结构）
匹配启发：把需求里的技术/形态线索词对照各候选 selection——单端对短名单用 `get_template_params` 读底座
`suited_for/tradeoffs`；多端 `list_combos` 已含合并 selection——取 suited_for 覆盖需求最多的 1 个候选。
**必须输出结构化推荐**（给用户看）：
{
  "推荐": "<combo 或 template 名>",
  "理由": "<引用 suited_for/tradeoffs 的一句人话>",
  "备选": ["<同 kind/同技术族候选>", "…"],
  "待确认参数": ["<落参要问的必填/关键原生参数>", "…"],
  "建议目录": "<如 my-app，小写连字符>"
}

## 4 L3 确认（闸门，不可跳）
把上面的推荐 + 备选 + 所需参数给用户，确认或改选后才继续。技术栈取舍是开发者的决定，AI 不代定。

## 5 落参（先内省拿参数基线，最小集）
- 单端 `get_template_params(git_url)` → native（要问的）/ derived（自动算，只读勿传）/ selection。
- 多端 `get_combo_params(combo)` → params（原生）/ internal（勿传）/ derived（只读）。
- **shared 语义（U1）**：多端 params 里标 `shared: true` = 全链单一决策——**给一个值即广播全链**，
  不要试图给各端分别取值；需要逐端差异时那是该单元私有参数的事（由 get_combo_params 各参数面给出）。
- 只问 native 里必填/无默认或用户要覆盖的关键参数，其余用默认即可。
- 缺信息就问，不瞎猜。

## 6 生成
- `generate_single(git_url, params, target_dir)` 或 `generate_multi(combo, params, target_dir)`。
- 只传原生参数（派生 / internal 禁止）；`target_dir` 须为空或不存在（否则拒绝覆盖）。

## 7 失败修正
工具报错（未知/派生参数、choices 非法、缺必填、target_dir 非空）→ 读错误改 spec 或换 target 后重调；
不要用同一错误反复重试。

## 8 汇报
成功后给用户：单端 = 结构 + README 位置；多端 = 结构 + README 入口 + `docs/CONTRACT.md` 契约路径
（两端对照契约实现业务）。返回里已含 `next_steps`，照抄给用户即可。

## 边界
本 server 只生成；修底座 / 契约 / 漂移属治理链（桥 CI / 维护面），不在此声称能做。
"""


def guide() -> str:
    return _GUIDE
