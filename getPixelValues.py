# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        getPixelValues.py
# Purpose:
#
# Author:      claudio piccinini
#
# Created:     11/09/2015
#-------------------------------------------------------------------------------

import math
import os

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo import gdalconst
import rasterstats
import numpy as np

import utility

ogr.UseExceptions()
gdal.UseExceptions()

def getSinglePixelValues(shapes, inraster, fieldname, bandcombination=True, combinations=[]):
    """intersect polygons/multipolygons with multiband rasters

        polygons and raster must have the same coordinate system!!!

    :param shapes: polygons/multipolygons shapefile
    :param inraster: multiband raster
    :param fieldname: vector fieldname that contains the labelvalue
    :param bandcombination: bandcombination : if true the result will contain columns with the normalized difference index
           ndi = (bandj) - (bandi)/(bandj) + (bandi)
    :param combinations: combinations: a list of tuples , each tuple with 2 band numbers for which we want to
    calculate the NDI [(1,2), (3,4), .....]; if empty list we take all the combinations
    :return: 1) a 2d numpy array
            --if bandcombination was False: each row contains the polygonID column, the unique id column, the apixel
                   values for each raster band plus a column with the label:
                   the array shape is (numberpixels, nbands + 3)
            --if bandcombination was True: each row contains the polygonID column, the unique id column, the pixel
                   values for each raster band, the NDI bands, plus a column with the label:
                   if conbination is empty we get all the combinations
                   the array shape is (numberpixels, nbands + number of band combinations +3)
            2) a set with the unique labels
            3) a list with column names
    """

    raster = None
    shp = None
    lyr = None
    target_ds = None
    outDataSet = None
    outLayer = None
    outdata = []

    try:

        # Open data
        raster = gdal.Open(inraster)
        shp = ogr.Open(shapes)
        lyr = shp.GetLayer()

        sourceSR = lyr.GetSpatialRef()

        # get number of features; get number of bands
        featureCount = lyr.GetFeatureCount()
        nbands = raster.RasterCount

        # iterate features and extract unique labels
        classValues = []
        for feature in lyr:
            classValues.append(feature.GetField(fieldname))
        # get the classes unique values and reset the iterator
        uniqueLabels = set(classValues)
        lyr.ResetReading()

        # Get raster georeference info
        transform = raster.GetGeoTransform()
        xOrigin = transform[0]
        yOrigin = transform[3]
        pixelWidth = transform[1]
        pixelHeight = transform[5]

        numfeature = 0

        # keep trak of the number of ids, necessary to assign id to subsequent polygons
        idcounter=1

        # if we want the normalized indexes we need to add additional columns to the outputdata
        if bandcombination:
            # get the number of combinations and the column names
            numberCombinations, comb_column_names = utility.combination_count(nbands)

            #combination_count() will return all the combination, but pixel value of  ndi A/B is just the inverse of ndi 2/1;
            # therefore we get only the first half of the combinations
            numberCombinations = numberCombinations/2
            comb_column_names = comb_column_names[0: int(numberCombinations)]

        for feat in lyr:

            numfeature +=1
            print ("working on feature %d of %d"%(numfeature,featureCount))

            # get the label and the polygon ID
            label = feat.GetField(fieldname)
            polygonID = feat.GetFID() + 1  # I add one to avoid the first polygonID==0

            # Get extent of feature
            geom = feat.GetGeometryRef()
            if geom.GetGeometryName() == "MULTIPOLYGON":
                count = 0
                pointsX = []
                pointsY = []
                for polygon in geom:
                    geomInner = geom.GetGeometryRef(count)
                    ring = geomInner.GetGeometryRef(0)
                    numpoints = ring.GetPointCount()
                    for p in range(numpoints):
                            lon, lat, z = ring.GetPoint(p)
                            pointsX.append(lon)
                            pointsY.append(lat)
                    count += 1
            elif geom.GetGeometryName() == "POLYGON":
                ring = geom.GetGeometryRef(0)
                numpoints = ring.GetPointCount()
                pointsX = []; pointsY = []
                for p in range(numpoints):
                        lon, lat, z = ring.GetPoint(p)
                        pointsX.append(lon)
                        pointsY.append(lat)

            else:
                raise Exception("ERROR: Geometry needs to be either Polygon or Multipolygon")

            xmin = min(pointsX)
            xmax = max(pointsX)
            ymin = min(pointsY)
            ymax = max(pointsY)

            # Specify offset and rows and columns to read
            xoff = int((xmin - xOrigin)/pixelWidth)
            yoff = int((yOrigin - ymax)/pixelWidth)
            xcount = int((xmax - xmin)/pixelWidth)+1
            ycount = int((ymax - ymin)/pixelWidth)+1

            # Create memory target multiband raster
            target_ds = gdal.GetDriverByName("MEM").Create('', xcount, ycount, nbands, gdalconst.GDT_UInt16)
            target_ds.SetGeoTransform((
                xmin, pixelWidth, 0,
                ymax, 0, pixelHeight,
            ))

            # Create for target raster the same projection as for the value raster
            raster_srs = osr.SpatialReference()
            raster_srs.ImportFromWkt(raster.GetProjectionRef())
            target_ds.SetProjection(raster_srs.ExportToWkt())

            # create in memory vector layer that contains the feature
            drv = ogr.GetDriverByName("ESRI Shapefile")
            outDataSet = drv.CreateDataSource("/vsimem/memory.shp")
            outLayer = outDataSet.CreateLayer("memoryshp", srs=sourceSR, geom_type=lyr.GetGeomType())

            # set the output layer's feature definition
            outLayerDefn = lyr.GetLayerDefn()
            # create a new feature
            outFeature = ogr.Feature(outLayerDefn)
            # set the geometry and attribute
            outFeature.SetGeometry(geom)
            # add the feature to the shapefile
            outLayer.CreateFeature(outFeature)

            # Rasterize zone polygon to raster
            # outputraster, list of bands to update, input layer, list of values to burn
            gdal.RasterizeLayer(target_ds, list(range(1, nbands+1)), outLayer, burn_values=[label]*nbands)

            # Read rasters as arrays
            dataraster = raster.ReadAsArray(xoff, yoff, xcount, ycount).astype(np.float)
            datamask = target_ds.ReadAsArray(0, 0, xcount, ycount).astype(np.float)

            # extract the data for each band
            data = []
            for i in range(nbands):
                data.append(dataraster[i][datamask[i]>0])

            # define label data for this polygon
            label = (np.zeros(data[0].shape[0]) + label).reshape(data[0].shape[0],1)
            polygonID = (np.zeros(data[0].shape[0]) + polygonID).reshape(data[0].shape[0],1)

            id = np.arange(idcounter,(data[0].shape[0])+idcounter ).reshape(data[0].shape[0],1) # +1 is there to avoid first polygon different from 0

            # update the starting id for the next polygon
            idcounter += data[0].shape[0]

            vstackdata = np.vstack(data).T

            if bandcombination and not combinations:
                # multi band samples and labels : shape -> num.pixels * (8 bands+ all number of band combinations + 3)
                outdata.append(np.hstack((polygonID, id,  np.hstack((vstackdata, np.zeros((vstackdata.shape[0],numberCombinations)))),label)))

            elif bandcombination and combinations:
                # multi band samples and labels : shape -> num.pixels * (8 bands+ custom band combinations + 3)
                outdata.append(np.hstack((polygonID, id,  np.hstack((vstackdata, np.zeros((vstackdata.shape[0],len(combinations))))),label)))
            else:
                # multi band samples and labels : shape -> num.pixels * (8 bands+3)
                outdata.append(np.hstack((polygonID, id,  vstackdata, label)))

            # Mask zone of raster
            #zoneraster = np.ma.masked_array(dataraster,  np.logical_not(datamask))
            # Calculate statistics of zonal raster
            #return np.average(zoneraster),np.mean(zoneraster),np.median(zoneraster),np.std(zoneraster),np.var(zoneraster)

            # give control back to c++ to free memory
            target_ds = None
            outLayer = None
            outDataSet = None

        # id = np.arange(1,(data[0].shape[0])+1).reshape(data[0].shape[0],1)

        # define the output data
        outdata = np.vstack(outdata)

        # store the field names
        columnNames = ["polyID\t", "id\t"]
        for i in range(nbands):
            columnNames.append("band" + str(i+1)+"\t")
        # if we want the normalized indexes we need additional columns to the outputdata
        if bandcombination and not combinations:  #this is when we want all the combinations

            columnNames += utility.column_names_to_string(comb_column_names)

            # calculate the NDI for all the band combinations
            print("calculating NDI for "+str(numberCombinations) + " columns, it will take some time")
            for i in comb_column_names:
                #get column index  ->  i[0]-i[1]/i[0]+i[1]

                #which column we want to update? # the 2 is there because the first 2 columns are the polygonid/id
                idx = comb_column_names.index(i)+ nbands + 2
                #calculate index  # the +1 is there because the first two columns are polyid and id
                outdata[:, idx] = (outdata[:, i[0]+1] - outdata[:, i[1]+1]) / (outdata[:, i[0]+1] + outdata[:, i[1]+1])
                print(".", end="")
            print()

        elif bandcombination and combinations: # this is when we want specific combination using the combination parameter

            columnNames += utility.column_names_to_string(combinations)

            # calculate the NDI for all the band combinations
            print("calculating NDI for "+str(len(combinations)) + " columns, it will take some time")
            for i in combinations:
                # get column index  ->  i[0]-i[1]/i[0]+i[1]

                # which column we want to update? # the 2 is there because the first 2 columns are the polygonid/id
                idx = combinations.index(i)+ nbands + 2
                # calculate index  # the +1 is there because the first two columns are polyid and id
                outdata[:,idx] = (outdata[:, i[0]+1] - outdata[:, i[1]+1]) / (outdata[:, i[0]+1] + outdata[:, i[1]+1])
                print(".", end="")
            print()

        columnNames.append("label")
        return (outdata, uniqueLabels, columnNames)

    finally:

        #give control back to c++ to free memory
        if raster: raster = None
        if shp: shp = None
        if lyr: lyr = None
        if target_ds: target_ds = None
        if outLayer: outLayer = None
        if outDataSet: outDataSet = None


def getGeneralSinglePixelValues(shapes, folderpath, fieldname, inimgfrmt = ['.tif']):
    """ general function to intersect polygons/multipolygons with a group of multiband rasters
        IMPORTANT
        polygons and raster must have the same coordinate system!!!
        the bands of a raster must have the same data type
    :param shapes: polygons/multipolygons shapefile
    :param folderpath: folder with multiband rasters
    :param fieldname: vector fieldname that contains the labelvalue
    :param inimgfrmt: a list of image formats necessary to filter the input folder content (default is tif format)
    :return: - a 2d numpy array,
                each row contains the polygonID column, the unique id column, the pixel
                values for each raster band plus a column with the label:
                the array shape is (numberpixels, numberofrasters*nbands + 3)
             - a set with the unique labels
             - a list with column names
    """

    raster = None     
    shp = None        
    lyr = None     
    target_ds = None  
    outDataSet = None 
    outLayer = None  
    band = None

    outdata = []
    
    try:

        shp = ogr.Open(shapes)
        lyr = shp.GetLayer()

        sourceSR = lyr.GetSpatialRef()

        # get number of features; get number of bands
        featureCount = lyr.GetFeatureCount()

        # iterate features and extract unique labels
        classValues = []
        for feature in lyr:
            classValues.append(feature.GetField(fieldname))
        # get the classes unique values
        uniqueLabels = set(classValues)

        # get the content of the images directory
        imgs= os.listdir(folderpath)

        imgcounter = 0  #keep track of the image number
        label = None
        columnNames = []
        labels = []  #this will store all the labels

        # iterate all the images
        for i in imgs:
            # filter content, we want files with the correct extension
            if os.path.isfile(folderpath+'/'+i) and (os.path.splitext(folderpath+'/'+i)[-1] in inimgfrmt) :
                # increase the image counter and open raster data
                imgcounter += 1
                raster = gdal.Open(folderpath+'/'+i)
                nbands = raster.RasterCount

                # we need to get the raster datatype for later use (assumption:every band has the same data type)
                band = raster.GetRasterBand(1)
                raster_data_type = band.DataType

                # Get raster georeference info
                transform = raster.GetGeoTransform()
                xOrigin = transform[0]
                yOrigin = transform[3]
                pixelWidth = transform[1]
                pixelHeight = transform[5]

                numfeature = 0

                # keep trak of the number of ids, necessary to assign id to subsequent polygons
                idcounter = 1

                # reset the iterator
                lyr.ResetReading()

                intermediatedata = []

                for feat in lyr:

                    numfeature += 1
                    print("working on feature %d of %d, raster %s" % (numfeature, featureCount, i))

                    #get the label and the polygon ID
                    label = feat.GetField(fieldname)
                    polygonID = feat.GetFID() + 1  #I add one to avoid the first polygonID==0

                    #  Get extent of feature
                    geom = feat.GetGeometryRef()
                    if geom.GetGeometryName() == "MULTIPOLYGON":
                        count = 0
                        pointsX = []; pointsY = []
                        for polygon in geom:
                            geomInner = geom.GetGeometryRef(count)
                            ring = geomInner.GetGeometryRef(0)
                            numpoints = ring.GetPointCount()
                            for p in range(numpoints):
                                lon, lat, z = ring.GetPoint(p)
                                pointsX.append(lon)
                                pointsY.append(lat)
                            count += 1
                    elif geom.GetGeometryName() == "POLYGON":
                        ring = geom.GetGeometryRef(0)
                        numpoints = ring.GetPointCount()
                        pointsX = []
                        pointsY = []
                        for p in range(numpoints):
                            lon, lat, z = ring.GetPoint(p)
                            pointsX.append(lon)
                            pointsY.append(lat)

                    else:
                        raise Exception("ERROR: Geometry needs to be either Polygon or Multipolygon")

                    xmin = min(pointsX)
                    xmax = max(pointsX)
                    ymin = min(pointsY)
                    ymax = max(pointsY)

                    # Specify offset and rows and columns to read
                    xoff = int((xmin - xOrigin)/pixelWidth)
                    yoff = int((yOrigin - ymax)/pixelWidth)
                    xcount = int((xmax - xmin)/pixelWidth)+1
                    ycount = int((ymax - ymin)/pixelWidth)+1

                    # Create memory target multiband raster, with the same nbands and datatype as the input raster
                    target_ds = gdal.GetDriverByName("MEM").Create("", xcount, ycount, nbands, raster_data_type)
                    target_ds.SetGeoTransform((
                        xmin, pixelWidth, 0,
                        ymax, 0, pixelHeight,
                    ))

                    # Create for target raster the same projection as for the value raster
                    raster_srs = osr.SpatialReference()
                    raster_srs.ImportFromWkt(raster.GetProjectionRef())
                    target_ds.SetProjection(raster_srs.ExportToWkt())

                    #create in memory vector layer that contains the feature
                    drv = ogr.GetDriverByName("ESRI Shapefile")
                    outDataSet = drv.CreateDataSource("/vsimem/memory.shp")
                    outLayer = outDataSet.CreateLayer("memoryshp", srs=sourceSR, geom_type=lyr.GetGeomType())

                    # set the output layer's feature definition
                    outLayerDefn = lyr.GetLayerDefn()
                    # create a new feature
                    outFeature = ogr.Feature(outLayerDefn)
                    # set the geometry and attribute
                    outFeature.SetGeometry(geom)
                    # add the feature to the shapefile
                    outLayer.CreateFeature(outFeature)

                    # Rasterize zone polygon to raster
                    # outputraster, list of bands to update, input layer, list of values to burn
                    gdal.RasterizeLayer(target_ds, list(range(1,nbands+1)), outLayer, burn_values=[label]*nbands)

                    # Read rasters as arrays
                    dataraster = raster.ReadAsArray(xoff, yoff, xcount, ycount).astype(np.float)
                    datamask = target_ds.ReadAsArray(0, 0, xcount, ycount).astype(np.float)

                    #extract the data for each band
                    data = []
                    for j in range(nbands):
                        data.append(dataraster[j][datamask[j]>0])

                    if imgcounter == 1:
                        #define label data for this polygon
                        label = (np.zeros(data[0].shape[0]) + label).reshape(data[0].shape[0],1)
                        polygonID = (np.zeros(data[0].shape[0]) + polygonID).reshape(data[0].shape[0],1)
                        # fill in the list with all the labels, this will be the last column in the final output
                        labels.append(label)

                    id = np.arange(idcounter,(data[0].shape[0]) + idcounter).reshape(data[0].shape[0], 1) #+1 is there to avoid first polygon different from 0

                    # update the starting id for the next polygon
                    idcounter += data[0].shape[0]
                    vstackdata = np.vstack(data).T

                    if imgcounter == 1:
                        intermediatedata.append(np.hstack((polygonID, id,  vstackdata)))
                    else:
                        intermediatedata.append(vstackdata)


                    # Mask zone of raster
                    #zoneraster = np.ma.masked_array(dataraster,  np.logical_not(datamask))
                    # Calculate statistics of zonal raster
                    #return np.average(zoneraster),np.mean(zoneraster),np.median(zoneraster),np.std(zoneraster),np.var(zoneraster)

                    #give control back to c++ to free memory
                    target_ds = None
                    outLayer = None
                    outDataSet = None

                #########END for feat in lyr


                #store the field names
                if imgcounter == 1:
                    columnNames += ["polyID\t","id\t"]
                for k in range(nbands):
                    columnNames.append(i + "_b" + str(k+1)+"\t")

                # stack vertically the output of each feature class
                outdata.append (np.vstack(intermediatedata))

        ########## END for i in imgs

        # stack horizontally
        outdata = np.hstack(outdata)
        # finally append the lables at the end
        outdata = np.hstack((outdata, np.vstack(labels)))

        columnNames.append("label")
        return (outdata, uniqueLabels, columnNames)

    finally:

        #give control back to c++ to free memory
        if raster:
            raster = None
        if shp:
            shp = None
        if lyr:
            lyr = None
        if target_ds:
            target_ds = None
        if outLayer:
            outLayer = None
        if outDataSet:
            outDataSet = None
        if band:
            band = None


def getMeanPixelValues(shapes, inraster, fieldname, bandcombination =True):
    """intersect shapefile with multiband rasters

        shapefile and raster must have the same coordinate system!!!

    :param shapes: shapefile
    :param inraster: multiband raster
    :param fieldname: vector fieldname that contains the labelvalue
    :param bandcombination: bandcombination : if true the result will contain columns with the normalized difference index
           ndi = (bandj) - (bandi)/(bandj) + (bandi)
    :return: - a 2d numpy array,
                -if bandcombination was False: each row contains the polygonID column, the unique id column, the average pixel
                values for each raster band plus a column with the label:
                   the array shape is (numberfeatures, nbands + 3)
                -if bandcombination was True: each row contains the polygonID column, the unique id column, the average pixel
                values for each raster band, the NDI bands, plus a column with the label:
                   the array shape is (numberfeatures, nbands + number of band combinations +3)
            - a set with the labels
            - a list with column names
    """

    dataset = None
    layer = None
    try:
        # open image
        # import the NDVI raster and get number of bands
        dataset = gdal.Open(inraster)
        nbands = dataset.RasterCount

        print(nbands)

        dataset = None # destroy dataset

        # use rasterstat to get the average pixel values
        # also collect the polygon IDs
        meanValues = []
        polygonIDs = []

        # store the field names
        columnNames = ["polyID\t", "id\t"]

        for i in range(nbands):
            print("getting mean values for band %d" % (i+1))
            crossing = rasterstats.zonal_stats( shapes, inraster, stats=["mean"], band_num =i+1, geojson_out=True)
            #print (crossing)
            meanValues.append([j["properties"]["mean"] for j in crossing])
            # we get the polygons ID only once because they are the same for the 8 bands
            if i == 0:
                polygonIDs.append([int(j["id"])+1 for j in crossing])
            columnNames.append("band" + str(i+1) + "\t")

        #print(meanValues)

        #create samples as a numpy array

        #define samples
        samples = np.array(meanValues).T

        #if we want the band combinations, add columns to the samples
        if bandcombination:

            #get the number of combinations and the column names
            numberCombinations, combColumnNames = utility.combination_count(nbands)
            #add columns to store th normalized indexes
            samples = np.hstack((samples, np.zeros((samples.shape[0], numberCombinations))))
            #add column names
            columnNames += utility.column_names_to_string(combColumnNames)

            #calculate the NDI for all the band combinations
            print("calculating NDI for " + str(numberCombinations) + " columns")
            for i in combColumnNames:
                #get column index  ->  i[0]-i[1]/i[0]+i[1]
                #which column we want to update?
                idx = combColumnNames.index(i)+ nbands
                #calculate index  # the -1 is there because the numpy array index starts from 0
                samples[:, idx] = (samples[:, i[0]-1] - samples[:, i[1]-1]) / (samples[:, i[0]-1] + samples[:, i[1]-1])
                print(".", end="")
            print()

        columnNames.append("label")

        #define a column with the polygons id
        polygonIDs = np.array(polygonIDs).T
        id = polygonIDs

        #now we define the unique classes
        dataset = ogr.Open(shapes)
        layer = dataset.GetLayer()

        count = layer.GetFeatureCount()
        print("there are %d shapes" % count)

        #iterate features and extract labels
        print("getting feature labels...")
        classValues = []
        for feature in layer:
            classValues.append(feature.GetField(fieldname))
            print(".", end="")
            print()

        #give control back to c++ to free memory
        layer = None
        dataset = None

        #get the labels unique values
        print("filering feature labels...")
        uniqueLabels = set(classValues)

        #create classes as a numpy array
        labels = np.array(classValues).reshape(count, 1)

        return (np.hstack((polygonIDs, id, samples, labels.reshape(count,1))), uniqueLabels, columnNames)

    finally:
        if layer:
            layer = None
        if dataset:
            dataset = None
