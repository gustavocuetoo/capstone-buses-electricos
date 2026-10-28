"""Reparación local: mejora real, reservas ajenas y devolución tras rechazo."""
from tres_fases.test_modelos import fixture
import unittest
from tres_fases.fase3 import construir,Calendario
from tres_fases.reparar import reparar,resolver_jornada,cambiar_reservas
from tres_fases.verificar import verificar

class RepairTests(unittest.TestCase):
    def setup_case(self,gap=2400):
        trips,_,d=fixture(gap)
        lookup={t['corrida_id']:t for t in trips}
        params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,16000)
        plans,_=construir([dict(id='J1',corridas=['a']),dict(id='J1',corridas=['b'])],lookup,*params)
        return trips,lookup,params,plans

    def test_reoptimizes_charge_and_removes_bus(self):
        trips,lookup,params,plans=self.setup_case()
        after,records=reparar(plans,lookup,*params)
        report,_,_=verificar(after,trips,*params)
        self.assertEqual(report['buses'],1)
        self.assertGreater(report['carga_kwh'],0)
        self.assertTrue(records[0]['aceptada'])
        self.assertFalse(records[0]['requiere_relajar_reserva_T'])

    def test_rejected_merge_preserves_original_plans(self):
        trips,lookup,params,plans=self.setup_case(0)
        before,_,_=verificar(plans,trips,*params)
        after,records=reparar(plans,lookup,*params)
        report,_,_=verificar(after,trips,*params)
        self.assertFalse(records[0]['aceptada'])
        self.assertEqual(report,before)

    def test_other_bus_parking_blocks_charging(self):
        trips,lookup,params,plans=self.setup_case()
        d,starts,physical,plugs,tariffs,t0,h=params
        calendar=Calendario(physical,plugs,t0,h)
        calendar.reservar('E1',0,h)
        candidate,_=resolver_jornada(trips,'J1',d,starts,calendar,tariffs)
        self.assertIsNone(candidate)
        self.assertEqual(int(calendar.presence['E1'].min()),1)

    def test_physical_feasible_without_conservative_terminal_reserve(self):
        trips,_,d=fixture(0)
        trips[1]['distancia_servicio_km']=70.
        d['S:A','T01']=(20.,4000)
        lookup={t['corrida_id']:t for t in trips}
        params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,16000)
        plans,_=construir([dict(id='J1',corridas=['a']),dict(id='J1',corridas=['b'])],lookup,*params)
        after,records=reparar(plans,lookup,*params)
        report,_,_=verificar(after,trips,*params)
        self.assertEqual(report['buses'],1)
        self.assertTrue(records[0]['requiere_relajar_reserva_T'])
        self.assertEqual(report['carga_kwh'],0)

if __name__=='__main__':unittest.main()
