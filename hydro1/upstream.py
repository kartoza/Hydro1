#!/usr/bin/env python3

__license__ = "GPL version 2 or later"

import fiona
from shapely.geometry import Point


def upstream(riverlines, riverdb='../data/HydroSHEDS.gpkg', layer = 'Rivers'):
        '''
        Trace the all the upstream lines from the targeted river line(s).
        
        Args:
          riverlines (dict): The river line(s) from which the network must 
                             be run recursively upwards. The key is the 'fid'
                             and the values are the GeoJSON presentation.
          riverdb (str)    : The name of the indexed geopackage containing 
                             the riverlines
          layer (str)      : The name of the layer containing the river lines.
          
        Returns:
          riverlines (dict): The same dictionary as the input but with all the
                             upstream river lines added.
        '''
        
        rnet = list()
        rids = set()
        for key, value in riverlines.items():
            rnet.append(value)
            rids.add(key)
        with fiona.open(riverdb, layer=layer) as source:
            while len(rnet) > 0:
                current = rnet.pop()
                up_node = Point(current['geometry']['coordinates'][0])
                node_area = up_node.buffer(0.001)
                hits = list(source.items(bbox=(node_area.bounds)))
                for item in hits:
                    if item[0] not in rids:
                        rnet.append(item[1])
                        riverlines[item[0]] = item[1]
                    rids.add(item[0])
        return riverlines
    