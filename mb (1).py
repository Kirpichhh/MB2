from abc import ABC, abstractmethod
from typing import Callable
from enum import Enum
from random import randint
import sys

class EErrors(Enum):
    MAX_TRIES = "MAX TRIES REACHED: may be impossible to place ships"

class ERevealSingals(Enum):
    EMPTY = (-1, 0)
    DESTROYED = (-2, 0)
    CONTINUE = (-3, 0)
    DIED = (-4, 0)

class ESymbols(Enum):
    UNKNOWN = '#'
    EMPTY = '.'
    SHIP = 'X'
    DESTROYED_SHIP = 'O'
    MINE = '*'

class IPlaceable(ABC):
    @property
    @abstractmethod
    def _x_pos(self):
        pass

    @property
    @abstractmethod
    def _y_pos(self):
        pass

    @abstractmethod
    def place(x_pos : int, y_pos : int):
        pass

class CShip(IPlaceable):
    def __init__(self, x_len : int, y_len : int):
        self.x_len = x_len
        self.y_len = y_len

        self.x_pos = 0
        self.y_pos = 0
        self.cells = set()
        self.region = set()

    def _x_pos(self):
        return self._x_pos
    def get_x_pos(self):
        return self._x_pose
    def set_x_pos(self, x_pos : int):
        self._x_pos = x_pos

    def _y_pos(self):
        return self._y_pos
    def get_y_pos(self):
        return self._y_pos
    def set_y_pos(self, y_pos : int):
        self._y_pos = y_pos

    def place(self, x_pos : int, y_pos : int):
        self.set_x_pos(x_pos)
        self.set_y_pos(y_pos)
        self.cells = set()
        self.region = set()
        for x in range(abs(self.x_len)):
            for y in range(abs(self.y_len)):
                self.cells.add((self._x_pos + x * int(abs(self.x_len) / self.x_len),
                                self._y_pos + y * int(abs(self.y_len) / self.y_len)))
        self.region = set()
        for x in (1, 0, -1):
            for y in (1, 0, -1):
                self.region = self.region.union(set([(c[0] + x, c[1] + y) for c in self.cells]))

    def rotate(self, direction : int):
        tmp = self.x_len
        if direction == 0:
            self.x_len = -self.y_len
            self.y_len = tmp
        elif direction == 1:
            self.x_len = self.y_len
            self.y_len = -tmp

class CMine(IPlaceable):
    def __init__(self, x_pos : int, y_pos : int):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def _x_pos(self):
        return self._x_pos
    def get_x_pos(self):
        return self._x_pos
    def set_x_pos(self, x_pos : int):
        self._x_pos = x_pos

    def _y_pos(self):
        return self._y_pos
    def get_y_pos(self):
        return self._y_pos
    def set_y_pos(self, y_pos : int):
        self._y_pos = y_pos

    def place(self, x_pos : int, y_pos : int):
        self.set_x_pos(x_pos)
        self.set_y_pos(y_pos)

class EShipConfigurations(Enum):
    DEFAULT = [ CShip(4, 1),
                CShip(3, 1), CShip(3, 1),
                CShip(2, 1), CShip(2, 1), CShip(2, 1),
                CShip(1, 1), CShip(1, 1), CShip(1, 1), CShip(1, 1)
                ]

class ACBasePlayer(ABC):
    @abstractmethod
    def makeShot(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def receiveShot(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def _reveal(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def revealEnemyField(self, x : int, y : int, symbol : ESymbols):
        pass

    @abstractmethod
    def enqueueShip(self, cell_pos : tuple[int, int]):
        pass

class ACShootStrategy(ABC):

    def __init__(self, enemy_field : list[list[str]], revealed_ships_queue : list[tuple[int, int]]):
        self._enemy_field = enemy_field
        self._x_size = len(enemy_field[0])
        self._y_size = len(enemy_field)
        self._revealed_ships_queue = revealed_ships_queue

    @abstractmethod
    def shoot(self) -> tuple[int, int]:
        pass

class CRandomShootStrategy(ACShootStrategy):

    def shoot(self) -> tuple[int, int]:
        print(self._revealed_ships_queue)
        if len(self._revealed_ships_queue) > 0:
            return self._revealed_ships_queue.pop(0)
        x, y = self.__tryShoot()
        while self._enemy_field[y][x] != ESymbols.UNKNOWN.value:
            x, y =  self.__tryShoot()
        return (x, y)
    
    def __tryShoot(self) -> tuple[int, int]:
        return (randint(0, self._x_size - 1), randint(0, self._y_size - 1))

class ACPlaceStrategy(ABC):

    def __init__(self, field : list[list[str]], ships : list[CShip], mines : list[tuple[int, int]], mines_cnt : int):
        self._field = field
        self._x_size = len(field[0])
        self._y_size = len(field)
        self._ships = ships
        self._mines = mines
        self._mines_cnt = mines_cnt

    @abstractmethod
    def place(self) -> list[list[str]]:
        pass

    def _isOccupied(self, ship_to_check : CShip) -> bool:
        for ship in self._ships:
            if ship == ship_to_check:
                continue
            if (len(ship_to_check.region - ship.cells) != len(ship_to_check.region)):
                return True
        return False

    def _isOutOfBounds(self, ship_to_check : CShip) -> bool:
        for cell in ship_to_check.cells:
            if (cell[0] >= self._x_size  or cell[0] < 0 or cell[1] >= self._y_size  or cell[1] < 0):
                return True
        return False

class CRandomPlaceStrategy(ACPlaceStrategy):
    MAX_TRIES = int(1e5)

    def place(self) -> list[list[str]]:
        for ship in self._ships:
            self.__tryPlaceShip(ship)
            tries = 0
            while self._isOccupied(ship) or self._isOutOfBounds(ship):
                self.__tryPlaceShip(ship)
                tries += 1
            if tries > self.MAX_TRIES:
                raise Exception(EErrors.MAX_TRIES.value)
            for cell in ship.cells:
                self._field[cell[1]][cell[0]] = ESymbols.SHIP.value
        placed_mines = 0
        tries = 0
        while placed_mines < self._mines_cnt:
            m = CMine(0 , 0)
            self.__tryPlaceMine(m)
            if self._field[m.get_x_pos()][m.get_y_pos()] == ESymbols.EMPTY.value:
                self._field[m.get_x_pos()][m.get_y_pos()] = ESymbols.MINE.value
                self._mines.append(m)
                placed_mines += 1
            else:
                tries += 1
            if tries > self.MAX_TRIES:
                raise Exception(EErrors.MAX_TRIES.value)
        return (self._field, self._mines)

    def __tryPlaceShip(self, ship : CShip):
        ship.rotate(randint(0, 1))
        ship.place(randint(0, self._x_size - 1), randint(0, self._y_size - 1))

    def __tryPlaceMine(self, mine : CMine):
        mine.place(randint(0, self._x_size - 1), randint(0, self._y_size - 1))

class ACReavealStrategy(ABC):
    
    def __init__(self, field):
        self._field = field

    @abstractmethod
    def reveal(self) -> tuple[int, int]:
        pass

class CRandomRevealStrategy(ACReavealStrategy):
    
    def reveal(self) -> tuple[int, int]:
        ship_cells = []
        for y in range(len(self._field)):
            for x in range(len(self._field[y])):
                if self._field[y][x] == ESymbols.SHIP.value:
                    ship_cells.append((x, y))
        return ship_cells[randint(0, len(ship_cells) - 1)]

class CGame:
    def __init__(self, x_size : int, y_size : int, ships : list[CShip], mines_cnt : int,
                place_strategy = CRandomPlaceStrategy, 
                shoot_strategy = CRandomShootStrategy,
                reveal_strategy = CRandomRevealStrategy):
        self.__players = (  CHumanPlayer(x_size, y_size, ships, mines_cnt),
                            CAIPlayer(x_size, y_size, ships, mines_cnt, 
                                                    place_strategy,
                                                    shoot_strategy,
                                                    reveal_strategy))
        self.__is_ai_turn = False
    
    def gameloop(self) -> bool:
        while True:
            cur_player = self.__players[self.__is_ai_turn]
            other_player = self.__players[not self.__is_ai_turn]
            x, y = cur_player.makeShot()
            print("Player " + str(int(self.__is_ai_turn)) + " makes a shot and ...")
            signal = other_player.receiveShot(x, y)
            if signal == ERevealSingals.CONTINUE.value:
                print("A ship was shot!")
                cur_player.revealEnemyField(x, y, ESymbols.DESTROYED_SHIP.value)
            elif signal == ERevealSingals.DIED.value:
                print("A ship was shot!")
                if self.__is_ai_turn:
                    print("AI WON!")
                else:
                    print("PLAYER WON!")
                return True
            else:
                self.__is_ai_turn = not self.__is_ai_turn
                if signal == ERevealSingals.EMPTY.value:
                    print("Misses!")
                    cur_player.revealEnemyField(x, y, ESymbols.EMPTY.value)
                elif signal == ERevealSingals.DESTROYED.value:
                    print("Misses!")
                    cur_player.revealEnemyField(x, y, ESymbols.DESTROYED_SHIP.value)
                else:
                    print("A mine was shot!")
                    cur_player.revealEnemyField(x, y, ESymbols.EMPTY.value)
                    other_player.enqueueShip(signal)           

            

class CHumanPlayer(ACBasePlayer):

    def __init__(self, x_size : int, y_size : int, 
                ships : list[CShip],
                mines_cnt : int):
        self.__ships = ships
        self.__hp = 0
        for ship in self.__ships:
            self.__hp += ship.x_len * ship.y_len

        empty_field = [[ESymbols.EMPTY.value for i in range(x_size)] for j in range(y_size)]
        mines = []
        self.__my_field, self.__mines = CRandomPlaceStrategy(empty_field, ships, mines, mines_cnt).place()

        self.__enemy_field = [[ESymbols.UNKNOWN.value for i in range(x_size)] for j in range(y_size)]

    def makeShot(self) -> tuple[int, int]:
        self.__draw()
        print("Make a shot...")
        print("Input x coord:")
        x = int(input())
        print("Input y coord:")
        y = int(input())
        return (x, y)

    def receiveShot(self, x : int, y : int) -> tuple[int, int]:
        if self.__my_field[y][x] == ESymbols.SHIP.value:
            self.__my_field[y][x] = ESymbols.DESTROYED_SHIP.value
            self.__hp -= 1
            if self.__hp == 0:
                return ERevealSingals.DIED.value
            else:
                return ERevealSingals.CONTINUE.value
        elif self.__my_field[y][x] == ESymbols.MINE.value:
            self.__my_field[y][x] = ESymbols.EMPTY.value
            return self._reveal()
        self.__draw()
        return ERevealSingals.EMPTY.value

    def _reveal(self) -> tuple[int, int]:
        print("Your mine was hit!")
        return CRandomRevealStrategy(self.__my_field).reveal()

    def revealEnemyField(self, x : int, y : int, symbol : ESymbols):
        self.__enemy_field[y][x] = symbol

    def enqueueShip(self, cell_pos : tuple[int, int]):
        self.revealEnemyField(cell_pos[0], cell_pos[1], ESymbols.SHIP.value)

    def __draw(self):
        sys.stdout.flush()
        num = " "
        for i in range(len(self.__my_field)):
            num += str(i)
        print(num)
        for i in range(len(self.__my_field)):
            print(i, end='')
            for j in range(len(self.__my_field[0])):
                print(self.__my_field[i][j], end='')
            print()

        num = " "
        for i in range(len(self.__enemy_field)):
            num += str(i)
        print(num)
        for i in range(len(self.__enemy_field)):
            print(i, end='')
            for j in range(len(self.__enemy_field[0])):
                print(self.__enemy_field[i][j], end='')
            print()

class CAIPlayer(ACBasePlayer):

    def __init__(self, x_size : int, y_size : int, 
                ships : list[CShip],
                mines_cnt : int,
                place_strategy : Callable,
                shoot_strategy : Callable,
                reveal_strategy : Callable):

        self.__x_size = x_size
        self.__y_size = y_size

        empty_field = [[ESymbols.EMPTY.value for i in range(x_size)] for j in range(y_size)]
        mines = []
        self.__ships = ships
        self.__placer = place_strategy(empty_field, ships, mines, mines_cnt)
        self.__my_field, self.__mines = self.__placer.place()

        self.__enemy_field = [[ESymbols.UNKNOWN.value for i in range(x_size)] for j in range(y_size)]
        self.__revealed_ships_queue = []
        self.__shooter = shoot_strategy(self.__enemy_field, self.__revealed_ships_queue)

        self.__revealer = reveal_strategy(self.__my_field)

        self.__hp = 0
        for ship in self.__ships:
            self.__hp += ship.x_len * ship.y_len

    def makeShot(self) -> tuple[int, int]:
        print("AIS fiels")
        num = " "
        for i in range(len(self.__enemy_field)):
            num += str(i)
        print(num)
        for i in range(len(self.__enemy_field)):
            print(i, end='')
            for j in range(len(self.__enemy_field[0])):
                print(self.__enemy_field[i][j], end='')
            print()
        return self.__shooter.shoot()

    def receiveShot(self, x : int, y : int) -> tuple[int, int]:
        if self.__my_field[y][x] == ESymbols.SHIP.value:
            self.__my_field[y][x] = ESymbols.DESTROYED_SHIP.value
            self.__hp -= 1
            if self.__hp == 0:
                return ERevealSingals.DIED.value
            else:
                return ERevealSingals.CONTINUE.value
        elif self.__my_field[y][x] == ESymbols.MINE.value:
            self.__my_field[y][x] = ESymbols.EMPTY.value
            return self._reveal()
        return ERevealSingals.EMPTY.value

    def revealEnemyField(self, x : int, y : int, symbol : ESymbols):
        self.__enemy_field[y][x] = symbol

    def _reveal(self) -> tuple[int, int]:
        return self.__revealer.reveal()
        
    def enqueueShip(self, ship_cell : tuple[int, int]):
        self.__revealed_ships_queue.append(ship_cell)
        self.revealEnemyField(ship_cell[0], ship_cell[1], ESymbols.SHIP.value)

print(CGame(2, 2, [CShip(1, 1)], 3).gameloop())