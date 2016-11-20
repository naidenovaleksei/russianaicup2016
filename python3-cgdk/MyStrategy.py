from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from model.LaneType import LaneType as LineType
from model.Faction import Faction
from PathBuilding import Point2D, VisibleMap
from Planning2 import BattleFront
import random

WAYPOINT_RADIUS = 100.0

class MyStrategy:
    def __init__(self, me: Wizard = None, world: World = None, game: Game = None, move: Move = None):
        from typing import Dict, List
        self.debug = None
        self.isInit = False
        self.waypoints_by_line = Dict[LineType, List[Point2D]]
        self.waypoints = List[Point2D]
        self.me = me
        self.world = world
        self.game = game
        self._move = move

        self.map = VisibleMap(self.debug)

        self.last_move = None
        self.last_move_duration = 0
        self.last_tick = 0
        self.move_index = 0

        self.battle_front = None
        self.front_score = 0

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug:
            self.debug.syncronize(world)

        self.initialize_strategy(me, world, game)
        self.initialize_tick(me, world, game, move)
        self.map.init_tick(me, world, game)

        score_threshold = -0.1
        wizard_score = me.life / (me.max_life * 0.5) - 1

        if self.battle_front:
            self.battle_front.init(world, me)
            self.front_score = self.battle_front.get_front_score(me)
            k = 0.6
            common_score = self.front_score * (1 - k) + wizard_score * k
        else:
            common_score = wizard_score
            self.battle_front = BattleFront(world)

        if common_score < score_threshold:
            previous_waypoint = self.get_previous_waypoint()
            self.go_to(previous_waypoint)
            return
        else:
            nearest_target = self.get_nearest_target()
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
                    self.go_to(Point2D(new_x, new_y))
                    return
            else:
                next_waypoint = self.get_next_waypoint()
                self.go_to(next_waypoint)

    def initialize_strategy(self, me: Wizard, world: World, game: Game):
        if ~self.isInit:
            self.isInit = True
            random.seed = game.random_seed
            map_size = game.map_size

            self.waypoints_by_line = {
                LineType.MIDDLE: [
                    Point2D(100.0, map_size - 100.0),
                    Point2D(600.0, map_size - 200.0)
                    if bool(random.getrandbits(1))
                    else Point2D(200.0, map_size - 600.0),
                    Point2D(800.0, map_size - 800.0),
                    Point2D(map_size - 600.0, 600.0)
                ],
                LineType.TOP: [
                    Point2D(100.0, map_size - 100.0),
                    Point2D(100.0, map_size - 400.0),
                    Point2D(200.0, map_size - 800.0),
                    Point2D(200.0, map_size * 0.75),
                    Point2D(200.0, map_size * 0.5),
                    Point2D(200.0, map_size * 0.25),
                    Point2D(200.0, 200.0),
                    Point2D(map_size * 0.25, 200.0),
                    Point2D(map_size * 0.5, 200.0),
                    Point2D(map_size * 0.75, 200.0),
                    Point2D(map_size - 200.0, 200.0)
                ],
                LineType.BOTTOM: [
                    Point2D(100.0, map_size - 100.0),
                    Point2D(400.0, map_size - 100.0),
                    Point2D(800.0, map_size - 200.0),
                    Point2D(map_size * 0.25, map_size - 200.0),
                    Point2D(map_size * 0.5, map_size - 200.0),
                    Point2D(map_size * 0.75, map_size - 200.0),
                    Point2D(map_size - 200.0, map_size - 200.0),
                    Point2D(map_size - 200.0, map_size * 0.75),
                    Point2D(map_size - 200.0, map_size * 0.5),
                    Point2D(map_size - 200.0, map_size * 0.25),
                    Point2D(map_size - 200.0, 200.0)
                ]
            }

            line = {
                1: LineType.TOP,
                2: LineType.TOP,
                6: LineType.TOP,
                7: LineType.TOP,
                3: LineType.MIDDLE,
                8: LineType.MIDDLE,
                4: LineType.BOTTOM,
                5: LineType.BOTTOM,
                9: LineType.BOTTOM,
                10: LineType.BOTTOM,
            }[me.id]

            self.waypoints = self.waypoints_by_line[line]

    def initialize_tick(self, me: Wizard, world: World, game: Game, move: Move):
        self.me = me
        self.world = world
        self.game = game
        self._move = move

    def get_next_waypoint(self):
        last_waypoint_index = len(self.waypoints) - 1
        last_waypoint = self.waypoints[last_waypoint_index]

        for waypoint_index in range(len(self.waypoints)):
            if waypoint_index == last_waypoint_index:
                continue

            waypoint = self.waypoints[waypoint_index]

            if waypoint.get_distance_to_unit(self.me) <= WAYPOINT_RADIUS:
                return self.waypoints[waypoint_index + 1]

            if last_waypoint.get_distance_to_unit(waypoint) < last_waypoint.get_distance_to_unit(self.me):
                return waypoint

        return last_waypoint

    def get_previous_waypoint(self):
        first_waypoint_index = 0
        first_waypoint = self.waypoints[first_waypoint_index]

        for waypointIndex in reversed(range(len(self.waypoints))):
            if waypointIndex == first_waypoint_index:
                continue

            waypoint = self.waypoints[waypointIndex]

            if waypoint.get_distance_to_unit(self.me) <= WAYPOINT_RADIUS:
                return self.waypoints[waypointIndex - 1]

            if first_waypoint.get_distance_to_unit(waypoint) < first_waypoint.get_distance_to_unit(self.me):
                return waypoint

        return first_waypoint

    def go_to(self, point: Point2D, angle=None):
        self._move.speed, self._move.strafe_speed, self._move.turn = self.map.get_optimal_move(point, angle)

    def get_nearest_target(self):
        targets = self.world.buildings + self.world.wizards + self.world.minions

        if len(targets) == 0:
            return None

        nearest_target = None
        nearest_target_distance = 1.5 * self.me.vision_range # float("inf")

        for target in targets:
            if (target.faction == Faction.NEUTRAL) or (target.faction == self.me.faction):
                continue

            distance = self.me.get_distance_to_unit(target)

            if distance < nearest_target_distance:
                nearest_target = target
                nearest_target_distance = distance

        return nearest_target
