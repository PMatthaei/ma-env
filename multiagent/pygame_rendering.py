import math
import os

import subprocess as sp
import pygame
from pygame.rect import Rect

from multiagent.core import Entity
from multiagent.utils.colors import hsl_to_rgb


def check_ffmpeg():
    ffmpeg_available = True
    print('Check if ffmpeg is installed...')
    try:
        print(sp.check_output(['which', 'ffmpeg']))
    except Exception as e:
        print(e)
        ffmpeg_available = False
    if not ffmpeg_available:
        print("Could not find ffmpeg. Please run 'sudo apt-get install ffmpeg'.")
    else:
        print('ffmpeg is installed.')

    return ffmpeg_available


class Grid:
    def __init__(self, screen, cell_size):
        self.screen = screen
        self.surface = screen.convert_alpha()
        self.surface.fill([0, 0, 0, 0])
        self.col_n = math.ceil(screen.get_width() / cell_size)
        self.line_n = math.ceil(screen.get_height() / cell_size)
        self.cell_size = cell_size
        self.grid = [[0 for i in range(self.col_n)] for j in range(self.line_n)]

    def draw_use_line(self):
        for li in range(self.line_n):
            li_coord = li * self.cell_size
            pygame.draw.line(self.surface, (0, 0, 0, 50), (0, li_coord), (self.surface.get_width(), li_coord))
        for co in range(self.col_n):
            colCoord = co * self.cell_size
            pygame.draw.line(self.surface, (0, 0, 0, 50), (colCoord, 0), (colCoord, self.surface.get_height()))

        self.screen.blit(self.surface, (0, 0))


class PyGameViewer(object):
    def __init__(self, env, caption="Multi-Agent Environment", fps=30, infos=True, draw_grid=True, record=True,
                 headless=False):
        """
        Create new PyGameViewer for the environment
        :param env: MultiAgentEnv to render
        :param caption: Caption of the window
        :param fps: Frames per second
        :param infos: Show additional information about performance and current game state.
        :param draw_grid: Draw underlying movement grid induced by step size
        :param record: Activate recording
        :param headless: Make rendering headless (no window)
        """
        self.env = env
        self.entities = None
        self.draw_grid = draw_grid
        self.record = record
        self.proc = None
        self.fps = 30
        self.headless = headless

        if self.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        # Skip audio module since it is not used and produced errors with ALSA lib on ubuntu
        pygame.display.init()
        pygame.font.init()
        self.font = pygame.font.SysFont('', 25)

        self.screen = pygame.display.set_mode(self.env.world.bounds)
        if self.draw_grid:
            self.grid = Grid(screen=self.screen, cell_size=int(self.env.world.grid_size))

        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.fps = fps
        self.infos = infos
        self.clear()

        width, height = self.env.world.bounds

        if self.record and check_ffmpeg():
            self.proc = sp.Popen(['ffmpeg',
                                  '-y',
                                  '-f', 'rawvideo',
                                  '-vcodec', 'rawvideo',
                                  '-s', str(width) + 'x' + str(height),
                                  '-pix_fmt', 'rgba',
                                  '-r', str(self.fps),
                                  '-i', '-',
                                  '-an',
                                  'env-recording.mov'], stdin=sp.PIPE)
        pass

    def update(self):
        """
        Update data. This does not update visuals
        :param t:
        :param episode:
        :return:
        """

        if self.infos:
            dt = self.font.render("FPS: " + str(self.fps), False, (0, 0, 0))
            t = self.font.render("Time step: " + str(self.env.t), False, (0, 0, 0))
            episode = self.font.render("Episode: " + str(self.env.episode), False, (0, 0, 0))
            max_step = self.font.render("Max. Step: " + str(self.env.max_steps), False, (0, 0, 0))
            self.screen.blit(dt, (0, 0))
            self.screen.blit(t, (0, 20))
            self.screen.blit(episode, (0, 40))
            self.screen.blit(max_step, (0, 60))

        if self.draw_grid:
            self.grid.draw_use_line()

        # update entity positions visually
        for entity in self.entities:
            entity.update()
            self.screen.blit(entity.surf, entity.rect)

    def init(self, world_entities):
        """
        Initialize viewer with its rendered entities, created from their counterparts in the environment data.
        :param world_entities:
        :return:
        """
        self.entities = pygame.sprite.Group()
        self.entities.add(*[PyGameEntity(entity) for entity in world_entities])

    def render(self):
        """
        Render current data and handle events
        :return:
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.flip()

        if self.record:
            self.proc.stdin.write(self.screen.get_buffer())

        self.dt = self.clock.tick(self.fps)

    def reset(self):
        """
        Reset the visuals to default
        :return:
        """
        self.entities = None
        self.clear()

    def clear(self):
        """
        Clear screen. Usually called to clear screen for next frame.
        :return:
        """
        self.screen.fill((255, 255, 255))

    def close(self):
        pygame.quit()
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc.wait()


class PyGameEntity(pygame.sprite.Sprite):
    def __init__(self, entity: Entity):
        super(PyGameEntity, self).__init__()
        # This reference is updated in world step
        self.entity = entity
        radius = entity.sight_range
        # This is its visual representation
        self.surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA, 32).convert_alpha()
        self.rect: Rect = self.surf.get_rect()
        # Move to initial position
        self.update()

    def update(self):
        # Draw entity as dot. A outline circle indicates its action range. Alpha colors indicate death
        alpha = 80 if self.entity.is_dead() else 255
        color = self.entity.color
        sight_range = self.entity.sight_range
        attack_range = self.entity.attack_range
        body_radius = self.entity.bounding_circle_radius
        pygame.draw.circle(self.surf, color=hsl_to_rgb(color, alpha), center=(sight_range, sight_range), radius=body_radius)
        pygame.draw.circle(self.surf, color=hsl_to_rgb(color, alpha), center=(sight_range, sight_range), radius=sight_range, width=1)
        pygame.draw.circle(self.surf, color=hsl_to_rgb(color, alpha), center=(sight_range, sight_range), radius=attack_range, width=1)
        # Core is updating with a move_by update while here we set the resulted new pos
        # TODO: if move_by needed the update needs to be saved in entity so we can recreate it here visually
        self.rect.centerx = self.entity.state.p_pos[0]
        self.rect.centery = self.entity.state.p_pos[1]