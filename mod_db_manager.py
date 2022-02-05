#!/usr/bin/env python

import os
import re
import glob
import shutil
import zipfile
import mod_globals

db_dir_list = [
    ".",
    ".."
]
android_dir_list = [
    "/mnt/sdcard/pyren"
]
ARCHIVE_FILE = 'DDT2000data.zip'
ZIPARCHIVE = None
def find_DBs():

    global ARCHIVE_FILE
    global ZIPARCHIVE
    if ZIPARCHIVE is not None:
        return ZIPARCHIVE
    df_list = sorted(glob.glob(os.path.join(mod_globals.user_data_dir, 'DDT2000data*.zip')), reverse=True)
    if len(df_list):
        ARCHIVE_FILE = df_list[0]
    else:
        df_list = sorted(glob.glob(os.path.join('./', 'DDT2000data*.zip')), reverse=True)
        if len(df_list):
            ARCHIVE_FILE = df_list[0]
    if not os.path.exists(ARCHIVE_FILE):
        return
    mod_globals.ddtroot = ARCHIVE_FILE
    mod_globals.ddt_arc = zipfile.ZipFile(df_list[0])




def saveDBver(verfilename):
    # create new version file
    verfile = open(verfilename, "wb")
    verfile.write(':'.join([mod_globals.cliproot, mod_globals.ddtroot]) + '\n')
    verfile.write("Do not remove me if you have v0.9.q or above.\n")
    verfile.close()


################### CLIP ###################

def get_file_list_from_clip( pattern ):
    if mod_globals.clip_arc=='':
        fl =  glob.glob(os.path.join(mod_globals.cliproot, pattern))
    else:
        if '*' in pattern:
            pattern = pattern.replace('*', '\d{3}')
        file_list = mod_globals.clip_arc.namelist()
        regex = re.compile(pattern)
        fl = list(filter(regex.search, file_list))
    res = []
    for i in fl:
        while len(i) and i[0] in ['.','/','\\']:
            i = i[1:]
        res.append(i)
    return res

def get_file_from_clip( filename ):
    if (filename.lower().endswith('bqm')
            or '/sg' in filename.lower() \
            or '\\sg' in filename.lower()):
        mode = 'rb'
    else:
        mode = 'r'

    if (mod_globals.os == 'android'
            or mod_globals.clip_arc != ''):
        mode = 'r'

    if mod_globals.clip_arc=='':
        return open(os.path.join(mod_globals.cliproot, filename), mode)
    else:
        if filename.startswith('../'):
            filename = filename[3:]
        try:
            f = mod_globals.clip_arc.open(filename, mode)
            return f
        except:
            fn = filename.split('/')[-1]
            lfn = fn.lower()
            filename = filename.replace(fn,lfn)
            return mod_globals.clip_arc.open(filename, mode)

def file_in_clip( pattern ):
    if mod_globals.clip_arc=='':
        pattern = os.path.join(mod_globals.cliproot, pattern)
        return pattern in glob.glob(pattern)
    else:
        file_list = mod_globals.clip_arc.namelist()
        return pattern in file_list

def extract_from_clip_to_cache( filename ):
    if mod_globals.clip_arc == '':
        print "Error in extract_from_clip_to_cache"
    else:
        source = mod_globals.clip_arc.open(filename)
        target = open(os.path.join(mod_globals.cache_dir, os.path.basename(filename)), "wb")
        with source, target:
            shutil.copyfileobj(source, target)

################### DDT ###################

def get_file_list_from_ddt( pattern ):
    if mod_globals.ddt_arc=='':
        return glob.glob(os.path.join(mod_globals.ddtroot, pattern))
    else:
        file_list = mod_globals.ddt_arc.namelist()
        regex = re.compile(pattern)
        return list(filter(regex.search, file_list))

def file_in_ddt( pattern ):
    if mod_globals.ddt_arc=='':
        li = glob.glob(os.path.join(mod_globals.ddtroot, pattern))
    else:
        file_list = mod_globals.ddt_arc.namelist()
        if '(' in pattern:
            pattern = pattern.replace('(','\(')
        if ')' in pattern:
            pattern = pattern.replace(')', '\)')
        regex = re.compile(pattern)
        li = list(filter(regex.search, file_list))
    return len(li)

def path_in_ddt( pattern ):
    if mod_globals.ddt_arc=='':
        li = glob.glob(os.path.join(mod_globals.ddtroot, pattern))
    else:
        file_list = mod_globals.ddt_arc.namelist()
        regex = re.compile(pattern)
        li = list(filter(regex.search, file_list))
    if len(li)>0:
        return True
    else:
        return False

def get_file_from_ddt( filename ):
    return mod_globals.ddt_arc.open(filename, 'r')

def extract_from_ddt_to_cache( filename ):
    targ_file = os.path.join(mod_globals.cache_dir, filename)
    try:
        if mod_globals.ddt_arc == '':
            source = open(os.path.join(mod_globals.ddtroot, filename))
        else:
            source = mod_globals.ddt_arc.open(filename)

        if not os.path.exists(os.path.dirname(targ_file)):
            os.makedirs(os.path.dirname(targ_file))

        target = open(targ_file, "wb")

        with source, target:
            shutil.copyfileobj(source, target)
        return targ_file
    except:
        return False

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    find_DBs()
