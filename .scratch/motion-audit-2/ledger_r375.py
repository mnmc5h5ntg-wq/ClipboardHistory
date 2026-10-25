#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R375 的七本台账（第 374 轮 / Round 372）：433 第一半 —— 崩溃安全还原 + 硬超时。"""
import io
import os
import re

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r374_full.log"
PY = u"/tmp/r375_py.log"


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
    head = (u"## 第 373 轮（R374 · 2026-10-25 · U-1303…U-1306）：读数通道守卫补上「来源」证人；r56 三根针重钉，"
            u"刀腿 NOT-RUN（U-1303…U-1306 · 产品 0 文件，判据账）")
    section = (
        u"## 第 374 轮（R375 · 2026-10-26 · U-1307…U-1309）：433 第一半 —— 崩溃安全还原 + 硬超时；"
        u"M279/M281 CAUGHT、M278 以 180s 超时具名（U-1307…U-1309 · 产品 0 文件，判据账）\n\n"
        u"- **U-1307：`knife_guard.py` 落地。** `backup` / `restore_if_stale` / `clear_backup` 负责「落刀前备份、"
        u"表启动时把没被还原的那一刀恢复」；`run` 用 POSIX 进程组 + 硬超时，超时只杀整组。"
        u"`scripts/tests/test_knife_guard.py` **6 格**（含 `sleep 5` 对 1s 超时必须 timed_out）。\n"
        u"- **U-1308：r56 接线 + 两处读数判法修正。** 预检前先 `restore_if_stale`（被杀过就打印 "
        u"`KNIFE_RESTORED_FROM_BACKUP`）；每臂落刀前备份、还原干净后清备份；swift 那一腿 180s 超时记 "
        u"`NOT_RUN_TIMEOUT`；CI 那一侧不再读「最后一行」，只认 unittest 的汇总行（自检在 `OK` 之后还会打样张行，"
        u"读末行会把 OK 读成 CAUGHT —— 这正是它上一轮预检失败的原因）。\n"
        u"- **U-1309：三臂现读。** `M279 CAUGHT`（红在 `testMotionReadingsUseTheFileChannel`，命中「不在末尾两格」）、"
        u"`M281 CAUGHT`（命中「扫描函数在合成样本上抓不到」）、`M278 NOT_RUN_TIMEOUT`（180s 到点被杀；"
        u"R374 它是 6 分 29 秒无人收尸）——三臂 `还原干净=yes`，复跑守卫 `ESCAPED`。"
        u"⇒ M278 的挂起**可复现**，下一格用 `sample` 抓栈；rot 不动（27，M278 的针本来就活着）。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 交付诚实性 | 15/15 | 挂起与残留都照实写，不写成「已修好」。 |\n"
            u"| 可复核性 | 15/15 | 守卫一条命令；挂起症状（6:29 vs 0.029s）与两次还原都有原文。 |\n\n"
            u"均分 = 88/105 ≈ 12.6/15（84）。")
    r372 = (
        u"\n\n## Round 372 · R375（第 374 轮 · 2026-10-26）：433 第一半 —— 崩溃安全还原 + 硬超时（产品 0 文件）\n\n"
        u"`knife_guard.py` + 6 格测试落地；r56 接上「备份 / 恢复 / 进程组超时」，CI 判词改读 unittest 汇总行。"
        u"三臂现读：`M279 CAUGHT`（不在末尾两格）、`M281 CAUGHT`（扫描函数在合成样本上抓不到）、"
        u"`M278 NOT_RUN_TIMEOUT`（180s 到点被杀，R374 是 6:29 挂死）——三臂还原干净、复跑守卫绿。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 两臂 CAUGHT（红线原文在三臂输出里）；M278 有具名超时。 |\n"
        u"| 假绿防御 | 15/15 | 超时不算 CAUGHT；CI 判词不再读末行；备份在表启动时自证。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在刀的运行面（不再挂死、不再留残留）。 |\n"
        u"| 台账一致性 | 13/15 | U-1307…U-1309、433/367 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | M278 只记超时与「可复现」，成因留给下一格，不猜。 |\n"
        u"| 可复核性 | 15/15 | 6 格测试 + 三臂一条命令；超时由 `sleep 5` 正对照兑现。 |\n\n"
        u"均分 = 90/105 ≈ 12.9/15（86）。"
    )
    it = once(it, tail, tail + r372)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    修法（下一轮）：① 刀跑之前先把目标文件备份到 `.scratch` 并在**表启动时**校验/恢复未完成的落刀；"
               u"② 给 swift 那一腿加一个硬超时（例如 180s，超时记 `NOT_RUN 超时` 而不是挂住）；"
               u"③ 再查 M278 为什么会挂 —— 先怀疑 `emit` 提前 return 后守卫的读文件分支与 `FileHandle` 生命周期。")
    bl_add = (bl_tail + u"\n\n"
              u"433 追记（R375 · 第一半落地）：`knife_guard.py`（备份 / 启动时恢复 / 进程组硬超时）+ 6 格测试；"
              u"r56 已接线，CI 判词改读 unittest 汇总行。\n"
              u"    三臂现读：`M279 CAUGHT`、`M281 CAUGHT`、`M278 NOT_RUN_TIMEOUT`（180s 到点；R374 是 6:29 挂死）——"
              u"三臂 `还原干净=yes`、复跑守卫 `ESCAPED`。\n"
              u"    **M278 可复现**：不是被杀的管道造成的假象。下一格：落刀后 30s 用 `sample <pid>` 抓栈，"
              u"判定挂在 `String(contentsOf:)` / `FileHandle` / 退出路径哪一处。\n\n"
              u"367 追记（R375）：M279/M281 两臂 CAUGHT（「不在末尾两格」/「扫描函数在合成样本上抓不到」）；"
              u"M278 记 NOT_RUN_TIMEOUT（刀没验成，针本来就活着，rot 仍 27）。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 433 第一半：刀的崩溃安全还原 + 进程组硬超时；r56 两臂 CAUGHT、M278 以 180s 超时具名（R375 / U-1307…U-1309 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R371，372 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R372，373 节自评）")
    rp = once(rp, u"U-31 … U-1306（R374 现读抬到最新一节）", u"U-31 … U-1309（R375 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **19**", u"产品面连续零改动轮数 = **20**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R374 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R375 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R374 这一段（R337 补写；R341 续到 341、R374 续到 374 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R375 这一段（R337 补写；R341 续到 341、R375 续到 375 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R374 续（判据账）**：读数通道守卫补上「来源」证人（`strayLines(in:)` + 合成样本）；"
                u"r56 三根针重钉、CI 预检改 `Ran \\d+ tests`；\n"
                u"  刀腿 **NOT-RUN**（M278 臂 xctest 挂 6:29、两次强杀各留一行 MUTANT 已还原）⇒ rot 保持 29，开 433。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R375 续（判据账）**：433 第一半 —— `knife_guard.py`（备份/恢复/进程组超时）+ 6 格测试；"
              u"r56 两臂 `CAUGHT`（M279/M281）、\n"
              u"  M278 `NOT_RUN_TIMEOUT`（180s，R374 是 6:29）；三臂还原干净、复跑守卫绿。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r374_head = (u"## R374 状态（2026-10-25 · 本地 · 第 373 轮 / Round 371）：读数通道守卫补上「来源」证人；"
                 u"r56 三根针重钉，刀腿 NOT-RUN（产品 0 文件，判据账）")
    state = (
        u"## R375 状态（2026-10-26 · 本地 · 第 374 轮 / Round 372）：433 第一半 —— 崩溃安全还原 + 硬超时；"
        u"M279/M281 CAUGHT、M278 以 180s 超时具名（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R375 / 第 374 轮 / Round 372）：`knife_guard.py` + 6 格测试；"
        u"r56 接线（启动恢复、逐臂备份、180s 进程组超时、CI 判词读汇总行）；"
        u"三臂 `M279 CAUGHT / M281 CAUGHT / M278 NOT_RUN_TIMEOUT`，三臂还原干净、复跑守卫 ESCAPED；"
        u"全量沿用 R374（本轮没动 Swift）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`357a763`（R374）已 success；`a17bc6a`（R373 追记）success；只登记不轮询。\n"
        u"② 433 第一半：备份/启动恢复/进程组超时 + 6 格正对照（`sleep 5` 对 1s 超时）。\n"
        u"③ r56 接线：预检前恢复、逐臂备份、`NOT_RUN_TIMEOUT`、CI 判词读汇总行（不读末行）。\n"
        u"④ 三臂现读；M278 挂起**可复现**（180s），下一格用 `sample` 抓栈。\n\n"
        u"验证读数（现读）：`M279 CAUGHT`（命中「不在末尾两格」）、`M281 CAUGHT`（命中「扫描函数在合成样本上抓不到」）、"
        u"`M278 NOT_RUN_TIMEOUT`；三臂 `还原干净=yes`、复跑 `ESCAPED`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R374 日志）；"
        u"脚本电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **20** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 374` 现读）。\n\n"
        u"NOT-RUN（分开写）：① M278 的 CAUGHT 仍没有读数（可复现超时）；② 全量卷没重跑（本轮没动 Swift）；"
        u"③ 真机腿没跑。\n\n"
        u"下一轮（R376）的靶：⓪ 读队列；① 433 第二半：M278 落刀后 30s `sample <pid>` 抓栈，定位挂点；"
        u"② 再回到 367（rot 27）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)))
    st = once(st, r374_head, state + r374_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R375_LEDGERS_OK full=%d/%d/%d battery=%d(%d)" % (n, skipped, failures, ran, py_skipped))


if __name__ == u"__main__":
    main()
