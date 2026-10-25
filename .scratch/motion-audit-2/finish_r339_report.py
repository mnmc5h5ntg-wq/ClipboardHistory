#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R339 收尾：报告计数器 + §14 + §1 刷新 + §8 名单 + 落盘后电池/曲线。

为什么单独一支：`ledgers_r339.py` 在写报告之前 die 了（§14 那一格有**两处同名标签**，
我的"恰好一处"断言按前缀数得到 2 —— 那正是 BACKLOG 408 记的事，断言没错，错在我只按前缀认）。
六本已经落盘，重跑整支会把 CHANGELOG 再插一遍（它没有幂等守卫），
所以剩下的步骤搬到这里，按同一套解析口径做。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
ITE = os.path.join(ROOT, u"AGENT_VISUAL_ITERATION.md")
DEC = os.path.join(ROOT, u"AGENT_DECISIONS.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
CURVE = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"curve_from_ledger.py")
FRESH = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"refresh_report_section1.py")
SRCCELL = os.path.join(ROOT, u"scripts", u"report_sources_cell.py")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")
STREAK = os.path.join(ROOT, u"scripts", u"product_streak.py")

ROUND, AUDIT_N, ITER_N, PRODUCT_N = 339, 338, 336, 3
U1, U8, D1 = 1155, 1162, 335
B_LADDER, B_LIGHT, B_OVERLAY = 413, 414, 415
ARMS_NEW = (u"M996", u"M997", u"M998")
ENV = dict(os.environ)
ENV[u"PYTHONUTF8"] = u"1"
ENV[u"PYTHONDONTWRITEBYTECODE"] = u"1"
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def sh(cmd):
    q = subprocess.run(cmd, cwd=ROOT, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return q.stdout.decode(u"utf-8", u"replace"), q.returncode


def die(msg):
    print(u"FINISH_R339_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


def once(text, anchor, replacement):
    n = text.count(anchor)
    if n != 1:
        die(u"锚点命中 %d 次（要 1 次）：%s" % (n, anchor[:90]))
    return text.replace(anchor, replacement)


def num_of(path, key, rx):
    out, rc = sh([sys.executable, path] + ([key] if key else []))
    m = re.findall(rx, out)
    if not m:
        die(u"没解析到 " + rx + u"：" + out.strip()[-200:])
    return out, m[-1]


# ── 现读：连读那一格要在**落盘之后**重取（ledger_round 已经变成 338）──────────
st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", u"%d" % AUDIT_N])
STREAK_N = (re.findall(u"streak=(\\d+)", st_out) or [u"?"])[-1]
if STREAK_N == u"?":
    die(u"连读那一格没解析到：" + st_out.strip()[-200:])
pre = rd(os.path.join(ROOT, u".scratch/motion-audit-2/mutate_needle_precheck.py")) and u""
pre_out, _ = sh([sys.executable, os.path.join(ROOT, u".scratch/motion-audit-2/mutate_needle_precheck.py")])
PRE = (re.findall(u"NEEDLE_PRECHECK tables=(\\d+) covered=(\\d+) arms=(\\d+) bad=(\\d+)", pre_out)
       or [(u"?", u"?", u"?", u"?")])[-1]
ARM_TOTAL = (re.findall(u"ARM_TOTAL files=(\\d+) arms=(\\d+)", pre_out) or [(u"?", u"?")])[-1]
if PRE[3] != u"0":
    die(u"针预检 bad≠0：" + str(PRE))
mut = rd(u"/tmp/r339_mutate.log")
CAUGHT = (re.findall(u"CAUGHT=(\\d+/\\d+)", mut) or [u"?"])[-1]
RESTORE = (re.findall(u"RESTORE_CLEAN=(\\w+)", mut) or [u"?"])[-1]
batt_pre = rd(u"/tmp/r339_py_pre.log")
BATT = (re.findall(u"Ran (\\d+) tests", batt_pre) or [u"?"])[-1]
BATT_SKIP = (re.findall(u"OK \\(skipped=(\\d+)\\)", batt_pre) or [u"?"])[-1]
bef = rd(u"/tmp/r339_before_final.log")
aft = rd(u"/tmp/r339_targeted.log")


def ladder(log):
    out = {}
    for ln in log.splitlines():
        if ln.startswith(u"SEG_PILL_BACKING dark"):
            p = re.search(u"页底=(\\d+)", ln).group(1)
            out[p] = (re.search(u"轨道=(-?\\d+)", ln).group(1),
                      re.search(u"选中=(-?\\d+)", ln).group(1),
                      re.search(u"差=(-?\\d+)", ln).group(1),
                      re.search(u"对比=([0-9.]+)", ln).group(1))
    if sorted(out) != [u"30", u"50", u"80"]:
        die(u"三档页底没读全：" + str(sorted(out)))
    return out


BEF, AFT = ladder(bef), ladder(aft)

# ── FINAL_REPORT ─────────────────────────────────────────────────────────────
fr = rd(FRA)
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
D_MAX = max(int(x) for x in re.findall(u"(?m)^### D-(\\d{3})", rd(DEC)))
B_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX, D_MAX, B_MAX) != (U8, D1, B_OVERLAY):
    die(u"最大号不一致：%d/%d/%d" % (U_MAX, D_MAX, B_MAX))
mUD = re.search(u"U-31 … U-(\\d+)", fr)
if not mUD:
    die(u"找不到 U 区间那一格")
fr = once(fr, mUD.group(0), u"U-31 … U-%d" % U_MAX)
mD = re.search(u"(决定台账[^\\n]*?D-\\d{3} … \\*\\*)(D-\\d{3})", fr)
if not mD:
    die(u"找不到「决定台账」那一格")
fr = fr[:mD.start(2)] + (u"D-%d" % D_MAX) + fr[mD.end(2):]
prod_hits = [ln for ln in re.findall(u"(?m)^- \\*\\*产品面（这一节最该被读的部分）\\*\\*：.*$", fr)
             if u"产品面连续零改动轮数" in ln]
if len(prod_hits) != 1:
    die(u"「产品面」那一格应为恰好一处，实得 %d" % len(prod_hits))
new_prod = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 **%d** 个（**动效主线 / 侧栏筛选胶囊**："
            u"`VisualTokens.swift` 新增 `selectedSegmentLiftWhite`、`PressableStyle.swift` 新增 "
            u"`SegmentKnob.liftAlpha`、`HistorySidebarView.swift` 在语义基准之上盖那一层）。"
            u"runner 连挂 8 跑的那朵红判成**产品事实**：新尺 `SEG_PILL_BACKING` 在本机原样复现出 "
            u"页底 50 那一档的 差=%s（轨道 %s 对 选中 %s），而同一跑系统那颗现读 差=+49.0；"
            u"改后三档 差 %s / %s / %s。"
            u"产品面连续零改动轮数 = **%s**（现读 `python3 scripts/product_streak.py`，"
            u"口径差一仍挂在 BACKLOG 412：本轮动了 %d 个产品文件，而这一格读成「本轮**之前**的连读轮数」）。"
            u"新开 %d（backing 尺只两档实测）、%d（亮档在原生页底上仍反号）、%d（轨道叠加量本身也按机器漂）；"
            u"411 结案（等 runner 验收），305 收到一条追记。"
            % (PRODUCT_N, BEF[u"50"][2], BEF[u"50"][0], BEF[u"50"][1],
               AFT[u"30"][2], AFT[u"50"][2], AFT[u"80"][2],
               STREAK_N, PRODUCT_N, B_LADDER, B_LIGHT, B_OVERLAY))
fr = once(fr, prod_hits[0], new_prod)
# §14 那一格与 §13 同名（BACKLOG 408 记的就是这件事）⇒ 只能按"哪一格是最新权威"来认，不能按前缀认
s14 = [ln for ln in fr.splitlines()
       if ln.startswith(u"- **判据与门的规模**") and u"最新的权威" in ln]
if len(s14) != 1:
    die(u"§14 那一格（带「最新的权威」）应为恰好一处，实得 %d ⇒ 同名标签的洞还在 BACKLOG 408 上挂着"
        % len(s14))
new_s14 = (u"- **判据与门的规模**（R%d 现读，这一格是最新的权威，§13 那格已冻结成历史）："
           u"脚本电池 `Ran %s`（skipped=%s）；变异臂在册 **%s** 把 / 扫了 **%s** 个表文件"
           u"（预检 tables=%s covered=%s arms=%s bad=%s）；"
           u"U 定义行最大 **U-%d**、决定最大 **D-%d**、BACKLOG 最大 **%d**；"
           u"本轮刀 `mutate_r%d.py CAUGHT=%s, RESTORE_CLEAN=%s`（%s）。"
           % (ROUND, BATT, BATT_SKIP, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], PRE[3],
              U_MAX, D_MAX, B_MAX, ROUND, CAUGHT, RESTORE, u"、".join(ARMS_NEW)))
fr = once(fr, s14[0], new_s14)
fr = re.sub(u"(?m)^(- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 R)\\d+( 节)",
            u"\\g<1>%d\\g<2>" % ROUND, fr, count=1)
if re.search(u"@\\w+@", fr):
    die(u"报告里还有没替换的占位符")
wr(FRA, fr)

sc, rc = sh([sys.executable, SRCCELL, u"--write"])
if rc != 0:
    die(u"Sources 那一格刷新失败：" + sc.strip()[-300:])
f1, rc = sh([sys.executable, FRESH])
if rc != 0 or u"REFUSED" in f1:
    die(u"报告 §1 的刷新器没签：" + f1.strip()[-300:])

# ── 七维表形状自检（行数=7、量纲全是 /15）────────────────────────────────────
ite = rd(ITE)
sec = ite.split(u"## Round %d · R%d" % (ITER_N, ROUND))[-1]
rows = re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", sec)
if len(rows) != 7 or any(mx != u"15" for _, _, mx in rows):
    die(u"七维表形状不对：行=%d 量纲=%s" % (len(rows), [r[2] for r in rows]))

cv, rc = sh([sys.executable, CURVE])
if rc != 0 or u"GAPS=none" not in cv:
    die(u"曲线仪器没签（GAPS）：" + cv.strip()[-400:])

# ── §8 搬运：把本轮各腿的日志并成一份，按"本轮声明的读数族"对账 ──────────────
combined = u""
for p in (u"/tmp/r339_build.log", u"/tmp/r339_targeted.log", u"/tmp/r339_full.log",
          u"/tmp/r339_capture3.log", u"/tmp/r339_baseline.log", u"/tmp/r339_mutate.log",
          u"/tmp/r339_pre.log", u"/tmp/r339_gate.log", u"/tmp/r339_py_pre.log",
          u"/tmp/r339_streak.log"):
    if os.path.exists(p):
        combined += rd(p) + u"\n"
io.open(u"/tmp/r339_rows_combined.log", u"w", encoding=u"utf-8").write(combined)
rw, rc = sh([sys.executable, ROWS, u"/tmp/r339_rows_combined.log",
             u"--must-include", u"SEG_PILL_BACKING"])
MISS = (re.findall(u"READINGS_MUST_INCLUDE 声明=(\\d+) 缺=(\\d+)", rw) or [(u"?", u"?")])[-1]
TOTAL = (re.findall(u"ROWS_TOTAL=(\\d+) ROWS_MISSING=(\\d+)", rw) or [(u"?", u"?")])[-1]
print(u"ROWS §8：声明/缺=%s 总数/缺值=%s rc=%d" % (MISS, TOTAL, rc))

chk, rc = sh([sys.executable, STREAK, u"--check"])
if rc != 0:
    die(u"连读门没签（落盘之后）：" + chk.strip()[-400:])
print(u"STREAK_CHECK " + chk.strip().splitlines()[-1][:200])

bt, rc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
BATT2 = (re.findall(u"Ran (\\d+) tests", bt) or [u"?"])[-1]
io.open(u"/tmp/r339_py_post.log", u"w", encoding=u"utf-8").write(bt)
if rc != 0:
    die(u"落盘之后脚本电池红了（Ran=%s）：%s" % (BATT2, bt.strip()[-1500:]))
print(u"R339_FINISH_OK 电池=%s(same as pre=%s) U=%d D=%d BL=%d 连读=%s 刀=%s 预检=%s"
      % (BATT2, BATT, U_MAX, D_MAX, B_MAX, STREAK_N, CAUGHT, u"/".join(PRE)))
