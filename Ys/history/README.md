# Ys Decompilation: Original M14 Git history

The GitHub `Ys` branch contains a source snapshot and subsequent transfer
commits, but its branch ancestry was initially based on the new standalone
repository. To preserve **all 44 original source-control commits** from the
restored Part 1/M14 history, the verified local Git bundle has been committed
here as eight binary segments. This archive is a supplement, not a substitute
for a normal Git branch checkout.

To reassemble the original bundle from a GitHub clone:

```sh
python3 Ys/tools/restore_m14_git_history.py --output ./Ys-M14-Foundation.bundle
git bundle verify ./Ys-M14-Foundation.bundle
git clone -b Ys ./Ys-M14-Foundation.bundle ys-original-history
```

The script checks the individual part sizes and SHA-256 digests, verifies the
fully reconstructed 1,931,042-byte bundle against SHA-256
`56672a6c7e7423f857ff8459719fd8e5d191425ed897915ff831f19d92e8c606`,
and refuses to overwrite a pre-existing bundle. The eight parts and restore
script are committed to Git, so the original history is recoverable even if
external temporary download links expire.

Snapshot information:
- The original local `Ys` branch head is `7d0c1937e475d12a66140a1264a3f24f65bbf71b`.
- The original history has 44 commits and the bundle is complete, verified by
  `git bundle verify`.
- The two large evidence graph files are archived separately as verified
  gzip files; see `Ys/whole_system/EVIDENCE_ARCHIVES.md`.
