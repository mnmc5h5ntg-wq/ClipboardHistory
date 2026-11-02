# R563 自存工作笔记（不是第七本账；收口时抄进 `ledgers_r563.py`）

第 562 轮 / Round 560 · 2026-11-03。规矩：**已到手**只写真读到的；被打断/超时/没跑的进**待读**；截断的 / 0 字节 / 没有 `Ran N tests` 汇总行的输出**不算读数**。

## 已到手

### ⓪ CI（开场）
- `41531750912 ↔ 75b32d6`（R562 那一批头笔 = 补记笔，含 R562 全部代码）状态 **queued、已等 229s**；`steps` 打 `conclusion=` 空串、`JOB build-and-test ⇒` 空 ⇒ **没有结论**，不是「没红」。
  ⇒ 四格具名 NOT-RUN：(a) `HEAT_LEGEND_*` 这一跑走哪条（**只是复核**，首次签收已在 `41519677393↔f12f50d`）；(b) `BULLET_LEVELS` 在 runner 1x 走哪条；(c) `过渡帧数=` 第五数；(d) STEP[9] 第五跑 + STEP[18] 622。
  收口前复述一次 `queue`，到数就把这四格改写成读数。
- 已读、不必重读：`41519677393↔f12f50d` = concluded **success**（R561 的几何派生尺被 runner 签收：`地板 格4/图例4 倍率=1.0x`、`HEAT_LEGEND_NOT_RUN` 零行；`过渡帧数` 第四数=5 ⇒ 四跑 2/5/0/5；STEP[9] 四跑绿；`BULLET_LEVELS` 零行＝判据未推）。
- `CI_UNREAD`：R562 中间四笔 `327bc53`/`ff2cb9f`/`5d71660`/`c8c950f`；R561 三笔；R560 五笔；R558 两笔。
- 永不重开：`41452722560↔58851c2`、`41455782587↔598b253`。

### ② 基线（全部本轮现读）
- 帧基线 `docs/frame_baseline.json` ⇒ `count=356`、`frames` 字典同长 356。
- `NEEDLE_PRECHECK tables=361 covered=295 arms=757 bad=0`；`ARM_TOTAL files=454 arms=1244 dupes=0 repeats=0`；`HIDDEN_ARMS 表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（日志 `/tmp/r563-precheck1.log`、`/tmp/r563-hidden1.log`）。
- 清账 `LEDGER_ABSENCE_CLAIMS 格=162 声明=63` / `LEDGER_ABSENCE_RESULT=ok 不成立=0/63`。
- streak `PRODUCT_STREAK ledger_round=561 streak=2 sections=537 last=631f910 last_round=559 newest=631f910 newest_round=559` ⇒ **产品面连零改动 2 轮 ⇒ 本轮必须落 `Sources/`**。
- 刀号现读最高位（扫 `.scratch/motion-audit-2/mutate_*.py` 里所有 `M\d{4}`）⇒ **MAX = M1462**（在 `mutate_r562_widen_merge_window.py`）⇒ 本轮从 **M1463** 起。
- git：`git log --oneline -1` = `75b32d6`；已跟踪改动 0；ahead=0；`api.github.com=200 / www.apple.com=200`。

### ③ 本轮要先消掉的一处账内矛盾（改账，不是改门）
`### R562 补记` ④ 写「**636 本轮结案**」，而同一轮的轮次节 ②(b)/ 与台账笔 `5d71660` 写「636 半落地、单子继续开（三级项目符的尺寸没有被判过）」⇒ 两处互斥。
按证据取**继续开单**（墨 bbox 只印不判；定尺寸契约要撞 R549/R560 两个禁碰面 ⇒ 归用户）。成因：补记笔写 ④ 那一格时沿用了 R561 的口径措辞，**没有跟同一轮里已经落盘的另外两处交叉核对**。

## 待读（截断的链要重跑）

- ② 的产品位：还没挑 —— 要先读清账表 + 盲区名册 + 逐张看图，再定「旧值→新值 + 帧/结构量 + ≥2 把刀」的那一格。
- build 0 告警 → filter 先红后绿 → 刀 → 名册登记 → 判据卷 → 重捕帧 + 同一笔 `update` → 全量 → 预检三读**串行** → 换装（备份 `before-R563`；label 撞名就 R563b）→ 台账 → 各笔本地提交 → `report_sources_cell --write` → 电池 → **一次性 push** → ahead=0。
- ⓪ 那跑 `41531750912↔75b32d6` 收口前复述：四格读数。
