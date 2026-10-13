#!/usr/bin/env python3
"""R28 变异对照：说明文字画全、夹具接缝对账、以及"反相墨"这个新分类。

五支：
  M123 把 `.lineLimit(1)` 装回快捷键说明（= 修之前的产品） ⇒ 两臂对照必须红在"有说明文字被截断了"
  M124 把夹具里新接的 `exportHistoryAction` 摘掉            ⇒ 接缝守卫必须红在"产品注入的接缝夹具没注入"
  M125 把文字墨的闸门从 60 挪到 24（平涂会混进来）          ⇒ 真值表必须红在"平涂底色不许算成字"
  M126 把宽臂从 900pt 改回 720pt（参照失去资格）           ⇒ 必须红在"不再是不动的参照"，
                                                                不许红成"两臂自比 ⇒ 恒真绿"
  M127 把 `signedInk` 的阈值抬到 400（什么都数不到）        ⇒ 侧栏探针必须红在"连一个像素都没动过"，
                                                                也就是那条新断言真的接在测量上
  M128 图例退回 `.tertiary`（参照不动、产品掉档）            ⇒ 相对参照必须红，证明改成相对没有把牙磨平
  M129 参照臂自己掉到 `.tertiary`                            ⇒ 必须红在"参照坏了"，不许静默跟着产品一起淡

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r28-mut-shots"

FILES = {
    "settings": os.path.join(SRC, "Views/SettingsView.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "probe": os.path.join(TESTS, "OffscreenSymbolInkProbeTests.swift"),
    "heatmap": os.path.join(SRC, "Views/DailyCopyHeatmapView.swift"),
}
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

CLIP = "UICaptureTests/testSettingsHelperTextIsNotClipped"
TRUTH = "UICaptureTests/testTextInkGateTruthTable"
SEAM = "UICaptureTests/testCaptureFixtureInjectsEveryActionSeamTheProductInjects"
PROBE = "OffscreenSymbolInkProbeTests/testProductSettingsSidebarIconInk"
CAPTION = "UICaptureTests/testCaptionTextStaysOnTheSecondaryTier"

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


# M123：缺陷的历史真实形态 —— 说明文字只准画一行。
# needle 带足上下文：这个文件里 `.fixedSize(horizontal: false, vertical: true)` 有三处，
# 裸 needle 会一次改三处，那是变异在撒谎（R27 的 M120 就是这么救回来的）。
mutation(
    "M123", "把 `.lineLimit(1)` 装回快捷键说明（修之前的产品）", "settings",
    [lambda s: sub(s, "                    Text(settings.action.description)\n"
                      "                        .font(.caption)\n"
                      "                        .foregroundStyle(.secondary)\n",
                   "                    Text(settings.action.description)\n"
                   "                        .font(.caption)\n"
                   "                        .foregroundStyle(.secondary)\n"
                   "                        .lineLimit(1)\n",
                   1, "M123")],
    CLIP, "有说明文字被截断了",
)

# M124：把夹具刚接上的一根接缝摘掉 —— 守卫必须点名是哪一根。
mutation(
    "M124", "夹具不再注入 exportHistoryAction", "harness",
    [lambda s: sub(s, "            exportHistoryAction: { _ in nil },\n", "", 1, "M124")],
    SEAM, "夹具没注入",
)

# M125：闸门挪到 24 ⇒ 平涂的控件底色混进"字"里，两臂的信号被稀释。
mutation(
    "M125", "文字墨闸门 60 → 24（平涂混进来）", "harness",
    [lambda s: sub(s, "    static let textInkMinDelta = 60",
                   "    static let textInkMinDelta = 24", 1, "M125")],
    TRUTH, "平涂底色不许算成字",
)

# M126：参照臂失去资格。这一支的价值是"它不许静默变绿"：
# 两臂同宽 ⇒ ratio 恒等于 1 ⇒ 如果只留 M123 那条断言，这条变异会绿着过去。
mutation(
    "M126", "宽臂 900pt → 720pt（参照失去资格）", "harness",
    [lambda s: sub(s, 'Fixture("settings-shortcuts-wide", NSSize(width: 900, height: 540))',
                   'Fixture("settings-shortcuts-wide", NSSize(width: 720, height: 540))', 1, "M126")],
    CLIP, "不再是不动的参照",
)

# M127：把"这块地方动不动过"的阈值抬到不可能达到 ⇒ 反相的那几行会被读成"整列空白"。
# 这条证明新增的 `absent == 0` 断言真的接在 `signedInk` 的读数上，而不是一句恒真的废话。
mutation(
    "M127", "signedInk 阈值 4 → 400（什么都数不到）", "probe",
    [lambda s: sub(s, "yRange: bands[index], threshold: 4)",
                   "yRange: bands[index], threshold: 400)", 1, "M127")],
    PROBE, "连一个像素都没动过",
)


# M128：把图例那一档退回 `.tertiary`。
# 这一支是"相对参照"这条改动的牙口证明：参照是**系统自己的一档**，产品掉档时参照不动，
# 比值就会掉到 0.47 —— 如果参照是"从同一批探针里取平均"，这一支会绿着过去。
mutation(
    "M128", "图例退回 `.tertiary`（参照不动、产品掉档）", "heatmap",
    [lambda s: sub(s, ".foregroundStyle(.secondary)\n    }",
                   ".foregroundStyle(.tertiary)\n    }", 1, "M128")],
    CAPTION, "要读的标签不许比能点的笔画更淡",
)

# M129：把**参照本身**改成 `.tertiary` —— 参照坏了必须被自己的地板拦住，
# 否则"参照跟着产品一起变淡"就是这条判据的静默失效通道。
mutation(
    "M129", "参照臂自己掉到 `.tertiary`", "harness",
    [lambda s: sub(s, "                    .font(.system(size: 10))\n"
                      "                    .foregroundStyle(.secondary)\n",
                   "                    .font(.system(size: 10))\n"
                   "                    .foregroundStyle(.tertiary)\n", 1, "M129")],
    CAPTION, "是渲染失效，不是产品淡了",
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

    print("=== 预检（不注入任何变异，五条判据都必须绿）===", flush=True)
    ok = True
    for test in (CLIP, TRUTH, SEAM, PROBE, CAPTION):
        verdict, out = run(test)
        print(f"  {test:70s} {verdict}", flush=True)
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
            reason = "对  「" + hit[0].strip()[-170:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R28 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
