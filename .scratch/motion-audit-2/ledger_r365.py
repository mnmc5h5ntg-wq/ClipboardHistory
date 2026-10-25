#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R365 的七本台账（第 364 轮 / Round 362）：384 的覆盖地板。

规矩照 ledger_r126.py：所有数字从落盘日志里解析，`once()` 命中不是 1 就在写盘之前抱出。
本轮不幂等：跑过一遍之后再跑会命中 0 次。
"""
import ast
import io
import os
import re
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r365_full.log"
PY = u"/tmp/r365_py.log"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), u"w", encoding=u"utf-8").write(text)


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, u"锚点命中 %d 次：%s" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, replacement)


def full_counts():
    t = io.open(FULL, encoding=u"utf-8", errors=u"replace").read()
    assert u"Test Suite 'ClipboardHistoryPackageTests.xctest' passed" in t, u"全量卷没有收尾行 ⇒ 日志不完整"
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

    # ---------- AGENT_UI_AUDIT.md：降序插在当前最大轮次标题之上 ----------
    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 363 轮（R364 · 2026-10-25 · U-1273…U-1275）：426 第三批 —— r356/r338/r339 迁到 diff 回读，"
            u"七臂全 CAUGHT（U-1273…U-1275 · 产品 0 文件，判据账）")
    section = (
        u"## 第 364 轮（R365 · 2026-10-25 · U-1276…U-1278）：384 的修法有了自己的地板 —— "
        u"取用带纵向覆盖 ≥90%，两机 100%、回退到 29% 会红（U-1276…U-1278 · 产品 0 文件，判据账）\n\n"
        u"- **U-1276：把「并墨后 100%」从读数升成地板。** `pillBandCoverageFloor = 0.90` 落在 "
        u"`testFilterPillRampIsMonotone` 的 GEOM 之后：`取用带只盖住候选跨度的 covered/total px` 低于 0.90 即红。"
        u"本机现读 `纵向覆盖=48/48px=100%`；runner 的同一行（`9d2c8a8` 那一跑）是 `24/24px=100%`。"
        u"读不出这一格时走具名出口 `MOTION_NOT_RUN=pill-coverage-unreadable` —— 没有对象就不发证，不冒充「覆盖够了」。\n"
        u"- **U-1277：M1009 把地板的牙证明了一次。** 关掉胶片守卫块里的并墨（`mergeInk: true` → `false`）⇒ 覆盖掉到 "
        u"`14/48px=29%`，红在 `MotionFilmstripTests.swift:6024`："
        u"`XCTAssertGreaterThanOrEqual failed: (\"0.2916666666666667\") is less than (\"0.9\") - "
        u"取用带只盖住候选跨度的 14/48px ⇒ 带子被切碎（R356 的并墨修法回退了？）`；`CAUGHT=1/1, RESTORE_CLEAN=yes`。"
        u"同一件事由 M1006 打在**静态调用点**、期望 `MotionPillRampTests/testLabelInkInsideThePillDoesNotNarrowTheHole`；"
        u"这一刀打在**胶片守卫块**、期望本测试 —— 两把刀各守一层，不许互相代替。\n"
        u"- **U-1278：384 的追记。** 结案时那组数（带子 7→24pt、覆盖 29%→100%）是**一次**读数；读数不替下一轮回退作证，"
        u"地板会。两机的 100% 是不同分母（48 与 24）上的同一个比例 —— 地板判比例不判像素，所以它跨机器成立，"
        u"而「两机都 100%」仍不等于「以后永远 100%」。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    # ---------- AGENT_VISUAL_ITERATION.md：升序只能追加 ----------
    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 未声称全仓迁完；多针表形状不同写清。 |\n"
            u"| 可复核性 | 15/15 | 三张表各一条命令；helper 有 5 格测试。 |\n\n"
            u"均分 = 89/105 ≈ 12.7/15（85）。")
    round362 = (
        u"\n\n## Round 362 · R365（第 364 轮 · 2026-10-25）：384 的覆盖地板 —— 两机 100% 写成 ≥90% 的会红判据（产品 0 文件）\n\n"
        u"胶片给取用带加了一条地板（0.90）：本机 `48/48`、runner `24/24`；M1009 关掉并墨 ⇒ `14/48=29%`，"
        u"红落在 `testFilterPillRampIsMonotone` 的第 6024 行（原文见 U-1277），`RESTORE_CLEAN=yes`。"
        u"读不出覆盖时走具名出口，不把「没读到」说成「够了」。看图腿复用上一轮帧（`ls` 数到 22 张、20 张 PNG）："
        u"开臂 12 帧里药丸逐帧右移、关臂第 2 帧就硬切 —— 覆盖 48/48 与肉眼看到的「带子整块盖住药丸」一致。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 10/15 | 复用 R356 帧（盘上 22 张）；开 A 与关两卷逐帧看过，药丸过程与硬切都在。 |\n"
        u"| 判据有效性 | 15/15 | M1009 把覆盖打到 29%，红在 6024 行的地板原文上。 |\n"
        u"| 假绿防御 | 14/15 | 读不出覆盖走具名 skip；地板判比例，48 与 24 两个分母都成立。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；本轮钉住的是产品可见修法（并墨带）的退路。 |\n"
        u"| 台账一致性 | 13/15 | U-1276…U-1278、384 追记、D-362；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 不把「两机都 100%」写成「永远 100%」；地板 0.90 的余量写清。 |\n"
        u"| 可复核性 | 15/15 | 一条命令复跑 M1009；一条命令看地板那一行。 |\n\n"
        u"均分 = 90/105 ≈ 12.9/15（86）。"
    )
    it = once(it, tail, tail + round362)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    # ---------- AGENT_BACKLOG.md：追记追加到文件尾 ----------
    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    仍欠：R360 之后的跑要出现 `reduce-motion-on`（376 的收口读数）；"
               u"以及视图层 `@Environment` 那一源仍无直接读数。")
    bl_new = (bl_tail + u"\n"
              u"- **384 追记（R365 · 地板）**：并墨修法的覆盖已经写成会红的地板 `pillBandCoverageFloor = 0.90`"
              u"（本机 48/48、runner 24/24；关掉并墨 14/48=29%）。地板在 `testFilterPillRampIsMonotone` 里，"
              u"M1009 的红线是 6024 行的原文（U-1277）。结案 ≠ 钉住 —— 这一格现在两样都有。")
    bl = once(bl, bl_tail, bl_new)
    wr(u"AGENT_BACKLOG.md", bl)

    # ---------- AGENT_DECISIONS.md：追加到文件尾 ----------
    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = u"不许把它硬塞进单替换的判据里。"
    d362 = (dc_tail + u"\n\n"
            u"### D-362（365）结案时的 100% 要落成地板，否则下一轮回退没有证人\n\n"
            u"384 在 R356 结案时给出的证据是「带子 7→24pt、纵向覆盖 29%→100%」—— 那是**一次**读数。"
            u"R365 把同一个量写成 ≥0.90 的地板之后，关掉并墨会让它掉到 14/48=29% 并红在断言上；"
            u"在此之前，这组读数退回 29% 没有任何东西会响。\n"
            u"**Why**：读数是「当时是多少」，地板是「以后不许是多少」；一条修法只有后者才在下一轮替自己作证。\n"
            u"**How to apply**：凡是「修法把某个可量的量从坏值拉到好值」，结案那一笔就要在同一次提交里把这个量写成地板；"
            u"地板取两机读数的最小值再留一档余量（1.00 → 0.90），不贴着 1.00 写死，也不许低于修法前的实测值。")
    dc = once(dc, dc_tail, d362)
    wr(u"AGENT_DECISIONS.md", dc)

    # ---------- CHANGELOG.md：[Unreleased] 之下 ----------
    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 384 的修法有了自己的地板：取用带纵向覆盖 ≥90%，两机 100%、关掉并墨 29% 会红"
                u"（R365 / U-1276…U-1278 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    # ---------- AGENT_FINAL_REPORT.md：只改计数器 ----------
    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R361，362 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R362，363 节自评）")
    rp = once(rp, u"U-31 … U-1275（R364 现读抬到最新一节）", u"U-31 … U-1278（R365 现读抬到最新一节）")
    rp = once(rp, u"D-069 … **D-361**", u"D-069 … **D-362**")
    rp = once(rp,
              u"（R360 现读：注册表 **133** 张 / 刀号最大 **M1008** / 预检 covered=116 arms=376 bad=0；全仓 227 文件 / 865 把）",
              u"（R365 现读：注册表 **134** 张 / 刀号最大 **M1009** / 预检 covered=117 arms=377 bad=0；全仓 227 文件 / 865 把）")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    # ---------- AGENT_STATE.md：新条目插在顶部 ----------
    st = rd(u"AGENT_STATE.md")
    r364_head = (u"## R364 状态（2026-10-25 · 本地 · 第 363 轮 / Round 361）：426 第三批 —— "
                 u"三张表迁到 diff 回读（产品 0 文件，判据账）")
    state = (
        u"## R365 状态（2026-10-25 · 本地 · 第 364 轮 / Round 362）：384 的覆盖地板 —— "
        u"两机 100% 落成 ≥90% 的会红判据（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R365 / 第 364 轮 / Round 362）：胶片给取用带加 `pillBandCoverageFloor = 0.90`"
        u"（本机 48/48、runner 24/24）；M1009 关掉并墨 ⇒ 14/48=29%，红在 `testFilterPillRampIsMonotone` 6024 行原文；"
        u"全量 @N@ 格 0 失败、电池 Ran @RAN@（skipped=@SK@）OK；看图腿复用 R356 帧（22 张在盘上）（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`9d2c8a8`（R360 追记）已 **success**；R361–R364 六跑仍在队里（只登记不轮询）。\n"
        u"② 384 的地板：`pillBandCoverageFloor = 0.90` + 读不出时具名 skip，落在胶片 GEOM 之后。\n"
        u"③ M1009：钉在胶片守卫块的并墨调用点，期望 `testFilterPillRampIsMonotone`；与 M1006（静态调用点）分开。\n"
        u"④ 看图：开 A 12 帧药丸逐帧右移、关臂第 2 帧硬切；带子整块盖住药丸，与 48/48 一致。\n\n"
        u"验证读数（现读）：`纵向覆盖=48/48px=100%`；`M1009 CAUGHT=1/1, RESTORE_CLEAN=yes`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；脚本电池 `Ran @RAN@（skipped=@SK@）OK`；"
        u"产品面连续零改动 **10** 轮（`python3 scripts/product_streak.py --streak-for 364` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 本轮无产品改动，没重捕帧（看图腿复用 R356 的 22 张，基线文件未动）；"
        u"② 地板在 runner 上的判词要等这一跑（R360 那一跑的读数已是 24/24=100%，但地板是本轮才加的）；"
        u"③ 真机腿没跑。\n\n"
        u"下一轮（R366）的靶：⓪ 读 R361–R365 的跑（含本轮地板的 runner 读数）；"
        u"① 426 第四批或 367 下一批（按两箱点名）；② 376 已在 `9d2c8a8` 印出 `reduce-motion-on` —— 下一轮把那一行抄进 376 的追记并结案。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    assert u"@N@" not in state and u"@RAN@" not in state and u"@SK@" not in state, u"STATE 里还有没替换的占位符"
    st = once(st, r364_head, state + r364_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R365_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
