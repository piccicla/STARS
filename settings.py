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



def parse_ini(inpt = "./settings/main.ini" ):
    """
    :param inpt:
    :return:
    """

    out = {}

    p = parser()
    p.read(inpt)

    #print(parser.sections())

    indata = p['indata']

    out["working_directory"] = indata.get("working_directory",".")
    field_name = indata.get("field_name","")
    if not field_name: raise ValueError("input field_name is mandatory")
    else: out["field_name"]=field_name

    data_extraction = p['data_extraction']
    out["mean"] = data_extraction.getboolean("mean", False)
    #the band combinations to use in format [(1,2),(1,3),....]; use * for all combinations; [] for no combinations
    out["band_combinations"] = data_extraction.get("band_combinations","[]")
    # a percentage of pixels to consider during polygons to raster intersection (>0); use 100 if no subset
    pixel_subset = data_extraction.getint("pixel_subset", 100)
    if pixel_subset == 100:
        pixel_subset = None
    else: out["pixel_subset"] = pixel_subset
    # the single band combination to use for charting the NDI in format [(1,2)]; only one combination is now possible
    out["NDI_chart_combinations"] = data_extraction.get("NDI_chart_combinations" , "[(7,5)]")

    #the nodatavalue to assign when polygons falls outside the raster (this works when mean == True)
    out["nodatavalue"] =  data_extraction.get("nodatavalue", None)


    #this is not necessary anymore because now the heralick paths are in thejson file
    #haralick = p['haralick']
    #folder tha will contain the input image for heralick
    #out["hara_dir"] = haralick.get("hara_dir","." )
    # heralick image suffix format (comma separated list)
    #out["haralick_format"] = haralick.get("haralick_format","tif")
    #simple, advanced, higher?
    #out["haralick_image_type"] = haralick.get("haralick_image_type","simple")
    #folder tha will contain the input ndi images for heralick
    #out["hara_ndi_dir"] =  haralick.get("hara_ndi_dir" ,"." )
    # heralick ndi image suffix format (comma separated list)
    #out["haralick_ndi_format"] =haralick.get("haralick_ndi_format" , "tif")
    #simple, advanced, higher?
    #out["haralick_ndi_type"] = haralick.get("haralick_ndi_type","simple")

    skll = p['skll']
    out["skll_dir"] = skll.get("skll_dir","." )

    boruta = p['boruta']
    out["boruta_dir"] = boruta.get("boruta_dir","." )

    classification = p['classification']
    #percentage of validation data
    out["validation_data"] = classification.getint("validation_data", 25)
    # classified raster name prefix
    out["out_name"] =   classification.get("out_name", "classify.tif")
    #tile size used during classification
    out["tile_size"] = classification.getint("tile_size", 1024)

    ipyparallel = p['ipyparallel']
    out["parallelize"] = ipyparallel.getboolean('parallelize', False)
    out["engine_messages"] = ipyparallel.getboolean('engine_messages', False)
    out["max_processes"] = ipyparallel.getint("max_processes", 4)

    return out

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


def parse_json(inpt = "./settings/paths.json"):
    """
    :param inpt:
    :return:
    """

    f= open(inpt)
    j=json.load(f)

    #here we initilize the data structure

    paths = {}

    #iterate all the satellite images
    for i,im in enumerate(j["images"]):

        paths[i] = {}

        #print("this is image ",i)
        image = im["image"]
        #print(image["type"])

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

    return paths

if __name__ == "__main__":


    out = parse_ini()
    print("working_directory:" ,out["working_directory"])
    #print("shapes:"  ,shapes)
    print("field_name:" ,out["field_name"])
    #print("image:" ,image)
    #print("tree_mask:" ,tree_mask)

    print()
    print("mean:" ,out["mean"])
    print("band_combinations:" ,out["band_combinations"])
    print("pixel_subset:" ,out["pixel_subset"])
    print("NDI_chart_combinations:" ,out["NDI_chart_combinations"])

    #this is not necessary anymore because the heralik paths are now in the json file
    #print()
    #print("hara_dir:" ,out["hara_dir"])
    #print("haralick_format:" ,out["haralick_format"])
    #print("haralick_image_type:" ,out["haralick_image_type"])
    #print("hara_ndi_dir:" ,out["hara_ndi_dir"])
    #print("haralick_ndi_format:" ,out["haralick_ndi_format"])
    #print("haralick_ndi_type:" ,out["haralick_ndi_type"])

    print()
    print("skll_dir:" ,out["skll_dir"])
    print()
    print("boruta_dir:" ,out["boruta_dir"])
    print()
    print("validation_data:" ,out["validation_data"])
    print("out_name:" ,out["out_name"])
    print("tile_size:" ,out["tile_size"])
    print()
    print("parallelize:" ,out["parallelize"])
    print("#####################")

    paths = parse_json()
    print(paths)

