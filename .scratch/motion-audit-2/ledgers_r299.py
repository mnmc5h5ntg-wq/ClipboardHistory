#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R299（第 298 轮 / Round 296）的七本台账落盘 —— 事务性，与 ledgers_r294c 同一形状。

规矩（栽过之后写死的，别改回去）：
· 七本的新文本**先全部算出来**，再一次性写盘；写盘前跑一次电池拿基线，写盘后再跑一次；
  计数变了或不绿 ⇒ 从内存里把七本全部还原，绝不留半批（R294 那一课）。
· 不往 CJK 正文里写 `%` 格式化（`%s` 会安静拿错键的值）；一律 @TOKEN@ 替换。
· 所有计数由仪器现读：电池、曲线、`scripts/product_streak.py`、帧基线、预检 ARM_TOTAL、U/D/BACKLOG 最大值。
· 写之前按守卫的正则原样自测形状（round_batch 前缀、U 区间与节内定义行吻合、七维表 7 行、
  STATE 最后更新行、以及本轮新增的 353 门要求的两格形状）。
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
FRAMES = "/tmp/r298_verify/frames"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [11, 13, 14, 4, 13, 14, 13]
RUN_RED = u"39795800668"      # fec526e：只动 AGENT_BACKLOG.md
RUN_GREEN = u"39795221489"    # 4190222：同一份 Swift 代码，早一跑
R_TAG = u"R299"
R_NEXT = u"R300"
TODAY = u"2026-10-22"


def s(x):
    return str(x)


def die(m):
    sys.stderr.write(u"LEDGERS_R299 REFUSED: " + m + u"\n")
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


def battery(tag, path=None):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    if path:
        wr(path, txt)
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        blocks = re.findall(u"(?m)^(?:FAIL|ERROR):.*?(?=^(?:FAIL|ERROR):\\s|^Ran \\d)", txt, re.M)
        return None, tag + u" 电池不绿（全文见 %s）：\n%s" % (path or u"?", u"\n---\n".join(blocks)[:4000])
    return (ran[-1], ok[-1], names), ""


def bullet(text, label):
    """按整行标签取 §13 的那一条 bullet；返回 (start, end)。找不到或找到多处都算尺坏。"""
    rx = re.compile(u"(?m)^- \\*\\*" + label + u"\\*\\*：.*?(?=^- |^\\Z)", re.S)
    hits = list(rx.finditer(text))
    if len(hits) != 1:
        die(u"报告 §13 的「%s」bullet 命中 %d 处（要恰好 1 处）" % (label, len(hits)))
    return hits[0].start(), hits[0].end()


# ── 读数（全部现取；任一缺档就整体不写）────────────────────────────
sout, src = sh(["python3", STREAK])
slines = re.findall(u"^PRODUCT_STREAK (.*)$", sout, re.M)
if src != 0 or not slines:
    die(u"product_streak 没出读数（rc=%s）：%s" % (src, sout.strip()[-300:]))
sk = dict(x.split(u"=", 1) for x in slines[0].split())
for key in (u"streak", u"last", u"last_round", u"ui_audit_max_round", u"sources_after"):
    if key not in sk:
        die(u"product_streak 读数缺格 %s：%s" % (key, slines[0]))
if sk[u"sources_after"] != u"0":
    die(u"sources_after=%s ⇒ 尺选错了「最后一笔产品提交」" % sk[u"sources_after"])
STREAK_NOW, LAST_SHA = sk[u"streak"], sk[u"last"]
LAST_ROUND, MAX_ROUND = sk[u"last_round"], sk[u"ui_audit_max_round"]
# **抬一格**：门读的是「台账落盘之后」的数。写盘前 product_streak 现读 streak=STREAK_NOW，
# 而本轮台账会把 UI_AUDIT 的最大节号推到第 ROUND 轮 ⇒ 落盘后同一颗尺读到 streak+1。
# 贴边不是安全（R296 那一课）：这一格若不抬，写盘后的 --check 必然红，而红的原因是尺被本轮推进了，
# 不是账写错了 —— 那种红会把人教成「放宽门」。
STREAK_N = s(int(STREAK_NOW) + 1)
ROUND = int(MAX_ROUND) + 1

bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", FRAMES, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u""])[-1]
CH = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u""])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u""])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u""])[-1]
if not all([CM, CH, MS, AD]) or CM == u"0":
    die(u"帧基线读数缺档或分母为 0（compared=%s）⇒ 空对账不算通过（R140）" % CM)

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

pout, prc = sh(["python3", PRECHECK])
# 读数形状（现读，别照抄上一轮的写法）：
#   ARM_TOTAL files=187 arms=734 dupes=0 repeats=0
#   NEEDLE_PRECHECK tables=93 covered=77 arms=241 bad=0
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_:
    die(u"变异臂预检读数缺档（rc=%s）：%s" % (prc, pout.strip()[-300:]))
ARMS = at[-1][1]
DUPES, REPEATS = at[-1][2], at[-1][3]
BAD = np_[-1][3]
if DUPES != u"0" or REPEATS != u"0" or BAD != u"0":
    die(u"预检有红（dupes=%s repeats=%s bad=%s）⇒ 先修刀表再写台账" % (DUPES, REPEATS, BAD))

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*D-(\\d{3})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (976, 279, 353):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账，先核对再写"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
DN, BLN = D_MAX + 1, BL_MAX + 1
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", ui))

pre, err = battery(u"写盘前", u"/tmp/r299_battery_pre.log")
if pre is None:
    die(err)

TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@RNEXT@": R_NEXT, u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@UD@": s(UD), u"@DN@": s(DN), u"@BLN@": s(BLN), u"@BLN2@": s(BLN + 1),
    u"@STREAK@": STREAK_N, u"@STREAK_NOW@": STREAK_NOW,
    u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@MAXROUND@": MAX_ROUND, u"@CM@": CM, u"@CH@": CH, u"@MS@": MS, u"@AD@": AD,
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@RUNRED@": RUN_RED, u"@RUNGREEN@": RUN_GREEN, u"@TODAY@": TODAY,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,
}


def fill(t):
    for k in sorted(SUBS, key=len, reverse=True):
        t = t.replace(k, SUBS[k])
    return t


def fill_tpl(t, mapping):
    """同一套 @TOKEN@ 替换，但用显式名册（§13 的格子要用「写盘后」的计数，与正文不同源）。"""
    for k in sorted(mapping, key=len, reverse=True):
        t = t.replace(k, mapping[k])
    return t


# ── 七本的新文本 ───────────────────────────────────────────────────
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UD@ · @TODAY@）：产品面那一格改成 git 派生，量完才发现报告里那句「上次改产品是 R263」是假的

- **U-@UA@：「产品面连续零改动的轮数」这一格只有一个取数口。** 新增 `scripts/product_streak.py`：
  `git log -1 -- ClipboardHistory/Sources/` 取最后一笔产品提交（现读 @LASTSHA@ / 第 @LASTROUND@ 轮），
  与 `AGENT_UI_AUDIT.md` 现读的最大节号相减 ⇒ 连续零改动轮数：**写盘前现读 @STREAK_NOW@（最大节 第 @MAXROUND@ 轮）、本轮台账落地后 @STREAK@（最大节 第 @ROUND@ 轮）**。本格按落盘后的读数写，「贴边不是安全」（R296 那一课）。
  派生不出来就 exit 1、不给默认值：subject 里「第 N 轮」缺失或多义、更早的产品提交带着更大的标签
  （标签与 diff 打架）、`..HEAD` 之间仍有动过 Sources 的笔、一个节都解析不到 —— 四种都各自红。
- **U-@UB@：报告 §13 那句「上一次落到 Sources 的改动是 R263 的收藏星字形墨」被 git 驳回，已公开撤回。**
  现读 R263 之后还有 R275、R289、R290 三笔动过产品目录；同一件事按台账短语数得到 7、8、「第十一轮」三个数
  （四种形状：「产品文件 N 个」9 节、「产品 N 文件」140 节、「N 个产品文件」10 节、无陈述 137 节）。
  短语统计量的是「我有没有在本轮正文里写下这句话」，不是「产品有没有动」⇒ 报告与 STATE 当前轮两格
  换成 git 派生，并配 `scripts/tests/test_product_streak_cell.py`（8 格）钉住：数不等红、
  **数对了但那一行没引用本命令也红**（手抄的数下一轮就烂）、格缺席红、两候选不同值红、
  STATE 只认第一节（历史节的旧数不作数）。
- **U-@UC@：runner 那一朵红与本轮改动无关，按同版对照登记而不是放宽。** 台账笔 @RUNRED@
  （只动 `AGENT_BACKLOG.md`）在 STEP[19] Motion coverage floor 红两朵
  （`testRowMoveIsVisibleToTheRuler` 两臂同形：开 1 帧/峰值 0.053、关 1 帧/峰值 0.053；
  `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` 2 < 3），而早一跑 @RUNGREEN@
  （同一份 Swift 代码）整跑 success ⇒ 成因在机器不在代码，归 254/255 那一族（同版两跑之间自己变）。
  处置：地板一条不降、红如实进账（新开 @BLN@），要的是「同版两跑的分布读数」而不是又一次单跑签字。

- **U-@UD@：写台账的守卫也会腐烂，第二种坏法是「拿今天的尺量昨天的笔」。** commit-subject 那一支（R297 装、R298 改成自定位生日）本轮又红三朵：它把**当前轮**读成一个全局数，而扫描范围从判据生日一路到 HEAD ⇒ 每推一轮，历史里那些「R296 代码半」自动变成超前的假红（证人 7b8f123 / 8a3e488 / 5225de5）。改成**按笔取轮**：每一笔与它自己那棵树里的 `AGENT_STATE.md` 对账（`git show <sha>:AGENT_STATE.md`，读不到就红，不许静默放行）。同一轮量出这条界必须有方向：代码半常先于本轮的轮次账 ⇒ 超前 1 轮合法、超前 2 轮红、落后 >2 轮红，三种形状各钉一格正对照（新开 @BLN2@，本轮开单即结案，剩下的「写台账没有门」那一格仍在 348）。

本轮产品文件 0 个（只动 `scripts/` 与台账）。看图腿复用 @ROUND@ 前一轮的 @CM@ 张帧（产品 0 改动才允许这么复用，
且必须先 `ls` 数出帧数、compared 不许为 0）：看了 `heatmap-populated-430x250` 亮/暗两张 ——
暗档图例第一档与「空格子」在肉眼层面几乎同色（71 那一族的旧账，本轮不据此判产品），
亮档前约 10 列整列是空格子（夹具数据只回填了最近若干周，属数据形状不属布局缺陷）。
帧基线 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：产品面那一格换成 git 派生，顺手量出报告里的一句假话

本轮做的事：把「产品面连续零改动几轮」这一格从台账短语改成唯一取数口 `scripts/product_streak.py`，
并因此发现上一版报告写错了主语（R263 → 实为 @LASTSHA@ / R290）。产品文件 0 个 —— 产物是一条被驳回的陈述、
一门 8 格的守卫、一朵按同版对照登记的 runner 红。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 只看热图两张（亮/暗），其余表面本轮没重看；
产品面推进 4 —— 0 个产品文件，git 现读连续 @STREAK@ 轮，这是本审计现在真正的欠账；
台账一致性 13 —— 353 结案并公开撤回报告里那句假话，但 §13 的 bullet 仍是每轮由生成器推，没接进刷新器；
可复核性 13 —— 取数命令唯一化并进门，本轮没加变异刀（测试内部的正对照不替「判据有牙」作证）；
判据有效性 13 / 假绿防御 14 / 交付诚实性 14 —— 新门把「数不对」「数对但没引用」「数缺席」「取末读到最老一节」
各自钉成一格红，runner 那两朵红没被放宽成出口。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（等 347）；② 347 的真机证人（要用户退出 App，路线见 352）；
③ @BLN@（runner 单跑红的分布读数）；④ 348 剩余格、349、350 第二步、351、344、341 的 CI 契约半、339、
312 具名出口、304、296、291；⑤ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""
**D-280（@RTAG@）：台账里每一个「数出来的」陈述都必须绑着一个可重跑的取数命令，否则它不算读数、算印象。**
本轮把产品面那一格交出去才发现：报告与 STATE 里那三句（连续 7 轮 / 第十一轮 / 上次改产品是 R263）
全部来自短语统计与记忆，而短语统计的四种形状各给一个数。定规三条：
① 数量类陈述的取数口写进**同一格**（命令名与数同一行），没有命令名的数就是手抄；
② 取数口派生不出来必须 exit 1 且**不给默认值**（「算不出来必须响」，R102）；
③ 守卫要能区分「数不对」与「数对但没引用」—— 后者照样红，否则下一轮抄一个恰好对上的数就能过门。
"""

BACK_APPEND = u"""  追记（@RTAG@ 结案）：两步修法都落地了。① 取数口 `scripts/product_streak.py` 现读
  `PRODUCT_STREAK last=@LASTSHA@ last_round=@LASTROUND@ ui_audit_max_round=@MAXROUND@ streak=@STREAK_NOW@`（写盘前的读数；本轮台账落地后同一颗尺读到 @STREAK@，两格按后者写）
  —— 报告 §13 与 STATE 当前轮两格都改成由它派生，并**撤回那句「上一次落到 Sources 的改动是 R263」**
  （git 现读 R263 之后还有 R275 / R289 / R290 三笔产品提交）。② 门 `scripts/tests/test_product_streak_cell.py`
  8 格：数不等红、数对但没引用本命令红、格缺席红、两候选不同值红、STATE 只认第一节、
  标签解析的多义与缺失、CLI `--check` 对真台账签字。教训比 350/351 更硬一档：
  **短语统计不是「近似的数」，它量的是另一件事**（我写没写这句话），所以没有「先近似着用」的余地。

**@BLN@. runner 在 STEP[19] Motion coverage floor 单跑红两朵，而同一份 Swift 代码的早一跑整跑绿（@RUNRED@ vs @RUNGREEN@，@RTAG@ 现读）**：两朵红是 `MotionFilmstripTests/testRowMoveIsVisibleToTheRuler`（两臂形状一致：开 1 帧/峰值 0.053、关 1 帧/峰值 0.053 ⇒ 断言判「这次 moveRow 是瞬移」）与 `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt`（`XCTAssertGreaterThanOrEqual` 2 < 3）。@RTAG@ 那笔台账只动了 `AGENT_BACKLOG.md`，产品与测试代码与绿跑逐字节相同 ⇒ 成因在机器不在代码，属 254/255 那一族（同版两跑之间自己变）。**不许据此放宽地板**：单次 runner 读数既不配给产品定罪，也不配替产品脱罪（R87 / D-251 同一课）。做法：① 同一份代码在 runner 上凑够两跑，把「这两朵红的出现率」变成读数而不是巧合；② 出现率 > 0 就登记成有名字的未覆盖（像 155/166 那样按机器×按用例切片），而不是每轮重读一次单跑；③ 若两跑同现，先读 `MOTION_BAND_INTERVAL`（间隔 − 抓帧 = 调度地板）在负载下的读数，再谈判据本身。

**@BLN2@. 台账守卫的第二种腐烂：把「当前轮」读成一个全局数，于是历史笔每轮都在被今天的尺重判（R299 现读三朵假红，证人 7b8f123 / 8a3e488 / 5225de5）**：`scripts/tests/test_commit_subject_hygiene.py` 的扫描范围是「判据生日（含）之后所有笔」，而期望值取自**工作树** STATE 的第一节 ⇒ 本轮把当前轮推到 R299 之后，三笔 R296 的提交立刻被判「标签是手抄的」—— 它们落笔当时是干净的。这与 R298 那一格（锚在 sha 上的基线会滑出窗口）是同一件事的两种坏法：**守卫的期望值必须与它问的那一笔同时代**。修法两条，本轮已落地并结案：① 按笔取轮（`git show <sha>:AGENT_STATE.md`，读不到红，不许静默放行）；② 界要有方向 —— 超前 1 轮合法（代码半先于轮次账）、超前 2 轮红、落后 >2 轮红，三种形状各一格正对照。剩下的欠账（仍开，记在 348）：电池只覆盖 `scripts/tests`，台账正文里的数字没有一道门要求它来自仪器（353 只钉住了产品面那一格）。
"""

CHG_NEW = (u"### Fixed（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 产品面那一格改成 git 派生，撤回报告里的一句假话）\n\n"
           u"新增取数口 `scripts/product_streak.py` 与门 `scripts/tests/test_product_streak_cell.py`（8 格）："
           u"「产品面连续零改动轮数」在 `AGENT_FINAL_REPORT.md` §13 与 `AGENT_STATE.md` 当前轮两格"
           u"**只能由该命令派生**，且那一行必须引用它 —— 数不等红、数对但没引用红、格缺席红、两候选不同值红。"
           u"现读 `PRODUCT_STREAK last=@LASTSHA@ last_round=@LASTROUND@ ui_audit_max_round=@MAXROUND@ streak=@STREAK_NOW@`，"
           u"据此**撤回**上一版报告里「连续 7 轮」与「上一次落到 `Sources/` 的改动是 R263 的收藏星字形墨」两句"
           u"（git 现读 R263 之后还有 R275 / R289 / R290 三笔产品提交）。同一轮把 §13 的计数器全部接到仪器"
           u"（电池 / 曲线 / U·D·BACKLOG 最大值 / 变异臂 / 帧基线），并登记 runner 单跑红两朵"
           u"（新开 @BLN@，地板一条不降）。产品文件 0 个；帧 @CM@ 张 changed=@CH@（复用上一轮帧，本轮无产品改动）；"
           u"脚本电池 Ran @BATT@ / OK (skipped=@SKIP@)。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：本轮已 push 的笔与现读结论成对 ——
`fec526e` → @RUNRED@ / completed / **failure**（STEP[19] Motion coverage floor 两朵红，见 @BLN@；
同一份 Swift 代码的早一跑 `4190222` → @RUNGREEN@ / completed / success ⇒ 机器侧，不是代码侧）；
本轮这笔（`scripts/` 两文件 + 七本台账）由 @RNEXT@ 现取 run 号。要验的两件事：
① 新门 `test_product_streak_cell` 在 runner 上**有没有对象** —— 它读 `git log` 与台账文件，
浅历史会让「最后一笔产品提交」取不到（那一格必须红而不是跳过，与 341 的 sources 浅历史闸门同一件事）；
② STEP[19] 那两朵红在下一跑是否再现：再现 ⇒ 按 @BLN@ 的②登记成有名字的未覆盖；不再现 ⇒ 也不许当成已修。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**353 结案，并当场量出报告里的一句假话** ——
「产品面连续零改动轮数」改由 `scripts/product_streak.py` 派生（写盘前 streak=@STREAK_NOW@、本轮落地后 streak=@STREAK@：最后一笔产品提交 @LASTSHA@ = 第 @LASTROUND@ 轮，UI_AUDIT 走到第 @ROUND@ 轮），报告 §13 与 STATE 两格同步；
**上一版那句「上一次落到 Sources 的改动是 R263」作废**（其后还有 R275 / R289 / R290 三笔产品提交）。
门 8 格，含「数对但没引用也红」。脚本电池 Ran @BATT@ / OK (skipped=@SKIP@)；变异臂 ARM_TOTAL=@ARMS@ bad=0；
帧 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@；产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `scripts/product_streak.py` 的 streak；本节上一版写的「第十一轮」是按短语数的，作废、只作历史不作数）。

① 下一轮（@RNEXT@）的靶：**305 的台阶地板** —— 唯一还挡着它的是 347 的真机证人（需要用户退出正在运行的
「时间剪史」，或回答「收藏星按下够不够明显」；352 写全了路线与两道 fail-closed 断言）。
产品面连续 @STREAK@ 轮 0 改动是本审计现在真正的欠账：若 347 仍挡着，就在**不需要真机**的那半张清单里
点一个位真做动效（候选：314 热图描边语义、291 墨轴、@BLN@ 的 runner 分布读数）。

② 仍开：347（真机或替代证人）、305（等 347）、@BLN@（runner 单跑红的分布读数）、348 的两格、349、
350 的第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、
328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW, "BL": BACK_APPEND,
    "CH": CHG_NEW, "ST": STATE_NEW,
}.items()}

# ── 形状自测（写盘之前；任一不符就一支笔都不动）────────────────────
ui_new = texts["UI"]
title = ui_new.splitlines()[0]
if u"（%s ·" % R_TAG not in title:
    die(u"标题缺 round_batch 要的前缀「（%s」" % R_TAG)
if not re.search(u"U-(\\d+)…U-(\\d+)", title):
    die(u"标题里没有可解析的 U 区间")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})：", ui_new)]
if nums != [UA, UB, UC, UD]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC, UD]))
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", texts["IT"])) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in texts["IT"]:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · %s / 第 \\d+ 轮 / Round \\d+）" % R_TAG,
                 texts["ST"], re.M):
    die(u"STATE 缺「最后更新」行形状")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮" % STREAK_N, texts["ST"])) != 1:
    die(u"STATE 那一格形状不满足 353 的门")
if len(re.findall(u"scripts/product_streak\\.py", texts["ST"])) < 2:
    die(u"STATE 那一格没在数旁边引用取数口")

# ── 幂等与锚点 ─────────────────────────────────────────────────────
orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 %d 轮" % ROUND in orig["UI"]:
    die(u"UI_AUDIT 已有第 %d 轮" % ROUND)
if re.search(u"(?m)^## Round %d · " % RD_N, orig["IT"]):
    die(u"ITERATION 已有 Round %d" % RD_N)
if u"**D-%d" % DN in orig["DEC"]:
    die(u"D-%d 已存在" % DN)
if re.search(u"(?m)^\\*\\*%d\\. " % BLN, orig["BL"]) or re.search(u"(?m)^\\*\\*%d\\. " % (BLN + 1),
                                                            orig["BL"]):
    die(u"%d 或 %d 已存在" % (BLN, BLN + 1))
if u"## %s 状态（" % R_TAG in orig["ST"]:
    die(u"STATE 已有 %s 节" % R_TAG)
if u"%s / 第 %d 轮" % (R_TAG, ROUND) in orig["CH"]:
    die(u"CHANGELOG 已有 %s" % R_TAG)
if orig["UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符（第 %d 轮不唯一）" % (ROUND - 1))
if orig["ST"].count(u"## R298 状态（") != 1:
    die(u"STATE 锚点不符（R298 节不唯一）")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")
if u"追记（%s 结案）" % R_TAG in orig["BL"]:
    die(u"353 已有 %s 的结案追记" % R_TAG)
bl_lines = orig["BL"].splitlines(True)
h353 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**353. ")]
if len(h353) != 1:
    die(u"353 锚点异常（%d 处）" % len(h353))
k353 = len(bl_lines)
later = [i for i in range(h353[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
if later:
    k353 = later[0]
while bl_lines[k353 - 1].strip() == u"":
    k353 -= 1

# ── 报告 §13：三条 bullet 整条重写，数全部来自仪器 ──────────────────
FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UD@**"
           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLN2@**（@BLN@ 与 @BLN2@ 本轮新开）。"
           u"最近这几轮立/改的门：0 告警从散文变成能拦的 `scripts/warning_gate.sh`（343 结案）、"
           u"`pillReading` 带窗上界去掉 + 漏电地板换相对判据（346 结案）、commit-subject 对账与具名豁免退场（348）、"
           u"台账区间的分箱对账（350）、**产品面轮数只能由 `scripts/product_streak.py` 派生（353 结案）**。\n")
SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + 4)
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"
             u"（唯一取数口 `python3 scripts/product_streak.py`：最后一次动 `ClipboardHistory/Sources/` 的是"
             u" `@LASTSHA@`（R290 / 第 @LASTROUND@ 轮 / 2026-10-21），`AGENT_UI_AUDIT.md` 现读到最大 第 @ROUND@ 轮，"
             u"两者相减；该命令派生不出来就 exit 1，不给默认值。写盘前它现读 @STREAK_NOW@，本轮台账把节号推到"
             u" 第 @ROUND@ 轮 ⇒ 本格按落盘后的读数抬一格，「贴边不是安全」R296 那一课）。"
             u"**这一格上一版是假的**：它写「连续 7 轮」「上一次落到 `Sources/` 的改动是 R263 的收藏星字形墨」，"
             u"而 git 现读 R263 之后还有 R275、R289、R290 三笔产品提交 —— 按台账短语数只能数出「我在正文里写没写过这句话」"
             u"（同一件事四种形状：「产品文件 N 个」9 节、「产品 N 文件」140 节、「N 个产品文件」10 节、无陈述 137 节，"
             u"数出 7 / 8 / 「第十一轮」三个不同的数）。353 结案：数改由 git 派生，并配一门 "
             u"`scripts/tests/test_product_streak_cell.py` 要求这一格只能由该命令派生"
             u"（手抄或按短语数都红，数缺席也算红）。这一格仍是本审计现在真正的欠账，不是判据、不是账本 —— "
             u"判据与账本这些轮一直在长（上面两行）。\n")
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R298 节 ② 为准）")
fr_still = fr[a:b]
fr_still = fr_still.replace(u"348 剩余格、349", u"%d（runner 单跑红的分布读数）、348 剩余格、349" % BLN)
fr_still = re.sub(u"R298 节 ②", u"%s 节 ②" % R_TAG, fr_still)
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)          # 从后往前替换，偏移不失效
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]
# §1 的 U 上界：门（test_final_report_headline）允许落后 3 条，本轮一次进 4 条 ⇒ 必须抬，
# 且只能抬到活账现读的最大值（写死数字就是下一轮的假话）。
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+", u"U-31 … U-%d（R299 现读抬到最新一节）" % UD, fr_new, count=1)
if n_ucell != 1:
    die(u"§1 的 U 上界那一格没命中（%d 处）⇒ 形状变了，先读再改" % n_ucell)
if u"scripts/product_streak.py" not in fr_new:
    die(u"报告里找不到取数口引用 ⇒ 353 的修法被回退了，先查")


def fill_tpl(t, mapping):
    for k in sorted(mapping, key=len, reverse=True):
        t = t.replace(k, mapping[k])
    return t


new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": u"".join(bl_lines[:k353]).rstrip(u"\n") + u"\n\n" + texts["BL"].strip(u"\n") + u"\n",
    "ST": orig["ST"].replace(u"## R298 状态（", texts["ST"] + u"## R298 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入，先查" % key)

for key, text in new.items():
    wr(FILES[key], text)

sh(["python3", REFRESH])          # §1 那一格由仪器推到现读

post, err = battery(u"写盘后", u"/tmp/r299_battery_post.log")
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
pairs2 = dict(re.findall(u"(\\d{3})=(\\d{2,3})", byround2))
score = pairs2.get(s(RD_N), u"?")
if score == u"?":
    die(u"曲线里没有 Round %d 的分数 ⇒ ITERATION 那一节没落地或形状不符：%s" % (RD_N, byround2[-120:]))
gaps = (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u"?"])[-1]
print(u"LEDGERS_R299 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") streak=" + STREAK_N + u" frames=" + CM + u"/changed=" + CH
      + u" prod=0 U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN) + u" BACKLOG_new=" + s(BLN)
      + u" arms=" + ARMS + u" derived_score(Round " + s(RD_N) + u")=" + s(score) + u" GAPS=" + gaps)
