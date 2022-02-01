FROM public.ecr.aws/lambda/python:3.8

ARG FUNCTION_NAME
ARG FUNCTION_HANDLER

# Copy function code
COPY functions/${FUNCTION_NAME}.py ${LAMBDA_TASK_ROOT}/app.py
COPY functions/custom_logger.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["app.handler"]