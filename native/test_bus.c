#include "sms_bus.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static uint8_t fixture[YS_ROM_BYTES];
static YsSmsBus bus;

static void setup(void) {
    for (unsigned bank = 0; bank < 16; ++bank)
        for (unsigned offset = 0; offset < YS_ROM_BANK_BYTES; ++offset)
            fixture[bank * YS_ROM_BANK_BYTES + offset] = (uint8_t)bank;
    assert(ys_sms_bus_init(&bus, fixture, sizeof(fixture)));
}

static void test_rom_windows(void) {
    setup();
    assert(ys_sms_bus_read(&bus, 0x0000) == 0);
    assert(ys_sms_bus_read(&bus, 0x03FF) == 0);
    assert(ys_sms_bus_read(&bus, 0x0400) == 0);
    assert(ys_sms_bus_read(&bus, 0x3FFF) == 0);
    assert(ys_sms_bus_read(&bus, 0x4000) == 1);
    assert(ys_sms_bus_read(&bus, 0x8000) == 2);
    assert(!ys_sms_bus_write(&bus, 0x4000, 0xFF));
    assert(ys_sms_bus_read(&bus, 0x4000) == 1);
    assert(ys_sms_bus_write(&bus, 0xFFFD, 6));
    assert(ys_sms_bus_read(&bus, 0x03FF) == 0); /* Immutable first KiB. */
    assert(ys_sms_bus_read(&bus, 0x0400) == 6);
    assert(ys_sms_bus_read(&bus, 0xDFFD) == 6); /* RAM shadow. */
    assert(ys_sms_bus_write(&bus, 0xDFFD, 4));
    assert(ys_sms_bus_read(&bus, 0xFFFD) == 4);
    assert(ys_sms_bus_read(&bus, 0x0400) == 6); /* Alias is not mapper. */
    assert(ys_sms_bus_write(&bus, 0xFFFE, 0xFF));
    assert(ys_sms_bus_read(&bus, 0x4000) == 15); /* 256 KiB wrap. */
}

static void test_console_ram_mirroring(void) {
    setup();
    assert(ys_sms_bus_write(&bus, 0xC000, 0xA5));
    assert(ys_sms_bus_read(&bus, 0xE000) == 0xA5);
    assert(ys_sms_bus_write(&bus, 0xF000, 0x33));
    assert(ys_sms_bus_read(&bus, 0xD000) == 0x33);
    assert(ys_sms_bus_read(&bus, 0xC001) == 0);
}

static void test_cartridge_ram(void) {
    setup();
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0x08));
    assert(ys_sms_bus_write(&bus, 0x8000, 0xA1));
    assert(ys_sms_bus_write(&bus, 0xBFFF, 0xB1));
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0x0C));
    assert(ys_sms_bus_read(&bus, 0x8000) == 0);
    assert(ys_sms_bus_write(&bus, 0x8000, 0xA2));
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0x08));
    assert(ys_sms_bus_read(&bus, 0x8000) == 0xA1);
    assert(ys_sms_bus_read(&bus, 0xBFFF) == 0xB1);
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0));
    assert(ys_sms_bus_read(&bus, 0x8000) == 2);
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0x1C));
    assert(ys_sms_bus_write(&bus, 0xC000, 0x75));
    assert(ys_sms_bus_read(&bus, 0xE000) == 0); /* Cart RAM window, not WRAM mirror. */
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0));
    assert(ys_sms_bus_read(&bus, 0xC000) == 0);
}

static void test_bank_shift_latches(void) {
    setup();
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0x01));
    assert(ys_sms_bus_read(&bus, 0x4000) == 1); /* Deferred shift. */
    assert(ys_sms_bus_write(&bus, 0xFFFF, 3));
    assert(ys_sms_bus_read(&bus, 0x4000) == 9);
    assert(ys_sms_bus_read(&bus, 0x8000) == 11);
    assert(ys_sms_bus_write(&bus, 0xFFFC, 0));
    assert(ys_sms_bus_read(&bus, 0x8000) == 11);
    assert(ys_sms_bus_write(&bus, 0xFFFF, 3));
    assert(ys_sms_bus_read(&bus, 0x4000) == 1);
    assert(ys_sms_bus_read(&bus, 0x8000) == 3);
}

int main(void) {
    assert(!ys_sms_bus_init(NULL, fixture, sizeof(fixture)));
    assert(!ys_sms_bus_init(&bus, fixture, sizeof(fixture) - 1));
    test_rom_windows();
    test_console_ram_mirroring();
    test_cartridge_ram();
    test_bank_shift_latches();
    puts("PASS: Sega mapper, RAM mirrors, SRAM windows and bank-shift latches");
    return EXIT_SUCCESS;
}
