import os
import pygame
from pygame.locals import (
    K_ESCAPE, K_RETURN,
    K_0, K_1, K_2,
    K_KP0, K_KP1, K_KP2,
    KEYDOWN,
    QUIT
)
import spritesheet
from typing import Tuple

import rlcard
from rlcard import models
from rlcard.agents import LimitholdemHumanAgent as HumanAgent
from rlcard.utils import reorganize

# Pygame
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
FONT_SIZE = 25
NORMAL_FONT_SIZE = 20
RESULT_FONT_SIZE = 60
FONT_NAME = "Arial"

# Sprites
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CARDS_SHEET = None
SUIT_INDEX = { 'H':0, 'D':1, 'S':2, 'C':3 }
RANK_INDEX = { '2':0, '3':1, '4':2, '5':3, '6':4, '7':5, '8':6, 
               '9':7, 'T':8, 'A':9, 'K':10, 'Q':11, 'J':12, 'B':13}
CARD_SIZE = (120, 170)
ROWS = 4
COLUMNS = 14

# env variables
env = None
trajectories = None
state = None
player_id = None
finished = False

def get_card_position(card: str) -> Tuple[dict]:
    return RANK_INDEX[card[1]] * CARD_SIZE[0],  SUIT_INDEX[card[0]] * CARD_SIZE[1]

def get_card_image(card: str):
    pos = get_card_position(card)
    image = CARDS_SHEET.image_at((pos[0], pos[1], CARD_SIZE[0], CARD_SIZE[1]))
    image.set_colorkey((52, 52, 52))
    return image

def config_env():
    global env, finished

    # Make environment
    # Set 'record_action' to True because we need it to get the results
    finished = False
    env = rlcard.make('limit-holdem', config={'record_action': True})
    human_agent = HumanAgent(env.action_num)
    cfr_agent = models.load('limit-holdem-dqn').agents[0]
    env.set_agents([human_agent, cfr_agent])
    return env

def reset_env():
    global env, trajectories, state, player_id

    trajectories = [[] for _ in range(env.player_num)]
    state, player_id = env.reset()
    trajectories[player_id].append(state)

def get_results():
    payoffs = env.get_payoffs()
    result = ""
    if payoffs[0] < 0:
        result = "You lost!"
    elif payoffs[0] > 0:
        result = "You won!"
    else: 
        result = "Tie!"
    result += " Press Enter to play again!"
    return result

def main():
    global CARDS_SHEET, env, trajectories, state, player_id, finished
    
    env = config_env()
    reset_env()
    
    pygame.init()
    # Set up the drawing window
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    CARDS_SHEET = spritesheet.spritesheet(os.path.join(DIR_PATH, 'sprites/Deck.png'))

    # fonts
    font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
    text_font = pygame.font.SysFont(FONT_NAME, NORMAL_FONT_SIZE)
    result_font = pygame.font.SysFont(FONT_NAME, RESULT_FONT_SIZE)

    # set variables
    last_player_action = ""
    last_ai_action = ""

    # Run until the user asks to quit
    running = True
    result = ""
    while running:  
        action = -1

        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                if finished and event.key == K_RETURN: 
                    finished = False
                    last_player_action = ""
                    last_ai_action = ""
                    reset_env()
                if player_id == 1 or finished: pass
                elif event.key == K_0 or event.key == K_KP0: action = 0
                elif event.key == K_1 or event.key == K_KP1: action = 1
                elif event.key == K_2 or event.key == K_KP2: action = 2
            elif event.type == pygame.QUIT: running = False

        # make background green
        screen.fill((37, 125, 95))

        # display chips
        player_chips = state["raw_obs"]['my_chips']
        all_chips = state["raw_obs"]['all_chips'][0] + state["raw_obs"]['all_chips'][1]
        text = text_font.render(f"Player chips {player_chips}", 0, (0,0,0))
        screen.blit(text, (0.65 * SCREEN_WIDTH, 0.75 * SCREEN_HEIGHT))
        text = text_font.render(f"All chips {all_chips}", 0, (0,0,0))
        screen.blit(text, (0.65 * SCREEN_WIDTH, 0.8 * SCREEN_HEIGHT))

        # display last actions
        text = text_font.render(f"Last player action: {last_player_action}", 0, (0,0,0))
        screen.blit(text, (0.65 * SCREEN_WIDTH, 0.2 * SCREEN_HEIGHT))
        text = text_font.render(f"Last ai action: {last_ai_action}", 0, (0,0,0))
        screen.blit(text, (0.65 * SCREEN_WIDTH, 0.25 * SCREEN_HEIGHT))

        # display player cards
        image_1 = get_card_image(env.get_perfect_information()["hand_cards"][0][0])
        screen.blit(image_1, (0.35 * SCREEN_WIDTH, 0.7 * SCREEN_HEIGHT))
        image_2 = get_card_image(env.get_perfect_information()["hand_cards"][0][1])
        screen.blit(image_2, (0.5 * SCREEN_WIDTH, 0.7 * SCREEN_HEIGHT))

        # display ai cards
        ai_cards = env.get_perfect_information()['hand_cards'][1] if finished else ["CB", "CB"]
        image_3 = get_card_image(ai_cards[0])
        screen.blit(image_3, (0.35 * SCREEN_WIDTH, 0.1 * SCREEN_HEIGHT))
        image_4 = get_card_image(ai_cards[1])
        screen.blit(image_4, (0.5 * SCREEN_WIDTH, 0.1 * SCREEN_HEIGHT))

        # display public cards
        for i, card in enumerate(state["raw_obs"]["public_cards"]):
            image = get_card_image(card)
            screen.blit(image, ((i * 0.15 + 0.15) * SCREEN_WIDTH, 0.4 * SCREEN_HEIGHT))

        if finished:
            # display results
            text = result_font.render(result, 0, (0, 15, 77))
            screen.blit(text, (0.0275 * SCREEN_WIDTH, 0.45 * SCREEN_HEIGHT))
            pygame.display.flip()
            continue

        # display actions
        if player_id == 0:
            text_string = ', '.join([f"{index}: {action}" for index, action 
                          in enumerate(state['raw_obs']['legal_actions'])])
            text = font.render(text_string, 0, (0,0,0))
            screen.blit(text, (0.02 * SCREEN_WIDTH, 0.75 * SCREEN_HEIGHT))
        else:
            action, _ = env.agents[player_id].eval_step(state)

        pygame.display.flip()

        if action == -1: continue

        # Environment steps
        use_raw = env.agents[player_id].use_raw
        if use_raw:
            action = state['raw_obs']['legal_actions'][action]
        next_state, next_player_id = env.step(action, use_raw)

        if player_id == 1: last_ai_action = env.decode_action(action)
        else: last_player_action = action
            
        # Save action
        trajectories[player_id].append(action)

        # Set the state and player
        state = next_state
        player_id = next_player_id

        # Save state.
        if not env.game.is_over():
            trajectories[player_id].append(state)
        else:
            finished = True
            # Add a final state to all the players
            for player_id in range(env.player_num):
                state = env.get_state(player_id)
                trajectories[player_id].append(state)
            
            result = get_results()

    pygame.quit()

if __name__ == "__main__":
    main()