#include "pc_collision_routes.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const uint16_t addresses[3]={0x47C2u,0x486Cu,0x48DFu};

static void test_guards(void) {
    YsPcCollisionTable table={0};
    table.boxes[2]=(YsPcCollisionBox){200u,20u,201u,20u};
    table.boxes[3]=(YsPcCollisionBox){7u,11u,9u,13u};
    YsPcCollisionCallState state={
        4u,3u,2u,{80u,80u,24u,0u,25u,0u}
    };
    YsPcCollisionCallResult result={0xBEEFu,99u,true};
    YsPcCollisionCallResult before=result;
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_OK);
    assert(result.original_source_pc==addresses[0] &&
           result.descriptor_index==2u && result.carry);
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_CONTACT,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_OK);
    assert(result.original_source_pc==addresses[1] &&
           result.descriptor_index==2u && result.carry);
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_ALTERNATE,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_OK);
    assert(result.original_source_pc==addresses[2] &&
           result.descriptor_index==3u && !result.carry);
    result=before;
    state.slot2_bank=7u;
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_WRONG_BANK);
    assert(memcmp(&result,&before,sizeof(result))==0);
    state.slot2_bank=4u;
    state.ix14=31u;
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_BAD_INDEX);
    assert(memcmp(&result,&before,sizeof(result))==0);
    state.ix14=2u;state.ix13=255u;
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_ALTERNATE,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_BAD_INDEX);
    assert(memcmp(&result,&before,sizeof(result))==0);
    assert(ys_pc_collision_route_eval(NULL,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     NULL,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_eval(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &state,NULL)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_eval(&table,(YsPcCollisionRoute)-1,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_eval(&table,(YsPcCollisionRoute)3,
                                     &state,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(memcmp(&result,&before,sizeof(result))==0);
}
static void test_frame_bounds(void) {
    YsPcCollisionTable table={0};
    table.boxes[1]=(YsPcCollisionBox){200u,20u,201u,20u};
    table.boxes[2]=table.boxes[1];
    YsPcCollisionFrameInput frame={
        4u,1u,1u,80u,80u,
        2u,2u,80u,80u
    };
    YsPcCollisionCallResult result={0xCAFEu,99u,true};
    for(unsigned route=0u;route<3u;++route) {
        assert(ys_pc_collision_route_frame(&table,
                  (YsPcCollisionRoute)route,&frame,&result)==
                  YS_PC_COLLISION_ROUTE_OK);
        assert(result.original_source_pc==addresses[route] &&
               result.descriptor_index==2u && result.carry);
    }
    const YsPcCollisionCallResult before=result;
    frame.c20d=0u;
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_INACTIVE);
    assert(memcmp(&result,&before,sizeof(result))==0);
    frame.c20d=128u;
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_CONTACT,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_INACTIVE);
    frame.c20d=31u;
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_CONTACT,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_BAD_INDEX);
    frame.c20d=1u;frame.c20e=0u;
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_ALTERNATE,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_INACTIVE);
    frame.c20e=1u;frame.slot2_bank=7u;
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_WRONG_BANK);
    assert(memcmp(&result,&before,sizeof(result))==0);
    assert(ys_pc_collision_route_frame(NULL,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_frame(&table,(YsPcCollisionRoute)3,
                                     &frame,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     NULL,&result)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(ys_pc_collision_route_frame(&table,YS_PC_COLLISION_ROUTE_FORWARD,
                                     &frame,NULL)==YS_PC_COLLISION_ROUTE_BAD_ARGUMENT);
    assert(memcmp(&result,&before,sizeof(result))==0);
}
static void source_cases(const char *path) {
    FILE *f=fopen(path,"rb");assert(f);
    YsPcCollisionTable table;
    assert(ys_pc_collision_load(f,&table));
    fclose(f);
    unsigned count=0u,positives[3]={0},negatives[3]={0};
    for(unsigned index=0;index<YS_PC_COLLISION_BOXES;++index) {
        YsPcCollisionBox box=table.boxes[index];
        for(unsigned seed=0;seed<16u;++seed) {
            uint8_t oy=(uint8_t)(seed*17u+33u);
            uint8_t ox=(uint8_t)(seed*29u+51u);
            uint8_t ya=(uint8_t)((unsigned)box.y_offset+oy);
            uint8_t xa=(uint8_t)((unsigned)box.x_offset+ox);
            for(unsigned variant=0;variant<8u;++variant) {
                YsPcCollisionCallState state={
                    4u,(uint8_t)index,(uint8_t)index,
                    {oy,ox,(uint8_t)(ya+variant%3u),
                     (uint8_t)((unsigned)ya+box.y_extent-1u+
                         (variant/3u)%3u),
                     (uint8_t)(xa+variant%3u),
                     (uint8_t)((unsigned)xa+box.x_extent-1u+
                         (variant/3u)%3u)}
                };
                bool direct=false;
                assert(ys_pc_collision_eval(&table,index,&state.probe,&direct));
                for(unsigned r=0;r<3u;++r) {
                    YsPcCollisionCallResult value={0};
                    assert(ys_pc_collision_route_eval(&table,(YsPcCollisionRoute)r,
                        &state,&value)==YS_PC_COLLISION_ROUTE_OK);
                    assert(value.original_source_pc==addresses[r] &&
                           value.descriptor_index==index &&
                           value.carry==direct);
                    if(value.carry) ++positives[r];
                    else ++negatives[r];
                }
                ++count;
            }
        }
    }
    assert(count==3968u);
    for(unsigned r=0;r<3u;++r)
        assert(positives[r]==3033u && negatives[r]==935u);
    /* Verify actual original-source target-box formation for 30 valid
       nonzero entries x 8 distinct offset seeds x all three paths.
       The first source index is zero and returns before the worker. */
    unsigned prepared=0u;
    for(unsigned target=1u;target<YS_PC_COLLISION_BOXES;++target) {
        YsPcCollisionBox box=table.boxes[target];
        for(unsigned seed=0u;seed<8u;++seed) {
            YsPcCollisionFrameInput frame={
                4u,(uint8_t)target,(uint8_t)target,
                (uint8_t)(seed*11u+57u),(uint8_t)(seed*23u+101u),
                (uint8_t)target,(uint8_t)target,
                (uint8_t)(seed*31u+17u),(uint8_t)(seed*19u+39u)
            };
            uint8_t y=(uint8_t)((unsigned)frame.c211+box.y_offset);
            uint8_t x=(uint8_t)((unsigned)frame.c210+box.x_offset);
            YsPcCollisionProbe p={
                frame.ix17,frame.ix16,
                (uint8_t)((unsigned)y+box.y_extent),y,
                (uint8_t)((unsigned)x+box.x_extent),x
            };
            bool direct=false;
            assert(ys_pc_collision_eval(&table,target,&p,&direct));
            for(unsigned route=0;route<3u;++route) {
                YsPcCollisionCallResult got={0};
                assert(ys_pc_collision_route_frame(&table,
                    (YsPcCollisionRoute)route,&frame,&got)==
                    YS_PC_COLLISION_ROUTE_OK);
                assert(got.carry==direct && got.descriptor_index==target);
                ++prepared;
            }
        }
    }
    assert(prepared==720u);
    puts("PASS PC-11: 3 bank1 routes x 3968 reference cases (11904),"
         " explicit bank4 mapping and IX+14/+13 selection");
}
int main(int argc,char **argv) {
    assert(argc==1 || argc==2);
    test_guards();
    test_frame_bounds();
    if(argc==2) source_cases(argv[1]);
    puts("PASS PC-11: wrong bank, invalid index, unknown call site,"
         " original-source routing and fail-closed outputs");
    return 0;
}
