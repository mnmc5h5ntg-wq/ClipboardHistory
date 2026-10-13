#!/usr/bin/env python3
"""R19 变异对照：这一轮的判据全是"限制还在不在"，所以每一支都在问
**"它红了吗"**，而不是"它绿了吗"。

三条模板规矩（都是上一轮烧掉 47 分钟换来的，见 mutate_r18_frame_rulers.py 顶部）：
① `BASE_ENV` 剔掉 python 注入的 `SDKROOT`；
② 第 0 支 = 预检：不注入任何东西，先要求每条被点名的判据能跑且为绿；
③ 还原自检比的是电池开跑前自己抓的字节，不是 `git diff`。
"""
import os
import shutil
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r19-mut-shots"

FILES = {
    "controller": os.path.join(SRC, "Managers/QuickPickController.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}
TEST = "UICaptureTests/testQuickPickOverlayCannotBeCapturedYet"


def read(name):
    with open(FILES[name], encoding="utf-8") as handle:
        return handle.read()


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


def run(test_filter):
    env = dict(BASE_ENV)
    shutil.rmtree(SHOTS, ignore_errors=True)
    os.makedirs(SHOTS, exist_ok=True)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1200)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


MUTATIONS = []


def mutation(mid, title, name, edits, expect=TEST):
    MUTATIONS.append((mid, title, name, edits, expect))


# M81：捕获入口建不出窗口 ⇒ 判据必须红（它没有对象了）。
mutation(
    "M81", "捕获入口返回 nil", "controller",
    [lambda s: sub(s, "        return panel\n    }\n\n    func hide()",
                   "        _ = panel\n        return nil\n    }\n\n    func hide()", 1, "M81")],
)

# M82：**所有权**——夹具不再留住控制器。
# `NSTableView.dataSource` 是弱引用，控制器一被释放表格就静默变成 0 行，
# 而帧仍然"合法"（一张空面板）。这条判据存在的最大理由就是抓这个。
mutation(
    "M82", "夹具不留住控制器（弱 dataSource 陷阱）", "harness",
    [lambda s: sub(s,
                   "            var kept: QuickPickController?\n"
                   "            return {\n"
                   "                if kept == nil {\n"
                   "                    kept = QuickPickController(historyStore: { store }, commit: { _ in })\n"
                   "                }\n"
                   "                guard let controller = kept else { return nil }\n"
                   "                return controller.windowForCapture(query: query)",
                   "            return {\n"
                   "                let controller = QuickPickController(historyStore: { store }, commit: { _ in })\n"
                   "                _ = controller.self\n"
                   "                return controller.windowForCapture(query: query)", 1, "M82")],
)

# M83：捕获入口不填行（忘了 rebuildRows）⇒ rows 必须是 0 ⇒ 判据红。
mutation(
    "M83", "捕获入口忘记 rebuildRows", "controller",
    [lambda s: sub(s, "        field?.stringValue = query\n        rebuildRows()\n        model.index = 0\n"
                      "        selectCurrentRow()\n        return panel",
                   "        field?.stringValue = query\n        model.index = 0\n"
                   "        selectCurrentRow()\n        return panel", 1, "M83")],
)

# M84：把"原因"断言的地板压到 1pt ⇒ 实测 stackWidth=24 必须把它打红。
# 这条证的是那句解释**有数字支撑**，不是一句注释。
mutation(
    "M84", "原因断言的地板压到 1pt", "harness",
    [lambda s: sub(s, "        XCTAssertLessThan(stackWidth, 100,",
                   "        XCTAssertLessThan(stackWidth, 1,", 1, "M84")],
)


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in FILES.values()}

    print("=== 预检（不注入任何变异）===", flush=True)
    verdict, out = run(TEST)
    first = [line for line in out.splitlines() if "error:" in line][:1]
    print(f"  {TEST}  {verdict}  {'' if verdict == 'ESCAPED' else (first[0][:140] if first else '')}", flush=True)
    if verdict != "ESCAPED":
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, name, edits, _ in MUTATIONS:
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
            verdict, out = run(TEST)
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

    print("\n=== R19 变异对照汇总 ===")
    for mid, verdict, line in results:
        mark = "OK " if verdict == "CAUGHT" else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, verdict, _ in results if verdict == "CAUGHT")
    print(f"CAUGHT={caught}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
