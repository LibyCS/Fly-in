import sys


def validate(zone: str, info: str, metadata=None) -> None:
    if zone == "nb_drones":
        try:
            int(info)
        except TypeError:
            raise Exception(f"Error: {zone}'s value: {info} is not of"
                            " type int")
    elif zone in ["start_hub", "end_hub", "hub"]:
        try:
            name, x, y = info.strip("", 3)
            if not name.isalnum() or "-" in name:
                raise TypeError
        except ValueError:
            raise Exception(f"Error: Invalid number of arguments were given"
                            " for {info}")
        except TypeError:
            raise Exception(f"Error: {name} is not valid, it must not contain"
                             " '-' and must be alphanumeric")
        try:
            int(x)
            int(y)
        except TypeError:
            raise Exception(f"Error: {name} ({x}, {y}) does not have"
                            " valid coordinates")
    elif zone == "connection":
        if not info.isalphanum():
            raise Exception(f"Error: Invalid connection was given, "
                            "must be alphanumeric")
        elif "-" not in info:
            raise Exception(f"Error: Could not find '-' in connection {zone}")
    else:
        raise Exception(f"Error: {zone} is not valid, must be"
                        "nb_drones, start_hub, end_hub, hub or connection")
    if metadata:
        tags = ["color", "zone", "max_drones"]
        zone_types = ["normal", "blocked", "restricted", "priority"]
        colour = ["green", "yellow", "red", "blue", "gray"]
        try:
            meta = dict(data.split("=") for data in data.split())
        except ValueError:
            raise Exception(f"Error: Tags for the metadata of {zone}"
                            " is invalid")
        if len (meta) > 3:
            raise Exception(f"Error: Too many tags were given")
        for data in meta.keys():
            if metadata.count(data) != 1:
                raise Exception(f"Error: multiple tags of {data} were found")
            if data not in tags:
                raise Exception(f"Error: {data} is not a valid tag")
            elif data == "zone" and meta[data] not in zone_types:
                raise Exception(f"Error: Unknwon zone type was given")
            elif data == "color" and meta[data] not in colour:
                raise Exception(f"Error: Colour given was not valid")
            elif data == "max_drones":
                try:
                    int(meta[data])
                    if meta[data] < 1:
                        raise ValueError
                except (TypeError, ValueError):
                    raise Exception(f"{meta[data]} for {zone} must be a"
                                    " positive valid int >= 1")
            if zone == "start_hub" or zone == "start_hub":
                if data == "zone" and meta[data] != "normal":
                    raise Exception(f"Error: {zone} can only have a"
                                    " normal zone")
            elif zone == "connection":
                if data != "max_link_capacity":
                    raise Exception(f"Error: Connections can only have the "
                                    "the tag max_link_capacity=<number>")
                try:
                    int(meta[data])
                    if meta[data] < 1:
                        raise ValueError
                except (TypeError, ValueError):
                    raise Exception(f"Error: max_link_capacity must be a"
                                    "valid positive int >= 1")
            

def parse(fname) -> dict:
    data: dict = {}
    data["hub"] = {}
    data["start_hub"] = {}
    data["end_hub"] = {}
    for line in fname.readlines():
        line = line.lstrip()
        if line[0] == "#":
            continue
        zone, info = line.split(":", 1)
        meta = None
        if "[" and "]" in info:
            index = info.find("[")
            info = info[:index]
            meta = info[index:]
        try:
            validate(zone, info)
        except Exception as message:
            print(message)
            sys.exit()
        if zone == "nb_drones":
            data[zone] = info
        elif (zone == "start_hub" or zone == "end_hub" or zone == "hub"):
            hub: dict[str, (tuple, dict)] = {}
            if "nb_drones" not in data.keys():
                print("Error: first line must be the number of"
                      " drones, defined as 'nb_drones: <number>'")
                sys.exit()
            name, x, y = info.strip("", 3)
            hub["coords"] = (x, y)
            if meta:
                meta_dict = dict(data.split("=") for data in data.split()) 
                if ((zone == "start_hub" or zone == "end_hub")
                   and "max_drones" in meta_dict.keys() and 
                   meta_dict["max_drones"] < data["nb_drones"]):
                    print("Error: Zone is too restricted to handle"
                          " all drones in start/end hub")
                    sys.exit()
                hub["metadata"] = meta_dict
            data[zone][name] = hub
        else:
            hub1, hub2 = info.split("-")
            if (hub1 not in data["hubs"].keys()
               or hub2 not in data["hubs"].keys()):
                print(f"{info} is not a valid connection couldn't find"
                      " one of the hubs")
                sys.exit()
            capacity = 1
            if meta:
                value_index = meta.find("=")
                value = meta[value_index + 1:]
                capacity = value
            data[zone][info] = capacity
    return data
