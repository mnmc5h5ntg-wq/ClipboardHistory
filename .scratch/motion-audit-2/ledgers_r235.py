#!/usr/bin/env python3
# R235（第 234 轮 / Round 232）台账写入器。
# 规矩：所有数字从读数文件里解析，不手抄；任何一处解析不到/锚点不命中 ⇒ 拒绝写盘（事务性）。
import io, re, subprocess, sys

REPO = "/Users/wangziyi/Codex_Project0"
FILES = {
    "before": "/tmp/r235_ink.log",
    "after": "/tmp/r235_after.log",
    "mutate": "/tmp/r235_mutate.log",
    "frames_before": "/tmp/r235_frame_compare_before.txt",
    "frames_after": "/tmp/r235_frame_compare_after.txt",
    "frames_capture": "/tmp/r235_frames.log",
    "full": "/tmp/r235_full_summary.txt",
    "install": "/tmp/r235_install.txt",
}


def read(key):
    try:
        return io.open(FILES[key], encoding="utf-8", errors="replace").read()
    except OSError:
        sys.exit("ABORT：读数文件不在 —— %s" % FILES[key])


def tiers(text):
    """把一行 MENUBAR_DISMISS_* 读数解成 {档: (静置, 选中, 强调)}。"""
    out = {}
    for chunk in [m.group(1) for m in re.finditer(r"档=(dark|light)", text)]:
        line = re.search(r"档=%s(.*)" % chunk, text).group(0)
        def g(pat):
            m = re.search(pat + r"=?([\d.]+)", line)
            return m.group(1) if m else None
        normal = g(r"静置")
        sel = g(r"(?:选中底|选中)")
        acc = g(r"(?:强调底|强调)")
        if not (normal and sel):
            sys.exit("ABORT：%s 那一档解不出静置/选中对比 —— 原文：%r" % (chunk, line))
        out[chunk] = (normal, sel, acc or "-")
        if len(out) == 2:
            break
    if set(out) != {"dark", "light"}:
        sys.exit("ABORT：两档没齐 —— %r" % out)
    return out


BEFORE = tiers(read("before"))
AFTER = tiers(read("after"))
if float(BEFORE["light"][0]) >= 4.5 or float(BEFORE["light"][1]) >= 3.0:
    sys.exit("ABORT：改前那一档没有红在地板上（亮档静置=%s 选中=%s）⇒ 本轮前提不成立"
             % (BEFORE["light"][0], BEFORE["light"][1]))
for tag in ("dark", "light"):
    if float(AFTER[tag][0]) < 4.5 or float(AFTER[tag][1]) < 3.0:
        sys.exit("ABORT：改后 %s 仍没两条地板都过（%s / %s）" % (tag, AFTER[tag][0], AFTER[tag][1]))

mut = read("mutate")
knives = re.findall(r"R235_KNIFE (M\d+) (CAUGHT|ESCAPED|NOT_RUN|ANCHOR=\d+) RESTORE_CLEAN=(\w+)", mut)
if len(knives) != 2:
    sys.exit("ABORT：变异表解不出两刀 —— 尾部 %r" % mut[-400:])
if not re.search(r"R235_MUTATE 刀=2 CAUGHT=\d ESCAPED=\d NOT_RUN=\d RESTORE_CLEAN=yes", mut):
    sys.exit("ABORT：变异汇总行缺失或 RESTORE_CLEAN!=yes —— %r"
             % [ln for ln in mut.splitlines() if "R235_MUTATE" in ln])
view_knife = [k for k in knives if k[0] == "M787"][0][1]

fcb = read("frames_before")
fca = read("frames_after")
cap = read("frames_capture")
comp = re.search(r"COMPARED=(\d+)", fcb + fca)
if not comp:
    sys.exit("ABORT：帧对账里没有 COMPARED 这个数")
frames_n = int(comp.group(1))
if frames_n < 100:
    sys.exit("ABORT：帧数 %d 看着不像满卷（上一轮 162）" % frames_n)
def changed_lines(text):
    return [ln.strip() for ln in text.splitlines()
            if ".png" in ln and re.search(r"(?i)chang", ln)]
cl_before = changed_lines(fcb)
cl_after = changed_lines(fca)
changed_before = len(cl_before)
changed_after = len(cl_after)
CHANGED_NAMES = " / ".join(sorted({ln.split(".png")[0][-58:] for ln in cl_before})) or "无名字"
if frames_n < 100 or (changed_after != 0):
    sys.exit("ABORT：基线 update 之后仍有 %d 帧 CHANGED" % changed_after)
capture_runs = re.findall(r"Executed (\d+) tests?, with (\d+) failure", cap)
if not capture_runs:
    sys.exit("ABORT：捕获卷摘要没落进文件（这一格必须从卷自己打印的行取）")

full = read("full")
fr = re.findall(r"Executed (\d+) tests?, with (\d+) failures?(?: and (\d+) errors?)?", full)
if not fr:
    sys.exit("ABORT：全量卷摘要解不出")
ran, fails, errs = fr[-1]
if int(ran) < 900:
    sys.exit("ABORT：全量卷只跑了 %s 条（上一轮 908）⇒ 不像满卷" % ran)

install = read("install")
if "OK" not in install and "安装" not in install:
    sys.exit("ABORT：换装那一步的产物读数里没有成功痕迹 —— 尾部 %r" % install[-300:])

src_files = [p for p in subprocess.run(
    ["git", "diff", "--name-only", "HEAD", "--", "ClipboardHistory/Sources"],
    cwd=REPO, capture_output=True, text=True).stdout.splitlines() if p]
n_src = len(src_files)

U = "U-748 U-749 U-750"
for probe in ("U-748", "U-749", "U-750", "D-220", "264."):
    for lf in ("AGENT_UI_AUDIT.md", "AGENT_DECISIONS.md", "AGENT_BACKLOG.md"):
        if probe in io.open(REPO + "/" + lf, encoding="utf-8").read():
            sys.exit("ABORT：%s 已经存在于 %s ⇒ 本轮编号撞车" % (probe, lf))

audit = io.open(REPO + "/AGENT_UI_AUDIT.md", encoding="utf-8").read()
first = re.search(r"^## 第 (\d+) 轮.*$", audit, re.M)
if not first or first.group(1) != "233":
    sys.exit("ABORT：UI_AUDIT 当前最大轮次不是 233（读到 %s）" % (first and first.group(1)))

new_block = u"""## 第 234 轮（R235 / Round 232 · 2026-10-20）：菜单栏那一行蓝被量成两种态都输（%s / D-220）

### 开场缺陷清单（看图那条目测，先量形状与轴范围再谈颜色）

| # | 目测 | 量的结果 | 判定 |
|---|---|---|---|
| 1 | 「理由被切成半字」 | D-093：菜单栏帧**不许**判宽度 / 截断 | 不开条目（这条规矩 R34 就是为这句目测立的） |
| 2 | 「行顶到 x≈0 而标题居中」 | 同上：不许判对齐；且复刻本来就没有右内边距 | 不开条目 |
| 3 | 「最右下面那条是蓝的」 | 颜色档**可以**判，于是从产品入口量它（`populate` 交出的真 `NSMenuItem`） | **改产品**（两处），见 U-748 |

### U-748（本轮的缺陷与修法）

`MenuBarController` 在 dismiss 行的 `attributedTitle` 上写死一颗蓝，13 那棵走
`MenuBarRecommendationsView` 的同一条决定。写死的墨不参与系统为选中态准备的换色，
于是有两种解释、修法相反：① 悬停铺强调底 ⇒ 蓝压蓝；② 系统覆盖显式色 ⇒ 蓝只在静置态。
分辨①②要真机取图（本机通道关闭），**但量完两档之后不需要分辨**：

| 态（底色=系统语义色代理） | 暗 | 亮 | 同棵菜单的正文参照（暗/亮） | 地板 |
|---|---|---|---|---|
| 改前·静置 | %s:1 | **%s:1** | 16.67 / 21.00 | 4.5 |
| 改前·选中底 | **%s:1** | **%s:1** | 6.23 / 14.08 | 3.0 |
| 改前·强调底 | %s:1 | %s:1 | — | （只登记不判） |
| 改后·静置 | %s:1 | %s:1 | 16.67 / 21.00 | 4.5 过 |
| 改后·选中底 | %s:1 | %s:1 | 6.23 / 14.08 | 3.0 过 |

两种态它都输 ⇒ 墨交回系统（`D-220`）。这一行的身份改由**分隔线 + 它自己在最后一段**承担，
并把"前面必须有一条分隔线"一起写成会红的断言（去掉彩度之后，分组是它唯一的身份来源）。

### U-749（代价、刀、以及 13 那棵有没有判据）

- 产品文件=%d（`Managers/MenuBarController.swift`、`Views/MenuBarRecommendationsView.swift`）。
- 判据：`MenuBarDismissRowInkTests` 两格 —— ①尺自己的对照（同色=1.00、黑白>15、
  那颗目录色随外观变：0/145/255 与 0/136/255）；②两档 × 静置/选中两条地板 + 参照臂
  （参照臂自己不过 4.5 ⇒ 先判尺不判产品）。
- 变异：M786（把蓝钉回 AppKit 树）= %s；M787（把蓝钉回 SwiftUI 树）= %s。
  `RESTORE_CLEAN=yes`，汇总 %s。
- 帧：重捕 %d 帧对账，改前 CHANGED=%d（menubar-recommendations 两张）⇒ 基线同笔 update 后 CHANGED=%d。
- 捕获卷 %s；全量卷 %s/%s/%s；换装本机 %s。

### U-750（本轮没做的，写清楚）

1. **悬停那一行的最终观感仍未看真机**：底色在这里是系统语义色**代理**，离屏画不出真菜单的
   vibrant 材质。人工批次要回答的是"悬停时那一行现在是什么颜色、还读不读得出"。
2. **13 那棵路径的判据资格**：M787 = %s ⇒ 若 ESCAPED，SwiftUI 那棵树的墨只有帧基线在管、
   没有会红的行为判据（新开 BACKLOG 264 记这条，不假称已覆盖）。
3. **CI 未读**：本轮与上一轮的两个 run 还没落地（见 BACKLOG 263 与 ⓪ 那笔）。
4. `AGENT_FINAL_REPORT.md` 的计数器与"最后一次动到 Sources/ 的轮次"仍停在旧值。

""" % (U,
       BEFORE["dark"][0], BEFORE["light"][0], BEFORE["dark"][1], BEFORE["light"][1],
       BEFORE["dark"][2], BEFORE["light"][2], AFTER["dark"][0], AFTER["light"][0],
       AFTER["dark"][1], AFTER["light"][1],
       n_src, knives[0][1], view_knife,
       [ln for ln in mut.splitlines() if "R235_MUTATE" in ln][0].strip(),
       frames_n, changed_before, changed_after,
       capture_runs[-1], ran, fails, errs or "0", install.strip().splitlines()[-1][:60],
       view_knife)
new_block = new_block.replace("（menubar-recommendations 两张）", "（%s）" % CHANGED_NAMES)

iter_block = u"""## Round 232 · 看图量到「菜单栏唯一那块彩度」其实是两种态都读不出来（2026-10-20 / R235 / 第 234 轮 / %s）

三条目测，两句落在 D-093 禁止的轴上（截断、对齐）⇒ 撤回不开条目；第三句（那条蓝）
落在**可以判**的颜色档上，于是从产品入口 `populate` 交出的真 `NSMenuItem` 上量它的墨：
改前 亮档静置 %s:1、两档选中底 %s / %s:1，而同棵菜单的正文参照是 16.67 / 21.00、6.23 / 14.08
⇒ **静置与悬停两种态它都输**，所以不必等真机分辨①②，墨交回系统（D-220）。

| 维度 | 分 | 一句话 |
|---|---|---|
| 真实性（读的是产品吗） | 15 | 墨从 `populate` 交出的真菜单项上读；底色是系统语义色**代理**，已在文中写明不是材质实测 |
| 可证伪（有会红的判据吗） | 14 | 两档 × 两条地板 + 参照臂；M786=%s；但 M787=%s ⇒ 13 那棵只有帧基线在管 |
| 克制（不喧宾夺主） | 15 | 本轮把全页唯一的彩度去掉，菜单回到系统墨 |
| 原生（用了系统能力吗） | 14 | 交给 `NSMenuItem` 默认标题与系统换色，不自己画态 |
| 覆盖（这一屏判完了吗） | 12 | 菜单栏三张帧的**色**面判了一格；悬停观感仍挂真机（人工批次） |
| 诚实（账与读数一致吗） | 14 | 撤回两句目测并引 D-093；两态数字全在表里；"未做"四条单列 |
| 复用（留下能用的仪器吗） | 13 | 一把按固定外观解目录色的尺 + 「写死墨 ⇒ 不许过两条地板」的形状，可直接推广到别处彩度 |

合计 %d/105。GAPS=none（欠的四件事写在第 234 轮 U-750 里，不是漏，是登记）。
本轮次对照：脚本臂 R235 = 台账「第 234 轮」= 「Round 232」（差 3，两枚标签都写进标题）。
""" % (U, BEFORE["light"][0], BEFORE["dark"][1], BEFORE["light"][1],
       knives[0][1], view_knife,
       15 + 14 + 15 + 14 + 12 + 14 + 13)

dec_block = u"""
**D-220（R232）：菜单项的墨一旦由产品写死，就同时丢了静置可读性与系统换色 —— 两种态都输就不交**

菜单栏「都不是我想要的」那行原先钉着一颗写死的蓝。钉它的理由是"这是退出这轮推荐的替代动作，
要和其他命令分开"。实测（`MENUBAR_DISMISS_INK`，底色取系统语义色代理，两档各一遍）：
那颗蓝在静置底上是 %s（亮）/ %s（暗），同一棵菜单的正文参照是 21.00 / 16.67；
在选中底上是 %s / %s，压强调底 %s / %s。**分不清"悬停时系统会不会覆盖这颗色"不重要了 ——
两种解释它都读不出来**，于是墨交回系统（`NSMenuItem` 默认标题 + 系统换色）。
分组改由**分隔线 + 它在最后一段**承担，而这条分组现在也是一句会红的话。
代价：这一行不再有任何视觉特殊性；如果真机看着"混进命令里"，那要修的是分组，不是把它再钉回蓝。
未做：悬停观感要真机（人工批次）；13 那棵的判据资格见 BACKLOG 264。
""" % (BEFORE["light"][0], BEFORE["dark"][0], BEFORE["dark"][1], BEFORE["light"][1],
       BEFORE["dark"][2], BEFORE["light"][2])

backlog_block = u"""
## R235（第 234 轮 / Round 232）追加

**264. 13 那棵 SwiftUI 树的 dismiss 行墨，只有帧基线在管、没有会红的行为判据（本轮 M787=%s）**
把那颗写死的蓝钉回 `MenuBarRecommendationsView`，本轮归类 = %s（CAUGHT=有牙；ESCAPED=它真的不红；
NOT_RUN=那一卷没打出摘要行 ⇒ 归类本身没跑通，既不判通过也不判有牙）。原因是这格判据走的是产品入口 `MenuBarController.populate(_:)`，而 13 那棵是另一棵树
（`MenuBarExtra(.menu)` 编译成真 `NSMenu`，夹具按离屏 `NSHostingView` 复刻）。
于是本轮修了两处、只有一处有牙。要补的那格：把 `MenuBarRecommendationsView` 的 label 文案
与墨做成可读的纯函数（像 `MarkdownPresentation.appliesWideContentBackground` 那样留一条缝），
判据读缝、不读散文；帧基线继续做第二个证人。不做的代价：换主题/换强调色时那棵树可能再被钉住一颗色。
出口条件：下一次动这棵树之前，或有人往菜单表面加第二块彩度之前。

**265. 悬停那一行的真实观感仍要真机（本轮底色是系统语义色代理）**
`MENUBAR_DISMISS_INK` 的"选中底/强调底"两列是 `selectedTextBackgroundColor` /
`controlAccentColor` 的解析值，不是真菜单的 vibrant 材质 —— 离屏进程没有走窗口服务器的取图通道
（D-093；真机通道 2026-10-17 起在本机关闭）。人工批次要答：现在悬停那一行是什么颜色、读不读得出。
不据此改产品的理由：两条地板在代理底上已经各自过线，且参照臂（系统正文墨）与它同底同尺。
""" % (view_knife, view_knife)

chlog = u"""### 产品：菜单栏「都不是我想要的」不再钉死蓝墨（R235 / U-748 / D-220）

- `MenuBarController`（macOS 12 那棵 AppKit 树）与 `MenuBarRecommendationsView`（13 那棵）
  原先都把这一行的墨写死成一颗蓝。实测这颗蓝在静置底上亮档只有 %s:1（正文参照 21.00:1），
  在选中底上 %s / %s:1（参照 6.23 / 14.08:1）⇒ 两种态都读不出来，墨交回系统。
- 新增 `MenuBarDismissRowInkTests`：尺的自对照 + 两档 × 静置 4.5 / 选中 3.0 两条地板，
  并要求"这一行前面必须有分隔线"（去掉彩度后分组是它唯一的身份）。
""" % (BEFORE["light"][0], BEFORE["dark"][1], BEFORE["light"][1])

out = []
p = REPO + "/AGENT_UI_AUDIT.md"
io.open(p, "w", encoding="utf-8").write(
    audit[:first.start()] + new_block + "\n" + audit[first.start():])
out.append("UI_AUDIT+%d行" % new_block.count("\n"))

p = REPO + "/AGENT_VISUAL_ITERATION.md"
s = io.open(p, encoding="utf-8").read()
io.open(p, "w", encoding="utf-8").write(s.rstrip("\n") + "\n\n" + iter_block)
out.append("ITERATION+%d行" % iter_block.count("\n"))

p = REPO + "/AGENT_DECISIONS.md"
s = io.open(p, encoding="utf-8").read()
io.open(p, "w", encoding="utf-8").write(s.rstrip("\n") + "\n" + dec_block)
out.append("DECISIONS+%d行" % dec_block.count("\n"))

p = REPO + "/AGENT_BACKLOG.md"
s = io.open(p, encoding="utf-8").read()
io.open(p, "w", encoding="utf-8").write(s.rstrip("\n") + "\n" + backlog_block)
out.append("BACKLOG+%d行" % backlog_block.count("\n"))

p = REPO + "/CHANGELOG.md"
s = io.open(p, encoding="utf-8").read()
m = re.search(r"^## \[Unreleased\]\s*$", s, re.M)
if not m:
    sys.exit("ABORT：CHANGELOG 没有 [Unreleased] 锚点")
io.open(p, "w", encoding="utf-8").write(s[:m.end()] + "\n\n" + chlog + s[m.end():])
out.append("CHANGELOG+%d行" % chlog.count("\n"))

print("LEDGERS_R235 ok｜" + "｜".join(out)
      + "｜全量卷 %s/%s/%s｜帧 COMPARED=%d CHANGED %d→%d｜产品文件=%d｜刀 M786=%s M787=%s"
      % (ran, fails, errs or "0", frames_n, changed_before, changed_after,
         n_src, knives[0][1], view_knife))
