from enum import Enum
from typing import Generator


class State(Enum):
    """
    Sets open and close states
    """
    OPEN = 0
    CLOSED = 1


class Direction(Enum):
    """
    Sets directions to a value
    """
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


class Colour(Enum):
    """
    Sets colour to their respective strings
    """
    GREEN = "  \033[42m"
    YELLOW = "  \033[43m"
    RED = "  \033[41m"
    BLUE = "  \033[44m"
    GREY = "  \033[100m"
    END = "  \033[0m"


class Cell():
    def __init__(self, x, y) -> None:
        """
        Initialises cell with these following variables.
        """
        self.coords: list[int, int] = [x, y]
        self.walls: list[int] = [State.CLOSED] * 4
        self.zone: str = "normal"
        self.colour: (None | Colour) = None
        self.capacity: int = 1


class grid():
    def __init__(self, row_limits: list, col_limits: list) -> None:
        """
        Creates an empty grid within row and columns limits
        and appends new default cells to a list.
        """
        self.grid: dict[int, list[int, int]]= {}
        if row_limits[1] > 0:
            row_limits[1] += 1
        else:
            row_limits[1] -= 1
        if col_limits[1] > 0:
            col_limits[1] += 1
        else:
            col_limits[1] -= 1
        for y in range(row_limits[0], row_limits[1]):
            for x in range(col_limits[0], col_limits[1]):
                self.grid[(x, y)] = Cell(x, y)


    def row_slice(self) -> Generator[list[Cell], None, None]:
        """
        yields the row from grid
        """
        max_x = max(cell.coords[0] for cell in self.grid.values())
        slice: list[Cell] = []
        for cell in self.grid.values():
            if cell.coords[0] != max_x:
                slice.append(cell)
            else:
                yield slice
                slice = []


    def visualiser(self):
        """
        prints the layout using terminal ascii
        """
        try:
            max_x = max(cell.coords[0] for cell in self.grid.values())
            min_x = min(cell.coords[0] for cell in self.grid.values())
        except ValueError:
            print("Empty")
            max_x = 0
        row_gen = self.row_slice()
        for slice in row_gen:
            for cell in slice:
                print("+", end="")
                if cell.walls[Direction.NORTH.value] == State.CLOSED:
                    char = "--"
                else:
                    char = "  "
                print(char, end="")
            print("+")
            for cell in slice:
                if cell.walls[Direction.WEST.value] == State.CLOSED:
                    char = "|"
                else:
                    char = " "
                print(char, end="")
                if cell.colour == None:
                    char = "  "
                else:
                    char = cell.colour + Colour.END
                print(char, end="")
            if slice[-1].walls[Direction.EAST.value] == State.CLOSED:
                print("|")
            prev = slice
        for cell in prev:
            print("+", end="")
            if cell.walls[Direction.SOUTH.value] is State.CLOSED:
                print("--", end="")
            else:
                print("  ", end="")
        print("+")