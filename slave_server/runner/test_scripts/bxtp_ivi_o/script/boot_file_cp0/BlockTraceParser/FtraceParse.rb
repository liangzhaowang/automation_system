class TraceData
  attr_reader:time
  attr_reader:pos
  attr_reader:size
  attr_reader:comm
  attr_reader:pid
  def initialize(comm, pid, time, pos, size)
    @comm = comm;
    @time = time
    @pos = pos
    @size = size
    @pid = pid
  end
end
class FtraceParse
  def initialize(filepath, traceex=false, filter_lanching = false, tgid_enable=true)
    @filepath = filepath
    @data =[]
    @launching_begin = 0
    @launching_end = 0
    @launch_name = ""
    @traceex = traceex
    @filter_lanching = filter_lanching
    @tgid_enable = tgid_enable
  end
  
  def launching_begin
    return @launching_begin
  end
  
  def launching_end
    return @launching_end
  end
  
  def beginParse()
    lines = IO.readlines(@filepath)
    if @tgid_enable
      #re_block = /^\s*(.+)-(\d+)\s+\(\s*(\d+|-+)\)\s\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_rq_insert):\s(.*)$/
      re_block = /^\s*(.+)-(\d+)\s+\(\s*(\d+|-+)\)\s\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_bio_queue):\s(.*)$/
      re_blockex = /^\s*(.+)-(\d+)\s+\(\s*(\d+|-+)\)\s\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_rq_leaveplug):\s(.*)$/
      re_launching = /^\s*(.+)-(\d+)\s+\(\s*(\d+|-+)\)\s\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+tracing_mark_write:\s(\w)\|(\d+)\|(launching):\s([\.\w]*)\|(\d+)$/
    else
     #re_block = /^\s*(.+)-(\d+)(\s+)\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_rq_insert):\s(.*)$/
      re_block = /^\s*(.+)-(\d+)(\s+)\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_bio_queue):\s(.*)$/
      re_blockex = /^\s*(.+)-(\d+)(\s+)\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+(block_rq_leaveplug):\s(.*)$/
      re_launching = /^\s*(.+)-(\d+)(\s+)\[(\d+)\]\s*[dX\.][N\.][Hhs\.][0-9a-f\.]\s+(\d+\.\d+):\s+tracing_mark_write:\s(\w)\|(\d+)\|(launching):\s([\.\w]*)\|(\d+)$/
    end
    lines.each do |line|
      if(@launching_begin == 0 || @launching_end == 0)
        match = re_launching.match(line)
        if(match!=nil && match.size > 0)
          if(match[6].eql?("S"))
            @launching_begin = match[5].to_f
          end
          if (match[6].eql?("F"))
            @launching_end = match[5].to_f
          end
          @launch_name = match[9]
          next
        end
      end
      
      if(!@traceex)
        match = re_blockex.match(line)
        if(match != nil)
          @traceex = true
        end
        if(!@traceex)
          match = re_block.match(line)
        end
      else
        match = re_blockex.match(line)
      end
      
      if(match != nil && match.size > 0)
        comm = match[1]
        time = match[5].to_f
        pid = match[2].to_i
        if(@filter_lanching)
          if(@launching_begin > 0 && time < @launching_begin)
            next
          end
          if(@launching_end > @launching_begin && time > @launching_end )
            next
          end
        end
        details = match[7]
       # re_detail = /\d+,\d\s(\w+)\s\d\s\(\)\s(\d+)\s\+\s(\d+)\.*/
         re_detail = /\d+,\d\s(\w+)\s(\d+)\s\+\s(\d+)\s\[(.*)\]/
        match = re_detail.match(details)
        if(match != nil && match.size > 0)
          if(match[1].eql?("R"))
            #puts "#{match[0]} @ #{time} @#{match[2]} - #{match[3]}"
            @data << TraceData.new(match[4], pid, time, match[2].to_i, match[3].to_i)
          end
        end
      end
    end
    if(@launching_begin != 0 && @launching_end != 0)
      puts "APP #{@launch_name} launching #{@launching_begin} ==> #{@launching_end}"
    end
    return @data
  end
  
end



#ftraceparse = FtraceParse.new(ARGV[0])
#ftraceparse.beginParse()