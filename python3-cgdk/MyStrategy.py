import random
from typing import List

from PathBuilding import VisibleMap
from Planning2 import BattleFront
from Points2D import Point2D, min_atack_distance
import Points2D

from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World

WAYPOINT_RADIUS = 100.0
START_WAIT_TICK = 250
START_SCORE_TRESHOLD = 0.0
START_LIMIT_UP_TIMES = 10
STOP_CHECK_TICK_COUNT = 10
SLOW_MOVE_TICK_COUNT = 500

class Health:
    Bad = 1
    Ok = 2
    Good = 3

class Action:
    NEXT = 0
    ENEMY = 1
    BACK = 2

class MyStrategy:
    def __init__(self, me: Wizard = None, world: World = None, game: Game = None, move: Move = None):
        self.debug = None
        self.waypoints = List[Point2D]
        self.initialized = False
        self.map = VisibleMap(self.debug)
        self.battle_front = None
        self.score_threshold = START_SCORE_TRESHOLD
        self.limit_up_times = START_LIMIT_UP_TIMES
        self.health = Health.Good
        self.last_poses = [x for x in range(STOP_CHECK_TICK_COUNT)]
        self.last_actions = [-1 for x in range(STOP_CHECK_TICK_COUNT)]

    def initialize(self, me: Wizard, world: World, game: Game):
        random.seed(game.random_seed)
        self.waypoints = Points2D.get_waypoints_by_id(me.id, game)
        self.battle_front = BattleFront(world, me)
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
            self.map.note_enemy_angle = False
            self.go_to(move, previous_waypoint, note_angle=False)
            self.last_actions[world.tick_index % STOP_CHECK_TICK_COUNT] = Action.BACK
            return
        else:
            nearest_target = Points2D.get_nearest_target(me, world)
            if nearest_target is not None:
                distance = me.get_distance_to_unit(nearest_target)

                if distance <= me.cast_range:
                    angle = me.get_angle_to_unit(nearest_target)
                    # move.turn = angle
                    self.go_to(move, None, note_angle=False)
                    if abs(angle) < game.staff_sector / 2.0:
                        move.action = ActionType.MAGIC_MISSILE
                        move.cast_angle = angle
                        move.min_cast_distance = distance - nearest_target.radius + game.magic_missile_radius
                    self.last_actions[world.tick_index % STOP_CHECK_TICK_COUNT] = Action.ENEMY
                    return
                else:
                    new_x = me.x + (nearest_target.x - me.x) / distance * (distance - min_atack_distance(me))
                    new_y = me.y + (nearest_target.y - me.y) / distance * (distance - min_atack_distance(me))
                    self.go_to(move, Point2D(new_x, new_y), note_angle=True)
                    self.last_actions[world.tick_index % STOP_CHECK_TICK_COUNT] = Action.NEXT
                    return
            else:
                next_waypoint = Points2D.get_next_waypoint(self.waypoints, me)
                note_angle = True
                if world.tick_index > STOP_CHECK_TICK_COUNT:
                    last_pos_index = (world.tick_index + 1) % STOP_CHECK_TICK_COUNT
                    dist_last_poses = me.get_distance_to_unit(self.last_poses[last_pos_index])
                    # если далеко не ушел и если последние все действия NEXT
                    if ((dist_last_poses < STOP_CHECK_TICK_COUNT * 0.2 * game.wizard_forward_speed) and
                                      (sum([x == Action.NEXT for x in self.last_actions]) == STOP_CHECK_TICK_COUNT)):
                        note_angle = False
                self.go_to(move, next_waypoint, note_angle=note_angle)
                self.last_actions[world.tick_index % STOP_CHECK_TICK_COUNT] = Action.NEXT
                if world.tick_index < SLOW_MOVE_TICK_COUNT:
                    move.speed *= 0.5
                    move.strafe_speed *= 0.5
                return

    def initialize_tick(self, me: Wizard, world: World, game: Game):
        self.map.init_tick(me, world, game)
        self.last_poses[world.tick_index % STOP_CHECK_TICK_COUNT] = Point2D(me.x, me.y)
        wizard_ratio = me.life / me.max_life
        if wizard_ratio <= 0.25:
            if self.health in [Health.Ok, Health.Good]:
                self.increase_score_threshold()
            self.health = Health.Bad
        if 0.25 < wizard_ratio < 0.75:
            self.health = Health.Ok
        if 0.75 <= wizard_ratio:
            if self.health in [Health.Ok, Health.Bad]:
                self.decrease_score_threshold()
            self.health = Health.Good


    def increase_score_threshold(self):
        self.score_threshold = (self.score_threshold * self.limit_up_times + 1) / (self.limit_up_times + 1)
        self.limit_up_times += 1

    def decrease_score_threshold(self):
        self.score_threshold = (self.score_threshold * self.limit_up_times - 1) / (self.limit_up_times + 1)
        self.limit_up_times += 1

    def go_to(self, move: Move, point: Point2D, angle=None, note_angle=False):
        move.speed, move.strafe_speed, move.turn = self.map.get_optimal_move(point, angle, note_angle)
