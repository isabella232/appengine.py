from __future__ import with_statement

import os
import subprocess
import sys


def install():
    try:
        value = int(os.environ.get('INSTALL_APPENGINE', '0'))
    except ValueError:
          value = 0

    install_appengine = bool(value)

    if install_appengine:
        filename = os.path.join(
          os.path.dirname(__file__),
          os.path.pardir,
          'appengine.py'
        )
        subprocess.call([sys.executable, filename])
