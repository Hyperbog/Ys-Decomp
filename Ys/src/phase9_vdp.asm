; Ys SMS — selected VDP transfer routines, independent custom subset-assembler input.
; ROM offsets == CPU addresses (fixed bank 0). No game ROM stored in Git.
; Branch labels are newly assigned; assembly emission is byte-checked.
org $05F2
UploadPendingVDPData:
    ld a,($C037)
    or a
    ret z
    ld a,($FFFF)
    push af
    ld a,($FFFC)
    push af
    ld a,$03
    ld ($FFFF),a
    xor a
    ld ($FFFC),a
    ld ($C037),a
    out ($BF),a
    ld a,$67
    out ($BF),a
    ld hl,($C035)
    ld bc,$00BE
.PendingCopy:
    outi
    djnz .PendingCopy
    pop af
    ld ($FFFC),a
    pop af
    ld ($FFFF),a
    ret

org $06C1
VDPWriteROMLinear:
    rst $28
    ld a,c
    or a
    jr z,.NoExtraBlock
    inc b
.NoExtraBlock:
    ld a,b
    ld b,c
    ld c,$BE
.ByteLoop:
    outi
    nop
    jr nz,.ByteLoop
    dec a
    jr nz,.ByteLoop
    ret

org $06D4
VDPFillWordPattern:
    rst $28
    ld a,c
    or a
    jr z,.NoExtraBlock
    inc b
.NoExtraBlock:
.WordLoop:
    ld a,l
    out ($BE),a
    push af
    pop af
    ld a,h
    out ($BE),a
    dec c
    jr nz,.WordLoop
    djnz .WordLoop
    ret

org $0BA1
VDPExpandBank3PairPlanes:
    ld a,$03
    ld ($FFFF),a
    rst $28
.BlockLoop:
    ld b,$10
.ByteLoop:
    ld a,(hl)
    out ($BE),a
    inc hl
    xor a
    nop
    out ($BE),a
    djnz .ByteLoop
    dec c
    jr nz,.BlockLoop
    ret
