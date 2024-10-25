import json
import time
import asyncio
import random
from datetime import datetime,timedelta
import uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import copy

class Interpreter():
    def __init__(self,ws_inbound_queue,ws_outbound_queue,heads_up_queue,exer_elem,logger,azure_conn,state):
        self.exer_list = []
        self.elem_list= []
        self.exer_dict = {}
        self.prev_device = {}
        self.exer_elem = exer_elem
        self.ws_inbound_queue = ws_inbound_queue
        self.ws_outbound_queue = ws_outbound_queue
        self.heads_up_queue = heads_up_queue
        self.state = state
        self.logger = logger
        self.start_time = datetime.now()
        self.current_time = self.start_time
        self.task_result_list = []
        self.countdown_count = 0
        self.azure_conn = azure_conn
        random.seed(str(datetime.now()))

    def countdown(self):
        for i in range(3, 0, -1):
            self.countdown_count = i
            time.sleep()

    
    def handle_interpreter_parameter(self,exer_name,parameter):
        # All exercise specific parameter handling to determine parameter values
        # at exercution time goes here
        match exer_name:
            case "Horseshoe" | "Horseshoe2":
                if parameter == "timeout":
                    return datetime.now()
                elif parameter == "path":
                    choice = random.choice(["TP_B_TO_A", "TP_A_TO_B"])
                    self.logger.debug(f'Random choice {choice}\n\n')
                    return choice
                else:
                    self.logger.debug(f'Exercise: {exer_name} parameter {parameter} unhandled:')
                    return None
            case _:
                self.logger.debug(f'Exercise: {exer_name} interpreter parameter handling undefined:')
                return None
    
    async def run_exercise(self,user,exer_name,app_parameters,elem_parameters):
        self.task_result_list = []
        self.start_time = datetime.now()
        exercise_result = {
            'ExecId': str(uuid.uuid4()),
            'user': user,
            'exerName': exer_name,
            'app_parameters': app_parameters,
            'elem_parameters': elem_parameters,
            'startTime': str(self.start_time),
            'endTime': "",
            'result': {
                'taskResultList': self.task_result_list
            }
        }

        #self.countdown()

        task_result_template = {
            'task': {},
            'setTime': datetime.now(),
            'replyTime': datetime.now(),
            'reply': {}
        }

        exercise = self.exer_elem.get_runtime_dict()[exer_name]
        
        #if the endcondition value is set in the parametrs popup it must be transfered to the exercise runtime copy
        if 'endCondition' in app_parameters and app_parameters['endCondition'] != "":
           exercise['endCondition']['condition'] = int(app_parameters['endCondition'])

        self.logger.debug(f'running exercise: {exercise}')

        self.current_time = self.start_time
        wait_for_anwser = False
        task_stack = copy.deepcopy(exercise['taskList'])
        while self.state.exer_running.is_active:
            if not wait_for_anwser:
                self.logger.debug(f'task stack: {task_stack}\n\n')
                task = copy.deepcopy(task_stack.pop(0))
                set_time = datetime.now()
                self.logger.debug(f' handling task: {task}\n\n')
                if task['taskType'] == 'Elem':
                    task_result = {}
                    task_result['task'] = task
                    task_result['setTime'] = str(set_time)
                    self.task_result_list.append(task_result)
                    if 'parameters' in task['setPayload']:
                        param = task['setPayload']['parameters']
                        self.logger.debug(f'element set parameters: {param}\n\n')
                        for k,v in task['setPayload']['parameters'].items():
                            if v == "Interpreter":
                                task['setPayload']['parameters'][k] = self.handle_interpreter_parameter(exer_name,k)
                            elif k in elem_parameters.keys():
                                task['setPayload']['parameters'][k] = elem_parameters[k]
                            else:
                                self.logger.debug(f'parameter: {k} unhandled')
                        self.logger.debug(f'setting task: {task} at: {self.current_time}')
                    await self.set_task(task)

                    if task['resultType'] == 'Sync':
                        wait_for_anwser = True
                    else:
                        wait_for_anwser = False
                    
                elif task['taskType'] == 'Ctrl':
                    repeat_tasks = []
                    if task['type'] == 'Repeat':
                        if 'count' in  task:
                            for i in range(task['count']):
                                repeat_tasks = repeat_tasks + task['taskList']
                            task_stack = repeat_tasks + task_stack
                        else:
                            task_stack = task['taskList'] + [task] + task_stack
                    if task['type'] == 'Random':
                        task_stack = [random.choice(task['taskList'])] + task_stack

            if not self.ws_inbound_queue.empty():
                input_json = await self.ws_inbound_queue.get()
                input = json.loads(input_json)
                self.current_time = datetime.now()
                self.logger.debug(f'handling result: {input} at: {self.current_time}')

                if 'payload' in input:
                    self.logger.debug(f'processing time {self.current_time - set_time}')
                    if "solved" in input["payload"]:
                        self.task_result_list[-1]['replyTime'] = str(self.current_time)
                        self.task_result_list[-1]['reply'] = input
                        await self.heads_up_queue.put(0)
                        input = {}
                
                    wait_for_anwser = False
            
            if self.check_end_condition(self.task_result_list,exercise['endCondition'],task_stack):
                await self.state.send('evt_exer_cycle')
                exercise_result['result']['taskResultList'] = self.task_result_list
                exercise_result['endTime'] = str(self.current_time) #str(datetime.now())
                await self.send_over_tasks(exercise)
            self.current_time = datetime.now()

            await asyncio.sleep(0.01)
        
        self.handle_result(exercise_result)

    
    def check_end_condition(self,task_result_list,end_condition,task_stack):
        if len(task_stack) == 0:
            return True
        
        if end_condition['type'] == 'countSolved':
            solved_results = (list(filter(lambda result: result if 'reply' in result and result['reply']["payload"]['solved'] == True else None, task_result_list)))
            return len(solved_results) >= end_condition['condition']
        elif end_condition['type'] == 'time':
            return self.current_time - self.start_time > timedelta(seconds=end_condition['condition'])

    def handle_result(self,result):
        self.logger.debug(f'Exercise result: {result}')

        self.azure_conn.upload_result(result)


    async def set_task(self,task):
        if task['seq'] == 99:
            device_list = task['elem']['deviceId'].copy()
            if self.prev_device in device_list:
                device_list.remove(self.prev_device)
            device = random.choice(device_list)
            device_id = list(device.keys())[0]
            element_id = list(device.values())[0]
            self.prev_device = device
        else:
            device_id = task['elem']['deviceId']
            element_id = task['elem']['elementId']

        setDict = {
            "deviceId": device_id,
            "messageId": "ABC",
            "timestamp": "12:00:00",
            "elementId": element_id,
            "payload": 
            {
                "task": "set",
                "parameters": task['setPayload']['parameters']
            }
        }

        await self.ws_outbound_queue.put(setDict)
        await self.heads_up_queue.put(element_id)

    def find_tasks(self,obj,key,value,task_list):
        if isinstance(obj, dict):
            if key in obj and obj[key] == value:
                #Element task found, find matching element
                task_list.append(obj)
            for k, v in obj.items():
                self.find_tasks(v,key,value,task_list)
        elif isinstance(obj, list):
            for item in obj:
                self.find_tasks(item,key,value,task_list)

    async def send_over_tasks(self,exer):
        self.logger.debug(f'Exercise over:{exer}')
        elem_task_list = []
        self.find_tasks(exer['taskList'],'taskType','Elem',elem_task_list)
        self.logger.debug(f'Send over to elements:{elem_task_list}')

        for task in elem_task_list:
            if task['seq'] == 99:
                for id in task['elem']['deviceId']:
                    for deviceId in id:
                        overDict = {
                                "deviceId": deviceId,
                                "messageId": "ABC",
                                "timestamp": "12:00:00",
                                "elementId": id[deviceId],
                                "payload": 
                                {
                                    "task": "over",
                                    "result": 999
                                }
                            } 
                    
                    await self.ws_outbound_queue.put(overDict)
            else:
                overDict = {
                        "deviceId": task['elem']['deviceId'],
                        "messageId": "ABC",
                        "timestamp": "12:00:00",
                        "elementId": task['elem']['elementId'],
                        "payload": 
                        {
                            "task": "over",
                            "result": 999
                        }
                    }

                await self.ws_outbound_queue.put(overDict)



if __name__ == "__main__":

    with open('exercises_test.json', 'r') as f:
        exer_dict = json.load(f)


    with open('elements.json', 'r') as f:
        elem_dict = json.load(f)
