import bpy
from bpy.props import EnumProperty,PointerProperty,BoolProperty
from bpy.types import Object,PropertyGroup
from .utils import generate_material_items,generate_uv_items

class MaterialMixerProps(PropertyGroup):
    material_mixer_selector : EnumProperty(
        name="Material",
        description="Select a material",
        items=generate_material_items,
        )
    change_obj_coord : BoolProperty(default=False)
    change_uv_maps : BoolProperty(default=False)
    ground_object : PointerProperty(type=Object)
    use_complex_mixer : BoolProperty(default=False)
    uv_selector : EnumProperty(
        name="Material",
        description="Select a material",
        items=generate_uv_items,
        )


CLASSES = [MaterialMixerProps]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

    bpy.types.Scene.material_mixer_props = PointerProperty(type=MaterialMixerProps)
    

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.material_mixer_props