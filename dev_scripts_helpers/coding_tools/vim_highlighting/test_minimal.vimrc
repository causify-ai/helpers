" Minimal vimrc for syntax testing (no plugins)
set nocompatible
set encoding=utf-8
syntax on
colorscheme gp

" Load our custom syntax file
autocmd BufRead,BufNewFile test_syntax_examples.txt setlocal filetype=txt
autocmd BufRead,BufNewFile test_syntax_examples.txt setlocal syntax=txt_syntax

" Export function
function! ExportSyntaxInfo()
    let output = []
    for lnum in range(1, line('$'))
        let line_content = getline(lnum)
        let line_info = lnum . ': ' . line_content . ' ['
        let syntax_groups = []
        for col in range(1, len(line_content) + 1)
            let syntax_id = synID(lnum, col, 0)
            let syntax_name = synIDattr(syntax_id, 'name')
            if syntax_name !=# 'Normal'
                call add(syntax_groups, col . ':' . syntax_name)
            endif
        endfor
        if len(syntax_groups) > 0
            let line_info .= join(syntax_groups, ', ')
        else
            let line_info .= 'Normal'
        endif
        let line_info .= ']'
        call add(output, line_info)
    endfor
    call writefile(output, 'test_syntax_output.txt')
    echo "Syntax info exported to test_syntax_output.txt"
endfunction

command! ExportSyntax call ExportSyntaxInfo()
