import os
from glob import glob
from matplotlib.pyplot import close
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

def merge(list):
    return rasterio.merge.merge(list)

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

# TREE STEP 1: IF TREE >=21%  E: Late juniper (trees highcover) (11)
high_tree_cover = np.where(tree_array >= 21, 11, 0)
create_raster(high_tree_cover, "working_data/high_tree_cover")

annuals_to_perennials = np.divide(annuals_array, perennials_array, out=np.zeros(annuals_array.shape, dtype=float), where=perennials_array!=0)
mod_tree_cover = np.where(((tree_array < 21) & (tree_array >= 5)), 1, 0)
low_tree_cover = np.where((tree_array < 5), 1, 0)

# TREE STEP 2: IF 5% <= TREE > 21% AND IF AFG:PFG ratio >=1.0 (trees low-mid cover/annuals dominant) (7)
dominant_ann = np.where(annuals_to_perennials >= 1, 1, 0)
moderate_trees_annuals_dominant = np.where(((dominant_ann > 0) & (mod_tree_cover  > 0)), 7, 0)
create_raster(moderate_trees_annuals_dominant, "working_data/moderate_trees_annuals_dominant")

# TREE STEP 3: IF 5% <= TREE > 21% AND IF  0.5 <= AFG:PFG ratio < 1.0 (trees low-mid cover/perennials slightly dominant) (8)
sdominant_per = np.where(((annuals_to_perennials < 1) & (annuals_to_perennials >= 0.5)), 1, 0)
moderate_trees_perennials_sdominant = np.where(((sdominant_per > 0) & (mod_tree_cover > 0)), 8, 0)
create_raster(moderate_trees_perennials_sdominant, "working_data/moderate_trees_perennials_sdominant")

# TREE STEP 4: IF 5% <= TREE > 21% AND IF  0.333 <= AFG:PFG ratio < 0.5 (trees low-mid cover/perennials dominant) (9)
dominant_per = np.where(((annuals_to_perennials < 0.5) & (annuals_to_perennials >= 0.333)), 1, 0)
moderate_trees_perennials_dominant = np.where(((dominant_per > 0) & (mod_tree_cover > 0)), 9, 0)
create_raster(moderate_trees_perennials_dominant, "working_data/moderate_trees_perennials_dominant")

# TREE STEP 5: IF 5% <= TREE > 21% AND IF 0.333 > AFG:PFG ratio (trees low-mid cover/perennials very dominant) (10)
vdominant_per = np.where(((annuals_to_perennials < 0.333)), 1, 0)
moderate_trees_perennials_vdominant = np.where(((vdominant_per > 0) & (mod_tree_cover > 0)), 10, 0)
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

high_trees.close()
mod_tree_ann_dom.close()
mod_tree_per_sdom.close()
mod_tree_per_dom.close()
mod_tree_per_vdom.close()

# SHRUB STEP 1: IF SHRUB >= 10% AND AFG:PFG < 0.333 AND TREE < 5% (high shrub cover/perrenials dominant) (1)
high_shrub_cover = np.where(shrub_array >= 10, 1, 0)
good_shrubland = np.where(((high_shrub_cover > 0) & (vdominant_per > 0) & (low_tree_cover > 0)), 1, 0) 
create_raster(good_shrubland, "working_data/good_shrubland")

# SHRUB STEP 2: IF SHRUB >= 10% AND 0.333 <= AFG:PFG < 1 AND TREE < 5% (high shrub cover/perrenials slightly dominant) (2)
intermediate_annauals_perennials = np.where(((annuals_to_perennials >= 0.333) & (annuals_to_perennials < 1)), 1, 0)
intermediate_shrubland = np.where(((high_shrub_cover > 0 ) & (intermediate_annauals_perennials > 0) & (low_tree_cover > 0)), 2, 0)
create_raster(intermediate_shrubland, "working_data/intermediate_shrubland")

# SHRUB STEP 3: IF SHRUB >= 10% AND AFG:PFG >= 1 AND TREE < 5% (high shrub cover/annuals dominant) (3)
poor_shrubland = np.where(((high_shrub_cover > 0) & (annuals_to_perennials >= 1) & (low_tree_cover > 0)), 3, 0)
create_raster(poor_shrubland, "working_data/poor_shrubland")

# Mosaic shrubs data into tree raster
good_shurbs = rasterio.open("working_data/good_shrubland.tif")
intermediate_shrubs = rasterio.open("working_data/intermediate_shrubland.tif")
poor_shrubs = rasterio.open("working_data/poor_shrubland.tif")

dest, output_transform = merge([good_shurbs, intermediate_shrubs, poor_shrubs])

with rasterio.open("working_data/good_shrubland.tif") as src:
        out_meta = src.meta.copy()    

out_meta.update({"driver": "GTiff", "height": dest.shape[1], "width": dest.shape[2], "transform": output_transform})

with rasterio.open("working_data/shrubs_mosaic.tif", "w", **out_meta) as dest1:
        dest1.write(dest)

good_shurbs.close()
intermediate_shrubs.close()
poor_shrubs.close()

# GRASS STEP 1: IF SHRUB < 10% AND AFG:PFG < 0.333 (low shrub cover/perrenials dominant) (4)
low_shrub_cover = np.where(shrub_array < 10, 1, 0)
good_grassland = np.where(((low_shrub_cover > 0) & (annuals_to_perennials < 0.333)), 4, 0)
create_raster(good_grassland, "working_data/good_grassland")

# GRASS STEP 1: IF SHRUB < 10% AND AFG:PFG < 0.333 (low shrub cover/perrenials slightly dominant) (5)
intermediate_grassland = np.where(((low_shrub_cover > 0) & (intermediate_annauals_perennials > 0)), 5, 0)
create_raster(intermediate_grassland, "working_data/intermediate_grassland")

# GRASS STEP 3: IF SHRUB < 10% AND AFG:PFG >= 1 (low shrub cover/annuals dominant) (6)
poor_grassland = np.where(((low_shrub_cover > 0) & (annuals_to_perennials >= 1)), 6, 0)
create_raster(poor_grassland, "working_data/poor_grassland")

# Mosaic grass data into tree raster
good_grass = rasterio.open("working_data/good_grassland.tif")
intermediate_grass = rasterio.open("working_data/intermediate_grassland.tif")
poor_grass = rasterio.open("working_data/poor_grassland.tif")

dest, output_transform = merge([good_grass, intermediate_grass, poor_grass])

with rasterio.open("working_data/good_grassland.tif") as src:
        out_meta = src.meta.copy()    

out_meta.update({"driver": "GTiff", "height": dest.shape[1], "width": dest.shape[2], "transform": output_transform})

with rasterio.open("working_data/grass_mosaic.tif", "w", **out_meta) as dest1:
        dest1.write(dest)

good_grass.close()
intermediate_grass.close()
poor_grass.close()

# Mosaic all data into final raster
tree_raster = rasterio.open("working_data/trees_mosaic.tif")
shrub_raster = rasterio.open("working_data/shrubs_mosaic.tif")
grass_raster = rasterio.open("working_data/grass_mosaic.tif")

dest, output_transform = merge([tree_raster, shrub_raster, grass_raster])

with rasterio.open("working_data/trees_mosaic.tif") as src:
        out_meta = src.meta.copy()    

out_meta.update({"driver": "GTiff", "height": dest.shape[1], "width": dest.shape[2], "transform": output_transform})

with rasterio.open("working_data/complete_mosaic.tif", "w", **out_meta) as dest1:
        dest1.write(dest)

tree_raster.close()
shrub_raster.close()
grass_raster.close()
