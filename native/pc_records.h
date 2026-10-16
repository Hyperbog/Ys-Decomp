#ifndef YS_PC_RECORDS_H
#define YS_PC_RECORDS_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

enum { YS_PC_GROUP_COUNT=22, YS_PC_RECORD_COUNT=209,
       YS_PC_RECORD_WIDTH=4, YS_PC_STAGING_BYTES=16,
       YS_PC_RECORD_FILE_BYTES=16 + 22*6 + 209*4 + 16 };
typedef struct {
    uint16_t source_pc, count;
    bool terminator_zero;
} YsPcRecordGroup;
typedef struct {
    YsPcRecordGroup groups[YS_PC_GROUP_COUNT];
    uint8_t records[YS_PC_RECORD_COUNT][YS_PC_RECORD_WIDTH];
    uint8_t staging[YS_PC_STAGING_BYTES];
} YsPcRecords;

/* Identified bank-7 source tuple boundaries, NOT decoded map geometry. */
bool ys_pc_records_load(FILE *stream,YsPcRecords *out);
unsigned ys_pc_records_start(const YsPcRecords *records,unsigned group);
#endif
