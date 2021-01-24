from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="alleycat-core",
    version="0.1.0",
    author="Xavier Cho",
    author_email="mysticfallband@gmail.com",
    description="Core packages of AlleyCat framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mysticfall/alleycat/core",
    packages=find_namespace_packages(".", include=["alleycat.*"]),
    install_requires=["returns==0.17.0", "validator-collection==1.5.0", "dependency-injector==4.36.2"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ]
)
