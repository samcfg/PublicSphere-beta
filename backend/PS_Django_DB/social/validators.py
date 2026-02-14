"""
Validators for social interaction models.
Includes validation for refactoring operation sequences.
"""
from typing import Dict, Set, List
from rest_framework.exceptions import ValidationError
import uuid


class RefactoringValidator:
    """Validates refactoring operation sequences for connection restructuring"""

    VALID_OPERATION_TYPES = {
        'create_claim',
        'create_source',
        'create_connection',
        'create_compound_connection',
        'delete_connection'
    }

    SPECIAL_MARKERS = {'$SOURCE', '$TARGET', '$ORIGINAL'}

    def __init__(self, proposed_changes: Dict):
        """
        Initialize validator with proposed changes.

        Args:
            proposed_changes: Dict containing 'original_connection_id' and 'operations'
        """
        self.changes = proposed_changes
        self.operations = proposed_changes.get('operations', [])
        self.original_id = proposed_changes.get('original_connection_id')

    def validate(self):
        """
        Run all validation checks.
        Raises ValidationError if any check fails.
        """
        self._validate_structure()
        self._validate_references()
        self._validate_graph_integrity()

    def _validate_structure(self):
        """Check required fields and operation types"""
        if not self.original_id:
            raise ValidationError({
                'original_connection_id': 'Required for connection refactorings'
            })

        if not self.operations or not isinstance(self.operations, list):
            raise ValidationError({
                'operations': 'Must be non-empty list'
            })

        # Validate each operation
        for i, op in enumerate(self.operations):
            if 'op_id' not in op:
                raise ValidationError({
                    'operations': f'Operation {i} missing op_id field'
                })

            if 'type' not in op:
                raise ValidationError({
                    'operations': f'Operation {op.get("op_id", i)} missing type field'
                })

            op_type = op['type']
            if op_type not in self.VALID_OPERATION_TYPES:
                raise ValidationError({
                    'operations': f'Invalid operation type "{op_type}" in op {op["op_id"]}. '
                                 f'Must be one of: {", ".join(self.VALID_OPERATION_TYPES)}'
                })

            # Type-specific validation
            if op_type in ['create_claim', 'create_source']:
                if 'temp_id' not in op:
                    raise ValidationError({
                        'operations': f'Node creation (op {op["op_id"]}) requires temp_id field'
                    })
                if 'data' not in op:
                    raise ValidationError({
                        'operations': f'Node creation (op {op["op_id"]}) requires data field'
                    })

                # Validate node creation data
                if op_type == 'create_claim':
                    if 'content' not in op['data']:
                        raise ValidationError({
                            'operations': f'create_claim (op {op["op_id"]}) requires data.content'
                        })
                elif op_type == 'create_source':
                    if 'title' not in op['data'] or 'source_type' not in op['data']:
                        raise ValidationError({
                            'operations': f'create_source (op {op["op_id"]}) requires data.title and data.source_type'
                        })

            elif op_type == 'create_connection':
                if 'from' not in op or 'to' not in op:
                    raise ValidationError({
                        'operations': f'create_connection (op {op["op_id"]}) requires from and to fields'
                    })
                if 'data' not in op:
                    raise ValidationError({
                        'operations': f'create_connection (op {op["op_id"]}) requires data field'
                    })

            elif op_type == 'create_compound_connection':
                if 'sources' not in op:
                    raise ValidationError({
                        'operations': f'create_compound_connection (op {op["op_id"]}) requires sources field'
                    })
                if not isinstance(op['sources'], list) or len(op['sources']) < 2:
                    raise ValidationError({
                        'operations': f'create_compound_connection (op {op["op_id"]}) requires at least 2 sources'
                    })
                if 'target' not in op:
                    raise ValidationError({
                        'operations': f'create_compound_connection (op {op["op_id"]}) requires target field'
                    })
                if 'data' not in op or 'logic_type' not in op['data']:
                    raise ValidationError({
                        'operations': f'create_compound_connection (op {op["op_id"]}) requires data.logic_type'
                    })

            elif op_type == 'delete_connection':
                if 'connection_id' not in op:
                    raise ValidationError({
                        'operations': f'delete_connection (op {op["op_id"]}) requires connection_id field'
                    })

    def _validate_references(self):
        """Check all temp_id/node references are valid"""
        created_nodes = set()  # Track temp_ids created

        # Sort operations by op_id to validate in execution order
        sorted_ops = sorted(self.operations, key=lambda x: x['op_id'])

        for op in sorted_ops:
            op_id = op['op_id']
            op_type = op['type']

            # Track node creations
            if op_type in ['create_claim', 'create_source']:
                temp_id = op['temp_id']
                if temp_id in created_nodes:
                    raise ValidationError({
                        'operations': f'Duplicate temp_id "{temp_id}" in op {op_id}'
                    })
                created_nodes.add(temp_id)

            # Validate connection references
            elif op_type == 'create_connection':
                self._validate_ref(op['from'], created_nodes, op_id, 'from')
                self._validate_ref(op['to'], created_nodes, op_id, 'to')

            elif op_type == 'create_compound_connection':
                for source_ref in op['sources']:
                    self._validate_ref(source_ref, created_nodes, op_id, 'sources')
                self._validate_ref(op['target'], created_nodes, op_id, 'target')

            elif op_type == 'delete_connection':
                conn_ref = op['connection_id']
                # Only validate that $ORIGINAL is valid, direct UUIDs validated at apply time
                if conn_ref not in self.SPECIAL_MARKERS and not self._is_valid_uuid(conn_ref):
                    raise ValidationError({
                        'operations': f'Invalid connection_id in op {op_id}: {conn_ref}'
                    })

    def _validate_ref(self, ref: str, created_nodes: Set[str], op_id: int, field_name: str):
        """Validate a single node reference"""
        # Special markers always valid
        if ref in self.SPECIAL_MARKERS:
            return

        # Temp_id must have been created in earlier operation
        if ref in created_nodes:
            return

        # Otherwise assume it's a direct UUID - validate format
        if not self._is_valid_uuid(ref):
            raise ValidationError({
                'operations': f'Invalid reference in op {op_id} field "{field_name}": "{ref}". '
                             f'Must be special marker ($SOURCE, $TARGET), temp_id from earlier operation, or valid UUID'
            })

    def _validate_graph_integrity(self):
        """Ensure operations form valid path from $SOURCE to $TARGET"""
        # Build adjacency list from operations
        graph = {}
        nodes = {'$SOURCE', '$TARGET'}

        for op in self.operations:
            op_type = op['type']

            if op_type in ['create_claim', 'create_source']:
                nodes.add(op['temp_id'])

            elif op_type == 'create_connection':
                from_node = op['from']
                to_node = op['to']
                nodes.add(from_node)
                nodes.add(to_node)
                if from_node not in graph:
                    graph[from_node] = []
                graph[from_node].append(to_node)

            elif op_type == 'create_compound_connection':
                for source in op['sources']:
                    nodes.add(source)
                    if source not in graph:
                        graph[source] = []
                    graph[source].append(op['target'])
                nodes.add(op['target'])

        # Check path exists from $SOURCE to $TARGET (BFS)
        if not self._path_exists(graph, '$SOURCE', '$TARGET'):
            raise ValidationError({
                'operations': 'Operations must form valid path from source to target node. '
                             'The refactoring should maintain connectivity from the original '
                             'connection\'s source to its target.'
            })

    def _path_exists(self, graph: Dict[str, List[str]], start: str, end: str) -> bool:
        """BFS to check if path exists from start to end"""
        from collections import deque

        visited = set()
        queue = deque([start])

        while queue:
            node = queue.popleft()

            if node == end:
                return True

            if node in visited:
                continue
            visited.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        return False

    @staticmethod
    def _is_valid_uuid(s: str) -> bool:
        """Check if string is valid UUID format"""
        try:
            uuid.UUID(s)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
