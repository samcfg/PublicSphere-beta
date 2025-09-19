from src.language import get_language_ops

ops = get_language_ops()
ops.set_graph("test_graph")
if __name__ == "__main__":
    print("Graph set to 'test_graph'")
    print("Hint: ops.create_claim(content='test')")
    print("      ops.delete_node('uuid')")
    import code
    code.interact(local=locals())