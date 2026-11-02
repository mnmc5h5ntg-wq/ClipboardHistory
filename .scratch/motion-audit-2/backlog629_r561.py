# -*- coding: utf-8 -*-
"""R561 的 BACKLOG 629 追记：第三个 runner 真数 = 0 ⇒ 「≥2 在那台机器的钟上不是恒可满足」写进单子。

只写读数与两条出路的代价，不登记、不动地板、不改期望 —— 登记成 `sampled` 具名放行会改变
CI 拦什么，那是需要用户点头的一步（红线：不放宽任何守卫）。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "AGENT_BACKLOG.md")

BLOCK = u"""    第三数（R561 收口前复述，`41509855001 ↔ 26c1939` = concluded failure）：**过渡帧数 = 0** —— `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=0 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 声明=200ms 窗口=1966ms 每格=75.6ms`，红原文 `XCTAssertGreaterThanOrEqual failed: (0) is less than (2)`，`MOTION_FLOOR_FACTS judged=5/5 executed=79 not-run=- 红的用例=testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1` ⇒ **STEP[19] 那一跑因此红**。
    三个 runner 真数并排（同一份代码，R558→R560 三批）：**2（每格 71.5ms）/ 5（26.0ms）/ 0（75.6ms）** ⇒ 结论比 R560 那句「余量随钟漂」更硬：**「≥2 帧地板在那台机器的钟上不是恒可满足的」** —— 当每格粗到 70ms 以上，200ms 的过渡只摊到 2–3 格，两端夹逼要求「有一帧离两端都 ≥ 首末差×15%」就可能一帧都数不到（旧口径那一跑反而读 2 通过 ⇒ 两把尺对相位的敏感度不同，这正是 R558 双口径同印的理由）。
    处置（本轮只做到这里）：按 629 既有口径**具名入账**，**不重开产品排查、不动 ≥2 地板、不改期望、不自行登记**。同族先例住在登记表里：`suite_reds` 的 `testNativeRowMoveIsVisibleToTheRuler` 与 `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` 都是 `recurrence=sampled` 的"runner 采样导致帧数不够"。
    两条出路（**都动到冻结项 ⇒ 要用户点头，本轮不自行选**）：① 把这条红登记成 `recurrence=sampled` 具名放行 ⇒ CI 不再因它红，代价是"靠登记过绿"（`MOTION_FLOOR_REGISTERED_REDS` 会数得出来，但它确实不再拦）；② 把尺改成对采样相位不敏感（例如按实测每格与声明时长算出"这一跑理论上最多能落几帧"再判，等于给地板加一个随钟漂的上界）⇒ 不放宽 ≥2，但要把 120ms 阈值与 `stepFloorRatio` 的口径重钉并配刀。**在用户定夺之前，这一朵红每跑照抄、照记。**

"""


def main():
    check = "--check" in sys.argv
    t = io.open(P, encoding="utf-8").read()
    anchor = u"    限定（R559，635 结案时补）"
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD backlog629 hits=%d\n" % t.count(anchor))
        return 1
    if u"第三数（R561 收口前复述" in t:
        sys.stderr.write("ALREADY_WRITTEN\n")
        return 1
    i = t.index(anchor)
    j = t.find(u"\n", i)
    if not check:
        # 接在 R559 那条「限定」之后（同一单子里按时间正序读）
        t = t[:j + 1] + BLOCK + t[j + 1:]
        io.open(P, "w", encoding="utf-8").write(t)
    sys.stdout.write("BACKLOG629_R561_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
