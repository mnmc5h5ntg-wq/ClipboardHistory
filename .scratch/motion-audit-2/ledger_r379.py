#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R379 的七本台账（第 378 轮 / Round 376）：r56 十臂全表第一次跑全。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r377_full.log"
PY = u"/tmp/r378b_py.log"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), u"w", encoding=u"utf-8").write(text)


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, u"锚点命中 %d 次：%s" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, replacement)


def full_counts():
    t = io.open(FULL, encoding=u"utf-8", errors=u"replace").read()
    assert u"Test Suite 'ClipboardHistoryPackageTests.xctest' passed" in t
    m = re.findall(r"Executed (\d+) tests?, with (\d+) tests? skipped and (\d+) failures?", t)
    assert m
    return tuple(int(x) for x in m[-1])


def battery_counts():
    t = io.open(PY, encoding=u"utf-8", errors=u"replace").read()
    m = re.findall(r"^Ran (\d+) tests? in", t, re.M)
    assert m and re.search(r"^OK( \(skipped=\d+\))?$", t, re.M)
    sk = re.findall(r"OK \(skipped=(\d+)\)", t)
    return int(m[-1]), int(sk[-1]) if sk else 0


def product_streak():
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"378"],
                                  cwd=ROOT).decode(u"utf-8")
    m = re.search(r"streak=(\d+)", out)
    assert m, out
    return int(m.group(1))


def main():
    n, skipped, failures = full_counts()
    ran, py_skipped = battery_counts()
    streak = product_streak()
    assert failures == 0
    print(u"PARSED full=%d/%d/%d battery=%d(%d) streak=%d" % (n, skipped, failures, ran, py_skipped, streak))

    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 377 轮（R378 · 2026-10-26 · U-1318…U-1321）：367 第三批 —— 七把腐烂针重钉，rot 27→21；"
            u"M188 的旧刀编译不过被当场判成刀坏（U-1318…U-1321 · 产品 0 文件，判据账）\n")
    section = (
        u"## 第 378 轮（R379 · 2026-10-26 · U-1322…U-1324）：r56 十臂全表第一次跑全（10/10 CAUGHT）；"
        u"M244 的重钉尝试 ESCAPED 并撤回（U-1322…U-1324 · 产品 0 文件，判据账）\n\n"
        u"- **U-1322：r56 全表 10/10 CAUGHT。** 这张表过去从没一次跑全：R374 只跑两臂、R375 三臂、R376/R377 各一臂。"
        u"本轮现读 `M277/M278/M279/M280/M281` 红在 `testMotionReadingsUseTheFileChannel`（分别命中「只走 stdout」"
        u"「文件里没有这一遍的 marker」「不在末尾两格」「CI 那一步找不到它」「扫描函数在合成样本上抓不到」），"
        u"`M282` 命中「夹具替换没有落地」（红在 `[]`，CI 自检样张那种有效红）、"
        u"`M283/M284` 红在两个恢复场景、`M285` 红在 `partial_stdout_loss_recovers_resolve`、"
        u"`M1010` 命中 `READOUT_CHANNEL_BLOCKED`；十臂 `还原干净=True`、表尾复跑 `ESCAPED`、`EXIT=0`。\n"
        u"- **U-1323：M244 的重钉尝试 ESCAPED，刀没收。** 旧针钉的是「目录快照永远是空」，而那个探针已被重写、"
        u"旧针没有对象；同义坏法改成「`HistoryStore.persist()` 里不调 `persistence.save(entries)`」，"
        u"结果对照组（放开闸门后 `history.json` 必须出现）**仍然绿** ⇒ `add` 的落盘还有第二条路（本轮没定位到）。"
        u"表已还原、rot 仍 21、`处置=ok`；这笔写在 BACKLOG 367 的追记里，下一批先找那条路。\n"
        u"- **U-1324：全表跑全才把 M282 的形状照出来。** 它的「红在 []」不是漏红：CI 那四把刀证的是"
        u"「夹具替换有没有落地 / 恢复场景跑不跑得动」，命中在自检样张而不在 XCTest 失败行。"
        u"过去单臂跑时这四把的读数从没和 Swift 那六把并排出现过，容易把 `红在 []` 读成「没红」。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 两张表各一条命令；rot/上界由 `hidden_arms.py` 现读。 |\n\n"
            u"均分 = 91/105 ≈ 13.0/15（87）。")
    r376 = (
        u"\n\n## Round 376 · R379（第 378 轮 · 2026-10-26）：r56 十臂全表第一次跑全（10/10 CAUGHT）"
        u"（产品 0 文件）\n\n"
        u"十臂一次跑全：Swift 五臂各自红在期望的那句话上，CI 四臂（M282–M285）红在自检样张与两个恢复场景，"
        u"M1010 命中 `READOUT_CHANNEL_BLOCKED`；十臂还原干净、复跑 ESCAPED、EXIT=0。"
        u"同一轮里 M244 的重钉尝试 ESCAPED（拿掉 `persist()` 的 save 后对照组仍绿 ⇒ `add` 还有第二条落盘路），"
        u"刀撤回、rot 仍 21。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品改动；画面沿用 R356 帧。 |\n"
        u"| 判据有效性 | 15/15 | 10/10 CAUGHT，每臂命中各自那句话；全表一次跑全，不是抽样。 |\n"
        u"| 假绿防御 | 15/15 | ESCAPED 的 M244 不记 CAUGHT、不进表尾绿账；`红在 []` 写明是哪种有效红。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；推进在「整表验证」这条覆盖面上。 |\n"
        u"| 台账一致性 | 14/15 | U-1322…U-1324、D-367、367 追记；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | M244 的失败尝试原样写，不把「跑过」写成「修好」。 |\n"
        u"| 可复核性 | 15/15 | 一条命令跑全表；十臂读数与 EXIT 都在日志里。 |\n\n"
        u"均分 = 91/105 ≈ 13.0/15（87）。"
    )
    it = once(it, tail, tail + r376)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    R378 追记：M244 的重钉**试过一次，ESCAPED** —— 同义坏法改成「`HistoryStore.persist()` 里不调 "
               u"`persistence.save(entries)`」，其余不变，对照组（放开闸门后 `history.json` 必须出现）**仍然绿** ⇒ "
               u"`add` 的落盘还有第二条路（我没定位到）。刀没收，rot 仍 21；下一批先找出那条路再钉，"
               u"不许把一把 ESCAPED 的刀塞回表里当已修。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R379）：r56 全表十臂第一次一次跑全 —— `10/10 CAUGHT`、十臂还原干净、复跑 `ESCAPED`、`EXIT=0`；"
              u"M282 的「红在 []」现读为 **CI 自检样张那种有效红**（命中「夹具替换没有落地」），与另外九臂的 XCTest 红分开记。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：针尽量取一行可执行语句 / 一个签名块；注释不进针。"
               u"重钉时先问「我要打的是哪一行代码」，再从盘上抄那一行；发现腐烂时先分清"
               u"「行为变了」还是「注释/签名变了」。\n")
    d_new = (dc_tail + u"\n"
             u"### D-367（379）一张表要整表跑全；单臂绿不算这张表被验过\n\n"
             u"R379 现读：r56 有十臂，过去四轮分别只跑过 2 / 3 / 1 / 1 臂 —— 每一轮都有一两朵 CAUGHT，"
             u"账上看起来「这张表在管」，而另外几臂的期望文案与还原路径从没在同一跑里对过。"
             u"本轮一次跑全，才把 M282 的「红在 []」与其余九臂的 XCTest 红分开看清。\n"
             u"**Why**：单臂 CAUGHT 证的是「这一刀被抓到」，不是「这张表还能整表运行」；"
             u"只跑一臂时，别的臂腐烂 / 期望文案过期 / 还原不干净都不会被看见。\n"
             u"**How to apply**：迁移或重钉之后，至少整表跑一遍（含预检与收尾复跑）；"
             u"预算不够整表时，账上写「本轮只跑了第 N 臂」，不许写成「表绿」。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### r56 十臂全表首次跑全（10/10 CAUGHT）；M244 重钉尝试 ESCAPED 并撤回（R379 / U-1322…U-1324 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R375，376 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R376，377 节自评）")
    rp = once(rp, u"U-31 … U-1321（R378 现读抬到最新一节）", u"U-31 … U-1324（R379 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **23**", u"产品面连续零改动轮数 = **24**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R378 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R379 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R378 这一段（R337 补写；R341 续到 341、R378 续到 378 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R379 这一段（R337 补写；R341 续到 341、R379 续到 379 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R378 续（判据账）**：367 第三批 —— r40 四把随 `decide(failure:)` 重钉、r42 两把缩到动作那一行，"
                u"六臂 `CAUGHT`，rot 27→21、上界同笔降；\n"
                u"  M188 旧刀编译不过记 `BROKEN-MUTATION`（刀坏），换写法后 CAUGHT；r49 M244 明确留待下一批。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R379 续（判据账）**：r56 十臂整表首次跑全（10/10 `CAUGHT`、还原干净、复跑 `ESCAPED`）；"
              u"M244 重钉尝试 `ESCAPED` 并撤回（rot 仍 21）。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    st = rd(u"AGENT_STATE.md")
    r378_head = (u"## R378 状态（2026-10-26 · 本地 · 第 377 轮 / Round 375）：367 第三批 —— 七把腐烂针重钉、rot 27→21；"
                 u"M188 旧刀编译不过判成刀坏（产品 0 文件，判据账）")
    state = (
        u"## R379 状态（2026-10-26 · 本地 · 第 378 轮 / Round 376）：r56 十臂全表第一次跑全（10/10 CAUGHT）；"
        u"M244 重钉尝试 ESCAPED 并撤回（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R379 / 第 378 轮 / Round 376）：r56 整表十臂一次跑全 —— "
        u"`M277…M281` 红在守卫各自那句、`M282` 命中「夹具替换没有落地」（`红在 []` 的有效红）、"
        u"`M283/M284` 红在两个恢复场景、`M285` 红在 partial 那一格、`M1010` 命中 `READOUT_CHANNEL_BLOCKED`；"
        u"十臂 `还原干净=True`、复跑 `ESCAPED`、`EXIT=0`；M244 的重钉尝试 ESCAPED（`persist()` 的 save 不是唯一落盘路）已撤回，rot 仍 21；"
        u"全量沿用 R377（本轮没动 Swift）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`a84cb73`（R377）与 `a63dcf5`（R378）已 success、`3ef8c59`（追记）在队；只登记不轮询。\n"
        u"② r56 全表跑全（十臂）：预检两路 OK，10/10 CAUGHT，还原干净，复跑 ESCAPED。\n"
        u"③ M244 的重钉尝试 ESCAPED ⇒ 表还原、刀没收；线索写进 BACKLOG 367 追记。\n"
        u"④ 记下「整表跑全才看得见 M282 那种有效红」（D-367）。\n\n"
        u"验证读数（现读）：`红得不对/未抓到=0  还原不干净=0`、`还原后复跑（Swift 守卫）：ESCAPED`、表 `EXIT=0`；"
        u"`HIDDEN_ARMS … rot=21 … 处置=ok`；预检 `tables=135 covered=118 arms=386 bad=0`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R377 日志）；"
        u"电池 `Ran @RAN@（skipped=@SK@）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；"
        u"产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 378` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R377 日志）；"
        u"③ r56 的 CI 四臂只在自检样张那一层验过（它们证的本来就不是产品像素）；④ 其余 20 条 rot 仍未重钉、M244 未定位。\n\n"
        u"下一轮（R380）的靶：⓪ 读队列（含 `3ef8c59`）；① 定位 `add` 的第二条落盘路（M244）；"
        u"② 回产品动效面点一个真实位（已连续 24 轮零产品改动，这一维必须动）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(streak)))
    st = once(st, r378_head, state + r378_head)
    wr(u"AGENT_STATE.md", st)

    print(u"R379_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d"
          % (n, skipped, failures, ran, py_skipped, streak))


if __name__ == u"__main__":
    main()
