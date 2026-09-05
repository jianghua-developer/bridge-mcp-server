"""bridge_mcp.config：桥 cli 可执行入口纯 env 注入解析（只认可执行，不暴露源码）。"""

import os

import pytest

from bridge_mcp import config


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """每个用例前清掉桥入口 env，避免互相污染。"""
    for k in ("BRIDGE_EXE", "BRIDGE", "BRIDGE_CLI"):
        monkeypatch.delenv(k, raising=False)


def _executable(tmp_path, name="bridge") -> str:
    exe = tmp_path / name
    exe.write_text("#!/bin/sh\n", encoding="utf-8")
    exe.chmod(0o755)
    return str(exe)


def test_no_env_raises_with_guidance():
    with pytest.raises(RuntimeError) as ei:
        config.bridge_cmd()
    msg = str(ei.value)
    assert "BRIDGE_EXE" in msg
    assert "BRIDGE" in msg
    assert "BRIDGE_CLI" not in msg  # 源码路径不再作配置面


def test_bridge_exe_wins(monkeypatch, tmp_path):
    exe = _executable(tmp_path)
    monkeypatch.setenv("BRIDGE_EXE", exe)
    monkeypatch.setenv("BRIDGE", "bridge")
    assert config.bridge_cmd() == [exe]


def test_bridge_exe_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_EXE", str(tmp_path / "nope"))
    with pytest.raises(RuntimeError) as ei:
        config.bridge_cmd()
    assert "不存在" in str(ei.value)


def test_bridge_name_on_path(monkeypatch, tmp_path):
    exe = _executable(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BRIDGE", "bridge")
    assert config.bridge_cmd() == [exe]


def test_bridge_name_not_found_raises(monkeypatch):
    monkeypatch.setenv("BRIDGE", "definitely-not-a-command-xyz")
    with pytest.raises(RuntimeError):
        config.bridge_cmd()


def test_bridge_cli_env_ignored(monkeypatch, tmp_path):
    """BRIDGE_CLI 不再被识别（源码不暴露）——仅设它仍视为未配置。"""
    cli = tmp_path / "cli.py"
    cli.write_text("", encoding="utf-8")
    monkeypatch.setenv("BRIDGE_CLI", str(cli))
    with pytest.raises(RuntimeError):
        config.bridge_cmd()


def test_cache_root_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_MCP_CACHE", str(tmp_path))
    assert config.cache_root() == tmp_path
    assert config.bases_cache_root() == tmp_path / "bases"
