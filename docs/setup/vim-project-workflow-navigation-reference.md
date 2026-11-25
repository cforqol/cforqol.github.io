---
tags: [vim]
---

# Vim Project Workflow Navigation Reference

Companion to my Vim setup doc. Focused on moving between files, symbols, and
locations inside a project. Assumes: fzf.vim, vim-lsp + vim-lsp-settings,
vim-vinegar, vim-signature.

---

## 1. Quick decision table

| I want to... | Use |
|---|---|
| Open a file by name, anywhere in the project | `:Files` |
| Open a git-tracked file by name | `:GFiles` |
| Switch to a file I already have open | `:Buffers` |
| Find a line in the current file | `:BLines` |
| Find a line in any open file | `:Lines` |
| Jump to where a symbol is defined | `:LspDefinition` (`gd`) |
| See every place a symbol is used | `:LspReferences` (`gr`) |
| Jump to a type's definition | `:LspTypeDefinition` |
| Jump to an implementation (interface → impl) | `:LspImplementation` |
| Find a symbol by name across the project | `:LspWorkspaceSymbol` |
| List symbols in the current file | `:LspDocumentSymbol` |
| Search text across the project, act on results | `:grep` + `:copen` |
| Search text across the project, explore interactively | `:Rg` |
| Go back to where I just was | `Ctrl-o` |
| Go forward again | `Ctrl-i` |
| Go back to where I last edited | `g;` |
| Browse the current file's directory | `-` (vinegar) |
| Open the file whose path is under the cursor | `gf` |
| Jump to a mark | `` `a `` or `'a` |
| See all marks | `:marks` or `m/` |
| Close a buffer without closing the split | `:bd` |
| Close every split except this one | `Ctrl-w o` |

---

## 2. Scenarios

### 2.1 "I know the filename, not the path"

```
:Files
```

Type a fragment (`usrsvc`), fzf fuzzy-matches `src/main/java/.../UserService.java`.
Enter opens it. `Ctrl-v` opens in a vertical split, `Ctrl-x` in a horizontal split,
`Ctrl-t` in a new tab.

Restrict to git-tracked files (skips `node_modules`, `build`, `.venv`):

```
:GFiles
```

`GFiles` only *reads* git's index — it runs no git commands and doesn't require
fugitive.

### 2.2 "I was just in that file, where did it go?"

```
:Buffers
```

Lists every loaded buffer. Fuzzy-match the name, Enter. This is usually faster
than `:Files` because the list is small and already loaded.

Adjacent: `:BLines` (search lines in *this* buffer), `:Lines` (search lines in
*all* open buffers). `:Lines` is the underrated one — when you remember the
comment but not the file, it finds it.

### 2.3 "I'm on a function call, take me to its definition"

Put the cursor on the symbol, then:

```
:LspDefinition          " or gd, if mapped
```

Lands in the defining file at the defining line. `Ctrl-o` returns.

Related jumps:

| Command | Goes to |
|---|---|
| `:LspDefinition` | Where it's defined |
| `:LspDeclaration` | Where it's declared (headers, interfaces) |
| `:LspTypeDefinition` | The type of the symbol under the cursor |
| `:LspImplementation` | Concrete implementations of an interface/abstract method |
| `:LspReferences` | Every use, in a quickfix-style list |

`:LspReferences` is the one to reach for before a refactor — it shows you every
call site across the project, and you can walk the list with `:lnext`/`:lprev`.

### 2.4 "I don't know the file, but I know the symbol name"

```
:LspWorkspaceSymbol
```

Type `parseConfig`, get every symbol matching it across the project, with file
and line. Works in any language with a running server. No ctags setup needed.

For the current file only:

```
:LspDocumentSymbol
```

Gives you an outline — every class, method, function, variable. Useful for
orienting in a large file you just opened.

### 2.5 "Find every place this string appears"

Interactive — you want to look around:

```
:Rg someString
```

fzf picker, fuzzy-filterable, Enter jumps to the hit. `Ctrl-v`/`Ctrl-x` open in
splits.

Batch — you want a persistent list to act on:

```
:grep someString
:copen
```

Now `:cnext`/`:cprev` walk the hits, `Enter` in the quickfix window jumps.
`:cdo s/old/new/g | update` replaces across every hit (review with `:copen`
first — it's a blind bulk edit).

Rule: **exploring → `:Rg`. Acting → `:grep` + `:copen`.**

Restrict by filetype when you know it:

```
:grep -tpy "TODO" src/
:grep -tjs "deprecated" frontend/
```

`rg --type-list` shows all type tags (`py`, `js`, `ts`, `rust`, `go`, `java`,
`c`, `cpp`, `sh`, `md`, ...).

### 2.6 "Take me back"

Three separate histories, all worth knowing:

| Key | History | Example |
|---|---|---|
| `Ctrl-o` / `Ctrl-i` | Jump list | Back/forward after `:LspDefinition`, `:grep` Enter, `G`, `/` |
| `g;` / `g,` | Changelist | Back to where you last edited |
| `:colder` / `:cnewer` | Quickfix list history | Back to a previous `:grep` result set |

Scenario: you `:LspDefinition` into `User.java`, edit a method, scroll away, then
want to return to the edit. `g;` — not `Ctrl-o` (that goes to the file you came
from, not the edit).

`:jumps` and `:changes` print the full lists if you need to see them.

### 2.7 "Browse the directory manually"

Vinegar gives netrw a better entry point:

| Key | Action |
|---|---|
| `-` | Open netrw at the current file's directory |
| `.` | Open netrw at the current working directory |

Inside netrw: `Enter` opens, `-` goes up a directory, `%` creates a file, `d`
creates a directory, `R` renames, `D` deletes.

This is the manual fallback when you don't know the name and don't want to
search — rare, but useful for unfamiliar trees.

### 2.8 "Open the file whose path is under my cursor"

Put the cursor on a string like `"./config/settings.json"` or `"src/util.py"`
and press:

```
gf
```

Vim opens that file. Works for imports, includes, `require()` paths, and most
string literals that look like paths. `Ctrl-o` returns.

If it can't find the file, check `:set path?` — Vim searches those directories.
For project-local paths, `:set path+=.,**` makes `gf` search the whole tree.

### 2.9 "Mark this spot, come back later"

With vim-signature, marks show in the sign column.

| Key | Action |
|---|---|
| `ma` | Set mark `a` at the cursor |
| `` `a `` | Jump to mark `a` (exact line+column) |
| `'a` | Jump to mark `a` (start of line) |
| `m/` | List all marks |
| `m,` | Set the next free mark |
| `mx` | Toggle a mark on the current line |
| `m<Space>` | Clear all marks in the buffer |
| `]'` / `['` | Next / previous marked line |

Scenario: you're reading a 900-line file, spot three things to fix. `ma`, `mb`,
`mc` at each. Then `` `a ``, fix, `` `b ``, fix, `` `c ``, fix. No scrolling.

### 2.10 "Split it, don't replace my current view"

From any fzf picker (`:Files`, `:Buffers`, `:Rg`, `:BLines`):

| Key | Opens in |
|---|---|
| `Enter` | Current window |
| `Ctrl-v` | Vertical split |
| `Ctrl-x` | Horizontal split |
| `Ctrl-t` | New tab |

From netrw: `o` = horizontal split, `v` = vertical split, `t` = new tab.

### 2.11 "Close this without losing my layout"

| Command | Effect |
|---|---|
| `:bd` | Remove the buffer, keep the window |
| `:bw` | Remove the buffer and wipe it (frees memory, loses undo) |
| `:q` | Close the window (buffer stays loaded) |
| `Ctrl-w o` | Close every other split |
| `Ctrl-w =` | Equalize split sizes |

`:q` on a quick-look split leaves the buffer loaded — it'll still show up in
`:Buffers`. `:bd` removes it properly.

### 2.12 "Navigate between splits"

| Key | Direction |
|---|---|
| `Ctrl-w h/j/k/l` | Left / down / up / right |
| `Ctrl-w w` | Next split (cycle) |
| `Ctrl-w p` | Previous split |
| `Ctrl-w H/J/K/L` | Move the split itself |

If you use `Ctrl-h/j/k/l` for splits, map them once:

```vim
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l
```

(Caveat: these clash with `Ctrl-h` = backspace in some terminals. Test first.)

---

## 3. Reference tables

### 3.1 fzf.vim pickers

| Command | Scope |
|---|---|
| `:Files` | All files under cwd |
| `:GFiles` | Git-tracked files |
| `:GFiles?` | Files modified since last commit |
| `:Buffers` | Open buffers |
| `:BLines` | Lines in current buffer |
| `:Lines` | Lines in all open buffers |
| `:Rg pattern` | Project-wide text search |
| `:Tags` | ctags (needs `ctags -R`) |
| `:BTags` | Tags in current buffer |
| `:Marks` | Jump to a mark |
| `:Jumps` | Jump list |
| `:Changes` | Changelist |
| `:History` | Command/search history |
| `:Commands` | Vim commands |
| `:Helptags` | Help tags |
| `:Filetypes` | Filetype picker |
| `:Colors` | Colorscheme picker |
| `:Windows` | Window picker |

### 3.2 vim-lsp navigation

| Command | Action |
|---|---|
| `:LspDefinition` | Go to definition |
| `:LspDeclaration` | Go to declaration |
| `:LspTypeDefinition` | Go to type definition |
| `:LspImplementation` | Go to implementation |
| `:LspReferences` | Find all references |
| `:LspDocumentSymbol` | Symbols in current file |
| `:LspWorkspaceSymbol` | Symbols in project |
| `:LspHover` | Docs for symbol under cursor |
| `:LspRename` | Rename symbol project-wide |
| `:LspCodeAction` | Quick fixes, auto-imports, extract |
| `:LspPeekDefinition` | Preview definition in popup (Vim 8.2+) |
| `:LspSelectionExpand` | Expand selection (scope-aware) |
| `:LspSelectionShrink` | Shrink selection |
| `:LspDocumentHighlight` | Highlight all occurrences in buffer |
| `:LspStatus` | Show running servers |

### 3.3 Quickfix navigation

| Command | Action |
|---|---|
| `:copen` / `:cclose` | Open / close the list |
| `:cwindow` | Open only if non-empty |
| `:cnext` / `:cprev` | Next / previous entry |
| `:cfirst` / `:clast` | First / last entry |
| `:cc N` | Jump to entry N |
| `:clist` | Print all entries |
| `:colder` / `:cnewer` | Previous / next result set |
| `:cdo cmd` | Run cmd on each entry |
| `:cfdo cmd` | Run cmd once per file |

Location list (`:lopen`, `:lnext`, ...) is the per-window version — vim-lsp
diagnostics and `:LspReferences` land here.

### 3.4 Jump list and changelist

| Key | Action |
|---|---|
| `Ctrl-o` | Jump back |
| `Ctrl-i` | Jump forward |
| `g;` | Previous change |
| `g,` | Next change |
| `:jumps` | Show jump list |
| `:changes` | Show changelist |
| `''` | Jump to line before last jump |
| `'.` | Jump to last change |

### 3.5 Marks

| Key | Action |
|---|---|
| `ma` | Set mark `a` |
| `` `a `` | Jump to mark `a` (line + column) |
| `'a` | Jump to mark `a` (line only) |
| `m/` | List marks (vim-signature) |
| `m,` | Set next free mark (vim-signature) |
| `mx` | Toggle mark on line (vim-signature) |
| `]'` / `['` | Next / previous marked line |
| `:marks` | Built-in mark list |
| `:delmarks a` | Delete mark `a` |
| `:delmarks!` | Delete all lowercase marks |

Uppercase marks (`mA`) are global across files; lowercase (`ma`) are per-buffer.

### 3.6 netrw / vinegar

| Key | Action |
|---|---|
| `-` | Open netrw at current file's directory |
| `.` | Open netrw at cwd |
| `Enter` | Open file/directory |
| `-` (in netrw) | Go up a directory |
| `o` | Open in horizontal split |
| `v` | Open in vertical split |
| `t` | Open in new tab |
| `%` | Create file |
| `d` | Create directory |
| `R` | Rename |
| `D` | Delete |
| `gh` | Toggle hidden files |

---

## 4. Suggested keymaps

Optional, but these make the above much faster. Put in `~/.vimrc`:

```vim
" File navigation
nnoremap <leader>ff :Files<CR>
nnoremap <leader>fg :GFiles<CR>
nnoremap <leader>fb :Buffers<CR>
nnoremap <leader>fl :BLines<CR>
nnoremap <leader>fL :Lines<CR>
nnoremap <leader>fr :Rg<CR>

" LSP navigation
nnoremap <silent> gd :LspDefinition<CR>
nnoremap <silent> gr :LspReferences<CR>
nnoremap <silent> gD :LspDeclaration<CR>
nnoremap <silent> gy :LspTypeDefinition<CR>
nnoremap <silent> gi :LspImplementation<CR>
nnoremap <silent> K  :LspHover<CR>
nnoremap <silent> <leader>rn :LspRename<CR>
nnoremap <silent> <leader>ca :LspCodeAction<CR>
nnoremap <silent> <leader>ds :LspDocumentSymbol<CR>
nnoremap <silent> <leader>ws :LspWorkspaceSymbol<CR>

" Quickfix
nnoremap <silent> ]q :cnext<CR>
nnoremap <silent> [q :cprev<CR>
nnoremap <silent> ]Q :clast<CR>
nnoremap <silent> [Q :cfirst<CR>
nnoremap <silent> <leader>co :copen<CR>
nnoremap <silent> <leader>cc :cclose<CR>

" Splits
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" Buffers
nnoremap <leader>bd :bd<CR>
```

If `Ctrl-h` breaks (some terminals send backspace), use `<leader>h` etc. instead.

---

## 5. Rules of thumb

- **Know the name → `:Files`. Know the symbol → `:LspWorkspaceSymbol`. Know the text → `:Rg` or `:grep`.**
- **Exploring → `:Rg`. Acting on results → `:grep` + `:copen` + `:cdo`.**
- **`Ctrl-o` for "where I came from." `g;` for "where I last edited." They are not the same.**
- **`:bd` to close a buffer, `:q` to close a window.**
- **Open in a split from the picker (`Ctrl-v`/`Ctrl-x`) rather than navigating away — you keep both views.**
- **Before a project-wide rename, `:copen` and read the list. `:cfdo` is blind.**
- **If `:LspDefinition` does nothing, check `:LspStatus` — the server probably isn't running for that filetype.**
