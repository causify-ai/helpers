pytest_log \
  # Category 1: Missing `uv` tool in Docker container (rc=127) — ~18 tests
  dev_scripts_helpers/documentation/test/test_convert_pdf_to_md.py::Test_convert_pdf_to_md::test1 \
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt_py1::test4 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test1 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test2 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test4 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test5 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test6 \
  dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py::Test__extract_markdown_section::test7 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py1::test1 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py1::test2 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py1::test3 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py1::test4 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py2::test1 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py2::test2 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py2::test3 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py2::test4 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py3::test1 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py3::test2 \
  dev_scripts_helpers/documentation/test/test_summarize_md.py::Test_summarize_md_py3::test3 \
  \
  # Category 2: Golden file drift — environment variables mismatch — 10 tests
  #   2a. Docker compose file env vars (8 tests)
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file1::test1 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file1::test2 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file1::test3 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file1::test4 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file2::test1 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file2::test2 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file2::test3 \
  helpers/lib_tasks/test/test_lib_tasks_docker.py::Test_generate_compose_file2::test4 \
  #   2b. Notes-to-pdf script env vars (2 tests)
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2 \
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test3 \
  \
  # Category 3: Architecture-dependent golden file (aarch64 vs x86_64) — 1 test
  dev_scripts_helpers/dockerize/test/test_lib_png.py::Test_build_png_container1::test2 \
  \
  # Category 4: Golden file drift — linting output format changed — 5 tests
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt2::test3 \
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt2::test6 \
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt2::test8 \
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt2::test9 \
  dev_scripts_helpers/documentation/test/test_lint_txt.py::Test_lint_txt_py1::test1 \
  \
  # Category 5: Submodule guard in docker build/release tests (working as designed) — 3 tests
  helpers/lib_tasks/test/test_lib_tasks_docker_release.py::Test_docker_build_prod_image1::test_candidate_user_tag1 \
  helpers/lib_tasks/test/test_lib_tasks_docker_release.py::Test_docker_build_prod_image1::test_single_arch_prod_image1 \
  helpers/lib_tasks/test/test_lib_tasks_docker_release.py::Test_docker_release_prod_image1::test_aws_ecr1 \
  \
  # Category 6: Test file outside standard `test/` directory — 2 tests
  helpers/lib_tasks/test/test_lib_tasks_find.py::TestLibTasksRunTests1::test_find_test_class1 \
  helpers/lib_tasks/test/test_lib_tasks_find.py::TestLibTasksRunTests1::test_find_test_files2
