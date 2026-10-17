#include "content_registry.h"
#include <string.h>

/* Only canonical dotted IDs; reject empty segments and path-like values. */
static bool valid_id(const char *s) {
    if (!s) return false;
    size_t n = 0;
    bool segment = false, dot = false;
    for (; n < YS_CONTENT_ID_CAPACITY && s[n]; ++n) {
        const char c = s[n];
        if (c == '.') {
            if (!segment) return false;
            segment = false;
            dot = true;
        } else if ((c >= 'a' && c <= 'z') ||
                   (c >= '0' && c <= '9') || c == '_') {
            segment = true;
        } else return false;
    }
    return n > 0 && n < YS_CONTENT_ID_CAPACITY && segment && dot;
}
static bool kind_valid(YsContentKind kind) {
    return kind >= YS_CONTENT_MAP && kind <= YS_CONTENT_RULE;
}
static YsContentEntry *lookup(YsContentRegistry *registry, const char *id) {
    for (size_t i = 0; i < registry->count; ++i)
        if (strcmp(registry->entries[i].id, id) == 0)
            return &registry->entries[i];
    return NULL;
}
void ys_content_init(YsContentRegistry *registry) {
    if (registry) memset(registry, 0, sizeof(*registry));
}
const YsContentEntry *ys_content_find(const YsContentRegistry *registry,
                                      const char *id) {
    if (!registry || !valid_id(id)) return NULL;
    for (size_t i = 0; i < registry->count; ++i)
        if (strcmp(registry->entries[i].id, id) == 0)
            return &registry->entries[i];
    return NULL;
}
YsContentStatus ys_content_apply(YsContentRegistry *registry,
                                 const char *origin,
                                 const YsContentSpec *specs, size_t count) {
    if (!registry || !valid_id(origin) || (!specs && count) || count == 0 ||
        registry->count > YS_CONTENT_CAPACITY) return YS_CONTENT_INVALID;
    const bool base = strcmp(origin, "base.game") == 0;
    if (!base && strncmp(origin, "mod.", 4) != 0) return YS_CONTENT_INVALID;
    /* Reject applying a pack twice, even if all of its entries differ. */
    for (size_t i = 0; i < registry->count; ++i)
        if (strcmp(registry->entries[i].origin, origin) == 0)
            return YS_CONTENT_DUPLICATE;
    YsContentRegistry next = *registry;
    for (size_t i = 0; i < count; ++i) {
        const YsContentSpec *spec = &specs[i];
        if (!valid_id(spec->id) || !valid_id(spec->binding) ||
            !kind_valid(spec->kind) ||
            (spec->operation != YS_CONTENT_ADD &&
             spec->operation != YS_CONTENT_REPLACE) ||
            (base && spec->operation != YS_CONTENT_ADD))
            return YS_CONTENT_INVALID;
        for (size_t j = 0; j < i; ++j)
            if (strcmp(specs[j].id, spec->id) == 0)
                return YS_CONTENT_DUPLICATE;
        YsContentEntry *slot = lookup(&next, spec->id);
        if (spec->operation == YS_CONTENT_ADD) {
            if (slot) return YS_CONTENT_DUPLICATE;
            if (next.count == YS_CONTENT_CAPACITY)
                return YS_CONTENT_CAPACITY_EXCEEDED;
            slot = &next.entries[next.count++];
        } else {
            if (!slot) return YS_CONTENT_MISSING;
            /* Explicitly forbid two mods silently replacing the same entry. */
            if (strcmp(slot->origin, "base.game") != 0 ||
                slot->kind != spec->kind) return YS_CONTENT_CONFLICT;
        }
        strcpy(slot->id, spec->id);
        strcpy(slot->binding, spec->binding);
        strcpy(slot->origin, origin);
        slot->kind = spec->kind;
    }
    *registry = next; /* Pack is atomic; validation never partially commits. */
    return YS_CONTENT_OK;
}
