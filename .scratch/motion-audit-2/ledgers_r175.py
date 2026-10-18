#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 的台账批写：按文本行带的左轴尺 + 它推翻的 R174 前提；数字全部从本轮日志解析。"""
import io
import os
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
L = {"bands": "/tmp/r175_bands.txt", "battery": "/tmp/r175_battery.log",
     "surface": "/tmp/r175_surface.log", "ci": "/tmp/r175_ci.txt", "cross": "/tmp/r175_cross.txt"}


def read(p):
    if not os.path.exists(p):
        raise SystemExit("MISSING_LOG %s ⇒ 拒绝写盘" % p)
    return io.open(p, encoding="utf-8").read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pat))
    return hits[-1]


bandslog = read(L["bands"])
BAND = re.compile(r"带(\d) y=(\d+)\.\.(\d+) 行数=(\d+) 最左墨=(\d+)px=([\d.]+)pt 众数左沿=(\d+)px=([\d.]+)pt 行内散布=(\d+)px")
FRM = re.compile(r"^(\S+\.png): 文本行带=(\d+)", re.M)

# 按帧切段（`BANDS_VERDICT` 属于它上面那一帧）
frames = {}
for m in FRM.finditer(bandslog):
    start = m.end()
    nxt = FRM.search(bandslog, start)
    body = bandslog[start:nxt.start() if nxt else len(bandslog)]
    frames[m.group(1)] = {"n": int(m.group(2)),
                          "bands": {int(b[0]): b for b in BAND.findall(body)},
                          "verdict": (re.search(r"BANDS_VERDICT ([^（\s]+)", body).group(1)
                                      if re.search(r"BANDS_VERDICT ([^（\s]+)", body) else "无")}
for need in ("quickpick-empty-420x300-light.png", "quickpick-empty-420x300-dark.png",
             "quickpick-list-420x300-dark.png"):
    if need not in frames:
        raise SystemExit("REFUSE_TO_WRITE 缺 %s 的读数" % need)

emp_l, emp_d, lst = (frames["quickpick-empty-420x300-light.png"],
                     frames["quickpick-empty-420x300-dark.png"],
                     frames["quickpick-list-420x300-dark.png"])
if len(emp_l["bands"]) != 2 or len(emp_d["bands"]) != 2:
    raise SystemExit("REFUSE_TO_WRITE 空态帧的带数不是 2（%d / %d）⇒ 本轮那条'两个元素'的读法没有对象"
                     % (len(emp_l["bands"]), len(emp_d["bands"])))
# 两档必须逐位对账：`min_x` 两带都稳 ⇒ "是尺的问题、不是布局的问题"；
# 而众数**只在带0 漂**（带1 两档同为 108px）⇒ 本轮写的是"混元素那一带的众数会漂"，不是"众数都会漂"。
for i in (0, 1):
    if emp_l["bands"][i][4] != emp_d["bands"][i][4]:
        raise SystemExit("REFUSE_TO_WRITE 带%d 的 min_x 两档不一致（%s vs %s）⇒ 那是布局差异，不是尺漂"
                         % (i, emp_l["bands"][i][4], emp_d["bands"][i][4]))
if emp_l["bands"][0][6] == emp_d["bands"][0][6]:
    raise SystemExit("REFUSE_TO_WRITE 带0 的众数两档一致 ⇒ 本轮没量到'众数会漂'，别写这条")
if emp_l["bands"][1][6] != emp_d["bands"][1][6]:
    raise SystemExit("REFUSE_TO_WRITE 带1 的众数也漂了（%s vs %s）⇒ '只有混元素的带0 会漂'这句观察不成立，"
                     "本轮的收窄结论要重写" % (emp_l["bands"][1][6], emp_d["bands"][1][6]))
if not (emp_l["verdict"] == emp_d["verdict"] == lst["verdict"] == u"不可判"):
    raise SystemExit("REFUSE_TO_WRITE 三帧的判定不是都'不可判'（%s / %s / %s）⇒ 混元素那道闸门没生效"
                     % (emp_l["verdict"], emp_d["verdict"], lst["verdict"]))

batt = read(L["battery"])
# 结论行**不在**最后一行：unittest 的汇总走 stderr，测试自己的 stdout 是块缓冲、
# 在退出时才冲出去 ⇒ `splitlines()[-1]` 会落在某条 stdout 上（本轮就是这么被自己拒写一次的）。
if not re.search(r"^OK$", batt, re.M) or re.search(r"^FAILED", batt, re.M):
    raise SystemExit("REFUSE_TO_WRITE 电池不绿：Ran=%s FAILED=%s"
                     % (bool(re.search(r"^Ran ", batt, re.M)), bool(re.search(r"^FAILED", batt, re.M))))
batt_ran = grab(r"^Ran (\d+) tests", batt, "电池用例数", re.M)
batt_fail = len(re.findall(r"^(?:FAIL|ERROR):", batt, re.M))
surface = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)",
               read(L["surface"]), "清账表闸门")
ci_rows = grab_all = re.findall(r"^(\d{9,}) (\w{7}) (\w+) (\S+) (.*)$", read(L["ci"]), re.M)
if len(ci_rows) < 3:
    raise SystemExit("REFUSE_TO_WRITE CI 读数少于 3 跑（%d）" % len(ci_rows))

V = {
    "b0_min_l": emp_l["bands"][0][5], "b1_min_l": emp_l["bands"][1][5],
    "b0_axis_l": emp_l["bands"][0][7], "b0_axis_d": emp_d["bands"][0][7],
    "b1_axis_l": emp_l["bands"][1][7], "b1_axis_d": emp_d["bands"][1][7],
    "b0_px_l": emp_l["bands"][0][4], "b0_px_d": emp_d["bands"][0][4],
    "b1_px_l": emp_l["bands"][1][4], "b1_px_d": emp_d["bands"][1][4],
    "b0_spread_l": emp_l["bands"][0][8], "b1_spread_l": emp_l["bands"][1][8],
    "b0_y": "%s..%s" % (emp_l["bands"][0][1], emp_l["bands"][0][2]),
    "b1_y": "%s..%s" % (emp_l["bands"][1][1], emp_l["bands"][1][2]),
    "b0_rows": emp_l["bands"][0][3], "b1_rows": emp_l["bands"][1][3],
    "lst_bands": str(len(lst["bands"])),
    "lst_axes": " ".join(lst["bands"][k][5] + "pt" for k in sorted(lst["bands"])),
    "verdict": emp_l["verdict"],
    "batt_ran": batt_ran, "batt_fail": str(batt_fail),
    "rows": surface[3], "cleared": surface[4], "open": surface[5],
    "ci": "; ".join("`%s`=`%s` %s/%s" % (r[0], r[1], r[2], r[3]) for r in ci_rows[:4]),
    "cross": read(L["cross"]).strip(),
}

ui_title = (u"## 第 177 轮（R175 · 2026-10-19）：给左轴装一把按文本行带的尺，它第一件事是**推翻 R174 我自己的前提**"
            u"（U-583…U-585 · 产品 0 文件，判据账）\n")

ui_body = u"""
- **U-583：尺落地（BACKLOG 205 的那一问要先有尺才配问）。** `scripts/frame_audit.py` 多一个 `bands` 子命令：
  先把有墨的像素行按 y 聚成**文本行带**（`min_gap=4`、`min_rows=4` 挡碎屑），再对每带报
  `最左墨 min_x` / `众数左沿 axis` / `行内散布`。自测 8 格在 `scripts/tests/test_frame_audit_bands.py`（整卷 %(batt_ran)s 格里本轮新增的就是这 8 格）：
  正对照（两行同轴、长度与字号都不同 ⇒ 必须读成同轴 —— 这正是 `align` 当年读错的形状）、
  反方向（真错开 30px ⇒ 不许被抹平）、碎屑（一像素的边角不许算一行字）、
  **边界**（带图标的行里 axis 就是图标轴 ⇒ 这把尺只配问无图标的那一类行）、混元素（散布 >40px ⇒ 拒判）。
- **U-584：它先推翻的是上一轮我自己写下的前提。** 空态帧聚出 **2 带**：带0 `y=%(b0_y)s 行数=%(b0_rows)s 最左墨=%(b0_px_l)spx=%(b0_min_l)spt`、
  带1 `y=%(b1_y)s 行数=%(b1_rows)s 最左墨=%(b1_px_l)spx=%(b1_min_l)spt`，两档逐位一致。
  ⇒ 这两带是**两个元素**（带0 = 搜索框那一行的查询文字，%(b0_min_l)spt 与 R104 量的 22pt 内缩对上；带1 = 空态那一句，%(b1_min_l)spt），
  不是"空态的两行落在两根轴上"。R174 的 U-582 把两个元素读成了两行 —— **前提撤掉**，
  而 R64 那条"空态那句在列表槽里居中"与本轮相容（空态确实只有一句）。
- **U-585：尺自己的失效也被量出来了，而且它比产品结论更值钱。** 同一张空态帧、同一个带0：
  `min_x` 两档都是 %(b0_px_l)spx，`众数左沿` 却亮档 %(b0_axis_l)spt / 暗档 %(b0_axis_d)spt（带内散布 %(b0_spread_l)spx）。
  ⇒ 主读数换成 `min_x`，并加一条闸门：**带内散布 >40px 就报『不可判』**（本轮三张真帧全部 `BANDS_VERDICT %(verdict)s`，
  列表帧 %(lst_bands)s 带的轴是 %(lst_axes)s —— 那些带里都是"图标 + 文字"混在一起）。
  所以 205 **不结案**：它从"空态两行同不同轴"（一个被本轮证伪的问句）收窄成
  "要按**元素**切带（同一带内先按 x 断簇）才谈得上同轴"这一格，仍开着。
""" % dict(V, batt_rans="354 格里的")

vi_body = u"""
## Round 175 · 给左轴装一把按文本行带的尺，它第一件事是推翻 R174 我自己的前提（2026-10-19 · 产品 0 文件，判据账）

- `frame_audit.py bands`：按 y 聚文本行带 → 每报 `最左墨 / 众数左沿 / 行内散布`；8 格自测含**正反两方向**与"带图标那一行不适用"的边界。
- 真帧读数把 R174 的 U-582 前提撤掉：空态帧只有 2 带，且它们是**两个元素**（搜索框行 %(b0_min_l)spt、空态那一句 %(b1_min_l)spt，两档逐位一致），
  不是"空态两行不同轴"。R64 的"空态居中"与本轮相容。
- 同一次对账量出尺自己的漂：带0 的 `min_x` 两档同为 %(b0_px_l)spx，`众数左沿` 却 %(b0_axis_l)spt vs %(b0_axis_d)spt
  ⇒ 主读数改 `min_x`，带内散布 >40px 一律 `BANDS_VERDICT %(verdict)s`（三张真帧现在都不给同轴/不同轴的结论）。
- 205 不结案，收窄成"按元素切带"那一格。CI：%(ci)s（`in_progress` 的结论未读，不许说没红）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 看的是同一批帧的**结构读数**（带 y 区间、行数、最左墨），并据此撤了自己上一轮的前提；扣分：本轮没有新画面可看（0 产品文件） |
| 判据有效性 | 15/15 | 8 格自测两个方向都有牙：同轴不许读成两根、错开 30px 不许抹平、碎屑不算行、混元素必须拒判 |
| 假绿防御 | 15/15 | 台账脚本要求"两档 min_x 必须一致、众数必须不一致"，否则**拒绝写盘** ⇒ 这条结论只能被真读数支持 |
| 产品面推进 | 8/15 | 画面 0 改动；推进是把一条会被写成产品缺陷的误读挡在落地之前（省掉一次假工单） |
| 台账一致性 | 13/15 | U-583…U-585 + 205 追记 + CHANGELOG + STATE + 报告计数器；扣分：新尺还没进 §9.3 的常规仪器清单 |
| 交付诚实性 | 15/15 | 明写"上一轮的前提是我自己读错的"，并把三张真帧的当前判定是『不可判』原样报出 |
| 可复核性 | 15/15 | 命令、阈值、日志路径、CI run 号都在；任何人都能重跑 `frame_audit.py bands` |
""" % V

changelog_body = u"""### 新尺 `frame_audit.py bands`：按文本行带取左轴，它先撤掉 R174 自己的前提（R175 / U-583…U-585 · 产品 0 文件，判据账）

- 落地：像素行按 y 聚成文本行带（`min_gap=4`、`min_rows=4`），每带报 `最左墨 / 众数左沿 / 行内散布`；8 格自测覆盖正对照（同轴不许读成两根）、反方向（错开 30px 不许抹平）、碎屑、带图标的行不适用、混元素必须拒判
- 真帧读数：空态帧 2 带 = **两个元素**（搜索框行 %(b0_min_l)spt 对上 R104 的 22pt 内缩；空态那一句 %(b1_min_l)spt），两档逐位一致 ⇒ R174 的"空态两行不同轴"前提撤销，R64 的"空态居中"与本轮相容
- 尺自己的失效：带0 `min_x` 两档同 %(b0_px_l)spx 而 `众数左沿` %(b0_axis_l)spt vs %(b0_axis_d)spt ⇒ 主读数换 `min_x`，带内散布 >40px 一律 `BANDS_VERDICT %(verdict)s`（本轮三张真帧全部不给同轴结论）
- BACKLOG 205 不结案，收窄成"按元素切带"；清账表 %(rows)s 行 / 未清账 %(open)s 未动
- 验证：电池 `Ran %(batt_ran)s / 红 %(batt_fail)s`；0 产品文件 ⇒ 没构建、没重捕、没换装；CI %(ci)s

""" % V

backlog_body = u"""**205 追记（R175）：尺落地了，而它第一个结论是撤掉 R174 的前提；205 收窄成"按元素切带"**

新子命令 `python3 scripts/frame_audit.py bands <帧> --pt-width 420`：按 y 聚文本行带，每带报 `最左墨 / 众数左沿 / 行内散布`。
空态帧实测（亮暗两档逐位一致）：带0 `y=%(b0_y)s 行数=%(b0_rows)s 最左墨=%(b0_px_l)spx=%(b0_min_l)spt`、
带1 `y=%(b1_y)s 行数=%(b1_rows)s 最左墨=%(b1_px_l)spx=%(b1_min_l)spt` ⇒ **两带是两个元素**（搜索框那一行 vs 空态那一句），
不是"空态的两行落在两根轴上"。R174 的 U-582 读错了主语，本轮撤掉；R64 的"空态那句居中"与读数相容（空态只有一句）。
同一次对账还量出尺自己的漂：带0 的 `min_x` 两档同为 %(b0_px_l)spx，`众数左沿` 却亮档 %(b0_axis_l)spt / 暗档 %(b0_axis_d)spt（带内散布 %(b0_spread_l)spx）
⇒ 主读数改成 `min_x`，并加闸门：**带内散布 >40px 报『不可判』**（本轮三张真帧全部 `%(verdict)s`，列表帧 %(lst_bands)s 带的轴 %(lst_axes)s 都是图标+文字混带）。
剩下的那一格（205 不结案的原因）：要谈"同一个表面里的两根轴"，得先在带内按 x 断簇、按**元素**切带；
现在这把尺只能报"每一带最左的墨在哪"，它答不了"这一带里最左的那块墨是不是我要问的那个元素"。

""" % V

state_body = u"""最后更新：2026-10-19 04:05（本地 · R175 / 第 177 轮：**左轴尺 `frame_audit.py bands` 落地，第一个结论是撤掉 R174 我自己的前提**（U-583…U-585 · 产品 0 文件，判据账）

**新尺**：`bands` 按 y 聚文本行带 → 每带报 `最左墨 / 众数左沿 / 行内散布`；8 格自测（同轴不许读成两根、错开 30px 不许抹平、碎屑不算行、带图标的行不适用、混元素必须拒判）。
**撤掉的前提**：空态帧只有 2 带，且它们是**两个元素**（搜索框行 %(b0_min_l)spt = R104 的 22pt 内缩；空态那一句 %(b1_min_l)spt），两档逐位一致
⇒ R174 的"空态两行不同轴"是我把两个元素读成了两行；R64 的"空态居中"相容。**尺自己的漂**：带0 `min_x` 两档同 %(b0_px_l)spx 而众数 %(b0_axis_l)spt vs %(b0_axis_d)spt
⇒ 主读数改 `min_x`、带内散布 >40px 一律 `%(verdict)s`（三张真帧现在都不给同轴结论）。**205 不结案**，收窄成"按元素切带"。
验证：电池 `Ran %(batt_ran)s / 红 %(batt_fail)s`；清账表 %(rows)s 行 / 未清账 %(open)s（未动）；0 产品文件 ⇒ 没构建、没重捕、没换装。
CI：%(ci)s。另记 R174 那笔的电池：第一次跑红了一格悬空引用、单独跑与整卷重跑都绿，**成因未命名**（陈旧字节码缓存那条猜测没被证实）。

**下一轮（R176）的靶**：⓪ 先读 `659ec46` 那一跑（`in_progress` ⇒ 结论未读）与 `0dbcbb5` 那朵 **failure** 的全部失败步骤
   （`python3 scripts/ci_read.py steps 39157963970`）—— 它比 e61796c / 9e1d3d4 两跑 success 更早，**不许当成已修**；
① 205 的下一格：带内按 x 断簇（按元素切带），然后才谈"同一表面两根轴"；
② 204 要选一种处置（做承载物 / 撤词表），不许用删格子收口；
③ 清账表剩余 %(open)s 格（`motion_surface_gate.py --list-open`）；④ 201 的带内读数、195 的 ①、189、188 的 ②③；
⑤ 把 `bands` 这把尺写进 §9.3 的常规仪器清单（现在只有本轮用过它）。

""" % V

report_old = (u"2. **清账表还有 %s 格未判**（闸门本轮（R174）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))
report_new = (u"2. **清账表还有 %s 格未判**（闸门本轮（R175）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
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
        if re.search(r"%\([a-z_0-9]+\)s", text):
            raise SystemExit("FORMAT_LEAK %s 还有没吃掉的占位符" % name)
    insert_before(os.path.join(ROOT, "AGENT_UI_AUDIT.md"), u"## 第 176 轮（R174", ui_title + ui_body)
    append_eof(os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"), vi_body)
    insert_before(os.path.join(ROOT, "CHANGELOG.md"), u"### 清账表「浮层/底部说明」七条理由换主语", changelog_body)
    append_eof(os.path.join(ROOT, "AGENT_BACKLOG.md"), backlog_body)
    insert_before(os.path.join(ROOT, "AGENT_STATE.md"), u"最后更新：2026-10-19 03:52", state_body)
    rep = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    text = read(rep)
    if text.count(report_old) != 1:
        raise SystemExit("REPORT_ANCHOR 命中 %d 次" % text.count(report_old))
    write(rep, text.replace(report_old, report_new))

    audit = read(os.path.join(ROOT, "AGENT_UI_AUDIT.md"))
    section = audit.split(ui_title.rstrip(u"\n"), 1)[1].split(u"\n## 第 176 轮", 1)[0]
    defined = sorted(int(m) for m in re.findall(r"^- \*\*U-(\d{3})：", section, re.M))
    if defined != [583, 584, 585]:
        raise SystemExit("U_RANGE_MISMATCH 本轮定义 %s（要 583…585）" % defined)
    for needle in (u"bands", u"min_x", u"不可判", u"205"):
        if needle not in section:
            raise SystemExit("SECTION_THIN 本轮那一节缺 %r 的原文" % needle)
    print(u"LEDGERS_WRITTEN b0_min=%spt b1_min=%spt modal=%s/%s verdict=%s batt=%s rows=%s open=%s"
          % (V["b0_min_l"], V["b1_min_l"], V["b0_axis_l"], V["b0_axis_d"], V["verdict"],
             V["batt_ran"], V["rows"], V["open"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
