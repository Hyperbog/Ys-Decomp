#include "pc_content.h"
#include <string.h>

static const char *const default_rows[YS_PC_MAP_H]={
    "################",
    "#..............#",
    "#...####.......#",
    "#..............#",
    "#......###.....#",
    "#..............#",
    "#..###.........#",
    "#..............#",
    "#........##....#",
    "#..............#",
    "#............G.#",
    "################"
};
static bool id_ok(const char *id) {
    if(!id || id[0]<'a' || id[0]>'z') return false;
    bool namespace_separator=false;
    for(size_t i=0;i<YS_PC_CONTENT_ID_SIZE;++i) {
        unsigned char c=(unsigned char)id[i];
        if(c==0u) return i>=3u && namespace_separator &&
                             id[i-1u]!='.';
        if(c=='.') {
            if(i==0u || id[i-1u]=='.') return false;
            namespace_separator=true;
        } else if(!((c>='a'&&c<='z') || (c>='0'&&c<='9') ||
                    c=='_' || c=='-')) return false;
    }
    return false; /* no NUL terminator within fixed-size ID */
}
void ys_pc_content_placeholder(YsPcSceneContent *out) {
    if(!out) return;
    YsPcSceneContent s={0};
    s.schema_version=YS_PC_CONTENT_SCHEMA;
    memcpy(s.id,"prototype.scene.test_room",sizeof("prototype.scene.test_room"));
    memcpy(s.player.id,"prototype.actor.player",sizeof("prototype.actor.player"));
    memcpy(s.foe.id,"prototype.actor.foe",sizeof("prototype.actor.foe"));
    for(unsigned y=0;y<YS_PC_MAP_H;++y)
        memcpy(s.cells[y],default_rows[y],YS_PC_MAP_W);
    s.player.x=2u;s.player.y=2u;s.player.hp=5u;
    s.foe.x=9u;s.foe.y=7u;s.foe.hp=3u;
    s.movement_ticks=8u;
    *out=s;
}
char ys_pc_content_cell(const YsPcSceneContent *scene,int x,int y) {
    if(!scene || x<0 || x>=YS_PC_MAP_W || y<0 || y>=YS_PC_MAP_H)
        return '#';
    return (char)scene->cells[y][x];
}
YsPcContentStatus ys_pc_content_validate(const YsPcSceneContent *s) {
    if(!s) return YS_PC_CONTENT_INVALID;
    if(s->schema_version!=YS_PC_CONTENT_SCHEMA)
        return YS_PC_CONTENT_VERSION;
    if(!id_ok(s->id)||!id_ok(s->player.id)||!id_ok(s->foe.id)||
       strcmp(s->player.id,s->foe.id)==0)
        return YS_PC_CONTENT_BAD_ID;
    if(s->next_scene_id[0]!=0 &&
       (!id_ok(s->next_scene_id) ||
        strcmp(s->next_scene_id,s->id)==0))
        return YS_PC_CONTENT_BAD_LINK;
    unsigned goal_count=0u;
    for(unsigned y=0;y<YS_PC_MAP_H;++y)
        for(unsigned x=0;x<YS_PC_MAP_W;++x) {
            unsigned t=s->cells[y][x];
            if(t!=YS_PC_WALL && t!=YS_PC_FLOOR && t!=YS_PC_GOAL)
                return YS_PC_CONTENT_BAD_TILE;
            if((x==0 || y==0 || x==YS_PC_MAP_W-1 ||
                y==YS_PC_MAP_H-1) && t!=YS_PC_WALL)
                return YS_PC_CONTENT_BAD_TILE;
            if(t==YS_PC_GOAL) ++goal_count;
        }
    if(goal_count!=1u || s->movement_ticks==0u ||
       s->movement_ticks>60u ||
       s->player.hp==0u || s->player.hp>20u ||
       s->foe.hp==0u || s->foe.hp>20u ||
       s->player.x>=YS_PC_MAP_W || s->player.y>=YS_PC_MAP_H ||
       s->foe.x>=YS_PC_MAP_W || s->foe.y>=YS_PC_MAP_H ||
       (s->player.x==s->foe.x && s->player.y==s->foe.y) ||
       ys_pc_content_cell(s,s->player.x,s->player.y)!=YS_PC_FLOOR ||
       ys_pc_content_cell(s,s->foe.x,s->foe.y)!=YS_PC_FLOOR)
        return YS_PC_CONTENT_BAD_SPAWN;
    return YS_PC_CONTENT_OK;
}
bool ys_pc_content_route_ok(const YsPcSceneContent *scene) {
    if(ys_pc_content_validate(scene)!=YS_PC_CONTENT_OK) return false;
    bool visited[YS_PC_MAP_H][YS_PC_MAP_W]={0};
    uint8_t queue_x[YS_PC_MAP_W*YS_PC_MAP_H];
    uint8_t queue_y[YS_PC_MAP_W*YS_PC_MAP_H];
    unsigned front=0u,back=0u;
    const unsigned px=scene->player.x,py=scene->player.y;
    visited[py][px]=true;
    queue_x[back]=(uint8_t)px;queue_y[back]=(uint8_t)py;++back;
    bool goal=false,foe=false;
    while(front<back) {
        unsigned x=queue_x[front],y=queue_y[front];++front;
        if(x==scene->foe.x && y==scene->foe.y) foe=true;
        if(scene->cells[y][x]==YS_PC_GOAL) goal=true;
        static const int8_t dx[4]={-1,1,0,0};
        static const int8_t dy[4]={0,0,-1,1};
        for(unsigned dir=0;dir<4u;++dir) {
            int xx=(int)x+dx[dir],yy=(int)y+dy[dir];
            if(xx<0 || yy<0 || xx>=YS_PC_MAP_W ||
               yy>=YS_PC_MAP_H || visited[yy][xx] ||
               scene->cells[yy][xx]==YS_PC_WALL) continue;
            visited[yy][xx]=true;
            queue_x[back]=(uint8_t)xx;
            queue_y[back]=(uint8_t)yy;
            ++back;
        }
    }
    return goal && foe;
}
void ys_pc_catalog_init(YsPcContentCatalog *catalog) {
    if(catalog) memset(catalog,0,sizeof(*catalog));
}
static size_t where(const YsPcContentCatalog *cat,const char *id) {
    size_t i=0u;
    while(i<cat->count && strcmp(cat->scenes[i].id,id)<0) ++i;
    return i;
}
YsPcContentStatus ys_pc_catalog_apply(YsPcContentCatalog *cat,
                                      const YsPcSceneContent *scene,
                                      bool replace_existing) {
    if(!cat) return YS_PC_CONTENT_INVALID;
    YsPcContentStatus status=ys_pc_content_validate(scene);
    if(status!=YS_PC_CONTENT_OK) return status;
    if(cat->count>YS_PC_CONTENT_MAX_SCENES)
        return YS_PC_CONTENT_INVALID;
    size_t pos=where(cat,scene->id);
    bool found=pos<cat->count && strcmp(cat->scenes[pos].id,scene->id)==0;
    if(found) {
        if(!replace_existing) return YS_PC_CONTENT_CONFLICT;
        cat->scenes[pos]=*scene;
        return YS_PC_CONTENT_OK;
    }
    if(replace_existing) return YS_PC_CONTENT_NOT_FOUND;
    if(cat->count==YS_PC_CONTENT_MAX_SCENES)
        return YS_PC_CONTENT_FULL;
    for(size_t i=cat->count;i>pos;--i)
        cat->scenes[i]=cat->scenes[i-1u];
    cat->scenes[pos]=*scene;
    ++cat->count;
    return YS_PC_CONTENT_OK;
}
const YsPcSceneContent *ys_pc_catalog_find(const YsPcContentCatalog *cat,
                                           const char *id) {
    if(!cat || !id || !id_ok(id) || cat->count>YS_PC_CONTENT_MAX_SCENES)
        return NULL;
    size_t pos=where(cat,id);
    return pos<cat->count && strcmp(cat->scenes[pos].id,id)==0 ?
        &cat->scenes[pos]:NULL;
}
