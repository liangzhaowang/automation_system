#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from uiautomator import Device
from atf import TestLogger
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
sys.path.append(CUR_DIR+'../../operation_lib')
from base_lib.exception_operation import kill_adb_uiautomator_block
from base_lib.exception_operation import kill_adb_uiautomator_block_old
from base_lib.UI_interface_operation import Swiping

dev = Device()
logger = TestLogger().get_logger("process")


class eventHunter:
    def __init__(self, device=dev, case_name="", repeat_swipes=2, cdstep=10, custep=10, crstep=10, clstep=10):
        self.case_name = case_name
        self.swiping_obj = Swiping(device)

    def center_down(self, repeat_swipes=5, cdtimes=5, cdtime_out=0.3, cdstep=10):
        try:
            for i in range(cdtimes):
                for j in range(repeat_swipes):
                    self.swiping_obj.up(num=cdstep)
                    time.sleep(cdtime_out)
                for k in range(repeat_swipes):
                    self.swiping_obj.down(num=cdstep)
                    time.sleep(cdtime_out)
        except Exception, e:
            logger.info("multiple down swipes failed %s" % e)
            return False

    def center_up(self, repeat_swipes=5, cutimes=5, cutime_out=0.3, custep=10):
        try:
            for i in range(cutimes):
                for k in range(repeat_swipes):
                    self.swiping_obj.down(num=custep)
                    time.sleep(cutime_out)
                for j in range(repeat_swipes):
                    self.swiping_obj.up(num=custep)
                    time.sleep(cutime_out)
        except Exception, e:
            logger.info("multiple up swipes failed %s" % e)
            return False

    def center_right(self, repeat_swipes=5, crtimes=5, crtime_out=0.3, crstep=10):
        try:
            for i in range(crtimes):
                for j in range(repeat_swipes):
                    kill_adb_uiautomator_block()
                    self.swiping_obj.right(num=crstep)
                    time.sleep(crtime_out)
                for k in range(repeat_swipes):
                    kill_adb_uiautomator_block()
                    self.swiping_obj.left(num=crstep)
                    time.sleep(crtime_out)
        except Exception, e:
            logger.info("multiple right swipes failed %s" % e)
            return False

    def center_left(self, repeat_swipes=5, cltimes=5, cltime_out=0.3, clstep=10):
        try:
            for i in range(cltimes):
                for j in range(repeat_swipes):
                    kill_adb_uiautomator_block()
                    self.swiping_obj.left(num=clstep)
                    time.sleep(cltime_out)
                for k in range(repeat_swipes):
                    kill_adb_uiautomator_block()
                    self.swiping_obj.right(num=clstep)
                    time.sleep(cltime_out)
        except Exception, e:
            logger.info("multiple left swipes failed %s" % e)
            return False

    def zoom_in(self, repeat_zoom=2, zooming_time_out=1):
        try:
            for i in range(repeat_zoom):
                kill_adb_uiautomator_block_old()
                self.swiping_obj.zoomout()
                time.sleep(zooming_time_out)
        except Exception, e:
            logger.error("multiple zoom_in failed %s" % e)
            return False

    def zoom_out(self, repeat_zoom=2, zooming_time_out=1):
        try:
            for i in range(repeat_zoom):
                kill_adb_uiautomator_block_old()
                self.swiping_obj.zoomin()
                time.sleep(zooming_time_out)
        except Exception, e:
            logger.error("multiple zoom_out failed %s" % e)
            return False

    def fourd_swipe(self, repeat_swipes=5, cdtimes=1, cutimes=1, cltimes=1, crtimes=1, cdtime_out=0.2, cutime_out=0.2, crtime_out=0.2, cltime_out=0.2, cdstep=10, custeo=10, clstep=10, crstep=10):
        try:
            self.center_down(repeat_swipes=repeat_swipes, cdtimes=cdtimes, cdtime_out=cdtime_out)
            self.center_up(repeat_swipes=repeat_swipes, cutimes=cutimes, cutime_out=cutime_out)
            self.center_right(repeat_swipes=repeat_swipes, crtimes=crtimes, crtime_out=crtime_out)
            self.center_left(repeat_swipes=repeat_swipes, cltimes=cltimes, cltime_out=cltime_out)
        except Exception, e:
            logger.info("one swipe failed %s" % e)
            return False

    def test_zooming(self, repeat_zoom=2, zooming_time_out=2):
        try:
            self.zoom_in(repeat_zoom=repeat_zoom, zooming_time_out=zooming_time_out)
            self.zoom_out(repeat_zoom=repeat_zoom, zooming_time_out=zooming_time_out)
        except Exception, e:
            logger.info("one zooming failed %s" % e)
            return False
