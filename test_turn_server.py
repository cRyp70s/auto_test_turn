from selenium import webdriver
import time
from selenium.webdriver.firefox.options import Options
import re
import os.path as pth
import sys
import argparse

class TrickleIce:
    def __init__(self):
        """
            Start firefox webdriver in headless mode and open the trickle ice page.
            
            self.results will be a set of tuples containing the boolean True or False
            depending on test result and a tuple of the servername and/or the credentials.
        """
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        self.driver.get("https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/")
        self.results = set()

    @staticmethod
    def match_turn_or_stun(url):
        """Check if url is turn or stun protocol and return
            the appropraite value.
        """
        stun_regexp = re.compile("^stun:.+")
        turn_regexp = re.compile("^turn:.+")
        if stun_regexp.match(url):
            return 'stun'
        elif turn_regexp.match(url):
            return 'turn'
        else:
            return False
            
    def match_turn_or_stun_merged(url_with_creds):
        parsed_url_merged = url_with_creds.split(':')
        length = len(parsed_url_merged)
        if length == 2:
            # if server is of form turn:server_name or stun:server_name
                if parsed_url_merged[0].lower() != 'turn' and parsed_url_merged[0].lower() != 'stun':
                    return False
                server = ':'.join(parsed_url_merged[0:2])
                return (server,)
        elif length == 3:
            # if server is of form turn:server_name:port or stun:server_name:port
            if parsed_url_merged[0].lower() != 'turn' and parsed_url_merged[0].lower() != 'stun':
                    return False
            server = ':'.join(parsed_url_merged[0:3])
            return (server,)
        elif length == 5:
            # if server is of form turn:server_name:port:username:password or stun:server_name:port:username:password
            if parsed_url_merged[0].lower() != 'turn' and parsed_url_merged[0].lower() != 'stun':
                    return False
            server = ':'.join(parsed_url_merged[0:3])
            return (server, parsed_url_merged[3], parsed_url_merged[4])
        elif length == 4:
            # if server is of form turn:server_name:username:password or stun:server_name:username:password
            if parsed_url_merged[0].lower() != 'turn' and parsed_url_merged[0].lower() != 'stun':
                return False
            server = ':'.join(parsed_url_merged[0:2])
            return (server, parsed_url_merged[2], parsed_url_merged[3])

    def test_server(self, servers): 
        self.servers = servers
        clear_prev_entry = r"""
                var options=document.getElementsByTagName('select')[0];while(options.firstChild){options.removeChild(options.firstChild)}
                """
        self.driver.execute_script(clear_prev_entry)
        for server in  servers:
            server_url = server[0]

            self.driver.find_element_by_css_selector("#url").send_keys(server_url)
            if len(server) == 3:
                self.driver.find_element_by_css_selector("#username").send_keys(server[1])
                self.driver.find_element_by_css_selector("#password").send_keys(server[2])
            self.driver.find_element_by_css_selector("#add").click()
        gather = self.driver.find_element_by_css_selector("#gather")
        gather.click()
        while not gather.is_enabled():
            time.sleep(0.5)

    def check_success(self):
        """
        Parse the trickleice result table and extract the appropriate data needed
        to confirm the test result.
        """
        success = False
        results = self.driver.find_element_by_css_selector("#candidatesBody")
        for result in results.find_elements_by_tag_name('tr')[:-2]:
            items = result.find_elements_by_tag_name('td')
            type_ = items[2].text
            foundation = int(items[3].text)
            try:
                server = self.servers[foundation-1]
                protocol = self.match_turn_or_stun(server[0])
                if protocol == "turn" and type_ == "relay":
                    self.results.add((True, server))
                elif protocol == "stun" and type_ == "srflx":
                    self.results.add((True, server))
            except IndexError:
                continue
        if len(self.results) != len(self.servers):
            for i in self.servers:
                if ((True, i) not in self.results) and ((False, i) not in self.results):
                    self.results.add((False, i))

def interactive():
    print("Welcome to the interactive stun/turn server testing tool.\n")
    servers = []
    print("Input url of each turn/stun server at each prompt. Input 'end' when your done.\n")
    server = input("url of STUN/TURN server (should be in the form: 'turn:server_name[:port]' or 'stun:server_name[:port]', type 'end' when finished inputing servers.): ")
    while server.lower() != 'end':
        if not TrickleIce.match_turn_or_stun(server):
            print(f"\nInvalid url {server}!!!\n")
            sys.exit()

        credentials = input("\nDoes the server require credentials (Y/N)? ")
        if credentials.lower() == 'y':
            username = input("username: ")
            password = input("password: ")
            servers.append((server, username, password))
            server = input("url of STUN/TURN server (should be in the form: 'turn:server_name[:port]' or 'stun:server_name[:port]'): ")
        else:
            servers.append((server,))
        server = input("url of STUN/TURN server (should be in the form: 'turn:server_name[:port]' or 'stun:server_name[:port]', type 'end' when finished inputing servers.): ")
    test_and_print_result(servers)
    
def parse_file_content(content):
    output = []
    for i in content:
         match = TrickleIce.match_turn_or_stun_merged(i.strip("\n"))
         if not match:
             print(f"\n{i} is not a valid stun/turn url.\n")
             sys.exit()
         output.append(match)
    return output
         
def test_and_print_result(servers):
    print("\nStarting...\n")
    ice = TrickleIce()
    print("Testing server(s)...\n")
    ice.test_server(servers)
    print("\nTest finished.\n")
    ice.check_success()
    for i in ice.results:
        if i[0] == True:
            print(f"Test passed for server {i[1][0]}.\n")
        else:
            print(f"Test failed for server {i[1][0]}.\n")

def main():
    desc = "Automate turn/stun server testing with selenium."
    parser = argparse.ArgumentParser(description=desc)
    urlhlp = """URL of stun/turn server (should be in the form: 'turn:server_name[:port[:username:password]]' or 'stun:server_name[:port[:username:password]]'
    or it could be a path to a file containing lines of valid turn/stun url)."""
    parser.add_argument("-i", "--interactive", action="store_true", help="Test in interactive mode.")
    parser.add_argument("-s", "--server", action="store", help=urlhlp)

    args = parser.parse_args()
    if args.interactive:
        interactive()
    else:
        if args.server:
            servers = []
            parsed = TrickleIce.match_turn_or_stun_merged(args.server)
            if not parsed:
                if not pth.exists(args.server):
                    print(f"\n{args.server} is not a valid url or file path\n")
                    sys.exit()
                content = open(args.server).readlines()
                servers.extend(parse_file_content(content))
            else:
                servers.append(parsed)
            test_and_print_result(servers)
        else:
            print("\nYou must specified the server and/or username with password or use interactive mode with -i argument.\n")

if __name__ == '__main__':
    main()