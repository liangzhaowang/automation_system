#!/usr/bin/env python
# coding=utf-8
from lib.adb_gfx_gl_lib import gfx
from atf import *
import os
# sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib'))
apk_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'gfxbench_gl-4.0.13-candidate+corporate.x86.apk')
# __init__(self,app_name,app_path,tr_name) 
if __name__ == "__main__":
	tr = TestResult(__file__)
	gfx_Man_on = gfx("glbenchmark",apk_path,'Gfx_manhattan_4013_onscreen')
	tr.result(gfx_Man_on.result)
	tr.save()
