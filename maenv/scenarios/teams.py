import numpy as np

from maenv.ai import BasicScriptedAI
from maenv.interfaces.ai import ScriptedAI
from maenv.core import World, Agent, Team, Action
from maenv.exceptions.scenario_exceptions import ScenarioNotSymmetricError
from maenv.interfaces.scenario import BaseTeamScenario
from maenv.utils.colors import generate_colors


class TeamsScenario(BaseTeamScenario):
    def __init__(self, match_build_plan, scripted_ai: ScriptedAI = BasicScriptedAI()):
        """
        Constructor for a team scenario.
        @param match_build_plan: Plan to setup the match and therefore team composition and possible AI`s.
        n_agents: How many agents per team
        n_teams: How many teams
        """
        self.match_build_plan = match_build_plan
        self.teams_n = len(match_build_plan)
        self.agents_n = [len(team["units"]) for team in match_build_plan]
        self.is_symmetric = self.agents_n.count(self.agents_n[0]) == len(self.agents_n)
        self.team_mixing_factor = 8  # build_plan["tmf"] if "tmf" in build_plan["tmf"] else 5
        self.scripted_ai = scripted_ai
        if not self.is_symmetric:
            raise ScenarioNotSymmetricError(self.agents_n, self.teams_n)

        self.team_spawns = None
        if "agent_spawns" in self.match_build_plan:
            self.agent_spawns = self.match_build_plan["agent_spawns"]
        else:
            self.agent_spawns = [None] * self.teams_n

    def _make_world(self, grid_size: int):
        agents_n = sum(self.agents_n)

        world = World(agents_n=agents_n, teams_n=self.teams_n, grid_size=grid_size)

        colors = generate_colors(self.teams_n)
        agent_count = 0
        for tid in range(self.teams_n):
            is_scripted = self.match_build_plan[tid]["is_scripted"]
            members = [
                Agent(
                    id=aid,  # is not reset per team. aid identifying all units globally
                    tid=tid,
                    color=colors[tid],
                    build_plan=self.match_build_plan[tid]["units"][index],
                    action_callback=self.scripted_agent_callback if is_scripted else None
                ) for index, aid in  # index is the team internal identifier
                enumerate(range(agent_count, agent_count + self.agents_n[tid]))
            ]
            agent_count += self.agents_n[tid]
            world.agents += members
            team = Team(tid=tid, members=members, is_scripted=is_scripted)
            world.teams.append(team)

        return world

    def reset_world(self, world: World):

        # How far should team spawns and agents be spread
        agent_spread = world.grid_size * sum(self.agents_n) / self.team_mixing_factor
        team_spread = self.teams_n * agent_spread

        # random team spawns
        if self.team_spawns is None:
            self.team_spawns = world.spg.generate_team_spawns(radius=team_spread, grid_size=world.grid_size)
            # take first teams size since symmetric for spawn generation
            agent_spawns = world.spg.generate(self.agents_n[0], world.grid_size, 1, agent_spread)
            # mirror spawns
            self.agent_spawns[0] = agent_spawns + self.team_spawns[0]
            self.agent_spawns[1] = (- agent_spawns) + self.team_spawns[1]

        # scatter agents of a team a little
        for team, team_spawn in zip(world.teams, self.team_spawns):
            for team_intern_id, agent in enumerate(team.members):
                spawn = self.agent_spawns[team.tid][team_intern_id]
                world.connect(agent, spawn)

    def reward(self, agent: Agent, world: World):
        reward = 0
        # reward += agent.state.health / agent.state.max_health
        # reward -= agent.stats.dmg_received / agent.state.max_health
        reward += agent.stats.dmg_dealt / agent.attack_damage * 0.5
        reward += agent.stats.kills * 5
        return reward

    def done(self, team: Team, world: World):
        if np.all(world.wiped_teams):  # if all teams are wiped simultaneously -> done
            return True
        # if only one team is not wiped and this team is the team under testing -> winner winner chicken dinner
        return not world.wiped_teams[team.tid] and world.wiped_teams.count(False) == 1

    def observation(self, agent: Agent, world: World):
        other_obs = world.obs[agent.id].flatten()
        return np.concatenate((other_obs, agent.self_observation))

    def scripted_agent_callback(self, agent: Agent, world: World) -> Action:
        return self.scripted_ai.act(agent, world)