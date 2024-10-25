import asyncio
from interpreter import Interpreter
from exer_elem_rec import ExerElem
from connection import WebsocketServer
from azure_connection import AzureConn
from gui import Gui
import queue
import logging
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
import cProfile 
from pstats import SortKey, Stats
from statemachine import StateMachine, State

class AppState(StateMachine):    
    start= State('Start', initial=True)
    gui= State('Gui')
    popup_params = State('PopupParams')
    popup_elem = State('PopupElem')
    exer_countdown = State('ExerCountdown')
    exer_running = State('ExerRunning')
    exer_result = State('ExerResult')
    exer_over = State('ExerOver')
    end = State('End',final = True)
    exer_list_flag = asyncio.Event()
    current_exercise = ''

    evt_ready = start.to(gui)
    evt_exer_cycle = (
        gui.to(popup_params)
        | popup_params.to(exer_countdown)
        | exer_countdown.to(exer_running)
        | exer_running.to(exer_over)
        | exer_over.to(exer_result)
        | exer_result.to(gui)
    )

    evt_cancle_exer_cycle = (
        gui.to(gui)
        | popup_params.to(gui)
        | exer_countdown.to(gui)
        | exer_running.to(gui)
        | exer_result.to(gui)
        | exer_over.to(gui)
    )

    evt_show_elem = gui.to(popup_elem)

    evt_popup_cancle = (
        popup_elem.to(gui)
        | popup_params.to(gui)
        )
    

    evt_end = gui.to(end)


    

    async def before_evt_exer_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        print(f"Event {event} from {source.id} to {target.id}{message}")

    async def before_evt_cancle_exer_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Event {event} from {source.id} to {target.id}{message}"
        
    def set_current_exercise(self, exercise):
        self.current_exercise = exercise
    
    async def on_enter_gui(self):
        print('Gui entered')
    



async def main(host,port,file):
    ws_inbound_queue = asyncio.Queue()
    ws_outbound_queue = asyncio.Queue()
    heads_up_queue = asyncio.Queue()

    stream_handler = AsyncStreamHandler()
    #file_handler = AsyncFileHandler(filename='appsim.log', mode='a')
    
    logger = Logger.with_default_handlers(level=logging.DEBUG)

    logger.info('AppSim:Starting')
    
    app_state = AppState()

    azure_conn = AzureConn(logger)
    exer_elem = ExerElem(logger,azure_conn,app_state)
    #exer_elem.load_exer_azure()
    exer_elem.load_exer('json/exercises_test.json')
    #exer_elem.load_elem('json/elements.json') 

    ws_server = WebsocketServer(host,port,ws_inbound_queue,ws_outbound_queue,exer_elem,app_state)

    interpreter = Interpreter(ws_inbound_queue,ws_outbound_queue,heads_up_queue,exer_elem,logger,azure_conn,app_state)
    gui = Gui(interpreter,exer_elem,heads_up_queue,logger,app_state)


    gui_task = asyncio.create_task(gui.start())   
    logger.info('AppSim:Gui Task started')
    
    await ws_server.start_server()
    logger.info('AppSim: server started')
    #await ws_server_task
    await gui_task

    await asyncio.gather(stream_handler.close()) #, file_handler.close())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main("192.168.8.123",8080,"file"))




