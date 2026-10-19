#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 `docs/motion_surface_ledger.json`（R127 建、R128 补强）。

为什么用脚本生成而不是手写 JSON：行数、地板、格子总数这三格必须**算出来**，手写就会抄错（U-264）。
CJK 串里一律用「」，不用 ASCII 双引号 —— 那会同时打断本文件与 JSON。

R128 的两处补强（都是上一轮自己登记的账）：
  U-424 → 证据指针必须有**可复查的具体对象**（源码文件 / BACKLOG 号 / D-号 / 批次号 / docs 路径），
          只写轮次号（`R14 / R15`）不算。所以本轮把 18 行的指针逐行补成代码对象，
          并把形状判据加进闸门 —— **先修数据再加判据**，反过来的话闸门会红在自己的表上。
  U-425 → 地板取「已清账格子数」，而 `not-measured` 不算已清账；另加两条"名册扩张要付账"的判据：
          每个表面至少一行、每个状态至少一行。这样往名册里塞新表面就会立刻红，
          覆盖率不再能被扩张稀释。
"""
import io
import json

surfaces = [
    "主窗口/列表行", "主窗口/详情区", "主窗口/侧栏", "主窗口/搜索框", "主窗口/筛选条",
    "主窗口/拖入落点", "主窗口/提示条", "设置窗口/侧栏", "设置窗口/热图",
    "设置窗口/开关与滑块", "设置窗口/说明段", "菜单栏/状态图标", "菜单栏/状态菜单",
    "菜单栏/推荐面板", "浮层/列表行", "浮层/搜索框", "浮层/空态",
    "设置窗口/快捷键录制器",   # R141 新加：这一处有自己的状态语言（录制中），不归「开关与滑块」
]
states = ["空", "加载", "错误", "成功", "选中", "悬停", "按下", "聚焦", "禁用"]

# R177 / BACKLOG 204：撤掉的表面**不许静默消失**。退役要在这里登记理由，
# `scripts/motion_surface_gate.py` 拿 HEAD 那一版对账：已清账格子少了而表面没登记退役 ⇒ `RETIRED_UNDECLARED` 红；
# 登记了退役却还在名册里 / 还留着行 / 理由为空 ⇒ 各有一格红。
retired_surfaces = {
    "浮层/底部说明": "R177 撤词表项：这一层在今天的浮层里没有承载物（`QuickPickController.swift:262` 的面板 stack 只有 field / empty / scroll 三个子视图，`footerLabel` / `hintLabel` 在产品源码 0 命中）。"
                    "键位提示行判为不做（见 DECISIONS 的 D-19x）：300pt 高的浮层里加一行常驻 chrome 会与内容争注意力，"
                    "而唯一真正需要提示的场合（搜不到东西）已经在空态那一句里就地给了 Esc。"
                    "留着这个表面只会让九格逐格判 not-applicable、每轮都算成已推进 —— 那正是目标禁止的为清账而清账。",
}

# (surface, state, verdict, 理由, 证据指针)
# 指针规则（U-424）：至少含一个可复查对象 —— Sources/…swift、Tests/…swift、docs/…、
# scripts/…、BACKLOG 号、D-号、批次号。轮次号可以附带，但不能是唯一内容。
rows = [
    ("主窗口/列表行", "悬停", "kept",
     "0.12s 的底色 + 图标/次要文字 opacity 0.55→0.78；更快会读成闪烁，更慢跟不上鼠标",
     "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift 的 `.animation(for: .hover)`；取证见 R14/R15"),
    ("主窗口/列表行", "按下", "added",
     "macOS 12 上 `.borderless` 那颗按下去原本没有任何反馈；给一层不缩放的按压",
     "Sources/ClipboardHistoryApp/Views/PressableStyle.swift；R4/R13/R20"),
    ("主窗口/列表行", "选中", "kept",
     "选中靠系统强调色 + 把视口外的行滚进来；再给选中加动画会把「哪一行被选中」变成运动而不是状态",
     "Sources/ClipboardHistoryApp/Views/SelectedRowRevealer.swift；BACKLOG 61"),
    ("主窗口/详情区", "加载", "added",
     "spinner 说「我在等」，骨架说「内容马上来」；扫光是全仓唯一常驻时钟，30Hz、只在 `.loading` 分支存在、8s 上界",
     "Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift；BACKLOG 38；R84/R85"),
    ("主窗口/详情区", "空", "kept",
     "空态与内容之间是 0.16s 交叉淡 —— 只有一臂的过渡等于没有，所以两臂都挂",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift 的 `.contentFade`；R16"),
    ("主窗口/详情区", "错误", "kept",
     "错误走详情区文本与提示条两条通道；给错误本身加动画会让它读成装饰而不是回执",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift；BACKLOG 58（R41 回执要成人话）"),
    ("主窗口/侧栏", "空", "kept",
     "空列表与有列表之间是 contentFade 换页，而不是给每行做入场动画 —— 后者会在采集高频时逐帧重排",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `.animation(for: .contentFade, value: filteredEntries.isEmpty)`"),
    ("主窗口/搜索框", "悬停", "kept",
     "搜索框的 hover 与行同一档 0.12s；再重会抢过列表本身",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `.animation(for: .hover, value: isHovered)`"),
    ("主窗口/搜索框", "空", "kept",
     "有字↔无字之间是 contentFade（清空按钮的出现/消失跟着走），不是瞬切",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `.animation(for: .contentFade, value: text.isEmpty)`"),
    ("主窗口/筛选条", "选中", "added",
     "筛选药丸的滑动/尺寸变化走 `FilterPillMotion`，是纯函数 + 令牌梯子里被守卫的那一族",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 里的 FilterPill 段；Tests/ClipboardHistoryAppTests/FilterPillMotionTests.swift"),
    ("主窗口/拖入落点", "悬停", "added",
     "拖入时整组一条亮带 + 落点框 0.12s；没有落点反馈时用户分不开「接住了」与「没接住」",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 dropTarget 三处；BACKLOG 117（R84 整组一条亮带）"),
    ("主窗口/提示条", "成功", "added",
     "回执行淡入 + `emphasis` 0.16s；「声明了动效却没供电」被抓到之后要么供电要么撤声明",
     "Sources/ClipboardHistoryApp/Views/ContentView.swift 的 `.animation(for: .bannerIn)`；R42/R43"),
    ("主窗口/提示条", "错误", "added",
     "复制失败走同一条淡入但换文案与配色；不给它动效会让失败读成「什么都没发生」",
     "Sources/ClipboardHistoryApp/Views/ContentView.swift；BACKLOG 58/59（R40/R41）"),
    # 曾经在这里写过一行「主窗口/提示条 × 消失」，被闸门以 `UNKNOWN_CELL` 拦下：
    # 「消失」不在这九个状态里 —— 它是一次转换，不是一个状态。留着这行注释是为了记下
    # **闸门拦住了我自己造的词**（R128），而 `bannerOut` 那条事实挂在上面两行的指针里。
    ("主窗口/提示条", "选中", "not-applicable",
     "提示条没有「被选中」这一态；记 not-applicable 是为了让它不再被当成没做",
     "docs/motion_surface_ledger.json 的 verdict 词表第 4 项"),
    # R173：浮层底部那一行说明逐格判（它是一把 NSTextField 静态标签 ⇒ 这几类交互态是 not-applicable，不是没做）。
    # 「空」与「选中」两格本轮故意不判：证据要落在标签那一行本身 ——
    # `isSelected` 在这个文件里确实有 4 处，但那都是列表行的，拿文件级缺席替「说明行不可选中」作证就是假话。

    ("设置窗口/侧栏", "悬停", "kept",
     "与主窗口行同一档 0.12s；侧栏行是导航不是内容，动得比内容重会抢注意力",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `.animation(for: .hover)`"),
    ("设置窗口/侧栏", "选中", "kept",
     "强调色药丸 + 图标与标签同色：两枚多色符号的 `.hierarchical` 换成 `.monochrome`，暗档 22 行黑底黑图标归 0",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift；scripts/real_screen_sidebar_icons.py 的 `REALSCREEN_ICON_BAND 0..5`；BACKLOG 170"),
    ("设置窗口/热图", "悬停", "added",
     "格子描边一圈（`VisualHeat.hoverRingOpacity` 是有名字的数）+ 日期与当日条数的 hover 提示；事务挂在变更点上而不是下游 `.animation(value:)`",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift；R45 第一次有帧"),
    ("设置窗口/开关与滑块", "禁用", "kept",
     "禁用态第一次有帧之前，那颗在 macOS 12 上永远点不动的开关连一张静帧都没有；这一格要的是可见性而不是动效",
     "Sources/ClipboardHistoryApp/Views/GlassControls.swift；R39 禁用态帧；docs/frame_baseline.json"),
    ("设置窗口/说明段", "悬停", "not-added",
     "说明文字是静态解释，响应鼠标会让它和它解释的那个开关抢注意力；判过之后决定不加",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的说明段（R33/R35 全覆盖那一族只判可读性）"),
    ("菜单栏/状态图标", "悬停", "not-applicable",
     "状态栏图标的高亮由系统绘制（NSStatusItem），SwiftUI 侧没有可用的 hover 语义；这一格不是漏做",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift；读数 `MENUBAR_GLYPH`"),
    ("菜单栏/状态菜单", "成功", "kept",
     "复制成功的反馈走主窗口提示条与菜单项文案，不给 NSMenu 项加动画（那层不执行 SwiftUI 过渡）",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift；BACKLOG 165（R111）"),
    ("菜单栏/状态菜单", "加载", "not-added",
     "不给这行加动画，理由不是难而是自相矛盾：`NSMenuItem` 挂不了动画视图，而 macOS 的原生菜单在加载时就是改**文字**"
     "（本仓库已经这么做：`isRefreshingPredictions ? \"正在整理推荐…\" : \"暂无推荐\"）。"
     "再叠一个假转的圈，等于把「文字说在算、图形说没在动」同时讲给用户",
     "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 `menubar-refreshing` 夹具"
     "（帧 menubar-refreshing-320x120-light/dark，R151 真看：符号静止 + 「正在整理推荐…」）；"
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift:147、:282；"
     "Sources/ClipboardHistoryApp/Utilities/StatePresentation.swift:92；BACKLOG 165"),
    ("菜单栏/状态菜单", "错误", "not-applicable",
     "这扇表面没有错误态可动：推荐算不出来时它回落到「暂无推荐」（同一三元式的 else 臂），"
     "而真失败（写盘 / 读档 / 写剪贴板）走主窗口提示条与详情区回执 —— 那是另外两个已清过的表面。"
     "给不存在的状态加动效，只会逼我造一条假的错误路径",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift:147、:282；"
     "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 `menubar-*` 夹具只有 empty / refreshing / recommendations 三种；BACKLOG 165"),
    ("菜单栏/推荐面板", "加载", "not-added",
     "`MenuBarExtraStyle.menu` 编译成**真 NSMenu**，SwiftUI 的过渡在那一层根本不执行；在这里挂 `.transition` 等于给自己造一条永不生效的声明",
     "Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift 的注释；D-055 / M15 实测"),
    ("浮层/列表行", "选中", "kept",
     "浮层选中是灰、侧栏选中是蓝 —— 同一台机器同一条离屏通道对两种控件给出两种颜色，所以这里不跟侧栏对齐，也不加动画",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 selectRow 路径；R102 按控件回答"),
    ("浮层/搜索框", "聚焦", "added",
     "焦点环：只读 alpha 的那把尺曾把「有环」读成「没环」，把 alpha 与亮度两轴都配上之后才有判据",
     "Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift 的焦点族；R76/R77/R78"),
    ("浮层/空态", "空", "kept",
     "空态是一句成句的话而不是动画；给「没有结果」加动效会把注意力钉在空上",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift；读数 `QUICKPICK_EMPTY_SENTENCE`（R64）"),
    # ---- R131 清的十二格（每一格的理由都落在一个可复查的对象上：源码里的调用点、
    #      或"整份文件里 grep 某个词 0 命中"这种缺席证据 —— 缺席也要是被量出来的缺席）----
    ("设置窗口/热图", "空", "kept",
     "零记录不画一张空日历，而是一句成句的话；空↔有记录之间挂 contentFade，"
     "而动画的键是「有没有记录」而不是那份计数本身 —— 后者每次复制都换实例，整张日历会跟着抖",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 的 isEmpty 分支与 `.animation(for: .contentFade)`"),
    ("设置窗口/热图", "选中", "not-applicable",
     "格子只回答「哪天多少条」，没有可延续的选中语义；整份文件里 Button / TapGesture / selection 全部 0 命中"
     "（本轮实测，不是印象）。给它一个选中态会诱导「点一下看详情」，而那里没有详情",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=onTapGesture 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=selection"),
    ("设置窗口/热图", "聚焦", "not-applicable",
     "键盘不落在格子上：日历是统计读出，不是可遍历的列表；若要让它可遍历，先要回答「Tab 到 365 个格子要按几次」",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=focused；与 BACKLOG 61 的滚动语义对照"),
    ("设置窗口/开关与滑块", "选中", "kept",
     "勾选框选中就是系统强调蓝，这一格不需要产品动 —— 但这条结论以前只有离屏帧，而那一层不解析语义色（139）。"
     "R132 换成真机判：同一张帧里参照（侧栏选中行）最大 b-r=194、内容区 190、比值 0.979、强蓝 2463 颗，"
     "包围盒正好压在勾选框那一列",
     "scripts/real_screen_control_chroma.py；BACKLOG 139（R132 结案）"),
    # ---- R134 清掉的六格（浮层那一卷 + 搜索框聚焦 + 设置里的系统控件 + 状态菜单）----
    # ---- R135 清掉的七格（筛选条那一卷 + 设置侧栏 + 浮层输入框 + 推荐面板）----
    # ---- R136 清掉的八格（热图与浮层的"加载/错误"、落点的"按下/聚焦"、状态图标的"选中/聚焦"）----
    # 全部是**缺席立论**，所以每条都写成 缺席:路径=词 让闸门去文件里查（U-436）。
    # 落点那两格刻意不写整文件缺席 —— 那个文件里 pressedStyle 有 2 处、focusable 有 1 处，
    # 只是它们长在行与药丸上（U-449）。路径一律写字面量：上一版在这里用了 %s 格式化，
    # 而生成器里没有那些变量 ⇒ NameError，而闸门读的是上一版 JSON 仍然报 ok（U-444 第二次，U-450）。
    ("设置窗口/热图", "加载", "not-applicable",
     "那一屏没有「正在读」这一态：按日计数来自已经在内存里的账本，渲染时不等待任何 IO。"
     "（ProgressView 与 isLoading 在该文件各 0 命中，本轮实测）",
     "缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=ProgressView 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=isLoading；Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift"),
    ("设置窗口/热图", "错误", "not-applicable",
     "热图自己不报错：写盘与读盘失败的通道是提示条与详情区（BACKLOG 58 那一族），"
     "这一屏出现的唯一非常态是「还没有记录」那句成句的话",
     "缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=error；Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 的 isEmpty 分支；BACKLOG 58"),
    ("浮层/空态", "加载", "not-applicable",
     "浮层的数据是内存里那份历史，打开即有全貌，没有「读一半」的中间态；"
     "空态那一枚标签是 NSTextField 而不是骨架（ProgressView 与 isLoading 在该文件 0 命中）",
     "缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=ProgressView 缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=isLoading；Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `emptyLabel`"),
    ("浮层/空态", "错误", "not-applicable",
     "那一层没有错误通道：查询无结果是「空」不是「错」，而写回失败由主窗口提示条说话"
     "（浮层关掉之后用户需要知道为什么没粘上）",
     "缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=error；Sources/ClipboardHistoryApp/Managers/QuickPickController.swift；BACKLOG 58"),
    ("主窗口/拖入落点", "按下", "not-applicable",
     "落点不是可按压的控件：它唯一的态是「拖拽进来了没有」（isTargeted），"
     "描边、过渡与那层光晕全都挂在这一个布尔上。没有手指按住的对应时刻",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `.onDrop(of:isTargeted:)` 与 `transition(for: .dropTarget)`"),
    ("主窗口/拖入落点", "聚焦", "not-applicable",
     "键盘没有「把文件放到这里」的对应动作，所以这层不接收焦点；"
     "同文件里那处 focusable 是给筛选条留键盘导航的，不在落点上",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `.onDrop(of:isTargeted:)`（落点那一段）"),
    ("菜单栏/状态图标", "选中", "not-applicable",
     "NSStatusItem 的按钮没有「选中」这一语义：只有常态与菜单打开时由系统画的高亮，"
     "我们一层都没叠（该文件 highlight 与 selected 各 0 命中）",
     "缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=highlight 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=selected；Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 `statusItem`"),
    ("菜单栏/状态图标", "聚焦", "not-applicable",
     "状态栏图标不在键盘焦点链里：Tab 走的是窗口内的 key-view 环，菜单栏那一行不参与。"
     "想让它可达要走系统的全键盘控制，那是另一件事，不该由这里补一层假的焦点环",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 `installStatusItemIfNeeded`；Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"),
    # ---- R141：快捷键录制器。这一格是**真做了一处动效**，不是清账（BACKLOG 173 欠的那一次）。
    #      尺的读数在 `HotKeyRecorderEvidenceTests` 的 `RECORDER_RING` 那两行（本机 2x：
    #      强度 0.965 / 0.976，面积 0.412 / 0.406，@1x 录制态 600 个墨像素，静置两档都是 0）。
    ("设置窗口/快捷键录制器", "按下", "added",
     "这颗按钮在录制态会吃掉所有按键，而它以前唯一的说法是一句瞬间换掉的标题 —— 标题不是形状。"
     "现在进入录制给一圈强调色描边（`VisualStroke.highlight` 那一档，与命中高亮同一档），"
     "由 `.animation(MotionCatalog.animation(for: .emphasis), value: isRecording)` 供电；"
     "不脉动、不常驻（常驻时钟全仓只留骨架扫光那一条）。静置态宽度与颜色都是「没有」，"
     "所以 136 张旧帧逐字节不变（`COMPARED=136 / CHANGED=0`）",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `HotKeyRecorderRing`；"
     "Tests/ClipboardHistoryAppTests/HotKeyRecorderEvidenceTests.swift；BACKLOG 173"),
    ("设置窗口/快捷键录制器", "成功", "not-added",
     "录到新组合键之后是**回显**，不是庆祝：标题必须立刻等于新组合，"
     "淡一下会让用户不确定自己刚按到了什么（这一格与「状态要说话」同族，但说话的是字不是动）",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `keyDown`（提交分支里直接 `title = shortcut.displayString`）；"
     "Tests/ClipboardHistoryAppTests/HotKeyRecorderButtonTests.swift"),
    # ---- R140 清掉的八格。缺席断言的**射程**按「这个文件是不是只装这一个表面」来定（U-463）：
    #      QuickPickController 整个文件就是浮层 ⇒ 可以写文件级缺席；
    #      SettingsView 同时装着侧栏与六个分区 ⇒ 对「侧栏」只引用常量，不引用文件级缺席。
    ("主窗口/详情区", "选中", "kept",
     "详情区有一件自己跟着选中走的事：搜索命中的高亮（正文里按当前查询标出命中）。"
     "但「选中哪一条」由列表那一侧说，详情区不再叠一层选中描边 —— 否则同一屏两个地方都在喊「是这个」",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift 的 `highlightQuery`（两处调用点）"),
    ("主窗口/详情区", "禁用", "not-applicable",
     "详情区没有整块禁用态：它是只读文本加几颗各有自己可用态的按钮。"
     "把整块压灰会连带把可读的内容也压掉，而「读不了」从来不是这里要表达的事",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift 缺席:Sources/ClipboardHistoryApp/Views/DetailView.swift=disabled"),
    ("主窗口/侧栏", "选中", "kept",
     "分类选中是整行药丸加图标同色，跟着 selection 走一档动画；这一格本来就有，判过之后保留",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `selected`（9 处）与 `.animation(for: .selection)`" ),
    ("设置窗口/侧栏", "空", "not-applicable",
     "分类是常量，六行永远在：这一屏不存在「空的侧栏」。这里刻意**不引用文件级缺席** —— "
     "SettingsView 同时装着六个分区，文件级缺席说明不了侧栏那一列的事（U-463）",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `SettingsCategory`（allCases 常量）"),
    ("设置窗口/侧栏", "加载", "not-applicable",
     "侧栏行不等待任何 IO：分类与选中项都在内存里。这里可以引用文件级缺席，因为说的是「这一屏没有加载态」—— "
     "ProgressView 与 isLoading 在整个 SettingsView 里 0 命中（本轮实测）",
     "缺席:Sources/ClipboardHistoryApp/Views/SettingsView.swift=ProgressView 缺席:Sources/ClipboardHistoryApp/Views/SettingsView.swift=isLoading；Sources/ClipboardHistoryApp/Views/SettingsView.swift"),
    ("浮层/列表行", "空", "not-applicable",
     "没有行就没有这一格：空态由「浮层/空态」那一格承担（那里是一句成句的话，不是骨架）",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `emptyLabel`"),
    ("浮层/列表行", "错误", "not-applicable",
     "那一层没有错误通道：查询无结果是「空」不是「错」，写回失败由主窗口提示条说话。"
     "整个文件 ProgressView / isLoading / disabled 全 0 命中 ⇒ 它连「在读 / 不能动」的表达都没有",
     "缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=disabled；Sources/ClipboardHistoryApp/Managers/QuickPickController.swift；BACKLOG 58"),
    ("菜单栏/推荐面板", "成功", "not-applicable",
     "推荐面板被编译成真 NSMenu，成功回执不在这层：复制成功走主窗口提示条与菜单项文案。"
     "该文件 highlight 与 selected 全 0 命中 ⇒ 我们在这层一层反馈都没叠",
     "缺席:Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift=highlight 缺席:Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift=selected；Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift；BACKLOG 58"),
    ("主窗口/筛选条", "悬停", "kept",
     "缩放与底色两档一起给：减弱动态时缩放归 1.0，底色那一层就是**唯一**的悬停表达 —— "
     "以前这一段只剩缩放一种说法，于是『开了减弱动态 = 悬停没有反馈』",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `FilterPillMotion.hoverFill` 与 `hoverScale`"),
    ("主窗口/筛选条", "按下", "kept",
     "药丸自己挂了按压样式（半径走 control 那一档），与主窗口其它小控件同一族；"
     "不给它缩放以外的第二种反馈，因为按下与选中在药丸上是同一个动作",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `.pressedStyle(in: VisualShape.rounded(VisualRadius.control))`"),
    ("设置窗口/侧栏", "聚焦", "not-added",
     "选中那一整条药丸已经在说『你在哪』，再画一圈焦点环会出现两个当前 —— 与主窗口列表行 × 聚焦同一族，"
     "那边有焦点链实测撑着（连按 14 次 selectNextKeyView 的落点名单）",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `SettingsSidebarRow`；Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"),
    ("设置窗口/侧栏", "禁用", "not-applicable",
     "分类是常量，六行永远可点：这一屏没有『把某一类禁掉』这条分支。"
     "（同文件里那四处 disabled 长在快捷键与数据页的控件上，不在侧栏行上 —— 所以这里不写整文件缺席）",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `SettingsSidebarRow`"),
    ("浮层/搜索框", "悬停", "not-added",
     "那一栏一出现就是第一响应者：焦点已经在说话，悬停再加一档会和焦点环抢同一个注意力位",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `QuickPickSearchField`"),
    ("浮层/搜索框", "禁用", "not-applicable",
     "浮层存在即可输入，没有『禁用的搜索框』这一态：真要禁的是整个浮层，而那是关闭而不是禁用",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"),
    ("菜单栏/推荐面板", "悬停", "not-applicable",
     "macOS 13 那一侧走 `MenuBarExtra(...).menuBarExtraStyle(.menu)`，内容被编译成**真 NSMenu**："
     "SwiftUI 的过渡与 hover 修饰符在那一层不执行。这条判定挂在一个 API 的默认值上，"
     "所以 R135 给它配了自己的守卫（那行字面量被删或改成 .window 就红），不再只靠注释",
     "Sources/ClipboardHistoryApp/App.swift 的 `.menuBarExtraStyle(.menu)`；Tests/ClipboardHistoryAppTests/DocumentationAnchorTests.swift"),
    ("浮层/列表行", "悬停", "kept",
     "行悬停真的有一层底色：那个「哪一行被悬停」的属性会驱动表格重绘，行视图自己带跟踪区"
     "（进入/移动/离开各写一次）。取证通道单独存在，是因为离屏那一层送不进 mouseEntered",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `rowHoveredForCapture` 与行视图的 `hovered`"),
    ("浮层/列表行", "按下", "not-added",
     "行不是按钮：在这一层 mouseDown 就是选中，再叠一层按压底色会出现「按下的行」与「选中的行」两种底色"
     "（SwiftUI 的 pressedStyle 在真 AppKit 那一层根本不执行，D-055 同一族）",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=pressedStyle"),
    ("主窗口/搜索框", "聚焦", "kept",
     "焦点环是系统画的那一圈，被显式恢复过（审计第二轮 1.10 实测它被关掉）；跟着焦点一起变的是"
     "放大镜图标那一档灰度 —— 不聚焦时它是次要色，聚焦后抬到主色，这一档不给动画",
     "Sources/ClipboardHistoryApp/Views/ChineseTextContextMenu.swift 的 `focusRingType = .default`；Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `isActive`"),
    ("设置窗口/开关与滑块", "悬停", "not-added",
     "勾选框与滑块是系统控件，自己画悬停档；SwiftUI 侧再叠一层会和它打架 —— "
     "R20 在圆形图标按钮上抓到过这种叠层（两层 hover 底色叠出第三档），当时的修法就是把悬停交给画它的那一处",
     "Sources/ClipboardHistoryApp/Views/GlassControls.swift 的 `pressedStyle(in: Circle(), hoverLevel: 0)`"),
    ("设置窗口/开关与滑块", "按下", "not-added",
     "同族：按下由系统画，这一格刻意不给自定义按压。开关的按下与它的状态切换是同一个动作，"
     "再加一层底色会把「我按了」与「它变了」混起来",
     "Sources/ClipboardHistoryApp/Views/GlassControls.swift；BACKLOG 166 那一族（自定义按压只给没有系统反馈的控件）"),
    ("菜单栏/状态菜单", "悬停", "not-applicable",
     "那一层是真 NSMenu：高亮由系统画，SwiftUI 的过渡与 hover 修饰符根本不执行。"
     "这不是「还没做」，是「这一层没有可挂的地方」",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 `NSMenuItem`；D-055"),
    ("主窗口/列表行", "聚焦", "not-added",
     "行不在 AppKit 的 key-view 环里，也不该在：实测连按 14 次 `selectNextKeyView`，第一响应者只在搜索框与详情文本之间走。"
     "再给行画一圈焦点环就会出现两个「当前」——选中环与焦点环各说一件事",
     "Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift 的 `testFocusChainReachesTheSearchFieldAndNotOnlyTheDetailTextView`"),
    ("主窗口/列表行", "加载", "not-added",
     "骨架只出现在详情区（那条约束就写在骨架自己的注释里）：行是「有数据才存在」的东西，"
     "给整列同时做入场或骨架会把「在读」画成一片闪动，而 500 条上限下那片闪动每次启动都会来",
     "Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift 开头关于 `SkeletonPreviewView` 出现位置的说明"),
    ("主窗口/详情区", "悬停", "kept",
     "详情区只有那颗「原文/渲染」的 chip 响应鼠标；正文不响应 —— 正文是可复制的内容不是控件，"
     "整块文字跟着鼠标亮会让选择目标抖动",
     "Sources/ClipboardHistoryApp/Views/DetailView.swift 的 `.onHover` 调用点（chip 那一处）"),
    ("主窗口/提示条", "禁用", "not-applicable",
     "横幅没有禁用态：它要么在、要么在淡出。一条点不动的回执再灰一档只会读成「系统卡了」，"
     "而它存在的唯一理由就是让刚才那一下有回执",
     "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift 缺席:Sources/ClipboardHistoryApp/Views/NoticeBanner.swift=disabled；BACKLOG 58"),
    ("主窗口/提示条", "聚焦", "not-applicable",
     "横幅不该抢焦点：抢了会把用户正在输入或正在选中的东西踢掉，而它只是回执",
     "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift 缺席:Sources/ClipboardHistoryApp/Views/NoticeBanner.swift=focus"),
    ("菜单栏/状态图标", "按下", "not-applicable",
     "那颗按钮由系统状态栏绘制，SwiftUI 侧拿不到按下态，也不该自己叠一层高亮 —— 叠了会和系统自己的高亮打架",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 `installStatusItemIfNeeded`（`NSStatusBar.system.statusItem`）"),
    ("设置窗口/说明段", "空", "not-applicable",
     "说明段的有无由分区决定，不存在「空的说明段」；把这一格记下来是为了让下一轮不去给它补一个占位动画",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift"),
    ("设置窗口/说明段", "错误", "not-applicable",
     "错误不走说明段这条通道：写盘与复制失败由提示条和详情区说话，说明段讲的是规则不是状态。"
     "记成 not-applicable 而不是留空，是因为留空看起来像还没判",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift；BACKLOG 58 / D-155"),
    ("设置窗口/说明段", "按下", "not-applicable",
     "说明段没有可按压的东西；它唯一的交互是「悬停时把整段折起来的那条 `.help`」，而那一条已经判过（悬停 not-added）",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `.helpLabel`；R128 已登记的说明段 × 悬停"),


    # R155（第 157 轮）一批：搜索框与侧栏容器逐格判完。证据都是**这一轮 grep 过的那几行**，
    # 判成"不加"的格要能在源码里被证伪（这条规矩来自 R74/R75：只在自家夹具上成立的理由不算理由）。
    ("主窗口/搜索框", "按下", "kept",
     "那颗 × 挂的是控件档按压（`.pressedStyle(in: Circle(), hoverLevel: controlHover, labelPadding: 4)`），而文本区按下去是系统插入点 —— 再叠一层底色会把「我在编辑」说成「我是按钮」",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `.pressedStyle`（R20 抬命中区 14→22pt、R21 抬静置墨到 control 那一档）"),
    ("主窗口/搜索框", "选中", "not-applicable",
     "文本框的「选中」是插入点与选区，作者是不锈钢的 NSTextField；这一层没有可延续的 selection 语义（整份文件没有 `selection`），给「焦点在搜索框」再画一圈会和系统的插入点变成两个当前",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift（无 selection 分支）；`ChineseEditableTextField` 才是文本的宿主"),
    ("主窗口/搜索框", "禁用", "not-applicable",
     "不存在「禁用的搜索框」这条分支：全文件没有 `disabled` / `isEnabled`。真要灰掉的只有那颗 ×，而它的有无由 `text.isEmpty` 决定 —— 消失比禁用诚实",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `if !text.isEmpty`"),
    ("主窗口/搜索框", "加载", "not-applicable",
     "搜索是对已经在内存里的那份历史做过滤（`perform(.updateSearch)` 同步返回），没有「读一半」的中间态；全文件无 `ProgressView` / `isLoading`。采集路径不许有同步磁盘写那条红线，也正是要这里**不出现**转圈",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `perform(.updateSearch(…))`；账本 C-1 采集路径约束"),
    ("主窗口/搜索框", "成功", "not-applicable",
     "搜索的「成功」就是列表变短，回执不写在框里；无结果那一句由空态承担，并且带着一颗「清除搜索」的动作按钮 —— 那才是这条通道的回执",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `EmptyStateView(actionTitle: … 清除搜索)`"),
    ("主窗口/搜索框", "错误", "not-applicable",
     "这一层没有错误通道：查询无结果是「空」不是「错」。把「0 条匹配」画成红色错误会把一次正常过滤读成一次故障（与 U-5 那句「说清发生了什么 + 说清下一步」相反）",
     "Sources/ClipboardHistoryApp/Views/SearchField.swift 无错误分支；账本 U-5"),
    ("主窗口/侧栏", "加载", "not-applicable",
     "侧栏不等待任何 IO：`filteredEntries` 来自内存里那份 store。全文件没有 `ProgressView` / `isLoading` / `disabled` ⇒ 这一格以前被当成「没做」，其实是「没有这一态」",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift（本轮 grep：无 ProgressView / isLoading / disabled）"),
    ("主窗口/侧栏", "悬停", "not-applicable",
     "侧栏的悬停就是行的悬停，已由「主窗口/列表行 × 悬停」那格判过（0.12s 底色 + 图标 opacity）；容器自己再响应鼠标会让整块侧栏跟着亮，两把尺问同一件事时按 R86 的分工只留一颗",
     "docs/motion_surface_ledger.json 的「主窗口/列表行 × 悬停」；`NonRedundancyTests` 的分工规矩"),
    ("主窗口/侧栏", "成功", "not-applicable",
     "复制成功的回执走提示条与行内符号那两格（已判），侧栏容器不再叠第三层：一条回执被三处同时说出来的时候，用户会去找「到底哪儿变了」",
     "docs/motion_surface_ledger.json 的「主窗口/提示条 × 成功」；Sources/ClipboardHistoryApp/Views/NoticeBanner.swift"),
    ("主窗口/侧栏", "禁用", "not-applicable",
     "侧栏没有整体禁用态：搜索框与筛选条随时可改，列表的有无由数据决定。把整块压灰会连带把「还能改筛选」这条出口一起压掉",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 无 disabled 分支"),
    # R158（第 160 轮）一批：设置侧栏行与快捷键录制器逐格判完。两处"不加"都有源码证人，
    # 且都是**这一轮真的读过的行**（不是印象）：录制器那颗是真 NSButton，侧栏行挂的是不缩放的按压样式。
    ("设置窗口/侧栏", "按下", "kept",
     "有按压，但**刻意不缩放**（`.pressedStyle(in: VisualShape.rounded(VisualRadius.panel), scales: false)`）：侧栏行是导航，"
     "让整列跟着一次按下缩放会把「我在切分区」读成「整块在抖」；底色与选中同一层，跟着 hover/selection 两档动画走",
     "Sources/ClipboardHistoryApp/Views/SettingsView.swift 的 `.pressedStyle(… scales: false)` 与 `.animation(for: .hover)`"),
    ("设置窗口/快捷键录制器", "悬停", "not-applicable",
     "这颗不是 SwiftUI 按钮：`makeNSView` 里 `button.setButtonType(.momentaryPushIn)`，悬停与按下都由 AppKit 画。"
     "在 SwiftUI 侧再叠一层 hover 底色正是 R20 在圆形图标按钮上抓过的『两层打架』；录制态另有自己的一句话（描边那一格）",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `setButtonType(.momentaryPushIn)`；账本 R20"),
    ("设置窗口/快捷键录制器", "选中", "not-applicable",
     "这颗按钮没有可延续的『选中』语义：按下即进入录制态，而录制态是一圈强调色描边 + 标题改成『按下新组合键』"
     "（那一格已判为 added）。再给『选中』画一层会出现『既在录制又被选中』两个当前",
     "docs/motion_surface_ledger.json 的「设置窗口/快捷键录制器 × 按下」；Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的录制态标题"),
    # R164（第 166 轮）一批：快捷键录制器与浮层剩余状态逐格判完。
    # 每条"不加"都绑本轮实测的缺席计数或那一行代码，不是印象（判为不做要能在源码里被证伪）。
    ("设置窗口/快捷键录制器", "加载", "not-applicable",
     "这层不等待任何东西：`ProgressView` / `isLoading` 实测各 0 处。进入录制态由点击与 firstResponder 决定，"
     "不存在「读一半」的中间态；给它转圈会把一个即时动作演成一次任务",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 缺席:Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift=ProgressView,isLoading"),
    ("设置窗口/快捷键录制器", "禁用", "not-applicable",
     "没有「禁用的录制器」这条分支（`disabled` / `isEnabled` 实测 0 处）。真要收回控制权走的是**退出录制**"
     "（`cancelRecording`：交还 firstResponder、标题还原），不是把按钮灰掉 —— 灰掉会留下"
     "「它在录制却点不动」那种 macOS 12 上抓过的错（R39 那一族）",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `cancelRecording()`"),
    ("设置窗口/快捷键录制器", "空", "not-applicable",
     "这颗按钮永远有标题：`shortcut.didSet { if !isRecording { title = shortcut.displayString } }`。"
     "未设置时显示的是组合键自己的显示串，不是一片空白 ⇒ 这一屏不存在「空的录制器」",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `HotKeyRecorderButton.shortcut` didSet"),
    ("设置窗口/快捷键录制器", "错误", "not-applicable",
     "非法组合键**不在这一层说话**：它有唯一出口 `onInvalidShortcut`，回执由上层（提示条那一族）负责。"
     "在这层再画一次红会把同一句话讲两遍，而 VoiceOver 会读到两条同样的失败",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 的 `var onInvalidShortcut: (() -> Void)?`；账本 BACKLOG 58 那一族"),
    ("设置窗口/快捷键录制器", "聚焦", "not-applicable",
     "它是真 `NSButton`，焦点环由系统画；这层没有任何自定义 focus 代码（`focus` / `Focus` 实测 0 处）。"
     "自己再叠一圈会出现两个当前（R20 在圆形图标按钮上抓过这种叠层）",
     "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift 缺席:Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift=focus,Focus；账本 R20"),
    ("浮层/搜索框", "按下", "not-applicable",
     "按下去就是系统插入点（那是一枚 `NSTextField`，`placeholderString = \"搜索历史记录…\"`）。"
     "再叠一层按压底色会把「我在编辑」说成「我是按钮」",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `field.placeholderString`"),
    ("浮层/搜索框", "选中", "not-applicable",
     "文本框的「选中」是插入点与选区，作者是 NSTextField；这层没有可延续的 selection 语义，"
     "也不该有 —— 浮层里被选中的是**行**，说那句话的地方是「浮层/列表行 × 选中」",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift（field 是 NSTextField）"),
    ("浮层/搜索框", "空", "not-applicable",
     "空输入不是空态：它显示 placeholder。「没有结果」那一句由「浮层/空态 × 空」那一格承担（R7 / 审计 B-P2）",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `emptyLabel`"),
    ("浮层/搜索框", "加载", "not-applicable",
     "过滤是对内存里那份历史同步做：`QuickPickModel.swift` 里 `Task {` / `async` / `await` / `ProgressView` 实测各 0 处"
     "⇒ 没有「读一半」可演；采集路径不许有同步磁盘写那条红线也正是要这里不出现转圈",
     "Sources/ClipboardHistoryApp/Utilities/QuickPickModel.swift 缺席:Sources/ClipboardHistoryApp/Utilities/QuickPickModel.swift=ProgressView,isLoading"),
    ("浮层/列表行", "加载", "not-applicable",
     "表格数据是面板打开即有的那份历史（`QuickPickController.swift` 无 `ProgressView` / `isLoading`，实测 0）"
     "⇒ 这一格以前被当成「没做」，其实是「没有这一态」",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=ProgressView,isLoading"),
    ("浮层/空态", "悬停", "not-applicable",
     "那一句是 `NSTextField(labelWithString:)`：不是控件、不可点、不进焦点环。"
     "给它悬停反馈会造出一个「点不动却有反应」的目标（R39 那一族的反面）",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `let empty = NSTextField(labelWithString: \"\")`"),
    ("浮层/空态", "按下", "not-applicable",
     "同「悬停」那条的同一事实：标签没有可按压的东西。这里刻意**不引用文件级缺席**当理由 —— "
     "用的是这一行声明的对象身份（它不是 NSButton）",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `empty` 构造行"),
    ("浮层/空态", "聚焦", "not-applicable",
     "标签不进 key-view 环；浮层里唯一该拿焦点的是搜索框（面板一出现就是第一响应者）。"
     "让空态可聚焦会把 Tab 引到一句没有动作的话上",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=becomesKeyOnly"),
    ("浮层/空态", "禁用", "not-applicable",
     "没有「被禁用的空态」：它的有无由结果集决定（`empty.isHidden`），**隐藏比禁用诚实** —— "
     "一句没有结果的话不该以灰掉的方式留在原地",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的 `empty.isHidden = true`"),
    # R166（第 168 轮）一批：热图剩余三格 + 菜单栏两族。每条都带 `缺席:` 例子（会被
    # `scripts/ledger_absence_claims.py` 逐条复查），关键字计数是本轮逐个 grep 出来的，不是合并计数。
    ("设置窗口/热图", "按下", "not-applicable",
     "格子只回答「哪天多少条」，没有可点击的东西：整份文件里 `Button` / `TapGesture` 实测各 0 处。"
     "要让它可点，先要回答「点一下发生什么」—— 目前没有那个动作",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=Button,TapGesture"),
    ("设置窗口/热图", "成功", "not-applicable",
     "没有动作就没有「成功」回执。这一屏唯一的反馈是 hover 那一格（描边 + 日期与条数的 tooltip），"
     "它已经把「你指到的是哪天」说完；再加一层成功态就是把统计读出当成按钮",
     "docs/motion_surface_ledger.json 的「设置窗口/热图 × 悬停」；Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 的 `.helpLabel`"),
    ("设置窗口/热图", "禁用", "not-applicable",
     "没有可禁用的东西（`disabled` 实测 0 处、`selection` 0 处）。零记录那一屏是「空」不是「禁用」，"
     "已由「热图 × 空」那格承担（那是一句成句的话，不是一张空日历）",
     "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift 缺席:Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift=disabled,selection"),
    ("菜单栏/状态图标", "加载", "not-applicable",
     "那颗图标由系统状态栏绘制，这一层没有任何动画或转圈通道（`withAnimation` / `animation` / `transition` 实测各 0 处）。"
     "推荐是在打开菜单那一刻算的（`onAppear` 里一次），图标不参与等待",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=withAnimation,transition"),
    ("菜单栏/状态图标", "成功", "not-applicable",
     "复制成功的回执不在这颗图标上：走主窗口提示条与菜单项文案。让状态栏图标闪一下是把系统区域当通知中心用",
     "docs/motion_surface_ledger.json 的「主窗口/提示条 × 成功」；Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=withAnimation"),
    ("菜单栏/状态图标", "禁用", "not-applicable",
     "图标没有「禁用」这条分支（`disabled` 实测 0 处）：它要么在，要么整个 App 不在。"
     "灰掉一颗只能点开菜单的图标，等于做一个点不动的目标（R39 那一族）",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=disabled"),
    ("菜单栏/状态图标", "空", "not-applicable",
     "图标自己不承载内容，因此不存在「空的图标」；没有推荐时是菜单里回落到「暂无推荐」那一行（见「推荐面板 × 空」的分支）",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift；docs/motion_surface_ledger.json 的「菜单栏/推荐面板」各行"),
    ("菜单栏/状态图标", "错误", "not-applicable",
     "这一层没有错误通道：写盘 / 读档 / 剪贴板写入失败都由主窗口提示条与详情区说话（BACKLOG 58 那一族）。"
     "把状态栏图标变成红色警报器，是把一条回执装在系统区域",
     "docs/motion_surface_ledger.json 的「主窗口/提示条 × 错误」；账本 BACKLOG 58"),
    ("菜单栏/状态菜单", "按下", "not-applicable",
     "这层是真 NSMenu：按下的高亮由系统画，SwiftUI 的 `.pressedStyle` 在那一层根本不执行"
     "（该文件 `onHover` / `transition` 实测各 0 处 —— 不是漏做，是这层没有可挂的地方）",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=onHover,transition"),
    ("菜单栏/状态菜单", "选中", "not-applicable",
     "菜单项没有「选中」语义：只有常态与系统画的悬停高亮。给菜单项加选中态会造出两个当前"
     "（与「状态图标 × 选中」同一族，那格已判）",
     "docs/motion_surface_ledger.json 的「菜单栏/状态图标 × 选中」；Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 NSMenuItem 用法"),
    ("菜单栏/状态菜单", "聚焦", "not-applicable",
     "键盘在 NSMenu 里走系统的高亮与方向键，不经过 SwiftUI 的焦点环；这层没有任何 focus 代码"
     "（`onHover` / `animation` 实测 0 处）",
     "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 缺席:Sources/ClipboardHistoryApp/Managers/MenuBarController.swift=animation,onHover"),
    ("菜单栏/推荐面板", "按下", "not-applicable",
     "与「状态菜单 × 按下」同一个机制：`MenuBarExtraStyle.menu` 编译成真 NSMenu，"
     "SwiftUI 的按压样式与过渡在那一层不执行；叠一层自绘底会把 U-1 拆掉的卡片感装回来",
     "docs/motion_surface_ledger.json 的「菜单栏/推荐面板 × 悬停」；Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift 的 `.buttonStyle(.plain)` 注释"),
    ("菜单栏/推荐面板", "选中", "not-applicable",
     "推荐项被点就是「复制并关闭」，没有停留的选中态；再画一层选中会把一次动作说成一个状态",
     "docs/motion_surface_ledger.json 的「菜单栏/推荐面板 × 成功」；账本 U-1"),
    ("主窗口/列表行", "空", "not-applicable",
     "R181 看图 + 读源码：列表为空时**没有行**这一层可言 —— 空态由 EmptyStateView 承载"
     "（左栏那句「暂无剪贴板历史」+ 右栏「选择一条记录查看详情」，帧 content-empty-750x560 两档都读得通），"
     "给一个不存在的行做空态等于把空态画两遍",
     "缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=EmptyStateView｜Sources/ClipboardHistoryApp/Views/EmptyStateView.swift｜Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 Fixture(「content-empty」, 750×560)"),
    ("主窗口/列表行", "错误", "not-applicable",
     "行不承载错误：写盘 / 粘贴失败走 NoticeBanner（ContentView 四处调用，tone .warning / .error），"
     "而行文件里 failure / errorText 各 0 命中 ⇒ 这一格无所附；错误态已按提示条那一表面逐格判过",
     "缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=failure｜缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=errorText｜Sources/ClipboardHistoryApp/Views/ContentView.swift"),
    ("主窗口/列表行", "成功", "not-applicable",
     "「已复制」回执只该有一处，而它已经长在详情区那颗按钮上（1.1 秒的勾 + VoiceOver 播报）；"
     "ReceiptLine 在产品源码里只被 SettingsView 用（三处）⇒ 行上再放一份会让两条回执互相追旧，"
     "详情区那句注释『上一条留下的回执必须收掉，否则挂在另一条记录上就是说谎』讲的正是这个风险",
     "缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=ReceiptLine｜Sources/ClipboardHistoryApp/Views/DetailView.swift｜Sources/ClipboardHistoryApp/Views/GlassControls.swift"),
    ("主窗口/列表行", "禁用", "not-applicable",
     "行没有可禁用态：整份行文件里 disabled / isEnabled / allowsHitTesting 各 0 命中（R181 grep 实测）；"
     "行内会被禁用的只有收藏与图钉那两颗控件，它们已按自己的表面逐格判过",
     "缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=disabled｜缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=isEnabled｜缺席:ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift=allowsHitTesting"),
    # ===== R203 批次（拖入落点 6 格 + 提示条 4 格；看图腿：notice-banner-560x170 两条横幅的动作位都垂直居中）=====
    ("主窗口/拖入落点", "空", "kept",
     "落点那一圈挂在 List 本体上而不是挂在行上：空列表时同一圈虚线框照样出现（空态只是列表里的内容），所以不需要为它另加一句话。"
     "口径如实分开写：这一格是读码 + 结构得到的，本轮没有「空列表 + 正在拖入」的帧，像素未验。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 `.overlay { if isDropTargeted ... }`（挂在 List 之后）"),
    ("主窗口/拖入落点", "加载", "not-applicable",
     "落点没有加载态：`loadItem` 是异步的，但那段时间描边已经在位；再叠一层进度会把「松手就在这里」这一句稀释成两句。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 acceptDroppedFileProviders / fileURLs(withCheckedContinuation)"),
    ("主窗口/拖入落点", "错误", "not-added",
     "类型不符时 `guard !wanted.isEmpty else { return false }` ⇒ 由系统画禁投光标，应用内不补话。"
     "这一格与批次 D-4 修的那个洞只隔一步：D-4 补的是「接住了但什么都没发生」，而「根本没接住」今天只有光标。"
     "翻面条件写在 BACKLOG 224：若分辨实验表明确实区分不了，就要就地补一句回执。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 acceptDroppedFileProviders；BACKLOG 224"),
    ("主窗口/拖入落点", "成功", "kept",
     "入库成功的回执就是「新行出现在列表里」本身：`_ = historyStore?.addDroppedFiles(urls:)` 刻意丢弃返回值，"
     "不再叠一条横幅 —— 刚松手的那一瞬间注意力在指针上，横幅会跟它争。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 acceptDroppedFileProviders 里那行 `_ = historyStore?.addDroppedFiles`"),
    ("主窗口/拖入落点", "选中", "not-applicable",
     "落点是整块面板描边（圆角 strokeBorder + 虚线），与「哪一行被选中」不是同一根轴，两者不互斥也不互相覆盖。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 VisualShape.rounded(VisualRadius.panel).strokeBorder"),
    ("主窗口/拖入落点", "禁用", "not-added",
     "暂停采集不禁拖入：拖入是用户显式动作，把落点灰掉会让「我正在放文件」这件事没有解释；"
     "该停的是自动轮询，那一半在采集侧已经有自己的开关语言。",
     "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift（该文件内 paused 0 命中，即落点与暂停开关无耦合）"),
    ("主窗口/提示条", "空", "not-applicable",
     "横幅只在有话说时存在：`message` 是非空 String 入参，没有「空横幅」这个状态；空态那一格归 EmptyStateView。",
     "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift 的 struct NoticeBanner 入参 message: String"),
    ("主窗口/提示条", "加载", "not-applicable",
     "NoticeTone 只有 warning / error 两例，没有进度语义；加载由骨架屏那条通道承担，不在横幅里画转圈。",
     "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift 的 enum NoticeTone；Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift"),
    ("主窗口/提示条", "悬停", "not-added",
     "横幅本体不可点，能点的只有动作位；悬停那一格归 StateLine 的按钮，在横幅这层再画一遍就是两层反馈打架。",
     "Sources/ClipboardHistoryApp/Utilities/StatePresentation.swift 的 struct StateLine（action 路径今天只有 NoticeBanner 在用）"),
    ("主窗口/提示条", "按下", "kept",
     "动作位走 StateLine 的按钮，按下态由 PressableStyle 统一；R25 那一改把按钮从「跟第一行基线」换成「相对整组垂直居中」，"
     "本轮看 notice-banner-560x170 两张帧复核：单行与三行那两条横幅的动作按钮都在色带中心（当年量出的偏差是两行 7.5pt、三行 14.5pt）。",
     "Sources/ClipboardHistoryApp/Utilities/StatePresentation.swift 的 StateLine body 注释（R25 / U-47 / D-084）；Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 Fixture(「notice-banner」, 560×170)（帧只在本机 /tmp，未入库）"),
    ('主窗口/筛选条', '空', 'kept',
     '列表为空时药丸与轨道整段照旧可点，空态那句话由 EmptyStateView 那一支承载（还带「清除搜索」那颗动作位），筛选条不额外说一句 ⇒ 保留现状。两个空要分开：filteredEntries 为空是「筛完没结果」，entries 为空是「整库空」，同一帧两档都读得通。',
     'Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 第 32 行的 if historyStore.filteredEntries.isEmpty 与第 153 行的 entries.isEmpty 那一支｜Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 Fixture(「content-empty」, 750×560)'),
    ('主窗口/筛选条', '加载', 'not-added',
     '骨架屏加载时不遮蔽筛选条，条上也没有进度表达；决定不加脉冲或转圈 —— 「当前筛的是哪一段」与「正在加载」是两种语言，叠在同一颗胶囊上会让人以为筛选本身在算。加载那一格归骨架屏自己那表面（R26 已判）。',
     '缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=isLoading｜缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=showSkeleton｜Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift｜Tests/ClipboardHistoryAppTests/FilterPillMotionTests.swift'),
    ('主窗口/筛选条', '错误', 'not-applicable',
     '筛选是纯本地谓词：没有 IO、没有异步，也就没有「筛选失败」这条通道；写盘与粘贴那类失败走 NoticeBanner，而它不在侧栏这个文件里（该文件 NoticeBanner 0 命中）。',
     '缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=NoticeBanner｜缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=errorText｜Sources/ClipboardHistoryApp/Views/FilterPillGeometry.swift 的 segmentIndex 与 pillRect（纯函数、无抛出）'),
    ('主窗口/筛选条', '成功', 'kept',
     '切换成功的回执就是药丸滑到那一段 + 列表内容变化，不叠横幅也不加勾。两态像素判据把这件事钉成能复查的读数：亮区必须落在**选中**那一段，两档都量（R189/R190 那批）。',
     'Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 slidingPill 与 FilterPillMotion.slideAnimation｜Tests/ClipboardHistoryAppTests/FilterPillGeometryTests.swift 的 testFilterPillBrightBandFollowsTheSelectedSegment｜Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 r189-pill-all 与 r189-pill-fav（第 11070、11071 行那对夹具）'),
    ('主窗口/筛选条', '聚焦', 'kept',
     '这一格是**有意识地**「保留可聚焦、关掉系统焦点环」：sidebarFocusRingHidden() 在 macOS 14+ 调 focusEffectDisabled()，12/13 没有对应 API 所以环照旧画 —— 那是平台缺开关不是漏。判据数的是视野内的焦点环视图个数。不加自绘描边：R196 的结构读数显示同位置已有 _FocusRingView，再画一圈是两圈；键盘可达性那一半还欠一条要用户授权的实验（BACKLOG 220）。',
     'Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 fileprivate extension View 的 sidebarFocusRingHidden()｜Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift 的 class SidebarKeyboardNavigationTests（焦点环个数读数在第 1255、1269 行）｜Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift 的 testSidebarKeyViewChainStructureIsPrinted｜BACKLOG 220'),
    ('主窗口/筛选条', '禁用', 'not-applicable',
     '两段筛选永远可点：该文件里 isEnabled 0 命中；确有两条 .allowsHitTesting(false)（第 211、225 行）但它们在 SegmentedFilterPicker 之外（那个 enum 从第 359 行才开始），挂的是落点覆盖层。把「暂停采集」做成禁用胶囊会让用户以为筛选在算数据 —— 采集开关的语言在设置与菜单栏那边已经有了。',
     '缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=isEnabled｜Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 第 211、225 行的 .allowsHitTesting(false) 与第 359 行起的 SegmentedFilterPicker'),
    ('主窗口/详情区', '成功', 'kept',
     '「已复制」这条回执全 App 只有一处，而且长在详情区那颗复制按钮上：1.1 秒的勾 + VoiceOver 播报（M7）。换选一条时上一条的回执会被显式收掉，否则「已复制」挂在另一条记录上就是说谎。',
     'Sources/ClipboardHistoryApp/Views/DetailView.swift 第 19 行那条 M7 注释、第 93 行「上一条留下的回执必须收掉」、第 131 行 VoiceOverReceipt.announce、第 133 行 1.1 秒'),
    ('主窗口/详情区', '按下', 'kept',
     '详情区可点的只有两颗控件（「原文/渲染」那颗 chip 与卡片里那颗动作），两处都挂了 .pressedStyle；卡片那颗刻意 scales:false（它面积大，缩放会读成整块内容在抖），chip 那颗允许缩放。',
     'Sources/ClipboardHistoryApp/Views/DetailView.swift 第 246 行的 .pressedStyle(in: chip)｜Sources/ClipboardHistoryApp/Views/DetailView.swift 第 587 行的 .pressedStyle(in: card, scales: false)'),
    ('主窗口/详情区', '聚焦', 'kept',
     '详情区自己**不写任何焦点表达**：可聚焦的是那两颗 SwiftUI 按钮，环由系统画。这里不像侧栏那样关环 —— 侧栏关是因为它有一圈自绘的落点/选中表达会打架，详情区没有那个冲突，所以「什么都不加」才是正确的一格。',
     '缺席:Sources/ClipboardHistoryApp/Views/DetailView.swift=focusEffectDisabled｜缺席:Sources/ClipboardHistoryApp/Views/DetailView.swift=keyView｜Sources/ClipboardHistoryApp/Views/DetailView.swift 第 246、587 行那两颗带 .pressedStyle 的按钮'),
    ('主窗口/侧栏', '错误', 'not-applicable',
     '侧栏没有错误通道：它只做「列出 + 选中 + 搜索/筛选」，写盘与粘贴那类失败统一走提示条（在 ContentView 那层），而统计读不到账本那种错误长在设置正文（StateLine），不在侧栏。',
     '缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=NoticeBanner｜缺席:Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift=errorText｜Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 637 行的 StateLine(kind: .error) 那一支'),
    ('主窗口/侧栏', '按下', 'kept',
     '分两层判：行**本体**按下就是选中（List(selection:)），再叠一层按压底色会出现「按下的行」与「选中的行」两种底色；行内那两颗圆形控件（收藏/图钉）有自己的 .pressedStyle(in: Circle())，那一层保留。',
     'Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift 第 109 行的 .pressedStyle(in: Circle(), hoverLevel: controlHover)｜Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 List(selection:) 通道'),
    ('主窗口/侧栏', '聚焦', 'kept',
     '与「筛选条 × 聚焦」同一处置但**不是同一条代码**：侧栏这里是 sidebarFocusRingHidden()（macOS 14+ 关系统环、保留可聚焦），12/13 没有对应 API 所以环照旧画 = 平台缺开关不是漏。',
     'Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift 的 fileprivate extension View 的 sidebarFocusRingHidden()｜Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift 的 class SidebarKeyboardNavigationTests'),
    ('浮层/列表行', '成功', 'not-applicable',
     '浮层的「成功」就是面板关掉 + 主窗口去粘贴，那一层不留回执；而且没有候选时回车**什么都不该做**（不许提交上一条还在列表里的东西），所以这里没有「提交成功」这一格。',
     'Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 163 行「没有候选时回车什么都不该做」那一段'),
    ('浮层/列表行', '聚焦', 'kept',
     '键盘移动由模型的下标驱动表格自己的选中（selectRowIndexes + scrollRowToVisible），那一层不画第二重焦点表达 —— 浮层里唯一该拿键盘焦点的是搜索框（面板一出现就是第一响应者）。',
     'Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 333、334 行的 selectRowIndexes 与 scrollRowToVisible｜Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 787 行的 keyDown'),
    ('浮层/列表行', '禁用', 'not-applicable',
     '浮层的行没有可禁用态：能进列表的就是能选的，过滤在模型里做完了；真要「不能选」是「不该出现」，那种东西根本不该进这一层。',
     '缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=isEnabled｜Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 91 行的 model.setQuery（过滤在模型侧）'),
    ('浮层/搜索框', '错误', 'not-applicable',
     '查询无结果是「空」不是「错」：那一格由「浮层/空态 × 空」承担（一句成句的话，不是动画也不是红字）。',
     '缺席:Sources/ClipboardHistoryApp/Managers/QuickPickController.swift=errorText｜Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 208 行的 placeholderString'),
    ('浮层/搜索框', '成功', 'not-applicable',
     '搜索框没有「提交成功」这一态：输入即时过滤，提交那一步属于列表行那一格（回车选中并关闭）。',
     'Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 91 行的 if !query.isEmpty 那一支 setQuery｜BACKLOG 95'),
    ('菜单栏/状态菜单', '空', 'kept',
     '空态在系统菜单里的语言就是**一枚 disabled 的说明项**（「暂无历史」那一行），不是动画也不是骨架：菜单是即时弹层，任何常驻动效都会在每次打开时重播。',
     'Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 第 150 行的 emptyItem.isEnabled = false'),
    ('菜单栏/状态菜单', '禁用', 'kept',
     '这一层「不可点」的唯一表达就是 isEnabled=false：标题项与推荐理由项都显式禁（它们是信息不是动作）。再叠一层淡化会与系统自己的灰字重复，而 NSMenu 的淡化由系统画。',
     'Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 第 91 行的 titleItem.isEnabled = false｜Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 第 98 行的 headerItem.isEnabled = false'),
    ('设置窗口/侧栏', '错误', 'not-applicable',
     '设置侧栏只是导航，没有错误通道：错误长在分区正文里（统计读不到账本、存档写入失败各有一条自己的文本）。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 637 行的 StateLine(kind: .error)｜Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 1000、1003 行的 lastWriteError 文本'),
    ('设置窗口/侧栏', '成功', 'not-applicable',
     '侧栏不承载成功回执：导出/反馈那条成功长在正文（exportMessage 由 FeedbackExportReceipt.success 生成），在导航栏上再说一遍会让「我刚刚做了什么」看起来像「我在哪一页」。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 203 行的 FeedbackExportReceipt.success'),
    ('设置窗口/开关与滑块', '空', 'not-applicable',
     '开关不承载「空」：它是设置项，永远有值（Bool 或枚举），没有「还没有数据」这一格。真要说什么都不显示，那是整个分区不存在，而不是这一颗开关空着。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 354、374、387 行那三枚 Toggle（同一形状：标签 + isOn 绑定）'),
    ('设置窗口/开关与滑块', '加载', 'not-applicable',
     '设置页的值都是打开时同步从 store / UserDefaults 读的，没有「读一半」的中间态；唯一会慢的那一步（开机启动项向系统注册）也是**结果**说话（失败写 exportMessage / StateLine），不画转圈。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 354 行 Toggle 与紧邻的 .disabled(!loginItemSettings.isSupported)（第 355 行）｜BACKLOG 38'),
    ('设置窗口/开关与滑块', '错误', 'not-applicable',
     '开关本身不报错：错误来自它触发的动作（注册登录项、导出、清空），而那些各有一条自己的文本通道，不在开关身上再画一遍。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 1098 行那枚 StateLine 的 .helpLabel("收起这条提示") 路径｜缺席:Sources/ClipboardHistoryApp/Views/SettingsView.swift=errorText'),
    ('设置窗口/开关与滑块', '成功', 'not-added',
     '切换成功的回执**就是开关自己滑到新位置**（系统 Toggle 自带那一下），再叠一条横幅会把「我刚改了哪个设置」说两遍；这一档与「详情区 × 按下」同一族判断：控件自己已经把状态说完了。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 374 行的 recordingPaused 绑定（切换即生效，无异步）｜Sources/ClipboardHistoryApp/Views/GlassControls.swift 的 .pressedStyle 家族（可点控件的反馈统一在那一层）'),
    ('设置窗口/开关与滑块', '聚焦', 'kept',
     '这层的焦点环由系统画，产品没有关它也没有自绘：设置页是**要能用 Tab 走的一页**，而侧栏那种关环理由（旁边有一圈自绘的落点/选中表达会打架）在这里不成立。',
     '缺席:Sources/ClipboardHistoryApp/Views/SettingsView.swift=focusEffectDisabled｜Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 354、374、387 行那三枚 Toggle'),
    ('设置窗口/说明段', '加载', 'not-applicable',
     '说明段是静态文字（11pt caption），没有「正在加载的说明」：它解释的那颗控件有没有值都不改变这句话本身。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 8~15 行那段关于「说明段离它解释的开关更近」的注释与判据名'),
    ('设置窗口/说明段', '成功', 'not-applicable',
     '说明段不承载回执：成功/失败由 StateLine 与 exportMessage 那条通道说，说明段只是解释「这个开关会改变什么」。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 203 行的 FeedbackExportReceipt.success 那条通道｜BACKLOG 58'),
    ('设置窗口/说明段', '选中', 'not-applicable',
     '说明段不可选、不可点：它是被读的文字。给它做选中态会让一段解释读起来像一项可操作的设置。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 795 行那段注释：说明文字的可发现性靠「看得见」，并把 .help() 折进悬停提示'),
    ('设置窗口/说明段', '聚焦', 'not-applicable',
     '文字不进 key-view 环（能聚焦的是它上面那颗开关）；让说明段可聚焦会把 Tab 引到读不动的东西上。',
     '缺席:Sources/ClipboardHistoryApp/Views/SettingsView.swift=focusEffectDisabled｜Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 8~15 行那段说明段间距的判据注释'),
    ('设置窗口/说明段', '禁用', 'not-added',
     '说明段不跟着它所解释的开关一起淡：开关被禁用（例如这台机器不支持登录项）时，**那句解释恰恰最需要被读到** —— 用户要的是「为什么这颗点不动」。',
     'Sources/ClipboardHistoryApp/Views/SettingsView.swift 第 355 行的 .disabled(!loginItemSettings.isSupported)（开关被禁而说明文字保持原档）'),
    ('菜单栏/推荐面板', '空', 'kept',
     '空态在代码里就是一个显式的 isEmpty 分支（没有推荐就不建那一节），而不是把空列表画出来；这与「状态菜单 × 空」同一族：菜单是即时弹层，没有骨架也没有动画。',
     'Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift 第 14 行的 if historyStore.predictionSuggestionEntries.isEmpty'),
    ('菜单栏/推荐面板', '错误', 'not-applicable',
     '推荐面板没有错误通道：算不出推荐就是「没有推荐」（走上面那一格），而真正会失败的那一步（写剪贴板）由主窗口提示条说话。',
     'Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift 第 14 行的 isEmpty 分支｜缺席:Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift=errorText'),
    ('菜单栏/推荐面板', '聚焦', 'not-applicable',
     '这一层是 NSMenu 里的行，键盘走系统的菜单高亮，不经过 SwiftUI 的焦点环；这一族在「状态菜单 × 聚焦」那格已经量过（该文件 onHover / animation 0 处）。',
     'Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 NSMenuItem 用法（推荐项是 menu item，不是 SwiftUI 视图）｜BACKLOG 220'),
    ('菜单栏/推荐面板', '禁用', 'kept',
     '面板里「不可点」的东西（标题与分组头）都显式 isEnabled=false，这是系统菜单里唯一的禁用语言；再叠一层淡化会与系统自己的灰字重复。',
     'Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 第 91 行的 titleItem.isEnabled = false｜Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 第 98 行的 headerItem.isEnabled = false'),
    ('浮层/空态', '成功', 'not-applicable',
     '空态是「没有结果」这句话本身，它不承载成功：真正的成功是选中某一行并关掉面板，而那一格归「浮层/列表行 × 成功」（那里判过：不留回执）。',
     'Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 243 行的 NSTextField(labelWithString:) 空态标签'),
    ('浮层/空态', '选中', 'not-applicable',
     '标签不进 key-view 环、不可点：浮层里唯一该拿焦点的是搜索框。给一句「没有结果」做选中态，等于把键盘引到一个没有动作的地方。',
     'Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 第 243、246、247、248、249 行那枚标签的声明（labelWithString + secondaryLabelColor + 居中 + 截尾）'),
]


data = {
    "_comment": [
        "动效与视觉的**按表面清账**表（R127 建 / R128 补强；阶段二的收尾判据）。",
        "为什么要有它：目标要求「每一个元素/文字段/可动部件都要重新判断加动效是否有积极作用，",
        "有作用才加，无作用或有害就写明理由不加」。127 轮下来这些判断散在 AGENT_UI_AUDIT 各轮正文里,",
        "没人能回答「哪个表面、哪个状态还没判过」。这张表把答案变成数据：一格一个 verdict + 一条理由 + 一个证据指针。",
        "**没覆盖的格子是显式记账的**（`MOTION_LEDGER 未清账=k`），不许靠删行或留白把它变小；",
        "地板取「已清账格子数」，只准升不准降（与 `testHistoryStoreStaysThin` 同一族：会红的必须是单调量）。",
        "`not-measured` **不算已清账** —— 它是一格占了位置的空白，写它只是为了让名册扩张立刻可见。",
        "证据指针的形状（U-424）：必须至少含一个可复查对象（源码文件 / Tests 文件 / docs 路径 /",
        "scripts 路径 / BACKLOG 号 / D-号 / 批次号）。轮次号可以附带但不能是唯一内容 ——",
        "「R14 说过」不复查得了，「Sources/.../HistoryRowViews.swift 里那一行」复查得了。",
        "verdict 词表：added=之前没有、后来加了；kept=本来就有、判过之后保留；",
        "not-added=判过且决定不加（必须给理由）；not-applicable=这一格没有那个状态（也要说为什么）；",
        "not-measured=还没判过 —— 占位用，计入未清账。",
    ],
    "verdicts": ["added", "kept", "not-added", "not-applicable", "not-measured"],
    "cleared_verdicts": ["added", "kept", "not-added", "not-applicable"],
    "surfaces": surfaces,
    "retired_surfaces": retired_surfaces,
    "states": states,
    "rows": [{"surface": a, "state": b, "verdict": c, "reason": d, "evidence": e}
             for (a, b, c, d, e) in rows],
    "floor_cleared": len([r for r in rows if r[2] != "not-measured"]),
}

io.open("docs/motion_surface_ledger.json", "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n")
cleared = data["floor_cleared"]
print("MOTION_LEDGER_ROWS=%d 已清账=%d 未清账=%d 格子=%d"
      % (len(rows), cleared, len(surfaces) * len(states) - cleared, len(surfaces) * len(states)))
