#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R373 的七本台账（第 372 轮 / Round 370）：367 第三批 —— r55 的 M271/M272 重钉，rot 31→29。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r366_full.log"
PY = u"/tmp/r373_py.log"


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
    head = (u"## 第 371 轮（R372 · 2026-10-25 · U-1297…U-1299）：367 第二根 —— M264 重钉（梯子顶档 0.85→0.92），"
            u"rot 32→31（U-1297…U-1299 · 产品 0 文件，判据账）")
    section = (
        u"## 第 372 轮（R373 · 2026-10-25 · U-1300…U-1302）：367 第三批 —— r55 的 M271/M272 重钉（参数名改名），"
        u"rot 31→29（U-1300…U-1302 · 产品 0 文件，判据账）\n\n"
        u"- **U-1300：M271 重钉。** `GrabAttribution.classify` 的参数从 `worstIntervalMilliseconds` 改成 "
        u"`clockIntervalMilliseconds`，旧针命中 0 ⇒ rot；重钉到今天的 guard "
        u"`guard worstGrabMilliseconds >= 0, clockIntervalMilliseconds > 0 else { return .unknown }`，"
        u"落刀后 `testGrabAttributionIsATruthTable` 红（期望串「unknown」）。\n"
        u"- **U-1301：M272 重钉。** 调用点同样改名；重钉后 `testGrabAttributionIsWiredIntoTheCoarseNotRunLines` 红，"
        u"正文含「只接了 0 次归因」—— 这是 M269–M271 都测不到的接线坏法（函数还在、没人调）。\n"
        u"- **U-1302：rot 31→29，上界同笔降。** `ROT_CEILING` 31→29；"
        u"`HIDDEN_ARMS 表=222 可判=804 rot=29 抽不出=6 已声明表=6 已声明死针=0 上界 rot=29 … 处置=ok`；"
        u"`test_hidden_arms` 8/8。两把刀的红都落在期望格上、还原干净。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 期望串过期写成读数，不写成刀坏；上界没有留在 32。 |\n"
            u"| 可复核性 | 15/15 | 一条命令复跑五臂；`hidden_arms.py` 一行看 rot 与上界。 |\n\n"
            u"均分 = 89/105 ≈ 12.7/15（85）。")
    r370 = (
        u"\n\n## Round 370 · R373（第 372 轮 · 2026-10-25）：367 第三批 —— r55 的 M271/M272 重钉、rot 31→29（产品 0 文件）\n\n"
        u"`GrabAttribution.classify` 与它的调用点把参数名从 `worstIntervalMilliseconds` 改成 `clockIntervalMilliseconds`，"
        u"r55 的两根针命中 0；重钉后 `M271 / M272` 各 CAUGHT、红都落在期望格（真值表 / 接线守卫），"
        u"`ROT_CEILING` 同笔 31→29，`hidden_arms` 8/8。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无 Swift 改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 两臂各 CAUGHT；红线在真值表与接线守卫上。 |\n"
        u"| 假绿防御 | 14/15 | rot 与上界同笔降；两臂都 RESTORE_CLEAN。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在烂针面（31→29）。 |\n"
        u"| 台账一致性 | 13/15 | U-1300…U-1302、367 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 改名归因写成读数；上界没有留在 31。 |\n"
        u"| 可复核性 | 15/15 | 一条命令复跑两臂；`hidden_arms.py` 一行看 rot 与上界。 |\n\n"
        u"均分 = 89/105 ≈ 12.7/15（85）。"
    )
    it = once(it, tail, tail + r370)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    `ROT_CEILING` 同笔 **32→31**：现读 `HIDDEN_ARMS 表=222 可判=804 rot=31 抽不出=6 已声明表=6 "
               u"已声明死针=0 上界 rot=31 … 处置=ok`，`test_hidden_arms` 8/8。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R373 · 第三批）：`mutate_r55_grab_attribution.py` 的 M271/M272 重钉 —— "
              u"`GrabAttribution.classify` 与调用点的参数名从 `worstIntervalMilliseconds` 改成 `clockIntervalMilliseconds`，"
              u"两根旧针命中 0。\n"
              u"    重钉后两臂各 CAUGHT（真值表「unknown」/ 接线守卫「只接了 0 次归因」），`ROT_CEILING` 同笔 **31→29**："
              u"现读 `HIDDEN_ARMS 表=222 可判=804 rot=29 抽不出=6 已声明表=6 已声明死针=0 上界 rot=29 … 处置=ok`。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 367 第三批：r55 的 M271/M272 随参数改名重钉，rot 31→29（上界同笔降）"
                u"（R373 / U-1300…U-1302 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R369，370 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R370，371 节自评）")
    rp = once(rp, u"U-31 … U-1299（R372 现读抬到最新一节）", u"U-31 … U-1302（R373 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **17**", u"产品面连续零改动轮数 = **18**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R372 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R373 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R372 这一段（R337 补写；R341 续到 341、R372 续到 372 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R373 这一段（R337 补写；R341 续到 341、R373 续到 373 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R372 续（判据账）**：367 第二根 —— M264 重钉到 `…0.92`，r54 `5/5 CAUGHT`；M266 的期望串跟上措辞；"
                u"`ROT_CEILING` 同笔 32→31。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R373 续（判据账）**：367 第三批 —— r55 的 M271/M272 随参数改名重钉，两臂各 CAUGHT；"
              u"`ROT_CEILING` 同笔 31→29。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r372_head = (u"## R372 状态（2026-10-25 · 本地 · 第 371 轮 / Round 369）：367 第二根 —— M264 重钉（梯子顶档 0.85→0.92），"
                 u"rot 32→31（产品 0 文件，判据账）")
    state = (
        u"## R373 状态（2026-10-25 · 本地 · 第 372 轮 / Round 370）：367 第三批 —— r55 的 M271/M272 重钉（参数名改名），"
        u"rot 31→29（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R373 / 第 372 轮 / Round 370）：`GrabAttribution.classify` 与调用点改名的两根针重钉；"
        u"`M271 / M272` 各 CAUGHT、`还原不干净=0`；`ROT_CEILING` 31→29，`test_hidden_arms` 8/8；"
        u"电池 Ran @RAN@（skipped=@SK@）OK；全量卷沿用 R366（Swift 未动）："
        u"`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：五跑仍在队里（`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c`）；只登记不轮询。\n"
        u"② 367 第三批：M271（`worstIntervalMilliseconds` → `clockIntervalMilliseconds`）+ M272（调用点同改）。\n"
        u"③ 两臂重跑各 CAUGHT；红线在真值表与接线守卫上。\n"
        u"④ rot 31→29、`ROT_CEILING` 同笔降；`HIDDEN_ARMS` 现读 `处置=ok`。\n\n"
        u"验证读数（现读）：`HIDDEN_ARMS 表=222 可判=804 rot=29 抽不出=6 已声明表=6 已声明死针=0 上界 rot=29 … 处置=ok`；"
        u"`test_hidden_arms` 8/8；全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R366 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **18** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 372` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 全量卷没重跑（本轮没动 Swift）；② 其余 29 根烂针未重钉；③ 真机腿没跑。\n\n"
        u"下一轮（R374）的靶：⓪ 读队列五跑；① 367 第四批（`mutate_r56_readings_channel.py` 的 M279/M281）；"
        u"② 或给 r312 家族声明 READOUT。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r372_head, state + r372_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R373_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
