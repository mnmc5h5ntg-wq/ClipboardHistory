#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R378 的七本台账（第 377 轮 / Round 375）：367 第三批 —— 七把腐烂针重钉，rot 27→21。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r377_full.log"
PY = u"/tmp/r378_py.log"


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
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"377"],
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
    head = (u"## 第 376 轮（R377 · 2026-10-26 · U-1314…U-1317）：434 结案 —— 读数通道装上有界等待"
            u"（M1010 CAUGHT）；r56 十把刀第一次进针预检（U-1314…U-1317 · 产品 0 文件，判据账）\n")
    section = (
        u"## 第 377 轮（R378 · 2026-10-26 · U-1318…U-1321）：367 第三批 —— 七把腐烂针重钉，rot 27→21；"
        u"M188 的旧刀编译不过被当场判成刀坏（U-1318…U-1321 · 产品 0 文件，判据账）\n\n"
        u"- **U-1318：r40 的四把针跟着 API 改。** R40 写它们时决策函数是 `decide(copyErrorMessage:)`，"
        u"后来变成 `decide(failure: ClipboardWriteFailure?)`，针里又把两行注释一起带着 ⇒ 盘上一个都不命中。"
        u"针改到 switch 整块（含新签名）后四臂现读 `M185/M186/M187/M188 CAUGHT`，"
        u"红在各自主张的那两格（闸门缺失 / 方向反 / 只取消不说话 / 决策表把成功也判成取消），"
        u"且四臂 `还原干净=yes`。\n"
        u"- **U-1319：M188 的第一版「反向」变异**编译不过 —— `guard failure == nil else` 之后还要读 "
        u"`failure.message`，可选型没解开 ⇒ `BROKEN-MUTATION`。**这是刀坏，不是判据没牙**："
        u"改成「`guard let failure else { return .cancel(...) }`（成功也判取消）」之后能编译，"
        u"现读 CAUGHT、红在 `testCopyThenPasteTruthTable` 与 `testCopySuccessIsNotBlockedByTheNewGate` 两格。"
        u"同时把 r40 表接上 `knife_guard`（落刀前备份、启动时恢复、600s 进程组超时）。\n"
        u"- **U-1320：r42 的两把针从「注释 + 动作」缩成「动作那一行」。** 旧针把三段解释性注释一起钉住，"
        u"注释后来改写过 ⇒ 针烂，而真正的对象（`.animation(... value: exportMessage == nil)`）一直活着。"
        u"改针后 `M194/M195 CAUGHT`，红在 `MotionDriverTests testEveryReceiptLineCallSiteIsDriven`。"
        u"⇒ 判据的针只许钉**被驱动的对象**，注释不是对象（D-366）。\n"
        u"- **U-1321：rot 27→21。** 六把（r40 ×4、r42 ×2）重钉后 `HIDDEN_ARMS 表=222 可判=805 rot=21 … 处置=ok`，"
        u"`ROT_CEILING` 同笔 27→21（`:17` 那条「两个方向都有牙」的红话仍是硬的）。"
        u"剩下 21 条里 r49 的 M244 这次**没有**重钉：它钉的是「目录快照永远是空」，而那个快照探针已被重写、"
        u"旧针在盘上没有对应对象 —— 要重钉得先给新探针写一支同义的坏法，留到下一批。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 一张表一条命令；超时由同格的合成样本兑现，不靠注释。 |\n\n"
            u"均分 = 91/105 ≈ 13.0/15（87）。")
    r375 = (
        u"\n\n## Round 375 · R378（第 377 轮 · 2026-10-26）：367 第三批 —— 七把腐烂针重钉，rot 27→21"
        u"（产品 0 文件）\n\n"
        u"r40 的四把针跟着 `decide(failure:)` 的新签名重钉（四臂 CAUGHT，含一支旧刀编译不过被判成刀坏的记录）；"
        u"r42 的两把针从「注释 + 动作」缩到「动作那一行」（两臂 CAUGHT）。`HIDDEN_ARMS … rot=21 处置=ok`，"
        u"`ROT_CEILING` 同笔 27→21。r49 的 M244 明确没动：旧针的对象（目录快照）已被重写，"
        u"要先给新探针写同义坏法才能重钉。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 六臂 CAUGHT 且各自红在主张的那一格；M188 编译不过时记 BROKEN 不记 CAUGHT。 |\n"
        u"| 假绿防御 | 15/15 | rot 降了就把上界同笔降；「没重钉」的 M244 写明理由，不冒充已修。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在「针别钉注释」与刀的可编译性这两条判据卫生上。 |\n"
        u"| 台账一致性 | 14/15 | U-1318…U-1321、D-366、367 追记、上界同笔；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | M244 与其余 20 条仍腐烂，写清「为什么这次没动它」。 |\n"
        u"| 可复核性 | 15/15 | 两张表各一条命令；rot/上界由 `hidden_arms.py` 现读。 |\n\n"
        u"均分 = 91/105 ≈ 13.0/15（87）。"
    )
    it = once(it, tail, tail + r375)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    证人 M1010（emit 写盘前 sleep 30s）：现读 `CAUGHT 红得对=True 命中=['READOUT_CHANNEL_BLOCKED'] "
               u"还原干净=True`、复跑 `ESCAPED`、表 `EXIT=0`。与 M278 的分界：M278 是「写不进去」，"
               u"M1010 是「写之前就不返回」——前者读文件那格红，后者只有 deadline 能救。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R378）：r40 四把（M185…M188）跟着 `CopyThenPaste.decide(failure:)` 的新签名重钉、"
              u"r42 两把（M194/M195）从「注释 + 动作」缩到**动作那一行**重钉 —— 六臂全 CAUGHT，"
              u"rot **27→21**，`ROT_CEILING` 同笔降到 21，`处置=ok`。\n"
              u"    M188 的第一版反向变异编译不过（`guard failure == nil else` 之后仍读可选型的 `.message`）⇒ "
              u"记 BROKEN-MUTATION；改成「成功也判取消」后可编译且 CAUGHT。r40 表同笔接上 knife_guard。\n"
              u"    **没动的**：r49 的 M244（钉「目录快照永远是空」，而快照探针已被重写、旧针没有对象）"
              u"与其余 20 条腐烂针 —— 下一批先给新探针写同义坏法再重钉，不许拿一把空刀冒充覆盖面。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：凡是判据里等别的线程/等盘/等锁，一律「后台执行 + 有界等待 + 超时具名」；"
               u"超时那一路只许交回 nil（不许半个结果），并配一条同格的合成正对照证明截止会触发。\n")
    d_new = (dc_tail + u"\n"
             u"### D-366（378）变异针只钉**被驱动的对象**，不钉注释\n\n"
             u"R378 现读：r42 的 M194/M195 两把针把三段解释性注释一起钉住，注释后来改写过 ⇒ 针全烂，"
             u"而它们真正要打的那一行 `.animation(... value: exportMessage == nil)` 一直活着。"
             u"同一批里 r40 的针也带着旧签名与旧注释，一起腐烂。\n"
             u"**Why**：注释是**关于对象的话**，不是对象；针跟着话走，就会把「注释被改写」误报成「判据腐烂」，"
             u"反过来也会让真正该钉的那一行悄悄换掉而针仍然命中（如果注释没变）。\n"
             u"**How to apply**：针尽量取一行可执行语句 / 一个签名块；注释不进针。"
             u"重钉时先问「我要打的是哪一行代码」，再从盘上抄那一行；发现腐烂时先分清"
             u"「行为变了」还是「注释/签名变了」。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 367 第三批：r40/r42 六把腐烂针重钉（六臂 CAUGHT），rot 27→21、上界同笔降；M188 旧刀编译不过记刀坏（R378 / U-1318…U-1321 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R374，375 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R375，376 节自评）")
    rp = once(rp, u"U-31 … U-1317（R377 现读抬到最新一节）", u"U-31 … U-1321（R378 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **22**", u"产品面连续零改动轮数 = **23**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R377 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R378 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R377 这一段（R337 补写；R341 续到 341、R377 续到 377 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R378 这一段（R337 补写；R341 续到 341、R378 续到 378 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R377 续（判据账）**：434 结案 —— 通道「emit 两行 + 读回」进 5s 有界等待，超时具名 "
                u"`READOUT_CHANNEL_BLOCKED`；M1010（写前 sleep 30s）`CAUGHT`；\n"
                u"  r56 十把刀首次进针预检（认出五元组 + `.yml`），`covered=118 arms=386 bad=0`，缺口 75/423→74/414。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R378 续（判据账）**：367 第三批 —— r40 四把随 `decide(failure:)` 重钉、r42 两把缩到动作那一行，"
              u"六臂 `CAUGHT`，rot 27→21、上界同笔降；\n"
              u"  M188 旧刀编译不过记 `BROKEN-MUTATION`（刀坏），换写法后 CAUGHT；r49 M244 明确留待下一批。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r377_head = (u"## R377 状态（2026-10-26 · 本地 · 第 376 轮 / Round 374）：434 结案 —— 读数通道 5s 有界等待"
                 u"（M1010 CAUGHT）；r56 十把刀第一次进针预检（产品 0 文件，判据账）")
    state = (
        u"## R378 状态（2026-10-26 · 本地 · 第 377 轮 / Round 375）：367 第三批 —— 七把腐烂针重钉、rot 27→21；"
        u"M188 旧刀编译不过判成刀坏（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R378 / 第 377 轮 / Round 375）：r40 四把针跟着 "
        u"`CopyThenPaste.decide(failure:)` 重钉、r42 两把从「注释 + 动作」缩到动作那一行 —— 六臂全 CAUGHT、"
        u"还原干净；M188 第一版反向变异编译不过记 `BROKEN-MUTATION`，改「成功也判取消」后 CAUGHT；"
        u"`HIDDEN_ARMS 表=222 可判=805 rot=21 … 处置=ok`，`ROT_CEILING` 同笔 27→21；"
        u"全量沿用 R377（本轮没动 Swift）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`1ff9d11`（R376）与 `187ffaf`/`2ffc6d0`（R375）已 success；"
        u"本轮 `a84cb73 ↔ 40213511314`（in_progress、前面=0）；只登记不轮询。\n"
        u"② r40 四臂重钉 + 接 knife_guard（备份 / 启动恢复 / 600s 进程组超时）→ 4/4 CAUGHT。\n"
        u"③ M188 旧写法编译不过 ⇒ 记刀坏并换写法（成功也判取消）→ CAUGHT（真值表 + 成功不许被挡两格）。\n"
        u"④ r42 两臂缩针到动作那一行 → 2/2 CAUGHT；rot 27→21、上界同笔降；r49 M244 明确留待下一批。\n\n"
        u"验证读数（现读）：`M185…M188 CAUGHT`（各红在主张的两格）、`M194/M195 CAUGHT`"
        u"（`MotionDriverTests testEveryReceiptLineCallSiteIsDriven`）；六臂 `还原干净=yes`；"
        u"`HIDDEN_ARMS 表=222 可判=805 rot=21 抽不出=6 已声明表=6 已声明死针=0 上界 rot=21 … 处置=ok`；"
        u"预检 `tables=135 covered=118 arms=386 bad=0`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R377 日志）；"
        u"电池 `Ran @RAN@（skipped=@SK@）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；"
        u"产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 377` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R377 日志）；"
        u"③ r49 M244 与其余 20 条腐烂针**没重钉**（旧针的对象已被重写，要先给新探针写同义坏法）。\n\n"
        u"下一轮（R379）的靶：⓪ 读队列（含 `a84cb73` 的结论）；① r49 M244 的新同义坏法 + 再钉一批 rot；"
        u"② 回到产品动效面点一个真实位（连续判据账之后优先）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(streak)))
    st = once(st, r377_head, state + r377_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R378_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d"
          % (n, skipped, failures, ran, py_skipped, streak))


if __name__ == u"__main__":
    main()
