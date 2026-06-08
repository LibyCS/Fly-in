from visualiser import Grid, Node
import math
from typing import cast
from collections.abc import Generator


class Pathfinding():
    def __init__(self, grid: Grid) -> None:
        """
        Sets needed variables from grid
        """
        self.start = grid.start
        self.end = grid.end
        self.grid = grid.grid
        self.drones = grid.drones
        self.timeline: dict[int, dict[Node, list[int]]] = {}

    def estimated_moves_to_goal(self, node: Node) -> int:
        """
        Calculates the distance based off the current nodes
        coords vs the goal coords using euclidian distance
        """
        h = round(math.sqrt((node.coords[0] - self.end.coords[0]) ** 2
                            + (node.coords[1] - self.end.coords[1]) ** 2))
        return h

    def add_cost_to_node(self, node: Node, parent: Node) -> None:
        """
        Finds the efficency of that node to get to it from start
        aswell as to get to goal
        """
        # parent.g + 1 for now need to make a working version
        node.g = parent.g + 1
        node.h = self.estimated_moves_to_goal(node)
        node.f = node.g + node.h

    def check_node_capacity(self, node: Node, turn: int) -> bool:
        if (turn in self.timeline.keys()
           and node in self.timeline[turn].keys()):
            if node.capacity <= len(self.timeline[turn][node]):
                return False
        return True

    def a_star(self) -> list[Node]:
        """
        Search algorithm that finds the best path to get
        from start to goal
        """
        open: list[Node] = []
        closed: list[Node] = []
        wait: dict[int, Node] = {}
        open.append(self.start)
        turn = 0
        while open:
            q = open[0]
            for node in open:
                if node.f < q.f:
                    q = node
            open.remove(q)
            turn += 1
            for child in q.children:
                if child not in closed:
                    child.parent = q
                if child == self.end:
                    return self.trace_path(wait)
                self.add_cost_to_node(child, q)
                if not self.check_node_capacity(child, turn):
                    continue
                if any(open_node.coords == child.coords
                       and open_node.f < child.f for open_node in open):
                    continue
                if any(closed_node.coords == child.coords
                       and closed_node.f < child.f for closed_node in closed):
                    continue
                else:
                    open.append(child)
            if not open:
                open.append(q)
                wait[turn] = q
            else:
                closed.append(q)
        raise ValueError("Error: Could not find goal")

    def trace_path(self, wait: dict[int, Node] | None = None) -> list[Node]:
        pathway = [self.end]
        node = self.end
        index = 1
        while node != self.start and index < 10:
            node = cast(Node, node.parent)
            pathway.append(node)
            index += 1
        pathway = list(reversed(pathway))
        if wait is not None:
            for index in wait.keys():
                pathway.insert(index, wait[index])
        print("Pathfinder:")
        print([node.name for node in pathway])
        return (pathway)

    def update_timeline(self, drone: int, path: list[Node]) -> None:
        turn = 0
        for node in path:
            if turn not in self.timeline.keys():
                self.timeline[turn] = {}
            if node not in self.timeline[turn].keys():
                self.timeline[turn][node] = []
            self.timeline[turn][node].append(drone)
            turn += 1

    def drone_allocation(self) -> None:
        drone = 1
        while drone <= self.drones:
            print("\ndrone", drone)
            self.update_timeline(drone, self.a_star())
            drone += 1

    def turn_generator(self) -> Generator[list[tuple[int, Node]]]:
        self.drone_allocation()
        turn = 1
        while turn in self.timeline.keys():
            drone_stat: list[tuple[int, Node]] = []
            for node in self.timeline[turn].keys():
                for drone in self.timeline[turn][node]:
                    if (node in self.timeline[turn - 1]
                       and drone in self.timeline[turn - 1][node]):
                        continue
                    drone_stat.append((drone, node))
            yield drone_stat
            turn += 1
