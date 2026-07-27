#!/usr/bin/env bash
# SUDO_ASKPASS helper: prompt for a password with rofi, echo it to stdout.
pass=$(rofi -dmenu -password -p "󰌾 ${1:-Password}" \
  -theme-str 'window { width: 20%; } mainbox { children: [ inputbar ]; }')
[ -z "$pass" ] && exit 1
printf '%s\n' "$pass"
