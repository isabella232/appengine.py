#!/usr/bin/env python
from __future__ import with_statement

import argparse
import os
import stat
import StringIO
import sys
import urlparse
import zipfile

from distutils import version as dist_version

import yaml
import requests


USER_AGENT = 'appengine.py'
VERSION_URL = 'https://appengine.google.com/api/updatecheck'
OLD_VERSION_URL = 'http://googleappengine.googlecode.com/files/google_appengine_%s.zip'
NEW_DEPRECATED_URL = 'http://storage.googleapis.com/appengine-sdks/deprecated/%s/google_appengine_%%s.zip'
CURRENT_VERSION_URL = 'https://storage.googleapis.com/appengine-sdks/featured/google_appengine_%s.zip'
LAST_OLD_VERSION = dist_version.StrictVersion('1.8.9')
sdk_version_key = 'APPENGINEPY_SDK_VERSION'


def _extract_zip(archive, dest=None, members=None):
    """Extract the ZipInfo object to a real file on the path targetpath."""
    # Python 2.5 compatibility.
    dest = dest or os.getcwd()
    members = members or archive.infolist()

    for member in members:
        if isinstance(member, basestring):
            member = archive.getinfo(member)

        _extract_zip_member(archive, member, dest)


def _extract_zip_member(archive, member, dest):
    # Python 2.5 compatibility.
    target = member.filename
    if target[:1] == '/':
        target = target[1:]

    target = os.path.join(dest, target)

    # It's a directory.
    if target[-1:] == '/':
        parent = target[:-1]
        target = ''
    else:
        target = os.path.normpath(target)
        parent = os.path.dirname(target)

    if not os.path.exists(parent):
        os.makedirs(parent)

    if target:
        with open(target, 'w') as fh:
            fh.write(archive.read(member.filename))


def make_parser():
    """Returns a new option parser."""
    p = argparse.ArgumentParser()
    p.add_argument(
        'sdk',
        nargs='?',
        default=None
    )
    p.add_argument(
        '-p', '--prefix',
        metavar='DIR',
        help='Install SDK in DIR'
    )
    p.add_argument(
        '-b', '--bindir',
        metavar='DIR',
        help='Install tools in DIR'
    )
    p.add_argument(
        '-f', '--force',
        action='store_true',
        help='over-write existing installation',
        default=False
    )
    p.add_argument(
        '-n', '--no-bindir',
        action='store_true',
        default=False,
        help='Do not install tools in DIR'
    )

    return p


def parse_args(argv):
    """Returns a tuple of (opts, args) for arguments."""
    parser = make_parser()

    args = parser.parse_args(argv[1:])
    sdk = args.sdk
    # Use APPENGINEPY_SDK_VERSION if set.
    if not sdk and (sdk_version_key in os.environ):
        sdk = (os.environ[sdk_version_key],)

    return args, sdk


def check_version(url=VERSION_URL):
    """Returns the version string for the latest SDK."""
    response = requests.get(url)
    update_dict = yaml.load(response.text)
    release_version = update_dict['release']
    return release_version


def parse_sdk_name(name, current_version):
    """Returns a filename or URL for the SDK name.

    The name can be a version string, a remote URL or a local path.
    """
    # Version like x.y.z, return as-is.
    try:
        version = dist_version.StrictVersion(name)
        if version == current_version:
            # get from current.
            url = CURRENT_VERSION_URL
        elif version > LAST_OLD_VERSION:
            # newer SDK, not on code.google.com
            url = NEW_DEPRECATED_URL % ''.join(name.split('.'))
        else:
            # old SDK in code.google.com
            url = OLD_VERSION_URL

        return url % name
    except ValueError:
      # this means we couldn't parse as x.y.z
        pass

    # A network location.
    url = urlparse.urlparse(name)
    if url.scheme:
        return name

    # Else must be a filename.
    return os.path.abspath(name)


def open_sdk(url):
    """Open the SDK from the URL, which can be either a network location or
    a filename path. Returns a file-like object open for reading.
    """
    if urlparse.urlparse(url).scheme:
        return _download(url)
    else:
        return open(url)


def _download(url):
    """Downloads an URL and returns a file-like object open for reading,
    compatible with zipping.ZipFile (it has a seek() method).
    """
    file_download = requests.get(url)
    return StringIO.StringIO(file_download.content)


def install_sdk(filename, dest='.', overwrite=False):
    archive = zipfile.ZipFile(filename)
    _extract_zip(archive, dest=dest)

    return dest


def install_tools(src, dest, overwrite=False):
    tools = [name for name in os.listdir(src) if name.endswith('.py')]
    all_x = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

    for name in tools:
        src_name = os.path.join(src, name)
        new_mode = os.stat(src_name).st_mode | all_x
        os.chmod(src_name, new_mode)
        dest_name = os.path.join(dest, name)

        if overwrite:
            try:
                os.unlink(dest_name)
            except OSError:
                pass

        os.symlink(src_name, dest_name)

    return tools


def main(argv):
    args, sdk = parse_args(argv)
    current_version = check_version()
    version = sdk or current_version
    sdk_url = parse_sdk_name(version, current_version)

    archive = open_sdk(sdk_url)
    install_path = install_sdk(archive, dest=sys.prefix, overwrite=args.force)

    src = os.path.join(install_path, 'google_appengine')
    dest = args.prefix or os.path.join(sys.prefix, 'bin')
    install_tools(src, dest, overwrite=args.force)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
