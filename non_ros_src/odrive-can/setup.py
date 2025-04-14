# type: ignore

"""The setup script."""


import codecs
import os
import os.path

from setuptools import find_packages, setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")


# please keep this lean and mean. Add dev requirements to .devcontainer/requirments.txt
requirements = ["click", "cantools", "python-can", "coloredlogs"]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Jev Kuznetsov",
    author_email="jev.kuznetsov@gmail.com",
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.10",
    ],
    description="Use odrive motion controller with CAN inteface",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    install_requires=requirements,
    keywords="",
    name="odrive_can",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    package_data={
        "odrive_can": ["dbc/*"],
    },
    test_suite="tests",
    tests_require=test_requirements,
    url="",
    version=get_version("src/odrive_can/__init__.py"),
    # zip_safe=False,
    entry_points={"console_scripts": ["odrive_can=odrive_can.cli:cli"]},
)
