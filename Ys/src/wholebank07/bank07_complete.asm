; Ys SMS physical bank 7. Standalone source-only 16-KiB reconstruction.
; Code uses Z80 mnemonics; typed data sources are in wholebank07/source.json.
; Unresolved art bytes are consciously preserved, not decoded.
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
SecondaryRecordDirectory:
    dw $AFBF, $AFD5, $AFEB, $B001, $B017, $B02D, $B043, $B059
    dw $B06F, $B085, $B09B, $B0B1, $B0C7, $B0DD, $B0F3, $B109
    dw $B11F, $B135, $B14B, $B161, $B177, $B18D, $B1A3, $B1B9
    dw $B1CF, $B1E5, $B1FB, $B211, $B227, $B23D, $B253, $B269
    dw $B27F, $B295, $B2AB, $B2C1, $B2D7, $B2ED, $B303, $B319
    dw $B32F, $B345, $B35B, $B371, $B387, $B39D, $B3B3, $B3C9
    dw $B3DF, $B3F5, $B40B, $B421, $B437, $B44D, $B463, $B479
    dw $B48F, $B4A5, $B4BB, $B4D1, $B4E7, $B4FD, $B513, $B529
UnrolledGraphicsUploader:
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    outi
    out ($BE),a
    out ($BE),a
    out ($BE),a
    ret
GridGraphicsEngine:
    ld a,($C198)
    or a
    ret z
    xor a
    ld ($C040),a
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
    ld hl,$C199
    cp (hl)
    ret z
    or $80
    ld (hl),a
    ex af,af'
    ld a,c
    sub $30
    ld d,a
    ld a,($C019)
    jr nc,$86F5
    add a,d
    jp $86F8
    add a,d
    jr c,$86FC
    cp $E0
    jr c,$86FE
    sub $E0
    and $F8
    ld de,$D600
    ld l,a
    ld h,e
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,de
    ld a,b
    sub $20
    ld d,a
    ld a,($C182)
    add a,d
    and $F8
    rrca
    rrca
    or l
    ld l,a
    inc l
    ld de,$0040
    exx
    ld h,$81
    ex af,af'
    add a,a
    ld l,a
    ld e,(hl)
    inc l
    ld d,(hl)
    ld hl,$C040
    exx
    push hl
    ld b,$0B
    push hl
    exx
    ld a,(de)
    inc de
    exx
    rrca
    call $87E5
    exx
    ld a,(de)
    inc de
    exx
    rlca
    ld c,a
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    rl c
    call $87E5
    pop hl
    add hl,de
    ld a,h
    cp $DD
    jr c,$8769
    ld h,$D6
    djnz $872B
    pop hl
    ld a,($C11E)
    or a
    jr z,$87A9
    cp $02
    jr c,$87B8
    jr z,$8780
    ld a,l
    rlca
    rlca
    add a,$F8
    jp $8785
    ld a,l
    rlca
    rlca
    add a,$48
    rrca
    rrca
    ld l,a
    ld b,$0B
    bit 5,(hl)
    jr z,$879A
    res 5,(hl)
    ld a,l
    exx
    ld (hl),a
    inc hl
    exx
    ld a,h
    exx
    ld (hl),a
    inc hl
    exx
    add hl,de
    ld a,h
    cp $DD
    jr c,$87A2
    ld h,$D6
    djnz $878A
    exx
    ld (hl),$00
    exx
    ret
    ld de,$02C0
    add hl,de
    ld a,h
    cp $DD
    jr c,$87C4
    sub $07
    ld h,a
    jp $87C4
    ld de,$FFC0
    add hl,de
    ld a,h
    cp $D6
    jr nc,$87C4
    add a,$07
    ld h,a
    ld b,$09
    bit 5,(hl)
    jr z,$87D6
    res 5,(hl)
    ld a,l
    exx
    ld (hl),a
    inc hl
    exx
    ld a,h
    exx
    ld (hl),a
    inc hl
    exx
    ld a,l
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld l,a
    djnz $87C6
    exx
    ld (hl),$00
    exx
    ret
    jr nc,$8800
    bit 5,(hl)
    jr nz,$87F7
    set 5,(hl)
    ld a,l
    exx
    ld (hl),a
    inc hl
    exx
    ld a,h
    exx
    ld (hl),a
    inc hl
    exx
    ld a,l
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld l,a
    ret
    bit 5,(hl)
    jr z,$8810
    res 5,(hl)
    ld a,l
    exx
    ld (hl),a
    inc hl
    exx
    ld a,h
    exx
    ld (hl),a
    inc hl
    exx
    ld a,l
    rlca
    rlca
    add a,$08
    rrca
    rrca
    ld l,a
    ret
    call $8856
    ld hl,$C040
    ld bc,$A2BF
    ld e,(hl)
    bit 0,e
    ret z
    inc l
    ld d,(hl)
    inc l
    ld a,(de)
    and $20
    jr z,$8840
    dec e
    out (c),e
    ld a,b
    add a,d
    out ($BF),a
    ld a,(de)
    inc de
    out ($BE),a
    ld a,(de)
    ld e,(hl)
    out ($BE),a
    jp $8823
    dec e
    out (c),e
    ld a,b
    add a,d
    out ($BF),a
    ld e,(hl)
    ld a,$E7
    out ($BE),a
    ld a,$18
    bit 0,e
    out ($BE),a
    jp nz,$8826
    ret
    ld hl,$C199
    ld a,(hl)
    res 7,(hl)
    add a,a
    ret nc
    add a,a
    ld l,a
    ld h,$80
    ld a,$20
    out ($BF),a
    ld a,$74
    out ($BF),a
    ld c,$BE
    ld e,(hl)
    inc l
    ld d,(hl)
    inc l
    ld a,(hl)
    inc l
    ld h,(hl)
    ld l,a
    xor a
    push de
    ret
PixelRecords:
    db $E0, $FF, $FF, $FF, $FF, $FF, $FF, $E0, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $0F
    db $FF, $7E, $7E, $7C, $7C, $78, $78, $78, $3C, $3C, $3C, $7E, $7E, $7E, $7E, $FF
    db $FE, $7E, $7E, $3E, $3E, $1E, $1F, $1F, $FF, $FF, $FF, $FF, $7E, $7E, $7E, $7E
    db $7F, $7E, $7E, $7E, $7E, $7E, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $FE, $FE
    db $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $0F, $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $7F, $3F, $1F, $0F, $07, $07, $03
    db $FF, $FF, $FF, $FF, $3F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FE, $F8, $E0, $80
    db $FF, $FC, $F8, $F0, $E0, $C0, $80, $80, $03, $07, $1F, $7F, $FF, $FF, $FF, $C0
    db $C0, $F0, $FC, $FF, $FF, $FF, $1F, $01, $01, $1F, $FF, $FF, $FF, $FC, $F0, $C0
    db $C0, $FF, $FF, $FF, $7F, $1F, $07, $03, $7C, $7C, $7C, $7C, $7E, $7E, $FE, $FF
    db $FF, $7E, $7E, $7C, $7C, $78, $78, $78, $FF, $FF, $FF, $FF, $7E, $7E, $7E, $7E
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FF, $FF, $FF, $FF, $FE, $FC, $FC
    db $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF
    db $03, $07, $0F, $0F, $1F, $3F, $7F, $FF, $0F, $0F, $1F, $1F, $3F, $3F, $7F, $FF
    db $3F, $3F, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $3F, $3F, $1F, $1F, $1F
    db $FF, $7F, $3F, $1F, $1F, $0F, $07, $07, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F
    db $80, $E0, $F8, $FF, $FF, $FF, $FF, $80, $80, $FF, $FF, $FF, $FF, $FC, $E0, $80
    db $03, $3F, $FF, $FF, $FF, $FF, $3F, $03, $7F, $7E, $7E, $7C, $7C, $78, $F8, $F8
    db $F0, $70, $78, $78, $7C, $7C, $7E, $7F, $FF, $FF, $FE, $FC, $F0, $E0, $C0, $80
    db $FF, $FF, $FF, $FE, $FE, $FC, $F8, $F8, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE
    db $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $FC, $FC, $FC, $FE, $FE, $FE, $FF, $FF, $F8, $FC, $FE, $FE, $FF, $FF, $FF, $FF
    db $80, $C0, $E0, $F0, $FC, $FE, $FF, $FF, $01, $07, $0F, $3F, $FF, $FF, $FF, $FF
    db $03, $07, $0F, $0F, $1F, $3F, $7F, $FF, $0F, $0F, $1F, $1F, $3F, $3F, $7F, $FF
    db $3F, $3F, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F
    db $FF, $7F, $7F, $3F, $3F, $1F, $1F, $1F, $FF, $7F, $3F, $1F, $1F, $0F, $07, $07
    db $FF, $FF, $FF, $FF, $3F, $0F, $07, $01, $C0, $F0, $FF, $FF, $FF, $FF, $F0, $C0
    db $01, $07, $7F, $FF, $FF, $7F, $07, $01, $FF, $7E, $7E, $7C, $7C, $78, $78, $78
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80
    db $FF, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE
    db $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $FC, $FC, $FC, $FE, $FE, $FE, $FE, $FF, $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF
    db $F0, $F8, $FC, $FC, $FE, $FF, $FF, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $1F, $1F, $3F, $7F, $FF, $FF
    db $0F, $0F, $1F, $1F, $3F, $3F, $7F, $FF, $3F, $3F, $3F, $7F, $7F, $7F, $7F, $FF
    db $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F
    db $FF, $7F, $7F, $3F, $3F, $1F, $1F, $1F, $FF, $7F, $3F, $1F, $1F, $0F, $07, $07
    db $03, $0F, $FF, $FF, $FF, $FF, $0F, $03, $80, $E0, $FE, $FF, $FF, $FE, $E0, $80
    db $FF, $7E, $7E, $3E, $3E, $1E, $1E, $1E, $1E, $1E, $1E, $3E, $3E, $7E, $7F, $FF
    db $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80, $FF, $FE, $FC, $F8, $F8, $F0, $E0, $E0
    db $FF, $FE, $FE, $FC, $FC, $F8, $F8, $F8, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE
    db $FC, $FC, $FC, $FE, $FE, $FE, $FE, $FF, $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF
    db $E0, $F0, $F8, $F8, $FC, $FE, $FF, $FF, $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF
    db $FF, $FF, $FF, $3F, $1F, $07, $03, $01, $01, $03, $07, $1F, $3F, $FF, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $7F, $7F
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F
    db $01, $07, $1F, $FF, $FF, $FF, $FC, $C0, $01, $FF, $FF, $FF, $FF, $FF, $FF, $01
    db $C0, $FC, $FF, $FF, $FF, $1F, $07, $01, $FF, $7E, $7E, $3E, $3E, $1E, $1E, $1E
    db $1E, $1E, $1E, $3E, $3E, $7E, $7F, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $E0, $80
    db $FF, $FE, $FC, $F8, $F8, $F0, $E0, $E0, $FF, $FE, $FE, $FC, $FC, $F8, $F8, $F8
    db $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC, $FE, $FE, $FE, $FE, $FF
    db $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $C0, $E0, $F0, $F0, $F8, $FC, $FE, $FF
    db $80, $E0, $F0, $FC, $FF, $FF, $FF, $FF, $0F, $3F, $7F, $FF, $FF, $FF, $FF, $FF
    db $03, $07, $0F, $0F, $1F, $3F, $7F, $FF, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $7F, $7F
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $3F, $1F, $1F
    db $FF, $FF, $7F, $3F, $0F, $07, $03, $01, $C0, $E0, $F8, $FE, $FF, $FF, $FF, $03
    db $03, $0F, $3F, $FF, $FF, $FF, $F8, $80, $80, $F8, $FF, $FF, $FF, $3F, $0F, $03
    db $03, $FF, $FF, $FF, $FE, $F8, $E0, $C0, $FF, $7E, $7E, $3E, $3E, $1E, $1E, $1E
    db $FF, $FF, $FF, $FF, $7E, $7E, $7E, $7E, $3E, $3E, $3E, $7E, $7E, $7E, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0, $80, $80
    db $FF, $FE, $FE, $FC, $FC, $F8, $F8, $F8, $FC, $FC, $FC, $FE, $FE, $FE, $FE, $FF
    db $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $80, $C0, $E0, $E0, $F0, $F8, $FC, $FE
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $3F, $7F, $FF, $FF, $FF, $FF, $FF, $FF
    db $0F, $0F, $1F, $1F, $3F, $3F, $7F, $FF, $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF
    db $FF, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $7F, $3F, $3F
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $80, $C0, $F0, $FC, $FF, $FF, $FF, $F0
    db $01, $07, $1F, $7F, $FF, $FF, $FF, $07, $F0, $FF, $FF, $FF, $FC, $F0, $C0, $80
    db $07, $FF, $FF, $FF, $7F, $1F, $07, $01, $FF, $FE, $FE, $7E, $7E, $7E, $7E, $3E
    db $3E, $3E, $7E, $7E, $7E, $7E, $FF, $FF, $FF, $FF, $FF, $FF, $7E, $7E, $7E, $7E
    db $7C, $7C, $7C, $7E, $7E, $FE, $FE, $FF, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FE, $FE, $FC, $FC, $F8, $F8, $F8, $F0, $F0, $F8, $F8, $FC, $FC, $FE, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $01, $01, $03, $07, $0F, $1F, $3F, $FF
    db $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F
    db $FF, $3F, $1F, $0F, $07, $03, $01, $01, $FE, $FE, $7E, $7E, $3E, $3F, $3F, $1F
    db $3F, $3F, $7F, $7E, $7E, $7E, $FE, $FE, $FC, $FC, $FE, $7E, $7E, $7E, $7F, $7F
    db $7F, $7F, $7E, $7E, $7C, $FC, $FC, $F8, $E0, $FF, $FF, $FF, $FE, $F8, $E0, $80
    db $0F, $FF, $FF, $FF, $3F, $0F, $03, $01, $FF, $FC, $F8, $F0, $E0, $C0, $80, $80
    db $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FC, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F
    db $FF, $7F, $3F, $1F, $0F, $07, $07, $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $E0, $3F, $3F, $7F, $7E, $7E, $7E, $FE, $FE
    db $FC, $FC, $FC, $7C, $7E, $7E, $7E, $7F, $7F, $7F, $7E, $7E, $7C, $FC, $FC, $F8
    db $C0, $FF, $FF, $FF, $7F, $1F, $07, $03, $01, $1F, $FF, $FF, $FF, $FC, $F0, $C0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FF, $FF, $FF, $FE, $FC, $FC, $F8
    db $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF, $C0, $F0, $FC, $FF, $FF, $FF, $FF, $FF
    db $03, $07, $1F, $7F, $FF, $FF, $FF, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $3F
    db $FF, $FF, $FF, $FF, $FF, $FF, $1F, $01, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $C0
    db $C0, $F0, $FF, $FF, $FF, $F8, $E0, $80, $FF, $FF, $FE, $7E, $7C, $7C, $7C, $78
    db $FF, $FF, $FE, $FC, $F0, $E0, $C0, $80, $FF, $FF, $FE, $FE, $FC, $F8, $F8, $F0
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $F8, $FC, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $1F, $7F, $FF, $FF, $FF
    db $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $3F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $3F, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $FF, $FF, $FF, $FF, $3F, $0F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $3F, $03, $C0, $F0, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE
    db $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF
    db $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $FC, $FC, $FE, $FF, $FF, $FF, $FF, $FF
    db $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $0F, $1F, $1F, $3F, $7F, $FF, $FF, $FF
    db $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $3F, $3F, $7F, $7F, $7F, $7F, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F
    db $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $80, $E0, $FE, $FF, $FF, $FF, $3F, $0F, $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $F0, $F8, $FE, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $1F, $3F, $FF, $FF, $FF, $3F, $3F, $7F, $FF, $FF, $FF, $FF, $FF
    db $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $3F, $3F, $7F, $7F, $7F, $7F, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F
    db $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $FF, $7F, $1F, $0F, $07, $01, $FF, $FF, $FF, $3F, $0F, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $E0, $F0, $FC, $FF, $FF, $FF, $FF, $FF
    db $C0, $FC, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $1F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $3F, $7F, $FF, $FF, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $FF
    db $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F
    db $FF, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $FF, $FF, $FF, $FF, $7F, $3F, $1F, $0F
    db $FF, $7F, $7F, $7E, $3E, $3E, $3E, $3E, $3E, $3E, $3E, $3E, $7E, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8
    db $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $C0, $E0, $F8, $FE, $FF, $FF, $FF, $FF
    db $80, $F8, $FF, $FF, $FF, $FF, $FF, $FF, $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $3F, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $1F, $7F, $FF, $FF
    db $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $7F, $1F, $0F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $F0, $FF, $FF, $FF, $FC, $F0, $C0, $80
    db $07, $FF, $FF, $FF, $FF, $3F, $0F, $03, $06, $06, $0E, $1E, $3E, $7F, $FF, $FF
    db $FF, $FF, $7F, $7E, $3E, $3E, $3E, $1E, $3C, $3C, $7E, $7E, $7E, $7E, $FF, $FF
    db $FF, $FF, $FE, $7E, $7C, $7C, $7C, $78, $40, $60, $60, $70, $78, $FC, $FE, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FE, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $3F, $1F, $0F, $07, $03, $01, $01, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $80, $C0, $F0, $FC, $FF, $FF, $FF, $FF, $01, $07, $1F, $7F, $FF, $FF, $FF, $FF
    db $0F, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $3F
    db $FF, $FF, $FE, $FE, $FE, $FE, $7E, $3C, $FE, $7E, $7E, $3E, $3F, $3F, $1F, $1F
    db $3C, $7E, $7E, $7E, $7E, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7E, $3C
    db $7F, $7E, $7E, $7C, $FC, $FC, $F8, $F8, $FF, $FF, $FF, $FF, $FF, $FF, $FE, $E0
    db $FF, $FF, $FF, $FF, $FC, $F0, $E0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0
    db $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $80, $80, $C0, $E0, $F0, $F8, $FC, $FF
    db $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF, $E0, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $3F, $FF, $FF, $FF, $FF
    db $03, $07, $07, $0F, $1F, $3F, $7F, $FF, $1F, $1F, $3F, $3F, $7F, $FF, $FF, $FF
    db $FF, $7F, $7F, $3F, $1F, $1F, $0F, $07, $FF, $FF, $FF, $FF, $3F, $0F, $07, $01
    db $FF, $FE, $7E, $7C, $7C, $7C, $78, $38, $7C, $7E, $7E, $7E, $FE, $FF, $FF, $FF
    db $C0, $FF, $FF, $FF, $7F, $1F, $07, $03, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $C0
    db $FF, $FF, $FF, $FE, $F8, $F0, $E0, $C0, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0
    db $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF
    db $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $C0, $E0, $F0, $F8, $FC, $FF, $FF, $FF
    db $C0, $F0, $FC, $FF, $FF, $FF, $FF, $FF, $01, $1F, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $07, $1F, $7F, $FF, $FF, $FF, $FF, $07, $07, $0F, $1F, $3F, $7F, $FF, $FF
    db $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $7F, $7F, $3F, $3F, $3F, $1F, $1F, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $07
    db $FF, $FF, $FF, $FF, $FF, $7F, $3F, $1F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $07
    db $7F, $7E, $7E, $7C, $FC, $F8, $F8, $F8, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0
    db $FF, $FF, $FF, $FF, $FC, $F0, $E0, $80, $FF, $FE, $FC, $F8, $F8, $F0, $E0, $E0
    db $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF
    db $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF
    db $FC, $FC, $FE, $FF, $FF, $FF, $FF, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF, $03, $3F, $FF, $FF, $FF, $FF, $FF, $FF
    db $0F, $3F, $FF, $FF, $FF, $FF, $FF, $FF, $01, $01, $03, $07, $0F, $1F, $3F, $FF
    db $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $1F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $FF, $7F, $1F, $0F, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $7F, $07, $01, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0
    db $FF, $FE, $FE, $FC, $FC, $FC, $F8, $F8, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC
    db $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $FC, $FC, $FE, $FF, $FF, $FF, $FF, $FF
    db $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $1F, $7F, $FF, $FF, $FF
    db $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F
    db $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $F8, $F8, $FC, $FE, $FE, $FF, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $F8, $FE, $FF, $FF, $FF, $FF, $FF, $FF
    db $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF
    db $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F, $FF, $7F, $7F, $3F, $3F, $3F, $1F, $1F
    db $FF, $7F, $7F, $3F, $1F, $1F, $0F, $07, $FF, $FF, $FF, $3F, $1F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $FE, $7E, $7E, $3E, $3F, $3F, $1F, $1F
    db $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0, $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FE, $FE, $FC, $FC, $FC, $F8, $F8
    db $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $80, $80, $C0, $E0, $F0, $F8, $FC, $FF
    db $E0, $F8, $FE, $FF, $FF, $FF, $FF, $FF, $80, $F8, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $03, $0F, $3F, $FF, $FF, $FF, $FF, $FF
    db $01, $01, $03, $07, $0F, $1F, $3F, $FF, $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF
    db $3F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $07
    db $FF, $FF, $3F, $1F, $07, $03, $01, $00, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $3E, $7E, $7E, $7E, $7E, $FF, $FF, $FF, $FF, $7F, $7F, $3E, $3E, $3E, $1E, $1E
    db $FF, $FF, $FF, $FF, $FF, $FF, $F8, $80, $FF, $FF, $FF, $FF, $FE, $F8, $E0, $C0
    db $FF, $FE, $FC, $F8, $F8, $F0, $E0, $E0, $FF, $FF, $FE, $FE, $FC, $FC, $FC, $F8
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $03, $07, $0F, $1F, $3F, $FF, $FF, $FF
    db $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FE, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F, $FF, $FF, $FF, $7F, $3F, $3F, $1F, $0F
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $3F, $0F, $03
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $03, $F0, $FF, $FF, $FF, $FC, $F0, $C0, $80
    db $7F, $7E, $7E, $7C, $FC, $FC, $F8, $F8, $FC, $FE, $FE, $7E, $7E, $7F, $7F, $7F
    db $3F, $7F, $7E, $7E, $7E, $FE, $FE, $FC, $FE, $7E, $7E, $3E, $3F, $3F, $1F, $1F
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FF, $FF, $FF, $FF, $FE, $FC, $F8, $F8, $FC, $FC, $FE, $FF, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $80, $C0, $F0, $FC, $FF, $FF, $FF, $FF
    db $07, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $1F, $7F, $FF, $FF, $FF, $FF
    db $01, $01, $03, $07, $0F, $1F, $3F, $FF, $0F, $0F, $1F, $1F, $3F, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $7F, $7F, $3F, $1F, $FF, $3F, $1F, $0F, $07, $03, $01, $01
    db $FF, $FF, $FF, $FF, $7F, $1F, $07, $01, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07
    db $FE, $FE, $7E, $7F, $7F, $3F, $3F, $3F, $3F, $3E, $3E, $3E, $7E, $7E, $7C, $FC
    db $FC, $7C, $7C, $7C, $7E, $7E, $3E, $3F, $7F, $7F, $7E, $FE, $FE, $FC, $FC, $FC
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $E0, $FF, $FF, $FF, $FF, $FE, $F8, $E0, $80
    db $FF, $FF, $FF, $FC, $F8, $F0, $E0, $C0, $FF, $FF, $FE, $FC, $FC, $F8, $F0, $F0
    db $F0, $F8, $F8, $FC, $FE, $FE, $FF, $FF, $80, $80, $C0, $E0, $F0, $F8, $FC, $FF
    db $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF, $E0, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $3F, $FF, $FF, $FF, $FF
    db $03, $07, $07, $0F, $1F, $3F, $7F, $FF, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $7F, $3F, $3F, $FF, $7F, $3F, $1F, $0F, $07, $07, $03
    db $FF, $FF, $FF, $FF, $3F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F
    db $01, $1F, $FF, $FF, $FF, $FF, $FF, $C0, $C0, $FF, $FF, $FF, $FF, $FF, $1F, $01
    db $7F, $FF, $FF, $FF, $7F, $1F, $07, $03, $FF, $FF, $FF, $FF, $7F, $3F, $1F, $0F
    db $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $FF, $FF, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $7E, $7E, $7E, $7C, $7C, $3C, $3C, $7C, $7C, $7C, $FC, $FE, $FE, $FE, $FF
    db $3F, $3F, $3F, $3F, $7F, $7F, $7F, $FF, $3F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $07, $07, $0F, $1F, $1F, $3F, $7F, $FF, $03, $07, $1F, $7F, $FF, $FF, $FF, $FF
    db $C0, $F0, $FC, $FF, $FF, $FF, $FF, $FF, $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF
    db $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FE, $FE, $FE, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $C0
    db $FF, $7F, $7E, $7E, $7E, $7C, $3C, $3C, $7C, $7C, $7C, $FC, $FE, $FE, $FE, $FF
    db $FF, $FF, $FF, $FF, $FF, $F8, $E0, $80, $FF, $FF, $FE, $FC, $F0, $E0, $C0, $80
    db $FF, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $FF, $FE, $FE, $FE, $FE, $FE, $FC, $FC
    db $FE, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $00, $01, $03, $07, $0F, $1F, $7F, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $3F, $3F, $3F, $3F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $FF, $FF, $FF, $3F, $1F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $3F, $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $80
    db $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0, $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80
    db $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0, $FF, $FE, $FE, $FC, $FC, $FC, $F8, $F8
    db $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FC, $FE, $FE, $FE, $F0, $F0, $F8, $F8, $FC, $FE, $FE, $FF
    db $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $1F, $7F, $FF, $FF, $FF
    db $3F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF
    db $3F, $3F, $3F, $3F, $7F, $7F, $7F, $FF, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $FF, $7F, $7F, $7F, $7F, $7F, $3F, $3F, $FF, $FF, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $FF, $FF, $FF, $7F, $1F, $0F, $07, $03
    db $FF, $FF, $FF, $FF, $FF, $7F, $07, $01, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0
    db $FF, $FE, $FE, $FC, $FC, $FC, $F8, $F8, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FC
    db $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF, $80, $C0, $E0, $F0, $FC, $FE, $FF, $FF
    db $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $3F, $3F, $3F, $3F, $7F, $7F, $7F, $FF, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $FF, $7F, $7F, $7F, $7F, $7F, $3F, $3F, $FF, $FF, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F
    db $FF, $FF, $FF, $3F, $1F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03
    db $FF, $FF, $7F, $7F, $7F, $3E, $3E, $3E, $3C, $3C, $3E, $3E, $7E, $7E, $7E, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $FF, $FF, $FF, $FF, $FC, $F8, $E0, $C0
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FE, $FE, $FE, $FC, $FC, $FC, $FC
    db $FC, $FC, $FC, $FE, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $03, $07, $0F, $1F, $7F, $FF, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF
    db $FF, $7F, $7F, $7F, $7F, $7F, $3F, $3F, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F
    db $FF, $FF, $FF, $3F, $1F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03
    db $FF, $FE, $7E, $7E, $7E, $3E, $3C, $3C, $3E, $3E, $3E, $3F, $7F, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80
    db $FF, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $FF, $FF, $FE, $FE, $FE, $FC, $FC, $FC
    db $FC, $FC, $FC, $FC, $FE, $FE, $FE, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $FF, $FF, $7F, $1F, $0F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $7F, $7F, $7E, $FE, $FE, $FC, $FC, $FC
    db $FC, $7C, $7C, $7C, $7E, $7E, $3E, $3F, $FF, $FE, $7E, $7E, $7E, $3E, $3C, $3C
    db $3E, $3E, $3E, $3F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0
    db $FF, $FF, $FF, $FF, $FC, $F0, $C0, $80, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FF, $FF, $FF, $FE, $FC, $FC, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $C0, $E0, $F0, $F8, $FC, $FE, $FF, $FF, $80, $C0, $F0, $FC, $FF, $FF, $FF, $FF
    db $F0, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $1F, $7F, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $1F, $3F, $FF, $FF
    db $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F
    db $FF, $FF, $FF, $3F, $1F, $0F, $07, $03, $FF, $FF, $FF, $FF, $7F, $1F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $3F, $3F, $3F, $7F, $7F, $7E, $FE, $FE
    db $FC, $7C, $7E, $7E, $3E, $3E, $3E, $3F, $3C, $3C, $7C, $7E, $7E, $7E, $7F, $FF
    db $FF, $FE, $FE, $FE, $FC, $7C, $7C, $7C, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $E0
    db $FF, $FF, $FF, $FF, $FE, $F8, $E0, $80, $FF, $FC, $F8, $F0, $E0, $C0, $80, $80
    db $FF, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF
    db $E0, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $07, $0F, $1F, $3F, $7F, $FF, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $7F, $3F, $1F, $0F, $07, $03, $FF, $FF, $FF, $FF, $3F, $0F, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $FF, $FE, $FE, $FE, $FC, $7C, $7C, $7C
    db $3C, $3C, $7C, $7E, $7E, $7E, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF
    db $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF, $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF
    db $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $3F, $3F, $3F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $3F, $3F, $3F, $3F
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $FF, $3F, $1F, $07, $03, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $FF, $FE, $FE, $FE, $FC, $7C, $7C, $7C, $3C, $3C, $7C, $7E, $7E, $7E, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0, $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FE
    db $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF
    db $80, $C0, $E0, $F8, $FC, $FE, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $07, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $1F, $3F, $FF, $FF, $FF
    db $07, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $3F, $3F, $3F, $7F, $7F, $7F, $FF, $FF
    db $FF, $7F, $7F, $7F, $3F, $3F, $3F, $3F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $3F
    db $FF, $FF, $FF, $FF, $FF, $FF, $7F, $07, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FE, $FE, $FE, $FC, $FC, $FC, $FC, $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FE
    db $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $F8, $F8, $F8, $FC, $FC, $FE, $FE, $FF
    db $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF
    db $3F, $3F, $3F, $7F, $7F, $7F, $FF, $FF, $3F, $3F, $7F, $7F, $7F, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $FF, $7F, $7F, $7F, $3F, $3F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $3F
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FE
    db $FF, $FF, $FE, $FC, $F0, $E0, $C0, $80, $FF, $FF, $FE, $FC, $FC, $F8, $F0, $F0
    db $FF, $FE, $FE, $FE, $FC, $FC, $FC, $FC, $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FE
    db $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FC, $FC, $FC, $FE, $FE, $FE, $FF, $FF
    db $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF, $80, $C0, $E0, $F0, $FC, $FE, $FF, $FF
    db $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $3F, $7F, $FF, $FF, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF
    db $3F, $3F, $3F, $7F, $7F, $7F, $FF, $FF, $3F, $3F, $7F, $7F, $7F, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $FF, $7F, $7F, $7F, $3F, $3F, $3F, $3F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $7F, $1F, $0F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $FF, $7F, $7E, $7E, $3E, $3E, $3E, $3C
    db $3E, $3E, $3E, $7E, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $E0
    db $FF, $FE, $FE, $FC, $FC, $FC, $F8, $F8, $FC, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $FF
    db $C0, $FC, $FF, $FF, $FF, $FF, $FF, $FF, $01, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $1F, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $3F, $7F, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $3F, $3F, $7F, $7F, $7F, $7F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03
    db $FC, $7C, $7E, $7E, $3E, $3E, $3E, $3F, $3F, $3F, $3F, $7F, $7F, $7E, $FE, $FE
    db $FF, $FF, $FF, $FF, $FF, $FF, $F8, $80, $FF, $FF, $FF, $FF, $FE, $F8, $E0, $C0
    db $FF, $FF, $FF, $FE, $FC, $F8, $F0, $E0, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FE, $FE, $FE, $FC, $FC, $FC, $FC, $FC, $FC, $FC, $FE, $FE, $FE, $FF, $FF
    db $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF, $F0, $F8, $FC, $FE, $FF, $FF, $FF, $FF
    db $C0, $E0, $F8, $FE, $FF, $FF, $FF, $FF, $80, $F8, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $03, $0F, $3F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF
    db $3F, $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $7F, $1F, $0F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $FC, $FC, $FC, $FE, $FE, $7E, $7F, $7F
    db $3F, $3E, $7E, $7E, $7C, $7C, $7C, $FC, $3C, $3C, $3E, $7E, $7E, $7E, $FE, $FF
    db $FF, $7F, $7F, $7F, $3F, $3E, $3E, $3E, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0
    db $FF, $FF, $FF, $FF, $FC, $F0, $C0, $80, $FF, $FF, $FE, $FC, $F8, $F0, $E0, $C0
    db $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0, $FC, $FC, $FE, $FF, $FF, $FF, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $80, $C0, $F0, $FC, $FF, $FF, $FF, $FF
    db $F0, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $1F, $7F, $FF, $FF, $FF, $FF, $03, $07, $0F, $1F, $3F, $FF, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $FF, $7F, $7F, $3F, $1F, $1F, $0F
    db $FF, $3F, $1F, $0F, $07, $03, $01, $01, $FF, $FF, $FF, $FF, $7F, $1F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $F8, $F8, $7C, $7C, $7C, $7E, $7E, $7F
    db $7F, $7F, $7F, $7E, $7E, $7E, $7E, $FC, $7C, $7E, $7E, $7E, $FE, $FE, $FF, $FF
    db $FF, $7F, $7F, $7F, $7E, $3E, $3E, $3E, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $E0
    db $FF, $FF, $FF, $FF, $FE, $F8, $E0, $80, $FF, $FC, $F8, $F0, $E0, $C0, $80, $80
    db $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0, $F8, $FC, $FE, $FE, $FF, $FF, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $80, $E0, $F8, $FE, $FF, $FF, $FF, $FF
    db $E0, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $1F, $1F, $1F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F
    db $FF, $7F, $3F, $1F, $0F, $07, $07, $03, $FF, $FF, $FF, $FF, $3F, $0F, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $FF, $FF, $FF, $FE, $7E, $7E, $7E, $7C
    db $38, $78, $7C, $7C, $7C, $7E, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FF, $FC, $F8, $F0, $E0, $C0, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0
    db $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $E0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $1F, $3F, $FF, $FF, $FF, $07, $0F, $1F, $1F, $3F, $7F, $7F, $FF
    db $1F, $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F
    db $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F, $FF, $FF, $7F, $3F, $1F, $0F, $07, $07
    db $FF, $FF, $FF, $FF, $FF, $7F, $1F, $0F, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $F8, $F8, $FC, $FC, $7C, $7E, $7E, $7F, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FF, $FF, $FF, $FE, $F8, $FF, $FF, $FF, $FC, $F8, $F0, $E0, $C0
    db $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC
    db $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $E0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $1F, $1F, $3F, $3F, $3F, $7F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03
    db $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0, $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80
    db $FF, $FF, $FF, $FF, $FF, $FE, $FC, $FC, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FE
    db $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $F8, $F8, $FC, $FC, $FC, $FE, $FE, $FF
    db $E0, $F0, $F8, $F8, $FC, $FE, $FE, $FF, $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF
    db $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $1F, $3F, $FF, $FF, $FF, $07, $0F, $1F, $1F, $3F, $7F, $7F, $FF
    db $1F, $1F, $3F, $3F, $3F, $7F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $FF, $7F, $1F, $0F, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $7F, $07, $01, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FF, $FE, $FE, $FC, $F8, $F8, $F0
    db $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FE, $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $1F, $3F, $FF, $FF, $FF
    db $07, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $1F, $1F, $3F, $3F, $3F, $7F, $7F, $FF
    db $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F
    db $FF, $FF, $FF, $FF, $FF, $7F, $3F, $3F, $FF, $FF, $FF, $3F, $1F, $07, $03, $01
    db $1F, $1F, $3F, $3F, $3E, $7E, $7E, $FE, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF
    db $F8, $F8, $FC, $FC, $FC, $FE, $FE, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $1F, $3F, $FF, $FF, $FF
    db $07, $0F, $1F, $1F, $3F, $7F, $7F, $FF, $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F
    db $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F, $FF, $FF, $7F, $1F, $0F, $07, $03, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $FF, $FF, $FF, $FF, $FE, $FC, $F8, $F8
    db $1F, $1F, $3F, $3E, $3E, $7E, $7E, $FE, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FF, $FF, $FE, $F8, $F0, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC
    db $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF
    db $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF, $80, $E0, $F0, $FC, $FF, $FF, $FF, $FF
    db $80, $F8, $FF, $FF, $FF, $FF, $FF, $FF, $03, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $0F, $3F, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $1F, $7F, $FF, $FF
    db $0F, $1F, $3F, $3F, $7F, $FF, $FF, $FF, $3F, $7F, $7F, $7F, $7F, $7F, $FF, $FF
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F
    db $FF, $7F, $7F, $3F, $1F, $1F, $0F, $0F, $FF, $FF, $FF, $3F, $1F, $0F, $07, $03
    db $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03, $F8, $F8, $FC, $FC, $7C, $7E, $7E, $7F
    db $7F, $7F, $7F, $7E, $7E, $FE, $FE, $FC, $FC, $FE, $FE, $7E, $7E, $7E, $7F, $3F
    db $1F, $3F, $3F, $3F, $7E, $7E, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0
    db $FF, $FF, $FF, $FF, $FC, $F0, $C0, $80, $FF, $FE, $FC, $F8, $F0, $E0, $C0, $C0
    db $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0, $E0, $F0, $F8, $F8, $FC, $FE, $FE, $FF
    db $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $7F, $FF, $FF, $FF, $FF, $FF, $01, $03, $0F, $1F, $7F, $FF, $FF, $FF
    db $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F
    db $FF, $3F, $1F, $0F, $07, $03, $01, $01, $FF, $FF, $FF, $FF, $7F, $1F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $FF, $FF, $FE, $7C, $78, $70, $60, $60
    db $78, $7C, $7C, $7C, $7E, $FE, $FF, $FF, $FF, $FF, $7E, $7E, $7E, $7E, $3C, $3C
    db $1E, $3E, $3E, $3E, $7E, $7F, $FF, $FF, $01, $03, $0F, $3F, $FF, $FF, $FF, $E0
    db $80, $E0, $F8, $FE, $FF, $FF, $FF, $0F, $FF, $7F, $3F, $1E, $0E, $06, $06, $02
    db $FF, $FF, $FF, $FF, $FE, $F8, $E0, $80, $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0
    db $FC, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $80, $80, $C0, $E0, $F0, $F8, $FC, $FF
    db $E0, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $03, $07, $07, $0F, $1F, $3F, $7F, $FF, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $FF, $FF, $FF, $FF, $3F, $0F, $03, $01
    db $FF, $FF, $FF, $7E, $7E, $7E, $7E, $7C, $7C, $7C, $7C, $7C, $7E, $FE, $FE, $FF
    db $80, $C0, $F0, $FC, $FF, $FF, $FF, $C0, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $C0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FE, $FE, $FC, $F8, $F8, $F0, $F0
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $F8, $FC, $FC, $FE, $FF, $FF, $FF, $FF
    db $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $FF, $7F, $3F, $1F, $0F, $07, $07, $03
    db $FF, $FF, $FF, $FF, $7F, $1F, $07, $03, $FF, $FF, $FF, $FF, $FF, $FF, $1F, $01
    db $F8, $FC, $FC, $7C, $7E, $7E, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FF, $FF, $FF, $FF, $FC, $F8, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $F8, $FC, $FE, $FF, $FF, $FF, $FF, $FF
    db $80, $C0, $F0, $FC, $FF, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F, $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F
    db $FF, $FF, $7F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $FF, $FF, $3F, $0F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $3F, $03, $C0, $F0, $FF, $FF, $FF, $FF, $F0, $C0
    db $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80, $FF, $FF, $FF, $FF, $FE, $FC, $FC, $F8
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $01, $07, $7F, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $1F, $7F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $FF, $FF, $FF, $7F, $3F, $1F, $1F, $0F
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $FF, $FF, $FF, $FF, $FF, $7F, $07, $01
    db $03, $0F, $FF, $FF, $FF, $FF, $0F, $03, $FF, $FF, $FF, $FF, $FF, $FE, $E0, $80
    db $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80, $FF, $FF, $FF, $FE, $FC, $F8, $F8, $F0
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $1F, $3F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $1F, $3F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $FF, $FF, $FF, $FF, $7F, $3F, $3F, $1F
    db $FF, $FF, $FF, $3F, $1F, $07, $03, $01, $1F, $3F, $3F, $3E, $7E, $7E, $FE, $FE
    db $FF, $FF, $FF, $FF, $FF, $FF, $FC, $C0, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $E0
    db $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0, $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0
    db $FF, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF
    db $01, $07, $1F, $FF, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $3F, $7F, $FF, $FF
    db $0F, $1F, $1F, $3F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F
    db $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $FF, $7F, $3F, $1F, $0F, $07, $07, $03
    db $FF, $FF, $FF, $FF, $FF, $FF, $3F, $1F, $FF, $FF, $FF, $FF, $FF, $FF, $0F, $03
    db $7F, $7F, $7E, $7E, $7E, $FE, $FC, $FC, $FE, $7E, $7E, $7E, $3E, $3F, $3F, $3F
    db $1F, $3F, $3F, $3E, $7E, $7E, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $F8, $80
    db $FF, $FF, $FF, $FF, $FE, $F8, $E0, $C0, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF
    db $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $FF
    db $80, $E0, $FE, $FF, $FF, $FF, $FF, $FF, $03, $0F, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $07, $1F, $3F, $FF, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $FF, $FF, $FF, $FF, $FF, $3F, $0F, $03
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $03, $F8, $FC, $FC, $7C, $7E, $7E, $7F, $7F
    db $7F, $7F, $7E, $7E, $7E, $FE, $FC, $FC, $FE, $FE, $7E, $7E, $7E, $7F, $3F, $3F
    db $1F, $3F, $3F, $3E, $7E, $7E, $FE, $FE, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $F0
    db $FF, $FF, $FF, $FF, $FC, $F0, $C0, $80, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF
    db $C0, $E0, $F8, $FC, $FF, $FF, $FF, $FF, $C0, $F0, $FF, $FF, $FF, $FF, $FF, $FF
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F
    db $FF, $7F, $3F, $1F, $0F, $07, $07, $03, $FF, $FF, $FF, $FF, $7F, $1F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $07, $80, $E0, $F8, $FE, $FF, $FF, $FF, $E0
    db $01, $03, $0F, $3F, $FF, $FF, $FF, $0F, $E0, $FF, $FF, $FF, $FE, $F8, $E0, $80
    db $0F, $FF, $FF, $FF, $3F, $0F, $03, $01, $FF, $FF, $7E, $7E, $7C, $7C, $7C, $78
    db $7C, $7C, $7E, $7E, $7E, $7E, $7F, $FF, $7F, $7F, $7F, $7E, $FE, $FE, $FE, $FE
    db $FE, $7E, $7E, $7E, $7E, $3F, $3F, $3F, $FF, $FC, $F8, $F0, $E0, $C0, $80, $80
    db $FF, $FF, $FF, $FF, $FF, $FE, $FE, $FC, $F0, $F8, $F8, $FC, $FC, $FE, $FF, $FF
    db $80, $80, $C0, $E0, $F0, $F8, $FC, $FF, $03, $07, $07, $0F, $1F, $3F, $7F, $FF
    db $1F, $1F, $1F, $3F, $3F, $7F, $7F, $FF, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F
    db $FF, $7F, $3F, $1F, $0F, $07, $07, $03, $03, $0F, $FF, $FF, $FF, $FF, $1F, $01
    db $C0, $F0, $FD, $FF, $FF, $FF, $FF, $C0, $FF, $FE, $7E, $7E, $7C, $7C, $7C, $7C
    db $7C, $7C, $7C, $7C, $7E, $7E, $7E, $FF, $FF, $FF, $FF, $FF, $FF, $FC, $F0, $C0
    db $FF, $FF, $FE, $F8, $F0, $E0, $C0, $80, $FF, $FE, $FC, $FC, $F8, $F0, $F0, $E0
    db $FF, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $E0, $F0, $F8, $FE, $FF, $FF, $03, $07, $1F, $3F, $FF, $FF, $FF, $FF
    db $07, $07, $0F, $1F, $1F, $3F, $7F, $FF, $1F, $1F, $1F, $3F, $3F, $7F, $7F, $FF
    db $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F, $FF, $7F, $3F, $1F, $0F, $0F, $07, $03
    db $FF, $FF, $FF, $FF, $7F, $1F, $07, $03, $78, $78, $78, $7C, $7C, $7E, $7E, $FF
    db $03, $3F, $FF, $FF, $FF, $FF, $F0, $C0, $C0, $F0, $FF, $FF, $FF, $7F, $07, $01
    db $FF, $FF, $FF, $FF, $FF, $FC, $F8, $E0, $FF, $FE, $FC, $F8, $F0, $F0, $E0, $C0
    db $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC
    db $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF
    db $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF, $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF
    db $C0, $E0, $F8, $FC, $FF, $FF, $FF, $FF, $01, $07, $0F, $3F, $FF, $FF, $FF, $FF
    db $07, $07, $0F, $1F, $1F, $3F, $7F, $FF, $1F, $1F, $1F, $3F, $3F, $7F, $7F, $FF
    db $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F
    db $FF, $FF, $FF, $FF, $7F, $7F, $7F, $3F, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $FF, $7F, $1F, $0F, $03, $01, $C0, $F0, $FF, $FF, $FF, $FF, $F0, $C0
    db $01, $07, $7F, $FF, $FF, $7F, $07, $01, $FF, $FF, $FF, $FC, $F8, $E0, $C0, $80
    db $FF, $FF, $FF, $FE, $FC, $FC, $F8, $F0, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0
    db $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC, $FF, $FF, $FE, $FE, $FE, $FE, $FE, $FE
    db $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF
    db $F8, $F8, $F8, $FC, $FC, $FE, $FE, $FF, $F0, $F0, $F8, $FC, $FC, $FE, $FF, $FF
    db $80, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $01, $03, $0F, $1F, $7F, $FF, $FF, $FF
    db $07, $07, $0F, $1F, $1F, $3F, $7F, $FF, $1F, $1F, $1F, $3F, $3F, $7F, $7F, $FF
    db $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $FF
    db $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $3F, $3F, $3F, $1F
    db $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07, $FF, $FF, $FF, $7F, $1F, $0F, $03, $01
    db $80, $E0, $FE, $FF, $FF, $FE, $E0, $80, $03, $0F, $FF, $FF, $FF, $FF, $0F, $03
    db $1F, $1F, $1E, $3E, $3E, $7E, $7E, $FE, $FF, $FF, $FF, $FE, $F8, $F0, $C0, $80
    db $FF, $FF, $FE, $FC, $F8, $F8, $F0, $E0, $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0
    db $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC, $FE, $FE, $FE, $FE, $FE, $FF, $FF, $FF
    db $F8, $FC, $FC, $FC, $FE, $FE, $FF, $FF, $E0, $F0, $F0, $F8, $FC, $FC, $FE, $FF
    db $80, $C0, $F0, $F8, $FE, $FF, $FF, $FF, $01, $03, $07, $1F, $3F, $FF, $FF, $FF
    db $0F, $0F, $1F, $3F, $3F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $7F, $7F
    db $FF, $7F, $7F, $7F, $7F, $3F, $3F, $3F, $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F
    db $FF, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $FF, $FF, $FF, $3F, $1F, $07, $03, $01
    db $01, $07, $1F, $FF, $FF, $FF, $FF, $01, $C0, $FC, $FF, $FF, $FF, $FF, $FC, $C0
    db $01, $FF, $FF, $FF, $FF, $1F, $07, $01, $1F, $1F, $1E, $3E, $3E, $7E, $7E, $FE
    db $FF, $FF, $FF, $FF, $FC, $F0, $E0, $80, $FF, $FE, $FC, $F8, $F0, $F0, $E0, $C0
    db $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC
    db $FE, $FE, $FE, $FE, $FE, $FE, $FE, $FF, $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF
    db $F8, $F8, $F8, $FC, $FC, $FE, $FE, $FF, $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF
    db $80, $E0, $F0, $FC, $FF, $FF, $FF, $FF, $01, $03, $07, $0F, $3F, $7F, $FF, $FF
    db $1F, $1F, $3F, $7F, $7F, $FF, $FF, $FF, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF
    db $7F, $7F, $7F, $7F, $7F, $7F, $7F, $FF, $FF, $7F, $7F, $7F, $7F, $3F, $3F, $3F
    db $FF, $7F, $3F, $3F, $1F, $1F, $0F, $0F, $FF, $FF, $FF, $FF, $7F, $7F, $3F, $1F
    db $FF, $FF, $7F, $3F, $0F, $07, $03, $01, $03, $0F, $3F, $FF, $FF, $FF, $FF, $03
    db $C0, $F0, $FF, $FF, $FF, $FF, $F8, $80, $03, $FF, $FF, $FF, $FF, $3F, $0F, $03
    db $3F, $3F, $3E, $3E, $7E, $7E, $7E, $FE, $FE, $7E, $7E, $7E, $3E, $3E, $3E, $3F
    db $FF, $FF, $FF, $FF, $FE, $F8, $E0, $C0, $FF, $FE, $FC, $F8, $F8, $F0, $E0, $E0
    db $FF, $FF, $FE, $FE, $FC, $FC, $F8, $F8, $FF, $FE, $FE, $FE, $FE, $FC, $FC, $FC
    db $FE, $FE, $FE, $FE, $FF, $FF, $FF, $FF, $F8, $F8, $F8, $FC, $FC, $FE, $FE, $FF
    db $E0, $E0, $F0, $F8, $F8, $FC, $FE, $FF, $C0, $E0, $F8, $FC, $FF, $FF, $FF, $FF
    db $01, $03, $07, $0F, $1F, $7F, $FF, $FF, $07, $0F, $0F, $1F, $3F, $3F, $7F, $FF
    db $7F, $7F, $7F, $7F, $7F, $FF, $FF, $FF, $FF, $7F, $3F, $3F, $1F, $0F, $0F, $07
    db $FF, $FF, $7F, $1F, $0F, $07, $03, $01, $80, $C0, $F0, $FC, $FF, $FF, $FF, $F0
    db $03, $0F, $FF, $FF, $FF, $FF, $FF, $07, $78, $78, $78, $7C, $7C, $7E, $7E, $FF
    db $7E, $7E, $7E, $7E, $FF, $FF, $FF, $FF, $FF, $FE, $FE, $7E, $7E, $7C, $7C, $7C
    db $FF, $FF, $7E, $7E, $3E, $3E, $3E, $1E, $1E, $1E, $1E, $3E, $3E, $7E, $7E, $FF
    db $FF, $FF, $FF, $FF, $FC, $F0, $C0, $80, $FF, $FE, $FC, $F8, $F0, $E0, $E0, $C0
    db $FF, $FE, $FC, $FC, $F8, $F8, $F0, $F0, $C0, $E0, $E0, $F0, $F8, $FC, $FE, $FF
    db $03, $07, $1F, $3F, $FF, $FF, $FF, $FF, $07, $07, $0F, $1F, $1F, $3F, $7F, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $7F, $FF, $7F, $3F, $1F, $0F, $07, $07, $03
    db $FF, $FF, $FF, $FF, $7F, $1F, $07, $01
SecondaryGraphicsRecords:
    db $00, $FC, $00, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $00, $FE, $00, $FC, $00, $00, $00, $FC, $00, $FE, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FE, $01, $FE, $00, $FE, $00, $7C, $00, $00, $00, $7C, $00, $FE
    db $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE, $00, $7C
    db $00, $00, $00, $7C, $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FE, $00, $FE, $00, $7C, $00, $00, $00, $7C, $00, $FE, $00, $FF, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE, $00, $7C, $00, $00, $00, $7C
    db $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE
    db $00, $7C, $00, $00, $00, $7E, $00, $FE, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $00, $FF, $00, $FF, $00, $FE, $00, $7C, $00, $00, $00, $7E, $00, $FE, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FE, $00, $7E, $00, $00
    db $00, $FC, $00, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $00, $FE, $00, $FC, $00, $00, $00, $7C, $00, $FE, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FE, $01, $FE, $00, $FE, $00, $FC, $00, $00, $00, $7C, $00, $FE
    db $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE, $00, $7C
    db $00, $00, $00, $7C, $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FE, $00, $FE, $00, $7C, $00, $00, $00, $7C, $00, $FE, $00, $FF, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE, $00, $7C, $00, $00, $00, $7C
    db $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE
    db $00, $7C, $00, $00, $00, $7C, $00, $FE, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $00, $FF, $00, $FF, $00, $FE, $00, $7E, $00, $00, $00, $7E, $00, $FE, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FE, $00, $7E, $00, $00
    db $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $30, $00, $7C, $00, $FE, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FE, $01, $FE, $00, $FE, $00, $FC, $00, $30, $00, $7C, $00, $FE
    db $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE, $00, $FC
    db $00, $30, $00, $7C, $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FE, $00, $7C, $00, $30, $00, $7C, $00, $FE, $00, $FF, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FE, $00, $7C, $00, $18, $00, $7C
    db $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE
    db $00, $7E, $00, $18, $00, $7C, $00, $FE, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $00, $FF, $00, $FF, $00, $FE, $00, $7E, $00, $18, $00, $3C, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $18
    db $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $38, $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FC, $00, $38, $00, $7C, $00, $FE
    db $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE, $00, $FC
    db $00, $38, $00, $7C, $00, $FE, $00, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FE, $00, $FC, $00, $38, $00, $7C, $00, $FE, $00, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FE, $00, $7E, $00, $38, $00, $7C
    db $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE
    db $00, $7E, $00, $38, $00, $3C, $00, $7E, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $38, $00, $3C, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C
    db $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $78, $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FC, $00, $78, $00, $78, $00, $FE
    db $01, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE, $00, $FC
    db $00, $38, $00, $78, $00, $FE, $00, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FE, $00, $FE, $00, $38, $00, $3C, $00, $FE, $00, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FE, $00, $FE, $00, $38, $00, $3C
    db $00, $FE, $00, $FF, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE
    db $00, $7E, $00, $38, $00, $3C, $00, $7E, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C, $00, $3C, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C
    db $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $78, $00, $78, $00, $FC, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FC, $00, $78, $00, $38, $00, $FC
    db $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FE
    db $00, $78, $00, $38, $00, $FE, $00, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FE, $00, $FE, $00, $78, $00, $38, $00, $FE, $00, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FE, $00, $FE, $00, $3C, $00, $38
    db $00, $7E, $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FF
    db $00, $FE, $00, $3C, $00, $3C, $00, $7E, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C, $00, $3C, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C
    db $00, $38, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $78, $00, $38, $00, $FC, $01, $FE, $01, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FC, $00, $78, $00, $38, $00, $FC
    db $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE
    db $00, $7C, $00, $38, $00, $FC, $00, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FE, $00, $FE, $00, $7C, $00, $38, $00, $7E, $00, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FE, $00, $FE, $00, $7C, $00, $38
    db $00, $7E, $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF
    db $00, $FE, $00, $7C, $00, $38, $00, $7E, $00, $FF, $00, $FF, $01, $FF, $01, $FF
    db $01, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C, $00, $38, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C
    db $00, $30, $00, $FC, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE, $01, $FE
    db $01, $FE, $00, $FC, $00, $78, $00, $30, $00, $FC, $00, $FE, $01, $FE, $01, $FE
    db $01, $FF, $01, $FF, $01, $FE, $01, $FE, $00, $FE, $00, $7C, $00, $30, $00, $FC
    db $00, $FE, $01, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FE, $00, $FE
    db $00, $7C, $00, $30, $00, $7C, $00, $FE, $01, $FF, $01, $FF, $01, $FF, $01, $FF
    db $01, $FF, $01, $FE, $00, $FE, $00, $7C, $00, $18, $00, $7C, $00, $FE, $01, $FF
    db $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF, $00, $FE, $00, $7C, $00, $18
    db $00, $7E, $00, $FE, $00, $FF, $01, $FF, $01, $FF, $01, $FF, $01, $FF, $00, $FF
    db $00, $FE, $00, $7C, $00, $18, $00, $7E, $00, $FE, $00, $FF, $00, $FF, $01, $FF
    db $01, $FF, $00, $FF, $00, $FF, $00, $FE, $00, $7C, $00, $18, $00, $7E, $00, $FF
    db $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $7E, $00, $3C
MapInitialization:
    ld hl,$D600
    ld bc,$0380
    ld a,(hl)
    cp $1C
    jr nc,$B550
    cp $12
    jr z,$B550
    ld (hl),$00
    inc hl
    inc hl
    dec bc
    ld a,b
    or c
    jr nz,$B545
    ld hl,$C600
    ld a,$E4
    ld b,$1F
    or $C0
    ld (hl),a
    inc hl
    add a,$02
    ld (hl),$7A
    inc hl
    djnz $B55E
    ld de,$7D20
    ld b,$13
    ld (hl),e
    inc hl
    ld (hl),d
    inc hl
    ld a,e
    add a,$40
    ld e,a
    jr nc,$B579
    inc d
    ld a,d
    cp $7F
    jr nz,$B580
    ld d,$78
    djnz $B56E
    ld hl,$D800
    ld bc,$0B4C
    call $B590
    ld hl,$D82E
    ld b,$09
    ld (hl),c
    inc hl
    inc hl
    djnz $B590
    ret
UnresolvedVisualData:
    db $91, $00, $03, $05, $05, $87, $11, $8B, $7F, $00, $C0, $E0, $E0, $E1, $89, $71
    db $FE, $1F, $03, $3F, $03, $7F, $82, $FF, $F8, $03, $FC, $02, $FE, $02, $FF, $02
    db $1F, $04, $3F, $83, $7F, $FF, $F8, $03, $FC, $02, $FE, $02, $FF, $91, $00, $03
    db $25, $85, $8E, $8B, $47, $3F, $00, $C0, $E4, $E1, $71, $D1, $E2, $FC, $1F, $03
    db $3F, $03, $7F, $83, $FF, $F8, $BC, $02, $FC, $02, $FE, $02, $FF, $02, $1F, $04
    db $3F, $84, $7F, $FF, $F8, $BC, $02, $FC, $02, $FE, $02, $FF, $90, $00, $01, $03
    db $05, $05, $07, $0F, $3E, $00, $A0, $90, $90, $80, $90, $30, $70, $02, $3F, $04
    db $1F, $83, $7F, $FF, $F8, $03, $FC, $03, $FE, $81, $FF, $02, $3F, $02, $1F, $02
    db $3F, $02, $FF, $02, $F8, $03, $FC, $02, $FE, $8C, $FF, $00, $06, $4E, $8C, $8C
    db $EC, $FE, $DF, $00, $40, $3C, $03, $3E, $CD, $1A, $FA, $DF, $7D, $3F, $30, $21
    db $21, $7F, $E1, $12, $D6, $FE, $1C, $F0, $F0, $FC, $FE, $00, $06, $4E, $8C, $8C
    db $EC, $FE, $DF, $DF, $DD, $FF, $70, $1F, $1F, $7F, $FF, $12, $DC, $F8, $08, $88
    db $88, $FE, $8F, $01, $03, $3F, $7F, $7C, $4F, $7F, $5F, $00, $20, $12, $11, $11
    db $1B, $1F, $39, $53, $53, $33, $1D, $30, $30, $FF, $70, $E5, $E5, $E6, $FC, $FC
    db $F8, $FF, $FE, $53, $53, $33, $03, $1F, $A4, $FF, $7F, $E5, $E5, $E6, $FE, $C2
    db $C2, $FC, $C4, $20, $27, $16, $0E, $0B, $0F, $13, $14, $00, $20, $10, $88, $08
    db $78, $A8, $28, $14, $1F, $3C, $3F, $3B, $3F, $FF, $7F, $78, $F8, $03, $08, $93
    db $04, $FF, $86, $14, $1F, $1E, $18, $18, $1F, $FC, $7F, $78, $F8, $78, $78, $7C
    db $FC, $7F, $FE, $00, $87, $00, $01, $03, $03, $40, $98, $47, $03, $00, $02, $80
    db $8D, $90, $CD, $82, $00, $06, $06, $02, $12, $12, $11, $15, $24, $F0, $03, $B0
    db $9C, $A8, $C8, $C0, $C0, $02, $06, $02, $12, $12, $13, $29, $28, $F0, $F8, $D8
    db $98, $AC, $A8, $A8, $A0, $00, $01, $03, $03, $00, $47, $27, $01, $02, $00, $02
    db $80, $B6, $40, $E2, $E4, $80, $02, $03, $02, $12, $12, $11, $15, $24, $60, $D0
    db $30, $B0, $A8, $C8, $C0, $C0, $06, $03, $02, $12, $12, $13, $29, $28, $60, $D8
    db $10, $90, $AC, $A8, $A8, $A0, $00, $60, $61, $63, $61, $63, $6B, $70, $00, $C0
    db $60, $60, $40, $90, $10, $00, $6E, $0C, $03, $02, $84, $01, $05, $14, $70, $03
    db $B0, $90, $A8, $C8, $C0, $C0, $6E, $0C, $02, $0A, $0A, $0B, $09, $08, $50, $D0
    db $D0, $90, $03, $A8, $83, $A0, $00, $01, $04, $07, $84, $4F, $6F, $00, $80, $02
    db $D0, $02, $D4, $84, $EC, $AC, $6A, $2E, $02, $1F, $02, $1E, $85, $1C, $1E, $EC
    db $6C, $8C, $03, $E0, $84, $A0, $00, $00, $01, $04, $07, $8D, $4F, $6F, $6A, $6E
    db $6F, $0F, $0E, $0E, $0A, $00, $EC, $68, $80, $03, $F0, $82, $E0, $F0, $02, $00
    db $02, $09, $C6, $28, $31, $01, $33, $00, $40, $E0, $E0, $80, $EE, $E8, $C4, $69
    db $29, $0D, $02, $1F, $1F, $1E, $1F, $13, $D2, $D8, $60, $30, $50, $00, $00, $69
    db $29, $0D, $03, $06, $05, $00, $00, $13, $D2, $D8, $60, $7C, $7C, $70, $78, $00
    db $04, $03, $07, $00, $06, $0E, $0F, $00, $C0, $E0, $00, $00, $30, $D0, $D0, $0B
    db $00, $1F, $19, $1D, $0D, $0C, $00, $80, $C0, $03, $F0, $85, $F8, $E0, $F8, $0B
    db $00, $05, $0F, $89, $00, $80, $C0, $90, $80, $98, $18, $B8, $30, $00, $02, $00
    db $02, $02, $8B, $78, $EE, $74, $00, $00, $80, $40, $40, $5E, $76, $5E, $0A, $00
    db $03, $48, $82, $44, $24, $02, $20, $0A, $00, $02, $20, $95, $10, $14, $14, $10
    db $00, $00, $1A, $7A, $71, $74, $3C, $00, $00, $80, $58, $5E, $CE, $2E, $3C, $40
    db $01, $07, $00, $89, $80, $48, $08, $48, $44, $24, $20, $20, $01, $07, $00, $90
    db $80, $40, $28, $28, $10, $14, $14, $10, $00, $40, $40, $42, $43, $40, $40, $61
    db $02, $00, $02, $C0, $85, $F0, $68, $C8, $88, $60, $08, $00, $03, $48, $85, $44
    db $24, $20, $20, $60, $09, $00, $02, $28, $9C, $10, $14, $14, $10, $00, $01, $37
    db $77, $77, $17, $4F, $63, $00, $80, $D8, $DC, $CC, $C4, $EC, $CC, $69, $2E, $01
    db $1F, $1E, $1E, $0E, $1E, $03, $EC, $03, $E0, $94, $40, $00, $00, $01, $37, $77
    db $77, $17, $4F, $61, $69, $6E, $61, $0F, $0E, $0E, $04, $00, $EC, $E8, $04, $F0
    db $CB, $70, $F0, $00, $00, $11, $31, $33, $31, $01, $31, $80, $C0, $EC, $EE, $EE
    db $E6, $E0, $C6, $6D, $2D, $0C, $02, $1F, $1F, $07, $1F, $DB, $DA, $58, $60, $30
    db $20, $00, $00, $6D, $2D, $0C, $03, $06, $02, $00, $00, $DB, $DA, $58, $60, $7C
    db $7C, $38, $78, $10, $18, $0B, $07, $04, $06, $0F, $0F, $00, $C0, $E0, $70, $F0
    db $B0, $D0, $D0, $0B, $00, $1F, $19, $1D, $01, $0C, $00, $80, $04, $F0, $85, $F8
    db $78, $F8, $0B, $00, $03, $0F, $8B, $03, $0F, $00, $80, $F0, $90, $80, $98, $88
    db $B8, $30, $00, $02, $00, $02, $02, $02, $00, $81, $04, $05, $00, $82, $02, $01
    db $24, $00, $85, $02, $4A, $10, $14, $18, $04, $00, $84, $12, $08, $28, $18, $0A
    db $00, $81, $40, $0F, $00, $81, $40, $07, $00, $02, $60, $81, $62, $03, $60, $81
    db $01, $02, $00, $02, $40, $83, $60, $50, $90, $23, $00, $86, $10, $50, $40, $00
    db $00, $03, $02, $00, $02, $10, $87, $04, $00, $00, $80, $00, $00, $01, $03, $00
    db $85, $0C, $00, $00, $40, $80, $07, $00, $89, $10, $50, $40, $00, $00, $01, $00
    db $00, $01, $06, $00, $82, $40, $80, $03, $00, $81, $60, $05, $00, $81, $20, $05
    db $00, $81, $08, $02, $0A, $02, $08, $83, $02, $05, $04, $04, $00, $85, $06, $00
    db $08, $48, $40, $05, $00, $82, $05, $04, $06, $00, $83, $08, $48, $40, $03, $00
    db $84, $30, $00, $00, $0C, $04, $00, $81, $02, $04, $00, $81, $40, $02, $80, $0B
    db $00, $81, $C0, $04, $00, $81, $60, $06, $00, $81, $03, $03, $00, $81, $C0, $03
    db $00, $81, $08, $02, $00, $00, $48, $49, $4A, $4B, $4C, $4D, $5B, $5C, $5D, $5E
    db $5F, $60, $00, $00, $00, $15, $15, $2A, $2A, $2A, $3F, $3F, $3F, $00, $00, $3F
    db $39, $3F, $3D, $2B, $16, $1D, $19, $2F, $1B, $1F, $37, $39, $3D, $00, $00, $3F
    db $34, $0F, $3C, $03, $02, $0C, $08, $2F, $06, $0B, $33, $24, $38, $3A, $94, $C1
StateCycleHandler:
    cp $01
    ret c
    jr nz,$BA01
    ld a,($C196)
    inc a
    cp $03
    jr c,$B9E4
    xor a
    ld ($C196),a
    ld hl,$BA0F
    ld b,a
    add a,a
    add a,b
    add a,l
    ld l,a
    jr nc,$B9F2
    inc h
    ld de,$C16D
    ldi
    ldi
    ldi
    ld a,$01
    ld ($C197),a
    ret
    ld a,($C196)
    inc a
    and $01
    ld ($C196),a
    ld hl,$BA18
    jr $B9EA
StateCycleTriples:
    db $38, $37, $37, $37, $38, $37, $37, $37, $38, $14, $15, $35, $14, $35, $15
StateCounters:
    ld a,($C1DF)
    or a
    ret z
    ld a,($C222)
    or a
    ret z
    dec a
    jr z,$BA2C
    dec a
    ld ($C222),a
    ret
    ld a,($C1E3)
    or a
    jr z,$BA3A
    dec a
    ld ($C1E3),a
    ret
MapObjectDirectory:
    dw $BA67, $BAA7, $BAE4, $BB21, $BB2D, $BB2E, $BB63, $BB94
    dw $BBC9, $BBFE, $BC27, $BC50, $BC81, $BC92, $BCB7, $BCE4
    dw $BCF9, $BD06, $BD3B, $BD60, $BD91, $BDBA
MapObjectRecords:
    db $03, $00, $06, $2C, $03, $01, $3A, $1B, $03, $02, $5A, $28, $03, $03, $65, $44
    db $05, $04, $59, $10, $06, $05, $14, $1E, $06, $06, $44, $36, $06, $07, $58, $37
    db $06, $08, $40, $14, $06, $09, $7B, $59, $07, $0A, $1E, $40, $07, $0B, $11, $10
    db $07, $0C, $50, $44, $07, $0D, $30, $1D, $07, $0E, $38, $2C, $02, $1A, $7D, $0B
    db $08, $80, $0E, $68, $08, $80, $1B, $5F, $09, $80, $13, $44, $09, $80, $32, $1F
    db $09, $80, $12, $12, $09, $81, $25, $3D, $09, $81, $3E, $29, $09, $81, $4A, $1D
    db $08, $81, $5D, $41, $08, $81, $6E, $28, $09, $82, $5F, $5B, $08, $82, $71, $10
    db $09, $82, $4B, $6D, $08, $82, $39, $42, $09, $82, $69, $26, $00, $0B, $0F, $71
    db $33, $0B, $10, $34, $79, $0B, $11, $5B, $74, $0B, $12, $1F, $76, $0B, $13, $75
    db $65, $0C, $14, $6D, $77, $0C, $15, $0D, $79, $0C, $16, $45, $76, $0C, $17, $4B
    db $63, $0C, $18, $52, $59, $09, $83, $76, $23, $08, $83, $60, $0B, $09, $83, $36
    db $16, $08, $83, $20, $17, $09, $83, $20, $27, $00, $09, $83, $29, $20, $08, $83
    db $4E, $23, $09, $83, $60, $07, $00, $09, $84, $79, $4C, $09, $84, $50, $5A, $09
    db $84, $42, $58, $09, $84, $34, $36, $09, $84, $19, $5A, $09, $85, $25, $4A, $09
    db $85, $0F, $4C, $09, $85, $0A, $36, $09, $85, $6A, $12, $09, $85, $41, $1F, $09
    db $86, $0A, $22, $0D, $1E, $2A, $0B, $0F, $86, $45, $0B, $00, $09, $86, $71, $3B
    db $09, $86, $63, $32, $09, $86, $78, $29, $09, $86, $25, $4C, $09, $85, $29, $39
    db $09, $84, $51, $32, $09, $85, $3D, $27, $09, $84, $48, $27, $09, $85, $65, $1A
    db $09, $84, $47, $0C, $09, $85, $17, $46, $09, $84, $0E, $15, $00, $09, $87, $1D
    db $43, $09, $87, $39, $4D, $09, $87, $39, $2B, $09, $87, $32, $0A, $09, $87, $03
    db $38, $09, $88, $04, $1B, $09, $88, $13, $0D, $09, $88, $4E, $58, $09, $88, $5D
    db $39, $09, $89, $70, $4C, $09, $89, $7A, $20, $09, $89, $63, $21, $09, $89, $7A
    db $5A, $00, $09, $87, $63, $5B, $09, $87, $78, $6A, $09, $87, $4D, $4A, $09, $87
    db $37, $67, $09, $88, $49, $3E, $09, $88, $20, $3E, $09, $88, $0A, $34, $09, $88
    db $06, $5C, $09, $88, $6F, $36, $09, $89, $79, $42, $09, $89, $74, $5D, $09, $89
    db $26, $63, $09, $89, $14, $6B, $00, $09, $8A, $67, $62, $11, $8A, $60, $6D, $09
    db $8A, $4F, $71, $09, $8B, $1D, $67, $09, $8B, $07, $52, $09, $8B, $2D, $36, $09
    db $8B, $2B, $0E, $11, $8C, $4B, $48, $09, $8C, $72, $3B, $09, $8C, $67, $0F, $00
    db $09, $8D, $61, $1B, $11, $8E, $56, $2E, $09, $8E, $76, $49, $0F, $8F, $62, $5F
    db $09, $8F, $48, $59, $09, $8D, $2B, $41, $09, $8F, $09, $4B, $11, $8D, $2C, $1D
    db $09, $8D, $3C, $10, $09, $8E, $4A, $20, $00, $09, $90, $77, $4E, $11, $91, $56
    db $3F, $09, $90, $75, $11, $11, $92, $32, $14, $11, $92, $37, $0A, $11, $92, $5C
    db $10, $09, $91, $22, $1E, $11, $91, $24, $38, $09, $91, $38, $3D, $11, $92, $43
    db $60, $11, $92, $25, $5F, $11, $92, $31, $4E, $00, $12, $23, $39, $13, $09, $93
    db $6A, $1F, $0F, $93, $0E, $1B, $0F, $93, $10, $1B, $00, $09, $94, $14, $3D, $09
    db $94, $04, $64, $09, $94, $44, $65, $09, $94, $73, $63, $09, $94, $62, $42, $09
    db $94, $55, $63, $09, $95, $33, $23, $09, $95, $27, $0B, $09, $95, $06, $23, $00
    db $01, $27, $4C, $1F, $09, $96, $4B, $0F, $09, $96, $63, $18, $09, $96, $74, $2D
    db $09, $96, $15, $3B, $09, $96, $2C, $53, $09, $96, $03, $6D, $21, $98, $18, $56
    db $21, $98, $0C, $56, $21, $98, $10, $5C, $21, $98, $14, $5C, $00, $14, $25, $6A
    db $3B, $1A, $2E, $55, $6D, $09, $97, $25, $78, $09, $97, $14, $5D, $09, $96, $69
    db $1D, $00, $09, $99, $79, $44, $09, $99, $70, $63, $09, $99, $4F, $5E, $00, $16
    db $30, $08, $09, $09, $9B, $3C, $49, $09, $9B, $2D, $6D, $09, $9B, $37, $6D, $09
    db $9B, $2F, $79, $09, $9B, $04, $6E, $11, $9A, $39, $16, $11, $9A, $30, $30, $11
    db $9A, $19, $2E, $11, $9A, $09, $33, $09, $9C, $71, $58, $09, $9C, $45, $51, $09
    db $9C, $67, $56, $00, $1E, $9E, $37, $18, $1F, $9E, $37, $18, $1F, $9E, $37, $18
    db $09, $9E, $0F, $20, $0F, $9E, $29, $72, $0F, $9E, $2B, $72, $09, $9D, $1D, $58
    db $09, $9D, $3A, $4C, $09, $9D, $29, $44, $00, $15, $26, $04, $19, $09, $9E, $29
    db $73, $09, $9E, $2B, $73, $09, $9F, $25, $3B, $09, $9F, $27, $5C, $09, $9F, $4A
    db $5D, $09, $9F, $6B, $1D, $09, $A0, $1F, $4A, $09, $A0, $16, $56, $09, $A0, $42
    db $46, $09, $A0, $61, $42, $09, $A0, $3A, $17, $00, $18, $28, $06, $0B, $1B, $22
    db $16, $0C, $09, $A1, $79, $1F, $09, $A1, $3B, $0A, $09, $A1, $5A, $44, $09, $A1
    db $15, $34, $09, $A2, $57, $10, $09, $A2, $2A, $1A, $09, $A2, $3C, $4C, $09, $A2
    db $3D, $2C, $00, $10, $34, $3F, $1C, $00
TextSelectorSymbols:
    db $81, $82, $92, $83, $84, $85, $8C, $86, $87, $88, $93, $89, $8A, $8B, $95, $8E
    db $91, $8F, $90, $94, $B0
TextPointerDirectory:
    dw $BE10, $BE20, $BE36, $BE49, $BE5E, $BE78, $BE89, $BE9F
    dw $BEB8, $BECF, $BEEC, $BF08, $BF1C, $BF31, $BF47, $BF5C
    dw $BF70, $BF84, $BF97, $BFAC, $BFC2
TextPrefix:
    db $58, $94, $20, $52, $30, $54, $4E, $44, $20, $52, $45, $4C, $45, $43, $53, $49
    db $30, $4E, $0F, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $46, $45, $45
    db $4E, $41, $15, $20, $20, $20, $20, $20, $46, $30, $54, $4E, $53, $41, $49, $4E
    db $20, $30, $46, $20, $4C, $30, $55, $45, $12, $20, $20, $20, $20, $20, $20, $20
    db $20, $53, $48, $45, $20, $52, $58, $30, $4E, $49, $4E, $14, $20, $20, $20, $20
    db $20, $20, $53, $45, $41, $51, $52, $20, $30, $46, $20, $52, $58, $4C, $4F, $48
    db $19, $20, $20, $46, $49, $51, $52, $53, $20, $52, $53, $45, $4F, $20, $53, $30
    db $56, $41, $51, $44, $52, $20, $56, $41, $51, $52, $10, $20, $20, $20, $20, $20
    db $20, $20, $20, $20, $20, $4F, $41, $4C, $41, $43, $45, $15, $20, $20, $20, $20
    db $20, $48, $30, $4C, $44, $45, $51, $52, $20, $30, $46, $20, $4F, $30, $56, $45
    db $51, $18, $20, $20, $20, $4F, $41, $4C, $41, $43, $45, $20, $30, $46, $20, $44
    db $45, $52, $53, $51, $54, $43, $53, $49, $30, $4E, $16, $20, $20, $20, $20, $42
    db $45, $41, $53, $20, $30, $46, $20, $53, $48, $45, $20, $53, $45, $51, $51, $30
    db $51, $1C, $53, $30, $56, $45, $51, $20, $30, $46, $20, $53, $48, $45, $20, $52
    db $48, $41, $44, $30, $56, $20, $30, $46, $20, $44, $45, $41, $53, $48, $1B, $53
    db $48, $45, $20, $4C, $41, $52, $53, $20, $4D, $30, $4D, $45, $4E, $53, $20, $30
    db $46, $20, $53, $48, $45, $20, $44, $41, $51, $4B, $13, $20, $20, $20, $20, $20
    db $20, $20, $46, $49, $4E, $41, $4C, $20, $42, $41, $53, $53, $4C, $45, $14, $20
    db $20, $20, $20, $20, $20, $20, $51, $45, $52, $53, $20, $49, $4E, $20, $4F, $45
    db $41, $43, $45, $15, $20, $20, $20, $20, $20, $53, $48, $45, $20, $4D, $30, $51
    db $4E, $49, $4E, $47, $20, $47, $4C, $30, $56, $14, $20, $20, $20, $20, $20, $20
    db $20, $52, $45, $45, $20, $58, $30, $54, $20, $41, $47, $41, $49, $4E, $13, $20
    db $20, $20, $20, $20, $20, $20, $20, $44, $45, $41, $44, $4C, $58, $20, $56, $49
    db $4E, $44, $13, $20, $20, $20, $20, $20, $20, $20, $53, $51, $45, $41, $52, $54
    db $51, $45, $20, $42, $30, $57, $12, $20, $20, $20, $20, $20, $20, $20, $20, $20
    db $47, $41, $4D, $45, $20, $30, $55, $45, $51, $14, $20, $20, $20, $20, $20, $20
    db $53, $45, $4D, $4F, $4C, $45, $20, $44, $45, $4C, $20, $52, $30, $4C, $15, $20
    db $20, $20, $20, $53, $48, $45, $20, $53, $48, $45, $4D, $45, $20, $30, $46, $20
    db $41, $51, $30, $4E, $0F, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
    db $45, $57, $49, $53, $FF
BankPadding:
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
