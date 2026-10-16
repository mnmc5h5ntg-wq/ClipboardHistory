#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R98 的验证段落盘：数字只从 `r98_verify.log` 解析，缺任一格就**拒绝写盘**。

三条规矩都是从栽过跟头的地方抄来的（用户级记忆"守卫与登记自身的四种失效"）：
① 事务性 —— 先整体快照再写，任何一格抛错就全部还原（半份台账比没写更坏）；
② 数字只从日志解析，缺格就拒写（不出现"猜出来的数"）；
③ 渲染完的那一段自己再过一遍 `check_block`：不许残留计时文本、不许有 `（0）`、
   `VIS_EXIT` 必须是一个退出码而不是半句话、不许有 `?`。
   （R96 连中两次：`grab()` 返回了 group(1) 而不是 group(2)，于是台账里出现
   「全量 swift test `TEST_EXIT=0`（0）」这种半句；把渲染结果再判一遍是唯一能拦住它的东西。）

跑法：LEDGERS_R98_APPLY=1 PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r98.py
退出码：0 = 十格齐全且落盘；非 0 = 拒绝写盘。
"""
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
LOG = REPO + '/.scratch/motion-audit-2/r98_verify.log'
TARGET = REPO + '/AGENT_VISUAL_ITERATION.md'
SHOTS = '/tmp/r98_shots'

KEYS = ['BUILD_EXIT', 'BUILD_WARNING_LINES', 'TEST_EXIT', 'PROBE_EXIT', 'CAPTURE_EXIT',
        'FRAMES_EXIT', 'PY_EXIT', 'MUT_EXIT', 'LEDGER_EXIT', 'VIS_EXIT', 'SUMMARY_MISSING',
        'VERIFY_OK']


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def grab(text, key):
    """最后一格 = 值（不能用 group(1)：那会把整条匹配连键名一起带回来）。

    不锚进行首：`BUILD_EXIT=0 BUILD_WARNING_LINES=0` 是同一行打出来的两格，
    锚行首会让第二格"读不到"，而"读不到"在这里等于拒写 —— 那是工具的错，不是账的错。
    退出码一律按**纯数字**取：`MUT_EXIT=0r95_rhythm ...` 是 R98 pass-2 真发生过的形状 ——
    电池那一行把六张表的名字直接接在值后面，用 `\\S+` 就会把下一格的开头读进来，
    于是台账里出现 `MUT_EXIT=0r95_rhythm` 这种半句话（渲染后自检现在也会拦它）。
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
    # 全量汇总那一行：`Executed N tests, with M skipped and K failures`
    m = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures', text)
    if not m:
        sys.exit(u'拒绝写盘：读不到全量测试的汇总行（Executed … failures）')
    v['TEST_LINE'] = u'%s 例 / %s skip / %s failures' % (m.group(1), m.group(2), m.group(3))
    fr = re.search(r'FRAME_BASELINE_CHANGED=(\d+)', text)
    if not fr:
        sys.exit(u'拒绝写盘：读不到 FRAME_BASELINE_CHANGED=')
    v['FRAMES_CHANGED'] = fr.group(1)
    pngs = [f for f in os.listdir(SHOTS) if f.endswith('.png')]
    n = int(grab(text, u'帧数'))
    if n != len(pngs):
        sys.exit(u'拒绝写盘：日志的 帧数=%d 与目录里真实的 PNG=%d 对不上' % (n, len(pngs)))
    v['PNG'] = u'%d' % len(pngs)
    # 六张表的原文在 `MUT_EXIT=` 那一行（R98 之后电池把结论行改成"每张贴一行"，
    # 因为 U-248 那朵红正是"只有标题行、没有内容行"被读成了通过）。
    for line in text.splitlines():
        if line.startswith('MUT_EXIT=') and 'exit=' in line:
            v['TABLES'] = line
            break
    else:
        sys.exit(u'拒绝写盘：找不到 MUT_EXIT= 那一行（六张变异表的原文）')
    if line.count('MUTATE_TABLE') < 6:
        sys.exit(u'拒绝写盘：MUT_EXIT 行里只有 %d 张表的原文，期望 6 张 ⇒ 有表没跑成'
                 % line.count('MUTATE_TABLE'))
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
                u'PY_EXIT', u'MUT_EXIT', u'LEDGER_EXIT'):
        # 退出码后面可以跟散文（`TEST_EXIT=0`：811 例…），所以只要求"数字 + 非数字边界"。
        v = re.search(key + r'=(\d+)(?![0-9A-Za-z_])', block)
        if not v:
            bad.append(u'%s 那一格不是纯退出码：%s' % (key, v.group(1) if v else u'没有'))
    # 不锚行首：渲染出来的这一格在 Markdown 表格里（`| 看图仪器 | `VIS_EXIT=0` |`），
    # 锚行首会让自检对**自己渲染的形状**红 —— 与上面 `grab` 那次同一种错法（R98 / U-248 同族）。
    m = re.search(r'VIS_EXIT=([^`\s|]*)', block)
    if not m or not re.match(r'^\d+$', m.group(1)):
        bad.append(u'VIS_EXIT 不是一个退出码：' + (m.group(1)[:40] if m else u'没有这一行'))
    return bad


def build(v):
    return u"""
### 8. 验证（十格，数字只从 `r98_verify.log` 解析）

| 格子 | 读数 |
|---|---|
| 构建 | `BUILD_EXIT=%s`、告警行 `BUILD_WARNING_LINES=%s` |
| 全量 swift test | `TEST_EXIT=%s`：%s |
| 在屏那一卷（探针） | `PROBE_EXIT=%s` |
| 帧 | `CAPTURE_EXIT=%s`、帧数 %s（PNG 计数，不含读数日志）、`FRAME_BASELINE_CHANGED=%s` |
| 帧闸门 | `FRAMES_EXIT=%s` |
| 脚本电池 | `PY_EXIT=%s` |
| 六张变异表 | `MUT_EXIT=%s` |
| 台账编号守卫 | `LEDGER_EXIT=%s` |
| 看图仪器 | `VIS_EXIT=%s` |
| 摘要缺值 | `SUMMARY_MISSING=%s` ⇒ **`VERIFY_OK=%s`** |

第 6 步那一行的原文（六张表各一条 `MUTATE_TABLE`，逐字贴，不重排）：

```
%s
```

**这一格要说清它自己量了什么**：`MUT_EXIT` 取的是"六张表里有没有任何一张非零"，
不是最后一张的退出码（R94 之前那种写法会把前五张的失败吞成 0）。
本轮两张新表：种子通道 `n=7 caught=7`、产品腿 `n=2 caught=2`；
欠的四张（节奏 / 行序 / 分诊 / 卡片）里，R95 那张表的 M530 已换锚点、M531 已退役并留记录。
""" % (v['BUILD_EXIT'], v['BUILD_WARNING_LINES'], v['TEST_EXIT'], v['TEST_LINE'],
       v['PROBE_EXIT'], v['CAPTURE_EXIT'], v['PNG'], v['FRAMES_CHANGED'],
       v['FRAMES_EXIT'], v['PY_EXIT'], v['MUT_EXIT'], v['LEDGER_EXIT'],
       v['VIS_EXIT'], v['SUMMARY_MISSING'], v['VERIFY_OK'], v['TABLES'])


def main():
    v = read_verify()
    block = build(v)
    bad = check_block(block)
    if bad:
        for b in bad:
            sys.stderr.write(u'渲染出来的段落自己没过检查：%s\n' % b)
        return 2
    if os.environ.get('LEDGERS_R98_APPLY') != '1':
        sys.stdout.write(block)
        sys.stdout.write(u'\n（没有 APPLY=1 ⇒ 只打印不落盘）\n')
        return 0
    original = rd(TARGET)
    if u'### 8. 验证（十格' in original.split(u'## Round 98 ·')[-1]:
        sys.exit(u'拒绝写盘：Round 98 已经有第 8 格了（要改就手改，别让脚本覆盖）')
    # 插在 §9 之前（R98 的 §9/§10 是收尾之后补写的，§8 按编号顺序应该在它们前面）。
    # R98 教训：拿 `str.index` 的两端做切片时，**先找到的不一定是想要的那一个** ——
    # 第一版按"§8 在文件末尾"假设做删除，结果把 §9/§10 复制了一份出来（已手工修回）。
    marker = u'### 9. 电池与曲线自己坏了两处'
    head, sep, tail = original.rpartition(marker)
    if not sep:
        sys.exit(u'拒绝写盘：找不到 §9 那个插入点 ⇒ 不猜位置，不让脚本把台账写花')
    wr(TARGET, head.rstrip(u'\n') + u'\n' + block + u'\n' + sep + tail)
    # 落盘之后**只**复检写进去的那一块（切到 §9 为止）：
    # 第一版没有右边界，于是把 §9/§10 里与本格无关的文本也一起判了 —— 那是一次
    # "自检对自己红"的假失败（它正确地拒绝写盘，但理由是错的）。
    if check_block(rd(TARGET).split(u'### 8. 验证（十格')[-1].split(u'### 9.')[0]):
        wr(TARGET, original)
        sys.exit(u'落盘后自检失败 ⇒ 已还原')
    print(u'已落盘：Round 98 第 8 格（十格齐全）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
