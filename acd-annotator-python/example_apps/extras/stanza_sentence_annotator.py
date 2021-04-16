# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import stanza
from fastapi import Request
import logging

from pydantic.typing import Optional, List

from acd_annotator_python.container_model.main import UnstructuredContainerData
from acd_annotator_python.container_model.common import BaseAnnotation
from acd_annotator_python import service_utils
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.acd_annotator import ACDAnnotator

base_logger = logging.getLogger(__name__)

# new concepts will be created with this type
MATCH_TYPE = 'StanzaSentence'


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


def get_sentence_begin(sentence):
    """Convenience method that gets the begin character position of a stanza sentence."""
    if sentence is not None:
        tokens = sentence.tokens
        if tokens is not None and len(tokens) > 0:
            return tokens[0].start_char
    return -1


def get_sentence_end(sentence):
    """Convenience method that gets the end character position of a stanza sentence."""
    if sentence is not None:
        tokens = sentence.tokens
        if tokens is not None and len(tokens) > 0:
            return tokens[-1].end_char
    return -1


class StanzaSentenceAnnotator(ACDAnnotator):
    """
    An annotator that creates Section annotations over sentences identified by stanza tokenization.
    """

    def on_startup(self, fastapi_app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        # download models
        stanza.download('en', processors='tokenize')
        fastapi_app.stanza_nlp = stanza.Pipeline(lang='en', processors='tokenize')

    async def is_healthy(self, fastapi_app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        return True

    async def annotate(self, unstructured_container, request: Request):
        """
        An annotator that injects sentence annotations into a container.
        :param unstructured_container: an UnstructuredContainer to be processed and modified in-place.
        :param request: a fastapi.Request object for the current request
        :return: none
        """
        #  decorate the logger with information about the correlation id, which allows you to track a single
        # request across the logs of multiple acd annotators.
        logger = service_utils.ACDLoggerAdapter(base_logger, request)

        data = unstructured_container.data
        text = unstructured_container.text
        if data is not None and text is not None:
            # run stanza nlp and get sentences out
            sentences = request.app.stanza_nlp(text).sentences
            # log the character/sentence ratio
            logger.debug("found %s sentences in %s chars", len(sentences), len(text))
            if sentences is not None and len(sentences) > 0:
                # stanza sentences are a list of tokens; each token has start_char/end_char info
                sentence_begins = [get_sentence_begin(sent) for sent in sentences if sent is not None]
                sentence_ends = [get_sentence_end(sent) for sent in sentences if sent is not None]

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
    return fastapi_app_factory.build(StanzaSentenceAnnotator())


# Debug your app in a python IDE debugger using the following
if __name__ == "__main__":
    import os
    import uvicorn
    import acd_annotator_python
    from acd_annotator_python import service_utils
    uvicorn.run("example_apps.extras.stanza_sentence_annotator:app", host="localhost", port=8000, reload=True,
                reload_dirs=[".", os.path.dirname(acd_annotator_python.__file__)],  # watch for changes
                factory=True,
                log_config=service_utils.DEFAULT_LOG_SETTINGS,
                env_file="server.env",
                )
