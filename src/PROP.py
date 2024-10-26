import bpy
from bpy.props import EnumProperty,PointerProperty,BoolProperty, CollectionProperty, StringProperty,FloatVectorProperty
from bpy.types import Object,Material,PropertyGroup
from .utils import generate_material_items,generate_uv_items,find_all_nodes_by_type

class MaterialMixerMaterialMix(PropertyGroup):
    
    def update_using_height_blending(self,context):
        mixer_node=self.get_mixer_node_group()
        if not mixer_node:
            return
        mixer_node.inputs[8].default_value = self.using_height_blending
    
    def update_object_blending(self,context):
        mixer_node=self.get_mixer_node_group()
        if not mixer_node:
            return
        mixer_nodes = mixer_node.node_tree.nodes
        blending_node = mixer_nodes.get('Object_Height_Mode')
        blending_node.operation = self.object_blending_mode

    def update_using_object_blending(self,context):
        mixer_node=self.get_mixer_node_group()
        if not mixer_node:
            return
        mixer_node.inputs[11].default_value = self.using_object_blending

        mixer_nodes = mixer_node.node_tree.nodes
        mode_nodes = ('Object_Height_Mode')
        for node_name in mode_nodes:
            blending_node = mixer_nodes.get(node_name)
            if self.using_object_blending:
                blending_node.operation = self.object_blending_mode
            else:
                blending_node.operation = 'MULTIPLY'


    def update_interpolation(self,context):
        map_range_name = 'Map Range.001'
        nodes = self.owner_material.node_tree.nodes
        mixer_node = nodes.get(self.mixer_group_name)
        if not mixer_node:
            return
        map_range_node = mixer_node.node_tree.nodes.get(map_range_name)
        map_range_node.interpolation_type = self.interpolation

    def update_using_controller(self,context):
        tex_coord_name = 'Texture Coordinate'
        mixer_node = self.get_mixer_node_group()
        if not mixer_node:
            return
        mixer_nodes = mixer_node.node_tree.nodes
        if self.using_controller:
            mixer_nodes.get(tex_coord_name).object = None
        else:
            mixer_nodes.get(tex_coord_name).object = self.ground_obj
        

    def update_ground_obj(self,context):
        if not self.using_controller and not self.using_object_blending:
            tex_coord_name = 'Texture Coordinate'
            mixer_node = self.get_mixer_node_group()
            if not mixer_node:
                return
            tex_coord_node = mixer_node.node_tree.nodes.get(tex_coord_name)
            tex_coord_node.object = self.ground_obj
        
        material_group = self.get_material_copy_group()
        if not material_group:
            print('Could not find material group, it may have been deleted')
            return
        material_nodes = material_group.node_tree.nodes
        tex_nodes = find_all_nodes_by_type(material_nodes,'TEX_COORD')
        for n in tex_nodes:
            n.object = self.ground_obj

    def update_color(self,context):
        mixer_node=self.get_mixer_node_group()
        if not mixer_node:
            return
        mixer_node.color = self.group_color
    
    owner_material : PointerProperty(type=Material)
    source_material : PointerProperty(type=Material)
    material_group_name : StringProperty(default='')
    mixer_group_name : StringProperty(default='')
    is_complex : BoolProperty(default=False)
    #Complex Mixer Props
    ground_obj : PointerProperty(type=Object,update=update_ground_obj)
    using_height_blending : BoolProperty(default=True,update=update_using_height_blending)
    is_change_object_coords : BoolProperty(default=False)
    is_change_uv_map : BoolProperty(default=False)#to implement
    #Props für Object Height Blend
    using_object_blending : BoolProperty(default=False,update=update_using_object_blending)
    using_controller : BoolProperty(default=False,update=update_using_controller)
    object_blending_mode : EnumProperty(items=[('MULTIPLY','Multiply','Where both masks intersect'),('MAXIMUM','Add','Adding to Mask')],update=update_object_blending)
    interpolation : EnumProperty(items=[('LINEAR','Linear','Using Linear'),('SMOOTHSTEP','Smooth','Using SMOOTH'),('SMOOTHERSTEP','Smoother','Using Smoother')],update=update_interpolation)
    #Props für Object Min_Max evt. in eine PropertyGroup
    min_max_group_name : StringProperty(default='')
    min_obj : PointerProperty(type=Object)
    max_obj : PointerProperty(type=Object)

    group_color : FloatVectorProperty(subtype='COLOR',update=update_color,min=0.0,max=1.0)
    
    def get_mixer_node_group(self):
        nodes = self.owner_material.node_tree.nodes
        group = nodes.get(self.mixer_group_name)
        if not group:
            print('Could not find mixer group, it may have been deleted')
        return group

    def get_material_copy_group(self):
        nodes = self.owner_material.node_tree.nodes
        group = nodes.get(self.material_group_name)
        return group

class MaterialMixerMaterialProps(PropertyGroup):
    mixes : CollectionProperty(type=MaterialMixerMaterialMix)

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
    

class MaterialMixerUtilsProps(PropertyGroup):
    material_mixer_selector : EnumProperty(
        name="Material",
        description="Select a material",
        items=generate_material_items,
        )


CLASSES = [MaterialMixerMaterialMix,MaterialMixerMaterialProps,MaterialMixerProps,MaterialMixerUtilsProps]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    Material.material_mixer_props = PointerProperty(type=MaterialMixerMaterialProps)
    bpy.types.Scene.material_mixer_props = PointerProperty(type=MaterialMixerProps)
    bpy.types.Scene.material_mixer_utils_props = PointerProperty(type=MaterialMixerUtilsProps)

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.material_mixer_props
    del bpy.types.Scene.material_mixer_utils_props