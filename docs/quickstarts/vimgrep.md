Here is the documentation adjusted to match the exact template format provided:

# Native Vim Search (`vimgrep` & `:grep`)

Built-in Vim commands for searching across multiple files and managing project working directories without relying on plugins.

## Flags

| Flag / Arg | Does |
| --- | --- |
| `/pattern/i` | Makes the search case-insensitive. |
| `%` | Limits the search to the currently open file. |
| `*` | Searches all files in the current directory only (non-recursive). |
| `**` | Searches all files recursively in the current directory and subdirectories. |
| `<C-r><C-w>` | Shortcut to paste the word currently under the cursor into the command line. |
| `:cd` | Changes the global working directory for the entire Vim session. |
| `:lcd` | Changes the working directory for the current window only. |
| `:tcd` | Changes the working directory for the current tab only. |

## Recipes

```vim
# Search for a keyword recursively in the current project
:vimgrep /my_keyword/ **

# Search for a keyword only in JavaScript files recursively
:vimgrep /my_keyword/ **/*.js

# Search for the word currently under your cursor across the whole project
:vimgrep /<C-r><C-w>/ **

# Search only within the current file
:vimgrep /my_keyword/ %

# Open the quickfix list to view all search results
:copen

# Navigate to the next or previous search result
:cnext
:cprev

# Close the quickfix list
:cclose

# Instantly change Vim's working directory to the root of the current Git project
:cd `git rev-parse --show-toplevel`

# Check what directory Vim is currently searching from
:pwd
```

```vim
# Configure native :grep to be recursive and fast (add to .vimrc)
set grepprg=grep\ -rnIH\ $*

# Use the fast native grep instead of vimgrep
:grep my_keyword
```

```vim
# Map quickfix navigation to shortcut keys (add to .vimrc)
nnoremap <leader>n :cnext<CR>
nnoremap <leader>p :cprev<CR>
nnoremap <leader>o :copen<CR>
nnoremap <leader>c :cclose<CR>
```

## Gotchas

- **The Project Root Problem:** `**` searches relative to Vim's Current Working Directory (`cwd`). If you open a file from deep inside a project, `**` might search your entire home directory. Always launch Vim from the project root (`cd ~/project && vim .`) or use `:cd `git rev-parse --show-toplevel`` to fix it.
- **`:cd` vs `:lcd`:** Using `:cd` changes the directory for *all* open tabs and windows. If you are working on multiple projects in different split windows, use `:lcd` to change the directory for only the current window so you don't break the search context of your other splits.
- **Performance:** `vimgrep` loads every file into memory to search, making it slow on large projects. Using `:grep` (configured with `set grepprg`) is much faster as it uses the system's external grep tool, while still populating the exact same Quickfix list.
