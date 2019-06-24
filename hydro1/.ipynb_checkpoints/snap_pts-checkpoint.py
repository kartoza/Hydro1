#!/usr/bin/env python

__license__ = "GPL version 2 or later"

import math


def angle(x1,y1,x2,y2):
    '''Determines the angle of a given line'''
    return math.atan2(y1-y2,x1-x2)*180/math.pi

def pt2line(point, line):
    
    '''
    Takes a point tuple and a two point line tuple. If the 
    point is not perpendicular to the line segment a False 
    is returned. Otherwise meta data are returned as 
    specified in Returns.
  
    Parameters: 
    point (tuple): (x1, y1)
    line  (tuple): (x1, y1, x2, y2) 
  
    Returns: 
    tuple: (Px, Py) The position of the point on the line
           perpendicular to the original given point
    float: Distance from the original given point to the
           line
    str:   LHS or RHS from the line
    '''
    
    Ax, Ay, Bx, By = line
    Cx, Cy = point
    L = ((Bx-Ax)**2+(By-Ay)**2)**0.5
    r = ((Cx-Ax)*(Bx-Ax)+(Cy-Ay)*(By-Ay))/L**2
    if r > 1 or r < 0: 
        return False
    Px = Ax+r*(Bx-Ax)
    Py = Ay+r*(By-Ay)
    dist = ((Cx-Px)**2+(Cy-Py)**2)**0.5
    ang = angle(Ax,Ay,Bx,By)-angle(Px,Py,Cx,Cy)
    if ang < 0:
        side = 'LHS'
    else:
        side = 'RHS'
    return ((Px, Py), dist, side)