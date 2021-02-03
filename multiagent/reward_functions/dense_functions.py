import numpy as np

from multiagent.core import Entity, Agent, Team

KILL_REWARD = 20
ASSIST_REWARD = 5


def reward_team_stats(team: Team):
    return sum([reward_agent_stats(agent) for agent in team.members])


def reward_agent_stats(agent: Agent):
    # TODO: normalize all rewards below -> set max reward
    reward = 0
    stats = agent.stats
    reward += stats.kills * KILL_REWARD
    reward += stats.assists * ASSIST_REWARD
    reward += stats.dmg_dealt
    reward += stats.dmg_healed
    reward += stats.heals_performed
    reward += stats.attacks_performed
    return reward


def reward_team_health(team: Team):
    return sum([reward_agent_health(agent) for agent in team.members])


def reward_agent_health(agent: Agent):
    return agent.state.health / agent.state.max_health


def reward_distance(agent: Agent, other: Entity):
    return np.linalg.norm(agent.state.p_pos - other.state.p_pos)