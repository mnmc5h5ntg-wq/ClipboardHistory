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
    "菜单栏/推荐面板", "浮层/列表行", "浮层/搜索框", "浮层/空态", "浮层/底部说明",
]
states = ["空", "加载", "错误", "成功", "选中", "悬停", "按下", "聚焦", "禁用"]

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
     "Sources/ClipboardHistoryApp/ContentView.swift 的 `.transition(bannerIn)`；R42/R43"),
    ("主窗口/提示条", "错误", "added",
     "复制失败走同一条淡入但换文案与配色；不给它动效会让失败读成「什么都没发生」",
     "Sources/ClipboardHistoryApp/ContentView.swift；BACKLOG 58/59（R40/R41）"),
    # 曾经在这里写过一行「主窗口/提示条 × 消失」，被闸门以 `UNKNOWN_CELL` 拦下：
    # 「消失」不在这九个状态里 —— 它是一次转换，不是一个状态。留着这行注释是为了记下
    # **闸门拦住了我自己造的词**（R128），而 `bannerOut` 那条事实挂在上面两行的指针里。
    ("主窗口/提示条", "选中", "not-applicable",
     "提示条没有「被选中」这一态；记 not-applicable 是为了让它不再被当成没做",
     "docs/motion_surface_ledger.json 的 verdict 词表第 4 项"),
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
    ("浮层/底部说明", "悬停", "not-added",
     "底部那一行讲的是键位，响应鼠标会把注意力从列表行引开；判过之后决定不加",
     "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift 的底部说明段（R64 位点逐个判）"),
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
