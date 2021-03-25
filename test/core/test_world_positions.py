import unittest

import numpy as np

from multiagent.core import World
from test.mock import mock_agent

N_AGENTS = 2


class WorldPositionsTestCases(unittest.TestCase):
    def setUp(self):
        self.agent = mock_agent(id=0)
        self.agent2 = mock_agent(id=1, tid=1)
        self.agent_spawn = np.array([1, 1])
        self.agent_spawn2 = np.array([1, 0])

        self.world = World(grid_size=10, teams_n=2, agents_n=N_AGENTS)
        self.world.agents = [self.agent, self.agent2]

        self.world.connect(self.agent, self.agent_spawn)
        self.world.connect(self.agent2, self.agent_spawn2)

    def test_update_pos_if_not_occupied(self):
        self.agent.action.u[:2] = [0, 1]  # move to -> 1,0 -> free
        self.world._update_pos(self.agent)

        np.testing.assert_array_equal(self.world.positions[0], [1, 2])
        np.testing.assert_array_equal(self.agent.state.pos, [1, 2])

    def test_no_update_pos_if_occupied(self):
        self.agent.action.u = [0, -1]  # move to -> 1,0 -> occupied by agent 2
        self.world._update_pos(self.agent)

        np.testing.assert_array_equal(self.world.positions[0], [1, 1])
        np.testing.assert_array_equal(self.agent.state.pos, [1, 1])

    def test_no_update_pos_if_noop(self):
        self.agent.action.u[:2] = [0, 0]  # noop action
        self.world._update_pos(self.agent)

        np.testing.assert_array_equal(self.world.positions[0], [1, 1])
        np.testing.assert_array_equal(self.agent.state.pos, [1, 1])

if __name__ == '__main__':
    unittest.main()
