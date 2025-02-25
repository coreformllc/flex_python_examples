import os
import sys
import pathlib

def mk_script_relative( filepath ):
    path_to_this_script = os.path.dirname( os.path.realpath( filepath ) )
    def script_relative( relpath ):
        return pathlib.Path(os.path.normpath( os.path.join( path_to_this_script, relpath ))).as_posix()
    return script_relative

def import_cubit( verbose=False ):
    coreform_paths = get_coreform_paths()
    sys.path.append( os.fspath( coreform_paths["cubit_path"] ) )
    import cubit
    if verbose:
        cubit.init( [] )
    else:
        cubit.init( [ "cubit", "-noecho", "-nojournal", "-information", "off", "-warning", "off" ])
    return cubit

def import_flex( verbose=False ):
    coreform_paths = get_coreform_paths()
    sys.path.append( os.fspath( coreform_paths["flex_path"] ) )
    from coreform import flex
    flex.init( verbose=verbose, gui=False )
    return flex

def get_coreform_paths():
    coreform_paths = {}
    if "win" in sys.platform:
        coreform_paths["cubit"] =        pathlib.Path( r"C:\Program Files\Coreform Cubit 2025.2\bin\coreform.exe" )
        coreform_paths["cubit_path"] =   pathlib.Path( r"C:\Program Files\Coreform Cubit 2025.2\bin" )
        coreform_paths["flex"] =         pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin\coreform_flex.exe" )
        coreform_paths["flex_path"] =    pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin" )
        coreform_paths["trim"] =         pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin\coreform_trim.bat" )
        coreform_paths["trim_path"] =    pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin" )
        coreform_paths["iga"] =          pathlib.Path( r"C:\Program Files\Coreform IGA 2025.2\bin\coreform_iga.exe" )
        coreform_paths["iga_path"] =     pathlib.Path( r"C:\Program Files\Coreform IGA 2025.2\bin" )
        coreform_paths["mpiexec"] =      pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin\mpiexec.exe" )
        coreform_paths["mpiexec_path"] = pathlib.Path( r"C:\Program Files\Coreform Flex 2025.2\bin" )
    elif "lin" in sys.platform:
        coreform_paths["cubit"] =        pathlib.Path( "/opt/Coreform-Cubit-2025.2/bin/coreform_cubit" )
        coreform_paths["cubit_path"] =   pathlib.Path( "/opt/Coreform-Cubit-2025.2/bin" )
        coreform_paths["flex"] =         pathlib.Path( "/opt/Coreform-Flex-2025.2/bin/coreform_flex" )
        coreform_paths["flex_path"] =    pathlib.Path( "/opt/Coreform-Flex-2025.2/bin" )
        coreform_paths["trim"] =         pathlib.Path( "/opt/Coreform-Flex-2025.2/bin/coreform_trim" )
        coreform_paths["trim_path"] =    pathlib.Path( "/opt/Coreform-Flex-2025.2/bin" )
        coreform_paths["iga"] =          pathlib.Path( "/opt/Coreform-IGA-2025.2/bin/coreform_iga" )
        coreform_paths["iga_path"] =     pathlib.Path( "/opt/Coreform-IGA-2025.2/bin" )
        coreform_paths["mpiexec"] =      pathlib.Path( "/opt/Coreform-Flex-2025.2/bin/mpiexec" )
        coreform_paths["mpiexec_path"] = pathlib.Path( "/opt/Coreform-Flex-2025.2/bin" )
    return coreform_paths