#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R233 台账（补记形状）：只往 BACKLOG 末尾追加一节、往 CHANGELOG 的 [Unreleased] 下插一块。

事务性：先全部算完再写盘；任何一条闸门不成立 ⇒ 一个字都不写。
写盘后核验：原文件每一行都必须仍是新文件的**子序列**（R100 那一族："编辑插入"实为替换）。

明记未做：本轮 0 产品文件 ⇒ 未换装本机、看图腿 NOT-RUN、未重捕帧（上一轮 162 帧仍与工作树一致，
但那是 R232 的读数，不是本轮的）；未轮换 AGENT_STATE；未开 U/D 编号；AGENT_VISUAL_ITERATION 未添条目。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
BACKLOG = os.path.join(ROOT, 'AGENT_BACKLOG.md')
CHANGELOG = os.path.join(ROOT, 'CHANGELOG.md')


def sh(cmd):
    p = subprocess.run(cmd, cwd=ROOT, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def read(path):
    with io.open(path, encoding='utf-8') as h:
        return h.read()


# ---------------- 读数（全部现取，不许手抄） ----------------
MUT_LOG = '/tmp/r233_mutate_run.log'
if not os.path.isfile(MUT_LOG):
    sys.exit(u'%s 不在 ⇒ 变异那一卷的正文没落盘，不许写账（也别在这一支里重跑刀：'
             u'它会改被审文件，不能和台账落盘同时发生）' % MUT_LOG)
mut = read(MUT_LOG)
if 'R233_MUTATE' not in mut:
    sys.exit(u'变异读数取不到 ⇒ 不写账：\n%s' % mut)
stats = {}
for key in (u'刀', u'CAUGHT', u'ESCAPED', u'NOT_RUN'):
    i = mut.index(key + u'=')
    j = i + len(key) + 1
    num = u''
    while j < len(mut) and mut[j].isdigit():
        num += mut[j]
        j += 1
    if not num:
        sys.exit(u'变异台账里 `%s=` 后面不是数字 ⇒ 不写账：%s' % (key, mut))
    stats[key] = int(num)
if stats[u'ESCAPED'] or stats[u'NOT_RUN'] or stats[u'CAUGHT'] != stats[u'刀']:
    sys.exit(u'变异表不干净（刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d）⇒ 不开这一节'
             % (stats[u'刀'], stats[u'CAUGHT'], stats[u'ESCAPED'], stats[u'NOT_RUN']))
if 'RESTORE_CLEAN=yes' not in mut:
    sys.exit(u'RESTORE_CLEAN 不是 yes ⇒ 树是脏的，本轮任何读数都不算')

_, prod = sh('git diff --name-only HEAD -- ClipboardHistory/Sources | wc -l | tr -d " " ')
prod_files = int(prod.strip().splitlines()[-1])
if prod_files != 0:
    sys.exit(u'本轮预设是 0 产品文件，实得 %d ⇒ 判据形状要重走（换装、重捕帧），这支脚本不适用' % prod_files)

_, pngs = sh('ls /tmp/shots_r232/*.png 2>/dev/null | wc -l | tr -d " "')
frames = int(pngs.strip().splitlines()[-1])

BACKLOG_TEXT = u"""

## R233 补记（runner 那一朵红的处置 / 253 的"接进 CI"这一半结案 / 新开 260）

**背景**：R232 之后 runner 唯一那朵红（run 39321660036 / STEP[9]「Release script tests」）本轮读到了正文并结案。
正文逐字取出来的尺输出现在是 `scripts/tests/test_surface_left_axes.py` 里的 `RUNNER_PLAIN_SAMPLE`，
不再靠记忆转述。那一跑 `Ran 410 tests / failures=1 / skipped=1`，唯一 FAIL 是
`RealFrameTests.test_working_frames_still_satisfy_the_three_relations`。

**结案（253 剩下那一半：把纯文本那一格也接进按机器的契约）**
- 病根不是阈值：`RealFrameTests` 写死了两件本机才成立的事 —— `assertEqual(0, code)` 加
  `assertIn(u'LEFT_AXIS_VERDICT ok')`、以及 `assertEqual(4, len(rule_rows))`。
  runner 上尺自己打的是 `问题=4 NOT_RUN帧=0`（四条盲区缝在同一个计数里）且**只打了 D 一行**
  （A/B/C 引用的探针都在它的 NOT_RUN 名单里）。也就是说 259 那轮把 `--ci` 那一格改成按机器切片时，
  **同一件事的第二份判定被漏掉了**（R151 那一族：一条规则两份实现互相掩盖，修一处忘一处）。
- 处置：期望由**这一台机器已登记的那一行**推导（`plain_expectation_from_row`：`问题 = hard + not_run`、
  规则行 = 未被盲区探针引用的那些条），两份判定退回成一份。没有把 skip 写成通过、没有抬地板、
  没有删断言；产品那一条轴（`hard`）在两台机器的期望里都钉死为 0，另有独立一格钉这条不许跟着机器放宽。
- 新增 `PlainContractTests` 六格，全都不碰环境、不跑子进程：两行推导必须不同、两张逐字正文各满足
  自己那一行、一份正文不许同时满足对面那行、把期望钉成"人人 ok"必须判不匹配、给没有对象的探针打
  规则行必须判不匹配、计数与名单互相签字那道闸门必须响。
- 变异对照（`.scratch/motion-audit-2/mutate_r233.py`，纯 python 卷）：
  M781 摘掉 `问题=` 里的 not_run / M782 规则行推导反号 / M783 闸门少算真红那一侧 ⇒ 三把都 CAUGHT、
  ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=yes。
- 刀的形状自曝两处（都是我这轮的错，不是产品的）：
  ① M782 第一版把注释 `# 刀刀` 加进了一个跨行括号表达式里 ⇒ 文件导入期 SyntaxError、
  整卷没有 `FAIL:` 行，却因 rc≠0 被我记成 CAUGHT。**崩栈不是结论**：现在这一支要求
  "红必须有名字"，没名字判 NOT_RUN 并让整支出非 0（修刀不修判据）。
  ② 预登记的期望被真产物驳回一次：我以为"计数与名单互相签字"会抓住伪造的规则行，实际不会
  （规则行进不了 `问题=` 计数）—— 抓住它的是画像里单独的 `规则行` 那一根轴。按实记进文档串。

**更正一笔旧账（259 的样本抄录）**：上一版 `RUNNER_SAMPLE` 的第一行
`LEFT_AXIS A 对称 ｜ 浮层/SelectedRow…` 是我手写拼的 —— 而同一份正文里 浮层/选中行药丸 在 NOT_RUN 名单里，
`judge()` 的规矩是"NOT_RUN 只免掉引用了那颗探针的那条关系"，所以那一行在 runner 上**不可能**被打印。
它当时没让任何一格红（解析器只读结论行与名单行），于是注释里那句"逐字抄录"一直在替一份拼出来的证据作证。
现在四张样本（本机/runner × 纯文本/--ci）都由真输出逐字生成，并加了"给没有对象的探针打规则行 = 红"那格当牙。

**260. 把新表登记进 `mutate_needle_precheck.py` 的名册会让预检静默截断：表在导入时真的执行自己那一卷并以 `sys.exit()` 收尾，`SystemExit` 不是 `Exception` ⇒ 穿过那句 `except Exception`，结论行 `NEEDLE_PRECHECK tables=… bad=…` 一次不打而 exit 仍是 0（R233 实测，名册本轮已退回）**

- 实测：我把 `mutate_r231b / r232 / r233` 追加进 `mutate_needle_precheck.py` 的 `TABLES` 之后跑预检，
  它在 r231b 那一支停住 —— 打印的是那支自己的 CAUGHT 行，**没有** `NEEDLE_PRECHECK tables=… bad=…` 结论行，
  而进程 exit code 是 **0**。成因：预检用 `spec.loader.exec_module(mod)` 读臂号，
  而每一支表在导入时**真的执行自己那一卷**并以 `sys.exit()` 收尾；`SystemExit` 不是 `Exception`，
  穿过那句 `except Exception` ⇒ 整支预检在名册中途退出，剩下的表与两条汇总闸门一次都没跑。
- 后果分两半：登记新表 = 让预检少跑若干支（包括"仓库现状必须 0 重复"那格），而且报告看起来像成功。
  本轮已把名册退回 `mutate_r230`（`git status` 干净），并显式记：**r231b / r232 / r233 不在名册覆盖里**，
  它们的臂号唯一性只由 `cross_table_ids` 那条扫全部 `mutate_r*.py` 的路保证。
- 候选修法（未做，需要先分辨"表该不该在导入时有副作用"）：给每支表加 `if __name__ == '__main__':` 守卫，
  或让预检 `except BaseException` 并把 SystemExit 记成该支的 NOT_RUN。两条都会改到既有 68 支表的行为，
  所以留作单独一轮，配"登记一张会 self-exit 的假表 ⇒ 预检必须仍然打出结论行且 exit≠0"的证人。

**未做的检查（NOT-RUN，别读成通过）**
- 看图腿：本轮产品文件 0 个（`git diff --name-only HEAD -- ClipboardHistory/Sources | wc -l` = 0），
  画面一字未变 ⇒ 没有新东西可看，记 NOT-RUN；帧目录 /tmp/shots_r232 仍有 %d 张（R232 的读数，不是本轮重捕）。
- 全量 `swift test`：本轮未跑（Sources/ 未动；上一笔读数 passed=863 skipped=44 failed=0 属 R232 那笔的账）。
- 未换装本机（同上，没有可换的改动）。
- 台账：未轮换 `AGENT_STATE.md`、未开 U/D 编号、`AGENT_VISUAL_ITERATION.md` 未添整轮条目（补记形状）。
- runner 验收：本轮修复的 runner 结论**待读**（成对号写进下一轮第 ⓪ 条）。
""" % frames

CHANGELOG_TEXT = u"""### 判据：纯文本那一格也不再拿本机的能力当另一台机器的地板（R233 / 253 的"接进 CI"结案）

- run 39321660036 在 runner 上唯一那朵红读到了正文：`scripts/surface_left_axes.py` 在不带 `--ci`
  的调用里把「硬违反」与「尺没有对象」缝进同一个 `问题=` 计数 ⇒ 那四条环境盲区让它 exit 1，
  而上一轮只把 `--ci` 那一格改成按机器切片，**同一件事的第二份判定漏了**。
- 现在两格由同一行机器画像推导：`问题 = hard + not_run`、规则行 = 未被盲区探针引用的那些条；
  产品那一条轴（`hard`）在两台机器都钉死 0，另有独立一格钉它不许跟着机器放宽。没抬地板、没删断言。
- 新契约卷 `PlainContractTests` 六格不碰环境就能红；三把刀 M781 / M782 / M783 全 CAUGHT、
  ESCAPED=0、NOT_RUN=0、RESTORE_CLEAN=yes。
- 两处形状自曝：M782 第一版让被审文件在导入期 SyntaxError，rc≠0 却没有 `FAIL:` 行 ⇒ 这一支现在
  要求"红必须有名字"，否则判 NOT_RUN 并出非 0；上一轮那张 `RUNNER_SAMPLE` 样本的第一行是我手拼的
  （runner 上那条关系根本不会打行），四张样本已改为由真输出逐字生成，并加了会红的牙钉住这种拼法。
- 新开 260：把新表登记进预检名册会让预检在导入那张表时静默截断（表的 `sys.exit()` 穿过
  `except Exception`），结论行不打而 exit 仍是 0 ⇒ 名册本轮退回，欠一条带证人的修法。

"""


def splice_under_unreleased(src, block):
    marker = u'## [Unreleased]'
    i = src.index(marker)
    j = src.index(u'\n', i) + 1
    return src[:j] + block + src[j:]


def check_no_line_eaten(before, after, path):
    it = iter(after.splitlines())
    nxt = next(it, None)
    for line in before.splitlines():
        while nxt is not None and nxt != line:
            nxt = next(it, None)
        if nxt is None:
            sys.exit(u'%s：原文件有一行在新文件里消失了 ⇒ 回滚，不写这一笔' % path)
        nxt = next(it, None)


backlog_before = read(BACKLOG)
changelog_before = read(CHANGELOG)
if u'R233 补记' in backlog_before:
    sys.exit(u'BACKLOG 里已经有 R233 补记那一节 ⇒ 别写第二遍')
if u'R233 / 253 的"接进 CI"结案' in changelog_before:
    sys.exit(u'CHANGELOG 里已经有 R233 那一块 ⇒ 别写第二遍')
# 这一支的锚点形状要**读出来**，不许照抄注释：本机实测两位数的老条目是裸的 `123. `，
# 而 R200 之后的三位号条目写成行首加粗 `**259. …**`（`test_ledger_ids` 的 ITEM 正则只认前者，
# 所以这一格不能拿它当依据）。取不到任何条目 = 红，而不是 ValueError 或 0。
ids = [int(m.group(1)) for m in re.finditer(r'^\*\*(\d{3})\. ', backlog_before, re.M)]
if not ids:
    sys.exit(u'BACKLOG 里一条 `**NNN. ` 定义行都没数到 ⇒ 这份账的形状变了，不写')
max_id = max(ids)
if max_id != 259:
    sys.exit(u'BACKLOG 现有最大编号=%d（数到 %d 条），本轮假设 259 ⇒ 形状要重看，不写' % (max_id, len(ids)))
if u'**260. ' in backlog_before:
    sys.exit(u'BACKLOG 里已经有 260 的定义行 ⇒ 本轮的"新开 260"会造出同号两份正文，不写')

backlog_after = backlog_before.rstrip(u'\n') + u'\n' + BACKLOG_TEXT
changelog_after = splice_under_unreleased(changelog_before, CHANGELOG_TEXT)

check_no_line_eaten(backlog_before, backlog_after, BACKLOG)
check_no_line_eaten(changelog_before, changelog_after, CHANGELOG)

with io.open(BACKLOG, 'w', encoding='utf-8') as h:
    h.write(backlog_after)
with io.open(CHANGELOG, 'w', encoding='utf-8') as h:
    h.write(changelog_after)

print(u'LEDGERS_R233 ok｜BACKLOG+%d行 CHANGELOG+%d行｜变异 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE=yes'
      u'｜产品文件=%d（⇒ 未换装、看图 NOT-RUN）｜帧盘上=%d'
      % (backlog_after.count(u'\n') - backlog_before.count(u'\n'),
         changelog_after.count(u'\n') - changelog_before.count(u'\n'),
         stats[u'刀'], stats[u'CAUGHT'], stats[u'ESCAPED'], stats[u'NOT_RUN'], prod_files, frames))
