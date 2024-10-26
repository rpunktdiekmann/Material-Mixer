import bpy 
from bpy.types import Panel


class NODE_PT_Material_Mixer(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Material Mixer"
    bl_label = "Material Mixer"

    @classmethod
    def poll(cls,context):
        return context.material is not None

    def draw(self, context):
        scn = context.scene
        prop = scn.material_mixer_props
        mat = context.material
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_x = 20
        row.label(text='New Mix')
        mix_settings_box = box.box()
        mix_settings_box.prop_search(prop, "material_mixer_selector", bpy.data, "materials")
        row = mix_settings_box.row()
        row.prop(prop,'ground_object',text='Ground Object')
        row = mix_settings_box.row()
        if not prop.ground_object:
            row.enabled = False
            row.label(text='No ground object selected',icon='ERROR')
        row.prop(prop,'change_obj_coord',text='Change Object Coords')
        row = mix_settings_box.row()
        if not prop.ground_object:
            row.enabled = False
            row.label(text='No ground object selected',icon='ERROR')
        elif not prop.ground_object.data.uv_layers:
            row.enabled = False
            row.label(text='Ground object has no UV data',icon='ERROR')
        row.prop(prop,'change_uv_maps',text='Change UV Map')
        if row.enabled and prop.change_uv_maps:
            row = mix_settings_box.row()
            row.prop(prop,'uv_selector',text='Target UV Map')
        row = mix_settings_box.row()
        row.prop(prop,'use_complex_mixer',text='Use complex Mixer')
        row = box.row()
        row.alert = bpy.data.materials.get(prop.material_mixer_selector) == mat
        if bpy.data.materials.get(prop.material_mixer_selector) == mat:
            row.label(text='Can not mix same material', icon='ERROR')
        else:
            row.scale_y = 2.0
            row.operator('object.mix_materials',icon='MATERIAL')
        if len(mat.material_mixer_props.mixes) > 0:
            draw_mixes(self,context,layout)


def draw_mixes(self,context,layout):
    material = context.material
    header,panel = layout.panel('mixes')
    header.label(text='All Mixes')
    if not panel:
        return
    for i, m in enumerate(material.material_mixer_props.mixes):
        box = panel.box()
        if not m.get_mixer_node_group():
            box.alert = True
            box.label(text='WARNING: Mixer Node have been deleted!',icon='ERROR')
        row = box.row()
        split = row.split(factor=0.09)
        split.prop(m,'group_color',text='')
        
        split.label(text=m.source_material.name,icon='MATERIAL')
        op = split.operator("object.update_material",text='Update',icon='RECOVER_LAST')
        op.material_index = i
        op = split.operator("object.delete_mix",text='Delete',icon='CANCEL')
        op.material_index = i
        if m.is_complex:
            row = box.row()
            row.prop(m,'using_height_blending',text='Enable height blending')
            row = box.row()
            row.prop(m,'using_object_blending',text='Enable object blending')
            row = box.row()
            row.prop(m,'ground_obj',text='Ground Object')
            box.separator(factor=0.25)    
            #Object Height Settings
            if m.using_object_blending:
                box = box.box()
                split = box.split()
                col = split.column()
                col.label(text='Object Height Blending')
                controller_height_text = 'Remove controller' if m.using_controller else 'Add controller'
                op = col.operator("object.contoller_object_height",text=controller_height_text)
                op.do_delete = m.using_controller
                op.material_index = i
                #Right Side
                split = split.split(factor=0.4)
                col = split.column()
                col.label(text='Blending Mode')
                col.label(text='Interpolation')
                col = split.column()
                col.prop(m,'object_blending_mode',text='')
                col.prop(m,'interpolation',text='')
            
                #Controller
                if m.using_controller:
                    row = box.row()
                    op = row.operator('object.contoller_select',text='Select Max',icon='RESTRICT_SELECT_OFF')
                    op.material_index = i
                    op.controller_type = 'MAX'
                    op = row.operator('object.contoller_select',text='Select Min',icon='RESTRICT_SELECT_OFF')
                    op.material_index = i
                    op.controller_type = 'MIN'
            panel.separator(factor=0.5)
                

class NODE_PT_Material_Mixer_Utils(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Material Mixer"
    bl_label = "Material Mixer Utils"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls,context):
        return context.material is not None

    def draw(self, context):
        scn = context.scene
        utils_prop = scn.material_mixer_utils_props
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text='Add mixer to node tree')
        row = box.row()
        row.operator('object.material_mixer_utils_add_mixer',text='Add simple mixer')
        op = row.operator('object.material_mixer_utils_add_mixer',text='Add complex mixer')
        op.mixer_type = 'COMPLEX'
        box = layout.box()
        row = box.row()
        row.alert = utils_prop.material_mixer_selector == context.material.name
        row.prop_search(utils_prop,'material_mixer_selector',bpy.data, "materials",text='')
        if utils_prop.material_mixer_selector == context.material.name:
            row.label(text='Can not mix same material', icon='ERROR')
        else:
            row.operator('object.material_mixer_utils_add_material_copy',text='Copy Material to Tree')

CLASSES = [NODE_PT_Material_Mixer,NODE_PT_Material_Mixer_Utils]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
