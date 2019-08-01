from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST

# Create a Colorfight Instance. This will be the object that you interact
# with.
game = Colorfight()

# Connect to the server. This will connect to the public room. If you want to
# join other rooms, you need to change the argument
game.connect(room = 'public')

# game.register should return True if succeed.
# As no duplicate usernames are allowed, a random integer string is appended
# to the example username. You don't need to do this, change the username
# to your ID.
# You need to set a password. For the example AI, the current time is used
# as the password. You should change it to something that will not change 
# between runs so you can continue the game if disconnected.
if game.register(username = 'Degadon', \
        password = '2019Color'):
    # This is the game loop
    while True:
        # The command list we will send to the server
        cmd_list = []
        # The list of cells that we want to attack
        my_attack_list = []
        # update_turn() is required to get the latest information from the
        # server. This will halt the program until it receives the updated
        # information. 
        # After update_turn(), game object will be updated.   
        last_turn = game.turn
        game.update_turn()

        # Turn number does not go back. So if it is going back, that means
        # a new game. You can add a infinite loop to continuously register
        # to the latest game and play.
        if game.turn < last_turn:
            break

        # Check if you exist in the game. If not, wait for the next round.
        # You may not appear immediately after you join. But you should be 
        # in the game after one round.
        if game.me == None:
            continue

        me = game.me

        building_num = 1;

        # game.me.cells is a dict, where the keys are Position and the values
        # are MapCell. Get all my cells.
        for cell in game.me.cells.values():

            if cell.building.can_upgrade and \
                    (cell.building.is_home or cell.building.level < me.tech_level) and \
                    cell.building.upgrade_gold < me.gold and \
                    cell.building.upgrade_energy < me.energy and \
                    game.turn <= 425:
                    #upgrading past a certain point in the game will not help win
                cmd_list.append(game.upgrade(cell.position))
                print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                me.gold   -= cell.building.upgrade_gold
                me.energy -= cell.building.upgrade_energy


            for pos in cell.position.get_surrounding_cardinals():
                # Get the MapCell object of that position
                c = game.game_map[pos]
                if c.attack_cost < me.energy and c.owner != game.uid \
                        and c.position not in my_attack_list:
                    cmd_list.append(game.attack(pos, c.attack_cost))
                    print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, c.attack_cost))
                    game.me.energy -= c.attack_cost
                    my_attack_list.append(c.position)
            
                
            if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:
                build = 0
                #Only build if it will be worthwhile
                if cell.gold >= 6:
                    building = BLD_GOLD_MINE
                    build = 1
                elif cell.energy >= 6:
                    building = BLD_ENERGY_WELL
                    build = 1
                if build == 1:
                    cmd_list.append(game.build(cell.position, building))
                    print("We build {} on ({}, {})".format(building, cell.position.x, cell.position.y))
                    me.gold -= 100

        
        # Send the command list to the server
        result = game.send_cmd(cmd_list)
        print(result)
