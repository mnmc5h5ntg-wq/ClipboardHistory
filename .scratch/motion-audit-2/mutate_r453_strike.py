#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R453 变异对照：删除线（文字弱化 / 自绘线，两把刀）。

- M1240 删除段的文字不弱化（颜色条件去掉 struck）⇒ 帧判据灰度差≈0、单测两色相同 ⇒ CAUGHT。
- M1241 两段都弱化（struck 恒真）⇒ 删除段与正常段同色：帧判据差≈0、单测两色相同 ⇒ CAUGHT。
  删除线本身由 AppKit 的 `.strikethroughStyle` 画：两版"去掉自绘线"的刀都 ESCAPED，
  且字形间隙列仍被填（9/9）—— 证明线一直在，自绘是冗余的；间隙列只作前提证人。
"""
import os, shutil, subprocess, sys, tempfile, time
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
PRESENT = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "StrikethroughPresentationTests|testStruckTextIsDeEmphasized"
COLOR_NEEDLE = '''        } else if struck {
            baseColor = struckTextColor
        } else {'''
STRIKE_NEEDLE = '        let struck = run.marks.contains(.strikethrough)'
MUTATIONS = [
    ("M1240", "删除段文字不弱化（颜色条件去掉 struck）", PRESENT, COLOR_NEEDLE,
     '''        } else if false {
            baseColor = struckTextColor
        } else {''',
     ["testStruckRunColorDiffersFromPlain", "颜色相同"]),
    ("M1241", "两段都弱化（struck 恒真）", PRESENT, STRIKE_NEEDLE,
     '        let struck = true',
     ["testStruckRunColorDiffersFromPlain", "颜色相同"]),
]


def read(p):
    with open(p, encoding="utf-8") as h:
        return h.read()


def run(f):
    shots = tempfile.mkdtemp(prefix="r453-mut-shots-")
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
    originals = {p: read(p) for p in (PRESENT,)}
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
        original = originals[path]
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
    clean = all(read(p) == originals[p] for p in originals)
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R453_STRIKE_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
