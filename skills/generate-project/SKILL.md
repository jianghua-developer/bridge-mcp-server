---
name: generate-project
description: 生成 AI 项目（单端/多端一体）——命中即调 bridge-gen（bridge-mcp-server）MCP 工具，按仓库 canonical 玩法（generate_project_guide）把需求收敛成 spec 并生成；菜单/参数/selection 以工具返回为准，不编造。
---

# 生成项目（壳侧入口）

**canonical 玩法全文** = MCP prompt `generate_project_guide`（仓库 `servers/generation/guide.py`）。本 skill 只做壳侧挂载：触发 + 工具定位 + 锚点，不重复写玩法（防双源漂移）。

## 触发后照 canonical 流程走
判定形态（多端 vs 单端）→ L1 过滤 → L2 结构化推荐 → **L3 用户确认（不可跳）** → 落参 → 生成 → 汇报 README / CONTRACT。

## 工具定位（server：bridge-gen，前缀见 `claude mcp list`）
- 菜单/地基：`list_templates`（单端）、`list_combos`（多端，含合并 selection）
- 落参内省：`get_template_params` / `get_combo_params`（internal、derived 勿传；多端 `shared:true` = 单值广播全链）
- 生成：`generate_single` / `generate_multi`（只传原生参数；target_dir 须为空/不存在）
- 资源：`templates://catalog`、`combos://catalog`

## 关键纪律（与 canonical 一致）
1. 受控取值用工具/资源返回，不发明新词。
2. 推荐必须给用户确认（带理由 + 备选 + 待确认参数）才生成。
3. 只生成；修底座/契约/漂移不在本 server。

## 排错
- 没触发工具：`claude mcp list` 确认 `bridge-gen` connected；或点名『用 bridge-gen 的工具』。
- 生成报错（choices/必填/target 非空）：读错误改 spec 或换 target 重调。
