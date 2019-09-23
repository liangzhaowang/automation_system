require File.expand_path('./device', 'runner/tools/memory')

class FPSTracer
  NS_PER_SEC = 1e9
  NS_PER_MS = 1e6
  REFRESH_PERIOD = 16666666
  def initialize(device)
    @device = device
  end

  def GetFPS(layname = "")
    io = @device.shellcmd("dumpsys SurfaceFlinger --latency #{layname}")
    lines = io.readlines
    io.close
    fps = parseResults(lines)
    io = @device.shellcmd("dumpsys SurfaceFlinger --latency-clear")
    io.readlines
    io.close
    return fps
  end

  def parseResults(lines)
    if(lines.size < 2)
      return 0
    end

    pending_fence_timestamp = (1 << 63) - 1
    average_fps_arithmetic = 0
    total_frames = 0
    max_frame_time = 0
    average_fps_moving = 0
    max_frames_lost_iar = 0
    total_frames_lost = 0
    
    last_timestamp = 0
    last_vsync = 0

    first_frame = 0
    last_frame = 0

    data = lines[1..-1]
    data = data.sort_by{ |x| (x.split('\t'))[0] }

    data[1..-1].each do |frame|
      fields = frame.split()
      if (fields.size < 3)
        break
      end
      if (fields[0].to_i == 0 || fields[1].to_i == pending_fence_timestamp )
        next
      end
      vsync = fields[2].to_f
      total_frames += 1
      frame_started = float( fields[0] )
      frame_finished = float( fields[2] )
      max_frame_time = [max_frame_time, (frame_finished - frame_started)/NS_PER_MS].max

      if total_frames > 1
        # Amount of lost frames is measured in special "refresh period" units
        frames_lost = ( (  (vsync - last_vsync) / REFRESH_PERIOD - 1 ) ).round.to_i

        # Sometimes HW_VSYNC can shift SW_VSYNC so much back, that two neighbour VSYNCs happen almost at the same time
        frames_lost =  [frames_lost, 0 ].max

        # If no gap between VSYNC's then the instant frame rate is exactly 60fps
        instant_fps = NS_PER_SEC / ( ( frames_lost + 1 ) * REFRESH_PERIOD )
        average_fps_moving += ( instant_fps - average_fps_moving ) / ( total_frames - 1 )

        if frames_lost
          max_frames_lost_iar = [max_frames_lost_iar, frames_lost ].max
          total_frames_lost += frames_lost
        end

      end
      last_vsync = vsync
    end
    if total_frames > 1
       average_fps_arithmetic = ( NS_PER_SEC / REFRESH_PERIOD ) * ( total_frames - 1 ) / ( total_frames + total_frames_lost - 1 )
    end
    return average_fps_arithmetic
  end

  def float(obj)
    return obj.to_f
  end
  private :parseResults
  private :float
end
