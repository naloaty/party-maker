import sys
from dataclasses import dataclass
from pathlib import Path
import asyncio

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog
from vlc import Instance, EventType, Event

from system.services.projector.projector_ui import Ui_MediaDisplay


@dataclass
class Media:
    path: str


class Projector(QDialog):
    fullscreen: bool = False

    def __init__(self):
        QDialog.__init__(self)

        self.ui = Ui_MediaDisplay()
        self.ui.setupUi(self)

        self._vlc = Instance("--loop")
        self._vlc.log_unset()
        self._player = self._vlc.media_player_new()

        self.setWindowFlags(Qt.WindowType.Window)

        self._vlc_event_manager = self._player.event_manager()
        self._vlc_event_manager.event_attach(EventType.MediaPlayerTimeChanged, self._media_time_changed)
        self._position_locks: dict[int, asyncio.Event] = dict()

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.fullscreen:
            self.showNormal()
            self.fullscreen = False
        else:
            self.showFullScreen()
            self.fullscreen = True
        super().mouseDoubleClickEvent(a0)

    def placeholder(self):
        self.show()
        self._player.set_media(self._vlc.media_new(f"{Path.cwd()}/assets/placeholder.jpg"))
        self.init_frame()
        self._player.play()

    def init_frame(self):
        if sys.platform.startswith('linux'):  # for Linux using the X Server
            self._player.set_xwindow(self.ui.videoframe.winId())
        elif sys.platform == "win32":  # for Windows
            self._player.set_hwnd(self.ui.videoframe.winId())
        elif sys.platform == "darwin":  # for MacOS
            self._player.set_nsobject(int(self.ui.videoframe.winId()))

    async def play(self, media: Media) -> None:
        self._player.set_media(self._vlc.media_new(media.path))
        self.init_frame()
        self._player.play()
        # self.showFullScreen()
        await asyncio.sleep(1)
        while self._player.is_playing():
            await asyncio.sleep(0.1)

    def reset(self):
        self._position_locks.clear()

    async def wait_position(self, position: int) -> None:
        lock = asyncio.Event()
        self._position_locks[position] = lock
        await lock.wait()

    def _media_time_changed(self, event: Event) -> None:
        curr_time = self._player.get_time()
        released = []
        for position in self._position_locks.keys():
            if curr_time >= position:
                lock = self._position_locks[position]
                lock._loop.call_soon_threadsafe(lock.set)
                released.append(position)

        for lock in released:
            del self._position_locks[lock]

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self.placeholder()

    def set_fullscreen(self, fullscreen: bool) -> None:
        self._player.set_fullscreen(fullscreen)

    def set_position(self, position: int) -> None:
        self._player.set_time(position)

    def get_position(self) -> int:
        return self._player.get_time()
