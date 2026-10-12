; Ys (SMS), bank 2, CPU $8000–$808E (ROM offsets $08000–$0808E).
; Partial reconstruction, not yet assembler round-trip verified.
; All mnemonic boundaries for this range are checked in phase3/code.lst.
; Labels are investigative; original developer symbols are unknown.
        org $8000

Bank2_Update:
        exx
        ld a,($de60)
        or a
        ex af,af'
        ld hl,$de6d
        exx
        call Bank2_TimerStep
        call Bank2_ThreeSlotStep
        call $80c0                  ; follow-on countdown helper (Phase 3 listing)
        call $81d9                  ; target not yet traced
        ld a,($de60)
        or a
        jp z,Bank2_ZeroMode
        ld ix,$de6f
        ld b,$08
Bank2_NonzeroLoop:
        push bc
        ld a,$03
        cp b
        jr z,Bank2_NonzeroSpecial
        bit 7,(ix+0)
        call nz,$837f              ; untraced
Bank2_NonzeroAdvance:
        ld de,$0020
        add ix,de
        pop bc
        djnz Bank2_NonzeroLoop
        ret
Bank2_NonzeroSpecial:
        bit 7,(ix+0)
        call nz,$8329              ; untraced
        jr Bank2_NonzeroAdvance

Bank2_ZeroMode:
        ld ix,$deaf
        ld b,$06
Bank2_ZeroLoop:
        push bc
        ld a,$03
        cp b
        jr z,Bank2_ZeroSpecial
        bit 7,(ix+0)
        call nz,$8947              ; untraced
Bank2_ZeroAdvance:
        ld de,$0020
        add ix,de
        pop bc
        djnz Bank2_ZeroLoop
        ret
Bank2_ZeroSpecial:
        bit 7,(ix+0)
        call nz,$8889              ; untraced
        jr Bank2_ZeroAdvance

Bank2_TimerStep:
        ld hl,$de61
        ld a,(hl)
        or a
        ret z
        dec (hl)
        ret nz
        ld a,($de62)
        ld (hl),a
        ld hl,$de79
        ld de,$0020
        ld b,$06
Bank2_TimerRecordLoop:
        inc (hl)
        add hl,de
        djnz Bank2_TimerRecordLoop
        ret

Bank2_ThreeSlotStep:
        ld de,$de64
        call $808f                 ; untraced routine begins immediately after this file
        inc de
        call $808f
        inc de
        call $808f
        ret
