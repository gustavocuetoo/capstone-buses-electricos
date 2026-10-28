from tres_fases.test_modelos import fixture
import unittest
import time
import numpy as np
import gurobipy as gp
from tres_fases.conjunta import resolver_conjunto,acoplar
from tres_fases.fase3 import Calendario
from tres_fases.verificar import verificar
from tres_fases.reparar import cambiar_reservas
from tres_fases.intercambios import evaluar_conjunto
from tres_fases import test_intercambios

class JointTests(unittest.TestCase):
    def case(self,gap):
        trips,_,d=fixture(gap,second_sector=True)
        for t in trips:t['sector_id']='1'
        params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,18000)
        return trips,[trips[:2],trips[2:]],params

    def test_two_buses_share_one_charger_without_overlap(self):
        trips,seqs,params=self.case(4200)
        d,starts,phys,plugs,tariffs,t0,h=params
        cal=Calendario(phys,plugs,t0,h)
        plans,info=resolver_conjunto(seqs,'J',d,starts,cal,tariffs,limit=5)
        self.assertIsNotNone(plans)
        for k,p in enumerate(plans):p['bus_id']=str(k)
        report,_,_=verificar(plans,trips,*params)
        self.assertEqual(report['buses'],2)
        self.assertGreater(report['carga_kwh'],0)
        self.assertEqual(report['capacidades']['E1']['cargas_simultaneas_maximas'],1)
        self.assertGreater(info['restricciones_conexiones'],0)
        self.assertEqual(int(cal.presence['E1'].sum()),0)

    def test_insufficient_shared_charge_window_rejected(self):
        trips,seqs,params=self.case(2400)
        d,starts,phys,plugs,tariffs,t0,h=params
        plans,info=resolver_conjunto(seqs,'J',d,starts,Calendario(phys,plugs,t0,h),tariffs,limit=5)
        self.assertIsNone(plans)
        self.assertEqual(info['estado'],3)

    def test_final_parking_is_shared(self):
        _,seqs,params=self.case(4200)
        d,starts,phys,plugs,tariffs,t0,h=params
        d['S:B','T01']=(3.,600)
        seqs=[[s[0]] for s in seqs];trips=[s[0] for s in seqs]
        plans,_=resolver_conjunto(seqs,'J',d,starts,Calendario(phys,plugs,t0,h),tariffs)
        self.assertIsNotNone(plans)
        for k,p in enumerate(plans):p['bus_id']=str(k)
        self.assertEqual(sum(p['terminal_final']=='E1' for p in plans),1)
        verificar(plans,trips,*params)

    def test_external_occupancy_at_non_grid_second(self):
        cal=Calendario({'E1':2},{'E1':2},0,1000)
        cal.reservar('E1',551,552)
        m=gp.Model();m.Params.OutputFlag=0
        a=m.addVar(vtype='B',lb=1);b=m.addVar(vtype='B',lb=1)
        acoplar(m,{'E1':[(500,800,a),(500,800,b)]},cal)
        m.optimize();self.assertEqual(m.Status,3);m.dispose()

    def test_budget_returns_original_calendar(self):
        _,lookup,params,plans=test_intercambios.ExchangeTests().setup_case()
        d,starts,phys,plugs,tariffs,t0,h=params
        cal=Calendario(phys,plugs,t0,h);cambiar_reservas(cal,plans,1)
        original=cal.presence['E1'].copy()
        result,_=evaluar_conjunto(plans,[['a'],['b']],lookup,d,starts,cal,tariffs,2,time.perf_counter()-1)
        self.assertIsNone(result)
        np.testing.assert_array_equal(original,cal.presence['E1'])

if __name__=='__main__':unittest.main()
