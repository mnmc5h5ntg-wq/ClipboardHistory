#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R386（第 385 轮 / Round 383）的七本台账：最后两根腐烂针重钉，rot 2→0；网络断，push 阻塞。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r385_full.log"
PY = u"/tmp/r386_py.log"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), u"w", encoding=u"utf-8").write(text)


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, u"锚点命中 %d 次：%s" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, replacement)


def counts():
    t = io.open(FULL, encoding=u"utf-8", errors=u"replace").read()
    assert u"Test Suite 'ClipboardHistoryPackageTests.xctest' passed" in t
    m = re.findall(r"Executed (\d+) tests?, with (\d+) tests? skipped and (\d+) failures?", t)
    assert m
    b = io.open(PY, encoding=u"utf-8", errors=u"replace").read()
    ran = re.findall(r"^Ran (\d+) tests? in", b, re.M)
    assert ran and re.search(r"^OK( \(skipped=\d+\))?$", b, re.M), u"电池没有 OK"
    sk = re.findall(r"OK \(skipped=(\d+)\)", b)
    return (int(m[-1][0]), int(m[-1][1]), int(m[-1][2]), int(ran[-1]), int(sk[-1]) if sk else 0)


def streak():
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"385"],
                                  cwd=ROOT).decode(u"utf-8")
    m = re.search(r"streak=(\d+)", out)
    assert m, out
    return int(m.group(1))


def main():
    n, skipped, failures, ran, py_skipped = counts()
    st = streak()
    assert failures == 0
    print(u"PARSED full=%d/%d/%d battery=%d(%d) streak=%d" % (n, skipped, failures, ran, py_skipped, st))

    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 384 轮（R385 · 2026-10-26 · U-1348…U-1351）：两颗「恢复默认」的禁用切换接上 .selection 过渡 + "
            u"源形状守卫；367 再钉 r64 两根，rot 4→2（U-1348…U-1351 · 产品 1 文件，动效主线）\n")
    section = (
        u"## 第 385 轮（R386 · 2026-10-26 · U-1352…U-1354）：最后两根腐烂针重钉，rot 2→0；"
        u"M147 的旧目标被重构掉、同义坏法换成「一条都不判」（U-1352…U-1354 · 产品 0 文件，判据账）\n\n"
        u"- **U-1352：r77 M411 重钉。** 守卫那句已经改成两行（R80 给轴名加了 `lowercased`）⇒ 旧单行针命中 0。"
        u"针改成两行整块后现读 `M411 CAUGHT`（红在 `testEveryTwoStateRulerReadsBothAxes`）；同一次整表跑 9/10，"
        u"**M406 记 NOT-APPLIED**（锚点不在盘上）——新的腐烂针，记进 BACKLOG 367 追记。\n"
        u"- **U-1353：M147 的旧目标**（`… scale: scale, gate: 8)` 那次调用）**已被重构掉**：`inkContrast` 现在没有 "
        u"gate 参数。盘上唯一剩下的 `gate: 8` 属于另一条 tier-profile 探针，把它抬到 250 只会让那条测试 "
        u"**skip**、不会红（实测 ESCAPED）⇒ 同名调用点不等于同一个对象（D-374）。同义坏法换成"
        u"「探针循环取 `prefix(0)`」，judged 停在 0；现读 `M147 CAUGHT`，红在 "
        u"`XCTAssertGreaterThanOrEqual failed: (\"0\") is less than (\"3\") - light 档 18 条说明段探针**一条都没判成**`。\n"
        u"- **U-1354：rot 2→0 且上界同笔降到 0。** `HIDDEN_ARMS 表=227 可判=811 rot=0 抽不出=6 … 处置=ok`。"
        u"两个新发现：① tier-profile 把整列墨 gate 抬高只会走 skip，skip 把「尺坏了」和「机器画不出」压成同形（BACKLOG 435）；"
        u"② M406 的锚点失效（367 追记）。**网络**：GitHub 侧链路断（`api=000` / apple=200），本地领先 4 笔未推，"
        u"`40234023212`/`40234058148` 与 R385 那一跑的结论全部 NOT-RUN（网络），不写成没红。\n\n"
    )
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 帧差分 182/0、M1016/M1017、r64 6/6、预检与清账表都有原文。 |\n\n"
            u"均分 = 99/105 ≈ 14.1/15（94）。")
    r383 = (
        u"\n\n## Round 383 · R386（第 385 轮 · 2026-10-26）：最后两根腐烂针重钉，rot 2→0（产品 0 文件）\n\n"
        u"r77 M411 与 r33 M147 重钉并各自真跑出 CAUGHT；M147 的旧目标（`gate: 8` 那次调用）在重构后已不存在，"
        u"盘上同名 gate 抬到 250 只会 skip ⇒ 换成「探针循环 prefix(0)」，红在 judged=0 那条地板。"
        u"rot 2→0、上界同笔降。网络断（api=000 / apple=200），本地领先 4 笔未推，CI 三跑结论记 NOT-RUN（网络）。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品画面改动；看图沿用 R385 的 182 张端态帧。 |\n"
        u"| 判据有效性 | 15/15 | 两把刀都 CAUGHT 且红在期望消息上；rot 归零有现读。 |\n"
        u"| 假绿防御 | 13/15 | 抓到 skip 会吞掉「尺坏了」这一新洞（BACKLOG 435），但本轮只开单未修。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件（判据账）；过渡过程仍无胶片证人。 |\n"
        u"| 台账一致性 | 14/15 | U-1352…U-1354、D-374、435 开单；CI 未读具名 NOT-RUN。 |\n"
        u"| 交付诚实性 | 15/15 | 网络阻塞、4 笔未推、三跑未读全部照实写，不冒充绿。 |\n"
        u"| 可复核性 | 14/15 | 两条命令各跑一次；红消息原文已抄。 |\n\n"
        u"均分 = 88/105 ≈ 12.6/15（84）。"
    )
    it = once(it, tail, tail + r383)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    bl = rd(u"AGENT_BACKLOG.md")
    bl_tail = (u"    **台账标签更正**：BACKLOG 尾部此前五条「R381 现读」（r49 / r42 / r54 / r53 那批）对应的提交 "
               u"`0264a63`/`e8228a8`/`ef45e65`/`fb641e7`/`9678d9c` 的 subject 都是 **R380** —— 那是 R380 追记批次的标签笔误；"
               u"本节的「R381」属于第 380 轮（Round 378），两批不是同一轮，按提交号区分。")
    bl_add = (bl_tail + u"\n\n"
              u"367 追记（R386）：M411 重钉到两行整块（R80 的 `lowercased`）⇒ CAUGHT；M147 的旧目标（`gate: 8` 调用）"
              u"已被重构成 `inkContrast`（无 gate 参数），盘上同名 gate 抬到 250 只会让 tier-profile **skip** ⇒ "
              u"同义坏法换成「探针循环 `prefix(0)`」⇒ CAUGHT（judged=0）。rot **2→0**，`ROT_CEILING` 同笔降；"
              u"`HIDDEN_ARMS 表=227 可判=811 rot=0 … 处置=ok`。\n"
              u"    **新开**：r77 整表 9/10，**M406 NOT-APPLIED**（锚点不在盘上）——下一批先重钉它。\n"
              u"\n"
              u"**435. tier-profile 的墨 gate 抬高只会 skip：skip 把「尺坏了」和「机器画不出」压成同形**（R386 现读）\n"
              u"    现场：把 `testSettingsCaptionRowTierProfileDiagnostic` 里那次 `inkSideCounts(..., gate: 8)` 抬到 250，"
              u"测试**全绿跳过**（`ROWTIER_NOT_RUN`），不是红。也就是说这条探针的「这台机器画不出」出口没有负半证人："
              u"真的把读数阈值弄坏，也会从同一个出口溜走。\n"
              u"    修法：给 skip 出口加一个**反向**前提——同一张帧上必须存在至少一处能读出的墨（例如页眉或开关标签），"
              u"否则不是「整页平涂」而是「尺坏了」，必须红；并用一支把 gate 抬到 250 的刀作证它红。"
              u"这与 174 / 331 那族「出口要能说不」同源。")
    bl = once(bl, bl_tail, bl_add)
    wr(u"AGENT_BACKLOG.md", bl)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：① 过渡的验收分两格：端态用逐字节帧，过程用胶片/时间读数；只有源守卫时，过程记 "
               u"`NOT-RUN=no-timeline-witness`。② 源守卫要钉**键**，不钉「有 .animation」；③ 下一轮若要收口这颗过渡，"
               u"加一个只拍按钮带（captureRect）的胶片场景，声明时长 = `.selection`，并先证明它在 1x/2x 都能读出 ≥2 个样本。\n")
    d_new = (dc_tail + u"\n"
             u"### D-374（386）重钉前先确认针打的是**同一个对象**，同名调用点不算\n\n"
             u"R386 现读：M147 的旧针指向「`… scale: scale, gate: 8)`」这次调用，而重构后 `inkContrast` 已没有 gate 参数；"
             u"盘上剩下的唯一 `gate: 8` 属于另一条 tier-profile 探针。把它抬到 250 只会让那条测试 skip（绿），"
             u"于是同一段针文本打在一个**同名但不同对象**的调用点上，刀看似落地、其实没咬住。\n"
             u"**Why**：针是文本匹配，函数/参数改名后最容易留下「形状相同、对象不同」的落点；这时候 CAUGHT 与否都不说明原判据。\n"
             u"**How to apply**：重钉前先读**对象**（函数名 + 上下文行），再用两行以上锚点把同名兄弟排除；"
             u"抬阈值/改常量之前，先确认这个常量确实长在判据的读数路径上（不是 skip 守卫的路径）。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### 最后两根腐烂针重钉（M411/M147 均 CAUGHT），rot 2→0、上界同笔降；新开 435（skip 吞掉「尺坏了」）；网络断，本地领先 4 笔未推（R386 / U-1352…U-1354 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp, u"U-31 … U-1351（R385 现读抬到最新一节）", u"U-31 … U-1354（R386 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **1**", u"产品面连续零改动轮数 = **2**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R385 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R386 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R380 这一段（R337 补写；R341 续到 341、R380 续到 380 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R386 这一段（R337 补写；R341 续到 341、R386 续到 386 —— 这份报告第三次差点停在几十轮之前）")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    stx = rd(u"AGENT_STATE.md")
    r385_head = (u"## R385 状态（2026-10-26 · 本地 · 第 384 轮 / Round 382）：两颗「恢复默认」的禁用切换接上 .selection 过渡 + "
                 u"源形状守卫；367 再钉 r64 两根（产品 1 文件，动效主线）")
    state = (
        u"## R386 状态（2026-10-26 · 本地 · 第 385 轮 / Round 383）：最后两根腐烂针重钉，rot 2→0；"
        u"M147 旧目标被重构掉、同义坏法换 `prefix(0)`（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R386 / 第 385 轮 / Round 383）：r77 `M411` 重钉到两行整块（R80 的 lowercased）⇒ `CAUGHT`；"
        u"r33 `M147` 的旧目标 `gate: 8` 调用已被重构成 `inkContrast`（无 gate 参数），盘上同名 gate 抬到 250 只会 skip ⇒ "
        u"同义坏法换成「探针循环 `prefix(0)`」⇒ `CAUGHT`（`judged=0` 那条地板）；`HIDDEN_ARMS 表=227 可判=811 rot=0 … 处置=ok`，"
        u"`ROT_CEILING` 2→0；r77 整表 9/10、**M406 NOT-APPLIED**（新腐烂针，已记 367）；"
        u"全量沿用 R385（本轮没动 Swift）：`Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：GitHub 链路断（`api=000` / apple=200，IPv4/IPv6 均断）⇒ `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` "
        u"与 R385 那一跑的 conclusion 全部 **NOT-RUN（网络）**；本地 ahead=4（`5166a2b`、`479dfaa`、补登记生成器那笔、本轮）。\n"
        u"② 367 收口：M411 与 M147 重钉并各自 CAUGHT；rot 2→0、上界同笔降。\n"
        u"③ 新发现：tier-profile 的墨 gate 抬高只会 skip（skip 吞掉「尺坏了」）⇒ 开 BACKLOG 435；r77 M406 锚点失效。\n"
        u"④ 补登记 R381–R385 五支台账生成器（此前只在本机未跟踪），并把两笔提交 subject 修到守卫能读的形状。\n\n"
        u"验证读数（现读）：`M411 CAUGHT`（`testEveryTwoStateRulerReadsBothAxes`）；`M147 CAUGHT`"
        u"（`(\"0\") is less than (\"3\") - light 档 18 条说明段探针一条都没判成`）；r77 整表 `抓到=9 未落地=1`（M406）；"
        u"`HIDDEN_ARMS 表=227 可判=811 rot=0 抽不出=6 上界 rot=0 … 处置=ok`；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`（沿用 R385 日志）；"
        u"电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **@STREAK@** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 385` 现读）。\n\n"
        u"NOT-RUN（分开写）：① CI 三跑结论未读（网络）；② 真机腿没跑；③ R385 那颗 `.selection` 过渡的过程仍无胶片证人；"
        u"④ M406 未重钉；⑤ 435（skip 吞红）只开单未修。\n\n"
        u"下一轮（R387）的靶：⓪ 网络恢复后先 `git push origin main`，再读 `40234023212`/`40234058148` 与本次推送那一跑的全部失败步骤，"
        u"把 run id↔commit 成对写回本行；① 重钉 M406；② 收口 R385 过渡：造只拍按钮带的胶片场景（≥2 样本、1x/2x），"
        u"并按 435 给 skip 出口加负半证人。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(st)))
    stx = once(stx, r385_head, state + r385_head)
    wr(u"AGENT_STATE.md", stx)

    print(u"R386_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d" % (n, skipped, failures, ran, py_skipped, st))


if __name__ == u"__main__":
    main()
