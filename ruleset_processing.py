from glob import glob
import rasterio
from osgeo import gdal
import numpy as np

def unique(data_array):
    x = np.array(data_array)
    print(np.unique(x))

def frequency(raster):
    (unique, counts) = np.unique(raster, return_counts=True)
    frequencies = np.asarray((unique, counts)).T
    print(frequencies)

raster_list = sorted(glob("*.tif"))

with rasterio.open(raster_list[0]) as src:
    meta = src.meta

annuals = gdal.Open(raster_list[1])
annuals_array = np.array(annuals.GetRasterBand(1).ReadAsArray())

perennials = gdal.Open(raster_list[1])
perennials_array = np.array(perennials.GetRasterBand(1).ReadAsArray())

shrubs = gdal.Open(raster_list[2])
tree_array = np.array(shrubs.GetRasterBand(1).ReadAsArray())

trees = gdal.Open(raster_list[3])
tree_array = np.array(trees.GetRasterBand(1).ReadAsArray())

def create_raster(raster, name):
    with rasterio.open("{}.tif".format(name), "w", **meta) as output_raster:
        output_raster.write(raster, 1)
        output_raster.close()

# RULESETS

# TREE STEP 1: IF Tree >=21%  E: Late juniper (trees highcover)
high_trees = np.where(tree_array >= 21, 1, 0)
create_raster(high_trees, "high_trees")
unique(high_trees)
frequency(high_trees)

# TREE STEP 2: IF 5% <= Tree > 21% AND IF AFG:PFG ratio >=1.0 (trees low-mid cover/annuals dominant) (Value=9)
annuals_to_perennials = np.divide(annuals_array, perennials_array, out=np.zeros(annuals_array.shape, dtype=float), where=perennials_array!=0)
high_annuals = np.where(annuals_to_perennials >= 1, 1, 0)
create_raster(high_annuals, "high_annauls")
