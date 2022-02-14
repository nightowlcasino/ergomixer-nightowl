"""
Proof Of Concept - Night Owl + ErgoMixer
"""

import os
import asyncio
import discord
from blockchain_actions import proxy_contract_builder, spend_proxy


client = discord.Client()
users = {}


async def run_actions(p2s, address, mixer_withdraws):
    await spend_proxy(p2s, address, mixer_withdraws)


@client.event
async def on_ready():
    """Respond to discord ready event"""
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    user = message.author
    channel = message.channel
    if message.content.startswith('!swap'):
        p2s = proxy_contract_builder(users[user])
        await message.channel.send(user.mention + " Please send input funds to ```"+p2s+"```")
        await asyncio.create_task(run_actions(p2s, users[user], []))

    if message.content.startswith('!Pswap '):
        withdraw_num = int(message.content[7])
        print(withdraw_num)
        mixer_withdraws = []
        p2s = proxy_contract_builder(users[user])
        for _ in range(withdraw_num):
            def check(response):
                return response.author == user and response.channel == channel

            msg = await client.wait_for('message', check=check)
            mixer_withdraws.append(msg.content)
        await message.channel.send(user.mention + " Please send input funds to ```"+p2s+"```")
        await asyncio.create_task(run_actions(p2s, users[user], mixer_withdraws))

    if message.content.startswith('!set wallet'):
        if len(message.content) == 63:
            users[message.author] = message.content[12:].strip()
            await message.channel.send(
                message.author.mention + ' Your wallet has been set to ' + users[message.author])

        else:
            await message.channel.send(message.author.mention + ' Your wallet is invalid, please try again')


client.run(os.getenv('TOKEN'))
