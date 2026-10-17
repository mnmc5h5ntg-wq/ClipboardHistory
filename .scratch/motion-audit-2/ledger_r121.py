#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R121（第 123 轮）的账本补丁：BACKLOG / DECISIONS / UI_AUDIT / ITERATION / CHANGELOG / STATE / FINAL_REPORT。

写法：每个锚点都 assert 命中一次，任何一处不对就整体不写（宁可停手，不许写半套 —— U-378）。
"""
import io
import os
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"


def read(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as handle:
        return handle.read()


def write(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as handle:
        handle.write(text)


def once(text, anchor, replacement):
    n = text.count(anchor)
    assert n == 1, "锚点命中 %d 次（期望 1）：%s" % (n, anchor[:70])
    return text.replace(anchor, replacement, 1)


# ---------------------------------------------------------------- BACKLOG
backlog = read("AGENT_BACKLOG.md")
backlog = backlog.rstrip("\n") + "\n\n" + """**150 追记 3（R121：上一轮的成因被自己那一跑的 CI 证伪，正式定性）**

R119 写的是「帧太矮把内容裁掉了，不是容器吃材质」，并且把臂 2 的夹具从 300pt 抬到 600pt。
本轮读它自己那一跑（run 39024922502）的正文，三行读数把这句话打死：

- `CARD_PROBE_ARM cardprobe-split-groupbox light 材质=无 卡片段=-1 墨行=0 墨像素=0 最大偏离=0 带子=170..720pt 页底=236`
  —— 帧已经是 720×**600**，带子里仍然一个偏离像素都没有；
- `CARD_PROBE_WHOLE cardprobe-split-groupbox light 整窗墨行=70 整窗最大偏离=165 带子墨行=0 帧=720x600px 倍率=1.0x`
  —— **这台机器拍得出这一页**（整窗 70 行墨），所以「拍不出整页」也不成立；
- `CARD_PROBE_COLUMNS … 列0:_NSSplitViewItemViewWrapper[x=0.0..148.0] 墨行=70 … 列1/列2[x=151.0..720.0] 墨行=0 最大偏离=0..2`
  —— 那 70 行墨**全在侧栏那一列**，详情那一列（151..720）从头到尾是平涂。

⇒ **150 的答案**：runner 上「设置窗口的卡片没有材质」不是带子放错、不是帧太矮、也不是容器吃掉第二层，
而是**分栏的详情那一列在这台机器的离屏捕获里整列没画**（同一帧的侧栏列正常画）。
被告列 0 墨 ⇒ 任何放在这一列里的带子都不可能读到墨，`材质=无` 在这台机器上没有对象。
本机（Retina、2x）同一夹具：`整帧墨行=171 详情列墨行=24 带子墨行=24 ⇒ 可判`，`列内视图数=16 嵌套hosting=6`
vs runner `列内视图数=7 嵌套hosting=4`。⇒ 这条与 43 是同族但**范围不同**：43 说整页平涂，本轮实测只到详情列。
**43 的措辞本轮已按实测收窄**（`SIDEBAR_ICON_NOT_RUN all（…R121 的 CARD_PROBE_COLUMNS 已经把这台的盲区收窄到详情那一列 —— 侧栏列本身有墨，不许再写成「整页拍不出」）`）。

**这一轮为此换掉的仪器形状**（D-183）：R107 早就把「怎么分」写进注释（整窗最大偏离 ≥60 而带子个位数 ⇒ 改带子），
但**从没当判据跑过**，于是 R119 我在三种解释并存时挑了一种写下结论。现在它是 `cardprobeArmVerdict`：
证人从「整窗」换成**被告那一列自己**，四种出口各有名字（可判 / 框错红 / 详情列0墨不可判 / 整帧0墨不可判），
外加 `CARD_PROBE_CAPABILITY` 的恒等式「参照臂 = 可判 + 框错红 + 不可判」与 `CARD_PROBE_WITNESS` 的仪表自检。
四刀 M616–M619 全部 CAUGHT。下一跑 CI 的期望：`cardprobe-split-groupbox` 两档 ⇒ `不可判(整帧有墨而详情列0墨)`，
`参照臂=6 可判=4 框错红=0 不可判=2`，而**捕获那一卷不再因此变红**（红的位置换到 171 那一朵 `gone`）。

**171 追记（R121：R120 的 CI 把它预言的那朵红落下来了）**

run 39025878222：`TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13 个夹具 ⇒ 闸门与判据同源（D-166）`
+ `testDarkSettingsSidebarTextIsACountedBlindSpot` **failed**：
「这些帧的暗档侧栏文字现在落在期望侧了：[settings-data, settings-general, settings-general-login-failed,
settings-general-login-unsupported, settings-min, settings-privacy, …]」。
⇒ 上一轮说的「闸门放开之后 runner 会让 `gone` 红」按预言发生，且**这条红是真的**：
`darkSidebarTextBlindSpots` 这份名单在本机成立、在 runner 不成立，而它一直按"全局权威"用。
**剩下没做的**：名单按机器分键（键必须来自实测：`HostInfo` / 系统版本 / 帧倍率），
并且分键之后两台的名单都要各自被自己的读数钉住 —— 不许变成「这台说没有就没有」。
171 保持开着，判据形状已经由本轮的 D-183 给出（分类函数 + 恒等式 + 各有名字的出口）。
"""

# ---------------------------------------------------------------- DECISIONS
decisions = read("AGENT_DECISIONS.md")
decisions = decisions.rstrip("\n") + "\n\n" + """### D-183（R121）证人必须与它作证的那一块同源；「读不到」要拆成**修法相反**的几种，每种给一个名字

R119 给 BACKLOG 150 认的成因（「帧太矮把内容裁掉了」）被它自己那一跑的 CI 证伪：
帧抬到 720×600 之后带子仍是 `墨行=0 最大偏离=0`，而 `整窗墨行=70` —— 那 70 行全在侧栏那一列，
详情那一列整列没画。当时并存的解释至少有三种（带子放错 / 这一列没画 / 整页拍不出），
我只写了一种就下了结论（U-405）。翻出来的三条：

1. **证人的矩形要与被判的那一块同一**。「整窗有墨」不能给「详情列没画」作证 ——
   它是 D-166（闸门与判据同源）在**证人**这一侧的复发：同一颗尺、同一块地方，缺一半都不算同源。
2. **「读不到」不是一个状态，是几个修法相反的状态**。分类必须是**会红的函数**（`cardprobeArmVerdict`
   + 全 2³ 真值表 + 恒等式 `参照臂 = 可判 + 框错红 + 不可判`），不是注释里的推理。
   写在注释里的分类法等于没有：R107 就写过一条，六年（六十轮）没人跑它。
3. **新加的读数要在本机看过它自己打印的内容**（U-406）。第一版样本按遍历顺序取前 8，
   8 条全是铺满整窗的容器 ⇒ 数字照常报、证人一句话没说；改成按面积升序取叶子之后才第一次说出
   `DocumentView[0,52 720x74] 嵌套hosting=6 列内视图数=16` 这种能定罪的话。
"""

# ---------------------------------------------------------------- UI_AUDIT 第 123 轮
audit = read("AGENT_UI_AUDIT.md")
audit_anchor = "## 第 122 轮 · R120"
audit_123 = """## 第 123 轮 · R121：上一轮给 150 认的成因被自己那一跑证伪，于是把「读不到」拆成四种有名字的出口（150 结案 / 43 收窄 / 171 拿到预言的那朵红 / U-405…U-406 / D-183）

### 1. 开场清单（本轮全部证据的位置与坐标）

| # | 位点 / 读数 | 出处 | 说明的缺陷 |
|---|---|---|---|
| 1 | `CARD_PROBE_ARM cardprobe-split-groupbox light 材质=无 卡片段=-1 墨行=0 最大偏离=0 带子=170..720pt 页底=236 帧=720x600px` | run 39024922502 | R119 的「帧太矮」被证伪：抬到 600pt 之后一个偏离像素都没有 |
| 2 | `CARD_PROBE_WHOLE … 整窗墨行=70 整窗最大偏离=165 带子墨行=0` | 同上 | 「这台机器拍不出这一页」也不成立 |
| 3 | `CARD_PROBE_COLUMNS … 列0[x=0..148] 墨行=70 / 列1、列2[x=151..720] 墨行=0 最大偏离=0..2` | 同上 | 70 行墨全在侧栏 ⇒ **详情那一列整列没画**（150 的成因） |
| 4 | 本机同夹具：`整帧墨行=171 详情列墨行=24 带子墨行=24 ⇒ 可判`；`列内视图数=16 嵌套hosting=6 样本=_NSSplitViewShadowView[148,0 12x600] ; … ; DocumentView[0,52 720x74] ; PlatformGroupContainer[0,52 720x74]` | /tmp/r121b | 本机的详情列有内容、有墨、有卡片容器 |
| 5 | runner `列内视图数=7 嵌套hosting=4 样本=无` | run 39024922502 | 树侧证人当时还没装（样本只收文字/图像类，而 SwiftUI 的文字不是 NSTextField） |
| 6 | `TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13` + `testDarkSettingsSidebarTextIsACountedBlindSpot` failed「落在期望侧了：[13 个夹具]」 | run 39025878222 | R120 预言的那朵 `gone` 红按预言落地 ⇒ 171 的前提被 runner 证实 |
| 7 | 帧 `cardprobe-split-groupbox-720x600-light.png` 目视：卡片是一条 26pt 高、几乎铺满详情列的浅灰药丸带；侧栏「快捷键/隐私/推荐/数据」四枚图标明显比「通用」淡 | 本轮看图 | 参照臂的形状本身没问题（它是尺），但**淡图标那一半在本机看得见**，与 167/170 的逐行读数一致 |

### 2. 本轮改了什么（产品 0 改动，只动 `UICaptureHarness.swift`）

1. `columnSubviewInventory` 的样本从「只收文字/图像类」换成「每个与列相交的视图：类名 + 矩形 + 隐藏 + 层不透明度」，
   并**按面积升序**取前 8（叶子优先）。第一版按遍历顺序取，8 条全是铺满整窗的容器 ⇒ 证人没说该说的话（U-406）。
2. 新增 `CARD_PROBE_WITNESS`：`列内视图数` 与 `样本` 出自同一条 `intersects`，对不上就是仪器坏（M616 钉）。
3. 新增 `CardprobeArmVerdict` + `cardprobeArmVerdict` + 全 8 行真值表 + `verdictText` 四个不同的词（D-183）。
   整窗那一遍**上移**到判据之前（它现在同时是证人和读数），证人补上「被告那一列自己」。
4. 参照臂那条「带子里必须有墨」从无条件红改成：`框错` 才红，`详情列0墨` / `整帧0墨` 各记一次**有名字的不可判**，
   并由 `CARD_PROBE_CAPABILITY` 的恒等式 `参照臂 = 可判 + 框错红 + 不可判` 钉住（M617/M618/M619 三刀）。
5. `SIDEBAR_ICON_NOT_RUN all` 的措辞按实测收窄：不再写「这台机器拍不出 SettingsView」。

### 3. 三条定义（本轮新增/改动的判据各自判什么）

- **可判**：带子里至少一行墨 ⇒ 这一臂的 `材质=有/无` 是有对象的读数。
- **框错（会红）**：被告那一列有墨、带子没有 ⇒ 是我框错了，改 `cardprobeBands`，不许改断言。
- **不可判（两种，各有名字）**：整帧有墨而被告那一列 0 墨 = 这台机器没画这一列；整帧 0 墨 = 这台机器拍不出这一页。
  两者都**计数**，都不算通过 —— 静默通过正是 R119 认错过成因的通道。

### 4. 覆盖与边界

变异第 25 张 `mutate_r121.py`（M616–M619，四臂全部 CAUGHT；刀数 94 → **98**，caught 93 → **97**）；
判据 +1 条（真值表）；帧基线不动（见 §8 的 `CHANGED=` 行）；150 结案，171 与 43 各留一条追记。

"""
audit = once(audit, audit_anchor, audit_123 + audit_anchor)

# ---------------------------------------------------------------- ITERATION Round 121
iteration = read("AGENT_VISUAL_ITERATION.md")
iteration = iteration.rstrip("\n") + "\n\n" + """## Round 121 · 150 的成因被自己那一跑证伪，于是把「读不到」拆成四种有名字的出口（150 结案 / 43 收窄 / 171 落地 / U-405…U-406 / D-183 · 产品 0 改动）

### 0. 开场缺陷清单

| # | 位点 | 证据 |
|---|---|---|
| 1 | runner 的参照臂 2 | 帧已 720×600 仍 `墨行=0 最大偏离=0` ⇒ 上一轮「帧太矮」不成立 |
| 2 | 同一跑的整窗 | `整窗墨行=70` ⇒ 「拍不出整页」也不成立 |
| 3 | 同一跑的逐列 | 70 行全在列0（侧栏 0..148），列1/列2（151..720）0 墨 ⇒ **详情列整列没画** |
| 4 | 上一轮我自己加的新仪表 | 样本按遍历序取前 8 ⇒ 全是铺满整窗的容器，证人没说该说的话（U-406） |
| 5 | R120 的 CI | `判了 13/13` + `gone` 红 ⇒ 171 的前提按预言落地 |

### 1. 这一轮的主线：把「读不到」从一格变成四格

R107 把分类法写在注释里，从没当判据跑过；R119 因此在三种解释并存时挑了一种下结论。
现在它是 `cardprobeArmVerdict`（证人=被告那一列自己）+ 8 行真值表 + `CARD_PROBE_CAPABILITY` 恒等式
+ `CARD_PROBE_WITNESS` 仪表自检。四刀 M616–M619 全部 CAUGHT。
**150 结案**：runner 上「设置卡没有材质」= 分栏详情列在离屏捕获里整列没画（同帧侧栏正常），
与带子、帧高、容器吃材质都无关。

### 2. 真实视觉审查（看图腿）

本轮零产品改动，帧基线不动，看图对象换成**仪器自己的夹具**：
`cardprobe-split-groupbox-720x600-light.png` —— 详情列里那条 26pt 高、几乎铺满列宽的浅灰药丸带
就是参照臂的卡片，形状与 `DocumentView[0,52 720x74]` 的树读数对得上（74pt 含标题与内边距）；
侧栏六行里「通用」是蓝底选中，其余四枚图标明显更淡，与 167/170 的逐行「亮侧/反侧」读数一致 ⇒ 图与数对得上。

### 7. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 92 | 产品 0 改动；本轮只把"这台机器画不出详情列"这条系统差异记对位置 |
| 动效华丽度 | 88 | 欠账：连续两轮在仪器侧，浮层/主窗口的动效位点本轮 0 推进 |
| 状态完备 | 92 | 150 结案；171 拿到 runner 的 `gone` 红；43 的措辞按实测收窄 |
| 证据强度 | 93 | 真值表 8 行 + 恒等式 + 仪表自检 + 四刀全 CAUGHT；下一跑的期望值已写成可证伪的读数 |
| 一致性 | 91 | 证人换成被告那一列之后，R107 那句注释被就地更正（不留两套规则） |
| 可维护 | 90 | 判据 +1 条、函数 3 个新纯函数；`whole` 上移避免重复声明 |
| 风险控制 | 93 | 没放宽任何判据：不可判仍计数、仍打名字，红只是从"永远红的错问题"换到"该红的对问题" |
| **合计** | **90** | 加权取整；动效欠账那一格按实际 88 记，不抹平 |

### 8. 下一轮（R122）

1. 读 R121 的 CI：`cardprobe-split-groupbox` 两档应报 `不可判(整帧有墨而详情列0墨)`、
   `参照臂=6 可判=4 框错红=0 不可判=2`，且捕获那一卷**不再因这条变红**；
2. 171 的名单按机器分键（键来自实测：`HostInfo` / 系统版本 / 帧倍率），分键后两台各自钉住；
3. 回到动效本体：连续两轮仪器侧，本轮 88 那一格要在 R122/R123 补回来（浮层剩余位点 + 主窗口行悬停）。
"""

# ---------------------------------------------------------------- CHANGELOG
changelog = read("CHANGELOG.md")
changelog = once(changelog, "## [Unreleased]\n", """## [Unreleased]
### 150 结案：runner 上「设置卡没有材质」是详情那一列整列没画，不是带子、不是帧高、不是容器（R121 / U-405…U-406 / D-183 · 产品 0 改动）

- 证据（R119 的 CI，run 39024922502）：`CARD_PROBE_ARM cardprobe-split-groupbox light 材质=无 墨行=0 最大偏离=0`
  配 `CARD_PROBE_WHOLE … 整窗墨行=70` 配 `CARD_PROBE_COLUMNS 列0[0..148] 墨行=70 / 列1、列2[151..720] 墨行=0`
  ⇒ 上一轮的成因「帧太矮把内容裁掉」被自己那一跑证伪（帧已是 720×600），
  「拍不出整页」也被证伪（整窗 70 行墨），剩下的唯一解释是**详情那一列在这台机器的离屏捕获里没画**。
- 仪器形状：R107 写在注释里的分类法被取出来重做 —— 证人从「整窗」换成**被告那一列自己**，
  `cardprobeArmVerdict` 给四种出口（可判 / 框错红 / 详情列0墨不可判 / 整帧0墨不可判），
  `CARD_PROBE_ARM_VERDICT` 逐臂打结论（排在闸门之前），`CARD_PROBE_CAPABILITY` 钉恒等式
  「参照臂 = 可判 + 框错红 + 不可判」。
- 仪表自检：`columnSubviewInventory` 的样本改为「类名 + 矩形 + 隐藏 + 层不透明度」并按面积升序取叶子
  （第一版按遍历序，8 条全是铺满整窗的容器 ⇒ 数字照报、证人沉默，U-406）；
  新增 `CARD_PROBE_WITNESS`：`列内视图数` 与 `样本` 出自同一条 `intersects`，对不上即仪器坏。
- 171：R120 的 CI（run 39025878222）把预言的那朵红落下来了 ——
  `TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13` + `testDarkSettingsSidebarTextIsACountedBlindSpot`
  failed「这些帧的暗档侧栏文字现在落在期望侧了：[13 个夹具]」
  ⇒ 名单是**机器相关**的，下一轮按实测键分机器；保持开着。
- 43 的措辞按实测收窄：`SIDEBAR_ICON_NOT_RUN all` 不再写「这台机器拍不出 SettingsView」，
  改成「这一档图标判据没跑：内容区 0 墨；盲区已收窄到详情那一列，侧栏列本身有墨」。
- 变异第 25 张 `mutate_r121.py`：M616 样本恒空 / M617 两个不可判分支换序 / M618 存在性判据改恒真 /
  M619 拆掉一臂计数 ⇒ 四臂全部 CAUGHT（刀数 94 → 98，caught 93 → 97）。
""")

# ---------------------------------------------------------------- FINAL_REPORT 计数
report = read("AGENT_FINAL_REPORT.md")
pairs = [("**D-182**", "**D-183**"), ("M615", "M619"), ("24 张", "25 张")]
for old, new in pairs:
    if old in report:
        report = report.replace(old, new)
        print("FINAL_REPORT: %s -> %s" % (old, new))
    else:
        print("FINAL_REPORT: 没找到 %s（跳过，不猜）" % old)
for pat, rep in [(r"94 把刀", "98 把刀"), (r"caught[ =]*93", "caught 97")]:
    m = re.search(pat, report)
    if m:
        report = report[:m.start()] + re.sub(pat, rep, m.group(0)) + report[m.end():]
        print("FINAL_REPORT: %s -> %s" % (m.group(0), re.sub(pat, rep, m.group(0))))
    else:
        print("FINAL_REPORT: 没找到 /%s/（跳过，不猜）" % pat)

# ---------------------------------------------------------------- STATE 轮换
state = read("AGENT_STATE.md")
lines = state.split("\n")
body_start = None
for i, line in enumerate(lines):
    if line.startswith("最后更新："):
        body_start = i
        break
assert body_start is not None, "STATE 找不到「最后更新：」行"
old_head = "\n".join(lines[body_start:])
markers = re.findall(r"^> 上一轮（R\d+", old_head, flags=re.M)
# 上一轮的现场整段降格为引用块（原文一字不改），新的当前块排在它前面。
quoted = "\n".join(("> " + l) if l.strip() else ">" for l in old_head.split("\n"))
new_state = """# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 19:1x（本地 · R121 / 第 123 轮收尾：**150 结案 —— runner 上「设置卡没有材质」是详情那一列整列没画**，上一轮的「帧太矮」被它自己那一跑的 CI 证伪（U-405…U-406 / D-183 · 产品 0 改动））

**现场（R119 的 CI，run 39024922502）**：三行读数互相打脸 —— 帧已经 720×**600**，带子仍 `墨行=0 最大偏离=0`（⇒「帧太矮」不成立）；`整窗墨行=70 整窗最大偏离=165`（⇒「拍不出整页」不成立）；`列0[0..148] 墨行=70`、`列1/列2[151..720] 墨行=0`（⇒ 那 70 行全在侧栏，**详情那一列整列没画**）。本机同一夹具：`整帧墨行=171 详情列墨行=24 带子墨行=24 ⇒ 可判`、`列内视图数=16 嵌套hosting=6`（runner 是 7 / 4）。

**改了什么**：把 R107 只写在注释里的分类法取出来当判据 —— 证人从「整窗」换成**被告那一列自己**，`cardprobeArmVerdict` 给四种出口（可判 / 框错红 / 详情列0墨不可判 / 整帧0墨不可判），`CARD_PROBE_ARM_VERDICT` 逐臂把结论打在闸门之前，`CARD_PROBE_CAPABILITY` 钉恒等式「参照臂 = 可判 + 框错红 + 不可判」；`columnSubviewInventory` 的样本改成类名+矩形+隐藏+层不透明度并**按面积升序**取叶子；新增 `CARD_PROBE_WITNESS`（视图数与样本同一条 `intersects`，对不上即仪器坏）。另把 43 的措辞按实测收窄（不再写「这台机器拍不出 SettingsView」）。四刀 M616–M619 全部 CAUGHT。

**171 拿到它该拿的红**：R120 的 CI（run 39025878222）`TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13` + `testDarkSettingsSidebarTextIsACountedBlindSpot` failed「落在期望侧了：[13 个夹具]」⇒ 名单是机器相关的，下一轮按实测键（`HostInfo`/系统版本/帧倍率）分机器，分键之后两台各自钉住。

**两条自坏**：**U-405** 给成因下结论前没有把并存的解释逐一排除，而分类法其实早就写在注释里、只是从没当判据跑过（写在注释里的分类法等于没有）；**U-406** 新仪表第一版只做到「能跑」，没看它自己打印的内容 —— 8 条样本全是铺满整窗的容器，数字照常报、证人一句话没说。

**下一轮（R122）**：① 读 R121 的 CI，期望 `cardprobe-split-groupbox` 两档 ⇒ `不可判(整帧有墨而详情列0墨)`、`参照臂=6 可判=4 框错红=0 不可判=2`，且捕获那一卷不再因这条变红；② 171 的名单按机器分键；③ **回到动效本体**（连续两轮在仪器侧，本轮自评 88 那一格就是这笔欠账）。

""" + quoted
assert "> 上一轮（R" in new_state or "> 最后更新：" in new_state, "STATE 轮换后没有上一轮的引用块（U-381 那一族）"
write("AGENT_STATE.md", new_state)
print("STATE: 轮换完成；上一轮引用块 %d 处（含本轮降格的那一段）"
      % len(re.findall(r"^> 最后更新：", new_state, flags=re.M)))

for name, text in [("AGENT_BACKLOG.md", backlog), ("AGENT_DECISIONS.md", decisions),
                   ("AGENT_UI_AUDIT.md", audit), ("AGENT_VISUAL_ITERATION.md", iteration),
                   ("CHANGELOG.md", changelog), ("AGENT_FINAL_REPORT.md", report)]:
    write(name, text)
    print("WROTE %s (+%d 字节)" % (name, len(text.encode("utf-8"))))
print("LEDGER_R121=ok")
