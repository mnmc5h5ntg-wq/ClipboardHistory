#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R359 七本台账（第 358 轮 / Round 356 · 产品 0 文件，判据账）。"""
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
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"358"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
battery = LOG(u"r359_py.log")
BAT_N = last(r"Ran (\d+) tests", battery, u"电池")[0]
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK"

U = u"""## 第 358 轮（R359 · 2026-10-25 · U-1258…U-1260）：必印族必须有专用 grep —— `MOTION_REDUCE_SOURCES` 在 runner 上被 head 截掉（U-1258…U-1260 · 产品 0 文件，判据账）

- **U-1258：`MOTION_REDUCE_SOURCES` 在绿跑里一行都没有。** `40195884862 ↔ 6a0258a` 是绿的、`MOTION_LINES=328`，
  而 CI 那一步只 `grep -E "^MOTION_" | head -120`；这一行由 `testTransitionsAreActuallyRunning` 打，
  排在它前面的测试已经占满了 120 行 ⇒ **不是没打印，是被截掉**。读数族必须接进它被打印的那一步（Skill 的规矩），
  R355 只加了 emit、没加专用 grep。
- **U-1259：接线 + 守卫，守卫当场抓到我的第一版。** `ci.yml` 的 filmstrip 步加一条
  `grep -E "^MOTION_REDUCE_SOURCES" … || echo MOTION_PRINT_MISSING=…`；
  新守卫 `scripts/tests/test_ci_motion_print_wiring.py` 四格：真步里四族都有**专用 grep**（SUMMARY / RESOLVE / NOT_RUN / REDUCE_SOURCES）、
  合成步缺两族必须点名、**光 echo 族名不算打印**、模式都能编译。
  第一版我写成 `for prefix in …; do grep -E "$prefix"`，守卫判它没打印 —— 那是守卫对：**字面 grep** 才是这条规矩要的形状（循环变量让"打印过哪几族"不再能从文本里读出来）。
- **U-1260：R355/R356 的 runner 验收读数（同一次绿跑）。** `MOTION_SUMMARY … empty-state=3`、
  `MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner`；`MOTION_PILL_RAMP_GEOM … 行带=52.0…76.0pt
  候选段=y52..76px 高24px 判=过 洞宽=49% 纵向覆盖=24/24px=100%`；注入 reduce 的那卷 `过渡帧数=3 变化段时长=101ms`。
  ⇒ 429 的验收成立、384 在两机上成立；431 还欠"三源"那一行（本轮的接线要等下一跑）。

"""

ITER = u"""## Round 356 · R359（第 358 轮 · 2026-10-25）：必印族专用 grep —— `MOTION_REDUCE_SOURCES` 不再被 head 截掉（产品 0 文件）

`ci.yml` 的 filmstrip 步加专用 grep + `MOTION_PRINT_MISSING` 点名；新守卫把四族必印名单钉住
（真步 / 合成正对照 / 光 echo 不算 / 正则可编译）。守卫抓到第一版的 for-loop 写法。
电池 `Ran @BAT@（skipped=4）OK`；本轮不动产品与尺，全量/基线沿用 R358。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮对象是 CI 日志的可见性，没有画面改动。 |
| 判据有效性 | 14/15 | 四格守卫 + 合成正对照；"echo 不算"与"必须字面 grep"两处都会红。 |
| 假绿防御 | 14/15 | 缺族时 CI 打 `MOTION_PRINT_MISSING=…`，不是静默；守卫不读运行结果只读接线。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"runner 的读数能被看见"。 |
| 台账一致性 | 13/15 | U-1258…U-1260、D-358、431 追记；计数器现读。 |
| 交付诚实性 | 15/15 | 接线本身要等下一跑 runner 才算验收（NOT-RUN 写明）。 |
| 可复核性 | 15/15 | 一条 unittest + 一行 grep；名单在测试里。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
431 追记（R359）：`MOTION_REDUCE_SOURCES` 的**接线**补上了 —— 绿跑 `40195884862` 里 `MOTION_LINES=328`，
    而 CI 只打 `head -120`，这一族排在后面的测试里 ⇒ 一行都没有（不是没打印）。
    现在 filmstrip 步里有专用 `grep -E "^MOTION_REDUCE_SOURCES"`，缺了会打 `MOTION_PRINT_MISSING=…`；
    `scripts/tests/test_ci_motion_print_wiring.py` 把四族必印名单（SUMMARY / RESOLVE / NOT_RUN / REDUCE_SOURCES）钉住。
    **仍欠**：下一跑 runner 日志里出现 `MOTION_REDUCE_SOURCES setting=… voiceOver=… catalog=…`（接线只在 CI 上才算验收）。

"""

DEC = u"""
### D-358（359）"必印族"必须有一条专用、字面、不截断的 grep

R355 加了 `MOTION_REDUCE_SOURCES` 的 emit，却没接进 CI 的打印那一步；绿跑 `40195884862` 里
`MOTION_LINES=328` 而 CI 只打 `head -120`，这一族一行都没有 —— 读数存在，日志里看不见。
R359 给 filmstrip 步加专用 grep，并把四族必印名单写进 `test_ci_motion_print_wiring.py`。
**Why**：`head -120` 是"先全打再截"的预算，它对**结论/缺席/通道身份**级别的读数不适用；
一条读数族只要没人能在日志里看见，它就等于不存在，而"不存在"在下一次读账时会被写成"没发生"。
**How to apply**：新增读数族时同时改三处 —— emit、CI 的**字面** grep、`MUST_PRINT` 名单；
不许用 `for prefix in …; do grep "$prefix"`（循环变量让"打印过哪几族"不再能从文本里读出来，守卫也就无从对账）。
缺行时打 `MOTION_PRINT_MISSING=<族名>`，让缺席有名字。

"""

CH = u"""### 必印族补接线：`MOTION_REDUCE_SOURCES` 不再被 head -120 截掉，缺行会打 MOTION_PRINT_MISSING（R359 / U-1258…U-1260 · 产品 0 文件，判据账）
"""

STATE = u"""## R359 状态（2026-10-25 · 本地 · 第 358 轮 / Round 356）：必印族专用 grep —— `MOTION_REDUCE_SOURCES` 不再被 head 截掉（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R359 / 第 358 轮 / Round 356）：`ci.yml` 的 filmstrip 步加 `MOTION_REDUCE_SOURCES` 专用 grep +
`MOTION_PRINT_MISSING` 点名；新守卫 `test_ci_motion_print_wiring` 四格钉住必印名单；电池 `Ran @BAT@（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ 读绿跑 `40195884862 ↔ 6a0258a`：R355 修复被签下（`empty-state=3`、`judged=3/4 not-run=notice-banner`）、
   R356 的 384 在 runner 上 100%（`行带=52…76pt`、`纵向覆盖=24/24px`）、注入 reduce 那卷 `3 帧/101ms`。
② 发现 `MOTION_REDUCE_SOURCES` 一行都没有：`MOTION_LINES=328` 而被 `head -120` 截掉。
③ 接线：filmstrip 步加**字面**专用 grep；缺行打 `MOTION_PRINT_MISSING=^MOTION_REDUCE_SOURCES`。
④ 新守卫四格（真步/合成正对照/光 echo 不算/正则可编译）；它抓到第一版的 for-loop 写法并逼成字面 grep。
⑤ 本机不动产品、不动尺：全量/基线/胶片沿用 R358 的数，本轮只改 CI 接线与脚本守卫。

验证读数（现读）：脚本电池 `Ran @BAT@（skipped=4）OK`；`test_ci_motion_print_wiring` 4/4；
runner 验收（同一次绿跑）`empty-state=3` / `judged=3/4 not-run=notice-banner` / `纵向覆盖=24/24px=100%` / `MOTION_REDUCE 3 帧 101ms`；
产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 358` 现读）。

NOT-RUN（分开写）：① 接线在 runner 上的验收（下一跑日志里要出现 `MOTION_REDUCE_SOURCES setting=…`）；
② 真机腿没跑；③ 本轮无 Swift 改动 ⇒ 全量卷/胶片/基线没有重跑（沿用 R358 的 1030/68/182）。

下一轮（R360）的靶：⓪ 读 `ff3deba` / `f975be8` 与下一跑（重点：`MOTION_REDUCE_SOURCES` 三源 +
R357/R358 的 STEP[9] 是否不再红）→ ① 376（第二通道）或 367（表自己声明针）→ ② 426（刀的 diff 判法）→
③ 若两机同格：386 的两条线标定。

"""
UP_UI = u"""## 第 357 轮（R358 · 2026-10-25 · U-1255…U-1257）：387① 落地 —— 墨量只印不判，色档 A/B 从「敏感=8」收到「同=11 / 漂=1」（U-1255…U-1257 · 产品 0 文件，判据账）"""
UP = u"""## R358 状态（2026-10-25 · 本地 · 第 357 轮 / Round 355）：387① 落地 —— 墨量只印不判，色档 A/B 收到 同=11/漂=1（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@BAT@": BAT_N, u"@STREAK@": str(STREAK)}
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
    fr = once(fr, u"| 决定台账 | D-069 … **D-357**", u"| 决定台账 | D-069 … **D-358**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1257（R358 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1260（R359 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1257**、决定最大 **D-357**",
              u"U 定义行最大 **U-1260**、决定最大 **D-358**")
    fr = once(fr, u"脚本电池 `Ran 655`（skipped=4）", u"脚本电池 `Ran 659`（skipped=4）")
    fr = once(fr, u"产品面连续零改动轮数 = **3**", u"产品面连续零改动轮数 = **4**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R358 节 ② 为准", u"`AGENT_STATE.md` 的 R359 节 ② 为准")
    bullet = u"""- **R359 续（判据账）**：必印族补接线 —— 绿跑 `40195884862` 里 `MOTION_LINES=328` 而 CI 只打 `head -120`，
  `MOTION_REDUCE_SOURCES` 一行都没有；filmstrip 步加字面专用 grep + `MOTION_PRINT_MISSING` 点名，
  `test_ci_motion_print_wiring` 四格钉住必印名单（它抓到了第一版的 for-loop 写法）。电池 @BAT@。
  同一次绿跑也签下 R355 修复（empty-state=3、judged=3/4）与 R356 的 384（纵向覆盖 24/24=100%）。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R359_LEDGERS_OK U=1260 D=358 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
