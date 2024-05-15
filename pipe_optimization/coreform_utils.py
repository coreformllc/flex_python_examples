import os
import sys
import pathlib

def mk_script_relative( filepath ):
    path_to_this_script = os.path.dirname( os.path.realpath( filepath ) )
    def script_relative( relpath ):
        return pathlib.Path(os.path.normpath( os.path.join( path_to_this_script, relpath ))).as_posix()
    return script_relative

def import_cubit( verbose=False ):
    if "win" in sys.platform:
        path_to_cubit = r"C:\Program Files\Coreform Cubit 2024.5\bin"
    elif "lin" in sys.platform:
        path_to_cubit = "/opt/Coreform-Cubit-2024.5/bin"
    sys.path.append( path_to_cubit )
    import cubit
    if verbose:
        cubit.init( [] )
    else:
        cubit.init( [ "cubit", "-noecho", "-nojournal", "-information", "off", "-warning", "off" ])
    return cubit

def import_flex( verbose=False ):
    if "win" in sys.platform:
        path_to_flex = r"C:\Program Files\Coreform Flex 2024.5\bin"
        sys.path.append( path_to_flex )
        from coreform import flex
    elif "lin" in sys.platform:
        path_to_flex = "/opt/Coreform-Flex-2024.5/bin"
        sys.path.append( path_to_flex )
        from coreform import flex
    flex.init( verbose )
    return flex