pandoc -o ref.pptx --print-default-data-file reference.pptx

pandoc tmp.md -o slides.pptx --reference-doc=papers/slides/causify_template.pptx

papers/slides/apply_pptx_template.py --input slides.pptx --template papers/slides/causify_template.pptx --output slides2.pptx

modify_pptx_colors.py --input slides.pptx --output slides2.pptx --background papers/slides/causify_background.png
