# If not running interactively, don't do anything
[[ -o interactive ]] || return

# -- History ------------------------------------------------------------------
export HISTFILE="$HOME/.local/state/zsh/history"
export HISTSIZE=10000
export SAVEHIST=10000
setopt INC_APPEND_HISTORY     # write as commands run, not on exit
setopt HIST_IGNORE_SPACE      # like bash HISTCONTROL=ignorespace
setopt HIST_IGNORE_ALL_DUPS
setopt EXTENDED_HISTORY

# -- Emacs-style word movement (Alt+B/Alt+F/Alt+D) ----------------------------
WORDCHARS=''

# -- Completion ---------------------------------------------------------------
autoload -Uz compinit
mkdir -p "$HOME/.cache/zsh"
compinit -d "$HOME/.cache/zsh/zcompdump"
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# -- Custom Bindings  ---------------------------------------------------------
bindkey '^[[Z' reverse-menu-complete

# -- Custom environment (base + drop-in overrides) ----------------------------
. "$ZDOTDIR/environment"
if [ -d "$ZDOTDIR/environment.d" ]; then
  for i in "$ZDOTDIR/environment.d/"*(N); do
    [ -r "$i" ] && . "$i"
  done
  unset i
fi

# -- Custom aliases -----------------------------------------------------------
. "$ZDOTDIR/alias"
if [ -d "$ZDOTDIR/alias.d" ]; then
  for i in "$ZDOTDIR/alias.d/"*(N); do
    [ -r "$i" ] && . "$i"
  done
  unset i
fi

# -- Custom functions ---------------------------------------------------------
. "$ZDOTDIR/function"
if [ -d "$ZDOTDIR/function.d" ]; then
  for i in "$ZDOTDIR/function.d/"*(N); do
    [ -r "$i" ] && . "$i"
  done
  unset i
fi

# -- Emacs Integration  ------------------------------------------------------
[ -n "$EAT_SHELL_INTEGRATION_DIR" ] && \
  source "$EAT_SHELL_INTEGRATION_DIR/zsh"

# -- Prompt -------------------------------------------------------------------
if command -v starship > /dev/null; then
  eval "$(starship init zsh)"
fi

# -- Atuin — history search (Ctrl-R) -------------------------------------------
if command -v atuin > /dev/null; then
  eval "$(atuin init zsh)"
fi

# -- Zoxide - smarter cd (replaces the cd builtin; cdi to pick interactively) --
# Must come after the alias/function files are sourced so nothing redefines cd.
if command -v zoxide > /dev/null; then
  eval "$(zoxide init zsh --cmd cd)"
fi

# -- GPG agent as SSH agent ---------------------------------------------------
export GPG_TTY=$(tty)
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
gpgconf --launch gpg-agent
gpg-connect-agent updatestartuptty /bye > /dev/null

# -- Plugins (syntax highlighting must be sourced LAST) -----------------------
if [ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
  . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
  # Ctrl+Space accepts the current suggestion (terminals send NUL/^@ for it)
  bindkey '^@' autosuggest-accept
fi
if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
  . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi
