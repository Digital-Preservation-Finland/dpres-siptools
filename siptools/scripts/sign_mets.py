"""Command line tool for creating digital signatures for SIP"""

import sys
import os
import click
import dpres_signature.signature

@click.command()
@click.option(
        "--workspace", default="./workspace",
        type=click.Path(exists=True),
        metavar='<WORKSPACE PATH>',
        help="Workspace directory that contains mets.xml file and where "
             "signature.sig is written."
    )
@click.argument("sign_key", type=click.Path(exists=True))
def main(workspace, sign_key):
    """The main method for sign_mets"""
    signature = sign_mets(workspace, sign_key)
    print "sign_mets created file: %s" % signature

    return 0

def sign_mets(workspace, key_path):
    """
    Create digital signature (signature.sig) for METS file.

    SIGN_KEY: Path for private key.

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
