import unittest

import numpy as np

from multiagent.core import World
from test.mock import mock_agent

N_AGENTS = 2


class WorldInitializationTestCases(unittest.TestCase):
    def setUp(self):
        self.agent = mock_agent(id=0)
        self.agent2 = mock_agent(id=1, tid=1)
        self.agent_spawn = np.array([1, 1])

        self.world = World(grid_size=10, teams_n=2, agents_n=N_AGENTS)
        self.world.agents = [self.agent, self.agent2]

    def test_occupied_position_matrix_init(self):
        oc_shape = self.world.positions.shape
        self.assertEqual(oc_shape, (N_AGENTS, self.world.dim_p))

    def test_distance_matrix_init(self):
        ds_shape = self.world.distances.shape
        self.assertEqual(ds_shape, (N_AGENTS, N_AGENTS))

    def test_visibility_matrix_init(self):
        vs_shape = self.world.visibility.shape
        self.assertEqual(vs_shape, (N_AGENTS, N_AGENTS))


if __name__ == '__main__':
    unittest.main()
