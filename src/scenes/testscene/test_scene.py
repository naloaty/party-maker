import asyncio

from system.scene import Scene, action


class TestScene(Scene):
    NAME = "Тестовая сцена"

    def on_start(self):
        self.run_action(self.do_something(42))

    async def something_done(self, reason: Scene.StopReason):
        print(f"something_done: {reason}")
        await asyncio.sleep(3)

    @action(something_done)
    async def do_something(self, x: int) -> None:
        for i in range(10):
            print(f"{self.NAME}: action {i} (x={x}) call")
            await asyncio.sleep(1)

    def on_stop(self):
        print("on_stop")
