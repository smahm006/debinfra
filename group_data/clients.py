from group_data.all import (  # noqa: F401
    lab_home,
    org_home,
    user_home,
    xdg_cache_home,
    xdg_config_home,
    xdg_data_home,
)

xdg_config_group = [
    f"{xdg_config_home}/emacs",
    f"{xdg_config_home}/maven",
    f"{xdg_config_home}/aws",
    # graphical stack (all clients run sway — laptop and vm alike)
    f"{xdg_config_home}/sway",
    f"{xdg_config_home}/sway/config.d",
    f"{xdg_config_home}/sway/scripts",
    f"{xdg_config_home}/swaync",
    f"{xdg_config_home}/rofi",
    f"{xdg_config_home}/waybar",
    f"{xdg_config_home}/foot",
    f"{xdg_config_home}/swaylock",
    f"{xdg_config_home}/gtk-2.0",
    f"{xdg_config_home}/gtk-3.0",
    f"{xdg_config_home}/gtk-4.0",
]

xdg_data_group = [
    f"{xdg_data_home}/wine",
    f"{xdg_data_home}/fonts",
    f"{xdg_data_home}/fonts/MapleMono",
    f"{xdg_data_home}/fonts/NerdFontsSymbolsOnly",
    f"{xdg_data_home}/fonts/SourceCodePro",
    f"{xdg_data_home}/icons",
    f"{xdg_data_home}/themes",
    f"{xdg_data_home}/terminfo",
    f"{xdg_data_home}/.pki",
]

xdg_cache_group = [
    f"{xdg_cache_home}/X11",
]

xdg_home_group = [
    f"{lab_home}/projects",
    f"{lab_home}/projects/private",
    f"{lab_home}/projects/public",
    f"{lab_home}/projects/archive",
    f"{lab_home}/projects/sandbox",
    f"{lab_home}/vms",
    f"{lab_home}/vms/vagrant",
    f"{user_home}/media",
    f"{user_home}/media/audio",
    f"{user_home}/media/videos",
    f"{user_home}/media/images",
    f"{user_home}/media/images/wallpaper",
    f"{user_home}/media/images/screenshot",
    f"{user_home}/media/images/misc",
    f"{user_home}/apps",
    org_home,
    f"{org_home}/books",
    f"{org_home}/inbox",
    f"{org_home}/notes",
    f"{org_home}/records",
]
