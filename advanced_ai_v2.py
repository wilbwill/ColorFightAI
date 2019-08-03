from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST
from colorfight.position import Position

#---------------------CLASS DEFINITIONS--------------------#

# Extension of the user class, comprehensive information about game and ai situation
class Situation:
    def __init__(self):
        self.gold = 0
        self.energy = 0
        self.cellCount = 0
        self.buildCount = 0
        self.cellsToBuildOn = []
        self.cellsToUpgrade = []
        self.cellsToAttack = []
        self.homePos = Position(0, 0)
        self.enemyHomePos = Position(0, 0)
        self.enemyContact = False
        self.enemyHomeContact = False
    #def__init__()

    def getInfo(self, game):
        #Info for debugging purposes
        print("Turn: ", game.turn)
        print("Total Gold: ", game.me.gold)
        print("Gold Allowed: ", int(game.me.gold * 0.90))
        print("Total Energy: ", game.me.energy)
        print("Energy Allowed: ", int(game.me.energy * 0.85))

        #update basic info
        self.gold = game.me.gold
        self.energy = game.me.energy
        self.cellCount = len(game.me.cells)

        # scan the game cells
        for x in range(game.game_map.width):
            for y in range(game.game_map.height):
                #for convenience
                cell = game.game_map._cells[x][y]


                if(cell.owner == 0):
                    continue

                if(cell.owner == game.me.uid):
                    if(not cell.building.is_empty):
                        self.buildCount += 1
                    if(cell.building.can_upgrade and \
                            (cell.building.is_home or cell.building.level < game.me.tech_level)):
                        if(cell.building.is_home and cell.building.upgrade_gold < me.gold and \
                                cell.building.upgrade_energy < me.energy):
                            self.cellsToUpgrade.append(cell.position)
                        elif(cell.building.upgrade_gold < int(me.gold * 0.9) and \
                                cell.building.upgrade_energy < int(me.energy * 0.85)):
                            self.cellsToUpgrade.append(cell.position)

                    elif(cell.building.is_empty):
                        # we can think about building on this
                        self.cellsToBuildOn.append(cell.position)


                    if(cell.building.is_home):
                        self.homePos = Position(x, y)
                else:
                    # must be an enemy cell
                    if(cell.building.name == 'home'):
                        enemyHomePos = cell.position

        # scan through available cells to attack
        energyAllow = int(game.me.energy * 0.85)
        for cell in game.me.cells.values():
            for pos in cell.position.get_surrounding_cardinals():
                c = game.game_map[pos]
                if c.attack_cost < game.me.energy and c.owner != game.uid \
                        and c.position not in self.cellsToAttack \
                        and c.building.name == 'home':
                    self.cellsToAttack.append(pos)
                elif c.attack_cost < energyAllow and c.owner != game.uid \
                        and c.position not in self.cellsToAttack:
                    self.cellsToAttack.append(pos)

                # check if enemy home and if otherwise contacting enemy
                if(c.owner != game.me.uid and c.owner != 0):
                    self.enemyContact = True
                    if(c.building.name == 'home'):
                        self.enemyHomeContact == True
    #def getInfo()
#Situation()

#-------------------END CLASS DEFINITIONS------------------#



#--------------------FUNCTION DEFINITIONS--------------------#

#helps to determine which building to build
def findDatBias(situation, game):
    bias = -1

    #if less gold than energy
    if(situation.gold <= situation.energy):
        bias -= 1
    #if beginning of match
    if(game.turn < int(0.3 * game.max_turn)):
        bias += 2
    #if in the mid-late game
    if(game.turn >= int(0.3 * game.max_turn)):
        bias -= 1
    #if in the late game
    if(game.turn >= int(0.8 * game.max_turn)):
        bias -= 1
    if(game.turn >= int(0.9 * game.max_turn)):
        bias -= 1
    #if contacting enemy
    if(situation.enemyContact):
        bias += 1

    return bias

def budgetGold(gold, situation):
    if(len(situation.cellsToUpgrade) == 0):
        return gold
    elif(len(situation.cellsToBuildOn) == 0):
        return 0;
    else:
        return int(gold * 0.2)

def organizeCells(listIn, game):
    newList = []
    highestCellIndex = 0
    highestScore = 0
    origLen = len(listIn)
    score = 0
    for i in range(origLen):
        for j in range(origLen - len(newList)):
            cell = game.game_map[listIn[j]]
            score = cell.gold + cell.energy

            if(cell.gold == 10 or cell.energy == 10):
                score = 20

            if(cell.gold == 9 or cell.energy == 9):
                score = 18

            if(cell.building.name == "home"):
                score += 100
                highestCellIndex = j

            if(cell.building.name == "energy_well"):
                score -= 7

            if(score > highestScore):
                highestCellIndex = j
                highestScore = score
        
        newList.append(listIn[highestCellIndex])
        del listIn[highestCellIndex]
        highestScore = 0
        score = 0
        highestCellIndex = 0

    return newList

def isNearHome(pos, situation):
    x = situation.homePos.x
    y = situation.homePos.y

    if(pos.x >= x - 2 and pos.x <= x + 2 \
            and pos.y >= y - 2 and pos.y <= y + 2):
        return True

    return False


def analysis(pos, game, situation):
    cell = game.game_map[pos]
    score = cell.gold + cell.energy
    if(cell.owner != game.me.uid and cell.building.name == 'energy_well'):
        score += 10
    if(cell.owner != game.me.uid and cell.building.name == 'gold_mine'):
        score += 8
    if(cell.owner != game.me.uid and cell.building.name == 'home'):
        score += 20
    if(cell.owner != game.me.uid and cell.building.name == 'fortress'):
        score -= 5
    if(isNearHome(pos, situation)):
        score += 50
        #pass
    return float(score / cell.attack_cost)


def attackList(listIn, situation, game):
    newList = []
    cellIndex = 0
    highestScore = 0
    origLen = len(listIn)

    for i in range(origLen):
        for j in range(origLen - len(newList)):
            # do a cost-benefit analysis
            benefitScore = analysis(listIn[j], game, situation)
            if(benefitScore > highestScore):
                cellIndex = j
                highestScore = benefitScore
        newList.append(listIn[cellIndex])
        del listIn[cellIndex]
        highestScore = 0
        cellIndex = 0

    return newList

    

#-----------------END FUNCTION DEFINITIONS------------------#



#------------------------BEGIN TURN-------------------------#

# Create a Colorfight Instance
game = Colorfight()

# Connect to the server. This will connect to the public room. If you want to
# join other rooms, you need to change the argument
game.connect(room = 'public')

#Musikverein
#public
#Acropolis
#rank_2_1

# game.register should return True if succeed.
# As no duplicate usernames are allowed, a random integer string is appended
# to the example username. You don't need to do this, change the username
# to your ID.
# You need to set a password. For the example AI, the current time is used
# as the password. You should change it to something that will not change 
# between runs so you can continue the game if disconnected.
i = 1
while( i != 3):
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

            situation = Situation()
            situation.getInfo(game)

            #keep a small percentage of gold and energy around for insurance
            goldAllow = int(me.gold * 0.90)
            energyAllow = int(me.energy * 0.85)

            buildGold = budgetGold(goldAllow, situation)
            upgradeGold = goldAllow - buildGold

            orderlyList = []
            # Fill command list
            building = 'n'
            fort = False
            
            # Build
            # Find the energy bias
            bias = findDatBias(situation, game)
            orderlyList = organizeCells(situation.cellsToBuildOn, game)
            for pos in orderlyList:
                if(buildGold > 100):
                    c = game.game_map[pos]
                    # see if we nee to build a fortress
                    if(situation.enemyContact):
                        for card in pos.get_surrounding_cardinals():
                            if(game.game_map[card].owner != me.uid and game.game_map[card].owner != 0):
                                fort = True

                        if(fort):
                            building = BLD_FORTRESS
                            fort = False
                    #Otherwise build whichever build would be best
                    if(c.gold > c.energy + bias and building == 'n'):
                        building = BLD_GOLD_MINE
                    elif(building == 'n'):
                        building = BLD_ENERGY_WELL

                    if(building != 'n'):     
                        cmd_list.append(game.build(pos, building))
                        #situation.cellsToBuildOn.remove(pos)
                        print("We build {} on ({}, {})".format(building, pos.x, pos.y))
                        me.gold -= 100
                        buildGold -= 100

                    building = 'n'


            #Upgrade
            orderlyList = organizeCells(situation.cellsToUpgrade, game)
            if(game.turn > int(game.max_turn * 0.85)):
                orderlyList = []
            for pos in orderlyList:
                #check to upgrade home first
                cell = game.game_map[pos]
                if(cell.building.is_home):
                    cmd_list.append(game.upgrade(pos))
                    print("We upgraded ({}, {})".format(pos.x, pos.y))
                    upgradeGold -= game.game_map[pos].building.upgrade_gold
                    me.gold   -= game.game_map[pos].building.upgrade_gold
                    me.energy -= game.game_map[pos].building.upgrade_energy
                    energyAllow -= game.game_map[pos].building.upgrade_energy
                if(game.game_map[pos].building.upgrade_gold < upgradeGold and \
                                game.game_map[pos].building.upgrade_energy < energyAllow):
                    #if in the late game, defund energy wells
                    if(game.turn > int(game.max_turn * 0.70)):
                        if(cell.building.name == "energy_well"):
                            continue
                    if(cell.building.name == "fortress"):
                        continue
                    cmd_list.append(game.upgrade(pos))
                    print("We upgraded ({}, {})".format(pos.x, pos.y))
                    upgradeGold -= game.game_map[pos].building.upgrade_gold
                    me.gold   -= game.game_map[pos].building.upgrade_gold
                    me.energy -= game.game_map[pos].building.upgrade_energy
                    energyAllow -= game.game_map[pos].building.upgrade_energy


            #Attack
            orderlyList = attackList(situation.cellsToAttack, situation, game)
            print("Cells: ", len(me.cells), " Buildings", situation.buildCount + 75)
            boolAttack = True
            if(len(me.cells) >= situation.buildCount + 75):
                orderlyList = []
                boolAttack = False
            print(len(orderlyList))
            if(boolAttack):
                for pos in orderlyList:
                    cell = game.game_map[pos]
                    if(cell.building.name == 'home' and me.energy > cell.attack_cost):
                        cmd_list.append(game.attack(pos, cell.attack_cost))
                        print("We are attacking ({}, {}), their Home, with {} energy".format(pos.x, pos.y, cell.attack_cost))
                        me.energy -= cell.attack_cost
                        energyAllow -= cell.attack_cost
                        my_attack_list.append(pos)
                    elif(energyAllow > cell.attack_cost):
                        if(len(me.cells) < 650 or cell.owner != 0):
                            cmd_list.append(game.attack(pos, cell.attack_cost))
                            print("We are attacking ({}, {}), with {} energy".format(pos.x, pos.y, cell.attack_cost))
                            me.energy -= cell.attack_cost
                            energyAllow -= cell.attack_cost
                            my_attack_list.append(pos)



            
            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print(result)

            i += 1
    #-------------------------END TURN-------------------------#