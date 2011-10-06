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
    if not config['LOGFILE_DIR']:
        return
    if not os.path.exists(config['LOGFILE_DIR']):
        mess = _make_log_dir(config['LOGFILE_DIR'])
        if mess is not None:
            logger.error(mess)
            return
    
    message_handler = MessageHandler(config, maxBytes=config['MAX_LOGFILE_SIZE'])
    logger.addHandler(message_handler)

def _make_log_dir(path):
    done = '/'
    for name in os.path.split(path):
        if not os.path.isdir(done):
            return "Could not create log directory. '{0}' is not a directory.".format(done)
        done = os.path.join(done, name)
        if not os.path.exists(done):
            try:
                os.mkdir(done)
            except Exception, e:
                return 'Could not create log directory {0}.'.format(done, e)


class LogFileHandler(RotatingFileHandler):
    '''
    This is the handler for our logfiles. It is the basic RotatingFileHandler
    but it never destroys the logs. The logs get gzipped to safe space after
    two generations.
    '''
    
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
            except IOError, e:
                print "An error occurred while opening the file '{0}' to gzip it.\n\t{1}".format(filename, e)
                return
            try:
                compressed = gzip.open(filename + '.gz', 'wb')
            except IOError, e:
                print "An error occurred while opening the file '{0}' to gzip it.\n\t{1}".format(filename + '.gz', e)
                plain.close()
                return
            try:
                compressed.writelines(plain)
            except IOError, e:
                print "An error occurred while gzipping the file '{0}'.\n\t{1}".format(filename, e)
            finally:
                plain.close()
                compressed.close()
            try:
                os.remove(filename)
            except IOError, e:
                print 'Failed to remove the original log file ({0}) after gzipping it.\n\t{1}'.format(filename, e)
    
    def doRollover(self):
        '''
        This method gets called when the file is about to grow bigger than
        maxBytes. We use it to gzip older log backups.
        '''
        print 'doing rollover of logfile: {0}'.format(self.baseFilename)
        RotatingFileHandler.doRollover(self)
        self._tar_logs()


class MessageHandler(LogFileHandler):
    '''
    This class is used as the main logfile handler. It distributes the messages
    it gets to a multitude of logfiles according to their content.

    The messages are split over the logfiles as follows:
    * Private messages from and to a user get logged to one file per user.
    * Messages in a channel get logged to a file specific to that channel.
    * Errors get logged to the error log.
    * All other messages go to the main logfile.
    * Additionally messages from the server about channels get logged to both
      the main logfile and the channel specific logfile.
    * If DEBUG_TO_LOG is set all messages get copied to the debug file.
    '''
    
    def __init__(self, config, maxBytes=0):
        self.config = config
        self.users = {}
        self.channels = {}
        
        # Setup the main logfile.
        formatter = logging.Formatter(FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        message_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.log')
        LogFileHandler.__init__(self, message_file, maxBytes=maxBytes, backupCount=2)
        self.setLevel(logging.INFO)
        self.setFormatter(formatter)
        
        # Setup the error logfile.
        error_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.errors')
        self.error_handler = LogFileHandler(error_file,
                maxBytes=config['MAX_LOGFILE_SIZE'],
                backupCount=2)
        self.error_handler.setLevel(logging.ERROR)
        self.error_handler.setFormatter(formatter)
        
        # Setup and collect the channel logfiles
        for channel in config['CHANNELS']:
            channel_file = os.path.join(config['LOGFILE_DIR'], channel + '.log')
            channel_handler = LogFileHandler(channel_file,
                maxBytes=config['MAX_LOGFILE_SIZE'],
                backupCount=2)
            channel_handler.setLevel(logging.INFO)
            channel_handler.setFormatter(formatter)
            self.channels[channel] = channel_handler
        
        # When DEBUG_TO_LOG is set, setup the debug logfile.
        self.debug_handler = None
        if config['DEBUG_TO_LOG']:
            debug_file = os.path.join(config['LOGFILE_DIR'], config['SERVER'] + '.debug')
            self.debug_handler = LogFileHandler(debug_file,
                    maxBytes=config['MAX_LOGFILE_SIZE'],
                    backupCount=2)
            self.debug_handler.setLevel(logging.DEBUG)
            self.debug_handler.setFormatter(formatter)
    
    def _log_private(self, user, record):
        '''Logs the message to the logfile for `user`.'''
        handler = self._get_user_log(user)
        handler.emit(record)
    
    def _get_user_log(self, user):
        '''Returns the logfile for `user` it is created if it does not exist.'''
        if not user in self.users:
            filename = os.path.join(self.config['LOGFILE_DIR'], user + '.log')
            handler = LogFileHandler(filename, maxBytes=self.maxBytes, backupCount=2)
            handler.setLevel(logging.INFO)
            handler.setFormatter(self.formatter)
            self.users[user] = handler
        return self.users[user]
    
    def emit(self, record):
        '''Determine the correct destination logfile and write the message to it.'''
        message = record.getMessage()
        if self.debug_handler:
            self.debug_handler.emit(record)
        if 'PRIVMSG' in message:
            index = message.index('PRIVMSG') + 8
            target = message[index:].split()[0]
            if target == self.config['NICK']:
                target = message[1:].split('!')[0]
            if target in self.channels:
                self.channels[target].emit(record)
            else:
                self._log_private(target, record)
        elif record.levelname == 'ERROR':
            self.error_handler.emit(record)
        else:
            LogFileHandler.emit(self, record)
            for channel in self.channels:
                if channel in message:
                    self.channels[channel].emit(record)

