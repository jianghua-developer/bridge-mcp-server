"""桥 cli shell-out client（多端腿，DESIGN §5.2：server 只消费桥 cli 生成面）。

- list-combos / show-combo --json → 解析 stdout 的 JSON（容忍前缀 warning 行）；
- generate → 位置参数 + `--kebab-name value` 选项；无 --json（人类输出，结构化由调用方走目录）。
"""

import json
import subprocess
from pathlib import Path

from . import config


class BridgeError(RuntimeError):
    """桥 cli 调用失败（非零退出 / 输出不可解析）。"""


def _parse_json(text: str):
    """从 stdout 稳健解析 JSON：跳过 warning/日志前缀行（找首个 '{' 或 '['）。"""
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                return json.JSONDecoder().raw_decode(text[i:])[0]
            except json.JSONDecodeError as exc:
                raise BridgeError(f"桥输出 JSON 解析失败: {exc}\n{text[:500]}") from exc
    raise BridgeError(f"桥输出无 JSON: {text[:300]}")


class BridgeCli:
    def __init__(self, cmd: list[str] | None = None):
        self._cmd = cmd or config.bridge_cmd()

    def _run(self, args: list[str]) -> str:
        r = subprocess.run(
            [*self._cmd, *args], capture_output=True, text=True, check=False
        )
        if r.returncode != 0:
            raise BridgeError(
                f"桥 cli 失败（{args[:1]}）: {r.stderr.strip() or r.stdout.strip()[:400]}"
            )
        return r.stdout

    def list_combos(self) -> list[dict]:
        return _parse_json(self._run(["list-combos", "--json"]))

    def show_combo(self, combo: str) -> dict:
        return _parse_json(self._run(["show-combo", combo, "--json"]))

    def generate(
        self, combo: str, project: Path, params: dict, skip_tasks: bool = False
    ) -> str:
        args = ["generate", combo, str(project)]
        for name, value in params.items():
            args += [f"--{name.replace('_', '-')}", _to_cli(value)]
        if skip_tasks:
            args.append("--skip-tasks")
        return self._run(args)


def _to_cli(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)
