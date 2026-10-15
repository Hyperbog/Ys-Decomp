#ifndef YS_PC_CONTENT_H
#define YS_PC_CONTENT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum { YS_PC_MAP_W=16, YS_PC_MAP_H=12,
       YS_PC_CONTENT_SCHEMA=1, YS_PC_CONTENT_ID_SIZE=64,
       YS_PC_CONTENT_MAX_SCENES=8 };
enum { YS_PC_WALL='#', YS_PC_FLOOR='.', YS_PC_GOAL='G' };

typedef struct {
    char id[YS_PC_CONTENT_ID_SIZE];
    uint8_t x,y,hp;
} YsPcActorSpawn;

/* Experimental canonical SCENE DATA, not a ROM address, a mod
   package/save format, or a recovered Ys location. */
typedef struct {
    uint32_t schema_version;
    char id[YS_PC_CONTENT_ID_SIZE];
    uint8_t cells[YS_PC_MAP_H][YS_PC_MAP_W];
    YsPcActorSpawn player, foe;
    uint8_t movement_ticks;
    /* Empty => terminal scene; otherwise next canonical symbolic scene ID.
       This is experimental native in-memory content, NOT original Ys data. */
    char next_scene_id[YS_PC_CONTENT_ID_SIZE];
} YsPcSceneContent;

typedef enum {
    YS_PC_CONTENT_OK=0,
    YS_PC_CONTENT_INVALID,
    YS_PC_CONTENT_VERSION,
    YS_PC_CONTENT_BAD_ID,
    YS_PC_CONTENT_BAD_TILE,
    YS_PC_CONTENT_BAD_SPAWN,
    YS_PC_CONTENT_CONFLICT,
    YS_PC_CONTENT_NOT_FOUND,
    YS_PC_CONTENT_FULL,
    YS_PC_CONTENT_BAD_LINK
} YsPcContentStatus;
typedef struct {
    size_t count;
    YsPcSceneContent scenes[YS_PC_CONTENT_MAX_SCENES];
} YsPcContentCatalog;

/* Recreates the ORIGINAL PC-0 PLACEHOLDER, not a faithful Ys map. */
void ys_pc_content_placeholder(YsPcSceneContent *out);
YsPcContentStatus ys_pc_content_validate(const YsPcSceneContent *scene);
/* A scene must have a traversable route to its foe and goal (potentially
   after defeating foe). This is prototype geometry, not Ys wall data. */
bool ys_pc_content_route_ok(const YsPcSceneContent *scene);
char ys_pc_content_cell(const YsPcSceneContent *scene,int x,int y);
/* add/replace by NAMESPACED symbolic scene ID, deterministic sorted
   order. Fails before mutation on invalid/duplicate/missing/full. */
void ys_pc_catalog_init(YsPcContentCatalog *catalog);
YsPcContentStatus ys_pc_catalog_apply(YsPcContentCatalog *catalog,
                                      const YsPcSceneContent *scene,
                                      bool replace_existing);
const YsPcSceneContent *ys_pc_catalog_find(const YsPcContentCatalog *catalog,
                                           const char *id);
#endif
