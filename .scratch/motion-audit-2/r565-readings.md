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
