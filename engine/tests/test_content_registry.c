#include "content_registry.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static YsContentRegistry registry;
int main(void) {
    ys_content_init(&registry);
    const YsContentSpec base[] = {
        {"base.map.start", YS_CONTENT_MAP, "base.asset.start", YS_CONTENT_ADD},
        {"base.entity.hero", YS_CONTENT_ENTITY, "base.asset.hero", YS_CONTENT_ADD}
    };
    assert(ys_content_apply(&registry, "base.game", base, 2) == YS_CONTENT_OK);
    assert(registry.count == 2);
    assert(strcmp(ys_content_find(&registry, "base.map.start")->origin,
                  "base.game") == 0);
    const YsContentSpec changes[] = {
        {"base.map.start", YS_CONTENT_MAP, "mod.asset.new_map", YS_CONTENT_REPLACE},
        {"mod.quest.new", YS_CONTENT_QUEST, "mod.asset.new_quest", YS_CONTENT_ADD}
    };
    assert(ys_content_apply(&registry, "mod.author.pack", changes, 2) == YS_CONTENT_OK);
    assert(registry.count == 3);
    assert(strcmp(ys_content_find(&registry, "base.map.start")->binding,
                  "mod.asset.new_map") == 0);
    assert(strcmp(ys_content_find(&registry, "base.entity.hero")->binding,
                  "base.asset.hero") == 0);
    assert(ys_content_apply(&registry, "mod.author.pack", changes, 2) ==
           YS_CONTENT_DUPLICATE);
    const YsContentSpec conflict[] = {
        {"base.map.start", YS_CONTENT_MAP, "other.asset.map", YS_CONTENT_REPLACE}
    };
    assert(ys_content_apply(&registry, "mod.other.pack", conflict, 1) ==
           YS_CONTENT_CONFLICT);
    assert(strcmp(ys_content_find(&registry, "base.map.start")->origin,
                  "mod.author.pack") == 0);
    const YsContentSpec atomic[] = {
        {"mod.entity.npc", YS_CONTENT_ENTITY, "mod.asset.npc", YS_CONTENT_ADD},
        {"base.entity.absent", YS_CONTENT_ENTITY, "mod.asset.absent", YS_CONTENT_REPLACE}
    };
    assert(ys_content_apply(&registry, "mod.atomic.pack", atomic, 2) ==
           YS_CONTENT_MISSING);
    assert(!ys_content_find(&registry, "mod.entity.npc"));
    assert(registry.count == 3);
    const YsContentSpec malformed[] = {
        {"../rom", YS_CONTENT_MAP, "mod.asset.bad", YS_CONTENT_ADD}
    };
    assert(ys_content_apply(&registry, "mod.bad.pack", malformed, 1) ==
           YS_CONTENT_INVALID);
    const YsContentSpec kind_change[] = {
        {"base.entity.hero", YS_CONTENT_QUEST, "mod.asset.hero", YS_CONTENT_REPLACE}
    };
    assert(ys_content_apply(&registry, "mod.kind.pack", kind_change, 1) ==
           YS_CONTENT_CONFLICT);
    assert(!ys_content_find(&registry, "INVALID_ID"));
    assert(ys_content_apply(&registry, "base.game", base, 2) ==
           YS_CONTENT_DUPLICATE);
    puts("PASS: stable IDs, deterministic additions, overrides, conflicts, atomic failure");
    return 0;
}
