# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import logging
import logging.config
import time
import json
from fastapi import FastAPI, Body, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from acd_annotator_python.container_model.main import ContainerGroup
from acd_annotator_python import container_utils
from acd_annotator_python import service_utils
from acd_annotator_python.service_utils import ACDException

logger = logging.getLogger(__name__)

EXAMPLE_REQUEST = {"unstructured": [
    {
        "text": "The patient reports severe bowel discomfort for the last week. No previous history of complaints. "
                "No current medications\n\nFamily history:\n- Hx IBS in an uncle\n- Liver cancer in father\n\n",
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
                },
                {
                    "cui": "C0022104",
                    "preferredName": "Irritable Bowel Syndrome",
                    "semanticType": "dsyn",
                    "source": "umls",
                    "sourceVersion": "2020AA",
                    "type": "umls.DiseaseOrSyndrome",
                    "begin": 143,
                    "end": 146,
                    "coveredText": "IBS",
                    "icd10Code": "K58.9,K58.0",
                },
                {
                    "cui": "C0345904",
                    "preferredName": "Malignant neoplasm of liver",
                    "semanticType": "neop",
                    "source": "umls",
                    "sourceVersion": "2020AA",
                    "type": "umls.NeoplasticProcess",
                    "begin": 161,
                    "end": 173,
                    "coveredText": "Liver cancer",
                    "icd10Code": "C78.7,C22.9",
                }
            ]
        }
    }
]
}

# example service properties. These will be overridden by environment properties
DEFAULT_ANNOTATOR_NAME = 'Example ACD Microservice'
DEFAULT_ANNOTATOR_DESCRIPTION = 'Example ACD microservice annotator'
DEFAULT_BASE_URL = '/services/example_acd_service/api/v1'
DEFAULT_VERSION = '2021-04-06T15:37:31Z'
DEFAULT_MAX_THREADS = 10


def build(custom_annotator, example_request=EXAMPLE_REQUEST):
    """
    Build a fastapi app from the given custom_annotator.

    Depends on the following environmental properties:

        # url where the app should be served. Must end with "/api/v#"
        com_ibm_watson_health_common_base_url

        # app version. A timestamp, e.g., 2021-04-06T15:37:31Z.
        # This is reported in ACD's annotator info APIs, and ideally corresponds to a build/release.
        com_ibm_watson_health_common_version

        # max number of threads per worker. fastapi defaults this to num_cpus*5, which can be too large in
        # a container setting where a process does not have access to all the cpus.
        com_ibm_watson_health_common_fastapi_max_threads

    :param custom_annotator: an ACDAnnotator subclass that performs the business logic of the service.
    :param example_request: The text of an example request
    :return: FastAPI app implementing an ACD microservice.
    """

    # read environment variables
    ANNOTATOR_NAME: str = service_utils.getenv('com_ibm_watson_health_common_annotator_name', DEFAULT_ANNOTATOR_NAME)
    ANNOTATOR_DESCRIPTION: str = service_utils.getenv('com_ibm_watson_health_common_annotator_description',
                                                      DEFAULT_ANNOTATOR_DESCRIPTION)
    BASE_URL: str = service_utils.getenv('com_ibm_watson_health_common_base_url', DEFAULT_BASE_URL).rstrip("/")
    VERSION: str = service_utils.getenv('com_ibm_watson_health_common_version', DEFAULT_VERSION)
    MAX_THREADS: int = int(service_utils.getenv('com_ibm_watson_health_common_python_max_threads',
                                                DEFAULT_MAX_THREADS))
    PROCESS_URL = "/process"

    app = FastAPI(
        title=ANNOTATOR_NAME,
        version=VERSION,
        description=ANNOTATOR_DESCRIPTION,
    )

    @app.post(BASE_URL + PROCESS_URL)
    async def process_endpoint(request: Request, body=Body(..., example=example_request)):
        """Run this microservice annotator over a request consisting of a ContainerGroup."""
        # Note: we can put `container_group:ContainerGroup` in the definition above and fastapi
        # would create a schema for it and expose it in swagger. But the container model is so
        # big that it makes this unwieldy. So we'll just accept the raw request for now. If
        # you want to see the schema you can do `print(ContainerGroup.schema_json(indent=2))`

        # require json input
        if not service_utils.has_json_content_type(request):
            raise ACDException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                               description="Unsupported Media Type")

        # body has already been parsed into a dict. Translate java offsets to python offsets.
        body = container_utils.java2python(body)
        # Input validation: you can enable/disable this input validation check depending on how much
        # you trust your input
        try:
            container_group = ContainerGroup(**body)
            container_group.schema_json()
        except Exception as e:
            # note: exception messages get sanitized in the exception handler to avoid logging doc bodies
            logging.exception('Input container failed validation')
            raise ACDException(status_code=status.HTTP_400_BAD_REQUEST,
                               description="Input container failed validation")

        # each container group consists of a list of UnstructuredContainer
        try:
            # Process all of the unstructured containers
            if container_group is not None and container_group.unstructured is not None:
                for unstructured_container in container_group.unstructured:
                    if unstructured_container is not None:
                        if unstructured_container.data is None:
                            unstructured_container.data = container_utils.create_unstructured_container()
                        # run the annotator over each UnstructuredContainer
                        await custom_annotator.annotate(unstructured_container, request)
            # Process all of the structured containers
            if container_group is not None and container_group.structured is not None:
                for structured_container in container_group.structured:
                    if structured_container is not None:
                        if structured_container.data is None:
                            structured_container.data = container_utils.create_structured_container()
                        await custom_annotator.annotate_structured(structured_container, request)
        # allow the annotator to raise custom acd errors without catching them--pass them on
        except ACDException:
            # note: "raise e" would create a new stack trace,
            # but a bare "raise" passes the error on with no changes.
            raise
        # validation exception -> 500
        except ValidationError:
            error_msg = 'This service produced an invalid container.'

            # note: exception messages get sanitized in the exception handler to avoid logging doc bodies
            logging.exception(error_msg)
            raise ACDException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                               description=error_msg)
        # unexpected exception -> 500
        except Exception as e:
            error_msg = f"Encountered an unexpected error while running annotator logic: {type(e).__name__}={e}"
            # This log is ok as long as none of the underlying errors thrown include customer data.
            logging.exception(error_msg)
            raise ACDException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                               description=error_msg)

        # return the ContainerGroup as a dictionary. (fastapi takes care of converting to json string)
        # any pydantic ContainerGroup validation was done dynamically during the edits,
        # so this really should never fail.
        try:
            result_body = container_group.dict(exclude_none=True)
            result_body = container_utils.python2java(result_body)
        except Exception as e:
            error_msg = f"Encountered an unexpected error while serializing container: {type(e).__name__}={e}"
            logging.exception(error_msg)
            raise ACDException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                               description=error_msg)
        return result_body

    @app.get(BASE_URL + "/status")
    async def status_endpoint(request: Request):
        """
        This method returns information describing the state of the server
        :return:
        """
        if await service_utils.is_annotator_healthy(custom_annotator, app):
            acd_service_info: service_utils.ServiceInfo = request.app.acd_service_info
            return {
                "version": VERSION,
                "upTime": acd_service_info.get_uptime(),
                "serviceState": service_utils.ServerState.ok,
                "hostName": acd_service_info.hostname,
                "requestCount": await acd_service_info.get_request_count(),
                "maxMemoryMb": await service_utils.get_max_rss_mb(),
                "inUseMemoryMb": await service_utils.get_rss_mb(),
                "commitedMemoryMb": await service_utils.get_vms_mb(),
                "availableProcessors": await service_utils.get_num_processors(),
                # "concurrentRequests": 0,
                # "maxConcurrentRequests": 3,
                # "totalRejectedRequests": 0,
                # "totalBlockedRequests": 0
            }
        else:
            raise ACDException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                               description="Status check failed. See log for details.")

    @app.get(BASE_URL + "/status/health_check")
    async def health_check_endpoint(request: Request):
        """Does this microservice appear healthy?"""
        if await service_utils.is_annotator_healthy(custom_annotator, request.app):
            return {
                "serviceState": service_utils.ServerState.ok
            }
        else:
            raise ACDException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                               description="Health check failed. See log for details.")

    # we aren't going to assume that startup logic is threaded (it will often involve IO
    # like 'open()' which doesn't know about async and await, so we will just define
    # this as 'def' and not 'async def'
    @app.on_event('startup')
    def on_startup():
        """A hook that gets called on server startup"""
        # specify a max number of workers. For context, starlette underneath fastapi
        # will by default allow num_cpus * 5. So in a docker setting, if your container is
        # limited to 2 cpus but the machine has 16 cpus, by default it will execute with
        # up to 80 threads, which seems excessive.
        service_utils.set_max_threads(MAX_THREADS)
        # create a ServiceInfo object to track server status
        app.acd_service_info = service_utils.ServiceInfo()
        # notify the annotator that we're starting up and let it load any resources it needs
        custom_annotator.on_startup(app)

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        """A hook that gets called on each request"""
        # set a context variable (acts like a thread local variable) that is used to
        # decorate all logging statements (adds a correlation id for tracking a request across microservices)
        correlation_id = request.headers.get("x-correlation-id", "null")
        service_utils.correlation_id_var.set(correlation_id)

        # entry logging
        start_ts = time.time()
        kv_log_builder = service_utils.KVLogBuilder()
        kv_log_builder.add_item('api_verb', request.method)
        logger.info(f'>{request.method} {request.url} {kv_log_builder}')
        logger.info(f'Req Headers={service_utils.get_header_log(request)}')

        # track how many requests have been serviced
        await request.app.acd_service_info.increment_request_count()

        # execute the call as normal
        response: Response = await call_next(request)

        # exit logging
        kv_log_builder.add_item('api_time', f'{time.time()-start_ts:0.03f}')
        kv_log_builder.add_item('api_rc', response.status_code)
        kv_log_builder.add_item('api_size_i', request.headers.get("content-length"))
        logger.info(f'<{request.method} {request.url} {kv_log_builder}')
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """
        By default fastapi returns 422 instead of 400 for malformed json, etc.
        Other ACD annotators treat these as 400s, so to be consistent with them,
        we will translate fastapi's 422s back to 400.
        :return:
        """
        # A bad mediatype trumps a bad json parse
        if request.url.path.endswith(PROCESS_URL):
            if not service_utils.has_json_content_type(request):
                return JSONResponse("Unsupported Media Type", status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        # Note: we don't want to log the full str(exc). In handling validation errors
        # pydantic is super aggressive and reports the whole document body.
        # error_msg = str(exc)  # this is super verbose and returns the whole input document

        # exc.raw_errors just includes the errors portion--not the document body
        error_msg = ',   '.join(str(e) for e in exc.raw_errors)
        acd_exception = service_utils.ACDException(status_code=400, description=error_msg)
        return JSONResponse(acd_exception.detail, status_code=acd_exception.status_code)

    return app
