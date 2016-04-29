# -*- coding: utf-8 -*-


#1) Creating a big and empty raster, same as the original image
m = np.zeros((1157, 1553))


#2) We fill the matrix with each ONE value found in each of the 45 little rasters, recycling variable m (defined in step 1)


if rastermask: #if we have a mask (e.g trees)
    pixelmasker = pixelmask.ReadAsArray(xoff, yoff, xcount, ycount).astype(np.float)
    datamask = datamask * pixelmasker
    m = utility.fill_matrix(m, xoff, yoff, xcount, ycount, datamask)

#3) The code of the filling function
def fill_matrix(m, xoff, yoff, xcount, ycount, pixelmask):
    # print("xoff: {0}, yoff: {1}, xcount: {2}, ycount: {3}".format(xoff, yoff, xcount, ycount))
    for i in range(0, ycount):
        for j in range(0, xcount):
            if pixelmask[0, i, j] == 1:
                m[i+yoff][j+xoff] = 1
    return m

#4) Change type of return of the function, by also returning the big raster with the selected pixels

return (outdata, uniqueLabels, columnNames, m)

#5) Getting this raster in the test file, then writing it to tiff
data, uniqueLabels, columnNames, m = getPixelValues.getGeneralSinglePixelValues(path_shape, path_tif, label_col, [img_name], rastermask=path_mask, subset=None, returnsubset = False)
utility.write_array_as_tiff(m, tif, path_out, name)

#6) My small function to write TIFF files
def write_array_as_tiff(m, tifsrc, path_out, name):
    rows = tifsrc.RasterXSize
    cols = tifsrc.RasterYSize
    prj_wkt = tifsrc.GetProjectionRef()
    geotransform = tifsrc.GetGeoTransform()
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(path_out.format(name), rows, cols, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(prj_wkt)
    outband=ds.GetRasterBand(1)
    outband.WriteArray(m)
    ds = None
    outband = None

