#!python3

import os
import sys
import numpy as np
import json

from make_cad import cubit_commands
from build_flex import flex_commands
from coreform_utils import mk_script_relative
import sim_data_fitting
import read_geometry_dimensions

script_relative = mk_script_relative( __file__ )

test_cases = {
                "nt_0_nl_2_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 2 },
                "nt_1_nl_2_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 4 },
                "nt_2_nl_2_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_0_nl_4_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 4 },
                "nt_1_nl_4_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_2_nl_4_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_0_nl_6_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_1_nl_6_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_2_nl_6_stabilized":   { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": True,  "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_0_nl_2_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 2 },
                "nt_1_nl_2_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 4 },
                "nt_2_nl_2_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 2, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_0_nl_4_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 4 },
                "nt_1_nl_4_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_2_nl_4_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 4, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_0_nl_6_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 0, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_1_nl_6_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 1, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
                "nt_2_nl_6_unstabilized": { "thread_radius": 0.05, "thread_spacing": 0.4, "layer_overlap_ratio": 0.1, "num_threads": 2, "num_layers": 6, "poissons_ratio": 0.48, "degree": 2, "solver": "quasistatic", "stabilization": False, "platen_mesh_bodyfit": True, "num_proc": 8 },
             }

test_case_ids = list( test_cases.keys() )
for test_id in test_case_ids:
    degree = test_cases[test_id]["degree"]
    thread_radius = test_cases[test_id]["thread_radius"]
    mesh_size = min( [ 2 * thread_radius / ( degree + 1 ), thread_radius / (degree + 1) ] ) # there is a factor 1 / (degree+1) to avoid cross-talk across gaps
    test_cases[test_id]["mesh_size"] = mesh_size

def run( test_id ):
    cad_file = 'diw_cad.cf'
    cf_cad_file = 'geom.cf'
    top_wd = os.getcwd()

    test_name = f"diw_{test_id}"
    subdir = os.path.join( top_wd, test_name )
    if not os.path.exists( subdir ):
        os.makedirs( subdir )
    os.chdir( subdir )

    cad_cmds_args = { 'cad_file': cad_file,
                      'test_name': test_name,
                      'params': test_cases[test_id] }

    flex_cmds_args = {  'cad_file': cad_file,
                        'cf_cad_file': cf_cad_file,
                        'test_name': test_name,
                        'params': test_cases[test_id] }

    cubit_commands( cad_cmds_args )
    flex_commands( flex_cmds_args )
    os.chdir( top_wd )
    process_results( subdir, test_id )

def get_eng_stress_strain_data( subdir ):
    pad_height, pad_volume_ratio, platen_width, top_platen_y_probe = read_geometry_dimensions.main( subdir )
    probe_filename = os.path.join( subdir, "jobs", "cf_iga_data_output.json" )
    probe_file = open( probe_filename, "r" )
    output_data = json.load( probe_file )['compress_pad']
    probe_data = output_data['history']
    probe_file.close()

    reaction_force = np.array( probe_data['bot_reaction_probe']['reaction_force']['y'] )
    displacement = -1.0 *np.array( probe_data['top_platen_probe']['displacement']['y'] )[:,0]

    platen_width /= 1000
    eng_stress = ( reaction_force / ( platen_width**2.0 ) ) / 1000
    eng_strain = displacement / pad_height
    return eng_stress, eng_strain
    

def process_results( subdir, test_id ):
    pad_volume_ratio = read_geometry_dimensions.main( subdir )[1]
    eng_stress, eng_strain = get_eng_stress_strain_data( subdir )

    fit_results = sim_data_fitting.main( eng_strain, eng_stress, subdir )

    computed_compression_ratio = eng_strain[-1]
    computed_densification_strain = fit_results["compression_fit"]["domain"][1]
    compression_fit_func = fit_results["compression_fit"]["fit_func"]
    computed_densification_stress = compression_fit_func( computed_densification_strain )
    computed_compression_modulus = fit_results["compression_fit"]["coeffs"][0]

    # These values are a "snapshot in time" for the specific simulation parameters specified in this test
    # that reflects the simulation model shared with KCNSC for demonstration.
    # These values were achieved with the Default workflow with stabilization turned on.
    max_compression_ratio = ( 1 - pad_volume_ratio )
    use_stabilization = test_cases[test_id]["stabilization"]
    if use_stabilization:
        expected_compression_ratio = 0.85 * max_compression_ratio
        expected_densification_strain = 0.45985049481381585
        expected_densification_stress = 20.801111845968553
        expected_compression_modulus = 45.234510086567376
    else:
        # The asserts for the unstabilized version are from the stabilized counterpart with the same setup.
        expected_compression_ratio = 0.75 * max_compression_ratio
        expected_densification_strain = 0.4788731191220529
        expected_densification_stress = 20.01616790454375
        expected_compression_modulus = 41.79847877291714
    print( f"expected_compression_ratio: {expected_compression_ratio}" )
    print( f"computed_compression_ratio: {computed_compression_ratio}" )
    print( f"expected_densification_strain: {expected_densification_strain}" )
    print( f"computed_densification_strain: {computed_densification_strain}" )
    print( f"expected_densification_stress: {expected_densification_stress}" )
    print( f"computed_densification_stress: {computed_densification_stress}" )
    print( f"expected_compression_modulus: {expected_compression_modulus}" )
    print( f"computed_compression_modulus: {computed_compression_modulus}" )

if __name__ == "__main__":
    run( sys.argv[-1] )