# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        main.py
# Purpose:
#
# Author:      claudio piccinini
#
# Created:     11/09/2015
#-------------------------------------------------------------------------------


# Data preparation in arcgis before using this python scripts
# 1)convert the multiband .til image to a multiband tiff image
# 2)assign 0 as the NoData value and pixel type 16BIt_unsigned
# 3) project shapefile to WGS84_UTM_30N
# 4) add a CLASS field to the shapefile


# import modules

# built-in modules
import os
import math
import sys


# 3rd-party modules
from osgeo import gdal
from osgeo import ogr
import rasterstats
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics

# custom modules
import fileIO
import visualization
import getPixelValues
import tiledClassify
import utility

###########################################################
# HARDCODED VALUES, CHANGE WIH YOUR VALUES!!!

# set working directory
os.chdir("D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/processing")

shapes = r"Mali_field_2014_smoothed_class_prj.shp"

#img = r"raster.tif"
img = r"ENVIraster.tif"
treemask = r"Intensity_mask1.tif"

# shapefile field that contains the classes
fieldname = "CLASS"

# percentage of validation data
percentage = 25

# classified raster name
outname = "classify.tif"

# size of the tiles (columns, rows)
tilesize =(1024,1024)
##########################################################

# mean=True to get the average multiband pixel values inside polygons
# mean=False to get all the multiband pixel values inside polygons
MEAN = False

##########################################################

ogr.UseExceptions()
gdal.UseExceptions()


# prepare supervised data and output it to the skll folder
if MEAN:
    data, uniqueLabels, columnNames = getPixelValues.getMeanPixelValues(shapes, img, fieldname, nodatavalue=-999.0,combinations=[])
    # output data to skll folder, we don't export the polygonID
    np.savetxt("dataMeanComb.tsv", data[:, 1:], fmt="%.4f", delimiter="\t", header="".join(columnNames[1:]),comments="")

else:

    data, uniqueLabels,columnNames,subsetcollection = getPixelValues.getSinglePixelValues(shapes, img, fieldname,rastermask=treemask,combinations='*',subset=10, returnsubset=True)

    #output data to skll, we don't export the polygonID   |rowid,band1, band2,..., 1-2, 1-3,....,label|
    # the first row will contain the field names
    np.savetxt('ENVIdataPixelsComb.tsv', data[:,1:], fmt='%.4f', delimiter='\t', header= ''.join(columnNames[1:]), comments='')

    #############   BORUTA  #####################
    # there is no header the field names  |band1, band2,..., 1-2, 1-3,....|
    #np.savetxt('dataPixelsCombX.csv', data[:,2:-1], fmt='%.4f', delimiter=',')
    np.savetxt('ENVIdataPixelsCombX.csv', data[:,2:-1], fmt='%.4f', delimiter=',')
    # there is no header with the field names  |polyID, rowid,band1, band2,..., 1-2, 1-3,....|
    #np.savetxt('dataPixelsCombX+IDS.csv', data[:,:-1], fmt='%.4f', delimiter=',')
    np.savetxt('ENVIdataPixelsCombX+IDS.csv', data[:,:-1], fmt='%.4f', delimiter=',')
    # there is no header with the field names  |label|
    #np.savetxt('dataPixelsCombY.csv', data[:,-1:], fmt='%.1f', delimiter=',')
    np.savetxt('ENVIdataPixelsCombY.csv', data[:,-1:], fmt='%.1f', delimiter=',')

    ############    SKLL    ####################
    # |rowid,band1, band2,,....,label|
    #np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\dataPixelsCombXA.tsv', np.hstack((data[:,1:10],data[:,-1:])), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:10]+columnNames[-1:]), comments='')
    np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\ENVIdataPixelsCombXA.tsv', np.hstack((data[:,1:10],data[:,-1:])), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:10]+columnNames[-1:]), comments='')

    # |rowid,1-2, 1-3,....,label|
    #np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\dataPixelsCombXB.tsv', np.hstack((data[:,1:2],data[:,10:] )), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:2]+columnNames[10:]), comments='')
    np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\ENVIdataPixelsCombXB.tsv', np.hstack((data[:,1:2],data[:,10:] )), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:2]+columnNames[10:]), comments='')

    # |rowid,image1, image2,....,label|  ; in this case we have the heralick images
    data, uniqueLabels, columnNames = getPixelValues.getGeneralSinglePixelValues(shapes, "D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/processing/image", fieldname, inimgfrmt = ['.tif'], rastermask=treemask, subset=subsetcollection, returnsubset = False)
    np.savetxt('D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/processing/Skll/stars/train+dev/dataPixelsCombXC.tsv', data[:,1:],fmt='%.6f',delimiter='\t',header=''.join(columnNames[1:]),comments='')

    # |rowid,image1, image2,....,label|  ; in this case we have the ndvi heralick images
    data, uniqueLabels, columnNames = getPixelValues.getGeneralSinglePixelValues(shapes, "D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/processing/haralik/NDI", fieldname, inimgfrmt = ['.tif'], rastermask=treemask, subset=subsetcollection, returnsubset = False)
    np.savetxt('D:/ITC/courseMaterial/module13GFM2/2015/code/STARS/processing/Skll/stars/train+dev/dataPixelsCombXD.tsv', data[:,1:], fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:]), comments='')

    ############    NDV charting    ##################
    # save NDVI table (band 7 is NIR, band 5 is R)
    # |polygonID, NDVI, labelcode| ; then use the table with the chartNDI.py script
    data, uniqueLabels,columnNames = getPixelValues.getSinglePixelValues(shapes, img, fieldname,rastermask=treemask,combinations=[(7,5)],subset=None, returnsubset = False)
    np.savetxt("NDVI.csv", np.hstack((data[:,0:1], data[:, -2:])), fmt='%.4f', delimiter=',')

#### EXIT THE SCRIPT#####################################
sys.exit(1)
##########################################################

#split into training and validation data
trainingSamples,trainingLabels,validationSamples,validationLabels, k = utility.shuffle_data(data, percentage)

# redo the shuffldata[:,-1:]ing if not all the labels are not represented in the training samples
dataOK = False
while not dataOK:
    for i in uniqueLabels:
        if i not in trainingLabels:
            trainingSamples,trainingLabels,validationSamples,validationLabels, k = utility.shuffle_data(data, percentage)
            break  # reshuffle,go out of the for loop, and check again the data
    dataOK = True

# train classifier
trainingLabels = trainingLabels.reshape(k,)

# initialize RandomForestClassifier class and call the fit method
print("training classifier, please wait....")
rf = RandomForestClassifier(n_estimators=20, n_jobs=-1)
rf.fit(trainingSamples, trainingLabels)


# predict labels using samples
y_predrf = rf.predict(validationSamples)

print("check random forest classification...")

# plot confusion matrix
count = data.shape[0]
validationLabels = validationLabels.reshape(count-k,)
cm = visualization.plotconfusionmatrix(validationLabels, y_predrf)

# calculate accuracy
accuracy, userAccuracy,producerAccuracy = visualization.getAccuracy(cm)
print("The overral accuracy is ",end="")
print(accuracy)
print("The user accuracy is ",end="")
print(userAccuracy)
print("The producer accuracy is ",end="")
print(producerAccuracy)
print()

print(metrics.classification_report(validationLabels,y_predrf))

print("Bands importances...")
importances=rf.feature_importances_
print(importances)

indices = np.argsort(importances)[::-1]
plt.figure()
plt.title("Band importances")
plt.bar(range(indices.shape[0]), importances[indices], color="b", align="center")
plt.xticks(range(indices.shape[0]), indices)
plt.xlim([-1, indices.shape[0]])
plt.show()

# print the charts
if MEAN:
    for i in range(len(uniqueLabels)):
        plt.subplot(math.floor(len(uniqueLabels)/2), len(uniqueLabels) - math.floor(len(uniqueLabels)/2), i+1)
        plt.plot(np.arange(1, data.shape[1]), trainingSamples[trainingLabels == i+1, :].T)
    plt.show()



# classify image using tiles
tiledClassify.tiledClassification( img,rf, tilesize = tilesize, outname=outname)