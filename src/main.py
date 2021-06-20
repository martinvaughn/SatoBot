import discord
import os
from discord.ext import commands
from discord.ext.commands import MemberConverter, has_permissions, CommandNotFound
from discord.utils import get
import helper
import elo

COUNT = 0
TEN_MIN = 600  # 10 minutes in seconds
CHANNEL_ID = 850867690318200833  # ID of channel to send messages.
GUILD_ID = 848422158857142323
NAME_CHANGE_QUEUE = []  # IDs of names that can be changed
MESSAGE_CAN_DELETE = {}  # Messages that can be deleted by the bot.
MESSAGE_CAN_DELETE_DISPUTES = []  # Same as ^ but also for disputed messages.
CAN_ADD_IDS = []  # List of IDs of who can have Elo added. Only people who've played can have elo added.
TIME_DELETE = 10  # 86400 seconds == 24 hours

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
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(f"{loser.mention} disputes that {winner.mention} beat them. Calling Admin to chat.")


@client.command()
async def send_channel_message(loser: discord.Member, message, winner=None):
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(message)


@client.command()
async def send_dm_to_loser(winner: discord.Member, loser: discord.Member):
    if winner == loser:
        await send_channel_message(loser, f"{loser.mention} is trying to play himself... do I smell a cheater??")
        return
    channel = await loser.create_dm()
    try:
        message = await channel.send(
            f"{winner.mention} claims you lost a match to them. Please confirm.\nNOTE: This message will delete after your response or {int(TIME_DELETE / 3600)} hrs.",
            delete_after=TIME_DELETE)
    except:
        await send_channel_message(loser, f"Unable to send dm to {loser.mention}. Adding points automatically.")
        await update_elo(winner, loser)

    MESSAGE_CAN_DELETE[message.id] = loser
    await message.add_reaction('✅')
    await message.add_reaction('❌')
    await send_channel_message(loser, f"Confirmation message sent to {loser.mention}. Waiting for response.")


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


# @client.event
# async def on_member_join(member):
#   if member.nick is None:
#     member.nick = member.name + " [0]"
#   else:
#     member.nick = purge_name_brackets(member.nick)
#     member.nick = member.nick + " [0]"


@client.command(name="beat")
# @commands.cooldown(1, TEN_MIN * 2, commands.BucketType.user)
async def beat(ctx):
    if ctx.message.author == client.user:
        return

    # if ctx.message.content.startswith('!beat'):
    if ctx.message.mentions:
        loser = ctx.message.mentions[0]
        if loser.nick == None:
            loser.nick = loser.name
    else:
        await send_channel_message(ctx.message.author.mention,
                                   f"{ctx.message.author.mention} You didn't mention anyone. Try again.")
        return
    if ctx.message.author.nick == None:
        CAN_ADD_IDS.append(ctx.message.author.id)
        await ctx.message.author.edit(nick=ctx.message.author.name + "[0]")
    await confirm_game(winner=ctx.message.author, loser=loser)


# @beat.error
# async def beat_error(ctx, error):
#     if isinstance(error, commands.CommandOnCooldown):
#         msg = 'On cooldown still, please try again in {:.2f} min.'.format(error.retry_after / 60)
#         await ctx.send(msg)
#     else:
#         raise error


@client.command(name="update", aliases=["updatePoints"])
@has_permissions(administrator=True)
async def update_name(ctx, *args):
    print("args: ", args)
    converter = MemberConverter()
    member = await converter.convert(ctx, args[0])
    nick = " ".join(args[1:])
    nick = helper.check_name_length(nick)
    CAN_ADD_IDS.append(member.id)
    await member.edit(nick=nick)


# return true bc this should only be accessed by an admin.


@client.event
async def on_member_update(before, after):
    if before.nick == after.nick:
        return

    # ctx = await client.get_context()
    if before.id in CAN_ADD_IDS:
        CAN_ADD_IDS.remove(before.id)
        return

    old_brackets = ""
    try:
        old_brackets = helper.find_name_brackets(before.nick)
    except:
        print("Old brackets was None. Either hacker or 2nd time round. \n")
    if old_brackets is None:
        old_brackets = "[0]"

    cleaned = ""
    try:
        cleaned = helper.purge_name_brackets(after.nick)
    except:
        cleaned = after.nick
        if cleaned is None:
            NAME_CHANGE_QUEUE.append(before.id)
            await after.edit(nick=after.name + old_brackets)
            await send_dm(before,
                          "It looks you tried to remove your nickname, so we added your points back. \n\nIf you'd like to be removed from the elo scoring, please contact an Admin.")
            return

    cleaned = helper.check_name_length(cleaned)

    new_nick = cleaned + old_brackets
    if before.id not in NAME_CHANGE_QUEUE:
        NAME_CHANGE_QUEUE.append(before.id)
        await after.edit(nick=new_nick)
        # await send_dm(before, "You changed your nickname. We're updating it to match our guidelines.")
    else:
        NAME_CHANGE_QUEUE.remove(before.id)
        return


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


# Use on_raw_message_delete if you want it to check messages from before the last loading.
@client.event
async def on_message_delete(message):
    if message.id in MESSAGE_CAN_DELETE:
        loser = MESSAGE_CAN_DELETE[message.id]
        try:
            winner_id = helper.extract_id_from_message(message.content)
        except:
            print("ignoring reaction from ", loser)
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

    # else:
    #     raise error


async def update_elo(winner, loser):
    winner_elo, loser_elo = elo.calc_elo(winner, loser)
    await change_role(winner, winner_elo)
    await change_role(loser, loser_elo)

    new_winner_name = helper.new_name(winner, winner_elo)
    new_loser_name = helper.new_name(loser, loser_elo)
    CAN_ADD_IDS.append(winner.id)
    try:
        await winner.edit(nick=new_winner_name)
    except discord.errors.HTTPException:
        print("Error: Name too long.")

    CAN_ADD_IDS.append(loser.id)
    try:
        await loser.edit(nick=new_loser_name)
    except discord.errors.HTTPException:
        print("Error: Name too long.")


async def confirm_game(winner, loser):
    await send_dm_to_loser(winner, loser)


async def change_role(member, elo_points):
    role_id = elo.get_role_id(elo_points)
    print("role_id: ", role_id)
    guild = client.get_guild(GUILD_ID)
    role = get(guild.roles, id=role_id)
    if role in member.roles:
        print("Member had role, returning")
        return
    else:
        await member.add_roles(role)
        not_roles = elo.ROLES[:]
        not_roles.remove(role_id)
        member_role_ids = [a.id for a in member.roles]

        print(member.nick + "'s roles: " + str(member_role_ids))
        print("Opposite roles: ", not_roles)

        for p_role_id in not_roles:
            if p_role_id in member_role_ids:
                p_role = get(guild.roles, id=p_role_id)
                print("user had other role: ", p_role_id)
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