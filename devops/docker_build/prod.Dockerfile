#
# Create a PROD image with the current code inside of the DEV image.
#
ARG VERSION
ARG ECR_BASE_PATH
ARG IMAGE_NAME
FROM ${ECR_BASE_PATH}/${IMAGE_NAME}:dev-${VERSION}

ARG IS_GIT_INIT=False

RUN ls .
COPY . /app
RUN /bin/bash -c 'if [[ $IS_GIT_INIT == "True" ]]; then git init; fi;'