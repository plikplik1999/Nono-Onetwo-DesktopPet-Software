import base64
import ctypes
import json
import os
import random
import sys
import tempfile
import time
import tkinter as tk
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageSequence, ImageTk

from assets_data import AUDIO, SKINS


PET_SIZE = (100, 100)
TRANSPARENT_COLOR = "#010203"

DEFAULT_CONFIG = {
    "switch_interval_seconds": 4.0,
    "sedentary_enabled": True,
    "sedentary_interval_minutes": 45,
    "water_enabled": True,
    "water_interval_minutes": 30,
    "idle_reset_minutes": 10,
    "bubble_duration_seconds": 6,
    "button_timeout_seconds": 10,
    "character": "onetwo",
    "messages_sedentary": [
        "主人，起来伸个懒腰吧～",
        "坐了这么久，站起来转转嘛~",
        "小腰要抗议啦，起来动一动！",
        "让眼睛休息一下，看看远处吧~",
        "起身走两步，顺带扭扭脖子？",
    ],
    "messages_water": [
        "该喝水啦主人~",
        "小水滴提醒：补充水分！",
        "来杯温水暖暖胃吧~",
        "水水喝起来，皮肤好好~",
        "主人记得喝水哦~",
    ],
    "long_work_enabled": True,
    "long_work_minutes": 120,
    "long_work_messages": [
        "你已经忙了一阵子啦，要不要陪我站起来活动一下？",
        "我的小腿都想伸伸啦，你也休息一会儿吧。",
        "我们暂停一下下，好不好？五分钟就够啦。",
        "我发现你一直在努力，我想提醒你照顾一下自己。",
        "工作很重要，但是你也很重要呀。",
        "我陪你休息一会儿，回来再继续。",
    ],
    "away_enabled": True,
    "away_interval_minutes": 15,
    "messages_away": [
        "你刚才去哪啦？我在这里等你回来。",
        "是不是休息去了？回来记得喝口水哦。",
        "桌面有点安静，我陪你等一会儿。",
    ],
    "companion_enabled": True,
    "companion_interval_minutes": 60,
    "companion_probability": 0.7,
    "companion_messages": [
        "你工作的时候，我也在认真陪伴。",
        "不用着急，我会一直陪你慢慢完成。",
        "让我陪你放松几分钟，然后再继续出发吧。",
        "肩膀是不是有点累啦？偷偷提醒你放松一下。",
        "今天已经完成很多事情了，不要忘记照顾自己。",
        "你的努力我都看到了，现在也该关心一下自己啦。",
    ],
    "window_switch_enabled": True,
    "window_switch_threshold": 8,
    "window_switch_window_minutes": 5,
    "window_switch_cooldown_minutes": 30,
    "switch_question": "我猜主人现在状态有点累，对吗？",
    "switch_answer_yes": "慢一点也没关系，我陪主人整理一下思绪",
    "switch_answer_no": "那主人继续加油，我陪着你就好～",
    "switch_question_timeout_seconds": 15,
}


def config_path() -> Path:
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    return base / "config.json"


def load_config() -> dict:
    path = config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            merged = {**DEFAULT_CONFIG, **data}
            for key in ("messages_sedentary", "messages_water", "long_work_messages", "messages_away", "companion_messages"):
                if not isinstance(merged.get(key), list) or not merged[key]:
                    merged[key] = list(DEFAULT_CONFIG[key])
            return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    config_path().write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_seconds() -> float:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    user32.GetLastInputInfo(ctypes.byref(info))
    return (kernel32.GetTickCount() - info.dwTime) / 1000.0


def get_mouse_pos() -> tuple[int, int]:
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", _RECT),
        ("rcWork", _RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


_MONITOR_DEFAULTTONEAREST = 2


_MUTEX_HANDLE = None
_MUTEX_NAME = "Local\\DesktopPetSingleton"
_ERROR_ALREADY_EXISTS = 183


def ensure_single_instance() -> bool:
    global _MUTEX_HANDLE
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return kernel32.GetLastError() != _ERROR_ALREADY_EXISTS


def get_work_area_at(x: int, y: int) -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    hmonitor = user32.MonitorFromPoint(_POINT(int(x), int(y)), _MONITOR_DEFAULTTONEAREST)
    info = _MONITORINFO()
    info.cbSize = ctypes.sizeof(_MONITORINFO)
    user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
    rect = info.rcWork
    return rect.left, rect.top, rect.right, rect.bottom


def clamp_to_work_area(x: int, y: int) -> tuple[int, int]:
    left, top, right, bottom = get_work_area_at(x + PET_SIZE[0] // 2, y + PET_SIZE[1] // 2)
    max_x = right - PET_SIZE[0]
    max_y = bottom - PET_SIZE[1]
    if max_x < left:
        max_x = left
    if max_y < top:
        max_y = top
    return max(left, min(x, max_x)), max(top, min(y, max_y))


@dataclass
class GifAnimation:
    frames: list[ImageTk.PhotoImage]
    durations: list[int]


class AudioPlayer:
    def __init__(self) -> None:
        self.mci = ctypes.WinDLL("winmm")
        self.mci.mciSendStringW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
            ctypes.c_void_p,
        ]
        self.alias = "desktop_pet_audio"
        self.playing = False
        self._temp_path: str | None = None

    def play(self, data: bytes, ext: str) -> None:
        self.stop()
        ext = ext if ext.startswith(".") else "." + ext
        fd, path = tempfile.mkstemp(prefix="dpet_", suffix=ext)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        self._temp_path = path
        mtype = "waveaudio" if ext.lower() == ".wav" else "mpegvideo"
        self.mci.mciSendStringW(
            f'open "{path}" type {mtype} alias {self.alias}', None, 0, None
        )
        self.mci.mciSendStringW(f"play {self.alias}", None, 0, None)
        self.playing = True

    def stop(self) -> None:
        if self.playing:
            self.mci.mciSendStringW(f"stop {self.alias}", None, 0, None)
            self.playing = False
        self.mci.mciSendStringW(f"close {self.alias}", None, 0, None)
        if self._temp_path is not None:
            try:
                os.remove(self._temp_path)
            except OSError:
                pass
            self._temp_path = None


class ReminderBubble:
    def __init__(
        self,
        root: tk.Tk,
        pet: tk.Tk,
        text: str,
        duration_seconds: float,
        on_dismiss,
        buttons: list[tuple[str, callable]] | None = None,
    ) -> None:
        self.root = root
        self.on_dismiss = on_dismiss
        self.job: str | None = None
        self._dismissed = False

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg=TRANSPARENT_COLOR)
        self.top.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.top.bind("<Button-1>", self.dismiss)

        bubble = tk.Frame(self.top, bg="#FFF8E7", bd=0, highlightthickness=0)
        bubble.pack()

        self.label = tk.Label(
            bubble,
            text=text,
            bg="#FFF8E7",
            fg="#4A3B32",
            font=("Microsoft YaHei UI", 10),
            wraplength=150,
            justify="left",
            padx=12,
            pady=8,
            bd=0,
            highlightthickness=0,
        )
        self.label.pack(fill=tk.BOTH)
        self.label.bind("<Button-1>", self.dismiss)

        if buttons:
            bar = tk.Frame(bubble, bg="#FFF8E7")
            bar.pack(pady=(0, 8))
            for label_text, callback in buttons:
                btn = tk.Button(
                    bar,
                    text=label_text,
                    command=lambda cb=callback: self._button_press(cb),
                    bg="#FFE4B3",
                    fg="#4A3B32",
                    activebackground="#FFD98A",
                    relief=tk.FLAT,
                    bd=0,
                    padx=14,
                    pady=3,
                    cursor="hand2",
                    font=("Microsoft YaHei UI", 10),
                )
                btn.pack(side=tk.LEFT, padx=6)

        self.top.update_idletasks()
        self.reposition_at(pet.winfo_x(), pet.winfo_y())
        self.job = root.after(int(duration_seconds * 1000), self.dismiss)

    def _button_press(self, callback) -> None:
        self.dismiss()
        callback()

    def reposition_at(self, pet_x: int, pet_y: int) -> None:
        if not self.top.winfo_exists():
            return
        width = self.top.winfo_reqwidth()
        height = self.top.winfo_reqheight()

        x = pet_x + PET_SIZE[0] // 2 - width // 2
        y = pet_y - height - 6

        left, top_edge, right, bottom = get_work_area_at(pet_x, pet_y)
        if y < top_edge:
            y = pet_y + PET_SIZE[1] + 6
        x = max(left, min(x, right - width))
        y = max(top_edge, min(y, bottom - height))

        self.top.geometry(f"{width}x{height}+{x}+{y}")

    def dismiss(self, _event: tk.Event | None = None) -> None:
        if _event is not None and isinstance(_event.widget, tk.Button):
            return
        if self._dismissed:
            return
        self._dismissed = True
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        if self.top.winfo_exists():
            self.top.destroy()
        self.on_dismiss()


class DesktopPet:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_COLOR)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        self.label = tk.Label(
            self.root,
            bd=0,
            highlightthickness=0,
            bg=TRANSPARENT_COLOR,
        )
        self.label.pack()

        self.cfg = load_config()
        character = self.cfg.get("character", "onetwo")
        if character not in ("nono", "onetwo", "both"):
            character = "onetwo"
        self.character = character

        self.animations = self.load_animations(self.character)
        self.current_index: int | None = None
        self.frame_index = 0
        self.playlist: list[int] = []
        self.play_index = 0
        self.switch_job: str | None = None
        self.frame_job: str | None = None

        self.audio_player = AudioPlayer()
        self.audio = {}
        for char, files in AUDIO.items():
            self.audio[char] = [
                (name, base64.b64decode(b64)) for name, b64 in sorted(files.items())
            ]
        self.audio_play_count = 0

        self.bubble: ReminderBubble | None = None
        self.reminder_queue: list[tuple[str, float | None]] = []
        self.settings_window: tk.Toplevel | None = None
        self.tick_job: str | None = None
        self.next_water_time = time.monotonic() + self.cfg["water_interval_minutes"] * 60
        self.next_companion_time = time.monotonic() + self.cfg["companion_interval_minutes"] * 60
        self.sedentary_start = time.monotonic()
        self.last_switch_question_time = 0.0
        self._last_window_hwnd: int | None = None
        self._switch_times: list[float] = []
        self._away_triggered = False
        self._last_mouse_pos = get_mouse_pos()
        self._last_mouse_move_time = time.monotonic()

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.drag)
        self.label.bind("<Button-3>", self.show_context_menu)

        self.root.geometry(f"{PET_SIZE[0]}x{PET_SIZE[1]}+100+100")
        self.switch_animation()
        self.reminder_tick()

    def load_animations(self, character: str) -> list[GifAnimation]:
        animations: list[GifAnimation] = []
        for name in sorted(SKINS[character]):
            image = Image.open(BytesIO(base64.b64decode(SKINS[character][name])))
            frames: list[ImageTk.PhotoImage] = []
            durations: list[int] = []

            for frame in ImageSequence.Iterator(image):
                rendered = self._fit_frame(frame)
                frames.append(ImageTk.PhotoImage(rendered))
                durations.append(max(20, int(frame.info.get("duration", 100))))

            animations.append(GifAnimation(frames=frames, durations=durations))

        return animations

    @staticmethod
    def _fit_frame(frame) -> Image.Image:
        img = frame.convert("RGBA")
        img.thumbnail(PET_SIZE, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", PET_SIZE, (0, 0, 0, 0))
        x = (PET_SIZE[0] - img.width) // 2
        y = (PET_SIZE[1] - img.height) // 2
        canvas.paste(img, (x, y), img)
        return canvas

    def _audio_pool(self) -> list[tuple[str, bytes]]:
        chars = ("nono", "onetwo") if self.character == "both" else (self.character,)
        pool: list[tuple[str, bytes]] = []
        for c in chars:
            for name, data in self.audio.get(c, []):
                if "换布布" not in name and "换一二" not in name:
                    pool.append((name, data))
        return pool

    def pet_action(self) -> None:
        pool = self._audio_pool()
        if not pool:
            return
        last = getattr(self, "_last_audio_name", None)
        name, data = random.choice(pool)
        if len(pool) > 1 and name == last:
            name, data = random.choice(pool)
        self._last_audio_name = name
        self.audio_play_count += 1
        self.audio_player.play(data, Path(name).suffix)

    def _health_buttons(self) -> list[tuple[str, callable]]:
        return [("谢谢", self.pet_action), ("摸摸", self.pet_action)]

    def switch_character(self, character: str) -> None:
        if character == self.character or character not in ("nono", "onetwo", "both"):
            return
        self.character = character
        self.cfg["character"] = character
        save_config(self.cfg)
        self._reload_character_skin()

        if character == "nono":
            self._play_switch_sound("换布布")
        elif character == "onetwo":
            self._play_switch_sound("换一二")
        elif character == "both":
            self._play_switch_sound("切换音效")

    def _reload_character_skin(self) -> None:
        if self.frame_job is not None:
            self.root.after_cancel(self.frame_job)
            self.frame_job = None
        if self.switch_job is not None:
            self.root.after_cancel(self.switch_job)
            self.switch_job = None
        self.animations = self.load_animations(self.character)
        self.current_index = None
        self.playlist = []
        self.play_index = 0
        self.frame_index = 0
        self.switch_animation()

    def _play_switch_sound(self, keyword: str) -> None:
        for name, data in self.audio.get(self.character, []):
            if keyword in name:
                self.audio_player.play(data, Path(name).suffix)
                return

    def _play_click_sound(self) -> None:
        for name, data in self.audio.get(self.character, []):
            if "点击音效" in name:
                self.audio_player.play(data, Path(name).suffix)
                return

    def reminder_tick(self) -> None:
        now = time.monotonic()
        cfg = self.cfg
        idle_seconds = get_idle_seconds()

        if idle_seconds >= cfg["idle_reset_minutes"] * 60:
            self.sedentary_start = now
            self._switch_times = []

        pos = get_mouse_pos()
        if pos != self._last_mouse_pos:
            self._last_mouse_pos = pos
            self._last_mouse_move_time = now
        mouse_idle_seconds = now - self._last_mouse_move_time

        if cfg["away_enabled"] and mouse_idle_seconds >= cfg["away_interval_minutes"] * 60:
            self._away_triggered = True
        elif cfg["away_enabled"] and self._away_triggered:
            self._away_triggered = False
            self.show_reminder(
                random.choice(cfg["messages_away"]),
                buttons=self._health_buttons(),
            )

        active_elapsed = now - self.sedentary_start

        if (cfg["sedentary_enabled"]
                and active_elapsed >= cfg["sedentary_interval_minutes"] * 60):
            self.show_reminder(
                random.choice(cfg["messages_sedentary"]),
                buttons=self._health_buttons(),
            )
            self.sedentary_start = now

        if cfg["water_enabled"] and now >= self.next_water_time:
            self.show_reminder(
                random.choice(cfg["messages_water"]),
                buttons=self._health_buttons(),
            )
            self.next_water_time = now + cfg["water_interval_minutes"] * 60

        if (cfg["long_work_enabled"]
                and active_elapsed >= cfg["long_work_minutes"] * 60):
            self.show_reminder(
                random.choice(cfg["long_work_messages"]),
                buttons=self._health_buttons(),
            )
            self.sedentary_start = now

        if cfg["companion_enabled"] and now >= self.next_companion_time:
            self.next_companion_time = now + cfg["companion_interval_minutes"] * 60
            if random.random() < cfg["companion_probability"]:
                self.show_reminder(
                    random.choice(cfg["companion_messages"]),
                    buttons=self._health_buttons(),
                )

        self._update_window_switches(now)
        if (cfg["window_switch_enabled"]
                and self.switch_count >= cfg["window_switch_threshold"]
                and now - self.last_switch_question_time
                >= cfg["window_switch_cooldown_minutes"] * 60):
            self.show_switch_question()
            self._switch_times = []

        self.tick_job = self.root.after(1000, self.reminder_tick)

    def _update_window_switches(self, now: float) -> None:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if self._last_window_hwnd is not None and hwnd != self._last_window_hwnd:
            self._switch_times.append(now)
        self._last_window_hwnd = hwnd
        cutoff = now - self.cfg["window_switch_window_minutes"] * 60
        self._switch_times = [t for t in self._switch_times if t >= cutoff]

    @property
    def switch_count(self) -> int:
        return len(self._switch_times)

    def show_switch_question(self) -> None:
        self.last_switch_question_time = time.monotonic()
        if self.bubble is not None:
            return

        def answer(choice: bool) -> None:
            text = (
                self.cfg["switch_answer_yes"]
                if choice
                else self.cfg["switch_answer_no"]
            )
            self.show_reminder(text)

        self.bubble = ReminderBubble(
            self.root,
            self.root,
            self.cfg["switch_question"],
            self.cfg["switch_question_timeout_seconds"],
            self.on_bubble_dismiss,
            buttons=[("对", lambda: answer(True)), ("不对", lambda: answer(False))],
        )

    def show_reminder(self, text: str, duration: float | None = None,
                      buttons: list[tuple[str, callable]] | None = None) -> None:
        if self.bubble is not None:
            self.reminder_queue.append((text, duration, buttons))
            return
        self._create_bubble(text, duration, buttons)

    def _create_bubble(self, text: str, duration: float | None = None,
                       buttons: list[tuple[str, callable]] | None = None) -> None:
        if duration is None:
            if buttons:
                seconds = self.cfg["button_timeout_seconds"]
            else:
                seconds = self.cfg["bubble_duration_seconds"]
        else:
            seconds = duration
        self.bubble = ReminderBubble(
            self.root,
            self.root,
            text,
            seconds,
            self.on_bubble_dismiss,
            buttons=buttons,
        )

    def on_bubble_dismiss(self) -> None:
        self.bubble = None
        if self.reminder_queue:
            text, duration, buttons = self.reminder_queue.pop(0)
            self._create_bubble(text, duration, buttons)

    def open_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("设置")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(bg="#FFFFFF")
        win.grab_set()
        self.settings_window = win

        sed_var = tk.BooleanVar(value=self.cfg["sedentary_enabled"])
        water_var = tk.BooleanVar(value=self.cfg["water_enabled"])
        sed_interval = tk.DoubleVar(value=self.cfg["sedentary_interval_minutes"])
        water_interval = tk.DoubleVar(value=self.cfg["water_interval_minutes"])
        idle_reset = tk.DoubleVar(value=self.cfg["idle_reset_minutes"])
        switch_interval = tk.DoubleVar(value=self.cfg["switch_interval_seconds"])
        long_work_var = tk.BooleanVar(value=self.cfg["long_work_enabled"])
        long_work_interval = tk.DoubleVar(value=self.cfg["long_work_minutes"])
        window_switch_var = tk.BooleanVar(value=self.cfg["window_switch_enabled"])

        content = tk.Frame(win, bg="#FFFFFF")
        content.pack(padx=16, pady=12)

        tk.Label(content, text="动图切换时长（秒）", bg="#FFFFFF").grid(
            row=0, column=0, sticky="w"
        )
        tk.Spinbox(
            content,
            from_=1,
            to=120,
            increment=1,
            textvariable=switch_interval,
            width=8,
        ).grid(row=0, column=1, sticky="w")

        tk.Checkbutton(
            content, text="久坐提醒", variable=sed_var, bg="#FFFFFF", anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        tk.Label(content, text="久坐间隔（分钟）", bg="#FFFFFF").grid(
            row=2, column=0, sticky="w", pady=(4, 0)
        )
        tk.Spinbox(
            content,
            from_=1,
            to=600,
            increment=5,
            textvariable=sed_interval,
            width=8,
        ).grid(row=2, column=1, sticky="w", pady=(4, 0))

        tk.Checkbutton(
            content, text="喝水提醒", variable=water_var, bg="#FFFFFF", anchor="w"
        ).grid(row=3, column=0, sticky="w", pady=(10, 0))

        tk.Label(content, text="喝水间隔（分钟）", bg="#FFFFFF").grid(
            row=4, column=0, sticky="w", pady=(4, 0)
        )
        tk.Spinbox(
            content,
            from_=1,
            to=600,
            increment=5,
            textvariable=water_interval,
            width=8,
        ).grid(row=4, column=1, sticky="w", pady=(4, 0))

        tk.Label(content, text="闲置判定（分钟）", bg="#FFFFFF").grid(
            row=5, column=0, sticky="w", pady=(10, 0)
        )
        tk.Spinbox(
            content,
            from_=1,
            to=120,
            increment=1,
            textvariable=idle_reset,
            width=8,
        ).grid(row=5, column=1, sticky="w", pady=(10, 0))

        tk.Checkbutton(
            content, text="长时间工作提醒", variable=long_work_var, bg="#FFFFFF", anchor="w"
        ).grid(row=6, column=0, sticky="w", pady=(10, 0))

        tk.Label(content, text="长时间（分钟）", bg="#FFFFFF").grid(
            row=7, column=0, sticky="w", pady=(4, 0)
        )
        tk.Spinbox(
            content,
            from_=1,
            to=600,
            increment=5,
            textvariable=long_work_interval,
            width=8,
        ).grid(row=7, column=1, sticky="w", pady=(4, 0))

        tk.Checkbutton(
            content,
            text="窗口切换检测（疲劳询问）",
            variable=window_switch_var,
            bg="#FFFFFF",
            anchor="w",
        ).grid(row=8, column=0, sticky="w", pady=(10, 0))

        buttons = tk.Frame(win, bg="#FFFFFF")
        buttons.pack(pady=(4, 12))

        def do_save() -> None:
            self.cfg["sedentary_enabled"] = bool(sed_var.get())
            self.cfg["water_enabled"] = bool(water_var.get())
            self.cfg["sedentary_interval_minutes"] = float(sed_interval.get())
            self.cfg["water_interval_minutes"] = float(water_interval.get())
            self.cfg["idle_reset_minutes"] = float(idle_reset.get())
            self.cfg["switch_interval_seconds"] = float(switch_interval.get())
            self.cfg["long_work_enabled"] = bool(long_work_var.get())
            self.cfg["long_work_minutes"] = float(long_work_interval.get())
            self.cfg["window_switch_enabled"] = bool(window_switch_var.get())
            save_config(self.cfg)
            self.next_water_time = time.monotonic() + self.cfg["water_interval_minutes"] * 60
            if self.switch_job is not None:
                self.root.after_cancel(self.switch_job)
            self.switch_job = self.root.after(
                int(self.cfg["switch_interval_seconds"] * 1000), self.switch_animation
            )
            win.destroy()
            self.settings_window = None

        tk.Button(buttons, text="保存", width=8, command=do_save).grid(
            row=0, column=0, padx=6
        )
        tk.Button(
            buttons,
            text="取消",
            width=8,
            command=lambda: (win.destroy(), setattr(self, "settings_window", None)),
        ).grid(row=0, column=1, padx=6)

    def switch_animation(self) -> None:
        if self.play_index >= len(self.playlist):
            self.build_playlist()

        self.current_index = self.playlist[self.play_index]
        self.play_index += 1
        self.frame_index = 0

        if self.frame_job is not None:
            self.root.after_cancel(self.frame_job)
            self.frame_job = None

        self.play_frame()
        self.switch_job = self.root.after(
            int(self.cfg["switch_interval_seconds"] * 1000), self.switch_animation
        )

    def build_playlist(self) -> None:
        last = self.current_index
        choices = list(range(len(self.animations)))
        random.shuffle(choices)
        if last is not None and len(choices) > 1 and choices[0] == last:
            choices[0], choices[1] = choices[1], choices[0]
        self.playlist = choices
        self.play_index = 0

    def play_frame(self) -> None:
        if self.current_index is None:
            return

        animation = self.animations[self.current_index]
        frame = animation.frames[self.frame_index]
        self.label.configure(image=frame)

        delay = animation.durations[self.frame_index]
        self.frame_index = (self.frame_index + 1) % len(animation.frames)
        self.frame_job = self.root.after(delay, self.play_frame)

    def start_drag(self, event: tk.Event) -> None:
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        x, y = clamp_to_work_area(x, y)
        self.root.geometry(f"+{x}+{y}")
        if self.bubble is not None:
            self.bubble.reposition_at(x, y)

    def _switch_options(self) -> list[tuple[str, str]]:
        if self.character == "onetwo":
            return [("布来！", "nono"), ("一起玩", "both")]
        if self.character == "nono":
            return [("宝来！", "onetwo"), ("一起玩", "both")]
        return [("布来！", "nono"), ("宝来！", "onetwo")]

    def show_context_menu(self, event: tk.Event) -> None:
        self._play_click_sound()

        menu = tk.Menu(self.root, tearoff=0)

        for label, target in self._switch_options():
            menu.add_command(label=label, command=lambda t=target: self.switch_character(t))

        menu.add_separator()
        menu.add_command(label="摸摸", command=self.pet_action)
        menu.add_command(label="设置", command=self.open_settings)
        menu.add_command(label="退出", command=self.quit)

        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def quit(self) -> None:
        self.audio_player.stop()
        if self.bubble is not None:
            self.bubble.dismiss()
        for job in (self.frame_job, self.switch_job, self.tick_job):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    if not ensure_single_instance():
        ctypes.windll.user32.MessageBoxW(
            None, "桌面宠物已在运行中，请先关闭再启动。", "提示", 0x40
        )
        sys.exit(0)
    DesktopPet().run()
