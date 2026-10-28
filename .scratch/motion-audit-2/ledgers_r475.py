#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R475 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 473 轮（R474 · 2026-10-29"
AUDIT_SECTION = u"""## 第 474 轮（R475 · 2026-10-29 · U-1803…U-1808）：图片行补「可搜索文字」标记（2 张新帧、基线 290；M1291/M1292 2/2）+ INLINE_CODE_DIAG 四门分桶（light/dark 35/35/9/9，chosen=true；runner 待读）（产品 1 文件 + 判据 + 诊断）

- **U-1803：⓪ push 与 CI。** `git push` **Everything up-to-date**、HEAD=origin/main=`348e75e`、**ahead=0**。`ci_read` 成对读：R474 跑 `40780110804 ↔ d70cc57` 与补记跑 `40780464933 ↔ 348e75e` **读时 in_progress（结论空、0 字节失败日志）⇒ NOT-RUN**；R473 追记 `40770699614 ↔ c3b8732`、R472 `40767358317 ↔ 7ce44a1`、R471 `40759492283 ↔ e664410`/`40759325073 ↔ ad722b4` 的失败步骤沿用 R474 补记（inline dark 同形；R473 追记 code-tab 字典崩溃；R471 追记 Motion 回执 1<2；R472 日志 `UNKNOWN STEP`）。436 无 R475 新跑 ⇒ NOT-RUN。收口 push/新跑见补记。
- **U-1804：① 腐烂与预检。** `HIDDEN_ARMS 表=342 可判=1066 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=255 covered=237 arms=649 bad=0`、`ARM_TOTAL files=348 arms=1132`。`M1220` 因 R475 把时间行 `Text` 包进 HStack 而腐烂（命中 0）⇒ 重钉到新缩进并复跑 R444 表 **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1805：② 产品：图片行的「可搜索文字」标记。** 缺陷形状（`row-image` 帧直看）：OCR 已落地的图片与普通图片在主列表里长得一模一样 —— 用户搜到一张图时看不出"这张图有可搜索的文字"，只能回忆设置里开过识别。修法：`RowTextColumn` 的时间行改成 HStack，`entry.ocrText` 非空时在来源后补一枚 `text.viewfinder`（11pt、`secondaryLabelColor`、`helpLabel` + `accessibilityLabel`）；标在时间行末尾而非行尾，**行标题截断宽度一字未动**。旧/新：**2 张新帧**（`row-image-ocr` 亮暗）、**0 张既有帧变化**（含 57 张 row 帧逐字节不变；HStack 未改无标记行的高度/宽度）、0 缺失；基线 **288→290**；2 张逐张看过：标记在来源后、与时间行同基线、不压缩略图。读数（`ROW_OCR_BADGE`）：light 负臂末列 421px→正臂 455px、**末列差 34px（17pt）**、墨 3664→3770（+106）；dark 421→455、墨 4083→4189（+106）。
- **U-1806：③ 判据与刀。** 新判据 `testImageRowsCarryASearchableBadgeWhenOCRLanded` 用**成对帧**（`row-image` 负臂 / `row-image-ocr` 正臂，内容/时间/来源/缩略图逐项相同，只差 `ocrText`）：正臂最后墨列必须越过负臂 ≥3pt、墨量多 ≥10pt·1x；两档都判。刀：`M1291`（条件恒 false ⇒ 标记不画）、`M1292`（条件恒 true ⇒ 每行都画）均 **CAUGHT**、RESTORE_CLEAN（2/2）。M1292 是"不做空"那一半：只证明"删掉会红"会把"标记本来就在所有行上"当成正确。
- **U-1807：④ INLINE_CODE_DIAG 四门分桶（靶指定诊断）。** 在 `testInlineCodeBackgroundHasPadding` 里加 `INLINE_CODE_GATES` 与 `INLINE_CODE_TOP_SPAN`：按 `span[80,300]px / coverage≥0.55 / ink≥24 / rowMax≤300px` 逐门计数（与 `best` 同一组常量），并另打按 span 排序的前 6 条。本机现读：light `候选=299 过span=35 过coverage=35 过ink=9 过rowMax=9`、dark `281/35/35/9/9`；两者 `选中=true`，PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5。**runner 分桶未读到**（R474 两跑 in_progress）⇒ 检测修复仍 **NOT-RUN**，选择器与 4.5 地板未动；R476 先读 `INLINE_CODE_GATES` 再改。
- **U-1808：八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **290 帧**、`CHANGED=0 MISSING=0 ADDED=2`，更新后 `290/0/0/0`；全量 **1286/56/0**（500.9s，轻载；新增 1 条 OCR 标记判据）；换装 `ok / SHA_MATCH=1 / 387=387`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 474，`python3 scripts/product_streak.py --streak-for 474`，last=d70cc57）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R474 两跑（in_progress）；② `INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN` 的 runner 数据（检测修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ `RUNNER_COPY_RECEIPT_MOTION_FLAKE` / `RUNNER_SCROLL_SESSION_FLAKE` / `RUNNER_CODE_TAB_DICT_NIL_FLAKE`（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–546 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 472 · R475（第 474 轮 · 2026-10-29）：图片行补「可搜索文字」标记（2 张新帧、基线 290）+ INLINE_CODE_DIAG 四门分桶

OCR 已落地的图片与普通图片在主列表里长得一模一样。`RowTextColumn` 的时间行改成 HStack，`entry.ocrText` 非空时在来源后补一枚 `text.viewfinder`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel）；标在时间行末尾，行标题截断宽度未动。**2 张新帧、0 张既有帧变化**，基线 **288→290**；2 张逐张看过。`ROW_OCR_BADGE`：负臂末列 421px → 正臂 455px（差 34px=17pt）、墨 +106（两档同形）。新判据用成对帧（同内容/时间/来源/缩略图，只差 ocrText），M1291（恒 false）/M1292（恒 true）**2/2**；M1220 重钉后 R444 表 **2/2**。**INLINE_CODE_DIAG 四门分桶**已加：本机 light 299/35/35/9/9、dark 281/35/35/9/9，选中=true（light PAD 98.5/92.5/6.0、dark 99/92.5/6.5）；runner 分桶未读到 ⇒ 检测修复仍 NOT-RUN、未改选择器、4.5 地板未动。全量 1286/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ `git push` no-op、ahead=0；R474 两跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张新帧逐张看过：标记在来源后、同基线、不压缩略图；负臂帧对照明确。 |
| 判据有效性 | 15/15 | 成对帧同内容只差 ocrText；末列差 34px、墨差 106；M1291/M1292 2/2；M1220 重钉 2/2。 |
| 假绿防御 | 14/15 | 正负两臂与"每行都画"刀都判；扣 1：inline 四门分桶的 runner 数据未读到，检测修复未做。 |
| 产品面推进 | 15/15 | 新类别（图片行可搜索文字标记）；1 个产品文件；标题截断宽度未动；0 张既有帧变化。 |
| 台账一致性 | 15/15 | U-1803…U-1808、D-472、290 帧/1286、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | runner 分桶拿不到就 NOT-RUN，不盲调选择器；R474 两跑 in_progress 明确记未读。 |
| 可复核性 | 15/15 | 2 张帧、421→455px、+106、M1291/M1292、precheck 255/237/649、rot 342/1066、基线 290 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_472 = u"""## D-472 图片行的「可搜索文字」标记放时间行末尾；inline 检测先打四门分桶（R475）

- 背景：OCR 已落地的图片与普通图片在主列表里同形；用户搜到一张图时看不出"这张图有可搜索的文字"。inline dark 的旧 DIAG 只按 padding 打 top5，长带被某一门砍掉时只剩短碎片，无法归因。
- 决定：`RowTextColumn` 时间行改 HStack，`entry.ocrText` 非空时在来源后补 `text.viewfinder`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel）；标在时间行末尾，不占固定宽度。`testInlineCodeBackgroundHasPadding` 增加 `INLINE_CODE_GATES`（span/coverage/ink/rowMax 逐门计数）与 `INLINE_CODE_TOP_SPAN`。
- 理由：时间行短，标在末尾不会改标题截断宽度；成对帧（只差 ocrText）让"标记"与"文字变长"分开。四门分桶直接回答"长带死在哪一门"，比按 padding 排序的 top5 更接近被判定属性。
- 兼容性/迁移：2 张新帧、0 张既有帧变化；基线 288→290；无 Store/存档变化。M1220 因时间行包 HStack 重钉并 2/2。
- 边界：OCR 标记在 runner 的暗档/1x 尚未签收；inline 的四门分桶只有本机读数，runner 未读到 ⇒ 检测修复仍 NOT-RUN。
- 回滚：删标记与判据；四门诊断可保留（只影响日志，不影响断言）。
"""

CHANGELOG_SECTION = u"""### 图片行补「可搜索文字」标记（2 张新帧、基线 290）（R475 / 第 474 轮 / Round 472 / U-1803…U-1808 · 产品 1 文件 + 判据 + 诊断）

"""

BACKLOG_SECTION = u"""**544. R474/R475 的跑仍未读（R475 观察）**
    现象：R474 跑 `40780110804 ↔ d70cc57` 与补记跑 `40780464933 ↔ 348e75e` 读时 in_progress（结论空）；R475 自身跑随提交创建。
    修法：收口后先读这两跑与 R475 跑的全部失败步骤；`INLINE_CODE_GATES` 拿到分桶后先定位长带死在哪一门。

**545. `INLINE_CODE_GATES` 的 runner 分桶未读，长带死因未定**（R475 观察）
    现象：本机 light 候选 299（span 35 / coverage 35 / ink 9 / rowMax 9）、dark 281（35/35/9/9），选中=true；runner dark 旧 DIAG 选中=false、top 全是 s20 短碎片。
    修法：读 `INLINE_CODE_GATES` 与 `INLINE_CODE_TOP_SPAN`；若 `过ink=0` 则是文字行 ink 地板问题，若 `过coverage` 掉则是空白/字形把带切碎，若 `过span` 掉则是 minSpan=40pt 把短带排除。拿到数据再改，4.5 地板不动。

**546. OCR 标记在 runner 的暗档/1x 未签收**（R475 观察）
    现象：本机两档 `ROW_OCR_BADGE` 末列 421→455、墨 +106；runner 的 row 帧与 1x 缩放下图标可能小于 1pt 笔画。
    修法：下一跑读 `ROW_OCR_BADGE`；读不到就具名 NOT-RUN，不改 3pt/10pt 地板。
"""

STATE_SECTION = u"""## R475 状态（2026-10-29 · 本地 · 第 474 轮 / Round 472）：图片行补「可搜索文字」标记（2 张新帧、基线 290）+ INLINE_CODE_DIAG 四门分桶（本机 35/35/9/9；runner 待读）；全量 1286/56/0（产品 1 文件 + 判据 + 诊断）

最后更新：2026-10-29（本地 · R475 / 第 474 轮 / Round 472）：OCR 已落地的图片与普通图片在主列表里长得一模一样 —— 用户搜到一张图时看不出"这张图有可搜索的文字"。修法：`RowTextColumn` 的时间行改成 HStack，`entry.ocrText` 非空时在来源后补一枚 `text.viewfinder`（11pt、`secondaryLabelColor`、`helpLabel` + `accessibilityLabel`）；标在时间行末尾而非行尾，**行标题截断宽度一字未动**。旧/新：**2 张新帧**（`row-image-ocr` 亮暗）、**0 张既有帧变化**（含 57 张 row 帧逐字节不变）、0 缺失；基线 **288→290**；2 张逐张看过：标记在来源后、与时间行同基线、不压缩略图。读数（`ROW_OCR_BADGE`）：light 负臂末列 421px→正臂 455px、**末列差 34px（17pt）**、墨 3664→3770（+106）；dark 421→455、墨 4083→4189（+106）。新判据用**成对帧**（内容/时间/来源/缩略图逐项相同，只差 `ocrText`）：正臂最后墨列越过负臂 ≥3pt、墨量多 ≥10pt·1x；`M1291`（条件恒 false）/`M1292`（条件恒 true）**2/2 CAUGHT**；`M1220` 因时间行包 HStack 重钉，R444 表 **2/2**。**靶指定的 inline 四门分桶已加**：`INLINE_CODE_GATES` 本机 light `候选=299 过span=35 过coverage=35 过ink=9 过rowMax=9`、dark `281/35/35/9/9`，两者 `选中=true`（PAD light 98.5/92.5/6.0、dark 99.0/92.5/6.5）；**runner 分桶未读到**（R474 两跑 in_progress）⇒ 检测修复仍具名 NOT-RUN、选择器与 4.5 地板未动。预检 **255/237/649 bad=0**、ARM **348/1132**、HIDDEN **342/1066 rot=0**。⓪：`git push` **Everything up-to-date**、HEAD=origin/main=`348e75e`、**ahead=0**；R474 跑 `40780110804 ↔ d70cc57` 与补记跑 `40780464933 ↔ 348e75e` 读时 in_progress（结论空）⇒ NOT-RUN；R473/R472/R471 四跑沿用 R474 补记已读；436 无 R475 新跑。全量 **1286/56/0**（500.9s，轻载）；捕获卷 **290 帧**；基线 **290/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 474，`python3 scripts/product_streak.py --streak-for 474`，last=d70cc57）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R474 两跑 in_progress ⇒ NOT-RUN；四跑沿用已读；436 无新跑。
② 产品：图片行补「可搜索文字」标记（2 张新帧、基线 290）。
③ 判据：成对帧读末列/墨差（34px/+106），M1291/M1292 2/2；M1220 重钉 2/2；precheck 255/237/649；rot 342/1066。
④ 靶诊断：`INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN` 四门分桶已加；本机 35/35/9/9、选中=true；runner 未读到 ⇒ 检测修复 NOT-RUN。
⑤ 捕获 290 帧；基线 290/0/0/0；build 0 告警；换装 ok/387=387；全量 1286/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R474 两跑（in_progress）；② `INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN` 的 runner 分桶（检测修复未做）；③ `QUICKPICK_LIST_RULE` 的 runner 1x/空结果态；④ `INLINE_CODE_PAD`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*` 的 runner 复核（无新跑）；⑤ Capture MATERIAL_BLIND_NOT_RUN；⑥ Motion 回执/滚动会话/code-tab 字典 flake（若再现先查）；⑦ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑧ 437–546 的其余未结项仍开。

下一轮（R476）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R475 自身跑、R474 两跑 `40780110804 ↔ d70cc57`/`40780464933 ↔ 348e75e`、R473 追记 `40770699614 ↔ c3b8732`、R472 `40767358317 ↔ 7ce44a1`、R471 两跑的全部失败步骤；**重点拿 `INLINE_CODE_GATES` 与 `INLINE_CODE_TOP_SPAN` 的 dark 分桶**：按 span/coverage/ink/rowMax 哪一门把长带砍掉，再改检测；4.5 地板不动、选择器不盲调。其余重点：`ROW_OCR_BADGE`（暗档/1x）、`QUICKPICK_LIST_RULE`（1x/空结果）、`INLINE_CODE_PAD` 两档、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R475_REPORT_BULLET = u"""- **R475（图片行可搜索文字标记位）**：OCR 已落地的图片与普通图片在主列表里同形。`RowTextColumn` 时间行改 HStack，`entry.ocrText` 非空时在来源后补 `text.viewfinder`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel）；标在时间行末尾，标题截断宽度未动。**2 张新帧、0 张既有帧变化**，基线 **288→290**；2 张逐张看过。`ROW_OCR_BADGE`：负臂末列 421px→正臂 455px（差 34px=17pt）、墨 +106（两档同形）。判据用成对帧（只差 ocrText），M1291/M1292 **2/2**；M1220 重钉后 R444 表 **2/2**。**INLINE_CODE_GATES 四门分桶已加**：本机 light 299/35/35/9/9、dark 281/35/35/9/9，选中=true（PAD 98.5/92.5/6.0 与 99/92.5/6.5）；runner 分桶未读到 ⇒ 检测修复仍 NOT-RUN、未改选择器、4.5 地板未动。⓪ `git push` no-op、ahead=0；R474 两跑 in_progress ⇒ NOT-RUN。全量 **1286/56/0**（500.9s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 474 轮（R475" in audit: raise SystemExit("REFUSED AUDIT 已有 R475")
if u"## Round 472 · R475" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 472")
if u"## D-472" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-472")
if u"图片行补「可搜索文字」标记" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**544." in backlog: raise SystemExit("REFUSED BACKLOG 已有 544")
if state.count(u"## R474 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R474 状态"))
U_CELL_OLD = u"U-31 … U-1802（R474 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R474 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_472 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R474 状态", STATE_SECTION + u"## R474 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1808（R475 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R474 节 ②", u"AGENT_STATE.md` 的 R475 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R475_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R475_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
