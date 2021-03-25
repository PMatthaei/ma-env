import unittest

import numpy as np

from multiagent.ai.basic_ai import BasicScriptedAI
from test.mock import mock_agent, mock_team, mock_world

AGENTS_N = 4


class BasicAgentActTestCases(unittest.TestCase):
    def setUp(self):
        self.a = mock_agent(id=0, tid=0)
        self.b = mock_agent(id=1, tid=0)
        self.c = mock_agent(id=2, tid=1)
        self.d = mock_agent(id=3, tid=1)
        self.at = mock_team(0, members=[self.a, self.b])
        self.bt = mock_team(1, members=[self.c, self.d])
        self.world = mock_world(AGENTS_N, teams=[self.at, self.bt])
        self.world.positions = np.array([[0, 0], [0, 10], [0, 20], [0, 30]], dtype=np.float)
        self.world.distances = np.array([[0, 3, 2, 1], [3, 0, 2, 1], [3, 2, 0, 1], [1, 1, 1, 0]], dtype=np.float)
        self.ai = BasicScriptedAI()

    def test_a_should_attack_d(self):
        result = self.ai.act(self.a, self.world)
        np.testing.assert_array_equal(result.u, [0, 0, self.d.id])

    def test_b_should_attack_d(self):
        result = self.ai.act(self.b, self.world)
        np.testing.assert_array_equal(result.u, [0, 0, self.d.id])

    def test_c_should_attack_a(self):
        result = self.ai.act(self.c, self.world)
        np.testing.assert_array_equal(result.u, [0, 0, self.b.id])

    def test_d_should_attack_a(self):
        result = self.ai.act(self.d, self.world)
        np.testing.assert_array_equal(result.u, [0, 0, self.a.id])

    def test_d_should_move_down_towards_b(self):
        # A and B are out of range -> no direct targeting -> -1
        # But B is closer (3 < 4) -> move to B
        self.world.distances = np.array([[0, 3, 2, 1], [3, 0, 2, 1], [2, 2, 0, 1], [4, 3, 1, 0]], dtype=np.float)
        result = self.ai.act(self.d, self.world)
        # Should move down to reach B -> B - D = (0,10) - (0,30) = (0,-20) -> move down by -10 (grid step)
        np.testing.assert_array_equal(result.u, [0, -10, -1])

    def test_a_should_move_up_towards_d(self):
        # A and B are out of range -> no direct targeting -> -1
        # But B is closer (3 < 4) -> move to B
        self.world.distances = np.array([[0, 1, 3, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], dtype=np.float)
        result = self.ai.act(self.a, self.world)
        # Should move up to reach C -> D - A = (0, 20) - (0, 0) = (0,20) -> move up by 10 (grid step)
        np.testing.assert_array_equal(result.u, [0, 10, -1])
