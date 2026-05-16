from core.fabric_connector import FabricConnector

class OrchestrationCore:
    def __init__(self):
        self.connector = FabricConnector()

    def generate_cli_payload(self, schema: dict) -> list:
        """Compiles standard configurations using decoupled, variable data templates."""
        feature = schema.get("feature_type", "").lower()
        v = schema.get("variables", {})
        commands = []

        if feature == "ospf":
            commands = [
                f"router ospf {v.get('process_id', 1)}",
                f"network {v.get('network_address', '192.168.1.0')} {v.get('wildcard_mask', '0.0.0.255')} area {v.get('area', 0)}",
                "log-adjacency-changes"
            ]
        elif feature == "bgp":
            commands = [
                f"router bgp {v.get('asn', 65001)}",
                f"neighbor {v.get('network_address')} remote-as {v.get('asn', 65001)}",
                "no auto-summary"
            ]
        elif feature == "vlan":
            commands = [
                f"vlan {v.get('vlan_id', 10)}",
                f"name NETBRAIN_VLAN_{v.get('vlan_id', 10)}"
            ]
        elif feature == "static_route":
            commands = [
                f"ip route {v.get('network_address')} 255.255.255.0 {v.get('interface')}"
            ]
        elif feature == "acl":
            commands = [
                f"ip access-list extended NETBRAIN_SECURITY_POLICY",
                f"permit ip any any",
                f"interface {v.get('interface', 'GigabitEthernet1')}",
                f"ip access-group NETBRAIN_SECURITY_POLICY {v.get('direction', 'in')}"
            ]
        elif feature == "nat":
            commands = [
                f"ip nat inside source list 1 interface {v.get('interface', 'GigabitEthernet1')} overload",
                "access-list 1 permit any"
            ]
        else:
            # Fallback wrapper for general simple execution requests
            if v.get("custom_command"):
                commands.append(v.get("custom_command"))
                
        return commands

    def deploy_feature(self, normalized_schema: dict) -> str:
        """Orchestrates configuration execution and verification diagnostics safely across target routers."""
        config_payload = self.generate_cli_payload(normalized_schema)
        show_payload = normalized_schema.get("verification_commands", ["show ip interface brief"])
        targets = normalized_schema.get("target_nodes", ["r1"])
        
        execution_report = "=== NetBrain Orchestration Log ===\n"
        
        if "r1" in targets:
            execution_report += "[DEPLOYING TO ROUTER 1 (Gateway Node)]...\n"
            execution_report += self.connector.execute_r1(config_payload, show_payload) + "\n"
            
        if "r2" in targets:
            execution_report += "[DEPLOYING TO ROUTER 2 (Jumpstock Node)]...\n"
            # Appending baseline system saves for downstream targets
            r2_config = config_payload + ["write memory"]
            execution_report += self.connector.execute_r2_via_jump(r2_config, show_payload) + "\n"
            
        return execution_report