# -*- coding: utf-8 -*-

import csv
import collections

def get_structure(filepath):
    ''' this function will read the structure of google engine files
    the fist row contains the raster names
    the second row contains many fields for each raster
    :param filepath: path to the csv file
    :return: on ordered dictionary  raster_name: field_count
    '''

    f = open (filepath)
    reader = csv.reader(f)

    first=next(reader)
    #print(len(first))

    uniquefirst=list(set(first))
    #print(len(uniquefirst))

    #sets are not ordered therefore I used the code below to get a unique list
    uniquefirst = []
    [uniquefirst.append(item) for item in first if item not in uniquefirst]
    #print(len(uniquefirst)

    #second=next(reader)
    #print(len(second)))

    #count how many columns for each first row fields
    fieldcount = [first.count(uniquefirst[i]) for i in range(len(uniquefirst))]

    #create a dictionary -> fist_row_name: column_counts
    tablestructure = collections.OrderedDict(zip(uniquefirst, fieldcount))

    images = list(tablestructure.keys())
    prefix = []
    [prefix.append(i.split('_')[0]) for i in images if i.split('_')[0] not in prefix ]


    return tablestructure


print(get_structure("data/train_kernel_1_v4.csv"))


def filter_by_row(filepath, outputfile, rows_by_class):
    ''' decrease the size of the file, for each class take no more than rows_by_class rows
    if the class has less rows than rows_by_class output a warning text file
    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param rows_by_class: the max number of returned rows for each class
    :return: the filtered csv file; the first 2 rows are kept
    '''
    pass

def filter_by_column(filepath, outputfile, image_filter, field_filter):
    '''

    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param image_filter: list of images names? pass ['*'] for all images
    :param field_filter:

    :return:
    '''
    pass