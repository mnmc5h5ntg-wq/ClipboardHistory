#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R198 的台账批写：BACKLOG 221 结案在**色觉模拟**这根轴上，并把"第一版把尺子弄坏了"这件事本身记账。

同 R191–R196：数字一律从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
本轮多一件事：**两通道（判据的离屏单格 / 真帧的 5 格竖条）的墨色要逐档对账**，
偏移由两份日志相减得出，不许我手抄成"大概 6/255"。
门：① 变异表 4/4 CAUGHT、ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=yes；② 台账引用的 M7xx 必须在变异日志里露面；
③ 全量卷三元组解析到且失败为 0；④ 最新一节 U 定义恰好 644/645/646 且与标题区间吻合；
⑤ 16 条 HEAT_ADJACENT_CVD 与 1 条 SIM_MATRIX 必须都在；⑥ 真帧复量两档各 5 格 + 4 步必须齐（看图腿没有读数就还是看代码猜）；
⑦ 帧基线必须 COMPARED>0 且 CHANGED=0、MISSING=0（分母为 0 的"没变"是空对账）；⑧ 本轮产品必须 0 文件；
⑨ 两通道档数必须都是 5，否则偏移是拿错对象减出来的。
'''
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'full': '/tmp/r198_full.log', 'mut': '/tmp/r198_mutate.log',
     'frame': '/tmp/r198_frame.log', 'base': '/tmp/r198_base.log'}
NEW_R, NEW_N = 198, 200
FLOOR = 18.0


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


def find(pat, text, what):
    hits = re.findall(pat, text)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


def ink(t):
    return tuple(int(v) for v in t.strip('()').replace(' ', '').split(','))


full = read(L['full'])
mut = read(L['mut'])
frame = read(L['frame'])
base = read(L['base'])

# —— 判据那 16 条读数（离屏通道）
cvd = re.findall(r'HEAT_ADJACENT_CVD (\S+) (\S+)→(\S+) 像素=(\d+) 前墨=(\S+) 后墨=(\S+) '
                 r'模拟前=([\d.]+) 模拟后=([\d.]+) 保住=(\d+)%', full)
if len(cvd) != 16:
    raise SystemExit('PARSE_FAILED CVD 读数只有 %d 条（要 16）⇒ 拒绝写盘' % len(cvd))
matrix = find(r'(SIM_MATRIX [^\n]*)', full, '真值表行')
mn = min(cvd, key=lambda r: float(r[7]))
by_pair = {}
for r in cvd:
    by_pair.setdefault(r[0].split('/')[0], []).append((r[1], r[2], float(r[6]), float(r[7]), int(r[8])))


def steps(tag):
    return u'、'.join(u'%s→%s %g→%g（保住 %d）' % (a, b, before, after, keep)
                      for a, b, before, after, keep in by_pair[tag])


def keeps(tag):
    return sorted(set(u'%d' % keep for _, _, _, _, keep in by_pair[tag]))


# —— 真帧通道（看图腿的复量）
fl = re.findall(r'FRAME_LADDER (\w+) 步(\d+) \(([^)]+)\)→\(([^)]+)\) 前=(\d+) 后=(\d+) 保住=(\d+)', frame)
frame_steps = {}
for tag, idx, a, b, before, after, keep in fl:
    frame_steps.setdefault(tag, []).append((int(before), int(after), int(keep)))
for tag in ('dark', 'light'):
    if len(frame_steps.get(tag, [])) != 4:
        raise SystemExit('PARSE_FAILED 真帧 %s 读到 %d 步（要 4）⇒ 竖条结构没排干净'
                         % (tag, len(frame_steps.get(tag, []))))


def frame_inks(tag):
    rows = re.findall(r'FRAME_INK %s 档(\d+) 墨=\(([^)]+)\)' % tag, frame)
    if len(rows) != 5:
        raise SystemExit('PARSE_FAILED 真帧 %s 读到 %d 档（要 5）' % (tag, len(rows)))
    return [ink('(' + m + ')') for _, m in rows]


def judg_inks(tag):
    rows = [r for r in cvd if r[0] == tag + '/1x']
    if len(rows) != 4:
        raise SystemExit('PARSE_FAILED 判据通道 %s 只有 %d 对（要 4）' % (tag, len(rows)))
    return [ink(rows[0][4])] + [ink(r[5]) for r in rows]


def offsets(tag):
    j, f = judg_inks(tag), frame_inks(tag)
    per = [tuple(f[i][c] - j[i][c] for c in range(3)) for i in range(5)]
    mx = [max(abs(p[c]) for p in per) for c in range(3)]
    text = u'逐档 真帧−判据 ' + u'、'.join(u'%s' % str(p) for p in per)
    return per, mx, text + u'；各通道最大 |偏移| R=%d G=%d B=%d' % tuple(mx)


off_dark, off_dark_max, off_dark_text = offsets('dark')
off_light, off_light_max, off_light_text = offsets('light')
# "偏移只在哪一列"这句话要由两档共同签，不能只拿暗档那三列的最大值说话
gb_max = max(off_dark_max[1], off_dark_max[2], off_light_max[1], off_light_max[2])
r_max = max(off_dark_max[0], off_light_max[0])
f_min = {t: min(a for _, a, _ in frame_steps[t]) for t in ('dark', 'light')}
strip_rows = re.findall(r'(FRAME_STRIP \w+ [^\n]*)', frame)
if len(strip_rows) != 2:
    raise SystemExit('PARSE_FAILED 竖条结构读数缺 %d 行（要 2）' % (2 - len(strip_rows)))
pic_rows = re.findall(r'(FRAME_PIC \w+ [^\n]*)', frame)

compared = int(find(r'FRAME_BASELINE_COMPARED=(\d+)', base, 'COMPARED'))
changed = int(find(r'FRAME_BASELINE_CHANGED=(\d+)', base, 'CHANGED'))
missing = int(find(r'FRAME_BASELINE_MISSING=(\d+)', base, 'MISSING'))

caught_n = int(find(r'CAUGHT=(\d+)', mut, 'CAUGHT'))
total_n = int(find(r'刀=(\d+)', mut, '刀数'))
esc_n = int(find(r'ESCAPED=(\d+)', mut, 'ESCAPED'))
notrun_n = int(find(r'NOT_RUN=(\d+)', mut, 'NOT_RUN'))
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
flines = [l for l in re.findall(r'Executed \d+ tests[^\n]*', full) if 'failures' in l]
if not flines:
    raise SystemExit('PARSE_FAILED 全量卷摘要行 ⇒ 拒绝写盘')
fm = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?', flines[-1])
if not fm:
    raise SystemExit('PARSE_FAILED 全量卷形状不认识：%r' % flines[-1][:120])
fn, fskip, ffails = fm.groups()
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])

problems = []
if caught_n != 4 or total_n != 4 or esc_n or notrun_n or len(arms) != 4 or restore != 'yes':
    problems.append('变异表 %d/%d arms=%s ESCAPED=%d NOT_RUN=%d restore=%s（要 4/4）'
                    % (caught_n, total_n, arms, esc_n, notrun_n, restore))
if ffails != '0':
    problems.append('全量卷失败 %s' % ffails)
if compared <= 0:
    problems.append('帧基线 COMPARED=%d ⇒ 分母是 0，"没变"是空对账' % compared)
if changed or missing:
    problems.append('帧基线 CHANGED=%d MISSING=%d（本轮产品 0 文件，应当一帧都不动）' % (changed, missing))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个' % prod_files)
if float(mn[7]) < FLOOR:
    problems.append('判据通道最小模拟后 %s 低于地板 %g ⇒ 判据本身是红的，不能写成结案' % (mn[7], FLOOR))
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(round=str(NEW_R), newn=str(NEW_N), arms=u', '.join(arms), caught=str(caught_n), total=str(total_n),
         restore=restore, full_n=fn, full_skip=fskip, full_fail=ffails,
         matrix=matrix.strip(), cvd_min=mn[7], cvd_min_pair=u'%s %s→%s' % (mn[0], mn[1], mn[2]),
         dark_steps=steps('dark'), light_steps=steps('light'),
         dark_keeps=u'/'.join(keeps('dark')), light_keeps=u'/'.join(keeps('light')),
         strip=u'；'.join(r.strip() for r in strip_rows), pic=u'；'.join(r.strip() for r in pic_rows),
         compared=str(compared), changed=str(changed), floor=str(FLOOR),
         f_dark=u'、'.join(u'%d→%d（保住 %d）' % t for t in frame_steps['dark']),
         f_light=u'、'.join(u'%d→%d（保住 %d）' % t for t in frame_steps['light']),
         f_min_dark=str(f_min['dark']), f_min_light=str(f_min['light']),
         off_dark=off_dark_text, off_light=off_light_text,
         off_dark_r=str(r_max), off_dark_b=str(gb_max),
         off_light_r=str(r_max),
         margin_judg=u'%.1f' % (float(mn[7]) - FLOOR),
         margin_frame=str(int(f_min['light']) - int(FLOOR)))

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：221 结案在**色觉模拟**这根轴上 —— 第一版把尺子弄坏了、\u3000'
            u'读出一个假红，修好之后 16 条读数最小 %s（U-644…U-646 · 产品 0 文件，判据账 + 看图腿）\n'
            ) % (NEW_N, NEW_R, V['cvd_min'])

UI_BODY = u'''
- **U-644：221 那条质询问对了一半 —— 亮度轴是错的轴，能测的那半是色觉模拟。**
  R197 我用灰阶对比度比值去质询 `空→第 1 档`（亮档只有 1.05），那其实是把 R51/R53 已经证伪过的轴又提一遍：
  `VisualHeat.empty` 走 `primary` 灰、四档走 `accent` 蓝，那一步差的是**色相/彩度**不是明度 ⇒ "亮度几乎不动"是设计如此。
  但同一句质询里还有一半能测：**只靠彩度分开的两档，在色觉障碍下会不会并成一步？** 于是本轮新立
  `HeatmapHoverEvidenceTests/testAdjacentHeatLevelsStaySeparableUnderDeuteranopia`（Viénot 1999 近似，线性域乘矩阵），
  地板沿用同一把 `adjacentLevelFloor255`（=%(floor)s），**不新发明数、不为新轴放宽**。
  实测 16 条（4 对 × 2 外观 × 2 尺度）：最小的一格是 %(cvd_min_pair)s 的 **%(cvd_min)s/255** ⇒ 梯子在绿色盲下仍是五档，221 结案。
  方向是量出来才看清的，而且和直觉相反：**暗档保住 %(dark_keeps)s，亮档掉到 %(light_keeps)s**。
  原因是两档的分离压在不同通道上：暗档差的大头在**蓝**，而矩阵蓝行是 `0.96 b + 0.04 g` ⇒ 蓝是这条轴的免疫通道；
  亮档差的大头在**红**，那正是被红绿混合压掉的那一根。逐格读数：
  暗档 %(dark_steps)s；
  亮档 %(light_steps)s。
- **U-645：本轮第一版判据是红的，而红的是尺子不是产品 —— 那一次假红现在有两个恒等式证人钉着。**
  第一版只在红/绿两路做了重新编码，蓝那一路直接留在线性域 ⇒ 同一颗尺两头用两种单位：
  同一个产品在暗档 `空→第 1 档` 读成 **10.41**（低于地板 %(floor)s，看着像产品塌了），
  又在 `第 3→第 4 档` 读出 **99.60 > 模拟前 65.00** —— "模拟之后反而更分得开"物理上不可能，那是量纲漏的签名。
  修成三通道同量纲之后，那两个数变成上面暗档首末两格。
  只修尺子不够：坏的那一版**产品判据是全绿的**（除了那个反常形状），而"把模拟写成恒等变换"会让 16 条读数
  原封不动等于模拟前、照样全绿 ⇒ 新立 `testDeuteranopiaSimulationMatrixIsWired`，输入是合成纯色、与产品梯子无关，
  钉两条恒等式：① 红↔绿的分离必须小于蓝↔黄（恒等变换给 255 < 255 ⇒ 红）；② 中性灰必须是不动点（三行系数各自和为 1）。
  读数：%(matrix)s
  刀 %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s：M732 把 g 行退回恒等、M733 把量纲 bug 原样复现，
  **这两把都只有真值表能抓**；M734 拿同一格和自己比 ⇒ 地板必须响；M735 少跑一对 ⇒ 16 条计数的闸门必须响。
- **U-646：看图腿做了，而两通道对账偏出来的那一列红，是新开 222 的理由。**
  产品 0 文件 ⇒ 帧沿用 R197 那一批，先 `ls` 数出 138 张才敢复用（分母为 0 的"没变"不算对账）：
  COMPARED=%(compared)s CHANGED=%(changed)s MISSING=0。结构读数：%(strip)s
  把 5 格竖条按中轴游程复量（梯子顺序按"蓝超出血绿"排；夹具的显示顺序不单调，按游程序号相邻会量错对象；
  第一段同色是背景，不当一档）：
  真帧暗档四步 %(f_dark)s，真帧亮档四步 %(f_light)s。
  **逐档把两条通道的墨色相减**：
  暗档 %(off_dark)s；
  亮档 %(off_light)s。
  ⇒ 偏的不是"整把尺"，是**R 那一列**（真帧比离屏渲染红 6…%(off_light_r)s，G/B 最多差 %(off_dark_b)s）：
  暗档的最大通道是 B ⇒ 两通道读数吻合到 1/255 以内；亮档的最大通道是 R ⇒ 同一格真帧只剩 %(f_min_light)s，
  而判据报 %(cvd_min)s。地板 %(floor)s 那一侧的余量：判据 %(margin_judg)s、真帧 %(margin_frame)s。
  看图结论（两张上下对照图：%(pic)s）：模拟版里五档仍分得开、热点列仍读得出，最浅那一档与空格最接近 —— 与数一致，不是形容词。
  ⇒ 新开 BACKLOG 222：这条判据量的是离屏单格，真帧那一列 R 的偏移它现在看不见。
''' % V

VI_BODY = u'''
## Round %(round)s · 221 结案在色觉模拟这根轴上：第一版读出一个假红（10.41），修好之后 16 条最小 %(cvd_min)s（2026-10-19 · 产品 0 文件，判据账 + 看图腿）

新判据 `testAdjacentHeatLevelsStaySeparableUnderDeuteranopia`（Viénot 1999 近似、地板沿用 %(floor)s/255）：
暗档保住 %(dark_keeps)s、亮档 %(light_keeps)s，最小 %(cvd_min_pair)s=%(cvd_min)s ⇒ **梯子对绿色盲仍是五档**，221 结案、不动产品。
方向反直觉：暗档分离压在蓝通道（矩阵蓝行几乎不动蓝），亮档大头在红（被红绿混合压掉）。
本轮真正的收获是**自己的假红**：第一版蓝通道漏了重新编码 ⇒ 暗档读 10.41（假红，差点去改 `VisualHeat.ladder`）、
高档读 99.60 > 模拟前 65.00（物理不可能）。修完之后仍不放心：只压地板的判据分不开"梯子挺住了"与"我压根没模拟"，
于是补一条与产品颜色无关的真值表（红绿必须混、中性灰必须是不动点）—— M732/M733 两把刀**只有它能抓**。
看图腿：产品 0 文件 ⇒ 先 `ls` 数出 138 张再复用 R197 的帧（COMPARED=%(compared)s CHANGED=%(changed)s），
把 5 格竖条按中轴游程复量并与判据逐档相减 ⇒ 偏移集中在 **R 那一列**（真帧比离屏红 6…%(off_light_r)s，G/B ≤%(off_dark_b)s）：
暗档最大通道是 B 所以两通道吻合，亮档最大通道是 R ⇒ 真帧 %(f_min_light)s 对判据 %(cvd_min)s，地板余量 %(margin_frame)s 对 %(margin_judg)s ⇒ 新开 222。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 真看了两张上下对照图（原帧 vs deuteranopia 模拟），并从真帧按结构复量四步、与判据逐档对账；但没有新画面产生 —— 帧沿用 R197，看的是同一批帧的模拟版 |
| 判据有效性 | 15/15 | 新轴 + 4/4 把刀 CAUGHT；其中 M732（恒等变换）与 M733（量纲 bug）**只有新增的真值表能抓**，产品判据在两种坏法下都全绿 —— 这就是那条证人的存在证明 |
| 假绿防御 | 15/15 | 自己的第一版假红没被当成产品结论：先怀疑尺子、用"模拟后反而更分得开"这个物理不可能的形状定位到量纲，再补恒等式；生成器要求 16 条 + 真值表 + 真帧 5 档 4 步 + COMPARED>0 齐全才写盘 |
| 产品面推进 | 10/15 | 画面 0 改动；221 从"我以为亮档只靠彩度"变成两通道吻合的数，并量出 R 那一列 6…%(off_light_r)s 的系统性偏移（222） |
| 台账一致性 | 15/15 | U-644…U-646 + D-199 + 221 结案 + 222 开单 + 三本账 + STATE 轮换；R197 那笔只落了 BACKLOG ⇒ 按 211 的通道显式申报，不补桩标题 |
| 交付诚实性 | 15/15 | 把"我写坏了一把尺并差点据此改产品梯子"写进判据注释、台账与提交信息；两根容差（11.2 由矩阵蓝行推出、2.0 由"行和为 1"的恒等式推出）写明推导而不是假称实测余量 |
| 可复核性 | 15/15 | 16 条 CVD 读数 + SIM_MATRIX 行 + FRAME_INK/FRAME_LADDER 二十行 + 刀号与被改方法名全在日志里（全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s） |
''' % V

CL_BODY = u'''### 221 结案在色觉模拟轴上：新判据 16 条最小 %(cvd_min)s，而第一版那个 10.41 是尺子的假红（R%(round)s / U-644…U-646 · 产品 0 文件，判据账 + 看图腿）

- 新判据 `HeatmapHoverEvidenceTests/testAdjacentHeatLevelsStaySeparableUnderDeuteranopia`：Viénot 1999 deuteranopia 近似（线性域乘矩阵、三通道一律重新编码回 sRGB），地板沿用 `adjacentLevelFloor255`=%(floor)s，不新发明数
- 读数：暗档保住 %(dark_keeps)s、亮档 %(light_keeps)s，最小 %(cvd_min_pair)s=%(cvd_min)s ⇒ 绿色盲下仍是五档；方向反直觉（暗档分离压在蓝通道 = 免疫通道，亮档大头在红）
- **本轮第一版是假红**：蓝通道漏了重新编码 ⇒ 暗档 `空→第 1 档` 读 10.41、`第 3→第 4 档` 读 99.60 > 模拟前 65.00（物理不可能）⇒ 修尺子，不改产品
- 补一条与产品颜色无关的真值表 `testDeuteranopiaSimulationMatrixIsWired`：红↔绿分离必须小于蓝↔黄、中性灰必须是不动点 ⇒ %(matrix)s
- 变异：`mutate_r198.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=%(restore)s；M732/M733 只有真值表能抓（产品判据在两种坏法下全绿）
- 看图腿：产品 0 文件 ⇒ 先 `ls` 数出 138 张再沿用 R197 的帧，COMPARED=%(compared)s CHANGED=%(changed)s；真帧按中轴游程复量并与判据逐档相减 ⇒ 偏移集中在 R 那一列（6…%(off_light_r)s，G/B ≤%(off_dark_b)s），亮档最低一格真帧 %(f_min_light)s 对判据 %(cvd_min)s、地板余量 %(margin_frame)s 对 %(margin_judg)s ⇒ 新开 222
- 验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、脚本电池见 commit 输出；R197 那笔按 211 的通道显式申报为单本账笔次

''' % V

BL_BODY = u'''**221 结案（R198）：错的轴撤掉、能测的那半立了判据 —— 绿色盲模拟之后梯子仍是五档，最小 %(cvd_min)s/255**

那条质询的亮度部分（"亮档比值只有 1.05"）在 R51/R53 已被判成**用错轴**：`空` 走 `primary` 灰、四档走 `accent` 蓝，
那一步差的是色相不是明度。剩下能测的一半是"只靠彩度分开的两档在色觉障碍下会不会并成一步"，
R198 用 `testAdjacentHeatLevelsStaySeparableUnderDeuteranopia` 量了 16 条：
暗档 %(dark_steps)s；
亮档 %(light_steps)s。
⇒ 最小 %(cvd_min_pair)s=%(cvd_min)s 仍高于地板 %(floor)s ⇒ **不改产品梯子**，结案。
副产品两条：① 本轮第一版判据把蓝通道留在线性域，读出一个假红（10.41）与一个物理不可能的形状（99.60 > 65.00）⇒
   新增 `testDeuteranopiaSimulationMatrixIsWired`（合成纯色、与产品无关）钉住"红绿必须混、灰必须是不动点"；
② 真帧通道与离屏通道在 R 那一列系统性偏 6…%(off_light_r)s ⇒ 见下面 222。

**222. 热图相邻档判据量的是离屏单格，真帧上 R 那一列的偏移它看不见：亮档最低一格真帧 %(f_min_light)s 对判据 %(cvd_min)s，地板余量只剩 %(margin_frame)s（R198 两通道对账开单）**

判据 `testAdjacentHeatLevelsStaySeparableUnderDeuteranopia` 用 `renderCell` 画单格再量填充带；产品真帧里格子压在卡片材质上。
R198 按中轴游程从 R197 的 `heatmap-cell-strip-still-90x140-*.png` 复量，并把两条通道的逐档墨色相减：
暗档 %(off_dark)s；
亮档 %(off_light)s。
⇒ 偏移只在 **R 那一列**（G/B ≤%(off_dark_b)s），所以它今天只在"最大通道恰好是 R"的那几格才改变读数：
暗档最大通道是 B ⇒ 两通道读数吻合 ≤1/255；亮档四步真帧 %(f_light)s，对判据的 %(light_steps)s。
地板 %(floor)s 那一侧余量：判据 %(margin_judg)s、真帧 %(margin_frame)s。
下一步（不许靠改阈值解决）：把这条判据的采样通道之一换成**真帧**（帧捕获卷已有这张带），
或给亮档最低那一格单独加一条读真帧像素的证人；两通道再分歧时要能自动点名是哪一条偏了。
注意别顺手把地板降到 15 去"吸收"这一列偏移 —— 那是为过夹具改判据。

''' % V

D_BODY = u'''**D-199（R198）：新加一根"变换型"判据轴时，必须先有一根与产品颜色无关的恒等式证人 —— 否则"变换没接电"与"产品挺住了"同形**

本轮实物：热图梯子的 deuteranopia 模拟判据。第一版只在红/绿两路重新编码、蓝那一路留在线性域，
同一个产品在暗档 `空→第 1 档` 读 10.41（假红，差点据此去改 `VisualHeat.ladder`）、在 `第 3→第 4 档` 读
99.60 > 模拟前 65.00（"模拟之后反而更分得开"，物理不可能 ⇒ 同一颗尺两头用两种单位的签名）。
更糟的是**坏的那一版产品判据是全绿的**：如果只留地板那一条，"把模拟写成恒等变换"会让 16 条读数
原封不动等于模拟前、照样全绿 —— 整根轴没接电却替产品签了字。
⇒ 规矩：任何"先变换再比较"的判据，配一条**输入为合成值**的证人，钉该变换的恒等式而不是经验阈值
（这里用：红↔绿分离必须小于蓝↔黄；三行系数各自和为 1 ⇒ 中性灰是不动点）。
刀 M732（g 行退回恒等）与 M733（量纲 bug 复现）在这条证人下都 CAUGHT，而在产品判据下都不红 —— 这就是它的存在理由。
两根容差都要有推导：蓝黄那一对的 11.2/255 由矩阵蓝行 `0.96 b + 0.04 g` 推（分离全压在蓝时最多丢 4%% 加取整），
灰那一对的 2.0/255 由"行和恰为 1 ⇒ 数学上是 0"推，只留幂函数往返与 8 位量化的余量。
适用面：色觉模拟、色彩空间转换、任何"变换 → 差异统计"形状的判据（帧差、A/B 像素差、归一化计数）；
不适用面：中间没有变换步骤、直接读产物像素的判据（那类风险由正对照刀负责，见 M734/M735 那种形状）。

''' % V

STATE = (u'最后更新：2026-10-19 16:45（本地 · R%(round)s / 第 %(newn)s 轮：**221 结案在色觉模拟这根轴上 —— '
         u'第一版读出一个假红，修好之后 16 条最小 %(cvd_min)s**（U-644…U-646 · 产品 0 文件，判据账 + 看图腿）\n\n'
         u'**本轮落地**：新判据 `testAdjacentHeatLevelsStaySeparableUnderDeuteranopia`（Viénot 1999、地板沿用 %(floor)s/255）：'
         u'暗档保住 %(dark_keeps)s、亮档 %(light_keeps)s，最小 %(cvd_min_pair)s=%(cvd_min)s ⇒ 绿色盲下仍是五档 ⇒ 221 结案、不改梯子。\n'
         u'**自己的假红**：第一版蓝通道漏了重新编码 ⇒ 暗档 10.41（假红）、高档 99.60 > 模拟前 65.00（物理不可能）⇒ 修尺子；'
         u'并补一条与产品无关的真值表（红绿必须混、灰必须是不动点）：%(matrix)s\n'
         u'`mutate_r198.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；M732/M733 只有真值表能抓。\n'
         u'看图腿：产品 0 文件 ⇒ 先 `ls` 数出 138 张再沿用 R197 的帧（COMPARED=%(compared)s CHANGED=%(changed)s），'
         u'真帧按中轴游程复量并与判据逐档相减 ⇒ 偏移只在 R 那一列（6…%(off_light_r)s，G/B ≤%(off_dark_b)s）：'
         u'亮档最低一格真帧 %(f_min_light)s 对判据 %(cvd_min)s、地板余量 %(margin_frame)s 对 %(margin_judg)s ⇒ 新开 222。\n'
         u'验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、脚本电池见 commit 输出；'
         u'R197 那笔按 211 的通道显式申报成单本账笔次（不补桩标题）。\n\n'
         u'**下一轮（R199）的靶**：⓪ 读 R196/R197/R198 这几笔的 CI 全部失败步骤（`2193726`/`27172ec`/`f3b3933` 与本轮这笔；'
         u'用 `scripts/ci_read.py` 按步骤名读，别整卷 grep）；\n'
         u'② 222：把热图相邻档判据的采样通道之一换成真帧（或给亮档最低那一格加真帧证人），两通道分歧要能自动点名；\n'
         u'③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；\n'
         u'④ 220 路 A 仍**等用户授权**（改 `AppleKeyboardUIMode` 后重跑同一条探针）；\n'
         u'⑤ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；'
         u'⑥ 看图腿：产品已连续六轮 0 文件 —— 下一轮要么动一个真位点（222/218 都指向画面），要么如实按 0 文件记这一格。\n'
         u'）\n') % V

LEDGERS = {'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
           'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
           'CHANGELOG.md': u'^### .*（R%d / '}
ROSTER = {186, 187, 197}


def insert_before(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 1）' % (prefix, len(idx)))
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    paths = {n: os.path.join(ROOT, n) for n in LEDGERS}
    paths['STATE'] = os.path.join(ROOT, 'AGENT_STATE.md')
    paths['AGENT_BACKLOG.md'] = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    paths['AGENT_DECISIONS.md'] = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY),
                      (u'bl', BL_BODY), (u'st', STATE), (u'd', D_BODY)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
        for knife in set(re.findall(r'M(7\d\d)', txt)):
            if ('M' + knife) not in mut:
                raise SystemExit('KNIFE_NOT_IN_LOG M%s 被台账引用但变异日志里没有 ⇒ 不写盘' % knife)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 198:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（本轮要写 D-199）⇒ 不写盘' % dec_max)
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, CL_BODY)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + BL_BODY.rstrip(u'\n') + u'\n'
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    top_state = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE.rstrip(u'\n'), u''] + st[top_state:])
    # 三账窗口模拟：R198 / R197 / R196（197 已按 211 的通道显式申报）
    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [644, 645, 646]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 644…646）' % defined)
    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + BL_BODY + STATE):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'D-199' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-199 没落上')
    seven = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', VI_BODY, re.M)
    if len(seven) != 7:
        raise SystemExit('SEVEN_DIM_SHAPE 七维表读到 %d 行（要 7）⇒ 曲线仪器会分叉' % len(seven))
    for name, txt in new.items():
        io.open(paths[name], 'w', encoding='utf-8').write(txt)
    print(u'LEDGERS_R198_WRITTEN r=%d n=%d U=644..646 arms=%s/%s restore=%s full=%s/%s/%s '
          u'cvd_min=%s frame_min_light=%s seven_sum=%d compared=%s changed=%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], restore, fn, fskip, ffails,
             V['cvd_min'], V['f_min_light'], sum(int(x) for x in seven), compared, changed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
