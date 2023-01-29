import asyncio
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from system.scene import SceneManager

if __name__ == "__main__":
    from qasync import QEventLoop
    from ScenesWindow import ScenesWindow
    from scenes import scenes

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        manager = SceneManager()
        for scene in scenes:
            manager.register_scene(scene)
        mainWindow = ScenesWindow(manager)
        mainWindow.show()
        loop.run_forever()
