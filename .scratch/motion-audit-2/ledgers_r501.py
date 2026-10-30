#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 498 轮续一（R499 续"
AS=u"""## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）：判据推进：录制帧重复渲染确定性（无产品变更，不记完成）

- **U-1964：⓪ push 与 CI。** 开工 `git push` no-op（Everything up-to-date）、HEAD=origin/main=`817a014`、**ahead=0**。成对读数：`41062934158 ↔ 79eb4fb` 读时 **in_progress ⇒ NOT-RUN**；`41063726929 ↔ 817a014` 读时 **in_progress ⇒ NOT-RUN**；`41057812582 ↔ 4963281` failure 仅 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条采样 flake（同跑 15.8 键登记 0、录制帧 12/11）；`41058094730 ↔ eae195b` success（1314/81/0，同读数）；`41051398635 ↔ d87d258` failure 仅 15.8 UNKEYED（已修）；`40941281838 ↔ c9d8d6c` failure 仅 Capture（30/0，同跑后读 12/11）。436 沿用 R481 跑 reds=0。
- **U-1965：② 产品位复核。** 597（放大项目符号+行高钳制）三次实测仍不成立（`natural` −2px / `natural+lineSpacing` 行距放大 / `natural+lineSpacing/2` 后续 +4px）；其余候选均为此前证伪或已完成类别；本轮**无产品文件**。
- **U-1966：③ 判据推进（会变读数）。** 新判据 `testRecordingCardFrameIsDeterministicAcrossRenders`：同一录制夹具**两次渲染逐字节比对**，并数墨作内容证人。读数：`RECORDING_REREAD` light **diff_px=0 墨=49162**、dark **diff_px=0 墨=57774**（2x）。空帧 ⇒ `RECORDING_REREAD_NOT_RUN=settings-content-blank`。刀 `M1345`（第二次渲染换非录制帧）/`M1346`（第二次渲染换另一外观）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`；它把 R499 那次 30/0 的相位 flake 从“同跑另一读掩盖”变成 `diff_px>0` 的具名红。
- **U-1967：④ 帧卷。** 捕获卷 **330 帧**、`COMPARED=330` 但 **89 张 changed**：逐张核对差异都是**源 App 图标栅格噪声**（例如 `content-min-600x440-light` diff bbox 16×16px、最大通道差 7/255），与产品改动无关 ⇒ **不吸收进基线**（`FRAME_BASELINE_ENV_NOISE=source-icon-raster`，基线保持 330 旧哈希）；下一轮若仍出现，先在 `frame_baseline` 里排除源图标区或另立噪声通道，不静默 update。
- **U-1968：⑤ 预检与门。** `NEEDLE_PRECHECK tables=280 covered=257 arms=688 bad=0`（新表 `mutate_r501_recording_reread` 登记）、`ARM_TOTAL files=373 arms=1175`、`HIDDEN_ARMS 表=367 可判=1114 rot=0`；build **0 告警**（arm64 冷编）；全量 **1315/56/0**（627.9s，轻载）；**无产品文件 ⇒ 不换装**（397 保持）；电池在台账后复跑。
- **U-1969：⑥ 结论。** 本轮为**判据推进**而非产品视觉推进：597 已三次证伪、无合法未捕获表面；按监督者“无产品位时至少落一条会变读数的判据”的口径记一条会红的确定性判据，**不记产品完成**；下一轮仍需换未捕获表面（真实窗口帧/新设计位）。

"""
DS=u"""## D-497 R501 判据推进：录制帧两次渲染必须逐字节一致（无产品变更，不记完成）

- 背景：R499 的 30/0 与 12/11 两读说明录制帧在 runner 上可能拍到未落定相位；597 的放大字形路线三次证伪，本轮无合法产品位。
- 决定：新增 `testRecordingCardFrameIsDeterministicAcrossRenders`（同一夹具两次渲染逐字节比对 + 墨证人 + NOT_RUN 出口），两把刀钉“换帧/换外观必红”；帧卷 89 张源图标栅格噪声**不吸收**进基线。
- 理由：把捕获相位问题变成会红的读数，比再写一条散文更接近根因；噪声哈希不 update，避免把环境噪声洗成产品基线。
- 边界：新判据的 runner 1x 读数待下一跑；源图标噪声若持续需在基线工具里立噪声通道。
"""
BS=u"""**601. 帧卷 89 张出现源 App 图标栅格噪声**（R501 现读）
    现象：无产品改动，330 帧里 89 张 changed，差异集中在 16×16px 的源图标区、最大通道差 7/255（例 `content-min-600x440-light`）。
    修法：先在 `scripts/frame_baseline.py` 立“源图标区排除/噪声通道”，或连续两跑同形再决定；**不许**直接 update 把噪声洗成基线。

**602. RECORDING_REREAD 的 runner 1x 读数未读**（R501 观察）
    现象：本机 2x diff_px=0、墨 49162/57774；R501 自身跑尚未创建（提交后取）。
    修法：下一跑读 `RECORDING_REREAD` 两档；若 1x diff>0，说明 runner 仍会拍到未落定相位，按帧定位。
"""
SS=u"""R501 记录（判据推进，无产品变更，不记完成）：⓪ push no-op（HEAD=origin/main=`817a014`、ahead=0）；`41062934158 ↔ 79eb4fb` 与 `41063726929 ↔ 817a014` 读时均 in_progress ⇒ NOT-RUN；`41057812582 ↔ 4963281` failure 仅 SelectionReveal 采样 flake（同跑 15.8 键登记 0、录制帧 12/11）、`41058094730 ↔ eae195b` success（1314/81/0）⇒ 前轮两修已签收。② 597 三次实测仍不成立、无合法未捕获表面 ⇒ 无产品文件。③ 判据推进：新 `testRecordingCardFrameIsDeterministicAcrossRenders`（同一录制夹具两次渲染逐字节比对）读数 `RECORDING_REREAD light diff_px=0 墨=49162 / dark diff_px=0 墨=57774`（2x），空帧具名 NOT_RUN；M1345/M1346 **2/2**、RESTORE_CLEAN=yes；它把 30/0 那类相位 flake 变成会红的 `diff_px>0`。④ 帧卷 330 帧、89 张 changed 均为**源 App 图标栅格噪声**（16×16px、最大差 7/255）⇒ **不吸收进基线**（`FRAME_BASELINE_ENV_NOISE=source-icon-raster`；601）。⑤ 预检 280/257/688 bad=0、ARM 373/1175、HIDDEN 367/1114 rot=0；build 0 告警；全量 **1315/56/0**；无产品文件 ⇒ 不换装；电池 683/OK skipped=5；清账 162/63/0。下一轮编号 R502（第 501 轮 / Round 499）：先 push 并复核 ahead=0；读 R501 自身跑（`RECORDING_REREAD` 1x/602）与 79eb4fb/817a014 跑；② 仍需未捕获表面的产品位；597 不再用放大字形；436 只复核新跑 Motion floor。
"""
RB=u"""- **R501（判据推进，无产品变更，不记完成）**：新 `testRecordingCardFrameIsDeterministicAcrossRenders`——同一录制夹具两次渲染逐字节比对，`RECORDING_REREAD` light diff=0/墨 49162、dark diff=0/墨 57774；M1345/M1346 2/2。597 放大字形三次证伪；帧卷 89 张变化均为源图标栅格噪声（16×16、差 7/255），不吸收进基线。⓪ push no-op、ahead=0；79eb4fb/817a014 跑 in_progress ⇒ NOT-RUN；4963281 跑唯一红=SelectionReveal 采样 flake、eae195b 跑 success。全量 1315/56/0；build 0 告警；无产品 ⇒ 不换装；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P)
if a.count(AT)!=1: raise SystemExit('A:'+str(a.count(AT)))
if u"## D-497" in d: raise SystemExit('D')
if u"**601." in b: raise SystemExit('B')
if u"R501 记录" in st: raise SystemExit('S')
if u"R501（判据推进" in pr: raise SystemExit('P')
wr(A,a.replace(AT,AS+AT,1)); wr(D,d.rstrip()+"\n\n"+DS+"\n"); wr(B,b.rstrip()+"\n\n"+BS+"\n")
wr(S,st.replace(u"## R498 状态",SS.strip()+"\n\n## R498 状态",1))
pr=pr.replace(u"U-31 … U-1963（R499 现读抬到最新一节）",u"U-31 … U-1969（R501 现读抬到最新一节）",1)
wr(P,pr.rstrip()+"\n\n"+RB+"\n"); print("OK")
