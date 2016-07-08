"""Sample implementation for parsing command line arguments"""

import sys
import argparse


def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    for x in range(args.print_count):
        print args.message


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(description="A short description of this "
                                     "program")

    parser.add_argument('message', help="Positional argument which "
                        "is needed for program to start.")
    parser.add_argument('-n', dest='print_count', type=int, default=3,
                        help='Optional integer argument which defaults to 3.')

    return parser.parse_args(arguments)

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
