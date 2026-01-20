from src.graph.neo4j_client import Neo4jClient

def heal_titan():
    print("🚑 STARTING TITAN NETWORK HEALING PROTOCOL...")
    try:
        client = Neo4jClient()
        
        # 1. Check how many are broken first (Safety Check)
        check_query = """
        MATCH (n) 
        WHERE (n:Factory OR n:Warehouse OR n:Port) AND n.status = 'Disrupted'
        RETURN count(n) as count
        """
        result = client.run_query(check_query)
        broken_count = result[0]['count']
        
        if broken_count == 0:
            print("✅ System is already healthy! No red nodes found.")
            client.close()
            return

        print(f"⚠️ Found {broken_count} Disrupted (Red) facilities.")
        print("🛠️ Applying repair patch...")

        # 2. The Healing Command (Safe - Removes Status Only)
        heal_query = """
        MATCH (n) 
        WHERE n:Factory OR n:Warehouse OR n:Port 
        REMOVE n.status, n.operational_status
        """
        client.run_query(heal_query)
        
        # 3. Unblock Routes
        route_query = """
        MATCH ()-[r:SUPPLIES_TO]->() 
        REMOVE r.status
        """
        client.run_query(route_query)

        print(f"🎉 SUCCESS: Repaired {broken_count} facilities and unblocked all routes.")
        print("🌍 Please refresh your Dashboard now.")
        client.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    heal_titan()