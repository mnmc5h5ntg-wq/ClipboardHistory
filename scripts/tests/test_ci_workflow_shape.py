"""CI 工作流文件的形状检查（不需要 pyyaml —— 本机就没有那个模块，而这条恰恰要在本机跑得动）。

起因是真实的一次自伤：给工作流加步骤时把步骤名写成了
`- name: Frame baseline: missing frames gate`，值里那个"冒号 + 空格"让 YAML 把它读成映射，
于是整条流水线 **0 秒失败、连 job 都没有**（`gh run view` 里 jobs 是空数组、日志不存在）。
"CI 红了"和"CI 根本没能开始跑"在通知里长得一模一样，而后者不会给你任何行号。

这里只做三件最便宜、也最能挡住那一类错误的事：
1. 每个 `- name:` 的值不许含裸的 `": "`（要么引起来，要么别用冒号）；
2. 每个 step 的键必须缩进到同一个层级，`run:` 后面必须有块标量或值；
3. 本轮加过的步骤名字要真的还在（步骤被误删时，"CI 全绿"反而最危险）。
"""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


class CiWorkflowShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = WORKFLOW.read_text(encoding="utf-8").splitlines()

    def test_step_names_do_not_contain_an_unquoted_colon_space(self):
        offenders = []
        for number, line in enumerate(self.lines, 1):
            match = re.match(r"^\s*-\s+name:\s+(?P<value>.+?)\s*$", line)
            if not match:
                continue
            value = match.group("value")
            if value.startswith('"') or value.startswith("'"):
                continue
            if ": " in value:
                offenders.append("第 %d 行：%s" % (number, line.strip()))
        self.assertEqual(offenders, [],
                         "步骤名里有裸的冒号+空格，YAML 会把整行读成映射，工作流会在 0 秒内失败而不给行号")

    def test_every_step_declares_run_or_uses_with_the_same_indent(self):
        step_indent = None
        problems = []
        for number, line in enumerate(self.lines, 1):
            if re.match(r"^\s*-\s+name:", line):
                indent = len(line) - len(line.lstrip())
                if step_indent is None:
                    step_indent = indent
                elif indent != step_indent:
                    problems.append("第 %d 行缩进 %d，与前面步骤的 %d 不一致" % (number, indent, step_indent))
                # 下一步要么是 `run:`/`uses:`/`with:`/`continue-on-error:` 等键，要么是新步骤
                body = [l for l in self.lines[number:number + 8] if re.match(r"^\s{8,}(run|uses|with|continue-on-error|timeout-minutes|env|id):", l)]
                if not body:
                    problems.append("第 %d 行的步骤没找到 run/uses/with" % number)
        self.assertEqual(problems, [])

    def test_the_steps_that_were_added_to_close_audit_items_are_still_here(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for name in ("Offscreen frame capture", "On-screen interaction probes",
                     "Runtime launch smoke", "Frame baseline"):
            self.assertIn(name, text,
                          "%r 这个步骤不在了 —— 它对应第三轮审计的一条验收面，删掉它 CI 只会更绿，不会更真" % name)

    def test_hard_gates_are_distinguishable_from_report_only_steps(self):
        # 报告型步骤必须逐条写明为什么可以红（这是 D-7 之后的规矩），
        # 否则下一步就有人把它们当噪声，或者反过来把噪声当硬门。
        offenders = []
        for number, line in enumerate(self.lines, 1):
            if "continue-on-error: true" in line:
                window = self.lines[max(0, number - 14):number]
                if not any("#" in entry for entry in window):
                    offenders.append("第 %d 行" % number)
        self.assertEqual(offenders, [], "有报告型步骤没有 nearby 注释解释它为什么不当硬门")


if __name__ == "__main__":
    unittest.main()
