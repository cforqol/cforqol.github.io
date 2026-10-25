---
tags: [shell, cli, terminal, multiplexer]
---
# screen

GNU screen. Detach a session, come back later, keep the job running.

Every key below follows the prefix `++ctrl+a++`.

## Keys

| Key | Does |
|-----|------|
| `++ctrl+a++ ++c++` | new window |
| `++ctrl+a++ ++n++` / `++ctrl+a++ ++p++` | next / previous window |
| `++ctrl+a++ ++0++`–`++9++` | jump to window by number |
| `++ctrl+a++ ++"++` | window list |
| `++ctrl+a++ ++shift+a++` | rename window |
| `++ctrl+a++ ++d++` | **detach** — session keeps running |
| `++ctrl+a++ ++shift+d++` | detach and log out |
| `++ctrl+a++ ++k++` | kill window |
| `++ctrl+a++ ++shift+s++` | split horizontally |
| `++ctrl+a++ ++|++` | split vertically |
| `++ctrl+a++ ++tab++` | move between regions |
| `++ctrl+a++ ++shift+x++` | kill region |
| `++ctrl+a++ ++[++` | copy mode / scrollback |
| `++ctrl+a++ ++]++` | paste |
| `++ctrl+a++ ++shift+h++` | start or stop logging |
| `++ctrl+a++ ++?++` | key help |
| `++ctrl+a++ ++:++` | command prompt |

## Commands

| Command | Does |
|---------|------|
| `screen -S name` | new named session |
| `screen -ls` | list sessions |
| `screen -r name` | reattach |
| `screen -d -r name` | detach elsewhere, reattach here |
| `screen -x name` | attach without detaching (shared) |
| `screen -dmS name cmd` | start detached and run a command |
| `screen -S name -X quit` | kill a session |
| `screen -wipe` | clear dead session entries |
| `screen -L` | log the session to `screenlog.0` |

## Recipes

```bash
# start a named session
screen -S build

# ... work ... then detach with: Ctrl-a d

# list what's running
screen -ls

# come back
screen -r build

# "already attached" — take it over instead
screen -d -r build

# fire and forget, from a script or cron
screen -dmS backup /usr/local/bin/backup.sh

# kill a stuck session
screen -S build -X quit

# clear zombie entries
screen -wipe

# log everything in this session
screen -L -S audit
```

`~/.screenrc` worth having:

```
startup_message off
defscrollback 10000
hardstatus alwayslastline "%{= kG}%-Lw%{= kW}%50>%n%f* %t%{= kG}%+Lw%< %{= kG}%=[%H]"
```

## Gotchas

- **Detach is `++ctrl+a++ ++d++`.** `Ctrl-D` closes the shell and kills the window.
- `screen -r` fails with "already attached" when the session is open elsewhere. `-d -r` steals it, `-x` joins it without stealing.
- `++ctrl+a++ ++a++` sends a literal `Ctrl-A` through to the app. You need it in vim and emacs.
- **Sessions do not survive a reboot.** Nothing restores them. `screen -wipe` clears the corpses.
- `-x` is shared attach — both terminals see and type. Great for pairing, confusing if you forget.
- Scrollback is `++ctrl+a++ ++[++`, then arrows or PageUp. `q` exits. Not mouse-driven by default.
- Set `defscrollback` high. The default 100 lines is useless for a build log.
- Screen's config syntax is gnarly and it's barely maintained. tmux is the more common choice — but screen ships on more boxes by default, which is why it's worth keeping in your fingers.

