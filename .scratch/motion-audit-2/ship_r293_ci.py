#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R293 的 CI 交账 + 自评曲线读数进 STATE ⓪（第 292 轮 / Round 290 的尾巴）。

证据链两条，都必须是仪器自己打的行：
· 步骤/作业：`ci_read.py steps` —— 红 run 能切出 STEP[n]，**绿 run 切不出**（R100 那一课：成功 run 里
  awk 按步骤名过滤恒为空）。所以绿这一侧由 `JOB build-and-test ⇒ success` 签：作业绿 ⇒ 后面每一步都过，
  包括 340 那两朵红所在的 STEP[15]/[17]。
· 正文：`gh run view --log` 里抓判据自己印的通道行（LEFT_AXIS_R292_1X / 只数到 N 个墨簇 / SKIP_ROSTER）。
  通道串必须用 LEFT_AXIS_，不能拿 ci_read.py readings 的默认通道（本轮实测它给的是 CARD_PROBE ⇒ 抓不到）。

三分支写死，不许见数改口：
① 作业绿 + 替身臂有行 + 全文无「只数到 N 个墨簇」⇒ 340 第④条**结案**。
② 作业绿 + 替身臂没行 ⇒ 第④条**仍无答案**：这一跑没有那句红话，但也没有那句读数 ⇒ 只能说没红，不能说判到了。
③ 作业红 ⇒ 照正文登记新红名，第④条无从判定，不许改 skip、不许放宽地板。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "AGENT_STATE.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
CI_FILE = "/tmp/r293_ci_tip.txt"
TIP_RUN = "39740056311"
TIP_SHA = "82a5c1a"
LEDGER_RUN = "39739173207"
LEDGER_SHA = "125884d"
MARK = u"（R293 CI 交账）"


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def die(m):
    sys.stderr.write("SHIP_R293_CI REFUSED: " + m + "\n")
    raise SystemExit(1)


def sh(argv, cwd=None):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    proc = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = sorted(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok:
        die(tag + u" 电池不是绿的或没有结论行（rc=" + str(rc) + u"）：" + txt[-1200:])
    return ran[-1], ok[-1], names


if not os.path.exists(CI_FILE):
    die(u"没有 " + CI_FILE + u" ⇒ 没读到 runner 的正文，本轮不写通过")
ci = rd(CI_FILE)

status = (re.findall(r"^TIP_STATUS=(\w+)", ci, re.M) or [u""])[-1]
concl = (re.findall(r"conclusion=(\w+)", ci, re.M) or [u"未读"])[0]
job = (re.findall(r"JOB build-and-test ⇒ (\w+)", ci) or [u"未读"])[0]
steps = re.findall(r"STEP\[(\d+)\] (.+?) ⇒ (\w+)", ci)
REDS = [s[0] + u":" + s[1].strip() for s in steps if s[2] == u"failure"]
SKIPS = [s[0] for s in steps if s[2] == u"skipped"]
MAO = re.findall(r"只数到 (\d+) 个墨簇", ci)
ARM1X = re.findall(r"LEFT_AXIS_R292_1X[^\n]*", ci)
R290 = re.findall(r"LEFT_AXIS_R290[^\n]*", ci)
ROSTER = re.findall(r"SKIP_ROSTER[^\n]*", ci)

# 作业结论必须有；步骤行只在红 run 里存在
if status != u"completed" or concl[0] == u"未读":
    die(u"这一跑还没结论（status=" + status + u"）⇒ 只能登记，不能交账")
if job == u"未读":
    die(u"解析不出 JOB build-and-test 的结论 ⇒ 没有签字的对象：" + ci.strip()[:200])
S4 = u"success" if job == u"success" else u"failure"
if job == u"success" and steps:
    die(u"作业绿却有失败步骤行 ⇒ 自相矛盾，先修解析再写账：" + str(REDS))

if S4 == u"success":
    if ARM1X and not MAO:
        VERDICT = (u"作业 ⇒ success（整跑每一步都过，含 STEP[15] executed-count 地板与 STEP[17] 未登记红闸门），"
                   u"且 runner 自己印出替身臂那一行、全文再无「只数到 N 个墨簇」⇒ 340 的第④条**结案**："
                   u"这朵连着三跑的红由「修好了吗」变成「跑了且不红」。runner 那一行现读＝"
                   + ARM1X[0].strip()[:260])
        CLOSE = True
    elif not ARM1X and not MAO:
        VERDICT = (u"作业 ⇒ success，且全文没有那句红话 —— 但也没有 LEFT_AXIS_R292_1X 那一行，"
                   u"即这一跑判据在 runner 上**没有留下正文** ⇒ 第④条只能说「没红」，"
                   u"不能说「量到了」；欠的是 runner 侧那条读数本身（新单登记，不许把 success 当结案）")
        CLOSE = False
    else:
        VERDICT = (u"作业绿但墨簇红仍露面（现读「只数到 " + u"/".join(MAO) + u" 个」）⇒ 第④条**判为没消失**，"
                   u"回到单位这一层继续查；对象地板与 tolerancePt 一条都不放宽（D-251）")
        CLOSE = False
else:
    VERDICT = (u"作业 ⇒ failure，失败步骤逐条＝" + (u"、".join(REDS) if REDS else u"未切出步骤名")
               + u"，skipped 步＝" + (u"、".join(SKIPS) if SKIPS else u"无")
               + u" ⇒ 第④条**仍无从判定**（没跑不等于消失），按正文继续查，不许改成 skip")
    CLOSE = False

curve_txt, crc = sh(["python3", CURVE])
if crc != 0:
    die(u"曲线尺不是绿的（rc=" + str(crc) + u"）：" + curve_txt[-600:])
by = re.findall(r"SCORES_BY_ROUND (.*)", curve_txt)
if not by:
    die(u"曲线尺没打出 SCORES_BY_ROUND ⇒ 本轮派生分取不到")
pairs = dict(re.findall(r"(\d+)=(\d+)", by[-1]))
for need in (u"288", u"289", u"290"):
    if need not in pairs:
        die(u"曲线里没有 Round " + need + u" 这一格")
S290, S289, S288 = pairs[u"290"], pairs[u"289"], pairs[u"288"]
gaps = (re.findall(r"^GAPS=(.*)", curve_txt, re.M) or [u"none"])[-1] or u"none"
ls_line = re.findall(r"^LEDGER_STATUS=(\w+)(?: conclusion=(\w+))?", ci, re.M)
LS = (ls_line[0][0] + (u" / " + ls_line[0][1] if ls_line and ls_line[0][1] else u"")) if ls_line else u"未读"

ADD = (MARK + u"：runner 现读 " + TIP_SHA + u" → " + TIP_RUN + u" / " + status + u" / " + concl[0]
       + u"，JOB build-and-test ⇒ " + job + u"。" + VERDICT + u"。"
       + u"（绿 run 切不出 STEP[n] 这件事按 R100 那一课登记：签字的是 job 结论与判据自己印的通道行，"
       + u"不是「STEP[4] 那一行不见了」；本轮 ci_read.py readings 默认通道是 CARD_PROBE，抓不到左轴那一行 ⇒ 正文改由 gh run view --log 现取。）"
       + u"名册那一格：SKIP_ROSTER 现读 " + (ROSTER[0].strip()[:120] if ROSTER else u"这一跑没印（无红）")
       + u"；账半那一笔 " + LEDGER_SHA + u" → " + LEDGER_RUN + u" / " + LS + u"。"
       + u"自评曲线现读（curve_from_ledger.py，GAPS=" + gaps + u"）Round 288=" + S288 + u"、289="
       + S289 + u"、**290=" + S290 + u"** ⇒ 连续三轮 <90 且 290 比 289 又低 3 分："
       + u"下一轮必须回到产品动效面选靶，但靶要由量出来的缺陷签（342 的画真底通道是 305 台阶地板的前置，D-274），"
       + u"不许为打破 0 改动纪录加动效。只登记不轮询，R140。")

st = rd(STATE)
if MARK in st:
    die(u"STATE 已有这笔交账 ⇒ 不幂等，先还原")
lines = st.splitlines(True)
hits = [i for i, l in enumerate(lines) if l.startswith(u"⓪ 读 CI：")]
if not hits:
    die(u"STATE 里找不到 ⓪ 行")
lines[hits[0]] = lines[hits[0]].rstrip(u"\n") + u"\n" + ADD + u"\n"
st_new = u"".join(lines)

bl_old = rd(BACKLOG)
if CLOSE:
    NOTE = (u"  " + MARK + u"：**第④条结案。** " + VERDICT + u"\n")
else:
    NOTE = (u"  " + MARK + u"：**第④条仍无答案。** " + VERDICT
            + u" 这一条不许登记成「红消失」，也不许改成 skip 或免检。\n")
al = bl_old.splitlines(True)
if MARK in bl_old:
    die(u"BACKLOG 已有这笔 ⇒ 不幂等")
h340 = [i for i, l in enumerate(al) if l.startswith(u"**340. ")]
h341 = [i for i, l in enumerate(al) if l.startswith(u"**341. ")]
if len(h340) != 1 or len(h341) != 1 or h341[0] <= h340[0]:
    die(u"340/341 锚点异常")
k = h341[0]
while al[k - 1].strip() == u"":
    k -= 1
bl_new = u"".join(al[:k]) + NOTE + u"\n" + u"".join(al[k:])

pre = battery(u"写盘前")
if pre[1] != str(len(pre[2])):
    die(u"电池颗数与名单不同源（汇总=" + pre[1] + u" 名单=" + str(len(pre[2])) + u"）")

wr(STATE, st_new)
wr(BACKLOG, bl_new)
if rd(BACKLOG).count(MARK) != 1 or rd(STATE).count(MARK) != 1:
    die(u"落盘后处数对不上 ⇒ 立刻停")

post = battery(u"写盘后")
if (post[0], post[1], len(post[2])) != (pre[0], pre[1], len(pre[2])):
    die(u"写盘前后电池不一致 " + str(pre) + u" → " + str(post))

print(u"SHIP_R293_CI OK job=" + job + u" 墨簇红处数=" + str(len(MAO))
      + u" 替身臂行=" + str(len(ARM1X)) + u" verdict340=" + (u"结案" if CLOSE else u"仍无答案")
      + u" score=288/" + S288 + u" 289/" + S289 + u" 290/" + S290
      + u" batt=Ran " + post[0] + u" skipped=" + post[1] + u" 名单=" + str(len(post[2])))
