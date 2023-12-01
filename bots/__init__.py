from .bot_base import Bot
from .smart_bot import SmartBot
from .dodging_collect_sphere_bot import DodgingCollectSphereBot
from .state_machine_bot import StateMachineBot
from .collect_sphere_bot import CollectSphereBot
from .wait_cling_bot import WaitClingBot
from .cling_bot import ClingBot
from .do_nothing_bot import DoNothingBot

bots = [SmartBot, DodgingCollectSphereBot, StateMachineBot, CollectSphereBot, WaitClingBot, ClingBot, DoNothingBot]
