import sys

from calculator import add, divide, multiply, subtract

OPS = {"add": add, "sub": subtract, "mul": multiply, "div": divide}


def main(argv):
    if len(argv) != 3 or argv[0] not in OPS:
        print("usage: python -m calculator {add|sub|mul|div} A B")
        return 1
    op, a, b = argv[0], float(argv[1]), float(argv[2])
    print(OPS[op](a, b))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
