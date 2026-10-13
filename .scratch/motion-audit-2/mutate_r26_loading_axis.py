#!/usr/bin/env python3
"""R26 变异对照：加载块的左轴，以及"看得见弱对比条带"的那根尺。

五支：
  M114 把横幅的文字列挪到 x=300（R24 的 M108 原样重放）
       ⇒ 这次必须红在**左锚定**那条（BACKLOG 38 补的就是这道缝），不许再红在对比度上
  M115 那一句人话退回居中（产品）        ⇒ 必须红在"加载块自己就两条左轴"
  M116 去掉 containerGutter 内缩（产品）  ⇒ 必须红在"它替代的详情头部在 x=20.5"（跨帧对照）
  M117 把条带的墨阈值从 6 抬到 40（尺瞎） ⇒ 必须红在"没找到条带"，不许静默通过
  M118 把 leadingInkColumn 的"最左"改成"最右" ⇒ 必须红（方向反了的尺比没有尺更坏）

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r26-mut-shots"

FILES = {
    "detail": os.path.join(SRC, "Views/DetailPreviewViews.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

NOTICE = "UICaptureTests/testNoticeBodyTextStaysReadable"
AXIS = "UICaptureTests/testLoadingBlockSharesTheDetailColumnsAxis"
WIRING = "SkeletonMotionTests/testSkeletonIsWiredIntoTheDetailLoadingBranch"

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


# M114：R24 的 M108 原样重放。
mutation(
    "M114", "横幅文字列挪到 x=300（R24 M108 重放）", "harness",
    [lambda s: sub(s, "            let rect = CGRect(x: 36, y: startPt + 2,",
                   "            let rect = CGRect(x: 300, y: startPt + 2,", 1, "M114")],
    NOTICE, "这一列里没有正文",
)

# M115：那一句退回居中。
mutation(
    "M115", "加载块那一句退回居中（修之前的产品）", "detail",
    [lambda s: sub(s, "        VStack(alignment: .leading, spacing: 14) {\n            SkeletonPreviewView(reduceMotion: reduceMotion)",
                   "        VStack(spacing: 14) {\n            SkeletonPreviewView(reduceMotion: reduceMotion)",
                   1, "M115")],
    AXIS, "加载块自己就两条左轴",
)

# M116：去掉详情栏内缩。
mutation(
    "M116", "去掉 containerGutter 内缩（条带顶到面板边）", "detail",
    [lambda s: sub(s, "        .padding(.horizontal, DetailTypography.containerGutter)\n        .padding(.top, 24)",
                   "        .padding(.top, 24)", 1, "M116")],
    AXIS, "条带顶到了面板边缘",
)

# M117：尺看不见弱对比条带。
mutation(
    "M117", "条带墨阈值 6→40（尺看不见弱对比）", "harness",
    [lambda s: sub(s, "                                               minDelta: 6, minInkPerColumn: 4)",
                   "                                               minDelta: 40, minInkPerColumn: 4)",
                   1, "M117")],
    AXIS, "没找到条带",
)

# M118：把"最左"改成"最右"。
mutation(
    "M118", "leadingInkColumn 从右往左扫（方向反了的尺）", "harness",
    [lambda s: sub(s, "        for x in x0..<x1 {\n            var ink = 0\n            for y in y0..<y1 where abs(luma(x, y) - background) > minDelta { ink += 1 }\n            if ink >= minInkPerColumn { return Double(x) / scale }\n        }",
                   "        for x in stride(from: x1 - 1, through: x0, by: -1) {\n            var ink = 0\n            for y in y0..<y1 where abs(luma(x, y) - background) > minDelta { ink += 1 }\n            if ink >= minInkPerColumn { return Double(x) / scale }\n        }",
                   1, "M118")],
    AXIS, "两条左轴",
)


# M119：让 `detail-loading` 不再渲染产品那个视图（帧与产品分家）。
mutation(
    "M119", "夹具改画 SkeletonPreviewView（帧不再等于产品）", "harness",
    [lambda s: sub(s, "                DetailLoadingView(reduceMotion: true)",
                   "                SkeletonPreviewView(reduceMotion: true)", 1, "M119")],
    WIRING, "帧不再渲染",
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
    for test in (NOTICE, AXIS, WIRING):
        verdict, out = run(test)
        print(f"  {test:56s} {verdict}", flush=True)
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
            reason = "对  「" + hit[0].strip()[-160:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R26 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
