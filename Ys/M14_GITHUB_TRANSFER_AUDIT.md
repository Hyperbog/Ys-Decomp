# M14 GitHub transfer audit — Ys branch

Date: 2026-10-12
Repository: `Hyperbog/Ys-Decomp`, branch `Ys`
Original local checkpoint: `7d0c1937e475d12a66140a1264a3f24f65bbf71b`

## Source transfer results

- Original checkpoint contained **375 tracked files**, including two oversized
  JSON evidence graphs and the original `.gitignore`.
- **372 files** are native Git blobs at their original paths and match their
  exact original Git blob SHA-1 IDs.
- `.gitignore` is intentionally updated to ignore the two restored JSON files
  while keeping the losslessly archived `.json.gz` files tracked.
- **2 original JSON evidence files** are stored as losslessly compressed Git
  blobs; restoration and original SHA-256 validation were tested locally.
- Thus all **375 original tracked file payloads** are preserved in GitHub,
  with explicit restoration steps for the two compressed JSON files.

## Large evidence graphs

| Original source | Original size | Compressed size | SHA-256 (original) |
| --- | ---: | ---: | --- |
| `Ys/whole_system/evidence_graph.json` | 4,558,351 bytes | 232,857 bytes | `7ec4a6b615b4f24f9d11d3d0616e83ed02e4fadae2e987ef2923336dc84cccae` |
| `Ys/whole_system/evidence_graph_m3.json` | 6,530,431 bytes | 334,973 bytes | `b88793c4085c061ce98dca28c67fda9262607b259daadeb339baf040814d4d10` |

To verify or restore the exact original bytes:

```sh
python3 Ys/tools/restore_evidence_graphs.py --verify
python3 Ys/tools/restore_evidence_graphs.py --restore
```

See `Ys/whole_system/EVIDENCE_ARCHIVES.md` for more information.

## Original commit history preserved

The complete M14 Git bundle (1,931,042 bytes, 44 original commits and all
recorded refs) was verified with `git bundle verify` and archived in **8 tracked
binary parts** under `Ys/history/m14_bundle_parts/`. All eight part Git blob
SHA-1 IDs were compared to the originals.

Reconstruct and verify it with:

```sh
python3 Ys/tools/restore_m14_git_history.py --output ./Ys-M14-Foundation.bundle
git bundle verify ./Ys-M14-Foundation.bundle
```

See `Ys/history/README.md`.

## Project validation at the source snapshot

- Source-only SMS ROM rebuild: **16/16 physical banks**, 262,144 bytes;
  SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- Bank 13: **50 indexed resources**, 200 RLE blocks, 14,400 decoded bytes;
  5,607-byte unresolved trailing region.
- Test baseline prior to transfer: M14 **8/8**, M13 **7/7** passed.
- These tests were not rerun in an independently network-cloned GitHub checkout;
  the GitHub audit verifies Git blob byte identity and restoration integrity.

## Transfer limitations

GitHub's public per-file 100 MB limit was **not** the blocking issue. This
connection failed when sending multi-megabyte payloads in one request; two
files were therefore committed as deterministic, SHA-256-verified gzip
archives. The original Git commit ancestry was not pushed as the live branch
ancestry; the complete history is recoverable from the bundled archive.

Next development milestone: validate a fresh GitHub clone, restore the two
JSON files, rerun full ROM reconstruction/tests, and resume semantic RLE
source conversion for Banks 13, 05, 14, and 15.
