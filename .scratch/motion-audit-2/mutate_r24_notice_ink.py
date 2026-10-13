#!/usr/bin/env python3
"""R24 变异对照：横幅正文的墨色 + 组件帧与产品的布局一致性。

六支，按"缺陷的历史真实形态"改法（不在原行上写会引入新错误的近似改法）：
  M104 正文退回 `.secondary`（就是 R24 修之前的产品）      ⇒ 像素判据必须红在"正文对底色只有"
  M105 组件帧改回 `VStack(spacing: 12)`（夹具替产品决定）  ⇒ 必须红在"没有底色的空缝"
  M106 **产品**的横幅容器塞进 12pt 缝（消费侧坏）          ⇒ 同样必须红在空缝，且红在产品那两张帧
  M107 把分带的色度阈值抬到永远命不中（把尺弄瞎）          ⇒ 必须红在"只找到 0 条色带"，不许静默通过
  M108 把文字列挪到带外的空白                              ⇒ 必须红在"这条带里没有字"（墨地板有牙）
  M109 把加载态也升档（判据的另一端）                      ⇒ 真值表必须红，且不许把菜单栏那行改亮

模板四件套：剔 `SDKROOT`、第 0 支预检（预检不许把 skip 读成绿）、还原比自抓的字节、
读**失败消息**确认红得对（红因与缺陷机制一致才算 CAUGHT）。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r24-mut-shots"

FILES = {
    "state": os.path.join(SRC, "Utilities/StatePresentation.swift"),
    "content": os.path.join(SRC, "Views/ContentView.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "round3": os.path.join(TESTS, "Round3StateLanguageTests.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

PIXEL = "UICaptureTests/testNoticeBodyTextStaysReadable"
TABLE = "Round3StateLanguageTests/testSeverityStatesCarryTheirOwnTextInk"

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


# M104：正文退回修之前的那一档。
mutation(
    "M104", "正文退回 `.secondary`（R24 修之前的产品）", "state",
    [lambda s: sub(s, ".foregroundStyle(StatePresentation.messageInkStyle(for: kind))",
                   ".foregroundStyle(.secondary)", 1, "M104")],
    PIXEL, "正文对底色只有",
)

# M105：夹具替产品决定布局（BACKLOG 36 的原始缺陷形态）。
mutation(
    "M105", "组件帧改回 spacing: 12", "harness",
    [lambda s: sub(s, """                VStack(spacing: 0) {
                    NoticeBanner(message: "主存档无法读取""",
                   """                VStack(spacing: 12) {
                    NoticeBanner(message: "主存档无法读取""", 1, "M105")],
    PIXEL, "没有底色的空缝",
)

# M106：同样的缝塞进**产品** —— 判据不能只看得见夹具。
mutation(
    "M106", "产品的横幅容器塞进 12pt 缝", "content",
    [lambda s: sub(s, """        VStack(spacing: 0) {
            notices""", """        VStack(spacing: 12) {
            notices""", 1, "M106")],
    PIXEL, "没有底色的空缝",
)

# M107：把尺弄瞎（阈值永远命不中）。
mutation(
    "M107", "分带色度阈值抬到命不中（把尺弄瞎）", "harness",
    [lambda s: sub(s, "            if chroma > 6 {", "            if chroma > 600 {", 1, "M107")],
    PIXEL, "只找到 0 条色带",
)

# M108：文字列挪到带外。
mutation(
    "M108", "文字列挪到带外的空白", "harness",
    [lambda s: sub(s, "            let rect = CGRect(x: 36, y: startPt + 2,",
                   "            let rect = CGRect(x: 470, y: startPt + 2,", 1, "M108")],
    PIXEL, "这条带里没有字",
)

# M109：判据的另一端 —— 不许把背景状态也升档。
mutation(
    "M109", "加载态一起升档（喧宾夺主）", "state",
    [lambda s: sub(s, "        case .warning, .error: return .prominent\n"
                      "        case .loading, .empty: return .subdued",
                   "        case .warning, .error, .loading: return .prominent\n"
                   "        case .empty: return .subdued", 1, "M109")],
    TABLE, "正在整理推荐",
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

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    preflight_ok = True
    for test in (PIXEL, TABLE):
        verdict, out = run(test)
        print(f"  {test:58s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            preflight_ok = False
            print(out.splitlines()[-1][:200] if out else "", flush=True)
    if not preflight_ok:
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
            reason = "对" if expect_text in out else "!! 红得不对（找不到期望文本）"
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            if hit:
                reason += "  「" + hit[0].strip()[:150] + "」"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R24 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
