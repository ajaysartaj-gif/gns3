import os
import time
import paramiko
from netmiko import ConnectHandler
from dotenv import load_dotenv

load_dotenv()

class FabricConnector:
    def __init__(self):
        # Enforce legacy cryptography suites for enterprise hardware appliances
        paramiko.Transport._preferred_kex = ('diffie-hellman-group14-sha1', 'diffie-hellman-group1-sha1')
        paramiko.Transport._preferred_ciphers = ('aes128-cbc', 'aes192-cbc', 'aes256-cbc')
        
        raw_link = os.getenv("PINGGY_LINK", "")
        self.r1_host = raw_link.replace("tcp://", "").split(":")[0]
        self.r1_port = int(raw_link.split(":")[-1]) if ":" in raw_link else 22
        
        self.r1_params = {
            "device_type": "cisco_ios",
            "host": self.r1_host,
            "port": self.r1_port,
            "username": os.getenv("ROUTER_1_USER"),
            "password": os.getenv("ROUTER_1_PASS"),
            "secret": os.getenv("ROUTER_1_SECRET"),
            "timeout": 60,
        }
        self.r2_ip = os.getenv("ROUTER_2_IP")

    def execute_r1(self, config_commands: list, show_commands: list = None) -> str:
        """Executes changes and diagnostic commands on Router 1."""
        output_log = ""
        try:
            with ConnectHandler(**self.r1_params) as conn:
                conn.enable()
                if config_commands:
                    output_log += "--- R1 Config Commit ---\n" + conn.send_config_set(config_commands) + "\n"
                if show_commands:
                    output_log += "--- R1 Telemetry State ---\n"
                    for cmd in show_commands:
                        output_log += f"# {cmd}\n" + conn.send_command(cmd) + "\n"
            return output_log
        except Exception as e:
            return f"Router 1 Fabric Error: {str(e)}"

    def execute_r2_via_jump(self, config_commands: list, show_commands: list = None) -> str:
        """Tunnels through Router 1 using interactive shell tracking to govern Router 2."""
        output_log = ""
        try:
            with ConnectHandler(**self.r1_params) as conn:
                conn.enable()
                # Initialize sub-shell connection over internal Layer 3 adjacency
                ssh_target = f"ssh -l {self.r1_params['username']} {self.r2_ip}"
                conn.write_channel(ssh_target + "\n")
                time.sleep(2)
                
                auth_check = conn.read_channel()
                if "Password:" in auth_check:
                    conn.write_channel(self.r1_params['password'] + "\n")
                    time.sleep(2)
                
                # Commit configuration changes in global mode
                if config_commands:
                    output_log += "--- R2 Config Commit ---\n"
                    conn.write_channel("configure terminal\n")
                    time.sleep(1)
                    for cmd in config_commands:
                        conn.write_channel(cmd + "\n")
                        time.sleep(0.5)
                    conn.write_channel("end\n")
                    time.sleep(1)
                
                # Fetch target operational verification commands
                if show_commands:
                    output_log += "--- R2 Telemetry State ---\n"
                    for cmd in show_commands:
                        conn.write_channel(cmd + "\n")
                        time.sleep(1)
                
                output_log += conn.read_channel()
                conn.write_channel("exit\n") # Gracefully break nested session
                return output_log
        except Exception as e:
            return f"Router 2 Jump Engine Error: {str(e)}"