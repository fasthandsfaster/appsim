import json
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
import copy

class ExerElem:
    def __init__(self,logger,azure_conn,state):
        self.elem_dict= {}
        self.exer_dict = {}
        self.runtime_dict = {}
        self.nextElementId = 0
        self.logger = logger
        self.state = state
        self.azure_conn = azure_conn
    
    def find_match_element(self,task,elem_lists_dict,task_seq_to_elem_dict):
        match_done = False
        match_99_count = 0
        element_found = True
        elem_id_list = []
        device_id_list = []
        
        while not match_done:
            if task['seq'] in task_seq_to_elem_dict.keys():
                elem = task_seq_to_elem_dict[task['seq']]
                task['elem']=elem.copy()
                match_done = True
            else:
                if task['type'] in elem_lists_dict.keys():
                    elem = elem_lists_dict[task['type']].pop(0)
                    if len(elem_lists_dict[task['type']]) == 0:
                        del elem_lists_dict[task['type']]
                    task['elem']=elem.copy()
                    if task['seq'] == 99:
                        elem_id_list.append(elem['elementId'])
                        device_id_list.append({elem['deviceId']: elem['elementId']})
                        task['elem']['elementId'] = elem_id_list
                        task['elem']['deviceId'] = device_id_list
                        match_99_count += 1
                    else:
                        task_seq_to_elem_dict[task['seq']] = task['elem']
                        match_done = True
                        break
                else:
                    match_done = True
                    if not match_99_count > 0:
                        element_found = False
        
        return element_found
    
    def find_and_match_elem_tasks(self,obj,elem_lists_dict,task_seq_to_elem_dict):
        key = 'taskType'
        value = 'Elem'

        if isinstance(obj, dict):
            if key in obj and obj[key] == value:
                #Element task found, find matching element
                self.logger.debug(f'ExerElem: Find elem for: {obj}')
                task_element_match = self.find_match_element(obj,elem_lists_dict,task_seq_to_elem_dict)
                if task_element_match == False:
                    self.logger.debug(f'ExerElem: no elem for: {obj}')
                    self.exer_elements_match = False
            for k, v in obj.items():
                self.find_and_match_elem_tasks(v,elem_lists_dict,task_seq_to_elem_dict)
        elif isinstance(obj, list):
            for item in obj:
                self.find_and_match_elem_tasks(item,elem_lists_dict,task_seq_to_elem_dict)
        

    
    def elem_dict_to_lists(self,elem_dict):
        # Create dict with lists for each active element type
        elem_type_lists_dict = {}
        for key, value in elem_dict.items():
            if value['active'] == True:
                item_type = value['type']
                if item_type not in elem_type_lists_dict:
                    elem_type_lists_dict[item_type] = []

                elem_type_lists_dict[item_type].append(value)
        
        return elem_type_lists_dict

    def merge_exer_elem(self,exer_dict,elem_dict):
        for exercise in exer_dict['exerciseList']:
            elem_type_lists_dict = self.elem_dict_to_lists(elem_dict)
            task_seq_to_elem_dict = {}
            self.exer_elements_match = True
            self.find_and_match_elem_tasks(exercise['taskList'],elem_type_lists_dict,task_seq_to_elem_dict)

            self.logger.debug(f'Exerzise after element merge: {exercise}')

            self.runtime_dict[exercise['exercise']] = exercise

            self.runtime_dict[exercise['exercise']]['elementsMatch'] = self.exer_elements_match
        
        
        self.state.exer_list_flag.set()

        self.logger.debug(f'ExerElem: runtime_dict after merge: {self.runtime_dict}')



    def find_tasks(self,obj,key,value,task_list):
        # Find all ovjects containing a given key/value pair
        if isinstance(obj, dict):
            if key in obj and obj[key] == value:
                #Element task found, find matching element
                task_list.append(obj)
            for k, v in obj.items():
                self.find_tasks(v,key,value,task_list)
        elif isinstance(obj, list):
            for item in obj:
                self.find_tasks(item,key,value,task_list)

    '''           
    def check_exer_hw(self):
        exer_with_hw = []
        elem_task_list = []
        if self.state.exer_list_flag.is_set():
            self.logger.debug(f'check_exer_hw runtime dict: {self.runtime_dict}')
            for exer in self.runtime_dict.values():
                elem_task_list = []
                self.logger.debug(f'checking hw for: {exer}')
                self.find_tasks(exer['taskList'],'taskType','Elem',elem_task_list)
                self.logger.debug(f'Element_task_list:{elem_task_list}')
                hw_task_list = (list(filter(lambda task: task if 'elem' in task else None, elem_task_list)))
                self.logger.debug(f'hw_task_list: {hw_task_list}')
                if len(hw_task_list) == len(elem_task_list):
                    exername = exer['name']
                    self.logger.debug(f'hw OK for: {exername}')
                    exer_with_hw.append(exer)
        
            self.prev_runtime_dict_copy = copy.deepcopy(runtime_dict_copy)
            return exer_with_hw,True

        else:
            self.logger.debug(f'EXER HW  CHange: NO CHANGE')
            exer_with_hw = copy.deepcopy(self.prev_exer_with_hw)
            return exer_with_hw,False
    '''

    
    def get_runtime_dict(self):
        return copy.deepcopy(self.runtime_dict) 
    
    def get_elem_dict(self):
        return self.elem_dict

    def add_element(self,elemdict):
        self.logger.debug(f'ExerElem: adding new element: {elemdict}')
        existingElement = (list(filter(lambda element: element if element['deviceId'] == elemdict['deviceId'] else None, list(self.elem_dict.values()))))
        self.logger.debug(f'ExerElem: adding known element: {existingElement}')

        if len(existingElement) == 1:
            existingElement = existingElement[0]
            self.logger.debug(f'Handle known element: {existingElement}')
            self.nextElementId = existingElement['elementId']
            existingElement['active'] = True
            existingElement= []
        else:   
            self.logger.debug(f'Handle new element: {existingElement}')

            self.nextElementId += 1

            elementDict = {
                "elementId": self.nextElementId,
                "deviceId": elemdict["deviceId"],
                "type": elemdict["payload"]["type"],
                "hwVersion": elemdict["payload"]["hwVersion"],
                "swVersion": elemdict["payload"]["swVersion"],
                "active": True
            }
            self.elem_dict[self.nextElementId] = elementDict

            newElement = True
            self.logger.debug(f'elem_dict after new element: {self.elem_dict}')
            #self.elem_list = list(self.elem_dict.values())
            if len(self.exer_dict.values()) > 0:
                self.merge_exer_elem(self.exer_dict,self.elem_dict)
                self.logger.debug(f'\nruntime_dict after new element: {self.runtime_dict}\n')

        initDict = { 
            "deviceId": elemdict["deviceId"],
            "messageId": "ABC",
            "timestamp": "12:00:00",
            "elementId": self.nextElementId,
            "payload": {
                "task":"init",
                "elementId": self.nextElementId
            }
        }


        self.state.exer_list_flag.set()

        return initDict

    def remove_element(self,deviceId):
        self.logger.debug(f'ExerElem: Removing device {deviceId}')

        elementId = [key for key, value in self.elem_dict.items() if value['deviceId'] == deviceId][0]

        self.elem_dict[elementId]['active'] = False

        self.logger.debug(f'elem_dict after removed element: {self.elem_dict}')
        #self.elem_list = list(self.elem_dict.values())
        if len(self.exer_dict.values()) > 0:
            self.merge_exer_elem(self.exer_dict,self.elem_dict)
            self.logger.debug(f'\nruntime_dict after new element: {self.runtime_dict}\n')

        self.state.exer_list_flag.set()

    def load_exer_azure(self):

        self.exer_dict = self.azure_conn.get_exercise_definition()

        for exercise in self.exer_dict['exerciseList']:
            self.runtime_dict[exercise['exercise']] = exercise
            self.runtime_dict[exercise['exercise']]['elementsMatch'] = False
        
        self.state.exer_list_flag.set()

        self.logger.debug(f'ExerElem: runtime_dict after azure load: {self.runtime_dict}')

        if len(self.elem_dict.values()) > 0:
            self.merge_exer_elem(self.exer_dict,self.elem_dict)
        else:
            self.state.exer_list_flag.set()
            

    def load_exer(self,file):
        with open(file, 'r') as f:
            self.exer_dict = json.load(f)

            for exercise in self.exer_dict['exerciseList']:
                self.runtime_dict[exercise['exercise']] = exercise
                self.runtime_dict[exercise['exercise']]['elementsMatch'] = False
            
            self.state.exer_list_flag.set()

            self.logger.debug(f'ExerElem: runtime_dict after azure load: {self.runtime_dict}')

            if len(self.elem_dict.values()) > 0:
                self.merge_exer_elem(self.exer_dict,self.elem_dict)


    def load_elem(self,file):
        with open(file, 'r') as f:
            self.elem_dict = json.load(f)
            
            if len(self.exer_dict.values()) > 0:
                self.merge_exer_elem(self.exer_dict,self.elem_dict)   

if __name__ == "__main__":
    logger = Logger.with_default_handlers()
    
    exer_elem = ExerElem(logger)

    stream_handler = AsyncStreamHandler()
    logger = Logger.with_default_handlers()
    
    exer_elem.load_exer('exercises_test.json')
    exer_elem.load_elem('elements.json')