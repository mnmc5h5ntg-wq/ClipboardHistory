# -*- coding: utf-8 -*-
"""R583 的 ⓪ 取数：成对号 + 全部失败步骤 + **三条待验形状各自反查**（一致 / 翻了 / 那一行命中 0 次）。

四条规矩（派单 ①/④ 点名）：
1. run↔sha **成对**取，对不上就 SystemExit；
2. `conclusion` 空 ⇒ 写**未到数**，并写明"每一步结论全空"不等于"没有失败步骤"；进行中的作业不去取日志；
3. 三条待验形状**修法相反**，必须分开处置：脚本从 runner 那一行反查命中哪一条，一条都不命中 ⇒ 整格 NOT-RUN；
4. `gh` 的返回值**先用一个已知 run 验字段顺序**（上一轮我把 `conclusion` 当 sha 对拍 ⇒ 那一格失去证人）——
   这一条由 `FIELDS_ANCHOR` 那一次自检落实：字段顺序不对就直接拒绝跑，不许拿错位的数往下算。

用法：python3 .scratch/motion-audit-2/ci_status_r583.py
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = '/tmp/r583/ci_status.txt'

RUNS = {
    'MAIN': ('42066364877', 'dbd13fb', 'R582 主笔：`D12_SHAPE_SCAN_REGISTRY` 的第一证人'),
    'BUJI': ('42066695864', '876bd3a', 'R582 补记笔：只带台账，不替主笔签'),
}

# 字段顺序自检用的已知 run（就是 MAIN）：sha 必须等于账上那个 7 位号。
FIELDS_ANCHOR = ('42066364877', 'dbd13fb')

CHANNELS = [
    # (主笔那一跑的标签, 补记笔那一跑的标签, 模式) —— 标签名要与写手 cifield() 要的一字不差，
    # 否则"名册在但读不到那一格"会被读成"那一格没数"（R583 ⑨：占位文字当读数这一族）。
    ('REGISTRY_LINE_MAIN', 'REGISTRY_LINE_BUJI',
     r'D12_SHAPE_SCAN_REGISTRY 机器=\S+ 登记=\S+ 实测=\S+ 判=\S+ 红路=\S+ 另一台已登记=\S+'),
    ('SHAPE_SCAN_MAIN', 'SHAPE_SCAN_BUJI', r'D12_SHAPE_SCAN [^\r\n]*'),
    ('GATE_RUNNER', 'GATE_RUNNER_BUJI', r'D12_LIVE_GATE [^\r\n]*'),
    ('PROBE_RUNNER', 'PROBE_RUNNER_BUJI', r'D12_LIVE_GATE_PROBE [^\r\n]*'),
    ('D12_MAP_RUNNER', 'D12_MAP_RUNNER_BUJI', r'D12_CHANNEL_MAP_SUMMARY [^\r\n]*'),
    ('MATERIAL_MAIN', 'MATERIAL_BUJI', r'REALSCREEN_MATERIAL_NOT_RUN=env-off[^\r\n]{0,140}'),
    ('PROBE18_MAIN', 'PROBE18_BUJI', r'PROBE_COVERAGE_SUMMARY [^\r\n]*'),
    ('MOTION_FACTS', 'MOTION_FACTS_BUJI', r'MOTION_FLOOR_FACTS [^\r\n]*'),
    ('MOTION_MAIN', 'MOTION_MAIN_BUJI', r'MOTION_FLOOR_SUITE_RED=[0-9]+'),
    ('GATE_MAIN', 'GATE_MAIN_BUJI', r'CAPTURE_GATE_CASES [^\r\n]*'),
    ('FRAME_GATE_MAIN', 'FRAME_GATE_BUJI', r'FRAME_BASELINE_RESULT=[^\r\n]*'),
    ('FRAME_DRIFT_MAIN', 'FRAME_DRIFT_BUJI', r'FRAME_BASELINE_DRIFT [^\r\n]*'),
]


def run(argv, timeout=300):
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def gh_view(run_id):
    """status / conclusion / headSha 三个字段**按名字取**，再单独验一次顺序。"""
    code, out = run(['gh', 'run', 'view', run_id, '--json', 'status,conclusion,headSha',
                     '--template', '{{.status}}|{{.conclusion}}|{{.headSha}}'])
    if code != 0 or '|' not in out:
        raise SystemExit('gh 取不到 %s：%s' % (run_id, out[:200]))
    status, concl, sha = out.split('|', 2)
    return status, concl, sha


def verify_field_order():
    """派单 ④ 那一格：解包顺序先拿一个已知 run 验，错位就不许往下算。"""
    anchor_id, anchor_sha = FIELDS_ANCHOR
    status, concl, sha = gh_view(anchor_id)
    if not sha.startswith(anchor_sha) or concl not in ('', 'success', 'failure', 'cancelled'):
        raise SystemExit('字段顺序自检失败：sha=%r conclusion=%r ⇒ 解包错位，拒绝取数'
                         % (sha[:12], concl))
    return (u'字段顺序自检（用已知跑 `%s`）：`headSha` 前缀逐字 =`%s`、`conclusion` 取值在 '
            u'`{空, success, failure, cancelled}` 之内 ⇒ status=%s / conclusion=%s ⇒ 解包没错位'
            % (anchor_id, sha[:7], status, concl or '空'))


def steps_view(run_id):
    code, out = run(['python3', 'scripts/ci_read.py', 'steps', run_id])
    if code != 0:
        raise SystemExit('ci_read.py steps 取不到 %s：%s' % (run_id, out[:200]))
    return out


def full_log(run_id):
    path = '/tmp/r583/fulllog_%s.txt' % run_id
    os.makedirs('/tmp/r583', exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    with io.open(path, 'w', encoding='utf-8', errors='replace') as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=1500)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的整跑日志取不到 ⇒ 那一格只能判未读，不许写「没有」' % run_id)
    return path


def main():
    fields = [('FIELDS_ORDER_CHECK', verify_field_order())]
    body = {}
    for tag, (run_id, sha, title) in RUNS.items():
        status, concl, head = gh_view(run_id)
        if head[:7] != sha:
            raise SystemExit('%s 的 sha 对不上：账上 %s，实际 %s ⇒ 拒绝写账' % (run_id, sha, head[:7]))
        if concl == '':
            fields.append(('STATUS_%s' % tag,
                           u'%s ↔ %s（%s）现读 **未到数**（`status=%s`、`conclusion` 空 ⇒ 通道还没内容；'
                           u'每一步的 conclusion 也全空 —— 那**不是**「没有失败步骤」）'
                           % (run_id, sha, title, status)))
            fields.append(('STEPS_%s' % tag,
                           u'不取（那一跑还没数；`steps` 视图对进行中的作业不给 success 建行）'))
            fields.append(('NAMES_%s' % tag,
                           u'不取（未到数 ⇒ 「没有新名字」与「有 N 朵」两句都没读到位）'))
            continue
        fields.append(('STATUS_%s' % tag, u'%s ↔ %s（%s）现读 到数（`%s / %s`）'
                                       % (run_id, sha, title, status, concl)))
        view = steps_view(run_id)
        reds = [ln.strip() for ln in view.split('\n') if u'⇒ failure' in ln]
        fields.append(('STEPS_%s' % tag, u'、'.join(reds) if reds else u'无失败步骤'))
        path = full_log(run_id)
        body[tag] = io.open(path, encoding='utf-8', errors='replace').read()
        names = sorted(set(re.findall(r"Test Case '-\[[A-Za-z.]+ ([A-Za-z0-9_]+)\]' failed", body[tag])))
        if not names:
            raise SystemExit('%s 里读不到任何失败用例名 ⇒ 「没有新名字」这句不能凭这句话写' % run_id)
        fields.append(('NAMES_%s' % tag, u' '.join(names)))

    for label_main, label_buji, pattern in CHANNELS:
        for tag in RUNS:
            text = body.get(tag, '')
            found = re.findall(pattern, text)
            label = label_main if tag == 'MAIN' else label_buji
            if found:
                fields.append((label, found[-1].strip()))
            else:
                fields.append((label,
                               (u'现读命中 0 次（模式 `%s`）⇒ 具名缺失，不许写成「没有这回事」' % pattern)
                               if text else u'未取（那一跑未到数）'))

    # —— 三条待验形状：各自处置，一条都不命中就整格 NOT-RUN。
    registry = dict(fields).get('REGISTRY_LINE_MAIN', '')
    registry_present = registry.startswith('D12_SHAPE_SCAN_REGISTRY')
    shape_present = dict(fields).get('SHAPE_SCAN_MAIN', '').startswith('D12_SHAPE_SCAN')
    # ⚠ `registry` 在未到数时**也是一句非空的话**（"未取（那一跑未到数）"）⇒
    #   拿 `if registry:` 当"读到了"就是把占位文字当成读数（这一族本账记过多次）。
    #   所以三条形状各自问"那一行到底在不在"，不在就是**没被问**，不是"命中新形状"。
    if registry_present and u'判=一致' in registry:
        hit = (u'⑴', u'登记那格**跨机器闭合**：runner 自己读到 `机器=github-runner 登记=1_2 判=一致` ⇒ '
                   u'R582 交接的「数值到了、判定那一半没闭合」就此结掉；下一轮不许再写「等第一证人」')
    elif registry_present and u'判=翻了' in registry:
        hit = (u'⑵', u'那一台的树与登记不同 ⇒ 唯一合法处置是**拿着那一跑的实测值改登记**（连来源 run id 一起换），'
                     u'不许改期望去迁就、不许改成具名不判、两档永久断言（`差=0` / `剥注释>=1`）不许跟着放宽')
    elif shape_present and not registry_present:
        hit = (u'⑶', u'**通道没跑**：`D12_SHAPE_SCAN` 在而 `D12_SHAPE_SCAN_REGISTRY` 命中 0 次 ⇒ '
                     u'先读 `executed=` 与全部失败步骤再下结论（判据没被执行？emit 没接上？），'
                     u'**不许**把「没有这一行」读成「与登记相符」')
    elif registry_present:
        hit = (u'新形状', u'registry 那一行读到了，但既不是一致也不是翻了，也不是缺席 ⇒ 整格 NOT-RUN、'
                        u'一条都不选，先把这个新形状写进 R584 的 ⓪')
    else:
        hit = (u'未问', u'⓪ 那一跑到数之前三条形状都没被问 ⇒ 一条都不选，整格记 NOT-RUN（R557 那一课）')
    fields.append(('CONTINGENCY_HIT', u'%s ⇒ %s（registry 那一行逐字 `%s`）' % (hit[0], hit[1], registry[:200])))
    fields.append(('CONTINGENCY_MISSED',
                   u'另外两条：⑴ 一致 ⑵ 翻了 ⑶ 命中 0 次 —— 逐条试完，命中的只有上面那一条'
                   if hit[0] in (u'⑴', u'⑵', u'⑶') else
                   u'三条都没被问：⑴ 判=一致 ⑵ 判=翻了 ⑶ 那一行命中 0 次（通道没跑）'))

    # —— 本轮新门在 runner 上的第一格（frame 基线门）：只有到数的那一跑能给。
    fields.append(('REGISTRY_RUNNER',
                   u'登记那一格在 ⓪ 两跑上的状态：主笔 `%s`；补记笔 `%s` ⇒ %s'
                   % (dict(fields).get('REGISTRY_LINE_MAIN', '')[:90],
                      dict(fields).get('REGISTRY_LINE_BUJI', '')[:60], hit[1])))
    fields.append(('FRAME_GATE_NOTE',
                   u'本轮新写的登记判定（`FRAME_BASELINE_DRIFT …`）随本笔才上树 ⇒ 在 ⓪ 这两跑上必然命中 0 次；'
                   u'它的第一证人是含 R583 那一笔的跑（修尺那一笔的跑签不了自己，R555/R565 那一族）'))

    # —— 三条通道现读。
    fields.append(('API_ANON', u'匿名 `curl https://api.github.com` 现读 HTTP=%s（不证可推也不证不可推）'
                   % run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                          'https://api.github.com'])[1].strip()))
    fields.append(('GITHUB_ANON', u'`curl https://github.com` 现读 HTTP=%s'
                   % run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                          'https://github.com'])[1].strip()))
    code, auth = run(['gh', 'auth', 'status'])
    if code != 0:
        raise SystemExit('gh 的 token 通道不可用：%s' % auth[:200])
    fields.append(('GH_TOKEN_CHANNEL', u'`gh auth status` 现读通（本轮读 CI 走这一条）'))
    code, ls = run(['git', 'ls-remote', 'origin', 'HEAD'])
    if code == 0 and ls.strip():
        fields.append(('PUSH_CHANNEL', u'`PUSH_TRANSPORT=ssh-ok` —— 现读 `git ls-remote origin HEAD` 通（远端 HEAD='
                       + ls.split()[0][:9] + u'）；没改 remote url、没动 `~/.ssh`、没换 DNS'))
    else:
        fields.append(('PUSH_CHANNEL', u'`PUSH_BLOCKED=` 待具名 —— `git ls-remote origin HEAD` 退出码 %d，正文首行 `%s`'
                       % (code, (ls.strip().splitlines() or [u'空'])[0][:60])))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8') as handle:
        for label, value in fields:
            handle.write(u'%s :: %s\n' % (label, value))
    for label, value in fields:
        print(u'%s :: %s' % (label, value))
    print('CI_STATUS 写了 %d 格 → %s' % (len(fields), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
