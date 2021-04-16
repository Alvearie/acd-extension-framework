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
from fastapi import Request

from acd_annotator_python.container_model.main import Concept, UnstructuredContainer
from acd_annotator_python import service_utils
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.acd_annotator import ACDAnnotator

base_logger = logging.getLogger(__name__)

# new concepts will be created with this concept unique identifier (CUI)
MATCH_CUI = 'RegexAnnotator'
# new concepts will be created with this type
MATCH_TYPE = 'RegexType'


class RegexAnnotator(ACDAnnotator):
    """
    An annotator that creates Concepts and adds them to the container whenever
    one of the regex patterns is matched.
    """

    def __init__(self, search_patterns):
        """
        Create a RegexAnnotator with the given list of patterns
        :param search_patterns:
        """
        super().__init__()
        self.search_patterns = search_patterns
        base_logger.info("Initializing RegexAnnotator with patterns: %s", search_patterns)

    def on_startup(self, fastapi_app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        pass

    async def is_healthy(self, fastapi_app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        return True

    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        """
        A very simple annotator that creates concepts that match the given regex, assigning them the
        indicated cui and type.
        :param unstructured_container: an UnstructuredContainer to be processed and modified in-place.
        :param request: a fastapi.Request object for the current request
        :return: none
        """
        # decorate the logger with information about the correlation id, which allows you to track a single
        # request across the logs of multiple acd annotators.
        logger = service_utils.ACDLoggerAdapter(base_logger, request)

        data = unstructured_container.data
        text = unstructured_container.text
        if data is not None and text is not None:
            pattern_match_counts = collections.Counter()
            for search_pattern in self.search_patterns:
                # add a custom concept to the container over the first occurrence of "patient"
                for match in re.finditer(search_pattern, text):
                    pattern_match_counts[search_pattern] += 1
                    match_begin, match_end = match.span()
                    match_text = text[match_begin:match_end]

                    new_concept = Concept(cui=MATCH_CUI,
                                          begin=match_begin,
                                          end=match_end,
                                          coveredText=match_text,
                                          type=MATCH_TYPE
                                          )
                    if data.concepts is None:
                        data.concepts = []
                    data.concepts.append(new_concept)

        # log how many times each regex got matched in this doc
        logger.debug("RegexAnnotator pattern match counts: %s", pattern_match_counts)


regex_patterns = [r'\b[Pp]atients?\b', r'\b[Ss]ubjects?\b', r'\b[Ii]npatients?\b',
                  r'\b[Oo]utpatients?\b', r'\b[Ss]ufferers?\b']


# This is our ASGI app, which can be run by any of a number of ASGI server implementations.
# Note: We alternatively could instantiate app=factory.build() directly and uvicorn could run that,
# but creating our app as a factory allows uvicorn to load in environment variables,
# logging configuration, etc, before our app is constructed.
def app():
    return fastapi_app_factory.build(RegexAnnotator(regex_patterns))


# Debug your app in a python IDE debugger using the following
if __name__ == "__main__":
    import os
    import uvicorn
    import acd_annotator_python
    from acd_annotator_python import service_utils
    uvicorn.run("example_apps.regex_annotator:app", host="localhost", port=8000, reload=True,
                reload_dirs=[".", os.path.dirname(acd_annotator_python.__file__)],  # watch for changes
                factory=True,
                log_config=service_utils.DEFAULT_LOG_SETTINGS
                )
