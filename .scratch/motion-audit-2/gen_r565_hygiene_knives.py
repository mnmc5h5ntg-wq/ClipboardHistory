#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 R565 补段 C 的四把刀（M1470-M1473）。

写法与 `mutate_r565_m1468.py` 同形（单臂：ARM/FILE/OLD/NEW + 跑 python 电池模块取判决），
但**不许写死本机根** —— 这一族正是本轮要钉的坏法，刀自己不能再犯（R564 的刀脚本里就抄过绝对根）。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BODY = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 变异表 %(ARM)s：%(WHY)s

刀的对象是 R565 补段 C 的统一卫生守卫 `scripts/ci_channel_hygiene.py`
（同族两次事故：R564 的绝对根打死 runner 的 STEP[9]、R565 的通道裸空格打死判它的测试）。
跑的是 python 那一条模块，不是 swift 卷 ⇒ 可以与别的卷并行。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = "%(FILE)s"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
TEST = "scripts.tests.test_ci_channel_hygiene"
ARM = "%(ARM)s"
OLD = %(OLD)r
NEW = %(NEW)r


def run():
    proc = subprocess.run([sys.executable, "-m", "unittest", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=600)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "PASSED", out
    return ("CAUGHT" if "FAILED (" in out else "ERROR"), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print("预检:", code)
    if code != "PASSED":
        print(out[-900:])
        return 2
    if text.count(OLD) != 1:
        print("needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print(ARM + ":", code)
    for line in out.splitlines():
        if "AssertionError" in line or "FAIL:" in line or "CI_CHANNEL_HYGIENE " in line:
            print("  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-900:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TABLES = [
    ('M1470', '把 `commit_round_identity.py` 的仓库根改回写死的绝对路径（别人的用户名也算）⇒ 守卫必须红。'
              '这一把钉的是形状判那一支：从前模式绑在某个具体用户名上，换一个人的目录它就哑。',
     'scripts/commit_round_identity.py',
     'ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))',
     'ROOT = "/Users/wangziyi/Codex_Project0"'),
    ('M1471', '把空名单那一检查改成恒不成立（`if not roster:` ⇒ `if False:`）⇒ 守卫必须红。'
              '这一把钉的是"零条也算通过"：工作流改了名、解析器抽不出脚本时门必须红而不是静默。',
     'scripts/ci_channel_hygiene.py',
     '    if not roster:',
     '    if False:'),
    ('M1472', '把退化说明塞回 `范围=` 的**值**里（一个 ASCII 空格）⇒ 守卫必须判出 `通道空格`。'
              '这一把钉的是 R565 真实自伤的回归：那一版让判它的测试在 `dict(kv.split("=", 1))` 上崩。',
     'scripts/commit_round_identity.py',
     '        scope = "HEAD~1..HEAD"',
     '        scope = "HEAD~1..HEAD 未推的为空"'),
    ('M1473', '在 `make_info_plist.sh` 里写死一个绝对根 ⇒ 守卫必须红（非 .py 那一支）。'
              '这一把钉的是：上一版扫描器只会 `ast.parse`，喂给它 shell 就报 parse-error —— '
              'CI 真跑的 `.sh` 完全在尺外。',
     'scripts/make_info_plist.sh',
     'set -eu',
     'set -eu\nREPO="/Users/wangziyi/Codex_Project0"'),
]


def main():
    for arm, why, target, old, new in TABLES:
        path = os.path.join(HERE, 'mutate_r565_%s.py' % arm.lower())
        text = BODY % dict(ARM=arm, WHY=why, FILE=target, OLD=old, NEW=new)
        io.open(path, 'w', encoding='utf-8').write(text)
        print('WROTE %s (target=%s)' % (os.path.basename(path), target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
