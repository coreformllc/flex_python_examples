#!python3

import os
import argparse
import numpy
import scipy
from scipy import optimize
import json
import run_coreform_cubit
import run_coreform_flex
from coreform_utils import mk_script_relative

parser = argparse.ArgumentParser( prog='PlateWithHoleOptimization' )

def cli_arguments( parser ):
    parser.add_argument( "-nt", dest="nt", type=int, default=16 )
    parser.add_argument( "-ni", dest="ni", type=int, default=16 )
    parser.add_argument( "--strategy", dest="strategy", type=str, choices=["bodyfit", "immersed"], default="immersed" )
    parser.add_argument( "--mesh-size", dest="mesh_size", type=float, default=4 )
    parser.add_argument( "--degree", dest="degree", type=int, default=4 )
    return parser.parse_args()

script_relative = mk_script_relative( __file__ )
top_wd = os.getcwd()
log_file = "optimization_monitor.log"
yield_stress = 36260 # PSI

def main( args ):
    iga_args = { 'top_wd': top_wd, 'strategy': args.strategy, 'degree': int( args.degree ), 'mesh_size': float( args.mesh_size ), 'nt': args.nt, 'ni': args.ni }
    obj_fun = lambda radius: evaluate_objective( radius, iga_args )
    con_fun = lambda radius: evaluate_constraint( radius, iga_args )
    constraint = ( {'type': 'ineq', 'fun': con_fun}, )
    bounds = ( (0.5, 24.5), )
    local_opt_options = { "method": "trust-constr", "gtol":1e-1, "xtol":1e-1 }
    global_opt_options = { "disp":True, "f_tol": 1e-3, "minimizer_kwargs":local_opt_options }
    results = scipy.optimize.shgo( func=obj_fun, bounds=bounds, constraints=constraint, iters=2, options=global_opt_options )
    print( results )
    run_coreform_flex.ctx.exit_flex()

def evaluate_objective( radius, args ):
    args["radius"] = radius[0]
    run_coreform_cubit.main( args )
    run_coreform_flex.flex_commands( args )
    max_displacement = get_max_displacement()
    obj_value = 1.0 / max_displacement
    fLog = open( log_file, "a+" )
    fLog.write( f"Radius: {args['radius']}\n" )
    fLog.write( f"Max Displacement: {max_displacement}\n" )
    fLog.write( f"Objective Value: {obj_value}\n" )
    fLog.close()
    return obj_value

def evaluate_constraint( radius, args ):
    args["radius"] = radius[0]
    run_coreform_cubit.main( args )
    run_coreform_flex.flex_commands( args )
    max_stress = get_max_stress()
    con_value = -1.0 * ( max_stress - yield_stress )
    fLog = open( log_file, "a+" )
    fLog.write( f"Max Stress: {max_stress}\n" )
    fLog.write( f"Constraint Value: {con_value}\n" )
    fLog.close()
    return con_value

def get_max_displacement():
    probe_filename = os.path.join( top_wd, "cf_iga_data_output.json" )
    with open( probe_filename ) as probe_file:
        probe_data = json.load( probe_file )['pull']['history']
        max_displacement = probe_data['disp_probe']['displacement']['x'][-1][-1]
    return max_displacement

def get_max_stress():
    probe_filename = os.path.join( top_wd, "cf_iga_data_output.json" )
    with open( probe_filename ) as probe_file:
        probe_data = json.load( probe_file )['pull']['history']
        max_stress = probe_data['stress_probe']['stress']['max_principal'][-1][-1]
    return max_stress

if __name__ == '__main__':
    main( cli_arguments( parser ) )
