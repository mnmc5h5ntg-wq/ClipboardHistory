#!/usr/bin/env python3
"""R38 变异对照：把"两台机器的读数当另一台机器的地板"换掉之后，两支新锁各该咬一次。

  M175 底行墨的读数来源换回 raw rep        ⇒ **恒等式**必须红（判据读数 ≠ 从 PNG 重算的那一份）
  M176 资格判据把所有探针都放行（可判对象归零） ⇒ **从表推导的地板**必须红（"对象快被清空了"）

R37 那一版的第二把锁写的是"`content-min` 至少读到 20%"，本机 43.4% 通过、
runner 上同一帧只有 9.3% ⇒ 红在机器差异上（run 38485603211，闸门第一次真跑就把它指名了）。
恒等式不依赖"这台机器的帧长什么样"，所以它两边都成立，而 M175 照样抓得住。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r38-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

FILTER = "UICaptureTests/(testCaptureKeyViews|testProbesDoNotSitOnVibrantColumns)"

SOURCE_PNG = "        let measured: NSBitmapImageRep = NSBitmapImageRep(data: data) ?? rep"
ELIGIBLE = """        func eligible(_ probe: InkProbe) -> Bool {
            !(capability.settingsFamilyIsBlank && probe.fixture.hasPrefix("settings-"))
        }"""

MUTATIONS = [
    ("M175", "读数来源换回 raw rep（判据不再读产物）", SOURCE_PNG,
     "        let measured: NSBitmapImageRep = rep  // MUTANT",
     "尺读的不是产物"),
    ("M176", "资格判据把每一条都放行（可判对象归零）", ELIGIBLE,
     "        func eligible(_ probe: InkProbe) -> Bool { false }  // MUTANT",
     "对象快被清空了"),
]


def run():
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(old, new):
    text = open(HARNESS, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"注入中止：那段话出现 {n} 次，不是 1 次 —— 电池与代码脱节\n  {old[:120]}")
    with open(HARNESS, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(original):
    with open(HARNESS, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(HARNESS, encoding="utf-8").read() == original


def main():
    wanted = set(sys.argv[1:])
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-900:])
    print("预检 OK")
    results = []
    for mid, desc, old, new, needle in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(old, new)
        code, out, failed = run()
        right = needle in out
        ok = restore(original)
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO",
                        ",".join(f.split(".")[-1] for f in failed)))
        print(f"{mid} {desc} ⇒ {code} 红得对={right} 红在 {failed}")
        if code != "CAUGHT" or not right:
            print(out[-900:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print(f"未被抓到/未真跑={len(bad)}  还原不干净={len(dirty)}")
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad:
        raise SystemExit(f"MUTATION_UNCAUGHT={len(bad)}")


if __name__ == "__main__":
    main()
