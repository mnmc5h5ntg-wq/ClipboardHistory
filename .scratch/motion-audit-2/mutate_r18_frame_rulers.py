#!/usr/bin/env python3
"""R18 变异对照：这一轮的判据是**量尺自己**，所以每一把尺都要被打一次。

规矩与前几轮相同（见 mutate_r17_row_move.py 的说明）：
* 每处变异先 `cp` 一份原件，跑完立刻按文件还原；
* 注入前先断言 needle 命中数，命中数不对 ⇒ **DID-NOT-RUN**，不算绿；
* 期望红的用例若真红 ⇒ CAUGHT；若绿 ⇒ ESCAPED（这一条判据抓不到这个缺陷，要记账）；
* 编译不过 ⇒ DID-NOT-RUN（红是"跑不起来"，不是"抓到了"）。
"""
import os
import shutil
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests")
SHOTS = "/tmp/r18-mut-shots"

# **本机 python3 会把 `SDKROOT` 注入成 CommandLineTools 的 SDK**（账本里记过的那条），
# 而 SwiftPM 拿这个 SDK 去编 `Package.swift` 会在 `Swift.swiftinterface` 里报
# "consecutive statements on a line" ⇒ `error: 'clipboardhistory': Invalid manifest`。
# 第一版电池就是踩在这里：**八支变异全报 DID-NOT-RUN，47 分钟一点判别力都没买到**。
# 直接在 shell 里跑 `swift test` 是好的 —— 因为那个环境里没有 SDKROOT，只有 python 会加。
BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}

FILES = {
    "controller": os.path.join(SRC, "Managers/QuickPickController.swift"),
    "harness": os.path.join(TESTS, "UICaptureHarness.swift"),
    "weights": os.path.join(SRC, "Views/RecommendationWeightsView.swift"),
}
TOUCHED = set()


def read(name):
    path = FILES[name]
    TOUCHED.add(path)
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(name, text):
    with open(FILES[name], "w", encoding="utf-8") as handle:
        handle.write(text)


def sub(text, old, new, expect, label):
    got = text.count(old)
    if got != expect:
        raise AssertionError(f"{label}: needle 命中 {got} 次，期望 {expect} ⇒ DID-NOT-RUN，不注入")
    return text.replace(old, new)


def run(test_filter, needs_shots=False):
    env = dict(BASE_ENV)
    if needs_shots:
        shutil.rmtree(SHOTS, ignore_errors=True)
        os.makedirs(SHOTS, exist_ok=True)
        env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    # "红"必须是**测试跑完判的红**，不是编译不过：编译错 = DID-NOT-RUN（仓库里记过多次，
    # 把加载失败当成"抓到了缺陷"是最容易自我表扬的一类假绿）。
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


MUTATIONS = []


def mutation(mid, title, name, edits, test_filter, expect, needs_shots=False):
    MUTATIONS.append((mid, title, name, edits, test_filter, expect, needs_shots))


# M73：捕获入口建不出视图 ⇒ 那条"限制还在"的判据必须红（它没有对象了）。
mutation(
    "M73", "浮层捕获入口返回 nil", "controller",
    [(lambda s: sub(s, "        return panel.contentView",
                    "        _ = panel\n        return nil", 1, "M73")),
     ],
    "UICaptureTests/testQuickPickOverlayStillCannotBeCapturedOffscreen", "CAUGHT",
)

# M74：把"什么算没画出来"的阈值归零 ⇒ 尺子瞎了。
# 两条读者（捕获失效闸门 / 浮层限制判据）共用同一个常量，所以它们必须一起失去判别力 ——
# 这正是"一把尺两个读者"要的效果：改尺的地方只有一处。
mutation(
    "M74", "透明判定阈值归零（尺子失明）", "harness",
    [(lambda s: sub(s, "static let transparentAlphaCeiling: UInt8 = 8",
                    "static let transparentAlphaCeiling: UInt8 = 0", 1, "M74"))],
    "UICaptureTests/testQuickPickOverlayStillCannotBeCapturedOffscreen", "CAUGHT",
)

# M75：钉尺寸这件事其实有**两层**保险（13+ 的 `sizingOptions` 与 12 也能用的 min/max）。
# 第一版把 `sizingOptions = []` 换成 `[.idealSize]`，编译就挂了（OptionSet 的字面量类型对不上）
# —— 报 DID-NOT-RUN，不是红。改成"整行删掉"这种真实世界会发生的退法，并且拆成两支：
#   M75a 只删 `sizingOptions`（留着 min/max）⇒ 期望 EITHER：
#        红了说明这行有用；绿了说明**它是一行装饰**，min/max 才是干活的那个 ——
#        两种结果都要写进账本，这正是要问的问题。
#   M75b 两层都删 ⇒ 期望 CAUGHT（不变量必须抓到"帧名 ≠ 帧尺寸"）。
SIZING_BLOCK = """            if #available(macOS 13.0, *) {
                hosting.sizingOptions = []
            }
"""
MINMAX_BLOCK = """        window.contentMinSize = size
        window.contentMaxSize = size
"""

mutation(
    "M75a", "只删 sizingOptions（min/max 还在）", "harness",
    [(lambda s: sub(s, SIZING_BLOCK, "", 1, "M75a"))],
    "UICaptureTests/testCaptureKeyViews", "EITHER", needs_shots=True,
)

mutation(
    "M75b", "两层钉尺寸全删", "harness",
    [(lambda s: sub(s, SIZING_BLOCK, "", 1, "M75b")),
     (lambda s: sub(s, MINMAX_BLOCK, "", 1, "M75b"))],
    "UICaptureTests/testCaptureKeyViews", "CAUGHT", needs_shots=True,
)

# M76：把权重页夹具改回 560 高（内容 850）⇒ **没有任何测试会红**。
# 这条是故意放的"期望 ESCAPED"：它量出的是这一轮承认的缺口 ——
# 夹具的高度是记的数，改小它不会有任何守卫报警（只能靠人眼）。见 BACKLOG 32。
mutation(
    "M76", "权重页夹具退回 560 高（已知无人看守）", "harness",
    [(lambda s: sub(s, "Fixture(\"weights\", NSSize(width: 520, height: 880))",
                    "Fixture(\"weights\", NSSize(width: 520, height: 560))", 1, "M76"))],
    "UICaptureTests/testCaptureKeyViews", "ESCAPED", needs_shots=True,
)

# M77：只读数值退回强调蓝 ⇒ 颜色那条必须红。
mutation(
    "M77", "数值标签退回强调色", "weights",
    [(lambda s: sub(s, "        case .atDefault: return .secondary",
                    "        case .atDefault: return .accentColor", 1, "M77"))],
    "PressFeedbackTests/testReadOnlyWeightValueDoesNotWearTheActionableColor", "CAUGHT",
)

# M78：色调改用**未取整**的 value 判 ⇒ 0.999 会出现"写着默认、按改过的颜色画"。
mutation(
    "M78", "文字与颜色各用一套判据", "weights",
    [(lambda s: sub(s, "        if pct == 100 { return .atDefault }\n        return pct > 100 ? .raised : .lowered",
                    "        if value == 1.0 { return .atDefault }\n        return pct > 100 ? .raised : .lowered",
                    1, "M78"))],
    "PressFeedbackTests/testReadOnlyWeightValueDoesNotWearTheActionableColor", "CAUGHT",
)

# M79：行里自己再算一遍百分比（绕过 policy）⇒ 接线断言必须红。
mutation(
    "M79", "行里绕过 policy 自己算", "weights",
    [(lambda s: sub(s, "Text(WeightValuePresentation.percentageText(value: value))",
                    "Text(\"\\(Int((value * 100).rounded()))%\")", 1, "M79"))],
    "PressFeedbackTests/testReadOnlyWeightValueDoesNotWearTheActionableColor", "CAUGHT",
)

# M80：把黑带检测的地板抬到 400pt ⇒ 8 处材质盲区"消失"，名单必须红。
# 这条证的是：那份名单不是装饰，检测器真的在数东西。
mutation(
    "M80", "黑带检测地板抬到 400pt", "harness",
    [(lambda s: sub(s, "minRunPt: Double = 60", "minRunPt: Double = 400", 1, "M80"))],
    "UICaptureTests/testCaptureKeyViews", "CAUGHT", needs_shots=True,
)


def main():
    originals = {name: read(name) for name in FILES}
    digests = {path: open(path, "rb").read() for path in TOUCHED}

    # **第 0 支变异：什么都不改，先要求每一条被点名的判据能跑、而且是绿的。**
    # 第一版没有这一步，于是环境坏掉时八支变异一起 DID-NOT-RUN，
    # 而电池跑满了 47 分钟才让人发现"红"根本不是红、"绿"根本不是绿。
    # 预检不通过 ⇒ 当场退出，一支都不注入。
    print("=== 预检（不注入任何变异）===", flush=True)
    for test_filter, needs in sorted({(m[4], m[6]) for m in MUTATIONS}):
        verdict, out = run(test_filter, needs)
        ok = verdict == "ESCAPED"  # 未注入时"测试跑完且通过"= ESCAPED，这才是预检要的
        first = [line for line in out.splitlines() if "error:" in line][:1]
        print(f"  {test_filter:70s} {verdict:12s} {'OK' if ok else '!! ' + (first[0][:120] if first else '')}",
              flush=True)
        if not ok:
            for path, blob in digests.items():
                with open(path, "wb") as handle:
                    handle.write(blob)
            print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
            return 2

    results = []
    for mid, title, name, edits, test_filter, expect, needs_shots in MUTATIONS:
        text = originals[name]
        try:
            for edit in edits:
                text = edit(text)
        except AssertionError as exc:
            results.append((mid, "DID-NOT-RUN", f"{title}：{exc}"))
            continue
        write(name, text)
        try:
            verdict, out = run(test_filter, needs_shots)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(FILES[name], "wb") as handle:
                handle.write(digests[FILES[name]])
        mark = "OK " if (verdict == expect or expect == "EITHER") else "!! "
        detail = ""
        if verdict == "ESCAPED" and expect == "CAUGHT":
            detail = "  ← 该判据抓不到"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            detail = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, f"{mark}{title}（期望 {expect}）{detail}"))
        print(f"{mid}: {verdict} {title}", flush=True)

    print("\n=== R18 变异对照汇总 ===")
    for mid, verdict, line in results:
        print(f"  {mid:5s} {verdict:12s} {line}")
    # 还原自检比的是**电池开跑前自己抓的字节**，不是 git HEAD ——
    # 这一轮工作树本来就有未提交改动，拿 git 比会把"还原成功"读成"三个文件没还原"。
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
