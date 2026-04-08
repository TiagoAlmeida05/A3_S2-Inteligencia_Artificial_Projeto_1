import pygame
import sys

class Visualizer:
    def __init__ (self, width = 800, height = 800, rows = 10, cols = 10 ):
        pygame.init()

        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("City Grid")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)

    def render(self, state):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.screen.fill((30, 30, 30))

        self.rows = state.get("rows", self.rows)
        self.cols = state.get("cols", self.cols)

        cell_w = self.width / self.cols
        cell_h = self.height / self.rows

        for r in range(self.rows):
            y = r * cell_h + cell_h/2
            pygame.draw.line(self.screen, (70, 70, 70), (0, y), (self.width, y), 1)
        for c in range(self.cols):
            x = c * cell_w + cell_w/2
            pygame.draw.line(self.screen, (70, 70, 70), (x, 0), (x, self.height), 1)

        for ride in state.get("unassigned_rides", []):
            start_pos = (ride["start_c"] * cell_w + cell_w/2, ride["start_r"]* cell_h +cell_h/2)
            end_pos = (ride["end_c"] * cell_w + cell_w/2, ride["end_r"] * cell_h + cell_h/2)

            pygame.draw.line(self.screen, (200, 200, 50), start_pos, end_pos, 2)
            pygame.draw.circle(self.screen, (50, 255, 50), start_pos, 6)
            pygame.draw.circle(self.screen, (255, 50, 50), end_pos, 6)

        for car in state.get("vehicles", []):
            car_pos = (car["c"] * cell_w + cell_w/2, car["r"] * cell_h + cell_h/2)
            pygame.draw.circle(self.screen, car["color"], car_pos, min(cell_w, cell_h)/3)

        current_step = state.get("current_step", 0)
        score = state.get("score", 0)

        step_text = self.font.render(f"Time Step: {current_step}", True, (255, 255, 255))
        score_text = self.font.render(f"Score: {score}", True, (255, 255, 255))

        self.screen.blit(step_text, (10, 10))
        self.screen.blit(score_text, (10, 40))

        pygame.display.flip()
        self.clock.tick(60)