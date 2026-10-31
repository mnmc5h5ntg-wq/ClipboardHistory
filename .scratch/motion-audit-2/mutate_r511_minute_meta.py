#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R511 变异表二：最小窗分钟档（M1373–M1374）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FMT="Sources/ClipboardHistoryApp/Utilities/ClipboardDateFormatters.swift"
VIEW="Sources/ClipboardHistoryApp/Views/DetailView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1373","分钟档仍带秒",
   FMT,
   '''    static let detailTimestampMinuteCompact: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "M月d日 HH:mm"
        return formatter
    }()''',
   '''    static let detailTimestampMinuteCompact: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "M月d日 HH:mm:ss"
        return formatter
    }()'''),
  ("M1374","详情头部没有分钟档（退回到中间截断）",
   VIEW,
   '''                            headerMeta(entry, includeIcon: false, includeCopyVerb: false,
                                       includeSize: false, includeSeconds: false)''',
   '''                            // M1374：这里被删掉'''),
]
TESTS={
  "M1373": "TimestampYearPolicyTests/testDetailMinuteTimestampDropsSecondsButKeepsTheYearPolicy",
  "M1374": "Round3DetailTypographyTests/testNarrowDetailHeaderFallsBackToCompactMeta",
}

def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    paths=sorted({os.path.join(ROOT,a[2]) for a in ARMS})
    orig={p:open(p,encoding="utf-8").read() for p in paths}
    # 预检：两条判据在未变异时都必须绿
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
