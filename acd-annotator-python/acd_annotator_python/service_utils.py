# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import contextvars
import json
import os
import socket
import time
from datetime import timedelta, datetime, timezone
import logging
import math
import resource
import multiprocessing
import platform
import psutil

from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


class ServerState:
    """
    The server status endpoints can return one of three possible states
    """
    ok = "OK"
    warning = 'WARNING'
    error = 'ERROR'


async def get_num_processors():
    """Get the number of processors on this machine"""
    return multiprocessing.cpu_count()


def set_max_threads(max_workers):
    """
    Set the maximum number of threads this server can use
    :param max_workers:
    :return:
    """
    # Hack borrowed from https://github.com/tiangolo/fastapi/issues/603
    # which leans on the fact that even though it doesn't expose this setting
    # itself, starlette (under fastapi) uses the default thread executor
    # which we can configure
    from concurrent.futures import ThreadPoolExecutor
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.set_default_executor(ThreadPoolExecutor(max_workers=max_workers))
    except RuntimeError:
        # if there is no running loop, then we are running tests and this doesn't matter
        pass


class ServiceInfo:
    def __init__(self):
        self.startTime = time.time()
        self.hostname = socket.gethostname()
        self.request_count = 0

    def get_uptime(self):
        # compute uptime since the server started
        td = timedelta(seconds=time.time() - self.startTime)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return "{:01}d {:02}:{:02}:{:02}".format(td.days, hours, minutes, seconds)

    async def increment_request_count(self):
        self.request_count += 1

    async def get_request_count(self):
        return self.request_count


async def get_max_rss_mb():
    """Get the max resident set size of this process in megabytes"""
    max_rss_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # rlimit in Linux returns kilobytes; other systems return bytes
    # mebibytes (as per IEC standard)
    # max_rss_denominator = 1024 if platform.system() == "Linux" else 1024 ** 2
    # megabytes (as per IEC standard)
    max_rss_denominator = 1000 if platform.system() == "Linux" else 1000000
    max_rss_mb = math.ceil(max_rss_bytes / max_rss_denominator)
    return max_rss_mb


async def get_rss_mb():
    """Get the resident set size of this process in megabytes"""
    rss_bytes = psutil.Process().memory_info().rss
    # mebibytes (as per IEC standard)
    # max_rss_denominator = 1024 ** 2
    # megabytes (as per IEC standard)
    rss_denominator = 1000000
    rss_mb = math.ceil(rss_bytes / rss_denominator)
    return rss_mb


async def get_vms_mb():
    """Get the virtual memory size of this process in megabytes"""
    rss_bytes = psutil.Process().memory_info().vms
    # mebibytes (as per IEC standard)
    # max_rss_denominator = 1024 ** 2
    # megabytes (as per IEC standard)
    rss_denominator = 1000000
    rss_mb = math.ceil(rss_bytes / rss_denominator)
    return rss_mb


# a few common status code messages. We could get these
# programmatically from httplib, but don't want to introduce that
# dependency, and they aren't too important
STATUS_CODE_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Bad Request",
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not Found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method Not Allowed",
    status.HTTP_406_NOT_ACCEPTABLE: "Not Acceptable",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Unprocessable Entity",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
    status.HTTP_501_NOT_IMPLEMENTED: "Not Implemented",
    status.HTTP_502_BAD_GATEWAY: "Bad Gateway",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Service Unavailable",
    status.HTTP_504_GATEWAY_TIMEOUT: "Gateway Timeout",
}


class ACDException(HTTPException):
    """
    A subclass of fastapi's HTTPException that has the internal json
    structure expected by ACD.
    """

    def __init__(self, status_code=500,
                 description="Unknown error. See logs for details."):
        """ Create a normal HTTPException with a json body containin ACD expected fields."""
        HTTPException.__init__(self, status_code=status_code, detail={
            "code": status_code,
            "message": STATUS_CODE_MESSAGES.get(status_code, ServerState.error),
            "level": ServerState.error,
            "description": description,
        })


async def is_annotator_healthy(custom_annotator, app):
    """
    Check whether an annotator is healthy or not, handling exceptions
    and interpreting them as not healthy.
    :param app:
    :param custom_annotator:
    :return:
    """
    try:
        is_healthy = await custom_annotator.is_healthy(app)
    except Exception:
        logger.exception("is_healthy check failed")
        is_healthy = False
    return is_healthy


def getenv(key, default):
    """
    Similar to os.getenv, but logs the values being used, especially when the key doesn't exist
    in the environment and we have to use a default value. This can be a clue that the service is misconfigured.
    :param key:
    :param default:
    :return:
    """
    if key not in os.environ:
        logger.warning(f'Service startup: environment variable {key} is not set. Using default value: "{default}"')
    else:
        val = os.environ[key]
        logger.info(f'Service startup: using environment variable {key} value of {val}')
    return os.getenv(key, default)


class KVLogBuilder:
    """
    Put together a key-value summary of the form:
    kv|key1=val1 key2=val2|

    Imitates ServiceLogKvBuilder in java.
    """

    def __init__(self):
        self.kv = []

    def add_item(self, key, value):
        self.kv.append((key, value))

    def __str__(self):
        kv_str = ' '.join(f'{k}={v}' for k, v in self.kv)
        return f'kv|{kv_str}|'


def has_json_content_type(request: Request):
    """
    Does this request have a content-type: application/json media type?
    """
    if request.headers.get('content-type') is None:
        return False
    return 'application/json' in request.headers.get('content-type')  # fast api converts to lower


def get_header_log(request: Request):
    remove_headers = ['cookie']
    mask_headers = ['authorization']

    def redact(headers):
        for key, val in headers.items():
            key = key.lower()
            if key not in remove_headers:
                if key in mask_headers:
                    yield key, '*****'
                else:
                    yield key, val

    redacted_header = [f'{key}:"{val}"' for key, val in redact(request.headers)]
    return ' '.join(redacted_header)


class ACDDateFormatter(logging.Formatter):
    """
    Format a date in the same iso format produced by java ACD services:
    e.g., "2021-04-20T14:54:18.693Z"
    """
    # converter = datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        # ct = self.converter(record.created)
        # technically we should use record.created, but not sure how to make that timezone compliant
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "")[:-3] + "Z"


# correlation id for the current requests (acts like a thread local variable)
correlation_id_var = contextvars.ContextVar("correlation_id")


class AppendACDMetadataLogFilter(logging.Filter):
    """
    This filter doesn't actually remove anything--it adds
    the correlation id (if available) from a thread local variable.
    """
    def filter(self, record):
        try:
            record.ACDCorrelationId = correlation_id_var.get()
        except LookupError:
            pass
        return True


class HasACDMetadataLogFilter(logging.Filter):
    """
    If require_acd_metadata is true, drops all records without acd metadata.
    Otherwise, drops all records with acd metadata.
    """
    def __init__(self, require_acd_metadata):
        super().__init__()
        self.require_acd_metadata = require_acd_metadata

    def filter(self, record):
        has_acd_metadata = hasattr(record, "ACDCorrelationId")
        return self.require_acd_metadata == has_acd_metadata


# read in default log settings from this module's directory
DEFAULT_LOG_SETTINGS = json.load(open(f"{os.path.dirname(__file__)}/defaultLogSettings.json"))
