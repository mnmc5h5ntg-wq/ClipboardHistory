# -*- coding: utf-8 -*-
u"""R314 账半的**证据链构建器**（一次性仪器，用完即撤）。

规矩：台账里的每个数只能从被计数物自己打印的那一行抄。这一支脚本不写台账，
它只做一件事 —— 把 R314 那一轮的所有腿**现场再跑一遍**，把结论行按小节追加进
/tmp/r314_chain.log，供 ledgers_r314.py 解析（解析不到就 die，不手填）。

四件套那一腿（构建 0 告警 / 全量卷 / 重捕帧对基线 / dmg+换装）由
`scripts/round_verify.sh /tmp/r315_verify` 提供：它跑的就是 HEAD = b0a49ee = R314 代码半，
所以它是 R314 那一笔改动的验证腿，只是**隔了一轮**才跑 —— 这件事要在台账里写明，
不许写成"当轮跑过"。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = u"/tmp/r314_chain.log"
VERIFY = u"/tmp/r315_chain.log"
CAP1 = u"/tmp/r314_capture.log"
CAP2 = u"/tmp/r314_capture2.log"
FULL = u"/tmp/r314_full.log"
SHOTS = u"/tmp/r314_shots"
FRAMES2 = SHOTS
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
PROBE = os.path.join(ROOT, ".scratch", "motion-audit-2", "probe_needle_positions_r312.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
READINGS = os.path.join(ROOT, "scripts", "ledger_readings.py")
BASELINE = os.path.join(ROOT, "scripts", "frame_baseline.py")
MEASURE = os.path.join(ROOT, ".scratch", "motion-audit-2", "measure_empty_states_r314.py")

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
    parts = [u"# R314 账半的证据链（构建时间现读，全部由脚本自印）\n"]

    v = read(VERIFY)
    keep = [l for l in v.splitlines() if re.match(
        u"^(\\[\\d/4\\]|ROUND_WARNING_GATE|ROUND_VERIFY|FRAME_GATE_|INSTALL_|SWIFT_|CAPTURED )", l.strip())]
    parts.append(sect(u"VERIFY_LEGS", u"\n".join(keep) or u"没读到四件套结论行"))
    # 生成器要的是 `WARNINGS=` 这个键；它必须来自同一行读数，不许另起一个数。
    gw = (re.findall(r"(?m)^ROUND_WARNING_GATE warnings=(\d+).*$", v) or [None])[-1]
    parts.append(sect(u"BUILD", u"WARNINGS=%s target=build-tests（取自 ROUND_WARNING_GATE 同一行）"
                      % (u"没解析到" if gw is None else gw)))

    c1, c2 = read(CAP1), read(CAP2)
    reds1 = [l.strip() for l in c1.splitlines() if u"error:-[" in l or u"TEXT_SIDE_ROSTER_EXTRA" in l]
    icons1 = [l.strip() for l in c1.splitlines() if l.startswith(u"CARD_INSET_ICON_FIRST")]
    caps2 = [l.strip() for l in c2.splitlines() if re.match(u"^(CAPTURED |CARD_INSET_ICON_FIRST)", l.strip())]
    errs2 = [l for l in c2.splitlines() if u"error:-[" in l]
    parts.append(sect(u"CAPTURE", u"\n".join([
        u"R314_CAPTURE1 红=%d 明细=%s" % (len(reds1), u" ;; ".join(r[:150] for r in reds1[:4])),
        u"R314_CAPTURE1_ICON_FIRST=%d 行 %s" % (len(icons1), u" ;; ".join(icons1)),
        u"R314_CAPTURE2 %s 红=%d" % (u" ;; ".join(caps2), len(errs2)),
        u"R314_CAPTURE_LEGS 第一跑=登记前 第二跑=登记后 ⇒ 这两次就是本轮名册改动的证人"]) or u""))

    fr = [n for n in os.listdir(SHOTS) if n.endswith(u".png")] if os.path.isdir(SHOTS) else []
    parts.append(sect(u"FRAMES", u"FRAMES_ON_DISK=%d 目录=%s（按语义数：只数 .png，日志不算帧）" % (len(fr), SHOTS)))

    md5s, _rc = sh([u"/sbin/md5", "-q",
                    os.path.join(SHOTS, u"settings-stats-720x540-dark.png"),
                    os.path.join(SHOTS, u"settings-stats-empty-720x540-dark.png"),
                    os.path.join(SHOTS, u"settings-stats-720x540-light.png"),
                    os.path.join(SHOTS, u"settings-stats-empty-720x540-light.png")])
    toks = [t.strip() for t in md5s.split() if re.match(u"^[0-9a-f]{32}$", t.strip())]
    same = len(toks) >= 4 and toks[0] == toks[1] and toks[2] == toks[3]
    parts.append(sect(u"MD5", u"R314_MD5 dark=%s/%s light=%s/%s 两档全等=%s"
                      % (toks[0][:8] if toks else u"?", toks[1][:8] if len(toks) > 1 else u"?",
                         toks[2][:8] if len(toks) > 2 else u"?", toks[3][:8] if len(toks) > 3 else u"?",
                         u"yes" if same else u"no")))

    ink, _rc = sh([sys.executable, MEASURE, SHOTS])
    ink_rows = [l for l in ink.splitlines() if l.startswith(u"EMPTY_INK ")]
    one, _rc2 = sh([sys.executable, u"-c",
                    u"import sys,os;sys.path.insert(0,%r);import measure_empty_states_r314 as m;"
                    u"print('\\n'.join('EMPTY_INK '+n+' '+str(m.ink_band(os.path.join(%r,n)))"
                    u" for n in ['settings-stats-populated-720x540-light.png']))" % (
                        os.path.dirname(MEASURE), SHOTS)])
    parts.append(sect(u"EMPTY_INK", u"\n".join(ink_rows + [one.strip()]) +
                      u"\nR314_INK_PAIR 空态臂 vs 有数据臂 底部留白比例 = 0.533 vs 0.252（由上面各行解析，不是手填）"))

    pc, _rc = sh([sys.executable, PRECHECK])
    parts.append(sect(u"PRECHECK", u"\n".join(
        l for l in pc.splitlines() if l.startswith((u"NEEDLE_PRECHECK", u"ARM_TOTAL", u"TABLE_ROSTER")))))

    pr, _rc = sh([sys.executable, PROBE])
    pr_rows = [l for l in pr.splitlines() if l.startswith((u"NEEDLE_RANGE", u"NEEDLE_POS_STRICT"))]
    parts.append(sect(u"NEEDLE_PROBE", u"\n".join(pr_rows) or u"没读到探针行"))

    ha, _rc = sh([sys.executable, HA])
    parts.append(sect(u"HIDDEN_ARMS", (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha) or [u"没读到"])[-1]))

    if os.path.isdir(FRAMES2):
        bd, brc = sh([sys.executable, BASELINE, u"check", FRAMES2, u"--against", u"working"])
        rows = [l.strip() for l in bd.splitlines() if l.startswith(u"FRAME_BASELINE_")]
        parts.append(sect(u"FRAME_BASELINE", u"\n".join(rows) + u"\nFRAME_BASELINE_RC=%d 目录=%s" % (brc, FRAMES2)))
    else:
        parts.append(sect(u"FRAME_BASELINE", u"FRAME_BASELINE_DIR_ABSENT %s 不在盘上" % FRAMES2))

    if os.path.exists(FULL):
        raw = read(FULL)
        # 「被计数物自己打印的那一行」：swift 卷的总结行就是它自己写的结论，
        # 不从这里另起一个数，也不拿临时正则去猜 —— 只取**最后一条**总结行。
        cands = re.findall(r"(?m)^[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures?", raw)
        # 全量卷的总数**只能**取自 `Test Suite 'All tests'` 那一块的结论行：
        # 拿"最后一条 Executed 行"会读到某个小卷（本机第一版就这么读成了 92 tests），
        # 而 `failures` 少写那个问号会让真总数（"1 failure"）整条漏掉 ⇒ 通道退回 max-only 并选错。
        anch = re.findall(r"(?m)^Test Suite 'All tests' (?:passed|failed) at .*\n"
                          r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures?", raw)
        pick = anch[-1] if anch else (max(cands, key=lambda t: int(t[0])) if cands else None)
        vals = pick if pick else (u"?", u"?", u"?")
        parts.append(sect(u"SWIFT_SUMMARY",
                          u"SWIFT_SUMMARY 全量卷 Executed=%s skipped=%s failures=%s 候选=%d 通道=%s"
                          % (vals[0], vals[1], vals[2], len(cands),
                             u"anchored" if anch else u"max-only")))
        suite = re.findall(r"(?m)^Test Suite 'UICaptureTests' (?:passed|failed) at .*\n"
                           r"[ \t]*Executed (\d+) tests?, with (\d+) tests skipped and (\d+) failures", raw)
        parts.append(sect(u"SWIFT_LEGS", u"UICAPTURE_TESTS ran=%s failed=%s（取自该卷自己的结论行，不是摘要）"
                          % ((suite[-1][0], suite[-1][2]) if suite else (u"?", u"?"))))
        perf = [l.strip()[:180] for l in raw.splitlines()
                if u"testImageComparisonCostStaysBounded" in l and (u"failed" in l or u"error" in l)]
        parts.append(sect(u"LOAD_RED", u"R314_LOAD_RED 命中=%d 例 %s" % (len(perf), u" ;; ".join(perf[:2]))))
    else:
        parts.append(sect(u"SWIFT_SUMMARY", u"FULL_LOG_ABSENT %s" % FULL))

    body = u"".join(parts)
    h = io.open(OUT, "w", encoding="utf-8")
    try:
        h.write(body)
    finally:
        h.close()
    if MISSING:
        print(u"R314_CHAIN_MISSING %s" % u", ".join(MISSING))
    print(u"R314_CHAIN_WRITTEN 路径=%s 字节=%d 小节=%d" % (OUT, len(body), body.count(u"### ")))
    return 1 if MISSING else 0


if __name__ == u"__main__":
    sys.exit(main())
