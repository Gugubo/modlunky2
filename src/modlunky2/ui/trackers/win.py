import logging
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from datetime import datetime

from modlunky2.config import Config, WinTrackerConfig
from modlunky2.constants import BASE_DIR
from modlunky2.mem import Spel2Process

from modlunky2.mem.state import WinState

from modlunky2.ui.trackers.common import (
    Tracker,
    TrackerWindow,
    WindowData,
    TRACKERS_DIR,
)

logger = logging.getLogger(__name__)


ICON_PATH = BASE_DIR / "static/images"


class WinModifiers(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        win_tracker_config: WinTrackerConfig,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.win_tracker_config = win_tracker_config


class WinTrackerButtons(ttk.Frame):
    def __init__(self, parent, modlunky_config: Config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.modlunky_config = modlunky_config
        self.columnconfigure(0, weight=1, minsize=200)
        self.columnconfigure(1, weight=10000)
        self.rowconfigure(0, minsize=60)
        self.window = None

        self.win_icon = ImageTk.PhotoImage(
            Image.open(ICON_PATH / "trophy.png").resize(
                (24, 24), Image.Resampling.LANCZOS
            )
        )

        self.win_button = ttk.Button(
            self,
            text=r"Win Tracker",
            image=self.win_icon,
            compound="left",
            command=self.launch,
            width=1,
        )
        self.win_button.grid(row=0, column=0, pady=5, padx=5, sticky="nswe")

        self.modifiers = WinModifiers(
            self,
            self.modlunky_config.trackers.win_tracker,
            text=r"Win Tracker Options",
        )
        self.modifiers.grid(row=0, column=1, pady=5, padx=5, sticky="nswe")

    def launch(self):
        self.disable_button()
        self.window = TrackerWindow(
            title=r"Win Tracker",
            color_key=self.modlunky_config.tracker_color_key,
            font_size=self.modlunky_config.tracker_font_size,
            font_family=self.modlunky_config.tracker_font_family,
            on_close=self.window_closed,
            file_name="",
            tracker=WinTracker(),
            config=self.modlunky_config.trackers.win_tracker,
        )

    def config_update_callback(self):
        self.modlunky_config.save()
        if self.window:
            self.window.update_config(self.modlunky_config.trackers.win_tracker)

    def window_closed(self):
        self.window = None
        # If we're in the midst of destroy() the button might not exist
        if self.win_button.winfo_exists():
            self.win_button["state"] = tk.NORMAL

    def disable_button(self):
        self.win_button["state"] = tk.DISABLED


class WinTracker(Tracker[WinTrackerConfig, WindowData]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win = False
        self.label = "No win"

    def initialize(self):
        self.win = False
        self.label = "No win"

    def poll(self, proc: Spel2Process, config: WinTrackerConfig) -> WindowData:
        game_state = proc.get_state()
        if game_state is None:
            return None

        WINS = [WinState.TIAMAT, WinState.HUNDUN, WinState.COSMIC_OCEAN]
        WIN_NAMES = ["No", "Normal", "Hard", "Special"]
        WINS_FILENAME = "wins.txt"
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

        # New win
        if not self.win and game_state.win_state in WINS:
            self.win = True
            date_string = datetime.now().strftime(DATE_FORMAT)
            self.label = f"{date_string} [{WIN_NAMES[game_state.win_state]} win]"
            self.write_to_file(self.label + "\n", WINS_FILENAME)

        # Reset
        if self.win and game_state.win_state not in WINS:
            self.label = "No win"
            self.win = False

        return WindowData(self.label)

    # Appends text to the file
    def write_to_file(self, text, file_name):
        TRACKERS_DIR.mkdir(parents=True, exist_ok=True)
        if file_name:
            text_file = TRACKERS_DIR / file_name
            with text_file.open("a", encoding="utf-8") as handle:
                handle.write(text)
