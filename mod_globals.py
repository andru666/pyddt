#!/usr/bin/env python
import os as sysos
import pickle
ns = {'ns0': 'http://www-diag.renault.com/2002/ECU', 'ns1': 'http://www-diag.renault.com/2002/screens'}
opt_debug = False
debug_file = None
savedEcus = ''
opt_dev_address = ''
opt_port = ""
opt_ecu = ''
opt_ecuid_on = ''
savedCAR = ''
opt_ecuid = ""
opt_ecuAddr = ""
opt_protocol = ""
opt_speed = 38400
opt_rate = 38400
opt_lang = ""
opt_car = ""
opt_log = ""
opt_demo = False
opt_scan = False
opt_csv = False
opt_csv_only = False
opt_csv_human = False
opt_usrkey = ""
opt_verbose = False
opt_cmd = False
opt_ddt = False
screen_orient = False
opt_si = False
opt_cfc0 = False
opt_caf = False
opt_n1c = False
opt_dev = False
opt_devses = '1086'
opt_exp = False
opt_dump = False
opt_can2 = False
opt_ddtxml = ""
opt_obdlink = False
opt_stn = False
opt_sd = False
opt_perform = False
opt_minordtc = False
dumpName = ""
fontSize = 20

state_scan = False

currentDDTscreen = None

ext_cur_DTC = "000000"

none_val = "None"

user_data_dir = "./"
cache_dir = "./cache/"
log_dir = "./logs/"
dumps_dir = "./dumps/"
ddt_arc = ""
ddtroot = ".."
clip_arc = ""
cliproot = ".."

os = ""

language_dict = {}

vin = ""

doc_server_proc = None

class Settings:
    opt_ecu = ''
    port = ''
    lang = ''
    log = True
    logName = 'log.txt'
    cfc = False
    si = False
    demo = False
    fontSize = 20
    screen_orient = False
    useDump = False
    csv = False
    dev_address = ''
    
    def __init__(self):
        global opt_ecu
        global opt_si
        global opt_log
        global opt_dump
        global fontSize
        global opt_port
        global opt_cfc0
        global screen_orient
        global opt_demo
        global opt_csv
        global opt_dev_address
        self.load()
        opt_ecu = self.opt_ecu
        opt_si = self.si
        opt_log = self.logName
        opt_dump = self.useDump
        fontSize = self.fontSize
        opt_port = self.port
        opt_cfc0 = self.cfc
        screen_orient = self.screen_orient
        opt_demo = self.demo
        opt_csv = self.csv
        opt_dev_address = self.dev_address

    def __del__(self):
        self.save()
        
    def load(self):
        if not sysos.path.isfile(user_data_dir + '/settings.p'):
            self.save()
        try:
            f = open(user_data_dir + '/settings.p', 'rb')
            tmp_dict = pickle.load(f)
            f.close()
        except:
            sysos.remove(user_data_dir + '/settings.p')
            self.save()
            f = open(user_data_dir + '/settings.p', 'rb')
            tmp_dict = pickle.load(f)
            f.close()
        self.__dict__.update(tmp_dict)        
    
    def save(self):
        self.opt_ecu = opt_ecu
        self.si = opt_si
        self.logName = opt_log
        self.useDump = opt_dump
        self.fontSize = fontSize
        self.port = opt_port
        self.cfc = opt_cfc0
        self.screen_orient = screen_orient
        self.demo = opt_demo
        self.csv = opt_csv
        self.dev_address = opt_dev_address
        f = open(user_data_dir + '/settings.p', 'wb')
        pickle.dump(self.__dict__, f)
        f.close()