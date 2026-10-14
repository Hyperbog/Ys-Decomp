#ifndef YS_PC_OBJECT_TYPES_H
#define YS_PC_OBJECT_TYPES_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

enum { YS_PC_OBJECT_TYPE_COUNT=35, YS_PC_OBJECT_TYPE_BYTES=10,
       YS_PC_OBJECT_TYPE_FILE_BYTES=16+35*10 };
/* Source bank-0 table $1C05-$1D62, NOT a resolved actor class taxonomy. */
typedef struct {
    uint8_t entry[YS_PC_OBJECT_TYPE_COUNT][YS_PC_OBJECT_TYPE_BYTES];
} YsPcObjectTypes;
bool ys_pc_object_types_load(FILE *file,YsPcObjectTypes *out);
#endif
