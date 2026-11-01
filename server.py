#!/usr/bin/env python3
# Akilli Cay Bardagi - yerel eski sunucu taklidi V3
# V3: Ayni FLV dosyasini ikinci kez ayni URL ile oynatma hatasini onlemek icin
# sanal soru/video ID'leri kullanir. /videos/200.flv gibi istekler fiziksel olarak
# 030.flv, 036.flv... dosyalarindan servis edilir; Flash ise bunlari farkli URL
# olarak gordugu icin yeni VideoViewer olusturur.

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
import mimetypes
import os
import re
import time

HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "videos"

BASE_QUESTIONS = [
    (30,  "Satin alinabilir mi?"),
    (36,  "Ses cikarir mi?"),
    (55,  "100 yil once de var miydi?"),
    (64,  "Bir alet veya arac mi?"),
    (123, "Kullandikca azalir veya biter mi?"),
]

# Gercek dosya -> metin
BASE_TEXT = {qid: text for qid, text in BASE_QUESTIONS}

# Ilk 5 gercek ID'ye ek olarak 100 adet benzersiz sanal ID.
# Her sanal ID, elimizdeki 5 gercek videodan birine yonlenir.
VIRTUAL_TO_BASE = {}
QUESTION_TEXT = dict(BASE_TEXT)
for n, virtual_id in enumerate(range(200, 300)):
    base_id, text = BASE_QUESTIONS[n % len(BASE_QUESTIONS)]
    VIRTUAL_TO_BASE[virtual_id] = base_id
    QUESTION_TEXT[virtual_id] = text

QUESTION_IDS = [qid for qid, _ in BASE_QUESTIONS] + list(VIRTUAL_TO_BASE)


def subtract_nine(s: str) -> str:
    out = []
    for ch in s:
        if "0" <= ch <= "9":
            out.append(str(9 - int(ch)))
        else:
            out.append(ch)
    return "".join(out)


def crypto_encrypt(text: str) -> str:
    hex_text = "".join(f"{ord(ch):02x}" for ch in text)
    return subtract_nine(hex_text)


def crypto_decrypt(cipher: str) -> str:
    try:
        h = subtract_nine(cipher.strip())
        if len(h) % 2:
            return f"<tek sayida hex karakteri: {h!r}>"
        return "".join(chr(int(h[i:i+2], 16)) for i in range(0, len(h), 2))
    except Exception as e:
        return f"<cozulemedi: {e}>"


def decode_client_q(q_raw: str):
    parts = q_raw.split("-")
    decoded = []
    for i, part in enumerate(parts):
        if not part:
            decoded.append("")
        elif i in (1, 2, 3):
            decoded.append(crypto_decrypt(part))
        else:
            decoded.append(part)
    return parts, decoded


def history_has_qid(history: str, qid: int) -> bool:
    return re.search(rf"(?<!\d)0*{qid}(?!\d)", history or "") is not None


def choose_question(answer_history: str) -> int:
    # Istemcinin gonderdigi gecmiste gorunmeyen ilk ID'yi sec.
    for qid in QUESTION_IDS:
        if not history_has_qid(answer_history, qid):
            return qid
    # 105 farkli URL tukenirse teorik olarak tekrar basa doner.
    # Normal oyun akisi bunun cok once sonlanacaktir.
    return QUESTION_IDS[0]


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[HTTP]", fmt % args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def _serve_virtual_flv(self, qid: int) -> bool:
        base_id = VIRTUAL_TO_BASE.get(qid)
        if base_id is None:
            return False
        src = VIDEO_DIR / f"{base_id:03d}.flv"
        if not src.exists():
            self.send_error(404, f"Base FLV bulunamadi: {src.name}")
            return True

        data = src.read_bytes()
        print(f"[VIDEO ALIAS] {qid:03d}.flv -> {base_id:03d}.flv ({len(data)} byte)")
        self.send_response(200)
        self.send_header("Content-Type", "video/x-flv")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(data)
        return True

    def do_GET(self):
        parsed = urlparse(self.path)

        # Sanal video yolu: /videos/200.flv ... /videos/299.flv
        m = re.fullmatch(r"/videos/(\d+)\.flv", parsed.path, flags=re.IGNORECASE)
        if m:
            qid = int(m.group(1))
            if self._serve_virtual_flv(qid):
                return

        if parsed.path.lower() == "/default.aspx":
            qs = parse_qs(parsed.query, keep_blank_values=True)
            c = qs.get("c", [""])[0]
            q_raw = unquote(qs.get("q", [""])[0])
            raw_parts, decoded_parts = decode_client_q(q_raw) if q_raw else ([""], ["<q yok>"])
            answer_history = decoded_parts[2] if len(decoded_parts) > 2 else ""

            print("\n=== OYUNDAN ISTEK ===")
            print("c =", c)
            print("q (sifreli) =", q_raw)
            for i, part in enumerate(decoded_parts):
                if part:
                    print(f"q parca {i} =", part)

            qid = choose_question(answer_history)
            base_id = VIRTUAL_TO_BASE.get(qid, qid)
            payload = (f"ok=1,id={qid},text={QUESTION_TEXT[qid]},"
                       f"guess=0,badword=0")
            encrypted = crypto_encrypt(payload)
            body = f"servertime={int(time.time())}##{encrypted}"
            data = body.encode("ascii")

            if qid in VIRTUAL_TO_BASE:
                print(f"secili soru = {qid} (sanal video -> {base_id:03d}.flv)")
            else:
                print(f"secili soru = {qid} (gercek video {base_id:03d}.flv)")
            print("cevap (acik) =", payload)
            print("cevap (ham)  =", body)
            print("=====================\n")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=us-ascii")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path.lower() == "/crossdomain.xml":
            body = ("<?xml version=\"1.0\"?>\n"
                    "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.adobe.com/xml/dtds/cross-domain-policy.dtd\">\n"
                    "<cross-domain-policy>\n"
                    "  <allow-access-from domain=\"*\" />\n"
                    "</cross-domain-policy>\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/x-cross-domain-policy")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/__test":
            plain = "ok=1,id=200,text=Satin alinabilir mi?,guess=0,badword=0"
            cipher = crypto_encrypt(plain)
            body = ("SERVER V3 OK\n"
                    "Video alias testi: /videos/200.flv -> 030.flv\n"
                    f"encrypt: {plain} -> {cipher}\n"
                    f"decrypt: {cipher} -> {crypto_decrypt(cipher)}\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        return super().do_GET()

    def do_POST(self):
        return self.do_GET()


if __name__ == "__main__":
    os.chdir(ROOT)
    print("Akilli Cay Bardagi yerel sunucusu V3")
    print(f"Klasor : {ROOT}")
    print(f"Adres  : http://{HOST}:{PORT}/")
    print(f"Test   : http://{HOST}:{PORT}/__test")
    print(f"SWF    : http://{HOST}:{PORT}/Main.swf")
    print("V3: 5 gercek videoya ek 100 sanal benzersiz video ID'si aktif.")
    print("\nPencereyi oyun acikken kapatma. Durdurmak icin Ctrl+C.\n")
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu durduruldu.")
