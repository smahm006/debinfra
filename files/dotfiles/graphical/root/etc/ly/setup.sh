#!/bin/sh
case $SHELL in
*/bash)
  [ -z "$BASH" ] && exec $SHELL "$0" "$@"
  set +o posix
  [ -f "/etc/profile" ]         && . "/etc/profile"
  [ -f "$HOME/.bash_profile" ]  && . "$HOME/.bash_profile" \
  || { [ -f "$HOME/.bash_login" ] && . "$HOME/.bash_login"; } \
  || { [ -f "$HOME/.profile" ]    && . "$HOME/.profile"; }
  ;;
*/zsh)
  [ -z "$ZSH_NAME" ] && exec $SHELL "$0" "$@"
  [ -d "/etc/zsh" ] && zdir="/etc/zsh" || zdir="/etc"
  zhome=${ZDOTDIR:-"$HOME"}
  [ -f "$zdir/zprofile" ] && . "$zdir/zprofile"
  [ -f "$zhome/.zprofile" ] && . "$zhome/.zprofile"
  ;;
*)
  [ -f "/etc/profile" ]   && . "/etc/profile"
  [ -f "$HOME/.profile" ] && . "$HOME/.profile"
  ;;
esac
exec "$@"
