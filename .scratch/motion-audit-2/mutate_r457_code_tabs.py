#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R457 变异对照：代码块制表位（撤修复 / 半宽 / 不清默认停止位，三把刀）。

- M1251 撤掉 codeBlock 的制表位分支 ⇒ 回到 TextKit 默认 28pt 一跳 ⇒ 判据红。
- M1252 间隔改成 2 个空格宽 ⇒ 一级落 16.07pt ⇒ 判据红。
- M1253 只设间隔、不清默认 12 个显式停止位 ⇒ 28pt 仍优先 ⇒ 判据红。
"""
import os, shutil, subprocess, sys, tempfile, time
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
PRES = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "testCodeBlockTabsMatchFourSpaces"
BLOCK = '''        if case .codeBlock = block.kind {
            let advance = ("0" as NSString).size(withAttributes: [.font: codeFont]).width
            style.tabStops = []
            style.defaultTabInterval = advance * 4
        }'''
MUTATIONS = [
    ("M1251", "撤掉代码块制表位修复（回默认 28pt 一跳）", PRES, BLOCK,
     '        // R457 制表位修复撤掉',
     ["制表符一级缩进在", "代码块的制表间隔是"]),
    ("M1252", "制表间隔改成 2 个空格宽", PRES,
     '            style.defaultTabInterval = advance * 4',
     '            style.defaultTabInterval = advance * 2',
     ["制表符一级缩进在", "应为 4×"]),
    ("M1253", "只设间隔、不清默认制表位", PRES,
     '            style.tabStops = []',
     '            // 保留默认制表位',
     ["制表符一级缩进在", "显式制表位"]),
]


def read(p):
    with open(p, encoding="utf-8") as h:
        return h.read()


def run(f):
    shots = tempfile.mkdtemp(prefix="r457-mut-shots-")
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
    originals = {p: read(p) for p in (PRES,)}
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
    print("R457_CODE_TABS_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
