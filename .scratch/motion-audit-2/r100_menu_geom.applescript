on run argv
  tell application "System Events"
    key code 53
    delay 0.3
    tell (first process whose unix id is 5779)
      click menu bar item 1 of menu bar 2
      delay 0.9
      set out to ""
      try
        set m to menu 1 of menu bar item 1 of menu bar 2
        set pp to position of m
        set ss to size of m
        set out to out & "MENU pos=" & (item 1 of pp) & "," & (item 2 of pp) & " size=" & (item 1 of ss) & "x" & (item 2 of ss) & linefeed
        set n to count of menu items of m
        set out to out & "items=" & n & linefeed
        repeat with i from 1 to n
          try
            set qi to position of menu item i of m
            set wi to item 1 of (size of menu item i of m)
            set out to out & i & " pos=" & (item 1 of qi) & "," & (item 2 of qi) & " w=" & wi & linefeed
          end try
        end repeat
      on error errMsg
        set out to out & "ERR " & errMsg & linefeed
      end try
      key code 53
      return out
    end tell
  end tell
end run
(*
  R100 的读法记录（不是脚本的一部分，别取消注释）：
  * 为什么走 AX 几何而不是截图：真状态菜单里是**用户真实剪贴板原文**，
    规矩是"帧与日志里不许出现用户内容" ⇒ 只读 position/size 这些数字，
    菜单项标题**只用来等值比较、一律不打印**（本轮连比较都没做，只要几何）。
  * 实测：MENU pos=1073,34 size=207x294，items=15。
    复刻夹具 `menubar-*` 是 320pt 宽 ⇒ 两侧第一次都有数了（207 vs 320，差 1.55 倍），
    这条喂给 `menuSurfaceReplicaFixtures` 那条注释（R34 当年只量过复刻那一侧）。
  * 两个 AppleScript 坑（都是"变量名撞上保留字"，报错文案像"不允许访问"，容易误判成权限问题）：
      `set it to …`  ✗（it 是保留字）
      `set ip to …`  ✗（大小写不敏感，撞上 IP）
      改 `set qi / pp / ss / wi` 就通了。
  * 逐项 position 那一段在 NSMenu 处于 tracking 状态时拿不到值（内层 try 全吞掉，
    所以输出里只有 MENU 与 items 两行）⇒ **要逐行的左沿，得换路子**：
    要么菜单不 open 时读（读不到），要么只能截图（有用户内容，不走）。
    这条就是 149 里"139/130 还欠一次换分区"的同类墙：AX 能开菜单、能读窗口，
    但驱动不了 SwiftUI List 的选中，也拿不到 tracking 中菜单的逐行几何。
  * 收尾：脚本进出各按一次 Escape（key code 53），把用户的会话还原成原样。
*)
