from enum import IntEnum
from typing import cast
from parser import DataDict, Hub, Keys
import time
import textwrap
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


class State(IntEnum):
    """
    Sets open and blocked states
    """
    OPEN = 0
    BLOCKED = 1


class Node():
    def __init__(self, name: str, hub_type: str, data: Hub) -> None:
        """
        Initialises node with these following variables.
        """
        self.name: str = name
        self.type: str = hub_type
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
        self.connection: dict[tuple[str, str], int] = data["connection"]
        self.state = State.BLOCKED


class Grid():
    def __init__(self, data: DataDict) -> None:
        """
        Creates an empty grid within row and columns limits
        and appends new default nodes to a list.
        """
        self.grid: list[Node] = []
        start = data[Keys.START_HUB.value]
        end = data[Keys.END_HUB.value]
        all_hubs = start | end | data[Keys.HUB.value]
        for name, hub in sorted(all_hubs.items(), key=lambda item:
                                (-item[1]["coords"][1],
                                 item[1]["coords"][0])):
            if name in start:
                hub_type = "start_hub"
                self.start = Node(name, hub_type, hub)
            elif name in end:
                hub_type = "end_hub"
                self.end = Node(name, hub_type, hub)
            else:
                hub_type = "hub"
            self.grid.append(Node(name, hub_type, hub))
        self.xlims = (min(map(lambda node: node.coords[0], self.grid)),
                      max(map(lambda node: node.coords[0], self.grid)))
        self.ylims = (min(map(lambda node: node.coords[1], self.grid)),
                      max(map(lambda node: node.coords[1], self.grid)))
        x_scale: int = 2
        y_scale: int = 1
        set_x: int = 1
        set_y: int = 1
        diff_x = self.xlims[1] - self.xlims[0]
        diff_y = self.ylims[1] - self.ylims[0]
        if diff_x >= 15:
            x_scale = diff_x
            set_x = round(diff_x / 10) * 5
        elif diff_x > 5:
            x_scale = 10
            set_x = 3
        if diff_y >= 15:
            y_scale = diff_y
            set_y = round(diff_y / 10) * 5
        elif diff_y > 5:
            y_scale = 10
            set_y = 3
        self.scale: list[int] = [x_scale, y_scale, set_x, set_y]

    def find_node(self, name: str) -> Node:
        """
        Finds node and returns node from grids
        """
        for node in self.grid:
            if node.name == name:
                return node
        raise ValueError("Error: Could not find node")

    def scaled(self, coords: tuple[int, int]) -> tuple[int, int]:
        return (coords[0] * self.scale[0], coords[1] * self.scale[1])

    def draw_arrow(self, node1: Node, node2: Node) -> None:
        start, end = map(self.scaled, [node1.coords, node2.coords])
        shrink: int = 20
        if self.scale[0] > 15:
            shrink = 5
        elif self.scale[0] > 5:
            shrink = 10
        plt.annotate("", xy=end, xytext=start,
                     arrowprops=dict(arrowstyle="->", shrinkA=shrink,
                                     shrinkB=shrink, color="grey",
                                     connectionstyle="arc3,rad=0.2"))

    def connections(self) -> None:
        visited: list[Node] = [self.start, self.end]
        queue: list[Node] = []
        for connect in self.start.connection.keys():
            child = self.find_node(connect[1])
            self.draw_arrow(self.start, child)
            queue.append(child)
            visited.append(child)
        while len(queue) > 0:
            current = queue[0]
            for relation_hubs in current.connection.keys():
                next_hub = self.find_node(relation_hubs[1])
                if next_hub == current:
                    continue
                self.draw_arrow(current, next_hub)
                if next_hub not in queue and next_hub not in visited:
                    queue.append(next_hub)
            queue.remove(current)
            visited.append(current)
        plt.savefig("layout.png")

    def visualiser(self) -> None:
        """
        prints the layout using terminal ascii
        """
        fig, axes = plt.subplots()
        scaler = self.scale
        axes.set_xlim((self.xlims[0] * scaler[0]) - scaler[2],
                      (self.xlims[1] * scaler[0]) + scaler[2])
        axes.set_ylim((self.ylims[0] * scaler[1]) - scaler[3],
                      (self.ylims[1] * scaler[1]) + scaler[3])
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        axes.set_axisbelow(True)
        plt.grid(True, color="lightgrey")
        axes.xaxis.set_major_locator(MultipleLocator(scaler[0]))
        axes.yaxis.set_major_locator(MultipleLocator(scaler[1]))
        for node in self.grid:
            font_colour = "white"
            x, y = self.scaled(node.coords)
            size: float = 1500
            fsize: float = 10
            if self.scale[0] >= 15:
                size = 200
                fsize = 2
            elif self.scale[0] > 5:
                size = 500
                fsize = 3
            if node.type == "start_hub" or node.type == "end_hub":
                size = size * 1.5
                fsize = fsize * 1.3
            if node.colour != "rainbow":
                axes.scatter(x, y, color=node.colour, s=size)
            else:
                cmap = plt.get_cmap("rainbow")
                axes.scatter(x, y, color=cmap(1), s=size)
            black_font = ["yellow", "cyan", "orange", "red"]
            if node.colour in black_font:
                font_colour = "black"
            wrap_name = "\n".join(textwrap.wrap(node.name, width=7))
            axes.text(x, y, wrap_name, ha="center", va="center",
                      color=font_colour, fontsize=fsize)
            plt.savefig("layout.png")
            time.sleep(0.2)
        self.connections()
