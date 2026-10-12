; Ys SMS bank 02: source-only reconstruction with ROM-independent typed song data.
; Unresolved sound command streams are byte-preserving, NOT decoded audio semantics.
org $8000
SoundFrameUpdate:
    exx
    ld a,($DE60)
    or a
    ex af,af'
    ld hl,$DE6D
    exx
    call $8067
    call $8080
    call $80C0
    call $81D9
    ld a,($DE60)
    or a
    jp z,$8042
    ld ix,$DE6F
    ld b,$08
    push bc
    ld a,$03
    cp b
    jr z,$8039
    bit 7,(ix+0)
    call nz,$837F
    ld de,$0020
    add ix,de
    pop bc
    djnz $8023
    ret
    bit 7,(ix+0)
    call nz,$8329
    jr $8030
    ld ix,$DEAF
    ld b,$06
    push bc
    ld a,$03
    cp b
    jr z,$805E
    bit 7,(ix+0)
    call nz,$8947
    ld de,$0020
    add ix,de
    pop bc
    djnz $8048
    ret
    bit 7,(ix+0)
    call nz,$8889
    jr $8055
    ld hl,$DE61
    ld a,(hl)
    or a
    ret z
    dec (hl)
    ret nz
    ld a,($DE62)
    ld (hl),a
    ld hl,$DE79
    ld de,$0020
    ld b,$06
    inc (hl)
    add hl,de
    djnz $807B
    ret
    ld de,$DE64
    call $808F
    inc de
    call $808F
    inc de
    call $808F
    ret
    ld a,(de)
    bit 7,a
    ret z
    and $7F
    ld hl,$8D02
    dec a
    ld b,$00
    ld c,a
    add hl,bc
    bit 7,(hl)
    jr z,$80AD
    ld a,(de)
    ld ($DE63),a
    xor a
    ld (de),a
    pop hl
    pop hl
    jp $8013
    ret
    ld a,($DE67)
    cp (hl)
    jr z,$80B5
    jr nc,$80BD
    ld a,(de)
    ld ($DE63),a
    ld a,(hl)
    ld ($DE67),a
    xor a
    ld (de),a
    ret
    ld a,($DE6A)
    or a
    ret z
    ld a,($DE6B)
    dec a
    jr z,$80CF
    ld ($DE6B),a
    ret
    ld a,($DE6C)
    ld ($DE6B),a
    ld a,($DE6A)
    dec a
    ld ($DE6A),a
    jp z,$8803
    ld hl,$DE77
    ld de,$0020
    ld b,$05
    ld a,(hl)
    inc a
    cp $10
    jr z,$80EE
    ld (hl),a
    add hl,de
    djnz $80E7
    ex af,af'
    jr nz,$80F6
    ex af,af'
    ret
    ex af,af'
    ld hl,$DE76
    ld de,$001F
    ld bc,$0530
    ld a,c
    out ($F0),a
    inc c
    ld a,(hl)
    and $F0
    inc hl
    or (hl)
    add hl,de
    out ($F1),a
    call $8883
    djnz $8100
    ret
    ld a,$0C
    ld ($DE6A),a
    ld a,($DE6C)
    ld ($DE6B),a
    xor a
    ld ($DF0F),a
    ld a,$FF
    out ($7F),a
    ld a,($DE60)
    or a
    jp z,$831A
    ld b,$03
    xor a
    ld c,$F0
    ld d,$23
    out (c),d
    inc d
    call $8883
    out ($F1),a
    call $8883
    djnz $8133
    ld ($DF0F),a
    ld ($DF2F),a
    ld ($DF4F),a
    jp $831A
    xor a
    ld ($DE67),a
    ld ($DF2F),a
    ld ($DF4F),a
    ld hl,$DECF
    res 2,(hl)
    ld hl,$DEEF
    res 2,(hl)
    ld hl,$DF0F
    res 2,(hl)
    ld hl,$8880
    ld c,$7F
    ld b,$03
    otir
    ld a,$24
    call $8184
    ld hl,$8880
    ld c,$7F
    ld b,$03
    otir
    ld a,$25
    call $8184
    jp $831A
    out ($F0),a
    call $8883
    xor a
    out ($F1),a
    ret
    push bc
    ld a,(bc)
    and $F0
    rra
    rra
    rra
    rra
    ld hl,$81B1
    call $8320
    ld h,b
    ld l,c
    ld b,$12
    ld c,$F1
    dec c
    outi
    inc c
    call $8883
    outi
    call $8883
    jr nz,$81A1
    pop bc
    ret
SoundInitRegisterSequence:
    db $B5, $81, $C7, $81, $16, $20, $17, $B0, $18, $01, $26, $05
    db $27, $01, $28, $01, $36, $00, $37, $40, $38, $51, $16, $20
    db $17, $B0, $18, $FF, $26, $05, $27, $01, $28, $A5, $36, $04
    db $37, $30, $38, $F6
    ld a,($DE63)
    bit 7,a
    jp z,$8803
    cp $A0
    jp c,$8204
    cp $B8
    jp c,$8235
    cp $BC
    jp c,$831A
    cp $BE
    jp nc,$8803
    sub $BC
    add a,a
    ld c,a
    ld b,$00
    ld hl,$8CFE
    add hl,bc
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    jp (hl)
    sub $81
    ret m
    push af
    call $8803
    pop af
    ld b,$00
    ld c,a
    ld hl,$8D40
    add hl,bc
    push af
    ld a,(hl)
    ld ($DE61),a
    ld ($DE62),a
    ld de,$DEAF
    ld hl,$8C90
    ex af,af'
    jr z,$822A
    ld de,$DE6F
    ld hl,$8CFE
    ex af,af'
    pop af
    call $8320
    call $818D
    jp $82D7
    xor a
    ld ($DF47),a
    ld ($DF67),a
    ld a,($DE63)
    sub $A0
    ld hl,$8CCE
    ex af,af'
    jr z,$824A
    ld hl,$8CFE
    ex af,af'
    call $8320
    ld h,b
    ld l,c
    inc hl
    inc hl
    ld a,(hl)
    ex af,af'
    jr z,$8282
    ex af,af'
    cp $10
    jr z,$8264
    cp $14
    jr z,$826C
    ld de,$DF4F
    jr $827B
    call $8803
    ld de,$DE6F
    jr $82D7
    ld de,$DF2F
    ld a,$24
    call $8184
    ld a,$14
    ld hl,$DEEF
    set 2,(hl)
    add a,$10
    call $8184
    jr $82D7
    ex af,af'
    cp $C0
    jr z,$82A4
    cp $E0
    jr z,$8297
    cp $A0
    jr z,$82A9
    call $8803
    ld de,$DEAF
    jr $82D7
    ld a,$DF
    out ($7F),a
    ld a,$E7
    out ($7F),a
    ld hl,$DF0F
    set 2,(hl)
    ld de,$DF4F
    jr $82B1
    ld de,$DF2F
    ld hl,$DECF
    set 2,(hl)
    ld h,b
    ld l,c
    push de
    ld de,$000B
    add hl,de
    pop de
    ld a,(hl)
    cp $E0
    jr nz,$82C7
    ld hl,$DF0F
    set 2,(hl)
    ld a,$E7
    out ($7F),a
    ld a,$FF
    out ($7F),a
    ld a,$C0
    out ($7F),a
    xor a
    out ($7F),a
    ld hl,$DEEF
    set 2,(hl)
    ld h,b
    ld l,c
    ld a,(hl)
    and $0F
    ld b,a
    inc hl
    push bc
    push hl
    pop ix
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ld a,$20
    ld (de),a
    inc de
    ld a,$01
    ld (de),a
    inc de
    xor a
    ld (de),a
    inc de
    ld (de),a
    inc de
    ld (de),a
    push hl
    ld hl,$0013
    add hl,de
    ex de,hl
    pop hl
    ld bc,$8317
    push bc
    ld a,($DE60)
    or a
    jp nz,$8472
    jp $8A4B
    pop bc
    djnz $82DE
    ld a,$80
    ld ($DE63),a
    ret
    add a,a
    ld b,$00
    ld c,a
    add hl,bc
    ld c,(hl)
    inc hl
    ld b,(hl)
    ret
    inc (ix+11)
    ld a,(ix+10)
    sub (ix+11)
    jr nz,$8343
    call $8351
    ld a,$0E
    out ($F0),a
    ld a,(ix+16)
    or $20
    out ($F1),a
    ret
    cp $02
    ret nz
    ld a,$0E
    out ($F0),a
    call $8883
    xor a
    out ($F1),a
    ret
    ld e,(ix+3)
    ld d,(ix+4)
    ld a,(de)
    inc de
    cp $E0
    jp nc,$8375
    cp $7F
    jp c,$8543
    bit 5,a
    jr z,$8369
    or $01
    bit 2,a
    jr z,$836F
    or $10
    ld (ix+16),a
    jp $8535
    ld hl,$837B
    jp $85E9
    inc de
    jp $8357
    inc (ix+11)
    ld a,(ix+10)
    sub (ix+11)
    call z,$84F1
    ld ($DE6D),a
    cp $80
    jp z,$83E8
    bit 5,(ix+0)
    jp z,$83E8
    exx
    ld (hl),$80
    exx
    bit 3,(ix+0)
    jp nz,$83C8
    ld a,(ix+17)
    bit 7,a
    jr z,$83BA
    add a,(ix+14)
    jr c,$83E5
    dec (ix+15)
    dec (ix+15)
    jp $83E1
    add a,(ix+14)
    jr nc,$83E5
    inc (ix+15)
    inc (ix+15)
    jp $83E1
    ld a,(ix+17)
    bit 7,a
    jr z,$83D9
    add a,(ix+14)
    jr c,$83E5
    dec (ix+15)
    jr $83E1
    add a,(ix+14)
    jr nc,$83E5
    inc (ix+15)
    set 1,(ix+7)
    ld (ix+14),a
    bit 2,(ix+0)
    ret nz
    ld a,(ix+19)
    cp $1F
    ret z
    ld a,($DE6D)
    bit 0,(ix+7)
    jr nz,$8401
    cp $02
    jp c,$8488
    or a
    jp m,$8412
    bit 7,(ix+20)
    ret nz
    ld c,(ix+6)
    dec c
    jp p,$8416
    ret
    ld c,(ix+6)
    dec c
    ld ixl,(ix+14)
    ld ixh,(ix+15)
    jp m,$8435
    ld a,l
    or h
    jr nz,$842B
    ld a,$FF
    ld (ix+20),a
    jp $8435
    ex de,hl
    ld hl,$8C2F
    call $849D
    call $84A9
    bit 3,(ix+0)
    call nz,$8590
    ld c,$F1
    ld a,(ix+1)
    out ($F0),a
    add a,$10
    call $8883
    call $8883
    out (c),l
    call $8883
    exx
    bit 7,(hl)
    exx
    out ($F0),a
    jr nz,$8467
    bit 0,(ix+7)
    jr z,$8467
    bit 1,(ix+7)
    ret z
    res 1,(ix+7)
    bit 2,(ix+7)
    jr z,$846F
    set 5,h
    out (c),h
    ret
    ld a,(ix+1)
    add a,$20
    out ($F0),a
    ld a,(ix+7)
    and $F0
    ld c,a
    ld a,(ix+8)
    and $0F
    or c
    out ($F1),a
    ret
    ld (ix+19),$1F
    ld a,(ix+1)
    add a,$10
    out ($F0),a
    call $8883
    call $8883
    xor a
    out ($F1),a
    ret
    ld b,$00
    add hl,bc
    add hl,bc
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ret
    ld (ix+13),a
    push hl
    ld c,(ix+13)
    ld b,$00
    add hl,bc
    ld c,l
    ld b,h
    pop hl
    ld a,(bc)
    bit 7,a
    jp z,$84D6
    cp $83
    jr z,$84CB
    jp nc,$84D2
    cp $80
    jr z,$84CF
    ld a,$FF
    ld (ix+20),a
    pop hl
    ret
    inc bc
    ld a,(bc)
    jr $84A6
    xor a
    jr $84A6
    ld h,$FF
    jr $84D8
    ld h,$00
    ld l,a
    inc (ix+13)
    add hl,de
    ld a,($DE60)
    or a
    jr z,$84ED
    ld a,h
    cp (ix+16)
    jr z,$84ED
    set 1,(ix+7)
    ld (ix+16),a
    ret
    ld e,(ix+3)
    ld d,(ix+4)
    ld a,(de)
    inc de
    cp $E0
    jp nc,$85E6
    bit 3,(ix+0)
    jp nz,$856C
    cp $80
    jp c,$8543
    jr nz,$850C
    call $85CF
    ld a,(hl)
    ld (ix+14),a
    inc hl
    ld a,(hl)
    ld (ix+15),a
    bit 5,(ix+0)
    jp z,$8535
    ld a,(de)
    inc de
    ld (ix+18),a
    ld (ix+17),a
    bit 3,(ix+0)
    ld a,(de)
    jr nz,$8542
    ld (ix+17),a
    inc de
    ld a,(de)
    jr $8542
    ld a,(de)
    or a
    jp p,$8542
    ld a,(ix+21)
    ld (ix+10),a
    jr $8553
    inc de
    ld b,(ix+2)
    dec b
    jr z,$854D
    ld c,a
    add a,c
    djnz $854A
    ld (ix+10),a
    ld (ix+21),a
    xor a
    ld (ix+12),a
    ld (ix+13),a
    ld (ix+11),a
    ld (ix+19),a
    ld (ix+20),a
    ld (ix+3),e
    ld (ix+4),d
    ld a,$80
    ret
    ld h,a
    ld a,(de)
    inc de
    ld l,a
    or h
    jr z,$8587
    ld a,(ix+5)
    or a
    jr z,$8587
    jp p,$8582
    add a,l
    jr c,$8586
    dec h
    jr $8586
    add a,l
    jr nc,$8586
    inc h
    ld l,a
    ld (ix+14),ixl
    ld (ix+15),ixh
    jp $8518
    push de
    ld a,h
    or a
    jr z,$85A3
    cp $02
    ld a,$12
    jr c,$85BC
    srl h
    rr l
    ld a,$10
    jr $85BC
    ld a,l
    or a
    jp z,$85CD
    ld bc,$0400
    rlca
    inc c
    jr c,$85B1
    djnz $85AB
    ld b,c
    ld a,$12
    inc a
    inc a
    sla l
    rl h
    djnz $85B4
    ld de,$0757
    ex de,hl
    or a
    sbc hl,de
    bit 1,h
    jr z,$85C9
    set 0,h
    ld d,a
    ld e,$00
    add hl,de
    pop de
    ret
    sub $80
    jr z,$85D6
    add a,(ix+5)
    ld hl,$8A58
    ex af,af'
    jr z,$85DF
    ld hl,$8AEA
    ex af,af'
    ld c,a
    ld b,$00
    add hl,bc
    add hl,bc
    ret
    ld hl,$85FC
    push hl
    sub $EC
    jp c,$868D
    ld hl,$8600
    add a,a
    ld c,a
    ld b,$00
    add hl,bc
    ld c,(hl)
    inc hl
    ld h,(hl)
    ld l,c
    jp (hl)
    inc de
    jp $84F7
SoundDispatchTargets:
    dw $868E
    dw $86EC
    dw $8628
    dw $863A
    dw $867B
    dw $867B
    dw $873E
    dw $86AA
    dw $86E1
    dw $86C3
    dw $86E6
    dw $87EB
    dw $87BD
    dw $87D8
    dw $868D
    dw $867B
    dw $873E
    dw $873E
    dw $8667
    dw $8646
    ex af,af'
    jr nz,$8630
    ex af,af'
    ld a,(de)
    inc de
    jr $8633
    ex af,af'
    inc de
    ld a,(de)
    add a,(ix+2)
    ld (ix+2),a
    ret
    ld a,($DE6A)
    or a
    ret nz
    ld a,(de)
    add a,(ix+8)
    jp $8694
    ld a,(ix+1)
    add a,$10
    out ($F0),a
    ld h,d
    ld l,e
    ld b,$08
    xor a
    ld c,$F1
    out (c),a
    call $8883
    out ($F0),a
    inc a
    call $8883
    outi
    jr nz,$8656
    ld d,h
    ld e,l
    dec de
    ret
    ld a,($DE6A)
    or a
    ret nz
    ld a,($DE60)
    or a
    ret z
    ld a,(de)
    add a,(ix+8)
    ld (ix+8),a
    jp $869E
    ex af,af'
    jr nz,$8683
    ex af,af'
    ld a,(de)
    inc de
    jr $8686
    ex af,af'
    inc de
    ld a,(de)
    add a,(ix+5)
    ld (ix+5),a
    ret
    dec de
    ld a,($DE6A)
    or a
    ret nz
    ld a,(de)
    and $0F
    ld (ix+8),a
    bit 2,(ix+0)
    ret nz
    ex af,af'
    jp nz,$86A6
    ex af,af'
    jp $8A4B
    ex af,af'
    jp $8472
    ld a,(de)
    or $E0
    out ($7F),a
    or $FC
    inc a
    jr nz,$86B9
    res 6,(ix+0)
    ret
    set 6,(ix+0)
    ld hl,$DEEF
    res 2,(hl)
    ret
    ex af,af'
    jr nz,$86D0
    ex af,af'
    ld a,(de)
    inc de
    cp $80
    ret z
    ld (ix+7),a
    ret
    ex af,af'
    inc de
    ld a,($DE6A)
    or a
    ret nz
    ld a,(de)
    cp $04
    ret z
    ld (ix+7),a
    jp $8472
    ld a,(de)
    ld (ix+6),a
    ret
    ex de,hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    dec de
    ret
    ld a,(de)
    cp $01
    jr z,$870F
    ld a,(ix+23)
    ld (ix+5),a
    ld a,(ix+27)
    ld (ix+8),a
    res 5,(ix+0)
    ld a,($DE60)
    or a
    ret z
    ld a,(ix+22)
    ld (ix+7),a
    jp $8472
    set 5,(ix+0)
    ld a,(ix+5)
    ld (ix+23),a
    xor a
    ld (ix+5),a
    ld a,(ix+8)
    ld (ix+27),a
    ld (ix+8),$03
    ld a,($DE60)
    or a
    ret z
    ld a,$12
    ld (ix+5),a
    ld a,(ix+7)
    ld (ix+22),a
    ld (ix+7),$53
    jp $8472
    xor a
    ld ($DE67),a
    ld (ix+0),a
    ex af,af'
    jp nz,$878B
    ex af,af'
    ld a,(ix+1)
    add a,$1F
    out ($7F),a
    cp $DF
    jp nc,$876F
    cp $9F
    jp nz,$8765
    ld hl,$DEAF
    res 2,(hl)
    ld hl,$DEC2
    jr $8785
    ld hl,$DECF
    res 2,(hl)
    ld hl,$DEE2
    jr $8785
    ld hl,$DF0F
    res 2,(hl)
    ld a,$DF
    out ($7F),a
    ld a,($DE68)
    out ($7F),a
    ld hl,$DEEF
    res 2,(hl)
    ld hl,$DF02
    ld a,$1F
    ld (hl),a
    pop hl
    pop hl
    ret
    ex af,af'
    ld a,(ix+1)
    add a,$10
    call $8184
    ld a,(ix+1)
    cp $14
    jr nz,$87BA
    ld hl,$DEEF
    ld a,(hl)
    or a
    jp p,$8788
    res 2,(hl)
    ld a,$34
    out ($F0),a
    ld hl,$DEF6
    ld a,(hl)
    and $F0
    ld c,a
    inc hl
    ld a,(hl)
    and $0F
    or c
    out ($F1),a
    jp $8788
    jp $8788
    ld a,(de)
    ld c,a
    inc de
    ld a,(de)
    ld b,a
    push bc
    push ix
    pop hl
    dec (ix+9)
    ld c,(ix+9)
    dec (ix+9)
    ld b,$00
    add hl,bc
    ld (hl),d
    dec hl
    ld (hl),e
    pop de
    dec de
    ret
    push ix
    pop hl
    ld c,(ix+9)
    ld b,$00
    add hl,bc
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc (ix+9)
    inc (ix+9)
    ret
    ld a,(de)
    inc de
    add a,$18
    ld c,a
    ld b,$00
    push ix
    pop hl
    add hl,bc
    ld a,(hl)
    or a
    jr nz,$87FC
    ld a,(de)
    ld (hl),a
    inc de
    dec (hl)
    jp nz,$86E6
    inc de
    ret
    push hl
    push de
    push bc
    ld hl,$DE63
    ld de,$DE64
    ld (hl),$00
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ldi
    ld hl,$DE6F
    xor a
    ld b,$08
    ld de,$0018
    ld (hl),a
    add hl,de
    ld (hl),a
    inc hl
    ld (hl),a
    inc hl
    ld (hl),a
    inc hl
    ld (hl),a
    ld de,$0005
    add hl,de
    djnz $8828
    ld a,$E4
    ld ($DE68),a
    pop bc
    pop de
    pop hl
    push hl
    push bc
    ld hl,$8878
    ld c,$7F
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
    push de
    ld b,$06
    xor a
    ld c,$F0
    ld d,$20
    out (c),d
    inc d
    call $8883
    out ($F1),a
    call $8883
    djnz $8867
    pop de
    pop bc
    pop hl
    ret
ChannelConstants:
    db $80, $00, $90, $00, $C0, $00, $E4, $9F, $BF, $DF, $FF
    nop
    nop
    nop
    push hl
    pop hl
    ret
    inc (ix+11)
    ld a,(ix+10)
    sub (ix+11)
    call z,$88B2
    bit 2,(ix+0)
    ret nz
    bit 4,(ix+19)
    ret nz
    ld c,(ix+7)
    dec c
    ret m
    ld hl,$8B7D
    call $849D
    call $8A13
    or $F0
    out ($7F),a
    ret
    ld e,(ix+3)
    ld d,(ix+4)
    ld a,(de)
    inc de
    cp $E0
    jp nc,$88DC
    cp $80
    jp c,$8543
    call $88E6
    ld a,(de)
    inc de
    cp $80
    jp c,$8543
    dec de
    ld a,(ix+21)
    ld (ix+10),a
    jp $8553
    dec de
    jp $8553
    ld hl,$88E2
    jp $85E9
    inc de
    jp $88B8
    bit 3,a
    jr nz,$8908
    bit 5,a
    jr nz,$8911
    bit 1,a
    jr nz,$8911
    bit 0,a
    jr nz,$8921
    bit 2,a
    jr nz,$8921
    bit 2,(ix+0)
    ret nz
    ld (ix+7),$00
    ld a,$FF
    out ($7F),a
    ret
    ex af,af'
    ld a,$02
    ld b,$02
    ld c,$E5
    jr $892E
    ld c,$04
    bit 0,a
    jr nz,$8919
    ld c,$03
    ex af,af'
    ld a,c
    ld b,$03
    ld c,$E4
    jr $892E
    ld c,$E4
    bit 2,a
    jr z,$8929
    ld c,$E6
    ex af,af'
    ld a,$01
    ld b,$04
    ld (ix+7),a
    ex af,af'
    bit 2,a
    jr z,$8938
    dec b
    dec b
    ld (ix+8),b
    ld a,c
    ld ($DE68),a
    bit 2,(ix+0)
    ret nz
    out ($7F),a
    ret
    inc (ix+11)
    ld a,(ix+10)
    sub (ix+11)
    call z,$84F1
    ld ($DE6D),a
    cp $80
    jp z,$8982
    bit 5,(ix+0)
    jp z,$8982
    exx
    ld (hl),$80
    exx
    ld a,(ix+18)
    bit 7,a
    jr z,$8977
    add a,(ix+14)
    jr c,$897F
    dec (ix+15)
    jr $897F
    add a,(ix+14)
    jr nc,$897F
    inc (ix+15)
    ld (ix+14),a
    bit 2,(ix+0)
    ret nz
    ld a,(ix+19)
    cp $1F
    ret z
    jr $899A
    ld a,$1F
    ld (ix+19),a
    add a,(ix+1)
    out ($7F),a
    ret
    ld a,(ix+19)
    cp $FF
    jp z,$89B9
    ld c,(ix+7)
    dec c
    jp m,$89B9
    ld hl,$8B7D
    call $849D
    call $8A13
    or (ix+1)
    add a,$10
    out ($7F),a
    ld a,($DE6D)
    or a
    jp m,$89CD
    bit 7,(ix+20)
    ret nz
    ld c,(ix+6)
    dec c
    jp p,$89D1
    ret
    ld c,(ix+6)
    dec c
    ld ixl,(ix+14)
    ld ixh,(ix+15)
    jp m,$89F0
    ld a,l
    or h
    jr nz,$89E6
    ld a,$FF
    ld (ix+20),a
    jp $89F0
    ex de,hl
    ld hl,$8C2F
    call $849D
    call $84A9
    bit 6,(ix+0)
    ret nz
    ld a,(ix+1)
    cp $E0
    jr nz,$89FE
    ld a,$C0
    ld c,a
    ld a,l
    and $0F
    or c
    out ($7F),a
    ld a,l
    and $F0
    or h
    rrca
    rrca
    rrca
    rrca
    out ($7F),a
    ret
    ld (ix+12),a
    push hl
    ld c,(ix+12)
    ld b,$00
    add hl,bc
    ld c,l
    ld b,h
    pop hl
    ld a,(bc)
    bit 7,a
    jr z,$8A3F
    cp $82
    jr z,$8A32
    cp $81
    jr z,$8A39
    cp $80
    jr z,$8A36
    inc bc
    ld a,(bc)
    jr $8A10
    pop hl
    jp $898F
    xor a
    jr $8A10
    ld (ix+19),$FF
    pop hl
    ret
    inc (ix+12)
    add a,(ix+8)
    bit 4,a
    ret z
    ld a,$0F
    ret
    ld a,(ix+8)
    and $0F
    or (ix+1)
    add a,$10
    out ($7F),a
    ret
PSGNotePeriodWords:
    dw $0000
    dw $03FF
    dw $03C7
    dw $0390
    dw $035D
    dw $032D
    dw $02FF
    dw $02D4
    dw $02AB
    dw $0285
    dw $0261
    dw $023F
    dw $021E
    dw $0200
    dw $01E3
    dw $01C8
    dw $01AF
    dw $0196
    dw $0180
    dw $016A
    dw $0156
    dw $0143
    dw $0130
    dw $011F
    dw $010F
    dw $0100
    dw $00F2
    dw $00E4
    dw $00D7
    dw $00CB
    dw $00C0
    dw $00B5
    dw $00AB
    dw $00A1
    dw $0098
    dw $0090
    dw $0088
    dw $0080
    dw $0079
    dw $0072
    dw $006C
    dw $0066
    dw $0060
    dw $005B
    dw $0055
    dw $0051
    dw $004C
    dw $0048
    dw $0044
    dw $0040
    dw $003C
    dw $0039
    dw $0036
    dw $0033
    dw $0030
    dw $002D
    dw $002B
    dw $0028
    dw $0026
    dw $0024
    dw $0022
    dw $0020
    dw $001E
    dw $001C
    dw $001B
    dw $0019
    dw $0018
    dw $0016
    dw $0015
    dw $0014
    dw $0013
    dw $0012
    dw $0011
FMNoteRegisterWords:
    dw $0000
    dw $1157
    dw $116B
    dw $1181
    dw $1198
    dw $11B0
    dw $11CA
    dw $11E5
    dw $1301
    dw $1310
    dw $1320
    dw $1331
    dw $1343
    dw $1357
    dw $136B
    dw $1381
    dw $1398
    dw $13B0
    dw $13CA
    dw $13E5
    dw $1501
    dw $1510
    dw $1520
    dw $1531
    dw $1543
    dw $1557
    dw $156B
    dw $1581
    dw $1598
    dw $15B0
    dw $15CA
    dw $15E5
    dw $1701
    dw $1710
    dw $1720
    dw $1731
    dw $1743
    dw $1757
    dw $176B
    dw $1781
    dw $1798
    dw $17B0
    dw $17CA
    dw $17E5
    dw $1901
    dw $1910
    dw $1920
    dw $1931
    dw $1943
    dw $1957
    dw $196B
    dw $1981
    dw $1998
    dw $19B0
    dw $19CA
    dw $19E5
    dw $1B01
    dw $1B10
    dw $1B20
    dw $1B31
    dw $1B43
    dw $1B57
    dw $1B6B
    dw $1B81
    dw $1B98
    dw $1BB0
    dw $1BCA
    dw $1BE5
    dw $1D01
    dw $1D10
    dw $1D20
    dw $1D31
    dw $1D43
LookupSentinel:
    db $FF
SequencePointerDirectory17:
    dw $8B9F
    dw $8BA2
    dw $8BAB
    dw $8BAF
    dw $8BB4
    dw $8BBF
    dw $8BCC
    dw $8BD5
    dw $8BE4
    dw $8BF0
    dw $8BF5
    dw $8C00
    dw $8C07
    dw $8C13
    dw $8C1D
    dw $8C21
    dw $8C2A
SequenceRecords:
    db $02, $06, $82, $00, $01, $02, $04, $05, $06, $07, $0A, $82
    db $03, $02, $08, $82, $02, $00, $05, $08, $82, $02, $01, $00
    db $01, $02, $02, $03, $03, $04, $04, $81, $01, $00, $01, $02
    db $03, $03, $04, $04, $05, $05, $06, $06, $82, $04, $04, $03
    db $03, $02, $02, $01, $01, $82, $00, $00, $01, $01, $02, $02
    db $02, $03, $03, $03, $03, $04, $04, $05, $81, $07, $04, $00
    db $01, $01, $02, $04, $03, $02, $02, $83, $04, $02, $00, $01
    db $02, $81, $04, $01, $00, $01, $03, $01, $02, $03, $04, $05
    db $81, $07, $00, $07, $00, $07, $00, $80, $04, $02, $00, $03
    db $02, $01, $00, $00, $01, $02, $83, $04, $04, $00, $00, $01
    db $01, $02, $03, $02, $83, $03, $03, $03, $03, $82, $04, $04
    db $04, $04, $04, $04, $04, $04, $82, $00, $03, $06, $09, $82
ShapePointerDirectory5:
    dw $8C39
    dw $8C52
    dw $8C68
    dw $8C80
    dw $8C89
ShapeRecords:
    db $02, $01, $01, $01, $01, $01, $01, $00, $00, $00, $01, $01
    db $01, $00, $00, $00, $01, $01, $00, $00, $00, $00, $FF, $FF
    db $FE, $FD, $FD, $FC, $FE, $FF, $00, $00, $00, $01, $02, $03
    db $02, $01, $00, $00, $FF, $FF, $FE, $FE, $FD, $83, $1D, $03
    db $01, $01, $01, $01, $01, $00, $00, $FF, $FE, $FD, $FD, $FE
    db $FF, $00, $01, $02, $03, $04, $03, $02, $01, $83, $0D, $FA
    db $FF, $00, $06, $00, $00, $03, $83, $04, $57, $18, $11, $00
    db $3F, $01, $80
SongDirectory55:
    dw $AA77
    dw $AA9C
    dw $AAC1
    dw $AAE6
    dw $AB0B
    dw $AB30
    dw $AB55
    dw $AB7A
    dw $AB9F
    dw $ABC4
    dw $ABE9
    dw $AC0E
    dw $AC33
    dw $AC58
    dw $AC7D
    dw $ACA2
    dw $ACC7
    dw $ACEC
    dw $AD11
    dw $AD36
    dw $AD5B
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $AA77
    dw $B319
    dw $B32F
    dw $B35A
    dw $B383
    dw $B3B2
    dw $B3E2
    dw $B401
    dw $B422
    dw $B453
    dw $B470
    dw $B497
    dw $B4AF
    dw $B4E8
    dw $B504
    dw $B554
    dw $B574
    dw $B58C
    dw $B5B1
    dw $B5D2
    dw $B5F1
    dw $B624
    dw $B677
    dw $B6A2
    dw $B6CA
UnresolvedSoundTablesAndEvents:
    db $12, $81, $4C, $81, $80, $80, $80, $80, $80, $80, $80, $80
    db $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80
    db $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $60
    db $60, $68, $50, $70, $70, $70, $70, $60, $70, $70, $70, $70
    db $70, $80, $70, $70, $68, $60, $60, $68, $60, $70, $60, $00
    db $80, $80, $80, $80, $80, $80, $02, $10, $04, $0A, $0A, $04
    db $03, $05, $07, $02, $00, $02, $02, $10, $00, $03, $00, $05
    db $05, $00, $80, $FF, $03, $A4, $0C, $A2, $A1, $9F, $A2, $A1
    db $9F, $9D, $F7, $00, $02, $57, $8D, $9D, $18, $9C, $9A, $9C
    db $F7, $00, $02, $65, $8D, $FB, $F4, $F4, $80, $60, $F5, $80
    db $00, $FF, $8A, $92, $C3, $32, $BC, $72, $A0, $01, $F8, $C6
    db $8D, $A9, $0C, $AE, $30, $80, $24, $F8, $C6, $8D, $A9, $0C
    db $A2, $18, $A5, $0C, $A9, $0C, $A2, $18, $A7, $0C, $A4, $60
    db $80, $F8, $F6, $8D, $F8, $EB, $8D, $A7, $03, $A5, $A7, $12
    db $A0, $06, $A2, $A4, $A7, $F8, $F6, $8D, $A7, $03, $A5, $A7
    db $12, $AC, $06, $AE, $B0, $B1, $B3, $0C, $B0, $AC, $A7, $24
    db $80, $18, $F5, $80, $80, $F6, $72, $8D, $AB, $03, $A9, $AB
    db $B0, $AB, $18, $A9, $0C, $AB, $03, $A9, $AB, $B0, $AB, $18
    db $A7, $0C, $F9, $9F, $30, $F7, $00, $04, $D9, $8D, $F9, $A9
    db $03, $A7, $A9, $12, $A2, $06, $A4, $A5, $F9, $A7, $03, $A5
    db $A7, $12, $A0, $06, $A2, $A4, $A5, $F9, $F8, $E1, $8D, $A7
    db $06, $F8, $E1, $8D, $A9, $06, $F9, $F5, $80, $80, $9A, $30
    db $99, $9A, $99, $A4, $60, $98, $F5, $80, $70, $9D, $30, $30
    db $9D, $30, $30, $9E, $30, $30, $F7, $00, $02, $12, $8E, $9D
    db $30, $EF, $01, $F7, $00, $04, $1D, $8E, $EF, $FC, $9E, $30
    db $9E, $9D, $9D, $9E, $9E, $9D, $60, $80, $30, $F6, $0C, $8E
    db $9D, $0C, $AB, $18, $A9, $0C, $9D, $0C, $AB, $18, $A7, $0C
    db $F9, $F5, $80, $40, $9D, $30, $30, $30, $30, $9F, $30, $30
    db $30, $30, $FB, $00, $F4, $F5, $80, $30, $F8, $84, $8E, $F8
    db $90, $8E, $F8, $90, $8E, $98, $30, $EF, $01, $F7, $00, $04
    db $5F, $8E, $EF, $FC, $F5, $80, $C0, $F8, $9F, $8E, $F8, $A9
    db $8E, $F8, $9F, $8E, $F5, $80, $00, $A4, $0C, $A0, $9B, $98
    db $24, $80, $18, $F6, $53, $8E, $80, $0C, $9B, $03, $06, $1B
    db $F7, $00, $02, $84, $8E, $F9, $F8, $84, $8E, $80, $0C, $99
    db $03, $06, $1B, $F7, $00, $02, $93, $8E, $F9, $B5, $03, $B1
    db $AE, $AA, $F7, $00, $08, $9F, $8E, $B3, $03, $B0, $AC, $A9
    db $F7, $00, $04, $A9, $8E, $F9, $01, $F8, $F0, $8E, $F8, $05
    db $8F, $A2, $06, $A5, $A9, $A7, $A5, $A7, $A5, $A2, $A4, $60
    db $F8, $F0, $8E, $80, $06, $9E, $A2, $A5, $A9, $A7, $80, $A5
    db $A4, $06, $80, $0C, $A5, $06, $80, $0C, $A7, $A5, $06, $A5
    db $A5, $A5, $80, $A5, $80, $A5, $80, $06, $A5, $80, $A5, $A7
    db $A7, $A5, $A7, $F6, $B5, $8E, $80, $06, $9D, $A0, $A4, $A7
    db $A5, $80, $9D, $A0, $06, $A4, $A7, $A5, $A4, $A5, $A4, $A0
    db $A2, $60, $F9, $80, $06, $9E, $A2, $A5, $A9, $A7, $80, $9E
    db $F9, $F8, $49, $8F, $9B, $06, $80, $0C, $9B, $06, $80, $18
    db $F8, $6E, $8F, $A0, $06, $80, $0C, $A0, $06, $80, $18, $F8
    db $79, $8F, $F8, $49, $8F, $F8, $6E, $8F, $F8, $79, $8F, $97
    db $06, $80, $0C, $97, $06, $80, $0C, $97, $06, $80, $97, $06
    db $80, $0C, $97, $06, $97, $97, $97, $97, $F6, $0F, $8F, $99
    db $06, $80, $0C, $99, $06, $80, $18, $99, $06, $80, $0C, $99
    db $06, $80, $99, $9B, $9D, $9E, $06, $80, $0C, $9E, $06, $80
    db $18, $9E, $06, $80, $0C, $9E, $06, $80, $9E, $9D, $9D, $F9
    db $9B, $06, $80, $0C, $9B, $06, $80, $9B, $9D, $9E, $F9, $A0
    db $06, $80, $0C, $A0, $06, $80, $94, $96, $98, $F9, $02, $F8
    db $C1, $8F, $AA, $12, $B1, $B3, $0C, $F8, $D9, $8F, $AC, $0C
    db $B8, $B6, $06, $B5, $0C, $B3, $12, $B3, $0C, $B5, $B6, $F8
    db $C1, $8F, $F8, $D9, $8F, $AC, $06, $80, $0C, $AC, $06, $80
    db $0C, $AC, $B1, $06, $B1, $B1, $B1, $80, $B1, $80, $B1, $80
    db $06, $B1, $80, $B1, $B1, $B1, $B1, $B1, $F6, $85, $8F, $A9
    db $12, $AC, $B1, $0C, $F7, $00, $02, $C1, $8F, $B1, $0C, $B5
    db $B3, $06, $B1, $0C, $AE, $12, $AE, $0C, $B0, $B1, $F9, $AA
    db $12, $AE, $B3, $0C, $F9, $01, $EF, $04, $A8, $0C, $06, $EF
    db $FF, $F7, $00, $06, $E4, $8F, $EF, $02, $AA, $18, $AC, $EF
    db $04, $A7, $0C, $06, $EF, $FF, $F7, $00, $06, $F5, $8F, $EF
    db $02, $A8, $18, $AA, $EF, $04, $A5, $0C, $06, $EF, $FF, $F7
    db $00, $06, $06, $90, $EF, $02, $A7, $18, $A3, $A5, $60, $80
    db $60, $F6, $E0, $8F, $99, $60, $97, $95, $30, $97, $99, $60
    db $99, $F6, $1A, $90, $F8, $4B, $90, $A8, $0C, $A0, $A5, $A0
    db $A3, $0C, $9E, $A5, $9E, $A7, $0C, $9E, $A3, $9E, $A1, $0C
    db $9C, $A5, $A1, $A3, $0C, $A0, $A7, $A3, $F8, $51, $90, $F8
    db $51, $90, $F6, $26, $90, $A5, $0C, $A0, $A7, $A0, $F9, $F8
    db $4B, $90, $A8, $0C, $A0, $A7, $A0, $F9, $01, $03, $9B, $18
    db $80, $0C, $9B, $03, $9D, $9E, $A0, $F8, $0D, $91, $9E, $03
    db $9D, $9B, $12, $80, $0C, $9B, $03, $9D, $9E, $A0, $F8, $0D
    db $91, $9E, $06, $9B, $03, $A7, $1B, $A7, $0C, $A9, $60, $A7
    db $18, $80, $0C, $A7, $03, $A9, $AA, $AC, $F8, $16, $91, $AA
    db $03, $A9, $A7, $12, $80, $0C, $A7, $03, $A9, $AA, $AC, $F8
    db $16, $91, $A7, $30, $A9, $18, $A2, $0C, $A9, $A7, $48, $AA
    db $06, $AC, $AE, $03, $B1, $09, $F8, $31, $91, $80, $0C, $AF
    db $24, $AC, $06, $AE, $AF, $18, $B1, $0C, $B3, $B1, $12, $AA
    db $12, $AC, $06, $AE, $36, $F8, $31, $91, $B8, $06, $BA, $BB
    db $24, $B8, $06, $BA, $BB, $1E, $BA, $06, $BA, $B6, $B8, $12
    db $B1, $18, $B2, $36, $F8, $1F, $91, $F8, $1F, $91, $A7, $03
    db $80, $06, $A7, $27, $A6, $03, $80, $06, $A6, $27, $AE, $0C
    db $ED, $01, $96, $18, $E0, $06, $80, $00, $00, $06, $94, $18
    db $E0, $06, $80, $00, $00, $06, $92, $18, $E0, $06, $80, $00
    db $00, $06, $ED, $00, $F6, $5C, $90, $A2, $18, $A0, $0C, $9E
    db $03, $9D, $09, $F9, $AE, $18, $AC, $0C, $AA, $03, $A9, $09
    db $F9, $A7, $03, $A2, $9E, $A7, $A2, $9E, $9B, $9E, $A7, $A2
    db $9E, $A7, $A2, $9E, $9B, $9E, $F9, $B3, $24, $AF, $06, $B1
    db $B3, $18, $B6, $B5, $12, $B1, $0C, $B3, $06, $AE, $30, $F9
    db $F8, $3F, $92, $F8, $0A, $92, $F8, $0A, $92, $F8, $3F, $92
    db $A2, $03, $80, $A2, $A2, $F7, $00, $03, $4E, $91, $A2, $A0
    db $9D, $A2, $9B, $80, $9B, $80, $99, $06, $9B, $03, $80, $8F
    db $8F, $9E, $80, $9D, $99, $06, $80, $03, $9B, $80, $9B, $80
    db $99, $06, $9B, $03, $80, $8F, $8F, $9D, $9D, $9E, $9E, $A2
    db $A2, $F8, $4F, $92, $F8, $15, $92, $F8, $20, $92, $9E, $03
    db $80, $9E, $A0, $F8, $0A, $92, $F8, $4F, $92, $9C, $03, $80
    db $9C, $9C, $F7, $00, $04, $93, $91, $99, $80, $99, $99, $F7
    db $00, $04, $9D, $91, $96, $80, $96, $96, $F7, $00, $03, $A6
    db $91, $96, $80, $96, $99, $F8, $2B, $92, $F8, $2B, $92, $97
    db $03, $80, $06, $97, $27, $96, $03, $80, $06, $96, $03, $06
    db $03, $80, $96, $80, $96, $80, $96, $80, $96, $80, $96, $80
    db $96, $80, $96, $80, $96, $80, $96, $80, $96, $80, $96, $99
    db $09, $F6, $42, $91, $9B, $03, $80, $9B, $9B, $F7, $00, $04
    db $E2, $91, $F9, $9E, $03, $80, $9E, $9E, $9E, $80, $9E, $9E
    db $A0, $80, $A0, $A0, $A0, $80, $A0, $A0, $F9, $A3, $03, $80
    db $A3, $A3, $F7, $00, $04, $FF, $91, $F9, $A2, $03, $80, $A2
    db $A2, $F7, $00, $04, $0A, $92, $F9, $A0, $03, $80, $A0, $A0
    db $F7, $00, $04, $15, $92, $F9, $9E, $03, $80, $9E, $9E, $F7
    db $00, $03, $20, $92, $F9, $9B, $03, $80, $9B, $80, $99, $9B
    db $06, $80, $03, $8F, $8F, $A0, $80, $A2, $A5, $06, $80, $03
    db $F9, $F8, $E2, $91, $F8, $ED, $91, $F8, $E2, $91, $F8, $ED
    db $91, $F8, $FF, $91, $F9, $F8, $FF, $91, $F8, $FF, $91, $F8
    db $0A, $92, $F8, $0A, $92, $F8, $15, $92, $F9, $02, $F8, $6C
    db $93, $A3, $03, $9E, $9B, $9E, $1B, $A0, $0C, $A2, $06, $9B
    db $03, $A2, $0F, $A6, $06, $A2, $03, $A6, $0F, $A9, $06, $A6
    db $03, $A9, $0F, $AE, $06, $A9, $03, $AE, $0F, $F8, $6C, $93
    db $9E, $18, $A3, $0C, $A7, $A5, $18, $06, $A2, $9D, $03, $99
    db $09, $9B, $18, $9E, $06, $A0, $A2, $03, $A5, $09, $A7, $1B
    db $ED, $01, $96, $18, $E0, $09, $94, $18, $E0, $06, $92, $18
    db $E0, $06, $ED, $00, $AF, $0C, $06, $AA, $12, $A7, $18, $AA
    db $0C, $A3, $A7, $F8, $4D, $93, $A0, $0C, $9B, $06, $A0, $12
    db $A3, $06, $A5, $A7, $18, $AC, $AA, $06, $A5, $A2, $AA, $A5
    db $A2, $AA, $A5, $A9, $06, $A6, $A2, $A9, $A6, $A2, $A9, $A6
    db $A3, $12, $9E, $9B, $18, $9E, $0C, $A3, $A7, $F8, $4D, $93
    db $A0, $0C, $06, $AC, $1E, $A0, $12, $AC, $AA, $06, $A7, $A9
    db $12, $AC, $18, $AE, $0C, $A9, $06, $AA, $A9, $AC, $AA, $A9
    db $AA, $F8, $62, $93, $F8, $62, $93, $ED, $01, $94, $18, $E0
    db $09, $94, $18, $E0, $09, $ED, $00, $A7, $03, $A7, $AA, $AA
    db $AF, $AF, $B3, $B3, $B6, $B6, $ED, $01, $94, $18, $E0, $09
    db $94, $18, $E0, $09, $ED, $00, $A6, $03, $A6, $A9, $A9, $AE
    db $AE, $B2, $B2, $B5, $B5, $AE, $03, $A9, $A6, $A2, $F7, $00
    db $04, $33, $93, $F6, $60, $92, $A2, $03, $9B, $9B, $A2, $27
    db $F9, $A5, $18, $9B, $0C, $A0, $F9, $A2, $06, $A5, $A9, $AE
    db $0C, $A9, $06, $A5, $0C, $A2, $06, $A5, $A9, $AE, $0C, $A9
    db $06, $A5, $A2, $F9, $9B, $18, $9E, $06, $A0, $A2, $03, $A5
    db $09, $F9, $F8, $40, $93, $F8, $47, $93, $F8, $40, $93, $F8
    db $47, $93, $F9, $04, $80, $24, $F7, $00, $10, $7A, $93, $A0
    db $48, $99, $24, $9C, $18, $9E, $0C, $A0, $48, $99, $24, $9C
    db $18, $A5, $0C, $A0, $48, $99, $24, $9C, $18, $9E, $0C, $9B
    db $48, $A0, $3C, $94, $0C, $A0, $48, $99, $24, $9C, $12, $9B
    db $06, $9C, $9E, $A0, $48, $99, $24, $9C, $12, $99, $06, $9C
    db $A5, $A0, $48, $99, $24, $9C, $12, $9B, $06, $9C, $9E, $9B
    db $24, $99, $18, $9B, $0C, $98, $36, $A0, $06, $9E, $9C, $F5
    db $80, $E0, $FB, $00, $0C, $A5, $06, $A5, $A5, $80, $A5, $A5
    db $A8, $06, $A5, $A5, $80, $A5, $A5, $AC, $06, $A5, $A5, $80
    db $A5, $A5, $B1, $06, $A5, $A5, $80, $A5, $A5, $B1, $06, $B1
    db $B1, $80, $B1, $B1, $B4, $06, $B1, $B1, $80, $B1, $B1, $B8
    db $06, $B1, $B1, $80, $B1, $B1, $BD, $06, $B1, $B1, $80, $B1
    db $B1, $F7, $00, $03, $EB, $93, $F5, $80, $80, $B4, $24, $B1
    db $0C, $B3, $B4, $B6, $24, $B4, $0C, $B3, $AF, $B1, $48, $BD
    db $30, $80, $18, $FB, $00, $F4, $F5, $80, $50, $F6, $81, $93
    db $F8, $97, $94, $F8, $8A, $94, $F8, $97, $94, $F8, $8A, $94
    db $F8, $97, $94, $F8, $8A, $94, $F8, $63, $94, $F8, $70, $94
    db $F8, $7D, $94, $F8, $70, $94, $F8, $63, $94, $F8, $70, $94
    db $F8, $7D, $94, $F8, $7D, $94, $F8, $7D, $94, $F8, $70, $94
    db $F8, $63, $94, $F8, $63, $94, $F6, $30, $94, $99, $06, $99
    db $80, $99, $99, $99, $F7, $00, $02, $63, $94, $F9, $97, $06
    db $97, $80, $97, $97, $97, $F7, $00, $02, $70, $94, $F9, $95
    db $06, $95, $80, $95, $95, $95, $F7, $00, $02, $7D, $94, $F9
    db $94, $06, $94, $80, $94, $94, $94, $F7, $00, $04, $8A, $94
    db $F9, $F8, $63, $94, $F8, $63, $94, $F8, $70, $94, $F8, $70
    db $94, $F8, $7D, $94, $F8, $7D, $94, $F9, $02, $F8, $2A, $95
    db $F8, $2A, $95, $F8, $2A, $95, $FB, $00, $0C, $F5, $80, $80
    db $A5, $03, $03, $A0, $A0, $A8, $A8, $A7, $A7, $A0, $A0, $9C
    db $9C, $F7, $00, $10, $BA, $94, $A1, $A1, $9C, $9C, $A5, $A5
    db $A1, $A1, $9C, $9C, $99, $99, $F7, $00, $02, $CC, $94, $A3
    db $A3, $9E, $9E, $A7, $A7, $A3, $A3, $9E, $9E, $9B, $9B, $F7
    db $00, $02, $DD, $94, $A5, $A5, $A0, $A0, $A8, $A8, $A5, $A5
    db $A0, $A0, $9C, $9C, $F7, $00, $03, $EE, $94, $A5, $A5, $A0
    db $A0, $A8, $A8, $A5, $A5, $A0, $0C, $FB, $00, $F4, $F5, $80
    db $20, $F6, $AE, $94, $AC, $06, $A7, $A5, $A7, $A5, $A0, $F7
    db $00, $02, $12, $95, $AC, $A7, $A4, $A7, $A4, $A0, $F7, $00
    db $02, $1E, $95, $F9, $AC, $24, $AA, $A8, $AA, $18, $B1, $0C
    db $F7, $00, $03, $2A, $95, $F8, $12, $95, $F9, $02, $F8, $CC
    db $95, $A6, $0C, $AC, $B1, $B2, $F8, $CC, $95, $A6, $0C, $AC
    db $B1, $B2, $3C, $F8, $D2, $95, $A3, $09, $A5, $A6, $A8, $AA
    db $06, $AC, $AF, $09, $AD, $1B, $AC, $0C, $F7, $00, $03, $58
    db $95, $AD, $09, $AA, $AD, $06, $AF, $0C, $B1, $06, $B4, $B6
    db $1B, $B8, $03, $B9, $BB, $BD, $BB, $B9, $B8, $B6, $09, $B8
    db $B4, $06, $B6, $18, $AA, $18, $A6, $03, $A8, $AA, $AC, $AD
    db $AF, $B1, $B2, $B1, $04, $AD, $AA, $A5, $AA, $AD, $B1, $AC
    db $A9, $A5, $A9, $AC, $F8, $D2, $95, $A3, $09, $A5, $A3, $A1
    db $A0, $06, $9C, $A0, $09, $9E, $27, $AA, $30, $B6, $24, $B1
    db $0C, $B4, $04, $B1, $AF, $B1, $AF, $AD, $AF, $AD, $AC, $AD
    db $AC, $A8, $AA, $09, $B6, $57, $AA, $18, $AC, $0C, $AD, $AF
    db $18, $B1, $0C, $B2, $B1, $30, $BD, $F6, $4D, $95, $99, $0C
    db $9A, $A0, $A5, $F9, $A3, $09, $A1, $A0, $9E, $A0, $03, $9C
    db $9E, $A0, $9C, $09, $9A, $9E, $9A, $99, $06, $97, $A3, $09
    db $A1, $A0, $9E, $A0, $06, $A1, $F9, $F8, $7C, $96, $F8, $7C
    db $96, $A5, $03, $99, $99, $99, $99, $A5, $99, $99, $F7, $00
    db $02, $F3, $95, $F8, $84, $96, $F8, $84, $96, $F8, $8C, $96
    db $F8, $8C, $96, $F8, $94, $96, $F8, $8C, $96, $F8, $84, $96
    db $99, $03, $F7, $00, $0E, $16, $96, $9A, $03, $9D, $F8, $94
    db $96, $F8, $8C, $96, $F8, $84, $96, $99, $03, $F7, $00, $0C
    db $29, $96, $A5, $04, $99, $99, $F8, $84, $96, $F8, $84, $96
    db $F8, $8C, $96, $F8, $8C, $96, $F8, $94, $96, $F8, $94, $96
    db $F8, $9C, $96, $9C, $0C, $A8, $03, $9C, $06, $0F, $A8, $03
    db $9C, $9C, $A8, $9E, $0C, $AA, $03, $9E, $06, $0F, $AA, $03
    db $9E, $9E, $06, $F7, $00, $02, $55, $96, $F8, $9C, $96, $97
    db $0C, $A3, $03, $97, $06, $03, $0C, $A3, $03, $97, $97, $A3
    db $F8, $7C, $96, $F6, $01, $96, $99, $03, $F7, $00, $20, $7C
    db $96, $F9, $9A, $03, $F7, $00, $10, $84, $96, $F9, $9C, $03
    db $F7, $00, $10, $8C, $96, $F9, $9E, $03, $F7, $00, $10, $94
    db $96, $F9, $9A, $0C, $A6, $03, $9A, $06, $0F, $A6, $03, $9A
    db $9A, $06, $F9, $F8, $F1, $96, $F7, $01, $05, $A9, $96, $F5
    db $80, $70, $F8, $FC, $96, $F8, $15, $97, $F8, $15, $97, $F8
    db $15, $97, $F8, $26, $97, $F8, $15, $97, $F8, $15, $97, $A1
    db $03, $A1, $A1, $A1, $80, $A1, $A3, $06, $A5, $03, $A3, $06
    db $A1, $A3, $09, $F8, $26, $97, $F8, $FC, $96, $F5, $80, $B0
    db $A5, $60, $30, $A3, $30, $A5, $60, $A1, $30, $A3, $A1, $A0
    db $F6, $B1, $96, $94, $03, $97, $9B, $A0, $F7, $00, $04, $F1
    db $96, $F9, $9E, $09, $09, $09, $09, $06, $06, $F7, $00, $02
    db $FC, $96, $A0, $09, $09, $09, $09, $06, $06, $F7, $00, $02
    db $08, $97, $F9, $A1, $03, $A1, $A1, $A1, $80, $A1, $A3, $06
    db $A5, $03, $A3, $06, $A1, $A0, $09, $F9, $A1, $03, $A1, $A1
    db $A1, $80, $A3, $A5, $80, $A0, $A0, $A0, $A0, $80, $A1, $A3
    db $80, $F9, $9E, $03, $9E, $9E, $9E, $80, $9E, $A0, $06, $A1
    db $03, $A0, $06, $9E, $06, $9C, $09, $F9, $9E, $03, $9E, $9E
    db $9E, $80, $A0, $A1, $80, $9C, $9C, $9C, $9C, $80, $9E, $A0
    db $80, $F9, $FF, $80, $40, $F5, $80, $50, $AF, $06, $AD, $02
    db $80, $04, $AF, $06, $AD, $02, $80, $04, $AF, $02, $AF, $AD
    db $80, $F7, $00, $02, $5F, $97, $AF, $06, $AD, $02, $80, $04
    db $AF, $30, $80, $04, $F7, $01, $03, $5F, $97, $F5, $80, $73
    db $AA, $04, $AA, $AF, $B2, $B1, $AD, $A8, $AA, $A6, $A8, $A5
    db $A6, $A3, $A5, $A1, $9C, $9E, $20, $80, $AA, $04, $AA, $AF
    db $B2, $B1, $B2, $B4, $B6, $B2, $B4, $B1, $B2, $AF, $B1, $AD
    db $AF, $24, $80, $20, $F5, $80, $80, $BB, $08, $B9, $04, $B4
    db $14, $80, $04, $BB, $B9, $B4, $BB, $B9, $B4, $08, $F7, $00
    db $02, $B5, $97, $BC, $08, $BA, $04, $B5, $14, $80, $04, $BC
    db $BA, $B5, $BC, $BA, $B5, $08, $BC, $08, $BA, $04, $B5, $14
    db $80, $04, $BC, $BA, $B5, $BC, $BA, $B5, $B7, $F5, $80, $50
    db $B3, $AB, $B2, $AB, $B0, $AB, $B2, $AB, $F7, $00, $02, $EA
    db $97, $B7, $B0, $B5, $B0, $B3, $B0, $B5, $B0, $F7, $00, $02
    db $F7, $97, $B6, $AF, $B4, $AF, $B2, $AF, $B4, $AF, $F7, $00
    db $04, $04, $98, $F6, $5F, $97, $F8, $51, $98, $F8, $59, $98
    db $F8, $51, $98, $F8, $59, $98, $F8, $51, $98, $F8, $59, $98
    db $F8, $51, $98, $F8, $51, $98, $F8, $51, $98, $F8, $51, $98
    db $F8, $51, $98, $F8, $59, $98, $F8, $59, $98, $9A, $04, $F7
    db $01, $20, $3B, $98, $F8, $59, $98, $F8, $59, $98, $F8, $51
    db $98, $F8, $51, $98, $F6, $17, $98, $97, $04, $F7, $00, $10
    db $51, $98, $F9, $98, $04, $F7, $00, $10, $59, $98, $F9, $80
    db $20, $20, $F5, $80, $50, $80, $40, $20, $AF, $06, $AD, $02
    db $80, $04, $AF, $0E, $B1, $01, $B2, $B4, $B6, $B8, $B9, $BB
    db $20, $B9, $10, $B4, $B6, $08, $B7, $04, $B6, $2D, $AF, $01
    db $B1, $B2, $B4, $B6, $B8, $B9, $BB, $20, $B9, $10, $BE, $BB
    db $30, $80, $10, $F5, $80, $C0, $B6, $20, $F7, $00, $07, $98
    db $98, $B6, $04, $B4, $BB, $B6, $B4, $BB, $B6, $B4, $F8, $C4
    db $98, $BC, $B7, $FE, $FF, $BB, $02, $BB, $B6, $B6, $B2, $B2
    db $F7, $00, $0A, $AF, $98, $BB, $BB, $B6, $B6, $FE, $01, $F6
    db $64, $98, $F5, $80, $20, $BB, $04, $B6, $B4, $F7, $00, $0A
    db $C7, $98, $BB, $B6, $BC, $B7, $B5, $F7, $00, $0A, $D2, $98
    db $BC, $B7, $BC, $B7, $B3, $F7, $00, $0A, $DC, $98, $F9, $80
    db $20, $20, $FE, $FE, $F5, $80, $50, $AA, $06, $A8, $02, $80
    db $04, $AA, $06, $A8, $02, $80, $04, $AA, $02, $AA, $A8, $80
    db $F7, $00, $02, $ED, $98, $AA, $06, $A8, $02, $80, $04, $AA
    db $30, $80, $04, $F7, $01, $03, $ED, $98, $F5, $80, $C0, $A8
    db $20, $F7, $01, $08, $15, $99, $F5, $80, $70, $B6, $08, $B4
    db $04, $AF, $14, $80, $04, $B6, $B4, $AF, $B6, $B4, $AF, $08
    db $F7, $01, $02, $1F, $99, $B7, $08, $B5, $04, $B0, $14, $80
    db $04, $B7, $B5, $B0, $B7, $B5, $B0, $08, $B7, $08, $B5, $04
    db $B0, $14, $80, $04, $B7, $B5, $B0, $B7, $B5, $A6, $08, $FE
    db $02, $AB, $04, $A4, $A9, $A4, $A7, $A4, $A9, $A4, $F7, $01
    db $02, $53, $99, $B3, $AB, $B2, $AB, $B0, $AB, $B2, $AB, $F7
    db $01, $02, $61, $99, $B2, $AA, $B1, $AA, $AF, $AA, $B1, $AA
    db $F7, $01, $04, $6E, $99, $F6, $E8, $98, $04, $F5, $80, $E0
    db $80, $30, $80, $BA, $3C, $AE, $18, $B1, $0C, $B5, $15, $B3
    db $3F, $80, $0C, $80, $BA, $30, $BD, $0C, $BC, $06, $BB, $03
    db $BA, $09, $B3, $0C, $BA, $42, $80, $18, $AE, $06, $03, $09
    db $BA, $06, $B3, $BA, $B8, $12, $B6, $06, $B5, $B1, $B3, $12
    db $B1, $06, $AF, $B1, $AE, $12, $06, $AF, $B1, $B3, $06, $03
    db $09, $BF, $06, $B8, $BF, $BD, $12, $B8, $06, $BA, $BB, $BD
    db $12, $B8, $06, $BA, $BB, $BD, $48, $ED, $01, $96, $18, $E0
    db $03, $96, $18, $E0, $03, $94, $18, $E0, $03, $92, $18, $E0
    db $03, $ED, $00, $F5, $80, $50, $B3, $03, $80, $80, $B6, $80
    db $06, $B5, $12, $B5, $06, $B3, $B1, $F7, $00, $02, $E8, $99
    db $BF, $03, $80, $80, $C2, $80, $06, $C1, $12, $C1, $06, $BF
    db $BD, $F7, $00, $02, $FA, $99, $F7, $01, $02, $E8, $99, $F5
    db $80, $80, $FE, $FF, $A7, $24, $A8, $06, $03, $09, $AA, $06
    db $AC, $AA, $A9, $06, $03, $09, $AA, $06, $AC, $A9, $AA, $06
    db $03, $09, $AC, $06, $AE, $AC, $AB, $06, $03, $09, $AC, $06
    db $AE, $AB, $AC, $48, $80, $24, $FE, $01, $F6, $7F, $99, $F8
    db $DE, $9A, $ED, $01, $92, $18, $E0, $06, $ED, $00, $80, $12
    db $F8, $DE, $9A, $80, $0C, $99, $03, $98, $96, $94, $F7, $00
    db $05, $41, $9A, $8F, $06, $03, $06, $03, $8F, $9B, $8F, $99
    db $98, $99, $92, $06, $03, $06, $03, $92, $9E, $92, $99, $92
    db $9E, $97, $06, $03, $06, $03, $97, $A3, $99, $A5, $A7, $A3
    db $8F, $06, $03, $06, $03, $8F, $9E, $90, $9F, $92, $9E, $94
    db $06, $03, $06, $03, $94, $A0, $94, $9E, $94, $A0, $97, $06
    db $03, $06, $03, $97, $A3, $97, $A3, $9B, $A3, $99, $06, $03
    db $06, $03, $99, $A5, $99, $A0, $99, $A5, $90, $48, $94, $03
    db $96, $97, $99, $94, $06, $03, $06, $03, $99, $06, $06, $06
    db $97, $03, $A3, $99, $A5, $97, $A3, $F7, $00, $08, $B1, $9A
    db $94, $92, $91, $96, $8F, $8D, $8F, $92, $94, $92, $94, $97
    db $99, $24, $9A, $9B, $9C, $9D, $48, $80, $24, $F6, $41, $9A
    db $8F, $03, $9B, $8F, $99, $8F, $98, $8F, $99, $F9, $01, $80
    db $30, $80, $F8, $2F, $9B, $ED, $01, $96, $18, $E0, $03, $96
    db $18, $E0, $03, $96, $18, $E0, $03, $94, $18, $E0, $03, $94
    db $18, $E0, $03, $94, $18, $E0, $03, $92, $18, $E0, $03, $92
    db $18, $E0, $03, $92, $18, $E0, $03, $96, $18, $E0, $03, $94
    db $18, $E0, $03, $92, $18, $E0, $03, $ED, $00, $A5, $24, $A6
    db $A7, $A8, $A9, $48, $80, $24, $F6, $E9, $9A, $80, $03, $B5
    db $BA, $80, $BC, $80, $B8, $BA, $80, $B3, $B5, $80, $B1, $B0
    db $AC, $AE, $F7, $00, $08, $2F, $9B, $80, $03, $B3, $B6, $BA
    db $B8, $B5, $B6, $B3, $B5, $06, $B1, $F7, $00, $03, $45, $9B
    db $80, $03, $B3, $B6, $BA, $B8, $B5, $B6, $B3, $B6, $06, $B8
    db $80, $03, $B8, $BB, $BF, $BD, $BA, $BB, $B8, $BA, $06, $B6
    db $F7, $00, $03, $62, $9B, $80, $03, $AC, $AF, $B1, $B3, $B6
    db $B8, $36, $B8, $03, $BA, $BB, $BD, $B3, $03, $80, $80, $B6
    db $80, $06, $B5, $12, $B5, $06, $B3, $B1, $F7, $00, $02, $81
    db $9B, $BB, $03, $80, $80, $BF, $80, $06, $BD, $12, $BD, $06
    db $BB, $BD, $F7, $00, $02, $93, $9B, $F7, $01, $02, $81, $9B
    db $F9, $30, $30, $02, $F8, $2F, $9B, $80, $22, $A5, $06, $03
    db $09, $A7, $06, $A9, $A7, $A6, $06, $03, $09, $06, $A9, $06
    db $A6, $A7, $06, $03, $09, $A9, $06, $AA, $A9, $A8, $06, $03
    db $09, $A9, $06, $AA, $A8, $A9, $48, $80, $24, $F6, $AB, $9B
    db $03, $A8, $09, $AA, $09, $AF, $12, $AD, $03, $AD, $AB, $AA
    db $F7, $00, $02, $DB, $9B, $A8, $18, $AA, $AB, $30, $A8, $18
    db $AA, $AA, $2A, $A8, $06, $A7, $30, $F6, $DB, $9B, $AF, $03
    db $B0, $B6, $F7, $00, $04, $FC, $9B, $AF, $03, $B0, $B2, $B4
    db $F7, $01, $02, $FC, $9B, $F8, $41, $9C, $AF, $03, $B4, $B6
    db $B7, $B9, $B7, $B6, $B4, $AF, $B4, $B6, $B7, $B9, $BB, $BB
    db $BE, $F8, $41, $9C, $A3, $03, $A3, $AF, $06, $A3, $03, $AF
    db $A3, $A3, $F7, $02, $03, $26, $9C, $BB, $03, $B2, $B6, $BB
    db $B2, $B6, $BB, $BE, $F6, $FC, $9B, $A4, $03, $A4, $B0, $06
    db $A4, $03, $AF, $09, $A6, $03, $A6, $B2, $06, $A6, $03, $B2
    db $09, $F9, $9C, $03, $F7, $00, $20, $54, $9C, $F8, $75, $9C
    db $9C, $03, $F7, $00, $0E, $5E, $9C, $9A, $03, $9A, $F8, $75
    db $9C, $97, $03, $F7, $00, $20, $6B, $9C, $F6, $54, $9C, $98
    db $03, $F7, $00, $08, $75, $9C, $9A, $03, $F7, $00, $08, $7C
    db $9C, $F9, $B4, $03, $B6, $BB, $B4, $B6, $BB, $B4, $B6, $BB
    db $B4, $B6, $BB, $B4, $B6, $B7, $B9, $F7, $00, $02, $84, $9C
    db $F8, $D5, $9C, $B6, $03, $B7, $BB, $BE, $C2, $BE, $BB, $B7
    db $B6, $B7, $BB, $BE, $C2, $C3, $C5, $C7, $F8, $D5, $9C, $B4
    db $03, $BB, $C0, $B6, $BB, $C0, $B6, $BB, $C0, $B6, $BB, $C0
    db $B6, $BB, $C0, $BB, $B6, $BB, $BF, $B6, $BB, $BF, $B6, $BB
    db $AF, $B3, $B6, $AF, $B3, $B6, $AF, $B3, $F6, $84, $9C, $AB
    db $03, $AB, $B7, $06, $AB, $03, $B7, $06, $AB, $03, $AD, $AD
    db $B9, $06, $AD, $03, $B9, $09, $F9, $03, $BA, $06, $B1, $B5
    db $0C, $B3, $AE, $B1, $18, $B0, $0C, $AC, $AE, $30, $80, $F6
    db $EA, $9C, $96, $18, $9B, $9E, $A0, $96, $9B, $96, $9B, $F6
    db $FC, $9C, $02, $F8, $24, $9D, $B1, $06, $AE, $AA, $AE, $B3
    db $B0, $AC, $B0, $F8, $24, $9D, $80, $06, $BA, $B5, $B1, $B3
    db $B7, $BA, $BF, $F6, $09, $9D, $80, $06, $BA, $B5, $B1, $B3
    db $B1, $AE, $B0, $F9, $02, $F5, $80, $C0, $B7, $06, $BC, $BF
    db $C1, $BE, $BA, $BF, $BC, $B8, $BE, $BA, $B5, $F7, $00, $04
    db $32, $9D, $F5, $09, $70, $B3, $24, $B5, $B7, $1E, $B3, $06
    db $BC, $24, $B5, $24, $B7, $BA, $1E, $B5, $06, $BE, $18, $BC
    db $06, $BA, $BC, $48, $BE, $24, $BF, $BF, $24, $C1, $C3, $48
    db $F8, $D8, $9D, $CB, $06, $CA, $CB, $C8, $36, $F5, $08, $50
    db $BC, $24, $BA, $12, $B5, $06, $B7, $B8, $BA, $12, $B8, $B7
    db $B3, $BC, $24, $BA, $12, $BE, $BC, $48, $BC, $24, $BA, $12
    db $B5, $06, $B7, $B8, $BA, $12, $B8, $B7, $B3, $BC, $24, $BE
    db $BF, $12, $BE, $BC, $BA, $F5, $09, $60, $BC, $24, $BE, $12
    db $BF, $BA, $24, $BC, $12, $BA, $B8, $24, $BA, $12, $BC, $BC
    db $24, $BB, $BC, $24, $BE, $12, $BF, $BE, $24, $BF, $12, $C1
    db $BF, $48, $F8, $D8, $9D, $F5, $00, $73, $CB, $06, $CA, $CB
    db $C8, $36, $EF, $01, $C8, $48, $EF, $01, $C8, $59, $EF, $01
    db $C8, $36, $EF, $01, $10, $F2, $BC, $06, $BE, $BF, $BE, $BC
    db $BA, $BC, $24, $BC, $06, $BE, $BF, $BE, $BC, $BA, $BC, $12
    db $B8, $BA, $06, $BC, $BE, $BF, $C1, $C3, $C4, $C3, $C1, $BF
    db $BE, $BA, $BC, $12, $BE, $BF, $C1, $C3, $06, $BC, $C3, $BC
    db $24, $BC, $06, $BF, $C1, $C3, $06, $BC, $C3, $BC, $24, $C8
    db $12, $C6, $24, $CA, $12, $CD, $F9, $F5, $80, $80, $98, $48
    db $48, $F5, $80, $20, $98, $12, $F7, $00, $10, $1E, $9E, $96
    db $12, $F7, $00, $08, $25, $9E, $94, $12, $F7, $00, $08, $2C
    db $9E, $93, $12, $F7, $00, $06, $33, $9E, $93, $06, $F7, $00
    db $06, $3A, $9E, $F8, $9C, $9E, $98, $48, $94, $24, $96, $98
    db $98, $94, $96, $98, $36, $96, $12, $94, $24, $96, $9B, $98
    db $94, $96, $98, $06, $F7, $00, $0C, $58, $9E, $F8, $C6, $9E
    db $F8, $D0, $9E, $91, $06, $9D, $91, $F7, $00, $04, $65, $9E
    db $93, $06, $9F, $93, $F7, $00, $04, $6E, $9E, $F8, $C6, $9E
    db $F8, $D0, $9E, $98, $06, $F7, $00, $06, $7D, $9E, $94, $06
    db $A0, $94, $96, $A2, $96, $F8, $9C, $9E, $F5, $0A, $73, $EF
    db $02, $98, $6C, $24, $98, $6C, $35, $A4, $2E, $F2, $F8, $BC
    db $9E, $F8, $C6, $9E, $F8, $D0, $9E, $98, $06, $A4, $98, $96
    db $A2, $96, $94, $A0, $94, $93, $9F, $93, $F8, $BC, $9E, $F8
    db $C6, $9E, $F8, $D0, $9E, $F9, $98, $06, $A4, $98, $F7, $00
    db $04, $BC, $9E, $F9, $94, $06, $A0, $94, $F7, $00, $04, $C6
    db $9E, $F9, $96, $06, $A2, $96, $F7, $00, $04, $D0, $9E, $F9
    db $B7, $03, $B8, $F7, $00, $18, $DA, $9E, $F5, $80, $C0, $EF
    db $FE, $B0, $06, $B3, $B7, $B8, $B5, $B2, $B7, $B3, $B0, $B5
    db $B2, $AE, $F7, $00, $02, $E7, $9E, $F5, $80, $F0, $EF, $02
    db $BC, $03, $B7, $F7, $00, $54, $FE, $9E, $BE, $03, $B7, $F7
    db $00, $0C, $06, $9F, $F5, $0B, $50, $EF, $FF, $F8, $BC, $9F
    db $A6, $AB, $06, $A9, $AB, $A7, $AB, $B0, $B3, $B7, $BC, $18
    db $F5, $08, $C0, $F8, $EF, $9F, $F8, $FE, $9F, $F8, $06, $A0
    db $F8, $EF, $9F, $F8, $06, $A0, $F8, $06, $A0, $F8, $EF, $9F
    db $F8, $FE, $9F, $F8, $06, $A0, $F8, $EF, $9F, $BC, $06, $B7
    db $B3, $B7, $B3, $B0, $F7, $00, $02, $43, $9F, $F5, $0B, $F0
    db $F8, $10, $A0, $B2, $03, $AE, $A9, $AE, $A9, $A6, $F7, $00
    db $04, $55, $9F, $B0, $03, $AC, $A9, $AC, $A9, $A4, $F7, $00
    db $04, $61, $9F, $B2, $03, $AF, $AB, $AF, $AB, $A6, $F7, $00
    db $04, $6D, $9F, $F8, $10, $A0, $B2, $03, $AE, $A9, $AE, $A9
    db $AE, $F7, $00, $04, $7C, $9F, $80, $24, $A7, $12, $A9, $F5
    db $80, $50, $F8, $BC, $9F, $A6, $AB, $06, $A7, $A4, $A7, $A9
    db $A6, $A7, $A6, $9D, $A6, $A2, $9A, $F7, $00, $03, $94, $9F
    db $AB, $07, $A7, $A4, $A7, $A9, $A6, $A7, $A6, $08, $9D, $A6
    db $A2, $9A, $EF, $01, $AB, $05, $A9, $AB, $3C, $F2, $F8, $D0
    db $9F, $A6, $A7, $B3, $A7, $A6, $B2, $A6, $A4, $B0, $A4, $A6
    db $B2, $A6, $F8, $D0, $9F, $F9, $AB, $06, $B0, $B3, $B5, $B2
    db $AE, $B3, $B0, $AC, $B2, $AE, $A9, $F7, $00, $02, $D0, $9F
    db $B2, $06, $AE, $A9, $AE, $A9, $A6, $B2, $AE, $A9, $AE, $A9
    db $F9, $BC, $06, $B8, $B3, $BC, $B8, $B3, $BA, $06, $B5, $B2
    db $BA, $B5, $B2, $F9, $BA, $06, $B7, $B3, $BA, $B7, $B3, $F9
    db $BC, $06, $B7, $B3, $F7, $00, $02, $06, $A0, $F9, $B0, $03
    db $AC, $A7, $AC, $A7, $A4, $F7, $00, $04, $10, $A0, $F9, $80
    db $24, $F7, $00, $08, $1D, $A0, $F5, $80, $90, $B0, $24, $B2
    db $B3, $B7, $AE, $24, $B0, $B2, $BA, $B8, $24, $BA, $BC, $BE
    db $BC, $48, $BB, $F5, $80, $50, $FE, $02, $80, $03, $F8, $BC
    db $9F, $A6, $80, $45, $FE, $FE, $F5, $80, $90, $AC, $24, $AE
    db $B3, $B0, $AC, $A9, $AB, $A4, $06, $A7, $AB, $B0, $B3, $B7
    db $F8, $B1, $A0, $B7, $06, $B3, $AE, $B7, $B3, $AE, $B7, $B3
    db $B0, $B7, $B3, $B0, $F8, $B1, $A0, $B3, $06, $B0, $AB, $B0
    db $AB, $A7, $B3, $B0, $AB, $B0, $AB, $A7, $B8, $24, $BA, $12
    db $BC, $BA, $24, $B8, $12, $B7, $B5, $24, $B7, $12, $B8, $B8
    db $24, $B7, $B8, $BA, $12, $BC, $BA, $24, $BC, $12, $BE, $BC
    db $24, $B3, $12, $B5, $FE, $02, $F5, $80, $50, $80, $03, $F8
    db $BC, $9F, $A6, $F6, $94, $9F, $80, $48, $48, $F7, $00, $04
    db $A8, $A0, $F9, $B8, $06, $B3, $B0, $B8, $B3, $B0, $B5, $B2
    db $AE, $B5, $B2, $AE, $F9, $AC, $30, $EF, $FF, $AD, $18, $EF
    db $FF, $AF, $18, $EF, $FF, $AC, $30, $EF, $FF, $AD, $18, $EF
    db $FF, $AF, $18, $AC, $18, $AF, $AE, $AD, $F7, $00, $04, $D5
    db $A0, $A5, $03, $AC, $A5, $A5, $AD, $A5, $A5, $AC, $A5, $A5
    db $AA, $A5, $A8, $A7, $A8, $AA, $A5, $AC, $A5, $A5, $B1, $A5
    db $A5, $AF, $A5, $A5, $B1, $A5, $AF, $AD, $AC, $AA, $F7, $00
    db $02, $DF, $A0, $F6, $D5, $A0, $EF, $06, $99, $03, $A0, $99
    db $99, $99, $A1, $99, $A0, $EF, $FF, $99, $03, $99, $9E, $99
    db $9C, $9B, $9C, $9E, $EF, $FF, $99, $A0, $99, $99, $A1, $99
    db $99, $A3, $EF, $FF, $99, $99, $A5, $99, $A3, $A1, $A0, $9E
    db $F7, $00, $02, $0A, $A1, $99, $03, $A5, $99, $99, $A5, $99
    db $99, $A5, $9C, $A8, $9C, $9C, $A8, $9C, $9C, $A8, $9E, $AA
    db $9E, $9E, $AA, $9E, $9E, $AA, $A1, $AD, $A1, $A1, $AD, $A1
    db $A1, $AD, $F7, $00, $04, $37, $A1, $F8, $63, $A1, $F6, $37
    db $A1, $99, $03, $A0, $99, $99, $A1, $99, $99, $A0, $99, $99
    db $9E, $99, $9C, $9B, $9C, $9E, $99, $A0, $99, $99, $A1, $99
    db $99, $A3, $99, $99, $A5, $99, $A3, $A1, $A0, $9E, $F7, $00
    db $02, $63, $A1, $F9, $01, $B8, $03, $B1, $B1, $B8, $B1, $B1
    db $B8, $B1, $B8, $B1, $B1, $B8, $B1, $B1, $B8, $B1, $EF, $FF
    db $F7, $00, $04, $8B, $A1, $F8, $BB, $A1, $F8, $AC, $A1, $F6
    db $A3, $A1, $B8, $03, $B1, $B1, $B8, $B1, $B1, $B8, $B1, $F7
    db $00, $08, $AC, $A1, $F9, $B8, $03, $B1, $B1, $B8, $B1, $B1
    db $B8, $B1, $BB, $B4, $B4, $BB, $B4, $B4, $BB, $B4, $BA, $B6
    db $B6, $BA, $B6, $B6, $BA, $B6, $BD, $B6, $B6, $BD, $B6, $B6
    db $BD, $B6, $F7, $00, $04, $BB, $A1, $F9, $02, $AF, $03, $AC
    db $AE, $AC, $F6, $E3, $A1, $01, $02, $94, $0C, $8F, $92, $93
    db $F6, $ED, $A1, $01, $AE, $06, $A5, $AA, $AE, $0C, $AC, $06
    db $AA, $AC, $AE, $06, $A5, $AA, $AE, $0C, $AC, $06, $AE, $AF
    db $B1, $18, $BD, $F2, $9E, $18, $9C, $F7, $00, $02, $0E, $A2
    db $9E, $30, $F2, $AE, $18, $A0, $F7, $00, $02, $19, $A2, $A2
    db $30, $F2, $FF, $03, $AE, $06, $B1, $B3, $24, $B6, $0C, $B5
    db $24, $B1, $06, $AC, $AC, $12, $AE, $1E, $80, $24, $AE, $06
    db $B1, $B3, $24, $B6, $0C, $B5, $24, $B1, $06, $B3, $B5, $24
    db $B8, $0C, $B8, $12, $B6, $AE, $06, $B1, $B3, $24, $BA, $0C
    db $B8, $06, $80, $B5, $80, $12, $B1, $06, $80, $B1, $12, $B3
    db $1E, $80, $24, $AE, $06, $B1, $F6, $29, $A2, $80, $0C, $F8
    db $94, $A2, $F8, $9D, $A2, $F8, $94, $A2, $96, $12, $06, $96
    db $12, $06, $8F, $12, $06, $0C, $9B, $06, $99, $97, $12, $06
    db $97, $12, $06, $96, $06, $80, $96, $80, $12, $96, $06, $80
    db $F8, $9D, $A2, $F6, $69, $A2, $97, $12, $06, $F7, $00, $04
    db $94, $A2, $F9, $8F, $12, $06, $F7, $00, $04, $9D, $A2, $F9
    db $03, $80, $0C, $F8, $E9, $A2, $F8, $F4, $A2, $F8, $FE, $A2
    db $9B, $06, $A2, $A9, $A7, $A7, $A2, $AA, $A7, $F8, $E9, $A2
    db $F8, $F4, $A2, $F8, $F4, $A2, $A9, $06, $A5, $A2, $A7, $0C
    db $A2, $06, $AA, $A7, $F8, $E9, $A2, $A9, $06, $80, $A5, $80
    db $12, $A2, $06, $80, $F8, $FE, $A2, $9B, $06, $9D, $9E, $A2
    db $A7, $A9, $AA, $AE, $F6, $A9, $A2, $AE, $06, $AA, $A7, $AA
    db $F7, $00, $02, $E9, $A2, $F9, $B1, $06, $AC, $A9, $AC, $B1
    db $AC, $A9, $A5, $F9, $A9, $06, $A5, $A2, $AA, $A7, $A2, $9E
    db $A2, $F9, $01, $B2, $06, $AD, $B2, $B4, $B6, $B2, $B6, $B9
    db $BD, $08, $B8, $B6, $0A, $B3, $B5, $20, $F2, $97, $30, $99
    db $44, $F2, $9E, $18, $A6, $A0, $44, $F2, $80, $30, $30, $FF
    db $C0, $C1, $B0, $0F, $B6, $F2, $74, $D0, $F8, $5A, $A3, $B8
    db $06, $03, $BA, $27, $F8, $5A, $A3, $B8, $0C, $BA, $BB, $BD
    db $BD, $09, $BB, $B6, $12, $B3, $06, $B6, $BD, $09, $BB, $B6
    db $0C, $B2, $06, $B6, $BB, $BB, $09, $BA, $57, $F6, $32, $A3
    db $80, $03, $B1, $B6, $B8, $BA, $0C, $BB, $06, $BA, $B8, $B6
    db $F9, $F8, $83, $A3, $F8, $83, $A3, $90, $06, $9C, $F7, $00
    db $08, $6D, $A3, $97, $06, $A3, $F7, $00, $08, $75, $A3, $F8
    db $83, $A3, $F6, $6A, $A3, $92, $06, $9E, $F7, $00, $08, $83
    db $A3, $F9, $F8, $B9, $A3, $F8, $B9, $A3, $F8, $B9, $A3, $80
    db $06, $A7, $03, $03, $80, $06, $A7, $03, $80, $F7, $01, $02
    db $95, $A3, $80, $06, $A6, $03, $03, $80, $06, $A6, $03, $80
    db $F7, $01, $02, $A4, $A3, $F8, $B9, $A3, $F6, $8F, $A3, $80
    db $06, $AE, $03, $03, $80, $06, $AE, $03, $80, $F7, $00, $04
    db $B9, $A3, $F9, $80, $06, $A5, $03, $03, $80, $06, $A5, $03
    db $80, $F7, $00, $04, $C9, $A3, $F9, $03, $80, $60, $80, $F5
    db $80, $70, $A8, $0C, $AB, $06, $AF, $2A, $B0, $0C, $AF, $AE
    db $AF, $0C, $A8, $06, $AB, $2A, $AA, $0C, $AB, $AD, $AF, $0C
    db $AB, $06, $A8, $2A, $A7, $0C, $A8, $AA, $AB, $0C, $AF, $06
    db $B4, $2A, $AF, $0C, $AE, $AF, $B0, $0C, $AD, $06, $A8, $1E
    db $B0, $0C, $AD, $06, $A8, $0C, $A8, $06, $A7, $A8, $B0, $0C
    db $AD, $06, $A8, $1E, $B0, $0C, $B2, $06, $B4, $0C, $B2, $06
    db $B0, $0C, $AF, $06, $06, $06, $06, $80, $0C, $AF, $06, $B0
    db $1E, $BC, $03, $BC, $B7, $B7, $B4, $B4, $B0, $B0, $AF, $06
    db $06, $06, $06, $80, $0C, $AF, $06, $B0, $1E, $AF, $0C, $B3
    db $F5, $80, $A0, $F8, $72, $A4, $BB, $03, $BD, $BF, $1E, $BB
    db $0C, $FB, $0C, $0C, $F8, $72, $A4, $BB, $03, $AF, $AF, $AF
    db $AF, $03, $B3, $B1, $B3, $F7, $00, $03, $62, $A4, $FB, $F4
    db $F4, $F6, $DA, $A3, $B4, $03, $B3, $B4, $B6, $09, $B7, $06
    db $B6, $03, $B4, $15, $B6, $03, $B4, $B6, $B7, $09, $B9, $06
    db $B7, $03, $B6, $15, $B7, $03, $B9, $BB, $12, $B9, $03, $BB
    db $BC, $12, $F9, $9C, $18, $9B, $9A, $9B, $F7, $00, $06, $95
    db $A4, $A1, $A0, $9F, $A0, $A1, $A0, $9F, $A0, $97, $06, $97
    db $97, $97, $80, $0C, $97, $06, $98, $36, $97, $06, $97, $97
    db $97, $80, $0C, $97, $06, $98, $1E, $97, $0C, $9B, $F8, $E3
    db $A4, $A3, $03, $80, $A3, $A3, $A3, $80, $A3, $A3, $A3, $80
    db $A3, $A3, $A3, $80, $97, $97, $F8, $E3, $A4, $A3, $06, $97
    db $97, $97, $97, $97, $97, $9B, $F6, $95, $A4, $9C, $03, $80
    db $9C, $9C, $9C, $80, $9C, $9C, $9C, $80, $9C, $9C, $9C, $80
    db $90, $90, $9E, $80, $9E, $9E, $9E, $80, $9E, $9E, $9E, $80
    db $9E, $9E, $9E, $80, $92, $92, $9F, $80, $9F, $9F, $9F, $80
    db $9F, $9F, $A1, $80, $A1, $A1, $A1, $80, $A1, $A1, $F9, $B4
    db $03, $B7, $BB, $B7, $F7, $00, $30, $15, $A5, $B9, $BB, $C0
    db $BB, $F7, $00, $10, $1F, $A5, $AA, $06, $06, $06, $06, $80
    db $0C, $AA, $06, $AB, $36, $AA, $06, $06, $06, $06, $80, $0C
    db $AA, $06, $AB, $1E, $AA, $0C, $AF, $F8, $5A, $A5, $AF, $03
    db $AF, $AF, $12, $BB, $03, $BB, $B6, $B6, $B3, $B3, $AF, $AF
    db $F8, $5A, $A5, $AF, $30, $F6, $15, $A5, $A8, $03, $AA, $AB
    db $F7, $00, $05, $5A, $A5, $A8, $AA, $AB, $AD, $F7, $00, $05
    db $64, $A5, $AA, $AB, $AD, $AF, $AB, $AD, $AF, $AD, $AF, $AD
    db $AF, $B0, $AD, $AF, $B0, $AD, $AF, $F9, $01, $F8, $BD, $A5
    db $A7, $60, $F8, $BD, $A5, $A3, $06, $A0, $5A, $F8, $CE, $A5
    db $AC, $0C, $A0, $A3, $06, $A5, $A3, $A7, $1E, $A8, $0C, $AA
    db $F8, $CE, $A5, $AC, $18, $06, $AE, $06, $AF, $AE, $12, $0C
    db $AF, $0C, $B1, $B3, $60, $60, $A8, $18, $A0, $06, $A3, $A8
    db $AA, $12, $0C, $A5, $0C, $A2, $A4, $60, $F6, $7F, $A5, $A7
    db $18, $AC, $06, $AA, $0C, $A5, $06, $A3, $18, $A2, $06, $A3
    db $0C, $A5, $06, $F9, $AC, $09, $AE, $AF, $1E, $AE, $09, $AC
    db $AA, $1E, $F9, $F8, $55, $A6, $F8, $93, $A6, $F8, $55, $A6
    db $F8, $55, $A6, $F8, $55, $A6, $F8, $93, $A6, $F8, $55, $A6
    db $F8, $55, $A6, $F8, $60, $A6, $A5, $06, $03, $03, $F7, $00
    db $04, $F4, $A5, $A3, $06, $03, $03, $F7, $00, $04, $FD, $A5
    db $F8, $60, $A6, $A5, $06, $03, $B1, $03, $F7, $00, $04, $09
    db $A6, $A7, $06, $03, $B3, $03, $F7, $00, $04, $13, $A6, $AC
    db $06, $A0, $03, $AC, $06, $A0, $03, $AC, $06, $AA, $06, $9E
    db $03, $AA, $06, $9E, $03, $AA, $06, $F8, $79, $A6, $A8, $06
    db $03, $B4, $03, $F7, $00, $04, $34, $A6, $AA, $06, $03, $B6
    db $03, $F7, $00, $04, $3E, $A6, $A0, $06, $03, $AC, $03, $F7
    db $00, $08, $48, $A6, $F6, $D9, $A5, $A0, $06, $AC, $03, $03
    db $F7, $00, $04, $55, $A6, $F9, $A8, $09, $A8, $A8, $A8, $03
    db $AC, $AF, $B4, $AF, $AC, $AF, $A7, $09, $A7, $A7, $A7, $03
    db $AA, $AE, $B3, $AE, $AA, $AE, $F9, $A8, $06, $9C, $03, $A8
    db $06, $9C, $03, $A8, $06, $AA, $06, $9E, $03, $AA, $06, $9E
    db $03, $AA, $06, $F7, $00, $03, $79, $A6, $F9, $9C, $06, $A8
    db $03, $03, $F7, $00, $02, $93, $A6, $9E, $06, $AA, $03, $03
    db $F7, $01, $02, $9D, $A6, $F9, $01, $A0, $30, $A7, $18, $A5
    db $A2, $30, $80, $06, $AE, $03, $AE, $AE, $AE, $F7, $00, $02
    db $B0, $A6, $80, $0C, $A0, $30, $A7, $18, $AA, $AC, $48, $A0
    db $03, $A2, $A3, $A5, $A3, $A2, $A0, $9E, $F8, $F9, $A6, $A3
    db $18, $A5, $A7, $AA, $F8, $F9, $A6, $A8, $18, $06, $AA, $06
    db $AC, $AB, $12, $0C, $AF, $0C, $B1, $B3, $30, $B1, $18, $AF
    db $0C, $AE, $F7, $00, $02, $E5, $A6, $AC, $30, $AE, $B0, $60
    db $F6, $A9, $A6, $9C, $09, $9E, $A0, $1E, $9E, $09, $9C, $9B
    db $1E, $F9, $03, $80, $18, $80, $0C, $A9, $03, $80, $09, $AA
    db $12, $80, $06, $AC, $12, $AA, $18, $80, $06, $80, $0C, $A9
    db $03, $80, $09, $AA, $12, $80, $06, $A7, $12, $A9, $18, $80
    db $06, $80, $0C, $A9, $03, $80, $09, $AA, $12, $80, $06, $AC
    db $12, $AA, $18, $80, $06, $80, $0C, $A9, $03, $80, $09, $AA
    db $12, $80, $06, $A0, $12, $A9, $18, $80, $06, $F8, $2B, $A8
    db $A2, $18, $80, $06, $A2, $A5, $AA, $80, $06, $A9, $80, $AC
    db $80, $A9, $A7, $A5, $A7, $0C, $80, $06, $A2, $0C, $80, $06
    db $A5, $80, $A4, $0C, $A5, $06, $A7, $80, $A0, $0C, $80, $06
    db $F8, $2B, $A8, $A2, $0C, $80, $06, $A5, $80, $AA, $AC, $AA
    db $A1, $0C, $80, $06, $A5, $80, $AA, $AC, $AA, $A9, $1E, $A7
    db $06, $A0, $AC, $2A, $80, $0C, $AE, $1E, $80, $06, $AE, $B1
    db $1E, $80, $06, $B1, $B0, $B1, $36, $80, $06, $B0, $80, $B0
    db $80, $AE, $AC, $0C, $F7, $00, $02, $8C, $A7, $AE, $24, $B0
    db $06, $B1, $12, $A7, $0C, $A9, $AC, $A9, $12, $A2, $A9, $0C
    db $A9, $12, $A0, $A9, $0C, $A4, $24, $A0, $06, $A2, $12, $A0
    db $0C, $9D, $A0, $9D, $18, $A2, $0C, $A4, $06, $A0, $12, $9B
    db $9D, $A4, $0C, $A5, $06, $A4, $0C, $A2, $9D, $06, $F7, $00
    db $02, $CF, $A7, $A4, $0C, $A5, $06, $A4, $0C, $A2, $A7, $12
    db $A5, $0C, $A4, $A5, $A4, $0C, $A5, $06, $A4, $0C, $A2, $9D
    db $06, $F7, $00, $02, $EA, $A7, $A4, $0C, $A5, $06, $A4, $0C
    db $A2, $A7, $12, $AC, $0C, $B0, $B3, $B0, $2A, $B1, $06, $24
    db $80, $0C, $A7, $03, $A0, $A4, $A7, $AC, $03, $A4, $A7, $AC
    db $B0, $A7, $AC, $B0, $B3, $AC, $B0, $B3, $F7, $00, $02, $11
    db $A8, $B8, $03, $B0, $B3, $B8, $F6, $07, $A7, $A7, $06, $A9
    db $80, $A9, $80, $A7, $A5, $AC, $18, $80, $06, $AE, $0C, $AC
    db $B1, $0C, $80, $06, $AE, $0C, $AC, $0C, $80, $06, $A9, $0C
    db $A7, $06, $A5, $80, $A9, $80, $A0, $F9, $80, $18, $F8, $E3
    db $A8, $99, $06, $A5, $03, $03, $F7, $00, $08, $53, $A8, $99
    db $06, $A5, $F7, $00, $04, $5D, $A8, $98, $06, $A4, $F7, $01
    db $04, $65, $A8, $96, $06, $A2, $F7, $02, $04, $6D, $A8, $F8
    db $F8, $A8, $92, $06, $9E, $F7, $00, $04, $78, $A8, $91, $06
    db $9D, $F7, $01, $04, $80, $A8, $8F, $06, $9B, $F7, $02, $04
    db $88, $A8, $F8, $F8, $A8, $99, $06, $F7, $00, $08, $93, $A8
    db $98, $06, $F7, $01, $08, $9A, $A8, $96, $06, $F7, $02, $08
    db $A1, $A8, $94, $06, $F7, $00, $08, $A8, $A8, $92, $06, $F7
    db $01, $10, $AF, $A8, $94, $06, $F7, $02, $10, $B6, $A8, $F8
    db $01, $A9, $F8, $01, $A9, $F8, $2A, $A9, $F8, $35, $A9, $F8
    db $40, $A9, $F8, $35, $A9, $F7, $01, $04, $C3, $A8, $F8, $2A
    db $A9, $F8, $2A, $A9, $F8, $35, $A9, $F8, $35, $A9, $F6, $50
    db $A8, $99, $06, $A5, $03, $03, $F7, $00, $07, $E3, $A8, $A2
    db $06, $A0, $03, $03, $F7, $01, $03, $E3, $A8, $F9, $94, $06
    db $A0, $F7, $00, $04, $F8, $A8, $F9, $A2, $03, $A2, $AE, $AE
    db $F7, $00, $04, $01, $A9, $A0, $03, $A0, $AC, $AC, $F7, $01
    db $04, $0B, $A9, $9E, $03, $9E, $AA, $AA, $F7, $02, $04, $15
    db $A9, $A0, $03, $A0, $AC, $AC, $F7, $00, $04, $1F, $A9, $F9
    db $A2, $06, $AE, $03, $AE, $F7, $00, $04, $2A, $A9, $F9, $A0
    db $06, $AC, $03, $AC, $F7, $00, $04, $35, $A9, $F9, $9E, $06
    db $AA, $03, $AA, $F7, $00, $04, $40, $A9, $F9, $01, $80, $18
    db $F8, $F1, $A9, $80, $0C, $A5, $03, $80, $09, $A5, $12, $80
    db $06, $A4, $12, $A5, $18, $80, $06, $F8, $F1, $A9, $F8, $F1
    db $A9, $F8, $02, $AA, $80, $06, $AA, $80, $AA, $80, $AA, $A9
    db $A7, $80, $06, $AC, $80, $AC, $80, $AC, $AA, $A9, $AA, $0C
    db $A9, $06, $AA, $80, $AA, $80, $AA, $AC, $0C, $AA, $06, $AC
    db $80, $AA, $80, $AA, $F8, $02, $AA, $A5, $0C, $80, $06, $A2
    db $0C, $A0, $9E, $06, $A5, $0C, $80, $06, $A1, $0C, $A0, $9E
    db $06, $A0, $12, $9B, $0C, $A0, $A4, $06, $A7, $06, $A0, $A4
    db $A7, $AC, $A4, $A7, $AC, $AE, $1E, $80, $06, $B0, $B1, $1E
    db $80, $06, $B1, $B0, $B1, $36, $80, $06, $AC, $80, $AC, $80
    db $A9, $A7, $0C, $F7, $00, $02, $B3, $A9, $F8, $58, $AA, $F8
    db $58, $AA, $F8, $58, $AA, $F8, $58, $AA, $A2, $03, $A5, $A9
    db $A5, $F7, $00, $08, $DA, $A9, $A0, $03, $A0, $AC, $A0, $F7
    db $00, $08, $E4, $A9, $F6, $4E, $A9, $80, $0C, $A5, $03, $80
    db $09, $A5, $12, $80, $06, $A7, $12, $A5, $18, $80, $06, $F9
    db $80, $06, $A5, $80, $A5, $80, $A0, $0C, $80, $06, $A7, $0C
    db $A9, $06, $A5, $0C, $A7, $0C, $80, $06, $A9, $0C, $80, $06
    db $A2, $0C, $80, $06, $A9, $0C, $A9, $80, $06, $A0, $0C, $80
    db $06, $A9, $0C, $F9, $A7, $06, $A9, $80, $A9, $80, $A7, $A5
    db $AC, $18, $80, $06, $AE, $0C, $AC, $B1, $0C, $80, $06, $AE
    db $0C, $AC, $0C, $80, $06, $A9, $0C, $A7, $06, $A5, $80, $A9
    db $80, $A5, $F9, $A2, $03, $A5, $A9, $A5, $F7, $00, $0C, $4D
    db $AA, $F9, $F8, $4D, $AA, $A0, $03, $A4, $A9, $A4, $F7, $00
    db $04, $5B, $AA, $F9, $80, $0C, $A2, $03, $80, $09, $A2, $12
    db $80, $06, $A4, $12, $A2, $18, $80, $06, $F9
RegularSongDescriptors21:
    db $04, $80, $80, $02, $57, $8D, $03, $01, $0D, $02, $80, $A0
    db $02, $01, $8E, $F7, $00, $05, $03, $80, $C0, $02, $43, $8E
    db $F7, $00, $0B, $04, $C0, $E0, $02, $80, $AD, $00, $00, $00
    db $0F, $04, $80, $80, $02, $B5, $8E, $F9, $01, $08, $03, $80
    db $A0, $02, $0F, $8F, $ED, $00, $08, $03, $80, $C0, $02, $85
    db $8F, $F9, $00, $0D, $05, $C0, $E0, $02, $AE, $AD, $00, $00
    db $00, $0F, $04, $80, $80, $02, $E0, $8F, $E8, $01, $00, $02
    db $80, $A0, $02, $1A, $90, $F4, $00, $09, $03, $80, $C0, $02
    db $26, $90, $F4, $00, $05, $03, $C0, $E0, $02, $FD, $AD, $00
    db $00, $00, $0F, $04, $80, $80, $02, $5C, $90, $F4, $00, $08
    db $02, $80, $A0, $02, $42, $91, $F4, $00, $08, $03, $80, $C0
    db $02, $60, $92, $E8, $00, $08, $04, $C0, $E0, $02, $FE, $AD
    db $00, $00, $00, $0F, $04, $80, $80, $02, $7A, $93, $EE, $01
    db $0D, $02, $80, $A0, $02, $2A, $94, $EE, $00, $06, $03, $80
    db $C0, $02, $AB, $94, $EE, $00, $08, $04, $C0, $E0, $02, $D7
    db $AE, $00, $00, $00, $0F, $04, $80, $80, $02, $3C, $95, $F8
    db $01, $0A, $02, $80, $A0, $02, $ED, $95, $EC, $00, $08, $01
    db $80, $C0, $02, $A9, $96, $F8, $00, $0B, $04, $C0, $E0, $02
    db $D8, $AE, $00, $00, $00, $0F, $04, $80, $80, $03, $5D, $97
    db $EB, $01, $0E, $02, $80, $A0, $03, $14, $98, $EB, $00, $0B
    db $03, $80, $C0, $03, $61, $98, $EB, $00, $0B, $04, $C0, $E0
    db $03, $C0, $AF, $00, $00, $00, $0F, $04, $80, $80, $02, $7F
    db $99, $EB, $00, $0A, $01, $80, $A0, $02, $41, $9A, $F7, $00
    db $08, $03, $80, $C0, $02, $E9, $9A, $EB, $00, $0A, $04, $C0
    db $E0, $02, $02, $B0, $00, $00, $00, $0F, $04, $80, $80, $02
    db $DB, $9B, $EB, $01, $00, $04, $80, $A0, $02, $54, $9C, $EB
    db $00, $09, $03, $80, $C0, $02, $84, $9C, $EB, $00, $07, $03
    db $C0, $E0, $02, $6A, $B0, $00, $00, $00, $0F, $04, $80, $80
    db $02, $EA, $9C, $F4, $01, $0B, $02, $80, $A0, $02, $FC, $9C
    db $F4, $00, $0B, $03, $80, $C0, $02, $09, $9D, $F4, $00, $0B
    db $04, $C0, $E0, $02, $8C, $B0, $00, $00, $00, $0F, $04, $80
    db $80, $02, $2F, $9D, $E2, $01, $0A, $02, $80, $A0, $02, $15
    db $9E, $EE, $00, $08, $03, $80, $C0, $02, $DA, $9E, $EE, $00
    db $08, $05, $C0, $E0, $02, $8D, $B0, $00, $00, $00, $0F, $04
    db $80, $80, $01, $BF, $A0, $EB, $01, $0E, $06, $80, $A0, $01
    db $08, $A1, $EB, $00, $08, $03, $80, $C0, $01, $8B, $A1, $EB
    db $00, $08, $08, $C0, $E0, $01, $F7, $B0, $00, $00, $00, $0F
    db $04, $80, $80, $01, $E2, $A1, $E2, $00, $05, $02, $80, $A0
    db $01, $E2, $A1, $E2, $00, $05, $03, $80, $C0, $01, $E2, $A1
    db $EE, $00, $05, $04, $C0, $E0, $01, $39, $B1, $00, $00, $00
    db $0F, $04, $80, $80, $05, $E3, $A1, $F7, $00, $08, $05, $80
    db $A0, $05, $ED, $A1, $F7, $01, $0E, $02, $80, $C0, $05, $E2
    db $A1, $F7, $00, $08, $05, $C0, $E0, $05, $39, $B1, $00, $00
    db $00, $0F, $04, $80, $80, $04, $F6, $A1, $EB, $01, $0E, $02
    db $80, $A0, $04, $0E, $A2, $F7, $00, $08, $03, $80, $C0, $04
    db $19, $A2, $EB, $00, $08, $04, $C0, $E0, $04, $39, $B1, $00
    db $00, $00, $0F, $04, $80, $80, $02, $26, $A2, $F2, $01, $0A
    db $03, $80, $A0, $02, $67, $A2, $F2, $00, $05, $01, $80, $C0
    db $02, $A7, $A2, $F2, $00, $0B, $04, $C0, $E0, $02, $39, $B1
    db $00, $00, $00, $0F, $04, $80, $80, $02, $09, $A3, $EB, $01
    db $08, $02, $80, $A0, $02, $1B, $A3, $F7, $00, $08, $03, $80
    db $C0, $02, $20, $A3, $EB, $00, $08, $04, $C0, $E0, $02, $39
    db $B1, $00, $00, $00, $0F, $04, $80, $80, $02, $26, $A3, $E5
    db $01, $0E, $02, $80, $A0, $02, $67, $A3, $F1, $00, $08, $03
    db $80, $C0, $02, $8C, $A3, $F1, $00, $08, $04, $C0, $E0, $02
    db $3A, $B1, $00, $00, $00, $0F, $04, $80, $80, $02, $DA, $A3
    db $E4, $01, $0E, $02, $80, $A0, $02, $95, $A4, $F0, $00, $05
    db $03, $80, $C0, $02, $15, $A5, $F0, $00, $0B, $05, $C0, $E0
    db $02, $53, $B1, $00, $00, $00, $0F, $04, $80, $80, $02, $7F
    db $A5, $EC, $01, $0D, $02, $80, $A0, $02, $D9, $A5, $EC, $00
    db $08, $03, $80, $C0, $02, $A9, $A6, $EC, $00, $05, $04, $C0
    db $E0, $02, $8D, $B1, $00, $00, $00, $0F, $04, $80, $80, $02
    db $05, $A7, $F0, $01, $0A, $01, $80, $A0, $02, $4E, $A8, $F0
    db $00, $08, $04, $80, $C0, $02, $4C, $A9, $F0, $00, $0B, $04
    db $C0, $E0, $02, $2D, $B2, $00, $00, $00, $0F
UnresolvedSongEventArea:
    db $80, $30, $F7, $00, $08, $80, $AD, $86, $18, $82, $82, $82
    db $82, $82, $82, $82, $82, $82, $86, $82, $86, $82, $82, $82
    db $82, $82, $86, $82, $82, $82, $86, $82, $86, $82, $86, $82
    db $80, $30, $F7, $00, $09, $A4, $AD, $F6, $87, $AD, $F8, $F0
    db $AD, $F7, $00, $03, $AE, $AD, $F8, $D9, $AD, $F8, $D9, $AD
    db $84, $06, $88, $88, $84, $0C, $88, $06, $88, $88, $F7, $00
    db $02, $BC, $AD, $F6, $AE, $AD, $84, $0C, $88, $06, $80, $0C
    db $84, $06, $88, $0C, $F9, $84, $0C, $88, $06, $84, $0C, $06
    db $88, $06, $06, $F9, $84, $0C, $88, $06, $84, $0C, $8C, $06
    db $88, $06, $06, $F9, $F8, $CE, $AD, $F8, $D9, $AD, $F8, $CE
    db $AD, $F8, $E4, $AD, $F9, $F2, $F8, $B8, $AE, $84, $03, $80
    db $81, $81, $84, $80, $81, $81, $84, $80, $89, $89, $8C, $88
    db $89, $89, $F8, $B8, $AE, $F8, $78, $AE, $F8, $A0, $AE, $F8
    db $C2, $AE, $F8, $A0, $AE, $F8, $C2, $AE, $F8, $78, $AE, $86
    db $06, $81, $03, $83, $84, $03, $80, $81, $81, $F7, $00, $03
    db $2C, $AE, $86, $06, $81, $03, $87, $84, $03, $80, $81, $81
    db $F7, $00, $03, $3B, $AE, $84, $03, $80, $81, $85, $80, $06
    db $81, $03, $85, $84, $88, $89, $85, $8C, $88, $81, $85, $F6
    db $FE, $AD, $85, $06, $85, $03, $85, $8D, $06, $85, $03, $85
    db $F7, $00, $02, $5A, $AE, $85, $06, $85, $03, $85, $8D, $85
    db $85, $85, $F7, $00, $02, $69, $AE, $F9, $84, $03, $80, $81
    db $89, $84, $03, $88, $89, $81, $84, $03, $80, $81, $89, $84
    db $03, $88, $81, $81, $8C, $03, $80, $89, $81, $84, $03, $88
    db $89, $89, $8C, $03, $88, $89, $89, $8C, $88, $89, $89, $F9
    db $85, $06, $03, $03, $A7, $06, $81, $03, $81, $85, $06, $03
    db $03, $8D, $06, $81, $03, $81, $F7, $00, $07, $A0, $AE, $F9
    db $F8, $5A, $AE, $F8, $5A, $AE, $F8, $5A, $AE, $F9, $84, $03
    db $80, $81, $81, $F7, $00, $02, $C2, $AE, $8C, $03, $88, $8D
    db $89, $88, $03, $84, $89, $89, $F9, $F2, $F8, $44, $AF, $F8
    db $4F, $AF, $F8, $70, $AF, $F8, $70, $AF, $F8, $87, $AF, $F8
    db $98, $AF, $85, $81, $89, $85, $81, $85, $89, $81, $85, $81
    db $89, $85, $81, $85, $89, $85, $F8, $70, $AF, $F8, $98, $AF
    db $85, $04, $85, $89, $85, $85, $89, $85, $85, $89, $85, $89
    db $89, $F8, $87, $AF, $F8, $70, $AF, $F8, $98, $AF, $85, $03
    db $81, $89, $81, $F7, $00, $02, $16, $AF, $95, $03, $91, $99
    db $95, $91, $03, $95, $8D, $95, $F8, $A9, $AF, $85, $03, $81
    db $81, $81, $89, $81, $81, $85, $85, $81, $81, $81, $89, $8D
    db $89, $89, $F8, $4F, $AF, $F6, $DE, $AE, $85, $03, $81, $81
    db $81, $F7, $00, $0C, $44, $AF, $F9, $85, $03, $81, $81, $81
    db $F7, $00, $03, $4F, $AF, $85, $03, $89, $89, $89, $8D, $03
    db $81, $81, $89, $85, $81, $89, $81, $85, $89, $81, $81, $8D
    db $89, $89, $81, $F9, $85, $03, $81, $89, $81, $85, $81, $89
    db $81, $85, $81, $89, $85, $81, $85, $89, $85, $F7, $00, $02
    db $70, $AF, $F9, $87, $03, $81, $89, $81, $85, $81, $89, $81
    db $85, $81, $89, $85, $81, $85, $89, $85, $85, $81, $89, $81
    db $85, $81, $89, $81, $85, $81, $89, $85, $81, $85, $89, $85
    db $F9, $85, $03, $81, $81, $81, $89, $85, $81, $85, $81, $81
    db $81, $81, $89, $85, $81, $85, $F7, $00, $05, $A9, $AF, $F9
    db $80, $40, $80, $20, $F7, $00, $04, $C2, $AF, $82, $20, $F7
    db $00, $08, $C9, $AF, $82, $10, $80, $0C, $81, $02, $81, $F7
    db $00, $0F, $D0, $AF, $80, $0C, $81, $02, $81, $F7, $00, $02
    db $DC, $AF, $84, $08, $88, $F7, $00, $06, $E6, $AF, $84, $08
    db $88, $84, $88, $04, $81, $02, $02, $84, $08, $88, $F7, $00
    db $08, $F7, $AF, $F6, $C2, $AF, $80, $48, $89, $06, $03, $03
    db $81, $06, $89, $F7, $00, $05, $02, $B0, $85, $06, $03, $89
    db $09, $85, $06, $85, $89, $F7, $00, $07, $10, $B0, $89, $06
    db $81, $81, $81, $81, $81, $81, $0C, $81, $81, $85, $03, $85
    db $89, $8D, $85, $06, $03, $06, $03, $89, $06, $81, $81, $85
    db $03, $81, $85, $81, $89, $89, $F7, $00, $08, $2E, $B0, $89
    db $03, $89, $85, $85, $89, $89, $85, $85, $89, $89, $89, $89
    db $85, $06, $03, $89, $09, $85, $06, $85, $89, $F7, $00, $04
    db $50, $B0, $81, $0C, $81, $81, $81, $81, $81, $80, $24, $F6
    db $02, $B0, $84, $06, $88, $84, $88, $84, $88, $03, $84, $06
    db $84, $03, $88, $06, $F7, $00, $06, $6A, $B0, $84, $06, $88
    db $84, $88, $84, $88, $8C, $03, $8C, $8C, $8C, $F6, $6A, $B0
    db $F2, $80, $24, $F7, $00, $04, $8D, $B0, $84, $12, $F7, $00
    db $26, $94, $B0, $8C, $06, $F7, $00, $06, $9B, $B0, $F8, $D9
    db $B0, $80, $24, $F7, $00, $0F, $A5, $B0, $8C, $06, $F7, $00
    db $0C, $AC, $B0, $84, $06, $81, $84, $F7, $00, $18, $B3, $B0
    db $84, $03, $84, $88, $06, $88, $F7, $00, $02, $BC, $B0, $8C
    db $03, $F7, $00, $0C, $C7, $B0, $F8, $D9, $B0, $80, $24, $F7
    db $00, $07, $D1, $B0, $F2, $84, $06, $81, $84, $F7, $01, $0E
    db $D9, $B0, $8C, $06, $F7, $00, $06, $E2, $B0, $84, $06, $81
    db $84, $F7, $00, $0C, $E9, $B0, $82, $18, $80, $0C, $F9, $80
    db $60, $48, $88, $03, $F7, $00, $08, $FA, $B0, $84, $06, $03
    db $03, $88, $03, $84, $06, $03, $84, $06, $03, $03, $88, $06
    db $84, $03, $03, $F7, $00, $03, $01, $B1, $84, $06, $03, $03
    db $88, $03, $84, $06, $03, $84, $06, $03, $03, $89, $03, $84
    db $85, $85, $F7, $01, $02, $01, $B1, $84, $0C, $F7, $00, $10
    db $2F, $B1, $F6, $01, $B1, $F2, $84, $06, $81, $03, $03, $88
    db $06, $81, $F7, $00, $07, $3A, $B1, $84, $06, $81, $03, $03
    db $89, $06, $89, $06, $F6, $3A, $B1, $8E, $30, $80, $80, $60
    db $F7, $00, $07, $56, $B1, $81, $06, $81, $81, $81, $85, $03
    db $84, $AF, $06, $85, $A3, $12, $A0, $0C, $A0, $A0, $F7, $00
    db $02, $5D, $B1, $85, $06, $03, $03, $89, $06, $85, $03, $85
    db $F7, $00, $0E, $73, $B1, $85, $06, $89, $89, $89, $89, $89
    db $8D, $8D, $F6, $53, $B1, $F8, $E2, $B1, $F7, $00, $03, $8D
    db $B1, $F8, $F5, $B1, $F7, $01, $02, $8D, $B1, $F8, $07, $B2
    db $F8, $07, $B2, $F8, $E2, $B1, $F8, $E2, $B1, $F7, $00, $02
    db $9D, $B1, $88, $03, $84, $84, $88, $80, $84, $88, $06, $88
    db $03, $84, $84, $88, $80, $84, $88, $06, $F7, $00, $04, $AE
    db $B1, $F8, $E2, $B1, $F7, $00, $03, $C5, $B1, $84, $06, $84
    db $03, $84, $88, $06, $84, $03, $84, $84, $88, $88, $84, $88
    db $84, $88, $88, $F6, $8D, $B1, $84, $06, $84, $03, $84, $88
    db $06, $84, $03, $03, $06, $03, $03, $88, $06, $84, $03, $84
    db $F9, $84, $06, $03, $03, $88, $06, $84, $03, $84, $84, $88
    db $88, $84, $84, $84, $88, $84, $F9, $88, $09, $09, $06, $84
    db $03, $88, $88, $84, $88, $84, $84, $90, $F9, $88, $03, $84
    db $84, $88, $80, $84, $88, $06, $88, $03, $84, $84, $88, $80
    db $84, $88, $06, $F7, $00, $04, $15, $B2, $F9, $8C, $03, $F7
    db $00, $08, $2D, $B2, $A6, $0C, $88, $84, $06, $03, $03, $88
    db $0C, $84, $0C, $88, $12, $84, $03, $03, $88, $0C, $F7, $00
    db $02, $3D, $B2, $F8, $D7, $B2, $F8, $AD, $B2, $F8, $E4, $B2
    db $F8, $C5, $B2, $F7, $00, $03, $54, $B2, $84, $0C, $88, $12
    db $84, $06, $88, $0C, $F8, $F0, $B2, $F8, $C5, $B2, $F7, $00
    db $04, $67, $B2, $84, $0C, $80, $18, $88, $0C, $84, $0C, $80
    db $18, $88, $06, $84, $84, $0C, $80, $18, $88, $0C, $84, $0C
    db $88, $88, $03, $F7, $00, $08, $85, $B2, $F7, $01, $02, $6F
    db $B2, $F8, $C5, $B2, $F7, $00, $09, $91, $B2, $84, $0C, $88
    db $12, $84, $06, $88, $0C, $84, $88, $88, $03, $F7, $00, $08
    db $A3, $B2, $F6, $34, $B2, $84, $0C, $88, $84, $06, $03, $03
    db $88, $0C, $84, $0C, $88, $12, $84, $03, $03, $88, $0C, $F7
    db $00, $02, $B6, $B2, $F9, $84, $0C, $88, $12, $84, $06, $88
    db $0C, $84, $0C, $88, $06, $84, $0C, $06, $88, $0C, $F9, $84
    db $0C, $88, $06, $84, $03, $03, $03, $03, $06, $88, $0C, $F9
    db $84, $0C, $88, $06, $80, $88, $88, $03, $06, $03, $06, $F9
    db $84, $0C, $88, $06, $84, $03, $06, $03, $06, $88, $03, $88
    db $88, $88, $F9, $F2, $FF, $FF, $F0, $F0, $03, $07, $61, $A2
    db $35, $78, $02, $40, $01, $00, $80, $01, $F7, $00, $03, $01
    db $B3, $00, $80, $05, $F2
VariableSongHeaders24:
    db $01, $A8, $E0, $01, $23, $B3, $00, $00, $07, $00
Song31UnresolvedEvents:
    db $00, $30, $F8, $03, $F5, $02, $04, $00, $30, $F8, $03, $F2
    db $02, $A8, $A0, $01, $42, $B3, $00, $01, $00, $00, $A8, $E0
    db $01, $42, $B3, $05, $01, $00, $10
Song32UnresolvedEvents:
    db $00, $30, $18, $05, $00, $F0, $50, $05, $F2, $02, $40, $01
    db $00, $80, $01, $F7, $00, $03, $6D, $B3, $00, $80, $05, $F2
    db $02, $88, $A0, $01, $6D, $B3, $00, $00, $00, $00, $88, $C0
    db $01, $6D, $B3, $01, $00, $00, $00
Song33UnresolvedEvents:
    db $02, $40, $01, $00, $80, $01, $F7, $00, $03, $6D, $B3, $00
    db $80, $05, $F2, $00, $40, $03, $00, $33, $0F, $F2, $02, $88
    db $A0, $01, $96, $B3, $00, $00, $05, $00, $88, $C0, $01, $96
    db $B3, $06, $00, $05, $00
Song34UnresolvedEvents:
    db $00, $20, $03, $00, $10, $06, $F2, $FF, $F0, $F0, $03, $07
    db $F0, $F0, $4F, $2F, $03, $80, $08, $08, $EF, $01, $F7, $00
    db $0A, $C5, $B3, $F2, $02, $A8, $A0, $01, $C5, $B3, $00, $00
    db $0C, $00, $A8, $E0, $01, $D1, $B3, $00, $00, $0C, $00
Song35UnresolvedEvents:
    db $03, $80, $08, $08, $EF, $01, $F7, $00, $0A, $C5, $B3, $F2
    db $00, $40, $08, $06, $EF, $01, $F7, $00, $0A, $D1, $B3, $F2
    db $00, $80, $E8, $04, $F2, $01, $A8, $C0, $01, $EC, $B3, $00
    db $00, $00, $00
Song36UnresolvedEvents:
    db $00, $80, $E8, $04, $F2, $FF, $30, $20, $03, $07, $F5, $F1
    db $5F, $29, $03, $F0, $03, $03, $00, $08, $F2, $02, $88, $A0
    db $01, $14, $B4, $00, $00, $0C, $00, $88, $E0, $01, $1B, $B4
    db $00, $00, $0C, $00
Song37UnresolvedEvents:
    db $03, $F0, $03, $03, $00, $08, $F2, $00, $80, $03, $00, $20
    db $08, $F2, $02, $A8, $A0, $01, $35, $B4, $00, $04, $01, $00
    db $A8, $C0, $01, $35, $B4, $F6, $04, $01, $00
Song38UnresolvedEvents:
    db $01, $70, $05, $04, $01, $80, $FB, $03, $F5, $02, $02, $01
    db $10, $DD, $0A, $F2, $FF, $F0, $00, $03, $07, $F2, $75, $99
    db $F7, $00, $80, $08, $04, $F2, $02, $A8, $A0, $01, $66, $B4
    db $00, $00, $00, $03, $A8, $E0, $01, $6B, $B4, $00, $00, $00
    db $01
Song39UnresolvedEvents:
    db $00, $50, $05, $04, $F2, $00, $30, $04, $04, $F2, $02, $A8
    db $A0, $01, $83, $B4, $00, $00, $00, $00, $A8, $C0, $01, $83
    db $B4, $01, $00, $00, $00
Song40UnresolvedEvents:
    db $01, $4F, $8F, $03, $00, $4F, $06, $02, $01, $00, $00, $04
    db $EF, $02, $F7, $00, $05, $83, $B4, $F2, $01, $A8, $C0, $01
    db $A1, $B4, $00, $00, $00, $00
Song41UnresolvedEvents:
    db $00, $90, $E0, $04, $00, $60, $E8, $02, $F7, $00, $02, $A1
    db $B4, $F2, $02, $A8, $A0, $01, $C6, $B4, $00, $00, $00, $00
    db $A8, $E0, $01, $D6, $B4, $00, $00, $00, $00
Song42UnresolvedEvents:
    db $00, $00, $00, $02, $02, $80, $F0, $06, $02, $00, $F0, $0D
    db $EF, $01, $F7, $00, $04, $CA, $B4, $F2, $F3, $03, $00, $50
    db $FC, $06, $00, $30, $FC, $0D, $EF, $01, $F7, $00, $04, $DC
    db $B4, $F2, $01, $A8, $C0, $01, $F2, $B4, $02, $00, $00, $00
Song43UnresolvedEvents:
    db $01, $09, $E4, $09, $01, $09, $E4, $02, $01, $FF, $F4, $02
    db $F7, $00, $07, $F2, $B4, $F2, $02, $A8, $A0, $02, $17, $B5
    db $00, $01, $00, $01, $A8, $C0, $02, $3B, $B5, $09, $00, $00
    db $01
Song44UnresolvedEvents:
    db $03, $B0, $10, $03, $03, $F0, $D0, $09, $F7, $00, $02, $17
    db $B5, $03, $20, $00, $01, $00, $10, $30, $01, $F7, $00, $0E
    db $24, $B5, $F2, $FF, $03, $02, $CB, $98, $F0, $80, $19, $2C
    db $03, $B0, $10, $03, $03, $F0, $D0, $09, $F7, $00, $02, $3B
    db $B5, $03, $F0, $D0, $06, $EF, $01, $F7, $00, $05, $48, $B5
    db $F2, $01, $80, $C0, $01, $5E, $B5, $00, $00, $00, $00
Song45UnresolvedEvents:
    db $AF, $03, $F2, $FF, $90, $E0, $02, $00, $80, $E9, $02, $F7
    db $00, $80, $E9, $02, $F7, $00, $04, $82, $B5, $F2, $01, $A8
    db $A0, $02, $7E, $B5, $00, $00, $00, $00
Song46UnresolvedEvents:
    db $00, $90, $E0, $02, $00, $80, $E9, $02, $F7, $00, $04, $82
    db $B5, $F2, $01, $88, $E0, $01, $96, $B5, $00, $00, $01, $00
Song47UnresolvedEvents:
    db $00, $40, $08, $F7, $00, $09, $96, $B5, $F2, $FF, $F8, $F5
    db $03, $07, $F2, $F5, $48, $77, $05, $30, $F1, $03, $05, $30
    db $0A, $0F, $F2, $01, $A8, $E0, $01, $BB, $B5, $00, $00, $00
    db $00
Song48UnresolvedEvents:
    db $00, $30, $F1, $03, $00, $30, $0A, $0F, $F2, $FF, $F8, $C0
    db $01, $07, $F2, $F5, $48, $77, $00, $10, $01, $10, $F2, $01
    db $A8, $E0, $01, $DC, $B5, $00, $00, $09, $00
Song49UnresolvedEvents:
    db $00, $10, $FF, $04, $F5, $05, $01, $00, $10, $01, $10, $F2
    db $00, $30, $00, $01, $00, $10, $05, $03, $F2, $01, $A8, $C0
    db $01, $FB, $B5, $00, $00, $09, $00
Song50UnresolvedEvents:
    db $00, $30, $00, $01, $00, $10, $05, $03, $F2, $FF, $72, $31
    db $08, $32, $F2, $60, $38, $94, $04, $00, $04, $FB, $00, $E5
    db $F7, $00, $08, $0D, $B6, $04, $00, $05, $FB, $00, $0B, $F7
    db $00, $0C, $18, $B6, $F2, $02, $88, $A0, $01, $37, $B6, $40
    db $00, $0A, $00, $88, $E0, $01, $4E, $B6, $28, $00, $00, $00
Song51UnresolvedEvents:
    db $03, $00, $04, $FB, $E8, $F0, $F7, $00, $08, $37, $B6, $03
    db $00, $06, $FB, $10, $10, $F7, $00, $0D, $42, $B6, $F2, $00
    db $10, $06, $FB, $FB, $F0, $F7, $00, $08, $4E, $B6, $00, $10
    db $06, $FB, $02, $10, $F7, $00, $0D, $59, $B6, $F2, $FF, $01
    db $06, $4C, $87, $B0, $70, $24, $27, $03, $30, $18, $02, $04
    db $F0, $50, $05, $F2, $02, $88, $A0, $01, $8A, $B6, $00, $00
    db $00, $02, $A8, $E0, $01, $99, $B6, $00, $00, $00, $00
Song52UnresolvedEvents:
    db $00, $00, $09, $00, $40, $01, $00, $10, $01, $F7, $00, $10
    db $8D, $B6, $F2, $00, $10, $04, $0B, $00, $20, $FE, $0D, $F2
    db $02, $88, $A0, $01, $B5, $B6, $02, $00, $08, $00, $88, $C0
    db $01, $B5, $B6, $00, $00, $08, $00
Song53UnresolvedEvents:
    db $00, $70, $03, $00, $A2, $10, $F2, $FF, $00, $50, $03, $07
    db $F3, $72, $AB, $B6, $03, $50, $10, $03, $F2, $01, $A8, $E0
    db $01, $D4, $B6, $00, $00, $00, $00
Song54UnresolvedEvents:
    db $00, $50, $20, $03, $F2, $01, $88, $C0, $01, $E3, $B6, $00
    db $00, $00, $00, $00, $30, $01, $F2, $FF
UndecodedSoundTrailingData:
    db $07, $0D, $1F, $3B, $2F, $5F, $47, $53, $E0, $B0, $F8, $DC
    db $F4, $FA, $E2, $CA, $58, $6F, $6F, $33, $38, $1A, $0F, $03
    db $1A, $F6, $F6, $CC, $1C, $B8, $F0, $C0, $06, $0D, $1B, $13
    db $2B, $55, $F5, $F2, $60, $B0, $D8, $C8, $D4, $AA, $AF, $4F
    db $52, $EB, $62, $96, $D4, $6E, $2A, $14, $4A, $D7, $46, $69
    db $2B, $76, $54, $28, $52, $EB, $62, $96, $CC, $76, $1A, $00
    db $4A, $D7, $46, $69, $33, $6E, $58, $00, $00, $01, $07, $1E
    db $39, $2F, $7F, $56, $70, $E8, $98, $7C, $FC, $E6, $EE, $F7
    db $76, $56, $76, $73, $31, $23, $25, $2A, $FF, $FB, $FB, $9E
    db $BE, $6C, $48, $80, $76, $56, $76, $73, $31, $23, $25, $2A
    db $FF, $FB, $FB, $9E, $BE, $AC, $88, $99, $C0, $0E, $17, $19
    db $3E, $3F, $4F, $5E, $BE, $00, $80, $E0, $78, $9C, $F4, $FE
    db $6A, $BE, $BE, $FF, $79, $7D, $36, $12, $01, $03, $6A, $8D
    db $CC, $8C, $C4, $A4, $54, $BE, $BE, $FF, $79, $7D, $35, $14
    db $06, $03, $6A, $FF, $4C, $8C, $C4, $A4, $54, $03, $0F, $1C
    db $3B, $36, $6C, $6C, $EE, $80, $E0, $70, $B8, $D8, $6C, $6C
    db $EE, $C7, $E3, $F0, $6A, $35, $1E, $0F, $03, $C6, $8E, $1E
    db $AC, $58, $F0, $E0, $80, $03, $04, $0E, $17, $37, $33, $60
    db $67, $80, $40, $E0, $D0, $D8, $98, $0C, $CC, $EF, $DF, $DF
    db $BF, $7F, $7F, $3F, $0F, $EE, $F6, $F6, $FA, $FC, $FC, $F8
    db $E0, $1F, $2F, $4D, $5F, $BB, $FF, $F7, $E2, $80, $E0, $38
    db $9C, $4E, $96, $4F, $97, $F4, $F1, $7A, $7E, $1E, $1E, $0D
    db $03, $2F, $9F, $FE, $FE, $F4, $F8, $E0, $00, $F5, $F2, $7A
    db $7E, $1E, $1D, $0F, $00, $AF, $9F, $FE, $FE, $F4, $F8, $E0
    db $00, $01, $07, $1E, $3D, $72, $69, $F2, $E9, $F8, $F4, $FF
    db $B2, $FA, $DD, $FF, $EF, $47, $F4, $F9, $7F, $7F, $3F, $1F
    db $07, $00, $2F, $8F, $5E, $7E, $78, $78, $B0, $C0, $F5, $F9
    db $7F, $7F, $3F, $1F, $07, $00, $AF, $4F, $5E, $7E, $78, $B8
    db $F0, $00, $03, $0F, $1B, $3F, $33, $75, $72, $78, $C0, $F0
    db $98, $DC, $CC, $4E, $8E, $1E, $3D, $3A, $1D, $1F, $0F, $06
    db $02, $00, $5C, $BC, $78, $F8, $F0, $60, $80, $80, $01, $01
    db $06, $0F, $1F, $1B, $37, $33, $00, $40, $60, $F0, $F8, $D8
    db $EC, $EC, $77, $62, $71, $38, $3A, $1D, $0F, $03, $CE, $A6
    db $4E, $1C, $AC, $78, $F0, $C0, $07, $1F, $3D, $70, $69, $F3
    db $E5, $F3, $00, $CE, $F1, $3E, $5D, $FE, $FF, $FF, $E5, $F3
    db $69, $70, $3D, $1F, $07, $00, $FF, $85, $FE, $5D, $3E, $F1
    db $CE, $03, $00, $85, $CC, $F2, $3D, $5C, $FE, $03, $FF, $85
    db $FE, $5C, $3D, $F2, $CC, $03, $00, $A5, $73, $8F, $7C, $BA
    db $7F, $FF, $FF, $E0, $F8, $BC, $0E, $96, $CF, $A7, $CF, $FF
    db $7F, $BA, $7C, $8F, $73, $00, $00, $A7, $CF, $96, $0E, $BC
    db $F8, $E0, $00, $00, $33, $4F, $BC, $3A, $7F, $03, $FF, $85
    db $7F, $3A, $BC, $4F, $33, $02, $00, $00, $CE, $01, $06, $08
    db $14, $10, $24, $3B, $2C, $80, $60, $10, $28, $08, $24, $DC
    db $34, $27, $30, $30, $1C, $1F, $0F, $07, $00, $E4, $0C, $0C
    db $38, $F8, $F0, $E0, $00, $03, $06, $0C, $1C, $14, $22, $86
    db $89, $C0, $60, $30, $38, $28, $44, $61, $91, $CF, $B7, $DF
    db $4C, $62, $32, $00, $08, $F3, $ED, $FB, $32, $46, $4C, $00
    db $10, $CF, $B7, $DF, $4C, $72, $12, $00, $00, $F3, $ED, $FB
    db $32, $4E, $48, $05, $00, $B5, $01, $07, $37, $16, $0C, $00
    db $10, $70, $F8, $F8, $38, $10, $28, $0C, $3F, $1E, $3E, $0D
    db $48, $50, $15, $28, $2C, $14, $20, $60, $C0, $00, $00, $0C
    db $3F, $1E, $3E, $0D, $08, $10, $14, $28, $2C, $14, $20, $60
    db $00, $00, $40, $00, $08, $0E, $1F, $1F, $34, $20, $45, $03
    db $00, $9E, $80, $E0, $EC, $68, $30, $55, $55, $08, $04, $06
    db $03, $00, $00, $30, $FC, $DC, $7C, $B0, $12, $0A, $A8, $55
    db $55, $08, $04, $06, $02, $00, $02, $30, $03, $FC, $AC, $B0
    db $10, $08, $28, $00, $07, $0F, $1C, $19, $35, $35, $71, $00
    db $C0, $E0, $70, $30, $58, $58, $1C, $78, $7C, $7F, $3F, $1F
    db $0F, $03, $00, $3C, $7C, $FC, $F8, $F0, $E0, $80, $00, $00
    db $01, $01, $08, $18, $1C, $3F, $38, $03, $00, $C3, $20, $30
    db $70, $F8, $38, $77, $68, $60, $50, $5C, $3F, $0F, $00, $DC
    db $2C, $0C, $14, $74, $F8, $E0, $00, $00, $17, $36, $34, $4C
    db $18, $78, $7D, $00, $80, $E0, $78, $BC, $7C, $BE, $7E, $0B
    db $6E, $6D, $10, $2C, $00, $00, $02, $FE, $7C, $7C, $B0, $88
    db $60, $00, $00, $0A, $6D, $6C, $10, $2C, $00, $02, $00, $7E
    db $7C, $BC, $B0, $08, $E0, $03, $00, $C3, $01, $07, $1E, $3D
    db $3E, $7D, $7E, $00, $E8, $6C, $2C, $32, $18, $1E, $BE, $7F
    db $3E, $3E, $0D, $01, $02, $00, $00, $D0, $76, $B6, $28, $14
    db $00, $00, $40, $7E, $3E, $3D, $0D, $00, $03, $00, $00, $50
    db $B6, $36, $28, $14, $00, $40, $00, $00, $03, $0C, $18, $1C
    db $3A, $3D, $3F, $00, $C0, $70, $38, $38, $BC, $7C, $FC, $1F
    db $1F, $0F, $0B, $04, $00, $02, $F8, $82, $F0, $D0, $08, $00
    db $84, $0A, $0C, $18, $1C, $04, $00, $B1, $50, $30, $18, $18
    db $38, $3D, $3E, $1F, $1F, $0F, $03, $00, $3C, $5C, $BC, $F8
    db $F8, $F0, $C0, $00, $00, $07, $1F, $3F, $3E, $7C, $7A, $7C
    db $00, $00, $C0, $F2, $A8, $10, $04, $04, $7A, $7C, $3E, $3F
    db $1F, $07, $00, $00, $04, $10, $A8, $F2, $C0, $05, $00, $84
    db $C0, $F4, $A8, $10, $03, $04, $84, $10, $A8, $F4, $C0, $05
    db $00, $93, $03, $4F, $15, $08, $20, $20, $00, $E0, $F8, $FC
    db $7C, $3E, $5E, $3E, $20, $08, $15, $4F, $03, $03, $00, $86
    db $5E, $3E, $7C, $FC, $F8, $E0, $04, $00, $84, $03, $2F, $15
    db $08, $03, $20, $84, $08, $15, $2F, $03, $03, $00, $00, $90
    db $01, $07, $0F, $1C, $10, $24, $3B, $3C, $80, $E0, $F0, $38
    db $08, $24, $DC, $3C, $03, $3F, $02, $1F, $83, $0F, $07, $00
    db $03, $FC, $02, $F8, $B2, $F0, $E0, $00, $03, $07, $0F, $1F
    db $17, $23, $A7, $A1, $C0, $E0, $F0, $F8, $E8, $C4, $E5, $85
    db $A5, $51, $8D, $25, $03, $03, $11, $00, $A5, $8A, $B1, $A4
    db $C0, $C0, $88, $00, $A5, $51, $8D, $25, $03, $0B, $05, $00
    db $A5, $8A, $B1, $A4, $C0, $D0, $A0, $03, $00, $F6, $01, $07
    db $1F, $3F, $1E, $0C, $00, $70, $F0, $F8, $F8, $3C, $9C, $AE
    db $2C, $2D, $2C, $3E, $03, $14, $0A, $40, $8E, $8E, $06, $44
    db $04, $08, $80, $00, $2C, $2D, $2C, $3E, $03, $14, $0A, $00
    db $8E, $8E, $06, $44, $04, $48, $40, $00, $00, $0E, $0F, $1F
    db $1F, $3C, $38, $74, $00, $00, $80, $E0, $F8, $FC, $78, $30
    db $70, $70, $60, $22, $20, $10, $01, $00, $30, $B4, $10, $7C
    db $C0, $28, $50, $02, $70, $70, $60, $22, $20, $10, $02, $00
    db $30, $B4, $30, $FC, $C0, $28, $50, $00, $00, $07, $0F, $1E
    db $1C, $3E, $3E, $7C, $00, $C0, $E0, $F0, $70, $F8, $F8, $7C
    db $7E, $7F, $7F, $3F, $1F, $0F, $03, $00, $03, $FC, $A3, $F8
    db $F0, $E0, $80, $00, $00, $02, $04, $0E, $1F, $1F, $3F, $38
    db $00, $80, $40, $E0, $F0, $F0, $F8, $38, $70, $67, $6F, $5F
    db $4F, $07, $00, $00, $1C, $CC, $EC, $F4, $E4, $C0, $03, $00
    db $03, $17, $AA, $2F, $1F, $7F, $7F, $00, $80, $E0, $F8, $FC
    db $FC, $FE, $FE, $0F, $0E, $2D, $21, $31, $0D, $02, $02, $FE
    db $7C, $7C, $B0, $08, $20, $00, $00, $0E, $0D, $2D, $21, $31
    db $0A, $02, $00, $7E, $7C, $BC, $30, $08, $20, $03, $00, $88
    db $01, $07, $1F, $3F, $3F, $7F, $7F, $00, $03, $E8, $88, $F4
    db $F8, $FE, $FE, $7F, $3E, $3E, $0D, $04, $00, $8C, $F0, $70
    db $B4, $A4, $8C, $B0, $40, $40, $7E, $3E, $3D, $0C, $04, $00
    db $8D, $70, $B0, $B4, $A4, $8C, $70, $40, $00, $00, $03, $0F
    db $1F, $1F, $03, $3F, $85, $00, $C0, $F0, $F8, $F8, $03, $FC
    db $02, $1F, $83, $0F, $03, $04, $03, $01, $02, $F8, $84, $F0
    db $C0, $20, $80, $04, $00, $86, $01, $04, $03, $0F, $1F, $1F
    db $03, $80, $85, $20, $C0, $F0, $F8, $F8, $03, $3F, $02, $1F
    db $83, $0F, $03, $00, $03, $FC, $02, $F8, $88, $F0, $C0, $00
    db $00, $07, $1F, $3F, $3F, $03, $7F, $02, $00, $93, $CE, $E1
    db $E8, $F4, $F6, $F6, $7F, $7F, $3F, $3F, $1F, $07, $00, $00
    db $F6, $F4, $E8, $E1, $CE, $05, $00, $84, $CC, $E2, $E9, $F4
    db $03, $F6, $84, $F4, $E9, $E2, $CC, $05, $00, $8B, $73, $87
    db $17, $2F, $6F, $6F, $00, $E0, $F8, $FC, $FC, $03, $FE, $85
    db $6F, $2F, $17, $87, $73, $03, $00, $02, $FE, $02, $FC, $82
    db $F8, $E0, $04, $00, $84, $33, $47, $97, $2F, $03, $6F, $84
    db $2F, $97, $47, $33, $03, $00, $00, $84, $00, $01, $07, $08
    db $03, $00, $85, $10, $00, $80, $E0, $10, $03, $00, $85, $08
    db $18, $0F, $0F, $03, $04, $00, $84, $18, $F0, $F0, $C0, $05
    db $00, $81, $01, $03, $03, $85, $09, $2D, $24, $00, $80, $03
    db $C0, $A2, $90, $B4, $24, $A4, $00, $84, $61, $61, $31, $11
    db $08, $25, $00, $21, $86, $86, $8C, $88, $10, $A4, $00, $84
    db $61, $71, $19, $05, $00, $25, $00, $21, $86, $8E, $98, $A0
    db $03, $00, $DE, $01, $06, $18, $08, $08, $21, $00, $60, $80
    db $00, $00, $04, $0C, $26, $01, $21, $01, $00, $0E, $5C, $5A
    db $55, $06, $02, $02, $64, $64, $C8, $80, $00, $01, $21, $01
    db $00, $0E, $1C, $1A, $14, $06, $02, $02, $64, $64, $48, $40
    db $40, $00, $06, $01, $00, $00, $08, $19, $34, $00, $00, $80
    db $60, $18, $10, $10, $84, $20, $20, $60, $26, $26, $13, $01
    db $00, $84, $84, $00, $00, $70, $3A, $5A, $AA, $20, $20, $60
    db $26, $26, $12, $02, $02, $84, $84, $00, $80, $70, $38, $58
    db $28, $03, $00, $85, $02, $05, $0B, $0B, $0D, $03, $00, $87
    db $80, $40, $A0, $A0, $60, $06, $03, $06, $00, $82, $C0, $80
    db $07, $00, $85, $03, $05, $06, $07, $03, $03, $00, $85, $80
    db $40, $C0, $C0, $80, $05, $00, $83, $10, $0C, $07, $05, $00
    db $83, $10, $60, $C0, $04, $00, $86, $21, $23, $63, $07, $07
    db $02, $03, $00, $8A, $80, $40, $80, $40, $80, $04, $00, $20
    db $00, $20, $07, $00, $89, $88, $20, $00, $00, $04, $00, $20
    db $00, $20, $06, $00, $83, $80, $08, $20, $05, $00, $8D, $01
    db $02, $01, $02, $01, $00, $00, $84, $C4, $C6, $E0, $E0, $40
    db $04, $00, $81, $01, $03, $00, $85, $20, $00, $04, $00, $04
    db $06, $00, $81, $01, $04, $00, $85, $20, $00, $04, $00, $04
    db $05, $00, $85, $03, $07, $03, $05, $02, $03, $00, $85, $80
    db $C0, $C0, $40, $80, $08, $00, $81, $01, $05, $00, $81, $80
    db $04, $00, $87, $01, $00, $01, $03, $07, $03, $80, $03, $00
    db $87, $80, $C0, $E0, $E0, $07, $02, $01, $05, $00, $83, $C0
    db $A0, $40, $09, $00, $84, $01, $03, $05, $03, $03, $00, $88
    db $02, $48, $E0, $F4, $F4, $05, $03, $01, $05, $00, $84, $F4
    db $E0, $48, $02, $07, $00, $83, $04, $48, $E0, $03, $F4, $83
    db $E0, $48, $04, $07, $00, $85, $40, $12, $07, $2F, $2F, $04
    db $00, $88, $80, $C0, $A0, $C0, $2F, $07, $12, $40, $04, $00
    db $83, $A0, $C0, $80, $08, $00, $83, $20, $12, $07, $03, $2F
    db $83, $07, $12, $20, $04, $00, $00
SoundBankEndPadding:
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
    db $FF, $FF, $FF, $FF, $FF
