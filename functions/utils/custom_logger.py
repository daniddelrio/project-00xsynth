#!/usr/bin/env python
# coding=utf-8
import logging
import json
import time
import os


class CustomAdapter(logging.LoggerAdapter):
    """Add general items (function name) to the log message"""

    def process(self, msg, kwargs):
        function = kwargs.pop("function", self.extra["function"])
        if "extra" in kwargs:
            if "custom_logging" in kwargs["extra"]:
                kwargs["extra"]["custom_logging"]["function"] = function
        return msg, kwargs


class JSONFormatter(logging.Formatter):
    """JSON formatter"""

    def format(self, record):
        """Format event info to json."""
        string_formatted_time = time.strftime(
            "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
        )
        obj = {}
        obj["message"] = record.msg
        obj["level"] = record.levelname
        obj["time"] = f"{string_formatted_time}.{record.msecs:3.0f}Z"
        obj["epoch_time"] = record.created
        if hasattr(record, "custom_logging"):
            for key, value in record.custom_logging.items():
                obj[key] = value
        return json.dumps(obj)


# This logger is for logging relevant information in an organized manner.
# Obtained from: https://lumigo.io/serverless-monitoring-guide/aws-lambda-python-logging/#structuredlogging
def setup_logger(module):
    """Create logging object."""
    logger = logging.getLogger(module)
    # logger.propagate = False  # remove default logger

    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    if "DEBUG" in os.environ and os.environ["DEBUG"] == "true":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
