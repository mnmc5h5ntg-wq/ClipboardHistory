#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R346 七本台账（第 345 轮 / Round 343 · 产品 0 文件，判据账）。"""
import io, os
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding=u"utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding=u"utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

U = u"""## 第 345 轮（R346 · 2026-10-25 · U-1200…U-1204）：九张变异表的汇总正则只认复数 —— 修完再给它一条会红的名单守卫（U-1200…U-1204 · 产品 0 文件，判据账）

- **U-1200：422 的范围第一次数清。** 用 `ast` 把 55 张 `mutate_*.py` 里"以汇总行开头的字符串常量"抽出来分类：
  **51 张已经认单数**（`tests?`），**9 张只认复数**（`Executed (\\d+) tests`）—— 那 9 张里任何一格只跑 1 个用例时
  都会被判成"没解析到 ⇒ 红"，正是 R345 我自己撞到的假红（`mutate_r345` 的第一跑 `PRECHECK_FAILED`）。
- **U-1201：九张都改成 `tests?` / `failures?`。** r130 / r133 / r135 / r141 / r142 / r335 / r336 / r338 / r339。
  其中 r141 的写法是 `Executed (\\d+) tests`（**没有逗号**），第一遍批量替换按 `tests,` 找锚点，漏了它 ——
  第二次按 `Executed (\\d+) tests?` 的正则才补上（"同一句有两种写法"又一次）。
- **U-1202：守卫不是逐张跑，而是对每一张表做**`re.compile` 后喂两条真实形状**。** 新增
  `scripts/tests/test_mutation_summary_regex.py`：单数 `Executed 1 test, with 0 failures` 与复数
  `Executed 9 tests, with 1 failure` 两条都必须匹配；名单地板 40 张（防止扫错目录）、"扫到的常量必须 > 0"。
  现在 `Ran 646`（比上一轮多 1）。
- **U-1203：守卫第一版把 needle 也当成了正则。** `mutate_r262.py` 的刀针里嵌着一行 `LITERAL = re.compile(r'Executed (\\d+) tests?\\b')`，
  静态扫描按"含 `Executed (`"取常量时把它也取了进来，于是它被当成"只认复数的表"报红 —— **尺读错了对象**
  （D-341 又一次）。改成只认**以 `Executed (` 开头**的常量之后通过：那才是运行器的汇总正则，嵌入的源码行不是。
- **U-1204：报告里「最后一次动到 Sources」那格跟着本轮之前的产品提交走。** `report_sources_cell.py --write` 现读
  `账上=R339/fb2cea0 git=R345/8d375b3` ⇒ 改写成 R345，复核一致。这一格是**派生**的，不是手抄。

"""

ITER = u"""## Round 343 · R346（第 345 轮 · 2026-10-25）：九张变异表认不出单数汇总行 —— 修完配一条会红的名单守卫（产品 0 文件）

`Executed 1 test, with 0 failures`（单数）在 9 张表里不匹配 ⇒ 单格只跑一个用例时被当成"没解析到 ⇒ 红"。
九张都改成 `tests?`，并新增一条对**每一张表**运行的守卫（两种形状都要匹配），名单地板 40 张。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 这一轮没有像素改动（产品 0 文件），看图腿不适用；理由写在这里而不是留空。 |
| 判据有效性 | 14/15 | 新守卫对每张表都在真正则上跑两种形状；名单地板 + "扫到 > 0" 两条防空对账。 |
| 假绿防御 | 14/15 | 修完立刻加会红的守卫；守卫自己第一版读错对象（把 needle 当正则）被当场发现并收窄。 |
| 产品面推进 | 6/15 | 产品 0 文件（工具轮）；但产品线的验收工具从此不再因单数汇总行假红。 |
| 台账一致性 | 13/15 | U-1200…U-1204 五条、D-343、422 结案追记；计数器与 §1 现读抄。 |
| 交付诚实性 | 15/15 | 9 张表的文件名逐张列；"第一遍漏了 r141"与自己守卫的误报都写在账上。 |
| 可复核性 | 14/15 | 分类用 `ast` 抽常量、守卫可单跑；复核命令就是 `unittest scripts.tests.test_mutation_summary_regex`。 |

均分 ≈ 12.3/15（86/105）。
"""

BL = u"""
422 结案追记（R346）：范围数清了 —— 51 张已经认单数、**9 张只认复数**（r130/r133/r135/r141/r142/r335/r336/r338/r339），
全部改成 `tests?` / `failures?`。并且不再靠"下次撞到再说"：新增 `scripts/tests/test_mutation_summary_regex.py`，
对每一张表把汇总正则编译出来喂**单数 + 复数**两条真实形状，两条都必须匹配；名单地板 40 张、扫到常量必须 > 0。
守卫自己的第一版把 `mutate_r262.py` 刀针里嵌的源码行当成了正则（那是被变异进产品的一行），
改成"只认以 `Executed (` 开头的常量"之后通过。**退场条件**：这张名单不再需要的那天，是因为
`mutate_*.py` 都不再各自维护汇总正则（改为共用一支 helper）——那是一件该做的合并，记在这里。

**423. `mutate_r192.py` 的 needle 在盘上命中 2 次：批量脚本按"整段常量"替换时撞到的，不是产品问题**（R346 现读）
    R346 的第二遍批量替换在 r192 上抛 `AssertionError`（`new.count(s)==1` 不成立）——那一段常量在文件里出现两次
    （一次是 needle，一次是期望串里复述的同一句）。脚本在写盘前抛错，所以**没有半批已写**；
    但它说明"按整段源码行做批量替换"在这个目录里不安全：针与期望串会互相包含。
    下一轮若还要批量改表，先做"每个 needle 在盘上恰好命中一次"的预检（`mutate_needle_precheck.py` 已有现成的判法），
    再动写盘。
"""

DEC = u"""
### D-343（346）修一个工具口径，必须同时留下一条**对全体名册**运行的守卫，否则修完就散

R346 现读：9 张变异表的汇总正则只认复数，单格只跑一个用例时会把"没解析到"判成红（假红），
而这类假红只有在**那一格恰好只跑一个用例**时才现身 —— 靠"下次撞到"永远修不完。
做法：先数清名册（55 张里 51 张已认单数、9 张不认），逐张修，再写一条**对每一张表**都运行的守卫
（把表里的正则编译出来，喂单数 + 复数两条真实形状），并给名单加地板（40 张）与"扫到 > 0"。
**How to apply**：任何"按名单逐项"的修法，收尾的判据必须是**遍历名册**的（不是抽查），
且名册本身要有地板与空对账保护；守卫第一版读错对象时，改的是**取对象的方式**（只认以 `Executed (` 开头的常量），
不是放宽判据。
"""

CH = u"""### 九张变异表认不出单数汇总行：逐张改成 `tests?`，并加一条对全体名册运行的守卫（R346 / U-1200…U-1204 · 产品 0 文件，判据账）
"""

STATE = u"""## R346 状态（2026-10-25 · 本地 · 第 345 轮 / Round 343）：九张变异表认不出单数汇总行 —— 修完配一条会红的名单守卫（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R346 / 第 345 轮 / Round 343）：55 张表里 9 张只认复数 `Executed N tests`，
单格只跑一个用例时会被判成"没解析到 ⇒ 红"；九张全改 + 新增对每一张表运行的守卫（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3` 首读 in_progress（只登记不轮询，R140）。
② 用 `ast` 数清名册：51 张认单数、9 张不认（r130/r133/r135/r141/r142/r335/r336/r338/r339）。
③ 九张改成 `tests?` / `failures?`；r141 是 `tests`（无逗号），第一遍按 `tests,` 找锚点漏了它，第二遍补上。
④ 新增 `scripts/tests/test_mutation_summary_regex.py`：对每张表把正则编译出来喂单数/复数两条真实形状。
⑤ 守卫第一版把 `mutate_r262.py` 刀针里嵌的源码行当成正则 ⇒ 收窄成"只认以 `Executed (` 开头的常量"。
⑥ `report_sources_cell.py --write` 把「最后一次动到 Sources」从 R339/fb2cea0 推到 R345/8d375b3（派生格）。

验证读数（现读）：分类 `tolerant=51 / plural-only=9`；改后 `blind=[]`；脚本电池 `Ran 646（skipped=4）OK`；
`SOURCES_CELL 账上=R339/`fb2cea0` git=R345/`8d375b3`` ⇒ 写后复核一致；帧 182（无产品改动，未重捕）；
产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 345` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 没有像素/帧判据（产品 0 文件）；② 本轮无变异刀（没有产品改动可打）；
③ 9 张表只做了**静态**验证（正则对两种形状），没有逐张真跑一格 —— 真跑要每张都有一段旧代码在盘上，
那已不在（表保留的是当时那一刀），静态 + 一条实跑（`mutate_r345` 上一轮 `CAUGHT=2/2`）是这一轮能给的最强证据。

下一轮（R347）的靶：⓪ 读两跑 CI 配对 → ① 399 的亮档悬停半边（亮度通道腾出来了：先量"提亮后 hover 与 selected 落在哪两档"）
→ ② 423（批量改表前先做 needle 命中预检）→ ③ 413 → ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 344 轮（R345 · 2026-10-25 · U-1194…U-1199）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R345 状态（2026-10-25 · 本地 · 第 344 轮 / Round 342）"
    assert s.count(h) == 1; wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1199（R345 现读抬到最新一节）", u"U-31 … U-1204（R346 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-342**", u"| 决定台账 | D-069 … **D-343**")
    r = once(r, u"U 定义行最大 **U-1199**、决定最大 **D-342**、BACKLOG 最大 **422**",
             u"U 定义行最大 **U-1204**、决定最大 **D-343**、BACKLOG 最大 **423**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R345 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R346 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **6**（现读", u"产品面连续零改动轮数 = **1**（现读")
    r = r.rstrip(u"\n") + u"""
- **R346 续（判据账）**：55 张变异表里 9 张只认复数汇总行（单格一个用例 ⇒ 假红），九张全改 `tests?`；
  新增对**每一张表**运行的守卫（单数 + 复数两条真实形状），`Ran 646`。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R346_LEDGERS_OK")

if __name__ == u"__main__":
    main()
