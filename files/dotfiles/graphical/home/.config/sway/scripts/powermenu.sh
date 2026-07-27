#!/usr/bin/env bash
# mod+0 power menu: power actions via swayexit, notifications via swaync.
set -eu

entries=(
  "  Lock"
  "󰂚  Notifications"
  "󰤄  Suspend"
  "󰒲  Hibernate"
  "󰍃  Logout"
  "󰜉  Reboot"
  "󰐥  Poweroff"
)

choice=$(printf '%s\n' "${entries[@]}" | rofi -dmenu -i -p "⏻" \
  -theme-str 'window { width: 20%; } listview { lines: 7; } inputbar { children: [ prompt ]; }')

case "${choice#*  }" in
  Lock)          swayexit lock ;;
  Notifications) swaync-client -t -sw ;;
  Suspend)       swayexit suspend ;;
  Hibernate)     swayexit hibernate ;;
  Logout)        swayexit logout ;;
  Reboot)        swayexit reboot ;;
  Poweroff)      swayexit shutdown ;;
  *)             exit 0 ;;
esac
