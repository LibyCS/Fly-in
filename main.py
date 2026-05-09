import sys
from parser import parse
from layout import Grid


def main() -> None:
    if len(sys.argv) < 2:
        raise FileNotFoundError("Error: Input File was not given"
                                " Please run as:\nmake run 'input.txt'")
    elif len(sys.argv) > 2:
        raise FileNotFoundError("Error too many files were given"
                                " Please run as:\nmake run 'input.txt'")
    with open(sys.argv[1]) as f:
        data = parse(f)
    test = Grid(data)
    test.visualiser()


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as message:
        print(message)
        sys.exit()
