import requests
from bs4 import BeautifulSoup
try: from rich import print
except Exception as e: pass
import uuid
import os
import platform

try: 
    with open("last_url.txt", "x") as f: pass
except Exception as e: pass

plat = platform.system()

if plat == "Windows":
    import ctypes
    
    def change_wallpaper(image_path):
        # Constants for setting the wallpaper
        SPI_SETDESKWALLPAPER = 20  # Action to change wallpaper
        SPIF_UPDATEINIFILE = 0x01  # Update user profile
        SPIF_SENDWININICHANGE = 0x02  # Notify change to system

        try:
            # Call Windows API to change wallpaper
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path,
                                                       SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
            return True
        except Exception as e:
            # Print error message if wallpaper change fails
            print(f"Error changing wallpaper: {e}")
            return False

elif plat == "Linux":
    '''
    This section was vibe coded by claude. This may or may not work. I dont have a linux system to test on.
    '''
    
    import subprocess
    import shutil

    def change_wallpaper(image_path: str) -> bool:
        """
        Set the desktop wallpaper on Linux.
        Tries multiple desktop environments and falls back gracefully.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            True if successful, False if no supported DE was detected.
        """
        image_path = os.path.abspath(image_path)

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        session = os.environ.get("DESKTOP_SESSION", "").upper()

        def run(cmd: list[str]) -> bool:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False

        # GNOME / Unity / Pop!_OS / Budgie
        if any(x in desktop for x in ("GNOME", "UNITY", "POP", "BUDGIE")):
            uri = f"file://{image_path}"
            for schema in (
                "org.gnome.desktop.background",
                "org.gnome.desktop.screensaver",
            ):
                run(["gsettings", "set", schema, "picture-uri", uri])
                run(["gsettings", "set", schema, "picture-uri-dark", uri])
            return True

        # KDE Plasma
        if "KDE" in desktop or "PLASMA" in desktop:
            script = f"""
    var allDesktops = desktops();
    for (var i = 0; i < allDesktops.length; i++) {{
        var d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
        d.writeConfig("Image", "file://{image_path}");
    }}
    """
            return run(["qdbus", "org.kde.plasmashell", "/PlasmaShell",
                        "org.kde.PlasmaShell.evaluateScript", script])

        # XFCE
        if "XFCE" in desktop or "XFCE" in session:
            result = subprocess.run(
                ["xfconf-query", "-c", "xfce4-desktop", "-lv"],
                capture_output=True, text=True
            )
            # Set wallpaper on every monitor/workspace property found
            success = False
            for line in result.stdout.splitlines():
                if "last-image" in line:
                    prop = line.split()[0]
                    if run(["xfconf-query", "-c", "xfce4-desktop",
                            "-p", prop, "-s", image_path]):
                        success = True
            return success

        # MATE
        if "MATE" in desktop:
            return run(["gsettings", "set", "org.mate.background",
                        "picture-filename", image_path])

        # Cinnamon
        if "CINNAMON" in desktop:
            return run(["gsettings", "set", "org.cinnamon.desktop.background",
                        "picture-uri", f"file://{image_path}"])

        # LXDE
        if "LXDE" in desktop:
            return run(["pcmanfm", "--set-wallpaper", image_path])

        # LXQt
        if "LXQT" in desktop:
            return run(["pcmanfm-qt", "--set-wallpaper", image_path])

        # Sway (Wayland tiling WM) — requires swaybg
        if "SWAY" in desktop or "SWAY" in session:
            return run(["swaybg", "-i", image_path])

        # Generic fallback: feh (works with most X11 WMs)
        if shutil.which("feh"):
            return run(["feh", "--bg-scale", image_path])

        # Last resort: xwallpaper
        if shutil.which("xwallpaper"):
            return run(["xwallpaper", "--zoom", image_path])

        return False

elif plat == "Darwin": 
    def change_wallpaper(image_path):
        # Use AppleScript to change the desktop wallpaper
        script = f"""
        osascript -e 'tell application "Finder" to set desktop picture to POSIX file "{image_path}"'
        """
        os.system(script)
        
else:
    print("[red]This device dosnt seem to be supported. you are welcome to implement support yourself. ")
    raise NotImplementedError

# Fetch image

nasa_home = requests.get("https://nasa.gov").content

soup = BeautifulSoup(nasa_home, 'html.parser')

# print(nasa_home)

image_url = soup.find_all(class_="hds-image-of-the-day")[0].find_all("a", href = True)[1]['href']


print(f"[cyan]image of the day url: {image_url}")

with open("last_url.txt", "w+", encoding="utf-8") as f:
    f.seek(0)
    if f.read() == image_url:
        print("[yellow]Image already loaded. Not downloading again")
        exit()
    else:
        f.write(image_url)

filename = str(uuid.uuid4()) + ".jpg"

img_data = requests.get(image_url).content
with open(filename, 'wb') as handler:
    handler.write(img_data)
    
print(f"[green]saved imaged as {filename}")

if change_wallpaper(os.path.abspath(filename)):
    print("[green]Changed wallpaper")
else:
    print("[red]wallpaperchange failed")
    exit()
    
os.remove(filename)

print("[green]Done!")