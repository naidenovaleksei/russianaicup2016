import math
import random

from model.ActionType import ActionType
from model.Faction import Faction
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World

WAYPOINT_RADIUS = 100.00
LOW_HP_FACTOR = 0.25

class Point2D:
    """
    Вспомогательный класс для хранения позиций на карте.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance_to(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def get_distance_to_point(self, point):
        return self.get_distance_to(point.x, point.y)

    def get_distance_to_unit(self, unit):
        return self.get_distance_to(unit.x, unit.y)

    def get_angle_to(self, x, y, angle):
        absolute_angle_to = math.atan2(y - self.y, x - self.x)
        relative_angle_to = absolute_angle_to - angle

        while relative_angle_to > math.pi:
            relative_angle_to -= 2.0 * math.pi

        while relative_angle_to < -math.pi:
            relative_angle_to += 2.0 * math.pi

        return relative_angle_to

    def get_angle_to_point(self, point, angle):
        return self.get_angle_to(point.x, point.y, angle)

    def get_angle_to_unit(self, unit, angle):
        return self.get_angle_to(unit.x, unit.y, angle)


def get_nearest_target(me: Wizard, world: World):
    """
    Находим ближайшую цель для атаки, независимо от её типа и других характеристик.
    """
    targets = []
    targets.extend(world.buildings)
    targets.extend(world.wizards)
    targets.extend(world.minions)

    nearest_target = None
    nearest_target_distance = 1.5 * me.vision_range

    for target in targets:
        # Нейтралов атакуем тоже если их хп меньше максимального - они стригеренны
        if (target.faction == Faction.NEUTRAL and target.life == target.max_life) or \
                 (target.faction == me.faction):
            continue

        distance = me.get_distance_to_unit(target)
        if distance < nearest_target_distance:
            nearest_target = target
            nearest_target_distance = distance

    return nearest_target

def apply_go_to_move(point: Point2D, me: Wizard, game: Game, move: Move):
    """
    Простейший способ перемещения волшебника.
    """
    angle = me.get_angle_to(point.x, point.y)
    move.turn = angle

    if math.fabs(angle) < game.staff_sector / 4.0:
        move.speed = game.wizard_forward_speed


def get_next_waypoint(waypoints, me: Wizard):
    """
    Данный метод предполагает, что все ключевые точки на линии упорядочены по уменьшению дистанции до последней
    ключевой точки. Перебирая их по порядку, находим первую попавшуюся точку, которая находится ближе к последней
    точке на линии, чем волшебник. Это и будет следующей ключевой точкой.

    Дополнительно проверяем, не находится ли волшебник достаточно близко к какой-либо из ключевых точек. Если это
    так, то мы сразу возвращаем следующую ключевую точку.
    """
    last_waypoint = waypoints[-1]
    for i, waypoint in enumerate(waypoints[:-1]):
        if waypoint.get_distance_to_unit(me) <= WAYPOINT_RADIUS:
            return waypoints[i + 1]

        if last_waypoint.get_distance_to_point(waypoint) < last_waypoint.get_distance_to_unit(me):
            return waypoint

    return last_waypoint


def get_previous_waypoint(waypoints, me: Wizard):
    return get_next_waypoint(waypoints[::-1], me)


def get_waypoints_by_id(id, game: Game):
    map_size = game.map_size
    if id in [1, 2, 6, 7]:
        # точки верхней линии
        return [
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
        ]
    elif id in [3, 8]:
        # точки средней линии
        return [
            Point2D(100.0, map_size - 100.0),
            random.choice([Point2D(600.0, map_size - 200.0), Point2D(200.0, map_size - 600.0)]),
            Point2D(800.0, map_size - 800.0),
            Point2D(map_size - 600.0, 600.0)
        ]
    else:
        # точки нижней линии
        return [
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

    # def get_next_waypoint(self):
    #     last_waypoint_index = len(self.waypoints) - 1
    #     last_waypoint = self.waypoints[last_waypoint_index]
    #
    #     for waypoint_index in range(len(self.waypoints)):
    #         if waypoint_index == last_waypoint_index:
    #             continue
    #
    #         waypoint = self.waypoints[waypoint_index]
    #
    #         if waypoint.get_distance_to_unit(self.me) <= WAYPOINT_RADIUS:
    #             return self.waypoints[waypoint_index + 1]
    #
    #         if last_waypoint.get_distance_to_unit(waypoint) < last_waypoint.get_distance_to_unit(self.me):
    #             return waypoint
    #
    #     return last_waypoint

    # def get_previous_waypoint(self):
    #     first_waypoint_index = 0
    #     first_waypoint = self.waypoints[first_waypoint_index]
    #
    #     for waypointIndex in reversed(range(len(self.waypoints))):
    #         if waypointIndex == first_waypoint_index:
    #             continue
    #
    #         waypoint = self.waypoints[waypointIndex]
    #
    #         if waypoint.get_distance_to_unit(self.me) <= WAYPOINT_RADIUS:
    #             return self.waypoints[waypointIndex - 1]
    #
    #         if first_waypoint.get_distance_to_unit(waypoint) < first_waypoint.get_distance_to_unit(self.me):
    #             return waypoint
    #
    #     return first_waypoint

    # def get_nearest_target(self):
    #     targets = self.world.buildings + self.world.wizards + self.world.minions
    #
    #     if len(targets) == 0:
    #         return None
    #
    #     nearest_target = None
    #     nearest_target_distance = 1.5 * self.me.vision_range # float("inf")
    #
    #     for target in targets:
    #         if (target.faction == Faction.NEUTRAL) or (target.faction == self.me.faction):
    #             continue
    #
    #         distance = self.me.get_distance_to_unit(target)
    #
    #         if distance < nearest_target_distance:
    #             nearest_target = target
    #             nearest_target_distance = distance
    #
    #     return nearest_target

