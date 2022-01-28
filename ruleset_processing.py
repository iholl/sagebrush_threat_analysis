import os
from glob import glob
import rasterio
import rasterio.merge
from osgeo import gdal
import numpy as np

def create_raster(raster, name):
    with rasterio.open("{}.tif".format(name), "w", **meta) as output_raster:
        output_raster.write(raster, 1)
        output_raster.close()

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

def merge(raster_list):
    return rasterio.merge.merge(raster_list)

raster_list = sorted(glob("*raster.tif"))

with rasterio.open(raster_list[0]) as src:
    meta = src.meta

annuals = gdal.Open(raster_list[0])
annuals_array = np.array(annuals.GetRasterBand(1).ReadAsArray())

perennials = gdal.Open(raster_list[1])
perennials_array = np.array(perennials.GetRasterBand(1).ReadAsArray())

shrubs = gdal.Open(raster_list[2])
shrub_array = np.array(shrubs.GetRasterBand(1).ReadAsArray())

trees = gdal.Open(raster_list[3])
tree_array = np.array(trees.GetRasterBand(1).ReadAsArray())

create_folder("working_data")

# TREE STEP 1: IF TREE >=21%  E: Late juniper (trees highcover)
high_tree_cover = np.where(tree_array >= 21, 13, 0)
create_raster(high_tree_cover, "working_data/high_tree_cover")

annuals_to_perennials = np.divide(annuals_array, perennials_array, out=np.zeros(annuals_array.shape, dtype=float), where=perennials_array!=0)
mod_tree_cover = np.where(((tree_array < 21) & (tree_array >= 5)), 1, 0)

# TREE STEP 2: IF 5% <= TREE > 21% AND IF AFG:PFG ratio >=1.0 (trees low-mid cover/annuals dominant)
dominant_ann = np.where(annuals_to_perennials >= 1, 1, 0)
moderate_trees_annuals_dominant = np.where(((dominant_ann > 0) & (mod_tree_cover  > 0)), 9, 0)
create_raster(moderate_trees_annuals_dominant, "working_data/moderate_trees_annuals_dominant")

# TREE STEP 3: IF 5% <= TREE > 21% AND IF  0.5 <= AFG:PFG ratio < 1.0 (trees low-mid cover/perennials slightly dominant)
sdominant_per = np.where(((annuals_to_perennials < 1) & (annuals_to_perennials >= 0.5)), 1, 0)
moderate_trees_perennials_sdominant = np.where(((sdominant_per > 0) & (mod_tree_cover > 0)), 10, 0)
create_raster(moderate_trees_perennials_sdominant, "working_data/moderate_trees_perennials_sdominant")

# TREE STEP 4: IF 5% <= TREE > 21% AND IF  0.333 <= AFG:PFG ratio < 0.5 (trees low-mid cover/perennials dominant)
dominant_per = np.where(((annuals_to_perennials < 0.5) & (annuals_to_perennials >= 0.333)), 1, 0)
moderate_trees_perennials_dominant = np.where(((dominant_per > 0) & (mod_tree_cover > 0)), 11, 0)
create_raster(moderate_trees_perennials_dominant, "working_data/moderate_trees_perennials_dominant")

# TREE STEP 5: IF 5% <= TREE > 21% AND IF 0.333 > AFG:PFG ratio (trees low-mid cover/perennials very dominant)
vdominant_per = np.where(((annuals_to_perennials < 0.333)), 1, 0)
moderate_trees_perennials_vdominant = np.where(((vdominant_per > 0) & (mod_tree_cover > 0)), 12, 0)
create_raster(moderate_trees_perennials_vdominant, "working_data/moderate_trees_perennials_vdominant")

# Mosaic tree data into tree raster
high_trees = rasterio.open("working_data/high_tree_cover.tif")
mod_tree_ann_dom = rasterio.open("working_data/moderate_trees_annuals_dominant.tif")
mod_tree_per_sdom = rasterio.open("working_data/moderate_trees_perennials_sdominant.tif")
mod_tree_per_dom = rasterio.open("working_data/moderate_trees_perennials_dominant.tif")
mod_tree_per_vdom = rasterio.open("working_data/moderate_trees_perennials_vdominant.tif")

dest, output_transform = merge([high_trees, mod_tree_ann_dom, mod_tree_per_sdom, mod_tree_per_dom, mod_tree_per_vdom])

with rasterio.open("working_data/high_tree_cover.tif") as src:
        out_meta = src.meta.copy()    

out_meta.update({"driver": "GTiff", "height": dest.shape[1], "width": dest.shape[2], "transform": output_transform})

with rasterio.open("working_data/trees_mosaic.tif", "w", **out_meta) as dest1:
        dest1.write(dest)
