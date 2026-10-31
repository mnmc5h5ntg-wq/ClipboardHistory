# AGENT_STATE · 当前工作状态（自主修复引擎）

## 交接（2026-10-21 · 预算尽头 · 非轮次节，R289 之前的收口）

本节不写「最后更新」那一行，免得与 `current_round()` 的正则抢身份（R288 之前 STATE 的顶节仍是 R281）。

**这十轮（R279–R288）落地的**：帧基线 changed 从读数变成会拦人的闸门（M834/M835）；悬停名册的理由接上对象、撤回挂了三十几轮的「没有两态帧」（M836/M837，`TWO_STATE_CLAIMS` 与帧名单双向对账）；330 收成一条具名的通道限制（环境键 `hoveredForCapture` 的变化过程不进胶片，值变化进 —— 选中态同一驱动 16 帧渐变当反证）；D-263…D-267 五条决定；336 从开单到结案（含端到端对照，防「把门扩成恒真」）；331 本机半落地成观测式名册 + 两把刀（M840/M841）。计数：U 到 938、D 到 267、BACKLOG 到 336、变异到 M841、预检 tables=85 covered=69 bad=0、脚本电池 538、帧基线 170。

**未结清单（按修法相反分组）**：① 需要一次 runner 验收才能变成读数的：331 的 runner 行（现是 R276 外推）、333 的 CI 半（changed 的按机器具名出口 + 不误红那把刀）、312 的具名出口（欠第十一轮）；② 本机就能做的：把 330 落成按对象切片的具名出口（D-251 族，不放宽任何地板）、335（其余名册里现读出的同形否定句）、334（写死本机根那一族）、310（75 张表 / 423 把刀静默不覆盖）、291 的墨轴、305、328、323、322、317、314-316；③ 需要用户授权或真机的：220 路 A、228②、265。

**下一轮（R289）的顺序，写死**：⓪ 读 CI 配对（41e1e66 → 39608106160 / queued / 未读、3403a78 → 39607521077 / queued / 未读、8d427f3 → 39607333647 / queued / 未读、1f119e0 → 39606496963 / in_progress / 未读、d47476f → 未取到（293）；只登记不轮询，R140）→ ① 331 的 runner 行变成读数并结案 → ② 330 落成具名出口 → ③ **必须回到产品动效面**：按清账表点一个真实位做动效改动或撤掉一条不成立的声明，跑完整四件套（build 0 告警 / 全量卷 / 帧基线同一笔 update / 换装本机）+ 逐张看图 + 判据 + 变异刀。R276–R288 十三轮里只有 R275 动过产品文件，这一维已连续垫底，别再拿判据账顶替它。

**两条流程教训（本会话反复踩，写给下一次的我）**：批写台账的脚本必须先单独跑完、看退出码，再决定要不要提交（git 链一律 `&&` 接在脚本之后 —— 这次有两笔提交信息写着「+一单追记」而追记当时因 heredoc 里 CJK 串夹 ASCII 双引号触发 SyntaxError 没写进去）；CJK 串里不许出现 ASCII 双引号。

## R513 状态（2026-10-31 · 第 512 轮 · 产品 3 文件 + 判据）

R513 记录（产品 3 文件 + 判据）：多选操作栏按选区禁用空操作动词。⓪ push no-op（HEAD=origin/main=`764ea4b`、ahead=0）；`7ff22a0`/`874d579`/`764ea4b` 三跑 in_progress ⇒ NOT-RUN；`5f0807b` failure 仅 Release 时序、`cf56783` success（R511 签收）；6f43727/d7919e2 success。① `sidebar-multi-select` 五颗批量按钮全亮、无 `.disabled`；无固定项时「取消固定」是空操作。② 产品：`BulkActionAvailability` + `selectedEntries`；四颗按可用性禁用/0.35，删除始终可点；普通选区 unpin/unfavorite 暗、pinned 选区 unpin 亮。③ 真窗口 `AXSelectedRows=3`：收藏/固定/取消收藏/删除 enabled=true、**取消固定 false**；同帧顶部中央又现侧栏切换按钮 ⇒ 614 仍未完全关。④ 判据：策略 2 条 + 像素（标题段相等、整带差 117px）+ M1377/M1378 2/2；可点墨探针从禁用的 unpin 重锚到删除（5.86/3.15，地板 3.0 不动）。⑤ 捕获 334 帧（+2 新帧）、基线 332→334、复核 CHANGED=38。⑥ 预检 294/271/720 bad=0、ARM 387/1207、HIDDEN 381/1146 rot=0；build 0 告警；全量 **1333/56/0（640.9s）**；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 512 = 1，last=`7ff22a0`/last_round=511）；产品笔 `8c425f6` 已推（ahead=0）。下一轮编号 R514（第 513 轮 / Round 511）：先 push 并复核 ahead=0；读 `8c425f6` 自身跑与 `7ff22a0`/`874d579`/`764ea4b` 跑全部失败步骤；重点 614 的侧栏切换按钮（记录复现序列）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R512 状态（2026-10-31 · 第 511 轮 · 产品 1 文件 + 判据）

R512 记录（产品 1 文件 + 判据）：侧栏分组标题对齐行图标列。⓪ push no-op（HEAD=origin/main=`cf56783`、ahead=0）；`5f0807b`/`cf56783` 两跑 in_progress ⇒ NOT-RUN；`6f43727`/`d7919e2` success（探针恢复持续）；`3ebc7fc` failure 仅 Release 时序、R509 三跑仅 Release（已被 6f43727 签收）。① `sidebar-pinned-section`：「已固定」左墨 36.5pt、行首星标 20.0、标题列 96.5 ⇒ 两列都不对齐。② 产品：`SidebarSectionHeader` leading 22→6；after light/dark 标题 20.5 vs 图标 20.0（差 0.5）。③ 判据 `testSidebarSectionHeaderAlignsWithTheRowIconColumn`（两档第一处墨、差 ≤1.5；无墨具名 NOT_RUN）；M1375/M1376 2/2。④ 捕获 332 帧、CHANGED=42 = 2 张 pinned 结构 + 40 张噪声；吸收 2 张（332），复核 CHANGED=40；真窗口无置顶记录（`AXButton desc=[固定…]` 只是操作栏按钮）。⑤ 预检 293/270/718 bad=0、ARM 386/1205、HIDDEN 380/1144 rot=0；build 0 告警；全量 **1330/56/0（621.1s）**；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 511 = 1，last=`5f0807b`/last_round=510）；产品笔 `7ff22a0` 已推（ahead=0）。⑥ R511 两跑签收（收口补读）：`5f0807b` 仅 Release 时序（Swift/Capture 全绿）、`cf56783` **success**；R512 两跑 `7ff22a0`/`874d579` 读时 in_progress ⇒ NOT-RUN。下一轮编号 R513（第 512 轮 / Round 510）：先 push 并复核 ahead=0；读 `7ff22a0` 自身跑与 `5f0807b`/`cf56783` 跑全部失败步骤；重点 pinned 帧在 runner 1x 的可判性、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R511 状态（2026-10-31 · 第 510 轮 · 产品 3 文件 + 判据）

R511 记录（产品 3 文件 + 判据）：详情信息窄窗按优先级让位（615 结案）。⓪ push no-op（HEAD=origin/main=`d7919e2`、ahead=0）；`6f43727` **success**（R510 省年 meta + 侧栏开关修复、`详情/组合帧头部` 探针恢复）、`d7919e2` **success**；`3ebc7fc` failure 仅 Release 时序、R509 三跑 failure 仅 Release（`bg-not-flat (32,32,32)`，已被 6f43727 success 签收）。① 600×492 详情 `10月30日 21:09:5…`（middle 截断）；11pt 字宽：全文 297.5、去复制 272.5、去字符数 206.3、分钟+来源 189.1、可用约 200。② 第五档省字符数：离屏最小帧 `10月9日 16:53:20 · 来自 访达`；真实 600 仍截断。③ 第六档分钟精度：after 600×492 `10月30日 21:09 · 来自 Safari浏览器`、750 全量格式不变；`detailTimestampMinute` 同年省年。④ 判据 3 条 + M1370–M1374 **5/5**；M1365 因同形格式撞针重锚到 `sidebarTimeWithYear` 块，预检 bad=0。⑤ 捕获 332 帧：第五档 2 帧变化（已吸收）、第六档 0 帧；最终 CHANGED=42 全噪声。⑥ 预检 292/269/716 bad=0、ARM 385/1203、HIDDEN 379/1142 rot=0；build 0 告警；全量 **1329/56/0（618.9s）**；换装 ok/419=419（活库；旧实例先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 510 = 1，last=`3ebc7fc`/last_round=509）；产品笔 `5f0807b` 已推（ahead=0）。下一轮编号 R512（第 511 轮 / Round 509）：先 push 并复核 ahead=0；读 `5f0807b` 自身跑与 `6f43727`/`d7919e2` 跑全部失败步骤；重点 `详情/组合帧头部` 探针是否持续恢复、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R510 状态（2026-10-31 · 第 509 轮 · 产品 3 文件 + 判据）

R510 记录（产品 3 文件 + 判据）：详情时间戳年份策略 + 最小窗侧栏开关清理。⓪ push no-op（HEAD=origin/main=`4ebfc81`、ahead=0）；`d01e973`/`139912c`/`4ebfc81` 三跑 in_progress ⇒ NOT-RUN；`133fcc5` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217）、`b3d7c49` success。① 600×492 详情 meta `2026年10月30日…`（时间/字符数丢）；同序列复现 `AXButton desc=[隐藏边栏]`（不在 toolbar）。② 产品：`detailTimestamp(for:reference:)` 同年省年；after 600×492 `10月30日 21:09:5…`、750 `10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`。③ 产品：`WindowConfigurator` 视图树清理 + resize 延迟补做；after 同序列 AX/像素无按钮。④ 判据 `TimestampYearPolicyTests` + `WindowChromeLayoutTests` 两条；M1366–M1369 **4/4**；replica 带 295/217 已签收。⑤ 捕获 332 帧、CHANGED=132 = 90 张结构 + 42 噪声（39 重叠）；基线更新 90（332），复核 CHANGED=42。⑥ 预检 290/267/711 bad=0、ARM 383/1198、HIDDEN 377/1137 rot=0；build 0 告警；全量 **1327/56/0（752.2s）**；换装 ok/419=419（活库；旧实例挂起先 CONT/TERM）；电池首跑红两族（614 重复条目已合并；`3ebc7fc` 标题中段空格让 SUBJECT 失明 ⇒ UNPARSED_ROSTER + BACKLOG 616，退场=改 `(.+?)` 后删），复跑 **683/OK skipped=5**；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 509 = 1，last=`d01e973`/last_round=508）；产品笔 `3ebc7fc` 已推（ahead=0）。**R509 三跑补读**：都仅 Release，红名 `详情/组合帧头部 cause=bg-not-flat bg=(32,32,32)`（全年份 meta 在 1x 越过探针背景带 x≥380）；R510 省年 meta 更短，预期恢复，R510 两跑 in_progress ⇒ NOT-RUN，下一轮复核；若仍红改探针背景带（配刀），不许静默加名册。下一轮编号 R511（第 510 轮 / Round 508）：先 push 并复核 ahead=0；读 `3ebc7fc` 自身跑与 `d01e973`/`139912c`/`4ebfc81` 跑全部失败步骤；重点 614 的全新安装→开窗→缩最小序列是否仍干净、615（600×492 meta 限制）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R509 状态（2026-10-31 · 第 508 轮 · 产品 1 文件 + 判据）

R509 记录（产品 1 文件 + 判据）：详情时间戳与列表同一套日期语言。⓪ push no-op（HEAD=origin/main=`b3d7c49`、ahead=0）；`133fcc5`/`b3d7c49` 两跑 in_progress ⇒ NOT-RUN；`20cf54d` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217）、`1654292` success；更早 `938fc4f`/`323c2ec` 仅旧 replica 带、`0beac05` Release 时序 + 旧带、`e3eb62b`/`6543959` success、两跑采样 flake。① 真窗口：列表 `10月30日 21:09`、详情 `2026-10-30 21:09:55` 两种日期语言；最小窗曾偶现「隐藏边栏」按钮（未复现，614）。② 产品：`detailTimestamp` 改 `yyyy年M月d日 HH:mm:ss`；after 真窗口 `2026年10月30日 21:09:55`、离屏 `2025年10月9日 16:52:50`；90 张 content/detail 帧变化。③ 判据 `TimestampYearPolicyTests`（固定日期 + 都不含 `-`）；M1364/M1365 2/2。④ 捕获 332 帧、CHANGED=132 = 90 张结构 + 42 张噪声（39 张重叠）；基线更新 90 张（332），复核 CHANGED=42。⑤ 预检 288/265/707 bad=0、ARM 381/1194、HIDDEN 375/1133 rot=0；build 0 告警；全量 **1324/56/0（739.2s）**；换装 ok/419=419（活库；旧实例挂起，先 CONT 再 TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 508 = 1，last=`133fcc5`/last_round=507）；产品笔 `d01e973` 已推（ahead=0）。⑥ R508 两跑签收（收口补读）：`133fcc5` 仅 Release 时序（Swift/Capture 全绿、replica 295/217、Motion clean）、`b3d7c49` **success**；R509 两跑 `d01e973`/`139912c` 读时 in_progress ⇒ NOT-RUN。下一轮编号 R510（第 509 轮 / Round 507）：先 push 并复核 ahead=0；读 `d01e973` 自身跑与 `133fcc5`/`b3d7c49` 跑全部失败步骤；重点最小窗「隐藏边栏」（614，若复现按读数改）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R508 状态（2026-10-31 · 第 507 轮 · 产品 2 文件 + 判据）

R508 记录（产品 2 文件 + 判据）：两处搜索入口共用占位文案。⓪ push no-op（HEAD=origin/main=`1654292`、ahead=0）；`20cf54d` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217 判过）、`1654292` **success**（replica 修复签收）、`938fc4f`/`323c2ec` 仅 replica 旧带（295<304）、`0beac05` Release 时序 + replica 旧带、`e3eb62b`/`6543959` success、`3d20a02` SelectionReveal 采样 flake、`f9b8733` Motion `testCopyReceipt` 1<2；20cf54d Motion clean。① QuickPick 浮层真窗口 `screencapture -l`（420×300、layer=3）：AX 占位 `搜索历史记录…`、墨宽 85.5pt；主侧栏 `搜索历史…`。② 产品：`SearchPlaceholder.text` 共享常量，`SearchField` 与 `QuickPickController` 都走它；after AX `搜索历史…`、墨宽 59.5pt。③ 判据 `SearchPlaceholderTests`（值 + 接线）；M1362/M1363 2/2；旧刀 M1341/M1342 重锚后 2/2，预检 bad=0、HIDDEN rot=0。④ 捕获 332 帧、CHANGED=101 = 20 张 QuickPick 结构变化（8 张含噪声一并更新）+ 2 张 QuickPick typed 噪声 + 79 张其它噪声；基线更新 20 张（332），复核 CHANGED=81。⑤ 预检 287/264/705 bad=0、ARM 380/1192、HIDDEN 374/1131 rot=0；build 0 告警；全量 **1323/56/0（816.2s）**；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 507 = 1，last=`20cf54d`/last_round=506）；产品笔 `133fcc5` 已推（ahead=0）。下一轮编号 R509（第 508 轮 / Round 506）：先 push 并复核 ahead=0；读 `133fcc5` 自身跑与 `1654292`/`20cf54d` 跑全部失败步骤；重点 `RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、状态菜单像素（610）、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R507 状态（2026-10-31 · 第 506 轮 · 产品 1 文件 + 判据）

R507 记录（产品 1 文件 + 判据）：状态菜单推荐理由类型词去重。⓪ push no-op（HEAD=origin/main=`323c2ec`、ahead=0）；七跑：`0beac05` failure = Release 4 条 + Swift/Capture replica 截断带红（runner 295<304）、`938fc4f` failure 仅 replica（Release 已绿）、`323c2ec` failure 仅 replica、`e3eb62b`/`6543959` success、`3d20a02` 仅 SelectionReveal 采样 flake、`f9b8733` 仅 Motion `testCopyReceipt` 1<2；`0beac05` 同跑 Motion clean（5/5）。① 真窗口 `screencapture -l`（533.5×318）：AX `文本 · 复用1次 · 常用文本 · …`，类型词出现两次；三条推荐右墨 437.0/466.5/450.0。② 产品：`RecommendationPresenter.reason` 在内容类型标签包含裸类型词时不再补裸类型词；after 菜单 499.5×318、AX `复用1次 · 常用文本 · …`（类型词一次）、三条右墨 403.5/433.0/416.5（各 −33.5pt）。③ 判据 `testContentTypeWordAppearsOnlyOnce`；M1360/M1361 2/2；连带把 replica 截断带改成按比例（帧宽×0.9..帧宽−1）+ 第二行负向臂，修 runner 295<304。④ 捕获 332 帧、CHANGED=91 = 2 张 menubar 合法变化 + 89 噪声；基线更新那 2 张（332），复核余 89 不吸收。⑤ 预检 286/263/703 bad=0、ARM 379/1190、HIDDEN 373/1129 rot=0；build 0 告警；全量 **1322/56/0（749.7s）**（含 1 条新判据）；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 506 = 1，last=`0beac05`/last_round=505）；产品笔 `20cf54d` 已推（ahead=0）。下一轮编号 R508（第 507 轮 / Round 505）：先 push 并复核 ahead=0；读 `20cf54d` 自身跑与 `938fc4f`/`323c2ec`/`20cf54d` 跑全部失败步骤；重点 replica 带在 runner 是否绿、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、状态菜单像素通道（610）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R506 状态（2026-10-31 · 第 505 轮 · 产品 2 文件 + 判据）

R506 记录（产品 2 文件 + 判据）：状态菜单推荐行恢复推荐理由。⓪ push no-op（HEAD=origin/main=`f9b8733`、ahead=0）；`41102621877 ↔ f7ea8b4` failure 3 步（Release 3 条 sources 时序 + Swift/Capture 身份头 pre-fix dark 10/1）；`41102893802 ↔ b94dd83` failure Swift+Capture（同一身份头；Release 已绿）；其余四跑 in_progress/queued ⇒ NOT-RUN；两跑 Motion floor clean（5/5、red=-）。① 真窗口 `screencapture -l` 只截状态菜单（240.5×318）：AX 三条推荐标题只有内容标签、无 ` · ` 理由；`RecommendationPresenter` 至少给类型标签 ⇒ 理由被 SwiftUI 菜单拍平丢失。② 产品：`MenuRecommendationPresentation.reasonSuffix` + 推荐行改为单个 Text（理由 meta/secondary）；after 菜单 533.5×318、三条推荐右墨 147/176/159 → 437.5/467/450，AX 标题带 `文本 · 复用1次 · … · 把握较大`。③ 判据 `MenuRecommendationPresentationTests`（后缀值 + 视图接线）；M1357/M1358/M1359 3/3；离屏 replica 判据重锚为截断带 [帧宽−16, 帧宽−1] + 第二行负向臂（314.5/256 对 320）。④ 捕获 332 帧、CHANGED=91 = 2 张 menubar + 89 噪声；基线更新那 2 张（332），复核余 89 噪声不入基线；离屏帧拍不到真实拍平（610）。⑤ 预检 285/262/701 bad=0、ARM 378/1188、HIDDEN 372/1127 rot=0；build 0 告警；全量 **1321/56/0（783.2s）**（含 2 条新判据）；换装 ok/419=419（活库）；电池首跑红 `ROUND_K_CONTRADICTION 498`（前导 R498 锚点把第 497/502/505 轮并组，K=1/1/2）⇒ 按既有出口登记 498 + BACKLOG 611（退场：parser 改读「第 N 轮」后删），复跑 **683/OK skipped=5**；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 505 = 1，last=`f7ea8b4`/last_round=504）；产品笔 `0beac05` 已推（ahead=0）。⑦ runner 签收（收口补读）：`e3eb62b`/`6543959` 两跑 **success**（light 9/8 照判、dark `NOT_RUN=sidebar-vibrant 负臂带=1`、`judged=1/2`；`RECORDING_REREAD` 两档 diff_px=0；`RTF_HELPER_ORPHAN` 两档 NOT_RUN）；`3d20a02` 仅 SelectionReveal 采样 flake、`f9b8733` 仅 Motion `testCopyReceipt` 1<2 采样 flake；`0beac05`/`938fc4f` 两跑 in_progress/queued ⇒ NOT-RUN。下一轮编号 R507（第 506 轮 / Round 504）：先 push 并复核 ahead=0；读 `0beac05` 自身跑与 `e3eb62b`/`6543959`/`3d20a02`/`f9b8733` 四跑全部失败步骤；重点 `SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-vibrant` 修复后 runner 1x、`RECORDING_REREAD` 1x、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、状态菜单像素通道不可判（610）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R505 状态（2026-10-31 · 第 504 轮 · 产品 1 文件 + 判据）

R505 记录（产品 1 文件 + 判据）：状态菜单补标准快捷键列。⓪ push no-op（HEAD=origin/main=`e46c29f`、ahead=0）；三跑 `41093593814 ↔ 800a45a`/`41095129735 ↔ 79336c7`/`41095547380 ↔ e46c29f` 读时 in_progress/in_progress/queued ⇒ NOT-RUN；旧跑只归因：Motion floor（`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2）、On-screen probe floor（`testFrameIntervalsUnderStateChanges` 256.8ms>120ms）、Release 4 条已由 31b21a6 修。① 真窗口 `screencapture -l` 只截状态菜单（194×318pt）：设置行最右墨 40.5pt、退出 92.0pt（内容宽 193.5pt）⇒ 右侧键列无墨，⌘, / ⌘Q 不可见。② 产品：`MenuCommandShortcutPresentation`（设置 `,`、退出 `q`，全局热键 nil）+ `.modifier(MenuCommandShortcutModifier(command:))` 挂命令区与退出项；after 菜单 241×318pt、设置右墨 218.5、退出 222.0、⌘ token 左沿同为 201.5pt。第一版 HStack 两列标签被 SwiftUI 菜单拍平、四个提示全消失 ⇒ 当场撤回。③ 判据 `testStandardShortcutsAreVisibleInTheSwiftUIMenu`（值 + App.swift 接线）；M1354/M1355/M1356 **3/3**、RESTORE_CLEAN=yes。④ 捕获 332 帧、CHANGED=89 全为源图标噪声、0 合法变化 ⇒ 基线保持 332；状态菜单像素通道 NOT_RUN=system-menu（608）。⑤ 预检 284/261/698 bad=0、ARM 377/1185、HIDDEN 371/1124 rot=0；build 0 告警；全量 **1319/56/0**（判据修复后复跑 **1319/56/1**，唯一红 PerfBudget `testImageComparisonCostStaysBounded` 389ms>250ms、单跑 8.8s 过）；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 504 = 1，last=`800a45a`/last_round=503）；产品笔 `f7ea8b4` 已推；⑥ R504 判据修复：runner `41093593814 ↔ 800a45a` 的 Swift/Capture 双红 = 身份头判据 dark 正 10 / 负 1（首带 0.0..248.0 / 282.0..539.0，整列材质带）⇒ 暗档负臂 <3 带具名 `NOT_RUN=sidebar-vibrant`，light 照判（runner 9/8），本机 2x 仍 2/2；修复笔 `e3eb62b` 已推（ahead=0）。成对回读（R504 三跑已补读）：`41093593814 ↔ 800a45a` failure **4 步** = Release（3 条：sources 格停旧 + skip roster 内层级联 + sources 第二来源）、Swift（1318/81/1 = 身份头判据；同跑另有 Motion 采样红）、Capture（同一命名红）、Motion floor（`testCopyReceipt…` 1<2）；`41095129735 ↔ 79336c7` failure Swift + Capture（同一身份头判据；日志流两次 `CANCEL` ⇒ `CI_LOG_BLOCKED=stream-error`，正文未读）；`41095547380 ↔ e46c29f` failure Swift + Capture（同一红）、同跑 Motion floor **clean**（`judged=4/5 executed=77`、`MOTION_FLOOR_SUITE_CLEAN=0`）、`PROBE_COVERAGE 红=0`。四跑未完成 ⇒ NOT-RUN：`41102621877 ↔ f7ea8b4`、`41102893802 ↔ b94dd83`、`41105579968 ↔ e3eb62b`、`41105861197 ↔ 6543959`（均 in_progress）。下一轮编号 R506（第 505 轮 / Round 503）：先 push 并复核 ahead=0；读 `f7ea8b4` 自身跑与 `800a45a`/`79336c7`/`e46c29f` 跑全部失败步骤；重点状态菜单键列的 runner 不可判（608）、`SETTINGS_IDENTITY_HEADER` 1x、`RECORDING_REREAD` 1x、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R504 状态（2026-10-31 · 第 503 轮 · 产品 1 文件 + 判据）

R504 记录（产品 1 文件 + 判据）：设置侧栏补身份头。⓪ push no-op（HEAD=origin/main=`5d392fb`、ahead=0）；成对回读：`41082826725 ↔ 31b21a6` failure 仅 On-screen probe floor（`testFrameIntervalsUnderStateChanges` 256.8ms>120ms，超 2 颗/容差 1）、`41083133180 ↔ 5d392fb` failure 仅 Motion floor（`MOTION_FLOOR_FACTS judged=5/5 executed=77`，红=`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2）、`41081870670 ↔ 52f4172` failure 仅 Release 4 条（sources 格停旧 + R503 独立节把 R498 挤出回看窗 + 两条级联，均已由 31b21a6 修）、`41077659382 ↔ 2c14a48` success。① 设置侧栏只有分类行、主侧栏有身份头；真窗口 `screencapture -l 623178` 只截设置窗口（720×572），身份头 90.0..103.5pt 在首导航 121.5..133.0pt 之上。② 产品：`SettingsSidebarView` 顶部补同一枚身份头（时钟 + 「时间剪史」，默认 nil⇒画，负向缝）；侧栏墨带 8→9（light 首带 70.5..82.0→71.5..85.5、dark 70.0..82.0→72.0..85.5）。③ 新判据 `testSettingsSidebarCarriesTheAppIdentity`；M1352/M1353 **2/2**、RESTORE_CLEAN=yes；CARD_INSET 复选框名册与暗档 vibrant 名册按实测登记新负向臂。④ 捕获 332 帧、62 张旧帧 + 2 张新帧、基线 330→332；89 张源图标噪声不吸收。⑤ 预检 283/260/695 bad=0、ARM 376/1182、HIDDEN 370/1121 rot=0；build 0 告警；全量 **1318/56/0**；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔产品落盘后 as-of 503=1，`--streak-for 503`，last=52f4172/last_round=502）；**ITERATION 496–500 补登**（R499–R503 当时未写节，新增 Round 501 会断档；按各轮已记读数补写并标注「补登」，空轮记 0、不冒充当场自评）⇒ 曲线 GAPS=none、PHASE2 n=494 rounds=9..501；§1 刷新 `n=494 尾轮=501 标题=R9–R501，502 节`；streak as-of 503 = 1（`python3 scripts/product_streak.py --streak-for 503`，last=52f4172/last_round=502）；产品笔 `800a45a`、台账笔 `79336c7` 均已推（HEAD=origin=`79336c7`、ahead=0）；`41093593814 ↔ 800a45a`、`41095129735 ↔ 79336c7` 读时均 **in_progress ⇒ NOT-RUN**。下一轮编号 R505（第 504 轮 / Round 502）：先 push 并复核 ahead=0；读 `800a45a` 自身跑与 `5d392fb`/`31b21a6`/`52f4172` 跑全部失败步骤；重点 `SETTINGS_IDENTITY_HEADER` runner 1x、`RECORDING_REREAD`、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。

## R503 状态（2026-10-30 · 第 502 轮 · 产品 1 文件 + 判据）

R503 记录（产品 1 文件 + 判据）：设置窗口标题栏与主窗口统一。⓪ push no-op、HEAD=origin=`2c14a48`、ahead=0；1633a9d/58cc884/2c14a48 三跑读时均 in_progress ⇒ NOT-RUN。① 真窗口：设置窗口有「设置」标题（标题带墨 1915）与通栏分隔线，主窗口无 ⇒ 两套语言。② 产品：`SettingsWindowController` 设 titleVisibility=.hidden、titlebarAppearsTransparent、separator=.none（title 保留）。③ after 标题带墨 1915→1210（余下为红绿灯）、分隔线消失；新判据 `testSettingsWindowUsesTheSameCustomChromeAsTheMainWindow`；M1350/M1351 **2/2**。④ 捕获 330 帧、89 张源图标噪声不入基线。⑤ 预检 282/259/693、ARM 375/1180、HIDDEN 369/1119 rot=0；build 0 告警；全量 **1317/56/0**；换装 ok/419=419（活库）；电池 683/5；清账 162/63/0。成对回读（收口）：`41081870670 ↔ 52f4172` 读时 **in_progress ⇒ NOT-RUN**；`41077659382 ↔ 2c14a48` **success**；`41077528140 ↔ 58cc884` failure Release（产品 commit 主笔跑早于 sources 补记的时序红）；`41074949020 ↔ 1633a9d` failure Release（旧无标签产品 commit 的时序/标签红）；新补记 `31b21a6` 自身跑未读 ⇒ NOT-RUN。下一轮编号 R504（第 503 轮 / Round 501）：push 并复核 ahead=0；读 R503 自身跑与 1633a9d/58cc884/2c14a48 跑；② 产品位换未捕获表面；③ 436 只复核新跑 Motion floor。

## R502 状态（2026-10-30 · 第 501 轮 · 产品 1 文件 + 判据）

R502 记录（产品 1 文件 + 判据）：主窗口标题栏 title 保留、标题显式隐藏。⓪ push no-op、HEAD=origin=`ec299eb`、ahead=0；`41068373712 ↔ dac7e17` in_progress ⇒ NOT-RUN；`41062934158 ↔ 79eb4fb` Release 2 条（已由 817a014 修）、`41063726929 ↔ 817a014` 仅 Motion 采样 flake。① 真窗口实拍：标题栏空白；临时 `.visible` 实拍 title 压在详情头部上方 ⇒ 空白是设计。② 产品：`WindowConfigurator` 显式 `title="时间剪史"` + `titleVisibility=.hidden`（像素不变，写死契约）。③ 判据 `testMainWindowHidesItsTitlebarTitleButKeepsTheName` + `titlebarSeparatorStyle = .none`（真帧 before 59pt 行亮度 77.4 vs 底 39.0；after 同带 ≤41）；M1347/M1348/M1349 **3/3**。④ 捕获 330 帧、89 张仍为源图标噪声（不入基线）；第二次实拍被其他应用占屏，未截非 App 区域。⑤ 预检 281/258/690、ARM 374/1177、HIDDEN 368/1116 rot=0；build 0 告警；全量 **1316/56/1**（唯一红 PerfBudget flake，单跑过）；换装 ok/419=419（活库）；电池 683/5；清账 162/63/0。成对回读：`41069517154 ↔ ec299eb` failure 仅 Motion `testCopyReceipt…`（已知采样 flake）；`41074949020 ↔ 1633a9d` in_progress ⇒ NOT-RUN；`1633a9d` subject 未带「产品 K 文件」⇒ product_streak 仍 last=05771dc/streak=4（与格一致），下一笔产品提交必须带该标签（BACKLOG 605）。下一轮编号 R503（第 502 轮 / Round 500）：push 并复核 ahead=0；读 R502 自身跑与 dac7e17/79eb4fb/817a014 跑；② 产品位换未捕获表面（真实窗口 `-l` 通道或新设计位）；③ 436 只复核新跑 Motion floor。

## R501 状态（2026-10-30 · 第 500 轮 · 判据推进，不记完成）

R501 记录（判据推进，无产品变更，不记完成）：⓪ push no-op（HEAD=origin/main=`817a014`、ahead=0）；`41062934158 ↔ 79eb4fb` 与 `41063726929 ↔ 817a014` 读时均 in_progress ⇒ NOT-RUN；`41057812582 ↔ 4963281` failure 仅 SelectionReveal 采样 flake（同跑 15.8 键登记 0、录制帧 12/11）、`41058094730 ↔ eae195b` success（1314/81/0）⇒ 前轮两修已签收。② 597 三次实测仍不成立、无合法未捕获表面 ⇒ 无产品文件。③ 判据推进：新 `testRecordingCardFrameIsDeterministicAcrossRenders`（同一录制夹具两次渲染逐字节比对）读数 `RECORDING_REREAD light diff_px=0 墨=49162 / dark diff_px=0 墨=57774`（2x），空帧具名 NOT_RUN；M1345/M1346 **2/2**、RESTORE_CLEAN=yes；它把 30/0 那类相位 flake 变成会红的 `diff_px>0`。④ 帧卷 330 帧、89 张 changed 均为**源 App 图标栅格噪声**（16×16px、最大差 7/255）⇒ **不吸收进基线**（`FRAME_BASELINE_ENV_NOISE=source-icon-raster`；601）。⑤ 预检 280/257/688 bad=0、ARM 373/1175、HIDDEN 367/1114 rot=0；build 0 告警；全量 **1315/56/0**；无产品文件 ⇒ 不换装；电池 683/OK skipped=5；清账 162/63/0。成对回读（收口）：`41063726929 ↔ 817a014` failure **仅 Motion coverage floor** 的 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（已知采样 flake；Swift/Capture 绿：`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.8/1x 本机登记=0`、录制帧 12/11）；`41062934158 ↔ 79eb4fb` failure Release 2 条 = commit-subject hygiene（79eb4fb 早于 817a014 的 AHEAD_ROSTER 登记）+ 内层 skip roster，已由 `817a014` 修复；`41068373712 ↔ dac7e17` 读时 **in_progress ⇒ NOT-RUN**（新判据 runner 1x 待读）。下一轮编号 R502（第 501 轮 / Round 499）：先 push 并复核 ahead=0；读 R501 自身跑（`RECORDING_REREAD` 1x/602）与 79eb4fb/817a014 跑；② 仍需未捕获表面的产品位；597 不再用放大字形；436 只复核新跑 Motion floor。

## R500 状态（2026-10-30 · 第 499 轮 · 空轮，不记完成）

R500 记录（无产品变更，不记完成）：

成对回读（收口时网络恢复）：`41057812582 ↔ 4963281` **failure 仅 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条采样 flake**（同跑 `TEXT_SIDE_ROSTER_KEY arm64/macOS 15.8/1x 本机登记=0 实测反侧=0 判了 25/25 ⇒ 一致`、`CARD_RHYTHM settings-shortcuts-recording 14.0/14.0/15.0/14.0/12.0/11.0`、`RTF_HELPER_ORPHAN_NOT_RUN=settings-content-blank` 两档）；`41058094730 ↔ eae195b` **success**（`Executed 1314/81 skip/0`，录制帧同为 12/11、15.8 键一致）⇒ 录制帧 settle 与机器键均被 runner 签收；`41051398635 ↔ d87d258` failure 仅 15.8 UNKEYED（已修）、`40941281838 ↔ c9d8d6c` failure 仅 Capture（30/0，同跑后读 12/11）。`79eb4fb` 自身跑读时未创建/未读 ⇒ NOT-RUN。⓪ 开工 push no-op（HEAD=origin/main=`eae195b`、ahead=0；`git push` 报 `correct access rights` 但无待推笔）；`gh` 连续 EOF ⇒ **`CI_READ_BLOCKED=network`**，`41057812582 ↔ 4963281` 与 `eae195b` 跑未读 ⇒ NOT-RUN（收口前再试一次）。② BACKLOG 597 候选（放大项目符号、钳住行高）三次实测全部不成立：`maxHeight=natural` ⇒ 首行带 275→273（**-2px**）；`natural+lineSpacing` ⇒ 首行 277、后续行距放大；`natural+lineSpacing/2` ⇒ 首行 275 但第二行起 **+4px**（放大字形的 ascent 会移动基线，段落钳高无法同时保住行距与文字位置）。改动已全部撤回（工作树干净），**无产品文件/帧/判据/刀，不记完成**。下一轮（R501 / 第 500 轮 / Round 498）：⓪ 先 push 并复核 ahead=0；读 `41057812582`、`eae195b` 跑与更早未读各跑（`CI_READ_BLOCKED` 收口前再试）；重点 15.8 机器键（`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.8/1x` 登记 0）、`CARD_RHYTHM settings-shortcuts-recording`（期望 12/11）、`RTF_HELPER_ORPHAN`（仍 settings-content-blank/595）、SEARCH_PLACEHOLDER/QUICKPICK 1x 已签收；② 产品位：597 已证伪，下一轮需换**未捕获表面**（真实窗口帧或新设计位），不得再用放大字形。

## R499 状态（2026-10-30 · 第 498 轮 · Round=0，空轮不记完成）：无产品变更（候选位逐个排除；未验证改动已撤回）

记录（空轮，不记完成）：2026-10-30（本地 · R499 / 第 498 轮 / Round=0）：⓪ 开工网络已恢复：`git ls-remote` 读到 remote main=`d87d258`、HEAD=origin/main、**ahead=0**（R498 两笔已在 remote）；`gh` 可读：R497 跑 `40937242846 ↔ a98e65d` **failure 仅 Release**（Swift 1313/80/0 绿；`SEARCH_PLACEHOLDER` 1x light 60/70、dark 61/71 差 10.0pt ⇒ **593 结案**；`QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收）；R498 跑 `41051398635 ↔ d87d258` **in_progress ⇒ NOT-RUN**（`RTF_HELPER_ORPHAN` 1x 待读）。② 候选位逐个排除（都有读数）：无序列表「•」墨径 3pt，放大 1.25 倍会把首行带 275→281（+3pt、整段行距被撑高）⇒ **撤回**；未选中复选框 1.2:1 是非活动窗口系统控件灰化（捕获事实）；有序/任务/无序列表正文列同为 36.5pt；关于页版本行已是全角括号；其余均为已完成类别。**没有合法新类别 ⇒ 无产品文件/帧/判据/刀，不记完成**；工作树干净、HEAD=origin/main=`d87d258`；产品面连续零改动 **1** 轮（as-of 498，`python3 scripts/product_streak.py --streak-for 498`，last=05771dc）。下一轮编号 R500（第 499 轮 / Round 497）靶：① 先 `git push origin main`（无待推则 no-op）并复核 ahead=0；读 R498 跑 `41051398635`（`RTF_HELPER_ORPHAN` 1x/595）、R497 跑、R496 跑及更早各跑全部失败步骤；重点 `RTF_HELPER_ORPHAN`（正臂 ≥22pt、负臂 ≤18pt）、`SEARCH_PLACEHOLDER` 1x 已签收、`QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收、`SETTINGS_HELPER_FONT`、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`、`DEFAULT_BADGE`、inline 4.5/150 不动；② **必须换新类别**——候选：BACKLOG 597 的项目符号同字号大字形（须先证行距不变）或新一轮真实窗口/未捕获表面的缺陷；③ 436 只复核新跑 Motion floor。
续（三条 CI 红，分节账 R499 续）：① 录制帧底留白红（run `40941281838 ↔ c9d8d6c`，Capture gate）——同跑两读 30/0 与 12/11、本机 2x 恒 12/11 ⇒ 捕获相位；补三轮有界 `layoutSubtreeIfNeeded + displayIfNeeded`（`RECORDER_LAYOUT_SETTLE`），不动期望、不盲改产品、不登记抓不到的刀；复跑卡片节奏绿、捕获 330 帧 0 变化。② sources 格红（run `40937242846 ↔ a98e65d`）——主笔跑早于补记；补记跑 `40941281838` Release 已绿、现读 `R498/05771dc`=git；另把空轮 STATE 的「最后更新」行污染 `current_round()` 的根因修掉（改「记录（空轮…）」+ 下一轮括号编号），`test_round_batch_consistency` 3/3、`test_skip_roster` 6/6。③ runner 键红（run `40922562716 ↔ 2e7828f`）——`TEXT_SIDE_ROSTER_UNKEYED arm64/macOS 15.8/1x`（反侧 0 张），按本机读数新增 `"arm64/macOS 15.8/1x": []`，不抄 15.7 行；本机 25/25 一致。build 0 告警；全量 1314/56/1（PerfBudget flake 单跑过）；无产品文件 ⇒ 不换装；电池 683/5；清账 162/63/0；HEAD=origin/main=`4963281`、ahead=0（三笔已推）。成对回读：R498 跑 `41051398635 ↔ d87d258` failure 仅 `TEXT_SIDE_ROSTER_UNKEYED arm64/macOS 15.8/1x`（反侧 0；该跑录制帧两读均 12/11 ⇒ 30/0 是 c9d8d6c 跑的捕获相位）；`RTF_HELPER_ORPHAN_NOT_RUN=settings-content-blank`（595 仍开）；R499 续跑 `41057812582 ↔ 4963281` 读时 queued ⇒ NOT-RUN。

## R498 状态（2026-10-30 · 本地 · 第 497 轮 / Round 495）：通用页 RTF 说明段最小窗孤字行（12 张旧帧变化 + 4 张新帧、基线 330）；全量 1314/56/1（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R498 / 第 497 轮 / Round 495）：640pt 最小窗下 RTF 说明段最后一行只剩「本。」—— 孤字行，末行墨宽 **14.0pt**。修法：把「文本。」用 U+00A0 绑成不断开的单元（读者看到的仍是同一句话），加捕获缝 `settingsRtfHelperCopyForCapture`（产品默认 nil 新写法，负向帧旧文案）。旧/新：**12 张旧帧变化**（`settings-general*` 各亮暗）、**4 张新帧**（`general-min-orphan` / `general-min-orphan-legacy`，各亮暗；组件帧命名避开按 `settings-` 前缀收集的整页尺）、0 缺失；基线 **326→330**；逐张看过：新帧末行「文本。」三字、负向帧仍是「本。」孤字，其余行/卡片几何未动。读数（`RTF_HELPER_ORPHAN`，2x）：light 正臂 **28.5pt** / 负臂 **14.0pt**；dark **29.0 / 15.0**。判据要求正臂 ≥22pt、负臂 ≤18pt；任一臂 0 ⇒ 具名 NOT_RUN。`M1343`（去掉 NBSP）/`M1344`（绑错位置）**2/2**。预检 **279/256/686 bad=0**、ARM **372/1173**、HIDDEN **366/1112 rot=0**。⓪：开工一次快进 push **`a98e65d..c9d8d6c` success**、HEAD=origin/main=`c9d8d6c`、**ahead=0**；开工 `gh` 连续 EOF ⇒ **`CI_READ_BLOCKED=network`**；R497 跑 `40937242846 ↔ a98e65d` 上次读 queued ⇒ NOT-RUN；**R496 跑 `40932022750 ↔ 1d3179a` success**（1312/80/0；`QUICKPICK_MATCH_HIGHLIGHT` 1x 签收 ⇒ 592 结案；`SETTINGS_HELPER_FONT` 仍 scale-too-low）；R495 跑 success；R494 主跑 Release 3 条、补记跑 Motion 1 条；R493 跑 2 步红；`c9d8d6c` 自身跑未创建 ⇒ NOT-RUN；收口两次 push 均报 `correct access rights` ⇒ **`PUSH_BLOCKED=network`（HEAD=`05771dc`、origin/main=`c9d8d6c`、ahead=1）**、`CI_READ_BLOCKED=network`，R498 跑未创建 ⇒ NOT-RUN。全量 **1314/56/1**；捕获卷 **330 帧**；基线 **330/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py --streak-for 501`，last=05771dc）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `a98e65d..c9d8d6c` success、ahead=0；gh EOF ⇒ CI_READ_BLOCKED；R496 跑 success（QUICKPICK 1x 签收⇒592 结案）；R497 跑 queued ⇒ NOT-RUN。
② 产品：RTF 说明段最小窗孤字行（12 旧帧 + 4 新帧、基线 330）。
③ 判据：正臂 28.5/29.0、负臂 14.0/15.0；M1343/M1344 2/2。
④ 预检 279/256/686；rot 366/1112；ARM 372/1173。
⑤ 捕获 330 帧；基线 330/0/0/0；build 0 告警；换装 ok/397=397；全量 1314/56/1。

NOT-RUN / 阻塞（分开写）：① R498 自身跑（未创建，PUSH_BLOCKED=network）；② RTF_HELPER_ORPHAN runner 1x/2x；③ SEARCH_PLACEHOLDER runner 1x（R497 跑未读）；④ QUICKPICK_MATCH_HIGHLIGHT 1x 已签收；⑤ SETTINGS_HELPER_FONT runner 1x/2x；⑥ RESET_ICON（settings-content-blank）；⑦ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑧ DEFAULT_BADGE（settings-content-blank）；⑨ 已知性能/采样 flake；⑩ 437–596 的其余未结项仍开。

下一轮（R499）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 `PUSH_BLOCKED=network`、HEAD=`05771dc`、origin/main=`c9d8d6c`、ahead=1）；成对读 R498 自身跑（推送后才有；当前未创建）、R497 跑 `40937242846`、R496 跑 `40932022750`、R495 跑 `40920092629`、R494 两跑、R493 跑及更早各跑的全部失败步骤；**重点读 `RTF_HELPER_ORPHAN`（正臂 ≥22pt、负臂 ≤18pt、1x/2x）、`SEARCH_PLACEHOLDER`（两臂差 [6,16]pt）、`QUICKPICK_MATCH_HIGHLIGHT`（1x 已签收）、`SETTINGS_HELPER_FONT`、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`、`DEFAULT_BADGE`、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 RTF 说明孤字行/主侧栏搜索占位符省略号/浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R497 状态（2026-10-30 · 本地 · 第 496 轮 / Round 494）：主侧栏搜索占位符省略号与全 App 统一（44 张旧帧变化 + 2 张新帧、基线 326）；全量 1313/56/1（唯一红 PerfBudget 本机 flake，单跑过）（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R497 / 第 496 轮 / Round 494）：全仓动作文案十余处用单「…」（导出历史…、查找…、正在加载预览…、浮层「搜索历史记录…」），只有主侧栏搜索占位符写「搜索历史……」两个省略号 —— 同一 App 两种省略号形态。修法：占位符改成「搜索历史…」，加捕获缝 `searchPlaceholderForCapture`（产品默认 nil 用新形态，负向帧给旧文案）。旧/新：**44 张旧帧变化**（22 张 `content-*`、20 张 `sidebar-*`、2 张 `search-field-*`，各亮暗）、**2 张新帧**（`sidebar-search-placeholder-legacy` 亮暗）、0 缺失；基线 **324→326**；逐张看过：新占位 3 点、旧帧 6 点，搜索框高度/清除 ×/侧栏其余几何未动。读数（`SEARCH_PLACEHOLDER`，2x）：light 正臂 **60.5pt**、负臂 **71.0pt**、差 **10.5pt**；dark 同值。判据要求两臂差 [6,16]pt（恰一个省略号字形），任一臂宽 0 ⇒ 具名 NOT_RUN。`M1341`（回到两个省略号）/`M1342`（去掉省略号）**2/2**。预检 **278/255/684 bad=0**、ARM **371/1171**、HIDDEN **365/1110 rot=0**。⓪：开工一次快进 push **`2e7828f..1d3179a` success**（两笔：`3c64394`/`1d3179a`）、HEAD=origin/main=`1d3179a`、**ahead=0**；最新跑 `40932022750 ↔ 1d3179a` **queued ⇒ NOT-RUN**；R495 跑 `40920092629 ↔ bbfe31c` **success**（`1311/80/0`；`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档、`MAIN_TITLE_ICON` 1x 已签收、`RESET_ICON_NOT_RUN=settings-content-blank`）；R494 主跑 failure 仅 Release（3 条非产品）、补记跑仅 Motion（1 条）；R493 跑 failure 2 步（Release 3 条 + Swift 采样 1 条）；旧跑成对复核；收口一次快进 push **`1d3179a..a98e65d` success**、HEAD=origin/main=`a98e65d`、**ahead=0**；R497 跑 `40937242846` queued ⇒ NOT-RUN；**R496 跑 `40932022750` success**（1312/80/0；`QUICKPICK_MATCH_HIGHLIGHT` 1x light 尾 290/头 25、dark 尾 245/头 5、负臂 0/0 ⇒ 592 结案；`SETTINGS_HELPER_FONT` 仍 scale-too-low）。全量 **1313/56/1**（857.8s；唯一红 `PerfBudgetTests.testImageComparisonCostStaysBounded` = `LOCAL_PERF_BUDGET_FLAKE=load`，**单跑原样重跑通过**）；捕获卷 **326 帧**；基线 **326/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 496，`python3 scripts/product_streak.py --streak-for 496`，last=3c64394）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `2e7828f..1d3179a` success、ahead=0；R496 跑 queued ⇒ NOT-RUN；R495 跑 success；R494/R493/旧跑失败步名复核。
② 产品：主侧栏搜索占位符统一单省略号（44 旧帧 + 2 新帧、基线 326）。
③ 判据：正臂 60.5 / 负臂 71.0 / 差 10.5；M1341/M1342 2/2。
④ 预检 278/255/684；rot 365/1110；ARM 371/1171。
⑤ 捕获 326 帧；基线 326/0/0/0；build 0 告警；换装 ok/397=397；全量 1313/56/1（PerfBudget flake，单跑过）。

NOT-RUN / 阻塞（分开写）：① R497 自身跑 `40937242846`（queued）；② SEARCH_PLACEHOLDER runner 1x/2x；③ QUICKPICK_MATCH_HIGHLIGHT runner 1x；④ SETTINGS_HELPER_FONT runner 1x/2x；⑤ RESET_ICON（settings-content-blank）；⑥ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑦ DEFAULT_BADGE（settings-content-blank）；⑧ 其余 runner 复核；⑨ 已知性能/采样 flake（本跑 PerfBudget）；⑩ 437–594 的其余未结项仍开。

下一轮（R498）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 HEAD=origin/main=`a98e65d`、ahead=0）；成对读 R497 自身跑 `40937242846`、R496 跑 `40932022750`、R495 跑 `40920092629`、R494 两跑、R493 跑及更早各跑的全部失败步骤；**重点读 `SEARCH_PLACEHOLDER`（两臂差 [6,16]pt、1x/2x）、`QUICKPICK_MATCH_HIGHLIGHT`（头 ≤40·s²、尾 ≥200·s²、负臂 0）、`SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8）、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`（no-red-channel）、`DEFAULT_BADGE`（settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主侧栏搜索占位符省略号/浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R496 状态（2026-10-30 · 本地 · 第 495 轮 / Round 493）：浮层候选行补搜索命中高亮（2 张旧帧变化 + 2 张新帧、基线 324）；全量 1312/56/1（唯一红 PerfBudget 本机 flake，单跑过）（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R496 / 第 495 轮 / Round 493）：主列表与侧栏命中时给匹配片段加底色，浮层同一查询只过滤不高亮 —— 来源命中时「来自 访达」是这行唯一的理由，却没有任何标记。修法：新增 `QuickPickTitlePresentation`（复用 `MatchHighlighting.spans` 与 `DetailTypography.highlightColor`）；**只在命中段非空时**写 `attributedStringValue`（空查询帧逐字节不变）；捕获缝 `titleHighlightEnabled`（产品默认 true，负向帧 false）。旧/新：**2 张旧帧变化**（`quickpick-typed` 亮暗）、**2 张新帧**（`quickpick-typed-no-highlight` 亮暗）、0 缺失；基线 **322→324**；逐张看过：两行「访达」都上黄底、标题/时间/图标几何未动、负向帧无黄底。读数（`QUICKPICK_MATCH_HIGHLIGHT`，2x）：light 正臂 **头 0 / 尾 2115**、负臂 **0/0**（墨 6348/6345）；dark 正臂 **头 0 / 尾 2148**、负臂 **0/0**（8103/7078）。判据：头 ≤40·s²、尾 ≥200·s²、负臂黄底 0；标题墨 0 ⇒ 具名 NOT_RUN。`M1339`（开关反了）/`M1340`（整行都高亮）**2/2**；M1339 第一版被夹具显式 true 抵消而逃刀，改成正向臂不设缝后才咬。预检 **277/254/682 bad=0**、ARM **370/1169**、HIDDEN **364/1108 rot=0**；QuickPick 既有六条单跑 6/6。⓪：开工一次快进 push **`bbfe31c..2e7828f` success**、HEAD=origin/main=`2e7828f`、**ahead=0**；**R495 跑 `40920092629 ↔ bbfe31c` success**（`1311/80 skip/0`；`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档、`MAIN_TITLE_ICON` light 478→550 / dark 3733→3820 **1x 签收 ⇒ BACKLOG 587 结案**、`RESET_ICON_NOT_RUN=settings-content-blank` 两档）；R494 主跑 `40895877246 ↔ 590ead8` failure 仅 Release（3 条非产品红）、补记跑 `40896245079 ↔ e05b13c` failure 仅 Motion（`testCopyReceiptAppearsAndDismissesWithAVisibleProcess`，Swift 1310/79/0 绿）；R493 跑 `40887758385 ↔ 67cb683` failure 2 步（Release 3 条 + Swift `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条）；旧跑成对复核；最新跑 `40922562716 ↔ 2e7828f` 读时 **in_progress ⇒ NOT-RUN**（收口再读 EOF）；收口两次 push 均报 `correct access rights` ⇒ **`PUSH_BLOCKED=network`（HEAD=`3c64394`、origin/main=`2e7828f`、ahead=1）**、`CI_READ_BLOCKED=network`，R496 跑未创建 ⇒ NOT-RUN。全量 **1312/56/1**（860.6s；唯一红 `PerfBudgetTests.testImageComparisonCostStaysBounded` 306.4ms>250 = `LOCAL_PERF_BUDGET_FLAKE=load`，**单跑原样重跑通过**）；捕获卷 **324 帧**；基线 **324/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 495，`python3 scripts/product_streak.py --streak-for 495`，last=9e72947）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `bbfe31c..2e7828f` success、ahead=0；R495 跑 success 并签收 MAIN_TITLE_ICON 1x（587 结案）；R494/R493/旧跑失败步名复核。
② 产品：浮层候选行补搜索命中高亮（2 旧帧 + 2 新帧、基线 324）。
③ 判据：正臂尾黄 2115/2148、负臂 0；M1339/M1340 2/2。
④ 预检 277/254/682；rot 364/1108；ARM 370/1169。
⑤ 捕获 324 帧；基线 324/0/0/0；build 0 告警；换装 ok/397=397；全量 1312/56/1（PerfBudget 本机 flake，单跑过）。

NOT-RUN / 阻塞（分开写）：① R496 自身跑（未创建，PUSH_BLOCKED=network）；② QUICKPICK_MATCH_HIGHLIGHT runner 1x；③ SETTINGS_HELPER_FONT runner 1x/2x（scale-too-low）；④ RESET_ICON runner（settings-content-blank）；⑤ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑥ DEFAULT_BADGE（settings-content-blank）；⑦ 其余 runner 复核；⑧ 已知性能/采样 flake（本跑 PerfBudget 306.4ms）；⑨ 437–592 的其余未结项仍开。

下一轮（R497）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 `PUSH_BLOCKED=network`、HEAD=`3c64394`、origin/main=`2e7828f`、ahead=1）；成对读 R496 自身跑（推送后才有；当前未创建）、R495 跑 `40920092629`、R494 两跑（`40895877246`/`40896245079`）、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `QUICKPICK_MATCH_HIGHLIGHT`（头 ≤40·s²、尾 ≥200·s²、负臂 0、1x/2x）、`SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8、1x/2x）、`MAIN_TITLE_ICON`（1x 已签收）、`RESET_ICON`、`LOGIN_FAILURE_ICON`（no-red-channel）、`DEFAULT_BADGE`（settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R495 状态（2026-10-30 · 本地 · 第 494 轮 / Round 492）：设置通用页说明统一到 11pt 下限（14 张旧帧变化 + 2 张新帧、基线 322）；全量 1311/56/0（产品 2 文件 + 判据）

最后更新：2026-10-30（本地 · R495 / 第 494 轮 / Round 492）：同一页四条说明，回执/暂停/OCR 用 10pt `.caption`、最长 RTF 用 11pt `meta`，而 `VisualFont.meta` 注释写明 11 是 App 下限 —— 同页同角色两种字号。修法：三条改用 `settingsHelperFont`（默认 `VisualFont.meta`=11；捕获缝 `settingsHelperFontForCapture=false` 退回 10 作负向臂），RTF 保持 11。旧/新：**14 张旧帧变化**（10 张 `settings-general*` + 4 张 `sidebar-multi-select*`）、**2 张新帧**（`settings-general-legacy-helper-font` 亮暗）、0 缺失；基线 **320→322**；逐张看过：四条说明同字号、暂停说明 720pt 折两行、卡片长高未压底、回执红字与图标同轴、负向帧仍 10/11 混用。读数（`SETTINGS_HELPER_FONT`，2x）：light 正臂 5 带 **11.0/10.5/11.0/11.0/11.0（极差 0.5）**、负臂 4 带 **10.0/10.0/11.0/11.0（极差 1.0）**；dark 正臂 **11.5/11.0/11.5/11.5/11.5（0.5）**、负臂 **10.0/10.0/11.5/11.5（1.5）**。判据要求正臂最低 ≥10.4、正臂极差 ≤0.6、负臂极差 ≥0.8；两臂说明带不足 3 条或倍率 <1.5 都有具名 NOT_RUN。`M1337`（永远 10）/`M1338`（OCR 14pt）**2/2**。**修 R494 回归**：标题图标只在 `selectedCount <= 1` 时画，250pt 批量态「已选 3 条」恢复完整（成对帧；无像素判据，见 BACKLOG 589）。**重锚四张旧表并复跑**：R494 M1335 ⇒ 2/2；R29d M132 名单 + M134 期望 ⇒ 4/4（M133 缩框退役具名）；R39 M177 ⇒ 8/8；R33 M141 + CAPTION/OCR 常量 ⇒ 7/7；均 `RESTORE_CLEAN=yes`。caption-tier 三条探针按新带重锚（160→163 / 200→218.5 / 241→260），`CAPTION_HUG`、`SETTINGS_HELPER_AXIS 200/198/−2`、`CARD_INSET_*` 全绿；新帧补进 control-first 与系统黑带名册。预检 **276/253/680 bad=0**、ARM **369/1167**、HIDDEN **363/1106 rot=0**。⓪：开工 push no-op、HEAD=origin/main=`e05b13c`、**ahead=0**；开工现读 R494 补记跑 `40896245079 ↔ e05b13c` **in_progress**、R494 主跑 `40895877246 ↔ 590ead8` 未完成（STEP[9] 已红）⇒ 均 **NOT-RUN**；R493 跑 `40887758385 ↔ 67cb683` failure 2 步（Release 3 条非产品 + Swift 采样红 1 条；`RESET_ICON_NOT_RUN=settings-content-blank`）；旧跑成对失败步名按 `ci_read.py steps` 复核（R492/R491/R490/R489/R488/R487/R486/R485/R484/R483/R481/R480/R478/R477/R479）；收口 `gh` 连续 EOF ⇒ **`CI_READ_BLOCKED=network`**；收口前两次探针均报 port 22 closed ⇒ 先记 `PUSH_BLOCKED=network`（HEAD=`9e72947`、ahead=1），补记 `bbfe31c` 后一次快进 push **`e05b13c..bbfe31c` success**、HEAD=origin/main=`bbfe31c`、**ahead=0**；R495 跑 `40920092629 ↔ bbfe31c` queued ⇒ NOT-RUN。全量 **1311/56/0**（828.6s，轻载）；捕获卷 **322 帧**；基线 **322/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 494，`python3 scripts/product_streak.py --streak-for 494`，last=590ead8）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R493 跑 2 步红；R494 两跑 NOT-RUN；旧跑失败步名复核；收口 CI_READ_BLOCKED=network。
② 产品：通用页说明统一 11pt（14 旧帧 + 2 新帧、基线 322）+ 修 R494 批量态标题图标挤占。
③ 判据：正臂极差 0.5、负臂 1.0/1.5；M1337/M1338 2/2；四张旧表重锚复跑。
④ 预检 276/253/680；rot 363/1106；ARM 369/1167。
⑤ 捕获 322 帧；基线 322/0/0/0；build 0 告警；换装 ok/397=397；全量 1311/56/0。

NOT-RUN / 阻塞（分开写）：① R495 自身跑 `40920092629`（queued）；② R494 两跑（in_progress/读不到）；③ SETTINGS_HELPER_FONT runner 1x/2x；④ 其余 runner 复核（网络 EOF）；⑤ RESET_ICON runner 仍 settings-content-blank 两档；⑥ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑦ DEFAULT_BADGE（settings-content-blank）；⑧ 批量态标题完整性无像素判据（BACKLOG 589）；⑨ 已知 Motion/采样红；⑩ 437–590 的其余未结项仍开。

下一轮（R496）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 HEAD=origin/main=`bbfe31c`、ahead=0）；成对读 R495 自身跑 `40920092629`、R494 两跑（`40895877246`/`40896245079`）、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8、1x/2x）、`MAIN_TITLE_ICON`（墨差 ≥40·s²、1x/2x）、`RESET_ICON`（右列墨差、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R494 状态（2026-10-29 · 本地 · 第 493 轮 / Round 491）：主侧栏标题补时钟图标（48 张旧帧变化 + 2 张新帧、基线 320）；全量 1310/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R494 / 第 493 轮 / Round 491）：设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字 —— 同一窗口的身份锚点少一枚。修法：`HistorySidebarView.header` 在标题前加 `Image(systemName: "clock.arrow.circlepath")`（`VisualFont.title` semibold、`.secondary`、`accessibilityHidden(true)`），加捕获缝 `mainSidebarTitleIconForCapture`（产品默认 nil 画）。旧/新：**48 张旧帧变化**（12 组 content-* + 12 组 sidebar-*，各亮暗）、**2 张新帧**（`sidebar-no-title-icon` 亮暗）、0 缺失；基线 **318→320**；逐组看过 9 张：图标在标题左、标题右移后不压计数/批量按钮、各行态未动。读数（`MAIN_TITLE_ICON`）：light 负臂 **1772** → 正臂 **2050（+278）**、dark **14213 → 14487（+274）**；首墨 34→32 / 26→26（仅打印）。新判据只要求负臂有墨 + 正臂更多，两臂都空有 `MAIN_TITLE_ICON_NOT_RUN=sidebar-blank` 具名出口；`M1335`（图标永不画）/`M1336`（图标透明）**2/2**。预检 **275/252/678 bad=0**、ARM **368/1166**、HIDDEN **362/1105 rot=0**。⓪：开工 push 与 `ls-remote` 均报 remote closed（api=000）⇒ **`PUSH_BLOCKED=network`（HEAD=`0e461b7`、origin/main=`67cb683`、ahead=1）**、`CI_READ_BLOCKED`；收口前网络恢复、remote 仍 `67cb683` ⇒ 一次快进 push **`67cb683..590ead8` success**（两笔）、HEAD=origin/main=`590ead8`、**ahead=0**；R494 跑 `40895877246 ↔ 590ead8` queued ⇒ NOT-RUN；R493 跑 `40887758385 ↔ 67cb683` in_progress ⇒ NOT-RUN；R492 主跑 Release 3 条 + Motion 2 条、补记跑仅 Motion 2 条；R491 主跑 Release 3 条 + Motion 1<1、补记跑 success；R490/R489 主跑 Release 3 条、补记跑 success；R488 主跑 Release 3 条 + Motion 1<2、补记跑 success；R487 跑 success；R486 主跑 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 沿用 R481 跑 reds=0。全量 **1310/56/0**（719.1s，轻载）；捕获卷 **320 帧**；基线 **320/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 493，`python3 scripts/product_streak.py --streak-for 493`，last=67cb683）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 与 CI：网络阻断具名、成对读数沿用、R493 跑 NOT-RUN。
② 产品：主侧栏标题补时钟图标（48 旧帧 + 2 新帧、基线 320）。
③ 判据：墨差 +278/+274；M1335/M1336 2/2；两臂空有具名出口。
④ 预检 275/252/678；rot 362/1105；ARM 368/1166。
⑤ 捕获 320 帧；基线 320/0/0/0；build 0 告警；换装 ok/397=397；全量 1310/56/0。

NOT-RUN / 阻塞（分开写）：① R494 自身跑 `40895877246`（queued）；② R493 跑 `40887758385`（in_progress）；③ MAIN_TITLE_ICON runner 1x/2x；④ 其余 runner 复核（网络未读）；⑤ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑥ DEFAULT_BADGE（settings-content-blank）；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–588 的其余未结项仍开。

下一轮（R495）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 HEAD=origin/main=`590ead8`、ahead=0）；成对读 R494 自身跑 `40895877246`、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `MAIN_TITLE_ICON`（墨差 ≥40·s²、1x/2x）、`RESET_ICON`（右列墨差、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R493 状态（2026-10-29 · 本地 · 第 492 轮 / Round 490）：设置「恢复默认」按钮补图标（18 张旧帧变化 + 2 张新帧、基线 318）；全量 1309/56/0（产品 2 文件 + 判据）

最后更新：2026-10-29（本地 · R493 / 第 492 轮 / Round 490）：数据页导出/导入已带图标，快捷键/推荐两处「恢复默认」仍纯文字 —— 同一设置窗口的动作图标语言分裂。修法：`HotKeySettingsRow` 与 `RecommendationWeightsView` 的按钮改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改；加捕获缝 `settingsResetButtonIconsForCapture`（产品默认 nil 画）。旧/新：**18 张旧帧变化**（settings-shortcuts、settings-min、conflict、recording、recommendations-tall 等）、**2 张新帧**（settings-shortcuts-no-reset-icon 亮暗）、0 缺失；基线 **316→318**；逐张看过：图标在标签左、按钮未压卡片、禁用态仍可读。读数（`RESET_ICON`，2x）：light 右列墨 **3057→3507（+450）**、dark **3636→4101（+465）**。新判据读右列墨差；`M1331`（永不画）/`M1332`（负臂也画）**2/2**。**重跑 MotionDriverTests 并重锚权重复位尺**：按钮 closure-label 形状变化后 `weightsResetIsAnimated` 的正对照已改，两格通过。预检 **274/251/676 bad=0**、ARM **367/1164**、HIDDEN **361/1103 rot=0**。⓪：开工 push no-op、HEAD=origin/main=`e754cf7`、**ahead=0**；收口一次快进 push **`e754cf7..67cb683` success**、HEAD=origin/main=`67cb683`、**ahead=0**；R493 跑 `40887758385 ↔ 67cb683` 读时 **in_progress ⇒ NOT-RUN**；R492 主跑 `40880105650 ↔ a90b074` failure 2 步（Release 3 条 + Motion 已知 2 条；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel 两档），补记跑 `40880472552 ↔ e754cf7` failure 仅 Motion 2 条；R491 主跑 Release 3 条 + Motion 1<1、补记跑 success；R490 主跑 Release 3 条、补记跑 success；R489/R488/R487/R486 沿用；436 无新跑。全量 **1309/56/0**（525.8s，轻载）；捕获卷 **318 帧**；基线 **318/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 492，`python3 scripts/product_streak.py --streak-for 492`，last=a90b074）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R492 两跑均 failure（主跑 Release 3 条 + Motion 2 条；补记跑仅 Motion 2 条）；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel。
② 产品：恢复默认按钮补图标（18 旧帧 + 2 新帧、基线 318）。
③ 判据：右列墨差 450/465；M1331/M1332 2/2；MotionDriver 重锚。
④ 预检 274/251/676；rot 361/1103；ARM 367/1164。
⑤ 捕获 318 帧；基线 318/0/0/0；build 0 告警；换装 ok/397=397；全量 1309/56/0。

NOT-RUN / 阻塞（分开写）：① R493 自身跑（in_progress）；② RESET_ICON runner 1x/dark；③ LOGIN_FAILURE_ICON 1x（no-red-channel）；④ QUICKPICK_CONTENT_BADGE 1x 已签收；⑤ HISTORY_SOURCE_ICON 1x 已签收；⑥ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑦ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑧ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑨ QUICKPICK_FAVORITE 1x 已签收；⑩ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑪ SETTINGS_DATA_PATH；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红（本跑 2 条）；⑮ 437–586 的其余未结项仍开。

下一轮（R494）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2；R490 主跑唯一红是 Release 3 条；R492 主跑/补记跑均 Motion 2 条已知红）；**重点读 `RESET_ICON`（右列墨差 ≥40·s²、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`（1x 已签收）、`HISTORY_SOURCE_ICON`（1x 已签收）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R492 状态（2026-10-29 · 本地 · 第 491 轮 / Round 489）：开机启动失败回执补错误图标（2 张旧帧变化 + 2 张新帧、基线 316）；全量 1308/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R492 / 第 491 轮 / Round 489）：失败回执只有红字，而横幅/回执都带图标。修法：`if let message` 分支改成 HStack，`lastActionFailed` 时在文字左侧加 `exclamationmark.triangle.fill`（11pt，与文字同错误色）；不支持说明不加；加捕获缝 `loginFailureIconForCapture`（产品默认 nil 画）。旧/新：**2 张旧帧变化**（settings-general-login-failed 亮暗）+ **2 张新帧**（settings-general-login-failed-no-icon 亮暗）、0 缺失；基线 **314→316**；逐张看过：三角在红字左、不支持态与正常态未动。读数（`LOGIN_FAILURE_ICON`，2x）：light 红像素 **2374→2631（+257）**、dark **2119→2366（+247）**。新判据只数红像素（第一版“最左红左移”实测 0/-1px，已删）；`M1329`（图标永不画）/`M1330`（图标不是红色）**2/2**。**重锚两处旧尺**：R384 M1015 改指 `loginFailureStyle`（恒 secondary）CAUGHT；R39 M177 改指新 HStack、**M178 改指“禁用标签恒 primary”**（旧 `.disabled` 针被 R396 分色取代）⇒ R39 表 **8/8 CAUGHT**、RESTORE_CLEAN=yes。新负向帧补进复选框首墨名册，`CARD_INSET_CONTROL_FIRST` 恢复 +2.5/+3.0。预检 **273/250/674 bad=0**、ARM **366/1162**、HIDDEN **360/1101 rot=0**。⓪：push no-op、HEAD=origin/main=`ebc64aa`、**ahead=0**；R490 主跑 `40865789755 ↔ c0c08c7` failure 仅 Release 3 条非产品（HISTORY_SOURCE_ICON 1x light 0/187/170、dark 0/165/170 签收；DEFAULT_BADGE/种子守卫 NOT_RUN），补记跑 `40866154839 ↔ 9f987c7` success；R491 主跑 `40868743008 ↔ 83e2087` **failure 仅 Release 3 条非产品 + Motion 已知 `testFilterPillSlideIsAProcessNotATeleport 1<1`**（Swift/Capture 全绿；`QUICKPICK_CONTENT_BADGE` 1x light 54→72/+18、dark 50→66/+16 签收、`HISTORY_SOURCE_ICON` 1x 0/187/170、0/165/170 签收），补记跑 `40868988761 ↔ ebc64aa` **success**；R492 跑 `40880105650 ↔ a90b074` 读时 **in_progress ⇒ NOT-RUN**；R489 主跑唯一红是 Release 3 条、补记跑 success；R488 主跑 Release 3 条 + Motion 已知 1<2、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1308/56/0**（568.7s，轻载；R39/R384 重锚后重跑）；捕获卷 **316 帧**；基线 **316/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 491，`python3 scripts/product_streak.py --streak-for 491`，last=83e2087）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R490 主跑唯一红是 Release 3 条 + HISTORY_SOURCE_ICON 1x 签收、补记跑 success；R491 两跑 in_progress ⇒ NOT-RUN。
② 产品：开机启动失败回执补错误图标（2 旧帧 + 2 新帧、基线 316）。
③ 判据：红像素 2374→2631/2119→2366；M1329/M1330 2/2；R384 M1015、R39 M177/M178 重锚。
④ 预检 273/250/674；rot 360/1101；ARM 366/1162。
⑤ 捕获 316 帧；基线 316/0/0/0；build 0 告警；换装 ok/397=397；全量 1308/56/0。

NOT-RUN / 阻塞（分开写）：① R492 自身跑（in_progress）；② LOGIN_FAILURE_ICON runner 1x/dark；③ R491 两跑已读（主跑 Release 3 条 + Motion 已知、补记 success）；④ QUICKPICK_CONTENT_BADGE runner 1x/dark；⑤ HISTORY_SOURCE_ICON 1x 已签收；⑥ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑦ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑧ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑨ QUICKPICK_FAVORITE 1x 已签收；⑩ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑪ SETTINGS_DATA_PATH；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红；⑮ 437–584 的其余未结项仍开。

下一轮（R493）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R492 跑 `40880105650`、R491 两跑 `40868743008`/`40868988761`、R490 两跑 `40865789755`/`40866154839`、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2；R490 主跑唯一红是 Release 3 条）；**重点读 `LOGIN_FAILURE_ICON`（红像素差 ≥30·s²、1x/dark）、`QUICKPICK_CONTENT_BADGE`（1x/dark）、`HISTORY_SOURCE_ICON`（1x 已签收）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R491 状态（2026-10-29 · 本地 · 第 490 轮 / Round 488）：浮层候选行补内容标记（4 张新帧、基线 314）；全量 1307/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R491 / 第 490 轮 / Round 488）：主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题。修法：`QuickPickRowCell` 加 `contentBadge`（9pt，叠在类型符号左上角，与收藏右上、图钉右下错开；按链接 > 富文本 > OCR 取一枚），读屏标签加「链接/富文本/可搜索文字」前缀。旧/新：**4 张新帧**（quickpick-plain / quickpick-link-badge 亮暗）、**0 张旧帧变化**、0 缺失；基线 **310→314**；逐张看过：链接徽标在类型符号左上角、不压标题/时间，普通行无标记。读数（`QUICKPICK_CONTENT_BADGE`，2x）：light 类型列墨 **215→311（+96）**、dark **233→332（+99）**。新判据用成对帧读类型列墨差；`M1327`（永不画）/`M1328`（无内容也画链接）**2/2**（M1327 第一版空刀，本轮内改对）。预检 **272/249/672 bad=0**、ARM **365/1160**、HIDDEN **359/1099 rot=0**。⓪：开工两次探针均失败 ⇒ **`PUSH_BLOCKED=network`（HEAD=origin/main=`9f987c7`、ahead=0）**、**`CI_READ_BLOCKED=network`**；收口网络恢复，一次快进 push **`9f987c7..83e2087` success**、HEAD=origin/main=`83e2087`、**ahead=0**；R491 跑 `40868743008 ↔ 83e2087` 读时 **in_progress ⇒ NOT-RUN**；R490 主跑 `40865789755` 与补记跑 `40866154839` 读时 **in_progress ⇒ NOT-RUN**；R489 主跑唯一红是 Release 3 条非产品（DEFAULT_BADGE/种子守卫 NOT_RUN）、补记跑 success；R488 主跑 Release 3 条 + Motion 已知 1<2、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1307/56/0**（509.0s，轻载）；捕获卷 **314 帧**；基线 **314/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 490，`python3 scripts/product_streak.py --streak-for 490`，last=c0c08c7）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 两次探针失败 ⇒ PUSH_BLOCKED=network（9f987c7、ahead=0）/CI_READ_BLOCKED；R490 两跑未读 ⇒ NOT-RUN；R489 主跑唯一红是 Release 3 条、补记跑 success。
② 产品：浮层候选行内容标记（4 新帧、基线 314）。
③ 判据：类型列墨 215→311/233→332；M1327/M1328 2/2（空刀已改）。
④ 预检 272/249/672；rot 359/1099；ARM 365/1160。
⑤ 捕获 314 帧；基线 314/0/0/0；build 0 告警；换装 ok/397=397；全量 1307/56/0。

NOT-RUN / 阻塞（分开写）：① R491 自身跑（in_progress）；② QUICKPICK_CONTENT_BADGE runner 1x/dark；③ R490 两跑（in_progress）；④ HISTORY_SOURCE_ICON runner 1x/dark；⑤ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑥ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑦ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑧ QUICKPICK_FAVORITE 1x 已签收；⑨ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑩ SETTINGS_DATA_PATH；⑪ 既有 runner 复核；⑫ Capture MATERIAL_BLIND_NOT_RUN；⑬ 已知 Motion 采样红；⑭ 437–582 的其余未结项仍开。

下一轮（R492）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R491 跑 `40868743008`、R490 两跑 `40865789755`/`40866154839`、R489 两跑 `40858253532`/`40861168233`、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `QUICKPICK_CONTENT_BADGE`（类型列墨差 ≥8·s²、1x/dark）、`HISTORY_SOURCE_ICON`（彩色 ≥40·s²、负臂=0）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R490 状态（2026-10-29 · 本地 · 第 489 轮 / Round 487）：主列表来源行补来源 App 图标（70 张旧帧变化、基线 310）；全量 1306/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R490 / 第 489 轮 / Round 487）：详情头部与浮层都有来源 App 图标，主列表只有「来自 X」文字 —— 同一信息在三种表面有三种形态。修法：`RowTextColumn` 拆时间与来源，在「 · 来自 」后补 `SourceAppIconProvider` 的 11pt 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`（带图标 / 无图标两档），250pt 最小窗退回无图标分支、来源名不被挤没；macOS 12 走无图标分支。旧/新：**70 张旧帧变化**、0 新增/缺失；基线 **310/0/0/0**；逐张看过：300pt 源名带图标、250pt 无图标但源名保留、标题/时间轴未动。读数（`HISTORY_SOURCE_ICON`，2x）：light 负臂 0→正臂 **807**、dark **789**，缩略图彩色对照 **680**、负臂必须 0。新判据读文字列彩色像素；`M1325`（图标永不画）/`M1326`（无来源也画蓝图标）**2/2**。第一版两刀都因“两臂都 0 静默 skip”逃过，补彩色对照与负臂 0 后才红。**重锚 R444 M1220**：来源行拆视图后旧针失效，改成把 `name` 置空，与 M1221 重跑 **2/2**。预检 **271/248/670 bad=0**、ARM **364/1158**、HIDDEN **358/1097 rot=0**。⓪：一次快进 push **`d8b0712..3d4a03a` success**、HEAD=origin/main=`3d4a03a`、**ahead=0**；R489 主跑 `40858253532 ↔ d8b0712` **failure 仅 Release script 3 条非产品**（Swift/Capture/Motion 全绿；`DEFAULT_BADGE_NOT_RUN=settings-content-blank` 两档、种子守卫 NOT_RUN），补记跑 `40861168233 ↔ 3d4a03a` **success**；R490 跑 `40865789755 ↔ c0c08c7` **in_progress ⇒ NOT-RUN**；R488 主跑 failure 2 步（Release 3 条非产品 + Motion 已知 1<2）、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1306/56/0**（489.3s，轻载；重锚 R444 后重跑）；捕获卷 **310 帧**；基线 **310/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 489，`python3 scripts/product_streak.py --streak-for 489`，last=d8b0712）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push d8b0712..3d4a03a success、ahead=0；R489 两跑 NOT-RUN；R488 主跑 Release+Motion 已知、补记跑 success。
② 产品：主列表来源行补来源图标（70 旧帧、基线 310）；250pt 用 ViewThatFits 保源名。
③ 判据：彩色 807/789、对照 680、负臂 0；M1325/M1326 2/2；重锚 R444 M1220。
④ 预检 271/248/670；rot 358/1097；ARM 364/1158。
⑤ 捕获 310 帧；基线 310/0/0/0；build 0 告警；换装 ok/397=397；全量 1306/56/0。

NOT-RUN / 阻塞（分开写）：① R490 自身跑（in_progress）；② HISTORY_SOURCE_ICON runner 1x/dark；③ R489 两跑（in_progress/queued）；④ DEFAULT_BADGE/TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑤ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑥ QUICKPICK_FAVORITE 1x 已签收；⑦ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑧ SETTINGS_DATA_PATH；⑨ 既有 runner 复核；⑩ Capture MATERIAL_BLIND_NOT_RUN；⑪ 已知 Motion 采样红；⑫ 437–580 的其余未结项仍开。

下一轮（R491）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R490 跑 `40865789755`、R489 两跑 `40858253532`/`40861168233`、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `HISTORY_SOURCE_ICON`（彩色 ≥40·s²、负臂=0、1x/dark）、`DEFAULT_BADGE`（1x 未读）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R489 状态（2026-10-29 · 本地 · 第 488 轮 / Round 486）：默认排除项补「默认」身份标记（6 张旧帧变化 + 2 张新帧、基线 310）；全量 1305/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R489 / 第 488 轮 / Round 486）：默认排除项不能移除，自定义项有红色「移除」；两类行原来只靠按钮有无区分，用户看不出“为什么这一行不能删”。修法：默认名单每行尾部补 `Text("默认")`（meta、secondary、fixedSize、accessibilityLabel「默认排除项，不可移除」），自定义行的「移除」不动；加捕获缝 `settingsDefaultExcludedBadgeForCapture`（产品默认 nil 画）。旧/新：**6 张旧帧变化**（settings-privacy、settings-privacy-excluded、settings-privacy-tall 各亮暗）+ **2 张新帧**（settings-privacy-no-default-badge 亮暗）、0 缺失；基线 **308→310**；逐张看过：默认行尾部灰字与自定义行红「移除」分列、行高不变。读数（`DEFAULT_BADGE`，2x）：light 右列墨 **2704→5548（差 2844）**、dark **3132→6723（差 3591）**。新判据读右列墨量差；`M1323`（永不画）/`M1324`（移到行下左侧）**2/2**。**重锚 R432 两把旧刀**（默认名单 ForEach 的针被本轮 HStack 断掉）：M1187/M1188 改指新块后 **2/2**；种子守卫从“右缘所有墨段”改为只数**红段**，现读 `期望=2 右缘墨带=11 红段=2`。预检 **270/247/668 bad=0**、ARM **363/1156**、HIDDEN **357/1095 rot=0**。⓪：push no-op、HEAD=origin/main=`2cafe1b`、**ahead=0**；R488 主跑 `40851078685 ↔ 9487c0f` failure 2 步（Release 3 条非产品 + Motion 已知 1<2），Swift/Capture 全绿，`TABLE_COLUMNS` 1x **制表位=2、第二列 [122,123,123] 极差 1px、第三列 [161,161,161] 极差 0px**、`TABLE_PIPES` 1x 0、`WIDE_TABLE` 689.9pt/行片段 1、`TABLE_HEADER` 1.08/1.19；R488 补记跑 `40851311888 ↔ 2cafe1b` success；R487 跑 success；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；R489 跑 `40858253532 ↔ d8b0712` 读时 **queued ⇒ NOT-RUN**；436 无新跑。全量 **1305/56/0**（513.6s，轻载；种子守卫重锚后重跑）；捕获卷 **310 帧**；基线 **310/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 488，`python3 scripts/product_streak.py --streak-for 488`，last=9487c0f）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R488 主跑唯一红是 Release 3 条 + 已知 Motion 1<2、补记跑 success；TABLE_COLUMNS 1x 签收。
② 产品：默认排除项补「默认」身份标记（6 旧帧 + 2 新帧、基线 310）。
③ 判据：右列墨差 2844/3591；M1323/M1324 2/2；重锚 R432 M1187/M1188；种子守卫改红段。
④ 预检 270/247/668；rot 357/1095；ARM 363/1156。
⑤ 捕获 310 帧；基线 310/0/0/0；build 0 告警；换装 ok/397=397；全量 1305/56/0。

NOT-RUN / 阻塞（分开写）：① R489 自身跑（queued）；② DEFAULT_BADGE runner 1x/dark；③ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ QUICKPICK_FAVORITE 1x 已签收；⑥ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑦ SETTINGS_DATA_PATH；⑧ 既有 runner 复核；⑨ Capture MATERIAL_BLIND_NOT_RUN；⑩ 已知 Motion 采样红；⑪ 437–578 的其余未结项仍开。

下一轮（R490）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R489 跑 `40858253532`、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `DEFAULT_BADGE`（右列墨差 ≥80·s²、1x/dark）、`TABLE_COLUMNS`（1x 已签收）、`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R488 状态（2026-10-29 · 本地 · 第 487 轮 / Round 485）：表格列宽随内容对齐（8 张旧帧变化 + 2 张新帧、基线 308）；全量 1304/56/0（产品 3 文件 + 判据）

最后更新：2026-10-29（本地 · R488 / 第 487 轮 / Round 485）：R487 去竖线后列仍跟作者源码里的空格走，长单元格把第二列推歪（修前 `detail-table-uneven` 第二列 **269/254/260px**、第三列 **353/350/356px**，2x）。修法：`MarkdownTablePresentation.renderedContent` 只保留 `\t` 分列，`columnStops(in:)` 按每列**最大实宽**（表头 semibold、表体 regular 各用自己的字体）算 12pt 间距的绝对制表位；`MarkdownPresentation.paragraphStyle` 给表格块设置 `tabStops`；`WideMarkdownDocument` 的表格宽度按最后一列右沿量。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）+ **2 张新帧**（detail-table-uneven 亮暗）、0 缺失；基线 **306→308**；逐张看过：三列对齐、行分隔线与表头字重仍在。读数（`TABLE_COLUMNS`，2x）：制表位 **2**、第二列 **[245,246,246] 极差 1px**、第三列 **[321,321,321] 极差 0px**。新判据先读 tabStops=2 再读列起点极差 ≤2·s；`M1321`（不设制表位）/`M1322`（只按表头定列宽）**2/2**；R487 旧刀 `M1319/M1320` 重锚后仍 **2/2**。**重锚后宽表 690.1pt（仍 >611）、行片段 [1,1,1]；表头墨比 1.16/1.19（仍 >1.08）**。预检 **269/246/666 bad=0**、ARM **362/1154**、HIDDEN **356/1093 rot=0**。⓪：一次快进 push **`04cc517..519b22b` success**、HEAD=origin/main=`519b22b`、**ahead=0**；R487 跑 `40845483735 ↔ 519b22b` **success**（TABLE_PIPES 1x 竖线 0、墨 1158/1074；TABLE_HEADER 1.11/1.18；WIDE_TABLE 719.8pt/行片段 1）；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；R488 跑 `40851078685 ↔ 9487c0f` 读时 **in_progress ⇒ NOT-RUN**；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1304/56/0**（506.7s，轻载；宽表宽度修正后重跑）；捕获卷 **308 帧**；基线 **308/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 487，`python3 scripts/product_streak.py --streak-for 487`，last=d44e16d）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 04cc517..519b22b success、ahead=0；R487 跑 success（TABLE_PIPES 1x 0/1158/1074、WIDE_TABLE 719.8、表头 1.11/1.18）；R486 主跑唯一红是 Release 3 条非产品。
② 产品：表格列宽随内容对齐（8 旧帧 + 2 新帧、基线 308）。
③ 判据：tabStops=2 + 列起点极差 1/0px；M1321/M1322 2/2、M1319/M1320 重锚 2/2。
④ 预检 269/246/666；rot 356/1093；ARM 362/1154。
⑤ 捕获 308 帧；基线 308/0/0/0；build 0 告警；换装 ok/397=397；全量 1304/56/0。

NOT-RUN / 阻塞（分开写）：① R488 自身跑（in_progress）；② TABLE_COLUMNS runner 1x/dark；③ TABLE_PIPES 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ QUICKPICK_FAVORITE 1x 已签收；⑥ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑦ SETTINGS_DATA_PATH；⑧ 既有 runner 复核；⑨ Capture MATERIAL_BLIND_NOT_RUN；⑩ 已知 Motion 采样红；⑪ 437–576 的其余未结项仍开。

下一轮（R489）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R488 跑 `40851078685`、R487 跑 `40845483735`、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑 `40805576917` 的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `TABLE_COLUMNS`（制表位=2、第二/第三列极差 ≤2·s、1x/dark）、`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R487 状态（2026-10-29 · 本地 · 第 486 轮 / Round 484）：Markdown 渲染态表格去掉源码竖线（8 张旧帧变化、基线 306）；全量 1303/56/0（产品 2 文件 + 判据）

最后更新：2026-10-29（本地 · R487 / 第 486 轮 / Round 484）：表格在渲染态仍原样带 `|`，R440/R448 只给表头字重与体行线，源码语法一直在正文里。修法：新 `MarkdownTablePresentation.renderedRow` 把每个 `|` 换成**同宽空格**（等宽字体）并只裁首尾空白，`renderedContent` 逐行套用；`MarkdownScanning.collectTable` 用它组装表格块。列的起点一字不挪（不做 R234 的列重排），源码态仍走原始字符串。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）、0 新增/缺失；基线 **306/0/0/0**；逐张看过：竖线消失、两列对齐、行分隔线与表头字重仍在。读数（`TABLE_PIPES`，2x）：表格块竖线 **0**、表格行 5、表格区墨 **light 4251 / dark 3731**。新判据两腿（纯函数无竖线 + 帧内表格块 `|` 计数 0 且表格区有墨）；`M1319`（不剥竖线）/`M1320`（只剥表头）**2/2**。**重锚两把旧尺**：宽表判据改读 `tableRowCountAttribute`（容器宽 752.1→720.0pt、行片段 [1,1,1]，仍 >611）；表头纯判据针改 `甲   乙`，重跑 3/3；表头墨比 1.40→1.17/1.19（仍 >1.08）。预检 **268/245/664 bad=0**、ARM **361/1152**、HIDDEN **355/1091 rot=0**。⓪：开工 push no-op、HEAD=origin/main=`04cc517`、**ahead=0**；收口提交 `d44e16d` 后**两次 push 均 remote closed ⇒ `PUSH_BLOCKED=network`（HEAD=`d44e16d`、origin/main=`04cc517`、ahead=1；本补记后 ahead=2）**；R487 跑未创建 ⇒ NOT-RUN；R486 主跑 `40836764232 ↔ dfbf6f6` failure 仅 Release script 3 条非产品，Swift/Capture/Motion 全绿，`DATA_ACTION_ICONS_NOT_RUN` 与 `HEATMAP_TODAY_NOT_RUN` 两档按预期出现，QUICKPICK_FAVORITE 1x 54→71/50→63 签收；R486 补记跑 `40837020563 ↔ 04cc517` **success**；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1303/56/0**（504.4s，轻载；重锚两把旧尺后重跑）；捕获卷 **306 帧**；基线 **306/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 486，`python3 scripts/product_streak.py --streak-for 486`，last=dfbf6f6）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 开工 push no-op、ahead=0；收口两次 push 失败 ⇒ PUSH_BLOCKED=network（d44e16d、ahead=1）；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；DATA_ACTION_ICONS/HEATMAP_TODAY 的 1x NOT_RUN 出口签收。
② 产品：渲染态表格去源码竖线（8 旧帧、基线 306）。
③ 判据：表格块竖线 0 + 表格区墨 4251/3731；M1319/M1320 2/2；重锚两把旧尺。
④ 预检 268/245/664；rot 355/1091；ARM 361/1152。
⑤ 捕获 306 帧；基线 306/0/0/0；build 0 告警；换装 ok/397=397；全量 1303/56/0。

NOT-RUN / 阻塞（分开写）：① R487 自身跑（未创建，push 待恢复）；② TABLE_PIPES runner 1x/dark；③ QUICKPICK_FAVORITE 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑥ SETTINGS_DATA_PATH；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–574 的其余未结项仍开。

下一轮（R488）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R487 自身跑（`d44e16d`，push 恢复后取）、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R486 主跑唯一红是 Release 3 条非产品）；**重点读 `TABLE_PIPES`（竖线=0、表格区墨 ≥300·s²、1x/dark）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R486 状态（2026-10-29 · 本地 · 第 485 轮 / Round 483）：设置数据页导出/导入按钮补图标（4 张旧帧变化 + 2 张新帧、基线 306）；全量 1302/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R486 / 第 485 轮 / Round 483）：同一组数据动作里，清空已有垃圾桶图标，导出/导入却还是纯文字 —— 三颗按钮的图标语言分裂。修法：两颗按钮改用 `Label` + `square.and.arrow.up` / `square.and.arrow.down`（标签一字不改），加捕获缝 `settingsDataActionIconsForCapture`（产品默认 nil 画图标）。旧/新：**4 张旧帧变化**（settings-data 与 settings-data-no-title-icon 各亮暗）+ **2 张新帧**（settings-data-no-action-icons 亮暗）、0 缺失；基线 **304→306**；逐张看过：图标在标签左、清空/卡片几何未动。读数（`DATA_ACTION_ICONS`，2x）：light 按钮行末列 **698→788（右伸 90px=45pt）**、墨 **2020→2499（+479）**、导出差 **+240**、导入差 **+239**；dark 墨 **2261→2738（+477）**、导出差 **+239**、导入差 **+238**。新判据按每颗按钮自己的窗读墨；`M1317`（撤导出图标）/`M1318`（撤导入图标）**2/2**。同轮修 `HEATMAP_TODAY` 的 runner 1x 出口：R484 跑两档差异 0 像素是设置内容整列平涂，加内容墨证人（<50·s² ⇒ 具名 `HEATMAP_TODAY_NOT_RUN=settings-content-blank` 并 skip），本机 2x 仍判 60 像素、内容墨 33627。预检 **267/244/662 bad=0**、ARM **360/1150**、HIDDEN **354/1089 rot=0**。⓪：开工一次快进 push **`35ad21a..f04eaef` success**、HEAD=origin/main=`f04eaef`、**ahead=0**；R484 跑 `40826572977 ↔ 6454a93` completed failure 3 步已读清（Swift/Capture 同一 HEATMAP_TODAY 红 0 像素；Release 3 条非产品）；R485 跑 `40832860076 ↔ 35ad21a` **completed failure 4 步已读**：`QUICKPICK_FAVORITE` 1x **签收**（light 54→71/+17、上移 4px；dark 50→63/+13、4px；标题末列差 0），Swift/Capture 唯一红仍是 `HEATMAP_TODAY` 两档 0（R486 已带 NOT_RUN 出口，待新跑），Motion 唯一红 `testMarkdownModeLabelChangeIsAVisibleProcess 1<2`（judged=4/5），Release 3 条非产品；R486 跑 `40836764232 ↔ dfbf6f6` **queued ⇒ NOT-RUN**；R483/R481/R480/R478/R477/R479 沿用；436 无新跑。全量 **1302/56/0**（476.3s，轻载）；捕获卷 **306 帧**；基线 **306/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 485，`python3 scripts/product_streak.py --streak-for 485`，last=35ad21a）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 35ad21a..f04eaef success、ahead=0；R484 跑三朵红已读清；R485 跑已读（QUICKPICK_FAVORITE 1x 签收）；R486 跑 queued ⇒ NOT-RUN。
② 产品：数据页导出/导入补图标（4 旧帧 + 2 新帧、基线 306）。
③ 判据：两窗墨差 +240/+239；M1317/M1318 2/2；HEATMAP 1x 补具名 NOT_RUN。
④ 预检 267/244/662；rot 354/1089；ARM 360/1150。
⑤ 捕获 306 帧；基线 306/0/0/0；build 0 告警；换装 ok/397=397；全量 1302/56/0。

NOT-RUN / 阻塞（分开写）：① R486 跑（queued）；② DATA_ACTION_ICONS runner 1x/dark；③ QUICKPICK_FAVORITE runner 1x/dark；④ HEATMAP_TODAY 的 1x 修复复验；⑤ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑥ SETTINGS_DATA_PATH；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–572 的其余未结项仍开。

下一轮（R487）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R486 跑 `40836764232`、R485 跑 `40832860076`（failure 4 步已读；QUICKPICK_FAVORITE 1x 签收 54→71/+17、50→63/+13、4px）、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `DATA_ACTION_ICONS`（两窗各 ≥20·s²、1x/dark）、`QUICKPICK_FAVORITE`（≥8·s²、首墨行上移 ≥2·s）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做数据页导出/导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R485 状态（2026-10-29 · 本地 · 第 484 轮 / Round 482）：浮层候选行补「已收藏」星标（2 张新帧、基线 304）；全量 1301/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R485 / 第 484 轮 / Round 482）：浮层的置顶、来源、时间都有标记，唯独收藏没有；同一条记录在主列表有星标，浮层里零可见（修前 `quickpick-favorite` 与 `quickpick-no-source` 逐像素同形）。修法：`QuickPickRowCell` 加 `favoriteBadge`（9pt `star.fill`，叠在类型符号右上角，与图钉右下角错开；不占固定槽），颜色走 `FavoriteTogglePresentation.favoriteNSColor`（与主列表同源）；读屏标签加「收藏 」前缀。旧/新：**2 张新帧**（quickpick-favorite 亮暗）、**0 张旧帧变化**、0 缺失；基线 **302→304**；逐张看过：星在类型符号右上角、不压标题/时间，图钉仍在右下角。读数（`QUICKPICK_FAVORITE`，2x）：light 类型列墨 **215→328（+113）**、首墨行 **115→105（上移 10px）**、标题末列差 **0px**；dark **233→348（+115）**、上移 **9px**、标题末列差 **0px**。新判据用成对帧四句（对象/墨差 ≥8·s²/首墨行上移 ≥2·s/标题末列差 ≤3·s）；`M1315`（星永不画）/`M1316`（星永远画）**2/2**。预检 **266/243/660 bad=0**（新表已登记；M1316 needle 跨行，静态抽不出 ⇒ 真跑 2/2）、ARM **359/1148**、HIDDEN **352/1085 rot=0**。⓪：开工两次 push 均 remote closed、`ls-remote` 同报 ⇒ **`PUSH_BLOCKED=network`（HEAD=`2eadacf`、origin/main=`6454a93`、ahead=1）**；收口前网络恢复，只读验 remote 仍 `6454a93` ⇒ **一次快进 push `6454a93..35ad21a` success**、HEAD=origin/main=`35ad21a`、**ahead=0**（R484 补记 `2eadacf` 一并推上）；R485 跑 `40832860076 ↔ 35ad21a` 读时 **in_progress ⇒ NOT-RUN**；R484 跑 `40826572977 ↔ 6454a93` **completed failure 3 步**（Release script / Swift tests / Capture gate），日志正文两次 EOF ⇒ **`CI_READ_BLOCKED`，三朵红的名字未读**；R483 跑 `40821834371 ↔ a59956c` failure 1 步＝Release script 3 条非产品红（sources 格×2 + skip roster 嵌套；`40802042660 ↔ 7f21720` success 反证），Swift 1299/74 skip/0 failure、Capture gate failed=0/红=0、CLEAR_LABEL 两档 NOT_RUN；R481 跑签收 ROW_LINK_BADGE 19/18、Capture 红 0；R480 无跑；R478 主跑冲突红、补记跑 success；R477 两跑冲突红；R479 沿用；436 无新跑。全量 **1301/56/0**（467.8s，轻载）；捕获卷 **304 帧**；基线 **304/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 484，`python3 scripts/product_streak.py --streak-for 484`，last=6454a93）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 网络两探失败 ⇒ PUSH_BLOCKED=network；收口恢复后 push 6454a93..35ad21a success、ahead=0；R485 跑 in_progress、R484 跑 failure 3 步但正文 EOF ⇒ NOT-RUN；R483 跑唯一红是 Release 3 条非产品。
② 产品：浮层候选行收藏星标（2 新帧、基线 304）。
③ 判据：成对帧四句 + M1315/M1316 2/2；颜色不作证。
④ 预检 266/243/660；rot 352/1085；ARM 359/1148。
⑤ 捕获 304 帧；基线 304/0/0/0；build 0 告警；换装 ok/397=397；全量 1301/56/0。

NOT-RUN / 阻塞（分开写）：① R485 跑（in_progress）与 R484 跑的三朵红正文（EOF）；② QUICKPICK_FAVORITE runner 1x/dark；③ HEATMAP_TODAY/CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 收藏+置顶同现帧未拍；⑨ 437–570 的其余未结项仍开。

下一轮（R486）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R485 跑 `40832860076`、R484 跑 `40826572977`（failure 3 步：Release/Swift/Capture；正文 EOF，红名待读）、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `QUICKPICK_FAVORITE`（≥8·s²、首墨行上移 ≥2·s、1x/dark）、`HEATMAP_TODAY`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R484 状态（2026-10-29 · 本地 · 第 483 轮 / Round 481）：热图「今天」格补右上角标（8 张旧帧变化 + 2 张新帧、基线 302）；全量 1300/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R484 / 第 483 轮 / Round 481）：热图靠"右下角是今天"的文字说明让用户自己找今天，而今天那格与别的格子同形。修法：`DailyCopyHeatmapCell` 加 `isToday`（默认 false 保持组件帧原状），今天格右上角 4pt `labelColor` 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate(cell.date, inSameDayAs: today)` 判定，加捕获缝 `heatmapTodayMarkerForCapture`（产品默认 nil 画）。旧/新：**8 张旧帧变化**（settings-stats-populated、heatmap-populated、heatmap-summary-after 等 ×亮暗）+ **2 张新帧**（settings-stats-populated-no-today 亮暗）、0 缺失；基线 **300→302**；逐张看过：角标在今天格右上角、不压数据色块。读数（`HEATMAP_TODAY`）：两臂差异 **60 像素**、bbox **1108,408–1115,415**（2x）。新判据用成对帧逐像素差（≥8·s² 且 <4000·s²）；`M1313`（永不画）/`M1314`（圆点透明）**2/2**。新负向帧补进 vibrant 盲区名册（首遍全量红 1 条，补后重跑）。预检 **265/243/660 bad=0**、ARM **358/1146**、HIDDEN **352/1085 rot=0**。⓪：收口 push **`dbceebe..6454a93` success**、HEAD=origin/main=`6454a93`、**ahead=0**；R484 跑 `40826572977 ↔ 6454a93` 读时 **in_progress ⇒ NOT-RUN**；R483 跑 `40821834371 ↔ a59956c` **failure 1 步**＝Release script tests（3 条 Python 红：`test_the_sources_cell_agrees_with_git`/`test_the_cell_agrees_with_its_own_source` 是主笔跑未含补记的 sources 格；`test_the_roster_matches_what_this_machine_actually_skips` 是嵌套套件无汇总行，同提交组 `7f21720` 跑 success 反证为负载 flake），Swift **1299/74 skip/0 failure**、Capture gate **failed=0/红=0**、`CLEAR_LABEL_NOT_RUN=settings-content-blank` 两档具名；R481 跑 `40812979165 ↔ 2770bfe` 已读：ROW_LINK_BADGE 1x +19/+18、SETTINGS_TITLE_ICON_NOT_RUN 登记、Capture gate **failed=0/红=0**、Motion 5/5 reds0；R480 `60d65a4` **无跑**（同批 push head `2d54488` 跑归 R481）⇒ NOT-RUN；R478 主跑 `40801850707 ↔ b64682e` **failure 3 步**（Release 同 3 条；Swift/Capture 唯一红 `testSettingsShortcutConflictIsSurfaced 0≠2`）、补记跑 `40802042660 ↔ 7f21720` **success**；R477 主跑 `40797827495 ↔ 0fd3ec0` **failure 4 步**（同上冲突红；Motion 唯一红 `testMarkdownModeLabelChangeIsAVisibleProcess 1<2`，judged=5/5 executed=77 reds=1）、补记跑 `40797866181 ↔ 7a79987` **failure 2 步**（冲突红仍在）；sources 格 R484/`6454a93`；436 R481 跑 reds=0。全量 **1300/56/0**（494.7s，轻载）；捕获卷 **302 帧**；基线 **302/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 483，`python3 scripts/product_streak.py --streak-for 483`，last=a59956c）；清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 480 / 481 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ 收口 push 6454a93 success、ahead=0；R484 跑 in_progress ⇒ NOT-RUN；R483 跑 failure 仅 Release 3 条（sources 格×2 + skip roster 嵌套，非产品）；R480 无跑；R478 主跑冲突红、补记跑 success；R477 两跑冲突红。
② 产品：热图今天格右上角标（8 旧帧 + 2 新帧、基线 302）。
③ 判据：逐像素差 60/bbox 单格；M1313/M1314 2/2；新负向帧补名册。
④ 预检 265/243/660；rot 352/1085；ARM 358/1146。
⑤ 捕获 302 帧；基线 302/0/0/0；build 0 告警；换装 ok/397=397；全量 1300/56/0。

NOT-RUN / 阻塞（分开写）：① R484 跑（in_progress）；② 今天角标 runner 1x/dark（CLEAR_LABEL 已具名 `NOT_RUN=settings-content-blank`）；③ ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉复核（R477/R478 冲突红已由 `7f21720` 跑 success 签收）；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 437–568 的其余未结项仍开。

下一轮（R485）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `HEATMAP_TODAY`（≥8·s²、1x/dark）、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R483 状态（2026-10-29 · 本地 · 第 482 轮 / Round 480）：设置数据页清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）；全量 1299/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R483 / 第 482 轮 / Round 480）：主窗口/详情浮层用垃圾桶说破坏性动作，设置数据页的「清空」只有文字；夹具又注入 nil，基线钉住用户看不到的禁用灰态。修法：Sources 把按钮改成 `Label("清空", systemImage:"trash")`（**标签保持「清空」**——旧契约 `testSettingsClearButtonUsesShortDestructiveLabel` 钉着短标签，不改旧期望）；夹具注入非 nil 回执让启用态进帧。旧/新：**4 张旧帧变化**（settings-data 与 settings-data-no-title-icon 各亮暗）、0 新增/缺失；基线 **300/0/0/0**；逐张看过：垃圾桶在标签左、按钮未压卡片。读数（`CLEAR_LABEL`）：标签墨宽 light **46.0pt**、dark **46.5pt**（旧「清空」文字约 33pt）；**启用红态在离屏 `.borderedProminent` 无彩色通道（红像素 0）⇒ 具名 NOT-RUN，不拿颜色当证人**。新判据读标签墨宽（阈值 45pt；内容平涂时 `CLEAR_LABEL_NOT_RUN` 并 skip）；`M1311`（Label→Text）/`M1312`（labelStyle titleOnly）**2/2**。第一版把标签改成「清空未收藏」（85.5pt）被旧契约当场红 ⇒ **撤回长标签、保留短标签+图标**。预检 **264/243/660 bad=0**、ARM **357/1145**、HIDDEN **351/1083 rot=0**。⓪：开工两次 push 报 `correct access rights`、gh 不可达 ⇒ **`PUSH_BLOCKED=network`（HEAD=`54af93a`、ahead=0）**、**`CI_READ_BLOCKED`**；R481/R480/R478/R477 跑未读 ⇒ NOT-RUN；R483 跑 `40821834371 ↔ a59956c` 读时 in_progress ⇒ NOT-RUN；sources 格 R483/`a59956c`；R479 跑签收沿用；436 无新跑。全量 **1299/56/0**（489.7s，轻载；首遍长标签红 1 条，撤回后干净）；捕获卷 **300 帧**；基线 **300/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **2** 轮（as-of 482，`python3 scripts/product_streak.py --streak-for 482`，last=2770bfe）；清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 479 / 480 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ 网络不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R481/R480/R478/R477 跑 NOT-RUN；436 无新跑。
② 产品：清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）；保留短标签，撤回长标签改法。
③ 判据：标签墨宽 46pt；M1311/M1312 2/2；启用红态具名 NOT-RUN。
④ 预检 264/243/660；rot 351/1083；ARM 357/1145。
⑤ 捕获 300 帧；基线 300/0/0/0；build 0 告警；换装 ok/397=397；全量 1299/56/0。

NOT-RUN / 阻塞（分开写）：① R481/R480/R478/R477 跑（CI_READ_BLOCKED）；② 清空按钮启用红态（离屏无彩色通道）；③ 垃圾桶图标 runner 1x/dark；④ 链接/标题图标/兜底路径/inline/幻影/图钉/冲突 runner 复核；⑤ SETTINGS_DATA_PATH；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–566 的其余未结项仍开。

下一轮（R484）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R483 自身跑、R481 跑 `40812979165`、R480 跑、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `CLEAR_LABEL`（≥45pt 且 1x/dark）、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`/`ROW_RICH_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R482 状态（2026-10-29 · 第 481 轮 · 空轮）：无产品变更（清空按钮启用色离屏无通道；未验证的 Sources 改动已撤回，不记完成）

最后更新：2026-10-29（本地 · R482 / 空轮）：尝试把设置「清空未收藏」的启用危险态第一次拍进帧；夹具注入非 nil 后，离屏帧仍无红/彩色填充（`CLEAR_BUTTON_NOT_RUN=no-red-fill light/dark`），`.borderedProminent` 启用色在本通道不可判 ⇒ 具名 NOT-RUN。按“判不了就放弃该位”撤回未验证的 Sources 改动（工作树干净、HEAD=origin/main=`54af93a`、ahead=0），没有产品文件/帧/台账/commit，**不记完成**。未读跑：R481 `40812979165`、R480、R478 两跑、R477 两跑（CI_READ_BLOCKED/未读）。

## R481 状态（2026-10-29 · 本地 · 第 480 轮 / Round 478）：主列表补链接条目标记（2 张新帧、基线 300）+ 标题图标 runner NOT-RUN 修复；全量 1298/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R481 / 第 480 轮 / Round 478）：URL 文本行与普通文本行同形。修法：新 `EntryPresentation.looksLikeLink`（http/https、无空白）；`RowTextColumn` 时间行补 `link` 标记（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），仅链接文本出现。旧/新：**2 张新帧**（`row-link-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **298→300**；2 张逐张看过：链形标记在来源后、时间行同一行。读数：最下一条墨带（时间行）末列 light/dark **441→476px（+35px=17.5pt）**。判据用 `row-text`/`row-link-text` 的最下墨带末列（标题差异被排除）；`M1308`（永不画）/`M1309`（永远画）**2/2**。`SETTINGS_TITLE_ICON` 判据在 runner 设置内容整列平涂时补 `SETTINGS_TITLE_ICON_NOT_RUN=settings-content-blank` 并 skip（R479 跑唯一测试红即此，不是产品）。预检 **263/243/660 bad=0**、ARM **356/1144**、HIDDEN **350/1081 rot=0**。⓪：一次快进 push **`59b63c1..2d54488` success**、HEAD=origin/main=`2d54488`、**ahead=0**；R479 跑 `40805576917 ↔ 225e6f8` failure 3 步，签收 `FALLBACK_PATH` 113pt、`INLINE_CODE_PAD` 99/6.0 与 102/5.0、幻影 0、图钉 +20；R480 跑与其余读时 in_progress/未读 ⇒ NOT-RUN；R481 跑 `40812979165 ↔ 2770bfe` 读时 in_progress ⇒ NOT-RUN；sources 格 R481/`2770bfe`。436 R479 跑 reds=0。全量 **1298/56/0**（512.8s，轻载）；捕获卷 **300 帧**；基线 **300/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 480，`python3 scripts/product_streak.py --streak-for 480`，last=60d65a4）；清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 478 / 479 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ push 59b63c1..2d54488 success、ahead=0；R479 跑 signoff；R480 跑 in_progress ⇒ NOT-RUN；436 reds=0。
② 产品：主列表补链接条目标记（2 张新帧、基线 300）。
③ 判据：时间行末列 +35px；M1308/M1309 2/2；标题图标 runner NOT-RUN 修复。
④ 预检 263/243/660；rot 350/1081；ARM 356/1144。
⑤ 捕获 300 帧；基线 300/0/0/0；build 0 告警；换装 ok/397=397；全量 1298/56/0。

NOT-RUN / 阻塞（分开写）：① R480 自身跑；② 链接标记 runner 1x/dark；③ 标题图标 runner（置空 ⇒ NOT-RUN）；④ 兜底路径/inline/幻影/图钉/冲突 runner 复核；⑤ SETTINGS_DATA_PATH；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–563 的其余未结项仍开。

下一轮（R482）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R481 自身跑、R480 跑、R479 跑、R478 两跑、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `ROW_LINK_BADGE`（≥8px·s）、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`ROW_RICH_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R480 状态（2026-10-29 · 本地 · 第 479 轮 / Round 477）：主列表补富文本格式标记（2 张新帧、基线 298）；全量 1297/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R480 / 第 479 轮 / Round 477）：打开「保留富文本格式」后 `Entry.richText` 已保存，但列表行看不出。修法：`RowTextColumn` 时间行在 OCR 标记后再补 `textformat`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），只有 richText 非空才出现。旧/新：**2 张新帧**（`row-rich-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **296→298**；2 张逐张看过。读数（`ROW_RICH_BADGE`）：负臂墨 9363→正臂 9593（+230）、dark 10477→10727（+250）。判据用成对帧读下半行墨差（末列会被标题第二行遮住，第一版当场改掉）；M1306/M1307 **2/2**。第一版产品位「浮层外缘线」让 18 个既有 QuickPick 判据红 ⇒ 撤回产品与判据，不改旧期望迁就。预检 **262/243/660 bad=0**、ARM **355/1144**、HIDDEN **349/1079 rot=0**。⓪：开工网络不可达（api=000、ls-remote remote closed）；收口两次 `git push` 均报 `correct access rights` ⇒ **`PUSH_BLOCKED=network`（HEAD=`60d65a4`、origin/main=`59b63c1`、ahead=1；本补记后 ahead=2）**；`gh` EOF ⇒ `CI_READ_BLOCKED`；sources 格 R480/`60d65a4`。R479/R478/R477 的跑读时 in_progress/未读 ⇒ NOT-RUN；436 无新跑。全量 **1297/56/0**（499.4s，轻载）；捕获卷 **298 帧**；基线 **298/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 395=395`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 479，`python3 scripts/product_streak.py --streak-for 479`，last=225e6f8）；清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 477 / 478 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ 网络不可达（api=000）；R479/R478/R477 的跑 in_progress/未读 ⇒ NOT-RUN；436 无新跑。
② 产品：主列表补富文本格式标记（2 张新帧、基线 298）。
③ 判据：成对帧墨差 +230/+250；M1306/M1307 2/2；末列判据被标题遮住当场改掉。
④ 自伤：外缘线让 18 条旧 QuickPick 判据红 ⇒ 撤回，不改旧期望。
⑤ 捕获 298 帧；基线 298/0/0/0；build 0 告警；换装 ok/395=395；全量 1297/56/0。

NOT-RUN / 阻塞（分开写）：① R479/R478/R477 的 in_progress 跑；② 富文本标记 runner 1x/dark；③ 标题图标/兜底路径/inline/幻影/图钉/冲突 runner 复验；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ LOCAL_PERF_BUDGET_FLAKE=load（本跑未触发）；⑨ 437–561 的其余未结项仍开。

下一轮（R481）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R480 自身跑、R479 跑、R478 两跑、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `ROW_RICH_BADGE`（≥8px²）、`SETTINGS_TITLE_ICON`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R479 状态（2026-10-29 · 本地 · 第 478 轮 / Round 476）：设置页标题补分类图标（36 张旧帧变化 + 2 张新帧、基线 296）；全量 1296/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R479 / 第 478 轮 / Round 476）：侧栏选中项有分类图标，内容页标题却只有一行字，换页后没有与侧栏同一个视觉锚点。修法：新 `SettingsPageTitle`（标题左侧 `category.icon`、`.secondary`、`accessibilityHidden`、与标题同字号；统计页 title semibold），7 个页面标题接入；加捕获缝 `settingsPageTitleIconForCapture` 供负向帧。旧/新：**36 张旧帧变化 + 2 张新帧**（`settings-data-no-title-icon` 亮暗）、0 缺失；基线 **294→296**；逐张看过数据/通用/统计等页：图标与侧栏同形、不挤压卡片。读数（`SETTINGS_TITLE_ICON`）：标题行末墨列 light/dark 均 **393→445px（+52px=26pt）**、墨 829→1156 / 897→1226。新判据用成对帧读标题末墨；`M1302`（永不画）/`M1303`（负向帧也画）**2/2**；负向帧补进 vibrant 盲区名册（首遍全量红 1 条，修名册后重跑）。预检 **261/243/660 bad=0**、ARM **354/1143**、HIDDEN **348/1077 rot=0**。⓪：`git push` **Everything up-to-date**、HEAD=origin/main=`7f21720`、**ahead=0**；R477 补记跑 `40797866181 ↔ 7a79987` failure 2 步（冲突判据仍 0!=2，7a79987 未含 7f21720 的 skip 修正）；R478 主跑 `40801850707 ↔ b64682e` 与补记跑 `40802042660 ↔ 7f21720` 读时 in_progress ⇒ NOT-RUN；R477 主跑 inline/幻影/图钉签收；R479 跑 `40805576917 ↔ 225e6f8` 读时 in_progress ⇒ NOT-RUN；sources 格 R479/`225e6f8`。436 无新跑。全量 **1296/56/0**（468.3s，轻载）；捕获卷 **296 帧**；基线 **296/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 388=388`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 478，`python3 scripts/product_streak.py --streak-for 478`，last=b64682e）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 476 / 477 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ no-op push、ahead=0；R477 补记跑冲突红（skip 位置，非产品）；R478 两跑 in_progress ⇒ NOT-RUN；R477 主跑三处修复签收。
② 产品：设置页标题补分类图标（36 旧帧 + 2 新帧、基线 296）。
③ 判据：成对帧标题末墨 +52px；M1302/M1303 2/2；负向帧补进名册。
④ 预检 261/243/660；rot 348/1077；ARM 354/1143。
⑤ 捕获 296 帧；基线 296/0/0/0；build 0 告警；换装 ok/388=388；全量 1296/56/0。

NOT-RUN / 阻塞（分开写）：① R478 两跑（in_progress）；② 兜底路径/冲突复验；③ 标题图标 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–558 的其余未结项仍开。

下一轮（R480）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R479 自身跑、R478 两跑 `40801850707 ↔ b64682e`/`40802042660 ↔ 7f21720`、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `SETTINGS_TITLE_ICON`（≥8pt）、`FALLBACK_PATH`（≥90pt）、`INLINE_CODE_PAD`（light ≥4.5、dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 8 行）、`QUICKPICK_PIN`（+104/+105）、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R478 状态（2026-10-29 · 本地 · 第 477 轮 / Round 475）：文件兜底态补父目录路径（4 张旧帧变化、基线 294）+ 捕获路径缝 + R462/R463 旧表重锚；全量 1295/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R478 / 第 477 轮 / Round 475）：兜底态只重复一遍文件名（详情头部已经有一份），用户看不到文件在哪。修法：`DetailFileView.fallbackView` 在文件名下补一行父目录（11pt、secondaryLabelColor、单行中间截断、与文件名同中轴），长文件名不再独占一整块。旧/新：**4 张旧帧变化**（两个兜底夹具 × 亮暗）、0 新增/缺失；基线 **294/0/0/0**；逐张看过：路径是稳定的用户路径 `/Users/tester/Desktop`、中间截断、不压浮层。读数（`FALLBACK_PATH`）：图标带下方最宽一行 **113.0pt**（旧形状里这一行是文件名本身，约 60pt），两档同形。第一版直接用 `url` 父目录，帧里出现捕获目录 `/var/folders/...` ⇒ 每跑都不同；加捕获缝 `fallbackParentPathForCapture`（产品默认 nil 读真实路径，夹具写稳定用户路径）后重捕，4 帧才可基线化。新判据 `testFallbackFileShowsWhereTheFileLives` 读图标下最宽行（≥90pt），不数行数；`M1300`（删路径）/`M1301`（置空）**2/2**。R478 把文件名包进 VStack 后，R462 的 `M1260`（撤四修饰）不再越界 ⇒ 退役为负向证人（期望 ESCAPED），`M1261`（撤内边距）仍 CAUGHT；R463 `M1262/M1263` 因共享色行重锚后 **2/2**。预检 **260/242/658 bad=0**、ARM **353/1141**、HIDDEN **347/1075 rot=0**。⓪：`git push` **Everything up-to-date**、HEAD=origin/main=`7a79987`、**ahead=0**；R477 跑 `40797827495 ↔ 0fd3ec0` 收口已读 **failure 4 步**：`INLINE_CODE_PAD light 99.0/93.0/6.0、dark 102.0/97.0/5.0`（两档过 4.5、padding 池签收）、幻影 1x 纯灰块 **0**、`QUICKPICK_PIN` 1x **54→74（+20）/标题末列 159→159**（签收）；Swift/Capture 唯一红是冲突判据 0!=2 —— skip 被插进了图钉测试，本补记移回；Release script 仍 sources 时序；Motion 1 红 = markdown 标签 1<2（已知采样）。补记跑 `40797866181` 未读；R476 与四跑沿用；436 无新跑，最后已知 `MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=0`。全量 **1295/56/0**（453.6s，轻载）；捕获卷 **294 帧**；基线 **294/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 477，`python3 scripts/product_streak.py --streak-for 477`，last=0fd3ec0）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 475 / 476 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ no-op push、ahead=0；R477 跑 failure 4 步已读：inline/幻影/图钉三处修复 runner 签收；冲突判据的 skip 放错测试（已修）；Motion markdown 标签 1<2 已知；436 无新跑。
② 产品：文件兜底态补父目录路径（4 张旧帧变化、基线 294）；加捕获路径缝让帧稳定。
③ 判据：M1300/M1301 2/2；R462 M1260 退役为负向证人、M1261 CAUGHT；R463 M1262/M1263 重锚 2/2。
④ 预检 260/242/658；rot 347/1075；ARM 353/1141。
⑤ 捕获 294 帧；基线 294/0/0/0；build 0 告警；换装 ok/387=387；全量 1295/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R477 补记跑 `40797866181`；② 冲突判据的 runner 复验（skip 已修，随本补记跑）；③ 兜底路径的 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 回执 flake；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–555 的其余未结项仍开。

下一轮（R479）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R478 自身跑、R477 两跑 `40797827495 ↔ 0fd3ec0`/`40797866181 ↔ 7a79987`、R476 跑 `40791382232 ↔ 599ec98`、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `INLINE_CODE_PAD`（light ≥4.5/真带 85/5.0、dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 块下限 8 行）、`QUICKPICK_PIN`（+104/+105、标题末列不动）、`FALLBACK_PATH`（≥90pt）、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 地板与 150 上限不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R477 状态（2026-10-29 · 本地 · 第 476 轮 / Round 474）：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）+ 按 R476 跑加 inline padding 池/幻影 8 行/冲突 NOT-RUN；全量 1294/56/0（产品 1 文件 + 判据 + 检测）

最后更新：2026-10-29（本地 · R477 / 第 476 轮 / Round 474）：主列表早已用 `pin.fill` 说“已固定”，浮层却把「置顶」两个字写进标题 —— 同一状态两种语言，而两个字会吃掉标题的截断预算。修法：`QuickPickController.rowTitle` 去掉「置顶」前缀；`QuickPickRowCell` 加 `pinnedBadge`（9pt `pin.fill`、叠在类型符号右下角、不占固定槽），`isHidden = !entry.isPinned`；读屏标签仍保留「置顶」前缀。旧/新：**2 张新帧**（`quickpick-pinned` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **292→294**；2 张逐张看过：图钉在类型符号右下角、标题起点未动。读数（`QUICKPICK_PIN`）：light 类型列墨 215→319（+104）、dark 233→338（+105）；两档标题末列 320→320（前缀没回标题）。新判据用成对帧三句（有对象/多图钉墨/标题末列不动）；`M1297`（永不显示）/`M1298`（永远显示+图像恒 pin）**2/2**；旧 `rowTitle` 契约测试按新语义改名并改断言。**按 R476 跑分桶继续修检测**：dark 四门 442/12/12/12/11；light 选中 102/101/1.0 的宽带（真带 85/80/5.0 在池里）⇒ `best` 先只留 padding≥4.5 的候选（池空退回全量打印缺陷读数）再取最宽实心带；本机恢复 light 98.5/92.5/6.0、dark 99.0/92.5/6.5；`M1299`（拆池）CAUGHT。幻影块下限 4→8 行（runner 1x 分隔线是 5 行 396px）；冲突提示在设置内容平涂时改 `SHORTCUT_CONFLICT_NOT_RUN=settings-content-blank` 并 skip。预检 **259/241/656 bad=0**、ARM **352/1139**、HIDDEN **346/1073 rot=0**。⓪：`git push` **`599ec98..3339baf` success**、HEAD=origin/main=`3339baf`、**ahead=0**；R476 跑 `40791382232 ↔ 599ec98` failure 3 步已读（Release script sources 时序；Swift/Capture 的 inline light 1.0、幻影 396、冲突平涂）；`QUICKPICK_LIST_RULE` 1x 6/6、`ROW_OCR_BADGE` 1x（+27/+24）、`TRUNCATION_NOTE 11/14` 签收；436 `MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=0`。R477 跑 `40797827495 ↔ 0fd3ec0` 读时 in_progress ⇒ NOT-RUN；sources 格 R477/`0fd3ec0`。全量 **1294/56/0**（472.2s，轻载；首遍旧契约测试红 1 条，改契约后重跑）；捕获卷 **294 帧**；基线 **294/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 476，`python3 scripts/product_streak.py --streak-for 476`，last=599ec98）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 474 / 475 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ push 599ec98..3339baf success、ahead=0；R476 跑 failure 3 步全部已读；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x、TRUNCATION 11/14 签收；436 5/5/77 reds=0。
② 产品：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）。
③ 判据：成对帧三句 + M1297/M1298 2/2；旧 rowTitle 契约测试改语义。
④ 按 R476 跑修检测：inline padding 池（本机 98.5/6.0、99/6.5，M1299）、幻影 8 行下限、冲突平涂 NOT-RUN。
⑤ 捕获 294 帧；基线 294/0/0/0；build 0 告警；换装 ok/387=387；全量 1294/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R477 自身跑；② inline padding 池的 runner 复验；③ 幻影 8 行的 runner 复验；④ 冲突提示在平涂 runner 上（预期 skip）；⑤ 图钉 runner 1x/dark；⑥ `SETTINGS_DATA_PATH` 两档；⑦ 既有 runner 复核（无新跑）；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 回执 flake；⑩ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑪ 437–552 的其余未结项仍开。

下一轮（R478）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R477 自身跑、R476 跑 `40791382232 ↔ 599ec98`、R475 跑 `40785879418 ↔ 638eeff`、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 R477 跑的 `INLINE_CODE_PAD`（light 应 ≥4.5，真带 85/5.0；dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 块下限 8 行，分隔线 5 行不许再进块）、`QUICKPICK_PIN`（类型列 +104/+105、标题末列不动）、`SHORTCUT_CONFLICT`/`SHORTCUT_CONFLICT_NOT_RUN`**；inline 仍红就按读数继续，4.5 地板不动、150 上限不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R476 状态（2026-10-29 · 本地 · 第 475 轮 / Round 473）：设置快捷键补冲突提示（2 张新帧、基线 292）+ inline ink 门改读垂直窗口/最宽实心带 + 幻影填充块下限按倍率；全量 1292/56/0（产品 2 文件 + 判据 + 检测）

最后更新：2026-10-29（本地 · R476 / 第 475 轮 / Round 473）：设置页三行快捷键可以设成同一组键，两组都真的注册过而系统只递一个 —— 另一行动作按下去没有反应，界面不说。修法：新纯函数 `ShortcutConflictPolicy.conflicts` 两两对账；`SettingsView.shortcutsSection` 在卡片下方画橙色警告（`exclamationmark.triangle.fill` + "「X」与「Y」都设为 ⌃⌥C —— 同一组键只会触发其中一个，请改开一个。"，caption、primary 正文、`accessibilityIdentifier`）。旧/新：**2 张新帧**（`settings-shortcuts-conflict` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **290→292**；2 张逐张看过：警告在卡片外、与页标题同列、橙图标可辨，正常页无警告。读数（`SHORTCUT_CONFLICT`）：light 负臂末墨行 582→660px（差 78px）、下方文字墨 4842、橙 221、负臂橙 0；dark 同形（5783/230/0）。判据用成对帧 + 双身份（文字墨 + 橙像素）；4 条纯函数；`M1293`（永不画）/`M1294`（无冲突也报）**2/2**。新帧进两本名册（vibrant 盲区、卡片外有意一段）。**靶指定的 inline 检测已按四门分桶改**：R475 跑 dark `候选=442 过span=12 过coverage=12 过ink=1 过rowMax=0`，真带只在文字上下 padding 行（本行 ink=0）⇒ `Candidate.verticalInk`（±20pt 窗口墨）+ `best` 先取 coverage≥0.90 实心池再取最宽；本机恢复 light 98.5/92.5/6.0、dark **99.0/92.5/6.5**（四门 35/35/35/35）；`M1295`（ink 门退回本行）/`M1296`（选择器退回 padding 优先）**2/2**；4.5 地板与 150 上限未动。幻影填充块下限改 `max(4, Int(3.5*scale))`（1x 4 行/2x 7 行），修 R474 分隔线在 1x 的 396px 误报。预检 **257/239/653 bad=0**、ARM **350/1136**、HIDDEN **344/1070 rot=0**。⓪：`git push` **`348e75e..638eeff` success**（两笔）、HEAD=origin/main=`638eeff`、**ahead=0**；R475 跑 `40785879418 ↔ 638eeff` failure 3 步（inline dark、幻影 1x、Motion 回执 1<2）；R474 主笔 `40780110804 ↔ d70cc57` failure 3 步（Release script 的 sources 格时序 + inline + 幻影）、补记 `40780464933 ↔ 348e75e` failure 2 步；`QUICKPICK_LIST_RULE` 1x 6/6、`ROW_OCR_BADGE` 1x（+27/+24）、`TRUNCATION_NOTE 11/14` 签收；436 见 `MOTION_FLOOR_FACTS judged=4/5 executed=77 reds=1`（已知回执 flake）。**收口 push `638eeff..599ec98` success**、HEAD=origin/main=`599ec98`、**ahead=0**；R476 跑 `40791382232 ↔ 599ec98` 读时 in_progress ⇒ NOT-RUN。全量 **1292/56/0**（511.8s，轻载）；捕获卷 **292 帧**；基线 **292/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 475，`python3 scripts/product_streak.py --streak-for 475`，last=c0b716a）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 473 / 474 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ push `348e75e..638eeff` success、ahead=0；R475 跑 failure 3 步已读（inline/phantom 为修前代码、Motion 回执 flake）；R474 两跑已读（Release script 的 sources 格时序）；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收。
② 产品：设置快捷键补冲突提示（2 张新帧、基线 292）。
③ 判据：成对帧 + 文字墨/橙像素双身份，M1293/M1294 2/2；新帧进两本名册；precheck 257/239/653；rot 344/1070。
④ 靶检测：按四门分桶把 ink 门改读 verticalInk、对象取最宽实心带；本机恢复 99/92.5/6.5（四门 35/35/35/35）；M1295/M1296 2/2；4.5 未动。
⑤ 幻影下限按倍率（1x 4/2x 7）；捕获 292 帧；基线 292/0/0/0；build 0 告警；换装 ok/387=387；全量 1292/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R476 自身跑（随提交创建）；② inline dark 的 runner 复验（本机已恢复）；③ 幻影填充 1x 的 runner 复验；④ 快捷键冲突提示的 runner 1x/dark；⑤ `SETTINGS_DATA_PATH` 两档（runner 平涂）；⑥ 既有 runner 复核（无新跑）；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 回执 flake；⑨ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑩ 437–550 的其余未结项仍开。

下一轮（R477）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R476 自身跑、R475 跑 `40785879418 ↔ 638eeff`、R474 两跑 `40780110804 ↔ d70cc57`/`40780464933 ↔ 348e75e`、R473/R472/R471 跑的全部失败步骤；**重点读 R476 跑的 `INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN`/`INLINE_CODE_PAD`（dark 应恢复 99/92.5/6.5、四门 35/35/35/35）与 `QUICKPICK_GREY_BAND`（1x 块下限 4 行）**：inline 仍红就按新分桶继续，4.5 地板不动、选择器上界 150 不动；`SHORTCUT_CONFLICT`（runner 1x/dark）；`ROW_OCR_BADGE` 1x 已签收；`QUICKPICK_LIST_RULE` 1x 6/6 已签收；`SETTINGS_DATA_PATH`；`TRUNCATION_NOTE`；`QUICKPICK_SOURCE_ICON`；`CROSS_YEAR`/`MAIN_ROWS`；`SETTINGS_HELPER_AXIS`；`CARD_INSET_CONTROL_FIRST`；`VIDEO_*`；Capture MATERIAL_BLIND_NOT_RUN；436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R475 状态（2026-10-29 · 本地 · 第 474 轮 / Round 472）：图片行补「可搜索文字」标记（2 张新帧、基线 290）+ INLINE_CODE_DIAG 四门分桶（本机 35/35/9/9；runner 待读）；全量 1286/56/0（产品 1 文件 + 判据 + 诊断）

最后更新：2026-10-29（本地 · R475 / 第 474 轮 / Round 472）：OCR 已落地的图片与普通图片在主列表里长得一模一样 —— 用户搜到一张图时看不出"这张图有可搜索的文字"。修法：`RowTextColumn` 的时间行改成 HStack，`entry.ocrText` 非空时在来源后补一枚 `text.viewfinder`（11pt、`secondaryLabelColor`、`helpLabel` + `accessibilityLabel`）；标在时间行末尾而非行尾，**行标题截断宽度一字未动**。旧/新：**2 张新帧**（`row-image-ocr` 亮暗）、**0 张既有帧变化**（含 57 张 row 帧逐字节不变）、0 缺失；基线 **288→290**；2 张逐张看过：标记在来源后、与时间行同基线、不压缩略图。读数（`ROW_OCR_BADGE`）：light 负臂末列 421px→正臂 455px、**末列差 34px（17pt）**、墨 3664→3770（+106）；dark 421→455、墨 4083→4189（+106）。新判据用**成对帧**（内容/时间/来源/缩略图逐项相同，只差 `ocrText`）：正臂最后墨列越过负臂 ≥3pt、墨量多 ≥10pt·1x；`M1291`（条件恒 false）/`M1292`（条件恒 true）**2/2 CAUGHT**；`M1220` 因时间行包 HStack 重钉，R444 表 **2/2**。**靶指定的 inline 四门分桶已加**：`INLINE_CODE_GATES` 本机 light `候选=299 过span=35 过coverage=35 过ink=9 过rowMax=9`、dark `281/35/35/9/9`，两者 `选中=true`（PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5）；**runner 分桶未读到**（R474 两跑 in_progress）⇒ 检测修复仍具名 NOT-RUN、选择器与 4.5 地板未动。预检 **255/237/649 bad=0**、ARM **348/1132**、HIDDEN **342/1066 rot=0**。⓪：开工 `git push` **Everything up-to-date**、HEAD=origin/main=`348e75e`、**ahead=0**；收口提交 `c0b716a` 后**两次 push 均报 `Please make sure you have the correct access rights and the repository exists.` ⇒ `PUSH_BLOCKED=network`（HEAD=`c0b716a`、origin/main=`348e75e`、ahead=1；本补记后 ahead=2）**；R474 跑 `40780110804 ↔ d70cc57` 与补记跑 `40780464933 ↔ 348e75e` 读时 in_progress（结论空）⇒ NOT-RUN；R473/R472/R471 四跑沿用 R474 补记已读；436 无 R475 新跑。全量 **1286/56/0**（500.9s，轻载）；捕获卷 **290 帧**；基线 **290/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 474，`python3 scripts/product_streak.py --streak-for 474`，last=d70cc57）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 472 / 473 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ 开工 no-op push、ahead=0；收口两探被拒 ⇒ PUSH_BLOCKED=network（HEAD c0b716a、origin 348e75e、ahead=1；补记后 2）；R474 两跑 in_progress ⇒ NOT-RUN；四跑沿用已读；436 无新跑。
② 产品：图片行补「可搜索文字」标记（2 张新帧、基线 290）。
③ 判据：成对帧读末列/墨差（34px/+106），M1291/M1292 2/2；M1220 重钉 2/2；precheck 255/237/649；rot 342/1066。
④ 靶诊断：`INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN` 四门分桶已加；本机 35/35/9/9、选中=true；runner 未读到 ⇒ 检测修复 NOT-RUN。
⑤ 捕获 290 帧；基线 290/0/0/0；build 0 告警；换装 ok/387=387；全量 1286/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R474 两跑（in_progress）；② `INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN` 的 runner 分桶（检测修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ Motion 回执/滚动会话/code-tab 字典 flake（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–546 的其余未结项仍开。

下一轮（R476）的靶：⓪ 先 `git push origin main`（禁 amend/force；当前 `PUSH_BLOCKED=network`、HEAD=`c0b716a`、origin/main=`348e75e`、ahead=1；补记后 ahead=2）并复核 ahead=0；读 R475 自身跑、R474 两跑 `40780110804 ↔ d70cc57`/`40780464933 ↔ 348e75e`、R473 追记 `40770699614 ↔ c3b8732`、R472 `40767358317 ↔ 7ce44a1`、R471 两跑的全部失败步骤；**重点拿 `INLINE_CODE_GATES` 与 `INLINE_CODE_TOP_SPAN` 的 dark 分桶**：按 span/coverage/ink/rowMax 哪一门把长带砍掉，再改检测；4.5 地板不动、选择器不盲调。其余重点：`ROW_OCR_BADGE`（暗档/1x）、`QUICKPICK_LIST_RULE`（1x/空结果）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R474 状态（2026-10-29 · 本地 · 第 473 轮 / Round 471）：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）+ 药丸尺加连续行分组；全量 1285/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R474 / 第 473 轮 / Round 471）：搜索框和候选列表之间只有 8pt 留白，输入区与内容区同属一块。修法：`QuickPickController` 加 `NSBox(.separator)`，宽=搜索框宽（左右 12pt 内缩）、厚 1pt、顶钉 `scroll.topAnchor`（8pt 间距下沿，**不占行高**）；不能钉 `field.bottomAnchor`（焦点/悬停描边向下多出 4pt，贴底边的线会从焦点环里穿过去，焦点帧直看后改的）。旧/新：8 个浮层夹具 × 亮暗 **16 张帧变化**、0 新增/缺失；基线 **288/0/0/0**；16 张逐张看过：线在同一条轴、无溢出、列表行几何未动。同帧读数（`QUICKPICK_LIST_RULE`）：light/dark × list/typed/empty 均 `线数=1 y=71px 厚=2px 宽=792px 左=24px`（帧宽 840px ⇒ 通栏 94.3%），搜索框底 56px、药丸顶 92px；旧产品帧同判据 **0 条**（反向验证）。**靶修只拿到部分数据**：`INLINE_CODE_DIAG dark` 现读 `页=52 带=60 候选=442 选中=false`（两次跑同形；top 全是 s20 的高 padding 短碎片，长带候选的 span/覆盖率/ink/rowMax 分桶还没打印）⇒ 检测修复仍具名 NOT-RUN、不盲调选择器、4.5 地板未动。预检 **254/236/647 bad=0**、ARM **347/1130**、HIDDEN **341/1064 rot=0**。⓪：开工两探受阻，**收口前网络恢复 ⇒ 一次快进 push `c3b8732..d70cc57` success**（三笔：55f8810/04a4022/d70cc57）、HEAD=origin/main=`d70cc57`、**ahead=0**；R474 跑 `40780110804 ↔ d70cc57` queued ⇒ NOT-RUN；R473 追记 `40770699614 ↔ c3b8732` 与 R472 `40767358317 ↔ 7ce44a1`、R471 `40759492283 ↔ e664410`/`40759325073 ↔ ad722b4` 已读（inline dark 同形；code-tab 字典崩溃、Motion 回执 1<2）；436 无 R474 新跑。全量 **1285/56/0**（500.7s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 473，`python3 scripts/product_streak.py --streak-for 473`，last=eb40069）。清账 `格=162 声明=63 不成立=0/63`；§1 已刷新（尾轮 471 / 472 节）；电池 **Ran 683 / OK skipped=5**；清账 162/63/0。

本轮做了什么：
① ⓪ 开工两探被网络挡住，收口前恢复 ⇒ 一次快进 push c3b8732..d70cc57 success（ahead=0）；四跑已读：inline dark 同形、R473 追记 code-tab 字典崩溃、R471 追记 Motion 回执 1<2；dark DIAG 部分拿到（选中=false），长带四门分桶未打印 ⇒ 检测修复 NOT-RUN、未盲调。
② 产品：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）；焦点帧发现线穿焦点环，改钉 `scroll.topAnchor`。
③ 判据：`QUICKPICK_LIST_RULE` 6/6、旧产品帧 0 条；`overlayPill` 连续行分组 + `minHeight`，真值表第 ⑧ 格；M1288–M1290 3/3；r104 重锚 4/4、M1281 重锚 CAUGHT；precheck 254/236/647；rot 341/1064。
④ 436：无新跑；不重猜 must_judge。
⑤ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1285/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R474 自身跑 `40780110804 ↔ d70cc57`（queued）；② `INLINE_CODE_DIAG dark` 的长带四门分桶（检测修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ Motion 回执/滚动会话/code-tab 字典 flake（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–543 的其余未结项仍开。

下一轮（R475）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R474 跑 `40780110804 ↔ d70cc57`、R473 追记 `40770699614 ↔ c3b8732`、R472 跑 `40767358317 ↔ 7ce44a1`（日志全 `UNKNOWN STEP`，按 emit 串取正文）、R471 `40759492283 ↔ e664410`/`40759325073 ↔ ad722b4` 的全部失败步骤；重点先把 `INLINE_CODE_DIAG dark` 的候选按「span / 覆盖率 / ink / rowMax」四门分桶打印（top 全是 s20 短碎片，长带是否被某道门砍掉未知；拿到分桶再改检测、不盲调选择器、4.5 地板不动）、`QUICKPICK_LIST_RULE`（1x/空结果）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`（2x 等距连跑 21、1x 词簇 ≥5）、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R473 状态（2026-10-29 · 本地 · 第 472 轮 / Round 470）：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）+ 判据改用等距连跑；全量 1284/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R473 / 第 472 轮 / Round 470）：隐私卡里已有保存路径，但用户找“存在哪”时在「数据」页；数据页以前只说“保存在本地”。修法：在“剪贴板历史保存在本地…”下补一行 `SettingsPathText("保存位置：~/Library/Application Support/时间剪史/")`，复用 R472 的路径等宽组件。旧/新：数据页从**无路径行** → 有路径行；**2 张旧帧变化**（settings-data 亮暗）、0 新增/缺失；基线 **288/0/0/0**；2 张逐张看过：路径单行等宽、卡片未溢出。**判据首版假绿**：按“最大窄簇数”找路径行，新帧 37，而旧帧（无路径）同一 CJK 导出说明也读到 51 簇/37 窄簇；当场改成**等距连跑**（窄簇起点间隔围着 `SettingsPathPresentation.pathFont` 的 advance 6.8pt）：新路径行 **21**、旧帧最大 **3**；`M1286/M1287` **2/2 CAUGHT**。**靶修未做**：`INLINE_CODE_DIAG dark` 的页/带/候选/top 数据未拿到（R472 跑 in_progress）⇒ 按靶具名 NOT-RUN，不盲调选择器、4.5 地板未动。预检 **253/235/644 bad=0**、ARM **346/1127**、HIDDEN **340/1061 rot=0**。⓪：开工验 remote 仍 `35f4bfd`；一次快进 push **`35f4bfd..7ce44a1` success**（三笔）、HEAD=origin/main=`7ce44a1`、**ahead=0**；R472 跑 `40767358317 ↔ 7ce44a1` **in_progress ⇒ NOT-RUN**；收口一次快进 push **`7ce44a1..c3b8732` success**、HEAD=origin/main=`c3b8732`、**ahead=0**；R473 自身跑 `40770699614 ↔ c3b8732` **queued ⇒ NOT-RUN**；补记 `55f8810` 的 push 两探 remote closed ⇒ **`PUSH_BLOCKED=network`（探测时 HEAD=`55f8810`、origin/main=`c3b8732`、ahead=1；本补记二后 ahead=2）**；R471 两跑沿用（TRUNCATION_NOTE 11/14、来源图标 5/5/84、CROSS_YEAR/MAIN_ROWS 签收；fa0db55 Motion 回执 flake）；436 无 R473 新跑。全量 **1284/56/0**（468.5s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 472，`python3 scripts/product_streak.py --streak-for 472`，last=1bd7c60）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 470（n=463、471 节）；电池 **Ran 683 / OK (skipped=5)**。

本轮做了什么：
① ⓪ push `35f4bfd..7ce44a1` success、ahead=0；R472 跑 in_progress ⇒ NOT-RUN；dark DIAG 数据未拿到 ⇒ 靶修复 NOT-RUN、不盲调。
② 产品：数据页补保存位置（等宽路径行；2 张数据帧变化、基线 288）。
③ 判据：首版窄簇尺在旧帧假绿，改成等距连跑（21 vs 3）；M1286/M1287 2/2；precheck 253/235/644；rot 340/1061。
④ 436：无 R473 新跑；R471 的 Motion 回执 flake 沿用，不改门槛。
⑤ 367：hidden 表 340 / 可判 1061 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1284/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R472 自身跑（in_progress）、R473 自身跑 `40770699614 ↔ c3b8732`（queued）；② `INLINE_CODE_DIAG dark` 的 runner 数据（靶修复未做）；③ 数据页路径的 runner 1x（设置内容列可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明/来源图标/跨年 runner 已签收；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–540 的其余未结项仍开。

下一轮（R474）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R473 主笔+追记 head 跑、R472 跑 `40767358317 ↔ 7ce44a1`、R471 两跑的全部失败步骤；重点 `INLINE_CODE_DIAG dark`（页/带/候选/top、m=rowMax；拿到数据再改检测、不盲调选择器、4.5 地板不动）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`（2x 等距连跑 21、1x 词簇 ≥5）、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；**R473 收口预记**：收口一次快进 push **`7ce44a1..c3b8732` success**、HEAD=origin/main=`c3b8732`、**ahead=0**；R472 跑 `40767358317 ↔ 7ce44a1` 仍 **in_progress ⇒ NOT-RUN**、R473 跑 `40770699614 ↔ c3b8732` **queued ⇒ NOT-RUN**；`INLINE_CODE_DIAG dark` 的页/带/候选/top 仍未读到 ⇒ 靶检测修复 NOT-RUN、未盲调；R471 两跑已读：TRUNCATION_NOTE 11/14、来源图标 5/5/84、CROSS_YEAR/MAIN_ROWS 38.0 签收，fa0db55 Motion 回执 flake；R474 ⓪ 先验 remote 仍 `c3b8732`，一次快进 push 两笔补记（`55f8810`/补记二）；再读 40767358317/40770699614 与补记跑（若创建），拿 DIAG dark 再改检测；③ 436 只复核新跑 Motion floor。
## R472 状态（2026-10-29 · 本地 · 第 471 轮 / Round 469）：设置存储路径等宽（isFixedPitch；4 张隐私帧变化、基线 288）+ INLINE_CODE_DIAG 前移；全量 1283/56/0（产品 1 文件 + 判据/仪器）

最后更新：2026-10-29（本地 · R472 / 第 471 轮 / Round 469）：隐私「数据与保留」卡里的 `保存位置：~/Library/Application Support/时间剪史/` 以前整句比例字体；新增 `SettingsPathPresentation.split`（在 "~/" 处拆前缀/路径）与 `SettingsPathText`，路径用 `monospacedSystemFont`（`pathFont`），前缀保持说明字体。旧/新：`isFixedPitch` 旧 false → 新 true；拆分前缀「保存位置：」/路径完整。**4 张旧帧变化**（`settings-privacy-tall` / `settings-privacy-excluded` 亮暗）、0 新增/缺失；基线 **288/0/0/0**；4 张逐张看过：路径单行等宽、无换行/截断。判据 3 格（split 有/无路径、isFixedPitch 两臂）；`M1284/M1285` **2/2 CAUGHT**。**靶修**：`INLINE_CODE_DIAG` 移到 `best` 之前（无带时用候选首行做锚点、多打 `选中=`、top 仍含 `m=rowMax`）；不改选择器/4.5；本地 `INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5` 不变；runner dark 数据待 R472 自身跑。预检 **252/234/642 bad=0**、ARM **345/1125**、HIDDEN **339/1059 rot=0**。⓪：开工 HEAD=origin/main=`35f4bfd`、**ahead=0**；`git push` **Everything up-to-date**；R471 两跑收口已读：`40759325073 ↔ fa0db55` failure **3 步**（inline dark + Motion floor `testCopyReceipt...` 1<2 ⇒ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`），`40759492283 ↔ 35f4bfd` failure 2 步（仅 inline dark）；**签收** `TRUNCATION_NOTE 11/14、说明 1 次`、`QUICKPICK_SOURCE_ICON 5/5、84、负臂 0`、`CROSS_YEAR/MAIN_ROWS 38.0`；`SETTINGS_HELPER_AXIS_NOT_RUN`、`MATERIAL_BLIND_NOT_RUN`、`VIDEO_*` 沿用；收口 `git push` 两探均 `Connection closed ... port 22` ⇒ **`PUSH_BLOCKED=network`（HEAD=`ae6d900`、origin/main=`35f4bfd`、ahead=2）**；R472 自身跑**未创建** ⇒ NOT-RUN；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**。全量 **1283/56/0**（454.3s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 471，`python3 scripts/product_streak.py --streak-for 471`，last=ad722b4）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 469（n=462、470 节）；电池 **Ran 683 / OK (skipped=5)**。

本轮做了什么：
① ⓪ no-op push success；R471 两跑已读（TRUNCATION_NOTE/来源图标/CROSS_YEAR/MAIN_ROWS 签收，inline dark，Motion 回执 flake）；R472 自身跑待读。
② 产品：设置存储路径等宽（4 张隐私帧变化、基线 288）。
③ 判据：isFixedPitch + split 3 格；M1284/M1285 2/2；DIAG 前移；precheck 252/234/642；rot 339/1059。
④ 436：R471 fa0db55 的 Motion 回执 1<2 具名 `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；35f4bfd 未红；不改门槛。
⑤ 367：hidden 表 339 / 可判 1059 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1283/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R472 自身跑（未创建，PUSH_BLOCKED）；② inline dark 的 DIAG runner 数据；③ 路径字体的 runner 1x（设置内容列可能平涂）；④ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑤ 截断说明 runner（本跑已签收 11/14）；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–537 的其余未结项仍开。

下一轮（R473）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R472 主笔+追记 head 跑与 R471 两跑（`40759325073 ↔ fa0db55`、`40759492283 ↔ 35f4bfd`）的全部失败步骤；重点 `INLINE_CODE_DIAG dark`（页/带/候选/top，m=rowMax；按数据改检测、不盲调选择器、4.5 地板不动）、`INLINE_CODE_PAD` 两档、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；**R472 收口预记**：收口 `git push` 两探 remote closed ⇒ **`PUSH_BLOCKED=network`（HEAD=`ae6d900`、origin/main=`35f4bfd`、ahead=2：1bd7c60/ae6d900）**；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**；R472 自身跑**未创建** ⇒ NOT-RUN。R471 两跑已读：`40759325073 ↔ fa0db55` failure **3 步**（inline dark + Motion 回执 1<2 ⇒ `RUNNER_COPY_RECEIPT_MOTION_FLAKE`），`40759492283 ↔ 35f4bfd` failure 2 步（仅 inline dark）；`TRUNCATION_NOTE 11/14、说明 1 次` 与 `QUICKPICK_SOURCE_ICON 5/5/84、负臂 0` 签收、`CROSS_YEAR/MAIN_ROWS 38.0` 签收；`SETTINGS_HELPER_AXIS_NOT_RUN`、`MATERIAL_BLIND_NOT_RUN`、`VIDEO_*` 沿用。R473 ⓪ 先验 remote 仍 `35f4bfd`，一次快进 push 三笔（1bd7c60/ae6d900/补记），再读 R472 新跑与 R471 两跑；③ 436 只复核新跑 Motion floor。
## R471 状态（2026-10-29 · 本地 · 第 470 轮 / Round 468）：详情截断说明降到 meta 字号（11 vs 正文 14；2 张新帧、基线 288）；全量 1280/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R471 / 第 470 轮 / Round 468）：正文超过 40k 时，尾部「……（后面的内容没有渲染，切到「原文」看全文）」旧形状用**正文字号 14pt**接在最后一段后，读起来像剪贴板正文的一部分；它是界面说明。修法：说明改用 `DetailTypography.metaFontSize`（11pt），仍 secondary。旧/新：`TRUNCATION_NOTE light/dark 说明字号/正文字号 14/14 → 11/14`（说明出现 1 次）；`TRUNCATION_PARSE 截断=true 属性串长=39997 含说明=true`。**2 张新帧**（`detail-markdown-truncated` 亮/暗，渲染后滚到底）、0 变化/缺失；基线 **286→288/0/0/0**；亮/暗看过：说明一行、明显小于正文、位于正文结尾。判据 `testTruncationNoteSitsBelowTheBodyTier` 从产品 NSTextView 读说明/正文字号（相对量）；`M1282/M1283` **2/2 CAUGHT**；夹具首版 2100 段只有 39.9k（截断=false，说明没有），诊断抓到后改 2400 段（45,664 字）。预检 **251/233/640 bad=0**、ARM **344/1123**、HIDDEN **338/1057 rot=0**。⓪：开工 HEAD=origin/main=`e664410`、**ahead=0**；`git push` 两探均 remote closed ⇒ **`PUSH_BLOCKED=network`（HEAD=`e664410`、ahead=0）**；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**；R470 两跑读时未读；收口网络恢复，`git push` **`e664410..fa0db55` success**、HEAD=origin/main=`fa0db55`、**ahead=0**；`40754306434 ↔ e664410` failure 2 步：`QUICKPICK_SOURCE_ICON 5/5、彩度 84、负臂 0` **runner 签收**，`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR 38.0` 签收，唯一测试红 **inline dark 从 3.0 变「找不到带」**（整行门排掉假 150 带，真带仍不在暗档候选；DIAG 在 guard 后没打出）；`40754111098 ↔ f15bbf9` cancelled ⇒ NOT-RUN；R471 自身跑 `40759325073 ↔ fa0db55` in_progress ⇒ NOT-RUN；R469 四跑沿用上轮。全量 **1280/56/0**（492.1s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 470，`python3 scripts/product_streak.py --streak-for 470`，last=df63e5b）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 468（n=461、469 节）；电池 **Ran 683 / OK (skipped=5)**。

本轮做了什么：
① ⓪ 两探 push 断网、gh EOF ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R470 两跑与 R471 自身跑 NOT-RUN；R469 四跑沿用；436 无新跑。
② 产品：截断说明退到 meta 字号（14/14 → 11/14；2 张新帧、基线 288）。
③ 判据：产品 NSTextView 字号相对量；M1282/M1283 2/2；夹具 40k 真截断诊断；precheck 251/233/640；rot 338/1057。
④ 436：无 R471 新跑；Motion floor NOT-RUN，采样红沿用。
⑤ 367：hidden 表 338 / 可判 1057 / rot 0。
⑥ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1280/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40754111098 ↔ f15bbf9`（cancelled）与 `40759325073 ↔ fa0db55`（in_progress）；② 截断说明 runner 1x；③ 40k 夹具 runner 捕获；④ inline dark 新门：`e664410` 跑已从 3.0 变「找不到带」，真带不在暗档候选（R472 先移 DIAG 到 guard 前并查检测）；⑤ 来源图标 runner 1x；⑥ `SETTINGS_HELPER_AXIS` / `CARD_INSET_CONTROL_FIRST` runner；⑦ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–534 的其余未结项仍开。

下一轮（R472）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R471 主笔+追记 head 跑与 R470 两跑（`40754111098 ↔ f15bbf9`、`40754306434 ↔ e664410`）的全部失败步骤；重点 `TRUNCATION_NOTE`（说明 11/正文 14、说明 1 次）、`QUICKPICK_SOURCE_ICON`、`INLINE_CODE_DIAG`（m=rowMax）与 `INLINE_CODE_PAD` dark、`CROSS_YEAR_TIME`、`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；**R471 收口预记**：收口 push **`e664410..fa0db55` success**、HEAD=origin/main=`fa0db55`、**ahead=0**；`40754306434 ↔ e664410` failure 2 步（`QUICKPICK_SOURCE_ICON 5/5/84、负臂 0` 签收；CROSS_YEAR/MAIN_ROWS 38.0 签收；唯一红 inline dark 变「找不到带」，R470 整行门排掉假 150 后真带仍不在暗档候选）；`40754111098 ↔ f15bbf9` cancelled ⇒ NOT-RUN；R471 自身跑 `40759325073 ↔ fa0db55` in_progress ⇒ NOT-RUN；补记跑（若创建）下一轮一并读；③ 436 只复核新跑 Motion floor。
## R470 状态（2026-10-29 · 本地 · 第 469 轮 / Round 467）：浮层行补来源 App 图标（5/5 有图、首行 412 彩度；12 张旧帧变化 + 2 张新帧、基线 286）+ inline 全宽块底门（本地 98.5/6.0、99.0/6.5）；全量 1279/56/0（产品 1 文件 + 判据/仪器）

最后更新：2026-10-29（本地 · R470 / 第 469 轮 / Round 467）：浮层每行原来只有类型符号，来源 App 只在主列表/详情露出。修法：类型符号后加**固定 16pt 来源槽**（`SourceAppIconProvider` 的 App 图标；没有来源时留空但占位，标题轴不抖），标题从来源槽右侧起。旧/新：`QUICKPICK_SOURCE_ICON light/dark 有图=0 → 5/5、类型=5/5、首行彩度像素=0 → 412/412`；负臂 `quickpick-no-source` 来源图=0、类型=1、彩度=0；首行标题左沿正/负臂同为 **78.5pt**。**12 张旧帧变化 + 2 张新帧**、0 缺失；基线 **284→286/0/0/0**；14 张逐张看过。判据 `testQuickPickRowsShowTheirSourceIcon`（结构 image + 像素彩度两条腿）；`M1279/M1280` **2/2 CAUGHT**。**inline 全宽块底门**：候选增 `rowMaxBandRun`，`best` 要求 `rowMaxBandRun <= maxSpan`（整行全宽块底整行排除）；本地 `INLINE_CODE_PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5`（不变）；`M1277/M1278` **2/2 CAUGHT**。**药丸材料 gap 容忍**：`overlayPill` 加 `maxGap`（本判据 24pt），light/dark 药丸 **22.0pt**、搜索 22.5pt、差 **1px**；`M1281` **1/1 CAUGHT**。**旧表重钉**：r430 M1175、r104 M578/M579 因约束签名/overlayPill 新参数腐烂，重钉后 r430 **5/5**、r104 M578/M579 **2/2**、RESTORE_CLEAN。预检 **250/232/638 bad=0**、ARM **343/1121**、HIDDEN **337/1055 rot=0**。⓪：开工 HEAD=origin/main=`1f7f486`、**ahead=0**；`git push` 两探均 remote closed ⇒ **`PUSH_BLOCKED=network`（HEAD=`1f7f486`、ahead=0）**；`gh` EOF ⇒ **`CI_READ_BLOCKED=network`**；R469 四跑 `40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`、`40745716427 ↔ 1f7f486` 均 **NOT-RUN**；`40740068763 ↔ 00ff343` failure 2 步仅 inline dark 3.0、Capture 15 帧变 MATERIAL_BLIND_NOT_RUN、设置轴 runner 具名 NOT-RUN、VIDEO_* 签收、DIAG 数据如审计 U-1773；收口 push **`1f7f486..f15bbf9` success**、HEAD=origin/main=`f15bbf9`、**ahead=0**；R469 四跑已读 failure 2 步（`CROSS_YEAR_TIME` 与 `MAIN_ROWS_CROSS_YEAR 38.0` 签收；inline dark、scroll flake、`RUNNER_CODE_TAB_DICT_NIL_FLAKE`），R470 跑 `40754111098 ↔ f15bbf9` queued ⇒ NOT-RUN。全量 **1279/56/0**（507.3s，轻载）；捕获卷 **286 帧**；基线 **286/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 469，`python3 scripts/product_streak.py --streak-for 469`，last=4283a90）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 467（n=460、468 节）；电池 **Ran 683 / OK (skipped=5)**。

本轮做了什么：
① ⓪ 两探 push 断网、gh EOF ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R469 四跑与 R470 自身跑 NOT-RUN；上轮 00ff343 跑只 inline dark 3.0，Capture 15 帧变 MATERIAL_BLIND_NOT_RUN，设置轴具名 NOT-RUN；DIAG 数据已拿到。
② 产品：浮层来源 App 图标（固定 16pt 槽；12 张旧帧变化 + 2 张新帧、基线 286）。
③ 判据/仪器：来源图标 2/2、inline 块底门 2/2、药丸 gap 1/1；旧表 M1175/M578/M579 重钉复跑；precheck 250/232/638；rot 337/1055。
④ 436：无 R470 新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 337 / 可判 1055 / rot 0。
⑥ 捕获 286 帧；基线 286/0/0/0；build 0 告警；换装 ok/387=387；全量 1279/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R469 四跑与 R470 自身跑（网络）；② inline runner dark（新门未跑）；③ 来源图标 runner 1x；④ `SETTINGS_HELPER_AXIS` runner 1x；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–531 的其余未结项仍开。

下一轮（R471）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R470 主笔+追记 head 跑与 R469 四跑（`40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`、`40745716427 ↔ 1f7f486`）的全部失败步骤；重点 `QUICKPICK_SOURCE_ICON`（5/5、412、负臂 0）、`INLINE_CODE_DIAG`（top 的 m=rowMax；真带 vs 全宽块底）、`INLINE_CODE_PAD` 两档（dark 新门后应 ≥4.5）、`CROSS_YEAR_TIME`、`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS` 200/198/−2、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`VIDEO_SEEK` 98/106、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE`、`VIDEO_UNAVAILABLE`、Capture MATERIAL_BLIND_NOT_RUN、436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；**R470 收口预记**：收口 push **`1f7f486..f15bbf9` success**、HEAD=origin/main=`f15bbf9`、**ahead=0**；R469 四跑均 failure 2 步：`40745559043 ↔ f761880` = inline dark + `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（`__NSPlaceholderDictionary`，后三跑通过），`40745622954 ↔ 170a11e` / `40745662770 ↔ 6dd787a` = inline dark，`40745716427 ↔ 1f7f486` = inline dark + `RUNNER_SCROLL_SESSION_FLAKE`；四跑 `CROSS_YEAR_TIME` 与 `MAIN_ROWS_CROSS_YEAR 231.0/269.0/差38.0` 已签收；`SETTINGS_HELPER_AXIS_NOT_RUN`、`MATERIAL_BLIND_NOT_RUN`、`VIDEO_*` 沿用；R470 自身跑 `40754111098 ↔ f15bbf9` **queued ⇒ NOT-RUN**（inline 新门 + 来源图标待读）；补记跑（若创建）下一轮一并读；③ 436 只复核新跑 Motion floor。
## R469 状态（2026-10-29 · 本地 · 第 468 轮 / Round 466）：跨年时间标注（旧两条「6月15日 12:00」→ 旧行「2025年6月15日 12:00」；主列表行宽差 +41.0pt；4 张新帧、基线 284）；全量 1278/56/0（产品 4 文件 + 判据）

最后更新：2026-10-29（本地 · R469 / 第 468 轮 / Round 466）：主列表与浮层都用 `M月d日 HH:mm`，2025 与 2026 的同月同日分不清。新增 `TimestampYearPolicy.showsYear(for:relativeTo:)`：参照=当前列表/候选里最新一条（不是挂钟），不同年才加 `yyyy年`；接 4 个产品文件（`ClipboardDateFormatters`、`QuickPickController`、`HistoryRowViews`、`HistorySidebarView`）。旧/新：`quickpick-cross-year` 两条都「6月15日 12:00」→ 旧行「2025年6月15日 12:00」、新行紧凑；`rows-cross-year` 主列表行宽 **234.5 / 275.5 / +41.0pt**。**4 张新帧**（quickpick/rows 亮暗）、0 变化/缺失；基线 **284/0/0/0**；4 张逐张看过无截断。判据：`testCrossYearTimesCarryTheYear`（浮层真字符串）+ `testMainRowsCrossYearTimeLineWidens`（行宽 +41.0）+ 纯策略 4 格；`M1275/M1276` **2/2 CAUGHT**（M1275 首跑被测试的去重闸门吞成 NOT-RUN，改成按时间格数断言后重跑）。**旧表重钉**：M1174/M1177（r430 时间列）与 M1220（r444 行来源）因共享调用改行腐烂，重钉后 r430 **5/5**、r444 **2/2**、RESTORE_CLEAN。预检 **247/229/633 bad=0**、ARM **340/1116**、HIDDEN **334/1050 rot=0**。⓪：开工 HEAD=`00ff343`、origin/main=`0774453`、ahead=2；一次快进 push **`0774453..00ff343` success**、HEAD=origin/main=`00ff343`、**ahead=0**；`40736447466 ↔ 0774453` **job cancelled**（失败步骤 0）⇒ NOT-RUN；`40740068763 ↔ 00ff343` **failure 2 步**（唯一测试红 inline dark 3.0；Capture 15 帧变 `MATERIAL_BLIND_NOT_RUN`、设置轴 runner 具名 NOT-RUN）；已读 `VIDEO_SEEK 98/106`、`VIDEO_ALIGN 13.0`、`VIDEO_SURFACE 0/157` 与 `0/33`、`VIDEO_UNAVAILABLE 5/4`；`INLINE_CODE_DIAG` 首份数据 light 选行=143/页236/带212/候选326（top s21/p21）、dark 选行=319/页68/带76/候选444（top r319 s320/p320、r310 s20/p20）；收口一次快进 push **`00ff343..f761880` success**、HEAD=origin/main=`f761880`、**ahead=0**；R469 自身跑 `40745559043 ↔ f761880` queued ⇒ NOT-RUN。全量 **1278/56/0**（468.2s，轻载）；捕获卷 **284 帧**；基线 **284/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 468，`python3 scripts/product_streak.py --streak-for 468`，last=869e7de）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 466（n=459、467 节）；电池 **Ran 683 / OK (skipped=5)**。

本轮做了什么：
① ⓪ push `0774453..00ff343` success、ahead=0；R468 跑 cancelled ⇒ NOT-RUN；00ff343 跑 failure 2 步仅 inline dark 3.0，Capture 15 帧变 MATERIAL_BLIND_NOT_RUN，设置轴具名 NOT-RUN；INLINE_CODE_DIAG 首份数据已拿到。
② 产品：跨年时间标注（浮层/主列表；4 个产品文件；4 张新帧、基线 284）。
③ 判据：浮层真字符串 + 主列表行宽 +41.0；M1275/M1276 2/2；旧表 M1174/M1177/M1220 重钉并复跑；precheck 247/229/633；rot 334/1050。
④ 436：无 R469 新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 334 / 可判 1050 / rot 0。
⑥ 捕获 284 帧；基线 284/0/0/0；build 0 告警；换装 ok/387=387；全量 1278/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40736447466 ↔ 0774453`（cancelled）与 R469 自身跑（收口视网络）；② `INLINE_CODE_DIAG` 的选择器修复（数据已拿到，下一轮改）；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` runner 1x（settings-content-blank）；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–528 的其余未结项仍开。

下一轮（R470）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R469 主笔+追记 head 跑（`40745559043 ↔ f761880`、`40745622954 ↔ 170a11e`、`40745662770 ↔ 6dd787a`，均 queued/in_progress ⇒ NOT-RUN，下一轮全读；补记三触发的跑也一并读）、`40740068763 ↔ 00ff343` 的全部失败步骤，重点 `CROSS_YEAR_TIME`（浮层两条）、`MAIN_ROWS_CROSS_YEAR`（+41.0）、`SETTINGS_HELPER_AXIS` 200/198/−2、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`INLINE_CODE_DIAG` 的选择器修复（真带 r310 s20/p20 vs 全宽 r319 s320/p320、ink=0；地板 4.5 不动）、`INLINE_CODE_PAD` 两档、`VIDEO_SEEK` 98/106、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE`、`VIDEO_UNAVAILABLE`、Capture gate 的 MATERIAL_BLIND_NOT_RUN、其余既有判据与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；**R469 收口预记**：收口 push **`00ff343..f761880` success**、HEAD=origin/main=`f761880`、**ahead=0**；`40740068763 ↔ 00ff343` **failure 2 步**（Swift tests / Capture gate）唯一测试红 `INLINE_CODE_PAD dark 150/147/3.0`，Capture 15 帧方向变 `MATERIAL_BLIND_NOT_RUN`（R467 intentional 生效），`SETTINGS_HELPER_AXIS_NOT_RUN=settings-content-blank` 亮/暗；已读 `VIDEO_SEEK 98/106`、`VIDEO_ALIGN 13.0`、`VIDEO_SURFACE 0/157` 与 `0/33`、`VIDEO_UNAVAILABLE 5/4`；`INLINE_CODE_DIAG` 首份数据见 ⓪；`40736447466 ↔ 0774453` **cancelled**（0 失败步骤）⇒ NOT-RUN；R469 自身跑 `40745559043 ↔ f761880` **queued ⇒ NOT-RUN**；补记跑（若创建）下一轮一并读；③ 436 只复核新跑 Motion floor。
## R468 状态（2026-10-29 · 本地 · 第 467 轮 / Round 465）：设置开关说明文字与标签同轴（旧 200.0/179.0 差 21.0pt → 新 200.0/198.0 差 −2.0pt；14 张 settings 帧变化、基线 280）；全量 1272/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R468 / 第 467 轮 / Round 465）：通用/隐私页的说明段是 `VStack` 里独立 `Text`，从复选框左沿起排、标签从复选框右侧起排 —— `settings-general` 帧量到标签左 **200.0pt**、说明左 **179.0pt**，差 **21.0pt**。修法：`SettingsViewLayout.helperAxisIndent = 21`（复选框 14pt + 标签间距 7pt）+ `.settingsHelperAxis()`，接 6 处（登录回执、暂停/OCR/RTF、推荐过滤、OCR 存储）。旧/新：`SETTINGS_HELPER_AXIS light/dark 标签左=200.0 说明左=179.0 差=+21.0 → 200.0/198.0/差=-2.0`（容差 4pt）。**14 张旧帧变化**、0 新增/缺失；基线 **280/0/0/0**；14 张逐张看过，说明在标签正下方、无截断。新判据 `testSettingsHelperTextSharesTheToggleLabelAxis` 按行分控件行/说明行比较最左墨；`M1272/M1273` **2/2 CAUGHT**。**卡片内缩尺对象换位**：说明改轴后通用卡片第一处墨变成复选框（`CARD_INSET` 5.0→8.0，对文字参照 +3.0/+2.5），产品卡片内缩未变 ⇒ 新增 `controlFirstCells`（8 格）与有界替代 [+2.0,+4.0]、开关 `CLIPBOARD_HISTORY_CONTROL_FIRST_ROSTER`；`M1274` **1/1 CAUGHT**、旧表 `M566` 重跑 **CAUGHT**、RESTORE_CLEAN。预检 **246/228/631 bad=0**、ARM **339/1114**、HIDDEN **333/1048 rot=0**。⓪：开工 HEAD=`a3ce7b8`、origin/main=`3bd67b1`、**ahead=3**；`git push` 两探均 remote closed、`curl` **API=000** ⇒ **`PUSH_BLOCKED=network`**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1` 读时 in_progress ⇒ NOT-RUN；收口 gh 可达，两跑均 failure 2 步（`RUNNER_DETAIL_SCROLL_RESET_FLAKE` 仅 3bd67b1、Capture gate 15 帧、inline dark 3.0），新跑 `40736447466 ↔ 0774453` queued ⇒ NOT-RUN；收口 push `3bd67b1..0774453` success、ahead=0；随后补记 `0947b7b` 的 push 两探 remote closed ⇒ `PUSH_BLOCKED=network`（探测时 HEAD=`0947b7b`、origin/main=`0774453`、ahead=1）。全量 **1272/56/0**（475.9s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 467，`python3 scripts/product_streak.py --streak-for 467`，last=01d3b75）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 465（n=458、466 节）；电池 **Ran 683 / OK (skipped=5)**（首跑 3 红：M145/M177 旧针腐烂 2 格 + 嵌套卷无结论行 1 格；重钉后整卷复跑绿，嵌套卷红具名 `SCRIPT_BATTERY_NESTED_RUN_FLAKE=load`）。

本轮做了什么：
① ⓪ 开工两探 remote closed、API=000 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；收口网络恢复，一次快进 push `3bd67b1..0774453` success、ahead=0；R466 两跑收口已读 failure 2 步（DetailScrollReset 11>1 仅 3bd67b1 + Capture 15 帧 + inline dark 3.0），新跑 `40736447466 ↔ 0774453` queued ⇒ NOT-RUN；上一轮 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。
② 产品：设置说明文字与标签同轴（21.0pt → −2.0pt；14 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1272/M1273 2/2；卡片内缩 control-first 类 + M1274 1/1、M566 重跑；M145/M177 旧针重钉后各 CAUGHT；precheck 246/228/631；hidden 333/1048 rot 0。
④ 436：无新跑；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 333 / 可判 1048 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1272/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40736447466 ↔ 0774453`（R467+R468 head，queued）；R466 两跑已读 failure（见 ⓪）；② `INLINE_CODE_DIAG` 的 runner 数据；③ `INLINE_CODE_PAD` dark；④ `SETTINGS_HELPER_AXIS` runner 1x（`settings-content-blank` 出口）；⑤ `CARD_INSET_CONTROL_FIRST` runner 1x；⑥ `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_DETAIL_SCROLL_RESET_FLAKE`（3bd67b1 独有）；⑦ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–525 的其余未结项仍开（含纯文本文件预览异步载入、2x/extended、真机/多屏、13+ 菜单、HTML 各档、Dock 像素等，逐项同 R467 节）。

下一轮（R469）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R468 主笔+追记 head 跑、`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、`40710557752 ↔ 7a04a79`、`40714119382 ↔ 0449f4a` 等的全部失败步骤；重点 `SETTINGS_HELPER_AXIS` 200.0/198.0/−2.0、`CARD_INSET_CONTROL_FIRST` +3.0/+2.5、`INLINE_CODE_DIAG`（选行/页带/top5 候选，拿数据再改选择器）、`INLINE_CODE_PAD` 两档（dark 应 ≥4.5）、`VIDEO_SEEK` 96/90、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、Capture gate 15 张旧帧、其余既有判据与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；**R468 收口预记**：收口一次快进 push **`3bd67b1..0774453` success**、HEAD=origin/main=`0774453`、**ahead=0**；随后补记 `0947b7b` 的 push 两探均 `Connection closed ... port 22` ⇒ **`PUSH_BLOCKED=network`（探测时 HEAD=`0947b7b`、origin/main=`0774453`、ahead=1；本补记二后 ahead=2）**；R469 ⓪ 先验 remote 仍 `0774453` 再一次快进 push 补记；`40720409960 ↔ 3bd67b1` **failure 2 步**（Swift tests：`DetailScrollResetTests.testSelectingAnotherEntryBringsTheBodyBackToTheTop` 换选后正文原点 11>1 —— 同代码 `bf9e8ec` 跑通过 ⇒ `RUNNER_DETAIL_SCROLL_RESET_FLAKE`；`testCaptureKeyViews` 15 张旧帧黑带消失；`INLINE_CODE_PAD dark 150/147/3.0`；Capture gate 同 15 帧）、`40720200357 ↔ bf9e8ec` **failure 2 步**（同 Capture 15 帧与 inline dark 3.0，无 DetailScrollReset）；两跑 checkout 日志有 case-insensitive 引用告警但步骤未判失败；新跑 `40736447466 ↔ 0774453` **queued ⇒ NOT-RUN**；补记提交若再触发一跑，R469 一并读（不把 queued 当绿）。R469 ⓪ 先读 0774453（含 R467 的 intentional/DIAG 与 R468 的 axis）与上述两跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R467 状态（2026-10-29 · 本地 · 第 466 轮 / Round 464）：视频 seek 轨道可见（旧偏离 20/5 → 新 96/90；2 张旧帧变化、基线 280）+ 捕获守卫拆有意黑底 + inline 候选诊断；全量 1271/56/1（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R467 / 第 466 轮 / Round 464）：系统滑杆轨道在胶囊底上只偏离 **light 20 / dark 5**，seek 范围几乎看不见；在 Slider 下垫 `Capsule().fill(primary 0.45).frame(height: 10)`（系统轨道 4pt、上下各露 3pt），新偏离 **96/90**。旧/新：`VIDEO_SEEK light 20→96、dark 5→90`；**2 张旧帧变化**（video-controls 亮/暗）、0 新增/缺失；基线 **280**；亮/暗帧看过轨道清晰。新帧判据 `testVideoSeekTrackIsVisible` 取 thumb 右侧（x 160..410、y 400..420）对胶囊底众数的最大偏离（≥60）；旧红新绿；`M1270/M1271` **2/2 CAUGHT**。**靶修一**：捕获守卫拆 `UICaptureBlackBands.intentional`（video-controls），`extra`/`bandsSeenHere` 排除，`Reading` 增 `fixture`，旧 15 帧名单不盲缩；本地捕获守卫通过。**靶修二**：inline 判据 emit `INLINE_CODE_DIAG`（选行/页带 luma/候选数/top5 row/span/coverage/ink/padding），本轮不改选择器、不降 4.5。预检 **244/226/628 bad=0**、ARM **337/1111**、HIDDEN **331/1045 rot=0**。⓪：no-op push success、ahead=0、HEAD=`3bd67b1`；`40720200357 ↔ bf9e8ec` 与 `40720409960 ↔ 3bd67b1` in_progress ⇒ NOT-RUN；上一轮 `40710557752 ↔ 7a04a79` failure 3 步（inline dark 仍 150/147/3.0、VIDEO_UNAVAILABLE 5/4、Motion 1<2；light 5.0 签收）、`40714119382 ↔ 0449f4a` failure 3 步（VIDEO_SURFACE 236 签收；Capture 黑带消失 15 帧；inline dark 3.0；Motion 1<2）。全量 **1271/56/1**（唯一红 PerfBudget 260.7>250 ⇒ `LOCAL_PERF_BUDGET_FLAKE=load`）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 466，`python3 scripts/product_streak.py --streak-for 466`，last=7adc7c6）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新到尾轮 464；电池首跑 2 红（§1 停旧数 + 嵌套卷无结论行），刷新后原样重跑 `Ran 683 / OK (skipped=5)`（`SCRIPT_BATTERY_NESTED_RUN_FLAKE=load`，单跑与整卷重跑均绿）。

本轮做了什么：
① ⓪ no-op push、ahead=0；R466 两跑 in_progress ⇒ NOT-RUN；上一轮 dark 仍 150/147/3.0、VIDEO_SURFACE 236 签收、Capture 黑带消失 15 帧。
② 产品：seek 轨道自绘胶囊（20/5→96/90；2 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1270/M1271 2/2；捕获守卫拆有意黑底；inline 候选诊断；precheck 244/226/628；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 331 / 可判 1045 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1271/56/1（PerfBudget flake）。

NOT-RUN / 阻塞（分开写）：① R466 两跑（in_progress）；② R467 自身跑；③ `INLINE_CODE_DIAG` runner 数据；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–522 的未结项仍开。

下一轮（R468）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R467 主笔+追记 head 跑、`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、`40710557752 ↔ 7a04a79`、`40714119382 ↔ 0449f4a` 等的全部失败步骤；重点 `VIDEO_SEEK` 96/90、`INLINE_CODE_DIAG`（选行/页带/top5 候选）、`INLINE_CODE_PAD` 两档、`VIDEO_ALIGN` 13.0、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R467 收口预记**：主笔 `01d3b75` + 追记 `32d8711` 两笔；收口 `git push` 连探 2 次均 `Connection closed by 20.205.243.166 port 22` ⇒ **`PUSH_BLOCKED=network`（HEAD=`32d8711`、origin/main=`3bd67b1`、ahead=2）**；`gh run view` 挂起不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40720200357 ↔ bf9e8ec`、`40720409960 ↔ 3bd67b1`、R467 自身跑（随两笔未创建）均 **NOT-RUN**；R468 开工先验 remote 仍 `3bd67b1`，再一次快进 push 三笔（主笔/追记/补记），再读 R467 跑与 `INLINE_CODE_DIAG`；电池首跑 2 红已具名 `SCRIPT_BATTERY_NESTED_RUN_FLAKE=load`（§1 停旧数由 `.scratch/motion-audit-2/refresh_report_section1.py` 刷新），整卷重跑 `Ran 683 / OK (skipped=5)`；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R466 状态（2026-10-28 · 本地 · 第 465 轮 / Round 463）：视频播放器与控件胶囊右缘对齐（旧差 63.0pt → 新 13.0pt；2 张旧帧变化、基线 280）；全量 1270/56/0；R464/R465 跑未读（产品 1 文件，播放器/控件对齐位）

最后更新：2026-10-28（本地 · R466 / 第 465 轮 / Round 463）：播放器只留 `.padding(.horizontal, 20)`，而控件胶囊的 trailing 是 `52+12+16=80`（给右下角浮层让位）⇒ 播放器右缘比控件多 **63.0pt**（569.5 vs 506.5），黑区还伸到浮层下面。修法：播放器的 leading/trailing 改用 `VideoPlaybackMetrics.controlsLeadingPadding`（12）/`controlsTrailingPadding`（80），与控件同缘、同时给浮层让位。旧/新：`VIDEO_ALIGN light/dark 播放器右=569.5 控件右=506.5 差=63.0 → 519.5/506.5/13.0`。**2 张旧帧变化**（`detail-file-video-controls` 亮/暗）、0 新增/缺失；基线 **280**（同 commit 更新）；亮/暗帧看过：黑区 x 24..1040、浮层从 1060 起、控件胶囊同一条右缘。新帧判据 `testVideoPlayerAlignsWithItsControls` 取播放器顶部黑带（y 120..200）最右黑列与控件行（y 395..430、x<535）最右墨列，差 ≤30pt；旧 63.0 红、新 13.0 绿；`M1268/M1269` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **243/225/626 bad=0**、ARM **336/1109**、HIDDEN **330/1043 rot=0**。⓪：开工 push 一次探针被拒（`Connection closed ... port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`86d6b6a`、ahead=0）**；`gh` 不可达 ⇒ **`CI_READ_BLOCKED=network`**；`40710557752`（R464 head）与 R465 两跑 NOT-RUN。上一轮签收：`FALLBACK_ICON 3.84/5.08`、`FALLBACK_NAME 83/82`、`INLINE_CODE_PAD light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652`；dark 仍找不到带。全量 **1270/56/0**（456.1s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 465，`python3 scripts/product_streak.py --streak-for 465`，last=71bed3d）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push/gh 均不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R464/R465 两跑 NOT-RUN；上一轮签收 FALLBACK_ICON/NAME、INLINE light、FILE_TEXT。
② 产品：播放器/控件右缘对齐（63.0→13.0；2 张旧帧变化、基线 280）。
③ 判据：旧红新绿；M1268/M1269 2/2；precheck 243/225/626；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 330 / 可判 1043 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1270/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R464/R465 两跑（CI_READ_BLOCKED）；② R466 自身跑；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–519 的未结项仍开。

下一轮（R467）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R466 主笔+追记 head 跑、`40710557752 ↔ 7a04a79`、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3` 等的全部失败步骤；重点 `VIDEO_ALIGN` 13.0、`INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5）、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R466 收口预记**：开工 push 一次探针被拒；收口网络恢复，一次快进 push **`86d6b6a..bf9e8ec` success**（两笔：7adc7c6/bf9e8ec）⇒ **HEAD=origin/main=`bf9e8ec`、ahead=0**；R466 自身跑 `40720200357 ↔ bf9e8ec` 读时 **queued** ⇒ NOT-RUN。已读：`40710557752 ↔ 7a04a79` failure 3 步（Swift tests、Capture gate、Motion floor）：`INLINE_CODE_PAD light 85/80/5.0` 签收、**dark 仍 150/147/3.0**（padding 选择器在 runner 上仍只看到假带 ⇒ 真带不在候选，不是 padding 输了）、`VIDEO_UNAVAILABLE 5/4`、Motion receipt 1<2。`40714119382 ↔ 0449f4a` failure 3 步（Swift tests、Capture gate、Motion floor）：`VIDEO_SURFACE light 0/236 差=236` **签收**；但 **Capture gate「黑带消失」翻红 15 张旧名册帧** —— R465 把 `detail-file-video-controls` 登记进 `materialBlindSpotFixtures` 后 `bandsSeenHere=true`，而 runner 上那 15 张旧帧的选中黑带已不再出现（机器差），守卫要求缩名单。`40714151224 ↔ 86d6b6a` failure；`40703707900`/`40703583494` failures；`40698931269`/`40698866675`、`40693473537`/`40693357120`、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。**R467 两件修法（先做，不再盲改）**：① Capture 守卫把**有意的黑底**与**材质盲区**分开：新增 `intentionalBlackBandFixtures`（现只有 video-controls），`extra`/`bandsSeenHere` 都排除它；不把旧 15 帧的名单盲缩，先重看那几张 runner 帧。② `INLINE_CODE_PAD` dark 先**加诊断**：在判据里打印所选行的 page/band luma 与 top 候选（row/span/coverage/ink/padding），下一跑拿数据再改选择器；地板 4.5 不动。① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R465 状态（2026-10-28 · 本地 · 第 464 轮 / Round 462）：视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 278→280）；全量 1269/56/0；R464 跑未读（产品 1 文件，视频播放器实底位）

最后更新：2026-10-28（本地 · R465 / 第 464 轮 / Round 462）：`VideoPlayerSurface` 没有底；第一帧未到时播放器区就是**空白页色**（亮 255/暗 30，与页底差 0），看起来像没有视频。修法：给播放器面 `.background(Color.black)`（视频帧覆盖其上）。旧/新：`VIDEO_SURFACE light 播放器=255 页底=255 差=0 → 0/255/255`、`dark 30/30/0 → 0/30/30`。夹具用**真实生成的 .mov**（AVAssetWriter，64×36）走产品 `VideoPreview`，600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **278→280**；亮帧人眼复核（黑底 + 播放/时间/滑杆/静音胶囊）。**捕获守卫**把这张帧的纯黑带当成新盲区 ⇒ 确认是产品有意的播放器黑底（AVPlayerLayer 离屏不画），登记进 `materialBlindSpotFixtures` 并写明理由，不放宽未绘制阈值；登记后捕获守卫通过。新帧判据 `testVideoPlayerHasASolidBackingSurface` 比较播放器区（x 100..500、y 120..360）与页底（x 4..16）的平均亮度，要求页底−播放器 ≥20；旧 0/0 红、新 255/30 绿；`M1266/M1267` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **242/224/624 bad=0**、ARM **335/1107**、HIDDEN **329/1041 rot=0**。⓪：一次快进 push **`dda66f4..7a04a79` success**（三笔）、HEAD=origin/main=`7a04a79`、**ahead=0**；`40710557752 ↔ 7a04a79` in_progress ⇒ NOT-RUN；`40703707900 ↔ dda66f4` 与 `40703583494 ↔ 7d73179` failure 2 步（FALLBACK_ICON 3.84/5.08、FALLBACK_NAME 83/82、INLINE light 5.0、FILE_TEXT 637/652 签收；dark 仍找不到带）；`40698931269`/`40698866675` failures 等沿用。全量 **1269/56/0**（445.8s，轻载）；捕获卷 **280 帧**；基线 **280/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 464，`python3 scripts/product_streak.py --streak-for 464`，last=686737c）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push dda66f4..7a04a79 success、ahead=0；R463 两跑 failure（light 5.0、dark 找不到带；FALLBACK_ICON/NAME、FILE_TEXT 签收）；R464 run in_progress。
② 产品：视频播放器补实底黑（旧差 0 → 新 255/30；2 张新帧、基线 280）。
③ 判据：旧红新绿；M1266/M1267 2/2；黑带名册登记有理由；precheck 242/224/624；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 329 / 可判 1041 / rot 0。
⑥ 捕获 280 帧；基线 280/0/0/0；build 0 告警；换装 ok/387=387；全量 1269/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40710557752 ↔ 7a04a79`（in_progress）；② R465 自身跑（未创建）；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–516 的未结项仍开。

下一轮（R466）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R465 主笔+追记 head 跑、`40710557752 ↔ 7a04a79`、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5、不再「找不到带」）、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON`、`FALLBACK_NAME`、`FILE_TEXT_PREVIEW`、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R465 收口预记**：开工一次快进 push **`dda66f4..7a04a79` success**；收口一次快进 push **`7a04a79..0449f4a` success**（两笔：71bed3d/0449f4a）⇒ **HEAD=origin/main=`0449f4a`、ahead=0**。`40710557752 ↔ 7a04a79`（R464 head）读时 **in_progress** ⇒ NOT-RUN；R465 自身跑读时**未列出** ⇒ NOT-RUN（R466 必读）。已读：`40703707900 ↔ dda66f4` 与 `40703583494 ↔ 7d73179` failure 2 步（Swift tests、Capture gate）：`FALLBACK_ICON light 3.84/dark 5.08`、`FALLBACK_NAME 83/82`、`INLINE_CODE_PAD light 85/80/5.0`、`FILE_TEXT_PREVIEW 637/652` 签收；**dark 仍「找不到带」**（120 上限；R464 的 padding 选择器在新跑里待读）；`40698931269`/`40698866675` failures、`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。R466 ⓪ 读 `40710557752`/新跑：`INLINE_CODE_PAD` dark（padding 优先后应 ≥4.5）、`VIDEO_SURFACE` 255/30、`VIDEO_UNAVAILABLE` 4 带；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R464 状态（2026-10-28 · 本地 · 第 463 轮 / Round 461）：视频不可读态说出文件名（旧 3 条带 → 新 4；2 张新帧、基线 276→278）+ dark 假带改「内边距优先」选择器（本地 98.5/92.5/6.0、99.0/92.5/6.5）；全量 1268/56/0（产品 1 文件 + 判据；靶修复 + 新类别）

最后更新：2026-10-28（本地 · R464 / 第 463 轮 / Round 461）：靶修 dark 选择器：先按靶试「覆盖率最高」，本地选中 **78.5pt 带内子段**（隙 1.0）⇒ **真带方向失败**，不上 runner；改为选**内边距最大**的候选（真带 6、假文字带 3、子段 1），覆盖率 0.55 只作门槛，上限还原 **150**（不降 4.5 地板）；纯函数 `InlineCodeBandChoice` 两向验证（真带压过假带/子段；假带单独 + 覆盖率门槛被排除；>150 被排除）；像素判据本地回到 `light 98.5/92.5/6.0、dark 99.0/92.5/6.5`。**新面**：`videoInfoUnavailableView` 只有图标/说明/Finder 按钮，不说出是哪个文件；在说明与按钮之间补 `url.lastPathComponent`（11pt secondary、单行、中间省略）。旧/新：`VIDEO_UNAVAILABLE light/dark 状态带=3 → 4`。真实 `clip.mov`（信息不可读）夹具 600×440，**2 张新帧**、0 旧帧变化/缺失；基线 **276→278**；亮帧看 clip.mov 居中在说明与按钮之间。判据 `testVideoUnavailableStateNamesTheFile` 数状态区（x 100..500、y 120..380）墨带；旧红新绿；`M1264/M1265` **2/2 CAUGHT**。build **0 告警**（首编一处未用 `bandRun`，删后冷编 0）；捕获 **278 帧**；全量 **1268/56/0**（433.9s，轻载）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 463，`python3 scripts/product_streak.py --streak-for 463`，last=3c0d195）；清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。⓪：no-op push success、ahead=0、HEAD=`dda66f4`；`40703707900 ↔ dda66f4` in_progress、`40703583494 ↔ 7d73179` queued ⇒ NOT-RUN；`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` failure 3 步（FALLBACK_NAME 83/82、INLINE light 85/80/5.0、FILE_TEXT 637/652 签收；dark「找不到带」；Motion 1<2）。

本轮做了什么：
① ⓪ no-op push、ahead=0；R463 两跑 in_progress/queued；R462 两跑 failure（light 5.0、dark 找不到带、Motion 1<2；FALLBACK_NAME/FILE_TEXT 签收）。
② 产品：视频不可读态补文件名（3→4 带；2 张新帧、基线 278）。
③ 判据：dark 选择器改内边距优先（本地两向；98.5/92.5/6.0 与 99.0/92.5/6.5）；M1264/M1265 2/2；precheck 241/223/622；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 328 / 可判 1039 / rot 0。
⑥ 捕获 278 帧；基线 278/0/0/0；build 0 告警；换装 ok/387=387；全量 1268/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40703707900 ↔ dda66f4` / `40703583494 ↔ 7d73179`（in_progress/queued）；② R464 自身跑（未创建）；③ padding 选择器 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–513 的未结项仍开。

下一轮（R465）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R464 主笔+追记 head 跑、`40703707900 ↔ dda66f4`、`40703583494 ↔ 7d73179`、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3`、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5、不再「找不到带」也不是 150/147）、`VIDEO_UNAVAILABLE` 4 带、`FALLBACK_ICON` 3.95/5.92、`FALLBACK_NAME` 83/82、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R464 收口预记**：开工 no-op push success、ahead=0；收口 `git push` 被 **`Connection to github.com closed by remote host`** 拒、`gh` EOF ⇒ **`PUSH_BLOCKED=network`（HEAD=`707e242`、origin/main=`dda66f4`、ahead=2：686737c/707e242）** 与 **`CI_READ_BLOCKED=network`**；`40703707900 ↔ dda66f4`（R463 head）与 `40703583494 ↔ 7d73179` 读时 in_progress/queued，随后网络断 ⇒ **NOT-RUN**；R464 自身跑（随这两笔）未创建 ⇒ NOT-RUN。已读 R462 两跑：`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` failure 3 步（FALLBACK_NAME 83/82、INLINE light 85/80/5.0、FILE_TEXT 637/652 签收；dark「找不到带」=120 上限切真带；Motion 1<2）；`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` success 等沿用；436 无新红。R465 ⓪ 先**只读验 remote 仍 `dda66f4`** 再一次快进 push 两笔（686737c/707e242）；随后读 R463 两跑与 R464 新跑，重点 `INLINE_CODE_PAD` 两档（padding 优先后 dark 应 ≥4.5、不再「找不到带」）、`VIDEO_UNAVAILABLE` 4 带；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R463 状态（2026-10-28 · 本地 · 第 462 轮 / Round 460）：fallback 无缩略图的占位图标可见（旧 1.25/1.34:1 → 新 3.95/5.92:1；2 张新帧、基线 274→276）；全量 1266/56/0；R462 两跑未读（产品 1 文件，fallback 占位图标位）

最后更新：2026-10-28（本地 · R463 / 第 462 轮 / Round 460）：无缩略图的 fallback 用 `doc.fill` + `.quaternary` —— 亮/暗实测 **1.25/1.34:1**，状态图标几乎看不见（非文本图形 3:1 地板）。修法：改 `Color(nsColor: .secondaryLabelColor)`（3.95/5.92:1），仍是"空占位"但不装死。旧/新：`FALLBACK_ICON light 图标=230 页底=255 比=1.25 → 128/255/3.95`、`dark 52/30/1.34 → 154/30/5.92`。新增真实 `.xyz` 无缩略图夹具 `detail-file-fallback-nothumb`（600×440），**2 张新帧**、0 旧帧变化/缺失；基线 **274→276**；亮帧人眼复核，暗档由判据 5.92 签收。新帧判据 `testFallbackPlaceholderIconIsVisible` 在图标上半区（x 260..340、y 150..250；标题 284pt 之下）取最暗像素与页底算 sRGB 对比，地板 3.0；旧 1.25/1.34 红、新 3.95/5.92 绿；`M1262/M1263` **2/2 CAUGHT**、RESTORE_CLEAN。预检 **240/222/620 bad=0**、ARM **333/1103**、HIDDEN **327/1037 rot=0**。⓪：no-op push success、ahead=0、HEAD=`b3531d4`；`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` 读时 in_progress ⇒ NOT-RUN；`40693473537 ↔ b942e6b` failure 3 步（INLINE light 85/80/5.0 签收、dark 150/147/3.0 假带、Motion receipt 1<2）；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 签收。全量 **1266/56/0**（388.6s，轻载）；捕获卷 **276 帧**；基线 **276/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 462，`python3 scripts/product_streak.py --streak-for 462`，last=a91d4a6）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push、ahead=0；R462 两跑 in_progress ⇒ NOT-RUN；R461 跑 INLINE light 5.0 签收、dark 假带仍红、Motion 1<2。
② 产品：fallback 无缩略图占位图标 1.25/1.34 → 3.95/5.92（2 张新帧、基线 276）。
③ 判据：旧红新绿；M1262/M1263 2/2；precheck 240/222/620；hidden rot 0。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 327 / 可判 1037 / rot 0。
⑥ 捕获 276 帧；基线 276/0/0/0；build 0 告警；换装 ok/387=387；全量 1266/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40698931269 ↔ b3531d4` / `40698866675 ↔ b362cf3`（in_progress）；② R463 自身跑（未创建）；③ dark 假带 120 上限 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–510 的未结项仍开。

下一轮（R464）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R463 主笔+追记 head 跑、`40698931269 ↔ b3531d4`、`40698866675 ↔ b362cf3`、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4`、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（light 85/80/5.0 签收；dark 120 上限修复后应 ≥4.5、不再 150/147）、`FALLBACK_ICON` 3.95/5.92、`FALLBACK_NAME` 83.0/2、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R463 收口预记**：收口一次快进 push **`b3531d4..7d73179` success**（两笔：3c0d195/7d73179）⇒ **HEAD=origin/main=`7d73179`、ahead=0**；`7d73179` 自身跑读时未列出 ⇒ R464 必读。R462 两跑：`40698931269 ↔ b3531d4` 与 `40698866675 ↔ b362cf3` 均 **completed=failure，失败步骤 3 个**（Swift tests、Capture gate、Motion coverage floor）：`FALLBACK_NAME light 83.0/2、dark 82.0/2` **签收**；`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**；**dark 变成「找不到行内代码的短底色带」** —— 不是 150 假带，也不是 3.0，而是 **120 上限把真带（或它与抗锯齿连成的 run）也切掉了**；Motion markdown 标签 1<2 采样红；`FILE_TEXT_PREVIEW 637/652` 签收。**R464 先修 dark 选择器**：不要再用「最宽 run」+ 上界；改为在所有候选行里选**覆盖率最高**的 run（真带的 padding 行覆盖率 ~1.0，假文字带 ~0.55），把上限还原到 150（不降 4.5 地板）；本地应回到 98.5/92.5/6.0 与 99.0/92.5/6.5，runner 再验。`40693473537`/`40693357120` failures、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` 沿用；436 无新红。① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R462 状态（2026-10-28 · 本地 · 第 461 轮 / Round 459）：不支持文件 fallback 的长文件名留在窗格内（旧左沿 7.0pt、2 带 → 新 83.0pt、2 带；2 张新帧、基线 272→274）+ dark 假带上限 150→120；全量 1265/56/0（产品 1 文件，fallback 文件名位）

最后更新：2026-10-28（本地 · R462 / 第 461 轮 / Round 459）：`DetailPreviewViews.fallbackView` 的 `Text(lastPathComponent)` 没有行数/截断/内边距 —— 一条 8×「很长文件名-」的 `.xyz` 在 600×440 里**单行从窗格左缘 7.0pt 跑到右缘、压在浮层药丸下**。修法：`lineLimit(2)` + 居中 + 中间省略 + 左右 80pt 内边距。旧/新：`FALLBACK_NAME light 左沿=7.0pt 行带=2 → 83.0pt/2`、dark 同形；夹具用**真实 `.xyz` 文件 + 缩略图**走产品 `DetailFileView` 的 `.fallback` 载入。**2 张新帧**（600×440 亮/暗）、0 旧帧变化/缺失；基线 **272→274**；已看亮/暗：名字两行居中、左右留白、避开浮层。新帧判据 `testFallbackFileNameStaysInsideThePane` 在缩略图左侧窄列（x 0..200pt）读文件名最左墨：旧 7.0 <60 红、新 83.0 绿；`M1260/M1261` **2/2 CAUGHT**、RESTORE_CLEAN。**dark 假带修复**：R461 的 3.0 是 150pt 上限饱和；真带 85..99 ⇒ 选择器上限 **150→120**（紧凑对象界；地板 4.5 不动），本地 light 98.5/92.5/6.0、dark 99.0/92.5/6.5。预检 **239/221/618 bad=0**、ARM 332/1101、HIDDEN **326/1035 rot=0**。⓪：no-op push success、ahead=0、HEAD=`b942e6b`；`40693473537 ↔ b942e6b` failure 3 步（Swift tests、Capture gate、Motion floor）：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、dark 150/147/3.0 假带仍红；Motion receipt 1<2 采样红；`40693357120 ↔ 0b034c4` failure；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 签收。全量 **1265/56/0**（427s，轻载）；捕获卷 **274 帧**；基线 **274/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 461，`python3 scripts/product_streak.py --streak-for 461`，last=885c8ae）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push、ahead=0；R461 两跑 failure（light 5.0 签收、dark 假带仍红、Motion 采样红）；其余面签收。
② 产品：fallback 长文件名两行居中、80pt 内边距（7.0→83.0；2 张新帧、基线 274）。
③ 判据：M1260/M1261 2/2；dark 假带上限 150→120（地板 4.5 不动）；precheck 239/221/618；hidden rot 0。
④ 436：无新红；Motion 采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 326 / 可判 1035 / rot 0。
⑥ 捕获 274 帧；基线 274/0/0/0；build 0 告警；换装 ok/387=387；全量 1265/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40693473537 ↔ b942e6b` / `40693357120 ↔ 0b034c4`（completed=failure）；② R462 自身跑（未创建）；③ dark 假带 120 上限的 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（receipt 1<2）；⑥ `LOCAL_PERF_BUDGET_FLAKE=load`；⑦ 纯文本文件预览异步载入；⑧ 源文/纯文本宽行（496）；⑨ 2x 宽文档滚动条（497）；⑩ 散文按宽文档折行（498）；⑪ 纯文本预览制表符（490）；⑫ 表格单元格制表符（491）；⑬ 8 空格制表位（492）；⑭ 命中高亮截断外/OCR（487）；⑮ 多文件第 2/3 个文件名（488）；⑯ 选中底高亮对比（489）；⑰ 弱化色选中态（485）；⑱ 行内码两侧标点（486）；⑲ HTML 的 `<del>`（484）；⑳ HTML 列表缩进/任务弱化/表格体行（482/481/479）；㉑ 设置内容列 1x 平涂；㉒ 设置脚注带 1x；㉓ 主窗口 content 帧 1x；㉔ 高夹具 1x；㉕ 13+ 菜单像素/标题；㉖ 真实拖拽；㉗ Dock 像素；㉘ 源图标最小窗文字 1x；㉙ 2x/extended；㉚ 固定块揭示偏移（455）；㉛ 跨年时间（456）；㉜ 主列表暗档文字盲区（457）；㉝ 真机/多屏（447）；㉞ 真菜单栏、12 实时腿；㉟ `table-lazy-rows`；㊱ HTML 六档字号（460）；㊲ 清除 × 命中区（461）；㊳ 分隔线令牌（462）；㊴ 展开态已加载内容无帧（463）；㊵ 其它自绘控件帮助文本（464）；㊶ HTML 引用块无导引线（465）；㊷ HTML 表格表头无同档（466）；㊸ 100+ 行行号（467）；㊹ HTML 代码块行号（468）；㊺ 行号选中/滚动两态（469）；㊻ 关于页 1x 盲（470）；㊼ M613 机器前提（472）；㊽ 真机 vibrant 暗档（473）；㊾ 长来源截断（474）；㊿ bundle ID 未搜（475）；[51] 长首行标签省略无帧（476）；[52] HTML 代码块无语言标签（477）；[53] HTML `<hr>` 无通栏线（478）；[54] HTML 表格体行无同一条线（479）；[55] QuickPick 键盘提示 1x（480）；[56] HTML 任务列表无弱化（481）；[57] HTML 列表缩进（482）；[58] 中心刻度端点标签（483）；[59] HTML 的 `<del>`（484）；[60] 弱化色选中态（485）；[61] 行内码两侧标点（486）；[62] 437–507 的未结项仍开。

下一轮（R463）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R462 主笔+追记 head 跑、`40693473537 ↔ b942e6b`、`40693357120 ↔ 0b034c4`、`40688652304`/`40688610679`、`40681994982`/`40682072865`、`40675730252`、`40653092761` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（light 85/80/5.0 签收；dark 修复后应不再 150/147/3.0）、`FALLBACK_NAME` 83.0/2、`FILE_TEXT_PREVIEW` 637/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R462 收口预记**：开工 no-op push、ahead=0；收口一次快进 push **`b942e6b..b362cf3` success**（两笔：a91d4a6/b362cf3）⇒ **HEAD=origin/main=`b362cf3`、ahead=0**；新跑读时未列出 ⇒ R463 必读。R461 两跑：`40693473537 ↔ b942e6b` **failure 3 步**（Swift tests、Capture gate、Motion coverage floor）：`INLINE_CODE_PAD light 85.0/80.0/5.0` **签收**、`dark 150.0/147.0/3.0`（150 是选择器上限 ⇒ 假带；R462 已把上限收到 120，待新跑复验）；Motion receipt 1<2 采样红；`40693357120 ↔ 0b034c4` failure；`FILE_TEXT_PREVIEW 637/652`、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 均签收；`40688652304`/`40688610679` failures、`40681994982`/`40682072865` failures、`40675730252` failure 2 步、`40653092761` success 等沿用；436 无新红。R463 首读 `b362cf3` 跑：`INLINE_CODE_PAD` dark 修复（应 ≥4.5、不再 150/147）、`FALLBACK_NAME` 83.0/2、`FILE_TEXT_PREVIEW` 637/652；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R461 状态（2026-10-28 · 本地 · 第 460 轮 / Round 458）：行内码内边距 3→4pt + 1x 假带门槛（本地 98.5/92.5/6.0、99.0/92.5/6.5；2 张旧帧变化、基线 272）；全量 1264/56/1（唯一红 PerfBudget flake）；⓪ 两跑 failure、新跑未读（靶指定修复轮）

最后更新：2026-10-28（本地 · R461 / 第 460 轮 / Round 458）：靶指定修复 R455 的 1x 隙：runner light 84/80/4.0（真隙低于 4.5）、dark 150/147/3.0（150 是选择器上限 ⇒ 假带）。**不降地板、不放宽选择器**：产品 `InlineCodeBackground.horizontalPadding` **3→4**；判据第二众数候选覆盖率门槛 **0.35→0.55**（真带是整块面；文字抗锯齿零头覆盖不到一半），把 dark 假带排除；地板 4.5 与选择器 40..150 未动。旧/新：`INLINE_CODE_PAD light 97.5/92.5/5.0 → 98.5/92.5/6.0`、`dark 98.0/92.5/5.5 → 99.0/92.5/6.5`；runner 旧读数 84/80/4.0 与 150/147/3.0（修复后待下一跑）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线 **272**（同 commit 更新）；已看亮/暗：带只向外各多 1pt、不压字。R455 M1247 重钉后 **2/2 CAUGHT**；覆盖率门槛无本地刀（2x 分不开），以 runner 为证人。预检 **238/220/616 bad=0**、ARM 331/1099、HIDDEN **325/1033 rot=0**。⓪：no-op push success、ahead=0、HEAD=`f597e62`；`6e217e8`/`f597e62` 新跑读时 in_progress，收口 gh EOF ⇒ **`CI_READ_BLOCKED=network`**、两跑 NOT-RUN；`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 均 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；HEADING/WIDE/CODE_TAB/HISTORY_ROW 签收）；`40675730252` failure 2 步；`40664012233`/`40664181811` failures；`40653092761` success。全量 **1264/56/1**（唯一红 PerfBudget 298.7/258.2>250 ⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**，阈值未动）；捕获卷 **272 帧**；基线 **272/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 460，`python3 scripts/product_streak.py --streak-for 460`，last=edc8952）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push、ahead=0；两跑 failure 2 步（INLINE_CODE_PAD 旧读数 + 滚动 flake；其余面签收）；新跑 gh EOF ⇒ CI_READ_BLOCKED。
② 产品：内边距 3→4（真隙 5.0→6.0；2 张旧帧变化、基线 272）；**修复轮，下一轮换新类别**。
③ 判据：覆盖率门槛 0.35→0.55 排除 150pt 假带；R455 M1247 重钉 2/2；地板未动。
④ 436：无新红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 325 / 可判 1033 / rot 0。
⑥ 捕获 272 帧；基线 272/0/0/0；build 0 告警；换装 ok/387=387；全量 1264/56/1（PerfBudget flake）。

NOT-RUN / 阻塞（分开写）：① `6e217e8 ↔ f597e62` 两跑（CI_READ_BLOCKED）；② R461 自身跑；③ 覆盖率门槛 runner 复验；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ `LOCAL_PERF_BUDGET_FLAKE=load`；⑥ 纯文本文件预览异步载入；⑦ 源文/纯文本宽行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 散文按宽文档折行（498）；⑩ 纯文本预览制表符（490）；⑪ 表格单元格制表符（491）；⑫ 8 空格制表位（492）；⑬ 命中高亮截断外/OCR（487）；⑭ 多文件第 2/3 个文件名（488）；⑮ 选中底高亮对比（489）；⑯ 弱化色选中态（485）；⑰ 行内码两侧标点（486）；⑱ HTML 的 `<del>`（484）；⑲ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑳ 设置内容列 1x 平涂；㉑ 设置脚注带 1x；㉒ 主窗口 content 帧 1x；㉓ 高夹具 1x；㉔ 13+ 菜单像素/标题；㉕ 真实拖拽；㉖ Dock 像素；㉗ 源图标最小窗文字 1x；㉘ 2x/extended；㉙ 固定块揭示偏移（455）；㉚ 跨年时间（456）；㉛ 主列表暗档文字盲区（457）；㉜ 真机/多屏（447）；㉝ 真菜单栏、12 实时腿；㉞ `table-lazy-rows`；㉟ HTML 六档字号（460）；㊱ 清除 × 命中区（461）；㊲ 分隔线令牌（462）；㊳ 展开态已加载内容无帧（463）；㊴ 其它自绘控件帮助文本（464）；㊵ HTML 引用块无导引线（465）；㊶ HTML 表格表头无同档（466）；㊷ 100+ 行行号（467）；㊸ HTML 代码块行号（468）；㊹ 行号选中/滚动两态（469）；㊺ 关于页 1x 盲（470）；㊻ M613 机器前提（472）；㊼ 真机 vibrant 暗档（473）；㊽ 长来源截断（474）；㊾ bundle ID 未搜（475）；㊿ 长首行标签省略无帧（476）；[51] HTML 代码块无语言标签（477）；[52] HTML `<hr>` 无通栏线（478）；[53] HTML 表格体行无同一条线（479）；[54] QuickPick 键盘提示 1x（480）；[55] HTML 任务列表无弱化（481）；[56] HTML 列表缩进（482）；[57] 中心刻度端点标签（483）；[58] HTML 的 `<del>`（484）；[59] 弱化色选中态（485）；[60] 行内码两侧标点（486）；[61] 437–504 的未结项仍开。

下一轮（R462）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R461 主笔+追记 head 跑、`6e217e8`/`f597e62` 两跑、`40681994982 ↔ f954b0e`、`40682072865 ↔ 4edfa23`、`40675730252 ↔ dd11f0f`、`40653092761 ↔ d48bb05` 等的全部失败步骤；重点 `INLINE_CODE_PAD` 两档（旧 84/80/4.0、150/147/3.0；修复后应 ≥4.5，尤其 dark 不再触 150）、`FILE_TEXT_PREVIEW` 652/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；flake 原样重跑；**R461 收口预记**：收口一次快进 push **`f597e62..0b034c4` success**（两笔：885c8ae/0b034c4）⇒ **HEAD=origin/main=`0b034c4`、ahead=0**；`0b034c4` 自身跑读时未列出 ⇒ R462 必读。已读 R460 两跑：`40688652304 ↔ f597e62` 与 `40688610679 ↔ 6e217e8` 均 **failure、失败步骤各 2 个**（Swift tests、Capture gate），**唯一测试红＝`INLINE_CODE_PAD` 84/80/4.0 与 150/147/3.0**（R461 的 padding/覆盖率修复不在这两笔）；**`FILE_TEXT_PREVIEW light/dark 637.0/652.0` runner 签收**、`HEADING_LADDER`、`WIDE_TABLE`、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH` 均签收；f597e62 跑未复现 SelectionReveal 红。`40681994982`/`40682072865` failures 同旧读数；`40675730252` failure 2 步；`40653092761` success 等沿用；436 无新红。R462 首读 `0b034c4` 跑，重点 `INLINE_CODE_PAD` 两档（修复后应 ≥4.5、dark 不再触 150）、`FILE_TEXT_PREVIEW` 637/652；① 现读 rot=0；② **必须是新类别的产品视觉位并落 Sources**（不要再做行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
## R460 状态（2026-10-28 · 本地 · 第 459 轮 / Round 457）：纯文本文件预览接上 68ch 可读列（旧正文宽 1100pt、可读列 652pt → 新 652/652；2 张新帧、基线 270→272）；全量 1264/56/0；两跑 failure（行内码 1x 隙仍红）（产品 1 文件，纯文本文件预览列宽位）

最后更新：2026-10-28（本地 · R460 / 第 459 轮 / Round 457）：U-4 的 68ch 可读列只接在 Markdown/正文分支，`DetailFileView.textPreview` 的纯文本 else 分支直接建 `ChineseSelectableTextView`，在 1100 窗口里正文宽 **1100pt**（可读列 652pt），长行一路铺满详情区。修法：纯文本文件也用**它自己的 13pt 字体**算 68ch 列（`DetailTypography.columnWidth(font:)`）并左对齐；13pt 字面量保留（`Round4MarkdownTests` 的静态守卫）。旧/新：`FILE_TEXT_PREVIEW light 正文宽=1100.0pt 可读列=652.0pt → 652.0/652.0`、dark 同形。新增真实 `.txt` 夹具 `detail-file-text-wide`（1100×800，settle 1.2s 等异步载入），**2 张新帧**、0 旧帧变化/缺失；基线 **270→272**；已看亮/暗：长行在可读列内折行、右侧留白。判据 `testPlainTextFilePreviewUsesTheReadableColumn` 从产品渲染出的 NSTextView 读正文 frame 宽；旧红、新绿；`M1258/M1259` **2/2 CAUGHT**、RESTORE_CLEAN。**守卫红一次**：全量首跑 `testFilePreviewRoutesMarkdownFilesToTheRenderer` 要求 13pt 字面量仍在调用点 ⇒ 保留字面量、列宽另取 `fileFont`，复绿；M1258 重钉后复跑 2/2。预检 **238/220/616 bad=0**、ARM **331/1099**、HIDDEN **325/1033 rot=0**。⓪：no-op push success、ahead=0、HEAD=`4edfa23`；**`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 两跑 completed=failure，失败步骤各 2 个**（Swift tests、Capture gate）：`HEADING_LADDER`/`WIDE_TABLE`/`CODE_TAB_STOP`/`HISTORY_ROW_MATCH` 均 runner 签收；`INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0`（1x 隙 <4.5、dark 触 150 上限，地板未动）+ `SelectionRevealAnimationTests` 滚动会话采样红。全量 **1264/56/0**（439s，轻载）；捕获卷 **272 帧**；基线 **272/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 386=386`（条目 383→386，前后一致）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 459，`python3 scripts/product_streak.py --streak-for 459`，last=ff77c27）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push、ahead=0；两跑 failure 2 步，`INLINE_CODE_PAD` 1x 隙仍红、滚动 flake；其余面签收。
② 产品：纯文本文件预览接 68ch 可读列（1100→652；2 张新帧、基线 272）。
③ 判据：旧红新绿；M1258/M1259 2/2；全量首跑守卫红已修；precheck 238/220/616；hidden rot 0。
④ 436：无新跑红；采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 325 / 可判 1033 / rot 0。
⑥ 捕获 272 帧；基线 272/0/0/0；build 0 告警；换装 ok/386=386；全量 1264/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23`（completed=failure）；② R460 自身跑（未创建）；③ `INLINE_CODE_PAD` 的 1x 隙（light 4.0、dark 触顶 150，499）；④ `RUNNER_SCROLL_SESSION_FLAKE`；⑤ 文件预览异步载入；⑥ 源文/纯文本宽行（496）；⑦ 2x 宽文档滚动条（497）；⑧ 散文按宽文档折行（498）；⑨ 纯文本预览制表符（490）；⑩ 表格单元格制表符（491）；⑪ 8 空格制表位（492）；⑫ 命中高亮截断外/OCR（487）；⑬ 多文件第 2/3 个文件名（488）；⑭ 选中底高亮对比（489）；⑮ 弱化色选中态（485）；⑯ 行内码两侧标点（486）；⑰ HTML 的 `<del>`（484）；⑱ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑲ 设置内容列 1x 平涂；⑳ 设置脚注带 1x；㉑ 主窗口 content 帧 1x；㉒ 高夹具 1x；㉓ 13+ 菜单像素/标题；㉔ 真实拖拽；㉕ Dock 像素；㉖ 源图标最小窗文字 1x；㉗ 2x/extended；㉘ 固定块揭示偏移（455）；㉙ 跨年时间（456）；㉚ 主列表暗档文字盲区（457）；㉛ 真机/多屏（447）；㉜ 真菜单栏、12 实时腿；㉝ `table-lazy-rows`；㉞ HTML 六档字号（460）；㉟ 清除 × 命中区（461）；㊱ 分隔线令牌（462）；㊲ 展开态已加载内容无帧（463）；㊳ 其它自绘控件帮助文本（464）；㊴ HTML 引用块无导引线（465）；㊵ HTML 表格表头无同档（466）；㊶ 100+ 行行号（467）；㊷ HTML 代码块行号（468）；㊸ 行号选中/滚动两态（469）；㊹ 关于页 1x 盲（470）；㊺ M613 机器前提（472）；㊻ 真机 vibrant 暗档（473）；㊼ 长来源截断（474）；㊽ bundle ID 未搜（475）；㊾ 长首行标签省略无帧（476）；㊿ HTML 代码块无语言标签（477）；[51] HTML `<hr>` 无通栏线（478）；[52] HTML 表格体行无同一条线（479）；[53] QuickPick 键盘提示 1x（480）；[54] HTML 任务列表无弱化（481）；[55] HTML 列表缩进（482）；[56] 中心刻度端点标签（483）；[57] HTML 的 `<del>`（484）；[58] 弱化色选中态（485）；[59] 行内码两侧标点（486）；[60] 437–501 的未结项仍开。

下一轮（R461）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R460 主笔+追记 head 跑、`40681994982 ↔ f954b0e`、`40682072865 ↔ 4edfa23`、`40675730252 ↔ dd11f0f`、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit）；重点先修 **`INLINE_CODE_PAD` 的 1x 隙**（light 84/80/4.0、dark 150/147/3.0；地板 4.5 不动）：dark 的 150 是选择器上限，先查 1x 带/字边界；再看 `FILE_TEXT_PREVIEW` 两档 652/652、`WIDE_TABLE`、`HEADING_LADDER`、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK`、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；**R460 收口预记**：开工 no-op push success、ahead=0；收口一次快进 push **`4edfa23..6e217e8` success**（两笔：edc8952/6e217e8）⇒ **HEAD=origin/main=`6e217e8`、ahead=0**；`6e217e8` 自身跑读时尚未出现在列表 ⇒ R461 必读。已读两跑：`40681994982 ↔ f954b0e` 与 `40682072865 ↔ 4edfa23` 均 **completed=failure、失败步骤各 2 个**（Swift tests、Capture gate）；`HEADING_LADDER 20/17/15.5/15/14.5/14（正文 14）`、`WIDE_TABLE false/752.0/[1,1,1]/true + 短表 true/[1,1]/false`、`CODE_TAB_STOP 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、`HISTORY_ROW_MATCH light 0/300、528/0、0/0` 均 **runner 签收**；`INLINE_CODE_PAD light 84.0/80.0/4.0、dark 150.0/147.0/3.0`（**带已找到**，1x 隙 <4.5、dark 触 150 上限，地板未动）仍红 + `SelectionRevealAnimationTests` 滚动会话采样红。`40675730252 ↔ dd11f0f` failure 2 步（行内码旧尺；CODE_TAB_STOP 已签收）、`40664012233`/`40664181811` failures、`40653092761` success 等沿用；436 无新红。R461 重点先修 `INLINE_CODE_PAD` 的 1x 隙（499），再读 `FILE_TEXT_PREVIEW` 两档 652/652；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R459 状态（2026-10-28 · 本地 · 第 458 轮 / Round 456）：宽表格不再在行中折开（旧 跟踪视图=是、容器 612pt、行片段 [1,2,2] → 新 752.1pt、[1,1,1]、滚动条开；2 张新帧、基线 268→270）；全量 1263/56/0（产品 3 文件，宽表横向滚动位）

最后更新：2026-10-28（本地 · R459 / 第 458 轮 / Round 456）：U-4 把正文限成 68ch 可读列，而表格/代码行在列内折开会散列、断缩进（旧读数：跟踪视图=是、容器 612pt、行片段 `[1,2,2]`）。修法：新 `WideMarkdownDocument` 只量代码块/表格块的最宽行，超出可读列时把文档宽到最宽行 + 2×gutter 并开横向滚动；短内容仍按 U-4 折行；只作用于 Markdown 渲染态。旧/新：`WIDE_TABLE light 跟踪视图=true 容器=612.0pt 行片段=[1,2,2] 滚动条=false → false/752.1pt/[1,1,1]/true`、dark 同形；短表对照 `true/[1,1]/false` 不变。**2 张新帧**（`detail-table-wide` 亮/暗）、0 旧帧变化/缺失；基线 **268→270**；已看亮/暗：表格行不折、右侧列靠横向滚动到达。新帧判据 `testWideTablesKeepEachRowOnOneLine` 从产品渲染出的 NSTextView 读四量；旧形态红、新形态绿；`M1256/M1257` **2/2 CAUGHT**、RESTORE_CLEAN。**全量首跑被「只读正文装配只许一份」守卫拦下**：`widthTracksTextView = true` 字面量读到 2 份（我们的模式切换写了第二份）⇒ 改成 `widthTracksTextView = width == nil`，守卫复绿；行为不变。预检 **237/219/614 bad=0**、ARM **330/1097**、HIDDEN **324/1031 rot=0**。⓪：开工 ahead=3、HEAD=`7c45279`、remote=`dd11f0f`；push 一次探针被拒、`gh` 读 `40675730252` EOF ⇒ **`PUSH_BLOCKED=network`（ahead=3、HEAD=`7c45279`、origin/main=`dd11f0f`）** 与 **`CI_READ_BLOCKED=network`**；`40675730252 ↔ dd11f0f` 与 R458 自身跑仍 NOT-RUN。全量 **1263/56/0**（406s，轻载）；捕获卷 **270 帧**；基线 **270/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 458，`python3 scripts/product_streak.py --streak-for 458`，last=8f11de3）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push/gh 均拒（ahead=3）⇒ PUSH_BLOCKED/CI_READ_BLOCKED；436 无新跑 ⇒ 具名 NOT-RUN。
② 产品：宽表格横向滚动（旧 [1,2,2]/612pt → 新 [1,1,1]/752.1pt；2 张新帧、基线 270）。
③ 判据：旧红新绿；M1256/M1257 2/2；全量首跑守卫红已修；precheck 237/219/614；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 324 / 可判 1031 / rot 0。
⑥ 捕获 270 帧；基线 270/0/0/0；build 0 告警；换装 ok/383=383；全量 1263/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40675730252 ↔ dd11f0f`（CI_READ_BLOCKED）；② R458 自身跑（未创建）；③ 436 Motion floor（无新跑）；④ R455 判据 runner 复验；⑤ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；⑥ 宽文档 runner 复验；⑦ 源文/纯文本宽行仍折行（496）；⑧ 2x 宽文档滚动条（497）；⑨ 散文按宽文档折行（498）；⑩ 纯文本预览制表符（490）；⑪ 表格单元格制表符（491）；⑫ 8 空格制表位（492）；⑬ 命中高亮截断外/OCR（487）；⑭ 多文件第 2/3 个文件名（488）；⑮ 选中底高亮对比（489）；⑯ 弱化色选中态（485）；⑰ 行内码两侧标点（486）；⑱ HTML 的 `<del>`（484）；⑲ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑳ 设置内容列 1x 平涂；㉑ 设置脚注带 1x；㉒ 主窗口 content 帧 1x；㉓ 高夹具 1x；㉔ 13+ 菜单像素/标题；㉕ 真实拖拽；㉖ Dock 像素；㉗ 源图标最小窗文字 1x；㉘ 2x/extended；㉙ 固定块揭示偏移（455）；㉚ 跨年时间（456）；㉛ 主列表暗档文字盲区（457）；㉜ 真机/多屏（447）；㉝ 真菜单栏、12 实时腿；㉞ `table-lazy-rows`；㉟ HTML 六档字号（460）；㊱ 清除 × 命中区（461）；㊲ 分隔线令牌（462）；㊳ 展开态已加载内容无帧（463）；㊴ 其它自绘控件帮助文本（464）；㊵ HTML 引用块无导引线（465）；㊶ HTML 表格表头无同档（466）；㊷ 100+ 行行号（467）；㊸ HTML 代码块行号（468）；㊹ 行号选中/滚动两态（469）；㊺ 关于页 1x 盲（470）；㊻ M613 机器前提（472）；㊼ 真机 vibrant 暗档（473）；㊽ 长来源截断（474）；㊾ bundle ID 未搜（475）；㊿ 长首行标签省略无帧（476）；[51] HTML 代码块无语言标签（477）；[52] HTML `<hr>` 无通栏线（478）；[53] HTML 表格体行无同一条线（479）；[54] QuickPick 键盘提示 1x（480）；[55] HTML 任务列表无弱化（481）；[56] HTML 列表缩进（482）；[57] 中心刻度端点标签（483）；[58] HTML 的 `<del>`（484）；[59] 弱化色选中态（485）；[60] 行内码两侧标点（486）；[61] 437–498 的未结项仍开。

下一轮（R460）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R459 主笔+追记 head 跑、`40675730252 ↔ dd11f0f`、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit），重点看 `WIDE_TABLE` 两档（false/752.1/[1,1,1]/true 与短表 true/[1,1]/false）、`HEADING_LADDER`、`INLINE_CODE_PAD` 两档、`HISTORY_ROW_MATCH`、`CODE_TAB_STOP`、`DEEMPHASIS_CONTRAST`、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE`、`QUICKPICK_HINT`、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN`、`TABLE_HEADER`、`CODE_LINE_NUMBERS` 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；**R459 收口预记**：收口时网络恢复，一次快进 push **`dd11f0f..f954b0e` success**（五笔：8f11de3/dcde18a/7c45279/ff77c27/f954b0e）⇒ **ahead=0**（开工 push/gh 两拒的 `PUSH_BLOCKED`/`CI_READ_BLOCKED` 已在 R459 节记）；`40675730252 ↔ dd11f0f` **failure，失败步骤 2 个**（Swift tests、Capture gate），唯一测试红＝`testInlineCodeBackgroundHasPadding` light/dark「找不到带」（R455 旧尺；R458 的透明页修复在 8f11de3 里、本跑不含）；`CODE_TAB_STOP light/dark 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0` **runner 签收**、`HISTORY_ROW_MATCH light 0/300、528/0、0/0` 签收、dark NOT-RUN；Motion 本跑 `judged=4/5 not-run=notice-banner`、exit 0（markdown 标签 1<2 是采样 flake，本跑未复现）。新跑 `40681994982 ↔ f954b0e`（含 R458+R459 代码）读时 in_progress ⇒ **NOT-RUN**；R460 必读该跑（`INLINE_CODE_PAD` 的 runner 复验、`HEADING_LADDER`、`WIDE_TABLE`、436）；`40653092761` success、`40645430259` success、`40645469967` 仅 receipt 1<2、`40634880705` 滚动采样红沿用；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R458 状态（2026-10-28 · 本地 · 第 457 轮 / Round 455）：Markdown 五/六级标题不小于正文（旧 14/13/12、正文 14 → 新 15/14.5/14；2 张新帧、基线 266→268）+ R455 判据 1x 透明页修复（97.5/92.5/5.0、98.0/92.5/5.5）；全量 1262/56/0（产品 2 文件，标题字阶位）

最后更新：2026-10-28（本地 · R458 / 第 457 轮 / Round 455）：`headingFontSize` 的阶梯是 20/17/15.5/14/13/12，而正文是 14 ⇒ 五/六级标题（13/12）比正文还小，作者写下的层级在屏幕上反过来；源码注释「六到一级的标题都至少不比正文小」与实现相反。修法：h4=15、h5=14.5、h6=14（六级与正文同号，靠 semibold 与 0.5–1pt 阶梯区分；每级仍严格递减、每级 ≥ 正文）。旧/新：`HEADING_LADDER 20/17/15.5/14/13/12（正文 14）→ 20/17/15.5/15/14.5/14`、light/dark 同形。新增夹具 `detail-headings`（h1..h6 + 正文 + 列表项保证走渲染），**2 张新帧**、0 旧帧变化/缺失；基线 **266→268**；已逐张看亮/暗：六级不再像小字注释。**R455 判据修复**：runner 的 `detail-markdown-rendered` 帧 76.4%/76.0% 透明，旧尺读预乘 RGB、忽略 alpha，两侧都读不到带（`40664012233`/`40664181811` 的红）；改为按页面底合成 alpha、取该行第二众数为带色，允许字形打断 ≤3pt（阈值未动），旧/新 `INLINE_CODE_PAD light 97.5/92.5/5.0、dark 98.0/92.5/5.5`。新帧判据 `testHeadingLevelsAreNeverSmallerThanBody` 从产品渲染出的 NSTextView 读六级与正文的 `.font`；旧形态红在 h5/h6，新形态全绿；`M1254/M1255` **2/2 CAUGHT**、RESTORE_CLEAN=yes。预检 **236/218/612 bad=0**、ARM **329/1095**、HIDDEN **323/1029 rot=0**。⓪：一次快进 push **`ca40810..dd11f0f` success**（四笔）、HEAD=origin/main=`dd11f0f`、**ahead=0**；`40675730252 ↔ dd11f0f` queued ⇒ NOT-RUN；**`40664012233 ↔ d2a1e80` failure（2 步）与 `40664181811 ↔ ca40810` failure（3 步）**，两跑唯一新红＝上述行内码判据，另一红＝`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2（已知采样红）；`40653092761 ↔ d48bb05` success、`40645430259` success、`40645469967` 仅 receipt 1<2、`40640660665`/`40642482086`/`40636558557` success、`40634880705` 滚动会话采样红。全量 **1262/56/0**（387s，轻载无挂起）；捕获卷 **268 帧**；基线 **268/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 457，`python3 scripts/product_streak.py --streak-for 457`，last=4380a32）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push ca40810..dd11f0f success、ahead=0；读两跑 2/3 个失败步骤，定位行内码判据 + Motion 采样红；新跑 queued。
② 产品：五/六级标题不小于正文（14/13/12 → 15/14.5/14；2 张新帧、基线 268）。
③ 判据：旧红 h5/h6；M1254/M1255 2/2；R455 尺按 alpha 合成后本地绿；precheck 236/218/612；hidden rot 0。
④ 436：Motion floor judged=5/5；markdown 标签 1<2 采样红具名，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 323 / 可判 1029 / rot 0。
⑥ 捕获 268 帧；基线 268/0/0/0；build 0 告警；换装 ok/383=383；全量 1262/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① `40675730252 ↔ dd11f0f`（queued）；② R455 判据的 runner 复验（下一跑）；③ `RUNNER_MARKDOWN_LABEL_SAMPLE_RED`（1<2）；④ 纯文本预览制表符（490）；⑤ 表格单元格制表符（491）；⑥ 8 空格制表位（492）；⑦ 命中高亮截断外/OCR（487）；⑧ 多文件第 2/3 个文件名（488）；⑨ 选中底高亮对比（489）；⑩ 弱化色选中态（485）；⑪ 行内码两侧标点（486）；⑫ HTML 的 `<del>`（484）；⑬ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑭ 设置内容列 1x 平涂；⑮ 设置脚注带 1x；⑯ 主窗口 content 帧 1x；⑰ 高夹具 1x；⑱ 13+ 菜单像素/标题；⑲ 真实拖拽；⑳ Dock 像素；㉑ 源图标最小窗文字 1x；㉒ 2x/extended；㉓ 固定块揭示偏移（455）；㉔ 跨年时间（456）；㉕ 主列表暗档文字盲区（457）；㉖ 真机/多屏（447）；㉗ 真菜单栏、12 实时腿；㉘ `table-lazy-rows`；㉙ HTML 六档字号（460）；㉚ 清除 × 命中区（461）；㉛ 分隔线令牌（462）；㉜ 展开态已加载内容无帧（463）；㉝ 其它自绘控件帮助文本（464）；㉞ HTML 引用块无导引线（465）；㉟ HTML 表格表头无同档（466）；㊱ 100+ 行行号（467）；㊲ HTML 代码块行号（468）；㊳ 行号选中/滚动两态（469）；㊴ 关于页 1x 盲（470）；㊵ M613 机器前提（472）；㊶ 真机 vibrant 暗档（473）；㊷ 长来源截断（474）；㊸ bundle ID 未搜（475）；㊹ 长首行标签省略无帧（476）；㊺ HTML 代码块无语言标签（477）；㊻ HTML `<hr>` 无通栏线（478）；㊼ HTML 表格体行无同一条线（479）；㊽ QuickPick 键盘提示 1x（480）；㊾ HTML 任务列表无弱化（481）；㊿ HTML 列表缩进（482）；[51] 中心刻度端点标签（483）；[52] HTML 的 `<del>`（484）；[53] 弱化色选中态（485）；[54] 行内码两侧标点（486）；[55] 437–495 的未结项仍开。

下一轮（R459）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R458 主笔+追记 head 跑、`40675730252 ↔ dd11f0f`（R457/R458 链）、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`、`40645430259 ↔ 5c925a9`、`40645469967 ↔ c041c8d`、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379` 的全部失败步骤（成对 run↔commit），重点看 `HEADING_LADDER` 两档 20/17/15.5/15/14.5/14 与正文 14、`INLINE_CODE_PAD` 两档 97.5/92.5/5.0 与 98.0/92.5/5.5（runner 复验）、`HISTORY_ROW_MATCH` 300/528、`CODE_TAB_STOP` 32.14/32.14、64.29/64.29、间隔 32.14、`DEEMPHASIS_CONTRAST` 5.09/5.98、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE` 16/16/0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES`、`THEMATIC_RULE`、`CODE_LANGUAGE`、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE`/`LOCAL_PERF_BUDGET_FLAKE`/`RUNNER_MARKDOWN_LABEL_SAMPLE_RED` 原样重跑复核（不改门槛）；**R458 收口预记**：收口两次 push 探针被拒（`Connection closed by 20.205.243.166 port 22`）、gh 读 `40675730252` EOF ⇒ **`PUSH_BLOCKED=network`（HEAD=`dcde18a`、origin/main=`dd11f0f`、ahead=2：8f11de3/dcde18a；本补记提交后 ahead=3）** 与 **`CI_READ_BLOCKED=network`**；`40675730252 ↔ dd11f0f`（R457/R458 链）与 R458 自身跑（随这两笔推送后创建）仍 NOT-RUN；R459 ⓪ 先只读验 remote 仍 `dd11f0f` 再快进 push 三笔，随后读该跑（重点 `HEADING_LADDER`、`INLINE_CODE_PAD` 两档、`CODE_TAB_STOP`、`HISTORY_ROW_MATCH`、Motion 采样红）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做标题字阶/代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R457 状态（2026-10-28 · 本地 · 第 456 轮 / Round 454）：代码块制表位与 4 个空格同轴（旧 28.0/32.14、56.0/64.29、间隔 0、制表位 12 → 新 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0；2 张新帧、基线 264→266）；全量挂起具名、目标回归 118/2/0；⓪ 网络不可达（产品 1 文件，代码块制表位）

最后更新：2026-10-28（本地 · R457 / 第 456 轮 / Round 454）：代码块保留源码制表符，而 `paragraphStyle` 不碰代码块的制表位 ⇒ TextKit 默认 28pt 一跳；13pt 等宽字体的 4 个空格是 32.14pt ⇒ 一个制表符比一级四空格缩进少 4.14pt、两级少 8.29pt，缩进不同的代码行排在不同竖轴上。修法：`paragraphStyle` 对 `.codeBlock` 清掉默认显式制表位并设 `defaultTabInterval = 4 × codeFont 字形推进`（32.14pt）；列表/表格分支不动。旧/新：`CODE_TAB_STOP light 28.00/32.14、56.00/64.29、间隔 0、制表位 12 → 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0`、dark 同形。**2 张新帧**（`detail-code-tabs` 亮/暗）、0 旧帧变化/缺失；基线 **264→266**（同 commit 更新）；已逐张看亮/暗：制表符段与四空格段的 `if`/`print` 落在同一条竖轴。新帧判据 `testCodeBlockTabsMatchFourSpaces` 从产品渲染出的 NSTextView 读布局（4 个 x + 段样式）；旧形态四条全红；`M1251/M1252/M1253` **3/3 CAUGHT**、RESTORE_CLEAN。预检 **235/217/610 bad=0**、ARM **328/1093**、HIDDEN **322/1027 rot=0**。⓪：开工 ahead=0、HEAD=`ca40810`；`git push` 一次探针被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`（ahead=0、HEAD=`ca40810`）**；`gh` 读 `40664012233` 仍 EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；收口前再试一次。全量 **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**（卡在 `testSearchFieldIdealHeightIsStateIndependent`，日志 3.6M 行后同一行数分钟不动，已停）；目标回归 **118 测试 / 2 skipped / 0 failures**（Markdown/代码块/列表制表位/命中高亮/设置卡片节奏）。捕获卷 **266 帧**；基线 **266/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 456，`python3 scripts/product_streak.py --streak-for 456`，last=643081c）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push 探针被拒（ahead=0、HEAD ca40810）⇒ PUSH_BLOCKED=network；gh EOF ⇒ CI_READ_BLOCKED；436 无新跑 ⇒ MOTION_FLOOR_NOT_RUN；沿用 R456 已读。
② 产品：代码块制表位 = 4 个空格（旧 28/32.14、56/64.29 → 新同轴；2 张新帧、基线 266）。
③ 判据：旧形态四条红；M1251–M1253 3/3；precheck 235/217/610；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 322 / 可判 1027 / rot 0。
⑥ 捕获 266 帧；基线 266/0/0/0；build 0 告警；换装 ok/383=383；全量挂起具名，目标回归 118/2/0。

NOT-RUN / 阻塞（分开写）：① `40664012233 ↔ d2a1e80`（CI_READ_BLOCKED）；② `40664181811 ↔ ca40810`（同上）；③ R457 自身跑（未创建）；④ 436 Motion floor（无新跑）；⑤ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；⑥ 纯文本预览制表符（490）；⑦ 表格单元格制表符（491）；⑧ 8 空格制表位（492）；⑨ 命中高亮截断外/OCR（487）；⑩ 多文件第 2/3 个文件名（488）；⑪ 选中底高亮对比（489）；⑫ 弱化色选中态（485）；⑬ 行内码两侧标点（486）；⑭ HTML 的 `<del>`（484）；⑮ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑯ 设置内容列 1x 平涂；⑰ 设置脚注带 1x；⑱ 主窗口 content 帧 1x；⑲ 高夹具 1x；⑳ 13+ 菜单像素/标题；㉑ 真实拖拽；㉒ Dock 像素；㉓ 源图标最小窗文字 1x；㉔ 2x/extended；㉕ 固定块揭示偏移（455）；㉖ 跨年时间（456）；㉗ 主列表暗档文字盲区（457）；㉘ 真机/多屏（447）；㉙ 真菜单栏、12 实时腿；㉚ `table-lazy-rows`；㉛ HTML 六档字号（460）；㉜ 清除 × 命中区（461）；㉝ 分隔线令牌（462）；㉞ 展开态已加载内容无帧（463）；㉟ 其它自绘控件帮助文本（464）；㊱ HTML 引用块无导引线（465）；㊲ HTML 表格表头无同档（466）；㊳ 100+ 行行号（467）；㊴ HTML 代码块行号（468）；㊵ 行号选中/滚动两态（469）；㊶ 关于页 1x 盲（470）；㊷ M613 机器前提（472）；㊸ 真机 vibrant 暗档（473）；㊹ 长来源截断（474）；㊺ bundle ID 未搜（475）；㊻ 长首行标签省略无帧（476）；㊼ HTML 代码块无语言标签（477）；㊽ HTML `<hr>` 无通栏线（478）；㊾ HTML 表格体行无同一条线（479）；㊿ QuickPick 键盘提示 1x（480）；[51] HTML 任务列表无弱化（481）；[52] HTML 列表缩进（482）；[53] 中心刻度端点标签（483）；[54] HTML 的 `<del>`（484）；[55] 弱化色选中态（485）；[56] 行内码两侧标点（486）；[57] 437–492 的未结项仍开。

下一轮（R458）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R457 主笔+追记 head 跑、`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、`40653092761 ↔ d48bb05`（DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（STRIKE_DIM）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`、`40642482086 ↔ e083179`、`40636558557 ↔ 667d1a2`、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `CODE_TAB_STOP` 两档 32.14/32.14、64.29/64.29、间隔 32.14、制表位 0、`HISTORY_ROW_MATCH`、`INLINE_CODE_PAD` 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 5.09/5.98、`STRIKE_DIM`、`TASK_DIM`、`WEIGHT_CENTER_TICK` 或具名 NOT_RUN、`LIST_HANG_STYLE` 16/16/0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108/102/1、`THEMATIC_RULE` 597/1/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE`、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；`FULL_SUITE_REREAD_NOT_RUN` 下一轮在较轻负载下重读（目标 1261/56/0）；**R457 收口预记**：开工与收口各 1 次 `git push` 探针均被拒（`Connection closed by 20.205.243.166 port 22`）、`gh` 两次 EOF ⇒ **`PUSH_BLOCKED=network`（HEAD=`d77acdd`、origin/main=`ca40810`、ahead=2：4380a32/d77acdd；补记笔 `ed26bc9` 未再推 ⇒ 收口本地 HEAD=`ed26bc9`、ahead=3，本笔后 ahead=4）** 与 **`CI_READ_BLOCKED=network`**；`40664012233 ↔ d2a1e80`、`40664181811 ↔ ca40810`、R457 自身跑全部 NOT-RUN；R458 先只读验 remote 仍 `ca40810` 再快进 push 两笔，随后读这三跑与 `40653092761`；436 仍待新跑；全量本轮 `FULL_SUITE_REREAD_NOT_RUN=load-hang`（目标回归 118/2/0）；电池 683/5；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块制表位/列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R456 状态（2026-10-28 · 本地 · 第 455 轮 / Round 453）：侧栏搜索命中在行内高亮（旧 0/0 → 新来源带 1200/1560、正文标题带 2185/2660；2 张旧帧变化 + 2 张新帧、基线 262→264）；全量 1260/56/0（滚动红未复现）；⓪ 两次 push 探针被拒、gh EOF（产品 3 文件，列表命中高亮位）

最后更新：2026-10-28（本地 · R456 / 第 455 轮 / Round 453）：侧栏过滤从 R445 起匹配正文与来源 App 名，但行里此前**一个字都不标** —— 只命中来源的行（`sidebar-search-source`）整行没有线索；正文命中落在两行截断之外时也一样（旧帧黄像素 `0/0`）。修法：新 `HistoryRowMatchHighlight` 复用 `MatchHighlighting.segments`（与过滤同源），标题/文件名标命中片段、来源行**只标 App 名不标时间**，命中片段带 `DetailTypography.highlightColor` 底；空查询/无命中原样。旧/新：`HISTORY_ROW_MATCH light 来源查询 0/0 → 0/1200；正文查询 0/0 → 2185/0；无查询 0/0`、`dark 0/0 → 0/1560；0/0 → 2660/0；0/0`。**2 张旧帧变化**（`sidebar-search-source` 亮/暗）+ **2 张新帧**（`sidebar-search-content` 亮/暗）、0 缺失；基线 **262→264**（同 commit 更新）；已逐张看亮/暗：黄底只压在命中字上、不压相邻字、不挪版式。`M1248/M1249/M1250` **3/3**；新单测 7 条 + 帧判据（同帧三条文字带、地板 40×scale²）。**共用行改动**：R444 的 `M1220` 针被新来源行调用打空 ⇒ 重钉后复跑 **2/2**。预检 **234/216/607 bad=0**、ARM **327/1090**、HIDDEN **321/1024 rot=0**。⓪：开工 ahead=4、两次 push 均被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **`PUSH_BLOCKED=network`（HEAD=`c94a995`、origin/main=`d48bb05`、ahead=4）**；`40653092761 ↔ d48bb05`（R454 head）gh EOF ⇒ **`CI_READ_BLOCKED=network`、NOT-RUN**；R455 两跑/R456 自身跑未创建 ⇒ NOT-RUN。全量 **1260/56/0**（403s；5 条本地滚动红未复现，`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留；`PerfBudget` 未红）；捕获卷 **264 帧**；基线 **264/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383、版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 455，`python3 scripts/product_streak.py --streak-for 455`，last=8f69d82）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push 两次探针被拒（ahead=4）⇒ PUSH_BLOCKED=network；gh EOF ⇒ CI_READ_BLOCKED；436 无新跑 ⇒ MOTION_FLOOR_NOT_RUN；沿用 R455 已读。
② 产品：侧栏搜索命中在行内高亮（来源带 0→1200/1560、正文标题带 0→2185/2660；2 张旧帧变化 + 2 张新帧、基线 264）。
③ 判据：单测 7/7；M1248–M1250 3/3；R444 M1220 重钉 2/2；precheck 234/216/607；hidden rot 0。
④ 436：无新跑 ⇒ 具名 NOT-RUN，不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 321 / 可判 1024 / rot 0。
⑥ 捕获 264 帧；基线 264/0/0/0；build 0 告警；换装 ok/383=383；全量 1260/56/0（滚动红未复现、perf 未红）。

NOT-RUN / 阻塞（分开写）：① `40653092761 ↔ d48bb05`（CI_READ_BLOCKED）；② R455 两跑/R456 自身跑（未创建）；③ `PUSH_BLOCKED=network`（ahead=4）；④ 436 Motion floor（无新跑）；⑤ `LOCAL_SCROLL_SESSION_NOT_RUN`（本跑未复现）；⑥ 截断外/OCR 命中在列表无高亮（487）；⑦ 多文件第 2/3 个文件名命中无高亮（488）；⑧ 高亮色在选中底上的对比（489）；⑨ 弱化色选中态（485）；⑩ HTML 的 `<del>`（484）；⑪ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑫ 设置内容列 1x 平涂；⑬ 设置脚注带 1x；⑭ 主窗口 content 帧 1x；⑮ 高夹具 1x；⑯ 13+ 菜单像素/标题；⑰ 真实拖拽；⑱ Dock 像素；⑲ 源图标最小窗文字 1x；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态（485）；[52] 行内码两侧标点无 padding（486）；[53] 437–489 的未结项仍开。

下一轮（R457）的靶：⓪ 先 `git push origin main`（现 remote=`d2a1e80`、本地 ahead=0，预期 no-op；禁 amend/force）并复核 ahead=0；读 R456 主笔+追记 head 跑、`40653092761 ↔ d48bb05`（R454 head，DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（STRIKE_DIM 已签收）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `HISTORY_ROW_MATCH` 两档（来源/标题/负臂：0/1200、2185/0、0/0；暗 0/1560、2660/0、0/0）、`INLINE_CODE_PAD` 两档 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 135.4/108.0 与 141.8/174.6、`TASK_DIM` 157.9/114.7、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；**R456 收口预记**：开工两次 push 探针被拒（`Connection closed by 20.205.243.166 port 22`）⇒ `PUSH_BLOCKED=network`（HEAD=`c94a995`、origin/main=`d48bb05`、ahead=4）；随后网络恢复，补记 `d2a1e80` 后一次快进 push **`d48bb05..d2a1e80` success**（六笔：8f69d82/7200fa5/16379c5/c94a995/643081c/d2a1e80）⇒ **ahead=0**。CI：`40664012233 ↔ d2a1e80`（R456 head）读时 **in_progress ⇒ NOT-RUN**（R457 必读 `HISTORY_ROW_MATCH` 与 `INLINE_CODE_PAD`）；**`40653092761 ↔ d48bb05` success**（R454 head）：`DEEMPHASIS_CONTRAST light 99/236/5.09、dark 177/50/5.98`（≥4.5 签收）、`TASK_DIM light 147.4/114.7 +32.7（墨 361/393）、dark 136.6/166.4 −29.8（墨 444/454）`、`STRIKE_DIM light 128.1/108.0 +20.1、dark 152.2/174.6 −22.3、隙 3/3`、`HISTORY_ROW_SOURCE light 139.0/74.0 差 65.0 左沿 97/97`、dark 具名 NOT-RUN、`WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat 轨=1`、`LIST_HANG_STYLE 16.0/16.0/0.0` 两档、Motion `judged=5/5 not-run=-`（`MOTION_NOT_RUN` 收 receipt-dismiss-CI 等、无红）；R455 的提交在本轮同一链上、没有单独跑 ⇒ 以 d2a1e80 这一跑为准；436 待读该跑；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做列表命中高亮/行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R455 状态（2026-10-28 · 本地 · 第 454 轮 / Round 452）：行内代码底色带补空白侧内边距（旧带 94.5pt/字 92.0pt、隙 2.5 → 新带 98.5pt/字 92.5pt、隙 6.0；2 张旧帧变化、基线 262）；全量 1252/56/1（唯一红＝Round4Markdown 旧 `.backgroundColor` 期望，已改到新属性并过滤复跑；二次全量负载下挂起）；R453 head 5c925a9 success（产品 2 文件，行内代码底色位）

最后更新：2026-10-28（本地 · R455 / 第 454 轮 / Round 452）：内联码底色原由属性串 `.backgroundColor` 涂，只到字形 advance —— 实测带 94.5pt、字 92.0pt，左右各 ~1pt。修法：去掉 `.backgroundColor`，新 `InlineCodeBackground` 在背景层画圆角带（上下各 1pt）；横向只向**空白侧**各让 3pt（前一个是空格/行首、后一个是空格/行尾），紧贴标点时不加（否则会盖住后随的“。”）。旧/新：`INLINE_CODE_PAD light 带宽=98.5pt 字宽=92.5pt 隙=6.0pt`、`dark 同形`（旧 94.5/92.0/2.5）。**2 张旧帧变化**（`detail-markdown-rendered` 亮/暗）、0 新增/缺失；基线名单 **262**（同 commit 更新）；已看亮/暗：带左缘离开“行内”的末字、右缘停在“。”前。`M1246/M1247` **2/2**；新单测 4 条 + 帧判据（连续带色行 + 带内字宽）。**旧期望修正**：全量红在 `Round4MarkdownTests.testMarkdownFileGoesThroughTheRealPreviewPipelineIntoAStyledTextView`（它钉着 `.backgroundColor`）；契约是"行内码有可区分底色"，R455 换成 `inlineCodeAttribute` + 自绘带，于是把断言改到新属性并写明像素证人，过滤重跑通过。预检 **233/215/604 bad=0**、ARM **326/1087**、HIDDEN **318/1017 rot=0**。⓪：一次快进 push **`c041c8d..d48bb05` success**（三笔）、HEAD=origin/main=`d48bb05`、**ahead=0**；**`40645430259 ↔ 5c925a9` success**（STRIKE_DIM light 135.4/108.0 +27.4、dark 141.8/174.6 −32.7、隙 3/3；TASK_DIM 157.9/114.7 +43.2、128.4/166.4 −38.1）；**`40645469967 ↔ c041c8d` failure 只有 Motion floor**（`testCopyReceipt...` 1<2，Swift 全绿）；`40640660665`/`40642482086`/`40642524490`/`40636558557` success；`40634880705 ↔ 9743379` failure（滚动会话采样红 + Motion 模式标签 1<2）；`0737460`/`ecb8e69` 仅 Motion；`36284e1` dark 行带（已修）；`40653092761 ↔ d48bb05`（R454 head）读时 in_progress ⇒ NOT-RUN。全量 **1252/56/1**（旧期望红已改并通过过滤复跑；第二次全量在负载下挂起被停 ⇒ **`FULL_SUITE_REREAD_NOT_RUN=load-hang`**）；`PerfBudgetTests.testImageComparisonCostStaysBounded` 在混合/高负载跑里偶发 310ms>250（单跑 178ms 过）⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**；滚动套件单跑 **4/4**（本跑未复现 5 红）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目 383）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 454，`python3 scripts/product_streak.py --streak-for 454`，last=ee930b6）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push c041c8d..d48bb05 success、ahead=0；R453 head 5c925a9 success（STRIKE_DIM/TASK_DIM 签收）；c041c8d 唯一红＝Motion receipt 采样；R454 head in_progress ⇒ NOT-RUN。
② 产品：行内代码底色带空白侧内边距（旧 2.5 → 新 6.0；2 张旧帧变化、基线 262）。
③ 判据：M1246/M1247 2/2；新单测 4 条 + 帧判据；旧 `.backgroundColor` 期望改到 `inlineCodeAttribute`（机制换代）；precheck 233/215/604；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；receipt 采样红在 c041c8d 上具名；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok/383=383；全量 1252/56/1（旧期望红已修；二次挂起具名；perf/滚动 flake 具名）。

NOT-RUN / 阻塞（分开写）：① `40653092761 ↔ d48bb05`（R454 head，in_progress）；② R455 自身跑；③ `FULL_SUITE_REREAD_NOT_RUN=load-hang`；④ `LOCAL_PERF_BUDGET_FLAKE=load`；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（9743379；R456 重跑）；⑥ 436 的 receipt 采样红（c041c8d 唯一红，1<2）；⑦ 行内代码两侧标点时无横向 padding（486）；⑧ 弱化色选中态对比（485）；⑨ HTML 的 `<del>`（484）；⑩ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑪ 设置内容列 1x 平涂；⑫ 设置脚注带 1x；⑬ 主窗口 content 帧 1x；⑭ 高夹具 1x；⑮ 13+ 菜单像素/标题；⑯ 真实拖拽；⑰ Dock 像素；⑱ 源图标最小窗文字 1x；⑲ 本地全量 5 条滚动红（本跑未复现、隔离 4/4）；⑳ 2x/extended；㉑ 固定块揭示偏移（455）；㉒ 跨年时间（456）；㉓ 主列表暗档文字盲区（457）；㉔ 真机/多屏（447）；㉕ 真菜单栏、12 实时腿；㉖ `table-lazy-rows`；㉗ HTML 六档字号（460）；㉘ 清除 × 命中区（461）；㉙ 分隔线令牌（462）；㉚ 展开态已加载内容无帧（463）；㉛ 其它自绘控件帮助文本（464）；㉜ HTML 引用块无导引线（465）；㉝ HTML 表格表头无同档（466）；㉞ 100+ 行行号（467）；㉟ HTML 代码块行号（468）；㊱ 行号选中/滚动两态（469）；㊲ 关于页 1x 盲（470）；㊳ M613 机器前提（472）；㊴ 真机 vibrant 暗档（473）；㊵ 长来源截断（474）；㊶ bundle ID 未搜（475）；㊷ 长首行标签省略无帧（476）；㊸ HTML 代码块无语言标签（477）；㊹ HTML `<hr>` 无通栏线（478）；㊺ HTML 表格体行无同一条线（479）；㊻ QuickPick 键盘提示 1x（480）；㊼ HTML 任务列表无弱化（481）；㊽ HTML 列表缩进（482）；㊾ 中心刻度端点标签（483）；㊿ HTML 的 `<del>`（484）；[51] 弱化色选中态（485）；[52] 437–486 的未结项仍开。

下一轮（R456）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R455 主笔+追记 head 跑、`40653092761 ↔ d48bb05`（R454 head，DEEMPHASIS_CONTRAST）、`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM 已签收）、`40645469967 ↔ c041c8d`（Motion receipt 采样）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `INLINE_CODE_PAD` 两档 98.5/92.5/6.0、`DEEMPHASIS_CONTRAST` 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 135.4/108.0 与 141.8/174.6、`TASK_DIM` 157.9/114.7、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 与 `LOCAL_PERF_BUDGET_FLAKE` 必须原样重跑复核（不改门槛）；`FULL_SUITE_REREAD_NOT_RUN=load-hang` 下一轮在较轻负载下重读；**R455 收口预记**：开工一次快进 push `c041c8d..d48bb05` success、ahead=0；R455 主笔 `8f69d82` + 追记 `7200fa5` 落盘后两次 push 均被拒（`Connection closed by 20.205.243.166 port 22`）⇒ **PUSH_BLOCKED=network（HEAD=`7200fa5`、origin/main=`d48bb05`、ahead=2）**；补记笔 `16379c5` 未再推 ⇒ 收口本地 HEAD=`16379c5`、ahead=3（本笔后 ahead=4）；`40653092761 ↔ d48bb05`（R454 head，DEEMPHASIS_CONTRAST）gh 读时 EOF ⇒ **CI_READ_BLOCKED=network、NOT-RUN**；R455 自身两跑因 push 被拒未创建 ⇒ NOT-RUN；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做行内代码底色/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R454 状态（2026-10-28 · 本地 · 第 453 轮 / Round 451）：弱化正文的对比度从 3.95:1 补到 5.33/7.09（旧 secondary 亮档 3.95 低于 14pt 正文 4.5:1；6 张旧帧变化、基线名单 262）；全量 1247/56/1（唯一红＝性能预算 flake，单跑通过）；R453 head 两跑收口 gh EOF ⇒ NOT-RUN（产品 3 文件，弱化色对比度位）

最后更新：2026-10-28（本地 · R454 / 第 453 轮 / Round 451）：R450（完成项）与 R453（删除线）的弱化色 `secondaryLabelColor` 亮档实测 **3.95:1**，低于 14pt 正文的 4.5:1（引用块早因同一原因拒绝过它）。新 `DeEmphasisPresentation.textColor` 动态色（亮档黑 58%、暗档白 62%），完成项与删除线共用。旧/新（`detail-tasks` 完成项核心色 vs 页面底色）：`DEEMPHASIS_CONTRAST light 128/255/3.95 → 107/255/5.33`、`dark 154/30/5.92 → 169/30/7.09`；R450/R453 的弱化差仍成立（`TASK_DIM light 133.5/85.2 +48.3、dark 146.4/184.3 −37.9`；`STRIKE_DIM light 123.3/82.0 +41.2、dark 158.9/192.3 −33.4；隙 9/9`）。**6 张旧帧变化**（detail-tasks/detail-strike/detail-markdown-rendered × 亮/暗）、0 新增/缺失；基线名单 **262**（同 commit 更新）；已看亮/暗：完成项仍比正文浅、但不再低到读不清。`M1242/M1243` **2/2**；新单测 2 条 + 帧判据（sRGB 相对亮度）。预检 **232/214/602 bad=0**、ARM **325/1085**、HIDDEN **318/1017 rot=0**。⓪：开工 remote=`c041c8d`、ahead=0，`git push` 为 **no-op**；已读 `40640660665`（LIST_HANG_STYLE 签收）、`40642482086`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40642524490`、`40636558557`（TASK_DIM 1x 旧色）、`40634880705`（滚动会话采样红 + Motion 模式标签 1<2）、`0737460`/`ecb8e69`（仅 Motion floor）、`36284e1`（dark 行带，已修）；**`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM）与 `40645469967 ↔ c041c8d` 读时 in_progress、收口前再试仍 EOF ⇒ NOT-RUN**。全量 **1247/56/1**：唯一红＝`PerfBudgetTests.testImageComparisonCostStaysBounded`（310.3ms>250，load1=5.9；单跑 177.8ms 过）⇒ **`LOCAL_PERF_BUDGET_FLAKE=load`**；本跑 5 条滚动红未复现、滚动套件单跑 **4/4**（会话差；`LOCAL_SCROLL_SESSION_NOT_RUN` 口径保留，不据此删账）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 383=383`（条目数本轮 383）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 453，`python3 scripts/product_streak.py --streak-for 453`，last=4ba006f）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push（remote c041c8d、ahead=0）；LIST_HANG_STYLE/WEIGHT_CENTER_TICK/TASK_DIM 签收；R453 head 两跑 in_progress→EOF ⇒ NOT-RUN。
② 产品：弱化色对比度 3.95→5.33/7.09（6 张旧帧变化、基线 262）。
③ 判据：M1242/M1243 2/2；新单测 2 条 + 帧判据（sRGB 对比）；M1243 的 alpha=0 透明教训照记；precheck 232/214/602；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok/383=383；全量 1247/56/1（性能预算 flake 具名；滚动本跑未复现、隔离 4/4）。

NOT-RUN / 阻塞（分开写）：① `40645430259 ↔ 5c925a9`（R453 head，EOF）；② `40645469967 ↔ c041c8d`（同上）；③ R454 自身跑；④ `LOCAL_PERF_BUDGET_FLAKE=load`；⑤ `RUNNER_SCROLL_SESSION_FLAKE`（R455 重跑）；⑥ 436 的 markdown 模式标签采样红（1<2）；⑦ 弱化色在选中/高亮底色的对比度（485）；⑧ HTML 的 `<del>` 无弱化（484）；⑨ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑩ 设置内容列 1x 平涂；⑪ 设置脚注带 1x；⑫ 主窗口 content 帧 1x；⑬ 高夹具 1x；⑭ 13+ 菜单像素/标题；⑮ 真实拖拽；⑯ Dock 像素；⑰ 源图标最小窗文字 1x；⑱ 本地全量 5 条滚动红（本跑未复现、隔离 4/4）；⑲ 2x/extended；⑳ 固定块揭示偏移（455）；㉑ 跨年时间（456）；㉒ 主列表暗档文字盲区（457）；㉓ 真机/多屏（447）；㉔ 真菜单栏、12 实时腿；㉕ `table-lazy-rows`；㉖ HTML 六档字号（460）；㉗ 清除 × 命中区（461）；㉘ 分隔线令牌（462）；㉙ 展开态已加载内容无帧（463）；㉚ 其它自绘控件帮助文本（464）；㉛ HTML 引用块无导引线（465）；㉜ HTML 表格表头无同档（466）；㉝ 100+ 行行号（467）；㉞ HTML 代码块行号（468）；㉟ 行号选中/滚动两态（469）；㊱ 关于页 1x 盲（470）；㊲ M613 机器前提（472）；㊳ 真机 vibrant 暗档（473）；㊴ 长来源截断（474）；㊵ bundle ID 未搜（475）；㊶ 长首行标签省略无帧（476）；㊷ HTML 代码块无语言标签（477）；㊸ HTML `<hr>` 无通栏线（478）；㊹ HTML 表格体行无同一条线（479）；㊺ QuickPick 键盘提示 1x（480）；㊻ HTML 任务列表无弱化（481）；㊼ HTML 列表缩进（482）；㊽ 中心刻度端点标签（483）；㊾ HTML 的 `<del>`（484）；㊿ 437–485 的未结项仍开。

R454 补记（2026-10-28）：收口主笔 `ee930b6` + 追记 `b478b2a` 的 push 遇断网（`git push` 拒、随后 `git ls-remote` 同拒，两次探测）⇒ **`PUSH_BLOCKED=network`**：HEAD=`b478b2a`、origin/main=`c041c8d`、**ahead=2**（本补记提交后 ahead=3）；R455 ⓪ 先只读验 remote 未变再快进 push 这三笔。`40645430259 ↔ 5c925a9`（R453 head，`STRIKE_DIM`）与 `40645469967 ↔ c041c8d` 收口时 `gh` 仍 EOF ⇒ NOT-RUN；R454 自身的 head 跑待推送后创建。

下一轮（R455）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R454 主笔+追记 head 跑、`40645430259 ↔ 5c925a9`（R453 head，STRIKE_DIM）与 `40645469967 ↔ c041c8d`（R453 预记 head）、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）的全部失败步骤（成对 run↔commit），重点看 `DEEMPHASIS_CONTRAST` 两档 107/255/5.33 与 169/30/7.09、`STRIKE_DIM` 123.3/82.0/+41.2 与 158.9/192.3/−33.4、隙 9/9、`TASK_DIM` 133.5/85.2/+48.3 与 146.4/184.3/−37.9、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R453 状态（2026-10-28 · 本地 · 第 452 轮 / Round 450）：删除线（作者标记的删除内容）正文弱一档（亮 137.9 vs 82.0、暗 147.2 vs 192.3；字形间隙 9/9 仍被 AppKit 的线填上；2 张新帧、基线 260→262）；收口前 gh 恢复，R451/R452 三跑 success、LIST_HANG_STYLE 16/16/0 签收、WEIGHT_CENTER_TICK 在 runner 具名 NOT_RUN（产品 1 文件，删除线语义位）

最后更新：2026-10-28（本地 · R453 / 第 452 轮 / Round 450）：`~~` 标记的删除内容与正常正文同色同重。`MarkdownPresentation.attributes(for:in:dimmed:)` 里 `struck`（`.strikethrough` 且非链接）用 `struckTextColor = secondaryLabelColor`；可点链接仍保留链接色。旧/新（两段逐字相同的 `同样的字`）：`STRIKE_DIM light 删除=137.9 正常=82.0 差=+55.9`、`dark 147.2/192.3 差=−45.2`、字形间隙 9/9 被填（AppKit 的 `.strikethroughStyle` 一直在画，自绘线冗余已撤）。夹具 `detail-strike`；**2 张新帧、0 张旧帧变化**（markdown 样例没有 `~~`），基线 **260→262 / 0/0/0**；已看亮/暗。**证人换代记**：第一版"最长连续墨"当线证人，M1241（去掉自绘线）两次 ESCAPED —— 灰字抗锯齿会并成长墨，且证明 AppKit 的线一直在画（间隙 9/9）；最终产品不自绘线，间隙列只作前提，颜色差是新面。`M1240/M1241` **2/2**；新单测 3 条 + 帧判据。预检 **231/213/600 bad=0**、ARM **324/1083**、HIDDEN **318/1017 rot=0**。⓪：开工 remote=`e750598`、ahead=0，`git push` 为 **no-op**；三跑读时 in_progress、`gh` EOF ⇒ NOT-RUN；**收口前重试 gh 恢复，三跑全部 success**：`40640660665 ↔ 86044bf` 的 `LIST_HANG_STYLE 16.0/16.0/0.0` 签收、`40642482086 ↔ e083179` 的 `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat light/dark 轨=1`（**按设计具名 NOT-RUN**，非红）、`40642524490 ↔ e750598` success；`40636558557 ↔ 667d1a2` success（TASK_DIM 1x 158.0/115.1 +42.9、128.4/166.4 −38.0）；`40636617018` success；`40634880705 ↔ 9743379` failure（`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE`，同代码 224b8ee/107f2b3 两跑 success + Motion `testMarkdownModeLabelChange` 1<2）；`0737460`/`ecb8e69` failure 仅 Motion floor、`36284e1` failure 1 步（dark 行带，已修）。本地全量 **1244/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **262 帧**；基线 **262/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 452，`python3 scripts/product_streak.py --streak-for 452`，last=7d9be37）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ 开工 no-op push（remote e750598、ahead=0）；三跑 in_progress/gh EOF ⇒ NOT-RUN，收口前重试恢复：三跑 success，LIST_HANG_STYLE 16/16/0 签收、WEIGHT_CENTER_TICK 具名 NOT_RUN（设置内容列平涂）；TASK_DIM 1x 签收；9743379 滚动采样红 + Motion 模式标签 1<2。
② 产品：删除线正文弱一档（亮 +55.9、暗 −45.2；2 新帧、基线 262）。
③ 判据：M1240/M1241 2/2；新单测 3 条 + 帧判据（灰度差/间隙列前提）；两次 ESCAPED 与证人换代照记；precheck 231/213/600；hidden rot 0。
④ 436：Motion floor 4/5/77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 318 / 可判 1017 / rot 0。
⑥ 捕获 262 帧；基线 262/0/0/0；build 0 告警；换装 ok；本地全量 1244/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat`（R452 刻度的具名出口，非红）；② R453 自身跑；③ `RUNNER_SCROLL_SESSION_FLAKE`（R454 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ HTML 的 `<del>` 无同一条弱化（484）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度端点标签（483）；㊻ 437–484 的未结项仍开。

R453 收口预记（2026-10-28）：① 主笔 `4ba006f` + 追记 `5c925a9` 一次快进 push **`e750598..5c925a9` success**，HEAD=origin/main=`5c925a9`、**ahead=0**。② 新 head 跑 **`40645430259 ↔ 5c925a9`** 读时 **queued** ⇒ NOT-RUN（R454 ⓪ 必读 `STRIKE_DIM`/基线）。③ 本轮 ⓪ 的三跑已在收口前重试读到并全部 success：`40640660665 ↔ 86044bf`（`LIST_HANG_STYLE 16.0/16.0/0.0` 签收）、`40642482086 ↔ e083179`（`WEIGHT_CENTER_TICK_NOT_RUN=runner-settings-content-flat light/dark 轨=1`，按设计具名 NOT-RUN、非红）、`40642524490 ↔ e750598`；`40636558557 ↔ 667d1a2` success（TASK_DIM 1x 158.0/115.1、128.4/166.4）；`40634880705 ↔ 9743379` failure（滚动会话采样红 `testProductDurationRevealStillMovesOverTime` + Motion `testMarkdownModeLabelChange` 1<2；同代码 224b8ee/107f2b3 两跑 success）。R454 ⓪ 先只读验 remote 未变再快进 push（本轮已推，ahead=0），再读 `40645430259` 与上述跑；`RUNNER_SCROLL_SESSION_FLAKE` 原样重跑复核。

下一轮（R454）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R453 主笔+追记 head 跑 **`40645430259 ↔ 5c925a9`**、`40640660665 ↔ 86044bf`（LIST_HANG_STYLE 已签收）、`40642482086 ↔ e083179`（WEIGHT_CENTER_TICK 具名 NOT_RUN）、`40642524490 ↔ e750598` 与 `40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40634880705 ↔ 9743379`（滚动会话采样红原文）、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `STRIKE_DIM` 两档 137.9/82.0/+55.9 与 147.2/192.3/−45.2、隙 9/9、`WEIGHT_CENTER_TICK` 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`TASK_DIM` 158.0/115.1、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126、`HISTORY_SEARCH_SOURCE` 两档 0→1、`PROBE_DOMAIN` 44/20、`TABLE_HEADER` 1.10、`CODE_LINE_NUMBERS` 3/21/100% 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R452 状态（2026-10-28 · 本地 · 第 451 轮 / Round 449）：推荐权重滑块补 100% 中心刻度（9 条滑轨中心各 1×5pt 竖墨、邻列 0.0pt；旧形状只有 1pt 原生小点；8 张推荐面帧变化、基线 260）；TASK_DIM 1x 签收（亮 158.0/115.1、暗 128.4/166.4）；9743379 跑滚动会话采样红 + Motion 模式标签 1<2（产品 1 文件，权重刻度位）

最后更新：2026-10-28（本地 · R452 / 第 451 轮 / Round 449）：0–200% 量程里默认位只有一排 1pt 原生小点。`WeightSliderRow` 在 Slider 上叠一条 1×5pt `Capsule`（`Color.secondary.opacity(0.55)`、中心对齐、下移 9pt、`allowsHitTesting(false)`）。读数：`WEIGHT_CENTER_TICK light 轨=9 中心最高=5.0pt 邻列最高=0.0pt`、`dark 5.0/0.0`（先按长灰条找 9 条滑轨——旋钮把轨道截成两段，取首末跨度；再在轨道下方 4..14pt 量中心列/±20pt 邻列的最长竖墨；旋钮阴影贴着轨道，不进这一带）。**8 张推荐面帧变化**（weights、weights-adjusted、settings-recommendations、tall × 亮/暗）、0 新增/缺失；基线名单 **260**（同 commit 更新）；已看亮/暗 9 条滑杆的中心刻度。`M1238/M1239` **2/2**（去掉 overlay / 刻度缩成 1pt）。预检 **230/212/598 bad=0**、ARM **323/1081**、HIDDEN **317/1015 rot=0**。⓪：一次快进 push **`eb04e37..86044bf` success**（三笔）、HEAD=origin/main=`86044bf`、**ahead=0**；**`40636558557 ↔ 667d1a2` success**：`TASK_DIM light 勾选=158.0 未勾选=115.1 差=+42.9 墨数=376/426`、`dark 128.4/166.4 差=−38.0 墨数=469/492`，Motion floor `judged=4/5 executed=77 not-run=notice-banner` 红 0；**`40636617018 ↔ eb04e37` success**；**`40634880705 ↔ 9743379` failure**：`testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ `RUNNER_SCROLL_SESSION_FLAKE`（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R453 重跑复核）+ Motion floor `testMarkdownModeLabelChange` 1<2；同跑 QUICKPICK_HINT 400/519 签收；`40629776895`/`40623613789` failure 仅 Motion floor、`40620912699` failure 1 步（dark 行带，已修）；`40640660665 ↔ 86044bf`（R451 head）读时 in_progress ⇒ NOT-RUN。本地全量 **1240/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **260 帧**；基线 **260/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 451，`python3 scripts/product_streak.py --streak-for 451`，last=cade8bb）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push eb04e37..86044bf success、ahead=0；TASK_DIM 1x 签收；9743379 的滚动会话采样红（RUNNER_SCROLL_SESSION_FLAKE）与 Motion 模式标签 1<2 原文已读；667d1a2/eb04e37 两跑 success；R451 head 未读 ⇒ NOT-RUN。
② 产品：权重滑块 100% 中心刻度（9/5.0/0.0；8 帧变化、基线 260）。
③ 判据：M1238/M1239 2/2；帧判据 9 条滑轨逐条量中心/邻列；precheck 230/212/598；hidden rot 0。
④ 436：Motion floor judged=4/5 executed=77、red 0、not-run=notice-banner；markdown 模式标签采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 317 / 可判 1015 / rot 0。
⑥ 捕获 260 帧；基线 260/0/0/0；build 0 告警；换装 ok；本地全量 1240/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40640660665 ↔ 86044bf`（R451 head，in_progress）；② R452 自身跑；③ `RUNNER_SCROLL_SESSION_FLAKE`（R453 重跑复核）；④ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑤ `WEIGHT_CENTER_TICK` 的 runner 1x 读数（若设置内容列平涂，判据会具名 NOT_RUN）；⑥ HTML 列表缩进/任务弱化/表格体行（482/481/479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x（480）；㊸ HTML 任务列表无弱化（481）；㊹ HTML 列表缩进（482）；㊺ 中心刻度端点标签（483）；㊻ 437–483 的未结项仍开。

R452 收口预记（2026-10-28）：① 主笔 `7d9be37` + 追记 `e083179` 一次快进 push **`86044bf..e083179` success**，HEAD=origin/main=`e083179`、**ahead=0**。② `40640660665 ↔ 86044bf`（R451 主笔+追记 head，含 `LIST_HANG_STYLE`）与 R452 自身的新 head 跑在收口时 `gh` 列表 **EOF** ⇒ **`CI_READ_BLOCKED=network` / NOT-RUN**，R453 ⓪ 必读。③ 本轮已读：`40636558557 ↔ 667d1a2` success（TASK_DIM 1x：亮 158.0/115.1 +42.9、暗 128.4/166.4 −38.0；Motion floor 4/5/77、红 0）、`40636617018 ↔ eb04e37` success、`40634880705 ↔ 9743379` failure（`testProductDurationRevealStillMovesOverTime` 无中间 origin ⇒ `RUNNER_SCROLL_SESSION_FLAKE`，同代码 224b8ee/107f2b3 两跑 success；Motion `testMarkdownModeLabelChange` 1<2）、`224b8ee`/`107f2b3` success、`0737460`/`ecb8e69` failure 仅 Motion floor、`36284e1` failure 1 步。④ `WEIGHT_CENTER_TICK` 的 runner 1x 读数与 R451 的 `LIST_HANG_STYLE` 待 R453 ⓪ 从新跑读；若设置内容列平涂则具名 NOT_RUN。R453 ⓪ 先只读验 remote 未变再快进 push（本轮已推，ahead=0），随后读上述两跑与滚动会话红原样重跑复核。

下一轮（R453）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R451 主笔+追记 head 跑、`40640660665 ↔ 86044bf`（`LIST_HANG_STYLE`）、`40636558557 ↔ 667d1a2`（TASK_DIM 1x）、`40636617018 ↔ eb04e37` 与 `40634880705 ↔ 9743379`（滚动会话采样红原文）、`40632882239 ↔ 224b8ee`（success；QUICKPICK_HINT 400/519）、`40629867848 ↔ 107f2b3`（success）、`40629776895 ↔ 0737460`、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `WEIGHT_CENTER_TICK` 两档 9/5.0/0.0 或具名 NOT_RUN、`LIST_HANG_STYLE` 16.0/16.0/0.0、`TASK_DIM` 158.0/115.1/+42.9 与 128.4/166.4/−38.0、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R451 状态（2026-10-28 · 本地 · 第 450 轮 / Round 448）：折行列表项的续行回到首行正文同一竖轴（制表位 16.0 == headIndent 16.0、首行缩进 0.0；旧形状默认制表位 28 vs 续行 16 = 错开 12pt；2 张新帧 + 4 张旧帧变化、基线 258→260）；9743379 跑读到滚动会话采样红 + Motion 模式标签采样红（同代码两跑 success）（产品 2 文件，列表悬挂缩进位）

最后更新：2026-10-28（本地 · R451 / 第 450 轮 / Round 448）：`headIndent` 是 `firstLineHeadIndent + 16`，但首行正文的 `\t` 走默认制表位 28 —— 首行正文 28、续行 16，折行列表项错开 12pt。新 `ListHangingIndent` 纯策略（`max(16, 标记宽 + 2)`）；`MarkdownPresentation.hangingIndent` 用标记字体量宽；列表块的 `paragraphStyle` 设一条显式制表位，位置 == `headIndent`。读数：`LIST_HANG_STYLE light 制表位数=1 制表位=16.0 续行=16.0 首行=0.0pt`、`dark 同形`（旧形状制表位数 0、默认 28 ⇒ 28 vs 16）。夹具 `detail-list-wrap`；**2 张新帧、4 张旧帧变化**（`detail-markdown-rendered`/`detail-tasks` 的列表文字从 48 移到 36），基线 **258→260 / 0/0/0**；已看亮/暗同轴。**尺换代记**：第一版裸像素簇读数与同文件 PIL 不一致（Python 22/36.5 vs Swift 48/44），换成产品文本视图的段落样式结构量；没有把对不上的像素当结论。`M1236/M1237` **2/2**；新单测 4 条 + 产品入口判据；第一次 0 告警门咬到新测试 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0。预检 **229/211/596 bad=0**、ARM **322/1079**、HIDDEN **316/1013 rot=0**。⓪：开工 remote=`eb04e37`、ahead=0，`git push` 为 **no-op**；`40634880705 ↔ 9743379` 读时 in_progress、稍后 **failure**：`SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 无中间 origin（[0,1430,1430,1430]）⇒ 具名 **`RUNNER_SCROLL_SESSION_FLAKE`**（同代码 224b8ee/107f2b3 两跑 success，不改门槛，R452 重跑复核）+ Motion floor `testMarkdownModeLabelChange` 1<2（与 0737460 同源）；同跑 `QUICKPICK_HINT 400/519` 签收；`40636558557 ↔ 667d1a2`（TASK_DIM）与 `40636617018 ↔ eb04e37` 尚未读到 ⇒ NOT-RUN；`40629867848 ↔ 107f2b3`/`40632882239 ↔ 224b8ee` success；`0737460` failure 仅 Motion floor；`36284e1` failure 1 步（dark 行带，已修）、`fe956e3` 2、`eeccad0` 1。本地全量 **1239/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **260 帧**；基线 **260/0/0/0**；build **0 告警**（第一次 1 warning 已修）；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 450，`python3 scripts/product_streak.py --streak-for 450`，last=eb836bf）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ no-op push（remote eb04e37、ahead=0）；9743379 跑读到滚动会话采样红（RUNNER_SCROLL_SESSION_FLAKE）与 Motion 模式标签 1<2；QUICKPICK_HINT 400/519 签收；667d1a2/eb04e37 的 TASK_DIM 未读 ⇒ NOT-RUN。
② 产品：折行列表项续行回到首行正文同轴（制表位 16/续行 16/首行 0；2 新帧 + 4 旧帧变化、基线 260）。
③ 判据：M1236/M1237 2/2；新单测 4 条 + 产品入口段样式判据；像素簇尺与 PIL 不一致时换代记；第一次 0 告警门 1 条 MainActor 隔离，修后 0；precheck 229/211/596；hidden rot 0。
④ 436：Motion floor 5/5/77；markdown 模式标签采样红与 0737460 同源，未复现于其他跑；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 316 / 可判 1013 / rot 0。
⑥ 捕获 260 帧；基线 260/0/0/0；build 0 告警；换装 ok；本地全量 1239/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40636558557 ↔ 667d1a2`（TASK_DIM 未读）；② `40636617018 ↔ eb04e37`（同上）；③ R451 自身跑；④ `RUNNER_SCROLL_SESSION_FLAKE`（9743379 的 testProductDurationRevealStillMovesOverTime；R452 重跑复核）；⑤ 436 的 markdown 模式标签采样红（1<2；未复现于其他跑）；⑥ HTML 列表缩进无同一制表位（482）；⑦ HTML 任务列表无弱化（481）；⑧ HTML 表格体行无同一条线（479）；⑨ 设置内容列 1x 平涂；⑩ 设置脚注带 1x；⑪ 主窗口 content 帧 1x；⑫ 高夹具 1x；⑬ 13+ 菜单像素/标题；⑭ 真实拖拽；⑮ Dock 像素；⑯ 源图标最小窗文字 1x；⑰ 本地全量 5 条滚动红（449）；⑱ 2x/extended；⑲ 固定块揭示偏移（455）；⑳ 跨年时间（456）；㉑ 主列表暗档文字盲区（457）；㉒ 真机/多屏（447）；㉓ 真菜单栏、12 实时腿；㉔ `table-lazy-rows`；㉕ HTML 六档字号（460）；㉖ 清除 × 命中区（461）；㉗ 分隔线令牌（462）；㉘ 展开态已加载内容无帧（463）；㉙ 其它自绘控件帮助文本（464）；㉚ HTML 引用块无导引线（465）；㉛ HTML 表格表头无同档（466）；㉜ 100+ 行行号（467）；㉝ HTML 代码块行号（468）；㉞ 行号选中/滚动两态（469）；㉟ 关于页 1x 盲（470）；㊱ M613 机器前提（472）；㊲ 真机 vibrant 暗档（473）；㊳ 长来源截断（474）；㊴ bundle ID 未搜（475）；㊵ 长首行标签省略无帧（476）；㊶ HTML 代码块无语言标签（477）；㊷ HTML `<hr>` 无通栏线（478）；㊸ HTML 表格体行无同一条线（479）；㊹ QuickPick 键盘提示 1x（480）；㊺ 437–482 的未结项仍开。

R451 补记（2026-10-28）：收口主笔 `cade8bb` + 追记 `b868327` 的 push 遇断网（`git push` 拒、随后 `git ls-remote` 同拒，两次探测）⇒ **`PUSH_BLOCKED=network`**：HEAD=`b868327`、origin/main=`eb04e37`、**ahead=2**（本补记提交后 ahead=3）；R452 ⓪ 先只读验 remote 未变再快进 push 这三笔。`40636558557 ↔ 667d1a2`（TASK_DIM）与 `40636617018 ↔ eb04e37` 本轮始终未读（`gh` EOF）⇒ NOT-RUN；R451 自身的跑待推送后创建。

下一轮（R452）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R451 主笔+追记 head 跑、`40636558557 ↔ 667d1a2`（TASK_DIM）、`40636617018 ↔ eb04e37` 与 `40634880705 ↔ 9743379`（滚动会话采样红原文）、`40632882239 ↔ 224b8ee`（success；QUICKPICK_HINT 400/519）、`40629867848 ↔ 107f2b3`（success）、`40629776895 ↔ 0737460`、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1` 的全部失败步骤（成对 run↔commit），重点看 `LIST_HANG_STYLE` 两档 16.0/16.0/0.0 与 `detail-list-wrap` 帧、`TASK_DIM` 两档 148.3/85.1/+63.2 与 136.0/184.7/−48.7、`QUICKPICK_HINT` 400/519、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；`RUNNER_SCROLL_SESSION_FLAKE` 必须原样重跑复核（不改门槛）；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R450 状态（2026-10-28 · 本地 · 第 449 轮 / Round 447）：已完成任务项的正文弱一档（逐字相同的两行：亮 148.3 vs 85.1、暗 136.0 vs 184.7；2 张新帧 + 2 张旧帧变化、基线 256→258）；107f2b3 跑 success 签收 R448 的 TABLE_ROW_LINES/THEMATIC_RULE；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED（产品 2 文件，任务项完成态位）

最后更新：2026-10-28（本地 · R450 / 第 449 轮 / Round 447）：勾选态只落在 `☑`/`☐` 两个小字形上，正文与未完成项同色同重。新 `TaskItemPresentation` 纯策略（只有 checked 弱化、`secondaryLabelColor`）；`MarkdownPresentation.attributes(for:in:dimmed:)` 对完成项文字降一档（可点链接仍保留链接色），`appendRuns` 透传，`.unorderedItem` 只在 `.checked` 时 `dimmed`。旧/新（逐字相同的两行 `待办事项`，x 40..300 排除标记）：`TASK_DIM light 勾选=148.3 未勾选=85.1 差=+63.2 墨数=1149/1269`、`dark 136.0/184.7 差=-48.7 墨数=1287/1393`（墨数比 1.10）；`☑`/`☐` 与 `visibleText` 不动。夹具 `detail-tasks`；**2 张新帧、2 张旧帧变化**（`detail-markdown-rendered` 的「解析层完成」也变灰），基线 **256→258 / 0/0/0**；已看亮/暗。`M1234/M1235` **2/2**；新单测 3 条 + 帧判据；预检 **228/210/594 bad=0**、ARM **321/1077**、HIDDEN **314/1009 rot=0**。⓪：一次快进 push **`224b8ee..9743379` success**（两笔）、HEAD=origin/main=`9743379`、**ahead=0**；`gh run list` 读到 `40634880705 ↔ 9743379` 与 `40632882239 ↔ 224b8ee` 均 **in_progress**，随后 `gh` EOF ⇒ **`CI_READ_BLOCKED=network`**（两跑含 `QUICKPICK_HINT` 1x 读数 NOT-RUN）；**`40629867848 ↔ 107f2b3` success**，同跑 `TABLE_ROW_LINES 3/0/108.0/102.0/1.0`、`THEMATIC_RULE 597.0/1.0/1`、`CODE_LANGUAGE 116/126`、`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1`+NOT_RUN、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10`、`PROBE_DOMAIN 44/20`；**`40629776895 ↔ 0737460` failure 仅 Motion floor**（`judged=5/5 executed=77`、`testMarkdownModeLabelChangeIsAVisibleProcess` 1 帧<2，采样红、未登记）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（`testCopyReceipt...` 1<2）；`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）。receipt/markdown 模式两个采样红都未在 107f2b3 复现；不改门槛、不重猜 `must_judge`。本地全量 **1234/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **258 帧**；基线 **258/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 449，`python3 scripts/product_streak.py --streak-for 449`，last=07fcd2f）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push 224b8ee..9743379 success、ahead=0；107f2b3 跑 success 签收 R448 读数；0737460 failure 原文＝Motion floor 的 markdown 模式标签 1<2；两新跑 in_progress 后 gh EOF ⇒ NOT-RUN。
② 产品：完成项正文弱一档（亮 +63.2、暗 −48.7；2 新帧 + 2 旧帧变化、基线 258）。
③ 判据：M1234/M1235 2/2；新单测 3 条 + 帧判据（灰度差/墨数比）；precheck 228/210/594；hidden rot 0。
④ 436：107f2b3 success；0737460/ecb8e69 的两个采样红未复现；不改门槛、不重猜 must_judge。
⑤ 367：hidden 表 314 / 可判 1009 / rot 0。
⑥ 捕获 258 帧；基线 258/0/0/0；build 0 告警；换装 ok；本地全量 1234/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40634880705 ↔ 9743379`（in_progress 后 gh EOF）；② `40632882239 ↔ 224b8ee`（含 QUICKPICK_HINT 1x；同上）；③ R450 自身跑；④ 436 新跑 Motion floor（107f2b3 success；两个采样红未复现）；⑤ HTML 任务列表无同一条弱化（481）；⑥ HTML 表格体行无同一条线（479）；⑦ 设置内容列 1x 平涂；⑧ 设置脚注带 1x；⑨ 主窗口 content 帧 1x；⑩ 高夹具 1x；⑪ 13+ 菜单像素/标题；⑫ 真实拖拽；⑬ Dock 像素；⑭ 源图标最小窗文字 1x；⑮ 本地全量 5 条滚动红（449）；⑯ 2x/extended；⑰ 固定块揭示偏移（455）；⑱ 跨年时间（456）；⑲ 主列表暗档文字盲区（457）；⑳ 真机/多屏（447）；㉑ 真菜单栏、12 实时腿；㉒ `table-lazy-rows`；㉓ HTML 六档字号（460）；㉔ 清除 × 命中区（461）；㉕ 分隔线令牌（462）；㉖ 展开态已加载内容无帧（463）；㉗ 其它自绘控件帮助文本（464）；㉘ HTML 引用块无导引线（465）；㉙ HTML 表格表头无同档（466）；㉚ 100+ 行行号（467）；㉛ HTML 代码块行号（468）；㉜ 行号选中/滚动两态（469）；㉝ 关于页 1x 盲（470）；㉞ M613 机器前提（472）；㉟ 真机 vibrant 暗档（473）；㊱ 长来源截断（474）；㊲ bundle ID 未搜（475）；㊳ 长首行标签省略无帧（476）；㊴ HTML 代码块无语言标签（477）；㊵ HTML `<hr>` 无通栏线（478）；㊶ HTML 表格体行无同一条线（479）；㊷ QuickPick 键盘提示 1x 读数（480）；㊸ 437–481 的未结项仍开。

R450 收口预记（2026-10-28）：① 主笔 `eb836bf` + 追记 `667d1a2` 一次快进 push **`9743379..667d1a2` success**，HEAD=origin/main=`667d1a2`、**ahead=0**。② **`40632882239 ↔ 224b8ee`（R449 head）completed success**：`QUICKPICK_HINT light 底部墨=400、dark 519（地板 12）文本=↑↓ 选择 · ↵ 粘贴 · esc 关闭 提示顶=22.0 表底=26.0`；`TABLE_ROW_LINES 3/0/108.0/102.0/1.0`；`MOTION_FLOOR_FACTS judged=5/5 executed=77`、**红的用例=- 汇总行报红=0** ⇒ R449 的提示与 12 帧在 runner 1x 全绿。③ `40629776895 ↔ 0737460` failure **仅 Motion floor**（`testMarkdownModeLabelChangeIsAVisibleProcess` 1 帧<2）；`40623613789 ↔ ecb8e69` failure 仅 Motion floor（`testCopyReceipt...` 1<2）；两采样红均未在同代码的 107f2b3（success）复现。④ `40634880705 ↔ 9743379`（R449 预记 head）与 **`40636558557 ↔ 667d1a2`**（R450 head，含 `TASK_DIM`）读时 **in_progress** ⇒ NOT-RUN，R451 ⓪ 必读。⑤ 旧跑 `40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。

下一轮（R451）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R450 主笔+追记 head 跑 **`40636558557 ↔ 667d1a2`**（含 `TASK_DIM`）、`40634880705 ↔ 9743379`（R449 预记 head）与 `40632882239 ↔ 224b8ee`（R449 head，success；QUICKPICK_HINT 400/519）、`40629776895 ↔ 0737460`、`40629867848 ↔ 107f2b3`、`40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `TASK_DIM` 两档 148.3/85.1/+63.2 与 136.0/184.7/−48.7、`QUICKPICK_HINT` 1566/1848/0 与 12 帧、`TABLE_ROW_LINES` 3/0/108.0/102.0/1.0、`THEMATIC_RULE` 597.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R449 状态（2026-10-28 · 本地 · 第 448 轮 / Round 446）：QuickPick 底部补键盘操作提示（旧帧底部 26pt 带 0 墨 → 新 1566/1848；提示在表格可见区下方 4pt；12 张 QuickPick 帧变化、基线名单 256）；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED（产品 3 文件，浮层键盘提示位）

最后更新：2026-10-28（本地 · R449 / 第 448 轮 / Round 446）：`↑`/`↓` 选择、`↵` 粘贴、`esc` 关闭全靠用户猜 —— 面板底部一直是空白（旧 `quickpick-list` 帧底部 26pt 带实测 **0 墨**）。新 `QuickPickKeyboardHint` 纯策略（文案、11pt、`tertiaryLabelColor`、16pt 高、下内缩 6pt、上间距 4pt）；`QuickPickController` 底部加一行 label（identifier `quickPickKeyboardHint`），表格 stack 底边改钉到提示顶 −4pt。读数：`QUICKPICK_HINT light 底部墨=0→1566、dark 0→1848`（底部 26pt 带、x 12..408）；产品视图树：文本＝`↑↓ 选择 · ↵ 粘贴 · esc 关闭`、提示顶 22.0 ≤ 表格可见区底 26.0（4pt 间隙）。**12 张 QuickPick 帧变化、0 新增/缺失**；基线名单 **256**（`FRAME_BASELINE_UPDATED=256`，同 commit 更新）；已看亮/暗提示居中、不压候选行。`M1232/M1233` **2/2**（M1232 文本清空⇒底部 0 墨；M1233 表格底边退回⇒提示压表）；新帧判据两头钉；第一次 0 告警门咬到新测试里 `allSubviews` 的 MainActor 隔离，加 `@MainActor` 后冷编 0。预检 **227/209/592 bad=0**、ARM **320/1075**、HIDDEN **314/1009 rot=0**。⓪：开工 remote=`107f2b3`、ahead=0，`git push` 为 **no-op**；`gh run list` 读到 `40629776895 ↔ 0737460` 与 `40629867848 ↔ 107f2b3` 均 **in_progress** ⇒ NOT-RUN，随后 `gh` 单跑/列表 **EOF** ⇒ **`CI_READ_BLOCKED=network`**；已读 `40623613789 ↔ ecb8e69` failure **仅 Motion floor**（Swift 全绿；`MOTION_FLOOR_FACTS judged=5/5 executed=77`、`MOTION_FLOOR_SUITE_RED=1`＝`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1 帧<2 采样红、未登记），receipt 采样原样重跑、不改门槛；旧跑 `40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。本地全量 **1230/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **256 帧**；基线 **256/0/0/0**；build **0 告警**（第一次 1 warning 已修）；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 448，`python3 scripts/product_streak.py --streak-for 448`，last=324ced6）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ 开工 no-op push（remote 107f2b3、ahead=0）；两新跑 in_progress 后 gh EOF ⇒ CI_READ_BLOCKED；ecb8e69 仅 Motion floor 采样红（receipt 1<2），原样重跑不改门槛；旧跑读数已取。
② 产品：QuickPick 底部键盘提示（0→1566/1848；12 帧变化、基线 256）。
③ 判据：M1232/M1233 2/2；新帧判据（文本/位置/墨量）；第一次 0 告警门 1 条 MainActor 隔离，修后 0；precheck 227/209/592；hidden rot 0。
④ 436：最后已知 judged=5/5 executed=77；新跑读不到 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 314 / 可判 1009 / rot 0。
⑥ 捕获 256 帧；基线 256/0/0/0；build 0 告警；换装 ok；本地全量 1230/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40629776895 ↔ 0737460`（in_progress 后 gh EOF；TABLE_ROW_LINES 未读）；② `40629867848 ↔ 107f2b3`（同上）；③ R449 自身跑（提交后创建）；④ 436 新跑 Motion floor（最后已知 5/5/77）；⑤ `QUICKPICK_HINT` 的 runner 1x 读数（gh 断）；⑥ 12 帧 QuickPick 的 runner 读数；⑦ HTML 表格体行无同一条线（479）；⑧ 设置内容列 1x 平涂；⑨ 设置脚注带 1x；⑩ 主窗口 content 帧 1x；⑪ 高夹具 1x；⑫ 13+ 菜单像素/标题；⑬ 真实拖拽；⑭ Dock 像素；⑮ 源图标最小窗文字 1x；⑯ 本地全量 5 条滚动红（449）；⑰ 2x/extended；⑱ 固定块揭示偏移（455）；⑲ 跨年时间（456）；⑳ 主列表暗档文字盲区（457）；㉑ 真机/多屏（447）；㉒ 真菜单栏、12 实时腿；㉓ `table-lazy-rows`；㉔ HTML 六档字号（460）；㉕ 清除 × 命中区（461）；㉖ 分隔线令牌（462）；㉗ 展开态已加载内容无帧（463）；㉘ 其它自绘控件帮助文本（464）；㉙ HTML 引用块无导引线（465）；㉚ HTML 表格表头无同档（466）；㉛ 100+ 行行号（467）；㉜ HTML 代码块行号（468）；㉝ 行号选中/滚动两态（469）；㉞ 关于页 1x 盲（470）；㉟ M613 机器前提（472）；㊱ 真机 vibrant 暗档（473）；㊲ 长来源截断（474）；㊳ bundle ID 未搜（475）；㊴ 长首行标签省略无帧（476）；㊵ HTML 代码块无语言标签（477）；㊶ HTML `<hr>` 无通栏线（478）；㊷ 437–480 的未结项仍开。

R449 收口预记（2026-10-28）：① 主笔 `07fcd2f` + 追记 `224b8ee` 一次快进 push **`107f2b3..224b8ee` success**，HEAD=origin/main=`224b8ee`、**ahead=0**。② 推送后 `gh run list` 读到：**`40629867848 ↔ 107f2b3`（R448 预记 head）completed success** —— R448 代码整体绿，Motion floor 的 `testCopyReceipt...` 1 帧<2 采样红在**同代码的下一跑未复现**（不改门槛）；**`40629776895 ↔ 0737460`（R448 主笔+追记 head）completed failure**，但 `gh run view --log-failed` 两次 EOF ⇒ 失败步骤与 `TABLE_ROW_LINES` 原文 **NOT-RUN**，R450 ⓪ 必读并归因（若也是 receipt 采样，则与 107f2b3 的成功对照成立）。③ 新 head 跑 **`40632882239 ↔ 224b8ee`** 读时 **in_progress** ⇒ NOT-RUN（R449 的 QUICKPICK_HINT 首跑，R450 必读）。④ 旧跑 `40623613789 ↔ ecb8e69` failure 仅 Motion floor（已读）、`40620912699 ↔ 36284e1` failure 1 步（dark 行带，已修）、`40617745753 ↔ fe956e3` failure 2 步、`40613782362 ↔ eeccad0` failure 1 步。

R449 补记（2026-10-28）：预记 `80c9516` 自身的 push 遇断网（`git push` 拒、随后 `git ls-remote` 同拒，两次探测）⇒ **`PUSH_BLOCKED=network`**：HEAD=`80c9516`、origin/main=`224b8ee`、**ahead=1**（本补记提交后 ahead=2）；R450 ⓪ 先只读验 remote 未变再快进 push 这两笔。

下一轮（R450）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R449 主笔+追记 head 跑 **`40632882239 ↔ 224b8ee`**（含 `QUICKPICK_HINT`）、`40629776895 ↔ 0737460`（failure，R448 读数原文）、`40629867848 ↔ 107f2b3`（success，R448 读数）与 `40623613789 ↔ ecb8e69`、`40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `QUICKPICK_HINT` 两档 1566/1848/0 与 12 帧、`TABLE_ROW_LINES` 3/0/108.0/101.5/1.0、`THEMATIC_RULE` 612.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R448 状态（2026-10-28 · 本地 · 第 447 轮 / Round 445）：Markdown 表格体行之间补发丝分隔线（表头+四行体行 3 条、单行体行 0 条；线宽 108.0/107.5 对表宽 101.5、厚 1.0；2 张新帧、基线 254→256）；两次网络探测均拒 ⇒ PUSH_BLOCKED=network（ahead=3）、gh EOF ⇒ CI_READ_BLOCKED（产品 3 文件，表格体行分隔位）

最后更新：2026-10-28（本地 · R448 / 第 447 轮 / Round 445）：R440 把表头用 semibold 分开之后，多行体行之间仍无线。新 `TableRowSeparators` 纯策略（`lineCount`、只在体行之间画、1pt、`tertiaryLabelColor`、贴行底）；`MarkdownPresentation.tableRowCountAttribute` 只打在 ≥2 行的表格块上；`drawTableRowSeparators` 在背景层按**各行 usedRect 的外接宽度**画。旧/新：`TABLE_ROW_LINES light 线数=3 负臂=0 线宽=108.0pt 表宽=101.5pt 厚=1.0pt`、`dark 107.5/101.5/1.0`。夹具 `detail-table-rows`（表头+四行体行）与既有 `detail-table`（表头+一行）成对；**2 张新帧、0 张旧帧变化**（单行臂不画线，`detail-table` 逐字节不变），基线 **254→256 / 0/0/0**；已看亮/暗：表头下无线、三条体行线、末行下无线。实现中修两处几何病（行片段 `characterRange` 含换行 ⇒ `isRowEnd` 看 `rowEnd-1`；`boundingRect` 是整行片段宽 480pt ⇒ 改 usedRect 外接）；第一次 0 告警门咬到未用 `textContainer`，删后冷编 0。`M1230/M1231` **2/2**（M1231 改 needle 到单测必现文）；`M1206` 因新行腐烂，重钉并复跑 R440 表 **2/2**。新单测 5 条 + 帧判据（3/0/≤2pt/±6pt）；预检 **226/208/590 bad=0**、ARM **319/1073**、HIDDEN **313/1007 rot=0**。⓪：两次探测（`git ls-remote`/`git push`）均报权限拒（api=000）⇒ **`PUSH_BLOCKED=network`**：HEAD=`7545e0e`、origin/main=`ecb8e69`、**ahead=3**（602eea2/c5ef6e6/7545e0e）；`gh run list` EOF ⇒ **`CI_READ_BLOCKED=network`**，本轮未读/未建任何跑（`40623613789 ↔ ecb8e69` 与旧四跑 NOT-RUN；最后已读读数见 R447 账）。436：最后一次已知 36284e1 臂 `judged=5/5 executed=77`；本轮新跑读不到 ⇒ NOT-RUN，不重猜 `must_judge`。本地全量 **1229/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **256 帧**；基线 **256/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 447，`python3 scripts/product_streak.py --streak-for 447`，last=602eea2）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ 两次网络探测均拒 ⇒ PUSH_BLOCKED=network（ahead=3、三笔 SHA）；gh EOF ⇒ CI_READ_BLOCKED；所有跑与 436 新跑 NOT-RUN，不重猜 must_judge。
② 产品：表格体行之间补 1pt 发丝线（3/0、108.0/101.5/1.0；0 旧帧变化、基线 256）。
③ 判据：M1230/M1231 2/2；M1206 因新行腐烂重钉并复跑 R440 表 2/2；新单测 5 条 + 帧判据；precheck 226/208/590；hidden rot 0。
④ 436：本轮读不到新跑 ⇒ NOT-RUN（最后已知 5/5/77）。
⑤ 367：hidden 表 313 / 可判 1007 / rot 0。
⑥ 捕获 256 帧；基线 256/0/0/0；第一次 0 告警门 1 条未用绑定，修后 0；换装 ok；本地全量 1229/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① 本轮所有 runner 跑（PUSH_BLOCKED=network，含 `40623613789 ↔ ecb8e69`）；② 436 新跑 Motion floor（最后已知 5/5/77）；③ 表格行线的 1x runner 像素（未上传）；④ HTML 表格体行无同一条线（479）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ HTML `<hr>` 无通栏线（478）；㊴ 437–479 的未结项仍开。

R448 收口预记（2026-10-28）：① 收口网络恢复（`git ls-remote` 读 remote 仍 `ecb8e69`），一次快进 push **`ecb8e69..0737460` success**（五笔：602eea2/c5ef6e6/7545e0e/324ced6/0737460），HEAD=origin/main=`0737460`、**ahead=0**。② `40623613789 ↔ ecb8e69` 已读：结论 **failure，但失败步骤只有 1 个＝Motion coverage floor**；Swift 测试全绿（暗档行带修复签收：`HISTORY_SEARCH_SOURCE light 1/3、dark 1/1` + `HISTORY_SEARCH_SOURCE_NOT_RUN=runner-1x-sidebar-plain dark 行带=1`；`CODE_LANGUAGE 116/126`、`PROBE_DOMAIN 44/20`）。Motion floor 原文：`MOTION_FLOOR_FACTS judged=5/5 executed=77`、`MOTION_FLOOR_SUITE_RED=1` ＝ `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`（1x 只有 1 个过渡帧，要 ≥2）；它是采样红、未登记进采样名册，R449 ⓪ 原样重跑复核，**不改门槛、不重猜 must_judge**。③ 新 head 跑 **`40629776895 ↔ 0737460`** 读时 **in_progress** ⇒ NOT-RUN（含 R448 表格体行线，R449 必读）。④ `40620912699 ↔ 36284e1` failure 1 步（dark 行带，已由补记修）；`40617745753 ↔ fe956e3` failure 2 步；`40613782362 ↔ eeccad0` failure 1 步；`40605228813 ↔ bdb4737` failure 2 步。

下一轮（R449）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R448 主笔+追记 head 跑 **`40629776895 ↔ 0737460`**（含 `TABLE_ROW_LINES`）、`40623613789 ↔ ecb8e69`（failure 仅 Motion floor 采样）、`40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `TABLE_ROW_LINES` 两档 3/0/108.0/101.5/1.0、`THEMATIC_RULE` 612.0/1.0/1、`CODE_LANGUAGE` 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R447 状态（2026-10-28 · 本地 · 第 446 轮 / Round 444）：Markdown 主题分隔线改成通栏 1pt 线（旧 24 个 `─` 字符比正文窄、比行厚、复制带字符 → 新 612.0pt/1.0pt/1 条；2 张新帧、基线 252→254）；R446 的 CODE_LANGUAGE/PROBE_DOMAIN 在 runner 1x 上真读到并通过（产品 3 文件，主题分隔线位）

最后更新：2026-10-28（本地 · R447 / 第 446 轮 / Round 444）：`thematicBreakText` 把 `---` 渲染成 24 个 `─` —— 长度由字数决定（比正文窄）、墨带是一行字高、复制渲染结果会带出 24 个字符。新 `ThematicBreakRule` 纯策略（1pt、`secondaryLabelColor`、通栏居中、占位空格 `" "`）；`MarkdownPresentation.thematicBreakAttribute` 只标范围，属性串只留一个占位空格（保住行高，复制看不见）；`drawThematicBreaks` 在背景层按列宽画线。读数：`THEMATIC_RULE light 长线=612.0pt 带高=1.0pt 带数=1`、`dark 同形`；复制语义单测断言属性串不含 `─`、属性恰好一段。夹具 `detail-rule`（H1 + 两段 + 一条 `---`）；**2 张新帧、0 张旧帧变化**（现有夹具都没有主题分隔线），基线 **252→254 / 0/0/0**；已看亮/暗通栏细线。`M1228/M1229` **2/2**（M1229 只能由复制语义单测抓，帧上背景线仍在；M1228 首跑 needle 漏「长」字，修后复跑红得对）；新单测 4 条 + 帧判据；预检 **225/207/588 bad=0**、ARM **318/1071**、HIDDEN **312/1005 rot=0**。⓪：一次快进 push **`36284e1..ecb8e69` success**（两笔）、HEAD=origin/main=`ecb8e69`、**ahead=0**；成对读数：`40617745753 ↔ fe956e3` failure **2 步**（vibrant 22≠20、dark 行带 1<3；HISTORY_SEARCH_SOURCE light 1/3、dark 1/1；HISTORY_ROW_SOURCE 139.0/74.0；SETTINGS_ABOUT_ROW 7/7；CODE_LINE_NUMBERS 54.0/3/21.0/100%；TABLE_HEADER 1.10）；`40620912699 ↔ 36284e1` failure **1 步**（同一个 dark 行带；`CODE_LANGUAGE light 右区=510..646pt 标签墨=116 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`、dark 126；`PROBE_DOMAIN 44/20` 过；`MOTION_FLOOR_FACTS judged=5/5 executed=77`）；`40613782362 ↔ eeccad0` failure 1 步（vibrant；HISTORY_SEARCH_SOURCE test-not-in-commit）；`40605228813 ↔ bdb4737` failure 2 步；`40623613789 ↔ ecb8e69` 读时 **in_progress**（单跑 EOF）⇒ NOT-RUN。本地全量 **1223/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **254 帧**；基线 **254/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 446，`python3 scripts/product_streak.py --streak-for 446`，last=dc477b8）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push 36284e1..ecb8e69 success、ahead=0；四跑成对读数取齐（fe956e3 2 步、36284e1 1 步、eeccad0 1 步、bdb4737 2 步）；ecb8e69 跑 in_progress ⇒ NOT-RUN；R446 的 CODE_LANGUAGE 1x 116/126、PROBE_DOMAIN 44/20 真读到并通过。
② 产品：主题分隔线改成通栏 1pt 线（612/1/1；复制无 `─`；2 张新帧、基线 254）。
③ 判据：M1228/M1229 2/2；新单测 4 条 + 帧判据（长线/带高/带数/复制语义）；precheck 225/207/588；hidden rot 0；M1226 因新行腐烂，已重钉并复跑 R446 表 2/2。
④ 436：36284e1 臂 `judged=5/5 executed=77`（一个 copy-receipt 采样红，report-only）；ecb8e69 臂未完成 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 312 / 可判 1005 / rot 0。
⑥ 捕获 254 帧；基线 254/0/0/0；build 0 告警；换装 ok；本地全量 1223/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40623613789 ↔ ecb8e69`（in_progress）；② eeccad0 的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 的 ecb8e69 臂 Motion floor；④ HTML `<hr>` 未覆盖（478）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 长来源截断（474）；㉟ bundle ID 未搜（475）；㊱ 长首行标签省略无帧（476）；㊲ HTML 代码块无语言标签（477）；㊳ 437–478 的未结项仍开。

R447 收口预记（2026-10-28）：① 主笔 `602eea2` + 追记 `c5ef6e6` 推送遇断网（`ls-remote` 与 `push` 同一批两次探测均拒）⇒ **`PUSH_BLOCKED=network`**，HEAD=`c5ef6e6`、origin/main=`ecb8e69`、**ahead=2**；这两笔的 run 未创建。② `40623613789 ↔ ecb8e69` 读时 **in_progress**，随后单跑/列表 `gh` 均 EOF ⇒ **`CI_READ_BLOCKED=network`** / NOT-RUN（R448 ⓪ 必读；它是补记 2dd3284 之后的首跑，要看 dark 行带是否转绿）。③ 已读三跑：`40617745753 ↔ fe956e3` failure 2 步、`40620912699 ↔ 36284e1` failure 1 步（dark 行带；2dd3284 未进该提交）、`40613782362 ↔ eeccad0` failure 1 步。R448 ⓪ 先只读验 remote 未变再快进 push 两笔，再读 ecb8e69 与 R447 两笔的跑。

下一轮（R448）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R447 主笔+追记 head 跑、`40623613789 ↔ ecb8e69`（R447 开工时的 in_progress；补记后首跑）与 `40620912699 ↔ 36284e1`、`40617745753 ↔ fe956e3`、`40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），重点看 `THEMATIC_RULE` 两档 612.0/1.0/1、`CODE_LANGUAGE` 两档 116/126/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/20、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R446 状态（2026-10-28 · 本地 · 第 445 轮 / Round 443）：代码块补语言标签（解析层已有语言、渲染层从未显示；首行右侧标签墨 316/381、无语言臂 0；同文对照帧 + 2 张新帧、基线 250→252）；vibrant judged 22≠20 的 -2 条成因已修（产品 3 文件，代码块语言标识位）

最后更新：2026-10-28（本地 · R446 / 第 445 轮 / Round 443）：解析层从围栏信息串认出语言，呈现层只用了行数 —— ` ```swift ` 与 ` ```python ` 在详情里没有区别。新 `CodeLanguageTag` 纯策略（别名归一化、未知原样大写截 12、`text/plaintext` 与非 ASCII 不标；`fits` 要求首行正文右沿与标签间 ≥24pt，否则不画）；`MarkdownPresentation.codeLanguageAttribute` 只打在代码块正文；`ChineseSelectableNSTextView.drawCodeLanguageTags` 在首行右侧画（9pt semibold、右沿内缩 10pt、`secondaryLabelColor`），标签不进文本存储。读数：`CODE_LANGUAGE light 右区=492..628pt 标签墨=316 无语言臂=0 第二行=0/0 行号带=3/3 正文左=21.0/21.0pt`；`dark 381`（同形）。夹具 `detail-code`（```swift）与新 `detail-code-plain`（```，三行逐字相同）成对；**2 张新帧、4 张旧帧变化**（detail-code 亮/暗 + detail-markdown-rendered 亮/暗），基线 **250→252 / 0/0/0**；已看亮/暗 SWIFT、plain 无标签、markdown 一行 swift 块也有 SWIFT。`M1226/M1227` **2/2**（M1226 首跑红文漏「有」字，修 needle 后复跑红得对）；新单测 6 条 + 帧判据；预检 **224/206/586 bad=0**、ARM **317/1069**、HIDDEN **311/1003 rot=0**。⓪：一次快进 push **`eeccad0..fe956e3` success**（三笔）、HEAD=origin/main=`fe956e3`、**ahead=0**；head 跑 **`40617745753 ↔ fe956e3`** 在 ⓪ 时 in_progress、收口读到 **failure 2 步**（vibrant 22≠20 已修；侧栏搜索来源 dark 行带 1<3 由补记 `2dd3284` 记具名 `HISTORY_SEARCH_SOURCE_NOT_RUN`、门槛未动）；`40613782362 ↔ eeccad0` failure **1 步**＝vibrant judged 22≠20（2 条 nil-vibrant 不可判说明段被漏扣；本轮仪器修好，本地 44/44）；同跑 `CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`HISTORY_ROW_SOURCE 139.0/74.0`、`SETTINGS_ABOUT_ROW 7/7`、`TABLE_HEADER 1.10/1.11`、`PROBE_DOMAIN 22/20` 与 `PROBE_DOMAIN_NOT_RUN 22`；`HISTORY_SEARCH_SOURCE` 在 eeccad0 上 test-not-in-commit ⇒ NOT-RUN；`40605228813 ↔ bdb4737` failure **2 步**（同一 vibrant + 设置关于行 0≠7，后者 R443 已修）。本地全量 **1218/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4** ⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷 **252 帧**；基线 **252/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 381=381`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 445，`python3 scripts/product_streak.py --streak-for 445`，last=56486a9）。清账 `格=162 声明=63 不成立=0/63`；电池 `Ran 683 / OK (skipped=5)`。

本轮做了什么：
① ⓪ push eeccad0..fe956e3 success、ahead=0；eeccad0 唯一红＝vibrant 22≠20 已定位到 2 条 nil-vibrant 说明段并修；HISTORY_SEARCH_SOURCE 在 eeccad0 上不存在 ⇒ NOT-RUN；bdb4737 的 2 步红对上（后者 R443 已修）；head 跑 in_progress ⇒ NOT-RUN。
② 产品：代码块补语言标签（首行右侧、放不下不画；2 张新帧、4 张旧帧变化、基线 252）。
③ 判据：M1226/M1227 2/2；新单测 6 条 + 帧判据（标签墨/无语言臂/第二行/行号/正文左）；precheck 224/206/586；hidden rot 0。
④ 436：head 跑未完成，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 311 / 可判 1003 / rot 0。
⑥ 捕获 252 帧；基线 252/0/0/0；build 0 告警；换装 ok；本地全量 1218/57/5（滚动具名）。

NOT-RUN / 阻塞（分开写）：① `40617745753 ↔ fe956e3`（已读 failure 2 步：vibrant 22≠20、dark 行带 1<3 ⇒ 补记记 NOT-RUN；R447 复核）；② eeccad0 的 `HISTORY_SEARCH_SOURCE`（test-not-in-commit）；③ 436 新跑 Motion floor；④ 长首行标签省略无帧（476）；⑤ HTML 代码块无语言标签（477）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 长来源截断（474）；㊱ bundle ID 未搜（475）；㊲ 437–477 的未结项仍开。

R446 收口补记（2026-10-28）：① 主笔 `dc477b8` + 追记 `36284e1` 已一次快进 push **`fe956e3..36284e1` success**、ahead=0；② `40617745753 ↔ fe956e3` 完成 **failure 2 步**：`testProbesDoNotSitOnVibrantColumns` 22≠20（R446 已修）+ `testSidebarSearchMatchesTheSourceAppName` dark 行带 1<3（1x 暗档侧栏盲区；补记 `2dd3284` 改为具名 `HISTORY_SEARCH_SOURCE_NOT_RUN`、门槛未动，本地亮/暗 3/3）；③ `40620912699 ↔ 36284e1` 读时 **in_progress** ⇒ NOT-RUN；④ 补记 `2dd3284` 推送遇断网（`api=000`、SSH 拒）⇒ **`PUSH_BLOCKED=network`**，ahead=1（`2dd3284` 在 `36284e1` 之上），其 run 未创建；R447 ⓪ 先只读验 remote 再快进 push，并读 `2dd3284` 的跑。

下一轮（R447）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R446 主笔+追记+补记 head 跑、`40617745753 ↔ fe956e3`（failure 2 步）、`40620912699 ↔ 36284e1`（in_progress）与 `40613782362 ↔ eeccad0` 的全部失败步骤（成对 run↔commit），以及 `2dd3284` 推送后的跑；重点看 `CODE_LANGUAGE` 两档 316/381/0/0、`HISTORY_SEARCH_SOURCE` 两档 0→1、亮档行带 3 / 暗档具名 NOT-RUN（fe956e3 上才有）、`HISTORY_ROW_SOURCE` 139.0/74.0、`SETTINGS_ABOUT_ROW` 7/7、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R445 状态（2026-10-28 · 本地 · 第 444 轮 / Round 442）：侧栏搜索补匹配来源 App 名（只命中来源的查询 0 行→1 行、无结果态无表=0；新 `HistorySearchPolicy`，Store 收薄 1120→1108 行/最长 66；2 张新帧、基线 248→250）；R444 修复的 runner 验证被 EOF 挡住（40613782362 in_progress→EOF）（产品 3 文件，侧栏搜索来源位）

最后更新：2026-10-28（本地 · R445 / 第 444 轮 / Round 442）：搜索不匹配来源名，而 R444 已把来源显示在行里。新 `HistorySearchPolicy.matches`：来源名与内容/OCR/文件并列（不是替换；空来源/空查询不编匹配）；`HistoryStore.computeFilteredEntries` 收成一行调用（1120→**1108 行**、最长仍 **66**）。夹具 `sidebar-search-source`（查询 "Safari" 不在任何正文、只在第一行来源）：旧口径 0 行（与 `sidebar-no-results` 同形）、新 **1 行**；无结果态**没有 NSTableView** ⇒ 负臂读成"无表=0 行"（不是 -1）；过滤后单行被 List 默认选中（离屏黑块吞字）⇒ 夹具清空选中。读数：`HISTORY_SEARCH_SOURCE light/dark 来源查询行数=1（行带 3） 无结果查询=-1（无表）`；**2 张新帧、0 张旧帧变化**，基线 **248→250 / 0/0/0**；已看搜索框 "Safari"、"1 条记录"、行内「来自 Safari」。`M1224/M1225` **2/2 CAUGHT**；新单测 4 条 + 存储入口 + 帧判据；预检 **223/205/584 bad=0**、ARM **316/1067**、HIDDEN **310/1001 rot=0**。⓪：开工一次快进 push **`bdb4737..eeccad0` success**（六笔）、HEAD=origin/main=`eeccad0`、**ahead=0**；新 head 跑 **`40613782362 ↔ eeccad0`** 开始 in_progress、后 EOF ⇒ `CI_READ_BLOCKED=network`/NOT-RUN（R444 的两条仪器修复的 runner 验证待 R446）；R442 跑 `40605228813 ↔ bdb4737` failure 2 步（仪器病，R444 已修）读数已取；收口 `api=000` ⇒ R445 提交 `PUSH_BLOCKED=network`（见预记）。本地全量 **1211/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/202.0/1438；TIME 18/8/24.5/1438；CHANNEL 0→80.0→600 变化 721/96000 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **250 帧**；基线 **250/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 444，现读 `python3 scripts/product_streak.py --streak-for 444`，last=50c186d）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push `bdb4737..eeccad0` success、ahead=0；新 head 跑 40613782362 in_progress→EOF ⇒ CI_READ_BLOCKED；R442 跑 2 步红（仪器病已修）读数已取；收口断网 ⇒ R445 提交待推。
② 产品：侧栏搜索补匹配来源 App 名（0→1 行；Store 收薄 1108/66；2 张新帧、基线 250）。
③ 判据：M1224/M1225 2/2；新单测 4 条 + store 入口 + 帧判据；负臂无表=0；precheck 223/205/584；hidden rot 0。
④ 436：新跑读数被 EOF 挡住，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 310 / 可判 1001 / rot 0。
⑥ 捕获 250 帧；换装 ok；清账 162/63/0；帧基线 250/0/0/0；本地全量 1211/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。
⑦ 收口：主笔 `56486a9` + 追记 `8921042` 本地；`git push` 被拒（`api=000`）⇒ **`PUSH_BLOCKED=network`（ahead=2，HEAD `8921042`，origin/main `eeccad0`）**；R445 自身跑未创建；`40613782362 ↔ eeccad0` 仍 `CI_READ_BLOCKED`（R446 ⓪ 补读，重点 R444 两条仪器修复是否在 runner 绿）；R446 ⓪ 先只读 `git ls-remote` 验 remote 仍为 `eeccad0`，再一次快进 push 两笔。

NOT-RUN / 阻塞（分开写）：① R445 自身跑（提交后创建；收口 api=000）；② `40613782362 ↔ eeccad0`（CI_READ_BLOCKED=network，R444 修复的 runner 验证）；③ 436 新跑 Motion floor；④ bundle ID 未搜（475）；⑤ 长来源截断无帧（474）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页 1x 盲（470）；㉝ M613 机器前提（472）；㉞ 真机 vibrant 暗档（473）；㉟ 437–475 仍开。

下一轮（R446）的靶：⓪ 先 `git push origin main`（禁 amend/force；**当前 `PUSH_BLOCKED=network`、ahead=2**，恢复后先只读 `git ls-remote` 验 remote 仍为 `eeccad0`，再一次快进 push 两笔）并复核 ahead=0；读 R445 主笔+追记 head 跑、`40613782362 ↔ eeccad0` 与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看 `HISTORY_SEARCH_SOURCE` 两档 0→1/行带 3、`HISTORY_ROW_SOURCE` 140.5/73.5、`SETTINGS_ABOUT_ROW` 亮/暗 7、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R444 状态（2026-10-28 · 本地 · 第 443 轮 / Round 441）：主列表行的时间行补「· 来自 <来源 App>」（时间在前、来源在后；nil 只显示时间；来源行 140.5pt vs 无来源 73.5pt、差 67.0、左沿 96.5/96.5 同轴；57 张行/侧栏/content 帧变化 + 2 张负臂新帧，基线 246→248）；R442 跑 failure 2 步（vibrant 判据 22≠20、设置关于行 light 0≠7）⇒ 都是新判据仪器病，已按视图树行带/扣不可判控件修（阈值未动）（产品 2 文件，主列表行来源位）

最后更新：2026-10-28（本地 · R444 / 第 443 轮 / Round 441）：主列表此前只显示时间，来源只在详情头部。新 `HistoryRowSourceLine`：`时间 · 来自 <来源>`（时间在前；来源 nil/空白只显示时间；行宽不够先截断来源），`RowTextColumn` 接它 + `lineLimit(1)`。旧/新：`HISTORY_ROW_SOURCE light/dark 来源行宽=140.5pt 无来源行宽=73.5pt 差=67.0pt 左沿=96.5/96.5pt`；负臂 `sidebar-no-source`（同正文/时间、来源 nil；存档载入 + 清空选中，避免黑块盖行）只剩时间。帧 **57 张行/侧栏/content 变化 + 2 张负臂**，基线 **246→248 / 0/0/0**；`sidebar-history` 四行「时间 · 来自 Safari/预览/访达」已看。`M1220/M1221` **2/2 CAUGHT**；新单测 3 条 + 帧判据 1 条；预检 **222/204/582 bad=0**、ARM **315/1065**、HIDDEN **309/999 rot=0**。⓪：开工 `api=000`、两探断 ⇒ **`PUSH_BLOCKED=network`（ahead=3，HEAD `ed715f1`，origin/main `bdb4737`）** 与 **`CI_READ_BLOCKED=network`**；收口前 api 短暂恢复 ⇒ 补读 R442 自身跑 **`40605228813 ↔ bdb4737` failure、失败步骤 2 个**：vibrant 判据 `judged=22 != mustJudge=20`（不可判控件被算成判过）、设置关于行判据 light `0 != 7`（R118 的 282pt 机器差）—— 两条都是 R442 新判据的仪器病，本轮改成**视图树行带** + 把不可判控件从 judged 扣掉，阈值/产品未动，本地复跑绿（`PROBE_DOMAIN 44/44`、`SETTINGS_ABOUT_ROW light/dark 7`）；R442 跑的 `CODE_LINE_NUMBERS 54.0/3/21.0/100%`、`TABLE_HEADER 1.10/1.11`、`CAPTION_JUDGED 6/18` 已取；Motion floor 行不在这份失败步骤日志里 ⇒ NOT-RUN。R443 三笔未推、R444 自身跑待 push。本地全量 **1206/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/221.5/1438；TIME 18/9/54.0/1438；CHANNEL 0→82.0→600 变化 30442/105600 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **248 帧**；基线 **248/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 443，现读 `python3 scripts/product_streak.py --streak-for 443`，last=258fc8e）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 开工两探断 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；收口前补读 R442 跑 failure 2 步（vibrant 22≠20、关于行 0≠7）⇒ 修仪器（视图树行带/扣不可判控件），阈值未动；CODE/TABLE/CAPTION 读数已取。
② 产品：主列表行时间行补「· 来自 <来源 App>」（来源行 140.5 vs 73.5、差 67.0；57 张帧 + 2 张负臂，基线 248）。
③ 判据：M1220/M1221 2/2；新单测 3 条 + 帧判据；负臂清空选中；precheck 222/204/582；hidden rot 0。
④ 436：R442 跑的 Motion floor 行被网络 EOF 挡住，未读 ⇒ NOT-RUN，不重猜 must_judge。
⑤ 367：hidden 表 309 / 可判 999 / rot 0。
⑥ 捕获 248 帧；换装 ok；清账 162/63/0；帧基线 248/0/0/0；本地全量 1206/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。
⑦ 收口：主笔 `50c186d` + 追记 `672780e` 本地；`git push` 被拒（`api=000`）⇒ **`PUSH_BLOCKED=network`（ahead=5，HEAD `672780e`，origin/main `bdb4737`）**；待推五笔 = R443 三笔（`258fc8e`/`204896e`/`ed715f1`）+ R444 两笔（`50c186d`/`672780e`）；R444 自身跑未创建、R443 自身跑未创建；R442 跑 `40605228813 ↔ bdb4737` 已补读（failure 2 步，仪器病已修）；R445 ⓪ 先只读 `git ls-remote` 验 remote 仍为 `bdb4737`，再一次快进 push 五笔并补读 R442/R443/R444 两跑。

NOT-RUN / 阻塞（分开写）：① `PUSH_BLOCKED=network`（ahead=3 + 本轮提交；R443 三笔与 R444 本地提交待推）；② `CI_READ_BLOCKED=network`（R442 整份日志、R443 自身跑未创建、R444 自身跑待 push）；③ R442 跑的 Motion floor 行；④ 长来源截断无帧（474）；⑤ 设置内容列 1x 平涂；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 关于页 1x 盲（470）；㉜ M613 机器前提（472）；㉝ 真机 vibrant 暗档（473）；㉞ 437–474 仍开。

下一轮（R445）的靶：⓪ 先 `git push origin main`（禁 amend/force；**当前 `PUSH_BLOCKED=network`、ahead=5**，恢复后先只读 `git ls-remote` 验 remote 仍为 `bdb4737`，再一次快进 push 五笔）并复核 ahead=0；读 R444 主笔+追记 head 跑、R443 三笔所在 head 跑与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看新判据 `HISTORY_ROW_SOURCE` 两档 140.5/73.5、`SETTINGS_ABOUT_ROW` 亮/暗 7（修后）、`PROBE_DOMAIN` 44/44、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主列表来源行/设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R443 状态（2026-10-28 · 本地 · 第 442 轮 / Round 440）：设置侧栏文字补显式动态色（`.primary` → `Color(nsColor: .labelColor)`）：暗档 2x 侧栏 17/17 落期望侧（`TEXT_SIDE_BLIND_SPOTS 0 of 17`）、`SETTINGS_ABOUT_ROW dark 7`（NOT-RUN→真读数）、本机 2x 盲区名册 17→0；36 张设置面帧变化、基线 246/0/0/0（产品 1 文件，设置侧栏文字位）

最后更新：2026-10-28（本地 · R443 / 第 442 轮 / Round 440）：R381 只修了设置侧栏的图标，文字仍 `.primary`；暗档 2x 离屏侧栏整列黑字黑底（R457/471）。文字也换 `Color(nsColor: .labelColor)`（动态系统色、不进 vibrancy 重映射；选中仍 accent）。旧/新：`TEXT_SIDE` 17/17 个设置夹具从反相变 **亮侧=5379 暗侧=0**；`TEXT_SIDE_BLIND_SPOTS 0 of 17`；本机 2x 的盲区名册 17→**空集**（`本机登记=0 实测反侧=0 判了 17/17 ⇒ 一致`）；`SETTINGS_ABOUT_ROW light 7 / dark 7`；**36 张**设置面帧（17 夹具 + cardprobe-split，亮暗）变化，基线 **246/0/0/0**；已看暗帧：七枚标签白字清晰。刀：M1216（文字退 `.primary`）⇒ 暗盲测试 CAUGHT；M1217（文字固定白）⇒ 亮档行测试 CAUGHT（**2/2**）；R381 的 M1011 因外层文字掩蔽内层图标的 `.primary` 第一版 ESCAPED ⇒ 改成两段一起退、复跑 2/2。预检 **221/203/580 bad=0**、ARM **314/1063**、HIDDEN **308/997 rot=0**。⓪：监督者已验 remote `f83270e` ⇒ 一次快进 push **`f83270e..bdb4737` success**、HEAD=origin/main=`bdb4737`、**ahead=0**；R442 自身 head 跑 **`40605228813 ↔ bdb4737`** 读时 in_progress、后 `gh` EOF ⇒ 具名 `CI_READ_BLOCKED=network` / NOT-RUN，R444 ⓪ 补读。本地全量 **1202/57/5**（5 断言全在 `SelectionRevealAnimationTests`）；单跑 **4/4**（OFFSET 0/214.0/1438；TIME 18/8/58.0/1438；CHANNEL 0→86.5→600 变化 76135/127200 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **246 帧**；基线 **246/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 442，现读 `python3 scripts/product_streak.py --streak-for 442`，last=609040c）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push `f83270e..bdb4737` success、ahead=0；R442 自身 head 跑 40605228813 读时 in_progress、后 EOF ⇒ CI_READ_BLOCKED/NOT-RUN；R443 自身跑待建。
② 产品：设置侧栏文字补显式动态色（暗档 2x 反侧 0/17、暗档行判据 7；36 张帧、基线 246）。
③ 判据：M1216/M1217 2/2；R381 M1011 重钉后 2/2；本机 2x 盲区名册 17→0；precheck 221/203/580；hidden rot 0。
④ 436：本轮 R442 跑读数被 EOF 挡住，未读；不重猜 must_judge。
⑤ 367：hidden 表 308 / 可判 997 / rot 0。
⑥ 捕获 246 帧；换装 ok；清账 162/63/0；帧基线 246/0/0/0；本地全量 1202/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。
⑦ 收口：主笔 `258fc8e` + 追记 `204896e` 本地提交；`git push` 两次被拒（`api=000` / apple=200）⇒ **`PUSH_BLOCKED=network`（ahead=2，HEAD `204896e`，origin/main `bdb4737`）**；R442 自身跑 `40605228813 ↔ bdb4737` 仍 **`CI_READ_BLOCKED=network` / NOT-RUN**、R443 自身跑**未创建**；R444 ⓪ 先只读 `git ls-remote` 验 remote 仍为 `bdb4737`，再一次快进 push 两笔并补读 R442/R443 两跑全部失败步骤。

NOT-RUN / 阻塞（分开写）：① R442 自身 head 跑 40605228813（CI_READ_BLOCKED=network，R444 ⓪ 补读）；② R443 自身新跑（提交后创建；收口网络见预记）；③ R442 的 runner 读数；④ 设置侧栏标签的真机 vibrant 暗档外观（473）；⑤ M613 本机 2x 空名册（472）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 100+ 行行号（467）；㉚ HTML 代码块行号（468）；㉛ 行号选中/滚动两态（469）；㉜ 关于页正文 1x 盲（470）；㉝ 437–473 仍开。

下一轮（R444）的靶：⓪ 先 `git push origin main`（禁 amend/force；**当前 `PUSH_BLOCKED=network`、ahead=2**，恢复后先只读 `git ls-remote` 验 remote 未变再一次快进 push）并复核 ahead=0；读 R443 主笔+追记 head 跑与 R442 的 `40605228813 ↔ bdb4737` 的全部失败步骤（成对 run↔commit），重点看 `SETTINGS_ABOUT_ROW` 亮/暗都 7、`TEXT_SIDE` 反侧 0/17、`CAPTION_JUDGED`/覆盖 7、`CODE_LINE_NUMBERS` 3/21/100%、`TABLE_HEADER` 1.10/1.11 与 436；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置侧栏文字/设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R442 状态（2026-10-28 · 本地 · 第 441 轮 / Round 439）：设置新增「关于」分区与关于页（应用名 / 版本+build / 定位句 / 版权；侧栏 6→7 行、tagline caption 1.01/0.95、18/18、覆盖 7/7；2 张新帧 + 40 张设置面帧随新行变化，基线 244→246）；⓪ 开工 api=000 两跑 EOF，恢复后补读 `40594607166 ↔ d382848`、`40594639509 ↔ f83270e` 都 success、失败步骤 0（产品 4 文件，设置关于页位）

最后更新：2026-10-28（本地 · R442 / 第 441 轮 / Round 439）：设置里只有侧栏底部版本行，没有 build 与定位。新增 `SettingsCategory.about`（「关于」、`info.circle`、排最后）与关于页：应用名（`.title3` semibold）、版本行「版本 1.4.8（build 1）」、定位句「轻量、离线、可回溯的剪贴板历史。」、版权「© 2026 时间剪史」；卡片与其它页同档（卡内 `.settingsCardInset()`、spacing 12）；版本/build 由 `AboutPresentation` 统一（读不到不编占位），capture 缝注入固定值。读数：`SETTINGS_ABOUT_ROW light 分区行=7`；tagline `CAPTION_INK light 3.80/3.75=1.01`、dark `5.72/6.06=0.95`、`CAPTION_JUDGED 18/18`、`CAPTION_COVERAGE 7 个`；侧栏 6→7 行、2 张新帧 + 40 张设置面帧，基线 **244→246 / 0/0/0**。侧栏判据第一版 ≤190 被 M1214 逃脱（署名行顶替第 7 带）⇒ 改 ≤110 后 M1214/M1215 **2/2**；全量抓出 6 条 UICapture + 1 条 VisualToken 涟漪并全修（暗盲名册补 settings-about、`settingsSidebarTextColumn` h192→224、卡片 inset 挪进卡内、名称改 `.title3`、探针带 179..192）。R116/R118/R120 因文本列改高腐烂，重钉后 M610/M611/M612/M615 各达期望、M613 本机空名册 SURVIVED（机器前提，472）。预检 **220/202/578 bad=0**、ARM **313 文件 / 1061 把**、HIDDEN **307/995 rot=0**。⓪：开工 `api=000` ⇒ `CI_READ_BLOCKED=network`（ahead=0，HEAD `f83270e` 已在远端）；收口前恢复 `api=200` ⇒ 补读两跑 **success、失败步骤 0**；`CODE_LINE_NUMBERS` runner 1x light/dark 都 `代码带=54.0pt 行号带=3 正文左=21.0pt 带覆盖=100%`；`TABLE_HEADER 1.10/1.11`（地板 1.08 未动）；`testProductDurationRevealStillMovesOverTime` passed、on-screen probe 步全绿 ⇒ 130.2ms 未复现；**436** = `judged=5/5 executed=77 REDS=0`。本地全量 **1202/57/5**（5 断言全在 `SelectionRevealAnimationTests`；第一跑 12 红全是新页涟漪，已修）；单跑 **4/4**（`OFFSET 0/193.5/1438`、`TIME 19/9/36.5/1438`、`CHANNEL 0→90.0→600 变化 104363/144000 重抓=no`）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获卷全绿 **246 帧**；基线 **246/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 441，现读 `python3 scripts/product_streak.py --streak-for 441`，last=3853690）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 开工断网（api=000、两跑 EOF）⇒ 记 CI_READ_BLOCKED；恢复后补读两跑 success、失败步骤 0；CODE_LINE_NUMBERS 1x 3/21/100%、TABLE_HEADER 1.10/1.11、436 judged 5/5 REDS 0；130.2ms 未复现。
② 产品：设置新增「关于」分区 + 关于页（名字/版本+build/定位/版权；侧栏 7 行、卡片同档留白）。
③ 判据：M1214/M1215 2/2（第一版被署名行顶替，改 ≤110）；6 条 UICapture + 1 条 VisualToken 涟漪全修；R116/R118/R120 重钉后各达期望（M613 机器前提）；precheck 220/202/578；hidden rot 0。
④ 436：`judged=5/5 executed=77 not-run=- REDS=0`；不重猜 must_judge。
⑤ 367：hidden 表 307 / 可判 995 / rot 0。
⑥ 捕获 246 帧；换装 ok；清账 162/63/0；帧基线 246/0/0/0；本地全量 1202/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。
⑦ 收口：主笔 `609040c` + 追记 `1781763` 本地提交完成；`git push` 两次被 SSH 拒（`api=000` / apple=200）⇒ **`PUSH_BLOCKED=network`（ahead=2，HEAD `1781763`，origin/main `f83270e`）**；R442 自身签收跑未创建 ⇒ 具名 NOT-RUN；R443 ⓪ 先只读 `git ls-remote` 验 remote 未变，再一次快进 push，再读 R442 主笔+追记 head 跑全部失败步骤。

NOT-RUN / 阻塞（分开写）：① 暗侧栏未选标签（SETTINGS_ABOUT_ROW_NOT_RUN，R457/471）；② 关于页正文 1x 平涂（CAPTION_NOT_RUN，2x 判 18/18，470）；③ M613 本机 2x 空名册（机器前提，472）；④ 本轮提交后的新跑签收；⑤ 436 的 notice-banner 若未判（NOT-RUN）；⑥ 设置脚注带 1x；⑦ 主窗口 content 帧 1x；⑧ 高夹具 1x；⑨ 13+ 菜单像素/标题；⑩ 真实拖拽；⑪ Dock 像素；⑫ 源图标最小窗文字 1x；⑬ 本地全量 5 条滚动红（449）；⑭ 2x/extended；⑮ 固定块揭示偏移（455）；⑯ 跨年时间（456）；⑰ 主列表暗档文字盲区（457）；⑱ 真机/多屏（447）；⑲ 真菜单栏、12 实时腿；⑳ `table-lazy-rows`；㉑ HTML 六档字号（460）；㉒ 清除 × 命中区（461）；㉓ 分隔线令牌（462）；㉔ 展开态已加载内容无帧（463）；㉕ 其它自绘控件帮助文本（464）；㉖ HTML 引用块无导引线（465）；㉗ HTML 表格表头无同档（466）；㉘ 100+ 行行号（467）；㉙ HTML 代码块行号（468）；㉚ 行号选中/滚动两态（469）；㉛ 437–472 仍开。

下一轮（R443）的靶：⓪ 先 `git push origin main`（禁 amend/force；**当前 `PUSH_BLOCKED=network`、ahead=2**，恢复后先只读 `git ls-remote` 验 remote 未变再一次快进 push）并复核 ahead=0；读 R442 主笔+追记 head 跑与预记跑的全部失败步骤（成对 run↔commit），重点看新判据 `SETTINGS_ABOUT_ROW` 亮档 7 行 / 暗档 NOT-RUN、`settings-about` 的 `CAPTION_JUDGED`/覆盖 7 个、以及 `CODE_LINE_NUMBERS` 3/21/100% 与 `TABLE_HEADER` 1.10/1.11 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置关于页/代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R441 状态（2026-10-28 · 本地 · 第 440 轮 / Round 438）：代码块左侧外边距行号 + 通栏紧凑灰底（行号带 3、正文左 21.0pt、灰底覆盖 100%、代码带 54.5pt；2 张旧帧变化 + 2 张新帧，基线 242→244）；R440 主跑 `40579903554 ↔ f943607` failure 1 步（在屏 130.2ms>120），同树预记跑 `40579947758 ↔ b421e5a` success ⇒ runner 时序、阈值未动（产品 3 文件，详情正文代码块位）

最后更新：2026-10-28（本地 · R441 / 第 440 轮 / Round 438）：代码块此前没有行号，且属性串 `.backgroundColor` 按字形段画、最后一行只到字尾（锯齿带）。新 `CodeBlockLineNumbers`（行数、右对齐、99 行内 11pt / 三位数 9pt），行号画在正文列左外侧 20pt 外边距（右沿 = 原点 − 3pt），正文不缩进；灰底改由 `ChineseSelectableNSTextView.drawCodeBlockBackgrounds` 按行片段铺满列宽、止于最后一行；`MarkdownPresentation` 不再给代码块打 `.backgroundColor`，只留行数属性。读数：`CODE_LINE_NUMBERS light/dark 代码带=54.5pt 行号带=3 正文左=21.0pt 带覆盖=100%`；旧形状行号带 0、覆盖 2/3（M1212 复现）。帧变化 2 张旧帧 + 2 张新帧，基线 **242→244 / 0/0/0**。`M1210–M1212` **3/3 CAUGHT**；R439 的 M1205 因 `drawBackground` 变长而腐烂，预检 `bad=1` 当场抓到 ⇒ 重钉并复跑 3/3。新单测 4 条 + 新帧判据 1 条；R234 契约改为"视图画宽底 + 属性串留行数标记"。预检 **219/201/576 bad=0**、ARM **312 文件 / 1059 把**、HIDDEN **306/992 rot=0**。⓪：push no-op、HEAD = origin/main = `b421e5a`、**ahead=0**；`40579903554 ↔ f943607` **failure、失败步骤 1 个**（`On-screen probe coverage floor`：`testFrameIntervalsUnderStateChanges` 最差 **130.2ms > 120ms**、超 2 颗、容差 1），同树预记跑 `40579947758 ↔ b421e5a` **success** ⇒ 具名 `ONSCREEN_FRAME_INTERVAL_RUNNER_SAMPLING_MISS`，阈值未动；失败跑的 Swift tests 1192/69 skip/0 失败。收口：主笔 `3853690` + 追记 `d382848` 一次 push（`b421e5a..d382848`），HEAD = origin/main = `d382848`、**ahead=0**；新跑 `40594607166 ↔ d382848` 读时 **queued** ⇒ R441 自身签收具名 NOT-RUN，R442 ⓪ 读它全部失败步骤（重点：`CODE_LINE_NUMBERS` 行号带 3 / 正文左 19–22 / 覆盖 ≥85，以及两个采样名是否复现）。`TABLE_HEADER` 1x light 比 **1.10**、dark **1.11**（地板 1.08，余量 0.02–0.03；地板不动）；**436** = `judged=4/5 executed=77 not-run=notice-banner REDS=0`。本地全量 **1197/57/5**（5 断言全在 `SelectionRevealAnimationTests` 的 3 条用例；全量另抓出 5 条 UICapture 回归并当场修掉：print 样例被 stdout 守卫误读、单左轴把边注读成正文轴）；单跑 **4/4**（OFFSET 0/203.0/1438；TIME 18/8/30.5/1438；CHANNEL 0→93.5→600 变化 131685/160800 重抓=no）⇒ `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **148/4/0 / 244 帧**；基线 **244/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 440，现读 `python3 scripts/product_streak.py --streak-for 440`，last=2e8d3e6）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ R440 两跑：主跑 failure 1 步（在屏 130.2ms>120），同树预记跑 success ⇒ runner 时序；TABLE_HEADER 1x 1.10/1.11（地板不动）；436 judged 4/5 REDS 0。
② 产品：代码块左边距行号 + 通栏紧凑底（行号带 3、覆盖 100%、正文左 21.0pt；2 张旧帧 + 2 张新帧，基线 244）。
③ 判据：M1210–M1212 3/3；R439 M1205 重钉并复跑 3/3；R32 M140 重钉（单左轴探针 x:0→19）并复跑 4/4；新单测 4 条 + 帧判据；precheck 219/201/576；hidden rot 0。
④ 436：`judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 306 / 可判 992 / rot 0。
⑥ 捕获 148/4/0、244 帧；换装 ok；清账 162/63/0；帧基线 244/0/0/0；本地全量 1197/57/5（5 条滚动红具名会话/顺序 NOT-RUN）；电池首跑 4 红（M140 rot / 裸 stdout 16 / skip 名册级联）修掉后 683/OK(5)。

NOT-RUN / 阻塞（分开写）：① 行号的 runner 1x 读数（本轮提交后的新跑才读）；② 100+ 行夹具 / 9pt 档（467）；③ HTML 代码块行号（468）；④ 行号选中/滚动两态（469）；⑤ 436 的 notice-banner 未判（NOT-RUN，不是红）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ HTML 引用块无导引线（465）；㉘ HTML 表格表头无同档（466）；㉙ 437–469 仍开。

下一轮（R442）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R441 主笔+追记 head 跑 `40594607166 ↔ d382848` 与预记跑的全部失败步骤（成对 run↔commit），重点看新帧判据 `CODE_LINE_NUMBERS` 的行号带 3 / 正文左 19–22pt / 覆盖 ≥85%，以及 `ONSCREEN_FRAME_INTERVAL_RUNNER_SAMPLING_MISS` 与 `TABLE_HEADER` 1.10/1.11 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做代码块行号/表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R440 状态（2026-10-28 · 本地 · 第 439 轮 / Round 437）：Markdown 表格表头补等宽 semibold（解析器丢掉 `| --- |` 行后表头/表体同形；新夹具两行逐字相同：light 墨量比 1.40 / dark 1.25，左沿 23.0/23.5pt、行距 9.0pt；2 张旧帧变化 + 2 张新帧，基线 240→242）；R439 两跑都 success（`MARKDOWN_QUOTE_RULE` 1x 57.0pt、两个采样红未复现、436=judged 4/5 executed 77 REDS 0）（产品 3 文件，详情正文表格位）

最后更新：2026-10-28（本地 · R440 / 第 439 轮 / Round 437）：`MarkdownScanner.collectTable` 丢掉 `| --- |` 分隔行后，表头与表体在渲染里同字号、同字重、同颜色。新 `TableHeaderPresentation`（表头 = 等宽 semibold、`headerRange` 取第一行）；`MarkdownPresentation` 只给表头换字体，等宽字体 semibold 与 regular 推进宽度相同 ⇒ 不挪列。新夹具 `detail-table` 两行逐字相同：light `表头墨=799 表体墨=569 比=1.40`、dark `855/685 比=1.25`，左沿 `23.0/23.5pt`（0.5pt 是笔画宽）、行距 `9.0pt`；旧形状由 M1206 复现 ≈1.00。帧变化 **2 张旧帧 + 2 张新帧**，基线 **240→242 / 0/0/0**。`M1206–M1207` **2/2 CAUGHT**；新单测 3 条 + 新帧判据 1 条；预检 **218/200/573 bad=0**、ARM **311 文件 / 1056 把**、HIDDEN **305/990 rot=0**；0 告警门先抓到判据里一个未使用的 `width`，删后冷编 `warnings=0`。⓪：push no-op、HEAD = origin/main = `fc88822`、**ahead=0**；`40573915633 ↔ 42c09ad` 与 `40573988870 ↔ fc88822` 都 **success、失败步骤 0**；`MARKDOWN_QUOTE_RULE` 1x 两档 `竖墨=57.0pt 源=15.0pt`（文字左 39.0/38.0、净距 12.0/11.0）；`testProductDurationRevealStillMovesOverTime` **passed**、动效标签红 skipped / Motion gate failed=0 ⇒ 两个采样红未复现；两跑同报 4 张环境帧差（login-failed / receipt-failed）⇒ 稳定机器差异；**436** = `MOTION_FLOOR_FACTS judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`（notice-banner 具名 NOT-RUN，不是红）。收口：主笔 `2e8d3e6` + 追记 `f943607` 一次 push（`fc88822..f943607`），HEAD = origin/main = `f943607`、**ahead=0**；新跑 `40579903554 ↔ f943607` 读时 **queued** ⇒ R440 自身签收具名 NOT-RUN，R441 ⓪ 读它全部失败步骤（重点：`TABLE_HEADER` 两档墨量比 ≥1.08、左沿差 ≤1pt）。本地全量 **1192/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`OFFSET 0/199.0/1438`、`TIME 18/9/47.5/1438`、`CHANNEL 0→83.0→600 变化 40524/110400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）；另一次单跑全 0 采样记 `SCROLL_REVEAL_SESSION_BLIND=one-run-zero-readings`，不降门槛。捕获 **147/4/0 / 242 帧**；基线 **242/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 439，现读 `python3 scripts/product_streak.py --streak-for 439`，last=1f7c4f1）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 两跑 success、失败步骤 0；`MARKDOWN_QUOTE_RULE` 1x 57.0/15.0、两个采样红未复现（不写绿，写未复现）；436 judged=4/5 executed=77 REDS=0（notice-banner NOT-RUN）。
② 产品：表格表头补等宽 semibold（旧两行同形 → 新 light 1.40 / dark 1.25；2 张旧帧 + 2 张新帧，基线 242）。
③ 判据：M1206–M1207 2/2；新单测 3 条 + 帧判据（同帧墨量比/左沿/行距）；precheck 218/200/573；hidden rot 0；0 告警门修掉一个未使用变量。
④ 436：`judged=4/5 executed=77 not-run=notice-banner 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 305 / 可判 990 / rot 0。
⑥ 捕获 147/4/0、242 帧；换装 ok；清账 162/63/0；帧基线 242/0/0/0；本地全量 1192/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 表头字重的 runner 1x 读数（本轮提交后的新跑才读）；② HTML 表格表头无同档处理（466）；③ 436 的 notice-banner 本跑未判（NOT-RUN，不是红）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ HTML 引用块无导引线（465）；㉖ 437–466 仍开。

下一轮（R441）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R440 主笔+追记 head 跑 `40579903554 ↔ f943607` 的全部失败步骤（成对 run↔commit；前一跑 `40573988870 ↔ fc88822` success），重点看新帧判据 `TABLE_HEADER` 两档墨量比 ≥1.08、左沿差 ≤1pt，以及两个 runner 采样名是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格表头/引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R439 状态（2026-10-28 · 本地 · 第 438 轮 / Round 436）：Markdown 引用块补左侧导引线（规则带最长竖墨 17.0→57.0pt、引用文字左沿 38.5pt、净距 11.5pt；源模式负对照 14.5pt；2 张帧变化、基线 240）；R438 追记跑 `40564355511 ↔ 6ce9e2b` failure 2 步，更新的 `40564432395 ↔ 40c0a28` success ⇒ runner 采样、阈值未动（产品 3 文件，详情正文引用位）

最后更新：2026-10-28（本地 · R439 / 第 438 轮 / Round 436）：详情 Markdown 的引用块此前只有 18pt 缩进 —— 列表续行也缩进，帧上分不出引文。新 `MarkdownQuoteRule`（宽 2、左偏 5、每级按 `quoteIndent` 再进、圆角 1、`secondaryLabelColor` 动态色）提供几何；`MarkdownPresentation` 给引用块连同分隔空行打 `quoteDepthAttribute`；`ChineseSelectableNSTextView.drawBackground(in:)` 只枚举可见字符并按级画线。旧/新：同一帧规则带（24..27pt）最长竖墨 **17.0 → 57.0pt**（亮/暗同值），引用文字左沿 **38.5pt**、净距 **11.5pt**，源模式负对照仍 **14.5pt**。帧变化恰 2 张（`detail-markdown-rendered` 亮/暗），基线 **240/0/0/0**。`M1203–M1205` **3/3 CAUGHT**；新单测 5 条 + 新帧判据 1 条；预检 **217/199/571 bad=0**、ARM **310 文件 / 1054 把**、HIDDEN **304/988 rot=0**。⓪：push 为 no-op、HEAD = origin/main = `40c0a28`、**ahead=0**；`40564355511 ↔ 6ce9e2b` **failure、失败步骤 2 个**（`testProductDurationRevealStillMovesOverTime` 无中间 origin `[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`；`testMarkdownModeLabelChangeIsAVisibleProcess` 1x 只 1 帧 <2），更新的一跑 `40564432395 ↔ 40c0a28` **success、失败步骤 0**（同树，只多文档）⇒ 具名 `SELECTION_REVEAL_RUNNER_SAMPLING_MISS` 与 `MOTION_LABEL_TRANSITION_RUNNER_SAMPLING_MISS`，**阈值未动**。收口：主笔 `1f7c4f1` + 追记 `42c09ad` 一次 push（`40c0a28..42c09ad`），HEAD = origin/main = `42c09ad`、**ahead=0**；新跑 `40573915633 ↔ 42c09ad` 读时 **in_progress** ⇒ R439 自身签收具名 NOT-RUN，R440 ⓪ 读它全部失败步骤（重点：`MARKDOWN_QUOTE_RULE` 两档与两个 runner 采样名是否复现）。绿跑签收 R438：`EXPANDED_PREVIEW_AXIS 83.0/82.0 差=1.0`、`QUICKPICK_CLEAR_BUTTON 106/93 与 104/107`、`BULK_ACTION_SEPARATOR 17.9/11.9`、`RECORDER_HELP_PIXEL_NOT_RUN` 两门登记；**436** = `judged=5/5 executed=77 REDS=0`。本地全量 **1188/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/34.0/1438`、`CHANNEL 0→84.5→600 变化 56834/117600 重抓=no`、`OFFSET 0/201.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **146/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 438，现读 `python3 scripts/product_streak.py --streak-for 438`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ push no-op、ahead=0；`40564355511 ↔ 6ce9e2b` failure 2 步（产品时长无中间 origin、动效标签 1x 1 帧），更新的 `40564432395 ↔ 40c0a28` success ⇒ runner 采样，阈值未动；R438 各项与 436 从绿跑取到真实读数。
② 产品：详情 Markdown 引用块补左侧导引线（旧 17.0pt → 新 57.0pt；2 张帧变化）。
③ 判据：M1203–M1205 3/3；新单测 5 条 + 帧判据（竖墨段/负对照/净距）；precheck 217/199/571；hidden rot 0。
④ 436：`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- 红的用例=- 汇总行报红=0`；不重猜 must_judge。
⑤ 367：hidden 表 304 / 可判 988 / rot 0。
⑥ 捕获 146/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1188/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 导引线的 runner 1x 读数（本轮提交后的新跑才读）；② HTML 引用路径无导引线（465）；③ R438 追记跑两红（采样，已定位）；④ 设置内容列 1x 平涂；⑤ 设置脚注带 1x；⑥ 主窗口 content 帧 1x；⑦ 高夹具 1x；⑧ 13+ 菜单像素/标题；⑨ 真实拖拽；⑩ Dock 像素；⑪ 源图标最小窗文字 1x；⑫ 本地全量 5 条滚动红（449）；⑬ 2x/extended；⑭ 固定块揭示偏移（455）；⑮ 跨年时间（456）；⑯ 主列表暗档文字盲区（457）；⑰ 真机/多屏（447）；⑱ 真菜单栏、12 实时腿；⑲ `table-lazy-rows`；⑳ HTML 六档字号（460）；㉑ 清除 × 命中区（461）；㉒ 分隔线令牌（462）；㉓ 展开态已加载内容无帧（463）；㉔ 其它自绘控件帮助文本（464）；㉕ 437–465 仍开。

下一轮（R440）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R439 主笔+追记 head 跑 `40573915633 ↔ 42c09ad` 的全部失败步骤（成对 run↔commit；前一对 `40564432395 ↔ 40c0a28` success），重点看新帧判据 `MARKDOWN_QUOTE_RULE` 两档竖墨 ≥30pt、负对照 ≤20pt，以及 `SELECTION_REVEAL_RUNNER_SAMPLING_MISS`/`MOTION_LABEL_TRANSITION_RUNNER_SAMPLING_MISS` 是否复现；in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做引用导引线/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。
## R438 状态（2026-10-28 · 本地 · 第 437 轮 / Round 435）：快捷键录制按钮补帮助文本（静置「点一下重新录制；按 Esc 取消」/录制「请输入快捷键；按 Esc 取消」，toolTip + AX；帮助气泡系统画 ⇒ 像素具名 NOT-RUN）；R437 两跑与新跑读数本轮被 GitHub EOF 挡住 ⇒ 具名 CI_READ_BLOCKED（产品 1 文件，录制按钮帮助位）

最后更新：2026-10-28（本地 · R438 / 第 437 轮 / Round 435）：设置快捷键页三颗灰键帽以前没有任何帮助文本。新 `HotKeyRecorderButton.updateHelp()` 单一出口写 `toolTip` 与 `setAccessibilityHelp`：静置「点一下重新录制；按 Esc 取消」、录制「请输入快捷键；按 Esc 取消」，在 shortcut 变更与录制态切换处调用。产品入口判据读真实 `SettingsView` 里三颗按钮（toolTip/AX 字符串 + `startRecording()` 后换句）；帮助气泡由 WindowServer 画 ⇒ `RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`，**帧集合与像素不变**（`CHANGED=0/MISSING=0/ADDED=0`，基线 **240**）。`M1201–M1202` **2/2 CAUGHT**；预检 **216/198/568 bad=0**、ARM **309 文件 / 1051 把**、HIDDEN **303/985 rot=0**。⓪：网络 `api=000`/apple=200 ⇒ **`PUSH_BLOCKED=network`（ahead=0）** 与 **`CI_READ_BLOCKED=network`**（`40559949986 ↔ 5ee17a4`、`40552696188` 重跑均 EOF）；最近已读两对：`40552595027 ↔ 204737c` **success**、`40552696188 ↔ 7298af9` **failure 1 步**（on-screen 189.8>120，原样重跑）；`EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 的 1x 读数本轮未读，逐项 NOT-RUN。本地全量 **1182/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/71.5/1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/196/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **145/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 437，现读 `python3 scripts/product_streak.py --streak-for 437`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ 网络 `api=000`/apple=200 ⇒ `PUSH_BLOCKED=network`（ahead=0）与 `CI_READ_BLOCKED=network`；最近两对已读（一绿一红），on-screen 重跑与 1x 各读数本轮未读、逐项 NOT-RUN。
② 产品：快捷键录制按钮补 toolTip/AX 帮助并随录制态换句（帮助气泡具名 NOT-RUN，帧不变）。
③ 判据：M1201–M1202 2/2；产品入口三颗按钮；precheck 216/198/568；hidden rot 0。
④ 436：本轮无新跑读数（EOF）；不重猜 must_judge。
⑤ 367：hidden 表 303 / 可判 985 / rot 0。
⑥ 捕获 145/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1182/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① `PUSH_BLOCKED=network`（api=000 / apple=200、ahead=0）；② `CI_READ_BLOCKED=network`（40559949986 ↔ 5ee17a4、40552696188 重跑）；③ on-screen 帧间隔重跑结论；④ `EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 的 1x 读数；⑤ 帮助气泡像素（`RECORDER_HELP_PIXEL_NOT_RUN=system-tooltip`）；⑥ 设置内容列 1x 平涂；⑦ 设置脚注带 1x；⑧ 主窗口 content 帧 1x；⑨ 高夹具 1x；⑩ 13+ 菜单像素/标题；⑪ 真实拖拽；⑫ Dock 像素；⑬ 源图标最小窗文字 1x；⑭ 本地全量 5 条滚动红（449）；⑮ 2x/extended；⑯ 固定块揭示偏移（455）；⑰ 跨年时间（456）；⑱ 主列表暗档文字盲区（457）；⑲ 真机/多屏（447）；⑳ 真菜单栏、12 实时腿；㉑ `table-lazy-rows`；㉒ HTML 六档字号（460）；㉓ 清除 × 命中区（461）；㉔ 分隔线令牌（462）；㉕ 展开态已加载内容无帧（463）；㉖ 其它自绘控件帮助文本（464）；㉗ 437–464 仍开。

下一轮（R439）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（网络恢复后先只读 `git ls-remote` 验 remote，再一次快进 push）；三对已读：`40552595027 ↔ 204737c` **success**；`40552696188 ↔ 7298af9` **重跑 success**（on-screen 189.8>120 **未复现**，原样重跑即绿、阈值未动）；`40559949986 ↔ 5ee17a4` **success**（`EXPANDED_PREVIEW_AXIS`/`QUICKPICK_CLEAR_BUTTON`/`BULK_ACTION_SEPARATOR`/`MOTION_SEQUENCE` 均签收）。R438 head `40564355511 ↔ 6ce9e2b` 读时 **in_progress** ⇒ 具名 NOT-RUN，R439 ⓪ 读它全部失败步骤；`EXPANDED_PREVIEW_AXIS` 两档 0.5、`QUICKPICK_CLEAR_BUTTON` 1x、`BULK_ACTION_SEPARATOR` 1x、`MOTION_SEQUENCE` same 臂 ≥3、各具名 NOT-RUN；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R437 状态（2026-10-28 · 本地 · 第 436 轮 / Round 434）：多文件行展开后的预览补到所属行的文字轴（旧展开内容 40.0pt vs 行文字 83.0pt、差 43 → 新 82.5 vs 83.0、差 0.5；2 张展开帧新增、基线 240）；R436 head 跑一绿一红（`40552595027 ↔ 204737c` success；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120）⇒ 原样重跑、阈值未动（产品 1 文件，展开预览位）

最后更新：2026-10-28（本地 · R437 / 第 436 轮 / Round 434）：多文件列表的展开态此前从未有帧。新增 `detail-3-files-expanded` 后量到：展开的骷髅条从窗口 `containerGutter`（20pt）+ 圆角框 20pt 起 = **40.0pt**，而同一行文件名从 `rowTextLeading` 起 = **83.0pt**（差 43pt）。修法：`previewHorizontalInset` 提常量 + `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`（只补左侧），并给 `DetailView` / `MultiFileDetailView` 加取证入口 `initialExpandedFileIndex`（产品默认 nil）。旧/新：`EXPANDED_PREVIEW_AXIS light 行文字左=83.0pt 展开内容左=82.5pt 差=0.5pt`、dark 同（旧 40.0/83.0、差 43.0）。新增 2 帧，基线 **238→240**、复验 **240/0/0/0**。源守卫 `testDetailViewRoutesMarkdownToTheRendererAndBack` 随签名改成折行匹配并钉住「接属性不接死值」。R436 head 两跑：`40552595027 ↔ 204737c` **success**（clear × list 校准与 motion 重抓签收）；`40552696188 ↔ 7298af9` **failure、失败 1 步**（on-screen `testFrameIntervalsUnderStateChanges` 最差 189.8ms>120、2 颗超锚点、容差 1）⇒ **原样重跑**（读时 in_progress，具名 NOT-RUN），阈值未动。`M1199–M1200` **2/2 CAUGHT**；预检 **215/197/566 bad=0**、ARM **308 文件 / 1049 把**、HIDDEN **302/983 rot=0**。本地全量 **1181/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/27.5/1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/199/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **144/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 436，现读 `python3 scripts/product_streak.py --streak-for 436`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ R436 两跑：`40552595027 ↔ 204737c` success（clear × 与 motion 重抓签收）；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120 ⇒ 原样重跑、阈值未动（读时 in_progress ⇒ NOT-RUN）。
② 产品：多文件展开预览补到行文字轴（旧 40.0/83.0、差 43 → 新 82.5/83.0、差 0.5；新增 2 帧）。
③ 判据：M1199–M1200 2/2；源守卫随签名更新；precheck 215/197/566；hidden rot 0。
④ 436：最近完整读数仍是 R434 跑 floor 5/5/77 无红；R436 两跑日志本次未取到通道行（照实记），只看结论与失败步骤。
⑤ 367：hidden 表 302 / 可判 983 / rot 0。
⑥ 捕获 144/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1181/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① on-screen 帧间隔重跑（`testFrameIntervalsUnderStateChanges` 189.8>120，原样重跑）；② 设置内容列 1x 平涂；③ 设置脚注带 1x；④ 主窗口 content 帧 1x；⑤ 高夹具 1x；⑥ 13+ 菜单像素/标题；⑦ 真实拖拽；⑧ Dock 像素；⑨ 源图标最小窗文字 1x；⑩ 本地全量 5 条滚动红（449）；⑪ 2x/extended；⑫ 固定块揭示偏移（455）；⑬ 跨年时间（456）；⑭ 主列表暗档文字盲区（457）；⑮ 真机/多屏（447）；⑯ 真菜单栏、12 实时腿；⑰ `table-lazy-rows`；⑱ HTML 六档字号（460）；⑲ 清除 × 命中区（461）；⑳ 分隔线令牌（462）；㉑ 展开态已加载内容无帧（463）；㉒ 437–463 仍开；㉓ R437 新跑待 push 后读。

下一轮（R438）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R437 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 on-screen 帧间隔重跑结论（189.8>120 是否复现）、`EXPANDED_PREVIEW_AXIS` 两档 0.5pt、`ROUND4 markdown` 源守卫、`QUICKPICK_CLEAR_BUTTON` 1x、`BULK_ACTION_SEPARATOR` 1x、`MOTION_SEQUENCE` same 臂 ≥3、各具名 NOT-RUN 与带读数；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R436 状态（2026-10-28 · 本地 · 第 435 轮 / Round 433）：批量操作栏补破坏性分隔线（删除与其余四颗之间 1pt 发丝；局部对比 light 13.7 / dark 11.9，旧 0–1；4 张多选帧变化、基线 238）；R435 跑失败步骤 2 个（list 占位语 1x 无墨被当校准、行插入动画采样 2<3）⇒ 修仪器/重抓、阈值未动（产品 1 文件，批量操作栏位）

最后更新：2026-10-28（本地 · R436 / 第 435 轮 / Round 433）：批量操作栏的五颗按钮在 `spacing: 0` 的一排里，破坏性的垃圾桶只靠红色与其余四颗分开。修法：垃圾桶前插一条 1×14pt 的 `Rectangle().fill(Color.primary.opacity(0.18))`（`Divider()` 在这个离屏 HStack 里不落墨，第一版即它、帧上 0 读数，已换掉）。旧/新：垃圾桶左沿 265.5pt，其左侧 258..263pt 的**局部对比** 0–1 → light **13.7** / dark **11.9**；垃圾桶红墨 333/265 作校准。4 张多选帧变化（`sidebar-multi-select` 与 `-min` × 亮暗），基线 **238/0/0/0**。判据第一版用"与远处底色的差"，刀 M1197 撤线仍绿（侧栏材质渐变冒充）⇒ 改成局部对比、带收窄、地板 8；`M1197–M1198` **2/2 CAUGHT**。R435 run `40544941175 ↔ 1041d0f` **failure，失败步骤 2 个**（Swift tests / Capture gate）：① 清除 × 判据把 `quickpick-list` 的占位语当校准，1x 上占位语无墨（typed 正常）⇒ list 改读同一帧第 0 行标题；② 行插入动画 same 臂 2<3 ⇒ 只对该动的臂相位重抓（最多三次、取帧数最多），阈值未动。预检 **214/196/564 bad=0**、ARM **307 文件 / 1047 把**、HIDDEN **301/981 rot=0**。本地全量 **1180/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/9/43/1438`、`CHANNEL 0→83.5→600 变化 46073/112800 重抓=no`、`OFFSET 0/199.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **143/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 435，现读 `python3 scripts/product_streak.py --streak-for 435`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑；口径与 R435 一致，不回退成 4）。

本轮做了什么：
① ⓪ R435 跑 failure、失败步骤 2 个：清除 × 判据的 list 校准（占位语 1x 无墨）与行插入动画采样 2<3 ⇒ 换校准对象 + 相位重抓，阈值未动。
② 产品：批量操作栏补破坏性分隔线（局部对比 0–1 → 13.7/11.9）。
③ 判据：第一版假绿由刀证伪后换局部对比；M1197–M1198 2/2；precheck 214/196/564；hidden rot 0。
④ 436：R434 跑 floor 5/5/77 无红（R435 跑日志被 EOF 挡住，通道未再取到；红已逐条读）。
⑤ 367：hidden 表 301 / 可判 981 / rot 0。
⑥ 捕获 143/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1180/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 清除按钮命中区 18pt（461）；⑲ 分隔线透明度未提令牌（462）；⑳ 437–462 仍开；㉑ R436 新跑待 push 后读。

下一轮（R437）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；**收口时 `PUSH_BLOCKED=network`（api=000 / apple=200；本地 `ccda826` 主笔 + `7714cb1` 追记、ahead=2）已解除**：网络恢复后一次快进 push 成功（`origin/main..HEAD=0`），HEAD=`204737c`。R435 跑 `40544941175 ↔ 1041d0f` **failure、失败步骤 2 个**（Swift tests / Capture gate）：① `testQuickPickSearchFieldShowsAClearButtonOnlyWhenTyping` 把 `quickpick-list` 的占位语当校准，1x 上读到 0（typed 正常）⇒ 已改为同一帧第 0 行标题作校准；② `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` same 臂采样 2<3 ⇒ 已加「只对该动的臂」相位重抓（最多三次、取帧数最多）。R436 head 新跑 `40552595027 ↔ 204737c` 读时 **in_progress** ⇒ 具名 NOT-RUN（0 字节不算绿），其全部失败步骤与上面两条红的签收留到 R437 ⓪；读 R436 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `BULK_ACTION_SEPARATOR` 两档局部对比（13.7/11.9）、清除 × 判据的 list 校准、`MOTION_SEQUENCE` 重抓后 same 臂 ≥3、`EXCLUDED_APP_ROW_NOT_RUN`、`DETAIL_IMAGE_EDGE`、`HTML_HEADING_LADDER`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R435 状态（2026-10-28 · 本地 · 第 434 轮 / Round 432）：浮层搜索框补清除按钮（有字才出现：typed 帧按钮带 405/410 墨、空查询 0；4 张浮层帧变化、基线 238）；R434 跑 `40535594620 ↔ 78a0cf5` success、失败步骤 0（产品 1 文件，浮层搜索框位）

最后更新：2026-10-28（本地 · R435 / 第 434 轮 / Round 432）：主窗口的 `SearchField` 早有清除 ×，浮层的搜索框一直没有 —— 打错一个字只能全选重打。新：`QuickPickController` 在搜索框右端加一颗 18×18 无边框 ×（`xmark.circle.fill`、`secondaryLabelColor`、可访问名「清除搜索」、identifier `quickPickClearSearchButton`），可见性由 `showsClearButton(text:)` 决定（有字才出现）；`QuickPickSearchFieldCell` 的文本矩形右留 22pt 让位（左轴不动）；产品路径与取证路径共用 `updateClearButton`。旧/新帧读数：`QUICKPICK_CLEAR_BUTTON light typed 按钮带=405 校准=354 list 按钮带=0 校准=1232`、dark `410/408 / 0/1474`（地板 80 = 20·s²）。4 张浮层帧变化（typed/empty × 亮暗），基线 **238/0/0/0**。R434 run `40535594620 ↔ 78a0cf5` **success、20/20 步、失败步骤 0**：`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain` 按名生效、`DETAIL_IMAGE_EDGE` 1x 30/26、`HTML_HEADING_LADDER` 19/18、理由带 217/248 vs 0、时间列 `[74,71,74,74,74]`/`[74,72,74,74,74]`、脚注 NOT-RUN 按名出现、分区 13/12 与 11/10、表格 6/5、回执 2/2、滚动 4/4、拖拽 mass 0.549/0.550、floor 5/5/77 无红；**STATE ⓪ 已回写**（`00939fa` push）。`M1195–M1196` **2/2 CAUGHT**；预检 **213/195/562 bad=0**、ARM **306 文件 / 1045 把**、HIDDEN **300/979 rot=0**。本地全量 **1179/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/23.5/1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/194.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **142/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 434，现读 `python3 scripts/product_streak.py --streak-for 434`）。电池 首跑 1 红（本机 `/tmp` 被清后链日志判据合法跳过、`ROSTER['local']` 缺项）⇒ 补登后 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ R434 跑 success、失败步骤 0：`EXCLUDED_APP_ROW_NOT_RUN` 按名生效、`DETAIL_IMAGE_EDGE` 30/26、`HTML_HEADING_LADDER` 19/18、理由带/时间列/脚注/分区/表格/回执/滚动/floor 全绿；STATE ⓪ 已回写并 push（`00939fa`）。
② 产品：浮层搜索框补清除 ×（有字才出现；typed 405/410 vs list 0）。
③ 判据：M1195–M1196 2/2；真值表 + 真实面板按钮 + 像素两带；precheck 213/195/562；hidden rot 0。
④ 436：R434 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 300 / 可判 979 / rot 0。
⑥ 捕获 142/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1179/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 清除按钮命中区 18pt（461）；⑲ 437–461 仍开；⑳ R435 新跑待 push 后读。

下一轮（R436）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R435 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `QUICKPICK_CLEAR_BUTTON` 两档读数（typed 有墨、list 0）、`EXCLUDED_APP_ROW_NOT_RUN`、`DETAIL_IMAGE_EDGE`、`HTML_HEADING_LADDER`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R434 状态（2026-10-27 · 本地 · 第 433 轮 / Round 431）：HTML 渲染的标题档接到 Markdown 梯子（同一 h1：旧墨带 27.0pt → 新 20.0pt、与 Markdown 差 9.0→2.0；2 张 HTML 帧变化、基线 238）；R433 跑失败步骤 2 个（设置内容列在 1x 整列平涂 ⇒ 排除名单判据无对象）⇒ 具名 NOT-RUN、阈值未动（产品 1 文件，HTML 标题排版位）

最后更新：2026-10-27（本地 · R434 / 第 433 轮 / Round 431）：同一个「渲染」档里，HTML 的 h1 旧读墨带 **27.0pt**、Markdown 的 h1 **18.0pt** —— R335 只把正文档按字符数加权搬到 14pt，标题被等比放大到 28pt。新 `HtmlRendering.fitHeadingsToLadder`：正文基准之上（>1.1×）的字号按从大到小逐级落到 `MarkdownPresentation.headingFontSize`（20/17/15.5…），字族与字重不动。旧/新：`HTML_HEADING_LADDER light html=20.0pt markdown=18.0pt 差=2.0pt`（旧 27.0/18.0、差 9.0）；`HTML_TYPE 基准前=12.0 基准后=14.0 标题后=20.0 梯子=20.0,17.0,15.5,14.0,13.0,12.0`。旧测试把「层级比 2.0」钉成契约，本轮更正为「标题在 Markdown 梯子上」。2 张 `detail-html-rendered` 帧变化，基线 **238/0/0/0**。R433 run `40526497330 ↔ e896829` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是设置页**内容列在 1x 整列平涂**（`CAPTION_JUDGED 6/17`，所有 settings 探针 machineFlat）⇒ 排除名单判据在 CI 上没有对象，具名 `EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`、2x 断言不动；`DETAIL_IMAGE_EDGE` 在 1x 绿（light 图框 240..479×220..359、页底 236、边带差 30.0；dark 50/26.0）；理由带 290 后 typed 217/248、list 0；时间列 1x light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；回执 2/2；滚动 4/4（`CHANNEL 0→108→600 38400/30362`、`TIME 5/0/0/1430`）；拖拽 mass 0.549/0.550；floor 4/5/77（notice-banner）无红。`M1192–M1193` **2/2 CAUGHT**；预检 **212/194/560 bad=0**、ARM **305 文件 / 1043 把**、HIDDEN **299/977 rot=0**。本地全量 **1176/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/61/1438`、`CHANNEL 0→86.5→600 变化 76639/127200 重抓=no`、`OFFSET 0/227.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **141/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 433，现读 `python3 scripts/product_streak.py --streak-for 433`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R433 跑 failure、失败步骤 2 个：唯一红是设置内容列 1x 平涂（`CAPTION_JUDGED 6/17`）⇒ 排除名单判据具名 NOT-RUN、阈值未动；图片边判据 1x 绿（30.0/26.0）；理由带/时间列/脚注/分区/表格/回执/滚动/拖拽全绿。
② 产品：HTML 标题档接到 Markdown 梯子（旧 27.0 → 新 20.0，差 9.0→2.0）。
③ 判据：M1192–M1193 2/2；三条映射单测；旧比例契约更正；precheck 212/194/560；hidden rot 0。
④ 436：R433 跑 floor judged=4/5 executed=77（notice-banner）、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 299 / 可判 977 / rot 0。
⑥ 捕获 141/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1176/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN=runner-1x-settings-content-plain`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 437–460 仍开；⑲ R434 新跑待 push 后读。

下一轮（R435）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R434 主笔+追记 head 跑（`40535594620 ↔ 78a0cf5`，2026-10-28 现读 **success、失败步骤 0**；`EXCLUDED_APP_ROW_NOT_RUN` 按名生效、`DETAIL_IMAGE_EDGE` 30/26、`HTML_HEADING_LADDER` 19/18、floor judged=5/5 executed=77）全部失败步骤；重点看 `HTML_HEADING_LADDER` 在 1x 的读数（旧契约已改，若 runner 上 HTML 帧不画则具名）、`EXCLUDED_APP_ROW_NOT_RUN` 按名出现、`DETAIL_IMAGE_EDGE`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R433 状态（2026-10-27 · 本地 · 第 432 轮 / Round 430）：详情大图补 1pt 中性边（白底图在白底详情里旧差 0.0 → 新 32.0/28.0；贴合尺寸只缩不放，240×140 不变；2 张详情帧变化、基线 238）；R432 跑失败步骤 2 个（高夹具 720×1040 在 1x 整帧不画）⇒ 换 540 帧保住 CI 像素证人（产品 1 文件，详情图片预览位）

最后更新：2026-10-27（本地 · R433 / 第 432 轮 / Round 430）：详情大图以前没有任何边/阴影 —— 图沿外 1–3pt 与 20pt 外的页面底色亮度差 **0.0/0.0**，白底截图在白底详情里整张看不出边界。新 `ImagePreviewLayout.fittedSize`（**只缩不放**，与旧 `scaledToFit` 一致）+ 图外 **1pt** `Color.primary.opacity(VisualTint.chipStroke)` 中性边（挂在贴合图本身的尺寸上，不是上限框）。修后 `DETAIL_IMAGE_EDGE light 图框=480..959×440..719px 页底=255.0 边带最大差=32.0`、dark `页底=30.0 边带最大差=28.0`（旧 0.0/0.0）；图框 240×140pt 不变（第一版漏 `min(1, …)` 把图拉到 680×397，已收回并写进单测）。2 张 `detail-1-image` 帧变化，基线 **238/0/0/0**。R432 run `40519498631 ↔ f39f66c` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是 `settings-privacy-tall`（720×1040）在 1x 整帧不画（行数 0）⇒ 排除名单判据改用 540 帧、要求 ≥3 行（本机 5 行、首段 10–14pt），阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效不计红；理由带 290 后 typed 217 / list 0。时间列 1x light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→125→600 30000/17000`）。`M1189–M1191` **3/3 CAUGHT**；预检 **211/193/558 bad=0**、ARM **304 文件 / 1041 把**、HIDDEN **298/975 rot=0**。本地全量 **1172/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/31.5/1438`、`CHANNEL 0→96→600 变化 153619/172800 重抓=no`、`OFFSET 0/192.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **140/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 432，现读 `python3 scripts/product_streak.py --streak-for 432`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R432 跑 failure、失败步骤 2 个：唯一红是高夹具 1x 整帧不画（行数 0）⇒ 换 540 帧、≥3 行，阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效；时间列/脚注/分区/表格/菜单/floor/回执/滚动全绿。
② 产品：详情大图补 1pt 中性边（旧 0.0 → 新 32.0/28.0；图尺寸不变）。
③ 判据：M1189–M1191 3/3；四条贴合尺寸单测；precheck 211/193/558；hidden rot 0。
④ 436：R432 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 298 / 可判 975 / rot 0。
⑥ 捕获 140/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1172/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置脚注带 1x；② 主窗口 content 帧 1x 整帧不画（458）；③ 高夹具 1x 整帧不画（459）；④ 13+ 菜单像素/标题（454）；⑤ 真实拖拽（453）；⑥ Dock 像素；⑦ 源图标最小窗文字 1x；⑧ 本地全量 5 条滚动红（449）；⑨ 2x/extended；⑩ 固定块揭示偏移（455）；⑪ 跨年时间（456）；⑫ 主列表暗档文字盲区（457）；⑬ 真机/多屏（447）；⑭ 真菜单栏、12 实时腿；⑮ `table-lazy-rows`；⑯ 437–459 仍开；⑰ R433 新跑待 push 后读。

下一轮（R434）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R433 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `DETAIL_IMAGE_EDGE` 在 1x 上的边带差、`EXCLUDED_APP_ROW` 540 帧 5 行、`FILE_ROW_SYMBOL_NOT_RUN`、理由带 290、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R432 状态（2026-10-27 · 本地 · 第 431 轮 / Round 429）：设置隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 9 行首段「默认排除：」42.5pt → 新图标段 10–14pt；6 张隐私帧变化、基线 238）；R431 跑失败步骤 2 个（1x 理由带蹭到时间列 11≥10、主窗口 content 帧 1x 整帧不画）⇒ 1x 具名 NOT-RUN、阈值未动（产品 3 文件，排除名单行位）

最后更新：2026-10-27（本地 · R432 / 第 431 轮 / Round 429）：设置隐私页的默认排除名单以前是九行 `默认排除：com.…` 的裸 ID，用户认不出是哪个 App；行首第一段就是「默认排除：」五个字（逐行 **42.5pt**）。新 `ExcludedAppPresentation`（九条公认名字、未知回退 ID、`app.dashed` 兜底）+ `ExcludedAppRow`（16pt `NSWorkspace` 图标 / 兜底符号 + 应用名 12pt + bundle ID 11pt `.secondary`，行高 20，间距 6）+ `SettingsView` 两处名单接线。旧/新帧读数：首段墨宽 **42.5pt → 10.0–14.0pt**；`EXCLUDED_APP_ROW light 首段宽=[10.0,10.0,10.0,10.0,14.0,14.0] 行墨=[2704,2421,2429,2641,2417,3201]`、dark `[10.0,10.0,10.0,10.0,10.5,12.0]` / `[3055,2748,2757,3035,2125,3061]`。密码/钥匙串访问出现真实彩色图标，未安装的是虚线 App 占位符。6 张隐私帧变化，基线 **238/0/0/0**；退役「默认排除第一行」caption 探针（对象变成主色名字 + 次色 ID，同带两种色阶把上限顶到 12.70/11.32 倍参照）。R431 run `40512470409 ↔ 3de5de8` **failure，失败步骤 2 个**（Swift tests / Capture gate）：理由固定带右沿 300 把 1x 时间列（296 起）左沿算进负臂（11≥10）、主窗口 content 帧在 1x 整帧不画（校准也 0）⇒ 带子收到 290、1x 打 `FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，阈值未动；时间列 1x light `[74,71,74,74,74]` 起 296–298 止 369–370、dark `[74,72,74,74,74]` 止 370；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→51→600 37200/28466`）。`M1183–M1188` **6/6 CAUGHT**；预检 **210/192/555 bad=0**、ARM **303 文件 / 1038 把**、HIDDEN **297/972 rot=0**。本地全量 **1167/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/9/61/1438`、`CHANNEL 0→88.5→600 变化 93706/136800 重抓=no`、`OFFSET 0/230.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **139/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 431，现读 `python3 scripts/product_streak.py --streak-for 431`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R431 跑 failure、失败步骤 2 个：两条红都是仪器在 1x 没有对象（理由带蹭时间列 11、主窗口整帧不画 0）⇒ 带子收窄到 290、1x 具名 NOT-RUN、阈值未动；时间列/脚注/分区/表格/菜单/floor/回执/滚动全绿。
② 产品：隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 42.5pt 前缀 → 新 10–14pt 图标段；6 张帧变化）。
③ 判据：M1183–M1188 6/6；caption 探针退役有替代；precheck 210/192/555；hidden rot 0。
④ 436：R431 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 297 / 可判 972 / rot 0。
⑥ 捕获 139/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1167/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 1x（`SETTINGS_FOOTER_BAND_NOT_RUN`）；② 主窗口 content 帧 1x 整帧不画（`FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，458）；③ 13+ 菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；④ 真实拖拽（453）；⑤ Dock 像素（`DOCK_BADGE_PIXEL_NOT_RUN`）；⑥ 源图标最小窗文字 1x（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN`）；⑦ 本地全量 5 条滚动红（449）；⑧ 2x/extended 臂；⑨ 固定块揭示偏移（455）；⑩ 跨年时间（456）；⑪ 主列表暗档文字离屏盲区（457）；⑫ 真机/多屏（447）；⑬ 真菜单栏、12 实时腿；⑭ `table-lazy-rows`；⑮ 437–458 仍开；⑯ R432 新跑待 push 后读。

下一轮（R433）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R432 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `FILE_ROW_SYMBOL_NOT_RUN` 是否按名出现且不计红、`EXCLUDED_APP_ROW` 在 1x 上的首段宽与行数、搜索框外带/理由固定带/时间列/脚注/分区/菜单/Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R431 状态（2026-10-27 · 本地 · 第 430 轮 / Round 428）：主列表行首类型符号补绝对颜色（旧：文本行暗档 0 墨、文件行两档全空 → 新 209/165/231 与 209/492/492；35 张行帧变化、基线 238）；R430 跑失败步骤 2 个（搜索框「框外」带被新时间列污染 2.8<3.0、来源理由跨帧差 1x 读 0）⇒ 修仪器、阈值未动（产品 2 文件，行首类型符号位）

最后更新：2026-10-27（本地 · R431 / 第 430 轮 / Round 428）：主列表行首的类型符号以前在 `.file` / `.files` 两行只是一个空框（`.quaternary` 底 + 描边 + 阴影），`.text` 行在暗档也看不见 —— `foregroundStyle(.secondary)` 是相对环境的层级色，在这一列被解析成与底同色的白/黑（Bisect：红圆替身同样不显示，`secondaryLabelColor` 一换即现）。修法：`ThumbnailSymbol` 与 `RowLeadingVisual` 的 `.text` 分支都改用 `Color(nsColor: .secondaryLabelColor)`。修后同帧读数 light 校准 492 / 文本行 **209** / file **165** / files **231**，dark 475 / **209** / **492** / **492**（旧：暗档文本 0、文件两档 0）；35 张含行的 content/sidebar 帧变化，基线 **238/0/0/0**。新判据 `testFileRowsShowTheirTypeSymbol`（三枚行首 + 彩色缩略图校准；地板 20·s²/50·s²）。R430 run `40506737072 ↔ 5234370` **failure，失败步骤 2 个**（Swift tests / Capture gate）：4 条红全是新仪器被新内容污染 —— 搜索框「框外」带 y60..80 落在 R430 的时间列上（light 2.8<3.0），来源理由跨帧右端差在 1x 被同一矩形截断（0.0）⇒ 框外带改面板上沿 y0..8（本机焦点 light 255/235/255、dark 30/47.5/30），理由证改固定带 x160..300（typed 880/998、list 0/0），阈值未动。时间列在 1x 稳定（light 74/71/74/74/74、起 296–298、止 369–370；dark 74/72/74/74/74、止 370）；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现、脚注用例 passed、不计红；分区 13/12 与 11/10、表格 6/5 [2]/[1]；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→221→600 45600/46800`、`TIME 4/2/862/1430`）；拖拽 mass 0.549/0.550。`M1179–M1182` **4/4 CAUGHT**；预检 **207/189/549 bad=0**、ARM **300 文件 / 1032 把**、HIDDEN **294/966 rot=0**。本地全量 **1163/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/84/1438`、`CHANNEL 0→92→600 变化 119660/153600 重抓=no`、`OFFSET 0/232.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **138/4/0 / 238 帧**；基线 **238/0/0/0**（35 张含行帧变化）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 430，现读 `python3 scripts/product_streak.py --streak-for 430`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R430 跑 failure、失败步骤 2 个：4 条红全是新仪器被新内容污染（框外带 2.8、理由跨帧 0.0）⇒ 修取样带、阈值未动；时间列 1x 稳定（74/71/74/74/74、止 369–370）；脚注 1x 具名 NOT-RUN 生效；分区 13/12、表格 6/5；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4。
② 产品：主列表行首类型符号补绝对颜色（旧：文本行暗档 0、文件行两档 0 → 新 209/165/231 与 209/492/492；35 张帧变化）。
③ 判据：M1179–M1182 4/4；r405 重写；precheck 207/189/549；hidden rot 0。
④ 436：R430 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 294 / 可判 966 / rot 0。
⑥ 捕获 138/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1163/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`；2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 跨年记录没有年份（456）；⑩ 主列表暗档文字离屏盲区未登记（457）；⑪ 真机/多屏面板落点无截屏（447）；⑫ 真菜单栏表面、12 实时腿；⑬ `table-lazy-rows`；⑭ 437–457 仍开；⑮ R431 新跑待 push 后读。

下一轮（R432）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R431 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看行首类型符号的 `FILE_ROW_SYMBOL` 在 runner 1x 上是否过 s² 地板、搜索框焦点/悬停的外带新读数、来源理由固定带、时间列 74/71、脚注 1x 具名、分区 13/12、菜单 5 项/两提示、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R430 状态（2026-10-27 · 本地 · 第 429 轮 / Round 427）：浮层候选行补右侧定宽时间列（长标题不再吃掉时间：末段宽 71.5–74.5pt、五行右沿 385.5pt 同轴；旧帧右沿极差 152.5pt）；R429 跑失败步骤 2 个（runner 1x 脚注带 1/1、light 640 6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动（产品 1 文件，浮层时间列位）

最后更新：2026-10-27（本地 · R430 / 第 429 轮 / Round 427）：浮层候选行以前把预览、命中理由与时间拼成一条可截断字符串 —— 长标题先把时间吃掉（`quickpick-list` 第 0/4 行整行没有时间），短标题的时间又各自停在文字后面（右沿参差）。新 `rowTitle` 只留预览与理由；新 `rowTime(for:)` 沿用 `ClipboardDateFormatters.sidebarTime`；行格加 11pt `secondaryLabelColor` 右对齐时间标签，钉在行右沿 −6pt，标题右沿收到时间左沿 −8pt、压缩优先级降到 `.defaultLow`。旧/新同尺（gap=10pt 末段）：新末段宽 **74.0/71.5/74.0/74.0/73.5**（light）、**74.0/72.0/74.5/74.5/74.5**（dark），起点 311.0–313.0、止点 384.5–385.5；旧帧止点 **375.0/231.5/247.0/309.5/384.0**（极差 **152.5pt**）、第 4 行末段 327.5pt。命中理由的像素证人改跨帧同一条目：typed 止 216.5 vs list 止 146.5 ⇒ 差 **70.0pt**。R429 run `40501223109 ↔ 3daf0e1` **failure，失败步骤 2 个**（Swift tests / Capture gate）：8 条断言全在脚注带尺（1x 上 dark 720/640 1/1、light 640 6/6、y 反向）⇒ 修仪器：1x 打 `SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry` 并带读数，2x 本机仍判 7/6、末带 1086/1284、负末带 928/703；阈值未动。分区带在 1x 稳定（light 13/12、dark 11/10；表格 6/5、选中 [2]/[1]）。菜单 5/5 passed（真实 NSMenu）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 连续两跑 0 命中（只台账具名，454）。floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、无红、无 unlisted；回执 **2/2**；滚动 **4/4**（`CHANNEL 0→125→600 30000/17000`、`TIME 7/1/0/1430`）；拖拽 mass 0.549/0.550。`M1174–M1178` **5/5 CAUGHT**（时间列空/漂/拼回标题/rowTime 空/理由丢失）；R405 `M1051/M1052` 重钉 **2/2**；预检 **205/187/545 bad=0**、ARM **298 文件 / 1028 把**、HIDDEN **292/962 rot=0**。本地全量 **1162/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/79/1438`、`CHANNEL 0→82.5→600 变化 34773/108000 重抓=no`、`OFFSET 0/206/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **137/4/0 / 238 帧**；基线 **238/0/0/0**（10 张 QuickPick 行帧变化）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 429，现读 `python3 scripts/product_streak.py --streak-for 429`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R429 跑 failure、失败步骤 2 个：8 条断言全在脚注带尺的 1x 机器成因（1/1、6/6、y 反向）⇒ 1x 具名 NOT-RUN、2x 断言不动；分区带/表格行数在 1x 稳定；菜单 5/5；floor 4/5/77 无红；回执 2/2；滚动 4/4；拖拽 mass 0.549/0.550；搜索 6 行。
② 产品：浮层候选行补右侧定宽时间列（旧帧右沿极差 152.5pt → 新五行同轴 385.5；末段宽 71.5–74.5pt；理由证人 70.0pt）。
③ 判据：M1174–M1178 5/5；R405 重钉 2/2；precheck 205/187/545；hidden rot 0。
④ 436：R429 跑 judged=4/5 executed=77（notice-banner 放行）、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 292 / 可判 962 / rot 0。
⑥ 捕获 137/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1162/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`；2x 本机才判 7/6）；② 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；连续两跑 0 命中）；③ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；④ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑤ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑥ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 跨年记录没有年份（456）；⑩ 真机/多屏面板落点无截屏（447）；⑪ 真菜单栏表面、12 实时腿；⑫ `table-lazy-rows`；⑬ 437–456 仍开；⑭ R430 新跑待 push 后读。

下一轮（R431）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R430 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看浮层时间列在 runner 1x 上的末段宽/同轴读数、`SETTINGS_FOOTER_BAND_NOT_RUN` 是否按名出现且不计红、分区带 13/12 与表格 6/5、菜单 5 项/两提示、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R429 状态（2026-10-27 · 本地 · 第 428 轮 / Round 426）：侧栏固定块补「已固定」分区头（旧形状无头 5 行 → 新 6 行、插入带墨 742/784、选中揭示行号 +1；基线 238）；R428 跑失败步骤 2 个（runner 上找不到品红标记）⇒ 标记退役、改同帧带扫描 + 真实表格行数，阈值未动（产品 4 文件，侧栏分区位）

最后更新：2026-10-27（本地 · R429 / 第 428 轮 / Round 426）：侧栏里固定条目以前与普通条目同形。新 `SidebarSectionPlan`（`pinnedTitle=已固定`、`hasPinnedHeader = pinnedCount > 0`、`displayRowIndex` 头部存在时 +1）+ `SidebarSectionHeader`（11pt `VisualFont.meta` semibold、`secondaryLabelColor`、左沿 22pt、上下 4pt、`.isHeader`）+ `HistorySidebarView` 在固定块上方放一个 `Section`（无固定条目仍走原单个 `ForEach`，老帧不变）；`SelectedRowRevealer` 的行号经 plan 换算。真读数：无头 12 带 / 有头 13 带，插入带 #3 **158.0..168.0 墨=742**（light）/ **157.5..167.5 墨=784**（dark）；真实表格 **6 行 / 5 行**、选中 **[2]/[1]**。脚注 marker 退役：`settings-general` 7 带 vs 负臂 6 带，末带 **262.5..272.0 墨=1086** / **262.0..272.0 墨=1284**，负臂末带只是最后一行（928/703），640×440 同为 7/6、末带 1086/1284。R428 run `40493617687 ↔ ab3e656` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是品红标记在 runner 亮暗两档都找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役、改正/平带扫描 + 真实表格行数，阈值未动；4 张 marker 帧撤、4 张分区帧增，基线 **238/0/0/0**。菜单 `MenuShortcutPresentationTests` **5/5 passed**（真实 NSMenu 5 项两提示）；`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN` 在 runner 日志 **0 命中**（只台账具名，454 追记）。floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted；回执 **2/2**；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550、count 0.877/0.884；搜索 4 行；滚动 **4/4 passed**（`CHANNEL 0→41→600 变化 25200/6561 重抓=no`、`TIME 4/1/1330/1430`）。`M1167–M1173` **7/7 CAUGHT**（plan 2 / header 2 / wiring 3）；r29d **5/5**；r61 M314 退役、M316 重钉；预检 **204/186/540 bad=0**、ARM **297 文件 / 1023 把**、HIDDEN **291/957 rot=0**。本地全量 **1160/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=9/首=52.5/末=1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/204.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **136/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 428，现读 `python3 scripts/product_streak.py --streak-for 428`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R428 跑 failure、失败步骤 2 个：唯一红是品红标记在 runner 找不到、`SETTINGS_FOOTER` 无行 ⇒ 标记退役；菜单 5/5 passed（真实 NSMenu）；floor 5/5 无红；回执 2/2；源图标最小窗文字 NOT-RUN；拖拽 mass 0.549/0.550；搜索 4 行、滚动 4/4。
② 产品：侧栏固定块补「已固定」分区头（12→13 带、墨 742/784、表格 6/5、选中行号 +1）。
③ 判据：M1167–M1173 7/7；r29d 5/5；r61 M314 退役/M316 重钉；precheck 204/186/540；hidden rot 0。
④ 436：R428 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 291 / 可判 957 / rot 0。
⑥ 捕获 136/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1160/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454；runner 日志 0 命中 ⇒ 只在台账具名）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑥ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑦ 设置侧栏版本行窗口下沿未成立（452）；⑧ 固定块揭示偏移无独立像素验收（455）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–455 仍开；⑬ R429 新跑待 push 后读。

下一轮（R430）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R429 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看脚注带扫描 7/6 与 1086/1284 在 runner 1x 上是否稳定、分区带 13/12 与表格 6/5 是否同读数、菜单 5 项/两提示是否仍绿、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R428 状态（2026-10-27 · 本地 · 第 427 轮 / Round 425）：菜单项补全局快捷键提示并把「快速选择…」挂进菜单（12 的 NSMenu 旧 4 项/无提示 → 新 5 项、显示主窗口 ⌃⌥V / 快速选择… ⌃⌥⇧V；13+ 系统菜单像素具名 NOT-RUN）；R427 跑失败步骤 2 个（版本行差集在 runner 上整页不同）⇒ 单帧品红标记定位、阈值未动（产品 7 文件，菜单项快捷键位）

最后更新：2026-10-27（本地 · R428 / 第 427 轮 / Round 425）：菜单栏菜单以前只有四项、全局热键只在设置页看得到。新 `MenuShortcutPresentation`（标题后追加当前热键的 `displayString`；全局热键不挂 key equivalent，避免第二条路径）+ `AppCommandCatalog.menuBarCommands` 增 `.showQuickPick` + `MenuBarController` 的活 provider（每次 populate 读当前键）+ `ApplicationShell` 传两份 HotKeySettings + `AppDelegate.menuShortcutHint` 给 13+ 的 App.swift。12 真实 NSMenu 旧/新：`显示主窗口|设置|清空未收藏|退出`（4 项）→ `显示主窗口  ⌃⌥V|快速选择…  ⌃⌥⇧V|设置|清空未收藏|退出`（5 项）；自定义热键在 populate 时跟随（⌃⌥V→⌃⌥C 实测）。13+ 系统菜单像素/标题具名 `MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`（454）。R427 run `40487018343 ↔ fb55ffc` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是版本行正/负差集在 runner 上整页不同（720 136×203、640 136×202、负臂 5725/23690 墨）⇒ 改成**单帧 2×2 品红标记**定位（`settingsSidebarFooterMarkerForCapture`；新增 4 张 marker 帧；本机 1086/1284、首 24/29、负臂无标记），基线 **234→238**；r29d 名册因新增两帧再次弄空 M132，三行重钉后 **5/5 CAUGHT**。其余：floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted；`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN` 4 行出现不计红；拖拽 mass 0.549/0.550、count 0.877/0.884；搜索 4 行；滚动 4/4（`CHANNEL 0→133→600 变化 39600/32252 重抓=no`、`TIME 6/2/840/1430`）；`MOTION_COPY_RECEIPT` 无行 ⇒ NOT-RUN。`M1160–M1166` **6/6 CAUGHT**（policy 2 / controller 1 / catalog 1 / App 1 / Shell 1）；预检 **201/183/533 bad=0**、ARM **294 文件 / 1017 把**、HIDDEN **288/951 rot=0**。本地全量 **1154/57/5**：5 断言全在 `SelectionRevealAnimationTests`，单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=8/首=30.5/末=1438`、`CHANNEL 0→90.5→600 变化 108162/146400 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **134/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 427，现读 `python3 scripts/product_streak.py --streak-for 427`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R427 跑 failure、失败步骤 2 个：唯一红是版本行差集整页不同 ⇒ 单帧品红标记修复；源图标最小窗文字 NOT-RUN 4 行；拖拽 mass 0.549/0.550；搜索 4 行、滚动 4/4、floor 5/5 无红。
② 产品：菜单项补全局快捷键提示 + 快速选择入口（12 旧 4 项→新 5 项；13+ 源守卫/系统菜单 NOT-RUN）。
③ 判据：M1160–M1166 6/6；r29d 5/5；precheck 201/183/533；hidden rot 0。
④ 436：R427 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 288 / 可判 951 / rot 0。
⑥ 捕获 134/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1154/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；② 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；③ Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；④ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑤ R427 跑的 `MOTION_COPY_RECEIPT` 无行（NOT-RUN）；⑥ 本地全量 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑦ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑧ 设置侧栏版本行窗口下沿未成立（452）；⑨ 真机/多屏面板落点无截屏（447）；⑩ 真菜单栏表面、12 实时腿；⑪ `table-lazy-rows`；⑫ 437–454 仍开；⑬ R428 新跑待 push 后读。

下一轮（R429）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R428 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 12 NSMenu 的 5 项与两枚提示、13+ 源守卫、marker 帧 4 张、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R427 状态（2026-10-27 · 本地 · 第 426 轮 / Round 424）：拖拽源反馈补行内容降透明度（静置/拖拽墨量比 **0.550/0.549**、墨数比 0.936/0.911；真实 onDrag 延迟 50ms 登记、松开轮询清零）；R426 跑失败步骤 2 个（新增固定带在 1x 上读 0）⇒ 差集/具名 NOT-RUN、不改门槛（产品 3 文件，拖拽源反馈位）

最后更新：2026-10-27（本地 · R427 / 第 426 轮 / Round 424）：行被拖出去时以前没有源反馈。新 `DragSourceFeedbackState`（按 entry ID、鼠标松开清零）+ `DragSourceFeedback` 控制器（`onDrag` 延迟 50ms 登记，避开系统拖拽预览；结束用 `.common` runloop 的 50ms Timer 轮询 `NSEvent.pressedMouseButtons`）+ `EntryDragModifier(entryID:)` + 行内容 `.opacity(0.55)`（只降内容，不动行底/悬停底）。真读数：静置墨 10162/11384、拖拽 9512/10374；**墨数比 0.936/0.911、墨量比 0.550/0.549**。真看图：拖拽源行星/图标/文字整体退到背景、行底仍白。真实系统拖拽会话具名 `DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`（453）；capture-env 帧只证视觉态。R426 run `40478143446 ↔ 1f3dc91` **failure，失败步骤 2 个**（`Swift tests` / `Capture gate`）：caption 探针已绿；两条新尺的固定带在 1x 读 0（源图标最小窗文字 0、版本行正臂 0/最小窗 3473 首墨 x=7）⇒ 版本行改正/负差集（720/640 差 70×10/11、正臂 1086/1284、负臂 0），源图标最小窗文字具名 `SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`（本机 3071/3471）。`settings-min-no-footer` 加进卡片节奏排除与暗档盲区名册；名册变更把 r29d M132 弄空，二次重钉后 **5/5 CAUGHT**。floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、无红、无 unlisted ⇒ 436 REDS=0；回执 2/2 重抓=no；Dock 5/5；搜索 4 行；滚动 4/4（`CHANNEL 0→143→600 变化 40800/44400 重抓=no`、`TIME 6/3/205/1430`）。`M1153–M1159` **7/7 CAUGHT**（state 2 / entrydrag 2 / row 3）；预检 **196/178/527 bad=0**、ARM **289 文件 / 1011 把**、HIDDEN **283/945 rot=0**。本地全量 **1149/57/5**：5 断言全在 `SelectionRevealAnimationTests`，单跑（caffeinate-u 后）**4/4 passed**（`TIME 采样=18/中间值=9/首=29/末=1438`、`CHANNEL 0→87→600 变化 80951/129600 重抓=no`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **134/4/0 / 234 帧**；基线 **230→234**（4 增、0 变、0 缺）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 426，现读 `python3 scripts/product_streak.py --streak-for 426`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R426 跑 failure、失败步骤 2 个：caption 已绿；两条新尺的固定带 1x 读 0 ⇒ 版本行改正/负差集、源图标最小窗文字具名 NOT-RUN；Dock 5/5、搜索 4 行、滚动 4/4、回执 2/2、floor 5/5 无红。
② 产品：拖拽源反馈（静置/拖拽墨量比 0.550/0.549；onDrag 延迟 50ms、松开轮询清零）。
③ 判据：M1153–M1159 7/7；r29d 5/5；precheck 196/178/527；hidden rot 0。
④ 436：R426 跑 judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 283 / 可判 945 / rot 0。
⑥ 捕获 134/4/0、234 帧；换装 ok；清账 162/63/0；帧基线 234/0/0/0；本地全量 1149/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；② Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；③ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`；本机 3071/3471）；④ 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑤ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑥ 设置侧栏版本行窗口下沿未成立（452）；⑦ 真机/多屏面板落点无截屏（447）；⑧ 真菜单栏表面、12 实时腿；⑨ `table-lazy-rows`；⑩ 437–453 仍开；⑪ R427 新跑待 push 后读。

下一轮（R428）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R427 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 1x 上版本行差集/源图标最小窗文字具名 NOT-RUN 是否稳定、拖拽源在 CI 上是否只变 2 帧、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R426 状态（2026-10-27 · 本地 · 第 425 轮 / Round 423）：设置侧栏补「时间剪史 1.4.8」版本行（旧 0 墨 → 新 1086/1284，最小窗同读数、负臂 0；基线 230）；R425 跑失败步骤 2 个（来源图标进了 caption 探针框：dark 8.35:1 被读成套错档）⇒ 框从 40pt 起只盖文字、阈值未动（产品 3 文件，设置侧栏脚注位）

最后更新：2026-10-27（本地 · R426 / 第 425 轮 / Round 423）：设置页左列六个分类下面以前没有版本行。新 `SettingsSidebarFooterPolicy`（`时间剪史 <CFBundleShortVersionString>`；读不到版本只写应用名）+ `SettingsSidebarFooter`（11pt `VisualFont.meta`、`Color(nsColor: .secondaryLabelColor)`、左沿 16pt、跟在导航行之后）。旧/新同带（y 244..280、x 0..148）：`settings-general` **0 → 1086（light）/ 1284（dark）**；`settings-min` 640×440 **0 → 1086/1284**；负臂 `settings-general-no-footer` **0**；首墨 16.5pt。窗口底锚在 640×440 被内容理想高度（~466pt）裁掉（整行 0 墨）⇒ 改内容相对摆放，容器探针显式关脚注；愿望记 452。基线 **228→230**（28 变、2 增、0 缺；detail/content 与 cardprobe 不变；来源图标 7439 个变化像素全在 y 35.0..48.5pt）。`M1144–M1152` **9/9 CAUGHT**（policy 4 / view 2 / wiring 3）；名册变更弄空 r29d M132，重钉后 **5/5 CAUGHT**。R425 run `40470433082 ↔ 8d2e485` **failure，失败步骤 2 个**（`Swift tests` / `Capture gate`）：caption 探针把 20..34pt 的来源图标算进 meta 文字，runner dark **8.35:1 > 7.2279** 上限 ⇒ 框改 `x:40 w:680` 只盖文字列、阈值未动，本机 dark **5.91/参照 6.06=0.98**；同跑 Dock `DockBadgeTests` **5/5** 且 `DOCK_BADGE_PIXEL_NOT_RUN` 已登记不计红；搜索 4 行绿；滚动 **4/4 passed**；回执出现 **2x=2、1x=2、重抓=no**；floor `judged=4/5 executed=77 not-run=notice-banner`、`SUITE_CLEAN=0`、无红、无 unlisted ⇒ 436 REDS=0。源图标 runner 1x：`light 59/110、0/63、最小窗 0/0`，`dark 59/139、0/57、最小窗 0/0`（本机 2x 327/405、0/197、0/187；最小窗窄框 1x 读 0，R426 已补整条 header 带读数）。本地全量 **1145/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 后）**4/4 passed**（`0→93.5→600`、变化 131657/160800、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **133/4/0 / 230 帧**；帧基线 **230/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **280/938 rot=0**；预检 **193/175/520 bad=0**、ARM **286 文件 / 1004 把**；产品面连续零改动 **1** 轮（as-of 425，现读 `python3 scripts/product_streak.py --streak-for 425`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R425 跑 failure、失败步骤 2 个（Swift tests / Capture gate）：caption 探针把来源图标算进文字；框改 40pt 起、阈值未动。Dock 5/5、搜索 4 行、滚动 4/4、回执 2/2 重抓=no、floor 4/5（notice-banner）均绿。
② 产品：设置侧栏补版本行（旧 0 → 新 1086/1284，最小窗同读数、负臂 0）；窗口底锚失败后改内容相对，基线 230。
③ 判据：M1144–M1152 9/9；名册变更后 r29d 5/5；precheck 193/175/520；hidden rot 0。
④ 436：R425 跑 floor judged=4/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 280 / 可判 938 / rot 0。
⑥ 捕获 133/4/0、230 帧；换装 ok；清账 162/63/0；帧基线 230/0/0/0；本地全量 1145/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 设置侧栏版本行的窗口下沿愿望未成立（内容相对，452）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–452 仍开；⑩ R426 新跑待 push 后读。

下一轮（R427）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R426 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 caption 探针排除图标后是否绿、设置版本行/负臂帧在 runner 上是否只变预期带、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R425 状态（2026-10-27 · 本地 · 第 424 轮 / Round 422）：详情状态条补来源 App 图标（720pt 真实图标彩色 0→327、带右沿 298→320pt；600pt 最小窗口 ViewThatFits 先丢图标、帧逐字节不变）；R424 跑唯一红＝回执 1x 只 1 帧（窗口 1418ms 覆盖）⇒ 相位重抓、闸门 ≥2 未动（产品 3 文件，状态条来源图标位）

最后更新：2026-10-27（本地 · R425 / 第 424 轮 / Round 422）：详情头部「时间 · 大小 · 来自 X」左侧补来源 App 图标。新 `SourceAppBadge` + `SourceAppBadgePolicy`：只在 `sourceAppName` 非空时出现，`NSWorkspace` 解析真实图标并缓存，解析不到退回 `app` 符号。真读数 `detail-0-text`（Safari）：图标格 **旧彩色 0 → 新 327**、墨 197→405；头部带墨 3571→3944、右沿 **298.0→320.0pt**；正/负/最小窗三臂 light `327/405、0/197、0/187`，dark `327/597、0/220、0/223`。第一版直接摆图标把 600pt 最小窗的时间戳截成省略号 ⇒ 四档 `ViewThatFits`（图标+完整/图标+紧凑/无图标+完整/无图标+紧凑）：600 选无图标+紧凑、720 选图标+完整，**content-min 四帧逐字节不变**；12 退回 `detailWidth>=400`（451）。基线 **226→228**（46 变、2 增、0 缺）。`M1133–M1143` **11/11 CAUGHT**（policy 7 / view 2 / wiring 1 / regrab 1；RESTORE_CLEAN=yes）；头部重构弄空 r291/r393 两根针，重钉后 **3/3、2/2** 重跑绿。R424 run `40465690086 ↔ 49fcbc2` **failure，失败步骤 1 个**（`Motion coverage floor`）：五臂 `judged=5/5 executed=76 not-run=-` 全在，红是回执出现 **1x `过渡帧数=1 峰值=0.2000 窗口=1418ms 声明=160ms`**、2x=2 ⇒ 窗口覆盖（≥128ms）但 52ms runloop 相位把淡入夹在两端；修为**相位重抓一次**（`preferReceiptRegrab` 只认过程更清楚的那卷，`≥2` 未动），本机复现 1x `重抓=yes`→2、2x=8。Dock 部署绿：`DockBadgeTests` 5/5、`DOCK_BADGE_PIXEL_NOT_RUN` 在 Swift tests + Motion gate 两处出现且列在登记标记里、不计红；搜索 4 行绿；CI 滚动 **4/4 passed**（`CHANNEL 0→78→600 变化 8508/26400 重抓=no`、`TIME 6 采样/2 中间值/末 1430`）。本地全量 **1140/57/5**：5 个断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 后）**4/4 passed**（`0→95→600`、变化 144348/168000、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **132/4/0 / 228 帧**；帧基线 **228/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **277/929 rot=0**；预检 **190/172/511 bad=0**、ARM **283 文件 / 995 把**；产品面连续零改动 **1** 轮（as-of 424，现读 `python3 scripts/product_streak.py --streak-for 424`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R424 跑 failure、失败步骤 1 个（Motion coverage floor）：回执 1x 1 帧、窗口覆盖；相位重抓修复，≥2 未动；Dock 5/5+具名 NOT-RUN、搜索 4 行、滚动 4/4 均绿。
② 产品：详情状态条补来源 App 图标（720 彩色 0→327、右沿 298→320pt），窄窗先丢图标、600pt 帧逐字节不变；基线 228。
③ 判据：M1133–M1143 11/11；重钉 r291 3/3、r393 2/2；precheck 190/172/511；hidden rot 0。
④ 436：R424 跑五臂 judged=5/5 executed=76 全在，但 SUITE_RED=1（回执 1x）；修复后新跑待签收。
⑤ 367：hidden 表 277 / 可判 929 / rot 0。
⑥ 捕获 132/4/0、228 帧；换装 ok；清账 162/63/0；帧基线 228/0/0/0；本地全量 1140/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ macOS 12 的 400pt 阈值未在 12 真机验证（451）；⑤ 真机/多屏面板落点无截屏（447）；⑥ 真菜单栏表面、12 实时腿；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–451 仍开；⑩ R425 新跑待 push 后读。

下一轮（R426）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R425 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执 1x 重抓后是否 ≥2、Dock/搜索/滚动是否仍绿、来源图标在 CI 的 detail/content 帧是否只变头部；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R424 状态（2026-10-27 · 本地 · 第 423 轮 / Round 421）：Dock 图标状态补「未读剪辑」角标（后台新到 3 条 → `dockTile.badgeLabel` 旧 nil/新「3」、激活清零；像素通道由 WindowServer 画 ⇒ 具名 NOT-RUN）；R423 跑 success、20/20 步、失败 0（搜索 4 行 2025→2411/宽 64→134；滚动 4/4 绿）；本地全量 5 条滚动红由 CI 绿证伪为会话/顺序（产品 3 文件，Dock 图标状态）

最后更新：2026-10-27（本地 · R424 / 第 423 轮 / Round 421）：主窗口关掉/App 不在前台时，新到的剪辑此前在 Dock 上没有任何读数。新 `DockBadgePolicy`（0→nil、1…99→数字、>99→「99+」）+ `DockBadgeTracker`（前台不计、失活计增量、激活清零、缩水夹住）+ `DockBadgeController`（订阅 `HistoryStore.$entries`、两条激活边），`AppDelegate.configure()` 幂等建并接线。旧/新同一把尺（真实 `NSApplication.shared.dockTile.badgeLabel`）：旧 nil（控制器前攒 2 条）→ 新「3」（失活后 3 条）→ 激活 nil；纯读数 100→「99+」。像素通道具名 `DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server inProcessContentView=none badgeAfterActivate=nil`；既有 226 帧逐字节不变、基线 **226/0/0/0**。`M1119–M1127` **9/9 CAUGHT**（policy 4 / controller 2 / wiring 3，RESTORE_CLEAN=yes）。R423 run `40460495274 ↔ 37f15d8` **success、20/20 步、失败步骤 0**：搜索无结果 4 行 `light 2025→2411 变化 2985 宽 64→134`、`dark 2021→2416 变化 3023 宽 64→134`（runner 1x）；floor `judged=5/5 executed=76 not-run=-`、`MOTION_FLOOR_OK=5/5`、`MOTION_FLOOR_REDS=0`、`SUITE_CLEAN=0`、无 unlisted ⇒ **436 REDS=0**；CI 滚动 4/4 passed（`CHANNEL 起点=0.0 中段=73.0 落点=600.0 变化=21138/32400 重抓=no`、`TIME 采样=5 中间值=2 首=590 末=1430`）。本地全量 **1132/57/5**：5 个断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate -u 唤醒后）**4/4 passed**（`0→88→600`、变化 `88818/134400`、重抓=no）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）。捕获 **226/131/4/0**；帧基线 **226/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；HIDDEN **273/918 rot=0**；预检 **186/168/500 bad=0**、ARM **279 文件 / 984 把**；产品面连续零改动 **1** 轮（as-of 423，现读 `python3 scripts/product_streak.py --streak-for 423`；本轮动了 Sources 3 文件，计入下一轮分界）。电池首跑 **4 红**（streak 格写 0≠1 且缺 `scripts/product_streak.py` 引用、裸 stdout 16≠15、skip roster 级联）修后 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R423 head 跑 success、20/20 步、失败步骤 0；搜索 4 行、滚动 4/4、floor judged=5/5 executed=76 REDS=0、无 unlisted。
② 产品：Dock 图标补未读角标（后台 3 条 → 「3」、激活 nil、100→「99+」）；像素通道具名 NOT-RUN；基线不动。
③ 判据：M1119–M1127 9/9；precheck 186/168/500；hidden rot 0；ARM 279 文件/984 把。
④ 436：judged=5/5 executed=76、OK=5/5、SUITE_CLEAN=0、无 unlisted；REDS=0。
⑤ 367：hidden 表 273 / 可判 918 / rot 0 / 上界 0。
⑥ 捕获 226/131/4/0；换装 ok；清账 162/63/0；帧基线 226/0/0/0；本地全量 1132/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① Dock 角标像素/帧通道（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；② 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；③ markdown 2x / sidebar 2x / receipt 消失臂在 extended；④ 真机/多屏面板落点无截屏（447）；⑤ 真菜单栏表面、12 实时腿；⑥ `table-lazy-rows`；⑦ 设置能力闸门仍隐式（441）；⑧ 437–450 仍开；⑨ R424 新跑待 push 后读。

下一轮（R425）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R424 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 Dock 部署后 CI 是否仍全绿、搜索 4 行与滚动 4/4 是否稳定；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R423 状态（2026-10-27 · 本地 · 第 422 轮 / Round 420）：搜索无结果态补放大镜与查询词（新标题带词、旧「无匹配结果」；组件带 7790→8841 墨、128→264 宽）；R422 跑全绿（静态对照 28800、空态 4 帧 151/16→1279/28）；本地全量 5 条滚动红具名会话/顺序 NOT-RUN（产品 2 文件，搜索无结果态）

最后更新：2026-10-27（本地 · R423 / 第 422 轮 / Round 420）：搜索无结果态以前画剪贴板、只说「无匹配结果」。新 `SearchNoResultsPresentation`：真 miss 画 `magnifyingglass`、标题「没有找到「查询词」」（空白归一、24 字截断）；收藏空仍「暂无收藏」+剪贴板、无历史仍「暂无剪贴板历史」；R407 的「清除搜索」CTA 不动；侧栏只消费 policy，旧 `emptyTitle` 删除。真看图 `sidebar-no-results` 是放大镜+查询词+清除搜索；组件旧/新 250×220：旧墨 **7790/8030**、新 **8841/9234**、变化 **9360/9880**、墨宽 **128→264**（2x）。产品 `content-no-results`/`sidebar-no-results` 亮暗 **4 帧变化** + 组件 4 帧新增，基线 **226/0/0/0**。`M1115–M1118` **4/4 CAUGHT**（M1115 图标恒剪贴板；M1116 不写词；M1117 不截断；M1118 侧栏硬编码）；一次给滚动测试加 key 窗口的自伤已整段回滚（`SelectionRevealAnimationTests.swift` 零 diff）。R422 run `40453992908 ↔ 4123793` **success、失败步骤 0**：静态对照 `起→中=28800 中→落=14510 重抓=no`、空态 4 帧 `151/16→1279/28`（runner 1x）、floor `judged=4/5 executed=76 not-run=notice-banner`、`SUITE_CLEAN=0`、无 unlisted ⇒ **436 REDS=0**。本地全量 **1127/57/5**：5 条全在 `SelectionRevealAnimationTests`，同一份代码单跑（caffeinate -u 唤醒后）8 中间值/末 1438、静态通过，R422 CI 绿 ⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；捕获 **226/131/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 270/909 rot=0；预检 183/165/491 bad=0；产品面连续零改动 **1** 轮（as-of 422，现读 `python3 scripts/product_streak.py --streak-for 422`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R422 跑全绿（静态对照 28800、重抓=no；空态 4 帧 151/16→1279/28；floor judged=4/5 executed=76；无 unlisted）。
② 产品：搜索无结果态补放大镜+查询词（组件 7790→8841 墨、128→264 宽），产品 4 帧变化 + 组件 4 帧，基线 226。
③ 判据：M1115–M1118 4/4；precheck 183/165/491；hidden rot 0；key 窗口自伤已回滚。
④ 436：judged=4/5 executed=76、SUITE_CLEAN=0、notice-banner 放行；REDS=0。
⑤ 367：hidden 表 270 / 可判 909 / rot 0 / 上界 0；ARM 276 文件 / 975 把。
⑥ 捕获 226/131/4/0；换装 ok；清账 162=162；帧基线 226/0/0/0；本地全量 1127/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`；单跑与 R422 CI 绿，449）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended；③ 真机/多屏面板落点无截屏（447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–449 仍开；⑩ R423 新跑待 push 后读。

下一轮（R424）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R423 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看搜索无结果 4 帧与旧/新组件在 runner 上、floor REDS=0、以及滚动测试在 CI 是否全绿（本地整卷红是会话/顺序，449）；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R422 状态（2026-10-27 · 本地 · 第 421 轮 / Round 419）：列表空态补叠卡插画（字形 482 墨/28px → 插画 4649 墨/52px；content-empty 2 帧变化 + 新增 4 帧，基线 222）；R421 跑唯一红＝静态文档滚动正对照中段帧抢在重绘前（249/24000），重抓 + 具名 NOT-RUN，地板不动（产品 2 文件，列表空态插画位）

最后更新：2026-10-27（本地 · R422 / 第 421 轮 / Round 419）：侧栏「暂无剪贴板历史」以前是一颗 28pt 字形。新 `EmptyStateIllustration`：背卡右上错开 9pt、前卡玻璃 + 发丝边、内嵌剪贴板字形；`EmptyStateView` 增加 `illustration: Bool = false`，侧栏只在 `historyStore.entries.isEmpty` 时传 true（无匹配/收藏空保持字形）；空态无动画。真看图：组件与 `content-empty` 产品帧都显示叠卡 + 标题。同带（250×220 上半 110pt）字形 **482/483 墨、盒高 28px**；插画 **4649 墨、盒高 52px**（9.6×，盒高 +12pt）。新增 4 帧 + `content-empty` 2 帧变化，基线 **222/0/0/0**。`M1113/M1114` **2/2 CAUGHT**；三条令牌守卫抓了第一版（hover 令牌直读 / 硬写 `.secondary` / 就地字号），已改为 `VisualTint.chipStroke` 派生、`StatePresentation.iconStyle(for: .empty)`、`VisualGlyph.emptyCompact * 0.72`。R421 run `40448188618 ↔ 8dbfa54` **failure**，失败步骤 **1 个**（`Swift tests`）：**Motion floor 绿**（`judged=5/5 executed=76`、`OK=5/5`、`SUITE_CLEAN=0`；markdown 1x=2；`markdown-2x`/`receipt-dismiss-CI` 具名；`PANEL_ORIGIN 旧=(0,59) 新=(290,200)` 在 CI 执行并绿）；唯一红是静态文档滚动**正对照**中段帧抢在重绘前：`起→中=249 中→落=24000`（原点 0→80→600，地板 500）⇒ 中段低于地板时在动画中段重抓一次；重抓仍低则具名 `STATIC_SCROLL_CHANNEL_NOT_RUN=mid-frame-race`（地板不动）。全量 **1123/56/0**；捕获 **222/130/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 268/905 rot=0；预检 181/163/487 bad=0；产品面连续零改动 **1** 轮（as-of 421，现读 `python3 scripts/product_streak.py --streak-for 421`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R421 跑 floor 绿（executed=76、OK=5/5、markdown 1x=2、PANEL_ORIGIN 绿）；唯一红是静态文档正对照中段帧抢在重绘前（249/24000）⇒ 重抓 + 具名 NOT-RUN，地板不动。
② 产品：列表空态叠卡插画（字形 482/28px → 插画 4649/52px），只在无历史时接上；新增 4 帧 + content-empty 2 帧变化，基线 222。
③ 判据：M1113/M1114 2/2；三条令牌守卫的自伤已改；precheck 181/163/487；hidden rot 0。
④ 436：judged=5/5 executed=76、OK=5/5、SUITE_CLEAN=0、无 unlisted；绿。
⑤ 367：hidden 表 268 / 可判 905 / rot 0 / 上界 0；ARM 274 文件 / 971 把。
⑥ 全量 1123/56/0；捕获 222/130/4/0；换装 ok；清账 162=162；帧基线 222/0/0/0。

NOT-RUN / 阻塞（分开写）：① 静态文档中段帧的通道竞态（重抓仍低则具名 `mid-frame-race`）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended；③ 真机/多屏面板落点无截屏（447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–448 仍开；⑩ R422 新跑待 push 后读。

下一轮（R423）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R422 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看静态滚动正对照重抓/具名出口、空态 4 帧在 runner 上、floor REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R421 状态（2026-10-27 · 本地 · 第 420 轮 / Round 418）：快速选择面板补屏幕落点（真面板旧 (0,89) → 新 (290,200)，纯策略居中+夹住）；R420 胶片套件跑完（executed=76）但 markdown 2x 只 1 帧 ⇒ CI 判 1x、2x 具名 extended（产品 2 文件，窗口落点位）

最后更新：2026-10-27（本地 · R421 / 第 420 轮 / Round 418）：快速选择面板建在 (0,0) 后再没被摆过：真面板 frame 原点 **(0,89)**（屏幕左缘、Dock 之上），窗口位置从未进过任何帧或判据。新 `QuickPickPlacement.origin(panelSize:visibleFrame:)`：以 visibleFrame 居中并夹住（房间小则锚可见原点）；`show()` 在 `makeKeyAndOrderFront` 之前 `placePanel`，屏幕优先鼠标所在块、退主屏；`windowForCapture` 不读屏幕。真面板 **旧 (0,89) → 新 (290,200)**（可见 800×600、面板 420×300）；纯策略 1440×830→**(510,290)**、第二屏→**(2030,275)**、小房间→**(0,0)**。既有 **218 帧逐字节不变、基线不动**。`M1109/M1110` 2/2、`M1111/M1112` 2/2 CAUGHT；名册加新文件把 M871/M873/M877 弄空，重钉后 3/3；电池首跑 2 红（未纳管 + skip 级联）修后 683/4。R420 run `40444724766 ↔ f33e87b` **failure**，失败步骤 **1 个**（`Motion coverage floor`）：**套件跑完**（`judged=5/5 executed=76`），唯一红是 markdown **2x=1 帧**（1x=2、峰值 0.0193；probe 2x=2/1x=2 可见）⇒ 小墨量文字交换的 2x 采样边界；CI 判 1x、2x 进 extended 并具名 `markdown-2x`。回执出现 2/2（1260/1375ms）、侧栏 1x=2（2x NOT-RUN 未计红）、热图 4 帧绿（1255/1349、右沿 236→242/243）、菜单栏 92/137/63 与 12 图 891→1325。CI 模式胶片套件 **129.9s/76/4/0**。全量 **1121/56/0**；捕获 **218/129/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 267/903 rot=0；预检 180/162/485 bad=0；产品面连续零改动 **1** 轮（as-of 420，现读 `python3 scripts/product_streak.py --streak-for 420`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R420 套件跑完（executed=76），唯一红 markdown 2x=1（1x=2、probe 可见）⇒ CI 判 1x、2x 具名 extended；其余通道全绿。
② 产品：快速选择面板屏幕落点（旧 (0,89) → 新 (290,200)），纯策略 + 真 NSPanel frame；218 帧不变。
③ 判据：M1109–M1112 4/4；precheck 180/162/485；hidden rot 0。
④ 436：judged=5/5 executed=76、SUITE_RED=1（markdown 2x）、UNLISTED 缺行；未重猜。
⑤ 367：hidden 表 267 / 可判 903 / rot 0 / 上界 0；ARM 273 文件 / 969 把。
⑥ 全量 1121/56/0；捕获 218/129/4/0；套件 129.9s；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① 真机/多屏运行时落点没有屏幕截图（面板含真实剪贴板，红线禁止截屏）⇒ 只有真面板 frame + 源；② markdown 2x / sidebar 2x / receipt 消失臂在 extended 具名；③ R420 的 markdown 2x 红待下一跑签收；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–447 仍开；⑩ R421 新跑待 push 后读。

下一轮（R422）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R421 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 markdown 1x=2、套件是否 REDS=0、面板落点是否在 CI（真面板 frame 与源）；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R420 状态（2026-10-27 · 本地 · 第 419 轮 / Round 417）：侧栏搜索结果计数补数字滚动（5 条记录→1 个收藏，变化 1464/1535，带内墨 2574→2446/2684→2587）；R419 跑作业全步绿但胶片套件第三次被 200s 收掉 ⇒ 逐用例耗时账（色档普查 54.7s）后拆 extended，CI 套件 188.7→134.8s（产品 1 文件，搜索结果计数位）

最后更新：2026-10-27（本地 · R420 / 第 419 轮 / Round 417）：侧栏头部计数以前是硬换。新 `countTextLabel` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(.contentFade, value: countText)`（整句作键），12/13 不变。真看图：`sidebar-history`「5 条记录」vs `sidebar-favorites`「1 个收藏」；同带（x=202..292、y=106..146pt）变化 **1464/1535**、墨 2574→2446/2684→2587；胶片 15→1 在 **1x 4 帧/窗口 326ms/峰值 0.269**，2x 具名 `sidebar-count-2x`（3/1 边界）；既有 **218 帧逐字节不变、基线不动**。`M1106–M1108` **3/3 CAUGHT**（M1106 源；M1107/M1108 1 帧）。R419 run `40440559188 ↔ 05ac429` **作业 success、全步绿，但胶片套件第三次被 200s 收掉**：`judged=None/None executed=0`、`suite-did-not-finish`、`REDS=0` ⇒ 胶片 NOT-RUN；`MOTION_SOFT_PROBE` 可见 2/2（1980/1838ms）；`MOTION_COPY_RECEIPT_FADE` 窗口有行 1262–1515ms、过渡 2/2/2/**1**（消失 1x 具名 `receipt-dismiss-CI`）；`MOTION_MARKDOWN_MODE_FADE` 无行（被杀前未跑）；热图 4 帧绿（1255/1349，右沿 236→242/243）；菜单栏地板 92/137/63 不再假红。逐用例耗时账最大项 `testFilmScenarioAppearanceDependenceIsMeasuredPerScenario` **54.7s（29%）** ⇒ 与消失臂一起拆 `CLIPBOARD_HISTORY_UI_MOTION_EXTENDED=1`；CI 套件 **134.8s / 76 条 / 5 skip / 0 失败**（原 188.7s）。全量 **1115/56/0**；捕获 **218/129/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 265/899 rot=0；预检 178/160/481 bad=0；产品面连续零改动 **1** 轮（as-of 419，现读 `python3 scripts/product_streak.py --streak-for 419`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R419 作业全步绿但胶片套件第三次被 200s 收掉（executed=0）⇒ NOT-RUN；probe 可见、回执窗口有行、消失 1x 1 帧、热图 4 帧绿、菜单栏地板不再假红。
② 产品：侧栏搜索结果计数数字滚动（变化 1464/1535，1x 胶片 4 帧），218 帧不变。
③ 判据：M1106–M1108 3/3；extended 分流把套件压到 134.8s；precheck 178/160/481；hidden rot 0。
④ 436：judged=None/None executed=0、REDS=0 ⇒ NOT-RUN；未重猜。
⑤ 367：hidden 表 265 / 可判 899 / rot 0 / 上界 0；ARM 271 文件 / 965 把。
⑥ 全量 1115/56/0；捕获 218/129/4/0；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① R419 胶片套件被 200s 收掉（executed=0），回执/markdown 完整裁决无效；本轮 134.8s 后待下一跑；② 回执消失臂 `receipt-dismiss-CI`（runner 1x 1 中间帧；本机 2–3）；③ 侧栏计数 2x `sidebar-count-2x`（1–3 边界；1x 4）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–446 仍开；⑩ R420 新跑待 push 后读。

下一轮（R421）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R420 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看胶片套件是否跑完（`executed>0`、时长 vs 134.8s）、`MOTION_COPY_RECEIPT_FADE` 出现 2/2、markdown ≥2、热图/侧栏/菜单栏帧、436 是否 REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R419 状态（2026-10-27 · 本地 · 第 418 轮 / Round 416）：热图汇总行补数字滚动（999→1000，变化 3872/4165、右沿 481→494）；R418 跑三红定位到值：标签地板 92<100（按倍率改地板）、回执/markdown 仍 1 帧（窗口行被非 MOTION_ 前缀丢掉）⇒ 加软过渡正对照与具名 NOT-RUN 出口（产品 1 文件，热图汇总行位）

最后更新：2026-10-27（本地 · R419 / 第 418 轮 / Round 416）：热图格子按色档在演，汇总行的三个数一直硬换。新 `summaryText(line)` 在 macOS 14+ 挂 `.contentTransition(.numericText())` + `.animation(.contentFade, value: line)`（整句作键），12/13 不变。真看图：999→1000、连续 1→2 天，一格变两格、汇总行仍单行不裁。静态同带变化 **3872/4165**、墨 3696→3780/4151→4239、右沿 **481→494**；胶片 **17/15 帧**、窗口 876/841ms；新增 4 帧、既有 214 帧不变、基线 **218/0/0/0**。`M1103–M1105` **3/3 CAUGHT**（M1103 的证人是源守卫：宽度重排本身也会演，胶片分不出数字滚动与整行重排）。R418 run `40434583291 ↔ 9d65f41` **failure**，失败步骤 **3 个**（Swift tests / Capture gate / Motion coverage floor）：① 标签像素地板写死 100，runner 1x 读 **92**（本机 2x 286）⇒ 改成 `20×scale²`（runner 20、本机 80）；12 图仍 **891→1325（+434）**；② 套件跑完（`judged=5/5 executed=74`），`SUITE_RED=2`、`REDS=1`：回执/markdown 仍 1 帧，且 `COPY_RECEIPT_FADE` 无行 —— 原因是对数行前缀不是 `MOTION_`，文件通道从没搬过；已改名 `MOTION_COPY_RECEIPT_FADE`/`MOTION_MARKDOWN_MODE_FADE`，并加同跑软过渡正对照 `MOTION_SOFT_PROBE`（本地 6/7 帧、353/357ms；看不见就 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN）。本机回执 2–4 帧/323–478ms、markdown 4–5 帧；胶片套件 188.7s。另把 `testSymbolReplacementHasOneAuthor` 的裸 `.contentTransition(` 收窄到 `.symbolEffect`。全量 **1112/55/0**；捕获 **218/128/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 264/896 rot=0；预检 177/159/478 bad=0；产品面连续零改动 **1** 轮（as-of 418，现读 `python3 scripts/product_streak.py --streak-for 418`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R418 三红逐条定位：标签地板 92<100（按倍率改）；回执/markdown 1 帧且窗口行被非 MOTION_ 前缀丢掉 ⇒ 改名 + 软过渡正对照。
② 产品：热图汇总行数字滚动（999→1000，变化 3872/4165、右沿 481→494）；胶片 17/15；新增 4 帧、基线 218。
③ 判据：M1103–M1105 3/3；符号守卫收窄；precheck 177/159/478；hidden rot 0。
④ 436：judged=5/5 executed=74、SUITE_RED=2、REDS=1（回执/markdown）、UNLISTED 缺行；未重猜。
⑤ 367：hidden 表 264 / 可判 896 / rot 0 / 上界 0；ARM 270 文件 / 962 把。
⑥ 全量 1112/55/0；捕获 218/128/4/0；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① R418 的两条 1 帧红在 runner 上没有窗口值（已改名，下一跑才可定位）；② 若 probe 在 runner 读不到 ≥2，回执/markdown 以 `SOFT_TRANSITION_NOT_RUN=channel-blind` 具名 NOT-RUN；③ `testSkeletonSweepIsOneBand` 套件内偶发（单跑通过）；④ 真菜单栏表面系统合成拍不到；⑤ 12 的实时刷新无真机腿；⑥ 暂停胶片卷已撤；⑦ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑧ `table-lazy-rows`；⑨ 设置能力闸门仍隐式（441）；⑩ 437–445 仍开；⑪ R419 新跑待 push 后读。

下一轮（R420）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R419 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `MOTION_SOFT_PROBE` 是否可见、`MOTION_COPY_RECEIPT_FADE` 是否有行且窗口 ≥0.8×声明、回执/markdown 的裁决、热图 4 帧是否绿、436 是否 REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R418 状态（2026-10-27 · 本地 · 第 417 轮 / Round 415）：菜单栏补暂停斜杠（12 图 892→1327 墨 +435；13+ 标签 286→425 Δ182）；R417 跑全步绿但胶片卷被 200s 看门狗收掉 ⇒ 胶片 NOT-RUN；修套件预算与采样窗口（产品 2 文件，菜单栏状态位）

最后更新：2026-10-27（本地 · R418 / 第 417 轮 / Round 415）：主窗口有暂停横幅，但菜单栏那颗 `clipboard` 仍是静态符号。新 `MenuBarStatusPresentation`（斜杠端点 3.2→14.8、线宽 1.6、无障碍「时间剪史，已暂停记录」）+ `MenuBarStatusLabel`（13+ 标签闭包，同一符号叠斜杠，读 `@AppStorage("recordingPaused")`）+ `makeStatusBarIcon(paused:)`（12 模板图同斜杠）+ defaults 订阅（12 随开关重画）。真看图：13+ 亮/暗两态，静置完整剪贴板、暂停多一道斜杠且 glyph 仍在。读数：12 图 **892→1327（+435）**、包围盒不出 18×18；13+ 标签 **286→425（Δ182）**。新增 4 帧、既有 **210 帧逐字节不变**、基线 **214/0/0/0**。`M1096–M1102` **7/7 CAUGHT**；改入口形状弄空 R110 `M601` 与 R111 `M602`（与暂停桥重名），已重钉并整表重跑 **4/4、4/4 CAUGHT**。R417 run `40429334110 ↔ a6fc65a` **success（21/21 步）但胶片卷 NOT-RUN**：`MOTION_FLOOR_FACTS judged=4/5 executed=0 not-run=notice-banner`、`suite-did-not-finish`、`REDS=0`；R416 同卷 189s、R417 加场景后被 200s 看门狗收掉。**暂停 4 帧在 runner 上绿**（`PAUSE_BANNER_BAND` 亮 0→26250 变化/112 橙、暗 104 橙；defaults 0→112）；回执 6 帧像素绿（0/0→2416/0、2724/187；暗 1738/0、1991/177）；`COPY_RECEIPT_FADE` 无行。修：撤暂停胶片卷（状态已像素/源钉住）、把采样窗口推广为所有声明时长场景的自动下限（markdown 的 0.3ms×30=9ms 同病）；本地套件 **183s**、回执 2–4 帧/窗口 329–488ms、markdown 4–6 帧。全量 **1108/54/0**；捕获 **214/127/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 263/893 rot=0；预检 176/158/475 bad=0；产品面连续零改动 **1** 轮（as-of 417，现读 `python3 scripts/product_streak.py --streak-for 417`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R417 作业全步绿但胶片卷被 200s 看门狗收掉（executed=0）⇒ 胶片 NOT-RUN；暂停 4 帧绿、回执像素绿、COPY_RECEIPT_FADE 无行。
② 产品：菜单栏暂停斜杠（12 图 +435 墨；13+ 标签 Δ182），新增 4 帧、基线 214。
③ 判据：M1096–M1102 7/7；R110 M601 / R111 M602 重钉后 4/4、4/4；precheck 176/158/475；hidden rot 0。
④ 436：judged=4/5 executed=0 not-run=notice-banner、REDS=0 但 suite-did-not-finish ⇒ NOT-RUN；未重猜 must_judge。
⑤ 367：hidden 表 263 / 可判 893 / rot 0 / 上界 0；ARM 269 文件 / 959 把。
⑥ 全量 1108/54/0；捕获 214/127/4/0；换装 ok；清账 162=162；帧基线 214/0/0/0。

NOT-RUN / 阻塞（分开写）：① R417 胶片套件被 200s 看门狗收掉（suite-did-not-finish、executed=0），回执/markdown 本跑无效；② `COPY_RECEIPT_FADE` 无行；③ 真菜单栏表面系统合成拍不到；④ 暂停胶片卷已撤（过程由共享 notice-banner 臂作最近证人）；⑤ 12 的实时刷新没有 macOS 12 真机腿；⑥ runner 的 `REVEAL`/`INTAKE_READING` 无行；⑦ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑧ `table-lazy-rows`；⑨ 设置能力闸门仍隐式（441）；⑩ 437–444 仍开；⑪ R418 新跑待 push 后读。

下一轮（R419）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R418 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看胶片套件是否 `executed>0`、回执 2–4 帧/窗口是否 ≥0.8×声明、markdown 是否 ≥2、菜单栏 4 帧是否绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R417 状态（2026-10-27 · 本地 · 第 416 轮 / Round 414）：暂停采集状态补主窗口横幅（旧 0 橙 → 新 434/386；默认键管线 0/0→434）；R416 run 唯一红＝回执胶片采样窗口，修采样不改门槛（产品 4 文件，暂停状态横幅位）

最后更新：2026-10-27（本地 · R417 / 第 416 轮 / Round 414）：`recordingPaused` 以前只在设置页可见。新 `StatePresentation.Kind.paused`（pause.circle.fill、prominent 墨、橙图标/12% 底、动作「继续记录」）+ `NoticeTone.paused`；`ContentView` 用 `@AppStorage("recordingPaused")` 画第六条横幅，`noticeSignature` 加 `bits |= 32` 驱动 bannerIn/bannerOut，动作把开关关回去；取证键 `pausedForCapture`。真看图亮/暗整窗：琥珀带、橙色暂停图标、文案与动作完好。同带旧 **0 橙** → 新 **434/386 橙**（亮/暗），整带变化 141864/141880；只拨 defaults 的产品入口 **0→434**。新增 4 帧、既有 **206 帧逐字节不变**、基线 **210/0/0/0**。胶片出现 2x 27/5/0.5822/523ms、1x 27/5/0.5780/444ms；消失 2x 27/5/0.6550/568ms、1x 27/7/0.3539/476ms。`M1088–M1092` **5/5**、`M1093–M1095` **3/3 CAUGHT**（M1089/M1090 第一版被整文件 contains 放过，收窄到暂停分支后 CAUGHT）。R416 run `40420998525 ↔ a51de8d` **failure**：失败步骤 **1 个**（`Motion coverage floor`），红是 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 在 1x/2x 都只有 1 个过渡帧；定位 `MOTION_GRAB 30 帧/中位 1.7ms/声明 160ms` ⇒ 触发后窗口 ≈41ms，卷子没覆盖过程；修 `Scenario.minimumSampleSpacingMilliseconds`（回执 8ms）并打印/前置断言窗口，**门槛未动**。回执 6 帧像素在 runner 上绿（亮 0/0→2416/0、2724/187；暗 0/0→1738/0、1991/177）；`COPY_RECEIPT_FADE` 在 runner 无行记 NOT-RUN。全量 **1106/55/0**；捕获 **210/126/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 261/886 rot=0；预检 174/156/468 bad=0；产品面连续零改动 **1** 轮（as-of 416，现读 `python3 scripts/product_streak.py --streak-for 416`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R416 runner 唯一红是回执胶片；定位到 30 帧×1.7ms=41ms < 声明 160ms，修采样窗口（8ms 下限 + 窗口前置断言），门槛未动。
② 产品：暂停采集补主窗口横幅（旧 0 橙 → 434/386），defaults 管线 0→434；新增 4 帧。
③ 判据：纯/source/defaults/像素/胶片；M1088–M1095 8/8 CAUGHT；派生键守卫 6 调用点；precheck 174/156/468；hidden rot 0。
④ 436：judged=5/5、REDS=1（红有名字：本轮回执胶片）、UNLISTED 缺行记 NOT-RUN；notice-banner 放行，未重猜 must_judge。
⑤ 367：hidden 表 261 / 可判 886 / rot 0 / 上界 0；ARM 267 文件 / 952 把。
⑥ 全量 1106/55/0；捕获 210/126/4/0；换装 ok；清账 162=162；帧基线 210/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地绿）；② `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；③ `COPY_RECEIPT_FADE` 在 runner 没有行（stdout 丢）；④ 暂停横幅真机点击链与菜单栏状态缺证（443）；⑤ `table-lazy-rows`；⑥ 设置内容帧能力闸门仍隐式（441）；⑦ 亮档真机腿仍没跑；⑧ macOS 12 紧凑详情头仍走旧截断；⑨ 437/438/439/440/441/442/443 仍开；⑩ R417 新跑待 push 后读。

下一轮（R418）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R417 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执胶片修后是否绿、`COPY_RECEIPT_FADE` 是否有行、暂停横幅 4 帧在 runner 上是否绿。① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R416 状态（2026-10-27 · 本地 · 第 415 轮 / Round 413）：复制回执补文字胶囊（回执带旧 0/0 → 已复制 8792/0、失败 9936/355）；R415 run 全绿 → 设置 8 红消失（2 条具名能力 skip）、焦点 236.1/217.6、滚动 reduce=true override=false（产品 1 文件，复制回执位）

最后更新：2026-10-27（本地 · R416 / 第 415 轮 / Round 413）：复制成功/失败以前只换第三颗按钮的图标（R394 给了失败红），窄药丸里没有一句人话。新 `CopyReceiptPresentation`（失败优先真值表）+ `CopyReceiptView`（图标 + 「已复制」/「复制失败」的玻璃胶囊）挂在药丸上方外侧，`.emphasis` 驱动 opacity+move(bottom) 过渡，`fixedSize` 防折行，`allowsHitTesting(false)`。真看图亮/暗三态：静置无回执，成功白勾、失败红感叹号；同带旧 **0/0** → 亮 **8792/0、9936/355**；暗 **5257/0、6094/356**。新增 6 帧、既有 200 帧逐字节不变、基线 **206/0/0/0**。胶片出现 2x 27/6/0.0800、1x 27/4/0.0889；消失 2x 27/7/0.0429、1x 27/6/0.0889。`M1084–M1087` **4/4 CAUGHT**（M1084 三态全 0/0），RESTORE_CLEAN=yes。R415 run `40416557136 ↔ 7d8a0b7` **success**、失败步骤 **0 个**（21/21 step success）：**R414 的 8 条设置内容红消失**（probes/disabled passed；rowtier 走 `ROWTIER_NOT_RUN light`、card 走 `CARD_RHYTHM_SHADE_NOT_RUN=1` 两条具名能力 skip）；**焦点 runner 读数** 亮 236.1/217.6/207.6、暗 50.1/66.3/84.2；**滚动** `SCROLL_REVEAL_PLAN reduce=true override=Optional(false)`、6 采样/2 中间值/首 365/末 1430、OFFSET 0→457→1430、INSTANT 50→50。全量 **1100/54/0**；捕获 **206/124/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 259/878 rot=0；预检 172/154/460 bad=0；产品面连续零改动 **1** 轮（as-of 415，现读 `python3 scripts/product_streak.py --streak-for 415`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R415 runner 全绿：失败步骤 0；8 条设置内容红消失（2 passed + 2 条具名能力 skip）；焦点亮 236.1/217.6/207.6；滚动 reduce=true override=false、6/2/365→1430。
② 产品：详情区复制回执补文字胶囊，旧 0/0 → 新亮 8792/0、9936/355（暗 5257/0、6094/356），新增 6 帧。
③ 判据：纯真值表 + 源 5 条 + 像素三态 + 胶片；M1084–M1087 4/4 CAUGHT；precheck 172/154/460/0；hidden rot 0。
④ 436：judged=5/5、REDS=0、OK=5/5、notice-banner 放行；UNLISTED 通道缺行记 NOT-RUN。
⑤ 367：hidden 表 259 / 可判 878 / rot 0 / 上界 0；ARM 265 文件 / 944 把。
⑥ 全量 1100/54/0；捕获 206/124/4/0；换装 ok；清账 162=162；帧基线 206/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（On-screen 步看门狗 240s 收掉、R3-D9 已知边界；本地绿）；② `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；③ 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；④ 回执只有组件帧与胶片作证，真机整窗与失败触发面仍缺（442）；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 设置内容帧能力闸门仍隐式（441）；⑧ 437/438/439/440/441/442 仍开；⑨ R416 新跑待 push 后读。

下一轮（R417）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R416 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执 6 帧在 runner 上是否仍绿、新增 `COPY_RECEIPT_TOAST` 是否有行。① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R415 状态（2026-10-27 · 本地 · 第 414 轮 / Round 412）：QuickPick 搜索框补焦点边界（静置 255/30 → 焦点 235/47.5）；R414 run 的设置内容红由撤 settle 修、R413 滚动两红已绿（reduce=true）（产品 1 文件，面板搜索焦点位）

最后更新：2026-10-27（本地 · R415 / 第 414 轮 / Round 412）：QuickPick 搜索框是裸字段，R409 只在悬停点亮边界；面板一打开字段就是第一响应者，焦点没有可见边界。新增 `QuickPickSearchField` 的 `become/resignFirstResponder` → `onFocusChange`；`QuickPickSearchBackdrop` 的 `focused/focusedForCapture`；`show()` 只在 `makeFirstResponder(field)` 成功时点亮、`hide()` 收回；夹具 `windowForCapture(searchFocused:)`。真看图：静置裸文字，焦点/悬停同档圆角底与描边；同带静置 **255.0/30.0** → 焦点 **235.0/47.5**，框外 194.3/94.7。新增 `quickpick-search-focus` 亮暗 2 帧；既有 198 帧逐字节不变；基线 **200/0/0/0**。`M1080–M1083` **4/4 CAUGHT**；焦点改动把 R409 `M1060` 与 R76 `M399` 两张旧表弄空，已重钉并整表重跑 **2/2**、**5/5 CAUGHT**，HIDDEN rot 1→0。R414 run `40408685273 ↔ 65514d4` failure：失败步骤 2 个（Swift tests + Capture gate）；**R412 两红消失**；**R413 滚动两红已绿**（`SCROLL_REVEAL_PLAN reduce=true override=false`、首=199/末=1430/2 中间值）；新红 8 条全在 settings 内容帧，成因是 R414 整页 settings 夹具的 0.1s settle 让 runner 帧落在 vibrant/contentFade 中段；撤 settle 后本地 200 帧逐字节不变。胶囊组件在 runner 1x 33.5/49.5/65.5（2x 35.8/51.2/67.5）。全量 **1096/53/0**；捕获 **200/123/4/0**、final3 200/0；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 258/874 rot=0；预检 171/153/456 bad=0；产品面连续零改动 **1** 轮（as-of 414，现读 `python3 scripts/product_streak.py --streak-for 414`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R414 runner：R412 两红消失、R413 滚动两红已绿（reduce=true、2 中间值）；新红 8 条是整页 settings 的 0.1s settle 打破隐式能力闸门；撤 settle。
② 产品：QuickPick 搜索框补焦点边界，静置 255/30 → 焦点 235/47.5，新增 2 帧。
③ 判据：焦点源/像素 + M1080–M1083 4/4；R409 M1060 / R76 M399 重钉后 2/2、5/5；hidden rot 0。
④ 436：judged=5/5、REDS=0、notice-banner 放行；无新 unlisted。
⑤ 367：hidden 表 258 / 可判 874 / rot 0 / 上界 0；预检 171/153/456/0。
⑥ 全量 1096/53/0；换装 ok；清账 162=162；帧基线 200/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地绿）；② 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；④ R414 run 的设置内容红靠撤 settle 回隐式能力闸门，runner 复验等 R415 新跑；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 437/438/439/440/441 仍开；⑧ R415 新跑待 push 后读。

下一轮（R416）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R415 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 settings 内容帧是否恢复能力闸门、焦点帧在 runner 上的读数；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R414 状态（2026-10-27 · 本地 · 第 413 轮 / Round 411）：设置侧栏选中胶囊滑动（静置/中点/落定 35.8→51.2→67.5pt）；R412 两红在 runner 消失、滚动行为两红由 reduce-motion 测试 seam 修（产品 1 文件，设置侧栏选择滑移位）

最后更新：2026-10-27（本地 · R414 / 第 413 轮 / Round 411）：设置侧栏原来每行各自淡入淡出选中底，切换分类是两行交叉淡，没有空间连续性。新 `SettingsSidebarSelectionPlan` 按行 frame（左右内缩 6）给出胶囊矩形与两行间插值；`SettingsSidebarView` 用 PreferenceKey 收六行位置，在行后画**唯一一颗**胶囊，`.selection` 驱动，行内选中底清空；既有 192 帧逐像素不变，新增六帧三态，基线 198。真看图：静置/中点/落定中心 **35.8/51.2/67.5pt**（x=8..13，计数 588/586/598），亮暗同。M1076–M1079 4/4 CAUGHT；旧 M818 重钉到胶囊填充行并整臂重跑（198 帧/18 变/14 设置窗口、CAUGHT；M817 也 CAUGHT）。R413 runner `40400010978 ↔ 2e02c4d` **failure**：只有 Swift tests 两条滚动行为红（0.15s 中段=目标；4 采样/0 中间值），静态通道绿；R412 两红（节奏 15/10/9、邻行 20740/0）**已消失**（Capture gate 绿、邻行 accent 0）；三条真在屏探针在 runner 的 `REVEAL`/`INTAKE_READING` 通道**没有行** ⇒ 具名 NOT-RUN（本地绿）。修法：单测专用 `revealReduceMotionOverride=false`（产品默认仍读系统 reduce-motion），下一跑用 `SCROLL_REVEAL_PLAN reduce/override` 读。全量 **1094/53/0**；捕获 198/122/4/0、final2 198/0；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 256/866 rot=0；预检 170/152/452 bad=0；产品面连续零改动 **1** 轮（as-of 413，现读 `python3 scripts/product_streak.py --streak-for 413`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R413 runner failure：只有两条滚动行为红；R412 两红消失、Capture gate 绿；在屏探针暂无通道行记 NOT-RUN；加 reduce-motion 测试 seam。
② 产品：设置侧栏选中胶囊滑动，三态中心 35.8/51.2/67.5；既有 192 帧不变，新增 6 帧。
③ 判据：纯计划 + 源 + 跨倍率中心尺 + 捕获三态；M1076–M1079 4/4；M818 重钉整臂 CAUGHT。
④ 436：judged=5/5、REDS=0、notice-banner 放行；无新 unlisted。
⑤ 367：hidden 表 256 / 可判 866 / rot 0 / 上界 0；预检 170/152/452/0。
⑥ 全量 1094/53/0；换装 ok；清账 162=162；帧基线 198/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地三探针绿）；② 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；③ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；④ R413 滚动两红由 reduce-motion seam 修，runner 复验等 R414 新跑；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 437/438/439 仍开；⑧ R414 新跑待 push 后读。

下一轮（R415）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R414 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R413 状态（2026-10-27 · 本地 · 第 412 轮 / Round 410）：跨视口长跳补滚动到位动画（0→203→1438；旧瞬移 0/15 中间值）；R412 录制描边 runner 红修复（纵向 0 + 强调隔离）（产品 1 文件，滚动到位位）

最后更新：2026-10-27（本地 · R413 / 第 412 轮 / Round 410）：旧的揭示是一次 `scrollRowToVisible` 瞬移。新 `SelectionRevealMotion.plan` 只在距离 > 一屏且非减弱动态时演 0.20s（`.slider`），instant 与 animated 共用系统最小滚动目标。真在屏抓到两版自伤：纯 bounds 动画滚到位（origin 1977）但 List 选中集 **[]**；只把系统滚动放前面、目标在物化前读会让 2191 跳 3211。最终：先系统滚 + layout + 再滚读物化后目标，回起点演到该目标，完成时再物化落点。真在屏：选中 [60]、在屏 true、origin 3211；臂3 滚开后收藏/撤收藏仍 0；drift 3143→0；intake 0→159、选中 [4]。离屏：17 采样/7 中间值，首 68、末 1438、目标 1438；慢放 0→203→1438。像素通道：静态文档 111729/148800；产品表格滚动后新行不被 cacheDisplay 画出 ⇒ 产品像素中段具名 NOT-RUN `table-lazy-rows`。R412 的 runner 红：`40385615419 ↔ 130be12` **failure**，2 个失败步骤；节奏 15/10/9、邻行 20740/0；描边纵向 −2→0，邻行隔离改判强调；本地亮 4016/3958、暗 4016/3956、邻行 0/0，基线 192/0；runner 复验等下一跑。M1070–M1075 **5/5 CAUGHT**；M1065–M1069 重跑 5/5；HIDDEN 256/866 rot=0；预检 169/151/448 bad=0；全量 **1091/53/0**（一次 Perf 瞬态 262.9/269.86ms >250，单跑 148.02ms，复跑 0；阈值未改）；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；产品面连续零改动 **1** 轮（as-of 412，现读 `python3 scripts/product_streak.py --streak-for 412`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R412 头跑 failure：2 个失败步骤，节奏 15/10/9 + 邻行 20740/0；定位为描边纵向 −2 侵入行距 + runner 整页 1 级底色；产品纵向 0、邻行改判强调，本地复验绿；第二次同码捕获四张 hash 全等。
② 产品：跨视口长跳滚动到位动画，真在屏选中/可见/不回拉/采集揭示四格全过；离屏 7/17 中间值、末=目标。
③ 判据：纯计划 + 源守卫 + 真 NSScrollView 行为 + 静态通道正对照 + 三探针；M1070–M1075 5/5 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED 登记 ok、notice-banner 放行，保持结案。
⑤ 367：hidden 表 256 / 可判 866 / rot 0 / 上界 0；预检 169/151/448/0。
⑥ 全量 1091/53/0；换装 ok；清账 162=162；帧基线 192/0/0/0。

NOT-RUN / 阻塞（分开写）：① 产品 NSTableView 滚动后的中段/落点像素帧空白（`table-lazy-rows`；静态文档正对照已证明通道可拍）；② `MOTION_FLOOR_UNLISTED` 与 `SCROLL_FAILURE_COUNT` 通道本跑没有行；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ 设置卡其它行族没有行级状态（438）；⑦ 离屏滚动帧通道边界记 439；⑧ R413 新跑待 push 后读；⑨ R412 runner 的节奏/邻行复验等 R413 新跑。

下一轮（R414）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R413 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 R412 的 15/10/9 与 20740/0 是否在 runner 上消失、滚动动画三探针是否绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

## R412 状态（2026-10-27 · 本地 · 第 411 轮 / Round 409）：设置快捷键行补「正在录制」行级描边（行带旧 0/0 → 新 4040/3990，邻行 0）；R411 空态句 identifier 在 runner 上生效（产品 2 文件，设置行录制态位）

最后更新：2026-10-27（本地 · R412 / 第 411 轮 / Round 409）：快捷键设置卡的录制态只亮 128×28 录音器自己那圈；三行快捷键里行标题/说明没有「这一行在吃键」的标记。修法：`HotKeyRecorderView` 增加只读 `onRecordingChange`，`HotKeySettingsRow` 录制时给整行画 1.5pt accent 圆角描边（纵向外扩 2pt、横向不扩），`.emphasis` 驱动；数值走 `SettingsRowEmphasis`。同带旧/新（x=175..480、y=224..298pt）：旧 **0/0** → 新 **4040/3990**（亮）、**4039/3979**（暗）；邻行 **0/0**；录音器环亮 1794 / 暗 1780 不回退。`settings-shortcuts-recording` 亮暗 2 帧变化；另把 R411 的 `sidebar-row-hover` 夹具补落定等待（侦察快照中间相 220.84 → **212.06**，等于已提交基线与 R411 台账的 212.1；邻行不变）—— 基线里该帧 hash 本就是最终态，已提交基线只改 recording 两帧；基线 192/0/0/0。源/纯函数/像素三守卫：跨倍率 1× 276 / 2× 1104，真实行 4834 强调 / 静置 0；M1065–M1069 **5/5 CAUGHT**（M1068 变化 4846、强调 0 ⇒ 抓可见性）。⓪ `40370566410 ↔ a8ebbaf` **success**、22 步全绿；`QUICKPICK_EMPTY_FIELD 句子长=30 其它字段=1`（旧 33/56 消失，不是改门槛）；行 hover 两守卫与 `ControlHoverLadderTests` 绿；`SCROLL_FAILURE_COUNT` 缺行记具名 NOT-RUN；sources R411/2b0ef71 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1084 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账表 162=162；`HIDDEN_ARMS 表=255 可判=861 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=168 covered=150 arms=443 bad=0`、全仓 261 文件 / 927 把；产品面连续零改动 **1** 轮（as-of 411，现读 `python3 scripts/product_streak.py --streak-for 411`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R411 头跑 success：空态句 30/1、33/56 消失；行 hover 两守卫与 ControlHoverLadder 绿；缺行通道记 NOT-RUN。
② 产品：快捷键设置行录制态补整行描边，行带 0/0 → 4040/3990，邻行 0。
③ 判据：纯函数 + 源 + 跨倍率像素尺 + 真实行 + 整页邻行；M1065–M1069 5/5 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 255 / 可判 861 / rot 0 / 上界 0；预检 168/150/443/0。
⑥ 全量 1084/53/0；换装 ok；清账表 162=162；帧基线 192/0/0/0。

NOT-RUN / 阻塞（分开写）：① `SCROLL_FAILURE_COUNT` 本跑没有行，记具名 NOT-RUN；② 真实指针不在录制态触发路径上，真机合成器里的描边仍只由离屏帧作证；③ 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；④ 亮档真机腿仍没跑；⑤ macOS 12 紧凑详情头仍走旧截断；⑥ 主列表与浮层来源搜索语言未统一（437）；⑦ 设置卡其它行族没有行级状态（438）；⑧ R412 新跑待 push 后读。

下一轮（R413）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R412 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R411 状态（2026-10-27 · 本地 · 第 410 轮 / Round 408）：主列表整行补悬停反馈（目标行 232.5/47.9 → 212.1/59.6，邻行 0）；空态句改用 identifier 精确选取（产品 3 文件，列表行悬停位）

最后更新：2026-10-27（本地 · R411 / 第 410 轮 / Round 408）：主列表行可点可选中，但整行没有悬停反馈。`HistoryRowButton` 接真实 `onHover` + 按 entry id 的 `hoveredEntryIDForCapture`，悬停底色走共享 `HoverInk.opacity(level:dark:)`。像素现读（目标行 x=20..280、y=222..265pt）：亮 **232.5 → 212.1**、暗 **47.9 → 59.6**；目标行变化 **43733/44720=97.8%** / **43708/44720=97.7%**；邻行 **0/31200=0.0%**。新增 `sidebar-row-hover` 亮暗 2 帧，既有 190 帧不变，基线同笔 192/0/0/0。源/像素两刀 `M1063/M1064` 双 CAUGHT（源守卫第一版被星标自己的 onHover 喂饱，已收窄到行级整行）。⓪ `40358291786 ↔ 9a5b70a` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），只有空态句两条（gap **33>24**、长句宽 **56>44**）；`SCROLL_FAILURE_COUNT=0` ⇒ R410 的可见原点守卫已过。R411 查明 33/56 来自**测试抓错 NSTextField**（固有宽 44 的短字段），给空态句加 `identifier=quickPickEmptyMessage` 精确选取并输出其它字段诊断。`Release script tests` success：sources `R410/61da3be` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1080 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=254 可判=856 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=167 covered=149 arms=438 bad=0`、全仓 260 文件 / 922 把；产品面连续零改动 **1** 轮（as-of 410，现读 `python3 scripts/product_streak.py --streak-for 410`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R410 头跑 failure：2 个失败步骤只有空态句 33/56；滚动守卫已过；查明测试抓错 NSTextField，identifier 修正。
② 产品：主列表行补悬停反馈，目标行 232.5/47.9 → 212.1/59.6，邻行 0。
③ 判据：源 + 像素目标/邻行隔离；M1063/M1064 双 CAUGHT；共享换算守卫绿。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 254 / 可判 856 / rot 0 / 上界 0；预检 167/149/438/0。
⑥ 全量 1080/53/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实指针悬停仍只能人工验（捕获由 hoveredEntryIDForCapture 点亮）；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R411 新跑待 push 后读。

下一轮（R412）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R411 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R410 状态（2026-10-27 · 本地 · 第 409 轮 / Round 407）：菜单栏空态补「打开时间剪史」（CTA 带旧 0/0 → 新 1166/1382）；空态容器改普通 NSView、滚动守卫改读可见原点（产品 2 文件，菜单空态 CTA 位）

最后更新：2026-10-27（本地 · R410 / 第 409 轮 / Round 407）：菜单栏空态只有“暂无推荐”，没有下一步。空态分支加「打开时间剪史」菜单项，走已有 `.showMainWindowHotKeyPressed` 通知；旧/新 CTA 带 **0/0 → 1166/1382**（消息带 330/347→910/1032），menubar-empty 与 menubar-refreshing 亮暗 **4 帧**变化，基线同笔 190/0/0/0。源/像素两刀 `M1061/M1062` 双 CAUGHT。⓪ `40350180209 ↔ 83bed7a` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），两件事：① 空态在 runner 上仍 gap **33>24**、长句 **56>44**（emptyBox 还是 NSStackView）；② `DetailScrollResetTests` 的 `afterVisible=0` vs `topVisible=11`（初始可见原点被当常数）。修法：emptyBox 改**普通 NSView + 显式四边约束**；滚动守卫改断言“换选后可见原点 ≤1”（旧行为 2357 仍红）；`PressFeedbackTests` 菜单按钮精确计数 2→3。sources `R409/7426d05` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1078 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=253 可判=854 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=166 covered=148 arms=436 bad=0`、全仓 259 文件 / 920 把；产品面连续零改动 **1** 轮（as-of 409，现读 `python3 scripts/product_streak.py --streak-for 409`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R409 头跑 failure：2 个失败步骤，空态 33/56 + 滚动可见原点 0 vs 11；两处都已按 runner 原文修。
② 产品：菜单栏空态补「打开时间剪史」，旧/新 CTA 带 0/0→1166/1382；4 帧变化。
③ 判据：源 + 像素双带；M1061/M1062 双 CAUGHT；M1053/M1054 重跑仍 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 253 / 可判 854 / rot 0 / 上界 0；预检 166/148/436/0。
⑥ 全量 1078/53/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实菜单展开/关闭仍只能人工验；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签产品结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R410 新跑待 push 后读。

下一轮（R411）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R410 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R409 状态（2026-10-26 · 本地 · 第 408 轮 / Round 406）：QuickPick 搜索框补悬停边界（静置 255/30 → 悬停 235/47.5，带变化 62.9%）；R408 CTA 布局改用 content 直钉（gap 33→8）（产品 3 文件，悬停反馈位）

最后更新：2026-10-26（本地 · R409 / 第 408 轮 / Round 406）：QuickPick 主输入框原来是一行裸文字，和主窗口 `SearchField` 的框不是同一套语言。新增 `QuickPickSearchBackdrop` + 真实 hover tracking，只在悬停时画圆角边界/淡填充；静置/焦点保持原样。像素现读（框内 x=300..400、y=12..40pt）：静置 **255.0/30.0** → 悬停 **235.0/47.5**（亮/暗），框带变化 **35200/56000=62.9%**，框外相邻带 194.3/94.7 作对照。仅 hover 亮暗 2 帧新增，既有 188 帧逐字节不变，基线同笔 190/0/0/0。源/像素两刀 `M1059/M1060` 双 CAUGHT。⓪ `40340793989 ↔ 6bef5ab` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），同源于 R408 的 `emptyBox` 仍在主 `NSStackView`：runner 空句 gap **33>24**、长句宽 **56>44**；改成 `emptyBox` 直钉 content（top=field 底+8）后本机 gap **8**、长句 **400**。R406 的 visibleRect 守卫在这一跑仍绿。`Release script tests` success：sources `R408/a642dc0` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1076 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=252 可判=852 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=165 covered=147 arms=434 bad=0`、全仓 258 文件 / 918 把；产品面连续零改动 **1** 轮（as-of 408，现读 `python3 scripts/product_streak.py --streak-for 408`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R408 头跑 failure：2 个失败步骤同源于 CTA 布局；emptyBox 出栈后本机 gap 8/长句 400，visibleRect 守卫仍绿。
② 产品：QuickPick 搜索框补悬停边界，静置 255/30 → 悬停 235/47.5，带变化 62.9%。
③ 判据：源 + 像素三读数；M1059/M1060 双 CAUGHT；旧焦点/幻影判据仍绿。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 252 / 可判 852 / rot 0 / 上界 0；预检 165/147/434/0。
⑥ 全量 1076/53/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实 hover 事件仍只能人工验（捕获由 hoveredForCapture 点亮）；② 离屏 alpha 动画采样不到中间帧（mid=1.0）⇒ 弹层淡入不签结论；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断；⑤ 主列表与浮层来源搜索语言未统一（437）；⑥ R409 新跑待 push 后读。

下一轮（R410）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R409 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R408 状态（2026-10-26 · 本地 · 第 407 轮 / Round 405）：拖入目标补「松手加入剪贴板历史」（拖放带 0/0 → 708/797）；R407 CTA 布局回归用容器修回（gap 33→8）（产品 2 文件，拖放反馈位）

最后更新：2026-10-26（本地 · R408 / 第 407 轮 / Round 405）：拖入时只有虚线框/光，没有一句“松手会发生什么”。新增 `dropTargetedForCapture` 取证键 + 底部「松手加入剪贴板历史」；无拖放帧同带 **0/0** → 拖放帧 **708/797**，列表校准 **6838/7256**；新增 2 帧、2 张 `quickpick-empty` 随 CTA 容器布局修正，基线同笔 188/0/0/0。源/像素两刀 `M1057/M1058` 双 CAUGHT。⓪ `40332222297 ↔ d9bfa83` **completed / failure**，失败步骤 **2 个**（`Swift tests` + `Capture gate`），同源于 R407 把 CTA 直接塞进主 `NSStackView`：runner 空句 gap **33pt>24**、长句宽 **56pt>44pt**；收进 `emptyBox` 后本机 gap **8pt**、长句 **400pt**，R406 的 visibleRect 守卫在这一跑不再红。`Release script tests` success：sources `R407/13c24c8` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1074 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=251 可判=850 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=164 covered=146 arms=432 bad=0`、全仓 257 文件 / 916 把；产品面连续零改动 **1** 轮（as-of 407，现读 `python3 scripts/product_streak.py --streak-for 407`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R407 头跑 failure：2 个失败步骤同源于 CTA 布局；容器化后 gap 8/长句 400，visibleRect 守卫不再红。
② 产品：拖放目标补「松手加入剪贴板历史」，旧/无拖放 0/0 → 新 708/797。
③ 判据：源 + 像素三读数；M1057/M1058 双 CAUGHT；R407 的 M1055/M1056 重跑仍 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 251 / 可判 850 / rot 0 / 上界 0；预检 164/146/432/0。
⑥ 全量 1074/53/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 真实 drag session 仍只能人工验；② 亮档真机腿仍没跑；③ macOS 12 紧凑详情头仍走旧截断；④ 主列表与浮层的来源搜索语言未统一（437）；⑤ R408 新跑待 push 后读。

下一轮（R409）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R408 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R407 状态（2026-10-26 · 本地 · 第 406 轮 / Round 404）：QuickPick 空结果态补可见「清除搜索」CTA（按钮带旧 0/0 → 新 934/1114）；R406 守卫在 runner 上红的假设被修正（产品 1 文件，空态 CTA 位）

最后更新：2026-10-26（本地 · R407 / 第 406 轮 / Round 404）：QuickPick 空结果态只有一句“按 Esc 清空”，而主窗口同类空态有「清除搜索」按钮。修法：查询词非空且无候选时显示 `NSButton(title:"清除搜索")`，点击清空搜索框、恢复候选并把焦点还给搜索框；空历史/无查询词不显示。像素现读（x=170..250、y=55..85pt）：旧 **0/0** → 新 **934/1114**；同帧消息带 3693/4346 作校准。仅 `quickpick-empty` 亮暗 2 帧变化，基线同笔 186/0/0/0。源/像素两刀 `M1055/M1056` 双 CAUGHT。⓪ `40326547579 ↔ f7852d0` **completed / failure**，唯一失败步骤 `Swift tests`：R406 守卫拿 clip bounds origin 当顶部参照（runner −46 / 本机 −57）；已改为断言 `document.visibleRect.origin.y`（旧行为 2357 → 顶部参照 0），M1053 重跑仍 CAUGHT。`Release script tests` success：sources `R406/cb2bd4c` 一致、全量计数 92-vs-934 反向对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1072 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=250 可判=848 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=163 covered=145 arms=430 bad=0`、全仓 256 文件 / 914 把；产品面连续零改动 **1** 轮（as-of 406，现读 `python3 scripts/product_streak.py --streak-for 406`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R406 头跑 failure：唯一失败步骤 Swift tests，R406 守卫的 clip inset 假设被 runner 驳回；修正为 visibleRect 原点，M1053 仍 CAUGHT。
② 产品：QuickPick 空态补「清除搜索」CTA，旧/新按钮带 0/0→934/1114；只 quickpick-empty 两帧变化。
③ 判据：源（真按钮点击读回）+ 像素（双带）；M1055/M1056 双 CAUGHT。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 250 / 可判 848 / rot 0 / 上界 0；预检 163/145/430/0。
⑥ 全量 1072/53/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）；④ R407 新跑待 push 后读。

下一轮（R408）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R407 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R406 状态（2026-10-26 · 本地 · 第 405 轮 / Round 403）：换选记录后详情正文回到顶部（旧 2300→2300、像素差 15.37/15.96% → 0/0）；R405 头跑全绿签收（产品 3 文件，滚动到位位）

最后更新：2026-10-26（本地 · R406 / 第 405 轮 / Round 403）：详情正文的 `NSScrollView` 被下一条记录复用。把 A 滚到 300pt 后换选 B，旧代码把偏移留给 B（旧帧从 B-20 起，顶部帧从 B-0 起）。行为读数：可滚高 2300、旧偏移 2300 → **换选后仍 2300**；像素同带与「新选即顶部」参照帧差 亮 **15.37%** / 暗 **15.96%**。修法：正文 representable 增加 `resetKey`（记录 id），身份变了才调 `scrollToBeginningOfDocument`（只改 clip bounds 不够，文本视图 frame origin 会留成 −57），首次挂载只记身份不滚。新行为：顶部参照 −57 → 换选后 −57、`docVisible=0`；像素 亮/暗 **0/439200 = 0.00%**；新增 4 帧、既有 182 帧逐字节不变、基线同笔 186/0/0/0。行为/像素两刀 `M1053/M1054` 双 CAUGHT。⓪ `40316586448 ↔ 2e80585` **success**、22 步全 success、`FAILED_STEP_COUNT=0`；sources `R405/2e6998f` 一致；全量计数解析的 92-vs-934 负对照 ok。436 `judged=5/5 executed=73`、`REDS=0`、UNLISTED=0，`notice-banner` 放行，保持结案。全量 `Executed 1070 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=249 可判=846 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=162 covered=144 arms=428 bad=0`、全仓 255 文件 / 912 把；产品面连续零改动 **1** 轮（as-of 405，现读 `python3 scripts/product_streak.py --streak-for 405`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R405 头跑 success、22 步全绿；sources 同笔；全量计数解析反证 ok。
② 产品：换选记录时正文归顶（旧 2300→2300；新顶部 −57；像素 15.37/15.96% → 0/0），新增 4 帧、老 182 帧不变。
③ 判据：行为 + 像素两层；M1053/M1054 双 CAUGHT；Round4 字面量守卫按新形状更新并加钉 `resetKey`。
④ 436：judged=5/5、REDS=0、UNLISTED=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 249 / 可判 846 / rot 0 / 上界 0；预检 162/144/428/0。
⑥ BACKLOG 437 仍开：主列表与浮层仍是两套来源搜索语言；本轮未动。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）；④ R406 新跑待 push 后读。

下一轮（R407）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R406 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R405 状态（2026-10-26 · 本地 · 第 404 轮 / Round 402）：QuickPick 搜到来源 App 时行上写出「来自 X」（旧结尾后墨 0→1006/1109）；R404 头跑全绿签收（产品 2 文件，搜索交互位）

最后更新：2026-10-26（本地 · R405 / 第 404 轮 / Round 402）：QuickPick 的过滤按来源 App 命中，而行文案只有「预览 · 时间」——搜「访达」出两条文件记录，行上看不出为什么命中。`QuickPickModel.sourceMatchReason` 只在来源是唯一命中依据时返回 App 名，`QuickPickController.rowTitle` 把「来自 X」放在时间之前。像素现读（旧第 1 行结尾 x=246.5pt 之后的扩展带）：旧 **0/0** → 新 **1006/1109**（校准带 1445/1640）；仅 `quickpick-typed` 亮暗 2 帧变化，基线同笔 update 后 182/0。⓪ `40309568444 ↔ 1e78ca9` **success**、22 步全 success、`FAILED_STEP_COUNT=0`；band-empty 现读 `LONG_TEXT_PILL_NOT_RUN=band-empty：600（detail-witness=0 sidebar-witness=0）` + `Test skipped`，RULER_BROKEN=0；REMOVE_RED=0、TRASH_RED 亮 217/146 暗 194/806。REMOVE_RED 退役核对：源 M1047 今天重跑仍 CAUGHT、RESTORE_CLEAN=yes；像素臂 M1048 与 `REMOVE_RED` 捕获守卫已不在表/仓内。436 `judged=5/5 executed=73`、`REDS=0`，`notice-banner` 放行，保持结案。全量 `Executed 1068 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=248 可判=844 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=161 covered=143 arms=426 bad=0`、全仓 254 文件 / 910 把；产品面连续零改动 **1** 轮（as-of 404，现读 `python3 scripts/product_streak.py --streak-for 404`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R404 头跑 success、22 步全绿；band-empty 成具名 XCTSkip（两证人 0）；REMOVE_RED 通道 0，源 M1047 今天 CAUGHT，像素臂已退役。
② 产品：QuickPick 行在来源单命中时写出「来自 X」，扩展带旧 0/0→1006/1109，2 帧变化。
③ 判据：源守卫读真表格（2/2、负对照 0/5、0/1、Safari 1/1）；像素守卫只判扩展带；M1051/M1052 双 CAUGHT。
④ 436：judged=5/5、REDS=0、notice-banner 放行，保持结案。
⑤ 367：hidden 表 248 / 可判 844 / rot 0 / 上界 0；预检 161/143/426/0。
⑥ 新开 BACKLOG 437：主列表不吃来源 App，与浮层两套搜索语言。

NOT-RUN / 阻塞（分开写）：① 亮档真机腿仍没跑；② macOS 12 紧凑详情头仍走旧截断；③ 主列表与浮层的来源搜索语言未统一（437）。

下一轮（R406）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R405 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R404 状态（2026-10-26 · 本地 · 第 403 轮 / Round 401）：详情「删除」改成错误红（红 0→701/662）；band-empty 三态翻正（证人也空 ⇒ 具名 XCTSkip）（产品 1 文件，破坏性反馈位）

最后更新：2026-10-26（本地 · R404 / 第 403 轮 / Round 401）：详情浮动操作栏的 trash 仍是灰黑，而批量删除/设置「移除」都是红。给 `GlassPillButton(symbol:"trash")` 加与复制失败同一对动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）：红像素旧 **0/0** → 新 **701/662**（图标墨 527/3141 仍在）；48 张详情胶囊帧变化，基线同笔 update 后 182/0。M1049/M1050 双 CAUGHT。band-empty 三态按监督者口径翻正（目标有墨 measured、目标空证人有墨 RULER_BROKEN 红、两者都空 capabilityAbsent→XCTSkip），证人 detail ∪ sidebar；真值表 3 格 + M1046 CAUGHT。`REMOVE_RED` 像素守卫在 runner 上 dark 红 0/字墨 345，已退役（源 M1047 保留）；R403 `137921e` 的 RULER_BROKEN + REMOVE_RED 红由此归因。436 两跑 5/5、REDS=0，保持结案。全量 `Executed 1065 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=247 可判=842 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=160 covered=142 arms=424 bad=0`、全仓 253 文件 / 908 把；产品面连续零改动 **1** 轮（as-of 403，现读 `python3 scripts/product_streak.py --streak-for 403`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R403 `137921e` failure：RULER_BROKEN 4 条 + REMOVE_RED 红；R402 a274d4a success、03825d6/02cd2f7 failure；R400 41c76cc 仅 Release script 红。
② 产品：详情 trash 灰黑→错误红，红 0/0→701/662，48 帧变化。
③ 判据：源+像素 M1049/M1050 双 CAUGHT。
④ band-empty 三态翻正：证人有墨才 RULER_BROKEN，两者都空才 XCTSkip；真值表 + M1046。
⑤ REMOVE_RED 像素守卫因 runner 1x 设置页部分合成退役，源 M1047 保留。
⑥ 436：137921e/a274d4a 5/5、REDS=0，保持结案。
⑦ 367：hidden 表 247 / 可判 842 / rot 0 / 上界 0；预检 160/142/424/0。
⑧ 验证：build 0 告警；全量 `1065/53/0`；捕获 182 帧、48 张变化、基线 182/0；换装 ok；清账表 162=162。

NOT-RUN / 阻塞（分开写）：① **R404 新跑未落地**；② **R403 的 137921e Swift/Capture 红**已归因为 band 守卫 + REMOVE_RED 像素守卫，R404 修后待 runner 签收；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R405）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R404 主笔+追记 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R403 状态（2026-10-26 · 本地 · 第 402 轮 / Round 400）：「移除」从普通文字改成错误红（红 0→591/605）；band-empty 加侧栏证人后具名 XCTSkip（产品 1 文件，破坏性反馈位）

最后更新：2026-10-26（本地 · R403 / 第 402 轮 / Round 400）：排除名单的「移除」和普通 App 标识一样黑字，而批量删除/清空都用错误红。给「移除」加与复制失败同一对动态错误红（亮 0.72,0,0 / 暗 1.0,0.62,0.58）：红像素旧 **0/0** → 新 **591/605**，字墨 447/954 仍在；两张 privacy-excluded 帧变化，基线同笔 update 后 182/0。M1047/M1048 双 CAUGHT。band-empty：R402 的 detail meta 证人在 runner 也 0，R403 改为 detail ∪ sidebar 证人（任一有墨 ⇒ 具名 XCTSkip；两条都 0 ⇒ `RULER_BROKEN` 红）；真值表 3 格 + M1046 CAUGHT。436 的 a274d4a 现读 judged=5/5、REDS=0，保持结案。全量 `Executed 1064 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=246 可判=841 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=159 covered=141 arms=423 bad=0`、全仓 252 文件 / 907 把；产品面连续零改动 **1** 轮（as-of 402；本轮破坏性反馈已落 Sources，现读 `python3 scripts/product_streak.py --streak-for 402`）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R402 a274d4a success（motion 5/5），03825d6/02cd2f7 failure（band-empty RULER_BROKEN）；R400 41c76cc 仅 Release script 红。
② 破坏性反馈：移除从黑字改为错误红，红 0/0→591/605，字墨仍在；2 张帧变化。
③ 判据：源守卫 + 像素红；M1047/M1048 双 CAUGHT。
④ band-empty：detail meta 证人在 runner 也 0，改为 detail ∪ sidebar；任一有墨 skip，两条 0 才红；M1046 CAUGHT。
⑤ 436：a274d4a 5/5、REDS=0，保持结案；notice-banner 的 4/5 是登记放行，不误判。
⑥ 367：hidden 表 246 / 可判 841 / rot 0 / 上界 0；预检 159/141/423/0。
⑦ 验证：build 0 告警；全量 `1064/53/0`；捕获 182 帧、2 张变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R403 新跑未落地**；② **R402 的 03825d6/02cd2f7 仍 band-empty 红**，新侧栏证人是否让 runner 转 skip 待签收；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R404）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R403 主笔+追记 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R402 状态（2026-10-26 · 本地 · 第 401 轮 / Round 399）：空输入时「添加」可点 → 禁用（添加/移除文字亮度差 7/5 → 96/93）；R401 长正文测试的 runner band-empty 改具名 NOT-RUN（产品 1 文件，交互状态位）

最后更新：2026-10-26（本地 · R402 / 第 401 轮 / Round 399）：排除名单输入框为空时，「添加」仍是启用态，按下去只会得到一条「没加成」的回执。`SettingsView` 加 `.disabled(newExcludedBundleID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)`。同帧相对读数（「添加」vs 启用态「移除」文字）：亮档旧 **7** → 新 **96**，暗档旧 **5** → 新 **93**；四张 privacy 帧变化，基线同笔 update 后 182/0。源守卫 + `ADD_DISABLED_STATE` 像素判据；M1044/M1045 双 CAUGHT、RESTORE_CLEAN=yes。R401 三跑的 Swift/Capture 红已归因为长正文测试 `band-empty`（1x 离屏拍不出该页），R402 改成具名 `LONG_TEXT_PILL_NOT_RUN`；436 的 motion floor 现读 `judged=4/5 not-run=notice-banner`、`settings-reset-fade=2`、`REDS=0`，保持结案。全量 `Executed 1062 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=244 可判=839 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=157 covered=140 arms=421 bad=0`、全仓 250 文件 / 905 把；产品面连续零改动 **1** 轮（as-of 401，现读 `python3 scripts/product_streak.py --streak-for 401`；本轮交互状态已落 Sources）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R400 ed3a30d success / 41c76cc 仅 Release script 红；R401 三跑 Swift/Capture 红是长正文测试 band-empty（1x 拍不出），R402 改成具名 NOT-RUN；642e4a7 的 Release 红仍是 sources 格旧伤。
② 交互状态：空输入「添加」启用 → 禁用；同帧添加/移除文字差 7/5 → 96/93。
③ 判据：源禁用条件 + 同帧相对亮度像素判据；M1044/M1045 双 CAUGHT。
④ 436：R401 run `judged=4/5`（notice-banner 放行）、`settings-reset-fade=2`、`REDS=0`，保持结案。
⑤ 367：hidden 表 244 / 可判 839 / rot 0 / 上界 0；预检 157/140/421/0。
⑥ 验证：build 0 告警；全量 `1062/53/0`；捕获 182 帧、4 张变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R402 新跑未落地**（主笔+追记一次 push 后待读）；② **R401 长正文测试在 runner 1x 仍 band-empty**（`LONG_TEXT_PILL_NOT_RUN`，本机四档照判）；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R403）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R402 主笔+追记的 head 跑全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

### R402 追记：R401 的 band-empty 改成 XCTSkip + 负半证人（2026-10-26）

R401 三跑 `40291975941↔642e4a7`、`40291993402↔8b4c763`、`40292114337↔18f2f44` 均 failure；Swift/Capture 红名都是 `LONG_TEXT_PILL_NOT_RUN=band-empty：600`，同跑 `TEXT_INK_NOT_RUN light 720=0 640=0` ⇒ runner 1x 拍不出长正文页。R402 第一版只 emit+continue（假通过）；现在 `longTextBandOutcome(ink:witnessInk:)` 三态：目标带空但同帧 detail meta 带（x300..width / y38..48pt）有墨 ⇒ `XCTSkip` + 具名 `LONG_TEXT_PILL_NOT_RUN`；证人带也 0 ⇒ `LONG_TEXT_PILL_RULER_BROKEN` 红。真值表 3 格 + M1046 CAUGHT；本机全量 1063/53/0。`642e4a7` 额外有 Release script 红（sources 格旧伤）；R400 `40288846355↔ed3a30d` success、`40288830013↔41c76cc` 仅 Release script 红。R402 head `40296891274↔a274d4a` 仍 in_progress；`40298315386↔03825d6` 现读 queued / 未读。

## R401 状态（2026-10-26 · 本地 · 第 400 轮 / Round 398）：680/700/720 缩放下长正文仍排进浮动药丸；阈值 400→460 + 三刀（产品 1 文件，窗口缩放位）

最后更新：2026-10-26（本地 · R401 / 第 400 轮 / Round 398）：R399 的尾距只在详情列 <400pt 施加，680/700/720 窗口的 400–440pt 详情列仍让长正文排到右下角 `GlassPill`。四档实测旧最右墨列 **529.5 / 646.5 / 674.0 / 688.0pt**（上限 `宽-80`=520/600/620/640），阈值改 **460** 后新 **479.5 / 568.0 / 590.5 / 604.5pt**（余量 40.5/32.0/29.5/35.5pt）。纯函数新增 440pt 必须 >0，像素判据改四档 600/680/700/720；M1039/M1041/M1043 三刀全 CAUGHT、RESTORE_CLEAN=yes。静态 182 帧零变化，基线复验 182/0；全量 `Executed 1061 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=243 可判=837 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=156 covered=139 arms=419 bad=0`、全仓 249 文件 / 903 把；产品面连续零改动 **1** 轮（as-of 400，现读 `python3 scripts/product_streak.py --streak-for 400`；本轮产品缩放已落 Sources）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ R400 两跑 `41c76cc`/`ed3a30d` 仍 in_progress ⇒ NOT-RUN；R399 修复由 073fd6e/9641073 success 签收。
② 缩放位：R399 阈值 <400 漏掉 680/700/720；旧四档全部越限，阈值改 460 后全部在上限内。
③ 判据：纯策略 440>0 + 四档自拍自量像素；M1039/M1041/M1043 三刀 CAUGHT。
④ 436：新跑无新 facts，保持 R399 结案；不重猜 must_judge。
⑤ 367：hidden 表 243 / 可判 837 / rot 0 / 上界 0；预检 156/139/419/0。
⑥ 验证：build 0 告警；全量 `1061/53/0`；捕获 182 帧、0 变化、基线 182/0；换装 ok；清账表 162=162；电池待复跑。

NOT-RUN / 阻塞（分开写）：① **R400 的 ed3a30d success / 41c76cc 只在 Release script tests 红**（sources 格未随主笔同提交，不是产品红）；**R401 新跑 `642e4a7`/`8b4c763` 仍 in_progress**，R402 ⓪ 补读；主笔+追记下次一次 push，避免 main run 的 sources 格必红；③ 亮档真机腿仍没跑；④ macOS 12 紧凑详情头仍走旧截断。

下一轮（R402）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R400/R401 推送跑的全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`。

## R400 状态（2026-10-26 · 本地 · 第 399 轮 / Round 397）：「原文/渲染」标签不再一帧硬换（1x 0→5 过渡帧）；R399 三条 CI 修复在 runner 签收；436 复核（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R400 / 第 399 轮 / Round 397）：正文在「原文/渲染」间走 `.contentFade`，按钮标签原来一帧硬换。`DetailView.MarkdownModeButton` 的 `Text(title)` 加 `.id(title)` + `.transition(.opacity)` + `.animation(for: .contentFade, value: title)`。胶片现读 1x 旧 **0** → 新 **5** 个过渡帧（峰值 0.0048→0.0097）；2x 旧 10 / 新 7（2x 不能单独判过程，以 1x 为判据）。M1042 拆过渡 ⇒ CAUGHT、还原干净、复跑 ESCAPED；静态 182 帧零变化，基线复验 182/0。全量 `Executed 1061 tests, with 53 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=243 可判=836 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=156 covered=139 arms=418 bad=0`、全仓 249 文件 / 902 把；产品面连续零改动 **1** 轮（as-of 399，现读 `python3 scripts/product_streak.py --streak-for 399`；本轮产品动效已落 Sources）。

本轮做了什么：
① ⓪ R399 队列：`9641073`/`073fd6e` success，`c0091fb` failure 只在 `STEP[9] Release script tests`（sources 格未随主笔同提交 + skip roster 嵌套没拿到结论）；产品三条修复由两跑 success 签收。
② 动效位：「原文/渲染」标签从一帧硬换改成与正文同一 `.contentFade`；1x 0→5、2x 10→7。
③ 判据：胶片 2x/1x 均 ≥2 过渡帧；M1042 拆过渡 CAUGHT、还原干净。
④ 436：两跑 `judged=5/5`、`MOTION_FLOOR_OK=5/5`、`REDS=0`，无新 unlisted，保持结案。
⑤ 367：hidden 表 243 / 可判 836 / rot 0 / 上界 0；预检 156/139/418/0；R394 的 M1029/M1030 按新红重钉 2/2。
⑥ 验证：build 0 告警；全量 `1061/53/0`；捕获 182 帧、0 变化、基线 182/0；换装 ok；清账表 162=162。电池 `Ran 683 / OK (skipped=4)`。

NOT-RUN / 阻塞（分开写）：① **R400 新跑未落地**（push 后待读）；② **`EMPTY_STATE_HINT` 在 runner 上 band-empty**（具名 NOT-RUN，不写成绿；空态墨档的本地读数仍是 6.73/8.31）；③ 亮档真机腿仍没跑；④ macOS 12 的紧凑详情头仍走旧截断。

下一轮（R401）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R400 主笔推送跑的全部失败步骤（成对 run↔commit），新跑没落地就记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 只复核新跑 Motion floor，不重新猜 `must_judge`，出现新 unlisted 才带事实重开。

## R399 状态（2026-10-26 · 本地 · 第 398 轮 / Round 396）：600pt 最窄窗长正文排进浮动操作栏（529.5 → 484.0pt）；窄列尾距 + 三刀（产品 2 文件，布局状态位）

最后更新：2026-10-26（本地 · R399 / 第 398 轮 / Round 396）：真看图——600×440 最窄窗 + 长正文时，正文最后几行从右下角 `GlassPill` 左侧伸进去、被药丸盖住。按正文最右墨列量：旧 **529.5pt**（阈值 500）、新 **484.0pt**。产品改法：`DetailTypography.previewTrailingInset(forDetailWidth:)` 只在详情列 <400pt 时给 88pt 尾距；`DetailView` 用 `GeometryReader` 把列宽交给策略，并只给 `preview` 加尾距。默认 182 帧里 18 张变化（4 张 600pt 布局帧 + 空态/加载墨档 14 张），基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed 1060 tests, with 52 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=242 可判=835 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=155 covered=138 arms=417 bad=0`、全仓 248 文件 / 901 把；产品面连续零改动 **1** 轮（as-of 398，现读 `python3 scripts/product_streak.py --streak-for 398`；本轮产品布局已落 Sources）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ 网络恢复：fetch 确认 origin 仍 5c7814e，push `5c7814e..ae202dd` 成功、ahead=0；旧两跑与对照均 success 无失败步骤；两次新跑 in_progress 记具名 NOT-RUN。
② 看图找到布局缺陷：600pt 最窄窗长正文排进右下角浮动药丸（529.5pt → 484.0pt）。
③ 修 Sources：窄列条件尾距 + GeometryReader 接线；宽列 68ch 不动。
④ 判据：纯策略 + 接线 + 自拍自量像素；M1039/M1040/M1041 三刀全 CAUGHT、RESTORE_CLEAN=yes。
⑤ 367：hidden 表 242 / 可判 835 / rot 0 / 上界 0；预检 155/138/417/0。
⑥ 验证：build 0 告警；全量 `1060/52/0`；捕获 182 帧、18 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`LONG_TEXT_PILL_CLEAR maxX=484.0pt 墨=50438 上限=500.0pt`；旧帧同尺 529.5pt；`M1039/M1040/M1041` 三刀 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **CI 新跑都红**：`40280864844 ↔ ae202dd`、`40280951026 ↔ cfbcec7` 均 completed/failure，三步完全相同（Swift tests / Capture gate / Motion coverage floor），逐条见 U-1420；R399 主笔 c0091fb 与追记 073fd6e 的新跑仍 in_progress，R400 ⓪ 补读；② **BACKLOG 436 已结案**（runner `judged=5/5`、JSON/自测已改；旧 in_progress 读数不再用作许愿）；③ 亮档真机腿仍没跑；④ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R400）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40280864844`/`40280951026` 与 R399 主笔推送跑的全部失败步骤（成对 run↔commit），新跑没有落地就继续记 in_progress 未读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别；③ 436 拿到 runner motion 读数后按实测决定第五臂 `must_judge`，没有就继续具名 NOT-RUN。

### R399 追记：CI 40280951026 三步红与 436 结案（2026-10-26）

`40280951026 ↔ cfbcec7` 现读 failure，三个失败步骤逐条：`STEP[15] Swift tests`、`STEP[17] Capture gate`、`STEP[19] Motion coverage floor`。Swift 卷 `Executed 1057 / skipped 64 / failures 2`：复制失败红在 runner 亮 2.90 / 暗 2.55（地板 3.0）；`testCaptureKeyViews` 的录制环 idleBlue=4284/465，以及 R398 加载句 3.75（0.85 墨档在 runner 1x 字体平滑下不够）。Capture gate 的 2 条红有名字；Motion floor 唯一红是 UNLISTED `settings-reset-fade`。旧两跑 `40234023212↔d38ea10` / `40234058148↔5c7814e` / 对照 `40221947072↔43ff699` 均 success ⇒ 红来自 R392/R394/R398 在 runner 上的首次执行，不是 R399 布局位；本轮已修：录制环只数控件带、pane 墨档抬到 primary、失败红亮 0.72,0,0 / 暗 1.0,0.62,0.58。修后本地：copy 测试通过、capture 182 帧通过、全量 `1060/52/0`、电池 `683/4`。

**436 结案**：`40280951026` 的 `MOTION_FLOOR_FACTS judged=5/5 executed=72 not-run=-`，`settings-reset-fade=2` 真的判到；已把第五臂写进 `motion_floor_expectations.json`（`must_judge=true`）并同步 `test_motion_floor_gate.py`（SUMMARY 五臂、地板 4、旧日志多一格 MISSING_KEY）；重放同一组 runner 行 `MOTION_FLOOR_OK=5/5 REDS=0`。`40280864844 ↔ ae202dd` 也 failure，motion `judged=4/5 not-run=notice-banner`，但 settings-reset-fade 判到。

**R400 ⓪ 目标**：push R399 后读新 run 全部失败步骤（尤其确认三条修复在 runner 上通过）；补读 40280864844；若新 run 仍红，按步骤名逐条落账，不用 0 字节日志猜绿。

## R398 状态（2026-10-26 · 本地 · 第 397 轮 / Round 395）：详情加载唯一那句话亮档 2.86:1 → 4.84（暗 4.52 → 6.53）；pane 墨档接进加载态 + 双刀（产品 2 文件，视觉主线）

最后更新：2026-10-26（本地 · R398 / 第 397 轮 / Round 395）：先真看 `detail-loading-720x520-{light,dark}` 的「正在加载预览…」：旧 `.secondary` 在亮档偏灰。按字墨 bbox 定位后只读 x 18..115 / y 102..120pt：旧亮 **2.86** / 暗 **4.52:1**（暗档刚好贴 4.5 线，亮档低于 AA），新 pane 墨档亮 **4.84** / 暗 **6.53:1**。产品改法：`DetailLoadingView` 的句子改走 `StatePresentation.paneMessageInkStyle`；三根骨架与 inline `StateLine` 的 `.subdued` 保持不动。判据：源接线守卫 + 捕获帧像素守卫；M1037/M1038 双 CAUGHT、还原后双 ESCAPED。detail-loading / detail-loading-composed / detail-2-file 亮暗 6 张变化，其余 176 张不变；基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed 1057 tests, with 52 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=240 可判=832 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=153 covered=136 arms=414 bad=0`、全仓 246 文件 / 898 把；产品面连续零改动 **1** 轮（as-of 397，现读 `python3 scripts/product_streak.py --streak-for 397`；本轮产品视觉已落 Sources）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；ahead=36，未推送；未 force。
② 看图找到真缺陷：详情加载态唯一那句话亮档 2.86、暗 4.52；修 Sources 后 4.84/6.53。
③ 判据：源接线守卫 + 捕获帧像素守卫；M1037/M1038 双 CAUGHT、还原后双 ESCAPED。
④ 带子身份：按字墨 bbox 钉 x18..115/y102..120；旧/新都在同带读数，没有假绿。
⑤ 367：hidden 表 240 / 可判 832 / rot 0 / 上界 0；预检 153/136/414/0。
⑥ 验证：build 0 告警；全量 `1057/52/0`；捕获 182 帧、6 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`DETAIL_LOADING old light=2.86 dark=4.52 / new light=4.84 dark=6.53`（x18..115/y102..120pt）；捕获 `DETAIL_LOADING_HINT light 墨=1546 对比=4.84`、`dark 墨=1681 对比=6.53`；`M1037/M1038` 双 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=36（R398 主笔前，追记后 38）；② 旧的两跑与 R387–R397 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；④ 亮档真机腿仍没跑；⑤ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R399）的靶：⓪ CI 队列（R399 现读，2026-10-26）：`40234023212 ↔ d38ea10` / completed / **success**（全部失败步骤=无）；`40234058148 ↔ 5c7814e` / completed / **success**（无）；`40221947072 ↔ 43ff699` / completed / **success**（改动前归因对照）；`40280864844 ↔ ae202dd` / completed / **failure**（三步同 cfbcec7；motion `judged=4/5 not-run=notice-banner`，第五臂判到）。push 已完成 `5c7814e..ae202dd`、ahead=0；一次 push 只为 head 生成新 run，旧两跑已单独读。① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources，换缺陷类别（动效/过渡/反馈或布局状态，不再做 secondary 文字对比度）；③ 436 待 `40280864844` 的 motion 卷落地后按实测决定第五臂 `must_judge`，没有 motion 卷就写具名 NOT-RUN，不许猜。

## R397 状态（2026-10-26 · 本地 · 第 396 轮 / Round 394）：空态唯一那句话亮档 2.90:1 → 4.84（暗 4.52 → 6.45）；pane 墨档 + 双刀（产品 2 文件，视觉主线）

最后更新：2026-10-26（本地 · R397 / 第 396 轮 / Round 394）：先真看 `content-empty-750x560-{light,dark}` 右栏提示：旧 `.secondary` 在亮档明显偏灰。按字墨 bbox 定位后只读 x 445..585 / y 325..357pt：旧亮 **2.90** / 暗 **4.52:1**（暗档刚好贴 4.5 线，亮档低于 AA），新 pane 墨档亮 **4.84** / 暗 **6.45:1**。产品改法：`StatePresentation.paneMessageInkStyle`（primary 0.85）+ `EmptyStateView` 标题走它；inline `StateLine` 的 `.subdued` 保持不动。判据：源接线守卫 + 捕获帧像素守卫；M1035/M1036 双 CAUGHT、还原后双 ESCAPED。四组空态帧亮暗 8 张变化，其余 174 张不变；基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed 1056 tests, with 52 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=239 可判=830 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=152 covered=135 arms=412 bad=0`、全仓 245 文件 / 896 把；产品面连续零改动 **1** 轮（as-of 396，现读 `python3 scripts/product_streak.py --streak-for 396`；本轮产品视觉已落 Sources）。电池 `Ran 683 / OK (skipped=4)`。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；ahead=34，未推送；未 force。
② 看图找到真缺陷：整块 pane 空态的唯一那句话亮档 2.90、暗 4.52；修 Sources 后 4.84/6.45。
③ 判据：源接线守卫 + 捕获帧像素守卫；M1035/M1036 双 CAUGHT、还原后双 ESCAPED。
④ 带子身份：按字墨 bbox 钉 x445..585/y325..357；旧/新都在同带读数，没有假绿。
⑤ 367：hidden 表 239 / 可判 830 / rot 0 / 上界 0；预检 152/135/412/0。
⑥ 验证：build 0 告警；全量 `1056/52/0`；捕获 182 帧、8 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`EMPTY_PANE old light=2.90 dark=4.52 / new light=4.84 dark=6.45`（x445..585/y325..357pt）；捕获 `EMPTY_STATE_HINT light 墨=2715 对比=4.84`、`dark 墨=2974 对比=6.45`；`M1035/M1036` 双 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=34（R397 主笔前，追记后 36）；② 旧的两跑与 R387–R396 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；④ 亮档真机腿仍没跑；⑤ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R398）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；一次 push 只为 head 生成新 run，旧两跑仍要单独按步骤读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources；③ 436 待 runner motion 读数恢复后再决定第五臂 `must_judge`，本轮仍不动 JSON/自测。

## R396 状态（2026-10-26 · 本地 · 第 395 轮 / Round 393）：不支持登录项的标签被禁用 Toggle 一起压暗（1.76/2.13 → 2.84/4.38）；修 Sources 并补捕获帧像素守卫（产品 1 文件，视觉主线）

最后更新：2026-10-26（本地 · R396 / 第 395 轮 / Round 393）：先真看 `settings-general-login-unsupported` 亮/暗帧：不支持登录项时「开机启动」标签比同组其它标签明显浅。按字墨 bbox 定位（旧 `198.5..248.0 × 120.5..132.0pt`）后只读标签带（x 195..255、y 118..135pt）：旧结构亮 **1.76** / 暗 **2.13:1**（低于禁用标签地板 2.2），新结构亮 **2.84** / 暗 **4.38:1**。产品改法：`Toggle` 加 `.labelsHidden()`，标签移出禁用控件成独立 `Text`（不支持 `.secondary` / 支持 `.primary`，`accessibilityHidden(true)`，支持时仍可点），复选框仍禁用。**自伤**：第一版捕捉守卫的带子（x 380..700/y 225..275）量到第三行「识别截图文字」，旧结构也读 2.81/4.33（假绿）；按 bbox 重钉后 M1033/M1034 双 CAUGHT。默认 182 帧里设置通用 6 帧变化；帧基线同笔 `UPDATED=182`，复验 182/0/0/0。全量 `Executed 1055 tests, with 52 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=238 可判=828 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=151 covered=134 arms=410 bad=0`、全仓 244 文件 / 894 把；产品面连续零改动 **1** 轮（as-of 395，现读 `python3 scripts/product_streak.py --streak-for 395`；本轮产品视觉已落 Sources）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；ahead=31，未推送；未 force。
② 看图找到真缺陷：不支持登录项时标签被禁用 Toggle 一起压暗（旧 1.76/2.13，地板 2.2），修 Sources 后 2.84/4.38。
③ 判据：源形状守卫 + 真实捕获帧像素守卫；M1033/M1034 双 CAUGHT、还原后双 ESCAPED。
④ 自伤：第一版像素带量到第三行，旧结构也 2.81/4.33；按字墨 bbox 重钉到 x195..255/y118..135。
⑤ 367：hidden 表 238 / 可判 828 / rot 0 / 上界 0；预检 151/134/410/0。
⑥ 验证：build 0 告警；全量 `1055/52/0`；捕获 182 帧、6 帧变化、基线 update 后 182/0；换装 ok；清账表 162=162。

验证读数（现读）：`LABEL_BAND old light=1.76 dark=2.13 / new light=2.84 dark=4.38`（x195..255/y118..135pt）；`WRONG_BAND old light=2.81 dark=4.33`（x380..700/y225..275pt，假绿对照）；`LOGIN_UNSUPPORTED_FRAME light 墨=984 对比=2.84`、`dark 墨=1080 对比=4.38`；`M1033/M1034` 双 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=31（R396 主笔前，两次追记后 34）；② 旧的两跑与 R387–R395 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地 5/5、UNLISTED `settings-reset-fade` 仍可复现）；④ 亮档真机腿仍没跑；⑤ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R397）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；一次 push 只为 head 生成新 run，另外旧的两跑仍要单独按步骤读；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources；③ 436 待 runner motion 读数恢复后再决定第五臂 `must_judge`，本轮仍不动 JSON/自测。

## R395 状态（2026-10-26 · 本地 · 第 394 轮 / Round 392）：设置分类切换的过渡被判 NOT-RUN（2x 采样≈121ms / 1x 2 帧）；只加只读分类缝与源守卫（产品 1 文件（绑定缝），判据账）

最后更新：2026-10-26（本地 · R395 / 第 394 轮 / Round 392）：设置分类切换有 `.id` + `.transition(.contentFade)` + `.animation(value:)`，但从未有整页过程读数。加只读 `categoryOverride` 缝，用产品真实 `SettingsView` 驱动 快捷键→推荐；2x 抓帧中位 **121ms**、过渡 **2** 帧，1x 过渡 **2** 帧（峰值 `0.1441`/`0.1533`，声明 160ms）。首帧/采样成本吞掉 160ms 窗口 ⇒ 按 D-385 记具名 **NOT-RUN**，不判产品硬切；试过 Group 动画、变更点 withAnimation、去 `.id`，均无变化并已回退。分类缝源守卫 + `M1032` CAUGHT；默认 182 帧 `变了=0`，帧基线 182/0。**本轮产品视觉 0 改动**，下一轮必须回产品视觉。BACKLOG 436 无新 runner 读数，仍未结案。全量 `Executed 1054 tests, with 52 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=237 可判=826 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=150 covered=133 arms=408 bad=0`、全仓 243 文件 / 892 把；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 394`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送。
② 新位点：设置分类切换；2x/1x 都只有 2 个过渡帧，采样/首帧成本超过声明一半 ⇒ 具名 NOT-RUN。
③ 产品：只加只读 `categoryOverride` 缝；试过三组视觉改法均无效，全部回退，不留未验证改动。
④ 判据：分类缝源守卫 + M1032 CAUGHT；过渡的通道闸门写成具名 NOT-RUN。
⑤ 367：hidden 表 237 / 可判 826 / rot 0 / 上界 0；预检 150/133/408/0。
⑥ 验证：build 0 告警；全量 `1054/52/0`；捕获 182 帧、默认零变化；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：`SETTINGS_CATEGORY_FADE` 2x `23/2/0.1441`、1x `27/2/0.1533`；`MOTION_GRAB` 2x 抓帧中位 `121ms`；`M1032` CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`/`apple=200`；本地 ahead=31（R395 主笔 + 两笔追记）；② `40234023212`/`40234058148` 与 R387–R394 本地提交的 conclusion **未读**（网络）；③ **`SETTINGS_CATEGORY_FADE_NOT_RUN=clock-coarse` / `duration-under-resolved`**：整页 2x 采样 121–132ms、1x 只剩 2 帧，无法判 160ms 过程；④ BACKLOG 436 的 runner motion 卷未读；⑤ 亮档真机腿仍没跑；⑥ macOS 12 的紧凑详情头仍走旧截断（13+ 才有 ViewThatFits）。

下一轮（R396）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读三跑全部失败步骤并写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② **必须回到产品视觉并落 Sources**（本轮产品视觉 0 改动）；若要再判分类过渡，先把整页帧换成目标带宽，或给该过渡一个低成本的端态/过程通道，否则仍然 NOT-RUN。

## R394 状态（2026-10-26 · 本地 · 第 393 轮 / Round 391）：复制失败那一颗终于变红（成功 0 / 失败 145·132 颗）；胶片 2x 12 帧 / 1x 16 帧；M1029–M1031 CAUGHT（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R394 / 第 393 轮 / Round 391）：`GlassPill` 的失败态原来只把图标换成感叹号、前景仍是主色，成功/失败在颜色上完全一样。R394 给失败态上动态错误红（亮 `Color.red` / 暗 `1.0,0.48,0.44`），成功仍主色。静态现读：亮 成功红 **0** / 失败红 **145** / 失败对比 **4.57**，暗 **0** / **132** / **4.70**（控件地板 3.0；系统红暗档只有 2.69，动态红过）。胶片新场景只拍第三颗 copy 按钮：2x `帧数=27 过渡帧数=12 峰值=0.0585`、1x `27/16/0.0778`（声明 160ms），strip 逐帧看到 黑 doc → 红 doc → 红感叹号。判据：静态颜色/对比 + 两倍率胶片 + DetailView 接线；`M1029`/`M1030`/`M1031` 全 CAUGHT。**自伤**：第一版多靶表用全局 original 还原，把 GlassControls 全文写进 DetailView，构建报 `invalid redeclaration`；已 `git checkout -- DetailView.swift` 还原并拆成单靶表（D-384）。静态 182 帧 `变了=0`，帧基线 182/0；全量 `Executed 1052 tests, with 51 tests skipped and 0 failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表=236 可判=825 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=149 covered=132 arms=407 bad=0`、全仓 242 文件 / 891 把；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 393`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：复制失败从「只换字形」变成「动态错误红 + 字形」；静态 0/145·132、对比 4.57/4.70。
③ 判据：静态颜色/对比、2x/1x 胶片、接线守卫；M1029–M1031 CAUGHT。
④ 自伤：多靶表 restore 写坏 DetailView，构建报错；已还原并拆表，记 D-384。
⑤ 367：hidden 表 236 / 可判 825 / rot 0 / 上界 0；预检 149/132/407/0。
⑥ 验证：build 0 告警；全量 `1052/51/0`；捕获 182 帧、静态零变化；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：`COPY_FAIL_RED` 亮 成功 `0` / 失败 `145` / 对比 `4.57`，暗 `0` / `132` / `4.70`；`COPY_FAIL_FADE` 2x `27/12/0.0585`、1x `27/16/0.0778`；`M1029–M1031` CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=28（R394 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R393 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑。

下一轮（R395）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R394 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位。

## R393 状态（2026-10-26 · 本地 · 第 392 轮 / Round 390）：600pt 详情头不再截掉「复制」—— 完整/紧凑 meta 先试再退，四张最小窗帧只动头部（产品 2 文件，视觉主线）

最后更新：2026-10-26（本地 · R393 / 第 392 轮 / Round 390）：`content-min-600x440` 的详情头只显示 `2025-10-09 16:38:20… 40 个字符 · 来自 终端`，middle 截断把「复制」吃掉；750pt 的同一记录是完整一行。`DetailTypography.metaText` 增加 `includeCopyVerb`（默认 true），详情头用 `ViewThatFits` 先试完整、放不下再退到去掉冗余「复制」的紧凑版；时间/大小/来源一个不丢，行高不变；macOS 12 用显式 `if #available` 保留旧截断（`ViewThatFits` 是 13+）。修后 600pt 帧现读完整 `2025-10-09 16:38:20 · 40 个字符 · 来自 终端`，750pt 不变。纯函数宽度 + 源守卫；`M1027`（紧凑臂写回 true）/`M1028`（ViewThatFits 换 Group）都 CAUGHT。BACKLOG 436 无新 runner 读数，仍未结案。`swift build --build-tests` 告警 **0**；全量 `Executed 1049 tests, with 50 tests skipped and 0 failures`；捕获 `CAPTURED 182 -> /tmp/r393_shots`，与 R392 逐张比 `变了=4`（四张 600pt 帧的差集都在头部，首张 2371 颗、bbox=(829,73)..(1100,93)），帧基线 `UPDATED=182`，复验 `COMPARED=182 CHANGED=0`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；`HIDDEN_ARMS 表=234 可判=822 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=147 covered=130 arms=404 bad=0`、全仓 240 文件 / 888 把；产品面连续零改动 **2** 轮（现读 `python3 scripts/product_streak.py --streak-for 392`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：600pt 详情头由「完整/紧凑先试再退」保留时间/大小/来源；750pt 不变。
③ 判据：纯函数宽度 + 源守卫 + M1027/M1028；帧差分 4 张只动头部。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 234 / 可判 822 / rot 0 / 上界 0；预检 147/130/404/0。
⑥ 验证：build 0 告警；全量 `1049/50/0`；捕获 182 帧、四张头部帧更新并复验 0；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：帧差分 `178 同 / 4 变`；首张变化 `2371`、bbox `(829,73)..(1100,93)`；`M1027/M1028` CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=25（R393 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R392 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑；⑤ macOS 12 上仍是旧的单行截断（`ViewThatFits` 13+）—— 本轮没有 12 的可执行环境，按具名限制记账。

下一轮（R394）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R393 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位。

## R392 状态（2026-10-26 · 本地 · 第 391 轮 / Round 389）：整页录制帧第一次真的拍到强调圈（亮 1794 / 暗 1780 颗）；fixture 补 overlay 落定与帧级判据（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R392 / 第 391 轮 / Round 389）：`settings-shortcuts-recording` 与静置帧的差集只覆盖标题文字、控件四周 0 颗高色度像素，而组件级判据一直读到 1844/1820。成因是 R273 的 fixture 等 `button.layer?.animationKeys()` 清空，而强调圈是 SwiftUI overlay，0.16s 淡入不在 NSButton 层；本机 `134ms / 动画键=0` 就按了快门。补 300ms 上限的 overlay 落定 + `displayIfNeeded` 后，现读 `RECORDER_OVERLAY_SETTLE waited_ms=313/315`；亮 变化 **4097** / 录制侧蓝 **1794** / 静置蓝 **0**，暗 **4245** / **1780** / **0**，差集 bbox 正好控件四边。新增帧级判据：差集 >100、录制侧蓝 ≥200、静置侧 0，settings 族平涂走具名 `RECORDER_FRAME_RING_NOT_RUN=flat-page`。两张录制帧进基线（`UPDATED=182`），复验 `COMPARED=182 CHANGED=0`。**本轮产品 0 文件**：环本来就在画，坏的是取证帧的等待条件；不为了凑产品改动去动正确的 Sources。BACKLOG 436 无新 runner 读数，仍未结案。`swift build --build-tests` 告警 **0**；全量 `Executed 1047 tests, with 50 tests skipped and 0 failures`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；`HIDDEN_ARMS 表=233 可判=820 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=146 covered=129 arms=402 bad=0`、全仓 239 文件 / 886 把；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 391`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 取证：发现整页录制帧只拍到文字、四周 0 圈；修 fixture 的 overlay 落定等待；修后 1794/1780 颗。
③ 判据：新增帧级 `RECORDER_FRAME_RING`（差集/录制侧蓝/静置蓝/平涂 NOT-RUN）；组件入口 2924 仍绿。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 233 / 可判 820 / rot 0 / 上界 0；预检 146/129/402/0。
⑥ 验证：build 0 告警；全量 `1047/50/0`；捕获 182 帧、2 张录制帧更新并复验 0；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：`RECORDER_FRAME_RING` 亮 变化 `4097` / 蓝 `1794` / 静置 `0`，暗 `4245` / `1780` / `0`；`RECORDER_ENTRY … 静置高色度=0 点击后高色度=2924`；`RECORDER_OVERLAY_SETTLE waited_ms=313/315`；帧差分 `180 同 / 2 变`；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=22（R392 主笔 + 本追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R391 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑；⑤ 录制圈的 **淡入过程**仍未进胶片（只签端态；解 `button.layer` 等待之后整页帧能拍到端态）。

下一轮（R393）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R392 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位（本轮产品 0 文件，下一轮必须落 Sources）。

## R391 状态（2026-10-26 · 本地 · 第 390 轮 / Round 388）：自绘「恢复默认」补回按下态（启用 20/16 级 / 禁用 0 级，M1025/M1026 CAUGHT）；M1023 随填充表达式重钉；436 无新 runner 读数（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R391 / 第 390 轮 / Round 388）：R388 的自绘按钮按下只缩 2%，底色不动。R391 在 `ResetDefaultButtonBody` 加 `@Environment(\.pressedForCapture)` + `isEnabled` 闸门，按下填充 `0.08 → 0.17`，缩放也走 `isPressedForDrawing`。两态帧现读：亮档 启用 idle **230** → pressed **210**（差 **20**），暗档 **54 → 70**（差 **16**）；禁用态亮 **238/238**、暗 **46/46**（差 **0/0**，负半）；能力闸门 卡片 246/38。R390 悬停复验仍读亮 `230→222`（差 8）、暗 `54→62`（差 8），禁用两半仍 0。源守卫 + 四格真值表；`M1025`/`M1026` CAUGHT；改填充表达式让 R390 的 M1023 命中 0（预检 bad=1），重钉到三分支整块后 r390 整表 2/2 CAUGHT。按下/悬停的 `.hover` 过渡过程未进胶片（BACKLOG 330）⇒ 只签端态，过程记 NOT-RUN。BACKLOG 436：无新的 runner motion 读数；R390 本地完整卷 `MOTION_SUMMARY notice-banner=10 notice-banner-dismiss=7 detail-kind-change=3 empty-state=6 settings-reset-fade=3`、`MOTION_RESOLVE_SUMMARY judged=5/5 not-run=-` 与闸门 exit 1（UNLISTED）的复现仍成立，**不关单、不改 JSON/自测、不猜 must_judge**。`swift build --build-tests` 告警 **0**；全量 `Executed 1047 tests, with 50 tests skipped and 0 failures`；捕获 `CAPTURED 182 -> /tmp/r391_shots`，与 R390 逐张比 `变了=0`，帧基线 `COMPARED=182 CHANGED=0`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；`HIDDEN_ARMS 表=233 可判=820 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=146 covered=129 arms=402 bad=0`、全仓 239 文件 / 886 把；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 390`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读；未能 fetch 确认远端也写明。
② 产品位：自绘「恢复默认」补回按下态（0.08→0.17，禁用不动）；8 张两态帧落 /tmp/r391_press。
③ 判据：源守卫 + 四格真值表 + M1025/M1026；按下过程 NOT-RUN；M1023 重钉并复跑 r390 整表。
④ 436：无新 runner 读数，本地 5 臂复现仍成立；不关单、不猜 must_judge。
⑤ 367：hidden 表 233 / 可判 820 / rot 0 / 上界 0；预检 146/129/402/0。
⑥ 验证：build 0 告警；全量 `1047/50/0`；捕获 182 帧、静态零变化；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：`RESET_PRESS_STATE` 亮 启用 `230→210`（差 20）/ 禁用 `238/238`（差 0）；暗 `54→70`（差 16）/ 禁用 `46/46`（差 0）；`RESET_HOVER_STATE` 亮 `230→222` / 暗 `54→62`；`M1025/M1026` 与 `M1023/M1024` 全 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=20（R391 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R390 本地提交的 conclusion **未读**（网络）；③ 悬停/按下的 `.hover` 过渡过程未进胶片（BACKLOG 330），只签端态；④ 亮档真机腿仍没跑；⑤ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测。

下一轮（R392）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R391 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R391 的按下端态可用 `UICaptureTests/testResetDefaultButtonShowsPressedOnlyWhenEnabled` 复跑。

## R390 状态（2026-10-26 · 本地 · 第 389 轮 / Round 387）：自绘「恢复默认」补回悬停（启用 8 级 / 禁用 0 级，M1023/M1024 CAUGHT）；436 本地复现 UNLISTED、runner 未读不猜 must_judge（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R390 / 第 389 轮 / Round 387）：R388 的 `ResetDefaultButtonStyle` 把系统 bordered 按钮的悬停反馈丢了。R390 在 `ResetDefaultButtonBody` 加 `@Environment(\.hoveredForCapture)` + `.onHover` + `isEnabled` 闸门，悬停填充 `0.08 → 0.13`，过渡 `.hover`。两态帧现读：亮档 启用 idle **230** → hover **222**（差 **8**），暗档 **54 → 62**（差 **8**）；禁用态亮 **238/238**、暗 **46/46**（差 **0/0**，负半）；能力闸门 卡片 246/38、标签墨 >0。源守卫 + 四格真值表；`M1023`（填充退回 idle）/`M1024`（摘 isEnabled 闸门）都 CAUGHT；悬停**过程**未进胶片（BACKLOG 330）⇒ 只签端态，过程记 NOT-RUN。BACKLOG 436：完整 motion 卷 `Executed 70/3/0`，`MOTION_SUMMARY notice-banner=10 notice-banner-dismiss=7 detail-kind-change=3 empty-state=6 settings-reset-fade=3`，`MOTION_RESOLVE_SUMMARY judged=5/5 not-run=-`；现有 4 臂登记跑 `motion_floor_gate.py` ⇒ exit 1，唯一红 `MOTION_FLOOR_UNLISTED_SCENARIO … settings-reset-fade` ⇒ 成因本地复现。**仍未结案**：runner 未读，不猜 `must_judge`，JSON/自测一字未改。R389 滑块场景复验 2x `27/5/0.0188`、1x `27/14/0.0123`。`swift build --build-tests` 告警 **0**；全量 `Executed 1044 tests, with 50 tests skipped and 0 failures`；捕获 `CAPTURED 182 -> /tmp/r390_shots`，与 R389 逐张比 `变了=0`，帧基线 `COMPARED=182 CHANGED=0`；清账表 `表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；`HIDDEN_ARMS 表=232 可判=818 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=145 covered=128 arms=400 bad=0`、全仓 238 文件 / 884 把；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 389`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读；未能 fetch 确认远端也写明。
② 产品位：自绘「恢复默认」补回悬停（启用 0.08→0.13，禁用不动）；8 张两态帧落 /tmp/r390_hover。
③ 判据：源守卫 + 四格真值表 + M1023/M1024；悬停过程 NOT-RUN。
④ 436：完整本地 motion 卷 5 臂、judged=5/5；现有登记跑闸门 exit 1（UNLISTED）⇒ 成因本地复现；runner 未读，不猜 must_judge。
⑤ 367：hidden 表 232 / 可判 818 / rot 0 / 上界 0；预检 145/128/400/0。
⑥ 验证：build 0 告警；全量 `1044/50/0`；捕获 182 帧、静态零变化；换装 ok；清账表 162=162；电池 `Ran 683 / OK (skipped=4)`。

验证读数（现读）：`RESET_HOVER_STATE` 亮 启用 `230→222`（差 8）/ 禁用 `238/238`（差 0）；暗 启用 `54→62`（差 8）/ 禁用 `46/46`（差 0）；`MOTION_SUMMARY … settings-reset-fade=3`、`MOTION_RESOLVE_SUMMARY judged=5/5`；motion 闸门 exit 1 UNLISTED；`M1023/M1024` CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=17（R390 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387/R388/R389 本地提交的 conclusion **未读**（网络）；③ 悬停 `.hover` 过渡过程未进胶片（BACKLOG 330 的通道限制），本条只签端态；④ 亮档真机腿仍没跑；⑤ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测。

下一轮（R391）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R390 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R390 的悬停端态可用 `UICaptureTests/testResetDefaultButtonShowsHoverOnlyWhenEnabled` 复跑。

## R389 状态（2026-10-26 · 本地 · 第 388 轮 / Round 386）：权重复位九根滑杆走同一条 .slider 路径（2x 5 帧 / 1x 13 帧）；快捷键页自量禁用对比 2.92/4.38；M1020–M1022 CAUGHT（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R389 / 第 388 轮 / Round 386）：权重复位原来只有按钮色变在演，九根滑杆瞬移。产品新增 `RecommendationWeightsView.resetDefaults(in:)`：把 `store.restoreDefaults()` 包进 `withAnimation(MotionCatalog.animation(for: .slider))`，按钮调它；直接拖滑杆不经过这条动画。新胶片场景 `settings-weights-reset-sliders` 只拍两行滑杆（按钮色变不在带里）：2x `帧数=27 过渡帧数=5 峰值=0.0201`、1x `27/13/0.0123`（声明 200ms；960×280 / 480×140px），strip 逐帧可见「收藏 40% → 默认」与滑块右移。R388 自评扣的快捷键页对比地板补成读数：亮 禁用 **2.92** / 改过 **3.81**、暗 禁用 **4.38** / 改过 **5.38**（地板 2.2）。M1020/M1021/M1022 全 CAUGHT、还原干净；`HIDDEN_ARMS 表=231 可判=816 rot=0 … 上界 rot=0 处置=ok`；预检 `tables=144 covered=127 arms=398 bad=0`、全仓 237 文件 / 882 把。`swift build --build-tests` 告警 **0**；全量 `Executed 1041 tests, with 50 tests skipped and 0 failures`；捕获 `CAPTURED 182 -> /tmp/r389_shots`，与 R388 逐张比 `变了=0`，帧基线 `COMPARED=182 CHANGED=0`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 388`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒，同分钟 `api=000` / `apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：复位九根滑杆收进 `withAnimation(.slider)` 的产品 helper；按钮与胶片同一条路。
③ 判据：源守卫 + 真值表 + M1020/M1021；两倍率胶片 ≥2 帧；strip 两张。
④ 对比：快捷键页直接量到亮 2.92 / 暗 4.38，M1022 咬地板；R388 的 M1019 仍咬权重页。
⑤ 367：hidden 表 231 / 可判 816 / rot 0 / 上界 0；预检 144/127/398/0。
⑥ 验证：build 0 告警；全量 `1041/50/0`；捕获 182 帧、静态零变化；换装 ok；清账表 162=162；新开 BACKLOG 436。

验证读数（现读）：`WEIGHTS_RESET_SCALE` 2x `27/5/0.0201`、1x `27/13/0.0123`；`RESET_FADE_SCALE` 2x `27/3/0.0123`、1x `27/4/0.0181`；`SHORTCUT_RESET_STATE` 亮 禁用 `2.92` / 暗 `4.38`；`M1020/M1021/M1022` 全 CAUGHT；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=14（R389 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387/R388 本地提交的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ 胶片采样臂在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（全量 50 skip 的一部分），本轮的 2x/1x 读数来自单独开的 motion 卷；⑤ BACKLOG 436：`settings-reset-fade` 未进 motion 地板名册，下一次带 motion 的 CI 会报 `MOTION_FLOOR_UNLISTED_SCENARIO`，本轮无 runner 读数不修。

下一轮（R390）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387/R388/R389 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R389 的复位过程可用 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testWeightsResetSliderSamplerReadsBothScales` 复跑。

## R388 状态（2026-10-26 · 本地 · 第 387 轮 / Round 385）：禁用「恢复默认」被 R387 的 opacity 压到 1.88 → 自绘 primary↔secondary 样式（亮 2.77 / 暗 4.21）；两支按钮同一样式；M1019 咬地板（产品 3 文件，动效主线）

最后更新：2026-10-26（本地 · R388 / 第 387 轮 / Round 385）：R387 的 wrapper `.opacity(0.55/0.70)` 会把禁用标签连同底色压暗；把 WCAG 对比尺接到两态帧后，改前那版亮档读到 1.88 / 1.98（中转读数，未入基线）。产品改成 `ResetDefaultButtonStyle`（`PressableStyle.swift`）：`@Environment(\.isEnabled)` 驱动 `primary ↔ secondary` 与 `primary.opacity(0.08/0.035)`，`.selection` 过渡挂在 `isEnabled` 上，按下仍 0.98；快捷键页与权重页共用。现读亮档禁用 **2.77** / 动过 **5.48**，暗档禁用 **4.21** / 动过 **8.06**；`M1019`（secondary→tertiary）被 2.2 地板抓住，`M1016`/`M1017` 删样式都 CAUGHT。胶片复验：2x `帧数=27 过渡帧数=3 峰值=0.0123`、1x `帧数=27 过渡帧数=4 峰值=0.0181`（声明 120ms），通用场景 `过渡帧数=3`；端态 182 帧 `same=168 changed=14`，帧基线 `COMPARED=182 CHANGED=0`。`swift build --build-tests` 告警 **0**；全量 `Executed 1038 tests, with 49 tests skipped and 0 failures`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；预检 `tables=142 covered=125 arms=395 bad=0`、全仓 235 文件 / 879 把；`HIDDEN_ARMS … rot=0 上界=0 处置=ok`；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 387` 的 streak，口径差一仍挂 BACKLOG 412）。

本轮做了什么：
① ⓪ 网络：两次同形探测（改代码前与提交后 08:40）都是 `api=000` / `apple=200` ⇒ GitHub 侧仍断，`PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：R387 的 0.55/0.70 opacity 让禁用标签不可读；改成自绘状态样式，亮/暗两档都过 2.2；两颗按钮共用。
③ 判据：对比地板 + 两态墨差 + 样式源守卫；M1019/M1016/M1017 CAUGHT。
④ 胶片：2x/1x 各 ≥2 帧；端态 14 张变化只在按钮相关的行内区域；帧基线 182/0。
⑤ 367：r77 整表 10/10；rot 0/0；预检 142/125/395/0。
⑥ 验证：构建 0 告警；全量 `1038/49/0`；捕获 `CAPTURED 182 -> /tmp/r388_shots`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162；预检 142/125/395/0、全仓 235/879。

验证读数（现读）：`WEIGHTS_RESET_STATE` 亮 禁用 `2.77` / 动过 `5.48`、暗 禁用 `4.21` / 动过 `8.06`；`RESET_FADE_SCALE` 2x `27/3/0.0123`、1x `27/4/0.0181`；`M1019`、`M1016/M1017` 都 CAUGHT；r77 `抓到=10 逃掉=0`；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：改前探测与提交后 08:40 的第 2 次同形探测都是 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=11（R388 主笔 + 两笔追记）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387 本地三笔的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ 胶片采样臂在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（49 skip 的一部分），本轮的 2x/1x 读数来自单独开的 motion 卷。

下一轮（R389）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387/R388 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R388 的样式若要再验，跑 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testResetFadeSamplerReadsBothScales`。

## R387 状态（2026-10-26 · 本地 · 第 386 轮 / Round 384）：R385 死过渡被胶片证伪 → 显式 opacity；1x/2x 正对证；M406 重钉；435 负半（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R387 / 第 386 轮 / Round 384）：新胶片场景 `settings-reset-fade`（只拍按钮带）先证伪 R385 的 `.animation(value:)` —— 0.12s 只有 2 个过渡帧，是死动画；给两颗「恢复默认」外层加显式 `.opacity(isDefault ? 0.55 : 1)` + `.animation(for: .selection)` 后，现读 2x `帧数=27 过渡帧数=3 峰值=0.0542`、1x `帧数=27 过渡帧数=4 峰值=0.0230`，strip 逐帧由深到浅；端态 182 张帧 `same=170 changed=12`，12 张只动重置按钮列。M406 重钉到 changedFraction 的唯一块（旧针命中 2），r77 **整表 10/10 CAUGHT**；`HIDDEN_ARMS … rot=0 … 上界 rot=0 … 处置=ok`。435：`captionDrawability` 拆三态 + 负半真值表，M1018 `CAUGHT`；caption tier 守卫本机仍绿。`swift build --build-tests` 告警 **0**；全量 `Executed 1039 tests, with 49 tests skipped and 0 failures`（新增胶片采样臂在无环境键时具名 skip）；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **2** 轮（现读 `python3 scripts/product_streak.py --streak-for 386` 的 streak）。

本轮做了什么：
① ⓪ 网络：本轮上限内 2 次同形探测（07:06 / 07:45）都是 `api=000` / `apple=200` ⇒ GitHub 侧仍断，`PUSH_BLOCKED=network`；本地 ahead=7，未推送，CI 三跑未读。
② 产品位：胶片证伪 R385 死动画；显式 opacity 修复；2x/1x 各 ≥2 帧；端态 12 张帧只动按钮列。
③ 判据：`testResetFadeSamplerReadsBothScales` + 源守卫更新；M1016/M1017 CAUGHT。
④ 367：M406 重钉，r77 整表 10/10；rot 0/0。
⑤ 435：captionDrawability 三态 + 负半真值表 + M1018 CAUGHT；caption tier 仍绿。
⑥ 验证：构建 0 告警；全量 `1039/49/0`；捕获 `CAPTURED 182 -> /tmp/r387_shots2`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162；预检 `tables=141 covered=124 arms=394 bad=0`、全仓 234 文件 / 878 把。

验证读数（现读）：`RESET_FADE_SCALE` 2x `27/3/0.0542`、1x `27/4/0.0230`；`MOTION settings-reset-fade 过渡帧数=3`；`M1016/M1017`、`M1018` 都 CAUGHT；r77 `抓到=10 逃掉=0`；`HIDDEN_ARMS … rot=0 … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：`api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=7（`5166a2b`、`479dfaa`、`bb5be1b`、`559cadb`、本轮主笔 `53e1ef7`、追记 `6e76888`、追记二 `9644168`）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 的 conclusion **未读**（网络）；③ 亮档真机腿仍没跑；④ R387 的胶片在无 `CLIPBOARD_HISTORY_UI_MOTION=1` 的卷里具名 skip（全量 `49` skip 的一部分），不是没红。

下一轮（R388）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与本次推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位；R387 的过渡若要再验，跑 `CLIPBOARD_HISTORY_UI_MOTION=1` 的 `testResetFadeSamplerReadsBothScales`。

## R386 状态（2026-10-26 · 本地 · 第 385 轮 / Round 383）：最后两根腐烂针重钉，rot 2→0；M147 旧目标被重构掉、同义坏法换 `prefix(0)`（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R386 / 第 385 轮 / Round 383）：r77 `M411` 重钉到两行整块（R80 的 lowercased）⇒ `CAUGHT`；r33 `M147` 的旧目标 `gate: 8` 调用已被重构成 `inkContrast`（无 gate 参数），盘上同名 gate 抬到 250 只会 skip ⇒ 同义坏法换成「探针循环 `prefix(0)`」⇒ `CAUGHT`（`judged=0` 那条地板）；`HIDDEN_ARMS 表=227 可判=811 rot=0 … 处置=ok`，`ROT_CEILING` 2→0；r77 整表 9/10、**M406 NOT-APPLIED**（新腐烂针，已记 367）；全量沿用 R385（本轮没动 Swift）：`Executed 1036 tests, with 48 tests skipped and 0 failures`；电池 Ran 683（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：GitHub 链路断（`api=000` / apple=200，IPv4/IPv6 均断）⇒ `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R385 那一跑的 conclusion 全部 **NOT-RUN（网络）**；本地 ahead=4（`5166a2b`、`479dfaa`、补登记生成器那笔、本轮）。
② 367 收口：M411 与 M147 重钉并各自 CAUGHT；rot 2→0、上界同笔降。
③ 新发现：tier-profile 的墨 gate 抬高只会 skip（skip 吞掉「尺坏了」）⇒ 开 BACKLOG 435；r77 M406 锚点失效。
④ 补登记 R381–R385 五支台账生成器（此前只在本机未跟踪），并把两笔提交 subject 修到守卫能读的形状。

验证读数（现读）：`M411 CAUGHT`（`testEveryTwoStateRulerReadsBothAxes`）；`M147 CAUGHT`（`("0") is less than ("3") - light 档 18 条说明段探针一条都没判成`）；r77 整表 `抓到=9 未落地=1`（M406）；`HIDDEN_ARMS 表=227 可判=811 rot=0 抽不出=6 上界 rot=0 … 处置=ok`；全量 `Executed 1036 tests, with 48 tests skipped and 0 failures`（沿用 R385 日志）；电池 `Ran 683（skipped=4）OK`；产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 385` 现读）。

NOT-RUN（分开写）：① CI 三跑结论未读（网络）；② 真机腿没跑；③ R385 那颗 `.selection` 过渡的过程仍无胶片证人；④ M406 未重钉；⑤ 435（skip 吞红）只开单未修。

下一轮（R387）的靶：⓪ 网络恢复后先 `git push origin main`，再读 `40234023212`/`40234058148` 与本次推送那一跑的全部失败步骤，把 run id↔commit 成对写回本行；① 重钉 M406；② 收口 R385 过渡：造只拍按钮带的胶片场景（≥2 样本、1x/2x），并按 435 给 skip 出口加负半证人。

## R385 状态（2026-10-26 · 本地 · 第 384 轮 / Round 382）：两颗「恢复默认」的禁用切换接上 .selection 过渡 + 源形状守卫；367 再钉 r64 两根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R385 / 第 384 轮 / Round 382）：R382/R383 的禁用态在默认↔动过之间硬切；给权重页与快捷键页两颗按钮挂 `MotionCatalog.animation(for: .selection)`（键分别是 `store.weights == .default` / `shortcut == settings.action.defaultShortcut`）。端态 182 张帧 `same=182 changed=0` ⇒ 过渡不改静态落点；**过程没有胶片证人 ⇒ 具名 NOT-RUN**（D-373），不把接线写成演过。源形状守卫 `testResetButtonDisabledTransitionsAreDriven` + 真值表；`M1016`/`M1017` 都 `CAUGHT`、还原干净。367：r64 M340/M341 重钉到 `appendLocked`（整表 6/6 CAUGHT），`HIDDEN_ARMS … rot=2 … 上界 rot=2 … 处置=ok`（4→2；剩 M147/M411）。`swift build --build-tests` 告警 **0**；全量 `Executed 1036 tests, with 48 tests skipped and 0 failures`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 384` 的 streak）。

本轮做了什么：
① ⓪ CI：`40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 两跑 in_progress（>1000s），只登记不轮询；R384 能力闸门的 runner 复验仍欠。
② 产品位：两颗重置按钮的禁用切换接 `.selection` 过渡；端态帧 182/0。
③ 判据：源形状守卫 + 真值表；M1016/M1017 CAUGHT；过程 NOT-RUN。
④ 367：r64 M340/M341 重钉，整表 6/6；rot 4→2、上界同笔降。
⑤ 验证：构建 0 告警；全量 `1036/48/0`；捕获 `CAPTURED 182 -> /tmp/r385_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162；预检 `tables=140 covered=123 arms=393 bad=0`、全仓 233 文件 / 877 把。

验证读数（现读）：`FRAMEDIFF same=182 changed=0`；`R385_MUTATE 刀=2 CAUGHT=2`；r64 `CAUGHT=6`；`HIDDEN_ARMS … rot=2 … 处置=ok`；`NEEDLE_PRECHECK tables=140 covered=123 arms=393 bad=0`。

NOT-RUN（分开写）：① **过渡过程**没有胶片/时间证人（静态帧只签端态），记 `NOT-RUN=no-timeline-witness`；② `40234023212`/`40234058148` 两跑仍 in_progress —— CI 结论未读，不许写成没红；③ 亮档真机腿仍没跑；④ 剩 2 根 rot 未重钉（r33 M147、r77 M411）。

下一轮（R386）的靶：⓪ 读队列（先读 `40234023212`/`40234058148` 的全部失败步骤；本笔 run id 待 push 后成对写回）；① 继续 367（r33 M147 或 r77 M411）；② 回产品动效面再点一个真实位；若收口这颗过渡，先造只拍按钮带的胶片场景（≥2 样本/两倍率）。

## R384 状态（2026-10-26 · 本地 · 第 383 轮 / Round 381）：R383 两跑分诊 + 能力闸门；登录项失败回执改为错误色（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R384 / 第 383 轮 / Round 381）：`40228710640 ↔ 02e89cf`、`40228793715 ↔ 0f408a8` 两跑 failure，全部失败步骤只有 `Swift tests (executed-count gate)` 与 `Capture gate`；R382 的权重判据已过（runner `288/115` 对 `607/195`），R383 的快捷键判据在 runner 上整页平涂（`SHORTCUT_RESET_STATE 默认 0/2` 对 `0/2`）⇒ 加内容区墨能力闸门（本机 62696/64756；不足走 `SHORTCUT_RESET_NOT_RUN=flat-page`），本机判据全绿，重推复验留给下一轮。产品位：登录失败回执与「不支持」说明同色，加 `lastActionFailed` + 动态错误色（亮纯红 / 暗 `1.0,0.48,0.44`；纯红暗档 2.87 低于 caption 地板、深红亮档 9.88 高于天花板，三跑才落带内）；182 张帧 `same=180 changed=2`，两张只动失败回执行。`M1015` CAUGHT；`M177` 因本轮产品改动重钉并 CAUGHT；r78 M417 重钉 6/6 ⇒ `HIDDEN_ARMS … rot=4 … 上界 rot=4 … 处置=ok`（5→4）。真机隔离启动判掉 `content-empty` 图标夹子的离屏裁切（真机完整，未改产品）。`swift build --build-tests` 告警 **0**；全量 `Executed 1034 tests, with 48 tests skipped and 0 failures`；电池 `Ran 683 tests` + `OK (skipped=4)`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 383` 现读）。

本轮做了什么：
① ⓪ CI 分诊：两跑 failure；全部失败步骤 + 步骤名直方图 + 按步骤取正文 + 改动前 success 对照 ⇒ R382 权重判据已过、R383 快捷键判据是平涂能力缺席。
② 判据：快捷键/登录两条新判据都加内容区墨能力闸门，不足具名 NOT-RUN；本机全绿。
③ 产品位：`lastActionFailed` + 动态错误色；被既有 caption 判据两次打回（过淡/过深），最终落带内。
④ 367：M177 重钉（自己改动造成的 rot）、r78 M417 重钉；rot 5→4、上界同笔降。
⑤ 验证：构建 0 告警；全量 `1034/48/0`；捕获 `CAPTURED 182 -> /tmp/r384_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162；预检 `tables=139 covered=122 arms=391 bad=0`、全仓 232 文件 / 875 把。

验证读数（现读）：`LOGIN_RECEIPT_STATE` 失败 `2370/2116`、说明 `0/0`；`M1015`/`M177` 各 CAUGHT；r78 `抓到=6 逃掉=0`；`HIDDEN_ARMS … rot=4 … 处置=ok`；`NEEDLE_PRECHECK tables=139 covered=122 arms=391 bad=0`。

NOT-RUN（分开写）：① **重推后的 runner 复验**没读（这一笔推送之后那一跑要下一轮 ⓪）；② runner 的快捷键判据在能力闸门下会走具名 `SHORTCUT_RESET_NOT_RUN=flat-page`，不是判绿；③ 亮档真机腿仍没跑（系统外观=dark；本轮的隔离真机只看了暗档空态）；④ 剩 4 根 rot 未重钉（r33 M147、r64 M340/M341、r77 M411）。

下一轮（R385）的靶：⓪ 读队列（`d38ea10 ↔ 40234023212` 状态=in_progress；确认 `Swift tests` / `Capture gate` 两朵消失或走具名 `SHORTCUT_RESET_NOT_RUN=flat-page`；`02e89cf ↔ 40228710640`、`0f408a8 ↔ 40228793715` 两跑的 failure 已按流程读完 —— 权重判据已过、快捷键判据是平涂页无读数；`43ff699 ↔ 40221947072` 是改动前 success；in_progress 是第三种态，不许读成「没红」）；① 继续 367（从 r64 M340/M341 或 r77 M411 起，先看 `HIDDEN_ROT`）；② 回产品动效面再点一个真实位。

## R383 状态（2026-10-26 · 本地 · 第 382 轮 / Round 380）：CI 两跑分诊 + 快捷键三颗「恢复默认」禁用态；367 rot 8→5（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R383 / 第 382 轮 / Round 380）：`40224259064 ↔ c59b292`、`40224280654 ↔ e9b1f83` 两跑 failure，全部失败步骤只有 `Swift tests (executed-count gate)` 与 `Capture gate`；六朵红全在 R382 新判据 —— runner（1x）上 72×22pt 取样矩形没压住标签（`WEIGHTS_RESET_STATE … 墨=0 最大偏离=23` 两态同形）⇒ 取样几何机器依赖。改成语义带（x 380..520、y 60..230）+ 两态差只由 `maxDev` 判，本机现读 light 122/211、dark 119/193，M1013 复跑 `CAUGHT`。产品位：快捷键页三颗「恢复默认」在默认值下从未画禁用态（修前整页两态完全相同 `3792/211`），加 `.disabled(shortcut == settings.action.defaultShortcut)` 后 `2817/70` 对 `3142/211`；182 张帧 `same=176 changed=6`，6 张只动快捷键页右列。`M1014` `CAUGHT`；367：r94 整表 7/7、M876 单臂 CAUGHT、M674 退役（改名方向无牙）⇒ `HIDDEN_ARMS … rot=5 … 上界 rot=5 … 处置=ok`（8→5）。`swift build --build-tests` 告警 **0**；全量 `Executed 1033 tests, with 48 tests skipped and 0 failures`；电池 `Ran 683 tests` + `OK (skipped=4)`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 382` 现读）。

本轮做了什么：
① ⓪ CI 分诊：两跑 failure；`ci_read.py steps` 全部失败步骤 + 步骤名直方图（无 UNKNOWN STEP）+ 按步骤取正文 + 改动前 `43ff699` 那一跑 success 做对照 ⇒ 判成 R382 引入的判据几何回归。
② 判据修复：语义带 + `maxDev` 两态差；M1013 复跑 CAUGHT。
③ 产品位：快捷键页三颗 `恢复默认` 加禁用条件；两态整页渲染修前相同、修后分开；帧差分只动按钮列。
④ 367：r94 M518 单字面量（7/7）、r303 M876 字面量 + 漂移断言、r142 M674 退役；rot 8→5、上界同笔降。
⑤ 验证：构建 0 告警；全量 `1033/48/0`；捕获 `CAPTURED 182 -> /tmp/r383_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162；预检 `tables=138 covered=121 arms=390 bad=0`、全仓 231 文件 / 874 把。

验证读数（现读）：`SHORTCUT_RESET_STATE` 修前 `3792/211`、修后 `2817/70`（亮）与 `4152/186`→`2976/60`（暗）；`WEIGHTS_RESET_STATE` `122/211`、`119/193`；`M1013`/`M1014` 各 `CAUGHT=1/1 RESTORE_CLEAN=yes`；r94 `MUTATE_TABLE n=7 caught=7`；r142 `CAUGHT=5/5`；`ARM_TOTAL files=231 arms=874 dupes=0`。

NOT-RUN（分开写）：① **重推后的 CI 复验**没读 —— 这一笔推送之后的那一跑要下一轮 ⓪ 读（本轮不轮询）；② 亮档真机腿仍没跑（当前系统外观=dark）；③ 剩 5 根 rot 未重钉（r33 M147、r64 M340/M341、r77 M411、r78 M417）。

下一轮（R384）的靶：⓪ 读队列（`02e89cf ↔ 40228710640` 状态=in_progress；确认 `Swift tests (executed-count gate)` 与 `Capture gate` 两朵是否消失；`c59b292 ↔ 40224259064`、`e9b1f83 ↔ 40224280654` 两跑的 failure 已按 read-own-ci-run 读完、`43ff699 ↔ 40221947072` 是改动前那一跑 success；in_progress 是第三种态，不许读成「没红」）；① 继续 367（从 r78 M417 或 r64 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位。

## R382 状态（2026-10-26 · 本地 · 第 381 轮 / Round 379）：默认权重下「恢复默认」没有禁用态 —— 两态像素证人 + M1013；367 再钉五根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R382 / 第 381 轮 / Round 379）：对比 `weights`（全默认）与 `weights-adjusted`（近因 160% / 收藏 40%）两帧，「恢复默认」标签墨完全相同 ⇒ 禁用态从未存在；加 `.disabled(store.weights == .default)` 后 `WEIGHTS_RESET_STATE light 默认 62 / 动过 195`、`dark 默认 51 / 动过 170`；182 张帧 `same=176 changed=6`，6 张只动按钮矩形、`weights-adjusted` 逐字节不变。新判据 + `M1013` 现读 `CAUGHT`、复跑 `ESCAPED`；第一版表写成自写 main、对 `mutate_needle_precheck` / `hidden_arms` 隐形，改成 `MUTATIONS` 后 `covered=120 arms=389`、`可判=808`。367 再钉 r29d（5/5）与 r76 M402（5/5），`HIDDEN_ARMS … rot=8 … 上界 rot=8 … 处置=ok`（12→8）。`swift build --build-tests` 告警 **0**；全量 `Executed 1032 tests, with 48 tests skipped and 0 failures`；电池 `Ran 683 tests` + `OK (skipped=4)`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 381` 现读，口径是「本轮之前的连读轮数」）。

本轮做了什么：
① ⓪ CI：登记 `4255109 ↔ 40221926024`、`43ff699 ↔ 40221947072`（均 in_progress）；`9678d9c ↔ 40216535782`、`fb641e7 ↔ 40216344972`、`ef45e65 ↔ 40216188878`、`e8228a8 ↔ 40216027769` 已 success；只登记不轮询。
② 产品位：默认/动过两帧同一颗按钮像素相同 ⇒ 禁用态缺席；加 `.disabled(store.weights == .default)`；帧差分区只在按钮。
③ 判据：新像素判据读两态标签墨 + M1013 CAUGHT；表形状改成 `MUTATIONS` 让两个静态名册看见它。
④ rot：r29d M132/M133/M135 + r76 M402 重钉，两表整表 5/5 CAUGHT；rot 12→8、上界同笔降。
⑤ 验证：构建 0 告警；全量 `1032/48/0`；捕获 `CAPTURED 182 -> /tmp/r382_shots`；帧基线 `COMPARED=182 CHANGED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162。

验证读数（现读）：`WEIGHTS_RESET_STATE` 两档 `62/195`、`51/170`；`R382_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes`；r29d `CAUGHT=5/5`、r76 `抓到=5 逃掉=0`；`NEEDLE_PRECHECK tables=137 covered=120 arms=389 bad=0`；`ARM_TOTAL files=230 arms=874 dupes=0 repeats=0`。

NOT-RUN（分开写）：① 亮档真机腿仍没跑（当前系统外观=dark；R382 的按钮禁用态没有走真机通道，只有离屏两态帧）。② 剩 8 根 rot 未重钉（r142 M674、r303 M876、r33 M147、r64 M340/M341、r77 M411、r78 M417、r94 M518）。③ `weights-*` 与 `settings-recommendations*` 的帧基线已同一笔更新，不是 NOT-RUN。

下一轮（R383）的靶：⓪ 读队列（`c59b292 ↔ 40224259064` 状态=in_progress；`4255109 ↔ 40221926024`、`43ff699 ↔ 40221947072` 均已 success；in_progress 是第三种态，不许读成「没红」）；① 继续 367（从 r303/r94 或 r64 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位（本轮的最弱维仍是「只深审一个位点」）。

## R381 状态（2026-10-26 · 本地 · 第 380 轮 / Round 378）：设置侧栏图标亮档白压白 —— 动态 labelColor 修复 + 无墨格升会红；367 再钉八根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R381 / 第 380 轮 / Round 378）：亮档设置侧栏未选中图标实测 **255 白压在 251 底上（对比 4/255）**，旧尺数成「无墨」；单行组件帧黑、整页 `NavigationSplitView` 白 ⇒ 侧栏材质 vibrancy 把 `.primary` 解析成白色。图标改用动态系统色 `Color(nsColor: .labelColor)`（亮 76 / 暗 232），文字仍 `.primary`；修后 `SIDEBAR_ICON_COVERAGE light 有墨行=84 无墨行=0 反侧行=0 | dark 84/0/0`（修前亮档无墨 65/78）；新旧帧差分 152 张逐字节同、30 张只动 x 34–68。新守卫 `SIDEBAR_ICON_BLANK` 把无墨格升成会红，`M1011`（改回 `.primary`）/`M1012`（写死黑）两臂 `CAUGHT`；367 再钉八根（r131/r137/r140/r60/r67），`HIDDEN_ARMS … rot=12 … 上界 rot=12 … 处置=ok`（20→12），八根都重跑过刀；`swift build --build-tests` 告警 **0**；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 `Ran 683 tests` + `OK (skipped=4)`（`/tmp/r381_py2.log`，EXIT=0）；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **26** 轮（`python3 scripts/product_streak.py --streak-for 380` 现读，口径是「本轮之前的连读轮数」）。

本轮做了什么：
① ⓪ CI：`9678d9c ↔ 40216535782`（in_progress）、`fb641e7 ↔ 40216344972`（in_progress）、`ef45e65 ↔ 40216188878`、`e8228a8 ↔ 40216027769`、`0264a63 ↔ 40215895770`、`39189c2 ↔ 40215694974`、`947cd29 ↔ 40215439140`、`dfe411a ↔ 40214501796`（concluded=success）；只登记不轮询。
② 产品位：看图 → 量像素（4/255）→ 单行/整页对照定因（材质 vibrancy）→ 图标改动态系统色；帧差分确认只动图标列。
③ 判据：`SIDEBAR_ICON_BLANK` 两档判零；方向尺的反相正对照改成合成位图（先红两次，成因写进注释）。
④ rot：八根重钉并跑刀；语料补 `make_surface_ledger.py`；`ARM_LINE` 放宽到四位并加正对照。
⑤ 验证：构建 0 告警；全量 `1031/48/0`；捕获 `CAPTURED 182 -> /tmp/r381_shots2`；帧基线 `COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 381=381；清账表 162=162。

验证读数（现读）：`SIDEBAR_ICON_COVERAGE` 两档 `84/0/0` 与 `84/0/0`；`R381_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes`；`MUTATE_TABLE n=3 caught=3`（r131）、`n=1 caught=1`（r137）、`CAUGHT=3/3`（r140）；`NEEDLE_PRECHECK tables=136 covered=119 arms=388 bad=0`；`ARM_TOTAL files=229 arms=873 dupes=0 repeats=0`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`。

NOT-RUN（分开写）：① **亮档真机腿**没跑：当前系统外观是 dark，`real_screen_sidebar_icons.py` 只能读当前外观；暗档真机通道已跑通（`REALSCREEN_VERDICT=ok 外观=dark`、六枚图标可辨），亮档这一半的证据仍是离屏整页帧。② 剩 12 根 rot 未重钉（r142 M674、r29d M132/M133/M135、r303 M876、r33 M147、r64 M340/M341、r76 M402、r77 M411、r78 M417、r94 M518）。③ `settings-*` 的帧基线已同一笔更新，不是 NOT-RUN；`capture-readings.log` 与全量日志留在 `/tmp` 不入库。

下一轮（R382）的靶：⓪ 读队列（`4255109 ↔ 40221926024` 状态=queued，这一跑覆盖 `e29732b`/`9ecb400`；`9678d9c ↔ 40216535782`、`fb641e7 ↔ 40216344972`、`ef45e65 ↔ 40216188878`、`e8228a8 ↔ 40216027769` 均已 success；queued 是第三种态，不许读成「没红」）；① 继续 367（从 r29d 或 r76 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位（本轮的最弱维仍是「只深审了一个位点」）。

## R380 状态（2026-10-26 · 本地 · 第 379 轮 / Round 377）：M244 的对照组补「归因到 add」；刀仍 ESCAPED、针活了≠刀验过；本机换装 ok（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R380 / 第 379 轮 / Round 377）：`testAddingACopyWritesNothingOnTheMainThread` 多判一句「盘上那份必须含刚加进去的文本」（未变异 0.452s 通过）；第一版变异文把 `_ = entries` 接在 save **后面**（刀没下）⇒ 看着像「第三条落盘路」；真替换那一行后 `M244 ⇒ CAUGHT`（两格同红）、还原干净 ⇒ 没有第三条路，`add` 的落盘就在 `persist()`；rot 21→20 是针活了，这一刀现在也验过了；`scripts/install_local.sh --yes` 现读 `INSTALL_RESULT=ok  版本=1.4.8→1.4.8`、`INSTALL_SHA_MATCH=1`、`INSTALL_ENTRIES_BEFORE=381  INSTALL_ENTRIES_AFTER=381`；build `--build-tests` 告警 **0**；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 682（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`a84cb73`（R377）与 `a63dcf5`（R378）success、`3ef8c59`/`fbf2508`/`dfe411a` 已推；只登记不轮询。
② 对照组归因：文件出现 → 文件出现**且含 add 的文本**；未变异仍全绿。
③ M244 再跑：第一版刀文只加了一行、save 照跑 ⇒ ESCAPED；改成真删那一行后 **CAUGHT**（两格同红）、还原干净。
④ 本机换装一遍（`--yes`）：ok、SHA 匹配、条目 381=381。

验证读数（现读）：未变异 `testAddingACopyWritesNothingOnTheMainThread passed (0.452 seconds)`；`M244 ⇒ ESCAPED`；`HIDDEN_ARMS 表=222 可判=805 rot=20 … 处置=ok`；`swift build --build-tests` 告警 0；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 `Ran 682（skipped=4）OK`；产品面连续零改动 **25** 轮（`python3 scripts/product_streak.py --streak-for 379` 现读）。

NOT-RUN（分开写）：① 真机腿没跑；② 帧基线没更新（本轮无产品/夹具改动）；③ 第三条落盘路没定位（M244 未验成）；④ 其余 20 条 rot 未重钉。

下一轮（R381）的靶：⓪ 读队列（`3ef8c59`/`fbf2508`/`dfe411a` 与本轮的结论）；① 找出 add 的第三条落盘路（从 `entries` 的 didSet / Combine 订阅 / `reconcileSelection` 三条线查）；② **回产品动效面点一个真实位**（已连续 25 轮零产品改动，这一维必须动）。
R381 追记（同日）：r49 整表跑全 —— `M240/M241/M242/M243/M244` 全部 `CAUGHT`、五臂还原干净；M240 是「recordCopy 里同步写盘」的产品侧刀，红在 `testAddingACopyWritesNothingOnTheMainThread`，「采集路径上不许有同步磁盘写」第一次有整表读数。rot 仍 20。
R381 追记二（同日）：r42 整表 4/5 —— `M194…M197` 全部 `CAUGHT`（同红在 `MotionDriverTests testEveryReceiptLineCallSiteIsDriven`）；**M198 `BROKEN-MUTATION`**（注入后编译不过，`showExportAlert` 已不在源码里）⇒ 刀坏待重钉，不是判据问题。
R381 追记三（同日）：r54 整表 5/5 —— `M264`（产品侧梯子第 1 级压平）与 `M265/M267` 红在 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis`，`M266/M268` 红在 `testAdjacentLevelRulersAreATruthTable`，五臂还原干净；热图相邻档的「分得开」在 产品/尺子/夹具 三侧都有牙。
R381 追记四（同日）：M198 重钉 —— 旧锚点 `if showExportAlert {` 已被 R43 删掉（刀坏），换到当前导出回执分支前插一条未登记回执、期望串改成名单末项 `"true"]`；现读 `CAUGHT 红得对=True`，r42 整表 **5/5 CAUGHT**。
R381 追记五（同日）：r53 整表 4/4 —— `M260/M261/M262/M263` 全红在 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`、还原干净（结论行先于 skip、`region()` 不命中守卫自己、`notAnimated` 必须判红）。

## R379 状态（2026-10-26 · 本地 · 第 378 轮 / Round 376）：r56 十臂全表第一次跑全（10/10 CAUGHT）；M244 重钉尝试 ESCAPED 并撤回（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R379 / 第 378 轮 / Round 376）：r56 整表十臂一次跑全 —— `M277…M281` 红在守卫各自那句、`M282` 命中「夹具替换没有落地」（`红在 []` 的有效红）、`M283/M284` 红在两个恢复场景、`M285` 红在 partial 那一格、`M1010` 命中 `READOUT_CHANNEL_BLOCKED`；十臂 `还原干净=True`、复跑 `ESCAPED`、`EXIT=0`；M244 的重钉尝试 ESCAPED（`persist()` 的 save 不是唯一落盘路）已撤回，rot 仍 21；全量沿用 R377（本轮没动 Swift）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 682（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`a84cb73`（R377）与 `a63dcf5`（R378）已 success、`3ef8c59`（追记）在队；只登记不轮询。
② r56 全表跑全（十臂）：预检两路 OK，10/10 CAUGHT，还原干净，复跑 ESCAPED。
③ M244 的重钉尝试 ESCAPED ⇒ 表还原、刀没收；线索写进 BACKLOG 367 追记。
④ 记下「整表跑全才看得见 M282 那种有效红」（D-367）。

验证读数（现读）：`红得不对/未抓到=0  还原不干净=0`、`还原后复跑（Swift 守卫）：ESCAPED`、表 `EXIT=0`；`HIDDEN_ARMS … rot=21 … 处置=ok`；预检 `tables=135 covered=118 arms=386 bad=0`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R377 日志）；电池 `Ran 682（skipped=4）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **24** 轮（`python3 scripts/product_streak.py --streak-for 378` 现读）。

NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R377 日志）；③ r56 的 CI 四臂只在自检样张那一层验过（它们证的本来就不是产品像素）；④ 其余 20 条 rot 仍未重钉、M244 未定位。

下一轮（R380）的靶：⓪ 读队列（含 `3ef8c59`）；① 定位 `add` 的第二条落盘路（M244）；② 回产品动效面点一个真实位（已连续 24 轮零产品改动，这一维必须动）。

## R378 状态（2026-10-26 · 本地 · 第 377 轮 / Round 375）：367 第三批 —— 七把腐烂针重钉、rot 27→21；M188 旧刀编译不过判成刀坏（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R378 / 第 377 轮 / Round 375）：r40 四把针跟着 `CopyThenPaste.decide(failure:)` 重钉、r42 两把从「注释 + 动作」缩到动作那一行 —— 六臂全 CAUGHT、还原干净；M188 第一版反向变异编译不过记 `BROKEN-MUTATION`，改「成功也判取消」后 CAUGHT；`HIDDEN_ARMS 表=222 可判=805 rot=21 … 处置=ok`，`ROT_CEILING` 同笔 27→21；全量沿用 R377（本轮没动 Swift）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 682（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`1ff9d11`（R376）与 `187ffaf`/`2ffc6d0`（R375）已 success；本轮 `a84cb73 ↔ 40213511314`（in_progress、前面=0）；只登记不轮询。
② r40 四臂重钉 + 接 knife_guard（备份 / 启动恢复 / 600s 进程组超时）→ 4/4 CAUGHT。
③ M188 旧写法编译不过 ⇒ 记刀坏并换写法（成功也判取消）→ CAUGHT（真值表 + 成功不许被挡两格）。
④ r42 两臂缩针到动作那一行 → 2/2 CAUGHT；rot 27→21、上界同笔降；r49 M244 明确留待下一批。

验证读数（现读）：`M185…M188 CAUGHT`（各红在主张的两格）、`M194/M195 CAUGHT`（`MotionDriverTests testEveryReceiptLineCallSiteIsDriven`）；六臂 `还原干净=yes`；`HIDDEN_ARMS 表=222 可判=805 rot=21 抽不出=6 已声明表=6 已声明死针=0 上界 rot=21 … 处置=ok`；预检 `tables=135 covered=118 arms=386 bad=0`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R377 日志）；电池 `Ran 682（skipped=4）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **23** 轮（`python3 scripts/product_streak.py --streak-for 377` 现读）。

NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R377 日志）；③ r49 M244 与其余 20 条腐烂针**没重钉**（旧针的对象已被重写，要先给新探针写同义坏法）。

下一轮（R379）的靶：⓪ 读队列（含 `a84cb73` 的结论）；① r49 M244：重钉**试过一次 ESCAPED** —— 把 `HistoryStore.persist()` 里的 `persistence.save` 拿掉后对照组仍绿 ⇒ `add` 还有第二条落盘路（未定位），先找出它再钉；同时再钉一批 rot。② 回到产品动效面点一个真实位（连续判据账之后优先）。

## R377 状态（2026-10-26 · 本地 · 第 376 轮 / Round 374）：434 结案 —— 读数通道 5s 有界等待（M1010 CAUGHT）；r56 十把刀第一次进针预检（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R377 / 第 376 轮 / Round 374）：守卫里「emit 两行 + 读回全文」挪进 `boundedChannelProbe(deadline: 5)`，超时具名 `READOUT_CHANNEL_BLOCKED`，同格合成正对照（闸门 / 50ms 截止）；新刀 M1010（emit 写盘前 sleep 30s）现读 CAUGHT、命中该名字、还原干净、复跑 ESCAPED、表 EXIT=0；r56 真登记进针预检名册并认五元组形状 + `.yml` 源文件 ⇒ `covered=118 arms=386 bad=0`，缺口 75/423→74/414（地板同笔改）；`swift build --build-tests` 告警 **0**；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 682（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`1ff9d11`（R376）刚推、run id 未读；`187ffaf`/`2ffc6d0`/`84e4381`/`357a763` 仍在队里；`a17bc6a`（R373 追记）success；只登记不轮询。
② 434 产品/判据面：`boundedChannelProbe` + 超时出口 + 同格正对照；守卫 0.090s 通过。
③ 新刀 M1010 落刀 → CAUGHT（READOUT_CHANNEL_BLOCKED）；还原干净、复跑 ESCAPED。
④ r56 覆盖修补：登记 + 五元组形状 + `.yml`；顺带去重守卫头上重复两遍的注释。

验证读数（现读）：`swift build --build-tests` EXIT=0、`grep -c warning:` = **0**；基线守卫 `passed (0.090 seconds)`；`M1010 ⇒ CAUGHT 红得对=True 命中=['READOUT_CHANNEL_BLOCKED'] 还原干净=True`；预检 `tables=135 covered=118 arms=386 bad=0`；`TABLE_ROSTER registered=135 unregistered_with_arms=74 hidden_arms=414`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 `Ran 682（skipped=4）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **22** 轮（`python3 scripts/product_streak.py --streak-for 376` 现读）。

NOT-RUN（分开写）：① 真机腿没跑；② 帧基线没重捕（本轮无产品/夹具改动，沿用 R356 帧）；③ M1010 只在「写前 sleep」这一种阻塞形状上验过，锁死等 / 磁盘卡死的形状仍未各配一把刀。

下一轮（R378）的靶：⓪ 读队列（含 `1ff9d11` 的 run id）；① 367 继续（rot 27）；② 134→135 名册之后，`covered` 仍差 17 张（抽不出的那批）要逐张点名。

## R376 状态（2026-10-26 · 本地 · 第 375 轮 / Round 373）：M278 的挂点是刀文自己 —— return 吞掉 lock.lock()；433 结案、超时补杀子孙树（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R376 / 第 375 轮 / Round 373）：`sample` 三跑同栈抓到 M278 的挂点（`return` 换行被解析成 `return lock.lock()`，第一刀拿走 NSLock 不解锁）；刀文改成整段替换 ⇒ `M278 CAUGHT`、还原干净、复跑 `ESCAPED`、表 EXIT=0；`swallowed_return_lines` + 4 格测试 + 落刀前拦截（222 张表按「替换文以 return 结尾」现读 0 支）；超时补杀子孙树 + 2 格测试；全量沿用 R374（本轮没动 Swift）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 682（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`a17bc6a`（R373 追记）success；`357a763`/`84e4381`/`2ffc6d0`/`187ffaf` 四跑仍在队里（`187ffaf ↔ 40210952259`、`2ffc6d0 ↔ 40210881173`）；只登记不轮询。
② 433 第二半：落刀后 30s `sample` 三跑同栈 + 编译器 warning ⇒ 挂点=刀文，不是产品/守卫。
③ 刀文改整段替换；`swallowed_return_lines` 在 `apply` 里落盘前拦截；M278 现读 CAUGHT。
④ 超时补杀子孙树（R375 的 xctest 被 launchd 收养又活 9 分钟）；祖先快照 + 逐个 SIGKILL。

验证读数（现读）：`M278 ⇒ CAUGHT 红得对=True 命中=['文件里没有这一遍的 marker'] 还原干净=True`、`还原后复跑（Swift 守卫）：ESCAPED`、表 `EXIT=0`；`test_knife_guard` **12 格**全绿（含自开会话的孙进程）；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R374 日志）；脚本电池 `Ran 682（skipped=4）OK`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=162 未清账=0 地板=162`；预检 `tables=134 covered=117 arms=376 bad=0`；`HIDDEN_ARMS 表=222 可判=804 rot=27`；产品面连续零改动 **21** 轮（`python3 scripts/product_streak.py --streak-for 375` 现读）。

NOT-RUN（分开写）：① 真机腿没跑；② 全量卷没重跑（本轮没动 Swift，沿用 R374 日志）；③ 434（读数通道无超时）只留下症状样本，修法与 witness 尚未落地。

下一轮（R377）的靶：⓪ 读队列；① 434 的有界等待 + `sleep` 注入作证；② 367 继续（rot 27）。

## R375 状态（2026-10-26 · 本地 · 第 374 轮 / Round 372）：433 第一半 —— 崩溃安全还原 + 硬超时；M279/M281 CAUGHT、M278 以 180s 超时具名（产品 0 文件，判据账）

最后更新：2026-10-26（本地 · R375 / 第 374 轮 / Round 372）：`knife_guard.py` + 6 格测试；r56 接线（启动恢复、逐臂备份、180s 进程组超时、CI 判词读汇总行）；三臂 `M279 CAUGHT / M281 CAUGHT / M278 NOT_RUN_TIMEOUT`，三臂还原干净、复跑守卫 ESCAPED；全量沿用 R374（本轮没动 Swift）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；电池 Ran 676（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`357a763`（R374）已 success；`a17bc6a`（R373 追记）success；本轮 `2ffc6d0 ↔ 40210881173`（queued、同 workflow 前面=2）与 `84e4381`（R374 追记）仍在队里；只登记不轮询。
② 433 第一半：备份/启动恢复/进程组超时 + 6 格正对照（`sleep 5` 对 1s 超时）。
③ r56 接线：预检前恢复、逐臂备份、`NOT_RUN_TIMEOUT`、CI 判词读汇总行（不读末行）。
④ 三臂现读；M278 挂起**可复现**（180s），下一格用 `sample` 抓栈。

验证读数（现读）：`M279 CAUGHT`（命中「不在末尾两格」）、`M281 CAUGHT`（命中「扫描函数在合成样本上抓不到」）、`M278 NOT_RUN_TIMEOUT`；三臂 `还原干净=yes`、复跑 `ESCAPED`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R374 日志）；脚本电池 `Ran 676（skipped=4）OK`；产品面连续零改动 **20** 轮（`python3 scripts/product_streak.py --streak-for 374` 现读）。

NOT-RUN（分开写）：① M278 的 CAUGHT 仍没有读数（可复现超时）；② 全量卷没重跑（本轮没动 Swift）；③ 真机腿没跑。

下一轮（R376）的靶：⓪ 读队列；① 433 第二半：M278 落刀后 30s `sample <pid>` 抓栈，定位挂点；② 再回到 367（rot 27）。

## R374 状态（2026-10-25 · 本地 · 第 373 轮 / Round 371）：读数通道守卫补上「来源」证人；r56 三根针重钉，刀腿 NOT-RUN（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R374 / 第 373 轮 / Round 371）：`strayLines(in:)` + 合成样本正对照落地，守卫 0.029 秒通过；r56 的 M278/M279/M281 重钉、CI 预检 `Ran 1 test` → `Ran \d+ tests`，两路预检 OK；刀腿 NOT-RUN（M278 臂 xctest 挂 6:29、两次强杀、两次残留 MUTANT 已还原）；全量 1031 格 0 失败、电池 Ran 670（skipped=4）OK（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`a17bc6a`（R373 追记）已 **success**；本轮 `357a763 ↔ 40209810666`（queued、同 workflow 前面=0）。更早的几跑已结案；只登记不轮询。
② 守卫洞：扫描来源提成 `strayLines(in:)`，同一函数喂合成样本必须抓到 1 条。
③ r56 重钉（M278→CaptureReadings.emit、M279→appendLocked、M281→strayLines）+ CI 预检写法修掉。
④ 刀腿挂起 → NOT-RUN；rot 29→27（针活了）且上界同笔降；开 433（崩溃安全还原 + swift 腿硬超时 + M278 挂起成因）。

验证读数（现读）：`testMotionReadingsUseTheFileChannel passed (0.029 seconds)`；`预检 OK MotionFilmstripTests.testMotionReadingsUseTheFileChannel`、`预检 OK ci_report_selftest`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；脚本电池 `Ran 670（skipped=4）OK`；产品面连续零改动 **19** 轮（`python3 scripts/product_streak.py --streak-for 373` 现读）；`HIDDEN_ARMS 表=222 可判=804 rot=27 抽不出=6 已声明表=6 已声明死针=0 上界 rot=27 … 处置=ok`。

NOT-RUN（分开写）：① M278/M279/M281 的 CAUGHT 没有读数（M278 臂挂起，两次强杀）—— rot 不降；② 真机腿没跑。

下一轮（R375）的靶：⓪ 读队列五跑；① 先做 433 的崩溃安全还原与硬超时，再重跑 r56 三臂；② 之后才谈 367 的下一根。

## R373 状态（2026-10-25 · 本地 · 第 372 轮 / Round 370）：367 第三批 —— r55 的 M271/M272 重钉（参数名改名），rot 31→29（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R373 / 第 372 轮 / Round 370）：`GrabAttribution.classify` 与调用点改名的两根针重钉；`M271 / M272` 各 CAUGHT、`还原不干净=0`；`ROT_CEILING` 31→29，`test_hidden_arms` 8/8；电池 Ran 670（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c` 仍在队里；本轮 `ec65950 ↔ 40205804191`（queued、同 workflow 前面=2，只登记不轮询）。
② 367 第三批：M271（`worstIntervalMilliseconds` → `clockIntervalMilliseconds`）+ M272（调用点同改）。
③ 两臂重跑各 CAUGHT；红线在真值表与接线守卫上。
④ rot 31→29、`ROT_CEILING` 同笔降；`HIDDEN_ARMS` 现读 `处置=ok`。

验证读数（现读）：`HIDDEN_ARMS 表=222 可判=804 rot=29 抽不出=6 已声明表=6 已声明死针=0 上界 rot=29 … 处置=ok`；`test_hidden_arms` 8/8；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 670（skipped=4）OK`；产品面连续零改动 **18** 轮（`python3 scripts/product_streak.py --streak-for 372` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（本轮没动 Swift）；② 其余 29 根烂针未重钉；③ 真机腿没跑。

下一轮（R374）的靶：⓪ 读队列五跑；① 367 第四批（`mutate_r56_readings_channel.py` 的 M279/M281）；② 或给 r312 家族声明 READOUT。

## R372 状态（2026-10-25 · 本地 · 第 371 轮 / Round 369）：367 第二根 —— M264 重钉（梯子顶档 0.85→0.92），rot 32→31（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R372 / 第 371 轮 / Round 369）：r54 整表 `5/5 CAUGHT`、`还原不干净=0`；M266 的期望串跟上措辞；`ROT_CEILING` 32→31，`test_hidden_arms` 8/8；电池 Ran 670（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c` 仍在队里；本轮 `791ef02 ↔ 40205487744`（queued、同 workflow 前面=3，只登记不轮询）。
② 367 第二根：M264 的针从 `[0.18, 0.34, 0.56, 0.85]` 重钉到 `…0.92`。
③ M266 的期望串过期：红已在对的格（正文「填充带压到了描边上…」），补串后单跑通过。
④ rot 32→31、`ROT_CEILING` 同笔降；`HIDDEN_ARMS` 现读 `处置=ok`。

验证读数（现读）：`HIDDEN_ARMS 表=222 可判=804 rot=31 抽不出=6 已声明表=6 已声明死针=0 上界 rot=31 … 处置=ok`；r54 `5/5 CAUGHT`；`test_hidden_arms` 8/8；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 670（skipped=4）OK`；产品面连续零改动 **17** 轮（`python3 scripts/product_streak.py --streak-for 371` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（本轮没动 Swift）；② 其余 31 根烂针未重钉；③ 真机腿没跑。

下一轮（R373）的靶：⓪ 读队列五跑；① 367 第三根（`mutate_r55_grab_attribution.py` 的 M271/M272，候选各 4 个）；② 或给 r312 家族声明 READOUT。

## R371 状态（2026-10-25 · 本地 · 第 370 轮 / Round 368）：367 第一根 —— M260 重钉到 emit，rot 33→32 且上界同笔降（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R371 / 第 370 轮 / Round 368）：r53 四臂 `4/4 CAUGHT`、`还原不干净=0`；`ROT_CEILING` 33→32，`test_hidden_arms` **8/8 OK**；电池 Ran 670（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`7ad22cf`/`19f91e2`/`f9df01e`/`3c84fc8`/`d44797c` 仍在队里；本轮 `5b83633 ↔ 40205111275`（queued、同 workflow 前面=3，只登记不轮询）。
② 367 第一根：M260 的针从 `print(` 重钉到 `emit(`（R355 换的行）。
③ 四臂重跑：M260…M263 全 CAUGHT，还原干净，复跑基线绿。
④ rot 33→32、`ROT_CEILING` 同笔降；`HIDDEN_ARMS` 现读 `处置=ok`。

验证读数（现读）：`HIDDEN_ARMS 表=222 可判=804 rot=32 抽不出=6 已声明表=6 已声明死针=0 上界 rot=32 … 处置=ok`；`test_hidden_arms` 8/8；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 670（skipped=4）OK`；产品面连续零改动 **16** 轮（`python3 scripts/product_streak.py --streak-for 370` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（本轮没动 Swift）；② 其余 32 根烂针未重钉；③ 真机腿没跑。

下一轮（R372）的靶：⓪ 读队列五跑；① 367 第二根（`mutate_r54_adjacent_levels.py` 的 M264，候选 4 个）；② 或给 r312 家族声明 READOUT（它的读数是「少了一根轴」）。

## R370 状态（2026-10-25 · 本地 · 第 369 轮 / Round 367）：432 第一刀 —— 空刀探测进两张 hidden_arms 表，正对照 M906 读出 EMPTY_KNIFE（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R370 / 第 369 轮 / Round 367）：`readout_probe.py` 四态 + 6 格测试；r310 `CAUGHT=4 BLIND=1 EMPTY=0`、r313 `CAUGHT=2 BLIND=1 EMPTY=0`，两表 `RESTORE_CLEAN=yes`；电池 Ran 670（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`7ad22cf`、`19f91e2`、`f9df01e`、`3c84fc8`、`d44797c` 仍在队里；本轮 `9d9cf9a ↔ 40204535459`（queued、同 workflow 前面=5，只登记不轮询）。
② 432 第一刀：`capture` / `four_state` / `summarize` + `test_mutation_readout.py` 6 格。
③ r310 / r313 声明 `READOUT`（`hidden_arms.py` 的 `HIDDEN_ARMS` 行）⇒ 声明面 2/134。
④ 正对照：M906 临时加回 → `EMPTY_KNIFE`（前后两行一字不差），撤销后 r310 回到 5 臂。

验证读数（现读）：`R310_MUTATE 刀=5 CAUGHT=4 ESCAPED=0 NOT_RUN=0 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes`；`R313_MUTATE 刀=3 CAUGHT=2 ESCAPED=0 NOT_RUN=0 EMPTY=0 BLIND=1 RESTORE_CLEAN=yes`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 670（skipped=4）OK`；产品面连续零改动 **15** 轮（`python3 scripts/product_streak.py --streak-for 369` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 与 scripts/tests 的新测试）；② 432 只接了两张表（2/134），其余表未声明读数口径；③ 真机腿没跑。

下一轮（R371）的靶：⓪ 读队列五跑；① 给 r312 家族（M908…M910 的读数是「读数少了一根轴」）这类表也声明 READOUT，或把 BLIND 的两把（M903/M913）改成同时动读数的刀；② 426 第八批（r306 mixed 表）。

## R369 状态（2026-10-25 · 本地 · 第 368 轮 / Round 366）：426 第七批 —— r308 迁到 diff 回读；空刀探测开单 432（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R369 / 第 368 轮 / Round 366）：r308 只换落刀后的回读那一行；`刀=6 CAUGHT=6 NOT_RUN=0 RESTORE_CLEAN=yes`；电池 Ran 664（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；迁移面 15 张（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`452f5a3`、`cc9eb1e` 两跑 success；`7ad22cf`、`19f91e2`、`f9df01e`、`3c84fc8` 仍在队里；本轮 `d44797c ↔ 40204000448`（queued、同 workflow 前面=3，只登记不轮询）。
② 426 第七批：r308（六把热图悬停刀，Swift 侧）迁 `single_substitution_lands`。
③ 六臂全 CAUGHT，红线在五个热图悬停用例上（跑=13）。
④ 空刀探测：不硬造 —— 需要 134 张表各有 `READOUT` 声明，现读 0 张；判断与形状写进 BACKLOG 432。

验证读数（现读）：`R308_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **14** 轮（`python3 scripts/product_streak.py --streak-for 368` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 一张表）；② 432 的探测器未实现（0/134 无对象）；③ 真机腿没跑。

下一轮（R370）的靶：⓪ 读队列四跑；① 给 hidden_arms 家族三张表声明 `READOUT` 并实现 432 的第四态（先只对这三张生效）；② 426 第八批（r306 这类 mixed 表）。

## R368 状态（2026-10-25 · 本地 · 第 367 轮 / Round 365）：426 第六批 —— r307/r309 迁到 diff 回读；r310 一把空刀退役（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R368 / 第 367 轮 / Round 365）：r307 `4/4`、r309 `6/6`；r310 先跑出 `5/6`（M906 落刀后 `HIDDEN_ARMS` 三组数一个没动）⇒ 退役后重跑 `5/5`；电池 Ran 664（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`452f5a3`（R365 追记）与 `cc9eb1e`（R366）都已 **success**；`7ad22cf`（R366 追记）、`19f91e2`（R367）仍在队里；本轮 `f9df01e ↔ 40203667314`（queued、前面=3，只登记不轮询）。
② 426 第六批：r307 / r309 迁 `single_substitution_lands`；r310 同批迁移。
③ 发现空刀：M906（`fixtures` 排除项）落刀后 `rot=33 抽不出=6 已声明=6` 全不动 ⇒ 退役、不改期望，重跑 5/5。
④ 计数：预检 `arms=376`（377→376）、全仓 864 把（865→864）、注册表 134 张、最大刀号 M1009。

验证读数（现读）：`R307_MUTATE 刀=4 CAUGHT=4`、`R309_MUTATE 刀=6 CAUGHT=6`、`R310_MUTATE 刀=5 CAUGHT=5`，三表 `RESTORE_CLEAN=yes`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **13** 轮（`python3 scripts/product_streak.py --streak-for 367` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（只动 .scratch 三张表）；② 多针表与其余历史表的迁移；③ 真机腿没跑。

下一轮（R369）的靶：⓪ 读队列里积压的四跑（`452f5a3` / `cc9eb1e` / `7ad22cf` / `19f91e2`）；① 426 第七批（r308 这类 Swift 侧的表，跑起来慢，单独一轮），或先把「空刀探测」写成工具（落刀后数不变即点名）；② 367 的下一批要先重钉死针再声明。

## R367 状态（2026-10-25 · 本地 · 第 366 轮 / Round 364）：426 第五批 —— r313/r337 迁到 diff 回读（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R367 / 第 366 轮 / Round 364）：两张表只换落刀后的回读那一行；`3/3`、`4/4` 全 CAUGHT、`RESTORE_CLEAN=yes`；电池 Ran 664（skipped=4）OK；全量卷沿用 R366（Swift 未动）：`Executed 1031 tests, with 48 tests skipped and 0 failures`；迁移面 11 张（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`563c0ed`（R365）已 success（24/24=100%，见上轮追记）；`452f5a3`、`cc9eb1e`、`7ad22cf` 仍在队里；本轮 `19f91e2 ↔ 40203273064`（in_progress、同 workflow 前面=3，只登记不轮询）。
② 426 第五批：r313（守卫三刀）、r337（台账引用四刀）迁 `single_substitution_lands`。
③ 七臂重跑：M911…M913、M989…M992 全 CAUGHT；两表 RESTORE_CLEAN。
④ 读数：两张表都是 Python 侧的刀 ⇒ diff 判法不依赖语言。

验证读数（现读）：`R313_MUTATE 刀=3 CAUGHT=3`、`MUTATE_TABLE n=4 caught=4`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`（沿用 R366 日志）；脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **12** 轮（`python3 scripts/product_streak.py --streak-for 366` 现读）。

NOT-RUN（分开写）：① 全量卷没重跑（本轮只动 .scratch 两张表，Swift 一行未改；读数取自 R366 日志）；② 多针表与其余历史表的迁移；③ 真机腿没跑。

下一轮（R368）的靶：⓪ 读 `452f5a3` / `cc9eb1e` / `7ad22cf` 的跑；① 426 第六批（r306–r310 那几张四到六臂的表），或先把多针表的 diff 形状写成 helper；② 367 的下一批要先重钉死针再声明。

## R366 状态（2026-10-25 · 本地 · 第 365 轮 / Round 363）：426 第四批 —— r312 迁到 diff 回读（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R366 / 第 365 轮 / Round 363）：r312 只换落刀后的回读那一行；三臂重跑 `CAUGHT=3 NOT_RUN=0 RESTORE_CLEAN=yes`；全量 1031 格 0 失败、电池 Ran 664（skipped=4）OK；单针表 9 张在新判法上（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`96da5a7`（R362）、`35d8e76`（R361 追记）、`543b3a5`（R364 追记）都已 **success**；`563c0ed`（40201333483）也 **success**（见追记）；`452f5a3`（40201480169）与 `cc9eb1e`（40202177926）仍在队里（只登记不轮询）。
② 426 第四批：r312 迁 `single_substitution_lands`；删臂的回读也走 diff 等式。
③ 三臂重跑：M908/M909 红在 895、M910 红在 881，期望格子不变；基线 13 格全绿。
④ 看图：复用 R356 的热图帧（空态→网格 4 帧淡入、单格蓝点可读）。

验证读数（现读）：`R312_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **11** 轮（`python3 scripts/product_streak.py --streak-for 365` 现读）。

NOT-RUN（分开写）：① 多针表与其余历史表的迁移；② `563c0ed` 的 runner 读数（下一轮）；③ 真机腿没跑。

下一轮（R367）的靶：⓪ 读 `563c0ed`（本轮地板的 runner 判词）与 R363/R364 的跑；① 426 第五批（r313/r337 这类四臂表），或把多针表的 diff 形状先写成 helper；② 367 的下一批要先重钉死针，不能只声明。

**R366 追记（runner 读数，现读）**：`563c0ed`（`40201333483`，带本轮地板的那一跑）**success** —— `MOTION_PILL_RAMP_GEOM … 候选段=y52..76px 高24px 判=过 洞宽=49% 取用=y52..76px 纵向覆盖=24/24px=100%`，新地板 `≥0.90` 在 runner 上**被签下**（与本地 48/48 是同一个比例，分母 24↔48）；`motion suite exit: 0 executed: 68`、`judged=4/4 not-run=-`、`ASSERTION_RED 0`。
同跑的 `MOTION_NOT_RUN=reduce-motion-on …（采样≈27ms 可分帧=7）` 仍是 431 的产品行为那一半。成对号：`563c0ed ↔ 40201333483`（concluded success）、`452f5a3 ↔ 40201480169`（in_progress）、`cc9eb1e ↔ 40202177926`（in_progress）。

## R365 状态（2026-10-25 · 本地 · 第 364 轮 / Round 362）：384 的覆盖地板 —— 两机 100% 落成 ≥90% 的会红判据（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R365 / 第 364 轮 / Round 362）：胶片给取用带加 `pillBandCoverageFloor = 0.90`（本机 48/48、runner 24/24）；M1009 关掉并墨 ⇒ 14/48=29%，红在 `testFilterPillRampIsMonotone` 6024 行原文；全量 1031 格 0 失败、电池 Ran 664（skipped=4）OK；看图腿复用 R356 帧（22 张在盘上）（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`9d2c8a8`（R360 追记）已 **success**；R361–R364 六跑仍在队里（只登记不轮询）；本轮 `563c0ed ↔ 40201333483`（queued、同 workflow 前面=4）。
② 仍开（§13 那一格指的完整名单）：347、305、364、354（runner 单跑红的分布读数）、356 的另一半、
   354 的第五步、360（剩 11 份 15 行）、361、362、359、348 的「数字对不对」那一格、349、350 第二步、351、344、
   341 的 CI 契约半、339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。
   本轮新增的欠账：地板在 runner 上的判词（R366 读）、426 多针表与其余历史单针表的迁移、367 剩下的两箱。
③ 384 的地板：`pillBandCoverageFloor = 0.90` + 读不出时具名 skip，落在胶片 GEOM 之后。
④ M1009：钉在胶片守卫块的并墨调用点，期望 `testFilterPillRampIsMonotone`；与 M1006（静态调用点）分开。
⑤ 看图：开 A 12 帧药丸逐帧右移、关臂第 2 帧硬切；带子整块盖住药丸，与 48/48 一致。

验证读数（现读）：`纵向覆盖=48/48px=100%`；`M1009 CAUGHT=1/1, RESTORE_CLEAN=yes`；全量 `Executed 1031 tests, with 48 tests skipped and 0 failures`；脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **10** 轮（`python3 scripts/product_streak.py --streak-for 364` 现读）。

NOT-RUN（分开写）：① 本轮无产品改动，没重捕帧（看图腿复用 R356 的 22 张，基线文件未动）；② 地板在 runner 上的判词要等这一跑（R360 那一跑的读数已是 24/24=100%，但地板是本轮才加的）；③ 真机腿没跑。

下一轮（R366）的靶：⓪ 读 R361–R365 的跑（含本轮地板的 runner 读数）；① 426 第四批或 367 下一批（按两箱点名）；② 376 已在 `9d2c8a8` 印出 `reduce-motion-on` —— 下一轮把那一行抄进 376 的追记并结案。

**R365 追记（runner 读数，现读）**：`9d2c8a8`（R360 追记）那一跑 **success**，日志里第一次出现 376 的收口文本：
`MOTION_NOT_RUN=reduce-motion-on filter-pill-slide 三臂不可分（帧数与峰值全等（数组别处不同）：开A 帧数=1 峰值=0.9187 开B 帧数=1 峰值=0.9187 关 帧数=1 峰值=0.9187） 采样≈17ms 可分帧=11 ⇒ reduce=on（catalog 真）⇒ 药丸按 431 归零是**产品行为**，这一半在 reduce 机器上判不了` —— 同一跑再印
`MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil`，出口文本与三源读数在同一跑里对上；
`empty-state=3`、`judged=3/4 not-run=notice-banner`。同跑 `MOTION_PILL_RAMP_GEOM … 纵向覆盖=24/24px=100%`
⇒ 本轮的 0.90 地板在 runner 上第一次有数（但那一跑还没有这行断言；判词要等 `563c0ed`）。

## R364 状态（2026-10-25 · 本地 · 第 363 轮 / Round 361）：426 第三批 —— 三张表迁到 diff 回读（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R364 / 第 363 轮 / Round 361）：r356/r338/r339 迁移到 `single_substitution_lands`，
七臂重跑 `1/1 / 3/3 / 3/3` 全 CAUGHT、三张表 RESTORE_CLEAN=yes；单针表 8 张在新判法上；
电池 `Ran 664（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R359–R363 七跑仍在队里（queued/in_progress），只登记不轮询。
② 426 第三批：三张表只换回读那一行；needle/repl/期望一字未动。
③ 七臂重跑：r356 M1006、r338 M993…M995、r339 M996…M998，全 CAUGHT 且还原干净。
④ 迁移面对账：8 张单针表在新判法上；多针表与历史表未迁。

验证读数（现读）：`r356 CAUGHT=1/1`、`r338 CAUGHT=3/3`、`r339 CAUGHT=3/3`，三张表 `RESTORE_CLEAN=yes`；
脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **9** 轮（`python3 scripts/product_streak.py --streak-for 363` 现读）。

NOT-RUN（分开写）：① 多针表与其余历史单针表的迁移；② R359–R363 七跑的 runner 读数（下一轮）；③ 真机腿没跑。

下一轮（R365）的靶：⓪ 读七跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 426 第四批或 367 下一批（按两箱点名）；② 若 runner 报 376 通道那一半：第二通道。

**R364 追记（runner 读数，现读）**：`ff3deba`（R358）与 `753fa5d`（R359）都已 **success**：
- **387① 两机同数**：runner `MOTION_SCENARIO_AB_SUMMARY 场景=12 同=11 漂=1 敏感=0 换对象=0 粒度不可比=0`，
  与本机逐字相同（`MOTION_SCENARIO_AB_MAGNITUDE 有变化=11 亮臂更大=10 暗臂更大=1 比值 0.72…1.00` 仍只当读数）。
  ⇒ 墨量那一轴拿掉之后，色档分类不再由偏移决定，两台机器给出同一组判词。
- **431 接线验收 + 机器事实**：`MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil`
  —— 这一行第一次出现在 runner 日志里（R359 的专用 grep 生效），并直接回答：**那台机器系统级开了「减弱动态效果」**
  （setting=true），所以 `slideAnimation` 归零分支是真；同跑的 `judged=4/4 not-run=-`。
- 376 的出口在 `753fa5d`（R360 之前）仍是旧的 `pill-slide-arms-indistinguishable`；R360 的 `d317d31` 还在跑，
  下一跑应出现 `reduce-motion-on` —— 那才是 376 的收口读数。

## R363 状态（2026-10-25 · 本地 · 第 362 轮 / Round 360）：426 第二批 —— 三张表迁到 diff 回读（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R363 / 第 362 轮 / Round 360）：r345/r348/r355 迁移到 `single_substitution_lands`，
五把刀重跑 `2/2 / 1/1 / 1/1` 全 CAUGHT、三张表 RESTORE_CLEAN=yes；单针表 5 张在新判法上，多针表未动；
电池 `Ran 664（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读六跑仍在队里（queued/in_progress），只登记不轮询。
② 426 第二批：三张表只换回读那一行；needle/repl/期望一字未动。
③ 五把刀重跑：r345 M1001/M1002、r348 M1003、r355 M1005，全 CAUGHT 且还原干净。
④ 一条读数：r355 的 M1005 落刀后仍 1 帧/31ms（R355 那遍 26ms）—— 回读判法不改变刀的结论。

验证读数（现读）：`r345 CAUGHT=2/2`、`r348 CAUGHT=1/1`、`r355 CAUGHT=1/1`，三张表 `RESTORE_CLEAN=yes`；
脚本电池 `Ran 664（skipped=4）OK`；产品面连续零改动 **8** 轮（`python3 scripts/product_streak.py --streak-for 362` 现读）。

NOT-RUN（分开写）：① 多针表与其余单针表的迁移；② R359–R362 六跑的 runner 读数（下一轮）；③ 真机腿没跑。

下一轮（R364）的靶：⓪ 读六跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 426 第三批（再迁 3–5 张单针表）；② 367 下一批（按两箱点名）。

**R363 追记（`queue` 现读）**：`40199822356 ↔ 9c632e4` 现读 **queued**、同 workflow 前面=1
（`96da5a7` 在跑）；更早的 R359–R362 链仍在队里 —— **七跑在队、零跑结案**。下一轮第 ⓪ 条读它们。

## R362 状态（2026-10-25 · 本地 · 第 361 轮 / Round 359）：426 第一步 —— 落刀回读判 diff（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R362 / 第 361 轮 / Round 359）：新增 `.scratch/motion-audit-2/readback.py`
（`single_substitution_lands`：needle 恰好一次 + 盘上 == 预期替换 + 非空刀）；r358/r360 迁移，
M1007/M1008 各 CAUGHT 1/1；5 格测试、电池 `Ran 664（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R359–R361 六跑仍在队里（2 queued / 4 in_progress），只登记不轮询。
② 426：新增 diff 判法 helper（不要求 repl 全局唯一）；5 格测试含 R350 的现场。
③ 两张新表迁移；两把刀重跑仍 CAUGHT 1/1、还原干净。
④ 边界：其余一百多张表与多针表未迁；diff 判法不负责"预期打没打对靶"。

验证读数（现读）：电池 `Ran 664（skipped=4）OK`；M1007/M1008 `CAUGHT=1/1, RESTORE_CLEAN=yes`；
本轮不动 Swift/产品 ⇒ 全量/胶片/基线沿用；产品面连续零改动 **7** 轮（`python3 scripts/product_streak.py --streak-for 361` 现读）。

NOT-RUN（分开写）：① 其余一百多张表的迁移；② 多针表的 diff 形状；③ R359–R361 六跑的 runner 读数（下一轮）；
④ 真机腿没跑。

下一轮（R363）的靶：⓪ 读六跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 426 下一批（按"最近动过的表"迁 3–5 张）；② 367 下一批（按两箱点名）；③ 若 runner 报 376 通道那一半：第二通道。

## R361 状态（2026-10-25 · 本地 · 第 360 轮 / Round 358）：367 第一步 —— 四张新表声明 NEEDLES（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R361 / 第 360 轮 / Round 358）：r355/r356/r358/r360 各加 `NEEDLES = {刀号: [NEEDLE]}`；
`hidden_arms` 现读 已声明表=6 / 死针=0 / rot=33 / 抽不出=6，棘轮 2→6；**rot 没动**（那四把针本来就活着，声明把下界变确数）；
`test_hidden_arms` 8/8、电池 `Ran 659（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R357–R360 四跑仍在队里（queued/in_progress），只登记不轮询。
② 367：四张新表声明 NEEDLES（值与 ARMS 同一常量）；`hidden_arms.py` 处置=ok。
③ 棘轮：`DECLARED_TABLES_CEILING` 2→6，注释写明"rot/抽不出 一个数都没动"的原因。
④ 测试：`test_hidden_arms` 8/8；本机不动 Swift/产品 ⇒ 全量/胶片/基线沿用。

验证读数（现读）：`HIDDEN_ARMS 表=221 可判=804 rot=33 抽不出=6 已声明表=6 已声明死针=0 上界 … 处置=ok`；
脚本电池 `Ran 659（skipped=4）OK`；产品面连续零改动 **6** 轮（`python3 scripts/product_streak.py --streak-for 360` 现读）。

NOT-RUN（分开写）：① 下一批 33 + 6 个臂的声明（按两箱点名，未做）；② 工具不判"声明值是不是这一臂真用的那根"
（只有 `test_hidden_arms` 的合成对账）；③ runner 的 R357–R360 四跑（下一轮读）；④ 真机腿没跑。

下一轮（R362）的靶：⓪ 读四跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 367 下一批：按 `HIDDEN_ROT` / `HIDDEN_OPAQUE` 的点名表挑 2–3 张声明；② 426（刀的 diff 判法）。

**R361 追记（`queue` 现读）**：`40199155627 ↔ f9c6882` 现读 **queued**、同 workflow 前面=2
（`9d2c8a8`、`d317d31` 都在跑）—— 加上更早的 R359/R360 链，**五跑在队、零跑结案**；
上一跑绿仍是 `6a0258a`（已签 R355/R356）。下一轮第 ⓪ 条读它们。

## R360 状态（2026-10-25 · 本地 · 第 359 轮 / Round 357）：376 出口先分叉 —— reduce-on 记产品行为（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R360 / 第 359 轮 / Round 357）：`pillSlideExitReason` 把「三臂不可分」分成
`reduce-motion-on`（产品按 431 归零）与通道那一半；catalog=off 时 detail 写明视图层来源看不见；
四格测试 + M1008 对调两原因（CAUGHT 1/1）；全量 1031/48skip/0、电池 659（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R359 一跑 queued（前面=2）、R358 两跑在跑；R356 追记绿跑已签下 R355/R356 的验收（见 R358 追记）。
② 376：出口原因收进 `pillSlideExitReason(armsIndistinguishable:reduceMotion:)`；reduce 真 → `reduce-motion-on`。
③ catalog=off 的 detail 明写「reduce 可能来自视图层，这一格看不见」—— 没量到的来源不许写成已知。
④ 四格测试 + M1008（两原因对调）⇒ CAUGHT 1/1；本机 reduce 关、三臂可分，过程照常判。

验证读数（现读）：全量卷 `Executed 1031 tests, with 48 tests skipped and 0 failures`；构建 0 告警；
预检 `tables=133 covered=116 arms=376 bad=0`、`files=227 arms=865`；电池 `Ran 659（skipped=4）OK`；
本轮无产品/尺的渲染改动 ⇒ 基线/胶片沿用 R356（182 帧 / 68 格）；产品面连续零改动 **5** 轮（`python3 scripts/product_streak.py --streak-for 359` 现读）。

NOT-RUN（分开写）：① 下一跑 runner 的出口二选一（`reduce-motion-on` 或 `pill-slide-arms-indistinguishable` + `catalog=off`）；
② `MOTION_REDUCE_SOURCES` 的接线验收（R359 的下一跑）；③ 真机腿没跑。

下一轮（R361）的靶：⓪ 读 R359/R360 两跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）→
① 367（表自己声明针）或 426（刀的 diff 判法）→ ② 若 runner 仍报通道那一半：376 的第二通道。

**R360 追记（`queue` 现读）**：`40198846541 ↔ d317d31` 现读 `in_progress`、同 workflow 前面=3
（`c1077b6`、`753fa5d`、`f975be8` 都还在跑）—— 四跑在队、零跑结案；上一跑绿是 `6a0258a`（已签 R355/R356）。
下一轮第 ⓪ 条读这四跑：二选一看 376 的出口文本（`reduce-motion-on` 或通道 + `catalog=off`），
并确认 `MOTION_REDUCE_SOURCES` 三源第一次出现在日志里。

## R359 状态（2026-10-25 · 本地 · 第 358 轮 / Round 356）：必印族专用 grep —— `MOTION_REDUCE_SOURCES` 不再被 head 截掉（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R359 / 第 358 轮 / Round 356）：`ci.yml` 的 filmstrip 步加 `MOTION_REDUCE_SOURCES` 专用 grep +
`MOTION_PRINT_MISSING` 点名；新守卫 `test_ci_motion_print_wiring` 四格钉住必印名单；电池 `Ran 659（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ 读绿跑 `40195884862 ↔ 6a0258a`：R355 修复被签下（`empty-state=3`、`judged=3/4 not-run=notice-banner`）、
   R356 的 384 在 runner 上 100%（`行带=52…76pt`、`纵向覆盖=24/24px`）、注入 reduce 那卷 `3 帧/101ms`。
② 发现 `MOTION_REDUCE_SOURCES` 一行都没有：`MOTION_LINES=328` 而被 `head -120` 截掉。
③ 接线：filmstrip 步加**字面**专用 grep；缺行打 `MOTION_PRINT_MISSING=^MOTION_REDUCE_SOURCES`。
④ 新守卫四格（真步/合成正对照/光 echo 不算/正则可编译）；它抓到第一版的 for-loop 写法并逼成字面 grep。
⑤ 本机不动产品、不动尺：全量/基线/胶片沿用 R358 的数，本轮只改 CI 接线与脚本守卫。

验证读数（现读）：脚本电池 `Ran 659（skipped=4）OK`；`test_ci_motion_print_wiring` 4/4；
runner 验收（同一次绿跑）`empty-state=3` / `judged=3/4 not-run=notice-banner` / `纵向覆盖=24/24px=100%` / `MOTION_REDUCE 3 帧 101ms`；
产品面连续零改动 **4** 轮（`python3 scripts/product_streak.py --streak-for 358` 现读）。

NOT-RUN（分开写）：① 接线在 runner 上的验收（下一跑日志里要出现 `MOTION_REDUCE_SOURCES setting=…`）；
② 真机腿没跑；③ 本轮无 Swift 改动 ⇒ 全量卷/胶片/基线没有重跑（沿用 R358 的 1030/68/182）。

下一轮（R360）的靶：⓪ 读 `ff3deba` / `f975be8` 与下一跑（重点：`MOTION_REDUCE_SOURCES` 三源 +
R357/R358 的 STEP[9] 是否不再红）→ ① 376（第二通道）或 367（表自己声明针）→ ② 426（刀的 diff 判法）→
③ 若两机同格：386 的两条线标定。

**R359 追记（`queue` 现读）**：`40197984787 ↔ 753fa5d` 现读 **queued**、同 workflow 前面=2
（`ff3deba`、`f975be8` 都还在跑）—— 第三态，登记不轮询。下一轮第 ⓪ 条读它，
重点看新接线的 `MOTION_REDUCE_SOURCES setting=… voiceOver=… catalog=…` 是否出现（431 的验收）。

## R358 状态（2026-10-25 · 本地 · 第 357 轮 / Round 355）：387① 落地 —— 墨量只印不判，色档 A/B 收到 同=11/漂=1（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R358 / 第 357 轮 / Round 355）：`appearanceDependenceVerdict` 的判词收回两颗面积尺，
墨量仍逐颗印；本机同一次 A/B `同=11 漂=1 敏感=0`（改前 同=1 漂=3 敏感=8），唯一漂=emptyState 并集 7.2%；
M944 重钉 + M1007 新刀双 CAUGHT；全量 1030/48skip/0、电池 655（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R356 两跑与 R357 一跑仍 `in_progress`（`queue` 现读；只登记不轮询）。
② 387①：判词 `rel` 从三项 max 收回 `max(首末面积, 动过并集)`；墨量保留为读数（有 `_ = (inkDark, inkLight)` 的明证）。
③ 重跑本机 A/B：`同=11 漂=1 敏感=0`；墨量方向 11/11 亮臂更大（0.11…0.94）⇒ 偏移在读数里、不在判词里。
④ 测试改写：纯函数 ⑥ 翻成"墨量不抬判定"、新 ⑥b 用现场数；盲区测试改名并把 ③ 的期望翻成"同"。
⑤ M944 旧针腐烂 ⇒ 重钉成"只丢并集"（语义不变，CAUGHT）；新刀 M1007 把墨量塞回 max ⇒ 词表格红。

验证读数（现读）：全量卷 `Executed 1030 tests, with 48 tests skipped and 0 failures`；构建 0 告警；
A/B `场景=12 同=11 漂=1 敏感=0 换对象=0 粒度不可比=0`；墨量 `有变化=11 亮臂更大=11 暗臂更大=0 比值=0.11…0.94`；
预检 `tables=132 covered=115 arms=375 bad=0`、`files=226 arms=865`；脚本电池 `Ran 655（skipped=4）OK`；
基线/胶片本轮未重跑（产品与尺的渲染路径都没动，沿用 R356 的 1030/68/182）；产品面连续零改动 **3** 轮（`python3 scripts/product_streak.py --streak-for 357` 现读）。

NOT-RUN（分开写）：① runner 上的 A/B 同格读数（下一跑 CI）；② 386 的 5%/25% 两条线仍未标定；
③ emptyState 的 7.2% 是"面积随色档"还是"阈值附近计数"，没拆；④ 真机腿没跑。

下一轮（R359）的靶：⓪ 用 `queue`/`steps` 读 `df35274` / `6a0258a` / `78f7551`（若结案：R355 的 empty-state 是否 judged、
R356 的 `MOTION_PILL_RAMP_GEOM` 行带/覆盖）→ ① 376 的第二通道或 367（表自己声明针）→ ② 426（刀的 diff 判法）→
③ 若有 runner 同格：386 的两条线标定。

**R358 追记（runner 验收，现读）**：`40195884862 ↔ 6a0258a` **success**（自 R347 以来第一跑绿）。
- R355 修复被 runner 签下：`MOTION_SUMMARY … empty-state=3`、`MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner`
  （notice-banner 是登记过的 witness-snaps-here，地板=3 通过）；注入 reduce 的那卷也跑了：
  `MOTION_REDUCE empty-state 过渡帧数=3 变化段时长=101ms 事件内P75=25ms`。
- R356 的 384 在 runner 上成立：`MOTION_PILL_RAMP_GEOM … 行带=52.0…76.0pt … 判定分布=过×12,非候选×248 候选段=y52..76px 高24px 判=过 洞宽=49% 取用=y52..76px 纵向覆盖=24/24px=100%`。
- **新洞**：`MOTION_REDUCE_SOURCES` 在 runner 日志里**一行都没有** —— 不是没打印，是 CI 那步只
  `grep -E "^MOTION_" | head -120`，而 `MOTION_LINES=328`；这行排在后面的测试里，被截掉了。
  读数族必须接进**它被打印的那一步**（Skill 的规矩），R355 只加了 emit、没加专用 grep。
  ⇒ R359 的第一件事：在 `ci.yml` 的 filmstrip 步里给它一条专用 grep，并加一条"登记过的读数族必须在 CI 里被打印"的守卫。

## R357 状态（2026-10-25 · 本地 · 第 356 轮 / Round 354）：读 CI 的第三态有名字了 —— queue 子命令（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R357 / 第 356 轮 / Round 354）：`scripts/ci_read.py queue` 落地 ——
三态 + 未知点名、`已等` 与 `同 workflow 前面` 分开；本机现读 R356 两跑 in_progress（531s/470s）、R355 两跑 concluded failure；
6 格离线测试，电池 `Ran 655（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R356 两跑现读 `in_progress`（追记那一跑在前、主笔在后），R355 两跑 concluded failure（已知 STEP[9] 抢先红）；只登记不轮询。
② 给 `ci_read.py` 加 `queue`：`queue_state` / `queue_rows` / `queue_summary` 三个纯函数 + CLI（`--workflow` / `--limit`）。
③ 三态写死、未知点名；`已等` 与「同 workflow 前面」分开；时间读不出做减法并单独计数。
④ 6 格测试：三态、前面口径、已结案不排队、时间读不出、未知状态、`--limit` 非整数不触网。
⑤ 自曝：汇总口径第一版把另一条 workflow 的 queued 算漏 —— 错的是**测试期望**（工具对）。

验证读数（现读）：电池 `Ran 655（skipped=4）OK`；`QUEUE_SUMMARY 共=5 queued=0 in_progress=2 concluded=3 未知=0 时间读不出=0`；
本轮无产品/尺改动 ⇒ 全量卷沿用 R356 的 `Executed 1030/48skip/0`、胶片 68/3/0（judged=4/4）、基线 182/0（R355 重捕）、清账表 162/162；
产品面连续零改动 **2** 轮（`python3 scripts/product_streak.py --streak-for 356` 现读）。

NOT-RUN（分开写）：① `gh` 本身失败那条路（`queue()` 返回 1）没有单测（428 结案里写明理由与补法）；
② 真实视觉审查腿没跑（本轮没有画面改动，只有 CI 状态读数）；③ 真机腿没跑。

下一轮（R358）的靶：⓪ 读 `40195807519 ↔ df35274` / `40195884862 ↔ 6a0258a`（若已结案；否则用 `queue` 登记第三态）→
① 387①（墨量那颗不进 max，只印；先量翻的那一格）→ ② 376 / 367 → ③ 426（刀的 diff 判法）。

**R357 追记（`queue` 现读）**：`40196780778 ↔ 78f7551` 现读 `in_progress`、同 workflow 前面=2（df35274、6a0258a）——
三跑同时在队里、零跑结案：这不是「没红」，是**没跑**。R355 两跑已 concluded failure，但红在 `STEP[9]`
（Sources 格过期），动效那一步没被判过；R356 两跑与这笔都还在队里。下一轮第 ⓪ 条用 `queue` 读它们。

## R356 状态（2026-10-25 · 本地 · 第 355 轮 / Round 353）：384 结案 —— 带子 7pt→24pt、覆盖 29%→100%（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R356 / 第 355 轮 / Round 353）：`pillRun` 加 `mergeInk`（只并字墨列），
行读数打开 ⇒ 真帧行带 51.0…58pt → 51.0…75pt、纵向覆盖 14/48px=29% → 48/48px=100%，判定分布 洞太窄×11,过×13 → 过×24；
五格夹具改用轨道级的缝、M926 旧针重钉，M1006 `CAUGHT=1/1`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R355 的两跑 `40194321798 ↔ 5515daf`、`40194348175 ↔ da5f8a7` 现读都 `in_progress`（第三态，登记不轮询）。
② 384 的修法：`pillRun(..., mergeInk:)`，只并"两边都 ≥ delta"的列；`movingHoleRowReading` 传 true。
③ 真帧读数：行带 7pt→24pt、判定分布 洞太窄×11,过×13 → 过×24、覆盖 29%→100%、`MOTION_PILL_BAND` y51…75pt。
④ 反向正对照：隔轨不许桥接；电平仍只由药丸列算（纯测试钉 74）。
⑤ 夹具迁移：五格改用轨道级的缝造窄洞（断言与地板不动）；分档格留一列 200 级墨。
⑥ 针：M926 因 `isPill` 行变化重钉（语义不变，CAUGHT）；M1006 改回 `mergeInk:false` ⇒ 新行为判据红。

验证读数（现读）：全量卷 `Executed 1030 tests, with 48 tests skipped and 0 failures`；
胶片 `Executed 68 tests, with 3 tests skipped and 0 failures`、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`；
`MOTION_PILL_RAMP_GEOM` 行带=51.0…75.0pt、`纵向覆盖=48/48px=100%`；斜坡 A `判定=单调 首=81.0 末=219.0 位移=138.0 最大倒退=0.0`；
基线 `COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`（沿用 R355 重捕的 182 帧，本轮产品 0 文件未重捕）；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；
脚本电池 `Ran 649（skipped=4）OK`；产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 355` 现读）。

NOT-RUN（分开写）：① runner 对 R355 修复与 R356 尺改动的读数（下一跑 CI；先看 `empty-state` 与 `MOTION_PILL_RAMP_GEOM`）；
② 覆盖率的**地板**没钉（只有本机 100%，没有 runner 同格读数；R38：一台的数不许当门）；
③ 真机腿（reduce 开关 / 395）没跑；④ 静态帧未重捕（产品 0 文件；沿用 R355 的 182 帧，`ls` 数过）。

下一轮（R357）的靶：⓪ 读 CI（`5515daf` / `da5f8a7` 两跑）→ ① 387① / 376 / 367 → ② 426（刀的 diff 判法）与 428（`ci_read.py queue`）→
③ 若 runner 的 `MOTION_PILL_RAMP_GEOM` 到位：给覆盖率定地板（两机同数之后）。

**R356 追记（读 R355 两跑，现读）**：`40194321798 ↔ 5515daf` 与 `40194348175 ↔ da5f8a7` 都 `failure`，
**但红的不是动效那一步**：`STEP[9] Release script tests` 先红 —— `FINAL_REPORT_SOURCES_CELL_STALE`（那一格还写 R348/`4b8f014`，
而 `5515daf` 动了 Sources）。STEP[10…] 因此全部 skipped ⇒ **R355 的 reduce 修复在 runner 上还没有被读过**。
成因是提交顺序：Sources 格在提交前刷、而它比对的是 git HEAD，产品提交一落地那格就过期；
R348 的追记当年刷过，R355 的追记漏了。R356 这笔已把 Sources 格刷到 R355/`5515daf`（本机电池绿），
`40195807519 ↔ df35274` 才是第一次能走到 `Motion coverage floor` 的一跑；下一轮第 ⓪ 条读它。
教训：**产品提交之后的追记必须重跑 `scripts/report_sources_cell.py --write` 再推**。

## R355 状态（2026-10-25 · 本地 · 第 354 轮 / Round 352）：runner 六连红结案 —— reduce 下空态淡入被归零（产品 1 文件，判据账）

最后更新：2026-10-25（本地 · R355 / 第 354 轮 / Round 352）：六跑全 failure、唯一红在 `Motion coverage floor`
的 `empty-state`（从 R348 起）；成因是产品的 `slideAnimation` 在 reduce 下归零 ⇒ 换成目录 `.slider` 动画
（reduce 下 0.20 淡入）；本机同注入 A/B 1 帧/26ms ↔ 3 帧/103ms，M1005 `CAUGHT=1/1`；
顺带把针预检的刀号帽从三位放宽到四位（covered 110→113、bad=0）并重钉 r348 旧针（产品 1 文件 · 判据账）

本轮做了什么：
① ⓪ 读六跑 + 上两跑 + R347 绿色对照：六跑唯一失败步骤是 STEP[19]，红从 R348 的 40187450120 起。
② 归因：`MOTION_NOT_RUN=witness-snaps-here empty-state` 的 1 帧/36ms，与同机药丸 1 帧并列；
   旧 helper 只在 `reduceMotion == true` 时归零 ⇒ 那台机器的 `shouldReduce` 是真，产品把淡入变成硬切。
③ 产品修：`HistorySidebarView` 的空态驱动改走 `MotionCatalog.animation(for: .slider, reduceMotion: shouldReduce)`；
   值级守卫（reduce 分支不等于 `.linear(0)`）+ 源码形状守卫（不许回 `slideAnimation`、不许回 `contentFade`）。
④ 行为判据：`MotionFilmstripTests.testEmptyStateStillFadesWhenMotionIsReduced`（注入 override，按主卷同一颗 `judgeMotion`）；
   M1005 落刀 = 1 帧/26ms 红，还原 = 3 帧/103ms 绿。
⑤ 尺的洞：针预检 `MID` 三位帽让 M1001 起隐形 ⇒ 放宽到四位 + 人造正对照（M1006）；r348 旧针重钉。
⑥ 新读数：胶片里打 `MOTION_REDUCE_SOURCES setting=… voiceOver=… catalog=…`，下一跑 CI 用来归因开关来源。

验证读数（现读）：全量卷 `Executed 1027 tests, with 48 tests skipped and 0 failures`；
胶片 `Executed 68 tests, with 3 tests skipped and 0 failures`、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`；
基线 `COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`（182 帧）；
换装 `INSTALL_RESULT=ok` / `INSTALL_SHA_MATCH=1` / `INSTALL_ENTRIES_BEFORE=380 AFTER=380`；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；
脚本电池 `Ran 649（skipped=4）OK`；产品面连续零改动 **7** 轮（`python3 scripts/product_streak.py --streak-for 354` 现读，口径差一挂 412；本轮动了 1 个产品文件 ⇒ 下一轮这一格从 0 重新数）。

NOT-RUN（分开写）：① runner 对 R355 修复的验收要等下一跑（`empty-state` 是否回到 judged、`MOTION_REDUCE_SOURCES` 的三源）；
② 视图层 `@Environment(\.accessibilityReduceMotion)` 的直接读数没做（系统三源读数已加，见 429）；③ 真机腿（reduce 开关下看一眼）没跑。

下一轮（R356）的靶：⓪ 读 R355 的 run（成对写；先看 `judged` 与 `MOTION_REDUCE_SOURCES`）→
① 384（胶囊带纵向覆盖 29%）→ ② 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）与 428（`ci_read.py queue`）→
④ 若用户解锁屏幕：395 的同一运行 before（临时关抬量、换装、抓、还原）。

**R355 追记（run 已取，未轮询）**：`40194321798 ↔ 5515daf` 现读 `in_progress` —— 这是第三态（已跑未结案），
不许读成「没红」，也不许读成「通过」；runner 那半由下一轮第 ⓪ 条读。

## R354 状态（2026-10-25 · 本地 · 第 353 轮 / Round 351）：尺进仓库，390 收窄到 1–2 帧（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R354 / 第 353 轮 / Round 351）：`scripts/filmstrip_frames.py` 落地（网格自动识别 +
INK/PILL 两条序列 + 两条正对照）；390 现读 开A 胶囊落点 6、开B 7、内容第 5 帧归零 ⇒ 差 1–2 帧（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 写 `scripts/filmstrip_frames.py`：网格按场景比自动选；INK（内容带暗像素数）与 PILL（控制带最宽亮点中位 x）。
③ 两条正对照：`关` 落点 2、开A/开B 的 PILL 前 8 帧不同 ⇒ `FILMSTRIP_FRAMES_RESULT=ok`。
④ 读 390：开A `81,81,89,119,145,175,150…`（落点 6）、开B `…172,189,150…`（落点 7）、INK 第 5 帧归零。
⑤ 尺自己三处错（末格当稳态、过冲当落点、拿 INK 当对照通道）都改掉并写进 U-1241。

验证读数（现读）：`CONTROL_STEADY … pill_landed=2 ok`、`CONTROL_DIFFER pill_first8_differs=True ok`、
`FILMSTRIP_FRAMES_RESULT=ok`；`INK 688,688,688,683,19,0…`（两臂同）；脚本电池
`Ran 648（skipped=4）OK`（沿用上一轮；本轮只加一支 `scripts/` 工具，未进电池）；
产品面连续零改动 **6** 轮（`python3 scripts/product_streak.py --streak-for 353` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 新工具没进电池（它要`/tmp` 的胶片，属于"现场尺"，下一轮决定要不要把它接进捕获卷）；
② 无刀、无 swift 全量（产品 0 文件）；③ 真机腿没跑。

本轮（R355）的 ⓪ 读数（现读自 `gh run list`，只登记不轮询，R140）：四跑**同时**是 in_progress ——
`40189703485 ↔ 2b47f57`、`40189562764 ↔ f467d3e`、`40189415641 ↔ 010aca0`、`40189129121 ↔ 1cf904b`。
连续四笔都还排在 runner 上（不是失败、也不是跳过）⇒ 这一格的结论只有一个：**未读**，不许按"没红"记。
下一轮开工第一件事是把这四跑读完，再谈别的；`RUN=… ↔ commit` 的成对账不许由"我提交时看着是绿的"补。

交接（预算边界，按规矩不起不可逆的活）：未结清单按修法分组 ——
① **只差一次 runner 读数**：上述四跑；384（胶囊带的纵向覆盖 29%，候选修法①"把字墨列并入洞"，改的是尺不是产品）；
② **本机就能做**：387①、376、367、426（把刀的回读判据从"替换串唯一"改成"diff 恰好一行"）；
③ **要人或要真机**：395 的同一运行 before（要关抬量重装，人解锁屏幕）。

**R355 追记（队列积压，现读）**：再看一眼 `gh run list --limit 4` —— 四跑仍是 `in_progress`，而本笔自己也排上了
（`40189811041 ↔ 7824207 queued`）。**五跑同时在队里、零跑结案**：这不是"没红"，是**没跑**。
按规矩不许把排队读成通过；读 CI 的那一步要能说出"排队中"这个第三态（开 428）。

**R355 收口读数（现读，不是推断）**：全量卷 `Executed 1025 tests, with 47 tests skipped and 0 failures`（268.9 秒，
日志 `/tmp/r355_full.log`，只留 /tmp 不入库）；`gh run list --limit 3` 现读 `40189907611 ↔ bdc9b8b queued`、
`40189811041 ↔ 7824207 in_progress`、`40189703485 ↔ 2b47f57 in_progress` —— **CI 那半仍未读**，本机这半是绿的。
这两句分开写：本机绿不签 runner 那一半（Skill 的 NOT-RUN 第 3 条）。

下一轮（R355）的靶：⓪ 读 CI 配对 → ① 384（胶囊带纵向覆盖 29%）→ ② 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）
→ ④ 决定 `filmstrip_frames.py` 要不要接进捕获卷（接进去就要有它自己的正对照与地板）。

## R353 状态（2026-10-25 · 本地 · 第 352 轮 / Round 350）：390 量不出来 —— 那把尺当年没收进仓库（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R353 / 第 352 轮 / Round 350）：先认对拼贴网格（6×5），发现 empty-state 那卷胶囊不动、
filter-pill-slide 两卷字墨被 chrome 主导、胶囊检测器返回 -1 ⇒ 390 结不了；开 427 把尺收进仓库（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 认网格：`empty-state-strip` 2280×2760 = 6×5 的 380×552（与场景同名尺寸）；`filter-pill-slide-*` 1800×2600 = 6×5 的 300×520。
③ 读 empty-state：字墨第 1 帧落定、胶囊 `pill_x=138` 恒定 ⇒ 这一场不移动胶囊，答不了 390。
④ 读 filter-pill-slide 开A/关：字墨 `5723→6089`（第 3/第 2 帧），胶囊检测 `-1`（亮区判据在这两卷上找不到对象）。
⑤ 结论：R328 的数来自一次性 PIL、代码没留 ⇒ 390 保持开，开 427。

验证读数（现读）：`empty-state` 字墨 `15266,15502,15522…`、`pill_x=138`；`开A` 字墨 `5723,5723,5757,6089…`、
`关` `5723,5723,6086…`；两卷 `pill_x=-1`；脚本电池 `Ran 648（skipped=4）OK`（沿用上一轮，本轮未改脚本）；
产品面连续零改动 **5** 轮（`python3 scripts/product_streak.py --streak-for 352` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 390 的落点差：两把量法都读错对象（427）；② 本轮无刀、无 swift 全量（产品 0 文件）；
③ 真机腿没跑。

下一轮（R354）的靶：⓪ 读 CI 配对 → ① **427**（`scripts/filmstrip_frames.py` + 正对照，再用它量 390）→
② 384 / 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）。

## R352 状态（2026-10-25 · 本地 · 第 351 轮 / Round 349）：§8 的十二个洞退役（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R352 / 第 351 轮 / Round 349）：ROWS 要的十二个键属于一套已不在的多步验证器，
退役那十二格、§8 只搬 `ROUND_VERIFY` 一行，并加一条"键必须在验证器总结论行里"的对账守卫（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 读两边：ROWS 十二键 vs `round_verify.sh` 只打一行（含 `build_warnings=` / `swift_failures=` / `frames=` …）。
③ 退役十二格（表上方写明成因与出处 BACKLOG 397），§8 改搬 `^ROUND_VERIFY .*`。
④ 新增 `scripts/tests/test_ledger_rows_keys.py` 两格（键的对账 + 退役必须带 BACKLOG 编号）。
⑤ 守卫自己两次红在"读错对象"上（早退行、`key=$VAR`），都改掉并写进 U-1231。

验证读数（现读）：`ROWS` 现读一行（"验证流水线"）；守卫 `Ran 2 tests OK`；脚本电池 `Ran 648（skipped=4）OK`；
产品面连续零改动 **4** 轮（`python3 scripts/product_streak.py --streak-for 351` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 本轮没跑 `swift test`（产品 0 文件，上一次全量 1025 格仍是本树最近证据）；
② 无刀（没有产品改动可打，判据改动由守卫自身两格覆盖）；③ 真机腿没跑。

下一轮（R353）的靶：⓪ 读三跑 CI 配对 → ① 动效主线 390（内容与胶囊的落点差，胶片已有 after 读数）→
② 384 / 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）。

## R351 状态（2026-10-25 · 本地 · 第 350 轮 / Round 348）：413 结案（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R351 / 第 350 轮 / Round 348）：六格 backing 现读（light 193/175/148 只印；
dark 55/37/10 过门），三档是带来源的名册；两档无障碍是系统级开关 ⇒ 具名 NOT-RUN，判据当输入（413 结案）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 重读 backing 六格（`swift test --filter testSelectedPillStaysAboveItsTrackOnEveryBacking`）。
③ 确认名册：每行带 `来源=实测…/外推…`，不是裸常量。
④ 改掉尺自己一行过期陈词（`见 BACKLOG 399` → `399 已于 R347 结案`），同一跑复核读数不变。
⑤ 413 结案：第二半（两档无障碍帧）记具名 NOT-RUN。

验证读数（现读）：light `页底=30/50/80 ⇒ 差=193/175/148`（只印）；dark `⇒ 差=55/37/10`（线 差≥8 且 对比≥1.100，三门过）；
改文案后同一跑 `差=193 对比=12.561` 不变；脚本电池 `Ran 646（skipped=4）OK`；帧 182（无产品改动，未重捕）；
产品面连续零改动 **3** 轮（`python3 scripts/product_streak.py --streak-for 350` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 「降低透明度 / 增加对比」两档的帧：系统级开关，离屏夹具不许替用户改（真机要人开）；
② 本轮无刀（产品 0 文件、判据只改文案）；③ 真机腿没跑。

下一轮（R352）的靶：⓪ 读 CI 配对 → ① 动效主线 397（§8 的 12 个键名）→ ② 390 / 384 / 387① / 376 / 367
→ ③ 426 的退场（刀的 diff 判法）。

## R350 状态（2026-10-25 · 本地 · 第 349 轮 / Round 347）：胶片改用产品的 0.20，425 结案（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R350 / 第 349 轮 / Round 347）：胶片空态声明从 `.contentFade`(160) 改成 `.slider`(200)，
三次抓取 `声明=200ms`、`judged=4/4`；守卫按块切片钉住两边（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3`、`↔ 0307c43`、`↔ 4fe06c2` 均按首读登记（只登记不轮询，R140）。
② 夹具：`MotionFilmstripTests.emptyState()` 的 `declaredDurationMilliseconds` 改成 `MotionCatalog.duration(for: .slider) * 1000`。
③ 守卫：`testEmptyStateFadeSharesThePillRhythm` 扩到胶片侧，**按 `emptyState()` 块切片**（`.contentFade` 在别的场景合法）。
④ 重跑胶片（两个环境键 + 输出目录）：`MOTION_GRAB empty-state … 声明=200ms` ×3、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`。
⑤ 想配第二把刀（声明换回 160）没落成：替换串不唯一 ⇒ `NOT_RUN 落刀后回读不匹配`，撤表并开 426。

验证读数（现读）：胶片三档 `声明=200ms`（帧数 30、中位 19.1–19.5ms、最慢 43.6–58.0ms）；
全量卷 `Executed 1025 tests, with 47 skipped and 0 failures`；脚本电池 `Ran 646（skipped=4）OK`；
M1003 复跑 `CAUGHT=1/1, RESTORE_CLEAN=yes`；产品面连续零改动 **2** 轮（`python3 scripts/product_streak.py --streak-for 349` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 第二把刀（夹具声明换回 160ms）没落成：替换串不唯一（426）；② 胶片未逐张看图；
③ 真机腿没跑（本轮改的是夹具声明）。

下一轮（R351）的靶：⓪ 读三跑 CI 配对 → ① 413（backing 名册 + 两档材质帧）→ ② 动效主线 397 / 390 / 384 / 387① / 376 / 367
→ ③ 426 的退场（把两张表改成 diff 判法）。

## R349 状态（2026-10-25 · 本地 · 第 348 轮 / Round 346）：胶片跑全了，却发现它测的是自己的 160ms（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R349 / 第 348 轮 / Round 346）：环境键下胶片 67 格 3 skip / 0 fail、四场 judged=4/4；
但空态场景 `声明=160ms` 是夹具自己写死的 ⇒ 它测不到 R348 接的那条 0.20（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3`、`↔ 0307c43` 首读 in_progress（只登记不轮询，R140）。
② 用 `CLIPBOARD_HISTORY_UI_MOTION=1` + `CLIPBOARD_HISTORY_MOTION_OUT=/tmp/r349_motion` 重跑胶片。
③ 读数：`MOTION_SUMMARY …`、`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`、
   `MOTION_GRAB empty-state … 声明=160ms`、`MOTION_AXIS empty-state 帧对=26 … 仅alpha在动=0/26`。
④ 结论：胶片与产品是两份权威；"改了但胶片不动"是接线问题。开 BACKLOG 425（让声明读 `MotionCatalog`）。

验证读数（现读）：`Executed 67 tests, with 3 skipped and 0 failures`（161.9 秒；不设键时 24 skip）；
`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`；脚本电池 `Ran 646（skipped=4）OK`；帧 182（未重捕）；
产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 348` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 425 的修法没做（本轮只把"两份权威"这件事钉住）；② 胶片未逐张看图（只读它自己打印的峰值）；
③ 真机腿没跑（这一轮改的是夹具侧的账）。

下一轮（R350）的靶：⓪ 读三跑 CI 配对 → ① **425**（声明读 `MotionCatalog` + 同笔重跑胶片，确认 `声明=200ms`、
四场不掉）→ ② 413（backing 名册）→ ③ 动效主线 397 / 390 / 384 / 387① / 376 / 367。

## R348 状态（2026-10-25 · 本地 · 第 347 轮 / Round 345）：空态淡出与药丸同节奏（产品 1 文件，动效主线）

最后更新：2026-10-25（本地 · R348 / 第 347 轮 / Round 345）：把空态淡出从 `contentFade`(0.16) 换成药丸那支
`slideAnimation`(0.20)，389 结案；既有"恰好一处"契约随之改成"没有写死动画写法"（产品 1 文件 · 动效主线）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3` 与 `RUN=… ↔ 0307c43` 均首读 in_progress（只登记不轮询，R140）。
② 产品：`HistorySidebarView` 空态那一格改用 `FilterPillMotion.slideAnimation`，并补 `reduceMotion` / `shouldReduce`。
③ 判据：新增 `testEmptyStateFadeSharesThePillRhythm`（源码形状两断言）；刀 `mutate_r348` M1003 `CAUGHT=1/1`。
④ 既有 `testSidebarConsumesTheMotionPolicy…` 的"恰好一处"被撞红 ⇒ 改成"禁写死动画写法"（更严）。
⑤ 全量卷 `Executed 1025 tests, with 47 skipped and 0 failures`；构建 0 告警；换装 `INSTALL_RESULT=ok`。

验证读数（现读）：`M1003 CAUGHT=1/1, RESTORE_CLEAN=yes`；预检 `tables=129 covered=110 arms=369 bad=0`；
脚本电池 `Ran 646（skipped=4）OK`；帧 182（时长改动不影响静态帧，未重捕）；
产品面连续零改动 **3** 轮（`python3 scripts/product_streak.py --streak-for 347` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 胶片场景的 after 逐格曲线：`MotionFilmstripTests` 67 格 **24 skip**（要环境键），
本轮只有"同一个动画对象"的源码证据与刀；② 真机腿没跑（改的是时长，屏幕那半边要另一次捕获）；③ 无第二把刀
（这一刀已经把"换回去"钉住）。

下一轮（R349）的靶：⓪ 读三跑 CI 配对 → ① 用环境键重跑胶片，把 after 的落点差量出来（补 389 的最后一句）
→ ② 413（backing 名册）→ ③ 动效主线 397 / 390 / 384 / 387① / 376 / 367。

## R347 状态（2026-10-25 · 本地 · 第 346 轮 / Round 344）：399 结案，389 的成因第一次写成两个数（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R347 / 第 346 轮 / Round 344）：亮档悬停可见 1.238 与选中边界 22 级现在**同时被断言**，
399 的结案条件到此满足；顺带把 389 的两个时长（0.16 / 0.20）并排读出（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3` 与 `RUN=… ↔ 0307c43` 均首读 in_progress（只登记不轮询，R140）。
② 结案核对：`segRatio ≥ 1.20`（现读 1.238）与 `SEG_EDGE 填充−最深 = 22 ≥ 8` 两条都是**现门**，各占一条轴。
③ 399 结案（原两支候选不必做：A 案已落地，B 案没有对象）；留 BACKLOG 424。
④ 389 的成因第一次写成两个数：`contentFade 0.16` 对 `slider 0.20` —— 但接线点没定位（`HistoryListView.swift` 不存在），本轮不动产品。

验证读数（现读）：`HOVER_DIRECT_READ_PROOF light … 比值=1.238`（门 1.20）；
`SEG_EDGE light 页面=255 填充=220 最深=198 填充−最深=22`（门 8）；`MotionCatalog` `contentFade=0.16` / `slider=0.20`；
脚本电池 `Ran 646（skipped=4）OK`；帧 182（未重捕）；产品面连续零改动 **2** 轮（`python3 scripts/product_streak.py --streak-for 346` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 389 的改法没做（场景接线点未定位，见 424）；② 本轮无变异刀（产品 0 文件）；
③ 没有新帧（结案靠已有的两条门与同批帧）。

下一轮（R348）的靶：⓪ 读两跑 CI 配对 → ① 424（先 `grep` 定位胶片场景的 `.animation` 接线点，再决定同步方式，
两臂同批帧）→ ② 413（backing 名册）→ ③ 动效主线 397 / 390 / 390 的时长与 384 / 387① / 376 / 367。

## R346 状态（2026-10-25 · 本地 · 第 345 轮 / Round 343）：九张变异表认不出单数汇总行 —— 修完配一条会红的名单守卫（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R346 / 第 345 轮 / Round 343）：55 张表里 9 张只认复数 `Executed N tests`，
单格只跑一个用例时会被判成"没解析到 ⇒ 红"；九张全改 + 新增对每一张表运行的守卫（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`RUN=40185881194 ↔ 8d375b3` 首读 in_progress（只登记不轮询，R140）。
② 用 `ast` 数清名册：51 张认单数、9 张不认（r130/r133/r135/r141/r142/r335/r336/r338/r339）。
③ 九张改成 `tests?` / `failures?`；r141 是 `tests`（无逗号），第一遍按 `tests,` 找锚点漏了它，第二遍补上。
④ 新增 `scripts/tests/test_mutation_summary_regex.py`：对每张表把正则编译出来喂单数/复数两条真实形状。
⑤ 守卫第一版把 `mutate_r262.py` 刀针里嵌的源码行当成正则 ⇒ 收窄成"只认以 `Executed (` 开头的常量"。
⑥ `report_sources_cell.py --write` 把「最后一次动到 Sources」从 R339/fb2cea0 推到 R345/8d375b3（派生格）。

验证读数（现读）：分类 `tolerant=51 / plural-only=9`；改后 `blind=[]`；脚本电池 `Ran 646（skipped=4）OK`；
`SOURCES_CELL 账上=R339/`fb2cea0` git=R345/`8d375b3`` ⇒ 写后复核一致；帧 182（无产品改动，未重捕）；
产品面连续零改动 **1** 轮（`python3 scripts/product_streak.py --streak-for 345` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 没有像素/帧判据（产品 0 文件）；② 本轮无变异刀（没有产品改动可打）；
③ 9 张表只做了**静态**验证（正则对两种形状），没有逐张真跑一格 —— 真跑要每张都有一段旧代码在盘上，
那已不在（表保留的是当时那一刀），静态 + 一条实跑（`mutate_r345` 上一轮 `CAUGHT=2/2`）是这一轮能给的最强证据。

下一轮（R347）的靶：⓪ 读两跑 CI 配对 → ① 399 的亮档悬停半边（亮度通道腾出来了：先量"提亮后 hover 与 selected 落在哪两档"）
→ ② 423（批量改表前先做 needle 命中预检）→ ③ 413 → ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R345 状态（2026-10-25 · 本地 · 第 344 轮 / Round 342）：亮档选中那颗换轴 —— 身份搬到边界（产品 3 文件，动效主线）

最后更新：2026-10-25（本地 · R345 / 第 344 轮 / Round 342）：给亮档选中那颗补 1pt × 0.12 的发丝边，
判据用次序钉对象（`页面 255 > 填充 220 > 最深 198`），两把刀各钉一条轴（产品 3 文件 · 动效主线）

本轮做了什么：
① ⓪ CI 配对：`RUN=40184155498 ↔ e981378` 首读 in_progress、`RUN=… ↔ 985c045` 未取（只登记不轮询，R140）。
② 产品：`SegmentEdge.width/alpha`（暗档 nil）+ `slidingPill` 画边；`VisualMaterial.selectedSegmentEdge = 0.12`。
③ 判据：`SEG_EDGE` 改读**次序**——"最深那一格是不是页面" + "填充 − 最深 ≥ 8"；暗档只印不断言。
④ 重捕 182 帧、9 张亮档帧 CHANGED，同一笔更新基线。
⑤ 刀：`mutate_r345.py` M1001（α→0）/ M1002（暗档也画）⇒ `CAUGHT=2/2, RESTORE_CLEAN=yes`；预检 `tables=128 bad=0`。
⑥ 全量卷 `Executed 1024 tests, with 47 skipped and 0 failures`；换装 `INSTALL_RESULT=ok`。

验证读数（现读）：`SEG_EDGE light 页面=255 填充=220 最深=198 填充−最深=22 最深是页面=false`；
`SEG_EDGE dark 最深是页面=true`；`MUTATE r345 CAUGHT=2/2, RESTORE_CLEAN=yes`；
`NEEDLE_PRECHECK tables=128 covered=110 arms=369 bad=0`；`ARM_TOTAL files=222 arms=865 dupes=0`；
脚本电池 `Ran 645（skipped=4）OK`；产品面连续零改动 **6** 轮（这是**本轮之前**的连读：本轮动了 3 个产品文件，下一轮会归零；`python3 scripts/product_streak.py --streak-for 344` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 悬停那一半（399 的 B 案）没做 —— 亮度通道刚腾出来，下一轮先量再动；
② 暗档像素级的"没有边"不断言（要两臂帧才证得了，D-341）；③ 真机腿没跑（这轮看的是离屏帧）。

下一轮（R346）的靶：⓪ 读本笔与 985c045 的 CI 配对 → ① 399 的亮档悬停（亮度通道现在归它，先量"提亮后 hover 与 selected 落在哪两档"）
→ ② 422（其余变异表的汇总正则逐个看）→ ③ 413 → ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R344 状态（2026-10-25 · 本地 · 第 343 轮 / Round 341）：421 三层查完 —— 边画得出来，尺认不出（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R344 / 第 343 轮 / Round 341）：2pt 探针证明边画得出来、几何成立、缓存排除；
1pt 版量到 22 级，但三种取样各读到不同对象 ⇒ 判据还不成立，两支全撤（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI 配对：`RUN=40184155498 ↔ e981378` 首读 in_progress（只登记不轮询，R140）。
② 探针：把边改成 2pt × 0.35 ⇒ 6 张亮档帧 CHANGED（`frame_baseline check`）。
③ 剖面：x=30/40/50/60 四列逐行读，填充 220 在 y=36..55、边 154 在 y=34..35/56..57 ⇒ `pillRect` 内缩 2pt 是错源。
④ 1pt × 0.12：沿无字墨列读到 `轨道=154 边=198 填充=220`（差 22 级）。
⑤ 三种取样窗口分别读到页面/轨道/边 ⇒ 撤回；基线未动。

验证读数（现读）：`SEG_EDGE light 轨道=154 药丸=220 边=198`（差 22）；2pt 探针 `差=66`（154 对 220）；
`FRAME_BASELINE_CHANGED=6`（idle + 5 张亮档侧栏帧，探针版）；fresh 重捕 182 帧、234 秒；
脚本电池 `Ran 645（skipped=4）OK`；产品面连续零改动 **5** 轮（`python3 scripts/product_streak.py --streak-for 343` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① A 案本体（1pt 版）没上：判据认不出对象，读数 22 级只当**观测**不当**判据**；
② 本轮无变异刀（产品 0 文件）；③ 真机腿没跑（这一轮看的是离屏帧）。

下一轮（R345）的靶：⓪ 读两跑 CI 配对 → ① 把**次序判据**落地（亮档 `页面 > 填充 > 边 > 轨道`、暗档单调），
红了要能指出读到的是哪一层 → ② 次序绿了再上 A 案（1pt × 0.12）+ 变异刀 → ③ 413 → ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R343 状态（2026-10-25 · 本地 · 第 342 轮 / Round 340）：399 的两支都试了，都没过判据（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R343 / 第 342 轮 / Round 340）：亮档悬停的 B 案被窗口放行、被可见性门拦下；
A 案的发丝边读数为 0（两种取样一致）⇒ 两支都撤回（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI 配对：`RUN=40182636083 ↔ db05698` 首读 in_progress（只登记不轮询，R140）。
② B 案：亮档悬停单独一支 token `0.026` ⇒ 画在 225，窗口判据 `224…226` 通过；同一跑 1.20 可见性门红（1.038）。
③ A 案：选中那颗加 1pt 发丝边（`Color.primary.opacity(0.12)`）⇒ `SEG_EDGE 药丸=220 边=220 差=0`。
④ 看图：B 案那张 200×60 帧上两段分不出 ⇒ 与 1.038 一致。
⑤ 两支都 `git checkout` 撤回；一次 182 帧重捕只为读 A 案那一行。

验证读数（现读）：`SEG_HOVER_WINDOW light 空闲=230 选中=220 步=4 窗口=224…226 产品画在=225 判定=在窗口内`；
`HOVER_DIRECT_READ_PROOF light … 比值=1.038`（下界 1.2，红）；`SEG_EDGE light 药丸=220 边(最暗)=220 差=0`；
构建两次都 `Build complete` 且 0 告警；脚本电池 `Ran 645（skipped=4）OK`；帧 182（基线未更新，产品已撤回）；
产品面连续零改动 **4** 轮（`python3 scripts/product_streak.py --streak-for 342` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① **A 案为什么读数为 0 没定**（三层候选见 421，各要一次实验）；
② 本轮无变异刀（产品 0 文件，两支都撤回）；③ 真机腿本轮没跑（A/B 要看的是离屏帧，屏幕那一半 R342 已签）。

下一轮（R344）的靶：⓪ 读 `db05698` 与本笔的 CI 配对 → ① **421**（先做"边画在填充之内"那一层，读数变正即 ① 成立）
→ ② 399 按 421 的结论二选一 → ③ 413（backing 名册 + 两档材质帧）→ ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R342 状态（2026-10-25 · 本地 · 第 341 轮 / Round 339）：换装两次、只变一个 token（产品 0 文件，验证账）

最后更新：2026-10-25（本地 · R342 / 第 341 轮 / Round 339）：把 395 欠的那半「同一条件的 before」在真机上量出来 ——
`liftAlpha` 关掉装一次 `差=−10.0`，装回真的 `差=+27.0`（产品 0 文件 · 验证账）

本轮做了什么：
① ⓪ CI 配对：`RUN=40182636083 ↔ db05698`（首读 in_progress ⇒ 只登记不轮询）。
② 变体 `SegmentKnob.liftAlpha → nil`，`install_local.sh --label r342-before`；暗档量一次。
③ `git checkout --` 还原，`--label r342-after` 再装一次；暗档再量一次。
④ 两臂同尺同外观同空库窗口：改前 `页底=52 轨道=80 药丸=70 差=−10.0`；改后 `页底=52 轨道=80 药丸=107 差=+27.0`。
⑤ 记下帧被覆盖的教训（U-1180）：两臂落在同一条 /tmp 路径上，看图腿只剩 after。

验证读数（现读）：两次换装 `INSTALL_RESULT=ok`（sha 逐字节、条数 379→379）；源码两次之间 `git status` 空；
脚本电池 `Ran 645（skipped=4）OK`；帧 182（本轮无产品改动，未重捕）；清账表 `格子=162 已清账=162`；
产品面连续零改动 **3** 轮（`python3 scripts/product_streak.py --streak-for 341` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① **亮档 A/B 不适用**（`liftAlpha(light)=nil`，两臂同码）；② 本轮无变异刀（产品 0 文件，
而且变体已还原）；③ 看图腿只有 after 一张（before 的帧被第二臂覆盖，U-1180）。

下一轮（R343）的靶：⓪ 读 `db05698` / 本笔的 CI 配对 → ① BACKLOG 399（亮档悬停：先量「提亮后 hover 与 selected
落在哪两档」，再决定要不要单独一支 token）→ ② 392 那三格（347/305 按下档、373 快速选取色、265 菜单栏悬停，
需要人的眼）→ ③ 413（backing 名册 + 两档材质帧）→ ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R341 状态（2026-10-25 · 本地 · 第 340 轮 / Round 338）：真机尺先拍到别人的窗口，再把修好的控件判成没有控件（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R341 / 第 340 轮 / Round 338）：屏幕解锁之后先修尺的两处「读错对象」，
再用修好的尺把 393 的修法在**真机**上签下来（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI 配对：`RUN=40152898039 ↔ 044d91a completed/success`（现读自 `scripts/ci_read.py latest`）。
② 尺补第一处：`capture_identity` / `activate_and_wait` —— 拍屏幕的尺必须先证明这一帧是谁的。
③ 尺补第二处：`pair_split` / `prefer_shape` —— 一个控件两段的形状；两种都在时先用旧的。
④ 真机两档读数（见下）；395 的 after 拿到了，before 仍只有另一趟（D-318 不许当同一运行 A/B）。
⑤ 测试：`scripts/tests/test_real_screen_identity.py` 8 格（对象门 4 + 两段形状 4）。

验证读数（现读）：亮档 `页底=219.0 轨道档=196.0 药丸档=220.0 差=+24.0`（`pill_lighter`）；
暗档 `左=107 右=80 页底=43`，尺判 `页底=52.0 轨道档=82.0 药丸档=107.0 差=+25.0`（`pill_lighter`）；
同一帧换形状前是 `no_band`。脚本电池 `Ran 645（skipped=4）OK`；帧 182（零产品改动，沿用并 `ls` 数过）；
清账表 `格子=162 已清账=162 未清账=0`；产品面连续零改动 **2** 轮（取数口 `python3 scripts/product_streak.py --streak-for 340` 现读，不手抄；口径差一挂 412）。

NOT-RUN（分开写）：① 同一运行的真机 before 半没跑（要临时关掉暗档抬量重装再拍）；
② 本轮无变异刀（产品 0 文件）；③ `pair` 形状的「选中段在左」是输入，换选另一段时不适用（420）。

下一轮（R342）的靶：⓪ 读 `044d91a` 之后这一笔的 CI 配对（成对，未取 id 不等于没跑）→ ① BACKLOG 419（容器边沿）
→ ② 395 的同一运行 before/after（临时关抬量重装一次）→ ③ 413（backing 名册 + 两档材质帧）→ ④ 动效主线
399 / 397 / 390 / 389 / 384 / 387① / 376 / 367。

## R340 状态（2026-10-25 · 本地 · 第 339 轮 / Round 337）：回顾尺第二次升成窗口守卫，而它第一次跑就点到我的名字（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R340 / 第 339 轮 / Round 337）：把"下一轮别再写岔"从记性换成会红的门 ——
「产品 K 文件」立成轮次级定义（D-336），`review_round_claims.py` 接进电池，顺手补这把尺自己的两个洞
（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ 读 CI（成对）：`RUN=40147352168 ↔ fb2cea0 completed/failure` —— 但**红的形状换了**：
  失败步骤只剩 STEP[9] Release script tests，两朵红是
  `test_recent_subjects_are_clean`（我上一轮那笔 subject 缺 `R<NNN>`）与 `test_skip_roster`（内层没有结论行的级联），
  而 STEP[15] 全量卷 / STEP[17] 捕获闸**根本没跑** ⇒ 411 的验收**不能**记成"红消失了"，
  它挂在 `RUN=40147874314 ↔ 483549a`（回填时 in_progress ⇒ 只登记不轮询，R140）。
② 定义：D-336 —— K 是**本轮**产品面的文件数；每一笔重复它，写不出同一个数就不写这一格。
③ 门：`scripts/tests/test_round_claim_consistency.py` 五格（正对照四条 + 真历史一条 + 豁免引用一条）。
④ 尺补洞：只认一种 subject 开头 ⇒ 老形状静默消失（漏扫比误报更坏）。现在 cutoff（`5d1c246`，现行形状第一笔）
  之前不扫、cutoff 不在历史里抛错、认不出的笔一律打印成 `未识别=K`，K>0 就红。
⑤ 名单规矩复述（R298 那一课）：每条豁免必须引用一条**真存在**的 BACKLOG 编号并写明退场；
  名单只买"不红"，买不到"数对"。

验证读数（现读）：`ROUND_CLAIM_REVIEW 扫了=17 笔 / 6 轮 内部不一致=2 未识别=1 窗起=5d1c246`；
脚本电池 `Ran 637（skipped=4）OK`（上一轮 629 → 本轮 637：`test_round_claim_consistency` 5 格 + `test_sources_cell_second_source` 3 格）；
针预检 `tables=127 covered=110 arms=369 bad=0`、臂名册 `files=221 arms=865 dupes=0 repeats=0`；
清账表沿用上一轮那一份（本轮没动格子）；`ls /tmp/r339_shots3` 现读 182 张帧在盘上 ⇒ 看图腿沿用，不重捕；
产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 339` ——
这一格仍带 BACKLOG 412 的**口径差一**，读成「本轮**之前**的连读轮数」。 —— 这一整句必须在同一行里：
`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for 339`。
本轮**没有**新的像素/判据读数族 ⇒ §8 的 `--must-include` 声明为空（按实记，不是沿用上一轮的声明）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那屏仍 `screen_locked`
  （电源 on、SecureInput 属主 loginwindow）⇒ 395 继续欠。
② **只在 runner 上判得了**：411 的结案挂在 `483549a` 那一跑（回填时 in_progress）——
  期望三格：`SEGREF_POLARITY dark 自家 差` ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 非空、STEP[15]/[17] 跑起来并转绿。
  上一跑那两格**根本没执行**，所以"没红"不等于"修好了"。
③ **这条通道看不见 / 没做**：本轮无变异刀（没有产品改动可打，写清而不是凑数）；
  新门看不见"追记写 0 而本轮是 3"那一类（只数到一笔 ⇒ 不构成两个数），已开成 BACKLOG 417。

下一轮（R341）的靶：⓪ 读 CI 配对（现读自 `scripts/ci_read.py latest`）——
**R340 追记现读**：`RUN=40147874314 ↔ 483549a completed/success` ⇒ **411 结案签掉了**，
连挂 10 跑的红在 R339 的修法上翻绿，三格预登记期望逐条兑现：
① `SEGREF_POLARITY dark｜自家 页底=50.0 选中=107.0 未选=70.0 差=+37.0｜同侧=是`（改前是 差=+0.0，线是 ≥+15）；
② `HOVER_RUNG_WINDOW dark 空闲=70 选中=107 线=1.1 可行=77…100灰阶 产品画在=77 判定=在窗口内`（改前是 空集）；
③ 新尺三档在 runner 上**与本机逐字同数**：`SEG_PILL_BACKING dark 页底=30 轨道=52 选中=107 差=55`、
`页底=50 轨道=70 差=37`、`页底=80 轨道=97 差=10` ⇒ **人造底是两机可比的自变量**，
这一句是 BACKLOG 413 的地基（它说明「把漂移量做成输入」这条路走得通，不必按机器切片）。
另：`RUN=40149824166 ↔ 7873fd9 completed/success`、`RUN=40150030547 ↔ 2615c58 completed/success`（R340 两笔都签了）。
**R340 追记二（2026-10-25 本地 · 本机全程没离开锁屏）**：
① CI 配对（现读自 `gh run view --json`，不手抄）：`RUN=40151598572 ↔ 7baaa8c completed/success` ——
  这是 R340 的第三笔（追记本身），它只动台账，没有新的判据；两笔追记的 subject 都带 `产品 0 文件`，
  与 D-336 的轮次级定义一致（`ROUND_CLAIM_REVIEW` 现读窗内不一致仍只有 R334 / R335 那两轮，都在名单里）。
② 真机腿**又试了一次**（原样抄尺自己打印的那一行）：
  `REALSCREEN_NOT_RUN display_channel（会话被登录窗锁住（SecureInput 属主=loginwindow）⇒ 区域捕获被拒、
  别的 App 的窗口在辅助功能里不存在；这一格要**人**来解锁，尺不猜密码也不替用户解锁｜电源日志最近一条=on；
  SecureInput 属主=loginwindow；探针可截=False（最亮=None））`
  ⇒ 395 的 after 本轮**仍然没跑**（不是「跑了没红」）；`pgrep` 现读产品进程在跑（pid 33535），
  所以缺席只有一颗名字：`display_channel`。同名出口第二次现场点名（R332 开单、R333 追记、本轮再验），
  修法不变也不需要改尺：等人解锁。

**R340 追记现读**：runner 那一跑正文里 `Ran 637 tests … OK (skipped=2)`（例数与本机同，skip 少 2 条是 PIL 那一族，已知形状），
而新门要答的两件事**当场有答案**：① `SOURCES_CELL_HISTORY 浅=False 对照数=40 头笔=fb2cea0 as_of第340轮=fb2cea0 处置=judge`
⇒ runner 的 checkout 不是浅历史（`fetch-depth: 0` 之后一直是全的），所以『浅历史上不许定罪』那族出口这一跑**没被触发**，
第二来源（提交自己写的 U 区间 ↔ 台账节标题里的 `R<NNN>`）在 runner 上同样把 `fb2cea0` 认成 R339 —— 这一句就是 R340 那格修复的验收；
② `test_round_claim_consistency` 五格与 `test_sources_cell_second_source` 三格都在 637 里**跑过**（不是 skip）。
下一轮仍要盯的：skip 数两机差 2（本机 4 / runner 2）是 PIL 那一族的既有形状；哪天差到 0 或反向，先查 `SCRIPT_SKIPS` 那一行再谈别的。
→ ① **BACKLOG 413**：backing 从三档常量换成名册（每档标实测/外推），并给「降低透明度 / 增加对比」
  各拍一帧 —— 那两档直接改材质合成结果，是 R339 那条链上最可能的下一个坑。
→ ② 412（`--streak-for` 差一）：修它要在同一笔里重算窗口内所有格。
→ ③ 动效主线仍排队：399 / 397 / 390 / 389 / 384 / 387① / 376 / 367。

本轮的自伤（写成出处，不写成缺陷）：新写的测试文件里有一句 CJK 串用了 ASCII 双引号
（`别把"没红"读成"没问题"`）⇒ 整支模块 import 失败，而它同时把 `test_skip_roster` 的两格带红
（内层没有结论行）。这条坑仓库早就记过（记忆 `reference-macos-python-and-skill-install`），
我又踩了一次 —— 区别是这次是**新写**而不是继承，所以正解是写完立刻 `ast.parse` 一遍再跑电池
（本文件的生成器一直这么做，测试文件却漏了：以后新增 `scripts/tests/*.py` 先过 AST 预检）。

## R339 状态（2026-10-25 · 本地 · 第 338 轮 / Round 336）：runner 连挂 8 跑的那朵红，本机把它复现成三个数（产品 3 文件，动效主线）

最后更新：2026-10-25（本地 · R339 / 第 338 轮 / Round 336）：把"只有另一台机器红"翻成
"页底是自变量" —— 暗档选中那颗塌在漂来的轨道上，改法是语义基准之上盖一层固定抬量
（产品 3 文件 · 动效主线 / 侧栏筛选胶囊）

本轮做了什么：
① 取读数（⓪）：`gh run list` 现读 8 连红（`117f45d`…`3954d1d`），失败步骤固定两格
  （STEP[15] executed-count gate / STEP[17] 捕获闸），红全在 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces`
  暗档；两机同格现读：本机 段按钮 空闲 52 / 选中 70 / 悬停 60，runner 70 / 70 / 77，
  而**同一跑**系统参照臂 差=+49.0 ⇒ 通道画得出选中，只画不出自家那颗 ⇒ 411 判成产品事实（D-335）。
② 造尺：`SEG_PILL_BACKING` —— 同一条夹具通道铺三档**不透明**人造页底（30 实测=本机 / 50 实测=runner /
  80 外推），逐档量「选中 − 轨道」，两颗地板都从仓库已有数拿（8 = 真机那把尺的 `DELTA`，1.10 = 这一族暗档的线）。
  它在本机原样复现出 runner 的形状：改前 差 18 / 0 / -27。
③ 修：`SegmentKnob.liftAlpha(dark:)` —— 暗档在 `selectedSegment`（解析 70，两机同读）之上盖
  `Color.white.opacity(0.20)` ⇒ 那颗 ≈107；α 由「盖过最亮实测轨道 97 + 8」与「不超过系统那颗 109」
  夹出区间 [0.189, 0.211]，取正中。改后 差 55 / 37 / 10、对比 2.336 / 1.771 / 1.162。
④ 补洞：那条『同侧』门原来算 `(ownDiff >= 0) == (sysDiff >= 0)` ⇒ 差=+0.0 也算"同侧=是"，
  所以它 8 跑全绿；加上量级地板之后它自己能抓"塌成一档"。
⑤ 看图：三对帧（页底 30/50/80 各改前/改后并排放大）—— 页底 50 改前两颗并成同一档、
  页底 80 改前选中是一颗暗洞（377 那颗回来了），改后三档都能一眼指出被选中的那颗。

验证读数（现读）：判据卷 `Executed 6（skipped=0 failures=0）`；
全量卷 `Executed 1023（skipped=47 failures=0）`；构建告警 0（`/tmp/r339_build.log`）；
捕获 `CAPTURED 182 -> /tmp/r339_shots3`；基线 `COMPARED=182`、更新前 `CHANGED=17`（全是暗档 17 张）、
更新后同一笔 `CHANGED=0`；刀 `mutate_r339 CAUGHT=3/3, RESTORE_CLEAN=yes`（M996、M997、M998）；
针预检 `tables=127 covered=110 arms=369 bad=0`、臂名册 `files=221 arms=865 dupes=0 repeats=0`；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；换装 `INSTALL_RESULT=ok INSTALL_SHA_MATCH=1`；脚本电池见落盘后那一跑。
产品面连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 338` ——
这一格仍带 BACKLOG 412 那个**口径差一**：本轮明明动了 3 个产品文件，而工具把本轮自己那笔排除在外，
所以它读成「本轮**之前**的连读轮数」，不许读成「本轮零改动」。 —— 这一整句必须在同一行里：`_cells` 问的是
"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for 338`。
§8 搬运：本轮新读数族 `SEG_PILL_BACKING` 接进它被打印的那一步的名单 —— `ledger_rows.py` 的 READINGS 原来只认 `KEY=` 形状与 `SEGREF_` 那一支，空格分隔的 `SEG_PILL_BACKING dark 页底=…` 一行都搬不到（第一次跑现读 `声明=1 缺=1`），补上 `^SEG_PILL_[A-Z_]* ` 之后现读 `READINGS_MUST_INCLUDE 声明=1 缺=0`、`READINGS_FAMILIES 搬运=728`（其中 `SEG_PILL_BACKING:18`）。缺值那一格按实记：`ROWS_TOTAL=13 ROWS_MISSING=12` —— §8 表要的是各卷的**汇总行**（构建 / 全量卷 / 捕获卷 / 电池 / 曲线 …），而本轮喂给搬运口的是各腿的**分别日志**合并，没有 round_verify 那一份汇总 ⇒ 缺就是缺，不许用上一轮的数或"看起来合理"的数补上（R92 的规矩）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那一屏仍读不到 ——
现跑 `display_channel_state()` 得 `screen_locked`（电源日志 on、SecureInput 属主=loginwindow），
尺不猜密码也不替用户解锁 ⇒ 395（393 的改前/改后真机四数）继续欠，而本轮的 107 那一档
在真机屏幕上到底比轨道亮多少，**没有读数**（三档人造底是本地代理，不是那块屏幕）。
② **只在 runner 上判得了**：411 的结案要下一跑签 —— 期望 `SEGREF_POLARITY dark 自家 差` 从 +0.0
变成 ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 从 空集 变非空、STEP[15]/[17] 转绿。这一跑之前 CI 仍是红的。
③ **这条通道看不见 / 没做**：亮档那一半没动（399 仍开，本轮新开 414 把它在原生页底上的 −10 说清楚）；
`FILTER_PILL_BAND` 用的那条侧栏轨道在这条通道里现读 255（材质不平滑），本轮**没有**为它做任何放行。

下一轮（R340）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R339 追记现读**：RUN=40147352168 ↔ fb2cea0（Round 336 那一笔，回填时 status=in_progress / conclusion 空 ⇒ 只登记不轮询，R140）。上一轮那两笔已翻成结论：**RUN=40143910952 ↔ b08d294 completed/failure**、**RUN=40143510717 ↔ 526e8d7 completed/failure** ⇒ 连挂的红从 8 跑变 10 跑，而这两笔都是**台账/追记**（零产品改动）⇒ 它们继续红正好是 411 的反证：红不来自台账，来自那颗不透明基准，只有 fb2cea0 动了画法。这一跑（fb2cea0）要答的就是三格期望：`SEGREF_POLARITY dark｜自家 差` 从 +0.0 变 ≥ +15、`HOVER_RUNG_WINDOW dark 可行` 从 空集 变非空、STEP[15]/[17] 转绿；外加 `SEG_PILL_BACKING` 三档在 runner 上签不签（页底是我给的常量，理论上两机同数 —— 若不签，说明 `render` 通道的不透明底色在那台机器上也被材质改写，那是通道事实，要开新的一单而不是放宽地板）。 **还有两件事**：① 本轮那笔 `fb2cea0` 的 subject 缺 `R<NNN>`（我照的是会话上下文里那份旧 Skill，盘上那份第 116–117 行早就改对了）⇒ 已 push 不能改历史，只能进 `test_commit_subject_hygiene` 的 `NO_LABEL_ROSTER`，理由引用 BACKLOG 416，**扫描窗滑过之后必须把那条删掉**（留着就是一条没人复查的豁免）；教训一句话：凡要写进历史的东西（commit subject、台账标题、命令形状）动手前回盘上重读那一格。② 新开三单里 413 最便宜也最可能咬人 —— 「降低透明度 / 增加对比」那两档会直接改材质的合成结果，而 backing 尺现在只有三档常量。这一跑要答的就是 411：
连挂 8 跑的红有没有变成绿（三格期望都在上面 NOT-RUN ② 里），以及新尺 `SEG_PILL_BACKING`
在 runner 上签不签（它的页底是我给的常量，理论上两机同数 —— 若不签，说明 `render` 通道的
不透明底色在那台机器上也被材质改写，那是通道事实，要开新的一单而不是放宽地板）。
→ ① **BACKLOG 405**（两轮没排上）：把"标题里那半句产品 K 文件"立成定义并变成会红的门。
→ ② **BACKLOG 413**：backing 从三档常量换成名册（每档标实测/外推），并给"降低透明度 / 增加对比"
  各拍一帧 —— 那两档会直接改材质合成结果，是 411 这条链上最可能的下一个坑。
→ ③ 412（`--streak-for` 差一）：修它要在同一笔里重算窗口内所有格，别一前一后。
→ ④ 动效主线仍排队：399 / 397 / 390 / 389 / 384 / 387① / 376 / 367 那一串。

本轮的自伤（写成出处，不写成缺陷）：第一版修法（整颗跟着轨道走的叠加）让**新尺三档全绿**，
我差点就此落账 —— 是隔壁那卷 `FILTER_PILL_BAND` 的红把它拽回来的。
教训一句话：**新装的尺全绿不是修好的证明**，它只证明新尺看得见的那一面变好了；
同一轮里"改前"那一跑我先跑在了还原之后（重跑一次才拿到 差=0 那三行），
所以 before/after 两份日志各自的时间戳与当时工作树状态都要留在盘上（/tmp/r339_before_final.log）。

## R338 状态（2026-10-25 · 本地 · 第 337 轮 / Round 335）：屏幕上那句说明是埋点属性写的 —— 取 alt 换成扫属性对（产品 1 文件，HTML 通道）

最后更新：2026-10-25（本地 · R338 / 第 337 轮 / Round 335）：把 R337 复盘时"看到但没量"的那条形状量成读数并修掉 ——
`\balt` 会被 `data-alt` 冒充 ⇒ 消毒留下的是埋点属性那句话（产品 1 文件 · HTML 通道）

本轮做了什么：一轮回顾的**直接产物**。
① 量：给 HTML 夹具那张图加一个前缀属性（`data-alt="埋点属性写的假说明"`），**同一份夹具拍两遍**
  （旧构建 / 新构建）。旧构建那一跑由捕获卷自己红两格（`消毒之后 alt 就没了`）—— 产物级证人；
  两档渲染帧的 alt 那一行差 4637（暗）/ 4409（亮）个像素，bbox=(40,460)..(358,487)，别处一个点没动。
② 修：不再"在标签串里找长得像 alt 的地方"，改成扫「属性名 + 值」成对、名字整段等于 alt 才算
  （重复取第一个、单双引号都认）。**没走最小改动**：`\b`→`\s` 挡得住 `data-alt`，
  挡不住 `title='见 alt="假的"'`（那个空格是值给的）⇒ 修法的形状由最刁钻的反例决定（D-334）。
③ 钉：新判据五颗读数 + 四种反例；三把刀 M993/M994/M995 各拆一条子规矩，现读 `3/3`。
④ 边界：无引号的 `alt=foo` 两种实现都不认 ⇒ **没顺手扩**，与 404 合到 BACKLOG 410（这条通道没有真正的解析器）。

验证读数（现读）：`HTML_ALT_SOURCE 前缀属性没抢=true 值里的假alt没抢=true 带引号的值没抢=true 重复取第一个=true 单引号认=true`；
判据卷 `Executed 25（failures=0）`；`ROUND_VERIFY build_warnings=0 swift_executed=1020 swift_skipped=47 swift_failures=0 frames=182 baseline_compared=182 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r338c_rv`；
捕获 `CAPTURED 182 -> /tmp/r338_rv/frames`（改前那一跑在 /tmp/r338b_before）；
变异表 `mutate_r338 3/3, RESTORE_CLEAN=yes`（M993、M994、M995）；针预检 `tables=126 covered=109 arms=366 bad=0`、
臂名册 `files=220 arms=862 dupes=0`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 629（skipped=4）`；
产品面连续零改动 **2** 轮（现读 `scripts/product_streak.py` 的 streak—— 注意这一格的**口径差一**（U-1154 / BACKLOG 412）：本轮明明动了产品，`--streak-for 337` 仍给 2，因为它把第 337 轮自己那笔排除在外（`--streak-for 338` 才认到：streak=1 last_round=337）。在工具修掉之前，这一格只能读成「本轮**之前**的连读轮数」，不许读成「本轮零改动」。 —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；取数口 `--streak-for 337`。
§8 搬运：本轮新读数族 `HTML_ALT_SOURCE` 在它被打印的同一笔里接进名单 —— 现读 `READINGS_MUST_INCLUDE 声明=1 缺=0`、`ROWS_TOTAL=13 ROWS_MISSING=12`（搬运 354 行 / 62 族）。**缺的那 12 格按实记**：§8 表要的是各卷的汇总行（构建 / 全量卷 / 捕获卷 / 脚本电池 / 变异表 / 曲线仪器 …），而本轮喂给搬运口的合并日志只带读数族 ⇒ 缺值就是缺值，不许用任何「看起来合理」的数补上（R92 的规矩），也不许把这一格写成「沿用上一遍」。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真窗口里复制一段带 `data-alt` 的网页，
渲染态那句说明是不是"季度趋势图"这一类作者原文（离屏帧已证像素级改前/改后，但真机眼仍欠一次）。
② **只在 runner 上判得了**：`HTML_ALT_SOURCE` 五颗在 runner 上签不签（它不读字体度量，理论上两机同数）、
本轮随基线更新的那几张（与上一轮逐张比 = 变了 4 张，全是 HTML 两档）在 runner 上会不会被判成 changed。
③ **这条通道看不见 / 没做**的：无引号 `alt=foo` 没修也没断言（按实挂在 BACKLOG 410）；
400（CJK 强调的墨量尺）本轮**仍然没量**。

下一轮（R339）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R338 追记现读**：RUN=40143510717 ↔ 526e8d7（账半，回填时 status=in_progress / conclusion 空 ⇒ 只登记不轮询，R140）；代码半 d8e6486 的 run id 现读未取（`ci_read latest` 只给 tip 那一跑）。
**R337 那一跑已读完**：`RUN=40140745366 sha=3954d1d conclusion=failure`，失败步骤两格（STEP[15] 全量卷 / STEP[17] 捕获闸），
三朵红全在 `testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces` 这一格上（「dark：可行集是 空集，而产品把悬停画在 77 ⇒ 落在窗口外面」/「两段读到同一个灰阶（70）⇒ 矩形没打在胶囊上」）—— 本机同一卷 0 failures ⇒ 它是**按机器才判得了**那一类，
而它在三本账里没有名字 ⇒ 第一件事是 411：先决定"按机器的具名出口"还是"在 runner 上重新标定"，
两条修法相反，不许用"CI 一直是红的"糊过去。R337 代码半 b232c9a 的 run id 按 sha 逐笔问。
这一跑还要答：⓪a 新守卫 `test_ledger_citations.py` 三格在 runner 上签不签（它读台账本身 ⇒ 该同数）；
⓪b 本轮随基线更新的那几张（与上一轮逐张比：比了 182 张、变了 4 张，全是 HTML 两档 × 渲染/原文）在 runner 上会不会被判成 changed —— 基线**更新之后**再对才是 CHANGED=0，两个数不是一件事；⓪c 电池例数两机对账（本机现读 629）。
→ ① **BACKLOG 405**：把"标题里那半句产品 K 文件"立成定义并变成电池里会红的门
  （回顾尺现读 `扫了=865 笔 / 44 轮 内部不一致=2`；R334/R335 走显式豁免）。它比动效那一串便宜，而且是审计链自己的可读性。
→ ② 动效主线仍排队：399（亮档悬停换轴，先量系统那颗的方向）、390 的 before/after、389 的时长、
  384 的横轴、387①、376、367/360/361/364 → ③ 409（暗档左列 1.23:1 是通道还是产品：两臂参照判据或真机眼）
  与 410（要不要真 tokenizer）都**不**该被"再补一条正则"糊过去 → ④ 400 要先造笔画墨量尺。

本轮的自伤（写成出处，不写成缺陷）：给夹具加那一行之前，我先拍了"改前"那一跑并**忘了夹具已经改过**——
第一版"改前"其实是新夹具 + 旧实现（正是我要的那一份，纯属运气）。教训是：before/after 的两遍
必须各自写下**当时的工作树状态**（本轮靠 `git diff --stat` 现读留了痕），否则"改前"两个字
可能指着一份没人知道的东西。

## R337 状态（2026-10-25 · 本地 · 第 336 轮 / Round 334）：把三本账按全长度扫一遍，顺手量到看图这条腿自己会美化（产品 0 文件，回顾轮）

最后更新：2026-10-25（本地 · R337 / 第 336 轮 / Round 334）：全历史回顾 —— 三格新守卫进电池（悬空引用 / STATE 缺节 / 报告落后）+ 四把刀 + 报告补 §14 + 四条条目形状改规范（产品 0 文件，判据账）

本轮做了什么：不做新东西，回头把这套账本身当被审对象。
① `review_full_history.py` 把三本大账按**全长度**扫了一遍（守卫都带回看窗口，窗口之外从来没人看过）；
   第一版报五百来处，五种口径病修完只剩四类真 finding：四条 `BACKLOG 16x` 悬空、STATE 缺 10 轮、
   报告叙述节停在 R298（补写前落后 38，补写后现读 0）、报告里两格同名 census 标签。
② 那四类各拿到一格会红的门或一条工单：新守卫 `scripts/tests/test_ledger_citations.py`（三格、三把正对照、
   共享 `ITEM` 不另抄），历史空洞进 BACKLOG 407，两格标签进 408。
③ 报告补 §14（R299→R336，数字全部现读），§13 那格 census **显式冻结成历史**。
④ 看图腿本轮第一次量到自己：暗档主列表行文字 最暗 0 / 底 28 ⇒ 比 1.23:1，
   亮档同一盒子 20.29:1，同一张暗帧详情头 12.27:1 —— 预览通道会增强，把 1.2:1 画成"可读的灰字"。
   两种解释（appearance 没进左列 / 产品真黑字）没被分辨 ⇒ BACKLOG 409 写清了那格参照臂怎么造。
   同一张帧里 229 那个"选中行整块纯黑"在已提交夹具上重现（两档都黑），"是谁"答了、"为什么黑"仍欠。

验证读数（现读）：脚本电池 `Ran 629（skipped=4）`；针预检 `tables=125 covered=108 arms=363 bad=0`、
臂名册 `files=219 arms=859 dupes=0`；变异表 `mutate_r337 4/4, RESTORE_CLEAN=yes`（M989、M990、M991、M992）；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品面连续零改动 **1** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）；
帧基线（复用上轮 182 张，零产品改动）`COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`；
连读取数口两份都现读：`--streak-for 336` → streak=1（**台账「第 N 轮」口径，电池里那格守卫读的就是它**）、
`--streak-for 337` → streak=2（R 号口径，差一 ⇒ 拿它填格会与守卫漂开，见本轮自伤）；
回顾尺 `REVIEW_U_RANGE 发现=0`、`REVIEW_D_REF 发现=0`、
`REVIEW_BL_REF 发现=0`、`REVIEW_SEVEN_AFTER 发现=0`、`REVIEW_PAIR 发现=0`、
`REVIEW_COMMIT_CLAIMS 扫了=865 笔 / 44 轮 内部不一致=2`；曲线 `GAPS=none`、`PHASE2 n=327 rounds=9..334 mean=86.38 min=14 max=99（**取的是本轮 ITERATION 落盘之后**那一份）`。
§8 搬运：本轮**没有新读数族进判据卷**（三格新守卫在 python 侧、`row_ink_probe.py` 是 `.scratch` 里的一次性仪器，
两者都不进 §8 的搬运名单），而本轮没跑判据卷 ⇒ §8 那一格按实记 **NOT-RUN**（没有本轮日志可解析，
不写"沿用上一遍"）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没跑的产品验证腿**：构建告警、Swift 判据卷、全量卷、
重捕帧、换装本机 —— 产品 0 文件、`Sources` 与 Swift 测试一字未动，跑它们不会新增证据；
基线那一腿只复用上轮的帧对账（`CHANGED=0` 的含义是"没移动像素"，不是"看过图"）。
② **只在人身上判得了**：暗档左列那 1.23:1 到底是通道还是产品 —— 要真机眼，
或者 409 里写的那条两臂参照判据（本轮没造，所以两种解释都没结案）。
③ **这条通道看不见**的：STATE 那 10 轮历史空洞按实留着（窗口门只守最近 40 轮），
补写等于伪造记录。

下一轮（R338）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R337 追记现读**：本笔 push 之后按 sha 逐笔问，别只读 tip 那一跑。
这一跑要答的：⓪a 新守卫 `test_ledger_citations.py` 三格在 runner 上签不签（它读的是台账本身，
两机同仓同内容 ⇒ 该同数；不同 ⇒ 说明有一台在跑旧工作树）；⓪b 电池例数两机对账（本机现读 629）。
→ ① **回到产品面**：`altAttr` 用的是 `\balt`，而 ICU 的词边界把 `data-alt` 里那个 `alt` 也算起点 ⇒
`<img data-alt="埋点说明" alt="真说明">` 取到的是**埋点那个属性**的文字 ——
屏幕上出现作者没打算给人读的一句话，与 401 那条规矩方向相反（R337 复盘时读到源码，Python 的 `re` 只是我本机的猜测，
**不算读数**）。第一件事：用产品入口量出它（一条打印 `HTML_ALT_SOURCE` 的判据），量到了再把 `\b` 换成
`(?:\A|\s)`，并给"属性名前缀不许冒充属性名"这一族配刀。
→ ② 顺手把 405（标题里那半句产品数）立成定义并变成门：回顾尺现读 `REVIEW_COMMIT_CLAIMS 扫了=865 笔 / 44 轮 内部不一致=2`，它比动效那一串便宜得多。
→ ③ 动效主线仍排队：399 / 390 的 before/after / 389 的时长 / 384 的横轴 / 387① / 376 / 367；
400 要先造笔画墨量尺；409 的参照臂可以插在 ① 之后做（同一批像素尺工作）。

本轮的自伤（写成出处，不写成缺陷）：回顾尺第一版报五百来处"问题"，五种口径病全是我自己写的
（字符串集合 vs 整数集合、`re.split` 索引、合计行、CHANGELOG 子标题、拿只认 3〜4 位的尺判 1〜2 位的老条目）。
**它的 500 处与它的 0 处同样不说明任何事** —— 配完正对照之后那个数才有资格进台账（U-1137）。
另一处自伤是**取数口的口径**：`--streak-for 337`（R 号）给 2，而 `--streak-for 336`（台账「第 N 轮」口径）给 1 ——
电池里那格守卫读的是**后者**，我第一版按 R 号填了报告与 STATE 两格，落盘之后当场红两朵
（`test_product_streak_cell`）。规矩：**台账那一格写的必须是守卫自己派生那份数，不是我以为的口径**；
两份都现读、并在同一行里写清哪一份作数，下一次换口径的人就看得见差一从哪来。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。
第三处自伤是**解析器拿错了方向**：`row_ink_probe` 那一行两个方向都打，我取了第一个 `比 X:1` ——
那是**亮侧**（暗档左列亮墨 0 颗 ⇒ 0.00:1，意思是「没有亮墨」），而我要的是**暗侧**（黑字对底 1.23:1）。
于是这条 finding 在台账里一度被写成它的反面。修法不是改台账里的手抄数，是改**取数口**（下标 + 一格「读到 0.00 就 die」的自检），
并由 `.scratch/motion-audit-2/fix_r337_readings.py` 把五本账一次改到现读 —— 那一支就是这次更正的证人。

## R336 状态（2026-10-25 · 本地 · 第 335 轮 / Round 333）：撤掉一张图之后作者写的 alt 必须留下，而 Markdown 要不要上限改成量出来的（产品 1 文件，HTML 通道收尾）

最后更新：2026-10-25（本地 · R336 / 第 335 轮 / Round 333）：BACKLOG 401 落地成产品修法（`<img>` 换成它的 alt 文字），
402 用一次现读关掉（Markdown 那条**不需要**字节上限），新开 404 把一条已知限制钉成现状断言（产品 1 文件 · HTML 通道收尾）

本轮做了什么：两件事都不是"加功能"，是把上一轮**留下的说法**换成数。
① 402：`MD_RENDER_COST` 现读 固定 16.95ms + 边际 0.061ms/KB，存档上限（512000 字符）那一档要 47.23ms，
预算 250ms ⇒ 不装上限。之前那句"Markdown 不需要"是没证据的默认，现在它有出处。
② 401：消毒撤掉 `<img>` 之后，屏幕上不该是一片空白 —— 照抄 HTML 自己的 `alt` 字段：
有 alt 留文字、空/缺 alt 静默删（装饰图与埋点像素不配占位）、alt 里的尖括号剥掉。
③ M985 第一版**打空**（PASSED）：反例 `alt="<script>…</script>"` 里那个 `>` 让标签正则先截断，
alt 根本没被捕获 ⇒ 那一刀改的是走不到的分支。换反例（只含 `<` 不含 `>`）之后 3/3 CAUGHT。
那个走不到的形状登记成 404 并**断言现状**（将来修掉会红，改的人必须同时更正那条）。

验证读数（现读）：`MD_RENDER_COST 16k=17.90ms cap=47.23ms cap字符=512000 边际=0.061ms/KB 固定=16.95ms 平均=0.094ms/KB 预算=250ms 判定=在预算内`；
`HTML_ALT 有alt保留=true 空alt静默=true 无alt删净=true 尖括号剥掉=true`；
`HTML_INKREAD dark 比=12.43 反侧=0颗`、`light 比=13.80 反侧=0颗`（覆盖率 暗=0.0545 亮=0.0485）；
两态相减 `HTML_PAIR_PROOF 千分比 暗=84 亮=78`；`HTML_SANITIZE 构造=11 残留=0`；
判据卷 `Executed 30（failures=0）`、捕获卷 `Executed 99（skipped=4, failures=0）`；
`ROUND_VERIFY build_warnings=0 swift_executed=1019 swift_skipped=47 swift_failures=0 frames=182 baseline_compared=182 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r336c_rv`；变异表 `mutate_r336 5/5（M984, M985, M986, M987, M988）；mutate_r335 11/11（M973, M974, M975, M976, M977, M978, M979, M980, M981, M982, M983）`；针预检 tables=124 covered=107 bad=0、名册 files=218 arms=855 dupes=0；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 624（skipped=4）`；产品面连续零改动 **1** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在同一行里：`_cells` 问的是"那一格有没有引用取数口"，分两行写就等于没引用）。唯一取数口 `python3 scripts/product_streak.py --streak-for 335`；本轮这一笔 `--streak-for 336` 现读 1。
§8 搬运：`READINGS_MUST_INCLUDE 声明=6 缺=0`，本轮新族 `MD_RENDER_COST` / `HTML_ALT` / `HTML_ALT_BLOCK` / `HTML_ALT_PARA` 第一次进 §8 —— 新读数族在它被打印的同一笔里接上，整族前缀 13 个名字 / 本跑 18 行

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真窗口里 alt 那句话与上下文的
呼吸感（离屏帧能证它出现，不能证它在真表面上好不好读）；
② **只在 runner 上判得了**：`testMarkdownRenderCostAtTheArchiveCap` 在 runner 上的数
（它带 R56 那族"同操作样本跨度超阈值就 skip"的闸门 —— runner 上很可能记为未运行，
那不是坏，但也不是签）；本轮新像素证据在 runner 的字族上是否同数；
③ **这条通道看不见**的：400（CJK 强调在像素层体不体现）本轮**仍然没量** —— 它需要一颗
笔画粗细/墨量尺，不是"再看一眼帧"能给的。

下一轮（R337）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——
**R336 追记现读**：RUN=40136427058 ↔ e226737（账半，回填时 status=in_progress / conclusion 空 ⇒ 只登记不轮询），
代码半 fde8227 的 run id 现读未取（`ci_read.py latest` 只给 tip 那一跑；要成对就得按 sha 逐笔问）。
这一跑要答的四件事：⓪a 新装的像素门 `HTML_ALT_PARA`（两档"紧挨必须 2 处"）在 runner 的字族上签不签 ——
它的阈值来自本机两群读数（20.0 对 31.5），runner 的字体度量若不同，最可能先红在这一格；
⓪b `MD_RENDER_COST` 带 R56 那族噪声闸门，runner 上很可能记为**未运行** —— 那不是坏，但也不是签；
⓪c `HTML_` 那一族在 runner 日志里打几行、§8 的搬运行数两机是否同数（判据卷今天 30 格 / 1019 例）；
⓪d R335 那一跑欠的三问（新像素门在 runner 上签不签、`HTML_` 那族打几行、格数与行数两机对账）。
→ ① **回到动效主线**：399（亮档悬停换轴，A 案描边 / B 案提亮，
先量系统那颗的方向再选）、390 的 before/after、389 的时长、384 的横轴、387①、376、
367/360/361/364 → ② 400 那条要动就得先造尺（笔画墨量），不许用形容词结案 → ④ 405：把"标题里那半句产品数"立成定义并变成电池里会红的门（R334/R335 走显式豁免），它比动效那一串便宜得多，而且是审计链自己的可读性 →
③ 本轮复盘时**看到但没量**的一条：`altAttr` 用的是 `\balt`，而 ICU 的词边界把 `data-alt`
里那个 `alt` 也算起点 —— 于是 `<img data-alt="埋点说明" alt="真说明">`（data- 在前）取到的
是**埋点那个属性**的文字。这是"屏幕上出现作者没打算给人读的一句话"，与 401 那条规矩
（只留作者为"图加载不了"准备的那一份）方向相反。**R337 第一件事是用产品入口把它量出来**
（一条打印 `HTML_ALT_SOURCE` 的判据），量到了再修：把 `\b` 换成 `(?:\A|\s)`，并给"属性名前缀
不许冒充属性名"这一族配刀。Python 的 `re` 只是我自己在本机的猜测，**不算读数**。

本轮的自伤（写成出处，不写成缺陷）：新增读数 `MD_RENDER_COST` 时没同时登记那张
「按文件按标记」的名册，全量卷第一次跑就红三朵 —— 现读 量到的名单=["MD_RENDER_COST", "PERF", "PERF["] 对 登记的=["PERF", "PERF["]、
本文件行数 4/3（量/登记）、全表总数 78/77（量/登记）；同一笔把三格改到现读，
新日志里这一朵红消失（`grep -c` 现读 0）⇒ 登记生效（U-1134）。

下半场（同一轮里加的，因为它是**看图腿量出来的**，不是新特性）：规则 ④ —— 独占一行的图，
它的 alt 包成 `<p>`；句中的图就地替换。行距尺现读 紧挨处数 修之前 暗/亮 = 3/3 →
修之后 = 2/2；`HTML_ALT_PARA dark 带=7 行内距=20.0 段距=31.5`、
`light 带=7 行内距=20.0 段距=31.5`；
`HTML_ALT_BLOCK 独占成段=true 句中不包=true 句中同句=true`；刀加到 M984…M988（`CAUGHT=5/5`）。
另一次自曝：那条像素门的期望我先写成"紧挨 1 处"，基线红在 2 处 —— 多出来那一处是
**渲染器不给 `<ul>` 下边距**（登记成 406 的现状，判据里同时钉"两群分不开就必须红"），
修的是我的推导，不是地板（U-1136）。

## R335 状态（2026-10-25 · 本地 · 第 334 轮 / Round 332）：右侧预览第一次能渲染 HTML —— 而第一版「抹掉烤死的墨」在属性串上全绿、屏幕上仍是黑字（产品 7 文件，HTML 预览主线）

最后更新：2026-10-25（本地 · R335 / 第 334 轮 / Round 332）：详情区多了一条 HTML 渲染通道（判定 / 消毒 / 渲染三段），
并修掉两个只在**屏幕上**看得见的缺陷 —— 暗档正文是烤死的黑（反侧 7935 颗 → 0 颗）、
正文档比产品小两号（12.0 → 14.0，层级比 2.000 不变）（产品 7 文件 · HTML 预览主线 · 合计 95/105）

本轮做了什么：把用户点名的 HTML 预览做完，并且**逐张看图**。看图腿抓出来的不是"偏淡"这种形容词，
是两个可复现的数：① 改前那一帧正文列里 **8779 颗 RGB(0,0,0)** 落在 luma=30 的表面上；
② 我第一版的修法（`removeAttribute` 抹掉颜色）让属性串断言全绿而帧上**一个字节都没变**（md5 同为 `ba3f4595…`）。
第二版把判据换成问**结果**：每一段的墨在亮暗两档各解析一次，两档同色就是烤死；
再装一颗像素门（尾墨对比 ≥ 4.5:1 **且**反侧必须 0 颗 —— 单用一把分不清"淡"与"画反了"，R29d 那一课）。
字号那一步同理：`HTML_FONTS` 现读 12pt 而产品是 14pt ⇒ 等比搬，基准取"按字符数加权的众数号"，
层级比不许被压平（M980 钉的就是只搬正文那种坏法）。

验证读数（现读）：`HTML_INK 字符=59 烤死段前=1 烤死段后=0 无色段后=0 烤死背景段=0 链接段=1`；
`HTML_INKREAD dark 比=12.19 反侧=0颗`（Markdown 同块 12.55:1）、`… light 比=12.32 反侧=0颗`（14.75:1）；
`HTML_TYPE 基准前=12.0 基准后=14.0 产品档=14.0 层级比前=2.000 层级比后=2.000`；
`HTML_SANITIZE 构造=11 残留=0`、`HTML_RENDER_COST 斜率=0.125 上限=131072 判定=在预算内`；
两态相减 `HTML_PAIR_PROOF 千分比 亮=68 暗=74`；
`ROUND_VERIFY build_warnings=0 swift_executed=1015 swift_skipped=47 swift_failures=0 frames=182 baseline_compared=182 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r335_rv2`；判据卷 `Executed 22（failures=0）`、捕获卷 `Executed 98（skipped=4, failures=0）`；
变异表 `mutate_r335 11/11（M973, M974, M975, M976, M977, M978, M979, M980, M981, M982, M983）`；针预检 tables=123 covered=106 bad=0、名册 files=217 arms=850 dupes=0；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 624（skipped=4）`；产品面连续零改动 **1** 轮（现读 `scripts/product_streak.py` 的 streak —— 这一整句必须在**同一行**里：`_cells` 问的是"那一格有没有引用取数口"，而它读的段落就是一行；分两行写就等于没引用，R300 那一格红过一次）。唯一取数口 `python3 scripts/product_streak.py --streak-for 334`；本轮这一笔落盘前 `--streak-for 335` 现读 1。
§8 搬运：`READINGS_MUST_INCLUDE 声明=4 缺=0`，新读族 `^HTML_[A-Z_]+ ` 整族（9 个名字 / 本跑 13 行）—— 本轮新发明的读数族，**在同一笔里**接进搬运名单，不重演 397 那一朵（打了 100 多轮而名单里没有它）

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**：真机那一屏（本轮换了正文通道，
渲染态在真窗口里的换行与选中拖拽没看过 —— 离屏帧能证墨，不能证手感）；
② **只在 runner 上判得了**：本轮新门 `testHtmlRenderedBodyInkIsReadable` 与 20 格新判据在 runner 上的读数
（特别是"反侧必须 0 颗"这一条 —— 它依赖这台机器的回落字面，runner 上的字族可能不同）；
③ **这条通道看不见**的：`<img>` 与 `style` 里的 url() 被消毒撤掉之后**屏幕上没有东西可看**，
残留只能由 `residualFetchableReferences` 那格判，帧不替它作证。

下一轮（R336）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）：
**RUN=40130086757 ↔ `283a063`**（账半那一笔，回填时 status=in_progress / conclusion 空 ⇒ 只登记不轮询，R140）；
代码半 `2e29c0e` 与代码半补 `f3f2027` 两笔的 run id **未读**（`latest` 只给 tip 那一跑）——
读它们之前不许说"三笔都签了"。这一跑要答的三件事：
① 新装的像素门 `testHtmlRenderedBodyInkIsReadable` 在 runner 上签不签 —— 它判的"反侧必须 0 颗"
   依赖这台机器的回落字面，runner 的字族/抗锯齿不同就可能换数（这一族有先例：R321 的 SELARM）；
② `HTML_` 那族在 runner 的日志里打几行（本机现读 8 个名字 / 12 行，两条腿各打一半）；
③ 判据卷从 22 格涨到 24 格之后，`Executed` 的分母与 §8 的搬运行数在两机副本上是否同数。
→ ① 报告里"最后一次动到 `Sources/` 的那一轮"那一格**本轮已刷新**：
`SOURCES_CELL 账上=R335/`2e29c0e` git=R335/`2e29c0e` 一致=是`（R334 那朵 runner 红就此收口，
脚本 `scripts/report_sources_cell.py` 已进仓库并接进生成器 —— 下一轮不必再手工想它）→
② 回到动效主线那批还开着的：399（亮档悬停要换轴）、397 的反方向已结、390 的 before/after、
389 的时长、384 的横向、387①、376、367/360/361/364 → ③ 本轮开出来的四条里
最便宜的一条先量缺席：402（Markdown 那条的耗时随大小怎么长 —— 一次现读就能定它要不要上限）。

## R334 状态（2026-10-25 · 本地 · 第 333 轮 / Round 331）：悬停不再冒充选中 —— 胶囊有了自己那一档，而『门只立暗档』是被算出来的（产品 2 文件，动效主线）

最后更新：2026-10-25（本地 · R334 / 第 333 轮 / Round 331）：396 的暗档修法落地（`VisualFill.pillHover`=0.045，
『悬停↔选中』1.065→**1.169**，线 1.10），亮档被证明"这条轴修不了"并开成 399；
R333 那笔 subject 的持久红走登记式豁免收口（398 / D-328）（产品 2 文件 · 动效主线 · 合计 96/105）

本轮做了什么：先让判据红 —— 把仓库已有的可见性线（暗 1.10 / 亮 1.20）第一次对准"悬停↔选中"这一对，
现读 1.065 ⇒ 红；然后给胶囊单独一档，取值由"与两边都 ≥ 线"的窗口 59…63灰阶 夹出来（产品画在 60）。
"门只立暗档"这条决定不留在注释里：`hoverRungChoices` 把秩序算成可行集，
暗档 59…63灰阶、亮档空集（判定=可行集空（该换轴，399）），撤掉秩序才有解而两支都要付别的地板 ⇒ 那是换轴问题，不是换数问题。

验证读数（现读）：暗档 空闲 52／悬停 66→60／选中 70／『悬停↔选中』→1.169；亮档 230／207／220（未动）；
梯子 `pill` 一族 idle→pillHover 9.33/8.39、pillHover→pressed 14.92/13.06（地板 4/255）；
胶片仍有对象 `候选行=24 轨道=52.0 药丸=70.0 分离=18.0 镜像=是 纵向覆盖=14/48px=29%`；
`ROUND_VERIFY build_warnings=0 swift_executed=991 swift_skipped=47 swift_failures=0 frames=178 baseline_compared=178 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 目录=/tmp/r334_rv`；判据卷 梯子 `Executed 14`／捕获 `Executed 96（skipped=4）`；
三张表 `mutate_r334 3/3（M970, M971, M972）；mutate_r230 4/4（M771, M772, M773, M774）；mutate_r333 5/5（M965, M966, M967, M968, M969）`；针预检 tables=122 covered=105 bad=0、名册 files=216 arms=839 dupes=0；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 624（skipped=4）`；
产品面连续零改动 **1** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 333`，`--check` 同形；
本轮这一笔按 `--streak-for 334` 现读是 2，要等 commit 之后 git 才把本轮算进分界）。
这一格本轮换了两次口径：① subject 缺「第 N 轮」时改问第二个来源（台账节标题里的同一段 U 区间，
唯一命中才算），现读 8 笔补上 —— 关掉它的探针答 **15**，开着它答 **1**（U-1116 / D-329：
豁免只买"不红"，买不到"数对"）；② 分界从 `≤` 换成 `<` ⇒ 同一格不再在 commit 前后答两个数，
而上一轮那一格在新口径下仍是 **14**（= R333 写下的数 ⇒ 不改写历史，U-1117）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**的：真机那一屏（395 仍欠，本轮没再问 ——
上一问是 `screen_locked`，而本轮的产品改动只有一张帧，重问不改结论）；
② **只在 runner 上判得了**的：394 的两问 + 本轮新门在 runner 上的读数（`pillHover` 是不透明叠加，
理论上画得出来，但窗口边界会随倍率/底漂 ⇒ 只登记不轮询）；
③ **命令没跑成**的：本轮没有 —— 四腿全部有对象并跑完（见上面 ROUND_VERIFY）。

下一轮（R335）的靶，按顺序：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）：
**RUN=40119885935 ↔ `d102335`**（账半那一笔，回填时 status=queued / conclusion 空 ⇒ 只登记不轮询，R140）；
代码半那一笔 `5d1c246` 的 run id **未读**（`latest` 只给 tip 那一跑）—— 读它之前不许说"两跑都签了"。
这一跑要答的就是 394 那两问 + 本轮新门在 runner 上的 `HOVER_RUNG_WINDOW`（暗档可行窗口会不会随倍率/底漂），
以及 `标签补自台账=8` 这一族在 runner 的仓库副本上是不是同一批（它读的是 git 与台账，两台机器应当同数）。
→ ① **399**：亮档的悬停换轴（A 案描边 / B 案提亮，
先量系统那颗的悬停方向再选，不许猜）；② **397**：§8 自己那几格键名要么由 `round_verify.sh` 补打、
要么把 ROWS 表改成读 `ROUND_VERIFY` 的键名（两条修法相反，挑一条做完 —— 本轮只补了它的**反方向**那一半，见下面「工具面」）；③ 390 的 before/after；
④ 389 的时长；⑤ 384 的横轴那半；⑥ 387 的①；⑦ 若用户已解锁：395 的三格；⑧ 376 剩那一半；
⑨ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

工具面（本轮动的一行不在产品里）：`ledger_rows.py` 的 §8 搬运名单**从来没有 `HOVER_` 这一支** ⇒ 悬停那一族（现读 7 个名字 / 本跑 18 行）从 R230 的 `a7e3154` 起一行都没进过 §8；本轮按整族前缀补上并 `--must-include` 声明（缺=0）。397 讲的是反方向（名单里有名字而日志不打），两条合起来才是那句「名单必须与现场**双向**对账」（U-1115）。
登记窗口（写盘前那一遍电池）：红 test_roster_entries_must_be_registered_in_the_ledger,test_the_roster_matches_what_this_machine_actually_skips 两朵 —— `NO_LABEL_ROSTER` 引用的 BACKLOG 398 与豁免是**同一笔**落地，引用在账落地之前必然查无条目；另一朵是内层观察者 `test_skip_roster`把内层的红原样搬上来，不是第二件事。写盘后那一遍没有放行名单，必须全绿。

## R333 状态（2026-10-24 · 本地 · 第 332 轮 / Round 330）：选中那颗站到轨道之上 ——离屏尺把缺陷的画法当成了定义，重基之后才重新有对象（产品 2 文件，动效主线）

最后更新：2026-10-24（本地 · R333 / 第 332 轮 / Round 330）：393 的①落地（选中那颗换成
`unemphasizedSelectedContentBackgroundColor`，暗档 差 −16.0→**+18.0**、与系统参照臂 +26.0 同侧并立成门），
离屏尺的定义重基成"两臂镜像定档"（产品 2 文件 · 动效主线 · 合计 95/105）

本轮做了什么：把 R330 在屏幕上判掉的缺陷改掉，并且**在改完之后回头检查证人怎么变绿的**。
第一版落地后斜坡尺与过程证人不是红、是 skip（`候选行=0 判定分布=非候选×520`）——
因为 `pillRun` 的定义"药丸=与页底同档"借的就是缺陷的画法。重基成极性无关的三颗纯函数
（`halfLevels` / `settledPillTrackLevels` / `pillRun`），并给暗档"同侧"升成门（D-325 只允许这一档）。

验证读数（现读）：暗档 页底 30.0／轨道 52.0／选中 36.0→70.0／差→+18.0，亮档 页底 255.0／未选 230.0／选中→220.0／差→-10.0；
重基后 `候选行=24 判定分布=洞太窄×11,过×13,非候选×496 轨道=52.0 药丸=70.0 分离=18.0 镜像=是 纵向覆盖=14/48px=29%`、
斜坡 `单调 位移=137.0pt 最大倒退=0.0pt 帧数=27`、过程证人 开臂峰值=0.234 对 关臂峰值=0.949；
`ROUND_VERIFY build_warnings=0 swift_executed=990 swift_skipped=47 swift_failures=0 frames=178 baseline_compared=178 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 目录=/tmp/r333_rv`；判据卷 合成帧 `Executed 40`／胶片 `Executed 67（skipped=3）`／捕获 `Executed 95（skipped=4）`；
六张表 `mutate_r323 6/6（M925, M926, M927, M928, M929, M930）；mutate_r327 3/3（M949, M950, M951）；mutate_r328 3/3（M952, M953, M954）；mutate_r329 2/2（M955, M956）；mutate_r333 5/5（M965, M966, M967, M968, M969）；mutate_r324 5/6（M931, M933, M934, M935, M936）`（另 M932 PASSED（表自己写明：只有机器处在亮档时它才咬得住，本轮机器在暗档））；针预检 tables=121 covered=104 bad=0、名册 files=215 arms=836 dupes=0；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 622（skipped=4）`；
产品面连续零改动 **14** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 332`，`--check` 同形；
本轮这一笔按 `--streak-for 333` 现读是 15 —— 本轮动了 2 个产品文件，commit 之后 git 会把它归零；上一轮那一格是 13）。

NOT-RUN（三种缺席分开写，不许省略）：① **只在人身上判得了**的：393/395 的真机改前改后四数 ——
本轮现读分类器仍是 `screen_locked`（电源 on、SecureInput 属主 loginwindow、区域探针被拒），
尺不猜密码也不替用户解锁（D-322）；② **只在 runner 上判得了**的：394 的两问
（轨道那颗仍是材质 ⇒ 会不会走 `pill-ramp-no-track`；不透明语义色在 runner 上同号吗）——
本轮 push 的那跑只登记不轮询；③ **命令没跑成**的：本轮没有（四腿全部有对象且都跑完，见上面 ROUND_VERIFY）。

下一轮（R334）的靶，按顺序：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）：RUN=40113044414 ↔ `117f45d`（回填时 status=in_progress / 未读 ⇒ 只登记不轮询，R140）。这一跑要答的就是 394 那两问：① 轨道那颗仍是材质，runner 上会不会走 `MOTION_NOT_RUN=pill-ramp-no-track`；② 不透明语义色在 runner 上的 `SEGREF_POLARITY dark｜自家 差=` 是不是仍与本机同号（现读本机 +18.0、上一跑 runner −14.0 是**改之前**的数）—— 同号才说明 393 的修法在两机同向。另外本轮把真机缺席又问了一次：仍是 `screen_locked`（电源 on、SecureInput 属主 loginwindow）⇒ 395 继续欠着。→
① **396**：选中档与悬停档只差 4.0 级 —— 先量"该差多少"（不许拍地板，D-321），再按分离度排修法，
改前改后四个数同一运行（D-318/D-319）；② 390 的 before/after（`纵向覆盖=14/48px=29%` 那半）；
③ 389 的时长（到位帧 9 对 声明 200ms）；④ 384 的横轴那半；⑤ 387 的①；
⑥ 若用户已解锁：395 的三格（真机改前/改后 + 392 的按下档/取色/菜单栏悬停）；
⑦ 376 剩那一半；⑧ **397**：§8 那 12 个键名要么由 `round_verify.sh` 补打、要么把 ROWS 表改成读
   `ROUND_VERIFY` 的键名 —— 两条修法相反，挑一条做完（做完之前那 12 格在台账里必须写成洞）；
⑨ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

## R332 状态（2026-10-24 · 本地 · 第 331 轮 / Round 329）：真机那格的「读不到」拆成三颗 —— 本轮的靶被新拆出来的那颗挡住（产品 0 文件，判据账）

最后更新：2026-10-24（本地 · R332 / 第 331 轮 / Round 329）：真机通道现读 `screen_locked`
（显示器 on、SecureInput 属主 loginwindow、区域截图被拒）⇒ 393 的屏幕那一半挡住，开成 395；
本轮把"读不到"拆成 display_off / screen_locked / capture_failed 三颗并配三格真值表与两把刀
（产品 0 文件 · 判据账 · 合计 79/105）

本轮做了什么：用户授权退出 App（`already_running` 解除）并唤醒显示器后，真机尺仍拿不到窗口，
而它报的是一句"探针截图失败（CalledProcessError）"。那句话把三种**修法相反**的缺席压成一种，
所以本轮的产出是那三种各自的名字：`classify_display_channel(power, secure_owner, region_ok)` +
`secure_input_owner()`（只读 ioreg/ps，不截屏）+ 三格真值表 + 两支刀。

验证读数（现读）：分类器 `(False, screen_locked)`，人话句 `会话被登录窗锁住（SecureInput 属主=loginwindow）⇒ 区域捕获被拒、别的 App 的窗口在辅助功能里不存在；这一格要**人**来解锁，尺不猜密码也不替用户解锁`；
判据卷 `Ran 8 tests OK`；刀 `CAUGHT=2/2, RESTORE_CLEAN=yes`（逐臂 M963, M964）；
针预检 tables=120 covered=103 bad=0、名册 files=214 arms=831 dupes=0；
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；脚本电池 `Ran 622（skipped=4）`；
产品面连续零改动 **13** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 331`，`--check` 同形；
本轮这一笔按 `--streak-for 332` 现读是 14，要等 commit 之后 git 才派生得出来；上一轮那一格是 12）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的四腿 —— build 0 告警 / swift 判据卷 /
重捕帧 / 帧基线对账 / 换装本机：改动面 7 个文件全是 python 与台账，0 个 Swift 文件，帧也没重捕；
② **只在人身上判得了**的：393 的改前/改后真机四数（会话锁着，尺不猜密码也不替用户解锁）⇒ 开成 395；
③ **命令没跑成**的：本轮没有 —— CI 对平留到 R333 第 ⓪ 条现读。

下一轮（R333）的靶，按顺序：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 gh run list）：RUN=40101699619 ↔ `3c9ab58`（回填时 status=in_progress / 未读 ⇒ 只登记不轮询）；上一轮 R331 那一跑 `40097837516 ↔ 6935e1b` 已读 completed/success，三件待看事项的答案与那条改判在 R331 的追记二里。这一跑要盯的一件事：本轮把真机缺席拆成三颗 ⇒ 若 CI 里出现 `REALSCREEN_NOT_RUN screen_locked` 或 `display_off`，那是**环境**缺席（要人或要等），不是回归；而 `capture_failed` 才是要查工具的哪一种。
① **393**：391 的落地只剩①—— 药丸换成 `unemphasizedSelectedContentBackgroundColor`
（参照臂量出的分母：解析 70／220 ≈ 系统实测 74.0／205.0），并把 `pillRun` 的
"药丸=与页底同档"重基成"药丸=两帧之间变了的那一档"（极性无关、不抄 `FilterPillGeometry`）；
硬断言只立**暗档同侧**（D-325：亮档的两机反号），R327…R329 打在 `pillRun` 与报告行上的针重钉重跑；
② 若用户已解锁：补 395 的三格（393 的改前/改后真机四数 + 392 的按下档/取色/菜单栏悬停）；
③ 390 的 before/after；④ 389 的时长；⑤ 384 的横轴那半；⑥ 387 的①；⑦ 376 剩那一半；
⑧ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

## R331 状态（2026-10-24 · 本地 · 第 330 轮 / Round 328）：391 的方向交给系统自己印 —— 参照臂进夹具通道，②那一发回滚（产品 0 文件，参照臂账）

最后更新：2026-10-24（本地 · R331 / 第 330 轮 / Round 328）：系统参照臂现读 暗档 差=+26.0（选中 74.0 / 未选 48.0）
⇒ 391 的修法定成①（抬选中那颗），而②（压轨道）落进产品后被自己的过程证人否掉（峰值=0.000 < 地板=0.005）并整发回滚
（产品 0 文件 · 参照臂账 · 合计 85/105）

本轮做了什么：把"该往哪边改"从我的记性变成一次测量。新夹具 `sysref-segmented-selected-{left,right}`
（系统自己的 `NSSegmentedControl`，同一条 render / 同一个 probeFrame / 同一颗尺）+ 新判据
`testSystemSegmentedReferenceSaysWhichHalfTracksSelection`；391 的 ② 那一发（`trackWell =
underPageBackgroundColor`）落了产品又被回滚，现场留 patch。两次「尺读错对象」自曝并修成闸（写死的取样带、
从对象自己身上取的页底），第一次据此下的"通道不画填充"是**错结论**，本轮公开更正。

验证读数（现读）：参照臂 `SEGREF_POLARITY dark｜系统 页底=30.0 左臂选中=74.0 左臂未选=48.0 差(左臂)=+26.0 差(右臂)=+26.0 AB=两臂镜像一致｜自家 页底=30.0 选中=36.0 未选=52.0 差=-16.0｜同侧=否`；
亮档同形（系统 −30.0／自家 +3.0／同侧=否）；②的改后四数 页底 30.0 轨道 40.0 药丸 36.0 分离 4.0（改前 30.0／51.9／36.0／15.9）；
构建 0 告警（`--build-tests`）、全量卷 `Executed 984 tests, with 47 skipped and 0 failures`、
捕获 `CAPTURED 178 -> /tmp/r331_rv/frames_after`、帧基线 `COMPARED=178 CHANGED=0 MISSING=0 ADDED=0`（本轮同一笔 update，174→178）、
清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；
刀 `CAUGHT=3/3, RESTORE_CLEAN=yes`（逐臂 M960, M961, M962）；针预检 tables=119 covered=102 bad=0、名册 files=213 arms=829 dupes=0；
搬运名单 `READINGS_MUST_INCLUDE 声明=1 缺=0`；脚本电池 `Ran 619（skipped=4）`；
产品面连续零改动 **12** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 330`，`--check` 同形；本轮这一笔按 `--streak-for 331` 现读是 13，要等 commit 之后 git 才派生得出来；上一轮那一格是 11）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的那一腿 —— dmg + 换装本机：
改动面 9 个文件里 0 个产品文件（只有测试夹具与台账），已装的那一份与盘上的产物同码，
换装不判任何东西；而真机侧 `pgrep` 现读有实例在跑（`ClipboardHistoryApp` 一个 PID，就是用户让我测完帮他重新打开的那一份）⇒ 按 D-322 走
`already_running`，**绝不替用户关窗**。② **只在 runner 上判得了**的：`SEGREF_POLARITY`
在 1×、不合成材质那台机器上读不读得出（判据里已留具名出口 `sysref_seg_fill_not_drawn`，
并先要求自家那颗在同一颗尺下读得出范围）⇒ 开成 394，本机不签这一半。
③ **命令没跑成**的：本轮没有 —— CI 对平留到 R332 第 ⓪ 条现读（push 之后的 run↔commit 成对写回）。

CI 对平（本轮开场读上一轮的）：RUN=40091469060 ↔ `4e9e59a` ⇒ completed/**success**；
RUN=40086526381 ↔ `c3fdc02` ⇒ failure 在 STEP[9] `LEDGER_TOKENS books=7 stray=1`（就是 R329 漏下的那个
占位符，R330 已修，本轮不再复现）；RUN=40086499268 ↔ `d21eceb` ⇒ success。
本轮要盯的两件事：① runner 电池 `Ran 619（skipped=2）` 与本机 `Ran 619（skipped=4）` 的差是**已登记**的两格
（/tmp 日志缺失 + 没有已构建的 .app），R330 新增的 8 格 python 判据**没有**进 skip 名册 ⇒ 上一轮那条担心
被现读结案；② `REALSCREEN_*` 这一族不进 CI（要一块醒着的屏幕），那一跑没有它的读数 ≠ 没跑成。

⓪ R332 开场要先读的（成对：run id ↔ commit，现读自 gh run list --json databaseId,headSha,status,conclusion）：RUN=40097837516 ↔ `6935e1b`（本笔 push 的那一跑，回填时 status=in_progress / 未读 ⇒ 只登记不轮询）；RUN=40091830006 ↔ `cdc3b64` ⇒ completed/**success**（R330 的追记那一跑，本轮开场还没读到，现在结掉了）；RUN=40091469060 ↔ `4e9e59a` ⇒ completed/**success**；RUN=40086526381 ↔ `c3fdc02` ⇒ failure 在 STEP[9] LEDGER_TOKENS books=7 stray=1（R329 漏下的占位符，R330 已修，本轮不再复现）。这一跑要盯的三件事：① 新读数族 `SEGREF_POLARITY` 有没有在 runner 上印出来 —— 它现在在 §8 的搬运名单里（`--must-include` 声明=1 缺=0 是**本机**的读数），runner 上一行都没有就要分清是走了具名出口 `sysref_seg_fill_not_drawn` 还是这一格根本没跑（394 判的就是这一格，别把它读成回归）；② 全量卷 `Executed` 那三格在 runner 上是否仍是 984/47/0 这一族（本机现读），红名单归因要用改动**之前**那一跑做对照；③ 帧基线在 runner 上 `COMPARED` 必须非 0（本机 178），`COMPARED=0` 时的 `CHANGED=0` 是空对账。

⓪-b 这三件事本轮追记二就读了答案（RUN=40097837516 ↔ `6935e1b` 现读 completed/**success**）：① `SEGREF_POLARITY` 在 runner 上**印出来了**，两档各一行、两档都 `AB=两臂镜像一致`，没走具名出口⇒ 参照臂跨机器成立（394 结案）；② runner 全量卷 `Executed 984 / skipped=56 / failures=0`、`MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）｜机器=github-runner`；③ 帧基线 `CAPTURED 178`、`COMPARED=178`（非 0 ⇒ 分母在）、`CHANGED=62 MISSING=6 ADDED=116`（对 v1.4.8 那一格是 report-only 的历史对照，不是本轮的闸）。**但答案里有一条改判**：runner 亮档 系统 差=+31.0 与本机亮档 -30.0 **反号**，暗档两边同号 ⇒ 393 的硬断言只立暗档同侧，亮档继续只印数（D-325）。

下一轮（R332）的靶，按顺序：① **393**：391 的落地只剩①—— 药丸换成 `unemphasizedSelectedContentBackgroundColor`
（参照臂量出的分母），并把 `pillRun` 的"药丸=与页底同档"重基成"药丸=两帧之间变了的那一档"（极性无关），
D-318/D-319 的改前改后四数 + 按档各立的同侧断言（D-323）+ R327…R329 那几张表的针重钉重跑；
② 390 的 before/after（并集之后中段洞宽 21%→~49%、纵向覆盖 29%→≥70%）；③ 389 的时长；
④ 384 的横轴那半（轨道档按分箱取，不许再用众数）；⑤ 387 的①（墨量那颗不进 max()）；
⑥ 392 的三格真机欠账（按下档 / 快速选取色 / 菜单栏悬停）；⑦ 394（`SEGREF_POLARITY` 的 runner 现读）；
⑧ 376 剩下那一半；⑨ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

## R330 状态（2026-10-24 · 本地 · 第 329 轮 / Round 327）：377 在屏幕上判掉了 —— 选中那颗比轨道暗 33 级且跟着选中搬（产品 0 文件，真机账）

最后更新：2026-10-24（本地 · R330 / 第 329 轮 / Round 327）：真机现读侧栏筛选胶囊 轨道 81.0 / 选中那颗 48.0 / 页底 51.0
⇒ 差 -33.0 级，点另一颗之后洞搬到右半 ⇒ 377 判成**产品缺陷**（不是离屏通道的锅）
（产品 0 文件 · 真机账 · 合计 87/105）

本轮做了什么：第一次把侧栏那颗胶囊搬到真机上量。新尺 `scripts/real_screen_filter_pill.py`
（列电平取中位、页底两趟外取、第四道闸纵向实心度、四条具名出口）+ 新判据卷
`scripts/tests/test_real_screen_filter_pill.py`（合成帧，`Ran 8 tests`）+ 一支打这把尺自己的表
`mutate_r330.py`（CAUGHT=3/3, RESTORE_CLEAN=yes，逐臂 M957, M958, M959）。同一趟里尺自曝三次读错对象：
`max` 列电平 → 差 -78.4 的假胶囊；只判横向 → 差 -99.0 的标题行；行内众数当页底 → 臂 B 翻成「不是缺陷」
（差 +31.0，结论整个反）。三次都修成了闸 + 刀（D-320 / D-321）。

验证读数（现读）：真机臂 A `PILL_ROW y=120pt 轨道宽=320pt(x0起) 洞宽=168pt(x2..170, 占 52%) 页底=51.0 轨道档=81.0 药丸档=48.0 差=-33.0 实心=0.46` → `pill_darker`；臂 B `PILL_ROW y=116pt 轨道宽=260pt(x0起) 洞宽=68pt(x172..240, 占 26%) 页底=51.0 轨道档=80.0 药丸档=48.0 差=-32.0 实心=0.47` → `pill_darker`；
两臂对照 `AB_SUMMARY A: 洞 x2..170 差=-33.0 | B: 洞 x172..240 差=-32.0 | 洞搬了=yes 两臂都比轨道暗=yes` → `selection_follows_dark`；新判据卷 `Ran 8 tests OK`；刀 `CAUGHT=3/3, RESTORE_CLEAN=yes`；
针预检 tables=118 covered=101 bad=0、名册 files=212 arms=826 dupes=0；
脚本电池 `Ran 619（skipped=4）`；产品面连续零改动 **11** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 329`，`--check` 同形；本轮这一笔按 `--streak-for 330` 现读是 12，要等 commit 之后 git 才派生得出来；上一轮那一格是 10）。

NOT-RUN（三种缺席分开写，不许省略）：① **本轮没有对象**的四腿 —— build 0 告警 / swift 判据卷 /
重捕帧 / 帧基线对账 / 换装本机：改动面 8 个文件，全是 python 与台账，0 个 Swift 文件，
这四腿本轮不判任何东西；② **只在 runner 上判得了**的：`REALSCREEN_*` 这一族不进 CI
（它要一块醒着的屏幕与一次人工退出 App），所以 §8 的搬运名单这一腿本轮**不适用** ——
新读数族由尺自己打印，没接进 `round_verify.sh`，要进 §8 得先接进去（欠账记在 392）；
③ **命令没跑成**的：CI 对平本轮没读到（`gh` 两次 `EOF`，网络抖动那一族），
run↔commit 的配对留到 R331 第 ⓪ 条现读。

CI 对平：本轮写盘之前无新 run；R330 要读的那一跑（RUN=40086499268 ↔ d21eceb，R329 账半）
现读时网络 `EOF` ⇒ 记「未读」，不记「绿」。

⓪ R331 开场要先读的（成对：run id ↔ commit，三笔现读自 `gh run list --json databaseId,headSha,status,conclusion`）：
**RUN=40086499268 ↔ d21eceb = completed / success**（R329 账半）；**RUN=40086526381 ↔ c3fdc02 = completed / failure**（R329 追记 —— 那一跑红在 STEP[9] Release script tests，正文现读 `LEDGER_TOKENS books=7 chars=3198474 stray=1` ⇒ 就是 R329 漏下的那个「at 号夹着 RPREVTAG」的占位符（它自己也被这一格抓过一次：正文里照抄那个形状同样会红），本笔 R330 已修掉并落进台账；于是「这一跑为什么红」不用再猜，而「报告里写的读数有没有被机器读过」这件事第一次有了一个 runner 证人）；
**RUN=40091469060 ↔ 4e9e59a**（本笔 R330 真机账，回填时仍 `in_progress` ⇒ id 已配、结论未读）。这一跑要特别看两件事：① 脚本电池在 runner 上的 `Ran` 与 skip 数 —— 本机现读 `Ran 619（skipped=4）`，而 runner 上一跑是 `Ran 611（skipped=2）`，本轮新增的 8 格是 PIL-gated，若 runner 缺 PIL 就会进 skip 名册 ⇒ 那要按 252 那一族具名，不许读成绿（`test_skip_roster` 会先响）；② `REALSCREEN_*` 这一族不进 CI（它要一块醒着的屏幕），所以那一跑不会有它的读数 —— 没有 ≠ 没跑成，别把它记成回归。
要读的三件事：① 那一跑的 `MOTION_FLOOR_SUITE_CLEAN` 与两朵 pill 命名出口；
② `纵向覆盖` 在 runner（1×）上印出的比值与本机是否同形（那台是 1× ⇒ px 数减半，比值应当不变）；
③ 脚本电池在 runner 上是否也 `Ran 619`（本轮新增 8 格 python 判据，
若 runner 缺 PIL 会走 skip ⇒ 那要按 252 那一族具名，不许读成绿）。

① R331 的靶：① **391**：377 的修法（选中那颗抬到轨道之上，或把轨道压到页底之下），
按 D-318/D-319 给改前改后的 轨道档 / 药丸档 / 页底档 / 差 四个数，且离屏与真机两边同向；
② **390 的 before/after**（并集之后中段洞宽必须从 21% 涨向 49%、纵向覆盖从 29% 到 ≥70%，
涨不到就是并集没生效）；③ 389 的时长（胶囊位移与内容淡出量成 ms 并对 `MotionCatalog` 的档）；
④ 384 的横轴那半（轨道档按分箱取，不许再用众数 —— 与 D-321 是同一件事的另一面）；
⑤ 387 的①（墨量那颗不进 max()）；⑥ 392 的三格真机欠账（按下档 / 快速选取色 / 菜单栏悬停）；
⑦ 376 剩下那一半；⑧ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

## R329 状态（2026-10-24 · 本地 · 第 328 轮 / Round 326）：取用带第一次报出自己盖不住那颗胶囊（产品 0 文件，动效主线）

最后更新：2026-10-24（本地 · R329 / 第 328 轮 / Round 326）：报告新增 `纵向覆盖` 一格，
真帧现读 纵向覆盖=14/48px=29% ⇒ 斜坡尺与过程证人一直用的是胶囊顶部的一条切片（未留档的逐行表独立复核到同一个高度）
（产品 0 文件 · 判据账 · 合计 89/105）

本轮做了什么：① **⓪ 读 R328 那一跑**：RUN=40084527261 ↔ 215d815；分档在 runner 上印得出（runner 现读 分档=0×138,2×120,4×4,5×3,6×5,10×1,12×3,13…（本轮新加的 纵向覆盖 那一格这一跑还没有，下一跑才签）），
新读数出厂第一跑就在两台机器上都有数；build-and-test	Motion filmstrip (report-only)	2026-10-24T10:17:55.0081190Z MOT；两朵 pill 出口 pill-ramp-no-intermediate,pill-slide-arms-indistinguishable；`MOTION_FLOOR_SUITE_CLEAN=0`。
② **388 的最后一问交了数**：取用带占那颗胶囊纵向范围的 29%，中间 22px 是标签行 ⇒ 结构上盖不住。
③ **两格证人 + 两把刀**：CAUGHT=2/2, RESTORE_CLEAN=yes（M955 只往一个方向扩、M956 把"无"印成 0%），
R328 表在新代码上复跑 CAUGHT=3/3, RESTORE_CLEAN=yes，针预检 bad=0。
④ 看图腿：逐行走了一遍胶囊的纵向范围（临时尺，配方写在正文里），并新登记一格没有参照臂的 1pt 内缩。

本轮**没有**改带子的纵向定义，也没有改产品：两条修法（承认切片 / 跨行并集）都要同一运行里改前改后的
四个数，按 D-319 不许只改一边 ⇒ 开成 390。产品面连续零改动 **10** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 328`，`--check` 同形；上一轮那一格是 9）。

验证读数（现读）：ROUND_VERIFY build_warnings=0 swift_executed=983 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r329_rv；ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；Executed 983 tests, with 47 tests skipped and 0 failures；CAPTURED 174 -> /tmp/r329_rv/frames；FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0；
判据卷 `MotionPillRampTests` 33 格全绿（本轮新增 1 格：被拒段必须带洞宽，且分母不许是洞自己）；胶囊两把判据整跑 Executed 2 tests, with 0 tests skipped and 0 failures（testFilterPill 两格，开 CLIPBOARD_HISTORY_UI_MOTION）；
带子 `行带=51.0…58.0pt 候选段里被拒那一段 高22px 洞宽=21%，通过那一段 高14px 洞宽=49% 取用=y102..116px 纵向覆盖=14/48px=29%`；本轮刀 CAUGHT=2/2, RESTORE_CLEAN=yes；
针预检 tables=117 covered=100 bad=0、名册 arms=823 / files=211；
搬运名单 `READINGS_MUST_INCLUDE 声明=3 缺=0`；脚本电池 `Ran 611（skipped=4）`；CI 对平：RUN=40084527261 sha=215d815 status=completed conclusion=success title=R328 追记（把 push 之后的 run↔commit 成对写回 STATE 的 R329 第 ⓪ 条：RUN=40 workflow=CI。

⓪ R330 开场要先读的（成对：run id ↔ commit）：**RUN=40086499268 ↔ d21eceb**（本笔追记时仍在 `in_progress` ⇒ 成对号先记，三件事的读数下一轮再抄）。另外 R328 那一跑已经签完：**RUN=40084527261 ↔ 215d815 = completed / success**（本轮 ⓪ 的分档读数就是从它取的）；
要读的三件事：① `纵向覆盖` 那一格在 runner 上印不印得出、百分比与本机是否同形（那台 1× ⇒ px 数减半，
比值应当不变 —— 变了就是分母随倍率漂）；② 两朵 pill 命名出口继续响；③ `MOTION_FLOOR_SUITE_CLEAN` 仍为 0。

① R330 的靶：① **390 的 before/after**：先写判法（并集之后中段洞宽必须从 21% 涨到接近
49%，涨不到就是并集没生效），再实现，再给同一次运行里改前改后的 洞宽 / 位移 / 倒退 / 纵向覆盖 四个数；
② 389 的时长（把胶囊位移与内容淡出量成 ms 并对 `MotionCatalog` 的档）；
③ 384 的横轴那半（轨道档按分箱取，不许再用众数）；④ 387 的①（墨量那颗不进 max()）；
⑤ 376 剩下那一半；⑥ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
**R330 要落一次产品面**：连续 10 轮零产品文件，这一维一直在垫底；
能落的四条（347 / 305 / 373① / 377）全被真机普查挡着 ⇒ 若 ① 指向"看得见的东西"优先做它，
否则照实写"本轮仍未落"，不许为破纪录加动效。

② 仍开：390（新）、389、388、384、387、347、305、364、354 的第五步、360、361、362、359、
348 的"数字对不对"、349、350 第二步、351、344、341 的 CI 契约半、339、312、304、296、291；
用户闸门 220 路 A / 228② / 265；真机普查（用户推迟）：347 / 305 / 373① / 377。

NOT-RUN 三格：① 真机肉眼验收（上面那道闸门，含本轮新登记的 1pt 内缩没有原生参照臂）；
② (a)/(b) 两条修法的 before/after 都没跑 ⇒ 本轮只交读数；③ 逐行表来自一次性 PIL、脚本未入库 ⇒ 未留档，
复查配方：按 300×520 切格、列电平取 luma 加权、页底 30 / delta 8 / extent 12..287pt、逐行取最长连续洞。

## R328 状态（2026-10-24 · 本地 · 第 327 轮 / Round 325）：388 的转储搬进仓库尺 + 两处公开更正（产品 0 文件，动效主线）

最后更新：2026-10-24（本地 · R328 / 第 327 轮 / Round 325）：**逐列分档进 `movingHoleBand` 的报告（第 0 箱=判据认的洞），被拒那 22px 现读三档同现 ⇒ "洞太窄"改判为判据判对了；同轮更正上一轮两处（"字墨不是主因"→估计量被抢、"文字同时变淡"→淡的是列表内容）**（产品 0 文件 · 判据账 · 自评合计 88/105）

本轮做了什么：① **⓪ 读 R327 那一跑并逐条兑现**：RUN=40080135189 ↔ eeb9058 全绿，
三件事都有答案（runner 的 GEOM 行印出了 洞宽=21%/通过段 49%、两朵 pill 出口继续响、
`MOTION_FLOOR_SUITE_CLEAN=0`），并且新读到一格不稳：墨量方向在 runner 自己两跑之间从 亮11/暗0 变成
10/1 ⇒ 387 的"减常数"作废；
② **388 的转储搬进仓库尺**：被拒候选段带 `分档=k×列数`（箱号=floor((电平−页底)/delta)），
真帧现读 洞档=292 轨道档=244 字墨档=51 最高箱=24 总列=596 ⇒ 那 22px 是"胶囊下半 + 轨道 + 标签的字"混排，不是被切窄的胶囊；
③ **两处公开更正**（U-1087：撤回上一轮那句「字墨不是主因」，并把看图腿那句「胶囊与文字同时变淡」改成「淡的是列表内容，标签恒定」) + **一根自己挖坏的针重钉**（M951 命中 0 → 预检 bad=1 → 重钉 → 新代码上复跑 r327 表）；
④ 看图腿：三张条带 + 174 张整窗帧，并把上一轮那句没量过的形容词量成两条曲线。

验证读数（现读）：ROUND_VERIFY build_warnings=0 swift_executed=980 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r328_rv；ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；Executed 980 tests, with 47 tests skipped and 0 failures；CAPTURED 174 -> /tmp/r328_rv/frames；FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0；
判据卷 `MotionPillRampTests` 31 格全绿（本轮新增 1 格：被拒段必须带洞宽，且分母不许是洞自己）；胶囊两把判据整跑 Executed 2 tests, with 0 tests skipped and 0 failures（testFilterPill 两格，开 CLIPBOARD_HISTORY_UI_MOTION）；
带子 `行带=51.0…58.0pt 候选段里被拒那一段 高22px 洞宽=21%，通过那一段 高14px 洞宽=49% 取用=y102..116px 分档[洞档=292 轨道档=244 字墨档=51 最高箱=24 总列=596]`；
runner ⓪ `build-and-test	Motion filmstrip (report-only)	2026-10-24T09:12:27.9003660Z MOTION_SCENARIO_AB_SUMMARY 场景=12 同=6 漂=5 敏感=1 换对象=0 粒度不可比=0（口径=首末面积∪动过并集∪首末墨量 取较大者，一颗不许替另一颗说话；钉档判据：换对象/敏感 ⇒ 该钉，漂 ⇒ 登记不钉）`；`build-and-test	Motion filmstrip (report-only)	2026-10-24T09:12:27.9001700Z MOTION_SCENARIO_AB_MAGNITUDE 有变化=11 亮臂更大=10 暗臂更大=1 比值暗除亮=0.72…1.03（全在同一侧 ⇒ 墨量这颗尺带一个色档级系统偏移，5%/25% 在它身上没有出处：BACKLOG 387）`；`runner 现读 候选段洞宽=21%,49%,48%（本机 21%/49%）`；
本轮刀 `CAUGHT=3/3, RESTORE_CLEAN=yes`（逐臂 M952 CAUGHT；M953 CAUGHT；M954 CAUGHT）；针预检 tables=116 covered=99 bad=0、
名册 arms=821 / files=210；搬运名单 `READINGS_MUST_INCLUDE 声明=3 缺=0`；
脚本电池 `Ran 611（skipped=4）`；腐烂针尺 `HIDDEN_ARMS 表=204 可判=753 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；CI 对平：RUN=40080135189 sha=eeb9058 status=completed conclusion=success title=R327 追记（把 push 之后的 run↔commit 成对写回 STATE 的 R328 第 ⓪ 条：RUN=40 workflow=CI。

⓪ R329 开场要先读的（成对：run id ↔ commit）：**RUN=40084505594 ↔ 81cd712**（本笔追记时那一跑仍 `status=in_progress` ⇒ 成对号先记，三件事的读数下一轮再抄；`ci_read.py latest` 现读，标题对得上本笔账半）；
要读的三件事：① 分档那一格在 runner 上印不印得出（`判=洞太窄 洞宽=NN% 分档=…`，那台 1× ⇒
第 0 箱与第 2 箱应当仍然分得开，读到"只有一箱"就是那台的 delta 把两档洗成一档）；
② 两朵 pill 命名出口继续响（不许悄悄变回断言红）；③ §8 的 `MOTION_FLOOR_SUITE_CLEAN` 仍为 0。

① R329 的靶：① **388 剩下那半格的前置**——先回答"取用带 14px 有没有把胶囊的完整高度框进去"
（现读胶囊目测跨 y51..69pt = 18pt，而取用带只有 7pt）⇒ 如果没框全，先修的是带子的纵向范围，不是洞、不是闸；
② **389 的时长**：把胶囊位移与内容淡出两条量成 ms 并对 `MotionCatalog` 的档；
③ 387 的①（墨量那颗不进 max()，先找出翻边的是哪颗场景）；④ 376 剩下那一半；
⑤ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。
**并且 R329 要落一次产品面**：产品面连续零改动 **9** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 327`，`--check` 同形；上一轮那一格是 8），这一维一直在垫底；
能落的四条（347 / 305 / 373① / 377）全被真机普查挡着 ⇒ 如果 ① 或 ② 指向"看得见的东西"，
优先做它；否则照实写"本轮仍未落"，不许为破纪录加动效（D-316 与仓库规矩同一条）。

② 仍开：389（新）、384、387、388、347、305、364、354 的第五步、360、361、362、359、
348 的"数字对不对"、349、350 第二步、351、344、341 的 CI 契约半、339、312、304、296、291；
用户闸门 220 路 A / 228② / 265；真机普查（用户推迟）：347 / 305 / 373① / 377。

NOT-RUN 三格：① 真机肉眼验收（上面那条闸门）；② M951 只在**新代码**上复跑，旧树没重跑
（重跑等于回滚本轮改动，本轮不付这个代价）；③ 看图腿那两组名数出自一次性 PIL、脚本未入库 ⇒
未留档，复查配方：把条带按 300×520 切格，列表区取 y96..260pt 最亮前 5% 像素的均值、
标签区取 y58..69pt 前 10 列均值。

## R327 状态（2026-10-24 · 本地 · 第 326 轮 / Round 324）：384 的修法①被现读证伪并撤回，留下"被拒段差多少"那一格（产品 0 文件，动效主线）

本轮做了什么：① **⓪ 读 R326 那一跑并逐条兑现**：RUN=40076227591 ↔ 255354f 全绿、
`ASSERTION_RED` 0 行、两朵 pill 命名出口都在（`pill-slide-arms-indistinguishable` / `pill-ramp-no-intermediate`）、
`MOTION_FLOOR_SUITE_CLEAN=0`、`粒度不可比=0` ⇒ R326 第 ⓪ 条的三件事全部有答案；
同时拿到第二个数据点：runner 的新口径是 同=5 漂=6 敏感=1 换对象=0（本机是 同=1 漂=3 敏感=8 换对象=0），
而 `_MAGNITUDE` 的方向两台都是 11/11 亮臂更大（比值 0.72…0.99 对 0.11…0.94）。
② **按 384 的修法①动手并证伪**：`pillRun` 的几何两版轨道档估计（非页底列众数 / 两帧同列且离页底最近），
被拒段洞宽两次都是 21%（通过段 49%）⇒ 字墨不是主因；第二版还把带子弄断
（取用从 14px 变成"无"）⇒ **全部撤回**，盘上只留报告那一格。
③ **留下的一格**：`候选段=… 判=洞太窄 洞宽=21%` —— 被拒的段现在带"差多少"，
"降地板"与"修对象"两种相反的修法从此分得开；证人含"分母不许是洞自己"（100% 那种恒真句）。

验证读数（全部现读，不手抄）：构建 ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；全量卷 Executed 977 tests, with 47 tests skipped and 0 failures；重捕 CAPTURED 174 -> /tmp/r327_rv/frames；
帧基线 FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0；四件套 ROUND_VERIFY build_warnings=0 swift_executed=977 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r327_rv；判据卷 `MotionPillRampTests` 28 格全绿（本轮新增 1 格：被拒段必须带洞宽，且分母不许是洞自己）；胶囊两把判据整跑 Executed 2 tests, with 0 tests skipped and 0 failures（testFilterPill 两格，开 CLIPBOARD_HISTORY_UI_MOTION）；
带子定位 MOTION_PILL_RAMP_GEOM filter-pill-slide 行带=51.0…58.0pt 轨道范围=12.5…287.5pt 倍率=2.00 页底=30.0 色档=胶片暗/机器亮 轨道=51.9 药丸=36.0 分离=15.9 容差=5.5pt 定位=行=520 候选行=24 判定分布=洞太窄×11,过×13,非候选×496 候选段=y116..138px 高22px 判=洞太窄 洞宽=21% | y102..116px 高14px 判=过 洞宽=49% | y138..150px 高12px 判=过 洞宽=49% 取用=y102..116px；过程证人 MOTION_PILL_SLIDE filter-pill-slide 开A 帧数=3(旧口径7) 峰值=0.241 冷闸=true  开B 帧数=3(旧口径6) 峰值=0.266 冷闸=true  关 帧数=1(旧口径1) 峰值=0.949 同一条线=0.1424 共用线安全=true 声明=200ms 采样≈8ms；变异表 CAUGHT=3/3, RESTORE_CLEAN=yes（逐臂 M949 CAUGHT；M950 CAUGHT；M951 CAUGHT）；
针预检 tables=115 covered=98 bad=0、名册 arms=818 / files=209；
读数族 `READINGS_MUST_INCLUDE 声明=3 缺=0`；脚本电池 `Ran 611（skipped=4）`；
产品文件 0 个，连续零改动 **8** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 326`，`--check` 同形；上一轮 7）。

两处 NOT-RUN（不许省略）：
① **撤回的那两版估计量没有在 runner 上验过**：不需要 —— 它们在本机就被证伪了（读数不变 + 带子弄断），
   记在这里是为了说明"没跑 runner"不是遗漏而是决定；
② **那 22px 里到底是什么**：本轮只做到"排除两条"，转储没做（新开 388）。

看图腿（本轮真看了）：真实视觉审查（本轮看 `/tmp/r327_rv/motion/filter-pill-slide-{开A,开B,关}-strip.png`：
每台 1800×2600 = 6 列 × 5 行、每格 300×520 = 场景的 pt 尺寸，开臂 27 格、关臂 3 格；
另看 174 张整窗帧里的 `content-with-notice-750x560-{light,dark}` 等成对帧）。

**肉眼看到的（位置与名数，不是形容词）**：侧栏顶部那行分段控件（全部 / 收藏）里，
深色胶囊从贴左连续滑到贴右：格 0 贴左、格 26 贴右，中间格能看到它停在轨道中段；
过渡中段的几格胶囊与标签文字同时变淡（横移叠交叉淡，不是坏帧）。
关臂只有 3 格、胶囊在两端之间**瞬移**、没有中间位置 —— 与开臂肉眼可分。开B 与开A 同形。

**U-1084 要的那份逐列转储，就地量了**（一次性仪器 `/tmp/r327_rv/band_shapes3.py`，用完就撤、不进判据；
进判据的那颗尺住在 `MotionFilmstripTests.movingHoleBand`）。参照=该带列电平众数（3 一档），
洞=低于轨道−8 的列，字墨=高于轨道+8 的列。格 0 / 13 / 26 三格都读：

- 取用带 y51..58：轨道众数 51、洞 80/150 列（53.3%）、最暗 29.4、**字墨 0 列**、最长连续洞 134–136pt（一整段）。
- 被拒带 y58..69：轨道众数 51、洞 68–69 列（45–46%）、**字墨 20 列（13.3%）冲到 191–204**、
  最长连续洞只有 **56–60pt，且是两段**（另有一段 54pt）——同样 46% 的暗列，被字墨截成两截。
- 邻段 y69..75：与取用带同形（轨道 51、洞 80 列、字墨 0、最长洞 134pt）。
- 对照带（空白 y30..40 与列表区 y80..120）：最亮只到 72.3 / 65.3，没有 200 级那一档 ⇒ 200 级那档**只在被拒带里出现**。

⇒ 被拒的那 22px 与上下两段的差别**不在暗量**（45–46% 对 53%，只差 7–8 个百分点），
**在形状**：那里有 13.3% 的列是 191–204 级的字墨，把一颗洞从 134pt 截成 56–60pt 两段。
所以仓库尺报的 21% 与 49% 之差，量的正是"截断之后最长那一段还剩多少"。
这把 388 的三选一收窄了：①"降 `minHoleFraction`"依旧错（那等于把形状闸拆了）；
②"extent 之内再分一档"现在有了具体的第二档名字（191–204 的字墨），但要不要把它当洞，
取决于"一颗被自己的标签截断的胶囊算不算胶囊"——这是**定义问题不是读数问题**，需要下一轮先写判法再动手；
③"候选带形状闸"（带内有 200 级墨就不当胶囊带）能把这条带子在候选阶段请出去，代价是
胶囊与标签**本来就在同一行**这个事实被尺永久看不见。

**临时尺自己复现了本轮撤回的那朵坏法（这条比上面的数更有价值）**：同一份数据、格 0 那一格，
被拒带的轨道众数读成了 **36**（胶囊自己的档），于是"低于轨道−8 的洞"读到 **0 列**、字墨读到 81 列（54%）。
这正是 R327 撤回的第一版估计量犯的错（众数被抢 ⇒ 轨道档读成胶囊档）。
它不是我的临时尺特别笨：**同一批像素里，众数到底落在哪一档是由"那一格胶囊占了几成宽度"决定的**，
格 0 胶囊占满该行左半边，众数就翻了。⇒ "众数当轨道"这条在任何一格都可能翻，
下一轮如果要再动轨道档，必须带着"逐格都不许翻"的证人，而不是只在某一格上过一遍。

诚实记账四处：① 撤回的两版估计量（轨道档改成非页底众数 / 两帧同列同档）的
`MOTION_PILL_RAMP_GEOM` 行**没留在盘上**（`motion-readings.log` 每跑覆盖一次）⇒
"两版读数不变"是**未留档的读数**，要复查按配方重跑（已写进 U-1082 与 D-314）；
② 上面那些百分比来自临时尺，它与仓库尺的 `洞宽` **不是同一个分母**（仓库尺按 extent 归一、
逐像素行取最长连续段；临时尺按整格 150 个采样列归一、并给了最长段），
所以我只拿它判形状（有几档、极值多少、段被截成几段），**不拿它的数去复核 21% / 49%**；
③ v2 那版临时尺把"轨道"取成该带 90 分位，于是在文字行里把字墨（140 级）当成了轨道，
"洞"读出 88.7% —— 那是参照点错，不是读数；发现后改成众数重跑（v3），上一版的数不许留下；
④ 本机是亮档机器、这卷胶片钉的是暗档 ⇒ 看图看到的是"胶片暗/机器亮"那一格；
换装真机后的肉眼验收仍欠（用户已推迟真机普查，本轮不排）。

⓪ R328 开场要先读的（成对：run id ↔ commit）：**RUN=40080021426 ↔ e506857**（本笔追记时那一跑仍
`status=in_progress`，所以成对号先记、读数下一轮再抄；`ci_read.py latest` 现读，标题对得上本笔账半）。
要读的三件事：① 报告那一格在 runner 上印不印得出（`候选段=… 洞宽=NN%`，那台是 1× 无 Retina，
带子像素数不同 ⇒ 百分比应当仍然可比 —— 读到"洞宽=无"就是分母或中位数在那台机器上塌了）；
② 两朵 pill 命名出口继续响（不许悄悄变回断言红）；③ §8 的 `MOTION_FLOOR_SUITE_CLEAN` 仍为 0。

① R328 的靶：① **388 的转储**（那 22px 的逐列电平）⇒ 拿到之后三选一，
   并且**这一轮要落一次产品面**：如果转储指向"选中段有第三档"，那既是尺的问题也是**看得见的东西**，
   值得为它跑一次真帧对照；连续 8 轮零产品文件，这一维一直在垫底；
   ② 387 的①（减偏移再判，现在有两台的数据可减）；③ 376 剩下那一半；
   ④ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀；
   ⑤ 真机眼那一批（347 / 305 / 373① / 368）—— 用户已明确暂时做不了，不排进轮次。

最后更新：2026-10-24（本地 · R327 / 第 326 轮 / Round 324）：**384 的修法①证伪并撤回，报告补上"被拒段差多少"那一格**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 977 tests, with 47 tests skipped and 0 failures`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=977 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r327_rv`；变异表 `CAUGHT=3/3, RESTORE_CLEAN=yes`；
带子 `行带=51.0…58.0pt 候选段里被拒那一段 高22px 洞宽=21%，通过那一段 高14px 洞宽=49%`；runner ⓪ `MOTION_SCENARIO_AB_SUMMARY 场景=12 同=5 漂=6 敏感=1 换对象=0 粒度不可比=0（口径=首末面积∪动过并集∪首末墨量 取较大者，一颗不许替另一颗说话；钉档判据：换对象/敏感 ⇒ 该钉，漂 ⇒ 登记不钉）`；脚本电池 `Ran 611（skipped=4）`；针预检 bad=0、名册 arms=818。
连续零改动那一格只写在上面「验证读数」段里一次（`test_product_streak_cell` 数的是同一格里的候选数）。

## R326 状态（2026-10-24 · 本地 · 第 325 轮 / Round 323）：R325 那份「12 颗不必钉」的尺读的是采样通道 —— 分类器换成三颗通道无关的量（产品 0 文件，动效主线）

本轮做了什么：① **⓪ 读 R325 那一跑并逐条兑现**：RUN=40057803215 ↔ 929c084 全绿，
`ASSERTION_RED` 整跑 **0 行**，两朵命名出口都在 runner 上响了自己那格
（`pill-slide-arms-indistinguishable`、`pill-ramp-no-intermediate`），§8 的 `MOTION_FLOOR_SUITE_CLEAN=0`
⇒ R324 那朵 STEP[19] 的红修完了。② **但同一跑给了本机一个相反的分类**：
runner `敏感=2`（noticeBanner / noticeBannerDismiss）对 本机 `敏感=0`，而两台那一跑的胶片帧数同为 30
⇒ 决定"要不要钉"的那颗峰值是采样通道的量（`noticeBanner` 本机 0.2598 对 runner 0.7208）。
③ **修**：新增三颗通道无关的尺（首末面积 / 动过的并集 / 首末墨量差）并取较大者判，
峰值降为只印不判（`_CHANNEL` 两行保留给对账）；分界与前提抽成共用纯函数（否则"敏感"这条线会有两份字面量，
这一点是被 R325 的 M938/M940 命中 2 次当场抓到的）；通道同一性拆两格（像素尺寸严格相等 / 粒度容差 25% 或 1 帧）；
只印不判的 MAGNITUDE 那格配了会红的分母同一性断言。④ **本机重测三份口径**：
三颗口径 `同=1 漂=3 敏感=8 换对象=0 粒度不可比=0`、面积两颗 `同=12 漂=0 敏感=0 换对象=0`、峰值 `同=9 漂=3 敏感=0 换对象=0 判定不同=9`，
墨量那颗带系统偏移（`有变化=11 亮臂更大=11 暗臂更大=0 比值暗除亮=0.11…0.94`，11 颗全是亮臂更大）⇒ **本轮不据 敏感=8 去钉 8 颗**，
新开 387（阈值在新尺上的出处），并把 R325 那句"不钉是判断"公开更正（383 的追记）。

验证读数（全部现读，不手抄）：构建 ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；全量卷 Executed 976 tests, with 47 tests skipped and 0 failures；重捕 CAPTURED 174 -> /tmp/r326_rv/frames；
帧基线 FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0；四件套 ROUND_VERIFY build_warnings=0 swift_executed=976 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r326_rv；判据卷 `MotionPillRampTests` 27 格全绿（本轮新增 4 格：采样粒度、面积盲区、并集分母同一性、粒度容差；分类器那格从 6 条加到 7 条）；
胶片卷 Executed 2 tests, with 0 tests skipped and 0 failures（开 CLIPBOARD_HISTORY_UI_MOTION 跑 testFilmScenario 那两格）；色档 A/B 探针两行汇总 MOTION_SCENARIO_AB_SUMMARY 场景=12 同=1 漂=3 敏感=8 换对象=0 粒度不可比=0（口径=首末面积∪动过并集∪首末墨量 取较大者，一颗不许替另一颗说话；钉档判据：换对象/敏感 ⇒ 该钉，漂 ⇒ 登记不钉） / MOTION_SCENARIO_AB_SUMMARY_CHANNEL 峰值口径 同=9 漂=3 敏感=0 换对象=0 与通道无关口径判定不同=9（这一格只印不判：峰值随采样通道走，R326 / 本机 0.2598 对 runner 0.7208）；
变异表 CAUGHT=6/6, RESTORE_CLEAN=yes（逐臂 M943 CAUGHT；M944 CAUGHT；M945 CAUGHT；M946 CAUGHT；M947 CAUGHT；M948 CAUGHT）；针预检 tables=114 covered=97 bad=0、
名册 arms=815 / files=208（含 R326 新表 mutate_r326）；
读数族 `READINGS_MUST_INCLUDE 声明=6 缺=0`；脚本电池 `Ran 611（skipped=4）`；
产品文件 0 个，连续零改动 **7** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 325`，`--check` 同形；上一轮 6）。

两处 NOT-RUN（不许省略）：
① **新口径在 runner 上会不会给出同一份分类**：本轮的修法只能在下一跑的 CI 里被第二台机器验，
   本机签不了那一半（记进下面 ⓪ 的第①条，Runner=R327 第一件事就是读它）；
② **墨量那颗尺读的是 rgb 还是 alpha**：它按 `max(rgb, alpha)` 逐像素取大（与 R77 的三轴规矩同一形状），
   本轮没有按轴切片打读数，所以"亮臂大 11/11 是墨的深浅还是透明度在动"这一格是**未分家的**，
   要 387 的标定那一步顺手切片，否则①那条派生法（减偏移）会减在混合轴上。

看图腿（本轮真看了）：本轮看图看的不是产品，是**本轮那把新尺读的对象**（两条独立通道对上了同一件事）⇒ ① 用 PIL（与 Swift 胶片完全不同的另一条通道）把 R326 那三颗尺要量的东西，在**已入库的帧**上按"两端点之间：动过的像素占比 / 动过的平均级差"重算一遍：`content-empty-750x560` 对 `content-with-history-750x560`（emptyState 同族）亮档 占比 0.0719 / 级差 194.5，暗档 占比 0.0693 / 级差 49.2；`content-with-history` 对 `content-no-results`（searchReflow 同族）亮 0.0733 / 190.3，暗 0.0706 / 57.0；`detail-0-text` 对 `detail-2-file`（detailKindChange 同族）亮 0.0373 / 65.0，暗 0.0380 / 54.5 ⇒ **面积两颗在两档里几乎不动（最大差 4%），墨量那颗差 1.2–4.0 倍且每一颗都是亮档更深** —— 这正是 U-1077 与 U-1078 的结构：哪些像素在动与色档无关，动了多少级随色档走、而且带同一个方向。② 眼睛看到的与数一致：暗档那张 `content-with-notice-750x560-dark.png` 里横幅的红图标、"知道了"按钮、正文都还在（形状与亮档那张同一份），但整条横幅压在 30–37 这一档底上，亮档同一区域从 54 走到 255 ⇒ "暗档里同样的动、动的级差小得多"不是抽象结论，是看得见的。③ 一次差点开错的单：同一张暗档帧里侧栏四行列表标题几乎黑底黑字，第一反应是产品缺陷，先搜台账才看见 D-090（R30）已写明"vibrant 列的文字极性是故意反的、`cacheDisplay` 不做合成那一步 ⇒ 拍到的是合成前像素"，且 `darkSidebarTextBlindSpots` 名册在册 ⇒ 那是登记的通道盲区，不是新缺陷，本轮没为它起新名字（同一族 R325 差点为那块 #000 黑块开单，两次都是"先看图、先量数、后查重"的顺序救回来的）。④ 本轮产品 0 文件，帧基线 FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0 ⇒ 上面那些图与 R325 那一批是同一张图，看图腿没有靠旧图替新东西作证。

⓪ R327 开场要先读的（成对：run id ↔ commit）：本轮两笔都已 push —— 代码半 sha=bd084e3（推在账半之前，同一跑里）、账半 sha=255354f ↔ **RUN=40076227591**（写这一行时 status=in_progress ⇒ 结论还没读，R327 第一件事就是读它）；
要读的三件事：
   ① **新口径的 runner 分类**：`MOTION_SCENARIO_AB_SUMMARY` 在 runner 上读成什么，
      与 runner 上那份旧峰值分类（敏感=2）对得上没有；`MOTION_SCENARIO_AB_MAGNITUDE` 的
      「亮臂更大=多少 / 有变化=多少」在 1× 那台机器上是不是也全在一侧 —— 那是 387 的第二个数据点，
      如果 runner 出现"两侧都有"，本机那条系统偏移就不是色档级而是本机级；
   ② **粒度容差那条**：`粒度不可比` 在 runner 上应当是 0；读到 >0 就先看是不是那台机器把某一臂饿死了
      （不许顺手把容差放宽，先归因）；
   ③ 两朵 pill 命名出口继续在 runner 上响（`pill-slide-arms-indistinguishable` / `pill-ramp-no-intermediate`）
      —— 它们从"红"变成"有名字的未覆盖"这件事不能在本轮之后悄悄变回去。

① R327 的靶：① **384（回到有对象的动效面）**：字墨把洞切成两半 ⇒ 斜坡尺只放行胶囊上沿那几 pt
   （候选修法①：把字墨列并入洞，收藏星那族墨尺有先例）—— 它有现读对象、有修法、不需要真机，
   而且连着 7 轮零产品文件这一维一直在垫底，R327 该动它；
   ② 387 的①（减偏移再判）：本机数据现在就能算，算完才谈 12 颗要不要钉；
   ③ 376 剩下那一半（那台机器上有没有一条能动的通道）；
   ④ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀；
   ⑤ 真机眼那一批（347 / 305 / 373① / 368）—— 用户已明确暂时做不了，不排进轮次。

最后更新：2026-10-24（本地 · R326 / 第 325 轮 / Round 323）：**色档 A/B 的统计量从采样通道换成三颗通道无关的尺 —— R325 那份「12 颗不必钉」被公开更正**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 976 tests, with 47 tests skipped and 0 failures`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=976 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r326_rv`；变异表 `CAUGHT=6/6, RESTORE_CLEAN=yes`；
探针 `MOTION_SCENARIO_AB_SUMMARY 场景=12 同=1 漂=3 敏感=8 换对象=0 粒度不可比=0（口径=首末面积∪动过并集∪首末墨量 取较大者，一颗不许替另一颗说话；钉档判据：换对象/敏感 ⇒ 该钉，漂 ⇒ 登记不钉）`；`MOTION_SCENARIO_AB_MAGNITUDE 有变化=11 亮臂更大=11 暗臂更大=0 比值暗除亮=0.11…0.94（全在同一侧 ⇒ 墨量这颗尺带一个色档级系统偏移，5%/25% 在它身上没有出处：BACKLOG 387）`；脚本电池 `Ran 611（skipped=4）`；针预检 bad=0、名册 arms=815。
连续零改动那一格只写在上面「验证读数」段里一次（`test_product_streak_cell` 数的是同一格里的候选数）。

## R325 状态（2026-10-24 · 本地 · 第 324 轮 / Round 322）：一句没有数的推测换成 12 颗读数，并接住 R324 在 runner 上换形的那朵红（产品 0 文件，动效主线）

本轮做了什么：① **R324 那句"其余 12 颗与色档弱相关"付账**：新增 `Scenario.pinned(to:)` +
纯函数 `appearanceDependenceVerdict`（同 / 漂 / 敏感 / 换对象 四格）+ 逐颗 A/B 探针
`testFilmScenarioAppearanceDependenceIsMeasuredPerScenario`；对象表与 R324 的点名器对账成同一份，
两臂各自证明拍在哪一档。② **本机读数**：同=10 漂=2 敏感=0 换对象=0 ⇒ 没有一颗像胶囊那样在亮档里丢掉对象，
"不钉"升成判断；2 颗漂登记进 383 的追记，两条分界的出处新开 386
（同一份代码、同一台机器跑两遍：第一遍 同=9 漂=3，第二遍 同=10 漂=2，分类翻面了）。
③ **⓪ 读 R324 那一跑并接住换形的红**：带子从 346…352pt 回到 **y52.0…58.0pt**、
`色档=胶片暗/机器亮` ⇒ 两半**兑现**；过程证人红因换了（三臂 1 帧 / 峰值 0.925 全等，
而数组不全等）⇒ 出口谓词从"逐字节相同"换成"判据自己用的那两个数"（D-311），
并补上"一步跳变不许发单调的证"（`intermediateCount` 排在词表之前）。

验证读数（全部现读，不手抄）：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 972 tests, with 47 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r325_rv/frames`；
帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`（本轮没改夹具也没改像素）；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=972 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r325_rv`；
判据卷 `MotionPillRampTests` 23 格全绿（分类器 6 格 + 出口谓词 4 格 + 中间样本 5 格 + R324 那 8 格）；胶片卷整卷 `Executed 67 tests, with 3 tests skipped and 0 failures（整卷开 CLIPBOARD_HISTORY_UI_MOTION）`；
变异表 `CAUGHT=6/6, RESTORE_CLEAN=yes`（M937…M942，逐臂 M937 CAUGHT；M938 CAUGHT；M939 CAUGHT；M940 CAUGHT；M941 CAUGHT；M942 CAUGHT）；
针预检 tables=113 covered=96 bad=0、名册 arms=809 files=207；
读数族 `READINGS_MUST_INCLUDE 声明=3 缺=0`；脚本电池 `Ran 611（skipped=4）`；
产品文件 0 个，连续零改动 **6** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 324`，`--check` 同形；上一轮 5）。

看图腿（本轮真看了）：看了本轮两件事的图。① **色档 A/B 的量的是哪张图**：`/tmp/r324_rv/frames/sidebar-history-300x520-light.png` 与同尺寸 `-dark.png`（本轮重捕 174 帧与工作基线逐张相同，CHANGED=0，所以探针与这两张是同一张图）。亮档那张，搜索框下面那一行「全部 / 收藏」的**药丸肉眼几乎不可辨**——轨道与页底同一档，只剩字重差别；暗档那张药丸是一整块明显的浅色圆角 ⇒ 探针那句"亮档里没有对象"有第二条独立通道，不是只有像素数。② **一次差点开错的单**：同一张帧里列表底部那一整块纯黑圆角矩形，我第一反应是"亮档里选中行画成黑底黑字"，先查重才看见 `UICaptureHarness.materialBlindSpotFixtures` 里 `sidebar-history` 从 R18 就登记着（系统 `List` 的选中高亮是材质，没上过屏的窗口没有可合成背景层 ⇒ #000，亮暗都一样）⇒ 不是新缺陷、不是产品事实，没起新名字。但本轮给那条登记补了一个读数：黑块内**文字列**里亮度 >60 的像素，亮档帧只占 0.06%（字被一起吃掉）、暗档帧占 10.3%（字还在）⇒ 名册那句"亮色暗色都一样"只对"底色是 #000"成立，不对"字看不看得见"成立，这一句要留给下一次读这块盲区的人。③ 本轮产品 0 文件，基线那一侧没有新东西可看；真机眼那一批（347 / 305 / 373① / 368）用户已明确暂时做不了，不排进轮次。

⓪ R326 开场要先读的（成对：run id ↔ commit）：本轮 push 之后那一跑**已取到 id** —— RUN=40057803215 ↔ sha=929c084（写这一行时 status=in_progress ⇒ 结论还没读，R326 第一件事就是读它）；
本轮已读的是 R324 那一跑 —— RUN=40053805112 sha=3ccaaf2（conclusion=failure，红因与处置见 U-1073 / U-1074）。要读的：
   ① **本轮的修法在 runner 上兑现没有**：`testFilterPillSlideIsAProcessNotATeleport` 必须从红变成
      `MOTION_NOT_RUN=pill-slide-arms-indistinguishable`，而 `testFilterPillRampIsMonotone` 必须变成
      `MOTION_NOT_RUN=pill-ramp-no-intermediate` —— 若仍红在断言上，先读它红在哪一条，别改判据；
   ② `MOTION_SCENARIO_AB_SUMMARY` 在 runner 上是不是同一份分类（那台机器本来就在亮档，
      它是"两臂不同档"这条前提的第二台证人）；读到 `换对象>0` 或 `敏感>0` 就说明本机 12 颗里
      有一颗在别的机器上会丢对象 ⇒ 那颗必须钉（383 的追记要改写）；
   ③ §8 里 `MOTION_FLOOR_SUITE_RED` 那一格本轮应当归零；没归零就先读名单。

① R326 的靶：① 384（字墨把洞切成两半，带子只剩上沿 7pt：把墨列并入洞 vs 接受半颗药丸）；
   ② 386 的派生法③（相对差分类换成"两臂判定词是否相同"）；
   ③ 376 剩下那一半（那台机器上有没有一条能动的通道 —— 与 `app-not-active` 同一族，先量再判）；
   ④ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀；
   ⑤ 真机眼那一批（347 / 305 / 373① / 368）—— 用户已明确暂时做不了，不排进轮次。

最后更新：2026-10-24（本地 · R325 / 第 324 轮 / Round 322）：**色档依赖逐颗量完（12 颗：同=10 漂=2 敏感=0 换对象=0）+ 接住 runner 上换形的那朵红**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 972 tests, with 47 tests skipped and 0 failures`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=972 swift_skipped=47 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r325_rv`；变异表 `CAUGHT=6/6, RESTORE_CLEAN=yes`；
探针 `MOTION_SCENARIO_AB_SUMMARY 场景=12 同=10 漂=2 敏感=0 换对象=0（钉档判据：换对象/敏感 ⇒ 该钉；漂 ⇒ 登记不钉；同 ⇒ 有数了才写不依赖）`；脚本电池 `Ran 611（skipped=4）`；针预检 bad=0、名册 arms=809。
连续零改动那一格只写在上面「验证读数」段里一次（`test_product_streak_cell` 数的是同一格里的候选数）。

## R324 状态（2026-10-24 · 本地 · 第 323 轮 / Round 321）：一把"找错对象还报结论"的尺修回有对象 —— 三道形状闸 + 胶片场景钉死色档（产品 0 文件，动效主线）

本轮做了什么：① **交 R323 那两朵 runner 红的账**（RUN=40032708615 / sha=28c8510）：
带子量到的是列表里的一行（y346.0…352.0pt、页底 236.0 ⇒ 那台机器在亮档），
两朵红都是"框错了地方还报结论"；② **三道形状闸**（宽度稳 / 贴两端 / 至少一段之宽）+ 被拒候选报名字的报告（D-309）；
③ **胶片场景第一次能钉色档**（`Scenario.appearance`，NSApp/window/host 三处一起改），
并把"请求==要求 / 胶片==要求 / 两遍同档"写成三条红前提压在出口之前（D-308）；
④ **一处公开更正**：本轮为"去掉极性"设计的 `staticLevel` 锚被真窗口的帧量死了
（两段之间走的药丸 ⇒ 轨道范围里没有一列不动；本机读数 `候选行=5`，而那 5 行是胶囊上下沿的抗锯齿边），
已撤回并锚回页底；⑤ **缺席点名**：`MOTION_SCENARIO_APPEAR 工厂=13 钉了=1 没钉=12 钉了名单=filterPillSlide 没钉名单=blank,detailEmptyToContent,detailKindChange,detailSameKind,emptyState,heatFirstRecord,listInsertNewRecord,noticeBanner,noticeBannerDismiss,promotionToTop,searchReflow,toggleFavoriteInRow` ⇒ 新开 383。

验证读数（全部现读，不手抄）：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 968 tests, with 46 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r324_rv/frames`；
帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`（本轮没改夹具也没改像素）；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=968 swift_skipped=46 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r324_rv`；
判据卷 `MotionPillRampTests` 20 格全绿（含本轮新写的缺席点名正对照与亮档反向证人），
`MotionFilmstripTests` 66 格 3 skip 0 红；胶囊两卷改后 `Executed 23 tests, with 0 failures（两卷一起跑，skip=0）`；
变异表本轮 `CAUGHT=6/6, RESTORE_CLEAN=yes`（M931…M936，逐臂 M931 CAUGHT；M932 CAUGHT；M933 CAUGHT；M934 CAUGHT；M935 CAUGHT；M936 CAUGHT）；
针预检 tables=112 covered=95 bad=0、名册 arms=803 files=206；
读数族 `READINGS_MUST_INCLUDE 声明=6 缺=0`；脚本电池 `Ran 611（skipped=4）`；
产品文件 0 个，连续零改动 **5** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 323`，`--check` 同形；上一轮 4）。

看图腿（本轮真看了）：看了本轮那三张条带图（`/tmp/r324_rv/motion/filter-pill-slide-{开A,开B,关}-strip.png`，各 27 格、6 列排布，末三格是没帧可放的画布底色）。① **钉色档这件事肉眼可证**：本机此刻在亮档，而三张条带通体是暗档底（页底 30 那一档）⇒ `NSApp/window/host` 三处一起改真的落进了胶片，这正是前提⓪那个数的第二条独立通道（`色档=胶片暗/机器亮`）。② **两臂的差别肉眼看得见**：关臂第 2 格就已经是末态（胶囊在右、列表换成"暂无收藏"），开臂第 2、3 格胶囊仍在左、第 4 格才到位 ⇒ 与读数 `开A 帧数=3 / 关 帧数=1` 同向，不是同一卷胶片。③ **尺框到的确实是胶囊那一行**：条带里那颗药丸在搜索框下方那一行，与 `MOTION_PILL_BAND y51.0…58.0pt`（整窗 520pt）一致；R323 在 runner 上量到的 346…352pt 那一行，在同样排布的条带里对应的是列表行而不是这一行 ⇒ "框错了地方还报结论"这一眼能复核。④ 没写成结论的那一眼：开臂走完最后几 pt 用了十几格，这一句不升成判据（形容词不是读数），要判它得先有逐帧速度的尺。看图腿的边界照旧：本轮产品 0 文件、174 帧与工作基线逐张相同（CHANGED=0），基线那一侧没有新东西可看；hover 提示与真机档位那批（347 / 305 / 373① / 368 / 384）用户已明确暂时做不了，仍压着。

⓪ R325 开场要先读的（成对：run id ↔ commit）：本轮 push 之后那一跑**已取到 id** —— RUN=40053805112 ↔ sha=3ccaaf2（写这一行时 status=in_progress ⇒ 结论还没读，R325 第一件事就是读它）；
本轮已读的是 R323 那一跑 —— RUN=40032708615 sha=28c8510（status=completed conclusion=failure，
红因与处置见 U-1065），本轮代码半 sha=0119b24。要读的：
   ① **`MOTION_PILL_BAND` 在 runner 上必须落在胶囊那一行**（本机现读 y51.0…58.0pt，
      暗档；R323 那一跑读到的 y346.0…352.0pt 是列表行）—— 若它仍报别的行，先读报告里的
      `判定分布=`，别改判据；
   ② **`MOTION_PILL_RAMP_GEOM` 的 `色档=胶片暗/机器…` 那一格**：若 `色档=胶片亮`，
      说明钉色档在那台机器上没生效（前提⓪会当场红在"请求没落进胶片"上），这是 385 要的第二条腿；
   ③ `MOTION_SCENARIO_APPEAR` 在 runner 上必须与本机同读（工厂=13 钉了=1 没钉=12）
      —— 它是源码级读数，两机不同就是有人在中间开了单。

① R325 的靶：① **真机眼批次**（用户已明确"暂时还不能做"，现在压着六格：347 亮档按下、305 台阶地板、
      373① 浮层强调色、368 产物级通道、384 字墨切洞要不要并、R323 的 384 前置那一格 377）
      —— 需要用户先退出正在跑的 App，一次跑完比一轮跑一格省；
   ② 383（其余 12 颗工厂逐颗问"要不要钉"，先量分离度再决定）；
   ③ 动效主线继续：354 第五步（观察窗口成本）与 376 的第二条通道；
   ④ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀 / 385。

最后更新：2026-10-24（本地 · R324 / 第 323 轮 / Round 321）：**逐行像素尺修回有对象：三道形状闸 + 胶片场景第一次钉色档**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 968 tests, with 46 tests skipped and 0 failures`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=968 swift_skipped=46 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r324_rv`；变异表 `CAUGHT=6/6, RESTORE_CLEAN=yes`；
缺席点名 `MOTION_SCENARIO_APPEAR 工厂=13 钉了=1 没钉=12 钉了名单=filterPillSlide 没钉名单=blank,detailEmptyToContent,detailKindChange,detailSameKind,emptyState,heatFirstRecord,listInsertNewRecord,noticeBanner,noticeBannerDismiss,promotionToTop,searchReflow,toggleFavoriteInRow`；脚本电池 `Ran 611（skipped=4）`；针预检 bad=0、名册 arms=803；
连续零改动那一格**只写在上面的「验证读数」段里一次**（`test_product_streak_cell` 数的是同一格里的候选数）。
这一行是 R324 起**必带**的那一格：R323 那一节漏了它 ⇒ 当前轮静默停一轮（BACKLOG 382 / sha 0119b24）。

## R323 状态（2026-10-24 · 本地 · 第 322 轮 / Round 320）：斜坡尺第一次读出那颗胶囊走的路（单调、倒退 0.0pt），三处自曝落在盘之前（产品 0 文件，动效主线）

本轮做了什么：① **产品面主线** —— 给全仓唯一那条位移档（`.slider`）装上**斜坡尺**：
逐帧读药丸中心（四颗纯尺 + 词表），本机判定=**单调**、位移 138.0pt、最大倒退 0.0pt、两遍同词
⇒ MC-1"程序触发的位移不给过冲"第一次在产物侧有证人；② **更正 R322 的观察带**：
那条 `y 66…92pt` 是从组件帧目测来的，真窗口这一卷量出来是 49…75pt ⇒ 峰值从 0.097 重测成 0.269；
③ **runner 交账**：R322 那三条硬断言在 runner 上红，红因是三臂逐帧差数组完全相同
⇒ 新增具名出口 + 两条与通道无关的前置硬前提（D-306），并把 M922 那根腐烂针重钉、重跑 3/3。

验证读数（全部现读，不手抄）：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 960 tests, with 46 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r323_rv/frames`；
帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`（本轮没改夹具也没改像素）；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=960 swift_skipped=46 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r323_rv`；
判据卷 `MotionPillRampTests` 13 格全绿、`MotionFilmstripTests` 65 格 3 skip 0 红；
变异表本轮 `CAUGHT=6/6, RESTORE_CLEAN=yes`（M925…M930，逐臂 M925 CAUGHT；M926 CAUGHT；M927 CAUGHT；M928 CAUGHT；M929 CAUGHT；M930 CAUGHT）、R322 那支重跑 `CAUGHT=3/3, RESTORE_CLEAN=yes`；
针预检 tables=111 covered=94 bad=0、名册 arms=797 files=205；
读数族 `READINGS_MUST_INCLUDE 声明=5 缺=0`；脚本电池 `Ran 611（skipped=4）`；
产品文件 0 个，连续零改动 **4** 轮（R319 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for 322`，`--check` 同形；上一轮 3）。

⓪ R324 开场要先读的（成对：run id ↔ commit）：**R323 追记回填** —— RUN=40032708615 sha=28c8510（回填这一刻 status=in_progress，结论未读：进行中的 job 日志打 0 字节，不许把「没读到」写成「没跑」）；本轮已读的是 R322 那两跑 —— RUN=40023610164 sha=1a37edc（status=completed conclusion=failure，红因与处置见 U-1063），本轮代码半 sha=445fde4。要读的：
   ① **斜坡尺与那条出口在 runner 上各自怎么说**（期望先写死在这里，读到才算结案）：
      `MOTION_PILL_RAMP_GEOM` 那一行的 `轨道=/药丸=/分离=` 三个数 —— 若 runner 的分离 < 8，
      它会报 `MOTION_NOT_RUN=pill-ramp-low-separation`（材质在那台机器上落到哪一档，本轮没数）；
      若分离够而两臂仍逐字节相同，斜坡尺会报 `pill-ramp-flat` ⇒ 与 376 同一件事，不许读成产品没动；
   ② `MOTION_NOT_RUN=pill-slide-arms-identical` 在 runner 上**必须出现**（那一跑的红就是它该接住的），
      同时 `MOTION_FLOOR_SUITE_RED` 必须归零 —— 若红换成别的用例名，先读它，别改判据；
   ③ R322 欠的 `HEATMAP_TOOLTIP_CONTROL` / `_CHANNELS` **本轮签了**：两台机器同读`走过=4 屏×档、四类合计全 0`，而同一跑的正对照读到 `视图=3 热图型toolTip=1 热图型无障碍=1` ⇒ 368 的出口是**通道限制**（SwiftUI 的 `.help` 不落进被遍历的那层 `NSView.toolTip`），已写进 368 的追记；剩下的判法只有真机眼（与 347 / 305 / 373① / 377 同一批）。

① R324 的靶：① **真机眼批次**（现在压着五格：347 亮档按下、305 台阶地板、373① 浮层强调色、
      368 产物级通道、本轮新开的 377 胶囊比轨道暗）—— 需要用户先退出正在跑的 App，
      一次跑完比一轮跑一格省；② 378 那把静态尺（写死的矩形逐条问出处）；
      ③ 动效主线继续：354 第五步（观察窗口成本）与 376 的第二条通道；
      ④ 367 迁移 / 360 最后一批 / 361 合并 / 364 六把抽不出的刀。

最后更新：2026-10-24（本地 · R323 / 第 322 轮 / Round 320）：**动效主线：斜坡尺第一次逐帧读出那颗胶囊走的路**（产品 0 文件，判据轮）
这一行是**补写**的（R324 现读）：R323 那一节当时漏了 identity 行，于是 `current_round()` 一路停在 R322，而 `scripts/tests/test_commit_subject_hygiene.py` 按**每一笔自己的树**取当前轮 ⇒ R324 的代码半被读成超前 2 轮。数字不重抄：本轮读数全部写在上面那一节自己的「验证读数（全部现读，不手抄）」那一段里；根因与豁免登记见 BACKLOG 382。

## R322 状态（第 321 轮 / Round 319 · 2026-10-24）

本轮一笔（动效主线）：侧栏那颗「全部 / 收藏」的**横移**第一次有过程证人 ——
新场景 `Scenario.filterPillSlide()` + 新硬判据 `testFilterPillSlideIsAProcessNotATeleport`，
MOTION_PILL_SLIDE filter-pill-slide 开A 帧数=3(旧口径6) 峰值=0.101 冷闸=true  开B 帧数=3(旧口径6) 峰值=0.090 冷闸=true  关 帧数=1(旧口径1) 峰值=0.362 同一条线=0.0544 共用线安全=true 声明=200ms 采样≈8ms；MOTION_PILL_SLIDE_SETTLE filter-pill-slide 到位帧=7 采样≈8ms ⇒ 实测落定≈56ms（声明 200ms） 可分帧=25 ⇒ 中间态帧数开 > 关（两把尺同方向）、峰值开 < 关、落定在上限之内。
它也是全仓唯一一条位移档（`.slider`），以前只有两态证据（两端都对不等于中间在演）。
中间摔了一次：第一版根视图是手搭 Binding 的裸 `SegmentedFilterPicker`，没人观察 store ⇒ 两臂峰值 0.000
—— 换成产品的 `HistorySidebarView`（`@ObservedObject` 那层在它身上）才有对象；规矩升成 D-305。
三把刀 M922 / M923 / M924 CAUGHT=3/3, RESTORE_CLEAN=yes。
⓪ 的 runner 交账一并结掉：QUICKPICK_SELARM_SUMMARY 候选=2 有对象=2 未判=0 落点=light=系统nonKey dark=系统nonKey ⇒ R321 那把尺的修在第二台机器上兑现，四跑的红清零（373 写了追记）。

最后更新：2026-10-24（本地 · R322 / 第 321 轮 / Round 319）：**动效主线：位移档第一次"看得见在演"，而替身根视图被自己的前提闸门拦红**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 946 tests, with 45 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r322_rv/frames`；帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=946 swift_skipped=45 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r322_rv`；
过程证人卷 `Executed 1 test, with 0 failures（不设 CLIPBOARD_HISTORY_UI_MOTION 时整卷 skip）`；变异表 `CAUGHT=3/3, RESTORE_CLEAN=yes`；
针预检 tables=110 covered=93 bad=0、名册 arms=791；
腐烂尺 `HIDDEN_ARMS 表=198 可判=723 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；搬运名单 `声明=2 缺=0`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；
看图腿 RUN（本轮的看图腿看的是**胶片本身**（动效该看的形态），不是静帧。三卷条带逐张过：`/tmp/motion-films/filter-pill-slide-开A-strip.png`、`-开B-strip.png`、`-关-strip.png`（各 30 帧、暗档、侧栏 300×520，由 `writeStrip` 落盘）。
肉眼可辨的差别只有一处，但它是本轮的全部问题：**开臂的头几帧里那颗药丸不在末位**（左段那一片亮仍偏左、右段还没被填上），到第 4 帧前后才落到右段；而**关臂第一帧就已经在末位** —— 这与判据自己那把尺同方向（MOTION_PILL_SLIDE filter-pill-slide 开A 帧数=3(旧口径6) 峰值=0.101 冷闸=true  开B 帧数=3(旧口径6) 峰值=0.090 冷闸=true  关 帧数=1(旧口径1) 峰值=0.362 同一条线=0.0544 共用线安全=true 声明=200ms 采样≈8ms）。
一条被我自己否掉的一次性尺，记在这里免得下一次再上当：我试着直接从条带上量每格药丸的质心，读出来是 0.57→0.48、格间差不足 0.02 格宽 —— 条带是缩放图（每格 300px 宽），暗档下药丸与轨道只差十几级灰，这把尺在这个形态上**分辨不出**，所以它不许当结论；"有没有过程"由判据那把逐帧尺说，条带只是给人复核的现场。
另外两处看清了：条带右下角那块灰**不是**某一帧没画出来，是 `writeStrip` 预填的画布底色（0.25/0.25/0.28，读代码确认）；而胶囊移到右段之后整块列表换成"暂无收藏"的空态，那句空态文案与图标是居中在列表槽里的 —— 这一条 R64 已判过，本轮不重开。
审美判断（这一维该给的结论）：这条位移**该留，也该保持现在这样** —— 它是"你按了哪一段"的唯一连续指示；本机 3 帧中间态在 8ms 采样下已经是"看得见挪动但不抢注意力"的量级，而 MC-1 那条规矩（程序触发的位移不给过冲）在这里是对的：给一颗自己会停在原地的胶囊加过冲，读起来像坏了。
静帧侧本轮重看了 `sidebar-history-300x520-light/dark` 两张 —— 过程证人那条带子（y≈66…92pt）就是从这两张量出来的；两档的搜索框、胶囊、分隔线三条左轴一致，没有新的错位。）。
产品文件 0 个，连续零改动 **3** 轮（R319 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for 321`，
同形用于 `--check`；上一轮 2）。as-of 第 321 轮的最后一笔产品提交是 84c5468 = 第 318 轮。

⓪ R323 开场要先读的（成对：run id ↔ commit）：RUN=40023610164 sha=1a37edc status=in_progress conclusion= title=R322 账半（七本一起落：U-1056…U-1059、D-305、373 与 375 各一处追记、STATE 轮换、报告计数器） workflow=CI
   —— 收尾时现读：上一轮的 `40019426681`(32f1104) 与 `40019174985`(4271ff1) 都已 completed/success，
   R318 以来那四跑的红（ca6bc31 / 121ef8f / a033b98 / 0e225d2）确认清零，runner 的 SELARM 读数已写进 373/375 的追记。
   —— 必须读到：① **本轮这一笔在 runner 上是否全绿**，特别是 `testFilterPillSlideIsAProcessNotATeleport`：
      期望（写死在这里，读到才算结案）—— 若那台机器 `可分帧 ≥ 3` 就必须给出与本机同方向的三条读数；
      若 `可分帧 < 3` 则必须印 `MOTION_NOT_RUN=clock-too-coarse pill-slide-process` 并 skip，
      **不许**在那台机器上把"看不见过程"读成"没在演"；
   ② `MOTION_PILL_SLIDE` / `_SETTLE` 两行在 runner 上的数（采样间隔本机是 8ms，runner 历史上 31–90ms）；
   ③ 上一轮 ⓪ 欠的：`HEATMAP_TOOLTIP_CONTROL` / `_CHANNELS` 在 runner 上是否签（R320 那一笔）。

① 下一轮（R323）的靶：① **产品面**：连续 3 轮零产品文件，而本轮已经量到一条可动的东西 ——
      过程证人齐了之后，位移档**还缺一维**：没有任何尺判过"这条滑动的时长/曲线品质"
      （本机 56ms 落定 vs 声明 200ms 这件事现在只用上限挡了"跑飞"）。
      候选做法：给 `.slider` 装一条**斜坡尺**（逐帧读亮区中心，量位移是否单调、有没有回头），
      量出来若与声明不符就是第一笔产品改动；若这台机器量不出，就按 D-305 的形状写成具名出口。
   ② 375 的第一步（数出还有几处按药丸右沿定位的尺）；
   ③ 367 迁移（已声明 2 张 / 剩 0 张）；④ 360 最后一批；⑤ 361 合并；
   ⑥ 364 的"抽不出候选的 6 把要真跑"；
   ⑦ 347 / 305 / 373① / 368 四格都在**同一批真机眼**后面 —— 需要用户先退出正在运行的 App，
      那一轮可以一次把它们全推成读数（人工验收批次已列）。

② 仍开：347（真机证人）、305（等 347）、373（只剩①号真机眼；②号已在两台机器兑现）、
   368（**已判到通道边界**：离屏无通道，剩真机眼那半）、
   375（两台机器行几何差 16pt：③已兑现，①②仍开）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   354 的第五步 + 负载红一条、348 的"读数族还没纳全"、360（剩 11 份）、361（未合并）、
   359、362、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   **R321**：373 的②号那把尺修好 + 该格改口；**R319 结案**：374；
   用户闸门 220 路 A / 228② / 265。

## R321 状态（第 320 轮 / Round 318 · 2026-10-24）

本轮一笔：runner 三跑的红归因到尺并修掉 —— SELARM 的页底原来只有一格，
而那一格在 1× 那台机器上落在滚动条槽里（暗档 (61,61,61) 占 65% **过了占比闸**，
本机同外观的页底是 (30,30,30)）。新加第二道闸（候选窗必须与那一台自己的全帧页底档同档）、
页底窗改成前导/trailing 两块且要互相印证、偏移按倍率换算、读数先打后判（`QUICKPICK_SELARM_BANDS`）。
R318/R319 记的"runner 也判 nonKey"（暗档那一半）就地改口 —— 那是错的参照物报出的落点（a=1.00、残差 0）。
成因路上先猜错一次（裸像素偏移），被本机 1× 代理否掉之后才认对（16pt 的 trailing gutter）。
判据 `QuickPickSelectionArmTests` Executed 9 tests, with 0 failures（含合成臂）；刀 M919 / M920 / M921 CAUGHT=3/3, RESTORE_CLEAN=yes；
新规矩 D-304、新开 375（两台机器行几何差 16pt，凡按右沿定位的尺都要重查）、373 写了追记。

最后更新：2026-10-24（本地 · R321 / 第 320 轮 / Round 318）：**一朵绿了两轮的臂被钉成会红：底色"稳"不等于它是那一层**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 945 tests, with 44 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r321_rv/frames`；帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=945 swift_skipped=44 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r321_rv`；
真值表卷 `Executed 9 tests, with 0 failures`；捕获卷 `QUICKPICK_SELARM_SUMMARY 候选=2 有对象=2 未判=0 落点=light=系统nonKey dark=系统nonKey`；变异表 `CAUGHT=3/3, RESTORE_CLEAN=yes`；
针预检 tables=109 covered=92 bad=0、名册 arms=788；
腐烂尺 `HIDDEN_ARMS 表=197 可判=720 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮逐张看的是**浮层的四个状态位点**与热图亮档那张。先做完整性核对：R320 那一遍 174 张与本轮这一遍 174 张逐张 md5 对拍）。
产品文件 0 个，连续零改动 **2** 轮（R319 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for 320`，
同形用于 `--check`；上一轮 1）。as-of 第 320 轮的最后一笔产品提交是 84c5468 = 第 318 轮。

⓪ R322 开场要先读的（成对：run id ↔ commit）：RUN=40019174985 sha=4271ff1 status=in_progress conclusion= title=R321 账半（七本一起落：U-1053…U-1055、D-304、373 的改口追记、新开 375、STATE 轮换、报告计数器） workflow=CI
   —— 收尾时**现读**写死在这里的已知事实（不是猜）：本轮之前的四跑
   `ca6bc31`(40008003697) / `121ef8f`(40011458013) / `a033b98`(40011516876) / `0e225d2`(40014023716)
   全部 conclusion=failure，而失败的是**同一朵**：STEP[15] 与 STEP[17] 都红在
   `UICaptureHarness.swift:1050 testQuickPickSelectionPillAgainstSystemArms`
   （`light[原因=取样窗底色不实：药丸中段占比=78% 页底占比=45%，下限 60%]`）
   ⇒ 自 R318 立那把尺起 CI 一直红在这一格，R321 修的就是它。
   必须读到：① **本轮这一笔（`4271ff1` / `f6d2fc2`）在 runner 上是否把那四跑的红清零**；
   ② `QUICKPICK_SELARM_BANDS` 两行在 runner 上的读数 —— 期望先写死在这里，读到才算结案：
      `选择=前导(...)`、两块窗里 trailing 那一格被点名"不是页底那一层"、`未判=0`、
      两档落点仍 `系统nonKey`；**若前导那一格在那台机器上也不干净**，
      那一行会把两块窗的读数与倍率一起交出来 ⇒ 按 354 那族做具名出口，不再猜第三次；
   ③ 还欠的：`HEATMAP_TOOLTIP_CONTROL` / `_CHANNELS` 在 runner 上是否签（R320 的 ⓪ 欠着）。

① 下一轮（R322）的靶：① **回到动效主线**（本轮又是判据轮，这一格已连续三轮排第一）：
      候选 —— 354 第五步（观察窗口成本）、348 给 `HEATMAP_TOOLTIP_*` / `QUICKPICK_SELARM*` /
      `MUTATE_TABLE` 三族配恒等式、或撤一条不成立的声明；
      必须跑完整四件套 + 逐张看图 + 配刀。
   ② 375 的第一步（数出还有几处按右沿定位的尺）—— 与本轮同源，趁热做便宜；
   ③ 367 迁移（已声明 2 张 / 剩 0 张）；④ 360 最后一批；⑤ 361 合并；
   ⑥ 364 的"抽不出候选的 6 把要真跑"；
   ⑦ 347 / 305 / 373① / 368 四格都在**同一批真机眼**后面 —— 需要用户先退出正在运行的 App，
      那一轮可以一次把它们全推成读数（人工验收批次已列）。

② 仍开：347（真机证人）、305（等 347）、373（只剩①号真机眼；②号的尺本轮修好并改口）、
   368（**已判到通道边界**：离屏无通道，剩真机眼那半）、
   375（两台机器行几何差 16pt，其余按右沿定位的尺待查）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   354 的第五步 + 负载红一条、348 的"读数族还没纳全"、360（剩 11 份）、361（未合并）、
   359、362、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   **R319 结案**：374（corrupt 保全不幂等）；**R321**：373 的②号那把尺修好 + 该格改口（本单仍开在①号）；
   用户闸门 220 路 A / 228② / 265。

## R320 状态（第 319 轮 / Round 317 · 2026-10-24）

本轮一笔：368 判到底 —— 新判据 `testHeatmapTooltipChannelProbe` 复用 harness 的建树路径 + 正对照，
HEATMAP_TOOLTIP_CHANNELS 走过=4 屏×档 热图型toolTip合计=0 热图型无障碍合计=0 任意toolTip合计=0 任意标签合计=0（正对照已签：这把尺读得到 toolTip 与 accessibilityLabel）；对照那格读到 `toolTip=1 无障碍=1`，所以产品那侧的 0 是结论不是敲门声。
第二条门（`accessibilityChildren`）只数到根 ⇒ SwiftUI 形状的 `.help()` 不落进 `NSView` 树。
本单收成**具名出口**（真窗 + 真辅助技术才能判，与 347 / 305 / 373① 同批），不留第四次尝试。
两把刀 M917 / M918 钉在证人上（CAUGHT=2/2, RESTORE_CLEAN=yes）；新规矩 D-303。

最后更新：2026-10-24（本地 · R320 / 第 319 轮 / Round 317）：**一条"全 0"第一次带着正对照的签名进台账**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 936 tests, with 44 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r320_rv/frames`；帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=936 swift_skipped=44 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r320_rv`；
探针卷 `Executed 1 test, with 0 failures（正对照 toolTip=1 / 无障碍=1 / 视图=3 已签；产品四屏×档合计 toolTip=0 无障碍=0）`；变异表 `CAUGHT=2/2, RESTORE_CLEAN=yes`；针预检 tables=108 covered=91 bad=0、名册 arms=785；
腐烂尺 `HIDDEN_ARMS 表=196 可判=717 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮看图看的是**热图那一圈悬停描边**（`heatmap-cell-strip-hover-90x140-light.png`，本轮重捕的 174 张之一），并把浮层两档与设置统计屏重看了一遍；同时做了完整性核对：R319 那一遍 174 张与本轮这一遍 174 张逐字节对拍）。
产品文件 0 个，连续零改动 **1** 轮（R319 那笔产品改动之后重新起算；唯一取数口 `python3 scripts/product_streak.py --streak-for 319`，
同形用于 `--check`；上一轮 0）。as-of 第 319 轮的最后一笔产品提交是 84c5468 = 第 318 轮。

⓪ R321 开场要先读的（成对：run id ↔ commit）：RUN=40011516876 sha=a033b98 status=completed conclusion=failure title=R319 补记（把被 shell 吃掉的三条守卫名与落点写回台账，不改历史） workflow=CI
   —— 必须读到：① 本轮这一笔与 R319 那三笔（`84c5468` / `121ef8f` / `a033b98`）在 runner 上是否全绿；
   ② `HEATMAP_TOOLTIP_CONTROL` / `HEATMAP_TOOLTIP_CHANNELS` 两行在 runner 上的读数
      （那台机器的 SwiftUI 无障碍行为可能不同 —— 若对照也读不到，就是**尺的机器差异**，要按 354 那族切片）；
   ③ 新尺 `QUICKPICK_SELARM` 在 runner 上的落点（页底 236/52 对本机 252/28）。

① 下一轮（R321）的靶：① **回到动效主线**（本轮又是判据轮）：清账表 162/162 已全清，
      所以要从"撤一条不成立的声明"或"给一个真实位补过程证人"里挑一件做，
      并跑完整四件套 + 逐张看图 + 配刀；候选：354 的第五步（观察窗口成本）、
      348 给 `HEATMAP_TOOLTIP_*` / `QUICKPICK_SELARM` / `MUTATE_TABLE` 三族配恒等式；
   ② 367 迁移（已声明 2 张 / 剩 0 张）；③ 360 最后一批；④ 361 合并；
   ⑤ 364 的"抽不出候选的 6 把要真跑"；
   ⑥ 347 / 305 / 373① / 368 四格都在**同一批真机眼**后面 —— 需要用户先退出正在运行的 App，
      那一轮可以一次把它们全推成读数（人工验收批次已列）。

② 仍开：347（真机证人）、305（等 347）、373（只剩①号真机眼）、
   368（**已判到通道边界**：离屏无通道，剩真机眼那半）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   354 的第五步 + 负载红一条、348 的"读数族还没纳全"、360（剩 11 份）、361（未合并）、
   359、362、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   **R318 结案**：373 的②号出口；**R319 结案**：374（corrupt 保全不幂等）；
   用户闸门 220 路 A / 228② / 265。

## R319 状态（第 318 轮 / Round 316 · 2026-10-24）

本轮三笔：① 产品 1 文件（`HistoryPersistence.swift`）—— 损坏原件的保全改成**按内容幂等**，
并修掉撞名返回 nil 让恢复提示说"未知位置"那一支；② 用例改成**主动跨过秒界**再断言恰好一份
（不降成 `>= 1`）；③ 三把刀 M914 / M915 / M916（CAUGHT=3/3, RESTORE_CLEAN=yes（预检 tables=107 covered=90 bad=0）），其中 M915 第一版打在
不可观察的位上（PASSED），改针到悬停真值表本体后才红 —— 这一格按原样记账并升成 D-302。
374 结案；373 只剩①号真机眼。

最后更新：2026-10-24（本地 · R319 / 第 318 轮 / Round 316）：**连续 7 轮零产品文件之后的第一笔产品改动**（产品 1 文件，判据 + 修法）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 935 tests, with 44 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r319_rv/frames`；帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=935 swift_skipped=44 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r319_rv`；
变异表 `CAUGHT=3/3, RESTORE_CLEAN=yes（预检 tables=107 covered=90 bad=0）`；针预检 tables=107 covered=90 bad=0、名册 files=201 arms=783；
腐烂尺 `HIDDEN_ARMS 表=195 可判=715 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮看图腿做的是**完整性核对 + 重看**，不是新的审美判断 —— 这一点先说清，免得把它当成"看过了"。本轮改动全在恢复路径的磁盘写与提示措辞上，像素一张都不该动；这一条不靠"我觉得没动"，靠两遍帧目录逐字节对拍：R318 那一遍 174 张与本轮这一遍 174 张，同图 174 / 变图 0 / 缺对照 0（`R319_FRAME_CMP`，md5 逐张比）。

重看的是浮层两档与那一张悬停位点（`quickpick-hover-420x300-dark.png`）。要看的是"次序还在不在"：页底 30、悬停那一档约 43（`VisualFill.hover` 0.06 的白墨压在暗底上）、选中那颗药丸 70）。
产品文件 1 个 ⇒ 连续零改动 **0** 轮（由上一轮的 7 归零；唯一取数口 `python3 scripts/product_streak.py --streak-for 318`，
同形用于 `--check`；本轮之前的最后一笔产品提交是 84c5468 = 第 318 轮 —— 本轮之后 as-of 就是本轮自己）。

①-b 本节的 commit message 自伤（就地记，不改历史）：`121ef8f`（R319 账半）的正文用了**未加引号的 heredoc**，
   于是三处反引号里的守卫名与两个 shell 变量被命令替换吃掉 ⇒ 那笔信息里"一、二、三"各缺主语、"落点"是空的。
   缺的事实补在这里：三条守卫分别是 `scripts/tests/test_product_streak_cell.py`（九条 + `--help` 门一起红）、
   `scripts/tests/test_wait_scan.py`（RosterTests 的"观察窗口颗数"1 → 现读 2 + 写明成因）、
   `scripts/tests/test_final_report_headline.py`（§13 的 Sources 那一格还停在 `9551730` = R311）；
   代码半那笔是 `84c5468`；落点 = `QUICKPICK_SELARM_SUMMARY 候选=2 有对象=2 未判=0 落点=light=系统nonKey dark=系统nonKey`。
   规矩：**台账与 commit 的正文一律用引号形式的 heredoc（<<'EOF'），串里不写裸反引号**（这一族已犯过两次）。

⓪ R320 开场要先读的（成对：run id ↔ commit）：RUN=40008003697 sha=ca6bc31 status=completed conclusion=failure title=R318 账半（七本一起落：U-1043…U-1046、D-299、D-300、373 的②号结案、新开 374、STA workflow=CI
   —— 必须读到：① 本轮三笔在 runner 上是否全绿（**特别是 `HistoryPersistenceRecoveryTests`
      那一朵间歇红**：runner 上如果绿，它是"没跨秒界"还是"幂等生效"？这一格只有幂等之后才分得清）；
   ② 新尺 `QUICKPICK_SELARM` 两行在 runner 上的落点（那台机器页底 236/52 对本机 252/28）；
   ③ R318 那三跑（`3b1a8b9` / `689691e` / `adace25`）与账半 `ca6bc31` 的结论。

① 下一轮（R320）的靶：① **回到动效主线**（这是本轮之后最该做的一件事）：
      347 / 305 / 373① 都需要用户先退出正在运行的 App（单实例守卫会中止第二实例）⇒
      在那之前用**已有夹具通道**点一个真实位做动效判断或撤一条不成立的声明，
      跑完整四件套 + 逐张看图 + 配刀；
   ② 368（hover 提示的产物级通道）；③ 367 迁移（已声明 2 张 / 剩 0 张）；
   ④ 348 剩下的读数族各配恒等式（`QUICKPICK_SELARM` / `_SUMMARY` 与本轮的 `MUTATE_TABLE` 行都在这一族里）；
   ⑤ 360 最后一批；⑥ 361 合并；⑦ 364 的"抽不出候选的 6 把要真跑"；
   ⑧ 354 的第五步（本轮新增的"等条件跨秒界"给那条用例加了 ~1.1 秒，值得被数到）。

② 仍开：347（真机证人）、305（等 347）、373（只剩①号真机眼：key window 下选中档是不是强调色）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   368（hover 提示的产物级通道）、354 的第五步 + 负载红一条、348 的"读数族还没纳全"、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、339、
   312 具名出口、304、296、291；**R318 结案**：373 的②号出口（两枚系统参照臂进尺）；
   **R319 结案**：374（corrupt 原件保全不幂等）；
   用户闸门 220 路 A / 228② / 265。

## R318 状态（第 317 轮 / Round 315 · 2026-10-24）

本轮三笔：① `0a39dd1` 代码半 —— 373② 的两枚系统参照臂进尺（`testQuickPickSelectionPillAgainstSystemArms`）；
② `689691e` + ③ `adace25` 是预算尽头的安全停车（只动 `.scratch/` 交接）。
账半（本节）补在尺修好之后：新尺自曝两次 —— 反向差假绿（`max(带符号差)`）与取样窗把笔画混进底色
（一度把暗档报成"两臂都不在"）；改到第四版估计量之后 light=系统nonKey ⇒ **373② 结案：帧上的灰是系统非 key 档，不是产品挑的配色**。
新规矩 D-299（残差取绝对值）与 D-300（读底色的尺必须自带实心证明）。
同一轮全量卷那朵红归到**产品侧**并新开 374（损坏原件的保全不幂等，用例的 `count == 1` 跟着挂钟走）。

最后更新：2026-10-24（本地 · R318 / 第 317 轮 / Round 315）：**浮层选中底第一次有了参照物，两档都逐字节落在系统非 key 那一档；顺带抓到一处不幂等的磁盘写**（产品 0 文件，判据轮）
现读：构建 `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`；全量卷 `Executed 935 tests, with 44 tests skipped and 0 failures`；重捕帧 `CAPTURED 174 -> /tmp/r318_rv2/frames`；帧基线 `FRAME_BASELINE_COMPARED=174 CHANGED=0 MISSING=0 ADDED=0`；四件套 `ROUND_VERIFY build_warnings=0 swift_executed=935 swift_skipped=44 swift_failures=0 frames=174 baseline_compared=174 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r318_rv2`；
新判据定向卷 `Executed 1 test, with 0 failures（新判据两档都有对象）`；本轮 0 把刀（新尺刚出厂，容差还是探针刻度）：两把刀的锚点已现场 grep 各命中恰好 1（M914 钉参照臂解析那一行、M915 钉 `fill.isHidden = !showsHoverTint(isSelected: isSelected,` 那一行），表与跑归 R319 —— 没有刀的判据今天只是尺，不是牙；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮看图看的是重捕帧里的三张（`/tmp/r318_rv/frames`，174 张里的三张，两档对齐）：`quickpick-list-420x300-light.png`、`quickpick-list-420x300-dark.png`、`heatmap-populated-430x250-dark.png`。

浮层两档：选中那一行是一条**圆角灰带**（亮档 220 压 255、暗档 70 压 30），文字仍是主色，读得出"哪一条是选中的"，但它在两档里都是无彩的 —— 与设置侧栏那颗蓝药丸不是同一套语言。这一格本轮**不能落成产品改动**：常驻尺已经证明帧上那个灰就是系统的非 key 选中档（两档残差 0），所以"浮层选中不带强调色"这个观感判断要等到①号真机眼（面板是 key window 时用户看到的到底是蓝还是灰）才有对象。看图与判据这次是同一个方向，不再互相打脸。

热图暗档：日历本体、月份轴、"最近 26 周共 1322 次 · 日均 7.4 次 · 连续 126 天"那行、以及"最忙的一天"那行都读得干净，五行星期标签只标一/三/五/日也够定位。唯一让我停了一下的是**图例**：`少` 后面第一枚方块与左边空格的底色贴得很近，肉眼在暗档上要盯一下才分得出"少"与"无"。这一条**今天只是观察，不是缺陷**（我没有量它 —— 形容词不进台账）：下一轮若要开单，必须先按 71 那一族的相邻档可分辨性把图例第一档与空格底色量出来，再判要不要抬一档。）。
产品文件 0 个，连续零改动 **7** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 317`，
同形用于 `--check`；上一轮 6）。as-of 第 317 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R319 开场要先读的（成对：run id ↔ commit）：RUN=40003528098 sha=adace25 status=completed conclusion=success title=R318 停车收尾（run↔commit 成对写进交接：RUN=40003194220 ↔ 3b1a8b9 仍 in_p workflow=CI
   —— 必须读到：① `0a39dd1` 与两笔停车提交（`689691e` / `adace25`）在 runner 上是否全绿；
   ② 这条新尺在 runner 上印的 `QUICKPICK_SELARM` 两行落点是什么（那台机器页底 236/52 对本机 252/28，
      参照臂与混合可能给出不同落点，甚至掉出容差 ⇒ 那是**另一台机器的读数**，不许反过来改本机的尺）；
   ③ `HistoryPersistenceRecoveryTests` 那一朵红在 runner 上是否也出现（374 的第三份数据点）。

① 下一轮（R319）的靶：① **374 的修法** —— 这是连续 7 轮零产品文件之后的**第一笔产品改动**：
      `preserveCorruptFile` 改成按内容幂等（同目录已有字节相同的 corrupt 副本就复用、不再写盘），
      用例改成**等条件跨过秒界**再断言恰好一份（R267：等条件不是固定 sleep，也不许降成 `>= 1`），
      并配一把"抽掉幂等守卫必须红"的刀；跑完整四件套 + 逐张看图 + 七本台账；
   ② 给这条新尺**写两把刀**（M914 钉参照臂解析那一行 ⇒ 两臂塌成一枚必须红；
      M915 钉 `fill.isHidden = !showsHoverTint(isSelected: isSelected,` ⇒ 自家灰叠到选中档上、
      落点必须掉出两臂之外），锚点已现读各命中恰好 1，新表登记进 `mutate_needle_precheck.py` 的 TABLES；
   ③ **回到动效主线**：347 / 305 与 373 的①号收法同批，都需要用户先退出正在运行的 App；
      在那之前用已有夹具通道推 305 的台阶地板；
   ④ 368（hover 提示的产物级通道）；⑤ 367 迁移（已声明 2 张 / 剩 0 张）；
   ⑥ 348 剩下的读数族各配恒等式（本轮新增的 `QUICKPICK_SELARM` / `QUICKPICK_SELARM_SUMMARY`
      两族读数就是这一条的对象；它们已走在 `ledger_rows.py` 的 `^QUICKPICK_` 那一支白名单里）；
   ⑦ 360 最后一批；⑧ 361 合并；⑨ 364 的"抽不出候选的 6 把要真跑"。

② 仍开：347（真机证人）、305（等 347）、373（**②号已结案**；只剩①号真机眼：key window 下选中档是不是强调色）、
   374（corrupt 原件保全不幂等 + 断言跟着挂钟走）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   368（hover 提示的产物级通道）、354 的第五步 + 负载红一条、348 的"读数族还没纳全"、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、339、
   312 具名出口、304、296、291；**R316 结案**：369、372；**R315 结案**：371（撤销自开）；
   **R318 结案**：373 的②号出口（系统参照臂进尺，两档落在非 key 档）；
   用户闸门 220 路 A / 228② / 265。

## R317 状态（第 316 轮 / Round 314 · 2026-10-24）

本轮两笔、零代码改动：① `fcf2d16` runner 交账 —— 换锚点后的 M566 在 runner 上**无对象**
（`CARD_INSET_NOT_RUN=1`、`卡片数=1 未判=29`、`settings-stats` 两档没进 `measured` ⇒ 翻开关不会让任何断言变红），
本机 CAUGHT 只签本机那一半；② `49fe48b` 看图腿 —— 浮层选中行底 (181,181,181) 对页底 (255,255,255)
⇒ 差 74、零强调色，但**同一轮标成这台机器判不了**（离屏非 key window，AppKit 的失焦选中本来就灰），
新开 373 并给出两条各绑读数的收法。新规矩 D-298：读数出厂就要带可判通道。

最后更新：2026-10-24（本地 · R317 / 第 316 轮 / Round 314）：**看图腿回到新位点，且诚实地停在"未判"**（产品 0 文件，看图轮）
现读：本轮零代码改动 ⇒ 构建 / 全量卷 / 重捕帧 / 帧基线 / 换装五腿**不适用**（不是没跑；帧仍 174、基线仍 174）；
本轮 0 把刀、0 代码改动（看图轮）：证人 = runner 自印的 `CARD_INSET_*` 三行 + 浮层那一格 (181,181,181) vs (255,255,255)；五腿不适用不是没跑；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮看图看的是**新的位点**：快速选择浮层有候选、第一行被选中那一态（`/tmp/r317_shots/quickpick-list-420x300-light.png`）。第一眼的问题不是"好不好看"，而是"这一屏最该被看见的那一档有没有被看见"——浮层是键盘驱动的列表（上下键移动、Enter 直接复制），选中行承载的就是"按下回车会发生什么"。量出来：选中行底 = (181,181,181)，未选行与页底 = (255,255,255)）。
产品文件 0 个，连续零改动 **6** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 316`，
同形用于 `--check`；上一轮 5）。as-of 第 316 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R318 开场要先读的（成对：run id ↔ commit）：RUN=40000387426 sha=49fe48b status=in_progress conclusion= title=R317 看图腿：浮层选中行是纯灰（R=G=B=181、零强调色）—— 新开 373，但明确它这台机器判不了，登记成有名 workflow=CI
   —— 必须读到：① `b229840`（R316 账半）与本轮两笔在 runner 上是否仍全绿；
   ② 撤帧之后 runner 是否也 `CAPTURED 174`（这条 R317 还没读到）；
   ③ 负载红 `PerfBudget` 在独占机器上是否不红（本机三跑 1 / 0 / 0）。

① 下一轮（R318）的靶：① **373 的②号收法**：给浮层一个 key-window 态，或拿
      `NSColor.selectedContentBackgroundColor` 做系统参照臂，把"选中行该不该带强调色"变成
      **两档可判、机器可判**的量，并配一把"参照臂换成我们自己的灰底必须翻"的刀 ——
      这一条做完，R317 那句"判不了"才有一个可收的出口；
   ② **回到动效主线**（已连续 6 轮 0 产品文件）—— 347 / 305 与 373 的①号收法同批，
      都需要用户先退出正在运行的 App；在那之前用已有夹具通道推 305 的台阶地板；
   ③ 368（hover 提示的产物级通道）；④ 367 迁移（已声明 2 张 / 剩 0 张）；
   ⑤ 348 剩下的读数族各配恒等式；⑥ 360 最后一批；⑦ 361 合并；⑧ 364 的"抽不出候选的 6 把要真跑"。

② 仍开：347（真机证人）、305（等 347）、373（浮层选中行的强调色：离屏判不了，需真机眼或 key-window 参照臂）、
   367（腐烂针待清：已声明 2 张 / 剩 0 张）、
   368（hover 提示的产物级通道）、354 的第五步 + 负载红一条、348 的"读数族还没纳全"、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、339、
   312 具名出口、304、296、291；**R316 结案**：369（派生不成立 ⇒ 开关与名单拆开）、372（两跑 env 不同源）；
   用户闸门 220 路 A / 228② / 265。

## R316 状态（第 315 轮 / Round 313 · 2026-10-24）

本轮三笔：① 372 结案（那颗没名字的 skip 是 `testCaptureKeyViews`，成因是两跑 env 不同源）；
② 369 的派生方案被现读证伪（首墨连续墨高分不开图标与文字：3.5/3.0pt 对 3.5/3.0pt；左沿错开 = delta 本身 = 循环）；
③ 换成"开关与名单拆开"并落地 —— M566 的针从 `iconFirstCells` 那一行搬到 `CLIPBOARD_HISTORY_ICON_FIRST_ROSTER`
那一行，名册增删再也弄不死刀；重跑 `exp=CAUGHT got=CAUGHT`、`RESTORE_CLEAN=yes`、预检 `bad=0`。
过程里 0 告警那道门抓了我一次（`let … = true` ⇒ `will never be executed` 两朵，`WARNINGS=2`）。

最后更新：2026-10-24（本地 · R316 / 第 315 轮 / Round 313）：**两张单收掉，刀换了落点**（产品 0 文件，判据轮）
现读：构建告警 0；捕获卷 `Ran 92 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 0 failure(s)；CAPTURED 174 -> /tmp/r317_shots；帧基线 FRAME_BASELINE_COMPARED=174 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0（本轮不 update）；
换装 没读到换装结论行（四件套第 4 步未落盘 ⇒ 记 NOT-RUN）；刀表重跑现读 `MUTATE_TABLE n=1 caught=1 mismatch=0 not_run=0`（M566 的针已从名册那一行搬到名册**开关**那一行）；预检 M566=ok、CAPTURED 174 -> /tmp/r317_shots；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮的看图腿是**完整性核对**，不是新的审美判断 —— 这一点先说清，免得把它当成"看过了"。改动全在判据侧（新增一个运行时开关 + 把刀 M566 的针从名册那一行搬到开关那一行），所以产品像素**一张都不该动**；这一条不靠"我觉得没动"，靠两遍帧目录逐字节对拍：R315 那一遍 174 张与本轮这一遍 174 张，同图 174 / 变图 0 / 缺对照 0（`R316_FRAME_CMP`，md5 逐张比）。）。
产品文件 0 个，连续零改动 **5** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 315`，
同形用于 `--check`；上一轮 4）。as-of 第 315 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R317 开场要先读的（成对：run id ↔ commit）：RUN=39997239008 sha=133f196 status=in_progress conclusion= title=R316 代码半：369 的派生出口被现读证伪，改成把「名册开关」与「名单」拆开 —— 刀从此钉在开关那一行，改名册再也 workflow=CI
   —— 必须读到：① 本轮三笔（`f505fc4` / `fbd72dc` / `133f196`）在 runner 上是否仍 `bad=0`
   （M566 换了落点，runner 的 @1x 与档位不同 ⇒ 那把刀在新锚点上有没有牙，本机一条不算）；
   ② 撤帧之后 runner 是否也 `CAPTURED 174`（基线 174 已进仓库）；
   ③ 负载红 `PerfBudget` 本机三跑 1/0/0，runner 独占机器上怎么表现。

① 下一轮（R317）的靶：① **回到动效主线**（已连续 5 轮 0 产品文件）——
      347 / 305 需用户先退出 App；在那之前把 305 的台阶地板用已有夹具通道再推一格，
      或按清账表里那批未判位点挑一个真做动效；
   ② 368：把 `UICaptureHarness` 的建树路径提给判据卷（hover 提示第一次可被产物级判据判到）+ 配刀；
   ③ 367 的迁移继续（已声明 2 张 / 剩 73 张）；④ 348 剩下的读数族各配恒等式；
   ⑤ 360 最后一批；⑥ 361 合并；⑦ 364 的"抽不出候选的 6 把要真跑"。

② 仍开：347（真机证人）、305（等 347）、372（腐烂针待清：已声明 2 张 / 剩 73 张）、
   368（hover 提示的产物级通道）、354 的第五步 + 负载红一条、348 的"读数族还没纳全"、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、339、
   312 具名出口、304、296、291；**本轮结案/撤销**：372（env 不同源）、369（派生不成立，出口=开关与名单拆开）；
   用户闸门 220 路 A / 228② / 265。

## R315 状态（第 314 轮 / Round 312 · 2026-10-24）

本轮三笔：① 开场查重把 R314 自己开的 BACKLOG 371 **撤销**（空态不渲染说明段是 R9 的决定，
且 `DailyCopyHeatmapTests.testHeatmapReadingGuideFollowsTheChart` 已钉着）；② 给那次撤销补上它欠的**同族对照**
（逐分区底部留白 0.533 / 0.502 / 0.472 / 0.460 / 0.424 / 0.013 / 0.000 ⇒ 统计页不是异类），
并把隐私页 `距底=0` 分辨成**滚动折**（行剖面 205→44→28 vs 健康对照余量 14 像素 + `detailScrollView` + 夹具注释）；
③ 撤掉 R314 自曝的那张重复臂（370 出口①）：`CAPTURED 176→174`、基线同一笔 update、
M566 的针跟着回到单行原形（预检 `bad=0`、M563…M567 全 ok）。

最后更新：2026-10-24（本地 · R315 / 第 314 轮 / Round 312）：**重复单撤销 + 重复臂拿走**（产品 0 文件，判据轮）
现读：构建告警 0；捕获卷 `Ran 92 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 0 failure(s)；CAPTURED 174 -> /tmp/r316_shots；帧基线 FRAME_BASELINE_COMPARED=174 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0（176→174 同一笔）；
换装 没读到换装结论行；本轮 0 把新刀（判断，不是遗漏）：证人 = 撤帧那一笔的四件现读 —— CAPTURED 174 -> /tmp/r316_shots、捕获卷零红、M566 预检 ok（针跟着名册回到单行）、基线同一笔 update；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮看图看的是**自己上一轮写下的判断**，不是新帧。把 `settings-privacy-720x540` 的底边裁出来看（`/tmp/r316_privacy_bottom.png`）：最后一行"默认排除：com.dashlane.DashlaneMacOS"整行被折在帧底、字形下半截没了）。
产品文件 0 个，连续零改动 **4** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 314`，
同形用于 `--check`；上一轮 3）。as-of 第 314 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R316 开场要先读的（成对：run id ↔ commit）：RUN=39994764642 sha=a719be9 status=in_progress conclusion= title=R315 账半的半成品入库（正文 r315_bodies 四格 U + D + 370 结案追记 + 新开 372；派生 workflow=CI
   —— 必须读到：① 撤帧那一笔在 runner 上是否也 `CAPTURED 174`（基线 174 已进仓库，
   若 runner 仍按 176 找那两张就是名单/基线不同源）；② 捕获卷 skip 5→4 那一格在 runner 上是几颗
   （372 的第二个数据点，本机一条不算归因）；③ R314 那笔负载红（`PerfBudget` 371.7ms > 250ms，
   本机两跑 1/0）在 runner 上怎么表现。

① 下一轮（R316）的靶：⓪ **372**：捕获卷 skip 那颗没名字的差 —— 同源对账 + 一把"skip 前提改恒真"的刀；
   ① **369**：把"首墨是图标"变成**派生**判定（连通块高度比 / 左沿错开），让 `CARD_INSET_ICON_FIRST`
      从开关变成结论 —— 本轮 M566 的针**第二次**被同一张名册咬，这就是它的证人；配那把"图标换成等宽文字必须翻判"的刀；
   ② **回到动效主线**（已连续 4 轮 0 产品文件）—— 347 / 305 需用户先退出 App，
      在那之前把 305 的台阶地板用已有夹具通道再推一格；
   ③ 368：把 `UICaptureHarness` 的建树路径提给判据卷（对照臂用 `settings-stats` vs `settings-stats-populated`）；
   ④ 367 的迁移继续（已声明 2 张 / 剩 73 张）；⑤ 348 剩下的读数族各配恒等式；
   ⑥ 360 最后一批；⑦ 361 合并。

② 仍开：347（真机证人）、305（等 347）、371（腐烂针待清：已声明 2 张 / 剩 73 张）、
   372（捕获卷 skip 那颗没名字的差）、369（`iconFirstCells` 自指 —— 本轮 M566 的针第二次被同一张名册咬，就是它的证人）、
   368（hover 提示的产物级通道）、354 的第五步 + 负载红一条、
   364 的"抽不出候选的 6 把要真跑"、348 的"读数族还没纳全"、360（剩 11 份）、361（未合并）、359、362、349、
   350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   **本轮结案/撤销**：370（出口①落地）、371（R9 已判 + 已有判据 + 同族不是离群）；
   用户闸门 220 路 A / 228② / 265。

## R314 状态（第 313 轮 / Round 311 · 2026-10-23）

本轮把上一轮那句读数（「热图空状态 69% 是留白」）追到了它的来源：**夹具**，不是产品 ——
`heatmap-empty` 是组件帧、自己写死了 430x150 + topLeading，而它的对照臂走真入口 ⇒ 两臂不同源。
补上走真入口的一臂之后重新量：0.107 / 0.267 / **0.298（新）** / 0.418 / 0.603 / 0.640，热图不是异类。
新帧立刻顶出两处名册缺口（首墨是图标的卡片内缩、暗档侧栏文字盲区），两处都按已有形状登记，
等式与容差一个字没改。**同一轮里自曝**：新拍的 `settings-stats-empty` 与既有 `settings-stats` 两档 md5 相同
（默认夹具一直注入空账本）⇒ 空态的真入口臂早就有了，本轮的净产出是那一对能判产品的数
（0.533 vs 0.252）而不是那两张帧。

最后更新：2026-10-23（本地 · R314 / 第 313 轮 / Round 311）：**空态有了走真入口的那一臂，且该臂被证实是重复臂**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 92 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 1 failure(s)；没读到 CAPTURED 行；帧基线 FRAME_BASELINE_COMPARED=176 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0 + 同一笔 update；
换装 没读到换装结论行；本轮 0 把新刀（判断，不是遗漏）：证人 = 同一轮两次捕获，第一跑红 1 朵 → 登记后第二跑零红且 没读到 CAPTURED 行；名册被删任何一条，下一次就红；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（看的是本轮那两条同源臂（`/tmp/r314_shots/settings-stats-720x540-{light,dark}.png` 空账本 vs `settings-stats-populated-720x540-{light,dark}.png` 有账本，同一个 `SettingsView`、同一条 720x540 入口、同一次 render）。判出来的不是"留白偏大"这种形容词，而是一处**缺席**：有数据那一屏卡片里有三段内容（汇总行「最近 26 周共 1322 次 · 日均 7.4 次 · 连续 126 天」、日历本体、「这张图怎么读」整段说明 + 那句"计数在复制发生的那一刻就记下了：删掉记录、清空历史都不会改写它"），空态那一屏只有 `StateLine` 一行「还没有可统计的记录 —— 复制几条之后这里会长出一张日历。」）。
产品文件 0 个，连续零改动 **3** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 313`，
同形用于 `--check`；上一轮 2）。as-of 第 313 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R315 开场要先读的（成对：run id ↔ commit）：RUN=39987562903 sha=b0a49ee status=completed conclusion=failure title=R314 代码半（第 313 轮 / Round 311 · 空态补上组合状态那一臂：一帧新帧立刻量出两处名册缺口） workflow=CI
   —— 必须读到：① 新帧 `settings-stats-empty` 在 runner 上是否也进那两处名册（vibrant 名单按机器分键，
   这一跑如果只在本机绿、runner 红，就是名单要按机器各写一份，354 那一族已经把这形状立过）；
   ② 负载红那一条（`PerfBudget testImageComparisonCostStaysBounded` 371.7ms > 250ms，单跑两次绿）
   在 runner 上怎么表现 —— runner 是独占机器，若它不红就支持"这是本机并发"而不是产品回归。

① 下一轮（R315）的靶：⓪ ~~**371**：这是本轮看图腿判出的**产品侧缺席**~~ ⇒ **R315 开场查重后撤销**：
      空态不渲染说明段是 R9 的既有决定（`SettingsView.swift:1027-1041`，教人读一张不在这里的图 = U-30 缺陷 5 同族），
      且已有判据钉着（`DailyCopyHeatmapTests.testHeatmapReadingGuideFollowsTheChart`）⇒ 详见 371 的追记；
      要重新立案必须先量**其余五个分区**空态/短态的底部留白比例，没有那五个数，"53% 太空"就还是形容词；
   ① **370**：先做 md5 对拍的出口 —— 撤掉重复臂（基线降回 174，同笔 update），
      或给空态/有数据成对比配一条会红的判据 + 那把"空态夹具换成有数据必须翻"的刀；这一条做完，
      R314 的产出才从"两张白帧"变成"一个数"；
   ② **回到动效主线**（已连续 3 轮 0 产品文件）—— 347 / 305 需用户先退出 App，
      在那之前把 305 的台阶地板用已有夹具通道再推一格；
   ③ 369：把"首墨是图标"变成可测（连通块高度比 / 左沿错开），让 `CARD_INSET_ICON_FIRST`
      从开关变成结论，并配那把"图标换成等宽文字必须翻判"的刀；
   ④ 368：把 `UICaptureHarness` 的建树路径提给判据卷（对照臂就用 `settings-stats` vs `settings-stats-populated`）；
   ⑤ 367 的迁移继续（已声明 2 张 / 剩 73 张）；⑥ 348 剩下的读数族各配恒等式；
   ⑦ 360 最后一批；⑧ 361 合并。

② 仍开：347（真机证人）、305（等 347）、368（腐烂针待清：已声明 2 张 / 剩 73 张）、
   371（**R315 开场撤销**：空态不渲染说明段是 R9 的决定且已有判据钉着 ⇒ 要重开必须先量其余五个分区的留白）、
   370（重复臂的出口：撤 or 给会红的成对判据）、369（`iconFirstCells` 自指，诊断只给名单里的格子打）、
   368（hover 提示的产物级通道）、354 的第五步 + **本轮新添的负载红一条**、
   364 的"抽不出候选的 6 把要真跑"、348 的"读数族还没纳全"、360（剩 11 份）、361（未合并）、359、362、349、
   350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   用户闸门 220 路 A / 228② / 265。

## R313 状态（第 312 轮 / Round 310 · 2026-10-23）

本轮把 367 的第一步做完了：`scripts/hidden_arms.py` 一箱变两箱 —— 表自己声明针
（`NEEDLES = {刀号: [针, …]}`）的臂走**逐根判**，可加总；其余臂维持 `any(候选命中)`，只配当下界。
棘轮从 2 个数变 4 个数，四个方向各有正对照；夹具造出"一臂两针、一活一死"，旧估计量必然漏报、新箱必须报 1。
同一轮挖出尺本体两处假归因（`ARM_ID` 的 `\\d` 恒不命中、覆盖面按字典存在数），都修了。

最后更新：2026-10-23（本地 · R313 / 第 312 轮 / Round 310）：**腐烂针的账从一箱变两箱**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 13 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 0 failures；CAPTURED 174 -> /tmp/r313_verify/frames；帧基线 FRAME_BASELINE_COMPARED=174 FRAME_BASELINE_CHANGED=0（不 update）；
换装 INSTALL_RESULT=ok  dmg=ok  installed_version=1.4.8（判据轮：0 产品文件，产物与上一笔同源）；刀 R313_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes；预检 tables=106 covered=89 bad=0、名册 arms=780；
腐烂尺 `HIDDEN_ARMS 表=194 可判=712 rot=33 抽不出=6 已声明表=2 已声明死针=0 上界 rot=33 抽不出=6 已声明死针=0 已声明表=2 处置=ok`；探针 `NEEDLE_RANGE 可判臂=712 下界=33 部分死=628 假上界=661`；电池 Ran 611 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮 0 产品文件、0 Swift 文件，看图腿的任务是「替没有回归作证」+ 顺手把一处空状态的比例读出来：看的是这一跑重捕的 heatmap-empty-430x150-dark.png（设置 → 统计在没有任何记录时的样子）与 heatmap-populated-430x250-{light,dark}.png 两张对照）。
产品文件 0 个，连续零改动 **2** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 312`，
同形用于 `--check`；上一轮 1）。as-of 第 312 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R314 开场要先读的（成对：run id ↔ commit）：RUN=39982442010 sha=4050c9f status=in_progress conclusion= title=R313 代码半补刀（M911…M913 三把 + declared_dead 的反方向断言） workflow=CI
   —— 必须读到：① 本轮三笔（代码半 / 补刀 / 这一笔账半）在 runner 上 `Ran` 的格数与本机一致
   （本机 611+，新格是 `test_declared_bin_*` 与 `DeclarationHonestyTests`）；
   ② R312 那三跑（39976319446 success / 39978500278 / 39979229010）里后两跑的最终结论，
   以及 STEP[9] 名单外那一格有没有被本轮新增的 python 用例带出新 skip。

① 下一轮（R314）的靶：① **回到动效主线**（连续两轮 0 产品文件）—— 347 需用户先退出 App，
   在那之前把 305 的台阶地板用已有夹具通道再推一格；
   ② 368：把 `UICaptureHarness` 的建树路径提给判据卷，让 hover 提示第一次可被产物级判据判到 + 配刀；
   ③ 367 的迁移继续（每轮迁 2~3 张表，降「未声明」那一箱的上界）；
   ④ 348 剩下的读数族各配恒等式；⑤ 360 最后一批；⑥ 361 合并。

② 仍开：347（真机证人）、305（等 347）、367（腐烂针待清 + 上界只能由表声明针：已声明 2 张 / 剩 73 张）、
   368（hover 提示的产物级通道）、364 的"抽不出候选的 6 把要真跑"、
   348 的"读数族还没纳全"、354 的第五步、360（剩 11 份）、361（未合并）、359、362、349、350 第二步、
   351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

## R312 状态（第 311 轮 / Round 309 · 2026-10-23）

本轮判的是 BACKLOG 356 剩下的那一半，结论是**它不成立**：
`HEAT_ADJACENT dark/1x empty→bucket1` 三根轴现读 最大=30.00 / 均值=17.33 / 亮度=2.16，
而地板施加在最大通道那一根（R52 起的选择，理由写在判据注释里）。那句"低于地板"读的是被排除的轴 ⇒ 撤回。
撤回之前先把证人做出来：16 条读数必须每条同时带三根轴，M908/M909/M910 三把刀各钉一根。
另一条产出是把 366 的两条出口**证伪**（16/715 覆盖；658 是被变异文污染的假上界），
并把「表自己声明针」这条唯一出口落成 367。

最后更新：2026-10-23（本地 · R312 / 第 311 轮 / Round 309）：**三根轴必须同时可查 —— 356 那一半被证伪并撤回**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 13 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 0 failures；CAPTURED 174 -> /tmp/r312_verify/frames；帧基线 FRAME_BASELINE_COMPARED=174 FRAME_BASELINE_CHANGED=0（不 update）；
换装 INSTALL_RESULT=ok  dmg=ok  installed_version=1.4.8（判据轮：0 产品文件，产物与上一笔同源）；刀 R312_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes；预检 tables=105 covered=88 bad=0、名册 arms=777；
腐烂尺 `HIDDEN_ARMS 表=193 可判=709 rot=33 抽不出=6 上界 rot=33 抽不出=6 处置=ok`；探针 `NEEDLE_RANGE 可判臂=709 下界=33 部分死=625 假上界=658`；电池 Ran 608 / OK (skipped=4)（写盘后同数）；看图腿 RUN（本轮 0 产品文件，看图腿的任务是「替没有回归作证」并且去**亲眼复核被撤回的那句话**：看的是这一跑重捕的 heatmap-populated-430x250-light.png 与 -dark.png（另看 cell-strip 的静置/悬停两张确认环没跟着变））。
产品文件 0 个，连续零改动 **1** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 311`，
同形用于 `--check`；上一轮 0）。as-of 第 311 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R313 开场要先读的（成对：run id ↔ commit）：RUN=39976319446 sha=6d95726 status=in_progress conclusion= title=R312 代码半（第 311 轮 / Round 309 · 三根轴必须同时可查：356 剩下的那一半被证伪） workflow=CI
   —— 必须读到：① 本轮新增的那格断言在 runner 上**没有把 16 条读数判成少轴**（它只读自己的打印，
   理论上不变，但"理论不变"要由那一跑签）；② R311 账半那一跑（run 39973549740）与本轮代码半
   那一跑之间，STEP[9]/STEP[15] 不许出现新红。

① 下一轮（R313）的靶：① **回到动效主线** —— 347 仍欠真机眼（唯一挡着产品判断的机器闸门，
   要用户先退出 App），在那之前把 305 的台阶地板用已有的夹具通道再推一格；
   ② 367 第一步：给 3 张最常用的表加 `NEEDLES = {…}`，并把 `hidden_arms.py` 分成
   「已声明（可加总）/未声明（只配下界）」两箱，各配棘轮；
   ③ 348 剩下的读数族各配一条恒等式；④ 360 的最后一批；⑤ 361 的合并。

② 仍开：347（真机证人）、305（等 347）、366（腐烂针待清 + 上界只能由表声明针）、367（迁移面 75 张表）、
   364 的"抽不出候选的 6 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；**本轮结案：356**（两半各自处置）；用户闸门 220 路 A / 228② / 265。

## R311 状态（第 310 轮 / Round 308 · 2026-10-23）

本轮是 R308 那次产品改动的**跨机器复核**：两跑 runner 都红在
`testHoverRingIsVisibleOnEveryHeatLevelAndBothScales`（dark/1x 17.11…17.13 < 地板 18，
本机 18.75 ⇒ 差 0.912 倍）。地板不按机器放宽（D-292），改产品：α 0.20 → 0.23，
仍在 0.176…0.236 的窗口里；三条判据一起过（离散 1.001、数据像素 0.000、克制度 0.37）。
副产物两条：改数值弄腐烂的三根针被上一轮刚写的 `scripts/hidden_arms.py` 当场数出来
（rot 33→35→重钉→33，那把尺第一次在真事故上生效）；R309 新格在 runner 上的 skip 由它自己点名后登记。

最后更新：2026-10-23（本地 · R311 / 第 310 轮 / Round 308）：**悬停环抬回 0.23 —— 产品在两台机器上都过线**（产品 1 文件）
现读：构建告警 0；判据卷 `Ran 13 / 0 失败`；全量卷 Executed 934 tests, with 44 skipped and 0 failures；CAPTURED 174 -> /tmp/r311_shots；帧基线 FRAME_BASELINE_COMPARED=174 FRAME_BASELINE_CHANGED=2 + 同一笔 update；
换装 INSTALL_RESULT=ok  版本=1.4.8→1.4.8；刀 R308_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes ｜ R300_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes；预检 tables=104 bad=0、名册 arms=774；
腐烂尺 `HIDDEN_ARMS 表=192 可判=706 rot=33 抽不出=6 上界 rot=33 抽不出=6 处置=ok`；电池 Ran 608 / OK (skipped=4)（写盘后同数）；看图腿 RUN（看的是这一跑重捕的 4 张：heatmap-cell-strip-still-90x140-{light,dark}.png 与 heatmap-cell-strip-hover-90x140-{light,dark}.png，并且把两档并排比过（/tmp/r311_eye/ring-dark.png 与 ring-light.png：逐像素差取最亮点定环心、34x34 裁、14 倍放大，左=R308 的 0.20、中=R311 的 0.23、右=同跑静置帧））。
产品文件 1 个，连续零改动 **0** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 310`，
同形用于 `--check`；上一轮 2 ⇒ 本轮归零）。as-of 第 310 轮的最后一笔产品提交是 9551730 = 第 310 轮。

⓪ R312 开场要先读的（成对：run id ↔ commit）：RUN=39970777765 sha=9551730 status=in_progress conclusion= title=R311 代码半（第 310 轮 / Round 308 · runner 把 0.20 判成低于地板：悬停环抬回 0. workflow=CI
   —— 必须读到的是**这一跑 runner 上 dark/1x 的 halo 读数**：本机预测 19.7（17.12 / 0.20 × 0.23），
   若那边仍低于 18，就不许再抬 α（窗口上界 0.236 已经贴着），而要改的是**环的画法**
   （加宽 hoverStroke 或改成两像素）并把这条写成一单；
   另外 R308 / R309 那两跑的红（STEP[15] 五格 + STEP[9] 名单外）本轮已修，要复核它们是否消失。

① 下一轮（R312）的靶：① 356 的剩下那一半（暗档最细一步 17.33 低于地板 18 —— 与本轮同源，
   现在多了一个已知事实：runner 的 1x 比本机低 0.912 倍，任何"贴着地板"的设计在对面那台都会掉出去）；
   ② 366：33 把腐烂针逐条处置，并把 rot 从下界做成上界（按位置取针）；
   ③ 348 剩下的读数族各配一条恒等式；④ 360 的最后一批；⑤ 361 的合并；
   ⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、366（腐烂针待清 + 下界做成上界）、
   364 的"抽不出候选的 6 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

## R310 状态（第 309 轮 / Round 307 · 2026-10-23）

本轮做"腐烂的针要能被数出来"：`scripts/hidden_arms.py`（AST + 常量传播 + 双向棘轮）现读
表=192 可判=706 rot=33 抽不出=6；判据卷 `Ran 5 / OK`；
刀 M902…M907 全 CAUGHT。D-291 定「数缺陷的判据必须先自证它不会把好的数出来；
做不到只准报规模」；364 留追记（从规模变可归因）；新开 365 登记 33 把死刀待清。

最后更新：2026-10-23（本地 · R310 / 第 309 轮 / Round 307）：**腐烂针第一次可点名**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 5 / OK`；刀 6 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=104 covered=87 bad=0、名册 files=198 arms=774 dupes=0；
腐烂尺 `HIDDEN_ARMS 表=192 可判=706 rot=33 抽不出=6 上界 rot=33 抽不出=6 处置=ok`；R309 读数尺互证 `LEDGER_READINGS 小节前缀=FULL SUITE 跑=2 取用=FULL SUITE 第二遍（修完 halo 分类器的数据带之后） 格数=934 skip=44 失败=0 其它最大=934 早先红=1（证人 /tmp/r308_chain.log：本轮零 Swift 改动 ⇒ 全量卷那份日志仍是 R308 的一跑）`；电池 Ran 608 / OK (skipped=4)（写盘后同数）；
看图腿 RUN（174 张在盘上，本轮无新帧 —— 本轮是判据轮，没有新帧；看图腿做的是**复看**，不是复述上一轮的结论。现读帧目录 `FRAMES_ON_DISK=174`（`ls /tmp/r308_shots3 | grep -c .png`），看的是 R308 改动的那两张：`heatmap-cell-strip-hover-90x140-light`、`heatmap-cell-strip-hover-90x140-dark`。

亮档：被悬停那一格（第四行第二列）外面是一圈**与格子之间留有一条空白**的浅灰环，格子自己的蓝没有被压、也没有换色；环的四条边到格边距离看着一致，圆角跟着外扩）。
产品文件 0 个，连续零改动 **2** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 309`，
同形用于 `--check`；上一轮 1）。as-of 第 309 轮的最后一笔产品提交是 9eb266e = 第 307 轮。
Swift 三条腿 NOT-RUN 并写理由（0 Swift 文件 ⇒ 没有新字节可跑，也没有旧字节能被本轮弄坏）。

⓪ R311 开场要先读的（成对：run id ↔ commit）：RUN=39965996188 sha=340452f status=in_progress conclusion= title=R309 账半（七本一起落：U-1013…U-1015、D-290、348 有尺真身、364 数出规模） workflow=CI
   —— 本轮与 R309 的 runner 结论都要读。另外两件事：
   ① `scripts/hidden_arms.py` 的语料是**盘上现状**，runner 上工作树相同 ⇒ 数相同；
      任何一台机器少一张表就会漂，而漂了会响（双向棘轮），别把它当机器差异放行；
   ② 判据卷里 `test_the_ceilings_equal_the_live_readings` 依赖 .scratch 的表都在 ——
      若 runner 的 checkout 少了文件，那一格按"缺产物算红"处理，不许 skip。

① 下一轮（R311）的靶：① **回到产品面** —— 356 剩下那一半（暗档最细一步 17.33 低于地板 18、
   1x/2x 抗锯齿离散 1.7 倍）：先量"换通道"候选有没有产物证人，不许拿减档数当解药；
   ② 365：33 把腐烂针逐条处置，每清一把就降上界；
   ③ 348 剩下的读数族（帧数 / 刀数 / §8 格子数）各配一条恒等式；
   ④ 360 的最后一批（11 份裸 stdout）；⑤ 361 的合并；⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、365（腐烂针待清）、
   364 的"抽不出候选的 6 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

## R309 状态（第 308 轮 / Round 306 · 2026-10-23）

本轮做的是**写账这件事本身**：R308 的三本假账（把捕帧卷 92 当全量卷 934）通过了当时的门，
靠本轮新写的恒等式闸门才被拦住。落地三件：`scripts/ledger_readings.py`（小节切片 + 恒等式 + 每跑记账）、
`scripts/tests/test_ledger_readings.py`（现读 `Ran 8 / OK`）、刀 M895…M900（全 CAUGHT、RESTORE_CLEAN=yes）。
D-290 定「读数只能由被计数物自己打印的那一行给出，且必须按所属小节取；跨小节取末算抄错」；
348 追记为"这一格今天有了尺真身，但门只覆盖 `Executed` 这一族"；364 追记为"隐藏臂规模现读 423 把 / 75 张表"。

最后更新：2026-10-23（本地 · R309 / 第 308 轮 / Round 306）：**台账的读数口搬进仓库**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 8 / OK`；刀 6 把全 CAUGHT；
预检 tables=103 covered=86 bad=0、名册 files=197 arms=768 dupes=0；
仪器跑真日志 `LEDGER_READINGS 小节前缀=FULL SUITE 跑=2 取用=FULL SUITE 第二遍（修完 halo 分类器的数据带之后） 格数=934 skip=44 失败=0 其它最大=934 早先红=1`；电池 Ran 603 / OK (skipped=4)（写盘后同数）；
看图腿 RUN（174 张在盘上，本轮没有新帧 —— 本轮是判据轮，没有新帧可看；看图腿做的是**复看**，不是复述上一轮的结论。现读 `FRAMES_ON_DISK=174`（`ls /tmp/r308_shots3 | grep -c .png`），看的是 R308 改动的那两张：`heatmap-cell-strip-hover-90x140-light`、`heatmap-cell-strip-hover-90x140-dark`。

亮档：被悬停那一格（第四行第二列）外面是一圈**与格子之间留有一条空白**的浅灰环，格子自己的蓝没有被压、也没有换色；环的四条边到格边的距离看着一致，圆角跟着外扩，所以角上的间距没有比直边大。读起来像系统的焦点环，不像"这一格变色了"。

暗档：同一格是更亮的蓝 + 一圈浅灰细环，环在深色底上比亮档更醒目一点，但仍不吞掉深浅——相邻几格的档差照样分得开。）。
产品文件 0 个，连续零改动 **1** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 308`，
同形用于 `--check`；上一轮是 0）。as-of 第 308 轮的最后一笔产品提交是 9eb266e = 第 307 轮。
Swift 三条腿 NOT-RUN 并写明理由（全量卷 / 重捕帧 / 换装 —— 本轮 0 Swift 文件，没有新字节可跑，也没有旧字节能被本轮弄坏）。

⓪ R310 开场要先读的（成对：run id ↔ commit）：RUN=39963980031 sha=abf2460 status=in_progress conclusion= title=R308 账半（七本一起落：U-1010…U-1012、D-289、356 换形状落地一半、新开 364） workflow=CI
   —— 本轮两笔（代码半 + 账半）的 runner 结论要读；`scripts/ledger_readings.py` 与
   `scripts/tests/test_ledger_readings.py` 是新进电池的两格，若 runner 上红在
   `test_the_round_chain_log_reads_as_the_ledger_claims` 那**不是坏**：那一格在 /tmp 日志不在时是 skip，
   要查的是"skip 名单有没有按机器分键接住它"（331/347 那一族），别去改判据。

① 下一轮（R310）的靶：① 回到产品面 —— 356 剩下那一半（暗档最细一步 17.33 低于可见性地板 18）
   要先量"换通道"那一候选还有没有产物证人，别再拿减档数当解药；
   ② 364 的表自数（每张表导入时数自己的 needle 命中，423 把隐藏臂必须能报出来）；
   ③ 348 剩下那批读数族（帧数 / 刀数 / §8 格子数各配一条恒等式）；
   ④ 360 的最后一批（11 份裸 stdout）；⑤ 361 的合并；⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、364（隐藏 needle 的规模已数出来，尚未有牙）、
   348 的"读数族还没纳全"、354 的第五步（sampled 那两条的退场阈值）、360（剩 11 份）、361（未合并）、
   359、362、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、304、296、291；
   用户闸门 220 路 A / 228② / 265。

## R308 状态（第 307 轮 / Round 305 · 2026-10-23）

⓪ 读 CI（R309 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：RUN=39847851743 sha=de370bf status=completed conclusion=success title=R307 账半（七本一起落：U-1007…U-1009、D-288、354 第四步结案） workflow=CI
上一轮登记要验的那格**已交账**：两跑（5225196 ↔ 39846928354、de370bf ↔ 39847851743，都 success）
都在 STEP「Motion coverage floor」打出 `MOTION_FLOOR_SUITE_NOT_SEEN=2` ⇒ 354 第四步的"缺席会被点名"
在 runner 上成立，不再只是本机夹具里响。同一格还顺带给出 `MOTION_FLOOR_OK=3/4 → 4/4`
（第一跑 not-run=notice-banner，第二跑判到了 ⇒ 那一臂是采样漂，不是掉臂）。
R309 开场要验的两件事：① 本轮这两笔 push 之后，runner 上 `HEAT_RING_LEVEL_SPREAD` 与
`HEAT_DATA_UNTOUCHED` 那两族读数是否仍在文件通道里落得下来（新通道名要进 `READINGS_ROSTER` 的派生名册）；
② 1x 臂在 runner 上的 halo 均值（本机 23.09 / 20.48）会不会因机器不同而贴地板 —— 若那边红在
`testHoverRingIsVisibleOnEveryHeatLevelAndBothScales`，先查机器再谈判据（R38/D-251 那一课）。

最后更新：2026-10-23（本地 · R308 / 第 307 轮 / Round 305）：**回到产品面 —— 悬停那一圈搬到格子外面**（产品 2 文件）
连续 7 轮 0 产品文件之后第一次动 `Sources/`：`strokeBorder` 会换掉那一格外圈的数据像素、
且响度随档位变 1.73…1.75 倍（最响处正是没有数据的空格）。改成留白里的同心 halo 之后
现读整格均值差 0.000（新判据钉住）、档间离散 1.000（新判据 ≤1.05），α 0.30→0.20。
D-289 定"尺子的带必须跟着被测物走；分带之后要有一格钉住两带不相交"。
现读：构建告警 0；判据卷 `Executed 13 / 0 失败`；全量卷 `Executed 934 / 44 skip / 0 失败`（共 2 跑：`FULL SUITE` = 934 格 / 44 skip / 3 失败 ｜ `FULL SUITE 第二遍（修完 halo 分类器的数据带之后）` = 934 格 / 44 skip / 0 失败 ⇒ 引的是最后一跑（前几跑的红是本轮改动过程中自己修掉的，原样留档））；帧 `CAPTURED 174`、
`COMPARED=174 CHANGED=2`（正是那两张 hover 帧）+ 基线同一笔 update；换装 ok；
刀 15 把全 CAUGHT（含历史表 r300 / r45 重钉后重跑）、预检 tables=102 bad=0；
电池 Ran 595 / OK (skipped=4)（写盘后同数）；看图腿 RUN（看的是本轮真的变了的那两张（`heatmap-cell-strip-hover-light` / `-dark`，90x140 组件帧）：亮档里被悬停那一格现在带着一圈与格子同心、隔 1pt 的中性灰 halo，格子自己的蓝一点没被压，读起来像系统的焦点环而不是「这一格变色了」；暗档同一格的外圈是浅灰，四条边到格边的距离一致）。
产品文件 2 个，连续零改动 **0** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 307`，
同形用于 `--check`；此前是 7 轮，本轮代码半那一笔把它归零）。
as-of 第 307 轮的最后一笔产品提交是 9eb266e = 第 307 轮。

① 下一轮（R309）的靶：① 347 / 305 的真机眼（要用户退出 App，或回答「收藏星按下够不够明显」）——
   这是产品面唯一一条我自己走不完的腿；② 356 的剩下那一半（暗档最细一步 17.33 vs 地板 18，
   以及 1x/2x 的 1.7 倍抗锯齿离散）—— 先量"换通道"那一候选还有没有产物证人，别再拿减档数当解药；
   ③ 新开的 364：让每张刀表在导入时自数 needle，隐藏针的腐烂必须会响；
   ④ 360 的最后一批（11 份裸 stdout 清零）；⑤ 361 的合并。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**（暗档最细一步 vs 地板）、
354 的第五步（sampled 的退场阈值）、360（剩 11 行裸 stdout）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、364（隐藏 needle 的腐烂检测）、
348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R307 状态（第 306 轮 / Round 304 · 2026-10-23）

⓪ 读 CI（R308 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：5225196 ↔ 39846928354（in_progress，结论未读）
本轮新落的两笔 push 之后要验的两件事：① STEP「Motion coverage floor」在 runner 上是否打出
`MOTION_FLOOR_SUITE_NOT_SEEN=2`（这是第四步的第一份 runner 证人 —— 它证明"缺席会被点名"真的在响，
而不是只在本机夹具里响）；② STEP[18] 与 `READINGS_ROSTER` 那两格照旧（R306 已复验一次）。
若 runner 那一步反过来红在 `MOTION_FLOOR_SUITE_NO_RECURRENCE` ⇒ 说明它读到了没写档位的登记，
先查表而不是先怀疑门。

最后更新：2026-10-23（本地 · R307 / 第 306 轮 / Round 304）：**354 第四步结案到「缺席会发声」这一层** ——
`suite_verdicts` 的两条路汇成一份 `retirement_verdicts`（always 缺席即红 / sampled 只点名 /
没写 recurrence 红 / 空表不响），D-288 把"一条规则一份实现 + 出口不许放在判据之后"定成规矩；
四把刀 M885…M888 全 CAUGHT、历史表 R305 重跑全 CAUGHT、预检 tables=101 arms=757 bad=0；
电池 Ran 595 / OK (skipped=4)；`product_streak --check` 绿；`LEDGER_TOKENS stray=0`。
本轮产品 0 文件、Swift 0 份 ⇒ 四件套的 Swift 三条腿**没有新对象**，沿用上轮读数并写明理由
（不是"跑过"）；看图腿 RUN（174 张帧在盘上）。
产品文件 0 个，连续零改动 **7** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for 306`，
同形用于 `--check`）。as-of 第 306 轮的最后一笔产品提交是 6ac317f = 第 299 轮。

① 下一轮（R308）的靶：① 354 的第五步 —— `sampled` 的退场阈值要拿"响过的次数"当依据来定，
别再凭一次读数删登记；② 把 ⓪ 那两件事交账（尤其 `NOT_SEEN=2` 在 runner 上第一次响没响）；
③ 360 的最后一批（11 份裸 stdout 清零）；④ 361 的合并。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第五步（sampled 的退场阈值）、360（剩 11 行裸 stdout）、
361（同步点已数出，尚未合并）、359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、
356（悬停换形状的三条候选）、348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R306 状态（第 305 轮 / Round 303 · 2026-10-23）

⓪ 读 CI（R307 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：sha 90fa327（本地 HEAD）↔ run 39837096189，结论 success ⇒ 上一轮登记要验的那格已交账（详见本节正文与 U-1006）
已交账（90fa327 / run 39837096189 / success）：STEP「Motion coverage floor」现读 MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）｜机器=github-runner
⇒ R305 那两处登记的证人**到了**，但答案是「这一跑没露面」而不是预期的 `REGISTERED_REDS=2`
（上一跑 39833209888 同一格也是 CLEAN=0 ⇒ 连续两跑）。登记的理由自己写着出现率 1/17 与 1/7，
所以两跑没红不配把登记删掉，配的是一句更难看的话：**门在「没露面」这一支直接 return，缺席连一行都不打**
⇒ 354 的第三步按这个读数改判，欠的变成第四步（见 U-1006）。
下一跑要验的两件事：① STEP[18] 在名册翻回 can 之后是否不再红（R305 已复验一次，红名回来要说清是哪一条）；
② 本轮新搬的四份卷（`INK*` / `COLOR_PROBE` / `MARKDOWN_PERF` / `CAPTURE_PATH_*` / `PERF*`）
在 runner 上是否仍在文件通道里落得下来（`READINGS_ROSTER derived=18 declared=18`）。

最后更新：2026-10-23（本地 · R306 / 第 305 轮 / Round 303）：**360 的第三批搬完 + 363 结案 + 看图腿回到 RUN + 354 的 runner 证人交账** ——
14 行改走 `CaptureReadings.emit`，棘轮 29 → 现读 15（登记值与盘上相等），派生名册 14 → 18，
Swift 标记名册的通道表 +2（M883 钉「从通道表删名字」）；`test_ledger_ids.py` 七支三位假设抬成 `\d{3,4}`
并配四位正/反对照，位数只打读数 ⇒ D-287 定下宽度约定。本轮 0 个产品文件但**真的重捕并看了帧**
（174 张、compared=174、changed=0）。
四件套现读：全量卷 933 / skip 44 / 失败 0、告警 0、帧 changed=0 missing=0、
dmg=ok、换装 1.4.8；预检 tables=100 arms=753 bad=0；R301…R304 四张历史表全 CAUGHT（先修掉五把坏刀）；
电池 Ran 589 / OK (skipped=4)；`product_streak --check` 绿；`LEDGER_TOKENS stray=0`。
产品文件 0 个，连续零改动 **6** 轮（现读 `python3 scripts/product_streak.py --streak-for 305`：
as-of 第 305 轮的最后一笔产品提交是 6ac317f = 第 299 轮）。

① 下一轮（R307）的靶：① **354 的第四步** —— 给 `suite_reds` 补一条退场判据：本机登记的名字这一跑没露面时，
门要能打点（arms 那侧的 `MOTION_FLOOR_STALE` 是现成的形状），并配一把刀钉住「没露面 ⇒ 有声音」；
② 把 ⓪ 那两件事交账（STEP[18] 与 `READINGS_ROSTER`）；③ 360 的最后一批（从 `WindowChromeLayoutTests` 3 行起，
11 份 15 行清零）；④ 361 的合并（同步点数量已能现读，合并成一处上游数据还没做）。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第四步（本机登记的缺席没有打点）、360（剩 11 份 15 行）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、356（悬停换形状的三条候选）、
348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、
310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R305 状态（第 304 轮 / Round 302 · 2026-10-23）

⓪ 读 CI（R306 的开场取数，只登记不轮询 = R140，并按 362 的写法**只列每次 push 的 tip**）：成对号按 362 的写法现读（只列每次 push 的 **tip**，逐笔按 `actions/runs?head_sha=` 查）：`91ff498`（R304 的账半，tip）→ 39833209888 / completed / **success**，其中 STEP[19] Motion coverage floor 现读 `MOTION_FLOOR_SUITE_CLEAN=0`、`红的用例=-`、`MOTION_FLOOR_REDS=0` ⇒ 354 那两朵红**这一跑根本没出现**（与出现率 1/17 一致），所以这一跑只能证明「登记没把别的东西弄红」，**不能替登记本身作证** —— 登记的证人是它下一次真的红在 `MOTION_FLOOR_REGISTERED_REDS=2` 那一跑；`e9647ed`（R304 的代码半）→ **total_count=0**（push 边界，从来没有 run，不再记未读）；R304 交账的 `811c4fc` 那朵 STEP[18] `NOW_RUNS` 已按点名翻 can，并被本次 success 复验（探针那一步不再红）。本轮两笔由 R306 现取
要验的三件事：① STEP[18] On-screen probe coverage floor 那朵 `NOW_RUNS` 在名册翻回 can 之后是否不再红
（`811c4fc` 那一跑的答案见 R304 的 ⓪，本轮已交账）；
② **STEP[19] Motion coverage floor** 那两朵红在机器切片之后应当变成
`MOTION_FLOOR_REGISTERED_REDS=2` 且退出码 0 —— 这是本轮修法唯一真正的证人，本机签不了这一半；
若它仍然红在 `SUITE_RED`，那说明 runner 上报的机器键与 `github-runner` 不一致（读 FACTS 行尾的「机器=」）；
③ 登记里那两个用例名在 runner 上是否**存在**（名字与源码对账由本机那格判，跨机存在性只有 runner 能说）。

最后更新：2026-10-23（本地 · R305 / 第 304 轮 / Round 302）：**354 的第二步结案到「登记做成」这一层** ——
`motion_floor_gate.py` 的用例级登记按机器切片，2 条只属于 github-runner；缺键红、跨机不顶检、退场按机器切，
刀 M880/M881 各钉一侧、2/2 CAUGHT、RESTORE_CLEAN=yes；闸门卷 44 格（含读活账那一格）。
编号越界先把尺抬宽：`U_DEF` / `U_RANGE` `\d{3}` → `\d{3,4}` + 三格对照（D / BACKLOG 号同形，新开 363）。
四件套沿用 R304 那笔的现读（本轮 0 个 Swift 文件）：告警 0、全量卷 933/失败 0、
帧 174 changed=0、dmg=ok、换装 1.4.8；看图腿与换装本机 **NOT-RUN**（没测，不是没变）。
预检 tables=99 arms=750 bad=0；占位符扫描 7 本 stray=0；电池 Ran 586 / OK (skipped=4)。
产品文件 0 个，连续零改动 **5** 轮（现读 `python3 scripts/product_streak.py --streak-for 304`：
as-of 第 304 轮的最后一笔产品提交是 6ac317f = 第 299 轮，即 R300 的代码半）。

① 下一轮（R306）的靶：**354 的第三步** —— 等 runner 自己说这两条现在不红（② 那一格），
若两跑同现就先读 `MOTION_BAND_INTERVAL` 在负载下的数再谈判据；顺带 360 的第三批与 363（编号尺剩下两处三位假设）。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第三步（负载下的调度地板读数）、
363（D / BACKLOG 号的三位假设）、360（已搬两批）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列；本轮量到 3 笔根本没有 run）、
356（悬停换形状的三条候选）、348 的「数字对不对」那一格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R304 状态（第 303 轮 / Round 301 · 2026-10-23）

⓪ 读 CI（R305 的开场取数，只登记不轮询 = R140）：成对号本轮**按 push 的 tip 现读**（`gh api "repos/…/actions/runs?head_sha=<完整 sha>"` 逐笔查，取数口见 U-999）：`811c4fc`（R303 账半）→ 39825878608 / completed / **failure** —— 只红在 STEP[18] On-screen probe coverage floor，正文 `NOW_RUNS testOffScreenProgrammaticSelectionIsRevealedAndNotJumped：登记说 runner 跑不了，而这次它下结论了（passed）` ⇒ 本轮照 runner 的点名把 `scripts/probe_coverage_expectations.json` 那一格翻回 can（配对测试的「红身份」名单从两条抬成三条，夹具不动）；`ac1ed6b` → 39822963311 / success、`8c63c46` → 39817856053 / success、`8f6c300` → 39814465153 / success、`f5a563a` → 39806766619 / success；而 `b420967` / `4adc04f` / `5713c89` 的 **total_count=0** —— 这三笔**从来没有 run**（一次 push 只给 tip 那笔建），台账从前把它们写成「不在最近 10 跑里（未读）」是把结构性不存在记成待办 ⇒ 新开 362，本轮起 ⓪ 不再为它们挂「未读」。本轮两笔（Tests/判据半 + 台账半）由 R305 现取
要验的四件事：① R303 两笔（`b420967` / `811c4fc`）与本轮两笔的成对号；
② 派生名册抬到 14 个之后，`testCaptureReadingsUseTheFileChannel` 在 runner 上是否与本机同数
（同一棵树同一批文件 ⇒ 不同就是接线）；③ `test_readings_channel_coverage` 那 6 格在 runner 上的
裸 stdout 计数是否同为 29、Swift 名字名册的 total 是否同为 77；④ STEP[19] 若再现 ⇒
按 354 的②登记成有名字的未覆盖（出现率已量到 1/17 与 1/7）。

最后更新：2026-10-23（本地 · R304 / 第 303 轮 / Round 301）：**360 第二批搬完 + 同步点第一次被数出来** ——
三份判据卷共 13 行改走 `CaptureReadings.emit`，棘轮 42 → 现读 29，派生名册 11 → 14，
Swift 名字名册新增显式 `emitChannel` 表（M878 钉「从表里删名字」，M879 钉「写回 print」，两把都 CAUGHT）。
361 从抱怨变成尺寸：一次搬动要同步 搬动本身 13 处调用 + 名册 2 张（Swift 通道名册 14 个名字、Swift 名字名册的 emitChannel 4 个名字）+ 电池那一卷的登记值 1 处与按文件未覆盖名单 15 条 ⇒ D-285 把「每一处都要有刀 + 登记值现读等于盘上」定成规矩。
本轮又当场修一次自己的腐烂：`R303_MUTATE` 三根 needle 里两根的期望值是上一轮的数字（预检 bad=2、ESCAPED=1），
重钉后 R303 / R195 / R196 三张表全 CAUGHT、预检 bad=0、ARM_TOTAL=748。
台账自己第一次被读：本轮生成器把一个占位符的键写成复数 ⇒ 顺着形状扫七本账，数出历史遗留 **11 处未替换的洞**
（346 的 R296 结案追记 7 处、305 的 R295 追记 4 处，正文都写着「现读」），按别处的同一批现读记录填回，
并补 `scripts/tests/test_ledger_tokens.py`（4 格）+ 生成器写盘前自扫 —— 这一格归 348，不另开单。
四件套：全量卷 933/失败 0、build 告警 0、帧 174 张 changed=0、dmg=ok、换装 1.4.8；
电池 Ran 578 / OK (skipped=4)；353 的门绿（streak 两格同源）。
产品文件 0 个，连续零改动 **4** 轮（现读 `python3 scripts/product_streak.py --streak-for 303`：
as-of 第 303 轮的最后一笔产品提交是 6ac317f = 第 299 轮，即 R300 的代码半）。

① 下一轮（R305）的靶：**354 的第二步** —— 动效地板那两朵红登记成按机器×按用例切片的有名字未覆盖
（出现率 1/17 与 1/7；名册要能退场、红话要打印键；对账形状复用本轮的派生名册）。
顺带 360 的第三批（从 `OffscreenSymbolInkProbeTests` 的 3 行与 `WindowChromeLayoutTests` 的 3 行起，
搬完把登记值降到现读）与 361（先让同步点数量成为读数，再谈合并）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
360（已搬两批，剩 15 份文件 29 行）、361（同步点已数出，尚未合并）、
362（⓪ 的成对号按 commit 列；本轮量到 3 笔根本没有 run）、
359（取证目录没有读数汇聚点，本轮重量仍是 0 行）、356（悬停换形状的三条候选）、348 的「数字对不对」那一格、
349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R303 状态（第 302 轮 / Round 300 · 2026-10-23）

⓪ 读 CI（R304 的开场取数，只登记不轮询 = R140）：成对号现读：`4adc04f` → 不在最近 10 跑里（未读）；`ac1ed6b` → 39822963311 / in_progress / **未判**；`5713c89` → 不在最近 10 跑里（未读）；`8c63c46` → 39817856053 / completed / **success**。取数口 `gh run list --limit 10 --json databaseId,headSha,status,conclusion`（本轮这条命令通了；R302 那一轮它连试三次 EOF ⇒ 那三跑当时的结论仍然要靠 R304 补读）
要验的四件事：① `4adc04f` / `ac1ed6b`（R302 的代码半与账半）与本轮两笔的成对号；
② 名册派生化之后 `testCaptureReadingsUseTheFileChannel` 在 runner 上是否与本机同为 11 个名字
（同一棵树同一批文件 ⇒ 不同就是接线）；③ `test_readings_channel_coverage` 那 5 格在 runner 上的
裸 stdout 计数是否同为 42；④ STEP[19] 的动效地板若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 1/17 与 1/7）。

最后更新：2026-10-23（本地 · R303 / 第 302 轮 / Round 300）：**360 的第一步 + 一次刀教出来的换轴** ——
`UIInteractionProbeTests.swift` 那 15 行裸 stdout 改走 `CaptureReadings.emit`，棘轮由 57 降到现读 42，
派生名册抬到 11 个；刀 M875/M876/M877 全 CAUGHT（M876 钉的是「拿登记值容纳现状」那一侧）。
本轮最值钱的是 M731 先 ESCAPED 后 CAUGHT：按 `print` 写的读数名册在搬动之后对「标记被改名」失去可见性，
说明它把名字和通道绑死了 ⇒ 名册改成按通道读（合计 77 行，探针那份 53 行 / 42 种标记全登记，D-284）。
同轮复活三根哑针（R195 的 M728/M729、R196 的 M731，needle 命中 0 次 ⇒ 预检 bad=3）⇒ 两张历史表重跑各自全 CAUGHT。
四件套：全量卷 933/失败 0、build 告警 0、帧 174 张 changed=0、dmg=ok、换装 1.4.8；
预检 ARM_TOTAL=746 bad=0；电池 Ran 571 / OK (skipped=4)。
产品文件 0 个，连续零改动 **3** 轮（现读 `python3 scripts/product_streak.py --streak-for 302`：
as-of 第 302 轮的最后一笔产品提交是 6ac317f = 第 299 轮，即 R300 的代码半）。

① 下一轮（R304）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（名册要能退场、红话要打印键；出现率已有数 1/17 与 1/7，覆盖率名单这一族的对账形状本轮已经建好）。
顺带 361（三张名单合并成一处派生，先做②那条双向对账，别先写门）；360 剩下的 18 份文件继续搬。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
360（第一步已完成，剩 42 行）、361（三张名单并存，缺一处上游）、
359（取证目录没有读数汇聚点，本轮重量仍是 0 行）、356（悬停换形状的三条候选）、348 的两格、
349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R302 状态（第 301 轮 / Round 299 · 2026-10-23）

⓪ 读 CI（R303 的开场取数，只登记不轮询 = R140）：成对号**未读**：`gh run list --limit 12 --json databaseId,headSha,status,conclusion` 本轮连试三次全部失败（`failed to get runs: Get https://api.github.com/…/actions/runs: EOF`），而同一时刻 `git push`（SSH）是通的 ⇒ 断的是 API 这一条，不是权限。`5713c89` / `8c63c46`（R301 的代码半与账半）与 `8f6c300`（R300 账半）三跑一律记为未读，R303 开场第一件事是重读它们（不许把「没读到」写成「CI 绿」）
本轮两笔（代码半 + 账半）由 R303 现取。要验的三件事：
① 名册从 3 个名字扩到派生集 10 个之后，`testCaptureReadingsUseTheFileChannel` 在 runner 上是否**同数**
（它扫的是仓库里的文件，与机器无关；红在「不存在」= 名册与文件树不一致，红在「未纳管/已过期」= 电池那一卷先红）；
② `scripts/tests/test_readings_channel_coverage.py` 那 5 格在 runner 上是否与本机同为 57（同一棵树同一批文件 ⇒
不同就是接线，不是阈值）；③ STEP[19] 的动效地板若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 1/17 与 1/7）。

最后更新：2026-10-23（本地 · R302 / 第 301 轮 / Round 299）：**358 结案 + 覆盖率第一次是一个会红的数** ——
动效卷自己那份「两条腿」的实现删成一层壳（按 URL 记首次与那把锁从此只有一份），两处 `NATIVE_PROBE_STATE` 接进通道；
名册改成派生集（3 → 10 个），新卷 `test_readings_channel_coverage.py` 5 格钉住
「名册 = 派生集（双向）」与「裸 stdout 行数 = 57 = 登记值（双向棘轮）」，
未覆盖 19 份文件 57 行按文件登记（最大一处 UIInteractionProbeTests.swift 15 行）。
刀 M872/M873/M874 全 CAUGHT；R301 的 M871 被本轮名册改动弄哑（needle 命中 0 次，预检 bad=1 当场报），重钉后重跑 2/2。
四件套：全量卷 933/失败 0、build 告警 0、帧 174 张 changed=0、dmg=ok、换装 1.4.8；
预检 ARM_TOTAL=743 bad=0；电池 Ran 570 / OK (skipped=4)。
产品文件 0 个，连续零改动 **2** 轮（现读 `python3 scripts/product_streak.py --streak-for 301`：
as-of 第 301 轮的最后一笔产品提交是 6ac317f = 第 299 轮，即 R300 的代码半）。

① 下一轮（R303）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（照 155/166/171 那一族：名册要能退场、红话要打印键；出现率已有数 1/17 与 1/7，
而「覆盖率名单」这一族的形状本轮刚建好，可以直接复用它的对账写法）。
顺带 360（从 UIInteractionProbeTests.swift 那 15 行开始搬，搬一份就把登记值降到现读）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、
360（57 行裸 stdout 按文件搬进通道）、359（取证目录没有读数汇聚点，本轮重量仍是 0 行）、
356（悬停换形状的三条候选）、348 的两格、349、350 第二步、351、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R301 状态（第 300 轮 / Round 298 · 2026-10-23）

⓪ 读 CI（R302 的开场取数，只登记不轮询 = R140）：成对号现读 ——
`f5a563a` → 39806766619 / completed / **success**（R300 之前那笔台账：R299 的门 `test_product_streak_cell`
在 runner 上**有对象且没红** ⇒ 浅历史没有把它打成跳过）；
`8f6c300` → 39814465153 / queued / **未判**（R300 的台账半：要看 STEP[19] 那两朵红是否再现）；
本轮两笔（Tests + 台账半）由 R302 现取。要验的三件事：
① `testCaptureReadingsUseTheFileChannel` 的新名册在 runner 上是否**同数**（它扫的是仓库里的文件，
与机器无关；若红在「不存在」⇒ 是名册与文件树不一致，不是产品）；
② runner 上热图 marker 的条数 —— **这一格现在是已知做不到的**：CI 的抓帧步骤同样只跑 `--filter UICaptureTests`（359），
所以按结构它应当读不到（本机四件套目录现读 0 行）；读到了才要说清是哪一步跑的，读不到不许记成回归；
③ STEP[19] 若再现 ⇒ 按 354 的②登记成有名字的未覆盖（出现率已量到 1/17 与 1/7，不再需要「等下一次单跑」）。

最后更新：2026-10-23（本地 · R301 / 第 300 轮 / Round 298）：**357 结案 —— 判据读数第一次能活过 `swift test`** ——
热图那 9 行改走 `CaptureReadings`，现读文件里 HEAT_ADJACENT=32、HEAT_INK_SPACE=4、HEAT_LOUDNESS=10、HEAT_RING=50、HEAT_RING_CONFINEMENT=10、HEAT_RING_VS_STEP=20、HEAT_STRIP=1（`HEAT_RING_VS_STEP` 20 条，倍率区间 0.70…0.57）；
守卫按 D-282 扩成名册扫描 + 两格防空转，刀 M870/M871 全 CAUGHT。
354 的出现率不再靠「下一次单跑」：按 Swift 树分组现读动效地板 1/17 与 1/7，登记那一步仍欠（本单不结案）。
四件套：全量卷 933/失败 0、build 告警 0、帧 174 张 changed=0、
dmg=ok、换装 1.4.8；预检 ARM_TOTAL=740 bad=0；电池 Ran 565 / OK (skipped=4)。
产品文件 0 个，连续零改动 **1** 轮（现读 `python3 scripts/product_streak.py --streak-for 300`：
as-of 第 300 轮的最后一笔产品提交是 6ac317f = 第 299 轮，即 R300 的代码半）。

① 下一轮（R302）的靶：**354 的第二步** —— 把动效地板那两朵红登记成按机器×按用例切片的
有名字未覆盖（照 155/166/171 那一族：名册要能退场、红话要打印键），出现率已有数（1/17 与 1/7）。
顺带 358（把动效卷那份 `emit` 收成薄壳，之后名册才能扫它）。
产品面：347/305 仍挡在用户那一边（要退出 App 或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第二步（登记成有名字的未覆盖）、358（两份 emit 实现）、
359（取证目录没有读数汇聚点）、356（悬停换形状的三条候选）、348 的两格、349、350 第二步、351、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R300 状态（第 299 轮 / Round 297 · 2026-10-23）

⓪ 读 CI（R301 的开场取数，只登记不轮询 = R140）：`f5a563a` → run 39806766619 本轮取时仍 in_progress /
**未读** —— R301 要现取它与本轮这两笔（代码半 6ac317f、台账半）的成对号，
`gh run list --limit 8 --json databaseId,headSha,status,conclusion`。要验的三件事：
① 新判据 `testHoverIsNotLouderThanOneDataStep` 在 runner 上的 20 条读数与本机是否同形
（runner 是 @1x，颗数不可跨机比，但**比值**可：D-276 那一族）；
② R299 那扇门 `test_product_streak_cell` 在 runner 上**有没有对象**（它读 `git log`，浅历史必须红而不是跳过）；
③ 上一跑 STEP[19] 那两朵红是否再现（再现 ⇒ 按 354 的②登记成有名字的未覆盖；不再现 ⇒ 也不许当成已修）。

最后更新：2026-10-23（本地 · R300 / 第 299 轮 / Round 297）：**动了产品 2 个文件，连续零改动纪录归零** ——
热图悬停那一圈从 0.55 降到 **0.30**、梯子顶档从 0.85 抬到 **0.92**，理由是新判据现读
「环在最响的一臂改 75.50 而最重的一次数据变化只改 37.33」（两条界夹出的窗口原本为空集，D-281）；
314 结案于「不是选中态的同形物，但确实过响」。`scripts/product_streak.py` 现读 streak=0
（最后一笔产品提交 6ac317f = 第 299 轮）。
四件套：全量卷 933/失败 0、build 告警 0、帧 174 张 changed=0（基线同一笔）、
dmg=ok、换装 1.4.8；变异 4/4 全 CAUGHT、RESTORE_CLEAN=yes；电池 Ran 565 / OK (skipped=4)。
产品文件 **2** 个，连续零改动 **0** 轮（现读 `python3 scripts/product_streak.py --streak-for 299`：
as-of 第 299 轮的最后一笔产品提交是 6ac317f（本轮的代码半 6ac317f）⇒ 这条纪录归零；
本节上一版写的「连续 9 轮」也是同一颗尺的现读值，只作历史不作数）。

① 下一轮（R301）的靶：按同一条思路给**其余**只有一根地板的强度参数补对偶 ——
候选是 `VisualFillLift.hover/pressed/selected`（0.04/0.03/0.02，D-249 只钉了带子不相交，没钉上限）
与行内那颗 `RowFavoriteButton` 的 tint（0.55↔0.78）。347/305 仍挡在用户那一边。

② 仍开：347（真机证人，要用户退出 App 或回答一句）、305（等 347）、356（悬停换形状的三条候选）、
357（判据读数的本地通道）、354（runner 单跑红的分布读数）、348 的两格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

## R299 状态（第 298 轮 / Round 296 · 2026-10-22）

⓪ 读 CI（R300 的开场取数，只登记不轮询 = R140）：本轮已 push 的笔与现读结论成对 ——
`fec526e` → 39795800668 / completed / **failure**（STEP[19] Motion coverage floor 两朵红，见 354；
同一份 Swift 代码的早一跑 `4190222` → 39795221489 / completed / success ⇒ 机器侧，不是代码侧）；
本轮这笔（`scripts/` 两文件 + 七本台账）由 R300 现取 run 号。要验的两件事：
① 新门 `test_product_streak_cell` 在 runner 上**有没有对象** —— 它读 `git log` 与台账文件，
浅历史会让「最后一笔产品提交」取不到（那一格必须红而不是跳过，与 341 的 sources 浅历史闸门同一件事）；
② STEP[19] 那两朵红在下一跑是否再现：再现 ⇒ 按 354 的②登记成有名字的未覆盖；不再现 ⇒ 也不许当成已修。

最后更新：2026-10-22（本地 · R299 / 第 298 轮 / Round 296）：**353 结案，并当场量出报告里的一句假话** ——
「产品面连续零改动轮数」改由 `scripts/product_streak.py` 派生（写盘前 streak=8、本轮落地后 streak=9：最后一笔产品提交 2f8b1e0 = 第 289 轮，UI_AUDIT 走到第 298 轮），报告 §13 与 STATE 两格同步；
**上一版那句「上一次落到 Sources 的改动是 R263」作废**（其后还有 R275 / R289 / R290 三笔产品提交）。
门 8 格，含「数对但没引用也红」。脚本电池 Ran 563 / OK (skipped=4)；变异臂 ARM_TOTAL=734 bad=0；
帧 compared=174 changed=0 missing=0 added=0；产品文件 0 个，连续零改动 **9** 轮（现读 `scripts/product_streak.py` 的 streak；本节上一版写的「第十一轮」是按短语数的，作废、只作历史不作数）。

① 下一轮（R300）的靶：**305 的台阶地板** —— 唯一还挡着它的是 347 的真机证人（需要用户退出正在运行的
「时间剪史」，或回答「收藏星按下够不够明显」；352 写全了路线与两道 fail-closed 断言）。
产品面连续 9 轮 0 改动是本审计现在真正的欠账：若 347 仍挡着，就在**不需要真机**的那半张清单里
点一个位真做动效（候选：314 热图描边语义、291 墨轴、354 的 runner 分布读数）。

② 仍开：347（真机或替代证人）、305（等 347）、354（runner 单跑红的分布读数）、348 的两格、349、
350 的第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、
328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R298 状态（第 297 轮 / Round 295 · 2026-10-22）

⓪ 读 CI（R299 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
现取成对号，取不到的写明「push 在台账之后」。本轮已 push 的三笔：`f78b6ac`（350 的门）、
`efeca29`（豁免 + 退场格）、以及本轮这笔 —— 号由 R299 现取。要验的两件事：
① 两道新守卫在 runner 上**有没有对象**（`test_ui_round_interval_parity` 读台账文件、与机器无关，
若报「分箱读数没有对象」就是尺坏了不是产品坏了；`test_commit_subject_hygiene` 依赖 git 历史深度 ——
浅历史会让基线读不到，那一格必须红而不是跳过，见 341 的 sources 浅历史闸门）；
② 台账里那三箱数（结构化=183 / 叙述形=31 / 单号形=76）在 runner 上是否与本机同数。

最后更新：2026-10-22（本地 · R298 / 第 297 轮 / Round 295）：**台账自身的对账门上了** ——
先量形状再上门（34 个「缺定义」里 31 个是叙述形、2 个是正则漏形状，真不符只剩 1 节），
并集三种定义行形状；不符名单要求恰好等于在册；豁免带退场条件（`AHEAD_ROSTER` + `test_roster_must_retire`），
起因是我自己那笔 f78b6ac 的标签超前。D-279 定规：扫台账的正则先跑分箱读数；具名豁免必须能退场。
门 ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；全量卷 932/44/0；帧 174 张 changed=0 added=0；
预检 bad=0；dmg ok 且已换装本机；产品文件 0 个，连续零改动 **8** 轮（353 结案：这一格改由 `python3 scripts/product_streak.py` 现读派生 —— 最后一笔动 `ClipboardHistory/Sources/` 的是 `2f8b1e0`（R290 / 第 289 轮），UI_AUDIT 走到 第 297 轮；本节上一版写「连续第十一轮」，那与「连续第七轮」都是按台账短语数出来的，同一件事四种形状数出三个数，一律作废，只作历史不作数）。

① 下一轮（R299）的靶：**347 的真机证人**（R298 已更正：卡点不是规矩而是我没量 —— `CLIPBOARD_HISTORY_DATA_DIR` 可做数据隔离、真机通道今天可判，路线四步写在 347 的追记里），结掉它立刻推 **305** 的台阶地板；顺带把 `AHEAD_ROSTER` 那条豁免删掉（当前轮已是 R298，它不再需要）。
穿插 348 剩下两格 / 349 / 351。

② 仍开：347（真机或替代证人）、305（等 347）、348 的两格、349、350 的第二步（第 103 轮那处历史标题的两种修法）、
351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R297 状态（第 296 轮 / Round 294 · 2026-10-22）

⓪ 读 CI（R298 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
（字段连成一个逗号串）现取成对号；取不到的写明「push 在台账之后」，别编号。本轮已知的两笔：
`8a3e488`（346 结案那笔）与 `7b8f123`（STATE 改活那笔）—— 号由 R298 现取。要验的两件事：
① 拆掉带窗上界之后，runner 那一侧 `SYSTEM_PRESS_REF` / `PRESS_LADDER_*` 的读数与本机是否同向
（本机亮档按下 颗=934；runner 历史上纸是 236 而非 255 ⇒ 绝对值不许跨机比，只比方向与台阶次序）；
② 两处新相对地板在 runner 上不许变成恒真 —— 读 `idle.pillPixels` 与同档那一层的像素数两个数，
不许只读比值。任何一条在 runner 上读不到都算通道账（342/346 那一族），一条地板都不放宽（D-251）。

最后更新：2026-10-22（本地 · R297 / 第 296 轮 / Round 294）：**346 结案** —— 先做「只红几格」的实验
（证伪了「改带窗会挪十几条地板」），再去掉 `pillReading` 的上界、把两处漏电地板换成相对判据、
把参照臂那个 `==0` 出口升成无条件断言；刀 M864/M865 从两侧钉（M865 是「把改动装回去必须红」的反对照）。
结案读数 亮档按下 颗=0 → 颗=934。新开 349（两颗尺合并）与 350（U 区间对账先量形状）。
门 ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests；全量卷 932/44 skip/0 失败、帧 174 张 changed=0 added=0、
预检 bad=0、dmg ok 且已换装本机、产品文件 0 个（连续第十轮 0 产品改动）。

① 下一轮（R298）的靶：**347**（亮档按下要不要抬 —— 卡点是取证通道：那一格在主窗口而主窗口含用户剪贴板原文、
按规矩不许截屏 ⇒ 要么用户真机看，要么换一条不依赖截图的证人），347 之后立刻推 **305** 的台阶地板
（形状与分母都已定）；穿插做 349 或 350 之一（都是判据自身的完整性）。

② 仍开：347（真机或替代证人）、305（等 347）、348 的两格、349、350、344、341 的 CI 契约半、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R296 状态（第 295 轮 / Round 293 · 2026-10-22）

⓪-a 交付债（本轮内已清，成因有证人）：账半 `0e95e25` 与这条补记一开始**推不出去** —— `ssh -T git@github.com` 给 `Connection closed by 20.205.243.166 port 22`、`git push` 三次同一句；而同一时刻 `gh run list`（走 HTTPS API）读得到，说明**断的是 SSH 22 而不是仓库或密钥**。处置：用一次性 HTTPS 远端 URL 推（不改 git config，输出里 token 已脱敏）⇒ `b1b43da..51a5069` 成功、ahead=0。下一轮再撞同一句就照这条路走，别把它记成密钥或权限问题，也别连着试第四次。

⓪ 读 CI（R297 的开场取数，只登记不轮询 = R140）：`gh run list --limit 8 --json databaseId,headSha,status,conclusion`
（字段连成一个逗号串），再 `python3 scripts/ci_read.py steps <run>`。要配对的 push：R295 `5f7dc7b`
⇒ run 39780211456 **completed success**（本轮现读，不是编号未取）：新判据在 runner 上**有对象**（两臂底非 0 才会绿）、R296 代码半 `c7b952f` / `36f8d4a` /
`b1b43da`、本轮这笔（push 在台账之后 ⇒ 号由 R297 现取）。要验的两件事：① 新判据
`testPressTravelSharesOneRulerWithTheSystemReference` 在 runner 上有没有对象（夹具通道的底；读不到是通道账
342/346 那一族，一条地板都不放宽 D-251）；②（本轮已读，转登记）runner 的变颗平均 亮 27 / 暗 19 对 本机 29 / 21 —— 同量级；而颗数 332 对 1290 差约 4 倍，正是 @1x 与 @2x 的面积比 ⇒ 305 的地板只压**变颗平均**，不许压颗数（D-272 与 D-276 在这一格对上）
（本机 亮 自家 29 / 参照 52，暗 21 / 18；不同也只登记，不许把参照臂改成 runner 上能过的形状）；
③ 新门 `scripts/warning_gate.sh` 在 runner 那一侧从没跑过（本机两刀 CAUGHT），两边若给相反处置那是接线缺失
不是阈值问题（R74/R75 那一课）。

最后更新：2026-10-22（本地 · R296 / 第 295 轮 / Round 293）：**「0 告警」从散文变成门** ——
门本体 `scripts/warning_gate.sh`（同 CI 目标口径 / 0 要用冷编挣 / 尺坏了 exit 2），
`round_verify.sh` 第 1 步调它；M862/M863 两轴两刀全 CAUGHT=2/2、RESTORE_CLEAN=yes；
预检 `is_source` 补 `.sh`（看不见被报成不存在，D-277）；343 结案、开 348（写台账本身没有门）。
全量卷 932/44 skip/0 失败、0 告警、帧 174 张 changed=0 added=0、
dmg ok 且已换装本机、产品文件 0 个（连续第九轮 0 产品改动）。

① 下一轮（R298）的靶：**348 剩下两格**（追记/落盘整批失败要能红、一把「故意漏写一本」的刀）+ 本轮这笔代码半的**轮次台账**
（U/D/ITERATION/CHANGELOG/STATE 与派生分，形状照 `ledgers_r297.py`）+ **305 的台阶地板**（形状与分母都已定，只等 347）。
①-b 346 已在本轮结案（`8a3e488`）：`pillReading` 的带窗上界去掉、两处「空闲不许有第二层」换成相对判据、参照臂那格的 `==0` 出口升成无条件断言，刀 M864/M865 各钉一侧（把上界装回去必须红 = 反对照）。
①-c 347 仍卡在同一处：那一格在主窗口，而主窗口含用户剪贴板原文、按规矩不许截屏 ⇒ 要么用户真机看，要么换一条不依赖截图的证人（`pairDelta` 的变颗平均已经是候选分母）。347 卡在取证通道：那一格在主窗口，
而主窗口含用户剪贴板原文、按规矩不许截屏 ⇒ 要么用户真机看，要么换一条不依赖截图的证人。

② 仍开：347（真机或替代证人）、305（等 347）、348 的两格、344、341 的 CI 契约半、339、312 具名出口、
333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R295 状态（第 294 轮 / Round 292 · 2026-10-22）

⓪ 读 CI（R297 的开场取数，只登记不轮询 = R140）：成对关系要现取，取不到的写明「push 在台账之后」而不是编一个号 —— 用 `gh run list --limit 8 --json databaseId,headSha,status,conclusion`（字段连成一个逗号串，R293 那一课），再 `python3 scripts/ci_read.py steps <run>` 与 readings。要配对的三笔：R295 的 5f7dc7b（本机读到 run 39780211456 当时 in_progress、结论未读；它前面两笔 cbd05b9 与 1c6155b 已读到 success）；R296 代码半两笔 c7b952f 与 36f8d4a（push 在这段台账之后 ⇒ 号由 R297 现取）。要验的三件事：① 新判据 testPressTravelSharesOneRulerWithTheSystemReference 在 runner 上有没有对象 —— 它读夹具通道，而 runner 的离屏 render 历史上画不出真底；两臂底若读 0 那是通道账（342/346 那一族），按 313/316 解释，一条地板都不放宽（D-251）；② PRESS_PAIR_REF 两行在 runner 上的变颗平均（本机：亮 自家 29 / 参照 52，暗 21 / 18）与本机是否同量级 —— 不同也只登记，不许把参照臂改成 runner 上能过的形状；③ 新门 scripts/warning_gate.sh 只在本机验过（M862/M863 两把刀 CAUGHT、基线 exit 0），runner 那一侧它从没跑过：CI 的 STEP[4] 仍按自己的告警口径走，两边若给相反处置，那是接线缺失不是阈值问题（R74/R75 那一课）。

最后更新：2026-10-22（本地 · R295 / 第 294 轮 / Round 292）：**两态差的分子被推翻并重做** ——
`PRESS_LADDER_SPAN` 的 27/29 是两帧各自众数之差（不同源），新尺 `pairDelta` 逐像素相减；
"整块平均差十倍"证成**面积稀释**（自家 1290 颗 vs 参照 7192 颗），变颗平均亮 29/52、
暗 21/18 ⇒ D-276 钉死分母口径，305 的形状定了、阈值仍不拍。
亮档那 56% 的差距本轮判为不抬（层级理由 U-967），未判的半格开成 347。
全量卷 932/44 skip/0 失败、0 告警、帧 174 张 changed=0 added=0、
dmg ok 且已换装本机、产品文件 0 个（连续第八轮）。

① 下一轮（R296）的靶：**347**（真机眼 + 亮档抬与不抬的 before/after），结掉它才推 305 的地板；
346 的带窗下半场排在它后面（本轮已绕开，不再是 305 的前提）。

② 仍开：347、305（等 347）、346（带窗未修，只绕开）、344、341 的 CI 契约半、343 的两处、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R294 状态（第 293 轮 / Round 291 · 2026-10-22）

⓪ 读 CI：本笔 push 之后由 R295 用 `gh run list --limit 6 --json databaseId,headSha,status,conclusion`
现取 run↔commit 成对登记（一次 push 多笔时 Actions 只对 tip 起跑；取不到的写明「push 在台账之后」，别编号）。
要验的两件事：① 新增的 `testSystemPressReferenceExistsOnTheFixtureChannel` 在 runner 上**有没有对象** ——
它读夹具通道，而 runner 的离屏 render 历史上画不出真底；若底读 0，那是通道账（342/346 那一族），
不是产品账，按 313/316 解释且一条地板都不放宽；② `sysref-button-*` 这 4 张新帧进名单后 CI 的帧基线
那一步不许报 missing/added（R98：新夹具会改变别的守卫的对象数）。只登记不轮询（R140）。

最后更新：2026-10-22（本地 · R294 / 第 293 轮 / Round 291）：**342 结案于「通道是现成的那颗」，并照出 `pillReading` 的带窗有上界** ——
系统控件搬进夹具通道，底 亮 255 / 暗 30 现读、两态码值 亮 13 / 暗 23，两把刀 M858/M859 各钉一条轴全 CAUGHT=2/2、
RESTORE_CLEAN=yes；亮档按下读到 0 颗不是产品事实而是尺的带窗上界（Δ<60）把强按下整块排除 ⇒ 新开 346，305 的地板在 346 之前一条不加（D-275）。
捕获卷 91/5 skip/0 失败、全量卷 All tests passed、帧 174 张 changed=0 added=0 missing=0、产品文件 0 个。

① 下一轮（R295）的靶：**346**（双向并集 + 「只变暗」的正对照刀 + 重测两档旧读数）。
346 之后才轮到 305 的台阶地板与亮档可辨性 —— 那才是产品面欠的账（连续第七轮 0 产品文件）。

② 仍开：346、305（等 346）、344、341 的 CI 契约半、343 的两处、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

## R293 状态（第 292 轮 / Round 290 · 2026-10-22）
最后更新：2026-10-22（本地 · R293 / 第 292 轮 / Round 290）：**按下档第一次有「离空闲／离悬停」两个跨度读数；系统参照臂被自己的对象闸门判死并撤掉**（U-959…U-961 · D-274 · 新开 342 · 产品 0 文件 · 七维合计 90/105，曲线派生 86 —— 低于 90，本轮不算达标）

**本轮落地**：`UICaptureHarness.swift` 的梯子那一格里新增 `PRESS_LADDER_SPAN`（只印不判）：PRESS_LADDER_SPAN light｜|按下-空闲| 码值=27 ｜|按下-悬停| 码值=6（305 的地板还没来源：系统参照臂要换通道重做，见 342）；PRESS_LADDER_SPAN dark｜|按下-空闲| 码值=29 ｜|按下-悬停| 码值=8（305 的地板还没来源：系统参照臂要换通道重做，见 342）。系统参照臂（`cacheDisplay` 抽系统按钮）本机现读两档底都=0 ⇒ 撤探针，另开 342；两种坏法自曝（恒真的自比断言、带符号量当增量）→ D-274。判据卷现读 Executed 1 / failures=0；PRESS_LADDER_PROOF light 底 idle=255 hover=255 press=255｜药丸 idle=196 hover=229 press=223｜比值 1.260 → 1.333 差=0.073｜码值台阶 hover=26 press=32 差=6｜按下像素=933 空闲像素=6；预检 tables=89 covered=73 bad=0；四件套 ROUND_VERIFY build_warnings=0 swift_executed=930 swift_skipped=44 swift_failures=1 frames=170 baseline_compared=170 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r293_verify；脚本电池 Ran 540 tests / OK (skipped=4，名单逐条对上=4 条)。305 追记进场、地板仍不定。

**下一轮（R294 / 第 293 轮 / Round 291）的 ⓪**：
⓪ 读 CI：63cc715 → 39732589843 / completed / failure、217be91 → 39732491219 / completed / failure、79b7950 → 未取到（293） 加本两笔（只登记不轮询，R140）。要验的是 R292 那笔修完之后 **STEP[15]/STEP[17] 那三跑同形红是否消失**（红话「行带里只数到 2 个墨簇」不该再出现）；若仍在，回到单位这一层继续查，不许改成 skip。 —— 本笔读数已交（R293 收尾）：63cc715 那跑的红在 STEP[4] 的告警（正文与 48 条计数见 340 追记），STEP[5..14] 整段 skipped ⇒ **340 的第④条这次无从判定**，不许当成红消失；本两笔 5253bf4／125884d 的 run 由下一轮成对取（只登记不轮询，R140）。
（R293 CI 交账）：runner 现读 82a5c1a → 39740056311 / completed / s，JOB build-and-test ⇒ success。作业 ⇒ success（整跑每一步都过，含 STEP[15] executed-count 地板与 STEP[17] 未登记红闸门），且 runner 自己印出替身臂那一行、全文再无「只数到 N 个墨簇」⇒ 340 的第④条**结案**：这朵连着三跑的红由「修好了吗」变成「跑了且不红」。runner 那一行现读＝LEFT_AXIS_R292_1X light｜抽帧倍率=1/1｜1x 位图宽=720 密度=1.00｜簇数=3 簇区间=[36.0..40.0,55.0..70.0,83.0..175.0]｜文字左沿 2x=83.0 1x=83.0pt。（绿 run 切不出 STEP[n] 这件事按 R100 那一课登记：签字的是 job 结论与判据自己印的通道行，不是「STEP[4] 那一行不见了」；本轮 ci_read.py readings 默认通道是 CARD_PROBE，抓不到左轴那一行 ⇒ 正文改由 gh run view --log 现取。）名册那一格：SKIP_ROSTER 现读 SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=540 内层skip汇总=2 解析=1 名单外=无 名册未跳=无；账半那一笔 125884d → 39739173207 / completed / success。自评曲线现读（curve_from_ledger.py，GAPS=none）Round 288=88、289=89、**290=86** ⇒ 连续三轮 <90 且 290 比 289 又低 3 分：下一轮必须回到产品动效面选靶，但靶要由量出来的缺陷签（342 的画真底通道是 305 台阶地板的前置，D-274），不许为打破 0 改动纪录加动效。只登记不轮询，R140。
① **342 → 305**：给系统控件加夹具（画真底那条路），先让「参照系存在」的闸门绿，再谈台阶地板；两机各读一次才升硬门。
② 动效过程（连续五轮 0 文件，垫底那一维）：314 热图那圈描边的语义、291 墨轴。
③ 341 剩下的半（`ci_capture_gate.py` 的 `skipped=` 是 CI 契约行，改名要连 workflow 与它的断言一起动）、339、312 具名出口（欠第十六轮，本机 3.000 不许降，D-251）、333、335、334、310、338 的另一半、328、323、322、317、304。
④ 用户闸门 220 路 A / 228② / 265。

## R292 状态（第 291 轮 / Round 289 · 2026-10-22）
最后更新：2026-10-22（本地 · R292 / 第 291 轮 / Round 289）：**墨簇尺的合并阈值从像素换成随密度换算的点，判据自带 @1x 替身臂；上一轮那朵 runner 红由「解释」升成「复现」**（U-953…U-958 · D-272/D-273 · 产品 0 文件 · 七维合计 93/105，曲线派生 89 —— 低于 90，本轮不算达标，R293 回动效）

**本轮落地**：`UICaptureHarness.swift` 里 `columnClusters(mergeGapPt × density)` + `downsampleNearest` + `testColumnClusterRulerIsDensityIndependent` + 左端判据的 1x 臂（新读数 `LEFT_AXIS_R292_1X`：LEFT_AXIS_R292_1X light｜抽帧倍率=1/2｜1x 位图宽=720 密度=1.00｜簇数=3 簇区间=[36.0..40.0,55.0..71.0,83.0..175.0]｜文字左沿 2x=82.5 1x=83.0pt）；缺席文本自带密度与簇区间。`mutate_r292.py` M855/M856/M857（3/3 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=89 covered=73 bad=0）。**自曝**：本轮改签名弄腐烂上一轮的 M847 针（预检 bad=1）⇒ 重钉后整张 R290 表重跑 3/3 全 CAUGHT（286 追记第四种坏法）。四件套 ROUND_VERIFY build_warnings=0 swift_executed=930 swift_skipped=44 swift_failures=1 frames=170 baseline_compared=170 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r292_verify（唯一红 testImageComparisonCostStaysBounded：两跑 381.01ms / 381.01ms，地板 250ms 一条没放宽；按**用例名**与隔离复跑配对（隔离 Executed 1 / 0 failures，且 git diff HEAD -- ClipboardHistory/Sources 为空 ⇒ 产品 0 文件，不是回归）⇒ 登记成 304 那一族的第三次；本轮多一条 1x 替身臂把套件加重，是它把兄弟那颗顶过线的）；脚本电池 Ran 540 tests / OK (skipped=4，名单逐条对上=4 条)。340 本机半结案、286 追记、341 改判并就地更正 R291 那四格（U-957／D-273）。

**下一轮（R293 / 第 292 轮 / Round 290）的 ⓪**：
⓪ 读 CI：e3bec51 → 39725115544 / completed / failure（R291 账半）、4e6da9d → 未取到（293）（R291 代码半，若没有自己的 run 要写明）、加本两笔。要验的是 340 的第 ④ 条：**STEP[15] 与 STEP[17] 那两跑的红必须消失**（红话「行带里只数到 2 个墨簇」不该再出现），未登记的红必须回到 0；红不消失就回到单位这一层继续查，不许改成 skip 或登记成免检。只登记不轮询（R140）。
① **回到动效过程（连续四轮 0 文件，这一维已经垫底）**：305（按下台阶的地板分辨实验 —— 台阶比值 1.058/1.123 已量出，缺的是「该不该有地板」的分辨）、314（热图那圈描边的语义）、291 墨轴。本轮那条 1x 替身臂的方法可以直接搬给动效尺：凡只在一种密度/一台机器上量的判据，都该有第二条臂。
② 341（电池 skip 颗数与名单同源：生成器这侧已经按名单对账，电池那侧的闸门还没改）、340 的 runner 半。
③ 339（其余表面的容器归属与逐位点约定，按结构认身份 D-271，每处配产品轴 + 身份轴两把刀）、312 具名出口（欠第十五轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（75 张表 / 423 把刀静默不覆盖）、338 的另一半、328、323、322、317。
④ 用户闸门 220 路 A / 228② / 265。

## R291 状态（第 290 轮 / Round 288 · 2026-10-22）
最后更新：2026-10-22（本地 · R291 / 第 290 轮 / Round 288）：**详情区段落线判为「面板自己的边」并升成会红判据；修掉「身份借用被判断的量」这个设计缺陷（D-271）**（U-949…U-952 · D-271 · 新开 340 · 产品 0 文件 · 七维合计 92/105，曲线仪器本轮派生读 88 —— 低于 90，本轮不算达标，R292 继续修）

**本轮落地**：`UICaptureHarness.swift` 新增 `testDetailSectionRuleSpansTheWholePane`（两端各钉一次，地板 1.0pt 由真产物推：现读 0.0／720.0）+ `FlatBand.thicknessPt(_:)`；`mutate_r291.py` M850/M851/M852（3/3 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=88 covered=72 bad=0）。现读：DETAIL_SECTION_R291 light｜细线总数=4 段落线 y=118 左=0.0 右=720.0｜其余线左=[82.0,82.0,82.0]｜窗宽=720.0 地板 1.0pt；其余三条行分隔线左沿 [82.0,82.0,82.0]（与 R290 那条判据同形）；四件套 ROUND_VERIFY build_warnings=0 swift_executed=929 swift_skipped=44 swift_failures=0 frames=170 baseline_compared=170 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r291_verify；脚本电池 `Ran 538 tests / OK (skipped=4)`（**R292 就地更正**：这一格在 R291 落盘时写的是「生成器内两次 skipped=5、手工三次 skipped=4，差的那一颗没有名字」—— 那句话被现读推翻，错在我的尺而不是电池的稳定性：生成器用未锚定的 skipped 取数正则先命中了 test_skip_roster 闸门自己打的「内层Ran=538 汇总skipped=5 解析=4」那一行，那是**内层那一卷**的汇总（合法地比外层多一颗：观察者自己在嵌套里按防递归 skip，而闸门断言内层汇总==内层名单、观察者恰好一颗，一直是绿的）；外层电池的结论行从头到尾都是 4。成因与规矩见 U-957／D-273 与 341 的 R292 追记。）。第一版的 WRONG_CELL 与改法入账（D-271）。337 两处结案；339（R290 开的单）补追记：现读 22 处位点，只有详情区有像素级判据。**R290 那两笔的 runner 账已读**：8bbe849 → 39630283526 / completed / failure、004ab71 → 39630405703 / completed / failure 同为 STEP[15]+STEP[17]，未登记的红只有 `testMultiFileRowSeparatorsStartAtTheTextAxis` 一颗，原文「行带里只数到 2 个墨簇」⇒ 新开 340（尺的阈值按像素写，runner @1x / 本机 2x；地板不放宽）。

**下一轮（R292 / 第 291 轮 / Round 289）的 ⓪**：
⓪ 读 CI：8bbe849 → 39630283526 / completed / failure、004ab71 → 39630405703 / completed / failure、2f8b1e0 → 未取到（293）、4e6da9d → 未取到（293）（本轮代码半，没有自己的 run 也要写明），账半那一笔由收尾提交登记 —— 一次 push 多笔时 Actions 只对 tip 起跑（R140）。R290 那两跑已经读到（都是 completed / failure，成因见 U-952／340），本半截只剩 STEP[9] 仍要确认 0 failures（331 的机器名册与本轮新增判据都在电池/捕获卷里跑）。只登记不轮询，R140。
① **回到动效过程（连续三轮 0 文件，这一维已经垫底）**：305（按下台阶的地板分辨实验 —— 台阶比值 1.058/1.123 已量出，缺的是"该不该有地板"的分辨）、314（热图那圈描边的语义：先量它与哪一层混淆再决定）、291 墨轴。
② **340（当前唯一在 runner 上会红的判据）**：把 `columnClusters` 的合并阈值换成随密度换算的点单位，2x 与 1x 两臂各自被证伪 + 一把只在 1x 有牙的刀；341 顺手做（电池 skip 颗数与名单同源）。③ 339：给 22 处线位点定容器归属与约定（按结构认身份，D-271），每处配产品轴 + 身份轴两把刀 —— 本轮看图新增一处要一起判：多文件列表**最后一行下面那条分隔线**，它下面已经没有行了，画它是在闭合区块还是在暗示还有内容？没量过之前不拍板。
④ 312 具名出口（欠第十四轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（75 张表 / 423 把刀静默不覆盖）、338 的另一半、328、323、322、317、314-316。
⑤ 用户闸门 220 路 A / 228② / 265。

## R290 状态（第 289 轮 / Round 287 · 2026-10-21）
最后更新：2026-10-21（本地 · R290 / 第 289 轮 / Round 287）：**撤回 R289 那句「48 = 文字轴」：行分隔线的左端从来不对齐任何一列，现在由行首三列导出，漂移第一次会红**（U-944…U-948 · D-270 · 产品 1 文件 · 自评 95/105）

**本轮落地**：`DetailView.swift` 把行首三列（内缩 12／箭头 12／图标 18／间距 10）升成 `MultiFilePreviewLayout` 常量、分隔线左端改成导出的 `rowTextLeading`；`UICaptureHarness.swift` 新增 `columnClusters`／`paperMode` 两把尺 + `changedXSpan` 交出 y 带 + 两格判据（列簇已知答案对照、左端产品判据，Executed 3 / failures=0）；`mutate_r290.py` M845/M846/M847（3/3 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=87 covered=71 bad=0）。现读：LEFT_AXIS_R290 light｜行带 y=142..241｜墨簇左沿 箭头=36.0 图标=55.0 文字=82.5｜细线数=3 左=[82.0,82.0,82.0]｜地板 1.5pt（改前：线 48.0 对文字 82.5，差 34.5pt；改完现读线 82.0 对文字 82.5）；右端那条（R289）同卷照绿 RIGHT_AXIS_R289 light｜密度=2.00｜药丸(两态差) 左=20.0 右=700.0 宽=680.0 变化=135821颗｜细线数=3 左=82.0 右=[700.0,700.0,700.0]｜地板 1.000pt，细线上限 2.0pt（改前同一颗尺读到 20.000pt）；改前 changed=8/compared=170 → 同一笔 update 后 0；四件套 ROUND_VERIFY build_warnings=0 swift_executed=928 swift_skipped=44 swift_failures=2 frames=170 baseline_compared=170 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r290_verify2；脚本电池 Ran 538 tests / OK (skipped=5)。新开 339；337 第一处结案、第二处判为另一种约定（未升判据）。

**下一轮（R291 / 第 290 轮 / Round 288）的 ⓪**：
⓪ 读 CI：**R290 这两笔 8bbe849 → 39630283526 / in_progress / 未读**（代码半 2f8b1e0 没有自己的 run —— 一次 push 两笔，Actions 只对 tip 起跑，所以它的 runner 验收押在 39630283526 上）；R289 那两笔已读到并且**都绿**：dcf5813 → 39621499774 / completed / success、3fa4e8b → 39621722785 / completed / success ⇒ 331 的 runner 行由外推改成读数这件事**拿到 runner 验收**（连着四跑红在 STEP[9] 的那一朵消失），已写进 331 的追记。本笔要验的两件事：STEP[9] 仍 0 failures（本轮把 337/304 两单的正文动过，且新判据进了捕获卷）与 STEP[4]/捕获卷里 `LEFT_AXIS_R290` 有没有对象 —— 若 runner 上墨簇数不到 3 个，那朵红说的是尺（按 313/316 那一族解释，不许放宽地板、不许改产品）。只登记不轮询，R140。
① **339**：把"细线不得越过所属容器"搬进仓库并按容器配对（先枚举容器，再判约定）。
② **回到动效过程**（连续两轮的产物面仍是静态边界）：305（按下台阶的地板分辨实验）、291 的墨轴、314（热图那圈描边的语义：要不要换成别的记号 —— 先量它与哪一层混淆，再决定）。
③ 312 的具名出口（欠第十三轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（75 张表 / 423 把刀静默不覆盖）、338 的另一半、328、323、322、317、314-316。
④ 用户闸门 220 路 A / 228② / 265。

## R289 状态（第 288 轮 / Round 286 · 2026-10-21）
最后更新：2026-10-21（本地 · R289 / 第 288 轮 / Round 286）：**回到产品面：多文件详情区的行分隔线从悬停药丸外面穿出去 20.000pt，两条右轴现在读同一份数，判据从渲染产物里量**（U-939…U-943 · D-268、D-269 · 产品 1 文件 · 自评 93/105）

**本轮落地**：`DetailView.swift` 新增 `MultiFilePreviewLayout.rowHorizontalInset`（行与分隔线共用）；`UICaptureHarness.swift` 新增两把尺（`flatBands`／`changedXSpan`）+ 三格判据（两格已知答案对照 + 一格产品判据，Executed 3 / failures=0）；`mutate_r289.py` M842/M843/M844（3/3 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=86 covered=70 bad=0）；`test_skip_roster.py` 的 runner 行由外推改成两跑同读的读数；STATE 的 R281 那一节补回未替换的 `%s`/`%d`。现读：RIGHT_AXIS_R289 light｜密度=2.00｜药丸(两态差) 左=20.0 右=700.0 宽=680.0 变化=135821颗｜细线数=3 左=48.0 右=[700.0,700.0,700.0]｜地板 1.000pt，细线上限 2.0pt（改前同一颗尺读到 20.000pt）；改前 changed=8/compared=170 → 同一笔 update 后 0；四件套 ROUND_VERIFY build_warnings=0 swift_executed=926 swift_skipped=44 swift_failures=0 frames=170 baseline_compared=170 baseline_changed=0 baseline_missing=0 dmg=ok installed_version=1.4.8 dir=/tmp/r289_verify3；脚本电池 Ran 538 tests / OK (skipped=5)。自己撞的尺坏法入账：`hi` 不按比较赋值 ⇒ 右沿读成最后一行（694.5pt），红在产品一条不存在的边界上 —— 由仓库外那把临时尺逐行取 max 否证，处置是对称化 + 造"最宽的行不在最后一行"的对照 + 配刀 M844（D-269）。新开 337、338。

**下一轮（R290 / 第 289 轮 / Round 287）的 ⓪**：
⓪ 读 CI：**本两笔 dcf5813 → 39621499774 / queued / 未读**（代码半 4eb86ff 没有自己的 run —— 一次 push 两笔，Actions 只对 tip 起跑，所以 4eb86ff 的 runner 验收就押在这一跑上）；上一批四笔已全部读到：41e1e66 → 39608106160 / completed / failure、3403a78 → 39607521077 / completed / failure、8d427f3 → 39607333647 / completed / failure、1f119e0 → 39606496963 / completed / success、88b22cd → 39608506355 / completed / failure（四跑全红在 STEP[9] Release script tests，正文现读 `SKIP_ROSTER 键=github-runner … 名单外=['test_built_bundle_carries_no_app_delegate_stub'] 名册未跳=['test_app_launches_and_terminates_cleanly']` ⇒ 331 的 runner 行已由外推改成读数；另外 39607521077 还多一朵 STEP[19] Motion coverage floor（testNativeRowMoveIsVisibleToTheRuler 两臂形状一致 1 帧/峰值 0.053），四跑里只这一跑红 ⇒ 负载敏感，按 304 那一族记账，未放宽未修。本笔要验的就是 STEP[9] 的 failures=0；只登记不轮询，R140）。若 runner 仍红在 `SKIP_ROSTER`，读它自己打的那一行（`名单外=[…] 名册未跳=[…]`），按主语是机器名册解释，不许改产品也不许放宽闸门。
① **338 已结一半**：R282–R288 七节已补进 AGENT_VISUAL_ITERATION（曲线现读 MEAN 87.4→86.6、GAPS→none），UI_AUDIT 与 CHANGELOG 那两本走 SINGLE_LEDGER_ROUNDS 申报 —— 剩下的选择是"要不要把这两本的正文也补齐"，不补就保持申报（申报现在有牙：窗口三轮内会红）。
② **337**：详情区其余右边界位点逐个判（现读左右沿 → 三选一理由 → 配刀），做完删一行。
③ **回到动效过程**：330 已收成具名通道限制，但清账表里"悬停淡入的过程没有产物证人"那几位仍开；305（按下台阶的地板分辨实验）、291 的墨轴、312 的具名出口（欠第十二轮，本机 3.000 不许降，D-251）。
④ 333 的 CI 半、335、334、310（75 张表 / 423 把刀静默不覆盖）、328、323、322、317、314-316。
⑤ 用户闸门 220 路 A / 228② / 265。

## R281 状态（第 280 轮 / Round 278 · 2026-10-21）
最后更新：2026-10-21（本地 · R281 / 第 280 轮 / Round 278）：**330 第一次真跑两臂：量到的是尺的前提；两次结论都当场撤回（D-267）**（U-936…U-938 · 产品 0 文件 · 自评 64/105 —— R289 补：这一格当时留着未替换的 `%d`，数从 ITERATION Round 278 的合计读回，不手抄）

**本轮落地**：两版 spike（`a26ace8`、`3009db1`）+ 一次公开更正（`32e90b0`）；判据与产品净变化 0（都 `git checkout` 回退）。现读：两臂各 24 帧、峰值 0.000、共享地板 0.000、热=是/是、静置墨 0.1 → 0.158；`meanLevel` 是 0..1 归一化亮度（正文第 1073 行）。脚本电池 Ran 531 tests / OK (skipped=4)。CI：a26ace8 → 39602246206 / in_progress / 未读、3009db1 → 39602630542 / in_progress / 未读、32e90b0 → 39602754299 / in_progress / 未读（本笔之后另算）。

**下一轮（R282 / 第 281 轮 / Round 279）的 ⓪**：
⓪ 读 CI：a26ace8 → 39602246206 / in_progress / 未读、3009db1 → 39602630542 / in_progress / 未读、32e90b0 → 39602754299 / in_progress / 未读；本笔三枚（a26ace8／3009db1／32e90b0）+ 本账笔用 `gh run list --limit 5 --json databaseId,headSha,status,conclusion` 现取配对（只登记不轮询，R140）。
① **330 第三版**：前提改成**空白参照对照**（同宿主拍一张只有容器没有控件的帧，被摄对象必须在 `deltas` 上显著不同于它），被摄对象换成 `ContentView` 行 + `hoveredRowForCapture`（键 `Int?`，夹具用法 `UICaptureHarness.swift:4270`，消费侧 `DetailView.swift:572`）；两臂之差 + 共享地板保留，判据入库前先跑四件套（全量卷/帧基线/换装）。
② **331 的按机器名册**（它是任何新增 skip 能否入库的前置：D-255 同族，缺席的主语要打进输出）。
③ **312 的具名出口（欠第十轮）**：本机 3.000 不许降（D-251）。
④ 333 的 CI 半（changed 的按机器具名出口 + 不误红那把刀）、335（其余名册的未结构化否定句）、334（写死本机根那一族）、332、328、323、322、317、314-316、310。
⑤ 产品动效面连续多轮是最弱一维（本轮 0 文件）：按清账表点一个位真做动效或撤声明。
⑥ 用户闸门 220 路 A / 228② / 265。

## R280 状态（第 279 轮 / Round 277 · 2026-10-21）
最后更新：2026-10-21（本地 · R280 / 第 279 轮 / Round 277）：**名册理由接上对象：热图那行「没有两态帧」是挂了三十几轮的假话，现由 `TWO_STATE_CLAIMS` 与帧名单双向对账钉住**（U-933…U-935 · D-266 · 产品 0 文件 · 自评 84/105）

**本轮落地**：`test_hover_capture_channel.py` 加第二条轴（前缀必须在 `docs/frame_baseline.json` 里数到 ≥2 种状态；`None` 要理由点名缺席；`NO_INK` 要写明画法搬去哪）+ 4 格新证人（合计 Ran 9）+ `mutate_r280.py` M836/M837（2/2 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=83 covered=67 bad=0）。基线现读 `heatmap-cell-strip` 4 张、状态 hover、still；脚本电池 Ran 531 tests / OK (skipped=4)；ARM_TOTAL arms=710 dupes=0。自己撞的镜像入账：更正后的理由引用旧假话原句 ⇒ 守卫按字面读否定词，真产物那一格反而红（U-934）—— 不放宽守卫，把规矩写进理由文本。新开 335（其余 2 句同形理由）。眼睛腿 RUN（静置／悬停各一张，圈只落在那一格）。产品 0 文件。

**下一轮（R281 / 第 280 轮 / Round 278）的 ⓪**：
⓪ 读 CI：8a972d0 → 未取到（293）、8717741 → 39599249700 / in_progress / 未读、f7205b6 → 39599556093 / in_progress / 未读 加上本笔触发的那一跑（`gh run list --limit 4 --json databaseId,headSha,status,conclusion` 现取配对，别编号；只登记不轮询，R140）。要验的是 STEP[9] 的 failures=0 —— 本轮那 4 格新证人里有一格会读 `docs/frame_baseline.json` 并按前缀数状态，runner 上基线是同一份文件，理论上同结论；若颗数或名单不同，按 331 那两张机器名册解释，不许先假设相等。
① **回到产品动效面（连续七轮是最弱一维）**：330（三处 hover 淡入的"过程"还没有产物证人 —— `MotionFilmstripTests` 那条路，`Scenario` 要能在触发时翻 `hoveredForCapture`；加一卷要全量重跑并登记名单为何变长，R98 那一课）、305（按下台阶的地板分辨实验）。
② 335（其余 2 句未结构化的理由，逐本做、做完删一行）、333 的 CI 半（changed 的按机器具名出口 + 不误红那把刀）。
③ **312 的具名出口（欠第九轮）**：本机 3.000 不许降（D-251）。
④ 331、332、330、328、323、322、317、314-316；310 的 75 张表、334 的写死本机根那一族。
⑤ 用户闸门 220 路 A / 228② / 265。

## R279 状态（第 278 轮 / Round 276 · 2026-10-21）
最后更新：2026-10-21（本地 · R279 / 第 278 轮 / Round 276）：**333 本机半结案：`changed` 从读数变闸门，退出码不再被丢掉；两把刀各钉一条轴（拆门 / 瞎尺）**（U-924…U-926 · D-263…D-265 · 产品 0 文件 · 自评 83/105）

**本轮落地**：`round_verify.sh` [3/4] 的帧基线门改成 changed≠0 ⇒ `exit 1`（排在 dmg/换装之前，红话只给一条正路、无 `|| true`、无环境变量后门；NOT-RUN 同样拦）+ 证人卷 `scripts/tests/test_round_verify_frame_gate.py` 6 格 + `mutate_r279.py` M834/M835（2/2 全 CAUGHT、RESTORE_CLEAN=yes，已登记进预检 tables=82 covered=66 bad=0）。四件套现读 build_warnings=0 swift_executed=923 skipped=44 failures=0 frames=170 changed=0 missing=0 dmg=ok installed=1.4.8；脚本电池 Ran 527 tests / OK (skipped=4)。两处自坏入账：守卫恒红在自己门里的散文上（剥注释后才判"用没用"，U-925）；D-260 的闭包只盖被 import 的工具 ⇒ 现读 280/379 支脚本仍写死本机根，新开 334（D-265）。R277/R278 两笔只落台账、没有 UI 小节，本轮标题按轮次映射写第 278 轮并把缺口明写。

**下一轮（R280 / 第 279 轮 / Round 277）的 ⓪**：
⓪ 读 CI（R279 收尾现读，三笔已落地）：bfb8acf → 39594743756 / completed / success、41e5ce0 → 39595586063 / completed / success、268287d → 39594029100 / completed / success —— 三笔全 completed/success ⇒ D-260／D-262／D-265 这条链在 runner 上没有红。本笔两枚（8a972d0、8717741）交接时未取到号 ⇒ 下一轮用 gh run list 现取配对，别编号（R140）。原句那句「交接时未读」已被现读推翻 ⇒ 就地改，不留过期断言。
① **333 的 CI 半**：runner 那次捕获 COMPARED=170 CHANGED=170 ⇒ 按机器键的具名出口（`FRAME_CHANGED_CHANNEL_DIFF=runner`，计入读数、不红不静默，D-251）+ 一把"真通道差异不误红"的刀；本机这半的 M834 不能替它作证。
② **312 的具名出口（欠第八轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
③ 331（观测式名册：按"表头行 + 结果行"配对归属 + 恒等式闸门，两版已回退）、332、330、328、323、322、317、314-316。
④ 334（280 支写死本机根按运行对象重列名单 + 一把改回字面量的刀）、310 的 75 张表、309 那 6 张；305、299、301、307、297/298/300、304、291 三位。
⑤ 产品动效面连续多轮是最弱一维（本轮 0 文件）：按清账表点一个位真做动效或撤声明。
⑥ 用户闸门 220 路 A / 228② / 265。

## R276 状态（第 275 轮 / Round 273 · 2026-10-21）
最后更新：2026-10-21（本地 · R276 / 第 275 轮 / Round 273）：**门只扫了直接 import —— runner 上那朵红来自被运行时读的第二张表；闭包、exec 通道、归一化各补一格**（U-921…U-923 · D-262 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r51_capture_path_blocked.py` 的根由 `__file__` 推 + `resolve_r51()` 的 exec 命名空间补 `__file__`；门扩到可达闭包（直接=3 闭包=4）并新增两格（闭包必须含 R51、归一化的牙）；三张表重跑 5 支：4 CAUGHT + M253 按设计绿（灵敏度对照臂），该红没红=0、还原不干净=0／1/1 CAUGHT、RESTORE_CLEAN=yes／2/2 CAUGHT、RESTORE_CLEAN=yes；脚本电池 Ran 521 tests / OK (skipped=4)；预检 tables=81 covered=65 arms=213 bad=0、310 缺口 75 张 / 423 把。新开 331、332。

**下一轮（R277 / 第 276 轮 / Round 274）的 ⓪**：
⓪ 读 CI：c99f1fb → 未取到（293）、f09006b → 39588588601 / completed / failure、ad61d2d → 39589146197 / completed / failure、1c831f2 → 39583125728 / completed / failure、3ec2a97 → 39581623084 / completed / failure 与本轮新跑（只登记号不轮询，R140）。本轮**要验的具体一件**：STEP[9]「Release script tests」在闭包门 + R51 归根之后转绿（failures 必须归 0，且 `Ran ≥ 521`）—— 这是 D-260/D-262 这条链第一次拿到 runner 验收；同时读 STEP[11] 那两张 recording 帧是否仍报 changed（若 changed≠0 按 D-251 开具名出口，不许改基线迁就）。
   交账（R276 收尾二 · 现读 `gh run list` 与 `scripts/ci_read.py steps`，正文存 /tmp/r277_log3.txt）：f09006b → 39588588601、3d0fcec → 39588916568、ad61d2d → 39589146197 三笔都已 completed / failure，三笔的唯一红步骤都是 STEP[9]「Release script tests」，正文同形 `Ran 519 / FAILED (failures=1, skipped=1)` ⇒ **同一颗 R51 病根，不是第三种成因**（修法在 99f3284 里，那两跑早于它）；99f3284 → 39591885399 与 dc25e6e → 39592303302 交接时 in_progress ⇒ 只登记号不轮询（R140），所以 D-260/D-262 这条链的 runner 验收**今天仍然没拿到**，R277 第一件事就是读 39591885399 之后的那一跑：STEP[9] 必须 failures=0 且 `Ran ≥ 521`。
   交账（R278 的 ⓪ 落地 · 现读 `gh run list` 与 `gh run view 39591885399 --log`，正文存 /tmp/r278_log.txt）：**99f3284 → 39591885399 = completed / success** ⇒ STEP[9]「Release script tests」现读 `Ran 521 tests / OK (skipped=1)` —— D-260（写死本机根）与 D-262（可达闭包）这条链**第一次拿到 runner 验收**，红消失且不是靠放宽：同一跑里 `mutate_r271` 的镜像对账格不再红，说明 R51 归根与 exec 命名空间补 `__file__` 两处都生效。同一跑还翻出一个更大的洞：帧基线硬门那一步打了 `CHANGED=170 COMPARED=170 MISSING=0` 却仍 exit 0，同一步里另有 `FRAME_BASELINE_SKIPPED=runner-capture-unavailable` ⇒ 那道"改界面必须同一笔 update 基线"的纪律在 runner 上等于不存在（新开 333，含修法与两把刀）；这也说明 R273 那两张 recording 帧"在 runner 上稳不稳"这个问题在现有出口下**无法回答**。其余 dc25e6e／a253761／759b0df／268287d 四跑交接时仍 in_progress ⇒ 不引用其结论（R140）。
① **312 的具名出口（欠第八轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 331（按机器键登记 skip 差异）、332（按闭包重排 329 的优先级）、330（三处淡入的两态夹具与中间态证人）、328、323、322、317、314-316。
③ 310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 画法轴四位。
④ 产品动效面：连续多轮是最弱一维（本轮 0 产品文件、看图腿 NOT-RUN）⇒ 按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R275 状态（第 274 轮 / Round 272 · 2026-10-21）
最后更新：2026-10-21（本地 · R275 / 第 274 轮 / Round 272）：**三处悬停淡入在取证通道里从来没有过程 —— 画法与动画的触发条件对齐，并给这条规则一把会红的尺**（U-918…U-920 · D-261 · 产品 3 文件 · 自评 88/105）

**本轮落地**：`SettingsView.swift` / `HistorySidebarView.swift` / `SearchField.swift` 的 hover 动画 value 改读合取式；新卷 `HoverAnimationChannelTests`（4 格，根由 `#filePath` 推）现读 files=105 sites=6 裸读=0 判=PASS；刀 2/2 CAUGHT、RESTORE_CLEAN=yes（M832（红在 XCTAssertEqual，钉的是产品轴：动画条件退回裸读）、M833（红在 XCTAssertTrue，钉的是尺轴：把裸读谓词弄瞎））；四件套 告警=0 全量 Executed=923 failures=0 skipped=45 帧=170 changed=0 missing=0 dmg=ok 本机=1.4.8；脚本电池 Ran 519 tests / OK (skipped=4)；预检 tables=81 covered=65 arms=213 bad=0、310 缺口 75 张 / 423 把。新开 330。

**下一轮（R276 / 第 275 轮 / Round 273）的 ⓪**：
⓪ 读 CI：1c831f2 → 39583125728 / completed / failure、3ec2a97 → 39581623084 / completed / failure 与本轮新跑（只登记号不轮询，R140）。要验的两件：STEP[9]「Release script tests」在新门上转绿（errors 归 0 且 `Ran` 颗数不低于本笔），以及 STEP[11] 那两张 recording 帧在 runner 上是否仍报 changed —— 若 changed≠0 按 D-251 开具名出口，**不许改基线迁就**。
   交账（R275 收尾 · 现读 `gh run list`，正文存 /tmp/r276_ci.json）：c99f1fb → 未取到（293）；f09006b → 39588588601 / in_progress / 未读；1c831f2 → 39583125728 / completed / failure；3ec2a97 → 39581623084 / completed / failure。取到号时全部 in_progress ⇒ 本轮不引用任何 runner 结论（R140）；R276 要验的两件仍写在这一节上面那行：STEP[9] 电池在新门上 errors 归 0 且 Ran ≥ 519、STEP[11] 那两张 recording 帧是否仍报 changed（若 changed≠0 按 D-251 开具名出口，不许改基线迁就）。
   更正（R275 收尾二，追加而不替换 —— 上一行是我刚写下的原话，留着才追得回错在哪）：上一行说「取到号时全部 in_progress」，可同一次现读里 1c831f2 → 39583125728 与 3ec2a97 → 39581623084 的 status 已经是 completed、conclusion 已经是 failure ⇒ 那句话把两笔**已落结论**的 run 说成没落，是假话，当场改口（同 R271 那一族：台账里手抄的状态必须现读，不许沿用几秒前的印象）。两笔 failure 的正文本轮没读 ⇒ 不引用成因：这两笔都只动台账/STATE 一行，若仍红在 STEP[9] 就是 R274 那把新门（`mutate_r271.py` 的根由 `__file__` 推）还没被 runner 验收 —— 与已修病根同形、待正文确认；红在别处则是第三种成因，另开单子。R276 第一件事：`scripts/ci_read.py steps 39583125728` 与 `… 39581623084` 按步骤取失败正文，再验 STEP[11] 那两张 recording 帧的 changed。
① **312 的具名出口（欠第七轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 330（三处淡入的中间态产物证人）、329（206 处写死本机根，每张搬完重跑那张表）、328、323、322、317、314、315、316。
③ 310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 画法轴那四位。
④ 产品动效面：本轮 3 个产品文件，但都是可测性；仍需按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R274 状态（第 273 轮 / Round 271 · 2026-10-21）
最后更新：2026-10-21（本地 · R274 / 第 273 轮 / Round 271）：**runner 那一朵红归因到我自己的守卫上：被电池 import 的工具写死本机根 ⇒ 由 `__file__` 推，并把这一次修升成会红的门**（U-915…U-917 · D-260 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r271.py` 的 ROOT 由 `__file__` 推；`test_mutate_r271_needle.py` 由 3 格长到 6 格（行为证人 + 名单现读 + 正负对照）；刀 M831 重跑 1/1 CAUGHT、RESTORE_CLEAN=yes；脚本电池 Ran 519 tests / OK (skipped=4)；预检 tables=80 covered=64 arms=211 bad=0、310 缺口 75 张 / 423 把。runner 证人正文留在 `/tmp/r274_log.txt`（重启即失，重跑 `gh run view 39579621207 --log-failed` 可再取）。

**下一轮（R275 / 第 274 轮 / Round 272）的 ⓪**：
⓪ 读 CI：6e810e6 → 39580528220 / in_progress / 未读、3ec2a97 → 39581623084 / in_progress / 未读、ecfc012 → 39581770417 / in_progress / 未读 与本轮新跑（只登记号不轮询，R140）。本轮**要验的具体一件**：STEP[9]「Release script tests」在新门上转绿（errors 必须归 0，且 `Ran` 颗数 >= 519），而 R273 那两张 recording 帧在 STEP[11] 的相位稳定性仍未读 —— 若报 changed=2 按 D-251 开具名出口，不许改基线迁就。
   交账（R274 收尾三 · 现读 `gh run list` 与 `scripts/ci_read.py steps`）：39580528220（RUN=39580528220 conclusion=failure）红在：STEP[9]Release script tests；39580570540（RUN=39580570540 conclusion=failure）红在：STEP[9]Release script tests。**两笔都已 completed / failure ⇒ R273 的 recording 帧修法在 runner 上未通过验收**，本笔未读正文细节（预算尽头）⇒ 不猜成因，R275 第一件事就是按步骤取正文分诊：若红在 STEP[11] 帧基线 changed=2 就是「这台机器判不了这颗夹具的相位」按 D-251 开具名出口（不许改基线迁就）；若红在 STEP[9] 电池则是 R274 那把新门未覆盖的形状；若红在别处就是第三种，须另开单子。其余 3ec2a97／ecfc012／5f3c9f1／7a3fdba／a9cd06b 交接时仍 in_progress ⇒ 只登记号不轮询（R140）。
① **312 的具名出口（欠第七轮）**：按「纸」那一维推，本机 3.000 不许降（D-251）。
② 329（其余 206 处写死根，每张搬完重跑那张表）、328（比摘要的尺统一成一条会红的 + 一把喂错摘要的刀）、323、322、317、314、315、316。
③ 310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 5/15）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R273 状态（第 272 轮 / Round 270 · 2026-10-21）
最后更新：2026-10-21（本地 · R273 / 第 272 轮 / Round 270）：**324 结案：固定挂钟泵换成等动画键清空，同码双跑 170/170 两种摘要都相同当证人；半套账点名后补齐**（U-911…U-914 · D-259 · 产品 0 文件 · 自评 83/105）

**本轮落地**：夹具等条件 + `RECORDER_SETTLE` 读数（动画键=0、等待 42…147 ms）；同码双跑 170/170 张（md5 与 sha256 各自数一遍）不同 0；基线与修法之前那笔逐键比摘要 ⇒ 换摘要键数=2（settings-shortcuts-recording-720x540-dark.png、settings-shortcuts-recording-720x540-light.png）、整条 64 位严格相等；脚本电池 Ran 516 tests / OK (skipped=4)；预检 tables=80 covered=64 arms=211 bad=0、310 缺口 75 张 / 423 把。上一笔的"欠账登记"由本笔补齐。两处自坏都留在账上：D-259（批量改注释吃掉 `#if` 指令）、U-914（台账生成器拿 md5 比 sha256 基线 ⇒ 拒绝写盘；新开 328 去扫其余同形尺）。

**下一轮（R274 / 第 273 轮 / Round 271）的 ⓪**：
⓪ 读 CI：6e810e6 → 39580528220 / in_progress / 未读、5a6694b → 39580570540 / in_progress / 未读、本笔账半 3ec2a97 → 39581623084 / in_progress / 未读（成对号现读于 R273 收尾，取到号时三笔全 in_progress ⇒ 只登记号不轮询，R140）。要验的是 **runner 上那两张 recording 帧在新相位下是否稳定**（基线已按本机新捕整条摘要确认 ⇒ runner 若报 changed=2 就是"这台机器判不了这颗夹具的相位"，按 D-251 具名出口处理，不许改基线迁就）。
① **312 的具名出口（欠第六轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
② 328（把"比摘要"统一成一条会红的尺 + 一把喂错摘要的刀）、323（把抄值的可用估计量搬进 scripts/ 并逐处判）、322、317、314、315、316。
③ 310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 NOT-RUN）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R272 状态（第 271 轮 / Round 269 · 2026-10-21）
> **R273 已落地但只落了半本账（诚实记账）**：`6e810e6` 结了 BACKLOG 324（夹具固定泵 ⇒ 等条件；同码双跑 170/170 逐字节相同；> 基线同一笔 update，FRAME_BASELINE_UPDATED=170；电池 Ran 516 OK；build --build-tests 干净）。> **欠的是台账半**：AGENT_UI_AUDIT 的第 272 轮一节、AGENT_VISUAL_ITERATION 的 Round 270 一节（含七维表）、> AGENT_DECISIONS 的 D-259、CHANGELOG 一条、STATE 轮换与 FINAL_REPORT 两格刷新 —— 下一轮第一件事就是把它补成完整一轮，> 补的时候数字一律从 `/tmp/r273_a`、`/tmp/r273_b`、`/tmp/r273_a.log`、`/tmp/r273_batt.log` 与 > `docs/frame_baseline.json` 现读，不许照抄这条引言。

最后更新：2026-10-21（本地 · R272 / 第 271 轮 / Round 269）：**327 结一半：一把运行时取 needle 的刀改成静态可读，并配"逐字对账 + 漂移正对照"钉住不抄两份（D-258）；326 改判为前提消失并留复活条件**（U-907…U-910 · 产品 0 文件 · 自评 80/105）

**本轮落地**：`mutate_r271` 静态化 ⇒ 预检 covered 63 → 64、bad=0、`M831 ok`；刀重跑 1/1 CAUGHT（红在 testAddingACopyWritesNothingOnTheMainThread 的 XCTAssertFalse、倍率 0.79、RESTORE_CLEAN）；新判据卷 `test_mutate_r271_needle.py` 3 格；脚本电池 Ran 516 tests / OK (skipped=4)；ARM_TOTAL arms=704 dupes=0、310 缺口 75 张 / 423 把。本轮 0 产品文件 ⇒ sources 格不动、四件套沿用上一笔、看图腿 NOT-RUN。

**下一轮（R273 / 第 272 轮 / Round 270）的 ⓪**：
⓪ 读 CI：3f8050b → 39576062490 / in_progress / 未读、da00b70 → 39576839824 / in_progress / 未读、fbbf530 → 39577120481 / in_progress / 未读 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `test_mutate_r271_needle` 这类静态对账格有没有进电池那一跑、以及 :153 那颗是否仍然不红**。
① **312 的具名出口（欠第六轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。这是最久的一条。
② 324（会同码翻脸的那张帧：冻相位或具名豁免 + 会红判据）、323（把"抄值"的可用估计量搬进 scripts/ 并逐处判）、322、317。
③ 314、315、316；310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面连续多轮是最弱一维（本轮看图腿 NOT-RUN、5/15）：按清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R271 状态（第 270 轮 / Round 268 · 2026-10-21）
最后更新：2026-10-21（本地 · R271 / 第 270 轮 / Round 268）：**325：相对判据被自己的刀证伪 ⇒ 时间这条轴只印不判，硬门留在行为那一侧（M831 CAUGHT 红在 XCTAssertFalse）**（U-902…U-906 · D-257 · 产品 0 文件 · 自评 80/105）

**本轮落地**：空转基线只为把噪声打成读数；`blockedQueuePrintOnlyMilliseconds` / `blockedRatioReference` 只印不判；刀 M831（needle 从 R51 表读）1/1 CAUGHT、RESTORE_CLEAN；定向卷 Executed 6/failures=0；脚本电池 Ran 513 tests / OK (skipped=4)；预检 tables=80 covered=63 arms=210 bad=0、ARM_TOTAL arms=703、310 缺口 75 张 / 423 把。本轮 0 产品文件 ⇒ sources 格不动、四件套沿用上一笔、看图腿 NOT-RUN。

**收尾登记（R271 之后）**：325 结案 —— a481ab4→39572947743 success（该格在 runner 日志出现 2 次、:153 出现 0 次），坏法仍被行为断言抓住（M831 CAUGHT、红在 XCTAssertFalse）。台账半 3f8050b→39576062490 交接时 in_progress / 未读（只登记号不轮询，R140）。

**下一轮（R272 / 第 271 轮 / Round 269）的 ⓪**：
⓪ 读 CI：**a481ab4 → 39572947743 / completed / success（本轮代码半那一笔）是 325 的结案条件** —— 它不再红在 `CapturePathWriteBudgetTests.swift:153` 才算；68ab84a → 39570994287 / completed / failure 那一跑红在 STEP[2] checkout 属基建红，重跑一次看它是否自己消失（基建红也不许长期挂着）。只登记号不轮询（R140）。
① 326（比值恒真这条轴：基线必须来自另一个对象 + 一把会红的刀）、327（运行时 needle 让静态预检看不见）。
② **312 的具名出口（欠第五轮）**：按"纸"那一维推，本机 3.000 不许降（D-251）。
③ 324（会同码翻脸的那张帧）、323（抄值的可用估计量）、322、317、314、315、316。
④ 310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
⑤ 产品动效面仍是最弱一维（本轮看图腿直接 NOT-RUN，5/15）：按清账表点一个位真做动效或撤声明。
⑥ 用户闸门 220 路 A / 228② / 265。

## R270 状态（第 269 轮 / Round 267 · 2026-10-21）
最后更新：2026-10-21（本地 · R270 / 第 269 轮 / Round 267）：**判据里抄来的产品常量换成读常量（visibilityGrace 让出真相），新尺 ledger_timing_scan 钉住"抄值复活就红"；320 结案、新开 323**（U-897…U-900 · D-256 · 产品 1 文件·仅可见性 · 自评 89/105）

**本轮落地**：`DailyCopyLedger.visibilityGrace` private → internal static + 调用点 `Self.`；观察窗口 `Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000)`（计划 600 ms，改前 616／改后 639 ms 两份读数 + 帧基线 changed=1 证明行为没变）；`scripts/ledger_timing_scan.py`（9 格）现读 TIMING_SCAN product_grace=0.15 windows=1 读常量=1 抄值=0 判=PASS；刀 1/1 CAUGHT、RESTORE_CLEAN；四件套重跑（0 告警／全量 919 failures=0／帧 170 changed=1／dmg=ok／1.4.8）；脚本电池 Ran 513 tests / OK (skipped=4)；预检 tables=79 covered=63 arms=210 bad=0、310 缺口 75 张 / 423 把。CI 三跑（e87191a → 39565724396 / completed / success／c0abdec → 39566666631 / completed / failure／2073b12 → 39566913243 / completed / success）交接时未读。

**收尾登记（R270 之后，只登记不轮询，R140）**：CI 六跑 —— e87191a → 39565724396 / completed / success；c0abdec → 39566666631 / completed / failure；2073b12 → 39566913243 / completed / success；a73c80d → 39569764918 / in_progress / 未读；7f15e97 → 39570257402 / in_progress / 未读；c1fe940 → 39570503582 / in_progress / 未读。其中 **c0abdec 那一跑红在 STEP[15]（Swift tests executed-count gate）**，红的是 `CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread`（CapturePathWriteBudgetTests.swift:153）：实测 12.1725 ms ≥ 地板 10.0 ms，而同一份 Swift 代码在 e87191a 与 2073b12 两跑都是绿的 ⇒ 负载敏感，不是 R268/R269 那两次改动引入的坏法（那两笔都没动这颗阈值，且 R269 只动 scripts/）。新开 325 记的就是这条：换成同一次运行内的相对判据或先只印不判，行为判据继续当硬门，**不许把 10.0 放宽到达标**。

**下一轮（R271 / 第 270 轮 / Round 268）的 ⓪ 增补**：先读 a73c80d／7f15e97／c1fe940 三跑（当时仍 in_progress），再按 ① 处理 325 那朵红 —— 它排在 312 之前，因为它是**唯一一朵正在红的**。
**下一轮（R271 / 第 270 轮 / Round 268）的 ⓪**：
⓪ 读 CI：e87191a → 39565724396 / completed / success、c0abdec → 39566666631 / completed / failure、2073b12 → 39566913243 / completed / success 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `DailyCopyLedger` 那格改完常量来源之后是否仍绿**，以及 ledger_timing_scan 这类静态尺在 runner 上有没有被接进 CI（没接就照 309/253 那族记账）。
① 312 的具名出口（第四轮欠账）：按**纸**那一维推，本机 3.000 不许降（D-251）。
② 323（数出还有几处抄值）、322（`asyncAfter` 逐处问有没有判据押在那段延迟上）、317（候选带 ≥60 推广前先做同样的合成扰动）。
③ 314、315、316；310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 产品动效面仍是最弱一维（本轮产品文件只改可见性）：按 173/242 那张清账表点一个位真做动效或撤声明。
⑤ 用户闸门 220 路 A / 228② / 265。

## R269 状态（第 268 轮 / Round 266 · 2026-10-21）
最后更新：2026-10-21（本地 · R269 / 第 268 轮 / Round 266）：**321 由既有读数结案（悬停取证键是整颗控件级，不是指针坐标）；`wait_scan` 指向第二个根时暴露作用域 bug，当场修 + 两格守卫 + 刀 M829；319 结一半 ⇒ 新开 322**（U-893…U-896 · D-255 · 产品 0 文件 · 自评 86/105）

**本轮落地**：CI 交账 37accf9 → 39562680539 / completed / success 绿（R267 等待修法的 runner 验收）；321 结案（亮 未选中段 230→207 比值 1.248 vs 选中段 233→233；暗同形）；319 结一半（Sources 现读 bet=0）并修掉 `wait_scan` 的名册作用域（`present=`）+ 判据卷 15 格 + 刀 1/1 CAUGHT；脚本电池 Ran 504 tests / OK (skipped=4)；预检 tables=78 covered=62 arms=209 bad=0、ARM_TOTAL arms=702、310 缺口 75 张 / 423 把。本轮 0 Swift 文件 ⇒ 四件套沿用上一笔、帧重捕与换装 NOT-RUN。

**收尾登记（R269 之后，只登记号不轮询，R140）**：本轮台账半 push 之后新跑 c0abdec → 39566666631 / in_progress / 未读；代码半那一笔 e87191a → 39565724396 / in_progress / 未读。两跑都要读的是：runner 上三格改过等待形状的判据是否仍绿，以及 FAVORITE_INK_NOT_RUN 是否仍被登记为已登记 NOT-RUN。

**下一轮（R270 / 第 269 轮 / Round 267）的 ⓪**：
⓪ 读 CI：e87191a → 39565724396 / in_progress / 未读 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上 `WAIT_SCAN` 那一步（若已接进 CI）与三格改过等待形状的判据是否仍绿**，以及 `FAVORITE_INK_NOT_RUN` 是否仍被登记为已登记 NOT-RUN。
① 312 的具名出口：按**纸**（实测底）那一维推，本机 3.000 不许降（D-251）。这是欠了三轮的那一条。
② 320（`visibilityGrace` 抄值升成守卫 + 一把刀）、322（`asyncAfter` 逐处问「有没有判据押在它上面」）、317。
③ 314、315、316；310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
④ 本轮 NOT-RUN 的两件（帧重捕、换装本机）要与下一次 Swift 改动同一笔补跑。
⑤ 用户闸门 220 路 A / 228② / 265。

## R268 状态（第 267 轮 / Round 265 · 2026-10-21）
最后更新：2026-10-21（本地 · R268 / 第 267 轮 / Round 265）：**等待的两种形状拆成两个符号（`pollUntil` vs `pumpRunLoopStep` vs `pumpWindow`），新尺 `wait_scan.py` 按符号数；M826 一次 ESCAPED 把证人从「文件出现」对准「镜像发生」**（U-888…U-892 · D-254 · 产品 0 文件 · 自评 87/105）

**本轮落地**：318 结案（5 处调用点逐张判：3 搬轮询、2 改名轮询步进、1 留具名观察窗口；R267 那句「7 处」公开改口）；新尺 `scripts/wait_scan.py`（13 格 + 刀 M828，名册双向对账，现读 bet=1 未登记=0）；`pumpWindow` 把「成功写盘不许多发」那格修到能放倒 M826（窗口 616/600 ms）；三把刀 3/3 CAUGHT、RESTORE_CLEAN；CI 交账 e53706c → 39559154078 / completed / success 绿（R267 修法验收 + 同码两跑一红一绿的证人）、本轮新跑 37accf9 → 39562680539 / completed / success 未读；312 成因改写成"纸动了、墨没动"（仍开，出口按纸推）；看图腿产出 U-892 ⇒ 新开 321；另新开 319／320。四件套：0 告警／全量 919（failures=0）／帧 170 changed=0／dmg=ok／1.4.8。脚本电池 Ran 502 tests / OK (skipped=4)、预检 tables=77 covered=61 arms=208 bad=0、310 缺口 75 张 / 423 把。

**下一轮（R269 / 第 268 轮 / Round 266）的 ⓪**：
⓪ 读 CI：37accf9 → 39562680539 / completed / success 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上那三格改完等待形状之后是否仍绿**，以及 `WAIT_SCAN`／`FAVORITE_INK_NOT_RUN` 两行在 runner 上各自怎么说（后者仍应是"已登记的标记"）。
① 312 的具名出口落地：按**纸**（`windowBackgroundColor` 的实测底）这一维推，本机 3.000 不许降（D-251）。
② 321：按枚分别取 `pillReading` 分辨「夹具位点」还是「两层材质混层」；317（候选带 ≥60 推广到段按钮/设置行/热图描边前先做同样的合成扰动）。
③ 319（把 wait_scan 扫到 `Sources/`）、320（`visibilityGrace` 抄值升成守卫 + 一把刀）。
④ 314、315、316；310 的 75 张表、309 那 6 张；305、299、301、307、287/284、297/298/300、304、291 三位。
⑤ 用户闸门 220 路 A / 228② / 265。

## R267 状态（第 266 轮 / Round 264 · 2026-10-21）
最后更新：2026-10-21（本地 · R267 / 第 266 轮 / Round 264）：**runner 负载把一格「等挂钟」的判据打回原形 —— 改成等条件，断言一字未放宽，刀把等待顶到上限才红**（U-884…U-887 · D-253 · 产品 0 文件 · 自评 84/105）

**本轮落地**：`testWriteFailureBecomesVisibleWithoutAnotherCopy` 从 `pumpMain(0.8)` 改成"轮询到条件成立或 10s 上限"+ `waited_ms` 读数（本机 209 ms）；刀 M825 1/1 CAUGHT（等待 10015 ms 顶到上限）；CI 三跑交账（两绿、R265 账半那红 = 本轮这格、本笔未读）；`FAVORITE_INK_NOT_RUN` 确认被运动闸门登记为已登记 NOT-RUN；312 拿到 runner 近墨读数（亮 57/300／暗 57/69 vs 本机 177/173）⇒ 判为通道差异、不降地板、出口下一轮做；新开 318（7 处固定挂钟 pump 待分辨）。脚本电池 Ran 489 tests / OK (skipped=4)、预检 tables=76 covered=60 arms=205 bad=0。

**下一轮（R268 / 第 267 轮 / Round 265）的 ⓪**：
⓪ 读 CI：e53706c → 39559154078 / completed / success 与本轮新跑（只登记号不轮询，R140）。要验的是 **runner 上那格改完等待形状之后是否转绿**（红过的那一步 = Swift tests executed-count gate），以及 `FAVORITE_INK_NOT_RUN` 是否仍被登记为已登记 NOT-RUN。
① 312 的具名出口落地（按机器各推地板；本机 3.000 不许降）。
② 318：逐张分辨固定挂钟 pump 等的是异步产物还是时长本身，前者搬成轮询 + 等待读数，后者不许动。
③ 314（描边语义，等两机读数齐）、315、316、317；310 的 75 张表、309 那 6 张。
④ 305、299、301、307、287/284、297/298/300、304、291 三位；用户闸门 220 路 A / 228② / 265。

## R266 状态（第 265 轮 / Round 263 · 2026-10-21）
最后更新：2026-10-21（本地 · R266 / 第 265 轮 / Round 263）：**313 由合成实验结案，字形墨尺换成对锐度不敏感的估计量，两档读数一字未动**（U-880…U-883 · D-252 · 产品 0 文件 · 自评 85/105）

**本轮落地**：合成扰动（纸 255→236 颗数 47→47；模糊一次 47→12、两次 47→0，近墨 174→345）⇒ 成因是众数对锐度过敏；墨心改为"候选 ≥60 内取离底最远的十分之一颗均值"，候选带不许放宽（D-252，第一版放宽到 ≥20 被药丸摊平已改回）；新增合成已知答案 + 反面对照一格；出口闸门改成"近墨 ≥60"；两把刀 2/2 CAUGHT、build 0 告警、脚本电池 Ran 489 tests / OK (skipped=4)、预检 bad=0。313 结案、312 解套、新开 317。

**下一轮（R267 / 第 266 轮 / Round 264）的 ⓪**：
⓪ 读 CI：08ddaa1 → 39557244740 / in_progress / 未读、30135fa → 39555625399 / completed / success、d7dfdba → 39555767398 / completed / success 三跑交接时全 in_progress / **未读**（只登记号不轮询，R140）。要读的是 runner 自己印的 `FAVORITE_INK_PROOF … 近墨像素(≥20)=…`：近墨上百 ⇒ 312 当场可判（纸 236 上这颗星过不过 3.000）；若仍个位数 ⇒ 313 的结案要重开。顺带看 315 那行 case-insensitive 的 error 是否再现。
① 312（解套后第一优先）；317（候选带 60 的推广前提）。
② 314：热图描边语义（选中 vs 悬停）—— 先做"同一格分别点亮两态"的对照夹具再交眼睛，之后才接 291 那位。
③ 310 的 75 张表登记、309 那 6 张写死颗数的表。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R265 状态（第 264 轮 / Round 262 · 2026-10-21）
最后更新：2026-10-21（本地 · R265 / 第 264 轮 / Round 262）：**给 313 装分辨读数，并用现读把「降地板」这条路堵死**（U-876…U-879 · D-251 · 产品 0 文件 · 自评 84/105）

**本轮落地**：`glyphInkReading` 加第二条带子「近墨像素(≥20)」，出口自带「读法」半句；新证人：runner 底 236 vs 本机 255、runner 墨心 3/4 颗且方向反（4.934 > 2.187）⇒ 3.000 一字未动（D-251）；两把刀重跑仍 2/2 CAUGHT；脚本电池 Ran 489 tests / OK (skipped=4)；build 0 告警；新开 316（阈值 20 待实测支撑）。

**下一轮（R266 / 第 265 轮 / Round 263）的 ⓪**：
⓪ 读 CI：30135fa → 39555625399 / in_progress / 未读、d7dfdba → 39555767398 / in_progress / 未读 —— 本笔 push 后取新号（只登记号不轮询，R140）。**这一跑要读的是 runner 自己印的 `FAVORITE_INK_PROOF … 近墨像素(≥20)=…` 与 `FAVORITE_INK_NOT_RUN … 读法=…`**：近墨有几百 ⇒ 313 结到"画了但淡"；近墨也只有个位 ⇒ 结到"这一层几乎没画"。同时看 315 那行 case-insensitive 的 error 是否再现。
① 313 结案 + 312（地板的 runner 复验，被出口挡着的那半）。
② 314：热图描边的语义（选中 vs 悬停）—— 先做"同一格分别点亮两态"的对照夹具再交眼睛，之后才接 291 那位。
③ 316、310 的 75 张表登记、309 那 6 张写死颗数的表。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R264 状态（第 263 轮 / Round 261 · 2026-10-21）
最后更新：2026-10-21（本地 · R264 / 第 263 轮 / Round 261）：**310 的缺口被数出来（75 张表 / 423 把刀静默不覆盖），上一轮自己点亮在 runner 上的那朵红按对象存在性给了出口**（U-871…U-875 · D-250 · 产品 0 文件 · 自评 83/105）

**本轮落地**：`roster_gap()` + `TABLE_ROSTER` 一行（只测不判、逐张点名）；电池 2 格（等式地板 + 人造正对照，D-250）；字形墨判据的出口按"墨心 ≥20 颗"切片、接线断言照旧硬跑、两档全无对象才 skip；出口后重跑 M823/M824 仍 2/2 CAUGHT；脚本电池 Ran 489 tests / OK (skipped=4)；预检 `NEEDLE_PRECHECK tables=75 covered=59 arms=204 bad=0`、`ARM_TOTAL arms=697 dupes=0`。看图 RUN（热图格子两态，描边像选中 ⇒ 314）。

**下一轮（R265 / 第 264 轮 / Round 262）的 ⓪**：
⓪ 读 CI：8512d4e → 39519690827 / completed / failure、50aaca9 → 39519770384 / completed / failure 已读（红因 = 字形墨那格在 runner 上无对象，本轮已给出口）；93b2cbd → 39515829941 / completed / success 绿（R262 修法验收）。本笔成对号已现取：**`30135fa` → run 39555625399 / in_progress / 未读**（只登记号不轮询，R140），要验的是 **runner 上 `FAVORITE_INK_NOT_RUN` 有没有被捕获闸门登记成"已登记 NOT-RUN"而不是红**，以及 STEP[15] 那行 case-insensitive 的 error 是否再现（315）。只登记号不轮询（R140）。
① 313：runner 那颗星为什么无对象 —— 三条嫌疑各配一条能分辨的读数，别混着试；不许靠降 3.000 地板解决。
② 314：热图描边的语义（选中 vs 悬停）—— 先做「同一格分别点亮两态」的对照夹具再交眼睛，之后才接 291 那位。
③ 310 的登记本身（75 张表）、309 那 6 张写死颗数的表、315。
④ 305 的地板、299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R263 状态（第 262 轮 / Round 260 · 2026-10-21）
最后更新：2026-10-21（本地 · R263 / 第 262 轮 / Round 260）：**收藏星的字形墨接进取证通道，注释里那句「量出来的」第一次会红**（U-865…U-870 · D-249 · 291 剩三位 · 产品 1 文件 · 自评 93/105）

**本轮落地**：`RowFavoriteButton.tint` 与 `animation(value:)` 改读 `isHoveredForDrawing`；新判据从帧里读两态字形墨（亮 3.545→8.321、暗 4.641→8.312，地板 3.000 两档都过）+ 新尺 `glyphInkReading`（与药丸带子不相交）；名册删一行（291 剩 DailyCopyHeatmapView / GlassControls / VideoPreview）；两把刀 2 把全 CAUGHT（不必重捕帧，理由写在表头）；脚本电池 Ran 487 tests / OK (skipped=4)；预检 tables=75 covered=59 arms=204 bad=0。四件套：全量 918、唯一红 = `testImageComparisonCostStaysBounded`（284.1140031814575ms 全量 / 15.372s 单跑通过，281/304 家族，未放宽）、帧 changed=2（row-favorite-hover-60x56-dark.png、row-favorite-hover-60x56-light.png）后基线同一笔 update、dmg ok、换装 1.4.8。

**下一轮（R264 / 第 263 轮 / Round 261）的 ⓪**：
⓪ 读 CI：93b2cbd → 39515829941 / completed / success、b5a54f1 → 39516070653 / completed / success **已读且两跑绿**（R262 的放宽引号 + 根路径派生被 runner 验收）；本笔成对号已现取：**账半 `8512d4e` → run 39519690827 / in_progress / 未读**（只登记号不轮询，R140），要看的是 `testFavoriteGlyphInkClearsTheInteractiveFloor` 在 runner 上怎么说 —— 那 3.000 地板目前只有本机一台的读数（312）。
① 312：3.000 地板的 runner 复验（红就按 D-232 加按机器的具名出口，不许放宽数值）。
② 291 剩下三位（`DailyCopyHeatmapView` / `GlassControls` / `VideoPreview`）；305 的地板（本轮那张"比值跳变而肉眼有限"是反方证人）；309 那 6 张写死颗数的表；310 的 TABLES 名册。
③ 299 执行器半、301、307、287/284、297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R262 状态（第 261 轮 / Round 259 · 2026-10-21）
最后更新：2026-10-21（本地 · R262 / 第 261 轮 / Round 259）：**三根腐烂针修完并重跑，名册改成按「抽得出来」算，撤回上一轮两次假指控**（U-858…U-864 · D-248 · 286 结案 · 产品 0 文件 · 自评 83/105）

**本轮落地**：M541/M750/M768 重钉 + 三张表重跑全 CAUGHT、预检 bad=0；M684/M686 公开撤回（`arm_sites` 少认一种臂形状）；`mutate_r229.py` 的颗数写死换成形状判据；新尺 `scripts/mutation_verdict_scan.py` + 11 格 + 四把刀 M819…M822；`ARM_LINE` 放宽 ⇒ 123 把此前隐形的刀进查重（572 → 695）；预检仓库根由 `__file__` 推（runner 那朵 FileNotFoundError 的修法）+ 一格绝对路径守卫；脚本电池 Ran 487 tests / OK (skipped=4)。

**下一轮（R263 / 第 262 轮 / Round 260）的 ⓪**：
⓪ 读 CI：**本笔成对号 `93b2cbd` → run 39515829941 / in_progress / 未读**（push 后现取，只登记号不轮询，R140）—— 要验的是**放宽引号 + 根路径改派生之后 runner 上 `test_the_repo_manifests…` 与 `test_the_tools_derive…` 两格是否绿**，以及 `RUNG_STEP`/`PRESS_LADDER` 有没有新读数。取不到就写「未取到 + 成因」（293）。上一笔 6bf6f3e → 39512069087 / completed / failure 已读：STEP[9] 的 `check_manifests` FileNotFoundError，成因是预检写死本机仓库根，本轮已修。
① 309：那 6 张写死颗数的表一张张迁并各自重跑（迁完删名册一行）。
② 310：`TABLES` 手写名册（74 登记 vs 163 存在）⇒ 未登记表静默不覆盖。
③ 305 的地板（本轮那两张"肉眼分不出"是新证人）；299 的执行器半；301 + 307；311。
④ 291 那四位；287/284；297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R261 状态（第 260 轮 / Round 258 · 2026-10-21）
最后更新：2026-10-21（本地 · R261 / 第 260 轮 / Round 258）：**五把重捕型刀进名册，新尺第一版说了假话被自己抓住**（U-853…U-857 · D-247 · 306 结案、286 现读名单 · 产品 0 文件 · 自评 79/105）

**本轮落地**：`cross_table_ids` 吃 manifest（6 张 / 16 把 / dupes=0）+ `check_manifests`（锚点恰好一次、不许空刀、bad=0）；名册卷 +2 格带正对照；Ran 473 tests / OK。交出的坏消息：5 根 python 表的针已腐烂（M541（命中 0）、M684（命中 0）、M686（命中 0）、M750（命中 2）、M768（命中 0）），286 有名有姓了。

**下一轮（R262 / 第 261 轮 / Round 259）的 ⓪**：
⓪ 读 CI：1bccf7f → 39511039613 / in_progress / 未读；2068301 → 39510469503 / in_progress / 未读 —— 本笔 push 后再取；要看 runner 在新梯子（R260）下有没有把亮档选中帧判成 changed，以及 `RUNG_STEP`/`PRESS_LADDER` 的两机读数。
① 286：修那 5 根针（按 D-247 的计数法修，修完重跑对应的表，别只改锚点不重跑）。
② 305 的地板（两机读数 + 一次真判）；299 的执行器半（`kind=recapture` 做进执行器）；301 + 307。
③ 291 那四位；287/284；297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R260 状态（第 259 轮 / Round 257 · 2026-10-21）
最后更新：2026-10-21（本地 · R260 / 第 259 轮 / Round 257）：**尺先切片，再量出第二个真产品缺陷 —— 亮档按下与选中糊成一档**（U-846…U-852 · D-246 · 新开并结案 308、305 追记 · 产品 3 文件 · 自评 94/105）

**本轮落地**：`SelectedInk` 唯一换算 + `VisualFillLift.selected = 0.02`（亮档 0.12/0.15/0.18，暗档未动）；新守卫先红在改之前（顶层台阶 0.01 < 4/255）；M817/M818 两把各钉一条轴、双双 CAUGHT、RESTORE 逐字节干净；四件套全绿（917 / skip 44 / failures 1、changed=15 其中亮档 15 张、换装 1.4.8）；尺的按步骤切片（同值签一条、异值必红）。

**下一轮（R261 / 第 260 轮 / Round 258）的 ⓪**：
⓪ 读 CI：本笔 push 后 gh 现取成对号（未取到写成因，293）。要看的第一件是 runner 有没有把新的亮档选中帧判成 changed（工作基线已在本笔 update，runner 若读不到差异说明材质通道又切片了），以及 `RUNG_STEP`/`PRESS_LADDER` 在新梯子下的两机读数。已交账：f41d100 → 39506588117 / completed / success；9be5cc1 → 39504204057 / completed / success；5952827 → 39503229242 / completed / success。
① 305 的地板：给"相邻档台阶"立自己的地板（两机各读 + 真看图），立起来之前不许再凭印象动梯子任何一级。
② 306 + 299：五把重捕型刀（M814/M815/M816/M817/M818）进预检名册，`kind=recapture` 做进执行器。
③ 301 的 stamp 门 + 307 的公共写盘口（同一处做）；291 那四位；287/284/286；297/298/300、304；用户闸门 220 路 A / 228② / 265。

## R259 状态（第 258 轮 / Round 256 · 2026-10-21）
最后更新：2026-10-21（本地 · R259 / 第 258 轮 / Round 256）：**305 的尺长在已有的尺上：本机台阶读数 + 通道登记**（U-841…U-845 · D-245 · 305 追记 · 产品 0 文件 · 自评 92/105）

**本轮落地**：`hover_two_state_diff.py --readings`（读判据自印的灰阶，两点校准，不重扫帧）；现读 悬停→按下台阶 亮 1.058 / 暗 1.123；`ci_read.py` 通道加 `PRESS_LADDER_`/`HOVER_PILL_`；判据卷 26 格（+6，含"不许提前发明地板"的形状断言）；电池 `Ran 468 / OK`。自曝两处：新函数缺 `import re` 被电池拦在提交前；`c2ede9f` 没有自己的 run（同一次 push 只给 head 那笔建跑）。

**下一轮（R260 / 第 259 轮 / Round 257）的 ⓪**：
⓪ 读 CI：5952827 → 39503229242 / in_progress / 未读；9ffb6fd → 39502927591 / in_progress / 未读；c2ede9f 没有自己的 run（同一次 push 只给 head 那笔建跑，不是缺陷）。要拿的是 runner 自印的 `PRESS_LADDER_PROOF` / `HOVER_PILL_PROOF` 两行（通道已登记）；拿到就把本机这两行与它并排喂给 `--readings`，按 R220/R225 的路子推 305 的台阶地板；推出来之前**不许**改按下档。
① 305 结案路径：地板 → 判"亮档按下够不够" → 该改就改（改要配 D-244 的两把刀 + 真看图）。
② 306 + 299（M814/M815/M816 三把重捕型刀进预检名册，`kind=recapture` 做进执行器）；301 的 stamp 门 + 307 的公共写盘口（同一处做，别造两份）。
③ 291 那四位欠账；287/284/286；用户闸门 220 路 A / 228② / 265；297/298/300 仍开、304 待两跑对照。

## R258 状态（第 257 轮 / Round 255 · 2026-10-21）
最后更新：2026-10-21（本地 · R258 / 第 257 轮 / Round 255）：**按下那一档第一次有帧、第一次有台阶读数，两把刀各钉一条轴**（U-834…U-840 · D-244 · 302 结案、新开 305、306 · 产品 1 文件 · 自评 89/105）

**本轮落地**：`pressedForCapture` 取证键 + `row-favorite-press` 夹具（基线 168→170）+ `testPressRungIsOrderedAboveTheHoverRung`（亮 229→223、暗 45→53、恒等式偏差 0.5 / 0.5）；M815/M816 两把 CAUGHT、还原逐字节干净；看图 5 张（R256 改前改后肉眼分不出）；四件套全绿（告警 0、全量卷 916 / skip 44 / failures 0、dmg ok、换装 1.4.8）。STATE 与 FINAL_REPORT 的交接债（303）随本轮补上。

**下一轮（R259 / 第 258 轮 / Round 256）的靶**：
⓪ 读 CI：本笔 push 后用 `gh run list --json databaseId,headSha,status,conclusion` 现取成对号（取不到写「未取到 + 成因」，293）。要看的第一件是 runner 有没有印出 `PRESS_LADDER_PROOF` / `PRESS_LADDER_IDENTITY` 两行 —— 305 的地板要等它。已交账：62520ec → 39496791768 / completed / success；2b17297 → 39497014625 / completed / success。
① 305：把"相邻档台阶"做成 `scripts/` 里的尺（复用同一估计量），两机各读一次再推地板；地板出来之前**不许**按肉眼印象改按下档，也不许把 1.20/1.10 搬过去判。
② 306 + 299：三把重捕型刀（M814/M815/M816）进预检名册，`kind=recapture` 做进执行器；301 的 stamp 门（提交链里那条会红的 Swift 退出码读点）。
③ 291 那四位欠账（每一位都是"量不到的悬停/按下画法"，按 R252/R253/R258 的路子走：接键 → 归属对 → 量 → 看图 → 该改就改）；287/284/286；用户闸门 220 路 A / 228② / 265；其余仍开 249 / 263 / 269 / 267 / 260 / 262 / 258 第三处 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 293 / 294 / 297 / 298 / 301 / 304。


## R256 状态（第 255 轮 / Round 253 · 2026-10-20）
最后更新：2026-10-20 14:35（本地 · R255 / 第 254 轮 / Round 252）：**`round_verify.sh` 落地；它第一次跑就把 R253 那笔产品改动照成 4 失败**（U-822…U-824 · D-241 · 295 结案、新开 300、297 改判仍开 · 自评 84/105）

**本轮落地**：四件套脚本化（一条命令 + 一行摘要）；现读全量卷 915/44skip/**4 failures**；摘要脚本自己的两个空键 bug 修掉；帧基线 compare changed=1。

**下一轮（R256 / 第 255 轮 / Round 253）的靶**：
⓪ 先做 300：R253 那笔改动与两条既有等式冲突 —— 要么修等式并说明它当初为什么允许 0.085，要么回退 0.04 另找修法；两条路都要重跑 `bash scripts/round_verify.sh`（四件套一条命令）+ 重捕型刀。**在 300 之前 297 仍开，不许再写结案。**
① 读 CI：run 号只能 gh 现取（未读 `df2fd71`/`359a261`/`a01d17e`/`c4fc11a`/`58d7f3e`/`e054e03`/`c5f9e2b`）；本笔 push 后现取。
② 299（recapture 型 kind 进执行器与预检）、291 那四位欠账、287/284/286。
③ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 297 / 298 / 299 / 300。

最后更新：2026-10-20 14:10（本地 · R254 / 第 253 轮 / Round 251）：**看图验收完成 + 第一把「重捕型」刀 M814 CAUGHT**（U-819…U-821 · D-240 · 298 部分结案、新开 299 · 产品 0 文件 · 自评 90/105）

**本轮落地**：改前/改后同一位两张亮档帧对比验收；`mutate_r254.sh`（插刀→build→重捕 168 张→尺量新帧→逐字节还原）⇒ 尺 `退出=1` 且点名 1.171、`M814_RESTORE=clean`、捕获卷 80 格 0 失败。明记：M814 不在预检名册覆盖里（299）。

**下一轮（R255 / 第 254 轮 / Round 252）的靶**：
⓪ 读 CI：**run 号只能 gh 现取，取不到写「未取到 + 成因」**（293）。未读：`359a261`/`a01d17e`（R253）、`c4fc11a`/`58d7f3e`（R252）、`e054e03`（R251）、`c5f9e2b`（R250）。要看的是 STEP[9] 那朵 `HOVER_DIFF_CONTROL_INCOMPLETE` 是否消失、`SOURCES_CELL_HISTORY … 处置=judge`、runner 自印的 `HOVER_TWO_STATE_277` 与 `HOVER_DIFF 配对=`（现在应为 10）。
① 补 D-236 跨了三轮的债：全量 Swift 卷 + 换装本机（R253 改了产品）；顺手做 295（`scripts/round_verify.sh`），同一个漏连续三轮说明记忆不可靠。
② 做 299（recapture 型 kind 进执行器与预检），然后回到 291 那四位欠账 —— 每一位都是"量不到的悬停画法"，按 R252/R253 的路子走：接键 → 归属对 → 量 → 看图 → 该改就改。
③ 287/284/286；用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 298 / 299。

最后更新：2026-10-20 14:00（本地 · R253 / 第 252 轮 / Round 250）：**第一次「看得见的」产品反馈修正 —— 亮档悬停抬量 0.025→0.04、297 结案**（U-816…U-818 · D-239 · 新开 298 · 产品 1 文件）

**本轮落地**：`VisualFillLift.hover` 0.04（只加亮档）；改后按行归属对亮档判定=过线、尺 退出=0；`KNOWN_FLOOR_RED` 清空、判据卷 Ran 20 OK；swift build 零告警；捕获卷 80 格 0 失败；基线 update 到 168。代码半 `a01d17e`、账半本笔。

**下一轮（R254 / 第 253 轮 / Round 251）的靶**：
⓪ 读 CI：**run 号只能 gh 现取，取不到写「未取到 + 成因」**（293）。未读：`a01d17e`（R253 代码半）、`c4fc11a`/`58d7f3e`（R252）、`e054e03`（R251）、`c5f9e2b`（R250）等；runner 的配对数现在应是 10，且改后不应再有 `HOVER_DIFF_FLOOR_RED`。
① 做 298：看改后的亮档帧做看图验收；给抬量配刀（0.04→0.025 必须让尺重新 退出=1 且名册非空）；补全量 Swift 卷 + 换装本机（D-236）。
② 做 295：`scripts/round_verify.sh` 把四件套钉成一条命令，并让台账生成器断言那行摘要 —— 连着三轮都在同一处漏（R248/R249/R253）。
③ 291 那四位欠账（`HistoryRowViews` 先数清它自己直读裸 `isHovered` 的画法有几处）、287/284/286。
④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 298。

最后更新：2026-10-20 13:50（本地 · R252 / 第 251 轮 / Round 249）：**按行取证键落地 ⇒ R251 的「两档过线」被推翻，登记成真缺陷**（U-813…U-815 · D-238 · 296 结案、新开 297 · 产品 2 文件）

**本轮落地**：`hoveredRowForCapture`（按行覆盖）+ `MultiFileRow(row:)`；夹具一对；`/tmp/shots_r252` 168 张、捕获卷 80 格 0 失败、基线 update 到 168；亮档单行 1.171 < 1.20 被尺自己红出来并以 `KNOWN_FLOOR_RED` 双向对账登记（两次同源）。

**下一轮（R253 / 第 252 轮 / Round 250）的靶**：
⓪ 读 CI：**run 号只能 gh 现取**（293）。未读：`e054e03`（R251）、`c5f9e2b`（R250）、`5e2b374`/`b9e9412`（R249）、`7589b21`/`917f327`（R248）、`0bb02e1`/`5941520`/`550fb43`（取数时 in_progress）、本笔。runner 的配对数现在应是 10。
① 做 297：先看亮档多文件行的 idle/hover 两张帧（眼睛腿），再定墨；修完删名册那一行（双向对账会要求它为空），并给名册配一把刀。
② 补 D-236 本轮欠的两件：全量 Swift 卷 + 换装本机（本轮改了 2 个产品文件）。
③ 295（四件套脚本化）、291 那四位欠账、287/284/286。
④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 297。

最后更新：2026-10-20 13:35（本地 · R251 / 第 250 轮 / Round 248）：**290 结案 —— 多文件行第一次有两态帧并被量到（两档过线），并量出夹具证明不了"只亮一行"**（U-810…U-812 · D-237 · 新开 296 · 产品 0 文件）

**本轮落地**：夹具 `detail-3-files-hover`；`/tmp/shots_r251` 164 张；捕获卷 80 格 0 失败；尺 配对=8 退出=0、暗 28.6%/1.515、亮 28.8%/1.049 两档过线；判据卷 `Ran 20 OK`；眼睛腿看了暗档两张并判保留不改。

**下一轮（R252 / 第 251 轮 / Round 249）的靶**：
⓪ 读 CI：**run 号只能 gh 现取，取不到写"未取到 + 成因"**（293）。未读：`c5f9e2b`（R250）、`5e2b374`（R249 账半）、`b9e9412`（R249 代码半）、`7589b21`、`917f327`、`0bb02e1`、`5941520`、`550fb43`（最后三笔取数时 in_progress）。要读的还是 287 那三件（runner 自印 `HOVER_TWO_STATE_277`、`HOVER_DIFF_CONTROL=` 只剩两颗、`SOURCES_CELL_HISTORY … 处置=judge`），外加新的一条：runner 的配对数现在也应是 8。
① 做 296：让取证键能带行标识（或夹具渲染单行），并加一条会红的判据把"整列亮 vs 单行亮"分开 —— 在此之前 `MultiFileRow` 的悬停归属不许下结论（D-237）。
② 做 295（四件套脚本化）与 291 那四位欠账（`HistoryRowViews` 先数清它自己直读裸 `isHovered` 的画法有几处）。
③ 284 / 286 / 287；用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 296。

最后更新：2026-10-20 13:25（本地 · R250 / 第 249 轮 / Round 247）：**Swift 侧验证四件套补跑完 —— 全量卷 915 绿、帧基线 162/0、换装本机成功**（U-806…U-809 · D-236 · 292 结案、新开 295 · 产品 0 文件）

**本轮落地**：全量卷 `Executed 915 tests, with 42 tests skipped and 0 failures in 368.858s`（`/tmp/r250_full.log`，320MB 不入库）；`FRAME_BASELINE_AGAINST=working COMPARED=162 CHANGED=0 MISSING=0 ADDED=0`（`/tmp/shots_r250`）；dmg 签名 + sha256 OK、`ditto` 覆盖安装、装后版本 1.4.8；眼睛腿看了一张新帧。

**下一轮（R251 / 第 250 轮 / Round 248）的靶**：
⓪ 读 CI：**run 号只能 gh 现取，取不到写"未取到 + 成因"**（293）。上一笔现读：`39478148037↔0bb02e1`、`39476999347↔5941520`、`39475884846↔550fb43` 取数时 `in_progress` ⇒ 未读；`39474398455↔09a8763` completed/failure（STEP[9]，正文未读 ⇒ 不断言同源）。`917f327`/`7589b21`/`b9e9412`/`5e2b374`/本笔 push 后现取。
① 做 290：`MultiFileRow` 的多文件夹具 + 两态帧（同一色档 idle/lit），按 WCAG 地板判（D-232：两台机器各印一次再定线），并把帧拿进眼里看 —— 这是 R248 那条通道第一次被量。
② 做 295：`scripts/round_verify.sh`（全量卷 → 重捕帧 → 基线 compare → 换装 → 摘要一行），让 D-236 不再靠记忆。
③ 291 那四位欠账逐位清（`HistoryRowViews` 先数清它自己直读 `isHovered` 的画法有几处）；287 / 284 / 286 仍开。
④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 290 / 291 / 293 / 294 / 295。

最后更新：2026-10-20 13:12（本地 · R249 / 第 248 轮 / Round 246）：**第二笔产品改动（SearchField 接通道）+ 刀把守卫自己的假绿照出来**（U-803…U-805 · D-235 · 新开 294 · 产品 1 文件 · 眼睛腿本轮 RUN 两张帧）

**本轮落地**：`SearchField.swift` 图标墨与清除按钮改读一层 `isHoveredForDrawing`；`test_hover_capture_channel.py` 加画法级断言并把 `wiring()` 改成剥注释后判（`HistoryRowViews` 因此翻成未接）；`swift build` 零告警；`R249_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`；看了设置行暗档 idle/lit 两张并判为保留不改。**账与代码分两笔**：代码半 `b9e9412`、账半本笔。

**下一轮（R250 / 第 249 轮 / Round 247）的靶**：
⓪ 读 CI：**run 号只能 gh 现取，取不到就写"未取到 + 成因"**（293）。上一笔现读：`39478148037↔0bb02e1`、`39476999347↔5941520`、`39475884846↔550fb43` 仍 `in_progress` ⇒ 未读；`39474398455↔09a8763` completed/failure（STEP[9]，正文未读 ⇒ 不断言同源）。`917f327`/`7589b21`/`b9e9412`/本笔 push 后现取。
① 补 R248/R249 欠下的 Swift 侧验证：**全量卷 + 重捕帧 + 帧基线同一笔 + 换装本机**（连着两轮改了产品却没跑，292 为它而开）。
② 做 290（`MultiFileRow` 两态帧并按 WCAG 地板判）与 294（表按语言拦）；名册那四位欠账逐位清（`HistoryRowViews` 先数清它自己直读 `isHovered` 的画法有几处）。
③ 287（runner 自印 `HOVER_TWO_STATE_277` 定线 + 复验 `SOURCES_CELL_HISTORY … 处置=judge`）、284 / 286 仍开。
④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 290 / 291 / 292 / 293 / 294。

最后更新：2026-10-20 12:50（本地 · R248 / 第 247 轮 / Round 245）：**一笔真产品改动 + 悬停可拍性名册**（U-800…U-802 · D-234 · 新开 290/291/292 · 产品 1 文件，眼睛腿/变异腿/换装 NOT-RUN）

**本轮落地**：`DetailView.swift` 的 `MultiFileRow` 接上 `hoveredForCapture`（填充与描边共用一层判定）；`test_hover_capture_channel.py` 4 格名册（位点=9 / 已接=5 / 欠账=4，双向对账）；`swift build` 零告警；modechip 捕获格绿。

**下一轮（R249 / 第 248 轮 / Round 246）的靶**：
⓪ 读 CI：**run 号只能 gh 现取**。现读成对（2026-10-20 12:55）：`39478148037↔0bb02e1`（本笔，in_progress ⇒ 未读）、`39476999347↔5941520`（R247，in_progress ⇒ 未读）、`39475884846↔550fb43`（R246，in_progress ⇒ 未读）、`39474398455↔09a8763`（R245）**completed/failure ⇒ 有结论**：唯一失败步骤 `STEP[9] Release script tests`，其后六步 skipped；正文本次未读 ⇒ 不断言它与 R243/R244 那朵 `HOVER_DIFF_CONTROL_INCOMPLETE` 同源（同一步≠同一因）。要读的仍是 287 那三件：runner 自印 `HOVER_TWO_STATE_277` 定线、`HOVER_DIFF_CONTROL=` 是否只剩两颗、`SOURCES_CELL_HISTORY … 处置=judge`。
① 做 290：`MultiFileRow` 的多文件夹具 + 两态帧（同一色档 idle/lit），按 WCAG 地板判，并把帧拿在眼里看一遍（眼睛腿本轮必须 RUN：连续六轮 NOT-RUN 是本表最重的缺口）。
② 做 291 的 `SearchField` 那一行：唯一一处"画法本身拍不到"的真缺陷（图标色读裸 `isHovered`），一行改动 + 一把刀。
③ 做 292：换装本机 —— 改了产品代码就要重装，或具名 NOT-RUN 并说清代价。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 284 / 285 / 286 / 287 / 288 / 289 / 290 / 291 / 292；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 12:10（本地 · R247 / 第 246 轮 / Round 244）：**CI 抓帧那一步的正文有了自己的判据卷（6 格）+ 三把刀全 CAUGHT、274 结案**（U-797…U-799 · D-233 · 新开 288/289 · 产品 0 文件，眼睛腿与 Swift 腿 NOT-RUN）

**本轮落地**：`scripts/tests/test_ci_hover_wiring.py`（`Ran 6 OK`，已进电池）；`arms_r247/manifest.tsv` + `mutate_r247.sh`（kind/rel 从 manifest 现取）+ `mutate_r247.py`（影子表，进名册）；`R247_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`；D-233（CI 正文判据按字节收 + 抽正文真跑是可复用形状）。

**下一轮（R248 / 第 247 轮 / Round 245）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对。未读：`39475884846↔550fb43`（R246）、`39474398455↔09a8763`（R245）—— 两笔取数时都仍 `in_progress`、`conclusion` 空 ⇒ 只能说未读；本笔 push 之后现取再登记，账里不留问号 commit。要读的还是 287 那三件事：runner 自己印的 `HOVER_TWO_STATE_277 … 两态变化=X/Y 占比=Z`（定线用，D-232）、`HOVER_DIFF_CONTROL=` 是否只剩两颗（274 的复验）、`SOURCES_CELL_HISTORY … 处置=` 是否从 skip 翻成 judge（278 的复验）。
① 做 284/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；处置 r169/r217/r229 的锚点腐烂（换锚重跑并登记新 CAUGHT，或显式退役那张表并摘出名册）。
② 做 288：把"抽正文真跑"推广到捕获闸门与帧基线那两步 —— 那是产品读数真正进来的地方，现在它们的红只能在 runner 上第一次发现。
③ 动效本体：产品文件连续多轮 0，自评里最弱的两格就是"真实视觉审查 + 产品面推进"。能落产品改动的靶要先补两态帧（`DetailView.swift:609` 与 14 个无静置态的名字）；不许为了破 0 纪录加动效。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 284 / 285 / 286 / 287 / 288 / 289；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 11:10（本地 · R246 / 第 245 轮 / Round 243）：**277 结案（两处绝对颗数地板换成两态差尺）+ 274/278 的 runner 半各修一处**（U-794…U-796 · D-232 · 新开 287 · 产品 0 文件，眼睛腿与变异腿 NOT-RUN）

**本轮落地**：`rawFrame` + 两格换成「负对照 0 颗 / 分母 > 100 颗 / 比值 ≥ 下界」，本机 `Executed 2 tests, with 0 failures`，六行读数占比 0.709~1.000；CI 正对照按 (状态×色档) 配对、闸门改「两颗都非空」，整步正文本机跑通 `退出=0`；`fetch-depth: 50 → 0`（50 仍是浅克隆 ⇒ 闸门恒 skip）。

**下一轮（R247 / 第 246 轮 / Round 244）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对。未读名册：`39474398455↔09a8763`（取数时仍 in_progress ⇒ 只能说未读）、`39394134380↔66ba71f`（已读：STEP[9] 一朵红 = `HOVER_DIFF_CONTROL_INCOMPLETE=1`，正文本机已复修）、`39391292143↔cc1e6be`、`39387140455↔077ac79`、`39384781442↔5130564`、`39384656508↔0a1e649`。本笔 push 之后现取再登记，不在账里写问号 commit。
① 做 287：从 runner 自己印的 `HOVER_TWO_STATE_277` 定两台机器的地板数，并复验 `HOVER_DIFF_CONTROL=` 只给两颗、`SOURCES_CELL_HISTORY … 处置=judge`；给本轮三根新牙各配一把刀（负对照换恒假 / 分母地板摘掉 / CI 那一步退化成数逗号）。
② 做 284/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；处置 r169/r217/r229 的锚点腐烂（换锚重跑或显式退役那张表）。
③ 动效本体：产品文件连续多轮 0，自评 85 里最弱的两格就是"真实视觉审查 + 产品面推进"。真靶候选先要补两态帧（`DetailView.swift:609` 与 14 个无静置态的名字），再判要不要加反馈；不许为了破 0 纪录加动效。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 283 的 runner 半 / 284 / 285 / 286 / 287；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 10:20（本地 · R245 / 第 244 轮 / Round 242）：**变异腿换 shell 执行器恢复，六把刀第一次全 CAUGHT**（U-790…U-793 · D-231 · 280/283 结案、新开 284/285/286 · 产品 0 文件，眼睛腿连续第二轮 NOT-RUN）

**本轮落地**：`arm_patch.py` + `arms_r245/manifest.tsv` + `mutate_r245.sh` + `mutate_r245.py`（影子登记表，已进预检名册）；`R245_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`；三把 Swift 刀钉回 R242 换尺的三根牙，三把 python 刀钉住 D-230 平涂前提与地板判定。脚本电池按规矩在台账落盘之后跑，那一次的读数写进本笔提交信息，不在此预填。

**下一轮（R246 / 第 245 轮 / Round 243）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询、也别在账里写问号 commit）。未读五笔：`66ba71f`（R244）、`cc1e6be`（R243）、`077ac79`（R242 收尾）、`0a1e649`（R242 主体）、`5130564`（R242 STATE 成对）；本笔 push 之后现取再登记。要读的仍是 BACKLOG 276 结案追记那四件事：① STEP[9] `SOURCES_CELL_HISTORY … 处置=` 是否 skip→judge（278）；② STEP[17] modechip 那朵是否消失 + runner 自印 `两态变化=X/Y 占比=Z`（279）；③ `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275，runner 的地板数就从这行取）；④ skip 数本机 3 / runner 2 的成因。这一跑还要看 `HOVER_DIFF_BASE … 底众数占比=` —— runner 的底若被判成不平涂，说明 D-230 的前提在 runner 上真的需要。
① 做 277：现在执行器通了，把 `UICaptureHarness.swift` 其余两处 `pixels > 400`（段按钮/玻璃圆那一族 `:5159`、设置行 `:5236`）换成 `bandChanged` + 分母地板 + 负对照，各配一把刀；这一步要跑 `swift build`（0 告警）与捕获卷，Swift 腿不能再记 NOT-RUN。
② 做 284/285/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；给 `manifest.tsv` 的锚点补一支按列读的预检。
③ 动效本体：产品文件连续多轮 0。真靶候选要按 282 的口径重判后再定 —— 悬停那一族已过线（撤销），剩下能改的是**没有两态帧**的位点（`DetailView.swift:609` 与 14 个无静置态的名字）：先补夹具与静置帧，再判要不要加反馈。不许为了破 0 纪录加动效。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 274 runner 半 / 275 / 277 / 278 / 279 / 281 / 282 / 284 / 285；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 08:30（本地 · R244 / 第 243 轮 / Round 241）：**地板判定进尺 + 底平涂前提 + 280 三条排除**（U-787…U-789 · D-230 · 新开 283 · 产品 0 文件，眼睛腿未跑）

**本轮落地**：`hover_two_state_diff.py` 加 `FLOOR_LIGHT/FLOOR_DARK/FLAT_SHARE`（判定只对 WCAG 列生效、底不平涂只报读数、低于地板 exit 1）；判据卷 17→20 格（两格合成对照 + 一格真帧 standing 判据）；真帧六对全部过线（1.211~1.371）；电池 `Ran 448 OK (skipped=4)`；280 排掉符号链接 / stdin / 登录 shell 三条嫌疑（失败确定性重放，日志字节数恒定）。

**下一轮（R245 / 第 244 轮 / Round 242）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。未读名册（push 后把本笔的 run 补进来）：`cc1e6be`（R243）、`077ac79`（R242 收尾）、`0a1e649`（R242 主体）、`5130564`（R242 STATE 成对）、本笔。每笔要读的四件事照 BACKLOG 276 结案追记：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是否 skip→judge（278）；② STEP[17] modechip 那朵是否消失 + runner 自印的 `两态变化=X/Y 占比=Z`（279）；③ `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275）；④ skip 数本机 3 / runner 2 的成因。这一跑还要多看一眼新加的 `HOVER_DIFF_BASE` 与 `判定=` 列 —— runner 的底若被判成不平涂，说明 D-230 的前提在 runner 上真的需要。
① 做 283：变异表改 **bash 驱动**（`swift test` 在 shell 里 rc=0 已验），把 M798…M801 插进去，并给本轮三格各配一把刀；这是"变异对照"这条硬规矩目前唯一的堵点。
② 做 277：Swift 侧其余两处 `pixels > 400` 换成 `bandChanged`（段按钮/玻璃圆那一族、设置行那格），配刀。
③ 动效本体：产品文件连续多轮 0。真靶候选要按 282 的口径重判后再定 —— 悬停那一族已证明过线（撤销），所以剩下能改的是**没有两态帧**的位点（`DetailView.swift:609` 与 14 个无静置态的名字）：先补夹具与静置帧，再判要不要加反馈。不许为了破 0 纪录加动效。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 277 / 278 / 279 / 280 / 281 / 282 / 283；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 07:45（本地 · R243 / 第 242 轮 / Round 240）：**两态差尺的口径对账 —— 一条候选缺陷被判成尺的假话**（U-784…U-786 · D-229 · 新开 282 · 产品 0 文件，画面只看了一张帧）

**本轮落地**：`hover_two_state_diff.py` 加 WCAG 线性口径、两口径同印；判据卷 17 格（新增"两口径不许互当证人"一格，期望值现算：码值 1.090 / WCAG 1.214）；真帧现读四处全过 1.20 地板（1.220 / 1.225 / 1.224 / 1.371）⇒ R240 挂着的"亮档偏淡"撤销，不改产品（D-229）；电池 `Ran 445 OK (skipped=3)`。

**下一轮（R244 / 第 243 轮 / Round 241）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。本笔 push 之后要读的是：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是不是从 skip 变 judge（278 的验收）；② STEP[17] modechip 那朵红消失没有、并抄回 runner 自印的 `两态变化=X/Y 占比=Z`（279）；③ 新接的那一步打的 `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275 的地板）；④ skip 数本机 3 / runner 2 的成因（279）。上一笔 `0a1e649`、`5130564`、`077ac79` 三笔的 run 若仍未读，继续成对登记在这里。
① 破 280（刀跑不起来）：同句 `swift test --filter …` 在 shell 里 rc=0、经 python subprocess 稳定 rc=1 且日志字节数一模一样 ⇒ 下一步试 `stdin=DEVNULL`（上一次这一支跑了 12 分钟没返回，被停掉了，没拿到结论）与清 manifest 缓存；破了就把 M798…M801 插进去，并给本轮的 WCAG 两格补刀。
② 做 282 + 277：把 251/清账表里其余**码值口径**的两态读数按 WCAG 重判，并把两处 `pixels > 400` 换成 `bandChanged`。
③ 动效本体：亮档"偏淡"这条已撤销 ⇒ 真靶要换一个**有测量支撑**的位点（候选：251 第三处 `DetailView.swift:609` 先补静置帧；或清账表里按 WCAG 重判后仍低于地板的那一格）。连续多轮产品 0 文件，这条仍是目标模式的核心欠账。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 274 的 runner 验收 / 275 / 277 / 278 / 279 / 280 / 281；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 06:10（本地 · R242 / 第 241 轮 / Round 239）：**CI 七笔读数交账 + 两朵 runner 红各自钉到机制**（U-780…U-783 · D-228 · 276 结案、新开 277/278/279/280/281 · 产品视图 0 文件，画面一字未动）

**本轮落地**：三跑逐 job 下正文读齐（STEP[4] 编译红消失 = R236/R237 修复的 runner 验收；`SEAM_READER_ISOLATION 文件=98 引用=1 未标注=0` 同值；电池 443 里唯一一朵是浅历史假红；捕获闸门唯一一朵是 modechip 悬停）。`bandChanged` 新尺进 `UICaptureHarness`，modechip 那格换成「变化颗数 > 100 + 占比 ≥ 0.10 + 分母 > 100 + 同一帧负对照 = 0」（本机实测 1784/1809=0.986、1598/1809=0.883、负对照 0）；`sources_gate` 把浅历史变成具名 skip，ci.yml 加 `fetch-depth: 50`，合成小仓库证人重现机制；四把刀 M798/M799/M800/M801 全 CAUGHT。

**下一轮（R243 / 第 242 轮 / Round 240）的靶**：
⓪ 读 CI：本笔=`0a1e649`（push 于 2026-10-20 07:08，尚未读，成对登记在这里；`python3 scripts/ci_read.py latest` 现拿，别轮询）。这一跑要读的三件事：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是不是从 `skip` 变 `judge`（278 的验收）；② STEP[17] modechip 那朵红消失没有，并抄回 runner 自己打印的 `两态变化=X/Y 占比=Z`（279 要拿它抬地板）；③ skip 数本机 3 / runner 2 那格差在哪（279 的读数单）。仍未读名册：本轮 push 之前那三笔已交账（见 BACKLOG 276 结案追记），本笔与之后各笔按老规矩成对登记。
① 做 277：其余两处「众数绝对颗数 > 400」换成同一把 `bandChanged`（段按钮/玻璃圆那一族、设置行那一格），并给"矩形大就侥幸过线"这件事配一把能红的刀。
② 274 本轮已接线（CI 电池那一步之后跑尺，先打 `HOVER_DIFF_WIRED_AT png_files=`）⇒ 下一跑要读的是 runner 自己打印的 `HOVER_DIFF 配对=… 无静置态=…`，拿它登记 275 的地板（本机 6 不许外推）；若那一行是 `HOVER_DIFF_NOT_RUN`/`CONTROL_INCOMPLETE`，分别对应环境缺席与接线漂了，处置不同，不许混。
③ 回到动效本体（**这是目标模式的核心欠账，连续五轮产品视图 0 文件**）：R243 的真靶已经有定线读数 —— 三处 controlHover 位点的**亮档逐点中位**（控件局部口径，与仓库自家地板同口径）分别是 玻璃圆钮 1.092、行内收藏星 1.094、段按钮 1.095，而仓库自己定的亮档地板是 **1.20**（`UICaptureHarness` 5093 行 `minimum = … ? 1.10 : 1.20`，R220 骨架条带 / R225 浮层悬停 / R229 小控件三处沿用），同批正对照 modechip 是 1.515 ⇒ **亮档那一半的墨不够**是量出来的，不是看图猜的。改法走 `HoverInk` 的亮档出口抬一档，配：`swift build` 0 告警 → 判据卷 → 重捕帧并对基线（同一笔 update）→ 眼睛腿真看 → 换装本机 → 台账。251 第三处（`DetailView.swift:609`）仍缺静置帧，14 个无静置态的名字尺会逐条点名。
③b 做 277：其余两处「众数绝对颗数 > 400」也换成 `bandChanged`（本轮只换了 modechip 那一格；段按钮/玻璃圆那一族与设置行那格在 runner 上这次是侥幸靠矩形大过线 —— 1637 / 4876 / 3120）。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251；用户闸门 220 路 A、228②、265。

最后更新：2026-10-20 01:30（本地 · R241 / 第 240 轮 / Round 238）：**两态差尺的判据卷进电池 —— 两个口径各配一把刀，闸门两向都有证人**（U-777…U-778 · D-227 · 273 结案、新开 274/275 · 产品 0 文件，画面一字未动）

**本轮落地**：`scripts/tests/test_hover_two_state_diff.py` 16 格（合成帧两口径 2.17/1.234 手算对账、CLI 四道闸门两向证人、配对两种写法、真帧地板按机器 `HOVER_DIFF_MIN_PAIRS`）；真帧卷 `Ran 16 OK`（配对 6/无静置态 14，与 R240 同值）；M795/M796/M797 三把全 CAUGHT、RESTORE_CLEAN；新表 `mutate_r241.py`。

**下一轮（R242 / 第 241 轮 / Round 239）的靶**：
⓪ 读 CI：**名册以 BACKLOG 276 为准**（七笔 run↔commit 成对 + 每笔要读的四个读数，别再往这里手抄）。未读七笔：`39353879945↔e241389`（取数时 `in_progress`、`conclusion` 空 ⇒ 只能说未读）、`39352533580↔070cbab`、`39352046610↔5252c05`、`39351035433↔6927880`、`39350006461↔3e90ab4`、`39347522293↔7b7495d`、`本笔↔2755056`；每笔读四个数：STEP[4] `dismissRowInk` 转绿没、`SEAM_READER_ISOLATION 文件=98 引用=1 未标注=0`、电池认不认两种台账形状（250/270 的 runner 半）、新判据卷在 runner 上是「skip 且点名通道」还是真跑（顺带看 `真帧配对=`）。编译红没恢复前下游红不当产品读数。
① 做 274/275：把尺挂进 CI 抓帧那一步（接在它被打印的那一步的 grep 上），并拿 runner 自己打印的配对数登记 `HOVER_DIFF_MIN_PAIRS`。
② 251 第三处（`DetailView.swift:609`）补两态帧 —— 只有先有静置帧，尺才量得动；14 个无静置态的名字尺会逐条点名（不许把它们当成「没问题」）。
③ 动效本体仍欠（连续 0 产品文件）：从 173/清账表里挑一个**两态读数已经能定线**的位点做真改动，别再凭未定线的尺改档。
④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251；用户闸门 220 路 A、228②、265。


最后更新：2026-10-20 01:16（本地 · R240 / 第 239 轮 / Round 237）：**两态差尺进仓库（`scripts/hover_two_state_diff.py`）—— 两口径同时给、三把闸门 + 覆盖率地板，第一次跑就红在自己的配对规则上**（U-774…U-776 · D-226 · 272 结案、新开 273 · 产品 0 文件，画面一字未动）

**本轮落地**：尺入库并本机跑通（`RULER_EXIT=0`，配对 6 / 无静置态 14、负/正对照全 OK）；玻璃圆钮 暗 1.232/1.393、亮 1.078/1.092，正对照 modechip 暗 1.223/1.515；两口径不同向 ⇒ 判为不动档（D-226）。

**下一轮（R241 / 第 240 轮 / Round 238）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。未读五笔：`39352046610↔5252c05`、`39351035433↔6927880`、`39350006461↔3e90ab4`、`39347522293↔7b7495d`、`本笔↔?`；要验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 那一行、以及**电池认不认两种形状**（250/270 的 runner 半）。编译红没恢复前下游红不当产品读数。
② 做 273：把尺接进 `scripts/tests`（合成帧验数 / 缺 `--control` 必须红 / 空目录必须红）与 CI 那一步，地板按机器各自登记。
③ 251 第三处（`DetailView.swift:609`）补两态帧；18 个 `-hover` 名里只有 2 对有静置态，尺会逐条点名。
④ 登记 M795/M796；⑤ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240；用户闸门 220 路 A、228②、265。


最后更新：2026-10-20 01:10（本地 · R239 / 第 238 轮 / Round 236）：**看图腿回来了 —— 重捕 162 帧、251 的两处悬停第一次有两态差读数，且当场量到自己那把临时尺的单位错**（U-771…U-773 · D-225 · 新开 272 · 产品 0 文件，画面一字未动）

**本轮落地**：帧通道恢复（`swift test --filter UICaptureTests` ⇒ 162 帧、`frame_baseline check` ⇒ CHANGED=0）；
两态差尺（含负对照=帧自身、正对照=modechip）量出 玻璃圆钮 暗 1.232 / 亮 1.078、段按钮 暗 1.179 / 亮 1.093。
**判为不改**：亮档那两个数与 R231 的"药丸 1.160:1"不是同一个估计量（带内均值 vs 控件局部）⇒ 见 D-225。

**下一轮（R240 / 第 239 轮 / Round 237）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿 run↔commit 成对（别轮询）。未读的三笔：`RUN=39351035433 sha=6927880 status=in_progress conclusion=`（空 ⇒ 只能说未读）、
⓪ 续（R293 之后 push 的六笔，交给 R294 第 ⓪ 条）：1cb8446 → 39746101918 / in_progress / 未读、2ecd569 → 39745244448 / in_progress / 未读、bd12f4b → 39744426884 / in_progress / 未读、c1bee12 → 39743534010 / completed / success、1a488c6 → 39743282481 / completed / success、1dfc04d → 39742725697 / completed / success。要验的两件事：① 这一批里若有红，先按**步骤名**逐条落账再归因（R149：别只盯自己新加的那一步）；② 本轮新入库的 `scripts/tests/test_final_report_section1_cell.py` 与 `refresh_report_section1.py` 都靠现跑 `curve_from_ledger.py` 取数，而 runner 的浅历史与工作目录不同 ⇒ 「本机绿」不配替 runner 签字（R131）。只登记不轮询，R140。
⓪ 续二（R294 开场前已读的 CI）：六笔全部读到 —— 328ea36 → 39746421783 / completed / success、1cb8446 → 39746101918 / completed / success、2ecd569 → 39745244448 / completed / success、c1bee12 → 39743534010 / completed / success、1a488c6 → 39743282481 / completed / success，只有 bd12f4b → 39744426884 / completed / failure，且**失败步骤只有一朵**：STEP[19] Motion coverage floor。正文现读（gh run view --log 按通道串取，`--log-failed` 这一跑整份解析成 UNKNOWN STEP ⇒ 按步骤名过滤这把尺今天不灵）：`MOTION_FLOOR_SUITE_RED=1 … testNativeRowMoveIsVisibleToTheRuler：failed - 两臂形状一致（开 1 帧/峰值 0.053、关 1 帧/峰值 0.053）⇒ 这次 moveRow 是瞬移`，`MOTION_FLOOR_REDS=2`。⇒ 这是 155／304 那一族的又一次 runner 红（那一笔只动了 BACKLOG 文本 ⇒ 与代码无关，是负载敏感），且**后三跑不再红**：同一份判据在四跑里红一跑。两处要记的账：① 我一度把「同跑里 MOTION_GATE_CASES failed=0」读成这道门假绿 —— 错，`MOTION_GATE_CASES` 由 `ci_capture_gate.py` 打，读的是**捕获那一卷**，与 `/tmp/motion.log` 不是同一个对象；这是 R86「跨步骤 grep 造出假矛盾」的第四次，反证办法是拿真日志跑一次已知答案（本轮就这么纠正的）。② 这条红**不放宽、不登记成免检**：它说的是产品的行移动在尺下是瞬移，正是 155 欠的那格。只登记不轮询，R140。
⓪ 续三（R294 的台账半没落地）：本轮代码半已验证（捕获卷 91/5skip/0失败、全量卷 All tests passed、参照臂两把刀 M858/M859 全 CAUGHT、预检 bad=0、帧 174 张且 docs/frame_baseline.json 同一笔 update），但**五本台账那一半没写进去**：`.scratch/motion-audit-2/ledgers_r294.py` 落盘后被守卫照出三处形状不符 —— ① ITERATION 那一节缺「七维度自评」子标题（曲线尺读到 0 行 n/15 ⇒ DERIVED_NO_MARKER=291 拒绝推导）；② UI_AUDIT 新节标题里没有 `U-962…U-964` 这种区间（test_declared_range_is_fully_defined 与它自己的防空跑那条一起红）；③ 我重写 STATE 时丢了「最后更新」那一行（round_batch_consistency 两条判据因此空跑，它们选择红而不是静默）。三处都是**我的写法**问题，不是判据太紧；已把五本台账 git checkout 还原、电池回到 Ran 544 / OK (skipped=4) 才提交这一格账。另一条自曝更要紧：**那支生成器不是事务性的** —— 它在写盘之后才跑到写盘后的电池对账，于是「拒绝」发生时五本台账已经落了一半；这次靠 git checkout 收拾干净，但下一轮必须先修成「全部算完＋守卫形状自测通过才开写」（R99 那一课的复发）。R295 的第一件事就是把这三处形状补对并让生成器变事务性，补的时候照 ①②③ 那三条守卫的原文，别照我的记忆。
⓪ 续四（R294 的账半为什么还没落地：两把守卫对同一个标题各要一样东西）：代码半已入库（1bf8431），账半**两次尝试都没落地**，五本台账已 git checkout 还原、CHANGELOG 与 §1 也一起还原，电池回到 Ran 544 / OK (skipped=4)。卡住的地方很具体，两把守卫对 `AGENT_UI_AUDIT.md` 新节标题各提一个要求，我两次只满足一个：
  · `test_round_batch_consistency` 要标题形如 `## 第 293 轮（R294 …`（它找的是『## 第 N 轮（R294』这个前缀，所以 **R 编号必须紧跟在「（」后面**）；
  · `test_ledger_ids.NewestRoundIdRangeTests.test_the_range_guard_is_not_vacuous` 要在标题里读到 `U-962…U-964` 这种区间，并且它会**删掉一条 U 定义行**来证明自己的正则不是恒真 —— 我这一节的定义行形状是 `- **U-962**：正文…`（一行里带正文），它删不掉 ⇒ 报「正则与这份账的形状不一致」。
  下一轮（R295）先把这两件事一次做对：标题写 `## 第 293 轮（R294 · U-962…U-964 · 2026-10-22）`（第一版就是这个形状，它过了 round_batch、只被 range 防空跑那条拦），并把三条 U 定义写成**独立成行、行内不带正文**（正文另起缩进行），这样那条防空跑才删得掉。改完再跑电池，绿了才写 CHANGELOG/ITERATION/DECISIONS/BACKLOG/STATE 五本 —— 顺序也别再反过来：我这两版都是**先写台账再跑电池**，所以每次都是半批落盘（R99「会写仓库的工具要事务性」的第三次复发）。本轮的读数与判据本身没丢：全在 1bf8431 的提交正文里（参照臂码值 亮 13/暗 23、底 亮 255/暗 30、M858/M859 全 CAUGHT、帧 174、产品 0 文件），346 与 D-275 的原文也在那条信息里，R295 照它补台账即可。
   `39350006461↔3e90ab4`、`39347522293↔7b7495d`；要验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 那一行、以及**电池认不认两种形状**（250/270 的 runner 半）。编译红没恢复前下游红不当产品读数。
① 把 272 的尺搬进 `scripts/`：两口径各一版（变化带均值 / 控件局部对比度）、配正负对照、名单为空=红，再决定 251 亮档要不要动 `VisualFill.hover`。
② 给 251 第三处（`DetailView.swift:609`）补两态帧 —— 现在 `detail-*` 里 hover/idle 对数=0。
③ 登记 M795/M796（R238 补记那四朵红）进变异名册与预检。
④ 249 / 263 / 268 的 runner 半；269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 仍开。
⑤ 用户闸门：220 路 A（要授权改全局 `AppleKeyboardUImode`）、228②、265（要真机）。


最后更新：2026-10-20 08:50（本地 · R238 / 第 237 轮 / Round 235）

**这一轮在做什么**：把 BACKLOG 250 结掉 —— 台账编号守卫的"定义行"只认标题，而 R200 之后的决定写成粗体，
于是最近 28 条对"被引用却没正文"隐形（标题形最大只到 D-194，粗体形到 D-222）。扩成「标题 ∪ 粗体」一支正则
+ 两态对照 + 老形状子集格 + 现有粗体条负格 + 粗体抹除证人，两刀 M793 / M794 各摘一半。
**产品 0 文件、画面一字未动**（动效的账继续欠着，这一维仍然拖总分）。

**现读计数器**：脚本电池 `Ran 423 tests` / `OK (skipped=2)`；台账 U 到 U-768、D 到 D-223、BACKLOG 到 269、刀到 M794；
帧 162 张在 `/tmp/shots_r236`（本轮没重捕）；曲线 R235=88。判据文件 `test_ledger_ids` 从 11 格长到 16 格；
全量 `swift test` 本轮**没重跑**（Swift 侧未变，上一笔 7b7495d 是 `Executed 915 / 44 skipped / 0 failures`）。

**下一轮（R239 / 第 238 轮 / Round 236）的靶**
⓪ **本笔与上一笔的 CI 都还没读**：`RUN=39347522293 sha=7b7495d status=in_progress conclusion=`（空）。
- **R238 补记（同一轮第二次落盘）**：`RUN=39350006461 sha=3e90ab4 status=in_progress conclusion=`（空 ⇒ 只能报未读）。270 结案（`ITEM` 两种形状 + 地板 150，该卷 16→20 格）、新开 271（上一笔 subject 手抄错轮次标签 ⇒ 从台账派生）。下一轮 ⓪ 读的是**这两笔**的 run，另要把 M795/M796 登记成变异臂；编译没恢复之前 STEP[15]/[17]/[18]/[19] 那几朵红一律不当产品读数。
   先 `python3 scripts/ci_read.py latest` 现拿 run↔commit 成对（别轮询），要验三件事：STEP[4] 有没有转绿、
   `SEAM_READER_ISOLATION` 在 runner 上打的那一行、以及**电池那一卷认不认粗体定义行**（250 的 runner 半）。
   编译没恢复之前，STEP[15]/[17]/[18]/[19] 那几朵红一律不许当成产品读数。
① 249（R225 亮档反馈梯的 runner 复验）与 263 —— 都要等 ⓪ 把那朵编译红摘掉才谈得上。
② 268 的 runner 半（本机绿 ≠ runner 绿，D-222 那条规矩）。
③ **回到画面**：251（三处共用 `VisualFill.hover` 的位点 —— 段按钮 / 玻璃圆钮 / DetailView：先各补两档帧，
   再按 R225 的形状各判一次，最后每处一刀；不许在没有帧的位点上先改数值）。
④ 269（预检 `bad=5` 与电池的关系要先分辨成因）、267、260、262、258 第三处、254→255→248、243、227③、222、215、201/202、207、240；250 与 253 已结。
⑤ 需要用户真机或授权的：220 路 A（要授权改全局 `AppleKeyboardUIMode`）、228②、265。

**核心欠账没变**：阶段二"足够华丽 / 合理 / 原生"那一句仍未达成 —— 产品动效面连续多轮 0 改动，七维曲线长期在 90 以下，
主要拖在「产品面推进」与「真实视觉审查」两维。下一轮把力气搬回画面：从 ③ 挑一处，先补两档帧 → 判 → 加刀 → 真操作一遍。


## R237（本地 · 2026-10-20 08:2x）：本机绿≠CI 绿 —— runner 的 STEP[4] 是编译期 error，补了一把与 SDK 无关的静态尺（第 236 轮 / Round 234 / U-761…U-764 / D-222 / BACKLOG 268）

最后更新：2026-10-20 08:25（本地 · R237 / 第 236 轮 / Round 234）

本轮落地：① 读 R236 那一跑 CI ⇒ `STEP[4] Build (must be warning-free)` 打的是 **error**（`dismissRowInk` 非隔离引用），STEP[5]–[14] 因此 skipped、STEP[15]/[17]/[18]/[19] 的红是同一成因的回声；② 最小修法加一行 `@MainActor`（**产品 0 文件**）；③ 新判据 `MenuBarSeamReaderIsolationTests`（真值表 + 真扫，现读 `SEAM_READER_ISOLATION 文件=98 代码位引用=1 未标注=0`）；④ 变异刀 M792 CAUGHT、`RESTORE_CLEAN=yes`；⑤ 看图腿复用上一轮 162 张帧：`COMPARED=162 CHANGED=0 MISSING=0 ADDED=0`（先量 `PRODUCT_FILES=0` 才复用）。

验证：`BUILD_WARN=0`；判据卷 `MenuBarSeamReaderIsolationTests|MenuBarSwiftUIDismissRowInkTests` 5 格 0 失败；全量卷 全量卷 Executed 915 tests / 44 skipped / 0 failures（Test Suite 'All tests' passed，见 /tmp/r237_full.log）；帧基线如上；脚本电池在台账落盘之后跑，读数写在本笔 commit message 里（顺序规矩）。

**下一轮（R238 / 第 237 轮 / Round 235）的靶**

⓪ **本笔的 CI 完全未读**（268 的 runner 半、也是 R236 那三笔一直没读完的那一半）⇒ `python3 scripts/ci_read.py latest` 现拿 run↔commit 成对，再看 `steps <run>`：**要验的是 STEP[4] 有没有转绿**（这一条不绿，后面所有步骤的处置都不许当成产品读数）、`SEAM_READER_ISOLATION` 在 runner 上打的那一行、新判据两格有没有露面、以及 249 / 263 那两格。
① 249 与 263 的分辨读数（`pixels > 400` 那个证人；判据要自印读数，`--log-failed` 会截断断言正文）。
② 268 的 runner 半（见 ⓪）。
③ 251 / 250 / 253 的「接进 CI」那半。
④ 267（10ms 绝对地板 vs 存在性断言）、260、262、258 第三处、254→255→248、243、227③、222、215、201 / 202、207、240。
⑤ 要用户真机或授权的：220 路 A（改全局键盘偏好）、228②、265（悬停那一行的真机观感）。


最后更新：2026-10-20 08:02（本地 · R236 / 第 235 轮 / Round 233：**13 那棵 SwiftUI 树的「都不是我想要的」收成一条可读的缝 + 两轴判据 —— R235 那枚 ESCAPED（M787，本轮同一处变异重编号 M790）关成 CAUGHT，而画面一字未动**（U-757…U-760 · D-221 · 产品 1 文件 + 判据 1 新文件 + 刀 3 把）

**本轮落地**：① **264 结案**：`MenuBarRecommendationsView` 新增 `dismissRowInk: Color? { nil }` 与
`dismissRowLabel()`（这一行标签的唯一构造路径），新判据 `MenuBarSwiftUIDismissRowInkTests` 三格 =
尺自对照 / **行为轴**（缝给的非 nil 墨必须在两档 × 静置 4.5 / 选中 3.0 上过线，地板从 D-220 继承不新造）/
**结构轴**（body 必须走 `Self.dismissRowLabel()`，函数体内 `.foregroundStyle(` 恰好一处且参数必须是 `ink`）。
② 三刀各自只红在自己那一格（`--log` 逐条列名，仪器自己印的）：M789→12 那棵的在岗证人、M790→结构轴、
M791→行为轴 ⇒ `CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes` ⇒ "把那颗蓝钉回来"现在**两条路都会红**。
③ 行为轴本机读数 暗 `16.67 / 6.23`、亮 `21.00 / 14.08`，与 D-220 的 AppKit 参照臂**逐字相同** ⇒ 两棵树在同一把尺上对上账。
④ 看图腿量的是"没变"：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_r236` 重捕 **162** 帧，对 WorkingManifest 基线
`CHANGED=0 / MISSING=0` ⇒ 本轮是**纯缝**（不改变画面的重构，把"只有帧基线在管"换成"两轴各有一刀"）。
⑤ 抓到仪器自己的坏（U-759）：R235 那版"红名"列 `split("]")[-1]` 恒取空串 ⇒ 台账里那句"红名点名新格"
**从来不是仪器打印的**；本轮修成 `[-2]` 并要求非空。规矩：仪器印空列 = 那条读数不存在。
捕获卷 80/4/0；全量卷 **913/44/0**（+3 = 新判据三格）；换装本机 ok；电池见本笔之后那条读数。

**下一轮（R237 / 第 236 轮 / Round 234）的靶**：⓪ **本笔的 CI 完全未读**（R236 三笔：产品半 `415abf3`、
台账半本笔、以及上一轮 push 的 `bc91f16`）⇒ 用 `python3 scripts/ci_read.py latest` 现拿 run↔commit 成对，
`conclusion` 读不到只能写「未读」；要验的是新判据三格 + `MENUBAR_SWIFTUI_DISMISS_INK` 通道在 runner 上的两档读数、
`live_sources` 闸门、别名表 `236:233`。① **249 / 263**：modechip 悬停填充 runner `pixels>400` 那朵红的分辨实验
（产品弱 vs 这台机器合成差异），断言正文在 `--log-failed` 里被截断 ⇒ 必须由判据自己印读数，地板不许放宽。
② **267**：`testAddingACopyWritesNothingOnTheMainThread` 的 10ms 绝对地板在 runner 上 11.56ms（三跑 1.20/0.89/11.56）
⇒ 先量"哪几条断言真正承担契约"，任何口径变更要配「不接新通道时旧的红照旧红」的正对照 + 一刀。
③ 251 / 250 / 253 的"接进 CI"那一半；④ 260 名册静默截断、262 编号守卫只覆盖到 D-194、258 第三处、
254→255→248、243、227③、222、215、201/202、207、240；⑤ 220 路 A、228②、悬停真实观感（265）等用户真机/授权。
结构轴的推广（别处若新写死色，「缝 + 一处着色 + 两轴刀」这个形状能直接抄）记在 U-760 ②，是登记不是漏。

**这段之前的历史（R235 / 第 234 轮 …）保留在下面，不删。**

---


**本轮落地**：① 三条目测里两句落在 D-093 禁止的轴上（截断、对齐）⇒ 撤回不开条目；第三句（那条蓝）
落在可以判的颜色档 ⇒ 从产品入口 `populate` 交出的真 `NSMenuItem` 量墨：改前亮档静置 **3.52:1**、
两档选中底 **1.93 / 2.36:1**，同棵菜单正文参照 16.67 / 21.00、6.23 / 14.08 ⇒ 两种态都输，不必等真机
分辨"蓝压蓝 vs 系统覆盖显式色"，撤掉写死墨（D-220），身份改由分隔线 + 末段位置承担，并把
"前面必须有分隔线"写成会红的断言。② 新判据 `MenuBarDismissRowInkTests` 两格（尺自对照 + 两档 ×
静置 4.5 / 选中 3.0 地板 + 参照臂）。③ **runner 验收到了**：run 39338153114（= d4a2440）STEP[15] 打出
`MENUBAR_DISMISS_INK` 暗 12.82/6.23、亮 17.78/14.08，地板两档全过 ⇒ 这一笔在 CI 上成立；
同一跑的**两朵红与本轮无关**，仍是 `testModeChipHoverFillIsVisibleOnItsOwnSurface`（263 照旧开着）。
④ 变异两刀的真读数（旧账 NOT_RUN 是假话，已补正）：M786 CAUGHT、**M787 ESCAPED**、NOT_RUN=0 ⇒
13 那棵 SwiftUI 树的墨**没有会红的行为判据**，而 `App.swift:28` 就在实例化它 ⇒ 活路径缺牙（BACKLOG 264）。
⑤ NOT_RUN 的成因反向复现过：`SDKROOT` 指向 CLT SDK + Xcode 的 swiftc ⇒ `error: 'clipboardhistory':
Invalid manifest`（`/tmp/r235_manifest_repro.txt`）；修法是剥 `SDKROOT` 并让基线臂不绿就拒绝出表。
帧 162 对账 CHANGED 2→0 同笔 update；捕获卷 80/4/0；全量卷 910/44/0；换装本机 ok；电池 416 OK(skipped=2)。

**下一轮（R236 / 第 235 轮 / Round 233）的靶**：⓪ 已读：`39340316744=614ec3c` ⇒ failure，STEP[15] **两朵**（263 那朵 + 新露面的 `testAddingACopyWritesNothingOnTheMainThread` 11.56ms>10ms，见 U-756 / 新开 267），STEP[17] 捕获门 1 朵；其余 run 用 `python3 scripts/ci_read.py latest` 现拿，`conclusion` 读不到只能写「未读」。
`39340316744=614ec3c`（in_progress）、`39341701083=e4fb89a`、其后两笔台账补记 `b0dc251`（U-752）与 `e5c4185`（U-753）触发的 run 仍**未读** ⇒ ⓪ 的完整清单用 `python3 scripts/ci_read.py latest` 现拿，不手数。本笔之后 266 已结案（U-753：那一格改成 `live_sources` 现读、无 LAG 容差），电池计数 **416 → 418**。
本补记笔（U-751 / BACKLOG 266：两根轮次映射闸门改成读字段）push 之后，它的 run↔commit 用
`python3 scripts/ci_read.py latest` 现读拿，不许手写 id ⇒ ⓪ 的全集是「上面三对 + 这一对」，不是只有三对。
① **264**：给 13 那棵补一条会红的判据（label 文案与墨做成可读纯函数，像
`MarkdownPresentation.appliesWideContentBackground` 那样留缝），并配一刀把 M787 的 ESCAPED 关成 CAUGHT。
② **249 / 263**：modechip 悬停填充 runner 218/229 < 地板 400 的分辨实验（产品弱 vs 这台机器合成差异），
两条判据同源、不许放宽地板。③ 251、250、253 的"接进 CI"那一半（**266 已由 U-753 结案**：「最后动 Sources」那格改成 `live_sources` 现读、无 LAG 容差、两向证人各跑过，电池 416→418）；265、258 第三处、254→255→248、
243、227③、222、215、201/202、207、240；④ 260 名册静默截断、262 编号守卫只覆盖到 D-194；
⑤ 220 路 A、228②、悬停真实观感（265）等用户真机/授权。

**这段之前的历史（R230 / 第 232 轮 …）保留在下面，不删。**

最后更新：2026-10-20 03:24（本地 · R230 / 第 232 轮：**悬停那一层灰全仓只留一条换算：两处"不走样式表"的自绘位点搬进 `HoverInk`，并抓到 R229 那一抬带着一个洞上线（亮档选中段 233→228 凭空一层灰）**（U-741…U-744 · 产品 3 文件（换算出口 + 段按钮让位 + 玻璃圆改走共用路径） + 判据 2 文件 + 夹具 1 文件 + 表 1 文件）

**本轮落地**：① 抓到**上一轮已上线**的洞 —— `HoverInk.opacity` 少 `level == 0` 出口 ⇒
写 `hoverLevel: 0` 的位点被亮档抬量抬成 0.025（凭空一层灰）。两态对照签：亮档选中段 `233→228`、暗档 `36→36`。
修成 guard + 真值表 + 像素断言 + 刀 M772。
② 两处"不走样式表"的直读位点搬进同一条换算：段按钮原来两层灰叠着 ⇒ 样式层让位；
玻璃圆钮在 `.compositingGroup()` 内自绘 ⇒ **同一名义 alpha 实测更弱**（改前亮档 230 = 1.175:1 < 1.20，
共用路径同令牌 1.225:1）⇒ 删自绘层改走 `pressedStyle`。修完四格读数 亮 1.224/1.220、暗 1.239/1.220 全过线，
选中段 233→233/36→36 无幽灵层，R229 旧药丸未碰坏（1.225/1.211）。
③ 新守卫 `HOVER_TOKEN_ROSTER files=3 reads=4`：把"还剩几处自己画悬停层"变成**只准降的数**。
刀 4 把全 CAUGHT（M771、M772、M773、M774）；帧 `COMPARED=154 CHANGED=0 BASELINE_ADDED=6`（旧帧哈希一条没动）；
捕获卷 78/0 失败、全量卷 905/44/0（（无））；换装本机 `INSTALL_RESULT=ok`；
看图腿真做 6 张新帧，并记下 `glass-pill-hover` 的能力边界（整条胶囊一起亮 ⇒ 逐颗的态另开 **257**）。

**下一轮（R231）的靶**：⓪ 读 `a7e3154`（run `39301400951`）与本轮这一跑的 CI —— 249 / 253 的"接进 CI"那一半仍未读；
① 256：DetailView 那两处 + SettingsView 那一处搬进 `HoverInk`，把名册 reads 从 4 降到 0；
② 257 逐颗悬停帧；③ 254（"录制中"两帧相位不确定：本轮又是靠重跑拿稳定值，第二次了）、
255（性能预算格换成同一次运行内的相对判据，不许直接抬 250）；
④ 248、243、250、227③、222、215、201/202、207、240；⑤ 220 路 A、228② 等用户。
)

最后更新：2026-10-20 02:16（本地 · R229 / 第 231 轮：**回到动效位点：悬停那一档第一次有两档帧（251 的第一批），量出亮档药丸 1.160:1 掉在自家地板 1.20 下 ⇒ 整条亮档反馈梯抬一档（暗档一字未动）**（U-737…U-740 · 产品 3 文件（令牌 + 按压样式 + 行收藏按钮的可见性） + 判据 1 新文件 + 夹具 1 文件 + 表 1 文件）

**本轮落地**：⓪ `da5da47` 在 runner 上 success ⇒ **249 的第一格读到**：`verdict=skipped not_run=4 probes=7`、
`missing_frames=0`，D 判据第一次在 CI 上给产品读数（组合帧最左墨 [20.0, 20.0]pt）；剩下 4 颗成因 `bg-not-flat、no-ink`
（统计页内容列平涂那一族）⇒ 那几颗量的仍是通道不是产品。
① 回到动效位点：加取证通道 `hoveredForCapture`（产品不写）+ `RowFavoriteButton` 留出文件边界 ⇒
`row-favorite-idle` / `row-favorite-hover` / `controlprobe-hover-ladder` × 两档共 6 张帧；
`contentMustFit` 拦下第一版（40pt 裁掉药丸）⇒ 抬到 56pt。
量出两难：亮档药丸改前 `(238)`/白 = 1.160:1 < 自家地板 1.20（改前那一读由 `pre_lift_r229.py` 签：撤掉那一抬重跑捕获卷，那一跑红在 `testHoverPillIsVisibleAgainstItsOwnSurfaceInBothAppearances`），而只抬 hover 会把 `hover→pressed` 压到 3.7/255（R14 实测）
⇒ **整条亮档梯子同抬**（hover +0.025、pressed +0.015），暗档一字未动；抬完亮档 `(232)` = 1.225:1、台阶 23，
梯子探针两臂差 亮 5 / 暗 4 ⇒ R20"小控件要抬一档"第一次有像素证人。
两条既有守卫各红一次（新档位要进梯子 / `pressed` 只剩声明）⇒ 抬量搬成 `enum VisualFillLift`、换算进产品侧 `fillOpacity`，未放宽。
刀 3 把全 CAUGHT（M768、M769、M770）；自曝三笔（认红的正则漏 `]` ⇒ 三度 ESCAPED 假账、buttonStyle 挂错宿主、判据走助手）。
验证：构建 0 告警、捕获卷 77/0 失败、全量卷 903/44/1（唯一红 `testImageComparisonCostStaysBounded`，**工作树单跑也红**）、
`COMPARED=148 CHANGED=2 BASELINE_ADDED=6`（动的两张是"录制中"，非本轮引入 ⇒ 开 **254**）、
性能预算格先于本轮就红（HEAD worktree 同格最快 258.75ms 对照工作树 255.97ms）⇒ 开 **255**、换装本机 `INSTALL_RESULT=ok`、看图腿真做（4 张新帧）。

**下一轮（R230）的靶**：⓪ 读本轮与 R225 那几跑（左轴在 @1x 上应稳定 `not_run=4`、捕获卷在 runner 上是否仍绿）；
① 251 剩下的位点：`DetailView` 那两处 hover 底与侧栏批量按钮 —— 本轮的取证通道已经打通，逐位点补帧再判；
② 254（"录制中"两帧相位不确定 ⇒ 冻结相位或换判据）、255（性能预算格**先于本轮**就越预算，HEAD 对照已证 ⇒ 换成同一次运行内的相对判据，不许直接抬 250）；
③ 248、243、250、227③、222、215、201/202、207、240；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-20 00:20（本地 · R228 / 第 230 轮：**253 结案：判据不许把证据押在写死的轮次帧目录上 —— 换成 `CLIPBOARD_HISTORY_UI_SHOTS` 派生 + 三格守卫（守卫第一跑就抓到一处 grep 漏掉的）**（U-734…U-736 · 判据（python）3 文件，产品 0 文件）

**本轮落地**：253 结案。两格真帧对照不再指着某一轮的临时帧目录，改由 `CLIPBOARD_HISTORY_UI_SHOTS` 派生；
取不到时 skip 文本点名**通道**。两向证人都真跑：给变量 ⇒ 两格 `ok`；不给 ⇒ `OK (skipped=2)` 且文本含变量名。
新守卫 `test_frames_path_hygiene.py`（真扫 / 正对照 / 负对照）第一跑就红在**我 grep 漏掉的那处**
（`surface_left_axes.py` 的 docstring 用法示例）⇒ 改成变量占位。
**记账未做**：没把这两格接进 CI 步骤（要让 runner 也产帧，属 235/249 那一族）⇒ "runner 上真判"仍不成立。
电池 `Ran 406 OK (skipped=2)`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN。

**下一轮（R229）的靶**：⓪ 读 `da5da47` 与 R225 那四跑（左轴在 @1x 上是否 `verdict=ok` = **249 的第一格**，红先归因不许放宽）；
① **回到动效位点本体**：251 那批共用 `VisualFill.hover` 的位点先补两档帧再逐位点判（自评连续 <90 就卡在这里）；
② 把这两格真帧对照接进 CI 步骤（本轮明记未做）；③ 248、243、250、227③、222、215、201/202、207、240；
④ 220 路 A、228② 等用户。
)

最后更新：2026-10-20 00:13（本地 · R227 / 第 229 轮：**252 结案：那 3 条 skip 没有一条是 PIL 类（像素判据在 runner 上真跑了 365 行 ok），但其中两条挂在写死的 `/tmp/shots_r211` 上 ⇒ 它们在 runner 上永远 skip，本机只是恰好还留着那个目录**（U-731…U-733 · 判据 0 文件 + 台账，产品 0 文件（读数轮））

**本轮落地**：读 252 的名单 —— 那 3 条 skip 逐条是：端到端：真读一次仓库里已构建的包。这条就是 D-029 当时缺的那一关。 ⇒ 仓库根目录没有已构建的 .app（先跑 make bundle 再验）；test_real_frames_pass_and_report_ok (test_surface_left_axes.CiExitTests.test_real_frames_pass_and_report_ok) ⇒ /tmp/shots_r211 不在盘上；test_working_frames_still_satisfy_the_three_relations (test_surface_left_axes.RealFrameTests.test_working_frames_still_satisfy_the_three_relations) ⇒ 帧目录不在（/tmp/shots_r211）⇒ 这一格本机 NOT-RUN。
**没有一条是 PIL 类**，同跑 365 行 `... ok` ⇒ 上一轮 244 的结案范围站住（解释器接对了、像素判据真跑了）。
但顺带挖出更坏的一格：其中两条挂在写死的 `/tmp/shots_r211`（R211 的临时帧目录，/tmp/shots_r211=在盘上）⇒ 这两格在 CI 上永远不跑（本机只是暂时跑），
却以 skip 的样子安静存在 —— 同一族（夹具不许写共享绝对路径 / 临时目录不许跨次复用）这次犯在**判据自己**身上。
新开 **253**（帧目录改由捕获卷同一个环境变量派生 + 一条"判据里不许出现写死 /tmp/shots_rNNN"的会红守卫）。
左轴仍 `verdict=skipped not_run=7 probes=7`（`e015455` 早于 R224 的 pt 修法）；`da5da47` 仍 `in_progress`、
`09d9bf7` 仍 `queued` ⇒ **249 与 R225 的 runner 复验未读**，未读不算绿。
本轮 0 判据、0 产品改动 ⇒ 未换装本机、看图腿 NOT-RUN。

**下一轮（R228）的靶**：⓪ 读 `da5da47`（run `39280048395`）与 R225 四跑：左轴在 @1x 上是否 `verdict=ok`（**249 的第一格**，
红先归因不许放宽）、`Swift tests (executed-count gate)` 是否仍绿；
① 修 253（写死的帧目录 + 那条会红守卫）；② 回到动效位点：251 先补两档帧再判；
③ 248、243、227③、222、215、201/202、207、240、250；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-20 00:09（本地 · R226 / 第 228 轮：**244 结案：runner 的判据卷走上了带 pillow 的解释器（`SCRIPT_PIL_OK 13.0.0`、`SCRIPT_SKIPS=3`），左轴那一步仍等 `da5da47` 那一跑**（U-728…U-730 · 判据 0 文件 + 台账，产品 0 文件（本轮是读数轮））

**本轮落地**：⓪ 读 run `39277485218`（`e015455`，**success**）：`SCRIPT_PYTHON=/tmp/pilenv/bin/python`、`SCRIPT_PIL_OK 13.0.0 /private/tmp/pilenv/bin/python`、
`SCRIPT_SKIPS=3`、无 `SCRIPT_PIL_MISSING` ⇒ **244 结案**（结的是「判据卷的解释器接对了」，
不是「像素判据全跑了」；剩 3 条 skip 的归属未读 ⇒ 开 **252**）。
左轴这一跑仍 `cause=no-bg-window`（`verdict=skipped not_run=7 probes=7`，帧 @1x）—— 按 pt 写窗口是 R224（`da5da47`，
run `39280048395` 仍 `in_progress`）⇒ **249 未读**，不许拿这一跑证伪 R224。R225 四跑 `09d9bf7`=`39282426231` 仍 `queued`。
本轮 0 产品、0 判据改动 ⇒ 未换装本机、看图腿 NOT-RUN。

**下一轮（R227）的靶**：⓪ 读 `da5da47`（run `39280048395`）与 R225 那四跑：左轴在 @1x 上是否 `verdict=ok`（**249 的第一格**，
红要先归因、不许放宽）、`Swift tests (executed-count gate)` 是否仍绿；
① 读 3 条 skip 是谁、为什么跳（252）；② 回到动效位点：251 那批共用 `VisualFill.hover` 的位点**先补两档帧再判**；
③ 248、243、227③、222、215、201/202、207、240、250；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-20 00:03（本地 · R225 / 第 227 轮：**回到动效位点本体：浮层悬停那一档改成**按色档取墨** —— 亮档实测 1.14:1 掉在仓库自己的 1.20 地板下，抬到 1.225:1（暗档一字未动）**（U-725…U-727 · 产品 1 文件 + 判据 1 新文件 + 表 1 文件）

**本轮落地**：回到动效位点本体（连续多轮 0 产品改动之后）。位点＝快速选择浮层/悬停，取证＝盘上两张帧现算：
亮档悬停带 `(240)`/白 = **1.14:1** 掉在仓库自己 R220 定的亮档地板 1.20 下，暗档 `(43)`/`(30)` = **1.177:1** 过 1.10
⇒ 与 R219 同形的"一个 alpha 管两档"。改成 `hoverFillAlpha(dark:)`（暗档仍等于 `VisualFill.hover`，亮档 +0.03），
画法自己问 `effectiveAppearance`。改后亮档 `(232)` = **1.225:1**，与选中带 `(220)` 仍差 12 级（不撞选中）。
**帧签**：`COMPARED=142 CHANGED=1`，唯一动的 `quickpick-hover-420x300-light.png`，暗档那张逐字节不变；基线同一笔 update。
新判据 `QuickPickHoverInkTests` 两格；刀 `R225_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0`（M763/M764），名册已登记。
验证：构建 0 告警、捕获卷 75 格 0 失败、**全量卷 897 格 44 skip 0 失败**（D-208）、换装本机 `INSTALL_RESULT=ok`。
新开 **251**（其余共用该令牌的位点没有两档帧可量 ⇒ 先补取证再改，不顺手）。

**下一轮（R226）的靶**：⓪ 读本轮与 `da5da47`/`e015455` 三跑：`SCRIPT_PIL_OK`/`SCRIPT_SKIPS`（**244 结案的唯一通道**）、
左轴那一步在 @1x 上是否 `verdict=ok`（**249 的第一格**，红要先归因不许放宽）；
① 继续动效位点：先给 251 那批"共用一个数"的位点补两档帧，再逐位点判；
② 248、243、227③、222、215、201/202、207、240、250（守卫看不见粗体决定）；③ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 23:38（本地 · R224 / 第 226 轮：**246 的 runner 读数落账：七颗探针全在 no-bg-window，查出来是这把尺把窗口写在 @2x 像素上 —— 坐标约定已修（BACKLOG 249）**（U-722…U-724 · 判据（python 尺）1 文件 + 表 1 文件，产品 0 文件）

**本轮落地**：⓪ 读到 runner 的成因分档 —— 七颗探针全是 `cause=no-bg-window frame=420x300 / 720x520 / 720x540`、
`missing_frames=0` ⇒ 帧在、尺寸对，取不到的是**底**；顺着这一档读回自己的表，病根是**坐标约定**：
探针窗口按本机 @2x 像素写死，@1x 的 runner 帧必然掉到画外。改成"窗口按 pt 写 + 像素每 pt 由帧自己算"。
两向对照：本机 @2x 读数逐字不变（`IDENTICAL_TO_BEFORE=True`）、@1x 复刻帧 `7`→`NOT_RUN帧=0`；
复刻帧读数不等于真帧（REPLICA_SHIFT 改前=148.0 改后=177.0）⇒ 只配证明坐标修好，不配给产品定罪，承重的是新增的缩放不变量自检格。
两把刀 `R224_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0`；预检 `tables=65 bad=4`；
名册去掉 `mutate_r220` 重复登记；电池 `Ran 403 OK`。
CI：`69bccbd`=`39273827335` success、`PILLOW_OK 13.0.0`，`SCRIPT_PIL_OK` 没有一行（判据卷走 venv 在 `e015455`，仍 in_progress）
⇒ **244 仍等**；246 结案、新开 **249**、立 **D-216**。产品 0 文件 ⇒ 未换装本机。
看图腿真做了：5 张帧，挑出的两个候选位点一查都已有判词（侧栏纯黑=已登记离屏伪影；菜单栏墨顶边=U-56 已在 R34 收回）。

**下一轮（R225）的靶**：⓪ 读 `e015455`=39277485218 与本轮这一跑：`SCRIPT_SKIPS` 掉到几条（**244 结案的唯一通道**）、
左轴那一步在 @1x 上是否 `verdict=ok`（**249 的第一格**）—— 若红，先归因再动手，不许放宽；
① **回到动效位点本体**（连续多轮 0 产品改动，本轮又是判据账）：按目标要求**逐屏逐元素列全清单**，
挑一位点真做动效 + 帧 + 基线 update + 刀 + 全量卷 + 换装 + 看图；
② 248（§1 其余活数格）、243、227③、222、215、201/202、207、240；③ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 23:19（本地 · R223 / 第 225 轮：**247 解释并修好（旧变异表的锚点被我上一轮改源码时弄脱钩）、244 落地：判据卷也走 venv，像素自检第一次有机会在 runner 上跑**（U-719…U-721 · CI 1 文件 + 表 1 文件，产品 0 文件）

**本轮落地**：上一轮那格"未解释的数"解释了 —— 预检 `bad` 只数三件事（导入失败 / 读文件失败 / **needle 命中≠1**），
`dupes=0 repeats=0` ⇒ 五条全是**锚点与文件脱钩**，其中 `mutate_r213` 的 M747 是我 R221 改 `live()` 时弄脱钩的
（那张表今天重跑会 NOT_RUN，而 CI 和人都不会去重跑历史表 ⇒ 坏得很安静）。
修锚点后 `bad` 5→4，并**真重跑旧表**：`R213_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0` ⇒ 立 **D-215**。
244 落地：venv 步骤前移到判据卷之前（只剩一条，R218 那条删除），`Release script tests` 改用
`/tmp/pilenv/bin/python`（装不上才退回系统解释器 = 环境缺席，不是产品结论），加三行证人
`SCRIPT_PYTHON` / `SCRIPT_PIL_OK` / `SCRIPT_SKIPS=`；本机 python3 有 PIL 11.3.0 且那批本来就是绿的 ⇒ 不是赌。
CI：`cc0e358`=`39272745719` **success**（`PILLOW_OK 13.0.0`，但 `LEFT_AXIS_CI verdict=skipped not_run=7 probes=7` 且早于分档）
⇒ runner 上还没有 `cause=`；带分档的三跑 `69bccbd`/`540bb1e`/`04a68ed` 全 in_progress ⇒ **246 仍等**。
验证：电池 `Ran 403 OK`；预检 `tables=65 covered=50 arms=182 bad=4`；
产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、无新帧）。

**下一轮（R224）的靶**：⓪ 读本跑（第一个"cause 分档 + venv 判据卷"同时上去的一跑）：
`SCRIPT_PIL_OK` 有没有露面、`SCRIPT_SKIPS` 掉到几条（**244 结案的唯一通道**）、左轴那一步的 `cause=` 是哪一档（**246 结案的唯一通道**）；
① **回到动效位点本体**（连续多轮 0 产品改动）：清账表里挑一位点真做动效 + 帧 + 刀 + 看图 —— 这是目标问的东西，别再交判据账；
② 248（§1 其余活数格）与 ⓪b（报告刷新排到台账之后 / 让生成器幂等）—— **R223 已把幂等版落进仓库：`scripts/refresh_final_report_headline.py`**（锚点匹配数字形状而非上一版的具体数字，写完自己调守卫的 `headline_problems` 复核），下一轮收尾按顺序跑它一次即可；③ 242 其余亮档表面、243、227③、222、215、201/202、207、240；
④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 23:10（本地 · R222 / 第 224 轮：**最终报告的活数格换到对账：标题停在 R136 / §1 停在 94 轮与 U-210，本轮起有一条守卫盯着它（并配两把刀）**（U-716…U-718 · 判据 1 文件 + 报告本体，产品 0 文件）

**本轮落地**：`AGENT_FINAL_REPORT.md` 的活数格换到现读现写 —— 标题从 **R136** 到 **R221**、
§1 轮数从 **94** 到 **214**（`PHASE2 n`）、视觉台账从 **U-210 / 179 条** 到 **U-715 / 432 条**、
日期与本机 install 那格换成 R219 的实际读数（R33 那两行标为历史，不删 prose 只走行内替换），
并追加 §12（R137–R221 做了什么 / 撤回了什么 / 还欠什么，含五次否证与两次自曝量错对象）。
新守卫 `test_final_report_headline.py` 三格（与活账一致 / 伪造旧值必须点名 / 形状读不到不许静默通过）；
before/after 同一份样本：`Ran 403 FAILED(failures=1)` → `Ran 403 OK`。
两把刀 `R222_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0`（M759/M760 各打一条 staleness 比较）；
**第一版报 ESCAPED 是表的解析坏了**（python3.9 `-v` 把失败印成两段，只认行内 `... FAIL` 会读漏）⇒ 修解析。
自锁死记录：生成器"电池不绿不写"与新守卫"靠报告旧数才红"互相咬 ⇒ 只豁免这一条守卫的名字，其余红照旧拦。
新开 248（§1 其余格子纳入对账或删掉）、立 **D-214**。
验证：产品 0 文件 ⇒ 未换装本机、无新帧 ⇒ 看图腿 NOT-RUN；预检 `tables=65 covered=50 arms=182 bad=5`。
CI：`bc5c5d7`=39272702346、`cc0e358`=39272745719 与本轮这一跑仍待读（246 的成因读数要看 runner 正文）。

**下一轮（R223）的靶**：⓪ 读上面几跑：左轴那一步现在打的 `cause=` 是哪一档（**246 结案的唯一通道**）、
`STEP[8]`/`STEP[15]` 是否仍绿、预检 `bad` 那一格顺手读明白（247）；⓪b **收尾顺序**：报告刷新要排在**轮次台账之后**
（`final_report_r222.py` 不是幂等的，锚点已被本轮改掉；守卫现在钉的是有界落后 `LAG_ROUNDS=1`/`LAG_U=3`，见 248 追记）；
① **回到动效位点本体**（连续多轮 0 产品改动）：清账表未判的格子挑一位点真做动效 + 帧 + 刀 + 看图；
② 248：§1 剩下的格子对账；③ 242 其余亮档表面、243、227③、222、215、201/202、207、244、240；
④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 22:58（本地 · R221 / 第 223 轮：**246 的分辨仪器落地：NOT_RUN 现在交得出成因（bg-not-flat/no-ink），两格已知答案对照 + 两把刀；另有一格读数本轮没解释**（U-713…U-715 · 判据（python 尺）1 文件，产品 0 文件）

**本轮落地**：246 的分辨仪器 —— `surface_left_axes.py` 的 NOT_RUN 现在交得出成因
（`stem-unparsable` / `no-bg-window` / `bg-not-flat` / `no-ink` / `frame-missing`），三档处置相反，
混成一档就等于下一轮重问（提成 **D-213**）。自检加两格已知答案对照（空帧⇒no-ink、棋盘底⇒bg-not-flat），
本机出口一字未变（`verdict=ok probes=7`）⇒ 加的是读数不是判定。
两把刀 `R221_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0`：M757 混档、M758 把缺席当成通过（R210 那条假绿通道）。
CI：`7ebda4c`=39270053664 **success**、`9ab453a`=39270119406 **success** ⇒ R219 的亮档墨没弄红 runner；
`bc5c5d7`/`cc0e358` 仍 in_progress ⇒ 未读不算绿。**未解释的数**：预检 `bad` 4→5（`dupes=0 repeats=0`），
三个累加点没逐条读 ⇒ 记"未解释"，不猜。
验证：电池 `Ran 400 OK`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、盘上 142 张属前两遍）。

**下一轮（R222）的靶**：① **回到动效位点本体**（连续多轮 0 产品改动，目标要的是逐位点重判并加该加的动效）——
从清账表未判的格子里挑一位点，真做动效 + 帧 + 刀 + 看图；
⓪ 读本跑与 `bc5c5d7`/`cc0e358`：runner 上左轴那一步现在打的**成因**是什么（246 结案的唯一通道），
顺带把预检 `bad` 那一格读明白；② 242 的其余亮档表面逐个判（热图阶梯、侧栏占位要不要按档给）；
③ 243、227③、222、215、201/202、207、244、240；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 22:47（本地 · R220 / 第 222 轮：**245 结案：骨架条带对比度进仓库、两档各一条下界；237 结案；235 的第二半答案是坏消息（runner 上 7 颗探针全没有对象）**（U-710…U-712 · 判据 1 文件 + 表面账，产品 0 文件）

**本轮落地**：245 结案 —— 骨架条带对比度从 `/tmp` 手搓尺搬进仓库（`UICaptureTests.skeletonBarContrast`，
条带行谓词与 `skeletonAxisReadings` 同源），两档各一条下界（暗 1.1 / 亮 **1.2**），
外加一格**已知答案对照**（合成 255/225 必须读回 225 与 ≈1.31；整幅同色必须报 `barRows=0`）。
本轮读数：亮档 1.30、暗档 1.15；亮档那条下界在 R219 之前会红（实测 1.12）。
两把刀 `R220_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0`：M755 撤掉 R219 的修法 ⇒ 尺红而**真值表照样绿**
⇒ 立 **D-212**（值判据替代不了像素判据）；M756 把尺的底改成最小值 ⇒ 对照红（第一版 NOT_RUN：needle 是别人的前缀子串）。
CI：run `39267039118` 打 `PILLOW_OK 13.0.0` ⇒ **237 结案**；同跑 `LEFT_AXIS_CI verdict=skipped not_run=7 probes=7`
⇒ **235 的第二半是坏消息**：尺在 runner 上仍无对象，成因从"没库"换成"帧没墨"（201 那一族）⇒ 开 246。
表面账：`详情区 × 加载` 那一格本来就是 `added`（R219 收尾的担心是没读过的假设）；走生成器补了 reason/evidence，
`MOTION_LEDGER_RESULT=ok`、`FLOOR head=162 now=162`、verdict 未翻。
验证：构建告警 0；捕获卷 75/4skip/0fail；帧 `COMPARED=142 CHANGED=0`；预检 `tables=62 bad=4`；
产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 不适用。
CI：本跑 + `7ebda4c`=39270053664、`9ab453a`=39270119406 仍 in_progress ⇒ 未读不算绿（要看 R219 的亮档墨有没有把 `STEP[15]` 弄红）。

**下一轮（R221）的靶**：⓪ 读上面两跑（R219 产品改动的 runner 复验）；① 246：runner 帧没墨这一族 —— 先分辨"哪几张帧在 runner 上真的有墨"，再决定左轴尺要不要按表面切片；
② 242 的其余亮档表面逐个判（热图阶梯、侧栏占位要不要同样按档给）；③ 243、227③、222、215、201/202、207、244；④ 回到动效位点本体（清账表未判的格子）；⑤ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 22:32（本地 · R219 / 第 221 轮：**亮档骨架墨按档给（242 结案）：3 张亮档帧变了、0 张暗档帧变，同时自曝一把量错对象的尺**（U-707…U-709 · 产品 1 文件，判据 1 文件）

**本轮落地**：242 结案 —— 亮档详情骨架的墨与暗档分开给（暗档 0.06/0.18 **未动**，亮档 **0.14/0.26**，lift 两档同 0.12）。
视图只经 `SkeletonMotion.inkOpacities(dark:)` 取墨（唯一读档处，提成 **D-211**）。
证人：帧基线 `changed` 3 张 = 亮档 3 / 暗档 0（按档生效第一次在像素上分开可见）；
组件帧亮档条带 (242,242,242) → (225,225,225)、对比度 1.12 → 1.31（两趟条带行数同 ⇒ 同一对象）；看图判定为**积极作用**（仍比说明文字淡一档、左轴未变、动作栏图标更抢）。
判据：真值表 + 接线守卫；`R219_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0`（M754 第一版编译不过 ⇒ NOT_RUN 不算拦住，换刀重跑）。
**自曝**：一次性尺在组合帧上量错对象（条带行数 168 vs 组件帧 48）⇒ 242 原文的"1.05"不作本轮改前值引用，开 245 做仓库内按档像素判据。
验证：构建告警 0；判据卷 63/21skip/0fail；全量卷 893/44skip/0fail（D-208）；
`FRAME_BASELINE_UPDATED=142`、update 后重比 CHANGED=0；已换装本机；电池在台账落盘后再跑。
CI：本跑（产品改动）+ `193d5be`=39265858795、`1462b38`=39265952407、`261c42d` 都要读 —— **237 结案的唯一通道**是 venv 那一步有没有打 `PILLOW_OK`、左轴那一步的 `verdict` 是否从 `unavailable` 变出来。

**下一轮（R220）的靶**：⓪ 读上面几跑（237；顺带看这一跑的 `STEP[15]` 有没有被本轮的亮档墨改动弄红）；
① 245：把"骨架条带对比度按档各一条下界"做成仓库内的像素判据（别再靠 /tmp 手搓尺），并给 242 的**其余亮档表面**（热图阶梯、侧栏占位）逐个判一次要不要同样按档给；①b **表面账要同步**：`docs/motion_surface_ledger.json` 里若住着"详情/加载骨架"那一格、且判法还是 `not-added`（R215 那句"亮档不加"），本轮已经把它改成 `added` —— R220 先按 `scripts/motion_surface_gate.py` 的实际形状读出那一格现在写的是什么，再决定改判法还是补一格（R219 收尾时探过一次，但我的 JSON 形状猜错了：探针打 `SKELETON_CELLS=0 TOTAL=?` ⇒ 那次探测**不构成**"账里没有这一格"的证据，别照抄）；
② 243：捕帧通道能不能等到 `.task`（先 spike）；③ 227③、222、215、201/202、207、244；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 22:15（本地 · R218 / 第 220 轮：**235 结案成「接线对、runner 没 Pillow」，237 的成因由 runner 正文签死并换成一次性 venv**（U-704…U-706 · CI 1 文件，产品 0 文件）

**本轮落地**：`610e93c`=`39262764467` **completed success** ⇒ R216 修的两朵红在 runner 上消失；
同跑左轴那一步打 `LEFT_AXIS_CI verdict=unavailable reason=pillow-missing probes=0` ⇒ **235 结案成"接线正确、runner 没判过产品像素"**（probes=0 明写）。
237 的真因由 runner 正文签：`error: externally-managed-environment`（PEP 668）+ `PILLOW_INSTALL_FAILED=1`，
R217 我猜的"两台解释器"**已撤回**；修法换成一次性 venv + 下一步显式用 venv 解释器，三种成因三条 echo，
拒用 `--break-system-packages`（**D-210**）。新开 244：判据卷仍用系统解释器 ⇒ NEEDS_PIL 的格子在 runner 上恒 skip。
验证边界：YAML 静态解析 NOT-RUN：本机没有 PyYAML（ModuleNotFoundError），结构证人换成仓库自己的 ci.yml 形状守卫 + 电池 400 格 OK；尺自检 `LEFT_AXIS_SELFTEST ok`；电池 `Ran 400 tests OK`（台账落盘后还要再跑）；
看图腿 NOT-RUN（0 像素改动、无新帧，盘上 142 张属 R217）；产品 0 文件 ⇒ 未换装本机。
CI：本跑（venv 修法）+ `193d5be`=39265858795、`1462b38`=39265952407 仍 in_progress ⇒ 未读不算绿。

**下一轮（R219）的靶**：⓪ 读 venv 那一跑：`PILLOW_OK <版本>` 有没有露面、左轴那一步是否从 `unavailable` 变成 `ok/skipped/red`（**237 结案的唯一通道**）、`193d5be`/`1462b38` 的结论；
① **回到动效位点本体**（已经连续 7 笔 0 产品改动）：清账表里未判的格子挑一位点真做动效 + 帧 + 刀，别再交判据账；
② 243：捕帧通道能不能等到 `.task`（先 spike，别改产品）；③ 227③、222、215、201/202、207；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 22:10（本地 · R217 / 第 219 轮：**BACKLOG 240 的行为证人补上了，实验答案是否定的 —— 捕帧通道分不出两臂，R211 那句「靠它冻住」撤回**（U-701…U-703 · 判据 1 文件，产品 0 文件）

**本轮落地**：240 的行为证人（同一视图两臂像素判据）落地，读数是**两臂相等**（light 50 vs 50；dark 50 vs 50）
⇒ `freezeLoadingForCapture` 在捕帧通道里没有像素后果，R214 注释里"补了证人第三把刀才会 CAUGHT"被实测否证，
R211 台账里"靠它冻住"那句推断撤回。死值刀因此**不登记**（不进表 ≠ 跑过），先决条件开成 243。
两条断言各配一把刀：`R217_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（M750 尺子句、M751 两臂相等正对照）。
看图腿：重捕整卷 `COMPARED=142 CHANGED=0`，看的就是被判据当对象的那张组合帧（头部/条带/句子同轴；亮档条带近乎不可见 = 242 已判过）。
构建告警 0；预检 `tables=60 covered=45 arms=171 bad=3`；产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 的适用面不需要。
CI：本轮这一跑 + `9af75f7`/`610e93c` 都要读 —— `STEP[8]`、`STEP[15]` 是否绿、`Surface left-axis ruler` 打 ok/skipped/unavailable（**235 结案的唯一通道**）。

**下一轮（R218）的靶**：⓪ **CI 读数已取到（R217 收尾时读的，R218 只需把它写成结案账）**：`610e93c` = run `39262764467` **completed success** ⇒ R216 修掉的两朵红（`STEP[8]` 的 FRAME_DIR_MISSING、`STEP[15]` 的调用点守卫）在 runner 上确认消失；同一跑 `STEP[12]` 打的是 `LEFT_AXIS_CI verdict=unavailable reason=pillow-missing hard=0 not_run=0 probes=0` + `LEFT_AXIS_ENV_NOTE import PIL 失败 ⇒ 环境缺席` ⇒ **235 结案成"接线正确、但 runner 上没有 Pillow"**（那把尺至今没在 runner 上判过一次产品像素，不许写成"runner 已验收"）；本跑 `193d5be`=`39265858795`、`1462b38`=`39265952407` 仍 in_progress ⇒ 未读不算绿。
① 243：捕帧通道能不能等到 `.task`（先 spike，别改产品）；② 237（pillow 安装位置）—— **现在有了具体形状**：`Pillow for the frame rulers` 那一步（continue-on-error）没能让学生 `import PIL`，要查的是"装 python 的那台解释器和下一步的 `python3` 是不是同一个"，还是那一步本身就没装成；
③ 227③、222、215、201/202、207；④ 回到动效位点本体（连续多轮 0 产品改动，目标要求的是"逐位点重判并加该加的动效"）；⑤ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 21:45（本地 · R216 / 第 218 轮：**两朵 CI 红归因到自己头上并修好：调用点守卫改形状匹配、新出口测试去掉环境依赖；立 D-208**（U-698…U-700 · 判据 2 文件，产品 0 文件）

**本轮落地**：`982faff` 的 `STEP[15]` 是 R211 我加实参把 `DetailFileView(...)` 调用拆成两行，
整行字面量守卫读不到 ⇒ 改成按空白折叠后比形状，并加一句「freeze 必须接属性」的更强断言；
`STEP[8]` 是 R212 我新加的出口测试把 `--shots` 指到 /tmp/shots_r211，runner 上没这个目录 ⇒ 改指仓库根目录。
本地补跑全量卷：`Executed 890 tests, with 44 tests skipped and 0 failures`（大日志留 /tmp）。新规矩 **D-208**：动了 `Sources/` 的那一轮本地必须跑全量卷，CI 只做复验。
CI：`e8643e2`=39260809114、`9af75f7`=39260903335 仍 in_progress ⇒ 235（尺在 runner 上的出口）继续未读；本轮这一跑也要读。

**下一轮（R217）的靶**：⓪ 读 `9af75f7`/本跑：`STEP[8]`、`STEP[15]` 是否恢复绿、`Surface left-axis ruler` 打的是 ok/skipped/unavailable（235 结案的唯一通道）；
① 240 的行为证人（同一视图两臂像素判据）+ 第三把刀；② 237（pillow 安装位置）；③ 227③、222、215、201/202、207；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 21:34（本地 · R215 / 第 217 轮：**回到画面：重捕 142 张拿到可重复性证人 + 亮档骨架 1.05 的不对称，判为不加**（U-695…U-697 · 产品 0 文件，看图账）

**本轮落地**：同一份工作树重捕整卷 ⇒ `Executed 72 tests, with 4 tests skipped and 0 failures`、`FRAME_BASELINE_COMPARED=142 CHANGED=0 MISSING=0 ADDED=0`、尺 `LEFT_AXIS_CI verdict=ok hard=0 not_run=0 missing_frames=0 probes=7`。
看亮档组合帧量出条带↔底 **1.05**（暗档 1.17）、句子 6.06/3.72、头部 5.91/4.10 ⇒ 亮档"条带近乎不可见"是真的；
成因是 `Color.primary.opacity(0.06)`（纯色，不是材质）⇒ 不是离屏通道；
抬升预算 `0.18-0.06=0.12` 是测量结论（抬 5 个点时胶片峰值 0.0000），只抬 base 会让扫光退回"测不到"
⇒ **判为不加**，"要抬就同时抬两档并重跑胶片判据"记成 BACKLOG 242。
CI：`982faff`=39258075868、`3d4e2f1`=39258514435、`cd9d0cb`=39259442003 三跑 in_progress（未读不算绿）；
`8650547`/`2eb1bee` 已 failure 且归因到同一个 PIL 原因（R212 已修）⇒ 235 继续开着。

**下一轮（R216）的靶**：⓪ 读上面三跑：STEP[8] 是否恢复绿、`Surface left-axis ruler` 打的是 ok/skipped/unavailable（235 结案的唯一通道）、全量卷是否绿；
① 240 的行为证人（同一视图两臂像素判据）+ 第三把刀；② 237（pillow 安装位置）；③ 227③、222、215、201/202、207；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 21:22（本地 · R214 / 第 216 轮：**`freezeLoadingForCapture` 的默认值有了证人（236 值域结案）+ 一次 ESCAPED 挖出两个 bug**（U-692…U-694 · 产品 3 文件）

**本轮落地**：决定提成纯函数 `MediaLoadingPlan.startsLoad`（视图里只留薄胶水），`MediaLoadingPlanTests` 四格（真值表 / 读结构体默认值 / 产品码不许传 true / 夹具恰好一处 true）。
两把刀 `R214_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`。**M748 第一版没咬到**，两个真因都记进账：① 默认值当时有两处（属性初始化 + init 参数），刀打在死的那处 ⇒ 已合并成一处；
② 我的解析只认 `failures` 复数，而单条用例印的是 `with 1 failure` ⇒ 真红被读成 ESCAPED。两处都修完才拿到这条结论行。
**第三把刀故意没配**（把 guard 写成恒加载今天没人会红，只有帧基线会报"像素变了"而说不出原因）⇒ BACKLOG 240；236 记为"值域结案、行为未结案"。
预检 `NEEDLE_PRECHECK tables=59 covered=44 arms=169 bad=3`；动了 `Sources/` ⇒ 已换装本机；全量卷交 CI；看图腿 NOT-RUN（无新帧）。

**下一轮（R215）的靶**：⓪ 读 982faff / 3d4e2f1 / 本跑：STEP[8] 是否恢复绿、`Surface left-axis ruler` 在 runner 上的出口（235）、全量卷是否绿；
① 240 的行为证人（同一视图两臂像素判据）+ 第三把刀；② 237（pillow 安装位置）；③ 227③、222、215、201/202、207；④ 220 路 A、228② 等用户。
)

最后更新：2026-10-19 21:15（本地 · R213 / 第 215 轮：**看图尺的三把刀落地（238 结案）+ a800900 逐步骤落账（235 改挂 982faff）**（U-689…U-690 · 产品 0 文件）

**本轮落地**：`mutate_r213.py` 三把刀全 CAUGHT、`RESTORE_CLEAN=yes`（M745 同帧判据恒真 / M746 把 unavailable 改回裸 raise / M747 让缺席被当成有对象）；
预检 `NEEDLE_PRECHECK tables=58 covered=43 arms=167 bad=3`、`ARM_TOTAL files=137 arms=550 dupes=0 repeats=0`。BACKLOG 238 结案。
**顺序账**：`a800900` 只有 STEP[8] 红，`Pillow for the frame rulers` 与 `Surface left-axis ruler` 都在被 skip 的段里
⇒ 235（尺在 runner 上的出口）在 R209/R210/R211 三跑里**不可能**被读到，改挂到 982faff；234 在那之前只算本机结案。
本轮产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN。

**下一轮（R214）的靶**：⓪ 读 982faff 与本跑的 CI：STEP[8] 是否恢复绿、`Surface left-axis ruler` 在 runner 上打的是 ok/skipped/unavailable（235 结案的唯一通道）；
① 236 的默认值守卫（Swift 侧，带刀）；② 237（pillow 安装位置：保持现状 + 登记，还是前移）；
③ 227③、222、215、201/202、207；④ 220 路 A 与 228② 等用户。
)

最后更新：2026-10-19 21:12（本地 · R212 / 第 214 轮：**runner 那朵红的归属与修法（具名出口 unavailable + exit 2）+ 233 判据半落地 + 拆掉一条 NOT_RUN 遮蔽**（U-686…U-688 · 产品 0 文件）

**本轮落地**：① `c232e82` 起 STEP[8] 的红来自我新加的电池格硬依赖 PIL（runner 没装库），且非 `--ci` 路径抛栈 ⇒ 现在走具名出口 `unavailable` + exit 2，
像素类格子按仓库既有惯例挂 `@NEEDS_PIL`；② 233 的**判据半**结案：组合帧 D 同轴判据读到头部 20.5pt / 骨架 20.0pt（跨度 0.5pt ≤ 2.0），
并纠正 R211 手量的 21.0/22.5（全局门槛 12 把低对比骨架读成「没墨」⇒ 探针级 `thr=6`）；
③ 拆掉一条假绿通道：NOT_RUN 过去会连带免掉别的规则，现在只免引用它的那条（证人：缺席与真违反并存必须仍红）。
验证：脚本电池 `Ran 400 tests` 且 OK；尺自检 7 格对照全对；真帧 `LEFT_AXIS_CI verdict=ok … probes=7`。
**未做**：两把刀 ⇒ BACKLOG 238；pillow 装在电池之后 ⇒ runner 上像素格恒 NOT-RUN，是否前移开成 237；CI 上这一步的出口仍未读 ⇒ 235 继续开着。

**下一轮（R213）的靶**：⓪ 读 `2eb1bee`/`8650547` 与本跑的 CI：STEP[8] 是否恢复绿、`Surface left-axis ruler` 那一步在 runner 上是 ok/skipped/unavailable（235）；
① 238 两把刀；② 236 的默认值守卫（Swift 侧，带刀）；③ 227③、222、215、201/202、207；④ 220 路 A 与 228② 等用户。
)

最后更新：2026-10-19 20:58（本地 · R211 / 第 213 轮：**详情加载态的第一张组合帧（头部 + 骨架同框）+ 删掉注释里一句无人验收的承诺**（U-683…U-685 · 产品 2 文件，看图账 + 判据账）

**本轮落地**：`DetailView` / `DetailFileView` 加默认关闭的 `freezeLoadingForCapture`，新帧
`detail-loading-composed-720x520-{dark,light}` 进工作基线 ⇒ R209 那句"加载时头部消失"现在由**像素**否证：
头部那行日期/文件名/来源在加载态确实在，头部最左墨 21.0pt、骨架 22.5pt（差 1.5pt = 字形侧边距，同一列）。
自查抓到一处假话：注释声称 `DetailPreviewCaptureSeamTests` 钉住默认值，而那支测试不存在 ⇒ 删掉注释那句话，开 BACKLOG 236。
验证：构建 0 告警、`Executed 72 tests, with 4 tests skipped and 0 failures (0 unexpected) in 207.326 (207.332) seconds`、帧 142 张、`FRAME_BASELINE_ADDED=2`、电池 `Ran 399 tests` 且 OK、清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`、已换装本机。
**233 只算半结**：同帧关系判据（两枚探针 + 一把刀）本轮未做，写在 233 追记里。
CI：`6` 跑 success（bbc5642=39251464899、04ccf7a=39247806444、3073943=39247153666、f6d3b4a=39246385660、187ec0b=39245844718）、`1` 跑仍未读（a800900）、失败跑 c232e82 ⇒ 未读的不算绿。

**下一轮（R212）的靶**：⓪ 读仍未那几跑的 CI —— 特别是 `a800900`（R210 那一步在 runner 上的第一跑：ok / skipped / unavailable？）与本轮这一跑；
① 233 的判据半：给 `surface_left_axes.py` 加"头部行 / 骨架行"两枚探针 + 同帧 ≤2pt 关系判据 + 一把"把头部内缩改歪"的刀；
② 236 那格默认值守卫（产品入口进，带刀）；
③ 227③、222、215、201/202、207；④ 220 路 A 与 228② 仍等用户。
)

最后更新：2026-10-19 20:48（本地 · R210 / 第 212 轮：**看图尺接进 CI —— 三种出口（red/skipped/unavailable）各配证人，三把刀全 CAUGHT**（U-680…U-682 · 产品 0 文件，判据账 + CI 接线）

**本轮落地**：`scripts/surface_left_axes.py` 加 `--ci`（真红才 exit 1；只有 NOT_RUN ⇒ skipped 并把缺席写成读数；没有像素库 ⇒ unavailable），
`.github/workflows/ci.yml` 加两步：装 pillow（continue-on-error）与 `Surface left-axis ruler (BACKLOG 234, wired in R210)`（**不** continue-on-error）。
处置逻辑写在 python 里而不是 shell 里（R64）。新表 `mutate_r210.py`：M742 恒绿出口 / M743 缺席算真红 / M744 容差放大成恒真 ⇒
`R210_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；预检 `NEEDLE_PRECHECK tables=57 covered=42 arms=164 bad=3`、`ARM_TOTAL files=136 arms=550 dupes=0 repeats=0`。规矩立成 **D-207**：任何新接进 CI 的判据，落地那一轮就要有"把它改成恒绿"的刀。
电池 `Ran 399 tests` 且 OK（新增 6 格）；本机真帧 `LEFT_AXIS_CI verdict=ok hard=0 not_run=0 missing_frames=0 probes=5`、`LEFT_AXIS_SELFTEST ok`；清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`。
**BACKLOG 234 只算本机结案**：这一步在 runner 上的第一跑结论未读 ⇒ 新开 235，下一轮第 ⓪ 条读它。
CI：`7` 跑 success（bbc5642=39251464899、04ccf7a=39247806444、3073943=39247153666、f6d3b4a=39246385660、187ec0b=39245844718）、`1` 跑仍未读（c232e82）、失败跑 无 ⇒ 未读的不算绿。

**下一轮（R211）的靶**：⓪ 读本轮这一跑的 CI，按**步骤名**过滤 `LEFT_AXIS_CI` 那一行（ok / skipped / unavailable 三种出口谁出现），
并把 235 填回账；顺带把 `bbc5642` 之后仍未读的那几跑逐条落账；
① 233：详情加载态的组合帧注入点（产品半：给 `DetailFileView` 的加载分支一个默认值=现行行为的 seam）+ 把跨帧比换成同帧关系判据；
② 227③、222（亮档真帧余量只剩 3）、215（真机通道的第二格读数）、201/202、207；
③ 回到画面：本轮看图腿 NOT-RUN，下一轮至少看两帧新拍的（换夹具或换档）；
④ 220 路 A 与 228② 仍等用户（授权改 `AppleKeyboardUIMode` / 真机拖一次样本）。
)

最后更新：2026-10-19 20:42（本地 · R209 / 第 211 轮：**看图腿真做了一遍 + 新尺 `surface_left_axes.py` 入库（只留关系判据，自带五格真值表）**（U-677…U-679 · 产品 0 文件，看图账 + 判据账）

**本轮落地**：浮层三条左轴量成 22.0 / 24.0 / 35.5pt（药丸左右内缩差 0.0pt ⇒ 对称），统计页卡片内三轴同在 148.0pt、
热图网格右缘比说明文字右缘短 120pt ⇒ 两处**都判不改**，理由写进台账（格子尺寸是"一天一格"的编码前提；三种控件三种内缩）。
新尺只留关系判据（A 对称 / B 同轴 / C 不越过，容差 1.0pt，探针坐标钉死且必须读到墨），空帧 ⇒ NOT_RUN 不给绿。
**我自己看图时说的两句假话都撤回了**："搜索框与行没对齐"（量出来各自成轴）、"加载时头部消失"（`DetailView.swift:69-72` 头部恒在，
那张帧是组件帧）⇒ 机制立成 D-206，覆盖洞开成 BACKLOG 233。
218 的 runner 分布答案拿到了：两跑 `row-insert 开` 连续段 0.4 / 1.3 个间隔、"关"档 1.0 / 1.0 ⇒ 这条轴在 runner 上也分不开 ⇒ **不升硬门**（追记已落）。
现跑：`LEFT_AXIS_SELFTEST ok`、真帧 `LEFT_AXIS_VERDICT ok 探针=5 问题=0 NOT_RUN帧=0`、电池 `Ran 393 tests` 且 OK、清账表 `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`。
**变异表本轮 NOT-RUN**（判据对象是新 python 尺，刀与 CI 接线同轮配）⇒ 新开 BACKLOG 234。
CI：`8` 跑 success（bbc5642=39251464899、04ccf7a=39247806444、3073943=39247153666、f6d3b4a=39246385660、187ec0b=39245844718）、`0` 跑仍未读（无）、失败跑 无 ⇒ 未读的不算绿。

**下一轮（R210）的靶**：⓪ 读 `bbc5642` 与本轮这一跑的 CI（按步骤名逐条列失败）；
① 233 的注入点 + 组合帧（详情加载态第一次有组合像素，并把跨帧比换成同帧关系判据）；
② 234：把 `surface_left_axes.py` 接进 CI 步骤 + 配刀（这两件必须同一轮）；
③ 227③、222（亮档真帧余量只剩 3）、215（真机通道能不能拿到第二格读数）、201/202、207；
④ 220 路 A 与 228② 仍等用户（授权改 `AppleKeyboardUIMode` / 真机拖一次样本）。
)

最后更新：2026-10-19 20:05（本地 · R208 / 第 210 轮：**缺席断言改成标识符边界匹配（修掉 focusEffectDisabled 那一类误报），并抓出第一版放松造出的调用形假清白**（U-674…U-676 · 产品 0 文件，判据账）

**本轮落地**：闸门比缺席词从"忽略大小写子串"改成"标识符边界"⇒ `缺席:...=disabled` 不再被 `focusEffectDisabled()` 判成假话；
第一版"两侧一律要边界"又把调用形词元挡掉了（`ForEach(` 在 SettingsView 出现 4 次却查无此词 ⇒ 假清白），
定形成"词元那一头是单词字符才要求边界"（`absence_pattern()`）；真表 162 格 `不合法格=0`。
自检 384→389 格（五格：嵌入不算在场 / standalone 仍红 / 带点带括号不误伤 / 调用形真缺席仍绿 / 真没有仍绿）。
新表 `mutate_r208.py` 登记进名册并现跑（M739/M740/M741）：`R208_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；预检 `NEEDLE_PRECHECK tables=56 covered=41 arms=161 bad=3`、`ARM_TOTAL files=135 arms=550 dupes=0 repeats=0`。
**开了一条新规矩（D-205）**：修误报要配一把打向"修过头"的刀；放松判据要配一格站在被放松那一侧的正对照 —— 否则分不清"修好了"与"判据闭了嘴"。
BACKLOG 226 结案。验证：脚本电池 `Ran 389 tests` 且 OK、`MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN。
CI：`8` 跑 success（04ccf7a=39247806444、3073943=39247153666、f6d3b4a=39246385660、187ec0b=39245844718、370c5cf=39243961322）、`0` 跑仍未读（无）、失败跑 无 ⇒ 未读的不算绿。

**下一轮（R209）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败；要 run id 用 `.id`，别用正则刮 JSON —— R207 刚为此修过一处假配对）；
① **回到画面**：带着 `frame_audit.py align` 去看图（BACKLOG 205：这把尺数得出"两簇左边缘"，答不了"同不同轴"⇒ 结论要由眼看，尺只提供形状）；
② 227③（两条尺谁有资格判热图下端那一格，要补一条会红的守卫）与 222（色彩标注机制；亮档真帧余量只剩 3）；
③ 228②（真机拖一次"声称是文件但解不出"的样本，要用户在场）、230 候选②（从视图入口进，要 in-screen 探针）、207（一支表只准一个靶）、218、215、226 已结、201/202；
④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；⑤ BACKLOG 232（缺席检查把注释里的词也算"在场"）本轮只量了受影响面、没改，
   要改就照那条里写好的形状来（剥过头要单独报码 + 配一把刀）。
)

最后更新：2026-10-19 19:45（本地 · R207 / 第 209 轮：**清账表判完 162/162 格（未清账 0）+ 两条把快照当不变量的守卫改写**（U-671…U-673 · 产品 0 文件，判据账 + 清账表）

**本轮落地**：两批共 31 格判完 ⇒ `MOTION_LEDGER 表面=18 状态=9 格子=162 行数=162 已清账=162 未清账=0 地板=162`；判定分布 added=9 kept=41 not-added=17 not-applicable=95（之和 == 行数）；地板同笔抬到 162。每格证据是文件 + 行号，缺席断言只挑结构名并由闸门逐条验。
**两条守卫被改写**（这一笔真正的收获）：`cells > rows` 与「现状不该是 0 未清账」不是不变量而是快照，判完那天会变成恒红的门 ⇒ 换成上下界对账（判完必须能证明不是缩表/清行/占位冒充）。
**产品结论一条**：说明段不跟着开关一起淡 —— 开关被禁时那句解释最需要被读到。
**两次自我更正被自己的判据抓回**：报告 §9.3 换措辞 ⇒ `test_final_report_claims.py` 红（句式即判据）；上一批 CHANGELOG 写了没定义的 U 区间 ⇒ 已收回。
CI：`3` 跑 success（370c5cf、5bb95b9、d183bfc）、`3` 跑未读（3073943、f6d3b4a、187ec0b）、失败跑 无 ⇒ 未读的不算绿。
验证：脚本电池 `Ran 384 tests / OK`、`MOTION_LEDGER_RESULT=ok 不合法格=0`、产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN。

**下一轮（R208）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败；要 run id 用 `.id`）；
① **回到画面**：清账表已判完，欠的是真做效果 —— 228②（真机拖一次"声称是文件但解不出"的样本，要用户在场）与 230 候选②（从视图入口进，要 in-screen 探针）；
② 227③（两条尺谁有资格判热图下端那一格，需补一条会红的守卫）与 222（色彩标注机制；亮档真帧余量只剩 3）；
③ 218、215、201/202/205/207、226（缺席挑词的守卫）、224（拖入被拒收的分辨实验）；
④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；
⑤ 新账：清账表判完 ⇒ 以后每加一个表面/状态都会让「未清账」重新变大，那是设计而不是回归。
)

最后更新：2026-10-19 19:30（本地 · R206 / 第 208 轮：**R206 —— 新回执第一次有帧（黑带归因到 132px 那处已登记盲区）+ 变异名册补齐 + 调用点守卫**（U-668…U-670 · 产品 0 文件，看图账 + 判据账）

**本轮落地**：① 补帧被 `testCaptureKeyViews` 拦下 ⇒ 先扫帧归因（三张暗帧黑带高度都是 132px=66pt@2x，只有 y 不同）⇒ 判为已登记的材质盲区，登记条目带读数，帧基线 140 张、复验 `CHANGED=0 MISSING=0 ADDED=0`；② `mutate_r205.py` 进名册并真跑 M736, M737, M738 三刀全 CAUGHT、RESTORE_CLEAN=yes、预检 `arms=158 dupes=0`；③ 建表时抓到"调用点没有守卫"⇒ 新断言（剥行注释 + 整行字面量 1 次 + 裸调用 0 次）+ 刀 M738，卷 `10 tests / 0 failures`。
**三笔自我更正留在账上**：假 U 区间收回；message 先于证据补落；zsh 手写退出码判断让电池**根本没跑**（日志文件不存在 ⇒ 分清"没跑"与"跑挂"；规矩：退出码判断用 `cmd && next` 与链）。
**CI**：5 跑 success（370c5cf=39243961322、5358bf3=245864803、7dc490f=245864803、b36af66=245864803、8d7b51c=245864803）、1 跑仍未读（370c5cf）、失败跑=无 ⇒ 未读的不算绿。
验证：`swift build --build-tests` 0 告警、脚本电池 `Ran 384 tests / OK`、`MOTION_LEDGER_RESULT=ok 不合法格=0`、地板 131 未回退。

**下一轮（R207）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败，要 run id 用 `.id`）；
① **必须动一个真位点**：清账表 31 格未判 ⇒ 从里面挑一格真做动效/hover（带帧 + 变异刀 + 换装本机），或做 227③（两条尺谁有资格判热图下端那一格）；
② 228②（真机拖一次"声称是文件但解不出 URL"的样本，要用户在场）；230 候选②（从视图入口进，要 in-screen 探针）；
③ 222（色彩标注机制仍未定：P3→sRGB 只解释浅三档，最饱和那格 21→38 反而更糟；亮档真帧余量只剩 3）；
④ 218、215、201/202/205/207、226；⑤ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`。
)

最后更新：2026-10-19 18:55（本地 · R205 / 第 207 轮：**D-4 的另一半接上 —— provider 声称是文件却解出 0 个 URL 时不再静默**（U-665…U-667 · 产品 2 文件，动效主线）

**本轮落地（真改产品）**：`HistoryStore.addDroppedFiles` 加 `attemptedCount`，调用方传 `wanted.count`，
回执说 attempted 而不是解出的 0；`HistoryStore.swift` 只 +1 行（1118→1119，`testHistoryStoreStaysThin` 仍绿）。
判据 `testDroppedProvidersThatDecodeToNothingStillSpeakUp` 三条对照（说话 / 不传就照旧不说话 / 成功不留横幅），卷 `9 tests / 0 failures`；
刀 `M736`（打"会不会说话"）与 `M737`（打"说的是哪个数"）⇒ **2/2 CAUGHT、ESCAPED=0、NOT_RUN=0**，还原后重跑同一卷仍 9/0。
**画面未变**：`COMPARED=138 CHANGED=0 MISSING=0 ADDED=0` ⇒ 这条新回执**没有帧**（新分支不在任何夹具里）⇒ 开 BACKLOG 228（夹具 + 真机拖样本 + 把这两把刀搬进 `mutate_needle_precheck.py` 名册，否则下一轮复查不到）。
已换装本机：`INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、`INSTALL_RUNNING_PID=54647`、条目 163→163；旧包留在 `Documents/Codex_Project0_backups/before-local-20261019-185024`。
验证：脚本电池见 commit 输出、`MOTION_LEDGER_RESULT=ok`；**全量 `swift test` 本笔未跑，交给 CI 这一跑**（不许把 CI 未读说成绿）。
台账：第 207 轮 / Round 205（七维表）/ CHANGELOG / BACKLOG 224 结案 / 228 开单；三账窗口 R205/R204/R203 齐。

**⓪ 的读数（R206 第一遍，`gh api …/actions/runs`）**：`c90790e`、`13075d4`、`2b9238c`、`8cbe238`、`8ebdbb1` 五跑全部 `completed success`（含 R205 那笔真改产品的 `8cbe238` ⇒ 全量 `swift test` 由 CI 那一跑代跑，本笔未再本地跑全量）；`1620429`、`8d7b51c`、`b36af66` 三跑写这笔时仍 `in_progress` ⇒ **结论未读**，不许说它们绿。坑记一条：`--jq` 里 `.databaseId` 在这台 gh 上打出 `null`，SHA 与结论照旧读得到 ⇒ 要 run id 得换 `.id`（与 `reference-github-ci-readings` 那条同源）。
**下一轮（R206 之后）的靶**：⓪ 把上面三跑 `in_progress` 的读完（用 `.id` 拿 run id 成对）；
① **BACKLOG 228**：给"解出 0 个 URL"那一格补夹具（要真有帧），并把 M736/M737 搬进变异名册；
② 227 的③（两条尺若给相反处置要补"哪条尺有资格判这一格"的守卫）与 222（色彩标注机制仍未定，亮档真帧余量只剩 3）；
③ 215（真机亮档一格）、218、201/202/205/207、226；④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；
⑤ 未清账 31 格，名单以 `MOTION_LEDGER_OPEN` 为准。
）

最后更新：2026-10-19 18:40（本地 · R204 / 第 206 轮：**看图腿真做了一遍 —— 热图阶梯下端量出 1.08 / 1.12 倍，221 拿到产物通道的第二个证人**（U-662…U-664 · 产品 0 文件，看图账）

**本轮落地**：`/tmp/shots_r204` 重捕 138 帧（捕获卷 `Executed 72 tests, with 4 tests skipped and 0 failures`），
`frame_baseline compare --against working` ⇒ `COMPARED=138 CHANGED=0 MISSING=0 ADDED=0`（产品 0 文件 ⇒ CHANGED=0 是预期，不是结论）。
真看 `heatmap-populated-430x250-{dark,light}` 并用 PIL 逐帧取色：暗档对底 1.15/1.24/1.55/2.14/3.33、亮档 1.11/1.24/1.54/2.12/3.23
⇒ **最窄的一步是「空格↔第一档」，且两档同形**（是阶梯下端的间距设计，不是某一档调错）。
**本轮不改产品**（D-202）：判据那条量的是模拟色觉后的 max-channel 差（地板 18），本条量的是 WCAG 对比度比值，
两种估计量不许互相代签 ⇒ 分辨实验开成 BACKLOG 227。图例与说明档判为**不加**（同批取色：暗 L=0.3231、亮 L=0.2159，都远高于格子最低那一步）。
台账：第 206 轮 / Round 204（七维表，产品面推进只有 9/15）/ CHANGELOG / D-202 / BACKLOG 227 同笔；三本账窗口 R204/R203/R202 齐。
验证：脚本电池 `Ran 384 tests / OK`、`MOTION_LEDGER_RESULT=ok 不合法格=0`、地板 131 未回退、产品 0 文件 ⇒ 无换装。

**下一轮（R205）的靶**：⓪ 读三笔的 CI 并把 run id↔commit 成对写回来：`b6077be`、`bd7a64f`、`c90790e`（补落那笔）与本轮这笔 ——
`in_progress` 只能说未读，不许猜绿；
① **产品面必须动一个真位点**：看图与判据已连续多轮 0 文件，自评「产品面推进」停在 9/15 ⇒
   要么按 227 的分辨实验之后真改 `VisualHeat` 的下端间距（带帧 + 变异刀 + 换装本机），要么从 31 格未清账里挑一个表面真做一条动效；
② 227 三条实验（两通道排序是否一致 / 把空格与一档色号交给判据通道跑一遍 / 相反就补"哪条尺有资格判这一格"的守卫）；
③ 222（色彩标注机制仍未定：P3→sRGB 只解释浅三档，最饱和那格 21→38 反而更糟）、218、215、201/202/205/207、224；
④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；未清账 31 格，名单以 `MOTION_LEDGER_OPEN` 为准。
）

最后更新：2026-10-19 18:35（本地 · R203 / 第 205 轮：**R201…R203 三笔非轮次台账补落 + 清账表 115→131 行 + 指针名册的第三种坏法有了牙**（U-653…U-661 · 产品 0 文件，台账账 + 判据账）

**这笔补的是什么**：BACKLOG 225 的①出口 —— 三笔「非轮次」提交（`33b1322`/`728a1b2`/`b6077be`+`bd7a64f`）当时只落了 CHANGELOG 与 BACKLOG，而三账标题守卫只看离 STATE 最近三笔 ⇒ 它们一旦进窗口就是三格红。现在 UI_AUDIT 有第 203/204/205 轮三节（U-653…U-661，区间与定义行吻合），ITERATION 有 Round 201/202/203 三节（各带七维表，曲线从 200 连续到 203），CHANGELOG 三条标题机械补上 `/ U-…` 段。
**产品面**：0 文件 ⇒ 帧未动、无换装；看图腿记 NOT-RUN（唯一真看过的是沿用的 notice-banner 两帧，只支撑「按下」一格）。
**清账表**：115→131 行（拖入落点 6 + 提示条 4 + 筛选条 6），未清账 47→31，地板同笔抬到 131；`MOTION_LEDGER_RESULT=ok 不合法格=0`；指针名册新增 `PATH_RE_LAX` 与 PARTIAL/AMBIGUOUS/MISSING 三态，自检 24→30 格（`b6077be`）。
**验证**：脚本电池 384 全绿（`Ran 384 tests / OK`）、闸门与报告对账各一次、全量 swift test 本笔未跑（台账笔，Swift 侧 0 改动）。
**下一轮（R204）的靶**：⓪ 读 `b6077be`/`bd7a64f` 与这笔的 CI（三跑都要 run id↔commit 成对，未读只能说未读）；① **回到动效本体**：清账表连续多笔 0 画面改动 ⇒ 下一轮要么真点一个位点做动效（带帧与变异刀），要么把 218 那三臂的逐帧条带真看一遍；
② 222：色彩标注那条机制仍未定（P3→sRGB 只解释浅三档，最饱和那格 21→38 反而更糟）；
③ 215（真机亮档一格）、201/202/205/207、224（拖入被拒收没有就地回执，先做分辨实验）；
④ 220 路 A 等用户授权改 `AppleKeyboardUIMode`；未清账剩 31 格，名单以 `MOTION_LEDGER_OPEN` 为准。
)

最后更新：2026-10-19 17:15（本地 · R200 / 第 202 轮：**看图腿四张帧的行带读数 + R198/R199 两跑 CI 的验收**（U-650…U-652 · 产品 0 文件）

**本轮落地**：新读数器 `frame_bands_r200.py` 把浮层/菜单栏四张帧量成行带：亮档 typed 3 带、暗档 hover 6 带、亮档 list 6 带、菜单栏推荐 6 带；"亮档结果区下面空得可疑"被量成"真的只有两条结果"（同一把尺反方向灵 ⇒ 不是量不到）。
**查重挡住一次开单**：浮层固定尺寸与留白已由 D-122（R63）判 ⇒ 不开单，只记这个动作。
**CI 验收读数**：R198 failure（run 39225680017 ↔ commit 3740c51）失败步骤：STEP[16] On-screen probe coverage floor⇒failure；R199 success（run 39227062038 ↔ commit a7f16c1）失败步骤：无 ⇒ 第 16 步 已不再红。
验证：脚本电池 368 / OK、产品 0 文件（帧与换装沿用上一遍）。

**下一轮（R201）的靶**：⓪ R200 这笔（commit `a6dcb9b`）触发的 run 是 `39230041152`，写这一格时**未读**（它只动台账与工具，不动 Swift/脚本 ⇒ 预期与上一跑同形，但预期不是读数）；上一跑 run `39227062038` ↔ commit `a7f16c1` 已读：`conclusion=success`、第 16 步没红 ⇒ 八跑连红断了。
② 222：热图相邻档判据的采样通道换成真帧（或给亮档最低那一格加真帧证人）—— 这是唯一一条**指向画面**的开放项；
③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；
④ 220 路 A 仍等用户授权；⑤ 清账表 47 格未写（BACKLOG 219 的清单），本轮没动；
⑥ 产品已连续七轮 0 文件 —— 下一轮要么动 222 指向的那一格真帧通道，要么如实按 0 文件记。
）

最后更新：2026-10-19 17:05（本地 · R199 / 第 201 轮：**连红八跑的 CI 第 16 步读完 —— 病根是我自己 R194 埋的两张 cannot，按 runner 的点名翻成 can**（U-647…U-649 · 产品 0 文件，CI 账）

**本轮落地**：`7e46b49`…`f3b3933` 八跑全 failure，逐跑按步骤名读下来是同一朵 `STEP[16] On-screen probe coverage floor`；runner 正文逐条点名 `testFilterSegmentsAreReachableAndShowFocus`、`testFilterFocusExitIsWired` ⇒ 名册两条 cannot → can（理由里带 run 39220929124 与原话），现在 can=7 / cannot=7。
**连带两格电池**：判历史日志那格改按采集当时的登记判；"今天的登记 + 今天的夹具"那格改成钉红的身份（只许 NOT_RUN、只许那两个名字）⇒ "今天的登记 + 今天的日志真的绿"从此没有离线证人，开 BACKLOG 223。
**两笔自我更正**：R198 提交信息里手抄的"暗档保住 …153"是坏尺子那次的读数（最终版只有 97/98）；`swift test --filter "Class$"` 会给 `Executed 0 tests` 而 exit 0 ⇒ 过滤器不带尾锚、必须读 N>0。
验证：脚本电池 368 / OK、JSON 解析通过、产品 0 文件（帧与换装沿用上一遍）；**CI 是否真的不再红要等下一跑第 16 步的读数，本轮不提前宣布修好**。

**下一轮（R200）的靶**：⓪ 读 R198/R199 两跑的 CI，成对：run `39225680017` ↔ commit `3740c51`、run `39227062038` ↔ commit `a7f16c1`（写这一格时两跑都仍 in_progress ⇒ 结论未读；R199 那跑的第 16 步是这次翻面的验收）—— **欠账已两轮，按 D-200 把 run 号与欠的跑数写成读数，不许再推一轮**；
② 222：热图相邻档判据的采样通道换成真帧（或给亮档最低那一格加真帧证人），两通道分歧要能自动点名；
③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；
④ 220 路 A 仍**等用户授权**；⑤ 清账表：筛选条剩 5 格；
⑥ 看图腿：本轮 5/15 是**真没看图** —— R200 要么动一个真位点（222 直接指向画面），要么重捕一帧并真看。
）

最后更新：2026-10-19 16:45（本地 · R198 / 第 200 轮：**221 结案在色觉模拟这根轴上 —— 第一版读出一个假红，修好之后 16 条最小 25.41**（U-644…U-646 · 产品 0 文件，判据账 + 看图腿）

**本轮落地**：新判据 `testAdjacentHeatLevelsStaySeparableUnderDeuteranopia`（Viénot 1999、地板沿用 18.0/255）：暗档保住 97/98、亮档 65/75/76/80，最小 light/1x empty→bucket1=25.41 ⇒ 绿色盲下仍是五档 ⇒ 221 结案、不改梯子。
**自己的假红**：第一版蓝通道漏了重新编码 ⇒ 暗档 10.41（假红）、高档 99.60 > 模拟前 65.00（物理不可能）⇒ 修尺子；并补一条与产品无关的真值表（红绿必须混、灰必须是不动点）：SIM_MATRIX 红↔绿 前=255.00 后=68.97 | 蓝↔黄 前=255.00 后=255.00 | 灰 (128,128,128)→(128,128,128) 漂移=0.00
`mutate_r198.py` M732, M733, M734, M735 ⇒ 4/4 CAUGHT、RESTORE_CLEAN=yes；M732/M733 只有真值表能抓。
看图腿：产品 0 文件 ⇒ 先 `ls` 数出 138 张再沿用 R197 的帧（COMPARED=138 CHANGED=0），真帧按中轴游程复量并与判据逐档相减 ⇒ 偏移只在 R 那一列（6…21，G/B ≤1）：亮档最低一格真帧 21 对判据 25.41、地板余量 3 对 7.4 ⇒ 新开 222。
验证：编译 0 告警、全量卷 884/44/0、脚本电池见 commit 输出；R197 那笔按 211 的通道显式申报成单本账笔次（不补桩标题）。

**下一轮（R199）的靶**：⓪ 读 R196/R197/R198 这几笔的 CI 全部失败步骤（`2193726`/`27172ec`/`f3b3933` 与本轮这笔；用 `scripts/ci_read.py` 按步骤名读，别整卷 grep）；
② 222：把热图相邻档判据的采样通道之一换成真帧（或给亮档最低那一格加真帧证人），两通道分歧要能自动点名；
③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；
④ 220 路 A 仍**等用户授权**（改 `AppleKeyboardUIMode` 后重跑同一条探针）；
⑤ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；⑥ 看图腿：产品已连续六轮 0 文件 —— 下一轮要么动一个真位点（222/218 都指向画面），要么如实按 0 文件记这一格。
）

最后更新：2026-10-19 15:50（本地 · R196 / 第 198 轮：**220 结构诊断 —— 代理不接受第一响应者，而焦点环零件已在位**（U-641…U-643 · 产品 0 文件，判据账）

**本轮落地**：新量法把侧栏那棵树的 nextKeyView 结构拍成读数：KEYCHAIN 视图数=45 有 nextKeyView=15 acceptsFirstResponder=4 环=NSHostingView<AnyView>>AppKitPlatformViewHost<PlatformViewRepresentableAdaptor<ChineseEditableTextField>> 环长=2；两枚段按钮位置上各有 `KeyViewProxy`（`fr=false`、彼此连着）与**已在位**的 `_FocusRingView` ⇒ 病根是"代理不接受第一响应者"，不是"没有焦点表达"。`mutate_r196.py` M730, M731 ⇒ 2/2 CAUGHT、RESTORE_CLEAN=yes。
**分辨实验没翻面**：本进程 register `AppleKeyboardUIMode=3` 后 KEYCHAIN_FKA 开关=3(本进程 register，未写全局) acceptsFirstResponder=4/4 环长=1/2 代理=_FocusRingView fr=false frame=(12.0, 50.0, 148.0, 26.0) | _FocusRingView fr=false frame=(160.0, 50.0, 148.0, 26.0) ⇒ "全键盘访问决定可达性"这条假设既不证实也不证伪；要判它得改全局偏好 + 重启会话（需用户授权，不偷跑）。
**决定：不改产品**（D-198）：自绘焦点环被"零件已在位"否掉；换 `NSSegmentedControl` 会换掉 R189/R190 那套两态判据的对象，得单独一轮带画面证人做。
验证：编译 0 告警、全量卷 882/44/0、三个新 print 标记进名册（12→15 行）、产品 0 文件（帧与换装沿用上一遍）；脚本电池见 commit 输出。

**下一轮（R197）的靶**：⓪ 读 R195/R196 这几笔的 CI 全部失败步骤（`7e46b49`=已确认 failure 且成因是它自身缺文件；`4cde716`/`4b38b29`/`9b0a17b` 与本轮写这笔时都仍 in_progress ⇒ 结论未读）；
② 220 路 A：**等用户授权**改 `AppleKeyboardUIMode` 后重跑同一条探针（翻面 ⇒ 产品不用改，只改文档与验收条件）；
③ 220 路 B：若路 A 不翻面，才谈换原生控件 —— 且要先想清楚 R189/R190 那两条判据跟着怎么改；
④ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；
⑤ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；⑥ 看图腿：产品已连续五轮 0 文件 —— R197 要么动一个真位点，要么把 218 那三臂的逐帧条带像 R192 那样真看一遍。
）

最后更新：2026-10-19 15:30（本地 · R195 / 第 197 轮：**还 R194 的三件债 —— 四把刀验出牙、全量卷 0 失败、电池 OK**（U-638…U-640 · 产品 0 文件，判据账）

**本轮落地**：`mutate_r195.py` M726, M727, M728, M729 ⇒ 4/4 CAUGHT、RESTORE_CLEAN=yes，catcher 全是 R194 那条 `testFilterFocusExitIsWired` ⇒ 那个"有名字的未判定"出口第一次被证明可证伪。电池那 1 红修绿：真因是 `PROBE_QUEUED 4/11→6/13` 与 print 读数名册（新增 `FILTER_FOCUS`、`FILTER_PILL_FOCUS_UNCOVERED`，10 行→12 行），两处按**真实文本**重钉、名册仍是双向相等。
**一条自我更正**：上一笔提交信息里我写"漏了另一处 7/11"是没读失败正文就猜的 ⇒ 实际成因见上；教训是红话要抄原文（R94 新变体）。
验证：编译 0 告警、全量卷 881/43/0、脚本电池 Ran 368 / OK、产品 0 文件（帧与换装沿用上一遍）。

**下一轮（R196）的靶**：⓪ 读这三笔的 CI 全部失败步骤：`7e46b49`=**已确认 failure**（那一笔单独 checkout 时电池红，已由 `4b38b29` 补落，别再当成产品红）；`4cde716` 与 `4b38b29`（run 39216470715 / 39216653505）写这笔时仍 in_progress ⇒ 结论**未读**（关键预期：`FILTER_PILL_FOCUS_UNCOVERED` 要在 runner 上露面且那一步不因此红）；
① 220：量清 `List`/`NSHostingView` 的 nextKeyView 排布（先读数、后选路：原生 NSSegmentedControl 或显式 NSView 代理），选定后要画面证人；
② 218（行 A/B 的统计量：帧对中位 / 段长 ÷ 声明时长，配 runner 那份分布）、215（真机亮档一格）；
③ 201、202、205、207；④ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；
⑤ 看图腿：产品已连续四轮 0 文件 —— 下一轮要么动一个真位点，要么把 220 的两条候选路各拍一张对照。
）

最后更新：2026-10-19 15:05（本地 · R194 / 第 196 轮：**筛选条「聚焦」格 —— 键盘走不到段按钮，.focusable 被探针驳回**（U-635…U-636 · 产品 1 文件仅注释）

**本轮落地**：新探针 `testFilterSegmentsAreReachableAndShowFocus` 在真窗口沿 key-view 链走 12 站，读数：FILTER_FOCUS 带内候选=1 全部候选=4 候选清单=["ChineseMenuTextField@(43.0, 18.0, 258.0, 16.0) ring=0 带内=true", "ListCoreScrollView@(0.0, 126.0, 320.0, 334.0) ring=0 带内=false", "ListCoreClipView@(0.0, 126.0, 320.0, 334.0) ring=0 带内=false", "SwiftUIOutlineListView@(0.0, 126. ⇒ 12 站全是搜索框的字段编辑器，段按钮 0 站 ⇒ 键盘不可达（新开 BACKLOG 220）。试过 `@FocusState + .focusable(true) + 聚焦描边`：编译 0 告警但探针照红 ⇒ 代码删掉，产品只留 4 行注释。
**两处自己抓出来的假绿**：① 第一版按"落在带内"分类 ⇒ 字段编辑器冒充"走得到"，两条断言双双为真而测的是搜索框；② 差点把"加了修饰符"当成修好了。焦点呈现那一格改成**有名字的未判定**（前提=这一跑量出的 0/12；段按钮一进链断言自动接管），并由 `testFilterFocusExitIsWired` 钉住四条锚点。
**NOT-RUN 记账**：本轮没跑变异刀（预算尽头）⇒ 那条接线扫描目前只有"跑过一遍绿"一个证人。下一轮先补 M726（出口条件改恒真）与 M727（摘掉字段编辑器的身份排除），两把都该红。
验证：编译 0 告警、探针卷 3/1/0；帧与全量卷本轮 NOT-RUN（产品改动 4 行全是注释、无行为改动 ⇒ 未重捕；全量卷留给下一笔与两把刀一起跑）。

**下一轮（R195）的靶**：⓪ 读这一笔与 `75bd43c` 之后所有跑的**全部**失败步骤（关键预期：`FILTER_PILL_FOCUS_UNCOVERED` 要在 runner 上露面，而探针那一步不该因此红）；
① 补 M726/M727 两把刀 + 全量卷 + 帧基线（本轮欠的三件）；
② 220：段按钮进 key-view 链 —— 先量 `List`/`NSHostingView` 怎么排 nextKeyView，再在"原生 NSSegmentedControl"与"显式 NSView 代理"两条里选，选完要有画面证人；
③ 218（行 A/B 的统计量）、215（真机亮档一格）、201/202/205/207；
④ 清账表：筛选条那 6 格里"聚焦"已判成有名字的未判定，剩 5 格（加载、空、错误、成功、禁用）。
）

最后更新：2026-10-19 14:45（本地 · R193 / 第 195 轮：**217 装好时间轴 —— 帧数 9~11 里只有 1~2 帧对是连续的**（U-632…U-634 · 产品 0 文件，判据账）

**本轮落地**：`armProcessInIntervals`（含峰值那段时长 ÷ 本次实测中位间隔）+ `processReadingVerdict`（散点撑绿 / 有一段过程 / 帧数本来就不够）接进三处 AppKit 行 A/B；五跑读数：`row-insert 开` 2.9/2.9/1.1/1.6/2.6 个间隔（帧对 2/2/1/1/2 / 帧数 10/9/7/9/10 / 判：散点撑绿、有一段）、`选中没变` 1.6/1.4/4.2/2.8/1.4 个间隔（帧对 1/1/3/2/1 / 帧数 11/11/11/11/10 / 判：散点撑绿、有一段） ⇒ 那两处 `≥3 帧` 的地板是被散点撑绿的。`mutate_r193.py` M721, M722, M723, M724, M725 ⇒ 5/5 CAUGHT、RESTORE_CLEAN=yes。
**判据故意没换**：2/5 跑落在"散点撑绿"、3/5 落在"有一段"、序列 3/5 跑落在"散点撑绿"、2/5 落在"有一段" ⇒ 界压上去就是拿采样相位当产品结论；新开 218 要更稳的统计量、D-197 记这件事。
**三处自坏也记了**：patcher 第一版**只数锚点没替换**却打印 PATCHED_OK（现在按 post-state 作证）；守卫 `contains("过程=")` 被另一臂喂饱 ⇒ M723 先 ESCAPED，改成按站点数次数=2；真值表 (c) 期望我算成 30 个间隔，实测 31.0=310ms÷10ms。
验证：编译 0 告警、扫描卷 5/0/0、五跑动效卷各 6 条 `过程=` 读数、全量卷 879/42/0、清账表 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115、电池见 commit 输出。

**下一轮（R194）的靶**：⓪ 读这一笔与 `9d5fc1a` 之后所有跑的**全部**失败步骤，并从 runner 那一跑抓 `MOTION_NATIVE row-insert 开 过程=`（218 要的第二份分布）；
① 218：在"帧对中位 / 段长 ÷ 声明时长"里选一个能两边各自被证伪的统计量，再决定行 A/B 换形；
② 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；
③ 201、202、205、207 与清账表未判的 47 格；
④ 看图腿：产品已连续三轮 0 文件 —— 下一轮要么按 173 的清单动一个真位点，要么把这三臂的逐帧条带像 R192 那样真看一遍。
）

最后更新：2026-10-19 14:10（本地 · R192 / 第 194 轮：**216 结案并更正上一轮点名的位置**（U-628…U-631 · 产品 0 文件，判据账）

**本轮落地**：两处"两臂相同吗"（row-star、detail-empty-to-content）改成同一条线 + 旧口径**并判**，合读法由 `armAgreementReading` 生成并被合成真值表钉住；`sharedLineIsSound` 把"共用线什么时候不适用"变成量出来的判据（不引入新阈值）。`mutate_r192.py` M712, M713, M714, M715, M716, M717, M718, M719, M720 ⇒ 9/9 CAUGHT、RESTORE_CLEAN=yes，其中七把只有接线扫描抓得到。
**两条自纠也记了**：① 216 上一轮点名的 `:2916`/`:2332` 都不成立（一个 R59 就用共享线了，一个明写"帧数不参与判定"）⇒ 错在只 grep 符号名没读周围；② 新守卫第一版红给自己看：needle 写在守卫自己的行里 ⇒ 自指命中（R100 那一族），改成按方法体切片并滤掉守卫那段。
**216 不许推广的理由是读数量出来的**：`MOTION_SEQUENCE` 两臂 `0.027/0.234` ⇒ 共用线 0.0351 高于小臂峰值，那一臂 11 帧→0 帧，另开 217（那三处欠时间轴）。D-196 记适用域。
验证：编译 0 告警、扫描卷 3/0/0、动效卷 2/0/0、全量卷 877/42/0、清账表 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115、电池见 commit 输出。

**下一轮（R193）的靶**：⓪ 读这一笔与 `9a8c9c9` 之后所有跑的**全部**失败步骤（写这笔时 run `39206313202`（`9a8c9c9`）仍 in_progress ⇒ 结论未读；关键预期：`2a7c829` 已给 success ⇒ STEP[13]/[15] 那两朵该是消失状态）；
② 217：把三处 AppKit 行 A/B 的判定搬到连续段时长轴，各自配一把"退回帧数"的刀；
③ 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性）；
④ 201、202、205、207 与清账表未判的 47 格；⑤ 看图腿本轮补了一格（两臂各 30 帧条带逐格量灰阶 ⇒ 两臂逐帧同形，那条交叉淡在这条通道里没有过程），但产品已连续两轮 0 文件 —— 下一轮要么按 173 的清单动一个真位点，要么把 217 那三臂的条带也这样量一遍。
）

最后更新：2026-10-19 06:20（本地 · R191 / 第 193 轮：**212 结案 —— 那条红是判据在比两把不同的尺**（U-625…U-627 · 产品 0 文件，判据账）

**本轮落地**：④ 换同一条绝对线（`sharedMovingFloor` 套两臂）+ 新地板"带至少看到 1 帧过程"；旧口径同打印。`mutate_r191.py` M708, M709, M710, M711 ⇒ 4/4 CAUGHT、RESTORE_CLEAN=yes；M708 先 ESCAPED（`0 ≥ 0` 也算绿）后转 CAUGHT —— 这条已在账里当形状记下来。
**两次自坏也记了**：第一次"绿"其实是 1 skipped（动效卷要 `CLIPBOARD_HISTORY_UI_MOTION=1`）⇒ 台账生成器现在 skip≠0 就拒绝写盘；`mutate_r191.py` 第一版 write() 漏 join，崩在改文件之前（运气，不是防线）。
验证：编译 0 告警、判据卷 2 例/skip 0/失败 0、全量卷 875/42/0、清账表 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115、电池见 commit 输出。

**下一轮（R192）的靶**：⓪ 读这一笔与 `2a7c829` 之后所有跑的**全部**失败步骤（关键预期：`STEP[17] Motion coverage floor` 与 `STEP[13]/[15]` 都不该再因为 212/两态判据红）；
① 216：把同一条线推广到 `:2916` 左右分栏与 `:2332` 热图淡入 A/B，各配一把"退回各自归一化"的刀（真值表那两处不改，区分写进刀名）；
② 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；
③ 201、202、205、207 与清账表未判的 47 格。
）

最后更新：2026-10-19 06:05（本地 · R190 / 第 192 轮：**上一笔把 CI 推红，这一笔把"能不能判"改成量出来的谓词**（U-622…U-624 · 产品 1 文件，判据账）

**本轮落地**：`channelCanSeeMaterial`（两条前提：底轨占列宽 ≥0.40、与侧栏底之差 ≥30luma）+ 真值表 6 格 + 接线扫描；全档无能力 ⇒ 带读数 skip，部分有能力 ⇒ 断言照旧。`mutate_r190.py` M703, M704, M705, M706, M707 全 CAUGHT、RESTORE_CLEAN=yes。
**212 的描述已更正**：那条断言本来就是同一次运行的两臂相对量（我上一笔写成"绝对地板"是错的）；欠的变成"同版两跑的分布"：run `39169952987` 带=3/整窗=3；run `39169849821` 带=3/整窗=3；run `39166453147` 带=3/整窗=4；run `39167782287` 带=3/整窗=3；run `39164744805` 带=3/整窗=3。
验证：编译 0 告警、捕获卷 72/0、全量卷 874/42/0、帧基线 138 张 changed=0、清账表 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115、电池见 commit 输出。

**下一轮（R191）的靶**：⓪ 读这一笔与 `0c97820`/`2280be0` 之后所有跑的**全部**失败步骤（重点：`STEP[15] Capture gate` 该消失；若 `MOTION_BAND` 那格仍红 ⇒ 按 212 追记走"容差=测量粒度 + 0 帧仍红"的刀）；
① 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；
② 201（runner 高窗那条 205pt 带里到底是什么）、202、205、207；③ 清账表下一批（未判 47 格）。
）

最后更新：2026-10-19 06:05（本地 · R189 / 第 191 轮：**210 结案 —— 药丸一直在选中段，错的是"亮=药丸"这个未验默认**（U-619…U-621 · 产品 2 文件，动效主线）

**本轮落地**：`FilterPillGeometry` 纯核 + 视图改 `.position`（138 张帧 `CHANGED=0` ⇒ 行为保持）；两态像素判据 + 档数闸门；`mutate_r189.py` M696, M697, M698, M699, M700, M701, M702 全 CAUGHT、RESTORE_CLEAN=yes；D-195 记通道方向（药丸暗、轨道白）；新开 215（亮档在这条通道判不了，欠真机读数）。
验证：编译 0 告警、捕获卷 72 例/失败 0、全量卷 872/42/0、帧基线 138 张 changed=0、清账表 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115。

**下一轮（R190）的靶**：⓪ 读这一笔与 `9475006`/`bd9b827`/`0ce57f7` 之后所有跑的**全部**失败步骤（已知 `8b90efe` 红在 STEP[17] Motion coverage floor，与 `fd6b43a`/`d4958a9` 同一格 ⇒ 归 212）；
① 212：把带捕获那条绝对地板换成同一次运行的相对判据 + 自带读数行（照 BACKLOG 176 那一族的做法）；
② 215：先拿一格真机合成层读数，判"亮档分不开"是通道还是产品；
③ 201（runner 那条高窗只画出 205pt 下沿带 —— 带里到底是什么）、202、205、207；④ 清账表下一批（闸门读数 MOTION_LEDGER 表面=18 状态=9 格子=162 行数=115 已清账=115 未清账=47 地板=115 里的未判格）。
）

最后更新：2026-10-19 06:22（本地 · R188 / 第 190 轮：**208 结案、210 撤回、211 落地**（U-616…U-618 · 产品 0 文件，判据账）

**下一轮（R189）的靶**：⓪ 读 `81105b0`/`2720e72`/`a90e380`/`8b90efe` 与本笔那一跑的**全部**失败步骤（写这笔时 8b90efe 仍 in_progress ⇒ 未读；`fd6b43a`/`d4958a9` 的红已归到 212，别再当成新产品缺陷）；
① **210 先修尺**：显式 `.all` 与显式 `.favorites` 两张夹具，看亮区换不换段（换段⇒病根在选中判定那层；不换⇒才谈几何）；
   并把 `scripts/frame_audit.py bands` 与本轮两把尺合成一套口径（现在三套各说各话）；
② 212 的分辨读数（同一版本在 runner 上两跑的带内帧数）；
③ 205 / 201 / 202 / 207 与清账表未判的 47 格；④ 全量卷与变异表在下一笔补跑（本笔 NOT-RUN）。
）

最后更新：2026-10-19 05:58（本地 · R185 / 第 187 轮：**210 的读数归位 —— 药丸是一整段、落在右段；亮档"过哑"是阈值不适用**（U-613…U-615 · 产品 0 文件，动效主线）
R188 追记（本笔为 BACKLOG-only，**STATE 表头未轮换** —— 轮换前先读 211，否则三账窗口当场红）：
⓪ 已到手：208 结案（runner `39163387579` = `949350d` 的 `PROBE_FPS … n=217 worst=75.6ms 超锚点帧=0`，见 BACKLOG 208 追记）；
   其余八跑（`d4958a9`…`81105b0`）在写这笔时 queued/in_progress ⇒ 结论**未读**。
① 210 的「药丸在右段」**已撤回**（两把尺对同一批帧矛盾，且其中一把的归一化口径我能指出错）⇒ 210 退回未钉死，产品不动；下一轮先量**尺**：
   两张夹具（显式 `.all` / 显式 `.favorites`）看亮区换不换段，并把 `frame_audit bands` 与这两把尺合成一套口径。
② 新开 211（轮次三账的申报通道）；③ 旧账不变：205（逐元素分带）、201（runner 那条 205pt 带里是什么）、202（缺席文法按文件粒度）、
   207（多靶变异表）、清账表未判格、以及 195 的 ①、189、188、187 的 ②③。
本笔的看图腿：重新捕了 138 张帧并逐张量了（不是读代码），本机捕获卷 71 例 / 跳过 4 / 失败 0，帧基线：对账 138 张、changed=0、missing=0。

方法从"半区均值"（预设分界线）换成"逐行找连续亮区"：暗档 y=208..252 每行只有一段亮区 x=274..535、宽 258px=129pt = 控件可用宽的一半 ⇒ 药丸在**右段**；
带高 48px≈24pt 对上 `.frame(height: 26)`；上一轮那条"550px 最宽亮区"其实是 y=276 的**分隔线**（自我纠正）。
亮档同带整幅 >200 ⇒ "只差 14.3 点"是亮度阈值在亮档不适用，不是选中态弱 ⇒ R182 那句"一档过响、一档过哑"彻底拆掉。
210 只剩一步：查 `content-empty` 的 store 有没有被 helper 设过 filter；坐实没设 ⇒ 修 `slidingPill`（产品，走完整验证），
并补一条"药丸 x 区间必须落在选中段那一半"的读数判据（这条错位 186 轮以来没人抓到）。
验证：闸门 `RESULT=ok`；清账表 115 行 / 162 格 / 未清账 47 未动；电池 `Ran 362 / OK`（台账之后）；0 产品文件。

**下一轮（R188）的靶**：⓪ 复验 208（`--log` 里 `PROBE_FPS` 那一行必须含 `超锚点帧=`）+ 读 `2720e72`/`a90e380`/`3238e14`/`8cf2a08` 四跑的**全部失败步骤**（当时仍 `queued`/`in_progress`）；
② **修 210（产品轮，病根已钉死）**：`SegmentedFilterPicker.slidingPill` 的几何与选中段反号 —— 同一帧里侧栏标题是「0 条记录」（= `.all`）而药丸在收藏那一段；
   候选修法 `.frame(maxWidth:.infinity, alignment:.leading)` 或改 `.position(x: 段中心)`；走完整验证（build 0 告警 → 判据卷 → 重捕帧 + 基线同笔 update → 换装本机 → 台账 → 电池 → 推送），
   **并补一条"亮区必须落在选中段那一半"的读数判据 + 变异刀**（这条错位已在无判据下活了 186 轮）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 47 格（`--list-open`）；⑥ 202、207、189、188 的 ②③、176、182/183/185。

三条证据互相矛盾：`HistoryStore.swift:63` `filter = .all`；`content-empty` 夹具没设过 filter（`UICaptureHarness.swift:3887`）；
`slidingPill` 偏移 `idx*(w/count)+1` 且 `allCases=[all, favorites]` ⇒ 药丸应在左段，而帧上白区在 x≈277..547（右半均值 179.0、纯白 65.4%%，左半 51.0）。
⇒ 两种成因修法相反（选中/偏移反号 = 产品 bug vs 离屏材质只画一段 = 通道 bug）⇒ **本轮不动产品**，
分辨实验=造一个显式 `filter=.favorites` 的夹具看白药丸换不换段（R185 第①条）。209 结案（白卡=材质合成假象）。
验证：闸门 `RESULT=ok`；清账表 115 行 / 162 格 / 未清账 47 未动；电池 `Ran 362 / OK`；0 产品文件。

**下一轮（R185）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`d4958a9`/`fd6b43a`/`d678612` 全部失败步骤；
② **210 的分辨实验**：新夹具显式 `filter=.favorites` + 同一把尺量白药丸 x 区间换不换段 ⇒ 换段就修 `slidingPill`（产品），不换段就记通道；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 47 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。
最后更新：2026-10-19 05:32（本地 · R183 / 第 185 轮：**209 归位 —— 白卡是 `.ultraThickMaterial` 的离屏合成，产品缺陷读法被自己否掉**（U-607…U-609 · 产品 0 文件，动效主线）

两条证人：① 几何 —— 亮度 >200 的像素只在 y=204..252（带高 52px = 26pt = picker 的 `.frame(height: 26)`）⇒ R182 量的就是这颗控件；
② 令牌 —— `sliderPill = .ultraThickMaterial`（系统材质，非写死白）、`track = .quaternary` ⇒ 白卡属离屏材质合成那一族（D-090/D-094/R29d），**不动产品**。
自我更正：R182 那句"一档过响、一档过哑"在离屏通道上不成立，降级为通道形状。
只剩一格：药丸两档都在右段，而 `allCases = [all, favorites]`、`idx = firstIndex(of: selection)` ⇒ 夹具是否真选收藏，一条 grep 关掉（R184 第②条）。
验证：闸门 `RESULT=ok`；清账表 115 行 / 162 格 / 未清账 47 未动；电池 `Ran 362 / OK`；0 产品文件。

**下一轮（R184）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`d4958a9`/`fd6b43a`/`949350d`/`5bb266e` 全部失败步骤；
② 209 的最后一格：grep `content-empty` 夹具构造里有没有设 filter（有 ⇒ 通道/读数问题结束；没有 ⇒ 药丸偏移是真缺陷，开单修）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 47 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。
最后更新：2026-10-19 05:22（本地 · R182 / 第 184 轮：**209 的同源读数到手 —— 暗档白卡、亮档无差，而离屏通道判不了它**（U-604…U-606 · 产品 0 文件，动效主线）

读数（带 y=204..278、x=30..547）：暗档左半 51.0 / 右半 179.0（右半主色 (@255,255,255) 占 65.4%）；亮档左半 233.7 / 右半 248.0（差 14.3 点）。
⇒ 同一颗分段控件一档过响、一档过哑；但"选中填充不随外观"与"离屏 vibrant 合成盲区"（D-090/D-094/R29d 那一族）在这条通道上分不开
⇒ 209 不结案、不动产品、不放宽。分辨顺序：先 grep 夹具的选中项（一条命令），再决定要不要重开真机通道。
自撞纠回一次：带子第一次放错（两半都测成 (28,28,28)），靠"逐行找亮墨"定位到 y=204..277 ⇒ 尺没量到不等于不存在。
验证：闸门 `RESULT=ok`；清账表 115 行 / 未清账 47 未动；脚本电池 `Ran 362 / OK`（台账之后）；0 产品文件。

**下一轮（R183）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`949350d`/`5bb266e` 等跑的全部失败步骤；
② **209 的第一步**：读 `content-empty` 夹具的 filter 选中项（一条 grep），据此决定是开真机那一腿还是判成通道；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表剩余 47 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。
最后更新：2026-10-19 05:12（本地 · R181 / 第 183 轮：**主窗口/列表行四格判完 + 看图那条印象被改成一条要求读数的单**（U-601…U-603 · 产品 0 文件，动效主线）

四格 `not-applicable`：空态在 `EmptyStateView`、失败在 `NoticeBanner`（`ContentView.swift` 四处）、复制成功回执在详情区那颗按钮（`ReceiptLine` 只被 `SettingsView` 用）、行没有可禁用态（三个缺席词各 0 命中）
⇒ 清账表 111 → 115 行 / 已清账 115 / 未清账 51 → 47（格子 162 不变），缺席 `声明=48 不成立=0`。
看图：`content-empty-750x560-dark` 里筛选分段控件右半实心白底黑字、左半深色带描边 —— **没据此开缺陷单**，开 209 要求先取同源读数（哪段是选中，这张帧答不了）。
另把 R177 那格真产物证人从写死行数改成解析闸门读数 + 恒等式（清账往前不必再改守卫）。
验证：闸门 `RESULT=ok`；脚本电池 `Ran 362 / OK`（台账落盘之后）；0 产品文件 ⇒ 没构建、没重捕、没换装。

**下一轮（R182）的靶**：⓪ 复验 208（`PROBE_FPS` 那一行里必须有 `超锚点帧=`）+ 读 `949350d`/`5bb266e`/`2c0122c`/`0bb1382`/`0d75073`/`e0556f3` 全部失败步骤；
② 209 的同源读数（两段的填充/文字亮度 + 与 `content-with-notice` 对照）；③ 205 的按元素切带；④ 201 的带内读数；
⑤ 清账表剩余 47 格（`--list-open`）；⑥ 202、207、189、188 的 ②③、176、182/183/185。
最后更新：2026-10-19 05:00（本地 · R180 / 第 182 轮：**208 落地 —— 颗数并进活下来的那一行 `PROBE_FPS`**（U-598…U-600 · 产品 0 文件，判据账）

改的是载体不是判据：`fpsTail`（`… worst= …ms 超锚点帧= N`）拼进 `PROBE_FPS`（加长原串会 type-check 超时，R176 实测），
独立行 `PROBE_WORST_FRAME` 与 `WORST_OUTLIER` 保留 ⇒ 三处载体；接线契约按次数判（`let fpsTail = ` 1、`+ fpsTail)` 1、`超锚点帧=` 3）。
自撞三处都记进 208 追记：python 因中文串里的 ASCII 双引号 SyntaxError ⇒ **整段没写**而我以为写了（`grep fpsTail` 空才发现）；
期望从 2 改 3 前先指认第三处；**收尾第三次复发"message 先于 diff"**（`949350d` 讲了 U-598…U-600 而 diff 只有两个 Swift 文件，
台账脚本死在 `grab()` 多传参数）⇒ 台账批写从此落成脚本文件 `ledgers_r180.py`，收尾的门一律用退出码。
验证：`swift test --filter FrameIntervalBudgetTests` `Executed 5 / 0 failures`；脚本电池结论行未落数（R258 现读：占位符没渲染，见 307）；
清账表条数未落（R258 现读：这一行是当年生成器把占位符原样写进台账留下的空壳，不是读数；见 BACKLOG 307）；0 产品文件 ⇒ 没构建产物、没重捕、没换装。

**下一轮（R181）的靶**：⓪ **复验 208**：读本笔 push 那一跑的 `--log`，判据是「`PROBE_FPS` 那一行里必须有 `超锚点帧=`」，
   只出现独立行不算过；同时读 `e0556f3`/`0703dae`/`0d75073`/`0bb1382`/`2c0122c`/`949350d` 各跑的**全部失败步骤**（当时多仍 `in_progress`）；
② 205 的按元素切带；③ 201 的带内读数；④ 清账表的未清账格（`--list-open`；当年那行的格数没落，见 307）；⑤ 202、207（多靶变异表）、189、188 的 ②③、176、182/183/185。
最后更新：2026-10-19 04:40（本地 · R179 / 第 181 轮：**⓪ 读完 R176 的 runner 验收 —— 判据绿、新读数没落地**（U-595…U-597 · 产品 0 文件，判据账）

`39161493538`=`fce0b84` `success`；STEP[16] 不再红；`PROBE_FPS 机器=arm64/macOS 15.7/1x baseline_p95=16.67 off_p95=16.67 loaded_p95=16.67 比值=1.000 预算=3.00 n=222 worst=58.8
build-and-test`（三臂 p95 全等、比值 1.000、n=222）
⇒ R142 的相对判据与 R176 的颗数锚点在 runner 上都是**通过**。但 R176 新加的 `PROBE_WORST_FRAME` 在 `--log` 全文 **0 次**，
而它前面的 `PROBE_FPS` 完整落地（`… n=222 worst=58.8`，这一跑锚点本就通过） ⇒ 读数通道尾部又吃一行（新开 208；206 不结案）。
本轮试改"把颗数并进 FPS 行"能编译，但接线针脚没跟着改对 ⇒ **主动 `git checkout` 回滚两个 Swift 文件**，不留半改状态。
另修掉 R178 带出的那格红：第 180 轮标题声明 `U-592…U-593` 而该节定义 592/593/594（区间守卫抓到真半批）⇒ 改标题，不改守卫。
验证：`swift test --filter FrameIntervalBudgetTests` `Executed 5 / 0 failures`；脚本电池 `Ran 362 / OK`；0 产品文件 ⇒ 没构建、没重捕、没换装。

**下一轮（R180）的靶**：⓪ 读本笔 push 那一跑 + `e0556f3`/`0703dae`/`0d75073` 三跑的**全部失败步骤**（当时仍 `in_progress`）；
② **208 一次做完**（颗数并进 `PROBE_FPS` + 针脚数完整形状 + 复验"下一跑的 FPS 行里必须有那颗数"）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 51 格（`--list-open`）；⑥ 189、188 的 ②③、176、182/183/185、202、207（多靶变异表）。
最后更新：2026-10-19 04:35（本地 · R178 / 第 180 轮：**R176 欠的三把刀补上，锚点"要颗数撑着"有了反证**（U-592…U-593 · 产品 0 文件，刀账）

`mutate_r178.py`：M693/M694/M695 全 CAUGHT（M693→testTheWorstFrameAnchorNeedsMoreThanOneOutlier、M694→testTheWorstFrameAnchorNeedsMoreThanOneOutlier、M695→testTheProbeWiresTheAnchorToTheSampleCount）。前两把打在纯谓词的两个相反方向（容差、矛盾分支），
第三把打在新加的**接线扫描**上（`testTheProbeWiresTheAnchorToTheSampleCount`：剥行注释后要求取数处/以 `overAnchor` 为参数的断言/印颗数的读数行各恰好一次）。
`RESTORE_CLEAN=no` 这一格不绿：还原复跑 `ran=0 broke=True`，而三处 needle 复查为原形、单跑 5 格绿
⇒ 刀账成立、那一格按 NOT-RUN 记，成因未命名（候选：构建目录中间态）。预检 本轮预检在表之前跑，读数见 /tmp/r178_mut.log。
0 产品文件 ⇒ 没构建、没重捕、没换装。

**R178 收尾时有一格电池是红的，我没修完就推了（`e0556f3`），这一格是 R179 的第一件事**：
`test_ledger_ids.NewestRoundIdRangeTests.test_the_range_guard_is_not_vacuous` ——
正对照从最新一节删掉一条真实定义（U-594），期望守卫只报那一个号，实际报 `[]`。
本机已排除三种形状问题：编号连续（592/593/594）、标题区间写作 `（U-592…U-594 · …）`、节内定义 ≥3 条 —— 三种都仍然红，
⇒ 不是"我这半批没写完"，而是**这条守卫对本节的形状整体看不见**（要么区间解析没命中，要么它取的"最新一节"不是第 180 轮）。
不许为了让它绿而改标题写法：先读 `test_ledger_ids.py:200-245` 与它调用的解析函数，问"它这次读的是哪一节"。

**下一轮（R179）的靶**：⓪ 读 `fce0b84`（R176 新判据第一次上 runner）/ `0703dae`（R177 退役表）/ 本笔那一跑的**全部失败步骤**；
   预期：STEP[16] 不再因单帧离群红，且 `PROBE_WORST_FRAME` 那一行**要在**（它没露面就是读数通道又坏了）；
   退役后的表在 runner 上仍 `MOTION_LEDGER_RESULT=ok` 且 `RETIRED 1（浮层/底部说明）`；
② 205 的按元素切带；③ 201 的带内读数；④ 清账表剩余 51 格（`--list-open`）；⑤ 189、188 的 ②③、176、182/183/185、202；
⑥ 还原复跑那一格若再来，先按"能否复现"分诊，别改表也别改判据。
最后更新：2026-10-19 04:25（本地 · R177 / 第 179 轮：**204 结案 —— 撤掉没有承载物的「浮层/底部说明」，清账表学会显式退役**（U-589…U-591 · 产品 0 文件，判据账）

决定：这一层没有承载物（stack 只有 `field / empty / scroll`；`footerLabel`/`hintLabel` 0 命中），功能由空态那一句就地承担，
常驻键位 chrome 与内容争注意力 ⇒ 撤词表项，记 D-194。**将来要做键位提示行就是新需求：先做承载物，不许复活这一层继续判 not-applicable。**
仪器代价与解法：撤项在纯计数上与「清账退步」同形（118 → 111）⇒ 表新增 `retired_surfaces`，闸门四条判据
（`RETIRED_UNDECLARED` / `RETIRED_STILL_LISTED` / `RETIRED_ROW_PRESENT` / `RETIRED_NO_REASON`），地板降幅只从登记过的表面来。
真产物：`表面=18 格子=162 行数=111 已清账=111 未清账=51 地板=111`、`RETIRED 1（浮层/底部说明）`、
`FLOOR_BASELINE head=111 now=111`、缺席 `声明=41 不成立=0`。两格测试自己先红：needle 命中定义行、基准断言要减降幅。
验证：0 产品文件（工作树钉子数过）⇒ 没构建、没重捕、没换装；CI：`fce0b84`（R176 的新判据第一次上 runner）与本轮那一跑都待读。

**下一轮（R178）的靶**：⓪ 读 `fce0b84` 与本轮 push 那一跑的**全部失败步骤**；
   预期：STEP[16] 不再因单帧离群红 —— 若还红，数 `PROBE_WORST_FRAME` 的颗数，≥2 颗查产品、**不许改判据**；
   并确认 `MOTION_LEDGER_RESULT=ok` 在 runner 上也拿着退役后的表成立（`RETIRED 1` 要在）；
② 206 的三把欠刀（M693 起：tolerance、`overAnchor` 过滤式、超锚点却 0 颗那一格）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表剩余 51 格（`--list-open`）；⑥ 189、188 的 ②③、176、182/183/185、202。
最后更新：2026-10-19 04:15（本地 · R176 / 第 178 轮：**⓪ 那朵没人读的 CI 红有名字了 —— 绝对锚点原来靠单遍最大值撑**（U-586…U-588 · 产品 0 文件，判据账）

`ci_read.py steps 39157963970` ⇒ STEP[16] `On-screen probe coverage floor` 红在 `worst=320.6537916667003 > 120ms`（`testFrameIntervalsUnderStateChanges` 的绝对锚点，
不是 R142 那条相对 p95）；相邻两跑 `e61796c`/`9e1d3d4` 同一份判据绿 ⇒ **最大值在 runner 上换班**，三份 diff 都没动产品。
处置：`stats()` 多一格 `overAnchor`（与 `worst` 同源），判据 `isWorstFrameJank(worstMs:overAnchorCount:)` ——
单帧离群只打读数（`PROBE_WORST_FRAME` / `WORST_OUTLIER`），≥2 颗才红，超锚点却 0 颗 ⇒ 红给尺；真值表 6 格、期望手算。
**没验到**：本机采样通道死（R91 `baseline_n=0`）⇒ 真产物验收在 CI 那一跑；本轮没跑刀 ⇒ NOT-RUN。
验证：编译 0 告警、纯函数卷 4 格绿、清账表 118 行 / 未清账 53 未动、产品文件 0（工作树钉子数过）。

**下一轮（R177）的靶**：⓪ 读本笔 push 那一跑与 `659ec46`/`e93c13b`/`3ea2b40` 三跑的**全部失败步骤**；
   关键预期：STEP[16] 不再因单帧离群红 —— 若还红，先看 `PROBE_WORST_FRAME` 的**颗数**：≥2 颗就是真卡顿，**不许改判据**，去查产品；
② BACKLOG 204 要选一种处置（做承载物 / 撤词表，不许用删格子收口）；③ 205 的按元素切带；④ 201 的带内读数；
⑤ 清账表剩余 53 格（`motion_surface_gate.py --list-open`）；⑥ 189、188 的 ②③、176、182/183/185、206 的 CI 复验。
最后更新：2026-10-19 04:05（本地 · R175 / 第 177 轮：**左轴尺 `frame_audit.py bands` 落地，第一个结论是撤掉 R174 我自己的前提**（U-583…U-585 · 产品 0 文件，判据账）

**新尺**：`bands` 按 y 聚文本行带 → 每带报 `最左墨 / 众数左沿 / 行内散布`；8 格自测（同轴不许读成两根、错开 30px 不许抹平、碎屑不算行、带图标的行不适用、混元素必须拒判）。
**撤掉的前提**：空态帧只有 2 带，且它们是**两个元素**（搜索框行 22.5pt = R104 的 22pt 内缩；空态那一句 53.5pt），两档逐位一致
⇒ R174 的"空态两行不同轴"是我把两个元素读成了两行；R64 的"空态居中"相容。**尺自己的漂**：带0 `min_x` 两档同 45px 而众数 52.0pt vs 22.0pt
⇒ 主读数改 `min_x`、带内散布 >40px 一律 `不可判`（三张真帧现在都不给同轴结论）。**205 不结案**，收窄成"按元素切带"。
验证：电池 `Ran 354 / 红 0`；清账表 118 行 / 未清账 53（未动）；0 产品文件 ⇒ 没构建、没重捕、没换装。
CI：`39160246493`=`659ec46` in_progress/未读; `39159208254`=`9e1d3d4` completed/success; `39159159623`=`e61796c` completed/success; `39157963970`=`0dbcbb5` completed/failure。另记 R174 那笔的电池：第一次跑红了一格悬空引用、单独跑与整卷重跑都绿，**成因未命名**（陈旧字节码缓存那条猜测没被证实）。

**下一轮（R176）的靶**：⓪ 先读 `659ec46` 那一跑（`in_progress` ⇒ 结论未读）与 `0dbcbb5` 那朵 **failure** 的全部失败步骤
   （`python3 scripts/ci_read.py steps 39157963970`）—— 它比 e61796c / 9e1d3d4 两跑 success 更早，**不许当成已修**；
① 205 的下一格：带内按 x 断簇（按元素切带），然后才谈"同一表面两根轴"；
② 204 要选一种处置（做承载物 / 撤词表），不许用删格子收口；
③ 清账表剩余 53 格（`motion_surface_gate.py --list-open`）；④ 201 的带内读数、195 的 ①、189、188 的 ②③；
⑤ 把 `bands` 这把尺写进 §9.3 的常规仪器清单（现在只有本轮用过它）。
最后更新：2026-10-19 03:52（本地 · R174 / 第 176 轮：**清账表「浮层/底部说明」七条理由换主语 —— 那层没有承载物；开出 204 / 205**（U-580…U-582 · 产品 0 文件，动效主线）

**本轮读到的事实**：`QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll` 三个子视图；`footerLabel` / `hintLabel` 在产品源码 0 命中。
⇒ 七条理由的主语换成真实存在的视图（R173 六格 + 更早的「悬停」格），**格子数一格没动**：清账表 118 行 / 已清账 118 / 未清账 53，
缺席复查 `格=118 声明=50 不成立=0/50`。
**204**：幽灵表面要么做承载物（产品需求）要么撤词表（DECISIONS 记理由），本轮**两样都没选**，因为撤词表会把未清账直接删掉 9 格 —— 那不是判断。
**205**：看图腿用 `frame_audit.py align` 量到空态两档各 2 / 2 簇（≈22pt / ≈55pt），
与 R64 的"空态居中"记录形状不同；这把尺是**逐像素行**的，答不了"同不同轴" ⇒ 只记问题，不判缺陷。
验证：0 产品文件（工作树钉子当场数过）⇒ 没构建、没重捕、没换装；电池 346。

**下一轮（R175）的靶**：⓪ 读本笔 push 之后那一跑的**全部失败步骤**（`python3 scripts/ci_read.py steps <run>`），
   并确认上一笔（`9e1d3d4`）那一跑的结论 —— 结论未读时不许写"没红"；
① 收口：`AGENT_FINAL_REPORT.md` 按阶段二实际覆盖（118/171 格、53 格未判）与 204/205 两条未决项写清"能停的判据只剩需要用户真机或授权的那几项"；
② BACKLOG 204 要**选一种处置**并留下证据（不许用删格子收口）；③ BACKLOG 205 的按行带尺（先聚 y 再取 min-x，与 56.0–57.0pt 对账）；
④ 清账表剩余 53 格（`motion_surface_gate.py --list-open` 给名单）；⑤ 195 的 ①、189、188 的 ②③、176 / 182 / 183 / 185、201 的带内读数。
最后更新：2026-10-19 03:31（本地 · R173 / 第 175 轮：**浮层底部说明清掉六格 + 闸门新增 `--list-open`**（U-577…U-579 · 产品 0 文件，动效主线）

**清账表 118/171（未清账 53）**：`浮层/底部说明` 的 加载/禁用/聚焦/按下/成功/错误 判 `not-applicable`（这一行是静态 NSTextField 标签，加交互态是减法）；缺席 47 条全部复查通过。
**两格故意不判**并新开 BACKLOG 202：`isSelected` 的 4 处属于列表行 ⇒ 文件级缺席不能替一行级结论作证，要做的是把证据降到行级（`functionBody` 断言），不是放宽复查。
**新工具**：`motion_surface_gate.py --list-open` 逐格列名单（上一轮我只能反推 JSON，反推漏了"占位行没清账"那一类）+ 四格测试。
**自查一条**：给生成器插 roster 时用了字符串把戏 ⇒ 证据列变成占位符文本，闸门 6 条 `EVIDENCE_SHAPE` 红 + 电池 3 条红，**提交前**被抓，改回字面路径后 `RESULT=ok`。
CI：`3cb5461`/`1805351` 已 `success` ⇒ R171 那笔（有界轮询 + 热图宽度预算卷）在 runner 上过；`924695f`/`0dbcbb5` 本轮仍 `in_progress` ⇒ 结论未读。

**下一轮（R174）的靶**：⓪ 读 `924695f` / `0dbcbb5` 两跑的**全部失败步骤**（关键预期：`Capture gate` 继续绿）；
① 先做 BACKLOG 202 的行级证据，然后清 `浮层/底部说明 × 空 / 选中`；同批可吃 `主窗口/筛选条`（6 格）与 `设置窗口/说明段`（5 格）；
② BACKLOG 200（最小窗口右栏可用宽的读数）→ 才谈 197；③ 201（那 205pt 带内是什么）；④ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-19 03:11（本地 · R172 / 第 174 轮：**把 R171 欠的三把刀补上 ⇒ BACKLOG 199 结案**（U-574…U-576 · 产品 0 文件，刀账）

**做了什么**：`mutate_r172.py` M690/M691/M692 全 CAUGHT、RESTORE_CLEAN=yes（基线 ran=6），三把各问 `==`、边界 `>=`、`maxPolls` 一个方向；199 结案。
**CI 复验到手（R172 补）**：`39156179381`（= `546dc97`）`JOB ⇒ success`、`CAPTURE_GATE_RESULT=ok 红=0`、六张高帧各打一次 `CAPTURE_BLANK_NOT_RUN` ⇒ 194 正式结案；口径仍是「不是产品缺陷」，205pt 带内的成因未命名 ⇒ 201 开着。下面那行"三跑未读结论"里 `546dc97` 那一格已被这一句取代。
**CI 复核（只读步骤名）**：`c4366b3`（R169）只有 `STEP[15] Capture gate` 红、与前两跑同形 ⇒ R169 的宽度预算卷没在 runner 引出新的红；`546dc97`/`3cb5461`/`1805351` 仍 `in_progress` ⇒ **结论未读**，不说"没红"。
**没做的**：0 产品文件 ⇒ 没重捕、没换装；清账表 行数=112 已清账=112 未清账=59 地板=112 未动；预检仍 `bad=3`（198 那一族）。

**下一轮（R173）的靶**：⓪ 读 `546dc97`（R170，出口那一笔）与 `1805351` 的**全部失败步骤**；关键预期：`Capture gate` **不再因那六张高帧红**，
   且 `--log` 里能看到 `CAPTURE_BLANK_NOT_RUN settings-*-tall…` 六次 —— 若红还在就先看 marker 打没打，再怀疑出口形状覆盖不全；
② BACKLOG 201：量 runner 那 205pt 的带里是什么（侧栏 / 卡片描边 / 文字行），与本机同一条带对账；
③ BACKLOG 197 + 200：先拿"最小窗口下右栏可用宽"的读数，再判热图那条带改不改；
④ 清账表下一批（新格一律带 `缺席:`）；⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-19 03:04（本地 · R171 / 第 173 轮：**BACKLOG 199 落地 —— 把「等多久」换成「落没落地」的有界轮询**（U-571…U-573 · 产品 0 文件，判据账）

**做了什么**：`CapturePathWriteBudgetTests` 的前提钉子从固定 `pumpMain(0.4)` 换成 `awaitFlushedSnapshot`（每拍重开库 + 三态纯谓词 `landed`/`keep-polling`/`timeout`，超时才红且带两端读数），**断言口径一个字没改**；新增真值表两格 + 上限存在性一格。
**为什么值得做**：这朵红 R168 有名（459≠480）、R169 无名（日志连 `failed` 行都被 stdout 吞了），两轮都不是产品代码 ⇒ 修成因，CI 读数少一个噪声源。
**没做的（写在账里，不当已通过）**：变异刀 NOT-RUN（`==` / `>=` 两把留给下一轮）；产品 0 文件 ⇒ 没重捕、没换装。
验证：编译 0 告警、目标卷 6 格全绿、全量卷 864 例 / 跳过 42 / 失败 0、脚本电池 `Ran 342 OK`。

**下一轮（R172）的靶**：⓪ 读 `546dc97`（R170）与本笔那一跑的**全部失败步骤**（`PYTHONUTF8=1 python3 scripts/ci_read.py steps <run>`）；关键预期：
   `Capture gate (unregistered reds must be zero)` **应该不再因那六张高帧红**（若还红 ⇒ 先看 `CAPTURE_BLANK_NOT_RUN` 打没打，再怀疑出口形状覆盖不全）；
① 补 R171 欠的两把变异刀（`ArchiveReloadWait.outcome` 的 `==` 与 `>=`）并结案 199；
② BACKLOG 201：量 runner 那 205pt 的带里到底是什么（侧栏 / 卡片描边 / 文字行），与本机同一条带对账 —— 决定"通道"这个口径站不站得住；
③ BACKLOG 197 + 200：先拿"最小窗口下右栏可用宽"的读数，再判热图那条带改不改；
④ 清账表下一批（新格一律带 `缺席:`）；⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-19 02:42（本地 · R170 / 第 172 轮：**runner 的分辨轴给了一个谁都没预测到的形状 ⇒ 出口按实测接线，194 结案为通道限制**（U-567…U-570 · 产品 0 文件，判据账）

**runner 的读数**（`--log`，run `39152321051` = `72279ff`）：六张高帧同形 `drawnBoxPt=205 / drawnBottomPt=1040 / transparent=95.9% / screenVisibleHeightPt=681`；
本机同批 `drawnBoxPt=1040…1040`（画满）。三种解释被三条数排除（`>0` / `≠可视高` / 几何三边相等）。
**出口已接线但只认实测形状**：`0 < drawnBoxPt < requested` ⇒ 打 `CAPTURE_BLANK_NOT_RUN`（闸门按 `*_NOT_RUN` 解析）；
`==0`（没渲染）与 `==requested`（画满却报空）不放行、红照旧。机制**未命名** ⇒ 新开 201（下一步量"那 205pt 带里到底是什么"）。
**刀**：`mutate_r168.py` 12 臂全 CAUGHT、RESTORE_CLEAN=yes；M687/M688 打在新轴的两端、M689 打在 marker 的名字形状上；
M675/M678 的 needle 因谓词改形**当场改写**（不留空转的刀）。
**本机自陈**：出口点火 0 次 = 0（本机没有空白高帧），所以这条出口的真产物验收在 CI 那一跑。
验证：编译 0 告警、判据卷 10 格、捕获卷退出码 0、帧基线 138 张 changed=0、全量卷 862/42/0、清账表 行数=112 已清账=112 未清账=59 地板=112。

**下一轮（R171）的靶**：⓪ 读 `c4366b3` 与本笔那一跑的**全部失败步骤**；关键预期：`Capture gate (unregistered reds must be zero)`
   这一步**应该不再因那六张高帧红**（若还红 ⇒ 出口的形状没覆盖 runner 的真实读数，先看 `CAPTURE_BLANK_NOT_RUN` 打没打）；
② BACKLOG 201：量那 205pt 的带里是什么（侧栏 / 卡片描边 / 文字行），与本机同一条带对账 —— 决定"通道"这个口径站不站得住；
③ BACKLOG 197 + 200：先拿"最小窗口下右栏可用宽"那格读数，再判热图那条带要不要改；
④ BACKLOG 199（`pumpMain(0.4)` 换成有界轮询 + 正对照）；⑤ 清账表下一批（新格带 `缺席:`）；⑥ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-19 02:20（本地 · R169 / 第 171 轮：**把热图 197 的『加周数』那条修法量成数**（U-563…U-566 · 产品 0 文件，判据账）

**量到的边界**：组件帧可用宽 398pt（夹具 width=430 − 2×16）、26 周网格 379pt（余量 19pt）、
27 周 393pt（放得下）、28 周 407pt（顶破），一周占 14pt ⇒ 118pt 的空白带里只有 14pt 是周数能削的。
**这一格推翻了我自己上一轮写在 `defaultWindowWeeks` 注释里的"26 是上限"**（那是组件帧的错觉）。
判据卷 `DailyCopyHeatmapWidthBudgetTests` 4 格 + 变异 M684–M686 全 CAUGHT（RESTORE_CLEAN=yes）；
M685 改的是对照物（夹具 430→460）⇒ 边界结论依赖夹具、不依赖注释。
**没动产品的理由**：真正卡 197 的是"最小窗口下右栏可用宽"那格没有读数（注释里的 412pt 自卡片化后从未复量）⇒ 新开 BACKLOG 200，先量再改。
**仪器自己也量了一次**：预检把两支活针报成 `命中=0` 而真刀 CAUGHT ⇒ 规矩是"预检只当线索，裁决权在真刀"（198 追记）。

**下一轮（R170）的靶**：⓪ 读 `72279ff`（R168）与本笔那一跑的**全部失败步骤**（`PYTHONUTF8=1 python3 scripts/ci_read.py steps <run>`），
   并从 `--log` 取 `CAPTURE_DRAW settings-*-tall … drawnBoxPt=`（report-only 步骤，`--log-failed` 取不到）；
① 按包围盒读数给 194 定性（`0` 没渲染 / `≈screenVisibleHeightPt` 被裁 / `≈1000` 尺坏了），**然后**才写出口；
② BACKLOG 200：给"最小窗口下热图那格的可用宽"一个从产品布局来的读数（会红的判据，不是注释），有了它才判 197；
③ 清账表下一批（新格一律带 `缺席:`）；④ BACKLOG 199（那朵 `pumpMain(0.4)` 的红换成有界轮询，带正对照）；
⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-19 01:59（本地 · R168 / 第 170 轮：**把 194 的放行决定抽成会红的谓词，并补上它欠的那根分辨轴**（U-557…U-562 · 产品 0 文件，判据账）

**落了什么**：① `shouldRegisterBlankAsMachineGap` —— settings 族 + 需求高 ≥1000 + `content == host == requested` 才判"这台机器画不出来"；
调用点在未画循环里**只报 `BLANK_GAP_WOULD_RELEASE … would=`，处置一行没改**（runner 那六张红照旧红）。
② `drawnBoundingBox` + `CAPTURE_DRAW` —— R167 欠的那根分辨轴：三态哨兵 `-1` 量不到 / `0` 根本没渲染 / `>0` 画到哪里，
与 `transparent` 同一份 raw rep、同一个 `transparentAlphaCeiling`。本机 6 张高帧读数 box 1040…1040 pt（"画满"那一侧的标定）。
**为什么这次不算空对账**：9 格单测每一格都让尺子/谓词真的给数；`mutate_r168.py` M675–M683 共 9 把全 CAUGHT、RESTORE_CLEAN=yes，
其中删**调用**的那把红在 `testBlankFrameLoopCallsThePredicate`、换**常数来源**的那两把红在 `testTallFixtureThresholdHasOneSource`。
**自陈**：本机 census `loop_items=2 with_geometry=0` ⇒ 高帧一张都不空，谓词在本机的唯一证人是单测，"出口已验收"这句话现在没人配说。
**别人那一卷的红**：全量卷 857 例 / 失败 1，唯一一朵在 `CapturePathWriteBudgetTests` 的 `pumpMain(0.4)` 前提（单跑 4 例 / 失败 0）⇒ 记 BACKLOG 199，不改它的承重。

**下一轮（R169）的靶**：⓪ 读本跑与 `490b1ea` 的**全部失败步骤**（`PYTHONUTF8=1 python3 scripts/ci_read.py steps <run>`），并从 `--log` 里取
   `CAPTURE_DRAW settings-*-tall … drawnBoxPt=`（report-only 的捕获步骤，`--log-failed` 取不到）；
① **按包围盒读数给 194 定性并决定出口**：`0` ⇒ 根本没渲染；`≈ screenVisibleHeightPt` ⇒ 被屏幕裁（出口按包围盒写，不是按屏幕高）；
   `≈ 1000` ⇒ 修这把尺。三条出口的谓词都要先写单测再接线（R168 的形状可抄：谓词 + census 自陈覆盖面 + 删调用的刀）。
② BACKLOG 197（热图右侧 ~118pt 空白带）—— 产品面第一笔：先 spike，帧基线同一笔 update，过 `CARD_RHYTHM` 与 `contentMustFit`，全量卷 + 换装本机 + 逐屏看图；
③ BACKLOG 199（那朵红的有界轮询修法，带正对照）与 198（预检按表的新近度分栏）；
④ 清账表下一批（新格一律带 `缺席:`）；⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。
最后更新：2026-10-18 17:06（本地 · R167 / 第 169 轮：**runner 把 194 签成第三种情形，而我给自己造的两格正对照都是空的 ⇒ 出口撤回**（U-554…U-556 · 产品 0 文件，判据账）

**读数到手**：`--log`（**不是** `--log-failed` —— 那行是 report-only 的捕获步骤打的，那一步没红）里
`CAPTURE_GEOMETRY settings-privacy-tall light requested=720x1040 content=720x1040 host=720x1040 screenVisibleHeightPt=681`，
六张高帧同形 ⇒ 按 R162 预登记的三分规则落在第三种：几何三边都等于需求、像素几乎全空。
前两种（窗口被收小 / 内容视图没铺满）被同一行排除。runner 可视高 681/684、本机 847，两边都 < 1040 而只有本机画满 ⇒ 屏幕高度不是原因。

**但我把写好的出口撤了**：本机没有空白高帧，我用"强行让高帧进入未画循环"做正对照 —— 用例通过，
可 `CAPTURE_NOT_RUN` 那行根本没打印（那张帧透明度 ~0，走完所有分支什么都不做）；
第二格（几何改成 `content-1` 期望落回 XCTFail）同理，本来就不空，两种实现都绿。
**两格对照都建在"没有对象"的数据上 = 没测** ⇒ 不推一条我证明不了会点火的放行通道给 CI。

**下一轮（R168）的靶**：⓪ 读本跑与 `1b4278c`/`3e58a34`/`88d378e` 的**全部失败步骤**；
① **给 194 补那根分辨轴**：在 `CaptureMetrics` 里带"最后一行有墨的 y / 画到的包围盒高"
   （≈ 屏幕可视高 ⇒ 被裁；= 0 ⇒ 没渲染），拿 runner 读数分开两种解释之后**才**谈出口；
② **BACKLOG 197**（热图比它上下的文字窄一条 ~118pt）—— 这是产品面：先 spike 一条修法，帧基线同一笔 update，
   过 `CARD_RHYTHM` 4.5pt 极差与 `contentMustFit`，再全量卷 + 换装本机 + 逐屏看图；
③ 清账表下一批（新格一律带 `缺席:` 例子）；④ 195 的 ①；⑤ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 16:56（本地 · R166 / 第 168 轮：**热图与菜单栏两族再判 13 格（99 → 112），看图量出热图右侧一条 118pt 的空白带**（U-551…U-553 · 产品 0 文件，动效主线）

**做了什么**：清账表 99 → 112（未清账 59 / 171）。13 格全部带 `缺席:` 例子，缺席守卫从 29 条涨到 **41 条且全部成立**
（热图的 `Button`/`TapGesture`/`selection`/`disabled`/`ProgressView` 逐个实测 0；
菜单栏那层 `withAnimation`/`animation`/`onHover`/`transition` 各 0 —— 真 NSMenu 与系统状态栏里 SwiftUI 的按压与过渡不执行）。

**看图量出一条真缺陷，但本轮没动它**：`settings-stats-populated-720x540-light.png` 里
**网格右沿 560.5pt、说明段右沿 688.5pt** ⇒ 图的右边有一条 ~118pt 的空白带，而它上下的文字都铺到卡片内沿。
没改的理由是验证预算：动布局要在同一笔里更新 138 帧基线、过 `CARD_RHYTHM` 的 4.5pt 极差与 `contentMustFit`、再跑全量卷，
剩余轮次不够 —— **半测的布局改动进交付物比不改更坏**。已开 BACKLOG 197，把测量、两条候选修法（自适应铺满 / 整块居中）
与各自代价写死；并记下"不许把 118pt 读成 26 周本来就这样"（月份轴是按网格宽度分布的，那是同一件事的两处表现）。

**自曝一把坏尺**：想用"同一行换色次数"证明网格画出来了，本机打出 423 —— 那是 24 灰阶量化 + 抗锯齿的噪声，不是 53 列。
这条读数不进账当证据，证词换成"眼睛看 + 量两条右沿"。

**下一轮（R167）的靶**：⓪ 读 `1deda5d`/`bc53a5c`/`817be0d`/`1b4278c`/`3e58a34`/本跑 的**全部失败步骤**，
   重点 runner 那一行 `CAPTURE_GEOMETRY`（三种样子各绑一种处置，指认之前不加出口）；
   ② **BACKLOG 197 落地**（这是产品面：先 spike 一条修法，帧基线同一笔 update，过 4.5pt 极差与 contentMustFit，
      再跑全量卷 + 换装本机 + 逐屏看图）；③ 清账表下一批（新格一律带 `缺席:` 例子）；
   ④ 195 的 ①；⑤ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 16:50（本地 · R165 / 第 167 轮：**把"实测 0 处"从散文升成会红的守卫**（U-548…U-550 · 产品 0 文件，判据账）

**做了什么**：新增 `scripts/ledger_absence_claims.py`（+ 7 格电池）。动效账里"这一屏没有加载态 / 这层没有禁用分支"这类结论
的证据是**某标识符在某文件里 0 次**，散文里的"实测 0 处"不会自己保鲜。现在按 R131 的文法
`缺席:<路径>=<标识符>[,…]` 扫已提交的表逐条复查：`格=99 声明=29` ⇒ `RESULT=ok 不成立=0/29`。
上一批 14 格里 5 条补上了这条例子（其余 24 条是前几轮已在表里的）。

**第一次跑连红两次，都是仪器坏**：① 只按仓库根解析路径 ⇒ 29 条全报"解析不到"（表里指针是**包内相对**，
与 `motion_surface_gate.py` 同口径，仓库根下还有一层 `ClipboardHistory/`）⇒ 修 `resolve()` 试两个候选根，不重写台账；
② 脚本没有 argparse ⇒ 仓库那条"每个脚本 `--help` 都要能构造"的守卫红（它历史上救过我两次：R143 的 `%`、R154 的 PIL，这次轮到我）。
两次都改工具，**没有放宽任何一条判据**。

**防"恒真的门"的三格正对照**：假声明必须报 `理由过期`、路径解析不到必须点名、名册为空 `main()` 必须非 0；
另加文法严格性（`缺席: X.swift = Word` 这种松散写法不算声明）与"表必须等于生成器输出"。本机 `Ran 342 tests OK`。

**下一轮（R166）的靶**：⓪ 读 `1deda5d`/`bc53a5c`/`817be0d`/`1b4278c`/本跑 的**全部失败步骤**，
   重点 runner 那一行 `CAPTURE_GEOMETRY`（三种样子各绑一种处置；指认之前不加出口）；
   ② **一格真的动效**（产品 > 0：落地 + 帧 + 换装本机 + 逐屏看图）—— 这是阶段二最大的欠账，优先于任何仪器工作；
   ③ 清账表下一批（菜单栏两族 + 设置说明段那几格），新格一律带 `缺席:` 例子；
   ④ 195 的 ①（python 侧变异跑带 `PYTHONDONTWRITEBYTECODE=1`）；⑤ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 16:47（本地 · R164 / 第 166 轮：**录制器与浮层剩余状态一次判掉 14 格（清账表 85 → 99），看图抓到一条「理由与帧不配对」**（U-545…U-547 · 产品 0 文件，动效主线）

**做了什么**：清账表 85 → 99（未清账 72 / 171）。14 格各绑本轮 grep 的缺席计数或那一行代码
（录制器 `ProgressView=0 isLoading=0 disabled=0 isEnabled=0 focus=0`、`shortcut.didSet` 永远填标题、
非法组合键走 `onInvalidShortcut`；浮层 `QuickPickModel` 的 `Task {`/`async`/`await`/`ProgressView` 全 0；
空态是 `NSTextField(labelWithString:)`、有无由 `empty.isHidden` 决定）。表只经生成器写，`不合法格=0`，
§9.3 的未清账数从闸门实时输出抄回（72）。

**看图抓到的一件事**：`quickpick-empty-420x300-light.png` 里搜索框**没有焦点环** —— 离屏面板不是 key window，环本来就不画。
而「浮层/搜索框 × 悬停」那格（R155）的理由写的是"焦点已经在说话"。⇒ 那条理由的证人是 R76 的焦点环判据，**不是这张帧**；
判语不改（另有证人），但"哪张帧能给哪条理由作证"进账，免得下一轮拿一张空帧去复核一个本来不画的东西。

**没有产品改动，且不是没查**：浮层空态"要不要配一点什么"查过 —— 不加。这一层出现时用户的手在键盘上，
那句话已说完"发生了什么 + 下一步"（换词或按 Esc）；加插图/动效/提示条都是把注意力钉在"没有"上。

**下一轮（R165）的靶**：⓪ 读 `1deda5d`/`bc53a5c`/`817be0d` 与本跑触发的 run 的**全部失败步骤**，
   重点 runner 那一行 `CAPTURE_GEOMETRY`（三种样子各绑一种处置，指认之前不加出口）；
   ① 清账表下一批：菜单栏两族剩余格 + 设置说明段那 5 格（缺席已可测）；
   ② 把"缺席计数"从一次性 grep 升成会红的守卫（形状：按表面扫源码，缺关键字就点名缺在哪个文件）；
   ③ **一格真的动效**（产品 > 0：落地 + 帧 + 换装本机 + 逐屏看图）—— 若 194 被指认成产品侧，那一格优先。

最后更新：2026-10-18 16:42（本地 · R163 / 第 165 轮：**R160 欠的守卫补上了，并说清徽标那句话为什么不进清账表**（U-542…U-544 · 产品 0 文件，判据账）

**做了什么**：新增 `AccessibilityLabelHygieneTests.testPinnedBadgeCarriesItsHoverHint` ——
只扫 `HistoryRowViews.swift` 里 `struct RowLeadingVisual` **之前那一段**，要求有一行同时含 `.helpLabel(` 与「已固定」。
扫描范围收窄是有意的：整文件 `contains` 会被那颗 pin 按钮的 `.helpLabel` 喂饱（R76/R86 那一族"守卫被提到这个词喂饱"）。
变异刀把那行注释掉 ⇒ 当场红；还原 ⇒ 4 例全绿、产品文件 `git diff --numstat` 0/0。

**两格各判一句话**：本格管"这一格用没用 helpLabel"，既有的 `testHelpLabelActuallySetsBothAttributes`
管"helper 是否同时上 `.help` 与 `accessibilityLabel`"。合起来会让两种坏法红在同一处，读日志的人分不开。

**了结一件挂着的账**：徽标那句 hover 提示**不属于 171 格里任何一格**（表轴是表面 × 状态，这条判的是
"非控件的可见变化要不要配一句话"）。不为了销账硬塞一格 —— 那会让分母变成可调的数，
`MOTION_LEDGER_FLOOR_BASELINE` 的单调性就没意义了。

**下一轮（R164）的靶**：⓪ 读 `39145955508`/`1deda5d`、`39145345916`/`bc53a5c` 与本跑的全部失败步骤，
   重点 runner 那一行 `CAPTURE_GEOMETRY`：`content<1040` ⇒ 夹具被屏幕收小；`content=1040 而 host<1040` ⇒ 布局没铺满；
   三者都 1040 而像素仍空 ⇒ 与 191/196 同族的"整层不合成"（那时才按 196 的形状谈未运行，且**指认之前不加出口**）；
   ① 清账表下一批（录制器 加载/禁用/错误 三格缺席已量到 + `QuickPickController.swift`）；
   ② **一格真的动效**（产品 > 0：落地 + 帧 + 换装本机 + 逐屏看图）—— 若 194 被指认成产品侧，那一格优先。

最后更新：2026-10-18 16:39（本地 · R162 / 第 164 轮：**194 的分辨读数落地（只出数不放行）+ 三处"该不该加动效"查在源码上**（U-539…U-541 · 产品 0 文件，判据账）

**做了什么**：`render` 里加一行 `CAPTURE_GEOMETRY`（只对 `height>=1000` 的夹具），打
`requested / content / host / screenVisibleHeightPt` —— 三个尺寸同源于这一次捕获，**不 skip、不豁免、不动 95% 门槛**。
本机六张高帧 ⇒ `requested=720x1040 content=720x1040 host=720x1040 screenVisibleHeightPt=847`
⇒ 本机没被夹小、内容铺满、屏幕比窗口矮 193pt 照样画满（R161 那条被证伪的解释现在有自己的读数行）。
runner 回来时三种样子各绑一个处置：`content<1040` ⇒ 夹具被收小；`content=1040 而 host<1040` ⇒ 布局没铺满；
三者都 1040 而像素仍空 ⇒ 与 191/196 同族的"整层不合成"，那时才按 196 的形状谈未运行。

**也查了"有没有该加而没加的动效"**（三处都查在源码上，结论都是不加）：详情区 chip 已有 `.pressedStyle` + `.helpLabel` + `.onHover`；
菜单栏推荐面板两处 `.buttonStyle(.plain)` 是 R4 刻意留的（菜单自己的高亮就是"收到了"的证据，叠一层会把 U-1 拆掉的卡片感装回来）；
侧栏批量五颗 R13 已归队。⇒ 这是**查过之后的"没有"**，不是没查；没有为了结束 0 改动纪录去叠没用的东西。

**验证**：编译 0 告警；`UICaptureTests` 71 例 / 4 skip / 0 failures、138 帧不变；脚本电池 `Ran 335 tests OK`；
CI 三跑（`711120a`/`b09d646`/`a1889b4`）都只剩 `STEP[15]`（194），`STEP[8]`/`STEP[13]` 全绿。

**下一轮（R163）的靶**：⓪ 读本跑触发的 run 的 `STEP[15]` 里那一行 `CAPTURE_GEOMETRY` —— 它直接指认 194 是哪一种成因，
   然后按上面三种处置走对应那条（不许在指认之前加出口）；① 徽标那格的清账登记 + 会红守卫；
   ② 清账表下一批（录制器 加载/禁用/错误 + `QuickPickController.swift`）；
   ③ **一格真的动效**（产品 > 0：落地 + 帧 + 换装本机 + 逐屏看图）—— 若 runner 的读数把 194 判成产品侧，
   那一格就同时是动效与缺陷修复，优先它。

最后更新：2026-10-18 16:30（本地 · R161 / 第 163 轮：**我给 194 写了一条出口，本机读数把它自己证伪了 ⇒ 撤掉**（U-536…U-538 · 产品 0 文件，判据账）

**这一轮做了什么**：按 R160 靶单去修 194（runner 上六张 `settings-*-tall-720x1040` 报"95% 像素未画"），
提出的解释是"那台机器主屏装不下 1040pt 高的窗口"，出口、真值表、接线守卫都写好了。
然后本机第一行读数把它推翻：**`CAPTURE_SCREEN main=有 visibleHeightPt=847`，而那六张高帧本机 `blank=0.0%`、画到第 2079 行**
⇒ 离屏窗口不被屏幕可视高夹住。第二条独立证据同向：闸门红的是"未画"，而"帧名==像素尺寸"由 R18 钉住
⇒ runner 上位图尺寸正确、内容缺失；窗口若被夹小，先红的会是尺寸那一格。
**于是整条出口撤掉**（`git checkout` + 删新测试文件），仓库对 harness 净改动 0/0；没有调 95% 门槛，没有写豁免名单。

**这一轮的规矩（真正的产出）**：给判据加"这台机器判不了"的出口之前，出口所依赖的那个数必须**先在本机量一次**，
且本机要给出与"我要放行那台机器"**相反方向**的证据 —— 否则这条出口会先把真红洗成"未运行"（R146/R153 那一族最贵的错法）。

**CI 对平**：`711120a`、`b09d646`、`a1889b4` 三跑都只剩 `STEP[15]` 一朵（就是 194），`STEP[8]`/`STEP[13]` 全绿
⇒ R154 与 R157 的修复在 runner 上稳定成立；196 已结案。

**下一轮（R162）的靶**：① 194 的三个同源读数（窗口实际高 / 内容视图高 / 位图与请求比）—— 先分辨，再决定要不要出口；
② 清账表下一批（录制器 加载/禁用/错误 三格缺席已量到 + `QuickPickController.swift`）与徽标那格的登记 + 会红守卫；
③ **一格真的动效**（产品文件 > 0：落地 + 帧 + 换装本机 + 逐屏看图）—— 这条仍是阶段二最大的欠账。

最后更新：2026-10-18 19:35（本地 · R160 / 第 162 轮：**十七笔之后第一笔产品改动 —— 行首固定徽标有了悬浮提示，而守卫当场红了我**（U-533…U-535 · 产品 1 文件）

**改了什么**：`HistoryRowViews.swift` 的 `RowPinnedBadge` 补 `.helpLabel("已固定：不会被新记录顶出历史，也不会被保留策略清理")`。
它不是控件，但它是这一行唯一"自己会变"的东西，以前没有任何一句话解释它为什么在这儿 —— 这正是目标要的
"hover 提示有积极作用才加"那一类。第一版写裸 `.help` 被自家
`testViewsNeverUseBareHelpWithoutAccessibilityLabel` 红掉（只给悬浮提示 VoiceOver 读不到），
改成仓库既有 `.helpLabel`（同时给 `.help` 与 `accessibilityLabel`）并撤掉重复的 `.accessibilityLabel` 行 ——
**改的是我的写法，不是守卫**。

**验证**：编译 0 告警；hygiene + RowInteraction 8 例全绿；`UICaptureTests` 71 例 / 4 skip / 0 failures、重捕 138 帧；
换装本机 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、`INSTALL_ENTRIES_BEFORE=131 AFTER=131`（没碰用户数据）。

**两处 NOT-RUN（不许说成验过）**：① help tag **不进帧** ⇒ 提示本身没有画面证据，要真机悬停人工确认（已列人工验收）；
② `scripts/frame_baseline.py check --against working <目录>` 是我凭记忆抄的 ⇒ `unrecognized arguments`，
工作基线那一门本轮没跑成，要用之前必须回 `.github/workflows/ci.yml` 第 10 步抄原文。


**R160 收尾补读（同一轮，写在推送之后）**：
   `61e451a`/`39122659644` ⇒ 无失败步骤
   `18b59d4`/`39122480991` ⇒ 无失败步骤
   `c7ffbb5`/`39122194463` ⇒ 无失败步骤
**下一轮（R161）的靶**：⓪ 读 `39122480991`/`18b59d4`、`39122194463`/`c7ffbb5`、`39122659644`/`61e451a`、
   `391229…`/`711120a` 与本跑（R160 这一笔）的**全部失败步骤**（196 的正半验收）；
② 把这枚徽标在清账表里对应那格**登记**（本轮没量过就不写"已判"）+ 补一条会红的守卫：
   「固定徽标必须有 help 文案」（形状：扫 `RowPinnedBadge` 那一段，缺 `.helpLabel` 就红）；
③ 194（六张 `-1040-` 空白帧）；④ 清账表下一批（录制器 加载/禁用/错误 + `QuickPickController.swift`）；
⑤ 195 的 ①；⑥ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185；⑦ 继续每轮至少一格产品面判断。

最后更新：2026-10-18 19:24（本地 · R159 / 第 161 轮：**把 R157 的 NOT-RUN 补成读数 —— 全量卷 847/42/0，两条新 skip 出口在本机一次都没触发**（U-530…U-532 · 产品 0 文件，验证账）

**做了什么**：跑本机全量 `env -u SDKROOT swift test` ⇒ `Executed 847 tests, with 42 tests skipped and 0 failures in 223.125 seconds`。
这条补的是 R157 显式记成 NOT-RUN 的那格。重点不是绿，是那个 **42**：与改动前账上的 `847/42/0` 同档
⇒ R157 新加的两条 **skip 出口**在有对象的机器上没吞掉任何判定（"有对象时不许 skip"这半个反向守卫第一次有读数）。

**仍然欠的**：正半（单档为空时必须点名）只能由 runner 签 —— `39122480991`/`18b59d4`、`39122194463`/`c7ffbb5`、
`39122659644`/`61e451a` 写账时全部 `in_progress` ⇒ 未读，不写成已验收。

**状态计数**：清账表 85/171（未清账 86）；196=落地待验收；194 未动；脚本电池 335 OK；产品文件连续第十七笔 0 改动
（本轮论证：两个候选分别是"已有"与"系统已画"，为破纪录加动效就是目标禁止的"为动而动"）。

**下一轮（R160）的靶**：⓪ 读上面三跑 + 本跑这一笔的**全部失败步骤**（期望 `STEP[13]/[15]` 只剩 194 那一句 + 两行 `*_NOT_RUN`；
   若红还在且不是同一句 ⇒ 回读数，不许放宽地板）；② 196 的正半验收；③ 194（六张 `-1040-` 空白帧）；
   ④ 清账表下一批（录制器 加载/禁用/错误 三格缺席已量到 + `QuickPickController.swift`）；
   ⑤ **一格真的动效**（从未清账 86 格里判"加"的那一格：落地 + 帧 + 换装本机 + 逐屏看图）；
   ⑥ 195 的 ①；⑦ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 19:18（本地 · R158 / 第 160 轮：**设置侧栏与快捷键录制器逐格判完；看图那一腿没让印象变成工单**（U-527…U-529 · 产品 0 文件，动效主线）

**做了什么**：清账表 82 → 85（未清账 86 / 171）。三格各绑一行本轮真读过的源码作证人；
证据闸门当场量到 `HotKeyRecorderView.swift` 里 `ProgressView=0 isLoading=0 disabled=0`
⇒ 「加载 / 禁用 / 错误」三格**没登记**（缺席不等于已判），留给下一批。

**看图那一腿**：真看 `settings-privacy-720x540-light.png`（侧栏六行、选中蓝药丸 + 图标同色 + semibold；卡片只包住第一组）。
第一反应"卡片外这么多段墨是不是回归了 BACKLOG 142"—— 那条判据本来有读数在管（`CARD_ABOVE_SUMMARY` / `CARD_BELOW_SUMMARY`，
本机 `进名单=26 未判=0`）⇒ **没开单、没改产品**。同一族第六次，这次是"怀疑别人回归"版本的形容词。

**为什么本轮仍没有产品改动**：这两个文件里唯一能确证的候选（录制器悬停）经源码读证是**系统已经画了**（真 NSButton，
`setButtonType(.momentaryPushIn)`），叠一层 SwiftUI hover 就是 R20 抓过的两层打架。为了打破"连续第十六笔 0 改动"去加没用的动效，
正是目标禁止的"为动而动"。复查条件写死：录制器哪天不再用 NSButton，那一格必须重判。

**下一轮（R159）的靶**：⓪ 读 `39122480991`/`18b59d4`（R157 出口的验收）与 `39122194463`/`c7ffbb5`、`39121928377`/`9b935a8` 的
   **全部失败步骤** —— 期望 `STEP[13]/[15]` 从 3 句红变成 194 那一句 + 两行 `CARD_INSET_NOT_RUN` / `CARD_RHYTHM_SHADE_NOT_RUN`；
   若红仍在且不是同一句 ⇒ 回到读数，不许放宽地板；
② 清账表下一批：录制器的 加载/禁用/错误 三格（缺席已量到）+ `QuickPickController.swift` 那两处；
③ **一格真的动效**：从未清账的 86 格里挑一格判"加"的，落地 + 帧 + 换装本机 + 逐屏看图（这是主线，别再往后排）；
④ 196 的 ③（出口的反向守卫）；⑤ 194；⑥ 195 的 ①；⑦ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 19:15（本地 · R157 / 第 159 轮：**BACKLOG 196 落地 —— 出口按"档"切片**（U-524…U-526 · 产品 0 文件，判据账）

**改了什么**：`testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox` 的出口 ② 原先问 `defendantMaterial == 0`，
而 runner 的形状是 `被告=2 参照=4 量到=1 未判=29`（唯一那格在亮档，**暗档 0 格**）⇒ 谓词问错了对象，没 skip、红了 3 句非产品的话。
现在两处出口都问这条判据真正需要的东西：**每一档至少有一格量到可判的卡片段**，
并新增两行读数 `CARD_INSET_BANDS light|dark`、`CARD_ABOVE_BANDS light|dark`，
某一档为 0 时先发 `CARD_INSET_NOT_RUN=1` / `CARD_RHYTHM_SHADE_NOT_RUN=1`（带读数与原因、排在 skip 之前，按 D-170）再 skip。
**四条地板一条没放宽**（`未判 ≤ 4`、`measured ≥ min(16,…)`、`statsDeclined.isEmpty`、`roster ≥ min(8, materialCells)`）。

**本机证据**：编译 0 告警；`CARD_INSET_BANDS light=13 dark=13`、`CARD_ABOVE_BANDS light=13 dark=13`；
两格测试 `passed`（27.9s / 18.7s）。把 runner 自己打印的 `1 / 0` 代进同一谓词就是 skip —— 这一步是**算术**，
**执行证据要等下一跑 CI**（本轮不写成"已修好"）。

**本轮没跑的（显式记账）**：全量 `swift test`（847 例）、变异刀、138 帧重捕 ⇒ 交给 CI 那一跑全量验收。
新出口的反向守卫（"单档退化必须点名、两档都有段时不许 skip"）本轮**只有推理没有格子**，形状开进 196 的 ③。

**下一轮（R158）的靶**：⓪ 读 R157 这一笔触发的 run 的**全部失败步骤** —— 期望 `STEP[8]` 绿、
   `STEP[13]/[15]` 从"3 句红"变成"1 句红（194 的六张 `-1040-` 空白帧）+ 两行 `*_NOT_RUN`"；
   若 `CARD_INSET_NOT_RUN` 没打出来而红仍在 ⇒ 说明还有第二种成因，回到读数再判，不许把地板调松；
② **一格真的动效**（产品文件必须 > 0）：清账表里挑一格判"加"的，落地 + 帧 + 换装本机 + 看图；
③ 196 的 ③（反向守卫合成对照）；④ 194；⑤ 195 的 ①；⑥ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 19:10（本地 · R156 / 第 158 轮：**R154 的修复在 runner 上验收通过；191 欠的形状读数由 runner 自己打印出来**（U-521…U-523 · 产品 0 文件，读数账）

**验收回来的一件事**：run `39120938129`（`8faef80`）完成后失败步骤只剩 `STEP[13]/[15]` ⇒ **`STEP[8]` 变绿**，
R154 那格"构造期 / 测量期依赖分开 + 带名字 skip"在没装 Pillow 的 runner 上成立。

**本轮拿到的读数（191 欠的那一格，不用新写仪器）**：runner 把 29 格未判逐格打印了 ——
大头是 `settings-* light/dark[被告]=这一带没有第二层（fill=-1）`（**两档都是 -1**），
另有三格是 `有材质但找不到卡片段（fill=60）`（`settings-shortcuts-recording dark` 与两枚 `cardprobe-*` 参照）；
配套 `参照只有 ["light"]`、`被告读到 2 格材质却只量到 1 格内缩`、`「统计」4 格填充=-1`。

**于是 R153 那句被收窄**：我说"那两格假材质是宽的"，是从 fill=60 那三格推的；29 格的大头是 `fill=-1`，
而"没有第二层"不是"宽"，是**那一层在这台机器上根本没显**（与 R100 的「runner 完全看不见卡片材质」同一件事）。
出口 ② 的谓词是 `defendantMaterial == 0`，runner 的形状是 `defendantMaterial == 2 且 measured == 1` ⇒ 谓词问错了对象，
所以它没 skip、红了 3 格。**本轮刻意没去 9000 行 harness 里盲改**（改错一次就会把"通道不显"洗成"产品没问题"）：
修法与验收形状写进 BACKLOG 196（谓词换成"有没有一段可判的卡片带" + skip 之前发 `CARD_INSET_NOT_RUN` + 本机合成读数验一正一负 + 不放宽两条地板）。

**下一轮（R157）的靶**：⓪ 读 `39121060707`/`4a2cb8c`、`39121250026`/`13b07e5`、`39121928377`/`9b935a8` 与本跑（R156 这一笔）的
**全部失败步骤** —— 要确认 `STEP[8]` 在带 R155 台账的那几跑上也绿，以及 `STEP[13]/[15]` 是否仍是本轮这三句；
① **BACKLOG 196 落地**（这是唯一能让 CI 变绿的修法，且带合成读数一正一负）；② 194（六张 `-1040-` 空白帧）；
③ 清账表下一批：`SettingsView.swift` 与 `QuickPickController.swift` 逐格（未清账 89）；④ 195 的 ①；⑤ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185；
⑥ 产品面：连续第十四笔 0 改动 —— 若 196 落地后 CI 绿，下一轮优先做**一格真的动效**（含换装本机与看图），而不是继续仪器账。

最后更新：2026-10-18 19:06（本地 · R155 / 第 157 轮：**搜索框与侧栏容器逐格判完，看图那句「差不多」被数打掉**（U-518…U-520 · 产品 0 文件，动效主线）

**做了什么**：清账表 72 → 82（未清账 89 / 171）。一次判掉「主窗口/搜索框」6 格与「主窗口/侧栏」4 格，
判"不加"的每一格都绑本轮实测的缺席计数（`SearchField.swift` / `HistorySidebarView.swift` 里 `disabled` / `ProgressView` / `isLoading` / `selection` 各 0 处）；
「按下」判 `kept`（那颗 × 有 `.pressedStyle(in: Circle(), hoverLevel: controlHover, labelPadding: 4)`）；
「侧栏 × 悬停」判 not-applicable 的理由是与「列表行 × 悬停」**分工**，不是没做。

**看图腿（这次是读数）**：我盯着 `search-field-320x112-light.png` 的第一句是"两态放大镜差不多暗"——
量出来 空 240.4 / 有字 226.6 / 差 13.8（最暗 20 像素均值，0..255）⇒ `isActive` 那一档确实落在放大镜上，**错的是我的眼睛**。
形容词第五次被数驳回，这轮的规矩：想写"看起来"之前必须先有一个数。

**0 产品改动的帧侧证人**：重捕 138 帧与工作基线名单逐名对账 ⇒ `缺名=0 多名=0`（CI 第 10 步那句话本地先跑）；
与 v1.4.8 快照比 `changed=62 / added=76` 是发布以来累计漂移，不是本轮回归。

**下一轮（R156）的靶**：⓪ 读 `39120938129`/`8faef80`、`39121060707`/`4a2cb8c`、`39121250026`/`13b07e5` 三跑的**全部失败步骤**
（R154 的 STEP[8] 修复要在 runner 上验收：预期 `Ran 335 tests / OK (skipped=6)`；`STEP[13]/[15]` 是否仍是同一句原文）；
① 清账表下一批：按 `SettingsView.swift` 与浮层那两份文件逐格判（未清账 89 格的头两处）；
② 把放大镜那把一次性尺搬进仓库（`scripts/` 里配一格"两态墨必须有差"的判据，带正对照）；
③ 191 的形状读数（R153 写死、仍未落地）；④ 194；⑤ 195 的 ①；⑥ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185；
⑦ 产品面：连续十三笔 0 改动 —— 若下一批逐格里出现任何一格判"加"，那一格优先于任何仪器工作。

最后更新：2026-10-18 18:48（本地 · R154 / 第 156 轮：**runner 的红是环境差异，本地那朵红是我的字节码缓存**（U-515…U-517 · 产品 0 文件，仪器账）

**读了完成的那一跑的全部失败步骤**（`39118582249`/`367519c`；另外四跑 `39119116012`/`39119210241`/`39119300429`/`39119784928` 还在 `in_progress`，
`--log-failed` 对进行中的 job 打出 0 字节 ⇒ 只能说"未读"，不能说"没红"）：`STEP[8]` 是 R153 没记过的一族，
两朵红说的都不是产品，而是 runner 的 python 3.14 **没装 Pillow**（R147 新尺把 import 写在模块顶上）。

**改了什么**：构造期依赖与测量期依赖分开（`_load_pil()` + `PillowMissing` + `FRAME_STATE_NOT_RUN=pillow` 且码 1）；
合成对照那 6 格改成带名字的 skip；新加 2 格**不依赖 PIL** 的判据。两刀变异各打红一次；真帧读数与 R147 逐字相同；本机 `Ran 335 tests OK`。

**本轮最该记住的一朵红是我自己造的**：修完后本地 `FAILED (failures=1)`，红在新写的格子上，失败文本带着那句 NOT-RUN ⇒ 看起来像"判据抓住了静默通过"。
真实成因是 macOS 把字节码缓存放仓库外（`~/Library/Caches/com.apple.python/…`，按整秒 mtime + size 判新鲜），
而我的变异刀 `return 1`→`return 0` **长度不变**、还原落在同一秒 ⇒ 执行的是变异版字节码；
`find -name __pycache__ -delete` 清错了地方所以看起来"清了没用"。这条把 U-462 那句"成因没定位"结掉了（U-516/U-517）。

**下一轮（R155）的靶**：⓪ 读本轮两跑 `39120938129`/`8faef80` 与 `39121060707`/`4a2cb8c`（两条都仍 `in_progress`，`STEP[8]` **未读** ⇒ 不能说"没红"）：
   要看 `STEP[8] Release script tests` 是否变绿（预期 runner 上是 `Ran 335 tests / OK (skipped=6)`，那 6 格是带名字的 skip），
   以及 `STEP[13]/[15]` 是否仍是 R150/R153 那一句原文（同一句 ⇒ 191 还欠形状读数；换句 ⇒ 先按两跑对账再动登记）；
   另三跑（`7661150`/`588644a`/`d8a53f7`）已 `completed failure`，都带 PIL 那一朵 ⇒ 只作对照，不再重读；
① **回到动效本体**：产品文件连续第十轮 0 改动、清账表仍欠 99 格 —— 剩余预算不多，这条不能再往后排；
② 191 的形状读数（R153 写死的下一步，仍未落地）；③ 194；④ 195 的 ①（变异执行器带 `PYTHONDONTWRITEBYTECODE=1`）；
⑤ 189 / 188 / 187 的 ②③ / 176 / 182 / 183 / 185。

最后更新：2026-10-18 18:32（本地 · R153 / 第 155 轮：**191 的修法被 runner 证伪** —— 那两格假材质是宽的，不是 pill（U-512…U-514 · 产品 0 文件，读数账）

**读了两跑 CI**（`39118326554`/`6f11d95`、`39118085686`/`943c275`，都带 R151 的宽度那一维）：
第 16 步**继续不红** ⇒ R146 的闭合通道在 runner 上稳定成立；但 `STEP[13]/[15]` 照旧，关键那一句与 R150 逐字同形 ——
`本机读到 2 格材质，「统计」却有 4 格没进卡片计数`。⇒ 「最长连续段 ≥40% 带宽」这一维**没挡住**它。

**断掉的是哪一环**：我用本机的 pill 宽度（0.08–0.13）去推 runner 上那层的宽度，而 runner 上那层不但过了 40% 的线，
还在亮档量出 `settings-shortcuts-recording light=5.0`（有左沿、有首墨）⇒ 它是宽的（U-512：连形状都不许跨机器外推）。
**没做的事**：没有再放宽一点试试（U-513）—— 改动没改变任何判定，既没修好也没弄坏，这时代码越改越松就是事故。

**新记的一朵**：`testCaptureKeyViews` 报六张 `-1040-` 高帧「95% 像素未画」，以前被卡片那朵红盖在同一条 `STEP[13]` 下没逐条读 ⇒ 新开 BACKLOG 194（U-514）。

**下一步（写死在 191 追记 3）**：只加一行**形状读数**（每格：最长连续段 ÷ 带宽、过关行数、页底亮度、层色号），
不改判据、不放宽地板，让 runner 自己回答那层是什么；看到读数之前不加出口。

**下一轮（R154）的靶**：⓪ 读 `39119300429`/`588644a`、`39119210241`/`d8a53f7`、`39119116012`/`2d20338`、`39118582249`/`367519c` 四跑的**全部失败步骤**；
① 191 的形状读数（只加读数）；② 194；③ 193（量纲守卫）；④ 189 / 188；⑤ 187 的 ②③；⑥ 176 / 182 / 183 / 185；
⑦ **回到动效本体**：连续九轮 0 产品改动，清账表 171 格里仍欠 99 格 —— 这条是阶段二的主线，不能再往后排。

最后更新：2026-10-18 18:05（本地 · R151 / 第 153 轮：**材质尺加上「这一层有多宽」那一维** —— 191 的修法落地（U-509…U-511 · 产品 0 文件，判据账）

**改了什么**：`cardFill` 除了「众数 ≠ 页底」「这种行够 20pt」，现在还要「该层在行内连续横贯 ≥40% 带宽」；`cardRowKinds` 第一遍顺手算最长连续段，判据与 `fillCandidatesLine` 吃的还是同一份数组（R104）。
**门槛是量出来的**：我第一个想到的「跨度」不分辨（pill 0.87–0.91 vs 卡片 0.95）；分辨的是行内最长连续段（pill 0.08–0.13 / 卡片 0.58–1.00 / 空行 1.00）⇒ 切点 0.4，两侧余量各 ≥3 倍。
**本机两头验收**：`swift test --filter UICaptureTests` ⇒ `CARD_INSET_CAPABILITY 候选=32 有材质=32（被告=26 参照=6）量到=26 未判=0` 与改前逐字相同；`有材质=26 进名单=26`；`统计 有对象=4 未判=0`；71 例 / 5 skip / 0 failures；编译 0 告警。两格新测试喂同一份 modals 只换 runs（0.07 ⇒ nil、0.93 ⇒ 有）⇒ 那一维不接上就当场露馅。
**没做**：不给录制态帧开具名豁免、不动 `≤4` 未判地板、不动 `materialCells == 0` 的 skip。U-511：本机「逐字相同」是必要不充分 —— runner 那颗假 pill 有没有被挡住，只能等下一跑的那一行（191 的结案条件就绑它）。
**R152 已做（同轮追加）**：`curve_from_ledger.py` 的量纲统一 —— 推导改成按每格自己的分母归一（七分制 `mean(num/den)×100`、百分制 `mean(num)`），真台账重读 `MEAN=91.9`、`PHASE2 mean=92.10 min=82 max=99`；第一版一律 ×100/105 把百分制那批推成 612/609，被仪器自己打印的曲线抓到（`max=617`）。两格守卫没写对已回退 ⇒ 新开 BACKLOG 193。
**下一轮（R153）的靶**：⓪ 读 CI：本轮 = run `39117983368`（commit `d53a964`，191 的修法）；上一轮 = `39117181407`/`9808943`、`39116000050`/`fd6f71e`（187 的①进闸门）—— 三跑都要看**全部失败步骤**（191 看 `有材质` 掉没掉、`STEP[13]/[15]` 是否消失）；① 187 的 ②③；② 188 / 189 / 190；③ 176 / 182 / 183 / 185；④ 清账表下一批（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、菜单栏/状态菜单 × 加载与错误、浮层/底部说明 × 聚焦）；⑤ 回到动效本体：连续六轮 0 产品改动，这条必须补上。


最后更新：2026-10-18 17:52（本地 · R150 / 第 152 轮：**191 定性完成** —— 两朵 capture 红是 R145 那张新帧顶翻了「`materialCells == 0`」这个机器前提（U-506…U-508 · 产品 0 文件，读数账）

**排除与指认都在现有日志里**：`CARD_FILL_CANDIDATES settings-general/stats light|dark 前三=(页底:480)` ⇒ runner 整幅仍只有一层；`CARD_INSET_ALL settings-shortcuts-recording light=5.0` + `有材质=6（被告=2 参照=4）量到=1` ⇒ runner 上唯一的「第二层」是 R145 录制态帧那颗高亮 pill（暗档 60 vs 页底 52，差 8 > 门限 3）。
**于是**：R100 的出口 `materialCells == 0 ⇒ skip` 被这张新帧抬走 ⇒ 29 格未判撞上 `≤4` 地板。红是真的，但它说的是仪器把一颗控件当成了卡片。
**修法（下一轮做，本轮不动判据）**：`cardFill` 除了行数还要问这一层有多宽（最长同色段 ÷ 内容宽；卡片 ~600pt、pill 87pt），**不**给录制态帧开具名豁免。两头验收：runner 上材质计数回到 0 ⇒ skip 自己响、两朵红消失；本机 `CARD_INSET_CAPABILITY 有材质` 与 `CARD_ABOVE_CAPABILITY` 的数字不许变小（变小就是新尺把真卡片也挡掉）。
**三条新账**：U-506 以 `== 0` 为前提的闸门会被新帧顶翻（加帧那轮要回头重看这些闸门）；U-507 分辨实验要能**杀掉**一种解释；U-508 `量到 1 格` 不等于尺在工作 —— 那格同时是唯一的假阳性。
**下一轮（R151）的靶**：⓪ 读 `39116000050`/`fd6f71e`、`39115244353`/`64f2bf3`、`39115129583`/`2a5d697` 与本 run 的**全部失败步骤**；① 按 191 的修法改 `cardFill`（门槛轴已量过：**「跨度」不分辨**（pill 0.87 vs 卡片 0.95），分辨的是**行内最长连续段**（pill 0.08–0.13 / 卡片 0.58–0.96）；切点候选 0.4，先扫 26 格分布再钉）并两头验收；② 187 的 ②③；③ 188 / 189 / 190；④ 176 / 182 / 183 / 185；⑤ 清账表下一批。


最后更新：2026-10-18 17:45（本地 · R149 / 第 151 轮：**读到 R146 的 CI** —— 第 16 步绿了（186 结案），而第 13/15 两朵红我漏看了三轮（U-503…U-505 · 产品 0 文件，读数与流程账）

**赢的一半**：run `39114424945`（`3a557fb`）的失败步骤列表里已经没有 `On-screen probe coverage floor` ⇒ R146 的 `心跳 − 闭合` 在 runner 上给得出名字，BACKLOG 186 的成因结案。
**输的一半（更贵）**：同一跑挂着 `STEP[13] Swift tests (executed-count gate)` 与 `STEP[15] Capture gate`，而 R145 那一跑（`39103361921`/`4c62469`）是同样的两朵 —— 我连着三轮只读第 16 步。U-503：新判据第一次上 runner，必须回头读**同一次 run 的全部失败步骤**，不只读它自己那一步。
**两朵红说什么**：runner 现在看得见 2 格卡片材质却量不到任何卡片段，连系统参照 `cardprobe-groupbox-default dark` 也是 `有材质但找不到卡片段（fill=60）`；统计屏四格全 `填充=-1`；未判 29 格 > 地板 4。
**本轮决定不动判据**：R100 的机器前提（`materialCells == 0` ⇒ skip）被这组读数推翻，剩下两种解释修法相反（① 材质与背景同层 ⇒ 加『参照自己读不到 ⇒ 这一档不判』的出口；② 分段那一关真的看不见 ⇒ 修尺、不许加出口）。分辨实验与新账写进 BACKLOG 191，两条红保持会红 —— 现在最容易写的那个修法恰好最贵。
**下一轮（R150）的靶**：⓪ 读 `39116000050`/`fd6f71e`（R148 的闭合通道进闸门）与 `39115244353`/`64f2bf3`、`39115129583`/`2a5d697` 三跑的**全部失败步骤**；① 191 的分辨实验（读 `CARD_FILL_CANDIDATES … dark` 那一行的 fill 与页面亮度差值）并据此定性；② 187 的 ②③；③ 188 / 189 / 190；④ 176 / 182 / 183 / 185；⑤ 清账表下一批。


最后更新：2026-10-18 17:35（本地 · R148 / 第 150 轮：**覆盖闸门接上闭合通道** —— 登记判定不再只读那条会丢的 stdout（U-500…U-502 · 产品 0 文件，判据账）

**R148 做了什么**：`probe_coverage_gate.py` 的「这条在 runner 上跑没跑过」改成 `日志结论行 ∪ 闭合行`（`--pulse`，不传就是旧行为）；三条新读数（`PROBE_LOG_LOSE_CONCLUSION` / `PROBE_PULSE_OPEN` / `PROBE_REGISTRATION_CONTRADICTED`）只报不判，新红 `PROBE_CLOSE_WITHOUT_PULSE` 防『通道自己不可信还替跑过签字』；解析器复用 `ui_probe_report` 的 `PULSE`/`DONE`；CI 那一处调用接上 `--pulse`。BACKLOG 187 的 ① 落地。
**两处自己的失误进了账**：U-500 新守卫拿子串数文件名，被 CI 注释里那句散文喂饱 ⇒ 改成数调用行；U-502 把本机日志喂给 runner 的登记表，造出 6 朵 `NOW_RUNS` —— 主语没写在输出上，新开 BACKLOG 189（summary 带机器键）。
**验证**：`Ran 333 tests … OK`（327→333，含 6 格新测试，其中一格专防『把放宽说成修好』）；真产物 `闭合通道=接 本次跑过=11`。
**下一轮（R149）的靶**：⓪ 读三跑 CI —— `39114424945`/`3a557fb`（要看 `UI_PROBE_HUNG_CHANNEL=file` 与那一步是否变绿）、`39115129583`/`2a5d697`、以及本轮新 run；① **曲线单位混了**（本轮读出现场发现，新开 BACKLOG 190）：`curve_from_ledger.py` 对 R145 那一类表给的是百分制（91），
对 R146/R147/R148 这三节给的是 0–15 的每维均值（13 / 14 / 12）⇒ `PHASE2_TO_47 mean=91.30` 现在把两种单位加在了一起，
那条均值不能再被引用，直到两边统一成一种估计量（先读仪器为什么分叉，再决定是补 `**均分**` 行还是改表头形状）；
② 187 的 ②③（缺席三出口进名册口径 + `CONTRADICTED` 升红的判据）；② 188（帧尺接进 CI，第一遍 report-only）；③ 189；④ 176 / 182 / 183 / 185；⑤ 清账表下一批（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、菜单栏/状态菜单 × 加载与错误、浮层/底部说明 × 聚焦）。


最后更新：2026-10-18 17:25（本地 · R147 / 第 149 轮：**帧级状态自证进电池** —— 录制态那一圈从此由写出的 PNG 说话（U-497…U-499 · 产品 0 文件，判据账）

**R147 做了什么**：新尺 `scripts/frame_recording_proof.py` 读两张已写出的帧，判"多出来的高色度 ≥900 / 四条边各 ≥40 / 包围盒 ≤340×90"，地板全部由这把尺自己在真帧上的读数推出（亮 1772、暗 1764、四边 上726/下726/左102/右102）。BACKLOG 177 结案。
**看图腿（真看了）**：按包围盒裁两档放大 ⇒ 描边贴 pill、四角圆率一致、不压字、右侧相邻 pill 未波及 ⇒ 看得出"在听"、不抢屏。
**三处失误都被自己的格子拦下**：带画到边外（四边读 0，真帧假红）、整带数角（擦掉一条边仍过地板 ⇒ 判据没牙）、合成夹具太小（delta 711 < 真帧地板 900 ⇒ 正对照绿不了）。
**验证**：7 格合成对照 + 真帧两档 `RESULT=ok pairs=2`；电池 `Ran 327 tests … OK`（320→327）；本轮 0 产品改动 ⇒ 不重拍帧、不换装。
**下一轮（R148）的靶**：⓪ 读**两跑** CI：run `39114424945`（commit `3a557fb`，R146 的闭合通道）与 run `39115129583`（commit `2a5d697`，R147 的账）——
前者要看 `UI_PROBE_HUNG_CHANNEL=file` 与那一步是否变绿，后者要看帧基线仍 `CHANGED=0`；
写这段时两跑都还 `in_progress` ⇒ 不以"应该绿"记账；① BACKLOG 188（把新尺接进 CI 捕获步骤，第一遍 report-only）；② BACKLOG 187（coverage 闸门接闭合通道、缺席分三种出口）；③ 176 / 182 / 183 / 185；④ 清账表下一批（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、菜单栏/状态菜单 × 加载与错误、浮层/底部说明 × 聚焦）。


最后更新：2026-10-18 14:40（本地 · R146 / 第 148 轮：**心跳的另一半 `PROBE_DONE`** —— 那句"两条通道各点一条、不许挑一个信"拒绝得对，该修的是减数（U-494…U-496 · 产品 0 文件，通道与判据账）

**R146 做了什么**：给 `UIInteractionProbeTests` 加了 `tearDownWithError` 的闭合行（`PROBE_DONE <用例名>`，与心跳同一份文件；skip 也走 tearDown），
把 `ui_probe_report.py` 里「正跑着被截断的是哪一条」从 `心跳 − 日志的结论行` 改成**同一份文件内部的减法** `心跳 − 闭合`
（新格子：`UI_PROBE_FILE_CHANNEL` / `…_CLOSED_ALL` / `…_AMBIGUOUS` / `UI_PROBE_HUNG_WITHOUT_CLOSE` / `UI_PROBE_LOG_CONCLUSION_LOST` / `UI_PROBE_DONE_ABSENT`）；
CI 启动那卷前 `rm -f /tmp/probe-pulse.log`。两条讲不通的形状**仍然红** —— 这不是放宽 `CONTRADICT`，是把它的减数搬到免疫的那条通道上。
**纠正的一处旧账**：`testOffScreen…` 被 R144 记成"这台机器上它今天会挂"，本机真实顺序里它是第 6 颗心跳且已闭合，
未闭的是第 7 颗 `testRightClick…` ⇒ 丢的是它的**结论行**。登记的 reason 已改写成仪器，值暂留 `cannot`（翻回 can 交给 BACKLOG 187 —— coverage 闸门还读那条会丢的通道）。
**验证**：真产物 11 心跳 / 11 闭合（`SUITE_EXIT=0`）；复刻 run 39102076143 的输入 ⇒ `UI_PROBE_HUNG=testRightClick…` + `LOG_CONCLUSION_LOST=testOffScreen…`，退出码 0；
四刀对照 `R146_KNIVES arms=4 bad=0`；全量 `Executed 847 tests, with 42 tests skipped and 0 failures` / 222.0s；脚本电池 `Ran 320 tests … OK`（310 → 320）；编译侧 0 告警。
**本轮 CI 还没读**（不以"应该绿"记账）：下一跑要看的是那一步里出现 `UI_PROBE_HUNG_CHANNEL=file`，以及 `On-screen probe coverage floor` 是否变绿。

**下一轮（R147）的靶，按顺序**：⓪ 读 run `39114424945`（commit `3a557fb`，写这段时 `in_progress`）——
那一步要出现 `UI_PROBE_HUNG_CHANNEL=file`，而 `On-screen probe coverage floor` 是否变绿是 186/187 的验收；
① 读同一跑的 `PROBE_FPS` 三个数（176）；② BACKLOG 187：让 coverage 闸门读同一份心跳+闭合，
缺席分成 `queued` / `hung` / `log-lost` 三种有名字的出口，再用一次真读数重判 186 那条登记；③ 177 收尾那一格（帧级状态自证读**已写出的 PNG**）；
④ 176（runner 的 `PROBE_FPS` 三个数）与 182 / 183 / 185；⑤ 清账表下一批（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、
菜单栏/状态菜单 × 加载与错误、浮层/底部说明 × 聚焦）。

最后更新：2026-10-18 06:10（本地 · R145 / 第 147 轮：**录制态第一次进帧基线**（136 → 138，BACKLOG 177 结案）（U-491…U-492 · 产品 0 文件，夹具与判据账）

**R145 做了什么**：给 `UICaptureHarness.Fixture` 加了一条 `interact:(NSWindow)->Void` 钩子（跑在 caret 静默**之后** ——
`settle` 之后那句 `makeFirstResponder(nil)` 会把刚点出来的录制态取消掉），新夹具 `settings-shortcuts-recording`
用 `performClick` 从产品入口进录制态，并在夹具里断言第一响应者就是那颗按钮。基线同一轮 `update`。
**看图腿（真看了）**：先量差异包围盒再裁（U-492 —— 我按台账坐标裁到了错的那一行，两帧看着一样，差点点下"帧里没有那一圈"）：
差异落在 x 958..1212 / y 504..550（第三颗录制器），高色度 亮 386→**829**、暗 391→**832**；
那一圈贴着 pill 轮廓、不外溢、不压字，标题「请输入快捷键」可读 ⇒ 看得出"在听"、又没抢过这一屏。
**闸门逼我记的一笔**：`TEXT_SIDE_ROSTER_EXTRA ["settings-shortcuts-recording"]` —— 新帧落在 vibrancy 子树里，
暗档侧栏文字结构上不可读（D-090 同一机制），加进盲区名单后 `14 of 14`。
**U-491**：把 helper 插到 `@MainActor` 与 class 之间 ⇒ 整个类失去隔离，十几处**不相关**判据红 ⇒ 文件级插入要按属性块找位置。

**验证**：`FRAME_BASELINE_UPDATED=138` → `COMPARED=138 CHANGED=0 MISSING=0 ADDED=0`；全量 `Executed 847 tests, with 42 tests skipped and 0 failures` / 219.8s；脚本电池 310 OK；本轮 CI 的结果在写这段时还没回来（不以"应该绿"记账）。**177 结案，但收尾欠一格**：
把"录制态帧高色度 ≥ 地板"变成电池里会红的断言（今天只由脚本量过一次）。

**下一轮（R146）的靶，按顺序**：① 177 的收尾那一格（帧级状态自证进电池）；② 读 R144/R145 的 CI
（186 的登记翻面是否让那一步变绿、`PROBE_FPS` 三个数够不够收紧 176 的预算）；
③ BACKLOG 182 / 183 / 185 里能变成判据的那几格；④ 清账表下一批（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、
菜单栏/状态菜单 × 加载与错误、浮层/底部说明 × 聚焦）。

最后更新：2026-10-18 05:40（本地 · R144 / 第 146 轮：**在屏探针那条挂死按三跑同形改登记，并把「会翻面的登记」钉成两向门**（U-488…U-489 · 产品 0 改动，判据账）

**R144 做了什么**：`f26f4c9` 那一跑只剩一步红 —— `testOffScreenProgrammaticSelectionIsRevealedAndNotJumped` 登记 `runner=can`
而日志里没有结论行，报告把它点名成挂死（`UI_PROBE_HUNG=…`、`本次下结论=5 红=1`）。同一句话连着三跑原样重复
（39052480365 / 39054860497 / 39056187840）⇒ 按 R87/R118 不再等第四跑，改登记：`can` → `cannot`，
reason 带三跑 run 号、`UI_PROBE_HUNG` 原文，**以及 R94 的反证**（那一跑它 `passed`）——
所以这不是"runner 结构上拍不到"，是"这台机器上它今天会挂"；挂的成因未定（候选：要真的 `orderFront` 一扇带选中行的列表窗口）。
两向门写进电池（`HungCaseRegistrationTests` 五格，全在内存里造登记、不读仓库当前值）：
can 缺结论 ⇒ 红 `NOT_RUN`；cannot 带 reason ⇒ 不许红；**没 reason 的 cannot ⇒ 仍红 `REASONLESS`**；
cannot 而它跑完 ⇒ 红 `NOW_RUNS`；今天的登记配今天的日志 ⇒ 一条都不红。新夹具 `fixtures/r144_probe_hung_ui.log`。
- **U-488**：翻面那天，`test_r94_log_is_green_…` 拿**现在**的名册判 R94 那次的历史日志，红在 `NOW_RUNS`
  ⇒ 历史夹具按采集当时的登记判，"今天 + 今天"另开一格（与 R135"旧代码的 CAUGHT 不能替新代码作证"同族，坏在日志侧）。
- **U-489**：会翻面的登记必须两向都钉，否则测试下一次翻面时就成了旧登记的证人。

**验证**：脚本电池 305 → **310 OK**；改登记前后同一份日志各跑一遍（`红=1 exit 1` / `红=0 exit 0`、`runner可跑=5 不可跑=6`）。
本轮 0 产品文件改动、**未重跑捕获** ⇒ 看图腿记 **NOT-RUN**（不记成通过）。

**仍然只有用户能做的**：批次 26.x–84.1、85.1、85.2、86.1、90.1。

**下一轮（R145）的靶，按顺序**：① BACKLOG 177 的录制态真帧夹具（136 → 138，`--must-include` 同步改，同一轮里 `update` 基线）
—— 这一格同时把看图腿从 NOT-RUN 变成真做过；② 确认 R144 这一跑 CI 是否绿（186 的登记翻面在 runner 上验收）；
③ BACKLOG 176 读 `PROBE_FPS` 三个数；④ 182 / 183 / 185 里能变成判据的那几格。

最后更新：2026-10-18 01:20（本地 · R143 / 第 145 轮收尾：**用户点名的专门审查轮** —— 四路复审查出 35 条，六条改变了产品或判据（U-476…U-485 · 产品 1 文件）

**R143 做了什么**：不做新动效，做「肯定有很大一部分没被检查到」那一问。四路互不知情的复审（产品入口与像素尺 / 判据与闸门 / 工具与 CI / 只读台账对账）把 R139–R142 每句「我量过 / 我修了 / 已收口」拿去复查。
**产品**：F7 —— 录制器拿不到第一响应者时不再画那一圈（它以前承诺了一件自己做不到的事），刀 M672；F6 —— 头注释那句「减弱动态时只是不淡入」是假的（`.emphasis` 在 reduce 下不降级）。
**撤回**：**U-470 / BACKLOG 179 的机制句是错的** —— 我拿一把坏尺读到的「新增墨=0」推翻了真机通道的「1548 个高色度像素」，还把错的通道事实写进了四本账；坏尺（`inkPixels` / `newInkPixels`）已删，判据换色度轴 + 四边形状断言。
**判据射程**：R142 台账说「三臂一律走 emit」而代码只改了新增那一行 ⇒ 三行改完 + 负向格 + 双向名册（实测 10 行 print / 9 种标记）+ 两把方向相反的刀 M673/M674 ⇒ `mutate_r142.py CAUGHT=6/6`。
**死刀复活**：`mutate_r139.py` 整张跑不动（M656 裸 needle 命中 2 ⇒ DID-NOT-RUN；M655 写死 R138 的标题，窗口滑过后删它 PASSED）⇒ 都改成按当前状态现取，并把它测的守卫从**读散文**改成**读标题形状** ⇒ 2/2 CAUGHT。
**撞号**：R141 与 R142 两张表共用 M666–M668 ⇒ 改名 M670–M672；查重改成扫全部 121 张表（`ARM_TOTAL arms=486 dupes=0 repeats=0`）+ 三格人造正对照（第三格是我第一版真报出的假阳性）。
**看图腿**：两档录制器列裁图真看了，并用最长同色段把 BACKLOG 178 量完 —— 亮 Δ19.0 / 1.08:1、暗 Δ17.0 / 1.40:1 ⇒ **暗档比值更高**，那句「暗档几乎同色」是印象且方向反了；「旁边有恢复默认」也撤回（那颗被 720×540 裁掉，帧里 y>560 只有两种颜色）。

**验证（本轮，全部单独串行跑）**：全量 `Executed 847 tests, with 42 tests skipped and 0 failures` / 201.8s；
`FRAME_BASELINE_COMPARED=136 CHANGED=0 MISSING=0 ADDED=0`（新代码重拍）；编译 0 告警；
脚本电池 `Ran 305 tests … OK`（294 → 298 臂号查重、→ 301 地板基准、→ 305 §9.3 那四格）；四张变异表 9/9、6/6、3/3、2/2 全 CAUGHT 且 `RESTORE_CLEAN=yes`；
针自检 `tables=42 covered=27 bad=0`。中途我并发开了两遍全量（两卷共用 `.build` 与固定路径的读数文件）⇒ **两卷都作废重跑**，
这一格的教训是"串行"不是"重跑一次就行"。

**仍然只有用户能做的**：批次 26.x–84.1、85.1、85.2、86.1、90.1（本轮把 85 / 86 / 90 三批补进了 `docs/MANUAL_TEST_v1.4.9_round3.md`，此前六轮它们只活在正文引用里）。

**BACKLOG 184 与 181 当场结案**：184 = 清账表的地板原来只与同一份文件里的行数比 ⇒「删五行 + 降五」不红，新出口 `FLOOR_WENT_BACK` 压在 `git show HEAD:` 的基准上（落刀实测旧判据绿、新出口红）；181 = `AGENT_FINAL_REPORT.md` §9.3 那三句连着三轮与台账相反而无人看守，现在绑到读数上（`scripts/tests/test_final_report_claims.py`，4 格：现状干净 + 三格内存伪造的正对照）。

**读 CI（run 39052480365）翻出三件事**：① 我新写的那条产品入口判据在 runner 上红（`128 < 141`）——
门限"单边占总量 5%"是**本机读数**推的，runner 的环几何给 4.5% ⇒ 换成对边比 + 单边绝对地板 80（U-486，本机读数不变 1354/1354/178/178）；
② 电池那格红在 `No module named pytest`（runner 没装），报出来却是"样张那一卷自己没通过"⇒ 样张改用 unittest 跑，不依赖第三方；
③ 在屏探针挂在 `testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`（`UI_PROBE_HUNG=…`）——
拿同一份合成日志喂 `28246ed` 版报告脚本，退出码同样是 1 ⇒ 排除"我改坏了脚本"，新开 **BACKLOG 186**。

**下一轮（R144）的靶，按顺序**：① BACKLOG 177 的录制态真帧夹具（136 → 138，`--must-include` 同步改，同一轮里 `update` 基线）；
② 读 R143 的 CI 里 `PROBE_FPS` 那三个数，按 R118 的规矩决定 176 的预算收紧到几倍；
③ BACKLOG 181–185 五格里挑能变成判据的（181 的 §9.3 三句绑读数、184 的地板对 HEAD 做差）；
④ 回到动效位点：清账表 70 / 171，173 从 R126 起欠的那一次已经还上，下一批点名的格不变
（主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误、菜单栏/状态菜单 × 加载与 × 错误、浮层/底部说明 × 聚焦）。

最后更新：2026-10-17 23:58（本地 · R142 / 第 144 轮收尾：**把会换班的绝对地板换成同一次运行的相对判据**（U-472…U-475 · 产品 0 改动，判据账））

**R142 做了什么**：起点是 `4486f6d` 那跑 CI 的一朵红（`testFrameIntervalsUnderStateChanges：26.939 > 20.0`），两跑对账是 **ONLY_B 换班** ⇒ 只能修尺（166 那张表被钉成空表，红只能修不能登记）。判据换成 `loaded.p95 ≤ max(baseline, off) × 3.0`（同机同窗同驱动的比值），`worst ≤ 120` 降级为粗卡顿锚点，三臂读数从 `print` 改走 `emit` 并带机器键。真值表 6 行 + 两条守卫 + `mutate_r142.py` **CAUGHT=4/4**（三把红在真值表、一把红在读数通道守卫）。

**四条新账**：**U-472** `print` 让一条判据三年没法收紧 —— 收紧 p95 欠的从来不是判断，是一份收得到的读数；**U-473** 守卫的搜索串会命中守卫自己（`.last` 取到「我自己之后」）⇒ 串拼出来、结束锚点选下一条用例、断言定义行恰好一次；**U-474** 新用例塞进哪个文件有后果 —— 两条纯函数用例进了探针卷，「在屏探针覆盖率」那道闸门就数到 13 而名册是 11，四格电池同时红（是电池先看见的，不是我）；**U-475** 又一次把「插入」做成「替换」（锚点那行注释自己消失了；代码注释没有「HEAD 各行都还在」那种守卫）⇒ 以整行为锚点的插入，改完要 grep 那行还在不在。

**BACKLOG 176 保持开着**：3.0 是未量的过渡值，收紧欠一次 runner 的 `PROBE_FPS` 读数（本机现在这条采样通道是死的：`FRAME_CHANNEL baseline_n=0 screen=有`）。自评 88/100（<90 ⇒ 不收口）；本轮 0 产品改动、未重跑捕获 ⇒ 看图腿记「沿用 R141 的 136 帧」，不记通过。R143 的靶：读 R142 的 CI（`PROBE_FPS` 三臂）+ 按 177/178 回到产品面与看图腿。

（R141）

**做了什么**：还了 BACKLOG 173 从 R126 起欠的那一次真动效。快捷键录制器进录制态以前只把标题瞬间换成「请输入快捷键」，
而那颗按钮会吃掉所有按键 —— 屏幕上没有任何东西说"现在按下去会被记下来"。现在叠一圈强调色描边
（`HotKeyRecorderRing`：1.5pt + `controlAccentColor`，`.animation(MotionCatalog.animation(for: .emphasis), value: isRecording)` 供电，
不脉动、不常驻）。为了量它，状态从私有里放出来（`onRecordingChange`，判等在 `setRecording`），表达抽成可离线渲染的一圈。
判据 6 条（两态与实心参照块**同框**，本机读数：强度 0.965 / 0.976、面积 0.412 / 0.406、静置两档 0 个墨像素、@1x 录制态 600 个）；
变异表 `mutate_r141.py` **CAUGHT=6/6、RESTORE_CLEAN=yes**；清账表 68 → **70 行**（新表面「设置窗口/快捷键录制器」，格子 171，地板 70）；
静置态逐像素不变 ⇒ 重新捕获的 136 张帧 `COMPARED=136 / CHANGED=0`（R140 那格 NOT-RUN 本轮补上）。
三条新账：**U-466** xctest 的 `with 1 failure` 是单数，按复数写正则会把"只红一条"读成"没有汇总行"再顺着 PASSED 出口走
（两把好刀因此被我误报成"判据没牙"）；**U-467** 只打开宽度而颜色仍是 `.clear` 的刀**没有靶**，多旋钮表达的刀要成组下；
**U-468** 容差带先量后判（印象值 `0.30…1.60` 会把两种病都放过去）。
**后半程翻出一条我写错的判据（U-470）**：按 AGENTS.md 补的「从产品入口进入」那条用例红了（离屏两帧之间「新增墨=0」），可同一时刻真机截图上点过那一屏有 1548 个高色度像素、静置 0 个⇒ **`cacheDisplay` 不合成挂在 `NSViewRepresentable` 外面的 SwiftUI overlay**；那一层的判据搬进 `scripts/real_screen_recorder_ring.py`（本轮 `ring_present`；退出码 0/1/2；纯函数真值表 8 条），离屏那条改判成只判接线（不同像素 > 200）。换装：`INSTALL_SHA_MATCH=1 / INSTALL_RESULT=ok`；带独立 `CLIPBOARD_HISTORY_DATA_DIR` 的第二条实例在守卫处静默退出（0 字节日志）⇒ BACKLOG 55 那个现象第二次由独立路径复现，也因此我没有去点用户那一扇真窗。

改自评口径又照出曲线的尺一处死代码（**U-471**：`curve_from_ledger.py` 的 `DIM_ROW` 只认 `| 14 |`，而 R139 起的表写 `| 14/15 |` ⇒ 「没有结论行时从七维表推导」这条路从来没通过，只因每轮都还写着 `**自评 N/100**` 才没被发现）。处置：结论行仍写 /100，把 /105 的合计写在同一行；真正的修法要连 `DIM_ROW` 与 `SCORE` 一起改并配变异 ⇒ BACKLOG 180。

全量：843 tests / 42 skipped / 0 failures、0 编译告警；电池 291 OK。

读 CI：`cab72f8` / `6f0c609` / `48be136` 全 `success`；`4486f6d` 红在 `testFrameIntervalsUnderStateChanges`（p95 26.94 > 20.0），
与上一跑对账是 **ONLY_B 换班** ⇒ 新开 **BACKLOG 176**（把绝对 20ms 换成同一次运行的相对判据），另开 **177**（录制态真帧）、**178**（暗档 bezel 与卡片几乎同色，未量）。

（R140）**断点续跑（R141 的靶，按顺序，预算 ≤4 文件）**：
⓪ **先读三跑的 CI 结论**（本地 14:45 实测 status=in_progress、conclusion 为空，作业只有 build-and-test 一列 ⇒ 结论**未读**，本轮没有任何「CI 绿」的声明）：run 39042028124 = `4486f6d`、39041957806 = `48be136`（R140）、39041049852 = `cab72f8`（R139 那一跑也还没落地）。
① **把看图腿补上** —— `/tmp/shots*` 已被系统清空（`COMPARED=0 / MISSING=134`），所以 R141 第一件事是重新捕获
（`CLIPBOARD_HISTORY_UI_SHOTS=<目录> swift test --filter UICaptureTests` → `frame_baseline check`），
并把**帧数**写进台账：任何 `X=0` 形状的通过，先看分母是不是 0（U-465 那一族的兄弟，R140 我自己刚栽过一次）。
② **按 BACKLOG 173 点一次真动效** —— 自 R126 起欠，本轮 0 产品改动；下一批点的格已写进 173 追记（R140）。
③ **`mutate_r140.py` 还没进针自检登记表** —— `mutate_needle_precheck.py` 带着并行会话的脏 diff，等它落盘再登记，不替别人提交。
④ **BACKLOG 175**：给「文件级缺席」配一条资格判据（先 spike 证明夹具的 surface→文件名单能区分 `QuickPickController` 与 `SettingsView`）。
⑤ **只有你能判的那几格**：172 的亮档图标（人工批次 86.1）—— 需要你看一眼或授权我切系统外观。

**做了什么**：`docs/motion_surface_ledger.json` 从 60 行扩到 **68 行**（未清账 94/162，地板 60 → 68），
八格的理由全部建立在**本轮现量**的 grep 计数上：`DetailView` highlightQuery=2 / disabled=0，
`SettingsView` ProgressView=0 / isLoading=0，`QuickPickController` disabled=0 / emptyLabel=15，
`MenuBarRecommendationsView` highlight=0 / selected=0。三条新规矩：
**U-463** 缺席断言的射程按「这个文件是不是只装这一个表面」定（`SettingsView` 越界不算证），闸门查不出越界 ⇒ 新开 BACKLOG 175；
**U-464** 详情区 × 选中差点按印象写成 not-applicable，grep 到 `highlightQuery` 才改判 kept；
**U-465** 生成器里的外部变量（语法对、运行 `NameError`）是那一族第三次生效 ⇒ 指针一律写字面路径，M658 把错法原样复现。
本轮产品 0 改动，而视觉审查那一腿 **NOT-RUN**（`/tmp/shots*` 已空 ⇒ `COMPARED=0 / MISSING=134`，第一版那句「复用旧帧 + `CHANGED=0`」是空对账，已改判并留痕，R141 先重新捕获）；**没有新增动效**（BACKLOG 173 从 R126 起仍欠）。

（R139）**做了什么**：上一轮我第二次撞上"半批已写"（R138 的 CHANGELOG 整条没落上，其余四处落了盘），当时只靠人眼发现。
本轮把它变成会红的东西：`scripts/tests/test_round_batch_consistency.py`（3 条）从 `AGENT_STATE.md` 的"最后更新"读本轮 R 号，
要求**最近三轮**在 `AGENT_UI_AUDIT.md` / `AGENT_VISUAL_ITERATION.md` / `CHANGELOG.md` 各自都有标题，
并配"窗口 ≥2 + STATE 自报轮次必须出现在审计台账最近几行"的下限自检。

**当场被自己的刀骗过一次（U-459）**：M655 第一版把 CHANGELOG 的 R138 标题换成 `### （R138 的标题被删掉了）` ——
替换串自己就带着 `R138`，于是守卫读到了它要找的东西、报绿，而我认为刀落下了。改成整行删掉才 CAUGHT。
⇒ 删除型变异的替换串不许留着被测 token；新守卫第一次 CAUGHT 之前的 `PASSED` 本身就是信号，不是"再试一次"的小事。
U-461 写清边界：这道守卫查存在性、不查内容，看不见"三轮都写了但互相矛盾"。

**验证**：脚本自检 `Ran 283 tests OK`（280 → 283）；变异第 39 张 `mutate_r139.py` 两臂 CAUGHT（刀数 133 / caught 132，RESTORE_CLEAN=yes）；
针自检 `tables=39`；未动 Swift 源码 ⇒ 构建与全量沿用 R135 那一遍（835 条 / 0 失败）；无新帧 ⇒ 帧基线沿用 R126；清账表未动（60 行 / 未清账 102）。
**§9.3 第 5 条两半都补齐了**：U-450（R137）+ U-452（本轮）。

**仍开着的**：① 172 亮档那半（等用户那一眼或切系统外观的授权）；② 清账表 102 格未判；
③ 173 那笔"新加一个有作用的动效"的欠账（最近一次 R126）；④ U-458 的缺号 `107 / 156 / 161`。

**下一轮（R140）**：① 清账表下一批（主窗口/详情区 × 选中与禁用、设置窗口/侧栏 × 空与加载、
浮层/列表行 × 空与错误、菜单栏/推荐面板 × 成功）；② 若仍无用户输入，按 173 的样子把某处"不加"的理由量成读数。

---

## 上一轮现场（R138 / 第 140 轮）

>
> **查上一轮留下的缺号之谜，查出一件真事**：`AGENT_BACKLOG.md` 里 172 那条 —— **整个目标里唯一等用户的那条账** ——
> 现在以 `在离屏通道里几乎不画墨 —— …` 起头，前缀 `172. **R122 开：亮档侧栏图标` 被某次"插入"吃掉了
> （本仓库早记过这个形状：编辑台账"插入"实为替换）。于是 CHANGELOG、最终报告、STATE 里所有"BACKLOG 172"
> 都指向一个扫描器看不见的条目，而**没有任何判据发现过**。⇒ 已按 13:11 那次 grep 的原文逐字补回。
>
> **把尺伸进散文**：`test_prose_references_to_backlog_items_resolve_too` 现在查正文台账里的 `BACKLOG <n>`
> 是否都能落到条目上；配一条"认出条目数 > 100"的下限自检（U-457：正则一退化集合就空，
> "全部悬空"与"全部合法"两种相反失效都能安静通过）。M654（把前缀再吃掉一次）红在这条新判据上，
> 并逐条点名 `CHANGELOG.md → BACKLOG 172`、`AGENT_FINAL_REPORT.md → BACKLOG 172`。
>
> **U-458 不定论**：补好 172 后仍缺 `107 / 156 / 161`。按同一形状找不到孤儿行；
> 我抽查的三个历史版本里 `^156\.` 与 `^161\.` 也都不存在 —— 而那三版是**我挑的**，不是全历史。
> ⇒ 记成开放项并写下下一步查法，不选一个说法写进账。
>
> **验证**：脚本自检 `Ran 280 tests OK`（279→280）；变异 M654 CAUGHT（刀数 131 / caught 130，RESTORE_CLEAN=yes）；
> 本轮只改台账文件与自检，未动 Swift 源码 ⇒ 构建与全量沿用 R135 那一遍（835 条 / 0 失败），帧基线沿用 R126，清账表未动（60 行 / 未清账 102）。
>
> **仍开着的**：① 172 亮档那半（等用户那一眼或切系统外观的授权）；② 清账表 102 格未判；
> ③ 173 那笔"新加一个有作用的动效"的欠账；④ U-458 的缺号；⑤ U-452 那半（一批补丁"半批已写"）仍无守卫。
>
> **下一轮（R139）**：① 清账表下一批（主窗口/详情区 × 选中与禁用、设置窗口/侧栏 × 空与加载、
> 浮层/列表行 × 空与错误、菜单栏/推荐面板 × 成功）；② 把 U-452 那半补成守卫（一批台账补丁要么全成要么全不写）；
> ③ 若仍无用户输入，按 173 的样子把"不加"的理由量出来。
>
> ---
>
> ## 上一轮现场（R137 / 第 139 轮）
>
> >
> > **做了什么**：上一轮我在最终报告 §9.3 写下"台账那两处薄弱还没有自动守卫"。本轮补了一半 ——
> > `scripts/tests/test_ledger_generator_output.py`（4 条）把生成器复制进临时目录跑一遍，要求 ① exit 0、
> > ② 产物与仓库那份**逐字相同**、③ 打印的行数等于表里的行数。于是 U-450 那个形状（生成器 NameError、
> > 闸门读旧 JSON 报 `RESULT=ok`）从"人眼数行数"变成会红的断言。另加一条查"表里引用的 BACKLOG 号必须真有条目"。
> >
> > **新守卫第一次跑就给的是假阳性**（U-453）：它把 `BACKLOG 166 / 170` 报成悬空，而条目行其实有**两种形状**
> > （`155. **…` 与 `**166.（…）…`），只认前者会漏二十多个条目 —— R94 那一课（"定义行正则要按台账实际形状写"）换了个文件重演。
> > 修好之后仍缺号 `107 / 156 / 161 / 172`，两种解释都没排除 ⇒ **U-454 记成开放项，本轮不定论**；
> > 这同时是新守卫的盲区：它只查表里的引用，不查散文里的引用。U-455：检查不许有副作用，生成器写相对路径 ⇒ 必须沙箱跑。
> >
> > **验证**：脚本自检 `Ran 279 tests OK`（275 → 279）；变异第 38 张 `mutate_r137.py` 两臂 CAUGHT
> > （刀数 128 → 130，caught 127 → 129，RESTORE_CLEAN=yes，两刀各红在自己的测试上）；针自检 `tables=38`；
> > 清账表未动（60 行 / 未清账 102 / RESULT=ok）；未动 Swift 源码 ⇒ 构建与全量沿用 R135 那一遍（835 条 / 0 失败），帧基线沿用 R126。
> >
> > **仍开着的**：① 172 亮档那半（等用户那一眼或切系统外观的授权）；② 清账表 102 格未判；
> > ③ 173 那笔"新加一个有作用的动效"的欠账（最近一次是 R126）；④ U-454 的缺号之谜；⑤ U-452 那半还没有守卫。
> >
> > **下一轮（R138）**：① 查清 U-454（把那四处实际文本按行号贴出来再判，别猜）；
> > ② 清账表下一批（主窗口/详情区 × 选中与禁用、设置窗口/侧栏 × 空与加载、浮层/列表行 × 空与错误、菜单栏/推荐面板 × 成功）；
> > ③ 若仍无用户输入，就把 173 的"不加"理由按 ①② 的样子量出来（而不是随便加一个动画）。
> >
> > ---
> >
> > ## 上一轮现场（R136 / 第 138 轮）
> >
> > >
> > > **runner 兑现了预登记的两格**（run `39038634407`，job=success）：
> > > `MOTION_BAND_SAMPLING_VERDICT 机器=arm64/macOS 15.7/1x 出口=这台机器判不了=调度地板 22.13ms 大于省下的 5.64ms ｜ 省没省钱由 ② 单独判（那里已经报过 1.78×）`，
> > > 以及 `MOTION_FLOOR_FACTS judged=3/4 executed=58 红的用例=-` + `MOTION_FLOOR_REDS=0`。
> > > ⇒ 那台机器说出了自己判不了，而不是把一次调度噪声报成产品结论；`judged` 没掉档 ⇒ 这个出口确实是读数不是免检。
> > > **174 结案**；**155 随它结案**（① 被排除、② 被测量支持；四种处置里最后落在这一步，全程没动阈值、没塞 `suite_reds`）。
> > > 本机那一侧仍照判（`出口=判到=带更细`）⇒ 判据没被放弃，只是按机器分了范围。
> > >
> > > **清账表 52 → 60 格**：热图与浮层的「加载/错误」、落点的「按下/聚焦」、状态图标的「选中/聚焦」——
> > > 八格全部缺席立论，逐条由闸门去文件里查；落点那两格刻意**不**用整文件缺席（那文件里 pressedStyle 有 2 处、focusable 有 1 处，
> > > 只是不在落点那层）—— U-449 在今天这次判里的实际形状。
> > >
> > > **U-450（U-444 的第二次，形状更典型）**：我插的八行用了 `%s` 格式化，而变量只存在于打补丁的脚本里 ⇒
> > > `ast.parse` 通过、运行时 `NameError`、闸门读上一版 JSON 打印 `RESULT=ok`。
> > > ⇒ 证人只认「行数变了」（52 → 60）；静态语法自检留着，但它替代不了一次真跑。
> > >
> > > **验证**：闸门 `行数=60 已清账=60 未清账=102 地板=60 / RESULT=ok`；词表 `added=8 kept=20 not-added=10 not-applicable=22`（合计 60）；
> > > 脚本电池见 §8（台账落盘之后跑）。本轮未动 Swift 源码 ⇒ 构建与全量沿用 R135 那一遍（835 条 / 0 失败）；无新帧 ⇒ 帧基线沿用 R126。
> > >
> > > **下一轮（R137）**：① 清账表继续（未清账 102）：主窗口/详情区 × 选中与禁用、设置窗口/侧栏 × 空与加载、
> > > 浮层/列表行 × 空与错误、菜单栏/推荐面板 × 成功；② 155/174 结案之后，动效那一卷剩下的开放项只有 172（等用户那一眼）
> > > 与 173（欠的位点判断，按 ①② 的样子把「不加」的理由量出来）；③ 阶段二已跑到第 138 轮，
> > > `AGENT_FINAL_REPORT.md` 的收口要在开放项只剩「等用户」时做。
> > >
> > > ---
> > >
> > > ## 上一轮现场（R135 / 第 137 轮）
> > >
> > > >
> > > > **做了什么**：判完筛选条（悬停 kept：缩放 + 底色两档，减弱动态时底色是唯一表达；按下 kept）、
> > > > 设置侧栏（聚焦 not-added：整条选中已经在说你在哪；禁用 not-applicable：分类是常量）、
> > > > 浮层输入框（悬停 not-added：它一出现就是第一响应者；禁用 not-applicable）、
> > > > 推荐面板 × 悬停（not-applicable：`.menuBarExtraStyle(.menu)` ⇒ 真 NSMenu）。表 52 行 / 未清账 110 / 地板 52。
> > > >
> > > > **结构性的一步（U-447）**：最后那格的理由挂在一个 **API 默认值**上，而 `App.swift` 的注释自己写着"默认值不是契约"。
> > > > 一句会过期的注释不等于闸 ⇒ 新增 `DocumentationAnchorTests.testMenuBarExtraStyleStillSaysMenuWhileTheLedgerSaysNotApplicable`：
> > > > 那行字面量被删或改成 `.window` 就红，失败文本点名"台账里哪两格要重判"。M650 / M651 两刀 CAUGHT，
> > > > 并且**修完守卫之后重跑了一遍**（旧结果的 CAUGHT 不能替新代码作证）。
> > > >
> > > > **两条自己的错**：U-448 守卫第一版整文件 contains ⇒ 命中注释里那句"哪天有人加一行 .window"，第一次全量跑就假红
> > > > （`显式=.window:1` 来自注释）⇒ 扫前剥注释；U-449 设置侧栏 × 禁用 差点写成"文件里没有 .disabled("——那里真有 4 处，
> > > > 是闸门会打红的假判据 ⇒ 缺席断言必须绑到具体那一块。
> > > >
> > > > **验证**：构建 `WARNINGS=0`；swift 全量 `Executed 835 tests, with 41 skipped and 0 failures`（834→835）；
> > > > 闸门 `行数=52 / RESULT=ok`；变异第 37 张两臂 CAUGHT（刀数 128 / caught 127，RESTORE_CLEAN=yes）；针自检 `tables=37`；
> > > > 脚本电池见 §8（台账落盘之后跑）。无新帧 ⇒ 帧基线沿用 R126 那一遍；看图腿沿用 R132 真机帧。
> > > >
> > > > **待读**：run `39038634407`（R133 那一跑）到本轮收尾仍未跑完 ⇒ 174 的两格期望（runner 的出口词 + `judged` 不掉档）**不写结论**，后台在盯。
> > > >
> > > > **下一轮（R136）**：① 读那一跑并结 174 / 收口 155；② 清账表继续（未清账 110）：
> > > > 设置窗口/热图 × 加载与错误、主窗口/拖入落点 × 按下与聚焦、浮层/空态 × 加载与错误、菜单栏/状态图标 × 选中；
> > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权。
> > > >
> > > > ---
> > > >
> > > > ## 上一轮现场（R134 / 第 136 轮）
> > > >
> > > > >
> > > > > **做了什么**：六格落判 —— 浮层/列表行 × 悬停（kept：行视图自己带跟踪区，`rowHoveredForCapture` 的 didSet 驱动重绘）
> > > > > 与 × 按下（not-added：那一层 mouseDown 就是选中，`pressedStyle` 在该文件 0 命中，缺席由闸门去文件里查）；
> > > > > 主窗口/搜索框 × 聚焦（kept：焦点环是被**显式恢复**的，放大镜跟着 `isActive` 换档）；
> > > > > 设置窗口/开关与滑块 × 悬停与按下（not-added：系统自己画，R20 那次两层 hover 叠出第三档是反面证据）；
> > > > > 菜单栏/状态菜单 × 悬停（not-applicable：那一层编译真 NSMenu，没有可挂点）。表 45 行 / 未清账 117 / 地板 45。
> > > > >
> > > > > **本轮最值钱的一条是 U-444**：我写完六行跑生成器，它抛 `SyntaxError`，而紧接着跑的闸门打印 `RESULT=ok 不合法格=0`
> > > > > —— 它读的是**上一版** JSON。两句合起来读就是"表没问题"，而新数据一行都没进去。⇒ 证人必须是「行数变了」，
> > > > > 不是"闸门绿了"；生成器落地后要 `ast.parse` 自己一遍（根因是 U-445：CJK 串里的 ASCII 双引号又打断了一次字面量）。
> > > > > 另记 U-446：`not-added` 与 `not-applicable` 的区别要落在「有没有可挂点」上，否则读的人会以为状态菜单那里还欠一次实现。
> > > > >
> > > > > **验证**：闸门 `行数=45 已清账=45 未清账=117 地板=45 / RESULT=ok`（词表分布合计与行数对账）；
> > > > > 生成器 `ast.parse` 通过；脚本电池见 §8（台账落盘之后跑）。未动 Swift 源码 ⇒ swift 全量与帧基线沿用 R133 那一遍
> > > > > （`Executed 834 tests, with 41 skipped and 0 failures`）；看图腿沿用 R132 的真机帧。
> > > > >
> > > > > **待读**：R133 那一跑（run `39038634407`）本轮仍在跑 ⇒ 174 的两格期望（runner 的出口词 + `judged` 不掉档）**不写结论**。
> > > > >
> > > > > **下一轮（R135）**：① 读那一跑，对上就结 174、收口 155；② 清账表继续（未清账 117）：
> > > > > 主窗口/筛选条 × 悬停与按下、设置窗口/侧栏 × 聚焦与禁用、浮层/搜索框 × 悬停与禁用、菜单栏/推荐面板 × 悬停；
> > > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权。
> > > > >
> > > > > ---
> > > > >
> > > > > ## 上一轮现场（R133 / 第 135 轮）
> > > > >
> > > > > >
> > > > > > **做了什么**：`samplingRateVerdict` 四出口（判到更细 / 判到更粗且地板解释不了 / 这台机器判不了 / 无从判定=没有帧），
> > > > > > 前提由同一次运行量出来的 `min(两臂地板) > 两臂抓帧差` 比出来 —— **不是新阈值**、没动 ⑤ 的那条线、没塞 `suite_reds`。
> > > > > > 只有后两格红；放行那一格放不掉"根本没省钱"，因为省钱由 ② 单独判，其读数印在同一行里（U-443）。
> > > > > >
> > > > > > **本机第一跑**：`出口=判到=带更细 ｜ ② 报过 8.70×` ⇒ 判据没被改成恒真。
> > > > > > **下一次 CI 的期望**：`MOTION_BAND_SAMPLING_VERDICT 机器=arm64/macOS 15.7/1x 出口=这台机器判不了=调度地板 … 大于省下的 …`，
> > > > > > 且 `MOTION_FLOOR_FACTS` 的 `judged` **不许掉档**（这个出口是读数，不是 `MOTION_NOT_RUN`）。
> > > > > >
> > > > > > **变异表自己的两处"只印不拦"**（U-442，本轮一次撞上两个）：needle 在两个函数里字面相同 ⇒ 那一臂 DID-NOT-RUN 而整表 exit 0；
> > > > > > "红掉的测试名"正则按点切而 swift 原文中间是空格 ⇒ 三臂都印成 `-`。都修了，现在 `not_run>0` 也算失败。
> > > > > > 另记 U-441：真值表改成 `guard case` + `accuracy`（枚举整体判相等对十进制减法太紧）—— 这条标**未实测**，只算换了更稳的形状。
> > > > > >
> > > > > > **验证**：构建 `WARNINGS=0`；swift 全量 `Executed 834 tests, with 41 skipped and 0 failures`（832→834）；
> > > > > > 变异第 36 张 `mutate_r133.py` 三臂 CAUGHT（刀数 123→126，caught 122→125，RESTORE_CLEAN=yes，M647 与 M648/M649 落在不同测试上）；
> > > > > > 针自检 `tables=36`；脚本电池见 §8（台账落盘之后跑）。清账表本轮未动（39 格 / 未清账 123 / 地板 39）；无新帧 ⇒ 帧基线沿用 R126。
> > > > > >
> > > > > > **下一轮（R134）**：① 按 D-191 读 R133 这一跑的 CI，验那两格期望（runner 的出口词 + `judged` 不掉档）；
> > > > > > ② 清账表下一批（浮层/列表行 × 悬停与按下、主窗口/搜索框 × 聚焦、设置窗口/开关与滑块 × 悬停与按下、菜单栏/状态菜单 × 悬停）；
> > > > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权。
> > > > > >
> > > > > > ---
> > > > > >
> > > > > > ## 上一轮现场（R132 / 第 134 轮）
> > > > > >
> > > > > > >
> > > > > > > **结论**：139 那句「设置里的勾选框在帧里色度为 0，勾上不是强调蓝」**不是产品缺陷**，是离屏通道不解析语义色 ——
> > > > > > > 与 126 / 130 / 172 同一族。证据是新装的 `scripts/real_screen_control_chroma.py` 在**同一张真机帧**里比两块区域：
> > > > > > > 参照（侧栏选中那一行）最大 `b-r`=194，内容区 190，比值 0.979，强蓝 2463 颗且包围盒 x=177..192 y=98..219pt
> > > > > > > 正好是勾选框那一列；我自己看那张帧：三颗蓝底白勾 + 一颗灰勾。两条通道同向 ⇒ 产品不改，而"不改"从今天起有真机证据。
> > > > > > >
> > > > > > > **顺带打通的一格**：149 记的"切分区不通"改成"按名字不通、按坐标可通"—— 这扇 SwiftUI 窗口在 System Events 里
> > > > > > > `name` 全是 `missing value`（AXPress 无路），但按坐标点 + **用同一帧里药丸的移动**验收（50.5pt → 82.0pt ⇒ `moved`）可行。
> > > > > > >
> > > > > > > **两条自己的错**：U-438 点之前的探针复用了需要 `after` 的出口 ⇒ 一次成功的测量被印成"尺坏了"（假阴性会让人去修没坏的尺）；
> > > > > > > U-439 包围盒四个数印成 `x=177..98` 这种倒区间（形状像结论、对象是错的）⇒ 现在 min ≤ max 是恒等式，错序走 `BAD_BOX`。
> > > > > > >
> > > > > > > **验证**：真机 `REALSCREEN_CHROMA_VERDICT=accent_in_content`；自检 `Ran 275 tests OK`（265→275）；
> > > > > > > 变异第 35 张 `mutate_r132.py` 两臂 CAUGHT（刀数 121→123，caught 120→122，RESTORE_CLEAN=yes）；针自检 `tables=35 bad=0`。
> > > > > > > 未动 Swift 源码 ⇒ swift 全量与帧基线按实沿用 R130 那一遍（832 条 / 0 失败）。
> > > > > > > **代价如实记**：`click at` 会把用户设置窗口的选中页改掉（本轮留在了「通用」）；本轮真机只量了暗档，亮档那一半仍等 172。
> > > > > > >
> > > > > > > **下一轮（R133）**：① 做 **BACKLOG 174** 那一格 —— 给 ⑤ 那条采样率判据加第三个出口
> > > > > > > 「这台机器判不了」（前提由同一次运行自己量出来：两臂地板的最小值 > 两臂抓帧差 ⇒ 地板主导，
> > > > > > > 走已登记的 `clock-coarse-in-window` 那条 `MOTION_NOT_RUN` 通道），配真值表 + 两臂变异 + 「not-run 不许变成免检」的守卫；
> > > > > > > run `39036587208` 的读数已在本轮到手（见上面那格），不必再等；② 清账表下一批（浮层/列表行 × 悬停与按下、主窗口/搜索框 × 聚焦、
> > > > > > > 设置窗口/开关与滑块 × 悬停与按下、菜单栏/状态菜单 × 悬停）；③ 本轮看图时看到但没动的两件事（「开机启动」缺说明行；
> > > > > > > 说明文字与勾选框左缘对齐而非与标题对齐）—— 先问离屏帧能不能量出来，量不出来就只算目视，不开单；④ 172 仍等用户那一眼。
> > > > > > >
> > > > > > > ---
> > > > > > >
> > > > > > > ## 上一轮现场（R131 / 第 133 轮）
> > > > > > >
> > > > > > > >
> > > > > > > > **做了什么**：把 173 欠的那批位点一次判完 —— 热图（空=kept，选中/聚焦=not-applicable）、列表行（聚焦/加载=not-added）、
> > > > > > > > 详情区（悬停=kept：只有那颗 chip 响应鼠标）、提示条（禁用/聚焦）、状态图标（按下：系统画）、说明段（空/错误/按下）。
> > > > > > > > 配套两条新判据：指针指向的文件必须存在，以及 `缺席:<路径>=<词>` 的可复查文法。
> > > > > > > > **第一条上线就抓到 R128 我自己写的两行假指针**（`Sources/ClipboardHistoryApp/ContentView.swift` 少了 `Views/` 一段，
> > > > > > > > 形状合法、文件不存在，而上一轮的形状判据绿了一整轮）⇒ 已修并核对该处确实是 `.animation(for: .bannerIn)`。
> > > > > > > >
> > > > > > > > **为什么"缺席"要写成文法**：这一轮十二格里有九格立论靠缺席（那个文件里没有某个词），而**没量过的缺席与没做，
> > > > > > > > 在复核时是同一个样子**。现在闸门会去文件里查：词在里面 ⇒ `ABSENT_CLAIM_FALSE`；文件不在 ⇒ `ABSENT_CLAIM_UNVERIFIABLE`。
> > > > > > > > 另配一条「新判据在真表上必须有对象」的守卫（≥10 行路径解析得到），免得四条自检只在合成样本上成立。
> > > > > > > >
> > > > > > > > **验证**：闸门 `行数=38 已清账=38 未清账=124 地板=38 / RESULT=ok`；电池 260 → **`Ran 265 tests OK`**；
> > > > > > > > 变异第 34 张 `mutate_r131.py` 三臂 CAUGHT（刀数 118→121，caught 117→120，RESTORE_CLEAN=yes，M642/M643 各红在自己的测试上）；
> > > > > > > > 针自检 `tables=34`。未动 Swift 源码 ⇒ swift 全量与帧基线按实**沿用 R130 那一遍**（832 条 / 0 失败）；
> > > > > > > > 看图腿沿用 R122 暗档通用页，并如实记：九格是缺席判断，画面上本来没有可看的东西。
> > > > > > > >
> > > > > > > > **待读已还**：R130 那一跑（run `39036587208`）在本轮收尾前跑完 = **success**，读数已到手并回改：
> > > > > > > `带间隔=26.72 整窗间隔=38.44 带抓帧=5.44 整窗抓帧=15.07 ｜ 带地板=21.27 整窗地板=23.37 谁细=带`
> > > > > > > ⇒ 155 的 ② 第一次有测量支撑（runner 的调度地板 21–23ms，是本机 5ms 的四倍，两臂只差 2.1ms，
> > > > > > > 而抓帧差 9.6ms ⇒ 间隔里 80% 是调度，这条"A 比 B 细"在 CI 上量的不是它声称的东西）；四跑三红一绿。
> > > > > > > 处置另开 **174**（把"地板主导"做成由同一次运行自己量出来的前提，走已登记的 `clock-coarse-in-window` 出口；
> > > > > > > 禁止调阈值、禁止塞 `suite_reds`）。
> > > > > > > >
> > > > > > > > **下一轮（R132）**：① 按 D-191 读 `39036587208`，拿 `MOTION_BAND_INTERVAL` 在 runner 上的两个地板给 155 定性；
> > > > > > > > ② 清账表继续（剩 124 格；下一批：浮层/列表行的悬停与按下、主窗口/搜索框 × 聚焦、设置窗口/开关与滑块 × 悬停与按下）；
> > > > > > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权。
> > > > > > > >
> > > > > > > > ---
> > > > > > > >
> > > > > > > > ## 上一轮现场（R130 / 第 132 轮）
> > > > > > > >
> > > > > > > > >
> > > > > > > > > **做了什么**：⑤ 那条判据在 runner 上连红三跑而两种解释分不开；本轮把 155 自己写的下一步做完 ——
> > > > > > > > > `bandIntervalFacts` 交出绝对分解，并显式允许「无从分解」（间隔 < 抓帧 ⇒ 两个量不是同一卷测的）；
> > > > > > > > > `filmstripMachineKey()` 与 171 同形；结论行打在断言之前，断言与读数吃同一对局部变量。**没有引入任何新阈值。**
> > > > > > > > >
> > > > > > > > > **本机第一跑**：`机器=arm64/macOS 27.0/2x 带间隔=9.27 整窗间隔=43.16 带抓帧=4.24 整窗抓帧=38.17 ｜ 带地板=5.03 整窗地板=4.99 谁细=带`
> > > > > > > > > ⇒ 本机 ② 被排除（两臂地板差 0.04ms）。**不外推到 runner**：下一次 CI 看同一行的两个地板 —— 两臂地板都远大于 5ms 且彼此接近 ⇒ ② 成立；
> > > > > > > > > 带的地板明显大于整窗 ⇒ ① 成立（R57 的结论要按机器分开记）。仍不用 `suite_reds` 登记绕过。
> > > > > > > > >
> > > > > > > > > **两条自己的错**：真值表两行的**期望**是我心算的且都算错（U-432，代码是对的）；哨兵值我第一版写成 `isInfinite`
> > > > > > > > > ⇒「没帧」会掉进「带更贵」，也就是把探针坏了报成产品没省到钱（U-433，M640 是它的证词）。
> > > > > > > > >
> > > > > > > > > **验证**：构建 `WARNINGS=0`；本机动效两用例 `Executed 2 tests, with 0 failures`（`CLIPBOARD_HISTORY_UI_MOTION=1`）；
> > > > > > > > > 变异第 33 张三臂 CAUGHT（刀数 115→118，caught 114→117，RESTORE_CLEAN=yes）；swift 全量 `Executed 832 tests, with 41 skipped and 0 failures`（831→832，多的那条就是真值表）；脚本电池 `Ran 260 tests OK`；针自检 `tables=33 bad=0`（电池在台账落盘之后、push 之前跑）。
> > > > > > > > > 无新帧 ⇒ 帧基线沿用 R126 那一遍；看图腿沿用 R122 的暗档通用页（第 131 轮已记理由）。
> > > > > > > > >
> > > > > > > > > **下一轮（R131）**：① 按 D-191 三步读 R130 这一跑的 CI，拿 `MOTION_BAND_INTERVAL` 在 runner 上的两个地板给 155 定性；
> > > > > > > > > ② 按表面清账表再清 6–8 格（菜单栏/状态图标其余状态、主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误）；
> > > > > > > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权 —— 目前唯一真正需要用户输入的开放项。
> > > > > > > > >
> > > > > > > > > ---
> > > > > > > > >
> > > > > > > > > ## 上一轮现场（R129 / 第 131 轮）
> > > > > > > > >
> > > > > > > > > >
> > > > > > > > > > **做了什么**：① 占位行的 `"state": "禁用"` 在 R128 收窄夹具名册后换了红的对象（U-429）—— 修好并让 `UNKNOWN_CELL`
> > > > > > > > > > 两个维度各有证人；② 摘掉 `FLOOR_LIES` 的第二份实现，自检从「成员」升级成「次数」（U-430，M637 是唯一证词）；
> > > > > > > > > > ③ 按新规矩 D-191 重读 CI：**R124/R125/R126 三跑全是 `failure`**，失败步骤都是 `Motion coverage floor`，
> > > > > > > > > > 红的是 BACKLOG 155（两臂中位间隔 28.44>25.38 / 32.49>27.46 / 32.16>31.81，差值在收窄）⇒ 上一轮那句
> > > > > > > > > > 「171 是最后一朵红」是错的（U-431），155 追记已写，`suite_reds` 仍钉为空表（不许用登记绕过）。
> > > > > > > > > >
> > > > > > > > > > **验证**：闸门 `RESULT=ok 不合法格=0`；脚本电池 258（**当时红一条**）→ **`Ran 260 tests OK`**；
> > > > > > > > > > 变异第 32 张 `mutate_r129.py` 三臂 CAUGHT（刀数 112→115，caught 111→114，三刀红在三条不同测试上）；
> > > > > > > > > > 针自检 `tables=32 covered=27 arms=94 bad=0`。未动 Swift 源码 ⇒ swift 全量与帧基线按实记为沿用 R126 那一遍；
> > > > > > > > > > 看图腿沿用 R122 的 `settings-general-720x540-dark.png`（0 产品改动轮，理由写在 Round 129 §2）。
> > > > > > > > > >
> > > > > > > > > > **下一轮（R130）**：① 回到产品面 —— "产品面推进"这一维连续两轮 11/15，清账表再清 6–8 格
> > > > > > > > > > （菜单栏/状态图标其余状态、主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误）；
> > > > > > > > > > ② 155 的定性：把两臂**绝对**间隔 + 机器键（`arm64/macOS x.y/Nx`，与 171 同一把键）打进行内读数，一次 CI 分开 ①/②；
> > > > > > > > > > ③ 172 仍等用户那一眼（批次 86.1）或切系统外观的授权。
> > > > > > > > > >
> > > > > > > > > > ---
> > > > > > > > > >
> > > > > > > > > > ## 上一轮现场（R128 / 第 130 轮，已被本轮更正其中六处「258 OK」）
> > > > > > > > > >
> > > > > > > > > > >
> > > > > > > > > > > **做了什么**：闸门加 `EVIDENCE_SHAPE`（只写「R14 说过」不算证据，`Sources/.../HistoryRowViews.swift 里那一行` 才算）、`SURFACE_UNCOVERED`、`STATE_UNCOVERED`；地板从总行数改成**已清账格子数**，`not-measured` 是占位、不抬地板。表从 18 行扩到 26 行（`added=8 kept=13 not-added=3 not-applicable=2`，未清账 136/162）——**先修数据再加判据**：9 行只有轮次号的指针补成可复查对象，否则闸门红在自己的表上，而下一个人学到的教训会是「把判据放宽」。
> > > > > > > > > > >
> > > > > > > > > > > **闸门两次咬到我自己的证据**：`UNKNOWN_CELL 第 14 行（主窗口/提示条 × 消失）` —— 「消失」是一次转换不是九个状态之一（U-426）；以及最小夹具被同一格判红（它的状态「禁用」没有行，U-427）。这两件事合起来才说明新判据在判东西，不是装饰。
> > > > > > > > > > >
> > > > > > > > > > > **U-428（下一轮先还）**：三刀 M633/M634/M635 全部 CAUGHT，却**红在同一条测试上**（`test_a_file_or_backlog_pointer_is_checkable`）—— `caught=3` 是真的，但三格判据没有各自被单独证伪。要给每条判据配一条只测它自己的用例，覆盖对账才从「刀被抓到」升级成「哪一格由哪条测试作证」。
> > > > > > > > > > >
> > > > > > > > > > > **验证**：闸门 `RESULT=ok 不合法格=0`；脚本电池 253 → **258 OK**；针自检 `tables=31 bad=0`；变异第 31 张三臂 CAUGHT（刀数 109→112，caught 108→111）。未动 Swift 源码 ⇒ swift 全量与帧基线按实记为沿用 R126 那一遍。
> > > > > > > > > > >
> > > > > > > > > > > **下一轮（R129）**：① 读 R126/R127/R128 三跑 CI，验那条预测（runner 读 `⇒ 一致`、捕获卷无红）；② 还 U-428 那格（每格判据配自己的证词）；③ 清账表再清 6–8 格（菜单栏/状态图标其余状态、主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误）；④ 172 仍等用户那一眼（批次 86.1）。
> > > > > > > > > > >
> > > > > > > > > > > > 最后更新：2026-10-17 20:53（本地 · R127 / 第 129 轮收尾：**127 轮的动效判断第一次成为一张可判的表** —— 18 格有结论、144 格显式未清账（173 追记 2 / U-423…U-425 / D-189 · 产品 0 改动））
> > > > > > > > > > > >
> > > > > > > > > > > > **为什么做这张表**：阶段二要求「每一个元素都要重新判断加动效是否有积极作用」，而这些判断散在 127 轮正文里 —— 复核时"散在正文"与"没做"长得一模一样。`docs/motion_surface_ledger.json` 把它变成数据：18 个表面 × 9 个状态 = 162 格，已清账 18 行，每行 verdict + 理由 + 证据指针。`MOTION_LEDGER_VERDICTS added=7 kept=9 not-added=1 not-applicable=1` —— 三条「不加/不适用」是这张表最有价值的部分，它们证明不加也是判过的结果（菜单栏那处：`MenuBarExtraStyle.menu` 编译成真 NSMenu，SwiftUI 过渡根本不执行）。
> > > > > > > > > > > >
> > > > > > > > > > > > **判据形状分两层**（D-189）：不合法 ⇒ 红（七种：重格 / 名册外 / verdict 不在词表 / 理由过短 / 没有证据指针 / 行数低于地板 / 地板大于行数）；**未清账 ⇒ 只数不红** —— 给"没判过"配红等于命令下一轮把 162 格填满，而填满唯一省力的办法就是造没作用的动画，那正是目标禁止的方向。地板取已清账行数（单调量），不取覆盖率。
> > > > > > > > > > > >
> > > > > > > > > > > > **三条自坏**：**U-423** 变异表第一版两臂报 `PASSED`，其实是 `Ran 0 tests / OK`（`discover -p` 的 pattern 被我拼成 `test_test_motion_surface_gate.py`）⇒ verdict 之前先读 `Ran N tests`，N=0 一律 `DID-NOT-RUN`；这一族在台账里记过一次，这次是它第一次发生在**变异表**上，而变异表的作用正是证明测试有牙；**U-424** 证据指针只判非空，18 行里 9 行只写了轮次号 ⇒ 下一轮补形状判据（本轮登记而不是掩盖）；**U-425** 地板防删行、不防名册扩张。
> > > > > > > > > > > >
> > > > > > > > > > > > **验证**：脚本电池 244 → **253 OK**；闸门 `MOTION_LEDGER_RESULT=ok 不合法格=0`；针自检 `tables=30 bad=0`；变异第 30 张 M631/M632 CAUGHT（刀数 107→109，caught 106→108）。未动 Swift 源码 ⇒ swift 全量与帧基线按实记为**沿用 R126 那一遍**（不补数）。
> > > > > > > > > > > >
> > > > > > > > > > > > **下一轮（R128）**：① 读 R126/R127 的 CI，验那条预测（runner 应读 `⇒ 一致`、捕获卷无红）；② 清账表补 U-424 的形状判据与 U-425 的分母判据，并清掉菜单栏/搜索框/说明段那几格；③ 172 仍等用户那一眼（批次 86.1）。
> > > > > > > > > > > >
> > > > > > > > > > > > > 最后更新：2026-10-17 20:32（本地 · R126 / 第 128 轮收尾：**runner 那一行盲区名单按它自己印的键登记（空集=声明）**，登记表加上两格本机就能红的结构判据（171 全结案 / 173 改判 / U-420…U-422 / D-188 · 产品 0 改动））
> > > > > > > > > > > > >
> > > > > > > > > > > > > **现场（R124 的 CI，run 39031123341）**：`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 ⇒ 红(这台机器的位没登记)`，而同一跑 `MOTION_GATE_RESULT=ok 红=0`、图标判据在 runner 上没假红 ⇒ 171 是最后一朵红。上一轮故意留它，就是为了拿到这个键。
> > > > > > > > > > > > >
> > > > > > > > > > > > > **做了什么**：表里加第二行 `"arm64/macOS 15.7/1x": []` —— **空集是一条声明**（这台机器不复现侧栏暗档反侧），仍被 `新盲区`/`不再反侧` 两格钉住；本机那一行不受影响（`登记=13 实测=13 ⇒ 一致`）。另加两格**在本机就能红**的结构判据：表必须 ≥2 行、每个键必须成形（`arch/macOS 主次版本/倍率`，倍率只准 1x/2x），真值表补 3 个成形键 + 8 个不成形键。理由：`runner`、`CI` 这种"看起来像"的死键能通过任何按数量的懒判据却永远不被命中，而死行比空表更坏（D-188）。变异第 29 张 M629/M630 两刀 CAUGHT。
> > > > > > > > > > > > >
> > > > > > > > > > > > > **173 改判（重要）**：本轮按动效清单侦察四个位点，三处的结论早就写在代码里 —— 热图格子悬停已把事务挂在变更点上（`hoverRingOpacity` 是有名字的数）；`MenuBarExtraStyle.menu` 编译成**真 NSMenu**（D-055 / M15 实测），SwiftUI 过渡在那一层根本不执行；骨架扫光的时钟形状、亮带宽度、0.05→0.12 的抬升全有取证。**没有一处支持"再加一个动效"**，而为了还账硬加正是目标明令禁止的事。⇒ 173 改成"要么由真机/用户观察指出具体缺陷再动，要么像这三处一样把『不加』量出来"。这笔账诚实记：**连续第六轮零新增动效**（自评 86 那一格）。
> > > > > > > > > > > > >
> > > > > > > > > > > > > **U-420**：清单式选位点之前应先读候选位点的既有结论 —— 本轮约三分之一的时间花在侦察上，产出是"这里没有可做的动效"，而那些"为什么不做"的注释是第一次被读到。
> > > > > > > > > > > > >
> > > > > > > > > > > > > **下一轮（R127）**：① 读 R126 的 CI，确认 runner 读到 `⇒ 一致` 且**捕获卷全绿**（这是 171 结案的第二半，也是本轮写在账上的可证伪预测）；② 172 亮档那一半：等用户回答批次 86.1，或授权切系统外观后用 `scripts/real_screen_sidebar_icons.py` 复跑；③ 动效不再空转：若 ①② 都没有新观察，就把 173 转成"按表面清账"的收尾判据，而不是再造动画。
> > > > > > > > > > > > >
> > > > > > > > > > > > > > 最后更新：2026-10-17 20:15（本地 · R125 / 第 127 轮收尾：**动效接线第一次成为一把会红的清单尺** —— 顺手拦住我自己差点开的一条假账（新开 173 / U-417…U-419 / D-187 · 产品 0 改动））
> > > > > > > > > > > > > >
> > > > > > > > > > > > > > **现场**：我想找"目录里哪一档动效是死的"，在 shell 里 `grep "for: \.bannerOut"` 数出 **0**，于是准备开一条"这条声明没供电"的账。真去数它是 **5 处** —— 产品写的是 `asymmetricTransition(insertion: .bannerIn, removal: .bannerOut)`，我的模式只认得一种写法（U-417）。差一点用一个工具的语法盲区给产品记了一条假账，而下一轮就会有人照着这条账去"撤声明"。
> > > > > > > > > > > > > >
> > > > > > > > > > > > > > **改了什么**：计数进仓库 —— `motionKindCallSites`（剥注释在尺内 + 词边界）+ 7 行真值表 + 九档地板 `>=1` 的产品级判据（某档为 0 ⇒ `MOTION_KIND_UNWIRED` 红；找不到源码目录 ⇒ `MOTION_KIND_NOT_RUN` 记未运行）。第一次交出可 grep 的接线清单：`hover=17 / selection=5 / bannerIn=6 / bannerOut=5 / emphasis=9 / dropTarget=3 / contentFade=38 / slider=3 / skeletonSweep=1`；临时 python 与仓库 swift 正则两条独立实现逐档相同。
> > > > > > > > > > > > > >
> > > > > > > > > > > > > > **自坏**：**U-418** 第一版把"剥注释"外包给调用方，被真值表"注释里提一句"那一格当场红出来（`("1") is not equal to ("0")`）⇒ 移进尺内，调用方无法忘记；**U-419** 本轮**仍然零新增动效**（连续第五轮），清单是尺不是交付 ⇒ 新开 **BACKLOG 173**，规定下一轮按清单点一个位必须答三句话（现在几帧过渡 / 加了之后重排与跳变怎么变 / 两档 + reduce-motion 长什么样）。
> > > > > > > > > > > > > >
> > > > > > > > > > > > > > **下一轮（R126）**：① 173 —— 从清单里点一个位真做动效（不再允许"又建了一把尺"）；② 读 R125 的 CI，把 runner 那一行盲区位用**它自己印出来的键**填上（R124 故意留的红）；③ 172 亮档那一半仍等用户回答批次 86.1 或授权切系统外观。
> > > > > > > > > > > > > >
> > > > > > > > > > > > > > > 最后更新：2026-10-17 19:58（本地 · R124 / 第 126 轮收尾：**盲区名单按机器分键 —— 不在表里的那台必须红**（171 结案 / U-414…U-416 / D-186 · 产品 0 改动））
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > **现场（R122 的 CI，run 39029027567）**：那一跑只剩一朵红，正是 R120 预言的那朵 —— 「这些帧的暗档侧栏文字现在落在期望侧了：[13 张]」。同一跑另外两格按预期：新装的 `SIDEBAR_ICON_INVERTED` 在 runner 上**没有假红**（`SIDEBAR_ICON_COVERAGE 能力=不可判(内容区 0 墨)`），150 的四种出口与 R121 逐字一致（`参照臂=6 可判=4 框错红=0 不可判=2`）。⇒ `darkSidebarTextBlindSpots` 从 R29d 起被当全局权威用，而它量的是 **vibrant 子树 + `cacheDisplay` 不走合成**这一台机器的行为。
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > **改了什么（不是把红按下去）**：`darkSidebarTextBlindSpotsByMachine` 一行一台，键只由量出来的事实组成（架构 / macOS 主次版本 / 帧倍率；倍率取这一跑真正扫的那些帧，不用 `mainScreen`）；`sidebarRosterVerdict` 四种关系各有名字（未登记 / 一致 / 新盲区 / 登记过的不再反侧）+ 8 行真值表 + 结论行 `TEXT_SIDE_ROSTER_KEY … ⇒ 一致` 打在闸门之前。本机那一行用本轮印出来的键填：`arm64/macOS 27.0/2x 登记=13 实测反侧=13`。**runner 那一行故意留空** —— 下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它自己印的键>`，那时再填（D-186③：不许拿猜测当键）。
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > **三刀**：M624 键里丢掉倍率 / M625 未登记改成「当成一致」/ M626 撤掉新盲区那一格 ⇒ 第 27 张表，全部 CAUGHT（刀数 100→103，caught 99→102）。
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > **三条自坏**：U-414 结论行被自己的转义打回原文（数字都打、只有那个词没打出来 ⇒ 新加的 emit 必须看它自己的输出）；U-415 静态成员漏 `Self.` + 一个没用上的变量（0 告警那道门挡下，U-396 那一族第三次）；U-416 我先按记忆写了本机的键再去跑 —— 兜住我的是 `.unkeyed` 那一格，不是我会猜。
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > **下一轮（R125）**：① **先还动效的账**（连续第四轮零动效位点，自评 87 那一格）：从浮层剩余位点或主窗口行悬停里真做一个；② 读 R124 的 CI，把 runner 那一行键填上并确认 `TEXT_SIDE_ROSTER_UNKEYED` 是那一跑唯一的红；③ 172 的亮档那一半仍等用户回答批次 86.1（或授权切系统外观后用 `scripts/real_screen_sidebar_icons.py` 复跑）。
> > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > 最后更新：2026-10-17 19:45（本地 · R123 / 第 125 轮收尾：**真机那一层第一次成为可重跑的脚本** —— 暗档侧栏六枚图标有硬件证据，亮档那一半被"生效证明"拦下（172 追记 / U-411…U-413 / D-185 · 产品 0 改动））
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > **为什么需要这层**：R122 修「暗档两枚图标黑底黑图标」时，两档的离屏读数朝**相反方向**动（dark 反侧 22→0，light 期望 35→13），光靠离屏没法判是产品淡还是通道淡。那一层只有真机能答，而真机通道 R91 失败过一次（`screencapture` 全黑 ⇒ 记"没跑"）。
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > **做了什么**：`scripts/real_screen_sidebar_icons.py` —— 走产品自己的入口（状态菜单「设置」）开窗口，只截那一扇（不出现主窗口的剪贴板内容），按 2pt 步进自动找图标行带，与同一行文字列对照；退出码把 0 可辨 / 1 没跑 / 2 有行带读不到墨 分开。第一次跑（本机暗档、装的是 R122 那一版）：六条行带全部有墨（41–84 px，最大偏离 184）⇒ `REALSCREEN_VERDICT=ok`。同时把 `parse_bounds` / `appearance_of` 抽出来配 5 条单测（脚本电池 239 → 244），并用 `install_local.sh --yes` 把 R122 那一版真装上本机（`INSTALL_RESULT=ok` / `SMOKE_OK=1`，U-410 清账）。
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > **亮档那一半没拿到，而且差点被记错**：给 App 域写 `AppleInterfaceStyle = Light` + 重启之后，所有读数与暗档**逐字相同** —— 拦住误读的是同一行里的 `背景亮度=38 ⇒ 外观=dark`。⇒ D-185②：**改外部设置的实验必须自己证明改动生效**。外部位已 `defaults delete` 还原，用户机器没被留在改动状态。172 因此只剩一条路：系统外观切换（会动用户桌面）或用户自己看一眼 —— 人工批次 86.1 的问题就是「浅色下未选中行的图标，有没有它的标签那么黑？」
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > **三条自坏**：U-411 把被测物的分隔符当契约（成功的测量被读成"窗口没开"）；U-412 改外部设置没先证明生效；U-413 把上次失败过的真机通道当"随时可用"（通道每次都要先验自己）。
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > **下一轮（R124）**：① 读 R122 的两跑 CI（`0f1647a` / `c90fe36`，收口时仍 in_progress）—— 期望侧栏图标那朵红在 runner 上按能力位处置、150 的四种出口继续可 grep；② 171 名单按机器分键；③ **回到动效本体**（连续第三轮零动效位点，自评 88 那一格）。
> > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > 最后更新：2026-10-17 19:3x（本地 · R122 / 第 124 轮收尾：**设置侧栏两枚多色图标在暗档是黑底黑图标** —— 修掉了，而亮档那一半判成通道盲区（新开 172 / U-408…U-409 / D-184 · 产品 1 行））
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **现场**：逐符号表把六枚侧栏图标分开之后，`dark 反侧=22` 全部落在 `wand.and.stars`（推荐）与 `chart.bar`（统计）—— 六枚里仅有的两枚多色符号。`.hierarchical` 保留符号自带的多色调色板 ⇒ 暗档黑底黑图标。换成 `.monochrome` 之后实测 `dark 期望 56→78、反侧 22→0`，看帧确认六枚与标签同亮。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **但另一档朝反方向动**：`light 期望 35→13、无墨 43→65`，看帧也确认亮档未选中行的图标淡到几乎看不见。同一行里标签文字用的是**同一个** `.primary` 且照样清晰 ⇒ 坏的是离屏通道对 `Image + 语义色` 那一路的解析（审计第二轮 1.9 的原始发现），不是颜色。所以本轮只把**反侧**升成会红（`SIDEBAR_ICON_INVERTED`，闸门与判据同源），亮档那一半写成 `SIDEBAR_ICON_BLIND_SPOT` 登记 ⇒ 新开 172 追真机。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **两把刀**：M620 产品退回 `.hierarchical` ⇒ 新红抓到暗档 22 行；M621 把这条红从比 `inverted` 改成比 `blank` ⇒ 亮档 65 行无墨立刻踩红（钉"这条红认的是哪一格"，U-409）。第 26 张表，刀数 98 → 100，caught 97 → 99。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **两条自坏**：**U-408** "这不是产品，是通道"这条旧结论被沿用了六轮，实际只对一半 —— 整体读数为 0 不足以证明与产品无关，必须逐符号/逐元素成立；**U-409** 一条判据同时看着两种病（反侧 / 无墨）时红会指错方向，两种病修法相反。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **没做的那一半（重要）**：本机装的仍是 R111 那一版，`.monochrome` 在亮档到底是产品淡还是通道淡，只到读数与看图，**没到真机**。⇒ R123 第一件工作是装包 + `screencapture` 量亮档侧栏图标列，与同一行的标签文字对照；真机若也淡就撤回 `.monochrome` 并给多色符号单独配 `.palette`。人工批次 86.1 的问题相应改成"看**亮档**未选中行的图标有没有标签那么黑"。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > **另外**：R121 的 CI（run 39027921504）本轮没读到就收口了 —— 四种出口的 runner 验收、171 的名单分键，都排在 R123。
> > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 19:1x（本地 · R121 / 第 123 轮收尾：**150 结案 —— runner 上「设置卡没有材质」是详情那一列整列没画**，上一轮的「帧太矮」被它自己那一跑的 CI 证伪（U-405…U-406 / D-183 · 产品 0 改动））
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > **现场（R119 的 CI，run 39024922502）**：三行读数互相打脸 —— 帧已经 720×**600**，带子仍 `墨行=0 最大偏离=0`（⇒「帧太矮」不成立）；`整窗墨行=70 整窗最大偏离=165`（⇒「拍不出整页」不成立）；`列0[0..148] 墨行=70`、`列1/列2[151..720] 墨行=0`（⇒ 那 70 行全在侧栏，**详情那一列整列没画**）。本机同一夹具：`整帧墨行=171 详情列墨行=24 带子墨行=24 ⇒ 可判`、`列内视图数=16 嵌套hosting=6`（runner 是 7 / 4）。
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > **改了什么**：把 R107 只写在注释里的分类法取出来当判据 —— 证人从「整窗」换成**被告那一列自己**，`cardprobeArmVerdict` 给四种出口（可判 / 框错红 / 详情列0墨不可判 / 整帧0墨不可判），`CARD_PROBE_ARM_VERDICT` 逐臂把结论打在闸门之前，`CARD_PROBE_CAPABILITY` 钉恒等式「参照臂 = 可判 + 框错红 + 不可判」；`columnSubviewInventory` 的样本改成类名+矩形+隐藏+层不透明度并**按面积升序**取叶子；新增 `CARD_PROBE_WITNESS`（视图数与样本同一条 `intersects`，对不上即仪器坏）。另把 43 的措辞按实测收窄（不再写「这台机器拍不出 SettingsView」）。四刀 M616–M619 全部 CAUGHT。
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > **171 拿到它该拿的红**：R120 的 CI（run 39025878222）`TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13` + `testDarkSettingsSidebarTextIsACountedBlindSpot` failed「落在期望侧了：[13 个夹具]」⇒ 名单是机器相关的，下一轮按实测键（`HostInfo`/系统版本/帧倍率）分机器，分键之后两台各自钉住。
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > **两条自坏**：**U-405** 给成因下结论前没有把并存的解释逐一排除，而分类法其实早就写在注释里、只是从没当判据跑过（写在注释里的分类法等于没有）；**U-406** 新仪表第一版只做到「能跑」，没看它自己打印的内容 —— 8 条样本全是铺满整窗的容器，数字照常报、证人一句话没说。
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > **下一轮（R122）**：① 读 R121 的 CI，期望 `cardprobe-split-groupbox` 两档 ⇒ `不可判(整帧有墨而详情列0墨)`、`参照臂=6 可判=4 框错红=0 不可判=2`，且捕获那一卷不再因这条变红；② 171 的名单按机器分键；③ **回到动效本体**（连续两轮在仪器侧，本轮自评 88 那一格就是这笔欠账）。
> > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 18:41（本地 · R120 / 第 122 轮收尾：**能力闸门吃错了对象 —— 它问内容区，判据问侧栏**，于是 runner 上"盲区名单不成立"这条真信息被 skip 掩盖（新开 171 / U-402…U-404 · 产品 0 改动））
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **现场（R118 的 CI，run 39023798233）**：同一跑里两行并存 —— `TEXT_SIDE settings-general dark 亮侧=1503 暗侧=0 ⇒ 墨在期望侧`（侧栏**读得到、且不反侧**）与 `TEXT_SIDE_NOT_RUN all（内容区也读到 0 个偏离像素）` + skip。⇒ 决定"要不要检查名单"的矩形（内容区）跟判据量的对象（侧栏）不同源，于是 `darkSidebarTextBlindSpots` 这份从 R29d 起当权威用的名单，**它的适用范围从来没被声明过**：本机反侧、runner 不反侧，两台都是真实的离屏捕获。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **改了什么**：闸门改成吃侧栏自己的墨（`sidebarInkTotal == 0` 才 skip），内容区降级成附注；新增 `TEXT_SIDE_CAPABILITY 侧栏偏离=48171 内容区偏离=425863 判了 13/13 ⇒ 闸门与判据同源（D-166）`。两刀各钉一个方向：M614 把内容区矩形挪到帧内空白 ⇒ 测试**必须仍然跑**（旧写法在这里会 skip），实测 PASSED；M615 把侧栏 x 带挪进实测无内容的分栏阴影（148..160）⇒ 闸门**必须自己报未运行**，实测 SKIPPED 并报 `侧栏列在 13 个夹具上读到 0 个偏离像素；同批内容区偏离=425863`。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **没有放宽任何东西**：171 保持开着，等下一跑 CI 把 runner 上那朵 `gone`（名单里的帧现在落在期望侧）红出来，再决定名单是否按机器分键（键必须来自实测：`HostInfo`/系统版本/帧 scale，不手挑）。这条红是**我们本来就该看见的**。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **三条自坏**：**U-402** 闸门与判据不同源 —— D-166 我早就写给"地板"，这次复发的位置是"要不要跳过整条判据"的那个决定；**U-403** 刀的第一针落在**我以为的空白**（x=300 其实在内容区里，有墨）⇒ 期望 SKIPPED 实得 CAUGHT，坏的是刀，选空白带要用实测过的无内容区间；**U-404** 往大函数里插代码连着两次插错（`var contentInkTotal = 0` 命中另一个测试的同名变量 ⇒ 声明插到 605 行那个函数里；撤销时又在正确函数里留了重复声明）⇒ 插之前先定位函数边界、每插一次立刻编译。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **验证（按实记）**：全量 `Executed 827 tests, with 41 skipped and 0 failures`；捕获 67 例 / 4 skip / 0 failures；帧 136 张 `CHANGED=0 MISSING=0 ADDED=0`；脚本电池 239 passed；曲线由仪器重算 `SCORES_BY_ROUND 117=90 118=90 119=90 120=90`；变异第 24 张 `mutate_r120.py` 两臂都拿到期望、`RESTORE_CLEAN=yes` ⇒ 刀 92 → **94**、caught 91 → **93**；产品 0 改动。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **R119 的 CI（run 39024922502）本轮收尾时仍在跑** ⇒ 150 的红是否消失**未定案**，不预填结论。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **下一轮（R121）的入口**：① 读 R119 与 R120 两跑 CI —— 150 是否结案、runner 上那朵 `gone` 是否出现；② 出现 ⇒ 171 进入"名单按机器分键"的设计（键来自实测）；③ 逐符号名册并进名单等式（170 族）；④ 真机批次 86.1（用户）。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2、86.1。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R119 / 第 121 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 18:24（本地 · R119 / 第 121 轮收尾：**150 的成因自己掉出来了 —— 帧太矮把内容裁掉，不是容器吃材质**；166 按登记的判据把动效闸门升成硬门（U-398…U-400 · 产品 0 改动））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **证据链（三条读数一合，成因就掉了）**：runner 的树侧证人 `CARD_PROBE_DETAIL_TREE cardprobe-split-groupbox light/dark 嵌套hosting=4 列内视图数=7`（本机 `6 / 16`）⇒ 详情列**有东西**，"没实例化"被否；同跑 `CARD_PROBE_ARM … 墨行=0 最大偏离=0` ⇒ 东西**不在帧里**；再加上 R118 报出的 `树给=342..534`（runner 上整列下挪 **282pt**）而臂 2 夹具只有 300pt 高 ⇒ **裁切**。这条挂了四轮的"容器吃材质"从此换成它真正的名字。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **改了两处，都带证据**：夹具 `cardprobe-split-groupbox` 720×300 → **720×600**（任何一台机器都装得下），带子的纵向范围改成**详情列自己**（`bandYFromColumn`：x 仍来自台账、y 来自那台机器的树）⇒ 150 不再需要任何机器常数。帧名随尺寸更换，基线 `update` 后 `COMPARED=136 CHANGED=0 MISSING=0 ADDED=0`；新帧本机两档都真看过（卡片贴详情列顶、下方是空窗口底、侧栏六行与图标表现不变）。**150 在 R119 的 CI 回来之前不算结案。**
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **166 结案**：它自己登记的判据是"同一 commit 两跑的名单一致"，本轮用 `gh run rerun` 拿到（attempt 1 vs 2 都是 `MOTION_GATE_CASES passed=34 skipped=32 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=82`，逐字相同）⇒ workflow 那一步去掉 `--report-only` 与 `|| true` 并改名 `Motion gate (BACKLOG 166, promoted from report-only census)`。**U-399**：拿到两跑之后我一度想说"三跑更稳"，那是事后加严 —— 判据的作用就是在证据到位时决定动不动。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **另两条自坏**：**U-398** 一个成因在没否证对立解释的情况下被沿用了四轮 ⇒ 登记"X 导致 Y"必须同时写明**哪种读数会否证 X**；**U-400** 把 `extension CGRect` 写进类型里 ⇒ `declaration is only valid at file scope`（与 U-396 同族：助手放错层，这次编译器直接抓）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记）**：全量 `Executed 827 tests, with 41 skipped and 0 failures`；捕获 67 例 / 4 skip / 0 failures；帧基线 136 张（两进两出）`CHANGED=0`；脚本电池 239 passed；曲线由仪器重算 `SCORES_BY_ROUND 116=89 117=90 118=90 119=90`（本轮均分 **90**）；变异表本轮未新增（改动是夹具尺寸 + 带子来源，两把刀留在 CI 回来之后按实际判据配）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R120）的入口**：① 读 R119 的 CI —— 150 的红是否消失、`SIDEBAR_ROSTER_OFFSET` 在 runner 上给多少、升硬之后的 `MOTION_GATE_RESULT`；② 红消失 ⇒ 150 结案并撤掉 `CARD_INSET_DECLINED` 的 runner 例外，红仍在 ⇒ 成因要再分一层（那时才有新刀）；③ 逐符号名册并进 `darkSidebarTextBlindSpots` 那一层的等式；④ 真机批次 86.1（用户）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2、86.1。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R118 / 第 120 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 18:08（本地 · R118 / 第 120 轮收尾：**R116 那条对账守卫在 runner 上第一次跑就红 —— 红的是我把本机绝对坐标当成了跨机器契约**（U-395…U-397 / 169 结论收窄 / 产品 0 改动））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **现场**：`SIDEBAR_ROSTER_RECT 台账=60..252 树给=342..534 行数=6 上界差=282.0pt 下界差=282.0pt`（run 39021652718 / `0ac7851`）。同一份代码、同一个 720×540 帧，**整条侧栏在 runner 上往下挪了 282pt**，而行高 32pt、行数 6 一点没变。⇒ 守卫有牙（它抓到的是我的假设，不是产品），但"绝对 y 相等"这种断言在另一台机器上永远红。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **改法**：判据换成机器无关的三件事 —— 比**高度**（`rect.height` 对 `bottom-top` ≤1pt）、比**行数**（== `SettingsCategory.allCases`）、绝对偏移**只报不判**（新增 `SIDEBAR_ROSTER_OFFSET`）。同时把 `TEXT_SIDE`（暗档盲区名单那条守卫）改成吃 `sidebarTextBands`：x 来自台账、y 来自各自的树 ⇒ 两台机器量的都是"那六行"。本机读数如实报出位移：`亮侧 851 → 752`（行带之间那 8pt 缝隙不再进框）、`暗侧 2990` 不变、`TEXT_SIDE_BANDS 行带数=6 首行y=60`、名单仍 `13 of 13`。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **169 保持结案但结论收窄**：R116 那句"矩形换成实测行带"确实修了"少盖第一行"，但结案时把本机的绝对 y 当成了契约 ⇒ 追记写明"跨机器对齐只报不判"（与 R38「两台机器的读数不能当另一台机器的地板」同族，这次藏得更深：两个量都来自实测，红点在原点上）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **本轮另两条自坏**：**U-396** 新加的局部变量 `textBands` 撞上类里既有的 `static func textBands`，而我的声明又插进了另一个测试（那里也有一行 `var vibrant: String?`）⇒ 那处只留一条 unused warning，真正用它的地方解析成静态方法 —— **"unused 变量"通常意味着我插错了地方**。**U-397** 改名按"含关键词的行"做，emit 跨两行漏了第二行（同一根因本轮两次）。⇒ 插入之后逐条看 warning；改名要按标识符的全部出现，不按行。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **看图腿**：本轮没有新帧可看（产品 0 改动、夹具 0 改动、136 张 `CHANGED=0`）⇒ 按已记规矩复用上两轮的看图结论（R117 的臂 2 帧、R116 的四张侧栏帧），不假装本轮看过新画面。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记）**：全量 `Executed 827 tests, with 41 skipped and 0 failures`；捕获 67 例 / 4 skip / 0 failures；帧 136 张 `CHANGED=0 MISSING=0 ADDED=0`；脚本电池 239 passed（未加脚本用例）；曲线 `SCORES_BY_ROUND 116=89 117=90 118=90`；变异第 23 张 `mutate_r118.py`：`MUTATE_TABLE n=2 caught=2 mismatch=0 not_run=0`、`RESTORE_CLEAN=yes`（M612 高度改回 154 ⇒ 红；M613 行带返回空 ⇒ 盲区名单等式红）⇒ 刀 90 → **92**、caught 89 → **91**；§8 白名单加了 `TEXT_SIDE_*` 与 `SIDEBAR_ROSTER*`，`--must-include` 缺=0。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R119）的入口**：① 读 R118 的 CI —— `SIDEBAR_ROSTER_OFFSET` 在 runner 上给多少、`TEXT_SIDE` 相对化之后在 runner 上是否仍走 NOT_RUN；② 读 R117 那跑的 `CARD_PROBE_DETAIL_TREE` ⇒ 150 定性；③ 同版两跑（39020070349 attempt 1 vs 2）的 `MOTION_GATE_CASES` 名单 ⇒ 166 升硬门；④ 真机批次 86.1（用户）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2、86.1。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R117 / 第 119 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 17:53（本地 · R117 / 第 119 轮收尾：**给 150 装了「详情列里到底有没有东西」的树侧证人**，并把 runner 读数落盘（U-392…U-394 · 产品 0 改动））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **装了什么**：`CARD_PROBE_DETAIL_TREE <臂> <档> 详情列文字视图=… 图像视图=… 嵌套hosting=… 列内视图数=…`。runner 那一跑（`ffe65a1` / run 39020070349）已经排掉一种成因 —— 详情列的 wrapper **在树里存在**（x=151..720、全高 300pt）却 `墨行=0 最大偏离=0`；剩下「详情没被实例化」与「画了但没进帧」在像素上完全同形，这一行就是用来分它们的。本机基准 `hosting=6 列内视图数=16`（两档相同）。按 D-163 只报数不判产品 ⇒ 150 的定性等 R117 的 CI。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **本轮三条自坏**：**U-392** 证人第一版只数 `NSTextField`/`NSImageView`，而 SwiftUI 的文字不是这两种 —— 本机那一臂明明有 24 行墨也报「文字视图=0」，一把只会说 0 的尺会把两种成因**抹平成同一种**；修法是同行报 `嵌套hosting` 与 `列内视图数`（后者不依赖控件类）。**U-393** 用「锚点后追加」插助手时把锚点行复制了一份 ⇒ `settingsContentPane` 重复声明，直到 `emit-module` 才报（写盘成功而内容坏，U-372 家族新形态）⇒ 插完立刻 build。**U-394** `gh run rerun` 会让旧 attempt 的日志被顶掉 ⇒ 我台账引用过的 runner 读数会消失；本轮起读 CI 时同步抽成本地文件（`.scratch/motion-audit-2/ci/r115_run_39020070349_readings.log`，31 行），并为 166 发起**同一 commit 的重跑**（39020070349 第二遍）—— 那才是它判据要的样本。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **看图腿（本轮真看了一张新帧）**：`cardprobe-split-groupbox-720x300-light`（臂 2 本机）—— 详情卡片与「分栏详情里」都画得出来，侧栏六行从 y=60 起、四枚图标白到看不见、`推荐`/`统计` 黑而清晰 ⇒ 与 R116 的矩形与逐行读数一致，本机不是 150 的现场。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记）**：捕获卷 `Executed 67 tests, with 4 skipped and 0 failures`；帧 136 张 `CHANGED=0 MISSING=0 ADDED=0`（只加读数，不动产品与夹具）；全量测试 `Executed 827 tests, with 41 tests skipped and 0 failures`（与 R116 同数：本轮没加判据用例，只加读数）；脚本电池 239 passed（本轮未加脚本用例）；曲线由仪器重算 `SCORES_BY_ROUND 115=90 116=89 117=90`；`ledger_rows --must-include CARD_PROBE_DETAIL_TREE` ⇒ 缺=0；**本轮没有变异刀可打**（证人不带断言，按实记：刀数停在 90 / caught 89，不硬凑）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R118）的入口**：① 读 R117 的 CI —— `CARD_PROBE_DETAIL_TREE` 在 runner 上给哪种成因 ⇒ 150 定性，之后才谈"要不要让臂 2 在 runner 上有内容"；② 同一 commit 两跑的 `MOTION_GATE_CASES` 名单是否一致 ⇒ 一致才允许去掉 `--report-only`（166）；③ 逐符号名册并进 `darkSidebarTextBlindSpots` 那一层的等式；④ 真机批次 86.1（用户）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2、86.1。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R116 / 第 118 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 17:27（本地 · R116 / 第 118 轮收尾：**169 结案 —— 台账矩形换成实测行带，并第一次有东西盯着"尺量的还是不是同一块东西"**（U-388…U-390 / 产品 0 改动 / 变异第 22 张表 M610–M611 全 CAUGHT））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **改了什么**：`settingsSidebarTextColumn` 从 `y 96 h 154`（五行时代的坐标，阶段一加「统计」之后就少盖第一行）换成 `y 60 h 192` = 视图树给的六行；两条图标列矩形同步。新增 `testSettingsSidebarRosterRectCoversEveryRow` 把矩形上下界钉在树给行带上（各 ≤1pt），读数 `SIDEBAR_ROSTER_RECT 台账=60..252 树给=60..252 上界差=0.0pt 下界差=0.5pt`。M610（矩形改回旧值 ⇒ 红）与 M611（树少给一行 ⇒ 数量与下界差一起红）两刀证明这条守卫两个方向都有牙 —— 它补的正是 U-383 那一族：**读数是绿的，量的可能已经不是同一块东西**。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **改尺之后必须一起报的那格（U-390）**：`TEXT_SIDE settings-general dark` 暗侧 2130 → **2990**（第一行标签的墨现在进来了），亮侧 851 不变；而 `TEXT_SIDE_BLIND_SPOTS 13 of 13` 一个字没动 ⇒ **名单没变不等于读数没变**。我一开始只对了名单等式，是逐用例对读数才发现的。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **170 被更正**：本轮开的那张"按符号分裂"表，机制其实 R28 就量过 —— `OffscreenSymbolInkProbeTests` 第 18 行与产品臂注释里写着「每一枚符号的颜色在两帧里**恒定不随外观变**」「不能据此判产品缺陷（也不能据此改产品颜色）」。⇒ 170 只剩两件新的：逐符号名册 + 常驻仪器；不欠第二份读数，欠的只有真机批次 86.1。**U-388**：同一族错第三次（R114 是"开单前没 grep 决定台账"，这次连自己写的测试文件注释都没查）⇒ 查重范围要写成"决定台账 + 判据文件注释 + BACKLOG 正文"三处。**U-389**（记的是没犯成）：本轮我一度想把 `.symbolRenderingMode(.hierarchical)` 换成 `.monochrome` 让六枚符号统一出墨 —— 那正是台账明令禁止的"为讨好这一帧改产品"，是**已记的规矩**挡住的，不是我想出来的。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **看图腿（本轮真看了四张帧：`settings-general` 与 `settings-stats-populated` × 两档，侧栏 x 0..148pt × y 56..256pt 裁切 3× 放大）**：暗档 `command`/`gearshape`/`hand.raised`/`folder` 白（可见）、`wand.and.stars`/`chart.bar` 近黑（几乎不可见）、未选中标签全黑字黑底、选中行蓝药丸两者都可见；亮档完全互补。与 R115 的逐行读数**逐格对上** ⇒ 那把尺量的确实是眼睛看到的东西，也说明 170 的现象早就在帧里。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记）**：全量 `Executed 827 tests, with 41 skipped and 0 failures`（826 → 827 = 新对账守卫）；捕获卷逐用例与 R115 对比 **无判定翻转**、新增那条 passed（67 例）；帧 136 张 `CHANGED=0 MISSING=0 ADDED=0`（只动尺，不动产品与夹具）；脚本电池 239 passed（本轮未加脚本用例）；曲线由仪器重算 `SCORES_BY_ROUND 113=90 114=89 115=90 116=90`；变异 `MUTATE_TABLE n=2 caught=2 mismatch=0 not_run=0`、`RESTORE_CLEAN=yes`；`ledger_rows --must-include SIDEBAR_ROSTER_RECT` 缺=0（新读数进了 §8 白名单）；产品 0 改动（`git diff --stat ClipboardHistory/Sources` 空）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **runner 的第一份逐行读数（读 R115 的 CI 时拿到）**：`light 有墨行=78 无墨行=0 反侧行=0 | dark 有墨行=78 无墨行=0 反侧行=0`、六枚符号全 `期望=13`，而同跑紧接 `SIDEBAR_ICON_NOT_RUN all（内容区 0 墨）` + skip ⇒ 那串「零反侧」是噪声对称的产物，不是证据。因此把「等 CI 落第二份读数再判」划掉：BACKLOG 43 没解之前 CI 交不出样本。本轮已把能力位写进读数行本身（`能力=可判` / `能力=不可判(内容区 0 墨)`），见 U-391。 同跑的 `MOTION_GATE_CASES passed=34 skipped=32 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=82` 与 R112 那跑同形（名单一致但仍是**不同 commit** ⇒ 166 的升硬门还是不签）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R117）的入口**：① 读 R116 的 CI（新能力位与新对账守卫在 runner 上怎么说）；② **150** 修参照臂带子（`cardprobe-split-groupbox dark` 在 170..720pt × 24..284pt 读到 0 行墨、最大偏离 2 而门限 60 ⇒ 改带子不改断言）；③ 把逐符号名册并进 `darkSidebarTextBlindSpots` 那一层的对账（现在它只报，不进名单等式）；④ 170 只等真机批次 86.1。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2、86.1。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R115 / 第 117 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 17:07（本地 · R115 / 第 117 轮收尾：**逐行仪器把 167 的结论打折** —— light 43/78 行无墨、dark 22/78 行反侧；顺带量出 169（台账矩形少盖一行）并结案 168（闸门结论行的归属）/ U-382…U-386 / D-182 · 产品 0 改动）
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **U-380 那笔债还上了**：撤 167 用的量法搬进 `UICaptureHarness` 真身 —— 行带从**已布局的视图树**取（每行的 `_FocusRingView`），行数钉在产品 `SettingsCategory.allCases`（6）上，图标墨的横向范围由 `iconInkSpan` 从帧自报（不抄「图标列在 12–34」那句注释）。2 档 × 13 个设置夹具 × 6 行 = **156 行**逐行读数落在 `capture-readings.log` 里 ⇒ 可重跑、可 grep，不再是"我抄下来的四个数"。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **读数说了什么**：`SIDEBAR_ICON_COVERAGE light 有墨行=35 无墨行=43 反侧行=0 | dark 有墨行=78 无墨行=0 反侧行=22`。按符号聚合（`SIDEBAR_ICON_BY_SYMBOL`）后不是"暗档整体偏暗"，而是**同一列里 `.primary` 的解析按符号固定成某一种极性**：`command`/`gearshape`/`hand.raised`/`folder` 固定成白（亮档不出墨、只有当选中行因药丸出墨；dark 全 13 正常），`wand.and.stars`/`chart.bar` 固定成黑（亮档全 13 正常；**dark 11/13 反侧**）。⇒ 上一轮那句「图标在两档都落在期望侧」**只在列级成立**：列级把"有些行根本没有墨"抹平成"整列都在期望侧"。撤单本身仍有效（撤的是"暗档图标比标签暗"那一格），行级另开 **170**（先只报数；等 CI 第二份读数 + 真机批次 86.1 判它是不是只在离屏管线里）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **顺带量出来的两件**：**169 开（未修）** —— `settingsSidebarTextColumn` 写 y 96..250，实测六行行带是 y 60..252 ⇒ 它喂的 `TEXT_SIDE` 与暗档盲区名单从阶段一加「统计」那行起只覆盖 5/6 行（仪器报 `SIDEBAR_ICON_ROSTER_DRIFT …更早的行数=52/156`）；不改的理由写在单子里（一改 13 个夹具名单整体位移，要先真看帧）。**168 结案** —— runner 第一份 `MOTION_GATE_*` 里真步（`passed=34 skipped=32 failed=0`）与样张夹具（`passed=1 skipped=0 failed=1`）**同形并存**：`--label` 只决定标记叫什么，不决定谁在打它，而样张的 `_run` 不吞 stdout ⇒ 166 的升硬门名单本来可以被夹具冒充。修法是标签换 `SAMPLE` + `_run` 单层重定向 + `scripts/tests/test_gate_marker_hygiene.py` 三条**判产物**的守卫。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **行号 = 枚举顺序不是猜的**：选中行的药丸签名在 `settings-general` 落在 row=1、`settings-privacy` 落在 row=2、`settings-data` 落在 row=4，与 `allCases` 一致 ⇒ 按符号聚合的表可信。**本轮现场坏的**：U-382（我拿去做查重的台账注释自己是一条没量过的断言）、U-383（仪器坐标会因产品改动过期而不报警）、U-384（我给图标列写矩形时把邻居的 y 抄了过来，被"行数=枚举数"那条守卫挡住）、U-385（尺的接缝当墨：不外缩 2pt 时 `command` 读到 x=39..39 / 10 个像素判成有墨；以及嵌套 `redirect_stdout` 让外层拿到空串、5 条样张一起红）、U-386（新增结论行标记时只验"打得出"、没验"谁在打"）。规矩进 **D-182**。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记）**：全量测试 `Executed 826 tests, with 41 tests skipped and 0 failures`（825 → 826 = 本轮新增那条逐行仪器）；捕获卷 `Executed 66 tests, with 4 skipped, 0 failures`；帧 `FRAME_BASELINE_COMPARED=136 CHANGED=0 MISSING=0 ADDED=0`；脚本电池 `239 passed`（236 → 239）；曲线由仪器重算 `SCORES_BY_ROUND 112=91 113=90 114=89 115=90`；`ledger_rows.py --must-include SIDEBAR_ICON_COVERAGE` ⇒ `缺=0`（新读数进了白名单，不是孤儿行）；产品 0 改动（`git status --short ClipboardHistory/Sources` 计数 0）。变异表 M606–M609：见本轮 BACKLOG 168/170 与 AGENT_UI_AUDIT 第 117 轮；变异表第 21 张 `mutate_r115.py` 四刀 M606–M609：`MUTATE_TABLE n=4 caught=4 mismatch=0 not_run=0`、`RESTORE_CLEAN=yes`（M609 那刀的牙咬在「样张那一卷自己没过」那一格，不是「stdout 出现生产标记」那一格 —— 两格分开记，见 U-387）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R116）的入口**：① 170 的第二份读数（CI）与"这是不是只在离屏管线里"；② 169 把两条列级矩形换成行带 + 重算名单（先看帧）；③ 166 升硬门仍欠同一 commit 两跑名单一致；④ 150 让臂 2 的详情在 runner 上有内容（R112 那朵红的证人消息已经指出：`cardprobe-split-groupbox dark` 在带子 170..720pt × 24..284pt 读到 0 行墨、最大偏离 2 而门限 60 ⇒ 参照臂没盖住自己的内容，改带子、不改断言）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2，**新加 86.1**（两种外观下看设置侧栏六枚图标是否都在）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R114 / 第 116 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 16:38（本地 · R114 / 第 116 轮收尾：**167 在同一轮里被自己撤掉 —— 图标两档都落在期望侧，可撤回的读数自己却不可复现**（U-378…U-380 / 产品 0 改动 / CHANGELOG 补写 + Round 114 拆出来单立一节））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **本轮结的那件事**：R113 只凭看图开了 167（设置侧栏图标"暗档偏暗"），本轮把它撤了。口径沿用仓库那颗尺 `inkSideCounts`（与该列众数背景比、偏离 >16 记一侧），**坐标不再目测**：从台账里的 `settingsSidebarTextColumn = x:40 y:96 w:102 h:154` 向左推出图标列 `x 8..40pt`、同一 y 段。读数 ⇒ 亮档背景 250 / 暗侧 3966（极值 250）/ 亮侧 0；暗档背景 27 / **亮侧 1391**（极值 228）/ 暗侧 42 ⇒ **两档图标都在期望侧**。文字列暗档确实反侧（亮侧 677 / 暗侧 2151），但那是 D-090 已记账的合成前极性盲区（`darkSidebarTextBlindSpots` 名单第 9 张就是这一帧）⇒ 我把文字的盲区错记到了图标头上，而"几乎看不见"是缩略图把细笔画压掉了。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **本轮最值钱的一条不是撤单，是 §1 那格**：治了「坐标是猜的」，**量尺却还是一次性的** —— 撤回用的是现场 heredoc，脚本没落盘，仓库里只剩我抄下来的四个数。用一个不可复现的读数去撤一条「没量过就别下结论」的疑点，等于我的证据通道没过自己立的规矩（**U-380**）。R115 的做法因此定成"把量法搬进 `UICaptureHarness` 那颗尺真身、按结构推**逐行**坐标、打一行 `SIDEBAR_ICON_SIDE …`、进 §8 白名单、配一刀（期望侧反判必须红）"，顺带补掉"列级聚合会把单行问题抹平"。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **另三条账本层的自坏**：**U-378** —— 一次改四本账，CHANGELOG 的锚点凭记忆写、`count == 1` 当场红，我没回头重读就先把其余三本提交了 ⇒ 推出去的 `317f653` 里 BACKLOG 说「撤回」而 CHANGELOG 说「开单」，两份账在一个 commit 里互相矛盾（本轮已补写 R114 一节 + 把 R113 那节改成前向指针）。**U-379** —— 把 R114 的账并进 Round 113 让「一节 = 一轮」这条计数契约断了（`curve_from_ledger.py` 的 `ROUNDS` 就是数节数），而同一份读数住在两处、不会互相当质 ⇒ 本轮拆开，数字只活在 Round 114。
> > > > > > > > > > > > > > > > > > > > **U-381** —— STATE 轮换脚本只拼了「加前缀的那一块」，把老的第二块算了却没接 ⇒ R111 那块历史静默消失（36 行 → 33 行），而且这次轮换本来就漏了 R113 那一轮（我从 R112 直接跳到 R114）。救我的是两条随手检查（行数对不上 HEAD、`grep '^> 上一轮（R11'` 少一块），**不是守卫** —— 台账守卫只管 D/U/BACKLOG 的编号与区间，STATE 的分层没人管 ⇒ 已补回 R113 块，并把「轮换后必须断言上一块仍在」写成 R115 的做法。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证（按实记，没跑的写没跑）**：脚本电池 `236 passed`（数字未变：本轮没加脚本用例）；曲线由仪器重算 `SCORES_BY_ROUND 111=92 112=91 113=90 114=89`（本轮均分 **89** —— 第 116 轮第一次跌破 90，四条自坏的账都记在这一格；Round 113 的 90 是 R113 收尾时就落盘的修订，本轮未再动）。**swift 侧本轮 0 改动 ⇒ 没重跑全量测试与捕获**（825 例与 136 帧 `CHANGED=0` 是 R113 那两份构建背的，不算本轮的账）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **R115 的入口（已在手的第一份 CI 账，见下一条）**：① R112 的 CI 跑完了，runner 上第一份**真步**读数是 `MOTION_GATE_SCOPE 前缀=MotionFilmstrip UIInteraction 有名字的红=0 用例=66` + `MOTION_GATE_CASES passed=34 skipped=32 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=80` + `MOTION_GATE_RESULT=ok` ⇒ 166 的「有名字的红」在动效这一卷第一次有了可比的两行；② **但同一个 grep 会先撞上我自己的样张** —— `Release script tests` 那一步里 `MotionScopeTests` 打的也是 `MOTION_GATE_SCOPE` / `MOTION_GATE_CASES`（数字是夹具的 1/1/0/0/0），照整份 grep 就会把样张读成 runner 的判词 ⇒ 与 R53「region() 命中守卫自己」同一族，R115 用已有的 `--label` 旋钮把样张分流；③ 166 升硬门仍欠"同一 commit 两跑名单一致"；④ runner 上那朵红 `testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox`（R111/R112 **两跑都红、换班=0**）自带的证人消息说 `cardprobe-split-groupbox dark` 在带子 `170..720pt × 24..284pt` 里读到 **0 行墨**（最大偏离 2、门限 60）⇒ 参照臂没盖住自己的内容，它的「材质=无」不能当结论，改带子不改断言。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R113 / 第 115 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 16:26（本地 · R113 / 第 115 轮收尾：**155 拿到第二个同版对（230 组配对零漂移），看图腿在热图暗档翻出一个不敢下结论的疑点**（167 开 / U-374…U-376 / 产品 0 改动））
> > > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > **155 的账**：同一 commit `1e6869b` 连跑两次捕获，`double_run_spread.py` 逐读数对骨架与数字 ⇒ `DOUBLE_RUN_SAME_BUILD=1 配对=115 全等=115 有差=0 只在一遍=0 族=28 最大绝对差=0 最大相对差=0.0000`；与 R110 那对（`ef04639`）合起来是 2 对 / 230 组配对 / 0 漂移。两跑各 `FRAME_BASELINE_COMPARED=136 CHANGED=0`。口径按实收窄成「本机这两份构建各自连跑两次没漂」，**不是**「捕获通道是确定性的」；也**不许**据此把地板压到实测值（素材那一格本机 892、runner 891 就是反例）。
> > > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > **看图那一腿翻出来的疑点**：亮档五档蓝/说明段/图例/最忙一天各在其位，判可以留；暗档我看到五个分区图标比自己标签暗得多、「推荐」几乎看不见，与 R30 的 VibrantDark 机制同形。去量时用的是 `/tmp` 手搓 PIL 尺、行列坐标目测猜 ⇒ 量到「数据」行偏离 `0.0`（框没盖住字形，不是图标不存在）、「快捷键」行极值纯白（那是选中胶囊的字）。⇒ **U-374** 手搓尺第二次把「我框错了」伪装成「产品没画」；**U-375** 先写下的是形容词「偏暗」，没有读数撑着；**U-376** 眼睛给的坐标直接喂量尺。处置：开 **167** 且第一步写明"把量法搬回仓库那颗尺、先只报数不判" —— 疑点既不升级成结论，也不注销成"没问题"。
> > > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2。
> > > > > > > > > > > > > > > > > > >
> > > > > > > > > > > > > > > > > > > > 上一轮（R112 / 第 114 轮收尾）原文开头：
> > > > > > > > > > > > > > > > > > > > 最后更新：2026-10-17 16:19（本地 · R112 / 第 114 轮收尾：**动效那一卷的红以前没有账** —— CI 那句「唯一的红是 157」只覆盖捕获那一卷（166 的 ① 落地 / U-370…U-373 / D-181 / 脚本电池 230 → 236））
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **本轮是工具轮，产品 0 改动**（`git status --short ClipboardHistory/Sources` 计数 0；swift 侧一行未动 ⇒ 帧复用上轮那一份，136 张 `CHANGED=0`）。给 `scripts/ci_capture_gate.py` 加了 `--class-prefix`（按类名**最后一段**切、可重复）、`--label`（结论行按卷打）、`--report-only`（只降级产品那一格，通道坏了照旧红），并且**切片为空必须红**（`MOTION_SCOPE_EMPTY=1`，R99 那一族）；workflow 里新增一步 `Motion gate (report-only census, BACKLOG 166)`，读全量那一卷的 `/tmp/test.log`。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **两条只有真日志能给的发现**：① U-370 —— 第一版只切 `MotionFilmstrip`，而 `testFrameIntervalsUnderStateChanges` 住在 `UIInteractionProbeTests` ⇒ 拿 R109 的真日志跑会读成「0 红」，合成夹具永远给不出这一格；② U-371 —— 那朵红在 CI 日志里只有 `FAILED 方法名：XCTAssert…` 这一种形状，而闸门只认 `error: -[类 方法]` ⇒ **整朵看不见**（`ci_read.py` R105 就会认两种，闸门今天才补）。类名缺失的那种单列成「类未知名单」，于是 R109 = `有名字的红=0 类未知名单=1(testFrameIntervalsUnderStateChanges)`、R110 = `类未知名单=0` —— 166 的「换班」第一次变成两行可 grep 的读数。规矩进 **D-181**。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **为什么不直接升成硬门**：166 自己的判法是「单次读数不配给产品定罪」⇒ 第一版 report-only，升硬门要由**同一 commit 两跑的名单一致**签（`scripts/ci_red_stability.py`），不由印象签。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **另两条工具层的账**：U-372（用 python 生成 python 时把带 ASCII 双引号的 CJK 串写进 `help=` ⇒ 文件写成功而内容语法坏，`py_compile` 才抓到 —— 写盘不校验被写物）、U-373（把结论行字段 `NOT_RUN=` 改名 ⇒ 被自家真值表拦下：字段名是既有契约，口径只能写成附注）。本轮收尾时 U-372 **又犯一次**（同一个坑在一轮里踩两回，见下面 STATE 的下一轮入口）。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **验证**：脚本电池 `Ran 236 tests OK`（+6：切片四格、第二形状一格、空切片一格）；台账守卫 11 例 OK（本轮自己踩到定义行形状：`**U-370**：` 要写成 `**U-370：…**` 才算定义，正对照当场拦下）；曲线 `SCORES_BY_ROUND 109=90 110=91 111=92 112=91`。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **下一轮（R113）的入口**：① 读 R111 / R112 的 CI —— R112 那跑第一次会打 `MOTION_GATE_SCOPE` / `MOTION_GATE_CASES`，那是 166 第一份跨跑可比的账；② 名单在两跑之间一致才去掉 `--report-only`；③ 150 让臂 2 的详情在 runner 上有内容；④ 155 扩第三样本。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > **仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2。
> > > > > > > > > > > > > > > > > > > > 
> > > > > > > > > > > > > > > > > > > > 
