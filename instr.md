In the purification stage of unit test

A line like:

container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_DOCKER_ENGINE -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app tmp.pandoc_texlive.arm64.9a4bae9a /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt --output /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.tex --template /dev_scripts_helpers/documentation/pandoc.latex -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s -t latex

1) need to have container replaced based on the value of the docker or container
   used with $DOCKER

2) the '-e AM_CONTAINER_VERSION -e CSFY_AWS_ACCESS_KEY_ID -e CSFY_AWS_DEFAULT_REGION ...' part of the docker command needs to be replaced
  with -e ...

Make a plan about how to change this

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
