; Ys fixed bank 0: source-only 16384-byte reconstruction.
; Full byte parity does not imply resolved graphics/data semantics.
org $0000
    di
    im 1
    jp $0089
; padding_0006: fill_ff, $0006-$0007
    db $FF, $FF
    add a,a
    add a,l
    ld l,a
    jr nc,$000E
    inc h
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    jp (hl)
; padding_0013: fill_ff, $0013-$0017
    db $FF, $FF, $FF, $FF, $FF
    add a,a
    add a,l
    ld l,a
    jr nc,$001E
    inc h
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ret
; padding_0023: fill_ff, $0023-$0027
    db $FF, $FF, $FF, $FF, $FF
    di
    ld a,e
    out ($BF),a
    ld a,d
    out ($BF),a
    ei
    ret
; padding_0031: fill_ff, $0031-$0037
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF
    push af
    in a,($BF)
    or a
    jp p,$0540
    jp $0102
    ld ($C021),a
    ei
    ld a,($C021)
    or a
    jr nz,$0046
    ret
    ld a,$02
    ld ($FFFF),a
    call $8842
    jp $0BC5
; padding_0058: fill_ff, $0058-$0065
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    push af
    ld a,($C01F)
    cp $0D
    jr z,$0080
    cp $06
    jr z,$0075
    pop af
    retn
    ld ($C020),a
    ld a,$0D
    ld ($C01F),a
    pop af
    retn
    ld a,($C020)
    ld ($C01F),a
    pop af
    retn
    ld sp,$DFF0
    ld hl,$FFFC
    ld (hl),$80
    inc hl
    ld (hl),$00
    inc hl
    ld (hl),$01
    inc hl
    ld (hl),$02
    xor a
    ld ($DE60),a
    dec a
    ld ($C001),a
    call $079A
    di
    ld sp,$DFF0
    ld hl,$C010
    ld de,$C011
    ld bc,$1E4F
    ld (hl),$00
    ldir
    ld a,$02
    ld ($FFFF),a
    call $8803
    call $0749
    call $0BC5
    ld a,($C018)
    ld ($C031),a
    ld a,($C01F)
    ld hl,$00D4
    rst $0008
    jp $00C4
; unresolved_00D4: unresolved, $00D4-$00FB
    db $FC, $00, $4A, $0C, $DE, $0E, $23, $0F, $39, $0F, $71, $0F, $C9, $0D, $05, $2C
    db $59, $44, $70, $3F, $05, $38, $CC, $38, $45, $3C, $4D, $00, $63, $4B, $39, $43
    db $A8, $63, $07, $6C, $26, $6A, $25, $7C
    ld a,$01
    ld ($C01F),a
    ret
    ld a,($C021)
    or a
    jr z,$0148
    ld hl,$C01A
    ld bc,$8BBF
    outd
    out (c),b
    outd
    out (c),b
    outd
    out (c),b
    ld hl,$85FF
    out (c),l
    out (c),h
    ld hl,$01AA
    rst $0008
    ei
    ld a,($C01F)
    cp $0D
    jr z,$0138
    call $0773
    ld a,$02
    ld ($FFFF),a
    call $8000
    in a,($DD)
    and $10
    jp z,$00A5
    xor a
    ld ($C021),a
    ld ($C10F),a
    pop af
    ret
    push bc
    push de
    push hl
    ex af,af'
    exx
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    ld a,($FFFF)
    push af
    ld a,($FFFC)
    push af
    xor a
    ld ($FFFC),a
    ld a,$02
    ld ($FFFF),a
    call $8000
    ld a,($C010)
    and $10
    jr z,$018F
    ld a,($C011)
    and $40
    jr z,$018F
    xor a
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld a,$FF
    out ($BF),a
    ld a,$85
    out ($BF),a
    ld a,($C031)
    out ($BF),a
    ld a,$88
    out ($BF),a
    ld a,$01
    ld ($C10F),a
    pop af
    ld ($FFFC),a
    pop af
    ld ($FFFF),a
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    exx
    ex af,af'
    pop hl
    pop de
    pop bc
    pop af
    ei
    ret
; bootstrap_dispatch_4: pointer_words, $01AC-$01B3
    dw $01B4, $01BA, $01D7, $03B8
    call $0427
    jp $03E8
    call $0427
    call $27F9
    ld a,($C198)
    or a
    jr z,$01CE
    ld a,$07
    ld ($FFFF),a
    jp $8819
    call $2864
    call $2899
    jp $0406
    call $0427
    ld a,$03
    ld ($FFFF),a
    ld a,($C105)
    ld hl,$01EB
    rst $0008
    xor a
    ld ($C105),a
    ret
; bootstrap_routines_9: pointer_words, $01EB-$01FC
    dw $01FD, $01FE, $0288, $02B1, $02C2, $032A, $0339, $035D
    dw $0389
    ret
    ld hl,($C10A)
    ld de,($C108)
    ld b,d
    ld a,($C10C)
    or a
    jr z,$0238
    inc a
    cp e
    jr z,$0260
    call $03A9
    ld a,b
    cp d
    jr z,$0225
    cp $01
    jr z,$022F
    ld a,$E7
    out ($BE),a
    ld a,$18
    out ($BE),a
    djnz $0210
    ld a,$EA
    out ($BE),a
    ld a,$18
    out ($BE),a
    djnz $0210
    ld a,$EA
    out ($BE),a
    ld a,$1A
    out ($BE),a
    ret
    call $03A9
    ld a,b
    cp d
    jr z,$024D
    cp $01
    jr z,$0257
    ld a,$E9
    out ($BE),a
    ld a,$18
    out ($BE),a
    djnz $0238
    ld a,$E8
    out ($BE),a
    ld a,$18
    out ($BE),a
    djnz $0238
    ld a,$E8
    out ($BE),a
    ld a,$1A
    out ($BE),a
    ret
    call $03A9
    ld a,b
    cp d
    jr z,$0275
    cp $01
    jr z,$027F
    ld a,$E9
    out ($BE),a
    ld a,$1C
    out ($BE),a
    djnz $0260
    ld a,$E8
    out ($BE),a
    ld a,$1C
    out ($BE),a
    djnz $0260
    ld a,$E8
    out ($BE),a
    ld a,$1E
    out ($BE),a
    ret
    ld hl,($C10A)
    ld de,($C108)
    ld bc,($C106)
    ld a,($FFFC)
    or $08
    ld ($FFFC),a
    call $03A9
    ld a,(de)
    out ($BE),a
    inc de
    ld a,(de)
    out ($BE),a
    inc de
    djnz $029B
    ld a,($FFFC)
    and $F7
    ld ($FFFC),a
    ret
    ld hl,($C10A)
    ld de,($C108)
    call $03A9
    ld a,e
    out ($BE),a
    ld a,d
    out ($BE),a
    ret
    ld a,$03
    ld ($FFFF),a
    ld hl,($C10A)
    ld de,($C108)
    ld a,l
    out ($BF),a
    ld a,h
    out ($BF),a
    ld a,(de)
    cp $FF
    ret z
    ld l,a
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld bc,$914A
    add hl,bc
    xor a
    ld c,$BE
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    outi
    out ($BE),a
    inc de
    jp $02D4
    ld hl,($C10A)
    ld a,l
    out ($BF),a
    ld a,h
    out ($BF),a
    ld a,($C10C)
    out ($BE),a
    ret
    ld hl,($C10A)
    ld de,($C108)
    ld bc,($C106)
    ld a,e
    out ($BF),a
    ld a,d
    out ($BF),a
    ld a,c
    or a
    jr z,$034F
    inc b
    ld a,b
    ld b,c
    ld c,$BE
    outi
    jp nz,$0353
    dec a
    jp nz,$0353
    ret
    ld de,($C101)
    ld hl,$A200
    add hl,de
    ex de,hl
    ld a,e
    out ($BF),a
    ld a,d
    out ($BF),a
    ld bc,$20BE
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    bit 5,d
    jr z,$037E
    out (c),e
    out (c),d
    djnz $036F
    ret
    ld a,$E7
    out ($BE),a
    ld a,$18
    out ($BE),a
    djnz $036F
    ret
    ld hl,($C10A)
    ld de,($C108)
    ld bc,($C106)
    ld a,e
    out ($BF),a
    ld a,d
    out ($BF),a
    ld a,c
    or a
    jr z,$039F
    inc b
    ld a,b
    ld b,c
    ld c,$BE
    otir
    dec a
    jr nz,$03A3
    ret
    ld a,l
    out ($BF),a
    ld a,h
    out ($BF),a
    ld a,l
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld l,a
    ret
    call $0427
    call $2864
    call $2899
    ld a,($C10E)
    or a
    call nz,$0389
    xor a
    ld ($C10E),a
    ld a,($C10D)
    or a
    ret z
    ld hl,$C040
    ld c,$BF
    outi
    outi
    dec c
    outi
    outi
    inc c
    dec a
    jp nz,$03D6
    ld ($C10D),a
    ret
    ld a,($C02C)
    or a
    ret z
    xor a
    ld ($C02C),a
    ld b,$C0
    djnz $03F3
    out ($BF),a
    ld a,$C0
    out ($BF),a
    ld hl,$C160
    ld bc,$40BE
    outi
    djnz $0401
    ret
    ld a,($C197)
    or a
    ret z
    ld b,$14
    djnz $040D
    xor a
    ld ($C197),a
    ld a,$0D
    out ($BF),a
    ld a,$C0
    out ($BF),a
    ld hl,$C16D
    ld c,$BE
    outi
    outi
    outi
    ret
    xor a
    out ($BF),a
    ld a,$7F
    out ($BF),a
    ld c,$BE
    ld hl,$DD00
    call $04BF
    inc a
    out ($BF),a
    dec a
    out ($BF),a
    ld hl,$DD40
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    outi
    ret
    push hl
    ld hl,($C022)
    jp (hl)
    ld a,$9B
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld hl,$0557
    ld ($C022),hl
    pop hl
    pop af
    ei
    ret
    ld a,$01
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld hl,$0575
    ld ($C022),hl
    push bc
    call $05F2
    ld a,($C198)
    or a
    call nz,$0624
    pop bc
    pop hl
    pop af
    ei
    ret
    ld a,$07
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld hl,$0587
    ld ($C022),hl
    pop hl
    pop af
    ei
    ret
    ld hl,$05A8
    ld ($C022),hl
    pop hl
    xor a
    out ($BF),a
    ld a,$88
    out ($BF),a
    ld a,$F9
    out ($BF),a
    ld a,$82
    out ($BF),a
    ld a,$EF
    out ($BF),a
    ld a,$85
    out ($BF),a
    pop af
    ei
    ret
    ld hl,$05BF
    ld ($C022),hl
    pop hl
    ld a,$02
    dec a
    jr nz,$05B1
    ld a,$FF
    out ($BF),a
    ld a,$82
    out ($BF),a
    pop af
    ei
    ret
    ld hl,$05D9
    ld ($C022),hl
    ld a,$FF
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld a,$F9
    out ($BF),a
    ld a,$82
    out ($BF),a
    pop hl
    pop af
    ei
    ret
    ld hl,$0545
    ld ($C022),hl
    xor a
    out ($BF),a
    ld a,$8A
    out ($BF),a
    ld a,$FF
    out ($BF),a
    ld a,$82
    out ($BF),a
    pop hl
    pop af
    ei
    ret
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
    outi
    djnz $0617
    pop af
    ld ($FFFC),a
    pop af
    ld ($FFFF),a
    ret
    ld bc,$0040
    ld hl,$C103
    ld a,(hl)
    cp $01
    jr c,$065D
    ld (hl),b
    jr z,$064D
    ld hl,($C580)
    add hl,bc
    ld a,h
    cp $7F
    jr c,$063D
    ld h,$78
    ld c,$BF
    out (c),l
    out (c),h
    ld hl,$C582
    ld bc,$7CBE
    outi
    djnz $0649
    ld hl,$C580
    ld c,$BF
    outi
    outi
    ld bc,$7CBE
    outi
    djnz $0659
    ld hl,$C104
    ld a,(hl)
    cp $01
    ret c
    ld (hl),b
    jr z,$0684
    ld hl,($C5C0)
    ld c,$40
    add hl,bc
    ld a,h
    cp $7F
    jr c,$0674
    ld h,$78
    ld c,$BF
    out (c),l
    out (c),h
    ld hl,$C5C2
    ld bc,$7CBE
    outi
    djnz $0680
    ld hl,$C5C0
    ld c,$BF
    outi
    outi
    ld bc,$7CBE
    outi
    djnz $0690
    ret
    ld c,$04
    ld b,c
    push bc
    push de
    ld a,(hl)
    inc hl
    or a
    jr z,$06BB
    ld b,a
    res 7,b
    rlca
    ex af,af'
    rst $0028
    ld a,(hl)
    out ($BE),a
    ex af,af'
    jr nc,$06AC
    inc hl
    ex af,af'
    ld a,c
    add a,e
    ld e,a
    jr nc,$06B3
    inc d
    djnz $06A4
    ex af,af'
    jr c,$069A
    inc hl
    jr $069A
    pop de
    inc de
    pop bc
    djnz $0698
    ret
    rst $0028
    ld a,c
    or a
    jr z,$06C7
    inc b
    ld a,b
    ld b,c
    ld c,$BE
    outi
    nop
    jr nz,$06CB
    dec a
    jr nz,$06CB
    ret
    rst $0028
    ld a,c
    or a
    jr z,$06DA
    inc b
    ld a,l
    out ($BE),a
    push af
    pop af
    ld a,h
    out ($BE),a
    dec c
    jr nz,$06DA
    djnz $06DA
    ret
    push bc
    rst $0028
    ld b,c
    ld c,$BE
    outi
    ld a,($C026)
    nop
    out (c),a
    nop
    jr nz,$06ED
    ex de,hl
    ld bc,$0040
    add hl,bc
    ex de,hl
    pop bc
    djnz $06E8
    ret
    push bc
    rst $0028
    ld b,c
    ld c,$BE
    outi
    nop
    jp nz,$0707
    ld a,$40
    add a,e
    ld e,a
    jr nc,$0714
    inc d
    pop bc
    djnz $0702
    ret
    ld ($C027),a
    rst $0028
    ld a,(hl)
    exx
    ld c,$BE
    ld b,$04
    ld h,a
    ld a,($C027)
    rra
    ld d,h
    jr c,$072C
    ld d,$00
    out (c),d
    djnz $0726
    exx
    inc hl
    dec bc
    ld a,b
    or c
    jp nz,$071C
    ret
    rst $0028
    ld c,$BE
    outi
    ld a,($C026)
    nop
    out (c),a
    nop
    jp nz,$073C
    ret
    ld hl,$0768
    ld de,$C010
    ld bc,$0B80
    ld a,(hl)
    ld (de),a
    out ($BF),a
    ld a,c
    out ($BF),a
    inc hl
    inc de
    inc c
    djnz $0752
    ld de,$C010
    xor a
    push af
    rst $0028
    pop af
    out ($BE),a
    ret
; unresolved_0768: unresolved, $0768-$0772
    db $26, $A0, $FF, $FF, $FF, $FF, $FF, $00, $00, $00, $00
    in a,($DC)
    ld hl,$C01B
    or $C0
    cpl
    ld b,a
    xor (hl)
    ld (hl),b
    inc hl
    and b
    ld (hl),a
    ret
; cartridge_title: ascii, $0782-$0799
    db $41, $6E, $63, $69, $65, $6E, $74, $20, $59, $73, $20, $56, $61, $6E, $69, $73
    db $68, $65, $64, $20, $4F, $6D, $65, $6E
    ld a,($FFFC)
    or $08
    ld ($FFFC),a
    ld hl,$0782
    ld de,$8010
    ld b,$18
    ld a,(de)
    cp (hl)
    jr nz,$07B4
    inc hl
    inc de
    djnz $07AA
    jr $07CC
    ld hl,$8010
    ld de,$8011
    ld bc,$1FEE
    ld (hl),$00
    ldir
    ld hl,$0782
    ld de,$8010
    ld bc,$0018
    ldir
    ld a,($FFFC)
    and $F7
    ld ($FFFC),a
    ret
    ld a,(hl)
    cp $FF
    jr z,$07FF
    or a
    jp m,$07FA
    inc a
    ld b,a
    push hl
    ld hl,$0801
    ld a,(hl)
    inc hl
    or a
    jp m,$07E4
    djnz $07E4
    add a,$80
    ld (de),a
    inc de
    ld a,(hl)
    inc hl
    or a
    jp m,$07EE
    pop hl
    inc hl
    jr $07D5
    ld (de),a
    inc hl
    inc de
    jr $07D5
    ld (de),a
    ret
; unresolved_0801: unresolved, $0801-$0A5A
    db $55, $CA, $C7, $55, $D0, $50, $C8, $4B, $D4, $4B, $CF, $55, $CA, $D0, $D6, $58
    db $C3, $D4, $55, $CA, $C3, $D5, $48, $D3, $D0, $CE, $4E, $DA, $48, $D0, $D3, $4E
    db $C7, $3C, $CA, $C7, $55, $CA, $C7, $D3, $C7, $55, $CA, $C7, $C7, $55, $D0, $D8
    db $C7, $D3, $47, $D7, $CB, $B2, $44, $C7, $32, $C8, $45, $C3, $CF, $4F, $D0, $D5
    db $4B, $D5, $4A, $C7, $D3, $C7, $55, $CA, $CB, $D4, $32, $D5, $45, $D3, $C7, $C3
    db $D5, $D6, $D3, $C7, $D4, $4E, $C3, $CF, $31, $C7, $54, $D5, $D3, $C3, $CF, $C9
    db $C7, $58, $CB, $B2, $B2, $44, $D0, $D0, $CD, $D4, $50, $CF, $43, $CF, $C6, $44
    db $DA, $4A, $C3, $D7, $C7, $45, $B2, $D0, $C3, $CD, $55, $CA, $CB, $C7, $D7, $C7
    db $D4, $36, $DA, $50, $D6, $D3, $4A, $C7, $C3, $D3, $C6, $41, $D4, $4D, $CF, $D0
    db $D8, $3C, $CA, $D0, $D6, $4A, $C3, $D4, $44, $C7, $C8, $D0, $D3, $C7, $55, $D0
    db $D8, $CF, $43, $CE, $32, $EC, $CE, $3C, $CA, $C7, $D3, $C7, $45, $D0, $CE, $C7
    db $55, $CB, $CE, $C7, $44, $D6, $D5, $43, $D3, $D5, $54, $D0, $CE, $C7, $49, $C7
    db $D5, $3F, $CA, $C7, $CF, $55, $CA, $C7, $DA, $54, $D5, $C3, $D5, $D6, $C7, $D4
    db $54, $D0, $44, $C7, $C7, $CF, $4E, $D6, $D4, $D5, $3A, $AA, $BD, $AB, $AA, $5A
    db $D0, $D6, $43, $D3, $D0, $D6, $CF, $C6, $54, $C3, $D8, $48, $CB, $C7, $B2, $C6
    db $D4, $43, $D3, $C7, $4A, $C7, $B2, $D1, $45, $C3, $CF, $D4, $D5, $54, $CB, $B2
    db $D7, $C7, $D3, $48, $D0, $D6, $CF, $C6, $49, $D0, $32, $C3, $CF, $C6, $4F, $C3
    db $CE, $C7, $C6, $4A, $C7, $58, $C7, $4A, $C3, $C6, $54, $D0, $CE, $C7, $D5, $CA
    db $CB, $CF, $C9, $3C, $CA, $C3, $CF, $CD, $55, $C3, $CD, $C7, $50, $B2, $C6, $49
    db $CB, $D3, $B2, $54, $D0, $CE, $C7, $D8, $CA, $C7, $D3, $C7, $45, $D0, $CE, $CB
    db $CF, $C9, $54, $D5, $D0, $B2, $C7, $CF, $3C, $CA, $C7, $D3, $C7, $EC, $D4, $45
    db $C3, $B2, $B2, $C7, $C6, $38, $B2, $C7, $C3, $D4, $C7, $57, $CB, $B2, $B2, $C3
    db $C9, $C7, $42, $AE, $B8, $B2, $B4, $2D, $A0, $A0, $B6, $AE, $AD, $49, $D0, $C6
    db $C6, $C7, $D4, $D4, $C7, $D4, $35, $BD, $BC, $B1, $AE, $BA, $51, $D3, $D0, $D5
    db $C7, $C5, $D5, $4A, $C3, $D3, $CE, $D0, $CF, $CB, $C5, $C3, $58, $CB, $D5, $CA
    db $D0, $D6, $D5, $47, $D4, $C5, $C3, $D1, $C7, $2A, $BA, $A0, $B7, $55, $CA, $D0
    db $D6, $C9, $CA, $33, $AE, $B6, $B6, $AA, $43, $CF, $DA, $D5, $CA, $CB, $CF, $C9
    db $48, $D3, $CB, $C9, $CA, $D5, $C7, $CF, $CB, $CF, $C9, $55, $D3, $D0, $D6, $C4
    db $B2, $C7, $3A, $A0, $AD, $AA, $43, $C4, $C3, $CF, $C6, $D0, $CF, $C7, $C6, $54
    db $D5, $D3, $D0, $CF, $C9, $54, $D0, $CE, $C7, $D0, $CF, $C7, $54, $CA, $CB, $C7
    db $B2, $C6, $3F, $CB, $B2, $B2, $D4, $D5, $43, $CF, $DA, $CE, $D0, $D3, $C7, $51
    db $C7, $D3, $D4, $D0, $CF, $4A, $CB, $B2, $B2, $D4, $48, $C7, $C7, $B2, $CB, $CF
    db $C9, $54, $C7, $C3, $B2, $C7, $C6, $51, $D0, $C7, $D5, $C7, $D4, $D4, $4E, $C3
    db $D5, $D5, $C7, $D3, $43, $C9, $C3, $CB, $CF, $44, $C7, $C9, $CB, $CF, $45, $D0
    db $D3, $D1, $D4, $C7, $49, $B2, $D0, $D8, $CB, $CF, $C9, $46, $D0, $CF, $EC, $D5
    db $44, $C7, $D5, $D5, $C7, $D3, $45, $C3, $CF, $EC, $D5, $55, $D3, $C3, $D1, $D1
    db $C7, $C6, $58, $CA, $CB, $C5, $CA, $45, $C3, $D1, $D5, $D6, $D3, $C7, $C6, $4D
    db $CB, $B2, $B2, $C7, $C6, $2D, $AE, $B4, $BC, $00
    call $0A80
    ld de,$8800
    rst $0028
    inc d
    rst $0028
    xor a
    ld ($C018),a
    ld ($C019),a
    ld hl,$0000
    ld de,$4000
    ld bc,$0020
    call $06D4
    ld de,$7800
    ld bc,$0380
    jp $06D4
    call $0AE8
    ld a,($C010)
    and $EF
    ld e,a
    ld d,$80
    rst $0028
    ld a,e
    ld ($C010),a
    ld a,($C011)
    and $BF
    ld ($C011),a
    ld e,a
    ld d,$81
    rst $0028
    ld de,$7F00
    ld a,$D0
    ld ($DD00),a
    jp $0762
    ld a,($C011)
    ld e,a
    ld d,$81
    set 5,e
    rst $0028
    in a,($BF)
    call $0BC5
    set 6,e
    rst $0028
    ld a,e
    ld ($C011),a
    ld a,($C010)
    ld e,a
    ld d,$80
    rst $0028
    call $0B10
    ld a,$03
    ld hl,$C530
    ld de,$C160
    ld bc,$0020
    call $0B19
    call $0B22
    ld hl,$C02C
    ld (hl),$01
    ld b,$03
    call $0BC5
    djnz $0ADE
    dec a
    jp p,$0AC8
    ret
    call $0B10
    xor a
    call $0B22
    ld hl,$C02C
    ld (hl),$01
    ld b,$03
    call $0BC5
    djnz $0AF6
    inc a
    cp $04
    jr nz,$0AEC
    ld a,$07
    ld ($FFFF),a
    ld hl,$B9C3
    ld de,$C170
    ld bc,$0010
    jr $0B19
    ld hl,$C160
    ld de,$C530
    ld bc,$0020
    push af
    ldi
    ld a,b
    or c
    jr nz,$0B1A
    pop af
    ret
    ld hl,$C160
    push af
    ld c,a
    ld b,$20
    rld
    and $03
    sub c
    jr nc,$0B31
    xor a
    rld
    ld e,a
    rrca
    rrca
    and $03
    sub c
    jr nc,$0B3C
    xor a
    rlca
    rlca
    ld d,a
    ld a,e
    and $03
    sub c
    jr nc,$0B46
    xor a
    or d
    rld
    inc hl
    djnz $0B29
    pop af
    ret
    ld a,$01
    jr $0B64
    ld a,$05
    jr $0B64
    ld a,$0A
    jr $0B64
    ld a,$0F
    jr $0B64
    ld a,$14
    jr $0B64
    ld a,$19
    ld ($DE6C),a
    xor a
    ld ($C02D),a
    ld a,$02
    ld ($FFFF),a
    jp $8112
    ld a,($C1B9)
    or a
    ret p
    ld a,$07
    ld ($FFFF),a
    ld hl,$C160
    ld b,$10
    ld c,$03
    ld d,(hl)
    ld e,$00
    ld a,d
    and $03
    add a,e
    ld e,a
    srl d
    srl d
    dec c
    jr nz,$0B87
    ld de,$B9A9
    add a,e
    ld e,a
    jr nc,$0B9B
    inc d
    ld a,(de)
    ld (hl),a
    inc hl
    djnz $0B82
    ret
    ld a,$03
    ld ($FFFF),a
    rst $0028
    ld b,$10
    ld a,(hl)
    out ($BE),a
    inc hl
    xor a
    nop
    out ($BE),a
    djnz $0BA9
    dec c
    jr nz,$0BA7
    ret
    ld b,$14
    ld de,$FFFF
    ld hl,$39DE
    add hl,de
    jr c,$0BBF
    djnz $0BBC
    ret
    push af
    push bc
    push de
    push hl
    ex af,af'
    exx
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    ld a,($FFFF)
    push af
    ld a,$01
    call $0042
    pop af
    ld ($FFFF),a
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    exx
    ex af,af'
    pop hl
    pop de
    pop bc
    pop af
    ret
    ld b,c
    push de
    push bc
    ld a,(hl)
    or a
    jr z,$0C19
    jp p,$0C0A
    and $7F
    ld b,a
    inc hl
    ld a,(hl)
    ld (de),a
    ld a,c
    add a,e
    ld e,a
    jr nc,$0C05
    inc d
    djnz $0BFC
    inc hl
    jr $0BF2
    ld b,a
    inc hl
    ld a,(hl)
    ld (de),a
    ld a,c
    add a,e
    ld e,a
    jr nc,$0C14
    inc d
    djnz $0C0C
    inc hl
    jr $0BF2
    pop bc
    pop de
    inc de
    inc hl
    djnz $0BF0
    ret
    ld a,(hl)
    inc hl
    or a
    ret z
    jp p,$0C33
    and $7F
    ld b,a
    ld a,(hl)
    ld (de),a
    inc de
    inc hl
    djnz $0C2A
    jp $0C20
    ld b,a
    ld a,(hl)
    ld (de),a
    inc de
    inc a
    djnz $0C35
    inc hl
    jp $0C20
    add a,$40
    ld hl,$FFFF
    ld (hl),$0C
    ld h,$80
    ld l,a
    ld a,(hl)
    ret
    call $0A5B
    ld a,$02
    ld ($FFFF),a
    call $8803
    ld ($C02E),sp
    ld a,$05
    ld ($FFFF),a
    ld hl,$B61A
    ld de,$C600
    call $0C20
    ld hl,$C600
    ld de,$D600
    ld c,$02
    call $0BEF
    ld hl,$D600
    ld de,$7900
    ld bc,$0600
    call $06C1
    ld hl,$8000
    ld de,$4000
    call $0695
    ld hl,$A4D1
    ld de,$C600
    ld c,$04
    call $0BEF
    ld a,$20
    ld ($C019),a
    ld a,$81
    ld ($DE64),a
    call $0AA7
    call $0D89
    ld bc,$0168
    call $0CD9
    call $0CF8
    ld bc,$00B4
    call $0CD9
    call $0CE2
    ld bc,$00F0
    call $0CD9
    call $0D0E
    call $0CCE
    jr $0CBD
    ld sp,($C02E)
    ld a,$02
    ld ($C01F),a
    jp $0B56
    call $0BC5
    ld a,($C01C)
    and $30
    jr nz,$0CC2
    ret
    call $0CCE
    dec bc
    ld a,b
    or c
    jr nz,$0CD9
    ret
    ld ix,$B831
    ld b,$0C
    push bc
    ld hl,$C600
    ld de,$5B20
    ld b,$20
    call $0D49
    pop bc
    djnz $0CE8
    ret
    ld ix,$B831
    ld b,$0C
    push bc
    ld hl,$CA00
    ld de,$5F20
    ld b,$67
    call $0D4F
    pop bc
    djnz $0CFE
    ret
    ld hl,$D6E0
    ld de,$6C00
    ld c,$08
    call $0CCE
    call $0CCE
    call $0CCE
    push hl
    push de
    ld b,$20
    push bc
    ld bc,$0004
    call $06C1
    ld a,$1C
    add a,l
    ld l,a
    jr nc,$0D31
    inc h
    ld a,$20
    add a,e
    ld e,a
    jr nc,$0D38
    inc d
    pop bc
    djnz $0D23
    pop de
    pop hl
    inc hl
    inc hl
    inc hl
    inc hl
    inc de
    inc de
    inc de
    inc de
    dec c
    jr nz,$0D16
    ret
    call $0CCE
    call $0CCE
    call $0CCE
    push bc
    ld c,$08
    ld b,$04
    push bc
    res 6,d
    rst $0028
    ld c,(ix+0)
    ld a,(hl)
    and c
    ld b,a
    ld a,c
    cpl
    ld c,a
    in a,($BE)
    and c
    ld c,a
    set 6,d
    rst $0028
    ld a,c
    or b
    out ($BE),a
    inc de
    inc hl
    pop bc
    djnz $0D57
    inc ix
    dec c
    jr nz,$0D55
    ld bc,$FFF8
    add ix,bc
    pop bc
    djnz $0D52
    push bc
    ld bc,$0008
    add ix,bc
    pop bc
    ret
    ld de,$1030
    call $0D98
    ld de,$0103
    call $0D98
    ld de,$040C
    ld c,e
    ld b,$03
    push bc
    ld hl,$B820
    ld iy,$C160
    ld b,$11
    ld a,(hl)
    and e
    cp c
    jr c,$0DB1
    ld a,(iy+0)
    add a,d
    ld (iy+0),a
    inc hl
    inc iy
    djnz $0DA5
    ld hl,$C02C
    ld (hl),$01
    ld b,$08
    call $0CCE
    djnz $0DBD
    pop bc
    ld a,c
    sub d
    ld c,a
    djnz $0D9B
    ret
    call $0FC8
    call $476C
    call $60B5
    call $19CC
    ld a,$07
    ld ($FFFF),a
    call $86C1
    call $2BF1
    ld hl,$C11B
    inc (hl)
    ld a,$02
    call $0042
    ld a,($C01F)
    cp $06
    ret nz
    ld a,($C01C)
    and $30
    ret z
    bit 5,a
    jr nz,$0DFE
    bit 4,a
    jr nz,$0E04
    ret
    ld a,$09
    ld ($C01F),a
    ret
    ld hl,$C1B6
    bit 7,(hl)
    jr nz,$0E1D
    inc hl
    bit 7,(hl)
    jr nz,$0E23
    inc hl
    bit 7,(hl)
    jr nz,$0E46
    inc hl
    inc hl
    inc hl
    bit 7,(hl)
    jr nz,$0E82
    ret
    call $0ED8
    jp $6215
    call $0ED8
    ld a,$AD
    call $1D8F
    ld b,$03
    push bc
    call $0AE8
    ld hl,$C530
    ld de,$C160
    ld bc,$0020
    call $0B19
    call $0AC3
    pop bc
    djnz $0E2D
    jp $0EFC
    ld a,($C1E2)
    dec a
    ld ($C1E2),a
    call z,$0ED8
    ld a,$20
    ld ($C1E3),a
    ld a,$AB
    ld ($DE64),a
    ld a,$07
    ld ($FFFF),a
    ld b,$06
    push bc
    ld hl,$B9B3
    call $0E6F
    call $0E6F
    pop bc
    djnz $0E61
    ret
    ld de,$C170
    ld bc,$0010
    call $0B19
    ld a,$01
    ld ($C02C),a
    ld b,$06
    jp $64CD
    ld a,$A8
    ld ($DE64),a
    ld a,($C181)
    cp $1F
    ret nz
    ld a,($C20C)
    and $0F
    ret nz
    ld a,($C1DE)
    or a
    ret nz
    ld hl,($C184)
    ld a,($C210)
    ld c,a
    ld b,$00
    add hl,bc
    ld a,l
    and $F0
    ld l,a
    add hl,hl
    add hl,hl
    ex de,hl
    ld hl,($C182)
    ld a,($C211)
    sub $08
    ld c,a
    add hl,bc
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    add hl,de
    ld a,l
    and $7F
    cp $40
    ret nz
    ld ($C1DE),a
    call $1FD4
    ld a,$B5
    ld ($DE64),a
    jp $267B
    xor a
    ld ($C1B5),a
    ld (hl),a
    ret
    ld hl,$C100
    ld de,$C101
    ld bc,$00FF
    ld (hl),l
    call $0B19
    ld a,$01
    ld ($C1A0),a
    ld hl,$03E8
    ld ($C225),hl
    ld hl,$0000
    ld ($C227),hl
    xor a
    ld ($C181),a
    ld a,$01
    ld ($C20C),a
    call $0F7D
    ld a,($C22A)
    ld ($C222),a
    ld hl,$0180
    ld de,$0000
    ld bc,$8860
    call $2654
    ld hl,$0308
    ld de,$0190
    call $2660
    call $0A5B
    ld hl,$C100
    ld de,$C101
    ld bc,$000F
    ld (hl),$00
    call $0B19
    call $1B1F
    jr $0F3C
    call $0A5B
    call $0F7D
    call $1E3F
    call $1DB2
    call $1FD4
    call $1D63
    call $0B73
    call $267B
    call $277D
    ld a,($C018)
    ld ($C031),a
    ld hl,$0545
    ld ($C022),hl
    ld a,($C010)
    or $10
    ld ($C010),a
    call $0AA7
    ld a,$06
    ld ($C01F),a
    ret
    call $267B
    call $1D63
    ld a,$06
    ld ($C01F),a
    ret
    ld hl,$B918
    ld ($C217),hl
    ld hl,$C1AA
    xor a
    ld b,$05
    or (hl)
    inc hl
    djnz $0F89
    rlca
    rl c
    ld hl,$C1A4
    xor a
    ld b,$05
    or (hl)
    inc hl
    djnz $0F96
    rlca
    rl c
    ld a,$03
    ld ($FFFF),a
    ld a,c
    and $03
    ld hl,$9000
    rst $0018
    ld ($C033),hl
    ld a,$01
    call $0FE1
    ld a,$08
    ld ($FFFF),a
    call $BEE8
    ld a,($C1C1)
    rlca
    ret nc
    ld a,($C1BA)
    rlca
    ret c
    xor a
    ld ($C222),a
    ret
    ld a,($C214)
    push af
    ld ix,$C200
    ld bc,($C01B)
    ld a,($C200)
    ld hl,$0FF7
    rst $0008
    pop af
    ld hl,$C214
    xor (hl)
    ret z
    ld ($C037),a
    ld c,$00
    ld a,($C214)
    and $07
    rra
    rr c
    ld b,a
    ld hl,($C033)
    add hl,bc
    ld ($C035),hl
    ret
; object_setup_dispatch_3: pointer_words, $0FF7-$0FFC
    dw $0FFD, $0FFE, $12A9
    ret
    ld hl,$0000
    ld ($C110),hl
    ld ($C112),hl
    ld a,c
    and $0F
    jr nz,$1013
    ld (ix+13),a
    ld (ix+22),a
    ret
    dec (ix+22)
    jp p,$1025
    ld (ix+22),$09
    ld a,(ix+20)
    xor $01
    ld (ix+20),a
    ld a,($C20C)
    ld hl,$102E
    jp $0008
    inc a
    djnz $1033
    ld de,$11A8
    ld a,($3E12)
    ld c,$32
    rra
    ret nz
    ret
    bit 0,c
    jp nz,$1111
    bit 3,c
    jp nz,$11B7
    bit 2,c
    jp nz,$1249
    ld (ix+13),$03
    ld a,$01
    ld ($C20C),a
    ld b,(ix+20)
    srl b
    rla
    ld ($C214),a
    ld bc,$F800
    call $13B2
    rlca
    jr c,$10AD
    ld bc,$0700
    call $13B5
    rlca
    jr c,$10E2
    ld bc,$0000
    call $13B5
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    ld a,$01
    ld ($C11E),a
    ld a,($C210)
    cp $80
    jr nc,$108C
    inc (ix+16)
    ret
    ld hl,$0001
    ld ($C112),hl
    call $28CE
    ret nc
    ld a,($C210)
    cp $A0
    jr nc,$10A1
    inc (ix+16)
    ret
    ld a,($C11D)
    and $02
    ret z
    ld a,$0E
    ld ($C01F),a
    ret
    ld bc,$0700
    call $13B5
    rlca
    jr nc,$10C2
    ld bc,$FF00
    call $13B2
    bit 6,a
    jp nz,$1036
    ret
    ld bc,$FF00
    call $13B2
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    ld bc,$08FF
    call $13B5
    rlca
    ret c
    ld bc,$08F8
    call $13B5
    rlca
    ret c
    jp $11DB
    ld bc,$0000
    call $13B5
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    ld bc,$F7FF
    call $13B5
    rlca
    ret c
    ld bc,$F7F8
    call $13B5
    rlca
    ret c
    jp $126D
    bit 1,c
    jp nz,$104B
    bit 3,c
    jp nz,$11B7
    bit 2,c
    jp nz,$1249
    ld (ix+13),$02
    ld a,$00
    ld ($C20C),a
    ld b,(ix+20)
    srl b
    rla
    ld ($C214),a
    ld bc,$F8F7
    call $13B2
    rlca
    jr c,$1173
    ld bc,$07F7
    call $13B5
    rlca
    jr c,$1198
    ld bc,$00F7
    call $13B2
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    ld a,$00
    ld ($C11E),a
    ld a,($C210)
    cp $31
    jr c,$1152
    dec (ix+16)
    ret
    ld hl,$FFFF
    ld ($C112),hl
    call $2935
    ret nc
    ld a,($C210)
    cp $11
    jr c,$1167
    dec (ix+16)
    ret
    ld a,($C11D)
    and $01
    ret z
    ld a,$0E
    ld ($C01F),a
    ret
    ld bc,$07F7
    call $13B5
    rlca
    jr nc,$1188
    ld bc,$FFF7
    call $13B2
    bit 6,a
    jp nz,$1036
    ret
    ld bc,$FFF7
    call $13B2
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    jp $10CF
    ld bc,$00F7
    call $13B2
    bit 6,a
    jp nz,$1036
    rlca
    ret c
    jp $10EF
    bit 2,c
    jp nz,$1249
    bit 0,c
    jp nz,$1111
    bit 1,c
    jp nz,$104B
    ld (ix+13),$05
    ld a,$03
    ld ($C20C),a
    ld b,(ix+20)
    srl b
    rla
    ld ($C214),a
    ld bc,$08F8
    call $13B2
    rlca
    jr c,$120C
    ld bc,$08FF
    call $13B5
    rlca
    jr c,$1227
    ld a,$03
    ld ($C11E),a
    ld a,($C211)
    cp $C8
    jr nc,$11EB
    inc (ix+17)
    ret
    ld hl,$0001
    ld ($C110),hl
    call $2993
    ret nc
    ld a,($C211)
    cp $F8
    jr nc,$1200
    inc (ix+17)
    ret
    ld a,($C11D)
    and $08
    ret z
    ld a,$0E
    ld ($C01F),a
    ret
    ld bc,$08FF
    call $13B5
    rlca
    ret c
    ld bc,$0700
    call $13B5
    rlca
    ret c
    ld bc,$F800
    call $13B5
    rlca
    ret c
    jp $107C
    ld bc,$07F7
    call $13B5
    rlca
    ret c
    ld bc,$F8F7
    call $13B5
    rlca
    ret c
    jp $1142
    bit 3,c
    jp nz,$11B7
    bit 0,c
    jp nz,$1111
    bit 1,c
    jp nz,$104B
    ld (ix+13),$04
    ld a,$02
    ld ($C20C),a
    ld b,(ix+20)
    srl b
    rla
    ld ($C214),a
    ld bc,$F7F8
    call $13B2
    rlca
    jr c,$129E
    ld bc,$F7FF
    call $13B5
    rlca
    jr c,$1227
    ld a,$02
    ld ($C11E),a
    ld a,($C211)
    cp $41
    jr c,$127D
    dec (ix+17)
    ret
    ld hl,$FFFF
    ld ($C110),hl
    call $2A20
    ret nc
    ld a,($C211)
    cp $11
    jr c,$1292
    dec (ix+17)
    ret
    ld a,($C11D)
    and $04
    ret z
    ld a,$0E
    ld ($C01F),a
    ret
    ld bc,$F7FF
    call $13B5
    rlca
    ret c
    jp $1214
    ld a,($C219)
    ld ($C11E),a
    ld hl,$12C0
    rst $0008
    dec (ix+15)
    ret nz
    res 2,(ix+1)
    ld (ix+0),$01
    ret
    ret z
    ld (de),a
    ld a,(bc)
    inc de
    ld c,h
    inc de
    ld a,a
    inc de
    ld bc,$00F6
    call $13B2
    rlca
    ret c
    ld bc,$F8F6
    call $13B2
    rlca
    ret c
    ld bc,$07F6
    call $13B5
    rlca
    ret c
    ld a,($C210)
    cp $32
    jr c,$12ED
    sub $02
    ld ($C210),a
    ret
    ld hl,$FFFE
    ld a,($C184)
    rrca
    jr nc,$12F7
    inc l
    ld ($C112),hl
    call $2935
    ret nc
    ld a,($C210)
    cp $12
    ret c
    sub $02
    ld ($C210),a
    ret
    ld bc,$0001
    call $13B2
    rlca
    ret c
    ld bc,$F801
    call $13B2
    rlca
    ret c
    ld bc,$0701
    call $13B5
    rlca
    ret c
    ld a,($C210)
    cp $7F
    jr nc,$132F
    add a,$02
    ld ($C210),a
    ret
    ld hl,$0002
    ld a,($C184)
    rrca
    jr nc,$1339
    dec l
    ld ($C112),hl
    call $28CE
    ret nc
    ld a,($C210)
    cp $9F
    ret nc
    add a,$02
    ld ($C210),a
    ret
    ld bc,$F6F8
    call $13B2
    rlca
    ret c
    ld bc,$F6FF
    call $13B5
    rlca
    ret c
    ld a,($C211)
    cp $42
    jr c,$1369
    sub $02
    ld ($C211),a
    ret
    ld hl,$FFFE
    ld ($C110),hl
    call $2A20
    ret nc
    ld a,($C211)
    cp $12
    ret c
    sub $02
    ld ($C211),a
    ret
    ld bc,$09F8
    call $13B2
    rlca
    ret c
    ld bc,$09FF
    call $13B5
    rlca
    ret c
    ld a,($C211)
    cp $C7
    jr nc,$139C
    add a,$02
    ld ($C211),a
    ret
    ld hl,$0002
    ld ($C110),hl
    call $2993
    ret nc
    ld a,($C211)
    cp $F7
    ret nc
    add a,$02
    ld ($C211),a
    ret
    ld de,$D601
    ld a,($C210)
    add a,c
    ld c,a
    ld a,($C019)
    add a,c
    jr c,$13C4
    cp $E0
    jr c,$13C6
    add a,$20
    and $F8
    ld l,a
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,de
    ld a,($C182)
    add a,(ix+17)
    add a,b
    and $F8
    rrca
    rrca
    ld c,a
    ld b,$00
    add hl,bc
    ld a,(hl)
    ret
    dec (ix+22)
    jp p,$13FA
    ld a,$34
    sub (ix+33)
    rrca
    rrca
    and $0F
    ld (ix+22),a
    ld a,(ix+12)
    xor $80
    ld (ix+12),a
    ld a,(ix+12)
    rlca
    ld (ix+20),a
    ret
    ld (ix+10),$00
    ld (ix+11),$00
    ld (ix+8),$00
    ld (ix+9),$00
    ld a,(ix+12)
    add a,a
    add a,a
    add a,a
    add a,a
    ld b,a
    ld a,r
    and $0F
    add a,b
    ld hl,$15D6
    add a,l
    ld l,a
    jr nc,$1427
    inc h
    ld a,(hl)
    ld hl,$142E
    jp $0008
    sbc a,c
    inc d
    exx
    inc d
    inc bc
    dec d
    inc a
    dec d
    ld (ix+10),$00
    ld (ix+11),$00
    ld (ix+8),$00
    ld (ix+9),$00
    ld a,($C198)
    or a
    jr z,$1455
    ld a,($C11B)
    and $0F
    cp (ix+47)
    ret nz
    ld a,r
    and $07
    jr z,$1412
    bit 0,(ix+1)
    jr nz,$1412
    ld a,($C210)
    sub (ix+16)
    jp p,$146C
    neg
    ld b,a
    ld a,($C211)
    sub (ix+17)
    jp p,$1478
    neg
    ld c,a
    cp b
    jr c,$148D
    ld a,b
    cp $08
    jr nc,$1412
    ld a,($C211)
    cp (ix+17)
    jp c,$1503
    jp $153C
    cp $08
    jr nc,$1412
    ld a,($C210)
    cp (ix+16)
    jr nc,$14D9
    ld (ix+13),$06
    ld a,(ix+12)
    and $80
    or $00
    ld (ix+12),a
    ld bc,$FAF6
    call $4A5D
    ret nz
    ld bc,$05F6
    call $4A5D
    ret nz
    res 5,(ix+1)
    ld hl,$0000
    ld d,h
    ld e,(ix+33)
    sbc hl,de
    add hl,hl
    add hl,hl
    add hl,hl
    bit 7,(ix+32)
    jr z,$14D1
    ld a,($C1BF)
    rlca
    jr c,$14D2
    add hl,hl
    ld (ix+8),ixl
    ld (ix+9),ixh
    ret
    ld (ix+13),$07
    ld a,(ix+12)
    and $80
    or $01
    ld (ix+12),a
    ld bc,$FA01
    call $4A5D
    ret nz
    ld bc,$0501
    call $4A5D
    ret nz
    res 5,(ix+1)
    ld h,$00
    ld ixl,(ix+33)
    add hl,hl
    add hl,hl
    add hl,hl
    jr $14C5
    ld (ix+13),$08
    ld a,(ix+12)
    and $80
    or $02
    ld (ix+12),a
    ld bc,$F6FC
    call $4A5D
    ret nz
    res 5,(ix+1)
    ld hl,$0000
    ld d,h
    ld e,(ix+33)
    sbc hl,de
    add hl,hl
    add hl,hl
    add hl,hl
    bit 7,(ix+32)
    jr z,$1534
    ld a,($C1BF)
    rlca
    jr c,$1535
    add hl,hl
    ld (ix+10),ixl
    ld (ix+11),ixh
    ret
    ld (ix+13),$09
    ld a,(ix+12)
    and $80
    or $03
    ld (ix+12),a
    ld bc,$09FC
    call $4A5D
    ret nz
    res 5,(ix+1)
    ld h,$00
    ld ixl,(ix+33)
    add hl,hl
    add hl,hl
    add hl,hl
    jr $1528
    ld a,(ix+25)
    ld hl,$1568
    jp $0008
    ld (hl),b
    dec d
    adc a,l
    dec d
    xor d
    dec d
    ret nz
    dec d
    ld bc,$FAF6
    call $4A5D
    ret nz
    ld bc,$05F6
    call $4A5D
    ret nz
    ld ixl,(ix+3)
    ld ixh,(ix+4)
    dec hl
    dec hl
    ld (ix+3),ixl
    ld (ix+4),ixh
    ret
    ld bc,$FA01
    call $4A5D
    ret nz
    ld bc,$0501
    call $4A5D
    ret nz
    ld ixl,(ix+3)
    ld ixh,(ix+4)
    inc hl
    inc hl
    ld (ix+3),ixl
    ld (ix+4),ixh
    ret
    ld bc,$F6FC
    call $4A5D
    ret nz
    ld ixl,(ix+6)
    ld ixh,(ix+7)
    dec hl
    dec hl
    ld (ix+6),ixl
    ld (ix+7),ixh
    ret
    ld bc,$09FC
    call $4A5D
    ret nz
    ld ixl,(ix+6)
    ld ixh,(ix+7)
    inc hl
    inc hl
    ld (ix+6),ixl
    ld (ix+7),ixh
    ret
    nop
    nop
    nop
    nop
    ld bc,$0000
    nop
    ld (bc),a
    nop
    nop
    nop
    inc bc
    nop
    nop
    nop
    nop
    ld bc,$0101
    ld bc,$0101
    ld bc,$0102
    ld bc,$0301
    ld bc,$0101
    nop
    ld (bc),a
    ld (bc),a
    ld (bc),a
    ld bc,$0202
    ld (bc),a
    ld (bc),a
    ld (bc),a
    ld (bc),a
    ld (bc),a
    inc bc
    ld (bc),a
    ld (bc),a
    ld (bc),a
    nop
    inc bc
    inc bc
    inc bc
    ld bc,$0303
    inc bc
    ld (bc),a
    inc bc
    inc bc
    inc bc
    inc bc
    inc bc
    inc bc
    inc bc
    ret
    ld (ix+23),$40
    ld (ix+24),$B9
    bit 6,(ix+1)
    ret z
    jr $1673
    ld (ix+23),$48
    ld (ix+24),$B9
    bit 6,(ix+1)
    ret
    call $1626
    ret z
    ld a,($C1D4)
    cp $01
    jr c,$1673
    jr nz,$1648
    inc a
    ld ($C1D4),a
    ld a,$1B
    jr $164A
    ld a,$1C
    ld ($C118),a
    ld a,$90
    ld ($C02D),a
    ld ($DE64),a
    jr $1679
    inc (ix+0)
    ld (ix+23),$D9
    ld (ix+24),$BA
    ret
    bit 6,(ix+1)
    jr nz,$1673
    bit 5,(ix+1)
    call nz,$1402
    jp $13E0
    ld a,(ix+32)
    ld ($C118),a
    res 6,(ix+1)
    ld a,$08
    ld ($C01F),a
    ret
    ld (ix+23),$39
    ld (ix+24),$BB
    ld (ix+0),$04
    ret
    ld (ix+23),$F9
    ld (ix+24),$BA
    jr $168B
    ld (ix+23),$19
    ld (ix+24),$BB
    jr $168B
    ld (ix+23),$B9
    ld (ix+24),$BB
    jr $168B
    ld (ix+23),$D9
    ld (ix+24),$BB
    jr $168B
    ld a,($C1DA)
    or a
    jp nz,$194B
    ld (ix+23),$44
    ld (ix+24),$B9
    inc (ix+0)
    bit 6,(ix+1)
    ret z
    ld a,($C1DA)
    or a
    jp nz,$1673
    ld a,$01
    ld ($C1DA),a
    ld a,$1D
    ld ($C118),a
    push ix
    call $4459
    pop ix
    jp $1673
    ld a,($C1DB)
    and $40
    jp nz,$194B
    ld hl,$BA5B
    ld ($C247),hl
    ld (ix+18),$05
    bit 6,(ix+1)
    ret z
    res 6,(ix+1)
    ld a,$34
    ld ($C118),a
    push ix
    call $4459
    call $267B
    pop ix
    ld a,$07
    ld ($C120),a
    ld a,$10
    jp $167F
    ld a,($C1D5)
    cp $02
    jp nc,$194B
    inc (ix+0)
    ld hl,$B938
    ld ($C247),hl
    ret
    bit 6,(ix+1)
    ret z
    ld a,($C1D5)
    cp $01
    jp c,$1673
    jr z,$1744
    ld a,$2F
    jp $1676
    ld ($C1BA),a
    inc a
    ld ($C1D5),a
    push ix
    ld a,$24
    call $1676
    call $4459
    ld hl,$90E4
    call $4D8D
    ld hl,$B866
    ld de,$1307
    ld a,$03
    call $4CFD
    pop ix
    ret
    ld a,($C1DE)
    or a
    jp nz,$194B
    call $1729
    bit 6,(ix+1)
    ret z
    push ix
    call $1673
    call $4459
    call $6215
    pop ix
    ret
    call $1729
    bit 6,(ix+1)
    ret z
    ld a,($C1D1)
    or a
    jr nz,$173F
    push ix
    call $1673
    call $4459
    ld a,$29
    call $1676
    call $4459
    pop ix
    ret
    ld a,($C1E0)
    or a
    jp nz,$194B
    inc (ix+0)
    call $1626
    ret z
    ld a,($C1D1)
    or a
    jp nz,$1673
    push ix
    ld a,$2A
    call $1676
    call $4459
    ld a,$2B
    call $1676
    call $4459
    ld hl,$A209
    call $4D8D
    ld hl,$B884
    ld de,$1207
    ld a,$03
    call $4CFD
    ld a,$32
    call $1676
    call $4459
    pop ix
    ld a,$01
    ld ($C1D1),a
    ld ($C1E0),a
    jp $1673
    ld a,($C1E1)
    or a
    jp nz,$194B
    inc (ix+0)
    ld (ix+23),$3C
    ld (ix+24),$B9
    ret
    bit 6,(ix+1)
    ret z
    ld a,($C1E1)
    or a
    jp z,$1673
    ld a,$33
    jp $1676
    call $17FE
    bit 6,(ix+1)
    ret z
    ld a,($C1D0)
    or a
    jp nz,$1673
    ld a,($C1D1)
    or a
    jr z,$1833
    ld a,($C1C6)
    or a
    jr nz,$1838
    ld a,$31
    jp $1676
    push ix
    ld a,$2C
    call $1676
    call $4459
    ld a,$2D
    call $1676
    call $4459
    ld hl,$A11D
    call $4D8D
    ld hl,$B89C
    ld de,$1207
    ld a,$03
    call $4CFD
    ld a,$01
    ld ($C1D0),a
    pop ix
    ret
    ld (ix+13),$00
    ld (ix+14),$00
    ld (ix+18),$00
    ld a,($C70B)
    cp $2B
    jp nz,$194B
    inc (ix+0)
    ld a,($C70B)
    cp $2B
    ret z
    ld (ix+13),$0A
    ld (ix+14),$0A
    ld (ix+18),$01
    ld (ix+23),$40
    ld (ix+24),$B9
    inc (ix+0)
    bit 6,(ix+1)
    ret z
    bit 7,(ix+0)
    jp nz,$173F
    ld a,($C1E1)
    or a
    jp nz,$1673
    inc a
    ld ($C1E1),a
    ld ($C1D5),a
    set 7,(ix+0)
    push ix
    ld a,$20
    call $1676
    call $4459
    ld a,$21
    call $1676
    call $4459
    ld hl,$A53C
    call $4D8D
    ld hl,$B8B4
    ld de,$1207
    ld a,$03
    call $4CFD
    pop ix
    ret
    bit 2,(ix+1)
    jr nz,$1904
    bit 5,(ix+1)
    call nz,$1402
    jp $13E0
    ld a,($D0C9)
    cp $87
    jr nz,$18F7
    ld (ix+0),$09
    ret
    ld (ix+13),$07
    ld (ix+20),$02
    bit 2,(ix+1)
    ret z
    ld (ix+0),$09
    jp $155F
    ld (ix+11),$00
    ld (ix+10),$00
    ld (ix+9),$00
    ld (ix+8),$00
    set 5,(ix+1)
    ret
    bit 0,(ix+1)
    jr nz,$190B
    bit 2,(ix+1)
    jp nz,$155F
    bit 5,(ix+1)
    call nz,$1436
    jp $13E0
    ld a,(ix+15)
    or a
    jr z,$194B
    and $04
    jr nz,$1946
    res 1,(ix+1)
    ret
    set 1,(ix+1)
    ret
    ld (ix+0),$00
    ret
    xor a
    ld ($C242),a
    ld ($C23E),a
    ld a,($C91C)
    cp $4B
    ret nz
    ld (ix+0),$08
    ld (ix+12),$01
    ld (ix+18),$01
    ld (ix+14),$01
    ret
    ld (ix+18),$00
    ld (ix+14),$00
    ld a,(ix-30)
    or a
    ret z
    inc (ix+0)
    ld (ix+22),$40
    dec (ix+22)
    ret nz
    jr $195D
; actor_handler_dispatch_34: pointer_words, $1988-$19CB
    dw $1616, $1617, $1633, $1657, $1663, $1683, $1690, $169A
    dw $18DB, $1926, $1937, $16A4, $16AE, $16B8, $16CA, $18F7
    dw $16EA, $1920, $171E, $1730, $1769, $1786, $17A7, $17B1
    dw $17F4, $1807, $1818, $1863, $187A, $1897, $1950, $196E
    dw $1982, $18EB
    ld ix,$C230
    ld b,$10
    push bc
    ld a,(ix+0)
    or a
    jp z,$1ACC
    ld hl,$1988
    rst $0008
    ld bc,$0000
    bit 2,(ix+1)
    jp nz,$1AD7
    ld a,($C1E3)
    or a
    jr z,$19F6
    ld e,(ix+6)
    ld d,(ix+7)
    jr $1A3B
    ld ixl,(ix+5)
    ld ixh,(ix+6)
    ld a,(ix+7)
    ld e,(ix+10)
    ld d,(ix+11)
    add hl,de
    bit 7,d
    jr nz,$1A0E
    adc a,b
    jp $1A10
    ccf
    sbc a,b
    ld (ix+5),ixl
    ld (ix+6),ixh
    ld (ix+7),a
    ex de,hl
    add hl,de
    ld e,d
    ld d,a
    ld a,e
    xor h
    and $08
    jr z,$1A3B
    set 5,(ix+1)
    ld a,$04
    add a,e
    ld e,a
    jr nc,$1A2E
    inc d
    and $F8
    ld e,a
    ld (ix+7),d
    ld (ix+6),e
    ld (ix+5),$00
    ld hl,($C182)
    ex de,hl
    sbc hl,de
    ld a,h
    or a
    jr nz,$1A46
    inc c
    ld a,l
    cp $F8
    jr nc,$1A4C
    inc c
    add a,$08
    ld (ix+17),a
    ld a,($C1E3)
    or a
    jr z,$1A5F
    ld e,(ix+3)
    ld d,(ix+4)
    jr $1AA4
    ld ixl,(ix+2)
    ld ixh,(ix+3)
    ld a,(ix+4)
    ld e,(ix+8)
    ld d,(ix+9)
    add hl,de
    bit 7,d
    jr nz,$1A77
    adc a,b
    jp $1A79
    ccf
    sbc a,b
    ld (ix+2),ixl
    ld (ix+3),ixh
    ld (ix+4),a
    ex de,hl
    add hl,de
    ld e,d
    ld d,a
    ld a,e
    xor h
    and $08
    jr z,$1AA4
    set 5,(ix+1)
    ld a,$04
    add a,e
    ld e,a
    jr nc,$1A97
    inc d
    and $F8
    ld e,a
    ld (ix+4),d
    ld (ix+3),e
    ld (ix+2),$00
    ld hl,($C184)
    ex de,hl
    sbc hl,de
    ld a,h
    or a
    jr nz,$1AAF
    inc c
    ld a,l
    cp $B0
    jr nc,$1AB5
    inc c
    ld a,c
    cp $04
    jr nz,$1AC4
    ld (ix+16),ixl
    res 0,(ix+1)
    jp $1ACC
    set 0,(ix+1)
    ld (ix+16),$FF
    pop bc
    ld de,$0030
    add ix,de
    dec b
    jp nz,$19D2
    ret
    dec (ix+15)
    jr nz,$1AE4
    res 2,(ix+1)
    set 5,(ix+1)
    ld ixl,(ix+6)
    ld ixh,(ix+7)
    ld de,($C182)
    or a
    sbc hl,de
    ld a,h
    or a
    jr nz,$1AC4
    ld a,l
    cp $F8
    jr nc,$1AC4
    add a,$08
    ld (ix+17),a
    ld ixl,(ix+3)
    ld ixh,(ix+4)
    ld de,($C184)
    or a
    sbc hl,de
    ld a,h
    or a
    jr nz,$1AC4
    ld a,l
    cp $B0
    jr nc,$1AC4
    ld (ix+16),a
    res 0,(ix+1)
    jp $1ACC
    ld hl,$C230
    ld de,$C231
    ld bc,$02FF
    ld (hl),$00
    call $0B19
    ld hl,$C25F
    ld de,$0030
    ld b,$10
    ld a,$10
    sub b
    ld (hl),a
    add hl,de
    djnz $1B35
    ld a,$07
    ld ($FFFF),a
    ld a,($C181)
    and $7F
    cp $16
    jr nc,$1B9A
    ld hl,$BA3B
    rst $0018
    ld ix,$C230
    ld a,(hl)
    or a
    jr z,$1B9A
    ld (ix+0),a
    ld (ix+41),a
    inc hl
    ld a,(hl)
    ld (ix+32),a
    call $1B9B
    inc hl
    push hl
    ld l,(hl)
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld de,$0008
    add hl,de
    ld (ix+6),ixl
    ld (ix+7),ixh
    ld (ix+43),ixl
    ld (ix+44),ixh
    pop hl
    inc hl
    push hl
    ld l,(hl)
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld (ix+3),ixl
    ld (ix+4),ixh
    ld (ix+45),ixl
    ld (ix+46),ixh
    pop hl
    inc hl
    ld de,$0030
    add ix,de
    jr $1B52
    ret
    push de
    push hl
    add a,a
    jr c,$1BB6
    ld (ix+1),$20
    ld (ix+33),$04
    ld (ix+18),$01
    ld (ix+13),$0A
    ld (ix+14),$0A
    jr $1C02
    ld l,a
    ld h,$00
    ld e,l
    ld d,h
    add hl,hl
    add hl,hl
    add hl,de
    ld de,$1C05
    add hl,de
    ld a,(hl)
    ld (ix+33),a
    inc hl
    ld a,(hl)
    ld (ix+34),a
    ld (ix+42),a
    inc hl
    ld a,(hl)
    ld (ix+35),a
    inc hl
    ld a,(hl)
    ld (ix+36),a
    inc hl
    ld a,(hl)
    ld (ix+37),a
    inc hl
    ld a,(hl)
    ld (ix+38),a
    inc hl
    ld a,(hl)
    ld (ix+39),a
    inc hl
    ld a,(hl)
    ld (ix+40),a
    inc hl
    ld a,(hl)
    ld (ix+23),a
    inc hl
    ld a,(hl)
    ld (ix+24),a
    ld (ix+18),$01
    ld (ix+1),$20
    ld (ix+14),$01
    pop hl
    pop de
    ret
; unresolved_1C05: unresolved, $1C05-$1D62
    db $08, $0F, $13, $0B, $0A, $00, $01, $00, $59, $BB, $08, $1F, $10, $09, $06, $00
    db $02, $00, $79, $BB, $0A, $1F, $19, $0F, $0E, $00, $03, $00, $99, $BB, $08, $2F
    db $28, $14, $0E, $00, $04, $00, $F9, $BB, $0B, $2F, $58, $23, $32, $00, $28, $00
    db $19, $BC, $0A, $3F, $5C, $2D, $3C, $00, $32, $00, $39, $BC, $0B, $4F, $69, $46
    db $46, $00, $3C, $00, $59, $BC, $09, $5F, $7D, $50, $64, $00, $46, $00, $79, $BC
    db $0B, $6F, $82, $55, $78, $00, $50, $00, $99, $BC, $0C, $6F, $87, $5A, $8C, $00
    db $5A, $00, $B9, $BC, $0A, $AF, $A0, $50, $C8, $00, $C8, $00, $D9, $BC, $0E, $AF
    db $A5, $55, $F0, $00, $F0, $00, $F9, $BC, $10, $AF, $A5, $5A, $18, $01, $18, $01
    db $19, $BD, $0E, $BF, $AA, $5F, $C8, $00, $40, $01, $39, $BD, $10, $CF, $AF, $64
    db $F0, $00, $68, $01, $59, $BD, $12, $DF, $B4, $69, $18, $01, $90, $01, $79, $BD
    db $0E, $FF, $A0, $69, $C8, $00, $B8, $01, $99, $BD, $10, $EF, $AF, $69, $F0, $00
    db $E0, $01, $B9, $BD, $12, $FF, $B9, $6E, $18, $01, $03, $02, $D9, $BD, $10, $FF
    db $A0, $5A, $18, $01, $FE, $01, $F9, $BD, $10, $FF, $A5, $5F, $18, $01, $FE, $01
    db $19, $BE, $10, $FF, $B4, $6E, $18, $01, $FE, $01, $39, $BE, $10, $FF, $A5, $73
    db $18, $01, $FE, $01, $59, $BE, $10, $FF, $B4, $6E, $18, $01, $FE, $01, $79, $BE
    db $10, $FF, $BE, $91, $18, $01, $FE, $01, $99, $BE, $10, $FF, $C8, $87, $18, $01
    db $FE, $01, $B9, $BE, $10, $FF, $CD, $96, $18, $01, $FE, $01, $D9, $BE, $10, $FF
    db $CD, $9B, $18, $01, $FE, $01, $F9, $BE, $10, $FF, $D7, $9B, $18, $01, $FE, $01
    db $19, $BF, $10, $FF, $C8, $87, $18, $01, $FE, $01, $39, $BF, $10, $FF, $EB, $AA
    db $18, $01, $FE, $01, $59, $BF, $10, $FF, $B9, $73, $18, $01, $FE, $01, $79, $BF
    db $10, $FF, $BE, $8C, $18, $01, $FE, $01, $99, $BF, $10, $FF, $D7, $A5, $18, $01
    db $FE, $01, $B9, $BF, $10, $FF, $DB, $9B, $18, $01, $FE, $01, $D9, $BF
    ld a,($C1DF)
    or a
    jr z,$1D6D
    ld a,$0D
    jr $1D77
    ld a,($C181)
    cp $15
    jr z,$1D96
    call $42BA
    ld hl,$1DA2
    add a,l
    ld l,a
    jr nc,$1D7F
    inc h
    ld a,($C02D)
    cp (hl)
    ret z
    push hl
    ld a,$02
    ld ($FFFF),a
    call $8803
    pop hl
    ld a,(hl)
    ld ($DE64),a
    ld ($C02D),a
    ret
    ld a,($C1DB)
    and $40
    ld a,$0E
    jr z,$1D77
    inc a
    jr $1D77
; unresolved_1DA2: unresolved, $1DA2-$1DB1
    db $82, $84, $84, $84, $85, $86, $86, $86, $86, $87, $87, $87, $88, $8E, $93, $8A
    ld a,$03
    ld ($FFFF),a
    ld hl,$9128
    ld de,$5EC0
    call $0695
    ld hl,$914A
    ld de,$5400
    ld c,$3E
    call $0BA1
    ld hl,$952A
    ld de,$5CE0
    ld a,$03
    ld ($FFFF),a
    call $0695
    ld a,($C181)
    and $7F
    cp $0C
    jr nc,$1E07
    ld l,a
    ld h,$00
    add hl,hl
    add a,l
    ld l,a
    jr nc,$1DEB
    inc h
    ld de,$1E15
    add hl,de
    ld a,(hl)
    ld ($FFFF),a
    inc hl
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld de,$C160
    ld bc,$0010
    call $0B19
    ld de,$4000
    jp $0695
    cp $15
    jr z,$1E10
    ld hl,$1E39
    jr $1DEF
    ld hl,$1E3C
    jr $1DEF
; unresolved_1E15: unresolved, $1E15-$1E3E
    db $0B, $00, $80, $0B, $DA, $8B, $0C, $D9, $A4, $0C, $D9, $A4, $0A, $00, $80, $0A
    db $00, $80, $0A, $00, $80, $0A, $00, $80, $0A, $00, $80, $0A, $F0, $AE, $0A, $F0
    db $AE, $0A, $F0, $AE, $09, $F9, $92, $09, $9C, $A2
    ld hl,$18E7
    ld de,$6000
    ld bc,$0380
    call $06D4
    ld a,$04
    ld ($FFFF),a
    ld hl,$BF99
    ld de,$7700
    ld bc,$000B
    call $06C1
    ld de,$7780
    ld bc,$0014
    call $06C1
    ld a,$03
    ld ($FFFF),a
    ld hl,$9008
    ld de,$76E0
    ld bc,$0020
    call $06C1
    ld de,$7720
    ld bc,$0060
    call $06C1
    ld de,$77A0
    ld bc,$0060
    call $06C1
    ld de,$7F40
    ld bc,$0040
    call $06C1
    ld a,$04
    ld ($FFFF),a
    ld de,$6780
    ld c,$01
    ld a,($C181)
    and $7F
    cp $16
    ret nc
    ld hl,$1EA8
    rst $0008
    ret
; graphics_upload_dispatch_22: pointer_words, $1EA8-$1ED3
    dw $1ED4, $1EF4, $1EFA, $1EFA, $1F00, $1F01, $1F01, $1F0F
    dw $1F0F, $1F15, $1F1B, $1F20, $1F25, $1F33, $1F38, $1F46
    dw $1F57, $1F5C, $1F64, $1F69, $1F71, $1F7E
    ld hl,$8322
    ld de,$6780
    call $0695
    ld de,$71A0
    call $1F9A
    ld hl,$82A2
    ld de,$7660
    ld a,$04
    ld ($FFFF),a
    ld bc,$0080
    jp $06C1
    ld hl,$8CF8
    jp $1F91
    ld hl,$93AA
    jp $1F91
    ret
    ld hl,$9A3C
    call $1F91
    ld hl,$8222
    ld de,$75E0
    jr $1EE9
    ld hl,$A156
    jp $1F91
    ld hl,$A7F0
    jp $1F91
    ld hl,$AF18
    jr $1F91
    ld hl,$B610
    jr $1F91
    ld hl,$BD49
    call $1F91
    ld hl,$80A2
    ld de,$7460
    jr $1EE9
    ld hl,$9C18
    jr $1F8C
    ld hl,$A0A2
    call $1F8C
    ld hl,$81A2
    ld de,$7560
    jr $1EE9
    ld hl,$A0A2
    call $1F8C
    call $1F2B
    ld hl,$8122
    ld de,$74E0
    jr $1EE9
    ld hl,$A677
    jr $1F8C
    call $1EE3
    ld hl,$A909
    jr $1F8C
    ld hl,$B004
    jr $1F8C
    ld hl,$B4BA
    call $1F8C
    jr $1F2B
    ld hl,$B596
    ld a,$07
    call $1F8E
    call $1F4F
    jr $1F3E
    ld hl,$B9F5
    ld de,$6800
    ld a,$08
    ld ($FFFF),a
    jp $0695
    ld a,$06
    ld ($FFFF),a
    ld de,$6780
    call $0695
    ld de,$7100
    ld a,(hl)
    inc hl
    or a
    ret z
    push hl
    ld bc,$2000
    ld l,a
    ld h,c
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,bc
    ex de,hl
    rst $0028
    ex de,hl
    in a,($BE)
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rrca
    rl c
    rst $0028
    ex de,hl
    ld a,c
    out ($BE),a
    inc hl
    inc de
    djnz $1FAB
    ex de,hl
    pop hl
    jr $1F9A
    call $1FE3
    ld a,($C198)
    or a
    ret z
    ld hl,$0320
    ld ($C18A),hl
    ret
    ld a,($C181)
    ld hl,$2533
    rst $0018
    ld a,(hl)
    ld ($FFFF),a
    inc hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    push hl
    ex de,hl
    ld de,$C600
    call $0C20
    ld a,($FFFC)
    or $08
    ld ($FFFC),a
    ld hl,$C600
    ld de,$8400
    ld c,$02
    call $0BEF
    ld a,($FFFC)
    and $F7
    ld ($FFFC),a
    pop hl
    inc hl
    ld a,(hl)
    ld ($FFFF),a
    inc hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    push hl
    ex de,hl
    ld de,$C600
    ld c,$01
    call $0BEF
    pop hl
    ld a,(hl)
    ld ($C193),a
    inc hl
    ld a,(hl)
    ld ($C194),a
    inc hl
    ld a,(hl)
    and $0F
    ld ($C11D),a
    xor a
    bit 7,(hl)
    jr z,$2041
    inc a
    ld ($C198),a
    xor a
    bit 6,(hl)
    jr z,$204A
    inc a
    ld ($C19A),a
    ld a,$09
    ld ($FFFF),a
    ld a,($C181)
    ld hl,$205A
    rst $0008
    ret
    db $AC, $20, $AD, $20, $AC, $20, $AC, $20, $F3, $20, $70, $21, $B1, $21, $D0, $21
    db $DB, $21, $5B, $22, $99, $22, $B8, $22, $D9, $22, $1D, $23, $34, $23, $67, $23
    db $99, $23, $A4, $23, $E6, $23, $4D, $24, $66, $24, $96, $24, $9D, $24, $9D, $24
    db $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $97, $24
    db $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24, $9D, $24
    db $9D, $24
    ret
    ld a,($C1D7)
    or a
    ld l,$CD
    call nz,$20D8
    ld a,($C1A7)
    or a
    jr nz,$20C7
    ld a,($C1D3)
    or a
    jr z,$20C7
    and $80
    jr z,$20D1
    ret
    ld l,$13
    call $20D8
    ld l,$14
    call $20D8
    ld l,$CE
    call $20D8
    ld l,$CF
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld de,$8401
    add hl,de
    ld a,$08
    ld ($FFFC),a
    ld b,$04
    res 6,(hl)
    inc hl
    inc hl
    djnz $20E8
    xor a
    ld ($FFFC),a
    ret
    ld hl,$C978
    ld a,($C1C8)
    and $80
    call nz,$2155
    ld hl,$CA41
    ld a,($C1D8)
    or a
    call nz,$214B
    ld hl,$CA2B
    ld a,($C1BE)
    or a
    call nz,$214B
    ld a,($C1CE)
    or a
    jr nz,$2126
    ld hl,$C71C
    ld de,$FFC0
    ld bc,$043C
    ld (hl),c
    dec c
    add hl,de
    djnz $2121
    ld a,($C1DB)
    rrca
    jr nc,$214A
    ld hl,$C6F4
    ld de,$C6F5
    ld bc,$0008
    ld (hl),$2B
    call $0B19
    ld hl,$C6B8
    ld (hl),$51
    inc hl
    ld (hl),$52
    ld hl,$C6F8
    ld (hl),$53
    inc hl
    ld (hl),$54
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$48
    add hl,de
    ld (hl),$1F
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$06
    inc hl
    ld (hl),$08
    dec hl
    add hl,de
    ld (hl),$05
    inc hl
    ld (hl),$07
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$04
    add hl,de
    ld (hl),$04
    ret
    ld hl,$D021
    ld a,($C1DC)
    and $01
    call nz,$214B
    ld hl,$CEC1
    ld a,($C1B9)
    or a
    call nz,$214B
    ld hl,$C787
    ld a,($C1D2)
    or a
    call nz,$214B
    ld hl,$C947
    ld a,($C1CA)
    and $02
    call nz,$2166
    ld hl,$C955
    ld a,($C1CA)
    and $04
    call nz,$2166
    ld hl,$C962
    ld a,($C1CA)
    and $08
    call nz,$2166
    ret
    ld hl,$CB3C
    ld a,($C1D9)
    or a
    call nz,$214B
    ld hl,$C7A9
    ld a,($C1CA)
    or a
    call nz,$214B
    ld hl,$CE8A
    ld a,($C1C9)
    or a
    call nz,$214B
    ret
    ld hl,$D177
    ld a,($C1CB)
    or a
    call nz,$214B
    ret
    ld hl,$D253
    ld a,($C1AD)
    or a
    call nz,$214B
    ld hl,$CCBC
    ld a,($C1CC)
    or a
    call nz,$214B
    ld a,($C1CB)
    or a
    call z,$2238
    ld hl,$C94A
    ld a,($C1CC)
    and $80
    call nz,$2155
    ld hl,$D131
    ld a,($C1B9)
    and $80
    call nz,$2246
    ld hl,$C782
    ld a,($C1C2)
    or a
    call nz,$214B
    ld a,($C1DB)
    and $02
    ret z
    ld hl,$C686
    ld de,$C687
    ld bc,$0005
    ld (hl),$00
    call $0B19
    ld hl,$C646
    ld de,$C647
    ld bc,$0005
    ld (hl),$00
    call $0B19
    ld hl,$C6C4
    ld de,$C6C5
    ld bc,$0008
    ld (hl),$2B
    jp $0B19
    call $2155
    dec hl
    ld de,$FFC0
    add hl,de
    ld (hl),$15
    inc hl
    ld (hl),$16
    dec hl
    add hl,de
    ld (hl),$17
    inc hl
    ld (hl),$18
    ret
    ld hl,$C74E
    ld a,($C1DC)
    and $02
    call nz,$2285
    ld hl,$C784
    ld a,($C1B3)
    or a
    call nz,$2285
    ld hl,$D004
    ld a,($C1BF)
    or a
    jp nz,$2285
    ld a,($C1CD)
    and $40
    ret z
    xor a
    ld ($C198),a
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$39
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$1B
    add hl,de
    ld (hl),$1A
    add hl,de
    ld (hl),$7E
    ret
    ld hl,$C7A8
    ld a,($C1D3)
    or a
    call nz,$2285
    ld hl,$C78C
    ld a,($C1D4)
    or a
    call nz,$2285
    ld hl,$D02B
    ld a,($C1C0)
    or a
    jp nz,$2285
    ret
    ld hl,$CC04
    ld a,($C1DC)
    and $04
    call nz,$2285
    ld hl,$C7AF
    ld a,($C1CD)
    or a
    call nz,$2285
    ld hl,$D187
    ld a,($C1CD)
    and $80
    jp nz,$228C
    ret
    ld hl,$C745
    ld a,($C1BF)
    or a
    call nz,$251F
    ld hl,$C74A
    ld a,($C1C8)
    and $40
    call nz,$251F
    ld hl,$C803
    ld a,($C1DC)
    and $08
    call nz,$2529
    ld hl,$C80C
    ld a,($C1C1)
    or a
    call nz,$2529
    ld hl,$D2B4
    ld a,($C1CD)
    and $08
    jr z,$2310
    call $2421
    ld hl,$C728
    ld a,($C1B9)
    and $80
    ret z
    call $2155
    ret
    ld hl,$D291
    ld a,($C1B9)
    and $80
    call nz,$2155
    ld hl,$D44F
    ld a,($C1CB)
    and $20
    call nz,$2155
    ret
    ld hl,$C766
    ld a,($C1A7)
    or a
    call nz,$251F
    ld a,($C1CA)
    and $40
    ld l,$88
    call nz,$20D8
    ld hl,$CB87
    ld a,($C1CF)
    or a
    call nz,$2529
    ld hl,$CB82
    ld a,($C1C6)
    or a
    call nz,$2529
    ld hl,$D109
    ld a,($C1AD)
    or a
    call nz,$2529
    ret
    ld hl,$C941
    ld a,($C1CB)
    and $80
    call nz,$2155
    ld hl,$C707
    ld a,($C1CB)
    and $40
    call nz,$2155
    ld hl,$CC3D
    ld a,($C1CD)
    and $04
    call nz,$2155
    ld hl,$CC3D
    ld a,($C1CD)
    and $02
    ret z
    call $2432
    ld l,$88
    jp $20D8
    ld hl,$CDD5
    ld a,($C1AE)
    or a
    call nz,$251F
    ret
    ld hl,$C977
    ld a,($C1CB)
    and $10
    call nz,$2155
    ld hl,$C737
    ld a,($C1CB)
    and $08
    call nz,$2155
    ld hl,$D20D
    ld a,($C1DC)
    and $10
    call nz,$251F
    ld hl,$CEF7
    ld a,($C1B4)
    or a
    call nz,$251F
    ld hl,$C8C3
    ld a,($C1C1)
    and $80
    call z,$2443
    ld hl,$C8C3
    ld a,($C1C8)
    and $08
    call nz,$2155
    ret
    ld a,($C1DB)
    and $04
    ld hl,$D3A8
    call nz,$2155
    ld hl,$D4F1
    ld a,($C1C4)
    or a
    call nz,$2529
    ld hl,$C737
    ld a,($C1C8)
    and $04
    call nz,$2155
    ld hl,$D455
    ld a,($C1A8)
    or a
    call nz,$251F
    ld hl,$C95B
    ld a,($C1C8)
    and $10
    ret z
    call $2421
    ld l,$88
    jp $20D8
    ld de,$FFC0
    add hl,de
    ld (hl),$4A
    inc hl
    ld (hl),$4B
    dec hl
    add hl,de
    ld (hl),$49
    inc hl
    ld (hl),$4C
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$21
    inc hl
    ld (hl),$23
    dec hl
    add hl,de
    ld (hl),$20
    inc hl
    ld (hl),$22
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$92
    inc hl
    ld (hl),$93
    ret
    ld hl,$CF4F
    ld a,($C1B3)
    or a
    call nz,$2529
    ld a,($C1CF)
    or a
    ret nz
    ld l,$34
    call $20D8
    ld l,$36
    jp $20D8
    ld hl,$CA09
    ld a,($C1BB)
    or a
    call nz,$251F
    ld hl,$CA06
    ld a,($C1C5)
    or a
    call nz,$251F
    ld hl,$CE84
    ld a,($C1CB)
    and $04
    call nz,$2155
    ld hl,$C74A
    ld a,($C1CD)
    and $08
    ret z
    call $2421
    ld l,$88
    jp $20D8
    ret
    ld a,($C1DE)
    or a
    jr nz,$24A0
    jp $24AB
    ld hl,$C610
    ld de,$CE00
    call $250B
    jr $24B4
    ld hl,$C600
    ld de,$CE00
    call $250B
    ld hl,$C608
    ld de,$C618
    call $250B
    ld de,$CE18
    call $250B
    ld hl,$C600
    ld de,$C608
    call $250B
    ld de,$C610
    call $250B
    ld de,$C620
    call $250B
    ld de,$C628
    call $250B
    ld de,$C630
    call $250B
    ld de,$C638
    call $250B
    ld de,$CE20
    call $250B
    ld de,$CE08
    call $250B
    ld de,$CE10
    call $250B
    ld de,$CE28
    call $250B
    ld de,$CE30
    call $250B
    ld de,$CE38
    push hl
    ld a,$0A
    ld bc,$0008
    ldir
    ld bc,$0038
    add hl,bc
    ex de,hl
    add hl,bc
    ex de,hl
    dec a
    jr nz,$250E
    pop hl
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$87
    add hl,de
    ld (hl),$1F
    ret
    ld de,$FFC0
    add hl,de
    ld (hl),$87
    add hl,de
    ld (hl),$77
    ret
; nine_byte_resource_directory_41: pointer_words, $2533-$2584
    dw $2585, $258E, $2597, $25A0, $25A9, $25B2, $25BB, $25C4
    dw $25CD, $25D6, $25DF, $25E8, $25F1, $25FA, $2603, $260C
    dw $2615, $261E, $2627, $2630, $2639, $2642, $264B, $264B
    dw $264B, $264B, $264B, $264B, $264B, $264B, $264B, $264B
    dw $264B, $264B, $264B, $264B, $264B, $264B, $264B, $264B
    dw $264B
    db $0B, $F6, $99, $0B, $20, $A2, $01, $00, $00, $0B, $A7, $9C, $0B, $11, $A7, $01
    db $01, $08, $0D, $23, $BC, $0C, $77, $B3, $01, $00, $05, $0D, $23, $BC, $0B, $B3
    db $B0, $01, $00, $02, $0A, $E8, $8B, $0A, $CF, $8D, $01, $00, $02, $0A, $E8, $8B
    db $0A, $EA, $93, $00, $00, $00, $0A, $E8, $8B, $0A, $AF, $9B, $00, $00, $00, $0A
    db $E8, $8B, $0A, $09, $A1, $00, $00, $00, $0A, $E8, $8B, $0A, $EB, $A7, $00, $00
    db $00, $0A, $19, $B8, $0B, $92, $B3, $00, $00, $80, $0A, $19, $B8, $09, $00, $80
    db $00, $00, $80, $0A, $19, $B8, $09, $E4, $89, $00, $00, $80, $09, $3B, $9F, $08
    db $00, $80, $00, $00, $00, $09, $3B, $9F, $09, $33, $AA, $00, $00, $00, $09, $3B
    db $9F, $09, $BA, $B1, $00, $00, $00, $09, $3B, $9F, $08, $DB, $84, $00, $00, $00
    db $09, $3B, $9F, $08, $8F, $8B, $00, $00, $04, $09, $3B, $9F, $08, $9F, $90, $00
    db $00, $00, $09, $3B, $9F, $08, $3D, $97, $00, $00, $00, $09, $3B, $9F, $08, $B5
    db $9D, $00, $00, $00, $09, $3B, $9F, $08, $60, $A6, $00, $00, $00, $09, $3C, $A9
    db $09, $00, $BB, $00, $00, $00, $09, $3B, $9F, $09, $31, $BE, $02, $00, $40
    ld ($C182),hl
    ld ($C184),de
    ld ($C210),bc
    ret
    ld bc,$0000
    ld ($C186),bc
    ld ($C188),bc
    ld ($C18A),hl
    ld ($C18C),de
    ret
    ld ($C186),hl
    ld ($C188),de
    ret
    ld a,($C182)
    neg
    ld ($C018),a
    ld a,($C19A)
    or a
    jp nz,$2711
    ld hl,($C184)
    ld de,$FF20
    add hl,de
    jr c,$2690
    sbc hl,de
    ld a,l
    ld ($C019),a
    ld bc,$00A0
    ld a,$15
    push af
    push bc
    call $2A64
    push de
    call $2AC9
    pop de
    call $2739
    pop bc
    ld hl,$FFF8
    add hl,bc
    ld c,l
    ld b,h
    pop af
    dec a
    jr nz,$269E
    ld a,($C198)
    or a
    jr z,$270C
    ld a,($C011)
    and $40
    jr nz,$270C
    ld bc,($C210)
    ld a,($C184)
    add a,c
    and $07
    rlca
    rlca
    rlca
    ld e,a
    ld a,($C182)
    add a,b
    and $07
    or e
    or $80
    ld ($C199),a
    ld a,$07
    ld ($FFFF),a
    call $8856
    ld hl,$2775
    ld de,$7400
    ld bc,$0008
    ld a,$01
    call $0718
    ld a,$06
    ld ($FFFF),a
    ld hl,$DD40
    ld ($C02A),hl
    ld hl,$DD00
    ld ($C028),hl
    call $9932
    ld hl,($C028)
    ld (hl),$D0
    xor a
    ld ($C100),a
    ret
    ld hl,$0000
    ld ($C184),hl
    xor a
    ld ($C019),a
    ld bc,$00A0
    ld a,$15
    push af
    push bc
    call $2AA8
    call $2B16
    ld a,$02
    call $0042
    pop bc
    ld hl,$FFF8
    add hl,bc
    ld c,l
    ld b,h
    pop af
    dec a
    jr nz,$2720
    ret
    ld a,($C198)
    or a
    jr nz,$275A
    ld a,($C011)
    and $40
    jr z,$274B
    ld a,$02
    jp $0042
    ld a,e
    and $C0
    ld e,a
    ld hl,$A200
    add hl,de
    ex de,hl
    ld bc,$0040
    jp $06C1
    ld a,$FF
    ld ($C199),a
    ld a,$07
    ld ($FFFF),a
    call $86C1
    xor a
    ld ($C040),a
    ld a,$07
    ld ($C105),a
    ld a,$03
    jp $0042
; padding_2775: fill_ff, $2775-$277C
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    ld de,$1800
    ld hl,$C582
    ld b,$1F
    ld (hl),e
    inc hl
    ld (hl),d
    inc hl
    djnz $2785
    ld hl,$C5C2
    ld b,$1F
    ld (hl),e
    inc hl
    ld (hl),d
    inc hl
    djnz $2790
    ld a,($C22A)
    ld b,a
    ld a,($C222)
    ld hl,$C594
    call $61AE
    ld hl,$C5D4
    ld b,$10
    ld (hl),$FF
    inc hl
    inc hl
    djnz $27A8
    ld bc,$00A8
    call $27EA
    ld hl,$C582
    ld bc,$003E
    call $06C1
    ld bc,$00B0
    call $27EA
    ld hl,$C582
    ld bc,$003E
    call $06C1
    ld bc,$00B8
    call $27EA
    ld hl,$C5C2
    ld bc,$003E
    call $06C1
    ld bc,$00C0
    call $27EA
    ld hl,$C5C2
    ld bc,$003E
    jp $06C1
    call $2A64
    ld hl,$A200
    add hl,de
    ld a,l
    and $C0
    add a,$02
    ld l,a
    ex de,hl
    ret
    ld hl,$C100
    ld a,(hl)
    ld (hl),$00
    cp $01
    ret c
    jr z,$281E
    ld de,($C101)
    ld hl,$A200
    add hl,de
    ld c,$BF
    out (c),l
    out (c),h
    ex de,hl
    dec c
    ld a,($C198)
    or a
    jp nz,$2858
    jp $04BF
    ld a,($C198)
    or a
    ret nz
    ld de,($C101)
    ld hl,$A200
    add hl,de
    ex de,hl
    ld bc,$3FBE
    ld a,e
    out ($BF),a
    ld a,d
    out ($BF),a
    ld a,$40
    add a,e
    ld e,a
    jr nc,$283C
    inc d
    outi
    ld a,d
    cp $7F
    jr c,$2845
    ld d,$78
    outi
    ld a,$3E
    add a,l
    ld l,a
    jr nc,$284E
    inc h
    ld a,h
    cp $DD
    jr c,$2855
    ld h,$D6
    djnz $282F
    ret
    ld de,$18E7
    ld b,$20
    out (c),e
    out (c),d
    djnz $285D
    ret
    ld hl,$C103
    ld a,(hl)
    cp $01
    ret c
    ld (hl),$00
    jr z,$288C
    call $288C
    ld hl,($C580)
    ld de,$0040
    add hl,de
    ld a,h
    cp $7F
    jr c,$2880
    ld h,$78
    inc c
    out (c),l
    out (c),h
    ld hl,$C582
    dec c
    jp $04C3
    ld hl,$C580
    ld c,$BF
    outi
    outi
    dec c
    jp $04C3
    ld hl,$C104
    ld a,(hl)
    cp $01
    ret c
    ld (hl),$00
    jr z,$28C1
    call $28C1
    ld hl,($C5C0)
    ld de,$0040
    add hl,de
    ld a,h
    cp $7F
    jr c,$28B5
    ld h,$78
    inc c
    out (c),l
    out (c),h
    ld hl,$C5C2
    dec c
    jp $04C3
    ld hl,$C5C0
    ld c,$BF
    outi
    outi
    dec c
    jp $04C3
    ld bc,($C184)
    add hl,bc
    ex de,hl
    ld hl,($C18C)
    or a
    sbc hl,de
    jr c,$292D
    ex de,hl
    ld ($C184),hl
    ld de,$FF20
    add hl,de
    jp c,$28E3
    sbc hl,de
    ld a,($C019)
    ld h,a
    dec h
    ld a,l
    ld ($C019),a
    dec a
    xor h
    and $08
    ret z
    ld bc,$00A0
    call $2A64
    ld hl,$A280
    add hl,de
    ld a,h
    cp $7F
    jr c,$2909
    sub $07
    ld h,a
    ld a,l
    and $C0
    add a,$02
    ld l,a
    ld ($C580),hl
    ld bc,$0080
    add hl,bc
    ld a,h
    cp $7F
    jr c,$291D
    ld h,$78
    ld ($C5C0),hl
    call $2AC9
    ld a,$01
    ld ($C103),a
    ld ($C104),a
    or a
    ret
    ld hl,$0000
    ld ($C112),hl
    scf
    ret
    ld bc,($C184)
    add hl,bc
    ex de,hl
    ld hl,($C188)
    scf
    sbc hl,de
    jp p,$292D
    ex de,hl
    ld ($C184),hl
    ld de,$FF20
    add hl,de
    jp c,$294B
    sbc hl,de
    ld a,($C019)
    ld h,a
    ld a,l
    ld ($C019),a
    xor h
    and $08
    ret z
    ld bc,$0000
    call $2A64
    call $2AC9
    ld a,$01
    ld ($C103),a
    ld ($C104),a
    ld hl,$A740
    add hl,de
    ld a,h
    cp $7F
    jr c,$297A
    sub $07
    ld h,a
    ld a,l
    and $C0
    add a,$02
    ld l,a
    ld ($C580),hl
    ld de,$0080
    add hl,de
    ld a,h
    cp $7F
    jr c,$298E
    ld h,$78
    ld ($C5C0),hl
    or a
    ret
    ld bc,($C182)
    add hl,bc
    ld a,($C19A)
    or a
    jr nz,$29DA
    ex de,hl
    ld hl,($C18A)
    sbc hl,de
    jr c,$29D2
    ld ($C182),de
    ld a,e
    neg
    ld ($C018),a
    ld a,c
    dec a
    dec e
    xor e
    and $08
    ret z
    ld bc,$0000
    call $2A64
    ld a,e
    rlca
    rlca
    sub $08
    rrca
    rrca
    ld e,a
    ld bc,$000F
    and $02
    jr z,$29CD
    inc c
    add iy,bc
    jp $2B7D
    ld hl,$0000
    ld ($C110),hl
    scf
    ret
    ld ($C182),hl
    ld a,l
    neg
    ld ($C018),a
    ld a,c
    dec a
    dec l
    xor l
    and $08
    ret z
    ld bc,$0000
    call $2A64
    ld a,e
    rlca
    rlca
    sub $08
    rrca
    rrca
    ld e,a
    ld bc,$000F
    and $02
    jr z,$2A00
    inc c
    add iy,bc
    push iy
    pop hl
    or a
    ld bc,$C600
    sbc hl,bc
    ld a,l
    and $3F
    bit 6,l
    ld l,a
    jr z,$2A17
    ld h,$08
    jr $2A19
    ld h,$00
    add hl,bc
    push hl
    pop iy
    jp $2B7D
    ld bc,($C182)
    add hl,bc
    ld a,($C19A)
    or a
    jr nz,$2A4D
    ex de,hl
    ld hl,($C186)
    scf
    sbc hl,de
    jp p,$29D2
    ex de,hl
    ld ($C182),hl
    ld a,l
    neg
    ld ($C018),a
    ld a,c
    xor l
    and $08
    ret z
    ld bc,$0000
    call $2A64
    jp $2B7D
    ld ($C182),hl
    ld a,l
    neg
    ld ($C018),a
    ld a,c
    xor l
    and $08
    ret z
    ld bc,$0000
    call $2A64
    jp $2A02
    ld hl,($C184)
    add hl,bc
    ld c,l
    ld b,h
    ld a,l
    and $F0
    ld l,a
    add hl,hl
    add hl,hl
    ld de,$C600
    add hl,de
    ex de,hl
    ld hl,($C182)
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld l,h
    ld h,$00
    add hl,de
    push hl
    pop iy
    ld l,c
    ld h,b
    ld de,$FF20
    add hl,de
    jp c,$2A88
    sbc hl,de
    ld a,l
    and $F8
    ld l,a
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld de,$D600
    add hl,de
    ld a,($C182)
    add a,$08
    and $F8
    rrca
    rrca
    add a,l
    ld l,a
    ex de,hl
    ret
    ld l,c
    ld h,b
    ld a,l
    and $F0
    ld l,a
    add hl,hl
    add hl,hl
    ex de,hl
    ld hl,($C182)
    ld a,h
    and $03
    bit 2,h
    ld h,a
    jr z,$2AC0
    ld a,d
    xor $08
    ld d,a
    push hl
    ld hl,$C600
    add hl,de
    ex de,hl
    pop hl
    jr $2A78
    ld a,$08
    ld ($FFFC),a
    ld a,$02
    ld ($C100),a
    ld a,e
    and $C0
    ld l,a
    ld h,d
    ld ($C101),hl
    ld b,$20
    push bc
    ld iyl,(iy+0)
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld bc,$8400
    add hl,bc
    xor a
    bit 1,e
    jr nz,$2AF1
    add a,$02
    bit 6,e
    jr z,$2AF7
    add a,$04
    add a,l
    ld l,a
    jr nc,$2AFC
    inc h
    ldi
    ldd
    ld a,e
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld e,a
    and $02
    jr z,$2B0E
    inc iy
    pop bc
    djnz $2ADD
    xor a
    ld ($FFFC),a
    ret
    ld a,$08
    ld ($FFFC),a
    ld a,$02
    ld ($C100),a
    ld a,e
    and $C0
    ld l,a
    ld h,d
    ld ($C101),hl
    ld b,$20
    push bc
    ld iyl,(iy+0)
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld bc,$8400
    add hl,bc
    xor a
    bit 1,e
    jr nz,$2B3E
    add a,$02
    bit 6,e
    jr z,$2B44
    add a,$04
    add a,l
    ld l,a
    jr nc,$2B49
    inc h
    ldi
    ldd
    ld a,e
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld e,a
    and $02
    call nz,$2B62
    pop bc
    djnz $2B2A
    xor a
    ld ($FFFC),a
    ret
    push iy
    pop hl
    ld bc,$3A00
    add hl,bc
    ld a,l
    inc hl
    xor l
    and $40
    jr z,$2B77
    ld a,h
    xor $08
    ld h,a
    ld bc,$3A40
    sbc hl,bc
    push hl
    pop iy
    ret
    ld a,$08
    ld ($FFFC),a
    ld a,$01
    ld ($C100),a
    ld ($C101),de
    ld b,$15
    push bc
    ld iyl,(iy+0)
    ld h,$00
    add hl,hl
    add hl,hl
    add hl,hl
    ld bc,$8400
    add hl,bc
    xor a
    bit 1,e
    jr nz,$2BA1
    add a,$02
    bit 6,e
    jr z,$2BA7
    add a,$04
    add a,l
    ld l,a
    jr nc,$2BAC
    inc h
    ldi
    ldd
    ld a,$40
    add a,e
    ld e,a
    jr nc,$2BB7
    inc d
    ld a,d
    cp $DD
    jr c,$2BBE
    ld d,$D6
    bit 6,e
    jr nz,$2BC7
    ld bc,$0040
    add iy,bc
    pop bc
    djnz $2B8D
    xor a
    ld ($FFFC),a
    ret
; sprite_ram_buffer_pointers_17: pointer_words, $2BCF-$2BF0
    dw $C200, $C230, $C260, $C290, $C2C0, $C2F0, $C320, $C350
    dw $C380, $C3B0, $C3E0, $C410, $C440, $C470, $C4A0, $C4D0
    dw $C500
    ld a,$06
    ld ($FFFF),a
    ld hl,$DD40
    ld ($C02A),hl
    ld hl,$DD00
    ld ($C028),hl
    jp $9966
    call $0A5B
    ld a,$01
    ld ($C20C),a
    call $0F7D
    ld a,$09
    ld ($C026),a
    call $3C88
    call $3CB3
    ld a,($C119)
    ld hl,$2C24
    jp $0008
    db $36, $2C, $9D, $2D, $2A, $2F, $14, $30, $94, $31, $9C, $32, $3B, $33, $15, $34
    db $19, $35
    ld a,($C1C2)
    or a
    jp nz,$2D63
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,($C1A3)
    and $3F
    jp z,$2CA4
    ld a,($C1A9)
    and $3F
    jp z,$2CA4
    ld a,($C1AF)
    and $3F
    jp z,$2CA4
    ld a,($C1CE)
    or a
    jp nz,$2D58
    call $2CBB
    bit 4,a
    jr nz,$2C71
    ld a,($C534)
    or a
    jr nz,$2C77
    call $2D48
    call $374D
    call $2D13
    bit 4,a
    jp nz,$2D3A
    ld a,($C534)
    or a
    jp z,$2D3A
    call $2D2F
    ld a,$01
    ld ($C1CE),a
    ld de,$0064
    call $2FE7
    call $374D
    ld hl,$9FBB
    xor a
    ld ($C541),a
    call $3F31
    jp $3744
    ld a,$27
    ld ($C531),a
    call $3DFB
    jp $3744
    ld ($C531),a
    call $3DFB
    call $374D
    jp $3E1C
    ld a,$28
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$78
    call $37C4
    ld ($DD00),a
    ld a,$D0
    ld ($DD01),a
    ld a,$88
    ld ($DD40),a
    ld a,$AB
    ld ($DD41),a
    xor a
    ld ($C53A),a
    ld ($C534),a
    call $0BC5
    ld a,($C01C)
    ld b,a
    and $03
    call nz,$3EFC
    ld a,($C01B)
    ld c,a
    and $03
    jr z,$2D09
    ld a,($C53A)
    inc a
    ld ($C53A),a
    and $0F
    ld a,c
    call z,$3EFC
    jr $2D0D
    xor a
    ld ($C53A),a
    ld a,b
    and $30
    jr z,$2CE6
    ret
    call $3E1C
    ld a,$29
    call $2CAF
    ld a,$62
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$50
    call $37C4
    jr $2CCD
    call $3E1C
    ld a,$2A
    ld ($C531),a
    jp $3DFB
    call $3E1C
    ld a,$2B
    ld ($C531),a
    call $3DFB
    jp $3744
    call $3E1C
    ld a,$2C
    call $2CAF
    ld a,$63
    ld ($C531),a
    jp $3DFB
    ld a,$2D
    ld ($C531),a
    call $3DFB
    jp $3744
    ld a,$09
    ld ($C119),a
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,($C1C3)
    or a
    jr nz,$2D98
    ld a,$2E
    call $2CAF
    ld a,$2F
    call $2CAF
    ld a,$64
    call $3564
    ld a,$01
    ld ($C1C3),a
    ld hl,$975C
    ld a,$03
    ld ($C541),a
    call $3F31
    jp $3744
    ld a,$30
    jp $2F91
    ld b,$92
    call $3CD6
    call $3DA3
    xor a
    ld ($C531),a
    ld a,$02
    ld ($C533),a
    ld hl,$3774
    ld a,$30
    jp $3758
    xor a
    ld ($C538),a
    ld ($C539),a
    ld a,$01
    ld ($C531),a
    ld a,$04
    ld ($C533),a
    ld hl,$377A
    ld a,$20
    jp $3758
    ld a,$02
    ld bc,$6F50
    ld de,$03E8
    ld hl,$C1D6
    push bc
    ex af,af'
    exx
    call $3E1C
    exx
    ld a,(hl)
    or a
    jp nz,$2E2A
    ex af,af'
    ld ($C531),a
    exx
    call $2CAF
    pop bc
    push bc
    ld a,b
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    pop bc
    ld a,c
    call $37C4
    call $2CCD
    exx
    bit 4,a
    jr nz,$2DB6
    ld a,($C534)
    or a
    jr z,$2DB6
    push hl
    call $3E9B
    pop hl
    ld a,($C536)
    or a
    jr z,$2DB6
    ld (hl),a
    ld de,$C1B8
    and a
    sbc hl,de
    jr nz,$2DB6
    ld a,$04
    ld ($C1E2),a
    jr $2DB6
    ld a,$03
    ex af,af'
    call $3E1C
    ex af,af'
    call $3564
    ld a,($C539)
    ld hl,$2E3D
    jp $0008
    or (hl)
    dec l
    xor (hl)
    ld sp,$3255
    and h
    ld ($1CCD),a
    ld a,$01
    adc a,b
    inc b
    ld de,$07D0
    ld hl,$C1B7
    ld a,(hl)
    or a
    jp nz,$2E2A
    ld a,b
    ld ($C531),a
    push bc
    exx
    call $3DFB
    pop bc
    ld a,$01
    ld ($C533),a
    ld a,c
    call $37C4
    call $2CCD
    exx
    jr $2E05
    ld a,$05
    ld bc,$7040
    ld de,$03E8
    ld hl,$C1B8
    jp $2DDA
    ld a,$06
    jp $2E2C
    ld a,$07
    ld ($C538),a
    ld ($C531),a
    ld a,$03
    ld ($C533),a
    ld hl,$3784
    ld a,$60
    jp $3758
    call $3E1C
    ld bc,$0870
    ld hl,$C1D8
    ld de,$04B0
    ld a,(hl)
    and $7F
    jp z,$2F22
    ld a,b
    ld ($C531),a
    push bc
    exx
    call $3DFB
    pop bc
    ld a,$01
    ld ($C533),a
    ld a,c
    call $2CCD
    exx
    jr $2EE5
    push hl
    ex af,af'
    exx
    call $3E1C
    pop hl
    ld a,(hl)
    and $7F
    jp z,$2F22
    ex af,af'
    call $2CAF
    exx
    ld a,b
    ld ($C531),a
    push bc
    exx
    call $3DFB
    pop bc
    ld a,$01
    ld ($C533),a
    ld a,c
    call $2CCD
    exx
    bit 4,a
    jp nz,$2E82
    ld a,($C534)
    or a
    jp z,$2E82
    push hl
    call $3EDA
    call $3EE7
    pop hl
    ld a,($C536)
    or a
    jp z,$2E82
    ld a,$80
    ld (hl),a
    jp $2E82
    ld a,$09
    ld bc,$7108
    ld hl,$C1D9
    ld de,$01F4
    jp $2EBF
    ld a,$0A
    ld bc,$7240
    ld hl,$C1D7
    ld de,$07D0
    jp $2EBF
    ld a,$0B
    call $3564
    jp $2E82
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,($C1D2)
    rlca
    jp c,$2FD5
    or a
    jp nz,$2FA7
    call $3E1C
    ld a,$16
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$70
    call $37C4
    call $2CCD
    bit 4,a
    jp nz,$2FA3
    ld a,($C534)
    or a
    jp z,$2FA3
    call $3E1C
    ld a,$17
    call $2CAF
    ld a,$73
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$40
    call $2CCD
    bit 4,a
    jp nz,$2F9F
    ld a,($C534)
    or a
    jp z,$2F9F
    call $3E1C
    ld a,$18
    call $2CAF
    ld a,$74
    ex af,af'
    call $3E1C
    ex af,af'
    ld ($C531),a
    call $3DFB
    jp $3744
    ld a,$19
    jr $2F91
    ld a,$1A
    jr $2F91
    call $3E1C
    ld a,$1B
    call $3564
    ld a,$01
    ld ($C1BD),a
    ld a,$80
    ld ($C1D2),a
    ld de,$03E8
    call $2FE7
    call $3E1C
    ld a,$1C
    call $3564
    ld hl,$9239
    ld a,$02
    ld ($C541),a
    call $3F31
    jp $3744
    ld a,$1D
    call $3564
    ld a,($C22A)
    ld ($C542),a
    ld e,a
    call $2FEF
    jp $3747
    ld hl,($C227)
    add hl,de
    ld ($C227),hl
    ret
    ld a,($C222)
    ld d,a
    ld a,$AA
    ld ($DE64),a
    ld hl,$C594
    ld b,e
    ld a,d
    push de
    call $61AE
    call $3CB3
    pop de
    ld a,($C542)
    ld hl,$C222
    cp (hl)
    ret z
    inc (hl)
    ld d,(hl)
    call $0BC5
    jr $2FF3
    ld b,$92
    call $3CD6
    call $3DA3
    xor a
    ld ($C537),a
    ld a,$0C
    ld ($C531),a
    ld a,$03
    ld ($C533),a
    ld hl,$378C
    ld a,$40
    jp $3758
    call $3E1C
    ld a,$0D
    call $2CAF
    ld a,$6C
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$68
    call $37C4
    call $2CCD
    bit 4,a
    jp nz,$301C
    ld a,($C534)
    or a
    jp z,$301C
    ld de,$0032
    call $3E9B
    ld a,($C536)
    or a
    jr z,$301C
    ld a,($C222)
    add a,$0A
    ld hl,$C22A
    ld e,(hl)
    jr c,$3083
    cp e
    jr nc,$3083
    ld ($C542),a
    ld ($C222),a
    ld hl,$C594
    call $2FEF
    jr $301C
    ld a,e
    ld ($C542),a
    call $2FEF
    jr $301C
    call $3E1C
    ld a,$0E
    call $2CAF
    ld a,$6D
    ld c,$78
    push bc
    ex af,af'
    call $3E1C
    ex af,af'
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    pop bc
    ld a,c
    call $37C4
    call $2CCD
    bit 4,a
    jp nz,$301C
    ld a,($C534)
    or a
    jp z,$301C
    ld de,$03E8
    call $3E9B
    ld a,($C536)
    or a
    jp z,$301C
    ld a,($C1B6)
    or a
    jr z,$30DD
    ld a,($C22A)
    ld ($C542),a
    ld e,a
    call $2FEF
    jp $301C
    ld a,$01
    ld ($C1B6),a
    ld a,$0F
    ld ($C537),a
    ld c,$38
    jr $3098
    ld a,$10
    push af
    call $3E1C
    pop af
    ld ($C531),a
    call $3DFB
    jp $3744
    call $3E1C
    ld a,$61
    ld ($C531),a
    call $3DFB
    ld a,$09
    ld ($FFFF),a
    ld a,$01
    call $316F
    ld de,$7968
    call $BEFB
    ld a,$02
    call $316F
    ld de,$79E8
    call $BEFB
    ld a,$03
    call $316F
    ld de,$7A68
    call $BEFB
    ld a,$04
    call $316F
    ld de,$7AE8
    call $BEFB
    ld a,$05
    call $316F
    ld de,$7B68
    call $BEFB
    ld a,$05
    ld ($C533),a
    ld a,$18
    call $2CCD
    bit 4,a
    jp nz,$301C
    ld a,($C534)
    or a
    jp z,$301C
    ld hl,$FFFF
    ld (hl),$09
    ld hl,$7A68
    ld e,$00
    ld d,a
    srl d
    rr e
    add hl,de
    ex de,hl
    call $3183
    jp $310B
    push af
    ld hl,$BF7A
    rst $0018
    ld a,$08
    ld ($FFFC),a
    ld c,(hl)
    inc hl
    ld b,(hl)
    dec hl
    xor a
    ld ($FFFC),a
    pop af
    ret
    push af
    ld hl,$BF7A
    rst $0018
    ld a,$08
    ld ($FFFC),a
    xor a
    ld (hl),a
    ld ($FFFC),a
    pop af
    ret
    ld b,$92
    call $3CD6
    call $3DA3
    ld a,$31
    ld ($C531),a
    ld a,$02
    ld ($C533),a
    ld hl,$3794
    ld a,$50
    jp $3758
    ld a,$01
    ld ($C539),a
    xor a
    ld ($C538),a
    ld a,$32
    ld ($C531),a
    ld a,$04
    ld ($C533),a
    ld hl,$379A
    ld a,$20
    jp $3758
    ld bc,$3380
    ld hl,$C1B0
    ld de,$0190
    exx
    call $3E1C
    exx
    ld a,(hl)
    or a
    jp nz,$2E2A
    ld a,b
    ld ($C531),a
    push bc
    exx
    call $3DFB
    ld a,$01
    ld ($C533),a
    pop bc
    ld a,c
    call $37C4
    call $2CCD
    exx
    bit 4,a
    jp nz,$3214
    ld a,($C534)
    or a
    jp z,$3214
    push hl
    call $3E9B
    pop hl
    ld a,($C536)
    or a
    jr z,$3214
    ld (hl),a
    ld a,($C538)
    or a
    jr z,$31AE
    jp $3255
    ld a,($C538)
    or a
    ld a,$01
    jp z,$31AE
    jp $3255
    ld bc,$3488
    ld hl,$C1B1
    ld de,$07D0
    jr $31D2
    call $3E1C
    ld a,($C1B2)
    or a
    jp nz,$2E2A
    call $3E1C
    ld a,$35
    call $2CAF
    ld bc,$6E40
    ld hl,$C1B2
    ld de,$1388
    jr $31DC
    ld a,$36
    push af
    call $3E1C
    pop af
    call $3564
    jp $3214
    ld a,$02
    ld ($C538),a
    ld ($C539),a
    ld a,$37
    ld ($C531),a
    ld a,$04
    ld ($C533),a
    ld hl,$37A4
    ld a,$20
    jp $3758
    ld bc,$3888
    ld hl,$C1AA
    ld de,$02BC
    jp $31D2
    ld bc,$3978
    ld hl,$C1AB
    ld de,$07D0
    jp $31D2
    ld bc,$3A88
    ld hl,$C1AC
    ld de,$1770
    jp $31D2
    ld a,$3B
    jr $324A
    ld a,$3C
    jp $30ED
    ld b,$92
    call $3CD6
    call $3DA3
    ld a,$03
    ld ($C539),a
    ld a,$11
    ld ($C531),a
    ld a,$03
    ld ($C533),a
    ld hl,$37AE
    ld a,$40
    jp $3758
    call $3E1C
    ld a,$12
    ld bc,$6568
    ld hl,$C1A4
    ld de,$01F4
    ex af,af'
    exx
    call $3E1C
    exx
    ld a,(hl)
    or a
    jp nz,$2E2A
    ex af,af'
    exx
    call $2CAF
    exx
    ld a,b
    ld ($C531),a
    push de
    push hl
    ld a,c
    push af
    call $3DFB
    ld a,$01
    ld ($C533),a
    pop af
    call $37C4
    call $2CCD
    pop hl
    pop de
    bit 4,a
    jp nz,$32A4
    ld a,($C534)
    or a
    jp z,$32A4
    push hl
    call $3E9B
    pop hl
    ld a,($C536)
    or a
    jp z,$32A4
    ld (hl),a
    ld a,$80
    ld ($C1A3),a
    jp $32A4
    call $3E1C
    ld a,$13
    ld bc,$6630
    ld hl,$C1A5
    ld de,$07D0
    jp $32C9
    call $3E1C
    ld a,$14
    ld bc,$6758
    ld hl,$C1A6
    ld de,$1388
    jp $32C9
    ld a,$15
    jp $30ED
    ld b,$92
    call $3CD6
    call $3DA3
    ld a,$3D
    ld ($C531),a
    ld a,$03
    ld ($C533),a
    ld hl,$37B6
    ld a,$30
    jp $3758
    ld a,$3E
    ex af,af'
    call $3E1C
    ex af,af'
    call $3564
    jp $3343
    call $3E1C
    ld a,($C1D6)
    rlca
    jp c,$33CB
    or a
    jp nz,$33A4
    call $3E1C
    ld a,$3F
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$68
    call $37C4
    call $2CCD
    ex af,af'
    call $3E1C
    ex af,af'
    bit 4,a
    jp nz,$33D0
    ld a,($C534)
    or a
    jr nz,$339A
    jr $33D0
    ld a,$40
    call $2CAF
    ld a,$75
    jp $3357
    ld a,$80
    ld ($C1D6),a
    ld hl,($C225)
    ld de,$05DC
    call $3EDA
    ld de,$0096
    call $2FE7
    call $3E1C
    ld a,$41
    call $2CAF
    ld a,$76
    call $3564
    call $3EE7
    jp $3343
    ld a,$42
    jp $3357
    ld a,$43
    jp $3357
    call $3E1C
    ld a,$44
    call $2CAF
    ld a,$77
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$58
    call $2CCD
    ex af,af'
    call $3E1C
    ex af,af'
    bit 4,a
    jp nz,$3410
    ld a,($C534)
    or a
    jr nz,$3401
    jr $3410
    ld a,$45
    call $2CAF
    ld a,$46
    call $2CAF
    ld a,$78
    jp $3357
    ld a,$47
    jp $3357
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,($C1C2)
    rlca
    jr nc,$342F
    ld a,($C1C3)
    rlca
    jr nc,$342F
    ld a,($C1C4)
    rlca
    jr c,$3471
    ld a,($C1B9)
    or a
    jr nz,$346C
    ld a,$1E
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$50
    call $2CCD
    ex af,af'
    call $3E1C
    ex af,af'
    bit 4,a
    jp nz,$3467
    ld a,($C534)
    or a
    jp z,$3467
    ld a,$1F
    call $2CAF
    ld a,$20
    call $2CAF
    ld a,$68
    jp $2F91
    ld a,$21
    jp $2F91
    ld a,$60
    jp $2F91
    ld a,($C1DA)
    or a
    jr z,$346C
    call $3E1C
    ld a,$22
    call $2CAF
    ld a,$69
    call $3564
    call $3E1C
    ld a,$23
    call $2CAF
    ld a,$25
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$88
    call $37C4
    call $2CCD
    ex af,af'
    call $3E1C
    ex af,af'
    bit 4,a
    jp nz,$34B1
    ld a,($C534)
    or a
    jr nz,$34B6
    ld a,$24
    jp $2F91
    ld a,($C1D4)
    or a
    jr z,$34CC
    dec a
    jr nz,$34DE
    call $3E1C
    ld a,$5D
    call $2CAF
    ld a,$6B
    jp $2F91
    call $3E1C
    ld a,$5E
    call $2CAF
    ld a,$7E
    call $3564
    ld a,$5F
    jp $2F91
    ld a,($C1B7)
    rrca
    jp nc,$34F3
    xor a
    ld ($C1B7),a
    ld a,$26
    call $2CAF
    ld a,$6A
    call $3564
    ld a,($C1CD)
    or $40
    ld ($C1CD),a
    ld a,$89
    ld hl,$0200
    ld de,$0000
    ld bc,$8088
    ld ($C181),a
    call $2654
    ld a,$03
    ld ($C01F),a
    ld a,$00
    ld ($C20C),a
    jp $0F7D
    ld a,($C1DA)
    or a
    jp nz,$35A3
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,($C1CE)
    or a
    jr z,$355C
    ld a,($C1C8)
    or a
    jr z,$3572
    ld a,($C1C3)
    or a
    jr z,$354B
    ld a,($C1D3)
    or a
    jp z,$35DE
    ld a,($C1A7)
    or a
    jp z,$35C2
    jp $35DE
    ld a,($C1A7)
    or a
    jp nz,$3558
    ld a,($C1D3)
    or a
    jr nz,$35C2
    ld a,$4A
    jr $355E
    ld a,$48
    call $3564
    jp $358D
    push af
    call $3E1C
    pop af
    ld ($C531),a
    call $3DFB
    jp $374D
    ld a,$01
    ld ($C1C8),a
    ld a,$49
    call $3564
    ld a,$01
    ld ($C541),a
    ld hl,$9BD0
    call $3F31
    call $374D
    jp $358D
    ld a,($C1C2)
    or a
    jr nz,$35DE
    ld a,($C1C4)
    or a
    jr nz,$35DE
    ld a,($C1DA)
    or a
    jp z,$3747
    jp $35B0
    ld a,$0A
    ld ($C119),a
    ld b,$83
    call $3CD6
    call $3DA3
    ld a,$4B
    ld ($C531),a
    ld a,$02
    ld ($C533),a
    ld hl,$37BE
    ld a,$60
    jp $3758
    call $3E1C
    ld a,$4C
    call $2CAF
    ld a,$79
    call $3564
    call $3E1C
    ld a,$4D
    call $3564
    ld a,($C1C2)
    or a
    jp z,$358D
    call $3E1C
    ld a,$4E
    call $2CAF
    ld a,$7A
    ld ($C531),a
    call $3DFB
    ld a,$01
    ld ($C533),a
    ld a,$30
    call $37C4
    call $2CCD
    ex af,af'
    call $3E1C
    ex af,af'
    bit 4,a
    jp nz,$360C
    ld a,($C534)
    or a
    jp nz,$3652
    ld a,($C1DA)
    or a
    jr z,$3599
    ld a,($C1C2)
    rlca
    jp nc,$3599
    ld a,($C1C3)
    rlca
    jp nc,$3599
    ld a,($C1C4)
    rlca
    jp nc,$3599
    call $3E1C
    ld a,$4F
    call $3564
    call $3E1C
    ld a,$50
    jp $2F91
    call $3E1C
    ld a,$51
    call $3564
    call $3E1C
    ld a,$52
    call $3564
    ld a,$08
    ld ($C119),a
    call $3E1C
    jp $35B0
    ld a,($C1C2)
    or a
    jp z,$36E9
    ld a,($C1C3)
    or a
    jr z,$3682
    ld a,($C1C4)
    or a
    jr z,$36B3
    call $3E1C
    ld a,$55
    ld ($C531),a
    ld a,$02
    ld ($C533),a
    ld hl,$367A
    ld a,$30
    jp $36C5
; state_handler_dispatch_4: pointer_words, $367A-$3681
    dw $35DE, $36F9, $3713, $3725
    ld a,($C1C4)
    or a
    jr z,$36A3
    call $3E1C
    ld a,$56
    ld ($C531),a
    ld a,$01
    ld ($C533),a
    ld hl,$369D
    ld a,$30
    jp $36C5
; state_handler_dispatch_3a: pointer_words, $369D-$36A2
    dw $35DE, $36F9, $3725
    call $3E1C
    ld a,$53
    call $3564
    bit 4,a
    jp nz,$35DE
    jp $36F9
    call $3E1C
    ld a,$54
    ld ($C531),a
    ld a,$01
    ld ($C533),a
    ld hl,$36E3
    ld a,$30
    push hl
    push af
    call $3E1C
    call $3DFB
    pop af
    call $2CCD
    bit 4,a
    jp z,$36DB
    ld a,$FF
    ld ($C534),a
    ld a,($C534)
    inc a
    pop hl
    jp $0008
; state_handler_dispatch_3b: pointer_words, $36E3-$36E8
    dw $35DE, $36F9, $3713
    call $3E1C
    ld a,$57
    call $3564
    bit 4,a
    jp nz,$35DE
    jp $3725
    ld a,$58
    call $370B
    ld a,$59
    call $370B
    ld a,$81
    ld ($C1C2),a
    jp $35DE
    push af
    call $3E1C
    pop af
    jp $3564
    ld a,$5A
    call $370B
    ld a,$7D
    call $370B
    ld a,$81
    ld ($C1C3),a
    jp $35DE
    ld a,$5B
    call $370B
    ld a,$7B
    call $370B
    ld a,$5C
    call $370B
    ld a,$7C
    call $370B
    ld a,$81
    ld ($C1C4),a
    jp $35DE
    call $0AA7
    call $374D
    ld a,$04
    ld ($C01F),a
    ret
    call $0BC5
    ld a,($C01C)
    and $30
    jr z,$374D
    ret
    push hl
    push af
    call $3E1C
    call $3DFB
    pop af
    call $2CCD
    bit 4,a
    jp z,$376D
    xor a
    ld ($C534),a
    ld a,($C534)
    pop hl
    jp $0008
; scenario_dispatch_40: pointer_words, $3774-$37C3
    dw $3747, $2E82, $2DB6, $2DA5, $2DCF, $2E45, $2E6F, $2E7D
    dw $2DA5, $2E97, $2F06, $2F14, $30EB, $3032, $308C, $30FB
    dw $3297, $31AE, $3255, $319C, $31C9, $3220, $322B, $3248
    dw $319C, $326F, $327B, $3287, $3293, $3336, $32BB, $3314
    dw $3325, $3747, $3355, $33D5, $3362, $3747, $3528, $3637
    push af
    ld h,$00
    ld l,a
    add hl,hl
    add hl,hl
    add hl,hl
    ld de,$7822
    add hl,de
    ex de,hl
    rst $0028
    ld hl,$37D9
    call $9EFC
    pop af
    ret
; unresolved_37D9: unresolved, $37D9-$37E1
    db $E7, $CF, $D0, $FD, $E7, $C1, $C7, $D4, $FF
    push hl
    call $0A5B
    ld a,($C010)
    and $DF
    ld ($C010),a
    ld a,$09
    ld ($C026),a
    call $3C88
    call $3CB3
    call $3E4D
    ld a,$0C
    ld ($FFFF),a
    pop hl
    jp $3E77
    ld hl,$8119
    call $37E2
    ld de,$7894
    rst $0028
    ld a,($C1A0)
    cp $0A
    jr nz,$3826
    ld a,$0C
    ld ($FFFF),a
    ld hl,$82E2
    ld de,$7892
    call $3EF7
    jr $382F
    ld b,a
    ld a,$0A
    ld ($FFFF),a
    call $3E8E
    ld de,$78A2
    ld a,($C222)
    call $38BE
    ld de,$7910
    ld a,($C223)
    call $38BE
    ld de,$7990
    ld a,($C224)
    call $38BE
    ld hl,($C227)
    ld de,$7924
    call $3E86
    ld hl,($C225)
    ld de,$79A6
    call $3E86
    ld a,($C22A)
    ld de,$78AA
    call $38BE
    ld hl,($C1A1)
    ld de,$7930
    call $3E86
    ld b,$05
    ld de,$79D6
    xor a
    push bc
    push af
    call $388F
    pop af
    pop bc
    inc a
    djnz $3874
    call $0AA7
    call $374D
    ld a,$26
    ld ($C010),a
    ld a,$04
    ld ($C01F),a
    ret
    ld c,a
    ld hl,$3A67
    rst $0018
    ld a,c
    push af
    call $38AD
    ld a,$0C
    ld ($FFFF),a
    pop af
    ld hl,$3BBD
    rst $0018
    ld a,c
    ex de,hl
    ld bc,$0080
    add hl,bc
    ex de,hl
    jp $3EF6
    ld bc,$0500
    cp $03
    jr nz,$38B5
    inc b
    inc hl
    inc c
    bit 7,(hl)
    ret nz
    djnz $38B5
    ld c,b
    ret
    ex af,af'
    rst $0028
    ex af,af'
    ld l,a
    ld h,$00
    ld a,$0A
    ld ($FFFF),a
    jp $BF16
    xor a
    ld ($C53F),a
    ld hl,$82E6
    call $37E2
    ld a,$01
    ld ($C026),a
    xor a
    ld ($C533),a
    call $3AA3
    ld a,$0D
    ld ($FFFF),a
    ld hl,$BBF7
    ld de,$7600
    call $0695
    ld hl,$8000
    ld de,$4120
    ld b,$1A
    xor a
    call $3ACC
    ld a,$08
    ld ($C026),a
    ld de,$798E
    ld hl,$C1A4
    ld b,$05
    ld a,$09
    ld ($C53E),a
    call $3AE3
    ld de,$7A4E
    inc hl
    ld b,$05
    ld a,$36
    ld ($C53E),a
    call $3AE3
    ld de,$7B0E
    inc hl
    ld b,$05
    ld a,$63
    ld ($C53E),a
    call $3AE3
    ld de,$7BCE
    inc hl
    ld b,$06
    ld a,$90
    ld ($C53E),a
    call $3AE3
    ld de,$7C8E
    inc hl
    ld b,$05
    ld a,$C6
    ld ($C53E),a
    call $3AE3
    call $3B1D
    call $0AA7
    call $0BC5
    ld bc,($C01B)
    ld hl,$C53B
    ld a,c
    and $0F
    jr nz,$395F
    ld (hl),a
    inc (hl)
    ld a,(hl)
    and $0F
    jr nz,$3966
    ld b,c
    ld a,b
    and $0C
    jr z,$3970
    call $39F5
    jr $394F
    ld a,b
    and $03
    jr z,$397A
    call $3A71
    jr $394F
    ld a,($C01C)
    and $30
    jr z,$394F
    and $10
    jp nz,$3884
    ld hl,$8325
    call $37E2
    ld a,$0D
    ld ($FFFF),a
    ld de,$4120
    ld a,$1A
    ld b,$18
    call $3ACC
    ld a,$08
    ld ($C026),a
    ld de,$7986
    ld hl,$C1C2
    ld b,$06
    ld a,$09
    ld ($C53E),a
    call $3AE3
    ld de,$7A46
    ld b,$06
    ld a,$3F
    ld ($C53E),a
    call $3AE3
    ld de,$7B06
    ld b,$04
    ld a,$75
    ld ($C53E),a
    call $3AE3
    ld de,$7BC6
    ld b,$04
    ld a,$99
    ld ($C53E),a
    call $3AE3
    ld de,$7C86
    ld b,$04
    ld a,$BD
    ld ($C53E),a
    call $3AE3
    ld a,$D0
    ld ($DD00),a
    call $0AA7
    call $0F7D
    call $374D
    jp $3884
    xor a
    ld ($C53B),a
    ld a,($C533)
    ld bc,$0500
    cp $03
    jr nz,$3A04
    inc b
    ld hl,$3A67
    rst $0018
    ld e,l
    ld d,h
    inc hl
    ld a,(hl)
    or a
    jr z,$3A10
    inc c
    djnz $3A0A
    ld a,c
    or a
    ret z
    ex de,hl
    ld b,(hl)
    ld a,($C01B)
    bit 3,a
    jr nz,$3A43
    dec b
    ret m
    ld (hl),b
    ld e,b
    push hl
    inc b
    inc hl
    ld a,(hl)
    or a
    jr z,$3A24
    djnz $3A24
    ld (hl),$01
    pop hl
    ld a,e
    or a
    jp z,$3B1D
    ld b,e
    inc hl
    ld a,(hl)
    or a
    jr z,$3A34
    djnz $3A34
    ld (hl),$81
    call $3F06
    jp $3B1D
    ld a,b
    cp c
    ret nc
    inc b
    ld (hl),b
    ld e,b
    dec b
    jr z,$3A57
    push hl
    inc hl
    ld a,(hl)
    or a
    jr z,$3A4D
    djnz $3A4D
    ld (hl),$01
    pop hl
    ld b,e
    inc hl
    ld a,(hl)
    or a
    jr z,$3A58
    djnz $3A58
    ld (hl),$81
    call $3F06
    jp $3B1D
    and e
    pop bc
    xor c
    pop bc
    xor a
    pop bc
    or l
    pop bc
    cp h
    pop bc
    rrca
    ld a,($C533)
    jr nc,$3A82
    dec a
    ret m
    ld ($C533),a
    inc a
    ld ($C534),a
    jr $3A8D
    inc a
    cp $05
    ret z
    ld ($C533),a
    dec a
    ld ($C534),a
    call $3F06
    ld a,$01
    ld ($C026),a
    ld a,($C533)
    call $3AA3
    ld a,$09
    ld ($C026),a
    ld a,($C534)
    add a,a
    ld h,a
    add a,a
    add a,h
    ld h,a
    ld l,$00
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld de,$7907
    add hl,de
    ld b,$06
    ex de,hl
    rst $0028
    ld a,($C026)
    out ($BE),a
    ld hl,$0002
    add hl,de
    djnz $3ABC
    jp $3B7D
    ld hl,$BF8A
    push af
    rst $0018
    push bc
    push de
    call $0695
    pop de
    ex de,hl
    ld bc,$0120
    add hl,bc
    ex de,hl
    pop bc
    pop af
    inc a
    djnz $3ACC
    ret
    push bc
    bit 0,(hl)
    push hl
    call nz,$3AF8
    pop hl
    inc hl
    pop bc
    ld a,($C53E)
    add a,$09
    ld ($C53E),a
    djnz $3AE3
    ret
    ld bc,$FF48
    ex de,hl
    add hl,bc
    ex de,hl
    ld b,$03
    ld a,($C53E)
    ld h,a
    push bc
    rst $0028
    ld b,$03
    ld a,h
    out ($BE),a
    inc h
    ld a,($C026)
    out ($BE),a
    djnz $3B08
    ex de,hl
    ld bc,$0040
    add hl,bc
    ex de,hl
    pop bc
    djnz $3B04
    ret
    ld hl,$DD40
    ld de,$DD00
    exx
    ld de,$C1A4
    ld hl,$1758
    ld b,$05
    call $3BC8
    ld a,($C543)
    ld ($C1A3),a
    ld de,$C1AA
    ld hl,$2F58
    ld b,$05
    call $3BC8
    ld a,($C543)
    ld ($C1A9),a
    ld de,$C1B0
    ld hl,$4758
    ld b,$05
    call $3BC8
    ld a,($C543)
    ld ($C1AF),a
    ld de,$C1B6
    ld hl,$5F58
    ld b,$06
    call $3BC8
    ld a,($C543)
    ld ($C1B5),a
    ld de,$C1BD
    ld hl,$7758
    ld b,$05
    call $3BC8
    ld a,($C543)
    ld ($C1BC),a
    exx
    ld a,$D0
    ld (de),a
    ld bc,$0500
    ld a,($C533)
    ld d,a
    ld hl,$3A67
    rst $0018
    ld a,d
    cp $03
    jr nz,$3B8E
    inc b
    inc hl
    inc c
    bit 7,(hl)
    jr nz,$3BA2
    djnz $3B8E
    ld hl,$0920
    ld de,$785E
    ld bc,$000D
    jp $06D4
    ld a,$09
    ld ($C026),a
    exx
    call $3B96
    exx
    ld a,$0C
    ld ($FFFF),a
    ld a,d
    ld hl,$3BBD
    rst $0018
    ld a,c
    ld de,$785E
    jp $3EF6
    ld a,(hl)
    add a,c
    call nz,$1681
    add a,d
    ld e,e
    add a,d
    and b
    add a,d
    ret
    xor a
    ld ($C543),a
    ld c,$00
    ld a,(de)
    inc de
    bit 0,a
    jr z,$3BD9
    inc c
    rlca
    call c,$3BDC
    djnz $3BCE
    ret
    ld a,c
    ld ($C543),a
    dec a
    rrca
    rrca
    rrca
    add a,l
    ld l,a
    ld a,h
    exx
    ld b,$04
    ld (de),a
    inc de
    djnz $3BEA
    ld b,$02
    add a,$08
    ld (de),a
    inc de
    ld (de),a
    inc de
    djnz $3BF0
    add a,$07
    ld (de),a
    inc de
    ld (de),a
    inc de
    ld a,$B0
    ld c,a
    exx
    ld a,l
    exx
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    add a,$08
    ld (hl),a
    inc hl
    inc c
    ld (hl),c
    inc hl
    add a,$08
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    add a,$07
    ld (hl),a
    inc hl
    inc c
    ld (hl),c
    inc hl
    add a,$E9
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    add a,$17
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    add a,$E9
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    add a,$10
    ld (hl),a
    inc hl
    inc c
    ld (hl),c
    inc hl
    add a,$F0
    ld (hl),a
    inc hl
    dec c
    dec c
    ld (hl),c
    inc hl
    add a,$08
    ld (hl),a
    inc hl
    ld (hl),c
    inc hl
    exx
    ret
    call $0A5B
    call $3C88
    call $3D8F
    call $3DCC
    call $0AA7
    ld a,($C11A)
    cp $02
    jr c,$3C7F
    cp $03
    jr z,$3C7F
    call $374D
    call $0A80
    ld hl,$0920
    ld de,$7880
    ld bc,$0340
    call $06D4
    ld a,($C11A)
    add a,$04
    ld ($C11A),a
    call $3DD6
    call $0AA7
    call $374D
    ld a,$04
    ld ($C01F),a
    ret
    ld hl,$0920
    ld de,$7800
    ld bc,$0380
    call $06D4
    ld hl,$91EA
    ld de,$6820
    ld c,$40
    call $0BA1
    ld hl,$914A
    ld de,$6600
    ld c,$0D
    call $0BA1
    ld hl,$952A
    ld de,$6400
    jp $0695
    ld hl,$C582
    ld de,$7D42
    ld bc,$003E
    call $06C1
    ld hl,$C5C2
    ld de,$7DC2
    ld bc,$003E
    call $06C1
    ld a,$0C
    ld ($FFFF),a
    ld hl,$8100
    jp $3E77
    call $3F0C
    ld a,$0D
    ld ($FFFF),a
    ld hl,$A9A3
    ld de,$5600
    call $0695
    ld hl,$ACB2
    ld de,$D600
    ld c,$02
    call $0BEF
    ld hl,$D600
    ld de,$7842
    ld bc,$0F1E
    call $0702
    ld hl,$3D4D
    call $3D40
    push bc
    ld a,b
    ld hl,$3D63
    rst $0018
    ld de,$C160
    ld bc,$0010
    ldir
    ld de,$4000
    call $0695
    xor a
    ld ($C026),a
    ld hl,$3D58
    call $3D40
    pop bc
    ld a,b
    ld hl,$3D79
    rst $0018
    ld de,$D600
    call $0C20
    ld hl,$D600
    ld de,$7884
    ld bc,$0D0D
    call $06E8
    call $3D8F
    jp $0AA7
    ld a,($C119)
    ld b,a
    ld e,a
    ld d,$00
    add hl,de
    ld a,(hl)
    ld ($FFFF),a
    ret
; unresolved_3D4D: unresolved, $3D4D-$3D8E
    db $0E, $0E, $0E, $0E, $0F, $0D, $0F, $0F, $0F, $0E, $0F, $0D, $0D, $0B, $0D, $0F
    db $0E, $0D, $0E, $0D, $0D, $0D, $00, $80, $32, $91, $32, $9C, $78, $AB, $00, $80
    db $47, $AD, $5F, $8F, $6B, $A1, $06, $AF, $42, $B6, $06, $AF, $BE, $B9, $D1, $B9
    db $1E, $BC, $3D, $BA, $B0, $BF, $75, $BF, $B5, $BA, $16, $BF, $45, $BB, $C6, $BA
    db $94, $BB
    ld hl,$914A
    ld de,$6C00
    ld c,$40
    call $0BA1
    ld hl,$952A
    ld de,$74E0
    jp $0695
    ld a,$0A
    ld ($FFFF),a
    ld a,$09
    ld ($C026),a
    ld hl,$BE70
    ld a,($C119)
    rst $0018
    ld de,$DA00
    call $07D5
    ld hl,$DA00
    ld de,$7C44
    rst $0028
    ld a,$0C
    ld ($FFFF),a
    call $9EFC
    jp $3EE7
    call $3DE0
    ld de,$780E
    rst $0028
    jp $9EFC
    call $3DE0
    ld de,$7886
    rst $0028
    jp $9EFC
    ld a,$0C
    ld ($FFFF),a
    ld a,$09
    ld ($C026),a
    ld hl,$9FC2
    ld a,($C11A)
    rst $0018
    ld de,$DA00
    call $07D5
    ld hl,$DA00
    ret
    ld a,$0C
    ld ($FFFF),a
    ld a,$09
    ld ($C026),a
    ld a,($C531)
    ld hl,$8332
    rst $0018
    ld de,$DA00
    call $07D5
    ld hl,$DA00
    ld de,$7862
    rst $0028
    jp $9EFC
    ld de,$7860
    ld bc,$1410
    ld a,$10
    ld ($C53C),a
    rst $0028
    ld a,$09
    ld ($C026),a
    ld a,$0A
    ld ($FFFF),a
    ld a,$A7
    call $3E91
    dec c
    jr nz,$3E28
    ld a,($C53C)
    ld c,a
    ld hl,$0040
    add hl,de
    ex de,hl
    djnz $3E27
    ld a,$D0
    ld ($DD00),a
    jp $0BC5
    ld a,$0D
    ld ($FFFF),a
    ld a,$29
    ld ($C164),a
    ld hl,$A9A3
    ld de,$7000
    call $0695
    ld hl,$ABBA
    ld de,$D600
    ld c,$02
    call $0BEF
    ld hl,$D600
    ld de,$7800
    ld bc,$0500
    jp $06C1
    ld b,(hl)
    inc hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    call $0739
    ld b,(hl)
    inc b
    jp nz,$3E77
    ret
    ld a,$0A
    ld ($FFFF),a
    jp $BEF7
    ld a,$30
    add a,b
    out ($BE),a
    ld a,($C026)
    nop
    out ($BE),a
    nop
    ret
    ld a,$0C
    ld ($FFFF),a
    xor a
    ld ($C536),a
    ld hl,($C225)
    and a
    sbc hl,de
    jr c,$3EB6
    ld ($C225),hl
    ld a,$01
    ld ($C536),a
    jr $3EE7
    ld a,$0A
    ld ($FFFF),a
    ld hl,$BB79
    ld de,$D600
    ld c,$02
    call $0BEF
    ld hl,$D600
    ld de,$7A62
    ld bc,$071C
    call $0702
    ld a,$D0
    ld ($DD00),a
    jp $374D
    ld a,$01
    ld ($C536),a
    ld hl,($C225)
    add hl,de
    ld ($C225),hl
    ret
    ld hl,$8111
    call $3E77
    ld hl,($C225)
    ld de,$7CD0
    jp $3E86
    rst $0018
    ld b,(hl)
    inc hl
    jp $0739
    ex af,af'
    ld a,$0C
    ld ($FFFF),a
    ex af,af'
    jp $9F68
    ld a,$AE
    ld ($DE64),a
    ret
    ld a,($C02D)
    cp b
    ret z
    ld a,b
    ld ($C02D),a
    ld ($DE64),a
    ret
; unresolved_3F19: unresolved, $3F19-$3F30
    db $21, $3F, $2D, $3F, $29, $3F, $25, $3F, $0A, $1E, $42, $BF, $0A, $22, $9A, $BF
    db $09, $22, $86, $BF, $0B, $2A, $67, $BF
    ld a,$0D
    ld ($FFFF),a
    ld de,$5D00
    call $0695
    ld hl,$3F19
    ld a,($C541)
    rst $0018
    ld a,(hl)
    ld ($FFFF),a
    inc hl
    ld a,(hl)
    ld ($C541),a
    inc hl
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld de,$D600
    ld c,$02
    call $0BEF
    call $0BC5
    ld b,$91
    call $3F0C
    ld hl,$D600
    ld de,$7A4E
    ld b,$05
    ld a,($C541)
    ld c,a
    jp $0702
    ld bc,$1202
    ld de,$0C0F
    ld hl,$B309
    call $46AC
    ld bc,$0500
    ld de,$3F88
    ld hl,$3F94
    jp $44A3
; endgame_local_dispatch_12: pointer_words, $3F88-$3F9F
    dw $1304, $1306, $1308, $130A, $130C, $130E, $3FA0, $3FA6
    dw $3FAA, $3FAE, $4129, $41C9
    ld a,$05
    ld ($C01F),a
    ret
    ld a,$0A
    jr $3FA2
    ld a,$0B
    jr $3FA2
    ld hl,$C1C2
    ld bc,$0600
    ld a,(hl)
    inc hl
    or a
    jr z,$3FBA
    inc c
    djnz $3FB4
    ld a,c
    ld hl,$3FC3
    jp $0008
; endgame_branch_dispatch_7: pointer_words, $3FC3-$3FD0
    dw $3FD1, $3FF5, $4025, $4055, $406D, $409D, $40B5
    ld bc,$0403
    ld de,$1405
    ld hl,$B343
    jr $3FE5
    ld bc,$0304
    ld de,$1909
    ld hl,$B355
    call $46AC
    call $0BC5
    ld a,($C01C)
    and $30
    jr z,$3FE8
    jp $3FA0
    ld bc,$0D03
    ld de,$1007
    ld a,($C1C4)
    or a
; unresolved_3FFF: unresolved, $3FFF-$3FFF
    db $20
