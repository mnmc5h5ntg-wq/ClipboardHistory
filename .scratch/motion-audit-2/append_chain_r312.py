# -*- coding: utf-8 -*-
"""R312 验证链日志的补记：把生成器要读的那几节现量现补（不改动已有行、不凭记忆填）。

R312 用的是 `scripts/round_verify.sh`，它打印的形状与 R311 手写链不同 ⇒
生成器要求的 `### HIDDEN_ARMS` / `### BUILD` / `### FRAMES` / `### SWIFT_LEGS` 四节要由
**这一支**现场补齐，每一行都是当场跑出来的读数：
· BUILD  ← /tmp/r312_verify/warning_gate.log（门本体自己打印的那行）
· HIDDEN_ARMS ← 现跑 scripts/hidden_arms.py
· FRAMES ← 现场数 PNG 张数，并与 CAPTURED 那行对账
· LEDGER_READINGS ← 现跑 scripts/ledger_readings.py（它吃这份链日志）
· SWIFT_LEGS ← 把链日志里已有的那几行原样列出来
幂等：已经有 NEEDLE_PROBE 那一节就说明补过，直接退出。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
CHAIN = u"/tmp/r312_chain.log"
VERIFY = u"/tmp/r312_verify"
SHOTS = u"/tmp/r312_verify/frames"


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace"), p.returncode


if not os.path.exists(CHAIN):
    sys.stderr.write(u"APPEND_REFUSE 验证链日志不存在\n")
    sys.exit(1)
text = io.open(CHAIN, encoding="utf-8").read()
if u"### FRAMES_ON_LEDGER" in text:
    sys.stdout.write(u"APPEND_SKIP 已经补过\n")
    sys.exit(0)

rows = []

# BUILD：告警门那一行原样抄
gate = u""
if os.path.exists(os.path.join(VERIFY, "warning_gate.log")):
    gate = io.open(os.path.join(VERIFY, "warning_gate.log"), encoding="utf-8").read()
warn = (re.findall(r"WARNINGS=(\d+)", gate) or re.findall(r"warnings=(\d+)", gate) or [u""])[-1]
rows += [u"### BUILD（现读自 %s/warning_gate.log）" % VERIFY,
         u"WARNINGS=%s" % (warn or u"没解析到 " + gate.strip()[-120:])]

# HIDDEN_ARMS：现跑仓库里那颗尺
ha, ha_rc = run([sys.executable, u"scripts/hidden_arms.py"])
ha_line = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha) or [u"没打印结论行 rc=%d" % ha_rc])[-1]
rows += [u"### HIDDEN_ARMS", ha_line]

# FRAMES：语义计数（只数 PNG），并与 CAPTURED 对账
if os.path.isdir(SHOTS):
    pngs = [n for n in os.listdir(SHOTS) if n.endswith(u".png")]
    cap = re.findall(r"CAPTURED (\d+)", text)
    rows += [u"### FRAMES_ON_LEDGER（落账之前现场数）",
             u"FRAMES_ON_DISK=%d" % len(pngs),
             u"FRAMES_MATCH=%s" % (u"1" if cap and int(cap[-1]) == len(pngs) else u"0"),
             u"### SWIFT_LEGS（本轮：判据轮，帧与换装由 round_verify 跑）",
             u"LEG CAPTURED=%s" % (cap[-1] if cap else u"没读到"),
             u"LEG BASELINE=%s" % (u" ".join(re.findall(r"FRAME_BASELINE_\w+=\d+", text)[:3]) or u"没读到"),
             u"LEG INSTALL=%s" % ((re.findall(r"(?m)^INSTALL_RESULT=.+$", text) or [u"没读到"])[-1])]
else:
    rows += [u"### FRAMES_ON_LEDGER", u"FRAMES_ON_DISK=0",
             u"FRAMES_DIR_MISSING %s 不在盘上 ⇒ 看图腿记 NOT-RUN" % SHOTS]

# LEDGER_READINGS：现跑读数口
lr, lrc = run([sys.executable, u"scripts/ledger_readings.py", CHAIN])
rows += [u"### LEDGER_READINGS",
         ((re.findall(r"(?m)^LEDGER_READINGS .+$", lr) or [u""])[0]
          or u"LEDGER_READINGS_RC=%d %s" % (lrc, lr.strip()[-160:]))]

with io.open(CHAIN, "a", encoding="utf-8") as h:
    h.write(u"\n".join(rows) + u"\n")
sys.stdout.write(u"\n".join(rows) + u"\nAPPEND_DONE\n")
