"""server 配置：桥 cli 入口、克隆缓存根——**纯 env 注入，代码不内嵌任何默认路径**。

多端腿消费的桥 cli（DESIGN §5.2：进程边界 + 数据契约）解析链——只认**可执行入口**，
不暴露源码（BRIDGE_CLI 已移除）：
  1. `BRIDGE_EXE` → dist/bridge 可执行（首选，自包含 python+copier+click+baked params）
  2. `BRIDGE`     → PATH 上名为 <值> 的命令（如安装的 bridge 控制台入口）
均未设置 → 明确报错（不猜 sibling/默认目录）。

缓存根：`BRIDGE_MCP_CACHE` > `~/.cache/bridge-mcp-server`。
"""

import os
import shutil
from pathlib import Path


def bridge_cmd() -> list[str]:
    """返回调用桥 cli 的命令前缀（list[str]）。env 缺配置 → RuntimeError（带配法提示）。"""
    exe = os.environ.get("BRIDGE_EXE")
    if exe:
        p = Path(exe)
        if p.exists():
            return [str(p)]
        raise RuntimeError(f"BRIDGE_EXE 指向的可执行不存在: {p}")

    name = os.environ.get("BRIDGE")
    if name:
        found = shutil.which(name)
        if found:
            return [found]
        raise RuntimeError(f"BRIDGE 指定的命令不在 PATH: {name}")

    raise RuntimeError(
        "未配置桥 cli 可执行入口。二选一（env 注入，MCP 注册时提供）：\n"
        "  BRIDGE_EXE = <dist/bridge 可执行>   # 首选\n"
        "  BRIDGE     = <PATH 上的 bridge 命令>"
    )


def cache_root() -> Path:
    root = Path(
        os.environ.get("BRIDGE_MCP_CACHE")
        or Path.home() / ".cache" / "bridge-mcp-server"
    )
    return root


def bases_cache_root() -> Path:
    return cache_root() / "bases"
