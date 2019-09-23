#!/usr/bin/env python
import os
import json
import re


class parse_flash_json:
    def __init__(self, configurations, image_path):
        self.configurations = configurations
        self.json_path = os.path.join(image_path, './flash.json')
        self.image_path = image_path
        self.json_data = dict()
        self.json_configurations = dict()
        self.json_conf = dict()
        self.json_group = dict()
        self.json_cparameters = dict()
        self.json_parameters = dict()
        self.json_command = []

    def get_json_data(self):
        jsfile = file(self.json_path)
        self.json_data = json.load(jsfile)
        jsfile.close()
        for key, value in self.json_data['flash'].items():
            if key == 'parameters':
                self.json_parameters = value
            elif key == 'configurations':
                self.json_configurations = value

    def parse_cofigurations_data(self):
        self.json_conf = self.json_configurations[self.configurations]
        for key, value in self.json_conf.items():
            if key == 'groupsState':
                self.json_group = value
            elif key == 'parameters':
                self.json_cparameters = value
            elif key == 'description':
                print value

    def get_enable_group(self):
        enable_group_list = []
        for key, value in self.json_group.items():
            if value:
                enable_group_list.append(str(key))

        return enable_group_list

    def get_parameters_data(self):
        for key, value in self.json_parameters.items():
            if self.json_cparameters.has_key(key):
                self.json_parameters[key] = os.path.abspath(self.image_path + str(value['options'][self.json_cparameters[key]]['value']))
            else:
                self.json_parameters[key] = os.path.abspath(self.image_path + str(value['value']))

    def get_command_from_json(self):
        enable_group = self.get_enable_group()
        for item in self.json_data['flash']['commands']:
                if str(item['tool']) == 'fastboot'and self.configurations in str(item['restrict']):
                    if item.has_key('group'):
                        if str(item['group']) in enable_group:
                            self.json_command.append(item)
                    else:
                        self.json_command.append(item)

    def replace_command_args_parameter(self, outlist):
        flash_command = []
        for item in outlist:
            searchobj = re.search(r'\${(?P<value>\S+)}', item, re.M | re.I)
            if searchobj:
                flash_command.append(item.strip(searchobj.group())+self.json_parameters[searchobj.group('value')])
            else:
                flash_command.append(item)

        return flash_command

    def get_ifwi_name(self):
        if 'ifwi_dnx' in self.json_cparameters:
            return 'ifwi_'+self.json_cparameters['ifwi_dnx'].split('/')[-1]+'.bin'
        elif 'gpt' in self.json_cparameters:
            return 'ifwi_' + self.json_cparameters['gpt'].split('/')[-1] + '.bin'
        else:
            print 'please input ifwi name with yourself'
        return False

    def parse_command_dict_get_output_command(self):
        out_list = []

        for item in self.json_command:
            out_list.append(str(item['args']))

        return self.replace_command_args_parameter(out_list)

    def output_command_list(self):
        command_data = []
        if os.path.exists(self.json_path):
            self.get_json_data()
            self.parse_cofigurations_data()
            self.get_parameters_data()
            self.get_command_from_json()
            if self.get_ifwi_name():
                command_data.append(self.get_ifwi_name())
            command_data.append(self.parse_command_dict_get_output_command())
        return command_data
