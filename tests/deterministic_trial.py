import gym
import gym_sdwan

MAX_TICKS = 30
total_reward = 0

env = gym.make('Sdwan-v0')

sla_bw = env.backend.sla_bw

observation = env.reset()

print('Initial State:', observation)

error = False
for t in range (MAX_TICKS):
	
	link_id = observation[0]
	current_bw = observation[1]
	available_bw = observation[2]

	if float(available_bw) > float(sla_bw):
		action = 0 # try  INTERNET link
	else: 
		action = 1 # try MPLS  link

	observation, reward, error, info = env.step(action)
	total_reward += reward
	print('Ticks:', t+1, 'Action:', action, 'Ob:', observation, 
				'R:', reward, 'Total Reward:', total_reward)

	if error:
		print("Episode Aborted after {} timesteps".format(t+1))
		break

if not error:
	print("Episode finished after {} timesteps".format(t+1))


env.cleanup()
