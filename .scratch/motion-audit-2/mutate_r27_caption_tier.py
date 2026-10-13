#!/usr/bin/env python3
"""R27 变异对照：说明文字的梯子，以及那本被清空的 `.tertiary` 账。

三支：
  M120 月份刻度退回 `.tertiary`（修之前的产品）  ⇒ 判据必须红在"要读的标签不许比能点的笔画更淡"
  M121 在另一个文件里用 `.tertiary`（账本已空）  ⇒ 点名守卫必须红在"账本里没有它"
  M122 把星期刻度的框挪到帧里的空白              ⇒ 必须红在"框里没有字"（墨占比地板有牙），
                                                    不许红成一个假的低对比度

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r27-mut-shots"

FILES = {
    "heatmap": os.path.join(SRC, "Views/DailyCopyHeatmapView.swift"),
    "search": os.path.join(SRC, "Views/SearchField.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

CAPTION = "UICaptureTests/testCaptionTextStaysOnTheSecondaryTier"
LEDGER = "PressFeedbackTests/testTheFaintestInkTierIsReservedForNonControls"

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


# M120：三处刻度一起退回修之前的那一档（缺陷的历史真实形态）。
# 三处都用**带上下文的 needle**：`.foregroundStyle(.secondary)` 在这个文件里还有两处本来就在
# 这一档（标题与说明行）—— 裸 needle 会一次改到五处，那是变异在撒谎。
mutation(
    "M120", "刻度退回 `.tertiary`（修之前的产品）", "heatmap",
    [lambda s: sub(s, ".foregroundStyle(.secondary)\n                        .fixedSize()",
                   ".foregroundStyle(.tertiary)\n                        .fixedSize()",
                   1, "M120-月份"),
     lambda s: sub(s, ".foregroundStyle(.secondary)\n                    .frame(width: weekdayLabelWidth",
                   ".foregroundStyle(.tertiary)\n                    .frame(width: weekdayLabelWidth",
                   1, "M120-星期"),
     lambda s: sub(s, ".foregroundStyle(.secondary)\n    }",
                   ".foregroundStyle(.tertiary)\n    }",
                   1, "M120-图例")],
    CAPTION, "要读的标签不许比能点的笔画更淡",
)

# M121：账本清空之后，任何一处再用这一档都必须先点名（放在账本之外的文件里）。
mutation(
    "M121", "在 SearchField 里用 `.tertiary`（账本已空）", "search",
    [lambda s: sub(s, "import SwiftUI\n",
                   "import SwiftUI\n\n// MUTANT：故意在账本之外的文件里引用一次最淡的一档\n"
                   "var mutantTint: AnyShapeStyle { AnyShapeStyle(.tertiary)}\n", 1, "M121")],
    LEDGER, "账本里没有它",
)

# M122：把星期刻度的框挪到帧里的空白。
mutation(
    "M122", "星期刻度的框挪到空白处", "harness",
    [lambda s: sub(s, "                 rect: CGRect(x: 10, y: 90, width: 26, height: 90)),",
                   "                 rect: CGRect(x: 150, y: 230, width: 26, height: 90)),",
                   1, "M122")],
    CAPTION, "框贴到空白上了",
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
    for test in (CAPTION, LEDGER):
        verdict, out = run(test)
        print(f"  {test:60s} {verdict}", flush=True)
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

    print("\n=== R27 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
