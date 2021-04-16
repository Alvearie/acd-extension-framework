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
from example_apps.extras.spacy_sentence_annotator import SpacySentenceAnnotator
from fastapi.testclient import TestClient

# TODO: load from env
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
    app = fastapi_app_factory.build(SpacySentenceAnnotator())
    with TestClient(app) as client:
        yield client
    print("shutting down test server")


class TestMain:

    def test_status(self, client):
        response = client.get(BASE_URL + "/status/health_check")
        assert response.status_code == 200

    def test_process(self, client):
        # positive example with two matches
        example_json = {"unstructured": [{
            "text": "Mean patient age is 43 years old. Patients have no hx of heart problems."
        }]}
        example_json_response = {
          "unstructured": [
            {
              "data": {
                "sentences": [
                  {
                    "type": "SpacySentence",
                    "begin": 0,
                    "end": 34,
                    "coveredText": "Mean patient age is 43 years old. "
                  },
                  {
                    "type": "SpacySentence",
                    "begin": 34,
                    "end": 72,
                    "coveredText": "Patients have no hx of heart problems."
                  }
                ]
              },
              "text": "Mean patient age is 43 years old. Patients have no hx of heart problems."
            }
          ]
        }
        request = json.dumps(example_json)
        response = client.post(BASE_URL + "/process", request)
        assert response.status_code == 200
        assert response.json() == example_json_response
