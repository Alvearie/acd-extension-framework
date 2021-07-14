# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
import collections
import re
import logging
import sys

from fastapi import Request

from acd_annotator_python.container_model.main import Concept, UnstructuredContainer
from acd_annotator_python import service_utils
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.acd_annotator import ACDAnnotator

logger = logging.getLogger(__name__)

# codes below ordered from less->more specific: ["cancer", "lung cancer", "non-small-cell lung cancer"] 
LUNG_CANCER_CODE_HIERARCHY = ['363346000', '93880001', '254637007']

# greatly simplified container (usually this will have concepts, insight model
# scores, etc. But keeping things simple and small for the sample).
EXAMPLE = {
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


class CodeResolutionAnnotator(ACDAnnotator):
    """
    This annotator demonstrates a use case where we want to integrate information from across
    the entire document.

    In this case we have a known hierarchy of specificity among our attributes.
    ACD has identified several candidates across a document, but in order to simplify downstream consumption
    we want to remove all but the most specific codes.
    """

    def __init__(self, snomed_code_hierarchy):
        """
        Create a CodeResolutionAnnotator with the given list of patterns
        :param search_patterns:
        """
        super().__init__()
        self.snomed_code_hierarchy = snomed_code_hierarchy
        logger.info("Initializing CodeResolutionAnnotator with codes: %s", snomed_code_hierarchy)

    def on_startup(self, fastapi_app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        pass

    async def is_healthy(self, fastapi_app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        return True

    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        """
        A very simple annotator that looks through attributes and removes all but the most
        specific snomed codes according to a simple hierarchy.
        :param unstructured_container: an UnstructuredContainer to be processed and modified in-place.
        :param request: a fastapi.Request object for the current request
        :return: none
        """

        data = unstructured_container.data
        text = unstructured_container.text
        if data is not None and text is not None:
            # this is the index of the most specific snomed codes we've found so far in our simple hierarchy
            most_specific_code_idx = None

            if data.attributeValues is not None:

                # Pass 1: figure out which is the most specific code in the container
                for attribute in data.attributeValues:
                    snomed_codes = attribute.snomedConceptId
                    if snomed_codes is not None:
                        # medical codes can be comma-delimited strings
                        for snomed_code in snomed_codes.split(","):
                            if snomed_code in self.snomed_code_hierarchy:
                                most_specific_code_idx = max(most_specific_code_idx or -1,
                                                         self.snomed_code_hierarchy.index(snomed_code))

                # Pass 2: filter out any codes that are subsumed by a more specific code
                if most_specific_code_idx is not None:
                    most_specific_code = self.snomed_code_hierarchy[most_specific_code_idx]

                    attributes_to_remove = []
                    for attribute in data.attributeValues:
                        snomed_codes = attribute.snomedConceptId
                        if snomed_codes is not None:
                            # medical codes can be comma-delimited strings
                            for snomed_code in snomed_codes.split(","):
                                if snomed_code in self.snomed_code_hierarchy and snomed_code != most_specific_code:
                                    attributes_to_remove.append(attribute)
                    for attribute in attributes_to_remove:
                        data.attributeValues.remove(attribute)

                    # log how many attributes were removed from this doc
                    logger.debug("CodeResolutionAnnotator removed %s attributes", len(attributes_to_remove))


# This is our ASGI app, which can be run by any of a number of ASGI server implementations.
# Note: We alternatively could instantiate app=factory.build() directly and uvicorn could run that,
# but creating our app as a factory allows uvicorn to load in environment variables,
# logging configuration, etc, before our app is constructed.
def app():
    return fastapi_app_factory.build(CodeResolutionAnnotator(LUNG_CANCER_CODE_HIERARCHY), example_request=EXAMPLE)


# Debug your app in a python IDE debugger using the following
if __name__ == "__main__":
    import os
    import uvicorn
    import acd_annotator_python
    from acd_annotator_python import service_utils

    uvicorn.run("example_apps.code_resolution_annotator:app", host="localhost", port=8000, reload=True,
                reload_dirs=[".", os.path.dirname(acd_annotator_python.__file__)],  # watch for changes
                factory=True,
                log_config=service_utils.DEFAULT_LOG_SETTINGS
                )
