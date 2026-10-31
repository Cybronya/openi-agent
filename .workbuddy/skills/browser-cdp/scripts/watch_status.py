#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""轮询任务状态栏，记录变化时间线。

用法: python tools/watch_status.py <秒数> [间隔秒]
"""
import json, subprocess, sys, time, os

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON = os.path.join(HERE, 'cdp_daemon.py')

EXPR = r"""(()=>{
  const trs=[...document.querySelectorAll('table tbody tr')];
  const r0=trs[0];
  const tds=r0?[...r0.querySelectorAll('td')].map(c=>c.innerText.replace(/\s+/g,' ').trim()):[];
  // 状态列（第4列，索引3）里的徽标文字
  const badge=r0?(r0.querySelectorAll('td')[3]?.innerText.replace(/\s+/g,' ').trim()||''):'';
  const badgeCls=r0?([...(r0.querySelectorAll('td')[3]?.querySelectorAll('*')||[])]
      .map(e=>e.className).filter(c=>typeof c==='string'&&/badge|status|tag/i.test(c))[0]||''):'';
  // 找同任务名的行（第二张表的任务名）
  const nameRows=[...document.querySelectorAll('table')][3];
  const name=nameRows?(nameRows.querySelectorAll('tbody tr')[0]?.innerText.trim()||''):'';
  // 弹窗与提示
  const dialogs=[...document.querySelectorAll('.el-dialog,.el-message-box')].filter(d=>d.offsetParent!==null)
      .map(d=>d.innerText.replace(/\s+/g,' ').trim().slice(0,200));
  const msgs=[...document.querySelectorAll('.el-message,.el-notification')].filter(m=>m.offsetParent!==null)
      .map(m=>m.innerText.replace(/\s+/g,' ').trim().slice(0,150));
  return JSON.stringify({
    状态徽标:badge, 徽标样式:badgeCls,
    首行单元格:tds,
    任务名:name,
    可见弹窗:dialogs, 可见提示:msgs,
    按钮集:r0?[...r0.querySelectorAll('a,button')].map(b=>b.innerText.trim()).filter(Boolean):[]
  });})()"""


def poll():
    req = json.dumps({"cmd": "eval", "expr": EXPR, "match": "openi"}, ensure_ascii=False)
    out = subprocess.run([sys.executable, DAEMON, "--client", req],
                         capture_output=True, text=True, timeout=120)
    try:
        r = json.loads(out.stdout.strip())
    except Exception:
        return {"error": out.stdout[:200] + out.stderr[:200]}
    if not r.get("ok"):
        return {"error": r.get("error")}
    raw = r.get("result")
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {"raw": raw}


def main():
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 120
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 4
    t0 = time.time()
    timeline = []
    last_sig = None
    print(f"开始轮询 {duration}s，间隔 {interval}s\n")
    while time.time() - t0 < duration:
        el = round(time.time() - t0, 1)
        d = poll()
        sig = json.dumps({k: d.get(k) for k in ("状态徽标", "任务名", "可见提示")}, ensure_ascii=False)
        changed = sig != last_sig
        if changed or not timeline:
            timeline.append({"t": el, "snap": d})
            print(f"[{el:>6.1f}s] {'★ 变化' if changed else '基线'}")
            print(f"   状态徽标: {d.get('状态徽标')!r}  样式: {d.get('徽标样式')!r}")
            print(f"   任务名  : {d.get('任务名')!r}")
            print(f"   弹窗    : {d.get('可见弹窗')}")
            print(f"   提示    : {d.get('可见提示')}")
            print(f"   按钮集  : {d.get('按钮集')}")
            print()
        last_sig = sig
        time.sleep(interval)
    with open(os.path.join(HERE, "..", "docs", "status_timeline.json"), "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"共记录 {len(timeline)} 个状态点，已存 docs/status_timeline.json")


if __name__ == "__main__":
    main()
