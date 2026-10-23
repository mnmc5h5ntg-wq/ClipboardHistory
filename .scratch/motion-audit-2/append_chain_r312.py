# -*- coding: utf-8 -*-
"""R312 验证链补记：把 round_verify.sh 的汇总行**原样派生**成生成器要读的那几行。

为什么需要：R311 的链是我手写的，键名（CAPTURED / INSTALL_RESULT= / FRAME_BASELINE_*）与
`scripts/round_verify.sh` 打印的形状不同。本轮改用 round_verify（它才是仓库里那颗四件套），
所以这里做一次**机械换形**：每一行都从它自己打印的那一行抄出来，不新增任何判断。

· WARNINGS          ← /tmp/r312_verify/warning_gate.log 的 ROUND_WARNING_GATE warnings=N
· CAPTURED          ← /tmp/r312_verify/capture.log 里最后一条 `CAPTURED n -> dir`
· FRAME_BASELINE_*  ← 链日志里 FRAME_GATE_PASS changed=C compared=N missing=M 与
                      ROUND_VERIFY 的 baseline_compared/baseline_changed
· INSTALL_RESULT    ← ROUND_VERIFY 的 dmg=D 与 installed_version=V（dmg=ok ⇒ ok）
· FRAMES_ON_DISK    ← 现场数 frames/ 里的 PNG（语义计数，不是 ls | wc -l）
· HIDDEN_ARMS / LEDGER_READINGS / NEEDLE_RANGE ← 现跑仓库里那两颗尺与探针
幂等：已经有 FRAMES_ON_DISK 那一行就说明补过。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
CHAIN = u"/tmp/r312_chain.log"
VERIFY = u"/tmp/r312_verify"
FRAMES = os.path.join(VERIFY, "frames")


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace"), p.returncode


def cat(path):
    if not os.path.exists(path):
        return u""
    return io.open(path, encoding="utf-8", errors="replace").read()


chain = cat(CHAIN)
if not chain:
    sys.stderr.write(u"APPEND_REFUSE 链日志不存在\n")
    sys.exit(1)
if u"FRAMES_ON_DISK=" in chain:
    sys.stdout.write(u"APPEND_SKIP 已经补过\n")
    sys.exit(0)

gate = cat(os.path.join(VERIFY, "warning_gate.log"))
caplog = cat(os.path.join(VERIFY, "capture.log"))
rv = (re.findall(r"(?m)^ROUND_VERIFY .+$", chain) or [u""])[-1]
fg = (re.findall(r"(?m)^FRAME_GATE_PASS .+$", chain) or [u""])[-1]

rows = []
warn = (re.findall(r"warnings=(\d+)", gate) or [None])[-1]
rows += [u"### BUILD（现读自 round_verify 的告警门）",
         u"WARNINGS=%s" % (warn if warn is not None else u"没解析到 " + gate.strip()[-100:])]

cap = (re.findall(r"CAPTURED \d+ -> \S+", caplog) or [None])[-1]
rows.append(cap if cap else u"CAPTURED 没读到（capture.log 缺或形状变了）")

n_cmp = (re.findall(r"compared=(\d+)", fg) or re.findall(r"baseline_compared=(\d+)", rv) or [None])[-1]
n_chg = (re.findall(r"changed=(\d+)", fg) or re.findall(r"baseline_changed=(\d+)", rv) or [None])[-1]
rows += [u"FRAME_BASELINE_COMPARED=%s" % n_cmp, u"FRAME_BASELINE_CHANGED=%s" % n_chg]

pngs = [n for n in os.listdir(FRAMES) if n.endswith(u".png")] if os.path.isdir(FRAMES) else []
rows += [u"### FRAMES_ON_LEDGER（落账之前现场数，语义计数只算 PNG）",
         u"FRAMES_ON_DISK=%d" % len(pngs),
         u"FRAMES_MATCH=%s" % (u"1" if cap and re.search(r"CAPTURED (\d+)", cap).group(1) == str(len(pngs)) else u"0")]

dmg = (re.findall(r"dmg=(\w+)", rv) or [None])[-1]
ver = (re.findall(r"installed_version=(\S+)", rv) or [None])[-1]
rows.append(u"INSTALL_RESULT=%s  dmg=%s  installed_version=%s（判据轮：0 产品文件，产物与上一笔同源）"
            % (u"ok" if dmg == u"ok" else u"NOT-RUN", dmg, ver))
rows += [u"### SWIFT_LEGS（判据轮：四件套由 round_verify 跑；**不 update 基线**，因为 changed=%s）" % n_chg]

ha, ha_rc = run([sys.executable, u"scripts/hidden_arms.py"])
rows += [u"### HIDDEN_ARMS",
         (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha) or [u"没打印结论行 rc=%d" % ha_rc])[-1]]

pr = run([sys.executable, u".scratch/motion-audit-2/probe_needle_positions_r312.py"])[0]
rows += [u"### PROBE（366 的两条出口）"] + [l for l in pr.splitlines() if l.startswith(u"NEEDLE_")]

lr, lrc = run([sys.executable, u"scripts/ledger_readings.py", CHAIN])
rows += [u"### LEDGER_READINGS",
         ((re.findall(r"(?m)^LEDGER_READINGS .+$", lr) or [u""])[0]
          or u"LEDGER_READINGS_RC=%d %s" % (lrc, lr.strip()[-160:]))]

with io.open(CHAIN, "a", encoding="utf-8") as h:
    h.write(u"\n" + u"\n".join(rows) + u"\n")
sys.stdout.write(u"\n".join(rows) + u"\nAPPEND_DONE\n")
