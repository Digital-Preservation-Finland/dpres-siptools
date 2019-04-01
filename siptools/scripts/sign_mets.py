"""Command line tool for creating digital signatures for SIP"""

import sys
import os
import click
import dpres_signature.signature

@click.command()
@click.option(
        "--workspace", default="./workspace",
        help="Workspace directory that contains mets.xml file and where "
             "signature.sig is written."
    )
@click.argument("sign_key", type=str)
def main(workspace, sign_key):
    """The main method for sign_mets"""
    signature = sign_mets(workspace, sign_key)
    print "sign_mets created file: %s" % signature

    return 0

def sign_mets(workspace, key_path):
    """Sign mets.xml file in workspace

    :workspace: directory that contains mets.xml
    :key_path: path to signing key
    :returns: path of created signature
    """
    signature_path = os.path.join(workspace, 'signature.sig')
    signature = dpres_signature.signature.create_signature(signature_path,
                                                           key_path,
                                                           ['mets.xml'])

    with open(signature_path, 'w') as outfile:
        outfile.write(signature)

    return signature_path


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
