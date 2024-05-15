import os
import sys
import pathlib
import coreform_utils
cubit = coreform_utils.import_cubit()

def main( args ):
    cubit.cmd( "reset" )
    coupon_vol_id = make_coupon_geometry( args["radius"] )
    assign_sets( coupon_vol_id )
    if args["strategy"] == "bodyfit":
        generate_bodyfit_mesh( args )
    export_model( args )

def make_coupon_geometry( radius ):
    cubit.cmd( "bri x 100 y 50 z 1" )
    bri_vol_id = cubit.get_last_id( "volume" )
    cubit.cmd( f"create Cylinder height 1 radius {radius}" )
    cyl_vol_id = cubit.get_last_id( "volume" )
    cubit.cmd( f"subtract vol {cyl_vol_id} from vol {bri_vol_id}" )
    cubit.cmd( f"section volume {bri_vol_id} with xplane offset 0 normal" )
    cubit.cmd( f"section volume {bri_vol_id} with yplane offset 0 normal" )
    cubit.cmd( f"section volume {bri_vol_id} with zplane offset 0 normal" )
    return bri_vol_id

def assign_sets( coupon_vol_id ):
    cubit.cmd( f"block 1 volume {coupon_vol_id}" )
    cubit.cmd( f"sideset 1 surface in volume {coupon_vol_id} with x_coord<0.01" )
    cubit.cmd( f"sideset 2 surface in volume {coupon_vol_id} with x_coord>49.9" )
    cubit.cmd( f"sideset 3 surface in volume {coupon_vol_id} with y_coord<0.01" )
    cubit.cmd( f"sideset 4 surface in volume {coupon_vol_id} with y_coord>24.9" )
    cubit.cmd( f"sideset 5 surface in volume {coupon_vol_id} with z_coord<0.01" )
    cubit.cmd( f"sideset 6 surface in volume {coupon_vol_id} with z_coord>0.49" )
    cubit.cmd( "block 1 name 'coupon'" )
    cubit.cmd( "sideset 1 name 'xmin'" )
    cubit.cmd( "sideset 2 name 'xmax'" )
    cubit.cmd( "sideset 3 name 'ymin'" )
    cubit.cmd( "sideset 4 name 'ymax'" )
    cubit.cmd( "sideset 5 name 'zmin'" )
    cubit.cmd( "sideset 6 name 'zmax'" )

def generate_bodyfit_mesh( args ):
    cubit.cmd( "surface in sideset 5 6 scheme polyhedron" )
    cubit.cmd( "surface in sideset 1 2 3 4 interval 1" )
    cubit.cmd( f"surface in sideset 5 6 size {args['mesh_size']}" )
    cubit.cmd( "volume in block 1 redistribute nodes off" )
    cubit.cmd( "volume in block 1 scheme Sweep  source surface in sideset 6 target surface in sideset 5 sweep transform translate propagate bias" )
    cubit.cmd( "volume in block 1 autosmooth target off" )
    cubit.cmd( "mesh volume in block 1" )

def export_model( args ):
    filename = os.path.join( args["top_wd"], "plate_with_hole_geom.cf" )
    cubit.cmd(f'export coreform "{filename}" overwrite')