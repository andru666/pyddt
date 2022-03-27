# -*- coding: utf-8 -*-
import sys, os, operator, ast, gc, time, pickle

import mod_ddt_utils, mod_globals, mod_db_manager, mod_scan_ecus
from shutil import copyfile
import xml.etree.ElementTree as et
from xml.dom.minidom import parse
import xml.dom.minidom
from kivy import base
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.base import EventLoop
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty
from kivy.uix.textinput import TextInput
from kivy.utils import platform
import Queue
from mod_ddt_ecu import DDTECU
from mod_ddt_screen import DDTScreen
from kivy.uix.accordion import Accordion, AccordionItem
from mod_elm import ELM

from mod_utils import *

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
resizeFont = False

class MyButton(Button):
    global fs
    def __init__(self, **kwargs):
        super(MyButton, self).__init__(**kwargs)
        self.bind(size=self.setter('text_size'))
        if 'halign' not in kwargs:
            self.halign = 'center'
        if 'valign' not in kwargs:
            self.valign = 'middle'
        if 'font_size' not in kwargs:
            self.font_size = fs
        if 'size_hint' not in kwargs:
            self.size_hint =(1, 1)

class MyLabel(Label):
    global fs
    def __init__(self, **kwargs):
        fs = mod_globals.fontSize
        if 'bgcolor' in kwargs:
            self.bgcolor = kwargs['bgcolor']
        else:
            self.bgcolor =(0, 0, 0, 0)
        super(MyLabel, self).__init__(**kwargs)
        self.bind(size=self.setter('text_size'))
        if 'halign' not in kwargs:
            self.halign = 'center'
        if 'valign' not in kwargs:
            self.valign = 'middle'
        if 'font_size' not in kwargs:
            self.font_size = fs
        if 'size_hint' not in kwargs:
            self.size_hint =(1, None)
        if 'height' not in kwargs:
            fmn = 1.3
            lines = len(self.text.split('\n'))
            simb = len(self.text) / 60
            if lines < simb: lines = simb
            if lines < 7: lines = 7
            if lines > 20: lines = 20
            if 1 > simb: lines = 2
            if fs > 20: 
                lines = lines * 1.05
                fmn = 1.5
            self.height = fmn * lines * fs

    def on_size(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
            Rectangle(pos=self.pos, size=self.size)

class DDT():
    decu = None
    cecu = None
    
    def __init__(self, elm, cecu, langmap={}):
        self.elm = elm
        self.cecu = cecu
        
        decucashfile = os.path.join(mod_globals.cache_dir, "ddt_" + cecu['ModelId'] + ".p") 
        if os.path.isfile(decucashfile) and mod_globals.opt_ddtxml == '':
            self.decu = pickle.load(open(decucashfile, "rb"))
        else:
            self.decu = DDTECU(self.cecu)
            self.decu.setELM(self.elm)
            self.decu.scanECU()
            self.decu.setELM(None)
            if len(self.decu.ecufname) > 0:
                pickle.dump(self.decu, open(decucashfile, "wb"))
        self.decu.setELM(self.elm)
        self.decu.setLangMap(langmap)
        
        if len(self.decu.ecufname) == 0:
            return
        
        if '/' in self.decu.ecufname:
            xfn = self.decu.ecufname[:-4].split('/')[-1]
        else:
            xfn = self.decu.ecufname[:-4].split('\\')[-1]

        dumpIs = False
        for root, dirs, files in os.walk(mod_globals.dumps_dir):
            for f in files:
                if (xfn + '.') in f:
                    dumpIs = True
                    break

        if not mod_globals.opt_demo and not dumpIs and not mod_globals.opt_dump:
            answer = raw_input('Save dump ? [y/n] : ')
            if 'N' in answer.upper():
                dumpIs = True

        if mod_globals.opt_demo:
            print "Loading dump1"
            self.decu.loadDump()
        elif mod_globals.opt_dump or not dumpIs:
            print "Saving dump"
            self.decu.saveDump()
        
        if not self.decu.ecufname.startswith(mod_globals.ddtroot):
            tmp_f_name = self.decu.ecufname.split('/')[-1]
            self.decu.ecufname = 'ecus/'+tmp_f_name

        if not mod_db_manager.file_in_ddt(self.decu.ecufname):
            print "No such file: ", self.decu.ecufname
            return None

        ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
              'ns1': 'http://www-diag.renault.com/2002/screens'}

        tree = et.parse(mod_db_manager.get_file_from_ddt(self.decu.ecufname))
        xdoc = tree.getroot()
        
        scr = DDTScreen(self.decu.ecufname, xdoc, self.decu)

        del scr
        del self.decu
    
    def __del__(self):
        del self.elm
        del self.cecu
    
    def start(self):
        global resizeFont
        gui = DDTLauncher()
        gui.run()
        if not resizeFont:
            return
        resizeFont = False

class DDTLauncher(App):
    def __init__(self, filterText=None):
        global fs
        fs = mod_globals.fontSize
        self.eculist = mod_ddt_utils.loadECUlist()
        self.carecus = []
        self.var_portList = []
        self.var_speedList = []
        self.elm = None
        self.currentEcu = None
        self.v_xmlList = []
        self.v_dumpList = []
        self.pl = mod_ddt_utils.ddtProjects()
        self.ecutree = {}
        self.v_proj = ''
        self.v_addr = ''
        self.v_vin = ''
        self.v_pcan = ''
        self.v_mcan = ''
        self.dv_xml = ''
        self.var_log = ''
        self.var_can2 = ''
        self.var_cfc = ''
        self.var_port = ''
        self.var_speed = ''
        self.var_logName = ''
        self.var_dump = mod_globals.opt_dump
        self.ids = {}
        self.ptree = list()
        self.filterText = filterText
        self.progress = {}
        
        self.dv_addr = []
        optsGrid = {'ipadx': 0, 'ipady': 0, 'sticky': 'nswe'}
        optsGrid_w = {'ipadx': 0, 'ipady': 0, 'sticky': 'w'}
        optsGrid_e = {'ipadx': 0, 'ipady': 0, 'sticky': 'e'}
        btn_style = { 'activebackground':"#d9d9d9",
                      'activeforeground':"#000000",
                      'background':"#d9d9d9",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}

        ent_style = { 'background':"#FFFFFF",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}
        self.fltBtnClick()
        
        if mod_globals.savedCAR != 'Select':
            self.LoadCarFile(mod_globals.savedCAR)
        else:
            self.CarDoubleClick()
        if mod_globals.opt_scan:
            self.ScanAllBtnClick()
        
        super(DDTLauncher, self).__init__()
        Window.bind(on_keyboard=self.key_handler)

    def key_handler(self, window, keycode1, keycode2, text, modifiers):
        global resizeFont
        if resizeFont:
            return True
        if keycode1 == 45 and mod_globals.fontSize > 10:
            mod_globals.fontSize = mod_globals.fontSize - 1
            resizeFont = True
            if self.clock_event is not None:
                self.clock_event.cancel()
            self.needupdate = False
            self.running = False
            self.stop()
            return True
        if keycode1 == 61 and mod_globals.fontSize < 40:
            mod_globals.fontSize = mod_globals.fontSize + 1
            resizeFont = True
            if self.clock_event is not None:
                self.clock_event.cancel()
            self.needupdate = False
            self.running = False
            self.stop()
            return True
        return False

    def finish(self, instance):
        self.stop()
    
    def build(self):
        
        self.getDumpListByXml()
        p = 0
        if not mod_globals.opt_demo: height_g = fs*6*len([v for v in range(len(self.carecus)) if self.carecus[v]['xml'] != ''])
        else: height_g = fs*6*len(self.carecus)
        if height_g == 0: height_g = 200
        layout = GridLayout(cols=1, size_hint=(None, None),size=(fs*90, ((fs*8)+height_g)))
        layout.add_widget(self.make_savedECU())
        box = GridLayout(cols=9, spacing=3, size_hint=(1, None), height=height_g)
        box.bind(minimum_height=box.setter('height'))
        cols = ['addr', 'iso8', 'xid', 'rid', 'prot', 'type', 'name', 'xml', 'dump']
        Cols = dict(addr=['Addr', (1,0,0,1)], iso8=['ISO8', (1,0,0,1)], xid=['XId', (1,0,0,1)], rid=['RId', (1,0,0,1)], prot=['Protocol', (1,0,0,1)], type=['Type', (1,0,0,1)], name=['Name', (1,0,0,1)], xml=['XML', (1,0,0,1)], dump=['dump', (1,0,0,1)])
        for key in cols:
            if key == 'addr':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.08, 1))
            elif key == 'name':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.25, 1))
            elif key == 'iso8':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.08, 1))
            elif key == 'xid':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.08, 1))
            elif key == 'rid':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.08, 1))
            elif key == 'dump':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.7, 1))
            elif key == 'xml':
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(1, 1))
            else:
                box1 = BoxLayout(orientation='vertical', spacing=1, size_hint=(0.18, 1))
            box1.add_widget(MyLabel(text=Cols[key][0], size_hint=(1, None), height=fs*3, bgcolor=Cols[key][1]))
            i = 1
            p = len(self.carecus)+1
            for v in range(len(self.carecus)):
                if self.carecus[v]['xml'] == '' and not mod_globals.opt_demo: continue
                if key == 'name':
                    self.but_name = MyButton(text=self.carecus[v][key],  id=str(v), on_press=lambda args,v=v,bt=str(v):self.popup_xml(bt, self.carecus[v]['addr']))
                    box1.add_widget(self.but_name)
                elif key == 'xml':
                    self.but_xml = MyButton(text=self.carecus[v][key], id=str(v), font_size=fs, on_press=self.openECUS)
                    self.ids[str(v)] = self.but_xml
                    box1.add_widget(self.but_xml)
                elif key == 'dump':
                    self.but_dump = MyButton(text=self.carecus[v][key], id=str(p), on_press=self.popup_dump)
                    self.ids[str(p)] = self.but_dump
                    box1.add_widget(self.but_dump)
                    p = p+1
                else:
                    box1.add_widget(MyLabel(text=self.carecus[v][key], size_hint=(1, 1), bgcolor=(0.8,0,0,0.8)))
            box.add_widget(box1)
        layout.add_widget(box)
        quitbutton = MyButton(text='<BACK>', size_hint=(1, None), height=fs*4, on_press=self.finish)
        layout.add_widget(quitbutton)
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(layout)
        return root

    def openECUS(self, bt):
        ecu = self.getSelectedECU(bt.text)
        if ecu==None or ecu['xml']=='':
            self.MyPopup(content='Selected ECU is undefined. Please scan it first.')
            return None
        self.OpenECUScreens(ecu)
        return

    def popup_xml(self, idds, inst):
        self.dv_addr = inst
        self.getXmlListByProj()
        layout = GridLayout(cols=1, spacing=5, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))
        for v in self.v_xmlList:
            btn = MyButton(text=v, size_hint=(1, None), height=fs*4, on_press=lambda bts, ids = idds: self.select_xml(bts, ids))
            layout.add_widget(btn)
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(layout)
        self.popup = Popup(title='Select xml ECU', content=root, size_hint=(None, None), size=(Window.size[0], Window.size[1]*0.9))
        self.popup.open()

    def popup_dump(self, bt):
        id = bt.id
        layout = GridLayout(cols=1, spacing=5, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))
        for v in self.v_dumpList:
            btn = MyButton(text=v, size_hint=(1, None), height=fs*4, on_press=lambda bts, ids = bt.id: self.select_dump(bts, ids))
            layout.add_widget(btn)
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(layout)
        self.popup = Popup(title='Select dump', content=root, size_hint=(None, None), size=(Window.size[0], Window.size[1]*0.7))
        self.popup.open()
 
    def select_xml(self, bt, idds):
        self.carecus[int(idds)]['xml'] = bt.text
        self.ids[idds].text = bt.text
        self.popup.dismiss()
        self.renewEcuList()

    def select_dump(self, bt, idds):
        self.carecus[int(idds)-len(self.carecus)-1]['dump'] = bt.text
        self.ids[idds].text = bt.text
        self.popup.dismiss()
        self.renewEcuList()

    def MyDroop(self, ltr):
        global fs
        glay = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        bt_dropdown = DropDown(size_hint=(1, None))
        for v in self.v_dumpList:
            btn = MyButton(text=v)
            btn.bind(on_release=lambda btn: bt_dropdown.select(btn.text))
            bt_dropdown.add_widget(btn)
        label_val = MyButton(text='')
        label_val.bind(on_release=bt_dropdown.open)
        bt_dropdown.bind(on_select=lambda instance, x: setattr(label_val, 'text', x))
        glay.add_widget(label_val)
        return glay

    def getXmlListByProj(self):
        self.v_xmlList = []
        try:
            for t in self.eculist[self.dv_addr]['targets']:
                if self.v_proj.upper() in self.eculist[self.dv_addr]['targets'][t]['Projects']:
                    self.v_xmlList.append(t)
        except:
            pass

    def getDumpListByXml(self, xmlname=None):
        if xmlname==None:
            self.v_dumpList = []
            try:
                xml = self.dv_xml[:-4]
            except:
                xml = ''
            for root, dirs, files in os.walk(os.path.join(mod_globals.user_data_dir, 'dumps')):
                for f in files:
                    if (xml + '.') in f:
                        self.v_dumpList.append(f)
        else:
            xmlname = os.path.join(mod_globals.user_data_dir, xmlname)
            xmlname = xmlname[:-4]
            flist = []
            for root, dirs, files in os.walk(os.path.join(mod_globals.user_data_dir, 'dumps')):
                for f in files:
                    if (xmlname + '.') in f:
                        flist.append(f)
            if len(flist) == 0: return []
            flist.sort()
            return flist

    def OpenECUScreens(self, ce):
        decu = None
        try:
            self.enableELM()
            print mod_globals.opt_demo
        except:
            return
        if not mod_globals.opt_demo and self.var_dump:
            mod_globals.opt_dump = True
        else:
            mod_globals.opt_dump = False
        if 'CAN' in ce['prot'] and ce['xid']!='' and ce['rid']!='':
            pro = 'CAN'
        else:
            pro = 'KWP'
        ct1 = time.time()
        
        if pro == 'CAN':
            self.elm.init_can()
        else:
            self.elm.init_iso()
        ct2 = time.time()
        if ct2-ct1 > 5:
            self.MyPopup(title='ERROR', content='ELM is not responding well.')
            return
        self.setEcuAddress(ce, pro)
        self.elm.start_session(ce['ses'])
        decucashfile = os.path.join(mod_globals.cache_dir, "ddt_" + ce['xml'][:-4] + ".p")
        if os.path.isfile(decucashfile):
            decu = pickle.load(open(decucashfile, "rb"))
        else:
            decu = DDTECU(None)
            decu.loadXml('ecus/'+ce['xml'])
            if len(decu.ecufname) > 0:
                pickle.dump(decu, open(decucashfile, "wb"))
        decu.setELM(self.elm)
        if len(decu.ecufname) == 0:
            return
        if '/' in decu.ecufname:
            xfn = decu.ecufname[:-4].split('/')[-1]
        else:
            xfn = decu.ecufname[:-4].split('\\')[-1]
        dumpIs = False
        for root, dirs, files in os.walk(mod_globals.dumps_dir):
            for f in files:
                if (xfn + '.') in f:
                    dumpIs = True
                    break
        os.path.join(mod_globals.dumps_dir, )
        if mod_globals.opt_demo:
            print "Loading dump"
            
            if len(ce['dump'])==0:
                decu.loadDump()
            else:
                decu.loadDump(os.path.join(mod_globals.dumps_dir, ce['dump']))
        elif mod_globals.opt_dump:
            ce['dump'] = self.guiSaveDump(decu)
            for ec in self.carecus:
                if ce['xml'][:-4] in ec['xml']:
                    ec['dump'] = ce['dump']
            self.renewEcuList()
            self.SaveBtnClick()

        if not mod_db_manager.file_in_ddt(decu.ecufname):
            print "No such file: ", decu.ecufname
            return None
        ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
              'ns1': 'http://www-diag.renault.com/2002/screens'}
        tree = et.parse(mod_db_manager.get_file_from_ddt(decu.ecufname))
        xdoc = tree.getroot()
        print "Show screen"
        scr = DDTScreen(decu.ecufname, xdoc, decu, top=True)
        del scr
        del decu

    def renewEcuList(self):
        print 'renewEcuList'
        self.ecutree = []
        for ecu in mod_ddt_utils.multikeysort( self.carecus, ['undef','addr']):
            columns = (ecu['iso8'], ecu['xid'], ecu['rid'], ecu['prot'], ecu['type'], ecu['name'], ecu['xml'], ecu['dump'], ecu)
            if ecu['undef']=='0':
                self.ecutree.append(dict(text=ecu['addr'], values=columns, tag='t1'))
            else:
                self.ecutree.append(dict(text=ecu['addr'], values=columns, tag=''))

    def LoadCarFile(self, filename):
        filename = os.path.join(mod_globals.user_data_dir, filename)
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as fin:
            lines = fin.read().splitlines()

        self.carecus = []
        for l in lines:
            l = l.strip()
            if len(l)==0 or l.startswith('#'):
                continue
            li = l.split(';')
            if li[0].lower()=='car':
                self.v_proj = li[1]
                self.v_addr = li[2]
                self.v_pcan = li[3]
                self.v_mcan = li[4]
                self.v_vin = li[5]
            else:
                ecu = {}
                ecu['undef'] = li[0]
                ecu['addr'] = li[1]
                ecu['iso8'] = li[2]
                ecu['xid'] = li[3]
                ecu['rid'] = li[4]
                ecu['prot'] = li[5]
                ecu['type'] = li[6]
                ecu['name'] = li[7]
                ecu['xml'] = li[8]
                ecu['dump'] = li[9]
                ecu['ses']  = li[10]
                self.carecus.append(ecu)
        self.renewEcuList()

    def make_savedECU(self):
        glay = BoxLayout(orientation='horizontal', size_hint=(1, None), height=4*fs)
        label1 = MyLabel(text='Name savedCAR:', size_hint=(0.5, 1), bgcolor=(0,0.5,0,1))
        lab = mod_globals.savedCAR[9:-4]
        self.label = TextInput(text=lab, size_hint=(1, 1), padding=[0, fs/2])
        self.savedECU = MyButton(text='Save', size_hint=(0.5, 1), on_press=lambda args: self.SaveBtnClick(self.label.text))
        glay.add_widget(label1)
        glay.add_widget(MyLabel(text='savedCAR_', size_hint=(0.5, 1), halign='right', bgcolor=(0.5,0,0,1)))
        glay.add_widget(self.label)
        glay.add_widget(self.savedECU)
        return glay

    def SaveBtnClick(self, name):
        filename = os.path.join(mod_globals.user_data_dir, './savedCAR_'+name+'.csv')
        with open( filename, 'w') as fout:
            car = ['car',self.v_proj, self.v_addr, self.v_pcan, self.v_mcan, self.v_vin]
            fout.write(';'.join(car)+'\n')
            for ecu in self.carecus:
                e = [ecu['undef'],
                     ecu['addr'],
                     ecu['iso8'],
                     ecu['xid'],
                     ecu['rid'],
                     ecu['prot'],
                     ecu['type'],
                     ecu['name'],
                     ecu['xml'],
                     ecu['dump'],
                     ecu['ses']]
                fout.write(unicode(';'.join(e)).encode("ascii", "ignore") + '\n')
        fout.close()

        copyfile(filename, os.path.join(mod_globals.user_data_dir, "./savedCAR_prev.csv"))
        self.MyPopup(content='Save file ECUS name savedCAR_'+name+'.csv', height=fs*30)
        return

    def fltBtnClick(self, ev=None):
        self.ptree = {}
        if self.filterText:
            ptrn = self.filterText.split(':')[0].strip().lower()
            self.v_proj = ptrn
            for m in self.pl.plist:
                for c in m['list']:
                    if ptrn:
                        if len(ptrn)==0 or ptrn.lower() in str(c).lower():
                            self.ptree = dict(name = [m['name']], iid = c['code'], text = c['code'], values = [c['name'],c['segment'],c['addr']])

    def CarDoubleClick(self):
        try:
            line = self.ptree['values']
            self.addr = mod_ddt_utils.ddtAddressing(line[2])
        except:
            pass
        tmpL = []
        self.carecus = []
        for e in self.addr.alist:
            if e['Address']==0:
                self.v_pcan = (e['baudRate'])
                continue
            if e['Address']==255:
                self.v_mcan = (e['baudRate'])
                continue

            if 'en' in e['longname'].keys():
                longname = e['longname']['en']
            else:
                longname = e['longname'].values()[0]

            if e['Address']:
                v_addr = hex(int(e['Address']))[2:].upper()
                if len(v_addr)==1:
                    v_addr = '0'+v_addr
            else:
                v_addr = ''
            if e['ISO8']:
                v_iso = hex(int(e['ISO8']))[2:].upper()
                if len(v_iso)==1:
                    v_addr = '0'+v_iso
            else:
                v_iso = ''
            if e['XId']:
                if len(e['XId'])>6:
                    v_XId = hex(0x80000000+int(e['XId']))[2:].upper()
                else:
                    v_XId = hex(int(e['XId']))[2:].upper()
            else:
                v_XId = ''
            if e['RId']:
                if len(e['RId'])>6:
                    v_RId = hex(0x80000000+int(e['RId']))[2:].upper()
                else:
                    v_RId = hex(int(e['RId']))[2:].upper()
            else:
                v_RId = ''

            if e['protocol']=='6' and (v_XId=='' or v_RId==''):
                continue

            key = e['protocol'] + v_addr

            if key in tmpL:
                continue

            tmpL.append(key)

            v_prot = e['protocol']
            if e['protocol']=='1':
                v_prot = 'ISO8'
            elif e['protocol']=='2' or e['protocol']=='3':
                v_prot = 'KWP-SLOW'
            elif e['protocol']=='4' or e['protocol']=='5':
                v_prot = 'KWP-FAST'
            elif e['protocol']=='6' and self.v_pcan=='250000':
                v_prot = 'CAN-250'
            elif e['protocol']=='6':
                v_prot = 'CAN-500'

            ecu = {}
            ecu['undef'] = '1'
            ecu['addr'] = v_addr
            ecu['iso8'] = v_iso
            ecu['xid'] = v_XId
            ecu['rid'] = v_RId
            ecu['prot'] = v_prot
            ecu['type'] = e['Name']
            ecu['name'] = longname
            ecu['xml'] = ''
            ecu['dump'] = ''
            ecu['ses'] = ''
            self.carecus.append(ecu)
        self.renewEcuList()

    def getSelectedECU(self, xml):
        if len(self.ecutree)==0:
            pop = "Please select the project in the left list and then ECU in the bottom"
        else:
            pop = "Please select an ECU in the bottom list"
        if not xml:
            self.MyPopup(content=pop)
            return None
        else:
            try:
                line = [self.ecutree[v]['values'] for v in range(len(self.ecutree)) if xml in self.ecutree[v]['values']][0]
            except:
                self.MyPopup(content=pop)
                return None
            try:
                ecu = ast.literal_eval(line[8])
            except:
                import json
                ecu = ast.literal_eval(json.dumps(line[8], ensure_ascii=False).encode('utf8'))
            return ecu

    def setEcuAddress(self, ce, pro ):
        ecudata = {'idTx': ce['xid'],
                   'idRx': ce['rid'],
                   'slowInit': '',
                   'fastInit': '',
                   'ModelId': ce['addr'],
                   'ecuname': 'ddt_unknown',
                   }
        if pro == 'CAN':
            if ce['prot'] == 'CAN-250':
                ecudata['protocol'] = 'CAN_250'
                ecudata['brp'] = '01'
            else:
                ecudata['protocol'] = 'CAN_500'
                ecudata['brp'] = '0'

            ecudata['pin'] = 'can'
            self.elm.set_can_addr(ce['addr'], ecudata)

        if pro == 'KWP' or pro == 'ISO':
            if ce['prot'] == 'KWP-FAST':
                ecudata['protocol'] = 'KWP_Fast'
                ecudata['fastInit'] = ce['addr']
                ecudata['slowInit'] = ''
                mod_globals.opt_si = False
            elif ce['prot'] == 'ISO8' and ce['iso8'] != '':
                ecudata['protocol'] = 'KWP_Slow'
                ecudata['fastInit'] = ''
                ecudata['slowInit'] = ce['iso8']
                mod_globals.opt_si = True
            else:
                ecudata['protocol'] = 'KWP_Slow'
                ecudata['fastInit'] = ''
                ecudata['slowInit'] = ce['addr']
                mod_globals.opt_si = True
            ecudata['pin'] = 'iso'
            self.elm.set_iso_addr(ce['addr'], ecudata)

    def ScanAllBtnClick(self):
        try:
            self.enableELM()
        except:
            return
        if self.elm==None or self.elm.port==0:
            self.MyPopup(title="ERROR", content="ELM is not connected. You may work only offline.")
            return
        scansequence = ['CAN','KWP','ISO']
        vins = {}
        lbltxt = Label(text='Init', font_size=20)
        popup_scan = Popup(title='Scanning CAN bus', content=lbltxt, size=(400, 400), size_hint=(None, None))
        base.runTouchApp(slave=True)
        popup_scan.open()
        EventLoop.idle()
        self.progress['maximum'] = len(self.carecus)+1
        progressValue = 1
        self.progress['value'] = progressValue
        i = 1
        u = 0
        lbltxt.text = 'Scanning:' + str(i) + '/' + str(len(self.carecus)) + ' Detected: ' + str(u)
        EventLoop.idle()
        for pro in scansequence:
            if pro == 'CAN':
                self.elm.init_can()
            else:
                self.elm.init_iso()
            for ce in self.carecus:
                if pro in ce['prot'] or ce['prot']=='':
                    lbltxt.text = 'Scanning:' + str(i) + '/' + str(len(self.carecus)) + ' Detected: ' + str(u)
                    i += 1
                    EventLoop.idle()
                    self.setEcuAddress(ce, pro)
                    progressValue = progressValue + 1
                    self.progress['value'] = progressValue
                    
                    (StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN) = mod_scan_ecus.readECUIds(self.elm)
                    if DiagVersion=='' and DiagVersion=='' and Version=='' and Soft=='' and VIN=='':
                        continue
                    u += 1
                    candlist = mod_ddt_ecu.ecuSearch(self.v_proj, ce['addr'], DiagVersion, Supplier, Soft, Version,self.eculist, interactive = False)
                    ce['xml'] = candlist[0]
                    ce['ses'] = StartSession
                    ce['undef'] = '0'
                    tmp = self.getDumpListByXml(ce['xml'])
                    if len(tmp)>0:
                        ce['dump'] = tmp[-1]
                    else:
                        ce['dump'] = ''

                    if VIN!='':
                        if VIN not in vins.keys():
                            vins[VIN] = 1
                        else:
                            vins[VIN] = vins[VIN] + 1
                
                    self.renewEcuList()
        EventLoop.window.remove_widget(popup_scan)
        popup_scan.dismiss()
        base.stopTouchApp()
        EventLoop.window.canvas.clear()
        del popup_scan
        if self.v_vin=='' and len(vins.keys()):
            self.v_vin = (max(vins.iteritems(), key=operator.itemgetter(1))[0])
        print self.progress
        self.progress['value'] = 0
        return

    def enableELM(self):
        if self.elm != None:
            try:
                self.elm.port.hdr.close()
                del(self.elm)
                self.elm = None
                gc.collect()
            except:
                pass
        try:
            self.elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)
        except:
            labelText = '''
                Could not connect to the ELM.

                Possible causes:
                - Bluetooth is not enabled
                - other applications are connected to your ELM e.g Torque
                - other device is using this ELM
                - ELM got unpaired
                - ELM is read under new name or it changed its name

                Check your ELM connection and try again.
            '''
            lbltxt = Label(text=labelText, font_size=mod_globals.fontSize)
            popup_load = Popup(title='ELM connection error', content=lbltxt, size=(800, 800), auto_dismiss=True, on_dismiss=exit)
            popup_load.open()
            base.runTouchApp()
        if mod_globals.opt_speed < mod_globals.opt_rate and not mod_globals.opt_demo:
            self.elm.port.soft_boudrate(mod_globals.opt_rate)

    def MyPopup(self, title=None, content=None, height=None, weigh=None):
        if title:
            title = title
        else:
            title = 'INFO'
        if content:
            content = content
        else:
            content = 'INFO'
        if not height:
            height = Window.size[1]*0.7
        if not weigh:
            weigh = Window.size[0]
        label = MyLabel(text=content, size_hint=(1, 1))
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1, 1))
        layout.add_widget(label)
        btn = MyButton(text='CLOSE')
        layout.add_widget(btn)
        popup = Popup(title=title, content=layout, size_hint=(None, None), size=(weigh, height))
        popup.open()
        btn.bind(on_press=popup.dismiss)