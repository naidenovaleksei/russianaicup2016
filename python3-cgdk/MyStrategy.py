from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from model.LineType import LineType
from model.Faction import Faction
from PathBuilding import Point2D, VisibleMap
from Planning2 import BattleFront

try:
    from debug_client import Color
except ImportError:
    pass

import math
import random

canvas_width = 200
canvas_height =200
python_green = "#476042"

WAYPOINT_RADIUS = 100.0
LOW_HP_FACTOR = 0.25

class MoveType:
    STOP = 0
    FORWARD = 1
    BACKWARD = 2
    TURN = 5
    GO_TO_POINT = 10000


class MoveNow:
    def __init__(self, move_type=MoveType.STOP, duration=-1, point=None, angle=0):
        self.move_type = move_type
        self.duration = duration
        self.point = point
        self.angle = angle

    def __str__(self):
        return "member of Test"

C_EmptyMoveNow = MoveNow()


class MyStrategy:
    def __init__(self, me: Wizard = None, world: World = None, game: Game = None, move: Move = None):
        from typing import Dict, List
        self.debug = None
        try:
            from debug_client import DebugClient
        except ImportError: # no debug module, maybe running on the russianaicup.ru server
            self.debug = None
        else:
            self.debug = DebugClient()
            self.green = Color(r=0.0, g=1.0, b=0.0)
            self.red = Color(r=1.0, g=0.0, b=0.0)
            self.grey = Color(r=0.7, g=0.7, b=0.7)
            self.black = Color(r=0.0, g=0.0, b=0.0)
            self.yellow = Color(r=1.0, g=1.0, b=0.0)
        self.isInit = False
        self.waypoints_by_line = Dict[LineType, List[Point2D]]
        self.waypoints = List[Point2D]
        self.me = me
        self.world = world
        self.game = game
        self._move = move
        self._last_waypoint = None
        self._last_nearest_target = None
        self._last_attack_tick_index = 0

        self.map = VisibleMap(self.debug)

        self.last_move = None
        self.last_move_duration = 0
        self.last_tick = 0
        self.move_index = 0

        self.battle_front = None
        self.front_score = 0

        self.log = {
            'go_to_previous_waypoint': lambda: print(self.world.tick_index,
                                       'previous',
                                       self.front_score,
                                       self._last_waypoint.x,
                                       self._last_waypoint.y,
                                       self.me.life, sep = '\t'),
            'go_to_next_waypoint': lambda: print(self.world.tick_index,
                                   'next    ',
                                   self.front_score,
                                   self._last_waypoint.x,
                                   self._last_waypoint.y,
								   self.me.life, sep = '\t'),
            'attack': lambda: print(self.world.tick_index,
                                    'attack  ',
                                    self.front_score,
                                    self._last_nearest_target.x,
                                    self._last_nearest_target.y,
                                    self._last_nearest_target.id,
                                    self._last_nearest_target.life,
                                    self.me.life, sep = '\t')
        }

    def do_your_move(self, move = C_EmptyMoveNow):
        pos_str = "{:.0f} {:.0f} {:.3f}".format(self.me.x, self.me.y, self.me.angle)
        speed_str = "{:.0f} {:.0f} {:.3f}".format(self.me.speed_x, self.me.speed_y, math.hypot(self.me.speed_x, self.me.speed_y))
        self.last_move_duration -= (self.world.tick_index - self.last_tick)
        self.last_tick = self.world.tick_index

        if self.last_move != move.move_type:
            self.last_move = move.move_type
            self.last_move_duration = move.duration

        if move.move_type == MoveType.GO_TO_POINT:
            self.last_move = MoveType.GO_TO_POINT
            if move.point is None:
                print("next point to go is not None")
                self.last_move = MoveType.STOP
            elif self.me.get_distance_to_unit(move.point) <= 1:
                self.next_move()
                print("next_move")
            else:
                #print("go to ", move.point.x, move.point.y, pos_str)
                print(self.world.tick_index, "move ", move.point.x, move.point.y, speed_str)
                self.go_to(move.point)
            return
        elif move.move_type == MoveType.STOP:
            self._move.speed = 0
            self._move.turn = 0
        elif move.move_type == MoveType.FORWARD:
            if self.last_move_duration > 0:
                self._move.speed = self.game.wizard_forward_speed
                self._move.turn = 0
            else:
                self._move.speed = 0
                self._move.turn = 0
                self.next_move()
                print("next_move")
            print("FORWARD ", self.last_move_duration, pos_str)
        elif move.move_type == MoveType.BACKWARD:
            if self.last_move_duration > 0:
                self._move.speed = -self.game.wizard_backward_speed
                self._move.turn = 0
            else:
                self._move.speed = 0
                self._move.turn = 0
                self.next_move()
                print("next_move")
            print("BACKWARD ", self.last_move_duration, pos_str)
        elif move.move_type == MoveType.TURN:
            if abs(move.angle - self.me.angle) >= math.pi / 180:
                self._move.speed = 0
                self._move.turn = move.angle - self.me.angle
            else:
                self._move.speed = 0
                self._move.turn = 0
                self.next_move()
                print("next_move")
            print("TURN ", self.last_move_duration, pos_str)


    def next_move(self):
        self.move_index += 1

    def do_next_move(self, move_list=[]):
        if len(move_list) > self.move_index:
            self.do_your_move(move_list[self.move_index])




    # /**
    #  * Основной метод стратегии, осуществляющий управление волшебником.
    #  * Вызывается каждый тик для каждого волшебника.
    #  *
    #  * @param me  Волшебник, которым данный метод будет осуществлять управление.
    #  * @param world Текущее состояние мира.
    #  * @param game  Различные игровые константы.
    #  * @param move  Результатом работы метода является изменение полей данного объекта.
    #  */
    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug:
            # call this the very first thing in your move()
            # to sync replays played in local runner and in repeater
            self.debug.syncronize(world)

        self.initialize_strategy(me, world, game)
        self.initialize_tick(me, world, game, move)
        self.map.init_tick(me, world, game)

        score_threshold = -0.1
        wizard_score = me.life / (me.max_life * 0.5) - 1
        common_score = 0

        if self.battle_front:
            self.battle_front.init(world, me)
            self.front_score = self.battle_front.get_front_score(me)
            # common_score = self.front_score + wizard_score
            k = 0.6
            common_score = self.front_score * (1 - k) + wizard_score * k
            print("{}:front: {:.2f}; wizard:{:.2f}; common: {:.2f}".format(self.world.tick_index, self.front_score, wizard_score, common_score))
        else:
            common_score = wizard_score
            self.battle_front = BattleFront(world)


        previous_waypoint = self.get_previous_waypoint()
        next_waypoint = self.get_next_waypoint()
        # if self.debug:
        #     with self.debug.pre() as dbg:
        #         dbg.circle(next_waypoint.x, next_waypoint.y, 50, self.green)
        #         dbg.circle(previous_waypoint.x, previous_waypoint.y, 50, self.red)
        #         if self.battle_front:
        #             colors = {
        #                 LineType.TOP: self.yellow,
        #                 LineType.MIDDLE: self.red,
        #                 LineType.BOTTOM: self.green
        #             }
        #             for unit in world.wizards + world.minions + world.buildings:
        #                 lines = self.battle_front.define_line_types(unit)
        #                 if len(lines) > 0:
        #                     dbg.circle(unit.x, unit.y, 50, colors[lines[0]])
        #                 else:
        #                     print("error no line type")


        # // Если осталось мало жизненной энергии, отступаем к предыдущей ключевой точке на линии.
        # if me.life < me.max_life * LOW_HP_FACTOR:
        if common_score < score_threshold:
            previous_waypoint = self.get_previous_waypoint()
            self.go_to(previous_waypoint)
            if self._last_waypoint.x != previous_waypoint.x or self._last_waypoint.y != previous_waypoint.y:
                self._last_waypoint = previous_waypoint
                self.log['go_to_previous_waypoint']()
            return

        nearest_target = self.get_nearest_target()

        # // Если видим противника ...
        if nearest_target is not None:
            distance = me.get_distance_to_unit(nearest_target)

            # // ... и он в пределах досягаемости наших заклинаний, ...
            if distance <= me.cast_range:
                angle = me.get_angle_to_unit(nearest_target)

                # // ... то поворачиваемся к цели.
                move.turn = angle
                # self.go_to(nearest_target, move.turn)
                # move.turn = angle

                # // Если цель перед нами, ...
                if abs(angle) < game.staff_sector / 2.0:
                    # // ... то атакуем.
                    if self._last_nearest_target is None or self._last_nearest_target.id == nearest_target.id:
                        self._last_nearest_target = nearest_target
                        if abs(self.world.tick_index - self._last_attack_tick_index) > self.game.magic_missile_cooldown_ticks:
                            self._last_attack_tick_index = self.world.tick_index
                            self.log['attack']()
                    move.action = ActionType.MAGIC_MISSILE
                    move.cast_angle = angle
                    move.min_cast_distance = distance - nearest_target.radius + game.magic_missile_radius
                    # self.go_to(nearest_target, move.turn)
                    # move.turn = angle

                return
            else:
                new_x = me.x + (nearest_target.x - me.x) / distance * (distance - me.cast_range)
                new_y = me.y + (nearest_target.y - me.y) / distance * (distance - me.cast_range)
                self.go_to(Point2D(new_x, new_y))
                return

        # // Если нет других действий, просто продвигаемся вперёд.
        next_waypoint = self.get_next_waypoint()
        self.go_to(next_waypoint)
        if self._last_waypoint is None or self._last_waypoint.x != next_waypoint.x or self._last_waypoint.y != next_waypoint.y:
            self._last_waypoint = next_waypoint
            self.log['go_to_next_waypoint']()

    # /**
    #  * Инциализируем стратегию.
    #  * <p>
    #  * Для этих целей обычно можно использовать конструктор, однако в данном случае мы хотим инициализировать генератор
    #  * случайных чисел значением, полученным от симулятора игры.
    #  */
    def initialize_strategy(self, me: Wizard, world: World, game: Game):
        if ~self.isInit:
            self.isInit = True
            random.seed = game.random_seed

            map_size = game.map_size

            # /**
            #  * Ключевые точки для каждой линии, позволяющие упростить управление перемещением волшебника.
            #  * <p>
            #  * Если всё хорошо, двигаемся к следующей точке и атакуем противников.
            #  * Если осталось мало жизненной энергии, отступаем к предыдущей точке.
            #  */
            self.waypoints_by_line = {
                LineType.MIDDLE: [
                    Point2D(100.0, map_size - 100.0),
                    # Point2D(600.0, map_size - 200.0)
                    # if bool(random.getrandbits(1))
                    # else Point2D(200.0, map_size - 600.0),
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

            # if self.debug:
            #     step = 100
            #     with self.debug.pre() as dbg:
            #         for line_ in self.waypoints_by_line:
            #             for point in self.waypoints_by_line[line_]:
            #                 dbg.circle(point.x, point.y, 40, self.black)
            #         for i in range(40):
            #             dbg.line(0, i*step, map_size, i*step, self.grey)
            #             dbg.text(0 + 20, i*step, str(i*step), self.black)
            #         for i in range(40):
            #             dbg.line(i*step, 0, i*step, map_size, self.grey)
            #             dbg.text(i*step, map_size - 20, str(i*step), self.black)

            # // Наша стратегия исходит из предположения, что заданные нами ключевые точки упорядочены по убыванию
            # // дальности до последней ключевой точки. Сейчас проверка этого факта отключена, однако вы можете
            # // написать свою проверку, если решите изменить координаты ключевых точек.

            # /*Point2D lastWaypoint = waypoints[waypoints.length - 1];
            #
            # Preconditions.checkState(ArrayUtils.isSorted(waypoints, (waypointA, waypointB) -> Double.compare(
            #         waypointB.get_distance_to(lastWaypoint), waypointA.get_distance_to(lastWaypoint)
            # )));*/

    # /**
    #  * Сохраняем все входные данные в полях класса для упрощения доступа к ним.
    #  */
    def initialize_tick(self, me: Wizard, world: World, game: Game, move: Move):
        self.me = me
        self.world = world
        self.game = game
        self._move = move

    # /**
    #  * Данный метод предполагает, что все ключевые точки на линии упорядочены по уменьшению дистанции до последней
    #  * ключевой точки. Перебирая их по порядку, находим первую попавшуюся точку, которая находится ближе к последней
    #  * точке на линии, чем волшебник. Это и будет следующей ключевой точкой.
    #  * <p>
    #  * Дополнительно проверяем, не находится ли волшебник достаточно близко к какой-либо из ключевых точек. Если это
    #  * так, то мы сразу возвращаем следующую ключевую точку.
    #  */
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

    # /**
    #  * Действие данного метода абсолютно идентично действию метода {@code get_next_waypoint}, если перевернуть массив
    #  * {@code waypoints}.
    #  */
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

    # /**
    #  * Простейший способ перемещения волшебника.
    #  */
    def go_to(self, point: Point2D, angle=None):
        # angle = self.me.get_angle_to(point.x, point.y)
        #
        # self._move.turn = angle
        #
        # if abs(angle) < self.game.staff_sector / 4.0:
        #     const_speed_koef = 1200
        #     self._move.speed = self.game.wizard_forward_speed * (1 if self.world.tick_index > 1200 else 0.5 )

        self._move.speed, self._move.strafe_speed, self._move.turn = self.map.get_optimal_move(point, angle)
        # speed_str = "{:.0f} {:.0f} {:.3f}".format(self.me.speed_x, self.me.speed_y, math.hypot(self.me.speed_x, self.me.speed_y))
        # print(self.world.tick_index, "move ", self.front_score, speed_str)


    # /**
    #  * Находим ближайшую цель для атаки, независимо от её типа и других характеристик.
    #  */
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
