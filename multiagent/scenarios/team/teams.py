import numpy as np

from multiagent.ai.basic_ai import BasicScriptedAI
from multiagent.core import World, Agent, Team, Action
from multiagent.exceptions.scenario_exceptions import ScenarioNotSymmetricError
from multiagent.interfaces.scenario import BaseTeamScenario
from multiagent.utils.colors import generate_colors
from multiagent.utils.spawn_generator import generate_spawns


class TeamsScenario(BaseTeamScenario):
    def __init__(self, build_plan):
        """
        Constructor for a team scenario.
        @param build_plan: Team setup supplied as needed
        n_agents: How many agents per team
        n_teams: How many teams
        """
        self.team_build_plan = build_plan
        self.n_teams = len(build_plan)
        self.n_agents = [len(team["units"]) for team in build_plan]
        self.is_symmetric = build_plan.count(build_plan[0]) == len(build_plan)

        self.scripted_ai = BasicScriptedAI()

        if self.is_symmetric and sum(self.n_agents) % self.n_teams != 0:
            raise ScenarioNotSymmetricError(self.n_agents, self.n_teams)

        self.team_spawns = None
        self.agent_spawns = [None] * self.n_teams

    def _make_world(self, grid_size: int):
        world = World(grid_size=grid_size)
        world.collaborative = True
        colors = generate_colors(self.n_teams)
        agent_count = 0
        for tid in range(self.n_teams):
            is_scripted = self.team_build_plan[tid]["is_scripted"]
            members = [
                Agent(
                    id=aid,  # is not reset per team. aid identifying all units globally
                    tid=tid,
                    color=colors[tid],
                    build_plan=self.team_build_plan[tid]["units"][index],
                    action_callback=self.scripted_agent_callback if is_scripted else None
                ) for index, aid in  # index is the team internal identifier
                enumerate(range(agent_count, agent_count + self.n_agents[tid]))
            ]
            agent_count += self.n_agents[tid]
            world.agents += members
            team = Team(tid=tid, members=members, is_scripted=is_scripted)
            world.teams.append(team)

        return world

    def reset_world(self, world: World):
        # random team spawns
        if self.team_spawns is None:
            self.team_spawns = generate_spawns(*world.grid_center, self.n_teams, mean_radius=world.grid_size * 3)
        # scatter agents of a team a little
        for team, team_spawn in zip(world.teams, self.team_spawns):
            if self.agent_spawns[team.tid] is None:
                self.agent_spawns[team.tid] = generate_spawns(*team_spawn, self.n_agents[team.tid], mean_radius=world.grid_size)
            for i, agent in enumerate(team.members):
                agent.state.reset(np.array(self.agent_spawns[team.tid][i]))

    def reward(self, agent: Agent, world: World):
        reward = 0
        # reward += agent.state.health / agent.state.max_health
        # reward -= agent.stats.dmg_received / agent.state.max_health
        reward += agent.stats.dmg_dealt
        reward += agent.stats.kills * 20
        return reward

    def done(self, team: Team, world: World):
        # if only one team is not wiped and this team is the team under testing -> winner winner chicken dinner
        return not team.is_wiped() and world.teams_wiped.count(False) == 1

    def observation(self, agent: Agent, world: World):
        # Movement observation of the agent
        obs = [world.get_available_movement(agent)]
        # Ally observations
        obs += [world.get_obs_of(agent, member) for member in world.get_team_members(agent)]
        # Enemy observations
        obs += [world.get_obs_of(agent, enemy) for enemy in world.get_enemies(agent)]
        # Self observation
        obs.append(agent.self_observation)
        # Flatten
        obs = np.concatenate(obs).astype(float)
        return obs

    def scripted_agent_callback(self, agent: Agent, world: World) -> Action:
        return self.scripted_ai.act(agent, world)
