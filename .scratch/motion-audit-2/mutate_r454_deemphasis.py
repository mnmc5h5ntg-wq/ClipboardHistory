#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R454 变异对照：弱化正文的对比度（回到 secondary / 完全变正文色，两把刀）。

- M1242 亮档 alpha 0.58→0.50（≈旧 secondary 128，亮档 3.95:1）⇒ 对比度判据红。
- M1243 亮档 alpha 0.58→1.00（=正文黑）⇒ 弱化消失：
  统一弱化色单测"没有弱化"那一格红（alpha=0 会变成透明，红在对比度，不是"弱化消失"）。
"""
import os, shutil, subprocess, sys, tempfile, time
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
POLICY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/DeEmphasisPresentation.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "DeEmphasisPresentationTests|testDeEmphasizedTextMeetsContrast|StrikethroughPresentationTests|testCheckedTasksDimTheirText"
LIGHT_ALPHA = '                : NSColor.black.withAlphaComponent(0.58)'
MUTATIONS = [
    ("M1242", "亮档弱化色回到 128（旧 secondary 3.95:1）", POLICY, LIGHT_ALPHA,
     '                : NSColor.black.withAlphaComponent(0.50)',
     ["testDeEmphasisColorMeetsBodyTextContrast", "低于 14pt 正文 4.5:1"]),
    ("M1243", "亮档弱化色变正文黑（弱化消失）", POLICY, LIGHT_ALPHA,
     '                : NSColor.black.withAlphaComponent(1.0)',
     ["testCheckedTasksDimTheirText", "完成态只在标记上"]),
]


def read(p):
    with open(p, encoding="utf-8") as h:
        return h.read()


def run(f):
    shots = tempfile.mkdtemp(prefix="r454-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        p = subprocess.run(["swift", "test", "--filter", f], cwd=ROOT,
                           capture_output=True, text=True, env=env, timeout=1800)
        out = p.stdout + p.stderr
        rc = p.returncode
    except subprocess.TimeoutExpired as e:
        raw = e.stdout or b""
        out = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else (raw or "")
        rc = -1
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in l for l in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    return ("CAUGHT" if rc != 0 else "ESCAPED"), out, failed


def main():
    original = read(POLICY)
    for mid, _d, path, old, _n, _x in MUTATIONS:
        c = read(path).count(old)
        if c != 1:
            raise SystemExit("预检中止：%s 针命中 %d 次" % (mid, c))
    code, out, _ = run(FILTER)
    if code != "ESCAPED":
        raise SystemExit("预检失败 %s %s\n%s" % (FILTER, code, out[-1500:]))
    print("预检 OK " + FILTER)
    caught = wrong = 0
    for mid, desc, path, old, new, needles in MUTATIONS:
        stamp = time.time() + 2
        open(path, "w", encoding="utf-8").write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and new in read(path)
        try:
            code, out, failed = run(FILTER)
        finally:
            open(path, "w", encoding="utf-8").write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(any(n in l for l in failed) or n in out for n in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))
    clean = read(POLICY) == original
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R454_DEEMPHASIS_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
