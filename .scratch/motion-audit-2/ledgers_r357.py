#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R357 七本台账（第 356 轮 / Round 354 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
LOG = lambda n: io.open(os.path.join(u"/tmp", n), encoding="utf-8", errors="replace").read()

def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

def last(pat, text, what):
    found = list(re.finditer(pat, text))
    assert found, u"没解析到 %s" % what
    return found[-1].groups()

STREAK = int(re.search(u"streak=(\\d+)", subprocess.run(
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"356"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
battery = LOG(u"r357_py_first.log")
BAT_N = last(r"Ran (\d+) tests", battery, u"电池")[0]
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK (skipped=4)"
queue_log = LOG(u"r357_queue.log")
Q_INPROG = len(re.findall(r"状态=in_progress", queue_log))
Q_CONCL = len(re.findall(r"状态=concluded", queue_log))

U = u"""## 第 356 轮（R357 · 2026-10-25 · U-1252…U-1253）：读 CI 的第三态有名字了 —— `queue` 子命令（U-1252…U-1253 · 产品 0 文件，判据账）

- **U-1252：`scripts/ci_read.py queue` 落地（428 的兑现）。** 三态写死：`queued` / `in_progress` / `concluded`，
  认不出的状态点名成 `unknown:<status>`（缺 status 也不许当成 concluded）。每跑两列独立读数：
  `已等=Ns`（createdAt→现在）与 `同workflow前面=N`（created 更早、且仍未结案的跑数）。
  时间读不出 ⇒ `已等=-1`、不参与排序、由 `QUEUE_SUMMARY … 时间读不出=N` 单独计数 ——
  「读不到」做减法，不许给它一个像结论的 0。本机现读（`--limit 5`）：
  `40195884862 ↔ 6a0258a in_progress 已等=470s 前面=1`、`40195807519 ↔ df35274 in_progress 已等=531s 前面=0`、
  `40194348175 / 40194321798 concluded failure`。⇒ 「R356 的两跑还在队里」第一次是一条读数，而不是一个词。
- **U-1253：两处自曝。** ① 汇总口径第一版写错的是**测试的期望**：`QUEUE_SUMMARY` 按**全体**数（含另一条 workflow），
  而「前面」按**同 workflow** 数 —— 同一段里两个问题，工具对、我第一版的期望把两跑 UI 的 queued 算漏了。
  ② `--limit` 不是整数时在触网**之前**退 2，测试用替身 argv 证明这一格不依赖网络；
  未覆盖的是 `gh` 本身失败那条路（`queue()` 返回 1），记在 428 的结案里。

"""

ITER = u"""## Round 354 · R357（第 356 轮 · 2026-10-25）：`ci_read.py queue` 落地 —— 排队的三态与两个读数（产品 0 文件）

`queue` 子命令：queued / in_progress / concluded + unknown 点名；`已等` 与 `同 workflow 前面` 分开。
本机现读 R356 两跑均 in_progress（531s / 470s）、R355 两跑 concluded failure。
6 格新测试（含汇总口径与时间读不出两处正对照）；电池 `Ran @BAT@（skipped=4）OK`。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮没有画面改动；看的是 CI 的状态读数（不是像素腿）。 |
| 判据有效性 | 14/15 | 6 格纯函数测试 + 真实 `gh` 现读一次；三种状态各有一格。 |
| 假绿防御 | 14/15 | 未知状态点名；时间读不出做减法；测试用替身 argv 证明 usage 路径不触网。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"读 CI 不许把没跑读成没红"这条通道上。 |
| 台账一致性 | 13/15 | U-1252/U-1253、D-356、428 结案；计数器现读。 |
| 交付诚实性 | 15/15 | gh 失败路径未单测（428 结案里写明）；queue 只在本地真跑过一跑。 |
| 可复核性 | 15/15 | 一条命令、三态词表在源码里、测试离线可跑。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
428 结案（R357）：`scripts/ci_read.py queue` 落地 —— 三态（queued / in_progress / concluded）+ `unknown:<status>` 点名；
    每跑两列独立读数：`已等=Ns`（createdAt→现在）与 `同workflow前面=N`（更早且仍未结案）；
    时间读不出 ⇒ 已等=-1、不参与排序、单独计数（不做减法就是猜顺序）。
    6 格测试：三态词表 / 前面只数同 workflow 未结案 / 已结案不排队 / 时间读不出 / 未知状态单独数 / `--limit` 非整数在触网前退 2。
    本机现读：`QUEUE_SUMMARY 共=5 queued=0 in_progress=@QIP@ concluded=@QC@ 未知=0 时间读不出=0`。
    **仍欠**：`gh` 本身失败那条路（`queue()` 返回 1、stderr 有名字）没有单测 —— 它要替身 `gh`，
    代价比这一单本身大；先用"取不到时返回 1 且不打印任何 QUEUE 行"当约定，下一轮若要接进轮次开场必须补上。

"""

DEC = u"""
### D-356（357）「未读」不是一种结论：排队要拆成三态 + 两个独立读数

R354 追记二那次「五跑同时在队里、零跑结案」，台账里只剩「未读」一个词 —— 读的人分不清
「还没轮到」与「跑了一半挂了」，而「没跑」被当成「没红」是本仓库栽过的形状。
R357 把 `queue` 做成：状态三档（含未知点名）、`已等`、`同 workflow 前面`。
**Why**：三件事修法相反 —— queued 只需等，in_progress 要查是不是挂住，concluded 才轮得到读结论；
把它们压成一个词，下一轮就会在读不到结论时替它编一个。
**How to apply**：凡是「还没有结论」的读数，先写出它有几种成因、每种怎么数；汇总与"前面"按不同口径数
（全体 vs 同 workflow）时，两个数都要在日志里各自出现，测试的期望也要按那个口径写。

"""

CH = u"""### 读 CI 的第三态有名字了：`queue` 子命令（queued / in_progress / concluded + 未知点名；已等与同 workflow 前面分开）（R357 / U-1252…U-1253 · 产品 0 文件，判据账）
"""

STATE = u"""## R357 状态（2026-10-25 · 本地 · 第 356 轮 / Round 354）：读 CI 的第三态有名字了 —— queue 子命令（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R357 / 第 356 轮 / Round 354）：`scripts/ci_read.py queue` 落地 ——
三态 + 未知点名、`已等` 与 `同 workflow 前面` 分开；本机现读 R356 两跑 in_progress（531s/470s）、R355 两跑 concluded failure；
6 格离线测试，电池 `Ran @BAT@（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R356 两跑现读 `in_progress`（追记那一跑在前、主笔在后），R355 两跑 concluded failure（已知 STEP[9] 抢先红）；只登记不轮询。
② 给 `ci_read.py` 加 `queue`：`queue_state` / `queue_rows` / `queue_summary` 三个纯函数 + CLI（`--workflow` / `--limit`）。
③ 三态写死、未知点名；`已等` 与「同 workflow 前面」分开；时间读不出做减法并单独计数。
④ 6 格测试：三态、前面口径、已结案不排队、时间读不出、未知状态、`--limit` 非整数不触网。
⑤ 自曝：汇总口径第一版把另一条 workflow 的 queued 算漏 —— 错的是**测试期望**（工具对）。

验证读数（现读）：电池 `Ran @BAT@（skipped=4）OK`；`QUEUE_SUMMARY 共=5 queued=0 in_progress=@QIP@ concluded=@QC@ 未知=0 时间读不出=0`；
本轮无产品/尺改动 ⇒ 全量卷沿用 R356 的 `Executed 1030/48skip/0`、胶片 68/3/0（judged=4/4）、基线 182/0（R355 重捕）、清账表 162/162；
产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 356` 现读）。

NOT-RUN（分开写）：① `gh` 本身失败那条路（`queue()` 返回 1）没有单测（428 结案里写明理由与补法）；
② 真实视觉审查腿没跑（本轮没有画面改动，只有 CI 状态读数）；③ 真机腿没跑。

下一轮（R358）的靶：⓪ 读 `40195807519 ↔ df35274` / `40195884862 ↔ 6a0258a`（若已结案；否则用 `queue` 登记第三态）→
① 387①（墨量那颗不进 max，只印；先量翻的那一格）→ ② 376 / 367 → ③ 426（刀的 diff 判法）。

"""
UP_UI = u"""## 第 355 轮（R356 · 2026-10-25 · U-1247…U-1251）：384 结案 —— 标签墨不再把胶囊劈成两半，带子纵向覆盖 29%→100%（U-1247…U-1251 · 产品 0 文件，判据账）"""
UP = u"""## R356 状态（2026-10-25 · 本地 · 第 355 轮 / Round 353）：384 结案 —— 带子 7pt→24pt、覆盖 29%→100%（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@BAT@": BAT_N, u"@STREAK@": str(STREAK),
             u"@QIP@": str(Q_INPROG), u"@QC@": str(Q_CONCL)}
    for k, v in pairs.items():
        text = text.replace(k, v)
    leftover = re.findall(u"@[A-Z0-9]{2,}@", text)
    assert not leftover, u"还有占位符：%s" % u",".join(sorted(set(leftover)))
    return text

def main():
    ui = rd(u"AGENT_UI_AUDIT.md")
    ui = once(ui, UP_UI, fill(U) + UP_UI)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    if not it.endswith(u"\n"):
        it += u"\n"
    wr(u"AGENT_VISUAL_ITERATION.md", it + fill(ITER))

    bl = rd(u"AGENT_BACKLOG.md")
    if not bl.endswith(u"\n"):
        bl += u"\n"
    wr(u"AGENT_BACKLOG.md", bl + fill(BL))

    de = rd(u"AGENT_DECISIONS.md")
    if not de.endswith(u"\n"):
        de += u"\n"
    wr(u"AGENT_DECISIONS.md", de + fill(DEC))

    ch = rd(u"CHANGELOG.md")
    ch = once(ch, u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + fill(CH) + u"\n")
    wr(u"CHANGELOG.md", ch)

    st = rd(u"AGENT_STATE.md")
    before = st.count(u"\n## R")
    st = once(st, UP, fill(STATE) + UP)
    wr(u"AGENT_STATE.md", st)
    st2 = rd(u"AGENT_STATE.md")
    assert UP in st2 and st2.count(u"\n## R") == before + 1, u"STATE 轮换后上一轮标记丢了或层数不对"

    fr = rd(u"AGENT_FINAL_REPORT.md")
    fr = once(fr, u"| 决定台账 | D-069 … **D-355**", u"| 决定台账 | D-069 … **D-356**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1251（R356 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1253（R357 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1251**、决定最大 **D-355**",
              u"U 定义行最大 **U-1253**、决定最大 **D-356**")
    fr = once(fr, u"脚本电池 `Ran 649`（skipped=4）", u"脚本电池 `Ran 655`（skipped=4）")
    fr = once(fr, u"产品面连续零改动轮数 = **1**", u"产品面连续零改动轮数 = **2**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R356 节 ② 为准", u"`AGENT_STATE.md` 的 R357 节 ② 为准")
    tail = u"（R356 现读：注册表 **131** 张 / 刀号最大 **M1006** / 预检 covered=114 arms=374 bad=0；全仓 225 文件 / 865 把） |"
    fr = once(fr, tail,
              u"（R357 现读：注册表 **131** 张 / 刀号最大 **M1006** / 预检 covered=114 arms=374 bad=0；全仓 225 文件 / 865 把） |")
    bullet = u"""- **R357 续（判据账）**：`ci_read.py queue` 落地（428 结案）—— 三态 + `unknown:<status>` 点名、
  `已等` 与「同 workflow 前面」分开、时间读不出做减法；6 格离线测试，电池 `Ran @BAT@`。
  本机现读 R356 两跑 in_progress、R355 两跑 concluded failure（已知 STEP[9] 抢先红）。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R357_LEDGERS_OK U=1253 D=356 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
