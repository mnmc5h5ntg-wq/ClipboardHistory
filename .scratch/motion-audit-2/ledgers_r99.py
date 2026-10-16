#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R99 的验证段落盘：数字只从 `r99_verify.log` 解析，缺任一格就**拒绝写盘**。

三条规矩都是从栽过跟头的地方抄来的（R96 / R98 各中过一次）：
① 事务性 —— 先整体快照再写，任何一格抛错就全部还原（半份台账比没写更坏）；
② 数字只从日志解析，缺格就拒写（不出现"猜出来的数"）；
③ 渲染完的那一段自己再过一遍 `check_block`：不许残留计时文本、不许有 `（0）`、
   退出码必须是纯数字而不是半句话、不许有 `?`。
插入点用 `rpartition(§9 标题)` 而不是"切到文件末尾"：R98 第一版按后者做，
把 §9/§10 复制了一份出来（已手工修回）。

跑法：LEDGERS_R99_APPLY=1 PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r99.py
退出码：0 = 十格齐全且落盘；非 0 = 拒绝写盘。
"""
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
LOG = REPO + '/.scratch/motion-audit-2/r99_verify.log'
TARGET = REPO + '/AGENT_VISUAL_ITERATION.md'
SHOTS = '/tmp/r99_shots'
MARKER = u'### 9. R98 的 CI：红有名字'
HEAD = u'### 8. 验证（十格，数字只从 `r99_verify.log` 解析）'
TABLE_COUNT = 7

KEYS = ['BUILD_EXIT', 'BUILD_WARNING_LINES', 'TEST_EXIT', 'PROBE_EXIT', 'CAPTURE_EXIT',
        'FRAMES_EXIT', 'PY_EXIT', 'MUT_EXIT', 'LEDGER_EXIT', 'VIS_EXIT', 'SUMMARY_MISSING',
        'VERIFY_OK']


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def grab(text, key):
    """最后一格 = 值。

    不锚进行首：`BUILD_EXIT=0 BUILD_WARNING_LINES=0` 是同一行打出来的两格，
    锚行首会让第二格"读不到"，而"读不到"在这里等于拒写 —— 那是工具的错，不是账的错。
    退出码一律按**纯数字**取：电池那一行把七张表的名字直接接在值后面，
    用 `\\S+` 就会把下一格的开头读进来（R98 pass-2 真发生过）。
    """
    if key.endswith('_EXIT') or key == 'SUMMARY_MISSING':
        m = re.findall(r'%s=(\d+)' % key, text)
    else:
        m = re.findall(r'%s=(\S+)' % key, text)
    if not m:
        sys.exit(u'拒绝写盘：日志里没有 %s= 这一格' % key)
    return m[-1]


def read_verify():
    if not os.path.exists(LOG):
        sys.exit(u'拒绝写盘：没有 %s' % LOG)
    text = rd(LOG)
    v = {k: grab(text, k) for k in KEYS}
    m = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures', text)
    if not m:
        sys.exit(u'拒绝写盘：读不到全量测试的汇总行（Executed … failures）')
    v['TEST_LINE'] = u'%s 例 / %s skip / %s failures' % (m.group(1), m.group(2), m.group(3))
    for key, out_key in ((u'FRAME_BASELINE_CHANGED', 'FRAMES_CHANGED'),
                         (u'FRAME_BASELINE_COMPARED', 'FRAMES_COMPARED'),
                         (u'FRAME_BASELINE_MISSING', 'FRAMES_MISSING')):
        hit = re.search(key + r'=(\d+)', text)
        if not hit:
            sys.exit(u'拒绝写盘：读不到 %s=' % key)
        v[out_key] = hit.group(1)
    pngs = [f for f in os.listdir(SHOTS) if f.endswith('.png')]
    n = int(grab(text, u'帧数'))
    if n != len(pngs):
        sys.exit(u'拒绝写盘：日志的 帧数=%d 与目录里真实的 PNG=%d 对不上' % (n, len(pngs)))
    v['PNG'] = u'%d' % len(pngs)
    for line in text.splitlines():
        if line.startswith('MUT_EXIT=') and 'exit=' in line:
            v['TABLES'] = line
            break
    else:
        sys.exit(u'拒绝写盘：找不到 MUT_EXIT= 那一行（七张变异表的原文）')
    if v['TABLES'].count('MUTATE_TABLE') < TABLE_COUNT:
        sys.exit(u'拒绝写盘：MUT_EXIT 行里只有 %d 张表的原文，期望 %d 张 ⇒ 有表没跑成'
                 % (v['TABLES'].count('MUTATE_TABLE'), TABLE_COUNT))
    # 本轮两条新读数通道必须自己报数（缺任何一条 = 判据没跑，不许被 §8 的"全绿"盖掉）
    for tag, key in ((u'CARD_ABOVE_SUMMARY', 'ABOVE'), (u'CARD_BELOW_SUMMARY', 'BELOW')):
        hit = re.search(tag + r' (.*)', text)
        if not hit:
            sys.exit(u'拒绝写盘：读不到 %s ⇒ 卡片外那两格名单这次没有读数' % tag)
        cells = re.findall(r'=(\d+)', hit.group(1))
        if not cells:
            sys.exit(u'拒绝写盘：%s 后面一格数都没有' % tag)
        v[key] = u'%d 格，全为 %s' % (len(cells), '/'.join(sorted(set(cells))))
    return v


def check_block(block):
    bad = []
    if re.search(r'\bin\s+[0-9.]+\s*s', block):
        bad.append(u'残留了计时文本')
    if u'（0）' in block:
        bad.append(u'出现了空括号计数「（0）」')
    if u'?' in block:
        bad.append(u'出现了 ?（说明有一格没解析出来）')
    for key in (u'BUILD_EXIT', u'TEST_EXIT', u'PROBE_EXIT', u'CAPTURE_EXIT', u'FRAMES_EXIT',
                u'PY_EXIT', u'MUT_EXIT', u'LEDGER_EXIT', u'VIS_EXIT'):
        v = re.search(key + r'=(\d+)(?![0-9A-Za-z_])', block)
        if not v:
            bad.append(u'%s 那一格不是纯退出码' % key)
    # 不锚行首：渲染出来的这一格在 Markdown 表格里，锚行首会让自检对**自己渲染的形状**红。
    m = re.search(r'VIS_EXIT=([^`\s|]*)', block)
    if not m or not re.match(r'^\d+$', m.group(1)):
        bad.append(u'VIS_EXIT 不是一个退出码：' + (m.group(1)[:40] if m else u'没有这一行'))
    return bad


def build(v):
    return u"""
%s

| 格子 | 读数 |
|---|---|
| 构建 | `BUILD_EXIT=%s`、告警行 `BUILD_WARNING_LINES=%s` |
| 全量 swift test | `TEST_EXIT=%s`：%s |
| 在屏那一卷（探针） | `PROBE_EXIT=%s` |
| 帧 | `CAPTURE_EXIT=%s`、帧数 %s（PNG 计数，不含读数日志）、`FRAME_BASELINE_COMPARED=%s`、`FRAME_BASELINE_CHANGED=%s`、`FRAME_BASELINE_MISSING=%s` |
| 帧闸门 | `FRAMES_EXIT=%s` |
| 脚本电池 | `PY_EXIT=%s` |
| 七张变异表 | `MUT_EXIT=%s` |
| 台账编号守卫 | `LEDGER_EXIT=%s` |
| 曲线仪器 | `VIS_EXIT=%s` |
| 摘要缺值 | `SUMMARY_MISSING=%s` ⇒ **`VERIFY_OK=%s`** |

本轮两条新读数通道的原文（名单由它生成，不是手抄）：上方 %s；下方 %s。

第 6 步那一行的原文（七张表各一条 `MUTATE_TABLE`，逐字贴，不重排）：

```
%s
```

**这一格要说清它自己量了什么**：`MUT_EXIT` 取的是"七张表里有没有任何一张非零"，
不是最后一张的退出码；"少一张表"与"某张表非零"一样算红（R98 / U-248 那朵红正是
"只有标题行、没有内容行"被读成了通过）。本轮新表 `r99` 四刀：
M552（`absoluteRows` 丢偏移，一条变异同时要把名单与真值表弄红）、M553（把尺弄瞎，名单必须红 ——
这条是名单那条判据的**非恒真证明**）、M554（两个产品文件整体还原成 `git show HEAD:` 那一版 ⇒
上方 3 段、下方 2 段同时红）、M555（第二张卡片丢掉 `maxWidth` ⇒ 下方 2 段红）。
""" % (HEAD, v['BUILD_EXIT'], v['BUILD_WARNING_LINES'], v['TEST_EXIT'], v['TEST_LINE'],
       v['PROBE_EXIT'], v['CAPTURE_EXIT'], v['PNG'], v['FRAMES_COMPARED'],
       v['FRAMES_CHANGED'], v['FRAMES_MISSING'], v['FRAMES_EXIT'], v['PY_EXIT'],
       v['MUT_EXIT'], v['LEDGER_EXIT'], v['VIS_EXIT'], v['SUMMARY_MISSING'], v['VERIFY_OK'],
       v['ABOVE'], v['BELOW'], v['TABLES'])


def main():
    v = read_verify()
    block = build(v)
    bad = check_block(block)
    if bad:
        for b in bad:
            sys.stderr.write(u'渲染出来的段落自己没过检查：%s\n' % b)
        return 2
    if os.environ.get('LEDGERS_R99_APPLY') != '1':
        sys.stdout.write(block)
        sys.stdout.write(u'\n（没有 APPLY=1 ⇒ 只打印不落盘）\n')
        return 0
    original = rd(TARGET)
    tail = original.split(u'## Round 99 ·')[-1]
    if HEAD in tail:
        sys.exit(u'拒绝写盘：Round 99 已经有第 8 格了（要改就手改，别让脚本覆盖）')
    head, sep, rest = original.rpartition(MARKER)
    if not sep:
        sys.exit(u'拒绝写盘：找不到 §9 那个插入点 ⇒ 不猜位置，不让脚本把台账写花')
    wr(TARGET, head.rstrip(u'\n') + u'\n' + block + u'\n' + sep + rest)
    # 落盘之后**只**复检写进去的那一块（切到 §9 为止）：没有右边界会把 §9 里
    # 与本格无关的文本一起判 —— 那是一次"自检对自己红"的假失败（R98 的教训）。
    if check_block(rd(TARGET).split(HEAD)[-1].split(u'### 9.')[0]):
        wr(TARGET, original)
        sys.exit(u'落盘后自检失败 ⇒ 已还原')
    print(u'已落盘：Round 99 第 8 格（十格齐全）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
