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
        try:
            data = parse(f)
        except ValueError as message:
            raise ValueError(message)
    test = Grid(data)
    test.visualiser()


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as message:
        print(message)
        sys.exit(1)
