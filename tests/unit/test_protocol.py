"""bridge_mcp.protocol：spec 校验 / 参数描述 / selection 抽取（离线）。"""

from bridge_mcp import protocol


def _native():
    return {
        "auth_mode": {
            "type": "str",
            "choices": [{"value": "none"}, {"value": "opaque"}],
            "default": "opaque",
            "derived": False,
        },
        "with_db": {"type": "bool", "default": True, "derived": False},
        "project_name": {"type": "str", "derived": False},
    }


def test_validate_spec_ok():
    assert (
        protocol.validate_spec(
            {"auth_mode": "opaque", "with_db": True, "project_name": "app"}, _native()
        )
        == []
    )


def test_validate_spec_rejects_derived_and_unknown():
    errs = protocol.validate_spec({"child_apps": [], "nope": 1}, _native())
    assert any("child_apps" in e and "派生" in e for e in errs)
    assert any("nope" in e and "未知" in e for e in errs)


def test_validate_spec_choice_and_type():
    errs = protocol.validate_spec({"auth_mode": "jwt", "with_db": "yes"}, _native())
    assert any("choices" in e for e in errs)
    assert any("布尔" in e for e in errs)


def test_validate_spec_missing_required():
    """必填原生参数（project_name 无 default）缺失 → 报错；提供后通过。"""
    errs = protocol.validate_spec({"auth_mode": "opaque"}, _native())
    assert any("project_name" in e and "必填" in e for e in errs)
    ok = protocol.validate_spec(
        {"auth_mode": "opaque", "project_name": "app"}, _native()
    )
    assert ok == []


def test_describe_params_marks_required():
    desc = {d["name"]: d for d in protocol.describe_params(_native())}
    assert desc["project_name"]["required"] is True
    assert desc["auth_mode"]["required"] is False
    assert desc["auth_mode"]["default"] == "opaque"
    assert desc["auth_mode"]["choices"] == ["none", "opaque"]


def test_split_params_derived_separated():
    doc = {"params": {"a": {"derived": False}, "b": {"derived": True}}}
    native, derived = protocol.split_params(doc)
    assert list(native) == ["a"]
    assert list(derived) == ["b"]


def test_extract_selection():
    doc = {"params": {}, "selection": {"suited_for": ["x"]}}
    assert protocol.extract_selection(doc) == {"suited_for": ["x"]}
    assert protocol.extract_selection({"params": {}}) is None
