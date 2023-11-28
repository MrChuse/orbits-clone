from abc import ABC, abstractmethod

from back.core import PlayerSphere, GameState

class Bot(ABC, PlayerSphere):
    @abstractmethod
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return False