from __future__ import annotations
from typing import cast, Callable
from parser import DataDict, Hub, Keys
import time
import textwrap
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.text import Text
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Polygon


class Connection():
    """
    Creates a connection between 2 nodes with a capacity
    Used to make connection capacity and visualisation of the drone
    on the connection easier to parse and understand.
    """
    def __init__(self, connect1: Node, connect2: Node, capacity: int) -> None:
        """
        Sets the name of the connection to be the 2 nodes names combined
        and sets the capacity of the connection to be the capacity given
        """
        self.name = connect1.name + "-" + connect2.name
        self.connect1 = connect1.name
        self.connect2 = connect2.name
        self.capacity = capacity
        self.calculate_coords(connect1, connect2)

    def calculate_coords(self, connect1: Node, connect2: Node) -> None:
        """
        Calculates the coords of the connection to be the average of
        the 2 nodes coords, returning a tuple of x, y
        """
        x = (connect1.coords[0] + connect2.coords[0]) / 2
        y = (connect1.coords[1] + connect2.coords[1]) / 2
        self.coords = (x, y)


class Node():
    """
    Creates a node with a name, type, coords, zone, colour, capacity,
    connection and children.
    """
    def __init__(self, name: str, hub_type: str, data: Hub) -> None:
        """
        Initialises node with these following variables.
        """
        self.name: str = name
        self.type: str = hub_type
        self.coords: tuple[int, int] = data["coords"]
        self.zone: str = "normal"
        if "metadata" in data.keys() and "zone" in data["metadata"]:
            self.zone = cast(str, data["metadata"]["zone"])
        self.colour: (None | str) = None
        if "metadata" in data.keys() and "color" in data["metadata"]:
            self.colour = cast(str, data["metadata"]["color"])
        self.capacity: int = 500
        if "metadata" in data.keys() and "max_drones" in data["metadata"]:
            self.capacity = cast(int, data["metadata"]["max_drones"])
        self.old_connection = data["connection"]
        self.connection: list[Connection] = []
        self.children: list[Node] = []

    def connection_converter(self, find: Callable) -> None:
        """
        Converts the old connection dictionary to a list of Connection objects
        """
        for node1, node2 in self.old_connection.keys():
            new_connect = Connection(find(node1), find(node2),
                                     self.old_connection[(node1, node2)])
            self.connection.append(new_connect)


class Grid():
    """
    A class that creates a grid of nodes from the parsed data
    aswell as keeping track of the start, end, hub nodes,
    and the number of drones.
    """
    def __init__(self, data: DataDict) -> None:
        """
        Creates an empty grid within row and columns limits
        and appends new default nodes to a list.
        """
        self.grid: list[Node] = []
        self.start: Node
        self.end: Node
        self.create_grid(data)
        self.drones = data["nb_drones"]

    def create_grid(self, data: DataDict) -> None:
        """
        Creates a grid of nodes from the parsed data
        """
        start = data[Keys.START_HUB.value]
        end = data[Keys.END_HUB.value]
        all_hubs = start | end | data[Keys.HUB.value]
        for name, hub in sorted(all_hubs.items(), key=lambda item:
                                (-item[1]["coords"][1],
                                 item[1]["coords"][0])):
            if name in start:
                hub_type = "start_hub"
                new_node = self.start = Node(name, hub_type, hub)
            elif name in end:
                hub_type = "end_hub"
                new_node = self.end = Node(name, hub_type, hub)
            else:
                hub_type = "hub"
                new_node = Node(name, hub_type, hub)
            self.grid.append(new_node)
        for node in self.grid:
            node.connection_converter(self.find_node)
        self.add_child_parent_nodes()

    def find_node(self, name: str) -> Node:
        """
        Finds node and returns node from grids
        """
        for node in self.grid:
            if node.name == name:
                return node
        raise ValueError("Error: Could not find node")

    def add_child_parent_nodes(self) -> None:
        """
        Finds the nodes and adds them to a list called children
        to that current node, cycles through all nodes that can be found
        from start
        """
        completed: list[Node] = []
        queue: list[Node] = []
        queue.append(self.start)
        while queue:
            curr_node = queue[0]
            for connection in curr_node.connection:
                if connection.connect1 != curr_node.name:
                    target_node = self.find_node(connection.connect1)
                else:
                    target_node = self.find_node(connection.connect2)
                curr_node.children.append(target_node)
                if target_node not in completed:
                    queue.append(target_node)
            queue.remove(curr_node)
            completed.append(curr_node)


class GridVisualiser():
    """
    A class that visualises the grid of nodes and connections
    using matplotlib, and saves the visualisation as an image.
    """
    def __init__(self, layout: Grid) -> None:
        """
        Sets variables needed to create the visualiser
        """
        self.grid = layout.grid
        self.start = layout.start
        self.end = layout.end
        self.find_node = layout.find_node
        self.drones = layout.drones
        self.create_boundaries()

    def create_boundaries(self) -> None:
        """
        Creates boundaries for the graph
        """
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

    def scaled(self, coords: tuple[int, int]) -> tuple[int, int]:
        """
        Scales the coords so that it looks ok
        """
        return (coords[0] * self.scale[0], coords[1] * self.scale[1])

    def draw_arrow(self, node1: Node, node2: Node) -> None:
        """
        draws the arrow appropriate to the scale between 2 nodes
        """
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
        """
        Goes through each node mapping out their parent connections
        """
        visited: list[Node] = [self.start, self.end]
        queue: list[Node] = []
        for connect in self.start.connection:
            child = self.find_node(connect.connect2)
            self.draw_arrow(self.start, child)
            queue.append(child)
            visited.append(child)
        while len(queue) > 0:
            current = queue[0]
            for relation_hubs in current.connection:
                next_hub = self.find_node(relation_hubs.connect2)
                if next_hub == current:
                    continue
                self.draw_arrow(current, next_hub)
                if next_hub not in queue and next_hub not in visited:
                    queue.append(next_hub)
            queue.remove(current)
            visited.append(current)
        plt.savefig("visualiser.png")

    def visualise_layout(self) -> tuple[Axes, list[int]]:
        """
        prints the layout using terminal ascii
        """
        _, axes = plt.subplots()
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
                fsize = 5
            if node.type == "start_hub" or node.type == "end_hub":
                size = size * 1.5
                fsize = fsize * 2
            if node.colour != "rainbow":
                axes.scatter(x, y, color=node.colour, s=size)
            else:
                rainbow = ["red", "orange", "yellow", "green", "blue",
                           "indigo", "violet"]
                increments = size / len(rainbow)
                new_size = size
                for colour in rainbow:
                    axes.scatter(x, y, color=colour, s=new_size)
                    new_size -= increments
            black_font = ["yellow", "cyan", "orange", "red"]
            if node.colour in black_font:
                font_colour = "black"
            wrap_name = "\n".join(textwrap.wrap(node.name, width=7))
            axes.text(x, y, wrap_name, ha="center", va="center",
                      color=font_colour, fontsize=fsize)
            plt.savefig("visualiser.png")
            time.sleep(0.3)
        self.connections()
        return axes, self.scale


class DroneVisualiser():
    """
    A class that visualises the drones moving through the
    grid of nodes and connections
    using matplotlib, and saves the visualisation as an image.
    """
    def __init__(self, layout: Grid, axes: Axes, scale: list[int]) -> None:
        """
        Sets variables needed to create the visualiser
        imports pathfinding to avoid circular import issues
        and creates a turnorder generator to get the timeline of
        drones at each turn.
        """
        from pathfinding import Pathfinding
        self.turnorder_gen = Pathfinding(layout).turn_generator()
        self.nb_drones = layout.drones
        self.axes = axes
        self.scale = scale
        self.start_x = layout.start.coords[0] * scale[0]
        self.start_y = layout.start.coords[1] * scale[1]
        self.time = 1

    def update_drone_coords(self, coords: tuple[int, int] | tuple[float, float]
                            ) -> list[tuple[float, float]]:
        """
        Takes in the drone coords and adding the padding
        to create a diamond shape to be used to visualise the drone
        on the grid.
        Returns a list of tuples of the diamond shape coords
        to be used to create a Polygon object.
        """
        x = coords[0] * self.scale[0]
        y = coords[1] * self.scale[1]
        size_x = size_y = 0.2
        if self.scale[0] >= 10:
            size_x = 2
        if self.scale[0] >= 15:
            size_x = 5
        diamond = [(x, y + size_y),
                   (x + size_x, y),
                   (x, y - size_y),
                   (x - size_x, y)]
        return diamond

    def create_drones(self) -> None:
        """
        Creates the drones on the grid at the start hub coords
        and saves the visualisation as an image.
        """
        starting_drone = self.update_drone_coords((self.start_x,
                                                   self.start_y))
        self.drones: list[tuple[Polygon, Text]] = []
        for drone in range(0, self.nb_drones):
            template_drone = Polygon(starting_drone, color="grey",
                                     zorder=(10 + drone))
            self.axes.add_patch(template_drone)
            label = self.axes.text(self.start_x, self.start_y,
                                   "D" + str(drone + 1), ha="center",
                                   va="center", zorder=(11 + drone))
            self.drones.append((template_drone, label))
        plt.savefig("visualiser.png")
        time.sleep(self.time)

    def move_drone(self, drone_stats: tuple[Polygon, Text],
                   node: Node | Connection) -> None:
        """
        Moves the drone to the new node coords and updates the label
        so that the label moves with the drone,
        saves the visualisation as an image.
        """
        drone, label = drone_stats
        scaled_coords = (node.coords[0] * self.scale[0],
                         node.coords[1] * self.scale[1])
        print(f"{label.get_text()}-{node.name} ", end="")
        drone.set_xy(self.update_drone_coords(node.coords))
        label.set_position(scaled_coords)
        plt.savefig("visualiser.png")

    def visualise(self) -> None:
        """
        This is the main visualisation function that creates the drones
        and moves them through the grid of nodes and connections according
        to the timeline generated by the turnorder generator.
        It moves each drone to the next node or connection for each turn,
        and saves the visualisation as an image after each move.
        """
        self.create_drones()
        while True:
            any_moved = False
            try:
                incoming_drone = next(self.turnorder_gen)
                for drone, node in incoming_drone:
                    any_moved = True
                    self.move_drone(self.drones[drone - 1], node)
                    time.sleep(0.5)
                if any_moved is True:
                    print()
                time.sleep(self.time)
            except StopIteration:
                break
