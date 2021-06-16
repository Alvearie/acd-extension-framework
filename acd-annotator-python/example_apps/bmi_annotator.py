# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
import logging
from fastapi import Request

from acd_annotator_python.container_model.main import StructuredContainer, StructuredContainerData
from acd_annotator_python import fastapi_app_factory
from acd_annotator_python.acd_annotator import ACDAnnotator

from pydantic import StrictInt
from typing import Optional

logger = logging.getLogger(__name__)


# Let pydantic know we'll about our new types inches and pounds at  structured.data.height_inches and
# structured.data.weight_pounds respectively.
# This is not necessary in order to add data to the container model, but it makes
# the new field become a proper part of the pydantic object model, which lets it
# validate this field.
StructuredContainerData.add_fields(height_inches=Optional[StrictInt])
StructuredContainerData.add_fields(weight_pounds=Optional[StrictInt])


class BMIAnnotator(ACDAnnotator):
    """
    An annotator that computes a Body Mass Index (BMI) from a given height (in inches) and weight (in pounds).
    """

    def on_startup(self, fastapi_app):
        """Load any required resources when the server starts up. (Not async to allow io operations)"""
        pass

    async def is_healthy(self, fastapi_app):
        """Is this annotator healthy? This gives the annotator a chance to indicate that
        resources failed to load correctly, etc."""
        return True

    async def annotate_structured(self, structured_container: StructuredContainer, request: Request):
        """
        Takes as input a structure container like this:
        {
          "structured": [{
            "data": {
              "height_inches": 74
              "weight_pounds": 190
            }
          }]
        }
        """
        data = structured_container.data
        if data is not None:
            # Note that to reference weight_pounds and height_inches like this, we had to add the types to the container
            # model at the top of this class.
            if data.weight_pounds is not None and data.height_inches is not None:
                data.bmi = round((data.weight_pounds / (data.height_inches * data.height_inches)) * 703, 1)


# This is our ASGI app, which can be run by any of a number of ASGI server implementations.
# Note: We alternatively could instantiate app=factory.build() directly and uvicorn could run that,
# but creating our app as a factory allows uvicorn to load in environment variables,
# logging configuration, etc, before our app is constructed.
def app():
    return fastapi_app_factory.build(BMIAnnotator(), example_request='''{
  "structured" : [ {
    "data" : {
       "height_inches" : 70,
       "weight_pounds" : 170
    }
   }
  ]
}''')


# Debug your app in a python IDE debugger using the following
if __name__ == "__main__":
    import os
    import uvicorn
    import acd_annotator_python
    from acd_annotator_python import service_utils

    uvicorn.run("example_apps.bmi_annotator:app", host="localhost", port=8000, reload=True,
                reload_dirs=[".", os.path.dirname(acd_annotator_python.__file__)],  # watch for changes
                factory=True,
                log_config=service_utils.DEFAULT_LOG_SETTINGS
                )
