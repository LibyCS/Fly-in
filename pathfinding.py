from visualiser import Grid, Node, Connection
import math
from collections.abc import Generator
from dataclasses import dataclass


@dataclass
class NodeState():
    node: Node
    turn: int = 0
    end: Node | None = None
    f: int = 0
    h: int = 0
    g: int = 0

    def update_fgh_values(self, hops: dict[Node, int], parent: NodeState | None = None
                          ) -> None:
        """
        Finds the efficency of that node to get to it from start
        aswell as to get to goal
        """
        if self.node.zone == "priority":
            weight = 0.8
        elif self.node.zone == "resticted":
            weight = 3
        else:
            weight = 1
        if parent is not None:
            self.g = parent.g + weight
        else:
            self.g = 0
        print(self.node.name)
        self.h = hops[self.node]
        self.f = self.g + self.h


class AStarStates():
    def __init__(self, timeline: dict[int, dict[Node | Connection, list[int]]],
                 connect: dict[tuple[Connection, int], int], end: Node
                 ) -> None:
        self.end: Node = end
        self.open: list[NodeState] = []
        self.closed: list[NodeState] = []
        self.node_reserve: dict[tuple[Node, int], int] = {}
        self.connect_reserve: dict[tuple[Connection, int], int] = connect
        if timeline:
            self.timeline_to_reserve(timeline)
        self.parent: dict[tuple[Node, int], tuple[Node, int]] = {}

    def timeline_to_reserve(self, timeline: dict[int, dict[Node | Connection,
                                                           list[int]]]
                            ) -> None:
        for turn in timeline.keys():
            for node in timeline[turn]:
                if isinstance(node, Connection):
                    connect = node
                    self.connect_reserve[(connect, turn)
                                         ] = len(timeline[turn][connect])
                else:
                    self.node_reserve[(node, turn)] = len(timeline[turn][node])

    def find_best_node_f(self) -> NodeState | None:
        if not self.open:
            return None
        if not self.open:
            raise ValueError("Lost a value")
        nodes = self.open
        lowest_f = nodes[0]
        for node in nodes[1:]:
            if node.f < lowest_f.f:
                lowest_f = node
            if (node.f == lowest_f.f and node.g < lowest_f.g):
                lowest_f = node
        for node in self.open:
            if self.end == node.node and node.f == lowest_f.f:
                lowest_f = node
        self.open.remove(lowest_f)
        return (lowest_f)

    def check_node_capacity(self, node_state: NodeState) -> bool:
        node = node_state.node
        turn = node_state.turn
        if ((node, turn) in self.node_reserve
           and self.node_reserve[(node, turn)]) == node.capacity:
            print(f"{node.name} has reached capacity")
            return False
        if (node, turn) in self.node_reserve:
            print(node.name, " has", self.node_reserve[(node, turn)], "drones")
        else:
            print(node.name, "has no drones")
        return True

    @staticmethod
    def find_shared_connect(src: Node, dest: Node) -> Connection | None:
        for connect in src.connection:
            if (connect.connect1 == dest.name
               or connect.connect2 == dest.name):
                return connect
        return None

    def check_connect_capacity(self, src: NodeState, dest: NodeState) -> bool:
        print(src.node.name, dest.node.name)
        connect = self.find_shared_connect(src.node, dest.node)
        if connect is None:
            raise ValueError("Error: Could not find shared connetion")
        if (dest.node.zone == "restricted"
           and (connect, dest.turn - 1) in self.connect_reserve.keys()):
            print("found restricted")
            if self.connect_reserve[(connect, dest.turn - 1)
                                    ] == connect.capacity:
                print("Found restircted but over capacity for link")
                return False
        if (connect, dest.turn) in self.connect_reserve.keys():
            print(self.connect_reserve[(connect,dest.turn)])
            print("Found a hit")
            if self.connect_reserve[(connect, dest.turn)] == connect.capacity:
                print("Not restircted but capcity for link is full")
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
        self.find_node = grid.find_node
        self.drones = grid.drones
        self.timeline: dict[int, dict[Node | Connection, list[int]]] = {}
        self.shared_connection = AStarStates.find_shared_connect
        self.reserve_connects: dict[tuple[Connection, int], int] = {}
        self.hops = self.find_hops_to_goal()

    def find_hops_to_goal(self):
        hops: dict[Node, int] = {}
        hops[self.end] = 0
        queue: list[Node] = []
        queue.append(self.end)
        while queue:
            node = queue[0]
            queue.remove(node)
            for connects in node.connection:
                if connects.connect1 != node.name:
                    connected_node = connects.connect1
                else:
                    connected_node = connects.connect2
                new_node = self.find_node(connected_node)
                if new_node not in hops.keys():
                    weight = 1
                    if node.zone == "restricted":
                        weight = 3
                    elif node.zone == "priority":
                        weight = 0.8
                    hops[new_node] = hops[node] + weight
                    queue.append(new_node)
        return hops


    def a_star(self) -> list[tuple[Node | Connection, int]]:
        """
        Search algorithm that finds the best path to get
        from start to goal
        """
        state = AStarStates(self.timeline, self.reserve_connects, self.end)
        start = NodeState(node=self.start, turn=0, end=self.end)
        start.update_fgh_values(self.hops)
        state.open.append(start)
        while state.open:
            best_found = state.find_best_node_f()
            if best_found is None:
                break
            q = best_found
            print(q.node.name, "is the best node in the list")
            if q.node == self.end:
                return self.trace_path(state.parent)
            for child_node in q.node.children:
                print("\n", child_node.name)
                c_turn = q.turn + 1
                if child_node.zone == "blocked":
                    continue
                if child_node.zone == "restricted":
                    c_turn += 1
                child = NodeState(node=child_node, turn=c_turn,
                                  end=self.end)
                child.update_fgh_values(self.hops, q)
                if any(node.node.name == child.node.name
                       and node.turn == child.turn
                       and node.g <= child.g for node in state.open):
                    print("same but better child is in open")
                    continue
                if any(node.node.name == child.node.name
                       and node.turn == child.turn
                       and node.g <= child.g for node in state.closed):
                    print("Already checked the same but better node")
                    continue
                if (not state.check_node_capacity(child)
                   or not state.check_connect_capacity(q, child)):
                    print("Waiting due to capacity")
                    wait = NodeState(node=q.node, turn=q.turn + 1,
                                     end=self.end)
                    wait.update_fgh_values(self.hops, q)
                    state.open.append(wait)
                    state.parent[(wait.node, wait.turn)] = (q.node, q.turn)
                    continue
                print("parent[(", child.node.name, child.turn, ")] =  ",
                     "(", q.node.name, q.turn, ")")
                state.parent[(child.node, child.turn)] = (q.node, q.turn)
                print("adding", child.node.name, "to queue")
                state.open.append(child)
            print("adding", q.node.name, " to closed")
            state.closed.append(q)
        raise ValueError("Error: Could not find goal")

    def trace_path(self, parent_list: dict[tuple[Node, int], tuple[Node, int]]
                   ) -> list[tuple[Node | Connection, int]]:
        pathway: list[tuple[Node | Connection, int]] = []
        node = self.end
        for node, turn in parent_list.keys():
            if node.name == self.end.name:
                pathway.append((node, turn))
                child_node = node
                child_turn = turn
                child = (child_node, child_turn)
        while child in parent_list.keys():
            parent = parent_list[child]
            if child[0].zone == "restricted":
                connect = self.shared_connection(parent[0], child[0])
                if connect is not None:
                    pathway.append((connect, child[1] - 1))
                pathway.append(parent)
            else:
                for i in range(parent[1], child[1]):
                    pathway.append(parent)
                    i += 1
            child = parent
        pathway = list(reversed(pathway))
        print("Pathfinder:")
        for node, turn in pathway:
            print(node.name, turn, end="")
        print()
        return (pathway)

    def update_connect_reserve(self,
                               path: list[tuple[Node | Connection, int]]
                               ) -> None:
        previous = path[0][0]
        for node, turn in path[1:]:
            if isinstance(node, Node) and isinstance(previous, Node):
                if node.zone == "restricted":
                    turn -= 1
                if node.name == previous.name:
                    continue
                connect = self.shared_connection(previous, node)
                if connect is None:
                    return
                if (connect, turn) not in self.reserve_connects.keys():
                    self.reserve_connects[(connect, turn)] = 1
                else:
                    self.reserve_connects[(connect, turn)] += 1
                previous = node

    def update_timeline(self, drone: int,
                        path: list[tuple[Node | Connection, int]]) -> None:
        compared_turn = 0
        for node, turn in path:
            if isinstance(node, Connection):
                connect = node
                if turn not in self.timeline.keys():
                    self.timeline[turn] = {}
                if connect not in self.timeline[turn].keys():
                    self.timeline[turn][connect] = []
                self.timeline[turn][connect].append(drone)
                compared_turn = turn + 1
                continue
            elif compared_turn != turn:
                for i in range(compared_turn, turn):
                    if i not in self.timeline.keys():
                        self.timeline[i] = {}
                    if node not in self.timeline[i].keys():
                        self.timeline[i][node] = []
                    self.timeline[i][node].append(drone)
                compared_turn = turn
            if turn not in self.timeline.keys():
                self.timeline[turn] = {}
            if node not in self.timeline[turn].keys():
                self.timeline[turn][node] = []
            self.timeline[turn][node].append(drone)
            compared_turn += 1

    def drone_allocation(self) -> None:
        drone = 1
        while drone <= self.drones:
            print("\ndrone", drone)
            path = self.a_star()
            self.update_timeline(drone, path)
            self.update_connect_reserve(path)
            drone += 1

    def turn_generator(self) -> Generator[list[tuple[int, Node | Connection]]]:
        self.drone_allocation()
        turn = 1
        while turn in self.timeline.keys():
            drone_stat: list[tuple[int, Node | Connection]] = []
            for node in self.timeline[turn].keys():
                for drone in self.timeline[turn][node]:
                    if (node in self.timeline[turn - 1]
                       and drone in self.timeline[turn - 1][node]):
                        continue
                    drone_stat.append((drone, node))
            yield drone_stat
            turn += 1
