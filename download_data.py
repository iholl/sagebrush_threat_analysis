import os
from osgeo import gdal

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

# coordinates for bounding box to limit the extent of the data
data_extent = [-120.1, 41.5, -119.1, 41]
# date range for downloading annual data
date_min = 2000
date_max = 2020
date_list = list(range(date_min, date_max + 1))
# create a folder for the data if no does not exist
create_folder("data")
# loop through all the dates in the range and downloads to the data folder
for date in date_list:
    url = "/vsicurl/http://rangeland.ntsg.umt.edu/data/rap/rap-vegetation-cover/v3/vegetation-cover-v3-{}.tif".format(date)
    raster = gdal.Open(url)
    gdal.Translate("data/output_{}.tif".format(date), raster, projWin = data_extent)
    raster = None