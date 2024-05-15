import os
import math
import json
import coreform_utils
flex = coreform_utils.import_flex()

import make_cad
initial_params = make_cad.initial_params
lower_params = make_cad.lower_params
upper_params = make_cad.upper_params

def main( eval_dir, x, options ):
    cad_params = x_to_params( x )
    if is_cad_feasible( cad_params ):
        volume, geom_success = make_cad.create_geom( cad_params )
        flex_commands( eval_dir, cad_params, options )
        max_mises_stress = get_max_mises_stress( eval_dir )
        return max_mises_stress, volume, geom_success
    else:
        return 1000, 1.0, False

def flex_commands( eval_dir, params, options ):
    flex.cmd( 'reset' )

    cf_file = os.path.join( eval_dir, "pipe.cf" )
    flex.cmd(f'open "{cf_file}"' )

    degree = options.degree
    mesh_size = options.mesh_size

    flex.cmd(f'fill "fill_1" affine hatch_spacing [{mesh_size} {mesh_size} {mesh_size}] degree {degree} continuity {degree-1} padding [ {degree} {degree} {degree}]' )
    flex.cmd( 'part 1 fill 1' )
    flex.cmd( 'part 1 volume_box axis_aligned' )

    ### IGA PARAMS
    flex.cmd( 'coreform_iga_version 2024.5' )
    flex.cmd( 'label "internal_pressure"' )

    flex.cmd( 'materials steel new' )
    flex.cmd( 'materials steel mass_density 1' )
    flex.cmd( 'materials steel elastic youngs_modulus 200e9' )
    flex.cmd( 'materials steel elastic poissons_ratio 0.3' )
    flex.cmd( 'materials steel elastic large_deformations false' )

    flex.cmd( 'flex_models flex_immersed new' )
    flex.cmd( 'flex_models flex_immersed database_name "geom"' )
    flex.cmd( 'flex_models flex_immersed small_cell_volume_ratio 0.2' )

    flex.cmd( 'flex_models flex_immersed parts pipe part "pipe"' )
    flex.cmd( 'flex_models flex_immersed parts pipe material "steel"' )
    flex.cmd( 'flex_models flex_immersed parts pipe material_model elastic' )
    flex.cmd( 'flex_models flex_immersed parts pipe quadrature QP1' )

    flex.cmd( 'functions constant_1 new' )
    flex.cmd( 'functions constant_1 constant value 1.0' )

    flex.cmd( 'functions linear_ramp new' )
    flex.cmd( 'functions linear_ramp piecewise_linear abscissa [0 1]' )
    flex.cmd( 'functions linear_ramp piecewise_linear ordinate [0 1]' )

    flex.cmd( 'intervals push_interval new' )
    flex.cmd( 'intervals push_interval start_time 0' )
    flex.cmd( 'intervals push_interval stop_time 1' )

    flex.cmd( 'time_steppers linear_statics new' )
    flex.cmd( 'time_steppers linear_statics linear linear_equation_solver "direct_multifrontal"' )

    flex.cmd( 'linear_equation_solvers direct_multifrontal new' )
    flex.cmd( 'linear_equation_solvers direct_multifrontal direct lu' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry displacement components 0 x' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry set "xmin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry penalty 200e12' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry displacement components 0 y' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry set "ymin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symmetry penalty 200e12' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion displacement components 0 x' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion displacement components 1 y' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion displacement components 2 z' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion set "ymax"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_trunnion penalty 200e12' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry displacement components 0 z' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry set "zmin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry penalty 200e12' )

    flex.cmd( 'solid_mechanics_definitions load_conditions pressure_load new' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pressure_load surface_pressure scale_factor 100e6' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pressure_load surface_pressure function "linear_ramp"' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pressure_load set "pressure_surface"' )

    pull_load_area = ( ( math.pi * ( params["pipe_inner_radius"] + params["pipe_thickness"] )**2.0 ) - ( math.pi * params["pipe_inner_radius"]**2.0 ) ) / 4.0
    pull_load_uniform_pressure = -282e3 / pull_load_area
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_load new' )
    flex.cmd( f'solid_mechanics_definitions load_conditions pull_load surface_pressure scale_factor {pull_load_uniform_pressure}' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_load surface_pressure function "linear_ramp"' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_load set "zmax"' )

    flex.cmd( 'solid_mechanics_definitions outputs field_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field database_name "results"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field interval "push_interval"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field part "pipe"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 2 z' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables stress 0 all' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field element_variable_output_strategy interpolate' )

    flex.cmd( 'solid_mechanics_definitions outputs probe_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history interval "push_interval"' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 0 "max_mises"' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 1 "load_reaction_force"' )

    flex.cmd( 'solid_mechanics_definitions probes max_mises new' )
    flex.cmd( 'solid_mechanics_definitions probes max_mises field extremum set "pipe"' )
    flex.cmd( 'solid_mechanics_definitions probes max_mises field extremum maximum stress von_mises' )
    flex.cmd( 'solid_mechanics_definitions probes max_mises field location_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes max_mises field field_variable_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes max_mises field variables stress 0 von_mises' )

    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force new' )
    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force integrated_surface_quantity variables reaction_force 0 x' )
    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force integrated_surface_quantity variables reaction_force 1 y' )
    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force integrated_surface_quantity variables reaction_force 2 z' )
    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force integrated_surface_quantity use_set_from_load_condition "pull_load"' )
    flex.cmd( 'solid_mechanics_definitions probes load_reaction_force integrated_surface_quantity part "pipe"' )

    flex.cmd( 'procedures push new' )
    flex.cmd( 'procedures push solid_mechanics flex_model "flex_immersed"' )
    flex.cmd( 'procedures push solid_mechanics interval "push_interval"' )
    flex.cmd( 'procedures push solid_mechanics time_stepping_method "linear_statics"' )
    flex.cmd( 'procedures push solid_mechanics outputs 0 "field_results"' )
    flex.cmd( 'procedures push solid_mechanics outputs 1 "probe_results"' )
    flex.cmd( 'procedures push solid_mechanics load_conditions 0 "pressure_load"' )
    flex.cmd( 'procedures push solid_mechanics load_conditions 1 "pull_load"' )
    flex.cmd( 'procedures push solid_mechanics boundary_conditions 0 "x_symmetry"' )
    flex.cmd( 'procedures push solid_mechanics boundary_conditions 1 "y_symmetry"' )
    flex.cmd( 'procedures push solid_mechanics boundary_conditions 2 "hold_trunnion"' )
    flex.cmd( 'procedures push solid_mechanics boundary_conditions 3 "z_symmetry"' )

    flex.cmd(f'save "{cf_file}"' )
    
    flex.cmd(f'model_tree "job_manager queues local working_dir" "{eval_dir}"')

    flex.cmd( 'job pipe_evaluation new' )
    flex.cmd( 'job pipe_evaluation simulation queue "local"' )
    flex.cmd( f'job pipe_evaluation simulation processor_count {int( options.np )}' )
    flex.cmd( 'job pipe_evaluation submit' )
    flex.cmd( 'job pipe_evaluation wait' )

def get_max_mises_stress( eval_dir ):
    probe_filename = os.path.join( eval_dir, 'cf_iga_data_output.json' )
    with open( probe_filename ) as probe_file:
        output_data = json.decode_io(probe_file)['push']
        probe_data = output_data['history']
        max_mises_stress = probe_data['max_mises']['extremum']['stress']['von_mises'][-1]
    return max_mises_stress

def is_cad_feasible( params ):
    if params["inner_fillet_radius"] >= 0.9 * ( params["trunnion_inner_radius"] ):
        print( "MODEL ERROR 1" )
        return False
    elif params["trunnion_inner_radius"] + params["trunnion_thickness"] >= 0.9 * ( params["pipe_inner_radius"] + params["pipe_thickness"] ):
        print( "MODEL ERROR 2" )
        return False
    elif params["trunnion_inner_radius"] + params["trunnion_thickness"] + params["outer_fillet_radius"] >= 0.9 * ( params["pipe_length"] ):
        print( "MODEL ERROR 3" )
        return False
    else:
        return True
    
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