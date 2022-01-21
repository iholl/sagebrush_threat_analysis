import os
import rasterio
import numpy as np

def average_rasters(raster_list):
    # initialize list to store all bands
    input_rasters = []
    # loop through all the rasters in the list and append them to the list
    for raster in raster_list:
        raster_path = "{}/{}".format(band_name, raster)
        raster_layer = rasterio.open(raster_path)
        layer = raster_layer.read(1)
        input_rasters.append(layer)
    # stack rastes based on input raster list and take the mean
    raster_stack = np.stack(input_rasters)
    mean_array = np.mean(raster_stack, axis=0)
    # write the mean raster to the base directory
    with rasterio.open(
        "{}_mean_raster.tif".format(band_name),
        "w", 
        driver="GTiff",
        width=raster_layer.width,
        height=raster_layer.height,
        count=1,
        crs=raster_layer.crs,
        transform=raster_layer.transform,
        dtype=rasterio.uint8
    ) as mean_raster:
        mean_raster.write(mean_array, 1)
        mean_raster.close()
# required bands: annuals, perennials, shrubs, trees
band_list = [1,4,5,6]
# loop through the folders and average all the rasters in each folder
for band in band_list:
    band_name = "band_{}".format(band)
    data_list = os.listdir(band_name)
    average_rasters(data_list)
    