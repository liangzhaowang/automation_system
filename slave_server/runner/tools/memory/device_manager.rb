
class DeviceManager
  def initialize
    @devices = []
  end
  
def findDevice
    puts "finding device..."
  f = IO.popen("adb devices")
  re = /^([\d\w]+)\s+device$/
  until f.eof?
    s = f.gets
    m = re.match(s)
    if (m != nil) && (m.size > 0)
      device = Device.new(m[1])
      puts "device:" + m[1] + " is found"
      @devices.push(device)
    end
  end
  f.close
  if @devices.size == 0
    puts "nothing is found..."
  end
  return @devices
  end
  
end
