import os
def main( subdir ):
    f = open( os.path.join( subdir, "pad_dimensions.txt" ), "r" )
    fLines = f.readlines()
    fDataLine = fLines[1].strip().split( "," )
    pad_height = float( fDataLine[0] )
    pad_volume_ratio = float( fDataLine[1] )
    platen_width = float( fDataLine[2] )
    top_platen_y_probe = float( fDataLine[3] )
    f.close()
    return pad_height, pad_volume_ratio, platen_width, top_platen_y_probe