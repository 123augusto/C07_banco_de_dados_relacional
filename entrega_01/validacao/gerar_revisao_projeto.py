from pathlib import Path
import xml.etree.ElementTree as ET
import re, json, hashlib, math
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1] / 'fontes'
OUT = Path(__file__).resolve().parent / 'gerados'
OUT.mkdir(exist_ok=True)
source = (BASE / 'trabalho_C07.sql').read_text(encoding='utf-8-sig')
sql = re.sub(r'--[^\n]*', '', source)
sql = re.sub(r'\n\s*\n+', '\n\n', sql).strip()
sql = sql.replace('CREATE TABLE IF NOT EXISTS', 'CREATE TABLE')
sql = sql.replace('data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP', 'data_inscricao DATETIME')
sql += '''

-- Relacionamento 1:1: um participante pode possuir no maximo uma credencial.
-- NOT NULL exige o participante; UNIQUE impede duas credenciais para ele.
CREATE TABLE credencial (
  id_credencial INT AUTO_INCREMENT,
  codigo VARCHAR(30) NOT NULL UNIQUE,
  id_participante INT NOT NULL UNIQUE,
  PRIMARY KEY (id_credencial),
  CONSTRAINT fk_credencial_participante
    FOREIGN KEY (id_participante)
    REFERENCES participante (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
'''
sql = '''-- Festival de Inovacao: modelo revisado para a disciplina C07.
-- Executar em um banco festival_inovacao sem as tabelas deste projeto.
-- Este arquivo cria a estrutura; nao migra tabelas que ja existam.
-- A data de inscricao deve ser informada quando conhecida; nao e automatica.

''' + sql
(OUT / 'trabalho_C07_corrigido.sql').write_text(sql, encoding='utf-8')

PALETTE = {
 'pessoas':('#e9f1ff','#406a9c'), 'evento':('#e9f4e8','#4d8152'),
 'inscricoes':('#fff4d7','#b78b24'), 'credenciais':('#f0eaff','#7a5aa3'),
 'relacoes':('#ffffff','#64748b'), 'legenda':('#f8fafc','#cbd5e1')}
LAYERS = [('relacoes','01 - Relacionamentos'),('pessoas','02 - Gestao de Pessoas'),
 ('evento','03 - Gestao do Evento'),('inscricoes','04 - Inscricoes'),
 ('credenciais','05 - Credenciais'),('legenda','06 - Legenda e orientacoes')]

class Diagram:
 def __init__(self,name,subtitle):
  self.name=name; self.nodes={}; self.edges=[]; self.labels=[]
  self.model=ET.Element('mxGraphModel',dict(dx='2200',dy='1650',grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth='2200',pageHeight='1650',math='0',shadow='0'))
  self.root=ET.SubElement(self.model,'root');ET.SubElement(self.root,'mxCell',id='0')
  for key,value in LAYERS:ET.SubElement(self.root,'mxCell',id=key,value=value,parent='0')
  self.text('title','FESTIVAL DE INOVAÇÃO',70,25,1800,45,size=30,bold=True,align='left')
  self.text('subtitle',subtitle,70,75,2000,34,size=18,align='left')
 def node(self,id,value,x,y,w,h,layer='pessoas',kind='rect',key=False,size=19):
  fill,stroke=PALETTE[layer]
  style=f'whiteSpace=wrap;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize={size};fillColor={fill};strokeColor={stroke};strokeWidth=2;'
  if kind=='ellipse':style+='ellipse;'
  elif kind=='diamond':style+='rhombus;'
  elif kind=='triangle':style+='shape=triangle;direction=south;'
  else:style+='rounded=0;'
  if key:style+='fontStyle=4;'
  cell=ET.SubElement(self.root,'mxCell',id=id,value=value,style=style,vertex='1',parent=layer)
  ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
  self.nodes[id]=dict(id=id,value=value,x=x,y=y,w=w,h=h,layer=layer,kind=kind,key=key,size=size)
  return id
 def text(self,id,value,x,y,w,h,size=17,bold=False,align='center',layer='legenda'):
  style=f'text;html=0;whiteSpace=wrap;align={align};verticalAlign=middle;fontFamily=Arial;fontSize={size};fontColor=#26354a;strokeColor=none;fillColor=none;'
  if bold:style+='fontStyle=1;'
  c=ET.SubElement(self.root,'mxCell',id=id,value=value,style=style,vertex='1',parent=layer)
  ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
  self.labels.append(dict(id=id,value=value,x=x,y=y,w=w,h=h,size=size,bold=bold,align=align))
 def point(self,id,anchor):
  n=self.nodes[id];return(n['x']+n['w']*anchor[0],n['y']+n['h']*anchor[1])
 def edge(self,id,src,dst,sa=(.5,1),ta=(.5,0),via=(),layer='relacoes'):
  a=self.point(src,sa);b=self.point(dst,ta);points=[a,*via,b]
  style=f'edgeStyle=none;rounded=0;html=0;endArrow=none;startArrow=none;strokeColor=#586879;strokeWidth=2;exitX={sa[0]};exitY={sa[1]};exitDx=0;exitDy=0;entryX={ta[0]};entryY={ta[1]};entryDx=0;entryDy=0;'
  c=ET.SubElement(self.root,'mxCell',id=id,source=src,target=dst,edge='1',parent=layer,style=style)
  g=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
  if via:
   arr=ET.SubElement(g,'Array',attrib={'as':'points'})
   for x,y in via:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  self.edges.append(dict(id=id,points=points,src=src,dst=dst,layer=layer))
 def attr(self,id,name,x,y,w,entity,sa=(.5,1),ta=(.5,0),key=False):
  layer=self.nodes[entity]['layer'];self.node(id,name,x,y,w,45,layer,'ellipse',key,16)
  self.edge('link_'+id,id,entity,sa,ta,layer=layer)
 def card(self,id,x,y,w,title,rows,layer):
  h=55+len(rows)*35
  self.node(id,title,x,y,w,h,layer,'card',size=23)
  cell=self.root.find(f"mxCell[@id='{id}']")
  cell.set('value',title)
  cell.set('style',cell.get('style')+'verticalAlign=top;spacingTop=13;fontStyle=1;')
  body=ET.SubElement(self.root,'mxCell',id=id+'_rows',value='\n'.join(rows),vertex='1',parent=id,style='text;html=0;whiteSpace=wrap;align=left;verticalAlign=top;spacingLeft=16;spacingTop=7;fontFamily=Arial;fontSize=18;strokeColor=none;fillColor=none;')
  ET.SubElement(body,'mxGeometry',x='0',y='48',width=str(w),height=str(h-48),attrib={'as':'geometry'})
  self.nodes[id]['rows']=rows
  return h
 def preview(self,filename):
  image=Image.new('RGB',(2200,1650),'white');draw=ImageDraw.Draw(image)
  def font(size,bold=False):
   arial = Path('C:/Windows/Fonts') / ('arialbd.ttf' if bold else 'arial.ttf')
   arquivo = str(arial) if arial.is_file() else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
   try:
    return ImageFont.truetype(arquivo, size)
   except OSError:
    return ImageFont.load_default(size)
  def text(value,x,y,w,h,size=17,bold=False,align='center',key=False):
   f=font(size,bold); lines=value.splitlines();step=size+5
   ty=y+(h-step*len(lines))/2
   for line in lines:
    tw=draw.textlength(line,font=f)
    assert tw<=w-4,(filename,line,tw,w)
    tx=x+(w-tw)/2 if align=='center' else x+4
    draw.text((tx,ty),line,fill='#26354a',font=f)
    if key:draw.line((tx,ty+size+1,tx+tw,ty+size+1),fill='#26354a',width=1)
    ty+=step
  for edge in self.edges:draw.line(edge['points'],fill='#586879',width=2)
  for n in self.nodes.values():
   x,y,w,h=n['x'],n['y'],n['w'],n['h'];fill,stroke=PALETTE[n['layer']]
   if n['kind']=='ellipse':draw.ellipse((x,y,x+w,y+h),fill=fill,outline=stroke,width=2)
   elif n['kind']=='diamond':draw.polygon([(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)],fill=fill,outline=stroke,width=2)
   elif n['kind']=='triangle':draw.polygon([(x,y),(x+w,y),(x+w/2,y+h)],fill=fill,outline=stroke,width=2)
   else:draw.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=2)
   if n['kind']=='card':
    draw.line((x,y+48,x+w,y+48),fill=stroke,width=1)
    text(n['value'],x,y,w,48,23,True)
    for i,row in enumerate(n['rows']):text(row,x+12,y+52+i*35,w-24,35,18,align='left')
   else:text(n['value'],x,y,w,h,n['size'],key=n['key'])
  for l in self.labels:
   text(l['value'],l['x'],l['y'],l['w'],l['h'],l['size'],l['bold'],l['align'])
  image.save(OUT/filename)

c=Diagram('01 - Modelo conceitual','DER • Entidades, atributos, cardinalidades mínimas/máximas e especialização ISA')
c.node('pessoa','Pessoa',950,240,200,60)
c.node('isa','ISA',1010,380,80,60,'pessoas','triangle')
c.node('palestrante','Palestrante',390,540,220,60)
c.node('participante','Participante',1510,540,220,60)
c.node('atividade','Atividade',940,900,220,60,'evento')
c.node('espaco','Espaço',340,1280,220,60,'evento')
c.node('credencial','Credencial',1810,920,220,60,'credenciais')
c.node('ministra','Ministra',550,830,160,100,'relacoes','diamond')
c.node('inscricao','Inscrição',1480,830,160,100,'inscricoes','diamond')
c.node('possui','Possui',1830,690,150,90,'relacoes','diamond')
c.node('sedia','Sedia',640,1220,150,90,'relacoes','diamond')
c.node('exige','Exige',1030,1270,150,100,'relacoes','diamond')
c.edge('heranca_pessoa','pessoa','isa')
c.edge('heranca_palestrante','isa','palestrante',(.25,.5),(.5,0),[(500,410)])
c.edge('heranca_participante','isa','participante',(.75,.5),(.5,0),[(1620,410)])
c.attr('p_id','id_pessoa',720,145,180,'pessoa',ta=(.2,0),key=True)
c.attr('p_nome','nome',930,135,160,'pessoa',ta=(.4,0))
c.attr('p_email','email',1120,135,160,'pessoa',ta=(.6,0))
c.attr('p_telefone','telefone',1310,145,170,'pessoa',ta=(.8,0))
c.attr('pal_cv','minicurriculo',110,485,200,'palestrante',(1,.5),(0,.25))
c.attr('pal_area','area_especialidade',100,615,230,'palestrante',(1,.5),(0,.75))
c.attr('par_tipo','tipo_ingresso',1800,490,210,'participante',(0,.5),(1,.25))
c.attr('a_id','id_atividade',770,710,180,'atividade',ta=(.2,0),key=True)
c.attr('a_titulo','titulo',980,690,150,'atividade',ta=(.5,0))
c.attr('a_duracao','duracao_minutos',1160,710,220,'atividade',ta=(.8,0))
c.attr('a_desc','descricao',850,1040,210,'atividade',(.5,0),(.3,1))
c.attr('a_data','data_hora_inicio',1110,1040,230,'atividade',(.5,0),(.7,1))
c.attr('e_id','id_espaco',170,1420,180,'espaco',(.5,0),(.2,1),key=True)
c.attr('e_nome','nome_local',390,1450,190,'espaco',(.5,0),(.5,1))
c.attr('e_cap','capacidade_maxima',610,1420,250,'espaco',(.5,0),(.8,1))
c.attr('i_data','data_inscricao',1450,1040,210,'inscricao',(.5,0),(.25,.75))
c.attr('i_status','status_checkin',1660,1040,210,'inscricao',(.5,0),(.75,.75))
c.attr('cr_id','id_credencial',1800,1150,190,'credencial',(.5,0),(.3,1),key=True)
c.attr('cr_codigo','codigo',2020,1120,150,'credencial',(.5,0),(.8,1))
c.edge('pal_ministra','palestrante','ministra',(.5,1),(.5,0),[(500,760),(630,760)])
c.edge('ministra_atv','ministra','atividade',(1,.5),(0,.5),[(820,880),(820,930)])
c.text('card_pal','(0,N)',380,620,110,30,layer='relacoes')
c.text('card_atv_pal','(0,1)',835,899,95,28,layer='relacoes')
c.edge('par_inscreve','participante','inscricao',(.5,1),(.5,0),[(1620,755),(1560,755)])
c.edge('inscreve_atv','inscricao','atividade',(0,.5),(1,.5),[(1420,880),(1420,930)])
c.text('card_par_nm','(0,N)',1495,620,110,28,layer='relacoes')
c.text('card_atv_nm','(0,N)',1180,895,110,28,layer='relacoes')
c.edge('par_possui','participante','possui',(1,.75),(.5,0),[(1905,585)])
c.edge('possui_cred','possui','credencial',(.5,1),(.5,0),[(1905,860),(1920,860)])
c.text('card_par_cr','(0,1)',1760,550,100,27,layer='relacoes')
c.text('card_cr','(1,1)',1940,875,105,28,layer='relacoes')
c.edge('esp_sedia','espaco','sedia',(1,.5),(0,.5),[(600,1310),(600,1265)])
c.edge('sedia_atv','sedia','atividade',(.5,0),(0,.75),[(715,1170),(745,1170),(745,945)])
c.text('card_esp','(0,N)',550,1320,100,30,layer='relacoes')
c.text('card_atv_esp','(0,1)',825,955,100,28,layer='relacoes')
c.edge('rec_dependente','atividade','exige',(.15,1),(0,.5),[(790,960),(790,1320)])
c.edge('rec_prerequisito','exige','atividade',(1,.5),(1,.8),[(1380,1320),(1380,948)])
c.text('rec_dep_label','Dependente (0,1)',830,1275,190,30,layer='relacoes')
c.text('rec_pre_label','Pré-requisito (0,N)',1185,1280,190,30,layer='relacoes')
c.text('intermediaria','Inscrição → inscricoes_atividade (N:M)',1330,1120,470,40,size=17,layer='inscricoes')
c.text('legend1','Retângulo: entidade  •  Elipse: atributo  •  Sublinhado: chave  •  Losango: relacionamento  •  Triângulo ISA: herança',70,1530,2050,35,size=18,align='left')
c.text('legend2','(mín,máx) junto à entidade: quantas associações cada ocorrência pode ter. Os dois papéis de Atividade formam o relacionamento recursivo.',70,1570,2050,35,size=17,align='left')

l=Diagram('02 - Modelo relacional','Tabelas e tipos de dados • Inscrição materializa N:M • Credencial acrescenta o relacionamento 1:1')
l.card('pessoa',800,155,520,'pessoa',[
 'id_pessoa INT [PK, AI]', 'nome VARCHAR(100) [NN]',
 'email VARCHAR(100) [NN, U]', 'telefone VARCHAR(15)'],'pessoas')
l.card('palestrante',110,495,520,'palestrante',[
 'id_pessoa INT [PK, FK → pessoa]', 'minicurriculo VARCHAR(255)', 'area_especialidade VARCHAR(50)'],'pessoas')
l.card('participante',1530,495,520,'participante',[
 'id_pessoa INT [PK, FK → pessoa]', 'tipo_ingresso VARCHAR(20) [NN]'],'pessoas')
l.card('credencial',1530,155,520,'credencial',[
 'id_credencial INT [PK, AI]', 'codigo VARCHAR(30) [NN, U]',
 'id_participante INT [NN, U, FK → participante]'],'credenciais')
l.card('atividade',800,780,570,'atividade',[
 'id_atividade INT [PK, AI]', 'titulo VARCHAR(150) [NN]', 'descricao VARCHAR(255)',
 'duracao_minutos INT', 'data_hora_inicio DATETIME [NN]', 'id_espaco INT [FK → espaco]',
 'id_palestrante INT [FK → palestrante]', 'id_atividade_prerequisito INT [FK → atividade]'],'evento')
l.card('espaco',100,1080,520,'espaco',[
 'id_espaco INT [PK, AI]', 'nome_local VARCHAR(50) [NN]', 'capacidade_maxima INT [NN]'],'evento')
l.card('inscricoes_atividade',1530,920,610,'inscricoes_atividade',[
 'id_participante INT [PK*, FK → participante]',
 'id_atividade INT [PK*, FK → atividade]',
 'data_inscricao DATETIME', 'status_checkin BOOLEAN [DEFAULT FALSE]'],'inscricoes')
l.edge('heranca_pal','pessoa','palestrante',(.15,1),(.5,0),[(878,415),(370,415)])
l.edge('heranca_par','pessoa','participante',(.85,1),(.5,0),[(1242,415),(1790,415)])
l.text('heranca_pal_text','Herança: PK da subclasse também é FK',160,372,590,32,size=18,layer='relacoes')
l.text('heranca_par_text','Herança: PK da subclasse também é FK',1370,372,620,32,size=18,layer='relacoes')
l.edge('possui','participante','credencial',(1,.5),(1,.5),[(2140,557.5),(2140,235)])
l.text('possui_label','Possui 1:1',1910,330,225,34,size=18,layer='relacoes')
l.edge('ministra','palestrante','atividade',(.5,1),(0,.30),[(370,725),(730,725),(730,880.5)])
l.text('ministra_label','Ministra 1:N',420,682,255,34,size=19,layer='relacoes')
l.edge('sedia','espaco','atividade',(1,.5),(0,.78),[(710,1160),(710,1041.3)])
l.text('sedia_label','Sedia 1:N',465,1010,210,34,size=19,layer='relacoes')
l.edge('realiza_inscricao','participante','inscricoes_atividade',(.5,1),(.5,0),[(1790,750),(1835,750)])
l.text('realiza_label','Realiza 1:N',1870,785,240,34,size=19,layer='relacoes')
l.edge('recebe_inscricao','atividade','inscricoes_atividade',(1,.50),(0,.5),[(1450,947.5),(1450,1017.5)])
l.text('recebe_label','Recebe 1:N',1375,878,235,34,size=18,layer='relacoes')
l.edge('prerequisito','atividade','atividade',(.3,1),(1,.86),[(971,1320),(1440,1320),(1440,1068.1)])
l.text('rec_label','Exige • recursivo 1:N',1060,1273,340,34,size=19,layer='relacoes')
l.text('nm_explicacao','N:M: Participante × Atividade\nPK composta impede inscrição duplicada.',1500,1160,630,65,size=20,layer='inscricoes')
l.text('legend_pk','PK: chave primária  •  FK: chave estrangeira  •  U: UNIQUE  •  NN: NOT NULL  •  AI: AUTO_INCREMENT',70,1400,2050,40,size=20,align='left')
l.text('legend_pk2','PK* = as duas colunas juntas formam a chave primária. Colunas PK são obrigatórias. As demais, sem NN, aceitam NULL.',70,1445,2050,35,size=18,align='left')
l.text('legend_card','Rótulos 1:1 e 1:N indicam máximos. Mínimos e papéis estão na página conceitual. Herança preserva o mesmo id_pessoa.',70,1490,2050,35,size=18,align='left')
l.text('legend_fk','Uma atividade pode ter 0..1 espaço, 0..1 palestrante e 0..1 pré-requisito. Cada credencial exige um participante único.',70,1535,2050,35,size=18,align='left')

mx=ET.Element('mxfile',host='app.diagrams.net')
for i,d in enumerate([c,l],1):
 diagram=ET.SubElement(mx,'diagram',id=f'festival_revisado_{i}',name=d.name);diagram.append(d.model)
ET.indent(mx,space='  ')
ET.ElementTree(mx).write(OUT/'Festival_corrigido.drawio',encoding='utf-8',xml_declaration=True)
for d,file in [(c,'Modelo_conceitual.png'),(l,'Modelo_relacional.png')]:d.preview(file)
for i,d in enumerate([c,l],1):
 ids=[x.get('id') for x in d.root.findall('mxCell')]
 assert len(ids)==len(set(ids))
 for cell in d.root.findall('mxCell'):
  for attr in ['parent','source','target']:
   if cell.get(attr):assert cell.get(attr) in ids,(cell.get('id'),attr)
 assert len(d.root.findall("mxCell[@parent='0']"))==6
 print(d.name,len(d.nodes),'figuras',len(d.edges),'conectores',6,'layers')
meta={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'trabalho_C07.sql',BASE/'BD_Drawio.xml',BASE/'BD_DRAWIO_TESTE.xml']}
(OUT/'validacao_arquivos.json').write_text(json.dumps({'originais_sha256':meta,'layers_por_pagina':6,'paginas_drawio':2,'tabelas_sql':7},ensure_ascii=False,indent=2),encoding='utf-8')
print('Arquivos gerados em',str(OUT).encode('ascii','backslashreplace').decode())
