USE_PYCHARM_DEBUGGER = True
DEBUG_PORT = 41441

if 'PYCHARM_HOSTED' not in os.environ:
    print(
        '[!] This debug script is designed to be run under JetBrains PyCharm.')
    print('[!] However, no PyCharm was found in the environment.')
    print('[?] What would you like me to do?')
    print(' 1 - Attempt to run with PyCharm remote debugger anyway')
    print(' 2 - Run in debug mode without PyCharm remote debugger')
    print(' 3 - Quit')
    print(' > ')
    choice = input().strip()
    if choice == '1':
        pass
    elif choice == '2':
        USE_PYCHARM_DEBUGGER = False
    elif choice == '3':
        exit(0)
    else:
        print('[-] Unrecognized option, quitting...')
        exit(0)

if USE_PYCHARM_DEBUGGER:

    try:
        import pydevd_pycharm
    except ImportError:
        print('[!] Node pydevd_pycharm package found.')
        print('[!] The script will now attempt to install the latest version.')
        try:
            from pip import main as pip_main
        except ImportError:
            from pip._internal import main as pip_main
        try:
            pip_main(['install', 'pydevd_pycharm'])
        except SystemExit as e:
            print('[!] Unable to install package:')
            print(e)
            exit(0)
        else:
            print('[+] Package installed successfully.')
            import pydevd_pycharm
    finally:
        print('[*] Starting debug server')
        pydevd_pycharm.settrace('localhost', port=DEBUG_PORT,
                                stdoutToServer=True,
                                stderrToServer=True)
