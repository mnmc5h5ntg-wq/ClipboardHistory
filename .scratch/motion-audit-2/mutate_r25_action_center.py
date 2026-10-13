#!/usr/bin/env python3
"""R25 变异对照：动作按钮的垂直居中，以及"读它的尺"本身。

四支：
  M110 外层 HStack 回到 `.firstTextBaseline`（修之前的产品）  ⇒ 判据必须红在"偏了 Xpt"
  M111 把每行最少墨像素抬到命不中（尺看不见按钮）            ⇒ 必须红在"没找到动作按钮的字形"，不许静默通过
  M112 给横幅底部多加 12pt 内边距（真实回归形态）            ⇒ 必须红在"偏了"，而且方向是负的
  M113 让 `inkRowSpan` 在找不到时返回整块矩形（把 nil 换成假居中）
       ⇒ **正对照**必须红在"空矩形必须返回 nil" —— 崩溃/兜底值把"没找到"读成"完美居中"是这一族最坏的错法

模板四件套：剔 SDKROOT、预检（预检不许把 skip 读成绿）、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r25-mut-shots"

FILES = {
    "state": os.path.join(SRC, "Utilities/StatePresentation.swift"),
    "banner": os.path.join(SRC, "Views/NoticeBanner.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

CENTER = "UICaptureTests/testNoticeActionIsVerticallyCenteredInItsBand"
CONTROL = "UICaptureTests/testActionSpanRulerReadsBothEnds"

MUTATIONS = []


def mutation(mid, title, name, edits, test, expect_text):
    MUTATIONS.append((mid, title, name, edits, test, expect_text))


def read(name):
    with open(FILES[name], encoding="utf-8") as handle:
        return handle.read()


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


# M110：回到"整行按第一行基线排"。
mutation(
    "M110", "外层 HStack 回到 firstTextBaseline（修之前的产品）", "state",
    [lambda s: sub(s, "        HStack(spacing: 10) {\n            HStack(alignment: .firstTextBaseline, spacing: 6) {",
                   "        HStack(alignment: .firstTextBaseline, spacing: 10) {\n            HStack(alignment: .firstTextBaseline, spacing: 6) {",
                   1, "M110")],
    CENTER, "的动作按钮偏了",
)

# M111：尺看不见按钮。
mutation(
    "M111", "每行最少墨像素抬到命不中（尺看不见按钮）", "harness",
    [lambda s: sub(s, "                           minInkPerRow: Int = 3) -> (startPt: Double, endPt: Double)? {",
                   "                           minInkPerRow: Int = 9000) -> (startPt: Double, endPt: Double)? {",
                   1, "M111")],
    CENTER, "没找到动作按钮的字形",
)

# M112：横幅底部多塞 12pt（真实回归形态：有人觉得"提示条该再高一点"）。
mutation(
    "M112", "横幅底部多加 12pt 内边距", "banner",
    [lambda s: sub(s, "                .padding(.vertical, 9)",
                   "                .padding(.top, 9)\n                .padding(.bottom, 21)",
                   1, "M112")],
    CENTER, "的动作按钮偏了",
)

# M113：把"没找到"换成兜底值。
mutation(
    "M113", "找不到时返回整块矩形（把 nil 换成假居中）", "harness",
    [lambda s: sub(s, "        guard first >= 0, last > first else { return nil }",
                   "        guard first >= 0, last > first else { return (Double(y0) / scale, Double(y1) / scale) }",
                   1, "M113")],
    CONTROL, "空矩形必须返回 nil",
)


def run(test_filter):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    passed = [line for line in out.splitlines() if "Test Case" in line and "passed" in line]
    failed = [line for line in out.splitlines() if "Test Case" in line and " failed" in line]
    if not passed and not failed:
        return "DID-NOT-RUN", "整条被 skip：" + out.splitlines()[-1][:120]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in FILES.values()}

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    ok = True
    for test in (CENTER, CONTROL):
        verdict, out = run(test)
        print(f"  {test:62s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            ok = False
            print((out.splitlines() or [""])[-1][:200], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, name, edits, test, expect_text in MUTATIONS:
        text = originals[name]
        try:
            for edit in edits:
                text = edit(text)
        except AssertionError as exc:
            results.append((mid, "DID-NOT-RUN", title, f"{exc}"))
            print(f"{mid}: DID-NOT-RUN {title}", flush=True)
            continue
        with open(FILES[name], "w", encoding="utf-8") as handle:
            handle.write(text)
        try:
            verdict, out = run(test)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(FILES[name], "wb") as handle:
                handle.write(digests[FILES[name]])
        reason = ""
        if verdict == "CAUGHT" and expect_text:
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = "对  「" + hit[0].strip()[-150:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R25 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
