# -*- coding: utf-8 -*-

import csv
import collections
import os
import numpy as np

#import fileIO

#constants for bands, vegetation indexes, texture bands, texture vegetation indexes
TYPES = ['b', 'vi', 'tb', 'tvi']

BANDS = ['b1','b2','b3','b4','b5','b6','b7','b8']

VITYPES = ['DVI', 'NDI','RVI','SAVI','TCARI','EVI','MSAVI2']

VTYPES_NOBAND = ['SAVI', 'TCARI', 'EVI', 'MSAVI2'] #types independent from bands

TEXTYPES = ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']


def get_structure(filepath):
    ''' this function will read the structure of google engine files
    the fist row contains the raster names
    the second row contains many fields for each raster
    :param filepath: path to the csv file
    :return: on ordered dictionary  raster_name: field_count and a set with the unique raster names
    '''

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
    '''
    utility function to return unque field names from the second row,
    :param filepath:
    :param outfile: set this if you want to output to a file
    :return: a list of unique fields
    '''

    f = open (filepath)
    reader = csv.reader(f)
    next(reader)
    fields = next(reader)
    f.close()

    uniquefields = []
    [uniquefields.append(item) for item in fields if item not in uniquefields]

    print('done')

    if outfile:
        f = open(outfile, 'w')

        for i in uniquefields:
            f.write(i+'      ')

        f.close()
    return uniquefields


def write_filtered_row(inputrow,indexes, csvwriter):
    '''
    utility function to filter a list and write it to csv
    :param inputrow:  the full input list
    :param indexes: the filter indexes
    :param csvwriter: the csv writer
    :return: None
    '''
    newline=[]
    for i in indexes:
        newline.append(inputrow[i])
    csvwriter.writerow(newline)

def filter_by_row(filepath, outputfile, rows_by_class=100):
    ''' decrease the size of the file, for each class take no more than rows_by_class rows
    the function print the numer of pixels for each class
    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param rows_by_class: the max number of returned rows for each class
    :return: the filtered csv file; the first 2 rows are kept
    '''

    #TODO: randomize data

    inp = open (filepath)
    reader = csv.reader(inp)


    out = open( outputfile, 'w',newline='')
    writer = csv.writer(out)

    #write first 2 rows
    writer.writerow(next(reader))
    writer.writerow(next(reader))

    countpix = {} #dictionary to store pixel counts for each class

    print('scanning file')
    for line in reader:
        print('.', end='')

        if not line[0]: continue #skik empty rows

        if line[0] not in countpix:
            countpix[line[0]] = 0 #start the counter

        if countpix[line[0]] < rows_by_class:
            countpix[line[0]] += 1
            writer.writerow(line)

    inp.close()
    out.close()

    print('\nresults: ',countpix)

def filter_by_column(filepath, outputfile, image_filter = None, type_filter = None, default_indexes = 2):
    ''' Filter the google engine files by field and output a new csv

    type_filter =
    { 'b' : ['b1','b2','b3','b4','b5','b6','b7','b8'],
      'vi': ['DVI', 'NDI', 'RVI', 'SAVI', 'TCARI', 'EVI', 'MSAVI2']
      'tb': ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']
      'tvi': ['asm', 'contrast','corr','dent','diss','dvar','ent','idm','imcorr1','imcorr2','inertia','prom','savg','sent','shade','svar','var']
    }

    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param image_filter: list of images names; pass None for all images
    :param type_filter: dictionary of types and subtypes to filter, possible names are in TYPES,VITYPES,VITYPES, TEXTYPES
    if no subfilter is needed leave the key empty   e.g. 'b':{}
    :param default_indexes: the number of left columns with the indexes

    :return:  list of output field names, indexes of field names, list of output imagenames
    '''

    #if no image and filter is specified exit
    if not image_filter and not type_filter:
        print('please, specify and image filter and/or a type filter')
        return

    #if the image is specified but not the filter take all for the image
    elif not type_filter:
        type_filter = { 'b' : BANDS,
                        'vi': VITYPES,
                        'tb': TEXTYPES,
                        'tvi': TEXTYPES }

    #if the filters for vi,tb,tvi are missing or empty take all
    if 'vi' not in type_filter or not type_filter['vi']: type_filter['vi'] = VITYPES
    if 'tb' not in type_filter or not type_filter['tb']: type_filter['tb'] = TEXTYPES
    if 'tvi' not in type_filter or not type_filter['tvi']: type_filter['tvi'] = TEXTYPES


    inp = open(filepath)
    reader = csv.reader(inp)
    out = open(outputfile, 'w', newline='')
    writer = csv.writer(out)

    #access field row
    next(reader)
    fields = next(reader)

    tablestructure, imagenames = get_structure(filepath)

    images = list(tablestructure.keys())
    counts = list(tablestructure.values())

    #this will store the field indexes
    indexes = list(range(default_indexes))+ []
    imagenames=[]
    # add indexes as first fields
    for i in range(default_indexes): imagenames.append('ID_'+str(i))

    for n,image in enumerate(images):

        image_name = image.split('_')[-3]+'_'+ image.split('_')[-2]

        if not image_filter or (image_filter and image_name in image_filter): #define wich images, all or some?

            #get the number of fields for this image
            offset = 0
            for i in range(n):
                offset += counts[i]

            #print(offset)

            field_count = tablestructure[image]

            for j in range(offset,offset+field_count):

                #split the field name
                splitted = fields[j].split('_')

                for t in type_filter: #itrate the dictionary

                    if t in TYPES:

                        if t=='b':
                            if fields[j].startswith('b') and len(splitted)== 1:

                                if type_filter[t]: #check subtype
                                    if splitted[0] in type_filter[t]:
                                        indexes.append(j)
                                        imagenames.append(image_name)
                                else: #no subtype, take all
                                    indexes.append(j)
                                    imagenames.append(image_name)
                                    # TODO additional filter for band number

                        elif t=='vi':

                            if splitted[0].upper() in VITYPES and (len(splitted)<= 3) : #check this field is ok

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[0].upper():

                                        if type_filter['b']: #check if there is a subfilter

                                            if tf in VTYPES_NOBAND: #check this is a special vi
                                                indexes.append(j)
                                                imagenames.append(image_name)
                                                break

                                            else: #if not special,
                                                if len(type_filter['b'])>1:  #check there are band combinations
                                                    bandcombination = 0
                                                    for bb in type_filter['b']:
                                                        if bb in fields[j]: bandcombination +=1
                                                    if bandcombination == 2:
                                                        indexes.append(j)
                                                        imagenames.append(image_name)
                                                        break

                                        else:  #type_filter['b']
                                            indexes.append(j)
                                            imagenames.append(image_name)


                        elif t=='tb':

                            if fields[j].startswith('b') and len(splitted) > 1:

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[1].upper(): #look for the filter

                                        if type_filter['b']:  # check if there is a subfilter

                                            for bb in type_filter['b']:
                                                if bb in fields[j]:
                                                    indexes.append(j)
                                                    imagenames.append(image_name)

                                        else:  # noband filter
                                            indexes.append(j)
                                            imagenames.append(image_name)

                        elif t == 'tvi':

                            if splitted[0].upper() in VITYPES and (len(splitted) >= 4) and (splitted[0].upper() in type_filter['vi']):

                                for tf in type_filter[t]:

                                    if tf.upper() == splitted[3].upper() or tf.upper() == splitted[1].upper():

                                        if type_filter['b']: #check if there is a subfilter

                                            if tf in VTYPES_NOBAND: #check this is a special vi
                                                indexes.append(j)
                                                imagenames.append(image_name)
                                                break

                                            else: #if not special,
                                                if len(type_filter['b'])>1:  #check there are band combinations
                                                    bandcombination = 0
                                                    for bb in type_filter['b']:
                                                        if bb in splitted: bandcombination +=1
                                                    if bandcombination == 2:
                                                        indexes.append(j)
                                                        imagenames.append(image_name)
                                                        break

                                        else:
                                            indexes.append(j)
                                            imagenames.append(image_name)

                    else:
                        print('type_filter should be:  b vi tb tvi ')
                        print('type_filter should be: '+  str(VITYPES))
                        print('try again!')
                        return

    #write filtered headers
    writer.writerow(imagenames)
    write_filtered_row(fields, indexes, writer)
    #write filtered rows
    print('filtering lines')
    for line in reader:
        if not line[0]:continue #skip empty lines
        write_filtered_row(line, indexes, writer)

    inp.close()
    out.close()

    print('done')

    return [fields[i] for i in indexes], indexes, imagenames


def splitinput(filepath, outdirectory, headerscount = 2, splitrows = 50):
    '''
    :param filepath:
    :param outdirectory: absollute path for temporary directory
    :param splitrows: number of rows for each out file
    :return:
    '''

    if not os.path.exists(outdirectory):
        os.mkdir(outdirectory)

    f = open(filepath)

    #write file with only headers
    h = open(outdirectory + '/0_tmp', 'w')
    for i in range(headerscount):
        h.write(next(f))
    h.close()

    #split file into multiple files
    g = None
    nfile = 1
    try:
        while(True):
            counter = 0
            g = open(outdirectory + '/' + str(nfile) +'_tmp', 'w')
            while counter < splitrows:
                row = next(f)
                if row[0] != ',' : g.write(row)
                counter+=1
            g.flush()
            g.close()
            nfile += 1

    except StopIteration as e:
        if g and not g.closed: g.close()

    if f and not f.closed: f.close()

    return nfile

def shuffle(directory, nfile):
    for i in (1,nfile):
        arr = np.loadtxt(directory + '/' + str(i) + '_tmp', delimiter=',')
        print('shuffling file '+str(i))
        np.random.shuffle(arr)
        arr.tofile(directory + '/' + str(i) + '_tmp', sep=",", format="%.16f")


###############################################TESTS############################
#print(get_structure("data/train_kernel_1_v4.csv"))

#filter_by_row("data/train_kernel_1_v4.csv","data/train_kernel_1_v4_fiteredrows.csv" ,1)

#a = filter_by_column("data/train_kernel_1_v4_fiteredrows.csv", "data/train_kernel_1_v4_fiteredfeldsa.csv", None,type_filter={'b': ['b4'], 'vi': ['RVI', 'MSAVI2','NDI' ]})
#b = filter_by_column("data/train_kernel_1_v4_fiteredrows.csv", "data/train_kernel_1_v4_fiteredfeldsb.csv", None,type_filter={'b': ['b4', 'b6', 'b8'], 'vi': ['RVI', 'MSAVI2','NDI' ]})
#c = filter_by_column("data/train_kernel_1_v4_fiteredrows.csv", "data/train_kernel_1_v4_fiteredfeldsc.csv", ['054112895040_01'],type_filter={'b': ['b4','b6'], 'vi': ['RVI', 'MSAVI2', 'NDI'], 'tb':['corr','dent','diss'],'tvi':['imcorr2','inertia','prom']})


#infile = splitinput( "data/train_kernel_1_v4.csv", r"C:\Users\claudio\PycharmProjects\STARS\temp" )
#shuffle(r"C:\Users\claudio\PycharmProjects\STARS\temp", 41)