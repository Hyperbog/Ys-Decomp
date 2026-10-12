#ifndef YS_SMS_BUS_H
#define YS_SMS_BUS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    YS_ROM_BYTES = 256 * 1024,
    YS_ROM_BANK_BYTES = 16 * 1024,
    YS_WRAM_BYTES = 8 * 1024,
    YS_CART_RAM_BYTES = 32 * 1024
};

typedef struct {
    const uint8_t *rom;             /* Caller owns immutable 256 KiB image. */
    uint8_t wram[YS_WRAM_BYTES];
    uint8_t cart_ram[YS_CART_RAM_BYTES];
    uint8_t mapper_control;         /* Value written to $FFFC. */
    uint8_t bank_select[3];         /* Raw values from $FFFD-$FFFF. */
    uint8_t mapped_bank[3];         /* Effective banks, including bank shift. */
} YsSmsBus;

/* In-memory ROM ownership remains with caller; does not read files. */
bool ys_sms_bus_init(YsSmsBus *bus, const uint8_t *rom, size_t rom_length);
uint8_t ys_sms_bus_read(const YsSmsBus *bus, uint16_t address);
/* False for attempted ROM writes; cartridge/console RAM writes return true. */
bool ys_sms_bus_write(YsSmsBus *bus, uint16_t address, uint8_t value);

#endif
