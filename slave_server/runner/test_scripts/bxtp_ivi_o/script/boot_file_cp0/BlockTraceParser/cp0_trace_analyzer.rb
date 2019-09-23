require './inodeparse'

class InputBase 
  
  def getline
    return "fake input"
  end
  
  def update
    @inputs = getline
    
  end
  
  def inputs
    update
    return @inputs
  end  
end

class InputConsole < InputBase
  def getline
    return $stdin.gets
  end
end

class Analyzer
  def initialize(trace_file_path, inode_file)
    @trace_file_path = trace_file_path
    @inode_file = inode_file
    @data_parsed = false
    @input = InputConsole.new
    @traceex = false
    @filter_lanching = false
    @tgid_enable = false
  end
  
  def parseInode
    puts "Begin to parse inodes from file #{@inode_file}"
    @inodes_info = InodesInfo.new(@inode_file)
    @indoe_data = @inodes_info.begin_parse
  end
  
  def parseFtrace
    puts "Begin to parse trace logs from file #{@trace_file_path}"
    @ftrace_parser = FtraceParse.new(@trace_file_path, @traceex, @filter_lanching, @tgid_enable)
    @trace_data = @ftrace_parser.beginParse()
  end
  
  def doParse
    if(!@data_parsed)
      parseInode
      parseFtrace
      @data_parsed = true 
    end
  end
  
  def offsetToPageNo(offset, size)
    i = offset
    pageNoset = []
    while i < offset + size
      pageno = i / 4096
      i = i + 4096
      pageNoset << pageno 
    end
    return pageNoset
  end
  
  def offsetToPageHash(offsets)
    pagehash = Hash.new
    overlapPageNum = 0
    offsets.each do |offset|
      pages = offsetToPageNo(offset.start, offset.tail - offset.start)
      pages.each do |page|
        if(pagehash[page] == nil)
          pagehash[page] = page
        end
      end
    end
    return pagehash
  end
  
  def overLapDectect(offsets)
    pagehash = Hash.new
    overlapPageNum = 0
    offsets.each do |offset|
      pages = offsetToPageNo(offset.start, offset.tail - offset.start)
      pages.each do |page|
        if(pagehash[page] != nil)
        overlapPageNum = overlapPageNum + 1
       # puts "#{offset.time}:overlap at page No.#{page}, #{offset.start} - #{offset.tail},  #{overlapPageNum}"
        else
         pagehash[page] = page
        end
      end
    end
    return overlapPageNum
  end
  
  def recordAnlysis()
    doParse
    recfile = File.new("#{@trace_file_path}.csv", "w")
    recfile.puts("Time, Thread, PID, File, offset, Size")
    number = 0
    @trace_data.each do |data|
      comm = data.comm
      time = data.time
      pid = data.pid
      fileinfo = @indoe_data.getFile(data.pos)
      if(fileinfo == nil)
       # puts "Unknow file at pos #{data.pos}"
        next 
      end
      fileoffset = fileinfo.getOffset(data.pos)
      recfile.puts("#{time}, #{comm}, #{pid}, #{fileinfo}, #{fileoffset}, #{data.size * 512}")
      #puts("#{time}, #{comm}, #{pid}, #{fileinfo}, #{fileoffset}, #{data.size * 512}")
      number += 1
      #puts "#{time}: #{comm} read #{fileinfo} at #{fileoffset}, size: #{data.size * 512}"
      
      # if(fileinfo.to_s.eql?("/data/app/com.facebook.katana-1/oat/x86/base.odex"))
      #   offset_set << OffsetInfo.new(fileoffset, data.size * 512, time)
      # end
    end
    puts "Total #{number} records are writen to #{recfile.path}"
    recfile.close
  end
  
  def analyze_process
    doParse
    number = 0
    puts "============================================================================"
    puts "Please input the process id your want to analyze :"
    inputs = @input.inputs
    carepid =  inputs.rstrip.to_i
    total_size = 0
    process_files = Hash.new(0)
    process_data = []
    if(carepid != nil)
      @trace_data.each do |data|
        if(carepid != data.pid)
          next
        end
        fileinfo = @indoe_data.getFile(data.pos)
        if(fileinfo == nil)
          next 
        end
        process_files[fileinfo.to_s] += data.size * 512
        process_data << data
      end
    end
    recfile = File.new("#{@trace_file_path}_#{carepid}.csv", "w")
    recfile.puts("File, Size")
    total_size = 0
    tmparry = process_files.sort_by {|key,value| value}.reverse
    process_data = process_data.sort_by {|data|  process_files[@indoe_data.getFile(data.pos).to_s]}.reverse
    tmparry.each do |e|
      recfile.puts("#{e[0]}, #{e[1]}")
      number += 1
      total_size += e[1]
    end
    recfile.close
    if(number > 0)
      replayfile = File.new("#{@trace_file_path}_#{carepid}.replay", "w")
      puts "Total #{number} records are writen to #{recfile.path}, read #{total_size.to_f / 1024 / 1024} Mbytes"
      process_data.each do |data|
        fileinfo = @indoe_data.getFile(data.pos)
        fileoffset = fileinfo.getOffset(data.pos)
        replayfile.puts("#{fileinfo} #{fileoffset} #{data.size * 512}")
      end
      replayfile.close
    else
      puts "Can not Analyze the process #{carepid}, remove #{recfile.path}"
      File.unlink("#{@trace_file_path}_#{carepid}.csv")
    end
  end
  
  def analyze_file
    doParse
    number = 0
    puts "Please input the file name your want to analyze :"
    inputs = @input.inputs
    filerFile =  inputs.rstrip
    offset_set = []
    total_size = 0
    if(filerFile != nil && !filerFile.empty?)
      recfile = File.new("#{@trace_file_path}_#{File.basename(filerFile)}.csv", "w")
      recfile.puts("Time, Thread, PID, File, offset, Size")
      @trace_data.each do |data|
        comm = data.comm
        time = data.time
        pid = data.pid
        fileinfo = @indoe_data.getFile(data.pos)
        if(fileinfo == nil)
          #puts "Unknow file at pos #{data.pos}"
          next 
        end
        if(fileinfo.to_s.eql?(filerFile))
          fileoffset = fileinfo.getOffset(data.pos)
          recfile.puts("#{time}, #{comm}, #{pid}, #{fileinfo}, #{fileoffset}, #{data.size * 512}")
          #if pid == 2012
          offset_set << OffsetInfo.new(fileoffset, data.size * 512, time)
         # end
          total_size += data.size * 512
          number += 1
        end
      end
    end
    if(number > 0)
      puts "Total #{number} records are writen to #{recfile.path}, read #{total_size.to_f / 1024 / 1024} Mbytes"
      overlapNumber = overLapDectect(offset_set)
      puts "Total #{overlapNumber} pages are re-read"
      recfile.close
      pagehash = offsetToPageHash(offset_set)
      pageset = pagehash.sort_by{|k,v| k}
      maxpagenum = pageset[-1][0]
      recfile = File.new("#{@trace_file_path}_#{File.basename(filerFile)}_pageno.csv", "w")
      for no in 0..maxpagenum
        if(pagehash[no] != nil)
          recfile.puts("#{no}, 1")
        else
          recfile.puts("#{no}, 0")
        end
      end
      puts "Total #{pagehash.size} pages are read"
      recfile.close
    elsif
     puts "Can not Analyze the file #{filerFile}, remove #{recfile.path}"
      recfile.close
      File.unlink("#{@trace_file_path}_#{File.basename(filerFile)}.csv")
    end
    
  end
  
  def interactive_loop
    puts "============================================================================"
    puts "Is your ftrace contain 'Launching' event : Y/N (N default)"
    inputs = @input.inputs
    inputs =  inputs.rstrip
    if(inputs == "Y")
      @filter_lanching = true
    elsif (inputs == "N")
      @filter_lanching = false
    end
    
    puts "============================================================================"
    puts "Is your ftrace contain 'TGID': Y/N (N default)"
    inputs = @input.inputs
    inputs =  inputs.rstrip
    if(inputs == "Y")
      @tgid_enable = true
    elsif (inputs == "N")
      @tgid_enable = false
    end
    
    while true
      puts "============================================================================"
      puts "What do you want to do ?, (R)ecord Analysis, (A)nlyze single File, (P)rocess file reading (E)xit :"
      inputs = @input.inputs
      inputs =  inputs.rstrip
      if(inputs == "R")
        recordAnlysis
      elsif (inputs == "A")
        analyze_file
      elsif (inputs == "P")
        analyze_process
      elsif (inputs == "E")
        break
      elsif
        puts "Not known #{inputs}"
      end
    end
  end
end


###Main
if(ARGV[0] != nil && ARGV[1] != nil)
  analyzer = Analyzer.new(ARGV[0], ARGV[1])
  #analyzer.interactive_loop
  analyzer.recordAnlysis
elsif
  puts "ruby trace_analyzer (ftracefile.html), (inodes.txt)"
end
