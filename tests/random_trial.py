import gym
import gym_sdwan

MAX_TICKS = 100
total_reward = 0

env = gym.make('Sdwan-v0')

observation = env.reset()

print('Initial State:', observation)

for t in range (MAX_TICKS):
	action = env.action_space.sample()
	observation, reward, done, info = env.step(action)
	total_reward += reward
	print('Action:', action, 'Ob:', observation, 'R:', reward, 'Total Reward:', total_reward)

	if done:
		print("Episode finished after {} timesteps".format(t+1))
		break


env.cleanup()
