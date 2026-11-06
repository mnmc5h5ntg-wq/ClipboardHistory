# -*- coding: utf-8 -*-
"""R593 台账写手（七本，整行锚点 + 幂等守卫 + 落盘后派生格）。

本轮新加的两条纪律（靶 4）就长在这一支身上，不是写在 ⑨ 里的话：
1. **⓪ 没读就不许落盘** —— 落笔之前先调 `scripts/ledger_preflight.judge`，
   本轮那一节的 ⓪ 里既没有成对号也没有具名未到数 ⇒ 当场 exit 1 并点名是哪一本没写成；
2. **删除行数自己算** —— 写完立刻跑 `git diff --numstat`，除 `AGENT_FINAL_REPORT.md` 的派生格之外
   任何一本出现删除行 ⇒ 当场 exit 1（R577 那一族第九次：批量补丁把别人的历史删掉，只有 numstat 能发现）。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r593.py --check    # 只算文本，不落盘
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r593.py --apply    # 落七本 + 派生格
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TMP = "/tmp/r593"
DATE = u"2026-11-06"

BOOKS = {
    u"UI": u"AGENT_UI_AUDIT.md",
    u"ITER": u"AGENT_VISUAL_ITERATION.md",
    u"STATE": u"AGENT_STATE.md",
    u"BACKLOG": u"AGENT_BACKLOG.md",
    u"DEC": u"AGENT_DECISIONS.md",
    u"FINAL": u"AGENT_FINAL_REPORT.md",
    u"CHANGE": u"CHANGELOG.md",
}

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ledger_preflight  # noqa: E402


def read(book):
    with io.open(os.path.join(ROOT, BOOKS[book]), encoding=u"utf-8") as handle:
        return handle.read()


def write(book, text):
    with io.open(os.path.join(ROOT, BOOKS[book]), u"w", encoding=u"utf-8", newline=u"\n") as handle:
        handle.write(text)


def must_read(path, label):
    if not os.path.exists(path):
        raise SystemExit(u"读数缺失：%s（%s）⇒ 先跑那一趟，不许手填" % (label, path))
    with io.open(path, encoding=u"utf-8", errors=u"replace") as handle:
        return handle.read()


def grep_line(text, prefix, label, last=False):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数里找不到前缀 %r（%s）" % (prefix, label))
    return (rows[-1] if last else rows[0])


def identity_from_disk():
    """轮次身份从盘上现读并交叉核对（STATE 最新节 +1 ⇒ UI 那一侧必须刚好差两轮）。

    不写死、不抄派单：R576 那一笔漏写身份被判红、R577 那次"记忆里的数"当成盘上的事实，都是这一格没现读。
    """
    ui = read(u"UI")
    prev_n = max(int(x) for x in re.findall(u"(?m)^## 第 (\\d+) 轮（R\\d+", ui))
    state_r = max(int(x) for x in re.findall(u"(?m)^## R(\\d+) 状态", read(u"STATE")))
    r = state_r + 1
    if prev_n != r - 2:
        raise SystemExit(u"身份交叉核对失败：STATE 最新节是 R%d ⇒ 本轮应是第 %d 轮，而 UI 最新一节写着第 %d 轮"
                         % (state_r, r - 1, prev_n))
    return {u"r": r, u"n": r - 1, u"round": r - 3, u"prev_n": prev_n, u"prev_r": r - 1}


def gather():
    d = {}
    i = identity_from_disk()
    d[u"ident"] = i
    d[u"ci"] = must_read(os.path.join(TMP, "ci_status.txt"), u"⓪ 现读")
    d[u"ci_json"] = must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 逐字读数")
    d[u"blind"] = must_read(os.path.join(TMP, "blind.txt"), u"帧通道盲区那一支")
    d[u"preflight"] = must_read(os.path.join(TMP, "preflight.txt"), u"⓪ 前置门")
    d[u"order"] = must_read(os.path.join(TMP, "order.txt"), u"读数行顺序")
    d[u"content"] = must_read(os.path.join(TMP, "bundle_content.log"), u"产物内容那一维")
    d[u"knife"] = must_read(os.path.join(TMP, "knife_status.txt"), u"刀末态")
    d[u"precheck"] = must_read(os.path.join(TMP, "precheck.txt"), u"针预检")
    d[u"capture"] = must_read(os.path.join(TMP, "capture_summary.txt"), u"捕获那一卷")
    d[u"gate"] = must_read(os.path.join(TMP, "gate_local.txt"), u"帧基线那一门")
    d[u"look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿")
    d[u"full"] = (must_read(os.path.join(TMP, "full_summary.txt"), u"全量卷")
                  if os.path.exists(os.path.join(TMP, "full_summary.txt"))
                  else u"（未读到：那一趟还没跑 ⇒ 台账不许替它填数）")
    d[u"paths"] = must_read(os.path.join(TMP, "paths.txt"), u"产品/守卫文件清单")
    d[u"swift_read"] = must_read(os.path.join(TMP, "swift_readings.txt"), u"本轮新读数逐字")
    return d


def block_state(d):
    i = d[u"ident"]
    return u"""## R593 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · **产品 2 文件**（√2 不变量补上「放得下」那一半）+ 判据 +34 格 + 刀 M1598–M1610 十三把全 CAUGHT + ⓪ R592 主笔那一跑到数、五条预测三中一不中一未读到）

⓪ **现读两对（`ci_status_r593.py`，取值时刻 20:04–20:11，主笔那一跑 `completed / failure`、补记笔那一跑 `in_progress`）**：
   1. `42210166309 ↔ 03b48b2`（R592 主笔）⇒ 全部失败步骤逐字：
```
%(ci)s
```
   2. `42211799683 ↔ 5b20a61`（R592 补记笔）⇒ `in_progress` ⇒ **未到数**（0 字节日志 = 通道还没内容，
      不是内容里没有）；这一格与上面那格是两种不同的账，本轮不判它那五条预测。
   3. **R592 那五条预测由脚本判（不目测）**：
      · ②`SMOKE_TARGET=/tmp/时间剪史_bundle/时间剪史.app` ⇒ **中** —— 构建落点那一改在 runner 上生效；
      · ③新硬步骤 `REPO_ROOT_BUNDLE_RESULT=ok` 且 `READER_SELFTEST=seen` ⇒ **中** —— 620 那一维第一次在 runner 上有读数；
      · ⑤`Ran 932`（R591 那一跑是 918，本轮 python 侧 +14）⇒ **中**，且口径就是本轮 ⓪ 现读收紧的那一条；
      · ④红名集合不超出那 7 条 ⇒ **不中** —— 多出来的一朵是 **R592 自己新加的判据**
        `testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio`（STEP[16]，`743.0 ≠ 860.0`），
        成因是**夹具前提写死在本机屏幕**上：窗口顶边 860 在 runner 的可见帧（顶只有 ~743）里放不下 ⇒
        产品按 `originY(clampingTop:)` 把它夹回屏内，那一格红的是仪器不是产品。本轮修前提（按 visibleFrame 反推起点，
        并把"放不下"那一档单独判"顶边被夹到可见帧顶部"），见本节① 第 4 条；
      · ⑥`SKIP_ROSTER 键=github-runner` 那一行 ⇒ **未读到**（`CI_CHANNEL_ABSENT`，该行在整份日志里出现 **0 次**）——
        不是"没红"也不是"绿了"：那一格的 `print` 坐在 `inner-red` 那一支的 `self.fail()` **之后**，
        内层一红就连行都印不出来（同一跑 STEP[9] 正是红的）。这就是本轮靶 4 做成仪器的东西，见本节②。
      另：STEP[19] `On-screen probe coverage floor` 在 R591 两跑是 success、这一跑 failure
      （`testFrameIntervalsUnderStateChanges`：最差帧 198.0ms > 锚点 120ms，超锚 3 颗）。
      两条解释本轮**只否掉一条**：探针那扇窗是 `900×640`，距 √2 只有 0.57%% < 容差 2%% ⇒
      `heightLift` 在这一档不出声（本轮把它写成判据 `testHeightLiftTruthTable` 里的一行，不靠注释），
      且 `applyGeometry` 的调用点只有三处（`WindowConfigurator:109`、`AppDelegate:71`、controller:96 折叠切换），
      探针卷一次都不经过它们 ⇒ (甲)「不变量带出来的」被否；剩下的 (乙)「runner 侧采样/负载」
      只能由含本笔的那一跑说，本轮不判（622 那张单继续挂着，一条不代选）。

① **真实推进（产品面 · 规格 §3 第①段对升级用户的交付缺陷的第二半）：√2 不变量补上「放得下」那一半**
   1. 上一轮那句推论（「产品从不记高度 + 13+ 锁住比例 ⇒ 不在 √2 上只能来自锁前的恢复」）只排除了**拖边角**。
      本轮逐条量剩下的通路，两条有读数、一条具名缺席：
      · **放大（Zoom）**：`FOLD_ZOOM_PATH 规格档=848x600 放大档=1201x850 isZoomed=1 放大态离√2=0.0013 不变量出声=0`
        ⇒ 13+ 的 `contentAspectRatio` 把 zoom 也管住了，放大档**天然还在 √2 的容差内** ⇒ 这条通路不构成例外，
        而且这一格把它写成断言（`XCTAssertNil(liftedWhileZoomed)`），下一轮换台机器若前提变了会红在前提上；
      · **系统全屏**：`FOLD_FULLSCREEN_PATH 进全屏=1 全屏档=1470x923 退出后=1470x923 还在全屏=1 不变量出声=1 抬到=1039.4 可见帧高=850.0`
        ⇒ 两件事同时成立：(a) 全屏那一档**确实**会把宽高推到非 √2（不变量会出声）；
           (b) 本机在单测进程里 2.0s 内退不出全屏 ⇒ 退出之后那一档**具名缺席**
           `FOLD_FULLSCREEN_MEASURE_NOT_RUN=exit-not-settled`，不许读成"全屏无害"也不许读成"宽度丢了"；
      · **非整数倍显示缩放 / 外接屏切换**：这台机器只有一块屏 ⇒ 没有证人，本轮不判（开 **667**，出路归用户）。
   2. **落地的产品改动**：`heightLift` 多收一个 `visibleHeight`，目标高度放不下可见帧就**不抬**；
      控制器把 `visible?.height` 喂进去，并把"为什么不抬"记成可读的两格
      （`heightLiftDeclines` 计数 + `heightLiftDecline="visible-too-short"`）。
      理由不是"以防万一"：宽度那一侧**本来就有**同一条界（`targetWidth` 取 `min(floor, visibleWidth)`），
      高度缺这一格是**不对称**；而全屏那一档量到的 1470×923 按 √2 抬是 1039.4 > 可见帧高 850.0 ⇒
      抬上去窗口比屏幕还高、底部够不着。产品入口那格现在能把它量出来：
      `FOLD_LIFT_DECLINE 内容=1470.0x923.0 抬次数=0 不抬次数=1 原因=visible-too-short 可见帧高=850.0`。
   3. 这一改把 D5 的一条边界推到用户面前：**放不下时"比例≈√2"让位于"整扇窗在屏内"**。
      本轮按宽度那一侧的既有先例做了这个选择并写进 D-593，但**接受与否归用户**（667 里列了两条出路）。
   4. 顺带修掉本轮 ⓪ 抓到的那格夹具前提（见 ⓪·3④）：起点由 `NSScreen.main?.visibleFrame` 反推，
      "放得下"与"放不下"两档各判各的，读数行 `FOLD_RATIO_INVARIANT` 多印 `可见帧=…x…@…  放得下=0/1`。
   刀：**M1598**（摘掉「放不下就不抬」那一格界）、**M1599**（控制器不再喂可见帧高 ⇒ decline 永不响）、
   **M1600**（原因写成 `tolerance` ⇒ 与真值表脱钩）、**M1601**（抬了却不计数 ⇒ 计数与写入是两件事）——
   四把都红在 `FoldGeometryMigrationTests` 上，M1599 与 M1600 红在**同一格的不同断言**上，判定按红话里的字样分开。
   **探针不占号**：`PROBE-12`（把 `#available(macOS 13.0, *)` 换成 12.0，模拟「12 上也抬」）实测 **PASSED** ⇒
   本机是 13+，那一档没有证人 ⇒ 空刀作废、不占刀位，归 667 的具名缺席。

② **真实推进（仪器面 · 靶 1 + 靶 2 + 靶 4：三条纪律做成会红的守卫）**
   1. `scripts/frame_geometry_blind.py`（新）：现读「捕获通道引用产品默认几何常量的次数」——
      `%(blind)s`。三种结论各有形状：refs>0 而登记说盲 ⇒ 红（具名不许当永久豁免）；
      refs=0 而默认与登记不一致 ⇒ 红（**产品变了而尺不响**，正是派单点名的那一响）；
      refs=0 且一致 ⇒ ok 并照旧印盲区读数。四把合成正对照内置（`READER_SELFTEST=seen` 四个 1）。
      登记落在 `docs/frame_geometry_blind.json`（含"今天这一维由哪三条独立通道签"）。
      ⇒ 于是旧账里那句「帧逐字节相同 ⇒ 产品没动」的**读法**被更正：它今天只能证"捕获那两棵树未变"，
      对默认几何这一维**不含信息**（旧原文不删，见 ITER 本轮那一节与 BACKLOG 666）。
   2. `scripts/ledger_preflight.py`（新）：⓪ 那一节既没有成对号、也没有具名未到数 ⇒ **exit 1**；
      裸写「未到数」而没带原因字样也红（"还没去取"与"取了没到"是两种账）。
      本轮写手在落盘**之前**调它：`%(preflight)s`。
   3. `scripts/reading_order_scan.py`（新）：名册里每一处"必须出声的读数行"都要在会崩的门**之前**；
      登记的允许门（今天只有 `test_skip_roster` 开头那道防递归 skip）若被挪到读数之后或删掉 ⇒ 红。
      `%(order)s` —— 这一支的由来就是 ⓪·3⑥ 那件事。
   4. `scripts/bundle_content_gate.py`（新）+ CI 新硬步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)`：
      产物**内容**那一维在 runner 上从此有读数，不必把电池挪到 `make bundle` 之后（那会撞 R558 那族并行锁）。
      本机照产品自己的驱动路径跑了一遍真产物：`%(content)s`
      —— `make bundle` 落地、`otool` 读到 3 个良性桩、`AppDelegate` 桩不在，落点仍只在暂存目录。
   5. `test_skip_roster` 的读数行挪到所有门之前（本轮修的那一处），runner 上那一行下一次就有值了。

③ **几朵红各由谁签（"今天有没有人判"与"单子出路"两套编号分开）**
   · 「今天有没有人判」这一套：
     第①态（判过、绿）：`frame_geometry_blind` / `ledger_preflight` / `reading_order_scan` / `bundle_content_gate`
       四支守卫本机全绿且各带正对照；`FoldGeometryMigrationTests` 13 格 0 红 1 具名 skip。
     第②态（判过、红）：本轮**没有**新的本机红（刀落下去的红是判据该有的红，不算这一格的②态）。
     第③甲（被上游红连带、这一步从没跑）：runner 上 `Info.plist gate` 那一跑仍 skipped（硬门、故意不带 `if: always()`），
       与 R591/R592 同形，不算独立缺陷。
     第③乙（跑了但本机没对象）：`FOLD_FULLSCREEN_MEASURE_NOT_RUN=exit-not-settled`（全屏退出没走完）、
       `FOLD_LIFT_DECLINE` 那格在"屏幕够高"的机器上会 `screen-tall-enough` 具名缺席（本机 850 高 ⇒ 有对象）。
     第④态（这一维没人判，具名）：`FRAME_GEOMETRY_BLIND=policy-default`（帧通道对默认几何盲，登记在案）、
       非整数倍缩放/外接屏（667）、macOS 12 那一档的不变量（667）。
   · 「单子出路」这一套：666 的三条（加一档按产品默认建的夹具 / 维持现状并把盲区读数当长期账 / 撤掉盲区登记改由帧判）
     与 667 的三条（第二台机器量 12 与外接屏 / 让全屏退出在单测里走完 / 由用户判 D5 是否接受"放不下就不抬"）
     —— **本轮一条没选**。
   · runner 仍红的那几朵（`STEP[16]` 五朵 + 本轮新增那一朵已修、`STEP[18]` 一朵、`STEP[20]` 两朵）与 R590/R591/R592
     同名同集合 ⇒ 不是本轮引入；`STEP[19]` 那一朵本轮**新增**，成因未定，见本节⓪ 第 3 条最后一段。
   · 段②三问逐问（本轮没碰第②段）：第一问 Light 过 / Dark 未验（具名未撤）；第二问本机真机通道过 /
     runner `env-off` 未验；第三问新通道过 / 主窗树未验（具名）/ 逐帧产物那一半不过（653）。
     ⇒ 三问**没有一条是本轮新过**的，第③段着色器本轮未开工，两条具名阻塞一字未撤。
- **红名对账**（口径=对账口径已启用；门报 `%(recon)s`，不由我数）：
  · 红名「runner 上 `testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio` 红在 743.0≠860.0」→ ⑨·1
  · 红名「`SKIP_ROSTER 键=github-runner` 在整份 runner 日志里出现 0 次」→ ⑨·2
  · 红名「`On-screen probe coverage floor` 由绿翻红（最差帧 198.0ms > 120ms）」→ ⑨·3
  · 红名「刀 M1598 第一次落刀 precheck 报 exit 2（kind 写成 python、证人却是 Swift 那一卷）」→ ⑨·4
  · 红名「刀 M1609 第一次落下是空刀（PASSED）」→ ⑨·5
  · 红名「探针 PROBE-12 锚点命中 0 次（缩进抄错）」→ ⑨·6
  · 红名「`ledger_preflight` 第一版把 heads[-1] 当最新一节 ⇒ 扫到最老那一节永远绿」→ ⑨·7
  · 红名「`ledger_preflight` 第一版只认 `RUN=` 写法 ⇒ 台账那种反引号写法被读成没读」→ ⑨·8
  · 红名「新守卫的合成正对照里，`stale` 那把撞的是"门不存在"而不是"门在之后"」→ ⑨·5
  · 红名「`reading_order_scan` 第一次跑把 `test_skip_roster` 开头那道防递归 skip 报成红」→ ⑨·9
  · 红名「帧基线门 `FRAME_BASELINE_RESULT=red 拦路=17（未登记13 出处不符4）`」→ 不计入对账口径（基名在漂：
    17 张差量全在来源图标那一列、luma>8 的像素 0 颗，而漂移名册本轮是红线不许动 ⇒ 门红着交出去，归 655/665）
  · 红名「归因实验第三步（`--skip` 重捕）本轮没跑」→ ⑨·10

④ **验证链（顺序照派单）**：build `%(build)s` → 判据卷（Swift `FoldGeometryMigrationTests` 13 格、
   python 新增 `test_frame_geometry_blind` 6 + `test_ledger_preflight` 5 + `test_bundle_content_gate` 3 +
   `test_reading_order_scan` 4）→ 刀 M1598–M1610 十三把（**落刀前现读高水位=M1597**）→
   新表 `mutate_r593_paths` 进预检名册（`%(precheck)s`）→ 刀已还原复跑判据（59 python + 13 swift 全绿）→
   `make bundle` 真跑一次（产物只落暂存目录）→ 捕获卷 `%(capture)s` → 帧基线门 `%(gate)s` →
   看图（本节⑤）→ 全量 `%(full)s` → 换装（本节⑥）→ 七本台账 → 派生格落盘之后现读 → 电池（canonical 配置）。

⑤ **看图那一腿**：`%(look)s`
   本轮产品面改的是「窗口高度在屏幕放不下时不抬」，而帧通道对默认几何是**结构性盲**（本节② 第 1 条）⇒
   推进的证人是 `FOLD_LIFT_DECLINE` 那行真窗读数与真机 AX，不是这批帧。
   **但"盲"不等于"没动"**：本轮这批 356 张与上一批比有 **17 张逐字节不同**（全是暗档：8 张 `detail-*-dark` +
   1 张 `detail-loading-composed` + 6 张 `quickpick-*-dark` + 2 张 `detail-file-*-dark`）。逐张定位差量包围盒：
   detail 那一族全部落在 `(43,71)-(64,93)`、quickpick 那一族落在 `(114,252)-(140,342)` ——
   两处都是**来源图标那一列**；差量像素按 luma>8 数是 **0 颗**（即全部差量 ≤8 档灰度），帧尺寸一个没变。
   我把四处差量区裁出来放大并排看了（左=上一批、右=本轮）：那是 **Finder 那颗蓝脸**，
   两批之间只有抗锯齿级的差别 ⇒ 归 **655 / R577 那一族**（系统给的素材今天的渲染），不是本笔的几何改动。
   ⚠ 诚实的一条：**R577 那套三步里我只做了前两步**（包围盒定位 + 是不是同一颗系统素材），
   第三步（`--skip` 新格重捕做归因对照）本轮**没跑** ⇒ 所以"不是本笔改的"在本节里是**带出处的推断**，
   不是做完的控制实验；门因此照旧红（见本节③），我也不去改名册（派单红线）。

⑥ **基线与名单**：本轮动过的文件 `%(paths)s`。帧基线门现读 `%(gate)s`，
   本轮与上一批之间 17 张不同（成因见本节⑤，控制实验没做完那一条也写在那里）；
   `update` 一次没跑（重烤归用户），漂移名册**一字未动**（派单红线：四张按机器登记的表不许改），
   所以这一门是**红着交出去的**，不是"没问题"；
   四张按机器登记的表其余部分一字未改；`SKIP_ROSTER` 里那一行的**理由文字**本轮又补了一次（指明产物内容那一维
   现在由 CI 新硬步骤出声），登记本身没增没减没删。

⑦ **闸门与单子（§3 第③段今天仍不开工）**：
   `STAGE2_CLICKTHROUGH_BLOCKED=awaiting-user-mechanism-choice` 与
   `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 一字未撤；
   `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree`、
   `FRAME_BASELINE_DRIFT_NOT_JUDGED` 一字未撤；规格里「三问全过」出现次数仍是 0。
   仍归用户（一条不代选）：655/656/657/658/659/660/661/662/663/638①/654/646/647/650/651/653/644/639/640/637/633/
   664/665/**666**/**667**/Motion ≥2 帧地板/SSH 成因/手感签字；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、容差 1.5、
   跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、四张按机器登记的表、
   既有名册与豁免表、禁碰 14 面 —— 一字未动；`update` 一次没跑；没改这台机器的全局外观；
   没动用户的 Dock 与登录项；帧与日志不含真实剪贴板原文。
   **禁碰清单本轮的证人**：产品面动的是「主窗默认几何的**高度决策**」与「恢复帧改写」这两面（D5 已授权），
   同一文件里的 `collapsedWidthDefault=424`、`expandedWidthDefault=848`、`contentHeightDefault=600`、
   `seamDividerThickness=1`、`minWidth/minHeight` 逐字未变（`git diff` 只增不改那几行，见 numstat）⇒
   禁碰面数**不抬**；本轮新增的界只读 `visibleHeight`，不写任何 defaults 键。

⑧ **人工验收批次（本轮新增，见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 92）**：
   92.1 把主窗拖到**外接屏/较小分辨率**下放大一次，看退出放大后窗口是否仍在屏内、比例是否还是 √2；
   92.2 进一次全屏再退出，看回来的那扇窗宽高是不是你离开时那一档；
   92.3 批次 91.1 那条（登录项重开一次）如果还没做，本轮仍然挂着 —— 我没动你的 Dock 与登录项。

⑨ **自伤（照实，不缩）**：
   1. **runner 上红了一朵我自己上一轮加的判据**：`testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio`
      把窗口起点写死成 `585 368`（顶边 860），本机可见帧够高就绿，runner 顶只有 ~743 ⇒ 产品按契约把顶边夹回屏内，
      那一格红的是**夹具的前提**。⇒ 规矩：**判"位置不动"的格子，起点必须由那台机器的 visibleFrame 反推**，
      并且"放不下"那一档要单独判"被夹到可见帧顶部"，否则换一台机器就把产品的正确行为判成缺陷。
   2. **`SKIP_ROSTER` 读数行坐在会崩的门后面**（R589 那一族的第二次，这次是观察者自己）：
      内层一红 ⇒ runner 上连一行都不印。本轮把 print 挪到所有门之前，并做成 `reading_order_scan.py` 这一支守卫。
   3. **`On-screen probe coverage floor` 由绿翻红**（最差帧 198.0ms > 锚点 120ms）：本轮**只否掉一条解释**
      （900×640 距 √2 0.57%% ⇒ 不变量不出声；探针也不经过 `applyGeometry`），
      另一条（runner 采样/负载）留给含本笔的那一跑说 ⇒ 120ms 与容差一字未动，也不许顺手登记成 flake。
   4. **M1598 第一次落刀 precheck 就 exit 2**：表里 kind 写成 `python` 而证人是 Swift 那一卷 ⇒
      `unittest` import 不到模块。预检把它拦下来了 ⇒ 记这一条是因为**形状**：kind/证人这两格是配对约束，
      写错不会让表自己响，只有预检会。
   5. **M1609 第一次落下是空刀（PASSED）**：合成样本里那条"允许的门"根本不存在 ⇒ 摘掉"门在之后"那一支
      没人响。补第五把正对照（门存在但坐在读数之后）之后才 CAUGHT。⇒ 空刀第六种形态：
      **正对照撞的不是你要摘的那一支** —— 登记前先自问"这把刀落下去，哪一把合成对照会不响"。
   6. **探针 PROBE-12 锚点命中 0 次**：缩进从判据里抄的（12 空格）而不是从产品文件里现读的（8 空格）⇒ 未落刀。
      同一族（短前缀锚看不见改名/缩进）本轮第三次。
   7. **`ledger_preflight` 第一版取 `heads[-1]` 当"最新一节"**：台账是降序 ⇒ 它切到**最老**那一节，
      而那一节的 ⓪ 早就填好了 ⇒ 这一支永远绿。改成 `heads[0]` 并加一格"不许切到历史节"的判据。
   8. **`ledger_preflight` 的成对号只认 `RUN=` 一种写法**：台账正文里习惯写成反引号的 `42179047067 ↔ 40cccd4` ⇒
      把填好的账读成"没读"。两种形状都认，并在判据卷里各留一格。
   10. **归因实验只做了一半**：17 张帧变了，我按 R577 那三步走了前两步（包围盒 + 是不是同一颗系统素材）就
       在台账里写"不是本笔改的"。第三步（同一棵树 `--skip` 新格重捕）没跑 ⇒ 那句话的强度只到"带出处的推断"。
       ⇒ 记这一条是因为它的形状：**做过的实验决定能写多重的话**；本节⑤ 因此把"没做完"写在同一行里。
   9. **新守卫第一次跑就把合法的前置门报成红**：`test_skip_roster` 开头那道防递归 skip 是**正当**的，
      而扫描器只按"门在读数之前"判 ⇒ 假红。修法不是放宽判据，是**具名豁免 + 陈旧检测**
      （登记的门必须真的在那儿、且不许挪到读数之后，否则红）—— 把"我需要一个例外"变成一张会过期的通行证。
""" % {u"date": DATE, u"n": i[u"n"], u"round": i[u"round"],
       u"ci": d[u"ci"].strip(), u"blind": _first_line(d[u"blind"]),
       u"preflight": _first_line(d[u"preflight"]), u"order": _first_line(d[u"order"]),
       u"content": _first_line(d[u"content"], 2), u"recon": u"（落盘之前那一趟，落盘之后由 --post-land 复算）",
       u"precheck": _first_line(d[u"precheck"]), u"capture": _first_line(d[u"capture"]),
       u"gate": _first_line(d[u"gate"]), u"full": _first_line(d[u"full"]),
       u"look": d[u"look"].strip(), u"paths": d[u"paths"].strip().replace(u"\n", u"、"),
       u"build": u"warnings=0"}


def _first_line(text, idx=0):
    rows = [l.strip() for l in text.splitlines() if l.strip()]
    return rows[idx] if len(rows) > idx else u"（没读到）"


def block_ui(d, u0):
    i = d[u"ident"]
    rows = [
        (u"不变量在放大档不出声（实测）",
         u"`FOLD_ZOOM_PATH 放大档=1201x850 isZoomed=1 离√2=0.0013 出声=0` ⇒ 13+ 那条锁把 zoom 也管住了"),
        (u"不变量在全屏档出声、退出那一档具名缺席",
         u"`FOLD_FULLSCREEN_PATH … 抬到=1039.4 可见帧高=850.0`；退出没走完 ⇒ `exit-not-settled`，不判"),
        (u"「放不下就不抬」落地成产品行为",
         u"`FOLD_LIFT_DECLINE 内容=1470.0x923.0 抬次数=0 不抬次数=1 原因=visible-too-short`"),
        (u"帧通道对默认几何结构性盲（更正旧读法），但本轮帧确实变了 17 张——不是几何",
         u"`FRAME_GEOMETRY_DEFAULTS 捕获侧引用=0 扫的文件=4 帧档数=38 与默认同档的帧=0` ⇒ "
         u"旧那句「帧逐字节相同 ⇒ 产品没动」今天只能证捕获那两棵树未变；"
         u"而本轮与上一批的 17 张差量全部落在来源图标那一列、luma>8 的像素 0 颗 ⇒ 归 655 那一族，不归几何"),
        (u"runner 上一朵判据红是夹具前提",
         u"起点由 visibleFrame 反推 + 放不下那一档单独判「被夹到可见帧顶部」"),
        (u"三条纪律做成守卫",
         u"`frame_geometry_blind` / `ledger_preflight` / `reading_order_scan` + CI 新硬步骤 `Built bundle content gate`"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：√2 不变量补上「放得下」那一半；"
            u"帧通道对默认几何的盲做成会红的守卫"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0


def block_iteration(d):
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：√2 不变量的另一半（放得下），以及"尺不响"做成会响的守卫

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 10/15 | 本轮产品面是"窗口高度在屏幕放不下时不抬"，而帧通道对默认几何**结构性盲**（`FRAME_GEOMETRY_DEFAULTS 捕获侧引用=0`）⇒ 像素那一腿只能记"没有回归"，推进的证人换成真窗读数（`FOLD_LIFT_DECLINE`、`FOLD_ZOOM_PATH`、`FOLD_FULLSCREEN_PATH`）与真机 AX。扣 5 分：这一维的**第二条独立通道**今天只有"我在这台机器上开一扇 1470 宽的窗"这一种形状，外接屏/缩放那一档没有第二台机器可量（667）。 |
| 判据有效性 | 14/15 | 13 把刀全 CAUGHT、逐把单独取退出码、`RESTORE_CLEAN=yes`、预检 `bad=0`；判据 +34 格（Swift 13 卷里新增 3 格 + python 四卷 18 格 + 顺序/豁免那两卷），每格都带合成正对照。扣 1 分：`FOLD_FULLSCREEN_PATH` 那一格退出没走完 ⇒ 它只量到"全屏那一档会出声"，没量到"退出之后是什么"。 |
| 假绿防御 | 15/15 | 四把新守卫全部内置正对照且**逐把验过刀**（M1602–M1610）：`frame_geometry_blind` 四把、`ledger_preflight` 六格、`reading_order_scan` 五把、`bundle_content_gate` 三形状；"产物不在"是 not-run 不是干净、"一个桩都没读到"是尺瞎不是没有、"⓪ 空着"不许落盘、"门在读数之前"要响、**陈旧豁免要响**（第五把是本轮空刀之后补的）。 |
| 产品面推进 | 14/15 | 产品 2 文件：`heightLift` 收 `visibleHeight`、控制器喂进去并记原因/计数；`applyGeometry` 三处调用点逐处点名。用户机上的窗口不受影响（848×600 在 850 高可见帧里放得下）。扣 1 分：D5 那条"放不下时让位于整扇在屏内"是我按宽度先例做的选择，**接受与否还归用户**（667）。 |
| 台账一致性 | 13/15 | 写手本轮自己带两道门：⓪ 前置（`ledger_preflight` 不绿就不落盘）+ 删除行数证人（`git diff --numstat`，除 FINAL 派生格外任何一本出现删除行就停）。红名对账 10 行每行指向 ⑨·N 或 `不计入对账口径`+具名类别。扣 2 分：本轮 ⑨ 记了 9 条，其中 3 条是"刀/守卫自己没牙"（M1598 kind 写错、M1609 空刀、探针锚点缩进）—— 都是预检/预跑抓的，不是我抓的。 |
| 剩余风险处置 | 12/15 | 新开 666（帧通道要不要真看得见默认几何）与 667（12 那一档 + 外接屏 + D5 那条让位），两条各列三条出路、一条不代选；622 那朵 probe 红**只否掉一条解释**就停手，没顺手登记成 flake；`update` 一次没跑；没动 Dock/登录项。扣 3 分：probe 那一朵的 (乙) 解释要等含本笔的那一跑，本轮只能说"未定"；`SKIP_ROSTER` 那一行的理由文字本轮改了两次，说明它承载的机制还在动。 |
| 交接可读性 | 15/15 | R594 的 ⓪ 六格写进 `ci_status_r593.py` 的 `PREDICTIONS_R594`，每条四格齐，并写明反向读法：`SKIP_ROSTER 键=github-runner` 那一行**下一次必须出现**（不出现=那一支又被挪到门后面）；`BUNDLE_CONTENT_GATE_RESULT` 不出现=新硬步骤没落地；`名册未跳=[那一格]` 出现=该删登记。 |

本轮一句话：上一轮我把"高度不在 √2 上"当成只能来自锁前的恢复，本轮量出**全屏那一档也会**——
而按 √2 抬它会抬得比屏幕还高，所以不变量还差另一半：**放不下就不抬**。
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE}


def block_backlog(d):
    i = d[u"ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

**新开单 2 张**：

**666. 帧通道对「产品默认几何」结构性盲：旧那句「帧逐字节相同 ⇒ 产品没动」是它的反证**（R593 现读）
· 现象：R592 把默认从 750/420 抬到 848/424，同一轮台账写着「356 张帧与上一批逐字节相同」——
  那句话被当成"产品没动"的反证用过，而它恰恰是**这一维看不见**的必然结果。
· 现读证人：`FRAME_GEOMETRY_DEFAULTS 展开=848x600 折叠=424x600 捕获侧引用=0 扫的文件=4 帧档数=38 与默认同档的帧=0`；
  捕获走的是夹具钉死的尺寸（`UICaptureHarness.swift:5484` 用 `/420.0`、`:5633` 用 `/750.0`，
  `:278`/`:421` 两处注释说明折叠帧与通栏帧各自的固定带）。
· 今天怎么办：`scripts/frame_geometry_blind.py` + `docs/frame_geometry_blind.json` 把这一维**具名**挂着，
  默认几何一旦再变而捕获侧引用仍是 0 ⇒ 守卫红（刀 M1603 钉的就是这一响）。
· 出路（归用户，一条不代选）：甲 加一档按产品默认建的夹具（**会改捕获尺寸 ⇒ 整批基线重烤**，与 655/620 的处置同族）；
  乙 维持现状，把"这一维由真窗读数 + 真机 AX 签"当长期账（本轮就是这一条）；
  丙 撤掉盲区登记、改由帧判这一维（要先做甲才有意义，否则撤的是措辞不是盲区）。

**667. √2 不变量还有两档没有证人：macOS 12 那一档、外接屏/非整数倍缩放那一档；外加 D5 的一条让位要不要接受**（R593 现读）
· 现象：① `PROBE-12`（把 `#available(macOS 13.0, *)` 换成 12.0，模拟「12 上也抬」）实测 **PASSED** ⇒
  本机 13+ 时那一支不可观察 ⇒ **空刀不占号**，这一档今天没人判；
  ② 全屏退出那一档本机单测进程 2.0s 内走不完 ⇒ `FOLD_FULLSCREEN_MEASURE_NOT_RUN=exit-not-settled`；
  ③ 非整数倍显示缩放/外接屏切换这台机器只有一块屏 ⇒ 没对象。
· 还没决的（归用户）：本轮把「放不下就不抬」落进产品，等于在 D5 里让"整扇窗在屏内"排在"比例≈√2"前面
  （先例是宽度那一侧的 `min(floor, visibleWidth)`）。接受 ⇒ 667 只剩取证手段问题；不接受 ⇒ 要改成"抬并具名"或"根本不抬"。
· 先要量的东西：第二台机器（12.x 或外接屏）上同一组读数；以及全屏退出走完之后那一档的宽高。

**未结案但本轮动过的**：622（probe 最差帧那一朵在 runner 上由绿翻红，本轮否掉「不变量带出来」这一条解释，
另一条留给含本笔的那一跑）；664/665 一字未动。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


def block_decisions(d):
    i = d[u"ident"]
    return u"""## D-593（2026-11-06）：不变量还差另一半 —— 放不下就不抬；以及"尺不响"要做成会响的守卫

① 上一轮我把 √2 写成一条**只跟"锁出现之前的恢复"有关**的不变量。本轮量出第二条通路：
   全屏那一档（`FOLD_FULLSCREEN_PATH … 抬到=1039.4 可见帧高=850.0`）也会把宽高推到非 √2，
   而按 √2 抬它会把窗口抬得比屏幕还高。⇒ **不变量的定义补上界**：目标高度必须放得下可见帧，
   放不下就不抬，并把原因记成可读的两格（计数 + `visible-too-short`），
   否则读数只剩 `抬=0`，下一轮分不清"已在比例上"与"屏幕放不下"（两种修法相反）。
② 先例是宽度那一侧本来就有的 `targetWidth = min(floor, visibleWidth)` ⇒ 高度缺这一格是**不对称**，
   不是新发明。但"让位"这件事动到 D5 的口径 ⇒ **接受与否归用户**（BACKLOG 667），本轮只把选择写清不代选。
③ 放大（zoom）那一档被实测排掉：`1201×850` 距 √2 只有 0.13%% ⇒ 13+ 那条锁连 zoom 都管住了 ⇒
   这一条通路**不构成例外**，而且它写成断言（`XCTAssertNil(liftedWhileZoomed)`）而不是注释 ——
   换台机器前提若变，红在前提上。
④ 纪律只有做成会红的东西才算纪律：本轮把三件"写在 ⑨ 里的事"做成守卫 ——
   ⓪ 没读不许落盘（`ledger_preflight`）、读数行必须在门之前（`reading_order_scan`）、
   帧通道对默认几何盲必须被点名（`frame_geometry_blind`）。每一件都带合成正对照，并且**都验过刀**
   （M1602–M1610）；其中 M1609 第一次是空刀 ⇒ 补了第五把正对照才占号。
""" % {}


def block_changelog(d):
    i = d[u"ident"]
    return u"""### √2 不变量补上「放得下」那一半；帧通道对默认几何的盲做成会红的守卫（R%(r)s / 第 %(n)s 轮 / Round %(round)s）

- 产品：`MainWindowCollapsePolicy.heightLift` 多收 `visibleHeight`，目标高度放不下可见帧就**不抬**；
  控制器把 `visible?.height` 喂进去，并把"为什么不抬"记成 `heightLiftDeclines` + `heightLiftDecline="visible-too-short"`。
  证人：`FOLD_LIFT_DECLINE 内容=1470.0x923.0 抬次数=0 不抬次数=1 原因=visible-too-short 可见帧高=850.0`。
- 产品（通路逐条量）：放大档 `1201×850` 距 √2 0.13%% ⇒ 不变量不出声（写成断言）；
  全屏档会出声，但退出那一档本机走不完 ⇒ `FOLD_FULLSCREEN_MEASURE_NOT_RUN=exit-not-settled`。
- 判据：`FoldGeometryMigrationTests` 13 格（新增 zoom/全屏/decline 三格 + 真值表补 `visibleHeight` 三行 + 900×640 那一行）；
  新守卫四支 `frame_geometry_blind` / `ledger_preflight` / `reading_order_scan` / `bundle_content_gate`，
  判据卷 +18 格；CI 新硬步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)`。
- 修：runner 上红的那朵 `testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio` 是**夹具前提写死在本机屏幕** ⇒
  起点改由 visibleFrame 反推，"放不下"那一档单独判"被夹到可见帧顶部"；
  `SKIP_ROSTER` 读数行从门后挪到门前（内层一红时 runner 上那一行原本连印都印不出来）。
- 更正旧读法：「帧逐字节相同 ⇒ 本轮没动产品」今天只能证"捕获那两棵树未变"——
  捕获侧对 `MainWindowCollapsePolicy` 的引用是 **0**（`FRAME_GEOMETRY_DEFAULTS` 现读）。旧原文不删。
- 单子：新开 **666**（帧通道要不要真看得见默认几何，三条出路归用户）、
  **667**（12 那一档 + 外接屏 + D5 那条让位要不要接受）；622 那朵 probe 红只否掉一条解释、另一条留给含本笔的那一跑。
- 刀：**M1598–M1610 十三把全 CAUGHT**（落刀前现读高水位 M1597）；
  `PROBE-12` 探针 PASSED ⇒ 空刀不占号；`update` 一次没跑；没动用户的 Dock 与登录项。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"]}


def shapes(tag):
    return ((u"UI 轮次标题", u"## 第 %s 轮（R%s ·" % (tag[u"n"], tag[u"r"])),
            (u"ITER 标题", u"## Round %s · R%s（" % (tag[u"round"], tag[u"r"])),
            (u"STATE 主节", u"## R%s 状态（" % tag[u"r"]),
            (u"DECISIONS", u"## D-%s（" % tag[u"r"]),
            (u"BACKLOG 追账节", u"## R%s 追账（" % tag[u"r"]),
            (u"CHANGELOG 标题行", u"（R%s / 第 %s 轮 / Round %s）" % (tag[u"r"], tag[u"n"], tag[u"round"])))


def counts(tag, book_names):
    rows = []
    for book in book_names:
        text = read(book)
        rows.append(u"%s :: %s" % (BOOKS[book], u" | ".join(u"%s=%d" % (n, text.count(s)) for n, s in shapes(tag))))
    return u"\n".join(rows) + u"\n"


def u_high_water():
    text = read(u"UI")
    nums = [int(x) for x in re.findall(u"U-(\\d+)", text)]
    return max(nums) if nums else 0


def deletions_by_book():
    out = subprocess.check_output([u"git", u"diff", u"--numstat", u"--"] +
                                  [BOOKS[b] for b in BOOKS], cwd=ROOT).decode(u"utf-8")
    res = {}
    for line in out.splitlines():
        parts = line.split(u"\t")
        if len(parts) == 3:
            res[parts[2].strip()] = int(parts[1]) if parts[1].isdigit() else -1
    return res


def apply(d, do_write):
    i = d[u"ident"]
    pre = counts(i, (u"UI", u"ITER", u"STATE", u"BACKLOG", u"DEC", u"FINAL", u"CHANGE"))
    totals = [int(x) for x in re.findall(u"=(\\d+)", pre)]
    if max(totals) > 1:
        raise SystemExit(u"本轮标题形状在盘上出现 %d 次 ⇒ 不是幂等重放，停\n%s" % (max(totals), pre))
    if any(totals):
        print(u"DRY：盘上已有本轮标题（幂等重放）⇒ 一本都不再写\n" + pre)
        return 0
    print(u"PRE（写之前逐本现读）：\n" + pre)

    u0 = u_high_water() + 1
    state_text = block_state(d)
    # 靶 4 第 1 条：**⓪ 没读就不许落盘** —— 问守卫自己，不写第二条正则。
    rc, why = ledger_preflight.judge(state_text)
    if rc != 0:
        raise SystemExit(u"⓪ 前置门拦下（rc=%d）：%s ⇒ 七本一本都不写。先跑 ci_status_r593.py 再落账" % (rc, why))
    print(u"LEDGER_PREFLIGHT_GATE=%s ⇒ 允许落盘" % why[:120])
    ui_text, u0 = block_ui(d, u0)
    iter_text = block_iteration(d)
    backlog_text = block_backlog(d)
    dec_text = block_decisions(d)
    change_text = block_changelog(d)
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text), (u"DEC", dec_text), (u"CHANGE", change_text)):
        if u"@@" in blob:
            raise SystemExit(u"令牌没填满：%s 里还有 @@" % name)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from stage_gate_claims import classify_line
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text)):
        for raw in blob.splitlines():
            kind = classify_line(raw)
            if kind in (u"断言", u"冒充段号"):
                raise SystemExit(u"写手自己造出「%s」：%s :: %s" % (kind, name, raw.strip()[:120]))
    if not do_write:
        io.open(os.path.join(TMP, u"state_preview.md"), u"w", encoding=u"utf-8").write(state_text)
        print(u"DRY：六块文本算完，长度 STATE=%d UI=%d ITER=%d BACKLOG=%d DEC=%d CHANGE=%d ⇒ 未落盘"
              % (len(state_text), len(ui_text), len(iter_text), len(backlog_text), len(dec_text), len(change_text)))
        return 0

    new = {}
    new[u"STATE"] = insert_before(read(u"STATE"), r"(?m)^## R\d+ 状态（", state_text + u"\n\n", u"STATE 主节")
    new[u"UI"] = insert_before(read(u"UI"), r"(?m)^## 第 \d+ 轮（R\d+ ·", ui_text, u"UI 轮次节")
    new[u"ITER"] = read(u"ITER") + u"\n" + iter_text
    new[u"BACKLOG"] = insert_before(read(u"BACKLOG"), r"(?m)^## R\d+ 追账（", backlog_text + u"\n", u"BACKLOG 追账节")
    new[u"DEC"] = insert_before(read(u"DEC"), r"(?m)^## D-\d+（", dec_text + u"\n\n", u"DECISIONS")
    ch = read(u"CHANGE")
    # 锚点必须是**行首那一行标题**：`CHANGELOG.md:3406` 的正文里就引用过一次这个串
    # （它讲的是"曾经出现过两行同样的标题"），按子串数会得到 2 ⇒ 写手以为锚点坏了。
    # 尺读错了对象（R555 那一族：短前缀锚看不见上下文）。
    anchor_re = re.compile(u"(?m)^## \\[Unreleased\\]$")
    hits = list(anchor_re.finditer(ch))
    if len(hits) != 1:
        raise SystemExit(u"ANCHOR-MISS CHANGELOG：行首 [Unreleased] 标题命中 %d 次（该恰 1）" % len(hits))
    anchor = hits[0].group(0)
    head, rest = ch[:hits[0].end()], ch[hits[0].end():]
    new[u"CHANGE"] = head + u"\n" + change_text.rstrip(u"\n") + u"\n\n" + rest.lstrip(u"\n")
    fin = read(u"FINAL")
    m2 = re.search(u"产品面连续零改动轮数 = \\*\\*(-?\\d+)\\*\\*（R(\\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit(u"ANCHOR-MISS FINAL：streak 那一格现读不到")
    end = fin.index(u"上一格原文留着：", m2.start())
    cell = (u"产品面连续零改动轮数 = **（落盘之后现读）**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py`；"
            % i[u"r"])
    new[u"FINAL"] = fin[:m2.start()] + cell + fin[end:]
    for book in new:
        write(book, new[book])

    post = counts(i, (u"UI", u"ITER", u"STATE", u"BACKLOG", u"DEC", u"FINAL", u"CHANGE"))
    print(u"POST（写之后逐本现读）：\n" + post)
    bad = []
    for book in (u"UI", u"ITER", u"STATE", u"BACKLOG", u"DEC", u"CHANGE"):
        vals = [int(x) for x in re.findall(u"=(\\d+)",
                                           [l for l in post.splitlines() if l.startswith(BOOKS[book])][0])]
        if vals.count(1) != sum(1 for v in vals if v) or any(v > 1 for v in vals):
            bad.append(u"%s 的标题形状不是各 1：%s" % (BOOKS[book], vals))
    if bad:
        raise SystemExit(u"落盘后形状不是各 1：\n" + u"\n".join(bad))
    print(u"SEVEN_COUNTS_OK=1")
    # 靶 4 第 2 条：**删除行数自己算**（守卫比人快）。FINAL 的派生格允许有删除，其余必须 0。
    dele = deletions_by_book()
    print(u"NUMSTAT_DELETIONS " + u" ".join(u"%s=%d" % (k.split(u"/")[-1], v) for k, v in sorted(dele.items())))
    wrong = {k: v for k, v in dele.items() if v != 0 and not k.endswith(u"AGENT_FINAL_REPORT.md")}
    if wrong:
        raise SystemExit(u"删除行数不该非零（写手吞了历史）：%s ⇒ 立刻 git checkout 那几本，别继续" % wrong)
    print(u"LEDGER_DELETION_WITNESS=ok 除 FINAL 派生格外全部删除=0")
    return 0


def insert_before(text, pattern, block, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(u"ANCHOR-MISS %s：现读模式 %r 没命中" % (label, pattern[:60]))
    return text[:m.start()] + block + text[m.start():]


def main():
    d = gather()
    do_write = u"--apply" in sys.argv
    rc = apply(d, do_write)
    return rc


if __name__ == u"__main__":
    sys.exit(main())
