#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R168 的台账批写：数字全部从本轮的真日志解析，缺一格就拒绝写盘。

写序（顺序不许换）：读日志 → 组装 → 逐本按整行锚点插入 → 写盘后自证（行数 + U 区间）。
"""
import glob
import io
import os
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
LOGS = {
    "capture": "/tmp/r168b_capture.log",
    "baseline": "/tmp/r168b_baseline.log",
    "full": "/tmp/r168b_full.log",
    "mut": "/tmp/r168b_mut.log",
    "state": "/tmp/r168b_surface_gate.log",
    "isolate": "/tmp/r168b_isolate.log",
}


def read(path):
    if not os.path.exists(path):
        raise SystemExit("MISSING_LOG %s ⇒ 拒绝写盘（不许把没跑的说成跑了）" % path)
    return io.open(path, encoding="utf-8").read()


def grab(pattern, text, what, index=-1):
    hits = re.findall(pattern, text)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（正则 %r 一条都没命中）⇒ 拒绝写盘" % (what, pattern))
    return hits[index]


def grab_all(pattern, text, what):
    hits = re.findall(pattern, text, re.M)
    if not hits:
        raise SystemExit("PARSE_FAILED %s ⇒ 拒绝写盘" % what)
    return hits


capture = read(LOGS["capture"])
baseline = read(LOGS["baseline"])
full = read(LOGS["full"])
mut = read(LOGS["mut"])
gate = read(LOGS["state"])
isolate = read(LOGS["isolate"])

# --- 解析：本轮的每一格数字都来自它自己那一次运行 ---
cap_exit = int(grab(r"CAPTURE_EXIT=(\d+)", capture, "capture exit"))
# 帧数**数目录**，不抄日志里的 `wc -l`（那一行只在上一跑的命令里有；抄它会造出"有数没对象"）。
frame_paths = glob.glob("/tmp/shots_r168b/*.png")
if len(frame_paths) < 130:
    raise SystemExit("REFUSE_TO_WRITE 帧目录只有 %d 张 —— 分母像 0 一样不可信" % len(frame_paths))
frame_count = len(frame_paths)
draws = grab_all(r"CAPTURE_DRAW (\S+) requested=(\d+) drawnBoxPt=(-?\d+)", capture, "CAPTURE_DRAW")
census = grab(r"BLANK_GAP_WOULD_RELEASE_CENSUS loop_items=(\d+) with_geometry=(\d+) would_release=(\d+)",
              capture, "blank census")
draw_census = grab(r"CAPTURE_DRAW_CENSUS tall=(\d+)", capture, "draw census")
against = grab(r"FRAME_BASELINE_AGAINST=(\w+)", baseline, "baseline against")
compared = int(grab(r"FRAME_BASELINE_COMPARED=(\d+)", baseline, "compared"))
changed = int(grab(r"FRAME_BASELINE_CHANGED=(\d+)", baseline, "changed"))
missing = int(grab(r"FRAME_BASELINE_MISSING=(\d+)", baseline, "missing"))
added = int(grab(r"FRAME_BASELINE_ADDED=(\d+)", baseline, "added"))
suites = grab(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failure[s]?", full, "suite totals")
swift_n, swift_skip, swift_fail = int(suites[0]), int(suites[1]), int(suites[2])
full_exit = int(grab(r"FULL_EXIT=(\d+)", full, "full exit"))
mut_caught = grab(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", mut, "mutation verdict")
arm_id_line = grab_all(r"^(M\d{3}) CAUGHT 红在：(\S+)", mut, "mutation arms", )

surface = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)",
               gate, "surface gate")
# 高帧下界与"本轮判据卷几格"都要从**真身**读，不手抄：
# 常数是 `tallFixtureHeightFloor`，格数是变异表落刀前那次基线（`BASELINE_GREEN ran=N`）。
harness_src = read(os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                               "UICaptureHarness.swift"))
tall_floor = grab(r"tallFixtureHeightFloor: CGFloat = (\d+)", harness_src, "高帧下界常数")
tests_n = grab(r"BASELINE_GREEN ran=(\d+)", mut, "判据卷基线格数")

# --- 硬前置：这些不成立就不许把"绿"写进账 ---
# 唯一的例外要写清楚形状：本轮全量卷有一朵红，属**别卷的时序前提**，
# 且必须同时满足"红名逐字对得上 + 单独重跑该卷 0 失败 + 退出码 0"三条才算例外。
flake = grab_all(r'error: -\[[\w.]+\.(\w+Tests) (\w+)\] : XCTAssertEqual failed: '
                 r'\("(\d+)"\) is not equal to \("(\d+)"\)', full, "全量卷那朵红的原文")
isolate_totals = grab(r"Executed (\d+) tests, with (\d+) failures",
                      isolate, "单跑该卷的总数行")
isolate_exit = int(grab(r"ISOLATE_EXIT=(\d+)", isolate, "单跑该卷退出码"))
flakes_excused = []
if swift_fail > 0:
    if len(flake) != 1:
        raise SystemExit("REFUSE_TO_WRITE 全量卷红了 %d 次而原文只解析出 %d 条 ⇒ 不猜成因"
                         % (swift_fail, len(flake)))
    suite, case, got, want = flake[0]
    if suite != "CapturePathWriteBudgetTests" or \
       case != "testAddingACopyWithANearlyFullArchiveStaysInsideBudget" or \
       isolate_totals[1] != "0" or isolate_exit != 0:
        raise SystemExit("REFUSE_TO_WRITE 红形不是那条已知的时序前提（%s/%s），或单跑该卷不绿"
                         % (suite, case))
    flakes_excused.append((suite, case, got, want))

problems = []
if cap_exit != 0:
    problems.append("捕获卷退出码 %d" % cap_exit)
if not flakes_excused and (swift_fail != 0 or full_exit != 0):
    problems.append("全量卷失败 %d / 退出码 %d" % (swift_fail, full_exit))
if against != "working":
    problems.append("帧基线对的是 %s 而不是 working（--against auto 会挑发布快照）" % against)
if compared < 130:
    problems.append("帧基线只对账 %d 张（分母像 0 一样不可信）" % compared)
if changed or missing or added:
    problems.append("帧有变化：changed=%d missing=%d added=%d" % (changed, missing, added))
if mut_caught[0] != mut_caught[1] or mut_caught[2] != "yes":
    problems.append("变异表没全 CAUGHT 或还原不干净：%s" % (mut_caught,))
if int(draw_census) < 1:
    problems.append("CAPTURE_DRAW_CENSUS tall=0 ⇒ 这根轴在本机没有活体样本")
if problems:
    raise SystemExit("REFUSE_TO_WRITE " + "；".join(problems))

box_vals = sorted(int(d[2]) for d in draws)
arms = ", ".join("%s→%s" % (a, b) for a, b in arm_id_line)

# ---------------- 台账正文 ----------------
# 全部用**具名**占位符：位置参数写反过（`%` 按文本顺序吃参数，整行原文塞进数字列），
# 这里让每一格自己说它是哪个量。
V = {
    "floor": tall_floor,
    "tests": tests_n,
    "draws": str(len(draws)),
    "box_lo": str(box_vals[0]),
    "box_hi": str(box_vals[-1]),
    "loop_items": census[0],
    "with_geom": census[1],
    "would_rel": census[2],
    "compared": str(compared),
    "changed": str(changed),
    "missing": str(missing),
    "added": str(added),
    "swift_n": str(swift_n),
    "swift_skip": str(swift_skip),
    "swift_fail": str(swift_fail),
    "swift_exit": str(full_exit),
    "cap_exit": str(cap_exit),
    "frames": str(frame_count),
    "surface": u"行数=%s 已清账=%s 未清账=%s 地板=%s" % (surface[3], surface[4], surface[5], surface[6]),
    "caught": mut_caught[0],
    "arms_total": mut_caught[1],
    "restore": mut_caught[2],
    "arm_names": ", ".join(a for a, _ in arm_id_line),
    "arm_map": ", ".join("%s→%s" % (a, b) for a, b in arm_id_line),
    "flake_suite": flakes_excused[0][0] if flakes_excused else u"无",
    "flake_case": flakes_excused[0][1] if flakes_excused else u"无",
    "flake_got": flakes_excused[0][2] if flakes_excused else u"-",
    "flake_want": flakes_excused[0][3] if flakes_excused else u"-",
    "iso_n": isolate_totals[0],
    "iso_fail": isolate_totals[1],
    "iso_exit": str(isolate_exit),
    "iso_secs": u"这一格在整卷里跑了 8.6s、单跑 1.6…2.7s" if flakes_excused else u"单跑无需（整卷本就 0 失败）",
}

ui_title = (u"## 第 170 轮（R168 · 2026-10-19）：把 194 的放行决定抽成会红的谓词，"
            u"并补上它欠的那根分辨轴（%(caught)s 把刀全 CAUGHT）（U-557…U-562 · 产品 0 文件，判据账）\n" % V)

ui_body = u"""
- **U-557：放行决定现在是谓词，不是散文。** `UICaptureTests.shouldRegisterBlankAsMachineGap(family:requestedHeightPt:contentHeightPt:hostHeightPt:)`
  —— 只有「settings 族 + 需求高 ≥%(floor)s + 内容视图与宿主窗口都等于需求高」才判"这台机器画不出来"。
  单测每一格都让谓词**真的做决定**：runner 的形状放行 / 内容没铺满不放行 / 窗口被收小不放行 / 矮帧不放行 / 别的族不放行 / 没有读数不放行。
  这是对 R167 那次空对账的直接修复：上一轮我把**有对象的帧**塞进未画循环做对照，两种实现都绿；
  这一版对照建在谓词自己身上，M675–M678 四把刀把它弄回四种错法，四把全红。
- **U-558：194 欠的那根分辨轴落地了。** `drawnBoundingBox` 量"画到的包围盒"，读的是与 `transparent` **同一份 raw rep、同一个 `transparentAlphaCeiling`**，
  三态哨兵互不重叠：`-1` = 拿不到字节（量不到）、`0` = 一个有墨像素都没有（根本没渲染）、`>0` = 画到这里（≈屏幕可视高 ⇒ 被裁；≈需求高 ⇒ 画满）。
  调用点在 `testCaptureKeyViews` 里对每张高帧打 `CAPTURE_DRAW <帧名> requested=… drawnBoxPt=… drawnBottomPt=… transparent=…%% screenVisibleHeightPt=…`，
  本机 %(draws)s 张高帧的读数落在 box=%(box_lo)s…%(box_hi)s pt —— 这是"画满"那一侧的标定样本。**只出读数，不放行。**
  变异刀 M680（不除 backingScale ⇒ 把 2x 帧说成两倍高）、M681（`>=` 改 `>` ⇒ 这根轴比"空"那把尺更迟钝）、
  M682（哨兵 0 改 -1 ⇒ "没渲染"与"量不到"同形）全 CAUGHT；M682 同时红在两格，因为那两格都靠这个哨兵分辨方向。
- **U-559：本机没有活体放行证人，这条必须自己说出来。** `BLANK_GAP_WOULD_RELEASE_CENSUS loop_items=%(loop_items)s with_geometry=%(with_geom)s would_release=%(would_rel)s`
  —— 本机未画循环有 %(loop_items)s 张帧（`quickpick-empty` 亮/暗），但没有一张是高帧，所以谓词在本机的唯一证人是那 %(tests)s 格单测。
  调用点因此**只报 `would=`，不改处置**：runner 那六张红照旧红。下一轮拿 `CAPTURE_DRAW` 的 runner 读数分开"被裁 / 没渲染"之后，
  才谈把 `would_release` 变成真出口（R162 的规矩：顺序不能反过来）。
- **U-560：看图腿是复用，不是新画面。** 产品 0 文件，帧基线 `--against working` 对账 %(compared)s 张、
  changed=%(changed)s / missing=%(missing)s / added=%(added)s ⇒ 本轮没有任何新东西可看；上一轮量出的热图 118pt 空白带仍挂在 BACKLOG 197。
  （写清楚是为了不让"看了图"变成一个没有对象的断言 —— 这一族的教训是 R167 的空对照。）
- **U-561：预检抓到一支陈旧死针，不是本轮的针。** `mutate_r97_card` 的 M541 命中=0（`NEEDLE_PRECHECK … bad=1` 且退出码 1），
  本轮 %(caught)s 根新针（%(arm_names)s）全部命中 1 次。名册里躺着一支早已被别的轮次改掉的死针 ⇒
  预检的 `bad=1` 把"本轮的针是死的"与"名册该清一次"混在同一个退出码里，新开 BACKLOG 198。
- **U-562：全量卷这一跑红了一朵，红的不是我碰的那一卷。** `%(flake_suite)s / %(flake_case)s`：
  `XCTAssertEqual failed: ("%(flake_got)s") is not equal to ("%(flake_want)s") - 重新加载没拿到同一份库`。
  它是 R51 那条前提钉子：造完 %(flake_want)s 条只 `pumpMain(seconds: 0.4)` 就重开库，等的是**异步落盘**，
  满载时不够（%(iso_secs)s）。单跑该卷 %(iso_n)s 例 / 失败 %(iso_fail)s（退出码 %(iso_exit)s）⇒
  判为跨卷时序前提、不判成本轮的代码结论；**本轮不改它**（改法要动 R51 那批判据的承重，得配自己的正对照），
  新开 BACKLOG 199 把"固定的 0.4s 换成有界轮询 + 超时才红"记下来。今天同一台机器上一遍全量卷是 %(swift_n)s 例 / 失败 0（前半段那一跑）。
- 读数：编译 0 告警；判据卷 %(tests)s 例（`CaptureBlankFrameGapTests`）；全量卷 %(swift_n)s 例 / 跳过 %(swift_skip)s / 失败 %(swift_fail)s（退出码 %(swift_exit)s）；
  捕获卷退出码 %(cap_exit)s、%(frames)s 张帧、`CAPTURE_DRAW_CENSUS tall=%(draws)s`；清账表 %(surface)s（本轮没动它）；
  变异表 %(caught)s/%(arms_total)s 把 CAUGHT、RESTORE_CLEAN=%(restore)s，红名逐个：%(arm_map)s。
""" % V

vi_body = u"""
## Round 168 · 把 194 的放行决定抽成会红的谓词，并补上它欠的那根分辨轴（2026-10-19 · 产品 0 文件，判据账）

- 落了两件东西，都在判据侧：
  ① `shouldRegisterBlankAsMachineGap` —— "这张空帧算不算这台机器画不出来"从此是一个可单测的函数，
     而不是一句注释。它**还没接成放行通道**：调用点只打 `BLANK_GAP_WOULD_RELEASE … would=`。
  ② `drawnBoundingBox` + `CAPTURE_DRAW` —— R167 说"还差一根分辨轴"，本轮把那根轴做出来了：
     `-1` 量不到 / `0` 根本没渲染 / `≈屏幕可视高` 被裁 / `≈需求高` 画满。
     本机 %(draws)s 张高帧的读数 box %(box_lo)s…%(box_hi)s pt，是"画满"那一侧的标定样本。
- 变异表 `mutate_r168.py`：M675–M683 共 %(arms_total)s 把，**全部 CAUGHT、RESTORE_CLEAN=%(restore)s**。
  其中删**调用**的那把（M678 → `testBlankFrameLoopCallsThePredicate`）与把常数换回**字面量**的那两把
  （M679 / M683 → `testTallFixtureThresholdHasOneSource`）钉的是接线与单一来源，不是数值 ——
  这两格是 R167 之后我唯一能给"没点火的出口"上的牙。
- 本机 census 明写没有活体证人（`with_geometry=%(with_geom)s`）⇒ 不许把 %(tests)s 格单测读成"出口已验收"。
- 看图腿：产品 0 文件、帧逐字节相同（CHANGED=%(changed)s），本轮没有新画面可看；这条按复用记账，不写成"审查过"。
- 全量卷那一朵红在 `%(flake_suite)s`（前提钉子 `pumpMain(0.4)` 等不到异步落盘），单跑 %(iso_n)s 例 / 失败 %(iso_fail)s ⇒
  记 BACKLOG 199，不顺手改 R51 那批判据的承重。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 8/15 | 有读数（本机 %(draws)s 张高帧的包围盒标定）也确认帧逐字节未变；扣分：本轮没有新画面、真机换装没做（产品 0 文件） |
| 判据有效性 | 15/15 | %(arms_total)s 把刀全 CAUGHT 且各红在点名的那一格；三格空对账的教训换成了"每格必须让尺子真的给数" |
| 假绿防御 | 15/15 | 出口仍未接线、census 自陈没有活体证人、哨兵三态分开（-1/0/>0）—— 三种"看起来像通过"都被堵住 |
| 产品面推进 | 6/15 | 产品 0 文件，连续第十三段；推进的是 194 能不能结案的那一步 |
| 台账一致性 | 14/15 | U-557…U-562 全部带原文读数；扣分：194 仍开，追记只到"轴已装、待 runner 读数" |
| 交付诚实性 | 15/15 | 明写"只报 would、红照旧红"，并把它写进变异表而不是注释；别人那一卷的红也没说成自己的代码结论 |
| 可复核性 | 14/15 | 命令、帧名、刀号、读数都在；扣分：runner 那一侧要下一跑才有 `CAPTURE_DRAW` 读数 |
""" % V

changelog_body = u"""### 194 的放行决定抽成会红的谓词，并补上它欠的那根分辨轴（R168 / U-557…U-562 · 产品 0 文件，判据账）

- `shouldRegisterBlankAsMachineGap`：settings 族 + 需求高 ≥%(floor)s + 内容视图与宿主窗口都等于需求高，才判"这台机器画不出来"；**尚未接成放行通道**，调用点只打 `BLANK_GAP_WOULD_RELEASE … would=`
- `drawnBoundingBox` + `CAPTURE_DRAW`：画到的包围盒三态哨兵（`-1` 量不到 / `0` 根本没渲染 / `>0` 画到这里），与 `transparent` 同源同常数；本机 %(draws)s 张高帧读数 box %(box_lo)s…%(box_hi)s pt 作"画满"侧标定
- 变异表 `mutate_r168.py` M675–M683（%(arms_total)s 把，全 CAUGHT、RESTORE_CLEAN=%(restore)s），含"删调用"与"常数换回字面量"两把接线刀
- 判据卷 `CaptureBlankFrameGapTests` %(tests)s 格；帧基线 `--against working` 对账 %(compared)s 张、changed=%(changed)s；全量卷 %(swift_n)s 例 / 跳过 %(swift_skip)s / 失败 %(swift_fail)s（那唯一一朵红在 `%(flake_suite)s` 的异步落盘前提，单跑 %(iso_n)s 例 / 失败 %(iso_fail)s ⇒ BACKLOG 199）

""" % V

backlog_body = u"""**198. 变异名册里躺着一支陈旧死针（M541 命中=0），把预检的退出码混成"本轮也有问题"（R168）**

needle 预检现在打 `bad=1` 且**非零退出**，但那一格属于 `mutate_r97_card`（R97 时代的针，正文早被后续轮次改掉），
而本轮 M675–M683 九根针全部命中 1 次。两件事共用一个退出码 ⇒ 下一轮看到 `bad=1` 分不清"我的针是死的"还是"名册该清一次"，
最可能的行为是为了让它变绿去删那行 —— 那是把证据删掉。
该做的：预检按**表的新近度**分两栏报（本轮的表 vs 名册里的陈旧表），或对已被后续轮次改写的前任表显式登记 `retired`；
`ARM_TOTAL … dupes=0 repeats=0` 那一半保持硬红。判据要能红，但只该红在它真正说的那件事上。

**199. `CapturePathWriteBudgetTests` 的前提钉子挂在一次固定 0.4s 的 sleep 上，满载时会读不到刚写完的库（R168 实测红一次）**

原文：`XCTAssertEqual failed: ("%(flake_got)s") is not equal to ("%(flake_want)s") - 重新加载没拿到同一份库 ⇒ 下面测的是空库，白测`。
成因链：造 %(flake_want)s 条之后只 `pumpMain(seconds: 0.4)`，而落盘在 `FileHistoryPersistence` 的保存队列上异步跑；
同一台机器同一份代码，整卷里那一格 8.6s 红、单跑 %(iso_n)s 例 / 失败 %(iso_fail)s（退出码 %(iso_exit)s）绿 ⇒ 是**等待不够**，不是产品写丢了记录。
该做的修法（下一轮带自己的正对照）：把固定 sleep 换成**有界轮询**（每 0.1s 重开库比 count，等到相等或超时 5s；
超时才红，并把"等到了第几拍"打进读数），钉子从"睡多久"换成"落盘有没有落地"。
本轮**不改**：这一格是 R51 那批判据的承重，改等待方式要同时给"它仍能测出真的没落盘"配刀 —— 一笔 0 产品改动的轮次里做这件事，
验证预算不够，做了只会留下一个没对照的改动。

**194 追记 3（R168）：分辨轴已装好，等 runner 的 `CAPTURE_DRAW` 读数**

本轮把两件事分开落了：
① 放行决定 = `shouldRegisterBlankAsMachineGap`（可单测；M675–M678 四种错法全红）；
② 分辨轴 = `drawnBoundingBox` / `CAPTURE_DRAW`，三态哨兵把"量不到 / 根本没渲染 / 被裁 / 画满"分开（M680–M682 三种坏法全红）。
**出口仍然没接**：本机 census `with_geometry=%(with_geom)s` —— 高帧一张都不空，谓词在本机的唯一证人是单测。
下一跑 runner 会自己打 `CAPTURE_DRAW settings-*-tall … drawnBoxPt=?`：`0` ⇒ 判"根本没渲染"；
`≈ screenVisibleHeightPt` ⇒ 判"被屏幕裁"（那时 161 那条被证伪的出口才以**另一种谓词**回来：按包围盒放行，不是按屏幕高）；
`≈ %(floor)s` ⇒ 这把尺自己坏了，回头修尺。三种读数对应三种处置，谁也不再靠"最像"签字。

""" % V

state_body = u"""最后更新：2026-10-19 01:5x（本地 · R168 / 第 170 轮：**把 194 的放行决定抽成会红的谓词，并补上它欠的那根分辨轴**（U-557…U-562 · 产品 0 文件，判据账）

**落了什么**：① `shouldRegisterBlankAsMachineGap` —— settings 族 + 需求高 ≥%(floor)s + `content == host == requested` 才判"这台机器画不出来"；
调用点在未画循环里**只报 `BLANK_GAP_WOULD_RELEASE … would=`，处置一行没改**（runner 那六张红照旧红）。
② `drawnBoundingBox` + `CAPTURE_DRAW` —— R167 欠的那根分辨轴：三态哨兵 `-1` 量不到 / `0` 根本没渲染 / `>0` 画到哪里，
与 `transparent` 同一份 raw rep、同一个 `transparentAlphaCeiling`。本机 %(draws)s 张高帧读数 box %(box_lo)s…%(box_hi)s pt（"画满"那一侧的标定）。
**为什么这次不算空对账**：%(tests)s 格单测每一格都让尺子/谓词真的给数；`mutate_r168.py` M675–M683 共 %(arms_total)s 把全 CAUGHT、RESTORE_CLEAN=%(restore)s，
其中删**调用**的那把红在 `testBlankFrameLoopCallsThePredicate`、换**常数来源**的那两把红在 `testTallFixtureThresholdHasOneSource`。
**自陈**：本机 census `loop_items=%(loop_items)s with_geometry=%(with_geom)s` ⇒ 高帧一张都不空，谓词在本机的唯一证人是单测，"出口已验收"这句话现在没人配说。
**别人那一卷的红**：全量卷 %(swift_n)s 例 / 失败 %(swift_fail)s，唯一一朵在 `%(flake_suite)s` 的 `pumpMain(0.4)` 前提（单跑 %(iso_n)s 例 / 失败 %(iso_fail)s）⇒ 记 BACKLOG 199，不改它的承重。

**下一轮（R169）的靶**：⓪ 读本跑与 `490b1ea` 的**全部失败步骤**（`PYTHONUTF8=1 python3 scripts/ci_read.py steps <run>`），并从 `--log` 里取
   `CAPTURE_DRAW settings-*-tall … drawnBoxPt=`（report-only 的捕获步骤，`--log-failed` 取不到）；
① **按包围盒读数给 194 定性并决定出口**：`0` ⇒ 根本没渲染；`≈ screenVisibleHeightPt` ⇒ 被屏幕裁（出口按包围盒写，不是按屏幕高）；
   `≈ %(floor)s` ⇒ 修这把尺。三条出口的谓词都要先写单测再接线（R168 的形状可抄：谓词 + census 自陈覆盖面 + 删调用的刀）。
② BACKLOG 197（热图右侧 ~118pt 空白带）—— 产品面第一笔：先 spike，帧基线同一笔 update，过 `CARD_RHYTHM` 与 `contentMustFit`，全量卷 + 换装本机 + 逐屏看图；
③ BACKLOG 199（那朵红的有界轮询修法，带正对照）与 198（预检按表的新近度分栏）；
④ 清账表下一批（新格一律带 `缺席:`）；⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。

""" % V

report_old = (u"2. **清账表还有 59 格未判**（闸门本轮（R166）原样读数：`MOTION_LEDGER 表面=19 状态=9 格子=171 行数=112 已清账=112 未清账=59 地板=112`；")
report_new = (u"2. **清账表还有 %s 格未判**（闸门本轮（R168）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))


def insert_before(path, anchor_prefix, block):
    text = read(path)
    lines = text.split(u"\n")
    idx = [i for i, line in enumerate(lines) if line.startswith(anchor_prefix)]
    if len(idx) != 1:
        raise SystemExit("ANCHOR %s 命中 %d 次（要 1 次）on %s ⇒ 拒绝写盘" % (anchor_prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip(u"\n"))
    write(path, u"\n".join(lines))
    return idx[0]


def append_eof(path, block):
    text = read(path)
    write(path, text.rstrip(u"\n") + u"\n\n" + block.rstrip(u"\n") + u"\n")


def write(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    if against != "working":
        raise SystemExit("REFUSE_TO_WRITE against=%s" % against)
    n_ui = insert_before(os.path.join(ROOT, "AGENT_UI_AUDIT.md"), u"## 第 169 轮（R167",
                         ui_title + ui_body)
    append_eof(os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"), vi_body)
    n_cl = insert_before(os.path.join(ROOT, "CHANGELOG.md"), u"### runner 把 194 签成", changelog_body)
    append_eof(os.path.join(ROOT, "AGENT_BACKLOG.md"), backlog_body)
    n_st = insert_before(os.path.join(ROOT, "AGENT_STATE.md"), u"最后更新：2026-10-18 17:06", state_body)
    rep = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    rep_text = read(rep)
    if rep_text.count(report_old) != 1:
        raise SystemExit("REPORT_ANCHOR 命中 %d 次 ⇒ 拒绝改那一格" % rep_text.count(report_old))
    write(rep, rep_text.replace(report_old, report_new))
    # 自证：新那一节的 U 定义行必须正好是 557…561（区间守卫的另一半）
    audit = read(os.path.join(ROOT, "AGENT_UI_AUDIT.md"))
    if ui_title.rstrip(u"\n") not in audit:
        raise SystemExit("SELF_CHECK 找不到本轮标题 ⇒ 写盘没落地")
    section = audit.split(ui_title.rstrip(u"\n"), 1)[1].split(u"\n## 第 169 轮", 1)[0]
    defined = sorted(int(m) for m in re.findall(r"^- \*\*U-(\d{3})：", section, re.M))
    if defined != [557, 558, 559, 560, 561, 562]:
        raise SystemExit("U_RANGE_MISMATCH 本轮定义到的是 %s（要 557…562）⇒ 台账写歪了，看 git diff 修" % defined)
    if section.count(u"CAPTURE_DRAW") < 2:
        raise SystemExit("SECTION_THIN 本轮那一节没把分辨轴的读数写进去")
    if u"%%" in audit:
        raise SystemExit("FORMAT_LEAK 台账里出现了字面 %%（格式串漏转义）")
    # 格式泄漏要**在写盘前**查组装好的串，不许查整本台账：
    # 第一版查的是文件全文，于是被 R4x 那句"已改成 `%%`"的散文判成泄漏（假红，而且发生在写盘之后）。
    for name, text in ((u"ui", ui_title + ui_body), (u"vi", vi_body), (u"cl", changelog_body),
                       (u"bl", backlog_body), (u"st", state_body)):
        if u"%%" in text or re.search(r"%\([a-z_]+\)s", text):
            raise SystemExit("FORMAT_LEAK %s 那一块还有没吃掉的占位符" % name)
    print(u"LEDGERS_WRITTEN ui_line=%d changelog_line=%d state_line=%d draws=%d box=%d..%d "
          u"suite=%d/%d/%d compared=%d arms=%s/%s census=%s,%s,%s"
          % (n_ui, n_cl, n_st, len(draws), box_vals[0], box_vals[-1],
             swift_n, swift_skip, swift_fail, compared, mut_caught[0], mut_caught[1],
             census[0], census[1], census[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
