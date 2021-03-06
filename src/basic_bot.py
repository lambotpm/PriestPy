# -*- coding: utf-8 -*-

import discord
from discord import Forbidden
from discord.ext import commands
import random
from dict import DictionaryReader
from botkey import Key
from subprocess import call
import sys
from priestLogger import PriestLogger
import logging
import time
from discord import HTTPException

logging.basicConfig(level=logging.INFO)

client = discord.Client()

prefix = Key().prefix()

logger = PriestLogger()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    r = DictionaryReader()
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
        
    if message.content.startswith(prefix):
        await messageHandler(message)
        
    if message.channel.name != None and message.channel.name in r.logChannels():
        logger.log(message)    
                 
@client.event
async def on_member_join(member):
    await sendWelcomeMessage(member)
    await logAction(member, 'joined')

@client.event   
async def on_member_remove(member):
    print('member left')
    await logAction(member, 'left')
    
@client.event
async def on_member_ban(member):
    await logAction(member, 'banned')
    
@client.event
async def on_member_unban(member):
    await logAction(member, 'unbanned')

async def logAction(member, action):
    r = DictionaryReader()
    if member.server:
        await client.send_message(client.get_channel(r.actionLogChannel()), '['+time.strftime("%Y-%m-%d %H:%M:%S")+'] {0.server.name} - {0.name} ({0.id}) {1}'.format(member, action))
    else:
        await client.send_message(client.get_channel(r.actionLogChannel()), 'No Server - {0.name} ({0.id}) {1}'.format(member, action))
    #print('error while writing {0} log'.format(action))

            
async def messageHandler(message):
    if message.server:
        await client.send_message(client.get_channel('220534135947526154'), '{0.server.name} - {0.channel.name} - {0.author} invoked {0.content}'.format(message))
    else:
        await client.send_message(client.get_channel('220534135947526154'), 'PM - PM - {0.author} invoked {0.content}'.format(message))
    
    if message.content.startswith(prefix+'fullupdate') or message.content.startswith(prefix+'update') or message.content.startswith(prefix+'channel'):
        await maintenanceMessages(message)

    elif message.content.startswith(prefix+'send'):
        await forwardMessage(message)
        
    elif message.content.startswith(prefix+'item'):
        await itemMessage(message)
    
    elif message.content.startswith(prefix+'pin') or message.content.startswith(prefix+'pins'):
        await sendPinMessages(message)
        
    elif message.content.startswith(prefix+'channel'):
        await client.send_message(message.channel, message.channel.id)
        
    else:
        await generalMessage(message)

async def maintenanceMessages(message):
    if message.content.startswith(prefix+'update'):
        call(["git","pull"])
    p = DictionaryReader()
    if message.content.startswith(prefix+'fullupdate'): 
        if message.author.id not in p.admins():
            await client.send_message(message.channel, 'You\'re not my dad, {0.mention}!'.format(message.author))
            return
        call(["git","pull"])
        call(["start_bot.sh"])
        sys.exit()

async def forwardMessage(message):
    p = DictionaryReader()
    roles = message.author.roles
    canSend = False
    for role in roles:
        canSend = canSend or (role.name in p.roles())
    if not canSend:
        print('{0.author.name} can\'t send whispers'.format(message))
        return
    entries = message.content.split(' ')
    target = message.mentions[0]
    if target != None:
        entry = ' '.join(entries[2::])
        msg = p.commandReader(entry)
        if msg != None:
            await client.send_message(target, msg)
            await client.delete_message(message)    
            await client.send_message(message.author, 'Message sent to {0.mention}'.format(target))
        else:
            await client.send_message(message.channel, 'Invalid Message, {0.mention}'.format(message.author))

async def itemMessage(message):
    p = DictionaryReader()
    msg = p.itemReader(message.content[1::])
    await client.send_message(message.channel, msg)
    
async def sendWelcomeMessage(member):
    p = DictionaryReader()
    msg = p.commandReader('help')
    await client.send_message(member, msg)
    
async def sendPinMessages(message):
    pins = await client.pins_from(message.channel)
    size = 10
    count = 0
    command = message.content.split(' ')
    try:
        await client.delete_message(message)
    except (HTTPException, Forbidden):
        print('Error deleting message, probably from whisper')
    if len(command) > 1:
        size = int(command[1]) if isinstance(command[1], int) else 10
        
    for msg in pins:
        if count >= size:
            return
        if msg.content:
            await client.send_message(message.author, '``` Pin '+ str(count+1) + ' ```')
            await client.send_message(message.author, msg.content)
        count += 1

async def generalMessage(message):
    p = DictionaryReader()
    try:
        roles = len(message.author.roles)
    except Exception:
        roles = 10
    command = message.content[1::].split(' ')[0].lower()
    msg = p.commandReader(message.content[1::],message.channel.name)
    if msg != None:
        if command in p.whisperCommands():
            if command == 'pub' and roles > 1 and 'help' not in message.content:
                await client.send_message(message.channel, msg)
            else:
                await client.send_message(message.author, msg)
                try:
                    await client.delete_message(message)
                except (HTTPException, Forbidden):
                    print('Error deleting message, probably from whisper')
        else:
            await client.send_message(message.channel, msg)
    else:
        msg = p.commandReader('invalid',message.channel.name)
        await client.send_message(message.author, msg)        
        try:
            await client.delete_message(message)
        except (HTTPException, Forbidden):
            print('Error deleting message, probably from whisper')

client.run(Key().value())
