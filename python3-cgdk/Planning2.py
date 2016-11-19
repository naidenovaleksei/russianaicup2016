from model.Game import Game
from model.World import World
from model.Wizard import Wizard
from model.LivingUnit import LivingUnit
from model.CircularUnit import CircularUnit
from PathBuilding import Point2D
from model.LineType import LineType
from model.Faction import Faction

from typing import List

import math
import numpy as np


class BattleFront:
    canal_width = 800

    base_disp = 400

    def __init__(self, world: World):
        # equals.
        self.path_length = {
            LineType.TOP: world.height + world.width - 2 * self.base_disp,
            LineType.MIDDLE: (world.height + world.width - 2 * self.base_disp), # / 1.414,
            LineType.BOTTOM: world.height + world.width - 2 * self.base_disp
        }
        self.left = self.top = 0
        self.bottom = world.height
        self.right = world.width
        self.line_fronts = {
            LineType.TOP: List[LivingUnit],
            LineType.MIDDLE: List[LivingUnit],
            LineType.BOTTOM: List[LivingUnit]
        }
        self.world = world

    def calc_front_destination(self, line_type: LineType, me: Wizard):
        path_length = me.vision_range # self.path_length[line_type]
        score = 0
        me_pos = me.x + (self.bottom - me.y)
        friend_sum_pos = 0 # me.x + (self.bottom - me.y)
        friend_sum_life = 0 # me.life
        enemy_sum_life = enemy_sum_pos = 0
        for unit in self.line_fronts[line_type]:
            position = unit.x + (self.bottom - unit.y) - me_pos
            life = unit.life
            if unit.faction == me.faction:
                friend_sum_life += life
                friend_sum_pos += life * position
            elif unit.faction != Faction.NEUTRAL:
                enemy_sum_life += life
                enemy_sum_pos += life * position

        if friend_sum_life > 0:
            friend_sum_pos /= friend_sum_life
        else:
            friend_sum_pos = - path_length #self.base_disp

        if enemy_sum_life > 0:
            enemy_sum_pos /= enemy_sum_life
        else:
            enemy_sum_pos = path_length # path_length

        if enemy_sum_life + friend_sum_life > 0:
            common_pos = (friend_sum_pos * enemy_sum_life + enemy_sum_pos * friend_sum_life) / (enemy_sum_life + friend_sum_life)
        else:
            common_pos = path_length

        return common_pos / path_length

    def get_front_score(self, me: Wizard):
        line_types = self.define_line_types(me)
        return self.calc_front_destination(line_types[0], me)

    def add_unit_to_line(self, unit: LivingUnit, line_types: List[LineType]):
        for line_type in line_types:
            self.line_fronts[line_type].append(unit)

    def define_line_types(self, unit: LivingUnit):
        line_types = []
        x = unit.x
        y = unit.y #self.bottom - unit.y

        if min(abs(x - self.left), abs(y - self.top)) < self.canal_width:
            line_types.append(LineType.TOP)

        if min(abs(x - self.right), abs(y - self.bottom)) < self.canal_width:
            line_types.append(LineType.BOTTOM)

        if max(abs(x - self.left), abs(y - self.bottom)) < self.canal_width:
            line_types.append(LineType.MIDDLE)
        elif max(abs(x - self.right), abs(y - self.top)) < self.canal_width:
            line_types.append(LineType.MIDDLE)
        elif min(abs(x - self.left), abs(x - self.right), abs(y - self.bottom), abs(y - self.top)) > self.canal_width:
            line_types.append(LineType.MIDDLE)
        return line_types

    def add_unit(self, unit: LivingUnit):
        self.add_unit_to_line(unit, self.define_line_types(unit))

    def clear(self):
        self.line_fronts = {
            LineType.TOP: [],
            LineType.MIDDLE: [],
            LineType.BOTTOM: []
        }

    def init(self, world: World, me: Wizard):
        self.world = world
        self.clear()
        range = 1.5 * me.vision_range

        for unit in world.minions + world.buildings:
            if unit.get_distance_to_unit(me) <= range:
                self.add_unit(unit)
        for wizard in world.wizards:
            if not wizard.me and wizard.get_distance_to_unit(me) <= range:
                self.add_unit(wizard)
