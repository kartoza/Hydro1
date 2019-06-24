#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import math
import fiona
from rtree import index
from shapely.geometry import shape
from shapely.geometry import Point
from shapely.geometry import LineString


class PointSnap:
    
    def __init__(self, ppt, riverdb='../data/HydroSHEDS.gpkg', layer='Rivers'):
        self.ppt = ppt
        self.riverdb = riverdb
        self.layer = layer
        self.ndx = False
        
        
    def angle(self, x1,y1,x2,y2):
        '''Determines the angle of a given line in degrees'''
        return math.atan2(y1-y2,x1-x2)*180/math.pi
    
    
    def pt2line(self, point, line):
        '''
        Takes a point tuple and a two point line tuple. If the 
        point is not perpendicular to the line segment a False 
        is returned. Otherwise meta data are returned as 
        specified in Returns.
      
        Args: 
          point (tuple): (x1, y1)
          line  (tuple): (x1, y1, x2, y2) 
      
        Returns: 
          tuple :(Px, Py) The position of the point on the line
                 perpendicular to the original given point
          float :Distance from the original given point to the
                 line
          str   :LHS or RHS from the line
          float :The length of the intersect point down the line 
        '''
        
        Ax, Ay, Bx, By = line
        Cx, Cy = point
        L = ((Bx-Ax)**2+(By-Ay)**2)**0.5
        r = ((Cx-Ax)*(Bx-Ax)+(Cy-Ay)*(By-Ay))/L**2
        # Lenth down the line
        length = r*L
        if r > 1 or r < 0: 
            return False
        Px = Ax+r*(Bx-Ax)
        Py = Ay+r*(By-Ay)
        dist = ((Cx-Px)**2+(Cy-Py)**2)**0.5
        ang = self.angle(Ax,Ay,Bx,By)-self.angle(Px,Py,Cx,Cy)
        if ang < 0:
            side = 'LHS'
        else:
            side = 'RHS'
        return ((Px, Py), dist, side, length)
            
            
    def loadrivers(self, searchradius):
        '''
        Loads the river lines from an indexed geospatial file within
        the search radius and index all the river straight line
        segments using rtree.
        
        Args:
          searchradius (float): All river lines within this radius is loaded
          river_data (str)    : Filename of the river lines
          layername (str)     :The layer name of the river data set
        '''
        
        with fiona.open(self.riverdb, layer=self.layer) as source:
            rlines = dict()
            extent = ((shape(self.ppt['geometry'])).buffer(searchradius)).bounds
            hits = list(source.items(bbox=(extent)))
            for item in hits:
                rlines[item[0]] = item[1]
                    
        self.line_idx = index.Index()
        lcount = 0
        self.nd_idx = index.Index()
        ncount = 0
    
        for key, value in rlines.items():
        
            fid = value['id']
            rline = shape(value['geometry'])
            coords = list(rline.coords)
            
            for i, coord in enumerate(coords):
                
                if i == 0:
                    continue
                    
                # Don't add begin and end nodes as possible snap points
                # Todo: Add end point if it is a discharge
                if i != len(coords)-1:
                    x, y = coord[0], coord[1]
                    prec = (fid, (x, y))
                    node = Point(x, y)
                    self.nd_idx.insert(ncount,(node.bounds), obj=prec)
                    ncount += 1
                    
                # Line Segments
                x1, y1 = coords[i-1][0], coords[i-1][1]
                x2, y2 = coord[0], coord[1]
                lrec = (fid, (x1, y1, x2, y2))
                segment = LineString([(x1, y1), (x2, y2)])
                self.line_idx.insert(lcount,(segment.bounds), obj=lrec)
                lcount += 1
                
                
    def snap(self):
        '''
        Revise the pouring point (self.ppt) with the changed coordinates 
        that is snapped to the nearest line segment or node
        which excludes beginning and end nodes.
        '''
        
        if self.ndx is False:
            self.loadrivers(0.1)
        snap_data = list()
        point = list((shape(self.ppt['geometry'])).coords)[0]
        nearest_node = list(self.nd_idx.nearest(((shape(self.ppt['geometry'])).bounds),1, objects=True))
        nd_fid = nearest_node[0].object[0]
        x, y = nearest_node[0].object[1]
        # Distance to nearest node
        nd_dist = shape(self.ppt['geometry']).distance(Point(x, y))
        
        # The 10 closest line segments to the pouring point
        cl10 = list(self.line_idx.nearest(((shape(self.ppt['geometry'])).bounds), 10, objects=True))
        for line in cl10:
            fid = line.object[0]
            properties = self.pt2line(point, line.object[1])
            if properties is not False:
                dist = properties[1]
                snap_data.append((dist, (properties[0]), fid, line.object[1]))
        snap_data.sort()
        
        if len(snap_data) == 0 or snap_data[0][0] > nd_dist:
            self.ppt['geometry']['coordinates'] = (x, y)
            self.ppt['properties']['river_id'] = nd_fid
            self.upstream_node = (x, y) 
        else:    
            self.ppt['geometry']['coordinates'] = snap_data[0][1]
            self.ppt['properties']['river_id'] = snap_data[0][2]
            self.upstream_node = (snap_data[0][3][0], 
                                  snap_data[0][3][1]) 