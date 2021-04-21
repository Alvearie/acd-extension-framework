# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "acd-annotator-python",
    version = "0.0.1",
    description = "Extension framework for Annotator for Clinical Data (ACD) in python",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/Alvearie/acd-extension-framework",
    project_urls={
        "Bug Tracker": "https://github.com/Alvearie/acd-extension-framework/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    license="Apache License 2.0",
    python_requires = ">=3.8",
    install_requires = [
        # Note: this is similar to, but slightly different from requirements.txt
        # in that it attempts to be minimal and permissive whereas requirements 
        # freezes a single configuration known to work.
        "fastapi>=0.63.0",  # web server
        "uvicorn>=0.13.0",  # ASGI server
        "pydantic>=1.7.0",  # object modeling with parsing/validation
        "psutil>=5.8.0",  # report process stats
    ],
    extras_require = {
        "tests": [
            "pytest>=6.2.0",  # test framework
        ]
    },
    # point to the parent dir that contains the module we are looking for
    package_dir={"": "."},
    # Find acd_annotator_python and any of its submodules, but not siblings like example_apps
    packages=setuptools.find_packages(include=["acd_annotator_python","acd_annotator_python.*"]),
    # this file is resolved relative to the module acd_annotator_python
    package_data={"acd_annotator_python": ['defaultLogSettings.json']},
)

