# 纯单端底座入册 SOP（新增底座 = 协议自述 + templates.yaml 一行）

适用：**永不进 fullstack-bridge combos** 的单模板底座——DESIGN 形态 ⑤纯命令行 / ②Nuxt+BFF 单仓全栈 / ⑥其它单模板；以及 ③纯后端/④纯前端这类「也可单端生成」的共享底座（共享底座通常已在册，仅需保证列表条目在）。入册 = **底座自述（协议）+ 本仓 templates.yaml 一行薄指针**，无桥、无 combos、无 GitHub drift 配置。

> 对照：多端底座（进 combos）的接入见 fullstack-bridge `docs/base-onboarding.md`——差别只在「要不要在桥 combos.yaml 登记 + 激活 notify-drift」。

## 步骤

### 1. 底座侧：协议自述（三件套，源在 fullstack-param-protocol）

单端链零注册读取依赖底座根 `params.json`（两区：params + selection）。底座必须是 git 仓、模板体在 `template/`。

```bash
BASE=~/project/<新底座>
PROTO=~/project/fullstack-param-protocol
mkdir -p "$BASE/bin" "$BASE/.githooks" "$BASE/.github/workflows"
cp "$PROTO/gen-params.py" "$BASE/bin/gen-params.py"
sha256sum "$PROTO/gen-params.py" | awk '{print $1}' > "$BASE/bin/GEN_PARAMS_VERSION"
cp "$PROTO/hooks/pre-commit" "$BASE/.githooks/pre-commit"      # chmod +x + git config core.hooksPath .githooks
cp "$PROTO/workflows/params-check.yml" "$BASE/.github/workflows/params-check.yml"
uv run --with 'copier==9.17.1' python "$BASE/bin/gen-params.py" \
  --template-dir "$BASE/template" --output "$BASE/params.json"
# 可选：手补 params.json selection 区（suited_for/tradeoffs，供单端 L2 引导）→ regen 归一
git -C "$BASE" add -A && git -C "$BASE" commit -m "feat: params.json 协议接入" && git -C "$BASE" push
```

- 生成机制/自检详见 [fullstack-param-protocol SCHEMA.md](../../../fullstack-param-protocol/SCHEMA.md)。
- **无需** GitHub `DRIFT_DISPATCH_ENABLED` / `BRIDGE_DISPATCH_TOKEN`（不入 combos → 不 dispatch 桥）。

### 2. 本仓：templates.yaml 加一行（薄指针，不抄 selection）

编辑 [servers/generation/data/templates.yaml](servers/generation/data/templates.yaml)：

```yaml
templates:
  <底座名>:                       # 与底座 git 仓同名惯例；共享底座用与 combos.yaml bases 同裸名
    git: <git@github 地址或 https>
    kind: frontend | backend | cli   # 受控：单端用 kind 大类（cli/nuxt 等单端专属另给，见下）
    stack: [<技术 token 列表>]        # L1 过滤 token（如 python, click / nuxt, vue）
    forms: ["<受控语义 token：spa | api | fullstack | cli，见 templates.yaml 头注>"]
```

- **kind 取值**：现役 `frontend` / `backend`；纯单端专属（cli/nuxt 等）若需 L1 可加 `cli` / `fullstack`——**加前先与本仓 design/玩法对齐**，别发明新词不同步（guide 受控枚举同源）。
- **不抄 selection**：深选择事实单一真源在底座 params.json `selection` 区；templates.yaml 只放身份/标签（DESIGN §5.3）。

### 3. 验证（本仓）

```bash
uv run python -c "
from servers.generation import tools_single as t
print(t.list_templates(kind='cli'))                      # 新底座应出现
print(t.get_template_params('<git 地址或本地仓路径>')['native'][:2])  # 参数基线可读（无协议会回退 copier.yml）
"
uv run pytest tests/unit -q                                # 回归
```

- `get_template_params` / `generate_single` 对**不在册 git 地址也照常可用**（零注册）——templates.yaml 只是菜单，不是门槛。

### 4. 收尾

- commit + push 本仓（templates.yaml）；若 base 也新接入协议则先推 base。
- 可选：新底座有「选择价值」（与现有同 kind 底座竞争）→ 底座 selection 区写好，L2 引导自动可用。
- 需要新 kind 大类时：同步 [guide.py](servers/generation/guide.py) 受控取值节（玩法 v2），避免漂移。

## 与多端底座的差异速览

| | 纯单端底座（本 SOP） | 多端底座（bridge base-onboarding） |
|---|---|---|
| 协议三件套 | ✅ 要（自述 params/selection） | ✅ 要 |
| templates.yaml | ✅ 加一行 | 如需单端引导也加 |
| 桥 combos.yaml | ❌ 不进 | ✅ 登记 units + version |
| notify-drift / PAT | ❌ 不需要 | ✅ 需要（dispatch 桥 check-drift） |
| check 对齐 | ❌ 无（漂移靠底座自身协议 CI 自检） | ✅ 桥 check 基线 |
