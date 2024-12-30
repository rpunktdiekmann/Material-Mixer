import bpy
import os
from bpy.utils import previews

preview_collections  = {}
def register():
    global preview_collections
    pcoll = previews.new()
    addon_dir = os.path.dirname(__file__)
    icon_path = os.path.join(addon_dir, "icons", "twitter_logo.png")
    pcoll.load("twitter_logo", icon_path, 'IMAGE')
    preview_collections["color_pal_icons"] = pcoll

def unregister():
    global preview_collections
    for pcoll in preview_collections.values():
        previews.remove(pcoll)
    preview_collections.clear()