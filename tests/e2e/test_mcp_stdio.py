"""M3 gate e2e：以真实 MCP client（stdio）连起生成面 server，验证六工具/资源/玩法可调用。

前置：BRIDGE_EXE 指向打包好的 bridge 可执行（多端工具依赖）；未设则整模块跳过。
运行：BRIDGE_EXE=/home/jeff/.local/bin/bridge uv run pytest tests/e2e -q
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    not os.environ.get("BRIDGE_EXE"),
    reason="需 BRIDGE_EXE 指向打包好的 bridge 可执行（见 CLAUDE.md 开发前置）",
)

_SIX_TOOLS = {
    "list_templates",
    "get_template_params",
    "generate_single",
    "list_combos",
    "get_combo_params",
    "generate_multi",
}


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "servers.generation.server"],
        env={**os.environ},
        cwd=str(REPO),
    )


def test_handshake_six_tools_and_call():
    """initialize → tools/list（六工具）→ list_templates / list_combos 可调用。"""

    async def _run():
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                tools = await s.list_tools()
                names = {t.name for t in tools.tools}
                assert _SIX_TOOLS <= names, f"缺工具: {_SIX_TOOLS - names}"

                r = await s.call_tool("list_templates", {})
                text = "".join(c.text for c in r.content if hasattr(c, "text"))
                assert "vite-react-spa-template" in text

                r2 = await s.call_tool("list_combos", {})
                text2 = "".join(c.text for c in r2.content if hasattr(c, "text"))
                assert "python-react" in text2

    asyncio.run(_run())


def test_resources_and_guide_prompt():
    """resources/read（templates:// combos://）+ generate_project_guide 可取。"""

    async def _run():
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()

                res = await s.read_resource("templates://catalog")
                t1 = "".join(c.text for c in res.contents if hasattr(c, "text"))
                assert "python-fastapi-template" in t1

                res2 = await s.read_resource("combos://catalog")
                t2 = "".join(c.text for c in res2.contents if hasattr(c, "text"))
                assert "python-react" in t2

                prompts = await s.list_prompts()
                assert "generate_project_guide" in {p.name for p in prompts.prompts}
                got = await s.get_prompt("generate_project_guide", {})
                assert "L1" in got.messages[0].content.text

    asyncio.run(_run())
