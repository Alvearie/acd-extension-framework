# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import json
import pytest

from acd_annotator_python import fastapi_app_factory
from example_apps.bmi_annotator import BMIAnnotator
from fastapi.testclient import TestClient

from acd_annotator_python.fastapi_app_factory import DEFAULT_BASE_URL as BASE_URL


@pytest.fixture(scope="class", autouse=True)
def client():
    """
    This fixture is run once per test class, and it
    gives us a chance to do setup/teardown logic
    using "with" syntax. This is important because
    TestClient only calls on_event("startup") in the
    context of "with" syntax (when client.__enter__() is called)
    :return:
    """
    print("starting test server")
    app = fastapi_app_factory.build(BMIAnnotator())
    with TestClient(app) as client:
        yield client
    print("shutting down test server")


class TestMain:

    def test_status(self, client):
        response = client.get(BASE_URL + "/status/health_check")
        assert response.status_code == 200

    def test_process(self, client):
        headers = {'content-type': 'application/json'}
        # positive example with two matches
        example_json = {
            "structured": [
                {
                    "data": {
                        "heightInches": 74,
                        "weightPounds": 170
                    }
                }
            ]
        }
        example_json_response = {
            "structured": [
                {
                    "data": {
                        "heightInches": 74,
                        "weightPounds": 170,
                        "bmi": 21.8
                    }
                }
            ]
        }
        request = json.dumps(example_json)
        response = client.post(BASE_URL + "/process", request, headers=headers)
        assert response.status_code == 200
        assert response.json() == example_json_response
