from __future__ import annotations
from visualiser import Grid, Node, Connection
from collections.abc import Generator
from dataclasses import dataclass


@dataclass
class NodeState():
    """
    Data class that holds the state of a node in the A* search algorithm
    """
    node: Node
    turn: int = 0
    end: Node | None = None
    f: float = 0
    h: float = 0
    g: float = 0

    def update_fgh_values(self, hops: dict[Node, float],
                          parent: NodeState | None = None) -> None:
        """
        Finds the efficency of that node to get to it from start
        aswell as to get to goal, where f is g + h, g is the cost
        to get to the node from start and h is the estimated cost
        to reach the goal.
        """
        weight: float
        if self.node.zone == "priority":
            weight = 0.5
        elif self.node.zone == "resticted":
            weight = 2
        else:
            weight = 1
        if parent is not None:
            self.g = parent.g + weight
        else:
            self.g = 0
        self.h = hops[self.node]
        self.f = self.g + self.h


class AStarStates():
    """
    Class that holds the states of the A* search algorithm, which makes sure
    that the a* algorithm is reset each time a* algorithm is called.
    It does however retain the timeline and connection reserve from
    previous calls to a* so that the next drone can take into account
    the previous drones path to ensure node capacity is not exceeded.
    """
    def __init__(self, timeline: dict[int, dict[Node | Connection, list[int]]],
                 connect: dict[tuple[Connection, int], int], end: Node
                 ) -> None:
        """
        Sets the necessary variables for the A* search algorithm
        Preserves the timeline and connection reserve from previous calls to a*
        so that the next drone can take into account the previous drones path
        to ensure node capacity is not exceeded.
        """
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
        """
        Takes the timeline and converts it to a format that is more
        useful for the A* search algorithm, which is a dictionary of
        tuples of (node, turn) and the number of drones that are on that node
        at that turn. This is used to check if the node capacity is exceeded.
        """
        for turn in timeline.keys():
            for node in timeline[turn]:
                if isinstance(node, Connection):
                    connect = node
                    self.connect_reserve[(connect, turn)
                                         ] = len(timeline[turn][connect])
                else:
                    self.node_reserve[(node, turn)] = len(timeline[turn][node])

    def find_best_node_f(self) -> NodeState | None:
        """
        Finds the node with the lowest f value in the open list
        If there are multiple nodes with the same f value, it will choose
        the one with the lowest g value, and if there are still multiple
        nodes with the same g value, it will choose the one with the lowest
        h value.
        """
        if not self.open:
            return None
        nodes = self.open
        lowest_f = nodes[0]
        for node in nodes[1:]:
            if node.f < lowest_f.f:
                lowest_f = node
            elif (node.f == lowest_f.f and node.g < lowest_f.g):
                lowest_f = node
            elif (node.f == lowest_f and node.g == lowest_f.g
                  and node.h < lowest_f.h):
                lowest_f = node
        for node in self.open:
            if self.end == node.node and node.f == lowest_f.f:
                lowest_f = node
        self.open.remove(lowest_f)
        return (lowest_f)

    def check_node_capacity(self, node_state: NodeState) -> bool:
        """
        Checks if the node capacity is exceeded at the given turn
        by checking the node_reserve dictionary for the number of drones
        that are on that node at that turn.
        returns False if node capacity is full
        returns True if node capacity is not full
        """
        node = node_state.node
        turn = node_state.turn
        if ((node, turn) in self.node_reserve
           and self.node_reserve[(node, turn)]) == node.capacity:
            return False
        return True

    @staticmethod
    def find_shared_connect(src: Node, dest: Node) -> Connection | None:
        """
        Finds shared connection between two nodes, if it exists
        returns the connection, otherwise returns None
        """
        for connect in src.connection:
            if (connect.connect1 == dest.name
               or connect.connect2 == dest.name):
                return connect
        return None

    def check_connect_capacity(self, src: NodeState, dest: NodeState) -> bool:
        """
        Checks if the connection capacity is exceeded at the given turn
        by checking the connect_reserve dictionary for the number of drones
        that are on that connection at that turn.
        returns False if connection capacity is full
        returns True if connection capacity is not full
        """
        connect = self.find_shared_connect(src.node, dest.node)
        if connect is None:
            raise ValueError("Error: Could not find shared connetion")
        if (dest.node.zone == "restricted"
           and (connect, dest.turn - 1) in self.connect_reserve.keys()):
            if self.connect_reserve[(connect, dest.turn - 1)
                                    ] == connect.capacity:
                return False
        if (connect, dest.turn) in self.connect_reserve.keys():
            if self.connect_reserve[(connect, dest.turn)] == connect.capacity:
                return False
        return True


class Pathfinding():
    """
    Class that holds the pathfinding algorithm, which is the A* search
    algorithm.
    """
    def __init__(self, grid: Grid) -> None:
        """
        Sets needed variables from grid as well as holding functions
        from other classes so that they are more accessible
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

    def find_hops_to_goal(self) -> dict[Node, float]:
        """
        Estimates number of movements needed to reach the goal from each node,
        creating a dictionary with the the value being how many hops away
        from the goal. It starts from the end and goes to each node,
        adding 1 for each hop, and adding a weight for each node
        depending on the zone type.
        """
        hops: dict[Node, float] = {}
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
                    weight: float = 1
                    if node.zone == "restricted":
                        weight = 3
                    elif node.zone == "priority":
                        weight = 0.5
                    hops[new_node] = hops[node] + weight
                    queue.append(new_node)
        return hops

    def a_star(self) -> list[tuple[Node | Connection, int]]:
        """
        Search algorithm that finds the best path to get
        from start to goal
        It uses the A* search algorithm, appends the start
        and explores the best node in the open list which has the
        lowest f value. It adds the children of the best node to
        the open list and repeats until the goal is found.
        It takes in account the timeline and connection reserve from
        previous calls to a*, aswell  as node capacity, node zone and
        connection capacity. If any capcity is exceeded,
        it will add the node again to the open list but one turn later
        to simulate waiting for the node to be free.
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
            if q.node == self.end:
                return self.trace_path(state.parent)
            for child_node in q.node.children:
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
                    continue
                if any(node.node.name == child.node.name
                       and node.turn <= child.turn
                       and node.g <= child.g for node in state.closed):
                    continue
                if (not state.check_node_capacity(child)
                   or not state.check_connect_capacity(q, child)):
                    wait = NodeState(node=q.node, turn=q.turn + 1,
                                     end=self.end)
                    wait.update_fgh_values(self.hops, q)
                    state.open.append(wait)
                    state.parent[(wait.node, wait.turn)] = (q.node, q.turn)
                    continue
                state.parent[(child.node, child.turn)] = (q.node, q.turn)
                state.open.append(child)
            state.closed.append(q)
        raise ValueError("Error: Could not find goal")

    def trace_path(self, parent_list: dict[tuple[Node, int], tuple[Node, int]]
                   ) -> list[tuple[Node | Connection, int]]:
        """
        Traces the path from the end node to the start node
        by following the parent nodes in the parent_list dictionary.
        It returns a list of tuples of the node and the associated turn number.
        If the node is a restricted zone, it will also add the connection
        between the parent and child node to the path
        """
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
        return (pathway)

    def update_connect_reserve(self,
                               path: list[tuple[Node | Connection, int]]
                               ) -> None:
        """
        Updates the connection reserve dictionary with the number of drones
        that are on each connection at each turn. It takes in the path
        that was found by the A* search algorithm and adds the connections
        to the reserve dictionary with the associated turn number.
        If the connection is a restricted zone, it will add the connection
        to the reserve dictionary with the turn number - 1, to simulate
        the drone in the connection.
        It skips the nodes that are the same as the previous node,
        as the drone has chosen to wait
        """
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
        """
        Updates the timeline dictionary with the number of drones
        that are on each node at each turn. It takes in the path
        that was found by the A* search algorithm and adds the nodes
        to the timeline dictionary with the associated turn number.
        If the node is a restricted zone, it will add the connection
        to the timeline dictionary with the turn number - 1, to simulate
        the drone in the connection.
        It skips the nodes that are the same as the previous node,
        as the drone has chosen to wait
        Timeline contains the timeline of all drones that have had their path
        calculated, so that the next drone can take into account the previous
        drones path to ensure node capacity is not exceeded.
        """
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
        """
        Allocates the path for each drone by calling the A* search algorithm
        and updating the timeline and connection reserve dictionaries
        with the path found by the A* search algorithm. It does this for the
        number of drones specified by the parsed text file.
        """
        drone = 1
        while drone <= self.drones:
            path = self.a_star()
            self.update_timeline(drone, path)
            self.update_connect_reserve(path)
            drone += 1

    def turn_generator(self) -> Generator[list[tuple[int, Node | Connection]]]:
        """
        Generates the timeline of drones at each turn by calling the
        drone_allocation function and yielding the timeline for each turn.
        It yields a list of tuples of the drone number and the node or
        connection that the drone is on at that turn. It sorts the list
        by drone number so that the drones are in order of their number
        instead of nodes.
        """
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
            drone_stat.sort(key=lambda x: x[0])
            yield drone_stat
            turn += 1
