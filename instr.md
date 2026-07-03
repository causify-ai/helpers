Update the tests below to use a different expected value when running inside a
Docker container

--------------------------------------------------------------------------------
ACTUAL vs EXPECTED: Test_build_markdown_toc_container1.test2
--------------------------------------------------------------------------------

/usr/local/lib                                                            (
`-- markdown-toc@1.2.0                                                    (
                                                                          <
npm notice                                                                <
npm notice New major version of npm available! 10.8.2 -> 11.18.0          <
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.18.0    <
npm notice To update run: npm install -g npm@11.18.0                      <
npm notice                                                                <
Diff with:
> ./tmp_diff.sh
--------------------------------------------------------------------------------
ACTUAL VARIABLE: Test_build_markdown_toc_container1.test2
--------------------------------------------------------------------------------
expected = r"""/usr/local/lib
`-- markdown-toc@1.2.0

npm notice
npm notice New major version of npm available! 10.8.2 -> 11.18.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.18.0
npm notice To update run: npm install -g npm@11.18.0
npm notice"""
FAILED dev_scripts_helpers/dockerize/test/test_lib_png.py::Test_build_png_container1::test2 - RuntimeError:
--------------------------------------------------------------------------------
ACTUAL vs EXPECTED: Test_build_png_container1.test2
--------------------------------------------------------------------------------

Version: ImageMagick 7.1.2-19 Q16-HDRI aarch64 23897 https://imagemagick. |  Version: ImageMagick 7.1.2-19 Q16-HDRI x86_64 23897 https://imagemagick.o
Diff with:
> ./tmp_diff.sh
--------------------------------------------------------------------------------
ACTUAL VARIABLE: Test_build_png_container1.test2
--------------------------------------------------------------------------------
expected = r"""Version: ImageMagick 7.1.2-19 Q16-HDRI aarch64 23897 https://imagemagick.org"""

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
