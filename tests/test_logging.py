import unittest

from irctk import logging
import logging as log
import os


class LoggerTestCase(unittest.TestCase):
    
    def setUp(self):
        self.logger = logging.create_logger()
        
        self.assertTrue(isinstance(self.logger, log.Logger))
    
    def test_set_logfiles(self):
        tmp_dir = '/tmp/irctk_test'
        config = {
                'SERVER'            : 'irc.test.local',
                'CHANNELS'          : ['#testing'],
                'LOG_TO_FILE'       : False,
                'LOGFILE_DIR'       : os.path.join(tmp_dir, 'logs'),
                'MAX_LOGFILE_SIZE'  : 1024, # Test with really small size so rollover will happen.
                'DEBUG_TO_LOG'      : False,
                }
        logging.set_logfiles(config)
        log_dir = os.path.join(tmp_dir, 'logs')
        
        self.assertTrue(os.path.exists(log_dir))
        self.assertTrue(os.path.exists(log_dir + '/irc.test.local.log'))
        self.assertTrue(os.path.exists(log_dir + '/irc.test.local.errors'))
        self.assertTrue(os.path.exists(log_dir + '/#testing.log'))
    
    def test_rollover(self):
        pass
    
    def test_private(self):
        pass


if __name__ == '__main__':
    unittest.main()

