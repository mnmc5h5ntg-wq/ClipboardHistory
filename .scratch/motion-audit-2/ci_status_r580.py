#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R580 ⓪：把「三跑到没到数」与「本轮 ① 那两问的答案」做成**落盘的摘录**，而不是我在账里写的一句话。

与 R579 那版的差别只有一处：本轮 ⓪ 有三跑（上一轮的主笔 + 两笔补记），而且派单 ① 明写了
两个必须回答的问题 —— ⑴ `MAGENTA_CONTROL_GEOMETRY` 第一次上 runner 的那一行，`档位真值=` 逐字抄；
⑵ 那一跑的材质那臂**是不是仍然 env-off**（硬规矩：「runner 在跑」不等于「runner 是 Light」，
656 的出路丙「由另一跑提供第二档」没拿到就只能写没拿到）。这两个数都由 emit 通道取，不按步骤名赌。

取数全部走 token 那条通道（`gh run view --json` / `ci_read.py steps` / `ci_read.py readings`），
匿名 `curl api.github.com` 只作为**另一个通道**记录它自己的形状。任一格取不到 ⇒ 不写文件、退出码 1。

用法：python3 .scratch/motion-audit-2/ci_status_r580.py     （写 /tmp/r580/ci_status.txt）
退出码：0=全部格子取到；1=某一格取不到（此时**不写文件**，账就不能落）。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = '/tmp/r580/ci_status.txt'
RUNS = {
    'MAIN': ('42023214425', '87b234e', 'R579 主笔'),
    'BUJI': ('42023451609', '50501e3', 'R579 补记笔'),
    'BUJI2': ('42024230922', 'f818c07', 'R579 补记二笔'),
}


def run(argv, timeout=300):
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def gh_json(run_id):
    code, out = run(['gh', 'run', 'view', run_id, '--json',
                     'status,conclusion,headSha', '--template',
                     '{{.status}}|{{.conclusion}}|{{.headSha}}'])
    if code != 0 or '|' not in out:
        raise SystemExit('gh 取不到 %s：%s' % (run_id, out[:200]))
    status, conclusion, sha = out.split('|', 2)
    return status, conclusion, sha


def steps_of(run_id):
    code, out = run(['python3', 'scripts/ci_read.py', 'steps', run_id])
    if code != 0:
        raise SystemExit('ci_read.py steps 取不到 %s：%s' % (run_id, out[:200]))
    return out


def failed_log(run_id):
    path = '/tmp/r580/log_%s.txt' % run_id
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', errors='replace') as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log-failed'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=900)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的失败步骤日志取不到（字节=%d）⇒ 这一跑只能判未读'
                         % (run_id, os.path.getsize(path) if os.path.exists(path) else -1))
    return path


def one(pattern, path, label):
    found = re.findall(pattern, open(path, encoding='utf-8', errors='replace').read())
    if not found:
        raise SystemExit('%s 没在 %s 里命中（模式 %s）⇒ 拒绝写账' % (label, path, pattern))
    return found[0].strip()


def full_log(run_id):
    """**整跑日志**（不只失败步骤）：某一格绿了的时候，它的正文在 `--log-failed` 里根本不存在
    —— 那是「那一步不在失败列表里」这一格与「那一步的读数」两件事的区别（read-own-ci-run 第 2 步）。"""
    path = '/tmp/r580/fulllog_%s.txt' % run_id
    with open(path, "w", encoding="utf-8", errors="replace") as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=900)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的整跑日志取不到（字节=%d）⇒ 只能判未读' % (run_id, os.path.getsize(path)))
    return path


def names_of_failed(path):
    raw = re.findall(r"Test Case '-\[[A-Za-z.]+ ([A-Za-z0-9_]+)\]' failed",
                     open(path, encoding='utf-8', errors='replace').read())
    if not raw:
        raise SystemExit('%s 里读不到任何失败用例名 ⇒ 「没有新名字」不能凭这句话写' % path)
    return sorted(set(raw))


def main():
    fields = []
    logs = {}
    for tag, (run_id, sha, title) in RUNS.items():
        status, conclusion, head = gh_json(run_id)
        if head[:7] != sha:
            raise SystemExit('%s 的 sha 对不上：账上 %s，实际 %s ⇒ 拒绝写账' % (run_id, sha, head[:7]))
        if conclusion == '':
            verdict = u'未到数（`status=%s`、`conclusion` 空 ⇒ 通道还没内容，**不是「没有失败步骤」**）' % status
        else:
            verdict = u'到数（`%s / %s`）' % (status, conclusion)
        fields.append((u'STATUS_%s' % tag, u'%s ↔ %s（%s）现读 %s' % (run_id, sha, title, verdict)))
        view = steps_of(run_id)
        reds = [ln.strip() for ln in view.split('\n') if '\u21d2 failure' in ln]
        fields.append((u'STEPS_%s' % tag, u'、'.join(reds) if reds else u'无失败步骤'))
        logs[tag] = failed_log(run_id)
        fields.append((u'NAMES_%s' % tag, u' '.join(names_of_failed(logs[tag]))))

    # 派单 ① 那两问，逐字取。
    fields.append(('GEOMETRY_MAIN', one(r'MAGENTA_CONTROL_GEOMETRY [^\r\n]*', logs['MAIN'],
                                        '新格第一次上 runner 那一行')))
    for tag in ('MAIN', 'BUJI2'):
        fields.append(('MATERIAL_%s' % tag,
                       one(r'REALSCREEN_MATERIAL_NOT_RUN[^\r\n]{0,140}', logs[tag], '材质那臂的状态')))
    fields.append(('PROBE_BUJI2', one(r'PROBE_COVERAGE_SUMMARY [^\r\n]*', logs['BUJI2'],
                                      'STEP[18] 那一格的读数')))
    # STEP[18] 在主笔那一跑**没进失败列表** ⇒ 它的正文只在整跑日志里；这一格因此必须从 `--log` 取，
    # 取不到就写明是哪一格没取到（「绿了」与「没读到」是两行不同的账）。
    fields.append(('PROBE_MAIN', one(r'PROBE_COVERAGE_SUMMARY [^\r\n]*', full_log(RUNS['MAIN'][0]),
                                     '前两跑 STEP[18] 的对照读数（整跑日志）')))
    fields.append(('GATE_MAIN', one(r'CAPTURE_GATE_CASES [^\r\n]*', logs['MAIN'], '捕获门')))
    fields.append(('MOTION_MAIN', one(r'MOTION_FLOOR_SUITE_RED=[0-9]+', logs['MAIN'], '动效门计数')))
    # 本轮那张表在 runner 上**还没有证人**（新格随本轮这一笔才上去）——这一格必须由「读不到」产生。
    # 本轮新格（`D12_LIVE_GATE` / `D12_LIVE_GATE_PROBE`）第一次上 runner 要等**本轮这一笔**⇒
    # 上一跑里它必须「没有一行」。这一格的价值正在于它是**取不到**产生的，不是我写的一句话：
    # 只有当 readings 自己打了「通道 … 没有一行」才叫没读到（别的输出都不算证人）。
    code, out = run(['python3', 'scripts/ci_read.py', 'readings', RUNS['MAIN'][0],
                     'D12_LIVE_GATE,D12_LIVE_GATE_PROBE'])
    hit = [ln.strip() for ln in out.splitlines()
           if 'D12_LIVE_GATE' in ln and ('⇒' in ln or '没有一行' in ln)]
    if not hit:
        raise SystemExit('D12_LIVE_GATE 那一格的取数没打印结论行 ⇒ 停手（退出码 %d）' % code)
    if any(u'没有一行' in ln for ln in hit):
        fields.append(('LIVE_GATE_MAIN', u'两串通道都「没有一行」（`ci_read.py readings` 逐字：%s）'
                       % u' ‖ '.join(hit)[:220]))
    else:
        fields.append(('LIVE_GATE_MAIN', u'意外命中：本轮新格出现在上一跑里 ⇒ %s' % u' ‖ '.join(hit)[:220]))

    code, api = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.github.com'])
    fields.append(('API_ANON', u'匿名 `curl https://api.github.com` 现读 HTTP=%s（未认证限流的形状，不是断网）'
                   % api.strip()))
    code, gh_host = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://github.com'])
    fields.append(('GITHUB_ANON', u'`curl https://github.com` 现读 HTTP=%s' % gh_host.strip()))
    code, auth = run(['gh', 'auth', 'status'])
    if code != 0:
        raise SystemExit('gh 的 token 通道不可用：%s' % auth[:200])
    fields.append(('GH_TOKEN_CHANNEL', u'`gh auth status` 现读通（token 那一条才是本轮读 CI 用的通道）'))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as handle:
        for label, value in fields:
            handle.write('%s :: %s\n' % (label, value))
    for label, value in fields:
        print('%s :: %s' % (label, value))
    print('CI_STATUS 写了 %d 格 → %s' % (len(fields), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
