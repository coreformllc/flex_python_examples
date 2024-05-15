#!python
import math
import coreform_utils

cubit = coreform_utils.import_cubit()

initial_params = {
                    "pipe_inner_radius": 60.0,
                    "pipe_thickness": 5.0,
                    "pipe_length": 500.0,
                    "trunnion_inner_radius": 35.0,
                    "trunnion_thickness": 15.0,
                    "trunnion_length": 300,
                    "outer_fillet_radius": 30.0,
                    "inner_fillet_radius": 10.0
                  }

lower_params = {
                    "pipe_inner_radius": 60.0,
                    "pipe_thickness": 0.5,
                    "pipe_length": 250.0,
                    "trunnion_inner_radius": 10.0,
                    "trunnion_thickness": 1.0,
                    "trunnion_length": 300.0,
                    "outer_fillet_radius": 1.0,
                    "inner_fillet_radius": 1.0
                  }

upper_params = {
                    "pipe_inner_radius": 60.0,
                    "pipe_thickness": 50.0,
                    "pipe_length": 500.0,
                    "trunnion_inner_radius": 50.0,
                    "trunnion_thickness": 5.0,
                    "trunnion_length": 300.0,
                    "outer_fillet_radius": 30.0,
                    "inner_fillet_radius": 7.5
                  }

cub_file = "pipe.cub5"
cf_file = "pipe.cf"

def create_geom( params ):
  cubit.cmd( "reset" )
  initial_error = cubit.get_error_count()
  create_main_pipe( params["pipe_inner_radius"], params["pipe_thickness"], params["pipe_length"] )
  create_support_trunnion( params["trunnion_inner_radius"], params["pipe_inner_radius"] + params["pipe_thickness"], params["trunnion_thickness"], params["trunnion_length"] )
  cubit.cmd( "unite volume all" )
  cid1 = find_fillet_curve( params["pipe_inner_radius"] + params["pipe_thickness"], params["trunnion_inner_radius"] + params["trunnion_thickness"] )
  cid2 = find_fillet_curve( params["pipe_inner_radius"] + params["pipe_thickness"], params["trunnion_inner_radius"] )
  cubit.cmd( f"modify curve {cid1} blend radius {params['outer_fillet_radius']}" )
  cubit.cmd( f"modify curve {cid2} blend radius {params['inner_fillet_radius']}" )
  assign_sets( params )
  volume = compute_volume()
  cubit.cmd( f"save cub5 '{cub_file}' overwrite" )
  cubit.cmd( f"export coreform '{cf_file}' overwrite")
  final_error = cubit.get_error_count()
  if final_error == initial_error:
    geom_success = True
  else:
    geom_success = False
  return volume, geom_success

def create_main_pipe( inner_radius, thickness, length ):
  cubit.cmd( f"create Cylinder height {length} radius {inner_radius}" )
  vid_1 = cubit.get_last_id( "volume" )
  cubit.cmd( f"create Cylinder height {length} radius {inner_radius + thickness}" )
  vid_2 = cubit.get_last_id( "volume" )
  cubit.cmd( f"subtract vol {vid_1} from vol {vid_2}" )
  cubit.cmd( f"section volume {vid_2} with xplane offset 0 normal" )
  cubit.cmd( f"section volume {vid_2} with yplane offset 0 normal" )
  cubit.cmd( f"move volume {vid_2} z {length/2.0}" )

def create_support_trunnion( inner_radius, trim_radius, thickness, length ):
  cubit.cmd( f"create Cylinder height {length} radius {inner_radius}" )
  vid_1 = cubit.get_last_id( "volume" )
  cubit.cmd( f"create Cylinder height {length} radius {inner_radius + thickness}" )
  vid_2 = cubit.get_last_id( "volume" )
  cubit.cmd( f"subtract vol {vid_1} from vol {vid_2}" )
  cubit.cmd( f"section volume {vid_2} with xplane offset 0 normal" )
  cubit.cmd( f"section volume {vid_2} with yplane offset 0 normal" )
  cubit.cmd( f"move volume {vid_2} z {-1 * length/2.0}" )
  cubit.cmd( f"rotate Volume {vid_2} angle 90  about X" )
  cubit.cmd( f"create Cylinder height {length} radius {trim_radius}" )
  vid_3 = cubit.get_last_id( "volume" )
  cubit.cmd( f"subtract volume {vid_3} from volume {vid_2}" )

def assign_sets( params ):
  cubit.cmd( "block 1 volume all" )
  assign_inner_pressure_sideset( params["pipe_inner_radius"], params["pipe_length"] )
  cubit.cmd( f"sideset 2 surface with x_coord<0.001" )
  cubit.cmd( f"sideset 3 surface with y_coord<0.001" )
  cubit.cmd( f"sideset 4 surface with y_coord>{params['trunnion_length']-0.001}" )
  cubit.cmd( f"sideset 5 surface with z_coord<0.001" )
  cubit.cmd( f"sideset 6 surface with z_coord>{params['pipe_length']-0.001}" )
  cubit.cmd( "block 1 name 'pipe'" )
  cubit.cmd( "sideset 1 name 'pressure_surface'" )
  cubit.cmd( "sideset 2 name 'xmin'" )
  cubit.cmd( "sideset 3 name 'ymin'" )
  cubit.cmd( "sideset 4 name 'ymax'" )
  cubit.cmd( "sideset 5 name 'zmin'" )
  cubit.cmd( "sideset 6 name 'zmax'" )

def assign_inner_pressure_sideset( inner_radius, length ):
  cx = math.sqrt( ( inner_radius**2.0 ) / 2.0 )
  cy = math.sqrt( ( inner_radius**2.0 ) / 2.0 )
  cz = length / 2.0
  S = cubit.get_entities( "surface" )
  min_dist = float( "inf" )
  for sid in S:
    surf_type = cubit.get_surface_type( sid )
    if surf_type == "cone surface":
      surf_radius = get_cone_surface_radius( sid )
      if abs( surf_radius - inner_radius ) / inner_radius < 1e-3:
        x,y,z = cubit.surface( sid ).center_point()
        dist = math.sqrt( (cx - x)**2 + (cy - y)**2 + (cz - z)**2 )
        if dist < min_dist:
          min_dist = dist
          inner_surface_id = sid
  cubit.cmd( f"sideset 1 surface {inner_surface_id}" )

def find_fillet_curve( major_radius, minor_radius ):
  cx = math.sqrt( ( minor_radius**2.0 ) / 2.0 )
  cy = math.sqrt( major_radius**2.0 - cx**2.0 )
  cz = math.sqrt( ( minor_radius**2.0 ) / 2.0 )
  C = cubit.get_entities( "curve" )
  min_dist = float( "inf" )
  for cid in C:
    curve = cubit.curve( cid )
    x, y, z = curve.closest_point_trimmed( ( cx, cy, cz ) )
    dist = math.sqrt( ( cx - x )**2 + ( cy - y )**2 + ( cz - z )**2 )
    if dist < min_dist:
      min_dist = dist
      fillet_curve = cid
  return fillet_curve

def get_cone_surface_radius( sid ):
  surface = cubit.surface( sid )
  cXYZ = surface.position_from_u_v( 0.5, 0.5 )
  radius = 1 / max( surface.principal_curvatures( cXYZ) )
  return radius

def compute_volume():
  V = cubit.get_entities( "volume" )
  volume = 0.0
  for vid in V:
      volume += cubit.volume( vid ).volume()
  return volume

if __name__ == "__coreformcubit__":
  create_geom( initial_params )
