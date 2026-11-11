import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE/'.deps'))
sys.path.insert(0, str(BASE))
import copy
import unittest
from tres_fases.fase3 import Calendario, construir, precio
from tres_fases.verificar import verificar
from tres_fases.fase2 import descomponer_energia

def fixture(gap=2400, second_sector=False):
    ids = ['T01', 'E1', 'S:A', 'S:B']
    d = {(a,b): ((0.,0) if a==b else (1.,200)) for a in ids for b in ids}
    trips = [dict(corrida_id='a',inicio_s=600,fin_s=4200,inicio_stop_id='A',fin_stop_id='B',sector_id='1',distancia_servicio_km=150.),
             dict(corrida_id='b',inicio_s=4200+gap,fin_s=7800+gap,inicio_stop_id='B',fin_stop_id='A',sector_id='1',distancia_servicio_km=120.)]
    chains = [dict(id='J1',corridas=['a','b'])]
    if second_sector:
        other = [dict(t, corrida_id=t['corrida_id']+'2', sector_id='2') for t in trips]
        trips += other
        chains.append(dict(id='J2',corridas=['a2','b2']))
    return trips, chains, d

class ModelTests(unittest.TestCase):
    def solve(self, gap=2400, second_sector=False):
        trips, chains, d = fixture(gap, second_sector)
        params = (d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,16000)
        plans, splits = construir(chains, {t['corrida_id']:t for t in trips}, *params)
        result, _, _ = verificar(plans, trips, *params)
        return trips, plans, splits, result, params

    def test_charge_avoids_extra_bus(self):
        _, plans, splits, result, _ = self.solve()
        self.assertEqual(len(plans),1)
        self.assertEqual(splits,[])
        self.assertGreater(result['carga_kwh'],0)
        self.assertEqual(result['sesiones'],1)

    def test_no_gap_splits_and_new_bus_starts_at_terminal(self):
        _, plans, splits, result, _ = self.solve(gap=0)
        self.assertEqual(len(plans),2)
        self.assertEqual(len(splits),1)
        self.assertTrue(all(p['actividades'][0]['origen']=='T01' for p in plans))
        self.assertEqual(result['carga_kwh'],0)

    def test_capacity_shared_between_sectors(self):
        _, _, _, result, _ = self.solve(second_sector=True)
        self.assertLessEqual(result['capacidades']['E1']['cargas_simultaneas_maximas'],1)
        self.assertEqual(result['corridas'],4)

    def test_validator_rejects_falsified_charge(self):
        trips, plans, _, _, params = self.solve()
        bad = copy.deepcopy(plans)
        next(a for p in bad for a in p['actividades'] if a['tipo']=='carga')['carga_kwh']=100.
        with self.assertRaises(AssertionError):
            verificar(bad,trips,*params)

    def test_validator_rejects_duplicated_service(self):
        trips, plans, _, _, params = self.solve()
        bad = plans+copy.deepcopy(plans)
        bad[-1]['bus_id']='OTHER'
        with self.assertRaises(AssertionError):
            verificar(bad,trips,*params)

    def test_calendar_half_open_and_parking(self):
        c = Calendario({'E1':1},{'E1':1},0,1800)
        c.reservar('E1',0,300,True)
        self.assertTrue(c.libre('E1',300,600,True))
        c.reservar('E1',600,1800)
        self.assertFalse(c.libre('E1',900,1200,True))

    def test_no_midnight_reset(self):
        trips, chains, d = fixture()
        for t in trips:
            t['inicio_s']+=81000
            t['fin_s']+=81000
        params = (d,['T01'],{'E1':1},{'E1':1},[(0,8,.1),(8,24,.2)],0,100000)
        plans, _ = construir(chains,{t['corrida_id']:t for t in trips},*params)
        result,_,acts = verificar(plans,trips,*params)
        self.assertEqual(len(plans),1)
        self.assertGreater(result['carga_kwh'],0)
        self.assertTrue(any(a['inicio_s']>86400 and a['tipo']=='carga' for a in acts))
        self.assertEqual(precio(86400,params[4]),.1)

    def test_unreachable_new_service_is_reported(self):
        trips, chains, d = fixture()
        trips[0]['distancia_servicio_km']=300
        with self.assertRaisesRegex(RuntimeError,'No prueba infactibilidad'):
            construir(chains,{t['corrida_id']:t for t in trips},d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,16000)

    def test_energy_decomposition_preserves_every_arc(self):
        # Dos prefijos con distinto consumo confluyen antes de dos continuaciones.
        edges=[(0,1,100,'servicio'),(0,1,10,'servicio'),(1,2,100,'servicio'),(1,2,10,'servicio'),(2,0,0,'flota')]
        arcs=[dict(u=u,v=v,km=km,tipo=kind) for u,v,km,kind in edges]
        paths=descomponer_energia([0,1,2],arcs,[1,1,1,1,2],0,2)
        self.assertEqual(sorted(sorted(p) for p in paths),[[0,3],[1,2]])

if __name__=='__main__':
    unittest.main()
