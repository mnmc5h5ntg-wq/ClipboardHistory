#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R380 的七本台账（第 379 轮 / Round 377）：M244 的对照组归因 + 本机换装。"""
import io
import os
import re
import subprocess

ROOT = u"/Users/wangziyi/Codex_Project0"
FULL = u"/tmp/r380_full.log"
PY = u"/tmp/r379b_py.log"


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
    assert ran and re.search(r"^OK( \(skipped=\d+\))?$", b, re.M)
    sk = re.findall(r"OK \(skipped=(\d+)\)", b)
    return (int(m[-1][0]), int(m[-1][1]), int(m[-1][2]), int(ran[-1]), int(sk[-1]) if sk else 0)


def streak():
    out = subprocess.check_output([u"python3", u"scripts/product_streak.py", u"--streak-for", u"379"],
                                  cwd=ROOT).decode(u"utf-8")
    m = re.search(r"streak=(\d+)", out)
    assert m
    return int(m.group(1))


def main():
    n, skipped, failures, ran, py_skipped = counts()
    st = streak()
    assert failures == 0
    print(u"PARSED full=%d/%d/%d battery=%d(%d) streak=%d" % (n, skipped, failures, ran, py_skipped, st))

    ui = rd(u"AGENT_UI_AUDIT.md")
    head = (u"## 第 378 轮（R379 · 2026-10-26 · U-1322…U-1324）：r56 十臂全表第一次跑全（10/10 CAUGHT）；"
            u"M244 的重钉尝试 ESCAPED 并撤回（U-1322…U-1324 · 产品 0 文件，判据账）\n")
    section = (
        u"## 第 379 轮（R380 · 2026-10-26 · U-1325…U-1327）：M244 的对照组补上「归因到 add」；"
        u"刀仍 ESCAPED、针活了≠刀验过；本机换装 ok（U-1325…U-1327 · 产品 0 文件，判据账）\n\n"
        u"- **U-1325：对照组补内容断言。** 旧对照组只判「`history.json` 出现了」——R379 的 ESCAPED 说明"
        u"这可以是构造期/别处排的一次保存写的。现在多判一句：盘上那份必须**含刚加进去的文本**。"
        u"把这条断言加进 `testAddingACopyWritesNothingOnTheMainThread` 后，未变异的卷仍全绿"
        u"（`testAddingACopyWritesNothingOnTheMainThread passed (0.452 seconds)`）。\n"
        u"- **U-1326：M244 仍然 ESCAPED —— 但这次排除了一支。** 拿掉 `persist()` 的 `persistence.save` 后，"
        u"文件照样出现**且带着 add 的文本** ⇒ 既不是构造期的空快照，也不是 `persist()`；`add` 还有第三条落盘路（未定位）。"
        u"刀记 `NOT_VERIFIED`，r49 表头写明「跑这张表会红，别当成新坏法」。"
        u"**两轴分开**：M244 的针换到 `persist()` 后是**活的**，`HIDDEN_ARMS … rot=20`，"
        u"但「针活着」不等于「刀验过」——`ROT_CEILING` 同笔降到 20 并把这个区分写在注释里。\n"
        u"- **U-1327：本机换装 ok。** `scripts/install_local.sh --yes` 现读 `INSTALL_RESULT=ok  版本=1.4.8→1.4.8`、"
        u"`INSTALL_SHA_MATCH=1`、`INSTALL_ENTRIES_BEFORE=381  INSTALL_ENTRIES_AFTER=381`；"
        u"`swift build --build-tests` 告警 **0**；全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`。\n\n"
    )
    section = (section.replace(u"@N@", str(n)).replace(u"@SKIPPED@", str(skipped))
                      .replace(u"@FAIL@", str(failures)))
    ui = once(ui, head, section + head)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    tail = (u"| 可复核性 | 15/15 | 一条命令跑全表；十臂读数与 EXIT 都在日志里。 |\n\n"
            u"均分 = 91/105 ≈ 13.0/15（87）。")
    r377 = (
        u"\n\n## Round 377 · R380（第 379 轮 · 2026-10-26）：M244 的对照组补「归因到 add」；刀仍 ESCAPED、"
        u"针活了≠刀验过；本机换装 ok（产品 0 文件）\n\n"
        u"对照组从「文件出现了」加到「文件里必须含这次 add 的文本」，未变异仍全绿；把 `persist()` 的 save 拿掉后"
        u"文档照样带着 add 文本出现 ⇒ 第三条落盘路（不是构造期、不是 persist()），刀记 NOT_VERIFIED，"
        u"rot 21→20 只是针活了，`ROT_CEILING` 同笔降并在注释里分开两轴。换装腿：INSTALL_RESULT=ok、SHA_MATCH=1、"
        u"条目 381=381；build 0 告警、全量 1031/48/0。\n\n"
        u"**七维度自评**（恰七行，每格 n/15）：\n\n"
        u"| 维度 | 分 | 依据 |\n"
        u"| --- | --- | --- |\n"
        u"| 真实视觉审查 | 9/15 | 本轮无产品画面改动；看图仍是既有的 heat/filter 胶片。 |\n"
        u"| 判据有效性 | 14/15 | 对照组归因补上；但 M244 仍 ESCAPED，这一刀没验成。 |\n"
        u"| 假绿防御 | 15/15 | 「文件出现」不再单独作证；针活与刀验在账上分开。 |\n"
        u"| 产品面推进 | 8/15 | 产品 0 文件；换装腿补上了本机一致性。 |\n"
        u"| 台账一致性 | 14/15 | U-1325…U-1327、D-368、上界同笔；计数器现读。 |\n"
        u"| 交付诚实性 | 15/15 | ESCAPED 写清、没定位的路写清、针活≠刀验写清。 |\n"
        u"| 可复核性 | 15/15 | 测试一条命令、表一条命令、换装三行证据。 |\n\n"
        u"均分 = 90/105 ≈ 12.9/15（86）。"
    )
    it = once(it, tail, tail + r377)
    wr(u"AGENT_VISUAL_ITERATION.md", it)

    dc = rd(u"AGENT_DECISIONS.md")
    dc_tail = (u"**How to apply**：迁移或重钉之后，至少整表跑一遍（含预检与收尾复跑）；"
               u"预算不够整表时，账上写「本轮只跑了第 N 臂」，不许写成「表绿」。\n")
    d_new = (dc_tail + u"\n"
             u"### D-368（380）针活了 ≠ 刀验过：`rot` 与 `CAUGHT` 是两条轴\n\n"
             u"R380 现读：M244 的针换到 `persist()` 后 `HIDDEN_ARMS` 的 `rot` 从 21 掉到 20（静态：针在盘上命中一次），"
             u"而同一把刀跑出来仍是 `ESCAPED`（行为：拿掉 save 后对照组照样绿）。若只看 rot，这一格会被读成「修好了」。\n"
             u"**Why**：一个数同时代表两件事时，少的那一件会被另一件盖住 —— 这正是 R376 把「刀坏」与「判据没牙」分开的同一族。\n"
             u"**How to apply**：重钉只许改 rot；验刀只许看 `CAUGHT`。降 `ROT_CEILING` 的注释里必须写「针活了」还是「刀验过」；"
             u"没验过的刀留在表里要显式记 `NOT_VERIFIED`，不许用 rot 的下降替它作证。\n")
    dc = once(dc, dc_tail, d_new)
    wr(u"AGENT_DECISIONS.md", dc)

    cl = rd(u"CHANGELOG.md")
    cl_head = u"## [Unreleased]\n\n"
    cl_entry = (cl_head + u"### M244 的对照组补上「归因到 add」的内容断言（未变异全绿、刀仍 ESCAPED）；rot 21→20 与刀验分开记；本机换装 ok（R380 / U-1325…U-1327 · 产品 0 文件，判据账）\n\n")
    cl = once(cl, cl_head, cl_entry)
    wr(u"CHANGELOG.md", cl)

    rp = rd(u"AGENT_FINAL_REPORT.md")
    rp = once(rp,
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R376，377 节自评）",
              u"# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 R9–R377，378 节自评）")
    rp = once(rp, u"U-31 … U-1324（R379 现读抬到最新一节）", u"U-31 … U-1327（R380 现读抬到最新一节）")
    rp = once(rp, u"产品面连续零改动轮数 = **24**", u"产品面连续零改动轮数 = **25**")
    rp = once(rp, u"完整名单以 `AGENT_STATE.md` 的 R379 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R380 节 ② 为准")
    rp = once(rp,
              u"## 14. R299 → R379 这一段（R337 补写；R341 续到 341、R379 续到 379 —— 这份报告第三次差点停在几十轮之前）",
              u"## 14. R299 → R380 这一段（R337 补写；R341 续到 341、R380 续到 380 —— 这份报告第三次差点停在几十轮之前）")
    anchor14 = (u"- **R379 续（判据账）**：r56 十臂整表首次跑全（10/10 `CAUGHT`、还原干净、复跑 `ESCAPED`）；"
                u"M244 重钉尝试 `ESCAPED` 并撤回（rot 仍 21）。")
    rp = once(rp, anchor14, anchor14 + u"\n"
              u"- **R380 续（判据账）**：对照组补「归因到 add」的内容断言；M244 仍 `ESCAPED`（第三条落盘路），"
              u"针活了 rot 21→20 与刀验分开记；本机换装 `INSTALL_RESULT=ok`、SHA_MATCH=1、条目 381=381。")
    wr(u"AGENT_FINAL_REPORT.md", rp)

    ste = rd(u"AGENT_STATE.md")
    r379_head = (u"## R379 状态（2026-10-26 · 本地 · 第 378 轮 / Round 376）：r56 十臂全表第一次跑全（10/10 CAUGHT）；"
                 u"M244 重钉尝试 ESCAPED 并撤回（产品 0 文件，判据账）")
    state = (
        u"## R380 状态（2026-10-26 · 本地 · 第 379 轮 / Round 377）：M244 的对照组补「归因到 add」；"
        u"刀仍 ESCAPED、针活了≠刀验过；本机换装 ok（产品 0 文件，判据账）\n\n"
        u"最后更新：2026-10-26（本地 · R380 / 第 379 轮 / Round 377）：`testAddingACopyWritesNothingOnTheMainThread` "
        u"多判一句「盘上那份必须含刚加进去的文本」（未变异 0.452s 通过）；把 `persist()` 的 `save` 拿掉后"
        u"文件**仍带着 add 的文本**出现 ⇒ 第三条落盘路（不是构造期、不是 persist()），M244 记 `NOT_VERIFIED`；"
        u"rot 21→20 只是针活了，`ROT_CEILING` 同笔降并分开两轴；`scripts/install_local.sh --yes` 现读 "
        u"`INSTALL_RESULT=ok  版本=1.4.8→1.4.8`、`INSTALL_SHA_MATCH=1`、`INSTALL_ENTRIES_BEFORE=381  INSTALL_ENTRIES_AFTER=381`；"
        u"build `--build-tests` 告警 **0**；全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 Ran @RAN@（skipped=@SK@）OK（产品 0 文件 · 判据账）\n\n"
        u"本轮做了什么：\n"
        u"① ⓪ CI：`a84cb73`（R377）与 `a63dcf5`（R378）success、`3ef8c59`/`fbf2508`/`dfe411a` 已推；只登记不轮询。\n"
        u"② 对照组归因：文件出现 → 文件出现**且含 add 的文本**；未变异仍全绿。\n"
        u"③ M244 再跑：仍 ESCAPED（写出的带着 add 文本）⇒ 第三条落盘路；刀记 NOT_VERIFIED，表头写明会红。\n"
        u"④ 本机换装一遍（`--yes`）：ok、SHA 匹配、条目 381=381。\n\n"
        u"验证读数（现读）：未变异 `testAddingACopyWritesNothingOnTheMainThread passed (0.452 seconds)`；"
        u"`M244 ⇒ ESCAPED`；`HIDDEN_ARMS … rot=20 … 处置=?`；`swift build --build-tests` 告警 0；"
        u"全量 `Executed @N@ tests, with @SKIPPED@ tests skipped and @FAIL@ failures`；"
        u"电池 `Ran @RAN@（skipped=@SK@）OK`；产品面连续零改动 **@STREAK@** 轮"
        u"（`python3 scripts/product_streak.py --streak-for 379` 现读）。\n\n"
        u"NOT-RUN（分开写）：① 真机腿没跑；② 帧基线没更新（本轮无产品/夹具改动）；"
        u"③ 第三条落盘路没定位（M244 未验成）；④ 其余 20 条 rot 未重钉。\n\n"
        u"下一轮（R381）的靶：⓪ 读队列（`3ef8c59`/`fbf2508`/`dfe411a` 与本轮的结论）；"
        u"① 找出 add 的第三条落盘路（从 `entries` 的 didSet / Combine 订阅 / `reconcileSelection` 三条线查）；"
        u"② **回产品动效面点一个真实位**（已连续 25 轮零产品改动，这一维必须动）。\n\n"
    )
    state = (state.replace(u"@SKIPPED@", str(skipped)).replace(u"@FAIL@", str(failures))
                  .replace(u"@RAN@", str(ran)).replace(u"@SK@", str(py_skipped))
                  .replace(u"@N@", str(n)).replace(u"@STREAK@", str(st)))
    ste = once(ste, r379_head, state + r379_head)
    wr(u"AGENT_STATE.md", ste)

    print(u"R380_LEDGERS_OK full=%d/%d/%d battery=%d(%d) streak=%d"
          % (n, skipped, failures, ran, py_skipped, st))


if __name__ == u"__main__":
    main()
