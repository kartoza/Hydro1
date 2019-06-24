#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import fiona
from shapely.geometry import shape
from shapely.geometry import Point
from point_snap import PointSnap
from upstream import upstream

class SubNetwork(PointSnap):
    
    def __init__(self, ppt, riverdb='../data/HydroSHEDS.gpkg', layer='Rivers'):
        self.ppt = ppt
        self.riverdb = riverdb
        self.layer = layer
        self.ndx = False
        
    
    def target_river(self):
        '''
        Extract the target river line as identified by the pour point.
        The line is also shortened up to to the snapped point.
        '''
        
        self.river_network = dict()
        with fiona.open(self.riverdb, layer=self.layer) as source:
            self.rcrs = source.crs
            self.rschema = source.schema
            #for item in self.ppts:
            pt = shape(self.ppt['geometry'])
            bfpt = pt.buffer(0.005)
            hits = list(source.items(bbox=(bfpt.bounds)))
            for line in hits:
                if line[1]['id'] == self.ppt['properties']['river_id']:
                    self.river_network[line[0]] = line[1]
                    continue
                    
        change = list()
        for key, value in self.river_network.items():
            firstline = shape(value['geometry'])
            coords = list(firstline.coords)
            #print(self.upstream_node)
            x1 = self.upstream_node[0]
            y1 = self.upstream_node[1]
            node1 = Point(x1, y1)
            pour_pt = shape(self.ppt['geometry'])
            ppt_x = self.ppt['geometry']['coordinates'][0]
            ppt_y = self.ppt['geometry']['coordinates'][1]
            newline = []
            # Check if the Pour Point snapped to a node
            ppt_s2_node = False
            if node1.distance(pour_pt) < 0.001:
                ppt_s2_node = True
            for coord in coords:
                newline.append(coord)
                current_pt = Point(coord)
                if node1.distance(current_pt) < 0.001:
                    if ppt_s2_node == False:
                        newline.append(coord)
                        newline.append((ppt_x, ppt_y))
                        break
                    elif ppt_s2_node == True:
                        newline.append(coord)
                        break
            change.append((key, newline))
        for item in change:
            self.river_network[item[0]]['geometry']['coordinates'] = item[1]
            
    
    def retrieve_upstream(self):
        '''
        Trace the all the upstream lines from the targeted river line(s).
        '''
        
        self.river_network = upstream(self.river_network)