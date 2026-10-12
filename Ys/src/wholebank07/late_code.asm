org $B53F
    ld hl,$D600 ; $B53F
    ld bc,$0380 ; $B542
    ld a,(hl) ; $B545
    cp $1C ; $B546
    jr nc,$B550 ; $B548
    cp $12 ; $B54A
    jr z,$B550 ; $B54C
    ld (hl),$00 ; $B54E
    inc hl ; $B550
    inc hl ; $B551
    dec bc ; $B552
    ld a,b ; $B553
    or c ; $B554
    jr nz,$B545 ; $B555
    ld hl,$C600 ; $B557
    ld a,$E4 ; $B55A
    ld b,$1F ; $B55C
    or $C0 ; $B55E
    ld (hl),a ; $B560
    inc hl ; $B561
    add a,$02 ; $B562
    ld (hl),$7A ; $B564
    inc hl ; $B566
    djnz $B55E ; $B567
    ld de,$7D20 ; $B569
    ld b,$13 ; $B56C
    ld (hl),e ; $B56E
    inc hl ; $B56F
    ld (hl),d ; $B570
    inc hl ; $B571
    ld a,e ; $B572
    add a,$40 ; $B573
    ld e,a ; $B575
    jr nc,$B579 ; $B576
    inc d ; $B578
    ld a,d ; $B579
    cp $7F ; $B57A
    jr nz,$B580 ; $B57C
    ld d,$78 ; $B57E
    djnz $B56E ; $B580
    ld hl,$D800 ; $B582
    ld bc,$0B4C ; $B585
    call $B590 ; $B588
    ld hl,$D82E ; $B58B
    ld b,$09 ; $B58E
    ld (hl),c ; $B590
    inc hl ; $B591
    inc hl ; $B592
    djnz $B590 ; $B593
    ret ; $B595
org $B9D6
    cp $01 ; $B9D6
    ret c ; $B9D8
    jr nz,$BA01 ; $B9D9
    ld a,($C196) ; $B9DB
    inc a ; $B9DE
    cp $03 ; $B9DF
    jr c,$B9E4 ; $B9E1
    xor a ; $B9E3
    ld ($C196),a ; $B9E4
    ld hl,$BA0F ; $B9E7
    ld b,a ; $B9EA
    add a,a ; $B9EB
    add a,b ; $B9EC
    add a,l ; $B9ED
    ld l,a ; $B9EE
    jr nc,$B9F2 ; $B9EF
    inc h ; $B9F1
    ld de,$C16D ; $B9F2
    ldi ; $B9F5
    ldi ; $B9F7
    ldi ; $B9F9
    ld a,$01 ; $B9FB
    ld ($C197),a ; $B9FD
    ret ; $BA00
    ld a,($C196) ; $BA01
    inc a ; $BA04
    and $01 ; $BA05
    ld ($C196),a ; $BA07
    ld hl,$BA18 ; $BA0A
    jr $B9EA ; $BA0D
org $BA1E
    ld a,($C1DF) ; $BA1E
    or a ; $BA21
    ret z ; $BA22
    ld a,($C222) ; $BA23
    or a ; $BA26
    ret z ; $BA27
    dec a ; $BA28
    jr z,$BA2C ; $BA29
    dec a ; $BA2B
    ld ($C222),a ; $BA2C
    ret ; $BA2F
    ld a,($C1E3) ; $BA30
    or a ; $BA33
    jr z,$BA3A ; $BA34
    dec a ; $BA36
    ld ($C1E3),a ; $BA37
    ret ; $BA3A
