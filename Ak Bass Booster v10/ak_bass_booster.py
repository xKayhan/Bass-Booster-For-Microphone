"""
AK Company Bass Booster v4.0
- Mikrofon giriş seçimi
- Çıkış cihaz seçimi (VB-Cable için)
- Kendi sesini duymaz
pip install pyaudio numpy scipy
"""

import tkinter as tk
import sys
import os
from tkinter import ttk
import math
import threading
import numpy as np
import pyaudio
import scipy.signal as dsp

def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

RATE     = 44100
CHUNK    = 512
FMT      = pyaudio.paInt16
CHANNELS = 1

# ═══════════════════════════════════════════════════════════════════════════════
#  BASS İŞLEME
# ═══════════════════════════════════════════════════════════════════════════════

def make_low_shelf(gain_db, freq=150, rate=RATE):
    gain_db = min(gain_db, 40.0)
    if gain_db < 0.1:
        return None, None
    A  = 10 ** (gain_db / 40.0)
    w0 = 2 * math.pi * freq / rate
    cw = math.cos(w0); sw = math.sin(w0)
    alpha = sw / 2 * math.sqrt((A + 1/A) + 2)
    b0 =  A*((A+1)-(A-1)*cw+2*math.sqrt(A)*alpha)
    b1 = 2*A*((A-1)-(A+1)*cw)
    b2 =  A*((A+1)-(A-1)*cw-2*math.sqrt(A)*alpha)
    a0 =    (A+1)+(A-1)*cw+2*math.sqrt(A)*alpha
    a1 = -2*((A-1)+(A+1)*cw)
    a2 =    (A+1)+(A-1)*cw-2*math.sqrt(A)*alpha
    return (np.array([b0/a0, b1/a0, b2/a0]),
            np.array([1.0,   a1/a0, a2/a0]))

def process_bass(audio, knob_val):
    if knob_val < 0.01:
        return audio
    eq_db = knob_val * 40.0
    b, a  = make_low_shelf(eq_db)
    if b is not None:
        audio = dsp.lfilter(b, a, audio)
    amp   = 1.0 + (math.exp(knob_val * 5.5) - 1) * 0.8
    audio = audio * amp
    if knob_val > 0.25:
        thresh = max(32768.0 * (1.0 - knob_val * 0.85), 400.0)
        audio  = np.clip(audio, -thresh, thresh)
        diff   = np.diff(audio, prepend=audio[0])
        audio  = audio + diff * (knob_val * 0.6)
    return np.clip(audio, -32768, 32767)


# ═══════════════════════════════════════════════════════════════════════════════
#  SES MOTORU
# ═══════════════════════════════════════════════════════════════════════════════
class Engine:
    def __init__(self):
        self._pa      = pyaudio.PyAudio()
        self._lock    = threading.Lock()
        self._restart = threading.Event()
        self._stop    = threading.Event()
        self._knob    = 0.0
        self._rms     = 0.0
        self._in_idx  = None
        self._out_idx = None
        threading.Thread(target=self._run, daemon=True).start()

    def set_knob(self, v):
        with self._lock: self._knob = float(v)

    def set_devices(self, in_idx, out_idx):
        with self._lock:
            self._in_idx  = in_idx
            self._out_idx = out_idx
        self._restart.set()

    def get_rms(self):
        with self._lock: return self._rms

    def stop(self):
        self._stop.set()

    def list_devices(self):
        ins, outs = [], []
        for i in range(self._pa.get_device_count()):
            d = self._pa.get_device_info_by_index(i)
            if d["maxInputChannels"]  > 0: ins.append( (i, d["name"]) )
            if d["maxOutputChannels"] > 0: outs.append((i, d["name"]) )
        return ins, outs

    def default_devices(self):
        try:    di  = self._pa.get_default_input_device_info()["index"]
        except: di  = None
        try:    do_ = self._pa.get_default_output_device_info()["index"]
        except: do_ = None
        return di, do_

    def _open(self, ii, oi):
        kw = {}
        if ii  is not None: kw["input_device_index"]  = ii
        if oi  is not None: kw["output_device_index"] = oi
        return self._pa.open(
            format=FMT, channels=CHANNELS, rate=RATE,
            input=True, output=True,
            frames_per_buffer=CHUNK, **kw
        )

    def _run(self):
        stream = None
        while not self._stop.is_set():
            if self._restart.is_set():
                self._restart.clear()
                if stream:
                    try: stream.stop_stream(); stream.close()
                    except: pass
                stream = None

            if stream is None:
                with self._lock: ii, oi = self._in_idx, self._out_idx
                try:
                    stream = self._open(ii, oi)
                except Exception as e:
                    print(f"Cihaz hatası: {e}")
                    self._stop.wait(2)
                    continue

            try:
                raw   = stream.read(CHUNK, exception_on_overflow=False)
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

                with self._lock: knob = self._knob

                rms = float(np.sqrt(np.mean(audio**2))) / 32768.0
                with self._lock: self._rms = min(rms * (1 + knob * 4), 1.0)

                # Bass işle → CABLE Input'a gönder (kendi hoparlörüne değil)
                out = process_bass(audio.copy(), knob)
                stream.write(out.astype(np.int16).tobytes())

            except Exception:
                stream = None
                continue

        if stream:
            try: stream.stop_stream(); stream.close()
            except: pass
        self._pa.terminate()


# ═══════════════════════════════════════════════════════════════════════════════
#  KNOB
# ═══════════════════════════════════════════════════════════════════════════════
class Knob(tk.Canvas):
    def __init__(self, parent, size=160, on_change=None, **kw):
        super().__init__(parent, width=size, height=size,
                         bg="#1a1208", highlightthickness=0, **kw)
        self.size      = size
        self.on_change = on_change
        self._val      = 0.0
        self._drag_y   = None
        self.bind("<ButtonPress-1>",   self._press)
        self.bind("<B1-Motion>",       self._drag)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<MouseWheel>",      self._scroll)
        self._draw()

    def set(self, v):
        self._val = max(0.0, min(1.0, v))
        self._draw()

    def get(self): return self._val

    def _angle(self):
        return 225.0 - self._val * 270.0

    def _draw(self):
        self.delete("all")
        cx = cy = self.size / 2
        r_outer = self.size / 2 - 6
        r_inner = r_outer - 14
        r_mark  = r_inner - 8

        for i in range(12):
            t = i / 11; gray = int(40 + t * 30)
            col = f"#{gray:02x}{gray:02x}{gray:02x}"
            self.create_oval(cx-r_outer+i, cy-r_outer+i,
                             cx+r_outer-i, cy+r_outer-i, outline=col, width=1)

        self._arc(cx, cy, r_inner+6, 225, -270, "#2a2a2a", 6)

        if self._val > 0.01:
            self._arc(cx, cy, r_inner+6, 225, -(self._val*270), "#ff8800", 6)
            ang_r = math.radians(self._angle())
            ex = cx + (r_inner+6)*math.cos(ang_r)
            ey = cy - (r_inner+6)*math.sin(ang_r)
            self.create_oval(ex-5, ey-5, ex+5, ey+5, fill="#ffcc00", outline="")

        self.create_oval(cx-r_inner+3, cy-r_inner+3,
                         cx+r_inner+3, cy+r_inner+3, fill="#0a0a0a", outline="")
        for i in range(24, 0, -1):
            t = i/24; r = r_inner*t
            lum = int(28 + (1-t)*55)
            col = f"#{lum:02x}{lum:02x}{lum:02x}"
            self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=col, outline="")
        self.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner,
                         fill="", outline="#555555", width=2)

        ang_r = math.radians(self._angle())
        ix = cx + r_mark*0.35*math.cos(ang_r)
        iy = cy - r_mark*0.35*math.sin(ang_r)
        ox = cx + r_mark*math.cos(ang_r)
        oy = cy - r_mark*math.sin(ang_r)
        self.create_line(ix, iy, ox, oy, fill="#ffcc00", width=3, capstyle=tk.ROUND)
        self.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#333333", outline="#666")

    def _arc(self, cx, cy, r, start, extent, color, width):
        steps = max(int(abs(extent)/3), 6)
        pts = []
        for i in range(steps+1):
            a = math.radians(start + extent*i/steps)
            pts.append(cx + r*math.cos(a))
            pts.append(cy - r*math.sin(a))
        if len(pts) >= 4:
            self.create_line(*pts, fill=color, width=width,
                             capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)

    def _press(self, e):   self._drag_y = e.y
    def _release(self, e): self._drag_y = None

    def _drag(self, e):
        if self._drag_y is None: return
        dy = self._drag_y - e.y
        self._drag_y = e.y
        self.set(self._val + dy/220)
        if self.on_change: self.on_change(self._val)

    def _scroll(self, e):
        self.set(self._val + (0.03 if e.delta > 0 else -0.03))
        if self.on_change: self.on_change(self._val)


# ═══════════════════════════════════════════════════════════════════════════════
#  VU METER
# ═══════════════════════════════════════════════════════════════════════════════
class VUMeter(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, width=16, height=120,
                         bg="#1a1208", highlightthickness=0, **kw)
        self._draw(0.0)

    def update_level(self, v):
        self._draw(max(0.0, min(1.0, v)))

    def _draw(self, level):
        self.delete("all")
        segs = 20
        sh   = (120 - segs) / segs
        for i in range(segs):
            t  = (segs-1-i)/(segs-1)
            y1 = i*(sh+1); y2 = y1+sh
            lit = t <= level
            if   t > 0.8:  col = "#ff2244" if lit else "#2a0808"
            elif t > 0.55: col = "#ff8800" if lit else "#221408"
            else:          col = "#00e676" if lit else "#082208"
            self.create_rectangle(2, y1, 14, y2, fill=col, outline="")


# ═══════════════════════════════════════════════════════════════════════════════
#  ANA PENCERE
# ═══════════════════════════════════════════════════════════════════════════════
class AKBassBooster:
    BG   = "#1a1208"
    GOLD = "#c8860a"
    DIM  = "#7a6030"
    DARK = "#0f0b04"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AK Company Bass Booster")
        self.root.resizable(False, False)
        self.root.configure(bg=self.DARK)
        try:
            self.root.iconbitmap(resource_path("ak_icon.ico"))
        except Exception:
            pass

        self.engine   = Engine()
        self._in_map  = {}
        self._out_map = {}

        self._build()
        self._load_devices()
        self._vu_tick()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    # ── cihaz yükleme ─────────────────────────────────────────────────────────
    def _load_devices(self):
        ins, outs = self.engine.list_devices()
        di, do_   = self.engine.default_devices()

        self._in_map  = {f"[{i}] {n}": i for i, n in ins}
        self._out_map = {f"[{i}] {n}": i for i, n in outs}

        self.cb_in["values"]  = list(self._in_map.keys())
        self.cb_out["values"] = list(self._out_map.keys())

        # VB-Cable varsa otomatik seç
        cable_in  = next((k for k in self._in_map  if "CABLE" in k.upper()), None)
        cable_out = next((k for k in self._out_map if "CABLE" in k.upper()), None)

        # Giriş: gerçek mikrofon (CABLE Output DEĞİL)
        default_in = next((k for k in self._in_map
                           if self._in_map[k] == di), None)
        if default_in:
            self.cb_in.set(default_in)
        elif self._in_map:
            self.cb_in.current(0)

        # Çıkış: CABLE Input (varsa), yoksa varsayılan
        if cable_out:
            self.cb_out.set(cable_out)
        else:
            default_out = next((k for k in self._out_map
                                if self._out_map[k] == do_), None)
            if default_out: self.cb_out.set(default_out)
            elif self._out_map: self.cb_out.current(0)

        self._apply_devices()

    def _apply_devices(self, *_):
        ii = self._in_map.get(self.cb_in.get())
        oi = self._out_map.get(self.cb_out.get())
        self.engine.set_devices(ii, oi)

        # Durum etiketi güncelle
        out_name = self.cb_out.get()
        if "CABLE" in out_name.upper():
            self.lbl_status.config(
                text="✔ CABLE Input'a gönderiliyor → Discord'da CABLE Output seç",
                fg="#00e676")
        else:
            self.lbl_status.config(
                text="by AgahanKayhan🖤",
                fg="#ff8800")

    # ── VU ────────────────────────────────────────────────────────────────────
    def _vu_tick(self):
        self.vu.update_level(self.engine.get_rms())
        self.root.after(40, self._vu_tick)

    def _knob_changed(self, val):
        db = val * 600.0
        self.lbl_db.config(text=f"+{db:.1f} dB")
        self.engine.set_knob(val)

    def _quit(self):
        self.engine.stop()
        self.root.destroy()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        R = self.root

        # Combobox stili
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Dark.TCombobox",
            fieldbackground="#221a0a", background="#1a1208",
            foreground="#c8860a", selectbackground="#2a1d08",
            selectforeground="#c8860a", bordercolor="#3a2a10",
            arrowcolor="#7a6030", padding=3)
        s.map("Dark.TCombobox",
            fieldbackground=[("readonly","#221a0a")],
            foreground=[("readonly","#c8860a")])

        outer = tk.Frame(R, bg="#3a2a10", padx=3, pady=3)
        outer.pack()
        inner = tk.Frame(outer, bg=self.DARK)
        inner.pack()

        # Başlık
        tb = tk.Frame(inner, bg="#2a1d08", height=36)
        tb.pack(fill="x"); tb.pack_propagate(False)
        tk.Label(tb, text="AK Bass Booster V10",
                 fg=self.GOLD, bg="#2a1d08",
                 font=("Courier New", 11, "bold")).pack(side="left", padx=16, pady=8)
        tk.Label(tb, text="v4.0", fg=self.DIM, bg="#2a1d08",
                 font=("Courier New", 8)).pack(side="right", padx=10)

        tk.Frame(inner, bg=self.GOLD, height=1).pack(fill="x")

        # ── Cihaz Seçimi ──────────────────────────────────────────────────────
        dev = tk.Frame(inner, bg="#110d04", padx=16, pady=10)
        dev.pack(fill="x")

        # Giriş
        row1 = tk.Frame(dev, bg="#110d04")
        row1.pack(fill="x", pady=(0,6))
        tk.Label(row1, text="MİKROFON:", fg=self.DIM, bg="#110d04",
                 font=("Courier New", 7, "bold"), width=12, anchor="w").pack(side="left")
        self.cb_in = ttk.Combobox(row1, state="readonly",
                                   font=("Courier New", 7), style="Dark.TCombobox", width=38)
        self.cb_in.pack(side="left")
        self.cb_in.bind("<<ComboboxSelected>>", self._apply_devices)

        # Çıkış
        row2 = tk.Frame(dev, bg="#110d04")
        row2.pack(fill="x")
        tk.Label(row2, text="ÇIKIŞ:", fg=self.DIM, bg="#110d04",
                 font=("Courier New", 7, "bold"), width=12, anchor="w").pack(side="left")
        self.cb_out = ttk.Combobox(row2, state="readonly",
                                    font=("Courier New", 7), style="Dark.TCombobox", width=38)
        self.cb_out.pack(side="left")
        self.cb_out.bind("<<ComboboxSelected>>", self._apply_devices)

        tk.Frame(inner, bg="#2a1d08", height=1).pack(fill="x")

        # ── Knob + VU ─────────────────────────────────────────────────────────
        body = tk.Frame(inner, bg=self.BG, padx=24, pady=16)
        body.pack(fill="both")

        left = tk.Frame(body, bg=self.BG)
        left.pack(side="left", padx=(0,20))

        tk.Label(left, text="B A S S   L E V E L",
                 fg=self.DIM, bg=self.BG,
                 font=("Courier New", 7, "bold")).pack(pady=(0,8))

        self.knob = Knob(left, size=160, on_change=self._knob_changed)
        self.knob.pack()

        self.lbl_db = tk.Label(left, text="0.0 dB",
                                fg=self.GOLD, bg=self.BG,
                                font=("Courier New", 13, "bold"))
        self.lbl_db.pack(pady=(10,0))
        tk.Label(left, text="↑ kaydır veya sürükle",
                 fg=self.DIM, bg=self.BG,
                 font=("Courier New", 7)).pack(pady=(4,0))

        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", anchor="center")
        tk.Label(right, text="OUT", fg=self.DIM, bg=self.BG,
                 font=("Courier New", 7)).pack(pady=(0,6))
        self.vu = VUMeter(right)
        self.vu.pack()

        # ── Durum mesajı ──────────────────────────────────────────────────────
        tk.Frame(inner, bg=self.GOLD, height=1).pack(fill="x")

        status_bar = tk.Frame(inner, bg="#110d04", padx=10, pady=6)
        status_bar.pack(fill="x")
        self.lbl_status = tk.Label(status_bar,
                                    text="Cihazlar yükleniyor...",
                                    fg=self.DIM, bg="#110d04",
                                    font=("Courier New", 7),
                                    wraplength=420, justify="left")
        self.lbl_status.pack(anchor="w")

        # Alt bilgi
        tk.Frame(inner, bg="#2a1d08", height=1).pack(fill="x")
        foot = tk.Frame(inner, bg="#1a1208", height=22)
        foot.pack(fill="x"); foot.pack_propagate(False)
        lnk = tk.Label(foot, text="by AgahanKayhan",
                 fg=self.DIM, bg="#1a1208",
                 font=("Courier New", 7), cursor="hand2")
        lnk.pack(side="right", padx=10, pady=4)
        lnk.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://xkayhan.github.io/"))
        lnk.bind("<Enter>", lambda e: lnk.config(fg=self.GOLD, font=("Courier New", 7, "underline")))
        lnk.bind("<Leave>", lambda e: lnk.config(fg=self.DIM,  font=("Courier New", 7)))
        tk.Label(foot, text="mikrofon → bass boost → CABLE Input → Discord",
                 fg="#3a3020", bg="#1a1208",
                 font=("Courier New", 7)).pack(side="left", padx=10, pady=4)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AKBassBooster().run()