# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
import json
from fastapi import Request
from fastapi.testclient import TestClient

from acd_annotator_python.container_model.main import UnstructuredContainer
from acd_annotator_python.acd_annotator import ACDAnnotator
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.fastapi_app_factory import DEFAULT_BASE_URL as BASE_URL
from acd_annotator_python.fastapi_app_factory import EXAMPLE_REQUEST


class NoopAnnotator(ACDAnnotator):
    """A simple annotator that does nothing for testing purposes"""
    def on_startup(self, app):
        pass

    async def is_healthy(self, app):
        return True

    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        pass


class ErrorAnnotator(ACDAnnotator):
    """A simple annotator that throws errors for testing purposes"""
    def on_startup(self, app):
        pass  # can't throw an error here or the server fails to start

    async def is_healthy(self, app):
        raise RuntimeError("mock error")

    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        raise RuntimeError("mock error")


class InvalidContainerModelErrorAnnotator(ErrorAnnotator):
    """A simple annotator that throws a validation error for testing purposes.
    Simulates the situation where a custom annotator produces invalid container model,
    which is a 500."""
    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        # make an invalid edit
        unstructured_container.data.concepts[0].begin = 'b'


class TestMain:
    def test_status(self):
        with TestClient(fastapi_app_factory.build(NoopAnnotator())) as client:
            response = client.get(BASE_URL + "/status/health_check")
            assert response.status_code == 200

    def test_status_error(self):
        with TestClient(fastapi_app_factory.build(ErrorAnnotator())) as client:
            response = client.get(BASE_URL + "/status/health_check")
            assert response.status_code == 500

    def test_invalid_container_error(self):
        example_container = {
            "unstructured": [
                {
                    "text": "The patient reports severe bowel discomfort for the last week.",
                    "data": {
                        "concepts": [
                            {
                                "cui": "C1096594",
                                "preferredName": "bowel discomfort",
                                "semanticType": "sosy",
                                "source": "umls",
                                "sourceVersion": "2020AA",
                                "type": "umls.SignOrSymptom",
                                "begin": 27,
                                "end": 43,
                                "coveredText": "bowel discomfort",
                                "vocabs": "CHV"
                            }
                        ]
                    }
                }
            ]
        }
        with TestClient(fastapi_app_factory.build(InvalidContainerModelErrorAnnotator())) as client:
            response = client.post(BASE_URL + "/process", json.dumps(example_container))
            assert response.status_code == 500

    def test_process(self):
        with TestClient(fastapi_app_factory.build(NoopAnnotator())) as client:
            request = ""
            response = client.post(BASE_URL + "/process", request)
            assert response.status_code == 400

            # ignore empty container
            request = json.dumps({})
            response = client.post(BASE_URL + "/process", request)
            assert response.status_code == 200
            assert response.text == request

            # real container
            request = json.dumps(EXAMPLE_REQUEST)
            response = client.post(BASE_URL + "/process", request)
            assert response.status_code == 200

            # we require an unstructured container at the top level. You can
            # add unknown stuff to the inside and we'll pass it through, but not at the top level.
            request = json.dumps({"bogus": {}})
            response = client.post(BASE_URL + "/process", request)
            assert response.status_code == 400

    def test_process_error(self):
        with TestClient(fastapi_app_factory.build(ErrorAnnotator())) as client:
            # ErrorAnnotator should blow up when it sees a real request
            request = json.dumps(EXAMPLE_REQUEST)
            response = client.post(BASE_URL + "/process", request)
            assert response.status_code == 500


# enable to debug
if __name__ == '__main__':
    TestMain().test_process_error()
