from typing import TypedDict, TextIO
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


def validate_name(name: str) -> None:
    """
    Checks if the name is the correct format
    """
    if "_" in name:
        splitted_name = name.split("_")
        for part in splitted_name:
            if not part.isalnum():
                raise ValueError(f"{name} is not valid, it must not"
                                 "contain '-' and must be alphanumeric")
    elif not name.isalnum():
        raise ValueError(f"{name} is not valid, it must not contain"
                         " '-' and must be alphanumeric and can have '_'")


def validate_drones(info: str) -> None:
    """
    Checks if drone is an int greater than 1
    """
    try:
        value_int = int(info)
    except ValueError:
        raise ValueError(f"nb_drone's value: '{info}' is not of"
                         " type int")
    if value_int < 1:
        raise ValueError("Number of drones must be > 0")


def validate_hub(info: str) -> None:
    """
    Checks that hub has the valid parameters and obeys
    naming convention
    """
    try:
        name, x, y = info.split()
    except ValueError:
        raise ValueError("Invalid number of arguments were given"
                         f" for the hub {info}, please format it as such:\n"
                         "<hub type>: <hub name> <x> <y> ([metadata])\n"
                         "Hub type must either be start_hub, end_hub or hub\n"
                         "Hub name may be whatever you choose but it cannot "
                         "have a '-' or a space in it\n"
                         "x and y coords must be ints seperated by spaces\n"
                         "Metadata is optional but must have square brackets")
    validate_name(name)
    try:
        int(x)
        int(y)
    except ValueError:
        if "," in x or "," in y:
            raise ValueError(f"{name}'s coords {x} {y} "
                             "cannot be seperated by commas")
        raise ValueError(f"{name} ({x}, {y}) does not have"
                         " valid coordinates, must be of type int")


def validate_connect(info: str) -> None:
    """
    checks connect is valid and obeys naming convention
    """
    if "-" not in info:
        raise ValueError(f"Could not find '-' in connection: '{info}'")
    parts = info.split("-")
    if len(parts) != 2:
        raise ValueError("Connection name should only have 2 parts"
                         "\nPlease make sure there is only 1 '-'")
    for string in info.split("-"):
        validate_name(string)


def check_isolated_node(data: DataDict) -> None:
    """
    Checks for any hubs that have no connections
    and raises an error if found
    """
    all_types = {Keys.START_HUB, Keys.END_HUB, Keys.HUB}
    for hub_type in all_types:
        for hub in data[hub_type.value]:
            if not data[hub_type.value][hub]["connection"]:
                raise ValueError(f"Error: '{hub}' hub is "
                                 "isolated and has no connections")


def check_start_end(data: DataDict) -> None:
    """
    Checks that there is a start and end hub in the data dictionary
    """
    if not data[Keys.START_HUB.value]:
        raise ValueError("Error: No start hub was found")
    elif not data[Keys.END_HUB.value]:
        raise ValueError("Error: No end hub was found")


def validate_base(zone: str, info: str) -> None:
    """
    Checks zone is valid, checks the info such as the name,
    coords annd connections are valid types and obey naming
    convention.
    """
    info = info.strip()
    if zone == "nb_drones":
        validate_drones(info)
    elif zone in ["start_hub", "end_hub", "hub"]:
        validate_hub(info)
    elif zone == "connection":
        validate_connect(info)
    else:
        raise ValueError(f"'{zone}' is not a valid hub type, must be"
                         " nb_drones, start_hub, end_hub, hub or connection")


def validate_meta_hub(zone: str, metadata: str) -> None:
    """
    Checks that metadata if provided has the valid tags and
    correct valid values for hubs
    """
    tags = ["color", "zone", "max_drones"]
    zone_types = ["normal", "blocked", "restricted", "priority"]
    keys = []
    for data in metadata.split():
        if "=" in data:
            key, value = data.split("=", 1)
            if "-" in value:
                value_list = value.split("-")
            else:
                value_list = [value]
            for part in value_list:
                if not part.isalnum():
                    raise ValueError(f"For {zone}'s metadata"
                                     f" the '{value}' for '{key}' is invalid"
                                     " value must be alphanumeric")
        else:
            raise ValueError("Invalid format for metadata in"
                             f" {zone}: {data}, which must be formatted"
                             "as '<key>=<value>'")
        if key in keys:
            raise ValueError("Duplicate tag was found in "
                             f"{zone}")
        keys.append(key)
    try:
        meta = dict(data.split("=") for data in metadata.split())
    except ValueError:
        raise ValueError(f"Tags for the metadata of {zone}"
                         " has invalid format")
    if '' in meta.keys():
        raise ValueError(f"No metadata key was given in '{metadata}'")
    if len(meta) > 3:
        raise ValueError("Too many tags were given")
    for data in meta.keys():
        if metadata.count(data) != 1:
            raise ValueError(f"Multiple tags of '{data}' were found")
        if data not in tags:
            raise ValueError(f"{data} for {zone} is"
                             " not a valid tag")
        elif data == "zone" and meta[data] not in zone_types:
            raise ValueError("Unknown zone type was given")
        elif data == "color":
            if (meta[data] != "rainbow" and
               meta[data] not in colours.CSS4_COLORS):
                raise ValueError(f"Colour {meta[data]} was not valid")
        elif data == "max_drones":
            try:
                drones = int(meta[data])
            except ValueError:
                raise ValueError(f"{zone} capacity given was{meta[data]}"
                                 ", must be a valid int")
            if drones < 1:
                raise ValueError(f"{zone} capacity given was {meta[data]}"
                                 ", must be >= 1")
        if (zone in (Keys.START_HUB, Keys.END_HUB)
           and data == "zone" and meta[data] == "blocked"):
            raise ValueError(f"'{zone}' can not be a blocked zone")


def validate_meta_connect(metadata: str) -> None:
    """
    Checks that metadata if provided has the valid tags and
    correct valid values for connections
    """
    try:
        meta = dict(data.split("=") for data in metadata.split())
    except ValueError:
        raise ValueError("Tag for the metadata of connection"
                         " has invalid format")
    if len(meta) > 1:
        raise ValueError("Too many tags were given for connections")
    for data in meta.keys():
        if metadata.count(data) != 1:
            raise ValueError(f"Multiple tags of {data} were found")
        if data != "max_link_capacity":
            raise ValueError("Connections can only have the "
                             "the tag max_link_capacity=<number>")
        try:
            capacity = int(meta[data])
            if capacity < 1:
                raise ValueError
        except ValueError:
            raise ValueError("max_link_capacity must be a"
                             " valid positive int >= 1")


def build_hub(data: DataDict, zone: Keys, info: str, meta: (None | str) = None
              ) -> None:
    """
    Takes the existing prebuild dictionary and adds one key and its
    data at a time everytime its called
    """
    hubs: dict[str, Hub] = data[zone.value]
    hub: Hub = {}
    if zone == Keys.START_HUB and data[Keys.START_HUB.value]:
        raise ValueError("Found 2 or more start hubs")
    elif zone == Keys.END_HUB and data[Keys.END_HUB.value]:
        raise ValueError("Found 2 or more end hubs")
    name, x, y = info.split()
    if (name in data[Keys.START_HUB.value] or name in data[Keys.END_HUB.value]
       or name in data[Keys.HUB.value]):
        raise ValueError(f"Duplicate hub found, {name} is already a hub")
    hub["coords"] = (int(x), int(y))
    hub_types: list[Keys] = list(Keys)
    for hub_type in hub_types:
        for comp_hub in data[hub_type.value].keys():
            if hub["coords"] == data[hub_type.value][comp_hub]["coords"]:
                raise ValueError("Hubs cannot share the same"
                                 " coordinates")
    if meta:
        meta_dict: dict[str, int | str] = {}
        meta_list: list[str] = list(meta.split())
        for key, value in (meta_data.split("=") for meta_data in
                           meta_list):
            if key == "max_drones":
                meta_dict[key] = int(value)
            else:
                meta_dict[key] = value
        if ((zone in (Keys.START_HUB, Keys.END_HUB))
           and "max_drones" in meta_dict.keys()):
            meta_dict["max_drones"] == 500
        hub["metadata"] = meta_dict
    hub["connection"] = {}
    hubs[name] = hub


def build_connections(data: DataDict, info: str, meta: (None | str) = None
                      ) -> None:
    """
    Takes in the incomplete data dictionary and adds the neccessary
    connections to the specified hubs
    """
    all_hubs = {**data[Keys.START_HUB.value], **data[Keys.END_HUB.value],
                **data[Keys.HUB.value]}
    try:
        hub1, hub2 = map(str.strip, info.split("-"))
    except ValueError:
        raise ValueError(f"Connection {info} is not formatted"
                         "properly, must be formatted as hub1-hub2")
    if "hub" not in data.keys():
        raise ValueError("No hubs were provided")
    if (hub1 not in all_hubs or hub2 not in all_hubs):
        raise ValueError(f"{info} is not a valid connection couldn't find"
                         " one of the hubs")
    if hub1 == hub2:
        raise ValueError("Cannot make a connection with itself")
    capacity = 500
    if meta:
        value_index = meta.find("=")
        value = meta[value_index + 1:]
        capacity = int(value)
    all_types = {Keys.START_HUB, Keys.END_HUB, Keys.HUB}
    for hub_t in all_types:
        for compared_hub in data[hub_t.value]:
            if hub1 == compared_hub:
                if ((hub1, hub2) in
                   data[hub_t.value][hub1]["connection"].keys()
                   or (hub2, hub1) in
                   data[hub_t.value][hub1]["connection"].keys()):
                    raise ValueError("Duplicate connection found"
                                     f"({hub1}, {hub2})")
                data[hub_t.value][hub1]["connection"][(hub1, hub2)] = capacity
            elif hub2 == compared_hub:
                if ((hub1, hub2) in
                   data[hub_t.value][hub2]["connection"].keys()
                   or (hub2, hub1) in
                   data[hub_t.value][hub2]["connection"].keys()):
                    raise ValueError("Duplicate connection found"
                                     f"({hub1}, {hub2})")
                data[hub_t.value][hub2]["connection"][(hub1, hub2)] = capacity


def extraction(line: str, data: DataDict, connect_nb: int) -> None:
    """
    Takes in a line from the config file and extracts the zone and info
    and calls the neccessary functions to validate and build the
    data dictionary or hubs or connection
    """
    try:
        zone, info = map(str.strip, line.split(":", 1))
    except ValueError:
        raise ValueError(f"For '{line}' the hub type must have"
                         " ':' proceeding it to identify the hub_type")
    meta = None
    if "[" in info and "]" in info:
        index = info.find("[")
        end_index = info.find("]")
        meta = info[index + 1: end_index].strip()
        info = info[:index].strip()
    validate_base(zone, info)
    if meta is not None and meta.strip() != "":
        if zone == "connection":
            validate_meta_connect(meta)
        else:
            validate_meta_hub(zone, meta)
    if zone == "nb_drones":
        data["nb_drones"] = int(info)
    elif data["nb_drones"] == 0:
        raise ValueError("First line must be the number of"
                         " drones, defined as 'nb_drones: <number>'")
    elif zone == "connection":
        connect_nb += 1
        build_connections(data, info, meta)
    else:
        if connect_nb != 0:
            raise ValueError("All hubs must first be created"
                             " before connections can be initialised.\n"
                             "Please reformat the config file so that"
                             " all connections are after hubs")
        build_hub(data, Keys(zone), info, meta)


def parse(fname: TextIO) -> DataDict:
    """
    Takes the file object, reads line by line and returns a dictionary
    containing all the necessary variables
    """
    data: DataDict = {"nb_drones": 0, "hub": {}, "start_hub": {},
                      "end_hub": {}}
    connect_counter = 0
    line_nb = 1
    for line in fname:
        line = line.strip()
        if not line or line.startswith("#"):
            line_nb += 1
            continue
        try:
            extraction(line, data, connect_counter)
        except ValueError as message:
            raise ValueError(f"Error on line {line_nb}: {message}")
        line_nb += 1
    check_isolated_node(data)
    check_start_end(data)
    return data
