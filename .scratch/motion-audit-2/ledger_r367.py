#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R367 的七本台账（第 366 轮 / Round 364）：426 第五批 —— r313/r337 迁到 diff 回读。

Swift 未动：全量卷沿用 R366 的读数（同一份 Sources/Tests），台账里写明「沿用」。
"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r367_py.log"


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
    head = (u"## 第 365 轮（R366 · 2026-10-25 · U-1279…U-1281）：426 第四批 —— r312 迁到 diff 回读，三臂全 CAUGHT"
            u"（U-1279…U-1281 · 产品 0 文件，判据账）")
    section = (
        u"## 第 366 轮（R367 · 2026-10-25 · U-1282…U-1284）：426 第五批 —— r313/r337 迁到 diff 回读，七臂全 CAUGHT"
        u"（U-1282…U-1284 · 产品 0 文件，判据账）\n\n"
        u"- **U-1282：r313（三把 Python 守卫刀）迁到 `single_substitution_lands`。** 只换落刀后的回读那一行；"
        u"重跑 `R313_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`，"
        u"基线 `跑=8 失败=0`。\n"
        u"- **U-1283：r337（四把台账引用刀）也迁到同一判法。** `MUTATE_TABLE n=4 caught=4 escaped=0 not_run=0 "
        u"RESTORE_CLEAN=yes`（表自己印的旧形状汇总行与 `CAUGHT=4/4` 同时成立）；"
        u"M992 的红分两格（引用格 + ITEM 同一颗尺），与入账时一致。\n"
        u"- **U-1284：迁移面现读 11 张。** 单针与多针表里已有 11 张在 diff 判法上"
        u"（r312/r313/r337/r338/r339/r345/r348/r355/r356/r358/r360）；剩下的历史表与多针表未动。"
        u"本轮两张表都是 **Python 侧**的刀 —— 回读判法与语言无关，换的是「盘上是不是那一份」这句话。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 未声称多针表已迁；迁移只动回读那一行。 |\n"
            u"| 可复核性 | 15/15 | 一条命令复跑 r312。 |\n\n"
            u"均分 = 88/105 ≈ 12.6/15（84）。")
    r364 = (
        u"\n\n## Round 364 · R367（第 366 轮 · 2026-10-25）：426 第五批 —— r313/r337 迁到 diff 回读（产品 0 文件）\n\n"
        u"两张表只换落刀后的回读那一行：r313 `3/3`、r337 `4/4`，都 `RESTORE_CLEAN=yes`。"
        u"它们都是 Python 侧的刀（守卫与台账引用），说明 diff 判法不是 Swift 胶片专用的。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 的热图/药丸帧（上一轮已逐帧看过）。 |\n"
        u"| 判据有效性 | 14/15 | 七臂重跑 3/3、4/4 全 CAUGHT；两张表各自 RESTORE_CLEAN。 |\n"
        u"| 假绿防御 | 14/15 | 只换回读、不动 needle/repl/期望；删臂也走 diff 等式。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在 426 的迁移面（9→11 张）。 |\n"
        u"| 台账一致性 | 13/15 | U-1282…U-1284、426 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 全量卷写明沿用（Swift 未动）；未声称迁完。 |\n"
        u"| 可复核性 | 15/15 | 两条命令各复跑一张表。 |\n\n"
        u"均分 = 88/105 ≈ 12.6/15（84）。"
    )
    it = once(it, tail, tail + r364)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    ⇒ `pillBandCoverageFloor = 0.90` 在两台机器上都被签下（本机 48/48、runner 24/24，同一个比例）。"
               u"这一格从「结案时的读数」变成「两机都会红的判据」。")
    bl_add = (bl_tail + u"\n\n"
              u"426 追记（R367）：第五批 —— r313 / r337 只换落刀后的回读那一行；"
              u"`3/3`、`4/4` 全 CAUGHT、两表 `RESTORE_CLEAN=yes`。\n"
              u"    两张表都是 Python 侧的刀（守卫 / 台账引用）—— diff 判法不依赖语言。"
              u"已有 **11 张**表在新判法上；多针表与其余历史表未动。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 426 第五批：r313/r337 迁到 diff 回读（Python 侧的刀同样成立），七臂全 CAUGHT"
                u"（R367 / U-1282…U-1284 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R363，364 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R364，365 节自评）")
    rp = once(rp, u"U-31 … U-1281（R366 现读抬到最新一节）", u"U-31 … U-1284（R367 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **11**", u"产品面连续零改动轮数 = **12**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R366 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R367 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R366 这一段（R337 补写；R341 续到 341、R366 续到 366 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R367 这一段（R337 补写；R341 续到 341、R367 续到 367 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R366 追记（runner）**：`563c0ed` 绿跑现读 `纵向覆盖=24/24px=100%`、`judged=4/4`、"
                u"`ASSERTION_RED 0` ⇒ 0.90 地板两机都签下。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R367 续（判据账）**：426 第五批 —— r313/r337 迁到 `single_substitution_lands`（只换回读那一行），"
              u"七臂重跑 `3/3`、`4/4` 全 CAUGHT；\n"
              u"  两张都是 Python 侧的刀（守卫 / 台账引用），diff 判法不依赖语言。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r366_head = (u"## R366 状态（2026-10-25 · 本地 · 第 365 轮 / Round 363）：426 第四批 —— r312 迁到 diff 回读"
                 u"（产品 0 文件，判据账）")
    state = (
        u"## R367 状态（2026-10-25 · 本地 · 第 366 轮 / Round 364）：426 第五批 —— r313/r337 迁到 diff 回读"
        u"（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R367 / 第 366 轮 / Round 364）：两张表只换落刀后的回读那一行；"
        u"`3/3`、`4/4` 全 CAUGHT、`RESTORE_CLEAN=yes`；电池 Ran @RAN@（skipped=@SK@）OK；"
        u"全量卷沿用 R366（Swift 未动）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"迁移面 11 张（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`563c0ed`（R365）已 success（24/24=100%，见上轮追记）；`452f5a3`、`cc9eb1e`、`7ad22cf` 仍在队里（只登记不轮询）。\n"
        u"② 426 第五批：r313（守卫三刀）、r337（台账引用四刀）迁 `single_substitution_lands`。\n"
        u"③ 七臂重跑：M911…M913、M989…M992 全 CAUGHT；两表 RESTORE_CLEAN。\n"
        u"④ 读数：两张表都是 Python 侧的刀 ⇒ diff 判法不依赖语言。\n\n"
        u"验证读数（现读）：`R313_MUTATE 刀=3 CAUGHT=3`、`MUTATE_TABLE n=4 caught=4`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **12** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 366` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（本轮只动 .scratch 两张表，Swift 一行未改；读数取自 R366 日志）；"
        u"② 多针表与其余历史表的迁移；③ 真机腿没跑。\n\n"
        u"下一轮（R368）的靶：⓪ 读 `452f5a3` / `cc9eb1e` / `7ad22cf` 的跑；"
        u"① 426 第六批（r306–r310 那几张四到六臂的表），或先把多针表的 diff 形状写成 helper；"
        u"② 367 的下一批要先重钉死针再声明。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r366_head, state + r366_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R367_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
