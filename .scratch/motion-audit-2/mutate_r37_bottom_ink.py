#!/usr/bin/env python3
"""R37 变异对照：底行墨这把尺（参照点 / 读数来源 / 正对照 / 两条线的配对）。

R36 查出这把尺量的是"底行 vs 左上角那一个像素"的色差（U-60），
而那条正对照从写下那天起读的就是假 100%。这一轮把它改对，
所以电池要问的是四件**互不相同**的事 —— 每一件都必须有一条会红的判据：

  M169 尺恒读 0                     ⇒ 正对照帧必须红（"这把尺瞎了"）
  M170 参照点改回左上角那一个像素    ⇒ 合成真值表必须红（那张"只有角点不同"的图）
  M171 读数来源换回 raw rep         ⇒ content-min 那把锁必须红（PNG 43.4% / raw 3.4%）
  M172 一张 mustFit 夹具被压矮       ⇒ mustFit 必须红（R22 的原意，这次是真的在判裁切）
  M173 对照帧不再被裁（外框抬回 74） ⇒ 正对照必须红（对照物失效不能悄悄溜过去）
  M174 mustFit 的上限抬到 0.10       ⇒ 配对那条必须红（两条线一旦交叉，判据与正对照互相取消）

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r37-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

# 两条判据一起跑：尺的合成分支与真帧分支各钉一半
FILTER = "UICaptureTests/(testCaptureKeyViews|testBottomInkRulerUsesTheRowOwnBackground)"

RETURN_RATIO = """        return Double(ink) / Double(width)
    }"""
CORNER_REF = "        let r0 = channel(0), g0 = channel(1), b0 = channel(2)"
SOURCE_PNG = "        let measured: NSBitmapImageRep = NSBitmapImageRep(data: data) ?? rep"
RECEIPT = 'results.append(Fixture("receipt-line", NSSize(width: 430, height: 56), contentMustFit: true)'
CONTROL_FIXTURE = 'Fixture("row-clipped-control", NSSize(width: 300, height: 58))'
MUST_FIT_FLOOR = "        static let fixtureBottomInkMaxFraction: Double = 0.02"

MUTATIONS = [
    ("M169", "尺恒读 0（把它弄瞎）", RETURN_RATIO,
     "        return 0  // MUTANT\n    }", "这把尺**瞎了**"),
    ("M170", "参照点改回左上角那一个像素（U-60 原样）", CORNER_REF,
     "        let r0 = Int(bytes[0]), g0 = Int(bytes[1]), b0 = Int(bytes[2])  // MUTANT",
     "参照点又变回"),
    ("M171", "读数来源换回 raw rep（不是产物）", SOURCE_PNG,
     "        let measured: NSBitmapImageRep = rep  // MUTANT",
     "尺读的不是落盘那张图"),
    ("M172", "一张 mustFit 夹具被压矮（真的裁到内容）", RECEIPT,
     RECEIPT.replace("height: 56", "height: 40"),
     "这张夹具正在裁自己的内容"),
    ("M173", "对照帧不再被裁（外框抬回自然高度）", CONTROL_FIXTURE,
     CONTROL_FIXTURE.replace("height: 58", "height: 74"),
     "这把尺**瞎了**"),
    ("M174", "mustFit 的上限抬到 0.10（越过正对照的下限）", MUST_FIT_FLOOR,
     MUST_FIT_FLOOR.replace("= 0.02", "= 0.10"),
     "必须**低于**正对照的下限"),
]


def run():
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        code = "BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"
        return code, out, []
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
        raise SystemExit(f"注入中止：那段话出现 {n} 次，不是 1 次 —— 电池与代码脱节，先修电池\n  {old[:120]}")
    with open(HARNESS, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(original):
    with open(HARNESS, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(HARNESS, encoding="utf-8").read() == original


def main():
    wanted = set(sys.argv[1:])
    print("预检：两条判据都必须是绿的（红着开始就没有一支测得准）")
    code, out, failed = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-900:])
    print("预检 OK：", code)

    results = []
    for mid, desc, old, new, needle in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(old, new)
        code, out, failed = run()
        red_in_right_place = needle in out
        ok = restore(original)
        results.append((mid, code, "yes" if red_in_right_place else "NO", "yes" if ok else "NO",
                        ",".join(f.split(".")[-1] for f in failed)))
        print(f"{mid} {desc} ⇒ {code} 红得对={red_in_right_place} 红在 {failed}")
        if code != "CAUGHT" or not red_in_right_place:
            print(out[-1000:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    dirty = [r for r in results if r[3] != "yes"]
    bad = [r for r in results if r[1] != "CAUGHT"]
    print(f"未被抓到/未真跑={len(bad)}  还原不干净={len(dirty)}")
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no ⇒ 工作区脏了")
    if bad:
        raise SystemExit(f"MUTATION_UNCAUGHT={len(bad)}")


if __name__ == "__main__":
    main()
