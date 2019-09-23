import json
import os
#parent_list = ['OAM-38692', 'OAM-41343', 'OAM-41222', 'OAM-41009', 'OAM-41345']
#child_list = ['OAM-49041', 'OAM-49043', 'OAM-49037', 'OAM-42027', 'OAM-41146', 'OAM-40542', 'OAM-41866', 'OAM-40899', 'OAM-42823', 'OAM-41560', 'OAM-40762', 'OAM-42962', 'OAM-40832', 'OAM-42821', 'OAM-40974', 'OAM-40774', 'OAM-40742', 'OAM-40834', 'OAM-40776', 'OAM-40741', 'OAM-41477', 'OAM-39769', 'OAM-42441', 'OAM-42043', 'OAM-40761', 'OAM-41790', 'OAM-43809', 'OAM-40753', 'OAM-40737', 'OAM-41815', 'OAM-40110', 'OAM-41576', 'OAM-40284', 'OAM-43600', 'OAM-43758', 'OAM-41458', 'OAM-42030', 'OAM-43708']
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
link_base = "https://jira.devtools.intel.com/browse/"
def _byteify(data, ignore_dicts = False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data

def get_parent_data(js_path):
	new_list = []
	pdata = json.loads(open(js_path).read(),object_hook=_byteify)
	data_key = pdata.keys()
	data_list = []

	for item in data_key[0:]:#parent_list[0:]:
		if not item in data_list and len(pdata[item]['parent']) == 0:
			# print item
			tmplist = []
			tmplist.append('\tvar '+item.replace("-","_")+"={\n")
			tmplist.append("\t\tparent: Jira_root ,\n")
			if isinstance(pdata[item]["text"], dict):
				tmplist.append("\t\tHTMLclass:\"" + pdata[item]["text"]["colorName"] + "\",\n")
			else:
				tmplist.append("\t\tHTMLclass:\"" + pdata[item]["text"][-1] + "\",\n")
			tmplist.append("\t\ttext :{\n")
			tmplist.append("\t\t\tname: \""+item+"\",\n")
			if isinstance(pdata[item]["text"], dict):
				tmplist.append("\t\t\tcontact: \"assignee: " + pdata[item]["text"]["assignee"] + "\",\n")
				tmplist.append("\t\t\ttitle: \"status: " + pdata[item]["text"]['status'] + "\",\n")
				tmplist.append("\t\t\tdata_priority: \"priority: " + pdata[item]["text"]['priority'] + "\",\n")
				tmplist.append("\t\t\tdata_created: \"created: " + pdata[item]["text"]["created"] + "\",\n")
				tmplist.append("\t\t\tdata_updated: \"updated: " + pdata[item]["text"]["updated"] + "\",\n")
				tmplist.append("\t\t\tdesc: \"summary: " + pdata[item]["text"]["summary"].replace("\"", "\'") + "\",\n")
			else:
				tmplist.append("\t\t\ttitle: \"status: " + pdata[item]["text"][-2] + "\",\n")
				tmplist.append("\t\t\tdesc: \"summary: " + pdata[item]["text"][1].replace("\"", "\'") + "\",\n")
			tmplist.append("\t\t},\n")
			tmplist.append("\t\tlink: {\n")
			tmplist.append("\t\t\thref: \"https://jira.devtools.intel.com/browse/"+item+"\",\n")
			tmplist.append("\t\t\ttarget: \"_blank\"\n")
			tmplist.append("\t\t},\n")
			tmplist.append("\t};\n")
			new_list.extend(tmplist)
			data_list.append(item.replace("-","_"))
			data_key.remove(item)
	# print data_key
	while len(data_key)>0:
		# print 'ppppppppppppppppppp'
		# print len(data_key)
		for item in data_key[0:]:#parent_list[0:]:
			# print not item in data_list
			# print pdata[item]["parent"]
			# print pdata[item]["parent"] in data_list
			if not item in data_list and pdata[item]["parent"].replace("-","_") in data_list:
				tmplist = []
				tmplist.append('\tvar '+item.replace("-","_")+"={\n")
				tmplist.append("\t\tparent: " + pdata[item]["parent"].replace("-", "_") + ",\n")
				if isinstance(pdata[item]["text"], dict):
					tmplist.append("\t\tHTMLclass:\""+pdata[item]["text"]["colorName"]+"\",\n")
				else:
					tmplist.append("\t\tHTMLclass:\""+pdata[item]["text"][-1] + "\",\n")
				tmplist.append("\t\ttext :{\n")
				tmplist.append("\t\t\tname: \""+item+"\",\n")
				if isinstance(pdata[item]["text"],dict):
					tmplist.append("\t\t\tcontact: \"assignee: "+pdata[item]["text"]["assignee"]+"\",\n")
					tmplist.append("\t\t\ttitle: \"status: " + pdata[item]["text"]['status'] + "\",\n")
					tmplist.append("\t\t\tdata_priority: \"priority: " + pdata[item]["text"]['priority'] + "\",\n")
					tmplist.append("\t\t\tdata_created: \"created: " + pdata[item]["text"]["created"] + "\",\n")
					tmplist.append("\t\t\tdata_updated: \"updated: " + pdata[item]["text"]["updated"] + "\",\n")
					tmplist.append("\t\t\tdesc: \"summary: "+pdata[item]["text"]["summary"].replace("\"","\'")+"\",\n")
				else:
					tmplist.append("\t\t\ttitle: \"status: " + pdata[item]["text"][-2] + "\",\n")
					tmplist.append("\t\t\tdesc: \"summary: "+pdata[item]["text"][1].replace("\"","\'")+"\",\n")
				tmplist.append("\t\t},\n")
				tmplist.append("\t\tlink: {\n")
				tmplist.append("\t\t\thref: \"https://jira.devtools.intel.com/browse/"+item+"\",\n")
				tmplist.append("\t\t\ttarget: \"_blank\"\n")
				tmplist.append("\t\t},\n")
				tmplist.append("\t};\n")
				new_list.extend(tmplist)
				data_list.append(item.replace("-","_"))
				data_key.remove(item)

	return data_list,new_list

def remove_same_list(bro_list):
	new_list = []
	for sublist in bro_list:
		if not sublist in new_list:
			new_list.append(sublist)
	return new_list

def get_config_array(data_list):
	data_list = remove_same_list(data_list)
	new_list = []
	new_list.append("\tvar chart_config = [\n")
	i = 1
	tmp=""
	for item in data_list:
		if i == 1:
			tmp += "\t\t\t"
		tmp += item
		if i < len(data_list):
			tmp += ","
		if i > 1 and i%10 == 0:
			tmp += "\n\t\t\t"
		i+=1
	new_list.append(tmp)
	new_list.append("\t];\n")
	return new_list


def merge_parent_child_list(datalist,outexamp_path):
	all_data = open(CUR_DIR + "/tmp_data/examp_up").readlines()
	down_data = open(CUR_DIR + "/tmp_data/examp_down").readlines()
	all_data += datalist
	all_data += down_data
	with open(outexamp_path,"w+") as ew:
		ew.writelines(all_data)
	
def create_html_file_from_json(key,filedir):
	# print parent_list
	data_list = ['config', 'Jira_root']
	all_data = []
	pdlist,parentList = get_parent_data(CUR_DIR + "/tmp_data/"+filedir+'/'+key+"/result_total.json")
	all_data += parentList
	data_list+=pdlist
	all_data += get_config_array(data_list)
	merge_parent_child_list(all_data,CUR_DIR + "/examp_templates/examps"+key+'_'+filedir+".html")
