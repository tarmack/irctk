import gevent
import json
import sys

import voxbot.irc
import voxbot.loader
import voxbot.reloader

class Bot(object):
    
    def __init__(self, settings):
        self.irc = voxbot.irc.Irc(settings)
        self.settings = settings
        self._event_loop()
    
    def reply(self, msg):
        if not self.sender == self.irc.nick:
            self.irc.msg(self.sender, msg)
        else:
            self.irc.reply(self.user, msg)
    
    def _event_loop(self):
        while True:
            bot = self.irc
            logger = self.irc.logger
            line = self.irc.lines.get()
            msgs = line['args'][-1]
            self.sender = line['args'][0]
            self.user = line['prefix'].split('!', 1)[0]
            owners = self.settings['owners']
            plugins = json.load(open('plugins.json'))
            
            try:
                voxbot.loader.load_plugins(bot, plugins)
                if msgs.startswith('^reload') and self.user in owners: 
                    plugins = json.load(open('plugins.json'))
                    plugin = msgs[msgs.find('^reload'):].split(' ', 1)[-1]
                    if not plugin == '^reload':
                        voxbot.reloader.reload_plugins('voxbot.' + plugin)
                        self.reply('Reloading {0}'.format(plugin))
                    else:
                        for plugin in plugins:
                            voxbot.reloader.reload_plugins('voxbot.' + plugin)
                        self.reply('Reloading plugins')
                
                if msgs.startswith('^help'):
                    loaded = ' '.join(plugins)
                    plugin = msgs[msgs.find('^help'):].split(' ', 1)[-1]
                    if plugin == '^help':
                        self.reply('Plugins loaded: ' + loaded)
                    elif plugin in plugins:
                        p = [p for p in plugins if p == plugin]
                        p = ''.join(p)
                        info = sys.modules[p].__dict__[p].__doc__
                        self.reply(str(info))
                    else:
                        self.reply('Plugin not found')
                
            except Exception, e: # catch all exceptions, don't die for plugins
                logger.warning('Error loading plugins: ' + str(e))


class Plugin(object):
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.owners = self.bot.settings['owners']
        self.msgs = self.bot.line['args'][-1]
        self.sender = self.bot.line['args'][0]
        self.command = self.bot.line['command']
        self.prefix =  self.bot.line['prefix']
        self.user = self.prefix.split('!')[0]
    
    def reply(self, msg, channel=None, action=False):
        '''Directs a response to either a channel or user. If `channel`,
        overrides the target.
        '''
        
        if action:
            msg =  chr(1) + 'ACTION ' + msg + chr(1)
        if channel:
            return self.bot.msg(channel, msg)
        if not self.sender == self.bot.nick:
            self.bot.msg(self.sender, msg)
        else:
            self.bot.reply(self.user, msg)
    
    @staticmethod
    def command(command):
        def _decorator(func):
            def _wrapper(self):
                args = self.msgs[self.msgs.find(command):].split(' ', 1)[-1]
                cmd = self.msgs[self.msgs.find(command):].split(' ', 1)[0]
                if self.msgs.startswith(command):
                    return func(self, cmd, args)
            return _wrapper
        return _decorator
    
    @staticmethod
    def event(event):
        def _decorator(func):
            def _wrapper(self):
                args = self.msgs
                if event in self.command:
                    return func(self, args)
            return _wrapper
        return _decorator