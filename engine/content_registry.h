#ifndef YS_EXPANDED_CONTENT_REGISTRY_H
#define YS_EXPANDED_CONTENT_REGISTRY_H
#include <stdbool.h>
#include <stddef.h>

enum { YS_CONTENT_CAPACITY = 128, YS_CONTENT_ID_CAPACITY = 64 };
typedef enum {
    YS_CONTENT_MAP = 1, YS_CONTENT_ENTITY, YS_CONTENT_QUEST,
    YS_CONTENT_AUDIO, YS_CONTENT_GRAPHICS, YS_CONTENT_RULE
} YsContentKind;
typedef enum { YS_CONTENT_ADD = 1, YS_CONTENT_REPLACE } YsContentOperation;
typedef enum {
    YS_CONTENT_OK = 0, YS_CONTENT_INVALID, YS_CONTENT_CAPACITY_EXCEEDED,
    YS_CONTENT_MISSING, YS_CONTENT_DUPLICATE, YS_CONTENT_CONFLICT
} YsContentStatus;
/* References are stable symbolic IDs, not filesystem paths or ROM addresses. */
typedef struct {
    const char *id;
    YsContentKind kind;
    const char *binding;
    YsContentOperation operation;
} YsContentSpec;
typedef struct {
    char id[YS_CONTENT_ID_CAPACITY];
    char binding[YS_CONTENT_ID_CAPACITY];
    char origin[YS_CONTENT_ID_CAPACITY];
    YsContentKind kind;
} YsContentEntry;
typedef struct {
    YsContentEntry entries[YS_CONTENT_CAPACITY];
    size_t count;
} YsContentRegistry;

void ys_content_init(YsContentRegistry *registry);
/* One base or one mod pack per call. A failed pack changes no entries. */
YsContentStatus ys_content_apply(YsContentRegistry *registry,
                                 const char *origin,
                                 const YsContentSpec *specs, size_t count);
const YsContentEntry *ys_content_find(const YsContentRegistry *registry,
                                      const char *id);
#endif
