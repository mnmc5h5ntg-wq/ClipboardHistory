#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R348 七本台账（第 347 轮 / Round 345 · 产品 1 文件，动效主线）。"""
import io, os
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding=u"utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding=u"utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

U = u"""## 第 347 轮（R348 · 2026-10-25 · U-1210…U-1213）：空态淡出与药丸换成同一个节奏 —— 389 结案（U-1210…U-1213 · 产品 1 文件，动效主线）

- **U-1210：同一个手势的两半现在共用一个动画。** `HistorySidebarView` 里"空态出现/消失"那一格以前走
  `contentFade`（0.16），而药丸走 `slider`（0.20）—— 切筛选把列表切空（或切回）时，内容先落定、药丸还在走。
  本轮把它改成 `FilterPillMotion.slideAnimation(reduceMotion: shouldReduce)`（并给这个视图补了
  `@Environment(\\.accessibilityReduceMotion)` 与 `shouldReduce`）；`VisualFill` 与几何一字未动，过渡仍是 `.opacity`。
- **U-1211：守卫是源码形状 + 一把刀。** `testEmptyStateFadeSharesThePillRhythm` 钉两件事：
  那一行必须是 `slideAnimation`，且**不许**再出现 `contentFade` 那一行。`mutate_r348.py` M1003 把它换回去
  ⇒ `CAUGHT=1/1, RESTORE_CLEAN=yes`；预检 `tables=129`。
- **U-1212：既有的"恰好一处"契约被本轮撞红，判据改得更严而不是更松。** `testSidebarConsumesTheMotionPolicy…`
  原来数 `slideAnimation` 恰好出现 1 次 —— 本轮合理地多了第二处消费（空态淡出），那个"1"就不再是契约。
  改成：**每一处写死动画写法都不许出现**（`.spring(` / `.easeIn(` / `.easeOut(`；`.linear(duration: 0)` 是策略
  自己的减少动态分支，排除），并保留"至少一处由策略给出"。比原来盯着一个数更严。
- **U-1213：胶片场景的 after 曲线没拿到。** `swift test --filter MotionFilmstripTests` 现读 67 格 **24 格 skip**
  （胶片捕获要环境键），没有 `MOTION_PILL_SLIDE` 那种逐格序列 ⇒ 这一轮只有"同一个动画对象"的源码证据与刀，
  没有像素级的落点曲线。写成 NOT-RUN，不冒充。

"""

ITER = u"""## Round 345 · R348（第 347 轮 · 2026-10-25）：空态淡出与药丸共用同一个节奏，389 结案（产品 1 文件）

`HistorySidebarView` 的空态淡出从 `contentFade`(0.16) 换成 `FilterPillMotion.slideAnimation`(0.20)：
切筛选切空/切回时，内容与药丸是同一个手势的两半，现在同一个动画。源码形状守卫 + 刀 M1003（CAUGHT=1/1）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 11/15 | 本轮改的是时长，静态帧不变；胶片曲线没拿到（24 格 skip）—— 没有"看起来更好"的断言，只留源码与刀。 |
| 判据有效性 | 13/15 | 源码形状守卫两条断言（必须是 slideAnimation、不许是 contentFade）；刀把它换回去能抓住。 |
| 假绿防御 | 14/15 | 既有"恰好一处"契约被撞红时，改的是判据的形状（禁写死动画）而不是删断言；`.linear(duration: 0)` 的排除写了理由。 |
| 产品面推进 | 12/15 | 产品 1 文件：空态与药丸同节奏；389 这个开了二十轮的条目结案。 |
| 台账一致性 | 13/15 | U-1210…U-1213 四条、D-345、389/424 结案追记；计数器现读抄。 |
| 交付诚实性 | 15/15 | 胶片 after 曲线没拿到就写 NOT-RUN；全量卷 1 红（既有契约）也如实记并说明改法。 |
| 可复核性 | 14/15 | 一行 grep 能看到那一格；刀可重跑；全量卷结论在 /tmp/r348_full2.log。 |

均分 ≈ 13.1/15（92/105）。
"""

BL = u"""
389 结案（R348）：`HistorySidebarView` 的空态淡出与药丸现在共用 `FilterPillMotion.slideAnimation`（0.20）。
    这一单开了二十轮：R328 只把"6–7 格对 12 格"当采样现象挂起；R347 把两个时长读成两个数（0.16 / 0.20）；
    R348 把它改成一个动画对象，并用源码形状守卫 + 一把刀（M1003）钉住。胶片场景的 after 曲线仍欠
    （`MotionFilmstripTests` 24 格 skip，要环境键），所以"落点差 1–2 格"这句话本轮**没有**再量。

424 结案（R348，与 389 同一件事）：接线点找到了 —— 不在列表视图里，而在 `HistorySidebarView` 的
    `.animation(…, value: historyStore.filteredEntries.isEmpty)` 那一行（空态淡入淡出的驱动）。
    已改成药丸同一支动画；后续若要动"内容换页"的其它位点，先看 `MotionCatalog` 的 `.contentFade` 那几处
    （DetailView / SettingsView / QuickPick），它们各自有对象，不许一并改。
"""

DEC = u"""
### D-345（348）同一个手势的两半必须共用一支动画；把"调用点计数"当契约会挡住合理的第二处消费

R348 现读：空态淡出（0.16）与药丸滑动（0.20）是同一个手势的两半，落点差 1–2 格（R328 的 6–7 对 12）。
修法是把空态那一格换成药丸那支动画。撞红的是 `testSidebarConsumesTheMotionPolicy…` 里"`slideAnimation` 恰好一处"
——那个"1"只是当时只有一处消费，不是契约。改成"**没有一处**写死动画写法"之后，判据比原来更严。
**How to apply**：写"策略只有一个作者"这类守卫时，断的必须是**写法**（不许出现 `.spring(`/`.easeIn(` 等裸写法），
不是**次数**；次数会随合理的第二处消费者变化，而写法不会。
"""

CH = u"""### 空态淡出与药丸共用同一支动画：0.16 与 0.20 的两个落点合而为一（R348 / U-1210…U-1213 · 产品 1 文件，动效主线）
"""

STATE = u"""## R348 状态（2026-10-25 · 本地 · 第 347 轮 / Round 345）：空态淡出与药丸同节奏（产品 1 文件，动效主线）

最后更新：2026-10-25（本地 · R348 / 第 347 轮 / Round 345）：把空态淡出从 `contentFade`(0.16) 换成药丸那支
`slideAnimation`(0.20)，389 结案；既有"恰好一处"契约随之改成"没有写死动画写法"（产品 1 文件 · 动效主线）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3` 与 `RUN=… ↔ 0307c43` 均首读 in_progress（只登记不轮询，R140）。
② 产品：`HistorySidebarView` 空态那一格改用 `FilterPillMotion.slideAnimation`，并补 `reduceMotion` / `shouldReduce`。
③ 判据：新增 `testEmptyStateFadeSharesThePillRhythm`（源码形状两断言）；刀 `mutate_r348` M1003 `CAUGHT=1/1`。
④ 既有 `testSidebarConsumesTheMotionPolicy…` 的"恰好一处"被撞红 ⇒ 改成"禁写死动画写法"（更严）。
⑤ 全量卷 `Executed 1025 tests, with 47 skipped and 0 failures`；构建 0 告警；换装 `INSTALL_RESULT=ok`。

验证读数（现读）：`M1003 CAUGHT=1/1, RESTORE_CLEAN=yes`；预检 `tables=129 covered=110 arms=369 bad=0`；
脚本电池 `Ran 646（skipped=4）OK`；帧 182（时长改动不影响静态帧，未重捕）；
产品面连续零改动 **2** 轮（`python3 scripts/product_streak.py --streak-for 347` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 胶片场景的 after 逐格曲线：`MotionFilmstripTests` 67 格 **24 skip**（要环境键），
本轮只有"同一个动画对象"的源码证据与刀；② 真机腿没跑（改的是时长，屏幕那半边要另一次捕获）；③ 无第二把刀
（这一刀已经把"换回去"钉住）。

下一轮（R349）的靶：⓪ 读三跑 CI 配对 → ① 用环境键重跑胶片，把 after 的落点差量出来（补 389 的最后一句）
→ ② 413（backing 名册）→ ③ 动效主线 397 / 390 / 384 / 387① / 376 / 367。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 346 轮（R347 · 2026-10-25 · U-1205…U-1209）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R347 状态（2026-10-25 · 本地 · 第 346 轮 / Round 344）"
    assert s.count(h) == 1; wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1209（R347 现读抬到最新一节）", u"U-31 … U-1213（R348 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-344**", u"| 决定台账 | D-069 … **D-345**")
    r = once(r, u"U 定义行最大 **U-1209**、决定最大 **D-344**、BACKLOG 最大 **424**",
             u"U 定义行最大 **U-1213**、决定最大 **D-345**、BACKLOG 最大 **424**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R347 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R348 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **2**（现读", u"产品面连续零改动轮数 = **3**（现读")
    r = r.rstrip(u"\n") + u"""
- **R348 续（动效主线）**：空态淡出与药丸共用 `slideAnimation`（0.16→0.20），389/424 结案；
  源码形状守卫 + M1003 `CAUGHT=1/1`；全量卷 1025 格 0 失败；既有"恰好一处"契约改成"禁写死动画写法"。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R348_LEDGERS_OK")

if __name__ == u"__main__":
    main()
