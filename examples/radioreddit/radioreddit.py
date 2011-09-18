# radioreddit stuff
import plugin

import urllib
import json
import time

try:
    import bitly
except ImportError:
    bitly = None

@plugin.command
def test(context):
    if context.args:
        return repr(context.args) + repr(context.line)
    else:
        return str(context.line)

@plugin.command
def foo(context):
    return 'test args: ' + repr(context.args)

@plugin.command
def crash():
    raise Exception

@plugin.command
def sleep(context):
    time.sleep(int(context.args))
    return 'slept for %d seconds.' % int(context.args)

@plugin.command
def status(context):
    stream = context.args
    streams = [
                'rock', 
                'electronic', 
                'hiphop', 
                'random', 
                'talk', 
                'indie'
                ]
    
    url = 'http://radioreddit.com/api/'
    
    if not context.args:
        urls = [url + '{0}/status.json'.format(stream) for stream in streams]
        urls.append(url + 'status.json')
        i = 0
        for url in urls:
            i += int(json.loads(urllib.urlopen(url).read())['listeners'])
        listeners = 'There are {0} listeners currently'.format(i)
        return listeners
    elif stream == 'main':
            status = urllib.urlopen(url + 'status.json')
    elif stream in streams:
            status = urllib.urlopen(url + '{0}/status.json'.format(stream))
    status = json.loads(status.read())['listeners']
    listeners = 'There are {0} listeners currently'.format(status)
    return listeners

@plugin.command
def np(context):
    '''usage: .np [stream]'''
        
    streams = [
            'rock', 
            'electronic', 
            'hiphop', 
            'random', 
            'talk', 
            'indie'
            ]
    
    if context.args in streams:
        url = 'http://radioreddit.com/api/{0}/status.json'
        results = urllib.urlopen(url.format(context.args))
    else:
        results = urllib.urlopen('http://radioreddit.com/api/status.json')
    
    results = json.loads(results.read())['songs']['song'][0]
    
    url = str(results['reddit_url'])
    result = chr(2) + results['title'] + chr(2) + ' -- ' + results['artist'] \
            + ' ' + '(Redditor: {0})'.format(results['redditor']) + ' ' + \
            (bitly.shorten(longurl=url)['url'] if bitly else url)
    if context.args:
        np = 'Now playing on the {0} stream: '.format(context.args) + result
    else:
        np = 'Now playing on Radio Reddit: ' + result
    return np

