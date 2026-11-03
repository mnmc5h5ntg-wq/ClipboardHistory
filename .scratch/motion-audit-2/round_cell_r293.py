#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补上「报告轮数那一格」的守卫，并把停在 223 的数改成仪器现读的数。

本轮现读（都是仪器自己打的，不手抄）：
· curve_from_ledger.py ⇒ PHASE2 n=283 rounds=9..290
· AGENT_FINAL_REPORT.md §1 那一格 ⇒ 停在「223 轮 / R9–R230 / PHASE2 n=223 / Round 221」
· scripts/tests/test_final_report_headline.py 7 格全 OK —— 它只管 sources 那一格
⇒ 报告正文里那句「停旧数会红」是**空头承诺**：会红的那道门从没为这一格写过。

这一支做三件事：① 把那一格的两个数换成现读值；② 写一条真会红的守卫（配正对照：
把数改旧它必须点名）；③ 把「R 与 Round 两种编号在同一格里混用」开成一单，
守卫**故意不判**那个标签（不判就写明，不许静默通过）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
TEST = os.path.join(ROOT, "scripts", "tests", "test_final_report_round_cell.py")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")


def die(m):
    sys.stderr.write("ROUND_CELL REFUSED: " + m + "\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def battery(tag):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["python3", "-W", "ignore", "-m", "unittest", "discover",
                             "-s", "scripts/tests", "-v"], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    txt = proc.communicate()[0].decode("utf-8", "replace")
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = sorted(set(re.findall("skipped '([^']*)'", txt)))
    if proc.returncode != 0 or not ran or not ok:
        die(tag + u" 电池不是绿的：" + txt[-900:])
    return ran[-1], ok[-1], names


_pipe = subprocess.Popen(["python3", CURVE], cwd=ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         env=dict(os.environ, PYTHONUTF8="1"))
curve = _pipe.communicate()[0].decode("utf-8", "replace")
proc = _pipe.returncode
if proc != 0:
    die(u"曲线尺不是绿的")
n_line = re.findall(r"^PHASE2 n=(\d+) rounds=(\d+)\.\.(\d+)", curve, re.M)
if not n_line:
    die(u"曲线尺没打出 PHASE2 n=… rounds=… ⇒ 没有可比的数")
PHASE2_N, ROUND_LO, ROUND_HI = n_line[-1]

rep = rd(REPORT)
cell_pat = re.compile(u"^\\| 阶段二 \\*\\*(\\d+) 轮\\*\\*审计（R9–R(\\d+)；"
                      u"以 `curve_from_ledger\\.py` 的 `PHASE2 n=(\\d+)` 为准，"
                      u"最新一节是 `AGENT_VISUAL_ITERATION\\.md` 的 Round (\\d+)")
m = cell_pat.search(rep, re.M)
if not m:
    die(u"报告里那一格的形状与预期不符 ⇒ 别硬改，先看它被谁动过")
OLD_N, OLD_R, OLD_PN, OLD_RND = m.group(1), m.group(2), m.group(3), m.group(4)
if OLD_PN == PHASE2_N and OLD_RND == ROUND_HI:
    die(u"那一格已经是现读数 ⇒ 无事可做（不幂等）")

new_cell = (u"| 阶段二 **%s 轮**审计（R9–R%s；以 `curve_from_ledger.py` 的 `PHASE2 n=%s` 为准，"
            u"最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round %s" % (PHASE2_N, OLD_R, PHASE2_N, ROUND_HI))
rep_new = rep[:m.start()] + new_cell + rep[m.end():]
wr(REPORT, rep_new)

wr(TEST, u'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告 §1「阶段二多少轮」那一格必须与 `curve_from_ledger.py` 的现读数相等。

为什么要有这一支（R293 现读）：那一格停在 223 轮 / Round 221，而仪器已经是
`PHASE2 n=283 rounds=9..290` —— 差了 60 轮却没有任何东西红，
而报告正文自己写着「停旧数会红」。同名的 `test_final_report_headline.py` 7 格全绿，
因为它只管 sources 那一格：**承诺与门不是同一件事**。

故意不判的那一格：同一行里的 `R9–R<NNN>` 用的是 R 编号，而 `Round <NNN>` 用的是台账编号
（映射 R_n = Round n−3），标题那一格把同一个变量印进了两种标签（见 BACKLOG 344）。
这一支不判它 —— 不判要写在这里，不许让它看起来像已经对过账。
"""
import io
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
CELL = re.compile(u"^\\\\| 阶段二 \\\\*\\\\*(\\\\d+) 轮\\\\*\\\\*审计（R9–R(\\\\d+)；"
                  u"以 `curve_from_ledger\\\\.py` 的 `PHASE2 n=(\\\\d+)` 为准，"
                  u"最新一节是 `AGENT_VISUAL_ITERATION\\\\.md` 的 Round (\\\\d+)")


def instrument():
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out = subprocess.Popen(["python3", CURVE], cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, env=env).communicate()[0]
    txt = out.decode("utf-8", "replace")
    hit = re.findall(u"^PHASE2 n=(\\\\d+) rounds=(\\\\d+)\\\\.\\\\.(\\\\d+)", txt, re.M)
    return (hit[-1] if hit else None), txt


def cell_of(text):
    return CELL.search(text, re.M)


class FinalReportRoundCell(unittest.TestCase):
    def test_cell_equals_instrument(self):
        inst, txt = instrument()
        self.assertIsNotNone(inst, u"曲线尺没打出 PHASE2 n=… ⇒ 无从对账（读不到不等于通过）")
        rep = io.open(REPORT, encoding="utf-8").read()
        m = cell_of(rep)
        self.assertIsNotNone(m, u"报告 §1 那一格形状变了 ⇒ 对账断线，要么改守卫要么改回来")
        self.assertEqual(m.group(3), inst[0],
                         u"报告里写的 PHASE2 n=%s 与仪器现读 %s 不一致 ⇒ 那一格停旧数"
                         % (m.group(3), inst[0]))
        self.assertEqual(m.group(5), inst[2],
                         u"报告里写的 Round %s 与仪器现读尾轮 %s 不一致"
                         % (m.group(5), inst[2]))

    def test_guard_has_teeth(self):
        # 正对照：把两个数各改旧一格 ⇒ 必须两处都不相等（守卫不响就是假绿）。
        inst, _ = instrument()
        self.assertIsNotNone(inst, u"仪器读不到时这条正对照无从判定")
        rep = io.open(REPORT, encoding="utf-8").read()
        m = cell_of(rep)
        self.assertIsNotNone(m, u"形状不符 ⇒ 正对照没有对象")
        stale = rep[:m.start()] + m.group(0).replace(
            u"PHASE2 n=" + m.group(3), u"PHASE2 n=999").replace(
            u"Round " + m.group(5), u"Round 998") + rep[m.end():]
        s = cell_of(stale)
        self.assertNotEqual(s.group(3), inst[0], u"改旧了还不红 ⇒ 这一格是假的")
        self.assertNotEqual(s.group(5), inst[2], u"改旧了还不红 ⇒ 这一格是假的")


if __name__ == "__main__":
    unittest.main()
''')

if not os.path.exists(TEST):
    die(u"守卫文件没落盘")

pre = battery(u"改前")
print(u"ROUND_CELL OK 报告那一格 %s/%s → %s/%s 守卫已入库" % (OLD_PN, OLD_RND, PHASE2_N, ROUND_HI))

n344, proc = (0, 0), None
bl = rd(BACKLOG)
ITEM = (u"\n**344. 报告标题与 §1 那一格把两种编号印成了同一个数（R293 现读：标题 `R9–R290，290 轮自评`，"
        u"而 §1 同一行里 `R9–R230` 用 R 编号、`Round 221` 用台账编号，映射是 R_n = Round n−3 ⇒ 三个标签三种口径）**："
        u"`scripts/tests/test_final_report_round_cell.py` 故意只对账 `PHASE2 n` 与尾轮 `Round` 这两个无歧义的数，"
        u"标签混用这一格**没判**（写在这里而不是静默通过）。做法二选一：① 那一格统一成 Round 口径；"
        u"② 守卫按 R=Round+3 换算后对账，换算错了就红。做完之前不许说「报告的轮数标签是对的」。\n")
last_no = re.findall(u"^\*\*(\d{3})\. ", bl, re.M)[-1]
if last_no != u"343":
    die(u"BACKLOG 最后一条是 " + last_no + u" 而不是 343 ⇒ 新单号要重算")
wr(BACKLOG, bl.rstrip(u"\n") + ITEM)

post = battery(u"改后")
if (post[0], post[1], len(post[2])) != (pre[0], pre[1], len(pre[2])):
    die(u"电池不一致 " + str(pre) + u" → " + str(post))
if int(post[0]) <= int(pre[0]):
    die(u"新守卫没进电池（Ran 没变多 ⇒ 文件没被 discover 收到）：" + str((pre[0], post[0])))

print(u"ROUND_CELL DONE 新单=344 batt=Ran " + pre[0] + u" → " + post[0]
      + u" skipped=" + post[1] + u" 名单=" + str(len(post[2])))
