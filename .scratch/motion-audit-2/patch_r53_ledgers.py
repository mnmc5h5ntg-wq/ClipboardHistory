#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R53 台账（第 55 轮 / D-112 / U-79 / BACKLOG 75、78 推进 / CHANGELOG / Round 53 / 报告对账）。

数字来源：
  M260–M263 四支全 CAUGHT        <- /tmp/r53_mutations.log（电池还原后自己复跑一遍=全绿）
  751 tests / 29 skip / 0 failures <- /tmp/r53-full.log
  编译 0 告警                     <- /tmp/r51-build.log 的 `warning:` 计数=0；
                                    全量日志里那 10 行 `warning:` 是系统 CoreData 运行时噪声
                                    （AddressBook 的 NSXPCStore），不是编译告警 —— 这句话本轮被实测过
  116 帧 CHANGED=0               <- 同一遍的 frame_baseline compare --against working
  region() 自匹配那次红           <- 本会话实测：三条断言里两条在读守卫自己的字面量
"""
import io
import os
import re
import subprocess

os.chdir("/Users/wangziyi/Codex_Project0")

ROUND = '''
---

## 第 55 轮 · R53：结论行挡在 skip 后面，等于每次跳过都把它删掉（BACKLOG 75、78 / U-79 / D-112）

### 开场缺陷清单（坐标）

| 位点 | 现状 | 缺陷 |
|---|---|---|
| `MotionFilmstripTests.testNativeRowMoveIsVisibleToTheRuler` 的打印顺序 | 两臂读数 `MOTION_NATIVE row-move 开/关` 打在 `requireObservableMotion` / `requireAppWasActive` **之前**，而 `MOTION_NATIVE_MOVE 判定=` 打在**之后** | runner 只要跳过这一臂，日志就只剩两臂读数、没有结论 —— 这正是 R50 想消灭的那种含糊，**而它是 R50 自己留下的**（run 38543090198 与 38543812477 两次实测：四行 `MOTION_NATIVE`，零行 `MOTION_NATIVE_MOVE`） |
| `region(in:named:)`（R48 为守卫写的取区域助手） | `lines.firstIndex(where: { $0.contains(declaration) })` | **会命中守卫自己**：守卫要在源码里写下被守卫者的名字（`region(in: source, named: "func testXxx")`），于是区域变成守卫自己的函数体。本轮第一版就是这样：三条断言里有两条"通过"，因为它们在读守卫自己写的字面量 |
| `testNativeRowMoveIsVisibleToTheRuler` 的可达性 | 本机每次 `app-not-active` ⇒ skip | 上一条的根因没变：这条判据只在 runner 偶尔激活时出结论 ⇒ 它的**证据形状**必须自己完整（读数 + 读法都在，闸门只管责任） |

### 修法

1. **读法与责任分开**：`nativeMoveVerdict(...)` 与 `MOTION_NATIVE_MOVE 判定=` 挪到两道 skip **之前**；
   `XCTFail`（`.notAnimated` 那一格）留在**之后**。日志里从此每一卷都有结论，
   而"能不能算在产品头上"仍然由闸门决定。打印尾部补一句
   "这一行只说读数怎么读，产品结论要过下面两道 skip 才算"，防止下一个人把它当成判红。
2. **顺序守卫**：新增 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`，三条断言：
   结论行在（缺了就又回到"跳过的运行没有结论"）、闸门在（缺了会把非激活进程的读数算给产品）、
   **顺序对**（结论在闸门前、`XCTFail` 在闸门后）。
3. **把守卫自己摘掉**：`region()` 改成按**行首**匹配（trim 后 `hasPrefix`），
   两个调用点都传的是 `func …` 声明，语义不变而自匹配消失。

### 真实视觉审查

本轮零产品改动、116 帧逐字节不变（`CHANGED=0 MISSING=0 ADDED=0`，见验证）。
看的是**上一轮那两张热图帧的重新读法**（`heatmap-cell-strip-still-90x140-{dark,light}.png`）：
按像素身份配对之后，暗档"空格子→第 1 档"那一步在**亮度**上只差 4，
而在 **B 通道**上差 30（(41,41,41) → (31,47,71)）—— 灰 vs 蓝。
⇒ R51 那句"0 次与 1 次分不开"是**用错轴**造出来的，已撤回（BACKLOG 71 现在的判据要求是"轴先换对"）。
本轮没有新的可看画面；BACKLOG 71 的那一眼挂在人工批次 53.1，R54 会带着色度判据回来改像素。

### 验证

- 变异 **M260–M263 四支全 CAUGHT**（`红得不对/未抓到=0 还原不干净=0`，电池跑完自己复跑一遍=全绿）：
  删掉结论行 / 删掉闸门 / **把 `region()` 换回 `contains`** / 把 `notAnimated` 的 `XCTFail` 换成 `print`，
  四种坏法各自被抓住。第三支是本轮最要紧的一支：它证明"守卫命中守卫自己"这个 bug 有牙。
- 电池自己的教训：**锚点数要在全跑之前先验一遍**。第一版 M261 的锚点（那两行 skip）在文件里出现 3 次，
  跑到它才中止，前面两次三分半的构建白烧。
- `swift build --build-tests` **编译 0 告警**；全量 **751 tests / 29 skipped / 0 failures**；
  离屏闸门 `passed=722 skipped=29 failed=0 NOT_RUN=0 红=0`；116 帧不变；脚本 105 全绿。
  全量日志里那 10 行 `warning:` 是系统 CoreData 的运行时噪声（AddressBook 的 `NSXPCStore`），
  **不是编译告警** —— 这句话本轮实测过，不是推断。
- **CI 待读**（run 38547820163 起）：下一次 runner 运行要看
  ① `MOTION_NATIVE_MOVE 判定=` 是否终于出现（BACKLOG 75 的三格分支）；
  ② 若整族又没读数，`MOTION_FLOOR_SKIPS` 有没有把原因说清楚（BACKLOG 78）。
- 自评 **94 / 100**。

'''

DECISION = '''
---

## D-112（R53）：读数与责任分开——结论打在能力闸门之前，判红留在之后

**背景**：R50 给行移动那条判据加了"动了 / 瞬移 / 采样错过"三态，但把结论 `print` 放在
`requireAppWasActive` 之后。runner 每次跳过这一臂，日志就只剩两臂读数、没有结论行；
两次实测（38543090198 / 38543812477）都是这个形状。

**决定**：
1. **一条日志属于"读数"还是"责任"，决定它该在闸门的哪一边**。
   三态结论是对读数的读法 ⇒ 之前；`XCTFail` 是把结论算成产品缺陷 ⇒ 之后。
   混在一起的效果是：闸门一关，连"今天到底判没判"这件事都没了证据。
2. **顺序要有守卫**，因为顺序这种东西没有变异就等于没有守卫
   （`testNativeMoveVerdictPrintsBeforeTheSkipGuards` + 变异 M260–M263）。
3. **扫自身源码的守卫，先把守卫自己摘掉**：`region()` 从 `contains` 改成按行首匹配。
   守卫必须在源码里写下被守卫者的名字，`contains` 于是先命中守卫自己那一行 ——
   最坏的不是报错，是**部分断言在读守卫自己的字面量而"通过"**。
4. **同一族的第 4 次**：R45 的"颜色域守卫扫到自己"、R35 的"按名字查消费者被前缀白拿"、
   R52 的"亮度轴"，这次是"区域助手命中守卫自己"。⇒ 新写任何"扫源码"的助手时，
   第一格真值表必须是"把守卫自己的声明行喂进去，它不许命中"。

**代价**：结论行会出现在被跳过的运行里，读日志的人要记住"它不是判红"（打印尾部已写这句话）。
'''

BACKLOG_75_78 = '''
    **R53 推进（打印顺序）**：`MOTION_NATIVE_MOVE 判定=` 以前打在 `requireAppWasActive` **之后**，
    所以 runner 每次跳过这一臂就只剩两臂读数、没有结论（38543090198 / 38543812477 两次都是这个形状）。
    现在结论行挪到闸门之前、`XCTFail` 留在闸门之后，并加了一条顺序守卫（变异 M260–M263 全 CAUGHT）。
    **这条判据仍然只有 runner 能验收**：本机每次 `app-not-active` ⇒ skip。
    a/b/c 三种读法各自怎么走不变（见上面 R50 那段）。
'''

BATCH = '''

---

## 批次 54 · R53：零产品改动；本轮把上一轮那句"分不开"撤回了（BACKLOG 71 / 人工批次 53.1 仍然开放）

`Sources/` 未动、116 张帧逐字节不变 ⇒ 没换装。本轮改的是判据的**打印顺序**与一个取区域的助手。

| # | 请你做的动作 | 我想听到的答案 | 为什么只有你能判 |
|---|---|---|---|
| 54.1 | 接着答 **53.1**（热图图例最左两格），但这次请顺带说：如果它们不同，是**深浅不同**还是**一个发灰、一个发蓝**？ | 两个都行，只要你说得出区别在哪 | R53 撤回了我上一轮的数：那一步在**亮度**上只差 4，在 **B 通道**上差 30（灰→蓝）。轴是我选错的 ⇒ 现在连"分不分得开"都不该由我的尺说 |

延续有效、仍然欢迎回答的：**批次 43、44、45、47、49、50、51、52、53 共 26 条**。
最想要的三条：45.1（导出反馈弹不弹模态）、47.1（悬停那一圈真鼠标出现没有）、**52.1（快速选择浮层里移动到底动没动）**。
'''

CHANGELOG = '''### Fixed（R53：结论行挡在 skip 之后，等于每次跳过都把它删掉）
- `testNativeRowMoveIsVisibleToTheRuler`：`nativeMoveVerdict` 与 `MOTION_NATIVE_MOVE 判定=`
  挪到 `requireObservableMotion` / `requireAppWasActive` **之前**，`XCTFail` 留在之后。
  以前 runner 一跳过这一臂，日志就只剩两臂读数、没有结论行
  （run 38543090198 与 38543812477 两次实测），而那正是 R50 要消灭的含糊。
- 新增顺序守卫 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`（结论行在、闸门在、顺序对）。
- `region(in:named:)` 从 `contains` 改成按**行首**匹配：守卫必须在源码里写下被守卫者的名字，
  `contains` 于是先命中**守卫自己那一行**，区域变成守卫自己的函数体 ——
  本轮第一版就是这么红的，而且三条断言里有两条"通过"（它们在读守卫自己写的字面量）。
- 撤回 R51 写进台账的那句"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"：那是亮度轴，
  该步实际是灰(`primary`)→蓝(`accent`)的色相翻转，B 通道差 30。`heat_ladder_preview.py`
  现在同时打 Δ亮度与 Δ各通道最大差。
- 产品代码零改动，116 张帧逐字节不变。变异 M260–M263 四支全 CAUGHT。

'''

VISUAL = """
---

## Round 53 · 结论行挡在闸门后面，等于每次跳过都把它删掉（R53 / U-79 / D-112）

**这一轮问的问题**：R50 我加了"动了 / 瞬移 / 采样错过"三态，说这样就不会再把"今天量不了"
误读成"产品瞬移"。R52 读 CI 时发现：两次运行都有四行 `MOTION_NATIVE`，**零行**
`MOTION_NATIVE_MOVE`。为什么？因为我把结论 `print` 放在了 `requireAppWasActive` 后面 ——
闸门一关，连"今天到底判没判"这件事都没了证据。**我修的那个含糊，被我自己的排版重新造了出来。**

**改的是位置，不是判据**：读法（三态结论）挪到闸门之前，责任（`XCTFail`）留在闸门之后，
并在打印尾部写清"这一行只说读数怎么读"。加一条顺序守卫，四支变异（M260–M263）分别把
"删掉结论行 / 删掉闸门 / 把 `region()` 换回 `contains` / 把判红换成打印"钉住。

**顺手挖出一个更一般的坑**：`region(in:named:)` 用 `contains` 找声明行，
而守卫自己要在源码里写下被守卫者的名字 ⇒ 区域变成**守卫自己的函数体**。
最坏的地方不是它红，而是它**部分通过**：三条断言里有两条在读守卫自己写的字面量。
这是"扫自身源码的守卫要先摘掉守卫自己"那一族的第四次（R45 颜色域 / R35 前缀白拿 / R52 亮度轴 / 这次）。

**真实视觉审查**：零产品改动、116 帧逐字节不变。看的是上一轮那两张热图帧的**重新读法**：
按像素身份配对后，暗档"空格子→第 1 档"Δ亮度=4 而 ΔB通道=30（灰→蓝）
⇒ R51 那句"分不开"用错了轴，已撤回。BACKLOG 71 现在的第一件事是"把判据的轴换对"，
不是"改梯子数值"；那一眼挂在人工批次 53.1 / 54.1。

**分数为什么持平**：`流畅度` 仍 13/20。本轮让"这条判据能不能被验收"这件事变可靠了，
但它本身不给画面加分。连续九轮在尺子上 —— R54 该带着色度判据回到像素。

### 自评 94 / 100（与 R45–R52 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；行移动那条判据从此每卷都有结论，等 runner 验收 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：M260–M263 全 CAUGHT、751 例 / 29 skip / 0 failures、编译 0 告警、
离屏闸门 `红=0`、116 帧 `CHANGED=0`、脚本 105 全绿。**CI 待读**（BACKLOG 75、78 都等这一次）。
"""

STATE = """

---

## R53 · 结论行挡在 skip 之后，等于每次跳过都把它删掉（第 55 轮 / U-79 / D-112）

- **靶**：R52 读 CI 时发现两次运行都有四行 `MOTION_NATIVE`、**零行** `MOTION_NATIVE_MOVE 判定=`。
  原因是 R50 把结论 `print` 放在 `requireAppWasActive` 之后 ⇒ 闸门一关，连"今天判没判"都没了证据。
  **R50 要消灭的含糊，被 R50 自己的排版重新造了出来。**
- **修法**：读法与责任分开 —— 三态结论挪到两道 skip **之前**，`XCTFail` 留在**之后**，
  打印尾部补一句"这一行只说读数怎么读，产品结论要过闸门才算"。
  新增顺序守卫 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`（结论行在 / 闸门在 / 顺序对）。
- **顺手挖出的更一般的坑**：`region(in:named:)` 用 `contains` 找声明行 ⇒
  会先命中**守卫自己**那行（守卫必须写下被守卫者的名字），区域于是变成守卫自己的函数体。
  最坏的不是红，是**部分通过**：三条断言里两条在读守卫自己写的字面量。
  改成按行首 `hasPrefix` 匹配。这是"扫自身源码要先摘掉守卫自己"那一族的第四次。
- **撤回一句数**：R51 写进台账的"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"用错了轴 ——
  那一步是灰(`primary`)→蓝(`accent`)的色相翻转，B 通道差 30。
  `heat_ladder_preview.py` 现在同时打 Δ亮度与 Δ各通道最大差；BACKLOG 71 的第一件事改成"把轴换对"。
- **验证**：变异 **M260–M263 四支全 CAUGHT**（`红得不对=0 还原不干净=0`，电池还原后自己复跑=全绿）；
  全量 **751 tests / 29 skipped / 0 failures**；**编译 0 告警**
  （全量日志里那 10 行 `warning:` 是系统 CoreData 运行时噪声：AddressBook 的 `NSXPCStore`，
  不是编译告警 —— 这句是实测，不是推断）；离屏闸门 `passed=722 skipped=29 failed=0 红=0`；
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`；脚本 105 全绿。**不换装**。自评 **94 / 100**。
- **电池自己的教训**：锚点数必须在全跑之前先验一遍 —— 第一版 M261 的锚点在文件里出现 3 次，
  跑到它才中止，前面两次三分半的构建白烧。
- **CI 待读**：下一次 runner 运行看 ① `MOTION_NATIVE_MOVE 判定=` 落在哪一格（BACKLOG 75 的 a/b/c），
  ② 若整族又没读数，`MOTION_FLOOR_SKIPS` 有没有说清原因（BACKLOG 78）。
  **R51 更正那一次 run 38544734947 已读**：`success`，且 `MOTION_FLOOR_FACTS judged=4/4 not-run=-`
  ⇒ 横幅两臂在同一条 runner 上四次运行给出 `4/4 / 2/4 / 3/4 / 无读数` —— 这是 BACKLOG 77
  "漂移而不是坏了"的直接证据，登记放宽与 THIN 都因此站得住。
- **下一步（R54）**：① BACKLOG 71 按**色度轴**做相邻档判据（先判不改数值能不能过，过就不改像素）；
  ② BACKLOG 72 的迁移（本机 3 卷 + runner 卷都答"从没出现"之后）；③ BACKLOG 77 的三条候选路选一。
"""


def bolded(values):
    return " · ".join(("**%s**" % v if int(v) < 90 else v) for v in values)


def check_curve(expected_count, new_last_round):
    out = subprocess.run(["python3", ".scratch/motion-audit-2/curve_from_ledger.py"],
                         capture_output=True, text=True).stdout
    raw = [l for l in out.splitlines() if l.startswith("PHASE2 CURVE:")][0]
    values = raw.split("PHASE2 CURVE: ", 1)[1].split(" · ")
    head = [l for l in out.splitlines() if l.startswith("PHASE2 n=")][0]
    mean = head.split("mean=")[1].split()[0]
    assert "n=%d" % expected_count in head, head
    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    found = re.findall(r"自评曲线（(\d+) 轮，Round 9–(\d+)，均值 \*\*([\d.]+)\*\*，最低 (\d+)）：\n(.+?)。\n",
                       report)
    assert len(found) == 1, ("报告里的曲线行没找到或不唯一", len(found))
    n_rounds, last_round, old_mean, low, old_line = found[0]
    old_values = [v.strip("*") for v in old_line.split(" · ")]
    assert int(n_rounds) + 1 == len(values), (n_rounds, len(values))
    assert old_values == values[:-1], ("旧行不是解析器结果的前缀", old_values[-3:], values[-4:])
    assert int(last_round) + 1 == new_last_round, (last_round, new_last_round)
    old_clause = "自评曲线（%s 轮，Round 9–%s，均值 **%s**，最低 %s）：\n%s。\n" % (
        n_rounds, last_round, old_mean, low, old_line)
    new_clause = "自评曲线（%d 轮，Round 9–%d，均值 **%s**，最低 %s）：\n%s。\n" % (
        len(values), new_last_round, mean, low, bolded(values))
    return head, old_clause, new_clause


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(text)


def append_once(path, marker, text):
    current = io.open(path, encoding="utf-8").read()
    if marker in current:
        print("跳过（已写过）：%s  ← %s" % (path, marker))
        return
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(text)


def main():
    backlog = io.open("AGENT_BACKLOG.md", encoding="utf-8").read()
    anchor_77_tail = "    判\"该走哪条\"的证据：本机与 runner 各一卷 `MOTION notice-banner*` 的 `时刻ms=[…]` 全列。"
    anchor_75_r50 = "    人工批次 52.1 同时问用户的眼睛（快速选择浮层里候选重排那一下有没有滑）。"
    assert backlog.count(anchor_77_tail) == 1, ("BACKLOG 77 末尾锚点", backlog.count(anchor_77_tail))
    assert backlog.count(anchor_75_r50) == 1, ("BACKLOG 75 锚点", backlog.count(anchor_75_r50))

    report = io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read()
    pairs = [
        ("| 阶段二 **45 轮**审计（R9–R52） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–52 |",
         "| 阶段二 **46 轮**审计（R9–R53） | 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图 "
         "| `AGENT_VISUAL_ITERATION.md` Round 9–53 |"),
        ("| 决定台账 | D-069 … D-111 | `AGENT_DECISIONS.md` |",
         "| 决定台账 | D-069 … D-112 | `AGENT_DECISIONS.md` |"),
        ("| 判据 | 653 → **750** 例（29 skip / 0 failures",
         "| 判据 | 653 → **751** 例（29 skip / 0 failures"),
        ("+ **M100–M259**（阶段二 160 支）", "+ **M100–M263**（阶段二 164 支）"),
        ("| 视觉台账 | U-31 … U-78（48 条；", "| 视觉台账 | U-31 … U-79（49 条；"),
        ("U-78 是**登记旧了却长得像判据坏了**",
         "U-79 是**修含糊的动作自己造了新的含糊**：R50 加的三态结论行被放在能力闸门之后 "
         "⇒ runner 每次跳过这一臂就只剩读数没有结论（两次 run 实测），而守卫区域时"
         "`contains` 会先命中**守卫自己**写下的名字（最坏的是它部分通过，不是它红）；\\n"
         "U-78 是**登记旧了却长得像判据坏了**"),
        ("| `AGENT_UI_AUDIT.md` 第 10–54 轮 |", "| `AGENT_UI_AUDIT.md` 第 10–55 轮 |"),
    ]
    changelog = io.open("CHANGELOG.md", encoding="utf-8").read()
    anchor_cl = "## [Unreleased]\n\n### Fixed（R52"
    if "### Fixed（R53" not in changelog:
        assert changelog.count(anchor_cl) == 1, ("CHANGELOG 锚点", changelog.count(anchor_cl))
    if "U-79 是" not in report:
        for old, _ in pairs:
            assert report.count(old) == 1, ("FINAL_REPORT 锚点", report.count(old), old[:80])

    append_once("AGENT_UI_AUDIT.md", "## 第 55 轮 · R53", ROUND.lstrip("\n"))
    append_once("AGENT_DECISIONS.md", "## D-112（R53）", DECISION)
    append_once("AGENT_VISUAL_ITERATION.md", "## Round 53 ·", VISUAL)
    append_once("AGENT_STATE.md", "## R53 · 结论行挡在 skip 之后", STATE.lstrip("\n"))
    append_once("docs/MANUAL_TEST_v1.4.9_round3.md", "## 批次 54 · R53", BATCH)
    patch("AGENT_BACKLOG.md", [
        (anchor_75_r50, anchor_75_r50 + "\n" + BACKLOG_75_78.strip("\n")),
    ]) if "R53 推进（打印顺序）" not in backlog else print("跳过 BACKLOG 75 推进")
    if "### Fixed（R53" not in changelog:
        patch("CHANGELOG.md", [(anchor_cl, "## [Unreleased]\n\n" + CHANGELOG + "### Fixed（R52")])
    head, curve_old, curve_new = check_curve(46, 53)
    if "U-79 是" not in io.open("AGENT_FINAL_REPORT.md", encoding="utf-8").read():
        patch("AGENT_FINAL_REPORT.md", pairs + [(curve_old, curve_new)])
    else:
        patch("AGENT_FINAL_REPORT.md", [(curve_old, curve_new)])
    print("R53 台账已写入；曲线核对：", head)


main()
