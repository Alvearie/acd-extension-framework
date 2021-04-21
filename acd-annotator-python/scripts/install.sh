# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
# create a virtualenv sandbox if it doesn't already exist 
if [ ! -e .venv ]; then
  python3 -m venv .venv
fi

# activate the virtualenv sandbox and install prereqs from requirements/base.txt
source .venv/bin/activate && 
  pip3 install -r ./requirements/base.txt 
