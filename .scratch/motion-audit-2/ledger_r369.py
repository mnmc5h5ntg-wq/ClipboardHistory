#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R369 的七本台账（第 368 轮 / Round 366）：426 第七批 + 空刀探测开单（432）。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r369_py.log"


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
    head = (u"## 第 367 轮（R368 · 2026-10-25 · U-1285…U-1287）：426 第六批 —— r307/r309/r310 迁到 diff 回读；"
            u"r310 的一把空刀退役（U-1285…U-1287 · 产品 0 文件，判据账）")
    section = (
        u"## 第 368 轮（R369 · 2026-10-25 · U-1288…U-1290）：426 第七批 —— r308 迁到 diff 回读，六臂全 CAUGHT；"
        u"空刀探测开单 432（U-1288…U-1290 · 产品 0 文件，判据账）\n\n"
        u"- **U-1288：r308（六把热图悬停刀，Swift 侧）迁到 `single_substitution_lands`。** 只换落刀后的回读那一行；"
        u"重跑 `R308_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`，"
        u"红线落在 `testHoverLeavesTheDataPixelsUntouched` / `testHoverChangesOnlyTheRingBand` / "
        u"`testHoverIsNotLouderThanOneDataStep` / `testRingBandSelectorIsATruthTable` / "
        u"`testGridCellsRouteThroughTheProductCellView` 这几个期望格子上（跑=13）。\n"
        u"- **U-1289：迁移面现读 15 张。**（r308/r312/r313/r337/r338/r339/r345/r348/r355/r356/r358/r360/r307/r309/r310）；"
        u"其中 Swift 侧从三张扩到四张 —— diff 判法在两门语言上都兑现。\n"
        u"- **U-1290：空刀探测今天造不出来，开 432。** 通用探测需要每张表声明一个读数口径"
        u"（落刀前后各跑一次、数不变即点名）；现读声明数 **0/134** ⇒ 不是「不愿造」，是没有对象先声明，"
        u"硬造只会得到一把恒绿的尺。M906 的现场（R368）是它第一个证人，设计写进 BACKLOG 432。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 刀号总数下降照实写；全量卷写明沿用。 |\n"
            u"| 可复核性 | 15/15 | 三条命令各复跑一张表；退役可由 `HIDDEN_ARMS` 一行复现。 |\n\n"
            u"均分 = 89/105 ≈ 12.7/15（85）。")
    r366 = (
        u"\n\n## Round 366 · R369（第 368 轮 · 2026-10-25）：426 第七批 —— r308 迁到 diff 回读；空刀探测开单 432（产品 0 文件）\n\n"
        u"r308 只换落刀后的回读那一行：`刀=6 CAUGHT=6`、`RESTORE_CLEAN=yes`，红线在五个热图悬停用例上。"
        u"空刀探测不硬造：它需要 134 张表先各自声明一个读数口径，现读 0 张；本轮的判断与设计写进 BACKLOG 432。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 六臂全 CAUGHT（跑=13），红线逐个落在期望用例上。 |\n"
        u"| 假绿防御 | 14/15 | 空刀探测造不出来就写明缺席计数（0/134），不用一把恒绿的尺充数。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在 426 迁移面（14→15 张）。 |\n"
        u"| 台账一致性 | 13/15 | U-1288…U-1290、432 开单；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 「不造工具」写成判断与缺席计数，不写成遗漏。 |\n"
        u"| 可复核性 | 15/15 | 一条命令复跑 r308；432 的设计可逐条对照。 |\n\n"
        u"均分 = 89/105 ≈ 12.7/15（85）。"
    )
    it = once(it, tail, tail + r366)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    退役写进表头与这一格，不改期望；r310 重跑 `5/5`、`RESTORE_CLEAN=yes`。"
               u"已有 **14 张**表在新判法上；刀号总数 377→376、全仓 865→864。")
    bl_add = (bl_tail + u"\n\n"
              u"426 追记（R369）：第七批 —— r308（六把热图悬停刀，Swift 侧）只换回读那一行；"
              u"`刀=6 CAUGHT=6 RESTORE_CLEAN=yes`。已有 **15 张**表在新判法上。\n\n"
              u"**432. 空刀探测：需要每张表先声明一个「读数口径」，今天 0/134**（R369 开）\n"
              u"    现场：R368 的 M906 落刀后 `HIDDEN_ARMS rot=33 抽不出=6 已声明=6` 一个数都没动 —— 刀没牙，"
              u"而旧判法只看「测试红没红」。\n"
              u"    形状（下一批做）：表里加 `READOUT = (命令, 正则)`；回放时落刀前后各跑一次，"
              u"**两次数完全相等**即判 `EMPTY_KNIFE`（与 CAUGHT/PASSED 并列的第四态），并把两行读数一起打出来。\n"
              u"    缺席计数：现读声明 `READOUT` 的表 **0 / 134** ⇒ 通用探测器今天没有对象；"
              u"先给 M906 所属的 hidden_arms 家族三张表声明，再谈全仓。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 426 第七批：r308 迁到 diff 回读，六臂全 CAUGHT；空刀探测开单 432（读数口径 0/134，暂不硬造）"
                u"（R369 / U-1288…U-1290 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R365，366 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R366，367 节自评）")
    rp = once(rp, u"U-31 … U-1287（R368 现读抬到最新一节）", u"U-31 … U-1290（R369 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **13**", u"产品面连续零改动轮数 = **14**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R368 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R369 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R368 这一段（R337 补写；R341 续到 341、R368 续到 368 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R369 这一段（R337 补写；R341 续到 341、R369 续到 369 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R368 续（判据账）**：426 第六批 —— r307/r309 迁到 diff 回读（`4/4`、`6/6`）；"
                u"r310 迁完先跑出 `5/6`，\n"
                u"  M906 的落刀让 `HIDDEN_ARMS` 三组数一个没动 ⇒ **空刀退役**（不改期望），重跑 `5/5`；刀号 377→376、全仓 865→864。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R369 续（判据账）**：426 第七批 —— r308 迁到 diff 回读（六臂 `6/6`，红线在五个热图悬停用例上）；"
              u"迁移面 15 张；\n"
              u"  空刀探测 **开单 432**：需先有 134 张表的读数口径声明，现读 0/134，本轮不硬造。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r368_head = (u"## R368 状态（2026-10-25 · 本地 · 第 367 轮 / Round 365）：426 第六批 —— r307/r309 迁到 diff 回读；"
                 u"r310 一把空刀退役（产品 0 文件，判据账）")
    state = (
        u"## R369 状态（2026-10-25 · 本地 · 第 368 轮 / Round 366）：426 第七批 —— r308 迁到 diff 回读；"
        u"空刀探测开单 432（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R369 / 第 368 轮 / Round 366）：r308 只换落刀后的回读那一行；"
        u"`刀=6 CAUGHT=6 NOT_RUN=0 RESTORE_CLEAN=yes`；电池 Ran @RAN@（skipped=@SK@）OK；"
        u"全量卷沿用 R366（Swift 未动）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"迁移面 15 张（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`452f5a3`、`cc9eb1e` 两跑 success；`7ad22cf`、`19f91e2`、`f9df01e`、`3c84fc8` 仍在队里（只登记不轮询）。\n"
        u"② 426 第七批：r308（六把热图悬停刀，Swift 侧）迁 `single_substitution_lands`。\n"
        u"③ 六臂全 CAUGHT，红线在五个热图悬停用例上（跑=13）。\n"
        u"④ 空刀探测：不硬造 —— 需要 134 张表各有 `READOUT` 声明，现读 0 张；判断与形状写进 BACKLOG 432。\n\n"
        u"验证读数（现读）：`R308_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **14** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 368` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 一张表）；② 432 的探测器未实现（0/134 无对象）；③ 真机腿没跑。\n\n"
        u"下一轮（R370）的靶：⓪ 读队列四跑；① 给 hidden_arms 家族三张表声明 `READOUT` 并实现 432 的第四态"
        u"（先只对这三张生效）；② 426 第八批（r306 这类 mixed 表）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r368_head, state + r368_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R369_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
