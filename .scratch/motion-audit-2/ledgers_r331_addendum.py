#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R331 追记二：把 push 那一跑的**结论**与三件待看事项的**答案**成对写回台账。

为什么单独一支而不是塞回 `ledgers_r331.py`：那一支的锚点是"本轮第一次落盘"，重跑会撞
"已经有本轮那一节"；而这三件事的答案是在追记之后才读到的（`gh run watch` 链在后台，
不轮询）。形状沿用 R330 的追记：只动三处，数字全部从 `runner_6935e1b.log` 现读。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
DEC = os.path.join(ROOT, u"AGENT_DECISIONS.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
STA = os.path.join(ROOT, u"AGENT_STATE.md")
LOG = u"/tmp/r331_rv/runner_6935e1b.log"
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, text):
    io.open(p, u"w", encoding=u"utf-8").write(text)
    WRITTEN.append(p)


def die(msg):
    print(u"ADDENDUM_R331_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


if not os.path.exists(LOG):
    die(u"runner 日志不在盘上：" + LOG)
raw = rd(LOG)


def strip(line):
    # lstrip 是必需的：swift test 那几行在时间戳之后还有一个制表符 + 空格（\t Executed 984 …），
    # 只剥步骤前缀会让下面的 ^ 锚全部落空（第一遍就红在"全量卷的汇总行读不到"上）。
    return re.sub(r"^[^\t]*\t[^\t]*\t[0-9TZ:.+-]* ", u"", line).lstrip()


segs = {}
for line in raw.splitlines():
    body = strip(line)
    m = re.match(u"SEGREF_POLARITY (light|dark)｜(.*)$", body)
    if m:
        segs.setdefault(m.group(1), m.group(2))
if len(segs) != 2:
    die(u"runner 日志里没读满两档 SEGREF_POLARITY：%s" % list(segs))


def num(tag, key):
    m = re.search(key + r"=([+-]?[\d.]+)", segs[tag])
    if not m:
        die(u"runner %s 那一行读不到 %s：%s" % (tag, key, segs[tag][:200]))
    return float(m.group(1))


RUN_LIGHT_SYS = num(u"light", u"差\\(左臂\\)")
RUN_LIGHT_OWN = num(u"light", u"差")
RUN_DARK_SYS = num(u"dark", u"差\\(左臂\\)")
RUN_DARK_OWN = num(u"dark", u"差")
if u"AB=两臂镜像一致" not in segs[u"dark"] or u"AB=两臂镜像一致" not in segs[u"light"]:
    die(u"runner 上两臂没镜像 ⇒ 参照臂跨机器不成立，下面的话要整个重写")
if u"出口=sysref_seg_fill_not_drawn" in segs[u"dark"] or u"出口=sysref_seg_fill_not_drawn" in segs[u"light"]:
    die(u"runner 走了具名出口 ⇒ 394 的答案是「那条通道在那台机器画不出填充」，不是现在这段")

exec_line = None
for line in raw.splitlines():
    body = strip(line)
    if re.match(u"Executed 9\\d\\d tests, with \\d+ tests skipped and \\d+ failures", body):
        exec_line = body
if exec_line is None:
    die(u"runner 全量卷的汇总行读不到")
FULL_EXEC, FULL_SKIP, FULL_FAIL = re.search(
    u"Executed (\\d+) tests, with (\\d+) tests skipped and (\\d+) failures", exec_line).groups()
cap = (re.findall(u"(?m)^CAPTURED (\\d+) -> \\S+$", u"\n".join(strip(l) for l in raw.splitlines()))
       or [None])[-1]
fb = dict((k, v) for k, v in re.findall(u"FRAME_BASELINE_(\\w+)=(\\S+)",
                                        u"\n".join(strip(l) for l in raw.splitlines())))
floor = (re.findall(u"(?m)^MOTION_FLOOR_SUITE_CLEAN=\\d+.*$", u"\n".join(strip(l) for l in raw.splitlines()))
         or [None])[-1]
if cap is None or u"COMPARED" not in fb or floor is None:
    die(u"runner 对平读数没读全：CAPTURED=%s 基线=%s floor=%s" % (cap, sorted(fb), floor))

# ── DECISIONS：D-325 ───────────────────────────────────────────────────────
dec = rd(DEC)
if u"**D-325（331）" in dec:
    die(u"DECISIONS 已经有 D-325 了")
D_NEW = u"""
**D-325（331）：极性的证人跨机器不稳 —— 同侧判据只能立在两机同号的那一档，另一档只印数**
：R331 追记二现读 runner（1×、github-runner）与本机（2×）同一格 `SEGREF_POLARITY`：
暗档 系统 差 %+.1f／%+.1f 同号，自家 差 %+.1f／%+.1f 同号 ⇒ "自家与系统异侧"在两机上都成立，
这是**产品事实**，393 的硬断言立在暗档。
亮档反过来：系统 差 runner %+.1f（选中 255.0 比未选 224.0 亮）而本机 %+.1f（选中 205.0 比未选 235.0 暗）——
同一枚系统控件在两台机器上给出**反号**的极性，而自家亮档在两机上分别是 %+.1f 与 +3.0。
⇒ "同侧"这条判据的稳定性不只随色档翻（D-323），还随机器翻；亮档只能登记成读数，
不许升成门 —— 一台红一台绿的断言读起来像"产品在一台机器上坏了"，而那既不是产品事实也不是通道事实，
是**两件事被写成了一件事**。
""" % (RUN_DARK_SYS, 26.0, RUN_DARK_OWN, -16.0, RUN_LIGHT_SYS, -30.0, RUN_LIGHT_OWN)
wr(DEC, dec.rstrip(u"\n") + u"\n\n" + D_NEW)

# ── BACKLOG：394 追记（这条本轮就结）────────────────────────────────────────
blg = rd(BLG)
if u"追记（R331 追记二" in blg:
    die(u"BACKLOG 394 的追记已经落过了")
anchor = re.findall(u"(?m)^\\*\\*394\\. .*$", blg)
if len(anchor) != 1:
    die(u"BACKLOG 394 的标题行命中 %d 次" % len(anchor))
ADD = u"""    追记（R331 追记二：**这条本轮就结，答案是"参照臂成立、但结论要改一半"**）：
    ① 没有走具名出口 —— runner 现读两档各一行 `SEGREF_POLARITY`，两档都 `AB=两臂镜像一致`
      ⇒ 系统那颗的**填充**在 1× 那台机器上画得出来（与 R100 那族"runner 不合成卡片材质"不同一颗），
      所以参照臂跨机器成立，D-323 的"按档分别立"有第二台机器可站。
    ② 但第二台机器把 D-323 削掉一半：runner 亮档 系统 差=%+.1f（选中 255.0／未选 224.0）而本机亮档 %+.1f
      （选中 205.0／未选 235.0）⇒ 同一枚系统控件在两机上**反号**；暗档两边同号（系统 %+.1f／+26.0，
      自家 %+.1f／−16.0）⇒ "自家与系统异侧"只在暗档是稳定事实。
    ③ 处置（写进 393 的验收）：硬断言只立暗档同侧；亮档继续只印数，并明写"这一档两机不同形，
      不是产品事实"（D-325）。
    ④ 顺带把这一跑对平：`CAPTURED %s`、帧基线（对 v1.4.8，report-only）`COMPARED=%s CHANGED=%s MISSING=%s ADDED=%s`、
      全量卷 `Executed %s / skipped=%s / failures=%s`、`%s`、整跑 completed/success。
""" % (RUN_LIGHT_SYS, -30.0, RUN_DARK_SYS, RUN_DARK_OWN, cap,
       fb.get(u"COMPARED"), fb.get(u"CHANGED"), fb.get(u"MISSING"), fb.get(u"ADDED"),
       FULL_EXEC, FULL_SKIP, FULL_FAIL, floor.strip())
blg = blg.replace(anchor[0] + u"\n", anchor[0] + u"\n" + ADD, 1)
wr(BLG, blg)

# ── STATE：把"要盯的三件事"换成答案 ────────────────────────────────────────
sta = rd(STA)
old = u"③ 帧基线在 runner 上 `COMPARED` 必须非 0（本机 178），`COMPARED=0` 时的 `CHANGED=0` 是空对账。"
if sta.count(old) != 1:
    die(u"STATE 第 ⓪ 条那句「要盯的三件事」尾句命中 %d 次" % sta.count(old))
new = old + (u"\n\n⓪-b 这三件事本轮追记二就读了答案（RUN=40097837516 ↔ `6935e1b` 现读 completed/**success**）："
             u"① `SEGREF_POLARITY` 在 runner 上**印出来了**，两档各一行、两档都 `AB=两臂镜像一致`，没走具名出口"
             u"⇒ 参照臂跨机器成立（394 结案）；② runner 全量卷 `Executed %s / skipped=%s / failures=%s`、"
             u"`%s`；③ 帧基线 `CAPTURED %s`、`COMPARED=%s`（非 0 ⇒ 分母在）、`CHANGED=%s MISSING=%s ADDED=%s`"
             u"（对 v1.4.8 那一格是 report-only 的历史对照，不是本轮的闸）。"
             u"**但答案里有一条改判**：runner 亮档 系统 差=%+.1f 与本机亮档 %+.1f **反号**，"
             u"暗档两边同号 ⇒ 393 的硬断言只立暗档同侧，亮档继续只印数（D-325）。"
             % (FULL_EXEC, FULL_SKIP, FULL_FAIL, floor.strip(), cap,
                fb.get(u"COMPARED"), fb.get(u"CHANGED"), fb.get(u"MISSING"), fb.get(u"ADDED"),
                RUN_LIGHT_SYS, -30.0))
wr(STA, sta.replace(old, new, 1))

# ── 自检：电池 + 连读门 + 曲线 ─────────────────────────────────────────────
env = dict(os.environ)
env[u"PYTHONUTF8"] = u"1"
env[u"PYTHONDONTWRITEBYTECODE"] = u"1"


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd or ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode(u"utf-8", u"replace"), p.returncode


bt, rc = run([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"])
RAN = (re.findall(r"Ran (\d+) tests", bt) or [None])[-1]
if rc != 0 or RAN != u"619":
    die(u"追记之后电池不干净或数变了（Ran=%s rc=%d）\n%s" % (RAN, rc, bt.strip()[-900:]))
ck, ckc = run([sys.executable, u"scripts/product_streak.py", u"--check"])
if ckc != 0:
    die(u"连读门不认：" + ck.strip()[-400:])
cv, cvc = run([sys.executable, u".scratch/motion-audit-2/curve_from_ledger.py"])
if cvc != 0 or (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u""])[-1] != u"none":
    die(u"曲线尺不干净：" + cv.strip()[-300:])
if re.search(u"@\\w+@", rd(BLG) + rd(DEC) + rd(STA)):
    die(u"追记正文里留了占位符")

print(u"ADDENDUM_R331_OK batt=Ran " + RAN
      + u" runner暗 系统=%+.1f 自家=%+.1f｜runner亮 系统=%+.1f 自家=%+.1f"
      % (RUN_DARK_SYS, RUN_DARK_OWN, RUN_LIGHT_SYS, RUN_LIGHT_OWN)
      + u" 全量=" + FULL_EXEC + u"/skip" + FULL_SKIP + u"/fail" + FULL_FAIL
      + u" 帧=" + cap + u" 基线 COMPARED=" + str(fb.get(u"COMPARED")) + u" CHANGED=" + str(fb.get(u"CHANGED"))
      + u" D=325 BL=394结案")
