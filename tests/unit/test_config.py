"""bridge_mcp.config：桥 cli 入口纯 env 注入解析（无默认路径）。"""

import os
import sys

import pytest

from bridge_mcp import config


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """每个用例前清掉桥入口 env，避免互相污染。"""
    for k in ("BRIDGE_EXE", "BRIDGE", "BRIDGE_CLI"):
        monkeypatch.delenv(k, raising=False)


def test_no_env_raises_with_guidance():
    with pytest.raises(RuntimeError) as ei:
        config.bridge_cmd()
    assert "BRIDGE_EXE" in str(ei.value)
    assert "BRIDGE_CLI" in str(ei.value)


def test_bridge_exe_wins_and_returns(monkeypatch, tmp_path):
    exe = tmp_path / "bridge"
    exe.write_text("#!/bin/sh\n", encoding="utf-8")
    exe.chmod(0o755)
    cli = tmp_path / "cli.py"
    cli.write_text("", encoding="utf-8")
    monkeypatch.setenv("BRIDGE_EXE", str(exe))
    monkeypatch.setenv("BRIDGE_CLI", str(cli))
    assert config.bridge_cmd() == [str(exe)]


def test_bridge_exe_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_EXE", str(tmp_path / "nope"))
    with pytest.raises(RuntimeError) as ei:
        config.bridge_cmd()
    assert "不存在" in str(ei.value)


def test_bridge_name_on_path(monkeypatch, tmp_path):
    exe = tmp_path / "bridge"
    exe.write_text("#!/bin/sh\n", encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BRIDGE", "bridge")
    assert config.bridge_cmd() == [str(exe)]


def test_bridge_name_not_found_raises(monkeypatch):
    monkeypatch.setenv("BRIDGE", "definitely-not-a-command-xyz")
    with pytest.raises(RuntimeError):
        config.bridge_cmd()


def test_bridge_cli_dev(monkeypatch, tmp_path):
    cli = tmp_path / "cli.py"
    cli.write_text("", encoding="utf-8")
    monkeypatch.setenv("BRIDGE_CLI", str(cli))
    assert config.bridge_cmd() == [sys.executable, str(cli)]


def test_cache_root_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_MCP_CACHE", str(tmp_path))
    assert config.cache_root() == tmp_path
    assert config.bases_cache_root() == tmp_path / "bases"
