#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R301（第 300 轮 / Round 298）的七本台账落盘 —— 事务性，与 ledgers_r300 同一形状。

本轮**不动产品**（只动 Tests 与 .scratch），所以 streak 由取数口按 as-of 第 300 轮现读（=1），
不假设它是 0；`git show HEAD -- Sources` 为空是正常形状。

规矩（栽过之后写死的）：
· 七本的新文本先全部算出来再一次性写盘；写盘前后各跑一次电池，计数变了或不绿 ⇒ 全部还原（R294）。
· 一律 @TOKEN@ 替换（长 token 先换），不往 CJK 正文里写 `%` 格式化。
· 所有计数由仪器现读：电池、曲线、product_streak、帧基线、预检、变异表、round_verify 摘要。
· 写盘之前按守卫的正则原样自测形状（round_batch 前缀、U 区间与节内定义行吻合、七维表 7 行、
  STATE 最后更新行、353 门要求的两格形状、报告 §13 的 bullet 数与 §1 的 Sources 行）。
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
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
VERIFY_LOG = "/tmp/r301_verify_run.log"
READINGS = "/tmp/r301_frames/capture-readings.log"   # 定向跑的取数口（本轮把它写进账，见 U-@UD@ / @BLN2@）
VERIFY_READINGS = "/tmp/r301_verify/frames/capture-readings.log"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r301.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [11, 13, 14, 4, 13, 14, 14]
R_TAG = u"R301"
R_NEXT = u"R302"
PREV_TAG = u"R300"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
# ⓪ 的成对号（本轮现读，只登记不轮询 = R140）
CI_PAIRS = [(u"f5a563a", u"39806766619", u"success"),
            (u"8f6c300", u"39814465153", u"queued/未判")]


def s(x):
    return str(x)


def die(m):
    sys.stderr.write(u"LEDGERS_R301 REFUSED: " + m + u"\n")
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
    env["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag, path=None):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    if path:
        wr(path, txt)
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        blocks = re.findall(u"(?m)^(?:FAIL|ERROR):.*", txt)
        return None, tag + u" 电池不绿（全文见 %s）：%s" % (path or u"?", u" | ".join(blocks)[:1500])
    return (ran[-1], ok[-1], names), ""


def bullet(text, label):
    rx = re.compile(u"(?m)^- \\*\\*" + label + u"\\*\\*：.*?(?=^- |^\\Z)", re.S)
    hits = list(rx.finditer(text))
    if len(hits) != 1:
        die(u"报告 §13 的「%s」bullet 命中 %d 处（要恰好 1 处）" % (label, len(hits)))
    return hits[0].start(), hits[0].end()


def fill_tpl(t, mapping):
    for k in sorted(mapping, key=len, reverse=True):
        t = t.replace(k, mapping[k])
    return t


# ── 读数 ───────────────────────────────────────────────────────────
dout, drc = sh(["python3", STREAK])
dline = (re.findall(u"^PRODUCT_STREAK (.*)$", dout, re.M) or [u""])[-1]
dk = dict(x.split(u"=", 1) for x in dline.split() if u"=" in x)
if drc != 0 or u"ledger_round" not in dk:
    die(u"product_streak 没出现读（rc=%s）：%s" % (drc, dout.strip()[-300:]))
MAX_ROUND = dk[u"ledger_round"]
ROUND = int(MAX_ROUND) + 1
fout, frc = sh(["python3", STREAK, "--streak-for", s(ROUND)])
fl = (re.findall(u"^PRODUCT_STREAK_FOR (.*)$", fout, re.M) or [u""])[-1]
fk = dict(x.split(u"=", 1) for x in fl.split() if u"=" in x)
if frc != 0 or u"streak" not in fk:
    die(u"--streak-for 第 %d 轮取不到：%s" % (ROUND, fout.strip()[-300:]))
STREAK_N = fk[u"streak"]
LAST_SHA = (re.findall(u"last=(\\S+)", fl) or [u"?"])[-1]
LAST_ROUND = (re.findall(u"last_round=(\\d+)", fl) or [u"?"])[-1]
if LAST_ROUND != s(ROUND - 1):
    die(u"as-of 第 %d 轮读到的最后一笔产品提交是第 %s 轮 ⇒ 与本轮（第 %d 轮）不同源，先查"
        % (ROUND, LAST_ROUND, ROUND))

vlog = rd(VERIFY_LOG) if os.path.exists(VERIFY_LOG) else u""
VSUM = (re.findall(u"(?m)^ROUND_VERIFY (.*)$", vlog, re.M) or [u""])[-1]
vk = dict(x.split(u"=", 1) for x in VSUM.split() if u"=" in x)
for key in (u"build_warnings", u"swift_executed", u"swift_failures", u"frames",
            u"baseline_compared", u"baseline_changed", u"dmg", u"installed_version"):
    if key not in vk:
        die(u"round_verify 摘要缺格 %s（摘要行=%r）⇒ 四件套没跑完" % (key, VSUM[:200]))
if vk[u"baseline_changed"] != u"0" or vk[u"swift_failures"] != u"0" or vk[u"build_warnings"] != u"0":
    die(u"四件套不干净（changed=%s failures=%s warnings=%s）"
        % (vk[u"baseline_changed"], vk[u"swift_failures"], vk[u"build_warnings"]))

# 读数通道：本轮的全部意义就是「文件里能读到 marker」，所以这一格必须现数
if not os.path.exists(READINGS):
    die(u"读数文件不存在：%s ⇒ 通道没接上，本轮不能结案" % READINGS)
rtext = rd(READINGS)
HEAT_COUNTS = {}
for marker in (u"HEAT_RING", u"HEAT_RING_VS_STEP", u"HEAT_LOUDNESS", u"HEAT_ADJACENT",
               u"HEAT_STRIP", u"HEAT_INK_SPACE", u"HEAT_RING_CONFINEMENT"):
    HEAT_COUNTS[marker] = len(re.findall(u"(?m)^" + marker + u"[ _]", rtext))
for marker, want in ((u"HEAT_RING_VS_STEP", 20), (u"HEAT_ADJACENT", 16),
                     (u"HEAT_LOUDNESS", 10), (u"HEAT_RING", 20)):
    if HEAT_COUNTS[marker] < want:
        die(u"文件里 %s 只有 %d 行（判据自己要求 %d 条）⇒ 通道仍然在丢读数"
            % (marker, HEAT_COUNTS[marker], want))
SHIPPED_RATIO = (re.findall(u"HEAT_RING_VS_STEP [^\\n]*?倍率\\(对最重\\)=([0-9.]+)", rtext) or [u"?"])
SHIPPED_RATIO = u"%.2f…%s" % (float(SHIPPED_RATIO[0]), SHIPPED_RATIO[-1]) if SHIPPED_RATIO != [u"?"] else u"?"

# 取数口必须是**本轮那一次**的产物，不许是上一轮留在 /tmp 的旧文件（R140：/tmp 会被清；
# 没被清的旧文件更坏 —— 它会让「复用旧读数」看起来像本轮读数）。
import time as _time
_src_day = _time.strftime("%Y-%m-%d", _time.localtime(os.path.getmtime(READINGS)))
if _src_day != TODAY:
    die(u"读数文件 %s 的日期是 %s 而本轮是 %s ⇒ 拿旧跑的数字冒充本轮" % (READINGS, _src_day, TODAY))
# 结构读数（本轮量，不猜）：四件套那一跑的 readings 里有几行 HEAT*？
if not os.path.exists(VERIFY_READINGS):
    die(u"四件套的读数文件不存在：%s" % VERIFY_READINGS)
VERIFY_HEAT = len(re.findall(u"(?m)^HEAT", rd(VERIFY_READINGS)))

kout, krc = sh(["python3", KNIVES])
KS = re.findall(u"(?m)^R301_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                u"RESTORE_CLEAN=(\\w+)", kout)
if krc != 0 or not KS:
    die(u"变异表不是全 CAUGHT（rc=%s）：%s" % (krc, kout.strip()[-400:]))
KN, KC, KE, KNR, KREST = KS[-1]
if KE != u"0" or KNR != u"0" or KREST != u"yes" or KC != KN:
    die(u"变异表不干净：刀=%s CAUGHT=%s ESCAPED=%s NOT_RUN=%s RESTORE_CLEAN=%s"
        % (KN, KC, KE, KNR, KREST))

pout, prc = sh(["python3", PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_:
    die(u"预检读数缺档（rc=%s）：%s" % (prc, pout.strip()[-300:]))
ARMS, BAD = at[-1][1], np_[-1][3]
if at[-1][2] != u"0" or at[-1][3] != u"0" or BAD != u"0":
    die(u"预检有红（dupes=%s repeats=%s bad=%s）" % (at[-1][2], at[-1][3], BAD))

cv, crc = sh(["python3", CURVE])
if crc != 0:
    die(u"曲线仪器不是 0：" + cv.strip()[-200:])
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", cv, re.M) or [u""])[-1]
LAST_RND = (re.findall(r"\bfirst=\d+\s+last=(\d+)", cv) or [u""])[-1]
BYROUND = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv, re.M) or [u""])[-1]
pairs = re.findall(u"(\\d{3})=(\\d{2,3})", BYROUND)
if not SECTIONS or not LAST_RND or len(pairs) < 4:
    die(u"曲线读数缺档（ROUNDS=%s last=%s 分数对=%d）" % (SECTIONS, LAST_RND, len(pairs)))
RD_N = int(LAST_RND) + 1
TAIL_OLD = u" · ".join(u"%s=%s" % (a, b) for a, b in pairs[-4:])

# 354 的出现率（本轮现读的 CI 历史，按「同一份 Swift 树」分组）
APPEAR = u"1/17 与 1/7"

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*D-(\\d{3})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (984, 281, 357):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
DN, BLO, BLN2 = D_MAX + 1, BL_MAX + 1, BL_MAX + 2
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", ui))

pre, err = battery(u"写盘前", u"/tmp/r301_battery_pre.log")
if pre is None:
    die(err)

TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))
MARKERS = u"、".join(u"%s=%d" % (k, v) for k, v in sorted(HEAT_COUNTS.items()))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN),
    u"@BLO@": s(BLO), u"@BLN2@": s(BLN2),
    u"@UD@": s(UD), u"@VHEAT@": s(VERIFY_HEAT), u"@READSRC@": READINGS,
    u"@VREAD@": VERIFY_READINGS,
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@MAXROUND@": MAX_ROUND, u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],
    u"@FRAMES@": vk[u"frames"], u"@SWIFT@": vk[u"swift_executed"], u"@SWFAIL@": vk[u"swift_failures"],
    u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"], u"@WARN@": vk[u"build_warnings"],
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST, u"@TODAY@": TODAY,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,
    u"@MARKERS@": MARKERS, u"@RATIO@": SHIPPED_RATIO, u"@APPEAR@": APPEAR,
    u"@VSBATT@": s(HEAT_COUNTS[u"HEAT_RING_VS_STEP"]),
}


def fill(t):
    return fill_tpl(t, SUBS)


UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UD@ · @TODAY@）：读数终于有了能活下来的通道，热图那 20 条倍率第一次读得到

- **U-@UA@：`HeatmapHoverEvidenceTests` 的 9 行读数改走 `CaptureReadings`（stdout + 文件两条腿）。**
  上一轮我要引用「出货版的环倍率」时本地**一行都拿不到** —— `swift test` 的 stdout 会成块丢
  （R64 量过：同一批代码两遍分别少 324 / 238 行，切点在行中间），只能靠刀 M869 把界写成 0.0
  让判据红一次才逼出数字。本轮结案 357：读数一律 `emit`。现读文件里的 marker：@MARKERS@，
  其中 `HEAT_RING_VS_STEP` @VSBATT@ 条（判据自己要求的正好是 20 条 = 2 外观 × 2 尺度 × 5 档），
  倍率区间 @RATIO@。
- **U-@UB@：那条「零裸 stdout」的绝对规矩原来只扫守卫自己那一个文件。** 这就是它能漏掉一整卷读数的原因。
  现在按**名册**扫（`UICaptureHarness.swift` / `HeatmapHoverEvidenceTests.swift` / `CaptureReadings.swift`），
  并且加了两格防空转：名册里的文件**不存在就红**（改名或删文件不会让守卫悄悄少扫一处），
  每个被扫文件**必须至少用一次 `emit`**（否则「零违规」只是「没东西可违规」的别名）。
  两把刀各钉一侧：M870 把 `emit` 换回裸 stdout ⇒ 红「只走 stdout」；M871 把名册里一个文件名改成不存在的名字 ⇒
  红「不存在」。刀表 @KN@ 把全 CAUGHT=@KC@、RESTORE_CLEAN=@KREST@。
- **U-@UC@：354 的出现率不再是「又一次单跑」。** 把 CI 历史按 **Swift 树**分组
  （`git rev-parse <sha>:ClipboardHistory` 相同 = 同一份 Swift 代码），现读：
  树 `7454b4767ddd` 跑了 17 次全已判、红 5 次，但**失败步骤各不相同** ——
  3 次在 Release script tests（那是当轮已修的守卫腐烂：commit-subject 基线滑窗 + 台账半没刷 §1），
  1 次在 Motion coverage floor（@APPEAR@ 的另一侧是树 `7899574daa7e` 的 7 跑 1 红，R293 的 bd12f4b），
  1 次整跑无失败步骤（aa7e6cc，就是「红着 push」那一笔）。
  ⇒ **动效地板的出现率是 @APPEAR@**，不是「偶发一次可以忽略」，也不是「代码有问题」；
  按 354 的②它该被登记成有名字的未覆盖（按机器×按用例切片，照 155/166 那一族），本单不结案。

- **U-@UD@：本轮的取证目录里读不到本轮的热图读数 —— 四件套那一跑根本没跑热图判据。**
  现数两个文件：定向那一跑 `@READSRC@` 有 @MARKERS@；而四件套的 `@VREAD@` 里以 `HEAT` 开头的读数
  **@VHEAT@ 行**。成因在 `scripts/round_verify.sh` 第 3 步的命令：`swift test --filter UICaptureTests`
  —— 热图悬停那批读数住在 `HeatmapHoverEvidenceTests`，不在这支 filter 的名单里，所以本轮证据目录
  天然缺它（@PREV@ 那一跑同样 @VHEAT@ 行 ⇒ 结构性缺失，不是本轮改坏的）。
  后果不是学术问题：进台账的数字本来应当能从**本轮那一次跑**的证据里复查，现在靠的是散在 /tmp 的
  定向跑文件，而 /tmp 会被清（R140 量过）⇒ 取数口会过期而账还在。登记成 @BLN2@；本轮的处置是把
  取数口的**绝对路径**写进账（上面那条与 CHANGELOG 都写了），不许再用「某个 /tmp 文件」含糊指代。

本轮产品文件 0 个（只动 Tests 与 .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交
是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 @PREV@ 的代码半 ⇒ @PREV@ 归零之后又开始数）。
四件套现读：全量卷 @SWIFT@ 用例 / 失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张
compared=@CM@ changed=@CH@（产品没动 ⇒ changed 必须是 0）、dmg=@Dmg@、换装 @VER@；
预检 ARM_TOTAL=@ARMS@ bad=0。看图腿 RUN：读的是**画面之外的证据** —— 本轮把热图那 20 条倍率、
16 条档间差、10 条响度比从文件里逐条读了一遍（最响一臂 @RATIO@），
帧本身沿 @PREV@ 的基线未变。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：读数有了能活下来的通道，出现率换成同树分组的读数

本轮做的事：把热图判据的 9 行读数从裸 stdout 改成走文件通道（结案 357），
并把「零裸 print」那条规矩从「只扫自己那个文件」扩成按名册扫 + 两格防空转；
顺手把 354 欠的「出现率」从 CI 历史里按 Swift 树分组读出来（动效地板 @APPEAR@）。
产品文件 0 个 —— 产物是一条能复查的读数通道与一批以前拿不到的数字。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 本轮没有新帧，读的是文件里的 20+16+10 条读数与
@PREV@ 那批帧的既有结论，没有新的画面证据；产品面推进 4 —— 0 个产品文件，连续 @STREAK@ 轮；
台账一致性 13 —— streak 与 §1 的 Sources 行第一次由 as-of 现读（不再需要「写台账之前红一次」）；
可复核性 14 —— 读数落盘 + 名册两格防空转 + 两把刀；判据有效性 13 —— 354 只读到出现率，
登记成有名字的未覆盖那一步还没做（本单不结案）；假绿防御 14 / 交付诚实性 14 —— 没有把「通道接上了」
写成「所有卷都接上了」：动效卷那份自带 emit 实现仍在名册之外（新开 @BLO@）。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347 的真机证人 —— 要用户退出 App 或回答一句）；
② 354 的第二步（把动效地板登记成按机器×按用例的有名字未覆盖）；③ @BLO@（两份 emit 实现）；
④ 348 剩余格、349、350 第二步、351、344、341 的 CI 契约半、339、312、304、291；
⑤ 用户闸门 220 路 A / 228② / 265；⑥ @BLN2@（本轮量到的取证面缺口：四件套目录里热图 marker @VHEAT@ 行）。

"""

DEC_NEW = u"""
**D-282（@RTAG@）：一条「绝对不许出现 X」的源码守卫，扫描范围必须是一张会红的名单，而不是守卫自己那个文件。**
R64 立的规矩是「`UICaptureHarness.swift` 里一行裸 stdout 调用都不许有」——它守住了那一个文件，
于是接下来三年里新增的判据卷（热图那 9 行）照旧只走 stdout，而 stdout 是 R64 自己量过**会成块丢**的那条腿。
后果不是理论：@PREV@ 要引用出货版的环倍率时本地一行都拿不到，只能造一把刀（M869）把界写成 0.0、
让判据必然红一次才逼出数字。定规三条：① 规矩按**名册**扫，名册里的文件不存在就红（改名/删文件不许让守卫少扫）；
② 每个被扫文件必须**至少用一次** `emit`，否则「零违规」只是「没东西可违规」的别名；
③ 两侧各配一把刀（把实现换回违规、把名册换成不存在的文件），只有一侧的守卫等于没有守卫。
"""

BACK_357 = u"""  追记（@RTAG@ 结案）：通道接上了，而且不是新造一条 —— 复用 R64 的 `CaptureReadings`（stdout + 文件两条腿、
  整行原子、按 URL 记首次整份重写）。`HeatmapHoverEvidenceTests` 的 9 行读数全部改走 `emit`，
  现读文件里 @MARKERS@（`HEAT_RING_VS_STEP` @VSBATT@ 条 = 判据要求的 20 条，倍率区间 @RATIO@）。
  规矩本身按 D-282 扩成名册扫描 + 两格防空转，刀 M870/M871 各钉一侧。
  结案条件里「凡是改完之后要进账的数都必须来自能活下来的通道」这一条，从本轮起对热图卷成立；
  对动效卷**还不成立**（它自带一颗 R56 时代的 `emit` 实现与三处合法裸 stdout 调用，
  塞进绝对零 print 的名册会把合法实现判成违规）⇒ 那份重复另开 @BLO@，本单不因它不结案。

"""

ITEM_BLO = u"""
**@BLO@. 同一件「读数落盘」有两份实现：`CaptureReadings`（R64）与 `MotionFilmstripTests` 自带的那颗 `emit`（R56），而名册只能扫其中一份（@RTAG@ 现读）**：
把 `MotionFilmstripTests.swift` 塞进「零裸 stdout」的绝对名册会红在它自己的合法代码上 ——
它的 `emit` 实现里那一行 stdout 写就是它的第二条腿，另外两处是它正对照里的字面量。
白名单是下一次绕过去的入口（R55 的 M276），所以本轮选择**不扩名册**，把重复记成这一单。
做法两步：① 让 `MotionFilmstripTests.emit` 变成 `CaptureReadings.emit` 的一层薄壳（删掉自己那份
文件写入与首次整份重写逻辑 —— 那两段已经在 `CaptureReadings` 里被 M338/R81 锤过并发与残file），
② 然后把该文件加进名册，并保留「名册里文件不存在就红」那一格。
做完之前，动效卷的读数仍然依赖它自己那份实现：两条腿长得像，但只有一条被锤过。
"""



ITEM_BLN2 = u"""
**@BLN2@. 一轮的证据目录不是读数汇聚点：`round_verify.sh` 第 3 步只跑 `--filter UICaptureTests`，住在别的判据类里的 marker 永远进不了本轮的 `frames/capture-readings.log`（@RTAG@ 现读：定向跑 @MARKERS@ 对四件套 HEAT=@VHEAT@ 行）**：
  量到的事实：热图悬停那 20 条倍率只在 `@READSRC@` 里，本轮四件套目录 `@VREAD@` 里 HEAT 开头 @VHEAT@ 行；
  @PREV@ 同形状 ⇒ 结构性缺失，不是这一轮改坏的，也不是 `CaptureReadings` 又漏了（357 那条通道本身是通的）。
  为什么值得红：进台账的数字要能从**本轮那一次跑**的证据复查；现在引的是散在 /tmp 的定向跑文件，而 /tmp 会被清（R140）。
  两条候选修法（先量再选，别先写门）：① 第 3 步接受一支 filter 名单，逐类各跑一次，每类读数按类名分文件落到
  `$RUN/readings/`，台账生成器按名册合并且「名册里缺一类就红」—— 前提是先确认不同判据类往同一个 SHOTS 目录
  写样张会不会污染帧基线（R115 / 168 那一族）；② 每个判据类把自己的读数写到 `<shots>/readings/<类名>.log`，
  四件套只做聚合并断言每类都有文件。
  未做之前的规矩（本轮已按它记账）：任何进账的读数必须在账里写清取数口的绝对路径。"""

CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 判据读数落盘，357 结案）\n\n"
           u"`HeatmapHoverEvidenceTests` 的 9 行读数改走 `CaptureReadings`（stdout + 文件两条腿，整行原子）："
           u"`swift test` 的 stdout 会成块丢（R64 量过：两遍分别少 324 / 238 行），"
           u"@PREV@ 因此拿不到出货版的环倍率，只能靠刀 M869 把界写成 0.0 逼一次红。"
           u"本轮现读文件里 @MARKERS@，其中 `HEAT_RING_VS_STEP` @VSBATT@ 条（= 2 外观 × 2 尺度 × 5 档），"
           u"倍率区间 @RATIO@。守卫 `testCaptureReadingsUseTheFileChannel` 从「只扫自己那个文件」扩成**按名册扫**："
           u"名册里的文件不存在就红、每个被扫文件必须至少用一次 `emit`（D-282），"
           u"刀 M870（换回裸 stdout）与 M871（名册放一个不存在的文件）各钉一侧，全 CAUGHT=@KC@/@KN@、"
           u"RESTORE_CLEAN=@KREST@。同一轮把 354 欠的「出现率」按 **Swift 树**分组从 CI 历史里读出来："
           u"动效地板 @APPEAR@（同树 17 跑 1 红 + 另一树 7 跑 1 红），登记成有名字的未覆盖那一步仍欠，本单不结案。"
           u"新开 @BLO@（「读数落盘」两份实现，名册只能扫一份）。"
           u"同一轮量到取证面另一格：四件套目录 `@VREAD@` 里热图 marker = @VHEAT@ 行，"
           u"而定向跑 `@READSRC@` 有整批 ⇒ 第 3 步的 `--filter UICaptureTests` 结构上装不下别的判据类，新开 @BLN2@；"
           u"本轮进账的读数一律写明取数口绝对路径。"
           u"产品文件 0 个；四件套现读：全量卷 @SWIFT@/失败 @SWFAIL@、告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、"
           u"dmg=@Dmg@、换装 @VER@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：成对号现读 ——
`f5a563a` → 39806766619 / completed / **success**（@PREV@ 之前那笔台账：R299 的门 `test_product_streak_cell`
在 runner 上**有对象且没红** ⇒ 浅历史没有把它打成跳过）；
`8f6c300` → 39814465153 / queued / **未判**（@PREV@ 的台账半：要看 STEP[19] 那两朵红是否再现）；
本轮两笔（Tests + 台账半）由 @RNEXT@ 现取。要验的三件事：
① `testCaptureReadingsUseTheFileChannel` 的新名册在 runner 上是否**同数**（它扫的是仓库里的文件，
与机器无关；若红在「不存在」⇒ 是名册与文件树不一致，不是产品）；
② runner 上热图 marker 的条数 —— **这一格现在是已知做不到的**：CI 的抓帧步骤同样只跑 `--filter UICaptureTests`（@BLN2@），
所以按结构它应当读不到（本机四件套目录现读 @VHEAT@ 行）；读到了才要说清是哪一步跑的，读不到不许记成回归；
③ STEP[19] 若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 @APPEAR@，不再需要「等下一次单跑」）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**357 结案 —— 判据读数第一次能活过 `swift test`** ——
热图那 9 行改走 `CaptureReadings`，现读文件里 @MARKERS@（`HEAT_RING_VS_STEP` @VSBATT@ 条，倍率区间 @RATIO@）；
守卫按 D-282 扩成名册扫描 + 两格防空转，刀 M870/M871 全 CAUGHT。
354 的出现率不再靠「下一次单跑」：按 Swift 树分组现读动效地板 @APPEAR@，登记那一步仍欠（本单不结案）。
四件套：全量卷 @SWIFT@/失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@、
dmg=@Dmg@、换装 @VER@；预检 ARM_TOTAL=@ARMS@ bad=0；电池 Ran @BATT@ / OK (skipped=@SKIP@)。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 @PREV@ 的代码半）。

① 下一轮（@RNEXT@）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（照 155/166/171 那一族：名册要能退场、红话要打印键），出现率已有数（@APPEAR@）。
顺带 @BLO@（把动效卷那份 `emit` 收成薄壳，之后名册才能扫它）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、@BLO@（两份 emit 实现）、
@BLN2@（取证目录没有读数汇聚点）、356（悬停换形状的三条候选）、348 的两格、349、350 第二步、351、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW,
    "BL": BACK_357 + ITEM_BLO + ITEM_BLN2, "CH": CHG_NEW, "ST": STATE_NEW,
}.items()}

# ── 形状自测 ───────────────────────────────────────────────────────
ui_new = texts["UI"]
title = ui_new.splitlines()[0]
if u"（%s ·" % R_TAG not in title:
    die(u"标题缺 round_batch 要的前缀")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})：", ui_new)]
if nums != [UA, UB, UC, UD]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC, UD]))
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", texts["IT"])) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in texts["IT"]:
    die(u"ITERATION 缺锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · %s / 第 \\d+ 轮 / Round \\d+）" % R_TAG,
                 texts["ST"], re.M):
    die(u"STATE 缺「最后更新」行形状")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮" % STREAK_N, texts["ST"])) != 1:
    die(u"STATE 那一格形状不满足 353 的门（要「连续零改动 **%s** 轮」）" % STREAK_N)

orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 %d 轮" % ROUND in orig["UI"]:
    die(u"UI_AUDIT 已有第 %d 轮" % ROUND)
if re.search(u"(?m)^## Round %d · " % RD_N, orig["IT"]):
    die(u"ITERATION 已有 Round %d" % RD_N)
if u"**D-%d" % DN in orig["DEC"]:
    die(u"D-%d 已存在" % DN)
for n in (BLO, BLN2):
    if re.search(u"(?m)^\\*\\*%d\\. " % n, orig["BL"]):
        die(u"%d 已存在" % n)
if u"## %s 状态（" % R_TAG in orig["ST"]:
    die(u"STATE 已有 %s 节" % R_TAG)
if u"%s / 第 %d 轮" % (R_TAG, ROUND) in orig["CH"]:
    die(u"CHANGELOG 已有 %s" % R_TAG)
if orig["UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## %s 状态（" % PREV_TAG) != 1:
    die(u"STATE 锚点不符（%s 节不唯一）" % PREV_TAG)
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)
h357 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**357. ")]
if len(h357) != 1:
    die(u"357 锚点异常（%d 处）" % len(h357))
k357 = len(bl_lines)
later = [i for i in range(h357[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
if later:
    k357 = later[0]
while bl_lines[k357 - 1].strip() == u"":
    k357 -= 1
if u"追记（%s 结案）" % R_TAG in orig["BL"]:
    die(u"357 已有 %s 的结案追记" % R_TAG)

# ── 报告 §13 三条 bullet + 标题/U 格/Sources 行 ─────────────────────
FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"
              u"（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的"
              u"最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，也就是 @PREV@ 的代码半 —— "
              u"@PREV@ 动了 2 个文件把这条纪录归零，本轮（@RTAG@）只动 Tests 与 .scratch ⇒ 又开始数）。"
              u"这一格不再有任何「我自己数出来的」版本：手抄、按短语数、数缺席、两候选不同值，四种都红。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**"
           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLO@**。"
           u"最近这几轮立/改的门：0 告警能拦（343）、`pillReading` 带窗上界去掉（346）、"
           u"commit-subject 对账与豁免退场（348）、台账区间分箱（350）、产品面轮数只能由 "
           u"`scripts/product_streak.py` 派生（353）、交互标记不许比一次数据变化更响（314 结案，D-281）、"
           u"**判据读数必须有能活下来的通道，规矩按名册扫且名册不许空转（357 结案，D-282）**；"
           u"但**一轮的证据目录不是汇聚点**：本轮四件套的 readings 里热图 marker = **@VHEAT@ 行**，"
           u"而同轮定向跑有 @VSBATT@ 条（取数口 @READSRC@）⇒ 新开 @BLN2@，进账读数自此要在账里写清取数口绝对路径。\n")

SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + 4)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
fr_still = fr_still.replace(u"348 剩余格、349",
                            u"354 的第二步（登记成有名字的未覆盖）、%d（两份 emit 实现）、348 剩余格、349" % BLO)
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]

fr_new, n_title = re.subn(u"R9–R\\d+，\\d+ 轮自评",
                          u"R9–R%d，%s 轮自评" % (RD_N, SUBS2[u"@SECTIONS@"]), fr_new, count=1)
if n_title != 1:
    die(u"报告标题那一格没命中（%d 处）" % n_title)
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+", u"U-31 … U-%d（@RTAG@ 现读抬到最新一节）" % UC,
                          fr_new, count=1)
if n_ucell != 1:
    die(u"§1 的 U 上界那一格没命中（%d 处）" % n_ucell)
fr_new = fill_tpl(fr_new, SUBS2)
# Sources 那一格本轮不刷（产品没动）——但必须确认它仍然指向 as-of 的那一笔，否则说明 §1 在说谎
sources_row = u"**%s**（commit `%s`）" % (PREV_TAG, LAST_SHA)
if sources_row not in fr_new:
    die(u"§1 的 Sources 那一格不指向 as-of 读到的 @LASTSHA@ ⇒ 要么账错了，要么取数口错了"
        .replace(u"@LASTSHA@", LAST_SHA))
if u"scripts/product_streak.py" not in fr_new:
    die(u"报告里找不到取数口引用 ⇒ 353 的修法被回退了，先查")

new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": (u"".join(bl_lines[:k357]).rstrip(u"\n") + u"\n\n" + texts["BL"].strip(u"\n")
           + u"\n\n" + u"".join(bl_lines[k357:]).lstrip(u"\n")),
    "ST": orig["ST"].replace(u"## %s 状态（" % PREV_TAG, texts["ST"] + u"## %s 状态（" % PREV_TAG, 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
sec = re.compile(u"(?m)^## 13\\. .*?(?=^## |\\Z)", re.S)
old_sec, new_sec = sec.search(orig["FR"]), sec.search(new["FR"])
if not (old_sec and new_sec):
    die(u"§13 那一节在写前或写后不见了")
n_old = len(re.findall(u"(?m)^- \\*\\*", old_sec.group(0)))
n_new = len(re.findall(u"(?m)^- \\*\\*", new_sec.group(0)))
if n_new < n_old:
    die(u"§13 的 bullet 从 %d 条变成 %d 条 ⇒ 有内容被吞了" % (n_old, n_new))
if (u"产品面连续零改动轮数 = **%s**" % STREAK_N) not in new["FR"]:
    die(u"报告的 streak 那一格没落成本轮的值")

for key, text in new.items():
    wr(FILES[key], text)

sh(["python3", REFRESH])

post, err = battery(u"写盘后", u"/tmp/r301_battery_post.log")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"写盘后电池不绿 ⇒ 七本已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 七本已还原")

cout, crc2 = sh(["python3", STREAK, u"--check"])
if crc2 != 0:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"353 的门不认这版台账 ⇒ 七本已还原：" + (cout + u"\n").strip()[-400:])

cv2, _ = sh(["python3", CURVE])
byround2 = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv2, re.M) or [u""])[-1]
score = dict(re.findall(u"(\\d{3})=(\\d{2,3})", byround2)).get(s(RD_N), u"?")
if score == u"?":
    die(u"曲线里没有 Round %d 的分数 ⇒ ITERATION 那一节没落地" % RD_N)
gaps = (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u"?"])[-1]
print(u"LEDGERS_R301 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") streak=" + STREAK_N + u" prod=0 markers=" + MARKERS
      + u" ratio=" + SHIPPED_RATIO + u" swift=" + vk[u"swift_executed"] + u"/" + vk[u"swift_failures"]
      + u" knives=" + KC + u"/" + KN + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN)
      + u" BACKLOG_new=" + s(BLN2) + u" derived_score(Round " + s(RD_N) + u")=" + s(score)
      + u" GAPS=" + gaps)
