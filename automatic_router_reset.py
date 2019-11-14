from paramiko import client
import ping3
import time
import sys
import os
import csv

'''user defined variables'''
address = "192.168.1.1"  # replace with router network address
username = "root"  # you should usually leave this as root even if you've changed your web interface login username
password = "password"  # replace with your ssh password


class ssh:
    client = None

    def __init__(self, address, username, password):
        """
        connects to the router via ssh

        :param address: router network address
        :param username: router admin username (you should usually leave this as root even if you've changed your web
        interface login username)
        :param password: router admin password
        """
        print("Connecting to server.")
        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def send_command(self, command):
        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)
            while not stdout.channel.exit_status_ready():
                # Print data when available
                if stdout.channel.recv_ready():
                    all_data = stdout.channel.recv(1024)
                    prev_data = b"1"
                    while prev_data:
                        prev_data = stdout.channel.recv(1024)
                        all_data += prev_data

                    print(str(all_data, "utf8"))
        else:
            print("Connection not opened.")


class TimeMonitor:

    @staticmethod
    def ping_check():
        """
        ping Google.com as a somewhat reliable source for checking whether internet connection is still active,
        though any website could be substituted here
        :return: the final result of the check sequence
        """
        loop = 0
        r = ping3.ping('google.com')
        # loops though checks several times in case the connection loss is only a brief one
        while r is None and loop < 4:
            time.sleep(20)
            r = ping3.ping('google.com')
            loop += 1
        return r

    @staticmethod
    def reboot():
        """
        opens a ssh session an sends signal to reboot the router.  Also writes current time to a CSV in the directory,
        for the sake of tracking how many reboots occur
        """
        connection = ssh(address, username, password)
        connection.send_command("reboot")

        print("Executing reboot")

        with open((os.path.join(sys.path[0] + 'time_track.csv')), mode='a') as time_track:
            time_writer = csv.writer(time_track, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            time_writer.writerow([time.time()])

    def watch_for_drop(self, wait_seconds=60):
        """
        Check for a status update every 'wait_seconds' seconds.
        If the ping fails, reboot the router
        """
        while True:
            if self.ping_check() is None:
                self.reboot()
            time.sleep(wait_seconds)


if __name__ == '__main__':
    router_monitor = TimeMonitor()
    router_monitor.watch_for_drop()
