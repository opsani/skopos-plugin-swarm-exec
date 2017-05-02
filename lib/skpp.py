from __future__ import print_function
#
# skpp.py - Helper for implementing Skopos plugins as python modules
#
# Copyright (c) 2017, Datagrid Systems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# License template: http://opensource.org/licenses/BSD-2-Clause
#                   (as accessed on June 2, 2015)
"""
SKopos Python Plugin helper.

Common code for Skopos plugins implemented in Python. This allows coding a
plugin like a Python module (which can be imported and used by other plugins,
too) and run it easily using the executable plugin interface.

Use:
import skpp

def my_action(...): ...

if __name__ == "__main__":
    skpp.run("my_plugin_name", globals())

see help(run) for details.
"""

import sys
import os.path

import argparse
import json

ERR_EXIT_CODE=2

gbl_debug=False

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(ERR_EXIT_CODE)

def dbg_print(*args, **kwarg):
    if gbl_debug:
        if 'file' not in kwarg:
            kwarg['file'] = sys.stderr # print to stderr in order not to disrupt stdout json object
        print(*args, file=sys.stderr)

class _cond_trace(object):

    def __init__(self, die=None, trace=False):
        '''use: with _cond_trace([die=function],trace=True|False): do_some_stuff
        run some code and trap all exceptions (limited to those that are derived from Exception).
        If trace is set, traceback is displayed. If die is set, it must be callable and return
        a string. The returned string will be used as the argument to die() (which will EXIT the process)
        If die is not set, execution will continue.'''

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, tracebuf):
        if exc_type is not None:
            if not isinstance(exc_type,Exception):
                return False # not a normal exception, re-raise silently and let Python deal with it
            if self.trace:
                import traceback
                traceback.print_exception(exc_type,exc_value,tracebuf)
            if self.die:
                die(self.die()+': {}'.format(repr(exc_value)))
            return True # don't re-raise the exception
        return False    # ret value is ignored if no exception

# decorator for 'utility' actions which don't expect 'stdin'
def cmd(f):
    f.__call__ # fail if f not callable
    f._skpp_nostdin_ = True
    return f

def _is_cmd(f):
    return getattr(f,'_skpp_nostdin_',False)

# no-op (for now) decorator, can be used to tag a function as being plugin
# action
def action(f):
    f.__call__ # fail if f not callable
    return f


def args2dict(args):
    '''convert an array of strings (such as sys.argv or portion thereof) to a dict, using the following rules on each
       input string:
       string is  | result
       x=y        | output[x] = y
       x=y1,y2,y3 | output[x] = [y1,y2,y3] (use x=y1, to make a one-element array)
       -x, --x    | output[x] = True
       --x=y      | same as x=y
       other      | output['_args'].append(x)
    '''

    other = []
    output = {}
    for s in args:
        a = s.split('=',1)
        if len(a) == 2:
            k,v = a
            if k.startswith('--'): k=k[2:]
            if v.find(',') >= 0: # array
                if v.endswith(','): v = v[:-1]
                v = v.split(',')
            output[k] = v
        else:
            k = a[0]
            if k.startswith('--'): # --long-option
                output[k[2:]] = True
            elif len(k) == 2 and k.startswith('-'): # -x short option
                output[k[1:]] = True
            else:
                other.append(k)

    output['_args'] = other
    output['_allargs'] = args
    return output


def run(display_name, ns):
    '''Parse the command line (sys.argv), use the first non-option argument as 'action' - a function name to call.
    Lookup the function name in ns. If ns is a dict, the lookup is done as ns[name], otherwise the object's attributes
    are searched. You can use globals() to have the name looked up in the calling module's globals, or use any
    object, such as a module or a class as the 'namespace', e.g.: import other_plugin ; skpp.run(otherplugin).

    Read stdin and interpret it as json data, pass it to the action function as **kwargs.

    The value returned from the function is converted to json and printed to stdout.
    '''

    # parse command line
    parser = argparse.ArgumentParser(display_name)
    #parser.add_argument('--dry-run', help = 'verify command and parameters instead of running')
    #parser.add_argument('--display', '-d', action = "store_true", help = "display instead of executing")
    #parser.add_argument('--verbose', '-v', action = "store_true", help = "verbose")
    parser.add_argument('--debug', action = "store_true", help = "show additional debug info on some errors")
    parser.add_argument('--compact', '-c', action = "store_true", help = "output compact JSON instead of pretty")
    parser.add_argument('--stdout', help = "redirect normal output to file")
    parser.add_argument('--stderr', help = "redirect error output to file")
    parser.add_argument('action')
    args, extra   = parser.parse_known_args()

    # redirect stdout/stderr if requested, so everything else will go where requested
    # note: if a file cannot be open, exception trace will go to the old stderr
    if args.stdout and args.stdout == args.stderr:      # if both redirected to the same file
        sys.stdout = sys.stderr = open(args.stdout, 'w')
    else:
        if args.stdout: sys.stdout = open(args.stdout, 'w')
        if args.stderr: sys.stderr = open(args.stderr, 'w')

    # set global debug for debug printing
    global gbl_debug
    gbl_debug = args.debug

    # get action to call (key or attribute of ns), checking in the process that it exists and is callable
    try:
        if isinstance(ns,dict):
            action = ns[args.action]
        else:
            action = getattr(ns, args.action)
        # same as callable()? but likely works with more pythons, see http://bugs.python.org/issue10518
        action.__call__ # raise AttributeError if not callable
    except (KeyError,AttributeError) as e:
        # provide default 'nop' handler for a few actions
        if args.action in ('preflight','postflight'):
            def action(**args): pass
        else:
            die("Plugin {} does not support action {}".format(display_name, args.action))

    is_cmd = _is_cmd(action)
    # read stdin (it should be small enough to fit easily in memory)
    kwargs = {}
    if is_cmd:
        kwargs = args2dict(extra)
    else:
        # read arguments from stdin or command line (JSON object in string form)
        if extra:
            src = ' '.join(extra)       # should really be one argument
        else:
            try:
                src = sys.stdin.read()
            except Exception as e:
                die('Failed to read input data for plugin {}: {}'.format(display_name, e))

        # convert from JSON
        with _cond_trace(lambda:'Failed to parse input data for plugin {}'.format(display_name), args.debug):
            if src:
                kwargs = json.loads(src)
            else:
                kwargs = {}

        #TBD kwargs.update( args2dict(extra) ) - use cmd-line keys for actions, as well?

    # call action
    with _cond_trace(lambda:'Plugin {} action {} failed'.format(display_name, args.action), args.debug):
        #print('Plugin {}, Action {}, arguments {}'.format(display_name, args.action, src))
        dst = action(**kwargs)
        #print('Returned {}'.format(dst))

    if is_cmd:
        quit() ######@@@

    if dst is None: # return empty dict, if the handler returned nothing at all
        dst = {}

    if isinstance(dst,dict):
        dst.pop('_args',None) # FIXME plugins have the bad habit of returning everything they were given, remove some junk
        dst.pop('_allargs',None)

    # convert results to JSON
    with _cond_trace(lambda:'Plugin {} action {} failed to encode output'.format(display_name, args.action),args.debug):
        #TODO: the operation actually succeeded... communicate this?
        dst = json.dumps(dst, indent = (2 if not args.compact else 0))
        print(dst)

# TODO: get rid of this and have init handle the 'normal' inst_describe() data
def format_describe_for_init(state_desc):
    '''reformat the regular inst_describe output into the form expected by
    the init action.'''
    from collections import defaultdict
    raw_comps = state_desc['inst']
    comps = defaultdict(list)
    for c in raw_comps:
        comp_name = c.pop('component') # exclude component name from inst list
        comps[comp_name].append(c)
    comps = dict(comps)
    for c in comps.values():
        c.sort(key = lambda x: x.get('index',0))

    return dict(inst = comps)
