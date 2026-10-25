#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R370 的七本台账（第 369 轮 / Round 367）：432 第一刀 —— 空刀探测（两张 hidden_arms 表）。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r370_py.log"


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
    head = (u"## 第 368 轮（R369 · 2026-10-25 · U-1288…U-1290）：426 第七批 —— r308 迁到 diff 回读，六臂全 CAUGHT；"
            u"空刀探测开单 432（U-1288…U-1290 · 产品 0 文件，判据账）")
    section = (
        u"## 第 369 轮（R370 · 2026-10-25 · U-1291…U-1293）：432 第一刀 —— 空刀探测落进两张 hidden_arms 表，"
        u"正对照 M906 当场读出 EMPTY_KNIFE（U-1291…U-1293 · 产品 0 文件，判据账）\n\n"
        u"- **U-1291：`readout_probe.py` 的四态。** `capture` 取一条读数、`four_state` 把它折成"
        u"`EMPTY_KNIFE`（没红且读数全等）/ `READOUT_BLIND`（红了但读数全等，只印不判死）；读数拿不到时原样退回旧判词。"
        u"`scripts/tests/test_mutation_readout.py` **6 格**（含「拿不到读数不许冒充没变化」）。\n"
        u"- **U-1292：r310 / r313 接线后的现读。** `R310_MUTATE 刀=5 CAUGHT=4 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes`、"
        u"`R313_MUTATE 刀=3 CAUGHT=2 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes` —— 两张表各有一把「红了但读数全等」的刀："
        u"M903（双向棘轮改成只判上界）与 M913（已声明死针只判一个方向），它们红在判定式而不是 `HIDDEN_ARMS` 那行上。"
        u"BLIND **仍算过关**（刀咬住了别的判据），只是不再沉默。\n"
        u"- **U-1293：正对照 —— 把 M906 临时加回 r310，只跑它。** 输出 "
        u"`M906 EMPTY_KNIFE …` 并把前后两行 `HIDDEN_ARMS 表=222 可判=805 rot=33 抽不出=6 已声明表=6 已声明死针=0 …` "
        u"原样打出来（一字不差）；跑完立刻撤掉，r310 回到 5 臂、`EMPTY=0`。这把尺第一次对**已知空刀**兑现。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 「不造工具」写成判断与缺席计数，不写成遗漏。 |\n"
            u"| 可复核性 | 15/15 | 一条命令复跑 r308；432 的设计可逐条对照。 |\n\n"
            u"均分 = 89/105 ≈ 12.7/15（85）。")
    r367 = (
        u"\n\n## Round 367 · R370（第 369 轮 · 2026-10-25）：432 第一刀 —— 空刀探测进两张 hidden_arms 表（产品 0 文件）\n\n"
        u"四态落地（EMPTY_KNIFE / READOUT_BLIND 两个新名字）+ 6 格纯函数测试；r310 / r313 接线后各跑出"
        u"`CAUGHT=4 BLIND=1` 与 `CAUGHT=2 BLIND=1`、`EMPTY=0`、`RESTORE_CLEAN=yes`。"
        u"正对照把已知空刀 M906 临时加回，当场读出 EMPTY_KNIFE 并打出前后两行全等的 `HIDDEN_ARMS`；随即撤销。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 正对照 M906 读出 EMPTY_KNIFE；两张表 EMPTY=0、RESTORE_CLEAN=yes。 |\n"
        u"| 假绿防御 | 15/15 | 「拿不到读数」原样退回旧判词；BLIND 只印不判死、不冒充 CAUGHT。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在刀面的第四态（2/134 张表已声明读数口径）。 |\n"
        u"| 台账一致性 | 13/15 | U-1291…U-1293、432 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | BLIND 与 EMPTY 分开写；M906 的加回与撤销都记账。 |\n"
        u"| 可复核性 | 15/15 | 一条命令复跑两张表；6 格测试可单独跑。 |\n\n"
        u"均分 = 90/105 ≈ 12.9/15（86）。"
    )
    it = once(it, tail, tail + r367)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    缺席计数：现读声明 `READOUT` 的表 **0 / 134** ⇒ 通用探测器今天没有对象；"
               u"先给 M906 所属的 hidden_arms 家族三张表声明，再谈全仓。")
    bl_add = (bl_tail + u"\n\n"
              u"432 追记（R370 · 第一刀）：`readout_probe.py` 落地（`capture` / `four_state` / `summarize`），"
              u"四态里多出 `EMPTY_KNIFE` 与 `READOUT_BLIND`；\n"
              u"    r310 / r313 已声明 `READOUT`（`python3 scripts/hidden_arms.py` 的 `HIDDEN_ARMS` 行）⇒ 声明面 **2 / 134**。\n"
              u"    现读：r310 `CAUGHT=4 BLIND=1 EMPTY=0`、r313 `CAUGHT=2 BLIND=1 EMPTY=0`、两表 `RESTORE_CLEAN=yes`；\n"
              u"    正对照把 M906 临时加回：`M906 EMPTY_KNIFE`，前后两行 `HIDDEN_ARMS` 一字不差；撤销后 r310 回到 5 臂。\n"
              u"    BLIND 的现读两把是 M903 / M913 —— 它们红在判定式上，`HIDDEN_ARMS` 那行不动；只印不判死。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 432 第一刀：空刀探测落进两张 hidden_arms 表（四态 + 正对照 M906 读出 EMPTY_KNIFE）"
                u"（R370 / U-1291…U-1293 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R366，367 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R367，368 节自评）")
    rp = once(rp, u"U-31 … U-1290（R369 现读抬到最新一节）", u"U-31 … U-1293（R370 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **14**", u"产品面连续零改动轮数 = **15**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R369 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R370 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R369 这一段（R337 补写；R341 续到 341、R369 续到 369 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R370 这一段（R337 补写；R341 续到 341、R370 续到 370 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R369 续（判据账）**：426 第七批 —— r308 迁到 diff 回读（六臂 `6/6`，红线在五个热图悬停用例上）；"
                u"迁移面 15 张；\n"
                u"  空刀探测 **开单 432**：需先有 134 张表的读数口径声明，现读 0/134，本轮不硬造。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R370 续（判据账）**：432 第一刀 —— `readout_probe.py` 四态（新增 `EMPTY_KNIFE` / `READOUT_BLIND`）+ 6 格测试；"
              u"r310/r313 接线，\n"
              u"  `CAUGHT=4 BLIND=1` / `CAUGHT=2 BLIND=1`、`EMPTY=0`；正对照把 M906 临时加回，读出 `EMPTY_KNIFE` 后撤销。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r369_head = (u"## R369 状态（2026-10-25 · 本地 · 第 368 轮 / Round 366）：426 第七批 —— r308 迁到 diff 回读；"
                 u"空刀探测开单 432（产品 0 文件，判据账）")
    state = (
        u"## R370 状态（2026-10-25 · 本地 · 第 369 轮 / Round 367）：432 第一刀 —— 空刀探测进两张 hidden_arms 表，"
        u"正对照 M906 读出 EMPTY_KNIFE（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R370 / 第 369 轮 / Round 367）：`readout_probe.py` 四态 + 6 格测试；"
        u"r310 `CAUGHT=4 BLIND=1 EMPTY=0`、r313 `CAUGHT=2 BLIND=1 EMPTY=0`，两表 `RESTORE_CLEAN=yes`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK；全量卷沿用 R366（Swift 未动）："
        u"`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`7ad22cf`、`19f91e2`、`f9df01e`、`3c84fc8`、`d44797c` 仍在队里（只登记不轮询）。\n"
        u"② 432 第一刀：`capture` / `four_state` / `summarize` + `test_mutation_readout.py` 6 格。\n"
        u"③ r310 / r313 声明 `READOUT`（`hidden_arms.py` 的 `HIDDEN_ARMS` 行）⇒ 声明面 2/134。\n"
        u"④ 正对照：M906 临时加回 → `EMPTY_KNIFE`（前后两行一字不差），撤销后 r310 回到 5 臂。\n\n"
        u"验证读数（现读）：`R310_MUTATE 刀=5 CAUGHT=4 ESCAPED=0 NOT_RUN=0 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes`；"
        u"`R313_MUTATE 刀=3 CAUGHT=2 ESCAPED=0 NOT_RUN=0 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **15** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 369` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 与 scripts/tests 的新测试）；"
        u"② 432 只接了两张表（2/134），其余表未声明读数口径；③ 真机腿没跑。\n\n"
        u"下一轮（R371）的靶：⓪ 读队列五跑；① 给 r312 家族（M908…M910 的读数是「读数少了一根轴」）这类表也声明 READOUT，"
        u"或把 BLIND 的两把（M903/M913）改成同时动读数的刀；② 426 第八批（r306 mixed 表）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r369_head, state + r369_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R370_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
