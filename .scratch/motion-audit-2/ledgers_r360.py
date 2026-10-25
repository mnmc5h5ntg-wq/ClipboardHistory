#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R360 七本台账（第 359 轮 / Round 357 · 产品 0 文件，判据账）。"""
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
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"359"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
full = LOG(u"r360_full.log")
FULL_N, FULL_SKIP, FULL_FAIL = last(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full, u"全量卷")
pre = LOG(u"r360_pre.log")
P_TABLES, P_COVERED, P_ARMS, P_BAD = last(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre, u"针预检")
A_FILES, A_ARMS = last(r"ARM_TOTAL files=(\d+) arms=(\d+)", pre, u"臂名册")
battery = LOG(u"r360_py.log")
BAT_N = last(r"Ran (\d+) tests", battery, u"电池")[0]
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK"
build = LOG(u"r360_build.log")
assert u"Build complete" in build and u"warning:" not in build, u"构建不是 0 告警"

U = u"""## 第 359 轮（R360 · 2026-10-25 · U-1261…U-1263）：376 —— 三臂不可分先分叉：reduce-on 是产品行为，不是「这台机器看不见」（U-1261…U-1263 · 产品 0 文件，判据账）

- **U-1261：同一句读数有两种修法相反的成因。** 药丸的过程证人从 R323 起在 runner 上报
  `pill-slide-arms-indistinguishable`（开A/开B/关 帧数=1、峰值全等），读起来像"这台机器看不见过程"；
  但 `slideAnimation` 在 reduce 下返回 `.linear(duration: 0)`（位移就是药丸的全部内容 ⇒ 瞬移是**产品行为**），
  三臂自然一模一样，而 R355/R356 已经证明那台机器的 `shouldReduce` 是真（空态在 R348–R354 被归零）。
  R360 把出口原因收进一个纯函数 `pillSlideExitReason(armsIndistinguishable:reduceMotion:)`：
  reduce 真 ⇒ `reduce-motion-on`（具名未覆盖，产品行为）；reduce 关 ⇒ 才报通道那一半。
  catalog=off 时 detail 明写"reduce 若来自视图层这一格看不见"—— 没量到的来源不许写成量到了。
- **U-1262：判据与刀。** 新格 `testPillSlideExitReasonSeparatesReduceOnFromChannel`（四格：reduce→产品、
  非 reduce→通道、可分→nil 两格）；刀 `M1008` 把两个原因对调 ⇒ 该格红，`CAUGHT=1/1`。
  本机（reduce 关、三臂可分）照常判过程，不产生任何 not-run。
  全量卷 `Executed @FN@ tests, with @FS@ tests skipped and @FF@ failures`；构建 0 告警；电池 `Ran @BAT@`。
- **U-1263：376 的收口形状。** 它不再是"缺第二条通道"的悬案：runner 的这一跑若 `catalog=true`，
  下一份日志会直接出现 `MOTION_NOT_RUN=reduce-motion-on filter-pill-slide …`（产品行为，收口）；
  若 `catalog=false` 而三臂仍不可分，detail 会点明"可能来自视图层"，通道那一半**仍然成立**、仍欠第二通道。
  两种都写死在出口文本里，下一轮读日志即可二选一，不需要再猜。

"""

ITER = u"""## Round 357 · R360（第 359 轮 · 2026-10-25）：376 出口先分叉 —— reduce-on 记产品行为（产品 0 文件）

`pillSlideExitReason` 把"三臂不可分"分成 `reduce-motion-on`（产品按 431 归零）与通道那一半；
catalog=off 时 detail 写明视图层来源看不见。新格四格 + M1008 对调两原因（CAUGHT 1/1）。
全量 1031/48skip/0、电池 659；本机 reduce 关、三臂可分，过程照常判。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮对象是出口语义与 runner 读数；无画面改动。 |
| 判据有效性 | 14/15 | 纯函数四格 + 一刀；"可分时不给原因"也有格。 |
| 假绿防御 | 14/15 | catalog=off 时不把视图层来源写成已知；两种成因文本都落在日志里。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"产品行为与通道限制不再共用一句话"。 |
| 台账一致性 | 13/15 | U-1261…U-1263、D-359、376 追记；计数器现读。 |
| 交付诚实性 | 15/15 | runner 上二选一的结果要等下一跑；没把 reduce-on 写成已确认。 |
| 可复核性 | 15/15 | 一函数、一格测试、一把刀；细节全在日志文本里。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
376 追记（R360）：三臂不可分的出口按**成因**分叉 —— `pillSlideExitReason`：
    reduce 真 ⇒ `reduce-motion-on`（药丸按 431 归零是**产品行为**，具名未覆盖）；
    reduce 关 ⇒ `pill-slide-arms-indistinguishable`（通道那一半，仍欠第二通道）。
    catalog=off 时 detail 明写"reduce 可能来自视图层，这一格看不见"。
    本机（reduce 关、三臂可分）照常判过程；M1008 对调两原因 ⇒ 分叉证人红（CAUGHT 1/1）。
    **收口条件**：下一跑 runner 日志里二选一 —— 出现 `reduce-motion-on` 即按产品行为结案；
    若仍是 `pill-slide-arms-indistinguishable` 且 `catalog=off`，第二通道那条欠账继续挂着。

"""

DEC = u"""
### D-359（360）同一句"三臂不可分"要先分成因，再决定是产品行为还是通道限制

药丸的过程证人在 runner 上从 R323 起报 `pill-slide-arms-indistinguishable`，读起来像"这台机器看不见过程"；
而 reduce 下 `slideAnimation` 本来就是 0 时长（位移就是药丸的内容 ⇒ 瞬移是产品语义），三臂必然一模一样。
R360 把出口原因收进 `pillSlideExitReason`：reduce 真 → `reduce-motion-on`（产品行为，具名未覆盖）；
reduce 关 → 通道那一半；catalog=off 时明写视图层来源看不见。
**Why**：两种成因的修法相反 —— 一种要结案，一种要补第二通道；共用一句话会让下一轮去修一个不存在的通道问题，
或者反过来把通道限制洗成产品行为。
**How to apply**：出口谓词只要同时可能由"产品语义"与"通道/采样"造成，就必须先量出一个能分开它们的自变量
（这里是 `MotionCatalog.motionShouldBeReduced`），并在文本里写明"没量到的那一源"；不许用一个笼统的 not-run 名。

"""

CH = u"""### 药丸过程证的出口先分叉：reduce-on 记产品行为（431），reduce 关才记通道（376 追记）（R360 / U-1261…U-1263 · 产品 0 文件，判据账）
"""

STATE = u"""## R360 状态（2026-10-25 · 本地 · 第 359 轮 / Round 357）：376 出口先分叉 —— reduce-on 记产品行为（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R360 / 第 359 轮 / Round 357）：`pillSlideExitReason` 把「三臂不可分」分成
`reduce-motion-on`（产品按 431 归零）与通道那一半；catalog=off 时 detail 写明视图层来源看不见；
四格测试 + M1008 对调两原因（CAUGHT 1/1）；全量 1031/48skip/0、电池 659（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R359 一跑 queued（前面=2）、R358 两跑在跑；R356 追记绿跑已签下 R355/R356 的验收（见 R358 追记）。
② 376：出口原因收进 `pillSlideExitReason(armsIndistinguishable:reduceMotion:)`；reduce 真 → `reduce-motion-on`。
③ catalog=off 的 detail 明写「reduce 可能来自视图层，这一格看不见」—— 没量到的来源不许写成已知。
④ 四格测试 + M1008（两原因对调）⇒ CAUGHT 1/1；本机 reduce 关、三臂可分，过程照常判。

验证读数（现读）：全量卷 `Executed @FN@ tests, with @FS@ tests skipped and @FF@ failures`；构建 0 告警；
预检 `tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@`、`files=@AF@ arms=@AA@`；电池 `Ran @BAT@（skipped=4）OK`；
本轮无产品/尺的渲染改动 ⇒ 基线/胶片沿用 R356（182 帧 / 68 格）；产品面连续零改动 **@STREAK@** 轮。

NOT-RUN（分开写）：① 下一跑 runner 的出口二选一（`reduce-motion-on` 或 `pill-slide-arms-indistinguishable` + `catalog=off`）；
② `MOTION_REDUCE_SOURCES` 的接线验收（R359 的下一跑）；③ 真机腿没跑。

下一轮（R361）的靶：⓪ 读 R359/R360 两跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）→
① 367（表自己声明针）或 426（刀的 diff 判法）→ ② 若 runner 仍报通道那一半：376 的第二通道。

"""
UP_UI = u"""## 第 358 轮（R359 · 2026-10-25 · U-1258…U-1260）：必印族必须有专用 grep —— `MOTION_REDUCE_SOURCES` 在 runner 上被 head 截掉（U-1258…U-1260 · 产品 0 文件，判据账）"""
UP = u"""## R359 状态（2026-10-25 · 本地 · 第 358 轮 / Round 356）：必印族专用 grep —— `MOTION_REDUCE_SOURCES` 不再被 head 截掉（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@FN@": FULL_N, u"@FS@": FULL_SKIP, u"@FF@": FULL_FAIL,
             u"@PT@": P_TABLES, u"@PC@": P_COVERED, u"@PA@": P_ARMS, u"@PB@": P_BAD,
             u"@AF@": A_FILES, u"@AA@": A_ARMS,
             u"@BAT@": BAT_N, u"@STREAK@": str(STREAK)}
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
    fr = once(fr, u"| 决定台账 | D-069 … **D-358**", u"| 决定台账 | D-069 … **D-359**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1260（R359 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1263（R360 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1260**、决定最大 **D-358**",
              u"U 定义行最大 **U-1263**、决定最大 **D-359**")
    fr = once(fr, u"预检 tables=132 covered=115 arms=375 bad=0",
              u"预检 tables=133 covered=116 arms=376 bad=0")
    fr = once(fr, u"产品面连续零改动轮数 = **4**", u"产品面连续零改动轮数 = **5**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R359 节 ② 为准", u"`AGENT_STATE.md` 的 R360 节 ② 为准")
    tail = u"（R359 现读：注册表 **132** 张 / 刀号最大 **M1007** / 预检 covered=115 arms=375 bad=0；全仓 226 文件 / 865 把） |"
    fr = once(fr, tail,
              u"（R360 现读：注册表 **133** 张 / 刀号最大 **M1008** / 预检 covered=116 arms=376 bad=0；全仓 227 文件 / 865 把） |")
    bullet = u"""- **R360 续（判据账）**：376 的出口先分叉 —— `pillSlideExitReason` 把「三臂不可分」分成
  `reduce-motion-on`（药丸按 431 归零是产品行为）与通道那一半；catalog=off 时明写视图层来源看不见。
  四格测试 + M1008 对调两原因（CAUGHT 1/1）；全量 1031/48skip/0、电池 @BAT@。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R360_LEDGERS_OK U=1263 D=359 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
