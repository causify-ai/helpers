#
# Create a PROD image with the current code inside of the DEV image.
#
ARG VERSION
ARG ECR_BASE_PATH
FROM ${ECR_BASE_PATH}/helpers:dev-${VERSION}

RUN ls .
COPY . /app
