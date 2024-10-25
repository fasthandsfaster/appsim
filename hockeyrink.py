import pygame
import json
import math

class Rink:
    def __init__(self):
        self.height = 500
        self.width = 1000
        self.rink_surface = pygame.Surface((self.width,self.height), pygame.SRCALPHA)
        self.elem_surface = pygame.Surface((self.width,self.height), pygame.SRCALPHA)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 0, 255)
        self.RED = (255,0,0)
        

    def draw_rink(self):
        line_width = 3
        goal_line_indent = round(self.width/10)
        crease_width = round(self.height/11)
        crease_height = round(self.height/8)
        blue_line_width = 10
        blue_line_indent = round(self.width*(3/8))
        center_line_width = 10
        center_line_indent = self.width/2
        center_circle_diameter = round(self.width*(1/16))
        faceoff_circle_diameter = round(self.width*(1/16)*1.05)
        faceoff_x = round(self.width/5)
        faceoff_y = round(self.height/5)
        goal_size = round(self.height/6)
        
        ice_rect = pygame.Rect(0,0, self.width, self.height)
        pygame.draw.rect(self.rink_surface, self.WHITE, ice_rect, border_radius=round(self.width/11))
        
        pygame.draw.rect(self.rink_surface, self.BLUE, (goal_line_indent,0,line_width,self.height)) #Goal lines
        pygame.draw.rect(self.rink_surface, self.BLUE, (self.width - goal_line_indent - line_width,0,line_width,self.height))
        
        pygame.draw.rect(self.rink_surface, self.BLUE, (goal_line_indent,round((self.height - crease_height)/2),crease_width,crease_height)) #Creases
        pygame.draw.rect(self.rink_surface, self.WHITE, (goal_line_indent + line_width,round((self.height - crease_height)/2) + line_width,crease_width - line_width*2,crease_height - line_width*2))
        pygame.draw.rect(self.rink_surface, self.BLUE, (self.width - goal_line_indent - crease_width,round((self.height - crease_height)/2),crease_width,crease_height)) 
        pygame.draw.rect(self.rink_surface, self.WHITE, (self.width - goal_line_indent - crease_width + line_width,
                                                         round((self.height - crease_height)/2) + line_width,
                                                         crease_width - line_width*2,
                                                         crease_height - line_width*2))
   

        pygame.draw.rect(self.rink_surface, self.RED,(goal_line_indent + line_width - round(goal_size/2), #Goal1
                                                       round((self.height - goal_size)/2),
                                                       goal_size/2,goal_size),border_radius=round(goal_size/2))
        pygame.draw.rect(self.rink_surface, self.WHITE,(goal_line_indent + line_width*3 - round(goal_size/2), 
                                                       round((self.height - goal_size)/2 + line_width),
                                                       goal_size/2 - line_width*3,goal_size - line_width*3),border_radius=round((goal_size - line_width*2)/2))
        pygame.draw.rect(self.rink_surface, self.RED,(goal_line_indent + line_width - round(goal_size/2), #Goal1
                                                       round((self.height - goal_size)/2 + goal_size/5),
                                                       goal_size/2,line_width))
        pygame.draw.rect(self.rink_surface, self.RED,(goal_line_indent + line_width - round(goal_size/2), #Goal1
                                                       round((self.height + goal_size)/2 - goal_size/5 - line_width),
                                                       goal_size/2,line_width))
        
        pygame.draw.rect(self.rink_surface, self.RED,(self.width - goal_line_indent - line_width, #Goal2
                                                       round((self.height - goal_size)/2),
                                                       goal_size/2,goal_size),border_radius=round(goal_size/2))
        pygame.draw.rect(self.rink_surface, self.WHITE,(self.width - goal_line_indent, 
                                                       round((self.height - goal_size)/2 + line_width),
                                                       goal_size/2 - line_width*3,goal_size - line_width*3),border_radius=round((goal_size - line_width*2)/2))
        pygame.draw.rect(self.rink_surface, self.RED,(self.width - goal_line_indent - line_width, #Goal1
                                                       round((self.height - goal_size)/2 + goal_size/5),
                                                       goal_size/2,line_width))
        pygame.draw.rect(self.rink_surface, self.RED,(self.width - goal_line_indent - line_width, #Goal1
                                                       round((self.height + goal_size)/2 - goal_size/5 - line_width),
                                                       goal_size/2,line_width))

        pygame.draw.rect(self.rink_surface, self.BLUE, (blue_line_indent,0,blue_line_width,self.height)) #Blue lines
        pygame.draw.rect(self.rink_surface, self.BLUE, (self.width - blue_line_indent - line_width,0,blue_line_width,self.height))

        pygame.draw.rect(self.rink_surface, self.RED, (center_line_indent-center_line_width/2,0,center_line_width,self.height)) #Blue lines
        
        pygame.draw.circle(self.rink_surface, self.BLUE, ( self.width/2, self.height/2), center_circle_diameter) #Center circle
        pygame.draw.circle(self.rink_surface, self.WHITE, ( self.width/2, self.height/2), center_circle_diameter - line_width) #
        pygame.draw.circle(self.rink_surface, self.BLUE, ( self.width/2, self.height/2), round(center_circle_diameter/10)) #

        pygame.draw.circle(self.rink_surface, self.RED, (faceoff_x,faceoff_y), faceoff_circle_diameter) #faceoff_circle
        pygame.draw.circle(self.rink_surface, self.WHITE, (faceoff_x,faceoff_y), faceoff_circle_diameter - line_width) #
        pygame.draw.circle(self.rink_surface, self.RED, (faceoff_x,faceoff_y), round(faceoff_circle_diameter/10)) #

        pygame.draw.circle(self.rink_surface, self.RED, (faceoff_x,self.height -faceoff_y), faceoff_circle_diameter) #faceoff_circle
        pygame.draw.circle(self.rink_surface, self.WHITE, (faceoff_x,self.height - faceoff_y), faceoff_circle_diameter - line_width) #
        pygame.draw.circle(self.rink_surface, self.RED, (faceoff_x,self.height -faceoff_y), round(faceoff_circle_diameter/10)) #

        pygame.draw.circle(self.rink_surface, self.RED, (self.width - faceoff_x,faceoff_y), faceoff_circle_diameter) #faceoff_circle
        pygame.draw.circle(self.rink_surface, self.WHITE, (self.width - faceoff_x,faceoff_y), faceoff_circle_diameter - line_width) #
        pygame.draw.circle(self.rink_surface, self.RED, (self.width - faceoff_x,faceoff_y), round(faceoff_circle_diameter/10)) #

        pygame.draw.circle(self.rink_surface, self.RED, (self.width - faceoff_x,self.height -faceoff_y), faceoff_circle_diameter) #faceoff_circle
        pygame.draw.circle(self.rink_surface, self.WHITE, (self.width - faceoff_x,self.height - faceoff_y), faceoff_circle_diameter - line_width) #
        pygame.draw.circle(self.rink_surface, self.RED, (self.width - faceoff_x,self.height -faceoff_y), round(faceoff_circle_diameter/10)) #
        '''


        pygame.draw.circle(self.rink_surface, self.RED, (190,100), 55) #Face-off circles
        pygame.draw.circle(self.rink_surface, self.WHITE, (190,100), 52)
        pygame.draw.circle(self.rink_surface, self.BLUE, (190,100), 5)

        pygame.draw.circle(self.rink_surface, self.RED, (190,300), 55)
        pygame.draw.circle(self.rink_surface, self.WHITE, (190,300), 52)
        pygame.draw.circle(self.rink_surface, self.BLUE, (190,300), 5)

        pygame.draw.circle(self.rink_surface, self.RED, (610,100), 55)
        pygame.draw.circle(self.rink_surface, self.WHITE, (610,100), 52)
        pygame.draw.circle(self.rink_surface, self.BLUE, (610,100), 5)
 
        pygame.draw.circle(self.rink_surface, self.RED, (610,300), 55)
        pygame.draw.circle(self.rink_surface, self.WHITE, (610,300), 52)
        pygame.draw.circle(self.rink_surface, self.BLUE, (610,300), 5)
        '''

    def draw_elements(self,outline):

        for element in outline['elements']:
            color = (0,255,0)


            if element['type'] == 'Port':
                element_rect = pygame.Rect(0, 0, element['shape']['width'], element['shape']['height'])
                #rotated_rect.center = ((i + 1) * width // 4, height // 2)
                element_surface = pygame.Surface((element['shape']['width'], element['shape']['height']), pygame.SRCALPHA)
                pygame.draw.rect(element_surface, color, (0, 0,element['shape']['width'],element['shape']['height']))
                element_surface = pygame.transform.rotate(element_surface,element['rotation'])
            elif element['type'] == 'Triangle':
                element_surface = pygame.Surface((element['shape']['width'],element['shape']['width']), pygame.SRCALPHA)
                h = element['shape']['width'] * math.sin(math.pi/3)
                pygame.draw.polygon(element_surface, color, ((0,element['shape']['width']),
                                    (element['shape']['width']/2,element['shape']['width']-h),
                                    (element['shape']['width'],element['shape']['width'])))

                element_surface = pygame.transform.rotate(element_surface,element['rotation'])
            
            elif element['type'] == 'LongStraight':
                element_surface = pygame.Surface(((element['shape']['width']+2)*element['count'],element['shape']['width']), pygame.SRCALPHA)
                for i in range(element['count']):
                    pygame.draw.rect(element_surface, color, ((element['shape']['width']+2)*i, 0,element['shape']['width'],element['shape']['height']))
                
                element_surface = pygame.transform.rotate(element_surface,element['rotation'])
            elif element['type'] == 'Zigzag':
                element_surface = pygame.Surface((element['shape']['width']*element['count'],element['shape']['width']*2), pygame.SRCALPHA)
                sub_surface = pygame.Surface((element['shape']['width'],element['shape']['height']), pygame.SRCALPHA)
                pygame.draw.rect(sub_surface, color, (0,0,element['shape']['width'],element['shape']['height']))
                sub_surface = pygame.transform.rotate(sub_surface,30)
                for i in range(element['count']):
                    sub1_surface = pygame.transform.rotate(sub_surface,-60*(i % 2))
                    element_surface.blit(sub1_surface,(round(element_surface.get_width()/element['count']*i),round(element_surface.get_height()/2)))

                element_surface = pygame.transform.rotate(element_surface,element['rotation'])

            
            self.elem_surface.blit(element_surface,(element['x'],element['y']))


def set_element(self,element):
    pass

def unset_element(self,element):
    pass


if __name__ == "__main__":

    # Initialize Pygame
    pygame.init()

    # Set up the window
    WINDOW_SIZE = (1000, 600)
    window = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Hockey Rink")
    rink = Rink()
    rink.draw_rink()
    print("rink created")
    window.fill((0,0,255))

    with open('exercises_test.json', 'r') as f:
        exer_dict = json.load(f)


    outline = exer_dict["exerciseList"][-1]['outline']

    rink.draw_elements(outline)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        window.fill((0,0,255))
            

        window.blit(rink.rink_surface,(0,0))
        window.blit(rink.elem_surface,(0,0))
        pygame.display.flip()