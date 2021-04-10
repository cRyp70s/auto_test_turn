# auto_test_turn
Script to automatically test STUN/TURN server(s).
<br>
# Usage
<pre>
test_turn_server.py [-h] [-i] [-s SERVER]

Automate turn/stun server testing with selenium.

optional arguments:
  -h, --help            show this help message and exit
  -i, --interactive     Test in interactive mode.
  -s SERVER, --server SERVER
                        URL of stun/turn server (should be in the form:
                        'turn:server_name[:port[:username:password]]' or
                        'stun:server_name[:port[:username:password]]' or it
                        could be a path to a file containing lines of valid
                        turn/stun url).
                        </pre>
