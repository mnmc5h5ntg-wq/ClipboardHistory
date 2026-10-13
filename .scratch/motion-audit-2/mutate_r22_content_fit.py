#!/usr/bin/env python3
"""R22 变异对照：这一轮的判据全是"夹具与清单的形状"，所以变异也照形状打。

四支：
  M97 把 `weights` 的框改回 560（R18 裁了九轮的那个数）  ⇒ contentMustFit 必须红
  M98 把 `search-field` 的框改回 96（R20 一直在裁下半条）  ⇒ 同上
  M99 把底行墨的读数改成恒 0（把尺弄瞎）                 ⇒ **正对照**必须红
  M100 从胶片清单里删掉横幅的移除那一臂                   ⇒ "两臂都要有人判"必须红

M97/M98 是这条守卫的"该红的红"；M99 是它的"该红的没红怎么办" ——
十条对照全读 0.0% 的尺，没有 M99 这一支就等于没被检验过。

模板三件套（R18 烧了 47 分钟换来的）：剔 `SDKROOT`、第 0 支预检、还原比自抓的字节。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")

FILES = {
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "film": os.path.join(TESTS, "MotionFilmstripTests.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

CAPTURE = "UICaptureTests/testCaptureKeyViews"
ARMS = "MotionFilmstripTests/testBothBannerArmsAreJudged"

MUTATIONS = []


def mutation(mid, title, name, edits, test, expect_text=""):
    MUTATIONS.append((mid, title, name, edits, test, expect_text))


def read(name):
    with open(FILES[name], encoding="utf-8") as handle:
        return handle.read()


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


mutation(
    "M97", "weights 的框改回 560（R18 裁了九轮的那个数）", "harness",
    [lambda s: sub(s, 'Fixture("weights", NSSize(width: 520, height: 880)',
                   'Fixture("weights", NSSize(width: 520, height: 560)', 1, "M97")],
    CAPTURE, "正在裁自己",
)

mutation(
    "M98", "search-field 的框改回 96（R20 一直在裁下半条）", "harness",
    [lambda s: sub(s, 'Fixture("search-field", NSSize(width: 320, height: 112)',
                   'Fixture("search-field", NSSize(width: 320, height: 96)', 1, "M98")],
    CAPTURE, "正在裁自己",
)

mutation(
    "M99", "底行墨的读数改成恒 0（把尺弄瞎）", "harness",
    [lambda s: sub(s, "return Double(ink) / Double(width)", "return 0", 1, "M99")],
    CAPTURE, "瞎了",
)

mutation(
    "M100", "从胶片清单里删掉横幅的移除那一臂", "film",
    [lambda s: sub(s, "[noticeBanner(), noticeBannerDismiss(), detailKindChange(), emptyState()]",
                   "[noticeBanner(), detailKindChange(), emptyState()]", 1, "M100")],
    ARMS, "移除",
)


def run(test_filter):
    # 捕获类判据**只在设了 CLIPBOARD_HISTORY_UI_SHOTS 时才跑**，否则整条 skip 掉。
    # 第一版没给这个变量 ⇒ M97/M98/M99 三支"ESCAPED"其实是三条 skip，
    # 而预检也把"全被跳过"读成了"全绿" —— **预检的绿可以是跳过**，这一族记过（退出码复用），
    # 这次记的是它的兄弟：跳过码复用。
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r22-mut-shots"
    os.makedirs("/tmp/r22-mut-shots", exist_ok=True)
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env,
                          timeout=1800)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    executed = [line for line in out.splitlines() if "Test Case" in line and "passed" in line]
    failed = [line for line in out.splitlines() if "Test Case" in line and " failed" in line]
    skipped = [line for line in out.splitlines() if "Test Case" in line and "skipped" in line]
    if skipped and not executed and not failed:
        return "DID-NOT-RUN", "整条被 skip：" + skipped[0][:120]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in FILES.values()}

    print("=== 预检（不注入任何变异）===", flush=True)
    ok = True
    for test in sorted({m[4] for m in MUTATIONS}):
        verdict, out = run(test)
        first = [line for line in out.splitlines() if "error:" in line][:1]
        print(f"  {test:52s} {verdict:12s} {'OK' if verdict == 'ESCAPED' else '!! ' + (first[0][:130] if first else '')}",
              flush=True)
        if verdict == "DID-NOT-RUN":
            print("     ⇒ " + out.splitlines()[-1][:160] if False else "", end="")
        ok = ok and verdict == "ESCAPED"
    if not ok:
        for path, blob in digests.items():
            with open(path, "wb") as handle:
                handle.write(blob)
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, name, edits, test, expect_text in MUTATIONS:
        text = originals[name]
        try:
            for edit in edits:
                text = edit(text)
        except AssertionError as exc:
            results.append((mid, "DID-NOT-RUN", f"{title}：{exc}", ""))
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
            reason = "对" if expect_text in out else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R22 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
