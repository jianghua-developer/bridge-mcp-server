"""生成面 server · generate_project_guide 玩法 Prompt（DESIGN §7）。

引用六工具与两资源，不把注册表/selection 抄进文案（玩法从真源派生，避免第二真源）。
"""

_GUIDE = """# 项目生成玩法（双路径 · 统一目标：需求 → 项目目录）

你面对一次「AI 生成完整业务系统」需求。工具面 = 六个生成工具 + 两个只读注册表资源；
你负责理解需求 → 判形态 → 落 spec → 调生成工具。**先给用户确认，不得直接生成**。

## 判定形态（先想清楚走哪条链）
- 前后端分离、需要契约自动对齐（N≥2）→ **多端**：读 combos://catalog，用 list_combos。
- 纯底座单端（纯前端/纯后端/CLI/单仓全栈）→ **单端**：用户已给地址直走；
  未给 → 读 templates://catalog + list_templates 引导选底座。

## 选择三阶（L1/L2/L3，别跳 L3）
1. L1 硬过滤：用户显式栈/形态约束 → list_templates/ list_combos 过滤（确定性）。
2. L2 有界推荐：只在 L1 候选内语义匹配；地基 = 各候选 selection（单端 get_template_params
   短名单读底座；多端 list_combos 已含合并 selection）。输出 { 候选, 理由, 备选 }。
3. L3 确认闸门：带理由 + 备选给用户确认或改选 → 才进落参。

## 落参与生成
- 参数基线：单端 get_template_params(git_url) → native（要问的）/ derived（自动算的只读）/ selection；
  多端 get_combo_params(combo) → params（可问）/ internal（勿传）/ derived（只读）。
- spec 边界：只传**结构化 spec**（地址或组合名 + 原生参数 + target_dir），不收自然语言；
  **派生参数禁止传入**（derived 列出的都是自动算的）。
- 生成：generate_single(git_url, params, target_dir) 或 generate_multi(combo, params, target_dir)。
- 不知道的必问：缺参数 / 形态歧义 / target_dir 未定，不瞎猜。

## 纪律
- 生成前必须 L3 确认；selection/菜单事实以工具/资源返回为准，不脑补。
- 生成后返回里给结构 + 契约/README 位置（多端）/ 结构 + README（单端）。
- 需要修底座/契约/漂移的活不在这：本 server 只生成；治理链走桥 CI 与维护面。
"""


def guide() -> str:
    return _GUIDE
