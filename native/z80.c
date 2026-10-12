#include "z80.h"
#include <string.h>

static uint16_t pair(uint8_t hi, uint8_t lo) {
    return (uint16_t)((uint16_t)hi << 8 | lo);
}
static void split(uint16_t value, uint8_t *hi, uint8_t *lo) {
    *hi = (uint8_t)(value >> 8); *lo = (uint8_t)value;
}
static uint8_t fetch(YsZ80 *cpu) {
    uint8_t value = ys_sms_bus_read(cpu->bus, cpu->pc);
    cpu->pc = (uint16_t)(cpu->pc + 1u);
    return value;
}
static uint16_t fetch16(YsZ80 *cpu) {
    uint8_t lo = fetch(cpu), hi = fetch(cpu);
    return pair(hi, lo);
}
static bool store(YsZ80 *cpu, uint16_t address, uint8_t value) {
    if (ys_sms_bus_write(cpu->bus, address, value)) return true;
    cpu->status = Z80_BAD_WRITE; return false;
}
static uint8_t *reg(YsZ80 *cpu, unsigned index) {
    switch (index & 7u) {
    case 0: return &cpu->b;
    case 1: return &cpu->c;
    case 2: return &cpu->d;
    case 3: return &cpu->e;
    case 4: return &cpu->h;
    case 5: return &cpu->l;
    case 7: return &cpu->a;
    default: return NULL;  /* Register 6 is (HL), not a CPU register. */
    }
}
static uint8_t r8(YsZ80 *cpu, unsigned index) {
    uint8_t *r = reg(cpu, index);
    return r ? *r : ys_sms_bus_read(cpu->bus, pair(cpu->h, cpu->l));
}
static bool w8(YsZ80 *cpu, unsigned index, uint8_t value) {
    uint8_t *r = reg(cpu, index);
    if (r) { *r = value; return true; }
    return store(cpu, pair(cpu->h, cpu->l), value);
}
static uint8_t sz53(uint8_t value) {
    return (uint8_t)((value & (Z80_F_S | Z80_F_5 | Z80_F_3)) |
                     (value == 0 ? Z80_F_Z : 0));
}
static bool parity(uint8_t value) {
    unsigned count = 0;
    for (unsigned i = 0; i < 8; ++i) count += (value >> i) & 1u;
    return (count & 1u) == 0;
}
static uint8_t inc_flags(uint8_t old, uint8_t result, uint8_t carry) {
    return (uint8_t)(sz53(result) | carry |
        (((old & 15u) == 15u) ? Z80_F_H : 0) |
        (old == 0x7Fu ? Z80_F_PV : 0));
}
static uint8_t dec_flags(uint8_t old, uint8_t result, uint8_t carry) {
    return (uint8_t)(sz53(result) | carry | Z80_F_N |
        ((old & 15u) == 0 ? Z80_F_H : 0) |
        (old == 0x80u ? Z80_F_PV : 0));
}
static uint8_t sub_flags(uint8_t lhs, uint8_t rhs, uint8_t result) {
    return (uint8_t)(sz53(result) | Z80_F_N |
        ((lhs ^ rhs ^ result) & 0x10u ? Z80_F_H : 0) |
        (((lhs ^ rhs) & (lhs ^ result) & 0x80u) ? Z80_F_PV : 0) |
        (lhs < rhs ? Z80_F_C : 0));
}
static bool push16(YsZ80 *cpu, uint16_t value) {
    uint16_t hi = (uint16_t)(cpu->sp - 1u), lo = (uint16_t)(hi - 1u);
    if (!store(cpu, hi, (uint8_t)(value >> 8)) ||
        !store(cpu, lo, (uint8_t)value)) return false;
    cpu->sp = lo; return true;
}
static uint16_t pop16(YsZ80 *cpu) {
    uint8_t lo = ys_sms_bus_read(cpu->bus, cpu->sp++);
    uint8_t hi = ys_sms_bus_read(cpu->bus, cpu->sp++);
    return pair(hi, lo);
}

void ys_z80_reset(YsZ80 *cpu, YsSmsBus *bus) {
    memset(cpu, 0, sizeof(*cpu));
    cpu->bus = bus;
    cpu->status = Z80_RUNNING;
}

void ys_z80_attach_vdp(YsZ80 *cpu, YsSmsVdp *vdp) {
    if (cpu) cpu->vdp = vdp;
}

Z80Status ys_z80_step(YsZ80 *cpu) {
    if (!cpu || !cpu->bus) return Z80_UNSUPPORTED;
    if (cpu->status != Z80_RUNNING) return cpu->status;
    uint16_t start = cpu->pc;
    uint8_t opcode = fetch(cpu);
    if (opcode >= 0x40u && opcode <= 0x7Fu) {
        if (opcode == 0x76u) cpu->status = Z80_HALTED;
        else if (!w8(cpu, (opcode >> 3) & 7u, r8(cpu, opcode & 7u)))
            goto fail;
    } else if ((opcode & 0xC7u) == 0x06u) {
        if (!w8(cpu, (opcode >> 3) & 7u, fetch(cpu))) goto fail;
    } else if ((opcode & 0xC7u) == 0x04u) {
        unsigned i = (opcode >> 3) & 7u;
        uint8_t old = r8(cpu, i), result = (uint8_t)(old + 1u);
        if (!w8(cpu, i, result)) goto fail;
        cpu->f = inc_flags(old, result, cpu->f & Z80_F_C);
    } else if ((opcode & 0xC7u) == 0x05u) {
        unsigned i = (opcode >> 3) & 7u;
        uint8_t old = r8(cpu, i), result = (uint8_t)(old - 1u);
        if (!w8(cpu, i, result)) goto fail;
        cpu->f = dec_flags(old, result, cpu->f & Z80_F_C);
    } else switch (opcode) {
    case 0x00: break; /* NOP */
    case 0x02: if (!store(cpu,pair(cpu->b,cpu->c),cpu->a)) goto fail;break;
    case 0x0A: cpu->a=ys_sms_bus_read(cpu->bus,pair(cpu->b,cpu->c));break;
    case 0x12: if (!store(cpu,pair(cpu->d,cpu->e),cpu->a)) goto fail;break;
    case 0x1A: cpu->a=ys_sms_bus_read(cpu->bus,pair(cpu->d,cpu->e));break;
    case 0x01: split(fetch16(cpu), &cpu->b, &cpu->c); break;
    case 0x11: split(fetch16(cpu), &cpu->d, &cpu->e); break;
    case 0x21: split(fetch16(cpu), &cpu->h, &cpu->l); break;
    case 0x31: cpu->sp = fetch16(cpu); break;
    case 0x03: split((uint16_t)(pair(cpu->b,cpu->c)+1u),&cpu->b,&cpu->c); break;
    case 0x13: split((uint16_t)(pair(cpu->d,cpu->e)+1u),&cpu->d,&cpu->e); break;
    case 0x23: split((uint16_t)(pair(cpu->h,cpu->l)+1u),&cpu->h,&cpu->l); break;
    case 0x0B: split((uint16_t)(pair(cpu->b,cpu->c)-1u),&cpu->b,&cpu->c); break;
    case 0x1B: split((uint16_t)(pair(cpu->d,cpu->e)-1u),&cpu->d,&cpu->e); break;
    case 0x2B: split((uint16_t)(pair(cpu->h,cpu->l)-1u),&cpu->h,&cpu->l); break;
    case 0x22: {
        uint16_t at = fetch16(cpu);
        if (!store(cpu,at,cpu->l) || !store(cpu,(uint16_t)(at+1u),cpu->h)) goto fail;
        break;
    }
    case 0x2A: {
        uint16_t at = fetch16(cpu);
        uint8_t lo=ys_sms_bus_read(cpu->bus,at);
        uint8_t hi=ys_sms_bus_read(cpu->bus,(uint16_t)(at+1u));
        cpu->h=hi;cpu->l=lo; break;
    }
    case 0x32: if (!store(cpu,fetch16(cpu),cpu->a)) goto fail; break;
    case 0x3A: cpu->a=ys_sms_bus_read(cpu->bus,fetch16(cpu)); break;
    case 0xAF: cpu->a=0;cpu->f=Z80_F_Z|Z80_F_PV;break;
    case 0xE6: cpu->a=(uint8_t)(cpu->a & fetch(cpu));
        cpu->f=(uint8_t)(sz53(cpu->a)|Z80_F_H|(parity(cpu->a)?Z80_F_PV:0));
        break;
    case 0xF6: cpu->a=(uint8_t)(cpu->a | fetch(cpu));
        cpu->f=(uint8_t)(sz53(cpu->a)|(parity(cpu->a)?Z80_F_PV:0));
        break;
    case 0xBE: {
        uint8_t rhs=ys_sms_bus_read(cpu->bus,pair(cpu->h,cpu->l));
        cpu->f=sub_flags(cpu->a,rhs,(uint8_t)(cpu->a-rhs));break;
    }
    case 0xA7: cpu->f=(uint8_t)(sz53(cpu->a)|Z80_F_H|
                                      (parity(cpu->a)?Z80_F_PV:0));break;
    case 0xB7: cpu->f=(uint8_t)(sz53(cpu->a)|
                                      (parity(cpu->a)?Z80_F_PV:0));break;
    case 0xFE: {
        uint8_t rhs=fetch(cpu);
        cpu->f=sub_flags(cpu->a,rhs,(uint8_t)(cpu->a-rhs));break;
    }
    case 0xC3: cpu->pc=fetch16(cpu);break;
    case 0xC9: cpu->pc=pop16(cpu);break;
    case 0xCD: {
        uint16_t target=fetch16(cpu);
        if (!push16(cpu,cpu->pc)) goto fail;
        cpu->pc=target;break;
    }
    case 0xC5: if (!push16(cpu,pair(cpu->b,cpu->c))) goto fail;break;
    case 0xD5: if (!push16(cpu,pair(cpu->d,cpu->e))) goto fail;break;
    case 0xE5: if (!push16(cpu,pair(cpu->h,cpu->l))) goto fail;break;
    case 0xF5: if (!push16(cpu,pair(cpu->a,cpu->f))) goto fail;break;
    case 0xC1: split(pop16(cpu),&cpu->b,&cpu->c);break;
    case 0xD1: split(pop16(cpu),&cpu->d,&cpu->e);break;
    case 0xE1: split(pop16(cpu),&cpu->h,&cpu->l);break;
    case 0xF1: split(pop16(cpu),&cpu->a,&cpu->f);break;
    case 0x10: {
        int8_t displacement=(int8_t)fetch(cpu);
        cpu->b=(uint8_t)(cpu->b-1u);
        if(cpu->b) cpu->pc=(uint16_t)(cpu->pc+displacement);
        break;
    }
    case 0xEF: /* RST $28 -- VDP command helper in Ys bank 0. */
        if(!push16(cpu,cpu->pc)) goto fail;
        cpu->pc=0x0028u;break;
    case 0x18: {
        int8_t displacement=(int8_t)fetch(cpu);
        cpu->pc=(uint16_t)(cpu->pc+displacement);break;
    }
    case 0x20: case 0x28: case 0x30: case 0x38: {
        int8_t displacement=(int8_t)fetch(cpu);
        bool take = opcode==0x20 ? !(cpu->f & Z80_F_Z) :
                    opcode==0x28 ? !!(cpu->f & Z80_F_Z) :
                    opcode==0x30 ? !(cpu->f & Z80_F_C) : !!(cpu->f & Z80_F_C);
        if(take) cpu->pc=(uint16_t)(cpu->pc+displacement);
        break;
    }
    case 0xF3: cpu->iff1=false;cpu->iff2=false;break;
    case 0xFB: cpu->iff1=true;cpu->iff2=true;break; /* EI delay not modeled. */
    case 0xED: {
        uint8_t sub=fetch(cpu);
        if (sub==0x56) {cpu->interrupt_mode=1;break;}
        if (sub==0xB0) {
            uint16_t hl=pair(cpu->h,cpu->l), de=pair(cpu->d,cpu->e);
            uint16_t bc=pair(cpu->b,cpu->c);
            if (!store(cpu,de,ys_sms_bus_read(cpu->bus,hl))) goto fail;
            split((uint16_t)(hl+1u),&cpu->h,&cpu->l);
            split((uint16_t)(de+1u),&cpu->d,&cpu->e);
            split((uint16_t)(bc-1u),&cpu->b,&cpu->c);
            cpu->f=(uint8_t)((cpu->f & (Z80_F_S|Z80_F_Z|Z80_F_C)) |
                (bc!=1 ? Z80_F_PV : 0)); /* H,N reset; flags 3,5 deferred. */
            if (bc!=1) cpu->pc=start; /* Z80 LDIR repeats until BC reaches 0. */
            break;
        }
        cpu->status=Z80_UNSUPPORTED;goto fail;
    }
    case 0xD3: {
        uint8_t port=fetch(cpu);
        if (!cpu->vdp || !ys_sms_vdp_write(cpu->vdp,port,cpu->a)) {
            cpu->status=Z80_UNSUPPORTED_PORT;goto fail;
        }
        break;
    }
    case 0xDB: {
        uint8_t port=fetch(cpu), value=0;
        if (!cpu->vdp || !ys_sms_vdp_read(cpu->vdp,port,&value)) {
            cpu->status=Z80_UNSUPPORTED_PORT;goto fail;
        }
        cpu->a=value;break; /* IN A,(n) leaves Z80 flags unchanged. */
    }
    default: cpu->status=Z80_UNSUPPORTED;goto fail;
    }
    ++cpu->steps;
    return cpu->status;
fail:
    cpu->fault_pc=start;
    cpu->pc=start; /* Fail closed: identify original opcode address. */
    return cpu->status;
}

Z80Status ys_z80_run_until(YsZ80 *cpu, uint16_t stop_pc, uint64_t budget) {
    if (!cpu || !cpu->bus) return Z80_UNSUPPORTED;
    while(cpu->status==Z80_RUNNING && cpu->pc!=stop_pc && budget-- > 0)
        (void)ys_z80_step(cpu);
    if(cpu->status==Z80_RUNNING && cpu->pc!=stop_pc)
        cpu->status=Z80_STEP_LIMIT;
    return cpu->status;
}

const char *ys_z80_status_name(Z80Status status) {
    switch(status) {
    case Z80_RUNNING: return "running";
    case Z80_HALTED: return "halted";
    case Z80_UNSUPPORTED: return "unsupported opcode";
    case Z80_BAD_WRITE: return "ROM write rejected";
    case Z80_UNSUPPORTED_PORT: return "unsupported I/O port";
    case Z80_STEP_LIMIT: return "instruction budget exceeded";
    }
    return "invalid status";
}
