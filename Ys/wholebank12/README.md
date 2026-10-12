# Bank 12 — Source-only / partial semantic decoding

Entire 16-KiB bank source-owned. Existing 108-byte verified Z80 code at `$9EFC–$9F67` is re-used without double counting. The initial 128-byte numeric curve at `$8000–$807F` is grouped as a **candidate** lookup table; its consumer and game meaning are not established. Surrounding resource data is still undecoded. Bank-end FF fill is verified as a separate structured region.
