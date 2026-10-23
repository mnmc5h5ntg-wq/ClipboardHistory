# -*- coding: utf-8 -*-
u"""R315 账半的**证据链构建器**（一次性仪器，用完即撤）。

形状照 `append_chain_r314.py`：不写台账，只把本轮所有腿**现场再跑一遍**，
把结论行按小节追加进 /tmp/r315_chain.log，供 `ledgers_r315.py` 解析（解析不到就 die）。

本轮与上一轮不同的一处：证人不是"两次捕获"，而是**撤帧那一笔的四件现读** ——
捕获卷零红 + `CAPTURED 174` + 基线同一笔 update + 针预检里 M566 仍 ok。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = u"/tmp/r315_chain.log"
VERIFY = u"/tmp/r316_chain.log"
CAP = u"/tmp/r316_capture.log"
SHOTS = u"/tmp/r316_shots"
FULL = u"/tmp/r316_verify/full.log"
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
PROBE = os.path.join(ROOT, ".scratch", "motion-audit-2", "probe_needle_positions_r312.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
BASELINE = os.path.join(ROOT, "scripts", "frame_baseline.py")
PANE = os.path.join(ROOT, ".scratch", "motion-audit-2", "measure_pane_whitespace_r315.py")
INK = os.path.join(ROOT, ".scratch", "motion-audit-2", "measure_empty_states_r314.py")

MISSING = []


def sh(argv, cwd=None):
    p = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, close_fds=True)
    out, _ = p.communicate()
    return (out or b"").decode("utf-8", "replace"), p.returncode


def read(path):
    if not os.path.exists(path):
        MISSING.append(path)
        return u""
    h = io.open(path, encoding="utf-8")
    try:
        return h.read()
    finally:
        h.close()


def sect(name, body):
    return u"\n### %s\n%s\n" % (name, body.rstrip(u"\n"))


def main():
    parts = [u"# R315 账半的证据链（全部由脚本自印，不手填）\n"]

    v = read(VERIFY)
    keep = [l.strip() for l in v.splitlines() if re.match(
        u"^(\\[\\d/4\\]|ROUND_WARNING_GATE|ROUND_VERIFY|FRAME_GATE_|INSTALL_|SWIFT_|CAPTURED )", l.strip())]
    parts.append(sect(u"VERIFY_LEGS", u"\n".join(keep) or u"没读到四件套结论行"))
    gw = (re.findall(r"(?m)^ROUND_WARNING_GATE warnings=(\d+).*$", v) or [None])[-1]
    parts.append(sect(u"BUILD", u"WARNINGS=%s target=build-tests（取自 ROUND_WARNING_GATE 同一行）"
                      % (u"没解析到" if gw is None else gw)))

    c = read(CAP)
    reds = [l.strip() for l in c.splitlines() if u"error:-[" in l]
    icons = [l.strip() for l in c.splitlines() if l.startswith(u"CARD_INSET_ICON_FIRST")]
    capline = (re.findall(r"(?m)^CAPTURED .+$", c) or [u"没读到 CAPTURED 行"])[-1]
    pc, _rc = sh([sys.executable, PRECHECK])
    m566 = re.findall(u"M566 (ok|命中=\\d+|bad)", pc)
    parts.append(sect(u"CAPTURE", u"\n".join([
        capline,
        u"R315_REDS 红=%d 明细=%s" % (len(reds), u" ;; ".join(r[:140] for r in reds[:3])),
        u"R315_ICON_FIRST=%d 行 %s" % (len(icons), u" ;; ".join(icons[:4])),
        u"R315_M566 %s（针预检里那一臂的现读；撤名册 ⇒ 声明回到单行 ⇒ 针跟着回原形）"
        % (m566[-1] if m566 else u"没读到"),
        u"R315_LEGS 证人=撤帧那一笔：捕获卷零红 + CAPTURED 174 + 基线同一笔 update + M566 仍 ok"]) or u""))

    fr = [n for n in os.listdir(SHOTS) if n.endswith(u".png")] if os.path.isdir(SHOTS) else []
    parts.append(sect(u"FRAMES", u"FRAMES_ON_DISK=%d 目录=%s（只数 .png，日志不算帧）" % (len(fr), SHOTS)))

    pane, _rc = sh([sys.executable, PANE, SHOTS])
    pane_rows = [l for l in pane.splitlines() if l.startswith(u"PANE_INK settings-")]
    done = (re.findall(u"(?m)^PANE_INK_DONE .+$", pane) or [u"没读到 DONE 行"])[-1]
    fold = [l for l in pane.splitlines() if l.startswith(u"PANE_EDGE ")]
    parts.append(sect(u"PANE", u"\n".join(pane_rows + fold + [u"R315_PANE_DONE " + done]) or u"没读到留白读数"))

    ink, _rc2 = sh([sys.executable, INK, SHOTS])
    parts.append(sect(u"EMPTY_INK", u"\n".join(
        [l for l in ink.splitlines() if l.startswith(u"EMPTY_INK ")])))

    parts.append(sect(u"PRECHECK", u"\n".join(
        l for l in pc.splitlines() if l.startswith((u"NEEDLE_PRECHECK", u"ARM_TOTAL", u"TABLE_ROSTER")))))

    pr, _rc = sh([sys.executable, PROBE])
    parts.append(sect(u"NEEDLE_PROBE", u"\n".join(
        l for l in pr.splitlines() if l.startswith((u"NEEDLE_RANGE", u"NEEDLE_POS_STRICT"))) or u"没读到探针行"))

    ha, _rc = sh([sys.executable, HA])
    parts.append(sect(u"HIDDEN_ARMS", (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha) or [u"没读到"])[-1]))

    if os.path.isdir(SHOTS):
        bd, brc = sh([sys.executable, BASELINE, u"check", SHOTS, u"--against", u"working"])
        rows = [l.strip() for l in bd.splitlines() if l.startswith(u"FRAME_BASELINE_")]
        parts.append(sect(u"FRAME_BASELINE", u"\n".join(rows) +
                          u"\nFRAME_BASELINE_RC=%d 目录=%s" % (brc, SHOTS)))
    else:
        parts.append(sect(u"FRAME_BASELINE", u"SHOTS_DIR_ABSENT %s" % SHOTS))

    raw = read(FULL)
    if raw:
        cands = re.findall(r"(?m)^[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures?", raw)
        anch = re.findall(r"(?m)^Test Suite 'All tests' (?:passed|failed) at .*\n"
                          r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures?", raw)
        pick = anch[-1] if anch else (max(cands, key=lambda t: int(t[0])) if cands else None)
        vals = pick if pick else (u"?", u"?", u"?")
        parts.append(sect(u"SWIFT_SUMMARY",
                          u"SWIFT_SUMMARY 全量卷 Executed=%s skipped=%s failures=%s 候选=%d 通道=%s"
                          % (vals[0], vals[1], vals[2], len(cands), u"anchored" if anch else u"max-only")))
        suite = re.findall(r"(?m)^Test Suite 'UICaptureTests' (?:passed|failed) at .*\n"
                           r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures", raw)
        parts.append(sect(u"SWIFT_LEGS", u"UICAPTURE_TESTS ran=%s failed=%s（取自该卷自己的结论行）"
                          % ((suite[-1][0], suite[-1][2]) if suite else (u"?", u"?"))))
        perf = [l.strip()[:170] for l in raw.splitlines()
                if u"testImageComparisonCostStaysBounded" in l and (u"failed" in l or u"error" in l)]
        parts.append(sect(u"LOAD_RED", u"R315_LOAD_RED 命中=%d 例 %s" % (len(perf), u" ;; ".join(perf[:2]))))
    else:
        parts.append(sect(u"SWIFT_SUMMARY", u"FULL_LOG_ABSENT %s（四件套第 2 步还没落盘）" % FULL))

    body = u"".join(parts)
    h = io.open(OUT, "w", encoding="utf-8")
    try:
        h.write(body)
    finally:
        h.close()
    if MISSING:
        print(u"R315_CHAIN_MISSING %s" % u", ".join(MISSING))
    print(u"R315_CHAIN_WRITTEN 路径=%s 字节=%d 小节=%d" % (OUT, len(body), body.count(u"### ")))
    return 1 if MISSING else 0


if __name__ == u"__main__":
    sys.exit(main())
