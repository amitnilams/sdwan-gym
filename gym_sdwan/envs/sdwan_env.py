#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simulate the Sdwan channel selection  environment.

Each episode is sending data until bandwidth falls below SLA level 
"""

# core modules
import logging.config
import math
import pkg_resources
import random

# 3rd party modules
from gym import spaces
import cfg_load
import gym
import numpy as np

from mininet_backend import MininetBackEnd


path = 'config.yaml'  # always use slash in packages
filepath = pkg_resources.resource_filename('gym_sdwan', path)
config = cfg_load.load(filepath)
logging.config.dictConfig(config['LOGGING'])


class SdwanEnv(gym.Env):
    """
    Define Sdwan environment.

    The environment defines  how links will be selected based on bandwidth
    availability 
    """

    def __init__(self):
        self.__version__ = "0.1.0"
        logging.info("SdwanEnv - Version {}".format(self.__version__))

        # General variables defining the environment

        self.LINK_BW = 10.0
        self.LINK_SELECT_ACTION_INTERNET = 0
        self.LINK_SELECT_ACTION_MPLS = 1

        self.backend = MininetBackEnd(mu=5, sigma=2, link_bw=self.LINK_BW, sla_bw=6, seed=100)

        # Define what the agent can do
        # Choose link1 or Link2 
        self.action_space = spaces.Discrete(2)

        # Observation 

        low = np.array([0.0,  # active link
                        0.0,  #current_bw
                        0.0,  #available bw
                        ])
        high = np.array([self.LINK_SELECT_ACTION_MPLS, self.LINK_BW, self.LINK_BW])

        self.observation_space = spaces.Box(low, high, dtype=np.float32)

			  # episode over 
        self.episode_over = False

        # Store what the agent tried
        self.curr_episode = -1
        self.action_episode_memory = []





    def step(self, action):
        """
        The agent takes a step in the environment.

        Parameters
        ----------
        action : int

        Returns
        -------
        ob, reward, episode_over, info : tuple
            ob (object) :
                an environment-specific object representing your observation of
                the environment.
            reward (float) :
                amount of reward achieved by the previous action. The scale
                varies between environments, but the goal is always to increase
                your total reward.
            episode_over (bool) :
                whether it's time to reset the environment again. Most (but not
                all) tasks are divided up into well-defined episodes, and done
                being True indicates the episode has terminated. (For example,
                perhaps the pole tipped too far, or you lost your last life.)
            info (dict) :
                 diagnostic information useful for debugging. It can sometimes
                 be useful for learning (for example, it might contain the raw
                 probabilities behind the environment's last state change).
                 However, official evaluations of your agent are not allowed to
                 use this for learning.
        """
        self.take_action(action)
        reward = self.get_reward()
        ob = self.get_state()
        return ob, reward, self.episode_over, {}

    def take_action(self, action):
			  self.episode_over = self.backend.switch_link(action)

    def get_reward(self):
				logging.info('current bw:{0}, sla bw:{1}'.format(self.backend.current_bw, 
														self.backend.sla_bw))
				# reward for surviving this 'tick'
				reward = 1

				# every time we use the MPLS link reward is deducted
				if self.backend.active_link == 1:
					reward -= 1

				# check bandwidth for internet link - if less than SLA then penalize
				elif float(self.backend.current_bw)  <   float(self.backend.sla_bw):
					logging.info('BW is less than SLA')
					reward -= 2

				# everything fine - reward up
				else:
					reward += 1

				return reward
				

    def reset(self):
        """
        Reset the state of the environment and returns an initial observation.

        Returns
        -------
        observation (object): the initial observation of the space.
        """
        self.curr_episode += 1
        self.action_episode_memory.append([])
        return self.get_state()

    def render(self, mode='human', close=False):
        return

    def get_state(self):
        """Get the observation.  it is a tuple """
        ob = (self.backend.active_link, self.backend.current_bw,  self.backend.available_bw)
        return ob

    def seed(self, seed):
        random.seed(seed)
        np.random.seed


    def cleanup(self):
        self.backend.cleanup()


