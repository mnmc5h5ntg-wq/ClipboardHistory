#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R199 的台账批写：连红八跑的 CI 第 16 步读完 —— 病根是我自己 R194 埋的那两张 cannot。

数字一律从日志与名册解析：runner 那两行 NOW_RUNS 原文、名册翻面后的 can/cannot 计数、电池摘要行。
门：① 第 16 步正文里必须真有那两条 NOW_RUNS（翻面的证据，没有就不许写成"按证据翻面"）；
② 名册必须解析得到且 can/cannot 计数为 7/7（翻面前的 5/9 是另一回事，这里钉的是**现在盘上**的形状）；
③ 电池 Ran>0 且 OK（"Ran 0 / OK"是空对账）；④ 最新一节 U 定义恰好 647/648/649；
⑤ 三账窗口 R199/R198/R197 齐（197 走 211 的显式申报）；⑥ 本轮产品必须 0 文件。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'ci': '/tmp/r199_step16.log', 'bat': '/tmp/r199_battery2.log'}
NEW_R, NEW_N = 199, 201
RUN_ID, RUN_SHA = '39220929124', 'f3b3933'
LATE = ["testFilterSegmentsAreReachableAndShowFocus", "testFilterFocusExitIsWired"]


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


def find(pat, text, what):
    hits = re.findall(pat, text)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


ci = read(L['ci'])
bat = read(L['bat'])
now_runs = re.findall(r'(NOW_RUNS [^\n]*⇒ 把登记改成 can[^\n]*)', ci)
named = set(re.findall(r'NOW_RUNS (\w+)：', ci))
if not all(n in named for n in LATE):
    raise SystemExit('EVIDENCE_MISSING 第 16 步正文里没点到那两条 ⇒ 不许翻登记（点名到的是 %s）' % sorted(named))
summary = find(r'(PROBE_COVERAGE_SUMMARY [^\n]*)', ci, '覆盖摘要行')
exp = json.load(io.open(os.path.join(ROOT, 'scripts/probe_coverage_expectations.json'), encoding='utf-8'))['cases']
can = sorted(k for k, v in exp.items() if v['runner'] == 'can')
cannot = sorted(k for k, v in exp.items() if v['runner'] == 'cannot')
if len(exp) != 14:
    raise SystemExit('ROSTER_SIZE 名册 %d 条（要 14）' % len(exp))
for n in LATE:
    if exp[n]['runner'] != 'can':
        raise SystemExit('NOT_FLIPPED %s 还是 %s' % (n, exp[n]['runner']))
    if RUN_ID not in exp[n]['reason']:
        raise SystemExit('REASON_NO_RUNID %s 的理由里没有 run 号 ⇒ 翻面没有出处' % n)
bad = re.findall(r'^(?:FAIL|ERROR): (\S+)', bat, re.M)
# 注意：`find` 不带 re.M，`^Ran` 这种锚在这里永远匹配不到 —— 第一版就是被这条拦住（拒绝写盘，没有半份落盘）
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
if len(can) != 7 or len(cannot) != 7:
    problems.append('名册 can/cannot = %d/%d（要 7/7）' % (len(can), len(cannot)))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(round=str(NEW_R), newn=str(NEW_N), run=RUN_ID, sha=RUN_SHA,
         evidence=u'；'.join(r.strip() for r in now_runs), summary=summary.strip(),
         can_n=str(len(can)), cannot_n=str(len(cannot)),
         can_list=u'、'.join(u'`%s`' % n for n in can),
         late=u'、'.join(u'`%s`' % n for n in LATE),
         battery=u'%d / OK' % ran)

UI_TITLE = (u'## 第 %d 轮（R%d · 2026-10-19）：连红八跑的 CI 第 16 步读完了 —— 病根是我自己 R194 埋的两张 cannot，\u3000'
            u'runner 逐条点名之后按证据翻成 can（U-647…U-649 · 产品 0 文件，CI 账）\n') % (NEW_N, NEW_R)

UI_BODY = u'''
- **U-647：那朵红只有一朵，而且是我自己埋的。** 从 `7e46b49` 到 `f3b3933` 连续八跑 `conclusion=failure`，
  逐跑按步骤名读下来全部是同一个：`STEP[16] On-screen probe coverage floor`。正文里两条硬红：
  %(evidence)s
  ⇒ 这正是 R194 那两条登记里**预先写好的那一格**（"下一跑若 NOW_RUNS 逐条点名它，闸门会当场红在这里 ⇒ 那时按读来的证据翻成 can"）。
  同一份摘要：%(summary)s
  连红八跑而没人读，是前三轮把"⓪ 读 CI"一路推到下一轮的结果 —— 这条债本轮还，且写进 D-200 的适用面。
- **U-648：翻面之后必须同时钉住"夹具的年份"，否则历史日志会替新名册作证。**
  登记翻成 can 之后电池立刻红两条：`test_r94_log_is_green…` 与 `test_todays_expectations_pair_green_with_todays_fixture`。
  两红的成因都是**夹具比名册旧**（R94 那份日志采集时这两条判据根本不存在 —— 它们就列在那份夹具的 queued 名单里）。
  处置分两种，各钉一件事：判历史日志的那格改按**采集当时的登记**判（内存里把这两条覆回 cannot，注释写明为什么）；
  另一格从"一条都不红"改成钉**红的身份** —— 只许 `NOT_RUN` 这一种、且只许恰好落在 %(late)s 这两个名字上。
  旧名字保留：R144 的台账行引用它，改名会让那行账指向不存在的东西。
  ⇒ "今天的登记 + 今天的日志真的绿"这一格从此**没有离线判据**，只有 runner 每推一次自己演一遍 —— 这是真缺口，开 BACKLOG 223。
- **U-649：两笔更正，都关于我自己。**
  ① R198 那笔的提交信息里我把"暗档保住"手抄成 `97/98/96/100/153` —— `153` 是**坏尺子**那次的读数，
     最终版暗档保住只有 97 与 98（台账与日志都是解析出来的，坏的是提交正文）⇒ 这是手抄读数第三次出错，规矩改成：
     提交信息里要引读数就 `grep` 出来贴，不许凭记忆改写。
  ② 本轮第一次用 `--filter "HeatmapHoverEvidenceTests$"` 跑出 `Executed 0 tests` 而 `exit 0` ——
     又一次"分母为 0 的通过"（R140 那一族），差别只在这次的 0 来自**正则锚点**而不是空目录。
     ⇒ 判据卷的过滤器一律不带尾锚，且必须读 `Executed N` 的 N 是否 > 0。
''' % V

VI_BODY = u'''
## Round %(round)s · 读 CI：连红八跑的同一朵红是我自己 R194 埋的两张 cannot，按 runner 的点名翻成 can（2026-10-19 · 产品 0 文件，CI 账）

`7e46b49`…`f3b3933` 八跑全 `failure`，逐跑按步骤名读下来是同一朵：`STEP[16] On-screen probe coverage floor`。
runner 正文逐条点名 %(late)s ——「登记说 runner 跑不了，而这次它下结论了（passed / skipped）⇒ 把登记改成 can」，
而那句话正是 R194 登记里预先写好的出口 ⇒ 按证据翻面（名册现在 can=%(can_n)s / cannot=%(cannot_n)s）。
翻面立刻让两格电池红，成因都是"夹具比名册旧"：判历史日志那格改按采集当时的登记判，
另一格从"一条都不红"改成钉**红的身份**（只许 NOT_RUN、只许那两个名字）。
⇒ "今天的登记 + 今天的日志真的绿"从此没有离线判据，开 BACKLOG 223。
顺带两笔自我更正：R198 提交信息里手抄的"暗档保住 153"是坏尺子那次的读数；`--filter "Class$"` 给 `Executed 0 tests` + exit 0。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 5/15 | 本轮没看图：读的是 CI 正文与名册。帧沿用 R197（产品 0 文件），但"沿用"不等于"看过" —— 这一格低是事实，不是保守 |
| 判据有效性 | 13/15 | 翻面由 runner 自己的点名行驱动（不是我的推断），并把两格夹具判据从"要求绿"改成"钉红的身份"；扣分在没有新增能红的判据，且暴露出 223 那一格根本没有离线证人 |
| 假绿防御 | 14/15 | 拒绝让历史夹具替新名册作证（两种处置分开写）；抓到 `--filter "Class$"` 的"分母为 0 的通过"；生成器要求 NOW_RUNS 原文 + 名册解析 + 电池 Ran>0 才写盘 |
| 产品面推进 | 10/15 | 画面 0 改动，但交付链路实质推进：CI 连红八跑的原因定位并修掉，下一跑第 16 步应当不再红（待 runner 验收，不许提前写成已修好） |
| 台账一致性 | 14/15 | U-647…U-649 + D-200 + 223 开单 + 三本账 + STATE 轮换；R198 那笔提交信息的手抄错在 U-649 显式更正，没有偷偷改历史 |
| 交付诚实性 | 15/15 | 明写"这朵红是我自己埋的、连红八跑是我推了三轮没读"，并把"下一跑才见分晓"留在 STATE 而不是现在就宣布修好 |
| 可复核性 | 15/15 | run 号 %(run)s、commit %(sha)s、NOW_RUNS 原文两行、名册 can 名单、复算命令（`gh run view … --log` 按步骤名过滤）全在账里 |
''' % V

CL_BODY = u'''### 连红八跑的 CI 第 16 步：两张 R194 的 cannot 被 runner 逐条点名，按证据翻成 can（R%(round)s / U-647…U-649 · 产品 0 文件，CI 账）

- 八跑（`7e46b49`…`%(sha)s`）全部 `conclusion=failure`，逐跑按步骤名读下来是同一朵：`STEP[16] On-screen probe coverage floor`
- 证据（run %(run)s 正文）：%(evidence)s
- 处置：`scripts/probe_coverage_expectations.json` 两条 cannot → can，理由里带 run 号与 runner 原话；名册现在 can=%(can_n)s / cannot=%(cannot_n)s
- 连带修两格电池：判历史日志那格改按**采集当时**的登记判；"今天的登记 + 今天的夹具"那格改成钉**红的身份**（只许 NOT_RUN、只许那两个名字），旧测试名保留（R144 台账行引用它）
- 新开 BACKLOG 223：翻面之后"今天的登记 + 今天的日志真的绿"这一格没有任何离线判据，只有 runner 每次推送自己演
- 更正：R198 提交信息里手抄的"暗档保住 …153"是坏尺子那次的读数（最终版只有 97/98）；`swift test --filter "Class$"` 会给 `Executed 0 tests` 而 exit 0
- 验证：脚本电池 %(battery)s、JSON 解析通过、产品 0 文件（帧与换装沿用上一遍）；CI 是否真的不再红要等下一跑第 16 步的读数

''' % V

BL_BODY = u'''**223. 探针覆盖闸门缺一个离线证人：登记翻面之后，"今天的登记 + 今天的日志真的绿"这一格只有 runner 能演（R199 翻面当轮暴露）**

现状：`scripts/probe_coverage_gate.py` 的输入是 runner 那一步写出来的 `/tmp/ui.log`，而这份日志**不入库、不上传**
⇒ 本地只能拿历史夹具判，而历史夹具永远比名册旧（R199 把 %(late)s 翻成 can 之后，
两格夹具判据立刻红在"夹具里没有它们的结论行"上）。
于是名册的每一次翻面都只能靠"推上去看 CI"来验收，而 CI 连红八跑这件事本身说明这条通道会长期没人看。
下一步（便宜的那半优先）：CI 那一步把 `/tmp/ui.log` 与 `probe-floor.log` 作为 artifact 上传
（`actions/upload-artifact`，只含测试名与坐标/颜色数字，**不含任何用户剪贴板原文** —— 这条要先核一遍再传），
然后本地加一格判据：拿**当轮**的 runner 日志 + **当轮**的名册判一次，红就点名红在哪条。
不许用的两种偷懒解法：把 `can` 改回 `cannot`（那是把免检牌塞回抽屉）；把夹具断言改成恒真（那是让守卫闭嘴）。

''' % V

D_BODY = u'''**D-200（R199）：登记翻面要**成对**改判 —— 判历史日志的格按采集当时的登记判，判"今天"的格改成钉红的身份；而"连红八跑"本身要记成债，不是记成背景**

本轮把 %(late)s 从 cannot 翻成 can，证据是 run %(run)s 第 16 步逐条点名的两行原文
（%(evidence)s）。翻面之后电池红两格，两格都**不是**登记翻错了，而是"拿历史日志判现在的名册"：
R94 那份夹具采集时这两条判据还不存在（它们就列在同一份日志的 queued 名单里）。
⇒ 规矩：任何一次登记翻面都要同时处置两类格 ——
① 判**历史**日志的格：在内存里把该条覆回**采集当时**的登记，注释写明"只用于判这份历史日志"；
② 判**当下**的格：不许要求"绿"（历史夹具永远做不到），改成钉**红的身份**：状态词集合恰好 `{{NOT_RUN}}`、
   名字集合恰好等于这次翻面的那几条 ⇒ 多一条少一条都算量错。
两条都是"守卫要读字段不能读散文"（R74）的同一族：判据读的是红名单的**形状**，不是它有没有红。
另一侧的账：CI 连红八跑而三轮都把"⓪ 读 CI"推到下一轮 ⇒ 以后凡是 ⓪ 那一格欠两轮，
就要在 STATE 里把"欠了几跑、最后一跑的 run 号"写成读数（本轮起生效，见 STATE 的下一轮靶 ⓪）。
适用面：探针覆盖闸门、动效地板、捕获闸门这类"登记 + 日志"两头对账的判据；
不适用面：只有一份产物、没有登记通道的判据（那些的正对照是变异刀）。

''' % V

STATE = (u'最后更新：2026-10-19 17:05（本地 · R%(round)s / 第 %(newn)s 轮：**连红八跑的 CI 第 16 步读完 —— '
         u'病根是我自己 R194 埋的两张 cannot，按 runner 的点名翻成 can**（U-647…U-649 · 产品 0 文件，CI 账）\n\n'
         u'**本轮落地**：`7e46b49`…`%(sha)s` 八跑全 failure，逐跑按步骤名读下来是同一朵 `STEP[16] On-screen probe coverage floor`；'
         u'runner 正文逐条点名 %(late)s ⇒ 名册两条 cannot → can（理由里带 run %(run)s 与原话），'
         u'现在 can=%(can_n)s / cannot=%(cannot_n)s。\n'
         u'**连带两格电池**：判历史日志那格改按采集当时的登记判；"今天的登记 + 今天的夹具"那格改成钉红的身份'
         u'（只许 NOT_RUN、只许那两个名字）⇒ "今天的登记 + 今天的日志真的绿"从此没有离线证人，开 BACKLOG 223。\n'
         u'**两笔自我更正**：R198 提交信息里手抄的"暗档保住 …153"是坏尺子那次的读数（最终版只有 97/98）；'
         u'`swift test --filter "Class$"` 会给 `Executed 0 tests` 而 exit 0 ⇒ 过滤器不带尾锚、必须读 N>0。\n'
         u'验证：脚本电池 %(battery)s、JSON 解析通过、产品 0 文件（帧与换装沿用上一遍）；'
         u'**CI 是否真的不再红要等下一跑第 16 步的读数，本轮不提前宣布修好**。\n\n'
         u'**下一轮（R200）的靶**：⓪ 读 R198/R199 两跑的 CI（run 39225680017 = `3740c51` 写这笔时仍 in_progress ⇒ 结论未读；'
         u'本轮这笔的 run 号要成对记在这里）—— **欠账已两轮，按 D-200 把 run 号与欠的跑数写成读数，不许再推一轮**；\n'
         u'② 222：热图相邻档判据的采样通道换成真帧（或给亮档最低那一格加真帧证人），两通道分歧要能自动点名；\n'
         u'③ 218（行 A/B 的统计量 + runner 那份分布）、215（真机亮档一格）、201/202/205/207；\n'
         u'④ 220 路 A 仍**等用户授权**；⑤ 清账表：筛选条剩 5 格；\n'
         u'⑥ 看图腿：本轮 5/15 是**真没看图** —— R200 要么动一个真位点（222 直接指向画面），要么重捕一帧并真看。\n'
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
        if re.search(r'%\([a-z_0-9]+\)(?!s)', txt):
            raise SystemExit('FORMAT_LEAK %s 有没带 s 的占位符' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 199:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（本轮要写 D-200）⇒ 不写盘' % dec_max)
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, CL_BODY)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + BL_BODY.rstrip(u'\n') + u'\n'
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    top_state = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE.rstrip(u'\n'), u''] + st[top_state:])
    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [647, 648, 649]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 647…649）' % defined)
    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + BL_BODY + STATE):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'D-200' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-200 没落上')
    seven = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', VI_BODY, re.M)
    if len(seven) != 7:
        raise SystemExit('SEVEN_DIM_SHAPE 七维表读到 %d 行（要 7）' % len(seven))
    for name, txt in new.items():
        io.open(paths[name], 'w', encoding='utf-8').write(txt)
    print(u'LEDGERS_R199_WRITTEN r=%d n=%d U=647..649 can=%s cannot=%s battery=%s seven_sum=%d'
          % (NEW_R, NEW_N, V['can_n'], V['cannot_n'], V['battery'], sum(int(x) for x in seven)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
