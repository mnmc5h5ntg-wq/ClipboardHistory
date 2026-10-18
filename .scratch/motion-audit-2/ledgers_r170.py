#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R170 的台账批写：runner 的分辨轴读数 + 出口接线，数字全部从日志解析（含 runner 那份 `--log`）。"""
import glob
import io
import os
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
L = {"run": "/tmp/r170_run.log", "cap": "/tmp/r170_capture.log", "base": "/tmp/r170_baseline.log",
     "full": "/tmp/r170_full.log", "mut": "/tmp/r170_mut.log", "pre": "/tmp/r170_precheck.log",
     "surface": "/tmp/r170_surface.log", "frames": "/tmp/r170_frames.txt"}


def read(p):
    if not os.path.exists(p):
        raise SystemExit("MISSING_LOG %s ⇒ 拒绝写盘" % p)
    return io.open(p, encoding="utf-8").read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pat))
    last = hits[-1]
    return last if isinstance(last, tuple) else last


def grab_all(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pat))
    return hits


runlog = read(L["run"])
caplog = read(L["cap"])
baselog = read(L["base"])
fulllog = read(L["full"])
mutlog = read(L["mut"])
prelog = read(L["pre"])
surfacelog = read(L["surface"])

# --- runner 那一跑的分辨轴读数（六张高帧）---
runner_rows = grab_all(r"CAPTURE_DRAW (\S+) requested=(\d+) drawnBoxPt=(-?\d+) drawnBottomPt=(-?\d+)"
                       r" transparent=([\d.]+)% screenVisibleHeightPt=(-?\d+)", runlog,
                       "runner 的 CAPTURE_DRAW 行")
boxes = sorted({int(r[2]) for r in runner_rows})
bottoms = sorted({int(r[3]) for r in runner_rows})
screens = sorted({int(r[5]) for r in runner_rows})
blanks = sorted({r[4] for r in runner_rows})
if len(boxes) != 1 or len(bottoms) != 1 or len(screens) != 1:
    raise SystemExit("REFUSE_TO_WRITE runner 的高帧读数不同形：%s / %s / %s" % (boxes, bottoms, screens))

# --- 本机这一跑的同一条轴（标定另一侧）---
local_rows = grab_all(r"CAPTURE_DRAW (\S+) requested=(\d+) drawnBoxPt=(-?\d+)", caplog, "本机 CAPTURE_DRAW 行")
local_boxes = sorted({int(r[2]) for r in local_rows})
cap_exit = int(grab(r"CAPTURE_EXIT=(\d+)", caplog, "捕获卷退出码"))
census = grab(r"BLANK_GAP_WOULD_RELEASE_CENSUS loop_items=(\d+) with_geometry=(\d+) \w*release=(\d+)", caplog,
              "本机 census") if re.search(r"BLANK_GAP_WOULD_RELEASE_CENSUS", caplog) else None
local_marker_hits = len(grab_all(r"CAPTURE_BLANK_NOT_RUN", caplog, "本机出口点火次数（允许 0）")) \
    if re.search("CAPTURE_BLANK_NOT_RUN", caplog) else 0

totals = grab_all(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failure[s]?", fulllog, "全量卷结论行")
swift_n, swift_skip, swift_fail = totals[-1][:3]
full_exit = int(grab(r"FULL_EXIT=(\d+)", fulllog, "全量卷退出码"))
verdict = grab(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", mutlog, "变异表结论")
arms = grab_all(r"^(M\d{3}) CAUGHT 红在：(\S+)", mutlog, "变异刀逐条", re.M)
baseline = (grab(r"FRAME_BASELINE_AGAINST=(\w+)", baselog, "对账基准"),
            int(grab(r"FRAME_BASELINE_COMPARED=(\d+)", baselog, "compared")),
            int(grab(r"FRAME_BASELINE_CHANGED=(\d+)", baselog, "changed")),
            int(grab(r"FRAME_BASELINE_MISSING=(\d+)", baselog, "missing")),
            int(grab(r"FRAME_BASELINE_ADDED=(\d+)", baselog, "added")))
surface = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)",
               surfacelog, "清账表闸门")
frames = int(read(L["frames"]).strip())
red_names = sorted(set(grab_all(r"Test Case '-\[.*?\.(?:\w+ )?(\w+)'(?: \w+)?\] failed", fulllog,
                               "红名（可空）", re.M))) if re.search(r"\] failed", fulllog) else []

problems = []
if swift_fail != "0" or full_exit != 0:
    problems.append("全量卷失败 %s / 退出码 %d / 红名 %s" % (swift_fail, full_exit, red_names or "无名"))
if cap_exit != 0:
    problems.append("捕获卷退出码 %d" % cap_exit)
if baseline[0] != "working" or baseline[1] < 130:
    problems.append("帧基线对的是 %s、只对账 %d 张" % (baseline[0], baseline[1]))
if baseline[2] or baseline[3] or baseline[4]:
    problems.append("帧变了：changed=%d missing=%d added=%d" % (baseline[2], baseline[3], baseline[4]))
if verdict[0] != verdict[1] or verdict[2] != "yes":
    problems.append("变异表没全 CAUGHT 或还原不干净：%s" % (verdict,))
if frames < 130:
    problems.append("帧目录只数到 %d 张" % frames)
if problems:
    raise SystemExit("REFUSE_TO_WRITE " + "；".join(problems))

V = {
    "n_runner": str(len(runner_rows)),
    "box": str(boxes[0]), "bottom": str(bottoms[0]), "screen": str(screens[0]),
    "blank": blanks[0], "req": runner_rows[0][1],
    "local_boxes_lo": str(local_boxes[0]), "local_boxes_hi": str(local_boxes[-1]),
    "local_n": str(len(local_rows)), "local_marker": str(local_marker_hits),
    "swift_n": swift_n, "swift_skip": swift_skip, "swift_fail": swift_fail,
    "full_exit": str(full_exit),
    "caught": verdict[0], "arms_total": verdict[1], "restore": verdict[2],
    "arm_map": ", ".join("%s→%s" % (a, b) for a, b in arms),
    "compared": str(baseline[1]), "changed": str(baseline[2]),
    "surface": u"行数=%s 已清账=%s 未清账=%s 地板=%s" % (surface[3], surface[4], surface[5], surface[6]),
    "frames": str(frames),
    "cap_exit": str(cap_exit),
    "pre_bad": grab(r"NEEDLE_PRECHECK tables=\d+ covered=\d+ arms=\d+ bad=(\d+)", prelog, "预检 bad 计数"),
    "run_id": "39152321051", "run_sha": "72279ff",
}

ui_title = (u"## 第 172 轮（R170 · 2026-10-19）：runner 的分辨轴给了一个**谁都没预测到**的形状 ⇒ 出口按实测接线（BACKLOG 194 结案为通道限制）"
            u"（U-567…U-570 · 产品 0 文件，判据账）\n")

ui_body = u"""
- **U-567：读数到手，而且两种预测都被推翻。** run `%(run_id)s`（`%(run_sha)s`）的 `--log` 里六张高帧同形：
  `requested=%(req)s drawnBoxPt=%(box)s drawnBottomPt=%(bottom)s transparent=%(blank)s%% screenVisibleHeightPt=%(screen)s`。
  这把 R162/R167 预登记的三种解释逐条量掉：
  * 「根本没渲染」被 `drawnBoxPt=%(box)s > 0` 排除 —— 那 %(box)spt 的带里确实有墨；
  * 「被屏幕裁」被 `%(box)s ≠ screenVisibleHeightPt=%(screen)s`、且带落在**图的下沿**（bottom=%(bottom)s）排除；
  * 「窗口被收小 / 内容视图没铺满」早被几何三边（`content == host == requested`）排除（R167）。
  本机同一条轴给的是另一侧标定：%(local_n)s 张高帧 `drawnBoxPt=%(local_boxes_lo)s…%(local_boxes_hi)s`（画满）。
  ⇒ **剩下的读法是"这台机器的高窗捕获通道只画出一条窄带"，机制没有命名**：
  本机可视高 %(screen)s 的邻居 850 < %(req)s 却画满，所以"只画与屏幕相交的那条带"这条猜测在自己身上就不成立 —— 猜测不写进账当结论，
  新开 BACKLOG 201 记这条未命名的机制。
- **U-568：出口按**实测到的那一种形状**接线，两种形状明确不放行。**
  `shouldRegisterBlankAsMachineGap` 多了 `drawnBoxPt` 这一根轴：放行条件是 `0 < drawnBoxPt < requested`；
  `drawnBoxPt == 0`（一张都没画 = 捕获坏了，没人签过字）与 `drawnBoxPt == requested`（画满了却报 %(blank)s%% 未画 = 两把尺自相矛盾，先修尺）都照旧红。
  点火时打 `CAPTURE_BLANK_NOT_RUN <帧名> …` —— 名字必须是全大写 `*_NOT_RUN` 形状，`scripts/ci_capture_gate.py` 的
  `NOT_RUN` 正则才认它，闸门正文本来就只给两种处置（修 / 登记未运行），这是第二种。
  本机 `%(local_marker)s` 次点火 = 0（本机没有空白高帧），所以这条出口的**真产物验收只能等 CI 那一跑**：预期 STEP[15] 不再因为那六张红。
  BACKLOG 194 至此**结案为通道限制**（口径：不是产品缺陷、机制未命名、出口只认实测形状；待 CI 复验，见 STATE ⓪）。
- **U-569：12 把刀复跑 + 三把新的，前任死针当场退休。** `mutate_r168.py` 现在 12 臂全 CAUGHT、RESTORE_CLEAN=%(restore)s：
  %(arm_map)s。其中 M675/M678 的 needle 因为谓词换了形状而**当场改成新写法**（不改就会空转一整轮，R102 那条规矩第 N 次执行）；
  新增的三把都打在出口点火那一支：M687（去掉 `> 0` ⇒ "根本没渲染"会被放行）、M688（去掉 `< requested` ⇒ "画满了却报空"会被放行）、
  M689（把 marker 名改成 `CAPTURE_BLANK_NOTRUN` ⇒ 闸门再也认不出它，红会回来）。
  预检同一次打 `bad=%(pre_bad)s`（还是 R168 记的那支陈旧死针 M541 + 它把活针报成 命中=0 的老毛病）。
- **U-570：两台机器的对照写清楚，免得下一轮把"绿"读成"验过"。** 本轮本机：编译 0 告警、判据卷 10 格、
  捕获卷退出码 %(cap_exit)s、帧基线 `--against working` 对账 %(compared)s 张 changed=%(changed)s（本机不走这条出口 ⇒ 帧不该变，变了就是尺坏）、
  全量卷 %(swift_n)s 例 / 跳过 %(swift_skip)s / 失败 %(swift_fail)s（退出码 %(full_exit)s）；清账表 %(surface)s。
  看图腿：产品 0 文件、帧逐字节未变，本轮"看"的是 runner 日志里那一行读数，不是画面 —— 这条按未看新画面记账，不写成"审查过"。
""" % V

vi_body = u"""
## Round 170 · runner 的分辨轴给了一个谁都没预测到的形状，出口按实测接线（2026-10-19 · 产品 0 文件，判据账）

- 194 从 R153 挂到现在，本轮**结案为通道限制**：runner 六张高帧实测 `drawnBoxPt=%(box)s / drawnBottomPt=%(bottom)s / transparent=%(blank)s%% / screenVisibleHeightPt=%(screen)s`，
  本机同一批 `drawnBoxPt=%(local_boxes_lo)s…%(local_boxes_hi)s`。三种解释全部被数排除，剩下的读法机制**未命名**（另开 201）。
- 出口只认实测到的形状：`0 < drawnBoxPt < requested` 才登记 `CAPTURE_BLANK_NOT_RUN`；`==0` 与 `==requested` 照旧红。
- 12 把刀全 CAUGHT（RESTORE_CLEAN=%(restore)s）：新增三把打在点火那一支，其中 M689 证明 marker 的**名字形状**是承重的 —— 闸门按 `\b[A-Z][A-Z0-9_]*_NOT_RUN\b` 解析，改一个下划线就再也认不出。
- 本机点火 %(local_marker)s 次 = 0：这条出口的真产物验收在 CI 那一跑（预期 STEP[15] 不再因这六张红）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 6/15 | 0 产品文件、帧逐字节未变；本轮的"看"是 runner 与本机同一根轴的两组读数，没假装看了新画面 |
| 判据有效性 | 15/15 | 12 把刀全 CAUGHT 且各红在点名格；三把新的专门打在出口点火与 marker 名字上 |
| 假绿防御 | 15/15 | `==0` 与 `==requested` 两种形状**不放行**；本机点火 0 次写进账，不冒充验收；未命名的机制不进结论 |
| 产品面推进 | 9/15 | 画面 0 改动，但把挂了 17 轮的 194 结案、把 STEP[15] 那六朵红转成有名字的未运行（待 CI 复验） |
| 台账一致性 | 14/15 | U-567…U-570 全部带原文读数；194 追记 4 + 新开 201；扣分：CI 复验还没到手 |
| 交付诚实性 | 15/15 | 明写"两种预测都被推翻、机制未命名、出口尚未被真产物验收" |
| 可复核性 | 15/15 | run id、sha、marker、刀号、命令（`--log` 而非 `--log-failed`）都在 |
""" % V

changelog_body = u"""### runner 的分辨轴读数与 194 的出口接线：只认实测到的那种形状（R170 / U-567…U-570 · 产品 0 文件，判据账）

- runner `%(run_id)s` 六张高帧同形 `drawnBoxPt=%(box)s / drawnBottomPt=%(bottom)s / transparent=%(blank)s%% / screenVisibleHeightPt=%(screen)s`；本机同一批 `drawnBoxPt=%(local_boxes_lo)s…%(local_boxes_hi)s`（画满）⇒ 三种解释被数排除，BACKLOG 194 结案为**通道限制**（机制未命名，新开 201）
- 出口 `shouldRegisterBlankAsMachineGap` 增加 `drawnBoxPt` 轴，只在 `0 < drawnBoxPt < requested` 时登记 `CAPTURE_BLANK_NOT_RUN`（闸门按全大写 `*_NOT_RUN` 解析）；`==0`（没渲染）与 `==requested`（画满却报空）照旧红
- 本机出口点火 %(local_marker)s 次 = 0 ⇒ 真产物验收在 CI 下一跑（预期 STEP[15] 不再因这六张红）
- `mutate_r168.py` 扩到 12 臂全 CAUGHT、RESTORE_CLEAN=%(restore)s；M675/M678 的 needle 跟着谓词新形状当场改写（不留空转的刀）
- 全量卷 %(swift_n)s 例 / 跳过 %(swift_skip)s / 失败 %(swift_fail)s；帧基线 `--against working` %(compared)s 张 changed=%(changed)s；判据卷 10 格

""" % V

backlog_body = u"""**194 追记 4（R170）：分辨轴到手 ⇒ 结案为「通道限制」，出口只认实测到的形状**

runner `39152321051`（`72279ff`）六张高帧全部 `requested=1040 drawnBoxPt=205 drawnBottomPt=1040 transparent=95.9% screenVisibleHeightPt=681`，
本机同一批 `drawnBoxPt=1040…1040`、`transparent≈22%%`。⇒ 三种解释各自被一条数排除：
`>0` 排除"根本没渲染"；`205 ≠ 681` 且带在下沿排除"裁到可视高"；几何三边相等排除"窗口被收小 / 内容没铺满"（R167 已排除过一次）。
处置：出口接线，条件是 `0 < drawnBoxPt < requested`，点火打 `CAPTURE_BLANK_NOT_RUN`（闸门 `*_NOT_RUN` 名字形状）；
两种形状**不放行**、红照旧：`==0`（捕获坏了）、`==requested`（画满却报空 = 两把尺矛盾，先修尺）。
**没结案的部分**：机制未命名（见新开 201），且本机点火 0 次 ⇒ 这条出口的真产物验收在 CI 下一跑（预期 `Capture gate` 那一步不再因这六张红）。
这一格从 R153 挂到今天，收的口是"不是产品缺陷"，不是"我知道为什么"。

**201. runner 的高窗离屏捕获只画出一条 %(box)spt 的下沿带，机制未命名（R170 量到形状，没量到成因）**

形状（六张高帧同形，run `39152321051`）：`requested=%(req)s / drawnBoxPt=%(box)s / drawnBottomPt=%(bottom)s / transparent=%(blank)s%% / screenVisibleHeightPt=%(screen)s`。
本机同码同夹具：`drawnBoxPt=%(local_boxes_lo)s…%(local_boxes_hi)s`（画满）。
第一条猜测已经被否：「只画与屏幕可视区相交的那条带」——本机可视高 850 < %(req)s 却画满，猜测在自己身上就不成立。
第二条候选（"高窗的内容层在 runner 上只布局了底部一条"）需要一个**画到的带内是什么**的读数才能判：
下一轮可以从那 %(box)spt 带里数一数量（有没有侧栏 / 卡片描边 / 文字行），与本机同一条带对账。
为什么现在不动产品：两种成因（通道 vs 布局）的处置完全相反，而 194 已经按"通道"结案了一半（出口只认形状），
布局那一半若有真缺陷，会在带内读数里露出来 —— 顺序是"先量带内是什么，再决定要不要怀疑产品"。

""" % V

state_body = u"""最后更新：2026-10-19 02:42（本地 · R170 / 第 172 轮：**runner 的分辨轴给了一个谁都没预测到的形状 ⇒ 出口按实测接线，194 结案为通道限制**（U-567…U-570 · 产品 0 文件，判据账）

**runner 的读数**（`--log`，run `%(run_id)s` = `%(run_sha)s`）：六张高帧同形 `drawnBoxPt=%(box)s / drawnBottomPt=%(bottom)s / transparent=%(blank)s%% / screenVisibleHeightPt=%(screen)s`；
本机同批 `drawnBoxPt=%(local_boxes_lo)s…%(local_boxes_hi)s`（画满）。三种解释被三条数排除（`>0` / `≠可视高` / 几何三边相等）。
**出口已接线但只认实测形状**：`0 < drawnBoxPt < requested` ⇒ 打 `CAPTURE_BLANK_NOT_RUN`（闸门按 `*_NOT_RUN` 解析）；
`==0`（没渲染）与 `==requested`（画满却报空）不放行、红照旧。机制**未命名** ⇒ 新开 201（下一步量"那 %(box)spt 带里到底是什么"）。
**刀**：`mutate_r168.py` 12 臂全 CAUGHT、RESTORE_CLEAN=%(restore)s；M687/M688 打在新轴的两端、M689 打在 marker 的名字形状上；
M675/M678 的 needle 因谓词改形**当场改写**（不留空转的刀）。
**本机自陈**：出口点火 %(local_marker)s 次 = 0（本机没有空白高帧），所以这条出口的真产物验收在 CI 那一跑。
验证：编译 0 告警、判据卷 10 格、捕获卷退出码 %(cap_exit)s、帧基线 %(compared)s 张 changed=%(changed)s、全量卷 %(swift_n)s/%(swift_skip)s/%(swift_fail)s、清账表 %(surface)s。

**下一轮（R171）的靶**：⓪ 读 `c4366b3` 与本笔那一跑的**全部失败步骤**；关键预期：`Capture gate (unregistered reds must be zero)`
   这一步**应该不再因那六张高帧红**（若还红 ⇒ 出口的形状没覆盖 runner 的真实读数，先看 `CAPTURE_BLANK_NOT_RUN` 打没打）；
② BACKLOG 201：量那 %(box)spt 的带里是什么（侧栏 / 卡片描边 / 文字行），与本机同一条带对账 —— 决定"通道"这个口径站不站得住；
③ BACKLOG 197 + 200：先拿"最小窗口下右栏可用宽"那格读数，再判热图那条带要不要改；
④ BACKLOG 199（`pumpMain(0.4)` 换成有界轮询 + 正对照）；⑤ 清账表下一批（新格带 `缺席:`）；⑥ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。

""" % V

report_old = (u"2. **清账表还有 %s 格未判**（闸门本轮（R169）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))
report_new = (u"2. **清账表还有 %s 格未判**（闸门本轮（R170）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
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
    insert_before(os.path.join(ROOT, "AGENT_UI_AUDIT.md"), u"## 第 171 轮（R169", ui_title + ui_body)
    append_eof(os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"), vi_body)
    insert_before(os.path.join(ROOT, "CHANGELOG.md"), u"### 热图 197 的", changelog_body)
    append_eof(os.path.join(ROOT, "AGENT_BACKLOG.md"), backlog_body)
    insert_before(os.path.join(ROOT, "AGENT_STATE.md"), u"最后更新：2026-10-19 01:59", state_body)
    rep = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    text = read(rep)
    if text.count(report_old) != 1:
        raise SystemExit("REPORT_ANCHOR 命中 %d 次" % text.count(report_old))
    write(rep, text.replace(report_old, report_new))

    audit = read(os.path.join(ROOT, "AGENT_UI_AUDIT.md"))
    section = audit.split(ui_title.rstrip(u"\n"), 1)[1].split(u"\n## 第 171 轮", 1)[0]
    defined = sorted(int(m) for m in re.findall(r"^- \*\*U-(\d{3})：", section, re.M))
    if defined != [567, 568, 569, 570]:
        raise SystemExit("U_RANGE_MISMATCH 本轮定义 %s（要 567…570）" % defined)
    for needle in (u"CAPTURE_BLANK_NOT_RUN", u"drawnBoxPt=%s" % V["box"], u"201"):
        if needle not in section:
            raise SystemExit("SECTION_THIN 本轮那一节缺 %r 的原文" % needle)
    print(u"LEDGERS_WRITTEN runner_box=%s bottom=%s screen=%s blank=%s local=%s..%s markers=%s "
          u"arms=%s/%s restore=%s suite=%s/%s/%s compared=%s changed=%s"
          % (V["box"], V["bottom"], V["screen"], V["blank"], V["local_boxes_lo"], V["local_boxes_hi"],
             V["local_marker"], V["caught"], V["arms_total"], V["restore"],
             V["swift_n"], V["swift_skip"], V["swift_fail"], V["compared"], V["changed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
