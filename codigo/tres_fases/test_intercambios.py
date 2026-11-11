"""Cobertura, restricciones sectoriales, presupuesto y reversión del calendario."""
from tres_fases.test_modelos import fixture
import copy
import time
import unittest
from unittest.mock import patch
from collections import Counter
import numpy as np
from tres_fases.fase3 import construir,Calendario
from tres_fases.intercambios import alternativas,buscar,evaluar
from tres_fases.reparar import cambiar_reservas
from tres_fases.verificar import verificar

class ExchangeTests(unittest.TestCase):
    def setup_case(self):
        trips,_,d=fixture()
        lookup={t['corrida_id']:t for t in trips}
        params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,16000)
        plans,_=construir([dict(id='J1',corridas=['a']),dict(id='J2',corridas=['b'])],lookup,*params)
        return trips,lookup,params,plans

    def test_merges_different_chains_and_preserves_input(self):
        trips,lookup,params,plans=self.setup_case();saved=copy.deepcopy(plans)
        result,history,_=buscar(plans,lookup,*params,budget=10)
        report,_,_=verificar(result,trips,*params)
        self.assertEqual(report['buses'],1)
        self.assertTrue(any(r['aceptado'] for r in history))
        self.assertEqual(plans,saved)
        self.assertEqual(result[0]['cadena_fase2'],'J1|J2')

    def test_no_cross_sector_exchange(self):
        trips,lookup,params,plans=self.setup_case()
        trips[1]['sector_id']='2';plans[1]['sector_id']='2'
        result,history,_=buscar(plans,lookup,*params,budget=10)
        self.assertEqual(len(result),2);self.assertFalse(history)

    def test_budget_exhaustion_keeps_feasible_solution(self):
        trips,lookup,params,plans=self.setup_case()
        result,history,stats=buscar(plans,lookup,*params,budget=0)
        self.assertEqual(result,plans);self.assertFalse(history)
        self.assertEqual(stats['motivo_fin'],'presupuesto')
        verificar(result,trips,*params)

    def test_invalid_candidate_is_rejected_without_losing_baseline(self):
        trips,lookup,params,plans=self.setup_case()
        bad=copy.deepcopy(plans[0])
        bad['corridas']=['a','b'] # Omite realmente b en las actividades.
        with patch('tres_fases.intercambios.evaluar',return_value=([bad],['2'])):
            result,history,_=buscar(plans,lookup,*params,budget=10)
        self.assertEqual(result,plans)
        self.assertTrue(history)
        self.assertTrue(all(not r['aceptado'] for r in history))
        verificar(result,trips,*params)

    def test_failed_second_bus_restores_all_reservations(self):
        _,lookup,params,plans=self.setup_case()
        d,starts,physical,plugs,tariffs,t0,h=params
        calendar=Calendario(physical,plugs,t0,h);cambiar_reservas(calendar,plans,1)
        old_presence={e:a.copy() for e,a in calendar.presence.items()}
        responses=[(copy.deepcopy(plans[0]),{'estado':2}),(None,{'estado':3}),
                   (copy.deepcopy(plans[1]),{'estado':2}),(None,{'estado':3})]
        with patch('tres_fases.intercambios.resolver_jornada',side_effect=responses):
            candidate,_=evaluar(plans,[['a'],['b']],lookup,d,starts,calendar,tariffs,2,time.perf_counter()+10)
        self.assertIsNone(candidate)
        for e,a in old_presence.items():np.testing.assert_array_equal(a,calendar.presence[e])

    def test_suffix_and_single_service_moves_preserve_coverage(self):
        trips,_,d=fixture()
        template=trips[0]
        lookup={str(i):dict(template,corrida_id=str(i),inicio_s=1000*i,fin_s=1000*i+300,
                            inicio_stop_id='A',fin_stop_id='A') for i in range(1,7)}
        variants=list(alternativas(['1','3','5'],['2','4','6'],lookup,d))
        self.assertIn('sufijos',{kind for kind,_ in variants})
        self.assertIn('servicio',{kind for kind,_ in variants})
        for _,seqs in variants:self.assertEqual(Counter(t for s in seqs for t in s),Counter(lookup.keys()))

if __name__=='__main__':unittest.main()
