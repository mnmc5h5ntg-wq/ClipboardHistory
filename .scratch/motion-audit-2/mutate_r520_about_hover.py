#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R520 变异表：关于页 GitHub 链接悬停下划线（M1389–M1390）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Views/SettingsView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1389","悬停不再画下划线", VIEW,
   '''                                .overlay(alignment: .bottom) {
                                    Rectangle()
                                        .fill(Color.accentColor)
                                        .frame(height: 1)
                                        .scaleEffect(x: aboutGitHubLinkHoveredForDrawing ? 1 : 0,
                                                     anchor: .leading)
                                        .opacity(aboutGitHubLinkHoveredForDrawing ? 1 : 0)
                                        .animation(MotionCatalog.animation(for: .hover),
                                                   value: aboutGitHubLinkHoveredForDrawing)
                                }''',
   '''                                // M1389：下划线被删掉'''),
  ("M1390","取证悬停状态接不上", VIEW,
   '''        aboutGitHubLinkHovered || (hoveredForCapture ?? false)''',
   '''        aboutGitHubLinkHovered'''),
]
TESTS={"M1389":"UICaptureTests/testAboutGitHubLinkUnderlinesOnHover",
       "M1390":"UICaptureTests/testAboutGitHubLinkUnderlinesOnHover"}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    paths=sorted({os.path.join(ROOT,a[2]) for a in ARMS})
    orig={p:open(p,encoding="utf-8").read() for p in paths}
    for mid,desc,rel,old,new in ARMS:
        code,out=run(TESTS[mid]); print("预检 %s: %s"%(mid,code))
        if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,rel,old,new in ARMS:
        path=os.path.join(ROOT,rel); cur=orig[path]
        n=cur.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(cur.replace(old,new))
        try: code,out=run(TESTS[mid])
        finally: open(path,"w",encoding="utf-8").write(orig[path])
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=all(open(p,"rb").read()==orig[p].encode("utf-8") for p in paths)
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
