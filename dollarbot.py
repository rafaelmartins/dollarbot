#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
from datetime import datetime

import os
import visa # custom module

class DollarBot(irc.IRCClient):

    @property
    def nickname(self):
        return self.factory.nickname

    def _parse_username(self, user):
        return user.split('!')[0]

    def signedOn(self):

        # nickserv auth, if needed
        if self.factory.password is not None:
            self.msg('NickServ', 'IDENTIFY %s' % self.factory.password)

        # join channels
        for channel in self.factory.channels:
            self.join(channel)
        print "Signed on as %s." % self.nickname

    def joined(self, channel):
        print "Joined %s." % channel

    def privmsg(self, user, channel, msg):
        user = self._parse_username(user)
        pieces = msg.split()

        # !dollar command
        if len(pieces) == 1:
            if pieces[0] == '!dollar':
                self.msg(channel, '%s, cotação atual: %s (%s)' % \
                         (user, 1.0 / self.factory.visa.rate,
                          self.factory.visa.rate_date.strftime(
                              '%d/%m/%Y %H:%M:%S')))
            elif pieces[0] == '!dance':
                self.msg(channel, ':D\<')
                self.msg(channel, ':D/<')
                self.msg(channel, ':D|<')
                self.msg(channel, ':D\<')
                self.msg(channel, ':D/<')

        # conversion commands
        elif len(pieces) == 2 and pieces[0] in ('!brl', '!usd'):

            # validate value
            value = None
            try:
                value = float(pieces[1])
            except:
                pass
            if value is None:
                self.msg(channel, '%s, valor inválido: %s' % (user, pieces[1]))
                return

            talk = None

            # !usd
            if pieces[0] == '!brl':
                converted = self.factory.visa.reverse_convert(value)
                talk = '%s BRL = %s USD' % (value, converted)

            # !brl
            elif pieces[0] == '!usd':
                converted = self.factory.visa.convert(value)
                talk = '%s USD = %s BRL' % (value, converted)

            if talk is not None:
                self.msg(channel,
                         '%s, %s (%s)' % (user, talk,
                                          self.factory.visa.rate_date.strftime(
                                              '%d/%m/%Y %H:%M:%S')))


class DollarBotFactory(protocol.ClientFactory):

    protocol = DollarBot

    def __init__(self, channels, nickname, password=None):
        self.channels = channels
        self.nickname = nickname
        self.password = password
        self.visa = visa.VisaExchangeRate('USD', 'BRL', 3, 3600)

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % reason


if __name__ == "__main__":
    import local_settings as ls
    reactor.connectTCP(ls.HOST, ls.PORT, DollarBotFactory(ls.CHANNELS,
                                                          ls.NICKNAME,
                                                          ls.PASSWORD))
    reactor.run()
