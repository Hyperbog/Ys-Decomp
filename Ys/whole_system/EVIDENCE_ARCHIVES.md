# Restoring the two large evidence graphs

Two large machine-readable evidence graphs from the complete M14 source snapshot
are tracked as **lossless gzip archives**, because the GitHub connector could
not transmit the original 4.6 MB and 6.5 MB text blobs in one operation.
This is **not** a GitHub 100 MB file-limit problem.

Files checked into Git:

- `Ys/whole_system/evidence_graph.json.gz` (232,857 bytes)
- `Ys/whole_system/evidence_graph_m3.json.gz` (334,973 bytes)
- `Ys/tools/restore_evidence_graphs.py`

Restore the exact original JSON files after cloning:

```sh
python3 Ys/tools/restore_evidence_graphs.py --restore
```

Check their integrity without writing files:

```sh
python3 Ys/tools/restore_evidence_graphs.py --verify
```

The tool verifies the compressed bytes against fixed SHA-256 digests, decompresses
with Python's standard library, verifies the **original uncompressed byte length**
and **SHA-256**, and refuses to overwrite an existing non-matching JSON file.
Both original files are reproducible byte-for-byte.  Generated `.json` files are
ignored by Git to prevent duplicate tracking of their `.gz` archives.

The other 373 files in the M14 source snapshot are committed at their original
paths and verified against their original Git blob SHA-1 IDs.

The original history is preserved separately in the M14 Git bundle backup.
