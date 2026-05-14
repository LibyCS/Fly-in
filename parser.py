from typing import TypedDict, cast, TextIO
from enum import Enum
import matplotlib.colors as colours


class Hub(TypedDict, total=False):
    """
    Types the specialised hub dictionary
    """
    coords: tuple[int, int]
    metadata: dict[str, (int | str)]
    connection: dict[tuple[str, str], int]


class DataDict(TypedDict):
    """
    Types the specialised dictionary of data
    """
    nb_drones: int
    hub: dict[str, Hub]
    start_hub: dict[str, Hub]
    end_hub: dict[str, Hub]


class Keys(str, Enum):
    """
    Allows dictionary to pass zone as a string literal
    """
    HUB = "hub"
    START_HUB = "start_hub"
    END_HUB = "end_hub"


def validate(zone: str, info: str) -> None:
    """
    Checks zone is valid, checks the info such as the name,
    coords annd connections are valid types and obey nnaming
    convention.
    """
    name = None
    info = info.strip()
    if zone == "nb_drones":
        try:
            value_int = int(info)
        except ValueError:
            raise ValueError(f"Error: {zone}'s value: {info} is not of"
                             " type int")
        if value_int < 1:
            raise ValueError("Error: Number of drones must be > 0")
    elif zone in ["start_hub", "end_hub", "hub"]:
        try:
            name, x, y = info.split()
        except ValueError:
            raise ValueError("Error: Invalid number of arguments were given"
                             f" for {info}")
        if "_" in name:
            splitted_name = name.split("_")
            for part in splitted_name:
                if not part.isalnum() or "-" in part:
                    raise ValueError(f"Error: {name} is not valid, it must not"
                                     "contain '-' and must be alphanumeric")
        elif not name.isalnum() or "-" in name:
            raise ValueError(f"Error: {name} is not valid, it must not contain"
                             " '-' and must be alphanumeric and can have '_'")
        try:
            int(x)
            int(y)
        except ValueError:
            raise ValueError(f"Error: {name} ({x}, {y}) does not have"
                             " valid coordinates")
    elif zone == "connection":
        if "-" not in info:
            raise ValueError(f"Error: Could not find '-' in connection {zone}")
        for string in info.split("-"):
            if "_" in string:
                splitted_name = string.split("_")
                for part in splitted_name:
                    if not part.isalnum() or "-" in part:
                        raise ValueError("Error: Connection is not valid, "
                                         "it must not contain '-' and must"
                                         " be alphanumeric")
            elif not string.isalnum():
                raise ValueError("Error: Invalid connection was given, "
                                 f"{string} must be alphanumeric")
    else:
        raise ValueError(f"Error: {zone} is not valid, must be"
                         "nb_drones, start_hub, end_hub, hub or connection")


def validate_meta(zone: str, metadata: str) -> None:
    """
    Checks that metadata if provided has the valid tags and
    correct valid values
    """
    tags = ["color", "zone", "max_drones"]
    zone_types = ["normal", "blocked", "restricted", "priority"]
    try:
        meta = dict(data.split("=") for data in metadata.split())
    except ValueError:
        raise ValueError(f"Error: Tags for the metadata of {zone}"
                         " is invalid")
    if len(meta) > 3:
        raise ValueError("Error: Too many tags were given")
    for data in meta.keys():
        if metadata.count(data) != 1:
            raise ValueError(f"Error: multiple tags of {data} were found")
        if ((zone == "connection" and data != "max_link_capacity")
           or (zone != "connection" and data not in tags)):
            raise ValueError(f"Error: {data} is not a valid tag")
        elif data == "zone" and meta[data] not in zone_types:
            raise ValueError("Error: Unknwon zone type was given")
        elif data == "color":
            if (meta[data] != "rainbow" and
               meta[data] not in colours.CSS4_COLORS.keys()):
                raise ValueError(f"Error: Colour {meta[data]} was not valid")
        elif data == "max_drones":
            try:
                drones = int(meta[data])
                if drones < 1:
                    raise ValueError
            except ValueError:
                raise ValueError(f"{meta[data]} for {zone} must be a"
                                 " positive valid int >= 1")
        if zone == "start_hub" or zone == "start_hub":
            if data == "zone" and meta[data] != "normal":
                raise ValueError(f"Error: {zone} can only have a"
                                 " normal zone")
        elif zone == "connection":
            if data != "max_link_capacity":
                raise ValueError("Error: Connections can only have the "
                                 "the tag max_link_capacity=<number>")
            try:
                capacity = int(meta[data])
                if capacity < 1:
                    raise ValueError
            except ValueError:
                raise ValueError("Error: max_link_capacity must be a"
                                 "valid positive int >= 1")


def build_hub(data: DataDict, zone: Keys, info: str, meta: (None | str) = None
              ) -> None:
    """
    Takes the existing prebuild dictionary and adds one key and its
    data at a time everytime its called
    """
    all_hubs = (list(data["hub"].keys()) + list(data["start_hub"].keys())
                + list(data["end_hub"].keys()))
    if zone in [Keys.START_HUB, Keys.END_HUB, Keys.HUB]:
        hubs: dict[str, Hub] = cast(dict[str, Hub], data[zone.value])
        hub: Hub = {}
        if "nb_drones" not in data.keys():
            raise ValueError("Error: first line must be the number of"
                             " drones, defined as 'nb_drones: <number>'")
        if zone == Keys.START_HUB and data[Keys.START_HUB.value]:
            raise ValueError("Error found 2 or more start hubs")
        elif zone == Keys.END_HUB and data[Keys.END_HUB.value]:
            raise ValueError("Error found 2 or more end hubs")
        name, x, y = info.split()
        if name in all_hubs:
            raise ValueError(f"Error: {name} is already a hub")
        hub["coords"] = (int(x), int(y))
        hub_types: list[Keys] = [Keys.START_HUB, Keys.END_HUB, Keys.HUB]
        for hub_type in hub_types:
            for comp_hub in data[hub_type.value].keys():
                if hub["coords"] == data[hub_type.value][comp_hub]["coords"]:
                    raise ValueError("Error: hubs cannot share the same"
                                     "coordinates")
        if meta:
            meta_dict: dict[str, (int | str)] = {}
            meta_list: list[str] = list(meta.split())
            for key, value in (meta_data.split("=") for meta_data in
                               meta_list):
                if key == "max_drones":
                    meta_dict[key] = int(value)
                else:
                    meta_dict[key] = value
            if ((zone == "start_hub" or zone == "end_hub")
               and "max_drones" in meta_dict.keys() and
               int(meta_dict["max_drones"]) < data["nb_drones"]):
                raise ValueError("Error: Zone is too restricted to handle"
                                 " all drones in start/end hub")
            hub["metadata"] = meta_dict
        hub["connection"] = {}
        hubs[name] = hub


def build_connections(data: DataDict, info: str, meta: (None | str) = None
                      ) -> None:
    """
    Takes in the incomplete data dictionary and adds the neccessary
    connections to the specified hubs
    """
    all_hubs = (list(data["hub"].keys()) + list(data["start_hub"].keys())
                + list(data["end_hub"].keys()))
    try:
        hub1, hub2 = map(str.strip, info.split("-"))
    except ValueError:
        raise ValueError(f"Error: Connection {info} is not formatted"
                         "properly, must be formatted as hub1-hub2")
    if "hub" not in data.keys():
        raise ValueError("Error: No hubs were provided")
    if (hub1 not in all_hubs or hub2 not in all_hubs):
        raise ValueError(f"{info} is not a valid connection couldn't find"
                         " one of the hub")
    if hub1 == hub2:
        raise ValueError("Error: Cannot make a connection with itself")
    capacity = 1
    if meta:
        value_index = meta.find("=")
        value = meta[value_index + 1:]
        capacity = int(value)
    all_types: list[Keys] = [Keys.START_HUB, Keys.END_HUB, Keys.HUB]
    for hub_t in all_types:
        for compared_hub in data[hub_t.value]:
            if hub1 == compared_hub:
                data[hub_t.value][hub1]["connection"][(hub1, hub2)] = capacity
            elif hub2 == compared_hub:
                data[hub_t.value][hub2]["connection"][(hub1, hub2)] = capacity


def parse(fname: TextIO) -> DataDict:
    """
    Takes the file object, reads line by line and returns a dictionary
    containing all the necessary variables
    """
    data: DataDict = {"nb_drones": 0, "hub": {}, "start_hub": {},
                      "end_hub": {}}
    for line in fname:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        zone, info = map(str.strip, line.split(":", 1))
        meta = None
        if "[" in info and "]" in info:
            index = info.find("[")
            end_index = info.find("]")
            meta = info[index + 1: end_index].strip()
            info = info[:index].strip()
        validate(zone, info)
        if meta is not None:
            validate_meta(zone, meta)
        if zone == "nb_drones":
            data["nb_drones"] = int(info)
        elif zone == "connection":
            build_connections(data, info, meta)
        else:
            build_hub(data, Keys(zone), info, meta)
    return data
