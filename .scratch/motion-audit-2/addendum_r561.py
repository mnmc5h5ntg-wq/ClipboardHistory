# -*- coding: utf-8 -*-
"""R561 补记：本轮成对号（含收口前到数的 runner 四格）与 R562 的 ⓪ 读单。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R561 补记（2026-11-03 · 第 560 轮 / Round 558 · 成对号 + R562 读单）

① **本轮成对号（一次性 push 的自证）**：⓪ 笔 `5e08357`（纯台账开工节）、A 笔 `a8adab4`（判据 1 文件：`SolidRuler` 几何派生 + 真值表 + 契约钉子 + 三张刀表 + 名册）、台账笔 `324c513`（七本 + 636 头一格 + 629 第三数；**本轮产品 0 文件 ⇒ 帧基线一帧未动，无须 update**）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间三笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。本补记笔自己的跑取号时尚不存在 ⇒ 具名 NOT-RUN，R562 现读。sources 格本轮**没有变化**（`账上=R560/631f910 git=R560/631f910 一致=是` ⇒ 不需要补正笔）。
② **⓪ 那跑收口前到数**（`41509855001 ↔ 26c1939` = **concluded failure**，已等 2922s；`steps` 全量只列一朵红 = **STEP[19] `Motion coverage floor`**）：
- **⓪(a) 最好的一条**：`TASK_BOX_SIZE light 勾选=9x9px(9.00×9.00pt) 未勾选=9x9px(9.00×9.00pt) 宽差=0px 高差=0px 墨=62/49 倍率=1.0x 标记列 x 16..36`、`dark … 墨=65/49`，且 `TASK_BOX_NOT_RUN` **零行** ⇒ R560 那条判据在 runner 的 1x 上**真的判到了**（没走具名出口）⇒ **R560 的产品改动由 runner 签收**；同时它是本轮设计的活证据：**按 `scale` 派生的地板在 1x 站得住**。
- **⓪(b)** `HEAT_LEGEND_NOT_RUN=scale-too-low light/dark 倍率=1.0x 格宽=11px 实心判定 格6px/图例3px` = **连续第二跑同形**（上一跑 `41501679574↔7260562` 同串）⇒ 按 (b) 的预写口径升成判据位（本轮已落）。`HEAT_LEGEND_COVERAGE` **零行**，而这条「零」是**正读**、不是缺证据：同一跑同一通道族打出了 5 行 `HEAT_LEGEND_NOT_RUN` ⇒ 日志真的取到了、判据真的走到了、只是走了具名出口。**本轮改完之后 R562 才能验它是否真的开始判**（1x 实测 `格宽=11px` ⇒ 派生式给 `每方块采样点=9 ≥ 4` ⇒ 预期这一跑打 `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`）
- **⓪(c) 坏消息照实**：`过渡帧数=` 第三个 runner 真数 = **0**（逐字 `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=0 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 声明=200ms 窗口=1966ms 每格=75.6ms`），`MOTION_FLOOR_REDS=1`、`红的用例=testMarkdownModeLabelChangeIsAVisibleProcess`，红原文逐字（抄到 `ci_read.py readings` 的打印窗口截止处，尾部被工具截掉的部分没回补，也没手补） `XCTAssertGreaterThanOrEqual failed: ("0") is less than ("2") - 1x：两端夹逼只读到 0 个中间帧（要 ≥2）⇒ 按钮标签是硬切：每一帧要么等于前态要么等于后态。旧口径同批读 2 帧（首末连续差 0.0048，余量=首末差×0.15）；先查 `MarkdownModeButton` 的 `.id(title)`/`.transition(.opacity)`/`.animation(value:)` 是否还在` ⇒ **STEP[19] 那一跑因此红**。三跑并排 2 / 5 / 0（每格 71.5 / 26.0 / 75.6ms）⇒ 结论升级为**「≥2 帧地板在那台机器的钟上不是恒可满足的」**。**这一跑新增的一格信息**：同批**旧口径读到 2 帧、新口径读到 0 帧** ⇒ 两个估计量在同一跑上**给相反结论**（R558 换的是估计量，那时没有同跑双口径的证人）。按 629 既有口径具名入账，**没重开产品排查、没动 ≥2 地板、没改期望、没自行登记**（登记成 sampled 会改 CI 拦什么 ⇒ 归用户点头）
- **⓪(d)** STEP[9] `SKIP_ROSTER 键=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 **连续第三跑**绿；STEP[18] 622 本跑**无新值**（第十四值仍是 219.7ms/2 颗）。**这两格不是从"不在失败名单"推的**：`gh run view 41509855001 --json jobs` 现读 9=`success`（`Release script tests`）、18=`success`（`On-screen probe coverage floor`）、19=`failure`（`Motion coverage floor`）、7/11/15/16/17 全 `success`（读法见技能第 2 格：`steps` 视图只列 failure/skip，跑没跑要看 conclusion）。
③ **R562 的 ⓪ 必读**（逐条抄全部失败步骤；success 步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时未创建 ⇒ 现在去读。三格各问什么：
  (a) **`HEAT_LEGEND_COVERAGE … 倍率=1.0x` 还是 `HEAT_LEGEND_NOT_RUN=solid-unresolved`** —— 本轮把门从「倍率<1.5」换成「一个方块放不下 4 个采样点」，1x 的实测是 `格宽=11px → 每方块 9 个点 ≥ 4` ⇒ **预期这次终于判得到**（读数里会带 `地板 格4/图例4`）。若仍走出口 ⇒ 是派生式在真 1x 帧上算错了（不是产品问题），按读数修，**不许降地板、不许改期望、不许加豁免**。
  (b) `过渡帧数=` 的**第四个** runner 真数：三跑已 2/5/0 ⇒ 无论读到几都**按 629 既有口径具名入账**，不许重开产品排查；若它再次 ≤1，就把「登记成 sampled」与「改成相位不敏感」两条出路的代价摆给用户定夺（**本轮不自行登记**）。
  (c) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无`（第四跑）；STEP[18] 622 有无新值（第十四值 219.7ms/2 颗；锚点与容差不动）。
- 仍挂着、永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、`log not found`）；`b8949f5`/`1ea1bb7` 与 R560 中间五笔 ⇒ 同批无独立跑 `CI_UNREAD`。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到，账里没写任何结论；629 写「(B) 已落地 + 635 已结案 + **runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足**」，不写完全结案，两条出路等用户点头；**636 头一格已落地（无夹具 ⇒ 具名 NOT-RUN），单子继续开**，退场两步（先补 depth2 夹具 ⇒ 不破 R549 禁碰；再量三级同尺寸）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 11 面不变**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、R560 任务勾选框标记字体）—— **本轮产品 0 文件 ⇒ 不抬禁碰数**；刀号 **M1460** 起（现读最高 M1459）；4.5 地板、150 上限、120ms 阈值、**Motion ≥2 帧地板**、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%` 一律不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped **57 连四跑稳定**（R558–R561 都是 57 ⇒ 只记现读，不动门、不修回 55）。
⑤ **本轮现读（收口时）**：build 告警 0；判据 filter 绿（`Executed 2 tests, with 0 failures`，读数 `地板 格12/图例18 每方块采样点 格25/图例36`、`格色=8/9 图例色=5 缺=[]` 与旧常数**逐字相同**）；三把刀 **M1457/M1458/M1459 全 CAUGHT、RESTORE_CLEAN=yes**（M1459 设计成"像素判定不变、只有契约钉子红"）；三张表登记进名册 ⇒ 预检 **tables=358 covered=295 arms=757 bad=0**、`ARM_TOTAL files=451 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=445 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（三读**串行**）；判据卷 `UICaptureTests` **220/4 skipped/0 失败（619.4s）**；帧 **354 CHANGED=0 MISSING=0 ADDED=0**（产品 0 文件 ⇒ 基线一帧未动，无须 update，也没有漏改到别处）；全量 **1404/57/0（678.1s）**；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→93599，备份 `before-R561`）；清账 **162/63/0**；streak 现读 `PRODUCT_STREAK ledger_round=560 streak=1 last=631f910 last_round=559 newest=631f910 newest_round=559` ⇒ `PRODUCT_STREAK_LEDGER_OK streak=1 两格均由本命令派生并带引用`（**台账落盘之后现读**，R560 那格推错的事没重演）；电池 **`Ran 696 / OK (skipped=5)`、退出码 0**（台账与 `--write` 之后复跑；本轮**没有时序红以外的红**，sources 格本轮无需补正）。
⑥ **本轮自伤（照实记，同一坑的第四回）**：台账笔 `324c513` 里 STATE 的 ① 格落盘成两种没渲染完的形状 —— 标签后直接跟冒号（`① ：`）与一个「percent-s」占位符原文（`。占位符 同批无独立跑`）。根因：生成器用的 u-string 带格式化占位，而变量只存在于**打补丁的那个脚本**里、生成器里没有 ⇒ 写盘路径不校验被写物；标题形状守卫、`current_round()`、电池全都不红（U-450 / U-943 记过两回，规则「写盘前先 `py_compile`、再把渲染结果打出来看一眼」这次没执行）。处置：本补记笔**逐字补回** ① 格，并在补回的句子里明写「这半句是补正笔补的，不是开场就有的」，免得下一轮把补记的读数当成开场就读到。可复查读数（本轮实测，不含本节自己）：正则 `%(?=[a-zA-Z])` 在「`## R561 状态` 标题行 → `### R561 补记` 之前」这一段里 **补正前=1（就在 ① 格）⇒ 补正后=0**；复现命令 `python3 -c "import io,re;t=io.open('AGENT_STATE.md',encoding='utf-8').read();s=t[t.index(u'## R561 状态'):t.index(u'### R561 补记')];print(len(re.findall(r'%(?=[a-zA-Z])',s)))"`（这段里没有别的「percent+字母」形状 ⇒ 计数就是那一处）。**根因不是笔误而是通道**：写台账的脚本没有「渲染后回读一次」的闸门 ⇒ 与 634/635 同族（只打印失败通道的尺抓不到「根本没打印」）。本轮**没有为它开新单**（同一坑的落地条件是「生成器自带一次 re-read」，本轮推进在尺上、不同时开两格）；R562 若要落它，位置就写在这句话里。

"""


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = (u"与声明时长一字未改。\n"
              u"## R561 ⓪ 开工")
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    if u"### R561 补记" in t:
        sys.stderr.write("ALREADY_WRITTEN\n")
        return 1
    if not check:
        new = (u"与声明时长一字未改。\n" + BLOCK.strip(u"\n") + u"\n\n## R561 ⓪ 开工")
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R561_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
