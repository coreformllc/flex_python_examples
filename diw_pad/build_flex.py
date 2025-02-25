import os
import math
import decimal
import read_geometry_dimensions
import coreform_utils

def flex_commands( options ):
    flex = coreform_utils.import_flex( verbose=True )
    params = options["params"]
    pad_height, pad_volume_ratio, platen_width, top_platen_y_probe = read_geometry_dimensions.main()
    pad_compression_distance = -0.9 * pad_height * ( 1 - pad_volume_ratio )
    top_platen_velocity = abs( pad_compression_distance / 1.0 )
    degree = params['degree']
    mesh_size = params['mesh_size']
    contact_activation_distance = 0.5 * mesh_size
    max_time_step = contact_activation_distance / top_platen_velocity
    print( f"Max Time Step from Heuristic: {max_time_step} time-units" )
    max_time_step = round_to_sf( max_time_step, 2, decimal.ROUND_DOWN )
    print( f"Max Time Step from Heuristic: {max_time_step} time-units" )


    flex.cmd("reset")

    cad_file = options["cad_file"]
    cf_cad_file = options["cf_cad_file"]
    flex.cmd(f'open "{cad_file}"' )

    degree = params['degree']
    mesh_size = params['mesh_size']
    flex.cmd(f'mesh "mesh_1" rectilinear degree {degree} continuity {degree-1} element_size [{mesh_size} {mesh_size} {mesh_size}] padding [{degree+1} {degree+1} {degree+1}]' )
    flex.cmd("part pad mesh mesh_1")
    flex.cmd("part pad volume_box axis_aligned")

    if params["platen_mesh_bodyfit"] == True:
        flex.cmd(f'mesh "mesh_2" mesh_from_cf degree {degree} continuity {degree-1}' )
        flex.cmd(f'mesh "mesh_3" mesh_from_cf degree {degree} continuity {degree-1}' )
        flex.cmd("part bot_platen mesh mesh_2")
        flex.cmd("part top_platen mesh mesh_3")
    else:
        flex.cmd(f'mesh "mesh_2" rectilinear degree {degree} continuity {degree-1} element_size [0.1 0.1 0.1] padding [{degree+1} {degree+1} {degree+1}]' )
        flex.cmd(f'mesh "mesh_3" rectilinear degree {degree} continuity {degree-1} element_size [0.1 0.1 0.1] padding [{degree+1} {degree+1} {degree+1}]' )
        flex.cmd("part bot_platen mesh mesh_2")
        flex.cmd("part top_platen mesh mesh_3")
        flex.cmd("part bot_platen volume_box axis_aligned")
        flex.cmd("part top_platen volume_box axis_aligned")

    ############### DEFINE SIMULATION PARAMETERS ###############

    flex.cmd( f'coreform_iga_version "{flex.version_short()}"' )
    flex.cmd( 'label "diw_compression"' )

    use_stabilization = params['stabilization']

    poissons_ratio = params["poissons_ratio"]
    shear_modulus = 1.0
    bulk_modulus = ( 2 * shear_modulus * ( 1 + poissons_ratio ) ) / ( 3 * ( 1 - 2 * poissons_ratio ) )
    youngs_modulus = 9 * bulk_modulus * shear_modulus / ( 3 * bulk_modulus + shear_modulus )

    flex.cmd( 'materials se1700 new' )
    flex.cmd( 'materials se1700 mass_density 1e-9' )
    # Neohookean
    flex.cmd(f'materials se1700 neohookean bulk_modulus {bulk_modulus}' )
    flex.cmd(f'materials se1700 neohookean shear_modulus {shear_modulus}' )
    if use_stabilization:
        flex.cmd( 'materials se1700 neohookean pressure_stabilization stabilization_parameter 0.1' )

    flex.cmd( 'materials rigid new' )
    flex.cmd( 'materials rigid mass_density 1.0' )
    flex.cmd(f'materials rigid elastic youngs_modulus {youngs_modulus*1e3}' )
    flex.cmd( 'materials rigid elastic poissons_ratio 0.00' )
    flex.cmd(f'materials rigid neohookean youngs_modulus {youngs_modulus*1e3}' )
    flex.cmd( 'materials rigid neohookean poissons_ratio 0.00' )

    flex.cmd( 'flex_models flex_inf new' )
    flex.cmd( f'flex_models flex_inf database_name "{cf_cad_file.split(".")[0]}"' )
    flex.cmd( 'flex_models flex_inf small_cell_volume_ratio 0.0' )

    flex.cmd( 'flex_models flex_inf parts pad_instance new' )
    flex.cmd( 'flex_models flex_inf parts pad_instance part pad' )
    flex.cmd( 'flex_models flex_inf parts pad_instance material se1700' )
    flex.cmd( 'flex_models flex_inf parts pad_instance material_model neohookean' )

    flex.cmd( 'flex_models flex_inf parts top_platen_instance new' )
    flex.cmd( 'flex_models flex_inf parts top_platen_instance part top_platen' )
    flex.cmd( 'flex_models flex_inf parts top_platen_instance material rigid' )
    flex.cmd( 'flex_models flex_inf parts top_platen_instance material_model neohookean' )

    flex.cmd( 'flex_models flex_inf parts bot_platen_instance new' )
    flex.cmd( 'flex_models flex_inf parts bot_platen_instance part bot_platen' )
    flex.cmd( 'flex_models flex_inf parts bot_platen_instance material rigid' )
    flex.cmd( 'flex_models flex_inf parts bot_platen_instance material_model neohookean' )

    flex.cmd( 'functions constant_1 new' )
    flex.cmd( 'functions constant_1 constant value 1.0' )

    flex.cmd( 'functions linear_ramp new' )
    flex.cmd( 'functions linear_ramp piecewise_linear abscissa [0 1]' )
    flex.cmd( 'functions linear_ramp piecewise_linear ordinate [0 1]' )

    flex.cmd( 'intervals compress_pad_interval new' )
    flex.cmd( 'intervals compress_pad_interval start_time 0.0' )
    flex.cmd( 'intervals compress_pad_interval stop_time 1.0' )
    flex.cmd( 'intervals compress_pad_interval time_increment 1e-2' )

    flex.cmd( 'intervals output_interval new' )
    flex.cmd( 'intervals output_interval use_start_stop_from_interval compress_pad_interval' )
    flex.cmd( 'intervals output_interval step_increment 1' )

    flex.cmd( 'procedures compress_pad new' )
    flex.cmd( 'procedures compress_pad solid_mechanics flex_model flex_inf' )
    flex.cmd( 'procedures compress_pad solid_mechanics interval compress_pad_interval' )

    golden_ratio = ( 1 + math.sqrt( 5 ) ) / 2
    increase_factor = golden_ratio
    decrease_factor = 1 - ( 1 / golden_ratio )
    flex.cmd( 'time_steppers nonlinear_quasistatics new ' )
    flex.cmd( 'time_steppers nonlinear_quasistatics continuation nonlinear_equation_solver newton_raphson' )
    flex.cmd( 'time_steppers nonlinear_quasistatics continuation adaptivity maximum_time_step 0.05' )
    flex.cmd( 'time_steppers nonlinear_quasistatics continuation adaptivity minimum_time_step 1e-5' )
    flex.cmd( f'time_steppers nonlinear_quasistatics continuation adaptivity decrease_factor {decrease_factor}' )
    flex.cmd( f'time_steppers nonlinear_quasistatics continuation adaptivity increase_factor {increase_factor}' )

    flex.cmd( 'time_steppers implicit_dynamic new' )
    flex.cmd( 'time_steppers implicit_dynamic implicit_midpoint nonlinear_equation_solver newton_raphson' )
    flex.cmd( 'time_steppers implicit_dynamic implicit_midpoint adaptivity maximum_time_step 0.05' )
    flex.cmd( 'time_steppers implicit_dynamic implicit_midpoint adaptivity minimum_time_step 1e-5' )
    flex.cmd( f'time_steppers implicit_dynamic implicit_midpoint adaptivity decrease_factor {decrease_factor}' )
    flex.cmd( f'time_steppers implicit_dynamic implicit_midpoint adaptivity increase_factor {increase_factor}' )


    # NOTE: Generalized-alpha with a zero spectral radius may be more stabe/robust than implicit midpoint (which is
    # just generalized-alpha with a spectral radius of 1).  This will damp-out high-frequency step-to-step
    # oscillations that are non-physical modes and basically artifacts of the spatial discretization.
    flex.cmd( 'time_steppers implicit_dynamics_numerical_damping new' )
    flex.cmd( 'time_steppers implicit_dynamics_numerical_damping generalized_alpha nonlinear_equation_solver newton_raphson' )
    flex.cmd( 'time_steppers implicit_dynamics_numerical_damping generalized_alpha spectral_radius 0.0' )
    flex.cmd( 'time_steppers implicit_dynamics_numerical_damping generalized_alpha adaptivity maximum_time_step 0.05' )
    flex.cmd( 'time_steppers implicit_dynamics_numerical_damping generalized_alpha adaptivity minimum_time_step 1e-5' )
    flex.cmd( f'time_steppers implicit_dynamics_numerical_damping generalized_alpha adaptivity decrease_factor {decrease_factor}' )
    flex.cmd( f'time_steppers implicit_dynamics_numerical_damping generalized_alpha adaptivity increase_factor {increase_factor}' )

    flex.cmd( 'time_steppers implicit_dynamics_quasistatic new' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha nonlinear_equation_solver newton_raphson' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha alpha_options alpha_f 1.0' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha alpha_options alpha_m 1.0' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha alpha_options gamma 1.0' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha alpha_options beta 0.5' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha adaptivity maximum_time_step 0.05' )
    flex.cmd( 'time_steppers implicit_dynamics_quasistatic generalized_alpha adaptivity minimum_time_step 1e-5' )
    flex.cmd( f'time_steppers implicit_dynamics_quasistatic generalized_alpha adaptivity decrease_factor {decrease_factor}' )
    flex.cmd( f'time_steppers implicit_dynamics_quasistatic generalized_alpha adaptivity increase_factor {increase_factor}' )

    flex.cmd( 'nonlinear_equation_solvers newton_raphson new' )
    # NOTE: Loose nonlinear tolerances can prevent convergence even with adaptive time stepping, since a poorly-converged
    # large step can leave the model in a state where even very small subsequent steps cannot converge.  It's probably better to
    # use tighter tolerances with moderate/low iteration counts, and just let the adaptivity shrink the time step size as needed.
    flex.cmd( 'nonlinear_equation_solvers newton_raphson newton linear_equation_solver direct_lu' )
    flex.cmd( 'nonlinear_equation_solvers newton_raphson newton target_relative_residual 1e-8' )
    flex.cmd( 'nonlinear_equation_solvers newton_raphson newton maximum_iterations 12' )

    flex.cmd( 'linear_equation_solvers direct_lu new' )
    flex.cmd( 'linear_equation_solvers direct_lu direct lu' )

    flex.cmd( 'linear_equation_solvers direct_multifrontal new' )
    flex.cmd( 'linear_equation_solvers direct_multifrontal direct multi_frontal' )

    ## BOUNDARY CONDITIONS
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_pad new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_pad displacement components 0 x' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_pad displacement function constant_1' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_pad displacement scale_factor 0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_pad set xfaces_pad' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_pad new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_pad displacement components 0 z' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_pad displacement function constant_1' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_pad displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_pad set zfaces_pad' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_platen new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_platen displacement components 0 x' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_platen displacement function constant_1' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_platen displacement scale_factor 0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symmetry_platen set xfaces_platen' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_platen new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_platen displacement components 0 z' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_platen displacement function constant_1' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_platen displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symmetry_platen set zfaces_platen' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_bot_platen_ymin new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_bot_platen_ymin displacement components 0 y' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_bot_platen_ymin displacement function constant_1' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_bot_platen_ymin displacement scale_factor 0.0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions hold_bot_platen_ymin set bot_platen_ymin' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions push_top_platen_ymax new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions push_top_platen_ymax displacement components 0 y' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions push_top_platen_ymax displacement function linear_ramp' )
    flex.cmd(f'solid_mechanics_definitions boundary_conditions push_top_platen_ymax displacement scale_factor {pad_compression_distance}' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions push_top_platen_ymax set top_platen_ymax' )

    flex.cmd( 'solid_mechanics_definitions interactions contact new' )
    flex.cmd( 'solid_mechanics_definitions interactions contact mechanical_contact base_contact' )
    flex.cmd( 'solid_mechanics_definitions interactions contact mechanical_contact base_contact complement true' )
    flex.cmd( 'solid_mechanics_definitions interactions contact mechanical_contact interaction_properties "coulomb_friction_contact"')

    flex.cmd( 'solid_mechanics_definitions interaction_properties coulomb_friction_contact new')
    flex.cmd( 'solid_mechanics_definitions interaction_properties coulomb_friction_contact coulomb_friction coefficient_with_regularization friction_coefficient 0.3')
    flex.cmd(f'solid_mechanics_definitions interaction_properties coulomb_friction_contact coulomb_friction coefficient_with_regularization regularization_velocity {0.1 * abs( top_platen_velocity )}')

    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field database_name pad_results' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field interval output_interval' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field part pad' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field variables displacement 2 z' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field variables stress 0 all' )
    flex.cmd( 'solid_mechanics_definitions outputs pad_field_results field element_variable_output_strategy interpolate' )

    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field database_name top_platen_results' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field interval output_interval' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field part top_platen' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field variables displacement 2 z' )
    flex.cmd( 'solid_mechanics_definitions outputs top_platen_field_results field element_variable_output_strategy interpolate' )

    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field database_name bot_platen_results' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field interval output_interval' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field part bot_platen' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field variables displacement 2 z' )
    flex.cmd( 'solid_mechanics_definitions outputs bot_platen_field_results field element_variable_output_strategy interpolate' )

    flex.cmd( 'solid_mechanics_definitions outputs probe_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history interval output_interval' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 0 top_reaction_probe' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 1 bot_reaction_probe' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 2 top_platen_probe' )

    flex.cmd( 'solid_mechanics_definitions probes top_reaction_probe new' )
    flex.cmd( 'solid_mechanics_definitions probes top_reaction_probe integrated_surface_quantity variables reaction_force 0 y' )
    flex.cmd( 'solid_mechanics_definitions probes top_reaction_probe integrated_surface_quantity part top_platen' )
    flex.cmd( 'solid_mechanics_definitions probes top_reaction_probe integrated_surface_quantity use_set_from_boundary_condition push_top_platen_ymax' )

    flex.cmd( 'solid_mechanics_definitions probes bot_reaction_probe new' )
    flex.cmd( 'solid_mechanics_definitions probes bot_reaction_probe integrated_surface_quantity variables reaction_force 0 y' )
    flex.cmd( 'solid_mechanics_definitions probes bot_reaction_probe integrated_surface_quantity part bot_platen' )
    flex.cmd( 'solid_mechanics_definitions probes bot_reaction_probe integrated_surface_quantity use_set_from_boundary_condition hold_bot_platen_ymin' )

    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe new' )
    flex.cmd(f'solid_mechanics_definitions probes top_platen_probe field single_point location [0 {top_platen_y_probe} 0]' )
    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe field location_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe field field_variable_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions probes top_platen_probe field variables displacement 2 z' )

    flex.cmd( 'procedures compress_pad solid_mechanics' )
    if params["solver"] == "static":
        flex.cmd( 'procedures compress_pad solid_mechanics time_stepping_method nonlinear_quasistatics' )
    elif params["solver"] == "quasistatic":
        flex.cmd( 'procedures compress_pad solid_mechanics time_stepping_method implicit_dynamics_numerical_damping' )
    elif params["solver"] == "dynamic":
        flex.cmd( 'procedures compress_pad solid_mechanics time_stepping_method implicit_dynamic' )

    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 0 x_symmetry_pad' )
    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 1 z_symmetry_pad' )
    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 2 x_symmetry_platen' )
    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 3 z_symmetry_platen' )
    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 4 hold_bot_platen_ymin' )
    flex.cmd( 'procedures compress_pad solid_mechanics boundary_conditions 5 push_top_platen_ymax' )
    flex.cmd( 'procedures compress_pad solid_mechanics interactions 0 contact' )
    flex.cmd( 'procedures compress_pad solid_mechanics outputs 0 pad_field_results' )
    flex.cmd( 'procedures compress_pad solid_mechanics outputs 1 top_platen_field_results' )
    flex.cmd( 'procedures compress_pad solid_mechanics outputs 2 bot_platen_field_results' )
    flex.cmd( 'procedures compress_pad solid_mechanics outputs 3 probe_results' )

    flex.cmd(f'save "flex_geom.cf"' )
    flex.cmd(f'export "iga_params.json5"' )

    coreform_paths = coreform_utils.get_coreform_paths()
    flex.cmd( f'model_tree "job_manager queues local mpiexec_path" "{coreform_paths["mpiexec"].as_posix()}"' )
    flex.cmd( f'model_tree "job_manager queues local trim_path" "{coreform_paths["trim"].as_posix()}"' )
    flex.cmd( f'model_tree "job_manager queues local iga_path" "{coreform_paths["iga"].as_posix()}"' )
    flex.cmd( f'root_dir "{os.getcwd()}"' )

    test_name = options["test_name"]
    num_proc = params["num_proc"]
    flex.cmd( f'job "{test_name}" new' )
    flex.cmd( f'job "{test_name}" simulation processor_count {num_proc}' )
    flex.cmd( f'job "{test_name}" submit' )
    flex.cmd( f'job "{test_name}" wait' )

def round_to_sf( value, sig_figs, rounding_mode ):
    """Rounds value to sig_figs significant figures using the specified rounding mode."""
    if value == 0:
        return 0  # Avoid log10 issues with zero
    d_value = decimal.Decimal( value )
    exponent = decimal.Decimal( sig_figs - 1 - d_value.log10().to_integral_value( decimal.ROUND_FLOOR ) )
    quant = decimal.Decimal( 10 ) ** ( -exponent )
    val = float( d_value.quantize( quant, rounding=rounding_mode ) )
    return val