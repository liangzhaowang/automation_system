require File.expand_path('./device.rb', 'runner/tools/memory')
require File.expand_path('./device_manager.rb', 'runner/tools/memory')
require File.expand_path('./FPSTracer', 'runner/tools/memory')
require File.expand_path('./PMemTracer', 'runner/tools/memory')

def findprocess(device, name, timeout=30)
  while timeout > 0 do
    io = device.shellcmd("ps -e")
    lines = io.readlines
    io.close
    lines.each do |line|
      fields = line.split()
      if(fields[8] == name)
        return fields[1].to_i
      end
    end
    sleep(1)
    timeout -= 1
  end
  return 0
end

def DumpKmesg(device, silent=true, file = nil)
  io = device.shellcmd("dmesg -c")
  until io.eof? do
    s = io.gets
    if(!silent)  
      puts s
    end
    if(file != nil)
            file.puts s
    end
  end
  io.close
end

  def DumpLogcatmessage(device, silent=true, file = nil)
    io = device.adbcmd("logcat -d")
    until io.eof? do
      s = io.gets
      if(!silent)
        puts s
      end
      if(file != nil)
        file.puts s
      end
    end
    io.close
    io = device.adbcmd("logcat -c")
    io.readlines
    io.close
  end

device_manger = DeviceManager.new
devices = device_manger.findDevice
if devices.size <= 0
  puts "no devices"
  return
end

android_device  = nil;

if( ARGV[2] != nil )
  devices.each do |device|
    if device.name == ARGV[1]
      android_device = device
    end
  end
else
  android_device = devices[0]
end
android_device.adbcmd("root")
sleep(5)

puts "Begin recording . . ."

pid = 0
if(ARGV[0] != nil)
  pid = findprocess(android_device, ARGV[0])
  puts(">>>>>>>>>>>>>>>>app pid: #{pid}")
end

dirname = nil
if(ARGV[1] != nil)
  dirname = ARGV[1]
end 

fps_tracer = FPSTracer.new(android_device)
pmem_tracer = PMemTracer.new(android_device)

x = []
plotdata = Hash.new([])
plotdata["Fps"] = []
plotdata["AvFps"] = []
plotdata["Pss-All of App"] = []
plotdata["Pss-Anon of App"] = []
plotdata["Pss-SHM of App"] = []
plotdata["Pss-Drm of App"] = []
plotdata["PriGFX of App"] = []
plotdata["Total of App"] = []
plotdata["Cache of System"] = []
plotdata["Shmem of System"] = []
plotdata["Swapd of System"] = []
plotdata["Free of System"] = []
plotdata["Cache-SHMEM"] = []
plotdataEnable = {"Fps" => true, "AvFps"=>false,"Pss-All of App"=>true, "Pss-Anon of App"=>false,
  "Pss-SHM of App"=>false,"Pss-Drm of App"=>false, "Total of App"=>false, 
  "Cache of System"=>true, "Swapd of System"=>false, "Shmem of System"=>true,"Free of System"=>true,
  "Cache-SHMEM"=>true, "PriGFX of App"=>true}
time = 0
 
date = Time.new
if (dirname == nil)
  dirname =  "#{android_device}_" + date.strftime("%m_%d_%H_%M_%S")
  Dir.mkdir(dirname)
end

logfile = File.new("#{dirname}/memlog.csv", "w")
kmsgfile = File.new("#{dirname}/kmsg.txt", "w")
logcatfile = File.new("#{dirname}/logcat.txt", "w")
logfile.puts("Time, FPS, AvFPS, Total of App, PriGFX of App, Pss-All of App,  Pss-Anon of App, Pss-Drm of App, Pss-SHM of App,  Free of System, Cache of System, Swapd of System, Shmem of System")

XTIMERANGE = 700
while time < 100000 do
  fps = fps_tracer.GetFPS("SurfaceView")
  pss, anon,drm, share,rss = pmem_tracer.GetPss(pid)
  if(pss.is_a?(FalseClass))
    pss = 0
    anon = 0
    drm = 0
    rss = 0
    share = 0
    if(ARGV[0] != nil)
      pid = findprocess(android_device, ARGV[0], 1)
    end
  else
    pss = pss.to_f / 1024.0
    anon = anon.to_f / 1024.0
    drm = drm.to_f / 1024.0
    share = share.to_f / 1024.0
  end

  # DumpKmesg(android_device, true)

  meminfo = pmem_tracer.GetMemInfoExt
  freemem =  meminfo["MemFree"].to_f / 1024.0
  cache =    meminfo ["Cached"].to_f / 1024.0
  swapd = meminfo ["SwapTotal"].to_f / 1024.0
  shmem = meminfo ["Shmem"].to_f / 1024.0
    
  gfxmeminfo = pmem_tracer.GetGFXMem(pid)
  if(gfxmeminfo == nil)
    gfx = 0
  else
    gfx = gfxmeminfo["PrivPHYsize"].to_f / 1024.0
  end
  if x.size >= XTIMERANGE
    x.delete_at(0)
    plotdata.each  do |key, value|
      value.delete_at(0)
    end
  end
  x << time
  
  plotdata["Fps"] << fps
  plotdata["Pss-All of App"] << pss
  plotdata["Pss-Anon of App"] << anon
  plotdata["Pss-SHM of App"] << share
  plotdata["Pss-Drm of App"]  << drm
  plotdata["PriGFX of App"] << gfx 
  plotdata["Total of App"]   << rss
  plotdata["Cache of System"]  << cache
  plotdata["Shmem of System"] << shmem
  plotdata["Swapd of System"]  << swapd
  plotdata["Free of System"] << freemem
  plotdata["Cache-SHMEM"] << cache - shmem

  fpshist = plotdata["Fps"]
  if(fpshist.size >= 5)
    avfps = (0.2*fpshist[-1] + 0.2*fpshist[-2] + 0.2*fpshist[-3] + 0.2*fpshist[-4] + 0.2*fpshist[-5])
  else
    avfps = fpshist[-1]
  end
  plotdata["AvFps"] << avfps
  
  logfile.puts("#{time}, #{fps}, #{avfps}, #{rss}, #{gfx}, #{pss},  #{anon}, #{drm}, #{share}, #{freemem}, #{cache}, #{swapd}, #{shmem}")

  if fpshist.size >= 3
    if(fpshist[-1] < 10  && (fpshist[-1]- plotdata["AvFps"][-3]).abs >= 2)
      puts "FPS (#{fpshist[-1]}) Drop at #{time}"
      logcatfile.puts("=================== FPS Drop (#{fpshist[-1]}) at #{time} ==================")
      kmsgfile.puts("=================== FPS Drop  (#{fpshist[-1]}) at #{time} ==================")
      DumpKmesg(android_device, false, kmsgfile)
      DumpLogcatmessage(android_device, true, logcatfile);
    end
  end

  apppsshist = plotdata["Pss-All of App"]

  if(apppsshist.size >= 2 && apppsshist[-2] > 0 && ((apppsshist[-2] - apppsshist[-1]) / apppsshist[-2]) > 0.9)
    puts "Mem release to (#{apppsshist[-1]}) release at #{time}"
    logcatfile.puts("=================== Mem release to (#{apppsshist[-1]}) release at #{time} ==================")
    kmsgfile.puts("=================== Mem release to (#{apppsshist[-1]}) release at #{time}==================")
    DumpKmesg(android_device, false, kmsgfile)
    DumpLogcatmessage(android_device, true, logcatfile);
  end
  
  sleep(1)
  time += 1
end

logfile.close
kmsgfile.close
logcatfile.close

