#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R300（第 299 轮 / Round 297）的七本台账落盘 —— 事务性，与 ledgers_r299 同一形状。

本轮与上一轮的关键差别：**动了产品**（`VisualTokens.swift` 的悬停环与梯子顶档）。
所以取数顺序是硬的：

    ① 代码半（Sources + Tests + 刀表 + 预检名册 + 帧基线）先提交；
    ② 再跑本脚本 —— `scripts/product_streak.py` 那时读到的「最后一笔产品提交」就是本轮那一笔，
       streak 归零，台账里那一格才写得诚实（353 的门读的是这个数）。

规矩（栽过之后写死的）：
· 七本的新文本先全部算出来再一次性写盘；写盘前后各跑一次电池，计数变了或不绿 ⇒ 全部还原（R294）。
· 不往 CJK 正文里写 `%` 格式化；一律 @TOKEN@ 替换（长 token 先换，免得 @BLN@ 被 @BL@ 吃掉）。
· 所有计数由仪器现读：电池、曲线、product_streak、帧基线、预检、round_verify 摘要、代码半的文件数。
· 写之前按守卫的正则原样自测形状（round_batch 前缀、U 区间与节内定义行吻合、七维表 7 行、
  STATE 最后更新行、353 门要求的两格形状）。
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
VERIFY_LOG = "/tmp/r300_verify_run.log"
CAPTURE = "/tmp/r300_verify/capture.log"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r300.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [13, 14, 14, 11, 12, 14, 12]
R_TAG = u"R300"
R_NEXT = u"R301"
TODAY = u"2026-10-22"
RUN_R300_LEDGER = u"f5a563a"        # R299 台账笔（CI 仍 in_progress，未读）
RUN_R300_LEDGER_ID = u"39806766619"


def s(x):
    return str(x)


def die(m):
    sys.stderr.write(u"LEDGERS_R300 REFUSED: " + m + u"\n")
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


# ── 读数（全部现取；任一缺档就整体不写）────────────────────────────
sout, src = sh(["python3", STREAK])
slines = re.findall(u"^PRODUCT_STREAK (.*)$", sout, re.M)
if src != 0 or not slines:
    die(u"product_streak 没出读数（rc=%s）：%s" % (src, sout.strip()[-300:]))
sk = dict(x.split(u"=", 1) for x in slines[0].split())
for key in (u"streak", u"last", u"last_round", u"ui_audit_max_round"):
    if key not in sk:
        die(u"product_streak 读数缺格 %s：%s" % (key, slines[0]))
STREAK_N, LAST_SHA = sk[u"streak"], sk[u"last"]
LAST_ROUND, MAX_ROUND = sk[u"last_round"], sk[u"ui_audit_max_round"]
# 代码半必须先提交：否则「最后一笔产品提交」还是 R290，这一格会被写成 10 而不是 0。
if LAST_ROUND != s(int(MAX_ROUND) + 1) and LAST_ROUND != s(int(MAX_ROUND)):
    die(u"product_streak 读到最后一笔产品提交是第 %s 轮，而 UI_AUDIT 最大节是第 %s 轮 ⇒ "
        u"本轮的产品改动（代码半）还没提交，先把代码半进账再写台账" % (LAST_ROUND, MAX_ROUND))
ROUND = int(MAX_ROUND) + 1
if LAST_ROUND != s(MAX_ROUND) and LAST_ROUND != s(ROUND):
    die(u"最后一笔产品提交（第 %s 轮）与本轮（第 %d 轮）不同源 ⇒ streak=%s 不可信"
        % (LAST_ROUND, ROUND, STREAK_N))

vlog = ""
if os.path.exists(VERIFY_LOG):
    vlog = rd(VERIFY_LOG)
VSUM = (re.findall(u"(?m)^ROUND_VERIFY (.*)$", vlog, re.M) or [u""])[-1]
vk = dict(x.split(u"=", 1) for x in VSUM.split() if u"=" in x)
for key in (u"build_warnings", u"swift_executed", u"swift_failures", u"frames",
            u"baseline_compared", u"baseline_changed", u"dmg", u"installed_version"):
    if key not in vk:
        die(u"round_verify 摘要缺格 %s（摘要行=%r）⇒ 四件套没跑完，先跑 scripts/round_verify.sh"
            % (key, VSUM[:200]))
if vk[u"baseline_changed"] != u"0" or vk[u"swift_failures"] != u"0":
    die(u"四件套不干净（changed=%s failures=%s）⇒ 先修再写账"
        % (vk[u"baseline_changed"], vk[u"swift_failures"]))
if vk[u"build_warnings"] != u"0":
    die(u"build_warnings=%s ⇒ 0 告警那道门没过（门本体 scripts/warning_gate.sh）"
        % vk[u"build_warnings"])

kout, krc = sh(["python3", KNIVES])
KS = re.findall(u"(?m)^R300_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) "
                u"RESTORE_CLEAN=(\\w+)", kout)
if krc != 0 or not KS:
    die(u"变异表不是全 CAUGHT（rc=%s）：%s" % (krc, kout.strip()[-400:]))
KN, KC, KE, KNR, KREST = KS[-1]
if KE != u"0" or KNR != u"0" or KREST != u"True" or KC != KN:
    die(u"变异表不干净：刀=%s CAUGHT=%s ESCAPED=%s NOT_RUN=%s RESTORE_CLEAN=%s"
        % (KN, KC, KE, KNR, KREST))

pout, prc = sh(["python3", PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_:
    die(u"预检读数缺档（rc=%s）：%s" % (prc, pout.strip()[-300:]))
ARMS, DUPES, REPEATS = at[-1][1], at[-1][2], at[-1][3]
BAD = np_[-1][3]
if DUPES != u"0" or REPEATS != u"0" or BAD != u"0":
    die(u"预检有红（dupes=%s repeats=%s bad=%s）" % (DUPES, REPEATS, BAD))

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

# 代码半的文件数与 sha（产品改动要有可 grep 的证人）
code_files, ccode = sh(["git", "show", "--name-only", "--format=", "HEAD", "--",
                        "ClipboardHistory/Sources"])
if ccode != 0:
    die(u"git show HEAD 取不到文件清单（rc=%s）" % ccode)
PROD = [f for f in code_files.splitlines() if f.strip()]
if not PROD:
    die(u"HEAD 里没有 Sources 改动 ⇒ 代码半没提交，本轮就不是「动了产品」那一轮，先查顺序")
CODE_SHA, _ = sh(["git", "rev-parse", "--short", "HEAD"])
CODE_SHA = CODE_SHA.strip()
TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

pre, err = battery(u"写盘前", u"/tmp/r300_battery_pre.log")
if pre is None:
    die(err)

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*D-(\\d{3})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (980, 280, 355):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账，先核对再写"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
DN, BLN, BLO = D_MAX + 1, BL_MAX + 1, BL_MAX + 2
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3}[：(]", ui))

SUBS = {
    u"@RTAG@": R_TAG, u"@RNEXT@": R_NEXT, u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@UD@": s(UD), u"@DN@": s(DN),
    u"@BLN@": s(BLN), u"@BLO@": s(BLO),
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@MAXROUND@": MAX_ROUND, u"@PROD@": s(len(PROD)), u"@PRODFILES@": u"、".join(
        os.path.basename(f) for f in PROD),
    u"@CODESHA@": CODE_SHA,
    u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],
    u"@FRAMES@": vk[u"frames"], u"@SWIFT@": vk[u"swift_executed"],
    u"@SWFAIL@": vk[u"swift_failures"], u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"],
    u"@WARN@": vk[u"build_warnings"],
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL), u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@KN@": KN, u"@KC@": KC, u"@KREST@": KREST, u"@TODAY@": TODAY,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,
    u"@RUNLEDGER@": RUN_R300_LEDGER, u"@RUNID@": RUN_R300_LEDGER_ID,
}


def fill(t):
    return fill_tpl(t, SUBS)


# ── 七本的新文本 ───────────────────────────────────────────────────
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UD@ · @TODAY@）：热图悬停那一圈被两条界夹住，产品动了 @PROD@ 个文件

- **U-@UA@：新判据 `testHoverIsNotLouderThanOneDataStep` —— 交互不许比一次真实的数据变化更响。**
  分母不是惯例值也不是拍的：同一条 render、同一颗 `meanChannelDelta` 现量四对相邻档在**填充带**上的档步，
  分子是同一档在**描边带**上悬停前后的差。改之前的读数：亮档档步 19.33 / 21.00 / 28.33 / 37.33、
  暗档 17.33 / 18.33 / 25.33 / 33.67，而 0.55 的环在最响的一臂（亮档 2x 空格子）改 **75.50** ⇒
  **交互是这张图最重一次数据变化的两倍**（75.50 ÷ 37.33）。出货版最响的一臂倍率 **0.70**（刀 M869 现读 —— 把界写成 0.0 才拿到的数，见 U-@UD@）。R264 看图时我只写下「那圈一眼可见」，那句话到今天为止只是形容词。
- **U-@UB@：两条界夹出来的窗口原本是空的，所以本轮同时动了调色板。**
  可见性那根地板（`perceptibleBand255 = 18`，R45 从 20 条真读数推出来）与克制度（不超过最重的一步）
  夹出来的窗口是**空集**：按比例算，透明度要 ≥0.274 才在最安静的一臂留得住 18，
  又要 ≤0.272 才在最响的一臂不超过 37.33 —— 两头没有交集（这段是推算，下面四把刀是现读）。
  四把刀各自钉一条轴：**M866** 把环装回 0.55 ⇒ 倍率 1.28 红；**M867** 把环降到 0.12 ⇒
  最安静一臂只改 13.17（<18）红；**M868** 只把顶档退回 0.85、环留在 0.30 ⇒ 倍率 1.11 红
  （⇒ 顶档那一格是承重的，不是审美微调）；**M869** 把界写成 0.0 ⇒ 出货版倍率 0.70 红一次并交出读数。
  所以本轮的修法是**同时动两处**：梯子顶档 0.85 → **0.92** 打开窗口，环 0.55 → **0.30** 落进窗口。
- **U-@UC@：314 结案于「不是选中态的同形物，但确实比数据响」。**
  清点全仓库的选中画法：侧栏与浮层是**系统**画的 accent 胶囊（`HistorySidebarView.swift:173`、
  `QuickPickController.swift:224`），设置行是 `Color.accentColor.opacity(VisualFill.selected=0.16)`
  的**填充** + `.semibold`（`SettingsView.swift:915`）—— 没有任何一处把选中画成描边，
  而热图这一圈是全仓库唯一的 `Color.primary` 描边 ⇒ R264 那句「读起来像选中」在本仓库内部**不成立**。
  成立的是另一半：它比数据响（改前最响一臂是最重一步的两倍，见 U-@UA@），所以本轮按数值改的是强度与梯子顶档，画法（描边）没换。
- **U-@UD@：判据的读数在本地没有通道，本轮靠一把"把界写成 0.0"的刀才拿到。**
  `swift test` 会吞掉通过用例的 `print`（`HEAT_RING` / `HEAT_LOUDNESS` 在 CI 日志里有、本地日志里没有一行），
  所以出货版的环读数拿不到 ⇒ 刀 M869 把 `heaviestDataStepAllowed` 写成 0.0 让那条判据**必然红一次**，
  正文里就带着真数（顺带证明这条界本身是承重的，不是装饰）。新开 @BLO@ 记这条通道缺失。

本轮产品文件 **@PROD@** 个（@PRODFILES@，代码半 @CODESHA@）⇒ **连续零改动纪录归零**：
`scripts/product_streak.py` 现读 streak=@STREAK@（最后一笔产品提交 @LASTSHA@ = 第 @LASTROUND@ 轮）。
看图腿 RUN：改前/改后各看热图两态与整窗（`heatmap-populated` 亮/暗、`heatmap-cell-strip-hover` 亮/暗），
顶档抬深之后最忙的那几格与卡片底的分离更明显、悬停那一圈从"压过一片"退成"指出这一格"。
四件套现读：全量卷 @SWIFT@ 用例 / 失败 @SWFAIL@；build 告警 @WARN@；帧 @FRAMES@ 张、
基线 compared=@CM@ changed=@CH@（同一笔 update）；dmg=@Dmg@、换装本机 @VER@。
变异表 @KN@ 把全 CAUGHT=@KC@、RESTORE_CLEAN=@KREST@；预检 ARM_TOTAL=@ARMS@ bad=0。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：热图悬停那一圈被两条界夹住，动了 @PROD@ 个产品文件

本轮做的事：给"悬停不许比数据响"装上一条能红的判据，量出 0.55 的环是**最重一次数据变化的两倍**，
于是把梯子顶档抬到 0.92、把环降到 0.30 —— 两条界（可见性 18 / 克制度 1.0×最重一步）夹出来的窗口
在改动前是空集，这是本轮动调色板的唯一理由。产品文件 @PROD@ 个（@PRODFILES@），
连续 @STREAK@ 轮零改动的纪录到此归零（数由 `scripts/product_streak.py` 现读，353 那一格第一次派上用场）。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 13 —— 看了改前/改后热图两态与整窗共 8 张，其余表面没重看；
产品面推进 11 —— 动了 @PROD@ 个文件，但只覆盖热图一个位点，主窗口/浮层/菜单栏本轮没重判；
台账一致性 12 —— streak 第一次由 git 派生并随产品改动归零，但 §13 的 bullet 仍是生成器每轮手推；
可复核性 12 —— 判据的读数在本地没有通道（新开 @BLO@），本轮是靠一把刀把它逼出来的；
判据有效性 14 / 假绿防御 14 —— 新界两侧各配刀（M866 装回 0.55、M867 降到 0.12、M868 顶档回退、M869 界写 0）。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **305 的台阶地板**（仍等 347 的真机证人 —— 要用户退出 App 或回答一句）；
② @BLN@（runner 单跑红的分布读数）；③ @BLO@（判据读数的本地通道）；
④ 348 剩余格、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、291；
⑤ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""
**D-281（@RTAG@）：交互标记的强度上限，必须由同一张图上"最重的一次数据变化"来定，不能由"看得见"来定。**
热图悬停那一圈从 R45 起就只有一个理由：在已经有色块的表面上要能读出来 —— 那是**下限**。
本轮补上限（同一条 render、同一颗尺现量四对档步）才发现两条界夹出的窗口是空集
（推算：可见性要 ≥0.274、克制度要 ≤0.272；现读证人：M866 装回 0.55 倍率 1.28、M868 退回顶档倍率 1.11、M867 降到 0.12 最安静一臂 13.17），而唯一同时满足两条的办法是**同时动数据通道**：
梯子顶档 0.85 → 0.92 把最重的一步撑到 ~46，环才降到 0.30。
定规：任何"看得见"式的地板，在给它配修法之前必须先问它的对偶（"不超过什么"）；
只有一边的强度参数都是没被审过的。派生形状限制记在 @BLN@（要让环连最细一档都不许超过，欠的是档数/格宽/换通道）。
"""

BACK_314 = u"""  追记（@RTAG@ 结案）：R264 那句「读起来像选中」被清点驳回，被数值改成成立的另一半。
  ① **不是同形物**：全仓库没有任何一处把选中画成描边 —— 侧栏 `List(selection:)` 与浮层
  `selectionHighlightStyle = .regular` 都是系统 accent 胶囊，设置行是
  `Color.accentColor.opacity(VisualFill.selected=0.16)` 的填充加 `.semibold`；
  而热图这一圈是唯一的 `Color.primary` 描边 ⇒ 换成别的画法不会减少混淆，只会丢掉唯一能钉住它的通道
  （深浅是这张图唯一的信息通道，悬停不许占它 —— 这条由既有判据 `testHoverChangesOnlyTheRingBand` 钉着）。
  ② **但确实过响**：新判据现读 0.55 的环在最响的一臂改 75.50，而最重的一次数据变化只改 37.33 ⇒ 两倍。
  本轮按数值改强度：环 0.55 → **0.30**、梯子顶档 0.85 → **0.92**（两条界夹出的窗口原本为空集，
  抬顶档是为了打开窗口，D-281）。四把刀 M866…M869 各钉一条轴，全 CAUGHT、RESTORE_CLEAN=@KREST@。
  剩下的形状限制不在本单：要让环连**最细**一档都不许超过，这套形状（11pt 格 + 4 档 + 描边环）装不下 ⇒ 新开 @BLN@。

"""

ITEM_BLN = u"""
**@BLN@. 悬停那一圈要「比最细一档数据更安静」在这套形状下数学上装不下（@RTAG@ 现读，D-281 的另一半）**：
可见性地板（`perceptibleBand255 = 18`，最安静的一臂 bucket4/1x 在 0.55 时改 36.10）把透明度顶到 ≥0.274，
而「环 ≤ 最细一档」（亮档 19.33 / 暗档 17.33）要求 ≤0.55×17.33/75.50 ≈ 0.126 —— 两头没有交集。
本轮把界压在**最重的一步**上（`heaviestDataStepAllowed = 1.0`）并把顶档抬到 0.92 才打开窗口，
那是可达到的最强形式，不是妥协成弱判据：刀 M869 把界写成 0.0 会红，M868 把顶档退回 0.85 也会红。
要走到「比最细一档还安静」只能换形状，三条候选按代价排：① 减档数（4 → 3，每步从 ~26 长到 ~35）；
② 加大格子（11pt → 13pt，R73 那条算式会跟着改，窗口右栏要重排）；
③ 悬停换通道（不画墨：几何微抬或 tooltip-only —— 但 330 已判定环境键变化不进胶片，那样这圈就没有产物证人）。
判据侧先欠一格：把「换形状之后界该抬到哪」写成可复查的推导，而不是到时候再挑一个数。
"""

ITEM_BLO = u"""
**@BLO@. 判据的读数在本地没有通道：`swift test` 吞掉通过用例的 print，@RTAG@ 要靠一把刀才拿到出货版读数**：
本轮新判据 `testHoverIsNotLouderThanOneDataStep` 绿的时候，它 `print` 的 20 条 `HEAT_RING_VS_STEP`
在本地日志里**一行都没有**（`/tmp/r300_*.log`：只有 Test Case 行与汇总行），而同样的 print 在 CI 日志里读得到
（R102 那一族 `--readings` 就是为它建的）。后果不是难看，是**账里只能写改前的红数**：
出货版（环 0.30 / 顶档 0.92）的环读数本轮是靠刀 M869 把界写成 0.0、让它必然红一次才从正文里拿到的。
做法两条，别混：① 给判据卷加一条"把结论行写进 `$CLIPBOARD_HISTORY_UI_SHOTS` 同级目录"的落盘通道
（照 R90 那一课：能活下来的通道才是通道，print 不是），② 或者把这条判据的读数升成断言正文的一部分
（绿的时候也在，代价是失败信息变长）。做完之前，凡是"改完之后是多少"这一类进账的数都必须来自
一次会红的运行或一次刀，不许来自记忆，也不许来自按比例换算。
"""

CHG_NEW = (u"### Changed（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 热图悬停那一圈不再比数据响，产品 @PROD@ 文件）\n\n"
           u"新增判据 `HeatmapHoverEvidenceTests/testHoverIsNotLouderThanOneDataStep`（20 条读数 = 2 外观 × 2 尺度 × 5 档）："
           u"分子是悬停在**描边带**上的变化，分母是同一条 render 现量的**相邻档在填充带上的档步**，"
           u"界压在「不超过最重的一次数据变化」。现读改前：亮档档步 19.33 / 21.00 / 28.33 / 37.33、"
           u"暗档 17.33 / 18.33 / 25.33 / 33.67，而 0.55 的环最响一臂改 75.50 ⇒ 两倍于数据。"
           u"产品改动 @PROD@ 个文件（@PRODFILES@）：`VisualHeat.hoverRingOpacity` 0.55 → **0.30**、"
           u"`VisualHeat.ladder` 顶档 0.85 → **0.92** —— 抬顶档是因为两条界（可见性 18 / 克制度 1.0）"
           u"夹出来的窗口原本是空集（≥0.274 与 ≤0.272），D-281。314 结案：热图那一圈**不是**选中态的同形物"
           u"（全仓库没有描边式选中），过响那一半按数值修掉；「比最细一档还安静」这套形状装不下 ⇒ 新开 @BLN@。"
           u"刀 M866…M869 全 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@（现读倍率：装回 0.55 是 1.28、退回顶档是 1.11、环降到 0.12 时最安静一臂只改 13.17、出货版是 0.70）；预检 ARM_TOTAL=@ARMS@ bad=0；"
           u"全量卷 @SWIFT@ 用例 / 失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张基线同一笔 changed=@CH@、"
           u"dmg=@Dmg@ 且已换装本机 @VER@；脚本电池 Ran @BATT@ / OK (skipped=@SKIP@)。"
           u"连续零改动纪录归零（`scripts/product_streak.py` 现读 streak=@STREAK@）。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140）：`@RUNLEDGER@` → run @RUNID@ 本轮取时仍 in_progress /
**未读** —— @RNEXT@ 要现取它与本轮这两笔（代码半 @CODESHA@、台账半）的成对号，
`gh run list --limit 8 --json databaseId,headSha,status,conclusion`。要验的三件事：
① 新判据 `testHoverIsNotLouderThanOneDataStep` 在 runner 上的 20 条读数与本机是否同形
（runner 是 @1x，颗数不可跨机比，但**比值**可：D-276 那一族）；
② R299 那扇门 `test_product_streak_cell` 在 runner 上**有没有对象**（它读 `git log`，浅历史必须红而不是跳过）；
③ 上一跑 STEP[19] 那两朵红是否再现（再现 ⇒ 按 354 的②登记成有名字的未覆盖；不再现 ⇒ 也不许当成已修）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**动了产品 @PROD@ 个文件，连续零改动纪录归零** ——
热图悬停那一圈从 0.55 降到 **0.30**、梯子顶档从 0.85 抬到 **0.92**，理由是新判据现读
「环在最响的一臂改 75.50 而最重的一次数据变化只改 37.33」（两条界夹出的窗口原本为空集，D-281）；
314 结案于「不是选中态的同形物，但确实过响」。`scripts/product_streak.py` 现读 streak=@STREAK@
（最后一笔产品提交 @LASTSHA@ = 第 @LASTROUND@ 轮）。
四件套：全量卷 @SWIFT@/失败 @SWFAIL@、build 告警 @WARN@、帧 @FRAMES@ 张 changed=@CH@（基线同一笔）、
dmg=@Dmg@、换装 @VER@；变异 @KC@/@KN@ 全 CAUGHT、RESTORE_CLEAN=@KREST@；电池 Ran @BATT@ / OK (skipped=@SKIP@)。

① 下一轮（@RNEXT@）的靶：按同一条思路给**其余**只有一根地板的强度参数补对偶 ——
候选是 `VisualFillLift.hover/pressed/selected`（0.04/0.03/0.02，D-249 只钉了带子不相交，没钉上限）
与行内那颗 `RowFavoriteButton` 的 tint（0.55↔0.78）。347/305 仍挡在用户那一边。

② 仍开：347（真机证人，要用户退出 App 或回答一句）、305（等 347）、@BLN@（悬停换形状的三条候选）、
@BLO@（判据读数的本地通道）、354（runner 单跑红的分布读数）、348 的两格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW,
    "BL": BACK_314 + ITEM_BLN + ITEM_BLO,
    "CH": CHG_NEW, "ST": STATE_NEW,
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
    die(u"STATE 那一格形状不满足 353 的门（本轮 streak=%s，正文里要出现「连续零改动 **%s** 轮」）"
        % (STREAK_N, STREAK_N))

# ── 幂等与锚点 ─────────────────────────────────────────────────────
orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 %d 轮" % ROUND in orig["UI"]:
    die(u"UI_AUDIT 已有第 %d 轮" % ROUND)
if re.search(u"(?m)^## Round %d · " % RD_N, orig["IT"]):
    die(u"ITERATION 已有 Round %d" % RD_N)
if u"**D-%d" % DN in orig["DEC"]:
    die(u"D-%d 已存在" % DN)
for n in (BLN, BLO):
    if re.search(u"(?m)^\\*\\*%d\\. " % n, orig["BL"]):
        die(u"%d 已存在" % n)
if u"## %s 状态（" % R_TAG in orig["ST"]:
    die(u"STATE 已有 %s 节" % R_TAG)
if u"%s / 第 %d 轮" % (R_TAG, ROUND) in orig["CH"]:
    die(u"CHANGELOG 已有 %s" % R_TAG)
if orig["UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## R299 状态（") != 1:
    die(u"STATE 锚点不符（R299 节不唯一）")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)
h314 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**314. ")]
if len(h314) != 1:
    die(u"314 锚点异常（%d 处）" % len(h314))
k314 = len(bl_lines)
later = [i for i in range(h314[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
if later:
    k314 = later[0]
while bl_lines[k314 - 1].strip() == u"":
    k314 -= 1
if u"追记（%s 结案）" % R_TAG in orig["BL"]:
    die(u"314 已有 %s 的结案追记" % R_TAG)

# ── 报告 §13：三条 bullet + 产品面那一格，数全部来自仪器 ────────────
FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：产品面连续零改动轮数 = **@STREAK@**"
              u"（唯一取数口 `python3 scripts/product_streak.py`：现读最后一笔动 `ClipboardHistory/Sources/` 的提交"
              u" = @LASTSHA@ / 第 @LASTROUND@ 轮，也就是 @RTAG@ 的代码半 @CODESHA@ —— 本轮动了 @PROD@ 个产品文件"
              u"（@PRODFILES@：热图悬停环 0.55→0.30、梯子顶档 0.85→0.92），所以这条纪录**归零**，"
              u"而不是又被我「数」成别的数）。上一版这一格写的是 9，那是 R299 落台账时的现读值，"
              u"只作历史不作数。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池 **Ran @BATT@**（现读 `python3 -m unittest discover -s scripts/tests`）；"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UD@**"
           u"（`AGENT_UI_AUDIT.md`）；决定最大 **D-@DN@**；BACKLOG 最大 **@BLO@**。"
           u"最近这几轮立/改的门：0 告警能拦（343）、`pillReading` 带窗上界去掉（346）、"
           u"commit-subject 对账与豁免退场（348）、台账区间分箱（350）、产品面轮数只能由 "
           u"`scripts/product_streak.py` 派生（353）、**交互标记不许比一次数据变化更响（314 结案，D-281）**。\n")

SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + 4)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R299 节 ② 为准）")
fr_still = fr[a:b]
fr_still = fr_still.replace(u"348 剩余格、349",
                            u"@BLN@（悬停换形状的三条候选）、@BLO@（判据读数的本地通道）、348 剩余格、349"
                            .replace(u"@BLN@", s(BLN)).replace(u"@BLO@", s(BLO)))
fr_still = re.sub(u"R299 节 ②", u"%s 节 ②" % R_TAG, fr_still)
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+", u"U-31 … U-%d（@RTAG@ 现读抬到最新一节）" % UD,
                          fr_new, count=1)
if n_ucell != 1:
    die(u"§1 的 U 上界那一格没命中（%d 处）" % n_ucell)
fr_new = fill_tpl(fr_new, SUBS2)
if u"scripts/product_streak.py" not in fr_new:
    die(u"报告里找不到取数口引用 ⇒ 353 的修法被回退了，先查")

new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": (u"".join(bl_lines[:k314]).rstrip(u"\n") + u"\n\n" + texts["BL"].strip(u"\n")
           + u"\n\n" + u"".join(bl_lines[k314:]).lstrip(u"\n")),
    "ST": orig["ST"].replace(u"## R299 状态（", texts["ST"] + u"## R299 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
if len(new["FR"]) <= len(orig["FR"]):
    die(u"报告写后不比写前长 ⇒ §13 的 bullet 可能被吞了")

for key, text in new.items():
    wr(FILES[key], text)

sh(["python3", REFRESH])

post, err = battery(u"写盘后", u"/tmp/r300_battery_post.log")
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
print(u"LEDGERS_R300 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") streak=" + STREAK_N + u" prod=" + s(len(PROD)) + u"(" + CODE_SHA + u")"
      + u" frames=" + vk[u"frames"] + u"/changed=" + vk[u"baseline_changed"]
      + u" swift=" + vk[u"swift_executed"] + u"/" + vk[u"swift_failures"]
      + u" knives=" + KC + u"/" + KN + u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN)
      + u" BACKLOG_new=" + s(BLN) + u"," + s(BLO) + u" derived_score(Round " + s(RD_N) + u")="
      + s(score) + u" GAPS=" + gaps)
