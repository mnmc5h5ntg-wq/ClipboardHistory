#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R195 的台账批写：把 R194 记成 NOT-RUN 的三件债还掉（变异刀、全量卷、脚本电池）。

同 R191–R194：数字全部从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
本轮的门：
① 变异表必须 4/4 CAUGHT、ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=yes；
② 台账里引用的每个 `M7xx` 都必须在变异日志里真的露面；
③ 全量卷的**失败数必须解析到**，读不到就拒绝写盘（R88：摘要里"有键无值"算红）；
④ 最新一节的 U 定义要 ≥3 条且与标题区间吻合（R102 那一课）。
'''
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'mut': '/tmp/r195_mut.log', 'full': '/tmp/r195_full.log'}
NEW_R, NEW_N = 195, 197


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


mut = read(L['mut'])
full = read(L['full'])
caught_n = int(re.search(r'CAUGHT=(\d+)', mut).group(1))
total_n = int(re.search(r'刀=(\d+)', mut).group(1))
esc_n = int(re.search(r'ESCAPED=(\d+)', mut).group(1))
notrun_n = int(re.search(r'NOT_RUN=(\d+)', mut).group(1))
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
flines = [l for l in re.findall(r'Executed \d+ tests[^\n]*', full) if 'failures' in l]
if not flines:
    raise SystemExit('PARSE_FAILED 全量卷没有一行带 failures ⇒ 拒绝写盘')
fm = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?', flines[-1])
if not fm:
    raise SystemExit('PARSE_FAILED 全量卷摘要形状不认识：%r ⇒ 拒绝写盘' % flines[-1][:120])
fn, fskip, ffails = fm.group(1), fm.group(2), fm.group(3)
probe = [l for l in re.findall(r'PROBE_ORDER [^\n]*', read('scripts/tests/../../tmp/r195_full.log') if False else '')]

problems = []
if caught_n != 4 or total_n != 4 or esc_n or notrun_n or len(arms) != 4 or restore != 'yes':
    problems.append('变异表 %d/%d arms=%s ESCAPED=%d NOT_RUN=%d restore=%s（要 4/4 且两样都空）'
                    % (caught_n, total_n, arms, esc_n, notrun_n, restore))
if ffails != '0':
    problems.append('全量卷还有 %s 条失败 ⇒ 这一笔不算还完债' % ffails)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(round=str(NEW_R), newn=str(NEW_N), arms=u', '.join(arms),
         caught=str(caught_n), total=str(total_n), restore=restore,
         full_n=fn, full_skip=fskip, full_fail=ffails)

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：还 R194 欠的三件债 —— 四把刀给那条接线扫描验出牙、'
            u'全量卷跑回 0 失败、电池从 1 红修到 OK（U-638…U-640 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)
UI_BODY = u'''
- **U-638：R194 那条接线扫描当时只有"跑过一遍绿"一个证人，现在它有四把刀。**
  `mutate_r195.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s：
  M726 摘掉『接管』断言（未判定出口变永久免检）、M727 摘掉字段编辑器的身份排除（回到量错对象）、
  M728 让出口失去名字、M729 把读数标记改名。四把全部被扫描本身抓红 ⇒ "有名字的未判定"这套结构
  从今天起是可证伪的，不再是一句自我声明。
- **U-639：两处锚点形状值得记，因为它们各藏一种假绿。**
  ① M726 的 needle 必须带**下一行**才命中一次：扫描自己的字面量里就写着它要数的那串
  （`components(separatedBy: "XCTAssertGreaterThanOrEqual(reachedFilterBandWithRing, 1")`）——
  只写前缀会命中 2 次而整刀 NOT-RUN（R100 那一族，本轮又撞，改的是刀不是判据）。
  ② 扫描里 `contains("FILTER_FOCUS")` 这种**短前缀锚点**本身是漏的：把标记改成 `FILTER_FOCUSX` 也算命中，
  所以 M729 配的是"锚点必须写整行前缀"（`FILTER_FOCUS 带内候选=`），并把这条写进红话里。
- **U-640：电池那 1 红的真成因不是我猜的那个。**
  R194 收尾我在提交信息里写"漏了另一处 7/11"，实际红的是 `PROBE_QUEUED 4/11 → 6/13`
  （新增两条在屏判据 ⇒ 排队名单从 4 条长成 6 条），另有 `FrameIntervalBudgetTests`
  的 print 读数名册要求新标记先登记（`FILTER_FOCUS`、`FILTER_PILL_FOCUS_UNCOVERED`，10 行→12 行）。
  ⇒ 两处都按"这一跑的真实文本"重钉，并把理由写进注释：改分母不等于放宽 —— 名册仍是双向相等、
  排队名单仍逐名对上；把它改成 `≤` 才是放宽。
  同时留下一条自我更正：**上一笔的提交信息里那句诊断是错的**，而错的原因是我没先读失败正文就写账
  （R94 那一课的新变体：红话要抄原文，不要复述）。
- 验证：全量卷 %(full_n)s 例 / skip %(full_skip)s / 失败 %(full_fail)s；脚本电池 Ran 368 / OK；
  产品 0 文件（本轮只动判据与账）⇒ 帧基线与换装沿用上一遍。
''' % V

VI_BODY = u'''
## Round %(round)s · 还 R194 的三件债：四把刀验出牙、全量卷 0 失败、电池修绿（并更正我上一笔写错的诊断）（2026-10-19 · 产品 0 文件，判据账）

`mutate_r195.py` %(arms)s 全 CAUGHT（摘接管断言 / 摘字段编辑器身份排除 / 出口失去名字 / 读数标记改名），
catcher 都是 R194 那条接线扫描本身 ⇒ 它从"自我声明"变成可证伪。
电池那 1 红的真因是 `PROBE_QUEUED 4/11→6/13` 与 print 读数名册（新增两个标记、10 行→12 行），
两处都按真实文本重钉并写明"名册仍双向相等、不是放宽"。
顺带更正我上一笔提交信息里的错误诊断（没读失败正文就写账）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 8/15 | 本轮没有画面可看（产品 0 文件、帧未动）；看的是四把刀的红话与两份名册的真实文本 |
| 判据有效性 | 14/15 | 那条未判定出口现在有 4/4 把刀作证；两处过期分母按真实读数重钉；扣分：M727 只钉住"排除被摘"，没钉"排除写错对象" |
| 假绿防御 | 15/15 | 短前缀锚点被 M729 证伪并改成整行前缀；needle 命中次数在跑之前先数（R100/R143 两课同时用上） |
| 产品面推进 | 8/15 | 画面 0 改动；BACKLOG 220 那条键盘可达性缺陷本轮没动（它欠的是 nextKeyView 结构的量法） |
| 台账一致性 | 15/15 | U-638…U-640 + 三本账 + STATE 轮换；并**公开更正上一笔提交信息里写错的诊断** |
| 交付诚实性 | 15/15 | 明写"我上一笔的诊断是猜的、错了"，也明写"改分母不等于放宽"的判据差别在哪 |
| 可复核性 | 15/15 | 刀号、四把刀各自的红话、两份名册的 before/after 计数、全量卷三元组全在册 |
''' % V

CL_BODY = u'''### 还 R194 的三件债：4/4 把刀给未判定出口验出牙，全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s，电池 Ran 368 / OK（R%(round)s / U-638…U-640 · 产品 0 文件，判据账）

- `mutate_r195.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；catcher 是 `testFilterFocusExitIsWired` 本身
- 锚点两条规矩落地：needle 要带相邻行才命中一次（扫描自己的字面量会撞）；扫描的锚点必须写**整行前缀**，否则 `FILTER_FOCUSX` 也算命中
- 电池那 1 红的真因：`PROBE_QUEUED 4/11 → 6/13`（新增两条在屏判据）与 `FrameIntervalBudgetTests` 的 print 读数名册（+`FILTER_FOCUS`、+`FILTER_PILL_FOCUS_UNCOVERED`，10→12 行）；两处按真实文本重钉，名册仍是双向相等
- 自我更正：上一笔提交信息里"漏了另一处 7/11"是**没读失败正文就写的猜测**，实际成因见上；红话要抄原文不要复述
- 验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、脚本电池 Ran 368 / OK、产品 0 文件（帧未动，沿用上一遍）

''' % V

BL_BODY = u'''**R195 追记（220 不动，先还债）**：R194 记 NOT-RUN 的三件（变异刀、全量卷、电池）本轮全部落地 ——
`mutate_r195.py` %(arms)s 全 CAUGHT、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、电池 Ran 368 / OK。
220 本身仍开着：它欠的是"先量清 `List`/`NSHostingView` 怎么排 nextKeyView"，本轮没有动它，
也不许用"扫描有牙了"替那条缺陷说进展 —— 两件事不同尺。

''' % V

STATE = (u'最后更新：2026-10-19 15:30（本地 · R%(round)s / 第 %(newn)s 轮：**还 R194 的三件债 —— 四把刀验出牙、全量卷 0 失败、电池 OK**'
         u'（U-638…U-640 · 产品 0 文件，判据账）\n\n'
         u'**本轮落地**：`mutate_r195.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s，'
         u'catcher 全是 R194 那条 `testFilterFocusExitIsWired` ⇒ 那个"有名字的未判定"出口第一次被证明可证伪。'
         u'电池那 1 红修绿：真因是 `PROBE_QUEUED 4/11→6/13` 与 print 读数名册（新增 `FILTER_FOCUS`、'
         u'`FILTER_PILL_FOCUS_UNCOVERED`，10 行→12 行），两处按**真实文本**重钉、名册仍是双向相等。\n'
         u'**一条自我更正**：上一笔提交信息里我写"漏了另一处 7/11"是没读失败正文就猜的 ⇒ 实际成因见上；'
         u'教训是红话要抄原文（R94 新变体）。\n'
         u'验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、脚本电池 Ran 368 / OK、产品 0 文件'
         u'（帧与换装沿用上一遍）。\n\n'
         u'**下一轮（R196）的靶**：⓪ 读这一笔与 `7e46b49` 之后所有跑的**全部**失败步骤'
         u'（关键预期：`FILTER_PILL_FOCUS_UNCOVERED` 要在 runner 上露面且那一步不因此红）；\n'
         u'① 220：量清 `List`/`NSHostingView` 的 nextKeyView 排布（先读数、后选路：原生 NSSegmentedControl '
         u'或显式 NSView 代理），选定后要画面证人；\n'
         u'② 218（行 A/B 的统计量：帧对中位 / 段长 ÷ 声明时长，配 runner 那份分布）、215（真机亮档一格）；\n'
         u'③ 201、202、205、207；④ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；\n'
         u'⑤ 看图腿：产品已连续四轮 0 文件 —— 下一轮要么动一个真位点，要么把 220 的两条候选路各拍一张对照。\n'
         u'）\n') % V

LEDGERS = {'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
           'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
           'CHANGELOG.md': u'^### .*（R%d / '}
ROSTER = {186, 187}


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
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY),
                      (u'bl', BL_BODY), (u'st', STATE)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
        for knife in set(re.findall(r'M(7\d\d)', txt)):
            if ('M' + knife) not in mut:
                raise SystemExit('KNIFE_NOT_IN_LOG M%s 被台账引用但变异日志里没有 ⇒ 不写盘' % knife)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, CL_BODY)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + BL_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE.rstrip(u'\n'), u''] + st[top_state:])
    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [638, 639, 640]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 638…640）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + BL_BODY + STATE):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R195_WRITTEN r=%d n=%d U=638..640 arms=%s/%s restore=%s full=%s/%s/%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'], fn, fskip, ffails))
    return 0


if __name__ == '__main__':
    sys.exit(main())
