import os
import sys
import time
import coreform_utils

def flex_commands( args ):
    flex = coreform_utils.import_flex()
    workdir = args["top_wd"]

    flex.cmd("reset")
    cf_filename = os.path.join( workdir, "plate_with_hole_geom.cf" )
    flex.cmd(f'open "{cf_filename}"' )

    if args["strategy"] == "immersed":
        hatch_spacing = args["mesh_size"]
        degree = args["degree"]
        flex.cmd(f'fill "fill_coupon" affine degree {degree} continuity {degree-1} hatch_spacing [{hatch_spacing} {hatch_spacing} {0.5}] padding [{degree} {degree} {degree}] hatch_layout [edge_centered edge_centered edge_centered]' )
        flex.cmd("part coupon fill 1")
        flex.cmd("part coupon volume_box axis_aligned extend_percent [1 1 1]")
    elif args["strategy"] == "bodyfit":
        degree = args["degree"]
        flex.cmd(f'fill "fill_coupon" mesh_from_cf degree {degree} continuity {degree-1}' )
        flex.cmd("part coupon fill 1")

    flex.cmd( 'coreform_iga_version 2024.5' )
    flex.cmd( 'label "axial_tension"' )

    flex.cmd( 'materials steel new' )
    flex.cmd( 'materials steel mass_density 7e-4' )
    flex.cmd( 'materials steel elastic youngs_modulus 30e6' )
    flex.cmd( 'materials steel elastic poissons_ratio 0.3' )
    flex.cmd( 'materials steel elastic large_deformations false' )

    flex.cmd( 'flex_models flex_inf new' )
    flex.cmd( 'flex_models flex_inf database_name "geom.cf"' )
    flex.cmd(f'flex_models flex_inf small_cell_volume_ratio 0' )

    flex.cmd( 'flex_models flex_inf parts coupon part "coupon"' )
    flex.cmd( 'flex_models flex_inf parts coupon material "steel"' )
    flex.cmd( 'flex_models flex_inf parts coupon material_model elastic' )
    flex.cmd( 'flex_models flex_inf parts coupon quadrature QP1' )

    flex.cmd( 'functions constant_1 new' )
    flex.cmd( 'functions constant_1 constant value 1' )

    flex.cmd( 'functions linear_ramp new' )
    flex.cmd( 'functions linear_ramp piecewise_linear abscissa [0 1]' )
    flex.cmd( 'functions linear_ramp piecewise_linear ordinate [0 1]' )

    flex.cmd( 'intervals pull_interval new' )
    flex.cmd( 'intervals pull_interval start_time 0' )
    flex.cmd( 'intervals pull_interval stop_time 1' )

    flex.cmd( 'time_steppers linear_statics new' )
    flex.cmd( 'time_steppers linear_statics linear linear_equation_solver "direct_lu"' )

    flex.cmd( 'linear_equation_solvers direct_lu new' )
    flex.cmd( 'linear_equation_solvers direct_lu direct lu' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm displacement components 0 x' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm displacement scale_factor 0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm set "xmin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions x_symm penalty 30e9' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm displacement components 0 y' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm displacement scale_factor 0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm set "ymin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions y_symm penalty 30e9' )

    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm new' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm displacement components 0 z' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm displacement function "constant_1"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm displacement scale_factor 0' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm set "zmin"' )
    flex.cmd( 'solid_mechanics_definitions boundary_conditions z_symm penalty 30e9' )

    flex.cmd( 'solid_mechanics_definitions load_conditions pull_xmax new' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_xmax surface_pressure scale_factor -5000' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_xmax surface_pressure function "linear_ramp"' )
    flex.cmd( 'solid_mechanics_definitions load_conditions pull_xmax set "xmax"' )

    flex.cmd( 'solid_mechanics_definitions outputs field_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field database_name "results"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field interval "pull_interval"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field part "coupon"' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 0 x' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 1 y' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables displacement 2 z' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field variables stress 0 all' )
    flex.cmd( 'solid_mechanics_definitions outputs field_results field element_variable_output_strategy interpolate' )

    flex.cmd( 'solid_mechanics_definitions outputs probe_results new' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history interval "pull_interval"' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 0 "stress_probe"' )
    flex.cmd( 'solid_mechanics_definitions outputs probe_results history probe_variables 1 "disp_probe"' )

    flex.cmd( 'solid_mechanics_definitions probes stress_probe new' )
    flex.cmd(f'solid_mechanics_definitions probes stress_probe field single_point location [0 {args["radius"]} 0]' )
    flex.cmd( 'solid_mechanics_definitions probes stress_probe field location_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes stress_probe field field_variable_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes stress_probe field variables stress 0 max_principal' )

    flex.cmd( 'solid_mechanics_definitions probes disp_probe new' )
    flex.cmd(f'solid_mechanics_definitions probes disp_probe field single_point location [50 0 0]' )
    flex.cmd( 'solid_mechanics_definitions probes disp_probe field location_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes disp_probe field field_variable_configuration reference' )
    flex.cmd( 'solid_mechanics_definitions probes disp_probe field variables displacement 0 x' )

    flex.cmd( 'procedures pull new' )
    flex.cmd( 'procedures pull solid_mechanics flex_model "flex_inf"' )
    flex.cmd( 'procedures pull solid_mechanics interval "pull_interval"' )
    flex.cmd( 'procedures pull solid_mechanics time_stepping_method "linear_statics"' )
    flex.cmd( 'procedures pull solid_mechanics boundary_conditions 0 "x_symm"' )
    flex.cmd( 'procedures pull solid_mechanics boundary_conditions 1 "y_symm"' )
    flex.cmd( 'procedures pull solid_mechanics boundary_conditions 2 "z_symm"' )
    flex.cmd( 'procedures pull solid_mechanics load_conditions 0 "pull_xmax"' )
    flex.cmd( 'procedures pull solid_mechanics outputs 0 "field_results"' )
    flex.cmd( 'procedures pull solid_mechanics outputs 1 "probe_results"' )

    # DEFINE LOCAL QUEUE
    # flex.cmd(f'model_tree "job_manager queues local working_dir" "{workdir.as_posix()}"' )
    flex.cmd( f'save "plate_with_hole"' )

    # DEFINE JOB
    flex.cmd(f'model_tree "job_manager queues local working_dir" "{workdir}"' )
    jobname = 'job_plate_with_hole'
    flex.cmd(f'job {jobname} trim trim_processor_count {args["nt"]}' )
    flex.cmd(f'job {jobname} trim trim_parts [coupon]' )
    # SUBMIT TRIM JOB
    flex.cmd(f'job {jobname} submit' )
    flex.cmd(f'job {jobname} wait' )
    # SUBMIT IGA JOB
    flex.cmd(f'job {jobname} simulation processor_count {args["ni"]}' )
    flex.cmd(f'job {jobname} submit' )
    flex.cmd(f'job {jobname} wait' )
    flex.shutdown()
