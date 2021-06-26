import helper

WEIGHT = 40
ROLES = [
  858419991477223484, # Academy Student 
  858420330614751272, # LAG GUARDIAN
  858420594683805706, # LAG ELITE 
  858420672112230410, # LAG CONQUEROR
  858420748690259979, # LAG SHINOBI
  858420824406753340, # LAG KAGE
  858421193824272425  # LAG RONIN
]


def get_role_id(score):
    if score < 499:
        return ROLES[0]
    elif score < 999:
        return ROLES[1]
    elif score < 1499:
        return ROLES[2]
    elif score < 1999:
        return ROLES[3]
    elif score < 2499:
        return ROLES[4]
    elif score < 2999:
        return ROLES[5]
    else:
        return ROLES[6]


def calc_elo(winner, loser):
    w_current_elo = get_current_elo(winner)
    l_current_elo = get_current_elo(loser)
    w_new_elo, l_new_elo, points = calculate_expected_score(w_current_elo, l_current_elo)
    # points is the points in play.
    w_new_elo = check_negative(w_new_elo)
    l_new_elo = check_negative(l_new_elo)
    return w_new_elo, l_new_elo, points


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
        points_given = lower_score
    else:
        new_winner, new_loser = winner + higher_score, loser - higher_score
        points_given = higher_score
    return new_winner, new_loser, points_given


def check_negative(elo):
    if int(elo) <= 0:
        elo = 0
    return elo
