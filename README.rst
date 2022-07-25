Base16 Shell Preview
====================

|PyPi Version|

A tool to preview and enable `Base16 Shell`_ themes in your terminal.

.. image:: https://raw.githubusercontent.com/nvllsvm/base16-shell-preview/master/preview.gif
   :alt: Preview GIF

Installation
------------

Requires Python 3.6+. Base16 Shell must also be present.

.. code:: shell

    pip install base16-shell-preview

Usage
-----

Before running, ensure that the ``BASE16_SHELL`` environment variable is set to the local
`Base16 Shell`_ path or that a theme is already symlinked to ``~/.base16_theme``.

.. code::

   base16-shell-preview -h
   usage: base16-shell-preview [-h] [--version] [--sort-bg]

   keys:
     up/down      move 1
     pgup/pgdown  move page
     home/end     go to beginning/end
     q            quit
     enter        enable theme and quit

   optional arguments:
     -h, --help  show this help message and exit
     --version   show program's version number and exit
     --sort-bg   sort themes by background (darkest to lightest)


.. |PyPi Version| image:: https://img.shields.io/pypi/v/base16_shell_preview.svg?
   :target: https://pypi.python.org/pypi/base16_shell_preview

.. _Base16 Shell: https://github.com/chriskempson/base16-shell
