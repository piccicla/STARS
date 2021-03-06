# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:
# Purpose:  - filter a google engine file by rows/columns
#
# Author:   claudio piccinini,
#
# Created:     04/07/2016
# -------------------------------------------------------------------------------

import csv
import collections
import os
import random
import numpy as np
import pandas as pd
from sklearn.cross_validation import KFold

#constants for bands, vegetation indexes, texture bands, texture vegetation indexes
TYPES = ['b', 'vi', 'tb', 'tvi']
BANDS = ['b1','b2','b3','b4','b5','b6','b7','b8']
VITYPES = ['DVI', 'NDI','RVI','SAVI','TCARI','EVI','MSAVI2']
VTYPES_NOBAND = ['SAVI', 'TCARI', 'EVI', 'MSAVI2'] #types independent from bands
TEXTYPES = ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']


def get_structure(filepath):
    """ this function will read the structure of google engine files
        -the fist row contains the raster names
        -the second row contains many fields for each raster
    :param filepath: path to the csv file
    :return: an ordered dictionary  {raster_name: field_count} and a set with the unique raster names
    """

    f = open (filepath)
    reader = csv.reader(f)

    first=next(reader)
    #print(len(first))

    #sets are not ordered therefore I used the code below to get a unique list
    uniquefirst = []
    [uniquefirst.append(item) for item in first if item not in uniquefirst]
    #print(len(uniquefirst)

    #second=next(reader)
    #print(len(second)))
    f.close()

    #count how many columns for each first row fields
    fieldcount = [first.count(uniquefirst[i]) for i in range(len(uniquefirst))]

    #create a dictionary -> fist_row_name: column_counts
    tablestructure = collections.OrderedDict(zip(uniquefirst, fieldcount))

    images = list(tablestructure.keys())
    prefix = []
    [prefix.append(i.split('_')[-3]+'_'+i.split('_')[-2]) for i in images if i.split('_')[0] not in prefix ]


    return tablestructure, set(prefix)


def field_names(filepath, outfile=None):
    """
    utility function to return unique field names from the second row
    :param filepath:
    :param outfile: set this if you want to output to a file
    :return: a list of unique fields
    """

    f = open (filepath)
    reader = csv.reader(f)
    next(reader)
    fields = next(reader)
    f.close()

    uniquefields = []
    [uniquefields.append(item) for item in fields if item not in uniquefields]

    if outfile:
        f = open(outfile, 'w')

        for i in uniquefields:
            f.write(i+'      ')

        f.close()

    print('done')

    return uniquefields


def write_filtered_row(inputrow,indexes, csvwriter):
    """utility function to filter a list and write it to csv
    :param inputrow:  the full input list
    :param indexes: the filter indexes
    :param csvwriter: the csv writer
    :return: None
    """

    newline = []
    for i in indexes:
        newline.append(inputrow[i])
    csvwriter.writerow(newline)


def clean_directory(directory, end=None):
    """ delete all the files in a directory, optionally filter the files
    :param directory: working directory
    :param end: the end of the file to filter
    :return: None
    """

    f = os.listdir(directory)
    if end:
        f = [i for i in f if i.endswith(end)]
    for i in f:
        try: #skip locked files
            os.remove(directory+'/'+i)
        except:
            pass


def check_item_count(infile, delimiter=','):
    """ utility function to check if the number of columns in a csv file is always the same
    :param infile:
    :return: True if the number is the same plus min and max values
    """
    f = open(infile)
    reader = csv.reader(f, delimiter= delimiter)
    count = []

    for line in reader:
        count.append(len(line))

    print('min =', str(min(count)), 'max =', str(max(count)))

    return min(count) == max(count), min(count), max(count)


def count_row(file):
    """ count number of rows in a text file
    :param file:
    :return:
    """
    with open(file) as f:
        row_count = sum(1 for row in f)
        print(row_count)
    return row_count


def get_row(file, start, end= None):
    """ read range of lines from a text file

    return a nested list, each sub list is a row as a string ( therefore it contains \n at the end, use string.strip())

    if end is not defined it will read only one row
    end must equal or  greater than start
    start must be positive

    the end in comprised in the result,

    :param file: input text file
    :param start: start index
    :param end: end index
    :return: a nested list, each sub list is a row
    """

    if not end:
        end=start
    if start<0:
        return []
    if end<start:
        return []

    out=[]

    f = open(file)

    n=0

    try:
        for i in range(start):
            next(f)
        for i in range(start, end+1):
            out.append(next(f))

    except StopIteration:
        pass

    finally:
        if f: f.close()
        return out


def skllifier(infile, outfile, indelimiter=',', outdelimiter='\t'):
    """convert a GoogleEngine file to an input skll file
    :param infile: input text file
    :param outfile: output text file
    :param indelimiter: delimiter for the input file
    :param outdelimiter: delimiter for the output file
    :return: None
    """
    f = open(infile)
    rdr = csv.reader(f, delimiter=indelimiter)

    out = open(outfile,'w', newline='')
    wrt= csv.writer(out, delimiter=outdelimiter)

    names=next(rdr) #skip firstrow
    fields = next(rdr)

    for i in range(2, len(names)):
        fields[i] = '_'.join(names[i].split('_')[-3:-1]) + '_' + fields[i]

    print('skllifying!...',end='')
    del fields[:2]
    fields.insert(0,'id')
    fields.append('label')

    wrt.writerow(fields)

    print('wait...', end='')
    for n,line in enumerate(rdr):

        del line[1]
        line.append(line.pop(0))
        line.insert(0,n+1)
        wrt.writerow(line)

    f.close()
    out.close()

    print('done')


############FILTER BY ROW###########

def filter_by_row(filepath, outputfile, clsfilter = 0, rows_by_class=100, skipnan=True,  **kwargs):
    """ decrease the size of the file, for each class take no more than rows_by_class rows
    the function will save the new file and print the number of pixels for each class

    IMPORTANT: this function will read all the file in memory. If the file is too big use filter_by_randomized_row()

    don't forget to pass  header=2 for the **kwargs to skip the headers!!!

    ######skip rows with empty values
    #filter_by_row(inp,out,  header=2)
    #filter_by_row(inp,out, skipnan=True,  header=2, na_filter=True)
    #filter_by_row(inp,out, skipnan=True,  header=2)

    #don't skip rows and output nan for empty values
    #filter_by_row(inp,out,skipnan=False, header=2,na_filter=True)
    #filter_by_row(inp,out,skipnan=False,  header=2)

    #don't skip rows and output empty for empty values
    #filter_by_row(inp,out,skipnan=False,  header=2, na_filter=False)

    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param clsfilter: the index of the column with filter values
    :param rows_by_class: the max number of returned rows for each class
    :param skipnan: True if rows with empty value must be skipped
            if skipnan is True then the pandas parameter na_filter must be True
    :param **kwargs: parameters for pandas.read_csv()
                  http://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html#pandas.read_csv

    :return: the count of rows for each class
    """

    inp = open (filepath)
    reader = csv.reader(inp)
    out = open( outputfile, 'w', newline='')
    writer = csv.writer(out)

    # write headers to output
    if kwargs and kwargs.get('header','infer'):
        if isinstance(kwargs['header'], int):
            for i in range(kwargs['header']):
                writer.writerow(next(reader))

    if skipnan:
        if kwargs and kwargs.get('na_filter',True) == False:
            print('if skipnan=True then na_filter must be True')
            print('try again!')
            return

    # using pandas/numpy to open and shuffle the entire file in memory
    print('opening csv file, wait....')
    f = pd.read_csv(filepath,**kwargs)
    arr = f.values

    if skipnan:
        print('delete incomplete rows...')
        arr = np.delete(arr, list(set(np.where(pd.isnull(arr))[0])), axis=0)

    print('shuffling data, wait....')
    np.random.shuffle(arr)

    # dictionary to store pixel counts for each class
    countpix = {}

    print('scanning file')
    for line in arr:

        if line[clsfilter] not in countpix:
            countpix[line[clsfilter]] = 0  # start the counter

        if countpix[line[clsfilter]] < rows_by_class:
            countpix[line[clsfilter]] += 1
            writer.writerow(list(line))

    inp.close()
    out.close()

    print('\nresults: ', countpix)
    return countpix


def split_input(filepath, outdirectory, headerscount=2, outsuffix='_tmp', splitrows=50):
    """ split a big text file info smaller pieces
    :param filepath: input file
    :param outdirectory:  path for temporary directory
    :param headerscount: number of header rows, these will go in file 0
    :param outsuffix: the suffix for the output file
    :param splitrows: number of rows for each output file
    :return: number of created files
    """

    if not os.path.exists(outdirectory):
        os.mkdir(outdirectory)

    f = open(filepath)

    # write file with only headers
    h = open(outdirectory + '/0' + outsuffix, 'w')
    for i in range(headerscount):
        h.write(next(f))
    h.close()

    # split file into multiple files
    g = None
    nfile = 1
    try:
        while True:
            counter = 0
            print("splitting file step ", nfile)
            g = open(outdirectory + '/' + str(nfile) + outsuffix, 'w')
            while counter < splitrows:
                row = next(f)
                if row[0] != ',': #skip empty rows
                    g.write(row)
                counter += 1
            g.flush()
            g.close()
            nfile += 1

    except StopIteration as e: # this will happen when we go over the last row
        if g and not g.closed:
            g.close()

    if f and not f.closed: f.close()

    return nfile


def shuffle(directory, start=1, endfile=10, fmt="%.16f", suffix=['_tmp', '_shuffletmp'], delimiter=','):
    """ shuffle csv files, the default start file is 1 because the file 0 store the headers

     IMPORTANT: this function cannot work with mixed values types and numpy.loadtext will fail ifthere are empty values

    :param directory: input directory with the files to shuffle
    :param start: the starting file prefix
    :param endfile: the end file prefix
    :param fmt: the data output format
    :param suffix: the suffix for the input and output files
    :param delimiter: items delimiter
    :return: start,endfile
    """

    for i in range(start, endfile + 1):
        arr = np.loadtxt(directory + '/' + str(i) + suffix[0], delimiter=delimiter)
        print('shuffling subfile ' + str(i))
        np.random.shuffle(arr)
        np.savetxt(directory + '/' + str(i) + suffix[1], arr, delimiter=delimiter, fmt=fmt)

    return start, endfile


def filter_by_randomized_row(directory, outputfile, suffix=['_tmp', '_shuffletmp'], headerscount=2, clsfilter = 0, rows_by_class=100):
    """ access chunk of files, randomize them, take 'rows_by_class' rows for each class

    the function print and return the number of pixels for each class

    IMPORTANT: if the input file is small you may want to use filter_by_row()

    :param directory: input directory
    :param outputfile: path to the output csv file
    :param suffix: the suffix for the input and output files
    :param headerscount: number of header rows, these will go in file 0
    :param clsfilter: the index of the column with filter values
    :param rows_by_class: the max number of returned rows for each class
    :return:  the count of rows for each class
    """

    # TODO exit the loop when all the classes have reached row_by_class (this would need the number of classes)

    # get the 2 headers
    inp = open(directory + '/0' + suffix[0])
    reader = csv.reader(inp)

    out = open(outputfile, 'w', newline='')
    writer = csv.writer(out)

    # write headers
    for i in range(headerscount):
        writer.writerow(next(reader))

    inp.close()

    # dictionary to store pixel counts for each class
    countpix = {}

    # list the suitable files in the directory
    f = os.listdir(directory)
    f = [i for i in f if i.endswith(suffix[1])]

    # randomize the list of files in place
    random.shuffle(f)

    # iterate the files and get rows
    for i in f:

        print('scanning file ' + i)

        inp = open(directory + '/' + i)

        reader = csv.reader(inp)

        for line in reader:

            if not line[clsfilter]:
                continue  # skip empty rows

            if line[clsfilter] not in countpix:
                countpix[line[clsfilter]] = 0  # start the counter

            if countpix[line[clsfilter]] < rows_by_class:
                countpix[line[clsfilter]] += 1
                writer.writerow(line)

        if inp and not inp.closed:
            inp.close()

    if inp and not inp.closed:
        inp.close()

    out.close()

    print('\nresults: ', countpix)

    return countpix

############FILTER BY COLUMN###########

def linked_iteration(filepath,image_filter, type_filter,default_indexes, fields):
    """  define the imagenames and indexes for the output using linked types
         the vegetation index output depends on the chosen bands,
         the texture bands depend on the chosen bands
         the texture vegetation indexes depend on the chosen bands and chosen vindex
    :param filepath: the input google engine csv file
    :param image_filter: list of image names or None for all the images
    :param type_filter: dictionary for the filter
    :param default_indexes: the left columns that stores the row indexes
    :param fields: the list of all fields (coming from the second csv row)
    :return: list of imagenames and list of filter indexes
    """

    if 'tvi' in type_filter and 'vi' not in type_filter:
        print('to get the "tvi" you need to specify the "vi"')
        return

    # get a tuple with an ordered dictionary {raster_name: field_count} and a set with the unique raster names
    tablestructure = get_structure(filepath)

    images = list(tablestructure[0].keys())
    counts = list(tablestructure[0].values())

    # this will store the field indexes
    indexes = list(range(default_indexes))+ []
    imagenames=[]
    # add indexes as first fields
    for i in range(default_indexes): imagenames.append('id_'+str(i))

    for n,image in enumerate(images):

        image_name = image.split('_')[-3]+'_'+ image.split('_')[-2]

        if not image_filter or (image_filter and (image_name in image_filter)): # define wich images, all or some?

            # get the number of fields for this image
            offset = 0
            for i in range(n):
                offset += counts[i]

            # print(offset)

            field_count = tablestructure[0][image]

            for j in range(offset,offset+field_count):

                #split the field name
                splitted = fields[j].split('_')

                for t in type_filter: # iterate the filter dictionary

                    if t in TYPES:

                        if t == 'b':
                            if fields[j].startswith('b') and len(splitted) == 1:

                                if type_filter[t]: # check subtype
                                    if splitted[0] in type_filter[t]:
                                        indexes.append(j)
                                        imagenames.append(image_name)
                                else:  # no subtype, take all
                                    indexes.append(j)
                                    imagenames.append(image_name)

                        elif t == 'vi':

                            if splitted[0].upper() in VITYPES and (len(splitted) <= 3):  # check this field is ok

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[0].upper():

                                        if tf in VTYPES_NOBAND:  # check this is a special vi
                                            indexes.append(j)
                                            imagenames.append(image_name)
                                            break

                                        if type_filter.get('b', False):  # check if there is a subfilter

                                            if len(type_filter['b']) > 1:  #check there are band combinations
                                                bandcombination = 0
                                                for bb in type_filter['b']:
                                                    if bb in fields[j]:
                                                        bandcombination +=1
                                                if bandcombination == 2:
                                                    indexes.append(j)
                                                    imagenames.append(image_name)
                                                    break

                                        else:  # no type_filter['b'], take all
                                            indexes.append(j)
                                            imagenames.append(image_name)

                        elif t == 'tb':

                            if fields[j].startswith('b') and len(splitted) > 1:

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[1].upper():  # look for the filter

                                        if type_filter.get('b', False):  # check if there is a subfilter

                                            for bb in type_filter['b']:
                                                if bb in fields[j]:
                                                    indexes.append(j)
                                                    imagenames.append(image_name)

                                        else:  # noband filter, take all
                                            indexes.append(j)
                                            imagenames.append(image_name)

                        elif t == 'tvi':

                            if splitted[0].upper() in VITYPES and (len(splitted) >= 4) \
                                    and (splitted[0].upper() in type_filter['vi']):

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[3].upper() or tf.upper() == splitted[1].upper():

                                        if set([splitted[0].upper()]).intersection(VTYPES_NOBAND):# check this is a special vi
                                            indexes.append(j)
                                            imagenames.append(image_name)
                                            break

                                        if type_filter.get('b', False):  # check if there is a subfilter

                                            if len(type_filter['b']) > 1:  # check there are band combinations
                                                bandcombination = 0
                                                for bb in type_filter['b']:
                                                    if bb in splitted: bandcombination +=1
                                                if bandcombination == 2:
                                                    indexes.append(j)
                                                    imagenames.append(image_name)
                                                    break

                                        else: # if no band filter, take all
                                            indexes.append(j)
                                            imagenames.append(image_name)

                    else:
                        print('type_filter should be:  b vi tb tvi ')
                        print('type_filter should be: ' + str(VITYPES))
                        return

    return imagenames, indexes


def standard_iteration(filepath,image_filter, type_filter,default_indexes, fields):
    """  define the imagenames and indexes for the output using linked types
         the filters are independent, for linked filters use the function linked_iteration()
    :param filepath: the input google engine csv file
    :param image_filter: list of image names or None for all the images
    :param type_filter: dictionary for the filter
    :param default_indexes: the left columns that stores the row indexes
    :param fields: the list of all fields (coming from the second csv row)
    :return: list of imagenames and list of filter indexes
    """

    # get a tuple with an ordered dictionary {raster_name: field_count} and a set with the unique raster names
    tablestructure = get_structure(filepath)

    images = list(tablestructure[0].keys())
    counts = list(tablestructure[0].values())

    # this will store the field indexes
    indexes = list(range(default_indexes)) + []
    imagenames = []
    # add indexes as first fields
    for i in range(default_indexes): imagenames.append('id_' + str(i))

    for n, image in enumerate(images):

        image_name = image.split('_')[-3] + '_' + image.split('_')[-2]

        if not image_filter or (image_filter and (image_name in image_filter)):  # define wich images, all or some?

            # get the number of fields for this image
            offset = 0
            for i in range(n):
                offset += counts[i]

            # print(offset)

            field_count = tablestructure[0][image]

            for j in range(offset, offset + field_count):

                # split the field name
                splitted = fields[j].split('_')

                for t in type_filter:  # iterate the filter dictionary

                    if t in TYPES:

                        if t == 'b':
                            if fields[j].startswith('b') and len(splitted) == 1:
                                if type_filter[t]:  # check subtype
                                    if splitted[0] in type_filter[t]:
                                        indexes.append(j)
                                        imagenames.append(image_name)
                                else:  # no subtype, take all
                                    indexes.append(j)
                                    imagenames.append(image_name)

                        elif t == 'vi':

                            if splitted[0].upper() in VITYPES and (len(splitted) <= 3):  # check this field is ok

                                for tf in type_filter[t]:
                                    if tf.upper() == splitted[0].upper():
                                        indexes.append(j)
                                        imagenames.append(image_name)

                        elif t == 'tb':

                            if fields[j].startswith('b') and len(splitted) > 1:
                                for tf in type_filter[t]:
                                    if tf.upper() == splitted[1].upper():  # look for the filter
                                            indexes.append(j)
                                            imagenames.append(image_name)

                        elif t == 'tvi':

                            if splitted[0].upper() in VITYPES and (len(splitted) >= 4):
                                for tf in type_filter[t]:
                                    if tf.upper() == splitted[3].upper() or tf.upper() == splitted[1].upper():
                                            indexes.append(j)
                                            imagenames.append(image_name)

                    else:
                        print('type_filter should be:  b vi tb tvi ')
                        print('type_filter should be: ' + str(VITYPES))
                        return

    return imagenames, indexes


def filter_by_column(filepath, outputfile, image_filter=None, type_filter=None, default_indexes=2, linked=True):
    """ Filter the google engine files by field and output a new csv

    the first 2 rows are considered as headers

    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param image_filter: list of images names; pass None for all images
    :param type_filter: dictionary of types and subtypes to filter, possible names are in TYPES,VITYPES,VITYPES, TEXTYPES

    type_filter =
    { 'b' : ['b1','b2','b3','b4','b5','b6','b7','b8'],
      'vi': ['DVI', 'NDI', 'RVI', 'SAVI', 'TCARI', 'EVI', 'MSAVI2']
      'tb': ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']
      'tvi': ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']
    }

    if no type_filter, take all
    if no subfilter is needed (which is take all) leave the key empty   e.g. 'b':{}
    if no key, no output for this filter

    :param default_indexes: the number of left columns with the indexes
    :param linked: dependent or independent filtrs?

    if linked=False you get:
    the vegetation index output is independent from  the chosen bands
    the texture bands is independent from the chosen bands
    the texture vegetation indexes is independent from the chosen bands and independent from the chosen vegindexes

    if linked=True you get:
    the vegetation index output depends on the chosen bands (but not for 'SAVI', 'TCARI', 'EVI', 'MSAVI2' )
    the texture bands depend on the chosen bands
    the texture vegetation indexes depend on the chosen bands (but not for 'SAVI', 'TCARI', 'EVI', 'MSAVI2' ) and chosen vegindex

    if linked=True or linked=False

    :return:  list of output field names, indexes of field names, list of output imagenames
    """

    # if no image and filter is specified exit
    if not image_filter and not type_filter:
        print('please, specify and image filter and/or a type filter')
        return

    # if the image is specified but not the filter take all for the image
    elif not type_filter:
        type_filter = { 'b' : BANDS,
                        'vi': VITYPES,
                        'tb': TEXTYPES,
                        'tvi': TEXTYPES }

    # if the lists are empty take all
    if 'b' in type_filter and not type_filter['b']: type_filter['b'] = BANDS
    if 'vi' in type_filter and not type_filter['vi']: type_filter['vi'] = VITYPES
    if 'tb' in type_filter and not type_filter['tb']: type_filter['tb'] = TEXTYPES
    if 'tvi' in type_filter and not type_filter['tvi']: type_filter['tvi'] = TEXTYPES

    inp = open(filepath)
    reader = csv.reader(inp)
    out = open(outputfile, 'w', newline='')
    writer = csv.writer(out)

    # access field row
    next(reader)  # first row with image names
    fields = next(reader) # second row with field names

    # define the indexes to filter the csv rows
    if linked:
        a = linked_iteration(filepath,image_filter, type_filter,default_indexes, fields)
    else:
        a = standard_iteration(filepath,image_filter, type_filter,default_indexes, fields)

    if not a:
        print('try again!')
        return

    imagenames = a[0]
    indexes = a[1]

    # write filtered headers
    writer.writerow(imagenames)
    write_filtered_row(fields, indexes, writer)
    # write filtered rows
    print('filtering lines')
    for line in reader:
        if not line[0]:
            continue  # skip empty lines
        write_filtered_row(line, indexes, writer)

    inp.close()
    out.close()

    print('done')

    return [fields[i] for i in indexes], indexes, imagenames


############ cross something



def ind_VfoldCross( data, **kwargs):
    """ Funcionqu se le introduce los datos las etiquetas y el numero de grupos que se quiere obtener
    :param data: numpy 1D collection with the labels
    :param **kwargs: keyword arguments  for  KFold

            default **kwargs values are

            n_folds : int, default=3 Number of folds. Must be at least 2.
            shuffle : boolean, optional Whether to shuffle the data before splitting into batches.
            random_state : None, int or RandomState When shuffle=True, pseudo-random number generator state
                            used for shuffling. If None, use default numpy RNG for shuffling.

    :return: train_fold list, test_fold list, the numbers of folds

    source from matlab
    function indc = ind_VfoldCross(Y, grupos)
    % Funcionqu se le introduce los datos las etiquetas y el numero de grupos
    % que se quiere obtener

    clase = unique(Y);
    indc = zeros(size(Y, 1), 1);
    for t=1:length(clase)
        ind = find(Y == clase(t));
        in =crossvalind('Kfold', length(ind), grupos);
        for p=1:grupos
            indc(ind( in == p))=p;
        end
    end

    """

    if len(data.shape)> 1:
        print("please, use a 1D array")
        return
    #get the unique classes

    if not kwargs.get('n_folds', False):
        print("n_folds parameter not specified, default 3 will be used")

    #numpy.unique(ar, return_index=False, return_inverse=False, return_counts=False)
    cls = np.unique(data)

    #initialize empty result 2d array
    arr_train = np.zeros(data.shape[0],)
    arr_test = np.zeros(data.shape[0],)

    i=0
    try:
        for i in cls:
            #get the indexes for each
            ind = np.where(data == i)

            #KFold(n, n_folds=3, shuffle=False, random_state=None)
            kf = KFold( len(ind[0]), **kwargs )

            for n,j in enumerate(kf):
                #print(j)
                arr_train[ ind[0][j[0]] ] = n
                arr_test[ind[0][j[1]]] = n

    except Exception as e:
        print("class ", i)
        print(e)
        return

    if not kwargs.get('n_folds', False):
        kwargs['n_folds'] = 3
    return arr_train, arr_test, kwargs['n_folds']






###############################################TESTS############################
#print(get_structure("data/train_kernel_1_v4.csv"))

############## cross folders

'''

originaldata = np.array([[1, 1, 9, 0, 1, 0, 6, 3, 7, 3],
                             [2, 2, 6, 4, 7, 3, 6, 7, 7, 8],
                             [3, 3, 1, 1, 0, 5, 9, 7, 7, 9],
                             [4, 4, 3, 6, 5, 7, 1, 3, 3, 8],
                             [1, 5, 0, 4, 1, 5, 4, 0, 0, 9],
                             [2, 6, 5, 2, 2, 6, 5, 5, 6, 8],
                             [3, 7, 5, 3, 7, 0, 9, 2, 0, 5],
                             [4, 8, 6, 4, 5, 4, 1, 3, 0, 2],
                             [1, 9, 2, 6, 0, 1, 4, 6, 4, 0],
                             [2, 10, 0, 7, 1, 5, 6, 2, 6, 7],
                             [3, 11, 8, 9, 4, 6, 4, 7, 6, 6],
                             [4, 12, 0, 7, 7, 0, 6, 6, 2, 9],
                             [1, 13, 9, 6, 9, 5, 5, 8, 5, 8],
                             [2, 14, 7, 3, 6, 9, 0, 3, 7, 7],
                             [3, 15, 8, 9, 8, 5, 1, 4, 9, 0],
                             [4, 16, 5, 1, 5, 6, 9, 1, 0, 1],
                             [5, 17, 5, 9, 4, 7, 6, 9, 8, 1],
                             [5, 18, 9, 3, 7, 8, 5, 2, 3, 7],
                             [2, 19, 7, 5, 8, 2, 8, 8, 0, 9],
                             [2, 20, 0, 3, 0, 3, 9, 9, 6, 6]])

#extract column with classes
cls = originaldata[:, 0]

arr_train, arr_test, n_folds = ind_VfoldCross(cls, n_folds=2)
print(arr_train, arr_test)

# this is the first group
print(originaldata[arr_train == 0])
# this is the second group
print(originaldata[arr_train == 1])

'''

#####skllify a file
#skllifier(r"C:\Users\claudio\PycharmProjects\STARS\temp\preskll.txt",r"C:\Users\claudio\PycharmProjects\STARS\temp\afterskll.tsv")
#check_item_count(r"C:\Users\claudio\PycharmProjects\STARS\temp\afterskll.tsv", delimiter='\t')


########get 1 or a range of rows
#r = get_row(r"C:\Users\claudio\PycharmProjects\STARS\temp\afterskll.tsv",0)


################################ FILTER BY ROW TESTS#####################

#########################filter with pandas (everything in memory)

#inp = r"C:\Users\piccinini\PycharmProjects\STARS\data\test.csv"
#out =  r"C:\Users\piccinini\PycharmProjects\STARS\data\test_filter_row.csv"
#inp= r"C:\Users\claudio\PycharmProjects\STARS\data\train_kernel_1_v5_Clean.csv"
#out= r"C:\Users\claudio\PycharmProjects\STARS\data\train_kernel_1_v5_Clean_filteredpandas.csv"


######skip rows with empty values
#filter_by_row(inp,out,  header=2)
#filter_by_row(inp,out, skipnan=True,  header=2, na_filter=True)
#filter_by_row(inp,out, skipnan=True,  header=2)


#don't skip rows and output nan for empty values
#filter_by_row(inp,out,skipnan=False, header=2,na_filter=True)
#filter_by_row(inp,out,skipnan=False,  header=2)

#don't skip rows and output empty for empty values
#filter_by_row(inp,out,skipnan=False,  header=2, na_filter=False)


############################filter by splitting (for very big files)
#### first plit the file, then randomize the chunks internally, finally iterate random chunks

#drt = r"C:\Users\claudio\PycharmProjects\STARS\temp"
#inp= r"C:\Users\claudio\PycharmProjects\STARS\data\train_kernel_1_v5_Clean.csv"
#out = r"C:\Users\claudio\PycharmProjects\STARS\data\train_kernel_1_v5_Clean_filteredsplitted.csv"

####clean_directory(drt)  #use this if you want to clean the temporary directory

#1) split file; by default 50 rows per chunck, use splitrows parameter to change it
#infile = split_input( inp, drt)

#2) shuffle the chunks internally
# the -1 is here because this input file had a problem with the last csv line, -1 means do not consider the last chunk of data
#generally it would be just infile
#shuffle(drt, endfile=(infile - 1))

#3) get the result from randomized chunks
#filter_by_randomized_row(drt,out, rows_by_class=100)

#4) clean the temporary directory
#clean_directory(drt)

######################################## check if the number of columns csv files is always the same
#import os
#tmp = r"C:\Users\claudio\PycharmProjects\STARS\temp"
#files=os.listdir(tmp)
#for f in files:
#    print(tmp + "/" + f, check_item_count(tmp + "/" + f))


################################ FILTER BY COLUMN TESTS#####################

############ same results
# 1 image,all bands
#a = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAa.csv", ['054112895040_01'],type_filter={'b': []})
#a = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAa_nolink.csv", ['054112895040_01'],type_filter={'b': []}, linked=False)
##################### same results
# all images, all bands
#aa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaa.csv",type_filter={'b': []})
#aa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaa_nolink.csv",type_filter={'b': []},linked=False)
################ same results
# 1 image, 2 bands
#aaa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaaa.csv", ['054112895040_01'],type_filter={'b': ['b3','b4']})
#aaa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaaa_nolink.csv", ['054112895040_01'],type_filter={'b': ['b3','b4']}, linked=False)
################## same results
# all images, 2 bands
#aaaa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaaaa.csv",type_filter={'b': ['b3','b4']})
#aaaa = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsAaaaa_nolink.csv",type_filter={'b': ['b3','b4']}, linked=False)

######################## same results
# 1 image, all vegindex
#b = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsB.csv",['054112895040_01'],type_filter={'vi': []})
#b = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsB_nolink.csv",['054112895040_01'],type_filter={'vi': []}, linked=False)

############################################### different results
# all images, 1 band, all vegindex ( only the general indexes, the vi with band combinations are not outputed)
#bb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbb.csv",type_filter={'b': ['b3'], 'vi': []})
# all images, 1 band, all vegindex
#bb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbb_nolink.csv",type_filter={'b': ['b3'], 'vi': []}, linked=False)

####################################################################### different results
# all images, 2 band, all vegindex (general indexes + the vi with the 2 band combinations are outputed )
#bbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbb.csv",type_filter={'b': ['b3','b6'], 'vi': []})
# all images, 2 bands, all vegindex
#bbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbb_nolink.csv",type_filter={'b': ['b3','b6'], 'vi': []}, linked=False)

##################################### same results
#all images, savi index
#bbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbb.csv",type_filter={'vi': ['SAVI']})
#bbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbb_nolink.csv",type_filter={'vi': ['SAVI']}, linked=False)

################################# same results
#1 image, savi index
#bbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbb.csv",['054112895040_01'],type_filter={'vi': ['SAVI']})
#bbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbb_nolink.csv",['054112895040_01'],type_filter={'vi': ['SAVI']}, linked=False)

################################# same results
#1 image, NDI index
#bbbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbbb.csv",['054112895040_01'],type_filter={'vi': ['NDI']})
# 1 image, NDI index
# bbbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbbb_nolink.csv",['054112895040_01'],type_filter={'vi': ['NDI']}, linked=False)

############################### different results
#1 image, 2 bands, NDI index( only the 2 band combinations)
#bbbbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbbbb.csv",['054112895040_01'],type_filter={'b': ['b2','b7'],'vi': ['NDI']})
#1 image, 2 bands, all NDI index
#bbbbbbb = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsBbbbbbbb_nolink.csv",['054112895040_01'],type_filter={'b': ['b2','b7'],'vi': ['NDI']}, linked=False)

####################################### same results
#1 image, all texture bands
#c = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsC.csv",['054112895040_01'],type_filter={'tb': []})
# 1 image, all texture bands
#c = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsC_nolink.csv",['054112895040_01'],type_filter={'tb': []}, linked=False)

######################################### same results
#all images, all texture bands
#c1 = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsC1.csv",type_filter={'tb': []})
# all images, all texture bands
#c1 = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsC1_nolink.csv",type_filter={'tb': []}, linked=False)

########################################## same results
#1 image, all texture bands
#cc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCc.csv",['054112895040_01'],type_filter={'tb': ['diss','dvar']})
#1 image, all texture bands
#cc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCc_nolink.csv",['054112895040_01'],type_filter={'tb': ['diss','dvar']}, linked=False)

###################################### different results
# #1 image, 1 band, 2 textures (for the the single band)
#ccc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCcc.csv",['054112895040_01'],type_filter={'b': ['b5'],'tb': ['diss','dvar']})
#1 image, 1 band, 2 textures (for all the band)
#ccc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCcc_nolink.csv",['054112895040_01'],type_filter={'b': ['b5'],'tb': ['diss','dvar']}, linked=False)

######################################## different results
#all images, 1 band, 2 textures (for the the band)
#cccc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCccc.csv",type_filter={'b': ['b5'],'tb': ['diss','dvar']})
#all images, 1 band, 2 textures (for all the bands)
#cccc = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsCccc_nolink.csv",type_filter={'b': ['b5'],'tb': ['diss','dvar']}, linked=False)

######################################## different results
#this will return None because the vi is not specified
#d = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsD.csv",['054112895040_01'],type_filter={'tvi': []})
#this will return all tvi
#d = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsD_nolink.csv",['054112895040_01'],type_filter={'tvi': []}, linked=False)

######################################### different results
# 1 image, vi for all band combinations, tvi for NDI
#dd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDd.csv",['054112895040_01'],type_filter={'vi':['NDI'],'tvi': ['diss']})
# 1 image, vi and tvi for all band combinations
#dd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDd_nolink.csv",['054112895040_01'],type_filter={'vi':['NDI'],'tvi': ['diss']}, linked=False)

#################################different results
#1 image, 2 bands, vi for 2 bands combinations, tvi for ndvi and 2 bands combinations
#ddd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDdd.csv",['054112895040_01'],type_filter={'b':['b5','b2'], 'vi':['NDI'],'tvi': ['diss']})
#1 image, 2 bands, all vi NDI, all tvi diss
#ddd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDdd_nolink.csv",['054112895040_01'],type_filter={'b':['b5','b2'], 'vi':['NDI'],'tvi': ['diss']}, linked=False)

##################################different results
#1 image, 2 bands, NDI for 2 bands combinations + MSAVI2, tvi for the 2 vi and 2 band combinations, tb for 2 band combinations
#ddd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDdd.csv",['054112895040_01'],type_filter={'b':['b5','b2'], 'vi':['NDI','MSAVI2'],'tvi': ['diss', 'corr'], 'tb':['inertia','prom']})
#1 image, 2 bands, NDI for all bands combinations + MSAVI2, tvi for  all vi and all band combinations, tb for all band combinations
#ddd = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsDdd_nolink.csv",['054112895040_01'],type_filter={'b':['b5','b2'], 'vi':['NDI','MSAVI2'],'tvi': ['diss', 'corr'], 'tb':['inertia','prom']}, linked=False)

#################################################different results
#all images, 1 band ,rvi and ndi are not outputed because they need a band combination
#e = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldse.csv",type_filter={'b': ['b4'], 'vi': ['RVI', 'MSAVI2','NDI' ]})
#all images, 1 band , vi for all band combinations
#e = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldse_nolink.csv",type_filter={'b': ['b4'], 'vi': ['RVI', 'MSAVI2','NDI' ]}, linked=False)

################################################different results
#all images, 3 bands, vi for 3 band combinations
#f = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsf.csv", type_filter={'b': ['b4', 'b6', 'b8'], 'vi': ['RVI', 'MSAVI2','NDI' ]})
#all images, 3 bands, vi for all band combinations
#f = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsf_nolink.csv", type_filter={'b': ['b4', 'b6', 'b8'], 'vi': ['RVI', 'MSAVI2','NDI' ]}, linked=False)

################################################ different results
#1 image, 2 bands, vi for the 2 band combinations, tb for the 2 band combinations, tvi for the 2 band combinations and the 3 vi
#g = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsg.csv", ['054112895040_01'],type_filter={'b': ['b4','b6'], 'vi': ['RVI', 'MSAVI2', 'NDI'], 'tb':['corr','dent','diss'],'tvi':['imcorr2','inertia','prom']})
#1 image, 2 bands, vi for all band combinations, tb for all bands, tvi for all band combinations and all vi
#g = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfieldsg_nolink.csv", ['054112895040_01'],type_filter={'b': ['b4','b6'], 'vi': ['RVI', 'MSAVI2', 'NDI'], 'tb':['corr','dent','diss'],'tvi':['imcorr2','inertia','prom']}, linked=False)