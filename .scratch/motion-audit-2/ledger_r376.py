#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R376 的七本台账（第 375 轮 / Round 373）：M278 的挂点是刀文自己；433 结案。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r374_full.log"
PY = u"/tmp/r376_py_pre.log"


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
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"375"],
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
    head = (u"## 第 374 轮（R375 · 2026-10-26 · U-1307…U-1309）：433 第一半 —— 崩溃安全还原 + 硬超时；"
            u"M279/M281 CAUGHT、M278 以 180s 超时具名（U-1307…U-1309 · 产品 0 文件，判据账）\n")
    section = (
        u"## 第 375 轮（R376 · 2026-10-26 · U-1310…U-1313）：M278 的挂点是刀文自己 —— "
        u"return 吞掉 lock.lock()；433 结案、超时补杀子孙树（U-1310…U-1313 · 产品 0 文件，判据账）\n\n"
        u"- **U-1310：M278 的挂点抓到了，不在产品里，在刀文里。** 落刀后 30s `sample <pid>` 连抓三跑，"
        u"栈都停在 `CaptureReadings.swift:76 lock.lock()`；编译器同一份合成文本给出的原文是 "
        u"`warning: expression following 'return' is treated as an argument of the 'return'`。"
        u"旧刀文是「针 + 一行 `return   // MUTANT`」，而针后面紧跟着 `lock.lock()` ⇒ Swift 把它解析成 "
        u"`return lock.lock()`：第一刀**真的把 NSLock 拿走了**，然后直接返回，`defer { lock.unlock() }` "
        u"永不执行 ⇒ 同一进程第二次 `emit` 死等。R374 的 6:29 与 R375 的 180s 超时都是这一条；"
        u"它既不是产品缺陷，也不是守卫没牙。\n"
        u"- **U-1311：刀改成整段替换，M278 第一次拿到 CAUGHT。** 把 `emit(_:to:)` 的文件腿整块删掉"
        u"（不留 `return` 悬念），现读 `M278 ⇒ CAUGHT 红得对=True 命中=['文件里没有这一遍的 marker'] "
        u"还原干净=True`；表尾 `还原后复跑（Swift 守卫）：ESCAPED`、`EXIT=0`。\n"
        u"- **U-1312：这种刀文在落盘之前就拦下。** `knife_guard.swallowed_return_lines` 认「`return` 独占一行 + "
        u"下一非空行是调用表达式」，r56 的 `apply` 在写盘前调用它（命中即 `SystemExit`，文件不动）；"
        u"4 格测试（M278 原形必须抓到 / `}` / `case` / `return ()` 三种必须不抓）。按「替换文以 return 结尾」"
        u"扫全部 222 张表，现读 `HITS=0` ⇒ 这个形状在仓库里只有 M278 一支，已修。\n"
        u"- **U-1313：硬超时补杀子孙树。** R375 超时那一刀的 `xctest` 没死：它被 launchd 收养（ppid=1）"
        u"又活了 9 分钟，只 `killpg` 杀不到。现在超时前先快照整棵子孙树，杀完进程组再逐个 SIGKILL；"
        u"2 格测试：孙进程**自开会话**也必须消失（`pgrep` 现读空），以及快照必须真看见活的孙进程（正对照）。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 6 格测试 + 三臂一条命令；超时由 `sleep 5` 正对照兑现。 |\n\n"
            u"均分 = 90/105 ≈ 12.9/15（86）。")
    r373 = (
        u"\n\n## Round 373 · R376（第 375 轮 · 2026-10-26）：M278 的挂点是刀文自己（return 吞掉 lock.lock()）；"
        u"433 结案 + 超时补杀子孙树（产品 0 文件）\n\n"
        u"`sample` 三跑同栈把挂点钉在 `lock.lock()`，编译器 warning 给出机制：`return` 换行被解析成 "
        u"`return lock.lock()`，第一刀拿走 NSLock 不解锁 ⇒ 第二次 `emit` 死等。刀文改成整段替换后 "
        u"`M278 CAUGHT`（命中「文件里没有这一遍的 marker」）、还原干净、复跑守卫 ESCAPED、表 EXIT=0。"
        u"新尺 `swallowed_return_lines` 接进 r56 的落刀前检查（4 格），全仓库 222 张表按「替换文以 return 结尾」"
        u"现读 0 支；超时补杀子孙树（2 格，含自开会话的孙进程），因为在 R375 那一刀里 xctest 被 launchd 收养又活了 9 分钟。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | M278 现读 CAUGHT，红在期望那一格；三臂/复跑/EXIT 三项同一次运行里读出。 |\n"
        u"| 假绿防御 | 15/15 | 刀文自检在落盘前拦截；`return` 三种合法形状不抓（防假红）；超时不算 CAUGHT。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在刀的可靠性上（不再挂死、不再留孤儿）。 |\n"
        u"| 台账一致性 | 14/15 | U-1310…U-1313、D-363/D-364、433 结案 + 434 开单；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 挂起从「产品可疑」改判成「刀坏」，并把「通道阻塞会挂死整卷」另开 434，不冒充已修。 |\n"
        u"| 可复核性 | 15/15 | 12 格测试 + 三跑 sample 栈 + 一张表一条命令；孙进程由 `pgrep` 现读。 |\n\n"
        u"均分 = 91/105 ≈ 13.0/15（87）。"
    )
    it = once(it, tail, tail + r373)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"367 追记（R375）：M279/M281 两臂 CAUGHT（「不在末尾两格」/「扫描函数在合成样本上抓不到」）；"
               u"M278 记 NOT_RUN_TIMEOUT（刀没验成，针本来就活着，rot 仍 27）。")
    bl_add = (bl_tail + u"\n\n"
              u"433 追记（R376 · 结案）：挂点抓到了 —— **刀文自己**。旧替换文是「针 + 一行 `return  // MUTANT`」，"
              u"而针后面紧跟 `lock.lock()`，Swift 解析成 `return lock.lock()`（编译器原文 "
              u"`expression following 'return' is treated as an argument of the 'return'`）："
              u"第一刀把 NSLock 拿走再返回，`defer { lock.unlock() }` 永不执行 ⇒ 第二次 emit 死等。\n"
              u"    证据：`sample <pid>` 连抓三跑，栈都停在 `CaptureReadings.swift:76 lock.lock()`；"
              u"R374 的 6:29 与 R375 的 180s 超时同因。\n"
              u"    修法：① 刀文改成整段替换（删掉文件腿整块）⇒ `M278 CAUGHT`（命中「文件里没有这一遍的 marker」）、"
              u"还原干净、复跑守卫 `ESCAPED`、表 `EXIT=0`；② `knife_guard.swallowed_return_lines` + 4 格测试，"
              u"r56 的 `apply` 在写盘前拦截（命中即 `SystemExit`，文件不动）；按「替换文以 return 结尾」扫 222 张表，"
              u"现读 0 支；③ 硬超时补杀子孙树（R375 的 xctest 被 launchd 收养又活 9 分钟）——2 格测试，"
              u"含孙进程自开会话也必须消失。\n"
              u"\n"
              u"**434. 读数通道一旦阻塞，整卷会挂死而不是变红**（R376）\n"
              u"    症状（R374–R376 的真实样本）：xctest 在 `emit` 的锁上死等 6:29；强杀父进程后它被 launchd 收养，"
              u"又活了 9 分钟；三次 `sample` 同栈。今天这条路径被「刀文自检」堵住了入口，但**读数通道本身没有超时**："
              u"任何一次真死锁都会让 `swift test` 挂到 CI 的 6 小时上限，而不是红一格。\n"
              u"    修法（下一格）：守卫里给 `emit` + 读文件加有界等待（后台队列 + 超时 `XCTFail`，超时要具名），"
              u"并用一支 `sleep` 注入（在 emit 里 sleep 30s）作证「超时后变红而不是挂住」；"
              u"本机可复现，前提是注入不改 `return`/锁的不变式。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：凡是「修法把某个可量的量从坏值拉到好值」，结案那一笔就要在同一次提交里把这个量写成地板；"
               u"地板取两机读数的最小值再留一档余量（1.00 → 0.90），不贴着 1.00 写死，也不许低于修法前的实测值。\n")
    d_new = (dc_tail + u"\n"
             u"### D-363（376）刀文里不许用「`return` 换行收尾」，除非下一行不是表达式\n\n"
             u"R376 现读：M278 的旧替换文以 `return   // MUTANT` 结尾，而针在文件里紧跟 `lock.lock()`，"
             u"Swift 把它解析成 `return lock.lock()` —— 刀实际做的是「拿走 NSLock 不解锁」，"
             u"守卫因此挂死 6:29/180s 两次，而账上一直写成「可复现挂起，原因未知」。\n"
             u"**Why**：刀要证的是「判据能说不」，可一个语义都不是它声称的刀，抓到了也不作证；"
             u"挂死比红更坏（CI 6 小时上限、占 runner）。\n"
             u"**How to apply**：替换文要在**语句边界**收尾（整段删/整段换），不留 `return` 悬念；"
             u"确实要提前返回时写 `return ()` 或让下一行是 `}`；落刀前用 `swallowed_return_lines` 扫一遍，"
             u"命中即拒（文件不动）。\n\n"
             u"### D-364（376）硬超时要杀「当时可见的整棵子孙树」，不是只杀进程组\n\n"
             u"R375 的 180s 超时确实触发了，但那一跑的 `xctest` 不在 `swift-test` 的进程组里："
             u"父进程死后它被 launchd 收养（ppid=1），又跑了 9 分钟才被我手动 `kill -9`。"
             u"**Why**：只杀进程组 = 用一个假设（子孙都留在组里）当保证；现实里测试框架会自开会话。\n"
             u"**How to apply**：超时的处理顺序固定为「先快照子孙树 → killpg → 逐个 SIGKILL 快照里的 pid」；"
             u"快照必须带正对照（能看见活的孙进程），并至少有一格测试让孙进程**自开会话**。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### M278 的挂点是刀文自己（return 吞掉 lock.lock()）；刀文自检 + 超时补杀子孙树，433 结案（R376 / U-1310…U-1313 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R372，373 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R373，374 节自评）")
    rp = once(rp, u"U-31 … U-1309（R375 现读抬到最新一节）", u"U-31 … U-1313（R376 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **20**", u"产品面连续零改动轮数 = **21**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R375 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R376 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R375 这一段（R337 补写；R341 续到 341、R375 续到 375 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R376 这一段（R337 补写；R341 续到 341、R376 续到 376 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R375 续（判据账）**：433 第一半 —— `knife_guard.py`（备份/恢复/进程组超时）+ 6 格测试；"
                u"r56 两臂 `CAUGHT`（M279/M281）、\n"
                u"  M278 `NOT_RUN_TIMEOUT`（180s，R374 是 6:29）；三臂还原干净、复跑守卫绿。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R376 续（判据账）**：M278 的挂点判成**刀文**（`return` 换行被解析成 `return lock.lock()`，"
              u"第一刀拿走锁不解锁）+ 刀文自检 4 格；\n"
              u"  M278 第一次 `CAUGHT`；超时补杀子孙树 2 格；开 434（通道阻塞会挂死整卷）。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r375_head = (u"## R375 状态（2026-10-26 · 本地 · 第 374 轮 / Round 372）：433 第一半 —— 崩溃安全还原 + 硬超时；"
                 u"M279/M281 CAUGHT、M278 以 180s 超时具名（产品 0 文件，判据账）")
    state = (
        u"## R376 状态（2026-10-26 · 本地 · 第 375 轮 / Round 373）：M278 的挂点是刀文自己 —— "
        u"return 吞掉 lock.lock()；433 结案、超时补杀子孙树（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R376 / 第 375 轮 / Round 373）：`sample` 三跑同栈抓到 M278 的挂点"
        u"（`return` 换行被解析成 `return lock.lock()`，第一刀拿走 NSLock 不解锁）；刀文改成整段替换 ⇒ "
        u"`M278 CAUGHT`、还原干净、复跑 `ESCAPED`、表 EXIT=0；`swallowed_return_lines` + 4 格测试 + 落刀前拦截"
        u"（222 张表按「替换文以 return 结尾」现读 0 支）；超时补杀子孙树 + 2 格测试；"
        u"全量沿用 R374（本轮没动 Swift）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`a17bc6a`（R373 追记）success；`357a763`/`84e4381`/`2ffc6d0`/`187ffaf` 四跑仍在队里"
        u"（`187ffaf ↔ 40210952259`、`2ffc6d0 ↔ 40210881173`）；只登记不轮询。\n"
        u"② 433 第二半：落刀后 30s `sample` 三跑同栈 + 编译器 warning ⇒ 挂点=刀文，不是产品/守卫。\n"
        u"③ 刀文改整段替换；`swallowed_return_lines` 在 `apply` 里落盘前拦截；M278 现读 CAUGHT。\n"
        u"④ 超时补杀子孙树（R375 的 xctest 被 launchd 收养又活 9 分钟）；祖先快照 + 逐个 SIGKILL。\n\n"
        u"验证读数（现读）：`M278 ⇒ CAUGHT 红得对=True 命中=['文件里没有这一遍的 marker'] 还原干净=True`、"
        u"`还原后复跑（Swift 守卫）：ESCAPED`、表 `EXIT=0`；`test_knife_guard` **12 格**全绿（含自开会话的孙进程）；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R374 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；"
        u"预检 `tables=134 covered=117 arms=376 bad=0`；`HIDDEN_ARMS 表=222 可判=804 rot=27`；"
        u"产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 375` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R374 日志）；"
        u"③ 434（读数通道无超时）只留下症状样本，修法与 witness 尚未落地。\n\n"
        u"下一轮（R377）的靶：⓪ 读队列；① 434 的有界等待 + `sleep` 注入作证；② 367 继续（rot 27）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(streak)))
    st = once(st, r375_head, state + r375_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R376_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d"
          % (n, skipped, failures, ran, py_skipped, streak))


if __name__ == u"__main__":
    main()
