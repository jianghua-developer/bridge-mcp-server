"""生成面 server · 多端链三工具实现（DESIGN §6.4-6.6）：全部 shell-out 桥 cli 生成面。

server 不直读 combos.yaml、不 clone 底座内省；menu/params/生成全经桥 cli --json。
治理链（桥 check）属 CI workflow，本 server 不消费不暴露（DESIGN §6/§10）。
"""

from pathlib import Path

from bridge_mcp.bridge_cli import BridgeCli


def _filter_rows(rows: list[dict], stack: str | None) -> list[dict]:
    """L1 stack 过滤（单元 stack 文本子串；空 = 不过滤）。"""
    if not stack:
        return rows
    token = stack.lower()
    return [
        r
        for r in rows
        if any(token in (u.get("stack") or "").lower() for u in r.get("units", []))
    ]


def list_combos(stack: str | None = None) -> list[dict]:
    """多端菜单行（units/edges + 合并 selection）。stack 可选 L1 过滤（单元 stack 文本）。"""
    return _filter_rows(BridgeCli().list_combos(), stack)


def get_combo_params(combo: str) -> dict:
    """参数基线（params/internal/derived/selection，桥 show-combo 分列）。"""
    return BridgeCli().show_combo(combo)


def generate_multi(
    combo: str, params: dict, target_dir: str, skip_tasks: bool = False
) -> dict:
    """shell-out 桥 `generate <combo> <project>`（选项由桥 schema 数据驱动）。"""
    dest = Path(target_dir)
    BridgeCli().generate(combo, dest, params, skip_tasks=skip_tasks)
    structure = sorted(p.name for p in dest.iterdir()) if dest.exists() else []
    contract = dest / "docs" / "CONTRACT.md"
    readme = dest / "README.md"
    return {
        "status": "ok",
        "combo": combo,
        "target_dir": str(dest),
        "structure": structure,
        "contract_path": str(contract) if contract.exists() else None,
        "readme_path": str(readme) if readme.exists() else None,
    }
