import asyncio
from PyQt6.QtWidgets import QDialog
from system.services.projector import Media, Projector
from system.services.lighting import Light
from system.scene import Scene, ActionManager
from .active_challenge_ui import Ui_ActiveChallenge

USUAL_GAME = Media("D:/NotGames/Обычное испытание.mp4")
FINAL_GAME = Media("D:/NotGames/Финальное испытание.mp4")
FAILURE = Media("D:/NotGames/Провалено 0.wav")
SUCCESS = Media("D:/NotGames/Выполнено 0.wav")

# neutral white
DEFAULT_LIGHT = Light(Light.Type.TEMP, temperature=3620, brightness=100)


class ActiveChallenge(Scene, QDialog):
    NAME = "Испытание"

    def __init__(self):
        Scene.__init__(self)
        QDialog.__init__(self)
        self.ui = Ui_ActiveChallenge()
        self.ui.setupUi(self)

        self.ui.btn_start.clicked.connect(self.on_start_click)
        self.ui.btn_stop.clicked.connect(self.on_stop_click)
        self.ui.btn_success.clicked.connect(self.on_success_click)
        self.ui.btn_fail.clicked.connect(self.on_fail_click)

    def on_start(self):
        self.show()

    def on_stop(self):
        self.hide()

    def reject(self) -> None:
        self.stop()

    # ===== Buttons =====

    def on_start_click(self):
        self.run_action(self.game_in_progress(), self.game_finished)

    def on_stop_click(self):
        self.run_action(self.game_interrupted(), None)

    def on_success_click(self):
        self.run_action(self.game_succeeded(), self.game_finished)

    def on_fail_click(self):
        self.run_action(self.game_failed(), self.game_finished)

    # ===== Actions =====

    @ActionManager.action
    async def game_in_progress(self):
        stage = self.context.get_stage()
        self.ui.btn_start.setEnabled(False)
        self.ui.btn_stop.setEnabled(True)
        final = self.ui.cb_final.isChecked()
        timeout = self.ui.cb_timeout.isChecked()

        stage.lighting.set(Light(  # pre-game color: turquoise
            Light.Type.COLOR, hue=180, saturation=100, brightness=100))

        if final:
            asyncio.create_task(stage.display.play(FINAL_GAME))
            await stage.display.wait_position(6200)
        else:
            asyncio.create_task(stage.display.play(USUAL_GAME))
            await stage.display.wait_position(5050)

        self.ui.btn_fail.setEnabled(True)
        self.ui.btn_success.setEnabled(True)

        stage.lighting.set(Light(  # game color: neutral white
            Light.Type.TEMP, temperature=3620, brightness=100))

        if final:
            await stage.display.wait_position(68500)
        else:
            await stage.display.wait_position(67500)

        self.ui.btn_stop.setEnabled(False)
        self.ui.btn_fail.setEnabled(False)
        self.ui.btn_success.setEnabled(False)

        if not final and timeout:
            asyncio.create_task(Projector().play(FAILURE))
            await asyncio.sleep(1)
            stage.lighting.set(Light(  # failure: red
                Light.Type.COLOR, hue=0, saturation=100, brightness=100))
            await asyncio.sleep(5)

    async def game_finished(self, reason: Scene.StopReason):
        stage = self.context.get_stage()

        _return = reason == Scene.StopReason.Return
        _local = reason == Scene.StopReason.LocalIntercept
        _external = reason == Scene.StopReason.ExternalIntercept
        _stop = reason == Scene.StopReason.SceneStop

        if _stop or _external:
            stage.display.stop()

        self.ui.btn_start.setEnabled(True)
        self.ui.btn_stop.setEnabled(False)
        self.ui.btn_fail.setEnabled(False)
        self.ui.btn_success.setEnabled(False)
        stage.lighting.set(DEFAULT_LIGHT)
        stage.display.reset()

    @ActionManager.action
    async def game_succeeded(self):
        stage = self.context.get_stage()
        stage.display.pause()
        stage.lighting.set(Light(  # success: gold
            Light.Type.COLOR, hue=41, saturation=27, brightness=100))
        await asyncio.create_task(Projector().play(SUCCESS))
        await asyncio.sleep(8)

    @ActionManager.action
    async def game_failed(self):
        stage = self.context.get_stage()
        stage.display.pause()
        asyncio.create_task(Projector().play(FAILURE))
        stage.lighting.set(Light(  # failure: red
            Light.Type.COLOR, hue=0, saturation=100, brightness=100))
        await asyncio.sleep(8)

    @ActionManager.action
    async def game_interrupted(self):
        stage = self.context.get_stage()
        stage.display.stop()
