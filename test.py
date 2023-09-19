import copy
import importlib
import os

import models
import self_play
import torch

from muzero import load_model_menu, MuZero

# check with the cuda device
#
# print(torch.cuda.is_available())
# print(torch.cuda.current_device())
#
# # 获取GPU设备的数量
# num_devices = torch.cuda.device_count()
#
# # 生成GPU设备的索引列表
# device_indices = list(range(num_devices))
#
# print("所有可用的GPU设备索引：", device_indices)

checkpoint = {
    "weights": None,
    "optimizer_state": None,
    "total_reward": 0,
    "muzero_reward": 0,
    "opponent_reward": 0,
    "episode_length": 0,
    "mean_value": 0,
    "training_step": 0,
    "lr": 0,
    "total_loss": 0,
    "value_loss": 0,
    "reward_loss": 0,
    "policy_loss": 0,
    "num_played_games": 0,
    "num_played_steps": 0,
    "num_reanalysed_games": 0,
    "terminate": False,
}
game_module = importlib.import_module("games.pacman")
Game = game_module.Game
config = game_module.MuZeroConfig()

model = models.MuZeroNetwork(config).to('cpu')
weigths = model.get_weights()
checkpoint["weights"] = copy.deepcopy(weigths)

# muzero = MuZero("pacman")
# load_model_menu(muzero, "pacman")
# model = models.MuZeroNetwork(config)
# absolute_path = os.path.abspath("./model.checkpoint")
# checkpoint["weights"] = torch.load(absolute_path)["weights"]

sp = self_play.SelfPlay(checkpoint, Game, config, 90054)
while True:
    game_history = sp.play_game(0, 0,True, "self", 0)
    muzero_reward = sum(
        reward
        for i, reward in enumerate(game_history.reward_history)
        if game_history.to_play_history[i - 1] % 2
        == config.muzero_player
    )
    opponent_reward = sum(
        reward
        for i, reward in enumerate(game_history.reward_history)
        if game_history.to_play_history[i - 1] % 2
        != config.muzero_player
    )
    print("muzero_reward", muzero_reward)
    print("opponent_reward", opponent_reward)