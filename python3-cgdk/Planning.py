from model.Game import Game
from model.World import World
from model.Wizard import Wizard
from model.CircularUnit import CircularUnit
from PathBuilding import Point2D
from model.LineType import LineType

import math
import numpy as np

pos_disp = 200
minion_appearance_pos = {
    LineType.TOP: Point2D(200, 3000)
}

minion_pos = {
	LineType.TOP: lambda s: Point2D(200 + max(0, s - abs(3000 - 200),
									max(200, 3000 - s))	
}


def get_minion_pos(s=0, line_type=LineType.TOP):
    return minion_pos[line_type](s)



class Planning:
    def __init__(self):
        x = 0

    def get_predicted_minion_poses(self, game: Game, world: World):
        now = world.tick_index
        minion_interval = game.faction_minion_appearance_interval_ticks
        waves_count, current_wave_time = divmod(now, minion_interval)

        if waves_count == 0:
            return None # no minion has been appeared

        minion_poses = []
        minion_speed = game.minion_speed
        for i in range(waves_count):
            s = (i * minion_interval + current_wave_time) * minion_speed
            minion_poses.append(get_minion_pos(s, LineType.TOP))


    def predictMassCenter(self, game: Game, world: World):
        now = world.tick_index
        minion_interval = game.faction_minion_appearance_interval_ticks
        waves_count, current_wave_time = divmod(now, minion_interval)

        if waves_count == 0:
            return Point2D(pos_disp, pos_disp) # no minion has been appeared

        minion_speed = game.minion_speed






