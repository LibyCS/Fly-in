from enum import IntEnum
from typing import Generator, cast
from parser import DataDict, Hub, Keys, Colour
import matplotlib as plot


class State(IntEnum):
    """
    Sets open and blocked states
    """
    OPEN = 0
    BLOCKED = 1


class Node():
    def __init__(self, name: str, data: Hub) -> None:
        """
        Initialises node with these following variables.
        """
        self.name = name
        self.coords: tuple[int, int] = data["coords"]
        self.zone: str = "normal"
        if "metatdata" in data.keys() and "zone" in data["metadata"]:
            self.zone = cast(str, data["metadata"]["zone"])
        self.colour: (None | str) = None
        if "metadata" in data.keys() and "color" in data["metadata"]:
            self.colour = cast(str, data["metadata"]["color"])
        self.capacity: int = 1
        if "metadata" in data.keys() and "max_drones" in data["metadata"]:
            self.capacity = cast(int, data["metadata"]["max_drones"])
        self.connection: dict[str, int] = data["connection"]
        self.state = State.BLOCKED


class Grid():
    def __init__(self, data: DataDict) -> None:
        """
        Creates an empty grid within row and columns limits
        and appends new default nodes to a list.
        """
        self.grid: list[Node] = []
        self.start = data[Keys.START_HUB.value]
        self.end = data[Keys.END_HUB.value]
        all_hubs = self.start | self.end | data[Keys.HUB.value]
        for name, hub in sorted(all_hubs.items(), key=lambda item:
                                (-item[1]["coords"][1],
                                 item[1]["coords"][0])):
            self.grid.append(Node(name, hub))

    def find_node(self, name: str) -> Node:
        """
        Finds node and returns node from grids
        """
        for node in self.grid:
            if node.name == name:
                return node
        raise ValueError("Error: Could not find node")


    def row_slice(self) -> Generator[list[Node], None, None]:
        """
        yields the row from grid
        """
        max_x = max(node.coords[0] for node in self.grid)
        slice: list[Node] = []
        for node in self.grid:
            slice.append(node)
            if node.coords[0] == max_x:
                yield slice
                slice = []

    def visualiser(self) -> None:
        """
        prints the layout using terminal ascii
        """








"""         row_gen = self.row_slice()
        for slice in row_gen:
            for node in slice:
                print("+", end="")
                if node.walls[Direction.NORTH.value] == State.CLOSED:
                    char = "--"
                else:
                    char = "  "
                print(char, end="")
            print("+")
            for node in slice:
                if node.walls[Direction.WEST.value] == State.CLOSED:
                    char = "|"
                else:
                    char = " "
                print(char, end="")
                if node.colour is None:
                    char = "  "
                else:
                    char = Colour.get_ansi(node.colour)
                print(char, end="")
            if slice[-1].walls[Direction.EAST.value] == State.CLOSED:
                print("|")
            prev = slice
            for node in prev:
                print("+", end="")
                if node.walls[Direction.SOUTH.value] is State.CLOSED:
                    print("--", end="")
                else:
                    print("  ", end="")
            print("+") """
