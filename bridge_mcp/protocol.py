"""底座协议读（params.json 两区）与 spec 校验（单端链 / 内省共用）。

协议见 fullstack-param-protocol SCHEMA.md：params（派生+hash）/ selection（策展+schema）。
单端链零注册：clone 底座 → 读根 params.json（无协议地址回退 copier.yml 由调用方处理）。
"""

import json
from pathlib import Path

# selection 字段集（单一真源在协议 SCHEMA.md；与桥 bridge/combos.py 同步演进，S3）
SELECTION_FIELDS = ("suited_for", "tradeoffs")

# copier.yml 里 jinja 表达式默认值/条件值的定界符（前端 _envops 用 [[]]，后端用 {{}}）
_JINJA_MARKERS = ("{{", "}}", "{%", "%}", "[[", "]]", "[%", "%]")


def load_params_json(repo: Path) -> dict:
    p = repo / "params.json"
    if not p.exists():
        raise FileNotFoundError(f"底座无 params.json（{p}）")
    return json.loads(p.read_text(encoding="utf-8"))


# ── A1：无协议底座回退 copier.yml 内省（⑥其它 / 通用 copier 模板，DESIGN §5.1）──


def _is_expression(value) -> bool:
    return isinstance(value, str) and any(m in value for m in _JINJA_MARKERS)


def _normalize_choices(raw) -> list[dict] | None:
    """choices → [{value}] / [{value, disabled, reason}]（镜像协议 gen-params）。"""
    if raw is None:
        return None
    out: list[dict] = []
    if isinstance(raw, list):
        out = [{"value": v} for v in raw]
    elif isinstance(raw, dict):
        for _label, v in raw.items():
            if isinstance(v, dict):
                entry = {"value": v.get("value")}
                if v.get("validator"):
                    entry["disabled"] = True
                    entry["reason"] = v["validator"]
                out.append(entry)
            else:
                out.append({"value": v})
    return out or None


def introspect_copier(template_dir: Path) -> dict:
    """无 params.json 时，用 copier 内省 template/copier.yml 拿原生参数（无 selection 区）。

    与协议 gen-params 同源逻辑（copier._template.Template.questions_data）；derived 只取
    when 字面 False；jinja 表达式默认省略（视为必填）。copier 9.17.1 与本仓依赖一致。
    """
    import copier._template  # noqa: F401  内部 API（同协议 gen-params，钉版本）
    from copier._template import Template

    questions = Template(url=str(template_dir)).questions_data
    params: dict[str, dict] = {}
    for name, spec in questions.items():
        entry: dict = {"type": spec.get("type", "str")}
        choices = _normalize_choices(spec.get("choices"))
        if choices:
            entry["choices"] = choices
        default = spec.get("default")
        if "default" in spec and default is not None and not _is_expression(default):
            entry["default"] = default
        entry["derived"] = spec.get("when") is False
        params[name] = entry
    return {"schema_version": None, "params": params, "selection": None}  # 非协议底座


def split_params(doc: dict) -> tuple[dict, dict]:
    """按 derived 分原生（要问的）与派生（自动算的只读）。"""
    allp = doc.get("params", {})
    native = {n: s for n, s in allp.items() if not s.get("derived")}
    derived = {n: s for n, s in allp.items() if s.get("derived")}
    return native, derived


def _has_default(spec: dict) -> bool:
    """是否可省略：spec 带字面 default 且非 None（与 describe_params 的 required 同源）。"""
    return "default" in spec and spec.get("default") is not None


def validate_spec(params: dict, native: dict) -> list[str]:
    """严格 spec 校验：键 ⊆ 原生参数、派生禁止、值类型/choices 合法、必填齐全。

    返回错误列表（空 = 合法）。参数显式传 None 视为缺省（计入必填检查）。
    """
    provided = params or {}
    errors: list[str] = []

    # 1) 键与值：非原生/派生禁止；类型与启用 choices 只对已提供值校验
    for name, value in provided.items():
        if value is None:
            continue  # None = 未提供，交给必填检查
        if name not in native:
            errors.append(f"参数 {name} 非原生/未知（派生参数禁止传入）")
            continue
        spec = native[name]
        ptype = spec.get("type", "str")
        if ptype == "bool" and not isinstance(value, bool):
            errors.append(f"{name} 应为布尔")
        elif ptype == "int" and not isinstance(value, int):
            errors.append(f"{name} 应为整数")
        elif ptype == "str" and not isinstance(value, str):
            errors.append(f"{name} 应为字符串")
        choices = [c["value"] for c in spec.get("choices", []) if not c.get("disabled")]
        if choices and value not in choices:
            errors.append(f"{name} 取值不在启用 choices 内: {choices}")

    # 2) 必填：无字面 default 的原生参数必须提供（None 视为未提供）
    for name, spec in native.items():
        if name in provided and provided.get(name) is not None:
            continue
        if not _has_default(spec):
            errors.append(f"缺少必填原生参数 {name}")
    return errors


def describe_params(params: dict) -> list[dict]:
    """原生参数描述（落参前基线）：name/type/required/has_default/default/choices。"""
    out = []
    for name, spec in params.items():
        has_default = "default" in spec and spec.get("default") is not None
        choices = [c["value"] for c in spec.get("choices", []) if not c.get("disabled")]
        out.append(
            {
                "name": name,
                "type": spec.get("type", "str"),
                "required": not has_default,
                "has_default": has_default,
                "default": spec.get("default") if has_default else None,
                "choices": choices or None,
            }
        )
    return out


def extract_selection(doc: dict) -> dict | None:
    """selection 区（可选）；缺省 → None。未知字段容忍但原样带上（供上层决定）。"""
    sel = doc.get("selection")
    return sel if isinstance(sel, dict) and sel else None
