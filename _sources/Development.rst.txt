Development
=======================================

Documentation system
---------------------------

Sphinx
^^^^^^^^^^^^
The documentation is powered by `Sphinx <https://www.sphinx-doc.org/>`_, using the reStructuredText (reST) format. 

`Install Sphinx <https://www.sphinx-doc.org/en/master/usage/installation.html>`_ using ::

   apt-get install python3-sphinx

or on MacOS::

   brew install sphinx-doc

With Sphinx installed locally, you can build the HTML files using ::

  cd $REPO_ROOT/docs/
  ./build_docs

Then open ``_build/html/index.html`` in your browser.

.. For the best viewing experience, (e.g. to view the `rendered API spec <api/spec.html>`_ using the `Swagger UI <https://editor.swagger.io/>`_), use `Docker <https://docs.docker.com/get-docker/>`_ to run a local webserver ::

..    docker run --rm -p 8080:80 -v "$PWD/_build/html":/usr/share/nginx/html nginx:1.19.0

.. and then open http://localhost:8080 in your browser.

File editors and viewers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.drawio`` files require the open source editor from https://www.diagrams.net/.

There is a very helpful VS Code extension called `reStructuredText <https://github.com/vscode-restructuredtext/vscode-restructuredtext>`_ that provides a live preview of reST files using the Sphinx theme from the most recent build.

.. image:: images/vscode_plugin.png

Development environment
----------------------------------------

Configure local workstation according to the SSH instructions at https://developer.lsst.io/services/lsst-login.html#lsst-login-connect. I installed ``kinit`` and executed this first::

  kinit manninga@NCSA.EDU

I added the following to a new file ``~/.ssh/config``::

  # Set common config for the lsst-login nodes
  Host lsst-login*
    # if your account on your local workstation/laptop does not match your LSST username, indicate the latter should be used;
    # substitute your own NCSA username
    User ncsausername
    # allow use of a Kerberos ticket on your local machine for auth to LSST machines
    GSSAPIAuthentication yes
    # prefer Kerberos ticket auth, amongst other possibilities (order/include others as desired)
    PreferredAuthentications gssapi-with-mic,keyboard-interactive,password
    # forward your local Kerberos ticket to the login node if you need to continue to another LSST server after the login
    GSSAPIDelegateCredentials yes
    # configure OpenSSH Control Master "multiplexing" (to allow reuse of an initial connection)
    ControlMaster auto
    ControlPath ~/.ssh/cm_socket_%r@%h:%p
    ControlPersist 5m

  # Define aliases onto full hostnames for each login node
  Host lsst-login01
    HostName lsst-login01.ncsa.illinois.edu
  Host lsst-login02
    HostName lsst-login02.ncsa.illinois.edu
  Host lsst-login03
    HostName lsst-login03.ncsa.illinois.edu

I logged in using a local terminal session and authenticated with my password and Duo 2FA. Subsequently I could browse remote files on ``lsst-login`` using Nautilus by opening ``sftp://manninga@lsst-login``.
