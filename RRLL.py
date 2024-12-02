import gym
from gym import spaces
import numpy as np
from stable_baselines3 import PPO
import matplotlib.pyplot as plt



class CustomEnv(gym.Env):
    def __init__(self):
        super(CustomEnv, self).__init__()

        self.x_increment_bins = np.linspace(-0.2, 0.2, 21)
        self.action_space = spaces.MultiDiscrete(
            [21, 2, 2, 2]
        ) 
        self.observation_space = spaces.Box(low=0, high=2, shape=(4,), dtype=np.float32)
        self.reset()

    def reset(self):
        self.x = 0
        self.y = [False, False, False]
        return self._get_state()

    def step(self, action):
        prev_value = self._calculate_function()

        # 更新 x
        x_increment_idx = action[0]
        self.x += self.x_increment_bins[x_increment_idx]
        self.x = np.clip(self.x, 0, 2)

        # 更新 y
        self.y = [bool(action[i]) for i in range(1, 4)]

        new_value = self._calculate_function()

        # 设置奖励
        if new_value > prev_value:
            reward = -999
        elif new_value < prev_value:
            reward = (1 - new_value) * 10
        else:
            reward = -1

        done = False  # 环境不会自然终止
        return self._get_state(), reward, done, {}

    def _calculate_function(self):
        return (self.x - 1) ** 2 + (0 if all(self.y) else 1)

    def _get_state(self):
        return np.array([self.x] + self.y, dtype=np.float32)



env = CustomEnv()

model = PPO("MlpPolicy", env, verbose=1, device="cuda")

model.learn(total_timesteps=10000)

model.save("ppo_custom_env")

model = PPO.load("ppo_custom_env", device="cuda")

num_episodes = 50
rewards = []

for episode in range(num_episodes):
    state = env.reset()
    done = False
    total_reward = 0
    step_count = 0

    while not done and step_count < max_steps:
        action, _ = model.predict(state)
        state, reward, done, _ = env.step(action)
        total_reward += reward
        step_count += 1

    rewards.append(total_reward)
    print(f"Episode: {episode + 1}, Total Reward: {total_reward}")

plt.figure(figsize=(10, 5))
plt.plot(range(1, num_episodes + 1), rewards)
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Total Reward per Episode")
plt.grid(True)
plt.show()

optimal_value = min(rewards)
optimal_episode = rewards.index(optimal_value) + 1
print("最优值：", optimal_value)
print("最优状态发生在情节：", optimal_episode)
