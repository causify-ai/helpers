#!/bin/bash
gh pr list --json number,title,url,headRefName --template \
    '{{range .}}{{$branch := ""}}{{if ne .title .headRefName}}{{$branch = .headRefName}}{{end}}{{tablerow .number .title .url $branch}}{{end}}{{tablerender}}'
