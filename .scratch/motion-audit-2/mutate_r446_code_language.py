#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R446 变异对照：代码块语言标签（不画 / 放不下也画，两把刀）。

两把刀打的是两条不同的判据：
- M1226 去掉背景层的绘制调用 ⇒ 像素判据 `testCodeBlocksShowTheirLanguage` 红（右区无墨）；
- M1227 让 `fits` 恒真（长行也画）⇒ 纯策略判据 `testTagIsSkippedWhenTheFirstLineWouldCollide`
  红。像素夹具的第一行很短、两臂都放得下，所以这条守卫只有单测看得见 —— 表里写明，
  不假装像素判据盖住了它。
"""
import os, shutil, subprocess, sys, tempfile, time
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/ChineseTextContextMenu.swift")
TAG = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/CodeLanguageTag.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "CodeLanguageTagTests|testCodeBlocksShowTheirLanguage"
DRAW_NEEDLE = '''        drawCodeBlockBackgrounds(in: rect)
        drawCodeLanguageTags(in: rect)'''
FITS_NEEDLE = '        return codeRightEdge + minimumGap <= containerWidth - rightInset - width(of: label)'
MUTATIONS = [
    ("M1226", "背景层不再画语言标签（调用被删）", VIEW, DRAW_NEEDLE,
     '        drawCodeBlockBackgrounds(in: rect)',
     ["testCodeBlocksShowTheirLanguage", "没有把围栏里的语言"]),
    ("M1227", "放不下也画（fits 恒真）", TAG, FITS_NEEDLE,
     '        return true',
     ["testTagIsSkippedWhenTheFirstLineWouldCollide"]),
]


def read(p):
    with open(p, encoding="utf-8") as h:
        return h.read()


def run(f):
    shots = tempfile.mkdtemp(prefix="r446-mut-shots-")
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
    originals = {p: read(p) for p in (VIEW, TAG)}
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
    print("R446_CODE_LANGUAGE_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
