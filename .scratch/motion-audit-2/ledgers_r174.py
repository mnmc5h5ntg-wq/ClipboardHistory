#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174 的台账批写：清账表「浮层/底部说明」换主语 + 204/205 两笔开账，数字全部从本轮日志解析。"""
import io
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
L = {"surface": "/tmp/r174_surface.log", "absence": "/tmp/r174_absence.log",
     "align": "/tmp/r174_align.txt", "frames": "/tmp/r174_frames.txt",
     "tokens": "/tmp/r174_tokens.txt", "battery": "/tmp/r174_battery.log"}


def read(p):
    if not os.path.exists(p):
        raise SystemExit("MISSING_LOG %s ⇒ 拒绝写盘" % p)
    return io.open(p, encoding="utf-8").read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pat))
    return hits[-1] if not isinstance(hits[-1], tuple) else hits[-1]


def grab_all(pat, text, what, flags=0):
    if not re.search(pat, text, flags):
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pat))
    return re.findall(pat, text, flags)


surface = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)",
               read(L["surface"]), "清账表闸门")
if "MOTION_LEDGER_RESULT=ok" not in read(L["surface"]):
    raise SystemExit("REFUSE_TO_WRITE 闸门没给 ok")
absent = grab(r"LEDGER_ABSENCE_CLAIMS 格=(\d+) 声明=(\d+)", read(L["absence"]), "缺席声明数")
absent_bad = grab(r"LEDGER_ABSENCE_RESULT=(\w+) 不成立=(\d+)/(\d+)", read(L["absence"]), "缺席复查结论")
if absent_bad[0] != "ok" or absent_bad[1] != "0":
    raise SystemExit("REFUSE_TO_WRITE 缺席复查不干净：%s" % (absent_bad,))
frames = int(read(L["frames"]).strip())
if frames < 130:
    raise SystemExit("REFUSE_TO_WRITE 帧目录只数到 %d 张（看图腿没有对象）" % frames)

# 本轮新登记的缺席词：产品源码里必须真的 0 命中（这就是"缺席"声明的正反两面）
tok = read(L["tokens"])
for name in ("footerLabel", "hintLabel"):
    n = int(grab(r"^%s=(\d+)$" % name, tok, "缺席词 %s 的命中数" % name, re.M))
    if n != 0:
        raise SystemExit("REFUSE_TO_WRITE 缺席词 %s 在产品源码里命中 %d 次 ⇒ 这条声明不成立" % (name, n))

# 看图腿：同一把 align 尺在四张浮层帧上的逐行左边缘分布
align_rows = grab_all(r"^(\S+\.png): 有墨的行=(\d+) 左边缘中位=(-?\d+) 跨度=(\d+) 分桶直方图=(.*)$",
                      read(L["align"]), "align 读数", re.M)
align = {os.path.basename(a[0]): a[1:] for a in align_rows}
for need in ("quickpick-empty-420x300-light.png", "quickpick-empty-420x300-dark.png",
             "quickpick-list-420x300-dark.png"):
    if need not in align:
        raise SystemExit("REFUSE_TO_WRITE 看图腿缺 %s 的读数" % need)

# 两簇：把每帧的直方图切成"簇"（同一簇 = 桶距 ≤ 8px），只数簇，不猜哪一簇属于哪一行
def clusters(hist_text):
    xs = sorted(int(m) for m in re.findall(r"x≈(\d+)", hist_text))
    if not xs:
        raise SystemExit("PARSE_FAILED 直方图里没有桶：%r" % hist_text)
    groups = [[xs[0]]]
    for x in xs[1:]:
        (groups.append([x]) if x - groups[-1][-1] > 8 else groups[-1].append(x))
    return groups


emp_light = clusters(align["quickpick-empty-420x300-light.png"][3])
emp_dark = clusters(align["quickpick-empty-420x300-dark.png"][3])
lst = clusters(align["quickpick-list-420x300-dark.png"][3])
if len(emp_light) < 2 or len(emp_dark) < 2:
    raise SystemExit("REFUSE_TO_WRITE 空态只数出一簇 ⇒ 本轮那条'形状与 R64 不同'的观察不成立，别写")

# 全量卷 / 电池：本轮 0 产品文件，所以只跑电池；电池必须在台账落盘之后跑 ⇒ 这里只登记"上一版的电池读数还没本轮的"
battery_ran = None
if os.path.exists(L["battery"]):
    b = read(L["battery"])
    battery_ran = grab(r"^Ran (\d+) tests", b, "电池用例数", re.M)

# 0 产品文件这条钉子：工作树里不许有 Sources 下的改动
dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode("utf-8")
prod = [line for line in dirty.splitlines() if "/Sources/" in line or line.startswith(" M Sources")]
if prod:
    raise SystemExit("REFUSE_TO_WRITE 本轮声明 0 产品文件，但工作树里有：%s" % prod)

V = {
    "surfaces": surface[0], "states": surface[1], "cells": surface[2], "rows": surface[3],
    "cleared": surface[4], "open": surface[5], "floor": surface[6],
    "claim_cells": absent[0], "claims": absent[1], "bad": absent_bad[1], "claims_total": absent_bad[2],
    "frames": str(frames),
    "emp_light_rows": align["quickpick-empty-420x300-light.png"][0],
    "emp_light_span": align["quickpick-empty-420x300-light.png"][2],
    "emp_light_hist": align["quickpick-empty-420x300-light.png"][3].strip(),
    "emp_dark_rows": align["quickpick-empty-420x300-dark.png"][0],
    "emp_dark_hist": align["quickpick-empty-420x300-dark.png"][3].strip(),
    "lst_rows": align["quickpick-list-420x300-dark.png"][0],
    "lst_hist": align["quickpick-list-420x300-dark.png"][3].strip(),
    "lst_median": align["quickpick-list-420x300-dark.png"][1],
    "emp_light_pt_lo": str(int(emp_light[0][0]) // 2), "emp_light_pt_hi": str(int(emp_light[-1][-1] + 3) // 2),
    "emp_light_pt_a": str(int(emp_light[0][0]) // 2), "emp_light_pt_b": str(int(emp_light[1][-1] + 3) // 2),
    "emp_clusters": str(len(emp_light)), "emp_clusters_dark": str(len(emp_dark)),
    "lst_clusters": str(len(lst)),
    "battery": battery_ran or "本轮电池在台账之后跑（见 STATE ⓪）",
}

ui_title = (u"## 第 176 轮（R174 · 2026-10-19）：清账表里那七条理由的主语是**一个不存在的层** ⇒ 换主语 + 开出 204/205"
            u"（U-580…U-582 · 产品 0 文件，动效主线）\n")

ui_body = u"""
- **U-580：换主语，格子数一格没动。** 「浮层/底部说明」那七条理由（R173 的六格 + 更早的「悬停」格）原本都写成"底部那一行是静态标签"，
  而 `QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll` 三个子视图 —— 这一层**没有承载物**。
  本轮把七条理由全部改成描述真实存在的视图，并补两个可复查的缺席词：`footerLabel` / `hintLabel`。
  缺席复查本轮读数：`LEDGER_ABSENCE_CLAIMS 格=%(claim_cells)s 声明=%(claims)s` → `不成立=%(bad)s/%(claims_total)s`；
  两个新词在产品源码里各 0 命中（`grep -rl` 两行都数到 0，写进 `/tmp/r174_tokens.txt` 当证人）。
  清账表 %(rows)s 行 / 已清账 %(cleared)s / 未清账 %(open)s —— **这一笔不是清账**，是把已经清掉的账改成能被机器复查的话。
- **U-581：204 开账，并把"选哪一种"的判据写死。** 一个不存在的表面被逐格判过 ⇒ 每格都 not-applicable、于是"已推进"，
  这正是目标禁止的那种为清账而清账。两种处置（① 认定该有 ⇒ 先做承载物再判九格；② 认定不该有 ⇒ 从词表撤掉并在 DECISIONS 记撤项理由），
  本轮只换主语、**词表没动**：撤词表会让未清账从 %(open)s 直接掉 9 格，那个数不是判断出来的，是删出来的。
  R63 的账解释了这个名字的来源（那句"空结果"的话原本挂在表格下面，R63 把它挪进列表槽 ⇒ 后继是 `empty`，属于「浮层/空态」那一表面）。
- **U-582：看图腿真看了，而它先推翻的是我自己的一条旧账的形状。** 复用 %(frames)s 张在盘帧（产品 0 文件 ⇒ 没重捕、没换装），
  看 `quickpick-list-*-dark` 与 `quickpick-empty-*-light/dark`，并用 `scripts/frame_audit.py align`（threshold=40）量逐行左边缘：
  空态两档各数出 **%(emp_clusters)s / %(emp_clusters_dark)s 簇**（亮档 `有墨的行=%(emp_light_rows)s 跨度=%(emp_light_span)spx 直方图=%(emp_light_hist)s`，
  即 ≈%(emp_light_pt_a)spt 与 ≈%(emp_light_pt_b)spt 两簇），而列表帧一簇为主（`%(lst_hist)s`，中位 %(lst_median)spx）。
  这与 R64 记的"空态那句在列表槽里居中（中心 209.25pt vs 面板 210pt）"**形状不同** —— 但**本轮不据此判产品**：
  `align` 是**逐像素行**的尺，两行长度不同 / 字号不同的文本本来就会给出多簇，它答不了"这两簇是不是同一根轴"，也答不了哪一簇属于哪一行。
  ⇒ 新开 205：要一把**按行带**切（先聚行、再取每行 min-x）的尺，才能判这条；旧的居中记录要么被复核、要么被更正。
""" % V

vi_body = u"""
## Round 174 · 清账表那七条理由的主语是一个不存在的层：换主语 + 开出 204/205（2026-10-19 · 产品 0 文件，动效主线）

- 「浮层/底部说明」七条理由全部改写：面板 stack 只有 `field / empty / scroll`，`footerLabel` / `hintLabel` 在产品源码 0 命中 ⇒ 主语换成真实存在的视图。
- 清账表 %(rows)s 行 / 已清账 %(cleared)s / 未清账 %(open)s **一格没动**：本轮改的是账的**可复查性**，不是覆盖率；缺席复查 %(claims)s 条 0 不成立。
- 204 把"这个表面要不要存在"变成有两条出口、且明确禁止用删格子来收口的决定；205 把看图那条观察交给一把按行带的尺（**当前这把 align 尺答不了这个问题**）。
- 看图腿：%(frames)s 张在盘帧复用，空态两档各 %(emp_clusters)s / %(emp_clusters_dark)s 簇 vs 列表帧 %(lst_clusters)s 簇 —— 与 R64 的"居中"记录形状不同，只写成问题，不写成缺陷。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 11/15 | 真看了三张浮层帧（列表 + 空态两档）并留下同一把尺的数；扣分：尺的粒度不够，所以看图只形成了一条问题 |
| 判据有效性 | 14/15 | 两个新缺席词由 `grep` 证人钉住（命中≠0 就拒绝写盘）；扣分：本轮没有新刀，靠 R173 那三格自证 |
| 假绿防御 | 15/15 | 格子数没动就不写"清了几格"；尺答不了的问题不升级成缺陷；0 产品文件由工作树钉子当场数过 |
| 产品面推进 | 8/15 | 画面 0 改动；推进的是账的诚实性（一个幽灵表面被点名）与两条开账 |
| 台账一致性 | 14/15 | U-580…U-582 + BACKLOG 204/205 + CHANGELOG + STATE + 报告计数器同源；扣分：电池在台账之后跑，本轮写的是"待跑" |
| 交付诚实性 | 15/15 | 明写"这一笔不是清账"、"这把尺答不了"、"删格子能把未清账变少但那是删出来的" |
| 可复核性 | 15/15 | 文件行（`QuickPickController.swift:262`）、缺席词、命令（`frame_audit.py align`）、日志路径全在 |
""" % V

changelog_body = u"""### 清账表「浮层/底部说明」七条理由换主语：那一层没有承载物（R174 / U-580…U-582 · 产品 0 文件，动效主线）

- 事实：`QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll` 三个子视图，`footerLabel` / `hintLabel` 在产品源码里 0 命中 ⇒ 七条理由的主语从"底部那一行"换成真实存在的视图，并补两条可复查的缺席声明
- 清账表 %(rows)s 行 / 已清账 %(cleared)s / 未清账 %(open)s **一格没动**（本轮改的是账的可复查性，不是覆盖率）；缺席复查 `格=%(claim_cells)s 声明=%(claims)s 不成立=%(bad)s/%(claims_total)s`
- 新开 BACKLOG 204（幽灵表面的两种处置，禁止用删格子收口）与 205（看图那把 `align` 尺是逐像素行的，答不了"两行同不同轴" ⇒ 要按行带重切）
- 看图腿复用盘上 %(frames)s 张帧：空态两档各 %(emp_clusters)s / %(emp_clusters_dark)s 簇 vs 列表帧 %(lst_clusters)s 簇，与 R64 的"空态居中"记录形状不同 ⇒ 只形成问题，不判缺陷
- 0 产品文件 ⇒ 没重捕、没换装；本轮没跑新刀（R173 的三格自证仍有效）

""" % V

backlog_body = u"""**205. 看图那把 `frame_audit.py align` 是逐像素行的尺：它数出空态有 %(emp_clusters)s 簇左边缘，却答不了"这两行同不同轴"（R174 量到形状，没量到成因）**

本轮看 `quickpick-empty-420x300-light/dark.png`（%(frames)s 张盘上帧里挑的），同一把尺、threshold=40：
亮档 `有墨的行=%(emp_light_rows)s 跨度=%(emp_light_span)spx 直方图=%(emp_light_hist)s` ⇒ 两簇（≈%(emp_light_pt_a)spt / ≈%(emp_light_pt_b)spt，帧 840px 宽 = 420pt，2px/pt）；
暗档 `%(emp_dark_hist)s` 同形；对照 `quickpick-list-420x300-dark.png` 是 `%(lst_hist)s`（一簇为主、中位 %(lst_median)spx）。
R64 的旧账写的是"空态那句在列表槽里**居中**，中心 209.25pt vs 面板 210pt" ⇒ 两件事不能同时是"一根轴"。
**为什么本轮不据此判产品**：`align` 取的是**每一像素行**的第一个有墨列，字号不同 / 长度不同的两行文本本来就会给出多簇，
它既没把像素行聚成"文本行"，也没报哪一簇属于哪一行 ⇒ 这把尺回答不了这个问句（R100 那条"尺要问得出问题"的规矩）。
下一步（有预算的一轮做）：按行带重切 —— 先把有墨的像素行按 y 聚成文本行，再对每行取 min-x，与列表行的标签轴（R65 结案后的 56.0–57.0pt）对账；
若空态两行确实落在两根不同的轴上，那才是排版缺陷，且要顺手复核 R64 那条"居中"是否已被 R65 之后的改动作废。

""" % V

state_body = u"""最后更新：2026-10-19 03:52（本地 · R174 / 第 176 轮：**清账表「浮层/底部说明」七条理由换主语 —— 那层没有承载物；开出 204 / 205**（U-580…U-582 · 产品 0 文件，动效主线）

**本轮读到的事实**：`QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll` 三个子视图；`footerLabel` / `hintLabel` 在产品源码 0 命中。
⇒ 七条理由的主语换成真实存在的视图（R173 六格 + 更早的「悬停」格），**格子数一格没动**：清账表 %(rows)s 行 / 已清账 %(cleared)s / 未清账 %(open)s，
缺席复查 `格=%(claim_cells)s 声明=%(claims)s 不成立=%(bad)s/%(claims_total)s`。
**204**：幽灵表面要么做承载物（产品需求）要么撤词表（DECISIONS 记理由），本轮**两样都没选**，因为撤词表会把未清账直接删掉 9 格 —— 那不是判断。
**205**：看图腿用 `frame_audit.py align` 量到空态两档各 %(emp_clusters)s / %(emp_clusters_dark)s 簇（≈%(emp_light_pt_a)spt / ≈%(emp_light_pt_b)spt），
与 R64 的"空态居中"记录形状不同；这把尺是**逐像素行**的，答不了"同不同轴" ⇒ 只记问题，不判缺陷。
验证：0 产品文件（工作树钉子当场数过）⇒ 没构建、没重捕、没换装；电池 %(battery)s。

**下一轮（R175）的靶**：⓪ 读本笔 push 之后那一跑的**全部失败步骤**（`python3 scripts/ci_read.py steps <run>`），
   并确认上一笔（`9e1d3d4`）那一跑的结论 —— 结论未读时不许写"没红"；
① 收口：`AGENT_FINAL_REPORT.md` 按阶段二实际覆盖（%(cleared)s/%(cells)s 格、%(open)s 格未判）与 204/205 两条未决项写清"能停的判据只剩需要用户真机或授权的那几项"；
② BACKLOG 204 要**选一种处置**并留下证据（不许用删格子收口）；③ BACKLOG 205 的按行带尺（先聚 y 再取 min-x，与 56.0–57.0pt 对账）；
④ 清账表剩余 %(open)s 格（`motion_surface_gate.py --list-open` 给名单）；⑤ 195 的 ①、189、188 的 ②③、176 / 182 / 183 / 185、201 的带内读数。

""" % V

report_old = (u"2. **清账表还有 %s 格未判**（闸门本轮（R173）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))
report_new = (u"2. **清账表还有 %s 格未判**（闸门本轮（R174）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))


def write(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def insert_before(path, prefix, block):
    lines = read(path).split(u"\n")
    idx = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit("ANCHOR %r 命中 %d 次（要 1）on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip(u"\n"))
    write(path, u"\n".join(lines))
    return idx[0]


def append_eof(path, block):
    write(path, read(path).rstrip(u"\n") + u"\n\n" + block.rstrip(u"\n") + u"\n")


def main():
    for name, text in ((u"ui", ui_title + ui_body), (u"vi", vi_body), (u"cl", changelog_body),
                       (u"bl", backlog_body), (u"st", state_body)):
        if re.search(r"%\([a-z_]+\)s", text):
            raise SystemExit("FORMAT_LEAK %s 还有没吃掉的占位符" % name)
    insert_before(os.path.join(ROOT, "AGENT_UI_AUDIT.md"), u"## 第 175 轮（R173", ui_title + ui_body)
    append_eof(os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"), vi_body)
    insert_before(os.path.join(ROOT, "CHANGELOG.md"), u"### 浮层/底部说明六格清账", changelog_body)
    append_eof(os.path.join(ROOT, "AGENT_BACKLOG.md"), backlog_body)
    insert_before(os.path.join(ROOT, "AGENT_STATE.md"), u"最后更新：2026-10-19 03:31", state_body)
    rep = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    text = read(rep)
    if text.count(report_old) != 1:
        raise SystemExit("REPORT_ANCHOR 命中 %d 次" % text.count(report_old))
    write(rep, text.replace(report_old, report_new))

    audit = read(os.path.join(ROOT, "AGENT_UI_AUDIT.md"))
    section = audit.split(ui_title.rstrip(u"\n"), 1)[1].split(u"\n## 第 175 轮", 1)[0]
    defined = sorted(int(m) for m in re.findall(r"^- \*\*U-(\d{3})：", section, re.M))
    if defined != [580, 581, 582]:
        raise SystemExit("U_RANGE_MISMATCH 本轮定义 %s（要 580…582）" % defined)
    for needle in (u"footerLabel", u"hintLabel", u"204", u"205", u"align"):
        if needle not in section:
            raise SystemExit("SECTION_THIN 本轮那一节缺 %r 的原文" % needle)
    print(u"LEDGERS_WRITTEN rows=%s cleared=%s open=%s claims=%s/%s bad=%s frames=%s "
          u"empty_clusters=%s/%s list_clusters=%s"
          % (V["rows"], V["cleared"], V["open"], V["bad"], V["claims_total"], V["bad"],
             V["frames"], V["emp_clusters"], V["emp_clusters_dark"], V["lst_clusters"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
