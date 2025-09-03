#
# Create a PROD image with the current code inside of the DEV image.
#
ARG VERSION
ARG ECR_BASE_PATH
ARG IMAGE_NAME
ARG GIT_INIT=False
FROM ${ECR_BASE_PATH}/${IMAGE_NAME}:dev-${VERSION}

RUN ls .
COPY . /app
RUN /bin/bash -c 'if [[ $GIT_INIT == "True" ]]; then git init; fi;'