import inspect
from functools import wraps
from typing import Optional, Callable, Any, Coroutine

from .scene import Scene
from .action_task import ActionTask

NoneFuncT = Callable[..., None]
NoneCoroutineT = Coroutine[Any, Any, None]
NoneAsyncFuncT = Callable[..., NoneCoroutineT]


# https://stackoverflow.com/questions/74344564/why-doesnt-pycharm-hint-work-with-decorators

def action(on_stop: Optional[NoneAsyncFuncT] = None) -> Callable[[NoneFuncT], Callable[..., ActionTask]]:

    if on_stop is not None:
        if not inspect.iscoroutinefunction(on_stop):
            raise RuntimeError("The @action decorator accepts async functions only as on_stop callback")

    def outer(func: Callable) -> Callable[..., ActionTask]:
        if not inspect.iscoroutinefunction(func):
            raise RuntimeError("The @action decorator can only be applied to async functions")

        @wraps(func)
        def wrapper(*args, **kwargs) -> ActionTask:
            if len(args) == 0:
                raise RuntimeError("The @action decorator can only be applied to methods of the class")

            scene: Scene = args[0]

            if not isinstance(scene, Scene):
                raise RuntimeError("The @action decorator can only be applied to methods of the Scene class")

            context = ActionTask(scene.context, func, args, kwargs)
            context.on_stop = on_stop
            return context

        return wrapper

    return outer
