require 'scanf'
require File.expand_path('./device', 'runner/tools/memory')

class PMemTracer
  def initialize(device)
    @device = device
    # @file_meminfo = File.new("#{@device}_meminfo.txt", "w")
    # @file_pmapinfo = File.new("#{@device}_pmapinfo.txt", "w")
  end

  def GetPss(pid)
    io = @device.shellcmd("pmap -x #{pid}")
    lines = io.readlines
    io.close
    return parseResults(lines)
  end
  
  def GetGFXMem(pid)
    gfxmeminfo = Hash.new(0)
    io = @device.shellcmd("cat /sys/class/drm/card0/gfx_memtrack/i915_gem_meminfo")
    lines = io.readlines
    io.close
    if(lines.size < 3)
      return nil
    end
    titles = lines[2].split()
    lines = lines[3..-1]
    lines.each do |line|
      fields = line.split()
      if(fields[0].to_i == pid)
        for i in 0..titles.size
          gfxmeminfo[titles[i]] = fields[i].to_i
        end
        return gfxmeminfo
      end
    end
    return nil
  end

  def GetMemInfoExt
    io = @device.shellcmd("cat /proc/meminfo")
    lines = io.readlines
    io.close
    meminfo = Hash.new(0)
    lines.each do |line|
      rex = /(\w+):\s+(\d+)\s+kB/
      fields = rex.match(line)
      if(fields != nil)
        meminfo[fields[1]] = fields[2].to_i
      end
    end
    return meminfo
  end

  def GetMemInfo
    io = @device.shellcmd("vmstat")
    lines = io.readlines
    io.close
    line = lines[-1]
    fields = line.split()
    meminfo = Hash.new(0)
    meminfo["free"] = fields[3].to_i
    meminfo["cache"] = fields[5].to_i
    meminfo["swapd"] = fields[2].to_i
    return meminfo
  end

  def parseResults(lines)
    totalline = lines[-1]
    if totalline == nil
      return false
    end
    fields = totalline.split()

    if(fields[0] == "total")
      total_mem = fields[1].to_i
      pss_mem = fields[2].to_i
      dirty_mem = fields[3].to_i
      swap_mem = fields[4].to_i
      anon_mem = 0
      drm_mem = 0
      share_mem = 0
      lines[2..-3].each  do |line|
        fields = line.scanf("%s %s %s %s %s %s %s")
        if (line.index("deleted") != nil)
            share_mem += fields[2].to_i
        end
        if(fields[6].index("[anon") == 0)
          anon_mem += fields[2].to_i
        elsif(fields[6].index("drm") == 0)
            drm_mem += fields[2].to_i
        end
      end
      return pss_mem, anon_mem,drm_mem, share_mem, total_mem
    else
      return false
    end
  end

end