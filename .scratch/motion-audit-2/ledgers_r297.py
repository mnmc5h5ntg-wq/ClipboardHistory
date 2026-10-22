#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R296 的轮次台账（第 295 轮 / Round 293）—— 补 R296 那两笔代码半欠的完整验证。

这一轮把 R296 那两笔**代码半**接上完整验证与轮次台账（当时明写过「不占轮次号、留给下一轮」），
并把门本体的读数现取进账。事务形状沿用 ledgers_r295.py：六本先全部算出来 → 写盘前跑电池 →
写盘后跑电池 → 计数不一致就从内存整体还原（含被刷新器动过的报告）。

读数一律现取，不手抄：
· `ROUND_WARNING_GATE` 那行来自 `/tmp/r297_verify/warning_gate.log`（round_verify 第 1 步写的）；
· 变异表由本脚本自己跑 `mutate_r296.py`；预检自己跑 `mutate_needle_precheck.py`；
· 帧闸门 `scripts/frame_baseline.py compare` 现跑；派生分 `curve_from_ledger.py` 现读。

模板里放 `@TOKEN@` 统一 replace（`%` 格式化会按文本顺序吃参数，R87 那一族）。
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
RUN = "/tmp/r297_verify"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r296.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 13, 14, 5, 11, 14, 14]


def die(m):
    sys.stderr.write(u"LEDGERS_R296 REFUSED: " + m + u"\n")
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


# ── 读数（全部现取）──────────────────────────────────────────────────
GATE_LOG = os.path.join(RUN, "warning_gate.log")
if not os.path.exists(GATE_LOG):
    die(u"没有 " + GATE_LOG + u" ⇒ 门这一轮的读数没有对象（先跑 scripts/round_verify.sh " + RUN + u"）")
gate_lines = re.findall(r"^(ROUND_WARNING_GATE[^\n]*)", rd(GATE_LOG), re.M)
if not gate_lines:
    die(u"warning_gate.log 里没有 ROUND_WARNING_GATE 结论行")
GATE = gate_lines[-1]
g_num = re.search(r"warnings=(\d+) incremental=(\d+) cold=(\S+) target=(\S+)", GATE)
if not g_num:
    die(u"门那行形状不符（不许猜数）：" + GATE)
G_W, G_INC, G_COLD, G_TARGET = g_num.groups()

full_p = os.path.join(RUN, "full.log")
if not os.path.exists(full_p) or u"All tests' passed" not in rd(full_p):
    die(u"全量卷不是 passed 或缺文件")
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", rd(full_p))
if not roll:
    die(u"全量卷没有汇总行")
ROLLED, SKIPPED, ROLLED_F = roll[-1]

frames_dir = os.path.join(RUN, "frames")
if not os.path.isdir(frames_dir):
    die(u"找不到帧目录 " + frames_dir)
frames = [f for f in os.listdir(frames_dir) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", frames_dir, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]
CH_ = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]

kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R296_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT：" + kout.strip()[-250:])
KN, KC, KE, KNR, KREST = KS[-1]

pout, prc = sh(["python3", PRECHECK])
PS = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if not PS or prc != 0:
    die(u"预检不是 bad=0：" + pout.strip()[-250:])
PT, PC, PA, PB = PS[-1]

prod_files, _ = sh(["git", "diff", "--name-only", "HEAD~3", "HEAD"])
prod = [l for l in prod_files.splitlines() if l.startswith("ClipboardHistory/Sources/")]
PROD_N = str(len(prod))

T = {
    "@GW@": G_W, "@GINC@": G_INC, "@GCOLD@": G_COLD, "@GTARGET@": G_TARGET,
    "@ROLLED@": ROLLED, "@SKIPPED@": SKIPPED, "@FAILS@": ROLLED_F,
    "@KN@": KN, "@KC@": KC, "@KREST@": KREST,
    "@PT@": PT, "@PC@": PC, "@PA@": PA, "@PB@": PB,
    "@FRAMES@": str(len(frames)), "@CM@": CM, "@CH@": CH_, "@MS@": MS, "@AD@": AD,
    "@PROD@": PROD_N,
}


def fill(s):
    for k, v in T.items():
        s = s.replace(k, v)
    if re.search(r"@[A-Z_]+@", s):
        die(u"模板里有没被替换的 token：" + " ".join(re.findall(r"@[A-Z_]+@", s)[:6]))
    return s


UI_NEW = fill(u"""## 第 295 轮（R296 · U-968…U-970 · 2026-10-22）：0 告警从一句散文变成一道能拦的门，并补上预检看不见 bash 针的那个洞

- **U-968：门本体独立成支 `scripts/warning_gate.sh`，三条规矩都是量出来的。** ① 目标口径与 CI 的 STEP[4] 同一个
  （`swift build --build-tests`，R293 那一课：只编产品目标时测试目标从来没进过编译器）；② 数到 0 要**挣**出来 ——
  换一条全新 scratch-path 冷编再数一遍（暖缓存不重印没改动的文件，「一条告警都没数到」可能只是没重新看）；
  ③ 构建自己失败或没有可判正文一律 exit 2，不许读成干净。`round_verify.sh` 第 1 步改成调它，拦下即
  `ABORTED_AT_WARNING_GATE` 退出。本机基线现读 `ROUND_WARNING_GATE warnings=@GW@ incremental=@GINC@ cold=@GCOLD@ target=@GTARGET@`。
- **U-969：两道门各钉一条轴，两把刀都要求门**自己**响。** M862 注入一条真告警（未使用常量）⇒ 必须 exit 1 且正文含
  `ROUND_WARNING_GATE_FAIL`；M863 把冷编换成必然失败的命令 ⇒ 必须 exit 2 且 `warnings=NOT-RUN`，
  不许 exit 0。全表 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@。第二把钉的是「0 的另一种成因」：
  尺没跑到编译器时数出来的一条告警都没有，读成干净就是假绿（R100 那一族）。
- **U-970：预检报「针不存在」，真凶是它自己的文件类型白名单。** 第一次跑 `mutate_r296` 得 `M863 命中=0` 且
  `NEEDLE_PRECHECK bad=1`、脚本 exit 1 —— 针没错（变异当场 CAUGHT 过），错在 `is_source` 只认 `.swift` 与 `.py`，
  而门本体的刀住在 bash 里 ⇒ **尺看不见被报成针不存在**。白名单补 `.sh` 之后现读
  `NEEDLE_PRECHECK tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@`、exit 0。这一格坏得响亮（它 exit 1），
  所以没有静默放行；但它是本轮唯一把「工具看不见」与「东西不存在」分开的证人，教训登记为 D-277。

本轮产品文件 @PROD@ 个（HEAD~3..HEAD 现数；R296 两笔与本轮只动测试靶、脚本与台账）。
全量卷 @ROLLED@ 用例 / @SKIPPED@ skip / @FAILS@ 失败；帧 @FRAMES@ 张，基线 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@。

""")

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
T["@ROWS@"] = ROWS
T["@TOTAL@"] = str(sum(SCORES))
ITER_NEW = fill(u"""## Round 293 · R296（第 295 轮 · 2026-10-22）：门能拦了，预检的白名单补上 bash

本轮做的事：把上一轮欠的完整验证与轮次台账补齐，并把「0 告警」这件事从汇总行里的一个数变成一道会拦的
门（`scripts/warning_gate.sh` + M862/M863 两轴两刀），顺带查掉预检自己的一个可见性盲区（`.sh` 不在
`is_source` 白名单 ⇒ bash 针被报成不存在）。产品文件 @PROD@ 个。

另一条现读（R295 那笔的 runner 结论，本轮读到）：同一颗 pairDelta 在 runner 上给 亮 27 / 暗 19 的变颗平均，本机是 29 / 21；而颗数 332 对 1290 差约 4 倍（@1x 对 @2x 的面积比）⇒ 305 的地板压在变颗平均上，不只因为它是同源分母（D-276），还因为它是这两台机器之间唯一不随 density 分叉的那一个数（D-272）。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@
| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 零产品改动的一轮，看的是重捕的 174 张里那几组台阶帧，没有新位点；
产品面推进 5 —— 连续第九轮 0 个产品文件，这是本审计现在最欠的一格；台账一致性 11 —— 上一轮欠的台账本轮补上，
但代价是历史里留了一笔 subject 被写坏的 commit（c7b952f，不 amend，见 348）；假绿防御 14 与可复核性 14 ——
门本体单独成支、两把刀各钉一条轴、预检登记在册，任何人都能一条命令重跑。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **347**（亮档按下要不要抬到系统量级 —— 需要真机眼，而那一格在**主窗口**里，
主窗口含用户剪贴板原文、按规矩不许截屏 ⇒ 这一判要么由用户真机看、要么换一条不依赖截图的证人）；
② 305 的台阶地板（形状已定：分子逐像素、分母取变化颗数，等 347）；③ 348（写台账这件事本身没有门）；
④ 346 的带窗下半场（`pillReading` 的 `Δ<60` 仍会把强填充读成缺席，本轮仍未修）；
⑤ 344、343 的 CI 侧（新门在 runner 上从没跑过）、341、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、296、291；⑥ 用户闸门 220 路 A / 228② / 265。

""")

DEC_NEW = fill(u"""
**D-277（R296）：工具「看不见」与东西「不存在」是两种病，报表必须分开；一条只印不拦的读数不算门。**
两件事同一轮撞出来。其一：`round_verify.sh` 过去只把告警数印进汇总行，从不 exit 非零 ——
「0 告警」一直是散文；本轮把它独立成 `scripts/warning_gate.sh`，数到 0 要用一次冷编**挣**出来，
构建失败或没有可判正文一律 exit 2（那是尺坏了，不是干净）。其二：预检第一次报 `M863 命中=0`，
看起来像针写错了，实际是 `is_source` 只认 `.swift` 与 `.py`，bash 里的针它看不见 ——
**尺的覆盖范围不足会被报成被测对象缺失**，与 R90「量不到先问这把尺在反方向灵不灵」、
R140「空对账」同族。定规：任何按文件类型/名册过滤的静态工具，报告缺失之前必须先报自己扫了哪些类型
（本轮把 `.sh` 补进白名单，并在预检输出里保留 tables/covered/arms 三个数互相对账）。
""" )

BACK_348 = fill(u"""
**348. 「写台账」这件事本身没有门（R296 现读两例）**：① 上一轮 R296 的一笔 commit（c7b95b9 之后的 c7b952f）subject 被写坏的 heredoc 咬了 —— 正文里混进 `<<'EOF' PLACEHOLDER` 三行，树是对的、消息是垃圾，而**没有任何判据会红**（不 amend 的规矩留着它当证人，但下一轮要把 subject 改成从台账模板派生，别再手打）；② 同一轮往 `AGENT_BACKLOG.md` 追加 343 的追记，第一次因 heredoc 里的 python 没带 `PYTHONUTF8=1` 而 Non-UTF-8 SyntaxError 整批拒绝 —— 脚本电池那一步**仍然绿**，因为它不读那一格。也就是说「台账没写上」与「台账写错了」在现有判据下同形，都不红。做法：给台账落盘加一格会红的对账（追记锚点命中数、五本行数变化与生成器声明的差、commit subject 与台账轮次标签同源），并配一把「故意漏写一本」的变异刀。\n""")

NOTE_343 = (u"  追记（R296 结案）：两半都落地并被刀钉住 —— 门本体 `scripts/warning_gate.sh`"
            u"（同 CI 的目标口径 / 数到 0 用冷编挣出来 / 构建失败一律 exit 2），`round_verify.sh` 第 1 步调它、"
            u"拦下即退出；本机基线现读 warnings=@GW@ incremental=@GINC@ cold=@GCOLD@ target=@GTARGET@，"
            u"刀 M862/M863 各钉一条轴全 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@。"
            u"剩下的半格转 348（写台账本身没有门）与 STATE ⓪ 的第 ③ 件（这道门在 runner 那一侧从没跑过）。\n")

CHG_NEW = fill(u"""### Improved（R296 / 第 295 轮 / Round 293 · 0 告警变成一道能拦的门，预检补上 bash 的可见性）

新增 `scripts/warning_gate.sh`：与 CI 的 STEP[4] 编同一个目标（`--build-tests`），数到 0 时换全新
scratch-path 冷编把那个 0 挣出来，构建失败或没有可判正文一律 exit 2；`round_verify.sh` 第 1 步改成调它，
拦下即 `ABORTED_AT_WARNING_GATE` 非零退出（原来只把告警数印进汇总行、从不 exit）。
变异表 `mutate_r296.py`：M862（注入未使用常量 ⇒ exit 1 + `ROUND_WARNING_GATE_FAIL`）、
M863（冷编换成必然失败的命令 ⇒ exit 2 + `warnings=NOT-RUN`）全 CAUGHT、RESTORE_CLEAN=@KREST@。
预检 `is_source` 的白名单补 `.sh`（bash 里的针此前被报成「命中 0」= 看不见被当成不存在），
现读 `NEEDLE_PRECHECK tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@`。
本轮补齐 R296 代码半欠的完整验证与轮次台账：全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、0 告警、
帧 @FRAMES@ 张 changed=@CH@ added=@AD@、dmg ok 且已换装本机、产品文件 @PROD@ 个。

""")

STATE_NEW = fill(u"""## R296 状态（第 295 轮 / Round 293 · 2026-10-22）

⓪ 读 CI（R297 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
（字段连成一个逗号串），再 `python3 scripts/ci_read.py steps <run>`。要配对的 push：R295 `5f7dc7b`
⇒ run 39780211456 **completed success**（本轮现读，不是编号未取）：新判据在 runner 上**有对象**（两臂底非 0 才会绿）、R296 代码半 `c7b952f` / `36f8d4a` /
`b1b43da`、本轮这笔（push 在台账之后 ⇒ 号由 R297 现取）。要验的两件事：① 新判据
`testPressTravelSharesOneRulerWithTheSystemReference` 在 runner 上有没有对象（夹具通道的底；读不到是通道账
342/346 那一族，一条地板都不放宽 D-251）；②（本轮已读，转登记）runner 的变颗平均 亮 27 / 暗 19 对 本机 29 / 21 —— 同量级；而颗数 332 对 1290 差约 4 倍，正是 @1x 与 @2x 的面积比 ⇒ 305 的地板只压**变颗平均**，不许压颗数（D-272 与 D-276 在这一格对上）
（本机 亮 自家 29 / 参照 52，暗 21 / 18；不同也只登记，不许把参照臂改成 runner 上能过的形状）；
③ 新门 `scripts/warning_gate.sh` 在 runner 那一侧从没跑过（本机两刀 CAUGHT），两边若给相反处置那是接线缺失
不是阈值问题（R74/R75 那一课）。

最后更新：2026-10-22（本地 · R296 / 第 295 轮 / Round 293）：**「0 告警」从散文变成门** ——
门本体 `scripts/warning_gate.sh`（同 CI 目标口径 / 0 要用冷编挣 / 尺坏了 exit 2），
`round_verify.sh` 第 1 步调它；M862/M863 两轴两刀全 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@；
预检 `is_source` 补 `.sh`（看不见被报成不存在，D-277）；343 结案、开 348（写台账本身没有门）。
全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、0 告警、帧 @FRAMES@ 张 changed=@CH@ added=@AD@、
dmg ok 且已换装本机、产品文件 @PROD@ 个（连续第九轮 0 产品改动）。

① 下一轮（R297）的靶：**348**（给台账落盘加一格会红的对账 + 一把「故意漏写一本」的刀）与
**346 的下半场**（带窗 `Δ<60` 仍会把强填充读成缺席）。347 卡在取证通道：那一格在主窗口，
而主窗口含用户剪贴板原文、按规矩不许截屏 ⇒ 要么用户真机看，要么换一条不依赖截图的证人。

② 仍开：347（真机或替代证人）、305（等 347）、348、346、344、341 的 CI 契约半、339、312 具名出口、
333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""")

# ── 形状自测（写盘之前，按守卫的正则原样验）────────────────────────
if len(re.findall(u"(?m)^- \\*\\*U-9(?:6[89]|70)：", UI_NEW)) != 3:
    die(u"U 定义行形状不符守卫的删除正则（要 `- **U-968：…**` 三行）")
if not re.search(u"U-(\\d+)…U-(\\d+)", UI_NEW.splitlines()[0]):
    die(u"标题里没有可解析的 U 区间")
if u"（R296 ·" not in UI_NEW.splitlines()[0]:
    die(u"标题缺 round_batch 要的「（R296」前缀")
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW)) != 7:
    die(u"七维格子不是 7 行 n/15（本轮实测 " + str(len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW))) + u" 行）")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R296 / 第 295 轮 / Round 293）", STATE_NEW, re.M):
    die(u"STATE 缺「最后更新」行形状")

# ── 幂等与锚点 ──────────────────────────────────────────────────────
orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 295 轮" in orig["UI"]:
    die(u"UI_AUDIT 已有第 295 轮")
if re.search(u"(?m)^## Round 293 · ", orig["IT"]):
    die(u"ITERATION 已有 Round 293")
if u"D-277" in orig["DEC"]:
    die(u"D-277 已存在")
if re.search(u"(?m)^\\*\\*348[. ]", orig["BL"]):
    die(u"348 已存在")
if u"## R296 状态（" in orig["ST"]:
    die(u"STATE 已有 R296 节")
if u"R296 / 第 295 轮" in orig["CH"]:
    die(u"CHANGELOG 已有 R297")
if orig["UI"].count(u"## 第 294 轮") != 1:
    die(u"UI_AUDIT 锚点不符（要恰好一个「## 第 295 轮」，实读 " + str(orig["UI"].count(u"## 第 294 轮")) + u"）")
if orig["ST"].count(u"## R295 状态（") != 1:
    die(u"STATE 锚点不符（R296 节数量不是 1）")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)


def head_of(num):
    return [i for i, l in enumerate(bl_lines) if re.match(u"^(?:\\*\\*)?" + str(num) + u"[. ] ", l.replace(u"*", u""))]


h343 = head_of(343)
h344 = head_of(344)
h346 = head_of(346)
if len(h343) != 1 or len(h344) != 1 or len(h346) != 1:
    die(u"343/344/346 锚点异常 " + str((h343, h344, h346)))
k343 = h344[0]
while bl_lines[k343 - 1].strip() == u"":
    k343 -= 1

pre, err = battery(u"写盘前")
if pre is None:
    die(err)

BL_TEXT = u"".join(bl_lines[:k343]) + NOTE_343 + u"".join(bl_lines[k343:]).rstrip(u"\n") + BACK_348

new = {
    "UI": orig["UI"].replace(u"## 第 294 轮", UI_NEW + u"## 第 294 轮", 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n",
    "BL": BL_TEXT,
    "ST": orig["ST"].replace(u"## R295 状态（", STATE_NEW + u"## R295 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + CHG_NEW, 1),
}
for key, text in new.items():
    wr(FILES[key], text)

FR = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
fr_orig = rd(FR)
sh(["python3", REFRESH])

# 标题尾轮与 §1 的 U 上界都从仪器现读派生（LAG_ROUNDS=1 / LAG_U=3，R295 那一课）。
cv0, _ = sh(["python3", CURVE])
ph = re.findall(r"PHASE2 n=\d+ rounds=9\.\.(\d+)", cv0)
if not ph:
    die(u"仪器没打印 rounds=9..N ⇒ 标题尾轮无从派生")
tail = ph[-1]
fr_now = rd(FR)
hm = re.search(u"R9–R(\\d+)", fr_now.splitlines()[0])
if not hm:
    die(u"报告第一行没有 R9–R<NNN> 形状 ⇒ 标题那一格无从对账")
if hm.group(1) != tail:
    fr_now = re.sub(u"R9–R(\\d+)", lambda m: u"R9–R" + tail, fr_now, count=1)
    wr(FR, fr_now)
    print(u"TITLE_BUMP " + hm.group(1) + u" -> R9–R" + tail)

ui_now = rd(FILES["UI"])
umax = [int(x) for x in re.findall(u"^- \\*\\*U-(\\d+)：", ui_now, re.M)]
if not umax:
    die(u"UI_AUDIT 里数不出 U 定义行 ⇒ §1 的 U 上界无从派生")
fr2 = rd(FR)
um = re.search(u"U-31 … U-(\\d+)", fr2)
if not um:
    die(u"§1 找不到 `U-31 … U-<NNN>` 那一格")
if int(um.group(1)) != max(umax):
    wr(FR, re.sub(u"U-31 … U-\\d+", u"U-31 … U-%d" % max(umax), fr2, count=1))
    print(u"UCELL_BUMP " + um.group(1) + u" -> U-%d" % max(umax))

post, err = battery(u"写盘后")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"写盘后电池不绿 ⇒ 六本与报告已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 六本与报告已还原")

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"293=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u"?"])[-1]
print(u"LEDGERS_R296 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F + u" knives=" + KC + u"/" + KN
      + u" precheck bad=" + PB + u" frames=" + str(len(frames)) + u" gate=" + GATE
      + u" prod=" + PROD_N + u" U=968..970 D=277 new=348 派生分=" + score + u" GAPS=" + gaps)
