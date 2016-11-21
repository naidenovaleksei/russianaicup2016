import random
from typing import List

from PathBuilding import VisibleMap
from Planning2 import BattleFront
from Points2D import Point2D
import Points2D

from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World

WAYPOINT_RADIUS = 100.0
START_WAIT_TICK = 250


class MyStrategy:
    def __init__(self, me: Wizard = None, world: World = None, game: Game = None, move: Move = None):
        self.debug = None
        self.waypoints = List[Point2D]
        self.initialized = False
        self.map = VisibleMap(self.debug)
        self.battle_front = None

    def initialize(self, me: Wizard, world: World, game: Game):
        random.seed(game.random_seed)
        self.waypoints = Points2D.get_waypoints_by_id(me.id, game)
        self.battle_front = BattleFront(world)
        self.initialized = True

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug:
            self.debug.syncronize(world)

        if not self.initialized:
            self.initialize(me, world, game)

        self.initialize_tick(me, world, game)

        score_threshold = -0.1
        wizard_score = me.life / (me.max_life * 0.5) - 1

        if self.battle_front:
            self.battle_front.init(world, me)
            front_score = self.battle_front.get_front_score(me)
            k = 0.6
            common_score = front_score * (1 - k) + wizard_score * k
        else:
            common_score = wizard_score

        if common_score < score_threshold:
            previous_waypoint = Points2D.get_previous_waypoint(self.waypoints, me)
            self.go_to(move, previous_waypoint)
            return
        else:
            nearest_target = Points2D.get_nearest_target(me, world)
            if nearest_target is not None:
                distance = me.get_distance_to_unit(nearest_target)

                if distance <= me.cast_range:
                    angle = me.get_angle_to_unit(nearest_target)
                    move.turn = angle
                    if abs(angle) < game.staff_sector / 2.0:
                        move.action = ActionType.MAGIC_MISSILE
                        move.cast_angle = angle
                        move.min_cast_distance = distance - nearest_target.radius + game.magic_missile_radius
                    return
                else:
                    new_x = me.x + (nearest_target.x - me.x) / distance * (distance - me.cast_range)
                    new_y = me.y + (nearest_target.y - me.y) / distance * (distance - me.cast_range)
                    self.go_to(move, Point2D(new_x, new_y))
                    return
            else:
                next_waypoint = Points2D.get_next_waypoint(self.waypoints, me)
                self.go_to(move, next_waypoint)

    def initialize_tick(self, me: Wizard, world: World, game: Game):
        self.map.init_tick(me, world, game)

    def go_to(self, move: Move, point: Point2D, angle=None):
        move.speed, move.strafe_speed, move.turn = self.map.get_optimal_move(point, angle)
