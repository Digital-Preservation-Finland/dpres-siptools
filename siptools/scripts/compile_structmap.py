""""Command line tool for compile structmap"""

import argparse
import os
import siptools.xml.mets as m

def parse_arguments(arguments):
        """ Create arguments parser and return parsed command line argumets"""

        parser = argparse.ArgumentParser(description="Tool for importing files"
            "which generates digital objects")
        parser.add_argument('input_directory', type=str ,help="Input directory to create a structMap")
        parser.add_argument('--workspace', type=str, default='./workspace/',
                help="Destination file")
        parser.add_argument('--stdout', help='Print output to stdout')
        return parser.parse_args(arguments)

def main(arguments=None):
    """The main method for argparser"""
    args = parse_arguments(arguments)

    source_path = os.path.abspath(args.input_directory)

    for root, dirs, files in os.walk(source_path, topdown=False):
        for name in dirs:
            #m.div(name, None, None, name, None, None, None, None, None, None)
            print "dirs: %s" % name


    return 0

if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
