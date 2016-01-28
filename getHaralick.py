# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        getHaralick.py
# Purpose:      compute Haralick, advanced and higher order texture features on every pixel in the selected channel
#                need to have Orfeo toolbox on your system https://www.orfeo-toolbox.org/
#
# Author:      claudio piccinini
#
# -------------------------------------------------------------------------------
import os
import sys
import utility


def compute_haralick(params, debug=False):
    """ compute haralick with the passed parameters
        possible Parameters:
        -progress         <boolean>        Report progress
        -in               <string>         Input Image  (mandatory)
        -channel          <int32>          Selected Channel  (mandatory, defaultvalue is 1)
        -ram              <int32>          Available RAM (Mb)  (optional, off bydefault, default value is 128)
        -parameters.xrad  <int32>          X Radius  (mandatory, default value is 2)
        -parameters.yrad  <int32>          Y Radius  (mandatory, default value is 2)
        -parameters.xoff  <int32>          X Offset  (mandatory, default value is 1)
        -parameters.yoff  <int32>          Y Offset  (mandatory, default value is 1)
        -parameters.min   <float>          Image Minimum  (mandatory, default value is 0)
        -parameters.max   <float>          Image Maximum  (mandatory, default value is 255)
        -parameters.nbbin <int32>          Histogram number of bin  (mandatory,default value is 8)
        -texture          <string>         Texture Set Selection [simple/advanced/higher]
        (mandatory, default value is simple)
        -out              <string> [pixel] Output Image  [pixel=uint8/uint16/int16/uint32/int32/float/double]
        (default value is float) (optional, on by default)
        -inxml            <string>         Load otb application from xml file  (optional, off by default)
    :param params: list of parameters, see above for the possible parameters
    :param debug: output all the messages?
    :return: msg, err
    """

    # print("compute Haralick for image " + params[2] + "\n" + "channel" + params[4])
    msg, err = utility.run_tool(params)
    if err:
        print(err)
    if debug:
        print(msg)
    return msg, err

def scale_image(rootpath, inputimage, exact= True, debug=False):
    """
    :param rootpath:
    :param inputimage:
    :param scaledout:
    :param exact:
    :param debug:
    :return: the output image path
    """

    if exact:  # scale all the bands exactly from 0 to 255 with orfeo
        print("scaling image exactly from 0 to 255, wait....")
        scaledout = rootpath + "rasterRescaled0_255.tif"
        out, err = utility.convert_raster(inputimage, scaledout)

        if debug:
            print(out)

        if err:
            if not (err == "\r\n" or err == "\r" or err == "\n"):  # windows, oldmac, unix
                print(err)
                sys.exit(1)

    else:  # scale all the bands within 0 to 255 with gdal
        print("scaling image within 0 to 255, wait....")
        scaledout = rootpath + "rasterRescaledWithin0_255.tif"
        out, err = utility.run_tool(['gdal_translate.exe', inputimage, scaledout, "-scale"])

        if debug:
            print(out)

        if err:
            if not (err == '\r\n' or err == '\r' or err == '\n'):  # windows, oldmac, unix
                print(err)
                print("the input image could not be rescaled, script is stopping")
                sys.exit(1)

    return scaledout


def heralick_from_image(input, outdir, params,xyoff,nbands=8, debug = False):
    """
    :param input:
    :param outdir:
    :param params:
    :param xyoff:
    :param nbands:
    :param debug:
    :return:
    """

    if not os._exists(outdir):
        os.mkdir(outdir)

    for i in range(1, nbands + 1):
        params[4] = str(i)  # set the channel

        # get image min and max
        min, max = utility.get_minmax(inputimage, i)
        print(min, max)

        params[8] = str(min)
        params[10] = str(max)

        # update parameters with the offset angle
        for x, y in xyoff:
            newparams = params + ['-parameters.xoff', str(x), '-parameters.yoff', str(y)]
            newparams[12] = outdir + '/HaralickChannel' + newparams[4] + newparams[6] + 'xoff' + newparams[
                14] + 'yoff' + newparams[16] + '.tif'  # set output
            print("computing haralick for " + newparams[2] + "\n" + "channel " + newparams[4] + " wait for a few hours :D ")
            msg, err = compute_haralick(newparams, debug)
            if err:
                if not (err == "\r\n" or err == "\r" or err == "\n"):  # windows, oldmac, unix
                    print(" some heraick from the image could not be created , script is stopping")
                    sys.exit(1)


def scale_ndvi(path,inimgfrmt = ['.tif'], debug = False):
    """ Scale NDVI images from 0 to 255
    note: this scaling seems not to work, that's why we use the min/max values in heralick_NDI()
    :param path: tha directory that contains the NDI images
    :param inimgfrmt: list of formats to filter
    :param debug: complete messages?
    :return: None
    """

    imgs = os.listdir(path)
    # make a "scaled" directory if it does not exist
    if not os.path.exists(path + "/scaled"):
        os.mkdir(path + "/scaled")
    # iterate the items in the folder
    for i in imgs:
        wrong = False
        # discard the directories
        if os.path.isfile(path + '/' + i) and (os.path.splitext(path + '/' + i)[-1] in inimgfrmt):
            print("scaling " + i)

            # scale within 0 and 255
            # out,err = utility.run_tool( ['gdal_translate.exe', path+"/"+i, path+"/scaled/"+i+"_scaled.tif", '-scale', '-1','1', '0', '255'])
            # ####path+'/'+i,path+'/scaled/'+i+'_scaled.tif','uint8', 'linear' )

            # scale exactly from 0 to 255 with orfeo
            out, err = utility.convert_raster(path + '/' + i, path + "/scaled/" + i + "_scaled.tif")

            if debug:
                print(out)
            if err:
                if not (err == "\r\n" or err == "\r" or err == "\n"):  # windows, oldmac, unix
                    print(err)
                    wrong = True
        # if some image could not rescaled exit
        if wrong:
            print("some NDI images could not be rescaled, script is stopping")
            sys.exit(1)


def heralick_NDI(rootpath, ndipath, params, xyoff,  inimgfrmt = ['.tif'], debug=False):
    """
    :param rootpath:
    :param ndipath:
    :param params:
    :param xyoff:
    :param inimgfrmt:
    :param debug:
    :return:
    """

    imgs = os.listdir(ndipath)
    if not os.path.exists(rootpath + "haralick"):
        os.mkdir(rootpath + "haralick")
    if not os.path.exists(rootpath + "haralick/NDI"):
        os.mkdir(rootpath + "haralick/NDI")

    outdir = rootpath + "haralick/NDI"
    for i in imgs:
        if os.path.isfile(ndipath + '/' + i) and (os.path.splitext(ndipath + '/' + i)[-1] in inimgfrmt):
            params[2] = ndipath + '/' + i
            params[4] = '1'

            # get image min and max
            min, max = utility.get_minmax(ndipath + '/' + i)
            print(min, max)

            params[8] = str(min)
            params[10] = str(max)

            # update parameters with the offset angle
            for x, y in xyoff:
                newparams = params + ['-parameters.xoff', str(x), '-parameters.yoff', str(y)]
                newparams[12] = outdir + '/' + i + 'HaralickChannel' + newparams[4] + newparams[6] \
                                + 'xoff' + newparams[14] + 'yoff' + newparams[16] + '.tif'  # set output
                print("computing haralick for " + params[2] + "\n" + "channel " + params[4]
                      + " wait for a few hours :D ")

                if debug:
                    import datetime as time
                    starttime = time.datetime.now()

                msg, err = compute_haralick(newparams, debug)
                if debug:
                    endtime = time.datetime.now()
                    print('elapsed time')
                    print(endtime - starttime)  # about 2h 25 minutes
                if err:
                    if not (err == "\r\n" or err == "\r" or err == "\n"):  # windows, oldmac, unix
                        print(" some NDI heralick images could not be created , script is stopping")
                        sys.exit(1)

def workflow(rootpath, inputimage, scaleimage, exactscale, heralickimage,herafolder, scalendi, heralickNDI, heralickimagedict=None, heralickNDIdict = None,herabands=8,debug = False):
    """ Execute a complete workflow, starting from the original image
    :param rootpath: root directory where original image and NDI images are located
    :param inputimage: path to the input multiband image
    :param scaleimage: scale the image bands to 0-255?
    :param exactscale: scale the image exactly from 0 to 255 or within 0-255?
    :param heralickimage:  calculate heralik for the image?
    :param herafolder: the folder to store the heralick for the image
    :param scalendi: scale the NDI images?
    :param heralickNDI: calculate heralick for the image?
    :param heralickimagedict: dictionary with params and xyoff keys
    :param heralickNDIdict: dictionary with params and xyoff keys
    :param herabands: number of image bands for heralick calculation
    :param debug: complete messages?
    :return: None
    """

    ###########SCALING IMAGE######################

    if scaleimage:
        scaledout = scale_image(rootpath, inputimage, debug=debug)

    ##################haralick for the multiband image################################

    if heralickimage:
        heralick_from_image(scaledout,herafolder,  heralickimagedict[0], heralickimagedict[1], debug=debug)

    ##############scale pixel values of the NDI images###############################
    if scalendi:  # a "indexes/scaled" directory is created if it does not exist
        scale_ndvi(rootpath + "indexes", debug=debug)

    #######################haralik for the ndvi###################################
    if heralickNDI:
        if scalendi:
            ndipath = rootpath + "indexes/scaled"
        else:
            ndipath = rootpath + "indexes"

        # a "haralik/NDI" directory is created if it does not exist
        heralick_NDI(rootpath, ndipath, heralickNDIdict[0], heralickNDIdict[1], debug=debug)


if __name__ == "__main__":

    debug = True # print all tool error messages and running time
    scaleimage = False  # scale the input image between 0 and 255?
    heralickimage = False  # output heralick for multiband image?
    scalendi = True  # scale pixel values of the NDI images?
    heralickNDI = True  # output heralick for ndvi images?
    rootpath = "D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/code/testdata/"
    inputimage = scaledout = rootpath + "raster.tif"

    heralickimagedict={}
    # starting default parameters; min/max/offset will be calculated inside the function
    heralickimagedict[0] = ["otbcli_HaralickTextureExtraction.bat", "-in", scaledout,
                  "-channel", "1",
                  "-texture", "simple", #change this for the texture type
                  "-parameters.min", "0", "-parameters.max", "255",
                  "-out", '']
    # set the angle (0, 45, 90, 135)
    heralickimagedict[1] = [(0, 1), (1, 1), (1, 0), (1, -1)]

    heralickNDIdict={}
            # some default parameters
    heralickNDIdict[0] = ["otbcli_HaralickTextureExtraction.bat", "-in", '',
                  "-channel", "1",
                  "-texture", "simple",  #change this for the texture type
                  "-parameters.min", "0", "-parameters.max", "255",
                  "-out", '']  # ,"-ram", '10000']
    # set the angle (0, 45, 90, 135)
    heralickNDIdict[1] = [(0, 1), (1, 1), (1, 0), (1, -1)]


    workflow(rootpath, inputimage, scaleimage, True, heralickimage,rootpath + "haralick", scalendi, heralickNDI, heralickimagedict, heralickNDIdict,herabands=8,debug=debug)