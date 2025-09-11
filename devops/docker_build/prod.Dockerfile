#
# Create a PROD image with the current code inside of the DEV image.
#
ARG VERSION
ARG ECR_BASE_PATH
ARG IMAGE_NAME
FROM ${ECR_BASE_PATH}/${IMAGE_NAME}:dev-${VERSION}

RUN ls .

COPY . /app
# Since the `.git/` was quite large, it is added to the `.dockerignore.prod`.
# Reinitialize an empty Git repository, required by some of our packages.
RUN /bin/bash -c 'git init'
