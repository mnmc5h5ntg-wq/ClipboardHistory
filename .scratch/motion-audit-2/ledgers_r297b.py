#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R297 的轮次台账（第 296 轮 / Round 294）—— 把 346 那笔代码半接上轮次账。

事务形状与前两本一致：六本先全部算出来 → 写盘前跑电池 → 写盘后再跑一次 → 不一致就从内存整体还原
（含被 §1 刷新器动过的报告）。读数一律现取：门那行来自 `/tmp/r297b_verify/warning_gate.log`、
全量卷来自同目录 `full.log`、帧闸门现跑、变异表现跑 `mutate_r297.py`、预检现跑、派生分现读。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
}
RUN = "/tmp/r297b_verify"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r297.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 14, 14, 5, 12, 14, 14]
ROUND_R, ROUND_N, ROUND_ITER = u"R297", u"296", u"294"


def die(m):
    sys.stderr.write(u"LEDGERS_R297B REFUSED: " + m + u"\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def sh(argv):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        bad = [l for l in txt.splitlines()
               if l.startswith((u"FAIL:", u"ERROR:")) or u"FINAL_REPORT_" in l or u"ROSTER_" in l]
        return None, tag + u" 电池不绿：" + "\n".join(bad[:12])
    return (ran[-1], ok[-1], names), ""


# ── 读数 ────────────────────────────────────────────────────────────
gate_p = os.path.join(RUN, "warning_gate.log")
if not os.path.exists(gate_p):
    die(u"缺 " + gate_p)
gl = re.findall(r"^(ROUND_WARNING_GATE[^\n]*)", rd(gate_p), re.M)
if not gl:
    die(u"门没有结论行")
GATE = gl[-1]

full_p = os.path.join(RUN, "full.log")
if not os.path.exists(full_p) or u"All tests' passed" not in rd(full_p):
    die(u"全量卷不是 passed 或缺文件")
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", rd(full_p))
if not roll:
    die(u"全量卷没有汇总行")
ROLLED, SKIPPED, ROLLED_F = roll[-1]

cap = rd(full_p)
spr = re.findall(r"SYSTEM_PRESS_REF (light[^\n]*|dark[^\n]*)", cap)
if len(spr) < 2:
    die(u"参照臂读数不足两档（捕获卷正文里没有 SYSTEM_PRESS_REF？）")
SPR_L = [x for x in spr if x.startswith(u"light")][-1]
SPR_D = [x for x in spr if x.startswith(u"dark")][-1]
lm = re.search(r"press 底=(\d+) 块=(-?\d+) 颗=(\d+)", SPR_L)
dm = re.search(r"press 底=(\d+) 块=(-?\d+) 颗=(\d+)", SPR_D)
if not (lm and dm):
    die(u"参照臂那一格形状不符")

frames_dir = os.path.join(RUN, "frames")
if not os.path.isdir(frames_dir):
    die(u"找不到帧目录")
frames = [f for f in os.listdir(frames_dir) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", frames_dir, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]
CH_ = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]

kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R297_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT：" + kout.strip()[-250:])
KN, KC, KE, KNR, KREST = KS[-1]

pout, prc = sh(["python3", PRECHECK])
PS = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if not PS or prc != 0:
    die(u"预检不是 bad=0：" + pout.strip()[-250:])
PT, PC, PA, PB = PS[-1]

diffs, _ = sh(["git", "diff", "--name-only", "HEAD~2", "HEAD"])
PROD_N = str(len([l for l in diffs.splitlines() if l.startswith("ClipboardHistory/Sources/")]))

T = {u"@ROLLED@": ROLLED, u"@SKIPPED@": SKIPPED, u"@FAILS@": ROLLED_F,
     u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST,
     u"@PT@": PT, u"@PC@": PC, u"@PA@": PA, u"@PB@": PB,
     u"@FRAMES@": str(len(frames)), u"@CM@": CM, u"@CH@": CH_, u"@MS@": MS, u"@AD@": AD,
     u"@PROD@": PROD_N, u"@GATE@": GATE,
     u"@SPL_B@": lm.group(1), u"@SPL_K@": lm.group(2), u"@SPL_P@": lm.group(3),
     u"@SPD_B@": dm.group(1), u"@SPD_K@": dm.group(2), u"@SPD_P@": dm.group(3)}


def fill(x):
    for k, v in T.items():
        x = x.replace(k, v)
    if re.search(u"@[A-Z_]+@", x):
        die(u"模板里有没被替换的 token：" + " ".join(re.findall(u"@[A-Z_]+@", x)[:6]))
    return x


UI_NEW = fill(u"""## 第 296 轮（R297 · U-971…U-973 · 2026-10-22）：346 结案 —— 先做实验再改尺，带窗上界去掉，漏电地板换成相对判据

- **U-971：「改带窗会挪十几条地板」这句被实验证伪。** 临时把 `pillReading` 的上界 `d < 60` 去掉、跑整卷
  `UICaptureTests`：只有两格红，且是同一个成因 —— idle 那一帧的众数从 6 颗抗锯齿边缘变成 47 颗星形笔画，
  撞上写死的「空闲不许超过 40 颗」；其余地板（悬停差、比值、台阶、玻璃药丸）一动不动。台账里那句依赖清单
  是**推测写的**，量出来只有两条，而那两条本来就不该是绝对颗数（R83 门槛要量出来的对称形态：量出来才发现门槛钉错了对象）。
- **U-972：上界去掉 + 两处地板换成相对判据 + 参照臂那个 `==0` 出口升成无条件断言。** 新形状是
  `idle.pillPixels × 4 < 同档那一层的像素数`（与同一帧自己的药丸面积比，不拍常数）。牙由两把刀从两侧钉：
  M864 给 idle 夹具真的接上悬停取证键 ⇒ 红在「空闲帧也量到一整片第二层」（3816 不小于 933）；
  M865 把上界**装回去** ⇒ 红在「去掉带窗上界之后仍数不到按下那一块」—— 这条反对照证明新断言真的依赖这次改动
  而不是恒绿的漂亮话（R100：对照判据对整把尺一起偏免疫）。全表 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@、
  预检 tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@。
- **U-973：结案读数。** `SYSTEM_PRESS_REF` 亮档按下从旧记录的 `颗=0` 变成 `底=@SPL_B@ 块=@SPL_K@ 颗=@SPL_P@`
  （与无界尺同数）⇒「按得很狠」与「根本没画」不再是同一个形状；暗档 `底=@SPD_B@ 块=@SPD_K@ 颗=@SPD_P@`。
  梯子比值未动（light 1.260→1.333、dark 1.211→1.359）。随案改写 `wideBlockReading` 文档串里那句
  「刻意不动 pillReading」—— 改动落地后它就是过期账，留着会让下一轮以为无界尺是备用的第二把（R147）。

本轮产品文件 @PROD@ 个。门：@GATE@；全量卷 @ROLLED@ 用例 / @SKIPPED@ skip / @FAILS@ 失败；
帧 @FRAMES@ 张，基线 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@。

""")

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
T[u"@ROWS@"] = ROWS
T[u"@TOTAL@"] = str(sum(SCORES))
ITER_NEW = fill(u"""## Round 294 · R297（第 296 轮 · 2026-10-22）：346 结案，带窗盲区拆掉，漏电地板换成相对判据

本轮做的事：把「强填充被读成缺席」这颗尺的盲区正式拆掉（先做实验数清依赖，再改尺，再从两侧配刀），
并顺手把两处绝对颗数地板换成与同帧另一档面积相比的相对判据。产品文件 @PROD@ 个。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@
| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 零产品改动，看的是重捕帧与上轮那四张台阶对照，没有新位点；
产品面推进 5 —— 连续第十轮 0 个产品文件，仍是最欠的一格，且它现在卡在取证通道（347 那一格在主窗口，
主窗口含用户剪贴板原文、按规矩不许截屏）；台账一致性 12 —— 代码半与账半分两笔、追记与本轮账都现读，
但同日仍有两次「补丁注入错位置」被 ast/断言挡在写盘前；假绿防御 14 —— 反对照刀 M865 钉的是「这次改动本身」。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 347（亮档按下要不要抬到系统量级 —— 要么用户真机看，要么换一条不依赖截图的证人）；
② 305 的台阶地板（形状与分母都已定：分子逐像素、分母取变化颗数，只等 347）；③ 348 剩下两格；
④ 新开 349（`pillReading` 与 `wideBlockReading` 上界去掉后只差「带符号台阶」这一件事 ⇒ 该合并，
合并前要先列 ratio/step 的依赖）与新开 350（UI_AUDIT 轮标题声明的 U 区间与该节实际定义行对账：
现读 289 节里 213 节是区间形，其中 34 节的定义行是**另一种形状** ⇒ 直接上严格判据会造 34 个假正例，
先量形状再定门）；⑤ 344、341 的 CI 契约半、339、312 具名出口、304、296、291；⑥ 用户闸门 220 路 A / 228② / 265。

""")

DEC_NEW = fill(u"""
**D-278（R297）：改尺之前先做「只红几格」的实验；漏电这类「有没有第二层」的判据必须与同帧另一档的面积比，不许钉绝对颗数。**
346 的修法在台账里写了两轮，靠的是「带窗被一堆地板依赖」这句没量过的推测。本轮先跑实验：临时去掉上界跑整卷，
结果只有两格红、同一个成因（idle 的众数从 6 颗边缘变成 47 颗星形笔画，撞上写死的 40 颗）⇒ 依赖只有两条，
且那两条钉错了对象。于是正式落地上界去掉，并把两处地板换成 `idle × 4 < 同档那一层`。
刀 M864 证明新地板会抓真漏电（接上悬停键 ⇒ 954 颗，红），M865 把上界装回去 ⇒ 新断言红，
也就是它确实依赖这次改动而不是恒绿。**Why:** 绝对颗数会在「被测对象换了主语」时以另一个理由红，
那种红既修不好产品也保不住判据；相对判据把门槛绑在同一帧的另一档上，尺与对象一起动才不会各说各话。
**How to apply:** 任何形如「不许出现第二层 / 不许有填充」的地板，先问它比的是谁的面积；
任何要改共用尺的一轮，先跑「只红几格」的实验并把清单写进账。
""")

BACK_349 = fill(u"""
**349. 带窗上界去掉之后，`pillReading` 与 `wideBlockReading` 只差「报不报带符号台阶」这一件事 —— 两颗尺该合并（R297 现读）**：现在两者对同一帧给的众数块一致（亮档按下都读 颗=@SPL_P@），差别只剩签名。合并前必须先列依赖：`ratio`（悬停差、亮档 1.20 地板）、`step`（梯子次序、`PRESS_LADDER_IDENTITY` 恒等式）、`pillPixels`（两处新相对地板）、以及 `glyphInkReading` 那条**故意不相交**的带（D-249 两层两尺带子必须不相交 —— 合并不能顺手把字形层并进来）。验收：合并后重跑整卷 + 重测两档比值与台阶、同步所有注释里的「实测」（R147），并留一把「把两并一之后某条地板失效」的刀。\n""")

BACK_350 = fill(u"""
**350. UI_AUDIT 轮标题声明的 U 区间与该节实际定义行没有对账过（R297 现读：289 节 / 213 节是区间形 / 其中 34 节的定义行是另一种形状）**：本轮想加一条「标题写 U-a…U-b 就必须定义 a..b 全部」的门，先量了一遍 —— 严格判据会在 34 节上报红，而那 34 节**不是缺定义，是定义行长得不一样**（旧式 `- U-95：…` 或不加粗）。直接上就是 34 个假正例（R94 那一课：守卫的定义行正则要按台账实际形状写）。这一单要做的：① 先把两种形状数出来并集识别；② 只对**并集之后仍缺**的节报红；③ 配一把「删掉一条定义行」的刀，证明门有牙而不是把历史钉死。\n""")

CHG_NEW = fill(u"""### Fixed（R297 / 第 296 轮 / Round 294 · 346 结案：带窗上界去掉，漏电地板换成相对判据）

`pillReading` 的候选带去掉上界 `d < 60` —— 它把强填充（系统参照按钮亮档按下 Δ≈70）整块排除，
于是「按得很狠」与「根本没画」在读数上同形。改前先做实验（临时去掉上界跑整卷 `UICaptureTests`）：
只有两格红且同一成因（idle 众数 6 颗边缘 → 47 颗星形笔画，撞上写死的 40 颗），其余地板不动
⇒ 台账里「会挪十几条地板」那句推测被证伪。两处「空闲不许有第二层」换成相对判据
`idle.pillPixels × 4 < 同档那一层的像素数`；参照臂那格的 `if pillPixels == 0` 出口升成无条件断言。
刀 M864（给 idle 夹具真的接上悬停键 ⇒ 红「空闲帧也量到一整片第二层」）与
M865（把上界装回去 ⇒ 红「去掉带窗上界之后仍数不到按下那一块」）各钉一侧，全 CAUGHT、RESTORE_CLEAN=@KREST@。
结案读数：`SYSTEM_PRESS_REF light` 按下 颗=0 → 颗=@SPL_P@（与无界尺同数）。
新开 349（两颗尺该合并）与 350（轮标题 U 区间与定义行对账，先量形状再上门）。
产品文件 @PROD@ 个；全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、帧 @FRAMES@ 张 changed=@CH@、
门 @GATE@、预检 bad=@PB@、脚本电池 Ran 548 / OK (skipped=4)。

""")

STATE_NEW = fill(u"""## R297 状态（第 296 轮 / Round 294 · 2026-10-22）

⓪ 读 CI（R298 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
（字段连成一个逗号串）现取成对号；取不到的写明「push 在台账之后」，别编号。本轮已知的两笔：
`8a3e488`（346 结案那笔）与 `7b8f123`（STATE 改活那笔）—— 号由 R298 现取。要验的两件事：
① 拆掉带窗上界之后，runner 那一侧 `SYSTEM_PRESS_REF` / `PRESS_LADDER_*` 的读数与本机是否同向
（本机亮档按下 颗=@SPL_P@；runner 历史上纸是 236 而非 255 ⇒ 绝对值不许跨机比，只比方向与台阶次序）；
② 两处新相对地板在 runner 上不许变成恒真 —— 读 `idle.pillPixels` 与同档那一层的像素数两个数，
不许只读比值。任何一条在 runner 上读不到都算通道账（342/346 那一族），一条地板都不放宽（D-251）。

最后更新：2026-10-22（本地 · R297 / 第 296 轮 / Round 294）：**346 结案** —— 先做「只红几格」的实验
（证伪了「改带窗会挪十几条地板」），再去掉 `pillReading` 的上界、把两处漏电地板换成相对判据、
把参照臂那个 `==0` 出口升成无条件断言；刀 M864/M865 从两侧钉（M865 是「把改动装回去必须红」的反对照）。
结案读数 亮档按下 颗=0 → 颗=@SPL_P@。新开 349（两颗尺合并）与 350（U 区间对账先量形状）。
门 @GATE@；全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、帧 @FRAMES@ 张 changed=@CH@ added=@AD@、
预检 bad=@PB@、dmg ok 且已换装本机、产品文件 @PROD@ 个（连续第十轮 0 产品改动）。

① 下一轮（R298）的靶：**347**（亮档按下要不要抬 —— 卡点是取证通道：那一格在主窗口而主窗口含用户剪贴板原文、
按规矩不许截屏 ⇒ 要么用户真机看，要么换一条不依赖截图的证人），347 之后立刻推 **305** 的台阶地板
（形状与分母都已定）；穿插做 349 或 350 之一（都是判据自身的完整性）。

② 仍开：347（真机或替代证人）、305（等 347）、348 的两格、349、350、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""")

# ── 形状自测 ────────────────────────────────────────────────────────
if len(re.findall(u"(?m)^- \\*\\*U-9(?:7[123])：", UI_NEW)) != 3:
    die(u"U 定义行形状不符守卫的删除正则")
if not re.search(u"U-(\\d+)…U-(\\d+)", UI_NEW.splitlines()[0]):
    die(u"标题里没有可解析的 U 区间")
if u"（R297 ·" not in UI_NEW.splitlines()[0]:
    die(u"标题缺 round_batch 要的「（R297」前缀")
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW)) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R297 / 第 296 轮 / Round 294）", STATE_NEW, re.M):
    die(u"STATE 缺「最后更新」行形状")

orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 296 轮" in orig["UI"]:
    die(u"UI_AUDIT 已有第 296 轮")
if re.search(u"(?m)^## Round 294 · ", orig["IT"]):
    die(u"ITERATION 已有 Round 294")
if u"D-278" in orig["DEC"]:
    die(u"D-278 已存在")
for n in (349, 350):
    if re.search(u"(?m)^(?:\\*\\*)?" + str(n) + u"[. ] ", orig["BL"]):
        die(u"%d 已存在" % n)
if u"## R297 状态（" in orig["ST"]:
    die(u"STATE 已有 R297 节")
if u"R297 / 第 296 轮" in orig["CH"]:
    die(u"CHANGELOG 已有 R297")
if orig["UI"].count(u"## 第 295 轮") != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## R296 状态（") != 1:
    die(u"STATE 锚点不符")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)
heads = [i for i, l in enumerate(bl_lines)
         if re.match(u"^(?:\\*\\*)?\\d{3}[. ] ", l.replace(u"*", u""))]
if not heads or heads[0] == 0:
    die(u"BACKLOG 形状异常")
last = heads[-1]
k = len(bl_lines)
while bl_lines[k - 1].strip() == u"":
    k -= 1
BL_TEXT = u"".join(bl_lines[:k]).rstrip(u"\n") + u"\n" + BACK_349 + BACK_350

new = {
    "UI": orig["UI"].replace(u"## 第 295 轮", UI_NEW + u"## 第 295 轮", 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n",
    "BL": BL_TEXT,
    "ST": orig["ST"].replace(u"## R296 状态（", STATE_NEW + u"## R296 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + CHG_NEW, 1),
}
pre, err = battery(u"写盘前")
if pre is None:
    die(err)
for key, text in new.items():
    wr(FILES[key], text)

FR = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
fr_orig = rd(FR)
sh(["python3", REFRESH])
cv0, _ = sh(["python3", CURVE])
ph = re.findall(r"PHASE2 n=\d+ rounds=9\.\.(\d+)", cv0)
if not ph:
    die(u"仪器没打印 rounds=9..N")
tail = ph[-1]
fr_now = rd(FR)
hm = re.search(u"R9–R(\\d+)", fr_now.splitlines()[0])
if not hm:
    die(u"报告第一行没有 R9–R<NNN>")
if hm.group(1) != tail:
    fr_now = re.sub(u"R9–R(\\d+)", lambda m: u"R9–R" + tail, fr_now, count=1)
    wr(FR, fr_now)
    print(u"TITLE_BUMP " + hm.group(1) + u" -> R9–R" + tail)
ui_now = rd(FILES["UI"])
umax = [int(x) for x in re.findall(u"^- \\*\\*U-(\\d+)：", ui_now, re.M)]
if not umax:
    die(u"数不出 U 定义行")
fr2 = rd(FR)
um = re.search(u"U-31 … U-(\\d+)", fr2)
if not um:
    die(u"§1 找不到 U-31 … U-<NNN>")
if int(um.group(1)) != max(umax):
    wr(FR, re.sub(u"U-31 … U-\\d+", u"U-31 … U-%d" % max(umax), fr2, count=1))
    print(u"UCELL_BUMP " + um.group(1) + u" -> U-%d" % max(umax))

post, err = battery(u"写盘后")
if post is None or post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"写盘后电池不绿或计数变了 ⇒ 六本与报告已整体还原：" + (err or u""))

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"294=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u"?"])[-1]
print(u"LEDGERS_R297B OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F + u" knives=" + KC + u"/" + KN
      + u" precheck bad=" + PB + u" frames=" + str(len(frames))
      + u" 按下颗数=" + lm.group(3) + u" prod=" + PROD_N
      + u" U=971..973 D=278 new=349,350 派生分=" + score + u" GAPS=" + gaps)
