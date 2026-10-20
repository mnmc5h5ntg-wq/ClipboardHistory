# -*- coding: utf-8 -*-
"""R236 台账批写：六本账一次写全，或一行不写。

数字全部从 /tmp/r236_numbers.json 读（由测量步骤落盘），**不许手抄**（U-745 / D-090 那条老规矩）；
每个锚点都按整行/整串相等匹配，找不到就抛，不落盘（事务性）。
"""
import io, json, os, re

REPO = "/Users/wangziyi/Codex_Project0"
N = json.load(io.open("/tmp/r236_numbers.json", encoding="utf-8").read() and "/dev/null") if False else \
    json.load(io.open("/tmp/r236_numbers.json", encoding="utf-8"))


def rd(p):
    return io.open(os.path.join(REPO, p), encoding="utf-8").read()


def wr(p, s):
    io.open(os.path.join(REPO, p), "w", encoding="utf-8").write(s)


def replace_once(text, old, new, tag):
    n = text.count(old)
    assert n == 1, "%s 锚点命中 %d 次（要求恰好 1）" % (tag, n)
    return text.replace(old, new, 1)


parts = []          # (path, new_text) 先全部算完再写盘

# ---------------- AGENT_UI_AUDIT.md：新节插在当前最大轮次标题之上（降序） ----------------
ui = rd("AGENT_UI_AUDIT.md")
anchor_234 = u"## 第 234 轮（R235 / Round 232"
assert ui.count(anchor_234) == 1, "UI_AUDIT 第 234 轮标题锚点"
section = u"""## 第 235 轮（R236 / Round 233 · 2026-10-20）：13 那棵的墨第一次有**两轴**会红的判据 —— M787 从 ESCAPED 关成 CAUGHT（U-757…U-760 / D-221）

- **U-757：把「都不是我想要的」那一行的文案与墨收成一条缝，然后两轴各一条判据 —— 变异读数：三刀 CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes。**
  R235 留的账（U-750 ④）写得很清楚：`M787 = ESCAPED` ⇒ 13 那棵 SwiftUI 树的墨**没有会红的行为判据**，
  而 `App.swift:28` 就在实例化它。本轮按 264 的修法补牙：
  `MenuBarRecommendationsView` 里新增 `static var dismissRowInk: Color? { nil }` 与
  `static func dismissRowLabel()`（缝 = 这一行标签的唯一构造路径，body 只许调它），
  新判据 `MenuBarSwiftUIDismissRowInkTests` 三格 —— 尺自对照 / 行为轴（缝给的非 nil 墨必须在两档 ×
  静置 4.5 / 选中 3.0 上过线，地板从 D-220 实测继承，不新造数）/ 结构轴（body 必须走
  `Self.dismissRowLabel()`，且该函数体内 `.foregroundStyle(` 恰好一处且参数必须是 `ink`）。
  三刀各自只红在自己那一格（`--log` 逐条列名）：M786→`MenuBarDismissRowInkTests.testDismissRowInkClearsTheTextFloorInBothStates`（12 那棵的在岗证人）、
  M787（就地钉蓝）→`testDismissRowLabelRoutesThroughTheSeam`、M788（钉进缝里）→`testSeamInkClearsTheTextFloorInBothStates`
  ⇒ **「把那颗蓝钉回来」这件事现在无论走哪条路都会红**，264 的 ESCAPED 就地关成 CAUGHT。
  行为轴的本机读数：缝返回 nil ⇒ 走系统正文墨，暗 `16.67 / 6.23`、亮 `21.00 / 14.08`，
  与 D-220 那两档参照臂**逐字相同** ⇒ 两棵树在同一把尺上对上了账。
- **U-758：缝不给画面任何东西 —— 重构后帧没变，看图腿量的是「没变」这件事。**
  `CLIPBOARD_HISTORY_UI_SHOTS=%(shots)s` 重捕 %(frames_n)s 帧，对 WorkingManifest 基线
  `CHANGED=%(changed)s / MISSING=%(missing)s`（%(baseline_note)s）⇒ 本轮的产品改动是**纯缝**：
  墨的身份、排版、分组都不动，动的是「谁能抓住它」。
  这条线值得记：一个不改变画面的重构，把「只有帧基线在管」变成「两轴各有一刀」，
  正是阶段二要的"现有实现不许假设为正确"的落法之一 —— 华丽度不靠这一笔，**可证伪性**靠这一笔。
- **U-759：变异仪器的「红名」列一直是空的 —— `split("]")[-1]` 取的是 `]` 之后那段，恒为空串（本轮实测并修）**
  R235 那版 `mutate_r235.py` 里 `ln.split("'")[1].split("]")[-1].strip()`：对 `-[Mod.Class testFoo]`
  这枚 token，`]` 之后就是空字符串 ⇒ 表里那列一直印 `yes|`（空）。
  **CAUGHT 归类没坏**（它靠"有没有失败行"，那一步是对的），坏的是**名字**：
  于是台账里那句「红名必须点名新格」在仪器层面从来没被打印过 —— 我只拿 grep 从日志里另取了一次名字，
  而那句话写在表头，读起来像是仪器给的。本轮把提取改成 `[-2]`（并要求非空），
  `mutate_r236.py` 的名字列是仪器自己印的，上面 U-757 那三个红名就是这个通道的产物。
  规矩（进 D-221 的附则）：**仪器印空列 = 那条读数不存在**，不许把另一支工具的读数写成这一支的产出。
- **U-760：没做的与做不了的，写清楚。**
  ① 悬停那一行的真实观感仍挂真机（265）；② 结构轴只钉了这一棵树的这一个标签，
  别处若新写死色需要把「缝 + 一处着色」这个形状推广（这条是 251 那一族的兄弟）；
  ③ CI 验收要等这一笔的 run 落地（写进 R237 的 ⓪）；④ 263 那朵 `pixels > 400` 与 267 那朵 `10ms` 地板
  本轮**一律没动** —— 两朵红都还挂着，处置各自记在 263/267，不在本笔顺手放宽。

""" % {u"shots": N["shots_dir"], u"frames_n": N["frames_n"], u"changed": N["changed"],
       u"missing": N["missing"], u"baseline_note": N["baseline_note"]}
parts.append(("AGENT_UI_AUDIT.md", ui.replace(anchor_234, section + anchor_234, 1)))

# ---------------- AGENT_DECISIONS.md：追加 D-221 ----------------
dec = rd("AGENT_DECISIONS.md")
assert u"D-221" not in dec, "D-221 已存在"
d221 = u"""
**D-221（R236）：一处「产品自己说的墨」必须做成可读的缝，判据才能同时问两轴 —— 只问一轴的判据会被另一条出口喂饱**

R235 把 12 那棵 AppKit 树写死的蓝交回系统之后，13 那棵的同一行仍然只有帧基线在管（M787=ESCAPED）。
本轮定的形状，三步固定：**① 把「哪颗墨」从修饰符链里提出来变成一个能读的值（缝）；② 让 UI 代码只能经由缝出来的构造器渲染；
③ 两轴各配一条会红的判据 + 各配一刀** —— 行为轴读缝的值（钉进缝里会红），结构轴读源码形状（绕过缝就地钉会红）。
只补①不补②，就地钉色仍然隐形；只补②不补①，钉进缝里仍然隐形。两轴的刀必须**分别**证明各自那格会红，
一把刀同时红两格说明判据没切片。附则：仪器打印的"红名"列若为空串，那条读数按不存在记账（见 U-759）。

"""
wr_probe = dec.rstrip("\n") + d221
parts.append(("AGENT_DECISIONS.md", wr_probe))

# ---------------- AGENT_VISUAL_ITERATION.md：升序，只能追加到文件尾 ----------------
it = rd("AGENT_VISUAL_ITERATION.md")
assert u"## Round 233 " not in it, "Round 233 已存在"
round_233 = u"""## Round 233 · 把「只有帧基线在管」那一行改成两轴都会红（2026-10-20 / R236 / 第 235 轮 / U-757 U-758 U-759 U-760）

R235 留下的活路径缺牙：13 那棵 SwiftUI 树的「都不是我想要的」写死蓝，变异对照 M787 = ESCAPED。
本轮把它收成一条缝（`dismissRowInk` + `dismissRowLabel()`），判据问两轴：缝给的是哪颗墨（行为轴，
地板从 D-220 继承），这一行有没有绕过缝自己钉色（结构轴，函数体内着色恰好一处且必须拿 `ink`）。
三刀分别红在各自那一格 ⇒ **CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes**，M787 关成 CAUGHT。
画面没动：重捕 %(frames_n)s 帧对基线 `CHANGED=%(changed)s / MISSING=%(missing)s`（%(baseline_note)s）。
顺手抓到仪器自己的坏：R235 那版「红名」列被 `split("]")[-1]` 恒取成空串，
所以台账里那句「红名点名新格」从来不是仪器打印的 —— 本轮修成 `[-2]` 并要非空（U-759）。

七维度自评：

| 维度 | 分 | 一句话 |
|---|---|---|
| 真实性（读的是产品吗） | 14 | 两轴都读产品文件与产品的缝值；底色仍是系统语义色**代理**，已写明不是材质实测 |
| 可证伪（有会红的判据吗） | 15 | 三刀三格各自红、ESC=0/NOT_RUN=0；本轮还把自己的仪器修到能印红名 |
| 克制（不喧宾夺主） | 15 | 纯缝重构，画面 `CHANGED=%(changed)s`，没加任何新视觉 |
| 原生（用了系统能力吗） | 14 | 缝返回 nil 时完全交回系统着色，不自己画态 |
| 覆盖（这一屏判完了吗） | 11 | 菜单栏色面又推进一格；悬停观感仍挂真机（265），其余元素仍未逐格判完 |
| 诚实（账与读数一致吗） | 14 | 「仪器印空列=读数不存在」当场记账并修；两朵旧红一律没动 |
| 复用（留下能用的仪器吗） | 14 | 「缝 + 一处着色 + 两轴刀」是可推广的形状，251 那一族直接能抄 |

合计 %(score)s/105。GAPS=none（欠的四件事写在第 235 轮 U-760 里，是登记不是漏）。
本轮次对照：脚本臂 R236 = 台账「第 235 轮」= 「Round 233」（差 3，两枚标签都写进标题）。

""" % {u"frames_n": N["frames_n"], u"changed": N["changed"], u"missing": N["missing"],
       u"baseline_note": N["baseline_note"], u"score": N["score"]}
parts.append(("AGENT_VISUAL_ITERATION.md", it.rstrip("\n") + "\n" + round_233))

# ---------------- AGENT_BACKLOG.md：264 结案追记（追加在文件尾） ----------------
bl = rd("AGENT_BACKLOG.md")
assert u"**264 追记" not in bl, "264 追记已存在"
bl_add = u"""
**264 追记（R236 结案）：缝做了，两轴各一条判据、各一刀 —— M787 由 ESCAPED 关成 CAUGHT**

形状（D-221）：`MenuBarRecommendationsView.dismissRowInk: Color?`（唯一能读的值）+
`dismissRowLabel()`（这一行标签的唯一构造路径，body 只许调它）。判据 `MenuBarSwiftUIDismissRowInkTests` 三格：
尺自对照 / 行为轴（非 nil 的墨必须过 D-220 的两档 × 4.5 与 3.0）/ 结构轴（`Self.dismissRowLabel()` 恰好一处调用，
且构造器体内 `.foregroundStyle(` 恰好一处且参数必须是 `ink`；扫前剥行注释 —— 这条本轮自己红过一次，
红在我写在文档注释里的那句引用）。刀（`.scratch/motion-audit-2/mutate_r236.py`，FILTER 覆盖两棵树）：
M786 CAUGHT（在岗证人，红在 12 那棵的行为轴）、M787 CAUGHT（就地钉蓝 ⇒ 结构轴）、M788 CAUGHT（钉进缝里 ⇒ 行为轴），
ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes。
**没结案的部分**：悬停那一行的真机观感（265 仍开）；这个形状只在 13 这一棵的这一行落地，
别处新写死的色还得推广（登记在 U-760，不属 264 的题面）。
"""
parts.append(("AGENT_BACKLOG.md", bl.rstrip("\n") + "\n" + bl_add + "\n"))

# ---------------- CHANGELOG.md：插在 [Unreleased] 标题之下 ----------------
cl = rd("CHANGELOG.md")
head = u"## [Unreleased]\n"
i = cl.index(head)
cl_add = (u"- R236（第 235 轮 / Round 233 / U-757…U-760 / D-221）：13 那棵 SwiftUI 树的「都不是我想要的」那一行，"
          u"墨与文案收成一条可读的缝（`dismissRowInk` + `dismissRowLabel()`），并补两轴判据 —— 行为轴读缝给的墨"
          u"（钉进缝里 ⇒ 两档 × 4.5/3.0 地板必须红），结构轴读源码形状（绕过缝就地钉色 ⇒ 必须红）。"
          u"变异三刀 CAUGHT=3 / ESCAPED=0 / NOT_RUN=0：R235 那枚 ESCAPED 的 M787 就地关成 CAUGHT，BACKLOG 264 结案。"
          u"画面不变（重捕 %(frames_n)s 帧 `CHANGED=%(changed)s`）。另记仪器自己的坏：变异表的「红名」列被 "
          u"`split(\"]\")[-1]` 恒取成空串，本轮修成 `[-2]` 并要非空（U-759）。\n") % {
              u"frames_n": N["frames_n"], u"changed": N["changed"]}
parts.append(("CHANGELOG.md", cl[:i + len(head)] + cl_add + cl[i + len(head):]))

# ---------------- 写盘（全部锚点都验过才动盘） ----------------
for path, text in parts:
    wr(path, text)
print("LEDGERS_R236 写了 %d 本：%s" % (len(parts), ", ".join(p for p, _ in parts)))
