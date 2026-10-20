#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R245（第 244 轮 / Round 242）七本账落盘：变异腿靠「换执行器」恢复，六把刀第一次全 CAUGHT。

编号全部现取；写盘事务性（任何断言红 ⇒ 一个字不落盘）。
本轮有结案（280 / 283）也有新开（284 / 285）。
"""
import io, os, re

ROOT = '/Users/wangziyi/Codex_Project0'
UI = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
IT = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
DEC = os.path.join(ROOT, 'AGENT_DECISIONS.md')
BK = os.path.join(ROOT, 'AGENT_BACKLOG.md')
CL = os.path.join(ROOT, 'CHANGELOG.md')
ST = os.path.join(ROOT, 'AGENT_STATE.md')
FR = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')

R, ROUND, RN = 245, 244, 242
UN = ['U-790', 'U-791', 'U-792', 'U-793']
DN = 'D-231'
CLOSED = ['280', '283']
BN = ['284', '285', '286']
VERDICT = u'R245_MUTATE 刀=6 CAUGHT=6 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes'


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def insert_before(lines, pred, new):
    for i, ln in enumerate(lines):
        if pred(ln):
            return lines[:i] + new + lines[i:]
    raise AssertionError('anchor not found')


# ── 0. 现取读数 ─────────────────────────────────────────────────────────────
ui_old = read(UI)
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui_old, re.M)]
d_txt = read(DEC)
d_ids = [int((mm[0] or mm[1]).replace('D-', '')) for mm in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', d_txt, re.M)]
bk_txt = read(BK)
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', bk_txt, re.M)]
st_txt = read(ST)
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st_txt)
prev_r, prev_round = int(m.group(1)), int(m.group(2))
live_verdict = [l for l in io.open('/tmp/r245_mutate2.log', encoding='utf-8').read().split(u'\n')
                if l.startswith(u'R245_MUTATE')]
assert len(live_verdict) == 1, '日志里没有恰好一行总结：%s' % live_verdict
assert live_verdict[0] == VERDICT, '台账要抄的结论与日志现读不同：%s' % live_verdict[0]
assert max(u_ids) + 1 == int(UN[0][2:]), 'U 上界对不上：%d vs %s' % (max(u_ids), UN[0])
assert max(d_ids) + 1 == int(DN[2:]), 'D 上界对不上：%d vs %s' % (max(d_ids), DN)
assert max(b_ids) == int(CLOSED[1]) and int(BN[0]) == max(b_ids) + 1, 'BACKLOG 号对不上：%s' % b_ids[-4:]
assert (prev_r, prev_round) == (R - 1, ROUND - 1), 'STATE 的轮次对不上：%s/%s' % (prev_r, prev_round)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui_old, re.M)) == ROUND - 1, 'UI_AUDIT 最大轮次不是上一轮'

# ── 1. AGENT_UI_AUDIT.md ────────────────────────────────────────────────────
sec = [
    u'## 第 %d 轮（R%d / 第 %d 轮 / Round %d · 2026-10-20）：变异腿靠换执行器恢复 —— 六把刀第一次全部真跑，280/283 结案（%s…%s / %s · %s/%s 结案、新开 %s/%s/%s · 产品 0 文件）'
    % (ROUND, R, ROUND, RN, UN[0], UN[3], DN, CLOSED[0], CLOSED[1], BN[0], BN[1], BN[2]),
    u'',
    u'本轮次对照：与 R244（三条嫌疑排干净、结论是「别再查环境，改用 bash 驱动」）相比，本轮把那句话做完并**验证**：`swift test` / `python3 -m unittest` 改在 shell 里跑，插拔由 `arm_patch.py` 做（needle 命中恰好一次才动手，逐字节还原后复核），本轮第一次 `刀=6 CAUGHT=6 NOT_RUN=0`。产品 0 文件、画面一字未动。',
    u'',
    u'- **%s：280 那朵挡了六轮的「刀跑不起来」，成因定在执行器那一侧，不是源码、不是包状态、不是环境。** 同一句 `swift test --filter UICaptureTests/testModeChipHoverFillIsVisibleOnItsOwnSurface` 在 shell 里 `Executed 1 test, with 0 failures`、`Invalid manifest` 计数 0；经 python `subprocess` 稳定 rc=1 且日志字节数恒定。换成 bash 驱动后基线两种 kind 各自转绿（日志头两行 `基线绿：kind=swift（3 行汇总）` / `基线绿：kind=python（1 行汇总）`），六把全 CAUGHT：%s。三把 Swift 刀（M802 负对照恒真 / M803 矩形挪出窗外 ⇒ 分母地板 / M804 点亮帧换成空闲帧 ⇒ 颗数与占比两条一起红）证明 R242 那格换尺不是换个数字好看；三把 python 刀（M805 摘浅历史闸门 / M806 平涂线压到 0 / M807 地板判定永远说过线）证明 R244 的 D-230 前提与本轮进尺的地板各有牙。' % (UN[0], VERDICT),
    u'- **%s：刀号是身份不是结果 —— 从未跑过的 M798…M801 也算消费掉了，而我第一版没查重。** 新表接着 M798 编号 ⇒ 名册的「跨表唯一」直接拦下（这是对的：一张表登记了四把没插的刀，那四把的号就不许复用）。改号时我用循环 rename（M798→M802、M802→M806）把臂文件自己盖掉了一遍，`.old/.new` 内容错位而 manifest 看不出来 ⇒ 只能整批按最终号重生成，重生成后逐条 `verify` 才继续。规矩：改号一次性按最终号写，不许循环改名。' % UN[1],
    u'- **%s：预检会 import 每张表 —— 而有四张历史表把刀循环写在模块顶层，于是「跑一次预检」= 把历史表的刀真跑一遍（会起 swift test、会插拔源码文件）。** 症状先于解释：这一轮我第一次跑预检，90 秒不返回，进程表里躺着 mutate_needle_precheck.py 与它派生的 swift test（/tmp/r242_base_M798.log 那种 21,663,809 字节的 manifest 诊断就是这么写出来的）。根因不在我自己那张新表：mutate_r235/r236/r238/r241 四张都有顶层 for mid, … in ARMS，import 即执行（mutate_r242 同形状，本轮一起关）。修法是把执行关进「直接运行」那一支（静态抽 needle 不受影响），预检从「≥90s 且会改文件」变成 1.68 秒纯静态。这一条同时纠正我本轮早些时候写下的半句话：影子表让预检恢复秒级 —— 只改自己那张不够，秒级是四张历史表一起关门之后才拿到的。' % UN[2],
    u'',
    u'- **%s：历史变异表的 needle 会因后来的源码修改腐烂，而唯一的发现方式是「再跑一次那张表」—— 本轮是撞上的，不是设计出来的。** M796（R241 那把「稀释吞进 per_pixel」）的锚点原本是 sum(pb[n]) / 3.0) for n in changed]；R244 我给 measure() 加底平涂占比时写了 greys = [int(round(sum(pb[n]) / 3.0) for n in changed] ⇒ 锚点从恰好一次变成两次命中，M796 当场 NOT_RUN（坏的是刀，不是产品）。换成带左半边的整串（现读命中=1）后重跑那张表：`R241_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`。同一跑预检还现读出别的腐烂：mutate_r169 的 M684/M686 命中=0、mutate_r217 的 M750 命中=2、mutate_r229 的 M768 命中=0 ⇒ 预检 exit=1。本轮不顺手修历史锚点（每把都要重跑那张表才确认它还在判原本那件事），新开 %s 逐张处置。' % (UN[3], BN[2]),
    u'',
    u'读数腿：RUN —— `/tmp/r245_mutate2.log`（基线两 kind 绿 + 六行刀 + 一行总结）；`arm_patch.py verify` 六把全部 RESTORE_CLEAN（逐字节），工作树现在只剩本轮新增的仪器文件与既有未跟踪的 `.local/`。',
    u'眼睛腿：NOT-RUN —— 产品 0 文件、没有新帧（帧沿用 R239 那 162 张），本轮没有新的画面判断要做；连续第二轮记 NOT-RUN，不许写成「看过」。',
    u'Swift 腿：部分 RUN —— 跑的是 `--filter UICaptureTests/testModeChipHoverFillIsVisibleOnItsOwnSurface` 一格（三把刀的基线与红都来自它），**`swift build` 0 告警、全量卷、重捕帧、换装本机本轮没跑**，因为 Swift 侧只改了 `Tests/` 里的一格且改后逐字节还原（工作树与 R244 的 Swift 内容一致）。最近的 Swift 全量读数仍是 R242 的 915/44/2。',
    u'未做（逐条）：① 280 的机制本身还是没名字（我只证明了「换执行器就好」，没证明「为什么 python 起就不行」）⇒ 284 之前不写成结案成因；② M798…M801 四把至今一颗没插，新开 %s 用新执行器补跑；③ arms 表的锚点不在静态预检覆盖里（新开 %s）；④ 277 那两处 `pixels > 400` 还没换尺（现在执行器通了，能做）；预检现读的历史表腐烂（M684/M686/M750/M768）本轮只点名不修，新开 %s；⑤ CI 五笔未读（`66ba71f`/`cc1e6be`/`077ac79`/`0a1e649`/`5130564`）；⑥ 产品动效本体仍 0 文件。' % (BN[0], BN[1], BN[2]),
    u'',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith(u'## 第 %d 轮' % (ROUND - 1))]) == 1, '上一轮标题锚点不唯一'
new_ui = '\n'.join(insert_before(lines, lambda l: l.startswith(u'## 第 %d 轮' % (ROUND - 1)), sec))
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了（本轮只该插入）：%s' % missing[:3]
assert new_ui.count(u'## 第 %d 轮' % ROUND) == 1, '新节标题不唯一'
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 4, 'U 定义行少了 4 条'
new_title = [l for l in new_ui.split('\n') if l.startswith(u'## 第 %d 轮' % ROUND)][0]
assert u'%s…%s' % (UN[0], UN[3]) in new_title and (u'R%d' % R) in new_title, '新标题的 U 区间或 R 标签不对'
assert u'结案' in new_title, '本轮有结案项，标题要写'

# ── 2. AGENT_VISUAL_ITERATION.md ────────────────────────────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [11, 14, 14, 8, 13, 14, 14]
assert sum(scores) == 88
it_rows = u''.join(u'| %s | %d/15 |\n' % (d, s) for d, s in zip(dims, scores))
it_sec = (u'\n## Round %d · 变异腿靠换执行器恢复：六把刀第一次全部真跑，280/283 结案（R%d / 第 %d 轮）/ %s / 新开 %s/%s/%s · 产品 0 文件\n\n'
          % (RN, R, ROUND, DN, BN[0], BN[1], BN[2])
          + u'本轮次对照：与 R244（排出三条嫌疑、判「改用 bash 驱动」）相比，本轮把执行器换掉并验证到底：`arm_patch.py`（插拔 + 恰好一次 + 逐字节还原复核）× `arms_r245/manifest.tsv`（臂内容在盘上，不在 python 字符串里）× `mutate_r245.sh`（shell 里跑判据、按 kind 建基线、红名按空格切）× `mutate_r245.py`（影子登记表，让号进名册又不 import 时跑测试）。\n'
          + u'看图腿：读数腿 RUN（`%s`）；眼睛腿 NOT-RUN（产品 0 文件、无新帧）。\n' % VERDICT
          + u'七维度自评：\n| 维度 | 分/满分 |\n' + it_rows
          + u'各维理由：真实视觉审查 11 —— 眼睛腿连续第二轮没跑，没有新画面可判也不许记成没缺陷；'
            u'判据有效性 14 —— 三把 Swift 刀把 R242 换尺的三根牙（负对照 / 分母地板 / 点亮帧）各自钉回单点可红，三把 python 刀钉住 D-230 与地板判定；扣 1 是 277 那两处地板还挂着；'
            u'假绿防御 14 —— `NOT_RUN=0` 是这条腿六轮以来第一次，且「抓错格=0」不是自说：M802 只允许红负对照那一格，红名按空格切后逐条对过表；扣 1 是 arms 表的锚点不在静态预检覆盖里（285）；'
            u'产品面推进 8 —— 连续 0 产品文件，本轮连判据也只是恢复没新增判据面；'
            u'台账一致性 13 —— 七本一支脚本、编号现取、结论行由日志现读并断言与台账要抄的那行逐字相同；'
            u'交付诚实性 14 —— Swift 腿写成「部分 RUN」并点明没跑的四件事（build 0 告警 / 全量卷 / 重捕 / 换装），280 的机制仍标未命名；'
            u'可复核性 14 —— 执行器是可复用形状（manifest.tsv 一行一把刀），下一轮加刀不必再写 driver；扣 1 是它还没进任何自动闸门。合计 **88**/105。\n')
new_it = it_old + it_sec
assert new_it.count(u'## Round %d ·' % RN) == 1, 'Round 标题不唯一'
assert new_it.split(u'## Round %d ·' % RN)[-1].count(u'合计 **88**/105') == 1, '新节里没有本轮的合计行'
assert len(re.findall(r'^\| (?:%s) \| \d+/15 \|' % u'|'.join(dims),
                      new_it.split(u'## Round %d ·' % RN)[-1], re.M)) == 7, '自评表不是 7 行'

# ── 3. AGENT_DECISIONS.md ───────────────────────────────────────────────────
dec_line = (u'**%s（R%d）：变异臂的执行通道定为 shell —— 插拔由 `arm_patch.py` 做（needle 命中恰好一次才写、逐字节还原后 verify），'
            u'判据一律用 `bash .scratch/motion-audit-2/mutate_rNNN.sh` 跑；python 侧只做登记（影子表），不许在 import 时执行测试。** '
            u'理由：同一句 `swift test --filter …` 在 shell 里 rc=0、经 python subprocess 稳定 rc=1（R242–R244 排掉符号链接 / stdin / 登录 shell / pty 四条嫌疑），'
            u'继续查「为什么」的成本已经高于绕开的收益，而这条腿一停整轮的假绿防御就没了。'
            u'**换通道不换闸门**：基线不绿就 NOT_RUN 出表、锚点必须恰好命中一次、还原必须逐字节、红名要与臂的期望那一格对得上。'
            u'这一条与 D-155 族（环境差异不许报成代码结论）相反方向应用：那里是「别让环境替产品作证」，这里是「别让执行器的坏替判据的死作证」。'
            u'配套规矩（同轮落地）：预检 import 每张表，而 mutate_r235/r236/r238/r241/r242 把臂循环写在模块顶层，跑预检等于真跑历史表的刀并插拔源码；这些循环一律关进直接运行那一支，预检变成 1.68 秒的纯静态检查。机制仍无名（284 之前不许写成已诊断）。\n' % (DN, R))
new_dec = d_txt.rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**%s（' % DN) == 1

# ── 4. AGENT_BACKLOG.md：280/283 结案追记 + 新开 284/285 ─────────────────────
bk_lines = bk_txt.split('\n')
for n in CLOSED:
    hits = [j for j, l in enumerate(bk_lines) if l.startswith(u'**%s. ' % n)]
    assert len(hits) == 1, '%s 那条不唯一：%s' % (n, hits)
note280 = (u'  结案追记（R%d）：执行器换成 shell（D-231）之后一次就破 —— `arms_r245/manifest.tsv` 六把 M802…M807 全部 CAUGHT，'
           u'`%s`。所以成因归到「python 作为父进程起 swift 驱动」这一侧。但机制仍未命名（为什么 python 起会重放同一份 manifest 诊断、'
           u'而 shell 起不会），这条不许写成「已诊断」，另开 %s 时保留。' % (R, VERDICT, BN[0]))
note283 = (u'  结案追记（R%d）：bash 驱动落地 = `arm_patch.py`（patch|restore|verify，needle 恰好一次）+ `mutate_r245.sh`（按 kind 建基线、'
           u'基线不绿整表 NOT_RUN、红名按空格切、逐把还原后 verify）。本轮新加的三格（地板判定 / 平涂前提 / 真帧 standing 判据）里前两把有刀（M806/M807），'
           u'第三格（真帧 standing）仍是合成对照撑着 —— 它要的是帧通道，runner 半属于 275。M798…M801 那四把不在本轮表里，拆给 %s 补跑。' % (R, BN[0]))
for n, note in ((CLOSED[0], note280), (CLOSED[1], note283)):
    j = [k for k, l in enumerate(bk_lines) if l.startswith(u'**%s. ' % n)][0]
    bk_lines = bk_lines[:j + 1] + [note] + bk_lines[j + 1:]
new_items = [
    u'',
    u'**%s. 用 R%d 的 shell 执行器补跑 `mutate_r242.py` 那四把（M798/M799/M800/M801，登记六轮、一颗没插）：'
    u'臂内容搬到 `arms_rNNN/manifest.tsv` 形状，四把各自 CAUGHT 之后才允许把 280 的追记升级成「机制已命名」；'
    u'同一条 python-subprocess 通道的失败原因仍未解释，不许因为「换 shell 就好了」就当成诊断完成（R%d 新开）**' % (BN[0], R, R),
    u'**%s. 影子登记表的锚点不在静态预检覆盖里：`mutate_needle_precheck.py` 是 import 表 + 抽 python 字面量，'
    u'看不见 `arms_*/*.old` 文件里的 needle（它如实报「不在覆盖里」，所以是薄而不是坏）。'
    u'要么加一支按 `manifest.tsv` 列读 needle 的预检并与 `arm_patch.py` 的「恰好一次」闸门对账，'
    u'要么在名册里显式登记这张表的覆盖缺口（不许静默）（R%d 新开）**' % (BN[1], R),
    u'**%s. 预检现读的变异表腐烂逐张处置：mutate_r169 的 M684/M686 命中=0、mutate_r217 的 M750 命中=2、mutate_r229 的 M768 命中=0（本轮只点名没修）。处置只有两种：换锚点重跑那张表并登记新的 CAUGHT，或显式退役那张表并从名册摘掉 ——不许留成「预检恒红」，也不许留成「锚点存在但没人跑」。M796 是同一族第一个样本，本轮已按前者修好（R245 新开）**' % (BN[2],),
]
new_bk = '\n'.join(bk_lines).rstrip('\n') + '\n' + '\n'.join(new_items) + u'\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + BN, 'BACKLOG 形状/编号变了'
assert new_bk.count(u'  结案追记（R%d）' % R) == 2, '结案追记不是恰好两条'

# ── 5. CHANGELOG.md ─────────────────────────────────────────────────────────
cl_lines = read(CL).split('\n')
idx = [j for j, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个：%d' % len(idx)
cl_sec = [
    u'',
    u'### Changed（R%d / 第 %d 轮 / Round %d · 变异腿换到 shell 执行器：六把刀第一次全 CAUGHT）' % (R, ROUND, RN),
    u'',
    u'- 新执行器（`.scratch/motion-audit-2/`）：`arm_patch.py` 做插拔（needle 命中恰好一次才写、`restore` 后 `verify` 逐字节复核），`arms_r245/manifest.tsv` 一行一把刀（臂内容存成 `.old/.new` 文件而不是 python 字符串），`mutate_r245.sh` 在 shell 里跑判据（`swift test --filter` / `python3 -m unittest -v`），按 kind 各建一次基线、基线不绿整表 NOT_RUN，红名按空格切并与「期望那一格」对账。',
    u'- 结果：`%s`（日志 `/tmp/r245_mutate2.log`）。M802 两态差判定换恒真 ⇒ 负对照红；M803 矩形挪出窗外 ⇒ 分母地板红；M804 点亮帧换成空闲帧 ⇒ 颗数与占比两条一起红；M805 摘浅历史闸门；M806 平涂线 0.70→0.0；M807 地板判定永远说过线。' % VERDICT,
    u'- `mutate_r245.py` 是影子登记表（只 load manifest），因为 `mutate_needle_precheck.py` 会 import 每张表 —— 表若在 import 时执行测试，预检从秒级变成十几分钟。已登记进名册 TABLES。',
    u'- 预检关门（D-231 配套）：mutate_r235/r236/r238/r241/r242 五张表的臂循环关进直接运行那一支，mutate_needle_precheck.py 现在是纯静态（1.68s，不再起测试、不再改文件）。',
    u'- 一把腐烂的历史刀修好并重新证明：mutate_r241.py 的 M796 锚点因 R244 给 measure() 加占比行而两次命中（NOT_RUN），换成整串后 R241_MUTATE 刀=3 CAUGHT=3 NOT_RUN=0 RESTORE_CLEAN=yes；同跑现读出 r169/r217/r229 三张表各自的锚点腐烂，新开 286 逐张处置。',
    u'- 台账与规矩两处新明记：刀号是身份不是结果（未跑过的 M798…M801 也算消费，撞号要查重）；改号不许循环 rename（本轮把 `.old/.new` 盖错位一次，整批重生成后才继续）。',
    u'- 产品侧 0 文件；`swift build` 0 告警 / 全量卷 / 重捕帧 / 换装本机本轮 NOT-RUN（Swift 只动 `Tests/` 里的一格且已逐字节还原）。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == u'## [Unreleased]']) == 1, 'Unreleased 变成两个'
assert (u'### Changed（R%d' % R) in new_cl

# ── 6. AGENT_STATE.md ───────────────────────────────────────────────────────
head_new = u'## R%d 状态（第 %d 轮 / Round %d · 2026-10-20）' % (R, ROUND, RN)
st_lines = st_txt.split('\n')
j = [k for k, l in enumerate(st_lines) if l.startswith(u'## R') and u'状态（' in l][0]
assert st_lines[j] != head_new, 'STATE 顶层标题已经是本轮'
st_lines[j] = head_new
blk = [
    u'',
    u'最后更新：2026-10-20 10:20（本地 · R%d / 第 %d 轮 / Round %d）：**变异腿换 shell 执行器恢复，六把刀第一次全 CAUGHT**（%s…%s · %s · 280/283 结案、新开 %s/%s/%s · 产品 0 文件，眼睛腿连续第二轮 NOT-RUN）' % (R, ROUND, RN, UN[0], UN[3], DN, BN[0], BN[1], BN[2]),
    u'',
    u'**本轮落地**：`arm_patch.py` + `arms_r245/manifest.tsv` + `mutate_r245.sh` + `mutate_r245.py`（影子登记表，已进预检名册）；`%s`；三把 Swift 刀钉回 R242 换尺的三根牙，三把 python 刀钉住 D-230 平涂前提与地板判定。脚本电池按规矩在台账落盘之后跑，那一次的读数写进本笔提交信息，不在此预填。' % VERDICT,
    u'',
    u'**下一轮（R%d / 第 %d 轮 / Round %d）的靶**：' % (R + 1, ROUND + 1, RN + 1),
    u'⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询、也别在账里写问号 commit）。未读五笔：`66ba71f`（R244）、`cc1e6be`（R243）、`077ac79`（R242 收尾）、`0a1e649`（R242 主体）、`5130564`（R242 STATE 成对）；本笔 push 之后现取再登记。要读的仍是 BACKLOG 276 结案追记那四件事：① STEP[9] `SOURCES_CELL_HISTORY … 处置=` 是否 skip→judge（278）；② STEP[17] modechip 那朵是否消失 + runner 自印 `两态变化=X/Y 占比=Z`（279）；③ `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275，runner 的地板数就从这行取）；④ skip 数本机 3 / runner 2 的成因。这一跑还要看 `HOVER_DIFF_BASE … 底众数占比=` —— runner 的底若被判成不平涂，说明 D-230 的前提在 runner 上真的需要。',
    u'① 做 277：现在执行器通了，把 `UICaptureHarness.swift` 其余两处 `pixels > 400`（段按钮/玻璃圆那一族 `:5159`、设置行 `:5236`）换成 `bandChanged` + 分母地板 + 负对照，各配一把刀；这一步要跑 `swift build`（0 告警）与捕获卷，Swift 腿不能再记 NOT-RUN。',
    u'② 做 284/285/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；给 `manifest.tsv` 的锚点补一支按列读的预检。',
    u'③ 动效本体：产品文件连续多轮 0。真靶候选要按 282 的口径重判后再定 —— 悬停那一族已过线（撤销），剩下能改的是**没有两态帧**的位点（`DetailView.swift:609` 与 14 个无静置态的名字）：先补夹具与静置帧，再判要不要加反馈。不许为了破 0 纪录加动效。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 274 runner 半 / 275 / 277 / 278 / 279 / 281 / 282 / 284 / 285；用户闸门 220 路 A、228②、265。',
    u'',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (R, ROUND), 'STATE 第一行最后更新不是本轮：%s' % (mm.groups(),)
assert u'本笔=`?' not in new_st, 'STATE 里不许留问号 commit'
assert all(l in new_st for l in st_lines if l.startswith(u'## 第') or l.startswith(u'**下一轮')), 'STATE 旧行丢了'

# ── 7. AGENT_FINAL_REPORT.md ────────────────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-%d' % max(u_ids), u'U-31 … U-%s' % UN[-1][2:])
m_rep = re.search(u'变异臂累计到 \\*\\*(M\\d+)\\*\\*', new_fr)
if m_rep:
    new_fr = new_fr.replace(m_rep.group(1), u'M807')
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R%d，%d 轮自评' % (RN, RN))
print('LEDGERS_R245_FINAL_REPORT 计数=%s' % (u'CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R245 七本落盘：UI(第 %d 轮)/IT(Round %d)/DEC(%s)/BK(结案 %s,%s;新开 %s,%s)/CL(R%d)/ST(R%d)/FR(U-%s)'
      % (ROUND, RN, DN, CLOSED[0], CLOSED[1], BN[0], BN[1], R, R, UN[-1][2:]))
