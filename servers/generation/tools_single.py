"""生成面 server · 单端链三工具实现（DESIGN §6.1-6.3）。

零注册：git 地址即身份——clone → 读底座 params.json（两区）→ spec 校验 →
指 template/ → copier copy。不在册地址照常可生成（templates.yaml 只是菜单）。
"""

from pathlib import Path

import yaml

from bridge_mcp import protocol, selection
from bridge_mcp.git import ensure_clone

_DATA = Path(__file__).parent / "data" / "templates.yaml"


def _registry() -> dict:
    return yaml.safe_load(_DATA.read_text(encoding="utf-8")).get("templates", {})


# ── list_templates（DESIGN §6.3：单端菜单，L1 候选集）──────────────


def list_templates(
    kind: str | None = None, stack: str | None = None, form: str | None = None
) -> list[dict]:
    """单端候选注册表行（离线，读 templates.yaml 纯规则过滤）。"""
    rows = []
    for name, meta in _registry().items():
        if kind and meta.get("kind") != kind:
            continue
        if stack and stack not in (meta.get("stack") or []):
            continue
        if form and form not in (meta.get("forms") or []):
            continue
        rows.append({"name": name, **meta})
    return rows


# ── get_template_params（DESIGN §6.2：单端参数内省 = 落参与选择地基）──


def get_template_params(git_url: str, version: str | None = None) -> dict:
    """clone 底座 → 读 params.json 两区 → 原生/派生/selection 分列。"""
    repo = ensure_clone(git_url, version)
    doc = protocol.load_params_json(repo)
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


def _template_dir(repo: Path) -> Path:
    """底座模板体：template/ 优先（copier.yml 在子目录），否则仓库根。"""
    tpl = repo / "template"
    if (tpl / "copier.yml").exists() or (tpl / "copier.yaml").exists():
        return tpl
    return repo


def generate_single(
    git_url: str,
    params: dict,
    target_dir: str,
    version: str | None = None,
    skip_tasks: bool = False,
) -> dict:
    """clone → 读协议 → spec 校验 → 指 template/ → copier copy → 结构化返回。"""
    repo = ensure_clone(git_url, version)
    doc = protocol.load_params_json(repo)
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
    }
