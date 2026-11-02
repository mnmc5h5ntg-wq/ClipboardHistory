# R564 读数台账（第 563 轮 / Round 561）

规矩：每条读数必须带它的日志路径。截断 / 0 字节 / 没有 `Executed N tests, with …` 汇总行 ⇒ **不算读数**。
turn 边界时若那卷的进程还活着、日志还在长 ⇒ 等它自己跑完再读完整日志（既不重跑，也不把半截输出当结论）。

## 已到手

- `CI_QUEUE`（2026-11-03，日志=终端现读）：`41542718166 ↔ 6ef9ff1` 状态 **in_progress 已等=380s 结论=无**；`41531750912↔75b32d6` concluded failure；`41519677393↔f12f50d` concluded success；`41509855001↔26c1939` concluded failure。⇒ ⓪ 四格开场**具名 NOT-RUN（成因=in_progress，日志通道还没内容）**，收口前复述 `queue` 再决定能不能转成读数。
- `CI_STEPS 41542718166`（/tmp 现读，无落盘）：`conclusion=` 空串，`JOB build-and-test ⇒ ` 空 ⇒ 失败步骤列表**尚不存在**（不是"没有失败步骤"）。
- `FRAMES`：`docs/frame_baseline.json` ⇒ `count= 356 frames= 356`。
- `STREAK`：`python3 scripts/product_streak.py` ⇒ `PRODUCT_STREAK ledger_round=562 streak=3 sections=538 … last=631f910 last_round=559`。
- `ABSENCE`：`python3 scripts/ledger_absence_claims.py` ⇒ `格=162 声明=63` / `LEDGER_ABSENCE_RESULT=ok 不成立=0/63`。
- `KNIFE_MAX`：`.scratch/motion-audit-2/*.py` + 七本账现读 ⇒ 已登记最高 **M1462**；串到 `M1463` 的只有"起且未使用"这类叙述（`addendum_r563.py:26`、`U-2430`），**没有 M1463 的刀文件** ⇒ 本轮从 **M1463** 起。
- `GIT`：`HEAD=origin/main=6ef9ff1`、`ahead=0`、`git status --porcelain` 只有 `.local/` 与 `.scratch/motion-audit-2/*` 未跟踪项（历史轮次的脚本，不是本轮产物）。
- `CI_QUEUE 复述`（开工节写完时）：`41542718166 ↔ 6ef9ff1` 仍 `status=in_progress conclusion=`（空）⇒ 四格维持 `CI_NOT_RUN=in_progress`，收口前再复述一次。
- `取靶扫（候选生成器，非判据）`：`PYTHONUTF8=1 python3 .scratch/motion-audit-2/sweep_r564_candidates.py /tmp/r563-frames` ⇒ `/tmp/r564-sweep.log`（341 行）。三条轴的结论都写进 STATE `## R564 ⓪ 开工` ③/④：**轴 A（暗档近白）命中的是暗档文字本身**（top 帧 `content-no-results / main-sidebar-title-hover / content-with-history` 均 ~1% 面积、bbox 落在侧栏文字带）；**轴 B（右边缘墨）命中的是窗口边框**（`settings-*-tall` 每行都有墨 = 2080/2080）；**轴 C（明暗同色中等灰）命中的是图片夹具与占位图**（`detail-1-image` 134580px、`detail-file-fallback-longname` 49176px）。⇒ 三条轴都没直接给出缺陷，但轴 C 把 `detail-file-fallback-longname` 推到眼前，看图后一度误判"文件名被左右裁掉"——**那是我自己 170..1032px 的切框切出来的**，整帧现读 `行1 x83.0..516.5pt`、`行动列 x552..571.5pt` ⇒ 文字与右侧动作条之间还有 35.5pt 空隙，**没有裁切**（R563 那一族"尺读错对象"的又一个样本，已记）。
- `浮层三枚叠层徽标现读`（2× 帧、成对差集口径；命令内联在 STATE ③）：`图钉 高9.00×宽6.00pt 墨=104`、`星 高8.50×宽9.00pt 墨=147`、`内容标记 高8.00×宽8.00pt 墨=96`，light/dark 逐字同形。**星 8.50pt 与 R551 账上的 8.5pt 对上 ⇒ 量法对齐老账**。盒子来自 `QuickPickController.swift:801-812` 现读 = 9 / 10 / 9pt。⚠ 差集是**下界**（徽标叠在类型符号角上，被符号吃掉一块），所以"盒子决定墨大小"未被证实 ⇒ 先做临时改动实验再决定落不落地（出路已写死在 STATE ④）。

## 待读

- 预检三读（串行）：`/tmp/r564-precheck3.log`（`NEEDLE_PRECHECK` + `ARM_TOTAL`）、`/tmp/r564-hidden3.log`（`HIDDEN_ARMS`）—— 后台在跑，完成标记 `/tmp/r564-precheck-done.txt`。
- ⓪(a) `BULLET_LEVELS` 第一次 runner 验：`/tmp/r564-ci.log` 或 `ci_read.py readings 41542718166 BULLET_LEVELS`（等 run 结论）。三条出路预先写死，见 STATE `## R564 ⓪ 开工`。
- ⓪(b) `HEAT_LEGEND_*` 复核：`readings … HEAT_LEGEND_COVERAGE HEAT_LEGEND_NOT_RUN`。
- ⓪(c) `过渡帧数` 第五数：`readings … MOTION_MARKDOWN_MODE_FADE`。
- ⓪(d) STEP[9] `SKIP_ROSTER` 第五跑、STEP[18] 622 新值：`readings … SKIP_ROSTER PROBE_COVERAGE` + `gh run view --json jobs` 的 `steps[].conclusion`。
- 判据卷 / 帧重捕 / 全量 / 换装 / 电池：见 `chain_r564.sh` 的日志路径（跑之前先 `ls -l` 确认没撞锁）。
