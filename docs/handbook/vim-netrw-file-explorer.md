---
tags: [vim, netrw, fzf, workflow, file-management]
date: 2023-10-26
---
# Vim's Built-in File Explorer (netrw) with fzf

<span class="status status-draft">draft</span>

A guide to using Vim's default file explorer (`netrw`) for structural browsing and `fzf` for rapid file searching, including how to handle deep directory trees.

## Prerequisites

- Vim or Neovim installed.
- `fzf` installed on your system.
- `junegunn/fzf` and `junegunn/fzf.vim` plugins installed in your Vim configuration.
- (Optional) `ripgrep` installed for content searching with `:Rg`.

## Why it's built this way

The reasoning behind this setup is a strict division of labor: `netrw` is for **browsing** (when you don't know what you want and need to see the project structure), and `fzf` is for **searching** (when you know the file name or content). 

I optimized for a setup that relies on Vim's built-in capabilities rather than heavy external plugins like NERDTree. This keeps the Vim environment lightweight and portable. I rejected the idea of replacing `netrw` entirely with `fzf` because `fzf` is terrible at showing you the spatial relationship between directories. Conversely, I rejected using only `netrw` because scrolling through a deep tree with `j` and `k` to find a specific file is painfully slow. 

By keeping `netrw` open in a sidebar for context and using `fzf` to jump to files, you get the best of both worlds.

## Setup

### 1. Configuring `netrw` for Tree View

Out of the box, `netrw` can feel cluttered. Add these settings to your `vimrc` to make it behave like a modern sidebar file explorer:

```vim
" Remove the top banner
let g:netrw_banner = 0

" Set the default view to 'Tree' (view 3)
let g:netrw_liststyle = 3

" Set the width of the window when opened in a vertical split
let g:netrw_winsize = 25

" Open files in the previous window (keeps the explorer open on the side)
let g:netrw_browse_split = 4
```

### 2. Basic `netrw` Operations

With Tree View enabled, you can navigate and manage files directly in the buffer:

- **`<Enter>`** on a directory: Expands/collapses the directory inline.
- **`<Enter>`** on a file: Opens the file in the previous window.
- **`d`**: Create a new directory.
- **`%`**: Create a new file.
- **`R`**: Rename the file/directory under the cursor.
- **`D`**: Delete the file/directory.
- **`c`**: Make the directory under the cursor the current working directory.

### 3. Integrating `fzf` inside `netrw`

To get the best workflow, we map keys inside the `netrw` buffer. We need two separate searches: one for the *current* directory, and one for the *project root* (so you don't get trapped when deep in a tree).

Add this to your `vimrc`:

```vim
" Function to find the project root by looking for common markers
function! s:find_project_root()
    let l:cwd = expand('%:p:h')
    let l:markers = ['.git', '.hg', 'package.json', '.project']
    while l:cwd !=# '/'
        for l:marker in l:markers
            if isdirectory(l:cwd . '/' . l:marker) || filereadable(l:cwd . '/' . l:marker)
                return l:cwd
            endif
        endfor
        let l:cwd = fnamemodify(l:cwd, ':h')
    endwhile
    return expand('%:p:h') " Fallback to current dir
endfunction

command! ProjectFiles execute 'Files ' . s:find_project_root()

augroup netrw_fzf
    autocmd!
    " Press 'f' to fuzzy find in the CURRENT directory (where netrw is looking)
    autocmd FileType netrw nnoremap <buffer> f :Files %<CR>
    
    " Press 'F' to fuzzy find from the PROJECT ROOT
    autocmd FileType netrw nnoremap <buffer> F :ProjectFiles<CR>
augroup END
```

## Gotchas

!!! warning
    If you map `fzf` to use `:Files %` inside `netrw`, it will **only** search the directory you are currently looking at. If you navigate deep into `src/components/buttons/`, `fzf` will not find files in `src/components/`. You must use the `F` mapping (Project Root) or press `c` in `netrw` to change your working directory upwards before searching.

!!! warning
    In standard `netrw` views (Thin/Long/Wide), pressing `<Enter>` on a directory *replaces* the buffer with that directory's contents. You must be in Tree View (`let g:netrw_liststyle = 3`) for `<Enter>` to expand directories inline.

## If it breaks

| Symptom | Cause | Fix |
|---------|-------|-----|
| `fzf` searches the wrong directory when pressing `f` | `%` evaluates to the current directory `netrw` is displaying, which may be a deep subfolder. | Use `F` (mapped to `:ProjectFiles` or `:GFiles`) to search from the project root, or press `c` in `netrw` to change the global working directory. |
| `<Enter>` on a directory opens a new buffer instead of expanding a tree | `netrw` list style is not set to Tree View. | Press `i` to cycle views until you see the Tree, or set `let g:netrw_liststyle = 3` in your `vimrc`. |
| Files open in the `netrw` sidebar instead of the main editing window | Default split behavior isn't configured to reuse the previous window. | Set `let g:netrw_browse_split = 4` in your `vimrc`. |
| The `netrw` banner takes up a third of the sidebar | The default help banner is enabled. | Set `let g:netrw_banner = 0` in your `vimrc`, or press `I` to toggle it. |

## Change log

- 2023-10-26 — first write-up
```
