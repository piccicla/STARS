# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        getNDI.py
# Purpose:      calculate NDI (A-B)/(A+B) for different band combinations
#
# Author:      claudio piccinini
#
# Created:     18/11/2015
#-------------------------------------------------------------------------------

import os
import sys
import utility

def compute_NDI(img,  bands, outdir= None,outname = 'NDI', debug = False):
    """ get the NDV for different band combinations, result is saved in the out dir; file names are like NDI1_2

    :param img: image path
    :param bands: a list of tuples where each tuple is the band combination (you can use utility.combination_count())
    :param outdir: the output directory path
    :param outname: the prefix for the file name
    :param debug: output all messages?
    :return: everythin OK?
    """


    ok = True

    #TODO: this will not work when the script is called from the command line
    #get the directory for this script
    cpath = os.path.dirname(os.path.realpath(__file__))

    if debug: print(cpath)

    if outdir:
        outdir = outdir + "/"
    else:
        outdir = ""

    for bandA,bandB in bands:
        bandA=str(bandA)
        bandB=str(bandB)

        print('calculating NDI '+bandA+'-'+ bandB+"/"+bandA+'+'+ bandB)

        '''gdal_calc.py  http://www.gdal.org/gdal_calc.html
         Options:
          --calc=CALC           calculation in gdalnumeric syntax using +-/* or any
                                numpy array functions (i.e. logical_and())
          -A A                  input gdal raster file, note you can use any letter
                                A-Z
          --A_band=A_BAND       number of raster band for file A (default 1)
          --outfile=OUTF        output file to generate or fill
          --NoDataValue=NODATAVALUE
                                set output nodata value (Defaults to datatype specific
                                value)
          --type=TYPE           output datatype, must be one of ['Int32', 'Int16',
                                'Float64', 'UInt16', 'Byte', 'UInt32', 'Float32']
          --format=FORMAT       GDAL format for output file (default 'GTiff')
          --creation-option=CREATION_OPTIONS, --co=CREATION_OPTIONS
                                Passes a creation option to the output format driver.
                                Multiple options may be listed. See format specific
                                documentation for legal creation options for each
                                format.
          --allBands=ALLBANDS   process all bands of given raster (A-Z)
          --overwrite           overwrite output file if it already exists
          --debug               print debugging information
        '''

        msg, err = utility.run_script([cpath+r"\gdal_calc.py","-A", img,"--A_band="+bandA, "-B",img,"--B_band="+bandB,"--outfile="+outdir+outname+bandA+"_"+bandB+".tif","--type=Float32",'--calc="((A-B)/(A+B))"'])

        if err:
            print(err)
        if debug:
            print(msg)
        if err:
            if not (err == "\r\n" or err == "\r" or err == "\n"):  # windows, oldmac, unix
                ok = False


    return ok  #return true or false depending on the result


def workflow(rootpath, inputimage, outdir, nbands,debug ):
    """
    :param rootpath: directory with input/output
    :param inputimage: image name
    :param outdir: directory name for the output
    :param nbands: number of band combinations
    :param debug: complete messages?
    :return: None
    """

    #create output directory if it does not exist
    if not os.path.exists(rootpath+outdir):
        os.mkdir(rootpath+outdir)

    #get the band combinations
    bands = utility.combination_count(nbands)
    #combination_count() will return all the combination, but pixel value of  ndi A/B is just the inverse of ndi 2/1;
    # therefore we get only the first half of the combinations
    end = (len(bands[1])/2)
    bands = bands[1][0: int(end)]

    ok = compute_NDI(rootpath+inputimage, bands, rootpath+outdir, outname='NDI', debug=debug)
    if not ok:
        print(" there were some errors, some NDI images may not have been created , check the output")
        sys.exit(1)

###########TEST
if __name__ == "__main__":

    debug = True # print all tool error messages and running time
    rootpath = "D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/code/testdata/"
    inputimage = "raster.tif"
    outdir = "indexes"

    workflow(rootpath, inputimage, outdir, 8 ,debug=debug)