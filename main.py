import tkinter as tk
from paramiko import SSHClient
from functools import partial
from subprocess import check_output


hosts = {}
import paramiko
import re


class ShellHandler:

    def __init__(self, host, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=22)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # up for now filled with shell junk from stdin
                shout = []
            elif str(line).startswith(finish):
                # our finish command ends with the exit status
                exit_status = int(str(line).rsplit(maxsplit=1)[1])
                if exit_status:
                    # stderr is combined with stdout.
                    # thus, swap sherr with shout in a case of failure.
                    sherr = shout
                    shout = []
                break
            else:
                # get rid of 'coloring and formatting' special characters
                shout.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).
                             replace('\b', '').replace('\r', ''))

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr

def load_hosts():
    f = open("config.txt","r")
    lines = f.readlines()

    for line in lines:
        splitted = line.split(" ")
        try:
            name = splitted[1].split("\n")[0]
        except:
            name = splitted[1]

        hosts[name] = splitted[0]

def connect_ssh(hostname):
    ip = hosts[hostname]
    shell = ShellHandler(ip,"hostname","password")
    print("Hostname: ", hostname)
    
    print("IP is: ", ip)
    print("Closing connection: ", shell.__del__)
    command = "ssh " + ip
    output = check_output(command, shell=True).decode()
    print(output)
    #os.system("start /wait cmd /k {dir}")


def main():
    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()

    for key in hosts.keys():
        action_with_arg = partial(connect_ssh, key)
        button = tk.Button(frame, 
                        text=key, 
                        fg="red",
                        command = action_with_arg
                        )

        button.pack(side=tk.LEFT)

    root.mainloop()

if __name__ == "__main__":
    load_hosts()
    main()