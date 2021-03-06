import math
import random
from typing import Tuple

import numpy as np


class SpawnGenerator:
    def __init__(self, center, grid_size: int, dim: int, n_agents: int, max_trials=50):
        """
        Generator producing random spawns. In a first step unique random spawns for each team are chosen.
        Based on these team spawn each agent receives a unique spawn.
        @param world_bounds:
        @param grid_size:
        @param max_trials:
        """
        self.world_center = center
        self.grid_size = grid_size
        self.n_agents_per_team = int(n_agents / 2)
        self.used_points = np.full((n_agents, dim), fill_value=np.inf)
        self.team_spawns = []
        self.max_trials = max_trials
        # Generate positions on grid
        self.on_grid = self.grid_size is not None
        if not self.on_grid:
            raise NotImplementedError("Generating spawns outside of the world grid (continuous) is not yet implemented")
        self.trials = 0

    def generate_team_spawns(self, radius, randomize: bool = False, buffer: int = 2):
        """
        Generate team spawns on a circle with the provided radius around the world center.
        Teams spawn on the opposite site of the circle resulting in a distance of radius * 2.
        Team spawns are always real numbered.
        @param radius: defined circle on which team spawns are generated
        @return:
        """
        if not randomize:
            w, h = self._get_team_box(self.n_agents_per_team)
            gs = self.grid_size
            c = self.world_center
            team_width_displacement = (w + buffer) * gs
            self.team_spawns = [c + [team_width_displacement, 0], c - [team_width_displacement, 0]]
            return self.team_spawns
        else:
            cx, cy = np.array(self.world_center)
            theta = random.uniform(0, 2 * math.pi)
            x1 = cx + radius * math.cos(theta)
            y1 = cy + radius * math.sin(theta)
            x2 = cx - radius * math.cos(theta)
            y2 = cy - radius * math.sin(theta)
            point1 = np.array([x1, y1])
            point2 = np.array([x2, y2])
            point1 -= (point1 % self.grid_size)
            point2 -= (point2 % self.grid_size)
            self.team_spawns = [point1, point2]
            return np.array(self.team_spawns)

    def generate(self, randomize: bool = False, mean_radius=1.0, sigma_radius=0.1):
        if not randomize:
            w, h = self._get_team_box(self.n_agents_per_team)
            gs = self.grid_size
            box_width_displacements = np.array(range(w)) * gs
            box_height_displacements = np.array(range(h)) * gs
            return np.array(np.meshgrid(box_width_displacements, box_height_displacements)).T.reshape(-1, 2)
        else:
            points = []

            for i in range(self.n_agents_per_team):
                point = self._generate_point(mean_radius, sigma_radius, grid_size=self.grid_size)
                used = np.all(self.used_points[:, [0, 1]] == point, axis=1)
                while np.any(used):  # Try generating new point if already used
                    if self.trials >= self.max_trials:
                        raise Exception("Maximum trials per point reached. Try generating with more variance allowed.")
                    point = self._generate_point(mean_radius, sigma_radius, grid_size=self.grid_size)
                    used = np.all(self.used_points[:, [0, 1]] == point, axis=1)
                    self.trials += 1
                self.used_points[i] = point
                self.trials = 0
                points.append(point)

            return np.array(points)

    def _generate_point(self, mean_radius: float, sigma_radius: float, grid_size: int = None):
        """
        Generates a point around the center with a mean radius.
        @param center:
        @param grid_size:
        @param mean_radius:
        @param sigma_radius:
        @return:
        """
        theta = random.uniform(0, 2 * math.pi)
        radius = random.gauss(mean_radius, sigma_radius)  # noise
        point = radius * np.array([math.cos(theta), math.sin(theta)])
        if grid_size is not None:  # Move points onto grid
            point -= (point % grid_size)
        return point

    def clear(self):
        self.used_points = None

    def _get_team_box(self, n)-> Tuple[int,int]:
        """
        @param n: number of agents
        @return: Return tuple which spawns a square which will hold all n agents positionally
        """
        sqrt_n = math.sqrt(n)
        if n % sqrt_n == 0:
            return int(sqrt_n), int(sqrt_n)
        if n % 2 == 1:
            n += 1
        i = int(n ** 0.5 + 0.5)
        while n % i != 0:
            i -= 1
        return i, int(n / i)
