import io, re
def rd(p): return io.open(p, encoding='utf-8').read()
ui_p='AGENT_UI_AUDIT.md'; it_p='AGENT_VISUAL_ITERATION.md'; de_p='AGENT_DECISIONS.md'
bl_p='AGENT_BACKLOG.md'; ch_p='CHANGELOG.md'; st_p='AGENT_STATE.md'; fr_p='AGENT_FINAL_REPORT.md'
ui=rd(ui_p); it=rd(it_p); de=rd(de_p); bl=rd(bl_p); ch=rd(ch_p); st=rd(st_p); fr=rd(fr_p)
ruler=rd('/tmp/r240_ruler.log') if False else io.open('/tmp/r240_ruler.log',encoding='utf-8').read()
rows=[l for l in ruler.splitlines() if l.startswith('HOVER_DIFF -')]
print('RULER_ROWS=%d' % len(rows))
SEC_UI=u'''## 第 239 轮（R240 / Round 237 · 2026-10-20）：把 R239 那把临时尺搬进仓库（`scripts/hover_two_state_diff.py`），两个口径同时交出来，并让它先红在我自己的配对规则上（U-774…U-776）

- **U-774：尺入库。** `scripts/hover_two_state_diff.py` 一次给两个口径：**带内均值**（变化带内全部像素，会被未变像素稀释）与**变化像素逐点中位数**（只看真的变了的那些点，才是"控件局部"那一档），外加变化面积占比。
  配对**按帧名推、不接受点坐标**（@2x 的教训在文件头写明）；三把闸门：负对照（帧↔自身必须 0）、正对照（`--control` 给一对已知有变化的帧，必须 ≥50 个变化像素）、空名单=红（`HOVER_DIFF_EMPTY=1`）。
  复现：`python3 scripts/hover_two_state_diff.py --shots /tmp/shots_r239 --control modechip-hover-idle-200x60-dark,modechip-hover-lit-200x60-dark`。
- **U-775：本机真读数（配对=2 / 三把对照全 OK / `RULER_EXIT=0`）。** 玻璃圆钮 暗 面积 21.1%、带内均值 **1.232**、逐点中位 **1.393**；亮 22.1%、**1.078**、**1.092**。
  正对照 modechip 暗：面积 3.4%、带内均值 1.223、逐点中位 **1.515**。⇒ **两个口径给出的结论不同向**：按带内均值，亮档 1.078 低于正对照 1.223；按逐点中位，亮档 1.092 也低于正对照 1.515，但暗档 1.393 同样低于 1.515。
  ⇒ 这条尺**能报数、还不能判产品**：缺的是"可分辨线压在哪个口径的哪个值上"，而那要先有第二台机器的读数（CI）与 251 的第三处两态帧。本轮**不动 `VisualFill.hover` 任何一档**。
- **U-776：新尺第一次跑就红，红在它自己的配对规则上（不是产品）。** 第一版只试 `X-hover-…`→`X-…` 与 `X-hover-…`→`X-hover-…-idle`，于是 `segmented-filter-hover-200x60` 被报成"无静置态"，而 `segmented-filter-idle-200x60-dark` 明明在盘上 —— 漏了把 `-hover` 换成 `-idle` 的中缀形。
  发现方式：加 `--min-pairs 4` 让覆盖率地板说话（真产物上只有 2 对 ⇒ 红），而不是数"有没有出现过配对"。修候选后仍只 2 对：`heatmap-cell-strip-hover` / `row-favorite-hover` / `quickpick-hover` / `controlprobe-hover-ladder` / `settingsrow-hover-idle↔lit` / `modechip-hover-idle↔lit` 这些**没有 hover↔静置同尺寸对**，逐条打印成显式缺席（不是红，是读数）。
  **未做**：① 这把尺**还没接进电池**（`scripts/tests` 里没有对应守卫，CI 也没有那一步）⇒ 下一轮接线，且要配"不给 `--control` 就红"的正对照；② 251 第三处（`DetailView.swift:609`）仍无两态帧；③ M795/M796 仍未登记；④ CI 未读（`RUN=39352046610 sha=5252c05 status=in_progress conclusion=` 空）。

'''
SEC_IT=u'''## Round 237 · 看图腿的尺子进了仓库（R240 / 第 239 轮）：两口径同时给，先红在自己的配对规则上 / D-226 / BACKLOG 272 结案、新开 273 · 产品 0 文件

本轮次对照：与 R239（临时尺、口径不统一、不能定罪）相比，本轮把尺搬进 `scripts/` 并让两种口径同时可见，且第一次运行就用自己的覆盖率地板抓出配对漏检。
做了什么：写 `scripts/hover_two_state_diff.py`（带内均值 / 变化像素逐点中位 / 面积占比 + 负对照 + 正对照 + 空名单红 + `--min-pairs`）→ 在本机 162 帧上跑 → 修配对候选 → 台账。
看图腿：读数腿 RUN（`RULER_EXIT=0`，配对 2、三把对照全 OK）；眼睛腿 NOT-RUN（本轮没再看新图，帧与 R239 同一批）。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | 11/15 |
| 判据有效性 | 12/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 12/15 |
| 交付诚实性 | 14/15 |
| 可复核性 | 13/15 |
各维理由：眼睛腿本轮没跑（11）；判据有效性 12 —— 尺在仓库里了但**没接电池**，下一轮不重跑就没人拦它坏；假绿防御 14 —— 空名单红、无 `--control` 红、帧↔自身必须 0、覆盖率地板第一次就把漏检逼出来；产品面推进 8 —— 连续 0 产品文件，且再次**拒绝**凭未定线的尺改档；可复核性 13 —— 复现命令在账里、尺在仓库里（比 R239 的手搓高一档）。合计 **84**/105。
'''
SEC_DE=u'''**D-226（R240）：一把新尺进仓库的第一件事不是拿它判产品，而是先问「它的名单会不会漏」—— 覆盖率要有一根地板，且地板要能被打红。**
本轮 `--min-pairs 4` 在真产物上只配到 2 对 ⇒ 立刻暴露"漏了 `-idle` 中缀形"这条 bug；如果我只判"配对数 > 0"，这把尺会带着漏检绿下去（R99「名单为空=红」的加强版：**名单不全也是红**，地板由真产物推）。
附则：两个口径（带内均值 / 变化像素逐点中位）**必须同时打印**，因为 R231 那本账用的是控件局部口径、R239 临时尺用的是带内均值 —— 只印一个就会有人拿它去跟另一本账对（跨口径互证是 D-225 那条病的复发形式）。
判为不做：本轮不给"可分辨线"定阈值。缺的是第二台机器（CI）的读数与 251 第三处的两态帧；先定线就是把贴边假峰写成契约（R231 的教训）。

'''
SEC_BL=u'''## R240 补记（2026-10-20 · 272 结案、新开 273）

**272 结案（R240）**：尺已进 `scripts/hover_two_state_diff.py`，两口径同时打印（带内均值 / 变化像素逐点中位数 + 面积占比），配对按帧名推、拒绝点坐标，三把闸门（帧↔自身=0 / `--control` 正对照 / 空名单=红）+ `--min-pairs` 覆盖率地板。本机真读数：玻璃圆钮 暗 1.232 / 1.393、亮 1.078 / 1.092；正对照 modechip 暗 1.223 / 1.515。
**没结案的那半**：这把尺**还没接进电池与 CI**，所以它坏掉没人拦 ⇒ 新开 273。

**273. `hover_two_state_diff.py` 要接进 `scripts/tests` 与 CI 那一步，并配「不给 --control 就红」「不给真帧就 skip 且点名通道」两格证人（新开）**

现场：本轮 `--min-pairs 4` 在真产物上只配到 2 对（漏检被地板逼出来），说明这把尺自己会坏；而它现在只在一次性命令里跑过，仓库里没有任何断言守着它。
下一轮要做：① 一格用合成帧（现造两态小图）验"变化像素数与面积对得上"，② 一格喂 `--control` 缺失 ⇒ 必须 `rc=1`，③ 一格喂空目录 ⇒ 必须 `HOVER_DIFF_EMPTY=1` 且 rc=1（不许 skip 成绿），④ 接进 CI 步骤后要把 `--min-pairs` 的地板按**每台机器各自**数出来的配对数登记（R121 的按机器分键那一族），别拿本机 2 当 runner 的地板。
另外 251 的欠账形状已经由这把尺自己打印出来：18 个 `-hover` 帧名里只有 2 个有同尺寸静置态配对 —— 逐条打印为显式缺席，下一轮补哪几对由它点名。

'''
SEC_CH=u'''### 看图与尺子：两态差尺进仓库 `scripts/hover_two_state_diff.py`（R240 / 第 239 轮 / Round 237 · U-774…U-776 / D-226 / BACKLOG 272 结案、新开 273 · 产品 0 文件，画面一字未动）

- 新尺一次给两个口径（带内均值 / 变化像素逐点中位数 + 变化面积占比），配对按帧名推、明确拒绝点坐标（@2x 帧把点坐标当像素会全读平涂背景）；三把闸门 = 帧↔自身必须 0、`--control` 正对照必须读到变化、空名单必须红，另加 `--min-pairs` 覆盖率地板。
- 本机真读数：玻璃圆钮 暗 1.232/1.393、亮 1.078/1.092；正对照 modechip 暗 1.223/1.515。两口径结论不同向 ⇒ **判为不动 `VisualFill.hover`**，缺的是可分辨线压在哪个口径（D-226 附则：不许跨口径互证）。
- 第一次跑就红在自己的配对规则上（漏 `-idle` 中缀形），由 `--min-pairs 4` 逼出；修候选后仍只有 2 对，其余 18 个 `-hover` 帧名逐条打印成显式缺席。**未做**：尺未接进电池与 CI（新开 273）、M795/M796 未登记、CI 未读。
'''
SEC_ST=u'''最后更新：2026-10-20 01:16（本地 · R240 / 第 239 轮 / Round 237）：**两态差尺进仓库（`scripts/hover_two_state_diff.py`）—— 两口径同时给、三把闸门 + 覆盖率地板，第一次跑就红在自己的配对规则上**（U-774…U-776 · D-226 · 272 结案、新开 273 · 产品 0 文件，画面一字未动）

**本轮落地**：尺入库并本机跑通（`RULER_EXIT=0`，配对 2、负/正对照全 OK）；玻璃圆钮 暗 1.232/1.393、亮 1.078/1.092，正对照 modechip 暗 1.223/1.515；两口径不同向 ⇒ 判为不动档（D-226）。

**下一轮（R241 / 第 240 轮 / Round 238）的靶**：
⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。未读五笔：`39352046610↔5252c05`、`39351035433↔6927880`、`39350006461↔3e90ab4`、`39347522293↔7b7495d`、`本笔↔?`；要验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 那一行、以及**电池认不认两种形状**（250/270 的 runner 半）。编译红没恢复前下游红不当产品读数。
② 做 273：把尺接进 `scripts/tests`（合成帧验数 / 缺 `--control` 必须红 / 空目录必须红）与 CI 那一步，地板按机器各自登记。
③ 251 第三处（`DetailView.swift:609`）补两态帧；18 个 `-hover` 名里只有 2 对有静置态，尺会逐条点名。
④ 登记 M795/M796；⑤ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240；用户闸门 220 路 A、228②、265。

'''
assert ui.count(u'## 第 239 轮（R240')==0 and ui.count(u'## 第 238 轮（R239')==1
ui_new=ui.replace(u'## 第 238 轮（R239', SEC_UI+u'## 第 238 轮（R239',1)
it_new=it.rstrip('\n')+u'\n\n'+SEC_IT; de_new=de.rstrip('\n')+u'\n\n'+SEC_DE; bl_new=bl.rstrip('\n')+u'\n\n'+SEC_BL
lines=ch.splitlines(True); hits=[n for n,l in enumerate(lines) if l.strip()==u'## [Unreleased]']; assert len(hits)==1
i=hits[0]+1
while i<len(lines) and not lines[i].strip(): i+=1
lines.insert(i, SEC_CH+u'\n'); ch_new=u''.join(lines)
sl=st.splitlines(True); sh=[n for n,l in enumerate(sl) if l.startswith(u'最后更新：')]; sl.insert(sh[0], SEC_ST+u'\n'); st_new=u''.join(sl)
u_max=max(int(x) for x in re.findall(r'(?m)^- \*\*U-(\d{3})', ui_new))
fr_new=re.sub(r'U-31\s*…\s*U-\d{3}', u'U-31 … U-%03d'%u_max, fr, count=1)
fr_new=re.sub(r'R9–R\d+，\d+ 轮自评', u'R9–R237，236 轮自评', fr_new, count=1)
assert u_max==776, u_max
for n in (u'774',u'775',u'776'): assert (u'- **U-'+n) in ui_new
assert u'**D-226（R240）' in de_new and u'**273. ' in bl_new and re.search(u'(?m)^### .*R240', ch_new) and u'R240' in it_new
for p,txt in ((ui_p,ui_new),(it_p,it_new),(de_p,de_new),(bl_p,bl_new),(ch_p,ch_new),(st_p,st_new),(fr_p,fr_new)):
    io.open(p,'w',encoding='utf-8').write(txt)
print('LEDGERS_R240 写了 7 本 / U-774…U-776 / D-226 / 272 结案 + 新开 273')
