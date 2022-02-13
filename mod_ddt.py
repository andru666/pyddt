#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, operator, ast, gc, time

import mod_ddt_utils
import mod_db_manager
from shutil import copyfile
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
import xml.etree.ElementTree as et
from xml.dom.minidom import parse
import xml.dom.minidom
from kivy.core.window import Window
from kivy import base
from kivy.app import App
from kivy.clock import Clock
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
from kivy.utils import platform

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
resizeFont = False

class DDT():
    decu = None
    cecu = None
    
    def __init__(self, elm, cecu, langmap={}):
        self.elm = elm
        self.cecu = cecu
        
        decucashfile = "./cache/ddt_" + cecu['ModelId'] + ".p"
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
        for root, dirs, files in os.walk("./dumps"):
            for f in files:
                if (xfn + '.') in f:
                    dumpIs = True
                    break

        if not mod_globals.opt_demo and not dumpIs and not mod_globals.opt_dump:
            answer = raw_input('Save dump ? [y/n] : ')
            if 'N' in answer.upper():
                dumpIs = True

        if mod_globals.opt_demo:
            print "Loading dump"
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
        gui = showDatarefGui()
        gui.run()
        if not resizeFont:
            return
        resizeFont = False

    def enableELM(self):

        # print self.elm
        if self.elm != None:
            try:
                self.elm.port.hdr.close()
                del(self.elm)
                self.elm = None
                gc.collect()
            except:
                pass

        self.applySettings()

        try:
            self.elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)
        except:
            result = tkMessageBox.askquestion("Warning", "ELM is not connected. Would you like to work OFF-line?", icon='warning')
            if result == 'yes':
                mod_globals.opt_demo = True
                self.elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)
            else:
                raise Exception('elm is not connected')
                return

        # change serial port baud rate
        if mod_globals.opt_speed < mod_globals.opt_rate and not mod_globals.opt_demo:
            self.elm.port.soft_boudrate(mod_globals.opt_rate)


class DDTLauncher():
    
    def ScanAllBtnClick(self):

        # Enable ELM
        try:
            self.enableELM()
        except:
            return

        if self.elm==None or self.elm.port==0:
            tkMessageBox.showinfo("ERROR", "ELM is not connected. You may work only offline.")
            return


        # for all carecus find can ecus, then k-line ecus
        scansequence = ['CAN','KWP','ISO']
        vins = {}
        self.progress['maximum'] = len(self.carecus)+1
        progressValue = 1
        self.progress['value'] = progressValue
        for pro in scansequence:

            # init protocol
            if pro == 'CAN':
                self.elm.init_can()
            else:
                self.elm.init_iso()

            for ce in self.carecus:
                if pro in ce['prot'] or ce['prot']=='':

                    # set address
                    self.setEcuAddress(ce, pro)

                    progressValue = progressValue + 1
                    self.progress['value'] = progressValue
                    self.progress.update()

                    # get ID
                    (StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN) = mod_scan_ecus.readECUIds(self.elm)

                    if DiagVersion=='' and DiagVersion=='' and Version=='' and Soft=='' and VIN=='':
                        continue

                    candlist = mod_ddt_ecu.ecuSearch(self.v_proj.get(), ce['addr'],
                                                     DiagVersion, Supplier, Soft, Version,
                                                     self.eculist, interactive = False)
                    ce['xml'] = candlist[0]
                    ce['ses'] = StartSession
                    ce['undef'] = '0'
                    tmp = self.getDumpListByXml(ce['xml'])
                    if len(tmp)>0:
                        ce['dump'] = tmp[-1]
                    else:
                        ce['dump'] = ''


                    # count most frequent VINs
                    if VIN!='':
                        if VIN not in vins.keys():
                            vins[VIN] = 1
                        else:
                            vins[VIN] = vins[VIN] + 1

                    self.renewEcuList()

        if self.v_vin.get()=='' and len(vins.keys()):
          self.v_vin.set(max(vins.iteritems(), key=operator.itemgetter(1))[0])

        self.progress['value'] = 0
        return
    
def optParser():
    '''Parsing of command line parameters. User should define at least com port name'''
    '''Not used in current version'''

    import argparse

    parser = argparse.ArgumentParser(
        # usage = "%prog -p <port> [options]",
        version="mod_ddt Version 0.9.q",
        description="mod_ddt - python program for diagnostic Renault cars"
    )

    parser.add_argument('-p',
                        help="ELM327 com port name",
                        dest="port",
                        default="")

    parser.add_argument("-r",
                        help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
                        dest="rate",
                        default="38400", )

    parser.add_argument("-a",
                        help="functional address of ecu",
                        dest="ecuAddr",
                        default="")

    parser.add_argument("-i",
                        help="interface protocol [can250|250|can500|500|kwpS|S|kwpF|F]",
                        dest="protocol",
                        default='500')

    parser.add_argument("-L",
                        help="language option {RU[default],GB,FR,IT,...}",
                        dest="lang",
                        default="RU")

    parser.add_argument("--cfc",
                        help="turn off automatic FC and do it by script",
                        dest="cfc",
                        default=False,
                        action="store_true")

    parser.add_argument("--n1c",
                        help="turn off L1 cache",
                        dest="n1c",
                        default=False,
                        action="store_true")

    parser.add_argument("--log",
                        help="log file name",
                        dest="logfile",
                        default="")

    parser.add_argument("--xml",
                        help="xml file name",
                        dest="ddtxml",
                        default="")

    parser.add_argument("--demo",
                        help="for debuging purpose. Work without car and ELM",
                        dest="demo",
                        default=False,
                        action="store_true")

    parser.add_argument("--dump",
                        help="dump responces from all 21xx and 22xxxx requests",
                        dest="dump",
                        default=True,
                        action="store_true")

    parser.add_argument("--exp",
                        help="swith to Expert mode (allow to use buttons in DDT)",
                        dest="exp",
                        default=False,
                        action="store_true")

    options = parser.parse_args()

    if not options.port and mod_globals.os != 'android':
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print ""
        print "Available COM ports:"
        for port, desc, hwid in iterator:
            print "%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc.decode("windows-1251"), hwid)
        print ""
        exit(2)
    else:
        mod_globals.opt_port = options.port
        mod_globals.opt_ecuAddr = options.ecuAddr.upper()
        mod_globals.opt_rate = int(options.rate)
        mod_globals.opt_lang = options.lang
        mod_globals.opt_log = options.logfile
        mod_globals.opt_demo = options.demo
        mod_globals.opt_dump = options.dump
        mod_globals.opt_exp = options.exp
        mod_globals.opt_cfc0 = options.cfc
        mod_globals.opt_n1c = options.n1c
        mod_globals.opt_ddtxml = options.ddtxml
        if 'S' in options.protocol.upper():
            mod_globals.opt_protocol = 'S'
        elif 'F' in options.protocol.upper():
            mod_globals.opt_protocol = 'F'
        elif '250' in options.protocol:
            mod_globals.opt_protocol = '250'
        elif '500' in options.protocol:
            mod_globals.opt_protocol = '500'
        else:
            mod_globals.opt_protocol = '500'

    
class showDatarefGui(App):
    
    def __init__(self):
        super(showDatarefGui, self).__init__()
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
        layout = GridLayout(cols=1, spacing=(4, 4), size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        quitbutton = Button(text='<BACK>', size_hint=(1, None), on_press=self.finish)
        layout.add_widget(quitbutton)
        root = ScrollView(size_hint=(None, None), size=Window.size, do_scroll_x=False, pos_hint={'center_x': 0.5,'center_y': 0.5})
        root.add_widget(layout)
        return root
        

def main():
    gui = showDatarefGui(self, datarefs, path)
    gui.run()

if __name__ == '__main__':
    main()