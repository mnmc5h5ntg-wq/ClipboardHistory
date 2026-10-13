#!/usr/bin/env python3
"""R20 变异对照：这一轮的判据一半是"接线/形状"，一半是"像素量出来的两态等高"。

模板三件套（R18 烧了 47 分钟换来的）：剔 `SDKROOT`、第 0 支预检、还原比自抓的字节。
"""
import os
import shutil
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r20-mut-shots"

FILES = {
    "glass": os.path.join(SRC, "Views/GlassControls.swift"),
    "search": os.path.join(SRC, "Views/SearchField.swift"),
    "row": os.path.join(SRC, "Views/HistoryRowViews.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "guards": os.path.join(TESTS, "PressFeedbackTests.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

GUARD_PILL = "PressFeedbackTests/testGlassPillPaintsExactlyOneHoverLayer"
GUARD_TIER = "PressFeedbackTests/testStyleForwardsItsParametersInsteadOfResupplyingDefaults"
GUARD_PAD = "PressFeedbackTests/testSmallControlsAskForThePillPadding"
GUARD_HEIGHT = "UICaptureTests/testSearchFieldKeepsTheSameHeightInBothStates"

MUTATIONS = []


def mutation(mid, title, name, edits, test, needs_shots=False):
    MUTATIONS.append((mid, title, name, edits, test, needs_shots))


def read(name):
    with open(FILES[name], encoding="utf-8") as handle:
        return handle.read()


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


# M85：详情区药丸的悬停层叠回来（两层 ≈0.14，比控件档高 1.75 倍）。
mutation(
    "M85", "药丸的 pressedStyle 又自带悬停层", "glass",
    [lambda s: sub(s, ".pressedStyle(in: Circle(), hoverLevel: 0)",
                   ".pressedStyle(in: Circle())", 1, "M85")],
    GUARD_PILL,
)

# M86：清除 × 退回默认那一档（0.06 是给整行定的）。
mutation(
    "M86", "清除 × 不表态悬停档", "search",
    [lambda s: sub(s, ".pressedStyle(in: Circle(),\n                              hoverLevel: VisualFill.controlHover,\n                              labelPadding: 4)",
                   ".pressedStyle(in: Circle())", 1, "M86")],
    GUARD_TIER,
)

# M87：**本轮真实犯过的那次回归**——文本列回到 17pt，
# 于是"有字的那颗框"被 22pt 的命中区顶高，两态差 5pt（打字时搜索框自己跳）。
mutation(
    "M87", "文本列回到 17pt（两态不再等高）", "search",
    [lambda s: sub(s, ".frame(maxWidth: .infinity, minHeight: 22, maxHeight: 22)",
                   ".frame(maxWidth: .infinity, minHeight: 17, maxHeight: 17)", 1, "M87")],
    GUARD_HEIGHT,
)

# M88：× 的命中区退回 0（贴着笔画的一圈，能点的地方只有字形）。
mutation(
    "M88", "清除 × 的命中区退回 0", "search",
    [lambda s: sub(s, "labelPadding: 4)", "labelPadding: 0)", 1, "M88")],
    GUARD_PAD,
)

# M89：把"整行有多少像素偏离底色"的地板抬到 0.99 ⇒ 一条带都找不出来。
# 这条证的是**量尺本身**有牙：判据不是"永远能读到两条带"的装饰。
mutation(
    "M89", "填充带判据的地板抬到 99%", "harness",
    [lambda s: sub(s, "let filled = Double(off) / Double(max(width, 1)) > 0.5",
                   "let filled = Double(off) / Double(max(width, 1)) > 0.99", 1, "M89")],
    GUARD_HEIGHT,
)


def run(test_filter, needs_shots=False):
    env = dict(BASE_ENV)
    if needs_shots:
        shutil.rmtree(SHOTS, ignore_errors=True)
        os.makedirs(SHOTS, exist_ok=True)
        env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1200)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in FILES.values()}

    print("=== 预检（不注入任何变异）===", flush=True)
    ok = True
    for test, needs in sorted({(m[4], m[5]) for m in MUTATIONS}):
        verdict, out = run(test, needs)
        first = [line for line in out.splitlines() if "error:" in line][:1]
        print(f"  {test:70s} {verdict:12s} {'OK' if verdict == 'ESCAPED' else '!! ' + (first[0][:120] if first else '')}",
              flush=True)
        ok = ok and verdict == "ESCAPED"
    if not ok:
        for path, blob in digests.items():
            with open(path, "wb") as handle:
                handle.write(blob)
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, name, edits, test, needs in MUTATIONS:
        text = originals[name]
        try:
            for edit in edits:
                text = edit(text)
        except AssertionError as exc:
            results.append((mid, "DID-NOT-RUN", f"{title}：{exc}"))
            print(f"{mid}: DID-NOT-RUN {title}", flush=True)
            continue
        with open(FILES[name], "w", encoding="utf-8") as handle:
            handle.write(text)
        try:
            verdict, out = run(test, needs)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(FILES[name], "wb") as handle:
                handle.write(digests[FILES[name]])
        detail = ""
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            detail = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, f"{title}{detail}"))
        print(f"{mid}: {verdict} {title}", flush=True)

    print("\n=== R20 变异对照汇总 ===")
    for mid, verdict, line in results:
        mark = "OK " if verdict == "CAUGHT" else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
