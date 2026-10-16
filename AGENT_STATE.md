# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 01:41（本地 · R101 / 第 103 轮收尾：**「统计」这一屏补上了卡片，这扇设置窗口现在没有一屏躲在自己那三条判据外面**（BACKLOG 131 结案）：六屏同一套分组语言（分区标题裸在页面上 + 内容在 `GroupBox` 里），那条压在页面底上的通宽 `Divider()` 消失 —— R92 从「数据」、R99 从「推荐」删掉的那个形状最后一次退场；**只动容器**，动画键 / 回执通道 / 禁用逻辑 / 文案一行没改。形状是被自己的尺驳回之后才定的：第一版把标题也包进卡片 ⇒ `CARD_ABOVE` 当场报「卡片顶之上读到 0 段墨」；131 里原本写的「两张卡片」被否（说明是从属不是并列），代价（一张卡片只有 1 条分隔线 ⇒ 节奏判据 declined）写进结案段。读数：`CARD_INSET_CAPABILITY 候选=26 有材质=26（被告=24 参照=2）量到=24 未判=0`（未判 4→0）、`卡片顶=109.0 卡片底=417.0 内缩=5.5pt` = 与系统 `GroupBox` 同档；空臂 `内缩=6.5` 不放宽等式，改成一条**有界的**替代判据 `[+0.5, +2.0]` + 读数 `CARD_INSET_ICON_FIRST`（D-165，牙 M566）。**读 R100 的 CI（run 38927822527，failure）一次拿到两件事**：① 147 结案 —— 48 行 `CARD_FILL_CANDIDATES` 全是 `前三=(236:480)`，整带只有一个色档 ⇒ 不是「差 ≤3 被门限吃掉」，是**没有第二个档**；② 更值钱的是同一份日志里 `有材质=2` 那两格是**参照**（裸 `GroupBox` 在同一台 runner 上量出 6.0pt）⇒ **成因在容器，不在 `GroupBox`** ⇒ 新开 **150**（把参照夹具装进 `Form` 再跑一次 CI，三种结果各是一条结论）。**而 R100 我装的那道能力闸门是坏的**（U-280 / D-164）：`materialCells` 把参照与被告数成同一个量 ⇒「参照有、被告无」既不满足 `==0` 的 skip、也不满足 `measured >= min(16, materialCells)` 的地板 ⇒ 三朵红说的都不是产品；现在拆成 `defendantMaterial` / `controlMaterial`（没对象响成 skip、没对照响成红，绝对锚点排在两条闸门之前），牙 M564 / M565。**改的过程中被量出来两格，都不在原计划里**：`.settingsCardInset()` 挂到 `GroupBox` **外面** ⇒ `边距=7.0/7.0`（其余 12.5~14.5）而**没有任何断言会红**（这一屏只 1 条分隔线，`dividers >= 2` 让它走 declined ⇒ 可以静默上线，U-281，补下界 `>= 10.0`，牙 M563）；我给自己那条留白判据写的上界 16.0 被真产物当场驳回（`recommendations-tall 下=17.5`、`general-login-unsupported 上=33.0`）⇒ 上界删掉、三个合法值进注释（U-282，「先问两侧是不是同一种东西」第四次撞上）。**台账与工具本轮自己坏了五处**：M560 被我的重写弄成 `needle 命中 0` ⇒ `MUTATE_TABLE n=3 caught=2 not_run=1` / `MUT_EXIT=1`，**是电池响出来的**，处置是写明退役理由 + 接班者（M564）而不是删 arm 混过去（U-286）；`verify_*.sh` 的 `: > "$OUT"` 裸截断改成「覆盖前按 mtime 另存」并在沙箱真跑一遍（U-283）；§8 先写的「已量」是**已被取代的中间态**（`卡片顶=116.0` → 落盘 `109.0`），而 §4 那组「改前→改后」成对数字里改前一侧的帧被电池自己的 `rm -rf` 删了 ⇒ 尺落盘重做成 `.scratch/motion-audit-2/r101_luma.py`（U-287；**结论一侧没变**：卡片 vs 页面底 Δ8/Δ7、空格 vs 卡片底 Δ13/Δ11、离卡片最近色档 Δ27/Δ13 ⇒ 卡片仍是这一屏最弱的边界，顺带量到图例四档与网格四档**逐色相同**），修它时一次 Edit 的 `old_string` 又跨掉 `AGENT_UI_AUDIT` 一整条 U-283（同条 ③，靠 grep 数编号抓到并原样复原）；grep `207pt` 命中 0 就把**有出处**的数判成印象（U-288：出处是 149 的 `size=207x294`，不带单位）⇒ 证否必须换式子再搜一遍；`testFrameIntervalsUnderStateChanges` R99 skip / R100 pass / R101 skip，自陈 `FRAME_CHANNEL baseline_n=0 screen=有` ⇒「屏幕在」≠「有刷新」，149 的前提每轮先自证（U-285）。验证：**`VERIFY_OK=1`（pass-2）**，本节每个数都出自 `r101_verify.log`：构建 0 告警、`TEST_EXIT=0`（**815** 例 / 41 skip / 0 failures）、在屏 `PROBE_EXIT=0`（11 例 / **3** skip，多的那条是 U-285 那条自己关了通道）、`帧数=130` 且 `COMPARED=130 CHANGED=0 MISSING=0 ADDED=0`、脚本 `Ran 213 tests OK`、**十张变异表 `MUT_EXIT=0 跑了=10 期望=10`、合计 46 刀全部拿到各自期望（`mismatch=0 not_run=0`）**、`LEDGER_EXIT=0`、曲线 `ROUNDS=102 first=1 last=101`（`PHASE2 n=94 mean=92.81`，本轮 **92.0**）、`SUMMARY_MISSING=0`；pass-1 那份 `VERIFY_OK=0` 的原因就是 M560，**两遍都报**。本机**已换装**：`INSTALL_RESULT=ok`、sha `026aa3aa…` → `812c246f…`、`staged == installed`、`SMOKE_OK=1` 且无第二实例中止、旧 pid 5779 优雅退出 / 新 pid 36773 路径逐字对上、存档 106 → 106、近 15 分钟无本二进制 `.ips`。**下一轮第一件事**：BACKLOG 150 的**前置**（`CARD_INSET_DECLINED` 其实早就在打，但它把「这一带没有第二层」与「有材质却没量到卡片」两种成因写成同一句话 ⇒ 按 `fill` 拆两条 + 给原因串带上角色），然后 151（两把尺对账 + 给那把 python 尺加等式自检）、148（浮层三条左轴 12.5 / 22.0 / 35.5–37.5pt，先量焦点环那一格）、把 207 写进 `menuSurfaceReplicaFixtures` 的注释；真机那五条（人工批次 80.1–80.5）与 126 / 130 / 139 / 149 只能用户来。

> 上一轮（R100 / 第 102 轮收尾）原文开头：2026-10-16 23:51（本地 · R100 / 第 102 轮收尾：**BACKLOG 138 结案为「不是缺陷」，而且这是量出来的**：新夹具 `cardprobe-groupbox-default`（什么都不加的 `GroupBox{Text}`，自己声明 `.padding(24)`）量出**系统自己那一档就是 5.5pt**（亮暗同数），产品六张卡片 5.0~5.5pt ⇒ `.settingsCardInset()` 横向一个像素没加，而那句「macOS 通常 16–20pt」是没有出处的印象，按它改会让这扇窗口更不像系统。新判据 `testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox` = 等式（20 格与系统参照差 ≤1pt）+ **绝对锚点**（参照左沿必须落在夹具自陈的 24pt）：锚点不是装饰，M559 第一版（墨门限 60→4）**没让等式红** —— 参照与被告同偏、差还是 0，相对判据对「整把尺一起偏」免疫（D-160）。新尺第一版坏在**一条带子问了两件事**：材质与墨共用「卡片顶往下 26pt」⇒ 材质被圆角骗（报出 0.0pt 这个产品里没有的数）、墨被带子骗（`settings-general` 报 26.0pt，因为带子只盖住第一行、那一行的墨是复选框**后面**的标签）；现在材质问卡片纵向中点那一行、墨问整张卡片内沿。**CI 那台机器被发现在 R95–R100 五轮里从没看见过卡片材质**（`CARD_BAND` 二十格全 `填充=-1`，页底 236/52，而本机 255/247、30/37）⇒ 新开 **147**，并把「没有对象」从永久红改成**响着的 skip**：地板 `min(8, 读到材质的格数)` 从**上游那一关**推（从名单自己推是恒真式，M553 那种「把尺弄瞎」的刀咬不住），D-161。收尾给 147 装了**成因通道** `CARD_FILL_CANDIDATES`（D-163）：`cardRowKinds` 多返回一格 `modals`，`cardFill` 给 nil 时由判据自己打印前三名连行数 ⇒ 三种形状（门限 / 通道 / 判据没走到）在下一次 run 里就能压成一种；**本机已经用它正过一次** —— `settings-stats` 两档前三名全是页底（`252:960` / `28:960`）⇒「统计缺的那 4 格」是产品事实（那一屏本来没有 `GroupBox`），runner 缺的 20 格才是通道问题。**真机观测通道中途打开**（显示器醒了：`screencapture -x` 99.7% 非黑、AX 走状态菜单真的开得设置窗）⇒ 新开 **149**，量到真状态菜单 `pos=1073,34 size=207x294`、15 项（复刻夹具是 320pt，两侧第一次都有数），真机卡片与页面底差 **16** 而离屏同一处只有 **7**；但 `click at` 打不进 SwiftUI `List` 的选中 ⇒ 130 / 139 仍然欠着，需要走键盘那条路。**145 结案**（红的原文第一次在 runner 上读得到：名字、断言类型、数、判据自己写的理由四样都在）；**146 不结案**（这次没红 ≠ 它好了）。工具三笔（U-277、U-279）：还原臂基准写 `HEAD` 会随提交前进 ⇒ 钉死 commit `3a05933`；新表的 needle 想用**缩进**区分同文两格（浅缩进那一串是深缩进那串的**子串** ⇒ 恒 `DID-NOT-RUN`，要靠上一行）；预检查表写 `passed` 而 `run()` 通过时返回 `ESCAPED` ⇒ 恒 `PREFLIGHT_FAILED`、一支都不注入（这次坏得安全，同形反烧就是一道永远红的门）。**台账自己坏过一次**：编辑时 `old_string` 取了上一轮的标题行 ⇒ 「插入」变「替换」，`## Round 99` 整行被吃掉；两道守卫各响一次 —— `GAPS=[99]` 只报不拦（现在 `CURVE_GAP` 会 `return 1`，配 `scripts/tests/test_curve_gaps.py` 三条），`CURVE_DROPS_TAIL` 又暴露**两份台账排序方向相反**（ITERATION 升序 / UI_AUDIT 降序）。验证：**`VERIFY_OK=1`，且是 pass-3** —— 本节每个数都出自 `r100_verify.log` 这一份产物（pass-2 那份 `Ran 210` 早于新自检落盘，不能引用）：构建 0 告警、全量 `TEST_EXIT=0`（**815** 例 / 41 skip / 0 failures）、在屏 `PROBE_EXIT=0`（11 例 / 2 skip）、捕获 `帧数=130` 且 `COMPARED=130 CHANGED=0 MISSING=0 ADDED=0`、脚本 `Ran 213 tests OK`、**九张变异表 43 刀全部拿到各自期望的 verdict**（r100 四刀 CAUGHT + r100b 三刀：M560/M561 期望 **SKIPPED**、M562 期望 **CAUGHT**）、`LEDGER_EXIT=0`、曲线 `ROUNDS=101 first=1 last=100 CURVE_DERIVED=95,96,97`、`SUMMARY_MISSING=0`；本轮**不重装**（产品零改动，sha 前缀 `026aa3aacd38dccf` + pid 5779 + `proc_pidpath` 逐字核过）。**下一轮第一件事：读 R100 的 CI**（照 `.scratch/motion-audit-2/r100_ci_readings.md`；§④ 那三句「runner 上要看的」今天起真有一行可读），然后产品面做 **131**（统计屏是这扇窗口唯一没有卡片的一屏，本轮已从论证变成读数；R92 有先例语法：只动容器），真机面用键盘换分区去量 130 / 139，并把 207 写进 `menuSurfaceReplicaFixtures` 的注释（那处今天只有复刻体单边数）。

> 上一轮（R99 / 第 101 轮收尾）原文开头：2026-10-16 22:02（本地 · R99 / 第 101 轮收尾：**上一轮结尾记下的那句「Swift 那颗尺说只有推荐屏卡片顶之上有墨，python 尺说每一屏都有」—— 错的是我新写的 Swift 那一版**：`cardRowKinds` 交回的是**带内相对行号**，`columnInk` 吃**位图绝对行**，直接对接 ⇒ 量的窗口是 0..45.5pt 而不是 60..106pt，九屏全报「卡片顶上没墨」，而分区标题一直画在 78.5..90.5pt；位置也被 `toPt` 多加一次 60pt（真墨 78.5..90.5 标成 138.5..150.5）⇒ 换算提成有真值表的纯函数 `absoluteRows`（六条，第 ② 条就是这个错本身）+ 调用处恒等式（两边由两条式子算出，M552 一丢偏移就红，且同时把真值表弄红 = 一条变异两本账）。**142 结案**：新判据「有卡片的每一屏，卡片顶之上恰好 1 段、最后一张卡片之下 0 段」由读数生成 —— 改前两档 × 十屏：上方九屏各 1 段、推荐屏 **3** 段（112.5..124.5 卡片级标题行+「恢复默认」、146.0..155.0 说明段），下方推荐屏 tall 档 **2** 段（885.0..895.0、911.5..923.5）、其余 0 段；产品照名字改（**只动容器**：两段搬进 `GroupBox`，「推荐反馈数据」从裸 `Divider()` + 卡片外内容收成第二张卡片，字号 `.headline → .subheadline` 并档），改后 `CARD_ABOVE_SUMMARY` 20 格全 =1、`CARD_BELOW_SUMMARY` 16 格全 =0。**两条只有看图才抓得到**（U-256、U-257）：新卡片会按内容缩成 250pt 宽 ⇒ 卡片尺读不到材质，「没有第二张卡片」与「卡片太窄」共用一个读数（修法是 `.frame(maxWidth: .infinity)`，M555 钉它）；标题与按钮同行时那颗 22pt 的按钮把标题往下推 4pt ⇒ 极差 6.0 > 4.5 判红，`firstTextBaseline` 那一版无效（bezel 在基线之上比标题 cap 更高），改抄 `清空未收藏记录` 那段「标题+说明在左块、按钮 trailing 居中」。**R98 的 CI 读了**（run 38898253512）：**failure**，红在 `On-screen probe coverage floor`（R97 同一支判据 红=0 ⇒ 不是环境噪声）；144 有答案并结案 —— 种子判据在 runner 上是 **NOT_RUN**（整页零墨，它没把「拍不出」读成「通过」，也没红在中间态），但「种子通道在 runner 上至今没有真值点」另记；新开并修 **145**：那一步只报「哪条红了」不报「红在哪一句」，而那句就在同一行里，被 `ASSERTION_RED` 截掉 ⇒ 现在结论行带原文（`test_probe_coverage_gate.py` 钉「数值与理由都必须在」）；新开 **146**：那条红在 runner 上到底为什么，等 145 上 runner 之后第一次能读到原文的那次 run，本轮不猜。**工具与纪律三笔**（U-262、U-263、U-264）：改容器把三刀变异臂的锚点挪掉了（`needle 命中 0 ⇒ DID-NOT-RUN`，不是通过 ⇒ 换锚点并注释「牙没变」，r98_seed 7/7、r98_card 2/2 复验）；我在电池跑着时编辑了被注入的文件，`RESTORE_CLEAN=NO` 如实报脏（那一格报对了，错的是操作顺序）；报告里五格汇总停在旧数（标题 R46、D-149、796 例、112 帧、M509、127 条）⇒ 本轮起数字从 `r99_verify.log` 读出来再写。验证：**`VERIFY_OK=1`** —— 构建 0 告警、全量 `TEST_EXIT=0`（812 例 / 41 skip / 0 failures）、在屏 `PROBE_EXIT=0`（11 例 / 3 skip / 0 failures）、帧 128 比对 `CHANGED=0 MISSING=0 ADDED=0`、脚本 `Ran 210 tests OK`、**七张变异表全绿**（节奏 4 / 行序 7 / 分诊 7 / 卡片 5 / 种子 7 / 产品腿 2 / R99 四刀 4）、`LEDGER_EXIT=0`、曲线 `VIS_EXIT=0 ROUNDS=100 first=1 last=99`、`SUMMARY_MISSING=0`。**下一轮第一件事：读 R99 的 CI（146 的答案 —— 红的原文现在可读得到），然后做 BACKLOG 138（先按 U-265 收窄：「5.5pt」是墨到边、含字形侧边距 ⇒ 要换成控件 bezel 到边重量，并核对「16–20pt」是量出来还是印象），产品面还欠 133 / 131 / 139 / 124②）

> 上一轮（R98 / 第 100 轮收尾）原文开头：2026-10-16 20:05（本地 · R98 / 第 100 轮收尾：**上一轮记下的"两条读图通道给出不同卡片边界"被它自己的对照证伪 —— 判据量的根本不是交付的那一页**。R98 按 141 写的做法接上第二条读图通道，第一件事就是它的前提塌了：`CARD_CHANNEL_SUMMARY 不一致=0`（settings 族 20 帧逐段一致，连页底/填充都同数），而 `CARD_BYTES` 打出`本用例=319980 捕获卷=333059 字节数不同` —— 不一致的是**两张不同的文件**，而它是全仓唯一声明了 `seed:` 的夹具；逐行指纹把分歧起点钉在 566.0pt，870.5..936.0pt 交付帧 54 行墨 / 判据帧 0 行，右边缘 x 684..706pt 交付帧 2 段「移除」/ 判据帧 0 段。根因：`Fixture.seed` 的"种 + 还原"只写在 `testCaptureKeyViews` 一处，其余二十多个 `render` 调用点把它当不存在 ⇒ 判据量的不是它名字里那张图，而帧基线钉的是有种的那一张（教训一句话：**先证明两边读的是同一个对象，再谈通道与阈值**）。修法：种子搬进 `render(...)` 这个唯一咽喉 + 三条新判据（拍之前故意把那个键种成**别的条数**、整页零墨记未运行、拍完必须还原）+ 调用点守卫（全文件只准一处写种子）；M543–M549 `n=7 caught=7`。台账：**141 撤机制**（原文保留、写明被哪条读数推翻）、**140 结案**（`settings-privacy-tall` / `settings-recommendations-tall` 进基线，124 → **128 帧**，540 档照旧 declined、没放宽）、**新开并修 143**（数卡片的守卫只扫 `SettingsView.swift`，而「推荐」那张长在 `RecommendationWeightsView.swift` ⇒ R95 那次"五处一起补"漏了它；改成枚举 Views 目录 + 点名文件）、**新开 144**（种子判据欠 runner 第一个读数：runner 的 settings 族未绘制是 90.6–95.9% 而非 100% ⇒ "整页零墨才 skip"只算半安全，不许借另一台机器的数加地板）。产品一处：高夹具第一次拍到「推荐」卡片底边，量出 `边距=11.5/9.5` 对 `内侧=16.5/18.0` ⇒ `spacing 16→12` + 孤儿 padding 换成共享 `.settingsCardInset()`，改后 `14.5/12.5` 对 `12.5/14.0`（亮暗两档都看了改前/改后对照），牙是 M550（只改行距 ⇒ 只许节奏红、调用点守卫必须绿）与 M551（撤共享留白 ⇒ 两条都要红且点名文件）。工具三处自己坏了（U-248…U-251）：电池用 `${tag^^}`（本机 bash 3.2.57）⇒ 六张表只跑一张而 `MUT_EXIT=0`（恒真的门，`bash -n` 看不出来）；`curve_from_ledger.py` 不认 `**均分 91.3**` ⇒ 六轮被静默跳过（尾轮守卫拦下）；Round 93/94 两节当时根本没写七维自评表 ⇒ 按那两轮自己的读数补上并标注"R98 补记"，报告那两格刷新成 **91 轮 / mean 92.86 / GAPS=none**；为 R99 写的 python 仪器三条自检全不过（卡片顶差 14pt、亮暗互差 7pt、把热图切成 11 段"卡片"）⇒ 现在默认拒绝出表，并顺手推翻 142 那句"其余几屏标题与内容一起进卡片"（实测每屏分区标题都在卡片外，真正的差别只有这一屏把卡片自己的标题+按钮+说明留在卡片外）。验证：`VERIFY_OK=1`：构建 0 告警、全量 `TEST_EXIT=0`（811 例 / 41 skip / 0 failures）、在屏 `PROBE_EXIT=0`、帧数=128 且 `FRAMES_EXIT=0`（`CHANGED=0 MISSING=0 ADDED=0`）、脚本 `Ran 209 tests OK`、**六张变异表 32 刀全 CAUGHT**（节奏 4 / 行序 7 / 分诊 7 / 卡片 5 / 种子 7 / 产品腿 2）、`LEDGER_EXIT=0`、看图仪器 `VIS_EXIT=0`。**下一轮第一件事：读 R98 的 CI（含 144 那一格：种子判据在 runner 上是绿/红/skip），然后做 142（前提已齐），产品面还欠 133 / 131 / 139 / 124②**）

> 上一轮（R97 / 第 99 轮收尾）原文开头：2026-10-16 18:55（本地 · R97 / 第 99 轮收尾：**卡片那把尺之前把一条 1pt 的分隔线、一颗按钮、两张卡片都当成"一张卡片"** —— 三条读数各推翻一次判定：① `边距=14.5/8.0` 是**假红**（独立复算 14.0），根因是"这一行的众数离页面底 ≤3 就算卡片外"，而材质与页面底在这台机器上只差一个色档（244 vs 252）；② 修完又红：y=106..129.5 那张"卡片"其实是「恢复默认」那颗 76pt 按钮（`内侧 0.0/0.0`）；③ 再修完发现一个带子里有**两张**卡片，判据把整带当一张量。修法是三格纯函数：`cardFill`（填充要占 ≥20pt 的行）、`cardRowKind`（一行算不算卡片看**最长连续材质**：实测 14% / 46% / 94% ⇒ 地板 30%）、`cardSegments`（先分段再逐段判），外加**BACKLOG 140 的真病根**：扫描带写死 440pt ⇒ 改成跟着夹具尺寸走 + 恒等式`带子下沿==窗口高`，而"这一页比窗口高，被切断了"那句解释从纯函数搬到见过窗口尺寸的调用处。台账那一腿：**132 结案** —— run 38884429809 给出 `主线程采样=314 等待帧占比=100% 等待终端=1 个` + `blocked@runloop-wait`，那条吃满 240 秒的探针是**挂**不是慢（上一轮欠的 SHAPE 那行没出现，因为它只在读不懂时才打；而那一格正是这次"读到了"可信的前提）。新开 **141**：判据读的是 `tiffRepresentation` 出来的 `NSCalibratedRGBColorSpace` 位图，不是它刚写下的 PNG —— 同一张帧两条通道给出不同卡片边界（705.5pt vs 765.5pt，顶边一致、另一段高度一致）⇒ 本轮高夹具上的"通过"记成**暂定**，换通道的代价是十几支像素判据的阈值都要重标（必须成对做 before/after）。仪器自己错一次（U-237）：我先假设"热图那块底色被当成卡片"，正对照当场否掉——那些行的众数全等于页面底，真凶是那条 1pt 的 `Divider()`。验证：`VERIFY_OK=1`：构建 0 告警、全量 `TEST_EXIT=0`、在屏 `PROBE_EXIT=0`、帧数=124 且 `FRAMES_EXIT=0`（`CHANGED=0`）、脚本 Ran 209 tests OK、四张变异表全 CAUGHT、`LEDGER_EXIT=0`、看图仪器 `VIS_EXIT=0`（候选块=9 自检=1 失败自检=0）。**下一轮第一件事：141**，然后回到产品面欠账 133 / 131 / 139 / 140 剩那一半）

> 上一轮（R96 / 第 98 轮收尾）原文开头：2026-10-16 18:05（本地 · R96 / 第 98 轮收尾：**上一轮"特意留下"的那一格 padding，被自己扩了对象的判据当场推翻** —— 把 `testSettingsCardVerticalRhythmIsOneNumber` 从"只压 settings-shortcuts 一张"扩到"每一张 settings 卡片"之后，`settings-data` 立刻红：`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`，根因是三段里只有第一段带 `.padding(.vertical, 4)`；我上一轮给它的理由是"卡片内部讲的是另一件事"，而它讲的就是同一件事（行与分隔线之间的距离），却只有一段有 ⇒ 删（U-227 / D-154）。容差 3.0→4.5 不是放宽：**3.5pt 是这张帧里"按钮 bezel 底下不画墨的边"的实测值**，加 1pt 余量，出处写在断言旁边，且 R95 的缺陷（8.5）与 M528（7.5）都仍被抓住；扩对象那一刀同时补了"读到墨却一条都没判 ⇒ 红"，否则扩出去的那九张只会让"没判"更安静（M530 从 DID-NOT-RUN 变 CAUGHT）。台账那一腿：读 run **38876999489**（`bf6b921`）**success**，覆盖率闸门与上一轮完全一致（`红=0`、`露面=7/11 未闭口=1`、`PROBE_QUEUED` 同一批四条）⇒ 上一轮的登记刷新没制造新红；而 132 的第一份 runner 栈读出来是 `主线程采样=306 主导路径占比=100% 最深帧=读不到` + `blocked@unknown` —— **后一半是假话**：`nodes` 为空时占比被兜底成 1.0，于是"我读不懂这份文件"被打印成"它挂在某个不认识的帧上"，还带着一个具体百分比 ⇒ 撤兜底（读不懂=未量到、占比 0.0），新增 `UI_PROBE_SAMPLE_UNPARSED` 与只含缩进/是否数字开头的`UI_PROBE_SAMPLE_SHAPE`（**不打帧名**：日志不许出现用户剪贴板内容，而诊断不需要帧名）。**137 结案**，修法不是补夹具而是换判定来源：`_waiting_leaves` 数"有多少采样停在等待帧上"（嵌套只算最内层、并列报两个族）⇒ `blocked@ambiguous`；变异表重做 `n=7 caught=7`，退役的 M525/M527 记在 harness 文档串里（"表里少一格"与"那一格永远绿"是同一种失忆）。看图那一腿：设置「隐私」逐元素 —— 勾选框两态可辨（框自己的填充换一档 223→213 / 58→67，对勾 46/47 颗 vs 未勾 12–20/13–20 颗）⇒ 不加动效；但五颗框 `chroma=0`（勾选态不是强调蓝）而源码全是裸 `Toggle` ⇒ 灰不是产品选的色，开 **139** 走真机（批次 75.1），本轮不改它；默认排除那一列帧里可见 8 行（名单共 9 项、第 9 项在窗口外）共一条左轴 177.5pt ⇒ 重复前缀判过不改（U-229）；仪器自己错两次（门槛 60 只检出 3 颗 → 降到 15 检出 7 颗 → 最后用"框有自己的填充"判，正好 5 颗）=U-230；三张比窗口高的卡片被尺明确报成"卡片底到带下沿 ⇒ 不判"而不是"没有分隔线" ⇒ 开 **140**。验证：`VERIFY_OK=1`：构建 0 告警、全量 `TEST_EXIT=0`、在屏 `PROBE_EXIT=0`、帧数=124（日志那格写的是 125：目录里除 PNG 还有一份 capture-readings.log） 且 `FRAMES_EXIT=0`、脚本 Ran 209 tests OK、三张变异表全 CAUGHT、`LEDGER_EXIT=0`、看图仪器 `VIS_EXIT=0`（卡片=2 框=10 自检=2 失败自检=0）。**下一轮第一件事：读 R96 的 CI 里 `UI_PROBE_SAMPLE_SHAPE` 那一行（三种形状三种下一步，写在 `r96_ci_readings.md` 末尾），然后做 140 与 133**）


> 上一轮（R92 / 第 94 轮收尾）原文开头：2026-10-16 13:30（本地 · R92 / 第 94 轮收尾：**两道最终闸门读的是我自己的自检夹具** —— R90 CI（run 38846896495）里 `Capture gate` 那句"这一步没跑到用例"与 probe floor 的 `started=probeA` 都是假红：`probeA` 是我夹具里的用例名，而 `run_bash()` 只把 `/tmp/shots-ci` 换进临时目录，`cp FAKE_LOG /tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log` 写进了作业共享的 /tmp，把挪到末尾的两道门要读的日志覆盖了。本机实测复现（写完 marker 跑一遍自检，marker 一行不剩），三次 run 对账钉住"是 R89 挪位置之后才有的"（挪之前 补回=0/passed=38/ok，之后两次 402/0/fail）。修：`prepare()` 通配映射所有 /tmp + 三条守卫（真值表 / 逐格扫描 / 行为证人成对断言）+ 闸门成因改三支（同源证人 / 异源 / 两边都空，标准一字未动）+ `CAPTURE_GATE_INPUT` 自报读到了多大（U-211…U-215、D-150）。中途读到 R91 的 CI（run 38852286519）：删掉僵尸之后在屏那一卷**第一次在 runner 上下了结论** —— `已下结论的用例: 6`、`started=7`、`UI_PROBE_CHANNELS_AGREE=1`、名册 10/10 无 STALE ⇒ **BACKLOG 92 结案**；第 7 条 `testRightClickMenusAppKitWouldShowAreChinese` 吃满 240 秒，本机它是跑完的 ⇒ 新开 132（只点名，没在 runner 上 `sample`，不写"同一族"）；同一次 run 里两道闸门仍报 `本次下结论=0`，与 `concluded=6` 直接矛盾 ⇒ 128 最好的现场证据。牙 M510–M515：5 CAUGHT / 1 如期 ESCAPED（M515 = 自检不认识的那一步仍能写共享 /tmp ⇒ 新开 129），另有两把刀第一次逃掉各自量出真东西（U-215：尾部边界没覆盖、临时目录跨次复用让上一遍的 PNG 替这一遍作证）。真实看图那一腿：设置「数据」分区逐元素判完（14 项带坐标），真正改的是**分组语言** —— 五种分区四套语法，这一屏唯一"卡片只圈一部分 + 外面压两条线"，三段并进一张卡片、线挪进卡片内：卡片 (172,106)..(696,158)→(696,318)、外部线 2→0、内部线 0→2（166pt、271pt）、说明段对比 3.59→3.64（与通用 3.74 同档），动画键/回执/禁用一行未动。**两条结论被读数撤回**：`appActive=false` 这条通道判不了 accent 派生的红与蓝（那颗 `.tint(.red)` 的按钮、那颗选中胶囊 3.53/3.47 都是通道的数，进 130 等真机）；抄来的"色相 ≥25"把一颗量得到的胶囊读成没判（U-212）。换装：本轮改了产品 ⇒ `install_local.sh --yes` 真换装，`INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`（staged=installed=`f0ccc2bc8c04f97b…`，换掉 `7ef8c6eca171adbd…`）、新 pid 40228 启动晚于安装且 exe 路径逐字对上、存档 105→105（只读核对）、旧包留在 `Documents/Codex_Project0_backups/before-local-20261016-134328`。**真机看一眼这一腿仍然做不了，而且是量出来的**：装完立刻 `screencapture -x` 得到 2940x1912 的图，3744 个采样点里非黑 **0** 颗、最亮 (0,0,0)，`pmset` 报 `UserIsActive 0` ⇒ 显示器睡着 + 没录屏权限，BACKLOG 126 与 130 继续记未运行（不是"看了没问题"）。验证：非台账文件 5 个（产品 1 个：SettingsView.swift，另 1 个是脚本生成的帧基线清单）；构建告警 0；全量 Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.840 (144.883) seconds| Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.840 (144.884) seconds|（exit 0）；捕获 exit 0 `Executed 47 tests, with 4 tests skipped and 0 failures (0 unexpected) in 115.767 (115.771) seconds`；帧 124 张 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；脚本 exit 0 `Ran 181 tests in 11.108s OK`；头条那条 hermeticity：四份 marker `4/4` 存活；电池 exit 0 `汇总：5 刀 CAUGHT / 1 如期 ESCAPED（已知盲区）/ 0 没跑成 / 0 预期不符（共 6）`。没跑的：runner 上这两道门第一次读到真日志（128 剩下那一格，只有下一次 CI 知道）；132（`testRightClickMenus…` 在 runner 上是挂还是慢，本轮只点名）；R91 CI 里那 6 条结论各自是什么判定（没按步骤名逐条读，U-178）；「清空」与选中胶囊在真机 key 窗口的 accent 那一档（130）；统计页那套分组要不要并入（131）；BACKLOG 127 的正对照；BACKLOG 124 第②步；BACKLOG 92 剩下那一格。**下一轮第一件事：读 R92 的 CI（`补回` 必须回到 0 附近、`probeA` 这种夹具名必须消失、两道闸门的 `本次下结论` 必须与那一步自己打的 `concluded=6+` 对上），然后 BACKLOG 132 的 `sample` 与 127 的正对照**）


> 上一轮（R91 / 第 93 轮收尾）原文开头：2026-10-16 12:25（本地 · R91 / 第 93 轮收尾：**追了五轮的"CI 上一条在屏判据都没跑完"，成因是一条我以为删掉了、其实没删的探针** —— D-034 的正文写着"原来那条拖选探针删除并在原位置留了一段解释"，解释在，函数也在：`git log --all -S "func testDragSelect…"` 只有 9d7b5ca 一次增、零次删（U-206）。它这六天做的事是把整卷挡死：本机三遍都是 180 秒被掐、心跳 2、有结论 0，`sample` 给出栈 `sendEvent → NSCoreDragManager _tryCatchDragUntilMouseUp → CoreDragStartDraggingAsync → _BlockUntilNextEventMatchingListInMode` —— CoreDrag 等的是窗口服务器的真 mouseUp，而探针把 mouseUp 排在 `sendEvent` 下游 ⇒ 进程内无解。我第一版"压到 2pt 阈值内"的修法被**第二次测量**撤掉（栈一模一样，U-207）。⇒ 撤掉合成拖拽（连工具函数），限制打成 `DRAG-LIMIT` 读数，机制级守卫 `testProbeSuiteNeverSynthesizesADragSession` 钉住事件类型（牙 M505–M509：4 CAUGHT / 1 逃掉（M509，故意）/ 0 没跑成）。**修完第一次跑到 心跳=10 executed=10 passed=7 skipped=2 failed=1**。另两格：帧间隔判据加了 `FRAME_CHANNEL` 通道证人（这台机器显示器睡着 ⇒ 0 个样本不配判产品，地板一条没放宽，U-209）；看图发现**亮档基线帧里被选中的那一行是纯黑色带（2/255）且整帧零蓝**，与在屏探针自己拍的帧同形 ⇒ 两条离屏路径共有的盲区，进 126；真机截图那一腿 NOT-RUN（`screencapture` 全黑、`UserIsActive 0`）。新开 **127**：一行两个半宽 `KeyViewProxy` —— 第一次跑完就红，本轮只点名不定性，所以推上去之后 main 带着一朵**有名字的红**。验证：非台账文件 3 个、产品 0 个；构建告警 0；全量 Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.711 (144.753) seconds| Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.711 (144.754) seconds|（exit 0）；脚本 Ran 173 tests in 10.955s OK（exit 0）；电池 M505–M509：4 CAUGHT / 1 逃掉（M509，故意）/ 0 没跑成；帧 124 张 + 对账 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；没跑的：BACKLOG 127 的定性（一行两个半宽 KeyViewProxy：产品无障碍结构 vs 探针期望没被正对照校准）—— 本轮只做到让它第一次跑出结论并点名；BACKLOG 126 的决定性实验（真机窗口截图 vs 离屏帧）：这台机器现在做不了 —— screencapture 返回 2940x1912 全黑、pmset 报 UserIsActive 0 ⇒ 显示器睡着/无录屏权限。这一格是**没跑**，不是「真机也看不见」；BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）；runner 上的两件事：① 在屏那一卷第一次能跑到 10 条结论吗（本机已证）② FRAME_CHANNEL 在 runner 上是 n=0 还是有 tick；换装：本轮产品文件 0 个 ⇒ 不换装（帧按构造不变，仍实测对账）。**下一轮第一件事：读 R91 的 CI（在屏那一卷第一次在 runner 上跑到几条 + coverage 门会不会报"说跑不了却跑到了"）+ BACKLOG 127 的正对照**）


> 上一轮（R90 / 第 92 轮收尾）原文开头：最后更新：2026-10-16 11:20（本地 · R90 / 第 92 轮收尾：**读 R89 的 CI 两条都成了，而 BACKLOG 122 的承重墙在动手前被自己的测量推翻** —— `UI_PROBE_ORPHAN_XCTEST=0`（R88 三条 run 连着是 1）与 `skipped 步骤数 = 0`（R88 是 7）⇒ U-192 / U-193 两条修法在 runner 上被证实，而且是那道门自己从红变绿。122 结案，但通道换了：R89 写的"stderr 活得过 SIGKILL"实测是假的 —— `swift test` 下 fd1/fd2 都是 SwiftPM 驱动的管道，驱动被杀时两块一起丢（U-201）⇒ 心跳改走**自己 open 的文件**，报告器加 `--pulse` 做**双通道对照**，一致才点名、不一致退回"只报观察"。93 第一次有名字：心跳点名 `testDragSelectExpandsSelectionInsideTheRealList`，`sample` 的栈独立同意（CoreDrag 模态循环等一个不会来的 mouseUp，本机可复现）⇒ 修法开成 **125**。CI 那朵新红是我自己造的：两卷共用一份读数文件，"第一写整份重写"把捕获卷抹掉（`passed=0 NOT_RUN=49`）⇒ 换目录 + `PulseWiringTests` 按步骤钉住归属（U-202）。真实看图这一腿：设置「统计」整屏重判，结论**不加任何新动效**；顺带量出 R88 那把侧栏尺的两处失效（只认比背景亮的墨 + 列常量错位一整列）⇒ "亮色侧栏没问题"从来不是读数而是没量到（U-203），本轮新尺第一次量到亮档标签 251/255；新尺在暗档 NOT-RUN，那一格仍只有一份旧读数（U-205 与 126）。**本轮破例：非台账文件 7 个（约定 ≤4）**，理由与代价写在正文 §5 与 D-148。验证：产品 0（只动 Tests/ ⇒ 帧按构造不变，但仍实测一遍）；构建告警 0；全量 Executed 801 tests, with 41 tests skipped and 0 failures (0 unexpected) in 144.690 (144.731) seconds ；Executed 801 tests, with 41 tests skipped and 0 failures (0 unexpected) in 144.690 (144.733) seconds（exit 0）；脚本 Ran 173 tests in 11.338s OK（exit 0）；帧 124 张 + 对账 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；电池 汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）；没跑的：拖拽探针挂死本身的修法（BACKLOG 125：加看门狗 vs 改成直接调手势逻辑，本轮只做到能点名）；runner 上的两件事：① 心跳通道在无头 runner 上是否同样落盘 ② 换目录之后 Capture gate 是否复绿 —— 只有下一次 CI 知道；第一次全量 swift test 的退出码不作数（那条 SWIFT_TEST_EXIT=0 量的是管道尾端的 tail）⇒ 本轮的数以上面 SWIFT_TEST_EXIT 那一行为准（U-200）；BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）；BACKLOG 126：离屏捕获 vs 真机窗口截图那一次对照（本轮只做到把不一致量出来：亮档四枚图标 0 墨、推荐一枚纯黑）；暗档侧栏逐行读数：新仪器在暗档上 COLUMN_SEGMENTS=1 ⇒ NOT-RUN，那一格仍只有 R88 那一份（且身份错位）。**下一轮第一件事：读 R90 的 CI（`Capture gate` 必须复绿 + 心跳通道第一次在 runner 上落盘），然后 BACKLOG 125 先 spike 再动仓库**）

> 上一轮（R89 / 第 91 轮收尾）原文开头：最后更新：2026-10-16 09:05（本地 · R89 / 第 91 轮收尾：**读 R88 的 CI 又读到 main 红，而红的是 R88 自己新写的那道门 —— 它同时给了两件东西：想要的那格读数，和修法不成立的证据** —— `UI_PROBE_START_LINES_LOST=1` 第一次在 runner 上说话（93 的成因由 CI 自己确认为②：stdout 块缓冲被 SIGKILL 整块带走），而 `PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑` 说明 R88 的组杀够不到它：本机量到 `swift-test pid=pgid=27359` 而 `xctest pid=pgid=27416` —— **xctest 自己 setpgid 成了另一个组的组长**（U-192）。更贵的是第二个后果：那道门红了之后 GitHub skip 掉后面**七个步骤**（动效卷、动效地板、脚本自测、两张帧基线、启动冒烟）⇒ 仪器的红吃掉了产品的证据（U-193），所以本轮**没有** coverage 第六个数据点，119 按欠账记。本轮（D-147）：① 残留收杀放在父壳 `wait` 之后（第一版塞进 killer 子壳会被 `kill "$killer"` 掐死在半路，对照读到 `Terminated: 15` + 残留 1 —— 同一段代码位置错了就是竞态，U-194）；② 四道硬门全部挪到产证据步骤之后并各自 `if: always()`；③ 自检改成按位置查 + 逐门查（U-195：`if: always()` 数总量 ≥4 是假尺，文件里本来有六处，M492 第一版因此 ESCAPED）。牙 M489–M496 八刀全 CAUGHT；三形状对照 6/6（旧形状留孤儿 / R88 形状**仍然**留孤儿 / R89 形状残留 0）；真机进程树实测残留 0。**本轮零产品改动 ⇒ 不换装**。验证：非台账文件 1 个、产品 0 个；脚本 Ran 160 tests in 10.964s OK（exit 0）；对照 接线检查 OK（10 项都在） 步骤顺序：Frame baseline vs previous release (change report, report-only) Runtime launch smoke (report-only) Swift tests (executed-count gate) Capture gate (unregistered reds must be zero) On-screen probe coverage floor Motion coverage floor   CAUGHT 旧形状留下孤儿（对照有内容）   CAUGHT R88 形状**仍然**留下孤儿（这条对照测的是 SwiftPM 的 setpgid，不是 bash 默认）   CAUGHT R89 形状收干净（残留=0）   CAUGHT R89 形状在收掉前量到"还在跑"   CAUGHT CI 两步都写了（含"再杀残留孩子的组"那一刀）   CAUGHT 四道硬门都排在产证据的步骤之后 R89 对照 6/6 通过；电池 汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）；树 PGID_OF_JOB=36612  PID_OF_JOB=36612 父壳收残留组 36633（孩子 pid=36633） 残留=0 ⇒ 组杀其实够到了（那 CI 那一格红的是别的原因） === 最终残留 === log_bytes=201 started=0；没跑的：swift_build / swift_test_full / motion 与 capture 闸门 / frame_baseline（本轮零 Swift 改动；CI 那一步会自己跑）；runner 上的真实效果（ + 残留收杀在无头 macOS runner 上够不够，只有下一次 CI 知道）；BACKLOG 122 的每条判据心跳（本轮先修 R88 留下的两处不完整，一次只改一处）。**下一轮第一件事：读 R89 的 CI（`UI_PROBE_ORPHAN_XCTEST` 必须变 0 —— 那才是『看门狗真的够到了』的证据）+ 把 BACKLOG 122 的 stderr 心跳接上**）

> 上一轮（R88 / 第 90 轮收尾）原文开头：最后更新：2026-10-16 07:20（本地 · R88 / 第 90 轮收尾：**读 R87 的 CI：main 绿了，而绿的方式说明上一轮那朵红的处置今天没被检验；同时本机按 CI 原样重跑看门狗，把 R86 写下的那句话判成了假话** —— `swift test` 是三层进程，`kill -9 $pid` 杀的是 `swift-test` 驱动，带着 11 条用例名的 `xctest` 被 reparent 之后继续活着（一次活了 5 分钟、占着 `.build` 锁把后面两遍全堵死），而日志停在 119 字节、`started=0` ⇒ `UI_PROBE_NO_CASE_STARTED=1（进程在第一条用例开口之前就死了）` 是假话，而 R86 我自己写的硬门把这句假话读了两遍当成"有名字"。本轮（D-146）：看门狗改 `set -m` + `kill -- -$pid`（进程组），收掉之前先 `pgrep` 写 `/tmp/ui-runner-alive`；报告脚本按这个数分三格（活着⇒点名 `START_LINES_LOST`；没起⇒才许说 `NO_CASE_STARTED`；没量⇒只报观察），三格互斥由自测钉住、坏值不许猜；硬门读**落盘**的孤儿数（U-188：跨步骤没有共享 shell 变量，第一版写成 `${orphans}` 会造出一道恒真的门），读不到文件另红一格。93 的成因由此分开（是②通道丢了），但"挂在哪一条"仍然没名字 ⇒ 新开 **122**（每条在屏判据自己写一行读数 + 那颗三遍分布 0.671/1.000/**0.043** 比产品还宽的等节拍证人配不配签红）。119 第五个点：coverage **0.690**（runner 四遍 0.522/0.842/0.032/0.690，跨度 0.81），而 `contradicted-by-travel` 那一支**至今没在 runner 上触发过** ⇒ D-145 挡红的能力仍未证。牙 M481–M488 八刀全 CAUGHT（M484/M485 第一版 ESCAPED 是刀留着原 token 前缀，子串查下"删掉了"隐形 —— U-189；U-190：对照第一版用 python 侧 pgrep 量的其实是管道开合，判定改读脚本自己 ps 那几行）。**本轮零产品改动 ⇒ 不换装**。验证：非台账文件 4 个、产品 0 个；脚本 Ran 160 tests in 6.692s OK（exit 0）；机制对照 CAUGHT 旧形状确实留下孤儿（对照有内容，不是恒真）   CAUGHT 新形状收干净（脚本自己 ps 里没有残留）   CAUGHT 新形状在收掉前量到"还在跑"（RUNNER_ALIVE=1）   CAUGHT CI 两步都写了（set -m / 组杀 / --runner-alive / 硬门那一格）   CAUGHT 两步的 shell 语法过 bash -n（块数=2） R88 对照 5/5 通过；电池 汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）；没跑的：swift_build（Swift 侧一行没动，见 PRODUCT_TOUCHED；CI 那一步会自己跑）；swift_test_full（同上，801 例由本轮 push 触发的 run 覆盖）；motion_floor_gate / capture_gate / frame_baseline（都要求 Swift 产物；本轮零 Swift 改动）；runner 上的 set -m 真效果（只有下一次 CI 才知道 —— 那正是本轮要读的那一格）。**下一轮第一件事：读 R88 的 CI（`UI_PROBE_RUNNER_ALIVE` 与 `UI_PROBE_ORPHAN_XCTEST` 第一次在 runner 上说话 —— 那一步会证明 `set -m` 在无头 macOS runner 上到底成不成立）+ BACKLOG 122**）

> 上一轮（R87 / 第 89 轮收尾）原文开头：最后更新：2026-10-16 06:20（本地 · R87 / 第 89 轮收尾：**读 R86 的 CI 读到 main 红了** —— 红在 `Motion coverage floor`，`testSkeletonSweepActuallySweeps` 把产品判成 `.productRed`（coverage **0.032**，1/23 对在变），而**同一卷**上位置尺读到 可用帧 12、行程 **134pt**、亮带从 x=21pt 走到 x=155pt。R84 换画法之后四遍：coverage 0.522 / 0.842 / 0.032，行程 109 / 134 / 134pt（本机那一遍见 Round 87 那张表）⇒ 翻脸的是 coverage，它只有 1–2 个变化帧对撑着，而位置尺在 runner 三遍上有 11–12 个可用帧（本机那一遍 7）。本轮把**定罪权按样本数分配**（D-145）：`loopAdjudication` 多一个 `travel` 入参，两把尺矛盾时改判 `notRunRulerBlind`、点名 `loop-coverage-contradicted-by-travel`（不红不绿，进登记表），并用三格方向钉子钉住它没被放宽（位置尺说没走过 / 没读数时仍然红，产品在动时行程不许翻案）。U-185：新坏法必须有新名字，自测两格 + Swift 两条断言钉住"两支 not-run 不许同名"。另一件半事同时发生：R86 那台报告器第一次在 runner 上给出停机名字 —— `UI_PROBE_NO_CASE_STARTED=1`，**推翻了我上一轮预先登记的"挂在字母序第一条"那一半**；但 `started=0` 还有第二种成因（SIGKILL 把块缓冲的 stdout 整块带走，R64/R84 各一次），这一份日志分不开 ⇒ 93 不结案，分开它的方法（看产物通道有没有帧）交 R88。新开 **120**：位置判据今天仍被 `loopCapable` 关着，而它恰恰是唯一有资格签字的那把尺。牙 M473–M480 八刀全 CAUGHT（M475 / M476 第一版 NOT-RUN 是变异文写了 `#` 注释、Swift 编译不过 —— U-186）。**本轮零产品改动 ⇒ 不换装**。全量 801 tests / 0 failures（41 skipped，swift test exit 0）；动效闸门 MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=4 notice-banner=12 notice-banner-dismiss=13 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0；捕获闸门 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）；帧基线 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；脚本 Ran 155 tests in 6.779s OK；告警 0。**下一轮第一件事：读 R87 的 CI（红有没有真的消失 + `LOOP_NOT_JUDGED=…contradicted-by-travel` 第一次在 runner 上出现）+ BACKLOG 93 那一步产物通道的分开法**）

> 上一轮（R86 / 第 88 轮收尾）原文开头：最后更新：2026-10-16 05:25（本地 · R86 / 第 88 轮收尾：读 R85 的 CI（run 38805382593）—— **main 连续第二轮绿，而 `loops` 那一层第一次在 runner 上判到自己**：两行状态都读到（`MOTION_SHIMMER_STATE 判定=ok` / `MOTION_SHIMMER_BAND_STATE 判定=ok`），闸门打了两行 `MOTION_FLOOR_LOOP_JUDGED`、REDS=0。119 拿到第四个数据点：产品 coverage 0.522 → **0.842**（同画法同机器）⇒ 这一格本轮被我自己读反过一次：两遍都在地板上并不构成"收成硬门"的理由，**0.32 的跨度本身就是它还不稳的证据**（R38 倒着读）。本轮改的是"没跑完也要有名字"：新增 `scripts/ui_probe_report.py`，用 started 减 concluded 点名挂死的那条用例，而"说不出为什么停"的四种形状（日志不完整 / 喂的是步骤摘要 / 空日志 / 读不到）**一律红**；CI 两步各用一次（报告型打名字，`On-screen probe coverage floor` 要求必须有名字）。为什么不动 11 处测试代码：spike 实测 `kill -9`（退出码 137，与 CI 同形）之后 started 行留在日志里，13/12 的差集正好点名。三条读数进台账：读 CI 要按步骤名过滤（U-178）、『没有 Test Case 行』有两种成因（U-179，我本轮真的拿错过一次）、判变异落地要看内容不是看文件变没变（U-180，M472 第一版是我的刀没带那个词）。116 被四遍测量**收窄**（不复现"差 7 条"，捕获那五条在 runner 上其实有名字），92 **不结案**：runner 上到底挂在哪一条是**下一次 CI 的读数**。牙 M465–M472 八刀全 CAUGHT；`must_judge` 仍然 false。**本轮零产品改动 ⇒ 不换装**（帧基线 124 张逐字节不变、`Sources/` 一行没动）。全量 801 tests / 0 failures（41 skipped，swift test exit 0）；动效闸门 MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=13 notice-banner-dismiss=12 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0；捕获闸门 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）；帧基线 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；脚本 Ran 155 tests in 6.837s OK；告警 0。**下一轮第一件事：读 R86 的 CI（`UI_PROBE_HUNG` 第一次在 runner 上说话）+ BACKLOG 116 剩下的那半格**）

> 上一轮（R85 / 第 87 轮收尾）原文开头：最后更新：2026-10-16 04:20（本地 · R85 / 第 87 轮收尾：读 R84 的 CI（run 38798408040）—— **main 绿了，而扫光这一族第一次在 runner 上判到**：产品 coverage 0.522（地板 0.50）、等节拍证人 0.594、位置判据 可用帧=11 / 绝对散布 1.0pt / 判定=整组一条带（1× 像素那格也第一次被真机验证）。三遍并排 ⇒ R83 那朵 `.productRed` 有了第三种解释：**旧的 fan-out 画法让运动跨不过像素门槛**（时钟一个数都没改，0.050 → 0.522）⇒ 119 不结案但归因顺序变了。本轮改的是账：常驻循环那一族进覆盖地板（结案 **118**）—— 两条判据的两条出口各打一行状态（`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`），闸门新增 `loops` 那一层，只判两格：状态行整行缺席 ⇒ LOOP_SILENT 红、点名理由没登记 ⇒ BAD_REASON 红，点名在登记之内不红但必须打一行看得见的未覆盖；`productRed` 不在这里红（同一件事只判一次）。牙 M458–M464 七刀全 CAUGHT —— 其中 M461 / M462 第一版**双双逃掉**，因为守卫只数"这个串出现过"、被 skip 那条出口喂饱 ⇒ 改成数次数（U-174）。另外三条读数写进台账：登记名允许细节后缀（U-175）、旧夹具补不补背景行要分开决定（U-176）、读不到运动有三种成因（U-177）。**本轮零产品改动 ⇒ 不换装**（判据：帧基线 124 张逐字节不变、`Sources/` 一行没动）；`must_judge` 仍然 false：0.522 只比地板高 0.022。全量 801 tests / 0 failures（41 skipped，swift test exit 0）；动效闸门 MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=10 notice-banner-dismiss=13 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0；捕获闸门 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）；帧基线 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；脚本 Ran 143 tests in 6.717s OK；告警 0。**下一轮第一件事：读 R85 的 CI（loops 那一层第一次在 runner 上判自己）+ BACKLOG 119 / 116**）

> 上一轮（R84 / 第 86 轮收尾）原文开头：最后更新：2026-10-16 03:20（本地 · R84 / 第 86 轮收尾：读 R83 的 CI（run 38786182395，11m55s）—— **runner 那一支翻面了**：同一份产品代码，R82 证人 coverage 0.284 ⇒ 点名环境，R83 证人 0.837 ⇒ 判产品红，而产品两遍都是 0.000/0.050 ⇒ 新开 **119**（单次 runner 读数不配判产品红）。产品那一处：骨架扫光的亮带从"每根条各扫各的"改成**一条光穿过整组**（新增 `SkeletonBarsShape`，渐变落在容器坐标系；条高/条间距提成 `SkeletonMotion` 令牌），结案 **117**。同帧内三根条亮斑绝对中心 169pt → **0pt**、归一化 0.005 → **0.450**（两把尺反向才对），判据与手量两份实现同结论，before/after 条带图都在 `.scratch`。新判据 `testSkeletonSweepIsOneBand` 三道闸门（合成正对照 / 行程正对照 / 由"同一把尺读高对比证人"签的处置），真值表 13 格。路上三条红全是尺子自己的：U-165 点→像素漏乘 scale、U-166 内边距 4pt 拦不住圆角让开一格的假峰（换 10pt 是量出来的）、U-168 两把尺的估计量不同（质心 vs 峰值列）。牙：八刀：七刀 CAUGHT，一刀按实存活为"本地无独立判别力"（M454 的牙被 M454b 那格检验过）。U-169 记下处置翻面，U-170 记下电池同文件两处编辑会互相覆盖，U-171 记下那 4 张帧到底变了多少（≤5 灰阶），U-172 把那条方向性约束写进判据（会翻脸的读数只准收窄断言，不准定罪），U-173 记下第二遍验证那朵 `judged=None/None` 的假红来自本地脚本没并文件通道（修法在 harness，不在闸门）。全量 801 tests / 0 failures（41 skipped，swift test exit 0）；动效闸门 MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=13 notice-banner-dismiss=11 红的用例=- 汇总行报红=0 MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0；捕获闸门 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）；帧基线 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0；脚本 Ran 142 tests in 6.581s OK；告警 0。**下一轮第一件事：读 R84 的 CI（119 的那一支在 runner 上今天怎么说）+ BACKLOG 118**）

> 上一轮（R83 / 第 85 轮收尾）原文开头：最后更新：2026-10-16 02:20（本地 · R83 / 第 85 轮收尾：读 R82 的 CI（run 38781113064，12m11s）—— **114 落在预登记的第一支**：runner 上产品 `帧数=21 变化帧对=0 峰值=0.000`、等节拍证人 `coverage=0.284`、粗节拍证人 `coverage=1.000` ⇒ 这台机器带得动 20Hz、带不动 30Hz 那一档，处置点名 `loop-clock-not-sustainable-at-product-rate`，不判产品。同一步仍然红，而两朵红都是我上一轮自己造的：**U-160** 卷长钉子挂在 `LoopShape.recordedMilliseconds` 上（峰值 0 时被 guard 归零 ⇒ "看不见运动"被改写成"探针坏了"）⇒ 新增 `FilmPremise`，前提从时刻本身算，真值表第⑧格钉"静止一卷 premise 报 1000ms 而结论尺报 0，两者不许相同"；**U-162** 绝对峰值地板不管处置 ⇒ 只有 .ok/.productRed 才判，其余打 `MOTION_SHIMMER_PEAK_NOT_JUDGED`（减弱动态那档不豁免）；**U-161** 闸门 NAMELESS 拿失败次数减用例名个数 ⇒ 两边同为失败行数，两格回归测试一正一反。看图那一半：`r83_band_fanout.py` 把 117 量成数字 —— 同帧内三根条的亮斑中心绝对差最大 170pt、归一化只差 0.003 ⇒ **亮带每根条各扫各的**（改产品在下一轮），路上又抓到两把尺读错东西（U-163）。新开 **118**：一朵有名字的未覆盖不在覆盖地板的登记表里。牙 M446–M450 五刀：三刀本地有牙、两刀按实存活为"本地无判别力"；两把刀的期望第一版写窄了（U-149 复发）。U-164：电池的 python 臂第三次撞上同一个盲区（模块级导入失败被读成全绿）。全量 799 tests / 0 failures（40 skipped，swift test exit 0）；动效闸门 MOTION_FLOOR_FACTS judged=4/4 executed=52 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=12 notice-banner-dismiss=12 红的用例=- 汇总行报红=0 MOTION_FLOOR_REDS=0CAPTURE_TEST_EXIT=0；捕获闸门 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）；帧基线 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0PY_EXIT=0；脚本 Ran 142 tests in 6.807s OK CURVE=PHASE2 n=76、rounds=9..83、均值 92.47、最低 86、最高 96、GAPS=none、SCORES_BY_ROUND 80=93 81=93 82=94 83=94；告警 0。**下一轮第一件事：改 117（把亮带抬到容器层，带 before/after 条带图与帧基线复核）**）

> 上一轮（R82 / 第 84 轮收尾）原文开头：最后更新：2026-10-16 01:20（本地 · R82 / 第 84 轮收尾：读 R81 的 CI（run 38770024897，12m38s）—— 唯一那朵红就是 113 说的那朵，而同一遍打出的`MOTION_CONTROL 渐变端点 帧数=21 变化帧对=13` 把"一颗证人"这条路堵死了：那颗证人是 20Hz / 抬 0.45，产品是 30Hz / 抬 0.12，它当时那 13 对不足以判产品红。**113 结案**：判据换成 **coverage**（时间之比，本机三遍真值 0.955 / 0.977 / 1.000，一次跳变 0.05，地板 0.5 一动不动），证人换成两颗，等节拍那颗（30Hz、每拍 (1/30)/1.5、0.06→0.18、同一颗 VisualShape.rounded）决定红与不红，四个数写死并由新判据 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住仍等于产品。**110 的第一个实例**：分辨率闸门改吃事件内 P75（`[50 51 52 53]` 与 `[50 51 52 81]` 的 P75 相同而最大值差 28ms）。**U-155**：`probe.lastStamps` 会被后一卷覆盖 ⇒ 形状吃了别卷的时刻，而**把那句话原样写回去，四条判据全绿**（M443 第一版，v1 日志）⇒ 修法换层：探针返回 `GrabbedFilm(frames:stamps:)`，同轮再补 U-156（前提故障不许冒充"只动了一下"）与 U-157（结构等式要双向）。新开 **114**（runner 上那一档节拍带不带得动，由三行 `MOTION_SHIMMER*` 分诊）与 **115**（TableProbe 还留着同款共享时刻）。新开 **116**（同一提交的全量卷里 skip 条数自己动了：38 / 45 / 40，而那五条 `UICaptureTests` 没有一行"为什么今天没跑"的读数 ⇒ 判据有没有跑没人审计）与 **117**（给这条扫光第一次画的逐帧条带图 `r82_skeleton_sweep_strip.png` 看出：亮带落在**每根条自己的**渐变上，三根条各扫各的，不是一块光穿过整组）。U-158（电池把"崩掉的用例"与"没轮到的用例"分开命名）、U-159（一个会抖的数被写成常量）。全量 799 例 / 40 skipped / 0 failures（145.4s），动效闸门 judged=4/4 红的用例=- REDS=0，捕获闸门 CAPTURE_GATE_RESULT=ok 红=0，帧基线 COMPARED=124 CHANGED=0，脚本 140 OK，告警 0，九刀 M437–M445 **9/9 CAUGHT**。**下一轮第一件事：读 R82 的 CI 那三行 coverage，按 114 的分诊表走**）

> 上一轮（R81 / 第 83 轮收尾）原文开头：最后更新：2026-10-16 00:32（本地 · R81 / 第 83 轮收尾：读 R80 的 CI（run 38766914234）——
**109 的答案是决定性的第二支**：runner 上焦点搬动 **0.0pt²**，而同一把尺在同一格里读出撤占位字
88.9/112.3pt²、打进字 113.4/143.2pt²、同态噪声 0.0pt² ⇒ **尺不瞎**，是这台机器的 AppKit 不为非 key
窗口调淡占位符（上一轮"最多 3/4 是网格"那句被量掉了；新事实：runner 那一格的墨只有本机 1/3）。
**112 结案**：`emit` 两条腿各改成"一整行一次 write"+一把锁，`opened`→按 URL 记的 `openedURLs`；
新判据 8 线程 × 60 条 900B 长行，主断言是**行首/行尾 (t,i) 必须相等**；M434/M435 拿掉锁 ⇒
**3/3 遍 SIGSEGV**、M436 ⇒ 3/3 遍红（U-151：电池第一版把崩溃归成"编译没过"，已补第三类）。
**新开 113**：`testSkeletonSweepActuallySweeps` 在 R80 的 CI 上红（变化帧对 2<3），而 R73/R75 的
runner 读数是 `0 对 / 峰值 0.000` ⇒ 那时它**没判**；R77 把轴改成并集之后 runner 第一次看得见这个渐变，
免检变成在判 —— 这朵红是成果不是回归，判据形状要换（帧对计数 → 时间跨度/不连续段数，与 110 同族）。
全量 796 例 / 38 skip / 0 failures，124 张帧逐字节不变，捕获闸门 ok 红=0，脚本 140 OK，告警 0。
**下一轮第一件事：修 113（main 上这朵红只许活一轮），第二件事才是 110 的第一个实例**）

> 上一轮（R80 / 第 82 轮收尾）原文开头：最后更新：2026-10-16 00:10（本地 · R80 / 第 82 轮收尾：读 R79 的 CI —— runner 上**存在性闸门是开的**
（`占位整条宽=87.0pt`）而两态差读 0 个像素 ⇒ 命中 109 预登记的第二分支：**那四条红是真的**。
按预登记的处置办：没抬地板，换了尺 —— `变化像素 ≥500` ⇒ `搬动的墨 ≥40pt² + 占比 ≥8%`（合成夹具证明旧尺按缩放²变：
2000 vs 8000 个像素，"本机 1797 / runner 0" 里最多 3/4 是网格），并加三条证人臂把"看不见"分成
『这台机器不调淡』与『这一格对这把尺失明』两支，各带名字、2× 上两支都红；两支 1× 才走得到 ⇒ 提成纯函数 + 8 格真值表。
三条更正：放大镜不存在（U-146，臂 D 之后带内墨 0.0pt² + 看图）、④被 continue 跳过而注释说照判（U-147）、
守卫反过来误伤驼峰写法 `deltaAlpha`（U-138 的反面 ⇒ 改成大小写不敏感 + 正对照 I）、一条红把后面 12 步整批吞掉（U-148）。新开 111（runner 上赎回这条轴）与 112（读数通道缝行）。
M423–M433 十一刀 11/11 CAUGHT（M430 第一次是**我的期望错**，U-149）。全量 795 例 / 38 skip / 0 failures，
124 张帧逐字节不变，脚本 140 OK，告警 0。**下一轮第一件事：读 R80 的 CI —— runner 那一遍的
`QUICKPICK_FOCUS_INK` 落在三支里的哪一支，决定 109/111 的下一步**；第二件事才是 BACKLOG 110）

> 上一轮（R79 / 第 81 轮收尾）原文开头：读 R78 的 CI 发现**那道存在性闸门没拦住** —— 放大镜一个人就凑够 20 个有墨像素（U-143）。闸门换成两根独立证人：带内有墨包围盒宽度 ≥40pt（图标 17.0pt vs 图标+占位字 86.5/87.0pt）+ "只有占位字能待的那一块"有墨 ≥20（本机 675/767），并加一条"只框图标必须过不了闸门"的对照（D-137 / M419–M422 四刀全 CAUGHT）。新开 110 未动（被 109 插队）。全量 793 例 / 40 skip / 0 failures，124 张帧逐字节不变。**下一轮第一件事：读 R79 的 CI —— runner 上 `文字独占区有墨=…` 与 `宽=…pt` 决定 109 的答案**）

## 当前状态（2026-10-13 · 视觉与动效长跑 R1）

用户新开一轮长跑：把视觉与动效做到"Apple 原生、流畅、华丽但克制、细节相当丰富"，
每轮出可编译代码 + 自评，**连续五轮 ≥90 且无 P0/P1 回归才停**；轮次现场记在
**`AGENT_VISUAL_ITERATION.md`**（设计令牌表 + 每轮已完成/未完成/风险/下一轮）。

- **R1 做完的事**：R0 审计数出的 6 种圆角 / 3 种发丝线 / 4 处投影 / 3 档悬停底色 / 4 处材质字面量
  全部收进新的 `Utilities/VisualTokens.swift`，并把"只有一个作者"做成 11 条会红的判据
  （出现字面量、令牌没人读、死表面、强度次序反转都打红）。顺带删掉两个死表面
  `GlassCircleButton`（连带三个永远只剩一种取值的参数）与 `HistoryRow`（注释的复用理由是假的），
  并把"正在加载预览…"从 12pt 接回自家规范的 13pt。决定见 **D-058**，视觉账见 **U-22**。
- **数字（本轮现场）**：`swift build` 0 warning；`swift test` **600 / 23 skipped / 0 failures**
  （HEAD 同口径 589 ⇒ 本轮 +11）；`scripts/tests` 72 passed；
  82 帧采齐、**28 帧有变化且逐帧归因**（最大通道差 1/2–8 的是描边与缩略图角，
  唯一的大差 124–127 是那句加载文案 12→13，bbox 86×12.5pt = 一行字；`glass-pill-*` 像素不变），
  基线 `FRAME_BASELINE_UPDATED=82` 与改动同提交、复跑 `CHANGED=0`；
  **10 支变异体 10/10 CAUGHT**（含一次"0 支有效"的自证修复：python3 注入的 `SDKROOT` 让每个变异体都编不过，
  分类器全判 `DID-NOT-RUN`，见 D-058）。
- **动效那一步本轮不算绿也不算红**：三臂交替（R1 → HEAD → R1）在同一台机器上给出三套不同的红集合，
  HEAD 那臂比 R1 更差 ⇒ 判据在测采样率而不是测动画。**没有为了绿去调阈值**；
  "把动效判据与采样率解耦"立项为下一轮主题（BACKLOG 快照第 6 条），它要带自己的变异对照。
- **自评**：80 / 100（<90 ⇒ 按规矩继续，不等确认）。扣分全部扣在同一事实上：本轮是地基
  （收口 + 减法 + 判据），可见的"华丽与细节丰富"还没增长 —— 按压态 / 焦点态 / 边缘高光 /
  内容类型层次 / 滚动层次都还没动。分数明细见 `AGENT_VISUAL_ITERATION.md` 的 R1 打分表。
- **未推送 / 未部署**：本轮改动提交后推送；**装到本机**按 D-057 那条默认动作做（几何变了，值得亲眼看一次）。

## 当前状态（2026-10-13 · 视觉迭代 R2：动效判据与采样率解耦）

- **本轮不碰外观**：82 帧 `CHANGED=0`（视觉完全惰性），改的全在 `MotionFilmstripTests` + CI 汇报行。
- **为什么先做这个**：R1 收尾时动效套件是红的，三臂交替（R1 全绿 → HEAD 两条红 → R1 另一条红）
  证明红来自尺子。"用绝对帧数表达判据，其实判的是采样率"（ab7a759 早就写下），
  而底座是"绿不表示验到了"时继续做九轮美化，等于写在沙子上。
- **改了什么**：要求帧数 = `min(3, floor(声明时长 / 实测采样间隔))`、地板 2 帧、切不出就报
  `clock-too-coarse`；取样锚点从预卷改到**触发那一帧**；"落定"从 `≤6 帧` 改成毫秒；
  新增前提检查"触发前后必须逐像素不同"；CI 结论行加 `MOTION_RESOLVE_SUMMARY judged=n/m`（自检 13→14 形状）。
- **修尺子修出来的假证据**：`MOTION_SUMMARY notice-banner=3` 原来被当成"横幅淡入量到了"。
  实测那一卷整窗逐帧差距 `[0.000, 0.222, 0.222, 0.067, 0.000 …]` —— 首尾相同、中段变了又回来，
  而模型里提示条一直在 ⇒ **离屏 `cacheDisplay` 抓不到落定之后的横幅**。
  现在如实报 `premise-not-visible`（本机 judged=2/3）。覆盖面退一步，可信度进一步。
- **数字**：605 tests / 23 skipped / 0 failures（R1 后 600，+5）；动效套件 18 条 0 failures / 3 skipped
  （每条带 not-run 原因）；**8 支变异 8/8 CAUGHT**（含前提恒真/恒假两支）；`scripts/tests` 全绿；产品代码零改动。
- **自评 85 / 100**（分数低在"界面上没有新细节"，换回来的是后面每一轮动效分数的可信度）。
- **下一轮（R3）**：排版与间距节奏 —— 10 档字号收成一族、空态两套统一、9pt 徽标复量对比度。

## 当前状态（2026-10-13 · 视觉迭代 R3：字号刻度与层级修正）

- **改了什么**：文本字号从 8 档收成 4 档（`meta 11 · row 12 · body 13 · title 14`）+ 8 个具名符号档；
  修掉侧栏"15 条记录"比标题还大一号的**层级倒置**、把 9pt 的"固定"徽标抬到 10 并写成全 App 下限；
  `body` 改为引用 `StatePresentation.messageFontSize`（不再抄数字）。
- **数字**：607 tests / 23 skipped / 0 failures（+2 条判据）；**20/82 帧变化并逐组归因**
  （`row-pinned-on` 只有已固定那一版变、`detail-*` 与 `glass-pill-*` 完全没变），基线已同提交更新；
  **5 支变异 5/5 CAUGHT**（第一轮 2 支 ESCAPED，据此修掉两条假守卫：按名字查消费者会被
  `controlHover` 这类前缀白拿；数值断言证明不了来源，13 就等于 13）；`scripts/tests` 全绿。
- **自评 88 / 100**（<90 ⇒ 继续）。R2 的 CI 已确认 success。
## 当前状态（2026-10-13 · 视觉迭代 R4：按压态）

- **改了什么**：新增 `Views/PressableStyle.swift`（`PressedStyle: ButtonStyle` + `PressableAppearance` 纯函数），
  9 处按钮接上"缩放 0.97 + 底色 0.12 / 0.12s"的按压反馈；整行类不缩放只加深底色；
  菜单栏两处刻意不接（系统菜单自己的高亮就是反馈，理由在代码旁边 + 白名单判据）；
  新增 `MotionCatalog.pressScale` 与 `VisualFill.pressed`，次序 `hover < pressed < selected` 有判据。
- **焦点那一半没做**：读码发现搜索框的 `focusRingType = .default` 早就恢复了（R2-02），再画就是两圈；
  剩下的缺口（筛选段/设置行的键盘焦点）要先量 `List` 行代理，单独一轮。
- **数字**：613 tests / 24 skipped / 0 failures（+6 条判据）；0 warning；**82 帧 `CHANGED=0`**；
  5 支变异 5/5 CAUGHT（第一版 1 支 ESCAPED：像素断言把缩放与底色混在一起量，拆成分通道才打红）；
  `scripts/tests` 72 passed。
- **自评 90 / 100**（第一轮达到阈值线，但**这一分不敢给满**：按压态只有源码级与合成级证据）。
- **按压态的产物级证据仍缺**：真按下探针在 xctest 里 `送达=0`、`keyWindow=nil isActive=false`
  ⇒ SwiftUI Button 的按下跟踪要 key 窗口。已如实记为"源码已接、产物未量"，转人工批次 12.1–12.7。
- **已装到本机**（R1–R4 一起进去）：`install_local.sh --yes` 跑通 —— `INSTALL_RESULT=ok`、
  `INSTALL_SHA_MATCH=1`（staged 与 installed 都是 `ea29552ee41f0624…`）、新 pid 19048 的 exe
  逐字对上 `/Applications/时间剪史.app`、存档 92→92 条、运行时冒烟 `SMOKE_OK=1`；
  旧包留在 `~/Documents/Codex_Project0_backups/before-local-20261013-045123`。
  **请按批次 12 判手感**（尤其 12.1 按住收藏键、12.6 开减弱动态再来一遍）。

- **下一轮（R4）**：按压态与焦点态（全 App 现在只有 hover 一种反馈；`testSidebarListFocusRingAfterClick`
  那条已知红也在那一轮处理），并把间距节奏（padding 一族）一并收。


## 历史状态（2026-10-12 晚 · 动效补做批次）

- **HEAD**：`6fc8224`，工作树干净，全部已推送；CI 对最后一个代码提交 `155de63` 是绿的。
- **已交付到本机**（D-057）：`install_local.sh --yes` 跑通并正在运行新构建
  （pid 75839、exe 逐字对上 `/Applications/时间剪史.app`、`INSTALL_SHA_MATCH=1`、存档 92→92 条，
  旧包留在 `~/Documents/Codex_Project0_backups/before-motion-batch9/`）。
  注意版本号字符串仍是 **1.4.8**（`Makefile VERSION` 要到发版时才抬，CHANGELOG 里这批挂在 `[Unreleased]`）——
  所以"看版本号判断装没装上"是无效的，要按上面的 exe/sha/pid 认。
- **这一批做完的事**：用户反馈"新版本没加什么动画"→ 重读报告找回四条被我判错的条目
  （QuickPick 原生行动画 / 收藏固定的 `replace`+`bounce` 叠加 / M9 骨架扫光 / M8 落点光晕），
  两条主动撤下并写明理由（`reduce-transparency` 门、"跳转才动"的滚动策略）。
  决定见 **D-056**，视觉账见 **U-21**，报告见 **§20**，人工验收见手工清单**批次 9**。
- **数字**：588 tests / 22 skipped / 0 failures；两个 triple 各 0 warning；
  82 帧 `CHANGED=0`（2 帧是这次刻意改的加载态，基线已随包更新）；26 条新判据（22 纯值/守卫 + 4 像素）；本机像素套件 13 条全绿；
  16 支变异 15 支红在该红的那条 + 1 支故意逃逸（据此删了一条死守卫）。
  像素证据：QuickPick 行动画 开 11 帧 / 关 1 帧、产品形状（插完行紧接着写选中）11 帧 vs 1 帧 —— 这两条**带前提**：`NSTableView` 只在激活的 App 里跑行动画，裸测试进程拿不到激活态时判据自己报 `MOTION_NOT_RUN=app-not-active` 并 skip（本机当前就是这个状态；CI 那台 runner 拿到了：3 帧 vs 1 帧）；骨架扫 23 对在变 / 减弱动态 0 对。
  CI 的动效那一步补了两行固定输出（各条读数 + 红用例名字，由 motion/failing_test_names 形状钉住）；三条新像素判据在 runner 看不见位移时改报 MOTION_NOT_RUN + skip，而不是红。
- **两条已知红（都不是这批造成的，也都记着）**：帧间隔判据 `p95=28.68ms` 超 20ms
  （同一次运行里"曲线全关"那臂 27.67ms ⇒ 环境）；
  `testSidebarListFocusRingAfterClick` 找不到行代理（在整轮动效之前的提交上同样红，
  现场是一行变成两个半宽 `KeyViewProxy`，疑无障碍结构退化，BACKLOG 快照 33 第 5 条）。
- **下一步该做的**：装包做批次 9 的 8 条人工验收（尤其 9.4 符号动效、9.5 扫光观感）；
  机器安静时复测帧间隔；单独一轮查行代理分裂。

**仓库位置（2026-10-09 起）**：`/Users/wangziyi/Codex_Project0`。
原先在 `~/Documents/Codex_Project0`，那在 iCloud「桌面与文稿」同步范围内（`CloudDocs/Documents` 是指向 `~/Documents` 的符号链接，
`bird` 在跑），同步会在仓库里留下 `名字 2.扩展名` 的重复副本 —— 本次就出现 29 个，SwiftPM 把 `Sources/` 下的类型编译两遍，构建直接崩，
第一次发布准备因此失败。旧路径现在是一个指向新位置的**符号链接**（保住旧书签/旧会话路径），确认无误后可以删掉它。
搬离时实测：跨出同步边界的 `mv` 会 `Operation timed out`（File Provider 需要先物化），要用 `rsync -a` 复制 + 校验 + 再删源。
分支：`fix/audit-remediation` 已删除（本地与远端；其提交全部在 `main` 上，删除前用 `git log main..分支` 验过为 0）
回滚基线：提交 `8007b19` "Checkpoint: 1.4.5 working state before audit remediation" —— 修复前工作区的全部 WIP（含此前未被 git 跟踪的 `Intelligence/` 等 25 个路径）已入该提交。**任何一步都可以 `git revert` 或 `git diff 8007b19..HEAD` 审查。**

## 权限与边界（本轮）

- 工作区内可读写增删；允许 git 写操作（不 push，不 `--force`，不改 config，不跳过钩子）。
- 禁止：伪造验证、删测试或改断言来"绕过"、把工作区外的破坏性操作当副作用。
- 数据/接口/依赖/架构变更必须兼容、可迁移、可回滚、有记录 → 一律写进 `AGENT_DECISIONS.md`。
- **用户真实数据保护（重要）**：`~/Library/Application Support/时间剪史/` 是用户真实剪贴板历史。在 A-3（损坏存档 + 一次复制即全量删除）修复之前，**不得**以默认数据目录启动真实 App；所有验证都用临时目录或环境变量重定向。

## 基线数字（已实测，作为改进的对照）

| 指标 | 基线 | 命令 |
|---|---|---|
| `swift build` | OK，5.81s（含 1 条编译告警） | `cd ClipboardHistory && swift build` |
| `swift test` | **退出码 1**，`passed=3 started=4`，1 次 `Fatal error` | `swift test > /tmp/baseline-test.log 2>&1; echo $?` |
| 用例总数（源码计数） | 135 个 `func test` / 23 文件 | `grep -c "func test" Tests/**/*.swift` |
| `scripts/tests` | OK，11 tests（Python 3.9.6） | `python3 -m unittest discover -s scripts/tests` |
| 一次 `save()`（12 张 1600×1200） | **667.8ms 主线程** | 审计探针 P-12 |
| 启动 `load()`（8 张 2000×1500） | **605.8ms 主线程** | 审计探针 P-14 |
| `filteredEntries`（500 条 ×1KB + 搜索词） | **14.07ms/次** | 审计探针 P-20 |
| Gatekeeper | `spctl -a -t execute` → rejected（ad-hoc，无 entitlements） | 见审计 06 附 6.2(3) |

## 执行顺序（按价值，见 AGENT_BACKLOG.md 的分数）

第一批（S1，数据/信任/闸）：R-01 调试开关与日志位置 → R-02 损坏存档保护 → R-03 菜单无确认清空 → R-04 Web URL 误判 → R-05 来源 App 丢失 → R-06 反馈载荷含原文。
第二批（性能，实测驱动）：R-07 PNG 字节缓存 + 保存去抖 → R-08 图片指纹去绘制 → R-09 派生列表缓存 → R-10 预览文案先截断 → R-11 预测改事件驱动。
第三批（契约与可观测）：R-12 README/安装说明与行为对齐 → R-13 Info.plist 用途描述 + 授权失败可见 → R-14 死代码清理 → R-15 构建脚本与版本单一来源。
第四批（UI 视觉审计与修复）：U-01..U-0n，方法见 `AGENT_UI_AUDIT.md`（离屏渲染真实视图取像素，不依赖屏幕录制授权）。
第五批（矩阵新维度补审计）：边界/错误/内存/兼容/可访问性/国际化/可观测性/类型/迁移/回滚 逐格填平，`待审` 必须归零。

## 已完成（每项 = 提交号 + 验证方式）

| 项 | 提交 | 验证结果 |
|---|---|---|
| R-01 调试日志门控 + 移出 /tmp（顺带恢复测试闸） | `cb8db30` | `swift test` 退出码 0，**Executed 135→146→176** 用例全绿；`/tmp` 两个日志不再新增；`DebugLoggingTests` 7 条守卫 |
| R-02 存档损坏恢复 + 滚动备份 + 原件保全 | `0792e6b` | 4 条 `HistoryPersistenceRecoveryTests`；变异检查：去掉修复即报 "P-06 修复验证：图片文件不得被连带删除" |
| R-03/R-04/R-05 菜单确认、Web URL 误判、来源 App 归因 | `cc0c2df` | 3 组新测试；各自变异回旧实现即复现缺陷 |
| R-06 反馈不再存正文 + 级联清理 + 导出失败可见 | `0792e6b` | `FeedbackStorageHygieneTests` 7 条；实测用户 plist 该键 66,716,424 字节会被收窄 |
| R-48 推荐排序确定性 | `f17fc86`/`f8ce4dd` | `RecommendationDeterminismTests` 4 条；两处变异各自可复现地变红 |
| R-07/R-09/R-10 主线程热点（保存/派生列表/预览文案） | `f8ce4dd` | `PerfBudgetTests`：667.8→5.2ms、14.07→0.00ms/次、45.8→0.02ms |
| R-11/R-17/R-18/R-19/R-21 事件驱动预测 + 语义收敛 | `cb3a69b` | `PredictionSchedulingTests`（含代际丢弃）；静置不再 2s 轮询 |
| R-22/R-40/R-41/R-42/R-43 上限、拖选表、视频错误态、观察者释放、菜单脱敏 | `50e5a4e` | `DisplayPrivacyAndCapsTests` 等；离屏帧复验 |
| 第四批 · 视觉审计链路与 3 个真实缺陷 | `95b4301` | 离屏捕获 54 帧；修：设置侧栏图标隐形、破坏性按钮重复、5 处信息文字 `.tertiary`（暗色 2.2:1 → 5.79:1，亮色 1.89 → 3.98） |
| R-13 自动粘贴失败可见 + 存档恢复提示上屏 | `654a787` | `PasteFailureVisibilityTests` 7 条；变异（把上报改成空函数）⇒ 以正确原因变红；离屏帧确认横幅不破坏布局 |
| R-12/R-15/R-34 README 三条虚承诺、Info.plist 模板化、DMG 新鲜度与校验 | `1d442f5`,`fd59dbb` | `make dmg` 全链路跑通：通用二进制 + 16 键 Info.plist（含 `NSAppleEventsUsageDescription`）+ `.sha256`；挂载 DMG 复核内部产物；`scripts/tests` 17 条（新增 6 条，含"缺键必须构建失败"与"mtime 未变必须拒发"，两条都做过变异验证） |
| R-23 OCR 像素解码移出主线程 + R-08 残留的图片比较成本 | `4324441` | 实测 `add(3000x2000)` 主线程 94ms → 0.04~0.77ms；冷 `==` 4000x3000 217ms → 148ms（同字节重复 0.17ms）；`PerfBudgetTests` 那条**恒绿假守卫**（计时对象根本没算指纹）已重写 |

当前基线（复跑命令见下方恢复指令；本轮结束时的最终复跑见 AGENT_FINAL_REPORT.md）：

| 指标 | 现在 |
|---|---|
| `swift build`（清空 .build 后干净重建） | OK，**0 告警** |
| `swift test` | 退出码 0，**Executed 229 tests, 1 test skipped, 0 failures**（2026-10-09 在新路径复跑核实；现取方法：`swift test > /tmp/test.log 2>&1; rc=$?; grep -E 'Executed [0-9]+ tests' /tmp/test.log | tail -1`（`tail -1` 单独用会取到 swift-testing 那行 `Test run with 0 tests`，看着像"一条都没跑"），别信这里写的数字）；那个 skip 是离屏视觉套件，按设计只在设了 `CLIPBOARD_HISTORY_UI_SHOTS` 时跑 |
| `python3 -m unittest discover -s scripts/tests` | OK，**18 tests**（必须在**仓库根目录**跑；`ClipboardHistory/` 下没有 `scripts/tests`，在那里跑以退出码 1 报 `Start directory is not importable`） |
| `make build` / `make bundle` / `make dmg` | 全部退出码 0；DMG 挂载后复核：通用二进制（x86_64 + arm64）、`codesign --verify --deep --strict` 通过、Info.plist 16 键含 `NSAppleEventsUsageDescription`、`.sha256` 可校验且改一个字节就失败 |
| 离屏视觉捕获 | 64 帧（32 夹具 × 亮/暗；第二轮末加了菜单栏面板的三个状态），未绘制比例全部 <95%，同代码连拍 sha 完全一致 |
| 审计矩阵 | 190/190 格全部判定完毕，**待审 0** |
| Backlog | 54 行，**待办 0**（其余为 已完成(提交号) / 记录不改(理由)） |
| 工作区 | `git status` 干净；**已推送并核对，Latest = v1.4.7**（v1.4.6 保留；CI 在发布提交与之后的账本提交上都全绿）。当日一度因 GitHub 不可达而落后，网络恢复后推上去了，并用 API 核对：远端 `main` == 本地 `main`、`v1.4.6→e4ac62b`、`v1.4.7→5190ad1`，两个 Release 附件的 sha256 与本地 `.dmg.sha256` 逐字相同。核对命令写在文末"恢复指令"第 6 条（别信这里写的 SHA，跑一遍现取） |

本轮新发现（原审计未覆盖，已进 backlog）：
- **R-49** `ClipboardIntake` 各读取方法的 `from:` 默认 `.general` ⇒ 注入的 pasteboard 被静默忽略，测试会读到**用户真实剪贴板内容**。已修（R-05 同批），断言改成"只报类型不报正文"。
- **R-48** 推荐排序跨启动不稳定。已修。
- **R-50** `HistoryStoreTests` 排序断言依赖前台 App。已修。
- **R-51** 图片去重仍要"同尺寸不同内容"时两侧各解一帧（148ms/次，主线程）。已比旧实现快 2.9×，残留部分记为待办：把 64px 采样值随条目一起持久化即可彻底摘掉。
- **守卫本身的失效模式**（方法级发现）：`PerfBudgetTests` 的指纹用例计时的是"构造"而不是"比较"，惰性缓存令它永远 0.00ms —— 已重写，并把"每类比较用各自第一次被比较的对象"写进注释。同类问题也出现在视觉捕获上（4 类假帧，见 `AGENT_UI_AUDIT.md`）。
- **实测确认 R-06 的现实规模**：`~/Library/Preferences/com.clipboardhistory.app.plist` = 66,724,574 字节，其中反馈键 66,716,424 字节。

## 恢复指令（若上下文丢失，从这里续做）

## 第二轮审计（2026-10-09）· 修复进度

审计交付在仓库外：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-09_第二轮/`
（`00-README` / `01-增量台账`（15 模块 × 9 维度 = 135 格全覆盖）/ `02-新缺陷与回归` / `03-UI与HIG视觉审查` / `04-验证附录` + `frames/` + `probes/`），
被审对象是 HEAD `81bce8d`（v1.4.7，工作区干净）。它的结论：修复轮质量高于平均，但自己留下 4 条新缺陷（N-1…N-4，其中 2 条是"为修 A 引入 B"），
UI 侧暗色与 60fps 达标、**键盘可达性实测不达标**、亮色 chrome 不可见、拖拽能力为零。

本轮已完成（每条一个提交；提交后 `swift build` 0 告警、`swift test` **229 例 / 1 skip / 0 失败**）：

| 审计项 | 提交 | 做了什么 |
|---|---|---|
| N-1（S2 崩溃） | `876c015` | `intelligenceByEntryID` 两个重载不再用 `Dictionary(uniqueKeysWithValues:)`（重复键 = `fatalError`），改为保留首条 |
| N-2（S2 数据丢失） | `bacde44` | `HistoryStore.init` 不再写盘，首次写回推迟到 `startMonitoring`（守卫已放行）；3 条原"init 即持久化"的用例保留全部断言并新增"init 阶段零写入" |
| N-3（S4） | `fb37c4b` | `load()` 开头复位 `isArchiveFromNewerVersion` |
| N-4（S4 假绿） | `a56f2e5` | `guard … else { return }` 换成钉住两侧的断言；**顺带暴露一个真行为**：只含非文件 `NSURL` 的剪贴板当前不被记录（`readFileURLs` 限定 `.urlReadingFileURLsOnly`，是 P-15 的修法） |

本轮**还欠**（明细见 `AGENT_BACKLOG.md` 的 R2-* 条目，按价值排序）：

1. **N-1 的端到端守卫还没写** —— 审计明确要求"走 `HistoryStore`、不走 engine"的用例（存档含同 id 两条 ⇒ 预测刷新不崩且只出一条）。
   现在只有实现改动，`RecommendationBoundaryTests:96-103` 仍然绕过 adapter ⇒ **这条修复还没有一条会红的测试**，
   必须补上并用变异对照（把实现改回 `uniqueKeysWithValues`）证明它真的会红。这是本轮第一优先。
2. B-1…B-6（保存仍重写全部图片文件、来源 App 不落盘、`sizeDescription` 全串计数、图片无像素上限、过期项文档、粘贴前不复核目标 App）。
3. UI 批次 A/B/C：亮色 chrome 9 处 `.white.opacity`、`"questionable"` 非法符号、破坏性确认的默认按钮、减少动态未门控、
   **键盘焦点链**（审计实测 14 次 Tab 全落在同一个 `NSTextView`）、拖拽缺失。
4. 一个待决策的产品问题：只含 `public.url` 的剪贴板要不要记成文本条目（现在是丢弃；浏览器复制链接同时带字符串，所以日常不受影响）。

子代理调研结论（只读，已采纳）：**不要**把自绘列表整体换成 `List(selection:)` —— `.draggable` 是 macOS 13+ 而本项目下限是 macOS 12，
`List` 的系统 chrome 会改掉 4 个 `sidebar-*` 帧的像素，还会丢掉 `dragSelectRange` 的锚点语义（只有 store 级测试钉着）。
改走最小方案：恢复搜索框焦点环、行 `focusable` + `onMoveCommand` 方向键映射到既有 store 动作、行上暴露 `isSelected` 语义；
拖出条目用 `onDrag { NSItemProvider }`（macOS 10.15+ 可用），不是 `.draggable`。

### 第二轮进度快照（本节为最新状态，上面那份"还欠"清单写于开工时）

已完成并推送（每条一个提交，全部有会红的测试；`swift build` 0 告警、`swift test` **265 例 / 5 skip / 0 失败**、`python3 -m unittest discover -s scripts/tests` **25 例 OK**）：

| 审计项 | 提交 | 证据 |
|---|---|---|
| N-1 端到端守卫（R2-01） | `ca12531` | 变异对照：改回 `uniqueKeysWithValues` ⇒ 测试进程 `Fatal error: Duplicate values for key`，退出码 1；随后按 sha 逐字节还原 |
| R2-09 非法符号 / 菜单空态 / spinner 兜底 | `1214526` | 新增 `SystemSymbolValidityTests`：扫出 **24 个符号名字面量 / 22 个不同名**，全部可解析；识别器用含 `questionable` 的合成源自证；数量下限 18 由 grep 独立得出 |
| R2-03 亮色 chrome（9 处） | `6a2c040` | `scripts/frame_audit.py`：亮色 pill 的 chrome 从 245–250（背景 247，≤3 级差 = 不可见）变成 202–207（43 级差）；暗色 81→64（背景 34，仍高 30 级） |
| R2-06 破坏性确认默认按钮 | `a841337` | `DestructiveAlertLayoutTests` 2 条钉住按钮顺序/角色/快捷键与 `runModal` 返回值映射 |
| R2-10 pill 减少动态门控 | `2438aa6` | `FilterPillMotionTests` 3 条（含接线守卫：视图里不许再出现写死的 `.spring(response: 0.38`） |
| R2-11 有界字符计数 | `8cfdfe5` | 2.4MB 文本 `sizeDescription` 实测 **0.87–1.11ms**（旧实现基线 5.5ms），性能上界从 20ms 收回 **5ms** |
| R2-04 保存不再重写全部图片 | `9ac4661` | `ImageWriteAmortizationTests` 4 条，判据是 inode（原子写必换 inode）+ "history.json 必须每次换 inode" 的阳性对照；变异对照：去掉跳过 ⇒ 2 条红 |
| R2-07 来源 App 落盘（D-016） | `d8d11f4` | 4 条用例（文本/图片/文件往返、手写旧存档仍可读且读成 nil、隐私文案披露）；变异对照：四处写 nil ⇒ 2 条红 |
| R2-02 键盘可达性（部分） | `d4edf1f` | 在屏探针实测：真实 Tab 按键现在能到搜索框（`NSTextView(fieldEditor)`）；改动前 14 次 Tab 全停在详情的 `NSTextView` |

顺手修掉的一个**测试环境依赖**（`fe4ca27`）：`InstanceGuardTests` 有一条断言"本机没有产品 bundle id 的其他进程"，
用户一打开 `/Applications/时间剪史.app` 它就红（本轮实测 pid 75412）—— 那是在断言机器状态而不是代码行为。
现在改成按测试进程自己的 bundle id 判定，本机因为 xctest 不是 GUI App 而 skip；**Finder 那个阳性对照单独成一条用例**，
否则一个 skip 会把它一起染成"没跑过"。

新工具：`scripts/frame_audit.py`（`diff` / `stats` / `band`，纯标准库解 PNG，自带 7 条单测；它自己抓到一个真 bug ——
亮度用截断而非四舍五入会把纯白算成 254）。捕获 harness 也修了一处证据污染源：**闪烁的插入点**曾让同一份代码连拍两次
有 30/58 帧不同（最大通道差 251），现在捕获前交出第一响应者并把插入点设为透明，噪声降到 16/58 且只剩 `content-*`/`detail-*`。

**验证等级要分清**（本轮明确记为未验证的）：Tab 能否走到列表行 —— 本机 `AppleKeyboardUIMode` 读出来是 `-1`（缺省，
即「完全键盘访问」关闭），此时 macOS 的 Tab 只在文本框与列表之间走，`.focusable()` 的自绘视图根本不进环；
所以"键盘用户能用方向键浏览列表"目前只有**纯函数单测 + 接线守卫**，没有在屏证据，需要人工开一次该开关后用
`CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests` 复测。
同理未验证：`NSAlert` 的真实按键行为（Return/Escape）、真实拖放（拖出已实现并有单测，但需要鼠标拖拽与接收方 App，离屏测不了）。
菜单栏面板视觉在 D-019 加了注入接缝之后**仍然** NOT-RUN，理由更新为"离屏 `cacheDisplay` 不画菜单表面材质，试拍帧 97.7% 未绘制，被捕获闸门判为无效证据"。

### 第二轮进度快照 2（收尾时；上面那张表仍有效，这里是增量）

| 审计项 | 提交 | 证据 |
|---|---|---|
| R2-05 拖出条目 | `d463ef9` | 7 条用例（含把 PNG 字节从 provider 里读回来比对）；多文件条目刻意不给拖拽（半截动作比没有更糟）；真机拖放未验证 |
| R2-08 图片 4096px 上限 | `1183f9f` | D-017；端到端采集用例断言入库 ≤4096 且字节数严格变小；4K（3840）逐字节不动；变异对照红过并还原 |
| R2-12 粘贴前复核目标 App | `d218803` | 6 条真值表 + "复核必须在注入之前"的顺序守卫；变异对照（延时直接注入）红过并还原 |
| R2-13 行时间戳 11pt | `d218803` | 帧差异 3.3–13.1% vs 同代码对照 0.12–0.38%；肉眼核对未裁切；**差异里混着夹具时钟字符串变化（R2-19）** |

当前判据：`swift build` 0 告警 · `swift test` **301 例 / 5 skip / 0 失败** · `python3 -m unittest discover -s scripts/tests` **25 例 OK** ·
远端 `main` 与本地一致 · CI 最近三次（`d0b2416`/`a22d394`/`268ccaa`）全 success；再往后的以 `gh run list --limit 3` 现取。
本轮之后又加了：菜单内容直测 + "还在算/确实没有"的区分（D-021）、拖入文件入库（D-022）。
本轮 CI 一共红过五次，根因全都是同一类：**把本机测出来的数字写进断言**。分别是
`@MainActor` 测试类的 setUp 写隔离属性（6.1.2 更严）、把本机 2× 渲染倍率当契约、
"热比较快于冷比较"这条在 2 核 runner 上没有分辨力的计时判据、搜索词代价取均值，
以及"离屏列表能数出 5 行"（runner 只数出 4 行，`e8a59e4` 改成量整列墨水）。
五次都是**本地绿、远端红**，所以"本机全绿"在本项目里从来不算交付证据。
第四次的修法顺手否证了我自己给它的修法：先加的 load1/核数闸门，实测 CI 是 `load1=11.8 活跃核=3`（比值 3.9），
会把 5 条性能守卫在唯一的自动化环境里全部变成 skip —— 改用"样本自身跨度 > 该条阈值才 skip"，阈值一个没动（D-023）。

**CI 红过两次，都是同一类错**（`1183f9f`/`d218803`）：`testPixelDimensionsReadsARealPNG` 把本机的 2× 渲染倍率当成了契约，
CI runner 是 1×，"编码后严格大于点尺寸"立刻红。已在 `d160b52` 改成与倍率无关的不变量（与 `NSImage` 自己的位图表示一致）。
教训记在 `~/.qoder-cn/memory/feedback-probe-and-assertion-hygiene.md`：**本机实测的数字进断言前，先问别的机器上它还是不是这个数**。

仍未做（明细与理由在 `AGENT_BACKLOG.md` 的 R2-* 与"进度快照 3"）：R2-02 的在屏复测（需人工开「完全键盘访问」）、
设置侧栏符号风格统一（离屏证据不可信，标 NOT-RUN）、菜单栏面板视觉（等 D-019 的接缝走在屏探针）、
多文件条目的拖出（需要 NSView 级 dragging session）。
本轮**证伪**的一条审计结论：R2-15 说 AI 脚手架"零产品调用"，实际 `AIPrivacyScope`/`AIPrivacySensitivity` 被 4 个产品文件使用，
整体搬走编译失败；最终按编译器给的事实拆成"词汇表 target + 草案 target"（D-020）。

### 第二轮进度快照 3（同夜最后两件：性能判据的自我推翻 + 菜单栏面板补拍）

- CI 第四次红（搜索词代价均值 69.0ms vs 上界 60ms）后我先加的 load1 闸门**是错的**：CI 实测 `load1=11.8/3 核`，
  比值 3.9 ⇒ 5 条性能守卫会在唯一的自动化环境里永久 skip。已改成"N 次同操作采样取最快 + 跨度 > 该条阈值才 skip"，
  阈值一个没动，双向变异对照都实跑（D-023）。**已核**：`c952905` 的 CI 上 runner 是 `load1=27.7/3 核`，
  8 条 `PERF[...]` 全部下结论、零 skip。
- 菜单栏面板从"从未画出一帧"变成 6 帧（有推荐 / 还在整理 / 暂无推荐 × 亮暗，58 → 64）：
  以前那句"离屏拍不到"只对 macOS 12 的 NSMenu 成立，13+ 的 `MenuBarExtra` body 是普通 View（D-024）。
  第一次看画面就抓到"来源 App 在一行里说两遍"，`16d658d` 修掉。
- **已发布 v1.4.8**（2026-10-10，用户授权）：轻量 tag `v1.4.8` 打在发布准备提交 `e4aee3c`，线上 Latest 已切换。
  产物级验证与"仍欠运行时冒烟"都记在 D-031 与 `AGENT_FINAL_REPORT.md` §11。
- 当前判据（发布提交上实测）：`swift build` 0 告警 · `swift test` **328 例 / 9 skip / 0 失败** ·
  发布脚本测试 **30 例 OK**（`python3 -m unittest discover -s scripts/tests`）·
  68 帧同代码连拍两次 sha 完全一致。
  **已确认**：`14a37a0`（录制器修复）与账本提交在 CI 上 success（run 37927639110），
  远端 `main` 与本地 HEAD 一致（`git ls-remote origin refs/heads/main`，与 API 是两条独立通道）。
  中途 12:05–12:11 GitHub 两条通道同时不可达过一次（`git ls-remote` 端口 22 被关 + `gh` API EOF），
  那段时间里"推上去了吗"无法定性 —— 记下来是因为下一次很容易把它当成"没推上去"而重推。
- 矩阵里 08-08 / 13-08 两块补了测试：工具栏"猜出来再删"的判断（9 条正反用例，D-026）、
  快捷键录制器的退出路径（6 条，D-027）—— 后者当场抓到一条真缺陷（录完仍显示"请输入快捷键"，`14a37a0` 修）。
  13-08 仍欠"设置页交互"与"生命周期回调"两块：要先加接缝才好测，本轮不硬凑，记在 backlog 快照 11。
- **启动闪退回归（D-029，S1）**：D-019 给 `AppDelegate` 加的显式 init 让 ObjC 的 `-init`
  变成 trap 桩，而 SwiftUI 的 `@NSApplicationDelegateAdaptor` 正是走那条 —— 327 个用例全绿、包一打开就死。
  已修（`override convenience init()`）+ 两条守卫（运行时走元类型 / 源码扫描），包重打为 `1.4.7-fix1` 并在
  二进制层核对桩已消失。缺口记成 R2-21：CI 里没有「能不能启动」这一关。
- 用户提出"收藏/复制要滑到最右边"⇒ 行内直接可操作（D-028，`1395425`）：双击行复制、行首星标就地收藏。
  星标从 `.clear` 指示器变成真控件，对比度量化到 ≥3:1；**这次是在屏合成点击真点验证的**
  （单击选中 / 双击恰好一次复制 / 点星标不动选中）。遗留 R2-20：收藏切换会把多选收成一条。
- 审计 1.9 的"侧栏图标看不见"从推断升级为测量（D-025）：产品里 0.0000、固定色 0.175–0.402、复刻 List 行里
  `.primary` 正常 ⇒ 离屏语义色伪影，**产品一字未改**；真机那一列仍未验收（在屏捕获要付权限框或废弃 API 的代价）。

### 第二轮进度快照 4（2026-10-10 夜：issue #13 右键菜单汉化，D-032）

- 用户点名修 #13。落地的不是"改文案"，是**把编辑态右键的所有权拿回来**：
  实测共享 field editor 才是右键的接收者，`hitTest` 让位 / 给 `editor.menu` 赋值 / 就地改 `menu(for:)` 三条
  都被数字推翻（第三位的证据是两次调用 `!==`，改完再问又是满的、`allowsContextMenuPlugIns` 回到 `true`）。
  最终用 `addLocalMonitorForEvents` 在派发前截走，认领判据是"field editor 沿 superview 往上属于 `ChineseMenuTextField`"。
- 菜单交付：搜索框 `撤销/重做/剪切/复制/粘贴/全选`、只读详情区 `复制/全选/查找…`；
  `NSWindow.allowsAutomaticWindowTabbing = false` 建窗前设；每次弹出前 `sanitize`（常驻 `MenuSanitizer` 代理，
  因 `NSMenu.delegate` 是 weak）。
- **测量上的一条硬限制**：`popUpContextMenu` 模态且 `didBeginTracking` 里 `cancelTrackingWithoutAnimation()`
  叫它不返回（8 秒看门狗 exit） ⇒ "屏幕上真弹出来的样子"不进仓库判据，改成
  `docs/MANUAL_TEST_v1.4.8_issue13.md` 人眼核对（记成 R2-22；顺带 R2-23：将来新增裸 `TextField` 会绕开拦截器）。
- 在屏探针 `testRightClickMenusAppKitWouldShowAreChinese` 带反面对照（搜索框没在编辑时 `owns == false`）
  和 20 秒看门狗；变异对照 5 组逐一点亮，其中"让拦截不吞事件"那一组表现为**挂住后看门狗报红**，
  这正是它有效的方式。
- 当前判据：`swift build` 0 告警 · `swift test` **339 例 / 10 skip / 0 失败** · 在屏右键探针绿。
  10 条 skip 已逐条核对，全是 env 门控的在屏探针（含这条新增的）。
- CI 定性（现取，别信这里写的数）：`gh run list --branch main --limit 1` —— 本次两个提交的那一跑是
  `success`（`gh run view <id> --json conclusion,jobs`）。
- **#13 已经关闭，但不是我主动关的**：账本提交 `eb7c767` 的标题里有 "…to fix #13…"，
  GitHub 把 `fix #13` 当闭合关键字自动关了它（timeline 里 `closed` 事件带的 commit_id 就是它）。
  记下来有两个原因：① 上一轮的口径是"没碰右键菜单所以不顺手关掉它"，这次是修完且 CI 绿才关，结论没错但**动作不是我做的**；
  ② 提交消息里出现 `#<编号>` 会引用、`fix/close/resolve #<编号>` 会**真的改外部状态** —— 写提交标题时要有这个意识。

### 第三轮进度快照（2026-10-10 夜，D-033）

- 输入：仓库外 `~/Documents/时间剪史_审计_2026-10-10_第三轮`，8 条新缺陷 D-1…D-8 全部处理完。
  用户点名的两处按指定做：**D-1 用修法③**（`List(selection:)` + 把手拖出 + `EntryDragGate`），
  **D-3 给「通用」补两项**（暂停记录 / OCR 可关，取 §5 的 F1/F4）。
- 推翻了自己上一轮的决定（R2-02 说不换 List）——理由逐条对账写在 D-033，不留"看起来反复"的账。
- **测量边界**：换成系统表格后合成鼠标事件送不进去（`clickedRow` 恒 -1），
  点选/双击/拖选三条行为判据转人工（手工清单 `docs/MANUAL_TEST_v1.4.9_round3.md`），
  结构判据留在常规套件；这条缺口记成 R3-D9，别把它当成"已经自动化了"。
- 新离屏伪影一条：`List` 选中高亮在帧里是整块黑，判据是黑块跟随选中集合 ⇒ 不据此判产品（见 AGENT_UI_AUDIT.md）。
- 当前判据（现取，别信这里写的数）：`cd ClipboardHistory && swift build && swift test`
  → 本轮实测 0 告警、355 例 / 10 skip / 0 失败；帧：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`
  → 68 帧、同代码连拍两次聚合 sha 相同。
- **D-034 更正（同一夜，用户真机反馈）**：修法③原本"拖出只从行首把手发起、行体留给拖选"被实测否掉 ——
  `List` 会把行内任何一处 `.onDrag` 提升成整行拖拽源，于是按下就开会话、容器上的拖选手势拿不到事件。
  取舍（用户定）：**保留整行拖出、删掉拖选**，`dragSelectRange` 动作 + 行位置表 + 拖选探针全部清掉，
  不留半套死码；选中靠单击 / shift / ⌘ / 方向键。改动 0 帧变化，判据换成
  "拖出入口恰好一处（在行上）+ 拖选残留必须为空 + 真值表"，变异对照三组点亮。
  教训：**源码扫描钉得住写法，钉不住 AppKit 怎么处理这个写法**；"作用域/归属"类断言要有一条落到真实容器上的判据。

- **D-035（同一夜，用户截图反馈）**：图片文件条目在列表里没有预览 —— 根因是 `.file` 的 thumbnail 只来自剪贴板顺带给的图像数据，从 Finder 复制时通常没有。改成 `add` 后在后台解一张 ≤256px 缩略图写回并落盘，启动时回填老历史；夹具补 `row-file-thumb` 亮暗两帧（68→70）。判据与变异见 D-035。

- **D-036（同一夜，用户真机反馈：点选有延迟）**：这条与上两条不同 —— 上两条是闸门放过真缺陷，这条是**我为了迁就一条不代表真实容器的离屏探针，主动改坏了产品交互**。D-1 之后行内没有兄弟手势，离屏孤立宿主里 `simultaneousGesture(TapGesture(count:2))` 收不到第二击，我就换成 `.onTapGesture(count:2)`，并写了一句没测过的注释"单击选中仍然立刻生效"。实际 `count:2` 的识别器要等一个双击间隔才确定"这只是单击"，而新 `List` 的选中正走这条路 ⇒ 高亮延迟。现在改回 `simultaneousGesture`。判据只剩源层反向守卫（行上出现 `.onTapGesture(count: 2)` 即红），"点选无延迟 / 双击仍可复制"转人工清单 §1 的 1.1 / 1.5（具名）。**规矩：为了让自动化判据点亮而改产品交互之前，先证明那个夹具代表真实容器；不代表就只能改判据或转人工。** 判据：0 告警 · 362 例 / 10 skip / 0 失败 · 变异 1 组点亮 · 帧 0/70 变化。
  **交付形态**：本机正在跑 `make bundle VERSION=1.4.8-fix4` 的产物（仓库根 `时间剪史.app`，universal，
  ad-hoc 签名）；"点选无延迟 / 双击仍可复制"两条要由用户在真机确认（清单 §1.1 / §1.5），我测不到。

## 恢复指令（若上下文丢失，从这里续做）

1. `git log --oneline` 与 `git diff 8007b19..HEAD --stat` 看清已完成什么。
2. 跑 `cd ClipboardHistory && swift build && swift test`（**必须看退出码与 `Executed N tests`，不要用管道**）。
2b. 视觉帧：`cd ClipboardHistory && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`（改 UI 前后各拍一组同参数帧，见 AGENT_UI_AUDIT.md 的复验规则）。
3. 读 `AGENT_BACKLOG.md` 找第一条未关闭的高/中价值项；`AGENT_DECISIONS.md` 读最近 5 条决定；`AGENT_UI_AUDIT.md` 看视觉项。
4. 外部参考：审计报告在仓库外 `/Users/wangziyi/Documents/时间剪史_审计_2026-10-08/`（145 条记录 + 21 条探针源码 `probes/`，探针断言的是"缺陷存在"，接入仓库时需逐条翻转）。
5. 停止条件见本文件开头与 AGENT_BACKLOG.md 末尾的"发布前检查单"。
6. 远端一致性核对（本轮遗留项已做完，这段留作随时复查的入口）：
   ```bash
   cd /Users/wangziyi/Codex_Project0
   git log --oneline origin/main..main                  # 空 = 没有未推送的提交
   git push origin main                                 # 当日 GitHub 只在这一刻通：443/22 其余时间被断
   gh api repos/mnmc5h5ntg-wq/ClipboardHistory/branches/main --jq '.commit.sha'
   for t in v1.4.6 v1.4.7; do gh api "repos/mnmc5h5ntg-wq/ClipboardHistory/git/refs/tags/$t" --jq '.object.sha + " " + .ref'; done
   gh release view v1.4.7 --json assets --jq '.assets[] | .name + " " + .digest'
   ```
   实测结果（2026-10-09 04:52 CST）：远端 `main` 与本地相同，`refs/tags/v1.4.6 = e4ac62b`、`v1.4.7 = 5190ad1`，
   与本地 `git rev-list -n1 <tag>` 一致；两个 Release 附件的 `digest` 与本地 `时间剪史_v1.4.x.dmg.sha256` 逐字相同。
   **注意 `git ls-remote` 走 22 端口、`gh` 走 443 API：同一时刻前者可能失败而后者成功**，别因为一条失败就判定"没推上去"。
   另外用户从新路径确认过项目能打开之后，旧路径的兼容符号链接 `~/Documents/Codex_Project0` 可以直接删除。

- **D-037（同一夜，CI 侧）**：报告型步骤第三次"红了但没有数字"，根因换到了汇报行自己身上
  （runner 的 XCTest 打单数 `Executed 1 test`，抽取用的 `grep 'Executed [0-9]+ tests'` 失手 ⇒ 非零 ⇒
  `bash -e`+`pipefail` 中止 ⇒ 结论行没打、"没跑完"分支永远走不到）。修法：抽取行全部 `|| true` + 正则允许单数；
  新增 `scripts/tests/test_ci_report_selftest.py`（抽 ci.yml 原文、喂日志形状变体，随 CI discovery 真执行，
  变异对照已点亮）。**这条修法还不够**：run 38064293655 里离屏步骤打出来了（`captured frames: 70 executed: 1
  捕获失效帧: 2`），在屏步骤仍只有 `Killed: 9` —— 第二条中止点是 `kill "$killer"`（看门狗执行完 kill 自己退出了，
  `2>/dev/null` 不改退出码），一并兜底并给自检补两格。规矩：**`bash -e` 里"允许失败"的步骤，
  每一行都要问"它非零了脚本还活着吗"，包括清理动作与取值动作。**附带一条自检教训：测"看门狗挂死"时自己的夹具**不能用管道读子进程输出** ——
  孤儿 `sleep` 持有继承的 stdout，`communicate()` 等不到 EOF，实测把自己吊死在超时上；改写文件 + 独立会话按 pgid 收。

## 当前状态（2026-10-11，批次 2 收尾）

- 第三轮审计 §5 的 F-1 / F-4 / F-5 已落地并验证：全量 382 tests 0 失败、`make bundle` 0 warning、
  帧 76 张两次同 sha、4 条新守卫全部变异对照（其中一条最初是假守卫，加强后才红）。
- 下一批：批次 3 = U-4（详情排版 ≤68ch / 单行左对齐 meta / 搜索命中高亮）+ U-5（状态语言统一）。
  再往后：批次 4（U-2 拖拽图像、F-2 RTF/HTML 保真）、批次 5（F-3 快速选择浮层——**先 spike**、C-4 运行时启动冒烟）。
- 恢复要点：`cd ~/Codex_Project0/ClipboardHistory && swift test`；帧
  `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_x swift test --filter UICaptureTests`；
  用 python 驱动 swift 时必须显式设 `SDKROOT=$(xcrun --sdk macosx --show-sdk-path)`（否则报 SDK 不兼容，
  那条红是环境问题）。

## 当前状态（2026-10-11，批次 3 收尾）

- §4 U-4 与 U-5 已落地并验证：407 tests 0 失败、`make bundle` 0 warning、78 帧两次同 sha、5 条新守卫变异对照全过。
- U-5 的"12/13 自绘焦点环"这半条**刻意没做**，理由与所需前提写在 D-039 与快照 18，backlog 标 ready-for-human。
- 下一批：批次 4（U-2 拖出 drag image 含多文件 / F-2 RTF·HTML 保真）。
- 帧取证的一个新坑（别再撞）：逐行取最右墨点会把右下角浮层的按钮数成正文行 ——
  这类"改动有没有进像素"的问题，用两两帧 diff 的包围盒比用行数统计更难被污染。

## 当前状态（2026-10-11，批次 4 收尾）

- §5 F-2 与 §4 U-2（多文件拖出）已落地：416 tests 0 失败、`make bundle` 0 warning、78 帧两次同 sha、
  5 条新守卫变异对照全过、设置页改动的作用范围核对（其余分区 0 像素差异）。
- 最后一批：F-3（⌘⇧V 快速选择浮层，**先做 spike**：`NSPanel` 非激活样式下的键盘焦点是已知坑，
  spike 不通过就不要动仓库）+ C-4（构建产物运行时启动冒烟，必须用可覆盖的数据目录，D-002 不许破）。

## 当前状态（2026-10-11，批次 5 收尾）

- 第三轮 15 条建议（C-1…C-5 / U-1…U-5 / F-1…F-5）全部要么落地、要么在账本里写明了不做的理由。
- 最后一道验证：全量 430 tests / 10 skipped / 0 failures；`make bundle` 0 warning；
  78 帧两次同 sha；本批 5 条新守卫变异对照全过；Python 自测 43 例 OK。
- 剩下的两项都不是"忘了"：C-2 的"对上一版本帧基线做自动对比"仍未自动化；
  InstanceGuard 对直接 exec 启动的第二实例是否漏判，需要真机确认（快照 20）。
## 当前状态（2026-10-11，账面收口）

- 15 条建议全部落地；F-4 的写回分支补成端到端（D-049），15 条里不再有"只测了纯函数"的欠账。
- 现取判据：Swift 433 例 / 10 skip / 0 失败 · Python 64 例 · `make bundle` 0 告警 ·
  78 帧两次同 sha · 24 条守卫变异对照 · CI 全绿（含帧基线两步与运行时启动冒烟）。
- 留给真机的：批次 2–5 的手点清单；待查：InstanceGuard 对直接 exec 第二实例的漏判。

## 当前状态（2026-10-11 晚，新增功能：右侧预览渲染 Markdown）

- 功能已交付并验证：`.md` / `.markdown` 文件与"两类以上 Markdown 语法"的文本条目，
  详情区默认渲染，头部同一行给「原文 / 渲染」。渲染只改看法，存档/搜索/复制路径一行未动。
- 账本：D-050（为什么自己写子集而不是引依赖）、D-051（四个被实测否掉的做法）、
  D-052（帧基线会随系统外观漂移，已钉死并加了双向守卫）。
  视觉验收在 `AGENT_UI_AUDIT.md` U-17（含每个元素的实量对比度）。
- 数字：Swift 520 例 / 11 skip / 0 失败；Python 64 例；`swift build` 与 `make bundle` 0 告警；
  82 帧多次连拍与工作基线 `CHANGED=0 MISSING=0 ADDED=0`（且是在系统深色时段拍的，修之前会漂 18 帧）。
  取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- 新守卫 14 条全部实跑变异对照，**14/14 红在该红的那条用例**，跑完逐字节还原。
- 还没做的：v1.4.9 打包发布（没人要求）；那颗控件的"按下去真的会切换"只有手工清单（D-051 ④）。

## 当前状态（2026-10-11 晚，用户真机报的窗口装饰遮挡已修并装机）

- 缺陷：收起侧栏后详情头部与交通灯叠在一起（账本 D-053 / 视觉 U-18）。
- 修法：让位量由 `WindowChromeMetrics` 在运行时发布（谁摆按钮谁发布），详情头部消费它；
  首帧兜底 35pt。实测 meta 顶部 10pt → 42pt，灯带底边 33pt。
- 数字：Swift 526 例 / 11 skip / 0 失败；`swift build` 0 告警；82 帧与工作基线 0/0/0
  （22 帧因头部下移而变化，属预期）；5 条新守卫变异对照 5/5 红在该红的那条。
- 取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- 本机 `/Applications/时间剪史.app` 已是含此修复的构建（二进制 sha `bf761424…`），
  版本串仍是 1.4.8（v1.4.9 未发布）。上一份留在备份目录，未删。

## 当前状态（2026-10-12 凌晨，侧栏改成"永远显示"：已验证、已装机）

- 用户提议撤销"收起侧栏"这个能力：工具栏按钮与菜单命令本来就已摘掉，本轮补的是**拖分隔条**这条路 ——
  窗口配置器把侧栏列钉成不可折叠，已折叠的（旧存档）当场展开。账本 D-054 / 视觉 U-19。
- 实测：分隔条能去的最左位置 **-1pt → 250pt**；硬按到 0pt 之后列宽仍是 250pt（下限由列自己报）。
- 数字：Swift **531 例 / 0 失败**（+5 条判据）；**7 条变异 7/7 红在该红的那条**（含"钉错列"）；
  82 帧与工作基线 `CHANGED=0 MISSING=0 ADDED=0`（与新判据同进程拍的）；`swift build` 0 告警；Python 64 例 OK。
  取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- CI `e4b5359` 服务端结论 **success**（Swift 6.1.2 / macOS 15）：531 例 / 11 skip / 0 失败，
  5 条新判据在 CI 上**真的执行过**（不是被跳过），日志里的 `SIDEBAR_PIN` 数字与本机一致：
  钉住后最左 250pt、未钉住 -1pt。
- **状态由这一条决定**：`/Applications/时间剪史.app` 的二进制已是 `14f2f079…`（含本轮钉侧栏），
  装机前那份 `bf761424…` 留在 `~/Documents/Codex_Project0_backups/before-pinned-sidebar-20261012-002001/`
  （只此一份，另一份重复副本已清掉）。装完进程是从新路径起来的（pid 58939，`ps`/`lsof` 都指向 /Applications），
  不是"旧进程还在跑"那种假装机。
- 用户数据前后逐字节未变：`history.json` 70527 bytes / sha `98b00782…` / 84 条 / mtime 不变，`images/` 8 个文件。
- 留给真机的：**拖一次分隔条**（拖不动即成立，批次 7 第 7.1 条）；macOS 12/13 上这条判据没跑过（欠账 8）。

## 当前状态（2026-10-12 清晨，动效专项：交付 + 砍单，账本 D-055 / 视觉 U-20）

- 输入是 501 行的动效专项审计报告（含它自己 §11/§13 的 15 条 MC 缺陷）。用户要"先判出最不合理的
  约 10% 并说明为什么不做，剩下的实现"。结果：**加进去的 7 处动效，价值都来自先砍掉的 8 条**
  （M1 列表行过渡、M3/M10 热键呼出、M4 整块淡入、M9 扫光、M12 共享元素、M13 高亮、M14 stagger、M18 彩带）。
- 本轮最值钱的一条实测：**分带归因**。把动画事务挂到 `HistoryStore` 变更漏斗上之后，
  整窗逐帧从"一帧跳变"变成 4 帧斜坡，看起来 M1 成了 —— 但只量列表中部那条带（第 4~8 行）
  是 `0.304` 一帧到位、落定残余 0.000，与关掉曲线时一模一样。斜坡全部来自详情区。
  ⇒ 报告的结论成立，M1 在 `List` 上做不成；差点把"详情区在淡"当成"列表在滑"交付出去。
- 尺子自己也换了两轮驱动：`CADisplayLink` 在显示器休眠时 `ticks` 恒为 0（本机实测），
  `Timer` 被 App Nap 节流，最后用**自旋循环**当时钟 + `cacheDisplay` 离屏合成。
  顺带摘掉整个类的 `@available(macOS 15.0, *)` —— 那扇门本来只为 `CADisplayLink` 存在。
- 数字：`swift build` **0 告警**；`swift test` **560 例 / 0 失败 / 17 skip**；
  `MotionCatalogTests` 21 条、`MotionFilmstripTests` 8 条（`MOTION_SUMMARY notice-banner=3
  detail-kind-change=3 empty-state=4`，反向 `list-insert=一帧`、`same-kind=0.000`）；
  **7 个变异 7/7 红在该红的那条**；82 帧 `CHANGED=0`（动效只改在途帧，与基线闸门零冲突）；
  帧间隔对照臂：动画开 p95 16.67ms / worst 50.5ms，动画关 p95 16.67ms / worst 39.1ms ⇒ 量不出代价。
  `HistoryStore` 1094 行（比本轮开始前还低 7 行）。
- **一件自伤要记**：变异脚本里一句 `git checkout -- .` 把 9 个未提交文件还原到了 HEAD。
  靠事前 5 份 `cp` 备份 + 逐条重放恢复，恢复后所有数字是**重新跑出来的**，不是推测的。
  规矩：还原只准逐文件字节级 `cp`。
- 留给真机：批次 8 的 9 条（尤其 8.3 方向键连翻、8.6 VoiceOver 听那句"已复制"、
  8.7 中途打开减弱动态当场生效、8.8 热键呼出确实无动画）。
- **CI 那道像素闸的正文终于读到了**（run 38224108646）：`motion suite exit: 0 executed: 8`
  + `MOTION_SUMMARY notice-banner=3 detail-kind-change=4 empty-state=3` ⇒ MC-8 关闭，
  8 条判据在 CI 上真的执行且与本机同数。根因是日志噪声（一次 `swift test` 打 360 万条
  colorspace 消息，占 97.4%），过滤后整份日志 2386 行。
  我先前把"读不到"记成"下载不下来"，那是错的解释（下载只是慢，放宽超时就完成了）—— 已就地更正。
- 未覆盖：Switch Control 那一格（无公开 API）；设置页/菜单栏两处淡入没有各自的像素判据
  （机制与已量到的三条同源）；500 条时那一次 56ms 帧仍未定位（M1 砍掉后动效不再随条目数增长）；
  macOS 12/13 全档未跑（本机 27、CI 15）。


## 2026-10-12 17:13 换装：新版已装到 /Applications 并在跑（HEAD `b4ee260`）

- 用户要求"以后要手动运行检测都这么干"：需要真机验收的判据由我构建+换装+跑起来，不让他自己编。
- 已装：universal 包，二进制 sha `aaa032b463dfc13b…`；**版本号仍是 1.4.8**（自上次发布没 bump），
  所以"是哪一版"按 sha 与 HEAD 认，不要看 About 框。
- 旧包（`14f2f079…`）移到 `~/Documents/Codex_Project0_backups/before-motion-round-20261012-171308/`，没删。
- 证据链：`SMOKE_OK=1`（先退出旧版才拿得到，见下）→ staged 与 installed sha 相同 →
  `codesign --verify --deep --strict` 通过 → 新 pid 44938、启动时刻晚于安装、`lsof` 的 txt 指向
  `/Applications/…` → 存档 85 条未减少 → `DiagnosticReports` 无新崩溃。
- 流程已固化成 **`scripts/install_local.sh`** + 4 条自检（`scripts/tests/test_install_local.py`）：
  默认 dry-run、`--yes` 才动、失败自动回滚；沙箱三条判据（预检不过不许动现场 /
  sha 必须相等 / **回滚回来的必须与新包内容可分辨**）都真跑过。脚本 68 条自检全过。
- 三个坑写进了脚本注释与长期记忆：① 冒烟闸门必须排在退出旧版之后（守卫按 bundleIdentifier
  找第二实例，否则假报 `SMOKE_OK=0`）；② 活着的 App 随时写存档，"逐字节相同"不是有效判据，
  改判"条数只增不减"；③ CJK 路径在 `ps`/`lsof` 里是转义输出，别直接喂给 `shasum`。
- 交给用户的只剩人眼判据：批次 8 的 9 条（本轮新增一条往返测试由用户自己点：复制一次看历史长没长）。


---

## 状态 · 视觉迭代 R5（2026-10-13）

- 本轮是**第一轮把"全部页面全部元素"当范围**：约 206 个位点过完，产出 `.scratch/motion-audit/`，
  其中 8 条我自己读码核实、6 条已修、2 条证伪并写明理由。
- 连续 ≥90 的轮次：**R1 80 → R2 85 → R3 88 → R4 90 → R5 91**（R5 是第一个 ≥90 的下一轮，
  目标要求"连续五轮 ≥90"，所以还差三轮）。
- 全量测试 615 / 24 skipped / 0 failures；动效套件 20 / 3 skipped / **0 failures**（开工前它是红的）；
  0 warning；82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 M6 2/2 + M8 1/1 CAUGHT。
- `HistoryStore` 零改动（1093/1120 行，上限只降不升那条守卫仍然绿）。
- 本机安装：R5 的包在提交后换装（`scripts/install_local.sh --yes`），
  人眼判据见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 13。
- 下一轮（R6）主题已经立项：**"状态变化的可读性"** —— 详情预览三态硬换、
  设置页清空后的数字回执、暂停采集那一下的指示（三条共用同一个判据形状）。


---

## 状态 · 视觉迭代 R6（2026-10-13）

- 连续 ≥90 的轮次：**R4 90 → R5 91 → R6 92**（目标要"连续五轮 ≥90"，还差两轮）。
- R6 主题「状态变化的可读性」：预览三态软交接、清空后的数字回执（含播报）、展开箭头与揭示同曲线。
- 新增判据一族 `MotionDriverTests`（8 条）：**恒真的 `.animation(value:)` 键**是 R5 那族守卫的镜像，
  带真值表；回执的"先数再清"用两行代码的先后钉住。
- 验证：623 tests / 24 skipped / 0 failures；动效套件 20 / 4 skipped / 0 failures；
  0 warning；82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 6/6 CAUGHT。
- 未闭环：预览三态与回执淡入的**产物级**证据（人工批次 14）；QuickPick 空结果；
  排除名单增删过程；本机 `judged=1/3` 的覆盖损失（BACKLOG 第 8 条，推荐修法 ③ 尚未落地）。
- R7 建议主题：**浮层与临时状态**（QuickPick 空结果一句话 + 落选态、批量条出现/消失的可插值落点、
  视频两颗图标接 `symbolMotion`）+ 把 BACKLOG 第 8 条的 `judged` 下限做成判据。


---

## 状态 · 视觉迭代 R7（2026-10-13）

- 连续 ≥90：**R4 90 → R5 91 → R6 92 → R7 93**（还差一轮就到"连续五轮 ≥90"）。
- R7 收掉 QuickPick 空结果、批量条两臂、视频两颗图标，新增"符号替换只有一个作者"一族判据，
  并把动效覆盖率下限做成 CI 里会红的一步（BACKLOG 第 11 条结案）。
- 验证：629 tests / 24 skipped / 0 failures；动效套件 20 / 4 / 0；0 warning；
  82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 5/5 CAUGHT。
- 本机安装：R7 包在提交后换装（人工判据 = 批次 15）。
- 未闭环：QuickPick 淡入与空态播报的产物级证据（AppKit 侧，D-055）；
  排除名单增删（P2）；设置分区切换的 Scenario（P3）；实验 E1/E2/E3。
- R8 建议主题：**设置窗口专轮**（分区切换过渡转正为可量场景、排除名单增删过程、
  三处 caption 的"永不清空"、快捷键录制态），因为那 50 个位点里已核实的一批还没动。


---

## 状态 · 视觉迭代 R8（2026-10-13）· 目标达成

- **连续五轮 ≥90 达成**：R4 90 → R5 91 → R6 92 → R7 93 → R8 93；无新增 P0/P1 回归。
- R8 做掉设置窗口已核实的三条：排除名单六种结局各有话术（纯函数 `ExcludedAppListPolicy`）、
  名单增删过渡、三处结果文案统一成可关掉的 `ReceiptLine`（不自动消失）。
- 验证：632 tests / 24 skipped / 0 failures；动效套件 20 / 4 / 0；0 warning；
  82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 M20–M23 4/4 CAUGHT。
- 本机安装：R8 包在提交后换装；人眼判据 = 批次 16。
- 仍未闭环（不粉饰）：AppKit 侧淡入与播报的产物级证据（D-055 边界）；
  菜单栏原生菜单在打开期间不重绘（P4，动效是唯一不该用的修法）；
  设置分区切换仍无 Scenario；实验 E1/E2/E3 未跑；
  已知两条红（`testSidebarListFocusRingAfterClick`、帧间隔 p95）本轮之前就存在。
- 总报告：`AGENT_FINAL_REPORT.md`。


---

## 状态 · 视觉迭代目标收口（2026-10-13 23:25）

- **目标达成**：连续五轮 ≥90（R4 90 / R5 91 / R6 92 / R7 93 / R8 93），
  全页面逐元素审计约 206 个位点已做完并落成 `.scratch/motion-audit/`。
- main 的 CI：R8b 与总报告两次 run **均成功**；R8 那次红由覆盖率闸门指出真实覆盖空洞，
  已在 R8b 用"三档判据"修掉（CI `judged` 0/3 → 2/3，门槛未动）。
- 本机跑的就是 R8 的包（pid 41157，sha 与 staged 相同，存档 92 → 92）；
  R8b 只改测试与账本，**不需要重装**。
- 人眼判据累计欠账：批次 12（按压态）、13（R5 空态与失败回执）、14（R6 预览三态与清空回执）、
  15（R7 QuickPick 空态与批量条）、16（R8 排除名单与结果文案）。
- 未闭环项都写在 BACKLOG 第 8/9/10/12/13 条与总报告 §21.4，没有"顺手当完成"的。
- 总报告：`AGENT_FINAL_REPORT.md` §21。

## 状态 · 目标模式阶段一完成，阶段二起跑（2026-10-13 12:30 本地）

**阶段一 · 每日复制热图已交付**（新功能，不是动效轮）：
设置 → 新增「统计」分类，26 周 × 7 天日历热图 + 汇总行 + 图例 + 原生 tooltip + 悬停详情 + 空态。
数据源是**单独的只追加账本** `daily-copy.json`（日键→条数，保留 730 天，损坏改名保原字节），
**不是**从 `entries` 现算 —— 后者有 500 条上限，现算出来的历史会随旧条目被淘汰而**倒退**。
首次为空时从存档时间戳回填一次；采集路径零同步磁盘写；退出同步 flush；回滚 = 删那一个文件。
决定见 **D-068**，视觉账见 **U-30**，人工验收见批次 **17**，轮次现场见 `AGENT_VISUAL_ITERATION.md` 阶段一节。

- **数字**：0 warning；653 tests / 16 skipped / **0 failures**（+21 条新用例）；
  动效套件 20 / 4 / 0，`judged=2/3`（与 R8b 同档，未退）；帧基线 **82 → 90**，
  `check --against working` = `COMPARED=90 CHANGED=0 MISSING=0 ADDED=0`（同提交 update）；
  `scripts/tests` 72 passed；`HistoryStore` 只加 4 行胶水（`lines=1111 funcs=52 longest=66`，只减不加的闸仍绿）。
- **变异 9 支**（M25、M25b、M26–M32）：第一次 8/9 —— **M31 逃逸**，因为它的判据用 `debounce: 60`
  且从不等待，"排了写盘"与"没排"看起来一模一样（恒真判据）；重写后 9/9 CAUGHT。
  M32 是本轮真实崩溃（MainActor 闭包被 `dispatch_assert_queue` 打断 → SIGTRAP）转成的回归判据，
  顺带把变异分类器教成"崩溃 = `CAUGHT=crash`，不是没跑"。
- **自评 88 / 100**（<90 ⇒ 按规矩继续修；扣在"动效细节"与"可访问性"两栏，都是新界面自己的账）。

**阶段二已准备**：`.scratch/motion-audit-2/00-inventory.md` —— 两个只读代理并行产出的全量位点清单
（主窗口/QuickPick 89 行 + 设置/菜单栏约 90 行，含 MotionCatalog 八档引用表、两套互相矛盾的 reduce 闸门、
去重后 20 条"最可能真缺陷"合并榜、R9–R28 排期）。
**这一轮明确禁止沿用 R1–R8 的结论当"已经对了"**：包括 D-066 里"快捷键录制态刻意不加动效"那一条，
R16 会带着原文理由重新判一次。

**下一步（R9 的三条头账）**：①`lastWriteError` 发布通道（BACKLOG 14）；②热图 hover 插值兑现（15）；
③`OffscreenSymbolInkProbeTests` 名单从产品枚举取 + 加"名单 == 产品"守卫（16）。
本机换装：见下面"本机跑的就是…"一行，阶段一的包在提交后重装并独立核对 sha / pid / 存档条数。

## 状态 · R9 完成（阶段二第 1 轮，2026-10-13 12:5x 本地）

审的是**上一轮自己交的东西**。六条改动全部来自看帧或读事务形状，读代码看不出来：
悬停描边与"当天变深"进了事务（键是 `bucket` 不是 `count`）、页脚那条**永远不演**的动画
被撤掉并写明理由（本轮唯一"减"的一条）、空↔网格两臂补齐过渡并由 `counts.isEmpty` 驱动、
零值汇总行与「这张图怎么读」不再在没有图的屏上说话。账见 **U-31 / D-069**，人工验收批次 18。

- **数字**：0 warning；658 tests / 16 skipped / 0 failures（+5）；动效套件 20 / 4 / 0、`judged=2/3` 未退；
  帧基线 `update` 后 `CHANGED=0`，本轮只有 4 张空态帧变（有数据的 8 张逐字节不变 ⇒ 重排没动布局）；
  `scripts/tests` 72 passed；变异 **M33–M42 十支全 CAUGHT**（第一次 M39 只改声明 ⇒ 编译不过 ⇒
  那是"没跑"不是"抓住"，改成连调用点一起改名后才红）。
- **自评 91 / 100**：新加的两条动画目前只有**结构证据 + 静帧**，像素证据排在 R9b
  （胶片套件的 `Scenario` 要能挂非主窗口的根视图，那条改动单独一支）。
- **CI 的第一发红了，红的是编译器**：Swift 6.1.2 在 `emitLazyGlobalInitializer → emitRawApply`
  SIGSEGV，本机 6.2.1 不复现。绕法与"为什么不做二分"见 **D-069**。
  这一发要盯：如果这次 CI 还红在同一个栈上，说明嫌疑不止那两处，得换一条绕法。
- **R10 的头一条已经定死**：`lastWriteError` 的发布通道（BACKLOG 14）——
  本轮刻意没顺手做，它是功能级缺陷，混在动效轮里做会让两件事的判据互相借光。

## 状态 · R10 完成（2026-10-13 13:1x 本地）

**R9 的 CI 绿了**（run 38348602329，8m12s：0 warning / 658 executed / 90 帧 / 0 捕获失效），
D-069 那条"全局惰性初始化器"绕法成立 —— 但**没有定位到具体是哪一处**，注释里写的是"嫌疑"。

R10 做的是 R9 留下的两条：
- `lastWriteError` 现在有发布通道（`@Published` 镜像 + 只送"该重绘"不送值的主队列回看 +
  flush 自己同步 + **没失败时不许多发**的反向判据）；
- 图标墨水探针的名单改成从 `SettingsCategory.allCases` 推导，并加"名单 == 产品"与逐枚墨水两条判据。

**顺手被数字否证的一个目测结论**：`chart.bar` 不是"实心柱混进描线那一列"（它是第二重的，0.0138 vs 同列 0.0118–0.0143）；
真正的异类是 `wand.and.stars` = 0.0052，比同列最轻的还轻 2.3 倍，而且从 D-8 那轮起就在。
本轮**不改**（换符号是语义 vs 重量的取舍），也**不加阈值判据**（拿六个数反推门槛 = 把一次观测写成规律）。
记 BACKLOG 22 + 人工验收 19.3，把判断交给人眼。

- **数字**：0 warning；664 tests / 16 skipped / 0 failures（+6）；动效套件 20 / 4 / 0、`judged=2/3` 未退；
  帧基线 `CHANGED=0 MISSING=0 ADDED=0`（本轮零像素变化，这是正确的结论）；`scripts/tests` 72 passed；
  变异 M43–M46 四支全 CAUGHT。自评 **90 / 100**（本轮按设计没有视觉交付，分数如实反映）。
- **下一轮（R11）**：回到像素 —— R9b 那三条动画的胶片证据（`Scenario` 要能挂非主窗口根视图），
  然后按清单进主窗口（侧栏批量按钮零按压反馈 / 行没有 hover / 筛选滑块 0.38s 越权那三条）。

## 状态 · R11 完成（2026-10-13 14:0x 本地）

去兑现 R9 欠的"像素证据"，结果**推翻的是结论不是分数**。

`Scenario` 现在能挂非主窗口的根视图（宿主是产品自己的 `DailyCopyStatsSection`，
为此 `private` → internal），新场景 `heat-first-record` 第一次跑就把 main 判红：一帧到位。
按这个方向改了两版产品代码，**两版读数一模一样**；于是做仓库里已有的那件工具 —— 双向 A/B：

```
MOTION_HEAT_FADE_A/B 开 帧数=1 峰值=0.225 冷闸=true  关 帧数=1 峰值=0.225
```

**关掉动效目录读数不变 ⇒ 这把尺看不见纯 opacity 的淡入**（`cacheDisplay` 抓模型树）。
所以这条淡入定为**「源码已接、产物未量」**：不写进已验证，也不反过来说产品没做。
影响面比这一条大：**以前几轮的 MOTION 数字只覆盖带布局位移的那类过渡**（记 BACKLOG 23，
总报告要把"已验证 / 产物未量 / 人眼判"三类分开列）。

同轮补的：冷采样闸门 `clockIsWarm`（新窗口头两帧 260–340ms，触发落在上面会把 160ms 的过程拍成两三个样本）、
说明块「这张图怎么读」的过渡与驱动成对（它以前是整块硬蹦的）。
**我自己写的守卫先红了一次且红得不对**：needle 把 `private struct` 写死了，
去掉 `private` 就找不到目标 —— 产品没坏，守卫锁了个不相关的语言细节（已改并写进注释）。

- **数字**：0 warning；666 tests / 16 skipped / 0 failures（+2）；
  动效套件 21 / 4 skipped / 0 failures，`MOTION_SUMMARY` 三键形状不变、`judged=2/3` 未退；
  帧基线 `CHANGED=0`（说明块包进 `VStack(spacing:16)` 后布局逐字节不变）；`scripts/tests` 72 passed；
  变异 **M47–M49 三支全 CAUGHT**（M49 打的是尺子自己的闸门：`warmIntervalMilliseconds` 设成达不到 ⇒
  "看不见"这条结论必须作废，不许拿冷采样宣布尺子的极限）。自评 **92 / 100**（性能栏扣 6 分给预卷放宽与 A/B 多录一卷）。
- **人眼欠账**：批次 20 就是这条淡入的验收 —— 机器量不到，只能看。
- **R12 选题**（清单里的第 6/7 条，都是"我改过的要重新判"）：
  筛选滑块 0.38s / damping 0.72 越过目录自己的 ≤0.25s 与不过冲两条；
  同一个文件里两套 reduce 闸门（`@Environment(\.accessibilityReduceMotion)` 只认系统开关、不认 VoiceOver，
  且 `.linear(duration: 0)` 是**清零**而不是替换 —— 违反 R1 定的规矩）。

## 状态 · R12 完成（2026-10-13 14:3x 本地）

清的是**自己前几轮留下的两笔账**（全新清单第 6、7 条）：侧栏筛选胶囊
`0.38s / damping 0.72` 越目录上限且必有过冲（它是点出来的，不是手势跟手）；
它的 reduce 闸门只读系统开关、不认 VoiceOver；而这一段悬停**只有缩放一种表达** ⇒
开了「减弱动态效果」= 悬停零反馈。
现在：目录新增 `.slider`（0.20s、临界阻尼）、闸门取或、悬停补一层 `controlHover` 底色。
**性质是清账不是发现** —— 目录注释当时就写着"这两处有过冲，是已知例外"，知道了没排上。
账见 **D-070 / U-34**，人工验收批次 21。

- **翻案**：`FilterPillMotionTests` 原有一条把"过冲是想要的"钉成了规矩；先读原文（R2-10 的
  动机是"滑块不读 reduce 开关"，那半条仍成立并保留），只推翻"过冲"这半句，理由写在测试上方。
- **设计好的摩擦**：目录白名单守卫立刻红了 —— `HistorySidebarView.swift` 不再在目录外写曲线，
  名字已按提示删掉。顺带把 `Shape.Slide.leading` 这条死分支用起来。
- **数字**：0 warning；667 tests / 16 skipped / 0 failures；动效套件 21 / 4 / 0、`judged=2/3` 未退；
  帧基线 `CHANGED=0`（静止态逐字节不变是这一轮应有的结果）；`scripts/tests` 72 passed；
  变异 **M50–M53 四支全 CAUGHT**（M51 故意打到另一个套件）。自评 **93 / 100**。
- **欠**：悬停态无像素证据（BACKLOG 24）、"0.20s 且不过冲"尺子量不到（纯 transform，同 R11 那族）。
- **R13 选题**：清单第 11 条 —— 侧栏五颗批量按钮（含删除）用 `.buttonStyle(.borderless)`，
  零按压、零悬停，是全 App 唯一一处绕开 `PressableStyle` 的地方；
  以及第 19 条 `PressableStyle:53` 那个硬写的 `isHovered: false` 让 `VisualFill.hover` 档全 App 不可达。


## 状态 · R13 完成（2026-10-13 15:3x 本地）

清的是**我自己在 R4 留下的那一半**：`PressedStyle.makeBody` 里硬写 `isHovered: false`
（`ButtonStyle` 不能有 `@State`），于是 `VisualFill.hover` 这一档在**全 App 12 处按钮**上
运行时不可达，而真值表、令牌、字段名全都绿着 —— 载荷绿、消费侧坏。
现在样式内部多了一个真的视图持有它；顺带把三处 `.buttonStyle(.borderless)`
（侧栏五颗批量按钮含**删除**、排除名单「移除」、回执 ×）收进同一档，
并给小控件新增 `hoverLevel` 参数（0.10，其余站点保持 0.06 不动）。
账见 **D-071 / U-35**，人工验收批次 22。

- **视觉复核第一次用 bbox 定位**：`CHANGED=2` 两帧都在多选条，整帧看不出差别，
  逐像素 diff 指到 `(343,220)-(529,266)` ＝ 四颗描线图标，明暗各 0.19%、最大通道差 264/201。
  判读：**图标从灰提到满**（`.borderless` 对 label 的处理，不是暗色对比度问题）；
  红色 trash 一像素没动（它带显式 `foregroundStyle`）⇒ 反证压暗来自样式。
  这五颗全文件零 `.disabled(` ⇒ 压暗不携带信息，只是把可用动作画成禁用。**改善，无回归。**
- **变异第一次 4/5**：M58（样式转交时把 `hoverLevel` 换成默认档）全绿通过 ——
  本轮新加的参数自己重演了本轮修的缺陷族。补"花括号配平区域 + 转交点不许出现常量 +
  全仓恰好三处消费者"的接缝判据后 **5/5**，区域助手另配真值用例。
- **一条关于报告型数字的新认识**：`MOTION_RESOLVE_SUMMARY` 是**负载敏感**的 ——
  同一场景单独跑最粗采样 70ms（判）、全量并跑 81ms（门槛 48ms ⇒ 拒判）。
  两个数都记；以后既不许把 2→1 当回归去追，也不许当"都验过"去报。
- **数字**：0 warning；全量（开在屏探针）670 tests / 16 skipped / 0 failures；
  胶片单独 21 / 4 / 0、`judged=2/3` 与 R12 同；脚本 72 passed；
  帧基线 `update` 后 `CHANGED=0 MISSING=0 ADDED=0`；自评 **94 / 100**（R9 91 / R10 90 / R11 92 / R12 93）。
- **核对过的一条老账**：`--against auto` 对 v1.4.8 报 `MISSING=2` 是
  `glass-pill-120x200` → `120x232` 的改名（R1/R2 之间刻意改高），不是夹具掉帧。
- **R14 选题（改尺子，不改观感）**：① 给交互探针加一条**真** `mouseEntered` / tracking-area 通路，
  让胶片能框住单个控件判"悬停药丸画没画出来" —— 做成一次解锁清单里约 15 处 hover-only 位点；
  ② 帧夹具补两帧（`settings-privacy-excluded`、`settings-data-receipt`），
  让「移除」与回执行**第一次**进基线（本轮这两处是"源码已接、产物未量"）。
  R15 再谈药丸几何与命中区（BACKLOG 25）。


## 状态 · R14 完成（2026-10-13 16:4x 本地）

**这一轮改的是尺子，不是观感**（顺带修掉一条被旧尺子漏掉的真实回归）。
排期里的"合成 hover 取证通道"三条路实测全断（spike 文件带复现命令）：
CGEvent 投递被窗口服务器静默丢弃、对 `NSHostingView` 直接调 `mouseEntered:`/`mouseMoved:`
不进 SwiftUI 的 hover 分支、`window.sendEvent(合成 mouseEntered)` 直接崩。
⇒ 把"悬停有没有效果"拆成两半：**触发**永久人眼（批次 23），**表达**从此有判据。

- **新判据上线抓到的第一条是 R13 自己引入的回归**：小控件悬停 0.10 与按下 0.12 在 22pt 上
  只差 `3.7/255`（地板 4）—— 抬悬停的动作把按压抹平了，而 R13 所有判据全绿。
  改 `controlHover` 0.08（不是抬按下：那会把 `pressed→selected` 压到地板以下，同一种塌法换个位置）。
- **两张从没存在过的帧**：`settings-privacy-excluded`（含那颗破坏性「移除」）、`receipt-line`（× ）。
  基线 90 → 94。三次翻车全是"看帧"抓的：540 高拍不到按钮（用户行排在 10 行默认清单之后）、
  种子串手写分隔符（`;` 不是 `,`）导致一颗「移除」冒充两行、以及那句说明在屏幕上打印字面 `**`。
- **夹具机械自己也进了判据**：种过的默认值必须还原（污染是静默的，基线会把它钉成"产品长这样"）。
- **数字**：0 warning；671 tests / 16 skipped / 0 failures；脚本 72 passed；
  帧基线 `CHANGED=0 MISSING=0 ADDED=0`（94 张）；变异 **M59–M62 全 CAUGHT**。自评 **95 / 100**
  （R9 91 / R10 90 / R11 92 / R12 93 / R13 94）。
- **R15 选题**：BACKLOG 25 —— 悬停药丸的几何与命中区（`PressedStyle` 的底色铺在 label 包围盒上，
  比系统工具栏那颗小一圈，且命中区与药丸同尺寸）。现在"表达"有尺子了，可以谈几何。
  顺带把 BACKLOG 29（改令牌必须跑完整梯子）做成一条真守卫。


## 状态 · R15 完成（2026-10-13 17:5x 本地）

做了 R14 排的两条：药丸几何（BACKLOG 25）与"令牌必须进梯子"（BACKLOG 29）。
`PressedStyle` 新增 `labelPadding`（默认 0 ⇒ 其余 12 处按钮一个字节不变），
三处小控件给 4–5pt：**高亮比字形大一圈，而且那一圈点得中**（padding 挂 overlay 是骗眼睛，
挂 label 才让命中区一起长）；侧栏 `spacing` 8→0 让相邻两颗挨着。
账见 **D-073 / U-37**，人工验收批次 24。

- **本轮最关键的一刻是判据自己错了**：新加的 field 梯子从硬编码 0 起步再 `dropFirst()`，
  而输入框静止态不是 0 ⇒ 它量的是 `idle→fieldActive`，`fieldIdle→fieldActive` 从未被比过。
  **M66 因此全绿通过（第一次 3/4）**。修好起点之后当场量出真缺陷：
  **暗色下搜索框"空"与"正在输入"只差 3.98/255（地板 4）—— 等于没有状态通道**。
  `fieldActive` 0.06 → 0.075 ⇒ `7.97 / 6.97`。两条出路选了改动小的（6 张帧 vs 20 张）。
- **日志现在打出两档各自的令牌值**：这一轮绕圈的原因就是"改了令牌、读数不变、看不出量的是谁"。
- **夹具又撒过一次谎**：`sidebarFrame` 把宽度写死 300，第一次拍 250 窄帧时两边各裁 25pt，
  extent 正好等于整幅宽 ⇒ 一眼看出是夹具不是产品。**先量 extent 再下结论**，
  否则"窄侧栏溢出"这个假缺陷会被当成真缺陷去修。宽度现在是参数。
- **数字**：0 warning；673 tests / 16 skipped / 0 failures；脚本 72 passed；
  帧基线 94 → 96、`CHANGED=0 MISSING=0 ADDED=0`；变异 M63–M66 **修完 4/4**。自评 **96 / 100**
  （R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95）。
- **R16 选题**：清单第 4 条 —— `DetailView:38 vs :47` 只有空臂有过渡，而注释承诺"换类型交叉淡"。
  先读 R5 那批的原文再判（改过去钉过的设计要先看当初为什么那样钉）。
  顺带把 BACKLOG 27（用户排除项被埋在 10 行默认清单之后）作为一个**交互**决定提给用户。


## 状态 · R16 完成（2026-10-13 18:1x 本地）

清单第 4 条：详情区 `if/else` 只有空臂挂过渡，内容臂一帧硬切 ⇒
**删掉最后一条时整块详情区空白约 160ms** —— 而那正是 D-055 当年否决 M4"整块淡入"用的理由，
砍对了方向却把另一头留成了半个。现在两臂成对，才是真交叉淡；
换选仍然不演（守卫第三条钉住供电键不许变成"选中的是哪一条"）。
账见 **D-074 / U-38**，人工验收批次 25。

- **"上次量不到"不当成"这次不用量"**：重做双向 A/B ⇒ `开 帧数=1 峰值=0.030 / 关 帧数=1 峰值=0.030`
  （冷闸已过、前提看得见）⇒ 这条淡入同样在 `cacheDisplay` 的可见面之外。
  判据是**自我作废**的：两臂哪天不同它就红。
- **判据自己红过两次**（锚点取第一个 `var body` 把别人的过渡数进来；
  数 `.transition(` 子串把一行数成两次）—— 都修成"按换人本身取区域 + 按行数"。
- **reduce 路径逐函数查过**：`contentFade` 两模式都是纯 opacity，两臂同事务换人，不给空白留机会。
- **数字**：0 warning；675 tests / 16 skipped / 0 failures；脚本 72 passed；
  帧基线 96 张 `CHANGED=0`（过渡类改动应有的结果）；变异 M67–M69 **3/3 CAUGHT**。自评 **93 / 100**
  （R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96）。
- **R17 选题**：清单第 10 条 —— QuickPick 三处（重排退回首 `reloadData`、原地换字、滚动无平滑）。
  这一族的账本记录说"原生行动画已经接上"，但**没人为这三处逐行复判过**，照例先读原文再判。


## 状态 · R17 完成（2026-10-13 18:3x 本地）

清单第 10 条。浮层里**最高频**的一次变化 —— 刚复制的那条被顶到最前 —— 一直是 `reloadData()`：
`QuickPickRowDiff` 里那句"保留行相对顺序变了 ⇒ 原生 API 表达不了"把这一档一起划掉了。
现在"恰好一行挪位"升成一次 `moveRow`（reduce 时照样挪、只是不滑），
多行同时跳与"移动混着增删"**仍然**硬刷新（不猜 AppKit 的连续 move 坐标系 —— 猜错是安静地排错行）。
账见 **D-075 / U-39**，人工验收批次 26。

- **三个直觉被实现纠正**：两行互换是一次移动、三行循环位移是一次移动、
  而"第一个不同的下标处动的是左边的元素"**不一定** —— 只试一个候选会漏掉本轮唯一要救的形状。
- **`CHANGED=0` 这轮不算证据**：快速选择浮层是 AppKit 面板，而帧夹具只会拍 SwiftUI
  ⇒ 96 张基线里没有一张是它。缺口记 **BACKLOG 30**（补 `quickpick-*` 三张）。
- **胶片对照臂已加，本机没拿到激活态**（`visible=true key=false active=false`）⇒ 按规矩报
  `MOTION_NOT_RUN=app-not-active`，既没读成"不会动"，也没为了绿放宽门槛。
- **数字**：0 warning；678 tests / 16 skipped / 0 failures；脚本 72 passed；变异 M70–M72 **3/3 CAUGHT**。
  自评 **95 / 100**（R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96 / R16 93）。
- **刻意不做的一条**：移动之后不给 `scrollRowToVisible` 加平滑滚动 —— 键盘驱动的浮层里
  "选中行跟着跳"是系统习惯，加了会把跟手变成慢半拍（与 D-055 砍 M3/M10 同一理由）。写进注释了。
- **R18 选题**：BACKLOG 30（给帧夹具加 AppKit 通路 + 补 `quickpick-*` 三张）——
  它同时是本轮结论的前提，也是清单里"浮层每一个状态"能不能被复判的门槛。

## 当前状态（2026-10-13 · 视觉迭代 R18：量尺的诚实性）

**选题没做成，而这正是本轮最有用的产出**：AppKit 通路（`Fixture.appKit`）与控制器捕获入口
（`QuickPickController.buildContentForCapture`）都建好了，浮层**仍然一张都拍不出来** ——
`NSVisualEffectView` 在没上过屏的窗口里没有可合成层，六张候选帧全报 `transparent=99.5%~100%`。
结论改由一条**自我作废**的判据守着（它红了就是能拍的那天）。顺带查出的三处量尺不诚实，
比原选题值钱：

- **6/96 张帧的名字不等于它的尺寸**（`NSHostingView` 把内容理想尺寸写回窗口）。
  最贵的是 `content-with-notice-750x560` 实际 1304 高 —— 这张帧的职责是"提示条会不会把布局挤坏"，
  而窗口偷偷长高 ⇒ **它从来没被挤过**。钉死两层 + 快门前断言，现在 98 张全部名实相符。
- **`weights` 夹具把整页头部裁了九轮**：560 的框套 850 的内容，标题/说明/「恢复默认」/第一行因子
  从来不在帧里。改成 880，并补 `weights-adjusted`（新颜色梯子的"动过"那一态此前**没有任何帧**）。
- **系统 `List` 的选中高亮在离屏画成纯黑** ⇒ "选中"这个状态从来没有像素证据，
  而这块黑此前被读成"最后一行是空的"。现在每张帧报 `blackBandPt`，
  8 个夹具名钉进 `materialBlindSpotFixtures`（多一个红、少一个也红）。
- **产品侧唯一一处**：权重列的只读数值穿着系统强调蓝（实测字形 (0,122,255)，
  而真按钮是中性白 (223,223,223)）⇒ 九个"链接"点了都没反应。重写颜色语义，
  改后同一条判据数到 **0 个蓝像素**（改前暗色 2345 / 亮色 2557）。

- **两条被当场推翻的"现成尺子"**：`host.fittingSize` 是**恒真尺**（有 `.frame(height:)` 时
  只报被钉死的数），而且**读它会改窗口尺寸**（那次跑出来 58/98 帧自己变高）；
  "整行 60% 是黑的"这种**占比**判据对窄块必然漏（`content-*` 三张全漏）⇒ 改成绝对宽度 ≥60pt。
- **一次重复踩的坑，要记成规矩而不是记成教训**：变异电池第一版八支全 `DID-NOT-RUN`
  烧了 47 分钟 —— 本机 python3 注入的 `SDKROOT` 让 `Package.swift` 编不过。
  **R1 的账本里就写过同一条**。差别是那次修在一次性脚本里，这次把它写进模板：
  `BASE_ENV` 剔 SDKROOT + **第 0 支变异=预检**（不注入任何东西先要求每条判据能跑且为绿，
  不过就一支都不注入、退出码 2）+ 还原自检比"电池开跑前自己抓的字节"而不是 `git diff`。
  R19+ 的电池直接从 `mutate_r18_frame_rulers.py` 抄这三件。
- **数字**：0 warning；**680 tests / 16 skipped / 0 failures**（日志里那 10 条 `warning:`
  是 CoreData 运行时噪声，不是编译告警）；脚本 72 passed；帧基线 **96 → 98**、同提交 update、
  复跑 `CHANGED=0 MISSING=0 ADDED=0`；变异 **M73–M80 九支全部符合预期**
  （M76 = 故意放的"期望漏网"：夹具高度退回 560 **没有任何测试会红** ⇒ BACKLOG 32；
  M75a 期望 EITHER、实测 CAUGHT ⇒ `sizingOptions` 那行不是装饰）。
  自评 **91 / 100**（R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96 / R16 93 / R17 95 / **R18 91**）。
- **R19 选题**：BACKLOG 31 —— 先 spike"把捕获窗口 `orderFront` 到屏幕外，材质能不能合成"。
  它决定的是**选中态**这一整个状态类能不能被机器复判；spike 成，则补 `selected` 系列帧；
  不成，则把"给人眼"这件事钉死（**不许**用自绘选中底色绕过去，那是 D-034 否掉的方向）。
  清单第 13 条剩下的那一半（拖动时数值与滑块之间没有视线锚点）排在它后面。

## 当前状态（2026-10-13 · 视觉迭代 R19：推翻上一轮自己写下的"根因"）

**这一轮的产出主要是"把一句错的结论改成对的"**，界面零改动 —— 所以自评 86（<90），
R20 必须交付看得见的改善，不再连续第二轮纯量尺。

- **R18 那句"浮层背景是 `NSVisualEffectView`，离屏没有可合成层"两半都错**：
  读 `ensurePanel()` 里根本没有材质视图；spike 证明裸材质离屏画得出来 `(58,58,58,a=255)`。
  读数是真的（`transparent=99.5%~100%`），**解释是编的** —— 这是账本里最贵的一类错，
  因为它带着数字，下一轮会拿它当前提。
- **真正的原因（这次是量的）**：浮层的 `NSStackView` 在捕获环境里只有 24pt 宽
  （真实 App 里 420×300）⇒ `NSScrollView` 0×0 ⇒ `NSTableView.visibleRect` 0×0 ⇒ 5 行画不出一行。
  补"真实显示周期"（orderFront 到屏幕外 + runloop + 递归 `tile()` + `display()`）**不解决**它。
- **判据从一层变三层**：`rows>0` 症状 / `transparent>0.9` 标题 / `stackWidth<100` **原因**。
  第三条保证"哪天原因又变了"会红着说"解释过期"，而不是让新的一句猜测继续顶上去。
- **本轮最值钱的一条规矩**：M82 打掉夹具对控制器的持有之后，`rows > 0` **没红**
  （`numberOfRows` 报的是上次 reload 的缓存），红的是新加的 `table.dataSource is QuickPickController`。
  ⇒ **症状会活过病因**；写判据先问"接线断了这条读数还对不对"。四支变异 M81–M84 全 CAUGHT。
- **`Fixture.appKit` 改成返回 `NSWindow`**：R18 那条"帧名必须等于帧的尺寸"从此核的是
  产品真实的 420×300，而不是夹具自己填的数。
- **又排除一个候选解释**：选中态那块黑在**上屏之后仍然是黑**，`isKeyWindow=false`
  ⇒ 它要的是 key window，不是材质。BACKLOG 31 的原因同步更正。
- **真实视觉审查**：详情区玻璃药丸三帧并排量过 ——
  暗色填充与底色 Δ=6（看着像"容器消失"），但分离本来就由**自适应描边**
  （`Color.primary.opacity(0.20→0.07)`，实测 Δ 81/75）+ `VisualShadow.raised` 承担 ⇒ **判过不改，理由入账**。
- **数字**：0 warning；680 tests / 16 skipped / 0 failures；脚本 72 passed；
  帧基线 **98 张不变**、`CHANGED=0 MISSING=0 ADDED=0`（本轮零像素改动）；
  自评 **86 / 100**（R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96 / R16 93 / R17 95 / R18 91 / **R19 86**）。
- **R20 选题（硬指标：必须有界面改善）**：清单第 14 条 —— 提示条插入/撤走时的**布局位移**。
  现在横幅出现会把整条 `NavigationSplitView` 往下顶一下，没有过渡；
  这一条 R18 刚把夹具尺寸钉真（`content-with-notice` 终于真的是 750×560），
  所以"挤不挤"第一次可测。配套要判：位移要不要动画、`bannerIn/bannerOut` 时长是否对称、
  以及 reduce 下是否只改高度不改时序。

## R20 · 悬停档与命中区清扫（U-42 / D-078）—— 换了选题，换了的原因记在这里

**选题偏离**：R19 立的硬指标是"必须有界面改善"，具体做哪一处由读码决定。
开场重读 `PressedStyle` 时发现 `XCTAssertEqual(consumers, 3)` 那条守卫**把 R15 的未完成态钉成了边界**
（五处圆形小控件一直用着给整行定的 0.06），于是本轮先做这一件；
清单第 14 条（提示条布局位移）**顺延**，且它现在更值得做 —— R18 已把夹具尺寸钉真。

- **界面改动 4 个文件**：`GlassControls`（撤掉叠上去的第二层悬停底色，`hoverLevel: 0`）、
  `HistoryRowViews`（行首星标抬到控件档）、`SearchField`（清除 × 抬档 + 命中区 14→22pt + 文本列声明 22pt）、
  `VideoPreview`（播放/静音抬档）。
- **本轮最值钱的两条**：① 一条只数已完成部分的守卫会把"没做完"伪装成边界 ⇒ 改成**按形状要求每一处表态**；
  ② 变异 M88 把 × 写成 `labelPadding: 0` 而旧守卫**全绿** —— 它在数字符串，不在数参数 ⇒ 现在读**值**。
- **自己引入又自己抓到的回归**：只加命中区让搜索框两态不等高（31 vs 32pt，打字时框自己跳）。
  根因是**这一行的定高者换了**，不是数值大小；第一次修只把方向反过来。
  新判据 `testSearchFieldKeepsTheSameHeightInBothStates` 把两态真的量一遍（带高差 ≤ 2px），
  并顺手发现 `search-field` 夹具 96pt 一直在裁自己 ⇒ 抬到 112（基线仍 98 张，帧名随之变）。
- **真实视觉审查（新做了一把行带尺）**：22 帧哈希变化被压成一句
  "框长高 1pt + 下面整列平移 1pt"：详情列 k=0 **0 行不同**、筛选段 k=2px **0 行不同**、
  搜索框那 16 行才是真变化。量尺自己也要报配置 —— zsh 吞参数那次差点变成假归因。
- **看着帧量出来、本轮没修的缺陷（BACKLOG 33）**：清除 × 静置对比度 **暗 2.22 / 亮 1.86**，
  低于可辨线 3.0（同帧占位符 9.42 ⇒ 尺没坏）。命中区抬大之后这条更要紧：看不见的大目标仍然看不见。
- **数字**：0 warning；682 tests / 25 skipped / 0 failures；脚本 72 passed；
  帧基线 **98 张**（22 changed + `search-field` 改名 2，同提交 update）；
  变异 **M85–M89 五支全 CAUGHT**（预检 4/4 绿、`RESTORE_CLEAN=yes`）；
  自评 **89 / 100**（R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96 / R16 93 / R17 95 / R18 91 / R19 86 / **R20 89**）。
- **R21 选题（89 < 90，继续修）**：图标控件的**静置对比度** —— 把可辨线从文字推广到控件，
  做一条跑在夹具帧上的判据（`inspect_r20.swift stats` 那套：众数=背景、2% 极值=字形、WCAG 比值），
  扫全部图标按钮并把不过线的改色（方向：静置 `.secondary`，悬停交给 R20 的底色药丸）。
  顺带做掉 BACKLOG 32（`contentMustFit`）：本轮又一次靠人眼才发现夹具在裁自己，那条守卫该有了。

## R21 · 可辨线推广到控件（U-43 / D-079）—— 量出来的缺陷修了，还立了能推广的尺

- **界面改动 3 个文件**：`VisualTokens`（新增 `VisualInk.control` / `controlTargeted` 两档画笔）、
  `SearchField`（清除 × 静置从 `.tertiary` 抬到 `VisualInk.control`，指到 `.primary`）、
  `DetailView`（多文件行展开箭头同一族）。
- **实测账**：× 1.86/2.22 → **3.74/5.34**；箭头 1.88/2.27 → **3.85/6.06**；
  两处参照位（药丸星 4.43/7.86、侧栏批量 14.56/12.43）未动 —— 尺要能同时说"过"与"不过"。
- **新增判据**：`UICaptureHarness.inkContrast`（产物像素上的 WCAG 比值 + 墨占比）、
  `testActionableInkStaysAboveTheLegibilityFloor`（4 处 × 2 外观，自己拍自己量）、
  `testContrastRulerArithmetic`（21:1 / 1:1 / `#767676` 对纯白 4.54:1 / 两个方向的单调性）、
  `testTheFaintestInkTierIsReservedForNonControls`（`.tertiary` 按文件点名，计数走标识符边界）。
- **本轮最值钱的三条**：① 尺的真值表抓到作者把单调性写反（黑底上"更亮"才是"更对比"）；
  ② 像素探针要自带"这块真的有墨"的地板 —— 估的五个框里两个贴在空白上；
  ③ R15 的"死令牌"守卫把放错文件的常数抓了出来 ⇒ 地板住判据旁边（`InkFloor`），
  产品侧只留真的被读的 `VisualInk`，没人读的 `smallText` 删掉。
- **电池升级**：每支变异除 CAUGHT 之外还要在失败输出里找到期望文本（M92 必须红在墨地板那条）。
  **M90–M94 五支全 CAUGHT**，预检 3/3 绿，`RESTORE_CLEAN=yes`。
- **真实视觉审查**：行带尺读数 = 6 帧、三条 9pt 带（三颗箭头）+ 两条 12.5pt 带（那颗 ×），
  **k=0 就对齐 ⇒ 零几何牵连**；暗色下逐张看过，层级是"内容 > 可点 > 说明"。
- **排除一条假缺陷**：`MotionCatalog.asymmetricTransition` 已给两个方向各绑 `.animation`
  ⇒ 清单 14 里"时长不对称没生效"那一半不成立，只剩"横幅会不会把内容顶下去"。
- **数字**：0 warning；685 tests / 25 skipped / 0 failures；脚本 72 passed；
  帧基线 **98 张**（6 changed，同提交 update）；自评 **91 / 100**
  （R9 91 / R10 90 / R11 92 / R12 93 / R13 94 / R14 95 / R15 96 / R16 93 / R17 95 / R18 91 / R19 86 / R20 89 / **R21 91**）。
- **R22 选题**：清单 14 剩下的那一半 —— 提示条插入/撤走时的**布局位移**
  （`content-with-notice` 现在尺寸是真的，"挤不挤"可测；reduce 下只改高度不改时序也要判），
  顺带做掉 BACKLOG 32（`contentMustFit`：本轮之前又一次靠人眼才发现夹具在裁自己）。

## R21b · CI 打红的是判据自己（D-080）—— 像素尺换成了布局尺

- **现象**：R21 推上去 CI 685 tests / 1 failure，红在 R20 新立的
  `testSearchFieldKeepsTheSameHeightInBothStates`：本机 32.5/33.0pt，runner **15.5/17.0pt**。
- **根因**：那张框太淡（填充 0.035、描边 0.05），在无头 runner 的白底上落不进像素阈值 ⇒
  "框"塌成"有墨的行"。**同一把尺在两台机器上量的不是同一件事。**
- **改法**：等高改判**布局**（`GeometryReader` 读实排高度，新判据
  `testSearchFieldIdealHeightIsStateIndependent`）；像素那条降级为诊断并改名
  `testSearchFieldFixtureShowsBothStates`（只核"夹具在、帧里有两条带"）。
- **顺带修掉一个真缺陷**：新判据第一次跑就报 32.0 vs 32.5 —— `xmark.circle.fill` 固有高度 14.5pt，
  R20 那句"两态都锁在 32pt"其实没锁住。钉 `.frame(14×14)` 后两态都是 32.0，容差 1.5pt → **0.2pt**。
- **两条过程账**：`fittingSize` 在本仓库作废（裸 hosting 读 0；建离屏窗口读会 **SIGSEGV**；R19 已证恒真）；
  前提断言 `> 10pt` 第一次跑就把 0.0 拦下 —— 没有它，这条判据会**绿着通过**。
- **数字**：0 warning；`686 tests / 25 skipped / 0 failures`；脚本 72 passed；
  帧基线 98（6 changed，同提交 update）；变异 **M90–M96 七支全 CAUGHT**（含红得对不对的核对）。
- **R22 选题不变**：清单 14 剩下的那一半（提示条插入的布局位移）+ BACKLOG 32（`contentMustFit`）。

## R22 · 取证面一轮（U-44 / D-081）—— 没有界面改动，这是本轮的分数为什么是 87

- **改了什么**：只有测试与夹具（`UICaptureHarness`、`MotionFilmstripTests`）。
  **产品代码零改动 ⇒ 本机装的还是 R21b 那一份**（`make bundle` 的输出会逐字节相同，
  所以本轮不重新换装，理由记在这里而不是默默跳过）。
- **新增判据**：`Fixture.contentMustFit`（10 张自包含帧）+ 底行墨判据 + **正对照**
  （`sidebar-history` 底行 100% 有墨）；`testBothBannerArmsAreJudged`（横幅两臂都要在清单里）；
  `premise-not-visible` 现在报"卷内最大逐帧差 + 过渡帧数"。
- **新增帧**：`content-with-two-notices`（亮暗两张，基线 98 → **100**）。
  两条都走产品入口；组件帧 `notice-banner` 自己写的 `VStack(spacing: 12)` 是**夹具替产品做的决定**，
  真窗口里没有那 12pt。
- **本轮最值钱的一条**：变异电池第一版报 M97/M98/M99 三支 ESCAPED，
  真相是**整批测试被跳过**（没设 `CLIPBOARD_HISTORY_UI_SHOTS`，skip 的退出码是 0），
  预检也把跳过读成了绿。补上"只有 skipped ⇒ DID-NOT-RUN"与环境变量之后
  **M97–M100 四支全 CAUGHT**，且每支红在该红的那条断言上。
- **量出来但没修**：一条文字的警告横幅占 **88pt**，两行文字的错误横幅占 **50pt**。
  两个候选解释（底色涂到透明标题栏后面 / 那其实是两条同色横幅）都还没判掉 ⇒ BACKLOG 35。
  **不在读懂之前动产品**，所以本轮没有界面改善。
- **数字**：0 warning；`687 tests / 25 skipped / 0 failures`；脚本 72 passed；
  帧基线 **100**（同提交 update）；`MATERIAL_BLIND_SPOTS 9 of 50`；自评 **87 / 100**
  （… R20 89 / R21 91 / **R22 87**）。
- **R23 选题（硬指标：必须有看得见的改善）**：判掉并修掉 BACKLOG 35 那条 88pt；
  顺带把 `notice-banner` 组件帧的 `spacing: 12` 改成与产品一致（0 + Divider），
  让那张帧不再展示一个产品里不存在的布局。

## R23 · 提示条的底色不再涂到标题栏后面（U-45 / D-082）—— 本轮有看得见的改善

- **界面改动 1 个文件**：`NoticeBanner` —— `.background(style)` → `.background(style, ignoresSafeAreaEdges: [])`
  （macOS 13+；12 的默认行为本来就对，所以按版本分叉而不是补偿式 padding）。
- **诊断**：临时 `GeometryReader` 探针打出 `safeAreaTop=52.0`，再用新加的 `column` 模式沿一列扫色度
  ⇒ 修前 `y 0–52` 已经是橙色底色（只有底色、没有内容），文字从 54pt 才开始。
  **R22 留的两个候选解释到此判掉一个**（那里没有第二条横幅）。
- **实测账**：一条文字的横幅 **88pt → 38pt**；装饰区 `R-B` 从 **+26 → 0.0**；
  横幅自己那一条仍是 +24.9（底色没被削掉）。行带尺归因：
  **4 张帧变、每张恰好 `0.0–52.0pt` 不同，以下逐像素相同 ⇒ 零布局位移**。
- **新判据**：`redMinusBlue(...)` + `testNoticeTintDoesNotReachTheTitlebar`
  （**自带正对照**：先要求横幅那条带 `R-B > 8`，再要求装饰区 `|R-B| < 4`）。
  变异 **M101/M102/M103 三支全 CAUGHT**，各自红在该红的那条断言上；预检真绿（不是跳过）。
- **清理**：诊断探针夹具**没有留在基线里**（它产出一张 `Color.clear` 覆盖图，留着就是谁也不审的死帧）。
- **数字**：0 warning；`688 tests / 25 skipped / 0 failures`；脚本 72 passed；
  帧基线 **100**（4 changed，同提交 update）；自评 **90 / 100**
  （… R21 91 / R22 87 / **R23 90**）。
- **R24 选题**：BACKLOG 36 —— 组件帧 `notice-banner` 还在用 `VStack(spacing: 12)` 摆两条横幅，
  而产品是 `spacing: 0` + 每条自带 `Divider` ⇒ 那张帧展示的是产品里不存在的布局；
  顺带把清单 15/16/17 里没判过的位点继续推。

## R24 · 提示条的正文不再是灰的：文字侧第一次有尺（U-46 / D-083）—— 本轮有看得见的改善

- **界面改动 2 个文件**：`StatePresentation`（新增 `messageInk(for:)` 档位 + `StateLine` 走档位）、
  `UICaptureHarness`（组件帧 `notice-banner` 的 `VStack(spacing: 12)` → `0`）。
- **量到的缺陷**：亮色下三张横幅帧的正文对比 **3.82–3.92**（13pt 常规要 4.5 ⇒ 不达 AA），
  而同一帧那枚"知道了"是 **12.28** ⇒ 一条横幅里"下一步"比"发生了什么"清楚 3.2 倍。
  根因不是颜色选错，是**"这件事需不需要被读到"从来没有进过规范**（四个状态共用 `.secondary`）。
- **修完的账**：亮色 **12.98–13.94**、暗色 **10.48–11.54**；组件帧带间缝 **13pt → 1pt**（与产品同值）。
  行带尺归因：产品两张帧**只有字母那层**变（`content-with-notice` 仅 y 64–93），
  `content-with-history` 与九张 `settings-*` **rows=0** ⇒ 零布局位移。
- **新判据**：`noticeBands`（自己找带，不写死坐标）+ `testNoticeBodyTextStaysReadable`
  （四条地板：带内墨占比 / 对比 ≥4.5 / 带间缝 ≤2pt / 每张帧至少几条带）
  + 正对照 `testNoticeBandFinderReadsBothEnds`（深墨 14.11 过、浅墨 1.32 必须不过）
  + 真值表与接线两条。**判据不依赖 `CLIPBOARD_HISTORY_UI_SHOTS` ⇒ CI 上真的跑。**
- **变异 M104–M109 六支全 CAUGHT**，`RESTORE_CLEAN=yes`。
  M108 **红得与我预测的不同**（红在对比度地板而不是墨地板）⇒ 自家地板的适用边界被量出来了：
  "带里有墨"挡不住"框里有别的控件"（BACKLOG 38 写清补法）。
- **量尺自己犯的三件事**：① 移植时丢括号，Swift 的 `<<` 优先级高于 `/` ⇒ 尺瞎成"0 条带"，
  是正对照逼出来的（原型跑通 ≠ 移植跑通）；② 判据里 `bands[0]` 越界把测试进程打死（signal 5）
  ⇒ 崩溃是把红伪装成"环境问题"；③ 我按估值把组件帧 170→150，被上一轮自己写的 `contentMustFit` 打红
  ⇒ 帧的高度只能量（实测内容 y41–160，高度保持 170）。
- **数字**：0 warning；`692 tests / 27 skipped / 0 failures`（+4 条判据；两条 skip 是 env 门住的捕获/探针，与本轮无关）；
  脚本 72 passed；帧基线 **100**（6 changed，同提交 update，compare 现 CHANGED=0）；自评 **92 / 100**
  （… R21 91 / R22 87 / R23 90 / **R24 92**）。
- **CI**：R23 那次红是** runner 没抢到**（`The job was not acquired by Runner of type hosted`），
  不是判据红 —— 已 `gh run rerun` 重跑取真读数。
- **R25 选题**：清单里未判过的位点继续推（16 扫光曲线、17 菜单栏图标语言、24 缩略图 pop-in、
  25 视频进度条步进、26 `symbolEffect` 12/13 分叉、27 GlassPill 材质切换），
  并做本轮新开的 **37**（多行横幅里动作按钮的垂直位置，判据雏形已有）。

## R25 · 提示条的"知道了"回到整条带的正中（U-47 / D-084）—— 本轮有看得见的改善

- **界面改动 2 个文件**：`StatePresentation.StateLine`（一行里两根轴：内层 baseline 钉图标+文字，
  外层 `.center` 只管动作位）、`UICaptureHarness`（新增 `inkRowSpan` + 两条判据）。
- **量到的缺陷**：按钮字形行的中心 vs 色带中心 —— 单行 **0pt**（碰巧对，所以那张帧从没暴露过它）、
  两行 **−6.5pt**、三行 **−14.5pt**。读起来像"这个动作只管第一句话"。
- **修完的账**：10 条带（3 帧 × 两外观）偏移**全部 +0.0**；
  代价是每条多行横幅**矮 1pt**（以前按钮下沿把行撑高 1pt）⇒ 下面整列上移 1pt/2pt，
  **本轮不是零位移**（行带尺报 530 行不同正是这个平移，与 R23 的结论分开写）。
- **新判据**：`testNoticeActionIsVerticallyCenteredInItsBand`（|按钮中心 − 带中心| ≤ 3pt，
  找不到按钮就红，不许静默跳过）+ 三端正对照 `testActionSpanRulerReadsBothEnds`
  （居中读居中 / 偏上 8pt 必须读出超过容差 / 空块必须返回 nil）。
- **变异 M110–M113 四支全 CAUGHT**，`RESTORE_CLEAN=yes`。M113 专打"兜底值把不见了读成完美"。
- **量尺自己错过的两件事**：① 动作框开宽到 95pt ⇒ 同一套代码在两帧上读出 +0.0 与 −4.2，
  差的是正文混进了框（**两张同构的帧读数不一致，先怀疑尺**）；② `nil` 不能换成兜底值。
- **数字**：0 warning；`694 tests / 27 skipped / 0 failures`（+2 条判据）；脚本 72 passed；
  帧基线 100（6 changed，同提交 update，compare 现 CHANGED=0）；自评 **91 / 100**
  （… R22 87 / R23 90 / R24 92 / **R25 91**）。
- **R26 选题**：清单里未判过的位点（16 扫光曲线、17 菜单栏图标语言、24 缩略图 pop-in、
  25 视频进度条步进、26 `symbolEffect` 12/13 分叉、27 GlassPill 材质切换），
  以及 BACKLOG 38（带内文字列的左锚定地板 —— 上一轮 M108 量出来的那道拦不住的缝）。

## R26 · 详情加载态第一次进帧基线：条带与那一句同一条左轴（U-48 / D-085）—— 本轮有看得见的改善

- **界面改动 3 个文件**：`DetailPreviewViews`（`loadingView` → 具名 `DetailLoadingView` +
  `.leading` 对齐 + `containerGutter` 内缩）、`UICaptureHarness`（新夹具与判据、BACKLOG 38 的左锚定地板）、
  `SkeletonMotionTests`（接线守卫升级：帧与产品必须引用同一个类型）。
- **本轮最大的发现不是缺陷而是空白**：51 个夹具里**没有一个**是加载态 ——
  全 App 唯一的常驻动效从来没被帧看过。原因是它异步、拍它等于赌时机（墙钟依赖的夹具不许进仓库）。
- **第一次拍到就量出两条轴**：条带 x=**0.0**（该在 gutter=20）、句子 x=**316.5**（居中）。
  修后 20.0 / 20.5 / 令牌 20，亮暗一致。归因：全 102 帧只有 `detail-2-file` 变，
  且恰好是条带与句子的四段（84–156.5pt）。
- **判断（不改，交证据）**：条带对面板只有 Δ13（1.09:1）—— 装饰性表面，
  AA 的 4.5 与 3.0 两根线都不适用；抬亮抢的是正文。行内 16pt 缩略图的换图也不加淡：
  它在整窗帧里只占 0.06%，低于胶片尺 0.5% 的可见地板，"淡"和"蹦"用户都看不见。
- **新判据**：`leadingInkColumn`（最左有墨列，条带要 `minDelta: 6` 才看得见）+
  `skeletonAxisReadings`（按弱墨/强墨自己分行）+ `testLoadingBlockSharesTheDetailColumnsAxis`；
  横幅判据补上**左锚定**（BACKLOG 38 关闭）。
- **变异 M114–M119 六支全 CAUGHT**，`RESTORE_CLEAN=yes`。
  **M116 第一次 ESCAPED**：跨帧对照的"另一帧"里最左的强墨就是同一个加载块自己
  ⇒ 去掉 gutter 两边一起挪，判据照样绿。**跨帧对照必须先证明两帧量的是不同的东西。**
  第二版改成"落在产品自己的 gutter 令牌上"后它红了。
- **数字**：0 warning；`695 tests / 27 skipped / 0 failures`；脚本 72 passed；
  帧基线 **102**（2 added + 2 changed，同提交 update，compare 现 CHANGED=0）；自评 **92 / 100**
  （… R23 90 / R24 92 / R25 91 / **R26 92**）。
- **R27 选题**：`MotionCatalog.skeletonSweep` 的 curve/transition 两支是死的（要么接上要么删）；
  17 菜单栏图标语言；26 `symbolEffect` 12/13 分叉（`.id()` 强制重建 ⇒ 不可能交叉淡，
  只有从透明淡入 = 一帧空白）；BACKLOG 30 / 31 / 34 剩余 / 39。

## R27 · 要读的标签不许比能点的笔画更淡：`.tertiary` 清零（U-49 / D-086）—— 本轮有看得见的改善

- **界面改动 1 个文件**：`DailyCopyHeatmapView` 三处刻度（月份 / 星期 / 图例"少·多"）
  从 `.tertiary` 提到 `.secondary`。判据与账本改动在 `UICaptureHarness`、`PressFeedbackTests`。
- **推翻的是上一轮的判断**：R21 把 `.tertiary` 判为"看不见"（控件实测 1.86–1.88）之后，
  给热图刻度留了三处免检，理由是"那不是控件，是刻度文字"。本轮重新量：**1.88 亮 / 2.27 暗**，
  与被判死的控件同一组数；而刻度恰恰是这张图里唯一被读的东西 ⇒ 免检不成立。
- **修完的账**：亮 1.88 → **3.75–3.85**，暗 2.27 → **6.06**。
  归因：102 帧只有两张热图帧 + 两张内嵌它的设置帧变，且全是文字行 ⇒ 格子几何零位移。
- **口径（本轮最重要的决定）**：地板立成**梯子**不是及格线 —— `captionInk = 3.5`
  （"必须在 secondary 那一档或以上"）。**不追 WCAG 4.5**：系统的 `secondaryLabelColor`
  实测只有 4.0，用 4.5 钉 caption 会把"标题—说明"压平。正文 4.5（R24）与说明 3.5 分属两种角色。
- **新判据**：`captionInkProbes`（三处 × 两外观，带墨占比地板）+
  `testCaptionTextStaysOnTheSecondaryTier`；`.tertiary` 点名账本**清空**。
- **变异 M120–M122 三支全 CAUGHT**，`RESTORE_CLEAN=yes`。
  M120 第一次被电池自己拒注入（裸 needle 命中 5 次 ≠ 期望 1 次 ⇒ 变异会撒谎），
  换成三根带上下文的 needle 才拿到真实的红 —— 这条流程本身是对的。
- **数字**：0 warning；`696 tests / 27 skipped / 0 failures`；脚本 72 passed；
  帧基线 102（4 changed，同提交 update）；自评 **91 / 100**
  （… R24 92 / R25 91 / R26 92 / **R27 91**）。
- **R28 选题**：`MotionCatalog.skeletonSweep` 的 curve/transition 两支是死的（接上或删），
  以及清单 17 / 22 / 26 / 27 里挑一条做。**R28 是阶段二的第 20 轮**，之后转入最终报告收口。


## R28 · 阶段二第 20 轮（U-50 / D-087 / BACKLOG 40–41 / 人工批次 36）

- **一句话**：开场去重新判"设置侧栏图标字重"，量到的第一件事是**尺在骗人**；
  真正的产品缺陷在同一张帧的内容列 —— 快捷键页第三行说明带 `.lineLimit(1)`，
  被切掉的恰好是唯一那句需要解释的话（默认 ⌃⌥⇧V、刻意不是 ⌘⇧V 的理由）。
- **动产品**：`HotKeySettingsRow` 说明改成换行 + `.fixedSize`，与同一个窗口里通用页那段三行说明同语言。
  不是零位移：快捷键页第三行约 +26pt，`settings-min` 跟着变。
- **动夹具**：`makeSettingsView` 补注入 `exportHistoryAction` / `importHistoryAction`
  —— 产品永远注入，而视图里它们是 `.disabled(x == nil)` ⇒ 帧里那两颗一直是禁用态，
  帧基线把禁用态钉成标准（真接坏了也看不出来）。配一条从产品调用点推导名单的对账守卫。
- **动尺（三处）**：
  ① `signedInk` 把"反相"与"没画"分开数 —— 亮色帧里 `command`/`hand.raised`/`folder` 是
    (255,255,255) 对 (248,248,248)，暗色帧里换两枚是 (0,0,0) 对 (24,24,24)，
    **每枚的 RGB 跨两帧恒定** ⇒ 语义色被解析到另一套外观，产品一行没改
    （把 `.primary` 换成固定色是审计第二轮明文禁止的方向）；
  ② `textInkMass` 的闸门 60：平涂的录制框每块 ≈14k 像素、整页文字 ≈17k，
    用 R24 那档 24 会把信号**静默**稀释一半 ⇒ 七档真值表钉住；
  ③ **修 R27 的回归**：`captionInk = 3.5` 是本机数，CI 的 macos-15 runner 上同一条红了两处
    （星期 2.85 / 图例 3.30，run 38443414396）⇒ 改成"同机同外观现拍的 `.secondary` 当参照"
    （`captionTierTolerance = 0.8`），绝对值只留 2.2 一条"参照坏了"的兜底。
- **两臂对照**：新夹具 `settings-shortcuts-wide`（1100×540）当"全文"参照；
  修前 ratio 0.809/0.792，修后 1.003/0.998。**参照臂的资格也判**（宽于默认 +300），
  否则两臂自比会恒真且无一条判据会红。
- **变异 M123–M129 七支全 CAUGHT**（`RESTORE_CLEAN=yes`），每支都红在期望的那一句上。
  过程收益：M128 的失败消息暴露了我自己写的 `String(format: "%.0fpt", 10)`（Int 递给 %f ⇒ 打出 0pt）。
- **数字**：0 warning；`699 tests / 27 skipped / 0 failures`（+3 条判据）；
  帧基线 102 → **104**（6 changed + 2 added，同提交 update）；自评 **92 / 100**
  （… R25 91 / R26 92 / R27 91 / **R28 92**）。
- **未判定**：「清空」这颗在帧里不是红的（`.borderedProminent` + `.tint(.red)` 到底有没有吃到）——
  需要一次真机截屏，BACKLOG 40 + 人工批次 36.4。
- **阶段二 20 轮跑满**（R9–R28）。下一步：`AGENT_FINAL_REPORT.md` 收口。


## R28b · 同一天：CI 把本轮新立的判据打回，参照臂 1100pt → 900pt

- `c5db5ec` 的 CI 红在 `testSettingsHelperTextIsNotClipped`：
  runner 上参照臂**整帧 0 墨**，本机读 23864 ⇒ 报"参照坏了，这条比较恒真"。
- 与 R3-D11 的 `content-wide-1100x800`（95% 未绘制）同族，两条都落在 1100pt（@2x>2048px）。
  根因**未证明**，只记现象 + 新开 BACKLOG 42（含一条定位实验：900/1024/1100 三档拍同一张帧看断崖）。
- 处置：参照臂 900pt；"参照必须有墨"的红保留；本机 ratio 1.001/0.998、M123 0.809/0.792 均未变弱；
  帧基线仍 104（两帧改名 900x540，同提交 update）。

## R28c + R29 · 参照臂换方向 + 判墨的尺第一次有方向

- **R28c**：900pt 的参照臂在 CI 上**仍然整帧读 0 墨**（run 38451162726）⇒ 我给的
  "越过 2048px"解释被证伪（900×2=1800px）。可复现的边界只剩
  "≤750pt 全好，>750pt 两档全坏"。对照换成 `settings-min`(640) vs `settings-shortcuts`(720)，
  两臂都在拍得出来的那一档；新增两条资格断言（≤750pt、窄臂至少窄 60pt）。
  实测修后 0.999 / 1.001，M123 掉到 0.925。`settings-shortcuts-wide` 撤下，基线 104 → **102**。
- **R29**：`inkTailSplit` + `inkIsOnTheExpectedSide` 进了仓库尺，两条"太淡"判据的失败消息
  各挂一行方向诊断（反相 ⇒ 不许改产品）。正对照来自真的坏帧：
  `INK_SIDE 图标列 亮35/暗0 标题列 亮0/暗118`。真值表七条 + 变异 M130。
- **数字**：0 warning；701 例 / 27 skip / 0 失败；脚本 72 passed；帧基线 102 / `CHANGED=0`；
  变异 M123–M130 全 CAUGHT（结果以 `/tmp/r29-mutation.log` 为准）。

## R29b · CI 暴露：runner 拍不出「设置」这一页（不是尺寸问题）

- R29 的 CI（run 38453566489）三条红，共同点是**读到的设置帧什么都没有**：
  `settings-general` 图标列与标题列都读到 0 个偏离像素，`settings-shortcuts` 整列墨量 0；
  同一次运行里 430pt 热图帧与 750pt 横幅帧读数正常。
- ⇒ **上一轮写的"宽度 >750pt 就不行"也是错的**：720×540 的 `settings-general` 同样空白。
  现在能说的是"空白跟着 `SettingsView` 走，不跟着尺寸走"。原因仍未证明。
- 处置：两条依赖设置页的判据在"读到 0"时打印诊断（帧像素尺寸 / scale / 透明率）并记 **NOT-RUN**，
  本机仍然实跑（`720=23889 / 640=23868`、`图标列 亮35/暗0`、`标题列 亮0/暗118`）。
  恒红的判据等于没有判据；但"静默跳过"更糟 ⇒ 必须留一行可数的 NOT-RUN。
- 顺手把 BACKLOG 41 的最后一半收了：**先量**（横幅正文在彩色带上 `light 亮0/暗2277`、
  `dark 亮2277/暗0`，四帧×两外观全部单边且方向正确），**再挂**方向断言与诊断行。
- 新开 **BACKLOG 43**：读下一次 CI 的 `TEXT_INK_FRAME` 行 —— `transparent=100%` 是没画，
  `0%` 且像素均匀是画了一块底色；两种的下一步完全不同。
- 数字：0 warning；701 例 / 27 skip / 0 失败；变异 M123–M131 重跑 9/9 CAUGHT。

## R29c · CI 绿了，而且那行诊断当场把 BACKLOG 43 答完

- 收口提交 `d5c79da`：**runner 上 701 例 / 29 skip / 0 失败**（两条依赖设置页的判据记 NOT-RUN）。
- 诊断行的读数：`px=720x540 scale=1.0 bpp=32 samples=4 bpr=2880 transparent=0.0% hist=0/0/0/0/0/0/1/99%`
  ⇒ ① 字节布局与尺的假设一致（排除"读错字节"）；② 透明率 0%（排除"没画"）；
  ③ 99% 像素在最亮一档 ⇒ **画了一块底色，内容一个字都没有**。本机同一张帧 `hist=0/0/0/1/0/0/1/97%`。
- **顺带量到一条谁都没说过的**：runner 是 **@1x** 截图（`scale=1.0`，本机 2.0）。
  这把 R27 那次 CI 红的解释换了：不是"平台把 `secondaryLabelColor` 解析得更淡"，
  而是半分辨率下细笔画根本进不了"最暗 2%"那一档。修法（同平台相对参照）不变，**原因已改写**。
- 我自己写的那条 NOT-RUN 守卫第一版**永远不会触发**（它判 `total == 0`，而 `total` 被
  `max(1, …)` 兜底）⇒ 记一条规矩：**跳过路径也要有正对照**，"看起来有记账"比没记账更危险。

## R29d · 收口之后又跑的一轮：暗档侧栏文字是黑字黑底，而我先用眼睛"看错了"

- 触发点是复核本身：我裁了 `settings-min-640x440-dark.png` 报"标签浅灰可读"。
  像素相反 —— 那一列最亮只比底亮 4，最暗是 (0,0,0)。**肉眼那条通道读的是期望，不是文件**（BACKLOG 46）。
- 量出来的事实（U-52）：九张 `settings-*` 暗档帧里，**未选中行**的标签与图标落在背景的错误一侧
  （`settings-shortcuts` 亮侧=0 / 暗侧=2647），**选中那一行两档都对**（亮侧 851）。
  亮档同一列全部正常 ⇒ 判别量是选中与否，不是页 / 帧宽 / 符号名。
- 十五臂复刻体（`.scratch/motion-audit-2/sidebar_appearance_r29d.swift`）**一臂都没重现**：
  绘制外观域 / orderFront / 嵌套 hosting+NSSplitView / 运行时翻外观 / 钉外观 / 显式 `.primary` /
  `Button{Label}+.plain` / 以及"嵌套 hosting view 装一列 Button"那一格（O、P）—— 全画对
  ⇒ 机制未定，**产品零改动**（D-089）。
- 仓库侧新加一条会红的账：`testDarkSettingsSidebarTextIsACountedBlindSpot`
  + `inkSideCounts`（整列按侧计数，尾墨尺在这里会漏 —— 白字把黑字挤出那 2%）。
  两个方向都会红：名单外冒出反侧墨 / 名单里不再冒（R18 材质名单同一族）。
  实测 `TEXT_SIDE_BLIND_SPOTS 9 of 9 settings fixtures`。
- 修掉取证工具自己的 bug：`sidebar_icons_r28.swift` 的 `modalColor` 把 pt 当 px，
  所有 `bg` 取自目标区域左上角 1/4 处 ⇒ 我据此下过的一条读数已作废并撤回。仓库判据无此问题（逐条核过）。
- **数字**：0 warning；**702 例 / 25 skip / 0 失败**（+1 条守卫）；脚本 72 passed；
  帧基线 102 / `CHANGED=0`（产品零改动，符合预期）；变异 **M132–M134 三支全 CAUGHT**、
  `RESTORE_CLEAN=yes`（`/tmp/r29d-mutation.log`）。
  25 条 skip 的构成：动效胶片 14 + 在屏交互探针 8 + 按压探针 1 + 实例守卫 1 + 浮层 1，
  全是环境门控。**这个数字不能跨轮比**：上一轮账本写的是 27，但没留构成 ——
  口径没记构成，差 2 条就查不动（BACKLOG 46 顺手补的一条）。

### R29d 的第二次 push：那条守卫在 runner 上红了，而它红的就是我上一轮写进账的那件事

`1f9ea34` 的 CI 红在 `testDarkSettingsSidebarTextIsACountedBlindSpot`（run 38461676256）：
runner 上九张设置帧的侧栏列**全部读到 0 个偏离像素** ⇒ 名单九条全"消失"、`judged = 0`。
这正是 BACKLOG 43 记下的现象（那一页在 runner 上是一块平涂底色），
而它证明我第一版守卫把两件相反的事读成了同一个 0：
**"这台机器拍不出这一页"** 与 **"我这把尺没压住字"**。

修法不是放宽断言，是加一条**与产品无关的判别臂**：同一张帧的内容区也按同样方式计数。
内容区有墨而侧栏没判 ⇒ 红，并指名去核坐标；两列都 0 ⇒ 整条 XCTSkip（显式，不是静默）。
M133（把尺的框缩到压不住字）在新结构下仍然红，且红在"尺没压住字"这句话上（本机复验：
`内容区读到了墨（308093 个偏离像素）… 是**尺没压住字**，不是环境问题`）。

## Round 30 · 侧栏暗档黑字的机制：那一列在 `NSAppearanceNameVibrantDark` 里解析颜色

- **换方法**：R29d 十五臂复刻体全画对 ⇒ 不再猜形状。给 `render` 加 `inspect:` 钩子
  （默认空实现，调用点零改动），在"已布局、外观已注入、未开画"时打印产品的 AppKit 树。
- **量到**：侧栏列的 `NSHostingView<...SidebarStyleContext>` 生效外观 = **VibrantDark**，
  内容区 = DarkAqua。九张 `settings-*` 帧逐帧如此。产品代码零改动（D-090 / U-53）。
- **没量到（写清是推论）**：vibrant 极性指望窗口服务器合成翻回来，而 `cacheDisplay` 不走合成
  ⇒ 帧是"合成前"像素。真机正常与否仍是人工批次 37.1 / 37.2。
- **名单改由前提决定**：`XCTAssertEqual(vibrantColumns, darkSidebarTextBlindSpots)` +
  `wrongSide ⊆ vibrantColumns` ⇒ 给那一列钉 darkAqua 把帧调好看会当场红。
- **本轮真实视觉审查按"先量后看"执行**：亮档 暗墨 18493 / 亮墨 0；
  暗档 亮墨 15797 + 暗墨 2843。裁图两档均与数字一致（上一轮眼睛报错的那处，这次对上了）。
- **数字**：0 warning；**703 例 / 26 skip / 0 失败**（+1 条永远记 skip 的诊断）；
  帧基线 102 / `CHANGED=0`（产品零改动，符合预期）；脚本 72 passed；
  变异 M132–M136 **5/5 CAUGHT**、`RESTORE_CLEAN=yes`（`/tmp/r30-mutation.log`）。

## Round 31 · 边界轮：没有第二条离屏取图通道（材质/vibrant/prominent 三处盲区只能真机）

- `CGWindowListCreateImage` 在 macOS 15 SDK 标 unavailable，替代要录屏授权 + 真上屏
  ⇒ R30 的"帧是合成前像素"**无法靠再写捕获器解决**。已写进 BACKLOG 40 / 45 的下一步与 §5.15。
- 同一支 spike 的四行读数按 **DID-NOT-RUN** 处理（对照组连底色都没画出来），没据此下结论。
- 自评 89（边界轮）。下一轮回到产品：BACKLOG 39 详情区左轴契约。

## Round 32 · 详情区左轴统一到 gutter（BACKLOG 39 收口 / U-54 / D-091）

- **产品改动**：新增 `View.detailReadableColumn()`，头部 meta / 渲染正文 / 原文正文三处统一走它。
  实测 spread **35.0pt → 0.5pt**（五块 × 亮暗两档，`DETAIL_AXIS` 行）。
- **新判据**：`testDetailAreaHasASingleLeftAxis`（五块各自贴 gutter ±2 且彼此差 ≤2pt）。
- **两条源码守卫改强**：从"DetailView 里有没有那个字符串"改成"调用点计数 ≥3 + helper 里仍有上限"。
- **本轮犯的尺错**：正文带起在 y=110 切掉了首行 ⇒ 假轴 41.5；按 `rows` 剖面重放后正确。
  教训与 M140 一起入账（**锚点过窄会把排版读成缺陷**）。
- **代价与退路**：宽窗口正文右侧留白变大；嫌空就抬 ch 上限，不许改回居中（D-091）。

### R32 换装本机（产品几何变了，必须真装真跑）

- `make bundle` → `✅ 时间剪史.app ready (ad-hoc signed, quarantine-free)`；
  `install_local.sh --yes --no-build` → `INSTALL_SHA_MATCH=1`、
  `INSTALL_RUNNING_PID=86576`（启动晚于安装，exe 路径逐字对上 `/Applications/时间剪史.app`）、
  `INSTALL_ENTRIES_BEFORE=103 → AFTER=103`（真存档没动）、运行时冒烟 `SMOKE_OK=1`、`INSTALL_RESULT=ok`。
- 旧包留在 `Documents/Codex_Project0_backups/before-local-20261014-045426`，退回命令脚本里已打印。
- **一次工具性教训**：第一次跑 `make bundle` 时报 `No rule to make target` —— 我在
  `ClipboardHistory/` 子目录里跑的（Makefile 在仓库根），而命令的退出码是 0
  （管道尾巴 `tail` 的退出码）。**后台退出码 ≠ 子进程真跑过**这条又应验一次：
  读输出、不读退出码。

## Round 33 · 说明段探针加天花板 + 通用页说明段归位（BACKLOG 34②③ / U-55 / U-56 / D-092）

- **判据侧**：`captionInkProbes` 每条从"只有地板"变成**两侧都钉**（`captionTierCeiling = 1.5`）。
  我上一轮放进去的两条设置页探针当场被它打回：**比值 3.67（亮）/ 1.89（暗）** —— 套的是标题与开关标签。
  框重放后 8 条 × 两档全部 **0.95–1.03**（热图三条、菜单栏两条本来就贴参照 ⇒ 回审通过）。
- **新尺**：`rowTierProfile`（说明档 / 标题档两堆）+ `textBands`（按行距并段）+
  真值表 `testRowTierProfileSeparatesCaptionFromTitle`（钉顺序与间隙：120/121 对 206/185，阈值 150 在中间）。
- **产品侧（U-55）**：通用页四组"开关 + 它的说明"，`SettingsViewLayout.captionGap = 3`，组间 8；
  讲 OCR 的那句挪回自己那颗下面。实测上缝 **12.0 → 7.0**（暗 11.5 → 6.5），下缝不变 12.0 / 11.5。
  判据 `testSettingsCaptionSitsCloserToItsOwnToggle`（三条 + 段数 ≥3 × 两档）。
- **修掉自己上一轮埋的**：NOT-RUN 判别臂装在了没有设置页帧的那张表上（永不触发的装饰 + 日志名撒谎），
  说明段测试反而没有 ⇒ CI 第一轮必红（R29d 同族第二次）。现在说明段测试有判别臂 **且** `judged ≥ 3`
  —— **判别臂不许把判据变成恒绿**。
- **U-56（新发现，未修，BACKLOG 47）**：菜单栏面板第一行的推荐理由被硬切成半字（墨到 `x=319.5` = 帧边界），
  而产品没给 `MenuBarExtra` 任何宽度约束 ⇒ 要么真机面板比 320 宽（切的是夹具），要么产品真会切。
  要先看真机（人工批次 39.1），R31 已定"离屏没有取图通道"。
- **验证**：全量 **707 tests / 29 skipped / 0 failures**、**0 warning**；
  帧基线 2 张（`settings-general` 亮/暗）随提交 `update`，复验 `CHANGED=0`；脚本 **72 OK**；
  变异 **M141–M147 七支全 CAUGHT**、`RESTORE_CLEAN=yes`（逐支读失败消息；M145 第一版预期写错，
  它实际红在①「这段说明不跟着任何开关」而不是段数，改预期后单跑复验）。
- **前几轮的 CI 收口**：`ab76562` / `efbafa6` / `1a27d59` 三条 run 全部 **success**
  （38466314575 / 38466675809 / 38466878342）—— 上一轮那个"watcher 退出时还在 in_progress"的悬账结掉。
- 自评 **90 / 100**（七维度见 `AGENT_VISUAL_ITERATION.md` Round 33）。

### R33 换装本机

- `make bundle`（在仓库根）→ `✅ 时间剪史.app ready`、冒烟 `SMOKE_OK=1`；
  `install_local.sh --yes --no-build` → `INSTALL_SHA_MATCH=1`、
  `INSTALL_RUNNING_PID=91740`（启动晚于安装，exe 路径逐字对上 `/Applications/时间剪史.app`）、
  `INSTALL_ENTRIES_BEFORE=103 → AFTER=103`、`INSTALL_RESULT=ok`、版本 1.4.8→1.4.8。
- 旧包留在 `Documents/Codex_Project0_backups/before-local-20261014-053500`。

## Round 34 · 菜单栏帧的资格（U-56 收回 / U-57 / D-093）

- **产品零改动**（帧基线 `CHANGED=0`）⇒ 本机已装的 R33 包就是当前产品状态，不需要重装。
- **U-56 收回**：R33 那句"产品的推荐理由被硬切成半字"量的不是产品。
  `MenuBarExtra` 全仓没有 `.menuBarExtraStyle(.window)` ⇒ 默认 `.menu` ⇒ 内容编译成真 `NSMenu`，
  而 `menubar-*` 帧拍的是离屏 `NSHostingView` 复刻；复刻里那一行在 320/400/520/720 四档下
  **都顶到帧边界**（320.0 / 398.0 / 518.0 / 718.5）⇒ 顶边是复刻的性质。
- **新规矩**：`menuSurfaceReplicaFixtures` + `testMenuBarFramesAreReplicasOfTheMenuSurface`
  （前提现读 `App.swift` / 名单≡由 `menubar-` 前缀推导 / 证据是顶边读数）
  ⇒ 这批帧**可判颜色档，不可判宽度、截断、对齐、命中区**。
- **U-57（R33 的 CI 红，run 38472213484）**：NOT-RUN 判别臂问的是"整帧有墨吗"，
  该问"探针所在那一竖条画出来了吗"。runner 上设置页内容列平涂而帧底色有墨 ⇒
  整帧那一问永远答"画得出来" ⇒ 三条设置页探针被红成"框贴到空白"。
  已改成 `columnIsDrawable(textInkPixels:)` + **正对照真值表**
  （`testNotRunDiscriminatorTruthTable`：blank=0 判"画不出来"、真实页=31890 判"画得出来"）。
  规矩：**判别臂要问的区域，必须就是这条判据自己要读的区域**。
- **新尺**：`trailingInkColumn`（左边界判对齐，右边界才看得见截断留没留痕迹）。
- **改口径先审计消费者**：`grep menubar- Tests/` 只有两条颜色档探针 + 一条帧名对账
  ⇒ 没有几何判据建立在这批帧上，需要撤的只是账本里那句话。
- **验证**：710 tests / 30 skipped / 0 failures、0 warning、脚本 72 OK、
  变异 **M148–M151 四支全 CAUGHT**、`RESTORE_CLEAN=yes`。自评 **90 / 100**。

## Round 35 · 说明段全覆盖 + 探针的颜色域资格（BACKLOG 34② 收口 / U-58 / U-59 / D-094）

- **产品零改动**，帧基线 `CHANGED=0`；`captionInkProbes` 8 → **16 条**，
  设置窗口 6 个分区各至少一处 + 详情头部 meta，全部从"说明档带"量位置。
  读数 16 × 两档 = 比值 **0.93–1.18**，地板 0.8 / 天花板 1.5 都留着余量。
- **覆盖规则**（新）：分区清单从 `SettingsCategory.allCases` 推导 ⇒ 新增分区没人点名就红。
- **一条 ESCAPED 的变异换出一条机制**（U-58）：M155 第一版（行内 meta 降到 `.tertiary`）全绿，
  查下去是**侧栏那一列活在 `NSAppearanceNameVibrantLight` / `…VibrantDark` 里**，
  拍到的是 vibrancy 合成前的像素：侧栏 `.primary` 行标题最深 113，与旁边 `.secondary` 一样深，
  而设置页内容列同样 `.primary` 的标签是 38。⇒ 撤掉那条探针，位点记 BACKLOG 48。
- **新判据 `testProbesDoNotSitOnVibrantColumns`**：40 条读数逐条问颜色域，
  说明段表零容忍、控件表必须点名登记（R21 那条侧栏按钮从此不判产品）。
- **口径修正（U-59 / BACKLOG 49）**：CI 的帧捕获步骤是 **report-only**
  （`continue-on-error` + `|| true`），runner 上现有 4 条红被吞
  （材质盲区名单在 runner 上是"黑带消失"、正对照帧底行 0% 墨、两张 `settings-privacy-excluded` 被捕获失效闸门锁住）。
  ⇒ 账本里"CI 上真的跑"只成立到"跑了"。下一轮（R36）做"**红必须有名字**"：
  已知画不出来的守卫登记成 NOT-RUN，工作流改判"未登记的红色 == 0"。
- **R34 的 CI 结论**：run 38473962277 **success**，runner 日志里
  `CAPTION_NOT_RUN × 3`、`CAPTION_JUDGED 5/8`、`DISCRIMINATOR_ARM_A ✓`、`ARM_B_NOT_RUN`
  —— 那条本机永远走不到的分支第一次在真环境按预期走了一遍。
- **验证**：712 tests / 31 skipped / 0 failures、0 warning、脚本 72 OK、
  变异 M152–M156 五支全 CAUGHT、`RESTORE_CLEAN=yes`。自评 **89 / 100**（<90 ⇒ 继续）。

---

## Round 36 · CI 的红必须有名字（BACKLOG 49 收口 / U-59 收口 / U-60 开 / BACKLOG 50 开 / D-095）

- **闸门落地**：新增 `scripts/ci_capture_gate.py` + 工作流硬门那一步。三条退出码规矩：
  未登记的红 >0 ⇒ 红；日志里一条 `Test Case` 结论都没有 ⇒ 红（"没跑"不是通过）；
  判出绿 < `--min-passed 15` ⇒ 红（整批退回 `XCTSkip` 也是一条红都没有）。
  红有两个来源：`error: -[类 方法] :`（断言行）与 `Test Case … failed`（崩溃/超时只有结论行）。
- **正对照是逐字日志**：`scripts/tests/fixtures/r36_runner_capture.log`（run 38473962277 那 257 行，
  `gh api .../jobs/115559876687/logs` 取的）。它当场纠正三件事：那 4 条红属于 **1 个用例**
  （`4 failures` 是断言数）；settings 族在 runner 上 18 张**全部** 90.6–95.9% 未绘制（本机 20.8–78.8%）；
  runner 上**一处黑带都没有**（本机 9 处）⇒ "黑带消失了"那条守卫在那边恒红。
  旧账 BACKLOG 43"List 族在 runner 画不出来"是错的，已就地改。
- **机器能力前提拆成三条**（`CaptureCapability.measure` 纯函数 + 5 臂真值表，用两台机器各自的实测读数）：
  `settingsFamilyIsBlank` / `bandsSeenHere` / `rulerSeesBottomEdge`，
  反例臂：单帧空白、尺全 0、族只一张 —— 都不许被"整族画不出来"顺走。
- **U-60（本轮真正的产出，看图看出来的）**：`bottomInkFraction` 的参照点是**左上角那一个像素**，
  它读的是色差不是墨。51 张帧双参照：15 张假 100%（sidebar 四帧×亮暗 + detail 亮色七帧），
  `settings-privacy-light` 反向漏报（0.1% vs 真实 6.7%）。黑区实测在 pt 371..436.5、下沿距帧底 83pt
  ⇒ 那 100% 连"黑带被数成墨"都不是。⇒ R22 那条正对照从写下起就是假的，
  `contentMustFit` 十条判据十四轮没有有效正对照。**本轮只改话术 + 记账 + 留绊线**，尺留给 R37。
- **验证**：713 tests / 31 skipped / 0 failures、`swift build` 0 告警、脚本 72→83 全绿、
  帧基线 `CHANGED=0 / 102`（产品零改动）、变异 M157–M168：11 CAUGHT + M168 本地无判别力（下一次 CI 判）、
  `RESTORE_CLEAN=yes`。自评 **90 / 100**。
- **仍未验证**：闸门在 runner 上第一次真跑是否绿（这正是这一步存在的理由；红了会指名是谁）。
  人工批次 40（设置六页最底行 / 侧栏选中行真机 / 最小尺寸下的半行）+ 39.1–39.3 仍待用户。

---

## Round 37 · 底行墨这把尺改对（U-60 收口 / U-61 / BACKLOG 50 收口、51 开 / D-096）

- **参照点**：`bottomInkFraction` 从"左上角那一个像素"改成**底行自身的每通道中位数**；
  三张合成图钉住（角点不同 0% / 半行 50% / **整行同色 0% —— 写下来的边界**）。
- **正对照从找改成造**：`row-clipped-control`（同一颗行 + 58pt 外框 + `.clipped()`），
  实测 10.8% / 12.5%，线 5%；并加**配对守卫** `mustFit 上限 2% < 正对照下限 5%`
  （两条线一旦交叉，判据与正对照互相取消）。
- **第二处**：尺读的是 raw rep 而不是落盘 PNG（同一帧 3.4% vs 43.4%，方向相反）⇒ 改成读产物，
  `content-min` 那块药丸帧当锁（M171）。`blackBandHeight` 仍读 raw rep（要的是 alpha）。
- **U-61**：R35 起 CI 一直红（7d0a89b / 68027fc failure），红在 `testProbesDoNotSitOnVibrantColumns`
  —— runner 上 settings 族整体没画出来时那棵树答"内容列压在 vibrant 里"。
  判据侧补机器前提 + `judged ≥ 20`；流程侧立规矩："CI 绿"只写读过的那一次（BACKLOG 51）。
- **撤掉** R36 那条"尺活着"的机器前提：那种情况正是判据最该红的一次，不该登记成未运行。
- **新知识**：18 张帧底行真压着东西（含 `settings-recommendations` 42.4%、`settings-privacy` 27.2%
  确实切成半截 —— 滚动区正常，不进 mustFit，但从此可数）；`row-*` 的 2.5% 是行自己的下边缘，
  **别为放过它去抬 mustFit 那条 2%**。
- **验证**：714 tests / 29 skipped / 0 failures、`swift build --build-tests` 0 告警、
  帧基线 102→104 且 `CHANGED=0`、脚本 83 全绿、变异 M169–M174 六支全 CAUGHT、`RESTORE_CLEAN=yes`。
  自评 **91 / 100**。
- **待 CI 验证**：闸门那一步这次仍然没跑到（第 5 步红在前面）；本轮把那条恒红的资格判据修好，
  下一次 CI 才第一次真正判到 `Capture gate`。

---

## Round 38 · 判据不许拿一台机器的读数量另一台机器（U-62 / D-097）

- **闸门第一次跑到并指名**：`CAPTURE_GATE_CASES passed=22 skipped=9 failed=1 有名字的红=1 NOT_RUN=40`
  ⇒ `CAPTURE_GATE_RESULT=fail`，红的是 R37 我自己写的那把锁（不是产品，也不是机器不行）。
- **锁换形状**：`content-min 底行 ≥20%`（本机 43.4% / runner **9.3%**）⇒ 换成恒等式
  "判据读数 == 从落盘 PNG 重算的读数"，104 张全对；M175 证明换回 raw rep 照样咬得住。
- **地板从表推导**：`judged ≥ 20` 在 runner 上恰好 20/40 压线 ⇒ 改成
  `judged == 可判条数` + `可判条数 ≥ 16`；M176 把每条都放行 ⇒ 红在"对象快被清空了"。
- **两台机器的诊断清单各留一份**：`BOTTOM_EDGE_INK` 本机 18 张 / runner 30 张，
  差值全在 `content-*` ⇒ "底行压着东西"是排版量，不是判据该问的东西。
- **验证**：714 tests / 29 skipped / 0 failures、`swift build --build-tests` 0 告警、
  帧基线 `CHANGED=0 / 104`、脚本 83 全绿、变异 M175 / M176 全 CAUGHT、`RESTORE_CLEAN=yes`。
  自评 **90 / 100**。
- **CI 已读**：闸门第一次真跑并**绿**：run 38487277143（job 115612…）整作业 `completed success`，第 7 步 `Capture gate` 打出 `CAPTURE_GATE_CASES passed=23 skipped=9 failed=0 有名字的红=0 NOT_RUN=40` ⇒ `CAPTURE_GATE_RESULT=ok 红=0`；第 5 步（主测试）也过了 —— 资格判据的机器前提在 runner 上成立（放行 20 条、判成 20 条，派生地板 `judged == 可判条数` 成立）。
  这是 U-61 那条规矩第一次被执行：推完 → 读逐步 conclusion → 才写这句话。
- **下一步（R39）**：目标里那句"全部状态"里，**禁用态**是唯一一帧都没有的一档 ——
  产品里 4 处 `.disabled(...)`（SettingsView 325/611/613/639），先问"哪一处在真机上真的可达"，
  可达的那几处补成对帧 + 两条判据（可辨、禁用后仍可读），不可达的那几处按"无作用就写明理由不加"处理。


---

## Round 39（R39）· 禁用态与失败回执 —— 已交付，CI 待读

- **产品**：macOS 12 的开机启动路径加了"写完读回"（`verifyApplied`），
  不一致抛 `loginItemNotApplied` ⇒ 那句"开启失败，请稍后重试"第一次会出现。
  比对拆成纯函数，四格真值表在本机（macOS 14+）真的跑得到。
- **帧**：+4（`settings-general-login-unsupported` / `-failed` × 亮暗）⇒ **108 张**，基线同 commit update。
- **判据**：`testDisabledToggleAndFailureReceiptAreVisible`（三臂，两臂成对）+ 2 条说明段探针（18 条）。
  读数：禁用后标签 亮 13.76→1.82（0.13×）/ 暗 11.43→2.29（0.20×）；回执 1.01 / 0.95 参照。
- **方法账**：负对照从"读 0 墨"改成**差值**（布局会随内容移动 ⇒ 跨帧比同一块有没有墨是错的）；
  变异电池的"预期红"必须实测（第一版两支推理错，靠"红得不对"这个计数揪出来）。
- **盲区名单**：两张新帧进 `darkSidebarTextBlindSpots` ⇒ **11 of 11**：
  设置族每一张帧的暗档侧栏文字都结构上量不到（D-090 同一机制）。
- **不做的**：`SettingsView:611/613/639` 三处 `.disabled`（产品恒注入 ⇒ 不可达）；
  失败回执不单独染红（会与 `ReceiptLine` 分裂成两种语言）。
- **新开两条**：BACKLOG 53（`ReceiptLine` 的 `.contentFade` 没供电，要**供电**不是撤声明）、
  BACKLOG 54（`.disabled` 淡到 1.82:1，若哪天 `isSupported` 真的会 false，别用它表达禁用）。
- **验证**：718 tests / 29 skipped / 0 failures、0 告警、脚本 83 全绿、
  变异 M177–M182 六支全 CAUGHT、`RESTORE_CLEAN=yes`。自评 **91 / 100**。
- **换装本机**：`make bundle` → 装到 `/Applications/时间剪史.app`（md5 与新包一致）→ 冷启动 `SMOKE_OK=1`。**顺带 A/B 查出新缺陷 U-64 / BACKLOG 55**：机器上已有同 bundle 实例时，守卫中止的那次启动在盘上**一行日志都不留**（header、启动标记、守卫自己那句"本次启动取消"全丢），而 `launch_smoke.py` 把这件事报成"启动失败"。两半各修各的，见 BACKLOG 55。
- **R39b（同一轮的第二次提交）**：CI 第一次跑就红 —— run 38494383404 第 5 步 12 条红全部来自本轮新写的
  `testDisabledToggleAndFailureReceiptAreVisible`：runner 上 `SettingsView` 内容列是平涂（BACKLOG 43），
  于是那条判据在那里读到对比度 1.00 / 墨 0 / 差值 0，**从写出来那刻起就恒红**。
  修法不是放宽线：补「这一台画不画得出这一页」这一问（`settingsDrawability`：三张全有 ⇒ 判；
  三张全无 ⇒ 显式 `DISABLED_STATE_NOT_RUN`；只有 1–2 张 ⇒ 红），并把这条走不到的中间格拆成纯函数
  打桩测一次（`testSettingsDrawabilityTruthTable` 四格 + 变异 M183 / M184）。
  覆盖账从 `judged == 2` 换成 `judged + notRun == 2`。本机读数一字未变。
  **这是同一族第三次犯**（R35 资格判据恒红、R37 量级地板 9.3%、R39 这条）⇒ U-65 / BACKLOG 56：
  新写一条读像素的判据，落库前先回答「这一台画不出来时它输出什么」，且那个回答本身要能被咬。
  自评从 91 下调到 **89**（曲线 32 轮，均值 91.0）。
- **CI 已读（两次，逐步结论）**：第一次 run 38494383404 第 5 步红（12 条，全来自本轮新判据，runner 上设置页内容列是平涂）；R39b 修完再推，run 38496845658 **整作业 success**（12m53s）：第 4 步 0 告警、第 5 步 Swift tests ✓、第 6 步帧捕获 ✓、第 7 步闸门 `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=5 ⇒ CAPTURE_GATE_RESULT=ok`、第 13 步帧基线（夹具集闸）✓、第 15 步 `SMOKE_OK=1`。`testDisabledToggleAndFailureReceiptAreVisible` 在 runner 上 passed（两次，2.8s / 3.6s）—— 它与 R39 第一版读的是同一批帧与同一批矩形，第一版红、这一版过 ⇒ 走的是 `noneDrawn` 那一支（判据里除它以外没有别的通过路径）。**一条没搞清的口径**：闸门这一轮报 `NOT_RUN=5`，而 R38 那轮同一步报的是 40 —— 本轮只可能**多**出标记（两条新探针 × 两档 + 未运行的两档），不可能少 35 条。两种解释都没证：① 计数口径（闸门数的是含 `*_NOT_RUN` 的**行数**，见 `ci_capture_gate.analyse`）在 R38 之后被某次改动换了来源；② runner 上有一批 NOT-RUN 打印路径本轮不再走到。⇒ 记 BACKLOG 57：不许把这两个 40 / 5 当同一把尺比较，先复现再解释。
- **下一步（R40）**：BACKLOG 53 那条要么供电要么撤声明（先量一次"加了 `withAnimation` 之后
  帧序列到底有没有中间态"，量不到就写清"机器量不到"并交人工批次）；
  另把主窗口里剩下的"错误态"逐处点名（`copyFailed`、写盘失败、OCR 失败）看有没有第二处静默失败。


---

## Round 40（R40）· 复制失败必须挡住自动粘贴 —— 已交付，CI 待读

- **普查**：把 R39 那句问法（"失败了界面说了什么"）复用到全仓，15 条清单落
  `.scratch/motion-audit-2/silent-failures-survey.md`，逐条标"已修/已核/未核"。
- **产品（D-099）**：`CopyThenPaste.decide` 一道闸门 + 一句走已有横幅通道的回执。
  修的是"**做错的事**"：浮层回车 / 菜单栏点一条时复制失败仍会切前台并注入 ⌘V，
  目标应用粘出来的是用户剪贴板里**上一条无关内容**，而界面一句话都没有。
- **判据**：4 条（管线级 2 / 真值表 1 / 接线守卫 1）。`testCopySuccessIsNotBlockedByTheNewGate`
  是 M186 逼出来的 —— 第一版断言太弱，闸门方向反了也能全绿（正常路径被挡掉没人喊）。
- **帧**：+2（`content-with-copy-failure-notice` 亮暗）⇒ **110 张**，同 commit update 基线。
  文案从产品生产者 `CopyThenPaste.decide` 取，不手写 ⇒ 有人把它拼长，帧自己会红。
  新帧撞上材质盲区闸（`blackBandPt=66`）：对过两张姐姐帧读数后确认是同一处侧栏伪影，登记进名单。
- **换装本机**：`make bundle` 0 告警 → `/Applications/时间剪史.app`（md5 与新包一致）→
  冷启动冒烟 `SMOKE_OK=1` → 应用在运行（pid 20846）。
  **一条自我否定**：我试图用 `pbcopy` 验「采集没被改坏」，两次都「没采集」，
  而 `pbpaste` 回读为空证明是**我的仪器不对** —— agent shell 的 pbcopy 不通向 GUI 会话的剪贴板。
  ⇒ 账本里不写「已验采集」，这条只能由用户做（批次 42.1 / 42.3）。
- **验证**：723 tests / 29 skipped / 0 failures、0 告警、脚本 83 全绿、
  变异 M185–M188 四支全 CAUGHT、`RESTORE_CLEAN=yes`。自评 **90 / 100**。
- **新开三条**：BACKLOG 58（回执里嵌系统英文原文，读不懂）、59（保存失败静默，未复核）、
  60（普查其余 12 条全部"未核"，不许直接当缺陷修）。
- **CI 已读（逐步结论）**：run 38501481700 **整作业 success**（12m52s），17 步全 ✓ ——
  第 4 步 0 告警、第 5 步 `Executed 723 tests, 36 skipped, 0 failures`、第 7 步闸门
  `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=26 ⇒ ok`、
  第 13 步帧基线夹具集闸 `ADDED=0`（110 张对得上）、第 15 步 `SMOKE_OK=1`。
  36 skipped（本机 29）= runner 上多 7 条环境门控的在屏探针/胶片。
- **下一步（R41）**：BACKLOG 58 —— 把 `SystemEventsPasteKey.reason(fromStderr:)` 那套
  "错误码 → 人话 + 下一步"的成例接到复制这条路上（真值表 + 原文留日志不留界面）；
  顺带复核 BACKLOG 59 那一条（保存失败到底哪几种可达）。

---

## R41 · 上一轮那句回执，在三种最常见的失败里说了假话（第 43 轮 / U-67 / D-100）

- **本轮修的正是 R40 自己交付的东西**：`ClipboardWriter.swift` 的真实顺序是
  `:67` 校验 → `:71` `clearContents()` → `:78/:97/:99` 写入失败 ⇒
  四种已知失败里有**三种**发生在清空之后，而 R40 的回执固定说"剪贴板里仍是原来的内容，没有被替换"。
  用户照这句话去 ⌘V，粘出来的是空或上一条无关内容。另一半：`localizedDescription` 直出，英文原文进横幅。
- **修法**：`ClipboardWriteFailure { message, clearedPasteboard }` + `classify`（未分类**保守**当作已清空，
  因为猜错方向的代价不对称）；`HistoryStore` 存这个值，`clipboardWriteErrorMessage` 退化成计算属性；
  `decide` 按事实分两支说话；系统原文改道 `LifecycleDebugLogger`。**BACKLOG 58 收口**。
- **两条既有契约测试被改掉**（它们钉的就是 `message == error.localizedDescription` 这个缺陷形状），
  改后加 `XCTAssertNotEqual` ⇒ "退回裸描述"这件事本身会红。这是为改契约而改测试，不是为了变绿。
- **帧 110 → 112**：补上 R40 缺的那一臂 —— `content-min-with-copy-failure-notice`（**600×440 = 产品最小窗口**，
  数字取自 `App.swift:12` / `WindowConfigurator:94`）。两行完整、`NOTICE_ACTION offset=+0.0`、
  亮 `ratio=12.98 ink=24.5%` / 暗 `11.54 / 27.8%`。
  顺带量到 `blackBandPt` 66 → 0 的机制：**横幅把选中行整行顶出可视区，而详情区还在显示它**
  ⇒ 新开 **BACKLOG 61**（本轮只登记读数，不动产品），且新帧**不进**材质盲区名单（登记前看了帧）。
- **BACKLOG 59 已逐行复核（只核不修）**：两处 catch 只写 debug 日志，
  `lastSaveError|saveFailure|didFailToSave|onSaveFailure` 在这两个文件 **0 命中**，
  `HistoryStore` 那 6 条回执通道里**没有一条是存盘失败** ⇒ 这次没有现成通道可复用，先定形状再动。
- **换装本机（11:53）**：`install_local.sh --yes --no-build` ⇒ `INSTALL_RESULT=ok`、
  `INSTALL_SHA_MATCH=1`（`9a36a103…` → `a261a308…`）、旧 pid 20846 优雅退出、
  `SMOKE_SAW_START=True / SMOKE_OK=1`、新 pid 26795、**存档 103 → 103 条**。旧包留在备份目录。
- **验证**：724 tests / 29 skipped / 0 failures、`swift build` 0 告警、
  闸门 `passed=695 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、
  基线同 commit update 后复跑 `CHANGED=0 / ADDED=0 / MISSING=0`、脚本 83 全绿、
  变异 M189–M193 五支全 CAUGHT。自评 **91 / 100**。
- **needle 第三次犯同一个错**（U-65 那一族）：M189/M193 的预期红消息按 `decide` 猜，实际红在 `classify`
  ⇒ 第一遍 `红得不对=2`。⇒ 下一轮把"needle 与实际消息不符 ⇒ DID-NOT-RUN、不注入"钉进电池脚本。
- **本轮超出 ≤4 文件**：非台账 7 个（产品 4 + 测试/夹具 3），原因是修复整条在生产者链上，拆开必红。
  已在第 43 轮正文里记账，下一轮恢复。
- **CI 已读（逐步结论）**：run **38508965110** / job 115672825962 **整作业 success**（12m2s），
  15 个步骤全 ✓ —— 第 4 步 0 告警、第 5 步 `Executed 724 tests, with 36 tests skipped and 0 failures`、
  第 7 步闸门 `passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=8 ⇒ ok`、
  第 11 步 `Ran 83 tests`、第 13 步夹具集闸 `COMPARED=112 / MISSING=0 / ADDED=0`
  （`check` 的退出码**只由 missing 决定** —— 多帧与变帧交给人判断，这是脚本里写明的口径）、
  第 14 步对上一版发布 `CHANGED=62 / ADDED=50 / MISSING=6`（报告型）、第 15 步 `SMOKE_OK=1`。
  **本轮第一次看懂了第 13 步那个 `CHANGED=112`**：`check` 也逐帧比 sha，
  而 runner 是 @1x、本机基线是 @2x ⇒ **每一帧都"变了"** —— 所以那一门不看这个数字，只看帧名。
  NOT_RUN 在 run 之间继续漂（40 → 5 → 26 → **8**）⇒ BACKLOG 57 的说法（`tee` 那份日志不可靠）再添一个数据点。
- **下一步（R42）**：**回到动效本体**。流畅度 13/20、动效细节 12/15 已连续三轮没动，
  因为 R39–R41 都在修"它说不说话、说得对不对"。候选按优先级：
  ① BACKLOG 53（`ReceiptLine` 的 `.contentFade` 没有 `withAnimation` 供电 —— 要么供电要么撤声明）；
  ② BACKLOG 61（横幅插入后选中行的可见性，先判值不值得动）；
  ③ 变异电池那条"needle 不符 ⇒ DID-NOT-RUN"的自检。

---

## R42 · 回到动效本体：三处回执的淡入，两句是死的、一句推不动（第 44 轮 / U-68 / D-101）

- **复核把 BACKLOG 53 改窄也改准**：原账"全文 0 个 `withAnimation` ⇒ 三处瞬间插入"是按关键字数的。
  逐调用点量完：两处**死声明**（导出反馈 `:555`、导出/导入历史 `:619`）、
  一处**缺半个键**（排除名单 `:489` 只有那份持久化字符串 ⇒ 名单没变时推不动）、
  一处**本来就有电**（清空回执 `:659`，而且它不是 `ReceiptLine`）。
- **本轮最值钱的是查出尺的粒度**：仓库里已有同族守卫
  `testNoUnexecutedTransitionClaimsAcrossViews`，但它报"**整个文件**没有驱动"
  —— `SettingsView.swift` 有 9 条动画键 ⇒ 这些死声明在它底下永远隐身。
  新判据把这一族降到"调用点 + 门控状态名"，旧那条留着管更粗那一层。
- **修法**：产品 +3 行（两条 `.animation(contentFade, value: 门控 == nil)` + 排除名单补一条键）。
  元组键被编译器否掉（Swift 元组不 conform `Equatable`）⇒ 是"再加一条"而不是"合成一条"。
  约定写进 `ReceiptLine` 定义处注释，边界记 BACKLOG 63（判据只认 `.animation(value:)`）。
- **验证等级要如实**：稳态 112 张帧逐字节不变（`CHANGED=0`，这条同时是"没改到布局"的证据），
  而淡入活在 presentation 层 ⇒ `cacheDisplay` 量不到、胶片探针进不了设置窗口。
  所以本轮是"**源码已接 + 结构已判，产物未量**"，人眼判据交批次 44.1–44.4，`流畅度` 这一维**没涨分**。
- **两条新账**：BACKLOG 62（"导出反馈数据"同一件事既弹模态又发行内回执，失败那条又直出
  `localizedDescription` ⇒ U-67 同一族、另一个出口）、63（新判据只认一种驱动写法）。
- **仪器的两条新账（都进 D-101）**：needle 不许抄 `Set` 的打印（顺序不稳定 ⇒ M198 第一遍"红得不对"），
  只认 `if let` 的门控扫描会**看不见** `if 布尔` 那一类调用点。
  另：44.4 那一格我第一版写的是"减弱动态下淡入该消失"，读回 `MotionCatalog.shape(for:reduceMotion:)`
  才发现 `contentFade` 走的是 `break`（规则是"滑→淡、缩放→落位、时长不归零"）
  ⇒ 预测必须从代码来，不能从"我觉得应该"来 —— 这条已经犯过很多次，今天差点又犯在人工清单里。
- **验证**：726 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
  `passed=697 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、脚本 83 全绿、
  变异 M194–M198 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。自评 **92 / 100**。
- **CI 已读**：run 38511570267 **整作业 success**（12m45s，15 步全 ✓）—— 第 5 步 `Executed 726 tests / 36 skipped / 0 failures`、第 7 步闸门 `有名字的红=0 NOT_RUN=8 ⇒ ok`、第 13 步 `COMPARED=112 / MISSING=0 / ADDED=0`、第 15 步 `SMOKE_OK=1`。
  **第 10 步是本轮唯一一条动效数字上的好消息**：`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` ⇒ `MOTION_FLOOR_OK=4/4` —— 覆盖率地板在 runner 上四条全判到（本机同一把尺只判 1/3）。它不证明回执在淡，但它把「CI 上看不到动效」这句老话削掉了一半：能被看见的那四件在跑，回执这一族量不到是**尺的通道**问题（presentation 层），不是没人跑。
- **下一步（R43）**：① BACKLOG 62 那片代码一次判完（回执留行内还是留模态 + 原文进日志）；
  ② 或 BACKLOG 61（选中行滚进可视区）先问用户接不接受；③ 电池脚本补"needle 只许来自 --measure"。


---

## R43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文（第 45 轮 / U-69 / D-102）

- **复核把"一个出口"扩成三个**：`SettingsView:177`、`SettingsWindowController:94`、`:104`
  全在把 `error.localizedDescription` 拼进界面，而这三条路上的错误类型都不是 `LocalizedError`
  ⇒ **U-67 那一族 R41 根本没收口**，只是收了一条。
- **修法**：新增 `Utilities/ReceiptWordings.swift`（`FeedbackExportReceipt` + `ArchiveTransferReceipt`），
  三处 catch 改成「原文进日志 + 界面用映射器」；导出反馈那条**同时**存在的模态 `.alert` 与
  `showExportAlert` 删掉（仓库其余三处回执都是行内）。
- **两条"顺带"才是本轮最值钱的**：
  ① `receipt-line` 那张帧从 R14 起画的是**产品根本没说过的一句话**（全仓 grep 无此文案）
     ⇒ 新增夹具文案判据 `testHarnessNeverHandWritesReceiptCopy`；
  ② 换成真文案之后 `contentMustFit` 当场红两张（底行 18.4% / 20.2% 有墨）
     ⇒ 那张帧**一直在裁自己**，56 → 72pt 才放得下。
- **BACKLOG 64 被一条真问题挡住**：`ContentView` 五条 `NoticeBanner` 的驱动是派生键
  `noticeSignature`（bitmask）⇒ 按名字匹配的判据会把它们全部误报成没电。
  推广之前要先让判据会把派生键展开成它读的那几个状态。新开 BACKLOG 65（× 顶对齐 vs 横幅动作居中）。
- **验证**：733 tests / 29 skipped / 0 failures（+7）、`swift build` 0 告警、
  闸门 `有名字的红=0 NOT_RUN=0`、帧基线 112（改名 `MISSING=2 / ADDED=2` 同 commit update，复跑全 0）、
  脚本 83 全绿、变异 M199–M205 七支全 CAUGHT（needle 全部实测抄来 —— R42 立的流程第一次真跑）。
- **换装本机（12:48）**：`INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`（`a5c52cbe…`）、
  新 pid 34026、存档 103 → 103、`SMOKE_OK=1`。
- **CI 待读**。
- **下一步（R44）**：① BACKLOG 64 的派生键展开（做成了才能把调用点级守卫推广到 NoticeBanner / 热图）；
  ② BACKLOG 59 的存盘失败通道形状（一次性横幅 vs 常驻只读标记）；③ BACKLOG 61 等人工批次 43.4 的回答。

---

## R44 · 判据先学会读派生键（第 46 轮 / U-70 / D-103）

- **本轮改的是尺，产品零改动**：`ContentView:32` 用一条**派生键** `noticeSignature`
  推五条 `NoticeBanner`，R42 那把按名字匹配的尺读不懂 ⇒ 直接推广会把五条**全部误报成没电**
  （而它们确实有电，R22 量过）。⇒ 先给判据加一跳展开（`drivingStates`），
  设计主点是**读不懂时既不放行也不报错**：只增不减，退回按名字匹配。
- **新增**：`testNoticeBannerCallSitesArePoweredByTheirDerivedKey`（读数
  `BANNER_DRIVE 调用点 5 个、键 1 条、展开后状态 13 个、无驱动 0 个`）
  + 派生键展开的 5 格真值表 + 4 个纯函数。
- **假阴性的靶**：变异 M207 —— 从签名 body 里删掉一条 ⇒ **只有那一条红**。
  这一支在，"展开"才不是万能通行证。
- **BACKLOG 64 只做了一半**（写清楚，别当成推广完了）：热图那两处是
  `if 布尔 { … } else { … }` 的**分支**形状，扫描器现在只认"组件调用点 + `if let`"。
- **本轮不换装**，理由记账：没有任何"只有装上新包才看得见"的东西；112 帧逐字节不变。
- **验证**：735 tests / 29 skipped / 0 failures、0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿、
  变异 M206–M209 四支全 CAUGHT。自评 **93 / 100**。**CI 待读**。
- **下一步（R45）**：① BACKLOG 64 的后半（分支门控）或 ② BACKLOG 59 的存盘失败通道形状；
  ③ R42/R43/R44 三轮都在加固尺与措辞，`流畅度` 已经五轮没涨 ——
  下一轮优先做**能产生像素证据**的那类（分带抓帧 / 能进设置窗口的胶片通道），
  否则就承认这一维的上限并把话写死。

---

## R46 · 地板会报"掉了谁、为什么"了（第 48 轮 / U-72 / D-105）

- **本轮改的是 CI，产品零改动**：`Motion coverage floor` 从"只问 `judged<2`"换成
  `scripts/motion_floor_gate.py` + 一份登记表。来历是 R45 读 CI 时发现 R44 那次
  `4/4 → 3/4`（`notice-banner-dismiss` not-run）**整步仍然绿**，而理由行被 `head -24` 挤出了日志。
- **设计主点**：**红不红取决于登记，不取决于读数**。
  会随采样漂的臂判到不红、判不到也不红（否则恒红 → 守卫被删）；
  "跑完却没有结论行"从 `exit 0` 改成红（旧版那张免检牌）。
- **理由不是猜的**：本机真跑一遍 `MotionFilmstripTests` 产出 `/tmp/motion-local.log`，
  逐字收成正对照夹具 ⇒ 新闸门跑真日志必须红，且红在 `BAD_REASON` + `UNDERCOVERED` 两格。
- **不判帧数**：`MOTION_SUMMARY <arm>=<帧数>` 由采样相位决定（R2 实测 2/3/2）。
- **撞出一条新的（BACKLOG 68，R47 的靶）**：`testHeatmapFadeIsNotVisibleToThisRuler`
  本机报红，读数 `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— 两臂峰值完全相同，
  只有帧数不同 ⇒ 它在拿自己宣布过不可靠的量做判据。**红的是尺，不是产品。**
- **验证**：脚本自测 83 → **101** 全绿、变异 M216–M222 七支全 CAUGHT、
  Swift 侧零改动（742/29/0 与 116 帧沿用 R45）、**本轮不换装**（理由记账）。
  R45 的 CI 已逐步骤读过：15 步全 ✓、`Executed 742 / 36 skipped / 0 failures`、`SMOKE_OK=1`。
  自评 **94 / 100**（与 R45 持平；曲线不涨是因为这轮抬的不是画面）。**R46 的 CI 待读。**
- **下一步（R47）**：① BACKLOG 68（热图淡入那条 A/B 换成时长轴）—— 它是 `流畅度` 那一维
  唯一一条"看起来能判、其实判的是采样"的判据；② 若新闸门在 runner 上红在 `BAD_REASON`，
  先把真理由抄进登记表再往下走；③ BACKLOG 64 的后半（分支门控）仍在。


---

## R45 · 悬停那一圈被画出来对账（第 47 轮 / U-71 / D-104）

- **本轮是"能产生像素证据"那一类**（上一轮的下一步）：把单格画法抽成
  `DailyCopyHeatmapCell(isHovered:)`，于是"悬停长什么样"第一次可离线渲染、可逐档量、可看。
  产品侧只是搬家：**既有 112 张帧逐字节不变**（`CHANGED=0`）。
- **新增 7 条判据 + 4 张帧**（`heatmap-cell-strip-still` / `-hover`，亮暗各一）。
  读数：描边带 36.10–75.50/255（地板 18 = 最小读数一半）、带外 0.00、
  **悬停 ÷ 数据全幅度 = 0.46–0.75**（这条轴本轮新立，M213 画两遍 ⇒ 1.16 会红）。
- **本轮查出并修掉的两个自身错误**：① 描边带用"方框减角块"切掉了真描边 ⇒ 报**假 ✗**，
  改用圆角矩形 SDF；② 夹具取 `prefix(3)`（最老三列全空档）⇒ **帧存在 ≠ 被摄对象在帧里**，
  改 `suffix(3)` 并补一条夹具自检（M214/M215 专打它）。
- **重构搬走两条 R9 时代的源码守卫**：`DailyCopyHeatmapTests` 按 `func cellView` 取区域，
  画法一搬就双双报红。**一条断言都没放宽**，只把它们各自指回现在的主人，
  并给区域助手补了"同名成员取到哪一个"（文件里现在有两个 `var body`）。
- **判断记账**：`0.55` 与 `Color.primary` 本轮**都不改** —— 前者被量了且站在正确一侧
  （1× 那臂低 20–25%，但最弱仍是恰可察觉台阶的九倍），后者换强调色会在同色系格子上糊成一片。
- **验证**：742 tests / 29 skipped / 0 failures、0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿、
  帧基线 112 → 116、变异 M210–M215 六支全 CAUGHT。自评 **94 / 100**。**CI 待读**。
- **换装本机**：`INSTALL_RESULT=ok`，新包 sha `8753ffa722a09701…`（staged 与 installed 逐字节相同），
  旧实例 pid 34026 优雅退出后新 pid 41193 在跑，存档条数 103 → 103，`SMOKE_OK=1`。
  备份在 `~/Documents/Codex_Project0_backups/before-r45`。
- **下一步（R46）**：① BACKLOG 66（动效覆盖地板需要一个会红的形状）—— 它现在是"掉了没人报"；
  ② BACKLOG 64 的后半（分支门控）；③ `流畅度` 六轮没涨，若下一轮仍做不了能进设置窗口的胶片通道，
  就在最终报告里把这一维的上限写死，别再每轮空转一格。


---

## R47 · 那条 A/B 判的是采样，不是淡入（第 49 轮 / U-73 / D-106）

- **靶是上一轮自己撞出来的**：R46 为拿像素证据跑了动效胶片套件，`testHeatmapFadeIsNotVisibleToThisRuler`
  在本机报红 —— 而它报红的理由是**它自己用的轴不可靠**（两臂峰值 0.226 / 0.226 完全相同，只有帧数不同，
  帧数正是这个文件写着「会随采样相位漂」的量）。
- **改法**：判据抽成纯函数 `fadeVisibility(elapsedOnA:elapsedOnB:elapsedOff:peakOn:declared:interval:)`，
  换成时长轴 + 四个门槛（下限 0.3×声明 / **上限 声明+2×间隔** / 归因看两遍里较短的那个 /
  A/A 不一致 ⇒ `.inconsistent` 只打印不红）。真值表 12 格。
- **上限是读数逼出来的，不是设计出来的**：本机反复抓到 `258 / 259 / 260 / 265 / 307ms` 的变化段，
  而这条过渡**声明只有 160ms** ⇒ 那不是淡入。没有上限，判据会把它读成「尺子终于看见了」，
  然后催我把场景放进 `Scenario.all()` —— **把探针的毛病当产品进步**。加上限后 3/3 稳定「看不见」。
- **`流畅度` 这一维今天写死了**：离屏 `cacheDisplay` 抓模型树，纯 opacity 交叉淡活在 presentation 层
  ⇒ 这条通道对淡入的可见性是 0。抬它要换通道（真屏抓帧 / presentation 采样），不是再改判据。
  连续三轮 94 不体面，但比在曲线上虚涨一分诚实。
- **本轮看图看出的两条新账**（不是读代码读出来的）：
  BACKLOG 70 = 读数函数名叫 `changedRun…` 但它的取法**不要求连续**，两段变化之间隔着静止帧也会被
  首尾相连算成一段 ⇒ 那正是 258–307ms 的一个候选解释（**假设，未证**）；
  BACKLOG 71 = 暗色帧里图例最低那一格几乎与背景同色，而**梯子相邻两档能不能被分开**这件事从来没有一条判据
  ——「1 次的那天」如果和「0 次的那天」看着一样，这张图就在骗读数的人。
- **顺手抓到自己写的解析器的错**：为了「曲线必须从台账生成」新写的 `curve_from_ledger.py`
  第一版正则不认 `Round 29d` 这种带字母后缀的轮次，于是**静默少一轮**、均值跟着错。
  是拿它算出来的 38 轮对上报里写的 39 轮才发现的 —— 判据是「两处独立数字对不上」，不是「看起来没事」。
- **验证**：743 tests / 29 skipped / 0 failures、闸门 `红=0 NOT_RUN=0`、脚本 101 全绿、
  `swift build` 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`（本轮 `Sources/` 未动）、
  变异 M223–M229 七支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。自评 **94 / 100**。**CI 待读。**
- **本轮不换装**：`Sources/` 一个字节没动，装了旧包和装新包界面上不会有任何差别。
- **下一步（R48）**：① BACKLOG 70 的连续性 —— 把 `changedRunElapsedMilliseconds` 改成真正的「run」，
  并用两波带空隙的形状钉住它（它同时给 BACKLOG 69 一个答案）；② BACKLOG 71 的梯子档间可分辨性；
  ③ 读 R46/R47 的 CI，特别是新地板闸门第一次在 runner 上的读数。
---

## R48 · 那条"演了 266ms 的淡入"是钟停了，而"看不见"是我写错的（第 50 轮 / U-74 / D-107）

- **本轮最重要的一行是撤回**：R11 起台账里写着"离屏 `cacheDisplay` 对纯 opacity 淡入可见性 = 0"。
  本轮第一次给这条 A/B 补上条带图，第 3 帧是**半透明中间态**（空态那行字与整块日历叠在一起）
  ⇒ 这条通道**看得见**这条淡入，只是不每次都抓得到。"没抓到"被写成"看不见"，
  是把探针的占空比当成了产品的极限 —— 与"把没跑写成跑过"同一族，方向相反。
- **我上一轮的假设也错了**：R47 我在源码注释里写"265ms 只能来自两波被跨度算法并成一段"。
  补上 per-run 打印之后真形状是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`
  —— **一段连续的**变化，段内有一次 **260ms 的抓帧空档**。缺的不是连续性，是**分辨率轴**。
- **改了什么**：① 撒谎的名字改回 `changedSpanElapsedMilliseconds`（行为不变）；
  ② 新建 `contiguousChangedRun(s)`（含峰值那一段 + 段内最粗采样）；
  ③ `fadeVisibility` 从两态改三态，新增 `.clockTooCoarse`（0.5×声明那档，沿用 `judgeMotion` 口径，
  排在一致性门**之前**）；④ `看不见` 分支文案改成"今天没抓到"；⑤ 三臂各出一张条带；
  ⑥ 调用点守卫钉四件事（段来源 / 臂归属 / 时长轴 / 分辨率轴有没有传）。
  本机今天的判定因此从"看不见"变成 **`判定=钟太粗`**（`MOTION_NOT_RUN=clock-coarse-in-window`，不红）。
- **新开 BACKLOG 73（性质比 69 硬）**：那次 260ms 的抓帧空档发生在**用户刚按下 ⌘C 的那一刻**。
  候选是首次布局 182 个格子、`DailyCopyLedger.record` 主线程侧的工作、或去抖落盘回主线程。
  目标里明令"采集路径上不许有同步磁盘写"，所以这条要单独量，不许猜着修。
- **本轮自己错四处，全部由数据顶回来**：真值表期望心算错（308 vs 实测 316）；
  守卫前两版都在读邻居（数词频、固定取两行 —— 同一支变异 M237 顶红了两次）；
  打印用了绝对时钟（`731797829–731797842`，跑一遍才看见）；
  **注释里写了一个没量过的数**（"约 130ms"是拿 266 ÷ 2 估的，实测是 260ms 的一次空档）。
  外加电池自己的一处错：M239 第一版把 `// MUTANT` 加在条件行尾，**顺手注释掉了 `{`**
  ⇒ 编译失败 ⇒ 电池如实报 `BROKEN-MUTATION`（这个码存在的意义就在这一格）。
- **验证**：真值表 15 + 8 格、M230–M239 十支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）、
  745 tests / 29 skipped / 0 failures、闸门 `红=0 NOT_RUN=0`、脚本 101 全绿、
  `swift build` 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`。**本轮不换装**（`Sources/` 未动）。
  自评 **94 / 100**。
- **R47 的 CI 已读**（run 38530030589，success）：`motion suite exit: 0`（R46 那次是 1）、
  `executed: 25`、`MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss`、
  新地板闸门第一次在 runner 上给出 `MOTION_FLOOR_OK=3/4 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`；
  离屏闸门 `passed=25 skipped=9 failed=0 NOT_RUN=24`（BACKLOG 57 那个漂移今天仍是 24，未解释）。
  runner 上那条淡入 A/B 的读数是 **开臂 249 / 227ms**（声明 160ms）——
  与本机同一族形状，所以 R47 那道上限门在 runner 上真的挡下了一次误判。
  R46 那次红的正是这条 A/B 的旧写法（`testHeatmapFadeIsNotVisibleToThisRuler]' failed`），
  本轮的靶因此有 runner 证据，不是我推出来的。
- **下一步（R49）**：① BACKLOG 73（那次 260ms 空档是谁占的，用"设置窗口没打开"的对照臂去量）；
  ② BACKLOG 71（热图梯子相邻档可分辨性，暗档第 1 级 vs 空格子）；
  ③ BACKLOG 72（其余调用点还在跨度上，先数真胶片有没有"段内掉回地板以下"）；④ 读 R48 的 CI。
---

## R49 · 目标里那句"采集路径不许同步写盘"，40 轮以来没有一条判据在管（第 51 轮 / U-75 / D-108）

- **本轮最难看的一条事实**：阶段一的目标里明写着"采集路径上不许有同步磁盘写"，
  而 `Tests/` 里**没有任何一条判据在管它**。实现是对的（`recordCopy` 只排去抖），
  但"对"不可证 —— 把同步写盘塞回去，748 条用例一条都不会红。
  新增 `CapturePathWriteBudgetTests`（3 条）之后，M240 真的把它塞回去试了一次：红了。
- **两条判据各管一件事**：结构判据（复制之后临时目录**一个文件都不许多** + "去抖到期必须出现"的对照组）
  管"有没有写盘"，与机器快慢无关；时长判据（40 个样本，中位与 p95 分开）管"不写盘但算了多久"。
  只要计时判据会在慢机器上恒红、快机器上恒绿；只要结构判据会漏掉"没写盘但卡 200ms"。
- **门槛从实测推导**：本机三次跑 `median=0.59 / 0.56 / 0.63ms`、`p95=1.46 / 1.28 / 1.34ms`、
  `max=3.08 / 2.27 / 1.50ms` ⇒ 中位门槛 10ms（实测的 17 倍，且在可感知线 ≈100ms 之下），
  p95 门槛 40ms（4×）。Runner 若顶红，按 R38 的规矩是**门槛错**不是产品错。
- **BACKLOG 73 结案**：R48 那次 260ms 抓帧空档**不在产品的采集链上**（产品侧 `add` 中位 0.6ms、
  盘上不多文件），它是探针自己对新生子树的首帧 `cacheDisplay` —— R11 在同一份文件里记过
  "新窗口的头两次要 260–340ms 一帧"，量级与位置都对得上。旁证：开臂 `粗260`、**关臂 `粗6`**。
  剩下的真问题另开 **BACKLOG 74**（淡入第一帧的真实成本，现在的读数混着冷缓存不能当产品数用）。
- **R48 的 CI 已读**（run 38536051202，success）：`Executed 745 tests / 36 skipped / 0 failures`、
  离屏闸门 `passed=25 skipped=9 failed=0 NOT_RUN=24`、
  地板闸门 `MOTION_FLOOR_OK=4/4 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`（judged 从 R47 的 3/4 回到 4/4）。
  **但 `motion suite exit: 1`** —— 这一步是 report-only，所以红的是一条被吞掉的用例：
  ```
  MOTION_NATIVE row-insert 开 帧数=4 峰值=0.052 采样≈28ms
  MOTION_NATIVE row-insert 关 帧数=1 峰值=0.061 采样≈18ms
  MOTION_NATIVE row-move   开 帧数=1 峰值=0.047 采样≈28ms
  MOTION_NATIVE row-move   关 帧数=1 峰值=0.047 采样≈15ms
  testNativeRowMoveIsVisibleToTheRuler]' failed (2.682 seconds)
  ```
  这是**这台机器第一次真的跑完这条判据**（以前每次都是 `app-not-active` 而 skip）。
  同一次运行里 `row-insert` 看得见（开 4 帧 / 关 1 帧），`row-move` 开关两臂一模一样 ⇒
  **探针能看见行动画，而"移动"这一条没被看见**。新开 **BACKLOG 75**，
  它是阶段二以来第一条"可能是产品少做了一段动画"的候选（不是尺的问题，因为同一卷里 insert 是好的）。
- **本轮自己错一处**：先写的 `XCTAssertEqual(samples.count, Self.sampleCount)` 恒真
  （断言右边就是驱动循环的常量），设计 M243 时才看见 ⇒ 改成与取值无关的地板 `minimumSampleCount = 20`。
- **验证**：3 条判据 + 真值表 7 格、M240–M244 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）、
  748 tests / 29 skipped / 0 failures、闸门 `红=0`、脚本 101 全绿、0 告警、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、`Sources/` 与提交前逐字节相同（M240 改过，已还原）。
  **本轮不换装**。自评 **94 / 100**（涨的那一分在七个维度里没有能诚实收下它的位置，记在文字里）。
- **下一步（R50）**：① **BACKLOG 75**（行移动到底有没有动画：本机复现 + 归因，
  这次要防的是"把它当成探针的锅"——同一卷里 insert 是被看见的）；
  ② BACKLOG 71（热图梯子相邻档可分辨性）；③ BACKLOG 72（其余调用点还在跨度上）；④ 读 R49 的 CI。
---

## R50 · 报红之前先问：探针做的事，产品做了吗（第 52 轮 / U-76 / D-109）

- **靶**：R49 读 CI 时撞见 `testNativeRowMoveIsVisibleToTheRuler` 在 runner 上第一次出结论就是红
  （`row-move 开 1 帧 峰值 0.047 / 关 1 帧 峰值 0.047`），而**同一卷里** `row-insert 开 4 帧 / 关 1 帧`。
- **先抓到的是探针**：move 臂在宣布一次 `moveRow` 之前把六行文案全改了（`·已挪`），
  而产品的移动分支只 `moveRow`、不改文案（文案变化走 `plan.reloads`）
  ⇒ 两臂像素差里混进与动画无关的"文字变了"，那次红**不能算产品的结论**（U-76）。删掉 rename。
- **结论分三态**：`nativeMoveVerdict` ⇒ `动了 / 瞬移 / 采样错过`。
  以前只有"帧数 ≥2 否则红"，把"两臂形状一致"（产品瞬移）与"两臂都 1 帧但峰值不同"（今天量不了）
  混成同一种红。形状判据用**绝对值**：开臂变得比对照还少也是"说不清"。
- **没有把红改成 not-run**：它有名字、有读数、有同一卷的阳性对照。
  R36 的规矩是"红必须有名字"，不是"红必须少"。登记的是第三种形状（`native-move-sampling-missed`）。
- **真实视觉审查**：零产品改动、116 帧逐字节不变；本轮看图看的是 runner 两行读数的并排关系。
- **验证**：真值表 7 格（第 ② 格就是 runner 的真读数）、M245–M248 四支全 CAUGHT
  （`未被抓到=0 红得不对=0 还原不干净=0`）。
  **全量/闸门/帧基线没有独立跑过一遍**：R50 之后紧接着是 R51，验证跑在合并后的树上
  （750 例 / 29 skip / 0 failures / 0 告警 / 116 帧不变，原文见 R51 那一节与 `/tmp/r51-full.log`）。
  这一句是**记账不是结论** —— R50 单独那个提交从没被全量判据扫过，CI 跑的是 tip。
  自评 **94 / 100**。**CI 待读：本轮的修法只有 runner 能验收**（本机进程无法激活 ⇒ 每次 skip）。
- **下一步（R51）**：① 读 R50 的 CI，看 `MOTION_NATIVE_MOVE 判定=` 落在哪一格（三种可能各自怎么走，
  已写在 BACKLOG 75 里）；② BACKLOG 71（热图梯子相邻档可分辨性）；③ BACKLOG 72（其余调用点还在跨度上）。
---

## R51 · 那条判据红得不正确：它测的是后台写，不是主线程写（第 53 轮 / U-77 / D-110 / BACKLOG 76）

- **靶**：R49 立的"采集路径不许同步写盘"判据在全量跑与 CI（run 38538371464）都红。
  对账之后：**红得不对** —— 多出来的是 `history.json.sb-XXXX`，后台 `saveQueue` 的原子写临时文件。
  目录快照分不清同步与异步 ⇒ 判据测错了对象（U-77）。
- **修法**：注入的串行写队列**先堵起来**再 `store.add` ⇒ 堵着不许出现 `history.json` / `daily-copy.json`，
  `blocked.signal()` 之后两个都必须出现（对照组）。没有对照组，"没写盘"能靠"没接上盘"来绿（M250 试了，红）。
- **新增一条**：480 条的库 + 堵住的队列 ⇒ 主线程只剩这条链时一次复制多久。
  四次实测 `median=2.34 / 2.43 / 2.47 / 2.49ms`、`p95=2.56 / 2.64 / 3.39 / 5.91ms` ⇒ 门槛 20ms（最差 median 的 8 倍）。
  旧那两条只测了几条记录的小库，而这条链的成本随库大小增长（同一次跑 0.55 → 2.47ms）。
- **两条判据互不覆盖（M249 实测）**：真把写搬回调用线程之后，行为判据红，
  时长判据打印 `add 用时=2.54ms` **仍然绿** ⇒ 小库上同步写只值 2ms。这句话写进门槛注释，
  防止下一个人以为时长那条也在管同步写。
- **本轮自己错三处**：① 新加的前提断言写成 `fullArchiveEntries - 20` ⇒ 自适应阈值恒真，
  设计 M251 时才发现（与 `sampleCount`/`minimumSampleCount` 同一族，上一轮刚记过一次）；
  ② 注释里写"这条测的是整库快照"，M253 实测 median 只涨 0.5ms ⇒ 快照只占 1/5，
  注释与失败消息都改了，分段量开成 **BACKLOG 76**。
- **真实视觉审查**：零产品改动、116 帧逐字节不变。看的是暗档热图（`heatmap-cell-strip-still-90x140-dark.png`），
  并用 `heat_ladder_preview.py` 把"分不出来"变成数：**暗档"空格子→第 1 档"Δ=4**、亮档同一格 Δ=13、
  暗档第 1→2 档 Δ=13，全部低于 `perceptibleBand255 = 18` ⇒ BACKLOG 71 有数了，R52 去做判据（会改像素，帧基线要 update）。
  **这张表在同一轮里错过位**：脚本第一版按亮度排序认台阶，而 `empty` 是灰（`primary`）、四档是蓝（`accent`），
  两档外观亮度方向相反 ⇒ 次序排乱，先写进台账的"15 / 13"是错的（已改，脚本现在按像素数指纹配对、配不上就中止）。
  这是本轮**第三处**自己错：数从读数来了，但"哪个读数属于哪个台阶"没对账（同一族：整窗像素把效果归给错的元素）。
  **（R52 又补一刀）**那张表的**轴**也用错了：亮度差 4 的那一步，B 通道差 30 ⇒ "分不开"这个结论作废，见第 54 轮。
- **验证**：M249–M252 四支全 CAUGHT、M253 按设计绿；`swift build --build-tests` **0 告警**；
  全量 **750 tests / 29 skipped / 0 failures**；离屏闸门 `passed=721 skipped=29 failed=0 NOT_RUN=0 红=0`；
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`；脚本 **101 全绿**。**不换装**。
  **动效覆盖地板闸门本机没有输入**（motion 场景判据要 `CLIPBOARD_HISTORY_UI_MOTION=1` 才跑，
  全量跑里是 skip）⇒ 本机那一门的 `MOTION_FLOOR_NO_RESOLVE` 是喂错日志，不是产品退化；真结论等 runner。
  自评 **94 / 100**。
- **R50 与 R51 合并验证**：全量那一遍跑在两轮的树上（R50 单独那个提交没有被全量扫过，CI 跑 tip）。
- **下一步（R52）**：① **BACKLOG 71**（相邻档 Δ 判据 + 抬 `empty` 或抬第 1 级，改像素要 update 帧基线）；
  ② 读 R50/R51 的 CI：`MOTION_NATIVE_MOVE 判定=` 落在哪一格、`MOTION_RESOLVE_SUMMARY` 的 not-run 名单；
  ③ BACKLOG 72（其余调用点还在跨度上 —— 已有 `.scratch/motion-audit-2/answer_backlog_72.py`，
  它自检复现了夹具的 135ms vs 45ms，缺的是带 `CLIPBOARD_HISTORY_UI_MOTION=1` 的真胶片日志）。
---

## R52 · 覆盖率地板第一次在 runner 上红，红的是"我的登记旧了"（第 54 轮 / U-78 / D-111 / BACKLOG 77、78）

- **靶**：R50/R51 推上去之后 CI 连红两次，都在 `Motion coverage floor`：
  run 38543090198 `NO_RESOLVE`（整族零读数），run 38543812477
  `BAD_REASON notice-banner 的理由是 clock-coarse-in-window，而登记过的是 无`。
- **闸门说的是事实，旧的是登记**：R46 那句"runner 上四次全部判到"已被两次实测推翻
  （最粗 76ms vs 声明 150ms；本机这一臂一直是 `premise-not-visible`）
  ⇒ `notice-banner` 改成 `must_judge=false` + 放行那两个理由，note 写死 run 号与毫秒（D-111）。
- **放宽必须留证据**：新增自测 `testRelaxedArmsMustCiteARunId` ——
  任何 `must_judge=false` 的臂，note 里没有 run 号或夹具路径就红。没有出处的放宽 = 测试红。
- **红必须有名字**：`NO_RESOLVE` 之后新增 `MOTION_FLOOR_SKIPS`，逐条打 `Test skipped - <原因>`。
  CI 那一步只 grep `MOTION_NOT_RUN=`，而 XCTest 层 `XCTSkipUnless` 的中文原因不带这个前缀
  ⇒ 整族缺席那种红以前**说不出为什么**。
- **不红不等于不说**：新增 `MOTION_FLOOR_THIN`（非红）—— 横幅两臂同场缺席时打一行，指向 BACKLOG 77
  （150/120ms 的过渡 vs 段内最粗 73–101ms 的每帧成本 ⇒ 两台机器今天都分辨不了）。
  这是 R36（红必须有名字）与 R39（恒红的守卫会被人删）之间的折法。
- **放宽的副作用被自测抓住，不是被我抓住**：地板 3→2 之后 `UNDERCOVERED` 再也无法单独红
  （任何 must_judge 臂缺席都会先撞 `BAD_REASON`）——`test_ci_report_selftest` 的 `under_covered`
  那一格当场失效。换成只有地板能抓的形状：`judged=1/4` 而 not-run 名单只登记两条横幅臂
  ⇒ **`judged` 与名单不自洽**（判据说谎），并用 `REDS=1` 钉住"只有这一条红"。
- **撤回一句用错轴的话**：R51 的"暗档 0 次 vs 1 次只差 4/255"是 Rec.709 **亮度**；
  那一步实际是灰→蓝的**色相**翻转（B 通道 41→71，差 30）⇒ 结论作废，
  BACKLOG 71 改成"先把判据的轴换对，再谈要不要改数值"。同一张表我在这轮里错过位两次
  （一次归位、一次轴），都属于"只用亮度判两态 = 用错轴"那一族。
- **验证**：脚本自测 **101 → 105**（`Ran 105 … OK`）、变异 **M254–M259 六支全 CAUGHT**
  （`红得不对=0 还原不干净=0`，电池跑完自己复跑一遍确认全绿）、
  闸门对本机真日志 `/tmp/r51-motion.log` ⇒ `THIN + OK=2/4 + REDS=0`、exit 0。
  产品零改动、Swift 判据零改动、116 帧不变 ⇒ **不换装**、不需要 `frame_baseline update`。自评 **94 / 100**。
- **CI 待读**：下一次运行看 `MOTION_FLOOR_SKIPS` 有没有把 38543090198 那次的原因说清楚
  （BACKLOG 78 的结案条件），以及 `MOTION_NATIVE_MOVE 判定=` 是否终于出现（BACKLOG 75）。
- **下一步（R53）**：① `MOTION_NATIVE_MOVE` 那行打印要挪到 `requireAppWasActive` **之前**
  （现在两臂读数打了、结论行被 skip 挡在后面 ⇒ runner 跳过时永远看不到三态结论）；
  ② BACKLOG 71 按色度轴重做判据；③ BACKLOG 72 的迁移（本机 3 卷已答"从没出现"，还欠 runner 卷）。
---

## R53 · 结论行挡在 skip 之后，等于每次跳过都把它删掉（第 55 轮 / U-79 / D-112）

- **靶**：R52 读 CI 时发现两次运行都有四行 `MOTION_NATIVE`、**零行** `MOTION_NATIVE_MOVE 判定=`。
  原因是 R50 把结论 `print` 放在 `requireAppWasActive` 之后 ⇒ 闸门一关，连"今天判没判"都没了证据。
  **R50 要消灭的含糊，被 R50 自己的排版重新造了出来。**
- **修法**：读法与责任分开 —— 三态结论挪到两道 skip **之前**，`XCTFail` 留在**之后**，
  打印尾部补一句"这一行只说读数怎么读，产品结论要过闸门才算"。
  新增顺序守卫 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`（结论行在 / 闸门在 / 顺序对）。
- **顺手挖出的更一般的坑**：`region(in:named:)` 用 `contains` 找声明行 ⇒
  会先命中**守卫自己**那行（守卫必须写下被守卫者的名字），区域于是变成守卫自己的函数体。
  最坏的不是红，是**部分通过**：三条断言里两条在读守卫自己写的字面量。
  改成按行首 `hasPrefix` 匹配。这是"扫自身源码要先摘掉守卫自己"那一族的第四次。
- **撤回一句数**：R51 写进台账的"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"用错了轴 ——
  那一步是灰(`primary`)→蓝(`accent`)的色相翻转，B 通道差 30。
  `heat_ladder_preview.py` 现在同时打 Δ亮度与 Δ各通道最大差；BACKLOG 71 的第一件事改成"把轴换对"。
- **验证**：变异 **M260–M263 四支全 CAUGHT**（`红得不对=0 还原不干净=0`，电池还原后自己复跑=全绿）；
  全量 **751 tests / 29 skipped / 0 failures**；**编译 0 告警**
  （全量日志里那 10 行 `warning:` 是系统 CoreData 运行时噪声：AddressBook 的 `NSXPCStore`，
  不是编译告警 —— 这句是实测，不是推断）；离屏闸门 `passed=722 skipped=29 failed=0 红=0`；
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`；脚本 105 全绿。**不换装**。自评 **94 / 100**。
- **电池自己的教训**：锚点数必须在全跑之前先验一遍 —— 第一版 M261 的锚点在文件里出现 3 次，
  跑到它才中止，前面两次三分半的构建白烧。
- **CI 待读**：下一次 runner 运行看 ① `MOTION_NATIVE_MOVE 判定=` 落在哪一格（BACKLOG 75 的 a/b/c），
  ② 若整族又没读数，`MOTION_FLOOR_SKIPS` 有没有说清原因（BACKLOG 78）。
  **R51 更正那一次 run 38544734947 已读**：`success`，且 `MOTION_FLOOR_FACTS judged=4/4 not-run=-`
  ⇒ 横幅两臂在同一条 runner 上四次运行给出 `4/4 / 2/4 / 3/4 / 无读数` —— 这是 BACKLOG 77
  "漂移而不是坏了"的直接证据，登记放宽与 THIN 都因此站得住。
- **下一步（R54）**：① BACKLOG 71 按**色度轴**做相邻档判据（先判不改数值能不能过，过就不改像素）；
  ② BACKLOG 72 的迁移（本机 3 卷 + runner 卷都答"从没出现"之后）；③ BACKLOG 77 的三条候选路选一。
---

## R54 · 相邻档第一次有判据，而它判的是我用的轴（第 56 轮 / BACKLOG 71 结案 / U-80 / D-113）

- **靶**：BACKLOG 71（R47 挂到现在）。R51 我"量出"暗档 0 次 vs 1 次只差 4/255，
  下一步本应是抬 `empty` 或抬梯子第 1 级 —— 一次会改像素、还会让 126 个空格子一起变响的产品改动。
- **答案：梯子没错，我的轴错了。** `empty` 走 `primary`（灰）、四档走 `accent`（蓝），
  那一步差的是**色相**：亮度轴 2.16，B 通道 30。
  新判据取**逐像素最大通道差**，16 条读数（4 对 × 2 外观 × 1×/2×）**全部过地板 18，最小 30.00**
  ⇒ **产品数值一个没改，帧基线不需要 update**。
- **用错轴的代价不是"数不准"，是"去做一件不该做的事"**：按亮度轴改，我会把一张没病的图改响。
- **尺子的夹具坏过一次，被真值表抓住**：`flatRep` 第一版用 `setColor(_:atX:y:)` 上色，
  两幅"不同色"的图读出 **0.00**（整数格式位图上那条 API 不落地也不报错）⇒ 改成直接写 `bitmapData`。
  没有"只有 B 差 30 必须读出 30 与 10"那一格，这条判据会全绿地量着一片空气。
- **一条与 R45 相反的实测**：整格填充**对尺度不敏感**（1× 与 2× 逐条相同）；
  R45 那句"1× 比 2× 低 20%–25%"只成立于 1pt 描边。以后引用要带范围。
- **验证**：真值表 8 格、变异 **M264–M268 五支全 CAUGHT**
  （M264 改产品令牌 0.18→0.06 会红；M265 把轴换回均值会红 ⇒ "不用改产品"这个结论有牙）；
  全量 **753 tests / 29 skipped / 0 failures**、编译 0 告警、离屏闸门 `红=0`、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本 105 全绿。**不换装**。自评 **94 / 100**。
- **CI 已读**：R52 的 run 38547820163 `success`，`MOTION_FLOOR_FACTS judged=4/4 … REDS=0`；
  同一条 runner 上横幅两臂六次是 `4/4 / 2/4 / 无读数 / 3/4 / 4/4 / 4/4` ⇒ BACKLOG 77 的"漂移"有账。
  R53 那一次 run 38549020323 待读（要看 `MOTION_NATIVE_MOVE 判定=` 是否终于出现）。
- **一条自我记账**：R45–R54 **连续十轮 94** 不是稳定，是同一件事没做完 ——
  `流畅度` 13/20 与 `动效细节` 14/15 的失分点从 R42 起没动过，每轮都被尺子的问题截走。
  **R55 回到动效本体**：BACKLOG 77 三条候选路里选一条真的做出来（首选"把抓帧每帧成本降下来"，
  因为它同时解 74/75/77 三条）。
- **下一步（R55）**：① BACKLOG 77 落地一条（降 `Grabber` 每帧成本：按 1× 拍还是降采样，先 spike）；
  ② 读 R53/R54 的 CI；③ BACKLOG 72 的迁移（本机 3 卷 + runner 卷都答"从没出现"）。
---

## R55 · 那条"最粗 97ms"第一次有了归因，而真读数把两档版打回来了（第 57 轮 / BACKLOG 77 收窄 / U-81、U-82 / D-114）

- **靶**：BACKLOG 77 三条互斥的修法（缩捕获 / 慢动作夹具 / 交给人眼），依据全是同一句
  "事件段内最粗 Nms"。N 是混合量，而我在 R54 的台账里写过"根因是抓帧器" —— **没量过**。
- **量了**：`Grabber` 逐帧计时 ⇒ 本机三遍，主窗口那几卷**抓帧中位** 38.7–49.7ms，
  同一批胶片的**整卷中位间隔** 43–44ms（**事件段内最粗** 95–97ms —— 两个数不是一回事）
  ⇒ **一个采样间隔≈一次抓帧 + 一次等待**。粗钟 not-run 行现在带 `归因=…（解释=NN%…）`。
- **第一版分档被真读数证伪**：97ms 间隔 / 抓帧最慢 87.9ms 落在余量外 1.1ms，两档版报成"不是抓帧的锅 ⇒ 先别动捕获尺寸"，
  而它解释了 91% ⇒ 改成三档 + 未量档，并把比例本身打进日志。**这一格是本轮最值钱的一格。**
- **建议也有判据了**：面积那条测量 全视图 中位 **40.2ms**、横幅带 中位 **8.4ms**、小块 中位 **3.1ms** ⇒ 端到端 12.3–13.0 倍（三遍）/ 面积 29.8 倍 = **子线性**（地板 ≈3ms）。
  BACKLOG 77 由此收窄成"走路 a"，1× 预计 41.7→≈11ms（**推算**，R56 落地要自带实测 before/after）。
- **看图**：dismiss 胶片第一行的横幅那一条 —— 帧 0/1 满不透明、**帧 2 半透明**、帧 3 起没了。
  淡入在演，只是"只看得见一格"；而一格中间态**分不清淡出与布局塌陷** ⇒ 56.1 仍等人答。
- **新账 U-82 / BACKLOG 79**：同一条命令本机三遍（18:45 / 18:58 / 18:59）里有一遍 `print` 全丢、stderr 正常 ⇒
  BACKLOG 78 那次 CI 无读数从此有本机复现（1/3），而我刚建的归因就住在这条通道上。
- **验证**：真值表 30 格 + 接线守卫 4 格 + 面积 3 档；变异 **M269–M276 八支全 CAUGHT**
  （第一遍 7/8：M276 因为守卫在自己的消息文本里读到被搜的串而逃逸，改成按 `func tick()` 区域搜后 CAUGHT）；
  全量 **756 tests / 32 skipped / 0 failures**、编译 0 告警、
  116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本全绿。**不换装**。自评 **94 / 100**。
- **CI 已读**：R53 run 38549020323、R54 run 38550490674 均 `success`，
  `judged=4/4 … MOTION_FLOOR_REDS=0`，R54 另有 `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0`、
  `Executed 753 tests, with 36 skipped` ⇒ 连续两次满覆盖。
- **下一步（R56）**：① **BACKLOG 79 落地**（读数同时写文件：让 `MOTION_FLOOR_NO_RESOLVE` 有真东西可判）；
  ② BACKLOG 77 路 a 真做（1× 抓帧）并带 before/after 实测；③ 读 R55 的 CI。
---

## R56 · 读数有了第二条通道，第一次跑就救回 54 行（第 58 轮 / BACKLOG 79 加固 / U-83 / D-115）

- **靶**：R55 给 skip 行加完归因才想起来——那些读数走的 stdout **已被观察到整次失效**
  （CI run 38543090198、本机 18:58）。一条会消失的通道不该同时是判据的唯一来源。
- **做了什么**：44 处 `MOTION_*` 全部改走 `emit`（stdout + 与胶片同目录的
  `motion-readings.log`，第一次整份重写、之后追加）；CI 那一步取**并集**并打
  `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`，两条都空时打 `MOTION_READINGS_FILE_ABSENT=1`。
- **当场兑现**：加固后第一遍本机 = **stdout 2 行 / 文件 56 行**。
  没有这一轮，那 54 行（含每一条 not-run 的理由）又会被当成"今天没跑"。**本轮唯一重要的数。**
- **变异替我做了一次设计评审**：第一版是"以文件为准（换掉 stdout）"，
  写 M285 时才发现文件也可能只写一半 ⇒ 换掉会扔掉唯一活着的证据，
  地板接着红在 `MISSING_KEY` —— 把"修通道"做成"造新红"。⇒ 并集。
- **守卫自带正对照**：M281（清空扫描列表）在没有正对照时会绿着通过。
  另记一次翻车：M278 第一次红在**写错的理由**上（上一遍的旧文件让"末尾两格"不匹配）
  ⇒ 判据顺序改成"先判这一遍的 marker 在不在，再判它在不在末尾"。
- **仍未证实**：为什么丢。已知只丢子进程 stdout、stderr 与写盘不丢、三次 0/全/2 行。
  BACKLOG 79 结案条件收窄成"查机制"（下次 N≠M 时做集合差，看丢的是不是同一个前缀段）。
- **验证**：守卫 5 格、CI 自检 motion 9 个形状（+3）、
  变异 **M277–M285 九支全 CAUGHT**、全量 **757/32/0 failures**、
  编译 0 告警、116 帧 `CHANGED=0 MISSING=0 ADDED=0`、脚本 105 全绿。**不换装**。
- **自评 95 / 100**：连续十一轮 94 之后第一次动。不是产品变好，是"读不到"这一族有了兜底。
- **下一步（R57）**：① BACKLOG 77 路 a（1× 抓帧）真做，带 before/after 实测；
  ② 读 R55/R56 的 CI（含第一次带 `MOTION_CHANNEL_UNIONED` 的那一步）；
  ③ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。

---

## R57 · 带捕获把横幅两臂救回来了；而它先骗了我一次（第 59 轮 / BACKLOG 77 结案 / 新开 80、81、82 / U-84 / D-116）

- **靶**：BACKLOG 77 挂了五轮的那句"横幅的进入与撤走两台机器都量不到"。
  R55 的归因已经指到量尺自己（`解释=98%`：一个采样间隔≈一次抓帧 + 一次等 runloop）。
  本轮去把抓帧变便宜。
- **做了什么**：`Scenario.captureRect` + `Grabber(rect:)`，横幅两臂只拍顶部那条带
  （1520×96px，面积 1/14），仍然 2× 拍。新判据
  `testBandCaptureIsCheaperAndStillSeesTheMotion`（带 vs 整窗、同进程交错、各两遍）、
  新守卫 `testBandCaptureIsWiredIntoBothBannerArms`（两臂都声明带、`recordFrames` 真传、
  `tick()` 真读、登记表同向，外加谓词正对照）。
- **实测（本机三次连续跑，`.scratch/motion-audit-2/r57_motion_readings.log`）**：
  抓帧中位 39.5 / 39.5 / 39.8ms → **4.4 / 4.5 / 4.6ms（≈9 倍）**；
  整卷中位间隔 44–45ms → **9–10ms**；同一场景过渡帧数 3–4 → **10–11**；
  最慢一次抓帧 86.5–88.2ms → **8.4–11.0ms**；
  `MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` **三次都是**（这一族以前本机 2/4）。
  登记表随之改回严格：两臂 `must_judge=true`、`thin_warnings=[]`；
  闸门跑真日志 `MOTION_FLOOR_OK=4/4 / REDS=0`。
- **本轮最重要的一件事**：第一版带抓到了**窗口底部**（`NSHostingView` 是翻转的，
  我按"原点在左下"写），而四条"有没有变化"的前提**全部通过** —— 位移也是变化。
  "9 倍便宜、4/4 满覆盖"那句话当时是真的，量的是列表。
  ⇒ 新加的是**位置同一性**：带 vs 整窗同一头 = 0.000、vs 另一头 = 0.954。
  中间那版用颜色判（"带里必须有警告粉"，阈值 `r>60 且 r−g>18`），
  实测那层 12% 橙的 r−g 只有 ≈12 ⇒ 恒红 —— **删掉**：不许给自己没量过的色号写阈值。
- **撞出来的更大一条（BACKLOG 80）**：`changedFraction(band:)` 的归一化带**上下颠倒**
  （注释说缓冲区第 0 行是底边，实测第 0 行是画面顶边）。
  这个文件 7 处 `band:` 量的都是镜像位置：`// 横幅那一条` y 0.02–0.22 → 实际 0.78–0.98；
  `侧栏第 4 行的星标列` → y 0.62–0.74；`表格区` 上下各偏 0.02；
  `详情区`/`列表中部` 因对称侥幸没跑偏；R2 的分带归因网格行序整个是反的。
  **本轮绕开、不修**：修它要重算 7 条地板。它排在 77 之前 ⇒ R58 的靶。
- **另两条新开账**：81（带高 48pt 没有"必须盖住横幅"的判据，横幅变高就会溢出而不会红）、
  82（离屏帧里半透明的横幅底合成到白底上 ⇒ 按帧量横幅对比度量的是捕获通道，不是产品）。
- **补两次欠的 CI 账**：R55 的 run **38555878378 = 作业失败**，红在
  `MOTION_FLOOR_NO_RESOLVE`（`executed: 32 胶片: 9 无 MOTION_SUMMARY`）—— stdout 在 CI 上又整次丢了，
  而 R52 撤掉免检牌之后它变成有名字的红。R56 的 run **38560978754 = 整作业 success**，
  `MOTION_CHANNEL_UNIONED=1 stdout=0 文件=55`、`judged=4/4 not-run=-`、`REDS=0`、
  `CAPTURE_GATE_CASES passed=25 skipped=9 failed=0` ⇒ **同一件故障，R55 让作业红，R56 让证据完整**。
  机制仍未证实（BACKLOG 79 不变）。
- **验证**：变异 **M286–M294 九支全 CAUGHT 且红得对**（`红得不对=0 还原不干净=0`）；
  全量 **759 tests / 33 skipped / 0 failures**；`swift build` **0 告警**；
  116 帧 `FRAME_BASELINE_CHANGED=0 MISSING=0 ADDED=0`；离屏闸门
  `CAPTURE_GATE_CASES passed=30 skipped=4 failed=0 有名字的红=0 NOT_RUN=0`；脚本 **106 全绿**。
  **产品零改动 ⇒ 不换装**、不需要 `frame_baseline update`。
- **两次翻车也记账**：电池第一遍**预检就拦住**（漏了 `CLIPBOARD_HISTORY_UI_MOTION=1` ⇒
  探针被 skip，harness 判 `DID-NOT-RUN` 而不是"没红"）；M291 我把预期测试名**猜错**、
  M293 第一版的替身是**语法错**（`BROKEN-MUTATION`，不是红）—— 三种"电池自己坏了"的形状各不同，
  都被分类器分开了。
- **自评 96 / 100**（95→96）：`流畅度` 13→14/20。产品零改动；
  动的是"横幅这一族我能不能判"—— 本机第一次有 10–11 帧过程可看。
- **下一步（R58）**：① **BACKLOG 80 落地**（把 `changedFraction` 的映射改对，
  逐条重算 7 个调用点的地板，并写明哪几条旧结论被推翻）；
  ② 读本轮 CI（第一次带捕获的 runner 读数 —— `judged=n/4` 与是否红在 `UNDERCOVERED`）；
  ③ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。

---

## R58 · 分带映射是上下颠倒的：改一行、写真值表、再查出 CI 看不见新读数（第 60 轮 / BACKLOG 80 结案 / 新开 83、84 / U-85 / D-117）

- **靶**：R57 结案时写下的 BACKLOG 80 —— `changedFraction(band:)` 把归一化带上下颠倒，
  7 个调用点量的是镜像位置，"它排在 77 之前"。
- **做了什么（三层）**：① 先给方向写合成位图真值表（六格方向 + 夹具自检 + 整幅=0.2），
  它在坏的映射上**先红四格**、横轴与整幅全绿 ⇒ 红的形状就是诊断；② 改实现（一行 `yStart=minY*h`）；
  ③ 逐个重算 7 个调用点：两条**关于中线对称**的（详情区、列表中部）一直没跑偏也没能力发现 bug，
  `表格区` 上下各偏 0.02，实质跑偏的是 `// 横幅那一条` 与 `侧栏第 4 行的星标列`（读数 0.221 → 0.260）。
- **本轮真正的发现是第二层错，而它是 R57 自己带进来的**：`// 横幅那一条` 从 R57 起传的已经是
  **带捕获那一卷** ⇒ 同一个矩形量的是"带里再框一条 9.5pt 窄缝"。同一判据三个数：
  镜像错 帧 11/≈121ms、嵌套错 帧 6/≈66ms、修完 **帧 15/≈165ms**，
  **三个都没让任何判据变红**（上限 311ms）⇒ 新守卫
  `testNoTestFramesABandInsideABandCapturedFilm`：带捕获那一卷上不许再传非 nil `band:`。
- **守卫的第一版假红，被现有判据顶回来**：谓词"函数里同时出现带捕获场景与 band 矩形"
  误报 `testListRowsDoNotAnimate…`（它主判据用整窗那卷正常传带、阳性对照用横幅那卷不传带）
  ⇒ 改成"场景变量→胶片变量→传 band 的调用点"那一点点数据流。
  另两处自坏也记账：按花括号切函数体会被字符串里的 `{` 骗过（实测只切出 6 段 = 扫描器空跑）；
  正对照的完整形态写在源码里会被自己扫出来 ⇒ 拼起来写。
- **CI 那一半（BACKLOG 83，本轮开本轮修）**：R57 的 run 38570965657（success）里
  想查"runner 上带捕获成没成功"，而 `MOTION_BAND` 一行都没有 —— 那一步用**硬编码前缀白名单**，
  R55 的 `MOTION_GRAB` 也不在里面 ⇒ 只剩 `judged=4/4`，而带捕获之前的 R56 也是 4/4 ⇒ 分不开。
  改成"先报 `MOTION_LINES=N` 再全打"，自检加 `family_not_in_any_list`（M299 把白名单放回去就红）。
- **同一次 CI 读数**：`MOTION_CHANNEL_UNIONED=1 stdout=61 文件=65`（stdout 又部分丢 4 行，并集接住）、
  `judged=4/4 not-run=-`、`MOTION_FLOOR_REDS=0` ⇒ **收紧后的登记表在 runner 上没红**。
- **验证**：变异 **M295–M300 六支全 CAUGHT 且红得对**；全量 **761 / 33 skip / 0 failures**；
  motion 全量 37 / 3 skip / 0 failures、`judged=4/4`；`swift build` **0 告警**；脚本 **106 全绿**；
  116 帧不变 ⇒ **不换装**、不需要 `frame_baseline update`。
- **自评 96 / 100**（没动，是有意的）：天花板是 `流畅度 14/20`，缺的正是"runner 上看得见过程的读数"；
  本轮清掉的是"CI 根本不打它"这个障碍，数要下一次跑才回来。
- **下一步（R59）**：① 读 R58 的 CI —— 第一次能在日志里看到 `MOTION_BAND` 与 `MOTION_GRAB`，
  据此判一次"带捕获在 runner 上成没成"（BACKLOG 83 的结案条件）；
  ② BACKLOG 84（网格行序的判据）与 81（带高没有"盖住横幅"的判据）；
  ③ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。

## R59 · 逐帧图第一次看得清；然后我把自己配的两个数都证伪了（第 61 轮 / 新开 85、86、87 / 结案 83 / U-86、U-87、U-88 / D-118）

- **靶**：R57/R58 把采样变细之后横幅两臂本机第一次有 10–13 帧，但胶片是 `writeStrip`（按 `width/2` 画）
  ⇒ 96px 高的带卷被缩成 38px 一行色块，"要看的东西正好被缩掉了"；而 R22 那句
  "帧 2 是原地的半透明 ⇒ 淡出不是塌陷"我引用了五轮，它的证据是一格中间态。
- **做了什么**：① `writeStack` 按**原始像素**竖排十帧（1520×980）+ 判据
  `testBannerFrameStacksAreReadableEvidence`（文件在、尺寸是原始像素、**这一叠里至少有一对帧真的不同**）；
  ② 分栏那条测量（侧栏 vs 详情区）；③ 图标跟踪那条测量（质心 + 像素数）；④ CI 那一步补 `XCTAssert` 原文。
- **本轮真正的产出是把自己两个"证据数"撤了（U-86）**：
  - "侧栏 8–11 帧落定、详情区 13 帧 ⇒ 两栏进度不同" —— `transitionFrameCount` 的门槛是**各自峰值**×15%，
    两栏各归一化 ⇒ 墨多的那栏线更高、先判停。新增 `sharedMovingFloor`（较大峰值 × 同一个 15%）后，
    本机五遍两栏"最后一个还在变的帧号"**完全相同**（16/16、17/17、17/17、17/17、16/16）⇒ 那句话作废。
  - "图标质心 42→29px ⇒ 横幅在被抬走" —— 淡下去时高饱和边缘先脱落，质心必然朝剩下那半边漂
    ⇒ 那条轴量的是**阈值在动**。新增**外框上下沿**轴 + 只看强帧（像素 ≥ 首帧一半）后：
    强帧跨度 2.6/0/0/0/0px、外框 **4/5 遍一格没挪**（[29,50]→[29,50]）⇒ "上移 6.5pt"作废；
    但也没写成"绝对没动"（第 1 遍下沿上移 4px，正落在脱落量级里，±2px 容差分不开两者）。
    顺带**部分恢复** R22：淡出这一半被外框证实了。
  - 留下的只有一件：**淡出中的横幅与已经重排的内容重叠**（第 5 帧起搜索框压在横幅文字上，
    详情区那半截尾巴还在原高度淡，粉底整幅都还在）⇒ 是**层叠**问题不是时长问题，要不要修等批次 59.1。
- **立下来的三条尺子规矩**：比较两块区域先确认**线是同一条**；随强度掉的东西（颜色阈值）不许用来量位置；
  **措辞从函数里出来**（`columnSettlementVerdict` + 合成真值表 `testSharedFloorColumnComparisonIsATruthTable`）。
- **两个自己的错，都当场变成判据**：① M303 第一遍跑出 **BROKEN-MUTATION** —— 断言红之后继续
  `seen[0]` 越界 ⇒ 进程崩、"Test Case … failed" 没打出来 ⇒ 改成 `guard … else { XCTFail; return }`
  （**红不许变成崩溃**）；② 汇总脚本的 `(.*)$` 在没有 MULTILINE 时只认文末 ⇒ 分栏格式一改就抽不到数、
  `min()` 打在空序列上、文件写了一半 ⇒ 现在每条读数各自抽干净、抽不到就**报错退出**，表里的数全部现算。
- **读 R58 的 CI ⇒ BACKLOG 83 结案**（run 38576482491 摘录存进 `.scratch/motion-audit-2/ci_r58/`）：
  `MOTION_LINES=122`，`MOTION_GRAB` 与 `MOTION_BAND` 同时读到了，据此判了"带捕获在 runner 上成没成"——
  **成了，但买到的是时间不是分辨率**（带 5.6ms / 整窗 14.1ms，两臂间隔中位都是 22ms、过渡帧数都是 3）
  ⇒ 登记表里 R57 那句"runner 侧还没有一次带捕获的读数"已更正。
- **另开两条 CI 的账**：86 = 那一步 `continue-on-error` 把 `exit 1` 整个吞掉（同一次 run 结论是 success），
  本轮只补了"红的理由要能读"这半边，**没有**改成有闸（缺一次"红的是产品而不是环境"的样本）；
  87 = "构建 0 告警"那一步不编译测试目标 ⇒ R58 那条 `variable 'a' was never mutated` 两次 CI 都是绿的。
  清洁基线量出 **0 条** ⇒ 本轮就把命令收紧成 `swift build --build-tests`、多打告警原文，
  并加了一条**真跑那段脚本**的守卫（0 告警必须绿、1 告警必须红且能读到是哪一条）。
- **验证**：变异 **M301–M307 七支全 CAUGHT**（`红得不对=0 还原不干净=0`）；
  全量 **765 / 36 skip / 0 failures**；motion 全量 **41 / 3 skip / 0 failures**；脚本 **107 全绿**；
  清洁 `swift build --build-tests` **0 告警**；116 帧 vs working **CHANGED=0 / MISSING=0 / ADDED=0**
  ⇒ 产品零改动、**不换装**、不需要 `frame_baseline update`。
  读数：`.scratch/motion-audit-2/r59_motion_readings.log`（本机两条通道又不一样：stdout 21 / 文件 73）。
- **自评 96 / 100**（没动，是有意的）：本轮没让任何像素变好，它做的是把上一轮写进台账的两个假数拿掉。
- **下一步（R60）**：① 读 R59 的 CI —— 收紧后的告警闸门在 runner 的 Swift 6.1.2 上会不会报出新告警（87 的最后一格）、
  motion 那一步有没有红且这次能不能读到理由（86）；
  ② 外框那条轴分不清"边缘脱落"与"一边被裁" ⇒ 换一条**不吃饱和度**的位置轴（跟几何轮廓走）；
  ③ BACKLOG 84（分带网格行序没有判据）、81（带高没有"必须盖住横幅"的判据）、72 的迁移。

## R60 · 三条不依赖颜色的轴都没能量出"重叠"；CI 用一条假红教我把地板按机器分开（第 62 轮 / 结案 84、87 / 新开 88、89 / U-89、U-90 / D-119）

- **靶**：R59 撤掉两个数之后只剩一条看图结论（淡出中的横幅被上移的搜索框盖住）。本轮想把它变成判据，
  顺带钉上 R58 留下的"网格行序没有判据"（84）。
- **三条轴全失败，各因不同（这是本轮真正的产出，记为 BACKLOG 88 / U-89）**：
  中灰像素数 ⇒ 淡到一半的白字正好落进中灰带；最长均匀段 ⇒ 横幅那片**平底本身就是均匀的**；
  水平直边 ⇒ 只检出第 0–1 帧的分隔线，搜索框那条软渐变边根本不在候选里。
  ⇒ 方法级结论：**重叠双方都在动**（一个在淡、一个在位移），任何按亮度/颜色/边界的阈值都会被其中一方污染；
  要分开只能换捕获方式（关掉动画那一臂与开着那一臂在同一帧号相减）。观察**不撤也不升级**，
  批次 59.1 的问句仍然有效。证据：`.scratch/motion-audit-2/r60_evidence/`（三个探针 + 两张 3x 单帧）。
- **BACKLOG 84 结案**：`changeGrid` 拆成"位图版 + 薄壳"，新判据 `testChangeGridPrintsRowZeroAtTheTop`
  把差异分别放顶边/底边/左边（列序是同一处映射的另一半）；R58 的合成分位图闭包提成共用 `syntheticPair`。
- **读 R59 的 CI（run 38586812301，整作业 success；摘录存 `.scratch/motion-audit-2/ci_r59/`）**：
  `compile warnings: 0` ⇒ **87 结案**（收紧成 `--build-tests` 之后 runner 的 Swift 6.1.2 也没报数）；
  `motion suite exit: 1` 这次**带着两条红的原文**（R59 那条 grep 第一次跑就兑现），其中一条是**我写的假红**：
  `testBannerOutTracksWhetherItFadesOrSlides` 在 runner 上"整卷只找到 0 帧里有那颗红色图标" ——
  0 帧不是采样粗，是**判色前提在 1x 上不成立**（那颗 ~22px 实心红符号没有纯色核心像素），
  而我把地板 4 写成了本机的数（五遍 5–6 帧）⇒ **R38 那一族我自己重犯了**。
  改成 `MOTION_TRACK_VOID`（附缩放/单帧最多红像素/扫描窗换算成 pt 的诊断）不红，
  但 2x 上前提是被实测撑住的 ⇒ 那里认出 0 帧仍然必须红（M303 换 needle 后重跑 CAUGHT）。
- **新开 BACKLOG 89 / U-90**：runner 那条"提示条只演了 57ms ⇒ 一帧跳变"的红，
  57 < 2×38（它自己报的事件内最粗采样）⇒ 变化段连两次采样都不到，"演一帧就停"与"演很久只抓到一帧"
  同一个读数。缺的是 `judgeMotion` 里一格 `.spanUnresolved`；**本轮没顺手改**，因为那条 not-run 会让
  覆盖率闸门把 `notice-banner`（`must_judge=true`）翻成 UNDERCOVERED 红 ⇒ 先补一格"judged 与 not-run
  同时出现时怎么判"的夹具（R61）。
- **另一条旧话被更正**：带捕获在 runner 上这次采样**确实变细**（带 19ms / 整窗 32ms，过渡帧数都是 3），
  R58 那次是 22ms / 22ms ⇒ 登记表里"买到的是时间不是分辨率"不能当常数，得按"两次运行不一致"记。
- **验证**：变异 **M308–M310 三支全 CAUGHT 且红得对**（`r60_mutation_battery.log`）+ M303 重跑 CAUGHT；
  全量 **766 / 36 skip / 0 failures**；motion 全量 **42 / 3 skip / 0 failures**（89.6s）；
  脚本 **107 全绿**；清洁 `swift build --build-tests` **exit 0、0 告警**；
  116 帧 vs working **CHANGED=0 / MISSING=0 / ADDED=0** ⇒ 产品零改动、**不换装**。
- **自评 96 / 100**（不动，有意）：产品零改动；值钱的是"钉住一个洞、撤掉一条我自己写的假红、
  把一条看图结论的机器可复现性诚实标成未证明"。
- **下一步（R61）**：① BACKLOG 88 的换捕获 A/B（关掉动画那一臂），它同时可能把"重叠"变成可判；
  ② BACKLOG 89 的夹具 + `.spanUnresolved`；③ BACKLOG 86（有闸与否，需要一次"红的是产品"的样本）；
  ④ BACKLOG 81 / 82 / 72。


## R61 · 修 BACKLOG 61：先证伪自己上一轮写的论证和修法，再落地「只滚不选」（第 63 轮 / 结案 61 / D-120 / U-91）

- **开场**：61 是唯一一条"界面在讲一条用户看不见的记录"的挂账，上一轮我给了论证 + 候选修法。
  按仓库规矩先 spike —— 结果 spike 把两份结论双双否掉（详见 D-120）。
- **产品改动**：新文件 `Views/SelectedRowRevealer.swift`（`SelectionRevealPlan.rowIndex` 纯函数 +
  一个只调 `scrollRowToVisible` 的宿主视图）+ 侧栏 4 行 `.background` 胶水。
- **四条读数**（`REVEAL` / `INTAKE_READING`，全在屏）：
  近处 0.10s 落上且 originY 不动；视口外那条 0.10s 落上、集合恰好 `[60]`、originY 0→2191；
  选中没变而视图重算两次（收藏 + 撤）⇒ originY 保持 0；
  删掉顶部一条无关记录 ⇒ 选中项行号 60→59、id 不变、originY 保持 0（这一臂是 M313 第一次活下来之后补的）；
  采集路径 `新记录落点=4 在屏=true 集合=[4] originY 0→159`（修前是 `在屏=false 集合=[]`）。
- **量尺教训（本轮五条，全是我的）**：① `selectedRow` 是主选中行，判"选中了没有"必须读
  `selectedRowIndexes`；② 泵的条件写"变没变"会把 `2 → -1` 当成为"落了"，必须泵到**期望那一行**；
  ③ 探针自己的 Binding 若背后没有 `ObservableObject`，SwiftUI 根本不会重算 ⇒ spike 第一版
  四臂全打 `onChange=0`，读起来像"onChange 不触发"。
  ④ **断言写在推迟生效的动作之前**等于没断言 —— 臂 3 第一版 0.00s 就收工，M313 就是这么活的
  （判一个「不该发生」的滚动，必须先给落定时间）；
  ⑤ 从读数多走一步就当结论：我看到表格 `[0,60]` 就写「批量动作会作用在没选过的记录上」，
  而同一行读数里 `store 条数=1` 已经把那句否掉了 ⇒ 推论必须能被同一批读数支持（BACKLOG 90 正文）。
- **工具事故两条，都修进脚本**：变异脚本用 `git checkout --` 还原未入库的新文件（pathspec 不匹配 ⇒
  四刀叠在同一文件里，读数全污染）；两套电池并发跑（基线读到对面那一刀的产物）。
  ⇒ 改成按内容还原 + pidfile 锁 + 基线不绿拒跑。
- **验证**：全量 **772 / 39 skip / 0 failures**（140.5s）；motion 全量 **42 / 3 skip / 0 failures**（89.4s）；
  脚本 **108 全绿**；`swift build --build-tests` **exit 0、0 告警**；
  电池 **M311–M317：5 刀 CAUGHT，M313 与 M317 按实存活**（⇒ 新开 BACKLOG 91：那条闸门目前没有读数）；
  本机已换装并跑起来（`/Applications/时间剪史.app`，pid 44097，`proc_pidpath` 核对过路径、两边二进制同哈希）；
  116 帧 vs working **CHANGED=0 / MISSING=0 / ADDED=0**（离屏通道结构上看不到本次改动）；
  电池日志：`.scratch/motion-audit-2/r61_mutation_battery.log`。
- **自评 96 / 100**：动了产品；原生感 −1（多一个 AppKit 桥）、性能 −1（多一次有界树解析），
  换来的是"详情区与列表重新指向同一条记录"。
- **R61 的 CI 已逐步读完（run 38603034761，整作业 success）**：`compile warnings: 0`；
  Swift **772 / 44 skip / 0 failures**（本机是 39 skip ⇒ runner 多跳 5 条，就是那三条在屏探针 + 两条老探针）；
  离屏捕获 **116 帧 / 捕获失效 0**、capture gate `passed=25 skipped=9 failed=0 有名字的红=0`；
  motion **exit 0、42 例、judged=4/4**、floor `OK=4/4 REDS=0`；帧基线 vs working `MISSING=0 ADDED=0`（像素全等）；
  脚本 **Ran 108 OK**。而**最要紧的一行是**：`ui suite exit: 137 executed: 0 已下结论的用例: 0` ——
  在屏交互探针在 runner 上被 240s 看门狗收掉，**一条都没跑完** ⇒ 本轮那三条揭示判据在 CI 上不存在，
  61 的回归在 CI 侧只有「真值表 + 两条源码守卫」兜着（它们不依赖 env，确实在 772 例里跑过）。
  ⇒ 新开 BACKLOG 92 记这件事（不粉饰成「CI 覆盖了」）。
- **下一步（R62）**：① BACKLOG 92（把在屏探针做成 runner 跑得完的形状，或在账本里明确它们是本机专属）；
  ② BACKLOG 91（给那条闸门找一条有分辨率的产品路径，否则把声明降级成注释）；
  ③ BACKLOG 90（滚回顶部后表格选中集多留一行）；④ BACKLOG 89（runner 那条红的夹具与
  `.spanUnresolved`）；③ BACKLOG 88（重叠：关掉动画那一臂与开着那一臂同帧号相减）；
  ④ BACKLOG 86（motion 步骤要不要有闸）；⑤ 81 / 82 / 72。


## R62 · CI 那句「探针没跑完」是真的，但它让 11 条在屏判据一起免检（第 64 轮 / 结案 91、92 / 新开 93 / U-93、U-94 / D-121）

- **开场读数**：R61 的 CI（run 38603034761，整作业 success）里有一行
  `ui suite exit: 137  executed: 0  已下结论的用例: 0` ⇒ 61 的三条行为判据在 CI 上一条都没跑。
  其余步骤逐条读过：`compile warnings: 0`、Swift **772 / 44 skip / 0 failures**、
  离屏 **116 帧 / 捕获失效 0**、capture gate `passed=25 skipped=9 failed=0 有名字的红=0`、
  motion **exit 0 / 42 例 / judged=4/4**、floor `OK=4/4 REDS=0`、脚本 `Ran 108 OK`。
- **交的东西**：`scripts/probe_coverage_gate.py`（判形状，不判耗时）+
  `scripts/probe_coverage_expectations.json`（11 条逐条登记）+ CI 新步骤
  `On-screen probe coverage floor`（硬门）+ `scripts/tests/test_probe_coverage_gate.py`（12 条）
  + 电池 `mutate_r62_gate.py`（M318–M324 **七刀全 CAUGHT**）。
- **推翻自己上一轮的一条结论**：BACKLOG 91「闸门没有读数」是电池 filter 指错测试造的；
  修好重跑 M313 / M317 ⇒ 都 CAUGHT，红在 `2125.0 ≠ 0.0`。产品结论不变，账本改了。
- **两条新的工具规矩**（都落进脚本，不靠自觉）：每刀必须能证明「那一臂在被跑的那条测试里」
  （基线缺一条判据的结论行 ⇒ 整套拒跑）；电池统一 `PYTHONDONTWRITEBYTECODE=1`
  （M319 连跑 SURVIVED / 单跑 CAUGHT 是 `__pycache__` 撞车）。
- **验证**：脚本 **120 全绿**（108 → 120）；116 帧 vs working **CHANGED=0**（本轮产品零改动）；
  Swift 侧零改动，故不重跑全量、不换装。
- **自评 93 / 100**（比 R61 低 3，有意）：连续两轮没碰产品与画面。价值在「让盲区可见 +
  推翻自己一条错判」，但阶段二的主体没推进 ⇒ **R63 回到产品面**。
- **R62 的 CI 已逐步读完（run 38674789147，整作业 success）**：新步骤
  `On-screen probe coverage floor` 第一次在 runner 上跑，输出是
  `PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0`
  加一行 `PROBE_NOT_RUN 11/11 …`（逐条点名，含 R61 那三条）⇒ **它既没恒红也没恒绿**：
  缺席被写成事实，红留给"新判据没登记 / 登记过期 / 说跑不了却跑到了"。
  其余：`compile warnings: 0`、Swift **772 / 44 skip / 0 failures**、离屏 **116 帧 / 捕获失效 0**、
  motion **exit 0 / 42 例 / judged=4/4**（这次 `notice-banner=3`，上一轮是 2 —— 在登记之内，
  但再次说明那个数由采样决定，不能当判据）、floor `OK=4/4 REDS=0`、脚本 **Ran 120 OK**。
- **下一步（R63）**：① 回到产品与画面：BACKLOG 63/64/65/66 那一族位点逐个判"加动效有没有积极作用"，
  并把 88（重叠：关掉动画那一臂与开着那一臂在同一帧号上相减）做掉；
  ② 产品/视觉面：BACKLOG 63/64/65/66 那一族位点逐个判「加动效有没有积极作用」，
  顺带把 88（重叠那条轴，A/B 相减）做掉；③ BACKLOG 93（探针在 runner 上挂在哪一句）。

- **R63（第 65 轮，产品面）· 快速选择浮层第一次被看见：它从来就是塌的**：
  R19 记的"stack 只在捕获环境里塌，真实 App 里撑满 420×300"被证伪 ——
  产品路 `show()` 与捕获路 `windowForCapture` 读到同一个塌法
  （`NSStackView` `{{0,0},{24,49}}`、`NSScrollView 0×0`、`visibleRect 0×0`、`drawn 0.0%`）。
  机制由最小对象图 spike 给出：`NSStackView(views:)` 生下来
  `translatesAutoresizingMaskIntoConstraints == false` ⇒ 那两行 `frame` + `autoresizingMask` 是空操作。
  修后 stack `396×276`、`visibleRect 396×251`、`drawn 19.3%`。
  另外三件：① 空结果那句的可见性不再押在淡入上（`wantsLayer`，四臂 spike 量到
  非图层 view 上 `animator()` 不提交模型值：0.000 停在两秒、完成回调从不跑）；
  ② 那句从面板最底挪到列表那一格（gap 243pt → 8.0pt，帧看过之后才判的，推翻我自己 R7 的决定）；
  ③ **本轮自己改出来的回归**：钉住 stack 之后内容第一次能反过来定窗口宽度，
  40 字查询词把面板从 420 顶到 899 ⇒ 降抗压缩，面板回到 420 并截出省略号。
  交付：`quickpick-list / -typed / -empty` × 亮暗 = 6 张帧（116 → **122**，同提交 `update`）、
  R19 那条判据翻成契约 + 空结果态新契约、撤掉一条基于假解释的夹具豁免、
  一份带正对照的 `sparseByDesignFixtures`（它当轮就抓出一个"帧名 typed、内容 empty"的假夹具）。
  电池：M325–M329 + M335 六刀全 CAUGHT；**M330/M331/M333/M334/M336 五刀绿**
  ⇒ 那五处代码没有作者，本轮删掉（删后 `list`/`typed` 四张帧逐字节不变）。
  新开 BACKLOG 94（📄 emoji 图标）、95（在屏像素通道返回"尺寸正确的空图"）、
  96（本机 `swift test` 丢一卷测试后半段的 stdout ⇒ 动效卷靠 R11 的文件通道活下来，捕获卷没有）。
  自评 **93 / 100**。人工验收新增**批次 63.1–63.4**（这一批是地基：我的像素判据全在离屏通道上）。
- **R63 的 CI 已读（run 38683762166，job 红在一步）**：红的正是本轮新写的那条守卫 ——
  `这些帧不再需要「天生就稀」的豁免了：["quickpick-empty"]`，而 runner 的读数是
  本机 97.9% / runner 94.9% 对上门槛 95.0% ⇒ **假红**，成因与 R38 记过的那条完全相同
  （一台机器的读数当了另一台的地板）。同轮已改成**同一次运行内的兄弟比较**
  （empty 2.1% vs list 14.2%；runner 5.1% vs 17.9%）+ 正对照无条件生效
  + 新写 `testQuickPickTypedFixtureShowsFilteredRowsNotAnEmptyList`（all=5 / typed=2 / empty=0）。
  其余步骤：`Build (must be warning-free)` ✓、`Swift tests` ✓、捕获步骤报 **122 帧 / 捕获失效 0**。
  本机修后：`swift test` **774 / 39 skip / 0 failures**、`--build-tests` **0 告警**、122 帧 `CHANGED=0`。
  另一件记进工具账：那条守卫第一版**当场 crash**（`Dictionary(uniqueKeysWithValues:)` 撞同名亮暗两张帧），
  而我在那行上面刚写完"取更空的那一张"的注释 —— **注释里写对的规则不等于代码里存在的规则**。
- **R63 的修后 CI 已逐步读完（run 38685562002，整作业 success，11m29s）**：
  `compile warnings: 0`；Swift **774 executed / 44 skip / 0 failures**；
  三条浮层判据**逐条 `Test Case … passed`**（`…FillsItsPanelAndCanBeCaptured`、
  `…EmptyStateSentenceIsCommittedAndSitsInTheListSlot`、`…TypedFixtureShowsFilteredRowsNotAnEmptyList`）；
  新守卫在 runner 上给的是
  `SPARSE_EXEMPTION_OK quickpick-empty drawn=5.1% < quickpick-list drawn=17.9% - 3pt`，
  同一行还记下 `本次真正走了豁免分支的帧 []` ⇒ **假红没了，而"这台机器根本不需要这条豁免"也被写下来了**；
  `CAPTURE_GATE_RESULT=ok 红=0`、`PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 本次下结论=0 红=0`
  （BACKLOG 93 原样开着）、`MOTION_FLOOR_FACTS judged=4/4 executed=42`（每档 4/3/2/3，已登记的采样噪声）、
  `FRAME_BASELINE_AGAINST=working / COMPARED=122` 绿。整作业里唯一 exit 1 的是 report-only 的
  "Frame baseline vs previous release"（对 v1.4.8 快照改了 62 帧 —— 新版本本来就该改像素）。
  **BACKLOG 96 因此加重而不是收窄**：runner 上也有两条 print 整条不见了
  （`CAPTURE_PROBE quickpick` 与本轮新写的 `QUICKPICK_FIXTURE_ROWS` 各 0 行），
  而同一个类里 `QUICKPICK_EMPTY_SENTENCE` / `QUICKPICK_LONG_QUERY` / `BOTTOM_INK_IDENTITY` 都在 ⇒
  丢的不是"函数后半段"，是**按条随机丢，两台机器都会**。
  ⇒ 结论："`Test Case … passed` 那条 XCTest 结论"是唯一能证明判据跑过的东西；
  自打印的读数必须走文件通道（R11 给动效卷做过的那一套），捕获卷还没做。

## R64（第 66 轮账本 / D-123 / BACKLOG 96 交付面 + 新开 97）：判据的结论必须有第二条通道

- **上面 R63 那句"按条随机丢"本轮被自己的测量推翻**：真实形状是**连续大块丢**。
  本机三遍真 artifact 逐行比对：`--filter` 两遍各丢 **324/488 行**（同一块，下标 164–487，
  = 316 条不同的行），全量 `2>&1 | tee` 那一遍丢 **238/488 行**（3 块：0–48、142–217、296–408）；
  切点在**行中间**（`…bottomI` 直接接 `Test Case …`）；五条判据自写的 marker 三遍全丢，
  而 37 / 775 条 `Test Case … passed` 一条没少、作业 0 退出。
  runner 只算现场：run 38683762166 捕获那一步浮层 marker **0/4**，run 38687419144 **2/4**。
- **交的东西**：`CaptureReadings.swift`（新，第一次整份重写 + 之后追加）、
  捕获卷 **69 处** `print(` → `emit(`、守卫 `testCaptureReadingsUseTheFileChannel`
  （绝对规则：那个文件剥注释后 `print` = 0）、`ci_capture_gate.py --readings`
  （并集 + **缺通道是一条有名字的红**）。并集从 workflow 的 awk 挪进 python，
  workflow 只留"通道在不在"的汇报行 + 一条**接线断言**（删掉 `--readings` 会被自检抓住）。
- **验证**：`--build-tests` **0 告警**；`--filter UICaptureTests` 37 例 / 4 skip / **0 failures**、
  122 帧；全量 `swift test` **775 条结论行 / 0 条红**、122 帧 vs working
  `COMPARED=122 CHANGED=0 MISSING=0 ADDED=0`；脚本自测 **120 → 127** 全绿；
  闸门拿真 artifact 跑：`补回=316 行`，同一份日志不给 `--readings` 仍是 0（正对照）。
  电池 **M337–M342 六刀全 CAUGHT**（`.scratch/motion-audit-2/r64_mutation_battery2.log`）。
- **本轮自己坏掉的三件工具**（都记进 D-123）：正对照拿 needle 拼（M338 抓到）；
  上一遍留下的读数文件让"落盘坏了"那一刀逃过（M341 第一版）；
  电池汇总比对了带尾随空格的字符串 ⇒ **六刀全抓到却写"非抓到=6"**。
- **产品零改动**，但逐帧看浮层量出一条真缺陷 ⇒ **BACKLOG 97**：
  纯文本行标签 34.5–35.0pt vs 文件行标签 56.5–57.5pt（图标占 36.0–50.0pt）⇒ 差 **22pt 两种左轴**。
  同批好消息：选中不产生位移（0.5pt 是字形边距）、空态那句居中误差 0.75pt。
  我自己那把 `|亮度差|>8` 的粗尺读出的"药丸左右不对称"与 R63 那把有正对照的尺冲突 ⇒ **不采信**。
- **R63 台账那次 CI（run 38687419144）已逐步读完**：整作业 success、18/18 步全绿；
  `CAPTURE_GATE_CASES passed=27 skipped=9 failed=0 有名字的红=0 NOT_RUN=25` + `RESULT=ok`；
  `PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 本次下结论=0 红=0`（93 原样开着）；
  `MOTION_FLOOR_FACTS judged=4/4 executed=42 REDS=0`；`executed cases: 774`；
  捕获那一步 `captured frames: 122 executed: 36 捕获失效帧: 0`；
  `FRAME_BASELINE` 对 working `MISSING=0 ADDED=0`、对上一版发布 `CHANGED=62`（report-only）；
  三条浮层判据在 runner 上**逐条 `passed`**。
- **下一步（R65）**：回到产品面 —— BACKLOG 94 与 97 是同一个决定（先定图标语言，再定左轴），
  后面排着 63/64/65/66 那一族与 88；96 的验收等 R64 的 CI 把 `补回=k>0` 打出来。

## R65（第 67 轮账本 / D-124 / 结案 94、96、97，新开 98、99 / U-104…U-106）：浮层的图标从文案搬进视图，左轴随之归一

- **开场读数**（R64 那把尺，同一套坐标）：纯文本行标签 **34.5–35.0pt** 起、文件行标签 **56.5–57.5pt** 起
  ⇒ 五行两种左轴、差 **22pt**；那 22pt 是 `EntryPresentation.preview` 里的 `"📄 "` 两个字符。
- **先推翻自己上一轮的一句话**：94 写着"侧栏、浮层、详情共用同一条字符串"。读调用点：
  侧栏 `.file`/`.files` 走 `FileNameText`/`MultiFileTitle`（不经过 `shortPreview`）、详情走 `sizeDescription`、
  菜单栏走 `menuTitle` ⇒ **唯一可见的表面是浮层**；"参与搜索匹配"是真的。⇒ 记 U-104。
- **交的东西**：文案里三处 `"📄 …"` 去掉；浮层每行一枚 16pt `NSImageView`
  （`doc.text`/`photo`/`doc`/`doc.on.doc`，与侧栏 `RowLeadingVisual` 一一对上）；
  标签左锚点改成 `symbol.trailing+6` ⇒ 左轴是副产品，没单独修。
- **判据 5 条 + 电池 M343–M349 七刀全 CAUGHT**（`r65_mutation_battery.log`）。
  两条"静默的空白"各有一条正对照：符号名写错必须画不出（`doc.textt` ⇒ nil）、
  夹具必须真有 ≥2 种类型（否则"左轴一致"平凡为真）。
- **验证**：`--build-tests` **0 告警**；全量 `swift test` **780 例 / 37 skip / 0 failures / 157.0s**
  （780 = 上一遍 775 + 本轮 5 条新判据）；捕获卷 38 例 **111.195s**（R64 两遍 113.374 / 114.754）
  ⇒ 每行多一枚符号图**没有可测代价**；帧 `COMPARED=122 CHANGED=0 MISSING=0 ADDED=0`（对刚更新的基线），
  本轮 **4 张换、118 张逐字节不变**；脚本自测 127 全绿。
- **R64 的 CI 也在本轮读到**（run 38693365411，18/18 全绿）：`补回=65 行`、`NOT_RUN` 25 → **50**
  ⇒ **BACKLOG 96 结案**；同一轮开出 **98**（在屏探针那一步仍只有一条通道）。
- **换装已完成**：`install_local.sh --yes --label r65-overlay` ⇒ `INSTALL_RESULT=ok`、
  新包与装上的一份逐字节相同（sha `de899ebccf34b756…`）、新 pid 578、存档 105→105、`SMOKE_OK=1`。
- **R65 的 CI 已读**（run 38696695788，18/18 全绿）：新守卫在 runner 上打出 `标签左轴散布=0.00pt`；
  `--readings` 第二次跑，`补回=131 行`（上一次是 65 ⇒ 这个数每次不同，正是不能省的理由）。
  **读到一处没有名字的红**：`motion suite exit: 1` 连着两遍而 `MOTION_FLOOR_REDS=0` ——
  那道门数的是自己四臂的结论，不看测试有没有失败 ⇒ 新开 **BACKLOG 100 / U-107**。
  BACKLOG 99（浮层 13pt vs 令牌 12pt，**判断没量过**）；浮层的动效三轮没碰；
  R66 的第一件事是 BACKLOG 100（动效那一步的红必须有名字）。

## R66（第 68 轮账本 / D-125 / 结案 100，新开 101、102 / U-108…U-111）：动效的红必须有名字，而"这台机器看不见淡入"要有个与被告无关的证人来签

- **开场读数**（同一条声明 150ms 的淡入）：本机 `MOTION_CUT_CONTROL` 落定残余四遍
  **0.554 / 0.719 / 0.729 / 0.974**、runner **0.025**；采样 10–11ms vs 21ms；
  `MOTION_SETTLE banner-in` 16 帧 ⇒ ≈160ms vs 4 帧 ⇒ **≈76ms**。
  ⇒ 采样差 2 倍解释不了残余差 22–39 倍 ⇒ **R65 写的"在 runner 上登记成未覆盖"被本轮推翻**：
  那是拿被告的证词给被告免检（U-108）。
- **证人**：`FadeClockProbe` + `FadeClockView`（测试自己的夹具，机制与提示条相同：
  插入/移除 + `.transition(.opacity)` + `withAnimation(.easeInOut(duration: 0.15))`；
  150ms 写死在测试里、**不读 `MotionCatalog`**；逐帧读**平均亮度电平**而不是帧间差）。
  三档：跨度 < 0.05 ⇒ 证人坏了**判红**；中间态 ≥ 2 ⇒ 机器能分辨（产品读不出=红）；
  否则 ⇒ `MOTION_NOT_RUN=fade-clock-snaps-here` + skip。
  本机 `跨度=1.000 中间态帧数=8–11 帧数=87–91 采样≈21ms 判定=能分辨`。
- **决定表纯函数化**：`controlJudgment(residual:clock:)` + 六格真值表（U-109：
  只有某台机器才会走到的分支等于没有判据 —— 本机残余永远高于地板，三条判定从未被执行）。
- **闸门补一层** `suite_verdicts()`：`SUITE_RED` / `SUITE_NAMELESS_RED` / `REGISTERED_REDS` / `SUITE_STALE`，
  排在 `verdicts()` 两处提前 return **之前**（U-110）。CI 那一步不必改（报告步仍 continue-on-error，
  红由下一步的地板闸门挡）。`suite_reds` 登记表今天**故意空着**，并有一格自测钉住。
- **数字**：产品 **0 个文件**；122 张帧 `CHANGED=0 MISSING=0 ADDED=0`；
  全量 **783 例 / 38 skip / 0 failures / 156.7s**；动效卷 45 例 exit 0；脚本测试 127 → **139**；
  `--build-tests` 0 告警；电池 **M350–M362 十三刀全 CAUGHT**
  （M362 动产品：撤掉淡入驱动 ⇒ 红在 `.productSnapped` 那一句，没被新登记吞掉）。
- **真实视觉审查**：`fade-clock-strip.png`（91 帧）逐行看得见 4–6 级中间灰 ⇒
  "本机看得见淡入"是看出来的；图还纠正了我一处预期（黑块铺满视口 ⇒ 跨度 1.000 而不是我估的 0.5）。
- **本轮没换装**（并说明为什么不算跳步）：产品 0 文件、帧 0 变化 ⇒ 屏幕上的东西与 R65 装的那份完全同一
  （sha `de899ebccf34b756…`）。"交付默认自己构建换装"管的是改了产品的轮次。
- **下一步（R67）**：BACKLOG **101**（整卷级缺席要能被数出来：`suite_not_run` 白名单 + 每次打计数）
  与 **102**（runner 的读数被 `head -120` 截、胶片从不上传 ⇒ 先让 runner-only 的现象有图可看）；
  然后回到产品面：浮层的动效（R63–R66 四轮没碰，这一族最该还的账）与 BACKLOG 99（字号/行高，量了再判）。
  下一次 CI 会回答：runner 那一档到底是 `能分辨` 还是 `拍成跳变` —— 两种答案都有名字了。

## R66 的 CI 附记（本轮读的 run 38706222682 / job 116326186712，逐步读完）

- **淡入时钟在 runner 上那一档 = `拍成跳变`**：
  `MOTION_FADE_CLOCK 声明=150ms 跨度=1.000 中间态帧数=0 帧数=26 采样≈80ms 判定=拍成跳变`
  （本机同颗探针：中间态 8–11 帧、采样≈21ms、判定=能分辨）⇒ BACKLOG 100 的两台机器表**齐了**。
- **红的用例有名字了**：`MOTION_FLOOR_SUITE_RED=1 … testTransitionsAreActuallyRunning：
  failed - notice-banner：画面只变了 53ms 就停了，而声明的过渡是 150ms（事件内最粗采样 35ms）`
  ⇒ R66 那层新闸门第一次在 runner 上生效，红不再隐身。
- **对照上一次"绿"的 run 38699044800**：它的 `motion suite exit:` **同样是 1**，
  红的却是另一条（`testBandCaptureIsCheaperAndStillSeesTheMotion`，26.04 > 22.20），
  而整份 CI 结论是 success ⇒ 这就是 BACKLOG 100 说的"红着绿过去"，本轮第一次拿到它的实物证据。
- **但这两条红都还没归因，而且 R66 的证人今天没资格给它们作证**：
  证人采样 80ms，比它要作证的判据（35ms）还粗 ⇒ 新开 **BACKLOG 104**，R68 去把证人搬到同一颗尺子上。
  `suite_reds` 登记表**继续留空** ⇒ 下一次 CI 仍然会红，这是如实记账，不是漏修。

## R67（第 69 轮账本 / D-126 / 结案 —，新开 103、104 / U-112…U-116）：浮层那一行第一次有指针反馈

- **还的是 R63–R66 欠的产品账**：浮层唯一提交入口是双击（`table.doubleAction`，没有 `action`、
  没有 `NSTrackingArea`）⇒ 改之前是一列不能碰的文字。加的是**一档灰**（`VisualFill.hover`，与侧栏同一枚令牌），
  选中那一行不叠（真值表四格全钉）。
- **本轮真正的产出在判据侧**：R15 那把"按列取带内最大"的宽度尺给出"左差 −2px / 右差 +2px"是**绿的**，
  而帧上那层灰是**直角满高**的一块、药丸是圆的 ⇒
  **总范围相同的两块墨可以有完全不同的轮廓**，任何阈值都救不了（读数丢信息，不是阈值太松）。
  补了逐行尺（`alphaLiftProfile` / `profileLeftInsetSpread`）+ 一条"参照物自己也必须是圆的"的断言。
- **读数推翻三版**：直角（内缩 0px，红）→ 6pt（8px，红）→ `VisualRadius.card`=8pt（**11px，与药丸逐行 0px 差**）；
  `hoverFillInset` 9 → 10（9pt 时左右各宽 1pt，容差内一直绿 ⇒ **绿不等于对上**）。
- **验证**：全量 **786 / 38 skip / 0 failures / 157.9s**；捕获卷 41 例 0 failures；
  `FRAME_BASELINE_COMPARED=124 CHANGED=0`（改产品那一刻 `CHANGED=2` = 两张 hover 帧，逐字对上后同提交 update）；
  脚本测试 139 OK；编译告警 0（日志里 10 行 `CoreData: warning:` 是运行时噪声，口径分开记 = U-114）；
  电池 **M363–M371 九刀全 CAUGHT**（M369 就是本轮真实存在过的直角版，它从其余六刀下全部逃掉）。
- **换装本机**：`INSTALL_RESULT=ok`，新包 sha `db4872e4a852b426…`，pid 21873，存档 105→105，`SMOKE_OK=1`。
- **自评 96 / 100**（曲线 n=60、均值 92.28、`GAPS=none`、尾轮守卫通过）。
  涨在画面上：浮层从"不能碰"变成有指针反馈且与系统选中逐行同形。
- **仍未解决（都写了名字）**：这一档"够不够响"没有机器判据（通道里没有窗口底 ⇒ **103**）；
  真鼠标进出没被任何判据覆盖（自动化打不进面板 ⇒ 人工批次 **67**）；
  那层灰没有淡入（本轮判为不做，理由与代价分开记 = U-115）；
  浮层搜索框的焦点态本轮**没量**（U-116，位点清单里明写"未判"）；
  以及 **104**（证人比被告粗 ⇒ 没资格作证）。
- **下一步（R68）**：BACKLOG **104** —— 把 `FadeClockProbe` 换成与判据同一条抓帧路径、同一帧尺寸
  （760×48 那条带）、同一 runloop 节奏，并给 `controlJudgment` 加一条"证人必须不比判据粗"的闸门格；
  然后 push 让 runner 重新回答①/②（产品跳变 vs 环境未覆盖）。
  BACKLOG **99**（浮层字号 13pt vs 令牌 12pt，量了再判）与 **101/102** 排在它后面。

## R67 的 CI 附记（run 38719528833，4m37s，failure —— 红在本轮自己写的那条判据上）

- 失败点：`Swift tests (executed-count gate)` 步，`testOverlayHoverFillSharesTheSelectionPillsOutline`
  亮暗两档各三条断言全红（`药丸内缩只有 2px` / `逐行左沿差 3px` / `右沿差 3px`）。
  **产品侧那两判据（alpha 抬升、极性、宽度）在 runner 上是绿的。**
- ⇒ 这一条不是"CI 又抖了"，是 R38 那课在新判据上重犯：地板 `pillInset ≥ 4px` 与容差 `2px`
  都是从 2× 的读数写下来的，runner 是 1×。处置见 R69 / D-128 / BACKLOG 105。
- 顺带：这一遍**没跑到动效步** ⇒ BACKLOG 104 的①/②仍未回答（下一次 CI 回答）。

## R68+R69（第 70、71 轮账本 / D-127、D-128 / 结案 104 第一半，新开 105 / U-117…U-120）

- **R68**：决定表多一根轴 `witnessQualifies`（新格 `.witnessCannotAdjudicate`）+ 证人抓帧面积
  57,600pt² ⇒ 4,560pt²（被告那条带是 36,480pt² ⇒ 证人从"贵 1.6 倍"变成"1/8"）。
  合格线只依赖证人自己的量（`声明 ÷ 采样 ≥ 中间态地板 + 1`）。
  本机 `可分数段=7 合格=是`；runner `150/80=1 ⇒ 不合格 ⇒ 红着指名修证人`，不再偷偷 skip。
- **R69**：R67 那条轮廓判据在 runner 上假红（1× 上参照物量不出圆角：5.5pt ⇒ 2pt）。
  线一个数没动，改的是"这条线在哪些机器上适用"：`pillInset < 4px ⇒ FRAME_CORNER_AXIS_NOT_RUN=1`，
  保留三条两台机器都有牙的断言。**验收是电池**：R67 九刀重跑 9/9 CAUGHT、R68 六刀 6/6 CAUGHT。
- **数字**：全量 **787 / 38 skip / 0 failures / 158.4s**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、
  编译告警 0、脚本测试 139 OK。产品 0 文件 ⇒ 本机仍是 `db4872e4a852b426…`（R67 装的那份）。
- **自评**：R68 = 93、R69 = 93（曲线 n=62，见下）。
- **下一步（R70）**：BACKLOG **105** 的①——在 runner 上把 `alphaLiftProfile` 的门从 `≥4/255` 降到 `≥1/255`
  复量一次，验证"1× 量不出圆角"到底是门的问题还是通道的性质；如果是门，那条轴就能在 1× 上赎回来。
  同一次 push 还会第一次回答 BACKLOG 104（动效那一步在 runner 上到底答①还是答②）。

## R70+R71（第 72、73 轮账本 / D-129 / 结案 99、105① / U-121…U-123）

- **R70**：轮廓判据里对参照物用三道门（1/2/4）各量一遍（`OVERLAY_HOVER_DOOR`），线一个数没动。
  本机 2× `药丸@门1/2/4 = 10/11/11px` ⇒ 门在 2× 上几乎不影响 ⇒ 是门还是通道，只能由 runner 答。
- **R71 结案 BACKLOG 99**：①量完就把②的前提打掉 —— 浮层行距 33–35pt（单行）vs 侧栏 38–47pt（双行）不可比；
  真正的依据是"同一条记录的标题五处全是 `row`(12)，浮层是唯一那一处 13"。
  改：行标签 ⇒ `row`、搜索框 14 ⇒ `body`(13)（主窗口那颗就是 13）、空态同值去字面量；
  另把 `MenuBarController` 四处 / `ChineseTextContextMenu` 一处换成同值令牌（那几张帧 `CHANGED=0`）。
- **守卫补半边网**：`testTextSizesComeFromTheScale` 原来只扫 SwiftUI + `Views/` ⇒ AppKit 整个栈不在网里，
  浮层那个 13 活了六轮。现在两模式 × 两目录 + 一条喂假源码的正对照。
- **两条判据的分工**由 M381 钉：换成另一档合法令牌 ⇒ 守卫不红、产品路径判据红。
- **电池抓到我自己两次**（U-122、U-123）：正对照写成 `Array.contains("13")`（永远不可能通过）；
  M382 第一版逃掉 —— 守卫与正对照各读一份数组 ⇒ 共用 `Self.fontLiteralPatterns`（R57 那一课，犯在十分钟前）。
- **数字**：全量 **788 / 38 skip / 0 failures / 158.3s**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`（改产品那一刻 8 张）、
  编译告警 0、脚本 139 OK、电池五刀全 CAUGHT。换装 `INSTALL_RESULT=ok`（`c03cf278d3a4dd98…`，pid 29503）。
- **自评**：R70 = 92、R71 = 93（曲线 n=64、均值 92.31、`GAPS=none`）。
- **下一步（R72）**：读 R68+R69 与 R70+R71 的 CI —— 它们第一次同时回答三件事：
  BACKLOG 104 的①/②（动效那一步在 runner 上到底是产品跳变还是环境）、
  BACKLOG 105 的门假设（`OVERLAY_HOVER_DOOR` 在 1× 上的三道门读数）、
  以及 R69 那条 `FRAME_CORNER_AXIS_NOT_RUN` 有没有如约出现。
  之后回到产品面：浮层搜索框焦点态（U-116）与浮层淡入那一格（U-115）。

## R68+R69 的 CI 附记（run 38723020548 / 12m / failure —— 三条答案一次读齐）

- `FRAME_CORNER_AXIS_NOT_RUN=1` 亮暗各一条，1× 上 `药丸内缩=2px` ⇒ **R69 的处置在 runner 上生效**，
  捕获那一步不再假红。
- `MOTION_FADE_CLOCK 采样≈81ms`（R66 是 80ms）而面积小 12.6 倍 ⇒ **R68 的因果解释被证伪**；
  `MOTION_WITNESS … 可分数段=1 合格=否（判据自身 23ms）` ⇒ 新加的闸门如实拒绝免检（它按设计工作了）。
- `MOTION_FLOOR_SUITE_RED=1 … testBandCaptureIsCheaperAndStillSeesTheMotion`（26.036 > 22.200）
  ⇒ 省 1.70× 真实存在，只是不到那条本机写的 2×。
- 动效那一步仍 `exit 1` ⇒ CI 红着，这是如实记账；R72 把证人换到有资格回答的形状之后，下一次 CI 才分得出①/②。

## R72（第 74 轮账本 / D-130 / 结案 104 / U-124…U-126）

- **证人的节拍与判据对齐**（0.02 → 0.004），并把间隔与抓帧成本**分成两个数**打（`MOTION_FADE_CLOCK_COST`）。
  本机 `采样≈4ms 抓帧中位=0.1ms` ⇒ 面积不是原因、节拍才是；我上一轮拿一个数当了一个原因。
- **`bandCaptureSavingFloor` 2 → 1**：判方向不判倍数（runner 1.70× vs 本机 8.8× 是成本结构差，不是缺陷差）。
  "rect 是装饰"由几何两条拦；M384（两臂都抓整窗）四格一起红 ⇒ 降线之后牙还在。
- M385（节拍改回 0.02）**本地无判别力** ⇒ 明写"由 runner 判"，不混进 CAUGHT 计数。
- **数字**：全量 **788 / 38 skip / 0 failures / 157.7s**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、
  编译告警 0、脚本 139 OK、动效卷 46 例 0 failures / 90.4s。产品 0 文件 ⇒ 本机仍是 `c03cf278…`。
- **自评 94 / 100**（曲线 n=65、均值 92.34、`GAPS=none`）。
- **下一步（R73）**：读 R70+R71 的 CI（`OVERLAY_HOVER_DOOR` 第一次在 runner 上跑 ⇒ BACKLOG 105 的门假设有了读数）
  与 R72 的 CI（证人落到哪一档 ⇒ 104 的①/②）。之后回到产品面：
  浮层搜索框焦点态（U-116）→ 浮层淡入那一格（U-115）→ BACKLOG 95 剩下的位点。

## R70+R71 的 CI 附记（run 38725116481 / 12m42s / failure —— R73 读）

- `OVERLAY_HOVER_DOOR 缩放=1× 药丸内缩@门1/2/4 = 2/2/2px，灰带@门1/4 = 4/5px`
  ⇒ **BACKLOG 105 的①答案是"不是门"**：R69 那条机制假设作废（降到 1/255 读数不动）。
  灰带两档都量得对（1× 理论 5.2 / 实测 4–5；2× 理论 12.0 / 实测 11）⇒ 坏的是参照物那一侧。
- `MOTION_FLOOR_SUITE_RED=1 … testListRowsDoNotAnimateAndNothingClaimsTheyDo：failed - 证人读不出…连自己都分辨不了`
  ⇒ R68 那条新闸门按设计工作：证人不合格 ⇒ **红着指名**，不 skip。R72 的节拍修正正是冲着它去的。
- 动效那一步仍 `exit 1`（这一遍红的是证人不合格那一格，不是 band 那一格）
  ⇒ 下一遍（R72 之后）才知道节拍是不是全部原因。

## R73（第 75 轮账本 / D-131 / 结案 105 / U-127）

- 只改注释与台账（0 行为变化）：把 `pillInset ≥ 4` 那条的**理由**从"材质角过不了门"（假设）
  换成"1× 上参照物量不出角，而灰带两档都对"（结论），并把被证伪的假设留在原地（划掉式记账）。
- 判据处置一个字没改；BACKLOG 105 结案，赎回 1× 那条轴只剩 103（换捕获对象）。
- **数字**：全量 **788 / 38 skip / 0 failures**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本 139 OK。
- **自评 92 / 100**（曲线 n=66）。
- **下一步（R74）**：读 R72 的 CI（证人节拍 0.004 在 runner 上落到哪一档 ⇒ 104 的①/②第一次有资格的答案）。
  之后回到产品面：浮层搜索框焦点态（U-116）→ 浮层淡入那一格（U-115）→ BACKLOG 95 剩下的位点。


## R74（第 76 轮账本 / D-132 / 新开 106 / U-115 判过、U-128）

- 浮层淡入那一格（U-115）判完了，而**判的过程先把 R67 的理由杀掉**：
  帧夹具语料 6 个前缀只让整列变 1 次（我原来写的是"每个候选字都重排"），
  嵌套前缀语料才是 8 个前缀变 7 次、指针那一格换 6 次。
- 决定不变、理由换掉，并且**两个语料都留在判据里**（各带反向断言）——
  只留正面那一条，判据就退化成"挑一个能证明我的夹具"（U-128）。
- 两条同族守卫合并成一把尺 `Self.functionBody`，带正 / 反 / 右边界三格对照。
- **数字**：全量 **789 / 38 skip / 0 failures / 158.9s**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、
  编译告警 0、脚本 139 OK、电池 M386–M391 **6/6 CAUGHT**。产品 0 文件 ⇒ 不重装。
- **自评 93 / 100**（曲线见下）。
- **下一步（R75）**：**第一件事是读 R72 的 CI（run 38726667469）与 R73 的（38726991211）**
  —— 证人节拍 0.004 在 runner 上落到哪一档，是 BACKLOG 104 的①/②第一次有资格的答案。
  之后回到产品面：浮层搜索框焦点态（U-116）→ BACKLOG 95 剩下的位点 → BACKLOG 106（真实语料）。


## R75（第 77 轮账本 / D-133 / 结案 104、推进 101 / U-129、U-130）

- 三遍 runner 日志读完：**104 的①** = 那 80ms 里抓帧只占 0.4–0.5ms，其余是节拍；
  证人现在 `采样≈32ms 可分数段=4 合格=是`。
  **104 的②** = 那条红既不是产品也不是含糊的"环境"，而是 `notice-banner` 三遍都只有 2 帧，
  "变化段时长"就是一次采样间隔 ⇒ 判据在判采样。三遍 32/≥60/36ms ⇒ 红、绿、红。
- 修：`jumpAdjudication` 把证人接到 `.jump` 那一支（原来只有阳性对照问证人），
  八格真值表 + M392/M393 两刀钉住"赦免恰好一个形状"。
- 登记表按实测放宽一臂（地板 4⇒3，带 run 号），R57 那条 Swift 守卫改成
  "放宽必须带理由与 run 号"，且**读数组不读散文** —— M395 第一版逃掉就是被 note 喂饱（U-130）。
- **数字**：全量 **790 / 38 skip / 0 failures / 157.9s**、动效卷 47 例 / 3 skip / `judged=4/4`、
  `FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本 **140** OK、电池 **5/5 CAUGHT**。
  产品 0 文件 ⇒ 不重装（`git log -1 -- Sources` = `dd77480`，本机那颗是 R71 装的）。
- **自评 94 / 100**（曲线见下）。
- **下一步（R76）**：回到产品面 —— 浮层搜索框焦点态（U-116）→ BACKLOG 95 剩下的位点 →
  BACKLOG 106（真实存档上的重排频率）。动效那边欠的是 **77 路 b**（让判据不吃帧数），
  证人已经是它的验收工具。R75 的 CI 要读：`witness-snaps-here` 有没有如约出现在 runner 那一遍。


## R76（第 78 轮账本 / D-134 / 新开 107 / U-116 判完、U-131…U-133）

- 浮层搜索框焦点态（U-116，R67 起欠着）判完：**焦点反馈存在，但只在 alpha 轴上**
  （框内 1797 / 2354 个变化像素、那一格 alpha 10.71⇒6.77 与 13.15⇒8.64；亮度轴只有 -0.66 / +2.25）。
  框外 0 像素 ⇒ 这条通道看不见系统焦点环（面板 `key=false`）。
- 决定：不加自定义焦点视觉（三条理由都有读数），代价点名给真机（人工批次 68.1 / 68.2）。
- 两次错在自己新写的判据里，都当场修：一张帧减自己（那颗框建出来就聚焦，U-131）、
  `NSFocusRingType.none` 的 raw 是 1 不是 0（U-133）。
- **数字**：全量 **791 / 38 skip / 0 failures / 158.7s**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、
  编译告警 0、脚本 140 OK、电池 M398–M402 **5/5 CAUGHT**。产品 0 文件 ⇒ 不重装。
- **读 R75 的 CI（run 38735395615，绿）**：`witness-snaps-here` 如约出现、`judged=3/4`、
  `MOTION_FLOOR_OK=3/4`、`motion suite exit: 0` ⇒ R75 那一步在 runner 上落地。
  同一份日志里 `FRAME_BASELINE_CHANGED=124` 是 1× vs 2× 的已知差，那一步只判帧名齐不齐。
- **自评 94 / 100**（曲线见下）。
- **下一步（R77）**：回到动效本体 —— BACKLOG **77 路 b**（让判据不吃帧数；证人今天正是它的验收工具），
  或 BACKLOG **107**（把"轴对照"变成捕获卷的通用形状）。产品面还剩 U-116 的真机那一半与 95 的其余位点。
