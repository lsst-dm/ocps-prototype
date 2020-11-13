.. OCPS Job Manager documentation master file, created by
   sphinx-quickstart on Wed Oct 21 09:46:45 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

OCPS Job Manager Documentation
============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Readme
   Development
   api/Readme

Links
------------------------------

* `DMTN-133: OCS driven data processing <https://dmtn-133.lsst.io>`_
* `DMTN-143: Image Capture Simplification <https://dmtn-143.lsst.io>`_

Documentation system
---------------------------

The documentation is powered by `Sphinx <https://www.sphinx-doc.org/>`_, using the reStructuredText (reST) format. 

Install `Sphinx <https://www.sphinx-doc.org/en/master/usage/installation.html>`_ using ::

   apt-get install python3-sphinx

or on MacOS::

   brew install sphinx-doc

With Sphinx installed locally, you can build the HTML files using ::

  cd $REPO_ROOT/docs/
  ./build_docs

Then open ``_build/html/index.html`` in your browser.

For the best viewing experience, (e.g. to view the `rendered API spec <api/spec.html>`_ using the `Swagger UI <https://editor.swagger.io/>`_), use `Docker <https://docs.docker.com/get-docker/>`_ to run a local webserver ::

   docker run --rm -p 8080:80 -v "$PWD/_build/html":/usr/share/nginx/html nginx:1.19.0

and then open http://localhost:8080 in your browser.
