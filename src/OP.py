import bpy
from bpy.props import IntProperty,StringProperty,BoolProperty
from bpy.types import Operator

from .utils import mix_materials,copy_nodes_from_mat_to_group,remove_material_output,add_group_outputs,clear_node_group,add_empty,add_height_controll_node,remove_controller,find_all_nodes_by_type,get_current_shader_output,add_material_copy,append_mixer_group,add_shader_group_to_nodes
from .report_msg import report_error,report_warning

class MixMaterialsOperator(Operator):
    '''Blends two materials together using linear interpolation or height information.'''
    bl_idname = "object.mix_materials"
    bl_label = "Mix Materials"

    def execute(self, context):
        scn = context.scene
        prop = scn.material_mixer_props
        material = context.material
        tree = material.node_tree
        nodes = tree.nodes
        material_output_node = get_current_shader_output(nodes)
        target_material = bpy.data.materials.get(prop.material_mixer_selector)
        if not material_output_node:
            report_error(self,'No Material Output Node')
            return {'CANCELLED'}
        if not material_output_node.inputs[0].is_linked:
            
            outputs_nodes = find_all_nodes_by_type(nodes,'OUTPUT_MATERIAL')
            material_output_node = None
            for n in outputs_nodes:
                if n.inputs[0].is_linked:
                    material_output_node = n
                    report_warning(self,'The active Material Output node has no shader link! \n Using any Material Output node with a connected shader input instead.')
                    break
            if not material_output_node:
                report_error(self,'Could not find a Material Output node with a linked shader input. \n Please link a shader input to the active Material Output node.')
                return {'CANCELLED'}
        mix_materials(material,target_material,material_output_node,context)
        return {'FINISHED'}

class UpdateMaterialOperator(Operator):
    '''Updates the material to apply any changes.'''
    bl_idname = "object.update_material"
    bl_label = "Update Material"

    material_index : IntProperty(default=0)

    def execute(self, context):
        material = context.material
        mix_prop = material.material_mixer_props.mixes[self.material_index]
        source_material = mix_prop.source_material
        mixer_node = mix_prop.get_mixer_node_group()
        if not mixer_node:
            report_error(self,'Could not found mixer node!\n It may have been deleted. Please delete the current mix.')
            return {'CANCELLED'}
        if not source_material:
            report_error(self,f'No material found with the name {source_material.name}.\n It may have been deleted.')
            return {'CANCELLED'}
        material_copy_node = material.node_tree.nodes.get(mix_prop.material_group_name)
        clear_node_group(material_copy_node)
        if not material_copy_node:
            #Wenn die Material Copy Node gelöscht wurde
            tree = mix_prop.owner_material.node_tree
            nodes = tree.nodes
            material_copy_node = add_material_copy(source_material,nodes)
            add_group_outputs(material_copy_node)
            remove_material_output(material_copy_node.node_tree.nodes)
            tree.links.new(material_copy_node.outputs[0],mixer_node.inputs[4])
            tree.links.new(material_copy_node.outputs[1],mixer_node.inputs[5])
            material_copy_node.location = mixer_node.location
            material_copy_node.location.y -= 500
            mix_prop.material_group_name = material_copy_node.name
            mix_prop.update_ground_obj(context)
            return {'FINISHED'}
        copy_nodes_from_mat_to_group(group=material_copy_node.node_tree,target_nodes=source_material.node_tree.nodes)
        add_group_outputs(material_copy_node,make_new_socket=False)
        remove_material_output(material_copy_node.node_tree.nodes)
        mix_prop.update_ground_obj(context)
        return {'FINISHED'}

class ControllerObjectHeight(Operator):
    '''Adds or removes control objects for height-based object blending.'''
    bl_idname = "object.contoller_object_height"
    bl_label = "SHI"
    material_index : IntProperty(default=0)
    do_delete : BoolProperty(default=False)
    def execute(self,context):
        material = context.material
        tree = material.node_tree
        mix_prop = material.material_mixer_props.mixes[self.material_index]
        if not mix_prop.get_mixer_node_group():
            report_error(self,'Could not found mixer node!\n It may have been deleted. Please delete the current mix.')
            return {'CANCELLED'}
        self.object = context.object
        if self.do_delete:
            self.remove_controller(mix_prop,tree)
        else:
            self.add_controller(mix_prop,tree,material)

        return{'FINISHED'}

    def add_controller(self,mix_prop,tree,material):
        mix_node = tree.nodes.get(mix_prop.mixer_group_name)
        min_empty = add_empty(f'{material.name}_Height_Min')
        max_empty = add_empty(f'{material.name}_Height_Max')
        if self.object:
            if self.object.parent:
                loc = self.object.matrix_world@self.object.location
            else:
                loc = self.object.location
                
            min_empty.location = loc
            max_empty.location = loc
            max_empty.location[2] += 1
        else:
            max_empty.location[2] += 1

        controller_group_node = add_height_controll_node(material.node_tree.nodes)
        controller_nodes = controller_group_node.node_tree.nodes
        controller_nodes.get('Min_Obj').object = min_empty
        controller_nodes.get('Max_Obj').object = max_empty
        
        tree.links.new(controller_group_node.outputs[0],mix_node.inputs[12])
        tree.links.new(controller_group_node.outputs[1],mix_node.inputs[13])

        mix_prop.min_max_group_name = controller_group_node.name
        mix_prop.min_obj = min_empty
        mix_prop.max_obj = max_empty
        mix_prop.using_controller = True
        mix_prop.update_using_controller(None)

    def remove_controller(self,mix_prop,tree):
        remove_controller(mix_prop,tree)

class DeleteMix(Operator):
    '''Removes the current mix.'''
    bl_idname = "object.delete_mix"
    bl_label = "Delete Mix"
    material_index : IntProperty(default=0)

    def execute(self,context):
        material = context.material
        prop = material.material_mixer_props
        mix_prop = prop.mixes[self.material_index]
        tree = material.node_tree
        nodes = tree.nodes
        if mix_prop.is_complex:
            if mix_prop.using_controller:
                remove_controller(mix_prop,tree)

        material_copy_node = nodes.get(mix_prop.material_group_name)
        if material_copy_node:
            nodes.remove(material_copy_node)

        mixer_node = nodes.get(mix_prop.mixer_group_name)
        if mixer_node:
            if mixer_node.inputs[0].is_linked and mixer_node.outputs[0].is_linked:
                from_socket = mixer_node.inputs[0].links[0].from_socket
                to_socket = mixer_node.outputs[0].links[0].to_socket
                tree.links.new(from_socket,to_socket)

            if mixer_node.inputs[1].is_linked:
                if mixer_node.outputs[2].is_linked:
                    from_socket = mixer_node.inputs[1].links[0].from_socket
                    to_socket = mixer_node.outputs[2].links[0].to_socket
                    tree.links.new(from_socket,to_socket)
                else:
                    #Link Displacement Output to Material Output Displacement 
                    displacement_input_from_node = mixer_node.inputs[1].links[0].from_node
                    #TODO falls shader output == None, Warning ausgeben
                    shader_output_node= get_current_shader_output(nodes)
                    if shader_output_node:
                        if displacement_input_from_node.type == 'GROUP' and displacement_input_from_node.node_tree.name.startswith('Material_Mixer_Group'):
                            tree.links.new(displacement_input_from_node.outputs[1],shader_output_node.inputs[2])
                        else:
                            #Sucht im Node Tree nach einer Displacement Node, deren Output nicht linked ist und verbindet die dann 
                            displacement_nodes = find_all_nodes_by_type(nodes,'DISPLACEMENT')
                            for n in displacement_nodes:
                                if not n.outputs[0].is_linked:
                                    tree.links.new(n.outputs[0],shader_output_node.inputs[2])
                        
            nodes.remove(mixer_node)


        prop.mixes.remove(self.material_index)
        return {'FINISHED'}

class ControllerSelect(Operator):
    '''Selects controll object.'''
    bl_idname = "object.contoller_select"
    bl_label = "Select controller object"
    material_index : IntProperty(default=0)
    controller_type : StringProperty(default='MIN')
    def execute(self,context):
        material = context.material
        mix_prop = material.material_mixer_props.mixes[self.material_index]
        self.deselect_all(context)
        if self.controller_type == 'MIN':
            if not mix_prop.min_obj:
                report_error(self,'No controller object found!')
                return {'CANCELLED'}
            mix_prop.min_obj.select_set(True)
            bpy.context.view_layer.objects.active = mix_prop.min_obj
        else:
            if not mix_prop.max_obj.users_scene:
                report_error(self,'No controller object found!')
                return {'CANCELLED'}
            mix_prop.max_obj.select_set(True)
            bpy.context.view_layer.objects.active = mix_prop.max_obj
        return{'FINISHED'}
    def deselect_all(self,context):
        selected = context.selected_objects
        for o in selected: 
            o.select_set(False)

class AddUtilsMixer(Operator):
    '''Adds a mixer node group, without adding a material mix.'''
    bl_idname = "object.material_mixer_utils_add_mixer"
    bl_label = ""

    mixer_type : StringProperty(default='SIMPLE')

    def execute(self,context):
        material = context.material
        tree = material.node_tree
        nodes = tree.nodes
        group_name = 'Material_Mixer_Group_Complex' if self.mixer_type=='COMPLEX' else 'Material_Mixer_Group'
        mixer_group = append_mixer_group(group_name)
        mixer_node = add_shader_group_to_nodes(mixer_group,nodes,is_copy=True,delete_og=True)
        mixer_node.location = tree.view_center
        return {'FINISHED'}

class AddUtilsMaterialCopy(Operator):
    '''Adds a material copy, without adding a mix node.'''
    bl_idname = "object.material_mixer_utils_add_material_copy"
    bl_label = ""

    def execute(self,context):
        scn = context.scene
        util_props = scn.material_mixer_utils_props
        material = context.material
        tree = material.node_tree
        nodes = tree.nodes
        target_material = bpy.data.materials.get(util_props.material_mixer_selector)
        material_copy_group = add_material_copy(target_material,nodes)
        add_group_outputs(material_copy_group)
        remove_material_output(material_copy_group.node_tree.nodes)
        material_copy_group.location = tree.view_center
        return {'FINISHED'}

CLASSES = [MixMaterialsOperator,UpdateMaterialOperator,ControllerObjectHeight,ControllerSelect,DeleteMix,AddUtilsMixer,AddUtilsMaterialCopy]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in CLASSES:
        bpy.utils.unregister_class(c)