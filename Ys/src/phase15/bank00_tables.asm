; Ys SMS physical ROM bank 00; source-only reconstructed pointers/header
; Values derived from reviewed phase ledgers, not from ROM at assembly time.

org $205A
GameStateDispatch:
    dw $20AC, $20AD, $20AC, $20AC, $20F3, $2170, $21B1, $21D0
    dw $21DB, $225B, $2299, $22B8, $22D9, $231D, $2334, $2367
    dw $2399, $23A4, $23E6, $244D, $2466, $2496, $249D, $249D
    dw $249D, $249D, $249D, $249D, $249D, $249D, $249D, $2497
    dw $249D, $249D, $249D, $249D, $249D, $249D, $249D, $249D
    dw $249D

org $2C24
SceneDispatch:
    dw $2C36, $2D9D, $2F2A, $3014, $3194, $329C, $333B, $3415
    dw $3519
