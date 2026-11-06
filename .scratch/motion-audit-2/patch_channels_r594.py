# -*- coding: utf-8 -*-
'''R594 靶 2：给 `PREDICTIONS_R594` 那五条各补上第四格「通道」。
写一次就用（一次性补丁），跑完留在 .scratch 里当"这一格是谁补上的"的证人。'''
import io

P = '.scratch/motion-audit-2/ci_status_r593.py'
CHANNELS = [
    '步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)` 的 stdout：'
    '`bundle_content_gate.py` 自己 print 的那两行（`if: always()` ⇒ 上游红也出声；步骤绿时正文只在 --log）',
    '步骤 `Release script tests` 的 stdout：`test_skip_roster` 把这一行印在**所有会崩的门之前**（R593 修的那一处）',
    '步骤 `Swift tests (executed-count gate)` 的 --log-failed 正文里 `Test Case … failed` 行：'
    '由 gh 的日志通道给、不是判据自己印 ⇒ 取不到就是**未读到**，不是「没红」',
    '步骤 `On-screen probe coverage floor` 的 stdout：`PROBE_COVERAGE_SUMMARY` 由判据 print；失败行在 --log-failed',
    '步骤 `Release script tests` 的 stdout：内层电池自己的 `Ran <N>` 汇总行（不是台账里抄来的数）',
]
ANCHOR = 'u"取处"'

text = io.open(P, encoding='utf-8').read()
start = text.index('PREDICTIONS_R594 = [')
end = text.index('\n]', start) + 2
block = text[start:end]
assert block.count(ANCHOR) == 5, block.count(ANCHOR)
assert '通道' not in block

out = []
i = 0
n = 0
while True:
    j = block.find(ANCHOR, i)
    if j < 0:
        out.append(block[i:])
        break
    out.append(block[i:j])
    out.append('u"通道": u"' + CHANNELS[n] + '",\n             ' + ANCHOR)
    n += 1
    i = j + len(ANCHOR)          # 关键：从锚之后继续找，否则同一处被反复命中
patched = ''.join(out)
assert patched.count('u"通道"') == 5
io.open(P, 'w', encoding='utf-8', newline='\n').write(text[:start] + patched + text[end:])
print('CHANNEL_CELLS_WRITTEN=5')
