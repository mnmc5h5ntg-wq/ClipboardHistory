# -*- coding: utf-8 -*-
"""R594 台账写手（七本，整行锚点 + 落盘前 ⓪ 前置门 + 落盘后幂等证人）。

本轮新增的规矩就长在这一支自己身上（靶 4 第四次复发）：
1. **⓪ 没读就不许落盘** —— 落笔前调 `scripts/ledger_preflight.judge`（R593 那一支，本轮把
   "本轮那一节"从**只看位置**改成**按轮次号认**，刀 M1615 钉的就是这一响）；
2. **删除行数自己算** —— 写完立刻 `git diff --numstat`，除 FINAL 派生格外任何一本出现删除行 ⇒ 停；
3. **落盘之后跑 `scripts/ledger_idempotency_gate.py`**（新）：写手重放两趟，第二趟必须一字不改，
   不许再用"我数过没重复"当证人 —— 幂等这一维第四次靠手工，第四次都漏（⑨·1）。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r594.py --check    # 只算文本，不落盘
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r594.py --apply    # 落七本 + 派生格
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TMP = "/tmp/r594"
DATE = u"2026-11-07"

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


def _env():
    """跑子进程时的环境：剥掉 SDKROOT（python3 注入的那一颗会害了 swift），并禁掉胶片通道。"""
    e = {k: v for k, v in os.environ.items() if k != u"SDKROOT"}
    e[u"PYTHONUTF8"] = u"1"
    e[u"PYTHONDONTWRITEBYTECODE"] = u"1"
    e.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)
    return e


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


def pick(path, prefix, label, idx=0):
    """从一份日志里按**行首前缀**取那一行读数；取不到就停手，不许凭记忆填。"""
    if not os.path.exists(path):
        raise SystemExit(u"读数缺失：%s（%s）" % (label, path))
    text = io.open(path, encoding=u"utf-8", errors=u"replace").read()
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数里找不到前缀 %r（%s，%s）" % (prefix, label, path))
    return rows[idx] if len(rows) > idx else rows[-1]


def identity_from_disk():
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
    d[u"ident"] = identity_from_disk()
    d[u"ci"] = must_read(os.path.join(TMP, "ci_status.txt"), u"⓪ 现读")
    d[u"drift"] = must_read(os.path.join(TMP, "drift_identity.txt"), u"靶 1 身份读数")
    d[u"knife"] = must_read(os.path.join(TMP, "knife_status.txt"), u"刀末态")
    d[u"precheck"] = must_read(os.path.join(TMP, "precheck.txt"), u"针预检")
    d[u"capture"] = must_read(os.path.join(TMP, "capture_summary.txt"), u"捕获那一卷")
    d[u"gate"] = must_read(os.path.join(TMP, "gate_local.txt"), u"帧基线那一门")
    d[u"look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿")
    d[u"guards"] = must_read(os.path.join(TMP, "guards.txt"), u"三支新守卫的读数")
    d[u"old"] = must_read(os.path.join(TMP, "old_values.txt"), u"改之前那三档旧值")
    d[u"new"] = must_read(os.path.join(TMP, "new_values.txt"), u"改之后那三档新值")
    d[u"install"] = must_read(os.path.join(TMP, "install.txt"), u"换装那一趟")
    d[u"paths"] = must_read(os.path.join(TMP, "paths.txt"), u"产品/守卫文件清单")
    d[u"full"] = (must_read(os.path.join(TMP, "full_summary.txt"), u"全量卷")
                  if os.path.exists(os.path.join(TMP, "full_summary.txt"))
                  else u"（未读到：那一趟还没跑 ⇒ 台账不许替它填数）")
    return d


def block_state(d):
    i = d[u"ident"]
    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · **产品 4 文件**（列宽改成跟当前窗口宽 = 用户实测那一朵 + 「放得下就不记记忆宽」+ 全屏契约）+ 判据 Swift +6 格 / python 四卷 31 格 + 刀 M1611–M1622 十四把全 CAUGHT + ⓪ R593 两跑到数、五条预测三中一不中一未读到）

⓪ **现读两对（`ci_status_r594.py`，取值时刻见 `ci_readings.json` 的 mtime；两跑都已 `completed / failure`）**：
   1. 配对与逐步骤（正文里逐字贴，**不做截断**）：
```
%(ci)s
```
   2. **R593 那五条预测由脚本判（不目测）**：
      · ②新硬步骤 `BUNDLE_CONTENT_GATE_RESULT=ok APP_DELEGATE_STUB=absent 良性桩=3` ⇒ **中**；
      · ③`SKIP_ROSTER 键=github-runner … 内层判=…` 那一行在 runner 上出现了 ⇒ **中**（R593 把 print 挪到门之前，
        这一格就是那一改的第一证人）；但同一行里 `名单外=['test_the_gate_reads_the_bundle_the_makefile_produces']`
        ⇒ **本机绿而 runner 名单外多一颗**，本轮不判它（归 634/658 那一族，见本节③）；
      · ④`STEP[16] 红名集合不超出那 7 条` ⇒ **不中**，但这一条要按 R588/R590 那一课写两格：
        判法给的"命中行"是日志里一条 ANSI 注释行（`#     切点落在**行中间**…`）⇒ **不中可能是尺错而不是主张错**；
        现读那一跑 STEP[17] 的红名确实有 **7** 条、其中两条是 R593/R594 自己新加的
        （`testTheInvariantDeclinesWhenTheLiftWouldNotFitTheScreen`、`testTheZoomedWindowIsMeasuredNotAssumed`），
        两条都在**本机已经改掉**的那两格里（本轮给它们加了 `premiseNotInFullScreen` 与具名缺席）⇒
        所以 ④ 按判法记不中、按内容记"未定"，由含本笔的那一跑裁决；
      · ⑤`PROBE_COVERAGE_SUMMARY … 红=8` ⇒ **中**（口径没变）；
      · ⑥电池汇总 `Ran` 比 932 多 ⇒ **未读到**（`CI_CHANNEL_ABSENT`）：取处那一格写的是"以 `Ran ` 开头的汇总行"，
        而 runner 把电池跑在 `if: always()` 的**下一步**，`Ran ` 那颗 token 在上面几步里被 grep 的是**脚本回显行**
        ⇒ 与 R593 同一格同一个病，修法留给 668 那条守卫之外，见本节②第 3 条。

① **真实推进（产品面 · 用户实测：两栏仍然不等宽、拖窗口只有右侧在变）= 对 R592/R593 那两轮的公开更正**
   1. **根因不是旧构建，是实现方式**：列宽被 `MainWindowCollapsePolicy.columnWidth`（旧同名常量）
      写成 `(expandedWidthDefault − seam)/2 = 423.5`，`ContentView` 两棵树把它当 min/ideal/max 钉死 ⇒
      左栏永远不跟窗口走。R592/R593 落的是一次性几何迁移 + √2 不变量，**两轮的验收都只在 848 那一档量**，
      而 848 恰好是常量成立的那一档 ⇒ 假绿。
   2. **改之前的旧值**（同一判据、同一台机器、三档现读；`COLUMN_EQUALIZE`）：`%(old)s`
      —— 差 152pt / 352pt 那两档在旧验收里根本没有对象。
      **落刀复现**：M1620 把那一行钉回常量（= R592/R593 交付里实际在跑的形状）⇒ 判据红在同一组数上
      （`152.0 > 1.0`、`423.5 ≠ 499.5`）⇒ 旧值不是我回忆出来的，是**这一把刀现在还能打出来的**。
   3. **改之后的新值**：`%(new)s`
   4. 实现（产品 4 文件）：
      · `MainWindowCollapsePolicy.columnWidth(contentWidth:collapsed:)` —— 列宽由**当前分栏宽**推，
        展开档 `(总宽 − 中缝)/2`、折叠档铺满；旧常量改名 `legacyConstantColumnWidth` 并**只留给刀落**（产品不再引用它当列宽）；
      · `WindowConfigurator.Coordinator.equalizeColumns(in:)` —— 唯一把中缝放到"当前宽一半"的入口，
        挂在 `windowDidResize` / `windowDidEndLiveResize` / `windowDidBecomeKey` / `windowDidBecomeMain` /
        `scheduleSidebarCleanup` 的延迟补拍（SwiftUI 放列宽是异步的，与 R510 那颗开关同一形状）；
        返回 Bool，"没找到分栏器"不许被读成"钉好了"；
      · `ContentView` 两棵树把钉死值换成伸缩范围（min 200 / max .infinity），`ideal` 只剩**首帧那一档**、
        由 `columnWidth(contentWidth:)` 从窗口宽推 —— 列宽本身不再是这里的任何一个值（刀 M1620 证明钉回去会红）；
      · `MainWindowCollapsePolicy.shouldRememberWidth` + 控制器的 `memoryWritesSkipped`/`lastMemorySkip`
        （靶 3 顺手落的第二条产品界：屏幕放不下那一档**不把超宽记进记忆**，否则下次启动永久非 √2）。
   5. 判据：`FoldGeometryReanchorTests` +3 格（① 三档展开宽度 + 折叠档现找分栏器、两条出路各判各的；
      ② 纯函数分档真值表；③ **首帧那一档**——只走 `WindowManager.showMainWindow()`、不做任何 `setContentSize`，
      现读 `侧栏=374.5 详情槽=374.5 差=0.0 期望=374.5`），
      `FoldGeometryMigrationTests` 里"记忆界"那一格带两行正对照。
   6. **这一改带出来的一个行为变化，本轮没有再钉回去（写清，不藏）**：从前 min=ideal=max=常量 ⇒ 中缝
      **物理上拖不动**；现在 SwiftUI 那一侧只给伸缩范围（min 200 / max .infinity），等分由 `setPosition` 落，
      于是**两次 resize 之间**用户可以把分隔条拖到一个不对称的位置并停在那里（下一次拖窗口宽会被拉回中缝）。
      本轮没有把 `minimumThickness/maximumThickness` 重新钉死 —— 那等于与 SwiftUI 的列宽约束抢布局，
      而"抢赢"这件事在剩下的验证预算里没有证人。⇒ 具名进批次 93.3（请用户实测拖中缝那一条），
      要不要"中缝永远拖不动"回到旧契约归用户（669 的第四条出路）。
      ② 纯函数分档真值表；③ **首帧那一档**——只走 `WindowManager.showMainWindow()`、不做任何 `setContentSize`，
      现读 `侧栏=374.5 详情槽=374.5 差=0.0 期望=374.5`），
      `FoldGeometryMigrationTests` 里"记忆界"那一格带两行正对照。
   刀 **M1620 / M1621 / M1622** = 用户点名的三向（钉回常量 / 只改一侧 / 折叠态用展开档列宽），
   三把各红在**不同的断言**上：M1620 同时红在三档差值**和**首帧那一格（`423.5 ≠ 374.5`、差 98.0pt）、
   M1621 红在两档差值、M1622 红在纯函数那一格 ——
   只落一把就等于"另一条坏法还能绿着交付"。

② **真实推进（仪器面 · 靶 2 + 靶 4：三件"写在 ⑨ 里的事"做成会红的守卫）**
   1. `scripts/prediction_block_guard.py`（新，668 那条出路）：现读最新的 `ci_status_r*.py`，取
      `PREDICTIONS_R<nnn>` 里最大那一块，逐条查四格齐（主张/判法/取处/通道）并**真调用判法**三种输入
      （合成正文 / 空 / 完全无关）：崩 ⇒ 红（R593 那两条 NameError 的形状）、空输入为真 ⇒ 红（absence 被满足）、
      无关输入为真 ⇒ 红（没牙）。本轮它第一跑就抓到自己两处：①一条判法坐死 True、⑤`max()` 在空列表上崩。
      读数：`%(guards)s`。**668 因此从"散文"变成"门"，但结案仍要含本笔的那一跑签**（尺是被本笔改的）。
   2. `scripts/instrument_quote_guard.py`（新）：台账里"从仪器输出抄一行"那些句子必须对得上被抄那一行的**表名/臂号**
      （R593 ④ 抄成 `mutate_r245` 那一朵）；扫描面=名册，`%(guards)s` 第二行是现读计数。
   3. `scripts/ledger_idempotency_gate.py`（新）：写手重放两趟 ⇒ 第二趟七本 md5 必须一字不改；
      顺序是"先落盘、再取快照、再重放"（第一版把快照取在第一次之前 ⇒ 幂等写手被判红，尺读错对象）。
      本机现读：见本节⑦那一趟（电池之后）。
   4. `scripts/ledger_preflight.py`（R593 那一支，本轮改两格）：认"本轮那一节"从**只看位置**改成
      **按轮次号认**，并把取到的那一节逐字打印（`依据/位置/内容/一致/切到/依凭`）；判据卷扩到
      `格子=11 不符=0`，刀 M1615 钉"退回只看位置"。
      ⚠ M1615 **第一次落下是 PASSED（空刀）**：`locate` 选了哪一节没有读数 ⇒ 加 `切到=` 那一格 + 两格对照才响。
   5. CI 接线：三支守卫的自检卷都放在 `scripts/tests/`，被判据卷那一步的
      `python3 -m unittest discover -s scripts/tests` **自动收到**（不是显式接线，这一点写清楚）⇒
      runner 上 STEP[9] 应当印出 `PREDICTION_BLOCK_RESULT=` / `INSTRUMENT_QUOTE_RESULT=` 两行，
      这正是 R589 那一课的正面形状（**只在测试里被调用的守卫在 CI 上没有读数行** ⇒ 读数行要由那一卷自己印）。

③ **靶 1：655 的成因与本轮那朵红互相矛盾 ⇒ 先量，不选边**
   恒等式与出处逐张读数在 `drift_identity.txt`：`%(drift)s`
   现读的三件事：① 本轮变帧总数与"已登记 + 未登记"对得上（不是 17 这一个数）；
   ② 名册那 16 行的 `observed` 哈希**在同倍率的会话里 11–14/14 命中** ⇒ 第①甲（名册读错对象）**被否**；
   ③ 那 17 张里 12 张逐字节不同而像素相同、17 张按 luma>8 数都是 0 颗 ⇒ 第①乙（差量真的又在漂）**成立**。
   ⇒ 于是 655 那句"跨会话一次性差"需要一条 **forward 更正**（旧原文不删，见 BACKLOG 655 追账），
     并新开 **669**（判据只量一个宽度这一族在几何面复发）与 **670**（折叠档那一列今天只有纯函数证人）。
   红线照单：**门这一轮仍红着交出去**（`%(gate)s`），`register-drift --restamp`、改 `observed`、`update`
   一条都没做，也没把这朵红改成具名不判；它仍由 655 跟踪。

④ **靶 3：那 2.0s 在等什么 —— 量完之后撤掉两把为不可达状态写的产品守卫**
   1. 等的是 `styleMask` 里那颗 `.fullScreen` 位（现读：置位 0.04s / 清位 ≈6.07s），**不是**
      `windowDidExitFullScreen` 通知（通知在单测进程里投递 **0** 次）⇒ 前一版拿通知当出口是等一个不会来的东西。
   2. 拆成三种修法相反的具名出路：(甲) 事件从不发生（投递 0 次）／(乙) 事件晚于 2.0s（mask ≈6.07s 清）／
      (丙) 那个状态对产品窗根本不可达。**本轮量到的是 (丙)**：`WindowConfigurator` 写死
      `collectionBehavior = [.managed, .fullScreenNone]` ⇒ `toggleFullScreen` 之后 mask 永不含 `.fullScreen`。
      所以"多等会就绿"不是结论：契约上这一档不该等，等的预算和退出全屏的收尾都是**没有对象的窗口**。
   3. 由此本轮做了两件"往回收"的事：① 删掉整卷全屏退出仪器（它量的是不可达状态）；
      ② **撤掉我本轮早些时候为全屏加的两条产品守卫**（`applyGeometry` 里那两条对不可达状态兜底），
      改成一条**契约格**（`testTheMainWindowRefusesFullScreenBecauseTheConfiguratorPinsFullScreenNone`，
      断言 mask 在 2.0s 与 8.0s 都不含 `.fullScreen`、帧不变）+ 刀 **M1619**（把 `.fullScreenNone` 换成
      `.fullScreenPrimary` 必须红）。⇒ 记进 ⑨：**为不可达状态写产品兜底 = 给自己造空刀**。
   4. 落下来的真实产品改动是 `shouldRememberWidth`（同一处代码的**可达**分支）+ 放大→折叠那一格
      `FOLD_ZOOM_MEMORY`，界与 `heightLift` 用同一条式子（真值表 7 行含两行正对照），刀 M1617/M1618 一正一反。

⑤ **验证链（顺序照派单）+ 换装**：build `warnings=0` → 判据卷（Swift `FoldGeometryReanchorTests` 7 格 +
   `FoldGeometryMigrationTests` 全绿；python 新增 `test_prediction_block_guard` 10 +
   `test_instrument_quote_guard` 9 + `test_ledger_idempotency_gate` 6 + `test_ledger_preflight` 扩到 11）→
   刀 M1611–M1622 十四把（**落刀前现读高水位=M1610**）→ 新表 `mutate_r594_knives` 已进预检名册
   （`%(precheck)s`；第一次跑 `bad=2` = 本轮产品改动撞断 M1369/M1478 两支老锚点，重锚后各复跑 CAUGHT、
   预检串行重跑到 `bad=0`；期间与捕获并行那一次撞 SwiftPM 锁报 `NOT_RUN_TIMEOUT`，读数作废不算证人）→ 重捕帧（`%(capture)s`）→ 帧基线门（`%(gate)s`，红着交出去）→ 看图（本节⑥）→
   全量卷 `%(full)s` → **换装**（用户手上那份不是这一轮的实现 ⇒ 本轮必须换）→ 七本台账 → 派生格现读 → 电池。
   **换装那一趟现读**：`%(install)s`

⑥ **看图那一腿**：`%(look)s`

⑦ **基线与名单**：本轮动过的文件 `%(paths)s`。帧基线门现读 `%(gate)s`；列宽在 848 那一档**数值未变**
   （423.5/423.5），但产品树里 `equalizeColumns` 会多做一次布局判断 ⇒ 帧是否逐字节不变**由门说，不由我说**；
   `update` 一次没跑，漂移名册一字未动（派单红线：四张按机器登记的表不许改），名册/豁免表一字未动；
   `SKIP_ROSTER` 本轮**没有**新增条目（靶 3 那格改成契约格而不是 skip）。

⑧ **闸门、单子与人工验收（§3 第③段今天仍不开工，本轮推的是第①段交付缺陷返修）**：
   `STAGE2_CLICKTHROUGH_BLOCKED=awaiting-user-mechanism-choice`、
   `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction`、
   `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree`、
   `FRAME_BASELINE_DRIFT_NOT_JUDGED` 四条一字未撤；规格里「三问全过」出现次数仍是 0；
   第③段（着色器）本轮未开工。
   仍归用户（一条不代选）：655/656/657/658/659/660/661/662/663/638①/654/646/647/650/651/653/644/639/640/
   637/633/664/665/666/667/**668**/**669**/**670**/**671**/Motion ≥2 帧地板/SSH 成因/手感签字；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、
   容差 1.5、跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、
   四张按机器登记的表、既有名册与豁免表 —— 一字未动；`update` 一次没跑；没改这台机器的全局外观；
   没动用户的 Dock 与登录项；帧与日志不含真实剪贴板原文。
   **人工验收批次 93**：93.1 把主窗**拖宽/拖窄各几次**，看左右两栏是不是**一起**变（用户实测那一句：
   从前只有右侧预览在变）；93.2 折叠一次再展开，展开那一下的左栏是不是仍然等于当前窗口宽的一半；
   93.3 **拖一下中缝**（分隔条）：现在它在两次改窗口宽之间是可以拖走的、松手会停在你放的位置 ——
   请判这一条要不要回到旧契约「中缝永远拖不动」（本轮没把它钉回去，理由见主节①·6）；
   93.4 批次 92.1/92.2 那两条如果还没做，本轮仍然挂着。

⑨ **自伤（照实，不缩）**：
   1. **幂等第四次**：本轮台账写手前三次靠手工"我看过没重复"。这一维从今天起由
      `ledger_idempotency_gate.py` 判（重放两趟 + md5 对拍），不再由我数 ⇒ 但**这一格今天只有本机证人**，
      runner 那一维要等含本笔的那一跑。
   2. **两条产品守卫写给一个不可达的状态**：靶 3 的量还没做完就往 `applyGeometry` 里塞了"在全屏里怎么办"，
      而产品窗 `.fullScreenNone` ⇒ 那两行永远不会被走到，刀落下去只能是空刀。撤掉、改成契约格 + M1619。
      ⇒ 规矩：**先证状态可达，再写兜底**。
   3. **M1615 第一次落下是 PASSED（空刀，又一形态：变异改了选择结果而选择结果没有读数）**：
      `locate` 换了选节方式但**没有印出选了哪一节** ⇒ 判据无法分辨。加 `切到=` 读数 + 两格对照才 CAUGHT。
   4. **判据读了错对象（帧尺度之外的第二次）**：`splitView.arrangedSubviews[1].frame.width` 实测是**整个分栏宽**
      而不是详情列宽 ⇒ 848 那一档被报成"左右差 424.5"。改成"侧栏帧宽 + 分隔条位置"两个独立口径推详情槽。
   5. **折叠档读了一个已下树的视图**：折叠后产品换的是 `collapsedLayout`（没有分栏器），
      而判据复用上一个 `split` 引用 ⇒ 读到 848.0 的旧帧，报成"这一档没折起来"。改成现找 + 两条出路各判各的。
   6. **`setContentSize` 之后没排版就读** ⇒ 读到的是没重排的帧（同一格第 4、5 条之外第三次"尺读错对象"）。
   7. **heredoc 里写中文说明 + ASCII 双引号又炸了一次**（本轮第一次），补丁没落盘；
      接着第一个补丁又把锚点里的 `u"取处"` 一起吞了 ⇒ 文件坏在半路，`git checkout HEAD --` 才收回来
      （未提交的改动，台账没被波及）。⇒ 规矩照旧：**补丁写成文件、不用 heredoc**。
   8. **`gh run view --json jobs -q` 那串 jq 被步骤名里的引号打断** ⇒ 改成 python 里格式化（R565 那一族：
        把结构交给不会碎的通道）。
   9. **预检与捕获并行撞了 SwiftPM 锁** ⇒ `mutate_needle_precheck` 报 `NOT_RUN_TIMEOUT`。
      这不是腐烂（R558 那一课）：读数作废、串行重跑，本轮台账里的预检数是**重跑之后**那一份。
   10. **runner 上红着两格我自己本轮/上轮加的判据**（`testTheInvariantDeclinesWhenTheLiftWouldNotFitTheScreen`、
       `testTheZoomedWindowIsMeasuredNotAssumed`）：两格的前提都写死在**本机形状**上（可见帧高度、上一格退出全屏没走完
       留下的污染），本轮改成本机也走"具名缺席"（`screen-tall-enough` / `premiseNotInFullScreen`）⇒
       **裁决只能由含本笔的那一跑说**，本轮不许自称修好。
   11. **`SKIP_ROSTER` 那一行在 runner 上报 `名单外=['test_the_gate_reads_the_bundle_the_makefile_produces']`**：
       R593 新增的那一格没有登记 ⇒ 634 那一族的旧账，本轮只在 ⓪ 里读数、没动登记（登记归用户，一条不代选）。
   12. **一条预测的"取处"写得不完整**：预测④ 的判法在 runner 日志里给出的命中行是一条 ANSI 注释行
       （`#     切点落在**行中间**…`）⇒ "不中"这个结论里混着**尺错**的成分。本轮不回头改判法（R588 那一课：
       判法一字不改、两个读数一起写），只把"取处必须写明 `--log` 还是 `--log-failed`"写进 ⑨ 与 R595 的 ⓪。
   13. **本轮的产品改动撞断两支老刀的锚点**：**改之前**预检那两行现读
       `mutate_r510_sidebar_toggle M1368 ok；M1369 命中=0` 与
       `mutate_r567 M1476 ok；M1477 ok；M1478 命中=0；M1479 ok`
       （前者钉的是 `windowDidResize` 整段原文，我往那段里加了等分；后者的起点正是被撤掉的钉死值）；
       **重锚之后**同一张表的两行都读 `ok`（`bad=0` 那一趟见本节⑤）。
       ⇒ 按 R580 那条规矩**改新代码不动老表的语义**：M1369 重锚到"等分之后仍要补延迟清理"那两行、
       M1478 起点换成现在这一行而终点（可拖区间 250~340）一字未改；两把各复跑一次 **CAUGHT / RESTORE_CLEAN=yes**。
       记这一条是因为形状：**改了产品就必须当场重跑预检**，否则下一轮的预检才是第一次响。
   14. **一次"把尺读错对象"发生在自己身上并被自己的探针否证**：我先按胶片写下"首帧没等分 ⇒ 要加一拍"，
       PROBE-594-A（把 `becomeKey`/`becomeMain` 两拍一起摘掉再跑那一格）**仍然绿** ⇒ 首帧由 resize 那条路兜住，
       真正的成因是夹具那棵树不挂 `WindowConfigurator`（671）。⇒ 规矩：**落产品之前先跑一次"摘掉它会红吗"**；
       两拍留着（覆盖"开窗时宽没变过"那一档）但具名 `COLUMN_EQUALIZE_NO_WITNESS=no-resize-launch`，不占刀号。

- **红名对账**（口径=对账口径已启用；归属由 `red_name_reconciliation.py` 判，不由我数）：
  · 红名「帧基线门 `FRAME_BASELINE_RESULT=red 拦路=17（未登记13 出处不符4）`」→ 不计入对账口径（基名在漂：
    本轮身份读数给出"名册 observed 在同倍率会话里 11–14/14 命中、17 张里 12 张字节不同而像素相同"⇒
    归 655 跟踪，门红着交出去，`register-drift`/改 `observed`/`update` 一条没做）
  · 红名「runner STEP[17] 那两格本轮/上轮新加的判据（`testTheInvariantDeclines…`、`testTheZoomedWindowIsMeasured…`）」→ ⑨·10
  · 红名「runner STEP[9] `SKIP_ROSTER … 名单外=[test_the_gate_reads_the_bundle_the_makefile_produces]`」→ ⑨·11
  · 红名「预测④按判法不中、命中行是一条 ANSI 注释」→ ⑨·12
  · 红名「预测⑥电池 `Ran` 那一格连续两轮 `CI_CHANNEL_ABSENT`」→ 不计入对账口径（通道未跑：取处那一格的 `Ran ` token
    在 runner 上被上面几步的脚本回显行抢走，本轮没有把它改成具名不判，留作 668 之外的下一格）
  · 红名「预检 `NEEDLE_PRECHECK … bad=2`（M1369/M1478 命中=0）」→ ⑨·13
  · 红名「刀 M1615 第一次落下是 PASSED（空刀）」→ ⑨·3
  · 红名「预检 `NOT_RUN_TIMEOUT`（撞锁那一次）」→ ⑨·9
  · 红名「`ledger_preflight` 判据第一版把 `切到=` 落空 ⇒ M1615 落不下去」→ ⑨·3
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
       u"ci": d[u"ci"].strip(), u"drift": _first_line(d[u"drift"]),
       u"old": _first_line(d[u"old"]), u"new": _first_line(d[u"new"]),
       u"guards": _first_line(d[u"guards"]), u"precheck": _first_line(d[u"precheck"]),
       u"capture": _first_line(d[u"capture"]), u"gate": _first_line(d[u"gate"]),
       u"full": _first_line(d[u"full"]), u"install": d[u"install"].strip().replace(u"\n", u"；"),
       u"look": d[u"look"].strip(), u"paths": d[u"paths"].strip().replace(u"\n", u"、")}


def _first_line(text, idx=0):
    rows = [l.strip() for l in text.splitlines() if l.strip()]
    return rows[idx] if len(rows) > idx else u"（没读到）"


def block_ui(d, u0):
    i = d[u"ident"]
    rows = [
        (u"列宽不再等于常量：三档各判一次",
         u"旧 `宽=1000 差=152.0 / 宽=1200 差=352.0` ⇒ 新 `三档差全 0.0`；刀 M1620 钉回常量仍能打出同一组旧数"),
        (u"拖窗口只有右侧在变这一朵，实现方式换成观察当前分栏宽",
         u"`equalizeColumns` 挂在 resize/endLiveResize/becomeKey/becomeMain/延迟补拍五条路上，返回 Bool"),
        (u"折叠档那一列铺满当前宽（两个分支分开判）",
         u"`COLUMN_EQUALIZE 纯函数分档 宽=600 折叠档=600.0 展开档=299.5 旧常量=423.5`；产品折叠态没有分栏器 ⇒ 现找"),
        (u"「屏幕放不下就不把超宽记进记忆」落地",
         u"`shouldRememberWidth` + `memoryWritesSkipped`/`lastMemorySkip`，界与 `heightLift` 同一条式子；刀 M1617/M1618 一正一反"),
        (u"全屏那一档对产品窗不可达（契约，不是散文）",
         u"`collectionBehavior=[.managed, .fullScreenNone]` + 契约格；等的是 mask（0.04s 置 / ≈6.07s 清）不是通知（0 次）"),
        (u"三支守卫：预测块 / 抄行 / 台账幂等",
         u"`prediction_block_guard`（668 那条出路）+ `instrument_quote_guard` + `ledger_idempotency_gate`，各带正对照与刀"),
        (u"帧基线那朵红的身份：甲被否、乙成立",
         u"名册 `observed` 在同倍率会话里 11–14/14 命中；本轮 17 张里 12 张字节不同而像素相同 ⇒ 655 那句「一次性差」要 forward 更正"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：列宽改成跟当前窗口宽（公开更正 R592/R593）；"
            u"预测块/抄行/幂等做成会红的守卫"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0


def block_iteration(d):
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：判据只量一个宽度造成的假绿 —— 列宽改绑当前窗口宽，并把三件纪律做成门

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 11/15 | 用户实测那一朵（两栏不等宽、只有右侧在变）本轮由**真窗口的两条独立口径**量出来：旧 1000 档差 152.0pt、1200 档差 352.0pt，新值三档全 0.0；折叠档现读"没有分栏器 + 内容宽=600"。扣 4 分：像素那一腿本轮**只能记回归**（848 那一档列宽数值未变），而"拖窗口"这个动作在帧通道里没有对象（666 那一族），要看效果只能由用户手上的新构建（批次 93.1）。 |
| 判据有效性 | 14/15 | 14 把刀全 CAUGHT、逐把单独取退出码、`RESTORE_CLEAN=yes`、预检串行重跑到 `bad=0`（第一次 `bad=2` 是本轮产品改动撞断两支老锚点，重锚后各复跑 CAUGHT）；新判据 Swift +6 格 + python 四卷 31 格，每格带合成正对照；`prediction_block_guard` 第一跑就抓出我自己两条判法没牙/会崩。扣 1 分：折叠档那两格今天只有纯函数证人（产品那一档没有分栏器），像素侧没人判（新开 670）；`becomeKey`/`becomeMain` 那两拍被 PROBE-594-A 证否，只能具名不能签（671）。 |
| 假绿防御 | 15/15 | 本轮正面处理了三种假绿：①**只量一个宽度**（旧值在 1000/1200 才现形，判据扩到三档 + 折叠档）；②**尺读错对象**（`arrangedSubviews[1].frame.width` 是分栏总宽 ⇒ 换两个独立口径；折叠档复用旧引用读到已下树的视图 ⇒ 现找；`setContentSize` 后不排版就读 ⇒ 补 layout）；③**为不可达状态写兜底**（`.fullScreenNone` ⇒ 撤两条产品守卫、改契约格 + M1619）。刀 M1620/M1621/M1622 是用户点名"必须各红一次"的三向，各红在不同断言上。 |
| 产品面推进 | 15/15 | 产品 4 文件，且这一改直接落在用户报的那一句上：`columnWidth(contentWidth:collapsed:)` 由观察到的分栏宽推、`equalizeColumns` 五条路挂上、`ContentView` 两棵树的钉死值撤成伸缩范围、`shouldRememberWidth` 把"放不下就不记"变成产品行为。换装已做（`install.txt` 现读构建时刻与 SHA），用户可立即拖窗口复核。 |
| 台账一致性 | 13/15 | 写手带三道门：⓪ 前置（本轮把"本轮那一节"改成按轮次号认 + `切到=` 读数）、删除行数证人、**幂等重放证人**（新，第四次复发的处置）；红名每行单行、类别由门给。扣 2 分：③ 那条预测的"不中"里含**尺错**成分（判法给的命中行是一条 ANSI 注释），本轮只能记"按判法不中、按内容未定"，裁决要等下一跑；⑨ 记了 9 条自伤，其中 4 条是仪器自己没牙/读错对象。 |
| 剩余风险处置 | 12/15 | 新开 669（判据只量一个宽度这一族在几何面复发 ⇒ 要不要把多档宽度接进 CI/帧基线）、670（折叠档那列的像素证人）、671（**捕获夹具那棵树不挂 `WindowConfigurator`** ⇒ 帧里的中缝由 SwiftUI 初始档给，产品整套等分在帧通道里没有对象）；655 的成因做了 forward 更正（旧原文不删）；668 从散文变成门但**等 runner 签**；帧基线那朵红**仍红着交出去**（同一个 17，一行没新增、没登记），一条出路都没代选。扣 3 分：`⑥电池 Ran` 那一格连续两轮未读到，本轮仍未修到 runner 有值；④ 的裁决、634 那颗 runner 名单外多出来的用例都还挂着。 |
| 交接可读性 | 14/15 | R595 的 ⓪ 六条预测写进 `ci_status_r594.py` 的 `PREDICTIONS_R595`，每条四格齐（含"这条通道由哪一步以什么方式印出去"），并由守卫真调用过；反向读法写明：`COLUMN_EQUALIZE` 那一行在 runner 上不出现=那一格被 skip、`差` 非 0.0=等分在那台机器上不成立、`FOLD_MAINWINDOW_FULLSCREEN`/`FOLD_ZOOM_MEMORY` 缺一条=契约格或记忆界那格没跑。扣 1 分：②那一格要求两个 token 都在，但 `--log` 与 `--log-failed` 的取法仍未在预测里写成命令（下轮补）。 |

本轮一句话：R592/R593 两轮的验收都在 848 那一档量，而 848 恰好是"列宽 = 常量"成立的那一档 ⇒
**两轮都绿着把用户看得见的不等宽交付了**；这一轮把列宽绑到观察到的分栏宽，并把"判据只量一个宽度"记成一族缺陷而不是一个 bug。
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE}


def block_backlog(d):
    i = d[u"ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

**新开单 3 张**：

**669. 「判据只量一个宽度」这一族在默认几何面复发：R592/R593 两轮的验收都只在 848 那一档做**（R594 现读）
· 现象：用户实测"拖窗口时只有右侧预览在变"，而 R592 的迁移格、R593 的验收格、以及
  `FoldGeometryReanchorTests.testTheTwoColumnsEachTakeHalfTheContentWidth`（现读第 338 行只量 848）
  **三处都只在 848 那一档判** —— 而 848 恰好等于 `2×423.5+1` ⇒ 常量的那一档与等分的那一档重合，
  错的实现被量成对的。
· 本轮已做：`testColumnsFollowTheCurrentWindowWidthNotTheSpecConstant` 把同一判据在 848/1000/1200 各判一次
  + 折叠档现找分栏器各判一次；旧值现读 152.0/352.0，新值三档全 0.0；刀 M1620 还能把旧数打回来。
· 还欠的（归用户，一条不代选）：甲 把"多档宽度"接进 CI（现在只在 swift 判据卷里，runner 跑得到但**没有单独门**）；
  乙 帧基线补一档非规格宽（**会新增基线帧 ⇒ 与 655/620 的处置同族，需要重烤**）；
  丙 维持现状，把这一族当"判据必须逐档点名"的长期规矩（靠 ⑨·4/5/6 那三条教训维持）。
· 为什么单独立单：记忆里"判据只量了一个宽度"已经写过一次（R555 按倍率拆口径那一族），
  本轮是同族第二次落到**产品可见**的缺陷上 ⇒ 只修 bug 不立单，下一轮还会在别的维度只量一档。

**670. 折叠档那一列今天只有纯函数证人：产品折叠态不渲染分栏器 ⇒ 像素侧没人判"折叠用了展开档列宽"**（R594 现读）
· 现象：折叠走的是 `collapsedLayout`（一棵树，没有 `NSSplitViewController`），
  所以 `equalizeColumns` 在那一档 `guard` 就返回、判据的两条出路里"有分栏器"那一支**在本机不可达**
  （现读 `折叠态 有分栏器=0 内容宽=600.0`）。
· 今天怎么办：分支由 `testCollapsedColumnWidthIsNotTheExpandedHalf` 钉（7 行真值表 + 旧常量对照），
  刀 M1622 证明"不看 collapsed"会红；窗口宽那一侧由折叠档的 `contentWidth=600` 判据兜住。
· 出路（归用户）：甲 加一档"折叠且仍带分栏器"的夹具（不真实，只是给刀落位）；
  乙 承认这一档只能判纯函数，把像素证人撤出这一格（当前做法，写明在此）；
  丙 折叠也保留分栏器（**这是产品形状的改变**，与 D-552 折叠一步切换相反）。

**671. 捕获夹具那棵树不挂 `WindowConfigurator` ⇒ 帧里的中缝由 SwiftUI 初始档给，产品整套等分在帧通道里没有对象**（R594 现读）
· 现象：`WindowConfigurator(collapse:)` 只出现在 `App.swift:83` 的根上；`UICaptureHarness` 的 Fixture 直接渲染
  `ContentView` ⇒ 建窗后那五条等分挂载路（resize / endLiveResize / becomeKey / becomeMain / 延迟补拍）在夹具里一条都不走。
· 现读证人：`main-sidebar-title-hover-750x560-light.png` 侧栏右沿 **423.5pt**（750 那一档的等分是 374.5）；
  本轮改完之后整批 **356/356 逐字节相同**；而唯一有中缝像素证人的那一格
  `FOLD_SEAM_PIXEL 帧=1696x1200 缝列=424.5pt 期望=424.0pt` 只有 848 那一档 ⇒ 它在旧实现下本来就绿。
· 与 666 的分别：666 说的是"默认几何那一维看不见"，这一条说的是**整个窗口布局**看不见（列宽、中缝、等分都不参与），
  而且它给出一个具体可查的形状：夹具树与产品树的 `.background(...)` 装配不同。
· 出路（归用户，一条不代选）：甲 夹具挂上 `WindowConfigurator`（**会改一批非 848 档的帧 ⇒ 需要重烤基线**，
  与 655/620 的处置同族）；乙 加一档 750/1000 的整窗夹具并单独登记（同样要重烤，但只加不改）；
  丙 维持现状，把"窗口布局这一维由真窗口判据 + 用户实测签"当长期账（本轮就是这一条，写在这里不许读成"已判"）。

**未结案但本轮动过的**：655 —— **forward 更正写在这一节，那条单子原文不动**（台账与 STATE 按编号/SHA 引用历史，
回头改它的正文就是把昨天的话改成今天的话）：原句「跨会话一次性差」在本轮的身份读数下不成立，
应读作「系统素材的渲染会在会话之间**反复**漂；名册里 `observed` 那一份哈希只对**同倍率同会话**成立」
（本轮 17 张里 12 张字节不同而像素相同、17 张按 luma>8 数都是 0 颗；名册 16 行的 observed 在同倍率会话里 11–14/14 命中）；
668（仪器做掉 ⇒ 待含本笔那一跑签，本轮不结案）；666/667 一字未动；634 那颗
`test_the_gate_reads_the_bundle_the_makefile_produces` 在 runner 上仍属"名单外"，本轮没碰它的登记。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


def block_decisions(d):
    i = d[u"ident"]
    return u"""## D-%(r)s（%(date)s）：列宽必须由**观察到的窗口宽**推；纪律只有做成门才算纪律

① 一个几何量如果只在**它成立的那一档**上量过，它就不是判据。R592/R593 两轮的"两栏等宽"验收都落在 848，
   而 848 = 2×423.5+1 正是常量实现成立的那一档 ⇒ 两轮全绿、用户看得见的不等宽。**修法不是补一个宽度**，
   是把列宽的实现换成"由当前分栏宽推"（`columnWidth(contentWidth:collapsed:)` + `equalizeColumns` 五条挂载路），
   并让**旧实现在今天仍能被打出来**（M1620 钉回常量 ⇒ 红在同一组旧数上）—— 否则"新判据看得见旧缺陷"这句话只是我说。
② 帧/像素通道对自己没覆盖的维度**不含信息**（记忆 R592 那条今天第二次用到）：848 那一档列宽数值没变，
   所以"帧没变"既不能证明修好也不能证明没修好；这一轮的证人是真窗口两条独立口径（侧栏帧宽 + 分隔条位置），
   以及用户手上那份新构建（批次 93.1）。
③ **先证状态可达，再写兜底**：靶 3 那 2.0s 等到最后量出来的是"这一档对产品窗不可达"
   （`collectionBehavior` 里 `.fullScreenNone`）⇒ 撤掉本轮早些时候为全屏写的两条产品守卫（它们永远走不到，
   刀只能落空），改成契约格 + M1619。同一处代码里**可达**的那一支（屏幕放不下就不记记忆宽）才是本轮落的产品行为。
④ 三件"写在 ⑨ 里的事"做成门（668 那条出路）：预测块必须真调用判法（空/无关输入不许为真）、
   抄仪器行必须对得上表名与臂号、台账写手必须重放两趟一字不改。
   ⚠ 本轮的教训是**守卫自己也没牙**：`prediction_block_guard` 第一跑抓出的两处坏形状，一处是我写的判法坐死 True，
   一处是 `max()` 在空列表上崩 —— 守卫的正对照必须先于被守卫的东西成立，否则"有门"这句话还是散文。
""" % {u"r": i[u"r"], u"date": DATE}


def block_changelog(d):
    i = d[u"ident"]
    return u"""### 列宽改成跟当前窗口宽（公开更正 R592/R593）；预测块 / 抄行 / 幂等做成会红的守卫（R%(r)s / 第 %(n)s 轮 / Round %(round)s）

- 产品（用户实测那一朵的根因）：`MainWindowCollapsePolicy.columnWidth(contentWidth:collapsed:)` 由**当前分栏宽**推
  （展开 `(总宽−中缝)/2`、折叠铺满）；旧常量改名 `legacyConstantColumnWidth` 并只留给刀落。
  `WindowConfigurator.Coordinator.equalizeColumns(in:)` 挂在 resize / endLiveResize / becomeKey / becomeMain /
  延迟补拍五条路上；`ContentView` 两棵树把钉死的 min/ideal/max 换成伸缩范围（min 200 / max .infinity）。
  证人（旧→新）：`宽=1000 侧栏 423.5 详情槽 575.5 差=152.0` 与 `宽=1200 差=352.0` ⇒ 三档 `差=0.0`（423.5/499.5/599.5）。
- 产品：`shouldRememberWidth`（屏幕放不下就不把超宽记进记忆）+ 控制器 `memoryWritesSkipped`/`lastMemorySkip`；
  `FOLD_ZOOM_MEMORY` 现读 `changed==fits`，界与 `heightLift` 用同一条式子。
- 撤掉：为**不可达**的全屏状态写的两条产品守卫（`WindowConfigurator` 写死 `.fullScreenNone`）；
  整卷全屏退出仪器删掉，换成契约格 `testTheMainWindowRefusesFullScreenBecauseTheConfiguratorPinsFullScreenNone`。
- 判据：`FoldGeometryReanchorTests` +3 格（三档宽度 + 折叠档现找分栏器两条出路；纯函数分档真值表；首帧那一档）；
  新守卫三支 `prediction_block_guard`（668 那条出路）/ `instrument_quote_guard` / `ledger_idempotency_gate`，
  判据卷 +25 格；`ledger_preflight` 的"本轮那一节"从位置改成**按轮次号认**（`切到=` 读数 + 判据扩到 11 格）。
- 更正（公开）：R592/R593 那两轮"第①段交付缺陷已修"的结论**只在 848 一档验证过**，而 848 恰好是常量成立的那档 ⇒
  用户实测的不等宽由本轮修掉并换装；655 那句"跨会话一次性差"按本轮身份读数 forward 更正（旧原文不删）。
- 单子：新开 **669**（判据只量一个宽度这一族）、**670**（折叠档那列只有纯函数证人）；668 仪器做掉、待 runner 签；
  帧基线那朵红**仍由 655 跟踪、门红着交出去**，`register-drift`/改 `observed`/`update` 一条没做。
- 刀：**M1611–M1622 十四把全 CAUGHT**（落刀前现读高水位 M1610；M1615 第一次是空刀，补 `切到=` 之后才响）；
  换装一次（构建时刻与 SHA 见 `install.txt` 现读）；没动用户的 Dock 与登录项。
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
    rc, why = ledger_preflight.judge(state_text)
    if rc != 0:
        raise SystemExit(u"⓪ 前置门拦下（rc=%d）：%s ⇒ 七本一本都不写。先跑 ci_status_r594.py 再落账" % (rc, why))
    print(u"LEDGER_PREFLIGHT_GATE=%s ⇒ 允许落盘" % why[:160])
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
                raise SystemExit(u"写手自己造出「%s」：%s :: %s" % (kind, name, raw.strip()[:140]))
    # 抄行守卫：本轮正文里凡"从仪器输出抄一行"必须对得上被抄那一行（R593 ④ 那一朵）。
    # 它读的是**文件路径**（尺自己那格 `--state`），所以先把 STATE 那一块写到临时预览里再问它，
    # 不许把守卫改成吃字符串 —— 那是为了让门好过而改尺（R544 那一课）。
    preview = os.path.join(TMP, u"state_preview.md")
    io.open(preview, u"w", encoding=u"utf-8").write(state_text)
    qrc = subprocess.call([sys.executable, os.path.join(ROOT, "scripts", "instrument_quote_guard.py"),
                           u"--state", preview], env=_env())
    if qrc != 0:
        raise SystemExit(u"抄行守卫拦下（rc=%d）⇒ 本轮有一句抄错了对象，七本一本都不写" % qrc)
    print(u"INSTRUMENT_QUOTE_GATE=0 ⇒ 允许落盘")
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
    anchor_re = re.compile(u"(?m)^## \\[Unreleased\\]$")
    hits = list(anchor_re.finditer(ch))
    if len(hits) != 1:
        raise SystemExit(u"ANCHOR-MISS CHANGELOG：行首 [Unreleased] 标题命中 %d 次（该恰 1）" % len(hits))
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
    return apply(d, do_write)


if __name__ == u"__main__":
    sys.exit(main())
