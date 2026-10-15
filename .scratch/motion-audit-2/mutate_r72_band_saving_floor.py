#!/usr/bin/env python3
"""R72 的变异对照：把"带捕获必须省 2 倍"降到"严格更便宜"之后，牙还在不在。

被判的那条判据：`MotionFilmstripTests/testBandCaptureIsCheaperAndStillSeesTheMotion`。
它有四组断言：① 帧高必须变小、② 带宽必须不变、③ 带那一臂必须严格更便宜、④ 首尾差必须装得下变更。
R72 只把 ③ 从"省 ≥2 倍"降到"严格更便宜"，因为那个 2 是本机数
（runner 实测 1.70×：带 26.0ms / 整窗 44.4ms —— 真实存在，只是不到 2）。

M384 是这一格要拦的那族错：**`captureRect` 变成空操作**（两臂都抓整窗）。
它必须同时红在 ①（帧高没变小）与 ③（成本没变小）。

**特意不收进计数的一刀**（M385）：把淡入时钟的睡眠节拍从 0.004 改回 0.02。
本机读数会从 `采样≈4ms 可分数段=37` 退到 `≈20ms 可分数段=7`，两档都仍然"合格" ⇒
**本地没有判别力**，只有 runner 上才有（那里 4ms→16ms 会跨过 50ms 那条线）。
按 M168 的先例记成"由 runner 判"，不混进 CAUGHT/ESCAPED。

用法：`python3 .scratch/motion-audit-2/mutate_r72_band_saving_floor.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
LOCK = "/tmp/r72_mutation.lock"
BAND = "testBandCaptureIsCheaperAndStillSeesTheMotion"
FILTER = "MotionFilmstripTests/" + BAND
CASES = [BAND]

MUTATIONS = [
    ("M384", "`captureRect` 变成空操作（两臂都抓整窗）⇒ 必须同时红在'帧高变小'与'严格更便宜'两格。"
             "这一刀是 R72 降线之后**唯一还需要成立的保证**：省倍数不再被门，那'带捕获'这件事靠什么守？"
             "靠的是几何与方向，两者都在这条 mutation 下塌",
     TESTS, FILTER,
     "        let capture = fullCapture ? nil : scenario.captureRect?(host)",
     "        let capture: NSRect? = nil"),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
    env["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r72_mutation_out"
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr


def verdicts_of(text):
    if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(BAND), text):
        return "red"
    if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(BAND), text):
        return "green"
    if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' skipped" % re.escape(BAND), text):
        return "skipped"
    return "absent"


def failure_messages(text):
    return [l[:230] for l in text.splitlines() if "error: -[" in l and BAND in l]


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        original = read(TESTS)
        print("=== 基线（未变异）===")
        text = run()
        base = verdicts_of(text)
        print("   %s = %s" % (BAND, base))
        if base != "green":
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面的『红』不是证据，整批作废")
            for line in failure_messages(text)[:6]:
                print("     " + line)
            return 1
        for tag, note, path, _filter, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            source = read(path)
            if needle not in source or needle in replacement:
                print("   DRIFT-NOT-APPLIED 原文找不到或变异文含原文 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地")
                write(path, original)
                results.append((tag, "NOT-APPLIED"))
                continue
            print("   落地确认")
            try:
                text = run()
                mark = verdicts_of(text)
                if mark == "red":
                    print("   CAUGHT 红在 %s" % BAND)
                    results.append((tag, "CAUGHT"))
                elif mark == "skipped":
                    print("   NOT-RUN 被 skip 了")
                    results.append((tag, "NOT-RUN"))
                else:
                    print("   ESCAPED %s" % mark)
                    results.append((tag, "ESCAPED"))
                for line in failure_messages(text)[:4]:
                    print("     " + line)
            finally:
                write(path, original)
                print("   已还原（逐字节相同：%s）" % (read(path) == original))
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
        print("\n=== 汇总 ===")
        for tag, mark in results:
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0),
                 counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
