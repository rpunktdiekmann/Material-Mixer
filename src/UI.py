import bpy 
from bpy.types import Panel


class NODE_PT_Material_Mixer(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Material Mixer"
    bl_label = "Material Mixer"

    def draw(self, context):
        scn = context.scene
        prop = scn.material_mixer_props
        mat = context.material
        layout = self.layout

        layout.prop_search(prop, "material_mixer_selector", bpy.data, "materials")
        box = layout.box()
        row = box.row()
        row.prop(prop,'ground_object',text='Ground Object')
        row = box.row()
        if not prop.ground_object:
            row.enabled = False
            row.label(text='No ground object selected',icon='ERROR')
        row.prop(prop,'change_obj_coord',text='Change Object Coords')
        row = box.row()
        if not prop.ground_object:
            row.enabled = False
            row.label(text='No ground object selected',icon='ERROR')
        elif not prop.ground_object.data.uv_layers:
            row.enabled = False
            row.label(text='Ground object has no UV data',icon='ERROR')
        row.prop(prop,'change_uv_maps',text='Change UV Map')
        if row.enabled and prop.change_uv_maps:
            row = box.row()
            row.prop(prop,'uv_selector',text='Target UV Map')
        row = layout.row()
        row.prop(prop,'use_complex_mixer',text='Use complex Mixer')
        row = layout.row()
        if bpy.data.materials.get(prop.material_mixer_selector) == mat:
            row.label(text='Can not mix same material', icon='ERROR')
        else:
            row.scale_y = 2.0
            row.operator('object.mix_materials',icon='MATERIAL')

CLASSES = [NODE_PT_Material_Mixer]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
