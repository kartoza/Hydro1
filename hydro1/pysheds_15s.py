#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import os
import numpy as np
import fiona
from pysheds.grid import Grid
from collections import OrderedDict


def watershed_15s(path):
    '''
    From path to the project a 15s watershed is generated and added to
    the geopackage.
    '''
    
    grid = Grid.from_raster(os.path.join(path, 'dir_15s.tif'), data_name='dir')
    grid.read_raster(os.path.join(path, 'acc_15s.tif'), data_name='acc')
    
    with fiona.open(os.path.join(path, 'HydroSHEDS_15s.gpkg'), 
                layer='pour_point_15s') as source:
        crs = source.crs
        for pt in source:
            coord = pt['geometry']['coordinates']
            x, y = coord[0], coord[1]
    
    xy = np.column_stack([x, y])
    new_xy = grid.snap_to_mask(grid.acc > 100, xy, return_dist=False)
    new_x, new_y = new_xy[0][0], new_xy[0][1]
    
             #N    NE    E    SE    S    SW    W    NW
    dirmap = (64,  128,  1,   2,    4,   8,    16,  32)
    
    grid.catchment(data='dir', x=new_x, y=new_y, dirmap=dirmap, 
                   out_name='catch',recursionlimit=15000, xytype='label')
    
    grid.clip_to('catch')
    shapes = grid.polygonize()
    
    for item in shapes:
        geom = item[0]
        
    schema = {'geometry': 'Polygon',
              'properties': OrderedDict([])}
    
    with fiona.open(os.path.join(path, 'HydroSHEDS_15s.gpkg'), 
                    'w', layer='catchment_15s', driver='GPKG', 
                    schema=schema, crs=crs) as sink:
        data = dict()
        data['geometry'] = geom
        data['properties'] = OrderedDict()
        sink.write(data)