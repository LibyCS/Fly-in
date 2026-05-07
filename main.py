import sys
from parser import parse

def main() -> None:
    if sys.args < 2:
        raise FileNotFoundError("Error: Input File was not given"
                                "Please run as:\nmake run 'input.txt'")
    elif sys.args > 2:
        raise FileNotFoundError("Error too many files were given"
                                "Please run as:\nmake run 'input.txt'")
    with open(sys.args[1]) as f:
        parse(f)
    
if __name__ == "__main__":
    main()
