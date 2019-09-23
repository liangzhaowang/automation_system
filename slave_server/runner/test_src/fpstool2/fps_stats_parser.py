from enum import Enum
import os,sys

# Some constants
PROFILE_DATA_MARKER = "---PROFILEDATA---"
REFRESH_PERIOD = 0
NS_PER_SEC = 1e9
NS_PER_MS = 1e6

class ParserState( Enum ):
    APP_SEARCHING = 1
    ACTIVITY_SEARCHING = 2
    PROFILE_DATA_START_SEARCHING = 3
    COLLECTING_DATA = 4

class Result(object):
    def __init__(self):
        self.average_fps_arithmetic = 0.0
        self.average_fps_moving = 0.0
        self.total_frames_lost = 0
        self.max_frames_lost_iar = 0
        self.max_vsync_missed = 0
        self.max_frame_time = 0.0
        self.total_frames = 0
        self.frame_ready_timestamp = 0
        self.frame_desired_timestamp = 0
        self.frame_actual_timestamp = 0

class FpsStatsParser( object ):

    def __init__( self, adb, app_name, activity_name, debug, legacy, vsync_field ):
        self._adb = adb
        self._app_name = app_name
        self._activity_name = activity_name
        self._debug = debug
        self._legacy = legacy
        self._vsync_field = int(vsync_field)
        self.UpdateCommands()

    def UpdateCommands( self ):
        if self._legacy:
            self._command_get_data = 'dumpsys   SurfaceFlinger --latency "' + self._app_name + '"'
            self._command_clear_data = 'dumpsys SurfaceFlinger --latency-clear "' + self._app_name + '"'
        else:
            self._command_get_data = 'dumpsys gfxinfo "' + self._app_name + '" framestats'
            self._command_clear_data = 'dumpsys gfxinfo "' + self._app_name + '" reset'

    def Detect( self ):
        output = self._adb.RunShellCommand( 'dumpsys SurfaceFlinger' )
        layers = []

        max_frame_area = 0
        new_app_name = ""
        for line in output:
            # Looking for layers which are currenty redered by SurfaceFlinger
            if line.startswith( "       HWC |" ):
                items = line.split( '|' )
                coords = items[8].split( "," )
                x = int( coords[2] ) - int( coords[0] )
                y = int( coords[3] ) - int( coords[1] )

                frame_area = x * y
                app_name = items[9].strip()

                # SurfaceView layer is kind of exception. We always want to monitor it
                # because it is normally used by high-performance tasks
                if app_name.startswith( "SurfaceView" ):
                    new_app_name = app_name
                    break;

                # Looking for a layer which covers the biggest area of the screen
                if max_frame_area <= frame_area :
                    new_app_name = app_name
                    max_frame_area = frame_area


        if new_app_name != self._app_name :
            print "NEW APP NAME '", new_app_name, "'"
            self._app_name = new_app_name
            self.UpdateCommands()
        self.ClearStats()


    def ClearStats( self ):
        self._adb.RunShellCommand( self._command_clear_data )

    def UpdateRefreshPeriod( self ):
        global REFRESH_PERIOD
        output = self._adb.RunShellCommand( 'dumpsys SurfaceFlinger --latency' )
        REFRESH_PERIOD = long( output[0] )
        print 'Device diplay frequency ', round ( NS_PER_SEC / REFRESH_PERIOD, 1 ), 'Hz'

    def GetStats( self ):
        if self._legacy:
            return self.GetStatsLegacy()
        return self.GetStatsNew()
    
    def GetStatsNew( self ):
        if self._debug:
            print "---------------------------------"

        result = Result()
        output = self._adb.RunShellCommand( self._command_get_data )

        self.ClearStats()

        # State machine to parse sumpsys output
        state = ParserState.APP_SEARCHING
        data = []
        for line in output:
            if state == ParserState.APP_SEARCHING:
                if self._app_name in line:
                    state = ParserState.ACTIVITY_SEARCHING
            elif state == ParserState.ACTIVITY_SEARCHING:
                if self._activity_name in line:
                    state = ParserState.PROFILE_DATA_START_SEARCHING
            elif state == ParserState.PROFILE_DATA_START_SEARCHING:
                if line == PROFILE_DATA_MARKER:
                    state = ParserState.COLLECTING_DATA
            elif state == ParserState.COLLECTING_DATA:
                if line == PROFILE_DATA_MARKER:
                    break
                data.append( line )
            else:
                print "Internal error ", __file__
                sys.exit(1)
       
        data = data[1:]


        last_timestamp = 0
        last_vsync = 0

        first_frame = 0
        last_frame = 0

        for line in data:
            fields = line.split(',')

            # Avoiding tool crash if connection is lost
            if len( fields ) < 14 :
                break

            # We only accept fields with FLAGS equal to 0 and 1
            if long(fields[0]) > 1:
                continue
            result.total_frames += 1

            # vsync timestamp will be used for fps computing
            vsync = float( fields[self._vsync_field] )
            intended_vsync = float( fields[1] )
            frame_completed = float( fields[13] )

            # warning appendix to easier identification of problematic frame
            warning = ""

            # Amount of lost VSYNCs is measured in special "refresh period" units
            vsync_missed = (int)( round( vsync - intended_vsync ) / REFRESH_PERIOD )
            if vsync_missed :
                result.max_vsync_missed = max( result.max_vsync_missed, vsync_missed )
                warning += "   *****"

            # Total frame lifetime from application side to display
            result.max_frame_time = max( result.max_frame_time, ( frame_completed - intended_vsync ) / NS_PER_MS )

            # frame rate can only be calculated if we have at least two frames
            if result.total_frames > 1:
                # Amount of lost frames is measured in special "refresh period" units
                frames_lost = (int)( round(  (vsync - last_vsync) / REFRESH_PERIOD - 1 ) )

                # Sometimes HW_VSYNC can shift SW_VSYNC so much back, that two neighbour VSYNCs happen almost at the same time
                frames_lost = max( frames_lost, 0 )


                # If no gap between VSYNC's then the instant frame rate is exactly 60fps
                instant_fps = NS_PER_SEC / ( ( frames_lost + 1 ) * REFRESH_PERIOD )
                result.average_fps_moving += ( instant_fps - result.average_fps_moving ) / ( result.total_frames - 1 )

                if frames_lost :
                    result.max_frames_lost_iar = max( result.max_frames_lost_iar, frames_lost )
                    result.total_frames_lost += frames_lost
                    warning += "   #####"
                if self._debug:
                    print "FRAME_COMPLETED(ns): ", (long)( frame_completed ) , "frame length(ms) = ", round( ( frame_completed - intended_vsync ) / NS_PER_MS, 2  ), "  intended/actual VSYNC gap = ", vsync_missed, "  instant_fps = ", round( instant_fps, 2 ), " current/previous VSYNC gap = ", frames_lost + 1, "(", ( vsync - last_vsync ) / NS_PER_MS, "ms)", warning
                last_frame = vsync
            else:
                first_frame = vsync


            last_vsync = vsync

        if result.total_frames > 1:
                result.average_fps_arithmetic = ( NS_PER_SEC / REFRESH_PERIOD ) * ( result.total_frames - 1 ) / ( result.total_frames + result.total_frames_lost - 1 )

        return result


    def GetStatsLegacy( self ):
        if self._debug:
            print "---------------------------------"
        
        result = Result()
        data = self._adb.RunShellCommand( self._command_get_data )

        self.ClearStats()

        if len(data) < 2 :
            return result

        data = data[1:-1]
        data = sorted( data, key=lambda key_frame: ( key_frame.split() )[0] )


        last_timestamp = 0
        last_vsync = 0

        first_frame = 0
        last_frame = 0
        
        desired = 0
        last_desired = 0
        
        actual = 0
        last_actual = 0

        pending_fence_timestamp = (1 << 63) - 1

        for line in data:
            fields = line.split()

            # Avoiding tool crash if connection is lost
            if len( fields ) < 3 :
                break

            # Ignore the fields with zero or MAX timestamps 
            if not long(fields[0]) or long( fields[1] ) == pending_fence_timestamp :
                continue
            
            desired = float( fields[0] )
            actual = float( fields[1] )
            # vsync timestamp will be used for fps computing
            vsync = float( fields[self._vsync_field] )

            result.total_frames += 1

            frame_started = float( fields[0] )
            frame_finished = float( fields[self._vsync_field] )

            # warning appendix to easier identification of problematic frame
            warning = ""


            # Total frame lifetime from application side to display
            result.max_frame_time = max( result.max_frame_time, ( frame_finished - frame_started ) / NS_PER_MS )

            # frame rate can only be calculated if we have at least two frames
            if result.total_frames > 1:
                # Amount of lost frames is measured in special "refresh period" units
                frames_lost = (int)( round(  (vsync - last_vsync) / REFRESH_PERIOD - 1 ) )

                # Sometimes HW_VSYNC can shift SW_VSYNC so much back, that two neighbour VSYNCs happen almost at the same time
                frames_lost = max( frames_lost, 0 )
                
                result.frame_actual_timestamp = (actual - last_actual)
                result.frame_desired_timestamp = (desired -last_desired)
                result.frame_ready_timestamp =  (vsync - last_vsync)
                print "frame timestamps:%d,%d,%d,%d,%d,%d"%(desired,result.frame_desired_timestamp,actual,result.frame_actual_timestamp,vsync,result.frame_ready_timestamp)

                # If no gap between VSYNC's then the instant frame rate is exactly 60fps
                instant_fps = NS_PER_SEC / ( ( frames_lost + 1 ) * REFRESH_PERIOD )
                result.average_fps_moving += ( instant_fps - result.average_fps_moving ) / ( result.total_frames - 1 )

                if frames_lost :
                    result.max_frames_lost_iar = max( result.max_frames_lost_iar, frames_lost )
                    result.total_frames_lost += frames_lost
                    warning += "   #####"
                if self._debug:
                    print "FRAME_COMPLETED(ns): ", (long)( frame_finished ) , "  instant_fps = ", round( instant_fps, 2 ), " current/previous VSYNC gap = ", frames_lost + 1, "(", ( vsync - last_vsync ) / NS_PER_MS, "ms)", warning
                last_frame = vsync
            else:
                first_frame = vsync


            last_vsync = vsync
            last_desired = desired
            last_actual = actual
        if result.total_frames > 1:
                result.average_fps_arithmetic = ( NS_PER_SEC / REFRESH_PERIOD ) * ( result.total_frames - 1 ) / ( result.total_frames + result.total_frames_lost - 1 )

        return result

