#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import os
import tempfile
import subprocess
import multiprocessing
import fiona
from shapely.geometry import Polygon


layers = ('con_3s_ndx', 'dir_15s_ndx', 'dir_3s_ndx', 
              'acc_15s_ndx', 'acc_3s_ndx')
db = '../data/HydroSHEDS.gpkg'


def grid_merge_clip(grids, extent, output):
    '''
    Uses GDAL to merge all the files in the grids list. The merged files 
    are then clipped to the extent given. The results are written 
    
    Args:
      grids(list)   : A list of the grid file to be merged.
      extent(tuple) : The bounds of the region to be clipped (x1, y1, x2, y2)
      output(str)   : The path to the resulting grid files.
    '''
    
    STDLOG = '../temp/processing.log'
    ERRLOG = '../temp/processing.error.log'

    logstd = open(STDLOG, 'a')
    logerr = open(ERRLOG, 'a')

    with tempfile.TemporaryDirectory() as tempdir:
    
        list_of_grid_files = os.path.join(tempdir, 'list_of_grid_files.txt')
        with open(list_of_grid_files, 'w') as sink:
            for item in grids:
                print(item, file=sink)
        
        cmd = ('gdalbuildvrt', '-input_file_list', list_of_grid_files, 
               os.path.join(tempdir, 'vrt_of_files.vrt'))
        subprocess.run(cmd, stdout=logstd, stderr=logerr)
        
        x1, y1, x2, y2 = extent
        cmd = ('gdal_translate', '-projwin', str(x1), str(y2), 
               str(x2), str(y1), '-of', 'GTiff',
               os.path.join(tempdir, 'vrt_of_files.vrt'), 
               output)
        subprocess.run(cmd, stdout=logstd, stderr=logerr)
    

def grids_from_gpkg_extent(path, gpkg):
    '''
    Obtain the extent of the basin from the 15 second river network.
    The grids from HydroSHEDS are then merged and clipped to the extent
    '''
    
    with fiona.open(os.path.join(path, gpkg), 
                    layer='river_net_15s') as source:
        x1, y1, x2, y2 = source.bounds
        grid_size = 0.0008333
        cells_buff = 120
        basin_poly = Polygon([(x1, y1), (x1, y2), 
                              (x2, y2), (x2, y1)])
        basin_bounds = (basin_poly.buffer(grid_size*cells_buff)).bounds
        
    arguments = list()
    for layer in layers:
        with fiona.open(db, layer=layer) as source:
            hits = list(source.items(bbox=basin_bounds))
            grids = list()
            for item in hits:
                grids.append(item[1]['properties']['File'])
        output = os.path.join(path, layer[:-4]+'.tif')
        arguments.append([grids, basin_bounds, output])
        
    #for arg in arguments:
        #grid_merge_clip(arg[0], arg[1], arg[2])

    process_num = 4
    pool = multiprocessing.Pool(process_num)
    for arg in arguments:
        pool.apply_async(grid_merge_clip, args=(arg[0], arg[1], arg[2]))
    pool.close()
    pool.join()
    
    
def grid_from_extent(path, extent):
    '''
    from a given extent merge and clip of the raster is done. A path to 
    the raster is returned.
    '''
    
    grid_size = 0.0008333
    cells_buff = 120
    
    
