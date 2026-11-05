# R578 读数台账（工作笔记，随本轮台账笔提交；所有串都由落盘文件派生，不是手打的）

## ⓪ CI（`/tmp/r578/ci-41980266648.log`、`/tmp/r578/ci_extract.txt`、`/tmp/r578_steps.txt`）

| run | commit | 现读 | 全部失败步骤（逐字） |
| --- | --- | --- | --- |
| `41980266648` | `c013d5d`（R576 补记笔，即 R577 主笔之前那一笔；派单里称"补记笔"） | `completed / failure` | `STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`（**`STEP[18]` 绿**） |
| `41994318725` | `1f0e4b2`（R577 主笔 = 当前 HEAD） | ⓪ 现读 `in_progress / conclusion 空` ⇒ **未到数**（不轮询）；收口前复核已到数，见下面"⓪b" |

- 日志字节数 `3,126,404` ⇒ "不在失败列表里"这次算读数。
- `@@COLDBUJI@@`、`@@COLDREGBUJI@@`、`@@COLDMECHBUJI@@` ⇒ 主窗 1.00x 实测=登记、浮层实测=登记 ⇒ **按机器登记的表第二次被同一台机器自洽签**。
- `@@HASMATRIXBUJI@@` ⇒ 这一跑的树里**不含** R577 的矩阵判据 ⇒ **到数 ≠ 能填 `EXPLANATION2` 的 1.00x 那一档**。
- `@@D12BUJI@@` ⇒ 映射表那一行第五次逐字相同。
- `executed=` 先读：判据卷 `Executed 230 tests, with 34 tests skipped and 15 failures`、全量 `Executed 1437 tests, with 89 tests skipped and 16 failures`、动效卷 `Executed 79/33/0`、`@@UISCANNERBUJI@@`。
- `@@CIGATEBUJI@@`、`@@MOTIONFLOORBUJI@@`（=1，与主笔同值；三跑序列 3→2→1 只在漂）、`@@FRAMEBUJI@@`（runner 自己两处一处 0 一处 1 ⇒ 与本机那 8 张是两件事，只登记不解释）、电池 `Ran 725 tests in 108.633s` / `python cases: 725`。
- **红名单包含关系**：这一跑 8 朵 = 主笔 6 朵 + `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` + `UICaptureTests.testRecordingCardFrameIsDeterministicAcrossRenders`；`只在主笔里出现的 = ∅` ⇒ "本轮没有新名字"成立、"红变少了"不成立。

## ⓪b 收口前复核（`/tmp/r578/ci-41994318725.log`、`steps_main.txt`、`ci_extract_main.txt` · 时刻 2026-11-05 17:34–17:37）

- `41994318725 ↔ 1f0e4b2` 现读 `completed / failure`；全部失败步骤逐字 `STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[18] On-screen probe coverage floor`、`STEP[19] Motion coverage floor`（四朵红；`STEP[18]` 五跑三红两绿 ⇒ 在漂）。
- `MAIN_EXPL2`（逐字见 CHANGELOG/STATE token `@@MAINEXPL2@@`）⇒ runner 上 ②=**被否**，与本机 2.00x 同一支 ⇒ 已把 1.00x 登记进 `declaredExplanationTwo`（来源=那一跑自己的读数，本机没有替它填）。
- `MAIN_SUMMARY` 逐字含 `分水岭=display_单独就够_上屏单独不够_runloop单独也够 同遍两读数相同=1 累计腿与独立乙A相同=1 正对照=6/6`。
- `MAIN_CAPTURE` = `Executed 231 tests, with 34 tests skipped and 14 failures`、`MAIN_FULL` = `Executed 1438 tests, with 89 tests skipped and 14 failures`、`MAIN_GATE` = `CAPTURE_GATE_CASES passed=197 skipped=33 failed=1 有名字的红=1 类未知名单=0 NOT_RUN=184`、`MAIN_RED` = 6 朵（与 R577 主笔同名同集合）。
- ⚠ 改完 `declaredExplanationTwo` 之后**又重跑了一遍固定链**（`/tmp/r578b/`：告警门 → 重捕帧 → 基线 compare → M1518/M1519 → 预检 → 全量）⇒ 下面 ②/刀/③ 的数以 `r578b` 那批为准，本文件上面那批是改之前的读数，两处若不同要现读对拍。

## ② 本轮推进（本机 2x · 最终代码状态那趟 `/tmp/r578b/d12_only.log` + `/tmp/r578b/capture.log`；`/tmp/r578/d12g.log` 那批是改之前的）

`D12_PREREQ 前置实测=显示通路那一步 冷态子层=-1 只走显示通路子层=2 只上屏子层=-1 只走夹具快门子层=2 快门算不算显示通路的一个实例=是 带前置的行数=5 同类相符=5/5 漂移量被写成地板处数=0`
`D12_REJUDGED 条=8 翻面=0 按行声明与快照相符=8/8 快照缺行=0 汇总与上轮逐字相同=1 前置相符=5/5 逐条证人=三条现扫+两条现量通道+一条环境键+一条前置实测`
`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关 离屏alpha通道采样=20160 不透明=2068 全透明=17261 产物采样=105000 产物全透明=0 窗口宽=750.0`
⇒ **八条一条也没翻面**；`夹具快门cacheDisplay` 由第四臂证明是"一次显示通路"的一个具名实例。
⇒ ⚠ **改之前那两版读数不是这个形状**：第一版 `翻面=` 打的是"分类有没有落全"（恒 0，除非有条目没落进三态），`同类相符=` 的分子直接等于分母（恒真），`前置改名=5/5` 同形。三个都是"读的不是它声称的那个对象"⇒ 本轮 commit 之前重读代码抓到，改成 `翻面=今天的实测 vs **上一轮按行快照**的不符行数`、`同类相符=(checked-mismatch)/checked`，并新增 `d12RowCategoriesR577`（八行独立抄本）+ 两条断言（`快照缺行=0`、`按行声明与快照相符=8/8`）。

## 刀（`/tmp/r578b/M1518.log`、`M1519.log`、`M1520.log`）

- **M1518 CAUGHT、RESTORE_CLEAN=yes**：把「投影宽度按余弦律」那行的前置写成 `上屏那一步` ⇒ `prerequisiteRowMatches` 走 `onScreenBuilds=false` ⇒ 红。只动声明这一边，四个现读数一字未动。
- **M1519 第一次落下 = PASSED（空刀）** ⇒ 暴露扫描门**瞎**：剥注释先剥块注释时，本文件一处文档注释里的 `/**禁用**）` 让 `/*…*/` 匹配一路吃到下一个 `*/`，**86 万个字符的真实代码被当注释删掉**（`覆盖该行的块注释匹配` 现读起点 684448、终点 1548868）。
- 修法：剥注释顺序改成"先行注释、再块注释"；新增 4 格合成真值表（含"注释里出现 `/*` 之后代码仍要看得见"那一格）。修完 **M1519 CAUGHT、RESTORE_CLEAN=yes**。
- 修完之后又两次被自己的门扫到：控制样本 `"if clear >= 200 …"` 与断言消息文本里那句含同形状的话 ⇒ 都改成**拼接/换写法**（门才回到读 0）。
- **M1520 CAUGHT、RESTORE_CLEAN=yes**（新门自己的刀，落在 `/tmp/r578b/M1520.log`）：只把 `d12RowCategoriesR577["角度单调"]` 抄成 `runner可判` ⇒ 表体一字未动、`声明==实测` 那条**旧**断言仍绿，红只从新门来：`XCTAssertEqual failed: ("1") is not equal to ("0")`（`快照不符` 那条），同一跑读数 `D12_REJUDGED … 翻面=1 按行声明与快照相符=7/8 …`。⇒ 证明"翻面"拿的是独立抄本而不是本轮自己那张表（否则改表永远不会红）。
- 下一轮从 **M1521** 起。

## ③ 655 三条

- 八张帧名逐字（见 STATE ③ / CHANGELOG）；本轮重捕 `COMPARED=356 CHANGED=8 MISSING=0 ADDED=0`，形状与 R577 一致（前四张各 19 颗、后四张各 12 颗）。
- `frame_baseline.py update` 一次都没跑；三条出路归用户。
- 漂移那条升级成**有刀**（M1519）；覆盖面照实写：钉写法形状，改名可绕；与 640 是两件事。相邻新读数：runner 同一跑两处 `夹具那步之后未画比例=0.8495 / 0.8511` ⇒ 漂的不只是 alpha 计数。

## ⑥ 禁碰证人（本轮碰的是捕获夹具那份测试文件 · 最终那趟 `/tmp/r578b/`）

`TRANSPARENCY_STATE isOpaque=0 窗口底色alpha=0.000 底衬=1 采样=39342 带内最小alpha=255 半透明样本=0/39342 洞范围=无`、`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位` ⇒ **这两条与 R577 逐字同**。
第三条**没签上**：`CLIPBOARD_HISTORY_UI_REALSCREEN=1` 那一趟 `TRANSPARENCY_MATERIAL 不透明 均值=0.1657 … 品红漏出=0`、反面臂 `撤掉底衬 均值=0.2929 … 品红漏出=0` ⇒ `XCTAssertGreaterThan(bare.magenta, 0)`（TransparencyForensicsTests.swift:1049）红；R568 那趟同一条判据读的是 `0.9339` 与 `品红漏出=319`。
排除记录：产品回归（`git diff --name-only` 里 `Sources/`=0）、区域被盖住（撤底衬那臂均值随我的操作移动 +0.1272）、整类顺序效应（整类跑 `0.2929` 与单跑 `0.2910` 两趟 `品红漏出` 同为 0）⇒ 剩**系统外观**一支：同一时刻 `defaults read -g AppleInterfaceStyle` = `Dark`，判据不锁 `window.appearance`。**缺 Light 对照实验**（不在授权内）⇒ 具名 `REALSCREEN_MATERIAL_ARM_APPEARANCE_SENSITIVE=dark-mode-supported-not-controlled`、新开 **656**（甲 锁 `.aqua` / 乙 按外观拆两档）归用户。
⇒ **禁碰数不抬（仍 14 面）**；地基那一格的证人今天按**两条**记，不写成三条。

## 台账卫生（dispatch ⑥ 那条的执行记录）

- 每次改完立刻 `git diff --numstat`：代码文件 `+163 / −0`、文档 `+1 / −0`。
- **一次 Edit 悄悄删掉一行**（两行 old_string → 一行 new_string，删了 `let rows = Self.d12Clauses`）⇒ 紧随其后的 numstat 检查抓到（该文件出现 `-1`），`git diff` 还原后改整块锚重写 ⇒ "兜底及格、事前才是规矩"（D-578 ④）。
- **一次抄数先写句子**：判据卷汇总我先写 `Executed 231 tests…`，现读 `230/34/15` ⇒ 草稿改回现读值。
