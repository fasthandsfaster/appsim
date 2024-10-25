
import pygame
import json

class HeadsUp:
# Initialize Pygame
    def __init__(self):
        self.height = 650
        self.width = 1050
        self.surface = pygame.Surface((self.width,self.height), pygame.SRCALPHA)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 0, 255)
        self.RED = (255,0,0)

    def create_layout(self,layout):
        # Colors
        red = (255, 0, 0)
        blue = (0, 0, 255)
        green = (0, 255, 0)

        # Draw a rectangle
        tmp_surface = pygame.Surface((1050,650), pygame.SRCALPHA)
        
        pygame.draw.rect(tmp_surface, red, (50, 50, 100, 80))

        # Draw a triangle
        triangle_points = [(200, 50), (250, 150), (150, 150)]
        pygame.draw.polygon(tmp_surface, red, triangle_points)

        tmp1_surface = pygame.Surface((tmp_surface.get_bounding_rect(1).width,tmp_surface.get_bounding_rect(1).height), pygame.SRCALPHA)
        
        pygame.draw.rect(tmp1_surface, red, (0,0, 100, 80))

        # Draw a triangle
        triangle_points = [(150,0), (200, 100), (1100, 100)]
        pygame.draw.polygon(tmp1_surface, blue, triangle_points)
        
        self.surface.blit(tmp1_surface,tmp1_surface.get_rect(center=self.surface.get_rect().center))


if __name__ == "__main__":

    # Initialize Pygame
    pygame.init()

    # Set up the window
    WINDOW_SIZE = (1100, 700)
    window = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Heads up")
    heads_up = HeadsUp()

    window.fill((255,255,255))

    with open('exercises_test.json', 'r') as f:
        exer_dict = json.load(f)


    outline = exer_dict["exerciseList"][-1]['outline']

    heads_up.create_layout(outline)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        window.fill((0,0,255))
            

        window.blit(heads_up.surface,(0,0))
        pygame.display.flip()