# servers/governance — 治理面 MCP server（占位，未实现）

未来车道（series-overview 后期待办，2026-09-05 定调）：check 链（漂移/对齐）若需跨壳稳定暴露，
作为**本仓内另一个 server**（独立入口）实现——不与生成面杂糅（DESIGN §3.1）。

- 数据面：桥 `cli.py check`（--base-repo/--base-version / --combo / --all）+ 底座 diff + drift issue 流
- 生成面 server 的六个工具 / 资源 / 玩法**不受影响**，本占位不建任何代码
- 前置：桥 `check` 出 `--json` 机器输出（现为人类文本），见 DESIGN §5.4 内省面演进
