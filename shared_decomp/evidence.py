#!/usr/bin/env python3
"""Portable structural evidence-graph validator (no CPU-specific decoding).

The caller supplies byte-offset nodes, basic-block ownership and directed
references. This audits graph coherence ONLY, never semantic correctness.
"""
from __future__ import annotations


def validate_graph(instructions, blocks, edges, image_size):
    errors = []
    if not isinstance(image_size,int) or image_size < 1:
        raise ValueError('image_size must be a positive integer')
    by_id = {}
    ownership = {}
    for node in instructions:
        ident, at, size = node['id'], node['offset'], node['size']
        if ident in by_id:
            errors.append(f'duplicate instruction ID {ident}')
        if not (isinstance(at,int) and isinstance(size,int) and size>0 and 0<=at and at+size<=image_size):
            errors.append(f'invalid node span {ident}')
            continue
        by_id[ident] = node
        for p in range(at,at+size):
            if p in ownership:
                errors.append(f'instruction overlap at offset {p:05X}')
                break
            ownership[p] = ident
    by_block = {}
    block_owners = {}
    for block in blocks:
        key=block['id']
        if key in by_block:errors.append(f'duplicate block {key}')
        by_block[key] = block
        start, span = block['offset'], block['byte_count']
        if not isinstance(span,int) or not isinstance(start,int) or span<=0 or start<0 or start+span>image_size:
            errors.append(f'invalid block span {key}')
            continue
        for p in range(start,start+span):
            if p in block_owners:
                errors.append(f'block overlap at offset {p:05X}')
                break
            block_owners[p] = key
        node_in_block=[n for n in instructions if start<=n['offset']<start+span]
        if (sum(n['size'] for n in node_in_block)!=span
            or len(node_in_block)!=block['instruction_count']
            or any(n['offset']+n['size']>start+span for n in node_in_block)):
            errors.append(f'block does not exactly partition its span {key}')
    if set(block_owners)!=set(ownership):
        errors.append('block-covered bytes differ from instruction-covered bytes')
    for e in edges:
        if e['from'] not in by_id:
            errors.append(f'missing source instruction {e["from"]}')
        target = e.get('to_instruction')
        if target is not None and target not in by_id:
            errors.append(f'missing target instruction {target}')
        if e.get('from_block') not in by_block:
            errors.append(f'missing source block {e.get("from_block")}')
        if target is not None and e.get('to_block') not in by_block:
            errors.append(f'missing target block {e.get("to_block")}')
        if e['from'] in by_id and e.get('from_block') in by_block:
            if block_owners.get(by_id[e['from']]['offset'])!=e['from_block']:
                errors.append('source block ID disagrees with instruction ownership')
        if target in by_id and e.get('to_block') in by_block:
            if block_owners.get(by_id[target]['offset'])!=e['to_block']:
                errors.append('target block ID disagrees with instruction ownership')
    return {'valid':not errors,'errors':errors,'instruction_count':len(instructions),
            'basic_block_count':len(blocks),'edge_count':len(edges),
            'byte_count':len(ownership),
            'qualification':'Graph topology/byte ownership checked; instruction semantics and runtime mapper state not verified.'}
