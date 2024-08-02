import os, glob
import hou

from .modules.settings_preset_template import SettingsPresetTemplate

materialx_import_library_name = 'materialx_import_library'
materialx_suffix = 'MATx'

default_texture_file_extensions =  ["jpg", "exr", "png"]

TEXTURE_DICT = {
    "BASE_COLOR": ["diffuse", "diff", "base-color", "basecolor", "base_color", "albedo", "color"],
    "ROUGHNESS": ["roughness", "gloss", "glossiness"],
    "NORMAL": ["normal", "bumb"],
    "AO": ["ao", "ambient_occlusion", "ambient-occlusion", "ambient_occlusion", "ambientocclusion"],
    "DISPLACEMENT": ["displacement", "height"],
    "TRANSLUCENCY": ["translucency", "transparency", "transmission", "reflaction"],
    "OPACITY": ["opacity", "alpha"],
    "METALNESS": ["metallic", "metalness", "metallicity", "metal"]
}

def import_materialx(texture_folder_path, material_full_name, material_import_library, settings: SettingsPresetTemplate, maps_dictionary: dict = TEXTURE_DICT):
    
    # Material subnet cleared
    mat_subnet: hou.VopNode = material_import_library.createNode("subnet", material_full_name)
    for node in mat_subnet.children():
            node.destroy()
    mat_subnet.setMaterialFlag(True)
    
    # All files whit the desired extensions in the texture folder
    textures_files_list = list_files_with_extensions(texture_folder_path)

    # Base maps
    base_color = filter_maps(textures_files_list, maps_dictionary.get("BASE_COLOR"), "Base Color")
    roughness = filter_maps(textures_files_list, maps_dictionary.get("ROUGHNESS"), "Roughness")
    normal = filter_maps(textures_files_list, maps_dictionary.get("NORMAL"), "Normal")

    # Optional maps
    metalness = None if not settings.metalness else filter_maps(textures_files_list, maps_dictionary.get("METALNESS"), "Metalness")
    ao = None if not settings.ao else filter_maps(textures_files_list, maps_dictionary.get("AO"), "Ambient Occlusion")
    translucency = None if not settings.translucency else filter_maps(textures_files_list, maps_dictionary.get("TRANSLUCENCY"), "Translucency")
    opacity = None if not settings.opacity else filter_maps(textures_files_list, maps_dictionary.get("OPACITY"), "Opacity")
    displacement = None if not settings.displacement else filter_maps(textures_files_list, maps_dictionary.get("DISPLACEMENT"), "Displacement")
    
    create_materialx_network(mat_subnet, base_color, roughness, normal, metalness, ao, translucency, opacity, displacement, settings.color_variation, settings.translucency)

    mat_subnet.layoutChildren()

def create_materialx_network(material_subnet, base_color, roughness, normal, metalness=None, ao=None, translucency=None, opacity=None, displacement=None, color_variation=False, translucent=False):

    houdini_version = hou.applicationVersion()

    mtlxstandard_surface: hou.VopNode = material_subnet.createNode("mtlxstandard_surface", "mtlxstandard_surface")

    # ----- Base Color -----
    if base_color:
        base_color_map: hou.VopNode = material_subnet.createNode("mtlximage", "Base_Color")
        base_color_map.parm("file").set(base_color)
        #
        if houdini_version < (20, 0, 0):
            base_color_correction: hou.VopNode = material_subnet.createNode("hmtlxcolorcorrect", "Base_Color_Correction")
        else:
            base_color_correction: hou.VopNode = material_subnet.createNode("mtlxcolorcorrect", "Base_Color_Correction")
        #
        base_color_correction.setInput(base_color_correction.inputIndex("in"), base_color_map)
        color_out = base_color_correction
    else:
        base_color: hou.VopNode = create_vop_parameter(material_subnet, "Base_Color", "color", "base_color", "Base Color")
        color_out = base_color
    
    # ----- Color Variation -----
    if color_variation:
        #
        if houdini_version < (20, 0, 0):
            variation_color_correct: hou.VopNode = material_subnet.createNode("hmtlxcolorcorrect", "Cariation_Color_Correct")
        else:
            variation_color_correct: hou.VopNode = material_subnet.createNode("mtlxcolorcorrect", "Cariation_Color_Correct")
        variation_color_correct.setInput(variation_color_correct.inputIndex("in"), base_color_correction)
        #
        color_variation_attribute:hou.VopNode = material_subnet.createNode("mtlxgeompropvalue", "ColorVariationAttribute")
        color_variation_attribute.parm("geomprop").set("ColorVariation")
        color_variation_attribute.parm("default").set(1)
        #
        color_mix: hou.VopNode = material_subnet.createNode("mtlxmix", "VariationMix")
        color_mix.setInput(color_mix.inputIndex("fg"), variation_color_correct)
        color_mix.setInput(color_mix.inputIndex("bg"), base_color_correction)
        color_mix.setInput(color_mix.inputIndex("mix"), color_variation_attribute)
        color_out = color_mix
    
    # ----- AO -----
    if ao:
        #
        ao_correct: hou.VopNode = material_subnet.createNode("mtlximage", "AO")
        ao_correct.parm("file").set(ao)
        ao_correct.parm("signature").set("color")
        #
        ao_mutiply: hou.VopNode = material_subnet.createNode("mtlxmultiply", "AO_mutiply")
        ao_mutiply.parm("signature").set("vector3")
        ao_mutiply.setInput(ao_mutiply.inputIndex("in1"), ao_correct)
        #
        ao_mutiply_color = material_subnet.createNode("mtlxmultiply", "AO_mutiply_color")
        ao_mutiply_color.parm("signature").set("color")
        ao_mutiply_color.setInput(ao_mutiply_color.inputIndex("in1"), color_out)
        ao_mutiply_color.setInput(ao_mutiply_color.inputIndex("in2"), ao_mutiply)
        color_out = ao_mutiply_color
    #
    mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("base_color"), color_out)

    # ----- Metalness -----
    if metalness:
        metalness_map: hou.VopNode = material_subnet.createNode("mtlximage", "Metalness_map") 
        metalness_map.parm("file").set(metalness)
        metalness_map.parm("signature").set("float")
        material_subnet.setInput(material_subnet.inputIndex("metalness"), metalness_map)

    # ----- Roughness -----
    if roughness:
        #
        roughness_map: hou.VopNode = material_subnet.createNode("mtlximage", "Roughness_map")
        roughness_map.parm("file").set(roughness)
        roughness_map.parm("signature").set("float")
        #
        roughness_remap: hou.VopNode = material_subnet.createNode("mtlxremap", "Roughness_remap")
        roughness_remap.setInput(roughness_remap.inputIndex("in"), roughness_map)
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("specular_roughness"), roughness_remap)

    # ----- Normal ----
    #
    if normal:
        normal_map: hou.VopNode = material_subnet.createNode("mtlximage", "Normal_map")
        normal_map.parm("file").set(normal)
        normal_map.parm("signature").set("vector3")
        #
        normal_intensity = create_vop_parameter(material_subnet, "Normal_Intensity", "float", "normal_intensity", "Normal Intensity")
        normal_intensity.parm("floatdef").set(1)
        #
        mtlxnormalmap: hou.VopNode = material_subnet.createNode("mtlxnormalmap", "mtlxnormalmap")
        mtlxnormalmap.setInput(mtlxnormalmap.inputIndex("in"), normal_map)
        mtlxnormalmap.setInput(mtlxnormalmap.inputIndex("scale"), normal_intensity)
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("normal"), mtlxnormalmap)

    # ---- Translucency -----
    if translucent:
        #
        base_translucency_out = None
        if translucency:
            translucency_map: hou.VopNode = material_subnet.createNode("mtlximage", "Translucency_map")
            translucency_map.parm("file").set(translucency)
            translucency_map.parm("signature").set("float")
            base_translucency_out = translucency_map
        else:
            translucency_def = create_vop_parameter(material_subnet, "Translucency_def", "float", "translucency", "Translucency")
            translucency_def.parm("floatdef").set(1)
            base_translucency_out = translucency_def
        #
        translucency_remap: hou.VopNode = material_subnet.createNode("mtlxremap", "Translucency_remap")
        translucency_remap.parm("outhigh").set(.1)
        translucency_remap.setInput(translucency_remap.inputIndex("in"), base_translucency_out)
        #
        thin_walled = create_vop_parameter(material_subnet, "thin_walled", "int", "thin_walled", "Thin Walled")
        thin_walled.parm("intdef").set(1)
        #
        translucency_color = create_vop_parameter(material_subnet, "translucency_color", "color", "translucency_color", "Translucency Color")
        translucency_color.parm("colordefr").set(0.62)
        translucency_color.parm("colordefg").set(1)
        translucency_color.parm("colordefb").set(0)

        #
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("subsurface"), translucency_remap)
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("subsurface_color"), translucency_color)
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("thin_walled"), thin_walled)

    # --- Opacity ----
    if opacity:
        opacity_map: hou.VopNode = material_subnet.createNode("mtlximage", "Opacity_map")
        opacity_map.parm("file").set(opacity)
        opacity_map.parm("signature").set("flaot")
        mtlxstandard_surface.setInput(mtlxstandard_surface.inputIndex("opacity"), opacity_map)

    #
    surface_output: hou.VopNode = material_subnet.createNode("subnetconnector", "surface_output")
    surface_output.parm("connectorkind").set("output")
    surface_output.parm("parmname").set("surface")
    surface_output.parm("parmlabel").set("Surface")
    surface_output.parm("parmtype").set("surface")
    surface_output.setInput(surface_output.inputIndex("suboutput"), mtlxstandard_surface)

    # ----- Displacement ----
    if displacement:
        #
        displacement_map: hou.VopNode = material_subnet.createNode("mtlximage", "Displacement")
        displacement_map.parm("file").set(displacement)
        displacement_map.parm("signature").set("float")
        #
        remap_displacement: hou.VopNode = material_subnet.createNode("mtlxremap", "Displacement")
        remap_displacement.parm("outlow").set(-.5)
        remap_displacement.parm("outhigh").set(.5)
        remap_displacement.setInput(remap_displacement.inputIndex("in"), displacement_map)
        #
        displacement_scale = create_vop_parameter(material_subnet, "Displacement_Scale", "float", "scale", "Scale")
        displacement_scale.parm("floatdef").set(0.015)
        displacement_scale.parm("rangeflt2").set(10)
        #
        mtlx_displacement: hou.VopNode = material_subnet.createNode("mtlxdisplacement", "mtlxdisplacement")
        mtlx_displacement.setInput(mtlx_displacement.inputIndex("displacement"), remap_displacement)
        mtlx_displacement.setInput(mtlx_displacement.inputIndex("scale"), displacement_scale)
        #
        displacement_output: hou.VopNode = material_subnet.createNode("subnetconnector", "displacement_output")
        displacement_output.parm("connectorkind").set("output")
        displacement_output.parm("parmname").set("displacement")
        displacement_output.parm("parmlabel").set("Displacement")
        displacement_output.parm("parmtype").set("displacement")
        displacement_output.setInput(displacement_output.inputIndex("suboutput"), mtlx_displacement)

def list_files_with_extensions(directory, extensions=default_texture_file_extensions):
    """
    List all files in a given directory whit the desired extensions
    """
    patterns = [os.path.join(directory, f'*.{ext}') for ext in extensions]
    return [file for pattern in patterns for file in glob.glob(pattern)]

def create_vop_parameter(context, name, type, parmname, parmlabel=None, export=0) -> hou.VopNode:
    vop_parameter: hou.VopNode =  context.createNode("parameter", name)
    vop_parameter.parm("parmtype").set(type)
    vop_parameter.parm("parmname").set(parmname)
    if parmlabel: vop_parameter.parm("parmlabel").set(parmlabel)
    vop_parameter.parm("exportparm").set(export)
    return vop_parameter

def filter_maps(texture_files_list, map_dictionary, map_name):
    
    filtered_maps_list = list(filter(lambda x: x is not None, [f if sub in f.lower() else None for f in texture_files_list for sub in map_dictionary]))

    selected_map = None

    if filtered_maps_list:
        if len(filtered_maps_list) > 1:
            res = hou.ui.selectFromList(
                filtered_maps_list, default_choices=[0],
                exclusive=True, title=f'Select one of the maps for the {map_name}', 
                column_header=f'{map_name} maps', width=900)
            selected_map = filtered_maps_list[res[0]]
        else:
            selected_map = filtered_maps_list[0]

    return selected_map

def get_materialx_import_library(context):
    
    material_import_library = hou.node('/mat')

    if context == 'obj':
        obj: hou.Node = hou.node('/obj')
        material_import_library: hou.ShopNode = obj.node(materialx_import_library_name)
        if material_import_library is None:
            material_import_library = obj.createNode('matnet', materialx_import_library_name)
    elif context == 'stage':
        stage: hou.Node = hou.node('/stage')
        material_import_library: hou.ShopNode = stage.node(materialx_import_library_name)
        if material_import_library is None:
            material_import_library = stage.createNode('materiallibrary', materialx_import_library_name)
            material_import_library.parm('matpathprefix').set('/materialx_import_library_name/')
            material_import_library.parm('genpreviewshaders').set(0)

    return material_import_library

def get_material_full_name(material_name):
    return '_'.join([material_name, materialx_suffix])