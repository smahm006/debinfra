# Login shells: environment only (interactive setup lives in .zshrc)
. "$ZDOTDIR/environment"
[ -f "$HOME/lab/toolchains/rust/.cargo/env" ] && . "$HOME/lab/toolchains/rust/.cargo/env"
