#!/usr/bin/env python3
"""R23 变异对照：判据跑在**色度**这根轴上，所以变异也要能量出这根轴有没有断。

三支：
  M101 把 `NoticeBanner` 的底色改回默认（会越进安全区）  ⇒ 判据必须红在"涂到标题栏后面"
  M102 把色度读数改成恒 0（把尺弄瞎）                    ⇒ **正对照**必须红
  M103 把"横幅自己那一条"的采样框挪到空白处              ⇒ 同样必须红在正对照上

M102/M103 是同一句话的两种做法：**一条只在"没红"上被检验的判据，没有被检验过**。
模板三件套：剔 `SDKROOT`、第 0 支预检（且预检不许把 skip 读成绿）、还原比自抓的字节。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r23-mut-shots"

FILES = {
    "banner": os.path.join(SRC, "Views/NoticeBanner.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}
CHROME = "UICaptureTests/testNoticeTintDoesNotReachTheTitlebar"

MUTATIONS = []


def mutation(mid, title, name, edits, expect_text):
    MUTATIONS.append((mid, title, name, edits, expect_text))


def read(name):
    with open(FILES[name], encoding="utf-8") as handle:
        return handle.read()


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


# M101：底色回到默认（SwiftUI 4 的默认就是越进安全区）。
mutation(
    "M101", "横幅底色改回默认（会涂到标题栏后面）", "banner",
    [lambda s: sub(s, """            band.background(StatePresentation.backgroundStyle(for: kind),
                            ignoresSafeAreaEdges: [])""",
                   "            band.background(StatePresentation.backgroundStyle(for: kind))",
                   1, "M101")],
    "涂到了标题栏",
)

# M102：把色度尺弄瞎。
mutation(
    "M102", "色度读数改成恒 0（把尺弄瞎）", "harness",
    [lambda s: sub(s, "return count == 0 ? 0 : total / Double(count)", "return 0", 1, "M102")],
    "尺读不到底色",
)

# M103：把横幅采样框挪到帧里的空白处（下方详情区）。
mutation(
    "M103", "横幅采样框挪到空白处", "harness",
    [lambda s: sub(s, "let band = CGRect(x: 40, y: 56, width: 300, height: 30)",
                   "let band = CGRect(x: 40, y: 300, width: 300, height: 30)", 1, "M103")],
    "尺读不到底色",
)


def run(test_filter):
    env = dict(BASE_ENV)
    # 捕获类判据靠环境变量开闸；不打开的话整条 skip，而 skip 的退出码是 0（R22 那一族）。
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

    print("=== 预检（不注入任何变异）===", flush=True)
    verdict, out = run(CHROME)
    print(f"  {CHROME:56s} {verdict}", flush=True)
    if verdict != "ESCAPED":
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, name, edits, expect_text in MUTATIONS:
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
            verdict, out = run(CHROME)
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

    print("\n=== R23 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
