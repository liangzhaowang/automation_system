import os
import json

class TestResult(object):
    csv_folder = None
    json_folder = None
    output_path = None
    current_loop = None
    test_name = None
    test_result = None
    test_unit = None
    test_attachments = []
    test_attch_modules = []
    
    def __init__(self, args):
        self.args = args[1:]
        self.output_path = self.get_output(args[1:]).split('@')[0]
        self.csv_folder = os.path.join(self.output_path, 'csv')
        self.json_folder = os.path.join(self.output_path, 'json')
        self.current_loop = self.get_output(args[1:]).split('@')[1]

    def get_output(self, args):
        if args.index('-o') < len(args) - 1:
            return args[args.index('-o') + 1]
        else:
            return None
        
    def save(self):
        data = {'name': self.test_name, 'daily': False, 'result': self.test_result, 'unit': self.test_unit, 'attachments': self.test_attachments, 'post2': self.test_attch_modules, 'loop': self.current_loop}
        file_name = os.path.join(self.json_folder, 'result_' + str(self.current_loop) + '.json')
        with open(file_name, 'w') as json_file:
            json_file.write(json.dumps(data))

    def result(self, test_name, result, unit = None):
        self.test_name = test_name
        self.test_result = result
        self.test_unit = unit
    
    def add_attachment(self, file_abs_path, post_to = None):
        print file_abs_path
        self.test_attachments.append(file_abs_path)
        self.test_attch_modules.append(post_to)