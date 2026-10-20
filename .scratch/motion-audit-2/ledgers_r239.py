# R238 补记台账：全字面文本、先断锚再写盘（任一处不命中就一本都不写）
import io, re, json

def rd(p): return io.open(p, encoding='utf-8').read()

bl = rd('AGENT_BACKLOG.md'); ui = rd('AGENT_UI_AUDIT.md'); de = rd('AGENT_DECISIONS.md')
ch = rd('CHANGELOG.md'); st = rd('AGENT_STATE.md'); fr = rd('AGENT_FINAL_REPORT.md')

# —— 现取读数（不手抄）——
head_items = re.findall(r'(?m)^(\d{3})\. ', bl)
bold_items = re.findall(r'(?m)^\*\*(\d{3})\. ', bl)
u_defined = re.findall(r'(?m)^- \*\*U-(\d{3})', ui)
d_defined = re.findall(r'(?m)^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', de)
dmax = max(int((m[0] or m[1]).replace('D-', '')) for m in d_defined)
cn = max(int(n) for n in re.findall(r'(?m)^## 第 (\d+) 轮', ui))
en = max(int(n) for n in re.findall(r'(?m)^## Round (\d+) ·', rd('AGENT_VISUAL_ITERATION.md')))
st_cn = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st)
assert (int(st_cn.group(2)), int(st_cn.group(1))) == (cn, 238), (st_cn.group(0), cn)
NUM = dict(H=len(head_items), B=len(bold_items), U=len(head_items) + len(bold_items),
           UMAX=max(int(x) for x in u_defined), D=dmax + 1, CN=cn, EN=en, R=int(st_cn.group(1)))
print('READINGS ' + json.dumps(NUM, ensure_ascii=False))

SEC_BL = u'''## R238 补记（2026-10-20 · 270 结案、新开 271）

**270. 与 250 同族：`DuplicateIdTests` 声称「BACKLOG 编号唯一」，实际只看得见 `^NNN. ` 这一种形状；写成 `**NNN. ` 的那一整代条目不在覆盖面里（R238 补记：当场结案）**

现场数字（本机、同一份账，现取）：标题形 __H__ 条（最大 186）/ 粗体形 __B__ 条（最大 269）/ 并集 __U__ 条，
**零重叠、零重复**。复现：`python3 -c "import re,io;t=io.open('AGENT_BACKLOG.md',encoding='utf-8').read();print(len(re.findall(r'^[0-9]{3}[.] ',t,re.M)),len(re.findall(r'^^[\\\\*]{2}[0-9]{3}[.] '.replace('^',''),t,re.M)))"`
⇒ 187…269 这一整代条目对那条守卫是**隐形**的：R102 立它的那次事故（同号两份正文）若发生在粗体形那批里，它一路绿着。
结案动作照 D-223 的规矩走：`ITEM` 改成**一支**正则两种形状（`^(?:\\*\\*)?(\\d{3})\\. `），不写成两份实现互相掩盖；
新形状配两态证人（合成语料 `test_the_bold_item_shape_is_counted`）、老形状配子集证人
（`test_the_heading_item_shape_is_still_counted`，加 `test_real_ledger_bold_items_are_an_extra_set`：并集必须**恰等于**两集之和，
不相等就说明有第三种形状混进来或两集重叠）、两形**各自**配「造一个重复号必须只抓到那一个号」
（`test_forging_a_duplicate_on_either_shape_is_caught`，靶子按形状各取一头，不依赖「最大号恰好是哪种形状」）。
**绝对锚点**：地板从 40 抬到量出来的 150 —— 正则若退回只认标题形就只剩 __H__ 条，这一格不靠对照也能红。
一次性反证（**未**登记名册）：把 `ITEM` 逐字节退回老字面 ⇒ 该卷 `FAILED (failures=4)`，还原 `RESTORE_CLEAN=yes`；
该判据文件从 16 格长到 20 格。
未做：① 那四朵红没做成可复查的变异臂（M795 / M796 留给下一轮，按 R238 的表形状接进 `test_mutate_arm_registry` 与预检名册）；
② 本笔与上一笔的 CI 都未读；③ 看图腿 NOT-RUN（产品 0 文件，也没重捕帧）。

**271. 上一笔提交 3e90ab4 的 subject 把轮次标签手抄错了（写成 `Round 227（第 238 轮 / Round 235）`，而三本台账都是 第 __CN__ 轮 / R238 / Round __EN__）⇒ commit subject 必须从台账现取派生（新开）**

成因：subject 是我手打的。「轮次标签与台账数字不许手抄」这条规矩（R88/R147 那批）只落在台账落盘口上，
仓库里**没有任何守卫看 `git log` 的 subject**，所以电池全绿、错标签进了远端历史，而历史不能改写（不 rebase、不 force push）。
本笔已经改成派生：subject 由脚本从台账现取（最大 `第 N 轮` / 最大 `Round N` / STATE 的 `R(\\d+)`）拼出，
它自己就是这一格的证人；下一轮要判的是「要不要再加一格守卫去比对最近 N 笔 subject 与台账那一轮」——
先想清楚它在 CI、浅克隆、别人并行提交时跑不跑得动，**不许为了让它绿而放宽**；跑不动就照 251 那条写成显式未覆盖。

'''
SEC_BL = (SEC_BL.replace('__H__', str(NUM['H'])).replace('__B__', str(NUM['B']))
          .replace('__U__', str(NUM['U'])).replace('__CN__', str(NUM['CN'])).replace('__EN__', str(NUM['EN'])))

SEC_UI_HEAD = u'- **U-769：补记读数（BACKLOG 270 的现场数字）。**'
assert ui.count(u'（U-765…U-768）') == 1 and ui.count(SEC_UI_HEAD) == 0
SEC_UI = u'''- **U-769：补记读数（BACKLOG 270 的现场数字与结案形状）。** 同一条「按形状认东西」的病在同一个文件里重演：
  `ITEM = ^(\d{3})\. ` 在 `AGENT_BACKLOG.md` 上数到 **__H__** 条（最大 186），而写成 `**NNN. ` 的那一整代条目
  ——**__B__** 条、最大 269 —— 对它完全隐形，于是「编号唯一」这条守卫**声称的覆盖面比实际的宽**。
  复现：`python3 -m unittest scripts.tests.test_ledger_ids -v`（**20** 格，16→20）。
  处置照 D-223：一支正则两种形状 + 新形状两态证人 + 老形状子集证人 + 两形各自造重复 + 地板 40→**150**（绝对锚点，
  退回老字面只剩 __H__ 条就必红）。一次性反证：`FAILED (failures=4)`、`RESTORE_CLEAN=yes`；**这四朵红未登记成变异臂**。
- **U-770：我这一轮自己印错了一个数，且错在「数红名」那把尺上。** 反证脚本按 `^(test_\w+)` 抓 stderr 报「红名=20」，
  而那一次真实只有 4 朵（结论行 `FAILED (failures=4)`）—— `-v` 的清单里连 `... ok` 的行也以 `test_` 开头。
  ⇒ 红名要按 `^FAIL: (test_\w+)` 抓（R102「红掉的测试名要按空格切」、R149「按步骤名过滤」同一族：
  **计数尺的行首要按输出实际形状写，不能按"看起来像测试名"写**）。这条没做成守卫，只记在这里，
  因为下一轮的 M795/796 要用它挑红名；写台账时把它当已知坑，不当结论。
'''.replace('__H__', str(NUM['H'])).replace('__B__', str(NUM['B']))

SEC_DE = u'''**D-224（R238 补记）：一条守卫「覆盖面比它声称的窄」修好之后，必须立刻在同一份文件里再问一遍「还有哪条正则也是按形状认东西的」——同一族的病不会只长在一处。**
判断：BACKLOG 250 结案（`DEC_DEF` 扩成标题 ∪ 粗体）之后，我没有立刻扫同文件的其它正则；是这一轮补记时顺手 `grep -n "re.compile" scripts/tests/test_ledger_ids.py` 才看见
`ITEM = ^NNN. ` 也在按形状认条目，于是那条「编号唯一」守卫对 187…269 一整代条目是瞎的。
三步（下次照做）：① 修完一个"按形状漏读"的守卫，**同文件同目录**的兄弟正则逐条问一遍"它认几种形状、这份账实际有几种"；
② 扩覆盖面时给**新那一半**配两态证人、给**老那一半**配子集/差集证人，两形各自配造靶子的正对照；
③ 地板取"量出来的绝对数"而不是一个宽松的 40 —— 否则"退回老字面"只能靠对照红，绝对锚点能自己红。
附则（这一轮的自坏）：数红名的行首也要按输出形状写。我按 `^(test_\w+)` 抓 `-v` 的 stderr，把 4 朵红数成 20 —— 那把尺不是判据，
是我临时写的；**临时尺也要在已知答案的样本上试一次**（这里已知答案是结论行 `FAILED (failures=4)`，两数不一致就该停）。

'''
SEC_CH = u'''- 判据：`DuplicateIdTests` 的 BACKLOG 条目正则从只认 `^NNN. ` 扩成「标题形 ∪ 粗体形」，地板 40→150 改成量出来的绝对锚点，
  两形各配造重复正对照（R238 补记 / U-769…U-770 / D-224 / BACKLOG 270 结案、新开 271 · 产品 0 文件，画面一字未动）。
'''

# —— 锚点与写盘 ——
i_cn = ui.find(u'## 第 237 轮')
assert i_cn >= 0
j = ui.find(u'\n## ', i_cn + 10)
assert j > i_cn
ui_new = (ui[:i_cn] + ui[i_cn:j].replace(u'（U-765…U-768）', u'（U-765…U-770）') + u'\n' + SEC_UI + ui[j+1:])

lines = ch.splitlines(True)
k = [n for n, ln in enumerate(lines) if ln.startswith(u'### 判据与尺：台账编号守卫的「定义行」')]
assert len(k) == 1, len(k)
lines.insert(k[0] + 1, SEC_CH)
ch_new = u''.join(lines)

st_lines = st.splitlines(True)
m = [n for n, ln in enumerate(st_lines) if u'RUN=39347522293' in ln]
assert len(m) == 1, len(m)
indent = re.match(r'\s*', st_lines[m[0]]).group(0)
SEC_ST = (indent + u'- **R238 补记（同一轮第二次落盘）**：`RUN=39350006461 sha=3e90ab4 status=in_progress conclusion=`'
          u'（空 ⇒ 只能报未读）。270 结案（`ITEM` 两种形状 + 地板 150，该卷 16→20 格）、新开 271（上一笔 subject 手抄错轮次标签 ⇒ 从台账派生）。'
          u'下一轮 ⓪ 读的是**这两笔**的 run，另要把 M795/M796 登记成变异臂；编译没恢复之前 STEP[15]/[17]/[18]/[19] 那几朵红一律不当产品读数。\n')
st_new = u''.join(st_lines[:m[0] + 1] + [SEC_ST] + st_lines[m[0] + 1:])

new_u_cell = u'U-31 … U-%03d' % (NUM['UMAX'] + 2)
fr_new, n_sub = re.subn(r'U-31\s*…\s*U-768', new_u_cell, fr, count=1)
assert n_sub == 1, 'FINAL_REPORT 的 U 区间锚点没命中'
assert new_u_cell in fr_new
assert fr_new != fr
bl_new = bl.rstrip('\n') + u'\n\n' + SEC_BL
de_new = de.rstrip('\n') + u'\n\n' + SEC_DE

# 写盘前自检：区间与定义集合吻合、新号有正文、旧行都还在
assert re.search(r'（U-765…U-770）', ui_new)
for n in (u'769', u'770'):
    assert (u'- **U-' + n) in ui_new
old_lines = [ln for ln in ui.splitlines() if ln.strip()]
new_set = set(ui_new.splitlines())
missing = [ln for ln in old_lines if ln not in new_set]
assert len(missing) == 1 and missing[0].startswith(u'## 第 237 轮') and u'（U-765…U-768）' in missing[0], \
    u'原台账被弄丢的行不止那一处标题：%s' % [m[:60] for m in missing]
assert u'**270. ' in bl_new and u'**271. ' in bl_new
assert len(re.findall(r'(?m)^\*\*(\d{3})\. ', bl_new)) == NUM['B'] + 2
assert (u'**D-%03d（' % NUM['D']) in de_new

for p, txt in ((u'AGENT_BACKLOG.md', bl_new), (u'AGENT_UI_AUDIT.md', ui_new),
               (u'AGENT_DECISIONS.md', de_new), (u'CHANGELOG.md', ch_new),
               (u'AGENT_STATE.md', st_new), (u'AGENT_FINAL_REPORT.md', fr_new)):
    io.open(p, 'w', encoding='utf-8').write(txt)
json.dump(NUM, io.open('/tmp/r239_ledger_numbers.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('LEDGERS_R239 写了 6 本，U-770 / D-%03d / 并集条目 %d 条' % (NUM['D'], NUM['U'] + 2))
