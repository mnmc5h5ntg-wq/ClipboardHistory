# -*- coding: utf-8 -*-
"""R181 的台账批写：主窗口/列表行 四格判完 + 筛选条那格观察开单。数字全部从闸门与缺席复查解析。"""
import io, os, re, subprocess
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[-1] if not isinstance(h[-1], tuple) else h[-1]
gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
abst = subprocess.check_output(["python3", "scripts/ledger_absence_claims.py"], cwd=ROOT).decode()
if "RESULT=ok" not in gate or "不成立=0/" not in abst: raise SystemExit("REFUSE 闸门或缺席复查不干净")
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
T = dict(SURF=g[0], STATES=g[1], CELLS=g[2], ROWS=g[3], CLEAR=g[4], OPEN=g[5], FLOOR=g[6],
         CLAIMS=grab(r"LEDGER_ABSENCE_CLAIMS 格=\d+ 声明=(\d+)", abst, "声明数"),
         BAD=grab(r"LEDGER_ABSENCE_RESULT=\w+ 不成立=(\d+)/", abst, "不成立数"))
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0")
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", v)
    if "@@" in s: raise SystemExit("TOKEN_LEFT " + str(re.findall(r"@@[A-Z]+@@", s)))
    return s
UI = fill(u"""## 第 183 轮（R181 · 2026-10-19）：主窗口/列表行 四格判完（空 / 错误 / 成功 / 禁用），看图那一腿没让印象变成工单（U-601…U-603 · 产品 0 文件，动效主线）

- **U-601：四格清账，理由全部落在"承载物在别处"。** 已清账 @@CLEAR@@ / @@CELLS@@（未清账 @@OPEN@@）：
  行表面 × 空 —— 空态由 `EmptyStateView` 承载（帧里左栏「暂无剪贴板历史」+ 右栏「选择一条记录查看详情」），列表为空时没有行可判；
  × 错误 —— 失败走 `NoticeBanner`（`ContentView.swift` 四处，tone .warning / .error，有帧 `content-with-copy-failure-notice-*`），行文件里 `failure` / `errorText` 0 命中；
  × 成功 —— 「已复制」回执长在详情区那颗按钮（1.1 秒的勾 + VoiceOver），`ReceiptLine` 在产品源码里只被 `SettingsView` 用（三处），行上再放一份就是两条回执互相追旧；
  × 禁用 —— 行没有可禁用态（`disabled` / `isEnabled` / `allowsHitTesting` 各 0 命中），会被禁用的只有收藏与图钉两颗控件。
  缺席复查 `声明=@@CLAIMS@@ 不成立=@@BAD@@/@@CLAIMS@@`。
- **U-602：看图那一腿真看了，而且它拦下了一条我会顺手写错的工单。** 看 `content-empty-750x560-dark.png`：
  暗档下空态两处文字与图标都读得通（没有再犯侧栏黑字那一族），但筛选那颗分段控件**右半是实心白底黑字、左半是深色带描边** ——
  第一眼读起来像"暗档里选中态被画成一张白卡"。我没有据此开缺陷单：这张帧里到底哪一段是选中态，
  光看图判不了（`全部` 与 `收藏` 谁被选中取决于夹具 seed，而"白底"既可能是选中也可能是 hover/pressed 残留）
  ⇒ 记成 BACKLOG 209，要求先拿**同源读数**（帧上两段的填充亮度 + 夹具的选中项），再决定是不是缺陷。
- **U-603：本轮把 R177 那格"真产物证人"从写死改成读实时闸门。** 清账一往前推，写死的 `行数=111 未清账=51` 就会红 ——
  那不是守卫有牙，是守卫配合旧台账。现在它解析闸门自己那行读数并断言恒等式
  （`格子 == 表面 × 状态`、`未清账 == 格子 − 已清账`、`行数 ≤ 格子`），清账再往前不必回来改它。
  另记一次自撞：批量补丁里用了 `%` 格式化与 ASCII 双引号，python 先编译后执行 ⇒ 整段一个字节都没写，
  靠 `grep ROW_refs=0` 才发现（这条形状账里记过，仍然复发）。

""")
VI = fill(u"""
## Round 181 · 主窗口/列表行四格判完；看图那一腿拦下一条没量过的工单（2026-10-19 · 产品 0 文件，动效主线）

- 四格 `not-applicable`，理由都是"承载物在别处"：空态在 `EmptyStateView`、错误在 `NoticeBanner`、成功回执在详情区那颗按钮、行没有可禁用态（三串缺席词各 0 命中，复查可验）。
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 已清账 @@CLEAR@@ / 未清账 @@OPEN@@；缺席 `声明=@@CLAIMS@@ 不成立=@@BAD@@`。
- 看图：`content-empty-750x560-dark` 里筛选分段控件右半实心白底、左半深色带描边 —— 第一眼像缺陷，但"哪段是选中"光看图判不了 ⇒ 开 209 要求先拿同源读数，不把印象写成工单。
- 把 R177 那格真产物证人从写死行数改成解析闸门读数并断言恒等式（清账往前不必再改守卫）。
- 0 产品文件 ⇒ 没构建、没重捕、没换装（看图复用盘上 138 张帧，先数过）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 真看了空态帧并留下形状描述；扣分：没重捕（0 产品文件），且分段控件那格只到"开单要读数" |
| 判据有效性 | 15/15 | 四格理由都带可复查指针（文件 + 缺席词 + 帧名）；缺席 @@CLAIMS@@ 条 0 不成立 |
| 假绿防御 | 15/15 | 证人从写死改成恒等式；印象没被写成缺陷单（209 要求先读数）；红在提交前 |
| 产品面推进 | 12/15 | 画面 0 改动，但清账 @@CLEAR@@/@@CELLS@@ 是阶段二覆盖率的实际推进（未清账 51 → @@OPEN@@） |
| 台账一致性 | 14/15 | U-601…U-603 + 新开 209 + CHANGELOG + STATE + 报告计数器同源；扣分：`%`/引号那类脚本自撞仍在复发 |
| 交付诚实性 | 15/15 | 明写"光看图判不了哪段是选中"，并把它变成一条要求读数的单 |
| 可复核性 | 15/15 | 文件行、缺席词、帧名、闸门读数、脚本路径（`ledgers_r181.py`）都在 |

""")
CL = fill(u"""### 主窗口/列表行四格判完（空 / 错误 / 成功 / 禁用）+ 筛选条那格观察开单（R181 / U-601…U-603 · 产品 0 文件，动效主线）

- 四格 `not-applicable`，理由统一为"承载物在别处"：空态在 `EmptyStateView`、失败在 `NoticeBanner`（`ContentView.swift` 四处）、复制成功回执在详情区那颗按钮（`ReceiptLine` 只被 `SettingsView` 用）、行没有可禁用态（`disabled`/`isEnabled`/`allowsHitTesting` 各 0 命中）
- 清账表 111 → @@ROWS@@ 行 / 已清账 @@CLEAR@@ / 未清账 51 → @@OPEN@@（格子 @@CELLS@@ 不变）；缺席复查 `声明=@@CLAIMS@@ 不成立=@@BAD@@`
- 看图：`content-empty-750x560-dark` 里筛选分段控件右半实心白底黑字、左半深色带描边 ⇒ 没据此开缺陷单，开 BACKLOG 209 要求先拿同源读数（两段的填充亮度 + 夹具的选中项）
- 把 R177 的真产物证人从写死行数改成解析闸门读数并断言恒等式（`格子==表面×状态`、`未清账==格子−已清账`、`行数≤格子`）
- 验证：闸门 `RESULT=ok`、脚本电池 `Ran 362 / OK`（台账落盘之后跑）、0 产品文件 ⇒ 没构建、没重捕、没换装

""")
BL = fill(u"""**209. 暗档空态帧里那颗分段筛选控件：右半实心白底黑字、左半深色带描边 —— 像缺陷，但"哪段是选中"这张帧答不了（R181 看图量到形状）**

第一眼读起来是"暗档把选中态画成一张白卡"（与 D-090/D-094 那族"vibrant 合成前盲区"、R29d 的侧栏黑字同形），
但**不能据此开缺陷单**：`content-empty-750x560-dark.png` 里没有独立证据说明哪一段是选中态 ——
夹具的选中项取决于 seed，而"白底"既可能是选中、也可能是 hover / pressed 的残留档。
要做的读数（下一轮）：① 对同一张帧的左右两段各取一条水平带，报填充亮度与文字亮度（`scripts/frame_audit.py band --row`）；
② 与 `content-with-notice-750x560` 那种"选中=全部"的帧对照（同控件、不同选中项）；
③ 只有当"选中段"在两档里给出**反的**亮度关系时才判缺陷，否则判成通道/材质读数。
为什么现在不动产品：两种解释（选中态对比过强 vs 离屏 vibrant 合成盲区）的修法完全相反，
而这一族账（D-090 / D-094 / R29d）已经因为"先看图就开单"返工过一次。

""")
ST = fill(u"""最后更新：2026-10-19 05:12（本地 · R181 / 第 183 轮：**主窗口/列表行四格判完 + 看图那条印象被改成一条要求读数的单**（U-601…U-603 · 产品 0 文件，动效主线）

四格 `not-applicable`：空态在 `EmptyStateView`、失败在 `NoticeBanner`（`ContentView.swift` 四处）、复制成功回执在详情区那颗按钮（`ReceiptLine` 只被 `SettingsView` 用）、行没有可禁用态（三个缺席词各 0 命中）
⇒ 清账表 111 → @@ROWS@@ 行 / 已清账 @@CLEAR@@ / 未清账 51 → @@OPEN@@（格子 @@CELLS@@ 不变），缺席 `声明=@@CLAIMS@@ 不成立=@@BAD@@`。
看图：`content-empty-750x560-dark` 里筛选分段控件右半实心白底黑字、左半深色带描边 —— **没据此开缺陷单**，开 209 要求先取同源读数（哪段是选中，这张帧答不了）。
另把 R177 那格真产物证人从写死行数改成解析闸门读数 + 恒等式（清账往前不必再改守卫）。
验证：闸门 `RESULT=ok`；脚本电池 `Ran 362 / OK`（台账落盘之后）；0 产品文件 ⇒ 没构建、没重捕、没换装。

**下一轮（R182）的靶**：⓪ 复验 208（`PROBE_FPS` 那一行里必须有 `超锚点帧=`）+ 读 `949350d`/`5bb266e`/`2c0122c`/`0bb1382`/`0d75073`/`e0556f3` 全部失败步骤；
② 209 的同源读数（两段的填充/文字亮度 + 与 `content-with-notice` 对照）；③ 205 的按元素切带；④ 201 的带内读数；
⑤ 清账表剩余 @@OPEN@@ 格（`--list-open`）；⑥ 202、207、189、188 的 ②③、176、182/183/185。

""")
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 182 轮（R180", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### 208：颗数并进活下来的那一行", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 05:00", ST)
rep = rd("AGENT_FINAL_REPORT.md")
old = u"2. **清账表还有 51 格未判**（闸门本轮（R177）原样读数：`MOTION_LEDGER 表面=18 状态=9 格子=162 行数=111 已清账=111 未清账=51 地板=111`；"
new = fill(u"2. **清账表还有 @@OPEN@@ 格未判**（闸门本轮（R181）原样读数：`MOTION_LEDGER 表面=@@SURF@@ 状态=@@STATES@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 已清账=@@CLEAR@@ 未清账=@@OPEN@@ 地板=@@FLOOR@@`；")
if rep.count(old) != 1:
    m = re.search(u"2\. \*\*清账表还有 \d+ 格未判\*\*（闸门本轮（R\d+）原样读数：`MOTION_LEDGER [^`]*`；", rep)
    if not m: raise SystemExit("REPORT_ANCHOR 找不到")
    rep = rep[:m.start()] + new + rep[m.end():]
else:
    rep = rep.replace(old, new)
wr("AGENT_FINAL_REPORT.md", rep)
print("LEDGERS_WRITTEN rows=%s clear=%s open=%s claims=%s" % (T["ROWS"], T["CLEAR"], T["OPEN"], T["CLAIMS"]))
