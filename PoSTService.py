#!/usr/bin/env python

import binascii
import subprocess
import sys
import os

from Xlib import X, display, Xutil, Xatom
import pyautogui

import PySimpleGUI as sg

from math_eval import compute, safe_compute

def log(msg, *args):
    sys.stderr.write(msg.format(*args) + '\n')

def error(msg, *args):
    log(msg, *args)
    sys.exit(1)

def main():
    
    '''
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        sys.exit('usage: {0} SELECTION [TYPE]\n\n'
                 'SELECTION is typically PRIMARY, SECONDARY or CLIPBOARD.\n'
                 'If TYPE is omitted, the available types for the selection are listed.'
                 .format(sys.argv[0]))
    '''

    d = display.Display()

    sel_name = "PRIMARY"
    sel_atom = d.get_atom(sel_name)

    '''
    if len(sys.argv) > 2:
        target_name = sys.argv[2]
        target_atom = d.get_atom(target_name)
    else:'
    '''
    #target_name = 'TARGETS'
    target_name = 'UTF8_STRING'
    target_atom = d.get_atom(target_name)

    # Ask the server who owns this selection, if any
    owner = d.get_selection_owner(sel_atom)

    if owner == X.NONE:
        log('No owner for selection {0}', sel_name)
        return

    log('selection {0} owner: 0x{1:08x} {2}',
        sel_name, owner.id, owner.get_wm_name())

    # Create ourselves a window and a property for the returned data
    w = d.screen().root.create_window(
        0, 0, 10, 10, 0, X.CopyFromParent)
    w.set_wm_name(os.path.basename(sys.argv[0]))

    data_atom = d.get_atom('SEL_DATA')

    # The data_atom should not be set according to ICCCM, and since
    # this is a new window that is already the case here.

    # Ask for the selection.  We shouldn't use X.CurrentTime, but
    # since we don't have an event here we have to.
    w.convert_selection(sel_atom, target_atom, data_atom, X.CurrentTime)

    # Wait for the notification that we got the selection
    while True:
        e = d.next_event()
        if e.type == X.SelectionNotify:
            break

    # Do some sanity checks
    if (e.requestor != w
        or e.selection != sel_atom
        or e.target != target_atom):
        error('SelectionNotify event does not match our request: {0}', e)

    if e.property == X.NONE:
        log('selection lost or conversion to {0} failed',
            target_name)
        return

    if e.property != data_atom:
        error('SelectionNotify event does not match our request: {0}', e)

    # Get the data
    r = w.get_full_property(data_atom, X.AnyPropertyType,
                            sizehint = 10000)

    # Can the data be used directly or read incrementally
    if r.property_type == d.get_atom('INCR'):
        log('reading data incrementally: at least {0} bytes', r.value[0])
        read_incremental(d, w, data_atom, target_name)
    else:
        handle_data(d, r, target_name)

    # Tell selection owner that we're done
    w.delete_property(data_atom)

def read_incremental(d, w, data_atom, target_name):
    # This works by us removing the data property, the selection owner
    # getting a notification of that, and then setting the property
    # again with more data.  To notice that, we must listen for
    # PropertyNotify events.
    w.change_attributes(event_mask = X.PropertyChangeMask)

    while True:
        # Delete data property to tell owner to give us more data
        w.delete_property(data_atom)

        # Wait for notification that we got data
        while True:
            e = d.next_event()
            if (e.type == X.PropertyNotify
                and e.state == X.PropertyNewValue
                and e.window == w
                and e.atom == data_atom):
                break

        r = w.get_full_property(data_atom, X.AnyPropertyType,
                                sizehint = 10000)

        # End of data
        if len(r.value) == 0:
            return

        handle_data(d, r, target_name)
        # loop around



def handle_data(d, r, target_name):
    log('got {0}:{1}, length {2}',
        d.get_atom_name(r.property_type),
        r.format,
        len(r.value))

    if r.format == 8:
        if r.property_type == Xatom.STRING:
            value = r.value.decode('ISO-8859-1')
        elif r.property_type == d.get_atom('UTF8_STRING'):
            value = r.value.decode('UTF-8')
        else:
            value = binascii.hexlify(r.value).decode('ascii')
        sys.stdout.write(value)
        sys.stdout.write('\n')
        serviceResult = perform_service(value)
        if serviceResult is not None:
            sys.stdout.write(serviceResult)
            pyautogui.typewrite(serviceResult)
            sys.stdout.write('\n')
        
    # 6*9 6*9 6*9 6*9 


    elif r.format == 32 and r.property_type == Xatom.ATOM:
        for v in r.value:
            sys.stdout.write('{0}\n'.format(d.get_atom_name(v)))

    else:
        for v in r.value:
            sys.stdout.write('{0}\n'.format(v))

def perform_service(value):
    layout = [[sg.Button("*M*ath Eval")], [sg.Button("*W*iki*P*edia Lookup")], [sg.Cancel()]]
    window = sg.Window("PoSTServices", layout)

    serviceResult = None
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Exit"):
            break
        if event == "*M*ath Eval":
            serviceResult = str(safe_compute(value))
            window.close()
        if event == "*W*iki*P*edia Lookup":
            url = 'https://en.wikipedia.org/w/index.php?search='+value
            sys.stdout.write(url)
            sys.stdout.write('\n')
            subprocess.Popen(['xdg-open', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            window.close()
    
    return serviceResult

if __name__ == '__main__':
    main()