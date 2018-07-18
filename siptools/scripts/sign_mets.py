"""Command line tool for creating digital signatures for SIP"""

import sys
import os
import argparse
import dpres_signature.signature


def main(arguments=None):
    """The main method for sign_mets"""
    args = parse_arguments(arguments)
    signature = sign_mets(args.workspace, args.sign_key)
    print "sign_mets created file: %s" % signature

    return 0


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser(
        description="Create digital signature (signature.sig) for METS file.")

    parser.add_argument(
        "--workspace", default="workspace",
        help="Workspace directory that contains mets.xml file and where "
             "signature.sig is written."
    )
    parser.add_argument("sign_key", help="Path for private key")

    return parser.parse_args(arguments)


def sign_mets(workspace, key_path):
    """Sign mets.xml file in workspace

    :workspace: directory that contains mets.xml
    :key_path: path to signing key
    :returns: path of created signature
    """
    signature_path = os.path.join(workspace, 'signature.sig')
    dpres_signature.signature.signature_write(
        signature_path,
        key_path,
        None,
        ['mets.xml']
    )
    return signature_path


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
