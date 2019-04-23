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
         "signature.sig is written. Defaults to ./workspace/"
    )
@click.argument("sign_key", type=click.Path(exists=True))
def main(sign_key, workspace):
    """Script for signing the Submission Information Package with a
    digital signature. This script creates signature.sig file.

    SIGN_KEY: Private key of the signature keypair.
    """
    run(sign_key, workspace)

    return 0


def run(sign_key, workspace="./workspace"):
    """Script for signing the Submission Information Package with a
    digital signature. This script creates signature.sig file.
    """
    signature = sign_mets(sign_key, workspace)
    print "sign_mets created file: %s" % signature


def sign_mets(key_path, workspace):
    """Sign METS file, which signs the whole package"""
    signature_path = os.path.join(workspace, 'signature.sig')
    signature = dpres_signature.signature.create_signature(signature_path,
                                                           key_path,
                                                           ['mets.xml'])

    with open(signature_path, 'w') as outfile:
        outfile.write(signature)

    return signature_path


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
