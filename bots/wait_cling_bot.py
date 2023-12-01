from back.core import GameState
from . import Bot

class WaitClingBot(Bot):
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.timer = 0

    def get_action(self, state: GameState, time_delta: float) -> bool:
        if self.timer < 5:
            self.timer += time_delta
            return False
        return not self.rotating_around and self.is_in_rotator(state.rotators)