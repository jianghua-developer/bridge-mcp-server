"""生成类 e2e：真实 copier（单端，本地底座克隆源）/ 真实桥 generate（多端，BRIDGE_EXE）。

- 单端 generate_single：git_url 用本机 python-fastapi-template 本地仓（离线 clone 源）；
- 多端 generate_multi：shell-out 打包好的 bridge（需 BRIDGE_EXE，见 CLAUDE.md 前置）；
- spec 严格校验：必填缺失 / 派生传入 / choices 非法 / target_dir 非空 → ValueError。
"""

import os
from pathlib import Path

import pytest

from servers.generation import tools_single

_LOCAL_FASTAPI = Path("/home/jeff/project/python-fastapi-template")

needs_local_base = pytest.mark.skipif(
    not _LOCAL_FASTAPI.exists(),
    reason="需本机 python-fastapi-template 本地仓（离线单端源）",
)
needs_bridge = pytest.mark.skipif(
    not os.environ.get("BRIDGE_EXE"), reason="需 BRIDGE_EXE（多端 shell-out 桥）"
)


@needs_local_base
def test_generate_single_fastapi_local(tmp_path):
    out = tools_single.generate_single(
        str(_LOCAL_FASTAPI),
        {"project_name": "e2e", "project_description": "P3 e2e"},
        str(tmp_path / "app"),
        skip_tasks=True,
    )
    assert out["status"] == "ok"
    assert "app" in out["structure"]
    assert "main.py" in out["structure"]
    assert out["readme_path"] and Path(out["readme_path"]).exists()


@needs_local_base
def test_generate_single_spec_rejects(tmp_path):
    # 派生参数传入 → 拒绝
    with pytest.raises(ValueError) as ei:
        tools_single.generate_single(
            str(_LOCAL_FASTAPI),
            {"project_name": "e2e", "child_apps": ["x"]},
            str(tmp_path / "a"),
            skip_tasks=True,
        )
    assert "child_apps" in str(ei.value)
    # 必填缺失（project_description 有默认、project_name 必填但这里给了——缺别的？给非法 choices）
    with pytest.raises(ValueError) as ei2:
        tools_single.generate_single(
            str(_LOCAL_FASTAPI),
            {"project_name": "e2e", "python_version": "9.99"},
            str(tmp_path / "b"),
            skip_tasks=True,
        )
    assert "choices" in str(ei2.value)
    # target_dir 非空 → 拒绝覆盖
    existing = tmp_path / "occupied"
    existing.mkdir()
    (existing / "x").write_text("", encoding="utf-8")
    with pytest.raises(ValueError) as ei3:
        tools_single.generate_single(
            str(_LOCAL_FASTAPI),
            {"project_name": "e2e"},
            str(existing),
            skip_tasks=True,
        )
    assert "非空" in str(ei3.value) or "拒绝覆盖" in str(ei3.value)


@needs_bridge
def test_generate_multi_python_react(tmp_path):
    from servers.generation import tools_multi

    dest = tmp_path / "proj"
    out = tools_multi.generate_multi(
        "python-react", {"project_description": "P3 e2e"}, str(dest), skip_tasks=True
    )
    assert out["status"] == "ok"
    assert {"frontend", "backend", "docs"} <= set(out["structure"])
    assert out["contract_path"] and Path(out["contract_path"]).exists()
