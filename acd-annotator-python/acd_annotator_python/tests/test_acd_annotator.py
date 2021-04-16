# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import pytest
from fastapi import Request

from acd_annotator_python.acd_annotator import ACDAnnotator
from acd_annotator_python.container_model.main import UnstructuredContainer


def test_good_acd_annotator():
    # trying to instantiate an ACDAnnotator with
    # non-async methods should raise an error
    class NoopAnnotator(ACDAnnotator):
        """A simple annotator that does nothing for testing purposes"""
        def on_startup(self, app):
            pass

        async def is_healthy(self, app):  # ERROR! must be async!
            return True

        async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
            pass
    NoopAnnotator()


def test_bad_acd_annotator1():
    with pytest.raises(AssertionError):
        # trying to instantiate an ACDAnnotator with
        # non-async methods should raise an error
        class NoopAnnotator(ACDAnnotator):
            """A simple annotator that does nothing for testing purposes"""
            def on_startup(self, app):
                pass

            def is_healthy(self, app):  # ERROR! must be async!
                return True

            async def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
                pass
        NoopAnnotator()


def test_bad_acd_annotator2():
    with pytest.raises(AssertionError):
        # trying to instantiate an ACDAnnotator with
        # non-async methods should raise an error
        class NoopAnnotator(ACDAnnotator):
            """A simple annotator that does nothing for testing purposes"""
            def on_startup(self, app):
                pass

            async def is_healthy(self, app):  # ERROR! must be async!
                return True

            def annotate(self, unstructured_container: UnstructuredContainer, request: Request):
                pass
        NoopAnnotator()


# enable to debug
if __name__ == '__main__':
    test_bad_acd_annotator1()
