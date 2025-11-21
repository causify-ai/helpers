FILES=$(find docs -name "*.md" | sort | head -5)

for FILE in $FILES; do
    echo $FILE
    lint_txt.py -i $FILE
done
