require './FtraceParse'

class Sectorinfo
  def initialize(min, max)
    @min = min
    @max = max
    @sector_number = max - min + 1
  end
  def min
    return @min
  end
  def max
    return @max
  end
  def sector_number
    return @sector_number
  end
  def in_sector?(index)
    return index >= @min && index <= @max
  end
end



class FileInfo
  def initialize(filename, block, sectortxt)
    @filename = filename
    @sectors = []
    @block = block
    parse_sectors(sectortxt)
    
  end
  def parse_sectors(sectortxt)
    sectors = sectortxt.split(",")
    sectors.each do |secotr|
      info = secotr.split("-")
      min = info[0].to_i
      max = info[1].to_i
      sectorInfo = Sectorinfo.new(min,max)
      @sectors << sectorInfo
    end
  end
  
  def sectors
    sectornums = []
    @sectors.each do |sector|
      for i in sector.min..sector.max
        sectornums << i
      end
    end
    #puts "create a file #{@filename} in block #{@block}, #{sectornums}"
    return sectornums
  end
  
  def getOffset(pos)
    offset = 0
    sectorindex = @block.getSectorIndx(pos)
    @sectors.each do |sector|
      if(sector.in_sector?(sectorindex))
        offset += (sectorindex - sector.min) * @block.blocksize
        break
      else
        offset +=  sector.sector_number *  @block.blocksize
      end
    end
    return offset
  end
  
  def block
    return @block
  end
  
  def to_s
    return "#{@filename}"
  end
end


class BlockInfo
  attr_reader:blockname
  attr_reader:size
  attr_reader:sectorsize
  attr_reader:blocksize
  attr_reader:fileSectortable
  def initialize(blockname, startpos, size, bsize, ssize)
    @blockname = blockname
    @start  = startpos
    @blocksize = bsize
    @sectorsize = ssize
    @size = size
    @fileSectortable = Hash.new
    puts "create block info #{@blockname}, start @#{@start}: #{@blocksize}, #{@sectorsize}"
  end
  def to_s
    return @blockname
  end
  
  def in_block?(pos)
    if(pos >= @start && pos < @start+@size)
      return true
    else
      return false
    end
  end
  
  def getSectorIndx(pos)
    return (pos - @start) / (@blocksize / @sectorsize)
  end
  
  def insertFileSector(sectorIndex, fileinfo)
    if(@fileSectortable[sectorIndex] != nil)
      oldfile = @fileSectortable[sectorIndex]
      puts "#{@blockname}-sectorn : #{sectorIndex} of #{oldfile} is confilict with #{fileinfo}"
      return 
    end
    @fileSectortable[sectorIndex] = fileinfo
  end
  
end

class Inodesdata
  def initialize(blocktable, filetable)
    @blkTab = blocktable
    @fileTab = filetable
  end
  
  def getFile(pos)
    @blkTab.each_value do |block|
      if(block.in_block?(pos))
        sectorindex = block.getSectorIndx(pos)
        file = block.fileSectortable[sectorindex]
        if(file == nil)
          #puts "find pos #{pos} in  block #{block} maybe wrong at sector #{sectorindex}"
          next 
        end
        if(file.block != block)
         # puts "find file #{file} in  block #{block} maybe wrong"
          next
        end
        return block.fileSectortable[sectorindex]
      end
    end
    return nil
  end
end

class InodesInfo
  def initialize(filepath)
    @filepath = filepath
    @blocktable = Hash.new
    @filetable = Hash.new
   # @fileSectortable = Hash.new
  end
  def begin_parse
    f = File.new(@filepath, "r")
    re_inodes = /(\/dev\/block\/mmcblk\d+p\d+) ([^ ]*):([^ ]*) \"(.*)\" (\d+) (\d+\-\d+.*)$/
    re_partion = /(\/dev\/block\/mmcblk\d+p\d+) ([^ ]*) ([^ ]*):([^ ]*) start=(\d+) size=(\d+) bsize=(\d+) ssize=(\d+)/
    lines = f.readlines
    lines.each do |line|
      match = re_partion.match(line)
      if(match != nil && match.size > 0)
        puts "find a partion"
        blkname = match[1]
        start = match[5].to_i
        blksize = match[7].to_i
        sszie = match[8].to_i
        size = match[6].to_i
        blockinfo = BlockInfo.new(blkname, start, size, blksize, sszie)
        @blocktable[blkname] = blockinfo
        next
      end
      
      match = re_inodes.match(line)
      
      if(match != nil && match.size > 0)
        # puts "find #{match[4]}, sectortxt#{match[6]}"
        filename = match[4]
        sectortxt = match[6]
        blockname = match[1]
        
        block = @blocktable[blockname]
        fileinfo = FileInfo.new(filename, @blocktable[blockname], sectortxt)
        fileSectorNumbers = fileinfo.sectors
        fileSectorNumbers.each do |sectorN|
          
        #  @fileSectortable[sectorN] = fileinfo
          block.insertFileSector(sectorN, fileinfo)
        end
        @filetable["#{blockname}\#{filename}"] = fileinfo
      end
    end
    return Inodesdata.new(@blocktable, @filetable)
  end
end


class OffsetInfo
  def initialize(start, size, time = 0)
    @start = start
    @tail = start+size
    @time = time
  end
  
  def start
    return @start
  end
  
  def tail
    return @tail
  end
  
  def time
    return @time
  end
end




=begin
##Main()
if(ARGV[1]==nil)
inode_file = "inodes.txt"
else
inode_file = ARGV[1]
end

info = InodesInfo.new(ARGV[1])
indoe_data = info.begin_parse

ftraceparse = FtraceParse.new(ARGV[0])
tracedata = ftraceparse.beginParse(true)
logfile = File.new("#{ARGV[0]}.csv", "w")
logfile1 = File.new("#{ARGV[0]}1.csv", "w")
offset_set = []

logfile.puts("Time, Thread, File, offset, Size")
tracedata.each do |data|
  comm = data.comm
  time = data.time
  fileinfo = indoe_data.getFile(data.pos)
  if(fileinfo == nil)
   # puts "Unknow file at pos #{data.pos}"
    next 
  end
  fileoffset = fileinfo.getOffset(data.pos)
  logfile.puts("#{time}, #{comm}, #{fileinfo}, #{fileoffset}, #{data.size * 512}")
  #puts "#{time}: #{comm} read #{fileinfo} at #{fileoffset}, size: #{data.size * 512}"
  if(fileinfo.to_s.eql?("/data/app/com.facebook.katana-1/oat/x86/base.odex"))
    offset_set << OffsetInfo.new(fileoffset, data.size * 512, time)
  end
end
logfile.close

pageOverLap = overLapDectect(offset_set)
puts "Total #{pageOverLap} pages were re-read!"

#offset_set.sort!{|a,b| a.start <=> b.start}
offset_set.each do |offset|
  if(ftraceparse.launching_begin !=0 && ftraceparse.launching_end !=0)
    if(offset.time > ftraceparse.launching_begin && offset.time < ftraceparse.launching_end)
      logfile1.puts "#{offset.time - ftraceparse.launching_begin},#{offset.start},#{offset.tail - offset.start}"
    end
  else
  logfile1.puts "#{offset.time},#{offset.start},#{offset.tail - offset.start}"
  end
end
logfile1.close




info = InodesInfo.new("inodes.txt")
data = info.begin_parse
logfile = File.new("offsectpre.log", "w")
lines = IO.readlines("posvecpre.txt")
lines.each do |line|
  pos = line.to_i
  fileinfo = data.getFile(pos)
  fileoffset = fileinfo.getOffset(pos)
  puts "#{fileinfo} at #{fileoffset}"
  logfile.puts "#{fileoffset}"
end
logfile.close


info = InodesInfo.new("inodes.txt")
indoe_data = info.begin_parse
fileinfo = indoe_data.getFile(ARGV[0].to_i)
fileoffset = fileinfo.getOffset(ARGV[0].to_i)
puts "#{fileinfo} at #{fileoffset}"
=end
