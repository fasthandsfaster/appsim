import asyncio 
import pygame
import pygame_gui
import cProfile
import os
import time
import copy
from hockeyrink import Rink

os.environ['PYGAME_BLEND_ALPHA_SDL2'] = '1'

class Gui:
    def __init__(self,interpreter,exer_elem,heads_up_queue,logger,state):
        pygame.init()
        self.screen = pygame.display.set_mode((1700, 1000))
        pygame.display.set_caption('GUI Window')
        
        self.set_element = 0
        self.end_condition = 0
        self.exer_buttons_list = []
        self.interpreter = interpreter
        self.exer_elem = exer_elem
        self.state = state
        self.heads_up_queue = heads_up_queue
        self.exer_with_hw = []
        self.logger = logger
        self.exer_exec_count = 0
        self.profiler = cProfile.Profile()
        self.draw_popup = False
        self.draw_popup_once = False
        self.manager = pygame_gui.UIManager((350, 750),'json/simple_theme.json')
        self.popup_manager = pygame_gui.UIManager((550, 750),'json/simple_theme.json')
        self.exer_manager = pygame_gui.UIManager((550, 750),'json/simple_theme.json')
        image = pygame.image.load('pictures/stadium.jpg')
        self.image = pygame.transform.scale(image, (1700, 1000))
        self.big_font = pygame.font.SysFont('DS-Digital',130)
        self.med_font = pygame.font.SysFont('DS-Digital',80)
        self.small_font = pygame.font.SysFont('DS-Digital',18)
        self.transparent_blue = (0,0,255,180)
        self.dark_transparent_blue = (15,37,75,240)
        self.prev_runtime_dict_copy = {}
        self.prev_exer_with_hw = []
        self.rink = Rink()
        self.main_buttons_list = []

    async def handle_events(self, event):
        gui_message = {
            'command':'',
            'gui_input':{}
        }

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.stop_button:
                #stop current exercise
                self.state.send('evt_cancle_exer_cycle')
            elif event.ui_element == self.terminate_button:
                #close down system
                self.state.send('evt_end')
            elif event.ui_element == self.elements_button:
                #Display currently connected elements
                self.state.send('popup_elem')

                self.element_window, self.close_button, self.element_buttons_list = self.create_element_window()
                self.draw_popup = True
            elif event.ui_element == self.load_button:
                pass
            elif event.ui_element == self.confirm_button:
                #Confirm pressed on the exercise parameters window
                self.logger.debug(f'Starting exercise task: {self.state.current_exercise}')
                self.state.send('evt_exer_cycle')
                #Countdown code
                self.state.send('evt_exer_cycle')
                self.start_exercise()
            elif event.ui_element == self.close_button:
                #handle all Close buttons on popups if existing 
                self.state.send('evt_popup_cancle')
                self.popup_manager.clear_and_reset()
                self.draw_popup = False
                self.draw_popup_once = True
            else:
                # An exercise is choosen and parameters can be set
                await self.prepare_exercise(event)


    async def prepare_exercise(self,event):
        self.reset_scoreboard()
        for button in self.exer_buttons_list:
            if event.ui_element == button:
                exer_name = str(button.text)
                self.state.set_current_exercise(exer_name)
                self.state.send('evt_exer_cycle')
                self.surfaces['score']['sur'].fill(self.transparent_blue)
                self.surfaces['game']['sur'].fill(self.dark_transparent_blue)
                self.logger.debug(f'Open parameter window for: {self.state.current_exercise}')
                self.parameter_window, self.parameter_rect,self.parameter_fields, self.confirm_button = self.create_parameter_window(button.text)
                self.draw_popup = True
                if self.exer_elem.get_runtime_dict()[self.state.current_exercise]['type'] == 'Ice':
                    self.rink.draw_rink()
                    self.rink.draw_elements(self.exer_elem.get_runtime_dict()[self.state.current_exercise]['outline'])
                    self.rink.rink_surface.blit(self.rink.elem_surface,(0,0))
                    self.surfaces['game']['sur'].blit(self.rink.rink_surface,self.rink.rink_surface.get_rect(center=self.surfaces['game']['sur'].get_rect().center))
                else:
                    await self.draw_heads_up_elements(self.exer_elem.get_runtime_dict()[self.state.current_exercise]['outline'])
                break

    def start_exercise(self):
        app_parameter_values = {}
        elem_parameter_values = {}
        parameter_values = {}
        # Translate pygame_gui input fields to dictionary
        for key in self.parameter_fields.keys():
            self.logger.debug(f'handling key: {key}')
            parameter_values = {}
            if type(self.parameter_fields[key][0]) == pygame_gui.elements.UITextEntryLine:
                parameter_values[key] = self.parameter_fields[key][0].get_text()
                self.logger.debug(f'{key} value {parameter_values[key]}')
            elif type(self.parameter_fields[key][0]) == pygame_gui.elements.UIDropDownMenu:
                parameter_values[key] = self.parameter_fields[key][0].selected_option
                self.logger.debug(f'{key} selected option {parameter_values[key]}')
        
            if self.parameter_fields[key][1] == 'App':
                app_parameter_values[key] = parameter_values.copy()[key]
            else:
                elem_parameter_values[key] = parameter_values.copy()[key]

        self.logger.debug(f'App Parameter dict {app_parameter_values}')
        self.logger.debug(f'Elem Parameter dict {elem_parameter_values}')
        self.popup_manager.clear_and_reset()
        self.draw_popup = False
        self.draw_popup_once = True
        self.profiler = cProfile.Profile()
        self.exer_exec_count += 1
        self.file = 'exercise' + str(self.exer_exec_count) + '.profile'
        self.profiler.enable()

        self.interpreter_task = asyncio.create_task(self.interpreter.run_exercise('hosse',self.state.current_exercise,app_parameter_values,elem_parameter_values))
 


    async def draw(self):
        #self.screen.fill((255, 255, 255))
        self.screen.blit(self.image, (0, 0))
        self.update_exer_list()
        
        self.manager.draw_ui(self.gui_surface['sur'])
        self.exer_manager.draw_ui(self.gui_surface['sur'])
        if self.state.exer_running.is_active:
            if not self.exer_elem.get_runtime_dict()[self.state.current_exercise]['type'] == 'Ice':
                await self.draw_heads_up_elements(self.exer_elem.get_runtime_dict()[self.state.current_exercise]['outline'])
            else:
                self.rink.rink_surface.blit(self.rink.elem_surface,(0,0))
                self.surfaces['game']['sur'].blit(self.rink.rink_surface,self.rink.rink_surface.get_rect(center=self.surfaces['game']['sur'].get_rect().center))
            
            self.draw_scoreboard(self.exer_elem.get_runtime_dict()[self.state.current_exercise])
        else:
            self.draw_scoreboard({})

        for surface in self.surfaces.values():
            surface['sur'].blit(surface['txt'], (10,10))
            self.screen.blit(surface['sur'], surface['loc'])
        
        self.screen.blit(self.gui_surface['sur'], self.gui_surface['loc'])
        self.popup_surface['sur'].fill((0,0,0,0))
        if self.draw_popup or self.draw_popup_once:
            self.popup_manager.draw_ui(self.popup_surface['sur'])
            self.screen.blit(self.popup_surface['sur'], self.popup_surface['loc'])
            self.draw_popup_once = False

        pygame.display.flip()

    def create_parameter_window(self,exer_name):
        #param_list = []
        param_dict = {}
        param_count = 0
        param_start_count = len(self.exer_elem.get_runtime_dict()[exer_name]['parameters'])

        parameter_rect = pygame.Rect((50, 50), (400,200 + 40*param_start_count))

        parameter_window = pygame_gui.elements.UIWindow(
            parameter_rect,  # Adjust the position and size
            manager=self.popup_manager,
            window_display_title="Parameter Window"
        )
    
        for param in self.exer_elem.get_runtime_dict()[exer_name]['parameters']:
            
            dyn_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((50, 50 + 40*param_count), (100, 20)),
                text=param['name'],
                container=parameter_window,
                manager=self.popup_manager
            )

            if param['type'] == 'List':
                values_list = []
                default = ''
                for val in param['validValues']:
                    values_list.append(val['value'])
                    if 'default' in val:
                        if val['default'] == True:
                            default = val['value']

                dyn_param = pygame_gui.elements.UIDropDownMenu(values_list,
                                                    starting_option=default,
                                                    relative_rect=pygame.Rect((50, 70 + 40*param_count), (100, 20)),
                                                    container=parameter_window,
                                                    manager=self.popup_manager)
            
            else:
                dyn_param = pygame_gui.elements.UITextEntryLine(
                    relative_rect=pygame.Rect((50, 70 + 40*param_count), (100, 20)),
                    initial_text="",
                    container=parameter_window,
                    manager=self.popup_manager
                )

            param_dict[param['name']] = [dyn_param,param['paramType']]
            param_count += 1



        # Create a confirm button
        confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 80 + 40*param_count), (100, 40)),
            text="Confirm",
            manager=self.popup_manager,
            container=parameter_window
        )

        return parameter_window,parameter_rect,param_dict,confirm_button

    async def draw_heads_up_elements(self,outline):
        #self.logger.debug(f'drawing heads_up elements:')
        if not self.heads_up_queue.empty():
            self.set_element = await self.heads_up_queue.get()
            self.logger.debug(f'heads_up queue element: {self.set_element}')
        
        self.surfaces['game']['sur'].fill(self.dark_transparent_blue)


        for element in outline['elements']:
            #print('draw element\n')
            #print(element)

            if self.set_element == element['id']:
                color = (0,255,0)
            else:
                color = (0,0,255)

            if element['type'] == 'Port':
                element_rect = pygame.Rect(0, 0, element['shape']['width'], element['shape']['height'])
                #rotated_rect.center = ((i + 1) * width // 4, height // 2)
                element_surface = pygame.Surface((element['shape']['width'], element['shape']['height']), pygame.SRCALPHA)
                pygame.draw.rect(element_surface, color, (0, 0,element['shape']['width'],element['shape']['height']))
                element_surface = pygame.transform.rotate(element_surface,element['rotation'])
                self.surfaces['game']['sur'].blit(element_surface,(element['x'],element['y']))
            elif element['type'] == 'Triangle':
                side_loc  = [(60,0,50),(-60,150,50),(0,30,300)]
                element_surface = pygame.Surface((400, 400), pygame.SRCALPHA)
                for rotation,x,y in side_loc:
                    self.logger.debug(f'side loc: {rotation},{x},{y}')
                    side_surface = pygame.Surface((element['shape']['width'], element['shape']['height']), pygame.SRCALPHA)
                    pygame.draw.rect(side_surface, color, (0, 0,element['shape']['width'],element['shape']['height']))
                    side_surface = pygame.transform.rotate(side_surface,rotation + element['rotation'])
                    element_surface.blit(side_surface,(x,y))

                self.surfaces['game']['sur'].blit(element_surface,element_surface.get_rect(center=self.surfaces['game']['sur'].get_rect().center))

    def reset_scoreboard(self):
        self.surfaces['score']['sur'].fill(self.transparent_blue)

        formatted_runtime = "00:00:00"
                
        time = f'{formatted_runtime}'
        tasks_atempts = f'0'
        tasks_solved = f'0'
        tasks_failed = f'0'
        time_text = self.big_font.render(time,True,(0,255,0))
        tasks_atempts_text = self.med_font.render(tasks_atempts,True,(255,255,255))
        tasks_solved_text = self.med_font.render(tasks_solved,True,(0,255,0))
        tasks_failed_text = self.med_font.render(tasks_failed,True,(255,0,0))

        self.surfaces['score']['sur'].blit(time_text, (250,50))
        self.surfaces['score']['sur'].blit(tasks_atempts_text, (900,20))
        self.surfaces['score']['sur'].blit(tasks_solved_text, (900,80))
        self.surfaces['score']['sur'].blit(tasks_failed_text, (900,140))

    def draw_scoreboard(self,exercise):
        
        #scoreboard_rect = pygame.Rect(800,30, 400, 300)
        #self.screen.blit(self.image, scoreboard_rect, scoreboard_rect) # draw the needed part of the background

        self.surfaces['score']['sur'].fill(self.transparent_blue)
    
        runtime = self.interpreter.current_time - self.interpreter.start_time
        
        task_result_list = self.interpreter.task_result_list

        tasks_atempts = len(task_result_list)
        tasks_solved = len(list(filter(lambda result: result if 'reply' in result and result['reply']["payload"]['solved'] == True else None, task_result_list)))
        tasks_failed = len(list(filter(lambda result: result if 'reply' in result and result['reply']["payload"]['solved'] == False else None, task_result_list)))

        formatted_runtime = "{:02d}:{:02d}:{:02d}".format((runtime.seconds // 60) % 60,
                                                            runtime.seconds % 60, 
                                                            (runtime.microseconds // 10000)%100)
                
        time = f'{formatted_runtime}'
        tasks_atempts = f'{tasks_atempts}'
        tasks_solved = f'{tasks_solved}'
        tasks_failed = f'{tasks_failed}'
        time_text = self.big_font.render(time,True,(0,255,0))
        tasks_atempts_text = self.med_font.render(tasks_atempts,True,(255,255,255))
        tasks_solved_text = self.med_font.render(tasks_solved,True,(0,255,0))
        tasks_failed_text = self.med_font.render(tasks_failed,True,(255,0,0))

        self.surfaces['score']['sur'].blit(time_text, (250,50))
        self.surfaces['score']['sur'].blit(tasks_atempts_text, (900,20))
        self.surfaces['score']['sur'].blit(tasks_solved_text, (900,80))
        self.surfaces['score']['sur'].blit(tasks_failed_text, (900,140))
    
    def draw_countdown(self):
        count = self.interpreter.countdown_count
        count = f'{count}'
        count_text =  self.med_font.render(count,True,(0,255,0))

        self.surfaces['game']['sur'].blit(count_text, (260,100))

    def create_element_window(self):
        elem_count = 0
        element_window = pygame_gui.elements.ui_window.UIWindow(
            pygame.Rect(50, 50, 400, 300),  # Adjust the position and size
            manager=self.popup_manager,
            window_display_title="Elements Window",
            element_id='elem_window'
        )
        element_buttons_list = []
        for element in self.exer_elem.get_elem_dict().values():
            element_text = element['type'] + ' Id: ' + str(element['elementId']) + ' Mac: ' + element['deviceId']
            element_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((50, 50 + 50*elem_count), (325, 40)),
                text=element_text,
                manager=self.popup_manager,
                container=element_window
            )
            element_buttons_list.append(element_button)
            elem_count += 1

        element_close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((250, 200), (100, 40)),
            text="Close",
            manager=self.popup_manager,
            container=element_window,
        )

        return element_window, element_close_button, element_buttons_list
    
    def update_exer_list(self):
        tmp_exer_buttons_list = []
        exer_count = 0
        runtime_dict = self.exer_elem.get_runtime_dict()

        if self.state.exer_list_flag.is_set():
            self.logger.debug(f'updating exercise list: {runtime_dict}')
            self.exer_manager.clear_and_reset()
            self.surfaces['exer']['sur'].fill(self.transparent_blue)
            for name,exer in runtime_dict.items():
                self.logger.debug(f'handling: {exer}')
                dyn_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((415, 80 + 50*exer_count), (120, 40)),
                    text=exer['exercise'],
                    manager=self.exer_manager
                )
                if exer['elementsMatch'] == False:
                    dyn_button.disable()

                tmp_exer_buttons_list.append(dyn_button)
                exer = exer['exercise']
                self.logger.debug(f'adding button for {exer}')
                exer_count += 1

            self.exer_buttons_list = tmp_exer_buttons_list
            self.state.exer_list_flag.clear()

    def draw_control_gui(self):
        start = 80
        
        self.stop_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((80,start), (240, 40)),
            text='Stop current exercise',
            manager=self.manager
        )
        self.main_buttons_list.append(self.stop_button)

        self.terminate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((80,start + 50), (240, 40)),
            text='End ATC',
            manager=self.manager
        )
        self.main_buttons_list.append(self.terminate_button)
                
        self.refresh_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((80, start + 100), (240, 40)),
            text='Refresh elements',
            manager=self.manager
        )
        self.main_buttons_list.append(self.refresh_button)
        
        self.elements_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((80, start + 150), (240, 40)),
            text='List elements',
            manager=self.manager
        )
        self.main_buttons_list.append(self.elements_button)
        
        self.load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((80, start + 200), (240, 40)),
            text='Load exercises',
            manager=self.manager
        )
        self.main_buttons_list.append(self.load_button)
        
    async def start(self):
        clock = pygame.time.Clock()
        
        self.screen.blit(self.image,self.image.get_rect())

        self.draw_control_gui()

        #self.state.exer_list_flag.set()

        self.confirm_button = None
        self.close_button = None
        self.parameter_fields = []
        self.surfaces = {}

        self.surfaces['ctrl'] = {'loc':(50,50),'sur':pygame.Surface((300, 500), pygame.SRCALPHA),'txt':self.small_font.render('Menu', True, (255, 255, 255))}
        self.surfaces['exer'] = {'loc':(400,50),'sur':pygame.Surface((150, 500), pygame.SRCALPHA), 'txt':self.small_font.render('Exercises', True, (255, 255, 255))}
        self.surfaces['stats'] = {'loc':(50,600),'sur':pygame.Surface((500, 350), pygame.SRCALPHA), 'txt':self.small_font.render('Stats', True, (255, 255, 255))}
        self.surfaces['score'] = {'loc':(600,50),'sur':pygame.Surface((1050, 200), pygame.SRCALPHA), 'txt':self.small_font.render('Score', True, (255, 255, 255))}
        self.surfaces['game'] = {'loc':(600,300),'sur':pygame.Surface((1050, 650), pygame.SRCALPHA), 'txt':self.small_font.render('Heads Up', True, (255, 255, 255))}
        self.gui_surface ={'loc':(0,0),'sur':pygame.Surface((550, 750), pygame.SRCALPHA)}
        self.popup_surface ={'loc':(0,0),'sur':pygame.Surface((550, 750), pygame.SRCALPHA)}
        self.background_surface ={'loc':(0,0),'sur':pygame.Surface((1700, 1000))}
        
        for surface in self.surfaces.values():
            pygame.draw.rect(surface['sur'],self.transparent_blue, surface['sur'].get_rect())

        self.gui_surface['sur'].fill((0,0,0,0)) #fully transparent
        self.popup_surface['sur'].fill((0,0,0,0)) #fully transparent

        await self.draw()

        pygame.display.update()

        self.state.send('evt_ready')
        
        #print("Gui initial runtime dict")
        #print(self.exer_elem.get_runtime_dict())
        
        #self.update_exer_list()

        try:
            while not self.state.end.is_active:

                dt = clock.tick(60) 
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.state.send('end')


                    if self.draw_popup == True or self.draw_popup_once == True:
                        self.popup_manager.process_events(event)
                    else:
                        self.manager.process_events(event)
                    
                    self.exer_manager.process_events(event)

                    await self.handle_events(event)

                self.manager.update(dt)
                self.popup_manager.update(dt)
                self.exer_manager.update(dt)

                await self.draw()

                pygame.display.update()

                if self.state.exer_over.is_active:
                    #print('Waiting for interpreter')
                    await self.interpreter_task
                    self.state.send('evt_exer_cycle')
                    #dispaly result
                    self.state.send('evt_exer_cycle')

                    '''
                    self.profiler.disable()
                    self.profiler.create_stats()
                    self.profiler.dump_stats(self.file)
                    await asyncio.sleep(1)
                    await self.logger.debug(f'Exer profiler stats: {self.file}')
                    del self.profiler
                    '''


                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("gui terminated by ctrl-c")
            pygame.quit()
        
        if hasattr(self, 'interpreter_task'):
            if not self.interpreter_task.done():
                await self.interpreter_task
        
        pygame.quit()


