# -*- coding: utf-8 -*-
import asyncio
import sys
from typing import IO

async def slow_print(msg: str, speed: float = 0.05, print_func=print):
    c = []
    s = ''
    for char in msg:
        if s == '' and char == '\033':
            c.append(char)
            s = 'e'
        if s == 'e' and char != 'm':
            c.append(char)
        if s == 'e' and char == 'm':
            c.append(char)
            s = ''
            print_func(''.join(c), end='', flush=True)
            c = []
        else:
            print_func(char, end='', flush=True)
            await asyncio.sleep(speed)
    print_func()


async def slow_print_to_io(msg: str, speed: float = 0.05, io: IO = sys.stdout):
    c = []
    s = ''
    for char in msg:
        if s == '' and char == '\033':
            c.append(char)
            s = 'e'
        if s == 'e' and char != 'm':
            c.append(char)
        if s == 'e' and char == 'm':
            c.append(char)
            s = ''
            io.write(''.join(c))
            io.flush()
            c = []
        else:
            io.write(char)
            io.flush()
            await asyncio.sleep(speed)
    io.write('\n')
