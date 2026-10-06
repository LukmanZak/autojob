import sys
import time
import threading
import queue
from datetime import datetime

import cv2
import mss
import numpy as np
from PIL import Image, ImageDraw
import pyautogui
from pynput import keyboard, mouse

from PyQt6.QtCore import Qt, QRect, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import QApplication, QWidget

import ctypes

# Disable fail-safe to prevent crash when mouse hits screen corners
pyautogui.FAILSAFE = False

# =========================================================================
# ==================== HD CURSOR SPRITE (like IDE arrow) ==================
# =========================================================================
# Bentuk mengikuti referensi: panah dengan sisi kiri vertikal, ujung kanan
# membulat, dan lekukan concave di tepi bawah. Render HD via supersampling
# PIL (4x) + joint rounded, isi hitam solid + outline putih.
# Hotspot = ujung panah (tip) = posisi mouse.

_CURSOR_SS = 4          # supersampling factor (HD)
_CURSOR_PAD = 10       # padding agar outline tidak kepotong (base units)
_CURSOR_OUTLINE = 22   # tebal outline putih pada resolusi 4x (~2.75px final)

_CURSOR_MASTER = None  # lazy singleton: (PIL.Image RGBA, tip_x, tip_y) @SS


def _quad_bezier(p0, p1, p2, n=14):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _cursor_outline_points():
    # Koordinat lokal base units (lebar ~36, tinggi ~46).
    tip = (3.0, 1.5)
    right = (33.0, 27.5)
    # Tepi bawah: garis horizontal dari ujung kanan ke kiri,
    # lalu melengkung concave (ke dalam) turun ke ujung bawah.
    h_end = (21.5, 27.5)
    curve = _quad_bezier(h_end, (14.0, 27.8), (11.5, 35.0), n=14)
    bottom = (5.0, 44.5)
    pts = [tip, right] + [h_end] + curve[1:] + [bottom]
    return pts


def _get_cursor_master():
    global _CURSOR_MASTER
    if _CURSOR_MASTER is not None:
        return _CURSOR_MASTER
    ss = _CURSOR_SS
    pad = _CURSOR_PAD * ss
    pts = _cursor_outline_points()
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = int(max(xs) * ss + pad * 2)
    h = int(max(ys) * ss + pad * 2)
    shifted = [(x * ss + pad, y * ss + pad) for (x, y) in pts]
    tip = (pts[0][0] * ss + pad, pts[0][1] * ss + pad)

    # Mask bentuk panah hitam, lalu outline putih = dilasi Euclidean
    # (distance transform). Dijamin menutup sempurna di semua sudut
    # termasuk ujung tip — tidak ada lagi joint yang kepotong.
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(shifted, fill=255)
    m = np.array(mask)
    dist = cv2.distanceTransform(255 - m, cv2.DIST_L2, 3)
    halo = (dist <= _CURSOR_OUTLINE / 2.0).astype(np.uint8) * 255
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[m > 127] = (0, 0, 0)
    img = Image.fromarray(np.dstack([rgb, halo]), "RGBA")
    _CURSOR_MASTER = (img, tip[0], tip[1])
    return _CURSOR_MASTER


def _draw_cursor_hd(frame_bgr, rel_x, rel_y, scale):
    # Overlay sprite cursor HD ke frame BGR dengan alpha blending.
    # frame_bgr: np.uint8 HxWx3. rel_x/rel_y: posisi mouse relatif capture.
    try:
        master, tip_x, tip_y = _get_cursor_master()
        tw = max(8, int(round(master.width * scale / _CURSOR_SS)))
        th = max(8, int(round(master.height * scale / _CURSOR_SS)))
        sprite = master.resize((tw, th), Image.LANCZOS)
        arr = np.array(sprite)  # RGBA
        rgb = arr[:, :, :3][:, :, ::-1]  # RGB -> BGR
        alpha = arr[:, :, 3:4].astype(np.float32) / 255.0
        if float(alpha.max()) <= 0:
            return
        tx = int(round(rel_x - tip_x * scale / _CURSOR_SS))
        ty = int(round(rel_y - tip_y * scale / _CURSOR_SS))
        fh, fw = frame_bgr.shape[:2]
        x0, y0 = max(0, tx), max(0, ty)
        x1, y1 = min(fw, tx + tw), min(fh, ty + th)
        if x1 <= x0 or y1 <= y0:
            return
        sx0, sy0 = x0 - tx, y0 - ty
        roi = frame_bgr[y0:y1, x0:x1].astype(np.float32)
        sp = rgb[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)].astype(np.float32)
        al = alpha[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
        frame_bgr[y0:y1, x0:x1] = (sp * al + roi * (1.0 - al)).astype(np.uint8)
    except Exception:
        pass

# =========================================================================
# ======================== SETTINGS & CONSTANTS ===========================
# =========================================================================

# Mengatur seberapa halus (smooth) kotak mengikuti mouse.
# Semakin kecil angkanya (misal 0.02), semakin lambat dan cinematic.
# Semakin besar (misal 0.20), semakin cepat dan kaku mengikuti mouse.
FOLLOW_SMOOTH_SPEED = 0.08

# Mengatur seberapa halus transisi visual saat kamu zoom in / zoom out.
ZOOM_SMOOTH_SPEED = 0.58

# Mengatur batasan maksimal Zoom In (Mentok). Nilai semakin kecil = semakin nge-zoom.
MIN_ZOOM_WIDTH = 450.0

# Kecepatan zooming ketika tombol di-hold (ditahan).
ZOOM_CONTINUOUS_SPEED = 12.0

# Kecepatan refresh pergerakan kotak (10ms = 100 FPS refresh rate agar sangat mulus)
UI_REFRESH_RATE_MS = 10

# Durasi animasi ALT+H (zoom-out ke max) dalam detik. Memakai easing
# ease-out agar awal cepat lalu mendarat dengan halus.
ZOOM_MAX_ANIM_DURATION = 0.6

# =========================================================================

class Recorder:
    def __init__(self):
        self.recording = False
        self.thread = None

        self.capture_rect = {
            "x": 0,
            "y": 0,
            "w": 1280,
            "h": 720
        }

        self.output_size = (1920, 1080)
        self.fps = 30
        self._is_stopped_event = threading.Event()

    def start(self, output_w, output_h):
        if self.recording:
            return

        self.output_size = (output_w, output_h)
        self.recording = True
        self._is_stopped_event.clear()

        self.thread = threading.Thread(target=self.record_loop)
        self.thread.start()

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        self._is_stopped_event.wait(timeout=5.0)

    def record_loop(self):
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(filename, fourcc, self.fps, self.output_size)

        frame_queue = queue.Queue()

        def encoding_thread():
            while True:
                item = frame_queue.get()
                if item is None:
                    break

                img, mouse_pos, monitor = item
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                mx, my = mouse_pos
                rel_x = mx - monitor["left"]
                rel_y = my - monitor["top"]

                if 0 <= rel_x <= monitor["width"] and 0 <= rel_y <= monitor["height"]:
                    # Kursor HD ala IDE: bentuk seperti referensi (rounded +
                    # lekukan concave), isi hitam solid, outline putih.
                    # Hotspot = ujung panah = posisi mouse.
                    # Skala mengikuti tinggi area capture agar proporsional.
                    _scale = max(1.0, monitor["height"] / 1080.0)
                    _draw_cursor_hd(frame, rel_x, rel_y, _scale)

                frame = cv2.resize(frame, self.output_size, interpolation=cv2.INTER_LINEAR)
                writer.write(frame)
                frame_queue.task_done()

        enc_t = threading.Thread(target=encoding_thread)
        enc_t.start()

        with mss.MSS() as sct:
            start_time = time.time()
            frame_count = 0

            while self.recording:
                rect = self.capture_rect.copy()

                monitor = {
                    "left": int(rect["x"]),
                    "top": int(rect["y"]),
                    "width": max(10, int(rect["w"])),
                    "height": max(10, int(rect["h"]))
                }

                try:
                    img = np.array(sct.grab(monitor))
                    current_mouse = pyautogui.position()
                    frame_queue.put((img, current_mouse, monitor))
                except Exception as e:
                    pass

                frame_count += 1
                target_next_time = start_time + (frame_count * (1.0 / self.fps))
                sleep_time = target_next_time - time.time()

                if sleep_time > 0:
                    time.sleep(sleep_time)

        frame_queue.put(None)
        enc_t.join()

        writer.release()
        print("Saved:", filename)
        self._is_stopped_event.set()

class SignalEmitter(QObject):
    start_record = pyqtSignal()
    stop_record = pyqtSignal()
    toggle_follow = pyqtSignal()
    change_aspect = pyqtSignal(float)
    set_zooming_in = pyqtSignal(bool)
    set_zooming_out = pyqtSignal(bool)
    change_fps = pyqtSignal(int)
    zoom_max = pyqtSignal()
    exit_app = pyqtSignal()

class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.recorder = Recorder()
        self.signals = SignalEmitter()
        self.signals.start_record.connect(self.on_start_record)
        self.signals.stop_record.connect(self.on_stop_record)
        self.signals.toggle_follow.connect(self.on_toggle_follow)
        self.signals.change_aspect.connect(self.on_change_aspect)
        self.signals.set_zooming_in.connect(self.on_set_zooming_in)
        self.signals.set_zooming_out.connect(self.on_set_zooming_out)
        self.signals.change_fps.connect(self.on_change_fps)
        self.signals.zoom_max.connect(self.on_zoom_max)
        self.signals.exit_app.connect(self.on_exit_app)

        # Ambil resolusi FISIK (physical pixels) langsung dari pyautogui,
        # bukan dari Qt geometry yang terpengaruh DPI scale (150% = dibagi 1.5).
        # pyautogui.position() juga pakai physical pixels, jadi harus konsisten.
        import pyautogui as _pag
        self.screen_w, self.screen_h = _pag.size()
        self.screen_w = float(self.screen_w)
        self.screen_h = float(self.screen_h)

        # DPI scale factor — dipakai untuk konversi koordinat Qt <-> physical
        # Qt overlay window pakai logical pixels, tapi semua kalkulasi box
        # dan posisi mouse pakai physical pixels.
        _qt_screen = QApplication.primaryScreen()
        self.dpi_scale = _qt_screen.devicePixelRatio()  # misal 1.5 untuk 150%

        # Deteksi aspect ratio OTOMATIS dari resolusi layar user
        # Tidak lagi hardcode 16:9 — menyesuaikan layar 4:3, 16:10, 21:9, dll.
        self.aspect_ratio = self.screen_w / self.screen_h

        # Box awal = seluruh layar
        self.target_box_w = float(self.screen_w)
        self.target_box_h = float(self.screen_h)

        self.box_w = self.target_box_w
        self.box_h = self.target_box_h

        self.box_x = 0.0
        self.box_y = 0.0

        self.follow_mouse = False

        # smooth_cx/cy = posisi CENTER yang diinterpolasi HALUS saat follow mouse.
        # Center di-lerp langsung ke posisi mouse, lalu pojok box diturunkan
        # sebagai (center - size/2). Ini membuat arah zoom selalu lurus ke
        # mouse — tidak ada gerak semu ke atas/kanan dulu seperti saat
        # menginterpolasi pojok kiri-atas dengan size yang berubah cepat.
        mx0, my0 = pyautogui.position()
        self.smooth_cx = float(mx0)
        self.smooth_cy = float(my0)

        # Titik tengah yang dikunci saat follow mouse OFF.
        self.static_center_x = self.screen_w / 2.0
        self.static_center_y = self.screen_h / 2.0

        self.alt_pressed = False
        self.is_zooming_in = False
        self.is_zooming_out = False

        # State animasi ALT+H: dict {t0, dur, start_w, target_w} atau None.
        # Selama animasi berjalan, target_box digerakkan bertahap dengan
        # easing agar zoom-out ke max terlihat mulus, bukan lompat.
        self._zoom_max_anim = None

        self.setup_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(UI_REFRESH_RATE_MS)

        self.kb_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.kb_listener.start()

    def setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Overlay geometry harus dalam logical pixels (physical / dpi_scale)
        log_w = int(self.screen_w / self.dpi_scale)
        log_h = int(self.screen_h / self.dpi_scale)
        self.setGeometry(0, 0, log_w, log_h)
        self.show()

        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
        except Exception:
            pass

    def on_key_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.alt_pressed = True

        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()
                # Tangkap event press untuk fitur hold to zoom
                if char == '`':
                    self.signals.set_zooming_in.emit(True)
                elif char == '1' and self.alt_pressed:
                    self.signals.set_zooming_out.emit(True)
        except Exception:
            pass

    def on_key_release(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = False
                # Hentikan zoom out jika ALT dilepas
                self.signals.set_zooming_out.emit(False)

            if hasattr(key, 'char') and key.char:
                char = key.char.lower()

                # Tangkap event release untuk fitur hold to zoom
                if char == '`':
                    self.signals.set_zooming_in.emit(False)
                elif char == '1':
                    self.signals.set_zooming_out.emit(False)

                # Fitur lain menggunakan on_release agar rapi
                elif char == 'v' and self.alt_pressed:
                    self.signals.start_record.emit()
                elif char == 'b' and self.alt_pressed:
                    self.signals.stop_record.emit()
                elif char == '2' and self.alt_pressed:
                    self.signals.change_aspect.emit(16/9.0)
                elif char == '3' and self.alt_pressed:
                    self.signals.change_aspect.emit(9/16.0)
                elif char == '4' and self.alt_pressed:
                    self.signals.change_aspect.emit(1.0)
                elif char == 'f' and self.alt_pressed:
                    self.signals.toggle_follow.emit()
                elif char == 'h' and self.alt_pressed:
                    self.signals.zoom_max.emit()
                elif char == '[':
                    self.signals.change_fps.emit(-5)
                elif char == ']':
                    self.signals.change_fps.emit(5)

            elif key == keyboard.Key.esc:
                self.signals.exit_app.emit()
        except Exception:
            pass

    def on_set_zooming_in(self, active):
        self.is_zooming_in = active

    def on_set_zooming_out(self, active):
        self.is_zooming_out = active

    def _clamp_zoom(self):
        max_w = float(self.screen_w)

        if self.target_box_w / self.aspect_ratio > self.screen_h:
            self.target_box_w = self.screen_h * self.aspect_ratio

        self.target_box_w = max(MIN_ZOOM_WIDTH, min(self.target_box_w, max_w))
        self.target_box_h = self.target_box_w / self.aspect_ratio

    def on_change_aspect(self, ratio):
        if self.recorder.recording:
            return

        self.aspect_ratio = ratio
        self.target_box_h = self.target_box_w / self.aspect_ratio

        if self.target_box_h > self.screen_h:
            self.target_box_h = float(self.screen_h)
            self.target_box_w = self.target_box_h * self.aspect_ratio

    def on_change_fps(self, delta):
        if self.recorder.recording:
            return

        new_fps = self.recorder.fps + delta
        new_fps = max(5, min(new_fps, 60))
        self.recorder.fps = new_fps

    def on_start_record(self):
        if self.recorder.recording:
            return

        # Output size dihitung proporsional dari aspect ratio aktual layar.
        # Target lebar output = 1920px (atau lebih kecil jika layar lebih kecil),
        # tinggi menyesuaikan aspect ratio.
        out_w = min(1920, self.screen_w)
        out_h = round(out_w / self.aspect_ratio)
        # Pastikan keduanya genap (syarat MP4 encoder)
        out_w = out_w if out_w % 2 == 0 else out_w - 1
        out_h = out_h if out_h % 2 == 0 else out_h - 1

        self.recorder.start(out_w, out_h)

    def on_stop_record(self):
        if self.recorder.recording:
            self.recorder.stop()

    def _set_follow(self, on: bool, snap: bool = True):
        self.follow_mouse = on

        if on:
            if snap:
                # Mode instan: center langsung = posisi mouse.
                mx, my = pyautogui.position()
                self.smooth_cx = float(mx)
                self.smooth_cy = float(my)
            else:
                # Mode smooth (ALT+H zoom-in / ALT+F): mulai dari center box
                # saat ini, biarkan update_loop glide halus ke mouse dengan
                # FOLLOW_SMOOTH_SPEED. Saat box masih full, range pan sempit
                # sehingga terlihat "tetap full dulu" lalu geser + mengecil.
                # Untuk ALT+F tidak ada perubahan zoom, jadi murni slide.
                self.smooth_cx = self.box_x + self.box_w / 2
                self.smooth_cy = self.box_y + self.box_h / 2
        else:
            # Kunci center ke posisi box saat ini sebelum follow dimatikan,
            # agar box diam di posisi terakhir saat follow.
            self.static_center_x = self.box_x + self.box_w / 2
            self.static_center_y = self.box_y + self.box_h / 2

    def on_toggle_follow(self):
        # ALT+F: ON selalu slide halus dari posisi saat ini (tanpa zoom),
        # OFF kunci di posisi terakhir.
        self._set_follow(not self.follow_mouse, snap=False)

    def on_zoom_max(self):
        # Toggle zoom-out max <-> zoom-in max, DIANIMASI dengan easing agar
        # mulus (durasi & feel sama untuk kedua arah). Sengaja boleh saat
        # recording (sekelas hold-zoom).
        # - Belum di max -> zoom-out ke max sesuai aspect ratio, follow
        #   dipaksa OFF, posisi diam di titik terakhir follow.
        # - Sudah di max -> zoom-in ke MIN_ZOOM_WIDTH (sama dengan mentok
        #   tahan `), follow dipaksa ON menuju mouse.
        max_w = min(float(self.screen_w), float(self.screen_h) * self.aspect_ratio)
        if self._zoom_max_anim is not None:
            effective_w = float(self._zoom_max_anim["target_w"])
        else:
            effective_w = float(self.target_box_w)
        if effective_w >= max_w - 1.0:
            target_w = MIN_ZOOM_WIDTH
        else:
            target_w = max_w
        # Selalu paksa: zoom-in -> follow ON smooth (glide dari posisi
        # saat ini ke mouse), zoom-out -> follow OFF (diam di posisi
        # terakhir follow).
        is_zoom_in = target_w <= MIN_ZOOM_WIDTH + 1e-6
        if is_zoom_in:
            self._set_follow(True, snap=False)
        else:
            self._set_follow(False)
        self._zoom_max_anim = {
            "t0": time.time(),
            "dur": ZOOM_MAX_ANIM_DURATION,
            "start_w": float(self.target_box_w),
            "target_w": float(target_w),
        }

    def _clamp_zoom_target(self, w):
        self.target_box_w = w
        self._clamp_zoom()

    def on_exit_app(self):
        if self.recorder.recording:
            self.recorder.stop()
        QApplication.quit()

    def update_loop(self):
        # Animasi ALT+H: gerakkan target_box bertahap dengan ease-out cubic.
        # Zoom manual (hold) membatalkan animasi agar user selalu menang.
        if self._zoom_max_anim is not None:
            if self.is_zooming_in or self.is_zooming_out:
                self._zoom_max_anim = None
            else:
                anim = self._zoom_max_anim
                p = (time.time() - anim["t0"]) / anim["dur"]
                if p >= 1.0:
                    self._clamp_zoom_target(anim["target_w"])
                    self._zoom_max_anim = None
                else:
                    eased = 1.0 - (1.0 - p) ** 3  # easeOutCubic
                    w = anim["start_w"] + (anim["target_w"] - anim["start_w"]) * eased
                    self._clamp_zoom_target(w)

        # Eksekusi hold to zoom secara terus menerus selama tombol ditahan
        if self.is_zooming_in:
            self.target_box_w -= ZOOM_CONTINUOUS_SPEED
            self._clamp_zoom()
        elif self.is_zooming_out:
            self.target_box_w += ZOOM_CONTINUOUS_SPEED
            self._clamp_zoom()

        # Smooth interpolasi UKURAN box (simpan ukuran lama untuk kompensasi
        # zoom-to-cursor di bawah).
        old_w = self.box_w
        old_h = self.box_h
        self.box_w += (self.target_box_w - self.box_w) * ZOOM_SMOOTH_SPEED
        self.box_h += (self.target_box_h - self.box_h) * ZOOM_SMOOTH_SPEED

        if self.follow_mouse:
            mx, my = pyautogui.position()

            # Kompensasi zoom-to-cursor: titik di bawah kursor harus tetap
            # diam selama ukuran berubah. Tanpa ini, sisi box yang sudah
            # mentok border (misal kiri+atas saat mouse di pojok) sempat
            # lepas lalu balik lagi, karena center (lerp lambat) tertinggal
            # dari size (lerp cepat). Dengan penskalaan ini, box_x/y di tepi
            # tetap 0 sepanjang animasi zoom.
            if old_w > 0:
                self.smooth_cx = mx + (self.smooth_cx - mx) * (self.box_w / old_w)
            if old_h > 0:
                self.smooth_cy = my + (self.smooth_cy - my) * (self.box_h / old_h)

            # Drift HALUS mengikuti gerakan mouse (tetap cinematic).
            # Saat mouse diam nilainya ~0 sehingga tidak merusak pinning di atas.
            half_w = self.box_w / 2
            half_h = self.box_h / 2
            desired_cx = max(half_w, min(float(mx), self.screen_w - half_w))
            desired_cy = max(half_h, min(float(my), self.screen_h - half_h))

            self.smooth_cx += (desired_cx - self.smooth_cx) * FOLLOW_SMOOTH_SPEED
            self.smooth_cy += (desired_cy - self.smooth_cy) * FOLLOW_SMOOTH_SPEED

            self.box_x = self.smooth_cx - half_w
            self.box_y = self.smooth_cy - half_h
        else:
            # Mode statis: zoom di sekitar static_center yang dikunci,
            # tidak bergerak ke mana-mana.
            self.box_x = self.static_center_x - self.box_w / 2
            self.box_y = self.static_center_y - self.box_h / 2

        # Clamp agar tidak keluar layar
        self.box_x = max(0, min(self.box_x, self.screen_w - self.box_w))
        self.box_y = max(0, min(self.box_y, self.screen_h - self.box_h))

        self.recorder.capture_rect = {
            "x": int(self.box_x),
            "y": int(self.box_y),
            "w": int(self.box_w),
            "h": int(self.box_h)
        }

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gap_size = 15
        s = self.dpi_scale  # physical -> logical conversion factor

        # Semua koordinat box adalah physical pixels, konversi ke logical untuk Qt
        lx = int(self.box_x / s)
        ly = int(self.box_y / s)
        lw = int(self.box_w / s)
        lh = int(self.box_h / s)

        outer_rect = QRect(
            lx - gap_size,
            ly - gap_size,
            lw + gap_size * 2,
            lh + gap_size * 2
        )

        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(outer_rect, QColor(0, 0, 0, 0))

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        if not self.recorder.recording:
            painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            follow = "ON" if self.follow_mouse else "OFF"

            # Tampilkan aspect ratio aktual dalam format A:B
            from math import gcd
            _aw = int(round(self.aspect_ratio * 100))
            _ah = 100
            _g = gcd(_aw, _ah)
            asp_str = f"{_aw // _g}:{_ah // _g}"

            texts = [
                "IDLE (Ready to Record)",
                f"Start Record: [ ALT + V ]",
                f"Stop Record:  [ ALT + B ]",
                f"Follow Mouse: {follow} [ ALT + F ]",
                f"Aspect: {asp_str} [ ALT + 2, 3, 4 ]",
                f"FPS: {self.recorder.fps} [ '[' or ']' ]",
                f"Zoom In: Hold [ ` ]",
                f"Zoom Out: Hold [ ALT + 1 ]",
                f"Zoom Max Toggle: [ ALT + H ]",
                f"Exit: [ ESC ]"
            ]

            painter.setPen(QColor(0, 0, 0))
            for i, text in enumerate(texts):
                painter.drawText(22, 42 + (i*32), text)

            painter.setPen(QColor(255, 255, 255))
            for i in range(len(texts)):
                painter.drawText(20, 40 + (i*32), texts[i])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()
    sys.exit(app.exec())