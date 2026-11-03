#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R553 A：`scripts/sign_bundle.sh` 的选身份逻辑 —— 两臂都要有牙，且不许回退成"静默 ad-hoc"。

为什么钉这一格（用户实测：反复弹「时间剪史想访问桌面文件夹」，已批准无数次）：
每次构建 `--remove-signature` + `-s -` ⇒ CDHash 每轮变 ⇒ TCC 把它当新 App，上一次的
"桌面文件夹"授权下一轮就作废。授权跟着**签名身份**走，所以这一格的坏法就是
「构建又直接 ad-hoc 签了，而没人报出来」。

两臂（用 PATH 上的 `security` / `codesign` **桩**，不碰真钥匙串、不签真包）：
  · 有固定身份 ⇒ 必须用 `-s <身份>`，并打 `SIGNATURE_KIND=local`；
  · 没有身份 ⇒ 必须打 `SIGNATURE_KIND=adhoc`（读数里看得见，不许静默）。

第三格是**现读那一台真机器**（`test_this_machine_actually_takes_the_identity_branch`，R566 加）：
桩测只证明"脚本会选对支"，它证明不了"这台机器今天走得通哪一支"。R553 当时的现读是回退支
（`find-identity` 给 0 条）；用户在钥匙串里对 `ClipboardHistory Local Signing` 点了「始终信任」
并放行私钥访问之后，现读换成身份支 ⇒ 这一格把那句话变成会红的事实，**假设一字未改，只换现读值**。
没有那个身份的机器（CI、别人的机器）走具名 skip（skip 与断言同函数），不许被读成"合格"。
另加一条源码守卫：`Makefile` 里不许再出现裸的 `codesign -s -` —— 签必须走这个脚本。
"""
import io
import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "sign_bundle.sh")
IDENTITY = u"ClipboardHistory Local Signing"


def run_script(security_out, workdir):
    """在 PATH 前面挂两个桩：`security` 给固定输出，`codesign` 把收到的参数写进文件。"""
    bin_dir = os.path.join(workdir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    calls = os.path.join(workdir, "codesign.calls")
    with io.open(os.path.join(bin_dir, "security"), "w", encoding="utf-8") as h:
        h.write(u"#!/bin/sh\ncat <<'EOID'\n%s\nEOID\n" % security_out)
    with io.open(os.path.join(bin_dir, "codesign"), "w", encoding="utf-8") as h:
        h.write(u"#!/bin/sh\nprintf '%%s\\n' \"$@\" >> %s\n" % calls)
    os.chmod(os.path.join(bin_dir, "security"), 0o755)
    os.chmod(os.path.join(bin_dir, "codesign"), 0o755)
    env = dict(os.environ, PATH=bin_dir + os.pathsep + os.environ["PATH"],
               CLIPBOARD_HISTORY_SIGN_IDENTITY=IDENTITY)
    proc = subprocess.run(["/bin/sh", SCRIPT, os.path.join(workdir, "Foo.app")],
                          capture_output=True, text=True, env=env, timeout=60)
    recorded = u""
    if os.path.exists(calls):
        recorded = io.open(calls, encoding="utf-8").read()
    return proc, recorded


class SignBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sign-bundle-")

    def tearDown(self):
        subprocess.run(["/bin/rm", "-rf", self.tmp], check=False)

    def test_prefers_the_fixed_identity_when_it_is_valid(self):
        listed = u'     1) 5F6C0955D4543282F5B2B12A3A2B9FB9FF5CE0A7 "%s"' % IDENTITY
        proc, calls = run_script(listed, self.tmp)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn(u"SIGNATURE_KIND=local", proc.stdout)
        self.assertIn(u"-s", calls)
        self.assertIn(IDENTITY, calls, u"有固定身份却没用 ⇒ CDHash 还会每轮变")

    def test_falls_back_to_adhoc_but_says_so(self):
        proc, calls = run_script(u"     0 valid identities found", self.tmp)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn(u"SIGNATURE_KIND=adhoc", proc.stdout,
                      u"回退 ad-hoc 可以，但必须被报出来 —— 静默回退就是这轮要修的洞")
        self.assertIn(u"-s\n-\n", calls, u"回退那一支必须真的用 ad-hoc（-s -）")

    def test_this_machine_actually_takes_the_identity_branch(self):
        """现读**这台机器**：钥匙串里有那个身份 ⇒ 真签一次必须走 `SIGNATURE_KIND=local`。

        为什么要有这一格：上面两臂喂的是桩，它们永远答"如果身份在/不在"，不答"今天在不在"。
        R553 写这两臂时那一台的现读是回退支（`0 valid identities found`），所以"授权能跨轮活下来"
        当时只是一句期望。用户点过「始终信任」并放行私钥之后，现读变成身份支 ⇒ 这一格把它钉住。
        没有该身份的机器具名 skip（与断言同函数）—— 那不等于合格，只是这一台判不了。
        """
        listed = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"],
                                capture_output=True, text=True, timeout=60)
        if IDENTITY not in listed.stdout:
            self.skipTest(u"SIGN_LIVE_NOT_RUN=no-identity 这一台的钥匙串里没有固定身份"
                          u"（两臂桩测仍然各自判着两条支）")
        work = tempfile.mkdtemp(prefix="sign-live-")
        self.addCleanup(lambda: subprocess.run(["/bin/rm", "-rf", work], check=False))
        bundle = os.path.join(work, u"\u65f6\u95f4\u526a\u53f2.app")   # 与产品同名的 CJK 包
        macos = os.path.join(bundle, "Contents", "MacOS")
        os.makedirs(macos)
        with io.open(os.path.join(bundle, "Contents", "Info.plist"), "w", encoding="utf-8") as h:
            h.write(u'<?xml version="1.0" encoding="UTF-8"?>\n'
                    u'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    u'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    u'<plist version="1.0"><dict>'
                    u'<key>CFBundleExecutable</key><string>ClipboardHistoryApp</string>'
                    u'<key>CFBundleIdentifier</key><string>local.selftest.signlive</string>'
                    u'<key>CFBundleName</key><string>signlive</string>'
                    u'<key>CFBundlePackageType</key><string>APPL</string>'
                    u'</dict></plist>\n')
        exe = os.path.join(macos, "ClipboardHistoryApp")
        with io.open(exe, "w", encoding="utf-8") as h:
            h.write(u"#!/bin/sh\necho live\n")
        os.chmod(exe, 0o755)

        proc = subprocess.run(["/bin/sh", SCRIPT, bundle],
                              capture_output=True, text=True, timeout=180)
        out = proc.stdout + proc.stderr
        self.assertEqual(0, proc.returncode, out)
        self.assertIn(u"SIGNATURE_KIND=local identity=%s" % IDENTITY, proc.stdout,
                      u"这台机器有固定身份却没用 ⇒ CDHash 还会每轮变、桌面授权又会反复弹：" + out)
        self.assertNotIn(u"SIGNATURE_KIND=adhoc", proc.stdout,
                        u"同一跑里既报 local 又报 adhoc ⇒ 报的不是被签那一次的种类：" + out)
        info = subprocess.run(["codesign", "-dvv", bundle],
                              capture_output=True, text=True, timeout=120)
        detail = info.stdout + info.stderr
        self.assertIn(u"Authority=%s" % IDENTITY, detail,
                      u"`SIGNATURE_KIND=local` 报了但包里没有该 Authority ⇒ 读数与被签对象脱节：" + detail)
        self.assertIn(u"flags=0x0", detail,
                      u"固定身份签出来的包 flags 不是 0x0（0x2 才是 adhoc）：" + detail)

    def test_makefile_must_route_signing_through_the_script(self):
        text = io.open(os.path.join(REPO, "Makefile"), encoding="utf-8").read()
        self.assertNotIn(u"codesign -s - --force", text,
                         u"Makefile 又直接 ad-hoc 签名 ⇒ 每轮换 CDHash，桌面授权又会反复弹")
        self.assertIn(u"scripts/sign_bundle.sh", text)

    def test_install_reports_which_signature_it_landed(self):
        text = io.open(os.path.join(REPO, "scripts", "install_local.sh"), encoding="utf-8").read()
        self.assertIn(u"INSTALL_SIGNATURE=adhoc", text)
        self.assertIn(u"INSTALL_SIGNATURE=local", text)
        self.assertLess(text.index(u"INSTALL_SHA_MATCH=1"), text.index(u"INSTALL_SIGNATURE="),
                        u"签名种类要在装完核对之后才报，否则报的不是被装进去那一份")


if __name__ == "__main__":
    unittest.main()
