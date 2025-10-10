from PS_Graph_DB.src.test_data import get_test_generator

test_gen = get_test_generator()
test_gen.create_test_suite('test_graph')
test_gen.print_stats('test_graph')