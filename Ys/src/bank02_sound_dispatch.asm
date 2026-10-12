; Ys: The Vanished Omens — SMS bank 2, pending sound-command dispatcher.
; CPU / ROM $81D9–$8203, exact instruction stream checked against ROM.
; Z80 mnemonics and symbolic labels are reconstructed, not original source.
; Not yet assembled or tested for binary-identical output.
        org $81d9

Sound_ProcessPendingCommand:
        ld a,($de63)           ; pending sound command
        bit 7,a
        jp z,$8803             ; no high-bit command: shared reset
        cp $a0
        jp c,$8204             ; $81..$9f sound-init family
        cp $b8
        jp c,$8235             ; $a0..$b7 family
        cp $bc
        jp c,$831a             ; $b8..$bb: clear pending command
        cp $be
        jp nc,$8803            ; $be..$ff: shared reset
Sound_BC_BD:
        sub $bc
        add a,a
        ld c,a
        ld b,$00
        ld hl,$8cfe           ; two little-endian function pointers
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        jp (hl)                ; $bc->$8112, $bd->$814c
