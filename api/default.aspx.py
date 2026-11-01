from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import time
import re

ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT / "videos"

BASE_QUESTIONS = [
    (30, "Satin alinabilir mi?"),
    (36, "Ses cikarir mi?"),
    (55, "100 yil once de var miydi?"),
    (64, "Bir alet veya arac mi?"),
    (123, "Kullandikca azalir veya biter mi?")
]

VIRTUAL = {}
QUESTION_TEXT = dict(BASE_QUESTIONS)

for n, virtual_id in enumerate(range(200, 300)):
    base_id, text = BASE_QUESTIONS[n % len(BASE_QUESTIONS)]
    VIRTUAL[virtual_id] = base_id
    QUESTION_TEXT[virtual_id] = text

QUESTION_IDS = list(QUESTION_TEXT)


def subtract_nine(s):
    return ''.join(str(9 - int(c)) if c.isdigit() else c for c in s)


def encrypt(text):
    return subtract_nine(''.join(f'{ord(c):02x}' for c in text))


def decrypt(cipher):
    try:
        h = subtract_nine(cipher.strip())
        if len(h) % 2:
            return ""
        return ''.join(
            chr(int(h[i:i+2], 16))
            for i in range(0, len(h), 2)
        )
    except Exception:
        return ""


def choose_question(history):
    for qid in QUESTION_IDS:
        if not re.search(rf'(?<!\d)0*{qid}(?!\d)', history or ''):
            return qid
    return QUESTION_IDS[0]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Video isteği
        if 'video' in qs:
            try:
                qid = int(qs['video'][0])
                base_id = VIRTUAL.get(qid)

                if base_id is None:
                    self.send_error(404)
                    return

                video_path = VIDEO_DIR / f"{base_id:03d}.flv"

                if not video_path.is_file():
                    self.send_error(404, "Video bulunamadi")
                    return

                data = video_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'video/x-flv')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
                return

            except (ValueError, OSError):
                self.send_error(404)
                return

        # Oyun soru isteği
        if parsed.path.lower().endswith('default.aspx'):
            q = qs.get('q', [''])[0]
            parts = q.split('-')

            decoded = [
                decrypt(p) if i in (1, 2, 3) and p else p
                for i, p in enumerate(parts)
            ]

            history = decoded[2] if len(decoded) > 2 else ''
            qid = choose_question(history)

            payload = (
                f"ok=1,id={qid},text={QUESTION_TEXT[qid]},"
                f"guess=0,badword=0"
            )

            body = (
                f"servertime={int(time.time())}##{encrypt(payload)}"
            ).encode('ascii')

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=us-ascii')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)
