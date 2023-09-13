# import importlib
#
# import models
# import self_play
import torch

# check with the cuda device

print(torch.cuda.is_available())
print(torch.cuda.current_device())

# 获取GPU设备的数量
num_devices = torch.cuda.device_count()

# 生成GPU设备的索引列表
device_indices = list(range(num_devices))

print("所有可用的GPU设备索引：", device_indices)

# checkpoint = {
#     "weights": None,
#     "optimizer_state": None,
#     "total_reward": 0,
#     "muzero_reward": 0,
#     "opponent_reward": 0,
#     "episode_length": 0,
#     "mean_value": 0,
#     "training_step": 0,
#     "lr": 0,
#     "total_loss": 0,
#     "value_loss": 0,
#     "reward_loss": 0,
#     "policy_loss": 0,
#     "num_played_games": 0,
#     "num_played_steps": 0,
#     "num_reanalysed_games": 0,
#     "terminate": False,
# }
# game_module = importlib.import_module("games.pacman")
# Game = game_module.Game
# config = game_module.MuZeroConfig()
#
# model = models.MuZeroNetwork(config)
# weigths = model.get_weights()
# checkpoint["weights"] = weigths
#
# sp = self_play.SelfPlay(checkpoint, Game, config, 90054)
# while True:
#     sp.play_game(0, 0,False, "self", 0)