import bpy 
import os
from pathlib import Path
from itertools import cycle

node_color_list = [[0.067600, 0.550380, 1.000000],[1.000000, 0.204258, 0.134375],[0.291712, 0.144129, 1.000000],
    [1.000000, 0.184242, 0.451761],[0.926385, 0.220595, 1.000000],[1.000000, 0.621973, 0.130095],
    [0.515016, 1.000000, 0.269065],[0.141472, 1.000000, 0.315565],[0.114951, 1.000000, 0.903986]]
color_pool = cycle(node_color_list)

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

def remove_controller(mix_prop,tree):
    nodes = tree.nodes 
    min_max_group = nodes.get(mix_prop.min_max_group_name)
    if min_max_group:
        nodes.remove(min_max_group)
    if mix_prop.min_obj:
        bpy.data.objects.remove(mix_prop.min_obj)
    if mix_prop.max_obj:
        bpy.data.objects.remove(mix_prop.max_obj)
    mix_prop.min_obj = None
    mix_prop.max_obj = None
    mix_prop.using_controller = False

def find_all_nodes_by_type(nodes,node_type:str):
    result = []
    for n in nodes:
        if n.type == node_type:
            result.append(n)
    return result

def add_group_outputs(group,make_new_socket=True):
    tree = group.node_tree
    nodes = tree.nodes

    if make_new_socket:
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
   
def add_empty(name):
    empty = bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(empty)
    empty.show_name = True
    empty.show_in_front = True
    return empty

def append_mixer_group(group_name):
    working_dir = Path(__file__).parent.absolute()
    dir_name = os.path.join(working_dir,'material_mixer_group.blend')
    if not bpy.data.node_groups.get(group_name):
        with bpy.data.libraries.load(dir_name, link=False) as (data_from, data_to):
            data_to.node_groups = [group_name]
    return bpy.data.node_groups.get(group_name)

def add_shader_group_to_nodes(target_node_tree,nodes,is_copy=True,delete_og=False):
    group_node = nodes.new('ShaderNodeGroup')
    if is_copy:
        group_node.node_tree = target_node_tree.copy()
    else:
        group_node.node_tree = target_node_tree
    if delete_og:
        bpy.data.node_groups.remove(target_node_tree)
    return group_node

def link_mixer(material_output_node,mixer_node,target_material_group_node,tree,is_complex):
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
    if is_complex:
        tree.links.new(target_material_group_node.outputs[0],mixer_node.inputs[4])
        tree.links.new(target_material_group_node.outputs[1],mixer_node.inputs[5])
    else:
        tree.links.new(target_material_group_node.outputs[0],mixer_node.inputs[3])
        tree.links.new(target_material_group_node.outputs[1],mixer_node.inputs[4])
    
    tree.links.new(mixer_node.outputs[0],material_output_node.inputs[0])
    tree.links.new(mixer_node.outputs[1],material_output_node.inputs[2])

def add_mixer_to_tree(nodes,use_complex=False,ground_object=None):
    group_name = 'Material_Mixer_Group_Complex' if use_complex else 'Material_Mixer_Group'
    mixer_group = append_mixer_group(group_name)
    mixer_node = add_shader_group_to_nodes(mixer_group,nodes,is_copy=True,delete_og=True)
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

def mix_materials(material, target_material,material_output_node,context):
    displacement_strenght_a = 0.0
    displacement_strenght_b = 0.0
    node_tree = material.node_tree
    scn = context.scene
    obj = context.object
    nodes = node_tree.nodes
    prop = scn.material_mixer_props

    mixer_node = add_mixer_to_tree(nodes,use_complex=prop.use_complex_mixer,ground_object=prop.ground_object)
    mixer_node.location = material_output_node.location
    material_output_node.location.x += 250

    target_material.node_tree.use_fake_user = True
    target_material_group_node = add_material_copy(target_material,nodes)
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

    # durchschnitt der displacement 
    dis_node_a = find_all_nodes_by_type(nodes,'DISPLACEMENT')
    if dis_node_a:
        displacement_strenght_a = dis_node_a[0].inputs['Scale'].default_value
    dis_node_b = find_all_nodes_by_type(target_material_group_node.node_tree.nodes,'DISPLACEMENT')
    if dis_node_b:
        displacement_strenght_a = dis_node_a[0].inputs['Scale'].default_value
    strenght_avg = (displacement_strenght_a+displacement_strenght_b)/2
    if prop.use_complex_mixer:
        mixer_node.inputs[15].default_value = strenght_avg
    else:
        mixer_node.inputs[7].default_value = strenght_avg

    link_mixer(material_output_node,mixer_node,target_material_group_node,node_tree,prop.use_complex_mixer)
    remove_material_output(target_material_group_node.node_tree.nodes)
    mixer_node.use_custom_color = True
    node_color = get_color()
    add_material_prop(material,target_material,target_material_group_node.name,mixer_node.name,prop.use_complex_mixer,prop,node_color,prop.ground_object)
    mixer_node.color = node_color
    
def add_material_copy(target_material,nodes):
    group = bpy.data.node_groups.new( name=target_material.name+'_copy', type="ShaderNodeTree" )
    target_nodes = target_material.node_tree.nodes
    copy_nodes_from_mat_to_group(target_nodes,group)
    group_node = nodes.new('ShaderNodeGroup')
    group_node.node_tree = group
    return group_node

def copy_nodes_from_mat_to_group(target_nodes,group):
    copy_nodes(target_nodes, group)
    copy_links(target_nodes, group)

def add_material_prop(material,target_material,material_group_name,mixer_group_name,is_complex,scn_prop,node_color,ground_obj=None):
    mixer_var = material.material_mixer_props.mixes.add()
    mixer_var.owner_material = material
    mixer_var.source_material = target_material
    mixer_var.material_group_name = material_group_name
    mixer_var.mixer_group_name = mixer_group_name
    mixer_var.is_complex = is_complex
    mixer_var.ground_obj = ground_obj
    mixer_var.is_change_object_coords = scn_prop.change_obj_coord
    mixer_var.is_change_uv_map = scn_prop.change_uv_maps
    mixer_var.group_color = node_color

def copy_links(nodes, group):
    for node in nodes:
        if node.type == 'FRAME':#wenn NodeFrame kopiert wird, crasht das ganze    Error   : EXCEPTION_ACCESS_VIOLATION
            continue
        new_node = group.nodes[ node.name ]
        for i, inp in enumerate( node.inputs ):
            for link in inp.links:
                connected_node = group.nodes[ link.from_node.name ]
                group.links.new( connected_node.outputs[ link.from_socket.name ], new_node.inputs[i] )

def copy_nodes(nodes, group):
    input_attributes = ( "default_value", "name" )
    output_attributes = ( "default_value", "name" )
    for node in nodes:
        if node.type == 'FRAME':#wenn NodeFrame kopiert wird, crasht das ganze    Error   : EXCEPTION_ACCESS_VIOLATION
            continue
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
    ignore_attributes = ( "rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select","parent")#Crash wenn Frame, also parent blacklisten
    attributes = []
    for attr in node.bl_rna.properties:
        if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
            attributes.append(attr.identifier)
    return attributes

def add_height_controll_node(nodes):
    group_name = 'Material_Mixer_Obj_Min_Max_Group'
    controller_node_group = append_mixer_group(group_name)
    node = add_shader_group_to_nodes(controller_node_group,nodes)
    return node
    
def get_current_shader_output(nodes):
    #Gibt den aktiven Material Output aus, falls keiner aktiv ist, wird der erste inaktive zurück gegeben, None falls keine Material Output existiert
    shader_outputs = find_all_nodes_by_type(nodes,'OUTPUT_MATERIAL')
    if not shader_outputs: return None
    first_inactive_output = None
    for n in shader_outputs:
        if n.is_active_output:
            return n
        if not first_inactive_output: first_inactive_output=n
    return first_inactive_output

def get_color():
    return next(color_pool)

def clear_node_group(group):
    if not group:
        return
    tree = group.node_tree
    nodes = tree.nodes 
    for n in nodes:
        nodes.remove(n)