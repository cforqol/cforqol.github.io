---
tags: [screen, screenrc, terminal, gnu-screen]
---

# GNU Screen: Caption Strings and Command Mode

How the caption line is built, and what `C-a :` is for — written against screen 4.9.0.

## Prerequisites

- `screen` 4.9.x. Escape sets differ in 5.0: `%s`, `%h` and the colour letters are not interchangeable between them.
- A `~/.screenrc`.
- `C-a` is still the command character. If it's remapped, substitute yours below.

## Why it's built this way

The caption is a status bar. `caption always` keeps it on screen all the time instead of only during split-screen. It's the only bar on the display — no `hardstatus` line exists — so it's also the only thing you can put anything in.

The line I started from was:

```screenrc
caption always "%3n %t%? @%u%?%? [%h]%?%=%c"
```

Three things in it are wrong.

**`%h` is not window height.** It's the window's hardstatus, which is empty unless something set one. There is no height escape; `%s` is window size. So `[%h]` rendered as `[]` and looked like a bug.

**The `%?` wrapper around `[%h]` was fine.** A conditional is true only if a `%` escape inside it expands to non-empty, and `"0"` counts as non-empty — but `%h` expands to `""`, not `"0"`, so the wrapper does work. It's the manual's own idiom: `%?%F%{.R.}%?%3n %t%? [%h]%?`. The bug was the escape inside it, not the conditional.

**`%u` is "all other users on this window", not your username.** In a single-user session it's empty, so `%? @%u%?` prints nothing at all. It only shows anything in a multiuser session, and then it exposes those users' names.

What was kept: window number, title, the right-hand clock, and `%=` as the filler that pushes the clock to the edge.

## Setup

### 1. The caption line

```screenrc
caption always "%3n %t%=%c"
```

### 2. Escapes used

| Escape | Meaning |
|---|---|
| `%3n` | Window number, padded to 3 columns |
| `%t` | Window title |
| `%=` | Filler, pushes everything after it to the right edge |
| `%c` | Current time, 24h `HH:MM` |
| `%s` | Window size, `WxH` — use this if you wanted height |
| `%h` | Window's hardstatus, empty unless set |
| `%u` | Other users attached to this window |
| `%?` … `%?` | Conditional block — `if` … `endif` |
| `%:` | `else` branch of a conditional |
| `%F` | True when the window has focus. Prints nothing itself |

### 3. What it renders

Two spaces, the window number, the title, filler, the clock:

```
  1 bash                                                      14:32
```

### 4. Adding a real condition

The only escape that works as a test is `%F` (focus) or `%P` (in copy mode). Focus highlighting, if/else done properly:

```screenrc
caption always "%?%F%{= rW}%:%{= wW}%?%3n %t%=%c"
```

`%{= rW}` sets reverse plus a red background with bright white text; `%{= wW}` is the same in default colours. Close every `%{` with `}` or the escape renders literally.

If you want the hardstatus back in the caption, keep the conditional around it: `%? [%h]%?`.

### 5. Applying it

```
C-a :source ~/.screenrc
```

Nothing here needs a restart, and nothing here ports to tmux — tmux uses `status-left` / `status-right` with `#[...]` styling instead.

### 6. Command mode

`C-a :` is the `colon` binding. It opens a `:` prompt on the bottom line and takes any command valid in a screenrc, so it's how you change a setting on a live session.

Editing the prompt: Tab completes commands and filenames, Up/Down walk history, `C-u` clears the line, `C-c` or Esc aborts.

### 7. Windows and layout

| Command | Does |
|---|---|
| `screen 3` | New window, numbered 3 |
| `split` / `split -v` | Split horizontally / vertically |
| `focus up`, `focus next` | Move input focus |
| `only` / `remove` | Drop all regions but this one / drop this region |
| `resize 15` | Set this region to 15 lines |
| `layout save mylayout` | Remember the current arrangement |
| `number 7` | Renumber this window to 7 |
| `title build` | Set the window title |

### 8. Lifecycle

| Command | Does |
|---|---|
| `kill` | Destroy this window |
| `zombie` | Keep dead windows in the list |
| `at 3 stuff "make^M"` | Run a command in window 3 |

### 9. Input

| Command | Does |
|---|---|
| `stuff "ssh host^M"` | Type into the window. `^M` is Enter, `^C` is interrupt |
| `paste .` | Paste the buffer |
| `slowpaste 30` | Pause 30 ms between pasted characters |

### 10. Session control

| Command | Does |
|---|---|
| `detach` / `pow_detach` | Detach / detach and hang up |
| `suspend` | Suspend screen |
| `quit` | Kill every window and exit |
| `wall` | Message all displays |
| `multiuser on` | Allow other users to attach |
| `acladd user`, `aclchg user +rwx` | Add a user, then grant them access |

### 11. Appearance, live

| Command | Does |
|---|---|
| `caption always "%3n %t%=%c"` | Replace the caption |
| `defscrollback 10000` | Default scrollback for new windows |
| `bind /` | Remove the binding on `/` |
| `escape ^Bb` | Move the command character to `C-b` |
| `msgwait 0` | Don't wait on the message line |
| `startup_message off` | Skip the copyright notice |

### 12. Window-local fixes

| Command | Does |
|---|---|
| `encoding utf-8` | Set this window's encoding |
| `wrap off` | Turn off line wrap |
| `logfile ~/log/%n.txt`, `log on` | Start logging, one file per window |
| `su user` | Substitute the user of this display |

### 13. Housekeeping

| Command | Does |
|---|---|
| `source ~/.screenrc` | Re-read the config |
| `eval "..."` | Run a quoted command |
| `version`, `info` | Version, window state |
| `verbose on` | Echo the command name as windows are created |

### 14. From the shell

`screen -X <command>` sends the same command to a running session, which is what makes this scriptable: `screen -X stuff "ls^M"`. It doesn't work on a password-protected session.

`C-a ?` lists key bindings. `man screen`, section `CUSTOMIZATION`, lists every command.

## Gotchas

!!! warning
    **No undo on `kill` or `quit`.** `kill` takes the window and its process with it. `quit` takes the session and every window in it.

!!! warning
    **Single quotes suppress `^M`.** The screenrc parser converts `^X` to a control byte, but skips that conversion inside single quotes — so `stuff 'make^M'` types a literal `^M`. Double-quote it: `stuff "make^M"`.

!!! warning
    **`$` expands at parse time, quoted or not.** `stuff "echo $HOME"` types the resolved path, not the word. Protect it with a backslash: `stuff "echo \$HOME^M"`. Single quotes protect `$` but cost you `^M`, so double quotes plus `\$` is the working combination.

!!! warning
    **`#` starts a comment even mid-command.** A `#` preceded by whitespace ends the line. Quote the string, or escape it as `\#`.

!!! warning
    **The caption is bottom-only and permanent.** With `always` there is no fallback bar, so a broken escape is visible on every window until you fix it. Test in `C-a :` first.

!!! warning
    **`%u` names other users.** On a shared box that's a small disclosure. It's also empty when you're alone, which is what makes the wrapper look broken.

## If it breaks

| Symptom | Cause | Fix |
|---|---|---|
| Caption never appears | `caption` left at the default `splitonly`, which only shows it in split screen | `caption always "..."` |
| Caption shows bare `[]` | `%h` with no hardstatus set | Wrap it — `%? [%h]%?` — or use `%s` for size |
| `@user` never shows | Single-user session; `%u` lists *other* users only | `multiuser on` plus `acladd`, or drop the escape |
| Escape renders as literal text | `%{` with no closing `}` | Close it, or remove the escape |
| `C-a :` does nothing | Command character remapped, or you're in copy mode | Check `escape`; press Esc first |
| `stuff` types the literal `^M` | Argument single-quoted | Double-quote it |
| `stuff` types a resolved path | `$` expanded at parse time | `\$` |
| `source` warns and skips a line | Unquoted `#` treated as a comment | Quote the string |
| `screen -X` does nothing | Session is password-protected | `auth off` |
```

One consequence worth knowing: with no `date:` and no change log, nothing on the page records when it was written. `git log -1 --format=%cs -- docs/handbook/screen-caption-and-command-mode.md` still answers it, and that's what `zfs/` pages rely on too.
