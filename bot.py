import discord
from discord.ext import commands

from collections import deque
from typing import TypedDict

import logging

import os


MAX_QUEUE_SIZE = 128

logging.basicConfig(
    filename='discord_bot.log',  # Specify the log file name
    level=logging.INFO,  # Set the minimum logging level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
    filemode='a'  # 'a' for append (default), 'w' for overwrite
)

discord_intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=discord_intents)


class QueueEntry(TypedDict):
    entry_data: str
    user: str


queue: deque[QueueEntry] = deque(maxlen=MAX_QUEUE_SIZE)

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logging.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logging.error(f'Failed to sync commands: {e}')

@bot.tree.command(name='add_show', description='Add show to show queue')
async def add_to_queue(interaction: discord.Interaction, item: str):
    logging.info(f'Adding {item} to queue. User {interaction.user.display_name}')
    if len(queue) < MAX_QUEUE_SIZE:
        queue.append(QueueEntry(entry_data=item, user=interaction.user.display_name))
        embed = discord.Embed(
            title="✅ Item Added",
            description=f'Added "{item}" to the queue',
            color=discord.Color.green()
        )
        logging.info(f'Successful adding {item} to queue. User {interaction.user.display_name}')
        embed.add_field(name="Queue Position", value=f"{len(queue)}", inline=True)
        embed.add_field(name="Total Items", value=f"{len(queue)}", inline=True)
    else:
        embed = discord.Embed(
            title="❌ Item Not Added",
            description=f'Max queue size of {MAX_QUEUE_SIZE} has been reached',
            color=discord.Color.red()
        )
        logging.info(f'Failed to add {item} to show queue. Queue at capacity of {MAX_QUEUE_SIZE} User {interaction.user.display_name}')
    return interaction.response.send_message(embed=embed)

@bot.tree.command(name='list_shows', description='List all the shows in the show queue')
async def list_show_queue(interaction: discord.Interaction):
    if not queue:
        embed = discord.Embed(
            title="📋 Queue Status",
            description="The queue is empty",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="📋 Current Queue",
            color=discord.Color.blue()
        )
        
        queue_list = []
        for i, queue_item in enumerate(queue, 1):
            queue_list.append(f"{i}. Show: {queue_item['entry_data']}  Submitted by {queue_item['user']}")
        
        # Discord embed field has a 1024 character limit
        queue_text = "\n".join(queue_list)
        if len(queue_text) > 15:
            # If too long, truncate and show partial list
            queue_text = queue_text[:15] + "\n... (truncated)"
        
        embed.add_field(name="Items", value=queue_text, inline=False)
        embed.add_field(name="Total Items", value=f"{len(queue)}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name='next_show', description='Display the first item in the show queue')
async def next_show_in_queue(interaction: discord.Interaction):
    if not queue:
        embed = discord.Embed(
            title="❌ Show Queue Empty",
            description="The queue is empty",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="🎯 Next Show",
            description=f"\"{queue[0]['entry_data']}\", submitted by {queue[0]['user']}",
            color=discord.Color.green()
        )
    
        logging.info(f"Looked at next item")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='remove_next_show',  description='Remove the first item in the show queue')
async def remove_next_show(interaction: discord.Interaction):
    if not queue:
        embed = discord.Embed(
            title="❌ Show Queue Empty",
            description="The queue is empty",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="🎯 Next Removed Show",
            description=f"\"{queue[0]['entry_data']}\", submitted by {queue[0]['user']}",
            color=discord.Color.green()
        )
        removed = queue.popleft()
        logging.info(f"Removed item: {removed}")
    
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name='clear_show_queue',  description='Remove the first item in the queue')
async def clear_show_queue(interaction: discord.Interaction):
    if not queue:
        embed = discord.Embed(
            title="❌ Show Queue Empty",
            description="The queue is empty",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="🎯 Cleared Show Queue",
            description=f"\"{queue[0]['entry_data']}\", submitted by {queue[0]['user']}",
            color=discord.Color.green()
        )
        queue.clear()
        logging.info(f"Cleared queue. User {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)
        print(f"Error: {error}")


if __name__ == "__main__":
    token = os.environ.get('DISCORD_QUEUE_BOT')
    if token is not None:
        bot.run(token=token)