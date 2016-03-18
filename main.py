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


import settings
###########################################################
# Get values from the settings file
xxx = settings.parse_ini()

setng={}


setng['working_directory'] = working_directory = xxx["working_directory"]
#os.chdir(settings.working_directory)

####setng['shapes'] = shapes = settings.shapes
#img = r"raster.tif"
####setng['img'] = img = settings.image
#####setng['treemask'] = treemask = settings.tree_mask

# mean=True to get the average multiband pixel values inside polygons
# mean=False to get all the multiband pixel values inside polygons
setng['MEAN'] = MEAN = xxx["mean"]
setng['nodatavalue'] = nodatavalue = eval(xxx["nodatavalue"])

band_combinations = xxx["band_combinations"]
if band_combinations != '*':
    exec(band_combinations)
setng['band_combinations'] = band_combinations
setng['pixel_subset'] = pixel_subset = xxx["pixel_subset"]
setng['NDI_chart_combinations'] = NDI_chart_combinations = eval(xxx["NDI_chart_combinations"])

setng['hara_dir'] = hara_dir = xxx["hara_dir"]
setng['haralick_format'] = haralick_format = eval(xxx["haralick_format"])
setng['haralick_image_type'] = haralick_image_type =  eval(xxx["haralick_image_type"])
setng['hara_ndi_dir'] = hara_ndi_dir = xxx["hara_ndi_dir"]
setng['haralick_ndi_format'] = haralick_ndi_format =  eval(xxx["haralick_ndi_format"])
setng['heralick_ndi_type'] = haralick_ndi_type =  eval(xxx["haralick_ndi_type"])

setng['skll_dir'] = skll_dir = xxx["skll_dir"]
setng['boruta_dir'] = boruta_dir = xxx["boruta_dir"]

# shapefile field that contains the classes
setng['fieldname'] = fieldname = xxx["field_name"]

# percentage of validation data
setng['percentage'] = percentage = xxx["validation_data"]

# classified raster name
setng['outname'] = outname = xxx["out_name"]

# size of the tiles (columns, rows)
setng['tilesize'] = tilesize =xxx["tile_size"]

#use ipyparallel
setng['parallelize'] = parallelize = xxx["parallelize"]
setng['engine_messages'] = engine_messages = xxx["engine_messages"]
setng["max_processes"] = max_processes = xxx["max_processes"]

paths = settings.parse_json()

# import modules

# built-in modules
import os
#import math
import sys
import time


#import matplotlib.pyplot as plt
#from sklearn.ensemble import RandomForestClassifier
#from sklearn import metrics

# 3rd-party modules
#import numpy as np

# custom modules
#import fileIO
#import visualization
#import getPixelValues
#import tiledClassify
#import utility


#########################


def preparedata(imagetag):

    import os
    import numpy as np
    import getPixelValues


    d = paths[imagetag]

    ####return(d['content'][0]['shape'], d['content'][0]['raster'], fieldname,d['content'][0]['mask'],band_combinations,pixel_subset)

    ##os.chdir(working_directory)

    # prepare supervised data and output it to the skll folder
    if MEAN:
        #first we go to the directory that stores the images
        os.chdir(d['basepath'])

        #for the same image we can have different shapes and masks
        for n, comb in enumerate(d['content']):

            data, uniqueLabels, columnNames = getPixelValues.getMeanPixelValues(comb['shape'], comb['raster'], fieldname, nodatavalue=nodatavalue, combinations=band_combinations)
            # output data to skll folder, we don't export the polygonID

            if not os.path.exists(skll_dir+"/"+d['name']):
                os.mkdir(skll_dir+"/"+d['name'])

            np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n)+ "_dataMeanComb.tsv", data[:, 1:], fmt="%.4f", delimiter="\t", header="".join(columnNames[1:]),comments="")

        return True

    else:


        #first we go to the directory that stores the images
        os.chdir(d['basepath'])

        #for the same image we can have different shapes and masks
        for n, comb in enumerate(d['content']):

            data, uniqueLabels,columnNames,subsetcollection = getPixelValues.getSinglePixelValues(comb['shape'], comb['raster'], fieldname,rastermask=comb['mask'],combinations=band_combinations,subset=pixel_subset, returnsubset=True)

            if not os.path.exists(skll_dir+"/"+d['name']):
                os.mkdir(skll_dir+"/" + d['name'])


            #output data to skll, we don't export the polygonID   |rowid,band1, band2,..., 1-2, 1-3,....,label|
            # the first row will contain the field names
            np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n) + '_dataPixelsComb.tsv', data[:,1:], fmt='%.4f', delimiter='\t', header= ''.join(columnNames[1:]), comments='')

            #############   BORUTA  #####################

            if not os.path.exists(boruta_dir+"/"+d['name']):
                os.mkdir(boruta_dir+"/" + d['name'])

            # there is no header the field names  |band1, band2,..., 1-2, 1-3,....|
            #np.savetxt('dataPixelsCombX.csv', data[:,2:-1], fmt='%.4f', delimiter=',')
            np.savetxt(boruta_dir+"/" + d['name'] + str(n) + '_dataPixelsCombX.csv', data[:,2:-1], fmt='%.4f', delimiter=',')
            # there is no header with the field names  |polyID, rowid,band1, band2,..., 1-2, 1-3,....|
            #np.savetxt('dataPixelsCombX+IDS.csv', data[:,:-1], fmt='%.4f', delimiter=',')
            np.savetxt(boruta_dir+"/" + d['name'] + str(n) + '_dataPixelsCombX+IDS.csv', data[:,:-1], fmt='%.4f', delimiter=',')
            # there is no header with the field names  |label|
            #np.savetxt('dataPixelsCombY.csv', data[:,-1:], fmt='%.1f', delimiter=',')
            np.savetxt(boruta_dir+"/" + d['name'] + str(n) + '_dataPixelsCombY.csv', data[:,-1:], fmt='%.1f', delimiter=',')

            ############    SKLL    ####################
            # |rowid,band1, band2,,....,label|
            #np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\dataPixelsCombXA.tsv', np.hstack((data[:,1:10],data[:,-1:])), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:10]+columnNames[-1:]), comments='')
            np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n)+"_dataPixelsCombXA.tsv", np.hstack((data[:,1:10],data[:,-1:])), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:10]+columnNames[-1:]), comments='')

            # |rowid,1-2, 1-3,....,label|
            #np.savetxt(r'D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\Skll\stars\train+dev\dataPixelsCombXB.tsv', np.hstack((data[:,1:2],data[:,10:] )), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:2]+columnNames[10:]), comments='')
            np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n)+"_dataPixelsCombXB.tsv", np.hstack((data[:,1:2],data[:,10:] )), fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:2]+columnNames[10:]), comments='')


            # haralick can be simple, advanced, higher
            for type in d['haralick_images']:
                t = d['haralick_images'][type]
                if not t: continue
                # |rowid,image1, image2,....,label|  ; in this case we have the heralick images
                data, uniqueLabels, columnNames = getPixelValues.getGeneralSinglePixelValues(comb['shape'], t["basepath"], fieldname, t["images"], rastermask=comb['mask'], subset=subsetcollection, returnsubset = False)
                np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n)+ "_"+ type+"_PixelsCombXC.tsv", data[:,1:],fmt='%.6f',delimiter='\t',header=''.join(columnNames[1:]),comments='')

            # haralick can be simple, advanced, higher
            for type in d['haralick_ndi']:
                t = d['haralick_ndi'][type]
                if not t: continue
                # |rowid,image1, image2,....,label|  ; in this case we have the ndvi heralick images
                data, uniqueLabels, columnNames = getPixelValues.getGeneralSinglePixelValues(comb['shape'], t["basepath"], fieldname, t["images"], rastermask=comb['mask'], subset=subsetcollection, returnsubset = False)
                np.savetxt(skll_dir+"/"+d['name'] + "/" + str(n)+ "_"+ type+ "_PixelsCombXD.tsv", data[:,1:], fmt='%.6f', delimiter='\t',header= ''.join(columnNames[1:]), comments='')

            ############    NDV charting    ##################
            # save NDVI table (band 7 is NIR, band 5 is R)
            # |polygonID, NDVI, labelcode| ; then use the table with the chartNDI.py script
            data, uniqueLabels,columnNames = getPixelValues.getSinglePixelValues(comb['shape'], comb['raster'], fieldname,rastermask=comb['mask'],combinations=NDI_chart_combinations,subset=None, returnsubset = False)
            np.savetxt( str(n)+"_NDVI.csv", np.hstack((data[:,0:1], data[:, -2:])), fmt='%.4f', delimiter=',')

        return True

###########################

def wait_watching_stdout(ar, dt=0.1, truncate=500):
    while not ar.ready():
        stdouts = ar.stdout
        #print(ar.stdout)
        if not stdouts:
            continue
        print('-' * 30)
        print ("%.3fs elapsed" % ar.elapsed)
        print ("")
        for stdout in stdouts:
            if stdout:
                print("processing OK")
                #print ("[ stdout %s ]" %  stdout[-truncate:])
        sys.stdout.flush()
        time.sleep(dt)
    else:
        #print complete messages
        stdouts = ar.stdout
        for stdout in stdouts:
            if stdout:
                print ("[ stdout %s ]" %  stdout[-truncate:])
        sys.stdout.flush()
        print(ar.get())
        print("finished!")

if parallelize:
    T0 = time.perf_counter()
    from ipyparallel import Client
    call = True
    while call:
        try:
            print('waiting for ipcluster connection....')
            client = Client(timeout=20)
        except Exception as e:
            print(e)
            print('waiting other 5 seconds for ipcluster connection....')
            time.sleep(5)
        else:
            print(client.ids)
            if not client.ids:
                print('nearly there, waiting 20 seconds for ipcluster connection....')
                time.sleep(20)
            if client.ids:
                call = False
    print("there are ", len(client.ids), "clients available")
    print("we want to use up to",max_processes , "processes")

    if max_processes < len(client.ids):
        #creating a direct view
        dview = client[:max_processes]
    else:
        dview = client[:]
    dview = client[:]
    #pushing configurations to the workers
    for k in setng:
        dview[k]=setng[k]

    #updating the sys.path, this is necessary, this is necessary for the engines to find the custom modules
    mydir = os.path.dirname(os.path.abspath(__file__))
    dview["mydir"]=mydir
    dview["paths"]=paths
    dview.execute("import sys")
    dview.execute("sys.path.append(mydir)")

    #calling a function asyncronously on all engines, each image in paths is assigned to one engine

    ar = dview.map_async(preparedata, list(paths.keys()))
    #ar = dview.map_async(preparedata, [0,0])

    #do we want the engine stdout
    if engine_messages:
        wait_watching_stdout(ar)
    else:
        ar.wait()
        print(ar.get())
        print("finished!")

    T1 = time.perf_counter()
    print("parallel elapsed: ",(T1 - T0)*1000)

    #dview.execute('sys.exit()')

else:
    T0 = time.perf_counter()
    for i in  list(paths.keys()):
    ####for i in  [0]:
        preparedata(i)
    T1 = time.perf_counter()
    print("sequential elapsed: ",(T1 - T0)*1000)

#### FOR NOW EXIT THE SCRIPT#####################################
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
tiledClassify.tiledClassification( img,rf, tilesize = (tilesize,tilesize), outname=outname)