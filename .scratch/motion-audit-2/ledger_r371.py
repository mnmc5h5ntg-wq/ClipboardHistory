#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R371 的七本台账（第 370 轮 / Round 368）：367 第一批 —— M260 重钉、rot 33→32。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r371_py.log"


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
    head = (u"## 第 369 轮（R370 · 2026-10-25 · U-1291…U-1293）：432 第一刀 —— 空刀探测落进两张 hidden_arms 表，"
            u"正对照 M906 当场读出 EMPTY_KNIFE（U-1291…U-1293 · 产品 0 文件，判据账）")
    section = (
        u"## 第 370 轮（R371 · 2026-10-25 · U-1294…U-1296）：367 第一根 —— M260 重钉到 emit，rot 33→32，"
        u"上界同笔降（U-1294…U-1296 · 产品 0 文件，判据账）\n\n"
        u"- **U-1294：M260 重钉。** `mutate_r53_print_order.py` 的针还停在 `print(\"MOTION_NATIVE_MOVE 判定=` 上，"
        u"而 R355 把结论行换成了 `emit(` ⇒ 针腐烂。重钉后四臂重跑 `M260…M263 CAUGHT 4/4`、`还原不干净=0`、"
        u"还原后复跑 `ESCAPED`（基线仍绿）。\n"
        u"- **U-1295：一次归因自伤（照实记账）。** 第一版把 `FILTER` 改到探针 `testNativeRowMoveIsVisibleToTheRuler` 上，"
        u"那一遍 4 臂全 `ESCAPED` —— 探针在无 UI 环境会 skip，**0 格被读成「没红」**；守卫的真名是 "
        u"`testNativeMoveVerdictPrintsBeforeTheSkipGuards`（原过滤串 `testNativeMove` 本来就匹配它）。改回后 4/4。\n"
        u"- **U-1296：rot 33→32，上界同笔降。** `scripts/hidden_arms.py` 的 `ROT_CEILING` 从 33 降到 32；"
        u"`HIDDEN_ARMS 表=222 可判=804 rot=32 抽不出=6 已声明表=6 已声明死针=0 上界 rot=32 … 处置=ok`；"
        u"`test_hidden_arms` **8/8 OK**（双向棘轮两格都在）。声明面 6 张没动 —— 这一根是「重新钉活」，不是新声明。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | BLIND 与 EMPTY 分开写；M906 的加回与撤销都记账。 |\n"
            u"| 可复核性 | 15/15 | 一条命令复跑两张表；6 格测试可单独跑。 |\n\n"
            u"均分 = 90/105 ≈ 12.9/15（86）。")
    r368 = (
        u"\n\n## Round 368 · R371（第 370 轮 · 2026-10-25）：367 第一根 —— M260 重钉、rot 33→32（产品 0 文件）\n\n"
        u"`mutate_r53_print_order.py` 的 M260 针从 `print(` 重钉到 `emit(`（R355 换的行），四臂重跑 4/4 CAUGHT。"
        u"`ROT_CEILING` 同笔 33→32，`test_hidden_arms` 8/8；一次归因自伤（把过滤串改到会 skip 的探针上，"
        u"0 格被读成没红）照实写进 U-1295。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 四臂 4/4 CAUGHT；`rot` 与上界同笔降，两格棘轮都在。 |\n"
        u"| 假绿防御 | 15/15 | 0 格被读成没红那一遍照实记账；上界没有留在 33。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在烂针面（33→32）。 |\n"
        u"| 台账一致性 | 13/15 | U-1294…U-1296、367 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 归因错的那一版不删，写成自伤并给出正确靶。 |\n"
        u"| 可复核性 | 15/15 | 一条命令复跑四臂；`hidden_arms.py` 一行看 rot 与上界。 |\n\n"
        u"均分 = 90/105 ≈ 12.9/15（86）。"
    )
    it = once(it, tail, tail + r368)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    BLIND 的现读两把是 M903 / M913 —— 它们红在判定式上，`HIDDEN_ARMS` 那行不动；只印不判死。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R371 · 第一根）：`mutate_r53_print_order.py` 的 M260 重钉 —— 针从 `print(` 搬到 `emit(`"
              u"（R355 换的行），四臂 `4/4 CAUGHT`、`还原不干净=0`。\n"
              u"    `ROT_CEILING` 同笔 **33→32**：现读 `HIDDEN_ARMS 表=222 可判=804 rot=32 抽不出=6 已声明表=6 "
              u"已声明死针=0 上界 rot=32 … 处置=ok`，`test_hidden_arms` 8/8。\n"
              u"    归因更正：过滤串**本来没坏**（`testNativeMove` 匹配守卫 `testNativeMoveVerdictPrints…`）；"
              u"我先改到探针上跑出 4 臂全 ESCAPED，那是 0 格被读成「没红」。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 367 第一根：M260 重钉到 emit、rot 33→32 且上界同笔降（含一次归因自伤的自曝）"
                u"（R371 / U-1294…U-1296 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R367，368 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R368，369 节自评）")
    rp = once(rp, u"U-31 … U-1293（R370 现读抬到最新一节）", u"U-31 … U-1296（R371 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **15**", u"产品面连续零改动轮数 = **16**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R370 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R371 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R370 这一段（R337 补写；R341 续到 341、R370 续到 370 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R371 这一段（R337 补写；R341 续到 341、R371 续到 371 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R370 续（判据账）**：432 第一刀 —— `readout_probe.py` 四态（新增 `EMPTY_KNIFE` / `READOUT_BLIND`）+ 6 格测试；"
                u"r310/r313 接线，\n"
                u"  `CAUGHT=4 BLIND=1` / `CAUGHT=2 BLIND=1`、`EMPTY=0`；正对照把 M906 临时加回，读出 `EMPTY_KNIFE` 后撤销。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R371 续（判据账）**：367 第一根 —— M260 从 `print(` 重钉到 `emit(`，四臂 `4/4 CAUGHT`；"
              u"`ROT_CEILING` 同笔 33→32，`hidden_arms` 8/8；\n"
              u"  一次归因自伤（把过滤串改到会 skip 的探针上，4 臂全 ESCAPED）照实记账。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r370_head = (u"## R370 状态（2026-10-25 · 本地 · 第 369 轮 / Round 367）：432 第一刀 —— 空刀探测进两张 hidden_arms 表，"
                 u"正对照 M906 读出 EMPTY_KNIFE（产品 0 文件，判据账）")
    state = (
        u"## R371 状态（2026-10-25 · 本地 · 第 370 轮 / Round 368）：367 第一根 —— M260 重钉到 emit，"
        u"rot 33→32 且上界同笔降（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R371 / 第 370 轮 / Round 368）：r53 四臂 `4/4 CAUGHT`、`还原不干净=0`；"
        u"`ROT_CEILING` 33→32，`test_hidden_arms` **8/8 OK**；电池 Ran @RAN@（skipped=@SK@）OK；"
        u"全量卷沿用 R366（Swift 未动）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`"
        u"（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：五跑（`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c`）仍在队里；只登记不轮询。\n"
        u"② 367 第一根：M260 的针从 `print(` 重钉到 `emit(`（R355 换的行）。\n"
        u"③ 四臂重跑：M260…M263 全 CAUGHT，还原干净，复跑基线绿。\n"
        u"④ rot 33→32、`ROT_CEILING` 同笔降；`HIDDEN_ARMS` 现读 `处置=ok`。\n\n"
        u"验证读数（现读）：`HIDDEN_ARMS 表=222 可判=804 rot=32 抽不出=6 已声明表=6 已声明死针=0 上界 rot=32 … 处置=ok`；"
        u"`test_hidden_arms` 8/8；全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **16** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 370` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（本轮没动 Swift）；② 其余 32 根烂针未重钉；③ 真机腿没跑。\n\n"
        u"下一轮（R372）的靶：⓪ 读队列五跑；① 367 第二根（`mutate_r54_adjacent_levels.py` 的 M264，候选 4 个）；"
        u"② 或给 r312 家族声明 READOUT（它的读数是「少了一根轴」）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r370_head, state + r370_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R371_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
