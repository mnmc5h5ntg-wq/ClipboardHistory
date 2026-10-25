#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R374 的七本台账（第 373 轮 / Round 371）：读数通道守卫的来源证人 + r56 重钉（刀腿 NOT-RUN）。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r374_full.log"
PY = u"/tmp/r374_py.log"


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
    head = (u"## 第 372 轮（R373 · 2026-10-25 · U-1300…U-1302）：367 第三批 —— r55 的 M271/M272 重钉（参数名改名），"
            u"rot 31→29（U-1300…U-1302 · 产品 0 文件，判据账）")
    section = (
        u"## 第 373 轮（R374 · 2026-10-25 · U-1303…U-1306）：读数通道守卫补上「来源」证人；r56 三根针重钉，"
        u"刀腿 NOT-RUN（U-1303…U-1306 · 产品 0 文件，判据账）\n\n"
        u"- **U-1303：`testMotionReadingsUseTheFileChannel` 的扫描来源第一次有证人。** 旧形状只验「谓词抓不抓得到」"
        u"（四条合成行、应抓 3 条），而 `strays` 那一边可以被改成恒空、谓词照样过 —— R56 的 M281「扫描列表清空」"
        u"正是这种坏法。现在把扫描提成 `strayLines(in:)`，**同一函数**再喂一段已知有一条游离读数的合成源码，"
        u"必须恰好抓到 1 条；真源码走同一个函数。守卫单跑 `passed (0.029 seconds)`。\n"
        u"- **U-1304：r56 三根针按今天的实现重钉 + CI 预检的写法修掉。** M278 搬 `CaptureReadings.emit(_:to:)`、"
        u"M279 搬 `appendLocked` 的首次整份重写分支、M281 换成清空 `strayLines` 的来源；"
        u"CI 那一侧把写死的 `\"Ran 1 test\"` 改成 `Ran \\d+ tests` —— 自检从 1 格长到 5 格之后，"
        u"整张表在预检就报 `BROKEN-MUTATION`（预检先死）。修后两路预检都 `OK`"
        u"（`预检 OK MotionFilmstripTests.testMotionReadingsUseTheFileChannel`、`预检 OK ci_report_selftest`）。\n"
        u"- **U-1305：刀腿 NOT-RUN，rot 不降。** M278 臂上 `xctest` 跑到 **6 分 29 秒**仍未结束"
        u"（同一个守卫单独跑 0.029 秒），两次都被强杀；强杀绕过 `finally`，两次都在 `CaptureReadings.swift` "
        u"留下 `return   // MUTANT` 一行 —— 都在提交前由 `git diff` 发现并还原，**没有进任何提交**。"
        u"因此 M278/M279/M281 的 CAUGHT **没有读数**，另开 BACKLOG 433。\n"
        u"- **U-1306：rot 29→27 是**静态事实**，不是「刀被验过了」。** 三根针重钉后都能命中 ⇒ 盘点器现读 `rot=27`、"
        u"上界同笔降到 27（这一格数的是**针活没活**）；三把刀的 CAUGHT 仍记 NOT-RUN —— 两件事分开记。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 改名归因写成读数；上界没有留在 31。 |\n"
            u"| 可复核性 | 15/15 | 一条命令复跑两臂；`hidden_arms.py` 一行看 rot 与上界。 |\n\n"
            u"均分 = 89/105 ≈ 12.7/15（85）。")
    r371 = (
        u"\n\n## Round 371 · R374（第 373 轮 · 2026-10-25）：读数通道守卫补上「来源」证人；r56 重钉，刀腿 NOT-RUN（产品 0 文件）\n\n"
        u"`strayLines(in:)` 让扫描的来源第一次有正对照（同一函数喂合成样本，必须抓到 1 条）；守卫 0.029 秒通过。"
        u"r56 的三根针按今天的实现重钉、CI 预检的 `Ran 1 test` 改成 `Ran \\d+ tests`（两路预检都 OK），"
        u"但 M278 臂上 xctest 挂到 6 分 29 秒，两次被强杀、两次留下 MUTANT 行（都还原、未提交）——"
        u"刀腿记 NOT-RUN，rot 保持 29。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 13/15 | 来源证人落地且守卫绿；三根针的 CAUGHT 缺读数（NOT-RUN）。 |\n"
        u"| 假绿防御 | 15/15 | 刀腿没跑就不降 rot；两次残留 MUTANT 都在提交前抓出。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在守卫的证人面。 |\n"
        u"| 台账一致性 | 13/15 | U-1303…U-1306、433 开单；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | 挂起与残留都照实写，不写成「已修好」。 |\n"
        u"| 可复核性 | 15/15 | 守卫一条命令；挂起症状（6:29 vs 0.029s）与两次还原都有原文。 |\n\n"
        u"均分 = 88/105 ≈ 12.6/15（84）。"
    )
    it = once(it, tail, tail + r371)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    重钉后两臂各 CAUGHT（真值表「unknown」/ 接线守卫「只接了 0 次归因」），`ROT_CEILING` 同笔 **31→29**："
               u"现读 `HIDDEN_ARMS 表=222 可判=804 rot=29 抽不出=6 已声明表=6 已声明死针=0 上界 rot=29 … 处置=ok`。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R374）：`mutate_r56_readings_channel.py` 的 M278/M279/M281 按今天的实现重钉"
              u"（CaptureReadings.emit / appendLocked / strayLines），CI 预检的 `\"Ran 1 test\"` 改成 `Ran \\d+ tests`；"
              u"两路预检 OK。\n"
              u"    **刀腿 NOT-RUN**：M278 臂上 xctest 6 分 29 秒未结束（同一守卫单独 0.029 秒），两次强杀、两次残留 MUTANT（已还原）。\n"
              u"    rot **29→27** 是针活了的静态事实，`ROT_CEILING` 同笔降到 27，现读 `处置=ok` —— 它不等于三把刀都被验过。\n\n"
              u"**433. 刀在 M278 臂上挂住 xctest；且 SIGKILL 绕过 `finally` 留下 MUTANT 行**（R374 开）\n"
              u"    现场：`mutate_r56_readings_channel.py M278` 让 `CaptureReadings.emit` 提前 return；"
              u"守卫本应 0.029 秒内红，实际 xctest 跑到 6:29 仍未结束，第一次 10 分钟包装超时后还出现「管道读者先死 ⇒ "
              u"xctest 写 stdout 阻塞」的二次挂起。\n"
              u"    第二个现场：强杀后 `CaptureReadings.swift` 两次留下 `return   // MUTANT: 只 stdout，不落盘` —— "
              u"`finally` 不执行。两次都由 `git diff` 在提交前发现并还原。\n"
              u"    修法（下一轮）：① 刀跑之前先把目标文件备份到 `.scratch` 并在**表启动时**校验/恢复未完成的落刀；"
              u"② 给 swift 那一腿加一个硬超时（例如 180s，超时记 `NOT_RUN 超时` 而不是挂住）；"
              u"③ 再查 M278 为什么会挂 —— 先怀疑 `emit` 提前 return 后守卫的读文件分支与 `FileHandle` 生命周期。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 读数通道守卫补上「来源」证人（同一函数喂合成样本）；r56 三根针重钉 + CI 预检写法修掉，刀腿 NOT-RUN 并开 433"
                u"（R374 / U-1303…U-1306 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R370，371 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R372，373 节自评）")
    rp = once(rp, u"U-31 … U-1302（R373 现读抬到最新一节）", u"U-31 … U-1306（R374 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **18**", u"产品面连续零改动轮数 = **19**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R373 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R374 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R373 这一段（R337 补写；R341 续到 341、R373 续到 373 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R374 这一段（R337 补写；R341 续到 341、R374 续到 374 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R373 续（判据账）**：367 第三批 —— r55 的 M271/M272 随参数改名重钉，两臂各 CAUGHT；"
                u"`ROT_CEILING` 同笔 31→29。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R374 续（判据账）**：读数通道守卫补上「来源」证人（`strayLines(in:)` + 合成样本）；"
              u"r56 三根针重钉、CI 预检改 `Ran \\d+ tests`；\n"
              u"  刀腿 **NOT-RUN**（M278 臂 xctest 挂 6:29、两次强杀各留一行 MUTANT 已还原）⇒ rot 保持 29，开 433。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r373_head = (u"## R373 状态（2026-10-25 · 本地 · 第 372 轮 / Round 370）：367 第三批 —— r55 的 M271/M272 重钉（参数名改名），"
                 u"rot 31→29（产品 0 文件，判据账）")
    state = (
        u"## R374 状态（2026-10-25 · 本地 · 第 373 轮 / Round 371）：读数通道守卫补上「来源」证人；"
        u"r56 三根针重钉，刀腿 NOT-RUN（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-25（本地 · R374 / 第 373 轮 / Round 371）：`strayLines(in:)` + 合成样本正对照落地，"
        u"守卫 0.029 秒通过；r56 的 M278/M279/M281 重钉、CI 预检 `Ran 1 test` → `Ran \\d+ tests`，两路预检 OK；"
        u"刀腿 NOT-RUN（M278 臂 xctest 挂 6:29、两次强杀、两次残留 MUTANT 已还原）；"
        u"全量 @N@ 格 0 失败、电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c` 仍在队里；只登记不轮询。\n"
        u"② 守卫洞：扫描来源提成 `strayLines(in:)`，同一函数喂合成样本必须抓到 1 条。\n"
        u"③ r56 重钉（M278→CaptureReadings.emit、M279→appendLocked、M281→strayLines）+ CI 预检写法修掉。\n"
        u"④ 刀腿挂起 → NOT-RUN；rot 29→27（针活了）且上界同笔降；开 433（崩溃安全还原 + swift 腿硬超时 + M278 挂起成因）。\n\n"
        u"验证读数（现读）：`testMotionReadingsUseTheFileChannel passed (0.029 seconds)`；"
        u"`预检 OK MotionFilmstripTests.testMotionReadingsUseTheFileChannel`、`预检 OK ci_report_selftest`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **19** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 373` 现读）；"
        u"`HIDDEN_ARMS 表=222 可判=804 rot=27 抽不出=6 已声明表=6 已声明死针=0 上界 rot=27 … 处置=ok`。\n\n"
        u"NOT-RUN（分开写）：① M278/M279/M281 的 CAUGHT 没有读数（M278 臂挂起，两次强杀）—— rot 不降；"
        u"② 真机腿没跑。\n\n"
        u"下一轮（R375）的靶：⓪ 读队列五跑；① 先做 433 的崩溃安全还原与硬超时，再重跑 r56 三臂；"
        u"② 之后才谈 367 的下一根。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r373_head, state + r373_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R374_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
