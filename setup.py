import os
import subprocess
import sys

from setuptools import setup


def install():
    try:
        value = int(os.environ.get('INSTALL_APPENGINE', '0'))
    except ValueError:
          value = 0
    install_appengine = bool(value)

    if install_appengine:
        filename = os.path.join(os.path.dirname(__file__), 'appengine.py')
        subprocess.call([sys.executable, filename])


setup(
    name='appengine',
    version='0.2.2',
    description='Google App Engine re-packaged for PyPI',
    author='David Buxton',
    author_email='david@gasmark6.com',
    url='https://github.com/davidwtbuxton/appengine.py',
    scripts=['appengine.py'],
    cmdclass={'install': install},
    install_requires=[
        'PyYAML>=3.11',
        'requests==2.6.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ],
    entry_points="""
    [console_scripts]
    appengine.py = appengine.setup:install
    """
)
