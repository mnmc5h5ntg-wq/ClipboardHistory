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

## 待读

- 预检三读（**串行**，与任何 swift 卷并行必撞锁）：`/tmp/r565-precheck.log`（`NEEDLE_PRECHECK` + `ARM_TOTAL`）、`/tmp/r565-hidden.log`（`HIDDEN_ARMS`）。
- ⓪ 两跑到数：`python3 scripts/ci_read.py steps <run>` + `gh run view <run> --json jobs -q '.jobs[].steps[] | "\(.number) \(.name) \(.conclusion)"'`（success 必须逐步读，不许从「不在失败名单」推）。
- ⓪ 各格正文：`python3 scripts/ci_read.py readings <run> BULLET_LEVELS HEAT_LEGEND_COVERAGE HEAT_LEGEND_NOT_RUN MOTION_MARKDOWN_MODE_FADE SKIP_ROSTER` + STEP[15] 的 `SelectionRevealAnimationTests` 形状（0.0 还是 R412 那个 1430）。
- 判据卷 / 帧重捕 / 全量 / 换装 / 电池：见 `chain_r565.sh` 的日志路径（跑之前先确认没有别的 swift 卷在跑）。
