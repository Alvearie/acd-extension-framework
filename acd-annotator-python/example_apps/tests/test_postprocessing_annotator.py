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
from example_apps.postprocessing_annotator import PostprocessingAnnotator
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
    # codes below ordered from less->more specific: ["cancer", "lung cancer", "non-small-cell lung cancer"]
    LUNG_CANCER_CODE_HIERARCHY = ['363346000', '93880001', '254637007']
    app = fastapi_app_factory.build(PostprocessingAnnotator(LUNG_CANCER_CODE_HIERARCHY))
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
            "unstructured": [
                {
                    "text": "Prior Medical History:\n"
                            "Lung cancer suspicion since a clinical exam in January.\n\n"
                            "Diagnosis: \n"
                            "non-small cell lung cancer.\n",
                    "data": {
                        "attributeValues": [
                            {
                                "name": "Diagnosis",
                                "preferredName": "primary malignant neoplasm of lung",
                                "source": "demo attributes",
                                "begin": 23,
                                "end": 34,
                                "coveredText": "Lung cancer",
                                "icd9Code": "162.9",
                                "icd10Code": "C34.90,C34.9",
                                "sectionNormalizedName": "Prior Medical History",
                                "snomedConceptId": "93880001",
                                "ccsCode": "19",
                                "hccCode": "9",
                                "sectionSurfaceForm": "Prior Medical History"
                            },
                            {
                                "name": "Diagnosis",
                                "preferredName": "non-small cell lung cancer",
                                "source": "demo attributes",
                                "begin": 92,
                                "end": 118,
                                "coveredText": "non-small cell lung cancer",
                                "icd9Code": "162.9",
                                "icd10Code": "C34.9,C34.90",
                                "sectionNormalizedName": "Diagnosis",
                                "snomedConceptId": "254637007",
                                "ccsCode": "19",
                                "hccCode": "9",
                                "sectionSurfaceForm": "Diagnosis"
                            }
                        ]
                    }}]}
        example_json_response = {
            "unstructured": [
                {
                    "data": {
                        "attributeValues": [
                            {
                                "begin": 92,
                                "end": 118,
                                "coveredText": "non-small cell lung cancer",
                                "name": "Diagnosis",
                                "preferredName": "non-small cell lung cancer",
                                "source": "demo attributes",
                                "icd9Code": "162.9",
                                "icd10Code": "C34.9,C34.90",
                                "ccsCode": "19",
                                "sectionNormalizedName": "Diagnosis",
                                "hccCode": "9",
                                "sectionSurfaceForm": "Diagnosis",
                                "snomedConceptId": "254637007"
                            }
                        ]
                    },
                    "text": "Prior Medical History:\n"
                            "Lung cancer suspicion since a clinical exam in January.\n\n"
                            "Diagnosis: \n"
                            "non-small cell lung cancer.\n"
                }
            ]
        }

        request = json.dumps(example_json)
        response = client.post(BASE_URL + "/process", request, headers=headers)
        assert response.status_code == 200
        assert response.json() == example_json_response
