"""
Created on Aug 16, 2018

@author: StarlitGhost
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import dateutil.parser
import dateutil.tz
import re


@implementer(IPlugin, IModule)
class Mastodon(BotCommand):
    def actions(self):
        return super(Mastodon, self).actions() + [('urlfollow', 2, self.followURL)]

    def triggers(self):
        return ['cw']

    def help(self, query):
        if query and query[0].lower() in self.triggers():
            return {
                'cw': 'cw <toot URL> - displays the contents of toots with content warnings'
            }[query[0].lower()]
        else:
            return ('Automatic module that fetches toots from Mastodon URLs. '
                    'Also {}cw to display contents of toots with content warnings'
                    .format(self.bot.commandChar))

    def execute(self, message: IRCMessage):
        # display contents of a toot with a content warning
        if message.command == 'cw':
            if not message.parameters:
                return IRCResponse(ResponseType.Say,
                                   self.help(['cw']),
                                   message.replyTo)

            match = re.search(r'(?P<url>(https?://|www\.)[^\s]+)',
                              message.parameters,
                              re.IGNORECASE)
            if not match:
                return IRCResponse(ResponseType.Say,
                                   '{!r} is not a recognized URL format'.format(message.parameters),
                                   message.replyTo)
            follow = self.followURL(message, url=message.parameters, showContents=True)
            if not follow:
                return IRCResponse(ResponseType.Say,
                                   "Couldn't find a toot at {!r}".format(message.parameters),
                                   message.replyTo)
            toot, _ = follow
            return IRCResponse(ResponseType.Say, toot, message.replyTo)

    def followURL(self, _: IRCMessage, url: str, showContents: bool=False) -> [str, None]:
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        if not response:
            return

        # we'd check Server: Mastodon here but it seems that not every server
        # sets that correctly
        if 'Set-Cookie' not in response.headers:
            return
        if '_mastodon_session' not in response.headers['Set-Cookie']:
            return

        soup = BeautifulSoup(response.content, 'lxml')

        toot = soup.find(class_='entry-center')
        if not toot:
            # presumably not a toot, ignore
            return

        date = toot.find(class_='dt-published')['value']
        date = dateutil.parser.parse(date)
        date = date.astimezone(dateutil.tz.UTC)
        date = date.strftime('%Y/%m/%d %H:%M')

        name = toot.find(class_='p-name')
        name = self.translateEmojo(name).text.strip()
        user = toot.find(class_='display-name__account').text.strip()

        user = '{} ({})'.format(name, user)

        content = toot.find(class_='status__content')
        summary = content.find(class_='p-summary')
        if summary:
            summary = self.translateEmojo(summary).text.strip()
        text = content.find(class_='e-content')
        text = self.translateEmojo(text)
        # if there's no p tag, add one wrapping everything
        if not text.find_all('p'):
            text_children = list(text.children)
            wrapper_p = soup.new_tag('p')
            text.clear()
            text.append(wrapper_p)
            for child in text_children:
                wrapper_p.append(child)
        # replace <br /> tags with a newline
        for br in text.find_all("br"):
            br.replace_with('\n')
        # then replace consecutive <p> tags with a double newline
        lines = [line.text for line in text.find_all('p')]
        text = '\n\n'.join(lines)

        # strip empty lines, strip leading/ending whitespace,
        # and replace newlines with gray pipes
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        text = graySplitter.join(lines)

        formatString = str(colour(A.normal[A.fg.gray['[{date}]'],
                                           A.bold[' {user}:'],
                                           A.fg.red[' [{summary}]'] if summary else '',
                                           ' {text}' if not summary or showContents else '']))

        return formatString.format(date=date, user=user, summary=summary, text=text), ''

    def translateEmojo(self, tagTree):
        for img in tagTree.find_all('img', class_='emojione'):
            img.replace_with(img['title'])
        return tagTree


mastodon = Mastodon()
