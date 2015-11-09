The Digital Preservation SIP tools library
==========================================

Building Documentation
----------------------

Documentation is available in HTML and PDF formats. You may build the
documentation with commands::

    cd doc
    make html
    make pdf

Alternatively you may view the documentation with the `docserver` command::

    cd doc
    make docserver

Now point your browser to http://10.0.10.10:8000/html

After finishing the documentation you may stop the `docserver` with command::

    cd doc
    make killdocserver


