# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import spacy
from fastapi import Request
import logging

from pydantic.typing import Optional, List

from acd_annotator_python.container_model.main import UnstructuredContainer, UnstructuredContainerData
from acd_annotator_python.container_model.common import BaseAnnotation
from acd_annotator_python import service_utils
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.acd_annotator import ACDAnnotator

logger = logging.getLogger(__name__)

# new concepts will be created with this type
MATCH_TYPE = 'SpacySentence'


class Sentence(BaseAnnotation):
    """Create a new acd datamodel object. This needs to be a pydantic object.
    It can achieve that by extending one of the container_model classes,
    or it can directly extend pydantic.BaseModel. """
    pass


# Let pydantic know we'll have a new list of Sentence at unstructured.data.sentences.
# This is not necessary in order to add data to the container model, but it makes
# the new field become a proper part of the pydantic object model, which lets it
# validate this field.
UnstructuredContainerData.add_fields(sentences=Optional[List[Sentence]])


class SpacySentenceAnnotator(ACDAnnotator):
    """
    An annotator that creates Section annotations over sentences identified by spacy tokenization.
    """

    def on_startup(self, fastapi_app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        fastapi_app.spacy_nlp = spacy.load("en_core_web_sm")

    async def is_healthy(self, fastapi_app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        return True

    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        """
        An annotator that injects sentence annotations into a container.
        :param unstructured_container: an UnstructuredContainer to be processed and modified in-place.
        :param request: a fastapi.Request object for the current request
        :return: none
        """
        data = unstructured_container.data
        text = unstructured_container.text
        if data is not None and text is not None:
            # run spacy nlp and get sentences out
            sentences = list(request.app.spacy_nlp(text).sents)
            # log the character/sentence ratio
            logger.debug("found %s sentences in %s chars", len(sentences), len(text))
            if sentences is not None and len(sentences) > 0:
                # spacy sentences are a list of tokens;
                # each token has an idx entry which is their begin character offset
                sentence_begins = [sent[0].idx for sent in sentences if sent is not None and len(sent) > 0]
                # spacy doesn't give us sentence ends, but we'll assume one sentence ends when the next begins
                sentence_ends = sentence_begins[1:] + [len(text)]
                # now create annotations over each sentence
                if data.sentences is None:
                    data.sentences = []
                for sent_begin, sent_end in zip(sentence_begins, sentence_ends):
                    # useful to return the covered_text for debugging, but it would probably be too verbose in practice.
                    sentence_text = text[sent_begin:sent_end]
                    # sentence_text = None

                    new_annotation = Sentence(
                        begin=sent_begin,
                        end=sent_end,
                        coveredText=sentence_text,
                        type=MATCH_TYPE
                    )
                    data.sentences.append(new_annotation)


# This is our ASGI app, which can be run by any of a number of ASGI server implementations.
# Note: We alternatively could instantiate app=factory.build() directly and uvicorn could run that,
# but creating our app as a factory allows uvicorn to load in environment variables,
# logging configuration, etc, before our app is constructed.
def app():
    return fastapi_app_factory.build(SpacySentenceAnnotator())


# Debug your app in a python IDE debugger using the following
if __name__ == "__main__":
    import os
    import uvicorn
    import acd_annotator_python
    from acd_annotator_python import service_utils
    uvicorn.run("example_apps.extras.spacy_sentence_annotator:app", host="localhost", port=8000, reload=True,
                reload_dirs=[".", os.path.dirname(acd_annotator_python.__file__)],  # watch for changes
                factory=True,
                log_config=service_utils.DEFAULT_LOG_SETTINGS,
                env_file="server.env",
                )
