# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
import os

# should validation be done permissively, allowing some non-critical problems
# to log warnings instead of throw errors?
PERMISSIVE_MODE = os.getenv('com_ibm_watson_health_common_python_permissive_validation', 'false').lower() == 'true'
