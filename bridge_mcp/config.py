"""server 配置：桥 cli 调用前缀、克隆缓存根、单端候选注册表路径。

解析优先级（env 覆盖 dev 默认）：
- 多端腿消费的桥 cli：`BRIDGE_EXE`（dist/bridge 可执行）> `BRIDGE_CLI`（cli.py 路径）
  > 默认隔壁 `~/project/fullstack-bridge/cli.py`（本机系列布局）
- 单端腿克隆缓存根：`BRIDGE_MCP_CACHE` > `~/.cache/bridge-mcp-server`
"""

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return _REPO_ROOT


def bridge_cmd() -> list[str]:
    """返回调用桥 cli 的命令前缀（list[str]）。"""
    exe = os.environ.get("BRIDGE_EXE")
    if exe and Path(exe).exists():
        return [exe]
    cli = Path(
        os.environ.get("BRIDGE_CLI")
        or (_REPO_ROOT.parent / "fullstack-bridge" / "cli.py")
    )
    if not cli.exists():
        raise SystemExit(
            f"❌ 找不到桥 cli.py（{cli}）。请设 BRIDGE_CLI 指向 fullstack-bridge/cli.py，"
            "或 BRIDGE_EXE 指向 dist/bridge 可执行"
        )
    return [sys.executable, str(cli)]


def cache_root() -> Path:
    root = Path(
        os.environ.get("BRIDGE_MCP_CACHE")
        or Path.home() / ".cache" / "bridge-mcp-server"
    )
    return root


def bases_cache_root() -> Path:
    return cache_root() / "bases"
