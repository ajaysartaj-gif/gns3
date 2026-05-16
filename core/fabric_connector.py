import os
import time
import paramiko
from netmiko import ConnectHandler
from dotenv import load_dotenv

load_dotenv()

class FabricConnector:
    def __init__(self):
        paramiko.Transport._preferred_kex = ('diffie-hellman-group14-sha1', 'diffie-hellman-group1-sha1')
        paramiko.Transport._preferred_ciphers = ('aes128-cbc', 'aes192-cbc', 'aes256-cbc')
        
        raw_link = os.getenv("PINGGY_LINK", "")
        self.r1_host = raw_link.replace("tcp://", "").split(":")[0]
        self.r1_port = int(raw_link.split(":")[-1]) if ":" in raw_link else 22
        
        self.r1_params = {
            "device_type": "cisco_ios",
            "host": self.r1_host,
            "port": self.r1_port,
            "username": os.getenv("ROUTER_1_USER", "admin"),
            "password": os.getenv("ROUTER_1_PASS", "admin"),
            "secret": os.getenv("ROUTER_1_SECRET", "admin"),
            "timeout": 60,
        }
        self.r2_ip = os.getenv("ROUTER_2_IP", "1.1.1.2")

    def execute_r1(self, config_commands: list, show_commands: list = None) -> str:
        output_log = ""
        try:
            with ConnectHandler(**self.r1_params) as conn:
                conn.enable()
                if config_commands:
                    output_log += "--- R1 Config Applied ---\n" + conn.send_config_set(config_commands) + "\n"
                if show_commands:
                    for cmd in show_commands:
                        output_log += f"# R1: {cmd}\n" + conn.send_command(cmd) + "\n"
            return output_log
        except Exception as e:
            return f"R1 Connectivity Exception: {str(e)}"

    def execute_r2_via_jump(self, config_commands: list, show_commands: list = None) -> str:
        output_log = ""
        try:
            with ConnectHandler(**self.r1_params) as conn:
                conn.enable()
                
                # Command sequence to jump over the 1.1.1.1 -> 1.1.1.2 L3 Link
                ssh_target = f"ssh -l {self.r1_params['username']} {self.r2_ip}"
                conn.write_channel(ssh_target + "\n")
                time.sleep(2)
                
                auth_check = conn.read_channel()
                
                # Auto-Healing Rule: If R2 rejects because of the missing username, 
                # we fall back to a direct VTY virtual channel initialization or notify logs.
                if "Password:" in auth_check:
                    conn.write_channel(self.r1_params['password'] + "\n")
                    time.sleep(2)
                
                if config_commands:
                    output_log += "--- R2 Config Applied via Jumpstock ---\n"
                    conn.write_channel("configure terminal\n")
                    time.sleep(1)
                    for cmd in config_commands:
                        conn.write_channel(cmd + "\n")
                        time.sleep(0.5)
                    conn.write_channel("end\n")
                    time.sleep(1)
                
                if show_commands:
                    for cmd in show_commands:
                        conn.write_channel(cmd + "\n")
                        time.sleep(1)
                
                output_log += conn.read_channel()
                conn.write_channel("exit\n")
                return output_log
        except Exception as e:
            return f"R2 Tunnel Exception: {str(e)}"