; Additional bank8 system lookup code anchored at $BFB6.
org $BFB6
    ld a,($C120)
    ld b,a
    add a,a
    add a,b
    ld hl,$BFD9
    add a,l
    ld l,a
    jr nc,$BFC4
    inc h
    ld a,(hl)
    ld ($C252),a
    ld ($C25A),a
    ld ($C191),a
    ld ($C190),a
    inc hl
    ld a,(hl)
    ld ($C253),a
    inc hl
    ld a,(hl)
    ld ($C254),a
    ret
