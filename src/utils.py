import bpy 
import os
from pathlib import Path

def generate_material_items(self,context):
    return [(m.name,m.name,'') for m in bpy.data.materials if not m.is_grease_pencil]

def generate_uv_items(self,context):
    scn = context.scene
    prop = scn.material_mixer_props
    if not prop.change_uv_maps:
        return []
    obj = prop.ground_object
    return [(uv.name,uv.name,'')for uv in obj.data.uv_layers]

def add_data_transfer(obj,ground,uv_map_name_src:str ,uv_map_name_dst:str):
    modi = obj.modifiers.new('Material Mixer Transfer','DATA_TRANSFER')
    modi.object = ground
    modi.use_loop_data = True
    modi.data_types_loops = {'UV'}
    modi.layers_uv_select_src = uv_map_name_src
    modi.layers_uv_select_dst = uv_map_name_dst
    modi.loop_mapping = 'POLYINTERP_NEAREST'

    n = len(obj.modifiers)-1
    if n > 0:
        obj.modifiers.move(n,0)



def find_all_nodes_by_type(nodes,node_type:str):
    result = []
    for n in nodes:
        if n.type == node_type:
            result.append(n)
    return result

def add_group_outputs(group):
    tree = group.node_tree
    nodes = tree.nodes

    tree.interface.new_socket(name="Shader", in_out='OUTPUT',socket_type='NodeSocketShader')
    tree.interface.new_socket(name="Displacement", in_out='OUTPUT',socket_type='NodeSocketFloat')
    output_node = nodes.new('NodeGroupOutput')

    material_output_node = nodes.get("Material Output")
    if material_output_node.inputs[0].is_linked:
        shader_socket = material_output_node.inputs[0].links[0].from_socket
        tree.links.new(shader_socket,output_node.inputs[0])

    if material_output_node.inputs[2].is_linked:
        displacement_node = material_output_node.inputs[2].links[0].from_node
        if displacement_node.inputs[0].is_linked:
            displacement_socket = displacement_node.inputs[0].links[0].from_socket
            tree.links.new(displacement_socket,output_node.inputs[1])

    

def append_mixer_group(use_complex = False):
    group_name = 'Material_Mixer_Group_Complex' if use_complex else 'Material_Mixer_Group'
    working_dir = Path(__file__).parent.absolute()
    dir_name = os.path.join(working_dir,'material_mixer_group.blend')
    if not bpy.data.node_groups.get(group_name):
        with bpy.data.libraries.load(dir_name, link=False) as (data_from, data_to):
            data_to.node_groups = [group_name]
    return bpy.data.node_groups.get(group_name)

def add_shader_group_to_nodes(target_node_tree,nodes,is_copy=True):
    group_node = nodes.new('ShaderNodeGroup')
    if is_copy:
        group_node.node_tree = target_node_tree.copy()
    else:
        group_node.node_tree = target_node_tree
    return group_node


def link_mixer(material_output_node,mixer_node,target_material_group_node,tree):
    shader_input_socket = material_output_node.inputs[0].links[0].from_socket
    tree.links.new(shader_input_socket,mixer_node.inputs[0])

    if material_output_node.inputs[2].is_linked:
        displacement_node = material_output_node.inputs[2].links[0].from_node
        if displacement_node.type == 'GROUP' and displacement_node.node_tree.name.startswith('Material_Mixer'):
            tree.links.new(displacement_node.outputs[2],mixer_node.inputs[1])
        else:
            if displacement_node.inputs[0].is_linked:
                displacement_input_socket = displacement_node.inputs[0].links[0].from_socket
                tree.links.new(displacement_input_socket,mixer_node.inputs[1])
    
    tree.links.new(target_material_group_node.outputs[0],mixer_node.inputs[3])
    tree.links.new(target_material_group_node.outputs[1],mixer_node.inputs[4])
    tree.links.new(mixer_node.outputs[0],material_output_node.inputs[0])
    tree.links.new(mixer_node.outputs[1],material_output_node.inputs[2])



def add_mixer_to_tree(nodes,use_complex=False,ground_object=None):
    mixer_group = append_mixer_group(use_complex=use_complex)
    mixer_node = add_shader_group_to_nodes(mixer_group,nodes)
    if use_complex and ground_object:
        set_texture_coords(mixer_node,ground_object=ground_object)
    return mixer_node


def set_texture_coords(group,ground_object=None):
    tree = group.node_tree
    nodes = tree.nodes
    tex_coord_nodes = find_all_nodes_by_type(nodes,'TEX_COORD')
    for node in tex_coord_nodes:
        if ground_object:
            node.object = ground_object

def swap_uv_map(tree,uv_map_name):
    nodes = tree.nodes
    uv_node = nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = uv_map_name
    for n in find_all_nodes_by_type(nodes,'TEX_COORD'):
        for l in n.outputs[2].links:
            tree.links.new(uv_node.outputs[0],l.to_socket)
        

def remove_material_output(nodes):
    material_output_node = nodes.get("Material Output")
    nodes.remove(material_output_node)


def mix_materials(node_tree, target_material,context):
    scn = context.scene
    obj = context.object
    nodes = node_tree.nodes
    material_output_node = nodes.get("Material Output")
    prop = scn.material_mixer_props

    mixer_node = add_mixer_to_tree(nodes,use_complex=prop.use_complex_mixer,ground_object=prop.ground_object)
    mixer_node.location = material_output_node.location
    material_output_node.location.x += 250

    target_material.node_tree.use_fake_user = True
    #target_material_group_node = add_shader_group_to_nodes(target_material.node_tree,nodes,is_copy=True)
    target_material_group_node = copy_nodes_from_mat_to_group(target_material,nodes)
    if not find_all_nodes_by_type(target_material_group_node.node_tree.nodes,'GROUP_OUTPUT'):
        add_group_outputs(target_material_group_node)
    if prop.change_obj_coord and prop.ground_object:
        set_texture_coords(target_material_group_node,ground_object=prop.ground_object)
    if prop.change_uv_maps and prop.ground_object:
        uv_map_name = 'MM_UV_Transfer_Map' + str(obj.data.uv_layers)
        obj.data.uv_layers.new(name=uv_map_name)
        add_data_transfer(obj,prop.ground_object,prop.uv_selector,uv_map_name)
        swap_uv_map(target_material_group_node.node_tree,uv_map_name)
    target_material_group_node.location = mixer_node.location
    target_material_group_node.location.y -= 500

    link_mixer(material_output_node,mixer_node,target_material_group_node,node_tree)
    remove_material_output(target_material_group_node.node_tree.nodes)

def copy_nodes_from_mat_to_group(target_material,nodes):
    group = bpy.data.node_groups.new( name=target_material.name+'_copy', type="ShaderNodeTree" )
    target_nodes = target_material.node_tree.nodes
    copy_nodes(target_nodes, group)
    copy_links(target_nodes, group)
    group_node = nodes.new('ShaderNodeGroup')
    group_node.node_tree = group
    return group_node




def copy_links(nodes, group):
    for node in nodes:
        new_node = group.nodes[ node.name ]
        for i, inp in enumerate( node.inputs ):
            for link in inp.links:
                connected_node = group.nodes[ link.from_node.name ]
                group.links.new( connected_node.outputs[ link.from_socket.name ], new_node.inputs[i] )


def copy_nodes(nodes, group):
    input_attributes = ( "default_value", "name" )
    output_attributes = ( "default_value", "name" )
    for node in nodes:
        new_node = group.nodes.new( node.bl_idname )
        node_attributes = get_node_attributes(node)
        copy_attributes(node_attributes, node, new_node )
        for i, inp in enumerate(node.inputs):
            copy_attributes(input_attributes,inp,new_node.inputs[i] )
        for i, out in enumerate(node.outputs):
            copy_attributes(output_attributes,out,new_node.outputs[i] )


def copy_attributes(attributes, old_prop, new_prop):
    for attr in attributes:
        if hasattr( new_prop, attr ):
            try:
                setattr( new_prop, attr, getattr( old_prop, attr ) )
            except:
                pass


def get_node_attributes(node):
    ignore_attributes = ( "rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select")
    attributes = []
    for attr in node.bl_rna.properties:
        if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
            attributes.append(attr.identifier)
    return attributes
