import json,csv,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter,NullLocator
ROOT=Path('/Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto')
OUT=ROOT/'08-entrega2/actualizacion_canva_20261006'
RED='#d42a1e';GRAY='#8a8a8a';INK='#232323';GRID='#e4e4e4'
fonts=ROOT/'08-entrega2/sensibilidad_presupuesto/fonts'
for p in fonts.glob('*.ttf'):
 if not p.stat().st_flags & 0x40000000:font_manager.fontManager.addfont(str(p))
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def num(x):return f'{x:,.0f}'.replace(',','.')
fmt=FuncFormatter(lambda x,pos:num(x))
def fig(w,h,m):
 f=plt.figure(figsize=(w/100,h/100),dpi=300);f.patch.set_alpha(0)
 l,b,r,t=m;a=f.add_axes([l/w,b/h,(w-l-r)/w,(h-b-t)/h]);a.patch.set_alpha(0)
 for s in ['top','right']:a.spines[s].set_visible(False)
 a.spines['left'].set_color('#cccccc');a.spines['bottom'].set_color('#cccccc')
 a.tick_params(length=0,labelsize=12,pad=6);a.set_axisbelow(True)
 return f,a

f,a=fig(645.333,453.333,(82,100,35,58))
vals=[4175,4014,3989,3873]
a.plot(range(4),vals,color='#b9382b',lw=2.2,marker='o',ms=7)
a.set_xticks(range(4),['Caso base','Construcción','Parejas','Tríos y\nrefinamiento'],fontsize=11)
a.set_xlim(-.25,3.25);a.set_ylim(3800,4250);a.set_yticks([3800,3900,4000,4100,4200]);a.yaxis.set_major_formatter(fmt)
a.grid(axis='y',color=GRID);a.set_ylabel('Buses usados (eje desde 3.800)',fontsize=12)
for i,v in enumerate(vals):a.annotate(num(v),(i,v),xytext=(0,12),textcoords='offset points',ha='center',fontsize=13,fontweight='bold')
a.set_title('Buses utilizados por etapa',fontsize=14,pad=17)
f.savefig(OUT/'buses_por_etapa.png',transparent=True);plt.close(f)

f,a=fig(853.333,386.667,(215,57,65,53))
vs=[75500,4158.19038167181,2980,2302.90546399936]
a.barh(range(4),vs,color='#b9382b',height=.56)
a.set_yticks(range(4),['Flota (−302 buses)','Electricidad','Sesiones de carga','Km recorridos'],fontsize=12);a.invert_yaxis()
a.set_xlim(0,85000);a.set_xticks([0,20000,40000,60000,80000]);a.xaxis.set_major_formatter(fmt);a.grid(axis='x',color=GRID)
for i,v in enumerate(vs):a.text(v+1200,i,num(v),va='center',fontsize=12)
a.set_title('Ahorro por componente de costo (USD/día)',fontsize=14,pad=16)
f.savefig(OUT/'ahorro_componentes.png',transparent=True);plt.close(f)

plt.rcParams['font.family']='PT Sans'
rows=list(csv.DictReader((ROOT/'08-entrega2/sensibilidad_presupuesto/resumen_barrido.csv').open()))
f,a=fig(935,402,(104,110,124,58))
a.spines['left'].set_visible(False);a.set_xscale('log',base=2);a.set_xlim(15/1.3,600*1.15);a.set_ylim(0,40000)
a.set_xticks([15,30,60,120,240,600],[f'{x} s' for x in [15,30,60,120,240,600]],fontsize=14);a.xaxis.set_minor_locator(NullLocator())
a.set_yticks([0,10000,20000,30000,40000]);a.yaxis.set_major_formatter(fmt);a.tick_params(labelsize=14);a.grid(axis='y',color=GRID)
for key,label,c in [('parejas','Solo parejas',GRAY),('parejas_y_trios','Parejas + tríos',RED)]:
 xs=[15,30,60,120,240];groups=[[float(r['ahorro_usd']) for r in rows if r['etapa']==key and float(r['presupuesto_s'])==x] for x in xs]
 ys=[statistics.median(g) for g in groups]
 a.fill_between(xs,[min(g) for g in groups],[max(g) for g in groups],color=c,alpha=.13,lw=0)
 a.plot(xs,ys,c=c,lw=1.8,marker='o',ms=6,label=label)
 v=1415348.6974639676-({'parejas':1403067.6310817823,'parejas_y_trios':1378806.9375112213}[key])
 a.plot(600,v,marker='D',color=c,ms=6)
 a.annotate('USD '+num(v),(600,v),xytext=(10,0),textcoords='offset points',fontsize=13,fontweight='bold',va='center',annotation_clip=False)
f.text(74/935,1-14/402,'Ahorro sobre la construcción cronológica (USD/día)',fontsize=15,fontweight='bold',va='top')
f.legend(loc='lower left',bbox_to_anchor=(.075,.085),ncol=2,frameon=False,fontsize=12)
f.text(.075,.04,'15–240 s: mediana/rango (n=3) · 600 s: búsqueda ampliada (n=1)',fontsize=12,color='#5e5e5e')
f.savefig(OUT/'sensibilidad_presupuesto.png',transparent=True);plt.close(f)
print('Created 3 charts')
