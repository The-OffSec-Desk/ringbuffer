#!/usr/bin/env python3
"""
Demo script: simulate parsing of segfault header + hex dump and show merging behavior.
"""
from core.parser import KernelLogParser
from core.engine import KernelLogEngine

header = "[102484.883686] zsh[2481341]: segfault at 10 ip 0000555a3852af74 sp 00007fff4e4b5fa0 error 4 in zsh[79f74,555a384b1000+b9000] likely on CPU 4 (core 14, socket 0)"
code = "[102484.883703] Code: f6 74 08 85 c9 0f 84 db 01 00 00 45 31 e4 89 c2 81 e2 ff ff bf ff 89 53 10 a9 00 00 00 01 75 0d 48 8b 43 20 44 89 f6 48 89 df <ff> 50 10 48 83 7b 30 00 74 1a 48 8b 7b 08 e8 49 7a f8 ff 48 8b 7b"

print('Parsing header...')
e1 = KernelLogParser.parse_dmesg_line(header, source='dmesg')
print('Header parsed:', e1.to_dict())
print('\nParsing code line...')
e2 = KernelLogParser.parse_dmesg_line(code, source='dmesg')
print('Code parsed:', e2.to_dict())

# Simulate engine merging
engine = KernelLogEngine()
engine.buffer.append(e1)
print('\nEngine buffer before merge:')
for ev in engine.get_buffer():
    print('-', ev.event_id, ev.severity, ev.subsystem, 'message_len=', len(ev.message))

# Emulate arrival of continuation event
is_cont = e2.annotations.get('continuation', False)
print('\nContinuation flag on code line:', is_cont)
if is_cont:
    last = engine.buffer[-1]
    last.message = (last.message or '') + '\n' + (e2.message or '')
    last.raw = (last.raw or '') + '\n' + (e2.raw or '')
    last.annotations.update(e2.annotations or {})

print('\nEngine buffer after merge:')
for ev in engine.get_buffer():
    print('Event ID:', ev.event_id)
    print('Severity:', ev.severity)
    print('Subsystem:', ev.subsystem)
    print('PID:', ev.pid)
    print('Message (first 200 chars):')
    print(ev.message[:200])
    print('\nRaw (first 200 chars):')
    print(ev.raw[:200])
    print('\nAnnotations:', ev.annotations)

print('\nDemo complete.')
