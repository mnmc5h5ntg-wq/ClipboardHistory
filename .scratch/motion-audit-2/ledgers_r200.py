#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R200 的台账批写：看图腿（浮层/菜单栏四张帧的行带读数）+ R198/R199 两跑 CI 的验收读数。

数字一律从日志解析：行带来自 /tmp/r200_visual.log，CI 来自 /tmp/r200_ci.log（两跑的 `ci_read.py steps` 正文）。
门：① 四张帧必须都量到（缺任一张 ⇒ 看图腿记 NOT-RUN，拒绝写盘）；
② 两跑的 conclusion 必须**读得到**（空字符串＝未读，不许写成"绿了"）；
③ 电池 Ran>0 且 OK；④ 最新一节 U 定义恰好 650/651/652；⑤ 三账窗口 R200/R199/R198 齐；⑥ 产品 0 文件。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'vis': '/tmp/r200_visual.log', 'ci': '/tmp/r200_ci.log', 'bat': '/tmp/r200_battery.log'}
NEW_R, NEW_N = 200, 202
RUNS = {'R198': ('39225680017', '3740c51'), 'R199': ('39227062038', 'a7f16c1')}


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


vis = read(L['vis'])
ci = read(L['ci'])
bat = read(L['bat'])

band_hdr = re.findall(r'^BANDS (\S+) 尺寸=(\d+)x(\d+) 行带=(\d+)', vis, re.M)
if len(band_hdr) != 4:
    raise SystemExit('REFUSE_TO_WRITE 看图腿只量到 %d/4 张帧' % len(band_hdr))
if 'BANDS_OK' not in vis:
    raise SystemExit('REFUSE_TO_WRITE 看图腿读数器自己没签 OK')
bands_by_frame = {n: int(c) for n, w, h, c in band_hdr}
if bands_by_frame.get('quickpick-typed-420x300-light.png') != 3:
    raise SystemExit('REFUSE_TO_WRITE 亮档 typed 那帧行带数不是 3 ⇒ 我对方象的描述要重写')
band_lines = [l.strip() for l in vis.splitlines() if l.startswith('y=')]

concls = {}
for tag, (run, sha) in RUNS.items():
    m = re.search(r'RUN=%s conclusion=(\w+)' % run, ci)
    if not m or not m.group(1):
        raise SystemExit('REFUSE_TO_WRITE %s 那跑（run %s）结论读不到 ⇒ 不许写成已验收' % (tag, run))
    body = ci.split('=== %s run' % tag, 1)
    steps = re.findall(r'STEP\[(\d+)\] ([^\n]*?) ⇒ (\w+)', body[1]) if len(body) > 1 else []
    concls[tag] = (run, sha, m.group(1), [(n, s, c) for n, s, c in steps if c != 'success'])
bad = re.findall(r'^(?:FAIL|ERROR): (\S+)', bat, re.M)
ran_hits = re.findall(r'^Ran (\d+) tests', bat, re.M)
if not ran_hits:
    raise SystemExit('PARSE_FAILED 电池 Ran 行 ⇒ 拒绝写盘')
ran = int(ran_hits[-1])
ok = re.search(r'^OK', bat, re.M) is not None
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])
problems = []
if not ok or ran <= 0 or bad:
    problems.append('电池 Ran=%d OK=%s 红=%s' % (ran, ok, bad))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

fmt = lambda t: u'%s（run %s ↔ commit %s）失败步骤：%s' % (
    t[2], t[0], t[1], u'、'.join(u'STEP[%s] %s⇒%s' % s for s in t[3]) if t[3] else u'无')
V = dict(round=str(NEW_R), newn=str(NEW_N),
         r198=fmt(concls['R198']), r199=fmt(concls['R199']),
         r199_conc=concls['R199'][2], r198_conc=concls['R198'][2],
         n_typed=str(bands_by_frame['quickpick-typed-420x300-light.png']),
         n_hover=str(bands_by_frame['quickpick-hover-420x300-dark.png']),
         n_list=str(bands_by_frame['quickpick-list-420x300-light.png']),
         n_menu=str(bands_by_frame['menubar-recommendations-320x320-dark.png']),
         band_sample=u'；'.join(band_lines[:9]),
         battery=u'%d / OK' % ran,
         fixed=u'已不再红' if not concls['R199'][3] else u'**仍红**')

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：看图腿量了浮层与菜单栏那四张帧的行带，\u3000'
            u'并拿到 R198/R199 两跑 CI 的验收读数（U-650…U-652 · 产品 0 文件）\n') % (NEW_N, NEW_R)

UI_BODY = u'''
- **U-650：看图腿有读数了 —— 亮档 typed 那帧只有 %(n_typed)s 条行带，而暗档 hover 那帧有 %(n_hover)s 条。**
  读数器 `.scratch/motion-audit-2/frame_bands_r200.py`（逐行取众数当背景，与背景亮度差 >24 的像素算墨，
  连续成带）：`quickpick-typed-420x300-light` %(n_typed)s 带（查询文字 + 两行结果）、
  `quickpick-hover-420x300-dark` %(n_hover)s 带、`quickpick-list-420x300-light` %(n_list)s 带、
  `menubar-recommendations-320x320-dark` %(n_menu)s 带。前九条带：%(band_sample)s
  ⇒ 我眼睛先给的判断是"亮档结果区下面空得可疑"，量出来是**真的只有两条结果**（不是尺子读不到：
  同一把尺在暗档读出 %(n_hover)s 条，反方向灵）。
- **U-651：那个"可疑的空白"不是新发现 —— 查重把它挡在了开单之前。**
  `grep` 决定台账：D-122（R63）已经判过"浮层的尺寸所有权必须写出来"，
  固定尺寸 + 结果少时留白是那条决定的**结果**，不是漏判。
  ⇒ 本轮不开单。这一格记的是"查重挡下了一次重复开单"这个动作本身
  （R88 那次我开完 123 才发现 D-090/D-094/R39 早已判过同一件事；这次是先查后开，所以只留一行）。
- **U-652：R199 那次登记翻面的验收读数到了。**
  R198 那跑：%(r198)s
  R199 那跑：%(r199)s ⇒ 第 16 步 %(fixed)s
  这一格只写 runner 自己打出来的东西：翻面是不是真把八跑连红修断了，以上面这行为准，
  不写"应该好了"。电池 %(battery)s。
''' % V

VI_BODY = u'''
## Round %(round)s · 看图腿：浮层四张帧的行带读数，加 R198/R199 两跑 CI 的验收（2026-10-19 · 产品 0 文件）

四张帧按行带量出来：亮档 typed %(n_typed)s 带（查询文字 + 两行结果）、暗档 hover %(n_hover)s 带、
亮档 list %(n_list)s 带、菜单栏推荐 %(n_menu)s 带 ——
"亮档结果区下面空得可疑"这句眼睛的话被量成**真的只有两条结果**（同一把尺在暗档读出 %(n_hover)s 条 ⇒ 反方向灵，不是量不到）。
那个空白**不开单**：D-122（R63）已判过浮层的尺寸所有权，留白是决定的结果而不是漏判（R88 那次的教训这回挡住了重复开单）。
CI 验收：R198 %(r198)s；R199 %(r199)s ⇒ 第 16 步 %(fixed)s。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 真看了帧（浮层亮档 typed 整张 + 三张同类），并且每句形容词都交出行带读数（%(band_sample)s 的前九条）；扣分在没有新渲染产物 —— 帧沿用 R197，产品连续七轮 0 文件 |
| 判据有效性 | 11/15 | 本轮没有新判据；产出是"查重挡下一次开单"与"CI 验收读数入账"，两条都是判据账的利息不是本金 |
| 假绿防御 | 15/15 | 形容词先过反方向对照（同一把尺在暗档读出 %(n_hover)s 条 ⇒ 亮档的 %(n_typed)s 条不是量不到）；读数器缺帧就 exit 1，生成器缺任一读数拒绝写盘 |
| 产品面推进 | 9/15 | 画面 0 改动；推进的是上一轮修复的验收（第 16 步 %(fixed)s） |
| 台账一致性 | 15/15 | U-650…U-652 + 三本账 + STATE 轮换；两跑的 run↔commit 成对入正文，可复查 |
| 交付诚实性 | 15/15 | 明写"这一格记的是查重这个动作本身"与"只写 runner 自己打出来的东西，不写应该好了" |
| 可复核性 | 14/15 | 读数器入库（`.scratch/motion-audit-2/frame_bands_r200.py`）、日志路径写明；扣分在帧仍是 R197 那一批，重跑读数器依赖 /tmp 还在 |
''' % V

CL_BODY = u'''### 看图腿四张帧的行带读数 + R198/R199 两跑 CI 的验收（R%(round)s / U-650…U-652 · 产品 0 文件）

- 新读数器 `.scratch/motion-audit-2/frame_bands_r200.py`：逐行取众数当背景，与背景亮度差 >24 算墨，连续成带；缺帧 exit 1
- 读数：亮档 typed %(n_typed)s 带、暗档 hover %(n_hover)s 带、亮档 list %(n_list)s 带、菜单栏推荐 %(n_menu)s 带 ⇒ "亮档下面空得可疑"量成"真的只有两条结果"（反方向对照通过）
- 查重挡下一次开单：浮层固定尺寸与留白已由 D-122（R63）判定 ⇒ 本轮不开单
- CI 验收：R198 %(r198)s；R199 %(r199)s ⇒ 第 16 步 %(fixed)s
- 验证：脚本电池 %(battery)s、产品 0 文件（帧与换装沿用上一遍）

''' % V

STATE = (u'最后更新：2026-10-19 17:15（本地 · R%(round)s / 第 %(newn)s 轮：**看图腿四张帧的行带读数 + '
         u'R198/R199 两跑 CI 的验收**（U-650…U-652 · 产品 0 文件）\n\n'
         u'**本轮落地**：新读数器 `frame_bands_r200.py` 把浮层/菜单栏四张帧量成行带：'
         u'亮档 typed %(n_typed)s 带、暗档 hover %(n_hover)s 带、亮档 list %(n_list)s 带、菜单栏推荐 %(n_menu)s 带；'
         u'"亮档结果区下面空得可疑"被量成"真的只有两条结果"（同一把尺反方向灵 ⇒ 不是量不到）。\n'
         u'**查重挡住一次开单**：浮层固定尺寸与留白已由 D-122（R63）判 ⇒ 不开单，只记这个动作。\n'
         u'**CI 验收读数**：R198 %(r198)s；R199 %(r199)s ⇒ 第 16 步 %(fixed)s。\n'
         u'验证：脚本电池 %(battery)s、产品 0 文件（帧与换装沿用上一遍）。\n\n'
         u'**下一轮（R201）的靶**：⓪ 若 R200 这笔又触发了新 run，成对记在这里再读；\n'
         u'② 222：热图相邻档判据的采样通道换成真帧（或给亮档最低那一格加真帧证人）—— 这是唯一一条**指向画面**的开放项；\n'
         u'③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；\n'
         u'④ 220 路 A 仍等用户授权；⑤ 清账表 47 格未写（BACKLOG 219 的清单），本轮没动；\n'
         u'⑥ 产品已连续七轮 0 文件 —— 下一轮要么动 222 指向的那一格真帧通道，要么如实按 0 文件记。\n'
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
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY), (u'st', STATE)):
        if re.search(r'%\([a-z_0-9]+\)(?!s)', txt):
            raise SystemExit('FORMAT_LEAK %s 有没带 s 的占位符' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, CL_BODY)
    st = old['STATE'].split(u'\n')
    top_state = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE.rstrip(u'\n'), u''] + st[top_state:])
    for name, fmt_ in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt_ % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [650, 651, 652]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 650…652）' % defined)
    seven = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', VI_BODY, re.M)
    if len(seven) != 7:
        raise SystemExit('SEVEN_DIM_SHAPE 七维表读到 %d 行（要 7）' % len(seven))
    for name, txt in new.items():
        io.open(paths[name], 'w', encoding='utf-8').write(txt)
    print(u'LEDGERS_R200_WRITTEN r=%d n=%d U=650..652 seven_sum=%d battery=%s r199=%s fixed=%s'
          % (NEW_R, NEW_N, sum(int(x) for x in seven), V['battery'], V['r199_conc'], V['fixed']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
