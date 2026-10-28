import unittest
from ejecutar import shortest, segments

class Tests(unittest.TestCase):
    def test_optimal_not_greedy(self):
        arcs=[(0,1,3),(0,2,2),(1,3,1),(2,3,7)]
        self.assertEqual(shortest(3,arcs),(4,[(0,1),(1,3)]))

    def test_all_small_graphs_against_enumeration(self):
        import random
        rng=random.Random(29)
        for n in range(1,9):
            for repeat in range(10):
                arcs=[(a,b,rng.randint(1,100)) for a in range(n) for b in range(a+1,n+1) if b==a+1 or rng.random()<.5]
                def brute(a):
                    return 0 if a==n else min(c+brute(b) for u,b,c in arcs if u==a)
                self.assertEqual(shortest(n,arcs)[0],brute(0))

    def test_infeasible(self):
        with self.assertRaises(ValueError):shortest(2,[(0,1,1)])

    def test_return_distance_can_decrease(self):
        lookup={'a':dict(inicio_stop_id='a',fin_stop_id='b',distancia_servicio_km=100),
                'b':dict(inicio_stop_id='c',fin_stop_id='d',distancia_servicio_km=10)}
        d={('T','S:a'):(0,0),('T','S:c'):(0,0),('S:b','T'):(150,0),('S:d','T'):(1,0),('S:b','S:c'):(0,0)}
        arcs=segments(['a','b'],lookup,d,{'a':('T','T',[]),'b':('T','T',[])})
        self.assertNotIn((0,1),[(a,b) for a,b,c in arcs])
        self.assertIn((0,2),[(a,b) for a,b,c in arcs])

if __name__=='__main__':unittest.main()
