# R319 开场交接（R318 停在「代码半已 push、账半未落」）

工作树状态：HEAD `3b1a8b9`（R318 代码半）已 push 到 `origin/main`，`git status` 只剩
`.local/` 与 `.scratch/` 里的一次性工具未跟踪。**没有半截在飞的改动**，这份就是停车点。

## ⓪ 开场先读的（成对：run id ↔ commit）

1. `python3 scripts/ci_read.py latest` —— 本轮提交 `3b1a8b9` 那一跑大概率还在 in_progress；
   它之前还有一跑 `e54715c`（R318 的 HANDOFF 之前那笔）。**这两跑的 run id 我这一轮没读到**，
   所以它们在 STATE 里仍是「未读」，不许被读成「没跑」或「绿了」。
2. `/tmp/r318_probe.log`、`/tmp/r318_build.log`、`/tmp/r318_py.log` —— R318 的全部读数都在盘上。
   `/tmp` 会被 macOS 清，**先 `ls` 数到再动笔**；数不到就把那几格写 NOT-RUN，不要抄记忆。
   关键三行（本轮原样读数，账半要解析而不是手抄）：
   - `QUICKPICK_SELARM light 帧选中底=(214,214,214) … key=(0,100,225) nonKey=(220,220,220) 判定=系统nonKey key残差=35(a=0.20) nonKey残差=6(a=1.00) 容差=6`
   - `QUICKPICK_SELARM dark 帧选中底=(106,106,106) … key=(0,89,209) nonKey=(70,70,70) 判定=两臂都不在 key残差=89(a=0.43) nonKey残差=36(a=1.00) 容差=6`
   - `QUICKPICK_SELARM_SUMMARY 候选=2 有对象=2 未判=0 落点=light=系统nonKey dark=两臂都不在`
3. `AGENT_STATE.md` 顶部那一节仍是 R317；R318 只落了代码半，**七本账一本没动**。
   编号现读（别按记忆）：U 最大 1042、D 最大 298、BACKLOG 最大 373、ITERATION 尾节 Round 314、帧 174。

## ① 第一件事：补 R318 的账半（不要先开新题）

一轮 = 七本各一格，这一笔欠着：

- `AGENT_UI_AUDIT.md`：新的 `## 第 317 轮（R318 · 日期）：…`（降序，插在当前最大轮次标题**之上**）
- `AGENT_VISUAL_ITERATION.md`：`## Round 315 · …`（只能追加到文件尾）+ **恰好 7 行**七维表
- 三条 U 定义行（U-1043…U-1045 起步，按实测内容定）：
  ①参照臂进尺、②abs 反向差的自曝与修、③众数→中位数（读不到 vs 有纹理）
- `AGENT_DECISIONS.md`：D-299（凡是「偏差可朝两个方向」的尺，残差必须取 abs；
  读数与读数自相矛盾时先怀疑尺，不放宽容差）
- `AGENT_BACKLOG.md`：**373 的追记写进原条目**（②号出口已进尺、亮档落点=系统nonKey、
  暗档=两臂都不在 ⇒ 373 仍 open），别开同号第二份
- `CHANGELOG.md`：`###` 插在 `## [Unreleased]` 之下（全文件该标题恰好 1 次）
- `AGENT_STATE.md`：新顶节 + 把上一轮的标记轮换下去，自己断言「上一轮标记还在、层数没少」
- `AGENT_FINAL_REPORT.md`：只改计数器（U 区间上界、`D-… ` 那格、变异表数/刀数）

形状抄 `.scratch/motion-audit-2/ledgers_r317.py`（最简版：正文外置 `rNNN_bodies.txt`、
`once()` 断言锚点命中恰好 1、崩溃闸门还原七本、数字全部从 `/tmp` 日志解析、末尾打 `RNNN_LEDGERS_OK`）。
执行前先 `ast.parse`，落盘后跑电池 + `curve_from_ledger.py`（要 `GAPS=none`、`last=` 就是本轮）。

## ② 第二件事：暗档那一格为什么「两臂都不在」

帧 (106,106,106) 比两枚参照色都**亮** 36 级。两条解释，判法相反，先逐一排除再定罪：

1. **取样带的锅**：`inside = (pill.left+4)..< (right-4)` 横跨整颗药丸（744px@2x），
   行内的图标与文字墨都在带里；亮档页底是 255、暗档页底是 30，同样的墨在暗档把中位数往上抬得更明显。
   → 先量「带内散布」并把它打进读数（`armMedian` 已经返回 spread，只是还没 emit），
   再看把取样带挪到药丸左段（避开字）之后读数变不变。
2. **暗档多叠了一层材质**（vibrancy / hover fill）：那就是产品事实，值得单独开单。

**不许**为了让它落在「系统nonKey」而放宽容差 6 —— 容差现在的身份是探针刻度，
下一轮要么把它换成从残差散布推出来的数（D-250 那种等式地板），要么明写它还是探针。

## ③ 刀（本轮欠的变异表）

- 刀 A（尺的身份）：needle 钉在
  `            let key = Self.armResolved(.selectedContentBackgroundColor, appearanceName: appearance)`
  （2026-10-23 现读：该行在本文件命中恰好 1 次），把 `selectedContentBackgroundColor` 换成
  `unemphasizedSelectedContentBackgroundColor` ⇒ 两臂塌成一枚 ⇒ 判定必须是 `两臂不可分` ⇒ 断言必须 RED。
- 刀 B（产品的牙）：needle 在 `Sources/ClipboardHistoryApp/Managers/QuickPickController.swift` 的
  `        fill.isHidden = !QuickPickController.showsHoverTint(isSelected: isSelected,`，
  换成 `(isSelected: !isSelected,` ⇒ 自家灰叠到选中那一行上 ⇒ 残差必须涨出容差 ⇒ RED。
  落刀前先跑 `mutate_needle_precheck.py`，新表登记进 `TABLES`；刀号跨表唯一。

## ④ 已知 NOT-RUN（不许写成已验）

全量 `swift test`、重捕帧 + 帧基线名单、`scripts/install_local.sh` 换装本机、runner 那半
（`3b1a8b9` / `e54715c` 两跑的读数未取）、变异刀（表还没写）。
另：373① 与 347 / 305 仍卡在**用户先退出正在运行的 App**（单实例守卫会中止第二实例）。

## ⑤ 别踩的三个坑（本轮现场撞过的）

1. `render(_ :appearance:to:)` 返回的是 `CaptureMetrics`，不是位图 —— 要帧字节就按 R104 那样
   从落盘 PNG 读回 `NSBitmapImageRep`。
2. 带符号的 `max(0, 负差)` 会把「对不上」报成「完全吻合」。凡写残差/偏差，先问它能不能为负。
3. 一把要求「实心众数」的尺，在有纹理的表面上等于「读不到」，于是整条判据会安静地 skip 掉自己。
   结论行排在闸门与 skip 之前（D-166 那条老规矩），否则没人发现它没判。

## ⓪-b 配对补一行（停车这最后一次现读，`python3 scripts/ci_read.py latest`）

RUN=40003194220 ↔ sha=3b1a8b9 status=in_progress / **结论未读**；本笔停车提交 = 689691e。
下一轮第一件事除了账半，就是把这一跑的正文读掉（走 `scripts/ci_read.py steps/readings 40003194220`，
不要临时 `gh run view | grep`），并确认 `e54715c` 那一跑的结论。

新判据的名字要进 §8 搬运名单：`QUICKPICK_SELARM` / `QUICKPICK_SELARM_SUMMARY`
（`python3 .scratch/motion-audit-2/ledger_rows.py --must-include QUICKPICK_SELARM …` 要读到 缺=0）。
