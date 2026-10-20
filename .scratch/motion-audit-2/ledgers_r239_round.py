# R239 / 第 238 轮 / Round 236 台账：看图腿回来了（重捕 162 帧 + 两态差尺），产品 0 文件
import io, re, json
def rd(p): return io.open(p, encoding='utf-8').read()
ui_p='AGENT_UI_AUDIT.md'; it_p='AGENT_VISUAL_ITERATION.md'; de_p='AGENT_DECISIONS.md'
bl_p='AGENT_BACKLOG.md'; ch_p='CHANGELOG.md'; st_p='AGENT_STATE.md'; fr_p='AGENT_FINAL_REPORT.md'
ui=rd(ui_p); it=rd(it_p); de=rd(de_p); bl=rd(bl_p); ch=rd(ch_p); st=rd(st_p); fr=rd(fr_p)

SEC_UI = u'''## 第 238 轮（R239 / Round 236 · 2026-10-20）：看图腿回来了 —— 重捕 162 帧、给 251 的两处悬停位点配上「静置↔悬停」两态差读数，并当场量到自己那把临时尺的单位错（U-771…U-773）

- **U-771：帧通道恢复（连续几轮的看图腿都是 NOT-RUN，这一轮不是）。** `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_r239 swift test --filter UICaptureTests` ⇒ `CAPTURE_EXIT=0`、
  **162** 张帧（暗 81 / 亮 82）；`python3 scripts/frame_baseline.py check /tmp/shots_r239 --against working` ⇒
  `FRAME_BASELINE_COMPARED=162 CHANGED=0 MISSING=0 ADDED=0`（产品 0 文件，所以"没变"是预期，不是跳过）。
  本轮真的看了图：段按钮两档、玻璃圆钮两档共四张。
- **U-772：251 的两处位点第一次有「两态差」读数（临时尺，未进判据）。** 按帧名配对做逐像素差，不猜坐标：
  玻璃圆钮 `glass-pill-120x232` ↔ `glass-pill-hover-120x232` ⇒ 暗档变化带 (76,85,164,443)、Δ>4 像素 **21.1%**、带内均值比 **1.232:1**；亮档 **22.1%**、**1.078:1**。
  段按钮 `segmented-filter-idle-200x60` ↔ `segmented-filter-hover-200x60` ⇒ 暗档 19.7% / **1.179:1**；亮档 20.0% / **1.093:1**。
  两把对照都在：**负对照**（帧↔自身）= `Δ>4 的像素=0`；**正对照**（`modechip-hover-idle` ↔ `modechip-hover-lit`，已知有变化）= 暗 1.223:1 / 亮 1.143:1。
  ⇒ 亮档那两处（1.078 / 1.093）**落在正对照那条已知可分辨的带之下**，问题仍在；但**这一轮不许据此改产品**（见 U-773 的单位错）。
- **U-773：我第一版尺子量错了对象，且错法正是老账里那条。** 先按点坐标取样（把 120x232 当像素用），结果四个框全读到平涂背景
  （暗 30.0 / 亮 255.0，min==max）—— 帧是 **@2x**（240x464），坐标整套错位；换成"两态逐像素差 + 变化带"才读到东西。
  第二条单位错：这里的比值是**变化带内所有像素的均值**（含大量未变像素，被稀释），与 R231 那本账里"药丸 1.160:1"的**控件局部对比度**不是同一个估计量 ⇒
  **跨账对账前必须先统一估计量**，所以本轮只登记读数、不动 `VisualFill.hover` 的任何一档。
  另记一处显式缺席：251 的第三处（`DetailView.swift:609` 的 `VisualFill.hover`）**没有两态帧** —— `detail-*` 帧名里没有任何 hover/idle 对（数出来的，不是印象）。
  **未做**：① 这把尺没搬进 `scripts/`（下一轮：按"变化带 + 控件局部"两口径各出一版，配正/负对照与刀）；② M795/M796 仍未登记；
  ③ CI 未读（`RUN=39351035433 sha=6927880 status=in_progress conclusion=` 空）；④ 没跑全量 swift 卷（只跑了 `--filter UICaptureTests` 那一卷）。

'''
SEC_IT = u'''## Round 236 · 看图腿回来：两态差尺与它那一次量错对象（251 的两处读数 / D-225 / BACKLOG 272 · 产品 0 文件）

本轮次对照：与 R238 补记（那条修的是"守卫按形状漏读"）相比，本轮把欠了几轮的**真看图**还上了 —— 重捕 162 帧、逐帧看了悬停两处、并给 251 交出第一批两态差读数。
做了什么：`swift test --filter UICaptureTests` 重捕 → `frame_baseline check`（CHANGED=0）→ 两态逐像素差（含负对照=帧自身、正对照=modechip 已知变化）→ 六本台账。
看图腿：**RUN**（162 帧，暗 81 / 亮 82；看了 4 张：段按钮两档、玻璃圆钮两档）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 13/15 |
| 判据有效性 | 11/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 13/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 12/15 |
各维理由：真实审查给 13 是"真的看了图且看了两档两态"，扣 2 是只覆盖 251 的三处里的两处；判据有效性 11 —— 读数出自**临时尺**，没进 `scripts/`、没进电池，下一轮不重跑就没人能复查；
假绿防御 14 —— 负对照（自身=0）与正对照（modechip 有变化）同跑，且第一版尺子量错对象被当场发现并写进 U-773；
产品面推进 8 —— 连续又一轮 0 产品文件，且这一轮**明确拒绝**凭临时尺改 `VisualFill.hover`（欠的是同口径的仓库尺，不是勇气）；
台账一致性 13；交付诚实性 14 —— 未做四项逐条记账；可复核性 12 —— 复现命令都在账里，但尺不在仓库里，命令跑第二遍要手搓。
合计 **85**/105。
'''
SEC_DE = u'''**D-225（R239）：两态对照的读数，先问「分子分母是不是同一个估计量」，再问「够不够亮」—— 不同口径的两个数不许跨账互证。**
本轮量到亮档悬停 1.078:1 / 1.093:1，比 R231 那本账的"亮档药丸 1.160:1"更低，看起来足够定罪；但它是**变化带内全像素均值**（未变像素一起进分母，被稀释），
而 1.160 是**控件局部对比度**。⇒ 处置：只登记读数 + 新开 272（把尺搬进 `scripts/`，两口径各一版、配正负对照与刀），**不改 `VisualFill.hover` 的任何一档**。
附则一（同一轮的自坏）：按点坐标取样那版全读到平涂背景（暗 30 / 亮 255、min==max）—— 帧是 @2x，我把点尺寸当像素尺寸用了；
**min==max 的框要当场判成"量到背景"，不许当"控件没画"**。
附则二：缺席要数出来 —— 251 第三处（DetailView 的悬停）没有两态帧这件事，是按 `detail-*` 帧名里 hover/idle 对数=0 数出来的，不是印象。

'''
SEC_BL = u'''## R239 补记（2026-10-20 · 新开 272）

**272. 251 的两态差读数出自一把临时尺（变化带内均值口径），必须搬进 `scripts/` 才能拿它判产品（新开）**

现场：`glass-pill` 亮档 1.078:1 / 段按钮亮档 1.093:1，都在正对照（modechip 已知变化，亮档 1.143:1）**之下**；暗档分别 1.232:1 / 1.179:1。
复现（本轮真跑过）：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_r239 swift test --filter UICaptureTests`，再按帧名配对做 `ImageChops.difference` + Δ>4 计数。
欠的三样：① 尺要进 `scripts/`（两口径各一版：**变化带均值**与**控件局部对比度**，两者不许互证 —— D-225）；② 要配负对照（帧↔自身=0）与正对照（modechip idle↔lit）各一格，且**名单为空=红**；
③ 251 第三处（`DetailView.swift:609`）先补两态帧再判 —— 现在 `detail-*` 里 hover/idle 对数=0。
不许做的事：拿这把临时尺的数去改 `VisualFill.hover` 的档位；也不许为了让 `scripts/` 里有尺而把阈值定在刚过线的位置（R231 的教训：贴边假峰躲过 4pt）。

'''
SEC_CH = u'''- 看图腿：重捕 162 帧（暗 81 / 亮 82、`FRAME_BASELINE_CHANGED=0`），给 251 的两处悬停位点交出第一批「静置↔悬停」两态差读数（暗 1.232/1.179、亮 1.078/1.093），
  并当场量出临时尺的两处错（点坐标当像素用 → 全读平涂背景；带内均值与 R231 的控件局部口径不同 ⇒ 不许跨账互证）⇒ 只登记读数、不改产品（R239 / U-771…U-773 / D-225 / 新开 272 · 产品 0 文件）。
'''
SEC_ST = u'''最后更新：2026-10-20 01:10（本地 · R239 / 第 238 轮 / Round 236）：**看图腿回来了 —— 重捕 162 帧、251 的两处悬停第一次有两态差读数，且当场量到自己那把临时尺的单位错**（U-771…U-773 · D-225 · 新开 272 · 产品 0 文件，画面一字未动）

**本轮落地**：帧通道恢复（`swift test --filter UICaptureTests` ⇒ 162 帧、`frame_baseline check` ⇒ CHANGED=0）；
两态差尺（含负对照=帧自身、正对照=modechip）量出 玻璃圆钮 暗 1.232 / 亮 1.078、段按钮 暗 1.179 / 亮 1.093。
**判为不改**：亮档那两个数与 R231 的"药丸 1.160:1"不是同一个估计量（带内均值 vs 控件局部）⇒ 见 D-225。

**下一轮（R240 / 第 239 轮 / Round 237）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿 run↔commit 成对（别轮询）。未读的三笔：`RUN=39351035433 sha=6927880 status=in_progress conclusion=`（空 ⇒ 只能说未读）、
   `39350006461↔3e90ab4`、`39347522293↔7b7495d`；要验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 那一行、以及**电池认不认两种形状**（250/270 的 runner 半）。编译红没恢复前下游红不当产品读数。
① 把 272 的尺搬进 `scripts/`：两口径各一版（变化带均值 / 控件局部对比度）、配正负对照、名单为空=红，再决定 251 亮档要不要动 `VisualFill.hover`。
② 给 251 第三处（`DetailView.swift:609`）补两态帧 —— 现在 `detail-*` 里 hover/idle 对数=0。
③ 登记 M795/M796（R238 补记那四朵红）进变异名册与预检。
④ 249 / 263 / 268 的 runner 半；269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 仍开。
⑤ 用户闸门：220 路 A（要授权改全局 `AppleKeyboardUImode`）、228②、265（要真机）。

'''

# —— 锚点 ——
assert ui.count(u'## 第 237 轮（R238') == 1 and ui.count(u'## 第 238 轮（R239') == 0
ui_new = ui.replace(u'## 第 237 轮（R238', SEC_UI + u'## 第 237 轮（R238', 1)
it_new = it.rstrip('\n') + u'\n\n' + SEC_IT
de_new = de.rstrip('\n') + u'\n\n' + SEC_DE
bl_new = bl.rstrip('\n') + u'\n\n' + SEC_BL
lines = ch.splitlines(True)
hits = [n for n, ln in enumerate(lines) if ln.strip() == u'## [Unreleased]']
assert len(hits) == 1, len(hits)
lines.insert(hits[0] + 1, u'\n' + SEC_CH)
ch_new = u''.join(lines)
slines = st.splitlines(True)
sh = [n for n, ln in enumerate(slines) if ln.startswith(u'最后更新：')]
assert len(sh) >= 1
slines.insert(sh[0], SEC_ST + u'\n')
st_new = u''.join(slines)
u_max = max(int(x) for x in re.findall(r'(?m)^- \*\*U-(\d{3})', ui_new))
fr_new = re.sub(r'U-31\s*…\s*U-\d{3}', u'U-31 … U-%03d' % u_max, fr, count=1)
fr_new = re.sub(r'R9–R\d+，\d+ 轮自评', u'R9–R236，235 轮自评', fr_new, count=1)

# 写盘前自检
assert u_max == 773, u_max
assert re.search(r'(?m)^## 第 238 轮（R239 / Round 236', ui_new)
assert it_new.count(u'| ') - it.count(u'| ') >= 9
for n in (u'771', u'772', u'773'):
    assert (u'- **U-' + n) in ui_new
assert (u'**D-225（R239）') in de_new and u'**272. ' in bl_new
assert fr_new.count(u'U-31 … U-773') == 1 and u'R9–R236' in fr_new
for p, txt in ((ui_p, ui_new), (it_p, it_new), (de_p, de_new), (bl_p, bl_new),
               (ch_p, ch_new), (st_p, st_new), (fr_p, fr_new)):
    io.open(p, 'w', encoding='utf-8').write(txt)
json.dump({'U': u_max, 'frames': 162}, io.open('/tmp/r239_round_numbers.json', 'w'))
print('LEDGERS_R239_ROUND 写了 7 本 / U-771…U-773 / D-225 / BACKLOG 272')
