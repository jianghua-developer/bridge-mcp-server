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
    react = tools_single.list_templates(stack="react")
    assert [r["name"] for r in react] == ["vite-react-spa-template"]
    script = tools_single.list_templates(
        stack="script"
    )  # 子串匹配：typescript 命中两前端
    assert {r["name"] for r in script} == {
        "vite-react-spa-template",
        "vite-vue-spa-template",
    }
    ts = tools_single.list_templates(stack="ts")  # 同义词 token：ts = typescript
    assert {r["name"] for r in ts} == {
        "vite-react-spa-template",
        "vite-vue-spa-template",
    }
    py = tools_single.list_templates(stack="py")
    assert [r["name"] for r in py] == ["python-fastapi-template"]


def test_list_templates_form_alias_match():
    """form 按别名子串匹配：口语『纯前端/单页应用』命中前端 SPA。"""
    for alias in ("spa", "纯前端", "单页应用"):
        got = tools_single.list_templates(form=alias)
        assert {r["name"] for r in got} == {
            "vite-react-spa-template",
            "vite-vue-spa-template",
        }, alias
    assert tools_single.list_templates(form="cli") == []  # 现役无 cli


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


# ── tools_multi list_combos stack 过滤（纯逻辑 _filter_rows）────


def test_list_combos_stack_filter():
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
    got = tools_multi._filter_rows(rows, stack="vue")
    assert [r["combo"] for r in got] == ["python-vue"]  # 仅 vue 行命中
    assert tools_multi._filter_rows(rows, None) == rows
