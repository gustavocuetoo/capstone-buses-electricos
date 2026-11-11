from tres_fases.test_modelos import fixture
import unittest
import copy
from collections import Counter
from tres_fases.trios import propuestas,buscar_trios
from tres_fases.fase3 import construir,Calendario
from tres_fases.conjunta import resolver_conjunto
from tres_fases.verificar import verificar

def caso():
    _,_,d=fixture()
    timetable=[('D1',3000,4000),('D2',7000,8000),('A1',1000,2000),('A2',6500,8500),('B1',2500,4500),('B2',9000,10000)]
    trips=[dict(corrida_id=k,inicio_s=s,fin_s=f,inicio_stop_id='A',fin_stop_id='A',sector_id='1',distancia_servicio_km=10.) for k,s,f in timetable]
    lookup={t['corrida_id']:t for t in trips}
    chains=[dict(id='D',corridas=['D1','D2']),dict(id='A',corridas=['A1','A2']),dict(id='B',corridas=['B1','B2'])]
    params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,15000)
    plans,_=construir(chains,lookup,*params)
    return trips,lookup,params,plans

class TrioTests(unittest.TestCase):
    def test_distributes_donor_between_two_receivers(self):
        _,lookup,params,_=caso();d=params[0]
        variants=list(propuestas([['D1','D2'],['A1','A2'],['B1','B2']],lookup,d,['T01'],['T01','E1']))
        absorptions=[s for kind,s in variants if kind=='absorcion_3_a_2']
        self.assertTrue(absorptions)
        self.assertTrue(any('D1' in s[0] and 'D2' in s[1] for s in absorptions))
        for _,seqs in variants:self.assertEqual(Counter(t for s in seqs for t in s),Counter(lookup.keys()))

    def test_full_search_reduces_three_to_two_and_preserves_input(self):
        trips,lookup,params,plans=caso();original=copy.deepcopy(plans)
        result,history,_=buscar_trios(plans,lookup,*params,budget=10)
        summary,_,_=verificar(result,trips,*params)
        self.assertEqual(summary['buses'],2)
        self.assertTrue(any(r['aceptado'] for r in history))
        self.assertEqual(plans,original)

    def test_different_sectors_do_not_form_trio(self):
        trips,lookup,params,plans=caso()
        for bus in plans:
            bus['sector_id']=bus['cadena_fase2']
            for key in bus['corridas']:lookup[key]['sector_id']=bus['sector_id']
        result,history,_=buscar_trios(plans,lookup,*params,budget=10)
        self.assertEqual(len(result),3);self.assertFalse(history)

    def test_zero_budget_preserves_solution(self):
        trips,lookup,params,plans=caso()
        result,history,stats=buscar_trios(plans,lookup,*params,budget=0)
        self.assertEqual(result,plans);self.assertFalse(history)
        self.assertEqual(stats['motivo_fin'],'presupuesto')

    def test_three_buses_jointly_share_one_charger(self):
        base,_,d=fixture(7200)
        sequences=[[dict(t,corrida_id=t['corrida_id']+str(i)) for t in base] for i in range(3)]
        params=(d,['T01'],{'E1':1},{'E1':1},[(0,24,.1)],0,20000)
        plans,info=resolver_conjunto(sequences,'J',d,['T01'],Calendario(params[2],params[3],0,20000),params[4],limit=5)
        self.assertIsNotNone(plans)
        for i,p in enumerate(plans):p['bus_id']=str(i)
        report,_,_=verificar(plans,[t for s in sequences for t in s],*params)
        self.assertEqual(report['buses'],3)
        self.assertEqual(report['capacidades']['E1']['cargas_simultaneas_maximas'],1)
        self.assertGreater(info['restricciones_conexiones'],0)

if __name__=='__main__':unittest.main()
