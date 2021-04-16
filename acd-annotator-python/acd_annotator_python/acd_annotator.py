# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

from abc import ABC, abstractmethod
import inspect
from fastapi import Request

from acd_annotator_python.container_model.main import UnstructuredContainer


class ACDAnnotator(ABC):
    def __init_subclass__(cls, **kwargs):
        """
        Make sure that any subclass that inherits ACDAnnotator
        defines is_healthy() and annotate() as coroutines (with the async keyword).
        This can lead to hard-to-track-down errors, so we'll do this check up front.
        :param arg:
        :param kwargs:
        """
        super().__init_subclass__(**kwargs)
        child_method = getattr(cls, "is_healthy")
        assert inspect.iscoroutinefunction(child_method), f'The method {child_method} must be a coroutine ("async def")'

        child_method = getattr(cls, "annotate")
        assert inspect.iscoroutinefunction(child_method), f'The method {child_method} must be a coroutine ("async def")'

    @abstractmethod
    def on_startup(self, app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        ...

    @abstractmethod
    async def is_healthy(self, app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        ...

    @abstractmethod
    async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
        """
        Apply annotator logic to the unstructured container, altering it in-place.
        :param unstructured_container:
        :param request:
        :return:
        """
        ...
