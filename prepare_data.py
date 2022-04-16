import os
import rasterio

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

def extract_bands(multiband_raster):
    dataset = rasterio.open("data/{}".format(multiband_raster)) 
    # loop through bands in list and extract them to individual rasters
    for band in band_list:  
        source_band = dataset.read(band)
        # create a folder for each band if one does not exist
        folder_name = "band_{}".format(band)
        create_folder(folder_name)
        # write each require band from each year to the designated folder
        with rasterio.open(
            "{}/{}".format(folder_name, multiband_raster),
            "w",
            driver="GTiff",
            height=source_band.shape[0],
            width=source_band.shape[1],
            count=1,
            dtype=source_band.dtype,
            crs=dataset.crs,
            transform=dataset.transform,
        ) as dst:
            dst.write(source_band, 1)
            dst.close()
    
# list of bands to be extracted: annuals, perennials, shrubs and trees
band_list = [1,4,5,6]
#create a list of all the rasters in the data folder
raster_list = os.listdir("data")
# function to extract the bands from a raster is used twice in the code
for raster in raster_list:
    extract_bands(raster)
