import numpy
import coreform_utils

platen_thickness = 0.1

def cubit_commands( options ):
    cubit = coreform_utils.import_cubit()
    cubit.cmd( "reset" )
    test_name = options['test_name']
    cad_file = options['cad_file']
    params = options['params']
    pad_vol_id = make_pad( cubit, params )
    bot_vol_id, top_vol_id = make_platens( cubit, pad_vol_id )
    cubit.cmd( f"block 1 volume {pad_vol_id}" )
    cubit.cmd( f"block 2 volume {bot_vol_id}" )
    cubit.cmd( f"block 3 volume {top_vol_id}" )
    cubit.cmd( "block 1 name 'pad'" )
    cubit.cmd( "block 2 name 'bot_platen'" )
    cubit.cmd( "block 3 name 'top_platen'" )
    if params[ "num_threads" ] == 0:
      # Special case for single-cell stack
      cubit.cmd( "webcut volume all with xplane" )
      cubit.cmd( "webcut volume all with zplane" )
      cubit.cmd( "delete volume all with x_coord<0" )
      cubit.cmd( "delete volume all with z_coord<0" )
    V = cubit.get_entities( "volume" )
    bbox = cubit.get_total_bounding_box( "volume", V )
    cubit.cmd( f"sideset 1 surface in vol in block 1 with x_coord >= {bbox[1]-1e-3} or with x_coord <= {bbox[0]+1e-3}" )
    cubit.cmd( f"sideset 2 surface in vol in block 1 with z_coord >= {bbox[7]-1e-3} or with z_coord <= {bbox[6]+1e-3}" )
    cubit.cmd( f"sideset 3 surface in vol in block 2 3 with x_coord >= {bbox[1]-1e-3} or with x_coord <= {bbox[0]+1e-3}" )
    cubit.cmd( f"sideset 4 surface in vol in block 2 3 with z_coord >= {bbox[7]-1e-3} or with z_coord <= {bbox[6]+1e-3}" )
    cubit.cmd( f"sideset 5 surface in vol in block 2 with y_coord <= {bbox[3]+1e-3}" )
    cubit.cmd( f"sideset 6 surface in vol in block 3 with y_coord >= {bbox[4]-1e-3}" )
    cubit.cmd( "sideset 1 name 'xfaces_pad'" )
    cubit.cmd( "sideset 2 name 'zfaces_pad'" )
    cubit.cmd( "sideset 3 name 'xfaces_platen'" )
    cubit.cmd( "sideset 4 name 'zfaces_platen'" )
    cubit.cmd( "sideset 5 name 'bot_platen_ymin'" )
    cubit.cmd( "sideset 6 name 'top_platen_ymax'" )
    cubit.cmd( "save cub5 'diw_pad.cub5' overwrite" )
    if params["platen_mesh_bodyfit"] == True:
        mesh_platens( cubit, top_vol_id, bot_vol_id )
    cubit.cmd( f"export acis '{test_name}.sat' overwrite" )
    cubit.cmd( f"export step '{test_name}.stp' overwrite" )
    cubit.cmd( f"save cub5 '{test_name}.cub5' overwrite" )
    cubit.cmd( f"export coreform '{cad_file}' overwrite" )
    export_geometry_dimensions( cubit, pad_vol_id, top_vol_id, bot_vol_id )

def export_geometry_dimensions( cubit, pad_vol_id, top_vol_id, bot_vol_id ):
    pad_bbox = cubit.get_total_bounding_box( "volume", [ pad_vol_id, ] )
    top_bbox = cubit.get_total_bounding_box( "volume", [ top_vol_id, ] )
    bot_bbox = cubit.get_total_bounding_box( "volume", [ bot_vol_id, ] )
    pad_volume = cubit.volume( pad_vol_id ).volume()
    pad_volume_ratio = pad_volume / ( ( pad_bbox[1]-pad_bbox[0] ) * ( pad_bbox[4]-pad_bbox[3] ) * ( pad_bbox[7]-pad_bbox[6] ) )
    pad_height = pad_bbox[4] - pad_bbox[3]
    platen_width = top_bbox[1] - top_bbox[0]
    top_platen_y_probe = top_bbox[3]
    with open( "pad_dimensions.txt", "w+" ) as f:
        f.write( "pad_height,pad_volume_ratio,platen_width,top_platen_y_probe\n" )
        f.write( f"{pad_height},{pad_volume_ratio},{platen_width},{top_platen_y_probe}")

def create_layer_a( cubit, params ):
    thread_vol_ids = []
    radius = params['thread_radius']
    if params["num_threads"] == 0:
        # Special case for single-cell stack
        num_threads = 1
    else:
        num_threads = params["num_threads"]
    thread_spacing = params["thread_spacing"]
    thread_length = num_threads * thread_spacing
    x = numpy.linspace( -thread_length/2, thread_length/2, 2*num_threads + 1 )
    x = x[1::2]
    for i in range( 0, num_threads ):
        cubit.cmd( f"cylinder radius {radius} height {thread_length}" )
        thread_vol_ids.append( cubit.get_last_id( "volume" ) )
        cubit.cmd( f"move volume {thread_vol_ids[i]} x {x[i]}" )
    return thread_vol_ids

def create_layer_b( cubit, params ):
    thread_vol_ids = []
    radius = params['thread_radius']
    if params["num_threads"] == 0:
        # Special case for single-cell stack
        num_threads = 1
    else:
        num_threads = params["num_threads"]
    thread_spacing = params["thread_spacing"]
    thread_length = num_threads * thread_spacing
    x = numpy.linspace( -thread_length/2, thread_length/2, 2*num_threads + 1 )
    x = x[0::2]
    for i in range( 0, num_threads + 1 ):
        cubit.cmd( f"cylinder radius {radius} height {thread_length}" )
        thread_vol_ids.append( cubit.get_last_id( "volume" ) )
        cubit.cmd( f"move volume {thread_vol_ids[i]} x {x[i]}" )
    return thread_vol_ids

def make_pad( cubit, params ):
    y_offset = 0.0
    if params["num_threads"] == 0:
        # Special case for single-cell stack
        num_threads = 1
    else:
        num_threads = params["num_threads"]
    thread_spacing = params["thread_spacing"]
    thread_length = num_threads * thread_spacing
    first_vol_id = cubit.get_last_id( "volume" ) + 1
    for i in range( 0, params["num_layers"] ):
        if numpy.mod( i + 1, 2 ) == 1:
          vid_1 = create_layer_b( cubit, params )
          cubit.cmd( f"move volume {list_to_str( vid_1 )} y {y_offset}" )
          y_offset += ( 2 * params['thread_radius'] ) - ( params['layer_overlap_ratio'] * 2 * params['thread_radius'] )
          vid_2 = create_layer_a( cubit, params )
          cubit.cmd( f"move volume {list_to_str( vid_2 )} y {y_offset}" )
          cubit.cmd( f"rotate Volume {list_to_str( vid_2 )} angle 90  about Y include_merged" )
          y_offset += ( 2 * params['thread_radius'] ) - ( params['layer_overlap_ratio'] * 2 * params['thread_radius'] )
        else:
          vid_1 = create_layer_a( cubit, params )
          cubit.cmd( f"move volume {list_to_str( vid_1 )} y {y_offset}" )
          y_offset += ( 2 * params['thread_radius'] ) - ( params['layer_overlap_ratio'] * 2 * params['thread_radius'] )
          vid_2 = create_layer_b( cubit, params )
          cubit.cmd( f"move volume {list_to_str( vid_2 )} y {y_offset}" )
          cubit.cmd( f"rotate Volume {list_to_str( vid_2 )} angle 90  about Y include_merged" )
          y_offset += ( 2 * params['thread_radius'] ) - ( params['layer_overlap_ratio'] * 2 * params['thread_radius'] )
    last_vol_id = cubit.get_last_id( "volume" )
    cubit.cmd( f"section volume {first_vol_id} to {last_vol_id} with xplane offset {thread_length/2.0} reverse" )
    cubit.cmd( f"section volume {first_vol_id} to {last_vol_id} with xplane offset -{thread_length/2.0}" )
    cubit.cmd( f"section volume {first_vol_id} to {last_vol_id} with zplane offset {thread_length/2.0} reverse" )
    cubit.cmd( f"section volume {first_vol_id} to {last_vol_id} with zplane offset -{thread_length/2.0}" )
    cubit.cmd( f"unite volume {first_vol_id} to {last_vol_id}" )
    cubit.cmd( "compress" )
    pad_vol_id = cubit.get_last_id( "volume" )
    return pad_vol_id

def make_platens( cubit, pad_vol_id ):
    bbox = cubit.volume( pad_vol_id ).bounding_box()
    platen_x = bbox[3] - bbox[0]
    platen_y = platen_thickness
    platen_z = bbox[5] - bbox[2]
    cubit.cmd( f"brick x {platen_x} y {platen_y} z {platen_z}" )
    top_vol_id = cubit.get_last_id( "volume" )
    cubit.cmd( f"brick x {platen_x} y {platen_y} z {platen_z}" )
    bot_vol_id = cubit.get_last_id( "volume" )
    cubit.cmd( f"move volume {top_vol_id} y {platen_y/2 + bbox[4]}" )
    cubit.cmd( f"move volume {bot_vol_id} y {-platen_y/2 + bbox[1]}" )
    return bot_vol_id, top_vol_id

def mesh_platens( cubit, top_platen_vol_id, bot_platen_vol_id ):
    cubit.cmd( f"volume {top_platen_vol_id} size {platen_thickness}" )
    cubit.cmd( f"volume {bot_platen_vol_id} size {platen_thickness}" )
    cubit.cmd( f"volume {top_platen_vol_id} {bot_platen_vol_id} scheme map" )
    cubit.cmd( f"mesh volume {top_platen_vol_id} {bot_platen_vol_id}" )

def list_to_str( input_list ):
    return " ".join( [ str( val ) for val in input_list] )

