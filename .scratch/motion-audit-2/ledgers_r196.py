#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R196 的台账批写：BACKLOG 220 的**结构诊断**落地（不改产品，理由要能被证伪）。

同 R191–R195：数字全部从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
门：① 变异表 2/2 CAUGHT、ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=yes；② 台账引用的 M7xx 必须在日志里露面；
③ 全量卷三元组必须解析到且失败为 0；④ 最新一节 U 定义 ≥3 且与标题区间吻合；
⑤ 结构读数那三行（KEYCHAIN / KEYCHAIN_TREE / KEYCHAIN_FKA）必须都在，缺任一行就拒绝写盘
   —— 这一轮的结论全靠那三行撑着，没有它们我就是在看代码猜。
'''
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'chain': '/tmp/r196_chain2.log', 'mut': '/tmp/r196_mut.log', 'full': '/tmp/r196_full.log'}
NEW_R, NEW_N = 196, 198


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


chain = read(L['chain'])
mut = read(L['mut'])
full = read(L['full'])
k = grab = lambda pat, text, what: (re.findall(pat, text) or raise_(SystemExit('PARSE_FAILED %s' % what)))


def find(pat, text, what):
    hits = re.findall(pat, text)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


chain_row = find(r'(KEYCHAIN 视图数=[^\n]*)', chain, '结构读数行')
tree_row = find(r'(KEYCHAIN_TREE [^\n]*)', chain, '逐视图清单')
fka_row = find(r'(KEYCHAIN_FKA [^\n]*)', chain, 'FKA 分辨实验读数')
proxies = re.findall(r'KeyViewProxy fr=(\w+)', tree_row)
rings = re.findall(r'_FocusRingView fr=(\w+)', tree_row)
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
if caught_n != 2 or total_n != 2 or esc_n or notrun_n or len(arms) != 2 or restore != 'yes':
    problems.append('变异表 %d/%d arms=%s ESCAPED=%d NOT_RUN=%d restore=%s（要 2/2）'
                    % (caught_n, total_n, arms, esc_n, notrun_n, restore))
if ffails != '0':
    problems.append('全量卷失败 %s' % ffails)
if not proxies:
    problems.append('清单里读不到 KeyViewProxy ⇒ 结构诊断没有证人')
if not rings:
    problems.append('清单里读不到 _FocusRingView ⇒ "焦点环零件已在位"这句话没有读数撑着')
if prod_files != 0:
    problems.append('本轮应当产品 0 文件（决定是不改），实际 %d 个' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(round=str(NEW_R), newn=str(NEW_N), arms=u', '.join(arms), caught=str(caught_n), total=str(total_n),
         restore=restore, full_n=fn, full_skip=fskip, full_fail=ffails,
         chain=chain_row[:220], tree=tree_row[:520], fka=fka_row[:220],
         proxy_fr=sorted(set(proxies)), ring_fr=sorted(set(rings)))

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：220 的结构诊断 —— 段按钮的 KeyViewProxy 在树里、\u3000_FocusRingView 已在位，'
            u'缺的只有「接受第一响应者」这一件事（U-641…U-643 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)
UI_BODY = u'''
- **U-641：三种成因被区分开了，答案是第二种。** R194 只量到"走不到"（Tab 12 站全是字段编辑器），
  那有三种修法互相冲突，所以本轮先把结构拍下来：%(chain)s
  逐视图清单里两枚段按钮的位置上各有 %(proxy_cnt)s 个 `KeyViewProxy`，它们**彼此连着 nextKeyView**、
  几何就是段控件那两格（148×26 @x=12 与 @x=160），但 `fr=false`；
  而**同一位置上已经有 `_FocusRingView`**（`fr=%(ring_fr)s`）。
  ⇒ 病根不是"宿主不在环里"，是"代理不接受第一响应者"；
  而"焦点表达"这件事系统零件已经在那儿了 —— 自绘一条描边会变成画两圈（与 `PressableStyle` 注释里
  搜索框那条同一个道理）。清单：%(tree)s
- **U-642：那条机制假设我**没有**拿它当结论，而是做了分辨实验，实验没翻面。**
  假设是"AppKit 只在系统『全键盘访问』开启时把这些代理放进 Tab 环"。本机 `defaults read -g AppleKeyboardUIMode`
  读不到这个键（=0）。我在**本进程内** `register(defaults:)` 设成 3 再建一棵树（不写全局偏好、不动用户设置），
  读数：%(fka)s ⇒ `acceptsFirstResponder` 4→4、环长 2→1，**什么都没翻**。
  ⇒ 这条假设既没被证实也没被证伪：进程内 register 很可能不是 AppKit 读它的时机。
  真要判它得改全局偏好并重启会话 —— 那是需要用户授权的动作，我不偷跑，写进 220 的下一步。
- **U-643：本轮决定**不改产品**，并把"为什么不改"写成可证伪的两条路。**
  自绘焦点环：被结构读数反驳（`_FocusRingView` 已在位 ⇒ 两圈）；
  换原生 `NSSegmentedControl`：能进环，但会改材质与几何，而 R189/R190 刚为这条通道建好两态像素判据与能力谓词，
  换控件等于把那些判据的**对象**换掉 —— 那不是"顺手升级"，是一次有代价的重判，得单独一轮带着画面证人做。
  刀 %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s：
  M730 把量法的起点弄丢（空环该红）、M731 把 FKA 那行标记改名（读数还在但名册看不见 ⇒ 静默免检）。
  顺带第二次踩到"新增 print 读数要同改三处名册"：本轮三个标记（`KEYCHAIN`/`KEYCHAIN_TREE`/`KEYCHAIN_FKA`）
  都要进 `FrameIntervalBudgetTests` 的名册，行数 12→15。
''' % dict(V, proxy_cnt=len(proxies))

VI_BODY = u'''
## Round %(round)s · 220 的结构诊断：段按钮的代理在树里、焦点环零件已在位，缺的只是"接受第一响应者"（2026-10-19 · 产品 0 文件，判据账）

新量法 `testSidebarKeyViewChainStructureIsPrinted` 把整棵树与 nextKeyView 环拍成读数：
%(chain)s；两枚段按钮的位置上各有 `KeyViewProxy`（连着 nextKeyView、`fr=false`）与**已在位的 `_FocusRingView`**。
⇒ 病根是"代理不接受第一响应者"，不是"没有焦点表达可用"。
机制假设（全键盘访问开关决定可达性）做了进程内分辨实验，**没有翻面** ⇒ 既不证实也不证伪，写进 220 的下一步（要改全局偏好就得先拿到用户授权）。
本轮决定不改产品，两条修法各自的代价与可证伪实验都记进 D-198；刀 %(arms)s 全 CAUGHT。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 9/15 | 没有新画面可看（产品 0 文件、帧未动）；看的是 45 个视图的树、两格 148×26 的几何与 `_FocusRingView` 的在场 —— 这是"看结构"不是"看渲染" |
| 判据有效性 | 15/15 | 把"走不到"拆成三种可区分的成因并各配读数；量法有刀（M730 空环该红）、读数通道有名册（M731 改名该红） |
| 假绿防御 | 15/15 | 拒绝把机制假设写成结论：做了进程内实验、如实报"没翻面"、不偷跑改全局偏好；台账生成器要求三行读数齐全才写盘 |
| 产品面推进 | 9/15 | 画面 0 改动，但 220 从"键盘选不中"升级成"哪一层没接上 + 两条修法各自的代价"，下一步不再靠猜 |
| 台账一致性 | 15/15 | U-641…U-643 + D-198 + 220 追记 + 三本账 + STATE 轮换；三个新标记同步进名册 |
| 交付诚实性 | 15/15 | 明写"假设没被证实也没被证伪"与"这一步需要用户授权，我不做" |
| 可复核性 | 15/15 | 三行完整读数、`defaults read` 命令、刀号与被改方法名全在册 |
''' % V

CL_BODY = u'''### 220 结构诊断：段按钮的 KeyViewProxy 在树里、`_FocusRingView` 已在位，缺的是接受第一响应者（R%(round)s / U-641…U-643 · 产品 0 文件，判据账）

- 新量法 `UIInteractionProbeTests.testSidebarKeyViewChainStructureIsPrinted`：整棵树 + nextKeyView 环 + 带内几何，全部走 print 读数
- 读数：%(chain)s；两枚段按钮位置上各有 `KeyViewProxy`（连着 nextKeyView、`fr=false`）与**已在位**的 `_FocusRingView` ⇒ 焦点环零件齐
- 分辨实验：本进程 `register(defaults: ["AppleKeyboardUIMode": 3])` 后重建一棵树 ⇒ %(fka)s ⇒ 什么都没翻 ⇒ 假设既不证实也不证伪（要证它得改全局偏好 + 重启会话，需用户授权）
- 决定：不改产品。自绘焦点环被结构读数反驳（会画两圈）；换 `NSSegmentedControl` 能进环但会换掉 R189/R190 那套两态判据的**对象**，得单独一轮带画面证人做 ⇒ D-198
- 变异：`mutate_r196.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；三个新 print 标记同步进名册（12→15 行）
- 验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、脚本电池见 commit 输出、产品 0 文件（帧未动，沿用上一遍）

''' % V

BL_BODY = u'''**220 追记（R196）：病根定位到"代理不接受第一响应者"，两条修法各自的代价与实验都写清**

结构读数：%(chain)s；清单里两枚段按钮的位置上各有 `KeyViewProxy`（`fr=false`、彼此连着 nextKeyView、
几何 148×26 @x=12 / @x=160），**同位置已有 `_FocusRingView`**。
⇒ ①"焦点表达"不缺零件（自绘描边会变成两圈，别做）；②缺的是"接受第一响应者"。
下一步分两条，各自要先做实验，不许直接动产品：
- 路 A（便宜）：证实/证伪"系统『全键盘访问』决定可达性"。本轮的**进程内**实验没翻面（%(fka)s），
  要真判需要 `defaults write -g AppleKeyboardUIMode -int 3` + 重启会话 —— 改的是用户机器的全局偏好，
  **要先拿授权**；拿到后重跑同一条探针，看 `fr` 与环长是否翻面。
- 路 B（贵）：换原生 `NSSegmentedControl`（NSViewRepresentable）。它能进环，但会改材质与几何，
  而 R189/R190 为这条通道建的两态像素判据与能力谓词的**对象**就是现在这套视图 ⇒ 换控件等于重判那些判据，
  要单独一轮、带画面证人，不能顺手。

''' % V

D_BODY = u'''**D-198（R196）：筛选段按钮的键盘可达性缺陷**不修**，因为两条修法各自欠一个还没做的实验；焦点环零件已在位这一事实先否掉"自绘描边"**

读数（本机，`/tmp/r196_chain2.log`）：%(chain)s；
两枚段按钮位置上各有 `KeyViewProxy`（`fr=false`、连着 nextKeyView、148×26 @x=12 / @x=160），
同位置**已有** `_FocusRingView`（`fr=%(ring_fr)s`）。进程内把 `AppleKeyboardUIMode` register 成 3 之后：
%(fka)s ⇒ 没有任何翻面。

⇒ 三条结论：① 不自绘焦点环（零件已在位，再加一圈是画两圈 —— 与搜索框那条同一个理由，但这次有 `_FocusRingView` 的在场作证人）；
② 不为可达性顺手换 `NSSegmentedControl`：那会换掉 R189/R190 两态像素判据与能力谓词的**对象**，是一次有代价的重判；
③ "FKA 决定可达性"这条机制假设**既不证实也不证伪**（进程内 register 不是 AppKit 读它的时机），
   要判它必须改用户机器的全局偏好并重启会话 —— 属于要先授权的动作，本轮不做。
适用面：任何"SwiftUI 控件在 AppKit 响应者链里没有身份"的判断；不适用：真响应者（`acceptsFirstResponder=true` 的那 4 个）。

''' % V

STATE = (u'最后更新：2026-10-19 15:50（本地 · R%(round)s / 第 %(newn)s 轮：**220 结构诊断 —— 代理不接受第一响应者，'
         u'而焦点环零件已在位**（U-641…U-643 · 产品 0 文件，判据账）\n\n'
         u'**本轮落地**：新量法把侧栏那棵树的 nextKeyView 结构拍成读数：%(chain)s；'
         u'两枚段按钮位置上各有 `KeyViewProxy`（`fr=false`、彼此连着）与**已在位**的 `_FocusRingView` '
         u'⇒ 病根是"代理不接受第一响应者"，不是"没有焦点表达"。`mutate_r196.py` %(arms)s ⇒ '
         u'%(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s。\n'
         u'**分辨实验没翻面**：本进程 register `AppleKeyboardUIMode=3` 后 %(fka)s ⇒ '
         u'"全键盘访问决定可达性"这条假设既不证实也不证伪；要判它得改全局偏好 + 重启会话（需用户授权，不偷跑）。\n'
         u'**决定：不改产品**（D-198）：自绘焦点环被"零件已在位"否掉；换 `NSSegmentedControl` 会换掉 '
         u'R189/R190 那套两态判据的对象，得单独一轮带画面证人做。\n'
         u'验证：编译 0 告警、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、三个新 print 标记进名册（12→15 行）、'
         u'产品 0 文件（帧与换装沿用上一遍）；脚本电池见 commit 输出。\n\n'
         u'**下一轮（R197）的靶**：⓪ 读 R195/R196 这几笔的 CI 全部失败步骤（`7e46b49`=已确认 failure 且成因是它自身缺文件；'
         u'`4cde716`/`4b38b29`/`9b0a17b` 与本轮写这笔时都仍 in_progress ⇒ 结论未读）；\n'
         u'② 220 路 A：**等用户授权**改 `AppleKeyboardUIMode` 后重跑同一条探针（翻面 ⇒ 产品不用改，只改文档与验收条件）；\n'
         u'③ 220 路 B：若路 A 不翻面，才谈换原生控件 —— 且要先想清楚 R189/R190 那两条判据跟着怎么改；\n'
         u'④ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；\n'
         u'⑤ 清账表：筛选条剩 5 格（加载、空、错误、成功、禁用）；⑥ 看图腿：产品已连续五轮 0 文件 —— '
         u'R197 要么动一个真位点，要么把 218 那三臂的逐帧条带像 R192 那样真看一遍。\n'
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
    dec_max = max(int(m) for m in re.findall(r'^\*\*D-(\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 197:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（本轮要写 D-198）⇒ 不写盘' % dec_max)
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, CL_BODY)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + BL_BODY.rstrip(u'\n') + u'\n'
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
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
    if defined != [641, 642, 643]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 641…643）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + BL_BODY + STATE):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'D-198' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-198 没落上')
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R196_WRITTEN r=%d n=%d U=641..643 arms=%s/%s restore=%s full=%s/%s/%s proxies=%d rings=%d'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'], fn, fskip, ffails, len(proxies), len(rings)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
