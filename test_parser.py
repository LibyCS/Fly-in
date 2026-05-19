from parser import parse, Hub, DataDict
from io import StringIO
import pytest


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

    @staticmethod
    def make_exp_hub(coords: tuple[int, int],
                     meta: dict[str, str | int] | None = None,
                     connect: dict[tuple[str, str], int] | None = None
                     ) -> Hub:
        exp_hub: Hub = {}
        exp_hub= {}
        exp_hub["coords"] = coords
        if meta is not None:
            exp_hub["metadata"] = meta
        if connect is not None:
            exp_hub["connection"] = connect
        return exp_hub

    @staticmethod
    def update_exp_hub_list(old_list: list[tuple[Hub, str]],
                            new_hub_list: list[tuple[Hub, str]]) -> None:
        for new_hub, new_hub_name in new_hub_list:
            index = 0
            for _, cur_hub_name in old_list:
                if new_hub_name == cur_hub_name:
                    old_list[index] = (new_hub, new_hub_name)
                    continue
                index += 1

    @staticmethod
    def hub_list_testing(validate_hubs: list[tuple[Hub, str]],
                         exp_hubs: list[tuple[Hub, str]]) -> None:
        assert len(validate_hubs) == len(exp_hubs)
        for exp_hub, exp_hub_name in validate_hubs:
            found = False
            for validate_hub, validate_hub_name in exp_hubs:
                if validate_hub_name == exp_hub_name:
                    assert validate_hub == exp_hub
                    found = True
                    break
            if found is False:
                raise ValueError(f"Error: Did not find {exp_hub_name}")

    def base_testing(self, text: str, new_exp_hubs: list[tuple[Hub, str]] | str | None = None
                     ) -> None:
        result = self.make_data(text)
        validate_hubs: list[tuple[Hub, str]] = []
        start_name = list(result["start_hub"].keys())
        end_name = list(result["end_hub"].keys())
        assert len(start_name) == 1
        assert len(end_name) == 1
        validate_hubs.append((result["start_hub"][start_name[0]],
                              start_name[0]))
        validate_hubs.append((result["end_hub"][end_name[0]], end_name[0]))
        for name in result["hub"].keys():
            validate_hubs.append((result["hub"][name], name))
        hub_names = ["start", "waypoint1", "waypoint2", "goal"]
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
        exp_hubs: list[tuple[Hub, str]] = []
        for i in range(0, len(hub_names)):
            exp_hub = self.make_exp_hub(exp_coords[i],
                                        exp_meta[i], exp_connects[i])
            exp_hubs.append((exp_hub, hub_names[i]))
        if new_exp_hubs is not None:
            self.update_exp_hub_list(exp_hubs, new_exp_hubs)
        self.hub_list_testing(validate_hubs, exp_hubs)

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
        new_start = self.make_exp_hub((0, 0), connect={("start", "waypoint1"): 3})
        self.base_testing(empty_meta, [(new_start, "start")])
        print("[OK]")
    
    def test_wrong_coords(self) -> None:
        """
        Testing no coords, 1 coords and more than 3 coords, wrong coords
        for all types of hubs
        """
        print("---Invalid Coords---")
        print("Test 1: No coords")
        no_coords = self.edit_line(self.DEFAULT, 3, "start_hub: start ")
        new_start = self.make_exp_hub((0, 0), connect={("start", "waypoint1"): 3})
        with pytest.raises(ValueError) as message:
            self.make_data(no_coords)
        print(message.value)
        print("[OK]")

