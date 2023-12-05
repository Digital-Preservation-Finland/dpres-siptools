"""Command line tool for creating digital signatures for SIP"""

import os
import sys

import click

import dpres_signature.signature

click.disable_unicode_literals_warning = True


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
    sign_mets(sign_key, workspace)

    return 0


def sign_mets(sign_key, workspace="./workspace"):
    """
    Script for signing the Submission Information Package with a
    digital signature. This script creates signature.sig file.

    :sign_key: Signature key for signing
    :workspace: Workspace path
    """
    signature = dpres_signature.signature.create_signature(
        workspace, sign_key, ['mets.xml']
    )

    signature_path = os.path.join(workspace, 'signature.sig')
    with open(signature_path, 'wb') as outfile:
        outfile.write(signature)

    print("sign_mets created file: %s" % signature_path)


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
