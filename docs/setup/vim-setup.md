# My Personal Vim Setup

Vim version: gVim 9.x recommended; minimum **Vim 7.3.885+ with `+lua`**  
Plugin manager: vim-plug  
Config location: `~/.vimrc` and `~/.gvimrc`

## 1. Purpose

This document describes how I install, configure, and use my personal **gVim** setup.
It is intended as a reference for rebuilding the environment on a new machine
and for remembering daily workflows.

**Scope:** gVim only. No Neovim. Git is used from the terminal, not inside Vim.

## 2. Why gVim, not Neovim

I use gVim because it is the GUI build of Vim and stays close to traditional Vim
keybindings and Ex commands. Neovim is a fork with a different runtime/API model
and intentionally different defaults, so it is excluded from this setup.

## 3. Install gVim with Lua first

### Minimum version

Use **Vim 7.3.885 or later compiled with `+lua`**.
For dynamic Lua loading, Vim 8.0+ supports `+lua/dyn`.
A separate `lua` binary in `PATH` is not the same as Vim's `+lua` API integration.

### Linux install examples

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install vim-gtk3   # or vim-gtk

# Arch
sudo pacman -S gvim

# Fedora
sudo dnf install vim-X11
```

Ubuntu's gVim package is `vim-gtk`/`vim-gtk3`; Arch's is `gvim`.

### Windows install

Install official gVim.
For `+lua/dyn`, put the matching Lua DLL beside `gvim.exe` or in `PATH`;
`:echo has('lua')` should return `1`. You can also set the `luadll` option to
point at the Lua DLL.

### macOS install

Use MacVim or a Homebrew Vim build compiled with `+lua`, then verify with the
commands below.

### Verify Lua support

```vim
:version
:echo has('lua')
:lua print('lua ok')
```

`:version` should show `+lua` or `+lua/dyn`.
If it shows `+lua/dyn`, Vim loads Lua only when needed; the Lua DLL/shared
library must still be findable.

### Python support (for gundo)

Python is **not** bundled with gVim. Vim must be compiled with `+python3` or
`+python3/dyn`, and for dynamic builds a matching Python 3 runtime must be
installed and findable (on Windows, `python3xx.dll` beside `gvim.exe` or in
`PATH`, or set `:set pythonthreedll=...`).

```vim
:echo has('python3')
:py3 print('ok')
```

If unavailable, use `mbbill/undotree` instead of `sjl/gundo.vim`.

## 4. Install Plugin Manager

Using vim-plug:

```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```

## 5. Plugins I Use

| Plugin | Purpose |
|---|---|
| `tpope/vim-vinegar` | Enhances built-in netrw (`-` opens parent dir) |
| `junegunn/fzf` | Fuzzy finder engine (binary) |
| `junegunn/fzf.vim` | `:Files`, `:GFiles`, `:Rg`, `:Buffers`, `:BLines`, `:Lines` |
| `tpope/vim-surround` | Add/change/delete surrounding chars |
| `tpope/vim-commentary` | Comment/uncomment (`gcc`, `gc`) |
| `jiangmiao/auto-pairs` | Auto-close brackets/quotes |
| `prabirshrestha/vim-lsp` | Lightweight LSP client (client only — needs a server) |
| `prabirshrestha/vim-lsp-settings` | Auto-registers servers, adds `:LspInstallServer` |
| `dense-analysis/ale` | Async lint/fix (optional — see 6.6) |
| `sjl/gundo.vim` | Undo tree (requires `+python3`; else use `mbbill/undotree`) |
| `kshenoy/vim-signature` | Mark visualizer (sign column) |
| `vim-airline/vim-airline` | Statusline |
| `vim-airline/vim-airline-themes` | Airline themes |
| `lifepillar/vim-solarized8` | Solarized colorscheme |
| `preservim/vim-markdown` | Markdown support |
| `dhruvasagar/vim-table-mode` | Markdown table editing |

The `Plug` declarations live in `VIMRC.md`. Install with:

```vim
:PlugInstall
```

## 6. QoL Plugin Usage

### 6.1 vim-lsp + vim-lsp-settings

vim-lsp is a **client only** — it needs a language server installed separately
(`pylsp`, `gopls`, `rust-analyzer`, `typescript-language-server`, ...). It spawns
the server as a background job on file open. No server = no features for that
filetype. It defines no default mappings.

**Install a server** — open a file of the target type, then:

```vim
:LspInstallServer
```

Detects the filetype, installs the matching server, registers it. Once per
language. Check what's running with `:LspStatus`.

#### Offline / no-internet use

vim-lsp itself **never needs the network**. The server is a local process and
LSP traffic goes over stdio pipes, not TCP. Once a server is installed and
running, everything works with no connection.

The only network step is `:LspInstallServer` — it downloads the server binary.
For a fully offline machine:

1. Install the server on a connected machine (`:LspInstallServer`, or your
   package manager / `pip` / `npm` / `cargo`).
2. Copy the binary to the offline machine and put it on `PATH`.
3. vim-lsp-settings will find it and register it — no download attempted.

LSP servers are just programs on your `PATH`; how they get there is up to you.
On Windows you may need a Windows-specific build. If `:LspInstallServer` fails
offline, that's expected — the server is already there, so just use it.

| Command | Action |
|---|---|
| `:LspDefinition` | Go to definition |
| `:LspDeclaration` | Go to declaration |
| `:LspTypeDefinition` | Go to type definition |
| `:LspImplementation` | Go to implementation |
| `:LspReferences` | Find all references |
| `:LspHover` | Hover docs |
| `:LspRename` | Rename symbol |
| `:LspDocumentSymbol` | Symbols in current file |
| `:LspWorkspaceSymbol` | Symbols in project |
| `:LspCodeAction` | Quick fixes, auto-imports, extract |
| `:LspDocumentFormat` | Format buffer via LSP |
| `:LspDocumentHighlight` | Highlight all occurrences in buffer |
| `:LspSelectionExpand` / `:LspSelectionShrink` | Scope-aware selection |
| `:LspDiag` | Diagnostics → location list |
| `:LspStatus` | Running servers |
| `:LspRestartServer` / `:LspStopServer` | Restart / stop |

**Completion** — no asyncomplete needed. In insert mode:

```text
<C-x><C-o>    omnifunc completion (LSP-backed)
```

Keymaps for the LSP commands live in `VIMRC.md`.

Diagnostics appear in the sign column automatically once a server is running.

### 6.2 gundo (undo tree)

Requires `+python3` (or `+python`). If your gVim lacks Python, use
`mbbill/undotree` instead (pure Vimscript).

- `:GundoToggle` — open/close the undo tree
- Navigate with `j`/`k`/`h`/`l`
- Press `<CR>` on a state to restore it
- The diff preview shows what changes

Fully local — no network access.

### 6.3 vim-signature (marks)

- `ma` — set mark `a` at the cursor
- `mx` — toggle a mark on the current line
- `m,` — place the next free mark
- `m/` — list all marks
- `m<Space>` — purge marks in current buffer
- `]'` / `['` — jump to next/prev mark line
- Marks show in the sign column automatically

Fully local — no network access.

### 6.4 auto-pairs

- `(` `[` `{` `"` `'` `` ` `` auto-close on insert
- `<BS>` in an empty pair deletes both
- `<CR>` between a pair expands to a multi-line block
- Skip over a closing char instead of inserting a duplicate

Fully local — no network access.

### 6.5 vim-table-mode

- `:TableModeToggle` — toggle table mode
- Type `|` to create a table; it auto-formats as you type
- `:TableModeRealign` — realign an existing table

### 6.6 ALE (linting/fixing)

ALE hooks Vim's autocmds and runs linters as background jobs, so linting happens
while you type without blocking. It does **not** auto-detect your project — it
fires on `TextChanged` / `InsertLeave` / `BufWritePost`. By default it runs every
linter it knows for that filetype, which is why it can feel heavy.

Commands: `:ALELint`, `:ALEFix`, `:ALENext` / `:ALEPrevious`, `:ALEInfo`,
`:ALEToggle`.

To keep it light: lint and fix on save only (not on every keystroke), and list
linters explicitly rather than letting ALE run everything. The exact
`g:ale_linters` / `g:ale_fixers` settings live in `VIMRC.md`.

Linters are local binaries — no network at runtime.

## 7. Daily Workflow

### Open a project

```bash
cd <project-dir>
gvim .
```

### Find and open files

- `:Files` — all files under cwd
- `:GFiles` — git-tracked only (reads git's index; runs no git commands)
- `:Buffers` — already-open buffers
- `:BLines` / `:Lines` — fuzzy search lines in current / all open buffers

### Search inside files

- `:Rg pattern` — interactive picker (exploring)
- `:grep pattern` + `:copen` — persistent list (acting on results)

### Edit with splits

```vim
:vs <file>   " vertical split
:sp <file>   " horizontal split
```

Navigate splits with `<C-h>`, `<C-j>`, `<C-k>`, `<C-l>`.

### LSP workflow

- `:LspDefinition` go to definition
- `:LspReferences` find references
- `:LspHover` hover docs
- `:LspRename` rename symbol
- `:LspCodeAction` quick fixes / auto-import

### Lua usage examples

```vim
:lua print('hello from lua')
:echo luaeval('math.pi')
```

These require a gVim build with `+lua` or `+lua/dyn`.

## 8. Maintenance

Update plugins:

```vim
:PlugUpdate
```

Clean unused plugins:

```vim
:PlugClean
```

Check plugin status:

```vim
:PlugStatus
```

Back up config:

```bash
cp ~/.vimrc ~/.vimrc.bak
cp ~/.gvimrc ~/.gvimrc.bak
cp -r ~/.vim ~/.vim.bak
```

Reproducibility (pin plugin versions):

```vim
:PlugSnapshot ~/.vim/plugins.lock    " write lock file
:PlugRestore  ~/.vim/plugins.lock    " restore exact versions
```

## 9. Troubleshooting

| Problem | Check |
|---|---|
| Plugin not loading | `:PlugStatus`, then `:PlugInstall` |
| Lua not available | `:echo has('lua')` → `1`; `:version` shows `+lua` or `+lua/dyn` |
| `+lua/dyn` but Lua fails | Install matching Lua shared library or set `luadll` |
| Windows Lua missing | Put matching Lua DLL beside `gvim.exe` or in `PATH` |
| gundo fails to load | `:echo has('python3')` → `1`; else use `mbbill/undotree` |
| LSP does nothing | `:LspStatus` — server probably not running for that filetype |
| `:LspInstallServer` fails offline | Expected — install the server elsewhere, copy it onto `PATH` |
| Clipboard not working | `set clipboard=unnamedplus`; install `xclip`/`wl-clipboard` |
| Slow startup | `gvim --startuptime /tmp/gvim.log`, inspect plugins |
| Keymap conflict | `:verbose map <key>` |
| Where was an option set? | `:verbose set <option>?` |
| Startup errors | `:messages` |
| Load order | `:scriptnames` |

## 10. Quick Cheatsheet

```text
i        insert mode
Esc      normal mode
:w       save
:q       quit
:wq      save and quit
:q!      quit without saving
u        undo
Ctrl-r   redo
/word    search
n        next search result
N        previous search result
gg       top of file
G        bottom of file
0        start of line
\$        end of line
dd       delete line
yy       yank line
p        paste
```

## 11. Rebuild Checklist

- [ ] Install gVim with Lua support: **Vim 7.3.885+ with `+lua`**
- [ ] Verify `:echo has('lua')` returns `1`
- [ ] Verify `:echo has('python3')` returns `1` (for gundo)
- [ ] Install vim-plug
- [ ] Copy `~/.vimrc` and `~/.gvimrc` (see `VIMRC.md`)
- [ ] Run `:PlugInstall`
- [ ] Run `:LspInstallServer` per language (needs internet once)
- [ ] Test fuzzy finder, LSP, clipboard, Lua

## 12. Built-in Vim Workflows

Plugins cover LSP, fuzzy finding, and editing. This section covers built-in Vim
features that add real daily value with zero dependencies.

### 12.1 Search & Quickfix

`:grep` uses `grepprg` — set it to ripgrep for speed and `--vimgrep` output:

- `grepprg=rg --vimgrep --smart-case --hidden` (or drop `--hidden` to skip dotfiles)
- `grepformat=%f:%l:%c:%m` (matches `--vimgrep` output)

No ripgrep? Use system `grep -rnH`. No external tool at all? `:vimgrep` is
built-in, slower, zero deps. Exact `set` lines live in `VIMRC.md`.

**Search commands:**

| Command | Fills quickfix? | Notes |
|---|---|---|
| `:grep pattern` | Yes | Runs `grepprg` in cwd |
| `:grep pattern src/` | Yes | Restrict to subdirectory |
| `:grep -tpy pattern` | Yes | rg: Python only (`-t` = type; `rg --type-list`) |
| `:vimgrep /pattern/ **/*.java` | Yes | Built-in, no external tool |
| `:Rg pattern` | No | fzf.vim interactive picker |
| `:BLines` | No | Fuzzy search current buffer |
| `:Lines` | No | Fuzzy search all open buffers |

**Quickfix navigation:**

| Command | Action |
|---|---|
| `:copen` / `:cclose` | Open / close quickfix window |
| `:cwindow` | Open only if list is non-empty |
| `:cnext` / `:cprev` | Next / previous hit |
| `:cfirst` / `:clast` | First / last hit |
| `:cc 5` | Jump to hit #5 |
| `:clist` | Print all hits |
| `:colder` / `:cnewer` | Back/forward through previous lists |

**Act on every hit:**

| Command | Runs on |
|---|---|
| `:cdo cmd` | Each entry (each line) |
| `:cfdo cmd` | Each file (once per file) |

Both accept `| update` to write. Examples:

```vim
:cdo s/oldName/newName/g | update
:cfdo %s/oldName/newName/g | update
```

Always `:copen` and review before `:cfdo` — it's a blind bulk edit.

**Workflows:**

- Where is X defined? `:grep def parse_config` → `:copen` → Enter on a hit.
- All references before changing? `:grep --fixed-strings get_user_id` → `:copen`.
  (`--fixed-strings`/`-F` prevents regex metachar interpretation.)
- Project-wide rename (no LSP): `:grep -F oldName` → review →
  `:cfdo %s/oldName/newName/g | update`. `:LspRename` is safer when available.
- Search part of the tree: `:grep -tpy TODO src/api/` — `-t` filters by filetype
  (`py`, `js`, `ts`, `rust`, `go`, `java`, `c`, `cpp`, `sh`, `md`, ...).
- Which files touch a config key? `:grep -F DATABASE_URL` → `:copen`.
- Exploring → `:Rg`. Acting on results → `:grep` + `:copen`.
- Return to a previous search: `:colder` / `:cnewer`.

(`]q`/`[q` for `:cnext`/`:cprev` are not built-in — either map them yourself
or add `tpope/vim-unimpaired`. Mappings live in `VIMRC.md`.)

### 12.2 Jump List & Changelist

Every `:LspDefinition`, `:grep` Enter, `G`/`gg`/`/` is recorded.

| Key/Cmd | Action |
|---|---|
| `Ctrl-o` | Jump back |
| `Ctrl-i` | Jump forward |
| `g;` | Previous change location |
| `g,` | Next change location |
| `:jumps` | Show jump list |
| `:changes` | Show change list |

Scenarios: after `:LspDefinition` lands you in another file, `Ctrl-o` returns
instantly. After editing and scrolling away, `g;` restores the edit spot.

### 12.3 Reindent (`=`)

| Command | Action |
|---|---|
| `gg=G` | Reindent whole file |
| `=` (visual) | Reindent selection |
| `==` | Reindent current line |

Scenarios: pasted code from Slack/GitHub has broken indentation → `gg=G`. Added
an `if` block by hand, body not indented → `==` on that line. Requires
`filetype indent on`.

### 12.4 Format text (`gq` / `gw`)

`gq` reformats to `textwidth`. `gw` does the same but keeps cursor position.

| Command | Action |
|---|---|
| `gqap` | Format current paragraph |
| `gqq` | Format current line |

Scenarios: long lines in a markdown doc or comment → `gqap`. Accidental
400-char line in code → `gqq`. Skip if you never write prose in Vim.

### 12.5 Text Objects

Pattern: `[operator][i|a][object]` — `i` = inner, `a` = around (includes
delimiters).

| Command | Meaning |
|---|---|
| `ciw` | Change inner word |
| `ci"` | Change inside quotes |
| `ci(` / `ci{` | Change inside parens/braces |
| `cit` | Change inside HTML/XML tag |
| `dat` | Delete around tag (tag included) |
| `yip` / `vip` | Yank / select inner paragraph |
| `di[` | Delete inside brackets |

Scenarios: cursor inside a string → `ci"` replaces the whole string. Editing
function args → `ci(` clears the arg list. HTML/JSX → `cit`/`dat`.

### 12.6 `gn` / `gN` — search-and-select

`gn` selects the next match of the last search. Killer combo: `cgn` + `.`

Scenario — local rename without LSP:

```text
/oldName        search
cgn             type newName, Esc
.               repeat on next match
.               again
```

`dgn` deletes, `ygn` yanks the next match.

### 12.7 Bulk editing (`:g`, `:v`, `:norm`, `:argdo`)

| Command | Effect |
|---|---|
| `:g/pattern/d` | Delete matching lines |
| `:v/pattern/d` | Delete non-matching lines |
| `:g/pattern/normal @q` | Run macro on matching lines |
| `:g/^$/d` | Delete blank lines |
| `:%s/\s\+$//e` | Strip trailing whitespace |
| `:argdo %s/a/b/ge \| update` | Sub across `:args` files |

Scenarios: log file, keep only `ERROR` lines → `:v/ERROR/d`. Strip trailing
whitespace repo-wide → `:args **/*.py` then `:argdo %s/\s\+$//e | update`.

### 12.8 `Ctrl-x` completion submodes

| Combo | Completes |
|---|---|
| `<C-x><C-f>` | Filenames (the useful one) |
| `<C-x><C-l>` | Whole lines from buffer |
| `<C-x><C-o>` | Omni (LSP) |
| `<C-x><C-n>` | Keywords from buffer |

Scenarios: typing an import path or `#include` → `<C-x><C-f>`. Repetitive
boilerplate (similar struct fields) → `<C-x><C-l>`.

### 12.9 Buffer commands

| Command | Why |
|---|---|
| `:bd` | Close buffer without closing window (vs `:q` on a split) |
| `:ls` | List buffers with numbers |
| `:b 3` | Jump to buffer 3 |
| `Ctrl-w o` | Close all other splits |
| `Ctrl-w =` | Equalize split sizes |

`:bd` matters: `:q` on a quick-look split leaves the buffer loaded; `:bd`
removes it.

### 12.10 Folding

Use `foldmethod=indent` — works in every language with no per-filetype setup.
`foldmethod=syntax` is nicer but slower on big files. Start with folds open
(`foldlevel=99`). Exact `set` lines live in `VIMRC.md`.

| Key | Action |
|---|---|
| `za` | Toggle fold under cursor |
| `zo` / `zc` | Open / close |
| `zR` / `zM` | Open / close all |
| `zj` / `zk` | Next / previous fold |

Scenario: 800-line file → `zM` collapses everything, `zo` on what you care about.
