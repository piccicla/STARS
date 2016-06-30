# -*- coding: utf-8 -*-

import csv
import collections
import fileIO

#types to look for (bands, vegetation indexes, texture bands, texture vegetation indexes
TYPES = ['b', 'vi', 'tb', 'tvi']

VITYPES = ['DVI', 'NDI','RVI','SAVI','TCARI','EVI','MSAVI2']


TEXTYPES = []


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

    uniquefirst=list(set(first))
    #print(len(uniquefirst))

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
    utility function to return field names
    :param filepath:
    :return:
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
    filter a list and write to csv
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
    if the class has less rows than rows_by_class output a warning text file
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


def filter_by_column(filepath, outputfile, image_filter = None, type_filter = [], subtype_filter=[], default_indexes = [0,1]):
    '''
    :param filepath: path to the csv file
    :param outputfile: path to the output csv file
    :param image_filter: list of images names; pass None for all images
    :param type_filter: list of types to filter, possible names are in TYPES
    :param subtype_filter: list with subtype filters
    :param default_indexes: fields that contains the ids and must be in the output

    :return:
    '''


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
    indexes= default_indexes+ []
    imagenames=[]
    for i in range(len(default_indexes)): imagenames.append('ID_'+str(i))


    for n,image in enumerate(images):

        image_name = image.split('_')[-3]+'_'+ image.split('_')[-2]

        if not image_filter or (image_filter and image_name in image_filter):

            #get the number of fields for this image

            offset = 0
            for i in range(n):
                offset += counts[i]

            #print(offset)

            field_count = tablestructure[image]

            for j in range(offset,offset+field_count):

                #split the field name
                splitted = fields[j].split('_')

                for t in type_filter:

                    if t in TYPES:

                        if t=='b':
                            if fields[j].startswith('b') and len(splitted)== 1:
                                indexes.append(j)
                                imagenames.append(image_name)
                                # TODO additional filter for band number

                        elif t=='vi':

                            if splitted[0].upper() in VITYPES and (len(splitted)<= 3) :
                                indexes.append(j)
                                imagenames.append(image_name)
                                #TODO additional filter for subtype

                        elif t=='tb':

                            if fields[j].startswith('b') and len(splitted) > 1:
                                indexes.append(j)
                                imagenames.append(image_name)
                                # TODO additional filter for subtype

                        elif t=='tvi':
                            if splitted[0].upper() in VITYPES and (len(splitted) >= 4):
                                indexes.append(j)
                                imagenames.append(image_name)
                                # TODO additional filter for subtype

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

#print(get_structure("data/train_kernel_1_v4.csv"))

#filter_by_row("data/train_kernel_1_v4.csv","data/train_kernel_1_v4_fiteredrows.csv" ,1)

#a = filter_by_column("data/train_kernel_1_v4_fiteredrows.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b'])
#fileIO.save_object('data/filteredbyband',a)


'''
a = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b'])
fileIO.save_object('data/filteredbyband',a)
b = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['vi'])
fileIO.save_object('data/filteredbyvi',b)
c = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['tb'])
fileIO.save_object('data/filteredbytb',c)
d = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['tvi'])
fileIO.save_object('data/filteredbytvi',d)

e = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b','vi'])
fileIO.save_object('data/filteredbyband_vi',e)
f = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b','tb'])
fileIO.save_object('data/filteredbyband_tb',f)
g = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b','tvi'])
fileIO.save_object('data/filteredbyband_tvi',g)


h = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['vi','tb'])
fileIO.save_object('data/filteredbyvi_tb',h)
i = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['vi','tvi'])
fileIO.save_object('data/filteredbyvi_tvi',i)

j = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['b','vi','tb'])
fileIO.save_object('data/filteredbyb_vi_tb',j)

k = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['*'], ['vi','tb','tvi'])
fileIO.save_object('data/filteredbyvi_tb_tvi',k)
'''


a = filter_by_column("data/train_kernel_1_v4.csv", "data/train_kernel_1_v4_fiteredfelds.csv", ['054112895010_01'], ['b'])
fileIO.save_object('data/filteredbyband',a)