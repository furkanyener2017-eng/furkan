from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import time
import re

BASE_QUESTIONS = [
    (30, "Satin alinabilir mi?"),
    (36, "Ses cikarir mi?"),
    (55, "100 yil once de var miydi?"),
    (64, "Bir alet veya arac mi?"),
    (123, "Kullandikca azalir veya biter mi?")
]

def subtract_nine(s):
    return ''.join(str(9-int(c)) if c.isdigit() else c for c in s)

def encrypt(text):
    return subtract_nine(''.join(f'{ord(c):02x}' for c in text))

def decrypt(cipher):
    try:
        h = subtract_nine(cipher.strip())
        return ''.join(chr(int(h[i:i+2],16)) for i in range(0,len(h),2))
    except:
        return ''

def handler(q):
    parts = q.split('-')
    decoded = [decrypt(p) if i in (1,2,3) and p else p
               for i,p in enumerate(parts)]
    history = decoded[2] if len(decoded)>2 else ''

    for qid,text in BASE_QUESTIONS:
        if not re.search(rf'(?<!\d)0*{qid}(?!\d)',history):
            return qid,text

    return BASE_QUESTIONS[0]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/default.aspx'):
            qs = parse_qs(self.path.split('?',1)[1] if '?' in self.path else '')
            q = unquote(qs.get('q',[''])[0])
            qid,text = handler(q)
            payload = f'ok=1,id={qid},text={text},guess=0,badword=0'
            body = f'servertime={int(time.time())}##{encrypt(payload)}'
            data = body.encode('ascii')
            self.send_response(200)
            self.send_header('Content-Type','text/plain; charset=us-ascii')
            self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()
