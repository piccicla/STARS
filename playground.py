# -*- coding: utf-8 -*-

#this is just a playground file to test things

import skll.utilities as r
import os
import warnings

def run_script(params):
    """ execute a python script
    :param params: a list of strings [ 'python version' , 'parameters']
    :return: script output
    """
    import subprocess
    params.insert(0,"py")
    p = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #print(params)
    out, err= p.communicate()
    #return bytes.decode(out)+'\n'+ bytes.decode(err)
    return bytes.decode(out), bytes.decode(err)

#get the path of skll.utilities directory

#path = os.path.dirname(r.__file__)


#call the skll run_experiment.py script
#run_script(["-3.5", path+"/"+"run_experiment.py"])


#call the skll run_experiment.py script
#print(run_script(["-3.5", path+"/"+ "skll_convert.py", r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\dataMean.tsv",
#                  r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\dataMean.jsonlines","-l","label"]))

#path = r"C:\Python35_64\Lib\site-packages\skll\utilities"

#warnings.simplefilter("ignore")

#call the skll run_experiment.py script
#print(run_script(["-3.5", path+"/"+ "run_experiment.py", r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\skllTutorial\examples\titanic\evaluate_tuned.cfg"]))


inpath = r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing"
outpath = r"D:\ITC\courseMaterial\module13GFM2\2015\code\STARS\processing\indexes"

bandA='1'
bandB='2'

print('calculating NDI '+bandA+'-'+ bandB+"/"+bandA+'+'+ bandB)
msg, err = run_script(["-3.5", "gdal_calc.py","-A", inpath+r"\raster.tif","--A_band="+bandA, "-B",inpath+r"\raster.tif","--B_band="+bandB,"--outfile="+outpath+r"\NDI"+bandA+"_"+bandB+".tif","--type=Float32",'--calc="((A-B)/(A+B))"'])
if err: print(err)


