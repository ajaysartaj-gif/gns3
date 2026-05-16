from core.fabric_connector import FabricConnector

class OrchestrationCore:
    def __init__(self):
        self.connector = FabricConnector()

    def generate_cli_payload(self, schema: dict, node_target: str) -> list:
        feature = schema.get("feature_type", "").lower()
        v = schema.get("variables", {})
        commands = []

        if feature == "ospf":
            # Proactive Duplex Auto-Healing optimization step
            # Split cleanly into individual items so Netmiko parses them without breaking
            if node_target == "r2":
                commands.extend([
                    "interface FastEthernet0/0",
                    "duplex full"
                ])
            elif node_target == "r1":
                commands.extend([
                    "interface GigabitEthernet1/0",
                    "duplex full"
                ])
                
            # Realized directly against your 1.1.1.0 network backbone
            commands.extend([
                f"router ospf {v.get('process_id', 1)}",
                "network 1.1.1.0 0.0.0.255 area 0",
                "log-adjacency-changes"
            ])
                
        elif feature == "vlan":
            commands = [
                f"vlan {v.get('vlan_id', 10)}", 
                f"name NETBRAIN_VLAN_{v.get('vlan_id', 10)}"
            ]
            
        elif feature == "static_route":
            commands = [f"ip route {v.get('network_address')} 255.255.255.0 {self.connector.r2_ip}"]
            
        elif feature == "acl":
            target_int = "GigabitEthernet1/0" if node_target == "r1" else "FastEthernet0/0"
            commands = [
                "ip access-list extended NETBRAIN_SECURITY",
                "permit ip any any",
                f"interface {target_int}",
                "ip access-group NETBRAIN_SECURITY in"
            ]
        return commands

    def deploy_feature(self, normalized_schema: dict) -> str:
        show_payload = normalized_schema.get("verification_commands", ["show ip interface brief"])
        targets = normalized_schema.get("target_nodes", ["r1", "r2"])
        
        execution_report = "=== NetBrain Orchestration Log ===\n"
        
        # Pre-Execution Stage: Let's explicitly create the admin credential on R2 if missing
        remediation_user_payload = ["username admin privilege 15 secret admin"]
        
        if "r1" in targets:
            r1_cmds = self.generate_cli_payload(normalized_schema, "r1")
            execution_report += "[DEPLOYING TO R1]...\n"
            execution_report += self.connector.execute_r1(r1_cmds, show_payload) + "\n"
            
        if "r2" in targets:
            r2_cmds = self.generate_cli_payload(normalized_schema, "r2")
            execution_report += "[DEPLOYING TO R2]...\n"
            # We push the username statement first to avoid ssh authentication deadlocks
            final_r2_cmds = remediation_user_payload + r2_cmds + ["write memory"]
            execution_report += self.connector.execute_r2_via_jump(final_r2_cmds, show_payload) + "\n"
            
        return execution_report
