; Ys: The Vanished Omens (SMS export) — bank 0 startup reconstruction
; NOTE: Instruction encodings are checked against ROM via src/bank00_boot.lst.
; This phase does not claim assembler-produced binary equivalence.
        org $0000

; Z80 reset vector (ROM offset == CPU address in bank 0)
ResetVector:
        di
        im 1
        jp Startup
        db $ff,$ff
; RST $08 table-dispatch helper: HL points to a word table; A indexes it
DispatchRst08:
        add a,a
        add a,l
        ld l,a
        jr nc,$000e
        inc h
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        jp (hl)
        db $ff,$ff,$ff,$ff,$ff
; RST $18 table lookup: returns target address in HL
TableLookupRst18:
        add a,a
        add a,l
        ld l,a
        jr nc,$001e
        inc h
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret
        db $ff,$ff,$ff,$ff,$ff
; RST $28 VDP command write helper: outputs E, then D, to port $BF
VdpSetAddressRst28:
        di
        ld a,e
        out ($bf),a
        ld a,d
        out ($bf),a
        ei
        ret
        db $ff,$ff,$ff,$ff,$ff,$ff,$ff
; Interrupt-mode-1 vector: reads VDP status port $BF
InterruptMode1Handler:
        push af
        in a,($bf)
        or a
        jp p,$0540
        jp $0102
WaitForVBlank:
        ld ($c021),a
        ei
        ld a,($c021)
        or a
        jr nz,$0046
        ret
; ROM bank 2 call bridge
Bank2InitBridge:
        ld a,$02
        ld ($ffff),a
        call $8842
        jp $0bc5
        db $ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff,$ff
; NMI vector
NmiHandler:
        push af
        ld a,($c01f)
        cp $0d
        jr z,$0080
        cp $06
        jr z,$0075
        pop af
        retn
        ld ($c020),a
        ld a,$0d
        ld ($c01f),a
        pop af
        retn
        ld a,($c020)
        ld ($c01f),a
        pop af
        retn
; Mapper setup, RAM initialization, entry to main loop
Startup:
        ld sp,$dff0
        ld hl,$fffc
        ld (hl),$80
        inc hl
        ld (hl),$00
        inc hl
        ld (hl),$01
        inc hl
        ld (hl),$02
        xor a
        ld ($de60),a
        dec a
        ld ($c001),a
        call $079a
ClearSystemRam:
        di
        ld sp,$dff0
        ld hl,$c010
        ld de,$c011
        ld bc,$1e4f
        ld (hl),$00
        ldir
        ld a,$02
        ld ($ffff),a
        call $8803
        call $0749
        call $0bc5
MainLoop:
        ld a,($c018)
        ld ($c031),a
        ld a,($c01f)
        ld hl,DispatchTable
        rst $08
        jp $00c4
; 20 little-endian jump-table targets; original meaning of states not yet confirmed
DispatchTable:
        dw $00fc
        dw $0c4a
        dw $0ede
        dw $0f23
        dw $0f39
        dw $0f71
        dw $0dc9
        dw $2c05
        dw $4459
        dw $3f70
        dw $3805
        dw $38cc
        dw $3c45
        dw $004d
        dw $4b63
        dw $4339
        dw $63a8
        dw $6c07
        dw $6a26
        dw $7c25
; Set RAM game-state selector to $01
InitGameState:
        ld a,$01
        ld ($c01f),a
        ret

; End of Phase 1 verified range at ROM offset $0102.
; Next stage: map code at $0102, VDP interrupt path, and $0749/$079A/$0BC5/$8803.
