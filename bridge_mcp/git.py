"""底座 git 克隆/版本解析（单端链，零注册地址即身份）。

缓存按 git 地址 hash 分目录（~/.cache/bridge-mcp-server/bases/<hash16>/），
非注册表——任何地址照常可 clone（DESIGN §4.8：注册表是菜单不是门槛）。
"""

import hashlib
import subprocess
from pathlib import Path

from . import config


def _run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def ensure_clone(url: str, version: str | None = None) -> Path:
    """clone git 地址到缓存 → checkout version（可选）→ 返回仓库根。"""
    root = config.bases_cache_root()
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    dest = root / key
    if not (dest / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"↻ clone {url} → {dest}")
        subprocess.run(
            ["git", "clone", url, str(dest)], check=True, capture_output=True
        )
    if version:
        cur = _run_git(["-C", str(dest), "rev-parse", "HEAD"]).stdout.strip()
        if cur != version:
            r = _run_git(["-C", str(dest), "checkout", version], check=False)
            if r.returncode != 0:  # 本地缺该 ref（缓存旧）→ fetch origin 后重试
                _run_git(["-C", str(dest), "fetch", "origin"])
                _run_git(["-C", str(dest), "checkout", version])
    return dest
