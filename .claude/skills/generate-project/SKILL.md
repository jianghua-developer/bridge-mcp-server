---
name: generate-project
description: 生成 AI 项目（单端/多端一体）：收到「生成/搭 X 项目」时，按双路径玩法调用 bridge-gen（bridge-mcp-server）的 MCP 工具产出项目目录，不要凭空编造底座/组合/参数。
---

# 生成项目玩法（bridge-mcp-server · bridge-gen）

用户要「生成一个 **X** 项目/系统」时走本流程。**全程调用 MCP server `bridge-gen` 的工具**（工具名见 `claude mcp list`，通常前缀 `mcp__bridge-gen__…`）；菜单、参数、selection 一律以工具/资源返回为准，禁止脑补。

## 1. 判定形态
- 前后端分离、要契约自动对齐 → **多端**：`list_combos`。
- 纯底座单端（纯前端/纯后端/CLI/单仓全栈）→ **单端**：用户给了 git 地址直走；未给 → `list_templates` 引导。

## 2. L1/L2/L3（别跳 L3）
1. L1：用户显式栈/形态约束 → `list_templates` / `list_combos` 过滤。
2. L2：只在候选内推荐，依据各候选 selection（单端对短名单 `get_template_params` 读；多端 `list_combos` 已含合并 selection）。输出 `{候选, 理由, 备选}`。
3. L3：**带理由+备选请用户确认/改选** → 确认后才落参。

## 3. 落参与生成
- 参数基线：单端 `get_template_params(git_url)`（native 要问 / derived 自动算 / selection）；多端 `get_combo_params(combo)`（params 可问 / internal 勿传 / derived 只读）。
- 只传结构化 spec：地址或组合名 + **原生参数** + target_dir。**派生参数禁止传入**。
- `generate_single(git_url, params, target_dir)` 或 `generate_multi(combo, params, target_dir)`。
- 缺参数/形态歧义/target_dir 未定 → 反问，不瞎猜。

## 4. 收尾
- 返回结构 + 契约/README 位置（多端）；结构 + README（单端）。
- 要修底座/契约/漂移的活不在这（治理链走桥 CI/维护面）——不要声称本 server 能做。

## 提示
- 若怀疑工具没触发：先跑 `claude mcp list` 确认 `bridge-gen` connected；单端 `generate_single` 无需桥可执行，多端需要 `BRIDGE_EXE`（已配在 ~/.zshrc）。
