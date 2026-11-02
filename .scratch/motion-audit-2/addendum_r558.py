# -*- coding: utf-8 -*-
"""R558 补记：本轮成对号（含 runner 已签的因果对照）与 R559 的 ⓪ 读单。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R558 补记（2026-11-03 · 第 557 轮 / Round 555 · 成对号 + R559 读单）

① **本轮成对号（一次性 push 的自证）**：⓪ 笔 `2f85c5d` 的跑 = **`41469418563` conclusion=success**（已在 U-2387 收口前补读里逐条抄过：STEP[9] 绿、STEP[15]–[19] 全 success）⇒ 这一笔是纯台账、账上 sources 格与 git 一致，**不是**注定红的中间跑。A 笔 `b8949f5`（判据 + 观察者 + 四把刀）与台账笔 `1ea1bb7` 与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间两笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成"没红"。本补记笔自己的跑取号时尚不存在 ⇒ 具名 NOT-RUN，R559 现读。
② **因果对照已被 runner 签死**（这一格是 634 的外部证据，不是我的推断）：账上格与 git 一致的三跑 `41465486002↔5d05578`、`41467173705↔61285b6`、`41469418563↔2f85c5d` **全 success**；格不一致的那跑 `41464892684↔ce4da8f` **failure 且只红 STEP[9]**。⇒ R557 记的「分批 push 造出注定红的中间跑」与 634 记的「`test_skip_roster` 的红是从 sources-cell 借来的」两条同时成立。**本轮起：验证链跑完一次性 push，不分批。**
③ **R559 的 ⓪ 必读**（逐条抄全部失败步骤；`ci_read.py steps` 只列 failure/skipped，success 步骤另用 `gh run view --json jobs` 读 conclusion）：
- 本轮 push 的头笔（= 本补记笔）那一跑，以及 `1ea1bb7`/`b8949f5` 若各自建跑也要读；取号时未创建 ⇒ 具名 NOT-RUN。
- `41467585182 ↔ ff15906`（R557 补记第二笔）已到手 failure，红在 STEP[18]（622 第十三值 225.3ms/3 颗）+ STEP[19]（629 未登记红）⇒ 两朵都是既有红，本轮未碰那两卷，已按同族入账；R559 只需复核新口径上线后 STEP[19] 还在不在。
- **头一格 = 新口径在 runner 上读几**：`MOTION_MARKDOWN_MODE_FADE … 过渡帧数=`（现在是两端夹逼的数）+ `相邻差帧数=`（旧口径，一起打印）。runner 上旧口径第四值 = `41467585182` 读 **1**（每格 29.1ms、只 1 格非零）⇒ 那一朵红本身还在；⚠ **旧口径那一行推不出新口径会读几**（新尺要连续距离，旧行只有阈值占比）⇒ 不许拿它当"新尺也会红"或"新尺会绿"的证据，只能由含新尺那一笔的跑作证。
- 第二格 = **635**：`MarkdownModeButton` 的 `.id(title)`/`.transition(.opacity)`/`.animation(value:)` 三行分别摘与全摘，本机胶片读数逐字不变（四臂探针 `probe_r558_what_the_film_measures.py`，本轮已入库 ⇒ 可重跑），且全仓没有 grep 守卫钉它们 ⇒ 要么补一条会红的钉子，要么降级成具名不判，两条都要配证人。
- 第三格 = 634 的 runner 复核：拆完之后 STEP[9] 的 `test_skip_roster` 还红不红（本机已 live 演示 inner-red 路径：注入一个临时失败再删，正文带内层汇总行与红名；`no-summary` 那一格只有真值表级证人，没有 live 演示）。
④ **口径不变**：633 仍等用户人工回执（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）；622 追加第十三值；624/627/635 继续；628/625/626/569/616/632 已落地那半不重开；禁碰清单 9 面不变；刀号 **M1450** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板一律不动；`.contentFade` 0.20 与声明时长一字未改。
⑤ **本轮现读（收口时）**：build 告警 0；判据卷 217/4 skipped/0（781.0s）；帧 354 CHANGED=0 MISSING=0 ADDED=0（基线 json 未动 ⇒ 真 0，无须 update）；全量 **1400/57/0（748.1s）** —— skipped 从前一轮的 55 变 57，去重名单差恰好两格：`UICaptureTests/testCaptureKeyViews` 与 `OffscreenSymbolInkProbeTests/testProductSettingsSidebarIconInk`（都是条件 skip，本轮没碰这两个文件 ⇒ 只记现读不猜成因，下一轮再读一次看是否稳定）；预检 tables=349 covered=295 arms=757 bad=0、`ARM_TOTAL files=442 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=436 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`；换装 `INSTALL_SIGNATURE=local`（Authority=ClipboardHistory Local Signing）⇒ `INSTALL_RESULT=ok / SHA_MATCH=1 / ENTRIES=433=433 / SMOKE_OK=1`（PID→92658，备份 before-R558）；电池 **Ran 696 / OK (skipped=5)**（台账与 sources 格之后复跑）；清账 162/63/0；streak 1（as-of 557，`--streak-for 557` 现读，last=`2ca9501`/556）；sources 格 `账上=R557/2ca9501 git=R557/2ca9501 一致=是`。

"""


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = u"2x 8.0pt 与 1x 6.0pt 均不动。\n## R558 ⓪ 开工"
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    if not check:
        new = (u"2x 8.0pt 与 1x 6.0pt 均不动。\n" + BLOCK.strip(u"\n") + u"\n\n## R558 ⓪ 开工")
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R558_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
