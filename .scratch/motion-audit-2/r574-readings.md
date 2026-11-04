# R574 读数（第 573 轮 / Round 571 · 2026-11-04 · 靶 = 折叠规格 §3 第②段 / BACKLOG 653）

## ⓪ 两跑现读（不轮询）

| 对 | 现读 | 处置 |
| --- | --- | --- |
| `41815985543 ↔ cf63079`（R573 判据笔） | `status=in_progress / conclusion 空` | **未读**。三格由它签：R573 新判据走哪条 /（乙）修好没有 / STEP[9] 是否绿 |
| `41816421295 ↔ 36e96b7`（R573 补记笔） | `status=in_progress / conclusion 空` | **未读**。不许替上一行签（R565 那一族） |

⇒ 本轮没有 ⓪ 读数可用，也不拿本机的数顶。两对号继续带进 R575 的 ⓪，加上本笔自己那一跑（三格，见 ⑦）。

## ① 647 的归属冲突（文档内部也有）与两条机制的后果表

现读的三条（R568 留在判据里、本轮重抄）：
`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位`

| | 甲 `contentShape`（SwiftUI 命中形状） | 乙 `ignoresMouseEvents`（窗口级） |
| --- | --- | --- |
| `空区命中` 那三项会怎么变 | `容器3 → 0`，且**必须**新增一组压在行上的探针，`内容 0 → N` 才算"只让空区让位" | **三项全 0**（整窗不吃鼠标）⇒ 旧那格的期望从"命中落到谁"翻成"谁都不命中" = 口径换代 |
| 必须有的证人 | ① 空区三探针 0；② 行上正对照仍命中产品那行；③ 帧一字不变（`均值差=0.0000 品红漏出=0`）；④ 底衬"永远不吃命中"逐字未变（刀 M1481 的形状）；⑤ 撤掉 `contentShape` ⇒ `容器` 回到 3 必须红 | ① 一条**从产品入口进**的"点行仍选中"判据（否则功能被换掉没人发现）；② 窗口属性只在该透的那扇窗为 true 的逐字证人；③ 帧一字不变；④ 无条件置 true 必须红 |
| 代价 / 边界 | 只管容器那一层，**窗口级穿透仍欠** ⇒ D4 那句只做一半 | 范围过宽：D4 要的是"透明区"透，乙做"整窗"透；浮层靠鼠标点行 ⇒ 破坏性 |
| 被否掉的第三条 | **「alpha=0 会自动穿透」** —— 就是上面现读那句（空区整幅 a=0 仍返回容器）⇒ 不是出路，是本单的成因 | 同 |

⇒ 本轮只把它做成第②段一行具名阻塞 `STAGE2_CLICKTHROUGH_BLOCKED=awaiting-user-mechanism-choice`，机制二选一归用户。

## ② 推进本体：夹具那条通道在 651 机制表里的位置（本机 2x，通道串 `FRAME_CHANNEL_MECHANISM`）

| 树 | 夹具 | 族 | 类 | 根类名 | 子层冷 | contents冷 | 子树 hosting | 通道未画比例 | 产物采样 | 产物不透明 | 产物全透明 | 有alpha平面 | 前置判 | 产物判 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 主窗 | content-with-history | swiftui | B | `NSHostingView<ModifiedContent<AnyView,__EnvironmentKeyWritingModifier<ColorScheme>>>` | 1 | 0 | 3 | 0.3586 | 105000 | 105000 | 0 | 1 | 夹具快门那步_contentView.cacheDisplay | 产物铺平alpha |
| 浮层 | quickpick-list | appkit | C | `NSView` | 6 | 0 | 0 | 0.8521 | 31500 | 31500 | 0 | 1 | 夹具快门那步_contentView.cacheDisplay | 产物铺平alpha |

三条结论（各钉一条，都有刀）：
1. 两棵都落在三态里的**第二态**：按快门之前 `contents=0`（没被画过），是夹具自己那一步 `contentView.cacheDisplay(in:to:)` 把它画出来的 ⇒ 第③段逐帧判据只要继续经过 `render` 就自带前置。⚠ runner 那一档由**含本笔的那一跑**签；本机不替它签。
2. **产物判不了 alpha 归零**：通道侧未画 `0.3586` / `0.8521`，而同一张帧的产物侧全 `a=255`（`flattenedPNG` 写盘前铺窗口底色）⇒ 判据钉的是"通道里有、产物里没有"这条**关系**（646 的口径清单因此从两件变三件）。
3. 类的判定只能读结构、不能读修饰过的 ObjC 名（`NSStringFromClass` 前缀把根是 `NSHostingView<…>` 的主窗读成 0 个 hosting、类判成 C）⇒ 换 `String(describing:)`，并配 M1508。

## ③ 刀（M1505–M1508 全 CAUGHT、RESTORE_CLEAN=yes）

| 刀 | 打在哪 | 读数怎么变 | 红在哪一格 |
| --- | --- | --- | --- |
| M1505 | `render` 里 `performAsCurrentDrawingAppearance { contentView.cacheDisplay(in:to:) }` 摘掉 | 两棵 `通道未画比例=1.0000` ⇒ `前置判=画不出` | `XCTAssertNotEqual(pre, .cannotDraw)` |
| M1506 | `flattenedPNG` 里 `out.setFillColor(windowBackgroundColor…) + out.fill(rect)` 两行摘掉 | 产物 `全透明 0 → 26696`、`中间 → 1465`，而通道侧 `0.8521` **一字不动**（只动一边） | `XCTAssertTrue(blocksZeroAlphaVerdict(artifact))` |
| M1507 | `scripts/ledger_round_headings.py` 的 `HEADING_PREFIX = '## '` 换成 `'###### '` | 现读解析到 `标题=0` ⇒ `ROUND_HEADINGS_EMPTY=1` | 现读格 + 正对照格 + 空名单格三处红 |
| M1508 | `isHostingView` 退回 `NSStringFromClass(type(of:)).hasPrefix("NSHostingView")` | 主窗 `宿主层内NSHostingView数=0 类=C`（假象，根其实就是 hosting） | `XCTAssertEqual(cls, "B")` |

撤掉的两把探测刀（不登记、不占号）：改 `产物采样` 的 stride；改 `倍率` 那一格 —— 两者都改变读数但**没有任何断言读它们**，因此不会红 ⇒ 空刀。下一轮从 **M1509** 起。

## ④ 上一轮写坏台账的修复证人（现读）

- `AGENT_UI_AUDIT.md` **15834** 行（HEAD 那一版 15812 + R573 一节 22 行）；U 定义行 **2216** 条，去重后仍 **2216** ⇒ **重复 U 号 = 0**；`U_ID_BOUNDARY 现读最大=U-2512 位数=4 最新一节定义行=10`。
- 轮次标题行逐字重复：UI_AUDIT `411` 条 **0** 重复 / STATE `308` 条 **0** 重复 / ITERATION `569` 条 **0** 重复（新尺现读：`ROUND_HEADINGS 本=7 标题=1825 逐字重复=0 RESULT=ok`）。
- 编号区间与一致性：`test_ui_audit_ids_are_unique`、`test_ui_round_interval_parity`（不符名单回到在册 `[103]`）、`test_round_batch_consistency`、`test_ledger_round_headings`（5 格）全绿。
- 七本行数：UI_AUDIT 15834 / ITERATION 21433 / BACKLOG 11261 / DECISIONS 9017 / FINAL_REPORT 1536 / STATE 8778 / CHANGELOG 6272（**本轮落盘后另行现读**）。
- 新尺的判法形状坑：第一次试写按"轮次号相同"判 ⇒ 把 `第 498 轮续一/续二/续三`、`Round 29d` 读成 4 处重复 ⇒ 改成"整行逐字相同"。

## ⑤ push 那一格（环境事实）

- `git config --get remote.origin.url` = `git@github.com:…`（**没改，也不改**）
- `git push origin main` ⇒ `git@github.com: Permission denied (publickey)`；`ssh-add -l` = `The agent has no identities.`；`ssh -v` 确实 `Offering public key: ~/.ssh/id_ed25519 SHA256:U5ZVyu4…` 而服务器不收；`ssh-keygen -y -P "" -f` 证明该 key **无口令**。
- `gh auth status` = 已登录、`Git operations protocol: https`；`git config credential.helper` = `osxkeychain` ⇒ 用**用户自带**的 HTTPS 凭据推。
- 第一趟 HTTPS ⇒ `! [remote rejected] main -> main (Internal Server Error)`；隔 20s 原样重试 ⇒ `79f7116..cf63079  main -> main`（GitHub 侧瞬时 500，不是本地坏）。
- **没做**：改 remote url / 动 `~/.ssh` / 给 key 加口令或删除或新建 / 换 DNS、hosts、直连 IP / `gh auth refresh` 加 scope。`gh api user/keys` 需要 `admin:public_key`（404）⇒ key 为何不被接受 = `SSH_KEY_REJECTED_REASON_UNKNOWN`，**归用户**。
- 本轮具名：**`PUSH_TRANSPORT=https-token`**。

## ⑥ 隐私与通道卫生

帧与日志只含判据自带的固定测试文本（`产品树取证判据的固定测试文本 N。` / `makePopulatedStore()` 那批），**没有一个字来自用户剪贴板**；读数里只有 sha7 与仓库相对路径；一次性帧写在 `FileManager.temporaryDirectory` 下的随机目录，看完即删、不入仓。

## ⑦ 验证链现读（顺序没换，逐条抄自己那一行）

- 门：`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- 判据卷（`--filter UICaptureTests`，不带帧变量）：`Executed 228 tests, with 5 tests skipped and 0 failures in 635.213 (635.232) seconds`（228 = R573 的 227 + 本轮新格）。
- 重捕那一遍（带 `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r574/frames`）：`Executed 228 tests, with 4 tests skipped and 0 failures in 748.314 (748.334) seconds` ⇒ skipped 在同一棵树上 5/4 之间漂（`testCaptureKeyViews` 那一格），**只记现读、不动门、不猜成因**。
- 帧：`FRAME_BASELINE_AGAINST=working / COMPARED=356 / CHANGED=0 / MISSING=0 / ADDED=0` ⇒ **不跑 `frame_baseline.py update`**（帧真没变；新判据只往临时目录写两张一次性帧，不进基线名单）。
- 全量卷：`Executed 1435 tests, with 60 tests skipped and 0 failures in 646.796 (646.880) seconds`（1435 = 1434 + 新格；skipped 60 与上一轮同值，只记现读）。
- 三支预检（**串行**，R558 的撞锁教训）：`NEEDLE_PRECHECK tables=382 covered=303 arms=790 bad=0`、`ARM_TOTAL files=475 arms=1277 dupes=0 repeats=0`、`HIDDEN_ARMS 表=469 可判=1216 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok`、`CI_CHANNEL_HYGIENE ci脚本=14 电池脚本=74 电池引用=24 合计=100 绝对根=0 真人路径=0 通道空格=0 ⇒ RESULT=ok`。
- 换装：产品 0 文件 ⇒ `SKIP_INSTALL=no-product-change`；`security find-identity -v -p codesigning` 现读 `1 valid identities found`（与 633 的人工回执是两格）。
- 派生格（台账落盘之后现读）：`PRODUCT_STREAK ledger_round=573 streak=6 sections=549 as_of=last=8f679f9 last_round=567 newest=8f679f9 newest_round=567 date=2026-11-04 标签补自台账=9(...)`；`product_streak.py --check` 对 STATE 与 FINAL_REPORT 两格同形签字；`SOURCES_CELL 账上=R568/8f679f9 git=R568/8f679f9 一致=是`；`LEDGER_ABSENCE_RESULT=ok 不成立=0/63`（格=162 声明=63）；`REFRESH_SECTION1 OK 改=无 n=564 尾轮=571`。
- 电池（台账与派生格之后）：`Ran 725 tests in 95.756s — OK (skipped=5)`（725 = 720 + 新名册 5 格）。⚠ 这一行的数**不回填进 STATE ⑧ / U-2521 / FINAL_REPORT 那三格**（那里写的是"数只进收口报告"），因为回填一次就要多签一次（R573 ⑨③）。
- 台账形状自查（本轮的修复证人义务）：七本 `git diff` 逐本验过**纯插入**（UI_AUDIT +13、ITERATION +24、BACKLOG +47、DECISIONS +40、CHANGELOG +10、STATE +33/-1（那一行是"最后更新"抬轮次，锚到锚）、FINAL_REPORT +7/-6（六行是计数器与 streak 格，逐行核过））；`LEDGER_TOKENS books=7 chars=5768717 stray=0`。
