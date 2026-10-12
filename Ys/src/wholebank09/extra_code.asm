org $BEFB
    ld a,c
    or a
    jr nz,$BF03
    ld a,$07
    jr $BF22
    ld a,b
    cp $92
    jr nz,$BF0C
    ld a,$05
    jr $BF22
    cp $0C
    jr c,$BF14
    ld a,$06
    jr $BF22
    cp $09
    jr c,$BF1C
    ld a,$05
    jr $BF22
    cp $04
    jr c,$BF22
    ld a,$04
    ld hl,$BF3C
    rst $0018
    ld a,$09
    ld ($C026),a
    rst $0028
    ld b,$06
    ld c,$BE
    outi
    ld a,($C026)
    nop
    out (c),a
    nop
    jr nz,$BF30
    ret
