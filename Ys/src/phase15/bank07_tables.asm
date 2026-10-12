; Ys SMS physical ROM bank 07; source-only reconstructed pointers/header
; Values derived from reviewed phase ledgers, not from ROM at assembly time.

org $8000
GraphicsDispatchDirectory:
    dw $82C0, $8CDF, $81C0, $8C3F, $8180, $8B97, $81C0, $8AF7
    dw $8180, $8A4F, $8180, $89A7, $8200, $890F, $8200, $8877
    dw $82C0, $AF3F, $8240, $AEAF, $8180, $AE07, $81C0, $AD67
    dw $8180, $ACBF, $81C0, $AC1F, $8240, $AB8F, $82C0, $AB0F
    dw $8240, $AA7F, $8200, $A9E7, $8180, $A93F, $8180, $A897
    dw $8180, $A7EF, $8180, $A747, $8240, $A6B7, $8280, $A62F
    dw $8240, $A59F, $8180, $A4F7, $81C0, $A457, $8180, $A3AF
    dw $8180, $A307, $81C0, $A267, $8200, $A1CF, $81C0, $A12F
    dw $81C0, $A08F, $8180, $9FE7, $8200, $9F4F, $8180, $9EA7
    dw $8180, $9DFF, $8200, $9D67, $8200, $9CCF, $81C0, $9C2F
    dw $81C0, $9B8F, $8200, $9AF7, $8240, $9A67, $8180, $99BF
    dw $8180, $9917, $81C0, $9877, $81C0, $97D7, $81C0, $9737
    dw $8200, $969F, $8200, $9607, $8180, $955F, $8180, $94B7
    dw $8180, $940F, $8180, $9367, $81C0, $92C7, $8240, $9237
    dw $8300, $91BF, $8200, $9127, $8180, $907F, $8180, $8FD7
    dw $8180, $8F2F, $8180, $8E87, $8200, $8DEF, $8240, $8D5F

org $8100
SecondaryRecordDirectory:
    dw $AFBF, $AFD5, $AFEB, $B001, $B017, $B02D, $B043, $B059
    dw $B06F, $B085, $B09B, $B0B1, $B0C7, $B0DD, $B0F3, $B109
    dw $B11F, $B135, $B14B, $B161, $B177, $B18D, $B1A3, $B1B9
    dw $B1CF, $B1E5, $B1FB, $B211, $B227, $B23D, $B253, $B269
    dw $B27F, $B295, $B2AB, $B2C1, $B2D7, $B2ED, $B303, $B319
    dw $B32F, $B345, $B35B, $B371, $B387, $B39D, $B3B3, $B3C9
    dw $B3DF, $B3F5, $B40B, $B421, $B437, $B44D, $B463, $B479
    dw $B48F, $B4A5, $B4BB, $B4D1, $B4E7, $B4FD, $B513, $B529
