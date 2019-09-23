import re

############################################
# Dictionnaries creation and transformations
############################################
def create_dict_files(filename):
    adict = {}
    regexp_inode = re.compile('^([^ ]+) (\d+):(\d+) (.+?) (\d+)([\d\s-]*)')
    with open(filename) as f:
        for line in f:
            if line[0] != '/':
                continue
            m = regexp_inode.search(line.strip())
            if not m:
                continue
            blockdev = m.group(1)
            major = m.group(2)
            minor = m.group(3)
            filename = m.group(4)
            inode = int(m.group(5))
            blocks_str = m.group(6)
            if not adict.has_key(blockdev):
                adict[blockdev] = []
            blocks = []
            for brange in blocks_str.split(','):
                if brange.find('-') == -1:
                    continue
                begin, end = brange.split('-')
                blocks.extend(range(int(begin), int(end)))
            adict[blockdev].append({ 'major': major, 'minor': minor, 'filename': filename, 'inode': int(inode), 'blocks': blocks})
    return adict

def dict_file_2_dict_inodes(dict_files):
    dict_inodes = {}
    for bdev in dict_files.keys():
        dict_inodes[bdev] = {}
        for afile in dict_files[bdev]:
            dict_inodes[bdev][afile['inode']] = afile['filename']
    return dict_inodes

def dict_file_2_dict_blocks(dict_files):
    dict_blocks = {}
    for bdev in dict_files.keys():
        dict_blocks[bdev] = {}
        for afile in dict_files[bdev]:
            for block in afile['blocks']:
                dict_blocks[bdev][block] = afile['inode']
    return dict_blocks

def dict_file_2_dict_dev(dict_files):
    dict_dev = {}
    for bdev in dict_files.keys():
        dict_dev[bdev] = {}
        for afile in dict_files[bdev]:
            dict_dev[bdev] = {'major': afile['major'], 'minor': afile['minor']}
    return dict_dev

def find_filename(dict_inodes, bdev, inode):
    filename = ""
    if dict_inodes.has_key(bdev):
            filename = dict_inodes[bdev].get(inode, "")
    return filename

    #print_pages(output['Others'], lambda x: 1 == 1)
