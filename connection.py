import asyncio
import websockets
import json
from exer_elem_rec import ExerElem
from datetime import datetime

class WebsocketServer():
    def __init__(self, host, port,ws_inbound_queue,ws_outbound_queue,exer_elem,state):
        self.host = host
        self.port = port
        self.connections = set()
        self.ws_inbound_queue = ws_inbound_queue
        self.ws_outbound_queue = ws_outbound_queue
        self.exer_elem = exer_elem

        self.websocket_dict = {}
        self.state = state
        #self.logger = logger

    async def handle_connection(self, websocket):
        self.connections.add(websocket)
        #closed = asyncio.ensure_future(websocket.wait_closed())
        #closed.add_done_callback(lambda task: self.handle_connection_closed(task))

        try:
            async for message in websocket:
                # Handle inbound message
                await self.handle_inbound_message(message,websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connections.remove(websocket)
            await self.handle_connection_closed(websocket)

    async def handle_connection_closed(self,websocket):
        #async with self.exer_elem_lock:
        print('LHP Connection closed %s',websocket)
        deviceId = [key for key, value in self.websocket_dict.items() if value == websocket][0]
        self.exer_elem.remove_element(deviceId)

    async def handle_inbound_message(self, message,websocket):
        json_dict = json.loads(message)
        # print('WS handling inbound message: %s at: %s',json_dict,datetime.now())

        if "connected" in json_dict["payload"]:
            # print('client connected')
            self.websocket_dict[json_dict['deviceId']] = websocket
            #async with self.exer_elem_lock:
            init_dict = self.exer_elem.add_element(json_dict)
            await self.send_outbound_message(init_dict)
        elif "confirmedTask" in json_dict["payload"]:
            pass
        elif "initialized" in json_dict["payload"]:
            pass
        else:
            #todo fejlhåndtering hvis øvelse ikke er igang
            await self.ws_inbound_queue.put(message)
        

    async def send_outbound_message(self,msg_dict):
        # Send an outbound message to all connected clients
        # print('WS send outbound message: %s at: %s',msg_dict,datetime.now())
        msg_json = json.dumps(msg_dict)
        await self.websocket_dict[msg_dict['deviceId']].send(msg_json)
        # print('WS message sent: %s',datetime.now())
        
    async def outbound_loop(self):
        while not self.state.end.is_active:
            if not self.ws_outbound_queue.empty():
                msg_dict = await self.ws_outbound_queue.get()
                await self.send_outbound_message(msg_dict)
            await asyncio.sleep(0.01)
        self.stop_server.set_result('Gygag')

    async def start_server(self):
        print('Starting server')
        self.stop_server = asyncio.Future()
        outbound_task = asyncio.create_task(self.outbound_loop())
        print('outbound task started')
        async with websockets.serve(self.handle_connection, self.host, self.port,ping_interval=None,ping_timeout=None):
            await self.stop_server  # Keep the server running
        await outbound_task

'''
        self.server = websockets.serve(self.handle_connection, self.host, self.port,ping_interval=None,ping_timeout=None)
        await self.stop_server  # Keep the server running
        self.server.close()
        await outbound_task
'''    

async def main(host,port,file):
    ws_inbound_queue = asyncio.Queue()
    ws_outbound_queue = asyncio.Queue()
    exer_elem_lock = asyncio.Lock()
    
    exer_elem = ExerElem()
    exer_elem.load_exer('exercises_test.json')
    exer_elem.load_elem('elements.json') 

    ws_server = WebsocketServer(host,port,ws_inbound_queue,ws_outbound_queue,exer_elem,exer_elem_lock)

    # Start the WebSocket server in the main thread
    await ws_server.start_server()

if __name__ == '__main__':
    asyncio.run(main("192.168.0.100",8080,"file"))