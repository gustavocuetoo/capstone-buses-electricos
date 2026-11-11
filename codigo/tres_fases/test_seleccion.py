import unittest
from collections import Counter
from tres_fases.datos import seleccionar

class SelectionTests(unittest.TestCase):
    def rows(self):
        return [dict(route_id=f'{s}_{r}',sector_id=str(s),distancia_servicio_km=float(r+1))
                for s in range(5) for r in range(12)]
    def test_nested_sample_preserves_routes_and_sector_balance(self):
        rows=self.rows();small=seleccionar(rows,10);large=seleccionar(rows,20,small)
        self.assertEqual(len(set(large)),20)
        self.assertTrue(set(small)<=set(large))
        self.assertEqual(Counter(r.split('_')[0] for r in large),{str(i):4 for i in range(5)})
        self.assertEqual(large,seleccionar(rows,20,small))
    def test_unknown_route_rejected(self):
        with self.assertRaises(ValueError):seleccionar(self.rows(),20,['unknown'])
    def test_full_quota_preserved(self):
        small=seleccionar(self.rows(),10)
        self.assertEqual(set(seleccionar(self.rows(),10,small)),set(small))
    def test_impossible_sector_quota_rejected(self):
        with self.assertRaises(ValueError):seleccionar(self.rows(),10,['0_0','0_1','0_2'])

if __name__=='__main__':unittest.main()
