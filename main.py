from muzero import MuZero, load_model_menu

if __name__ == "__main__":
    muzero = MuZero("pacman")
    # load_model_menu(muzero, "pacman")
    muzero.train()