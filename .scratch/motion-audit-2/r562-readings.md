# R562 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r562.py`）

第 561 轮 / Round 559 · 2026-11-03。规矩：**已到手**只写真读到的；被打断/超时/没跑的进**待读**；截断的日志不算读数。

## 已到手

### ⓪ CI（开场）
- `41519677393 ↔ f12f50d`（R561 那一批头笔 = 补记笔）状态 **queued、已等 232s**；`steps` 打 `conclusion=` 空串、`JOB build-and-test ⇒` 空 ⇒ **没有结论**，不是「没红」。
  ⇒ 三格具名 NOT-RUN：(a) `SolidRuler` 在 runner 真 1x 帧上判没判到；(b) `过渡帧数` 第四数；(c) STEP[9] 第四跑 + STEP[18] 622。
  收口前复述一次 `queue`，到数就改写成读数。
- `41509855001 ↔ 26c1939` = concluded failure（只红 STEP[19]）⇒ 已读，读数在 `### R561 补记` ②，不重读。
- `CI_UNREAD`：R561 中间三笔 `5e08357`/`a8adab4`/`324c513`；R560 五笔；R558 两笔。
- 永不重开：`41452722560↔58851c2`、`41455782587↔598b253`。

### ② 基线（全部本轮现读，命令写在 STATE ② 格）
- 帧基线 `count=354`（`docs/frame_baseline.json`，`frames` 字典同长）。
- `NEEDLE_PRECHECK tables=358 covered=295 arms=757 bad=0`；`ARM_TOTAL files=451 arms=1244 dupes=0 repeats=0`；`HIDDEN_ARMS 表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`。
  ⚠ 抄错一次：`scripts/hidden_arms.py --arm-total` **没有这个参数** ⇒ usage 报错 + 退出码 2；`ARM_TOTAL` 那行是 `mutate_needle_precheck.py` 打的。报错不是读数。
- 清账 `LEDGER_ABSENCE_RESULT=ok 不成立=0/63`；`PRODUCT_STREAK ledger_round=560 streak=1 last=631f910 last_round=559 newest=631f910 newest_round=559`（开工现读；收口那格落盘后重读）。
- 刀号最高 **M1459** ⇒ 本轮 **M1460** 起。
- 判据卷 / 全量卷 / 换装：本轮**还没跑** ⇒ 具名 `NOT_RUN=this-round-not-yet-run`，不许拿上一轮的收口读数冒充。

### ③ git / 网络前置
`git log --oneline -1` = `f12f50d`；已跟踪改动 0；ahead=0；`api.github.com=200 / www.apple.com=200`。

### ④ 本轮前置自检（第一次就用上了）
`state_r562_open.py` 落盘后回读：`%(?=[a-zA-Z])` 在「`## R562 ⓪ 开工` → `## R561 状态`」这一段 = **0**（R561 那笔落了一个进去，第四回同坑）。

## 待读（截断的链要重跑）

- ② 的第二格：636 退场第一步 —— 先看清夹具该放在哪个文件、哪个 `markdownSample`，再补 depth1/depth2 正文，重捕帧看那三级列表长什么样（**先看图**）。
- 新判据「三级同尺寸」的**先红后绿**（旧值→新值都要现读打印）；若红在禁碰面 ⇒ 不动产品，只开单 + 摆代价。
- 刀 M1460 起：登记前自问变化量是否出容差。
- build 0 告警 → filter → 刀 → 名册登记 → 判据卷 → 重捕帧 + 同一笔 `update` → 全量 → 预检三读**串行** → 换装（备份 `before-R562`，label 撞名就 R562b）→ 台账 → 各笔本地提交 → `report_sources_cell --write` → 电池 → **一次性 push** → ahead=0。
- ⓪ 那跑 `41519677393↔f12f50d` 收口前复述：三格读数（(a) 最要紧 —— 若仍走出口，R563 的头格就是修派生式）。
