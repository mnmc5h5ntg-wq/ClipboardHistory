#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R377 的七本台账（第 376 轮 / Round 374）：434 结案 —— 读数通道有界等待。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r377_full.log"
PY = u"/tmp/r377_py.log"


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


def product_streak():
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"376"],
                                  cwd=ROOT).decode(u"utf-8")
    m = re.search(r"streak=(\d+)", out)
    assert m, u"product_streak 没解析到：%r" % out
    return int(m.group(1))


def main():
    n, skipped, failures = full_counts()
    ran, py_skipped = battery_counts()
    streak = product_streak()
    assert failures == 0, u"全量卷有 %d 个失败 ⇒ 不许写台账" % failures
    print(u"PARSED full=%d skipped=%d failures=%d battery=%d(%d skipped) streak=%d"
          % (n, skipped, failures, ran, py_skipped, streak))

    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 375 轮（R376 · 2026-10-26 · U-1310…U-1313）：M278 的挂点是刀文自己 —— "
            u"return 吞掉 lock.lock()；433 结案、超时补杀子孙树（U-1310…U-1313 · 产品 0 文件，判据账）\n")
    section = (
        u"## 第 376 轮（R377 · 2026-10-26 · U-1314…U-1317）：434 结案 —— 读数通道装上有界等待"
        u"（M1010 CAUGHT）；r56 十把刀第一次进针预检（U-1314…U-1317 · 产品 0 文件，判据账）\n\n"
        u"- **U-1314：`boundedChannelProbe` 落地。** 守卫里「发两行 + 读回全文」那一段以前跑在主线程上 ——"
        u"通道一死锁，判据就不是变红而是挂住（R374 的 6:29）。现在整段放进后台队列，主线程最多等 5 秒；"
        u"超时走具名出口 `READOUT_CHANNEL_BLOCKED`（不是「没变化」）。**正对照同一格**：合成一个"
        u"闸门永不打开的动作、给 50ms 截止，必须判超时**且**不交回半个结果（断言完再放行闸门）。"
        u"第一版用的是 `Thread.sleep(0.3)` —— 电池里 `wait_scan` 名册当场点名「未登记的固定挂钟等待」，"
        u"连带的 `skip_roster` 内层汇总也一起红（内层那一卷读不到结论行）⇒ 换成确定性闸门。守卫现读 `passed (0.090 seconds)`；"
        u"`swift build --build-tests` 告警 **0**。\n"
        u"- **U-1315：M1010 把「阻塞」变成可判的红。** 新刀在 `CaptureReadings.emit(_:to:)` 里 sleep 30s"
        u"（写文件之前就返回不了），现读 `CAUGHT 红得对=True 命中=['READOUT_CHANNEL_BLOCKED'] 还原干净=True`、"
        u"表尾 `还原后复跑（Swift 守卫）：ESCAPED`、`EXIT=0`。这把刀与 M278 分得开：M278 是「写不进去」"
        u"（读文件那一格红），M1010 是「写之前就不返回」（只有 deadline 能救）。\n"
        u"- **U-1316：r56 的十把刀第一次进针预检。** 三处一起漏：① 表**没登记**进 `TABLES`"
        u"（`TABLE_ROSTER` 一直点名 `mutate_r56_readings_channel(9)`）；② 抽取器不认识它的五元组形状"
        u"`(编号, 说明, 文件, kind, 原文, 变异文, filter, heads)`，把 kind 当 needle；③ `.yml` 不算源文件 ⇒ "
        u"打在 `ci.yml` 上的四把刀连「抽不出来」都不算。三处都修后现读 "
        u"`mutate_r56_readings_channel M1010 ok；M277 ok；…；M285 ok`、"
        u"`NEEDLE_PRECHECK tables=135 covered=118 arms=386 bad=0`；未登记缺口 75/423 → **74/414**"
        u"（`test_the_roster_gap_is_pinned_to_the_measured_number` 的地板同笔改，红话写明「改账之前先看清是哪张表」）。\n"
        u"- **U-1317：守卫头上那段注释写了两遍。** 92–95 行是同一段（含同一条 BACKLOG 79 理由）复制了两份 ——"
        u"这次改动落在它紧邻的位置才看见，同笔去重；不动任何断言。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 12 格测试 + 三跑 sample 栈 + 一张表一条命令；孙进程由 `pgrep` 现读。 |\n\n"
            u"均分 = 91/105 ≈ 13.0/15（87）。")
    r374 = (
        u"\n\n## Round 374 · R377（第 376 轮 · 2026-10-26）：434 结案 —— 读数通道有界等待（M1010 CAUGHT）；"
        u"r56 十把刀第一次进针预检（产品 0 文件）\n\n"
        u"守卫里「emit 两行 + 读回全文」挪进 `boundedChannelProbe(deadline: 5)`，超时具名 "
        u"`READOUT_CHANNEL_BLOCKED`；同一格用「闸门不打开 vs 50ms 截止」作正对照（必须超时且不交回半个结果）。"
        u"新刀 M1010 在 emit 里 sleep 30s：现读 CAUGHT、命中该名字、还原干净、复跑 ESCAPED、表 EXIT=0。"
        u"顺手把 r56 真正登记进针预检名册（此前 10 把刀一把都没被静态预检过）：认五元组形状 + `.yml` 算源文件，"
        u"现读 `tables=135 covered=118 arms=386 bad=0`，未登记缺口 75/423→74/414。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | M1010 CAUGHT 且命中具名出口；守卫基线 0.090s 通过；超时控制在同一格。 |\n"
        u"| 假绿防御 | 15/15 | 超时不算通过；「不交回半个结果」有断言；预检覆盖面同笔扩大且 bad=0。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在「通道阻塞会红而不是挂死」这条可靠性上。 |\n"
        u"| 台账一致性 | 14/15 | U-1314…U-1317、D-365、434 结案、名册地板同笔降；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | M1010 与 M278 的差别写清（写不进 vs 写前不返回）；没把 CI 未跑冒充成跑过。 |\n"
        u"| 可复核性 | 15/15 | 一张表一条命令；超时由同格的合成样本兑现，不靠注释。 |\n\n"
        u"均分 = 91/105 ≈ 13.0/15（87）。"
    )
    it = once(it, tail, tail + r374)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    修法（下一格）：守卫里给 `emit` + 读文件加有界等待（后台队列 + 超时 `XCTFail`，超时要具名），"
               u"并用一支 `sleep` 注入（在 emit 里 sleep 30s）作证「超时后变红而不是挂住」；"
               u"本机可复现，前提是注入不改 `return`/锁的不变式。")
    bl_add = (bl_tail + u"\n"
              u"\n"
              u"    434 追记（R377 · 结案）：`MotionFilmstripTests.boundedChannelProbe(deadline:)` 落地 —— "
              u"「emit 两行 + 读回全文」整段进后台队列，主线程最多等 5s，超时走具名出口 "
              u"`READOUT_CHANNEL_BLOCKED`（不是「没变化」）。同一格的正对照：合成闸门（断言完再放行）+ 50ms 截止 ⇒ "
              u"必须超时且不交回半个结果；守卫现读 `passed (0.090 seconds)`。\n"
              u"    证人 M1010（emit 写盘前 sleep 30s）：现读 `CAUGHT 红得对=True 命中=['READOUT_CHANNEL_BLOCKED'] "
              u"还原干净=True`、复跑 `ESCAPED`、表 `EXIT=0`。与 M278 的分界：M278 是「写不进去」，"
              u"M1010 是「写之前就不返回」——前者读文件那格红，后者只有 deadline 能救。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：超时的处理顺序固定为「先快照子孙树 → killpg → 逐个 SIGKILL 快照里的 pid」；"
               u"快照必须带正对照（能看见活的孙进程），并至少有一格测试让孙进程**自开会话**。\n")
    d_new = (dc_tail + u"\n"
             u"### D-365（377）判据里任何会阻塞的 IO 都必须在有界等待里跑，超时要具名\n\n"
             u"R374–R377 现读：读数通道在锁上死等时，XCTest 不会超时，整卷会一直挂着 —— 在本机是 6 分 29 秒"
             u"没人收尸，在 CI 就是 6 小时上限；而账上能写的只有「看起来还在跑」。R377 把「emit 两行 + 读回」"
             u"放进 5s 有界等待，超时红在 `READOUT_CHANNEL_BLOCKED`，M1010（写前 sleep 30s）第一次让这条路径变红。\n"
             u"**Why**：挂死比红更坏 —— 红会指名，挂死只占机器；一个「不能说不」的判据在预算尽头等于不存在。\n"
             u"**How to apply**：凡是判据里等别的线程/等盘/等锁，一律「后台执行 + 有界等待 + 超时具名」；"
             u"超时那一路只许交回 nil（不许半个结果），并配一条同格的合成正对照证明截止会触发。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 读数通道装上 5s 有界等待（超时具名 READOUT_CHANNEL_BLOCKED）+ M1010 证人；r56 十把刀首次进针预检，434 结案（R377 / U-1314…U-1317 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R373，374 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R374，375 节自评）")
    rp = once(rp, u"U-31 … U-1313（R376 现读抬到最新一节）", u"U-31 … U-1317（R377 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **21**", u"产品面连续零改动轮数 = **22**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R376 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R377 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R376 这一段（R337 补写；R341 续到 341、R376 续到 376 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R377 这一段（R337 补写；R341 续到 341、R377 续到 377 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R376 续（判据账）**：M278 的挂点判成**刀文**（`return` 换行被解析成 `return lock.lock()`，"
                u"第一刀拿走锁不解锁）+ 刀文自检 4 格；\n"
                u"  M278 第一次 `CAUGHT`；超时补杀子孙树 2 格；开 434（通道阻塞会挂死整卷）。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R377 续（判据账）**：434 结案 —— 通道「emit 两行 + 读回」进 5s 有界等待，超时具名 "
              u"`READOUT_CHANNEL_BLOCKED`；M1010（写前 sleep 30s）`CAUGHT`；\n"
              u"  r56 十把刀首次进针预检（认出五元组 + `.yml`），`covered=118 arms=386 bad=0`，缺口 75/423→74/414。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r376_head = (u"## R376 状态（2026-10-26 · 本地 · 第 375 轮 / Round 373）：M278 的挂点是刀文自己 —— "
                 u"return 吞掉 lock.lock()；433 结案、超时补杀子孙树（产品 0 文件，判据账）")
    state = (
        u"## R377 状态（2026-10-26 · 本地 · 第 376 轮 / Round 374）：434 结案 —— 读数通道 5s 有界等待"
        u"（M1010 CAUGHT）；r56 十把刀第一次进针预检（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R377 / 第 376 轮 / Round 374）：守卫里「emit 两行 + 读回全文」挪进 "
        u"`boundedChannelProbe(deadline: 5)`，超时具名 `READOUT_CHANNEL_BLOCKED`，同格合成正对照（闸门 / 50ms 截止）；"
        u"新刀 M1010（emit 写盘前 sleep 30s）现读 CAUGHT、命中该名字、还原干净、复跑 ESCAPED、表 EXIT=0；"
        u"r56 真登记进针预检名册并认五元组形状 + `.yml` 源文件 ⇒ `covered=118 arms=386 bad=0`，缺口 75/423→74/414（地板同笔改）；"
        u"`swift build --build-tests` 告警 **0**；全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`1ff9d11`（R376）刚推、run id 未读；`187ffaf`/`2ffc6d0`/`84e4381`/`357a763` 仍在队里；"
        u"`a17bc6a`（R373 追记）success；只登记不轮询。\n"
        u"② 434 产品/判据面：`boundedChannelProbe` + 超时出口 + 同格正对照；守卫 0.090s 通过。\n"
        u"③ 新刀 M1010 落刀 → CAUGHT（READOUT_CHANNEL_BLOCKED）；还原干净、复跑 ESCAPED。\n"
        u"④ r56 覆盖修补：登记 + 五元组形状 + `.yml`；顺带去重守卫头上重复两遍的注释。\n\n"
        u"验证读数（现读）：`swift build --build-tests` EXIT=0、`grep -c warning:` = **0**；"
        u"基线守卫 `passed (0.090 seconds)`；`M1010 ⇒ CAUGHT 红得对=True "
        u"命中=['READOUT_CHANNEL_BLOCKED'] 还原干净=True`；"
        u"预检 `tables=135 covered=118 arms=386 bad=0`；`TABLE_ROSTER registered=135 unregistered_with_arms=74 hidden_arms=414`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 `Ran @RAN@（skipped=@SK@）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；"
        u"产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 376` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 真机腿没跑；② 帧基线没重捕（本轮无产品/夹具改动，沿用 R356 帧）；"
        u"③ M1010 只在「写前 sleep」这一种阻塞形状上验过，锁死等 / 磁盘卡死的形状仍未各配一把刀。\n\n"
        u"下一轮（R378）的靶：⓪ 读队列（含 `1ff9d11` 的 run id）；① 367 继续（rot 27）；"
        u"② 134→135 名册之后，`covered` 仍差 17 张（抽不出的那批）要逐张点名。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(streak)))
    st = once(st, r376_head, state + r376_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R377_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d"
          % (n, skipped, failures, ran, py_skipped, streak))


if __name__ == u"__main__":
    main()
