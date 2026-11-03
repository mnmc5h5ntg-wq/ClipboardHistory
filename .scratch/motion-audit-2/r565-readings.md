# R565 读数台账（第 564 轮 / Round 562）

规矩：每条读数必须带它的日志路径。截断 / 0 字节 / 没有 `Ran N tests` 或 `Executed N tests` 汇总行 ⇒ **不算读数**。
turn 边界时若那卷的进程还活着、日志还在长 ⇒ 等它自己跑完再读完整日志（既不重跑，也不把半截输出当结论）。
一段 = 一笔本地提交，**不 push**；全部提交等电池通过后一次性 push，再复核 ahead=0。

## 已到手

- `GIT`：`HEAD=origin/main=8eecbc7`、`ahead=0`、已跟踪改动 0；`api.github.com=200 / api.apple.com=200`（监督侧现读，本侧复核）。
- `CI_QUEUE`（开场，终端现读）：`41552571306↔4cfcfc6` **in_progress 已等 485s 结论=无**；`41552998637↔8eecbc7` **in_progress 已等 273s 结论=无 前面=1**；`41542718166↔6ef9ff1` concluded failure（R564 已读，不重读）。
  ⇒ 两跑都**没结论** ⇒ ⓪ 各格开场一律具名 `CI_NOT_RUN=in_progress`，不许写成「没红」，也不许写成「判到了」。收口前复述一次 `queue`，到数就逐格转成读数（数迟到就写补记，不回头改账）。
- `FRAMES`：`docs/frame_baseline.json` ⇒ 现读见 `/tmp/r565-baselines.log`。
- `ABSENCE` / `STREAK` / `KNIFE_MAX`：同 `/tmp/r565-baselines.log`。

- `逐字节撞号扫描`（356 帧，`/tmp/r565-dup.log`）⇒ 唯一哈希 346 / 撞组 8，逐组排除：
  `row-favorite-off`=`row-pinned-off`=`row-text`（三张都是"无标记"负臂）；`content-paused-idle`=`content-with-history`
  （R417 的负臂就是未暂停）；`quickpick-search-focus`=`quickpick-search-hover`（R415 明文「焦点与悬停共用同一档视觉」，
  `QuickPickSearchBackdrop.draw` 里两态同一 fill+stroke）；`detail-3-files`=`detail-3-files-row0`
  （`makePopulatedStore(selectingIndex: 3)` 选到的就是默认展示那一条）。⇒ 没有一组是产品缺陷；
  但基线里 6 张帧互为逐字节副本、不为任何断言单独作证 ⇒ **开 638**（仪器卫生）。
- `裸字号扫描`（全仓 Sources 里绕开 token 的硬编码字号）⇒ 只有 6 处：4 处 = R564 已证否的浮层徽标 `pointSize: 8`（637）；
  `SettingsView.swift:208` 的 `.system(size: 10)` = R495 的**负向帧缝**（产品路径走 `VisualFont.meta`）；
  `DetailPreviewViews.swift:384/386` 的 `monospacedSystemFont(ofSize: 13)` = 与 `VisualFont.body` 同值 ⇒ 换 token 是肉眼无变化，不落。
- `被机制当场否掉的猜想`：以为浮层搜索框焦点态"声明了没供电" ⇒ 现读 `QuickPickController.swift:86/160/440` 产品路径确实点亮 `focused`；
  顺带验了取证键的覆盖语义（`??` 在 `false` 时仍取键值 ⇒ 负臂能关掉边界，键没坏）。

## 已到手（产品位落地的这一格）

- `产品位＝浮层键盘提示的字芯对比`（R565 取靶扫描三「语义色 × 表面」命中）：
  `QuickPickKeyboardHint.color` 从前是 `.tertiaryLabelColor` —— 它是浮层上**唯一一句功能性文字**（R449 开它就是为了让用户不用猜键），
  而全仓其余次要文字（主列表时间行、行内三枚标记、详情 meta）都走 `.secondaryLabelColor`。
- `旧值（两条独立通道逐字对上）`：numpy 读 `quickpick-list` 底部那条带 ⇒ light 字芯 (140,140,140)/底 255 ⇒ **3.36:1**，
  dark 字芯 (127,127,127)/底 30 ⇒ **4.16:1**；Swift 判据同帧同带 ⇒ `HINT_CONTRAST light 底=255 字芯=(140,140,140) 对比=3.36:1`、
  `dark 底=30 字芯=(127,127,127) 对比=4.16:1`（`/tmp/r565-crit-red3.log`）⇒ **两档都跌破 4.5:1**，
  而同一张帧里候选行文字是 16–20:1（尺不是瞎的，淡的只有这一句）。
- `新值`：改成 `.secondaryLabelColor` 后 `HINT_CONTRAST light 字芯=(64,64,64) 对比=10.37:1`、`dark 字芯=(209,209,209) 对比=10.92:1`
  （`/tmp/r565-crit-green.log`，判据 `Executed 1 test, with 0 failures`）⇒ 过地板且**仍比候选行弱一档**（20:1 vs 10:1），设计意图未改。
- `禁碰 R550「提示 Esc」的证人`：`HINT_KEY_CAPS 键=Esc 高=7.85pt 宽=5.22pt 字号=11.0pt`（`/tmp/r565-hintcap.log`）
  ⇒ 与 R550 账上那两个数逐字相同 ⇒ 本轮只动了**颜色**，键名与字高那一面一字未动。
- `尺的两次自伤（都在落账前改掉）`：① 第一版把**整帧众数**当提示的底色 ⇒ light 档带内 99.8% 像素都算"偏差"，
  字芯被抗锯齿边稀释成 (163,163,163)、对比报 2.46:1（与 numpy 的 3.36 对不上）；改成**带内众数**后两通道逐字一致。
  ② 更早一版把 gamma 编码的 `bgLuma/255` 去比线性光的 `relLuma` ⇒ 暗档排序把**背景自己**排成字芯（报 1.02:1）。
- `刀`：**M1466 CAUGHT**（退回 tertiary ⇒ 3.36/4.16）、**M1467 CAUGHT**（再弱一档改 quaternary ⇒ 1.56/1.82），两把 RESTORE_CLEAN=yes；
  **M1468 试落即撤**：把"字芯"从偏差前 5% 改成全部偏差像素 ⇒ 读数 6.01/9.16:1 仍 ≥4.5 ⇒ 判据 PASSED ⇒ **空刀，不登记、不占号**
  （⇒ 下一轮仍从 M1468 起）。两张表已登记进 `mutate_needle_precheck.TABLES`。

- `1x 体检（降采样代理，不签字）`：`/tmp/r565-1x-preview.log` ⇒ 同一判据的口径搬到 1x 帧上：
  light `带底众数=255 偏差像素=828 字芯群=41 字芯中位=(145,145,145) 对比=3.15:1`（2x 是 3.36:1 / 106 像素），
  dark `带底众数=30 偏差像素=681 字芯群=34 对比=4.34:1`（2x 是 4.16:1 / 111 像素）
  ⇒ **1x 仍有几百个偏差像素、几十个字的字芯 ⇒ 这一格不会走 `scale-too-low` 那类出口**；
  比值随倍率只动 0.2 上下 ⇒ 判"比值"不需要按 scale 派生口径（R555 那一族在这里不适用）。
  ⚠ 这是 LANCZOS 代理，不是 runner 真 1x ⇒ 那一格留给 R566 ⓪(a)。

## 待读

- 预检三读（**串行**，与任何 swift 卷并行必撞锁）：`/tmp/r565-precheck.log`（`NEEDLE_PRECHECK` + `ARM_TOTAL`）、`/tmp/r565-hidden.log`（`HIDDEN_ARMS`）。
- ⓪ 两跑到数：`python3 scripts/ci_read.py steps <run>` + `gh run view <run> --json jobs -q '.jobs[].steps[] | "\(.number) \(.name) \(.conclusion)"'`（success 必须逐步读，不许从「不在失败名单」推）。
- ⓪ 各格正文：`python3 scripts/ci_read.py readings <run> BULLET_LEVELS HEAT_LEGEND_COVERAGE HEAT_LEGEND_NOT_RUN MOTION_MARKDOWN_MODE_FADE SKIP_ROSTER` + STEP[15] 的 `SelectionRevealAnimationTests` 形状（0.0 还是 R412 那个 1430）。
- 判据卷 / 帧重捕 / 全量 / 换装 / 电池：见 `chain_r565.sh` 的日志路径（跑之前先确认没有别的 swift 卷在跑）。

## 补正笔（收口后第二笔）· 三格改账 + 一格真修

- **ⓐ streak 那一格的解释改齐**（数没动）：门 `scripts/product_streak.py` 的口径是 **as-of** —— 第 N 轮的格 = N −（标签 < N 的最后一笔产品提交的轮次标签）= 564 − 559 = **5** ⇒ 读成「本轮**之前**的连读轮数」，本轮产品笔 `f6c2a1d` 不清零它，清零在下一轮（那时分界变成 564 ⇒ 那一格是 0）。从前写的「未推状态才数到 5、push 之后会变 0」是**错的解释配对的数**：push 之后 `--check` 仍报 `PRODUCT_STREAK_LEDGER_OK streak=5`（日志 `/tmp/r565-streak-post-push.log`）。
- **ⓑ 刀号互斥（本笔记上面那句「下一轮仍从 M1468 起」作废）**：名册现读 `grep -ho M14[0-9][0-9] .scratch/motion-audit-2/mutate_*.py | sort -u | tail` ⇒ 最高 **M1469**，`mutate_needle_precheck.py` 的 TABLES 里 r565 那一批是 **M1466/M1467/M1468/M1469 四把真刀**（B 笔 `020cef3` 登记的 M1468/M1469 是路径卫生守卫那两把，全 CAUGHT）。那把试完就撤的空刀**从来没占过号** —— 它的草稿临时借过 `mutate_r565_m1468` 这个名字，被 B 笔用掉了 ⇒ 借用作废，R566 从 **M1470** 起。六处账（U-2443 / D-565 ③ / CHANGELOG / ITERATION 正文与七维表 / 补记 ④ / 自伤 ⑥④）由 `.scratch/motion-audit-2/patch_r565_knife_number.py` 一次改齐。这是「同一轮里两处互斥地说一件事」**第三次犯**（R563 的 636、R564 的读单、R565 的刀号），机械形状都一样：后一笔沿用前一笔的草稿措辞，没跟同一轮已落盘的那一笔对账。
- **ⓒ 真修（判据文本之外的一格）**：`commit_round_identity.py` 把退化说明写进 `范围=` 的**值**里 ⇒ 那一行按空格切成「键=值」，一个 ASCII 空格让判它的测试 `ValueError: dictionary update sequence element #1 has length 1` 崩（不是断言红，是解析崩）。改成 `退化=未推的为空` 另开一格 + 新门 `test_channel_values_contain_no_spaces`。**这把没登记刀**（门自己就是判据：把标签写回带空格立刻红）⇒ 账里具名「无刀、靠活门」。**R564 的绝对根打死 runner、R565 的空格打死本机电池**：同一族第二种坏法 = 通道值里不许含分隔符。
- **ⓓ 现读**：`COMMIT_ROUND_IDENTITY 范围=HEAD~1..HEAD 退化=未推的为空 笔=1 无R前缀=0 身份缺失=0 不一致=0` / `COMMIT_ROUND_IDENTITY_RESULT=ok`；`PRODUCT_STREAK_LEDGER_OK streak=5`；`SOURCES_CELL 账上=R565/f6c2a1d git=R565/f6c2a1d 一致=是`；清账 `格=162 声明=63 不成立=0/63`；电池 **`Ran 710 / OK (skipped=5)`、退出码 0**（日志 `/tmp/r565-battery6.log`；709→710 = 那条新门，台账里写的 709/5 是它自己那一批的真读数 ⇒ 不改数、只在此补记）；本轮各节未渲染占位符（percent 后接字母）逐节现读 = **0**（脚本按节定位：STATE 3 节 / UI_AUDIT 第 564 轮 / ITERATION Round 562 / CHANGELOG R565 条 / DECISIONS D-565 / FINAL_REPORT R565 笔）。

## 补正笔的 push **没有落地**（通道故障，不是"没红"）

- `git push origin main` 的第一跑挂住 6 分钟：`ps` 现读子进程是 `/usr/bin/ssh git@github.com git-receive-pack …`（state S，etime 一路涨），`lsof` 读不到 TCP 句柄 ⇒ 不是慢，是**连不上**。杀掉重试，仍然不落地。
- 根因现读（三条互不替代）：`dscacheutil -q host -a name github.com` ⇒ **空**（本机此刻解析不出 github.com）；`dscacheutil … api.github.com` ⇒ `20.205.243.168`（有地址）；`curl --max-time 15 https://github.com` ⇒ `000`，而 `curl … https://api.github.com` ⇒ `200`、`gh api repos/…/git/ref/heads/main` ⇒ `c567879…`（API 通道活着，git 的 SSH 通道靠的那个域名死了）。
- 于是 bounded 重试立刻返回 `ssh: Could not resolve hostname github.com` ⇒ `fatal: Could not read from remote repository`。
- **账**：本地 HEAD 是补正笔（amend 之后现读 `9482f86`；本笔记下面那一笔又改了号 ⇒ 以 `git rev-list --count origin/main..HEAD` 与 `git log` 现读为准）未推 ⇒ `ahead=1`；远端 main 仍是 `c567879`（R565 补记笔，已推的那五笔在 runner 上）。**这一轮不能写"已收口"**：推送失败不是"绿"，是通道坏了（R565 之前 R557 那批"派生格排在台账之后"的教训同样适用于这里 —— 没推出去就没有那一跑，什么都没有）。
- 重试口令（DNS 恢复后）：`git push origin main && git rev-list --count origin/main..HEAD`（期望 0），再 `python3 scripts/ci_read.py latest --workflow CI` 取 `b6c7fce` 的成对号；那一跑要回答的是 R566 读单 (g)「补正笔单独推有没有造出注定红的派生格」。

## 收口前最后一读（补正之后）

- 电池 `/tmp/r565-battery8.log` ⇒ `Ran 710 tests in 88.967s` / `OK (skipped=5)`、退出码 0。
- 派生格再读：清账 `格=162 声明=63 不成立=0/63`、`PRODUCT_STREAK_LEDGER_OK streak=5`、`SOURCES_CELL 一致=是`、`COMMIT_ROUND_IDENTITY 笔=3 … 不一致=0`。
- push 第三次尝试（`ConnectTimeout=12`）⇒ 仍 `Could not resolve hostname github.com`；`dscacheutil -q host -a name github.com` 仍空。**这一轮的最后一格因此是"待推"**：本地领先、远端停在 `c567879`，`9482f86`/`ee16e2b`/交接笔 的成对号**还不存在**（不许预支一个号写进账）。


## 补段 A/C/B（监工发来的同一轮续段）

### A · 绝对根扫干净（现读，不改口径）

- 扫描口令 `grep -rn "/Users/wangziyi" scripts/ .github/workflows/` ⇒ **9 行 / 4 个文件**，逐位判定：
  - `scripts/tests/test_mutate_arm_registry.py:227,232` —— 文档串里**引用历史**（那一族的原委），不是运行时路径 ⇒ 改成不带真名的说法；
  - `scripts/tests/test_mutate_r271_needle.py:21,148,152` —— 正/负对照的样本路径 ⇒ 换成合成 `/Users/someone/DemoRepo`，并把那颗常量改名成 `BAD_MACHINE_PATH_SAMPLE`（名字带 ROOT 会被形状判抓到，而它本就是"坏形状样本"，不该长得像活根）；
  - `scripts/tests/test_frames_path_hygiene.py:36` —— 从前这支扫描器把自己的**模式**抄成真人用户名 ⇒ 判据的靶比它要防的缺陷窄（换一个人/写死别人的目录就抓不到）。改判形状 `(ROOT|REPO_ROOT|repo_root|REPO|*ROOT) = "/(Users|home)/`，正对照补一条 `REPO_ROOT = "/home/anyone/Repo"`；
  - `scripts/tests/fixtures/r46_motion_local.log` —— 数据夹具（R46 本机日志样本），不是脚本、不参与读数打印 ⇒ 具名不列修。
- 现读结论：**会进 CI 的脚本里 0 处运行时绝对根**（`CI_CHANNEL_HYGIENE … 绝对根=0 真人路径=0 通道空格=0`）。

### C · 同族两种坏法收成一条守卫（判据 1 支、电池 9 格、刀 4 把）

- 新守卫 `scripts/ci_channel_hygiene.py` 三格：①名单从 `.github/workflows/*.yml` 现读且**不许为空**；②绝对根（按"这台机器上真存在的账号"判，形状判交给 `test_frames_path_hygiene` 那一支，两支各判一件事）；③通道值里不许有裸空格（判法：`键=%s` 槽位喂的那个名字在本文件被赋过含空格的字面量）。
- **扫描范围是被迫扩出来的**：只按 ci.yml 抽名单会漏掉 R564 那支守卫 —— STEP[9] 跑的是 `unittest discover`，它是被电池 subprocess 调的。⇒ 加 `referenced_by_battery()`（只收真存在的那一颗，避免电池正文里的假样本 `scripts/x.py` 变成幽灵条目）。现读 `ci脚本=14 电池脚本=73 电池引用=24 合计=99`。
- 自撞两格照实记：① 新测试文件第一版把控制样本写成 `/Users/ziyi/…` ⇒ **被自己的 B 格判红**（守卫抓住我），改成 `/Users/ming/…` 又发现按"形状"判会咬正对照 ⇒ 把账号集合做成可注入参数（`accounts=`），默认仍现读那一台；② 探 `/home` 让守卫**挂死 5 分钟** —— macOS 上 `/home` 是 autofs 挂载点，`os.listdir('/home')` 不返回 ⇒ 杀掉、只探 `/Users`，并把这条写进注释。
- 刀四把（needle 现读各命中 1、全 CAUGHT、RESTORE_CLEAN=yes）：**M1470** 把绝对根塞回 `commit_round_identity.py` ⇒ `绝对根=1 真人路径=1` 红；**M1471** 把 `if not roster:` 改成 `if False:` ⇒ "零条也算通过"被钉（红话是"空名单被读成绿 ⇒ 这一格是恒真的"）；**M1472** 把退化说明塞回 `范围=` 的值 ⇒ `通道空格=1` 红；**M1473** 在 `make_info_plist.sh` 写死绝对根 ⇒ 非 `.py` 那一支红（上一版扫描器只会 `ast.parse`，喂 shell 就 parse-error ⇒ CI 真跑的 `.sh` 整个在尺外）。
- 名册：`mutate_needle_precheck.py` TABLES +4 ⇒ 现读 `tables=372 covered=295 arms=757 bad=0`、`ARM_TOTAL files=465 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=459 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`。⚠ 这一批仍是**单臂形状**（`ARM/FILE/OLD/NEW`）⇒ `ARM_TOTAL` 的臂数 +0（与 M1466-M1469 同形，抽臂器只认列表形状）—— 具名"臂数不可抽，会红性由四把真跑证明"，不许写成"1244 里含这四把"。

### B · HINT_CONTRAST 在 runner 的那朵红（排掉倍率、撤掉 NOT_RUN、开 639）

- 一次性探针 `.scratch/motion-audit-2/probe_r565_hint_contrast_1x.py`（判据自己的 0.01 偏差筛 + `max(40, 偏差/20)` 字芯集合）⇒ `/tmp/r565-hint-1x-postchange.log`：
  `light 2x 10.37:1（字芯群 106）` / `light 1x 代理 9.29:1（字芯群 46）`；`dark 2x 10.92:1` / `dark 1x 代理 11.70:1`。
  对照旧值的同一份 1x 代理 `/tmp/r565-1x-preview.log`（tertiary）= light **3.15** / dark 4.34 ⇒ **1x 判得出这两种颜色的差别** ⇒ 「倍率把字芯冲淡」这条解释被排掉（第一版探针少了 0.01 筛 ⇒ 读出 6.19:1 = 本轮撤掉的那把空刀的读数，已修）。
- 于是差的不是倍率，是**渲染 vs 名义**：本机 light `底=255 窗口底色现读=255 字芯/底=0.251`；runner `底=236 字芯/底=0.500`（正好是 `.secondaryLabelColor` 名义 50% 黑压在窗口底色上）。名义口径下 secondary 对白底 ≈4.0:1 ⇒ **仍跌破 4.5** ⇒ 这一条不是仪器能合掉的洞。
- **写过一版具名 `*_NOT_RUN` 并跑过**（条件：底==窗口底色现读 ±2 且 字芯/底≈0.5±0.05；本机两档都不落进去 ⇒ 本地读数逐字不变）—— 然后**撤掉**：它在 runner 上会把一朵真数改成"不判"，那是把红藏起来（R206 那张盲区名单判的是像素不可用，这一格是另一种口径下的合法读数）。撤掉不占刀号。
- 落地的那半：判据只补两格**诊断读数**（`窗口底色现读=`、`字芯/底=`）⇒ 任何一台机器都能把两种口径对上；判据的期望、地板、断言条数一字未动；本机重跑单条判据仍 `light 10.37 / dark 10.92、Executed 1 test, with 0 failures`。**runner 那一朵红原样留着**。
- 新开 **BACKLOG 639**（三种口径的代价摆在账里，本轮一条都没选；要改产品颜色就撞第 12 面 ⇒ 归用户）。

### 补段的收尾读数

- build 0 告警 0 错误（三次：带腿 / 撤腿 / 改注释）；判据卷 222/4 skipped/0 失败（779.1s，撤腿后那一卷）；全量 1406/57/0（827.5s，最终树）；预检 `tables=372 covered=295 arms=757 bad=0`、`ARM_TOTAL files=465 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=459 可判=1183 rot=0 抽不出=6 处置=ok`。
- **帧：基线不更新**。`CHANGED=138` 两次连拍同一批名字；撤掉诊断腿前后 356/356 逐字节相同 ⇒ 我自己被排除；`referenceDate` 是常量 ⇒ 时钟被排除；剩下是渲染状态漂移（640）。
- 电池：台账前 `Ran 719 / OK (skipped=5)`、台账后复跑同数（`/tmp/r565-补-battery1.log`、`-battery2.log`）；占位符逐节回读 = 1（那一处是 U-2447 里反引号内的 `%s` 引用，不是未替换模板）。
- 派生格：streak 仍 5（本段产品 0 文件 ⇒ 不动分界）、sources `一致=是`（不需要 `--write`）、清账 162/63/0、卫生守卫 ok、身份守卫 `笔=5 不一致=0`。
- 换装：**跳过并具名 `SKIP_INSTALL=no-product-change`**（没有产品文件可装；重装会打断用户在用的那一扇窗）。

### 收口（推送落地之后）

- `git push` 成功：`6a3542b..e391ddb`、`e391ddb..5762925`、`5762925..d3bc6ec`、`d3bc6ec..eeac454` ⇒ **`HEAD=origin/main=eeac454`、ahead=0**（服务端引用用 `gh api …/refs/heads/main` 复核，不看本地滞后引用）。
- 新跑四对（全部还没结论 ⇒ 复核未到）：`41689614123↔6a3542b`、`41689665625↔e391ddb`、`41690220222↔5762925`、`41691263117↔eeac454`。
- 电池独占重跑：`Ran 719 / OK (skipped=5)`（93.988s、106.355s 两次一致）⇒ 先前 808s/807s 那两红的成因是**我并发跑了两卷**，把 `test_install_local` 的沙箱装机挤过 180s（那两条单独重跑 1.405s OK）；判据本身没红。
- ⑯ + BACKLOG 641：连推四笔的 commit subject 与内容不符（`6a3542b`/`e391ddb` 逐字同标题；`5762925`、`d3bc6ec` 标题各抄了上一条）⇒ 已推不 amend，forward 点名；现有身份守卫只判 R 前缀 ⇒ 对"标题说的是哪件事"全盲，可判草稿（同批 subject 逐字重复即红，正对照就是本轮这一对）写进 641。

- ⚠ 641 的形状**当场又犯了一次**：`bc5a2af`（本笔记的收口段）的 subject 第三次逐字重复 `6a3542b`/`e391ddb` 那一条 ⇒ 正对照从一对变成三笔同标题。已推 ⇒ 不 amend，只在 641 的账上再加这一个数据点：**重复不是偶发，是"同一轮连写多笔时我 copy message"这个习惯的必然结果**，那条守卫该落。


## R566（第 565 轮 / Round 563）工作笔记 · 签名链

- 身份现读：`security find-identity -v -p codesigning` ⇒ `1 valid identities found` + `5F6C0955D4543282F5B2B12A3A2B9FB9FF5CE0A7 "ClipboardHistory Local Signing"`。
- `make bundle` ⇒ `/tmp/r566-bundle.log`：`SIGNATURE_KIND=local identity=ClipboardHistory Local Signing`、`codesign --verify --deep --strict` 过、MAKE exit 0。
- 换装 ⇒ `/tmp/r566-install.log`：`INSTALL_RESULT=ok 1.4.8→1.4.8 / SHA_MATCH=1 / INSTALL_SIGNATURE=local flags=0x0 / SMOKE_OK=1 / ENTRIES=451=451 / PID=7145`；备份 `/Users/wangziyi/Documents/Codex_Project0_backups/before-before-R566`（`--label` 被脚本再加一层前缀）。
- 跨轮对拍：本轮那份与上一轮备份 `codesign -dvv` 逐字相同（`CodeDirectory v=20400 size=23793 hashes=737+3`、`Signature size=1900`、`Authority=…Local Signing`）⇒ 633 的"身份不变"半边有判据了；人工那一格仍开着。
- 判据：`test_sign_bundle.py` 4 格 → 5 格（新增现读真钥匙串那一格，CI 无身份 ⇒ 具名 skip）。刀 **M1474 / M1475** 全 CAUGHT、RESTORE_CLEAN=yes、needle 各命中 1；名册 `tables=374 / files=467 / bad=0`、`HIDDEN 表=461 rot=0 处置=ok`。
- 验证链：build 0；判据卷 222/4-skipped/0（1010.3s）；帧 `CHANGED=135`（**不 update**；漂移规模本身 138→138→135 在动 ⇒ 640 的措辞要跟着改）；全量 **1406/57/1 红**两跑（`PerfBudgetTests/testImageComparisonCostStaysBounded` 255.1 / 294.2ms 对 250.0），同一判据单独重跑 148.29/148.80/149.64ms ⇒ 负载相关，不放宽、不删格；电池 `Ran 720 / OK (skipped=5)`。
- ⓪ 那七跑（R565 那批）全部 concluded failure，但形状变了：**STEP[9] 不再红**（两处修法被 runner 签收，`SKIP_ROSTER 名单外=无 名册未跳=无 内层Ran=719`），只剩 STEP[15]/[17] = `HINT_CONTRAST` light 3.84:1（639）；最后一跑另加 STEP[19] = `testBandCaptureIsCheaperAndStillSeesTheMotion` 11.394 vs 11.131（**212 的第二次露面、换形状**；同批只这一跑红 ⇒ 判间歇）。

## R565 补全（2026-11-04 · 监工点出「疑似工作到一半的 R565 也要补全」）

一段 = 本笔台账提交（只改五本账 + 本笔记；产品 0 文件、判据 0 条、刀 0 把）。

### 通道：`41691473773 ↔ fa8ae0a`（concluded failure）
- 逐步现读 `gh run view --json jobs`：STEP[15] `Swift tests (executed-count gate)`、STEP[17] `Capture gate`、STEP[19] `Motion coverage floor` = failure，其余 18 项 success。
- 对照跑（归因用）：`41691418800↔bc5a2af`、`41691263117↔eeac454` 都是 STEP[15]+[17] failure、**STEP[19] success**（读 `jobs[].steps[].conclusion`，不是从"不在失败名单"推）。
- `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(16.0/16.0pt) 容差=1px 合并=1px 筛除 宽≤8px 隙≥4px 倍率=1.0x 列x=36px 墨高=5px(5.00pt) 列x=52px 墨高=4px(4.00pt) 列x=68px 墨高=5px(5.00pt)`（4 行）；`BULLET_LEVELS_NOT_RUN` 零行 ⇒ 第四次判到，四次数值逐字同（`6ef9ff1` / `4cfcfc6` / `8eecbc7` / 本跑）。
- `HEAT_LEGEND_COVERAGE light/dark 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`；`HEAT_LEGEND_NOT_RUN` 零行 ⇒ 第四跑到数。
- `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=2 首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=691ms 每格=26.6ms` ⇒ 第七数 = 5（2/5/0/5/6/6/5）。
- `SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=719 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 绿；这一批里第一次真拿到该行（前几跑 STEP[9] 被绝对根打死，观察者按 634 拒给结论）。
- `CAPTURE_GATE_CASES passed=188 skipped=33 failed=1 有名字的红=1 类未知名单=0 NOT_RUN=181`。
- `HINT_CONTRAST light 底=236 字芯=(118,118,118) 对比=3.84:1 字芯像素=40 偏差像素=696 地板=4.5 倍率=1.0x` / `dark 底=50 字芯=(163,163,163) 对比=5.08:1 … 倍率=1.0x` ⇒ 现读三跑逐字同值（`c567879` / `6a3542b` / 本跑）⇒ 不是间歇；`118/236=0.500` = `.secondaryLabelColor` 名义 alpha ⇒ 本机 2x 的 10.37:1 含渲染加深。639 的口径选择仍归用户。
- `MOTION_BAND_SAVING`：`省=2.18×`（6.32/13.78ms，`eeac454`）→ `1.55×`（8.30/12.85，`bc5a2af`）→ `0.98×`（11.39/11.13，本跑红）⇒ 新开 **643**；`线=1.0×` 不动。
- `MOTION_FLOOR_FACTS judged=4/5 executed=79 not-run=notice-banner summary=… 红的用例=testBandCaptureIsCheaperAndStillSeesTheMotion 汇总行报红=1 机器=github-runner` ⇒ 与 STEP[15] 同一朵。
- `FRAME_BASELINE_AGAINST=working COMPARED=356 CHANGED=356 MISSING=0 ADDED=0`（STEP[11]，名册门 ⇒ 步 status success 与 CHANGED 无关）；STEP[13] 对 `v1.4.8` = `CHANGED=62 MISSING=6 ADDED=294`（report-only）⇒ 跨机像素通道不给 640 当证人（写进 640 追记二）。
- 日志：`/tmp/r565-full-fa8ae0a.log`（16610 行，先落盘再切）。

### 三处改账
1. `## R565 状态` 标题计数：判据 1 条 → 判据/守卫 3 支、刀 2 把 → 8 把（M1466–M1473）、新开 638 → 638/639/640/641（已推笔不 amend，工作树现读改齐；641 追记记第六种形状）。
2. `### R565 补记` ② 的「连续第三跑」→ 按跑数口径（⑰ 点名）。
3. `## D-565` 节内圈号撞号（⑤⑥⑦ 各两次）→ 按位置重编 ①…⑩，补段三条 = ⑧⑨⑩，节内留 ⑪ 作对照；逐条引用今天只有 ④，已推 commit 标题里的「D-565 ⑤⑥⑦」按新号读。

### 仍欠
- D-565 ④ 的跨节对账尺（没落，不塞半条守卫）。
- 占位符尺的正对照：今天由 R566 的两起真实漏替换补上（`U-2451+1` 撞号、§1 的 `@@UT@@`），**仍无变异刀** ⇒ 具名「无刀、靠活门」。

### 收口（补全笔）
- 通道：`github.com=200 / api=200` ⇒ 无 `PUSH_BLOCKED`；一次 push `f538d2c..d512932` ⇒ ahead=0。
- 成对号：`41708303631↔d512932`（本批头笔 = 补全台账笔）取号 in_progress ⇒ `CI_NOT_RUN`；R566 那笔 `41704430816↔f538d2c` 同样 in_progress。
- 门：清账 162/63 不成立=0；`product_streak --check` OK streak=1；sources 一致=是；`ci_channel_hygiene` ok（绝对根/真人路径/通道空格全 0）；`commit_round_identity` ok；七本 + 报告占位符回读 0；电池 Ran 720 / OK (skipped=5)。
- R567 的 ⓪ 读单已按到手号改齐（原先那句「现读取号」是抄未推状态 ⇒ 同族第三次，落在 `### R566 补记` ②）。

### 追加：R566 那一跑（41704430816 ↔ f538d2c）收口前到数了
- 逐步现读：STEP[9] failure（连带 STEP[10]-[14] skipped）+ STEP[15] failure + STEP[17] failure；STEP[19] success。
- STEP[9] 的逐字红因：`SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=720 内层skip汇总=4 解析=3 名单外=['test_this_machine_actually_takes_the_identity_branch'] 名册未跳=无`
  ⇒ `AssertionError: Lists differ: [] != ['test_this_machine_actually_takes_the_identity_branch']`；`FAILED (failures=1, skipped=3)`。
  那一格本身走的是自己写好的 `SIGN_LIVE_NOT_RUN=no-identity`（日志 4406 行）⇒ **行为对、缺登记** ⇒ 修法只有把名字登记进 `test_skip_roster.py` 的 github-runner 名册。
- STEP[15]/[17] = 639 那朵，第四次逐字同值（3.84:1 / 5.08:1，`CAPTURE_GATE_CASES passed=188 skipped=33 failed=1 有名字的红=1`）。
- 643 第四个数：`MOTION_BAND_SAVING 带中位=10.80ms 整窗中位=13.60ms 省=1.26× 线=1.0×`；四数 2.18/1.55/0.98/1.26，带臂 6.32→8.30→11.39→10.80（在涨），整窗臂无趋势。
- 台账落点：`### R566 补记` 新增 ④；643 追记；② 那张读单把"已读/未读"改到今天的状态。
- 修的那一笔签不了自己 ⇒ runner 转绿由后一跑作证；本机 `test_skip_roster` 4 格 OK（登记不影响本机承重路径）。

### 第五笔：两处「R566 没落地」一起补
- `test_skip_roster.py` 的 github-runner 名册登记 `test_this_machine_actually_takes_the_identity_branch`（名字取自 runner 那一行 `名单外=[…]`，不是猜的）。本机 4 格 OK；runner 转绿由后一跑作证 ⇒ 账上只写"已登记"。
- STATE 顶部「最后更新」从 `2026-11-03（本地 · R565…）` 抬到 `2026-11-04（本地 · R566 / 第 565 轮 / Round 563）`。抬之前 `test_round_batch_consistency` 的三轮窗口是 565/564/563，**从没扫过 R566 的三本标题**；抬之后现读 `^## 第 565 轮（R566`=1、`^## Round 563 · `=1、`^### …（R566 / `=1 ⇒ 门多看见一格（不是放宽）。
- ⑰ⓘ 那句「两跑复核未到」现在对 `41704430816` 过期 ⇒ forward 指到 `### R566 补记` ④，不回头改已推那一笔的正文。
