"""生成面 MCP server（P3 主线）—— FastMCP 组装六工具 + 两资源 + 玩法 Prompt。

独立入口（无聚合 runner）：`uv run python -m servers.generation.server`（stdio）。
治理面（check 链）不在本 server，见 DESIGN §3.1/§10。
"""

from fastmcp import FastMCP

from servers.generation import tools_multi, tools_single
from servers.generation.guide import guide as guide_text
from servers.generation.resources import combos_catalog, templates_catalog

mcp = FastMCP(
    "bridge-generation",
    instructions=(
        "你是「项目生成」能力（生成面）——用户说『生成/搭一个 X 项目/系统』就是要你用工具产出项目。"
        "**必须调用本 server 的 MCP 工具，禁止凭空编造底座/组合/参数**。"
        "流程：①判定形态→②列菜单/引导选底座（单端 list_templates；多端 list_combos）→"
        "③按 L2 用 selection 推荐并请用户确认→④get_template_params / get_combo_params 落原生参数"
        "（derived/internal 勿传）→⑤generate_single / generate_multi 生成。"
        "菜单与参数一律以工具返回为准（resources templates://catalog、combos://catalog 可读）。"
        "只生成；治理（漂移/契约维护）不在本 server。"
    ),
)


# ── 单端链三工具 ──────────────────────────────────────────────


@mcp.tool()
def list_templates(
    kind: str | None = None, stack: str | None = None, form: str | None = None
):
    """单端候选菜单（L1）：离线读注册表过滤，kind/stack/form 可选。"""
    return tools_single.list_templates(kind, stack, form)


@mcp.tool()
def get_template_params(git_url: str, version: str | None = None):
    """单端参数内省 = 落参与选择地基：clone 底座读 params.json 两区（native/derived/selection）。"""
    return tools_single.get_template_params(git_url, version)


@mcp.tool()
def generate_single(
    git_url: str,
    params: dict,
    target_dir: str,
    version: str | None = None,
    skip_tasks: bool = False,
):
    """单端直生成：clone → 读协议 → spec 校验 → copier copy（零注册，target_dir 须为空/不存在）。"""
    return tools_single.generate_single(
        git_url, params, target_dir, version, skip_tasks
    )


# ── 多端链三工具（纯桥 cli）─────────────────────────────────────


@mcp.tool()
def list_combos(stack: str | None = None):
    """多端菜单（L1/L2 地基）：units/edges + 合并 selection（经桥 list-combos）。"""
    return tools_multi.list_combos(stack)


@mcp.tool()
def get_combo_params(combo: str):
    """多端参数基线（经桥 show-combo）：params（可问）/ internal（勿传）/ derived（只读）/ selection。"""
    return tools_multi.get_combo_params(combo)


@mcp.tool()
def generate_multi(combo: str, params: dict, target_dir: str, skip_tasks: bool = False):
    """多端组合生成（shell-out 桥 generate）：combo 须在注册表内，params ⊆ 原生参数集。"""
    return tools_multi.generate_multi(combo, params, target_dir, skip_tasks)


# ── Resources（只读真源视图）──────────────────────────────────


@mcp.resource("templates://catalog")
def templates_resource() -> str:
    """单端候选注册表（自持 templates.yaml，薄菜单）。"""
    return templates_catalog()


@mcp.resource("combos://catalog")
def combos_resource() -> str:
    """多端注册表视图（桥 list-combos 物化，只读）。"""
    return combos_catalog()


# ── Prompt ─────────────────────────────────────────────────────


@mcp.prompt()
def generate_project_guide() -> str:
    """双路径生成玩法：判定形态 → L1/L2/L3 → 落参 → 生成。"""
    return guide_text()


if __name__ == "__main__":
    mcp.run()
