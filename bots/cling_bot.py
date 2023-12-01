from back.core import GameState
from . import Bot

class ClingBot(Bot):
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return not self.rotating_around and self.is_in_rotator(state.rotators)