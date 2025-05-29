#!/usr/bin/env python
# original code from https://gist.github.com/pwithnall/7bc5f320b3bdf418265a

"""
Gets the current version number.
If in a git repository, it is the current git tag.
Otherwise it is the one contained in the __init__ file.

To use this script, simply import it in your setup.py file
and use the results of get_version() as your package version:

    from version import *

    setup(
        ...
        version=get_version(),
        ...
    )
"""

import codecs
import os
import subprocess


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def version_from_init(rel_path="__init__.py"):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")


def get_version():
    # get git root directory

    # check if "CI" is set, if so, use the version from __init__.py
    if os.environ.get("CI") == "true":
        print("CI environment detected, using __init__.py")
        return version_from_init()

    try:
        cmd = "git describe --tags --match v[0-9]*".split()
        version = subprocess.check_output(cmd).decode().strip()

        # PEP 386 compatibility
        if "-" in version:
            version = ".post".join(version.split("-")[:2])

        # Don't declare a version "dirty" merely because a time stamp has
        # changed. If it is dirty, append a ".dev1" suffix to indicate a
        # development revision after the release.
        with open(os.devnull, "w", encoding="utf8") as fd_devnull:
            subprocess.call(["git", "status"], stdout=fd_devnull, stderr=fd_devnull)

        cmd = "git diff-index --name-only HEAD".split()

        dirty = subprocess.check_output(cmd).decode().strip()

        if dirty != "":
            version += ".dev1"

    except Exception as e:
        # Not a git repository or something went wrong with git
        print(f"{e}\nUnable to get version number from git tags, using __init__.py")
        version = version_from_init()

    return version


if __name__ == "__main__":
    print(get_version())
