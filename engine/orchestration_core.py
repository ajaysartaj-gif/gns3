from core.fabric_connector import FabricConnector

class OrchestrationCore:
    def __init__(self):
        self.connector = FabricConnector()

    def generate_cli_payload(self, schema: dict, node_target: str) -> list:
        feature = schema.get("feature_type", "").lower()
        v = schema.get("variables", {})
        commands = []

        # If the feature type is just an informational query, do not generate configuration commands
        if feature in ["telemetry", "query", "unknown"]:
            return []

        if feature == "ospf":
            # Removed the problematic interface duplex settings to prevent IOS command rejection
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
        feature = normalized_schema.get("feature_type", "").lower()
        show_payload = normalized_schema.get("verification_commands", ["show ip interface brief"])
        targets = normalized_schema.get("target_nodes", ["r1"])
        
        # Safe catch: If the user is just asking an informational question, fetch live telemetry data instead
        if feature in ["telemetry", "query", "unknown"]:
            execution_report = "=== Live Network Telemetry State ===\n"
            if "r1" in targets:
                execution_report += "[FETCHING FROM R1]...\n"
                execution_report += self.connector.execute_r1([], show_payload) + "\n"
            if "r2" in targets:
                execution_report += "[FETCHING FROM R2]...\n"
                execution_report += self.connector.execute_r2_via_jump([], show_payload) + "\n"
            return execution_report

        execution_report = "=== NetBrain Orchestration Log ===\n"
        remediation_user_payload = ["username admin privilege 15 secret admin"]
        
        if "r1" in targets:
            r1_cmds = self.generate_cli_payload(normalized_schema, "r1")
            execution_report += "[DEPLOYING TO R1]...\n"
            execution_report += self.connector.execute_r1(r1_cmds, show_payload) + "\n"
            
        if "r2" in targets:
            r2_cmds = self.generate_cli_payload(normalized_schema, "r2")
            execution_report += "[DEPLOYING TO R2]...\n"
            final_r2_cmds = remediation_user_payload + r2_cmds + ["write memory"]
            execution_report += self.connector.execute_r2_via_jump(final_r2_cmds, show_payload) + "\n"
            
        return execution_report
