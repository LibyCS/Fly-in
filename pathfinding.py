from visualiser import Grid, Node
import math
from typing import cast
from collections.abc import Generator

class AStarStates():
    def __init__(self, timeline: dict[int, dict[Node, list[int]]], end: Node
                 ) -> None:
        self.end: Node = end
        self.open: list[Node] = []
        self.closed: list[Node] = []
        self.reservation: dict[tuple[Node, int]] = {}
        if timeline:
            self.convert_timeline_to_reservation(timeline)
        self.f: dict[str, int] = {}
        self.h: dict[str, int] = {}
        self.g: dict[str, int] = {}
        self.parent: dict[tuple[Node, int], tuple[Node, int]] = {}

    def convert_timeline_to_reservation(self, timeline: dict[int, dict[Node, list[int]]]
                                        ) -> None:
        for turn in timeline.keys():
            for node in timeline[turn]:
                self.reservation[(node, turn)] = len(timeline[turn][node])

    def find_best_node_f(self) -> Node | None:
        if not self.open:
            return None
        lowest_f = self.open[0]
        for node in self.open[1:]:
            if self.f[node.name] < self.f[lowest_f.name]:
                lowest_f = node
        if (self.end.name in self.f.keys()
           and self.f[self.end.name] == self.f[lowest_f.name]):
            lowest_f = self.end
        self.open.remove(lowest_f)
        return lowest_f

    def estimated_moves_to_goal(self, node: Node) -> int:
        """
        Calculates the distance based off the current nodes
        coords vs the goal coords using euclidian distance
        """
        h = round(math.sqrt((node.coords[0] - self.end.coords[0]) ** 2
                            + (node.coords[1] - self.end.coords[1]) ** 2))
        return h

    def update_fgh_values(self, node: Node, parent: Node | None = None
                          ) -> None:
        """
        Finds the efficency of that node to get to it from start
        aswell as to get to goal
        """
        # parent.g + 1 for now need to make a working version
        if parent is not None:
            self.g[node.name] = g = self.g[parent.name] + 1
        else:
            self.g[node.name] = g = 0
        self.h[node.name] = h = self.estimated_moves_to_goal(node)
        self.f[node.name] = g + h

    def check_node_capacity(self, node: Node, arrival: int) -> bool:
        if ((node, arrival) in self.reservation
           and self.reservation[(node, arrival)]) == node.capacity:
            return False
        return True


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

    def a_star(self) -> list[Node]:
        """
        Search algorithm that finds the best path to get
        from start to goal
        """
        state = AStarStates(self.timeline, self.end)
        state.update_fgh_values(self.start)
        state.open.append(self.start)
        turn = 0
        while state.open:
            q = state.find_best_node_f()
            print(q.name, "is the best node in the list")
            if q.name == self.end.name:
                return self.trace_path(state.parent)
            for child in q.children:
                state.update_fgh_values(child, q)
                if not state.check_node_capacity(child, turn + 1):
                    print(child.name, "Capacity is full")
                    continue
                if any(node.name == child.name
                       and state.g[node.name] <= state.g[child.name] for node in state.open):
                    continue
                if any(node.name == child.name
                       and state.g[node.name] <= state.g[child.name] for node in state.closed):
                    continue
                else:
                    print(child.name, turn + 1, q.name, turn)
                    state.parent[(child, turn + 1)] = (q, turn)
                    print("adding ", child.name)
                    state.open.append(child)
                state.closed.append(q)
            turn += 1
        print(turn)
        raise ValueError("Error: Could not find goal")

    def trace_path(self, parent_list: dict[tuple[Node, int], tuple[Node, int]]) -> list[Node]:
        pathway = []
        node = self.end
        for node, turn in parent_list.keys():
            if node.name == self.end.name:
                pathway.append(node)
                child_node = node
                child_turn = turn
                child = (child_node, child_turn)
        while child in parent_list.keys():
            parent = parent_list[child]
            for i in range(parent[1], child[1]):
                pathway.append(parent[0])
                i += 1
            child = parent
        pathway = list(reversed(pathway))
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
