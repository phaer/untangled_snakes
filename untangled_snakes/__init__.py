import argparse
import logging

arg_parser = argparse.ArgumentParser()
logging.basicConfig(level=logging.INFO)


def main():
    args = arg_parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()
