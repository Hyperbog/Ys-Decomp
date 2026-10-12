; Ys SMS physical ROM bank 06; source-only reconstructed pointers/header
; Values derived from reviewed phase ledgers, not from ROM at assembly time.

org $8000
SpriteRecordDirectory:
    dw $8306, $82AB, $824D, $81EF, $8194, $8136, $80DB, $8080
    dw $98D7, $9879, $9818, $97B7, $9756, $96EF, $9691, $9636
    dw $95DE, $957A, $950D, $94AC, $944B, $93E1, $9380, $932E
    dw $9014, $8FA7, $8F3A, $8ED0, $8E66, $8DF9, $8D86, $8D25
    dw $92CA, $9266, $9205, $91A1, $9140, $90DF, $9078, $8CC1
    dw $8AC4, $8A5A, $89F3, $898C, $8925, $88C7, $8866, $8802
    dw $87A4, $873A, $86CA, $8663, $8C5A, $8BEA, $8B86, $8B28
    dw $860B, $85A7, $853D, $84DC, $847B, $8411, $83B3, $8361

org $9A77
ObjectWorkDirectory:
    dw $C200, $C230, $C260, $C290, $C2C0, $C2F0, $C320, $C350
    dw $C380, $C3B0, $C3E0, $C410, $C440, $C470, $C4A0, $C4D0
    dw $C500

org $9A99
SpriteHandlerDirectory:
    dw $9AF6, $9AA9, $9AF7, $9B45, $9B90, $9BC1, $9BB9, $9BF4
