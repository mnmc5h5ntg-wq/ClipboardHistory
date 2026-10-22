#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R293 收尾：把这一小时读到的三件事记进台账，并把改坏的门入库。

三件事都不是产品：
· 63cc715 → 39732589843 的红在 STEP[4] 的**告警**，STEP[5..14] 全 skip ⇒ 340 的第④条「那两跑的红必须消失」
  这一跑**没有答案**（没跑 ≠ 消失），照 R87 只能写成无从判定。
· 本机四件套的「0 告警」编的是产品目标，CI 那道门带 --build-tests ⇒ 连着三轮那句读数是半覆盖的。
· 四件套守卫从摘要行找用例名，恒得 [] ⇒ 304 那颗计时红每次都被判成「不在这一族」，
  而「先跑隔离」那条出口根本到不了（一条只有一种坏法的守卫）。

数字全从盘上现读（/tmp/r293_buildtests.log、/tmp/r293_isolation.txt、full.log），不许手抄。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = {n: os.path.join(ROOT, "AGENT_" + n + ".md") for n in
     ("BACKLOG", "STATE", "DECISIONS", "UI_AUDIT")}
MARK = u"追记（R293 收尾）"


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def die(m):
    sys.stderr.write("SHIP_R293 REFUSED: " + m + "\n")
    raise SystemExit(1)


def battery(tag):
    """跑一次脚本电池，返回 (Ran, skipped 颗数, -v 名单)。名单与颗数必须同源对账（341）。"""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(
        ["python3", "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests", "-v"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    txt = proc.communicate()[0].decode("utf-8", "replace")
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)$", txt, re.M)
    names = sorted(set(re.findall("skipped '([^']*)'", txt)))
    if proc.returncode != 0 or not ran or not ok:
        die(tag + " 电池不是绿的或没有结论行（rc=%d）：\n%s" % (proc.returncode, txt[-1500:]))
    return ran[-1], ok[-1], names


# ── 读数：全部从盘上取，取不到就拒绝写账 ─────────────────────────────
bt = rd(os.path.join("/tmp", "r293_buildtests.log"))
BT_WARN = str(bt.count("warning:"))
BT_FILE = "UICaptureHarness.swift" in bt
BT_OK = "Build complete!" in bt
iso = rd("/tmp/r293_isolation.txt") if os.path.exists("/tmp/r293_isolation.txt") else ""
ISO_GREEN = "with 0 failures" in iso
full = rd("/tmp/r293_verify/full.log") if os.path.exists("/tmp/r293_verify/full.log") else ""
RED_NAME = re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", full)
if not (BT_FILE and BT_OK and ISO_GREEN and RED_NAME):
    die("读数缺格：编到测试文件=%s 构建完成=%s 隔离绿=%s 红名=%s ⇒ 没读到的不许进账"
        % (BT_FILE, BT_OK, ISO_GREEN, sorted(set(RED_NAME))))

N15, S1, L1 = battery("写盘前")
if len(L1) != int(S1):
    die("电池名单颗数 %d 对不上汇总 skipped=%s ⇒ 两处不同源（341），先修对账再写账"
        % (len(L1), S1))

# ── ① BACKLOG 340 / 341 各自一条追记（整行定位，插在被追记那一条的块内）──
bl = rd(B["BACKLOG"])
if MARK in bl:
    die("BACKLOG 已有 R293 收尾的追记 ⇒ 不幂等，先还原")

NOTE_340 = (u"  " + MARK + u"：**" + u"63cc715 → 39732589843 读到了，但这一跑没有第④条的答案。**"
            u" 全部失败步骤现读为 STEP[4] Build（正文 `UICaptureHarness.swift:6139:13: warning: result of "
            u"call to 'withUnsafeBytes' is unused`、`compile warnings: 48`、exit 1）与连带的 STEP[17]/[18]/[19]，"
            u"而 STEP[5..14] 整段 skipped ⇒ 墨簇那朵红这次没露面**是因为捕获步骤根本没跑**，不是因为修好了 —— "
            u"按 R87 这条只能登记成「无从判定」，不许写成「红消失」，第④条仍开。告警本身在 R293 代码半里用 `_ =` 修掉了，"
            u"并且这次是按 CI 那道门同一个目标（`swift build --build-tests`）强制重编 `UICaptureHarness.swift` 现读到 "
            u"warnings=" + BT_WARN + u"（/tmp/r293_buildtests.log，编到测试文件=" + str(BT_FILE) + u"）⇒ "
            u"改前/改后两边都有数。下一跑 STEP[4] 该绿，那才是本单第②④条拿得到替身读数的前提。\n")

NOTE_341 = (u"  " + MARK + u"：**又踩到同一族，这次是「守卫只有一种坏法」。** 四件套的守卫从 "
            u"`ROUND_VERIFY` 那一行 findall 用例名 —— 那行只有摘要 `Executed n tests, with k failures`，"
            u"永远取到 `[]` ⇒ 304 那颗计时红每次都被判成「不在 304 那一族」，而紧跟着那句「先跑隔离」的出口**根本到不了**"
            u"（R293 第一次跑就是这么停的，红名其实是 " + u"、".join(sorted(set(RED_NAME))) + u"）。"
            u"两处一起改：① 失败名单改从 `$RUN/full.log` 取；② 把那条无条件 die 换成当场跑一次 "
            u"`--filter PerfBudgetTests/testImageComparisonCostStaysBounded`，只有隔离仍红才 die。"
            u"两条都在本轮真跑过：full.log 现读红名见上，隔离复跑绿（/tmp/r293_isolation.txt）。"
            u"第①条的「摘要与名单同源」在生成器里也已按颗数对账（本次写盘前后各一次，Ran " + N15 +
            u" / skipped=" + S1 + u" / 名单 " + str(len(L1)) + u" 颗）。\n")


def insert_into_item(text, item_no, note, label):
    """把 note 插进 `**item_no. ` 那一条的块尾（下一条目的锚点之前）。"""
    anchor = u"**" + item_no + u". "
    hits = [i for i, l in enumerate(text.splitlines(True)) if l.startswith(anchor)]
    if len(hits) != 1:
        die(label + " 锚点命中 %d 次" % len(hits))
    lines = text.splitlines(True)
    nxt = None
    for j in range(hits[0] + 1, len(lines)):
        if re.match(u"^\*\*\d{3}\. ", lines[j]) or lines[j].startswith(u"## "):
            nxt = j
            break
    end = nxt if nxt is not None else len(lines)
    k = end
    while k > hits[0] + 1 and lines[k - 1].strip() == u"":
        k -= 1
    if nxt is not None:
        out = u"".join(lines[:k]) + note + u"\n" + u"".join(lines[k:])
    else:
        out = u"".join(lines[:k]) + note.rstrip(u"\n") + u"\n" + u"".join(lines[k:])
    return out


bl2 = insert_into_item(bl, u"340", NOTE_340, u"340")
bl3 = insert_into_item(bl2, u"341", NOTE_341, u"341")

ITEM_343 = (u"\n**343. 本机那道「0 告警」的门编译的不是 CI 那道门编译的目标（R293 现读："
            u"`scripts/round_verify.sh` 第 1 步只 `swift build`，CI 的 STEP[4] 带 `swift build --build-tests` —— "
            u"workflow 注释里写着 R59/BACKLOG 87 就为这件事改过 CI，本机四件套漏了同一个坑）⇒ 连着三轮 "
            u"`build_warnings=0` 说的是产品目标，测试目标从没编过，runner 那朵告警红于是在本机绿了三轮**："
            u"本轮把本机门换成 `--build-tests`，两边读数：改前 CI 现读 48 条告警并 exit 1，改完本机强制重编同一颗文件 "
            u"现读 " + BT_WARN + u" 条（/tmp/r293_buildtests.log）。两处没做，做完之前不许说「本机 0 告警 = CI 也会 0 告警」："
            u"① 告警只在**真重编**那一刻进日志，缓存全命中时 0 是弱读数 ⇒ 门要同时报「这次编了几个文件」并断言 "
            u"`ClipboardHistoryAppTests` 在其中，编不到就红（成因按 313/316 那一族解释，一条地板都不放宽）；"
            u"② 给这道门配一把刀：往测试目标塞一条会告警的行，本机门必须红，两臂分别登记（D-272 的双机对称）。\n")

last_no = re.findall(u"^\*\*(\d{3})\. ", bl3, re.M)[-1]
if last_no != u"342":
    die("BACKLOG 最后一条是 " + last_no + u" 而不是 342 ⇒ 新单号要重算")
bl_new = bl3.rstrip(u"\n") + u"\n" + ITEM_343

# ── ② STATE 顶部那一节的 ⓪ 行：把交掉的账与剩下的前提写在同一行 ──
st = rd(B["STATE"])
lines = st.splitlines(True)
hits = [i for i, l in enumerate(lines) if l.startswith(u"⓪ 读 CI：")]
if not hits:
    die("STATE 里找不到 ⓪ 行")
ADD = (u" —— 本笔读数已交（R293 收尾）：63cc715 那跑的红在 STEP[4] 的告警（正文与 48 条计数见 340 追记），"
       u"STEP[5..14] 整段 skipped ⇒ **340 的第④条这次无从判定**，不许当成红消失；"
       u"本两笔 5253bf4／125884d 的 run 由下一轮成对取（只登记不轮询，R140）。")
if ADD[:24] in lines[hits[0]]:
    die("STATE 的 ⓪ 行已经有这笔 ⇒ 不幂等")
lines[hits[0]] = lines[hits[0]].rstrip(u"\n") + ADD + u"\n"
st_new = u"".join(lines)

# ── 事务性：三处都算好了才落盘 ──
wr(B["BACKLOG"], bl_new)
wr(B["STATE"], st_new)

n343 = len(re.findall(u"^\*\*343\. ", bl_new, re.M))
if n343 != 1:
    die("343 落盘后命中 %d 次" % n343)
if bl_new.count(MARK) != 2:
    die("追记处数 %d 应为 2" % bl_new.count(MARK))

N16, S2, L2 = battery("写盘后")
if (N16, S2, len(L2)) != (N15, S1, len(L1)):
    die("电池写盘前后对不上：" + str((N15, S1, len(L1))) + " vs " + str((N16, S2, len(L2))))

print(u"SHIP_R293 OK batt=Ran " + N16 + u" (skipped=" + S2 + u", 名单=" + str(len(L2)) + u")"
      + u" warn=" + BT_WARN + u" red=" + u",".join(sorted(set(RED_NAME)))
      + u" iso=green 340+341 追记 新单=343")
