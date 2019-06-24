#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import os
import fiona
import tempfile
from collections import Counter
from sub_network import SubNetwork
import basin_grids

#from pprint import pprint


class Ppts2Net:
    
    def __init__(self, ptsfile, ptslayer=None, 
                 riverdb='../data/HydroSHEDS.gpkg', rlayer='Rivers'):
        self.ptsfile = ptsfile
        self.ptslayer = ptslayer
        self.riverdb = riverdb
        self.rlayer = rlayer
        self.processors = 4
        

    def pt2net(self, ppt):
        '''
        Takes one point in GeoJSON and retuns the snapped point in GeoJSON
        format and the accompanied upstream river network as a dictionary.
        
        Args:
          ppt(dict) : The pouring point in GeoJSON format
          
        Returns:
          ppt(dict)     : The pouring point snapped to the nearest river line.
          riv_net(dict) : The river network upstream from the pouring point
                          in GeoJSON format.
        '''
        
        pinst = SubNetwork(ppt)
        pinst.snap()
        pinst.target_river()
        pinst.retrieve_upstream()
        return (pinst.ppt, pinst.river_network)
    
    def ppt2geojson(self, ppt):
        '''
        Takes a single pouring point and returns a geojson containg the 
        catchment are river lines, oroginal point and the snapped pouring 
        point.
        
        Args:
           ppt(dict) : The pouring point in GeoJSON format and EPSG 4326
           
        Returns:
           gjson(dict) : A GeoJSON containing
                         1. The original point
                         2. The snapped point
                         3. The catchment area
                         4. The river lines
        '''
        
        spt, rivers = self.pt2net(ppt)
        
        
        
    def ppts2gpkgs(self, target_folder, id_name='ID_Name'):
        '''
        Creates a folder for each pouring point with the 'id_name' name.
        The folder will contain all the data for on pourin point.
        If the folder already exists this calculation will be skipped.
        If there are duplicates in the 'id_name' column the user is warned
        and these calculations are also skipped.
        '''
        
        self.ppts_data = list()
        self.target_folder = target_folder
        self.id_name = id_name
        with fiona.open(self.ptsfile, layer=self.ptslayer) as source:
            self.ptcrs = source.crs
            self.ptschema = source.schema
            self.ptschema['properties']['river_id'] = 'str'
            for item in source:
                self.ppts_data.append(item)
                
        # Check that all 'id-names' are unique
        projects = list()
        for item in self.ppts_data:
            projects.append(item['properties'][id_name])
        count = Counter(projects)
        skip = set()
        if len(count) == len(projects):
            pass
        else:
            for key, value in count.items():
                if value > 1:
                    skip.add(key)
                    print(key, 'occurs more than once. All these names will be skipped.')
                    
        existing_dirs = os.listdir(target_folder)
        skip = skip.union(set(existing_dirs))
        arguments = list()
        for item in self.ppts_data:
            for proj in set(projects)-skip:
                if proj == item['properties'][id_name]:
                    arguments.append(item)
        self.ppts_data = arguments
        
        for item in self.ppts_data:
            rnet = self.pt2net(item)
            newdir = item['properties'][id_name]
            path = os.path.join(target_folder, newdir)
            os.mkdir(path)
            self.net2gpkg(rnet[0], rnet[1])
            basin_grids.grids_from_gpkg_extent(path, 'HydroSHEDS_15s.gpkg')
            

    def net2gpkg(self, pt, rivnet):
        '''
        Takes a pouring point, the resulting upstream river and writes the 
        data to a geopackage.
        '''
        
        folder = pt['properties'][self.id_name]
        target = os.path.join(self.target_folder, folder, 
                              'HydroSHEDS_15s.gpkg')
        
        with fiona.open(target, 'w', layer='pour_point_15s', 
                        driver='GPKG', schema=self.ptschema, 
                        crs=self.ptcrs) as sink:
            sink.write(pt)
            
        with fiona.open(self.riverdb, layer=self.rlayer) as source:
            schema = source.schema
            crs = source.crs
            
        rivlist = list()
        for key, value in rivnet.items():
            rivlist.append(value)
        
        with fiona.open(target, 'w', layer='river_net_15s', 
                        driver='GPKG', schema=schema, crs=crs) as sink:
            sink.writerecords(rivlist)
            
        
                