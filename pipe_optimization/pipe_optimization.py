#!python3

import os
import argparse
import numpy
import pandas
pandas.set_option( 'display.max_columns', None )
pandas.set_option( 'display.max_rows', None )

import parmoo
import parmoo.optimizers
import parmoo.surrogates
import parmoo.searches
import parmoo.acquisitions

import coreform_utils
cubit = coreform_utils.import_cubit()

import make_cad
initial_params = make_cad.initial_params
lower_params = make_cad.lower_params
upper_params = make_cad.upper_params

import run_flex

import logging
logging.basicConfig(level=logging.INFO)

# Define Globals
sim_id = 0
obj_id = 0
sim_base_name = 'simulation'
yield_stress = 700e6
top_wd = os.getcwd()

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

# Fix the random seed for reproducibility
numpy.random.seed(0)

parser = argparse.ArgumentParser( prog='PipeOptimization' )

def cli_arguments( parser ):
    parser.add_argument( "--mesh-size", dest="mesh_size", type=float, default=10.0 )
    parser.add_argument( "--degree", dest="degree", type=int, default=int(3) )
    parser.add_argument( "-np", dest="np", type=int, default=int(1) )
    return parser.parse_args()

global options
options = cli_arguments( parser )

def main( options ):
    my_moop = parmoo.MOOP( parmoo.optimizers.GlobalGPS )
    my_moop.addDesign( { "name": "pipe_thickness",        "des_type": "continuous", "lb": lower_params["pipe_thickness"],        "ub": upper_params["pipe_thickness"],        "des_tol": 1e-6 } )
    my_moop.addDesign( { "name": "pipe_length",           "des_type": "continuous", "lb": lower_params["pipe_length"],           "ub": upper_params["pipe_length"],           "des_tol": 1e-6 } )
    my_moop.addDesign( { "name": "trunnion_inner_radius", "des_type": "continuous", "lb": lower_params["trunnion_inner_radius"], "ub": upper_params["trunnion_inner_radius"], "des_tol": 1e-6 } )
    my_moop.addDesign( { "name": "trunnion_thickness",    "des_type": "continuous", "lb": lower_params["trunnion_thickness"],    "ub": upper_params["trunnion_thickness"],    "des_tol": 1e-6 } )
    my_moop.addDesign( { "name": "outer_fillet_radius",   "des_type": "continuous", "lb": lower_params["outer_fillet_radius"],   "ub": upper_params["outer_fillet_radius"],   "des_tol": 1e-6 } )
    my_moop.addDesign( { "name": "inner_fillet_radius",   "des_type": "continuous", "lb": lower_params["inner_fillet_radius"],   "ub": upper_params["inner_fillet_radius"],   "des_tol": 1e-6 } )

    my_moop.addObjective( { "name": "volume_length_ratio", "obj_func": compute_volume_length_ratio } )
    my_moop.addConstraint( { "name": "factor_of_safety", "constraint": compute_factor_of_safety } )
    my_moop.addAcquisition( {'acquisition': parmoo.acquisitions.UniformWeights} )
    my_moop.addAcquisition( {'acquisition': parmoo.acquisitions.UniformWeights} )

    my_moop.addSimulation({ 'name': "PipeCoreformIGA",
                            'm': 3,
                            'sim_func': evaluate_iteration,
                            'search': parmoo.searches.LatinHypercube,
                            'surrogate': parmoo.surrogates.GaussRBF,
                            'hyperparams': {'search_budget': 40}})

    # Extract numpy dtypes for all of this MOOP's inputs/outputs
    des_dtype = my_moop.getDesignType()
    obj_dtype = my_moop.getObjectiveType()
    con_dytpe = my_moop.getConstraintType()
    sim_dtype = my_moop.getSimulationType()

    # Display the dtypes as strings
    print("Design variable type:   " + str(des_dtype))
    print("Simulation output type: " + str(sim_dtype))
    print("Objective type:         " + str(obj_dtype))
    print("Constraint type:        " + str(con_dytpe))

    # Solve the MOOP
    my_moop.solve( 20 )
    
    # Collect Results
    results = my_moop.getPF(format='pandas')
    sim_data = my_moop.getSimulationData(format='pandas')
    obj_data = my_moop.getObjectiveData(format='pandas')

    # Print Results
    print( results )
    print( sim_data )
    print( obj_data )

    # Perform verification simulation of computed optimal result
    os.chdir( top_wd )
    results = my_moop.getPF(format='ndarray')
    max_mises_stress, volume, feasible_geom = run_flex.main( top_wd, results[0], options )
    print( f"Optimal Max Mises Stress: {max_mises_stress}" ) 

def evaluate_iteration( x ):
    global sim_id
    sim_id += 1
    eval_dir = f'{sim_base_name}_{sim_id}'
    subdir = os.path.join(top_wd, eval_dir )
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    os.chdir(subdir)
    max_mises_stress, volume, feasible_geom = run_flex.main( subdir, x, options )
    return max_mises_stress, volume, feasible_geom

def compute_volume_length_ratio( x, sim ):
    global obj_id
    obj_id += 1
    params = x_to_params( x )
    if sim["PipeCoreformIGA"][-1] < 0.01:
        print( f"Evaluation: {obj_id} Failed!  Value: 1.0" )
        bbox_vol = ( initial_params["pipe_inner_radius"] + upper_params["pipe_thickness"] ) * upper_params["trunnion_length"]  * upper_params["pipe_length"]
        return 
    else:
        volume = sim["PipeCoreformIGA"][1]
        volume_length_ratio = volume / params["pipe_length"]
        print( f"Evaluation: {obj_id} Worked! Value: {volume_length_ratio}" )
    return volume_length_ratio

def compute_factor_of_safety( x, sim ):
    global yield_stress
    if sim["PipeCoreformIGA"][-1] < 0.1:
        return 2.0
    else:
        factor_of_safety = sim["PipeCoreformIGA"][0] /  yield_stress
        print( f"Factor of Safety: {factor_of_safety}" )
        return factor_of_safety - 1

def x_to_params( x ):
    params = {
                "pipe_inner_radius": initial_params["pipe_inner_radius"],
                "pipe_thickness": x[0],
                "pipe_length": x[1],
                "trunnion_inner_radius": x[2],
                "trunnion_thickness": x[3],
                "trunnion_length": initial_params["trunnion_length"],
                "outer_fillet_radius": x[4],
                "inner_fillet_radius": x[5]
                }
    return params

if __name__ == '__main__':
    main( options )
