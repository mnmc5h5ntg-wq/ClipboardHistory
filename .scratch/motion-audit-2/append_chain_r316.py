# -*- coding: utf-8 -*-
u"""R316 账半的证据链（一次性仪器）。只跑只印，不写台账。

本轮特有的一格：改动全在判据侧 ⇒ **产品像素一张都不该动**。
这一条不靠"我觉得没动"，靠两遍帧目录逐字节对拍（@RPREVTAG@ 那遍 vs 本轮那遍）。
另有一格是重跑 M566：针换了落点之后必须重新拿到它自己那条 CAUGHT，不能引用上一轮的读数。
"""
import hashlib
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = u"/tmp/r316_chain.log"
VERIFY = u"/tmp/r319_chain.log"
BUILD = u"/tmp/r318_build.log"
CAP = u"/tmp/r317_capture.log"
SHOTS_NEW = u"/tmp/r317_shots"
SHOTS_OLD = u"/tmp/r316_shots"
FULL = u"/tmp/r319_verify/full.log"
KNIFE = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r101.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
PROBE = os.path.join(ROOT, ".scratch", "motion-audit-2", "probe_needle_positions_r312.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
BASELINE = os.path.join(ROOT, "scripts", "frame_baseline.py")
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


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parts = [u"# R316 账半的证据链（全部由脚本自印）\n"]

    b = read(BUILD)
    w = len([l for l in b.splitlines() if u"warning:" in l])
    parts.append(sect(u"BUILD", u"WARNINGS=%d target=build-tests（现数 /tmp/r318_build.log）" % w))

    v = read(VERIFY)
    keep = [l.strip() for l in v.splitlines() if re.match(
        u"^(\\[\\d/4\\]|ROUND_WARNING_GATE|ROUND_VERIFY|FRAME_GATE_|INSTALL_|CAPTURED )", l.strip())]
    parts.append(sect(u"VERIFY_LEGS", u"\n".join(keep) or u"四件套还在跑"))

    c = read(CAP)
    reds = [l.strip() for l in c.splitlines() if u"error:-[" in l]
    icons = [l.strip() for l in c.splitlines() if l.startswith(u"CARD_INSET_ICON_FIRST")]
    capline = (re.findall(r"(?m)^CAPTURED .+$", c) or [u"没读到 CAPTURED 行"])[-1]
    switch = (re.findall(r"(?m)^CARD_INSET_ROSTER_SWITCH .+$", c) or [u"没读到开关那一行"])[-1]
    kr, krc = sh([sys.executable, KNIFE, u"M566"])
    kt = (re.findall(r"(?m)^MUTATE_TABLE .+$", kr) or [u"没读到刀表汇总行"])[-1]
    pc, _ = sh([sys.executable, PRECHECK])
    m566 = re.findall(u"M566 (ok|命中=\\d+)", pc)
    parts.append(sect(u"CAPTURE", u"\n".join([
        capline,
        u"R316_REDS 红=%d 明细=%s" % (len(reds), u" ;; ".join(r[:120] for r in reds[:2])),
        u"R316_ICON_FIRST=%d 行 %s" % (len(icons), u" ;; ".join(icons[:3])),
        switch,
        u"R316_KNIFE %s rc=%d" % (kt, krc),
        u"R316_M566 %s" % (m566[-1] if m566 else u"没读到")])))

    fr = [n for n in os.listdir(SHOTS_NEW) if n.endswith(u".png")] if os.path.isdir(SHOTS_NEW) else []
    same = diff = miss = 0
    for n in sorted(fr):
        a, b2 = os.path.join(SHOTS_NEW, n), os.path.join(SHOTS_OLD, n)
        if not os.path.exists(b2):
            miss += 1
        elif md5(a) == md5(b2):
            same += 1
        else:
            diff += 1
    parts.append(sect(u"FRAMES", u"FRAMES_ON_DISK=%d 目录=%s" % (len(fr), SHOTS_NEW)))
    parts.append(sect(u"FRAMECMP", u"R316_FRAME_CMP 同图=%d 变图=%d 缺对照=%d（本轮改动全在判据侧 ⇒ 变图必须是 0）"
                      % (same, diff, miss)))

    parts.append(sect(u"PRECHECK", u"\n".join(
        l for l in pc.splitlines() if l.startswith((u"NEEDLE_PRECHECK", u"ARM_TOTAL", u"TABLE_ROSTER")))))
    pr, _ = sh([sys.executable, PROBE])
    parts.append(sect(u"NEEDLE_PROBE", u"\n".join(
        l for l in pr.splitlines() if l.startswith(u"NEEDLE_RANGE")) or u"没读到"))
    ha, _ = sh([sys.executable, HA])
    parts.append(sect(u"HIDDEN_ARMS", (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha) or [u"没读到"])[-1]))

    bd, brc = sh([sys.executable, BASELINE, u"check", SHOTS_NEW, u"--against", u"working"])
    parts.append(sect(u"FRAME_BASELINE", u"\n".join(
        l.strip() for l in bd.splitlines() if l.startswith(u"FRAME_BASELINE_"))
        + u"\nFRAME_BASELINE_RC=%d" % brc))

    raw = read(FULL)
    if raw:
        anch = re.findall(r"(?m)^Test Suite 'All tests' (?:passed|failed) at .*\n"
                          r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures?", raw)
        pick = anch[-1] if anch else (u"?", u"?", u"?")
        parts.append(sect(u"SWIFT_SUMMARY",
                          u"SWIFT_SUMMARY 全量卷 Executed=%s skipped=%s failures=%s 通道=%s"
                          % (pick[0], pick[1], pick[2], u"anchored" if anch else u"none")))
        suite = re.findall(r"(?m)^Test Suite 'UICaptureTests' (?:passed|failed) at .*\n"
                           r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures", raw)
        parts.append(sect(u"SWIFT_LEGS", u"UICAPTURE_TESTS ran=%s failed=%s"
                          % ((suite[-1][0], suite[-1][2]) if suite else (u"?", u"?"))))
        perf = [l for l in raw.splitlines() if u"testImageComparisonCostStaysBounded" in l
                and (u"failed" in l or u"error" in l)]
        parts.append(sect(u"LOAD_RED", u"R316_LOAD_RED 命中=%d" % len(perf)))
    else:
        parts.append(sect(u"SWIFT_SUMMARY", u"FULL_LOG_ABSENT %s（四件套第 2 步未落盘）" % FULL))

    body = u"".join(parts)
    io.open(OUT, "w", encoding="utf-8").write(body)
    if MISSING:
        print(u"R316_CHAIN_MISSING %s" % u", ".join(MISSING))
    print(u"R316_CHAIN_WRITTEN 字节=%d 小节=%d 同图=%d 变图=%d" % (len(body), body.count(u"### "), same, diff))
    return 1 if (MISSING or diff) else 0


if __name__ == u"__main__":
    sys.exit(main())
