#!python3

import os
import pathlib
import argparse
import numpy
import json
import run_coreform_cubit
import run_coreform_flex
from coreform_utils import mk_script_relative

parser = argparse.ArgumentParser( prog='PlateWithHoleSweep' )

def cli_arguments( parser ):
    parser.add_argument( "-nt", dest="nt", type=int, default=16 )
    parser.add_argument( "-ni", dest="ni", type=int, default=16 )
    parser.add_argument( "--strategy", dest="strategy", type=str, choices=["bodyfit", "immersed"], default="immersed" )
    parser.add_argument( "--mesh-size", dest="mesh_size", type=float, default=4 )
    parser.add_argument( "--degree", dest="degree", type=int, default=4 )
    return parser.parse_args()

script_relative = mk_script_relative( __file__ )
top_wd = os.getcwd()
log_file = "sweep_monitor.log"
yield_stress = 36260 # PSI

def main( args ):
    args = vars( args )
    args["top_wd"] = pathlib.Path( top_wd ).as_posix()
    N = 10
    radius_list = numpy.linspace( 0.1, 24.9, N )
    displacement_list = numpy.zeros( N )
    max_stress_list = numpy.zeros( N )
    for i in range( 0, len( radius_list ) ):
        args["radius"] = radius_list[i]
        run_coreform_cubit.main( args )
        run_coreform_flex.main( args )
        displacement_list[i] = get_max_displacement()
        max_stress_list[i] = get_max_stress()

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
