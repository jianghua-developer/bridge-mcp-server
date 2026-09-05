"""生成面 server · 单端链三工具实现（DESIGN §6.1-6.3）。

零注册：git 地址即身份——clone → 读底座 params.json（两区）/ 回退 copier.yml → spec 校验 →
指 template/ → copier copy。不在册地址照常可生成（templates.yaml 只是菜单）。

L1 词表单一真源在 templates.yaml `_filter_vocab`：匹配展开与词表提示（filter_hint）都由它生成，
勿在别处另写词表（防双源漂移）。
"""

from pathlib import Path

import yaml

from bridge_mcp import protocol, selection
from bridge_mcp.git import ensure_clone

_DATA = Path(__file__).parent / "data" / "templates.yaml"


def _data() -> tuple[dict, dict]:
    """返回 (templates 行源, _filter_vocab 词表)。"""
    raw = yaml.safe_load(_DATA.read_text(encoding="utf-8"))
    return raw.get("templates", {}), raw.get("_filter_vocab", {})


def _vocab() -> dict:
    return _data()[1]


def _expand(tokens: list[str], synonyms: dict) -> list[str]:
    """token 列表展开 = 自身 + 同义词（供子串/别名命中）。"""
    out: list[str] = []
    for t in tokens:
        out.append(t)
        out.extend(synonyms.get(t, []))
    return out


# ── list_templates（DESIGN §6.3：单端菜单，L1 候选集）──────────────


def list_templates(
    kind: str | None = None, stack: str | None = None, form: str | None = None
) -> list[dict]:
    """单端候选注册表行（离线）。kind 精确、stack/form 子串/同义词匹配（词表自 templates.yaml）。"""
    rows_src, vocab = _data()
    form_syn = vocab.get("form_synonyms", {})
    stack_syn = vocab.get("stack_synonyms", {})
    rows = []
    for name, meta in rows_src.items():
        if kind and meta.get("kind") != kind:
            continue
        if stack and not any(
            stack.lower() in x.lower()
            for x in _expand(meta.get("stack") or [], stack_syn)
        ):
            continue
        if form and not any(
            form.lower() in x.lower()
            for x in _expand(meta.get("forms") or [], form_syn)
        ):
            continue
        rows.append({"name": name, **meta})
    return rows


def filter_hint() -> str:
    """L1 受控词表提示文本（由 templates.yaml _filter_vocab 生成，壳/LLM 不必猜过滤值）。"""
    vocab = _vocab()
    kinds = " | ".join(vocab.get("kinds", []))
    form_parts = [
        f"{k}({'/'.join(aliases)})"
        for k, aliases in vocab.get("form_synonyms", {}).items()
    ]
    stack_parts = [
        f"{a}={k}"
        for k, aliases in vocab.get("stack_synonyms", {}).items()
        for a in aliases
    ]
    return (
        "受控 L1 过滤（list_templates 带参，子串/同义词匹配）：\n"
        f"  kind ∈ {kinds}\n"
        f"  form 别名：{'、'.join(form_parts) or '—'}\n"
        f"  stack 同义词：{', '.join(stack_parts) or '—'}\n"
    )


# ── 底座协议读 / 模板体定位 ─────────────────────────────────────


def _template_dir(repo: Path) -> Path:
    """底座模板体：template/ 优先（copier.yml 在子目录），否则仓库根。"""
    tpl = repo / "template"
    if (tpl / "copier.yml").exists() or (tpl / "copier.yaml").exists():
        return tpl
    return repo


def _load_doc(repo: Path) -> dict:
    """读底座协议；无 params.json（⑥其它/通用 copier 模板）→ 回退 copier.yml 内省（A1）。"""
    try:
        return protocol.load_params_json(repo)
    except FileNotFoundError:
        return protocol.introspect_copier(_template_dir(repo))


# ── get_template_params（DESIGN §6.2：单端参数内省 = 落参与选择地基）──


def get_template_params(git_url: str, version: str | None = None) -> dict:
    """clone 底座 → 读 params.json 两区（或回退 copier.yml）→ 原生/派生/selection 分列。"""
    repo = ensure_clone(git_url, version)
    doc = _load_doc(repo)
    native, derived = protocol.split_params(doc)
    sel = protocol.extract_selection(doc)
    # S3：未知 selection 字段显式告警（不静默丢弃）
    unknown = selection.unknown_fields(sel) if sel else []
    result = {
        "git_url": git_url,
        "version": version,
        "native": protocol.describe_params(native),
        "derived": sorted(derived),
        "selection": selection.render(sel),
    }
    if unknown:
        result["selection_warning"] = f"底座 selection 含未知字段: {unknown}"
    return result


# ── generate_single（DESIGN §6.1）─────────────────────────────────


def generate_single(
    git_url: str,
    params: dict,
    target_dir: str,
    version: str | None = None,
    skip_tasks: bool = False,
) -> dict:
    """clone → 读协议（或回退 copier.yml）→ spec 校验 → 指 template/ → copier copy。"""
    repo = ensure_clone(git_url, version)
    doc = _load_doc(repo)
    native, _ = protocol.split_params(doc)
    errors = protocol.validate_spec(params, native)
    if errors:
        raise ValueError("spec 非法:\n" + "\n".join(errors))

    dest = Path(target_dir)
    if dest.exists() and any(dest.iterdir()):
        raise ValueError(f"target_dir 非空或已存在内容，拒绝覆盖: {dest}")

    import copier  # 延迟导入：运行时依赖

    copier.run_copy(
        src_path=str(_template_dir(repo)),
        dst_path=dest,
        data=params,
        defaults=True,
        quiet=False,
        unsafe=True,
        skip_tasks=skip_tasks,
    )
    structure = sorted(p.name for p in dest.iterdir()) if dest.exists() else []
    readme = dest / "README.md"
    return {
        "status": "ok",
        "target_dir": str(dest),
        "structure": structure,
        "readme_path": str(readme) if readme.exists() else None,
        "next_steps": (
            f"项目已生成于 {dest}：先读 README.md 与 docs/ 起步；"
            "依赖安装/派生参数由底座 _tasks 与 copier 处理。"
        ),
    }
