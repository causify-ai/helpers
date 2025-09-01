Create a script generate_all_projects.py

generate_all_projects.py --input_dir XYZ --output_dir ABC

that finds all the Lesson* files in the input dir
and then calls

create_markdown_summary.py --in_file ~/src/umd_msml6101/msml610/lectures_source/Lesson02-Techniques.txt --action summarize --out_file Lesson02-Techniques.summary.txt --use_library --max_num_bullets 3

create_class_projects.py --in_file ~/src/umd_msml6101/msml610/lectures_source/Lesson02-Techniques.txt --action create_project --out_file Lesson02-Techniques.projects.txt

creating all the files in output dir

You must follow the instructions in general_testing_instr.md
