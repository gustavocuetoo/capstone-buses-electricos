"""Verificaciones pequeñas de cobertura, horarios y capacidades compartidas."""
import tempfile
import unittest
from pathlib import Path
from fase1.modelo import crear_red,resolver_red,descomponer,verificar_y_exportar

CFG=dict(costo_bus_usd=250,costo_km_usd=.5,costo_espera_min_usd=.03,regulacion_min=0)

def trip(key,start,end,origin,dest,sector='1'):
    return dict(corrida_id=key,inicio_s=start,fin_s=end,inicio_stop_id=origin,
                fin_stop_id=dest,sector_id=sector,distancia_servicio_km=3)

def distances():
    ids=['S:A','S:B','T1','T2','E1']
    return {(a,b):(0,0) if a==b else (.3,60) for a in ids for b in ids}

class PhaseOneTests(unittest.TestCase):
    def solve(self,trips,d,starts=None,caps=None):
        starts=starts or ['T1'];caps=caps or {'T1':None}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            nodes,arcs,source,sink,_=crear_red(trips,d,starts,caps,CFG)
            flow,summary=resolver_red(nodes,arcs,out)
            paths=descomponer(nodes,arcs,flow,source,sink)
            verified=verificar_y_exportar(trips,nodes,arcs,paths,d,caps,CFG,out)
            self.assertAlmostEqual(summary['objetivo_usd'],verified['costo_verificado_usd'],places=6)
            return verified

    def test_reverse_service_without_empty_return(self):
        result=self.solve([trip('ida',600,1200,'A','B'),trip('vuelta',1200,1800,'B','A')],distances())
        self.assertEqual(result['flota'],1)
        self.assertAlmostEqual(result['km_vacio'],.6) # Only initial and final depot travel.
        self.assertEqual(result['espera_min'],0)

    def test_overlap_requires_two_buses(self):
        result=self.solve([trip('uno',600,1800,'A','B'),trip('dos',1200,2400,'B','A')],distances())
        self.assertEqual(result['flota'],2)

    def test_insufficient_repositioning_time(self):
        result=self.solve([trip('uno',600,1200,'A','A'),trip('dos',1230,1800,'B','B')],distances())
        self.assertEqual(result['flota'],2)

    def test_wait_is_charged(self):
        result=self.solve([trip('uno',600,1200,'A','B'),trip('dos',1800,2400,'B','A')],distances())
        self.assertEqual(result['flota'],1)
        self.assertAlmostEqual(result['espera_min'],10)

    def test_distinct_final_terminal_and_shared_capacity(self):
        d=distances();d['S:B','E1']=(0,0);d['S:B','T1']=(10,2000)
        result=self.solve([trip('uno',600,1800,'A','B','1'),trip('dos',600,1800,'A','B','2')],d,caps={'T1':None,'E1':1})
        self.assertEqual(result['flota'],2)
        self.assertEqual(result['buses_finales']['E1'],1)
        self.assertEqual(result['buses_finales']['T1'],1)

    def test_missing_distance_is_not_zero(self):
        d=distances();del d['S:A','S:B']
        with self.assertRaises(ValueError):
            self.solve([trip('uno',600,1200,'A','A'),trip('dos',1800,2400,'B','B')],d)

if __name__=='__main__':unittest.main()
