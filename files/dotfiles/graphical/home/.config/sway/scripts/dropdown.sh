#!/usr/bin/env bash

# Check if the dropdown window exists in the tree
if swaymsg -t get_tree | grep -q '"app_id": "foot-dropdown"'; then

  # Check if the dropdown is currently the active, focused window
  if swaymsg -t get_tree | jq -e '.. | select(.focused? == true and .app_id == "foot-dropdown")' >/dev/null 2>&1; then

    # Check if it is currently fullscreen
    if swaymsg -t get_tree | jq -e '.. | select(.focused? == true and .app_id == "foot-dropdown" and .fullscreen_mode == 1)' >/dev/null 2>&1; then
      # If fullscreen, un-fullscreen it and snap it back to your 60% size layout
      swaymsg "fullscreen disable; resize set 60 ppt 60 ppt; move position center"
    else
      # If open but not fullscreen, hide it back into the scratchpad
      swaymsg '[app_id="foot-dropdown"] scratchpad show'
    fi

  else
    # If the dropdown exists but is hidden in scratchpad, pull it out, size it, and center it
    swaymsg '[app_id="foot-dropdown"] scratchpad show; resize set 60 ppt 60 ppt; move position center'
  fi

else
  # Launch it fresh if it doesn't exist
  foot --app-id foot-dropdown &
fi
