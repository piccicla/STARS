# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        chartNDVI.py
# Purpose:     output histograms and boxplots for ndi data
#
# Author:      Claudio Piccinini
#
# Created:     19-01-2016
# -------------------------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

# mapping shapefile field code
classes = {1: 'COTTON', 2: 'MAIZE', 3: 'MILLET', 4: 'PEANUT', 5: 'SORGHUM'}


def out_histo(data, path, frmt = ".jpg", nbins = 100):
    """ output histogram for each polygon
    :param data: a 2D numpy array with 3 columns |polygonID, NDI, labelcode|
    :param path: output path
    :param frmt: output format
    :param nbins: the number of bins fr the histogram
    :return: None
    """

    # get the unique  polygonIDs
    polyID = np.unique(data[:,0]).flatten()
    for id in polyID:
        # print(id)
        # filter by polyID and get the class for this polygon
        thisdata = data[data[:, 0] == id, 1]
        thisclass = (classes[np.unique(data[data[:, 0] == id, 2])[0]])
        # print(thisdata, end = '\n')

        print("output histogram for "+str(id) + ":" + thisclass)

        plt.clf() # clean the current figure

        # matplotlib.pyplot.hist(x, bins=10, range=None, normed=False, weights=None, cumulative=False, bottom=None,
        # histtype='bar', align='mid', orientation='vertical', rwidth=None, log=False, color=None, label=None,
        # stacked=False, hold=None, data=None, **kwargs)
        plt.hist(thisdata, bins=nbins)
        plt.xlabel('polyID ' + str(id) + ": "+ thisclass)
        plt.ylabel('Frequency')
        plt.savefig(path + str(id) + "_" + thisclass + frmt)


def out_boxplot(data, path, frmt=".jpg"):
    """
    output a boxplot for each class
    :param data: a 2D numpy array with 3 columns |polygonID, NDI, labelcode|
    :param path: output path
    :param frmt: output format
    :return: None
    """

    # define a mapping where key is the class code and value an empty list
    clt = {i: [] for i in classes.keys()}

    # get the unique classes
    cls = np.unique(data[:,2]).flatten()
    # get the unique  polygonID
    polyID = np.unique(data[:,0]).flatten()

    # for each polygon:
    for id in polyID:

        # print(id)
        thisdata = data[ data[:,0] == id ,-2:]  # this contains ndvi and label for this polygon
        clt[thisdata[0,1]].append( thisdata[:,0].flatten()) # append NDI collection for this polygon to the correct type

    # output a boxplot for each class
    for i in clt:
        print("output boxplot for " + classes[i] )

        plt.clf() #clean the current figure

        # matplotlib.pyplot.boxplot(x, notch=None, sym=None, vert=None, whis=None, positions=None, widths=None,
        # patch_artist=None, bootstrap=None, usermedians=None, conf_intervals=None, meanline=None, showmeans=None,
        # showcaps=None, showbox=None, showfliers=None, boxprops=None, labels=None, flierprops=None, medianprops=None,
        # meanprops=None, capprops=None, whiskerprops=None, manage_xticks=True, hold=None, data=None)

        plt.boxplot(clt[i])
        plt.xlabel(classes[i])
        plt.ylabel("NDI")
        plt.savefig(path + classes[i] + frmt)

if __name__ == "__main__":

    pth = r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing" #set root path
    # open the text file with the data as a np array
    with open(pth + r"\NDVI.csv") as f:
        dta = np.loadtxt(f, delimiter=",")  # columns = |polygonID, NDI, labelcode|
    # output charts
    out_histo(dta, pth+"/NDVIcharts/histo/")
    out_boxplot(dta, pth+"/NDVIcharts/boxplot/")