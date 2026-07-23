import sys
from parser import Parse
from visualiser import Grid, GridVisualiser, DroneVisualiser


def main() -> None:
    """
    the main program that calls the necessary functions
    """
    if len(sys.argv) < 2:
        raise FileNotFoundError("Error: Input File was not given"
                                " Please run as:\nmake run FILE='input.txt'")
    elif len(sys.argv) > 2:
        raise FileNotFoundError("Error too many files were given"
                                " Please run as:\nmake run 'input.txt'")
    with open(sys.argv[1]) as f:
        try:
            data = Parse().parse(f)
        except ValueError as message:
            raise ValueError(message)
    layout = Grid(data)
    plot, scale = GridVisualiser(layout).visualise_layout()
    DroneVisualiser(layout, plot, scale).visualise()


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as message:
        print(message)
        sys.exit(1)
