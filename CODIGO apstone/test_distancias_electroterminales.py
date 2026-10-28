"""Pruebas de dirección, proyección y lecturas de geometría del cálculo vial."""
import math
import struct
import unittest

from construir_distancias_electroterminales import (
    attach_locations, dijkstra, gpkg_line, haversine,
)


class RoutingTests(unittest.TestCase):
    def test_directed_shortest_path(self):
        graph = [[(1, 2), (2, 8)], [(2, 3)], []]
        self.assertEqual(dijkstra(graph, 0), [0, 2, 5])
        self.assertTrue(math.isinf(dijkstra(graph, 2)[0]))

    def test_gpkg_envelope_and_line(self):
        points = [(-70.7, -33.5), (-70.6, -33.4)]
        header = b'GP'+bytes([0, 3])+struct.pack('<i',4326)
        header += struct.pack('<dddd',-70.7,-70.6,-33.5,-33.4)
        line = bytes([1])+struct.pack('<II',2,2)
        line += struct.pack('<dddd',*points[0],*points[1])
        self.assertEqual(gpkg_line(header+line),points)

    def test_two_projections_preserve_one_way(self):
        coords = [(-70.70,-33.5),(-70.69,-33.5)]
        length = haversine(*coords)
        graph,reverse=[[(1,length)],[]],[[],[(0,length)]]
        def add_edge(u,v,w):
            graph[u].append((v,w))
            reverse[v].append((u,w))
        segments = [(0,1,length,True,False,1,'residential','Prueba',0,'F','F')]
        snaps = attach_locations({'A':(-70.698,-33.5),'B':(-70.692,-33.5)},
                                 graph,reverse,coords,segments,add_edge)
        a,b = snaps['A']['node'],snaps['B']['node']
        self.assertAlmostEqual(dijkstra(graph,a)[b],0.6*length,places=7)
        self.assertTrue(math.isinf(dijkstra(graph,b)[a]))

    def test_reverse_geometry_direction(self):
        coords = [(-70.70,-33.5),(-70.69,-33.5)]
        length = haversine(*coords)
        graph,reverse=[[],[(0,length)]],[[(1,length)],[]]
        def add_edge(u,v,w):
            graph[u].append((v,w))
            reverse[v].append((u,w))
        segments = [(0,1,length,False,True,1,'residential','Prueba',0,'F','F')]
        snaps = attach_locations({'A':(-70.698,-33.5),'B':(-70.692,-33.5)},
                                 graph,reverse,coords,segments,add_edge)
        a,b = snaps['A']['node'],snaps['B']['node']
        self.assertTrue(math.isinf(dijkstra(graph,a)[b]))
        self.assertAlmostEqual(dijkstra(graph,b)[a],0.6*length,places=7)


if __name__ == '__main__':
    unittest.main()
