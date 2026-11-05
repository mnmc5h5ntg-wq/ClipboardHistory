#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R581 ⓪：把「两跑到没到数」与**台账那三条预案到底命中哪一条**做成落盘的摘录。

与 R580 那版唯一的实质差别：本轮 ⓪ 要读的两跑是**第一次带 `D12_LIVE_GATE` 的跑**，
而上一轮我自己写给 R581 的三条预案（`AGENT_STATE.md` 的 `### R580 补记` 那一格）说的是
"读到哪一种判法就怎么处置"。⇒ 这一支不许由我回忆命中了哪条：**它从 runner 那一行自己解析出来**
（`判=` 的取值 → 预案编号 → 处置措辞），解析不出来就 SystemExit（不许读成"没触发"）。

取数全部走 token 那条通道（`gh run view --json` / `ci_read.py steps` / `ci_read.py readings`），
匿名 `curl api.github.com` 与 `curl https://github.com` 只作为**另一个通道**记录它自己的形状；
push 通道另由 `git ls-remote origin HEAD` 现读（`api=200` 不证可推，反过来也不证不可推）。

用法：python3 .scratch/motion-audit-2/ci_status_r581.py     （写 /tmp/r581/ci_status.txt）
退出码：0=全部格子取到；1=某一格取不到（此时**不写文件**，账就不能落）。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = '/tmp/r581/ci_status.txt'
RUNS = {
    'MAIN': ('42037392945', '52254ad', 'R580 主笔'),
    'BUJI': ('42037697819', 'a54c101', 'R580 补记笔'),
}
# 台账那三条预案：判法取值 → （预案号，处置）。这张表是**账里那句话的机器可读副本**，
# 两处不一致时必须由本轮改齐并写进账，不许只改一处。
CONTINGENCY = {
    '缺席': (u'⑴', u'那台机器上 A、B 两条通道都读 0 ⇒ `runner可判=0` 这句话在第二台机器上有证人 ⇒ 登记为**已复核**'),
    u'由A认得': (u'⑵', u'产品里出现了 A 认得的名字 ⇒ 五行逐条红 + 「本轮该翻=n」红 ⇒ **这不是缺陷，是活门在叫**；'
                    u'本轮产品 0 文件、第③段不许动 ⇒ 只能把事实报上来并停在第②段等用户定向'),
    u'现扫瞎': (u'⑶', u'那台机器上出现了**形状**而没有**名字** ⇒ 唯一合法处置是**重锚 A 的形状集合**，'
                    u'不许据此把那五行直接改成可判（B 只叫醒 A、不替 A 作证）'),
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
    path = '/tmp/r581/log_%s.txt' % run_id
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="replace") as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log-failed'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=900)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的失败步骤日志取不到 ⇒ 这一跑只能判未读' % run_id)
    return path


def full_log(run_id):
    """绿步的正文只在整跑日志里（R580 ⑨·5 那一课：「在不在失败列表」与「那一步的读数」是两格账）。"""
    path = '/tmp/r581/fulllog_%s.txt' % run_id
    with open(path, "w", encoding="utf-8", errors="replace") as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=900)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的整跑日志取不到 ⇒ 那一格只能判未读' % run_id)
    return path


def one(pattern, path, label, last=False):
    found = re.findall(pattern, open(path, encoding="utf-8", errors="replace").read())
    if not found:
        raise SystemExit('%s 没在 %s 里命中（模式 %s）⇒ 拒绝写账' % (label, path, pattern))
    return (found[-1] if last else found[0]).strip()


def names_of_failed(path):
    raw = re.findall(r"Test Case '-\[[A-Za-z.]+ ([A-Za-z0-9_]+)\]' failed",
                     open(path, encoding="utf-8", errors="replace").read())
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
        reds = [ln.strip() for ln in view.split('\n') if u'\u21d2 failure' in ln]
        fields.append((u'STEPS_%s' % tag, u'、'.join(reds) if reds else u'无失败步骤'))
        logs[tag] = failed_log(run_id)
        fields.append((u'NAMES_%s' % tag, u' '.join(names_of_failed(logs[tag]))))

    # 本轮 ⓪ 的头一格：活门第一次在 runner 上的判法，以及它命中台账三条预案里的哪一条。
    gate_main = one(r'D12_LIVE_GATE A按名字文件数=\d+ B按形状文件数=\d+ 判=\S+',
                    logs['MAIN'], 'runner 上活门那一格第一次读数')
    gate_buji = one(r'D12_LIVE_GATE A按名字文件数=\d+ B按形状文件数=\d+ 判=\S+',
                    logs['BUJI'], '补记笔那一跑的活门读数')
    probe_main = one(r'D12_LIVE_GATE_PROBE [^\r\n]*', logs['MAIN'], '注入正对照在 runner 上的第一次读数')
    if gate_main != gate_buji:
        raise SystemExit('同一棵树的同一格在两跑里给出两个值 ⇒ 停手对拍：主跑 %s ‖ 补记笔 %s'
                         % (gate_main[-80:], gate_buji[-80:]))
    verdict_value = gate_main.split(u'判=')[1].split(u' ')[0]
    hit = None
    for key, value in CONTINGENCY.items():
        if verdict_value.startswith(key):
            hit = (key, value)
            break
    if hit is None:
        raise SystemExit('runner 的判法「%s」不在台账那三条预案里 ⇒ 预案表要补，不许读成「没触发」' % verdict_value)
    fields.append(('GATE_RUNNER', gate_main))
    fields.append(('PROBE_RUNNER', probe_main))
    fields.append(('CONTINGENCY_HIT', u'判法=%s ⇒ 命中预案%s：%s' % (verdict_value, hit[1][0], hit[1][1])))
    fields.append(('CONTINGENCY_MISSED', u'另外两条：'
                   + u'；'.join(u'预案%s（%s）没触发' % (v[0], k)
                                for k, v in CONTINGENCY.items() if k != hit[0])
                   + u'。⚠「这次没命中」不许被读成「永远不会命中」'))

    for tag in ('MAIN', 'BUJI'):
        fields.append(('MATERIAL_%s' % tag,
                       one(r'REALSCREEN_MATERIAL_NOT_RUN[^\r\n]{0,140}', logs[tag], '材质那臂的状态')))
    fields.append(('PROBE18_MAIN', one(r'PROBE_COVERAGE_SUMMARY [^\r\n]*',
                                       full_log(RUNS['MAIN'][0]), 'STEP[18] 的正文（整跑日志）')))
    fields.append(('PROBE18_BUJI', one(r'PROBE_COVERAGE_SUMMARY [^\r\n]*',
                                       full_log(RUNS['BUJI'][0]), 'STEP[18] 补记笔的正文')))
    fields.append(('GATE_MAIN', one(r'CAPTURE_GATE_CASES [^\r\n]*', logs['MAIN'], '捕获门')))
    fields.append(('MOTION_MAIN', one(r'MOTION_FLOOR_SUITE_RED=[0-9]+', logs['MAIN'], '动效门计数')))
    fields.append(('MOTION_FACTS', one(r'MOTION_FLOOR_FACTS [^\r\n]*', logs['MAIN'],
                                       '动效地板那一步的 executed=')))
    fields.append(('D12_MAP_RUNNER', one(r'D12_CHANNEL_MAP_SUMMARY [^\r\n]*', logs['MAIN'],
                                         '映射表四个数在 runner 上')))

    code, api = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.github.com'])
    fields.append(('API_ANON', u'匿名 `curl https://api.github.com` 现读 HTTP=%s（未认证限流的形状，不是断网）'
                   % api.strip()))
    code, gh_host = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://github.com'])
    fields.append(('GITHUB_ANON', u'`curl https://github.com` 现读 HTTP=%s' % gh_host.strip()))
    code, auth = run(['gh', 'auth', 'status'])
    if code != 0:
        raise SystemExit('gh 的 token 通道不可用：%s' % auth[:200])
    fields.append(('GH_TOKEN_CHANNEL', u'`gh auth status` 现读通（token 那一条才是本轮读 CI 用的通道）'))
    code, ls = run(['git', 'ls-remote', 'origin', 'HEAD'])
    if code == 0 and ls.strip():
        fields.append(('PUSH_CHANNEL', u'`PUSH_TRANSPORT=ssh-ok` —— 现读 `git ls-remote origin HEAD` 通（远端 HEAD='
                     + ls.split()[0][:9] + u'）；这一格本轮**现读**（监工侧刚见过三次读数不一致的间歇），'
                     u'没改 remote url、没动 `~/.ssh`、没换 DNS'))
    else:
        fields.append(('PUSH_CHANNEL', u'`PUSH_BLOCKED=` 待具名 —— 现读 `git ls-remote origin HEAD` 退出码 %d，'
                       u'正文首行 `%s`（间歇未定论，成因归用户）' % (code, (ls.strip().splitlines() or [u'空'])[0][:60])))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        for label, value in fields:
            handle.write('%s :: %s\n' % (label, value))
    for label, value in fields:
        print('%s :: %s' % (label, value))
    print('CI_STATUS 写了 %d 格 → %s' % (len(fields), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
