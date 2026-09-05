"""selection 字段集单源引用（S3，P2 评审遗留 → P3 落地）。

字段集单一真源在 fullstack-param-protocol SCHEMA.md；桥 bridge/combos.py 与本仓引用同一组。
能力层消费底座 params.json selection 时：已知字段按结构呈现；**未知字段显式告警而非静默丢弃**
（协议演进新增字段时，这里/桥需同步，避免「内省面比底座策展少」）。
"""

from .protocol import SELECTION_FIELDS

KNOWN = SELECTION_FIELDS


def unknown_fields(selection: dict) -> list[str]:
    """返回 selection 中超出已知字段集的键（供消费方告警）。"""
    if not isinstance(selection, dict):
        return []
    return sorted(set(selection) - set(KNOWN))


def render(selection: dict | None) -> dict | None:
    """归一化呈现 selection：只保留已知字段；缺省/空 → None。"""
    if not isinstance(selection, dict):
        return None
    known = {f: selection[f] for f in KNOWN if selection.get(f)}
    return known if known else None
