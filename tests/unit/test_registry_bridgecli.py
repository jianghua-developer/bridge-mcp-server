"""离线：templates 注册表过滤 / bridge_cli JSON 解析与多端列表过滤。"""

import sys

import pytest

from bridge_mcp import bridge_cli
from servers.generation import tools_multi, tools_single

# ── list_templates（读注册表，离线）─────────────────────────────


def test_list_templates_rows():
    names = {r["name"] for r in tools_single.list_templates()}
    assert {"vite-react-spa-template", "python-fastapi-template"} <= names


def test_list_templates_filter():
    fe = tools_single.list_templates(kind="frontend")
    assert {r["name"] for r in fe} == {
        "vite-react-spa-template",
        "vite-vue-spa-template",
    }
    vue = tools_single.list_templates(stack="vue3")
    assert [r["name"] for r in vue] == ["vite-vue-spa-template"]


# ── bridge_cli JSON 解析（容忍 warning 前缀）────────────────────


def test_parse_json_skips_warning_prefix():
    text = '⚠️ 缺底座 xxx——跳过其参数\n[{"combo": "python-react"}]\n'
    assert bridge_cli._parse_json(text) == [{"combo": "python-react"}]


def test_parse_json_rejects_no_json():
    with pytest.raises(bridge_cli.BridgeError):
        bridge_cli._parse_json("没有 JSON 的输出")


def test_bridge_cli_with_stub(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import sys, json\n"
        "if sys.argv[1:2] == ['list-combos']:\n"
        "    print(json.dumps([{'combo': 'python-react', 'units': []}]))\n"
        "else:\n"
        "    print('no')\n",
        encoding="utf-8",
    )
    c = bridge_cli.BridgeCli(cmd=[sys.executable, str(stub)])
    assert c.list_combos() == [{"combo": "python-react", "units": []}]


# ── tools_multi.list_combos 过滤（monkeypatch _cli）─────────────


def test_list_combos_stack_filter(monkeypatch):
    rows = [
        {
            "combo": "python-react",
            "units": [
                {"key": "frontend", "stack": "Vite + React + TS"},
                {"key": "backend", "stack": "FastAPI + SQLAlchemy"},
            ],
        },
        {
            "combo": "python-vue",
            "units": [
                {"key": "frontend", "stack": "Vue 3 + Vite + TS"},
                {"key": "backend", "stack": "FastAPI + SQLAlchemy"},
            ],
        },
    ]

    class Fake:
        def list_combos(self):
            return rows

    monkeypatch.setattr(tools_multi, "_cli", Fake())
    got = tools_multi.list_combos(stack="vue")
    assert [r["combo"] for r in got] == ["python-vue"]  # 仅 vue 行命中
