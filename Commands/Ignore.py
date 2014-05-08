'''
Created on Dec 01, 2013

@author: Tyranic-Moron
'''

from IRCMessage import IRCMessage
from IRCResponse import IRCResponse, ResponseType
from CommandInterface import CommandInterface
import GlobalVars
from Data import ignores

import re

class Command(CommandInterface):
    triggers = ['ignore']
    help = 'ignore <user> - ignore all lines from the specified user'

    def onStart(self):
        if ignores.ignoreList is None:
            ignores.loadList()

    def __del__(self):
        if ignores.ignoreList is not None and 'Unignore' not in GlobalVars.commands:
            ignores.ignoreList = None

    def execute(self, message):
        if message.User.Name not in GlobalVars.admins:
            return IRCResponse(ResponseType.Say, 'Only my admins can edit the ignore list', message.ReplyTo)

        if len(message.ParameterList) > 0:
            for user in message.ParameterList:
                if user.lower() not in ignores.ignoreList:
                    ignores.ignoreList.append(user.lower())

            ignores.saveList()

            output = 'Now ignoring user(s) {0}'.format(', '.join(message.ParameterList))

            return IRCResponse(ResponseType.Say, output, message.ReplyTo)

        else:
            if ignores.ignoreList is not None and len(ignores.ignoreList) > 0:
                return IRCResponse(ResponseType.Say, 'Ignored users: {0}'.format(', '.join( sorted(ignores.ignoreList) )), message.ReplyTo)
            else:
                return IRCResponse(ResponseType.Say, 'Not currently ignoring anyone!', message.ReplyTo)