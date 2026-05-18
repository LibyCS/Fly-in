from parser import parse, Hub, DataDict
from io import StringIO


class TestParser:
    DEFAULT = """# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green max_drones=3]
hub: waypoint1 1 0 [color=blue zone=restricted max_drones=3]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1 [max_link_capacity=3]
connection: waypoint1-waypoint2
connection: waypoint1-goal
connection: waypoint2-goal"""

    @staticmethod
    def make_data(text: str) -> DataDict:
        """
        The file is an interable so will be used up
        therefore to avoid that we must remake the
        file each time
        """
        return parse(StringIO(text))

    @staticmethod
    def edit_line(old_text: str, line_num: int, new_line: str) -> str:
        lines = old_text.splitlines()
        lines[line_num] = new_line
        new_text = ""
        for line in lines:
            new_text = new_text + line + "\n"
        return new_text

    def hub_testing(self, node: Hub, coords: tuple[int, int],
                    meta: dict[str, str | int] | None = None,
                    connect: dict[tuple[str, str], int] | None = None) -> None:
        assert node["coords"] == coords
        if meta:
            if "metadata" in node.keys():
                assert node["metadata"] == meta
            else:
                print("Error")
        if connect:
            if "connection" in node.keys():
                assert node["connection"] == connect
            else:
                print("Error")

    def base_testing(self, text: str, hubs: list[Hub] | str | None = None,
                     coords: list[tuple[int]] | str | None = None,
                     meta: list[dict[str, str | int]] | str | None = None,
                     connects:
                     list[dict[tuple[str, str], int]] | str | None = None,
                     target_hub_name: str | None = None) -> None:
        result = self.make_data(text)
        start = result["start_hub"]["start"]
        point1 = result["hub"]["waypoint1"]
        point2 = result["hub"]["waypoint2"]
        goal = result["end_hub"]["goal"]
        hub_names = ["start", "waypoint1", "waypoint2", "goal"]
        exp_hubs = [start, point1, point2, goal]
        exp_coords = [(0, 0), (1, 0), (2, 0), (3, 0)]
        exp_meta: list[dict[str, str | int] | None
                       ] = [{"color": "green", "max_drones": 3},
                            {"color": "blue", "zone": "restricted",
                             "max_drones": 3},
                            {"color": "blue"},
                            {"color": "red"}
                            ]
        exp_connects = [{("start", "waypoint1"): 3},
                        {("start", "waypoint1"): 3,
                         ("waypoint1", "waypoint2"): 1,
                         ("waypoint1", "goal"): 1},
                        {("waypoint1", "waypoint2"): 1,
                         ("waypoint2", "goal"): 1},
                        {("waypoint1", "goal"): 1,
                         ("waypoint2", "goal"): 1}
                        ]
        if target_hub_name:
            for index in range(0, len(hub_names)):
                if target_hub_name == hub_names[index]:
                    break
            if target_hub_name != hub_names[index]:
                index = -1
            exp_list_type = [exp_hubs, exp_coords, exp_meta, exp_connects]
            index = 0
            for list_type in [hubs, coords, meta, connects]:
                if list_type is not None:
                    if isinstance(list_type, str):
                        if list_type != "remove":
                            raise ValueError("Error: Should be 'remove'")
                        exp_list_type[index] = {}
                    elif index != -1:
                        exp_list_type[index] = list_type[0]
                    else:
                        exp_list_type = exp_list_type + list_type
                index += 1
        for i in range(0, len(exp_hubs)):
            self.hub_testing(exp_hubs[i], exp_coords[i], exp_meta[i],
                             exp_connects[i])

    def test_base(self) -> None:
        """
        Testing valid configuration
        """
        print("Test 1: Valid Configuration")
        self.base_testing(self.DEFAULT)
        print("[OK]")

    def test_whitespaces(self) -> None:
        """
        Testing leading and trailing Valid Whitespaces
        with whitespaces in metadata
        """
        print("Test 2: Valid Whitespaces")
        meta_space = self.DEFAULT.replace("[", "  [  ")
        meta_space = meta_space.replace("]", "  ]  ")
        whitespace_text = ""
        for line in self.DEFAULT.splitlines():
            whitespace_text = whitespace_text + "  " + line + "  \n"
        self.base_testing(whitespace_text)
        print("[OK]")

    def test_empty_meta(self) -> None:
        """
        Testinng for empty metadata sets
        """
        print("Test 3: Testing empty Metdata")
        empty_meta = self.edit_line(self.DEFAULT, 3, "start_hub: start 0 0 []")
        self.base_testing(empty_meta, meta="remove", target_hub_name="start")
        print("OK")
