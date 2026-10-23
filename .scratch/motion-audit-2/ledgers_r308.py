# -*- coding: utf-8 -*-
"""R308 的七本台账（第 307 轮 / Round 305 · 悬停那一圈搬到格子外面）。

一支脚本写全套账，事务性：任何一处锚点或读数不对 ⇒ 在写任何盘之前退出。
数一律现读：git 的改动面、刀表与历史表的裁定文件、预检、判据卷、曲线仪器、
电池（写盘前后各一遍且必须同数）、product_streak、帧基线、装机结论行。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
KNIVES = "/tmp/r308_table_verdicts.txt"
CHAIN = "/tmp/r308_chain.log"
# 全量卷与判据卷的**证人日志**：两卷都在这一跑里（326 MB，只留 /tmp，永不入库 —— 见
# BACKLOG「.scratch 日志入库规矩」；这里只 grep 它自己打印的结论行，不整份读进内存）。
WIT = "/tmp/r308_full2.log"
R_TAG, PREV_TAG, R_NEXT = u"R308", u"R307", u"R309"
PREV_ROUND, ROUND, RDN = 306, 307, 305
TODAY = u"2026-10-23"
EYE = os.environ.get("R308_EYE", u"")


WROTE = []  # 写盘之后的每一次 die 都必须整体还原（R308 自伤：半套账留在工作树里，只能手工 checkout）
OK_EXIT = []  # 全部闸门通过才置位 —— atexit 用它区分「正常收工」与「崩在半路」


def die(msg):
    if WROTE:
        restore()
        msg = msg + u"（七本已整体还原）"
    sys.stderr.write(u"R308_LEDGERS_REFUSE " + msg + u"\n")
    sys.exit(1)


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


def sh(argv, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(argv, cwd=cwd or ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode("utf-8", "replace"), proc.returncode


def s(x):
    return x if isinstance(x, type(u"")) else json.dumps(x, ensure_ascii=False)


def fill_tpl(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests"], cwd=ROOT)
    with io.open(log_path, "w", encoding="utf-8") as h:
        h.write(out)
    ran = re.findall(r"^Ran (\d+) tests", out, re.M)
    ok = re.search(r"^OK \(skipped=(\d+)\)$", out, re.M) or re.search(r"^OK$", out, re.M)
    if not ran or not ok:
        die(u"%s 电池没有结论行（rc=%d）⇒ 不许把「没解析到」当绿" % (tag, rc))
    if re.search(r"^FAILED", out, re.M):
        reds = [l for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))][:6]
        die(u"%s 电池红：%s" % (tag, u" / ".join(reds)))
    skip = ok.group(1) if ok.lastindex else u"0"
    return ran[-1], skip


def once(text, anchor, replacement, label):
    n = text.count(anchor)
    if n != 1:
        die(u"锚点「%s」命中 %d 次（要恰好 1）" % (label, n))
    return text.replace(anchor, replacement, 1)


if not EYE.strip():
    die(u"看图腿没传 R308_EYE ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读区
pre, pre_skip = battery(u"写盘前", u"/tmp/r308_battery_pre.log")
prod, swift_files, others = [], [], []
# 本轮的改动面**从代码半那一笔提交读**，不从工作树读：账必须落在代码之后（as-of 口径，R300 / D-286），
# 而"先写账再提交代码"会让 streak 这一格在提交之后立刻变成假话（本轮实测：写盘后电池红在
# 「报告那一格写的是 7，git 派生是 8」上，就是这个顺序问题的形状）。
head_sub, _ = sh(["git", "log", "-1", "--format=%s"])
if R_TAG not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 代码半还没提交，账不许先落（%s）" % (R_TAG, head_sub.strip()[:80]))
diff, _ = sh(["git", "show", "--name-only", "--format=", "HEAD"])
for line in diff.splitlines():
    if not line.strip():
        continue
    if line.startswith("ClipboardHistory/Sources/"):
        prod.append(line)
    elif line.startswith("ClipboardHistory/"):
        swift_files.append(line)
    else:
        others.append(line)
if len(prod) != 2:
    die(u"本轮应当动 2 个产品文件，代码半那笔提交里是 %d 个（%s）⇒ 改动面与账对不上"
        % (len(prod), u", ".join(prod)))

chain = rd(CHAIN) if os.path.exists(CHAIN) else u""
for needle, label in ((u"### PRECHECK", u"预检"), (u"### BASELINE UPDATE", u"帧基线更新"),
                      (u"### FULL SUITE", u"全量卷"), (u"### INSTALL", u"换装")):
    if needle not in chain:
        die(u"验证链日志里没有「%s」那一节 ⇒ 那条腿没跑完，不许进账" % label)
warn = re.findall(r"WARNINGS=(\d+)", chain)
if not warn or warn[-1] != u"0":
    die(u"构建告警不是 0（现读 %s）" % (warn[-1] if warn else u"没解析到"))
cap = re.findall(r"CAPTURED (\d+) -> (\S+)", chain)
if not cap:
    die(u"没读到 CAPTURED <n> -> <目录> 那行 ⇒ 帧数不许手填")
FRAMES, SHOT_DIR = cap[-1][0], cap[-1][1]
# 帧基线那两格必须读**更新之前**那一遍：`CHANGED=2` 说的是"本轮的产品改动在帧里看得见"，
# 而 update 之后再对一遍天然是 CHANGED=0 —— 拿最后一遍当证人，就等于让"已经同步过"
# 替"确实变了"作证（这正是 R170 那一族"缺的恰恰是本轮用来下结论的那几行"的形状）。
pre_update = chain.split(u"### BASELINE UPDATE")[0]
base_changed = re.findall(r"FRAME_BASELINE_CHANGED=(\d+)", pre_update)
base_compared = re.findall(r"FRAME_BASELINE_COMPARED=(\d+)", pre_update)
if not base_changed or not base_compared:
    die(u"帧基线对账的 CHANGED / COMPARED 没解析到（更新之前那一遍）⇒ 不许写「基线已同步」")
CHANGED, COMPARED = base_changed[-1], base_compared[-1]
if CHANGED == u"0":
    die(u"CHANGED=0 而本轮动了产品画法 ⇒ 那一遍对账要么跑在改动之前，要么分母是空的")
# 全量卷的结论行**必须按小节切片取**。R308 实测的假账形状：`re.findall(...)` 在整份日志里取末，
# 拿到的是 `### CAPTURE 结论行补记` 那一行（UICaptureTests 那一卷 = 92 格），而它 0 失败 ⇒
# 「FULL_FAIL != 0 就拒写」这道门完全不响，于是 ITER / CHANGELOG / STATE 三本都写着
# 「全量卷 Executed 92 tests, with 4 skipped and 0 failures」，而真读数是 934 / 44 skip / 0。
EXEC_RX = re.compile(u"Executed (\\d+) tests?, with (?:(\\d+) tests? skipped and )?(\\d+) failures?")


def section_parts(text, prefix):
    """把验证链日志按 `### <prefix>…` 切成 (小节标题, 小节正文)（跳遍残留不许互相冒充）。

    `re.split` 只吃掉分隔符 ⇒ **标题与它的正文住在同一个块里**，正文要取本块去掉首行；
    取下一块就是"下一节的第一行"。写错这一格的后果当场被下面那条恒等式闸门抓到
    （FULL SUITE 的正文被读成 INSTALL/CAPTURE 那节 ⇒ 92 顶替 934）。
    """
    chunks = re.split(u"(?m)^### ", text)
    out = []
    for blk in chunks[1:]:
        if blk.strip().startswith(prefix):
            bits = blk.split(u"\n", 1)
            out.append((bits[0].strip(), bits[1] if len(bits) > 1 else u""))
    return out


full_passes = []
for title, body in section_parts(chain, u"FULL SUITE"):
    rows = list(OrderedDict.fromkeys(m.groups() for m in EXEC_RX.finditer(body)))
    if not rows:
        continue          # 那一节没有结论行（只有标题或补记）
    if len(rows) > 1:
        die(u"全量卷小节「%s」里有 %d 行不一致的结论行 ⇒ 哪一跑作数说不清：%s"
            % (title, len(rows), rows))
    full_passes.append((title, rows[0]))
if not full_passes:
    die(u"验证链的 FULL SUITE 小节里没有结论行 ⇒ 不许按「跑过了」写")
FULL_PASS_TITLE, (FULL_RUN, FULL_SKIP, FULL_FAIL) = full_passes[-1]
if FULL_SKIP is None:
    die(u"全量卷那一行读不到 skip 数 ⇒ 结论行的形状漂了：%s" % str(full_passes[-1]))
if FULL_FAIL != u"0":
    die(u"全量卷最后一跑是 %s 朵红 ⇒ 拒绝出账（先修，别把红写成旧跑）" % FULL_FAIL)
# 早先那几跑的红**原样抄进账**，不许抹成"只跑了一遍"：本轮真实顺序是第一跑 3 朵红
# （halo 分类器的数据带写错）→ 修 → 第二跑 0。账上只留第二跑就是把改动过程藏起来。
FULLPASSES = (u"只跑了一跑" if len(full_passes) == 1 else
              u"共 %d 跑：" % len(full_passes)
              + u" ｜ ".join(u"`%s` = %s 格 / %s skip / %s 失败" % (t, r[0], r[1], r[2])
                             for t, r in full_passes)
              + u" ⇒ 引的是最后一跑（前几跑的红是本轮改动过程中自己修掉的，原样留档）")
# 恒等式闸门：全量卷不可能比日志里任何一卷小 —— 再抄到子集（92）时这一格会响。
all_counts = [int(m.group(1)) for m in EXEC_RX.finditer(chain)]
if int(FULL_RUN) < max(all_counts):
    die(u"全量卷读到 %s，而日志里有一卷是 %s ⇒ 全量卷不可能比单卷小，取数口错了"
        % (FULL_RUN, max(all_counts)))
if not os.path.exists(WIT):
    die(u"判据卷的证人日志 %s 不在盘上 ⇒ 判据卷那一格不许手抄" % WIT)
jout, jrc = sh([u"grep", u"-a", u"-A2", u"Test Suite 'HeatmapHoverEvidenceTests'", WIT])
jrows = [m.groups() for m in EXEC_RX.finditer(jout)]
if not jrows:
    die(u"证人日志里读不到 HeatmapHoverEvidenceTests 的每卷结论行（rc=%d）⇒ 不许写「判据卷全绿」" % jrc)
JUDGE_RUN, JUDGE_SKIP, JUDGE_FAIL = jrows[-1]
if JUDGE_FAIL != u"0":
    die(u"判据卷 HeatmapHoverEvidenceTests 是 %s 朵红 ⇒ 拒绝出账" % JUDGE_FAIL)
install = re.findall(r"INSTALL_RESULT=(\S+)", chain)
install_match = re.findall(r"INSTALL_SHA_MATCH=(\d+)", chain)
if not install or install[-1] != u"ok":
    die(u"换装本机不是 ok（现读 %s）" % (install[-1] if install else u"没读到"))

tables = {}
if not os.path.exists(KNIVES):
    die(u"刀表裁定文件 %s 不在 ⇒ 六把新刀与两张历史表的读数不许手抄" % KNIVES)
for line in rd(KNIVES).splitlines():
    m = re.match(r"TABLE_VERDICTS table=(\S+) arms=(\d+) caught=(\d+) escaped=(\d+) "
                 r"not_run=(\d+) clean=(\w+) rc=(\d+)", line.strip())
    if m:
        tables[m.group(1)] = dict(arms=int(m.group(2)), caught=int(m.group(3)),
                                  escaped=int(m.group(4)), not_run=int(m.group(5)),
                                  clean=m.group(6), rc=int(m.group(7)))
for want in (u"mutate_r308", u"mutate_r300", u"mutate_r45_hover_ring"):
    t = tables.get(want)
    if not t:
        die(u"刀表 %s 没有裁定行 ⇒ 它没跑或日志被截" % want)
    if (t["escaped"] or t["not_run"] or t["clean"] != u"yes"
            or t["rc"] != 0 or t["caught"] != t["arms"] or not t["arms"]):
        die(u"刀表 %s 不干净：%s ⇒ 拒绝出账（ESCAPED/NOT_RUN/非零退出码都要先修）" % (want, t))
ARMS_TOTAL = sum(t["arms"] for t in tables.values())
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", chain)
if not pre_line:
    die(u"预检结论行没读到")
TABLES_N, COVERED, PRE_ARMS, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 腐烂在册，先修针再写账" % PRE_BAD)

dk, _ = sh([sys.executable, CURVE])
gaps = (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1]
if gaps != u"none":
    die(u"曲线尺报 GAPS=%s ⇒ 升序台账被插在中间了" % gaps)
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", dk, re.M) or [u""])[-1]
SCORES_RX = re.compile(r"(\d+)=(\d+)")


def scores_by_round(out):
    """曲线尺自己打印的 `SCORES_BY_ROUND r=分 …` ⇒ 派生分只能从这一行取。

    R308 实测：`re.findall(r"^CURVE_DERIVED=(\d+)", …)` 抓到的是那一长串**轮号**的头一个（110），
    不是任何一轮的分数 —— 我把「仪器打了这一行」当成「仪器给了我要的那个量」，两件事。
    """
    line = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    return dict((int(a), int(b)) for a, b in SCORES_RX.findall(line))


SCORES_PRE = scores_by_round(dk)
DERIVED = SCORES_PRE.get(RDN - 1)
if not SECTIONS or DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分 ⇒ 七维表的数无从派生（%s）"
        % (RDN - 1, dk.strip()[-200:]))

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES["DEC"])
D_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec))
DN = D_MAX + 1
bl = rd(FILES["BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
BLO, BLNEW = BL_MAX, BL_MAX + 1
if u"**356. " not in bl:
    die(u"BACKLOG 356 不在盘上 ⇒ 本轮的结案追记无处可挂")

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
if st_rc != 0:
    die(u"product_streak --streak-for 失败：%s" % st_out.strip()[-200:])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if not STREAK_N:
    die(u"没解析到 streak 的数：%s" % st_out.strip()[-200:])
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
# "此前连续几轮"必须是**上一轮那一格**的读数，不是本轮读数 +1（R300：推导式算术也算手抄）。
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到（rc=%d）：%s" % (prev_rc, prev_out.strip()[-160:]))
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), "latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（ci_read latest 给的是「%s」）" % CI[:80])

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC,
        u"@DN@": DN, u"@BLO@": BLO, u"@BLNEW@": BLNEW,
        u"@ARMS@": ARMS_TOTAL, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N,
        u"@PREVSTREAK@": PREV_STREAK,
        u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND, u"@CI@": CI,
        u"@NPROD@": len(prod), u"@NSWIFT@": len(swift_files),
        u"@FRAMES@": FRAMES, u"@SHOTDIR@": SHOT_DIR,
        u"@CHANGED@": CHANGED, u"@COMPARED@": COMPARED,
        u"@FULLRUN@": FULL_RUN, u"@FULLSKIP@": FULL_SKIP, u"@FULLFAIL@": FULL_FAIL,
        u"@JUDGERUN@": JUDGE_RUN, u"@JUDGEFAIL@": JUDGE_FAIL, u"@FULLPASSES@": FULLPASSES,
        u"@SECTIONS@": SECTIONS, u"@DERIVED@": DERIVED}
EYE = fill_tpl(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SHORT_EYE = EYE.split(u"⇒")[0].strip()
SUBS[u"@EYE_SHORT@"] = SHORT_EYE

# ---------------------------------------------------------------- 七本文本
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：悬停那一圈搬到格子外面 —— 交互不再换数据像素，响度也不再随深浅变（U-@UA@…U-@UC@ · 产品 @NPROD@ 文件，动效主线）

- **U-@UA@：`strokeBorder` 把 1pt 的环画在形状里面 ⇒ 鼠标每划过一格就换掉那一格外圈的数据像素，而三条既有判据对这件事全盲。**
  盲的机制不是"没人想到要判"，是**两条带之间缝掉了一片**：`fillBand` 故意离边一条描边之远（为的是"两档差多少"不被抗锯齿污染），
  `ringBand` 又把那一圈当成"环" —— 于是"整格"这个分母从来没被任何一格用过。本轮新立
  `testHoverLeavesTheDataPixelsUntouched`（分母 = `cellBoxBand` = 完整 cellPx²，同一颗 `meanChannelDelta`），
  现读 20 条全部 **0.000/255**（环搬到留白之后格内一个像素都不动），界压到 1.0；刀 M890 把外推距离归零 ⇒ 它当场红。
- **U-@UB@：同一个动作的响度随数据深浅变 1.73…1.75 倍，而且最响的一臂正是「没有数据」的那一格。**
  旧画法现读（α=0.30，亮档 2x）：empty 41.42 → bucket4 23.65；亮档 1x：32.60 → 18.87 ——
  最安静的臂只比可见性地板 18 高 0.87，也就是**在最忙的格子上那圈几乎看不见，在最空的格子上最响**。
  本轮把环搬到格子外面的留白里（`stroke` + `padding(-hoverRingGap)`，圆角半径跟着外扩以保持同心），
  同一颗尺现读五档在每一外观/尺度上给出同一个数：亮 1x 23.09 / 亮 2x 39.83 / 暗 1x 20.48 / 暗 2x 35.17，
  **档间离散 = 1.000**（新判据 `HEAT_RING_LEVEL_SPREAD` 把界压在 1.05）。
  α 因此从 0.30 降到 **0.20**：窗口是 0.176 ≤ α ≤ 0.236（下界=地板 18，上界=最重的一次数据变化 41.67），取中点。
- **U-@UC@：藏在 lambda 里的 needle 会腐烂而静态预检不响 —— `mutate_r45_hover_ring` 的那根针从 R300 起就是死的。**
  它的针写着 `isHovered ? 0.55 : 0`，而这个数 R300 就改成了 0.30；八轮里没人重跑那张表，
  预检也只报「不在覆盖里」不报 bad。本轮因为又改了同一行才撞见。顺带自曝第二条：
  新写的 halo 分类器第一版把**中心**也外推了一个 gap ⇒ 带整体偏移 2 个设备像素，
  真 halo 被算成带外（`testHoverChangesOnlyTheRingBand` 抓到 (11,5) 变了 65 却不在带里），
  而带里混进没画的像素会把均值稀释 —— 这一族由真值表第④b 格（按行号点验）钉住，刀 M893 打的就是它。

本轮还公开更正一条旧契约：`testAdjacentLevelRulersAreATruthTable` 里「两条带加起来要几乎等于整格」
在环搬到外面之后不成立（那说的是 strokeBorder 时代的互补分格）。换成的不是更弱的判据，
是两条各自更强的等式：整格带必须恰好 cellPx²，且描边带与整格**严格不相交**。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：悬停那一圈搬到格子外面 —— 交互不再换数据像素

做了什么：把热图格子的悬停反馈从「压在格子边上的描边」改成「格子外留白里的一圈 halo」
（产品 2 文件：`VisualTokens` 新令牌 `hoverRingGap` + 透明度 0.30→0.20，`DailyCopyHeatmapView` 改画法），
新立三条判据（整格不许被动 / 档间离散 / halo 分类器按行号点验 + 同心），
公开更正一条旧契约，六把刀 M889…M894 各钉一条轴，并重跑两张被本轮改动弄坏的历史刀表（r300 重钉针、r45 重钉画法与正文）。

读数（全部现读，同一遍验证链）：构建告警 0；判据卷 HeatmapHoverEvidenceTests `Executed @JUDGERUN@ tests, with @JUDGEFAIL@ failures`（全绿，证人 `/tmp/r308_full2.log`）；
全量卷 `Executed @FULLRUN@ tests, with @FULLSKIP@ skipped and @FULLFAIL@ failures`（@FULLPASSES@）；
重捕帧 `CAPTURED @FRAMES@ -> @SHOTDIR@`，与工作基线对账 `COMPARED=@COMPARED@ CHANGED=@CHANGED@`
（改的正是 `heatmap-cell-strip-hover-{light,dark}` 那两张，其余 @COMPARED@ 张没动 ⇒ 改动面与预期一致）；
帧基线在同一笔里 update；换装本机 `INSTALL_RESULT=ok`；
刀：本轮 @ARMS@ 把（含两张历史表）全 CAUGHT、RESTORE_CLEAN=yes、预检 tables=@TABLES@ covered=@COVERED@ arms=@ARMS@ bad=0；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；产品面连续零改动 = **@STREAK@** 轮
（代码半那一笔 @LASTSHA@ 之后归零；此前连续 @PREVSTREAK@ 轮 0 产品文件，取数口 `scripts/product_streak.py`）。

看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 11/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 13/15 |
| 产品面推进 | 11/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 13/15 |
| 合计 | 89/105 |

为什么不是满分（逐条）：真实视觉审查 11 —— 真看了那两张改动帧并据此把圆角改成同心（半径跟着外扩），
但没有真机眼，347 仍欠；判据有效性 14 —— 新立三条里有两条是"第一次有人量这块地方"（整格、档间离散），
扣分在离散那格的 1.05 余量只有我自己一遍读数支持；假绿防御 13 —— 六把刀各钉一条轴、
分类器自己的中心错被真值表钉住，但 r45 那根腐烂的针是**我改到同一行才撞见的**，不是被仪器抓到的（新开 @BLNEW@）；
产品面推进 11 —— 连续 @PREVSTREAK@ 轮之后第一次动产品，2 文件 + 帧基线同一笔 + 换装本机，
但 356 只走完一半：「比最细一档还安静」在暗档仍装不下（地板 18 > 暗档最细一步 17.33），
且剩下的离散来自 1x/2x 的抗锯齿（1.7 倍）而不是数据；台账一致性 13 —— 七本一支脚本、编号现取、
两张历史表重跑、报告计数器同步；交付诚实性 14 —— 公开更正写进注释而不是抹掉旧契约，
两次自伤（带中心算错、期望正文抄旧数）都留在账上；可复核性 13 —— 判据卷与刀表都能重跑，
但 halo 的同心那格只在 2x 上被点验（1x 的角在 11pt 格上只有 1 个像素，点不出更细的形状）。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 356 的剩下那一半（暗档最细一步 vs 地板 18；换通道那条候选仍欠产物证人）；
② 347 / 305（真机眼，等用户退出 App）；③ 360 的最后一批（11 份裸 stdout）；④ 361 的合并；
⑤ 359 汇聚点；⑥ 348 的「数字对不对」；⑦ 新开的 @BLNEW@（隐藏 needle 的腐烂检测）；
⑧ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""**D-@DN@（@RTAG@）：尺子的带必须跟着被测物走；被测物搬家之后，分子与分母不许再共用同一条带。**

`strokeBorder` 时代，"那一圈"与"数据"是同一片像素，所以 `testHoverIsNotLouderThanTheDataRange`
的分子分母共用 `ringBand` 是合法的。环搬到留白之后，同一条带上 empty 与 bucket4 一模一样
⇒ 分母恒为 0，那条判据自己红成"没在量东西"（这正是它该有的行为：红在尺子上，而不是悄悄放行）。
规矩两条：① **带是被测物画出来的那一圈的定义**，产品换画法必须同时换带，反过来（为了旧带不改而
不让产品换）就是把尺子当契约；② 分子分母分带之后，必须有一格判据钉住"两根带严格不相交"，
否则"交互响不响"与"数据分不分得开"会再次互相渗透。公开更正要在注释里留下被换掉的旧等式与新等式，
不许只留结论（读者需要知道当年为什么那么写）。
"""

NOTE_356 = u"""  追记（@RTAG@ 换形状落地一半）：三条候选里选了"换画法"而不是"换档数/换格子尺寸"——
  量出来的理由是：环的档间离散（1.73…1.75 倍）全部来自它**压在数据像素上**，
  把环搬到格子外面的留白里，离散直接归到 1.000（现读五档同一数），α 的可用窗口从"空集"变成
  0.176 ≤ α ≤ 0.236（于是取 0.20）。剩下那一半仍开，而且现在能说清是什么：
  「环 ≤ 最细一档」要求暗档最细一步 ≥ 可见性地板 18，而它是 17.33（均值通道）——
  两头差 0.67/255；而 1x 与 2x 之间还剩 1.7 倍的抗锯齿离散，两界夹出来的窗口要同时装下它俩。
  下一轮别再拿"减档数"当解药：那一条只放大均值通道上的步长，而暗档那一步的**可感知**差在色相/最大通道上
  （R198 已量：暗档模拟后保住 97–98%），拿它换安静等于用信息换口味。
"""

BL_NEW = u"""**@BLNEW@. 藏在 lambda 里的 needle 会腐烂，而静态预检只报「不在覆盖里」不报 bad（@RTAG@ 现读一例，八轮没响）**：
`mutate_r45_hover_ring` 的针写着 `isHovered ? 0.55 : 0`，那个数 R300 就改成了 0.30、@RTAG@ 又改成 0.20 ——
八轮里这张表一次没重跑，预检对它只打印「needle 藏在 lambda 里 ⇒ 不在覆盖里」，`bad` 仍然是 0。
也就是说"覆盖不全"与"内容腐烂"在现有仪器下同形。做法两条，代价差别很大：
① 让每张表自己**在导入时**数一遍 needle 命中（命中≠1 就打 `NEEDLE_DEAD` 并以退出码 1 结束，
不跑任何臂）—— 预检脚本再把这些表逐支 import 一次，隐藏针就变成会响的；
② 或者把 needle 从 lambda 里提出来做成模块级常量（静态可抽，但每张历史表都要改，改动面大且会碰到
D-284 那条"重跑历史表"的义务）。倾向 ①：它只加一层自证，不动任何一把既有刀的形状。
"""

CH_NEW = u"""### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 热图悬停那一圈搬到格子外面：交互不再换数据像素）

`DailyCopyHeatmapCell` 的悬停反馈从 `strokeBorder`（画在形状里面，会盖掉那一格外圈的数据像素，
且响度随深浅变 1.73…1.75 倍、最响处正是空格）改成 `stroke` + `padding(-VisualHeat.hoverRingGap)`
的同心 halo：圆角半径跟着外扩，环整个落在 3pt 格间距里，一格数据像素都不动。
新令牌 `hoverRingGap = 1`；环的透明度 0.30 → **0.20**（档间离散归一之后两条界第一次同时可满足，
窗口 0.176…0.236 取中点）。判据侧新立三条（整格均值差 ≤1.0 现读 0.000 / `HEAT_RING_LEVEL_SPREAD` ≤1.05 现读 1.000 /
halo 分类器按行号点验 + 同心），公开更正一条旧等式（两条带不再互补分格 ⇒ 换成"整格恰好 cellPx² 且与环带不相交"），
并把"交互不许比一次真实数据变化响"的分子分母分成两条带。六把刀 M889…M894 各钉一条轴，
历史表 r300 重钉针、r45 重钉画法与正文后全 CAUGHT；预检 bad=0；判据卷 `Executed @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 `Executed @FULLRUN@ tests, with @FULLSKIP@ skipped and @FULLFAIL@ failures`（@FULLPASSES@）；
重捕 @FRAMES@ 帧、`COMPARED=@COMPARED@ CHANGED=@CHANGED@` 且改的正是那两张 hover 帧，基线同一笔 update；换装本机 ok。
看图腿 RUN：@EYE_SHORT@

"""

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：@CI@
上一轮登记要验的那格**已交账**：两跑（5225196 ↔ 39846928354、de370bf ↔ 39847851743，都 success）
都在 STEP「Motion coverage floor」打出 `MOTION_FLOOR_SUITE_NOT_SEEN=2` ⇒ 354 第四步的"缺席会被点名"
在 runner 上成立，不再只是本机夹具里响。同一格还顺带给出 `MOTION_FLOOR_OK=3/4 → 4/4`
（第一跑 not-run=notice-banner，第二跑判到了 ⇒ 那一臂是采样漂，不是掉臂）。
@RNEXT@ 开场要验的两件事：① 本轮这两笔 push 之后，runner 上 `HEAT_RING_LEVEL_SPREAD` 与
`HEAT_DATA_UNTOUCHED` 那两族读数是否仍在文件通道里落得下来（新通道名要进 `READINGS_ROSTER` 的派生名册）；
② 1x 臂在 runner 上的 halo 均值（本机 23.09 / 20.48）会不会因机器不同而贴地板 —— 若那边红在
`testHoverRingIsVisibleOnEveryHeatLevelAndBothScales`，先查机器再谈判据（R38/D-251 那一课）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**回到产品面 —— 悬停那一圈搬到格子外面**（产品 @NPROD@ 文件）
连续 @PREVSTREAK@ 轮 0 产品文件之后第一次动 `Sources/`：`strokeBorder` 会换掉那一格外圈的数据像素、
且响度随档位变 1.73…1.75 倍（最响处正是没有数据的空格）。改成留白里的同心 halo 之后
现读整格均值差 0.000（新判据钉住）、档间离散 1.000（新判据 ≤1.05），α 0.30→0.20。
D-@DN@ 定"尺子的带必须跟着被测物走；分带之后要有一格钉住两带不相交"。
现读：构建告警 0；判据卷 `Executed @JUDGERUN@ / @JUDGEFAIL@ 失败`；全量卷 `Executed @FULLRUN@ / @FULLSKIP@ skip / @FULLFAIL@ 失败`（@FULLPASSES@）；帧 `CAPTURED @FRAMES@`、
`COMPARED=@COMPARED@ CHANGED=@CHANGED@`（正是那两张 hover 帧）+ 基线同一笔 update；换装 ok；
刀 @ARMS@ 把全 CAUGHT（含历史表 r300 / r45 重钉后重跑）、预检 tables=@TABLES@ bad=0；
电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；看图腿 RUN（@EYE_SHORT@）。
产品文件 @NPROD@ 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；此前是 @PREVSTREAK@ 轮，本轮代码半那一笔把它归零）。
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。

① 下一轮（@RNEXT@）的靶：① 347 / 305 的真机眼（要用户退出 App，或回答「收藏星按下够不够明显」）——
   这是产品面唯一一条我自己走不完的腿；② 356 的剩下那一半（暗档最细一步 17.33 vs 地板 18，
   以及 1x/2x 的 1.7 倍抗锯齿离散）—— 先量"换通道"那一候选还有没有产物证人，别再拿减档数当解药；
   ③ 新开的 @BLNEW@：让每张刀表在导入时自数 needle，隐藏针的腐烂必须会响；
   ④ 360 的最后一批（11 份裸 stdout 清零）；⑤ 361 的合并。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**（暗档最细一步 vs 地板）、
354 的第五步（sampled 的退场阈值）、360（剩 11 行裸 stdout）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、@BLNEW@（隐藏 needle 的腐烂检测）、
348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

# ---------------------------------------------------------------- 组装
orig = {k: rd(p) for k, p in FILES.items()}
texts = {k: fill_tpl(v, SUBS) for k, v in
         {"UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW, "N356": NOTE_356,
          "BLNEW": BL_NEW, "CH": CH_NEW, "ST": STATE_NEW}.items()}
for k, t in texts.items():
    hit = re.findall(u"@([A-Z][A-Z0-9_]{1,24})@", t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig["UI"])]
top = max(heads)[1]
new_ui = orig["UI"][:top] + texts["UI"] + orig["UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts["UI"])]
if nums != [UA, UB, UC]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC]))

new_it = orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].rstrip(u"\n") + u"\n"
rows = re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts["IT"])
if len(rows) != 7:
    die(u"七维表只有 %d 行 ⇒ 曲线仪器会拒绝推导" % len(rows))

new_dec = orig["DEC"].rstrip(u"\n") + u"\n\n" + texts["DEC"].rstrip(u"\n") + u"\n"
new_bl = append_note = None
bl_lines = orig["BL"].split(u"\n")
head = [i for i, l in enumerate(bl_lines) if l.startswith(u"**356. ")]
if len(head) != 1:
    die(u"356 的条目头命中 %d 行 ⇒ 追记无处可挂" % len(head))
later = [i for i in range(head[0] + 1, len(bl_lines)) if re.match(u"\\*\\*\\d{3}\\. ", bl_lines[i])]
k = later[0] if later else len(bl_lines)
while bl_lines[k - 1].strip() == u"":
    k -= 1
new_bl = (u"\n".join(bl_lines[:k]).rstrip(u"\n") + u"\n" + texts["N356"].rstrip(u"\n")
          + u"\n\n" + texts["BLNEW"].rstrip(u"\n") + u"\n" + u"\n".join(bl_lines[k:]).lstrip(u"\n"))
i356 = new_bl.find(u"**356. ")
i356note = new_bl.find(u"换形状落地一半")
iNew = new_bl.find(u"**%d. " % BLNEW)
if not (0 <= i356 < i356note < iNew):
    die(u"356 的追记落在别人那一节里（%d/%d/%d）" % (i356, i356note, iNew))

new_ch = once(orig["CH"], u"## [Unreleased]\n\n",
              u"## [Unreleased]\n\n" + texts["CH"], u"CHANGELOG [Unreleased]")


def heading_lines(text, title):
    # 按**整行相等**数，不按子串：CHANGELOG 第 1917 行的正文里用反引号转述过这个标题
    # （它讲的正是"当年多出一行标题"的事故）⇒ 子串计数天然是 2，这道门会红在一张没写错的账上。
    return sum(1 for line in text.split(u"\n") if line.strip() == title)


if heading_lines(new_ch, u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 标题行不再是恰好 1 行（现读 %d）"
        % heading_lines(new_ch, u"## [Unreleased]"))

new_st = once(orig["ST"], u"## %s 状态（" % PREV_TAG,
              texts["ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig["FR"]
# §1 的 U 那一格：闸门 LAG_U=3 ⇒ 每轮现读抬
before_u = len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr))
if before_u != 1:
    die(u"§1 的 U 那一格锚点命中 %d 次（要恰好 1）" % before_u)
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
if u"U-31 … U-%d（%s 现读抬" % (UC, R_TAG) not in fr:
    die(u"§1 的 U 上界没抬到 U-%d" % UC)
# §13 的 356 那一格与仍开名单
# §13 里 356 那一格：锚点必须避开同形干扰 —— 报告里还有一句 `M356（...）`（刀号），
# 裸子串会把两个都数进去 ⇒ 前面不许贴字母/数字/连字符（那正好排掉 M356 与 U-356 两种形状）。
RX356 = u"(?<![A-Za-z0-9-])356（[^）]*）"
b356 = len(re.findall(RX356, fr))
if b356 != 1:
    die(u"§13 里 356 那一格命中 %d 次（要恰好 1）" % b356)
fr = re.sub(RX356,
            u"356 的那一半（暗档最细一步 17.33 低于可见性地板 18；R308 已把环搬到格子外面，"
            u"档间离散 1.75→1.000，α 0.30→0.20）", fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")
if u"%s 节 ②" % R_TAG not in fr:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节")
fr = once(fr, u"347、305、354（runner 单跑红的分布读数）、",
          u"347、305、%d（隐藏 needle 的腐烂检测）、354（runner 单跑红的分布读数）、" % BLNEW,
          u"§13 仍开名单补新单")

new = {"UI": new_ui, "IT": new_it, "DEC": new_dec, "BL": new_bl,
       "CH": new_ch, "ST": new_st, "FR": fr}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)

STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
stray = [u"%s:%d %s" % (k, n, hit.group(0))
         for k, t in new.items() for n, line in enumerate(t.split(u"\n"), 1)
         for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))

for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)

import atexit


def _crash_guard():
    """崩在 die() 之外（本轮实测：报告那三格的 `%d` 拿到字符串 ⇒ TypeError 直接逃出去，
    七本留在半套状态里）也必须还原 —— `die` 只覆盖"我预期到的坏"，atexit 覆盖"我没想到的那种"。
    """
    if WROTE and not OK_EXIT:
        restore()
        sys.stderr.write(u"R308_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)


def restore():
    """写盘之后任何一格不对 ⇒ **七本整体还原**再退出。

    R308 实测的自伤：上一版只还原「电池计数变了」与「353 的门」两朵，其余 die() 都是
    写着半套账退出工作树的 ⇒ 我花了一整步才把六本手动 checkout 回来。
    """
    for key, text in orig.items():
        wr(FILES[key], text)


def refresh_report_after_write():
    """报告的标题格与 §13 三格**只能在六本落地之后**由仪器刷新。

    顺序是承重的（R308 实测）：那几格对的是 ITERATION 的尾轮 / 节数 / 末四个派生分，
    而把尾轮抬上去的正是这一次运行 ⇒ 写盘前跑仪器拿到的必然是旧数（上一版就红在
    「标题写到 R303 而最新一节是 Round 305」与「304=81 而仪器给 304=77」两格上）。
    """
    txt = rd(FILES["FR"])
    out, crc = sh([sys.executable, CURVE])
    if crc != 0 and u"GAPS=" not in out:
        die(u"曲线尺在写盘之后跑挂了（rc=%d）⇒ 报告那几格没有仪器可抄" % crc)
    rounds = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
    last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
    tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    if not rounds or not last_round or not tail:
        die(u"曲线尺没打出 ROUNDS= / rounds=9..N / SCORES_BY_ROUND ⇒ 报告不许按记忆刷（%s）"
            % u" / ".join(x for x in (rounds, last_round, tail) if not x))
    lines = txt.split(u"\n")
    head = lines[0]
    m = re.search(u"R9–R(\\d+)，(\\d+) 轮自评", head)
    if not m or head.count(u"R9–R") != 1:
        die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 轮自评`（或命中多于一处）⇒ 不敢整行改写")
    lines[0] = head[:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds) + head[m.end():]
    body = u"\n".join(lines)

    prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 %s 个（`Sources/…/"
                 u"VisualTokens.swift` + `Views/DailyCopyHeatmapView.swift`）、Swift %s 份，"
                 u"产品面连续零改动轮数 = **%s**（唯一取数口 `python3 scripts/product_streak.py "
                 u"--streak-for %s`，as-of 第 %s 轮的最后一笔产品提交是 %s = 第 %s 轮；"
                 u"此前连续 %s 轮 0 产品文件 ⇒ 本轮把它归零）。看图腿 RUN："
                 u"`CAPTURED %s -> %s` 的 %s 张帧都在盘上，本轮看的就是改动的那两张 "
                 u"（`heatmap-cell-strip-hover-light`、`heatmap-cell-strip-hover-dark`）"
                 % (len(prod), len(swift_files), STREAK_N, ROUND, ROUND, LASTSHA, LASTROUND,
                    PREV_STREAK, FRAMES, SHOT_DIR, FRAMES))
    scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
                  u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
                  u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**。"
                  u"本轮新落的读数现抄：`%s` 与 `%s`（证人 `/tmp/r308_full2.log`）"
                  % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD,
                     U_DEF_LINES, UC, DN, BLNEW, DATA_LINE, SPREAD_LINE))
    where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
                  u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
                  u"⇒ 按目标继续修，不收口。" % (rounds, last_round, tail))
    for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                        (u"判据与门的规模", scale_cell),
                        (u"走到哪了", where_cell)):
        parts = body.split(u"\n")
        hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
        if len(hits) != 1:
            die(u"§13 的「%s」那一格命中 %d 行（要恰好 1）⇒ 不许把三格并成两格或改了历史节"
                % (label, len(hits)))
        parts[hits[0]] = cell
        body = u"\n".join(parts)
    # 「最后一次动到 `Sources/` 的轮次」那一格是**纯手抄、没有 LAG 容差** ⇒ 只能逐字对 git。
    # R308 实测：写盘后电池就红在这一格还写着 R300/`6ac317f`（本轮的 9eb266e 没登记），
    # 并且级联弄红 `test_skip_roster`（它跑的内层那一跑因为这一朵红而没有结论行）——
    # 与 R307 那三格计数器同一族：动了源码却没刷报告格，报告替不动源码的那一笔作证。
    gout, grc = sh(["git", "log", "-40", "--format=%h\x1f%s", "--",
                    os.path.join("ClipboardHistory", "Sources")])
    if grc != 0:
        die(u"取「最近动过 Sources/ 的提交」失败（rc=%d）：%s" % (grc, gout.strip()[-160:]))
    src_rows = []
    for line in gout.splitlines():
        if u"\x1f" not in line:
            continue
        sha_, subj_ = line.split(u"\x1f", 1)
        mb = re.match(u"^R(\\d+)", subj_.strip())
        src_rows.append((sha_.strip(), int(mb.group(1)) if mb else None, subj_.strip()))
    picked = [r for r in src_rows if r[1] is not None and r[1] <= int(R_TAG[1:])]
    if not picked:
        die(u"标签 ≤ %s 的源码提交一笔都没有 ⇒ as-of 口径没有分界，那一格不许拿" % R_TAG
            + u"「此刻最新」凑数")
    live_sha, live_src_round, _ = picked[0]
    older = [r for r in src_rows if r[0] != live_sha and r[1] is not None]
    prev_txt = (u"上一笔动 `Sources/` 的是 R%d（`%s`）。" % (older[0][1], older[0][0])) if older else u""
    src_cell = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— 现读 %d 个 "
                u"`Sources/` 文件（%s）；改了什么以 `AGENT_UI_AUDIT.md` 里 %s 那一节为准"
                u"（这一格只登记号与数，不复述结论）。%s|"
                % (live_src_round, live_sha, len(prod),
                   u"、".join(os.path.basename(p) for p in prod), R_TAG, prev_txt))
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts)
            if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
    if len(hits) != 1:
        die(u"报告的「最后一次动到 Sources/」那一格命中 %d 行（要恰好 1）" % len(hits))
    parts[hits[0]] = src_cell
    body = u"\n".join(parts)

    if STRAY_RX.search(body):
        die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
    wr(FILES["FR"], body)
    return rounds, last_round, tail


# §13 的那三格 + 标题行：全部由写完账之后的仪器刷新（见函数注释里那条顺序）。
U_DEF_LINES = len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new["UI"]))
arm_total = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", chain)
if not arm_total:
    die(u"刀名册结论行 ARM_TOTAL 没读到 ⇒ 在册刀数不许手抄")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in arm_total[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"刀名册自己报 dupes=%d repeats=%d ⇒ 先修跨表撞号再写账" % (ARM_DUPES, ARM_REPEATS))
DATA_LINE = (sh([u"grep", u"-a", u"-m", u"1", u"HEAT_DATA_UNTOUCHED", WIT])[0].strip()
             if os.path.exists(WIT) else u"")
SPREAD_LINE = (sh([u"grep", u"-a", u"-m", u"1", u"HEAT_RING_LEVEL_SPREAD", WIT])[0].strip()
               if os.path.exists(WIT) else u"")
for lbl, ln in ((u"HEAT_DATA_UNTOUCHED", DATA_LINE), (u"HEAT_RING_LEVEL_SPREAD", SPREAD_LINE)):
    if not ln:
        die(u"证人日志里没有 %s 那一行 ⇒ 报告那格不许写成" % lbl + u"「本轮新落的读数」")
ROUNDS_AFTER, LAST_ROUND_AFTER, TAIL_AFTER = refresh_report_after_write()
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r308_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口 ⇒ 升序台账被插在中间")
DERIVED2 = scores_by_round(cv2).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分 ⇒ 七维表那一格没被仪器接上" % RDN)
fr_after = rd(FILES["FR"])
if u"R9–R%s" % LAST_ROUND_AFTER not in fr_after.split(u"\n")[0]:
    die(u"报告标题没接上写盘后的尾轮 Round %s ⇒ 那一格又被刷回旧的" % LAST_ROUND_AFTER)
if u"U-31 … U-%d" % UC not in fr_after:
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)
for lbl in (u"产品面（这一节最该被读的部分）", u"判据与门的规模", u"走到哪了"):
    if sum(1 for l in fr_after.split(u"\n") if l.startswith(u"- **%s**：" % lbl)) != 1:
        die(u"报告 §13 的「%s」那一格刷新后不再是恰好 1 行" % lbl)
if u"Streak %s" % STREAK_N not in fr_after and u"轮数 = **%s**" % STREAK_N not in fr_after:
    die(u"报告的产品面那一格没接上现读 streak=%s" % STREAK_N)

OK_EXIT.append(True)
print(u"LEDGERS_R308 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(此前 " + PREV_STREAK + u") prod=" + s(len(prod)) + u" swift=" + s(len(swift_files))
      + u" arms=" + s(ARMS_TOTAL) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表"
      + u" U=" + s(UA) + u".." + s(UC) + u" U行=" + s(U_DEF_LINES) + u" D=" + s(DN)
      + u" BL=" + s(BLNEW) + u" frames=" + FRAMES + u" changed=" + CHANGED
      + u"/" + COMPARED + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(LAST_ROUND_AFTER) + u" 节数=" + s(ROUNDS_AFTER)
      + u" 全量卷=" + s(FULL_RUN) + u"/" + s(FULL_SKIP) + u"skip/" + s(FULL_FAIL) + u"失败"
      + u" 判据卷=" + s(JUDGE_RUN) + u"/" + s(JUDGE_FAIL) + u"失败")
