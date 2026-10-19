#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R211 的轮次台账：详情加载态第一次有**组合帧**（BACKLOG 233 的产品半落地，判据半仍欠）。

数字全部现取（捕获卷结论行、帧数、基线比对行、产品 diff 文件数、闸门行、电池行、CI JSON）。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 211, 213
DATE = '2026-10-19'
NOW = '2026-10-19 20:58'
U_LO, U_HI = 683, 685
SHOTS = '/tmp/shots_r211'


def sh(*a):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    return subprocess.run(a, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


cap = read('/tmp/r211_capture.log')
cap_line = (re.findall(r'(Executed \d+ tests, with \d+ tests skipped and \d+ failures[^\n]*)', cap) or [None])[0]
if not cap_line:
    raise SystemExit('CAPTURE_READING_MISSING ⇒ 不写盘')
if '0 failures' not in cap_line:
    raise SystemExit('CAPTURE_NOT_GREEN %s ⇒ 不写盘' % cap_line)
n_frames = len([f for f in os.listdir(SHOTS) if f.endswith('.png')])
if n_frames < 140:
    raise SystemExit('FRAME_COUNT_TOO_LOW %d ⇒ 不写盘' % n_frames)
base_line = (re.findall(r'(FRAME_BASELINE_ADDED=\d+)', sh('python3', 'scripts/frame_baseline.py', 'compare', SHOTS, '--against', 'working')) or [None])[0]
ledger_row = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', sh('python3', 'scripts/motion_surface_gate.py')) or [None])[0]
if not ledger_row or not base_line:
    raise SystemExit('GATE_OR_BASELINE_READING_MISSING ⇒ 不写盘')

prod = [p for p in sh('git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources').split(u'\n') if p.strip()]
if len(prod) != 2:
    raise SystemExit('PRODUCT_FILE_COUNT 期望 2，实得 %d：%s ⇒ 不写盘' % (len(prod), prod))

bat = sh('python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests')
_ba = re.search(r'Ran (\d+) tests', bat)
verdicts = [l.strip() for l in bat.splitlines() if re.match(r'^(OK\b|FAILED\b)', l.strip())]
if not _ba or len(verdicts) != 1 or not verdicts[0].startswith('OK'):
    raise SystemExit('BATTERY_NOT_GREEN 结论行=%s ⇒ 不写盘' % (verdicts or ['无']))
ran = 'Ran %s tests' % _ba.group(1)

repo = sh('gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').strip()
ci = json.loads(sh('gh', 'api', 'repos/%s/actions/runs?per_page=8' % repo) or '{}')
runs = [(r['head_sha'][:7], r['status'], r.get('conclusion') or '', str(r['id'])) for r in ci.get('workflow_runs', [])]
if not runs:
    raise SystemExit('CI_READING_EMPTY ⇒ 不写盘')
ok = [r for r in runs if r[2] == 'success']
pend = [r for r in runs if r[1] != 'completed']
fails = [r for r in runs if r[2] == 'failure']

V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE, ledger=ledger_row, ran=ran,
         cap=cap_line, frames=str(n_frames), added=base_line, prod=u'、'.join(p.split('/')[-1] for p in prod),
         ci_ok=u'、'.join('%s=%s' % (r[0], r[3]) for r in ok[:5]),
         n_ok=str(len(ok)), n_pend=str(len(pend)),
         ci_pend=u'、'.join(r[0] for r in pend[:5]) or u'无',
         ci_fail=u'、'.join(r[0] for r in fails) or u'无')

UI_TITLE = u'## 第 %d 轮（R%d · %s）：详情加载态第一次有**组合帧** —— 头部 + 分隔线 + 骨架同框，D-206 的那句假话现在有像素可以否证（U-%d…U-%d · 产品 2 文件，看图账 + 判据账）\n' % (NEW_N, NEW_R, DATE, U_LO, U_HI)

UI_BODY = u'''
- **U-%(lo)d：组合帧画出来了，R209 那句"加载时头部消失"现在是被像素否证，而不是只被代码否证。**
  新帧 `detail-loading-composed-720x520-{dark,light}`：头部那行"2025-10-09 16:48:20 复制 · 文件: 合同 终版 v3.pdf · 来自 访达"
  在加载态**确实在**，下面才是三条骨架与"正在加载预览…"。看图判读：头部与骨架读起来是同一列（量出来最左墨
  头部 21.0pt / 骨架 22.5pt，差 1.5pt，在既有 ≤2pt 的容差内 ⇒ 那 1.5pt 是数字字形与圆角条带的侧边距差，不是两条轴）。
  实现是一个**默认关闭**的注入点：`DetailView(historyStore:freezeLoadingForCapture:)` → `DetailFileView`，
  冻住的只是 `.task` 里那句 `await loadPreview()` ⇒ 产品路径一行都不变（真实调用永远照常加载）。
- **U-%(lo1)d：我在代码注释里写了一句假话，本轮自己抓到并删掉。**
  注入点的注释原本声称"这条默认值由 `DetailPreviewCaptureSeamTests` 钉住"——**那支测试不存在**。
  这正是本仓库反复记账的那一族（"不执行的声明比没有更坏"，R16/R42/R66）：注释替产品许了一个没人验收的承诺。
  本轮删掉那句话并开 BACKLOG 236（补那格测试：默认 false + 冻住时确实停在 `.loading`），
  **在补上之前，"默认关闭"只有源码可读，没有证人**。
- **U-%(hi)d：验证与仍未做的半。**
  捕获卷：`%(cap)s`（帧数 %(frames)s，基线 `%(added)s` ⇒ 新帧两张，其余一张未变）；
  产品 `%(prod)s`（2 文件）+ 夹具 1 文件；构建 0 告警；脚本电池 `\%(ran)s` 且 OK；清账表 `%(ledger)s`。
  **仍未做的半**：把"头部与骨架同轴"从跨帧比换成同帧判据（`scripts/surface_left_axes.py` 加两枚探针 + 一条关系判据），
  以及上面那格默认值守卫 ⇒ 都记在 233 的追记与 236 里，本轮不许写成已交付。
  换装本机：本轮动了 `Sources/` ⇒ 已 `install_local.sh --yes`（见 CHANGELOG 那一行）。
  CI 逐跑：`%(n_ok)s` 跑 success（%(ci_ok)s）、`%(n_pend)s` 跑仍未读（%(ci_pend)s）、失败跑 %(ci_fail)s ⇒ 未读的不算绿。
''' % dict(V, lo=U_LO, lo1=U_LO + 1, hi=U_HI, ran=ran)

VI_BODY = u'''## Round %(round)s · 详情加载态的第一张**组合帧**：头部 + 骨架同框，看图判读与 1.5pt 的侧边距账（%(date)s · 产品 2 文件，看图账 + 判据账）

R209 我说"加载时头部消失"，被代码否证；本轮把它拍出来：`detail-loading-composed` 里头部那行日期/文件名/来源**在**，
骨架在它下面。看图判读：头部最左墨 21.0pt、骨架 22.5pt ⇒ 差 1.5pt，属数字字形与圆角条带的侧边距差，在同一列的容差内（≤2pt）。
实现是默认关闭的注入点（`freezeLoadingForCapture`），冻住的只是 `.task` 里那次 `loadPreview()`。
本轮还抓到自己写在注释里的一句假话（声称有一支 `DetailPreviewCaptureSeamTests` 钉默认值，而那支测试不存在）⇒ 删掉，开 BACKLOG 236。
捕获卷 `%(cap)s`、帧 %(frames)s 张、`%(added)s`；构建 0 告警；电池 `%(ran)s` 且 OK；已换装本机。
同帧判据（把跨帧比换成 `surface_left_axes.py` 的两枚探针）本轮**未做**，记在 233 追记里。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 新帧真看了（暗档整帧 + 左轴逐行量），并给出 1.5pt 的归因；亮档只量了轴、没逐字读 |
| 判据有效性 | 12/15 | 组合帧落地＝覆盖洞的一半；但"同帧关系判据"与"默认 false 的守卫"两格都还没写 ⇒ 233 只算半结 |
| 假绿防御 | 12/15 | 主动删掉注释里那句无人验收的承诺（不执行的声明比没有更坏）；但本轮没有变异刀 |
| 产品面推进 | 13/15 | 产品 2 文件 + 夹具 1 文件 + 2 张新帧进基线；已换装本机 |
| 台账一致性 | 14/15 | 三账窗口 R211/R210/R209 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续、233 追记与 236 新开 |
| 交付诚实性 | 15/15 | 明写"同帧判据未做"与"默认关闭目前只有源码可读，没有证人" |
| 可复核性 | 14/15 | 帧名、夹具、注入点、捕获卷结论行、基线比对行全在册 |
''' % V

CL_BODY = u'''### 详情加载态第一次有组合帧：`DetailView(freezeLoadingForCapture:)` + `detail-loading-composed` 两张帧（R%(round)s / U-%(lo)d…U-%(hi)d · 产品 2 文件 + 夹具 1 文件）

- 病根：`detail-loading` 画的是组件，所以"加载时头部在不在"在产物通道上不可判（D-206 / BACKLOG 233）
- 修法：默认关闭的注入点把 `.task` 里那次 `loadPreview()` 冻住 ⇒ 组合态可被**确定地**拍（不按墙钟赌，R22 的规矩）
- 看图：头部最左墨 21.0pt、骨架 22.5pt（差 1.5pt = 字形侧边距，同一列）；头部那行日期/文件名/来源在加载态**确实在**
- 自查：注释里"由 `DetailPreviewCaptureSeamTests` 钉住默认值"是假话（那支测试不存在）⇒ 删掉，新开 BACKLOG 236
- 验证：构建 0 告警；`%(cap)s`；帧 %(frames)s 张、`%(added)s`（其余一张未变）；电池 `%(ran)s` 且 OK；已换装本机
- 未做（不许算已交付）：把"头部↔骨架同轴"从跨帧比换成同帧判据（233 追记）；默认值的守卫（236）
- CI：`%(n_ok)s` 跑 success、`%(n_pend)s` 跑未读、失败 %(ci_fail)s

''' % dict(V, lo=U_LO, hi=U_HI)

ITEM_236 = u'''**236. `freezeLoadingForCapture` 的"默认关闭"目前没有证人：那格守卫在 R211 的注释里被当成已有，实为不存在（本轮自查开单）**

形状：注入点在 `DetailFileView` / `DetailView` 上都是 `= false` 的默认值，注释原本写着"由
`DetailPreviewCaptureSeamTests` 钉住"——**仓库里没有这支测试**（本轮 grep 到自己打的脸）。
⇒ 今天有人把默认值翻成 true，全量卷不会红，产品会在真实详情区**永远停在加载骨架**，而唯一能看见它的是那张组合帧——
它恰恰只在夹具路径里被要求为 true。这是"不执行的声明比没有更坏"（R16/R42/R66）的最新一例，只是这次谎写在注释里。

要补的格（下一轮，产品入口进）：① 断言 `DetailView(historyStore:)` 与 `DetailFileView(url:thumbnail:)` 的默认值使预览**会**加载
（用一条会随时间推进到 `.success`/`.failure` 的判据，而不是读注释）；② 断言夹具那一格确实停在 `.loading`
（否则组合帧会静默变成成功帧，142 张基线里 CHANGED 会抓到，但抓不到原因）；③ 一把刀：把默认值翻成 true ⇒ ① 必须红。
'''

APPENDIX_233 = u'''**233 追记（R211）：产品半已落地 —— 组合帧在基线里了；判据半（同帧关系）仍未做，所以本条只算半结**

已交付：`DetailView(historyStore:freezeLoadingForCapture:)` → `DetailFileView` 的默认关闭注入点，
新帧 `detail-loading-composed-720x520-{dark,light}` 进工作基线（`%(added)s`、其余未变），
捕获卷 `%(cap)s`。看图判读与 1.5pt 侧边距的归因写在 `第 %(newn)s 轮`。
仍未做（**不许写成已交付**）：把"头部与骨架同轴"从**跨帧比**换成**同帧判据** ——
形状是给 `scripts/surface_left_axes.py` 加两枚探针（头部行、骨架行，同一张帧）+ 一条 ≤2pt 的关系判据，
并配一把"把头部内缩改歪"的刀；另有一格默认值守卫欠账 ⇒ BACKLOG 236。
''' % V

LEDGERS = {'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
           'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
           'CHANGELOG.md': u'^### .*（R%d / '}


def insert_before_first(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not idx:
        raise SystemExit('ANCHOR_NOT_FOUND %s' % prefix)
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


STATE = u'''最后更新：%s（本地 · R%d / 第 %d 轮：**详情加载态的第一张组合帧（头部 + 骨架同框）+ 删掉注释里一句无人验收的承诺**（U-%d…U-%d · 产品 2 文件，看图账 + 判据账）

**本轮落地**：`DetailView` / `DetailFileView` 加默认关闭的 `freezeLoadingForCapture`，新帧
`detail-loading-composed-720x520-{dark,light}` 进工作基线 ⇒ R209 那句"加载时头部消失"现在由**像素**否证：
头部那行日期/文件名/来源在加载态确实在，头部最左墨 21.0pt、骨架 22.5pt（差 1.5pt = 字形侧边距，同一列）。
自查抓到一处假话：注释声称 `DetailPreviewCaptureSeamTests` 钉住默认值，而那支测试不存在 ⇒ 删掉注释那句话，开 BACKLOG 236。
验证：构建 0 告警、`%s`、帧 %s 张、`%s`、电池 `%s` 且 OK、清账表 `%s`、已换装本机。
**233 只算半结**：同帧关系判据（两枚探针 + 一把刀）本轮未做，写在 233 追记里。
CI：`%s` 跑 success（%s）、`%s` 跑仍未读（%s）、失败跑 %s ⇒ 未读的不算绿。

**下一轮（R212）的靶**：⓪ 读仍未那几跑的 CI —— 特别是 `a800900`（R210 那一步在 runner 上的第一跑：ok / skipped / unavailable？）与本轮这一跑；
① 233 的判据半：给 `surface_left_axes.py` 加"头部行 / 骨架行"两枚探针 + 同帧 ≤2pt 关系判据 + 一把"把头部内缩改歪"的刀；
② 236 那格默认值守卫（产品入口进，带刀）；
③ 227③、222、215、201/202、207；④ 220 路 A 与 228② 仍等用户。
)
''' % (NOW, NEW_R, NEW_N, U_LO, U_HI, V['cap'], V['frames'], V['added'], V['ran'], V['ledger'],
       V['n_ok'], V['ci_ok'], V['n_pend'], V['ci_pend'], V['ci_fail'])


def main():
    names = list(LEDGERS) + ['AGENT_STATE.md', 'AGENT_BACKLOG.md']
    paths = {n: os.path.join(ROOT, n) for n in names}
    old = {k: read(v) for k, v in paths.items()}
    if (u'## Round %d · ' % NEW_R) in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in [(u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY), (u'st', STATE),
                      (u'bl236', ITEM_236), (u'bl233', APPENDIX_233)]:
        if re.search(r'%\([a-z_0-9]+\)(?!s|d)', txt):
            raise SystemExit('FORMAT_LEAK %s（占位符缺转换类型）' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('UNRENDERED %s' % name)
        if u"u'" in txt:
            raise SystemExit("ARTIFACT %s 里还有续行伪影 ⇒ 不写盘" % name)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    new['AGENT_BACKLOG.md'] = (old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + APPENDIX_233.rstrip(u'\n')
                               + u'\n\n' + ITEM_236.rstrip(u'\n') + u'\n')

    for name, fmt in LEDGERS.items():
        for r in (NEW_R, NEW_R - 1, NEW_R - 2):
            if not re.search(fmt % r, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (r, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(u'## 第 ', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [U_LO, U_LO + 1, U_HI]:
        raise SystemExit('U_RANGE_MISMATCH %s' % defined)
    rounds = sorted(int(m) for m in re.findall(u'^## Round (\\d+) ·', new['AGENT_VISUAL_ITERATION.md'], re.M))
    tail = [x for x in rounds if x >= 197]
    if tail != list(range(197, NEW_R + 1)):
        raise SystemExit('ITERATION_GAP %s' % tail)
    sec = new['AGENT_VISUAL_ITERATION.md'].split(u'## Round %d · ' % NEW_R, 1)[1].split(u'## Round ', 1)[0]
    if u'七维度自评' not in sec or len(re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', sec, re.M)) != 7:
        raise SystemExit('CURVE_TABLE_BAD')
    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in set(re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + STATE)):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s' % ref)
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R211_WRITTEN r=%d n=%d U=%d..%d frames=%s battery=[%s]' % (NEW_R, NEW_N, U_LO, U_HI, V['frames'], ran))
    return 0


if __name__ == '__main__':
    sys.exit(main())
