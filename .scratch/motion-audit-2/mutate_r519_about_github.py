#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R519 变异表：关于页 GitHub 链接（M1387–M1388）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Views/SettingsView.swift"
PRES="Sources/ClipboardHistoryApp/Utilities/AboutPresentation.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1387","关于页把链接画成普通文字", VIEW,
   '''                    if let githubURL = URL(string: AboutPresentation.githubURLString) {
                        Link("GitHub 项目主页 ↗", destination: githubURL)
                            .font(.system(size: VisualFont.body))
                    }''',
   '''                    Text("GitHub 项目主页 ↗")
                        .font(.system(size: VisualFont.body))'''),
  ("M1388","GitHub URL 指向别处", PRES,
   '''    static let githubURLString = "https://github.com/mnmc5h5ntg-wq/ClipboardHistory"''',
   '''    static let githubURLString = "https://example.com/other"'''),
]
TESTS={
  "M1387": "AboutPageGitHubLinkTests/testGitHubURLHasOneSourceAndTheAboutPageUsesALink",
  "M1388": "AboutPageGitHubLinkTests/testGitHubURLHasOneSourceAndTheAboutPageUsesALink",
}
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
