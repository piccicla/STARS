import sys
if sys.version_info[0] == 2:
    from ConfigParser import ConfigParser as parser
elif sys.version_info[0] == 3:
    from configparser import ConfigParser as parser
else:
    print('python version 2 or 3 are required')
    sys.exit()

parser = parser()
parser.read("./settings/main.ini")

#print(parser.sections())


indata = parser['indata']
working_directory = indata.get("working_directory",".")
shapes = indata.get("shapes","")
if not shapes: raise ValueError("input shapes are mandatory")
field_name = indata.get("field_name","")
if not field_name: raise ValueError("input field_name is mandatory")
image = indata.get( "image","")
if not image: raise ValueError("input image is mandatory")
tree_mask = indata.get("tree_mask","")
if not tree_mask: tree_mask = None


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

heralick = parser['heralick']
#folder tha will contain the input image for heralick
hera_dir = heralick.get("hera_dir","." )
# heralick image suffix format (comma separated list)
heralick_format = heralick.get("heralick_format","tif")
#folder tha will contain the input ndi images for heralick
hera_ndi_dir =  heralick.get("hera_ndi_dir" ,"." )
# heralick ndi image suffix format (comma separated list)
heralick_ndi_format =heralick.get("heralick_ndi_format" , "tif")

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



if __name__ == "__main__":

    print("working_directory:" ,working_directory)
    print("shapes:"  ,shapes)
    print("field_name:" ,field_name)
    print("image:" ,image)
    print("tree_mask:" ,tree_mask)

    print()
    print("mean:" ,mean)
    print("band_combinations:" ,band_combinations)
    print("pixel_subset:" ,pixel_subset)
    print("NDI_chart_combinations:" ,NDI_chart_combinations)

    print()
    print("hera_dir:" ,hera_dir)
    print("heralick_format:" ,heralick_format)
    print("hera_ndi_dir:" ,hera_ndi_dir)
    print("heralick_ndi_format:" ,heralick_ndi_format)
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