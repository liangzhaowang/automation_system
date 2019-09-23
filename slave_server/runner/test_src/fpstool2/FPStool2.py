#!/usr/bin/env python
#
# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Copyright (c) 2015 Evgeny Kalugin <evgeny.kalugin@intel.com>
# This code is deeply modified original Chromium tool. 
# BSD licence is still applied.
#


import collections
import optparse
import sys
import time
import fps_stats_parser

from pylib import android_commands

MAX_SCORE = 5

def PrintResult( result ):
    print ""
    print "Average fps rate (moving): ", round( result.average_fps_moving, 2 )
    print "Average fps rate (arithmetic): ", round( result.average_fps_arithmetic, 2 )
    print "Total frames drawn: ", result.total_frames
    print "Total frames lost", result.total_frames_lost
    print "Lost frames rate", 1.0 * result.total_frames_lost / ( result.total_frames + result.total_frames_lost )
    print "Maximum frames lost in a row: ", result.max_frames_lost_iar
    print "Maximum vsyncs missed ", result.max_vsync_missed
    print "Maximum frame processing time: ", result.max_frame_time


def main(argv):
    parser = optparse.OptionParser(usage='Usage: %prog [options] AppName ActivityName\nLegacy mode: %prog [options] LayerName',
                                   description=__doc__)
    parser.add_option('--device',
                      dest='device',
                      help='Serial number of device we should use.')
    parser.add_option('-d',
                      '--delay',
                      dest='delay',
                      default=1,
                      type='float',
                      help='Time in seconds to sleep between taking animation statistics.')
    parser.add_option("-c", "--continuous",
                      action="store_true", 
                      dest="continuous", 
                      default=False,
                      help='Turn on continuous mode')
    parser.add_option("-l", "--legacy",
                      action="store_true", 
                      dest="legacy", 
                      default=False,
                      help='Use legacy method of getting timestamps (dumpsys SurfaceFlinger)')
    parser.add_option("-a", "--automatic",
                      action="store_true",
                      dest='automatic',
                      default=False,
                      help='Automatic detection of currently rendered layer')
    parser.add_option("-D", "--debug",
                      dest='debug',
                      default=0,
                      type='int',
                      help='Debug level  0 - Only final score.  1 - Basic statistics.  2 - Detailed statistics')
    parser.add_option("-f", "--target_fps",
                      dest='target_fps',
                      type='float',
                      help='Target for minimum average frame rate')

    parser.add_option("-r", "--target_lostframes_rate",
                      dest='target_lostframes_rate',
                      type='float',
                      help='Target for maximum rate of lost frames')

    parser.add_option("-t", "--target_lostframes_total",
                      dest='target_lostframes_total',
                      type='int',
                      help='Target for maximum total amount of lost frames')

    parser.add_option("-i", "--target_lostframes_iar",
                      dest='target_lostframes_iar',
                      type='int',
                      help='Target for maximum amount of frames lost in a row')

    parser.add_option("-T", "--target_frame_time",
                      dest='target_frame_time',
                      type='float',
                      help='Target for maximum time of frame being processed')

    parser.add_option("-n", "--target_vsync_field",
                      dest='target_vsync_field',
                      type='int',
                      default=2,
                      help='The target column for vsync value')

    ( options, args ) = parser.parse_args(argv)

    if options.automatic :
        options.legacy = True
        app_name = ""
    else:
        # Application name and activity name are mandatory
        if not options.legacy and len(args) != 3:
            parser.error("incorrect number of arguments")

        # Application name is mandatory for legacy method
        if options.legacy and len(args) != 2:
            parser.error("incorrect number of arguments")

        app_name = args[ 1 ]

    if not options.legacy:
        activity_name = args[ 2 ]
    else:
        activity_name = ""

    adb = android_commands.AndroidCommands(options.device)
    if not adb.IsOnline() :
        print "No device attached"
        sys.exit(1)

    parser = fps_stats_parser.FpsStatsParser(adb, app_name, activity_name, options.debug > 1, options.legacy, options.target_vsync_field)

    if options.automatic :
        parser.Detect()

    parser.ClearStats()
    parser.UpdateRefreshPeriod()

    infinite = True
    warning_printed = False
    try:
        while infinite:
            score = MAX_SCORE
            time.sleep(options.delay)

            if not adb.IsOnline() :
                if not warning_printed :
                    print "Connection with the device lost, waiting to reconnect..."
                    warning_printed = True
                continue
            if warning_printed :
                parser.UpdateRefreshPeriod()
                warning_printed = False

            result = parser.GetStats()

            if result.total_frames: 
                if options.target_fps :
                    score -= 1 if result.average_fps_moving < options.target_fps or result.average_fps_arithmetic < options.target_fps else 0

                if options.target_lostframes_rate :
                    score -= 1 if 1.0 * (result.total_frames_lost / ( result.total_frames + result.total_frames_lost )) > options.target_lostframes_rate else 0

                if options.target_lostframes_total :
                    score -= 1 if result.total_frames_lost > options.target_lostframes_total else 0

                if options.target_lostframes_iar :
                    score -= 1 if result.max_frames_lost_iar > options.target_lostframes_iar else 0

                if options.target_frame_time :
                    score -= 1 if result.max_frame_time > options.target_frame_time else 0

                if options.debug:  PrintResult( result )
                print "Total score: ", score

            infinite = options.continuous

            if options.automatic :
                parser.Detect()
            sys.stdout.flush()

    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main(sys.argv)
