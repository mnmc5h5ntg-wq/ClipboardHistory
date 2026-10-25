#!/usr/bin/env python3
"""R77 的变异对照：两态相减那几把尺子加了 alpha 这根轴之后，每一根轴是不是真的有人在读。

被钉的东西分三层，各自会坏在不同地方：
  ① `axisPair` 的三根轴（亮度 / alpha / 并集）—— 由 `testTheAxisRulerSeparatesAlphaFromLuminance`
     的八格真值表钉（含"暗墨只在 alpha 上动 ⇒ 亮度轴读 0"那一格，R76 的 U-132 是同族实物）。
  ② `testEveryTwoStateRulerReadsBothAxes` 那条守卫 —— 扫四个测试文件，
     凡"读了第三根通道、又做两态减法、却不读第四根通道"的尺子都必须带理由登记。
  ③ 两条**豁免**的理由（`rgbFraction`×2、`meanChannelDelta`）—— 名单里必须有理由、
     而且不能剩着已经不存在的条目。

十刀：
  M403 并集退化成"只看亮度"        ⇒ 只有 AXIS 该红（这一刀就是 R77 之前的世界）
  M404 并集写成 max(rgb, alpha)     ⇒ 只有 AXIS 该红（splitAxes 那一格专门抓它）
  M405 alpha 的地板比亮度粗(30)     ⇒ 只有 AXIS 该红（两轴共用地板才可比）
  M406 alpha 用 signed 差、不取绝对值 ⇒ 只有 AXIS 该红（淡出那一臂会读出另一个数）
  M407 把 `PressInteractionProbeTests.changedFraction` 改回三通道 ⇒ 只有 GUARD 该红
  M408 把一条豁免的理由缩成「见注释」 ⇒ 只有 GUARD 该红（放宽必须带理由）
  M409 名单里剩一条不存在的尺子        ⇒ 只有 GUARD 该红（过期名单比没名单更坏）
  M410 把 `bandHeadTailDiff` 改回三通道 ⇒ 只有 GUARD 该红（本轮自己修的那把也要有人看着）
  M411 把守卫的"用没用 alpha"放宽成"提过就算" ⇒ 只有 GUARD 该红（正对照 C 必须抓得住这一刀）
  M412 把"扫之前剥掉行尾注释"撤掉        ⇒ 只有 GUARD 该红（正对照 D 必须抓得住这一刀）

## 第一版电池教出来的那一刀（M407 ESCAPED，已修）

第一遍跑（`/tmp/r77_mutation_battery.log`）里 M407 是 **ESCAPED**：那一刀把
`if delta > 6 || alphaDelta > 6` 的后半截删掉，而 `let alphaDelta = abs(a[index + 3] - b[index + 3])`
那一行**还留在函数体里** ⇒ 旧守卫查的是"函数体里有没有出现过 + 3]"，于是照旧绿。
形状与 R75 的 M395 同一族（守卫被"提到"喂饱，而不是被"用了"喂饱），只是这次被喂的是**一行死读数**。
修法两步：① 判"用没用"——要求存在一行里 **同时** 出现 alpha 与比较运算（`alpha > 8` / `alphaDelta > 6`）；
② 扫之前先剥**行尾注释**（M407 第二遍还是 ESCAPED：变异行 `if delta > 6 { … }  // 又不读 alpha 了`
同一行里被注释凑齐了 alpha 与 `>` ⇒ 守卫扫的是行，不是代码）。
这两步各带一个正对照（读了不用 / 注释里提一句），并各挨一刀元层变异（M411 / M412）与一刀元层变异（M411 把规则放宽回去，必须红）。
顺带把守卫扩成**双向**：`只读亮度` 与 `只读alpha` 各一张名册（后者是 UICaptureHarness 里
R67/R76 那两把故意只读 alpha 的尺子 + R77 新建的报告尺），代价记进 BACKLOG 108。

三条电池规矩沿用 R64/R66/R67/R68/R71/R74/R75/R76：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场、变异文不含原文）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。编号从 M403 起（M398–M402 是 R76 的，先在台账查重）。

用法：`python3 .scratch/motion-audit-2/mutate_r77_axes.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
MFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
PFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/PressFeedbackTests.swift"
PIP = "ClipboardHistory/Tests/ClipboardHistoryAppTests/PressInteractionProbeTests.swift"
LOCK = "/tmp/r77_mutation.lock"

AXIS = "testTheAxisRulerSeparatesAlphaFromLuminance"
GUARD = "testEveryTwoStateRulerReadsBothAxes"
PRESS = "testPressedAppearanceIsVisibleAt44PointsChannelByChannel"
LADDER = "testFillLaddersAreVisibleOnBothControlClasses"
CASES = [AXIS, GUARD, PRESS, LADDER]
FILTER = "|".join(["MotionFilmstripTests/" + AXIS, "MotionFilmstripTests/" + GUARD,
                   "PressFeedbackTests/" + PRESS, "PressFeedbackTests/" + LADDER])

EXPECTED = {
    "M403": [AXIS],
    "M404": [AXIS],
    "M405": [AXIS],
    "M406": [AXIS],
    "M407": [GUARD],
    "M408": [GUARD],
    "M409": [GUARD],
    "M410": [GUARD],
    "M411": [GUARD],
    "M412": [GUARD],
}

MUTATIONS = [
    ("M403", "并集那一轴退化成『只看亮度』⇒ 就是 R77 之前的世界。真值表里『暗墨在 alpha 上淡入』那一格必须红",
     MFT,
     '                if rgb > 8 || alpha > 8 { changedEither += 1 }\n',
     '                if rgb > 8 { changedEither += 1 }  // R77 变异\n'),

    ("M404", "把并集写成 max(rgb, alpha)：看起来一模一样、多数场合也确实够用，"
             "但『两轴各动一半』时把变化量低估一半 ⇒ splitAxes 那一格专抓它",
     MFT,
     '        return AxisPair(rgb: Double(changedRgb) / n, alpha: Double(changedAlpha) / n,\n'
     '                        either: Double(changedEither) / n)\n',
     '        return AxisPair(rgb: Double(changedRgb) / n, alpha: Double(changedAlpha) / n,\n'
     '                        either: max(Double(changedRgb) / n, Double(changedAlpha) / n))  // R77 变异\n'),

    ("M405", "alpha 的地板从 8 改成 30（比亮度那一根粗）⇒ 『两轴共用门槛』这句话作废，"
             "而读数里那两列就不再可比了。过地板那一格（9/255）必须红",
     MFT,
     '                if alpha > 8 { changedAlpha += 1 }\n',
     '                if alpha > 30 { changedAlpha += 1 }  // R77 变异\n'),

    ("M406", "alpha 用 signed 差、不取绝对值 ⇒ 『变淡』与『变浓』读出两个数，"
             "而淡出那一臂正好是变淡。极性那一格必须红",
     MFT,
     '                let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[p + 3]))\n',
     '                let alpha = Int(b.pixels[p + 3]) - Int(a.pixels[p + 3])  // R77 变异\n'),

    ("M407", "把 `PressInteractionProbeTests.changedFraction` 改回只读三根通道（本轮修前的样子）"
             "⇒ 守卫必须点名这条未登记的盲区尺",
     PIP,
     '            if delta > 6 || alphaDelta > 6 { changed += 1 }\n',
     '            if delta > 6 { changed += 1 }  // R77 变异：又不读 alpha 了\n'),

    ("M408", "把一条豁免的理由缩成『见注释』⇒ 名单还在、等式还成立，但放宽不再有代价"
             "（R75 那一课：没有理由的名单等于把守卫撤了）",
     MFT,
     '            (qualifiedName: "PressFeedbackTests.swift#rgbFraction",\n'
     '             reason: "单轴报告尺。它的存在就是为了把亮度那一根**单独**报出来，配对的那条叫 alphaFraction，"\n'
     '                    + "真正做判断的是同文件里的 changedFraction（已经是并集）。"\n'
     '                    + "给它补 alpha 就等于把两根轴重新混成一个数 —— 那正是本轮要拆开的东西。"),\n',
     '            (qualifiedName: "PressFeedbackTests.swift#rgbFraction", reason: "见注释"),\n'),

    ("M409", "名单里剩一条已经不存在的尺子 ⇒ 过期登记必须红。"
             "（这一刀与 M407 一起才把那条等式钉成**双向**：少一条红、多一条也得红）",
     MFT,
     '            (qualifiedName: "PressInteractionProbeTests.swift#rgbFraction",\n',
     '            (qualifiedName: "MotionFilmstripTests.swift#imaginaryRuler",\n'
     '             reason: "M409 造的过期登记：它不对应任何真实尺子，守卫必须在名单剩着不存在的条目时就红，'
     '因为过期名单比没名单更坏。"),\n'
     '            (qualifiedName: "PressInteractionProbeTests.swift#rgbFraction",  // M409 锚点改写\n'),

    ("M410", "把 `bandHeadTailDiff`（本轮一起修掉的那把位置尺）改回只读三根通道"
             "⇒ 守卫必须抓到自己文件里的这一条：它不是历史遗留，是本轮新修的",
     MFT,
     '                    let alpha = abs(Int(a.pixels[p + 3]) - Int(b.pixels[q + 3]))\n'
     '                    if rgb > 8 || alpha > 8 { changed += 1 }\n',
     '                    if rgb > 8 { changed += 1 }  // R77 变异：这条尺子退回三通道\n'),

    ("M411", "元层一刀：把守卫里『alpha 有没有参与判定』放宽回『函数体里提过 alpha 就算』"
             "⇒ 正对照 C（读了不用那一格）必须红。这一刀钉的是**修法本身**有牙 —— "
             "M407 第一次跑就是 ESCAPED，靠的就是这条被放宽掉的判据",
     MFT,
# R386：这一行改成两行了（R80 加了 lowercased）⇒ 旧针烂。改钉当前两行整块。
     '            let alphaInVerdict = body.contains { $0.lowercased().contains(axisMarker)\n'
     '                && $0.contains(comparisonMarker) }\n',
     '            let alphaInVerdict = body.contains { $0.lowercased().contains(axisMarker) }  // R77 变异：提过就算\n'),

    ("M412", "第二刀的元层版：把『扫之前剥掉行尾注释』这一步撤掉"
             "⇒ 正对照 D（注释里提一句 alpha 那一格）必须红。"
             "M407 第二次 ESCAPED 就是从这儿走的：`if delta > 6 { … }  // 又不读 alpha 了` "
             "同一行里凑齐了 alpha 与 `>`，守卫把瞎尺子判成好尺子",
     MFT,
     '            .map { Self.strippingTrailingComment($0) }\n',
     '            .map { $0 }  // R77 变异：不剥行尾注释\n'),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run(filter_expression):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(["swift", "test", "--filter", filter_expression],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr


def verdicts_of(text, cases):
    out = {}
    for case in cases:
        if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text):
            out[case] = "red"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text):
            out[case] = "green"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' skipped" % re.escape(case), text):
            out[case] = "skipped"
        else:
            out[case] = "absent"
    return out


def failure_messages(text, cases):
    hits = []
    for line in text.splitlines():
        if "error: -[" in line and any(case in line for case in cases):
            hits.append(line[:260])
    return hits


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        originals = {path: read(path) for _, _, path, _, _ in MUTATIONS}
        print("=== 基线（未变异）：四条判据都必须绿 ===")
        text = run(FILTER)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-62s = %s" % (case[:62], mark))
        if any(mark != "green" for mark in base.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, CASES)[:6]:
                print("     " + line)
            return 1

        for tag, note, path, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            if needle in replacement:
                print("   DRIFT-NOT-APPLIED 变异文包含原文 ⇒ 回读必然判『没落地』，先改刀")
                results.append((tag, "NOT-APPLIED"))
                continue
            source = read(path)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文找不到 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            print("   落地确认（%s）" % os.path.basename(path))
            try:
                text = run(FILTER)
                marks = verdicts_of(text, CASES)
                reds = [c for c in CASES if marks[c] == "red"]
                compile_failed = "error:" in text and not reds
                if reds == EXPECTED[tag]:
                    print("   CAUGHT 只红在预期那一条：%s" % marks)
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif not reds:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                else:
                    print("   ESCAPED 红的不是预期那一条（或连带红了别的）：%s 预期=%s"
                          % (marks, EXPECTED[tag]))
                    results.append((tag, "ESCAPED"))
                for line in failure_messages(text, CASES)[:3]:
                    print("     " + line)
            finally:
                write(path, originals[path])
                print("   已还原（逐字节相同：%s）" % (read(path) == originals[path]))

        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0),
                 counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 \
            and counts.get("NOT-RUN", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
