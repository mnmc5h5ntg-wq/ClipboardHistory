#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 `docs/motion_surface_ledger.json`（R127 的按表面清账表）。

为什么用脚本生成而不是手写 JSON：行数、`floor_rows`、格子总数这三格必须**算出来**，
手写就会抄错（U-264 那一族）。CJK 串里一律用「」，不用 ASCII 双引号 —— 那会同时打断
本文件与 JSON（这台机器上犯过多次）。
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
rows = [
    ("主窗口/列表行", "悬停", "kept",
     "0.12s 的底色 + 图标/次要文字 opacity 0.55→0.78；更快会读成闪烁，更慢跟不上鼠标",
     "R14 悬停取证通道 / R15 药丸几何与命中区（`HistoryRowViews.swift` 的 `.animation(for: .hover)`）"),
    ("主窗口/列表行", "按下", "added",
     "macOS 12 上 `.borderless` 那颗按下去原本没有任何反馈；`pressedStyle` 给一层不缩放的按压",
     "R4 按压态落地 / R13 三处 `.borderless` 归队 / R20 圆形图标按钮（`PressableStyle.swift`）"),
    ("主窗口/列表行", "选中", "kept",
     "选中靠系统强调色 + 把视口外的行滚进来；再给选中加动画会把「哪一行被选中」变成运动而不是状态",
     "R19 选中可见性 spike / R61 BACKLOG 61 修法（`SelectedRowRevealer.swift`）"),
    ("主窗口/详情区", "加载", "added",
     "spinner 说「我在等」，骨架说「内容马上来」；扫光是全仓唯一常驻时钟，30Hz、只在 `.loading` 分支存在、8s 上界",
     "R26 骨架第一次进帧基线 / R84 一整组一条亮带 / R85 覆盖率 0.522 对地板 0.50（`SkeletonShimmer.swift`）"),
    ("主窗口/详情区", "空", "kept",
     "空态与内容之间是 0.16s 交叉淡 —— 只有一臂的过渡等于没有，所以两臂都挂",
     "R16 详情区空↔内容交叉淡"),
    ("主窗口/提示条", "成功", "added",
     "回执行淡入 + `emphasis` 0.16s；「声明了动效却没供电」被抓到之后要么供电要么撤声明",
     "R42 ReceiptLine 淡入 / R43 导出两条回执通道"),
    ("主窗口/提示条", "错误", "added",
     "复制失败走同一条淡入但换文案与配色；不给它动效会让失败读成「什么都没发生」",
     "R40 写剪贴板失败三条入口静默 / R41 BACKLOG 58 回执要成人话"),
    ("主窗口/提示条", "选中", "not-applicable",
     "提示条没有「被选中」这一态；记 not-applicable 是为了让它不再被当成没做",
     "verdict 词表第 4 项"),
    ("主窗口/拖入落点", "悬停", "added",
     "拖入时整组一条亮带 + 落点框 0.12s；没有落点反馈时用户分不开「接住了」与「没接住」",
     "R40 拖入反馈 / R84 BACKLOG 117 整组一条亮带"),
    ("设置窗口/侧栏", "悬停", "kept",
     "与主窗口行同一档 0.12s；侧栏行是导航不是内容，动得比内容重会抢注意力",
     "`SettingsView.swift` 的 `.animation(for: .hover)`"),
    ("设置窗口/侧栏", "选中", "kept",
     "强调色药丸 + 图标与标签同色：两枚多色符号的 `.hierarchical` 换成 `.monochrome`，暗档 22 行黑底黑图标归 0",
     "R122 + 真机 `REALSCREEN_ICON_BAND 0..5` 六条全有墨（R123 / R126）"),
    ("设置窗口/热图", "悬停", "added",
     "格子描边一圈（`VisualHeat.hoverRingOpacity` 是有名字的数）+ 日期与当日条数的 hover 提示；事务挂在变更点上而不是下游 `.animation(value:)`",
     "R45 热图悬停那一圈描边第一次有帧"),
    ("设置窗口/开关与滑块", "禁用", "kept",
     "禁用态第一次有帧之前，那颗在 macOS 12 上永远点不动的开关连一张静帧都没有；这一格要的是可见性而不是动效",
     "R39 禁用态帧"),
    ("菜单栏/推荐面板", "加载", "not-added",
     "`MenuBarExtraStyle.menu` 编译成**真 NSMenu**，SwiftUI 的过渡在那一层根本不执行；在这里挂 `.transition` 等于给自己造一条永不生效的声明",
     "D-055 / M15 实测；R5 删过一条；R126 侦察时读到"),
    ("菜单栏/状态菜单", "成功", "kept",
     "复制成功的反馈走主窗口提示条与菜单项文案，不给 NSMenu 项加动画（同上一条：那层不执行 SwiftUI 过渡）",
     "R111 BACKLOG 165 菜单刷新落地"),
    ("浮层/列表行", "选中", "kept",
     "浮层选中是灰、侧栏选中是蓝 —— 同一台机器同一条离屏通道对两种控件给出两种颜色，所以这里不跟侧栏对齐，也不加动画",
     "R102 按控件回答（旧轴尺的 ≥40 门限在亮档刚好掉线）"),
    ("浮层/搜索框", "聚焦", "added",
     "焦点环：只读 alpha 的那把尺曾把「有环」读成「没环」，把 alpha 与亮度两轴都配上之后才有判据",
     "R76 焦点态 / R77 alpha 与亮度轴对照 / R78 反方向盲区"),
    ("浮层/空态", "空", "kept",
     "空态是一句成句的话而不是动画；给「没有结果」加动效会把注意力钉在空上",
     "R64 浮层剩余状态位点（`QUICKPICK_EMPTY_SENTENCE`）"),
]

data = {
    "_comment": [
        "动效与视觉的**按表面清账**表（R127 / 阶段二的收尾判据）。",
        "为什么要有它：目标要求「每一个元素/文字段/可动部件都要重新判断加动效是否有积极作用，",
        "有作用才加，无作用或有害就写明理由不加」。127 轮下来这些判断散在 AGENT_UI_AUDIT 各轮正文里，",
        "没人能回答「哪个表面、哪个状态还没判过」。这张表把答案变成数据：一格一个 verdict + 一条理由 + 一个证据指针。",
        "**没覆盖的格子是显式记账的**（`MOTION_LEDGER 未清账=k`），不许靠删行或留白把它变小；",
        "`floor_rows` 只准升不准降 —— 与 `testHistoryStoreStaysThin` 同一族：会红的必须是单调量，",
        "均值与区间都被证伪过。",
        "verdict 词表：added=之前没有、后来加了；kept=本来就有、判过之后保留；",
        "not-added=判过且决定不加（必须给理由）；not-applicable=这一格没有那个状态（也要说为什么）；",
        "not-measured=还没判过 —— 计入未清账，不算通过。",
    ],
    "verdicts": ["added", "kept", "not-added", "not-applicable", "not-measured"],
    "surfaces": surfaces,
    "states": states,
    "floor_rows": len(rows),
    "rows": [{"surface": a, "state": b, "verdict": c, "reason": d, "evidence": e}
             for (a, b, c, d, e) in rows],
}

io.open("docs/motion_surface_ledger.json", "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print("MOTION_LEDGER_ROWS=%d CELLS=%d SURFACES=%d STATES=%d"
      % (len(rows), len(surfaces) * len(states), len(surfaces), len(states)))
