#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R42 变异对照：`ReceiptLine` 那句 `.transition` 的供电，五种坏法各该红一次。

  M194 导出反馈那条回执的驱动被删掉        ⇒ 红在"门控状态没出现在任何一条键里"
  M195 导出/导入历史那条回执的驱动被删掉    ⇒ 同上，红的是 archiveMessage 那一格
  M196 排除名单**新加的那一条**驱动被删掉   ⇒ 红在"名单里少了一个"还是"没驱动"？——实测才知道，
                                              所以这一支的 needle 只能从 --measure 的日志里抄
  M197 键换成**别的**状态（编译得过、看着也像接了动画） ⇒ 必须判成没驱动
  M198 冒出一条没登记、也没驱动的回执        ⇒ 红在名单两边不等（"外面冒出来红"那一半）

这一轮的电池**换了判法**（R41 的账：needle 第三次靠推理写，结果 `红得不对=2`）：
  ① 先跑 `--measure`：注入、跑、把**实际的失败消息原文**打出来，不判红得对不对；
  ② 把抄下来的片段填进下面的 needle，再跑正式的一遍；
  ③ 判据从"needle 出现在整份日志里"改成"**needle 出现在某条失败消息里**"——
     整份日志里哪都有可能出现那句话（比如它写在源码注释的打印里），那不算红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SETTINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "MotionDriverTests"

# R378：这两条驱动现在住在更深的缩进里，旧针把注释也带上了（注释后来被改写 ⇒ 针腐烂）。
# 针改成**动作那一行**：它才是"驱动在不在"的唯一对象，注释不是。
EXPORT_DRIVER = """                    .animation(MotionCatalog.animation(for: .contentFade), value: exportMessage == nil)"""
ARCHIVE_DRIVER = """                    .animation(MotionCatalog.animation(for: .contentFade), value: archiveMessage == nil)"""
EXCLUSION_DRIVER = """                    .animation(MotionCatalog.animation(for: .contentFade),
                               value: exclusionReceipt == nil)"""
# R381：旧锚点 `if showExportAlert {` 在 R43 就被删了（那处 alert 早已改成 ReceiptLine），
# 所以 M198 注入后编译不过。改成在**当前**的导出回执分支前插一条未登记的回执。
ARCHIVE_GATE = "                        if let message = exportMessage {"

# needle：**从 --measure 的失败消息原文里抄**（跑法见文件末注），不许从代码里推。
# 实测到的四支 XCTAssertTrue 全部红在 MotionDriverTests.swift:107，
# 而区分它们的是消息里那个**名单**：`… 的键里：["let message = exportMessage"]` 之类。
M194_NEEDLE = '键里：["let message = exportMessage"]'
M195_NEEDLE = '键里：["let archiveMessage"]'
M196_NEEDLE = '键里：["let exclusionReceipt"]'
# R381：守卫把 `if true` 里那条回执的门控式子读成 "true"（名单排过序，它是最后一项）。
M198_NEEDLE = '"true"]' 
MUTATIONS = [
    ("M194", "导出反馈那条回执的驱动被删掉", SETTINGS, EXPORT_DRIVER, "/* MUTANT */",
     [M194_NEEDLE]),
    ("M195", "导出/导入历史那条回执的驱动被删掉", SETTINGS, ARCHIVE_DRIVER, "/* MUTANT */",
     [M195_NEEDLE]),
    ("M196", "排除名单新加的那一条驱动被删掉", SETTINGS, EXCLUSION_DRIVER, "/* MUTANT */",
     [M196_NEEDLE]),
    ("M197", "键换成别的状态（看着像接了动画）", SETTINGS, EXPORT_DRIVER,
     EXPORT_DRIVER.replace("value: exportMessage == nil", "value: archiveMessage == nil"),
     [M194_NEEDLE]),
    ("M198", "冒出一条没登记、也没驱动的回执", SETTINGS, ARCHIVE_GATE,
     '                        if true {\n'
     '                            ReceiptLine(text: "MUTANT：未登记的回执") {}\n'
     '                        }\n' + ARCHIVE_GATE,
     [M198_NEEDLE]),
]


def failure_messages(out):
    """只看**失败消息**那一层。
    两种格式都得认（第一版只认前者，于是 M194–M197 的"实际红消息"数是 0，
    差点被我当成"没有失败消息可抄"）：
      XCTAssertEqual 走 `XCTAssertEqual failed: ("a") is not equal to ("b")`
      XCTAssertTrue  走 `XCTAssertTrue failed - <人话>`  ← 冒号在这里不存在
    """
    return [line for line in out.splitlines()
            if ("error: -[" in line and " failed" in line) or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1500:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        messages = failure_messages(out)
        hit = [n for n in needles if any(n in m for m in messages)]
        right = bool(needles) and len(hit) == len(needles)
        ok = restore(path, original)
        results.append((mid, code, "yes" if right else ("MEASURE" if measure else "NO"),
                        "yes" if ok else "NO", ",".join(f.split(".")[-1] for f in failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure:
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:400])
        elif not right or code != "CAUGHT":
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:400])
            print(out[-800:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] not in ("yes", "MEASURE")]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


if __name__ == "__main__":
    main()
