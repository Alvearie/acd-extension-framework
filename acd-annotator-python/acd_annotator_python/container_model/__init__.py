# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
import os

# Direct validation to be done permissively when possible, allowing some non-critical problems
# to log warnings instead of throwing errors
PERMISSIVE_MODE = os.getenv('com_ibm_watson_health_common_python_permissive_validation', 'true').lower() == 'true'
