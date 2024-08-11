import bpy
from bpy.types import Operator

from .utils import mix_materials

class MixMaterialsOperator(Operator):
    bl_idname = "object.mix_materials"
    bl_label = "Mix Materials"

    def execute(self, context):
        scn = context.scene
        prop = scn.material_mixer_props
        material = context.material
        tree = material.node_tree
        nodes = tree.nodes
        material_output_node = nodes.get("Material Output")
        target_material = bpy.data.materials.get(prop.material_mixer_selector)
        if not material_output_node:
            self.report({'ERROR'}, 'No Material Output Node')
            return {'CANCELLED'}
        mix_materials(tree,target_material,context)
        return {'FINISHED'}

CLASSES = [MixMaterialsOperator]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)