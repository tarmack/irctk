
import inspect
from irctk import Bot

bot = Bot()

def command(command=None, **kwargs):
    '''This method provides a decorator that can be used to load a
    function into the global plugins list.:

    If the `command` arument is provided the decorator will assign the command
    key to the value of `command`, update the `plugin` dict, and then return
    the wrapped function to the wrapper.

    Therein the plugin dictionary is updated with the `func` key whose
    value is set to the wrapped function.

    Otherwise if no `command` parameter is passed the, `command` is assumed to
    be the wrapped function and handled accordingly.
    '''

    plugin = {}

    def wrapper(func):
        plugin.setdefault('hook', func.func_name)
        plugin['funcs'] = [func]
        plugin['help'] = func.__doc__ if func.__doc__ else 'no help provided'
        bot._update_plugins(plugin, 'PLUGINS')
        return func

    if kwargs or not inspect.isfunction(command):
        if command:
            plugin['hook'] = command
        plugin.update(kwargs)
        return wrapper
    else:
        return wrapper(command)

def event(event=None, **kwargs):
    '''This method provides a decorator that can be used to load a 
    function into the global events list.
    
    It assumes one parameter, `event`, i.e. the event you wish to bind 
    this wrapped function to. For example, JOIN, which would call the 
    function on all JOIN events.
    '''
    
    plugin = {}
    
    def wrapper(func):
        plugin['funcs'] = [func]
        bot._update_plugins(plugin, 'EVENTS')
        return func
    
    plugin['hook'] = event
    plugin.update(kwargs)
    return wrapper

def add_command(command, function):
    ''' Binds `function` to `command`. '''
    return bot._add_plugin(command, function, command=True)

def add_event(event, function):
    ''' Binds `function` to `event`. '''
    return bot._add_plugin(event, function, event=True)

def remove_command(command, function):
    ''' Stop executing `function` on `command`. '''
    return bot._remove_plugin(command, function, command=True)

def remove_event(event, function):
    ''' Stop executing `function` on `event`. '''
    return bot._remove_plugin(event, function, event=True)

def reply(message, context):
    ''' Send a reply to the user or chanel the command or event came from. '''
    return bot._reply(message, context, action=False, notice=False)

def action(action, context):
    ''' Send an action to the user or chanel the command or event came from. '''
    return bot._reply(action, context, action=True, notice=False)

def notice(notice, context):
    ''' Send a notice to the user or chanel the command or event came from. '''
    return bot._reply(notice, context, action=False, notice=True)

