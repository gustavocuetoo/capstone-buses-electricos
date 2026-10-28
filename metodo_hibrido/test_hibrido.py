import copy
import unittest
from metodo_hibrido.ejecutar import etapa
from metodo_hibrido.caso_base import solve
from metodo_hibrido.test_caso_base import instance
from metodo_hibrido.intercambios import buscar,evaluar_conjunto
from metodo_hibrido.calendario import Calendario
from metodo_hibrido.recarga import cambiar_reservas
from metodo_hibrido.verificar import verificar


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.trips,*self.params=instance()
        self.plans=solve(self.trips,*self.params)[-1]

    def test_invalid_stage_restores_incumbent_even_if_input_mutated(self):
        saved=copy.deepcopy(self.plans)
        def invalid(plans,*args,**kwargs):
            plans[0]['actividades']=[]
            return plans,[],{}
        result,_,stats=etapa(self.plans,self.trips,self.params,invalid)
        self.assertEqual(result,saved)
        self.assertEqual(self.plans,saved)
        self.assertFalse(stats['etapa_aceptada'])

    def test_equal_solution_preserves_incumbent(self):
        result,_,stats=etapa(self.plans,self.trips,self.params,lambda p,*a,**k:(p,[],{}))
        self.assertIs(result,self.plans)
        self.assertFalse(stats['etapa_aceptada'])

    def test_missing_service_is_not_removed_from_expected(self):
        def missing(plans,*a,**k):return [],[],{}
        # Auditor may reject an empty fleet via coverage before producing its summary.
        result,_,stats=etapa(self.plans,self.trips,self.params,missing)
        self.assertIs(result,self.plans)
        self.assertFalse(stats['etapa_aceptada'])

    def test_pair_search_merges_two_valid_independent_plans(self):
        self.params[2]['E1']=2
        independent=[]
        for i,t in enumerate(self.trips):
            p=solve([t],*self.params)[-1][0]
            p['bus_id']=str(i);independent.append(p)
        before=verificar(independent,self.trips,*self.params)[0]
        result,_,stats=etapa(independent,self.trips,self.params,buscar,budget=10,coordination='conjunta')
        after=verificar(result,self.trips,*self.params)[0]
        self.assertTrue(stats['etapa_aceptada'])
        self.assertEqual(after['buses'],1)
        self.assertLess(after['costo_total_usd'],before['costo_total_usd'])

    def test_failed_joint_attempt_restores_reservations(self):
        import time
        d,starts,physical,plugs,tariffs,t0,h=self.params
        calendar=Calendario(physical,plugs,t0,h)
        cambiar_reservas(calendar,self.plans,1)
        before={e:a.copy() for e,a in calendar.presence.items()}
        con=copy.deepcopy(calendar.connections)
        result,_=evaluar_conjunto(self.plans,[self.plans[0]['corridas']],{t['corrida_id']:t for t in self.trips},
                d,starts,calendar,tariffs,2,time.perf_counter()-1)
        self.assertIsNone(result)
        self.assertEqual(con,calendar.connections)
        self.assertTrue(all((before[e]==calendar.presence[e]).all() for e in before))

    def test_three_sequences_share_one_charger(self):
        from metodo_hibrido.conjunta import resolver_conjunto
        base,d,starts,physical,plugs,tariffs,t0,h=instance(gap=7200)
        h=20000
        sequences=[[dict(t,corrida_id=t['corrida_id']+str(i)) for t in base] for i in range(3)]
        plans,info=resolver_conjunto(sequences,'prueba',d,starts,Calendario(physical,plugs,t0,h),tariffs,limit=5)
        self.assertIsNotNone(plans)
        for i,p in enumerate(plans):p['bus_id']=str(i)
        report=verificar(plans,[t for seq in sequences for t in seq],d,starts,physical,plugs,tariffs,t0,h)[0]
        self.assertEqual(report['capacidades']['E1']['cargas_simultaneas_maximas'],1)
        self.assertGreater(info['restricciones_conexiones'],0)

    def test_trio_absorption_preserves_services(self):
        from metodo_hibrido.trios import propuestas
        from collections import Counter
        times=[('D1',3000,4000),('D2',7000,8000),('A1',1000,2000),('A2',6500,8500),('B1',2500,4500),('B2',9000,10000)]
        lookup={key:dict(corrida_id=key,inicio_s=s,fin_s=f,inicio_stop_id='A',fin_stop_id='A',sector_id='1',distancia_servicio_km=10.) for key,s,f in times}
        variants=list(propuestas([['D1','D2'],['A1','A2'],['B1','B2']],lookup,self.params[0],['T01'],['T01','E1']))
        self.assertTrue(any(kind=='absorcion_3_a_2' for kind,seqs in variants))
        for _,seqs in variants:self.assertEqual(Counter(t for seq in seqs for t in seq),Counter(lookup.keys()))

    def test_cross_sector_pair_is_not_evaluated(self):
        trips,d,starts,physical,plugs,tariffs,t0,h=instance(second_sector=True)
        params=(d,starts,physical,plugs,tariffs,t0,h)
        plans=solve(trips,*params)[-1]
        result,history,_=buscar(plans,{t['corrida_id']:t for t in trips},*params,budget=2,coordination='conjunta')
        self.assertEqual(result,plans)
        sectors={p['bus_id']:p['sector_id'] for p in plans}
        self.assertEqual(len(set(sectors.values())),2)
        self.assertTrue(all(sectors[r['bus_a']]==sectors[r['bus_b']] for r in history))


if __name__=='__main__':unittest.main()
