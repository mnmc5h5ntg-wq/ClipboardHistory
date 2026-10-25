#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R349 七本台账（第 348 轮 / Round 346 · 产品 0 文件，判据账）。"""
import io, os
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding=u"utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding=u"utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

U = u"""## 第 348 轮（R349 · 2026-10-25 · U-1214…U-1218）：胶片第一次跑全 —— 而它测的不是产品那条 0.20（U-1214…U-1218 · 产品 0 文件，判据账）

- **U-1214：胶片在环境键下第一次跑全。** `CLIPBOARD_HISTORY_UI_MOTION=1` + `CLIPBOARD_HISTORY_MOTION_OUT=<dir>` ⇒
  `Executed 67 tests, with 3 skipped and 0 failures`（161.9 秒）；不设键时是 **24 格 skip**。四场都判了：
  `MOTION_SUMMARY notice-banner=11 notice-banner-dismiss=8 detail-kind-change=3 empty-state=2`、
  `MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`。
- **U-1215：空态场景自己声明 `160ms`。** `MOTION_GRAB empty-state 帧数=30 抓帧中位=19.5ms 抓帧最慢=53.1ms
  视图=380×552pt 像素=760×1104px 声明=160ms 色档=暗 请求=未钉` —— 这 160 是**夹具自己写死的**，
  不是 `MotionCatalog` 那一档。也就是说 R348 把产品的空态淡出改成 0.20 之后，**胶片这一格不会跟着变**：
  它测的是场景自己的声明，不是产品的接线。**第三方权威**（产品 token / 胶片声明）同一个量两份数。
- **U-1216："改了但胶片不动"不是没改，是胶片没接线。** 这一点必须写清楚，否则下一轮看到 `声明=160ms`
  会以为 R348 白改了。产品的源码形状守卫（`testEmptyStateFadeSharesThePillRhythm`）与刀 M1003 才是那半边的证人；
  胶片那半边要等 425。
- **U-1217：这一场景的过渡确实在动，而且不是只动 alpha。** `MOTION_AXIS empty-state 帧对=26 亮度峰值=0.1089
  alpha峰值=0.1063 并集峰值=0.1089 仅alpha在动=0/26` —— 26 帧对里没有一帧是"只动 alpha"，
  说明这条过渡在亮度与 alpha 两条轴上同时走（不是一条空转的淡入）。
- **U-1218：开 425。** 要胶片为 389 作证，得把场景的 `声明=160ms` 改成从 `MotionCatalog.duration(for:)` 读
  （一处权威），并在同一笔里重跑胶片、确认 `声明=200ms` 且四场判定不掉。在那之前，胶片**不许**替 389 说话。

"""

ITER = u"""## Round 346 · R349（第 348 轮 · 2026-10-25）：胶片跑全了，却发现它测的是自己的 160ms（产品 0 文件）

环境键下 67 格 3 skip / 0 fail（161.9 秒），四场 `judged=4/4`。但空态那场的 `声明=160ms` 是**夹具写死的**，
产品的 0.20 不在其中 —— "改了但胶片不动"是接线问题，不是改动无效。开 425（让声明读产品那支）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 胶片 30 帧抓取（中位 19.5ms、最慢 53.1ms），26 个帧对的亮度/alpha 峰值都读了；没逐张看图。 |
| 判据有效性 | 13/15 | 发现胶片与产品是两份权威；`MOTION_AXIS` 的 `仅alpha在动=0/26` 把"空转淡入"排除掉。 |
| 假绿防御 | 14/15 | 没有把"胶片四场全 judge"当成 R348 的验收 —— 证据链断在哪就写在哪。 |
| 产品面推进 | 6/15 | 产品 0 文件；产品面这一轮的产出是"知道胶片该接哪根线"。 |
| 台账一致性 | 13/15 | U-1214…U-1218 五条、D-346、425 新开；计数器现读抄。 |
| 交付诚实性 | 15/15 | `声明=160ms` 与"胶片不为 389 作证"都明写；R348 的改动没有被夸大。 |
| 可复核性 | 14/15 | 跑法（两个环境键 + 输出目录）与四条原始读数都在账上。 |

均分 ≈ 12.4/15（87/105）。
"""

BL = u"""
**425. 胶片的空态场景自己声明 `160ms`：同一个时长产品一处、夹具一处，胶片因此测不到产品的接线**（R349 现读）
    现读 `MOTION_GRAB empty-state … 声明=160ms`，而产品那一支是 `MotionCatalog.duration(for: .slider) = 0.20`。
    R348 把空态淡出接到药丸那支动画之后，胶片的读数**一个字没变** —— 因为场景按自己的 160ms 摆帧。
    这不是"改动无效"，是**夹具没接线**：判据想作证的那件事，它读的是另一份权威（记忆里同族：判据不许抄产品常量）。
    修法（下一轮）：场景的声明改成 `Int(MotionCatalog.duration(for: .slider) * 1000)`，同一笔里重跑胶片，
    要读到 `声明=200ms`、`judged=4/4` 不掉、`MOTION_AXIS` 的四条峰值仍在同一量级；
    若某条判定因此变红，先看它是不是把"160"当成了期望值（那同样是一份抄来的常量）。
"""

DEC = u"""
### D-346（349）判据想为某条产品行为作证，就必须读**产品那支**；夹具自己声明一份时长等于第三份权威

R349 现读：胶片空态场景 `声明=160ms`，产品空态淡出 R348 起是 0.20（`slider`）——改完重跑胶片，读数一字未变。
这不是"改没改"的问题，是**尺与产品各拿一份数**：胶片的帧号按 160 摆，产品按 200 走，两者永不相交。
**How to apply**：任何"按时间轴摆帧"的夹具，时长必须从 `MotionCatalog` 读（或由被测视图给出），
不许自己写；判据红/绿时先确认它读的是产品那支。判据里出现"160"这种字面量，默认当成抄来的常量审。
"""

CH = u"""### 胶片空态场景自己声明 160ms：它测不到产品那条 0.20，"改了胶片不动"是接线问题（R349 / U-1214…U-1218 · 产品 0 文件，判据账）
"""

STATE = u"""## R349 状态（2026-10-25 · 本地 · 第 348 轮 / Round 346）：胶片跑全了，却发现它测的是自己的 160ms（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R349 / 第 348 轮 / Round 346）：环境键下胶片 67 格 3 skip / 0 fail、四场 judged=4/4；
但空态场景 `声明=160ms` 是夹具自己写死的 ⇒ 它测不到 R348 接的那条 0.20（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3`、`↔ 0307c43` 首读 in_progress（只登记不轮询，R140）。
② 用 `CLIPBOARD_HISTORY_UI_MOTION=1` + `CLIPBOARD_HISTORY_MOTION_OUT=/tmp/r349_motion` 重跑胶片。
③ 读数：`MOTION_SUMMARY …`、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`、
   `MOTION_GRAB empty-state … 声明=160ms`、`MOTION_AXIS empty-state 帧对=26 … 仅alpha在动=0/26`。
④ 结论：胶片与产品是两份权威；"改了但胶片不动"是接线问题。开 BACKLOG 425（让声明读 `MotionCatalog`）。

验证读数（现读）：`Executed 67 tests, with 3 skipped and 0 failures`（161.9 秒；不设键时 24 skip）；
`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`；脚本电池 `Ran 646（skipped=4）OK`；帧 182（未重捕）；
产品面连续零改动 **4** 轮（`python3 scripts/product_streak.py --streak-for 348` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 425 的修法没做（本轮只把"两份权威"这件事钉住）；② 胶片未逐张看图（只读它自己打印的峰值）；
③ 真机腿没跑（这一轮改的是夹具侧的账）。

下一轮（R350）的靶：⓪ 读三跑 CI 配对 → ① **425**（声明读 `MotionCatalog` + 同笔重跑胶片，确认 `声明=200ms`、
四场不掉）→ ② 413（backing 名册）→ ③ 动效主线 397 / 390 / 384 / 387① / 376 / 367。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 347 轮（R348 · 2026-10-25 · U-1210…U-1213）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R348 状态（2026-10-25 · 本地 · 第 347 轮 / Round 345）"
    assert s.count(h) == 1; wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1213（R348 现读抬到最新一节）", u"U-31 … U-1218（R349 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-345**", u"| 决定台账 | D-069 … **D-346**")
    r = once(r, u"U 定义行最大 **U-1213**、决定最大 **D-345**、BACKLOG 最大 **424**",
             u"U 定义行最大 **U-1218**、决定最大 **D-346**、BACKLOG 最大 **425**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R348 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R349 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **3**（现读", u"产品面连续零改动轮数 = **4**（现读")
    r = r.rstrip(u"\n") + u"""
- **R349 续（判据账）**：胶片环境键下 67 格 3 skip / 0 fail、四场 judged=4/4；但空态场景 `声明=160ms`
  是夹具写死的 ⇒ 它测不到 R348 接的 0.20，"改了胶片不动"是接线问题（425）。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R349_LEDGERS_OK")

if __name__ == u"__main__":
    main()
