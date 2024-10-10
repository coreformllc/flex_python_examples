import os
import numpy as np
import scipy as sp
from scipy import optimize
from scipy import integrate
import json
from matplotlib import pyplot as plt

def main( eng_strain, eng_stress, savedir=os.getcwd() ):
    plot_data( eng_strain, eng_stress, savedir )
    fit_results = fit_simulation_data( eng_strain, eng_stress )
    plot_fit( fit_results, savedir )
    return fit_results

def compression_region_fit(x, c1 ):
        y = c1 * x
        return y

def compaction_region_fit( x, a, b ):
    y = a * np.exp( b * x )
    return y

def fit_simulation_data( eng_strain, eng_stress ):
    sim_data_interp = lambda x: np.interp( x=x, xp=eng_strain, fp=eng_stress )
    min_dens_strain = eng_strain[1]
    max_dens_strain = eng_strain[-2]
    bounds = [min_dens_strain, max_dens_strain]
    dens_strain = sp.optimize.minimize_scalar( lambda x: fit_obj_fun( x, eng_strain, eng_stress, sim_data_interp ), method="bounded", bounds=bounds )
    fit_results = fit_eval( dens_strain.x, eng_strain, eng_stress, sim_data_interp )
    return fit_results

def fit_obj_fun( dens_strain, eng_strain, eng_stress, sim_data_interp ):
        fit = fit_eval( dens_strain, eng_strain, eng_stress, sim_data_interp )
        compression_res = fit["compression_fit"]["res"]
        compression_l2_norm = fit["compression_fit"]["l2_norm"]
        compaction_res = fit["compaction_fit"]["res"]
        compaction_l2_norm = fit["compaction_fit"]["l2_norm"]
        fit_obj_val = ( compression_res / compression_l2_norm ) + ( compaction_res / compaction_l2_norm )
        return fit_obj_val

def fit_eval( dens_strain, eng_strain, eng_stress, sim_data_interp ):
    filter_compression = eng_strain <= dens_strain
    filter_compaction = eng_strain >= dens_strain
    compression_coeffs, _ = sp.optimize.curve_fit( compression_region_fit, eng_strain[filter_compression], eng_stress[filter_compression] )
    compaction_coeffs, _ = sp.optimize.curve_fit( compaction_region_fit, eng_strain[filter_compaction], eng_stress[filter_compaction] )
    compression_fit_func = lambda x: compression_coeffs[0] * x
    compaction_fit_func = lambda x: compaction_coeffs[0] * np.exp( compaction_coeffs[1] * x )
    compression_l2_norm, _ = sp.integrate.quad( lambda x: sim_data_interp(x)**2.0, 0.0, dens_strain, limit=int( 1e6 ) )
    compaction_l2_norm, _ = sp.integrate.quad( lambda x: sim_data_interp(x)**2.0, dens_strain, eng_strain[-1], limit=int( 1e6 ) )
    compression_res, _ = sp.integrate.quad( lambda x: ( sim_data_interp(x) - compression_fit_func(x) )**2.0, 0.0, dens_strain, limit=int( 1e6 ) )
    compaction_res, _ = sp.integrate.quad( lambda x: ( sim_data_interp(x) - compaction_fit_func(x) )**2.0, dens_strain, eng_strain[-1], limit=int( 1e6 ) )
    compression_fit = { "filter": filter_compression, "coeffs": compression_coeffs, "fit_func": compression_fit_func, "l2_norm": compression_l2_norm, "res": compression_res, "domain": [0.0, dens_strain] }
    compaction_fit = { "filter": filter_compaction, "coeffs": compaction_coeffs, "fit_func": compaction_fit_func, "l2_norm": compaction_l2_norm, "res": compaction_res, "domain": [dens_strain, eng_strain[-1]] }
    sim_data = { "eng_strain":eng_strain, "eng_stress": eng_stress, "interp_func": sim_data_interp }
    fit_results = { "compression_fit": compression_fit, "compaction_fit": compaction_fit, "sim_data": sim_data }
    return fit_results

def plot_data( eng_strain, eng_stress, savedir=None ):
    fig, ax = plt.subplots()
    ax.set_xlabel( "Engineering strain" )
    ax.set_ylabel( "Engineering stress (kPa)" )
    ax.plot( eng_strain, eng_stress, marker="o" )
    if savedir != None:
        plt.savefig( os.path.join( savedir, "diw_force_disp.png" ) )
    
def plot_fit( fit_results, savedir=None ):
    eng_strain = fit_results["sim_data"]["eng_strain"]
    eng_stress = fit_results["sim_data"]["eng_stress"]
    compression_domain = fit_results["compression_fit"]["domain"]
    compaction_domain = fit_results["compaction_fit"]["domain"]
    x_compression = np.linspace( compression_domain[0], compression_domain[1], int( 1e3 ) )
    x_compaction = np.linspace( compaction_domain[0], compaction_domain[1], int( 1e3 ) )
    compression_fit_func = fit_results["compression_fit"]["fit_func"]
    compaction_fit_func = fit_results["compaction_fit"]["fit_func"]
    fig, ax = plt.subplots()
    ax.set_xlabel( "Engineering strain" )
    ax.set_ylabel( "Engineering stress (kPa)" )
    ax.plot( eng_strain, eng_stress, label="Simulation Data" )
    ax.plot( x_compression, compression_fit_func( x_compression ), label="Compression Fit" )
    ax.plot( x_compaction,  compaction_fit_func( x_compaction ), label="Compaction Fit" )
    ax.legend( loc="upper left" )
    if savedir != None:
        plt.savefig( os.path.join( savedir, "diw_force_disp_fit.png" ) )
