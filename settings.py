import sys
if sys.version_info[0] == 2:
    from ConfigParser import ConfigParser as parser
elif sys.version_info[0] == 3:
    from configparser import ConfigParser as parser
else:
    print('python version 2 or 3 are required')
    sys.exit()

import json
import utility

#################### parsing the main.ini ##########################


parser = parser()
parser.read("./settings/main.ini")

#print(parser.sections())

indata = parser['indata']
working_directory = indata.get("working_directory",".")

field_name = indata.get("field_name","")
if not field_name: raise ValueError("input field_name is mandatory")

data_extraction = parser['data_extraction']
mean = data_extraction.getboolean("mean", False)
#the band combinations to use in format [(1,2),(1,3),....]; use * for all combinations; [] for no combinations
band_combinations = data_extraction.get("band_combinations","[]")
# a percentage of pixels to consider during polygons to raster intersection (>0); use 100 if no subset
pixel_subset = data_extraction.getint("pixel_subset", 100)
if pixel_subset == 100:
    pixel_subset = None
# the single band combination to use for charting the NDI in format [(1,2)]; only one combination is now possible
NDI_chart_combinations = data_extraction.get("NDI_chart_combinations" , "[(7,5)]")
#the nodatavalue to assign when polygons falls outside the raster (this works when mean == True)
nodatavalue =  data_extraction.get("nodatavalue", None)

haralick = parser['haralick']
#folder tha will contain the input image for heralick
hara_dir = haralick.get("hara_dir","." )
# heralick image suffix format (comma separated list)
haralick_format = haralick.get("haralick_format","tif")
#simple, advanced, higher?
haralick_image_type = haralick.get("haralick_image_type","simple")
#folder tha will contain the input ndi images for heralick
hara_ndi_dir =  haralick.get("hara_ndi_dir" ,"." )
# heralick ndi image suffix format (comma separated list)
haralick_ndi_format =haralick.get("haralick_ndi_format" , "tif")
#simple, advanced, higher?
haralick_ndi_type = haralick.get("haralick_ndi_type","simple")

skll = parser['skll']
skll_dir = skll.get("skll_dir","." )

boruta = parser['boruta']
boruta_dir = boruta.get("boruta_dir","." )

classification = parser['classification']
#percentage of validation data
validation_data = classification.getint("validation_data", 25)
# classified raster name prefix
out_name =   classification.get("out_name", "classify.tif")
#tile size used during classification
tile_size = classification.getint("tile_size", 1024)


ipyparallel = parser['ipyparallel']
parallelize = ipyparallel.getboolean('parallelize', False)
engine_messages = ipyparallel.getboolean('engine_messages', False)

############# parsing the paths.json #########################


def extract_haralick_images(tag0, tag1, tag2 ):
    """ fill in the dictionary with paths for haralick images
    :param tag0: "haralick_images" or "haralick_ndi"
    :param tag1: object y
    :param tag2: object image
    :return:
    """


    tag1[tag0] = {}
    tag1[tag0]["simple"] = {}
    tag1[tag0]["advanced"] = {}
    tag1[tag0]["higher"] = {}

    for n,haralick_images in enumerate(tag2[tag0]):

        if haralick_images["type"]== "folder":

            if haralick_images["name"]== "simple":
                x = tag1[tag0]["simple"]
                basepath = haralick_images["basepath"] + "/" + haralick_images["name"]
                x["basepath"] = basepath
                x["images"] = []

                #get all the haralick images in the folder
                x["images"] += utility.filter_files(basepath,haralick_images["formats"])

            elif haralick_images["name"]== "advanced":
                x = tag1[tag0]["advanced"]
                basepath = haralick_images["basepath"] + "/" + haralick_images["name"]
                x["basepath"] = basepath
                x["images"] = []
                #get all the haralick images in the folder
                x["images"] += utility.filter_files(basepath,haralick_images["formats"])

            elif haralick_images["name"]== "higher":
                x = tag1[tag0]["higher"]
                basepath = haralick_images["basepath"] + "/" + haralick_images["name"]
                x["basepath"] = basepath
                x["images"] = []
                #get all the haralick images in the folder
                x["images"] += utility.filter_files(basepath,haralick_images["formats"])

            else:
                raise ValueError("haralick image name can be  - simple advanced higher - ")

        else:
            raise NotImplementedError("only folders are possible")


f= open("./settings/paths.json")
j=json.load(f)

#here we initilize the data structure

paths = {}

#iterate all the satellite images
for i,im in enumerate(j["images"]):

    paths[i] = {}

    print("this is image ",i)
    image = im["image"]
    print(image["type"])

    if image["type"] == "folder":

        paths[i]["type"] = image["type"]
        paths[i]["name"] = image["name"]
        paths[i]["basepath"] = image["basepath"] + "/" + image["name"]

        paths[i]["content"] = []

        for n,content in enumerate(image["content"]):
            paths[i]["content"].append({})
            paths[i]["content"][n]["raster"] = content["raster"]
            paths[i]["content"][n]["shape"] = content["shapes"]
            paths[i]["content"][n]["mask"] = content.get("mask", None)

        y = paths[i]
        #y["haralick_images"] = {}
        #y["haralick_images"]["simple"] = {}
        #y["haralick_images"]["advanced"] = {}
        #y["haralick_images"]["higher"] = {}

        extract_haralick_images(tag0="haralick_images", tag1=y, tag2=image)

        y = paths[i]

        extract_haralick_images(tag0="haralick_ndi", tag1=y, tag2=image)

    else:
        raise NotImplementedError("only folders are possible")



if __name__ == "__main__":

    print("working_directory:" ,working_directory)
    #print("shapes:"  ,shapes)
    print("field_name:" ,field_name)
    #print("image:" ,image)
    #print("tree_mask:" ,tree_mask)

    print()
    print("mean:" ,mean)
    print("band_combinations:" ,band_combinations)
    print("pixel_subset:" ,pixel_subset)
    print("NDI_chart_combinations:" ,NDI_chart_combinations)

    print()
    print("hara_dir:" ,hara_dir)
    print("haralick_format:" ,haralick_format)
    print("haralick_image_type:" ,haralick_image_type)
    print("hara_ndi_dir:" ,hara_ndi_dir)
    print("haralick_ndi_format:" ,haralick_ndi_format)
    print("haralick_ndi_type:" ,haralick_ndi_type)

    print()
    print("skll_dir:" ,skll_dir)
    print()
    print("boruta_dir:" ,boruta_dir)
    print()
    print("validation_data:" ,validation_data)
    print("out_name:" ,out_name)
    print("tile_size:" ,tile_size)
    print()
    print("parallelize:" ,parallelize)
    print("#####################")
    print(paths)

