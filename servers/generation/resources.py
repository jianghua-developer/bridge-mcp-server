"""生成面 server · Resources（只读真源视图）：templates:// 与 combos://。

内容引用注册表/桥内省，不抄 selection 进第二份（选择事实单一真源在底座）。
"""

from bridge_mcp.bridge_cli import BridgeCli
from servers.generation.tools_single import list_templates


def templates_catalog() -> str:
    """单端候选注册表文本视图（自持 templates.yaml）。"""
    rows = list_templates()
    lines = ["# 单端可生成底座（薄菜单，非门槛；不在册地址照常 generate_single）"]
    for r in rows:
        lines.append(
            f"- {r['name']}  [{r['kind']}] stack={','.join(r['stack'])} forms={','.join(r['forms'])}"
        )
    return "\n".join(lines)


def combos_catalog() -> str:
    """多端注册表文本视图（桥 list-combos --json 物化，只读）。"""
    rows = BridgeCli().list_combos()
    lines = ["# 多端组合（纯 cli 消费桥；selection = 底座并集 + combo 段）"]
    for r in rows:
        units = ", ".join(f"{u['key']}({u['source']})" for u in r.get("units", []))
        lines.append(f"- {r['combo']}: {units}")
        for s in (r.get("selection") or {}).get("suited_for", []):
            lines.append(f"    suited_for: {s}")
    return "\n".join(lines)
