#!/bin/env python

from irctk import Bot

bot = Bot()
bot.config.from_pyfile('settings.cfg')

import radioreddit
import unobot

if __name__ == '__main__':
    bot.run()
