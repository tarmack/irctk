'''
    irctk.logger
    ------------
    
    Creates the logging object `logger`.
'''

from __future__ import absolute_import

import os
import gzip
import logging
from logging.handlers import RotatingFileHandler

FORMAT = '%(asctime)s %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'

def create_logger():
    logger = logging.getLogger('irctk')
    logger.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    
    return logger

def set_logfiles(config):
    logger = logging.getLogger('irctk')
    if config['LOGFILE_DIR']:
        if not os.path.exists(config['LOGFILE_DIR']):
            mess = _make_log_dir(config['LOGFILE_DIR'])
            if mess is not None:
                logger.error(mess)
                return
        
        formatter = logging.Formatter(FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        
        error_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.errors')
        error_handler = LogFileHandler(error_file,
                maxBytes=config['MAX_LOGFILE_SIZE'],
                backupCount=2)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        message_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.log')
        message_handler = MessageHandler(config, message_file,
                maxBytes=config['MAX_LOGFILE_SIZE'])
        message_handler.setLevel(logging.INFO)
        message_handler.setFormatter(formatter)
        logger.addHandler(message_handler)
        
        for channel in config['CHANNELS']:
            channel_file = os.path.join(config['LOGFILE_DIR'], channel + '.log')
            channel_handler = ChannelHandler(channel, channel_file,
                maxBytes=config['MAX_LOGFILE_SIZE'])
            channel_handler.setLevel(logging.INFO)
            channel_handler.setFormatter(formatter)
            logger.addHandler(channel_handler)
        
        if config['DEBUG_TO_LOG']:
            debug_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.debug')
            debug_handler = LogFileHandler(debug_file,
                    maxBytes=config['MAX_LOGFILE_SIZE'],
                    backupCount=2)
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(formatter)
            logger.addHandler(debug_handler)


def _make_log_dir(path):
    done = '/'
    for name in os.path.split(path):
        if not os.path.isdir(done):
            return "Could not create log directory. '{0}' is not a directory.".format(done)
        done = os.path.join(done, name)
        if not os.path.exists(done):
            try:
                os.mkdir(done)
            except:
                return 'Could not create directory {0}.'.format(done)


class LogFileHandler(RotatingFileHandler):
    
    def _tar_logs(self):
        '''Looks for old log files from this handler and tars them.'''
        filename = self.baseFilename + '.' + str(self.backupCount)
        log_dir, filebase = os.path.split(self.baseFilename)
        if os.path.exists(filename) and os.path.isfile(filename):
            
            dir_listing = [f for f in os.listdir(log_dir) if
                    f.startswith(filebase) and f.endswith('.gz')]
            dir_listing.sort(reverse=True)
            for archive in dir_listing:
                basename, i, ext = archive.rsplit('.', 2)
                new_name = os.path.join(log_dir, '.'.join((basename, str(int(i) + 1), ext)))
                archive = os.path.join(log_dir, archive)
                os.rename(archive, new_name)
            
            try:
                plain = open(filename, 'rb')
            except IOError:
                return
            try:
                compressed = gzip.open(filename + '.gz', 'wb')
            except IOError:
                plain.close()
                return
            try:
                compressed.writelines(plain)
            finally:
                plain.close()
                compressed.close()
            try:
                os.remove(filename)
            except IOError:
                print 'Failed to remove old log file.'
                pass
    
    def doRollover(self):
        print 'doing rollover of file:', self.baseFilename
        RotatingFileHandler.doRollover(self)
        self._tar_logs()


class ChannelHandler(LogFileHandler):
    def __init__(self, channel, filename, maxBytes=0):
        LogFileHandler.__init__(self, filename, maxBytes=maxBytes, backupCount=2)
        self.channel = channel
    
    def emit(self, record):
        message = record.getMessage()
        if self.channel in message and not 'ERROR' in message:
            LogFileHandler.emit(self, record)


class MessageHandler(LogFileHandler):
    def __init__(self, config, filename, maxBytes=0):
        LogFileHandler.__init__(self, filename, maxBytes=maxBytes, backupCount=2)
        self.config = config
        self.users = {}
    
    def _log_private(self, user, record):
        handler = self._get_user_log(user)
        handler.emit(record)
    
    def _get_user_log(self, user):
        if not user in self.users:
            filename = os.path.join(self.config['LOGFILE_DIR'], user + '.log')
            handler = LogFileHandler(filename, maxBytes=self.maxBytes, backupCount=2)
            handler.setLevel(logging.INFO)
            handler.setFormatter(self.formatter)
            self.users[user] = handler
        return self.users[user]
    
    def emit(self, record):
        message = record.getMessage()
        if 'PRIVMSG' in message:
            index = message.index('PRIVMSG') + 8
            user = message[index:].split()[0]
            if user == self.config['NICK']:
                user = message[1:].split('!')[0]
            self._log_private(user, record)
        elif 'ERROR' in message:
            return
        else:
            do_log = True
            for channel in self.config['CHANNELS']:
                if channel in message:
                    do_log = False
                    break
            if do_log:
                LogFileHandler.emit(self, record)

