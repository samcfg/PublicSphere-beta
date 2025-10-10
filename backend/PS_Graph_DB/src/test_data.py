from typing import List, Tuple
from .schema import get_schema
from .language import get_language_ops
from .database import get_db
import random

class TestDataGenerator:
    """Generate test data for Claims and Connections"""
    
    def __init__(self):
        self.schema = get_schema()
        self.language_ops = get_language_ops()
        self.db = get_db()
    
    def clear_graph(self, graph_name: str) -> None:
        """Remove all data from graph"""
        self.db.execute_cypher(
            graph_name,
            "MATCH (n) DETACH DELETE n"
        )
    
    def reset_graph(self, graph_name: str) -> None:
        """Reset graph with fresh schema"""
        if self.db.graph_exists(graph_name):
            self.db.drop_graph(graph_name)
        self.schema.apply_to_graph(graph_name)
    
    def create_simple_chain(self, graph_name: str, chain_length: int = 5) -> List[str]:
        """Create a simple chain of connected claims"""
        claim_ids = []
        
        # Create claims
        for i in range(chain_length):
            claim_id = self.language_ops.create_claim(graph_name)
            claim_ids.append(claim_id)
        
        # Connect them in sequence
        for i in range(chain_length - 1):
            self.language_ops.create_connection(
                graph_name, 
                claim_ids[i], 
                claim_ids[i + 1]
            )
        
        return claim_ids
    
    def create_star_pattern(self, graph_name: str, center_claim: str = None, 
                           branches: int = 4) -> Tuple[str, List[str]]:
        """Create a star pattern with one central claim connected to others"""
        if center_claim is None:
            center_claim = self.language_ops.create_claim(graph_name)
        
        branch_claims = []
        for i in range(branches):
            branch_claim = self.language_ops.create_claim(graph_name)
            branch_claims.append(branch_claim)
            
            # Connect center to branch
            self.language_ops.create_connection(graph_name, center_claim, branch_claim)
        
        return center_claim, branch_claims
    
    def create_cycle(self, graph_name: str, cycle_size: int = 4) -> List[str]:
        """Create a cycle of claims"""
        claim_ids = []
        
        # Create claims
        for i in range(cycle_size):
            claim_id = self.language_ops.create_claim(graph_name)
            claim_ids.append(claim_id)
        
        # Connect in cycle
        for i in range(cycle_size):
            next_i = (i + 1) % cycle_size
            self.language_ops.create_connection(
                graph_name,
                claim_ids[i],
                claim_ids[next_i]
            )
        
        return claim_ids
    
    def create_random_network(self, graph_name: str, num_claims: int = 10, 
                             connection_probability: float = 0.3) -> List[str]:
        """Create a random network of claims"""
        claim_ids = []
        
        # Create claims
        for i in range(num_claims):
            claim_id = self.language_ops.create_claim(graph_name)
            claim_ids.append(claim_id)
        
        # Create random connections
        for i in range(num_claims):
            for j in range(num_claims):
                if i != j and random.random() < connection_probability:
                    self.language_ops.create_connection(
                        graph_name,
                        claim_ids[i],
                        claim_ids[j]
                    )
        
        return claim_ids
    
    def create_test_suite(self, graph_name: str) -> dict:
        """Create a comprehensive test dataset"""
        self.reset_graph(graph_name)
        
        results = {}
        
        # Simple chain
        results['chain'] = self.create_simple_chain(graph_name, 5)
        
        # Star pattern
        center, branches = self.create_star_pattern(graph_name, branches=3)
        results['star'] = {'center': center, 'branches': branches}
        
        # Small cycle
        results['cycle'] = self.create_cycle(graph_name, 4)
        
        # Connect some patterns together
        self.language_ops.create_connection(
            graph_name,
            results['chain'][0],  # First in chain
            center  # Center of star
        )
        
        self.language_ops.create_connection(
            graph_name,
            results['cycle'][0],  # First in cycle
            results['chain'][-1]  # Last in chain
        )
        
        return results
    
    def print_stats(self, graph_name: str) -> None:
        """Print graph statistics"""
        stats = self.db.get_graph_stats(graph_name)
        print(f"Graph '{graph_name}' statistics:")
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")
        
        labels = self.db.get_node_labels(graph_name)
        edge_types = self.db.get_edge_types(graph_name)
        print(f"  Node labels: {labels}")
        print(f"  Edge types: {edge_types}")

# Global test data generator
test_gen = TestDataGenerator()

def get_test_generator() -> TestDataGenerator:
    """Get the global test data generator"""
    return test_gen

if __name__ == "__main__":
    # Quick test
    test_graph = "test_graph"
    test_gen.create_test_suite(test_graph)
    test_gen.print_stats(test_graph)