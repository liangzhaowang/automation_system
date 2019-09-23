class Device
  @@cpupath = "/sys/devices/system/cpu/cpu0/cpufreq"
  attr_reader:name
  attr_reader:abi
  attr_reader:curmaxfreq
  def initialize(device_name)
    @name = device_name
    @abi=""
    adbcmd("root")
    @curmaxfreq = 0
    getabi
  end
  
  def getabi
    f = self.shellcmd("getprop")
    re = /^\[ro.product.cpu.abi\]: \[(.+)\]$/
    until f.eof?
     s = f.gets.rstrip
     m = re.match(s)
     if (m != nil) && (m.size > 0)
        @abi = m[1]
        break
     end
   end
    return @abi
  end
  def adbcmd(cmd)
    adb_cmd = "adb -s " + @name + " " + cmd
    IO.popen(adb_cmd)
  end
  
  def shellcmd(cmd)
    adb_shell_cmd = "adb -s " + @name + " shell " + "'"  + cmd + "'"
   # puts adb_shell_cmd
    return IO.popen(adb_shell_cmd)
  end
  
  def to_s
     "#@name-#@abi"
  end
end


