import helper

WEIGHT = 40
# ROLES = [
#   855630140164014090, # BRONZE
#   851669066622959648, # ELITE
#   851669140463812608, # MASTERS
#   851669152108380201, # GRANDMASTERS
#   851669162887348234, # LEGEND
# ]

ROLES = [
    855641875972882443,  # BRONZE
    855641806758477844,  # SILVER
    855641716164919356,  # CHAMPION
    856066147438952478,  # LEGEND
]


def get_role_id(score):
    if score < 100:
        return ROLES[0]
    elif score < 200:
        return ROLES[1]
    elif score < 300:
        return ROLES[2]
    elif score < 400:
        return ROLES[3]
    else:
        return ROLES[3]


def calc_elo(winner, loser):
    w_current_elo = get_current_elo(winner)
    l_current_elo = get_current_elo(loser)
    w_new_elo, l_new_elo = calculate_expected_score(w_current_elo, l_current_elo)
    w_new_elo = check_negative(w_new_elo)
    l_new_elo = check_negative(l_new_elo)
    return w_new_elo, l_new_elo


def get_current_elo(member):
    brackets = helper.find_name_brackets(member.nick)
    if brackets is None:
        return 0
    num = brackets.replace("[", "")
    num = num.replace("]", "")
    try:
        int(num)
    except:
        num = 0
        # await message.author.edit(nick=message.current_name + " [5]")
    return int(num)


def calculate_expected_score(winner, loser):
    e = 1 / (1 + (10) ** (abs(winner - loser) / 400))
    lower_score = round(e * WEIGHT)
    higher_score = round((1 - e) * WEIGHT)
    if lower_score == 0:
        lower_score = 1
    if higher_score == 0:
        higher_score = 1

    if winner > loser:
        new_winner, new_loser = winner + lower_score, loser - lower_score
    else:
        new_winner, new_loser = winner + higher_score, loser - higher_score
    return new_winner, new_loser


def check_negative(elo):
    if int(elo) <= 0:
        elo = 0
    return elo
