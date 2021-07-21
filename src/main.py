import discord
import os
from discord.ext import commands
from discord.ext.commands import MemberConverter, has_permissions, CommandNotFound
from discord.utils import get
import helper
import elo
from datetime import datetime, timedelta
import logging
from collections import Counter


logging.basicConfig(filename="main.log",
                    format='%(asctime)s %(message)s',)
logger = logging.getLogger()
logger.setLevel(20)

logger.warning("Main initializing.")

ADMIN_ROLE_ID = 848423895408705546
COUNT = 0
TEN_MIN = 600  # 10 minutes in seconds
CHANNEL_ID = 850867690318200833  # ID of channel to send most messages.
RESULTS_ID = 858081752421236836 # ID of channel to send results.
GUILD_ID = 848422158857142323 # ID of the server in use.
CHEATER_ROLE_ID = 867473815167959080
# NAME_CHANGE_QUEUE = []  # IDs of names that can be changed --> For when people can change name
MESSAGE_CAN_DELETE = {}  # Messages that can be deleted by the bot.
MESSAGE_CAN_DELETE_DISPUTES = []  # Same as ^ but also for disputed messages.
# CAN_ADD_IDS = []  # List of IDs of who can have Elo added. Only people who've played can have elo added.
TIME_DELETE = 90  # 86400 seconds == 24 hours
SAME_USER_PLAY_LIMIT = 5

Intents = discord.Intents()
intents = Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)  # Or client = discord.Client(intents = intents)


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.command()
async def send_dm(member: discord.Member, content):
    channel = await member.create_dm()
    await channel.send(content)


@client.command()
async def send_dispute_message(winner: discord.Member, loser: discord.Member):
    channel = client.get_channel(RESULTS_ID)
    guild = client.get_guild(GUILD_ID)
    role = get(guild.roles, id=ADMIN_ROLE_ID)
    await channel.send(f"{loser.mention} disputes that {winner.mention} beat them. Calling {role.mention} to chat.")


@client.command()
async def send_channel_message(message, channel_id):
    channel = client.get_channel(channel_id)
    await channel.send(message)


@client.command()
async def send_dm_to_loser(winner: discord.Member, loser: discord.Member):
    if winner == loser:
        await send_channel_message(f"{loser.mention} is trying to play himself... do I smell a cheater??", CHANNEL_ID)
        return
    channel = await loser.create_dm()
    try:
        message = await channel.send(
            f"{winner.mention} claims you lost a match to them. Please confirm.\nNOTE: This message will delete after your response or {int(TIME_DELETE / 3600)} hrs.",
            delete_after=TIME_DELETE)
    except:
        await send_channel_message(f"Unable to send dm to {loser.mention}. Adding points automatically.", CHANNEL_ID)
        await update_elo(winner, loser)
        logger.warning(f"Unable to send message to {loser.name}, points added to {winner.name}")
        return

    MESSAGE_CAN_DELETE[message.id] = loser
    await message.add_reaction('✅')
    await message.add_reaction('❌')
    await send_channel_message(f"Confirmation DM sent to {loser.mention}. Waiting for response.", CHANNEL_ID)


@client.event
async def on_reaction_add(reaction, loser):
    if loser == client.user:
        return

    if reaction.count > 1:
        if reaction.emoji == '✅':
            await reaction.message.delete()  # delete the message so it can't be spammed.

        elif reaction.emoji == '❌':
            MESSAGE_CAN_DELETE_DISPUTES.append(reaction.message.id)
            await reaction.message.delete()



@client.command(name="beat")
# @commands.cooldown(1, TEN_MIN * 2, commands.BucketType.user)
async def beat(ctx):
    if ctx.channel.id != CHANNEL_ID:
        await send_channel_message(f"You're playing in the wrong channel. Plz stop :-/", ctx.channel.id)
        return

    if ctx.message.author == client.user:
        return

    # if ctx.message.content.startswith('!beat'):
    if ctx.message.mentions:
        loser = ctx.message.mentions[0]
        if loser == client.user:
          await send_channel_message(f"You wish to challenge{client.user.mention}?? You Lose!\njk but really you can't play me, I'm a bot.", CHANNEL_ID)
          return

        if loser.nick == None:
            loser.nick = loser.name
    else:
        await send_channel_message(f"{ctx.message.author.mention} You didn't mention anyone. Try again.", CHANNEL_ID)
        return
    if ctx.message.author.nick == None:
        # CAN_ADD_IDS.append(ctx.message.author.id) -> for user can change names
        await ctx.message.author.edit(nick=ctx.message.author.name + "[0]")
    await confirm_game(winner=ctx.message.author, loser=loser)

@client.command(name="update", aliases=["updatePoints"])
@has_permissions(administrator=True)
async def update_name(ctx, *args):
    converter = MemberConverter()
    member = await converter.convert(ctx, args[0])
    nick = " ".join(args[1:])
    nick = helper.check_name_length(nick)
    # CAN_ADD_IDS.append(member.id)
    await member.edit(nick=nick)


# TOURNE MODE:
@client.command(name="leaderboard")
@has_permissions(administrator=True)
async def leaderboard(ctx, *args):
    elo_list = []
    guild = client.get_guild(GUILD_ID)
    for member in guild.members:
      if member.nick is not None:
        current_elo = elo.get_current_elo(member)
        elo_list.append((member.nick, current_elo))
    sorted_elo_list = sorted(elo_list, key=lambda x: x[1], reverse=True)
    await send_channel_message(f''' ```\Blue
    ╭──── SATO LEADERBOARD ────╮
     1. {sorted_elo_list[0][0]}
     2. {sorted_elo_list[1][0]}
     3. {sorted_elo_list[2][0]}
     4. {sorted_elo_list[3][0]}
     5. {sorted_elo_list[4][0]}
     6. {sorted_elo_list[5][0]}
     7. {sorted_elo_list[6][0]}
     8. {sorted_elo_list[7][0]}
     9. {sorted_elo_list[8][0]}
     10. {sorted_elo_list[9][0]}
╰──────────────────╯''', CHANNEL_ID)
    # elo_list.sort( BOOM )


# TOURNE MODE:
@client.command(name="checkCheaters")
@has_permissions(administrator=True)
async def checkCheaters(ctx, *args):
    beaters = {}
    guild = client.get_guild(GUILD_ID)
    now = datetime.today()
    yesterday = now - timedelta(days=1)
    channel = client.get_channel(CHANNEL_ID)
    messages = await channel.history(after=yesterday, before=now).flatten()
    for message in messages:
      if message.content.startswith("!beat") and message.mentions:
        if message.author.id in beaters:
          old_list = beaters[message.author.id]
          old_list.append(message.mentions[0].id)
          beaters[message.author.id] = old_list
        else:
          beaters[message.author.id] = [message.mentions[0].id]
  
    for user in beaters:
      if isinstance(beaters[user] , list):
        counts = Counter(beaters[user])
        for c in counts:
          if counts[c] >= SAME_USER_PLAY_LIMIT:
            role = get(guild.roles, id=CHEATER_ROLE_ID)
            cheater = get(client.get_all_members(), id=user)
            if role not in cheater.roles:
              await cheater.add_roles(role)
              channel = client.get_channel(RESULTS_ID)
              guild = client.get_guild(GUILD_ID)
              role = get(guild.roles, id=ADMIN_ROLE_ID)
              await send_channel_message(f"{cheater.mention} you played the same player too many times. Talk to {role.mention} to get privileges back.", RESULTS_ID)
   


# Use on_raw_message_delete if you want it to check messages from before the last loading.
@client.event
async def on_message_delete(message):
    if message.id in MESSAGE_CAN_DELETE:
        loser = MESSAGE_CAN_DELETE[message.id]
        try:
            winner_id = helper.extract_id_from_message(message.content)
        except:
            return
        winner = get(client.get_all_members(), id=winner_id)
        ctx = await client.get_context(message)
        converter = MemberConverter()
        build_id = "<@" + str(loser.id) + ">"
        loser = await converter.convert(ctx, build_id)

        if message.id not in MESSAGE_CAN_DELETE_DISPUTES:
            MESSAGE_CAN_DELETE.pop(message.id, None)
            await update_elo(winner, loser)

        elif message.id in MESSAGE_CAN_DELETE_DISPUTES:
            MESSAGE_CAN_DELETE.pop(message.id, None)
            MESSAGE_CAN_DELETE_DISPUTES.remove(message.id)
            await send_dispute_message(winner, loser)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return

    elif isinstance(error, commands.CommandOnCooldown):
        msg = 'On cooldown still, please try again in {:.2f} min.'.format(error.retry_after / 60)
        await ctx.send(msg)

    else:
      raise error


async def update_elo(winner, loser):
    winner_elo, loser_elo, points = elo.calc_elo(winner, loser)
    await change_role(winner, winner_elo)
    await change_role(loser, loser_elo)

    new_winner_name = helper.new_name(winner, winner_elo)
    new_loser_name = helper.new_name(loser, loser_elo)
    # CAN_ADD_IDS.append(winner.id)
    try:
        await winner.edit(nick=new_winner_name)
    except discord.errors.HTTPException:
        logger.warning(f"User name: {winner.name} Exception line 256 main")

    # CAN_ADD_IDS.append(loser.id)
    try:
        await loser.edit(nick=new_loser_name)
    except discord.errors.HTTPException:
        logger.warning(f"User name: {loser.name} Exception line 262 main")
    # send winning message in results channel.
    await send_channel_message(f"Winner: {winner.mention} Points Added: {int(points)}\nLoser: {loser.mention} Points Taken: {int(points)}\n", RESULTS_ID)


async def confirm_game(winner, loser):
    await send_dm_to_loser(winner, loser)


async def change_role(member, elo_points):
    role_id = elo.get_role_id(elo_points)
    guild = client.get_guild(GUILD_ID)
    role = get(guild.roles, id=role_id)
    if role in member.roles:
        return
    else:
        await member.add_roles(role)
        not_roles = elo.ROLES[:]
        not_roles.remove(role_id)
        member_role_ids = [a.id for a in member.roles]

        for p_role_id in not_roles:
            if p_role_id in member_role_ids:
                p_role = get(guild.roles, id=p_role_id)
                await member.remove_roles(p_role)


client.run(os.getenv('TOKEN'))

# maybe use later for detecting if someone changed their name inaccurately
# if message.author.nick is None or message.author.name == message.author.nick:
#       pass
#       current_name = message.author.name + " [5]"
#       await message.author.edit(nick=current_name)
#       return
#     else:
#       current_name = message.author.nick


# member = message.guild.member(id)
# print(member)

# ctx = await client.get_context(message)

#     try:
#   pass
#   # loser = message.content.split(" ", 1)[1]
#   #id = loser.replace("/[!>]/g", '')
# except:
#   pass


# if not re.search(r'\[.+\]', current_name):
# current_name = purge_name_brackets(current_name)
# new_name = current_name + " [5]"



# ADD WHEN THE USERS ARE ABLE TO CHANGE NICKNAMES
# @client.event
# async def on_member_update(before, after):
#     if before.nick == after.nick:
#         return

#     # ctx = await client.get_context()
#     if before.id in CAN_ADD_IDS:
#         CAN_ADD_IDS.remove(before.id)
#         return

#     old_brackets = ""
#     try:
#         old_brackets = helper.find_name_brackets(before.nick)
#     except:
#         logger.warning(f"User name: {before.name} has no brackets.")
#     if old_brackets is None:
#         old_brackets = "[0]"

#     cleaned = ""
#     try:
#         cleaned = helper.purge_name_brackets(after.nick)
#     except:
#         cleaned = after.nick
#         if cleaned is None:
#             NAME_CHANGE_QUEUE.append(before.id)
#             await after.edit(nick=after.name + old_brackets)
#             await send_dm(before,
#                           "It looks you like tried to remove your nickname, so we added your points back.\nIf you'd like to be removed from the elo scoring, please contact an Admin.")
#             logger.warning(f"User name: {before.name} attempted to remove nickname")
#             return

#     cleaned = helper.check_name_length(cleaned)

#     new_nick = cleaned + old_brackets
#     if before.id not in NAME_CHANGE_QUEUE:
#         NAME_CHANGE_QUEUE.append(before.id)
#         await after.edit(nick=new_nick)
#         # await send_dm(before, "You changed your nickname. We're updating it to match our guidelines.")
#     else:
#         NAME_CHANGE_QUEUE.remove(before.id)
#         return



# ADD if going back to on_message
# @client.event
# async def on_message(message):
#   if message.author == client.user:
#     return

#   if message.content.startswith('!beat'):
#     if message.mentions:
#       loser = message.mentions[0]
#       if loser.nick == None:
#         loser.nick = loser.name
#     else:
#       await send_channel_message(message.author.mention, f"{message.author.mention} You didn't mention anyone. Try again.")
#       return
#     if message.author.nick == None:
#       CAN_ADD_IDS.append(message.author.id)
#       await message.author.edit(nick=message.author.name + "[0]")
#     await confirm_game(winner=message.author, loser=loser)
#   await client.process_commands(message)

# @beat.error
# async def beat_error(ctx, error):
#     if isinstance(error, commands.CommandOnCooldown):
#         msg = 'On cooldown still, please try again in {:.2f} min.'.format(error.retry_after / 60)
#         await ctx.send(msg)
#     else:
#         raise error




# When sato bot is tagged:
# if loser == client.user:
#           print("yee")
#           await send_channel_message(f"You wish to challenge{client.user.mention}?? You Lose!", CHANNEL_ID)