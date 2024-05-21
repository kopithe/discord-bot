import discord
from discord.ext import commands, tasks
import asyncio

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
intents.members = True
intents.presences = True  # Needed to monitor status updates

bot = commands.Bot(command_prefix='!', intents=intents)

# Define cooldown for the /free command
role_cooldowns = {
    "🪐・Bronze": commands.CooldownMapping.from_cooldown(1, 3 * 60 * 60, commands.BucketType.user),
    "🥈・Silver": commands.CooldownMapping.from_cooldown(1, 3 * 60 * 60, commands.BucketType.user),
    "💎・Diamond": commands.CooldownMapping.from_cooldown(1, 3 * 60 * 60, commands.BucketType.user)
}

# Role to level mapping
role_to_level = {
    "🪐・Bronze": "B",
    "🥈・Silver": "S",
    "💎・Diamond": "D"
}

# Track user command execution count
user_command_count = {}

# Start the status check task when the bot is ready
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="1hack-ogfnfree.netlify.app/"))
    await bot.tree.sync()
    check_custom_status.start()
    print(f'We have logged in as {bot.user}')

@bot.command()
async def free(ctx):
    # Check if the user has the owner role
    owner_role = discord.utils.get(ctx.guild.roles, name="owner")
    if owner_role in ctx.author.roles:
        # Delete the message of the user who runs the command
        await ctx.message.delete()

        try:
            # Read the "O+:" key from the file
            with open('key.txt', 'r+') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("O+:"):
                        key = line.strip().split(": ")[1]
                        del lines[i]
                        file.seek(0)
                        file.truncate()
                        file.writelines(lines)
                        break
                else:
                    raise ValueError("No 'O+:' key found in the file.")
        except FileNotFoundError:
            await ctx.send("Sorry, the key file is not available at the moment.")
            return
        except ValueError:
            await ctx.author.send(embed=discord.Embed(
                title="Key Not Available",
                description="Sorry, no 'O+:' key found in the file. Please contact the staff to restock the keys.",
                color=discord.Color.red()
            ))
            return

        # Send the key to the user with no cooldown
        await ctx.author.send(embed=discord.Embed(
            title="1hAck FREE OGFN (Owner Special)",
            description=(
                f"Dear {ctx.author.mention},\n\n"
                "As an owner, you have been granted a special key from O+. Enjoy your privileges!\n\n"
                "Your License key:\n"
                f"```{key}```\n"
                "[Loader download](https://1hack-ogfnfree.netlify.app/)"
            ),
            color=discord.Color.gold()
        ), delete_after=0)  # Instantly delete the message
        return

    # Check if the command is used in the correct channel
    correct_channel_id = 1241748405894643722
    if ctx.channel.id != correct_channel_id:
        correct_channel = bot.get_channel(correct_channel_id)
        msg = await ctx.send(f"This command is only available in {correct_channel.mention}.")
        ping_msg = await correct_channel.send(f"This is the right channel {ctx.author.mention}")
        await asyncio.sleep(10)
        await msg.delete()
        await ping_msg.delete()
        return
    
    # Delete the message of the user who runs the command
    await ctx.message.delete()

    # Find the highest role of the user
    user_role = max(ctx.author.roles, key=lambda r: r.position)

    # Check if the user is on cooldown based on their highest role
    if user_role.name in role_to_level:
        cooldown = role_cooldowns[user_role.name]
        retry_after = cooldown.update_rate_limit(ctx)
        if retry_after:
            hours, remainder = divmod(retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            # Sending a DM to the user about the cooldown
            await ctx.author.send(embed=discord.Embed(
                title="Cooldown Notice",
                description=f"Sorry, you are on cooldown for the `{ctx.prefix}free` command. Try again in {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.",
                color=discord.Color.red()
            ))
            return
    else:
        msg = await ctx.send("You do not have the required role to use this command.")
        await asyncio.sleep(3)
        await msg.delete()
        return
    
    # Send a thank you message in the channel with auto-deletion after 3 seconds
    await ctx.send(embed=discord.Embed(
        title="Thank you for using 1hack!",
        description=f"{ctx.author.mention}, we've sent your license key to your DMs. Please check your DMs.",
        color=discord.Color.green()
    ), delete_after=3)


    try:
        with open('key.txt', 'r') as file:
            lines = file.readlines()
            key = None
            for i, line in enumerate(lines):
                level, key_value = line.strip().split(": ")
                if level == role_to_level[user_role.name]:
                    key = key_value
                    # Remove the used key from the list
                    del lines[i]
                    break
            
            if key:
                # Determine the correct loader link based on the user's role
                loader_link = "https://1hack-ogfnfree.netlify.app/loader"
                if user_role.name == "🥈・Silver":
                    loader_link = "https://1hack-ogfnfree.netlify.app/silver/loader"
                elif user_role.name == "💎・Diamond":
                    loader_link = "https://1hack-ogfnfree.netlify.app/diamond/loader"
                
                # Send the key to the user's DM
                embed = discord.Embed(
                    title="1hAck FREE OGFN",
                    description=(
                        f"Dear {user_role.name} Customer,\n\n"
                        "Thank you for using 1hAck FREE OGFN. If you like it, leave a vouch in <#1242111933428007094>. "
                        "Your license key is 3 hours valid. Have fun!\n\n"
                        "Your License key:\n"
                        f"```{key}```\n"
                        f"[Loader download]({loader_link})"
                    ),
                    color=discord.Color.green()
                )
                await ctx.author.send(embed=embed)
                
                # Update the key file
                with open('key.txt', 'w') as file:
                    file.writelines(lines)
                # Update user command count
                user_id = ctx.author.id
                if user_id not in user_command_count:
                    user_command_count[user_id] = 0
                user_command_count[user_id] += 1
                
                # Check if the user should be leveled up
                if user_role.name == "🪐・Bronze" and user_command_count[user_id] == 3:
                    silver_role = discord.utils.get(ctx.guild.roles, name="🥈・Silver")
                    if silver_role not in ctx.author.roles:
                        await ctx.author.add_roles(silver_role)
                        user_command_count[user_id] = 0  # Reset the count after leveling up
                        # Send a DM about the reward
                        reward_embed = discord.Embed(
                            title="Congratulations! 🎉",
                            description=f"{ctx.author.mention}, you have been awarded the 🥈・Silver role for your continued support!",
                            color=discord.Color.blue()
                        )
                        await ctx.author.send(embed=reward_embed)
                elif user_role.name == "🥈・Silver" and user_command_count[user_id] == 6:
                    diamond_role = discord.utils.get(ctx.guild.roles, name="💎・Diamond")
                    if diamond_role not in ctx.author.roles:
                        await ctx.author.add_roles(diamond_role)
                        user_command_count[user_id] = 0  # Reset the count after leveling up
                        # Send a DM about the reward
                        reward_embed = discord.Embed(
                            title="Congratulations! 🎉",
                            description=f"{ctx.author.mention}, you have been awarded the 💎・Diamond role for your continued support!",
                            color=discord.Color.blue()
                        )
                        await ctx.author.send(embed=reward_embed)
            else:
                # Notify the user and owner about no available keys
                msg = await ctx.author.send(embed=discord.Embed(description="Sorry, no keys available at the moment. Owner has been notified.", color=discord.Color.red()))
                
                # Notify the owner to restock keys for the specific level
                if owner_role:
                    for member in ctx.guild.members:
                        if owner_role in member.roles:
                            embed = discord.Embed(
                                title="Keys Need Restocking",
                                description=f"The keys for {user_role.name} ({role_to_level[user_role.name]}) are exhausted and need restocking. Please provide more keys.",
                                color=discord.Color.red()
                            )
                            await member.send(embed=embed)
    except FileNotFoundError:
        msg = await ctx.send('Sorry, no keys available at the moment.')
        await asyncio.sleep(10)
        await msg.delete()

@bot.command()
async def state(ctx):
    await ctx.message.delete()
    user_id = ctx.author.id
    if user_id in user_command_count:
        count = user_command_count[user_id]
        if "🪐・Bronze" in [role.name for role in ctx.author.roles]:
            progress = min(100, (count / 3) * 100)
        elif "🥈・Silver" in [role.name for role in ctx.author.roles]:
            progress = min(100, (count / 6) * 100)
        else:
            progress = 0
        await ctx.author.send(embed=discord.Embed(
            title="Progress",
            description=f"Your progress towards the next level: {progress:.2f}%",
            color=discord.Color.blue()
        ))
    else:
        await ctx.author.send(embed=discord.Embed(
            title="Progress",
            description="You have no progress yet.",
            color=discord.Color.blue()
        ))

@tasks.loop(seconds=5)
async def check_custom_status():
    guild = discord.utils.get(bot.guilds)
    free_ex_role = discord.utils.get(guild.roles, name="🪐・Bronze")
    s_role = discord.utils.get(guild.roles, name="🥈・Silver")
    d_role = discord.utils.get(guild.roles, name="💎・Diamond")
    g_role = discord.utils.get(guild.roles, name="Gen access")
    for member in guild.members:
        if member.status == discord.Status.online or member.status == discord.Status.idle or member.status == discord.Status.dnd:
            if any(activity.name == 'Best free OGFN chair @ .gg/vDHcDfdwUX' for activity in member.activities if isinstance(activity, discord.CustomActivity)):
                if free_ex_role not in member.roles:
                    await member.add_roles(free_ex_role)
                    await member.add_roles(g_role)
                    embed = discord.Embed(
                        title="Thank you for supporting 1hAck FREE OGFN!",
                        description="You have been given the 🪐・Bronze role for setting your status to `Best free OGFN chair @ .gg/vDHcDfdwUX`! 🎉\n\nThank you for your support! If you have any questions, feel free to ask. 😊",
                        color=discord.Color.green()
                    )
                    await member.send(embed=embed)
            else:
                if free_ex_role in member.roles:
                    await member.remove_roles(free_ex_role)
                    await member.remove_roles(g_role)
                    # Send goodbye message if status removed
                    embed = discord.Embed(
                        title="We're sorry to see you leaving!",
                        description="It seems you have removed the status `Best free OGFN chair @ .gg/vDHcDfdwUX`. If you want to gain access back to the role, please set your status to `Best free OGFN chair @ .gg/vDHcDfdwUX` again. Thank you!",
                        color=discord.Color.red()
                    )
                    await member.send(embed=embed)

bot.run('')
