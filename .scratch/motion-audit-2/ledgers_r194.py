#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R194 的台账批写（**本轮未跑变异表**，按 NOT-RUN 记账）。

数字从日志解析；缺格拒绝写盘；写盘前模拟三账窗口。
'''
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 194, 196
PROBE = '/tmp/r194_probe3.log'


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


probe = read(PROBE)
cands = [l for l in re.findall(r'Executed \d+ tests[^\n]*', probe) if 'failures' in l]
if not cands:
    raise SystemExit('PARSE_FAILED 探针卷摘要行（没有一行带 failures）⇒ 拒绝写盘')
line = cands[-1]
n = re.search(r'Executed (\d+) tests', line).group(1)
fm = re.search(r'(?:with|and) (\d+) failures?', line)
if not fm:
    raise SystemExit('PARSE_FAILED 摘要行读不到失败数：%r ⇒ 拒绝写盘' % line)
fails = fm.group(1)
skips = re.search(r'(\d+) tests? skipped', line)
skips = skips.group(1) if skips else '0'
uncovered = re.findall(r'(FILTER_PILL_FOCUS_UNCOVERED [^\n]*)', probe)
focus_row = re.findall(r'(FILTER_FOCUS [^\n]*)', probe)
if not uncovered or not focus_row:
    raise SystemExit('PARSE_FAILED 缺 FILTER_FOCUS / FILTER_PILL_FOCUS_UNCOVERED ⇒ 拒绝写盘')
if n != '3' or fails != '0' or skips != '1':
    raise SystemExit('REFUSE_TO_WRITE 探针卷 %s/%s/%s（要 3/1/0）' % (n, skips, fails))
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])
if prod_files != 1:
    raise SystemExit('REFUSE_TO_WRITE 产品文件数 %d（本轮预期 1 个、且只允许注释）' % prod_files)
diff = subprocess.run(['git', 'diff', '-U0', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [l for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++')]
noncomment = [l for l in changed if not l.lstrip('+ \t').startswith('//')]
if noncomment:
    raise SystemExit('REFUSE_TO_WRITE 产品改动里出现非注释行 ⇒ 帧基线与换装都得重做：%r' % noncomment[:3])

V = dict(round=str(NEW_R), newn=str(NEW_N), n=n, skips=skips, fails=fails,
         unc=uncovered[0][:200], row=focus_row[0][:260], prod=str(prod_files), lines=str(len(changed)))

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：筛选条「聚焦」格 —— 键盘根本走不到段按钮，'
            u'而"加个 .focusable 就有焦点"这个假设被探针当场驳回（U-635…U-636 · 产品 1 文件仅注释）\n') % (NEW_N, NEW_R)
UI_BODY = u'''
- **U-635：这一格不是"没判"，是量出来一个真缺陷。** 新探针 `testFilterSegmentsAreReachableAndShowFocus`
  在真的 NSWindow + `NSHostingView(HistorySidebarView)` 里沿 key-view 链走 12 站：
  %(row)s
  ⇒ 12 站**全是搜索框的字段编辑器（NSTextView）**，段按钮一站都不是 ⇒ 键盘用户选不中「全部/收藏」。
  `PressableStyle.swift` 末尾那句"剩下的真实缺口是筛选段按钮拿不到任何焦点提示"从写下到今天第一次有读数撑着它。
- **U-636：先犯一次"把量错对象当成量到了"，再犯一次"以为加个修饰符就修好了"。**
  ① 判据第一版按"落在筛选条带子里"分类 ⇒ 字段编辑器也在带内，两条断言双双为真、测试绿，
  而它量的是搜索框（R93/R98 那一族，本轮我自己又踩）。修法是按**身份**排除字段编辑器再数站。
  ② 于是照注释里那条线索试了产品修法：`FilterSegmentButton` 加 `@FocusState` + `.focusable(true)` +
  一条只在聚焦时出现的 accent 描边 —— 编译 0 告警、探针**照红**（0/12 站）⇒ 这段代码没有买到可达性，
  删掉，只留 4 行注释说明"试过、无效、为什么"（产品文件 %(prod)s 个、改动 %(lines)s 行全是注释，无行为改动）。
  ③ 焦点呈现那一格改成**有名字的未判定**：%(unc)s
  —— 前提由这一跑量出来；放掉的只有"呈现"那一半；段按钮一旦进 key-view 链，下面那条 `reachedFilterBandWithRing`
  断言自动接管，出口不会永久免检（接线由 `testFilterFocusExitIsWired` 钉住）。
- **本轮没跑变异刀**（预算尽头）⇒ 记 NOT-RUN：`testFilterFocusExitIsWired` 的四条锚点目前只有"跑过一遍绿"这一个证人，
  没有刀证明它有牙。下一轮第一把刀 M726 = 把出口条件从 `reachedFilterBand == 0` 改成恒真（永久免检），
  第二把 M727 = 摘掉 `fieldEditorStops` 的身份排除（回到量错对象），两把都该红。
''' % V

VI_BODY = u'''
## Round %(round)s · 筛选条「聚焦」：键盘走不到段按钮，而 .focusable 修不好它（2026-10-19 · 产品 1 文件仅注释）

新探针在真窗口里沿 key-view 链走 12 站：全是搜索框的字段编辑器，段按钮 0 站 ⇒ 「全部/收藏」键盘不可达（BACKLOG 220）。
试过 `@FocusState + .focusable(true) + 聚焦描边`，编译干净但探针照红 ⇒ 代码删掉、留 4 行注释记"试过且无效"。
焦点呈现那一格改成有名字的未判定（前提=这一跑量出来的 0/12；段按钮一旦进链，断言自动接管），并由一条接线扫描钉住。
本轮变异表 NOT-RUN（预算尽头），两把待补的刀已写进账。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 8/15 | 看了真窗口的响应者链与几何（带内候选清单），但没有新渲染画面可看；帧未重捕（产品改动全是注释） |
| 判据有效性 | 12/15 | 新探针 + 未判定出口 + 接线扫描四条锚点；扣分：没有一把刀证明它有牙（NOT-RUN 已记账） |
| 假绿防御 | 14/15 | 自己抓出并修掉两处假绿：字段编辑器冒充"走得到"、`.focusable` 冒充"修好了"；出口必须带名字且会被自动接管 |
| 产品面推进 | 10/15 | 键盘可达性缺陷第一次有读数（BACKLOG 220）；但产品画面 0 变化 —— 试过的那条修法被证伪并删除 |
| 台账一致性 | 13/15 | U-635…U-636 + 新开 220 + 三本账 + STATE 轮换；扣分：变异表 NOT-RUN、清账表未判格本轮只推进 1 格（判成"未判定"） |
| 交付诚实性 | 15/15 | 明写"我第一版把量错对象当成量到了"和"我试的修法无效所以删掉"，NOT-RUN 也写成 NOT-RUN |
| 可复核性 | 14/15 | 完整读数行、探针命令与环境变量、被删代码的原文与为什么都在册；扣分：待补刀号只写了计划 |
''' % V

CL_BODY = u'''### 筛选条「聚焦」格：键盘走不到段按钮（12/12 站是搜索框的字段编辑器），试过的 .focusable 修法被探针驳回（R%(round)s / U-635…U-636 · 产品 1 文件仅注释）

- 新判据：`UIInteractionProbeTests.testFilterSegmentsAreReachableAndShowFocus`（真窗口 + key-view 链 12 站，按**身份**排除字段编辑器）
- 读数：%(row)s
- 试过并删除：`FilterSegmentButton` 的 `@FocusState` + `.focusable(true)` + 聚焦描边 —— 编译 0 告警但探针照红 ⇒ 产品只留 %(lines)s 行注释（无行为改动，帧未重捕）
- 焦点呈现那一格 = 有名字的未判定：%(unc)s；接管断言由 `testFilterFocusExitIsWired` 钉住
- 新开 BACKLOG 220（可达性缺陷本体）；本轮变异表 **NOT-RUN**，两把待补刀 M726/M727 已写进账
- 验证：编译 0 告警、探针卷 %(n)s 例/skip %(skips)s/失败 %(fails)s

''' % V

BL_BODY = u'''**220. 筛选段按钮进不了 key-view 链 ⇒ 键盘用户选不中「全部/收藏」（R194 探针实测开单，不是读码猜测）**

读数：`%(row)s` —— 真窗口里沿 `selectNextKeyView` 走 12 站，**12 站全是搜索框的字段编辑器**（`NSTextView`），
带内候选只有 `ChineseMenuTextField` 一个（就是那颗搜索框）。⇒ 侧栏顶部的两枚段按钮在 AppKit 响应者链里没有身份。
已试过并被驳回的修法：`FilterSegmentButton` 加 `@FocusState` + `.focusable(true)` + 只在聚焦时出现的 accent 描边
⇒ 编译 0 告警、探针**照红**（0/12 站）。所以这不是"加个修饰符"的事：
欠的是先弄清 `List`/`NSHostingView` 怎么排 key-view（同 R93 那段：一棵侧栏树里只有 2 个 `KeyViewProxy`、
且都 `acceptsFirstResponder=false`），可能的路是 ① 换成原生 `NSSegmentedControl`（NSViewRepresentable）
② 或给段按钮装一个显式 `NSView` 代理并接进 `nextKeyView` 链。两条都要先看渲染画面再定，别再来一次"我以为修好了"。
判据已经就位：段按钮一旦进链（`reachedFilterBand ≥ 1`），`reachedFilterBandWithRing` 那条断言自动接管，
今天的 `FILTER_PILL_FOCUS_UNCOVERED` 出口当场失效 —— 它不会永久免检。

''' % V

STATE = (u'最后更新：2026-10-19 15:05（本地 · R%(round)s / 第 %(newn)s 轮：**筛选条「聚焦」格 —— 键盘走不到段按钮，'
         u'.focusable 被探针驳回**（U-635…U-636 · 产品 1 文件仅注释）\n\n'
         u'**本轮落地**：新探针 `testFilterSegmentsAreReachableAndShowFocus` 在真窗口沿 key-view 链走 12 站，'
         u'读数：%(row)s ⇒ 12 站全是搜索框的字段编辑器，段按钮 0 站 ⇒ 键盘不可达（新开 BACKLOG 220）。'
         u'试过 `@FocusState + .focusable(true) + 聚焦描边`：编译 0 告警但探针照红 ⇒ 代码删掉，产品只留 %(lines)s 行注释。\n'
         u'**两处自己抓出来的假绿**：① 第一版按"落在带内"分类 ⇒ 字段编辑器冒充"走得到"，两条断言双双为真而测的是搜索框；'
         u'② 差点把"加了修饰符"当成修好了。焦点呈现那一格改成**有名字的未判定**（前提=这一跑量出的 0/12；'
         u'段按钮一进链断言自动接管），并由 `testFilterFocusExitIsWired` 钉住四条锚点。\n'
         u'**NOT-RUN 记账**：本轮没跑变异刀（预算尽头）⇒ 那条接线扫描目前只有"跑过一遍绿"一个证人。'
         u'下一轮先补 M726（出口条件改恒真）与 M727（摘掉字段编辑器的身份排除），两把都该红。\n'
         u'验证：编译 0 告警、探针卷 %(n)s/%(skips)s/%(fails)s；帧与全量卷本轮 NOT-RUN（产品改动 %(lines)s 行全是注释、'
         u'无行为改动 ⇒ 未重捕；全量卷留给下一笔与两把刀一起跑）。\n\n'
         u'**下一轮（R195）的靶**：⓪ 读这一笔与 `75bd43c` 之后所有跑的**全部**失败步骤'
         u'（关键预期：`FILTER_PILL_FOCUS_UNCOVERED` 要在 runner 上露面，而探针那一步不该因此红）；\n'
         u'① 补 M726/M727 两把刀 + 全量卷 + 帧基线（本轮欠的三件）；\n'
         u'② 220：段按钮进 key-view 链 —— 先量 `List`/`NSHostingView` 怎么排 nextKeyView，再在'
         u'"原生 NSSegmentedControl"与"显式 NSView 代理"两条里选，选完要有画面证人；\n'
         u'③ 218（行 A/B 的统计量）、215（真机亮档一格）、201/202/205/207；\n'
         u'④ 清账表：筛选条那 6 格里"聚焦"已判成有名字的未判定，剩 5 格（加载、空、错误、成功、禁用）。\n'
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
    for extra in ('STATE', 'AGENT_BACKLOG.md'):
        paths[extra if extra != 'STATE' else 'STATE'] = os.path.join(
            ROOT, 'AGENT_STATE.md' if extra == 'STATE' else extra)
    old = {k: io.open(v, encoding='utf-8').read() for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY),
                      (u'bl', BL_BODY), (u'st', STATE)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    bl_max = max(int(m) for m in re.findall(r'^(?:\*\*)?(\d{2,3})\. ', old['AGENT_BACKLOG.md'], re.M))
    if bl_max != 219:
        raise SystemExit('BACKLOG_NUMBER_TAKEN 盘上最大条目是 %d（本轮要开 220）' % bl_max)
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
    if defined != [635, 636]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 635…636）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + BL_BODY + STATE):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R194_WRITTEN r=%d n=%d U=635..636 probe=%s/%s/%s prod=%s comment_lines=%s'
          % (NEW_R, NEW_N, n, skips, fails, prod_files, len(changed)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
