# -*- coding: utf-8 -*-
"""R309 的七本台账（第 308 轮 / Round 306 · 台账的读数口搬进仓库：按小节取数 + 恒等式闸门）。

事务性：任何一格读不到或不干净 ⇒ 在写任何盘之前退出；写盘之后崩在任何地方 ⇒ 七本整体还原
（R308 实测：`%d` 拿到字符串那种未捕获异常会绕过 die()，所以 atexit 也挂了一道）。
数一律现读：git 的改动面从代码半那一笔取、刀表结论行、预检、判据卷、曲线尺、product_streak、
电池（写盘前后同数）、CI 配对。本轮是**判据轮**：Swift 侧三条腿（全量卷 / 重捕帧 / 换装）
按实写明 NOT-RUN 与理由，不许省略，也不许拿上一轮的读数替本轮签字。
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
READINGS = os.path.join(ROOT, "scripts", "ledger_readings.py")
CHAIN = "/tmp/r309_chain.log"
KNIFE_LOG = "/tmp/r309_knives2.log"
WIT = "/tmp/r308_chain.log"
R_TAG, PREV_TAG, R_NEXT = u"R309", u"R308", u"R310"
PREV_ROUND, ROUND, RDN = 307, 308, 306
TODAY = u"2026-10-23"
EYE = os.environ.get("R309_EYE", u"")

WROTE = []
OK_EXIT = []


def die(msg):
    if WROTE:
        restore()
        msg = msg + u"（七本已整体还原）"
    sys.stderr.write(u"R309_LEDGERS_REFUSE " + msg + u"\n")
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
    die(u"看图腿没传 R309_EYE ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读区
pre, pre_skip = battery(u"写盘前", u"/tmp/r309_battery_pre.log")

head_sub, _ = sh(["git", "log", "-1", "--format=%s"])
if R_TAG not in head_sub and u"R309" not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 代码半还没提交，账不许先落（%s）" % (R_TAG, head_sub.strip()[:80]))
# 改动面 = **本轮所有已提交的笔**的并集（R309 的代码半是两笔：仪器 + 它自己的 --help 修复），
# 只读 HEAD 那一笔会把上一笔的文件漏掉 —— 那正是"改动面与账对不上"的一种新形状。
books = set(os.path.relpath(v, ROOT) for v in FILES.values())
log_out, _ = sh(["git", "log", "-12", "--format=%H%x1f%s"])
prod, swift_files, others, surface_commits = [], [], [], []
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if R_TAG not in subj_:
        continue
    surface_commits.append((sha_[:7], subj_.strip()[:40]))
    names, _ = sh(["git", "show", "--name-only", "--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if not line or line in books:
            continue
        if line.startswith("ClipboardHistory/Sources/"):
            prod.append(line)
        elif line.startswith("ClipboardHistory/"):
            swift_files.append(line)
        else:
            others.append(line)
others = sorted(set(others))
if prod or swift_files:
    die(u"本轮按判据轮出账，改动面里却有 %d 个产品 / %d 个 Swift 文件 ⇒ 得按产品轮重跑 Swift 三条腿"
        % (len(prod), len(swift_files)))
if len(others) < 4 or not all(o.startswith(("scripts/", ".scratch/")) for o in others):
    die(u"改动面应当全是 scripts / .scratch 下的文件（≥4 个），现读：%s" % u", ".join(others))

chain = rd(CHAIN) if os.path.exists(CHAIN) else u""
for needle, label in ((u"### PRECHECK", u"预检"), (u"### BUILD", u"构建"),
                      (u"### READINGS_INSTRUMENT", u"新仪器跑真日志"),
                      (u"### FRAMES", u"帧目录在盘上的计数"),
                      (u"### SWIFT_LEGS", u"Swift 三条腿的 NOT-RUN")):
    if needle not in chain:
        die(u"验证链日志里没有「%s」那一节 ⇒ 那条腿没跑完或没写清，不许进账" % label)
warn = re.findall(r"WARNINGS=(\d+)", chain)
if not warn or warn[-1] != u"0":
    die(u"构建告警不是 0（现读 %s）" % (warn[-1] if warn else u"没解析到"))
FRAMES = (re.findall(r"FRAMES_ON_DISK=(\d+)", chain) or [u""])[-1]
if not FRAMES:
    die(u"没读到帧目录在盘上的张数 ⇒ 看图腿不许凭记忆说「上一轮的帧还在」")
RD_LINE = (re.findall(r"(?m)^LEDGER_READINGS 小节前缀=.+$", chain) or [u""])[-1]
if not RD_LINE:
    die(u"新仪器跑真日志那一行没读到 ⇒ 本轮的证据腿没落地")
for leg in (u"FULL_SUITE=NOT-RUN", u"CAPTURE=NOT-RUN", u"INSTALL=NOT-RUN"):
    if leg not in chain:
        die(u"Swift 那条腿（%s）没在日志里写明 NOT-RUN ⇒ 台账不许省略没跑的腿" % leg)

knife = rd(KNIFE_LOG) if os.path.exists(KNIFE_LOG) else u""
km = re.search(r"R309_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
               knife)
if not km:
    die(u"刀表结论行没解析到 ⇒ 六把刀的读数不许手抄")
K_N, K_CAUGHT, K_ESC, K_NOTRUN, K_CLEAN = (int(km.group(1)), int(km.group(2)),
                                          int(km.group(3)), int(km.group(4)), km.group(5))
if (K_CAUGHT != K_N or K_ESC or K_NOTRUN or K_CLEAN != u"yes"):
    die(u"刀表不干净：刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d CLEAN=%s ⇒ 先修再写账"
        % (K_N, K_CAUGHT, K_ESC, K_NOTRUN, K_CLEAN))
base = re.search(r"R309_MUTATE BASELINE 跑=(\d+) 失败=(\d+) exit=(\d+)", knife)
if not base or base.group(2) != u"0" or base.group(3) != u"0":
    die(u"刀表没有「未落刀先绿」那一行 ⇒ 后面每一朵 CAUGHT 都不说明任何事")
JUDGE_BASE = base.group(1)

pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", chain)
if not pre_line:
    die(u"预检结论行没读到")
TABLES_N, COVERED, PRE_ARMS, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 腐烂在册，先修针再写账" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", chain)
if not reg_line:
    die(u"刀名册结论行 ARM_TOTAL 没读到 ⇒ 在册刀数不许手抄")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"刀名册自己报 dupes=%d repeats=%d ⇒ 先修跨表撞号再写账" % (ARM_DUPES, ARM_REPEATS))
roster = re.findall(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)",
                    chain)
HID_TABLES, HID_ARMS = (int(roster[-1][1]), int(roster[-1][2])) if roster else (0, 0)

ju, jurc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "-v",
               "scripts.tests.test_ledger_readings"])
JUDGE_RUN = (re.findall(r"^Ran (\d+) tests", ju, re.M) or [u""])[-1]
JUDGE_OK = bool(re.search(r"^OK", ju, re.M))
if jurc != 0 or not JUDGE_RUN or not JUDGE_OK:
    die(u"判据卷不绿（rc=%d 跑=%s）⇒ 拒绝出账" % (jurc, JUDGE_RUN or u"没解析到"))
if JUDGE_RUN != JUDGE_BASE:
    die(u"判据卷的格数与刀表基线那一跑不符（%s vs %s）⇒ 两半不是同一颗尺" % (JUDGE_RUN, JUDGE_BASE))

dk, _ = sh([sys.executable, CURVE])
gaps = (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1]
if gaps != u"none":
    die(u"曲线尺报 GAPS=%s ⇒ 升序台账被插在中间了" % gaps)
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", dk, re.M) or [u""])[-1]
SCORES_RX = re.compile(r"(\d+)=(\d+)")


def scores_by_round(out):
    """派生分只能从仪器自己打印的 `SCORES_BY_ROUND r=分` 那一行取。"""
    line = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    return dict((int(a), int(b)) for a, b in SCORES_RX.findall(line))


DERIVED = scores_by_round(dk).get(RDN - 1)
if not SECTIONS or DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分 ⇒ 七维表的数无从派生" % (RDN - 1))

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
if st_rc != 0:
    die(u"product_streak --streak-for 失败：%s" % st_out.strip()[-200:])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if not STREAK_N:
    die(u"没解析到 streak 的数：%s" % st_out.strip()[-200:])
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到（rc=%d）" % prev_rc)
if STREAK_N != PREV_STREAK + u"" and int(STREAK_N) != int(PREV_STREAK) + 1:
    die(u"本轮 streak=%s 与上一轮 streak=%s 的关系不是 +1 ⇒ 本轮没动产品，这一格应当 +1"
        % (STREAK_N, PREV_STREAK))
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), "latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（ci_read latest 给的是「%s」）" % CI[:80])

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES["DEC"])
D_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec))
DN = D_MAX + 1
bl = rd(FILES["BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
for want in (u"**348. ", u"**364. "):
    if want not in bl:
        die(u"BACKLOG 条目 %s 不在盘上 ⇒ 本轮的追记无处可挂" % want.strip("* "))

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC,
        u"@DN@": DN, u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N,
        u"@PREVSTREAK@": PREV_STREAK, u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND,
        u"@CI@": CI, u"@NOFILES@": len(others), u"@K_N@": K_N, u"@JUDGERUN@": JUDGE_RUN,
        u"@JUDGEBASE@": JUDGE_BASE, u"@TABLES@": TABLES_N, u"@COVERED@": COVERED,
        u"@PREARMS@": PRE_ARMS, u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES,
        u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS, u"@FRAMES@": FRAMES,
        u"@RDLINE@": RD_LINE, u"@BLMAX@": BL_MAX, u"@SECTIONS@": SECTIONS}
EYE = fill_tpl(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

# ---------------------------------------------------------------- 七本文本
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：台账的读数口搬进仓库 —— 按小节取数 + 恒等式闸门（U-@UA@…U-@UC@ · 产品 0 文件，判据轮）

- **U-@UA@：台账生成器取「全量卷」是在整份验证链日志里 `re.findall(...)[-1]` ⇒ 拿到的是 `### CAPTURE 结论行补记` 那一行（捕帧卷 92 格、0 失败），而真读数是 934 / 44 skip / 0。**
  三本账（ITERATION / CHANGELOG / STATE）一度一起写着同一句假话，而当时那道
  「FULL_FAIL != 0 就拒写」的门**完全不响** —— 抄来的那一行恰好是 0 失败。
  这条不是"又抄错一个数"，是给这一族补了一条通用结论：**只在红时响的门，对「抄错但抄到一行绿的」是盲的**
  （R223「取末把内层 suite 当全量总数」同族第二次）。修法不是把那一格改对，而是把它收成仓库里的尺：
  `scripts/ledger_readings.py` 三条都会红 —— ① 按 `### 小节` 切片取数；② 恒等式闸门
  「全量卷不可能比同一份日志里任何一卷小」；③ 多跑日志每一跑各自记账，早先那跑的红不许被最后一跑抹掉。
  判据卷 `scripts/tests/test_ledger_readings.py` 现读 `Ran @JUDGERUN@ tests / OK`，刀 M895…M900 各钉一条轴。

- **U-@UB@：`re.split` 只吃掉分隔符 ⇒ 小节标题与它的正文住在**同一个块**里；切片时"取下一块"拿到的是下一节的第一行。**
  本轮写这一支时又踩了一次（`section_bodies` 把 FULL SUITE 的正文读成 INSTALL / CAPTURE 那节），
  而**这次不是靠人眼发现的**：新写的恒等式闸门当场 REFUSED，七本一个字节都没落盘。
  落地的形状是 `section_parts()` 返回 (标题, 正文) 成对，正文取本块去掉首行；
  刀 M896 把正文换成空 ⇒ `test_the_body_lives_in_the_same_chunk_as_the_heading` 必须红。

- **U-@UC@：多跑日志里「取用最后一跑」与「早先那跑的红原样留档」是两格，缺一格就等于把改动过程藏起来。**
  R308 的真实顺序是第一跑 3 朵红（夹具自己的数据带写错）→ 修 → 第二跑 0；
  台账只写第二跑绿，读者就看不到"本轮改过两次"。现读真日志给的是
  `@RDLINE@`（早先红=1，那一跑的原话另有 `LEDGER_READINGS_EARLIER_RED` 一行）。
  两把刀各钉一侧：M897 改成取第一跑 ⇒ 必须红；M898 把留档那圈抹掉 ⇒ 必须红。

- **本轮的坏法里最该被记住的一条不在产品面，在「写账这件事本身」**：R308 那三本假账是**通过了电池**落不了盘才被抓的，
  而抓它的那道门是本轮才写进仓库的 —— 也就是说 BACKLOG 348「写台账这件事本身没有门」到今天才有尺真身。
  本轮把 348 的「数字对不对」那一格追记成：读数口已是仓库里的纯函数 + 判据卷 + 六把刀；
  仍开的是 364（名册现读 `unregistered_with_arms=@HIDTABLES@ hidden_arms=@HIDARMS@` —— 那些表的 needle 藏在 lambda 里，
  静态预检看不见，要每张表导入时自数一遍才算结）。

读数（全部现读，同一遍验证链 /tmp/r309_chain.log）：构建告警 0（`swift build --build-tests`，本轮零 Swift 改动，仍跑是因为"0 告警"是产品构建的契约不是本轮的装饰）；
判据卷 `Ran @JUDGERUN@ tests / OK`（与刀表基线那一跑同数：`@JUDGEBASE@`）；
刀 M895…M900：本轮 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes、未落刀先绿；
预检 tables=@TABLES@ covered=@COVERED@ arms=@PREARMS@ bad=0，名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
新仪器跑真日志：`@RDLINE@`；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（取数口 `scripts/product_streak.py --streak-for @ROUND@`；上一轮 @PREVSTREAK@）。

Swift 侧三条腿 **NOT-RUN**（本轮 0 产品文件、0 Swift 文件 ⇒ 没有新字节可跑，写清而不是省略）：
全量卷 NOT-RUN（沿用 R308 那一跑的 934 / 44 skip / 0，本轮没有任何 Swift 改动能让它腐烂）；
重捕帧 NOT-RUN（帧目录仍住着 R308 的 @FRAMES@ 张，`FRAMES_ON_DISK` 现读，不是"我记得还在"）；
换装 NOT-RUN（产物未变）。看图腿 RUN：看的就是那 @FRAMES@ 张里 R308 改过的两张（本轮没有新帧）。
看图结论：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 10/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 14/15 |
| 合计 | 89/105 |

为什么不是满分（逐条）：真实视觉审查 10 —— 判据轮没有新帧可看，本轮看的是上一轮改动的那两张，
分数按"这一轮画面证据的贡献"给，不按"我跑了看图这一步"给；判据有效性 14 —— 三条新 U 都是尺真身，
扣分在恒等式闸门只覆盖了 `Executed` 这一族读数（帧数、刀数、§8 格子数还是各自的取法）；
假绿防御 15 —— 六把刀各钉一条轴、基线先绿、回读磁盘、RESTORE_CLEAN，且 M896 第一版是**刀自己坏**
（Swift 的 // 注释写进 python 变异文 ⇒ 语法红 ⇒ NOT_RUN 而不是 CAUGHT），这一课当场兑现了 D-243；
产品面推进 8 —— 本轮 0 产品文件，这是判断不是遗漏：356 剩下那一半要先量"换通道"候选、
347 / 305 要用户的真机眼；台账一致性 14 —— 七本一支脚本、编号现取、报告计数器与 §13 全部由写完账之后的仪器刷；
交付诚实性 14 —— 三条 NOT-RUN 写清理由，R308 那次假账在 348 的追记与本轮标题里都留了原文；
可复核性 14 —— 仪器、判据卷、刀表都能重跑，扣分在真产物那一格依赖 /tmp 日志（不在就 skip，不许拿合成样本替真产物作证）。

"""

IT_NEW = u"""## Round @RDN@ · R309（第 @ROUND@ 轮 · @TODAY@）：台账的读数口搬进仓库 —— 按小节取数 + 恒等式闸门（产品 0 文件，判据轮）

本轮的靶不是画面，是**写账这件事**：R308 落账时三本账一起把「捕帧卷 92 格」当成了全量卷，
而当时唯一的门（失败数非 0 就拒写）对这件事全盲。本轮把它收成 `scripts/ledger_readings.py`：
按 `### 小节` 切片取数、恒等式闸门「全量卷不可能比同一份日志里任何一卷小」、
多跑日志每一跑各自记账（早先那跑的红不许抹）。新判据卷 `Ran @JUDGERUN@ tests / OK`，
刀 M895…M900 全 CAUGHT；写这一支的过程里又踩了 `re.split` 的块形状坑，
**是新闸门当场 REFUSED 而不是人眼发现的**（七本一个字节都没落盘）。

读数：构建告警 0；判据卷 `Ran @JUDGERUN@`；刀 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=@TABLES@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（上一轮 @PREVSTREAK@，取数口 `scripts/product_streak.py`）。
Swift 三条腿 NOT-RUN（全量卷 / 重捕帧 / 换装 —— 本轮 0 Swift 文件，理由逐条写在 §5）；看图腿 RUN（@FRAMES@ 张在盘上）。
看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 10/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 14/15 |
| 合计 | 89/105 |

"""

DEC_NEW = u"""**D-@DN@（R@RTAG@）：台账里的每个读数只能由「被计数物自己打印的那一行」给出，并且必须按它所属的小节归属取；跨小节取末一律算抄错。**

这条是 R308 的假账换来的（现读，不是推想）：生成器在整份验证链日志里 `re.findall(...)[-1]` 取末，
拿到的是 `### CAPTURE 结论行补记` 那一行（捕帧卷 92 格、0 失败），真读数是 934 / 44 skip / 0；
三本账一起写错，而"失败数非 0 就拒写"那道门**完全不响** —— 因为它盯的是失败数，不是**这行属不属于那一卷**。

所以规矩要写成两条，而不是一条：
① 取数口必须**带小节归属**（`scripts/ledger_readings.py:section_parts`），并且
② 必须有一条与失败数无关的恒等式闸门 —— 「全量卷不可能比同一份日志里任何一卷小」。
只写 ① 会退化成"我把这一处改对了"，只写 ② 则下一次换一种读数（帧数、刀数、§8 格子数）照样能抄错。

配套三条不许省：多跑日志**每一跑各自记账**（早先那跑的红原样留档，否则"改动过程"被最后一跑洗白）；
「没解析到」与「解析到 0」必须分开（`LEDGER_READINGS_SKIP_MISSING`）；
新尺必须有真产物对照，而真产物不在盘上时**算 skip 不算通过**（不许拿合成样本替真产物作证）。
"""

BL_348 = u"""  追记（R309）：这一格今天有了**仓库里的尺真身** —— `scripts/ledger_readings.py`
  （按 `### 小节` 切片取数 + 恒等式闸门「全量卷不可能比同一份日志里任何一卷小」+ 多跑每一跑各自记账），
  判据卷 `scripts/tests/test_ledger_readings.py` 现读 `Ran @JUDGERUN@ tests / OK`，刀 M895…M900 六把各钉一条轴全 CAUGHT。
  上面那条 R308 追记里写的「仍欠的一把刀」今天补上了：M895 摘掉闸门 ⇒ `test_positive_control_…` 必须红，
  M896 把小节正文取空 ⇒ 切片那一格红，M897 取第一跑、M898 抹掉早先那跑的红、M899 读不到 skip 当 0、
  M900 同一小节两行不一致静默取末 —— 各红各的格子，两半都有（正反对照）。
  这一格里仍然开着的不是"没有门"，而是**门只覆盖了 `Executed` 这一族读数**：
  帧数、刀数、§8 格子数、曲线节数还是各按各的取法。下一批要么把这些也纳进同一支仪器，
  要么按族各配一条恒等式 —— 按 R298 那一课，"某一族有牙"不等于"取数这件事有牙"。"""

BL_364 = u"""  追记（R309）：本轮把 `mutate_r309` 登记进名册，名册自己给了这件事的规模现读：
  `TABLE_ROSTER registered=@TABLES@ unregistered_with_arms=@HIDTABLES@ hidden_arms=@HIDARMS@`
  —— 也就是说"藏在 lambda 里、静态预检看不见"的臂有 @HIDARMS@ 把，分布在 @HIDTABLES@ 张没登记的表里。
  这一格因此不能靠"每张表都登记"来结：登记与否不影响那 423 把臂看不见这件事。
  真要做的是让每张表在**导入时**自数一遍自己的 needle 命中（`MUTATIONS` 已经是数据结构，
  自数是可行的），把"不在覆盖里"从静态正则的失败换成表自己报的数；本轮先把它写成读数而不是写成结论。"""

CH_NEW = u"""### 台账的读数口搬进仓库：按小节取数 + 恒等式闸门（R309 / U-@UA@…U-@UC@ · D-@DN@ · 产品 0 文件，判据轮）

- R308 落账时生成器在整份验证链日志里取末，把 `### CAPTURE 结论行补记` 那一行（捕帧卷 92 格）
  当成全量卷 ⇒ ITERATION / CHANGELOG / STATE 三本一起写着 `Executed 92`，真读数是 934 / 44 skip / 0；
  而「FULL_FAIL != 0 就拒写」那道门完全不响，因为抄来的那行恰好 0 失败。
- 本轮收成仓库里的尺：`scripts/ledger_readings.py`（小节切片 + 恒等式闸门 + 多跑每跑各自记账）、
  `scripts/tests/test_ledger_readings.py`（现读 `Ran @JUDGERUN@ / OK`，合成已知答案 + 真产物对照）、
  刀 M895…M900（@K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes、未落刀基线 `Ran @JUDGEBASE@`）。
- 写这一支的过程里又踩了 `re.split` 的块形状坑（标题与正文同住一块），**是新闸门当场 REFUSED 抓到的**，
  七本一个字节都没落盘；另一处自曝：M896 第一版的变异文写了 Swift 的 `//` 注释 ⇒ python 语法红 ⇒ NOT_RUN，
  改成 `#` 才有 CAUGHT（刀坏不是判据没牙，D-243 同一课）。
- Swift 三条腿本轮 NOT-RUN 并写明理由（0 产品文件、0 Swift 文件）；帧目录仍 @FRAMES@ 张在盘上（现读）。
- 判据轮：构建告警 0；预检 tables=@TABLES@ bad=0、名册 arms=@ARMREG@；
  脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；产品面连续零改动 **@STREAK@** 轮。

"""

ST_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

本轮做的是**写账这件事本身**：R308 的三本假账（把捕帧卷 92 当全量卷 934）通过了当时的门，
靠本轮新写的恒等式闸门才被拦住。落地三件：`scripts/ledger_readings.py`（小节切片 + 恒等式 + 每跑记账）、
`scripts/tests/test_ledger_readings.py`（现读 `Ran @JUDGERUN@ / OK`）、刀 M895…M900（全 CAUGHT、RESTORE_CLEAN=yes）。
D-@DN@ 定「读数只能由被计数物自己打印的那一行给出，且必须按所属小节取；跨小节取末算抄错」；
348 追记为"这一格今天有了尺真身，但门只覆盖 `Executed` 这一族"；364 追记为"隐藏臂规模现读 @HIDARMS@ 把 / @HIDTABLES@ 张表"。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**台账的读数口搬进仓库**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran @JUDGERUN@ / OK`；刀 @K_N@ 把全 CAUGHT；
预检 tables=@TABLES@ covered=@COVERED@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
仪器跑真日志 `@RDLINE@`；电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；
看图腿 RUN（@FRAMES@ 张在盘上，本轮没有新帧 —— @EYE_SHORT@）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；上一轮是 @PREVSTREAK@）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。
Swift 三条腿 NOT-RUN 并写明理由（全量卷 / 重捕帧 / 换装 —— 本轮 0 Swift 文件，没有新字节可跑，也没有旧字节能被本轮弄坏）。

⓪ @RNEXT@ 开场要先读的（成对：run id ↔ commit）：@CI@
   —— 本轮两笔（代码半 + 账半）的 runner 结论要读；`scripts/ledger_readings.py` 与
   `scripts/tests/test_ledger_readings.py` 是新进电池的两格，若 runner 上红在
   `test_the_round_chain_log_reads_as_the_ledger_claims` 那**不是坏**：那一格在 /tmp 日志不在时是 skip，
   要查的是"skip 名单有没有按机器分键接住它"（331/347 那一族），别去改判据。

① 下一轮（@RNEXT@）的靶：① 回到产品面 —— 356 剩下那一半（暗档最细一步 17.33 低于可见性地板 18）
   要先量"换通道"那一候选还有没有产物证人，别再拿减档数当解药；
   ② 364 的表自数（每张表导入时数自己的 needle 命中，@HIDARMS@ 把隐藏臂必须能报出来）；
   ③ 348 剩下那批读数族（帧数 / 刀数 / §8 格子数各配一条恒等式）；
   ④ 360 的最后一批（11 份裸 stdout）；⑤ 361 的合并；⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、364（隐藏 needle 的规模已数出来，尚未有牙）、
   348 的"读数族还没纳全"、354 的第五步（sampled 那两条的退场阈值）、360（剩 11 份）、361（未合并）、
   359、362、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   用户闸门 220 路 A / 228② / 265。

"""

FR_SECTION13 = None

# ---------------------------------------------------------------- 组装与落盘
orig = {k: rd(v) for k, v in FILES.items()}
idemp = [(k, w) for k, w in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                             (u"ST", u"## %s 状态（" % R_TAG))
         if w in orig[k]]
if idemp:
    die(u"台账里已经有本轮那一节（%s）⇒ 生成器不许重跑第二遍，先看上一跑落在哪"
        % u",".join(k for k, _ in idemp))

texts = {
    u"UI": fill_tpl(UI_NEW, SUBS), u"IT": fill_tpl(IT_NEW, SUBS),
    u"DEC": fill_tpl(DEC_NEW, SUBS), u"BL348": fill_tpl(BL_348, SUBS),
    u"BL364": fill_tpl(BL_364, SUBS), u"CH": fill_tpl(CH_NEW, SUBS),
    u"ST": fill_tpl(ST_NEW, SUBS),
}
for k, t in texts.items():
    hit = re.findall(u"@([A-Z][A-Z0-9_]{1,24})@", t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")

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


def append_into_item(text, header_prefix, note, label):
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(header_prefix)]
    if len(hits) != 1:
        die(u"%s 的条目头命中 %d 行（要恰好 1）" % (label, len(hits)))
    h = hits[0]
    nxt = [i for i in range(h + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    k = nxt[0] if nxt else len(lines)
    while lines[k - 1].strip() == u"":
        k -= 1
    head = u"\n".join(lines[:k])
    if not head.endswith(u"\n"):
        head += u"\n"
    out = head + note.rstrip(u"\n") + u"\n" + u"\n".join(lines[k:]).lstrip(u"\n")
    i_head, i_note = out.find(header_prefix), out.find(note.split(u"\n")[0].strip())
    if not (0 <= i_head < i_note):
        die(u"%s 的追记落点不对（%d / %d）" % (label, i_head, i_note))
    return out


new_bl = append_into_item(orig["BL"], u"**348. ", texts["BL348"], u"348")
new_bl = append_into_item(new_bl, u"**364. ", texts["BL364"], u"364")
if len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", new_bl)) != len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", orig["BL"])):
    die(u"BACKLOG 的条目头数量变了 ⇒ 追记动到了条目结构，不只是追加")

new_ch = once(orig["CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"],
              u"CHANGELOG [Unreleased]")


def heading_lines(text, title):
    return sum(1 for line in text.split(u"\n") if line.strip() == title)


if heading_lines(new_ch, u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 标题行不再是恰好 1 行（现读 %d）"
        % heading_lines(new_ch, u"## [Unreleased]"))

new_st = once(orig["ST"], u"## %s 状态（" % PREV_TAG,
              texts["ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig["FR"]
before_u = len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr))
if before_u != 1:
    die(u"§1 的 U 那一格锚点命中 %d 次（要恰好 1）" % before_u)
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
           u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
if u"U-31 … U-%d（%s 现读抬" % (UC, R_TAG) not in fr:
    die(u"§1 的 U 上界没抬到 U-%d" % UC)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")
if u"%s 节 ②" % R_TAG not in fr:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
stray = [u"%s:%d %s" % (k, n, hit.group(0)) for k, t in new.items()
         for n, line in enumerate(t.split(u"\n"), 1) for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))

for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)

import atexit


def restore():
    for key, text in orig.items():
        wr(FILES[key], text)


def _crash_guard():
    if WROTE and not OK_EXIT:
        restore()
        sys.stderr.write(u"R309_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)


def refresh_report_after_write():
    """报告的标题格、§13 三格、Sources 那一格：**只能在六本落地之后**由仪器刷（R308 实测的顺序）。"""
    txt = rd(FILES["FR"])
    out, crc = sh([sys.executable, CURVE])
    rounds = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
    last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
    tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    if not rounds or not last_round or not tail:
        die(u"曲线尺没打出 ROUNDS= / rounds=9..N / SCORES_BY_ROUND（rc=%d）⇒ 报告不许按记忆刷" % crc)
    lines = txt.split(u"\n")
    head = lines[0]
    m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", head)
    if not m or head.count(u"R9–R") != 1:
        die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评`（或命中多于一处）⇒ 不敢整行改写")
    lines[0] = head[:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds) + head[m.end():]
    body = u"\n".join(lines)

    prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个、Swift 0 份（判据轮：改动面 %s 个文件，"
                 u"全在 `scripts/` 与 `.scratch/motion-audit-2/`），产品面连续零改动轮数 = **%s**"
                 u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"
                 u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：帧目录仍 %s 张在盘上（现读），"
                 u"本轮没有新帧 ⇒ Swift 三条腿（全量卷 / 重捕帧 / 换装）按 NOT-RUN 记账并各写理由"
                 % (len(others), STREAK_N, ROUND, ROUND, LASTSHA, LASTROUND, PREV_STREAK, FRAMES))
    scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
                  u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s，"
                  u"未登记表 %s 张 / 隐藏臂 %s 把 ⇒ 364）；U 定义行 **%s 条**、最大 **U-%s**；"
                  u"决定台账最大 **D-%s**，BACKLOG 最大 **%s**。本轮新落的读数现抄：`%s`"
                  % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS,
                     len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN, BL_MAX, RD_LINE))
    where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
                  u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
                  u"⇒ 按目标继续修，不收口。" % (rounds, last_round, tail))
    for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                        (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
        parts = body.split(u"\n")
        hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
        if len(hits) != 1:
            die(u"§13 的「%s」那一格命中 %d 行（要恰好 1）" % (label, len(hits)))
        parts[hits[0]] = cell
        body = u"\n".join(parts)

    gout, grc = sh(["git", "log", "-40", "--format=%h\x1f%s", "--",
                    os.path.join("ClipboardHistory", "Sources")])
    if grc != 0:
        die(u"取「最近动过 Sources/ 的提交」失败（rc=%d）" % grc)
    src_rows = []
    for line in gout.splitlines():
        if u"\x1f" not in line:
            continue
        sha_, subj_ = line.split(u"\x1f", 1)
        mb = re.match(u"^R(\\d+)", subj_.strip())
        src_rows.append((sha_.strip(), int(mb.group(1)) if mb else None, subj_.strip()))
    picked = [r for r in src_rows if r[1] is not None and r[1] <= int(R_TAG[1:])]
    if not picked:
        die(u"标签 ≤ %s 的源码提交一笔都没有 ⇒ 那一格不许拿「此刻最新」凑数" % R_TAG)
    live_sha, live_src_round, live_subj = picked[0]
    older = [r for r in src_rows if r[0] != live_sha and r[1] is not None]
    prev_txt = (u"上一笔动 `Sources/` 的是 R%d（`%s`）。" % (older[0][1], older[0][0])) if older else u""
    src_cell = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— 现读 0 个新 `Sources/` 文件"
                u"（本轮是判据轮：改动面 %s 个文件全在 `scripts/` 与 `.scratch/`）；这一格登记的是"
                u"仓库里**最近一笔动过源码的提交**，它属于 %s；改了什么以 `AGENT_UI_AUDIT.md` 里那一轮的节为准"
                u"（这一格只登记号与数，不复述结论）。%s|"
                % (live_src_round, live_sha, len(others), live_subj[:34], prev_txt))
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
    if len(hits) != 1:
        die(u"报告的「最后一次动到 Sources/」那一格命中 %d 行（要恰好 1）" % len(hits))
    parts[hits[0]] = src_cell
    body = u"\n".join(parts)
    if STRAY_RX.search(body):
        die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
    wr(FILES["FR"], body)
    return rounds, last_round, tail


ROUNDS_AFTER, LAST_ROUND_AFTER, TAIL_AFTER = refresh_report_after_write()
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r309_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
hline, _ = sh([u"head", u"-1", FILES["FR"]])
if u"R9–R%s" % LAST_ROUND_AFTER not in hline:
    die(u"报告标题没接上写盘后的尾轮 Round %s" % LAST_ROUND_AFTER)
if u"U-31 … U-%d" % UC not in rd(FILES["FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口 ⇒ 升序台账被插在中间")
DERIVED2 = scores_by_round(cv2).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分 ⇒ 七维表那一格没被仪器接上" % RDN)

OK_EXIT.append(True)
print(u"LEDGERS_R309 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(others)) + u" 刀=" + s(K_N)
      + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 隐藏臂=" + s(HID_ARMS)
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" BLmax=" + s(BL_MAX)
      + u" 判据卷=" + s(JUDGE_RUN) + u" 帧=" + FRAMES
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(LAST_ROUND_AFTER) + u" 节数=" + s(ROUNDS_AFTER))
