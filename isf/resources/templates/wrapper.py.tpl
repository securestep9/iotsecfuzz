import sys
import subprocess
import tempfile

if len(sys.argv) < 2:
    print('[!] No entry point specified')
    exit(0)

file = sys.argv[1]
print('[*] Starting wrapper script for %s' % file)

if sys.platform.startswith('win'):
    # Windows
    cmd = ['python', file]
    subprocess.run(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

elif sys.platform == 'darwin':
    # OS X
    # Not tested yet
    cmd = ['python', "'%s'" % file]
    with tempfile.NamedTemporaryFile(suffix='.command') as f:
        f.write('#!/bin/sh\n%s\n' % ' '.join(cmd))
        subprocess.call(['open', '-W', f.name])

else:
    # Linux
    # TODO test with gnome-terminal
    cmd = ['python', "'%s'" % file]
    subprocess.call(
        ' '.join(['x-terminal-emulator', '-e', "%s" % ' '.join(cmd)]),
        shell=True)
