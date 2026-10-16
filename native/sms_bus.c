#include "sms_bus.h"
#include <string.h>

static uint8_t effective_bank(uint8_t raw, uint8_t control) {
    const uint8_t shift = (uint8_t)(control & 3u);
    /* Sega mapper bank-shift latch: re-evaluated on $FFFD-$FFFF writes. */
    const unsigned addition = shift == 0 ? 0u : (4u - shift) * 8u;
    return (uint8_t)((raw + addition) & 15u);
}

bool ys_sms_bus_init(YsSmsBus *bus, const uint8_t *rom, size_t rom_length) {
    if (!bus || !rom || rom_length != YS_ROM_BYTES) return false;
    memset(bus, 0, sizeof(*bus));
    bus->rom = rom;
    for (unsigned i = 0; i < 3; ++i) {
        bus->bank_select[i] = (uint8_t)i;
        bus->mapped_bank[i] = (uint8_t)i;
    }
    /* Assumed 315-5235-style startup map; Ys also initializes mapper itself. */
    return true;
}

bool ys_sms_bus_set_wram_hook(YsSmsBus *bus,YsSmsWramWriteHook hook,
                             void *user) {
    if(!bus || (hook && !user) || (!hook && user)) return false;
    bus->wram_hook=hook;
    bus->wram_hook_user=user;
    return true;
}

uint8_t ys_sms_bus_read(const YsSmsBus *bus, uint16_t address) {
    if (address >= 0xC000u) {
        if (bus->mapper_control & 0x10u)
            return bus->cart_ram[address - 0xC000u];
        return bus->wram[address & 0x1FFFu];
    }
    if (address >= 0x8000u && (bus->mapper_control & 0x08u)) {
        const unsigned bank = (bus->mapper_control & 0x04u) ? 1u : 0u;
        return bus->cart_ram[bank * YS_ROM_BANK_BYTES + (address & 0x3FFFu)];
    }
    const unsigned slot = address >> 14;
    const unsigned bank = address < 0x0400u ? 0u : bus->mapped_bank[slot];
    return bus->rom[bank * YS_ROM_BANK_BYTES + (address & 0x3FFFu)];
}

bool ys_sms_bus_write(YsSmsBus *bus, uint16_t address, uint8_t value) {
    if (address < 0xC000u) {
        if (address >= 0x8000u && (bus->mapper_control & 0x08u)) {
            const unsigned bank = (bus->mapper_control & 0x04u) ? 1u : 0u;
            bus->cart_ram[bank * YS_ROM_BANK_BYTES + (address & 0x3FFFu)] = value;
            return true;
        }
        /* Commercial Ys ROM is immutable; ROM-write-enable is not emulated. */
        return false;
    }
    /* Mapper register writes ALSO update the visible RAM mirror. */
    if (bus->mapper_control & 0x10u)
        bus->cart_ram[address - 0xC000u] = value;
    else {
        uint16_t physical=(uint16_t)(address & 0x1FFFu);
        uint8_t before=bus->wram[physical];
        bus->wram[physical]=value;
        if(bus->wram_hook)
            bus->wram_hook(bus->wram_hook_user,address,physical,
                           before,value);
    }

    if (address == 0xFFFCu) {
        bus->mapper_control = value;
    } else if (address >= 0xFFFDu) {
        const unsigned slot = address - 0xFFFDu;
        bus->bank_select[slot] = value;
        for (unsigned i = 0; i < 3; ++i)
            bus->mapped_bank[i] = effective_bank(bus->bank_select[i], bus->mapper_control);
    }
    return true;
}
