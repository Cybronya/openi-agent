import json, subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON = os.path.join(HERE, 'cdp_daemon.py')


def send(req):
    out = subprocess.run([sys.executable, DAEMON, '--client', json.dumps(req, ensure_ascii=False)],
                         capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (out.stdout + out.stderr)[:300]}


CODE = """import platform, sys
print("platform:", platform.platform())
print("python:", sys.version.split()[0])
try:
    import torch
    print("torch:", torch.__version__)
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("gpu:", torch.cuda.get_device_name(0))
except Exception as e:
    print("torch unavailable:", e)
"""


def main():
    # 1) 写入代码到单元格
    expr = (
        "(()=>{const nb=document.querySelector('.jp-Notebook');"
        "if(!nb) return 'no notebook';"
        "const cmEl=nb.querySelector('.CodeMirror');"
        "if(!cmEl||!cmEl.CodeMirror) return 'no codemirror';"
        "const cm=cmEl.CodeMirror;"
        f"cm.setValue({json.dumps(CODE)});"
        "return 'typed ' + cm.getValue().length + ' chars';})()"
    )
    r = send({'cmd': 'eval', 'expr': expr, 'match': 'mlunotebook'})
    print('写入:', r.get('result') or r.get('error'))

    time.sleep(1)

    # 2) 执行：Shift+Enter（等价于点击 Run 按钮）
    expr2 = (
        "(()=>{const cmEl=document.querySelector('.jp-Notebook .CodeMirror');"
        "if(!cmEl||!cmEl.CodeMirror) return 'no cm';"
        "const cm=cmEl.CodeMirror;"
        "cm.focus();"
        "cm.setCursor(cm.lineCount(), 0);"
        "const ev=(t)=>{const E=KeyboardEvent; cm.dispatchEvent(new E('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,shiftKey:true,bubbles:true,cancelable:true}));};"
        "ev();"
        "return 'sent shift+enter';})()"
    )
    r2 = send({'cmd': 'eval', 'expr': expr2, 'match': 'mlunotebook'})
    print('执行:', r2.get('result') or r2.get('error'))

    # 3) 等待并读取输出
    for i in range(12):
        time.sleep(3)
        expr3 = (
            "(()=>{const outs=[...document.querySelectorAll('.jp-OutputArea-output, .jp-RenderedHTMLCommon')]"
            ".map(e=>e.innerText.trim()).filter(Boolean);"
            "const cells=[...document.querySelectorAll('.jp-Cell')].length;"
            "const st=document.querySelector('.jp-modals')?'':document.body.innerText.slice(-200);"
            "return JSON.stringify({cells, outputs:outs, 尾部:st});})()"
        )
        r3 = send({'cmd': 'eval', 'expr': expr3, 'match': 'mlunotebook'})
        val = r3.get('result')
        if val:
            try:
                d = json.loads(val)
                if d.get('outputs'):
                    print(f'\n=== 执行输出（第 {i+1} 次轮询）===')
                    for o in d['outputs']:
                        print(o)
                    break
                print(f'[{i+1}] 暂无输出 cells={d.get("cells")}')
            except Exception:
                print(val[:300])
    else:
        print('超时未捕获到输出')


if __name__ == '__main__':
    main()
