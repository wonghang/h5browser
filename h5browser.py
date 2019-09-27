#!/usr/bin/python3
# -*- coding: utf-8 -*-
import h5py
import numpy as np
from cmd import Cmd
import signal, fcntl, termios, struct, os, sys, traceback, unicodedata

kE=chr(27)
kRed=kE + '[1;31m'
kGreen=kE + '[1;32m'
kYellow=kE + '[1;33m'
kBlue=kE + '[1;34m'
kPurple=kE + '[1;35m'
kCyan=kE + '[1;36m'
kWhite=kE + '[1;37m'
kReset=kE + '[0m'

def _hdf5_safe_write(grp,k,v):
    if k in grp:
        del grp[k]
    grp[k] = v

def _pydict_to_hdf5(d):
    Ustr = h5py.special_dtype(vlen=str)
    type_row = []
    val_row = []
    ks = d.keys()
    for k in ks:
        v = d[k]
        if isinstance(v,str):
            t = Ustr
        elif isinstance(v,int):
            t = '<i4'
        elif isinstance(v,float):
            t = '<f8'
        elif isinstance(v,complex):
            t = '<c16'
        elif isinstance(v,bool):
            t = '|b1'
        else:
            raise TypeError("_pydict_to_hdf5: Unsupported type %s" % repr(type(d[k])))
        type_row.append((k,t))
        val_row.append(v)
    dtype = np.dtype(type_row)
    np_row = np.empty(shape=(1,1),dtype=dtype)
    np_row[0] = tuple(val_row)
    return np_row

class hdf5_group_mapper:
    def __init__(self,g):
        self.g = g

    def __getitem__(self,k):
        return self.g[k][()]

    def __setitem__(self,k,v):
        raise ValueError("Read-only")

def unicode_width(string):
    return sum(1+(unicodedata.east_asian_width(c) in "WF") for c in string)

def getTerminalSize():
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])

def require_readwrite(f):
    def wrapper(self,*a,**ka):
        if self.readonly:
            print("This command requires read-write mode. Please switch to read-write mode using command \"rw\" first")
            return
        try:
            r = f(self,*a,**ka)
        except:
            raise
        finally:
            self.h5.flush()
        return r
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

class h5browser(Cmd):
    def __init__(self,h5path,readonly=True):
        Cmd.__init__(self)

        self.h5path = h5path
        self.readonly = True
        self.h5 = None
        self.cgrp = None

        if not self.open_hdf5():
            self.readonly = False
            self.open_hdf5()

        self.update_prompt()

    def open_hdf5(self):
        if self.cgrp is not None:
            path = self.cgrp.name
        else:
            path = None

        if self.h5 is not None:
            self.h5.flush()
            self.h5.close()
            del self.h5

        if self.readonly:
            print("Opening %s (read-only)..." % self.h5path)
            try:
                self.h5 = h5py.File(self.h5path,'r',libver='earliest')
            except IOError:
                yn = input("%s not found. Do you want to create it [y/n]? " % self.h5path)
                if yn.lower() in ("y","yes"):
                    return False
                else:
                    raise
        else:
            print("Opening %s (read-write)..." % self.h5path)
            self.h5 = h5py.File(self.h5path,'a',libver='earliest')
        if path is None:
            self.cgrp = self.h5
        else:
            self.cgrp = self.h5[path]
        return True

    def update_prompt(self):
        if self.readonly:
            self.prompt = "%s$ " % self.cgrp.name
        else:
            self.prompt = "%s# " % self.cgrp.name

    def postcmd(self,stop,line):
        self.update_prompt()
        return stop

    def precmd(self,line):
        line = line.strip()
        return line

    def emptyline(self):
        pass

    def do_cd(self,argv):
        """cd (path|..|) - switch to different path"""
        try:
            if argv == "":
                self.cgrp = self.h5
            elif argv == "..":
                parts = self.cgrp.name.split(u'/')[0:-1]
                argv = "/".join(parts)
                if len(argv) == 0:
                    self.cgrp = self.h5
                else:
                    self.cgrp = self.h5[argv]
            else:
                newgrp = self.cgrp[argv]
                if isinstance(newgrp,h5py.Group):
                    self.cgrp = newgrp
                else:
                    print("Path \"%s\" is not a group" % argv)
        except ValueError:
            print("Path \"%s\" does not exist" % argv)
        except KeyError:
            print("Path \"%s\" does not exist" % argv)

    def do_print(self,argv):
        """print/p/cat (path) - Print out the detail of a dataset. The first line is the data shape."""
        try:
            g = self.cgrp[argv]
            print("%s %s" % (repr(g.shape),repr(g.dtype)))
            v = g[()]
            print(repr(v))
        except AttributeError:
            print("Path \"%s\" does not appear to be a Dataset" % argv)
        except KeyError:
            print("Path \"%s\" does not exist" % argv)
    do_p=do_print
    do_cat=do_print

    def do_dump(self,argv):
        """dump (path) - Dump a dataset (as list) to the screen. (It may take some time if the dataset is too big)"""
        try:
            g = self.cgrp[argv]
            v = g[()]
            print(v.tolist())
        except AttributeError:
            print("Path \"%s\" does not appear to be a Dataset" % argv)
        except KeyError:
            print("Path \"%s\" does not exist" % argv)

    def do_eval(self,argv):
        """eval (python code) - Evaluate a python code. numpy is accessible using np."""
        rw = False
        # check if argv contains = 
        p = argv.find('=')
        if p > 0:
            try:
                p2 = argv[p+1]
                if p2 != '=':
                    rw = True
                    name = argv[0:p].strip()
                    code = argv[p+1:].strip()
            except IndexError:
                pass

        try:
            if rw:
                self.eval_rw(name,code)
            else:
                self.eval_ro(argv)
        except:
            sys.stderr.write(traceback.format_exc())
            sys.stderr.flush()
    default=do_eval

    def eval_ro(self,code):
        r = eval(code,{'__builtin__':None,'np':np},hdf5_group_mapper(self.cgrp))
        print(r)

    @require_readwrite
    def eval_rw(self,name,code):
        r = eval(code,{'__builtin__':None,'np':np},hdf5_group_mapper(self.cgrp))
        if isinstance(r,dict):
            r = _pydict_to_hdf5(r)
        _hdf5_safe_write(self.cgrp,name,r)

    def do_pwd(self,argv):
        """pwd - Print the current path and all the attributes assigned to the current group"""
        print("%s" % self.cgrp.name)
        for (k,v) in self.cgrp.attrs.items():
            print("%s => %s" % (k,v))

    def do_ls(self,argv):
        """ls (path) - List all the subgroup and dataset inside the current group"""
        cgrp = self.cgrp
        ks = list(cgrp.keys())
        ks.sort()
        if len(ks) == 0:
            return

        ml = max(map(unicode_width,ks))
        (cols,rows) = getTerminalSize()
        n_per_rows = max(cols//(ml+3),1)

        f = lambda s: s + (" "*(ml-unicode_width(s)+1))

        c = 0
        for k in ks:
            b = []
            g = cgrp[k]
            if isinstance(g,h5py.Group):
                b.append(kBlue)
                b.append(f(k))
                b.append(kReset)
            elif isinstance(g,h5py.Dataset):
                v = g.shape
                if len(v) > 0:
                    b.append(kGreen)
                    b.append(f(k))
                    b.append(kReset)
                else:
                    b.append(f(k))
            else:
                b.append(kRed)
                b.append(f(k))
                b.append(kReset)
            b = "".join(b)
            sys.stdout.write(b)
            c += 1
            if c >= n_per_rows:
                c = 0
                sys.stdout.write("\n")
            else:
                sys.stdout.write(" ")
        if c != 0:
            sys.stdout.write("\n")
        sys.stdout.flush()

    def do_quit(self,argv):
        """quit - Quit the program"""
        print("")
        return True
    do_EOF=do_quit
    do_exit=do_quit

    def do_readonly(self,argv):
        """ro/readonly - Switch the program to read only mode"""
        self.readonly = True
        self.open_hdf5()
    do_ro=do_readonly

    def do_readwrite(self,argv):
        """rw/readwrite - Switch the program to read-write mode"""
        self.readonly = False
        self.open_hdf5()
    do_rw=do_readwrite

    @require_readwrite
    def do_rm(self,argv):
        """rm - Remove a dataset or a group"""
        try:
            del self.cgrp[argv]
        except KeyError:
            print("Path \"%s\" does not exist." % argv)

    @require_readwrite
    def do_mkdir(self,argv):
        """mkdir - Create a new group"""
        try:
            self.cgrp.create_group(argv)
        except ValueError:
            print("Path \"%s\" already exist" % argv)

    def complete_cd(self,text,line,begidx,endidx):
        ks = self.cgrp.keys()
        ks.sort()
        return filter(lambda x: x.find(text) == 0,ks)
    complete_print=complete_cd
    complete_cat=complete_cd
    complete_p=complete_cd
    complete_dump=complete_cd
    complete_rm=complete_cd
    complete_mkdir=complete_cd

    def do_license(self,argv):
        """license - Print BSD license"""
        txt = """h5browser.py - A lightweight HDF5 browser

Copyright (c) 2019, Wong Hang <wonghang@gmail.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
        print(txt)

if __name__ == '__main__':
    try:
        path = sys.argv[1]
    except IndexError:
        sys.stderr.write("%s (hdf5 file path)\n" % sys.argv[0])
        sys.exit(1)
    else:
        h5browser(path).cmdloop()
