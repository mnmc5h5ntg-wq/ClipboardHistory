#!/usr/bin/env python3
"""R21/R21b 变异对照：这一轮的判据是**像素**，所以变异也要能改出像素来。

七支：
  M90 把清除 × 退回 `.tertiary`      ⇒ 帧探针必须红（这是本轮全部结论的地基：尺真的在读产品）
  M91 把展开箭头退回 `.tertiary`      ⇒ 源码点名账本必须红
  M92 把 × 的探针框挪到空白处          ⇒ 必须红在**墨地板**上，不是红在对比度上（红要对的理由）
  M93 拆掉尺的 sRGB 线性化            ⇒ 算术真值表必须红
  M94 把账本清空（源码里三处还在）      ⇒ 点名账本必须红 ⇒ 证明它不是装饰

模板三件套（R18 烧了 47 分钟换来的）：剔 `SDKROOT`、第 0 支预检、还原比自抓的字节。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")

FILES = {
    "search": os.path.join(SRC, "Views/SearchField.swift"),
    "detail": os.path.join(SRC, "Views/DetailView.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "guards": os.path.join(TESTS, "PressFeedbackTests.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

PROBE = "UICaptureTests/testActionableInkStaysAboveTheLegibilityFloor"
ARITH = "UICaptureTests/testContrastRulerArithmetic"
LEDGER = "PressFeedbackTests/testTheFaintestInkTierIsReservedForNonControls"
HEIGHT = "UICaptureTests/testSearchFieldIdealHeightIsStateIndependent"

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


def sub_after(text, anchor, old, new, label):
    """只替换 anchor 之后**第一次**出现的 old —— 这一档颜色在这个文件里到处都是。"""
    start = text.find(anchor)
    if start < 0:
        raise AssertionError(f"{label}: 找不到锚点 {anchor!r}")
    tail = text[start:]
    if tail.count(old) < 1:
        raise AssertionError(f"{label}: 锚点之后找不到 {old!r}")
    return text[:start] + tail.replace(old, new, 1)


# M90：清除 × 退回 `.tertiary`（本轮修掉的那个缺陷本身）。
mutation(
    "M90", "清除 × 退回 .tertiary（静置 1.86/2.22）", "search",
    [lambda s: sub(s, ".foregroundStyle(isHovered ? VisualInk.controlTargeted : VisualInk.control)",
                   ".foregroundStyle(isHovered ? .secondary : .tertiary)", 1, "M90")],
    PROBE, "清除 ×",
)

# M91：多文件行的展开箭头退回 `.tertiary`。
mutation(
    "M91", "展开箭头退回 .tertiary", "detail",
    [lambda s: sub_after(s, 'Image(systemName: "chevron.right")',
                         ".foregroundStyle(VisualInk.control)", ".foregroundStyle(.tertiary)", "M91")],
    LEDGER, "DetailView.swift",
)

# M92：把 × 的探针框挪到帧里的空白处 —— 必须红在"墨地板"那条上，而不是"对比度不足"。
# 这一支证的是**两条断言各自有牙**：只报对比度的话，空白框会读到 1.0 而红成一条假缺陷。
mutation(
    "M92", "× 的探针框挪到空白处", "harness",
    [lambda s: sub(s, "rect: CGRect(x: 286, y: 80, width: 22, height: 22)",
                   "rect: CGRect(x: 150, y: 8, width: 22, height: 22)", 1, "M92")],
    PROBE, "框贴到空白",
)

# M93：拆掉尺的 sRGB 线性化（"三通道总差"那一类错误算法的化身）。
mutation(
    "M93", "对比度算式退回线性亮度", "harness",
    [lambda s: sub(s, "return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)",
                   "return c", 1, "M93")],
    ARITH, "4.54",
)

# M94：账本清空而源码里三处还在 ⇒ 点名那条必须红（证明账本不是装饰）。
mutation(
    "M94", "把 .tertiary 的点名账本清空", "guards",
    [lambda s: sub(s, 'var ledger: [String: Int] = ["DailyCopyHeatmapView.swift": 3]',
                   "var ledger: [String: Int] = [:]", 1, "M94")],
    LEDGER, "账本里没有它",
)


# M95：文本列的 22pt 声明被改回 17pt（R20 那次真实回归的形状）。
mutation(
    "M95", "文本列退回 17pt（两态差 5pt）", "search",
    [lambda s: sub(s, ".frame(maxWidth: .infinity, minHeight: 22, maxHeight: 22)",
                   ".frame(maxWidth: .infinity, minHeight: 17, maxHeight: 17)", 1, "M95")],
    HEIGHT, "定高者不是文本列",
)

# M96：把 × 的字形框拆掉 —— 它固有的 14.5pt 会让"有字"那一态漂 0.5pt。
# 这一支是**判据锋利度的探针**：容差若还停在 1.5pt，它就会 ESCAPED（0.5 < 1.5）。
mutation(
    "M96", "× 的字形不再钉成 14×14（漂 0.5pt）", "search",
    [lambda s: sub(s, "\n                        .frame(width: 14, height: 14)", "", 1, "M96")],
    HEIGHT, "定高者不是文本列",
)


def run(test_filter):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=dict(BASE_ENV),
                          timeout=1200)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in FILES.values()}

    print("=== 预检（不注入任何变异）===", flush=True)
    ok = True
    for test in sorted({m[4] for m in MUTATIONS}):
        verdict, out = run(test)
        first = [line for line in out.splitlines() if "error:" in line][:1]
        print(f"  {test:62s} {verdict:12s} {'OK' if verdict == 'ESCAPED' else '!! ' + (first[0][:120] if first else '')}",
              flush=True)
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
            # 红要对在正确的理由上：只报"红了"分不清"抓到了"与"崩了"。
            reason = "对" if expect_text in out else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R21/R21b 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
