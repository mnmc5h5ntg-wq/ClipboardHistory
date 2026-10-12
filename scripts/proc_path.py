#!/usr/bin/env python3
"""打印某个 pid 的可执行文件**原始路径**：`python3 scripts/proc_path.py <pid>`。

为什么要有这个文件（2026-10-12 真炸过一次）：`install_local.sh` 要判断
"正在跑的那一份就是我要替换的那一份"，靠的是拿进程的可执行路径和
`/Applications/时间剪史.app/...` 比。而这台机器上 App 的名字是中文：
`lsof` / `ps` 输出非 ASCII 路径时会把它**转义成 `\\346\\227\\266…` 八进制串**，
于是比较永远不相等 ⇒ 脚本判定"没在跑" ⇒ 跳过退出旧版 ⇒ 下一步冒烟闸门被
第二实例守卫假报成失败（这正是脚本文件头第 1 条警告的那个形状）。

`proc_pidpath`（libproc，属 libSystem）返回的是**未转义的字节**，解码后就是真路径，
不需要去猜每个工具的转义规矩。

退出码：0 = 打印成功；1 = 拿不到（pid 不存在、没权限、或非 macOS）。
"""
import ctypes
import sys

def path_of(pid: int) -> str:
    buf = ctypes.create_string_buffer(4096)
    lib = ctypes.CDLL(None)
    n = lib.proc_pidpath(ctypes.c_int(pid), buf, ctypes.c_uint(4096))
    if n <= 0:
        raise OSError("proc_pidpath(%d) -> %d" % (pid, n))
    # 只取到第一个 NUL：缓冲区后面是脏字节。
    return buf.raw[:n].split(b"\0")[0].decode("utf-8", "surrogateescape")


def main(argv):
    # 仓库有一条守卫（`test_script_help_runs`）要求 `scripts/` 下每个脚本 `--help` 都零退出。
    # 手写参数解析的脚本也要遵守：否则它就是"唯一不能 --help 的那个"，
    # 而那条守卫的判据会从"每个脚本"悄悄退化成"大多数脚本"。
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        sys.stdout.write("usage: proc_path.py <pid>\n"
                         "打印某个 pid 的可执行文件原始路径（CJK 不转义）；拿不到时非零退出，不打印空行。\n")
        return 0
    if len(argv) != 2:
        sys.stderr.write("usage: proc_path.py <pid>\n")
        return 2
    try:
        pid = int(argv[1])
    except ValueError:
        sys.stderr.write("pid 必须是整数，收到 %r\n" % argv[1])
        return 2
    try:
        sys.stdout.write(path_of(pid) + "\n")
    except OSError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
