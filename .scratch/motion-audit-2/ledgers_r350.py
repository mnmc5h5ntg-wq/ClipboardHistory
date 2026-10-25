#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R350 七本台账（第 349 轮 / Round 347 · 产品 0 文件，判据账）。"""
import io, os
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

U = u"""## 第 349 轮（R350 · 2026-10-25 · U-1219…U-1223）：胶片的空态声明改读药丸那一支 —— 425 结案（U-1219…U-1223 · 产品 0 文件，判据账）

- **U-1219：胶片的声明从 `.contentFade` 改成 `.slider`，三次抓取都读 `声明=200ms`。**
  `MOTION_GRAB empty-state … 声明=200ms`（暗 / 亮 / 未钉三档各一条，帧数 30、抓帧中位 19.2/19.5/19.1ms、最慢 58.0/43.6/52.9ms）；
  `MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` —— 四场判定一条没掉。425 到此结案：
  R348 接的那条 0.20 现在**胶片也看得见**。
- **U-1220：新守卫把"产品的接线"与"胶片的声明"钉在同一格。** `testEmptyStateFadeSharesThePillRhythm` 除了读
  `HistorySidebarView` 那一行，还读 `MotionFilmstripTests` 的 `emptyState()` 块：声明必须是 `.slider`、不许回到 `.contentFade`。
- **U-1221：守卫第一版把别的场景判成违规。** 全文搜 `MotionCatalog.duration(for: .contentFade) * 1000` 会命中
  `detail-kind-change` 那一场（它本来就该用 contentFade）⇒ 当场红。改成**按块切片**（从 `static func emptyState()` 到
  下一个 `static func`）之后才对。**同一条字面量在不同场景里合法与否不同**，判据必须带作用域。
- **U-1222：想给这条配第二把刀，没落成。** 把声明换回 160ms 的那一刀在 `落刀后回读不匹配` — 因为替换串
  （`.contentFade) * 1000) { store in`）在文件里**不唯一**（别的场景本来就有）。这一刀记 **NOT-RUN**，并从表里撤掉
  （留着它会让"CAUGHT=0/1"读成判据没牙，其实是刀没落下）。开 426。
- **U-1223：全量卷与电池。** `Executed 1025 tests, with 47 skipped and 0 failures`；脚本电池 `Ran 646（skipped=4）OK`；
  本轮唯一的刀 M1003 复跑 `CAUGHT=1/1, RESTORE_CLEAN=yes`。

"""

ITER = u"""## Round 347 · R350（第 349 轮 · 2026-10-25）：胶片改用产品的 0.20，425 结案（产品 0 文件）

空态场景的 `declaredDurationMilliseconds` 从 `.contentFade`(160) 改成 `.slider`(200)，三次抓取全读 `声明=200ms`、`judged=4/4`。
守卫扩到胶片侧，并按块切片（`.contentFade` 在别的场景合法）。第二把刀没落成（替换串不唯一）⇒ 记 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 胶片的 30 帧/场、抓帧中位与最慢都抄回；没有逐张看图（这一轮的对象是声明与帧数）。 |
| 判据有效性 | 14/15 | 声明与产品接线钉在同一格；按块切片避免了误伤别的场景（U-1221 是它自己的红换来的）。 |
| 假绿防御 | 14/15 | 第二把刀没落成就记 NOT-RUN 并撤表，没有把 CAUGHT=0/1 说成"判据没牙"。 |
| 产品面推进 | 7/15 | 产品 0 文件；但 R348 的产品改动现在有了胶片侧的证词（`声明=200ms`）。 |
| 台账一致性 | 13/15 | U-1219…U-1223 五条、D-347、425 结案 + 426 新开；计数器现读抄。 |
| 交付诚实性 | 15/15 | 刀没落下、守卫误伤一次，两件都写在账上。 |
| 可复核性 | 14/15 | 两个环境键 + 输出目录 + 四条原始读数都在；刀可重跑。 |

均分 ≈ 12.7/15（89/105）。
"""

BL = u"""
425 结案（R350）：胶片空态场景的声明从 `.contentFade`(160ms) 改成 `.slider`(200ms)，与产品接线一致；
    三次抓取现读 `MOTION_GRAB empty-state … 声明=200ms`（暗/亮/未钉），`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`。
    守卫 `testEmptyStateFadeSharesThePillRhythm` 现在同时读产品那一行与胶片那一块（按块切片，见 U-1221）。

**426. 变异刀的**替换串**也必须在文件里唯一：只查 needle 唯一是不够的**（R350 现读）
    R350 想给 425 配一把刀（把胶片声明换回 `.contentFade`），落刀后回读得到 `不匹配` —— 因为替换串
    （`.contentFade) * 1000) { store in`）在这个文件里**别的场景本来就有**，`read(path).count(repl)==1` 不成立，
    刀根本落不下去（跑器打 `NOT_RUN 落刀后回读不匹配`）。现有的六条规矩只要求**原文 needle 恰好命中一次**；
    这一轮补上第七条的候选：**替换串也要恰好一次**，否则"落刀成功"与"文件本来就这样"分不开。
    退场条件：等把两张表改成"替换后再 dump 出一份 diff"的判法（diff 里必须恰好一行变化），就可以只查 diff。
"""

DEC = u"""
### D-347（350）变异刀有**两个**唯一性：原文 needle 唯一 + 替换串唯一

R350 现读：把胶片声明换回 `.contentFade` 的那一刀打 `落刀后回读不匹配` —— 原文 needle 是唯一的，但替换串
在文件里不唯一（别的场景本来就有同一句）。于是一个**合法的刀**被判成"没落下"，`CAUGHT=0/1` 会被读成判据没牙。
**How to apply**：新写刀时两个唯一性都查；替换串不唯一就换一刀（改成一整段带上下文的替换），
或者把回读判据改成"改动前后恰好一行不同"。**不许把这种 NOT_RUN 记成 CAUGHT，也不许记成判据无效**。
"""

CH = u"""### 胶片的空态声明改读药丸那一支（160→200ms），425 结案；刀的第二唯一性记成 426（R350 / U-1219…U-1223 · 产品 0 文件，判据账）
"""

STATE = u"""## R350 状态（2026-10-25 · 本地 · 第 349 轮 / Round 347）：胶片改用产品的 0.20，425 结案（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R350 / 第 349 轮 / Round 347）：胶片空态声明从 `.contentFade`(160) 改成 `.slider`(200)，
三次抓取 `声明=200ms`、`judged=4/4`；守卫按块切片钉住两边（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3`、`↔ 0307c43`、`↔ 4fe06c2` 均按首读登记（只登记不轮询，R140）。
② 夹具：`MotionFilmstripTests.emptyState()` 的 `declaredDurationMilliseconds` 改成 `MotionCatalog.duration(for: .slider) * 1000`。
③ 守卫：`testEmptyStateFadeSharesThePillRhythm` 扩到胶片侧，**按 `emptyState()` 块切片**（`.contentFade` 在别的场景合法）。
④ 重跑胶片（两个环境键 + 输出目录）：`MOTION_GRAB empty-state … 声明=200ms` ×3、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`。
⑤ 想配第二把刀（声明换回 160）没落成：替换串不唯一 ⇒ `NOT_RUN 落刀后回读不匹配`，撤表并开 426。

验证读数（现读）：胶片三档 `声明=200ms`（帧数 30、中位 19.1–19.5ms、最慢 43.6–58.0ms）；
全量卷 `Executed 1025 tests, with 47 skipped and 0 failures`；脚本电池 `Ran 646（skipped=4）OK`；
M1003 复跑 `CAUGHT=1/1, RESTORE_CLEAN=yes`；产品面连续零改动 **2** 轮
（`python3 scripts/product_streak.py --streak-for 349` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 第二把刀（夹具声明换回 160ms）没落成：替换串不唯一（426）；② 胶片未逐张看图；
③ 真机腿没跑（本轮改的是夹具声明）。

下一轮（R351）的靶：⓪ 读三跑 CI 配对 → ① 413（backing 名册 + 两档材质帧）→ ② 动效主线 397 / 390 / 384 / 387① / 376 / 367
→ ③ 426 的退场（把两张表改成 diff 判法）。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 348 轮（R349 · 2026-10-25 · U-1214…U-1218）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R349 状态（2026-10-25 · 本地 · 第 348 轮 / Round 346）"
    assert s.count(h) == 1; wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1218（R349 现读抬到最新一节）", u"U-31 … U-1223（R350 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-346**", u"| 决定台账 | D-069 … **D-347**")
    r = once(r, u"U 定义行最大 **U-1218**、决定最大 **D-346**、BACKLOG 最大 **425**",
             u"U 定义行最大 **U-1223**、决定最大 **D-347**、BACKLOG 最大 **426**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R349 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R350 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **1**（现读", u"产品面连续零改动轮数 = **2**（现读")
    r = r.rstrip(u"\n") + u"""
- **R350 续（判据账）**：胶片空态声明 160→200ms（跟产品 `.slider`），三档现读 `声明=200ms`、`judged=4/4`；
  守卫按块切片钉住产品与胶片两边；第二把刀因替换串不唯一记 NOT-RUN（426）。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R350_LEDGERS_OK")

if __name__ == u"__main__":
    main()
