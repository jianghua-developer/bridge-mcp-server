"""bridge_mcp — MCP server 共享胶水（无 MCP 面，仅供各 server 复用）。

边界（DESIGN §3.1）：只放 config / 桥 cli shell-out / 协议读 / git clone 等无工具注册的
薄胶水；任何 tool/resource/prompt 注册都归属 servers/<name>/，避免生成/治理两面串扰。
"""
