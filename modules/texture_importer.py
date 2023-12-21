import hou
import os, glob

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

def create_materialx_network(context, base_color, roughness, normal, ao=None, displacement=None, metalness=None, translucency_texture=None, translucency=None, opacity_texture=None, opacity=False, color_variation=False):
    
    houdini_version = hou.applicationVersion()

    standard: hou.VopNode = context.createNode("mtlxstandard_surface", "mtlxstandard_surface")

    # ----- Base Color -----
    #
    base_color_map: hou.VopNode = context.createNode("mtlximage", "Base_Color")
    if base_color: base_color_map.parm("file").set(base_color)
    #
    if houdini_version < (20, 0, 0):
        base_color_correction: hou.VopNode = context.createNode("hmtlxcolorcorrect", "Base_Color_Correction")
    else:
        base_color_correction: hou.VopNode = context.createNode("mtlxcolorcorrect", "Base_Color_Correction")
    base_color_correction.setInput(0, base_color_map, 0)
    color_out = base_color_correction
    # ----- Color Variation -----
    if color_variation:
        #
        if houdini_version < (20, 0, 0):
            variation_color_correct: hou.VopNode = context.createNode("hmtlxcolorcorrect", "Cariation_Color_Correct")
        else:
            variation_color_correct: hou.VopNode = context.createNode("mtlxcolorcorrect", "Cariation_Color_Correct")
        variation_color_correct.setInput(0, base_color_correction, 0)
        #
        color_variation_attribute:hou.VopNode = context.createNode("mtlxgeompropvalue", "ColorVariationAttribute")
        color_variation_attribute.parm("geomprop").set("ColorVariation")
        color_variation_attribute.parm("default").set(1)
        #
        color_mix: hou.VopNode = context.createNode("mtlxmix", "VariationMix")
        color_mix.setInput(0, variation_color_correct, 0)
        color_mix.setInput(1, base_color_correction, 0)
        color_mix.setInput(2, color_variation_attribute, 0)
        color_out = color_mix
    # ----- AO -----
    if ao:
        #
        ao_correct: hou.VopNode = context.createNode("mtlximage", "AO")
        ao_correct.parm("file").set(ao)
        ao_correct.parm("signature").set("color")
        #
        ao_mutiply: hou.VopNode = context.createNode("mtlxmultiply", "AO_mutiply")
        ao_mutiply.parm("signature").set("vector3")
        ao_mutiply.setInput(0, ao_correct, 0)
        #
        ao_mutiply_color = context.createNode("mtlxmultiply", "AO_mutiply_color")
        ao_mutiply_color.parm("signature").set("color")
        ao_mutiply_color.setInput(0, color_out, 0)
        ao_mutiply_color.setInput(1, ao_mutiply, 0)
        color_out = ao_mutiply_color
    #
    standard.setInput(1, color_out, 0)

    # ----- Metalness -----
    if metalness:
        metalness_map: hou.VopNode = context.createNode("mtlximage", "Metalness_map") 
        metalness_map.parm("file").set(metalness)
        metalness_map.parm("signature").set("float")
        standard.setInput(3, metalness_map, 0)

    # ----- Roughness -----
    #
    roughness_map: hou.VopNode = context.createNode("mtlximage", "Roughness_map")
    if roughness: roughness_map.parm("file").set(roughness)
    roughness_map.parm("signature").set("float")
    #
    roughness_remap: hou.VopNode = context.createNode("mtlxremap", "Roughness_remap")
    roughness_remap.setInput(0, roughness_map, 0)
    standard.setInput(6, roughness_remap, 0)

    # ----- Normal ----
    #
    normal_map: hou.VopNode = context.createNode("mtlximage", "Normal_map")
    if normal: normal_map.parm("file").set(normal)
    normal_map.parm("signature").set("vector3")
    #
    normal_intensity = create_vop_parameter(context, "Normal_Intensity", "float", "normal_intensity", "Normal Intensity")
    normal_intensity.parm("floatdef").set(1)
    #
    mtlxnormalmap: hou.VopNode = context.createNode("mtlxnormalmap", "mtlxnormalmap")
    mtlxnormalmap.setInput(0, normal_map, 0)
    mtlxnormalmap.setInput(1, normal_intensity, 0)
    standard.setInput(40, mtlxnormalmap, 0)

    #
    surface_output: hou.VopNode = context.createNode("subnetconnector", "surface_output")
    surface_output.parm("connectorkind").set("output")
    surface_output.parm("parmname").set("surface")
    surface_output.parm("parmlabel").set("Surface")
    surface_output.parm("parmtype").set("surface")
    surface_output.setInput(0, standard, 0)

    # ---- Translucency -----
    if translucency:
        #
        base_translucency_out = None
        if translucency_texture:
            translucency_map: hou.VopNode = context.createNode("mtlximage", "Translucency_map")
            translucency_map.parm("file").set(translucency_texture)
            translucency_map.parm("signature").set("float")
            base_translucency_out = translucency_map
        else:
            translucency_def = create_vop_parameter(context, "Translucency_def", "float", "translucency", "Translucency")
            translucency_def.parm("floatdef").set(1)
            base_translucency_out = translucency_def
        #
        translucency_remap: hou.VopNode = context.createNode("mtlxremap", "Translucency_remap")
        translucency_remap.parm("outhigh").set(.1)
        translucency_remap.setInput(0, base_translucency_out, 0)
        #
        thin_walled = create_vop_parameter(context, "thin_walled", "int", "thin_walled", "Thin Walled")
        thin_walled.parm("intdef").set(1)
        #
        translucency_color = create_vop_parameter(context, "translucency_color", "color", "translucency_color", "Translucency Color")
        translucency_color.parm("colordefr").set(0.62)
        translucency_color.parm("colordefg").set(1)
        translucency_color.parm("colordefb").set(0)

        #
        standard.setInput(17, translucency_remap, 0)
        standard.setInput(18, translucency_color, 0)
        standard.setInput(39, thin_walled, 0)

    # --- Opacity ----
    if opacity and opacity_texture:
        opacity_map: hou.VopNode = context.createNode("mtlximage", "Opacity_map")
        opacity_map.parm("file").set(opacity_texture)
        opacity_map.parm("signature").set("flaot")
        standard.setInput(38, opacity_map, 0)

    # ----- Displacement ----
    if displacement:
        #
        displacement_map: hou.VopNode = context.createNode("mtlximage", "Displacement")
        displacement_map.parm("file").set(displacement)
        displacement_map.parm("signature").set("float")
        #
        remap_displacement: hou.VopNode = context.createNode("mtlxremap", "Displacement")
        remap_displacement.parm("outlow").set(-.5)
        remap_displacement.parm("outhigh").set(.5)
        remap_displacement.setInput(0, displacement_map, 0)
        #
        displacement_scale = create_vop_parameter(context, "Displacement_Scale", "float", "scale", "Scale")
        displacement_scale.parm("floatdef").set(0.015)
        displacement_scale.parm("rangeflt2").set(10)
        #
        mtlx_displacement: hou.VopNode = context.createNode("mtlxdisplacement", "mtlxdisplacement")
        mtlx_displacement.setInput(0, remap_displacement, 0)
        mtlx_displacement.setInput(1, displacement_scale, 0)
        #
        displacement_output: hou.VopNode = context.createNode("subnetconnector", "displacement_output")
        displacement_output.parm("connectorkind").set("output")
        displacement_output.parm("parmname").set("displacement")
        displacement_output.parm("parmlabel").set("Displacement")
        displacement_output.parm("parmtype").set("displacement")
        displacement_output.setInput(0, mtlx_displacement, 0)

def create_vop_parameter(context, name, type, parmname, parmlabel=None, export=0) -> hou.VopNode:
    vop_parameter: hou.VopNode =  context.createNode("parameter", name)
    vop_parameter.parm("parmtype").set(type)
    vop_parameter.parm("parmname").set(parmname)
    if parmlabel: vop_parameter.parm("parmlabel").set(parmlabel)
    vop_parameter.parm("exportparm").set(export)
    return vop_parameter

def list_files_with_extensions(directory, extensions=["jpg", "exr", "png"]):
    """
    List all files in a given directory whit the desired extensions
    """
    patterns = [os.path.join(directory, f'*.{ext}') for ext in extensions]
    return [file for pattern in patterns for file in glob.glob(pattern)]

def filter_maps(textures, map_substrings, map_name):
    maps = list(filter(lambda x: x is not None, [f if sub in f.lower() else None for f in textures for sub in map_substrings]))

    selected_map = None
    if maps:
        if len(maps) > 1:
            res = hou.ui.selectFromList(maps, default_choices=[0], exclusive=True, title="Select one of the maps for the {}".format(map_name), column_header="Maps", width=900)
            selected_map = maps[res[0]]
        else:
            selected_map = maps[0]

    return selected_map
