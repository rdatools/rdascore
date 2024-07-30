from setuptools import setup, find_packages

setup(
    name="rdascore",
    version="2.6.2",
    description="Redistricting analytics for scoring ensembles of redistricting plans",
    url="https://github.com/rdatools/rdascore",
    author="alecramsay",
    author_email="a73cram5ay@gmail.com",
    license="MIT",
    packages=[
        "rdascore",
    ],
    install_requires=[
        "rdabase",
        "rdapy",
    ],
    zip_safe=False,
)
