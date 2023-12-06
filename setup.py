from setuptools import setup, find_packages

"""
https://python-packaging.readthedocs.io/en/latest/minimal.html
https://packaging.python.org/en/latest/specifications/declaring-project-metadata/

Once:

$ python3 -m pip install --upgrade build
$ python3 -m pip install --upgrade twine

Each iteration:

$ python3 -m build
$ python3 -m twine upload --repository pypi dist/rdascore-x.y.z*.*

"""

setup(
    name="rdascore",
    version="2.0.1",
    description="Redistricting analytics for scoring ensembles of redistricting plans",
    url="https://github.com/dra2020/rdascore",
    author="alecramsay",
    author_email="a73cram5ay@gmail.com",
    license="MIT",
    packages=[
        "rdascore",
    ],
    install_requires=[
        "pytest",
        "rdabase",
        "rdapy",
    ],
    zip_safe=False,
)
