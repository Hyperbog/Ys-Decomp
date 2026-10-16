#include "pc44_c198_writes.h"
#include <limits.h>
#include <string.h>

bool ys_pc44_set_phase(YsPc44Writer *w,unsigned phase) {
    if(!w || !w->cpu || w->overflow || phase>1u ||
       phase<w->phase) return false;
    w->phase=phase;
    w->iteration=0ul;
    return true;
}
void ys_pc44_c198_hook(void *context,uint16_t logical,uint16_t physical,
                       uint8_t before,uint8_t after) {
    YsPc44Writer *w=context;
    if(!w || w->overflow || physical!=0x0198u) return;
    if(!w->cpu || !w->cpu->bus || w->phase>1u ||
       logical<0xC000u || (logical&0x1FFFu)!=physical ||
       w->count>=YS_PC44_MAX_WRITES ||
       w->phase_counts[w->phase]==UINT_MAX) {
        w->overflow=true;
        return;
    }
    unsigned phase=w->phase;
    const YsZ80 *cpu=w->cpu;
    uint8_t bank=cpu->irq_write_active?0u:cpu->instruction_bank;
    uint16_t pc=cpu->irq_write_active?0x0038u:cpu->instruction_pc;
    if((bank>15u && bank!=254u && bank!=255u) ||
       (before==after && w->same[phase]==UINT_MAX) ||
       (before!=after && w->changed[phase]==UINT_MAX) ||
       (logical>=0xE000u && w->aliases[phase]==UINT_MAX)) {
        w->overflow=true;return;
    }
    YsPc44Write *e=&w->writes[w->count++];
    *e=(YsPc44Write){0};
    e->phase=phase;
    e->iteration=w->iteration;
    e->cpu_step=cpu->steps;
    e->logical=logical;
    e->pc=pc;
    /* The bus invokes this callback before the interpreter updates
       block-transfer pointers. Preserve the actual copy source. */
    e->hl=(uint16_t)(((uint16_t)cpu->h<<8u)|cpu->l);
    e->de=(uint16_t)(((uint16_t)cpu->d<<8u)|cpu->e);
    e->bc=(uint16_t)(((uint16_t)cpu->b<<8u)|cpu->c);
    e->bank=bank;
    e->before=before;e->after=after;
    e->a=cpu->a;e->f=cpu->f;
    e->slot2=cpu->bus->mapped_bank[2];
    e->selector=ys_sms_bus_read(cpu->bus,0xC01Fu);
    e->irq=cpu->irq_write_active?1u:0u;
    ++w->phase_counts[phase];
    if(before==after) ++w->same[phase];
    else ++w->changed[phase];
    if(logical>=0xE000u) ++w->aliases[phase];
}
bool ys_pc44_write_report(FILE *out,const YsPc44Writer *w,
                          const YsSmsRuntime *rt,const char *reason,
                          unsigned long steps) {
    if(!out || !w || !rt || !rt->cpu || !rt->cpu->bus ||
       !reason || strcmp(reason,"budget")!=0 || steps!=600000ul ||
       w->phase!=1u || w->overflow ||
       w->count>YS_PC44_MAX_WRITES ||
       w->phase_counts[0]+w->phase_counts[1]!=w->count) return false;
    for(unsigned p=0;p<2u;++p)
        if(w->same[p]+w->changed[p]!=w->phase_counts[p])return false;
    if(fprintf(out,
       "{\"schema\":\"ys-pc44-physical-c198-writes-v1\","
       "\"stop_reason\":\"%s\",\"continued_steps\":%lu,"
       "\"final_pc\":\"%04X\",\"final_value\":%u,"
       "\"count\":%u,\"phase_counts\":[%u,%u],"
       "\"same\":[%u,%u],\"changed\":[%u,%u],"
       "\"aliases\":[%u,%u],\"events\":[\n",
       reason,steps,rt->cpu->pc,
       (unsigned)rt->cpu->bus->wram[0x0198u],
       w->count,w->phase_counts[0],w->phase_counts[1],
       w->same[0],w->same[1],w->changed[0],w->changed[1],
       w->aliases[0],w->aliases[1])<0) return false;
    for(unsigned i=0;i<w->count;++i) {
        const YsPc44Write *e=&w->writes[i];
        if(fprintf(out,
          "{\"phase\":%u,\"iteration\":%lu,\"cpu_step\":%llu,"
          "\"logical\":\"%04X\",\"physical\":\"0198\","
          "\"pc\":\"%04X\",\"bank\":%u,"
          "\"hl\":\"%04X\",\"de\":\"%04X\",\"bc\":\"%04X\","
          "\"before\":%u,\"after\":%u,\"a\":%u,\"f\":%u,"
          "\"selector\":%u,\"slot2\":%u,\"irq\":%u}%s\n",
          e->phase,e->iteration,(unsigned long long)e->cpu_step,
          e->logical,e->pc,(unsigned)e->bank,
          e->hl,e->de,e->bc,
          (unsigned)e->before,(unsigned)e->after,
          (unsigned)e->a,(unsigned)e->f,
          (unsigned)e->selector,(unsigned)e->slot2,(unsigned)e->irq,
          i+1u==w->count?"":",")<0) return false;
    }
    return fputs("]}\n",out)>=0 && ferror(out)==0;
}
