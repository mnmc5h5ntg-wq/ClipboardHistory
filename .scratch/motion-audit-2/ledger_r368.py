#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R368 的七本台账（第 367 轮 / Round 365）：426 第六批 + M906 退役。

Swift 未动：全量卷沿用 R366 的读数（同一份 Sources/Tests）。
"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r368_py.log"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), u"w", encoding=u"utf-8").write(text)


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, u"锚点命中 %d 次：%s" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, replacement)


def full_counts():
    t = io.open(FULL, encoding=u"utf-8", errors=u"replace").read()
    assert u"Test Suite 'ClipboardHistoryPackageTests.xctest' passed" in t, u"全量卷没有收尾行"
    m = re.findall(r"Executed (\d+) tests?, with (\d+) tests? skipped and (\d+) failures?", t)
    assert m, u"全量卷的汇总行没解析到"
    return tuple(int(x) for x in m[-1])


def battery_counts():
    t = io.open(PY, encoding=u"utf-8", errors=u"replace").read()
    m = re.findall(r"^Ran (\d+) tests? in", t, re.M)
    assert m, u"电池的 Ran 行没解析到"
    assert re.search(r"^OK( \(skipped=\d+\))?$", t, re.M), u"电池没有 OK 行"
    sk = re.findall(r"OK \(skipped=(\d+)\)", t)
    return int(m[-1]), int(sk[-1]) if sk else 0


def main():
    n, skipped, failures = full_counts()
    ran, py_skipped = battery_counts()
    assert failures == 0, u"全量卷有 %d 个失败 ⇒ 不许写台账" % failures
    print(u"PARSED full=%d skipped=%d failures=%d battery=%d(%d skipped)"
          % (n, skipped, failures, ran, py_skipped))

    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 366 轮（R367 · 2026-10-25 · U-1282…U-1284）：426 第五批 —— r313/r337 迁到 diff 回读，七臂全 CAUGHT"
            u"（U-1282…U-1284 · 产品 0 文件，判据账）")
    section = (
        u"## 第 367 轮（R368 · 2026-10-25 · U-1285…U-1287）：426 第六批 —— r307/r309/r310 迁到 diff 回读；"
        u"r310 的一把空刀退役（U-1285…U-1287 · 产品 0 文件，判据账）\n\n"
        u"- **U-1285：r307（四把门刀）与 r309（六把读数刀）迁到 `single_substitution_lands`。** 只换落刀后的回读那一行；"
        u"重跑 `R307_MUTATE 刀=4 CAUGHT=4`、`R309_MUTATE 刀=6 CAUGHT=6`，两表 `RESTORE_CLEAN=yes`。\n"
        u"- **U-1286：r310 迁完先跑出 5/6 —— M906 ESCAPED。** 落刀后 `HIDDEN_ARMS` 的三组数"
        u"（rot=33 / 抽不出=6 / 已声明=6）**一个都没动**：把语料排除项 `fixtures` 改成 `fixtures_x` 对今天的扫描没有作用，"
        u"这条针已经没有对象。\n"
        u"- **U-1287：M906 退役，不改期望。** 退役登记写进表头与 BACKLOG 426 的追记（理由 + 读数）；"
        u"r310 重跑 `刀=5 CAUGHT=5 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`。"
        u"刀号总数 377→376（预检 `arms=376`）、全仓 865→864 —— 退役让计数变少，这是诚实的减少，不是把红洗成绿。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 全量卷写明沿用（Swift 未动）；未声称迁完。 |\n"
            u"| 可复核性 | 15/15 | 两条命令各复跑一张表。 |\n\n"
            u"均分 = 88/105 ≈ 12.6/15（84）。")
    r365 = (
        u"\n\n## Round 365 · R368（第 367 轮 · 2026-10-25）：426 第六批 —— r307/r309 迁到 diff 回读；r310 一把空刀退役（产品 0 文件）\n\n"
        u"r307 `4/4`、r309 `6/6` 全 CAUGHT；r310 迁完先跑出 `5/6`，M906 的落刀对 `HIDDEN_ARMS` 三组数一个都没动 ⇒ 刀已无牙，"
        u"按退役处理（写清理由与读数，不改期望），重跑 `5/5`。刀号 377→376、全仓 865→864。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 14/15 | 十五臂重跑 4/4、6/6、5/5；三表 RESTORE_CLEAN。 |\n"
        u"| 假绿防御 | 15/15 | 空刀先被跑成 ESCAPED，再核出「三组数一个没动」才退役 —— 没有改期望换绿。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在 426 迁移面（11→14 张）与刀面清理。 |\n"
        u"| 台账一致性 | 13/15 | U-1285…U-1287、426 追记、退役登记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 刀号总数下降照实写；全量卷写明沿用。 |\n"
        u"| 可复核性 | 15/15 | 三条命令各复跑一张表；退役可由 `HIDDEN_ARMS` 一行复现。 |\n\n"
        u"均分 = 89/105 ≈ 12.7/15（85）。"
    )
    it = once(it, tail, tail + r365)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    两张表都是 Python 侧的刀（守卫 / 台账引用）—— diff 判法不依赖语言。"
               u"已有 **11 张**表在新判法上；多针表与其余历史表未动。")
    bl_add = (bl_tail + u"\n\n"
              u"426 追记（R368）：第六批 —— r307 / r309 只换回读那一行（`4/4`、`6/6`）；"
              u"r310 迁完先跑出 `5/6`：\n"
              u"    **M906 退役** —— 落刀（`fixtures` → `fixtures_x`）后 `HIDDEN_ARMS rot=33 抽不出=6 已声明=6`"
              u" 一个都没动 ⇒ 这条排除对今天的语料没有作用。\n"
              u"    退役写进表头与这一格，不改期望；r310 重跑 `5/5`、`RESTORE_CLEAN=yes`。"
              u"已有 **14 张**表在新判法上；刀号总数 377→376、全仓 865→864。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 426 第六批：r307/r309 迁到 diff 回读；r310 的 M906 落刀后三组数一个没动 ⇒ 空刀退役"
                u"（R368 / U-1285…U-1287 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R364，365 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R365，366 节自评）")
    rp = once(rp, u"U-31 … U-1284（R367 现读抬到最新一节）", u"U-31 … U-1287（R368 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **12**", u"产品面连续零改动轮数 = **13**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R367 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R368 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R367 这一段（R337 补写；R341 续到 341、R367 续到 367 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R368 这一段（R337 补写；R341 续到 341、R368 续到 368 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R367 续（判据账）**：426 第五批 —— r313/r337 迁到 `single_substitution_lands`（只换回读那一行），"
                u"七臂重跑 `3/3`、`4/4` 全 CAUGHT；\n"
                u"  两张都是 Python 侧的刀（守卫 / 台账引用），diff 判法不依赖语言。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R368 续（判据账）**：426 第六批 —— r307/r309 迁到 diff 回读（`4/4`、`6/6`）；"
              u"r310 迁完先跑出 `5/6`，\n"
              u"  M906 的落刀让 `HIDDEN_ARMS` 三组数一个没动 ⇒ **空刀退役**（不改期望），重跑 `5/5`；刀号 377→376、全仓 865→864。")
    rp = once(rp,
              u"（R365 现读：注册表 **134** 张 / 刀号最大 **M1009** / 预检 covered=117 arms=377 bad=0；全仓 227 文件 / 865 把）",
              u"（R368 现读：注册表 **134** 张 / 刀号最大 **M1009** / 预检 covered=117 arms=376 bad=0；"
              u"全仓 228 文件 / 864 把；M906 空刀退役）")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r367_head = (u"## R367 状态（2026-10-25 · 本地 · 第 366 轮 / Round 364）：426 第五批 —— r313/r337 迁到 diff 回读"
                 u"（产品 0 文件，判据账）")
    state = (
        u"## R368 状态（2026-10-25 · 本地 · 第 367 轮 / Round 365）：426 第六批 —— r307/r309 迁到 diff 回读；"
        u"r310 一把空刀退役（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R368 / 第 367 轮 / Round 365）：r307 `4/4`、r309 `6/6`；"
        u"r310 先跑出 `5/6`（M906 落刀后 `HIDDEN_ARMS` 三组数一个没动）⇒ 退役后重跑 `5/5`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK；全量卷沿用 R366（Swift 未动）："
        u"`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`452f5a3`（R365 追记）、`cc9eb1e`（R366）、`7ad22cf`（R366 追记）、`19f91e2`（R367）都还在队里；只登记不轮询。\n"
        u"② 426 第六批：r307 / r309 迁 `single_substitution_lands`；r310 同批迁移。\n"
        u"③ 发现空刀：M906（`fixtures` 排除项）落刀后 `rot=33 抽不出=6 已声明=6` 全不动 ⇒ 退役、不改期望，重跑 5/5。\n"
        u"④ 计数：预检 `arms=376`（377→376）、全仓 864 把（865→864）、注册表 134 张、最大刀号 M1009。\n\n"
        u"验证读数（现读）：`R307_MUTATE 刀=4 CAUGHT=4`、`R309_MUTATE 刀=6 CAUGHT=6`、"
        u"`R310_MUTATE 刀=5 CAUGHT=5`，三表 `RESTORE_CLEAN=yes`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **13** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 367` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 三张表）；② 多针表与其余历史表的迁移；③ 真机腿没跑。\n\n"
        u"下一轮（R369）的靶：⓪ 读队列里积压的四跑（`452f5a3` / `cc9eb1e` / `7ad22cf` / `19f91e2`）；"
        u"① 426 第七批（r308 这类 Swift 侧的表，跑起来慢，单独一轮），或先把「空刀探测」写成工具（落刀后数不变即点名）；"
        u"② 367 的下一批要先重钉死针再声明。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r367_head, state + r367_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R368_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
