#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R474 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


AUDIT_TITLE = u"## 第 472 轮（R473 · 2026-10-29"
AUDIT_SECTION = u"""## 第 473 轮（R474 · 2026-10-29 · U-1797…U-1802）：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288；M1288–M1290 3/3）+ 药丸尺加「连续行分组取最高带」（旧产品帧反向 0 条、合成真值表第 ⑧ 格）（产品 1 文件 + 判据）

- **U-1797：⓪ push 与 CI。** 开工两次探测 `git push` 均报 `Connection closed ... port 22`、`gh run list` EOF ⇒ **`PUSH_BLOCKED=network`**（探测时 HEAD=`04a4022`、origin/main=`c3b8732`、**ahead=2**：55f8810/04a4022）＋ **`CI_READ_BLOCKED=network`**。R473 主笔+追记 head 跑、R472 跑 `40767358317 ↔ 7ce44a1`、R471 两跑**均未读到** ⇒ **NOT-RUN**；`INLINE_CODE_DIAG dark` 的页/带/候选/top 仍未拿到 ⇒ 靶指定的检测修复**具名 NOT-RUN、不盲调**（选择器与 4.5 地板未动）。收口前再试一次网络，结果与最终 ahead/SHA 见补记。
- **U-1798：① 腐烂与预检。** `HIDDEN_ARMS 表=341 可判=1064 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=254 covered=236 arms=647 bad=0`、`ARM_TOTAL files=347 arms=1130`（新增表 `mutate_r474_list_separator` 3 臂；`mutate_r470_overlay_pill_gap` 的 M1281 与 r104 的 M578/M579 因函数签名换了锚点）。
- **U-1799：② 产品：浮层输入区与候选区分界。** 缺陷形状（`quickpick-list`/`quickpick-typed` 亮暗直看）：搜索框和候选列表之间只有 8pt 留白，输入区与内容区同属一块；命令面板的常见语言是一条分区线。修法：`QuickPickController` 加 `NSBox(.separator)`，宽=搜索框宽（左右各 12pt 内缩）、厚 1pt、顶钉在 `scroll.topAnchor`（8pt 间距的下沿，**不占行高**）；**不能**钉 `field.bottomAnchor`：搜索框焦点/悬停描边还要向下多出 4pt，贴底边的线会从焦点环里穿过去（焦点帧直看后改的）。旧/新：8 个浮层夹具 × 亮暗 **16 张帧变化**、0 新增/缺失；基线 **288/0/0/0**；16 张逐张看过：线在同一条轴、无溢出、列表行几何未动。同帧读数（`QUICKPICK_LIST_RULE`）：light/dark × list/typed/empty 均 `线数=1 y=71px 厚=2px 宽=792px 左=24px`（帧宽 840px ⇒ 通栏 94.3%），搜索框底 56px、药丸顶 92px；旧产品帧用同一判据读 **线数=0**（反向验证）。
- **U-1800：③ 判据、反向验证与刀。** 新判据 `testQuickPickSearchAreaIsSeparatedFromTheList`：恰好 1 条、宽 ≥90% 帧宽、厚 ≤4pt、落点在搜索框底边下 **3…12pt**、且在药丸之上（结构关系，不写死 y），6/6 帧。尺对象问题两处自己抓住并改：① 宽度地板 85% 时药丸自身的窄带（752px=89.5%）被当成第二条线 ⇒ 提到 90%（通栏 792px=94.3%）；② `overlayPill` 新增连续行分组 + `minHeight`，合成真值表第 ⑧ 格钉住「1px 通栏线压在药丸上方时仍读药丸顶=100」。刀：`M1288`（分隔线 alphaValue=0）⇒ 线数 0、`M1289`（钉到搜索框中心线）⇒ 落点差 −17pt、`M1290`（左沿缩进 40pt）⇒ 宽不到 90%，**3/3 CAUGHT**、RESTORE_CLEAN；r104 **4/4 CAUGHT**（M577/M578/M579/M580）、M1281 重钉后 **CAUGHT**。空刀登记：`height 1→0` 与 `boxType .custom` 都仍画一条 1pt 线（NSBox 自绘，不受高度约束）⇒ 不登记为「撤掉显影」的证人。
- **U-1801：④ 既有面与 436。** 既有浮层判据（左轴、幻影选中底、选中臂、悬停轮廓）全部复跑通过；`quickpick-typed` 的幻影灰块判据改成「连续 ≥3 行的纯灰**块**」——发丝线是单/双行，不是字后的填充（旧读数 32 行/1115 像素仍是整块，牙没钝）。436：无 R474 新跑（未 push）；最后已知读数沿用 R473 账，**不重猜 `must_judge`**。
- **U-1802：八步与电池。** build **0 告警**（arm64 + x86_64 冷编）；捕获卷 **288 帧**、`CHANGED=16 MISSING=0 ADDED=0`，更新后 `288/0/0/0`；全量 **1285/56/0**（500.7s，轻载；新增 1 条分隔线判据）；换装 `ok / SHA_MATCH=1 / 387=387`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 473，`python3 scripts/product_streak.py --streak-for 473`，last=eb40069）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R473 的补记跑与 R474 自身跑（`PUSH_BLOCKED=network`，跑未创建/未读到）；② `INLINE_CODE_DIAG dark` 的 runner 数据（靶修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE` / `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–543 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 471 · R474（第 473 轮 · 2026-10-29）：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）+ 药丸尺加连续行分组

搜索框和候选列表之间只有 8pt 留白，输入区与内容区同属一块。`QuickPickController` 加 `NSBox(.separator)`：宽=搜索框宽（左右各 12pt 内缩）、厚 1pt、顶钉 `scroll.topAnchor`（8pt 间距下沿，不占行高）；不能钉 `field.bottomAnchor` —— 焦点/悬停描边向下多出 4pt，贴底边的线会从焦点环里穿过去（焦点帧直看后改）。8 个浮层夹具 × 亮暗 **16 张帧变化**、0 新增/缺失，基线 288/0/0/0；16 张逐张看过。同帧读数：`线数=1 y=71px 厚=2px 宽=792px 左=24px`（840px 帧 ⇒ 94.3%），搜索框底 56px、药丸顶 92px；旧产品帧同判据 **0 条**。判据先按 85% 宽度把药丸自身窄带误收为第二条线，提到 90% 后 6/6；`overlayPill` 新增连续行分组 + `minHeight`，真值表第 ⑧ 格钉住分隔线不抢药丸身份。M1288/M1289/M1290 **3/3**（height 1→0 与 boxType .custom 是空刀，登记）；r104 重锚 **4/4**、M1281 重锚 **CAUGHT**。全量 1285/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ 两次探测 remote closed + gh EOF ⇒ `PUSH_BLOCKED=network`（HEAD=04a4022、origin=c3b8732、ahead=2）＋ `CI_READ_BLOCKED`；`INLINE_CODE_DIAG dark` 仍未读到 ⇒ 靶修复具名 NOT-RUN、不盲调。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 16 张变化帧逐张看过：线同轴、无溢出、行几何未动；焦点帧里线在焦点环之外。 |
| 判据有效性 | 14/15 | 6/6 帧；旧产品帧同判据 0 条；M1288–M1290 3/3。扣 1：首版宽度地板 85% 把药丸自身窄带读成第二条线（由自家判据当场红出并改到 90%）。 |
| 假绿防御 | 15/15 | 旧帧反向验证（0 条）在写判据当天做；合成真值表第 ⑧ 格钉住尺的身份；四把既有刀全部重锚后 CAUGHT。 |
| 产品面推进 | 15/15 | 新类别（浮层输入区/候选区分界）；1 个产品文件；不占行高；Store 不动。 |
| 台账一致性 | 15/15 | U-1797…U-1802、D-471、288 帧/1285、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 两次空刀如实登记；runner 数据拿不到就 NOT-RUN，不盲调选择器；PUSH/CI 阻塞分开写。 |
| 可复核性 | 15/15 | 16 张帧、792/840px、71px vs 56/92px、M1288–M1290、precheck 254/236/647、rot 341/1064、基线 288 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_471 = u"""## D-471 浮层分区线放在 8pt 间距的下沿；药丸尺按连续行分组取最高带（R474）

- 背景：搜索框与候选列表之间只有 8pt 留白，输入区与内容区同属一块。焦点/悬停描边比搜索框向下多出 4pt，若把 1pt 线钉在 `field.bottomAnchor`，线会从焦点环**里面**穿过去（R474 焦点帧直看）。
- 决定：加 `NSBox(.separator)`，宽=搜索框宽（左右 12pt 内缩）、厚 1pt、顶钉 `scroll.topAnchor`（8pt 间距下沿，不占行高）；判据要求恰好 1 条、宽 ≥90% 帧宽、厚 ≤4pt、落点在搜索框底边下 3…12pt 且在药丸之上。`overlayPill` 同时改成连续行分组 + `minHeight`，取最高的通栏带。
- 理由：结构关系（边界在输入区之下、候选行之上）比写死 y 稳；`overlayPill` 必须区分「1pt 发丝线」与「30–60pt 的选中填充」，否则分隔线会抢走药丸的身份、中段取样落进空白。
- 兼容性/迁移：仅 8 个浮层夹具 × 亮暗 16 帧变化；基线 288 同笔更新；无 Store/存档变化。
- 边界：NSBox 的 `separator`/`custom` 自绘 1pt 线，改高度或 boxType 都撤不掉像素（空刀已登记）；runner 的 1x 与空结果态尚未签收。
- 回滚：删分隔线与判据；`overlayPill` 的 `minHeight`/分组可保留（默认 1 等于旧行为）。
"""

CHANGELOG_SECTION = u"""### 浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）（R474 / 第 473 轮 / Round 471 / U-1797…U-1802 · 产品 1 文件 + 判据）

"""

BACKLOG_SECTION = u"""**541. R473 补记与 R474 的跑仍未读（R474 观察）**
    现象：`PUSH_BLOCKED=network`（HEAD=04a4022、origin/main=c3b8732、ahead=2）⇒ R473 的两笔补记没有跑、R474 的提交也还没建；`gh` EOF。
    修法：网络恢复后先验 remote 再快进 push；随后读 R473/R474 全部失败步骤，`INLINE_CODE_DIAG dark` 拿到数据再改检测。

**542. `QUICKPICK_LIST_RULE` 的 runner 1x 与空结果态未签收**（R474 观察）
    现象：本机 2x 六帧均 `线数=1 y=71px 厚=2px 宽=792px`；1x 上 1pt 线可能只占 1px，空结果态的布局分支也不同。
    修法：下一跑读 `QUICKPICK_LIST_RULE` 的两档与 quickpick-empty；读不到就具名 NOT-RUN，不改 90%/4pt 地板。

**543. NSBox(separator) 的厚度/boxType 改不出「有/无」——两把空刀**（R474 观察）
    现象：`height 1→0` 与 `boxType .custom` 都仍画一条 1pt 线，只有 `alphaValue=0` 能撤掉像素。
    修法：以后要撤这条线用 alpha/隐藏或换控件；「改高度变粗」不作为视觉证人。
"""

STATE_SECTION = u"""## R474 状态（2026-10-29 · 本地 · 第 473 轮 / Round 471）：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）+ 药丸尺加连续行分组；全量 1285/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R474 / 第 473 轮 / Round 471）：搜索框和候选列表之间只有 8pt 留白，输入区与内容区同属一块。修法：`QuickPickController` 加 `NSBox(.separator)`，宽=搜索框宽（左右 12pt 内缩）、厚 1pt、顶钉 `scroll.topAnchor`（8pt 间距下沿，**不占行高**）；不能钉 `field.bottomAnchor`（焦点/悬停描边向下多出 4pt，贴底边的线会从焦点环里穿过去，焦点帧直看后改的）。旧/新：8 个浮层夹具 × 亮暗 **16 张帧变化**、0 新增/缺失；基线 **288/0/0/0**；16 张逐张看过：线在同一条轴、无溢出、列表行几何未动。同帧读数（`QUICKPICK_LIST_RULE`）：light/dark × list/typed/empty 均 `线数=1 y=71px 厚=2px 宽=792px 左=24px`（帧宽 840px ⇒ 通栏 94.3%），搜索框底 56px、药丸顶 92px；旧产品帧同判据 **0 条**（反向验证）。**靶修未做**：`INLINE_CODE_DIAG dark` 数据仍未拿到（`PUSH_BLOCKED=network`，R473/R472/R471 跑均 NOT-RUN）⇒ 具名 NOT-RUN、不盲调选择器、4.5 地板未动。预检 **254/236/647 bad=0**、ARM **347/1130**、HIDDEN **341/1064 rot=0**。⓪：开工两探 remote closed + `gh` EOF ⇒ **`PUSH_BLOCKED=network`**（探测时 HEAD=`04a4022`、origin/main=`c3b8732`、**ahead=2**：55f8810/04a4022）＋ **`CI_READ_BLOCKED=network`**；R473 主笔+追记 head 跑、R472 跑 `40767358317 ↔ 7ce44a1`、R471 两跑均未读到 ⇒ NOT-RUN；436 无 R474 新跑。全量 **1285/56/0**（500.7s，轻载）；捕获卷 **288 帧**；基线 **288/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 473，`python3 scripts/product_streak.py --streak-for 473`，last=eb40069）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push/gh 均被网络挡住（两探）⇒ PUSH_BLOCKED=network（ahead=2、HEAD 04a4022、origin c3b8732）＋ CI_READ_BLOCKED；R473/R472/R471 跑与 dark DIAG 全部 NOT-RUN，未盲调。
② 产品：浮层搜索框与候选区补 1pt 通栏分隔线（16 张浮层帧变化、基线 288）；焦点帧发现线穿焦点环，改钉 `scroll.topAnchor`。
③ 判据：`QUICKPICK_LIST_RULE` 6/6、旧产品帧 0 条；`overlayPill` 连续行分组 + `minHeight`，真值表第 ⑧ 格；M1288–M1290 3/3；r104 重锚 4/4、M1281 重锚 CAUGHT；precheck 254/236/647；rot 341/1064。
④ 436：无新跑；不重猜 must_judge。
⑤ 捕获 288 帧；基线 288/0/0/0；build 0 告警；换装 ok/387=387；全量 1285/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R473 补记与 R474 自身跑（未 push）；② `INLINE_CODE_DIAG dark` 的 runner 数据（靶修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ Motion 回执/滚动会话/code-tab 字典 flake（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–543 的其余未结项仍开。

下一轮（R475）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R474 主笔+追记 head 跑、R473 补记跑、R472 跑 `40767358317 ↔ 7ce44a1`、R471 两跑的全部失败步骤；重点 `QUICKPICK_LIST_RULE`（1x/空结果）、`INLINE_CODE_DIAG dark`（页/带/候选/top、m=rowMax；拿到数据再改检测、不盲调选择器、4.5 地板不动）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`（2x 等距连跑 21、1x 词簇 ≥5）、`TRUNCATION_NOTE` 11/14、`QUICKPICK_SOURCE_ICON` 5/5/84、`CROSS_YEAR_TIME`/`MAIN_ROWS_CROSS_YEAR`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R474_REPORT_BULLET = u"""- **R474（浮层分区边界位）**：搜索框和候选列表之间只有 8pt 留白，输入区与内容区同属一块。`QuickPickController` 加 `NSBox(.separator)`：宽=搜索框宽（左右 12pt 内缩）、厚 1pt、顶钉 `scroll.topAnchor`（8pt 间距下沿，不占行高）；焦点帧发现钉 `field.bottomAnchor` 会穿进焦点环，改到间距下沿。**16 张浮层帧变化**、0 新增/缺失，基线 **288/0/0/0**；16 张逐张看过。`QUICKPICK_LIST_RULE`：light/dark × list/typed/empty 均 `线数=1 y=71px 厚=2px 宽=792px 左=24px`（840px ⇒ 94.3%），搜索框底 56px、药丸顶 92px；旧产品帧同判据 **0 条**。`overlayPill` 加连续行分组 + `minHeight`，真值表第 ⑧ 格钉身份；M1288–M1290 **3/3**（height/boxType 两把空刀已登记）；r104 重锚 4/4、M1281 重锚 CAUGHT。⓪ 两次探测 remote closed + gh EOF ⇒ `PUSH_BLOCKED=network`（HEAD=04a4022、origin=c3b8732、ahead=2）＋ `CI_READ_BLOCKED`；R473/R472/R471 跑与 `INLINE_CODE_DIAG dark` 均 NOT-RUN，靶修复未做、不盲调。全量 **1285/56/0**（500.7s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 473 轮（R474" in audit: raise SystemExit("REFUSED AUDIT 已有 R474")
if u"## Round 471 · R474" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 471")
if u"## D-471" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-471")
if u"浮层搜索框与候选区补 1pt 通栏分隔线" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**541." in backlog: raise SystemExit("REFUSED BACKLOG 已有 541")
if state.count(u"## R473 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R473 状态"))
U_CELL_OLD = u"U-31 … U-1796（R473 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R473 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_471 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R473 状态", STATE_SECTION + u"## R473 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1802（R474 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R473 节 ②", u"AGENT_STATE.md` 的 R474 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R474_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R474_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
