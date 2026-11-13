<script setup lang="ts">
import {computed} from 'vue';
import type {Replication} from '../types/domain';
import {number} from '../utils/format';
const props=defineProps<{rows:Replication[]}>();
const chartable=computed(()=>props.rows.filter(r=>r.mean_wait_minutes!=null));
const max=computed(()=>Math.max(1,...chartable.value.map(r=>r.mean_wait_minutes as number)));
</script>
<template>
 <div class="rep-chart">
  <svg viewBox="0 0 600 230" aria-label="重复仿真平均等待分钟（仅办理样本）">
   <line x1="35" y1="195" x2="585" y2="195"/>
   <line x1="35" y1="15" x2="35" y2="195"/>
   <g v-for="v in [0,.5,1]" :key="v">
    <line x1="35" x2="585" :y1="195-v*165" :y2="195-v*165" class="grid"/>
    <text x="0" :y="199-v*165">{{number(max*v,1)}}</text>
   </g>
   <rect v-for="(r,i) in chartable" :key="r.replication" :x="43+i*535/Math.max(1,chartable.length)" :y="195-(r.mean_wait_minutes as number)/max*165" :width="Math.max(2,480/Math.max(1,chartable.length))" :height="(r.mean_wait_minutes as number)/max*165">
    <title>重复{{r.replication}}：平均等待{{number(r.mean_wait_minutes)}}分钟，办理{{r.served}}/到达{{r.arrivals}}，拒收{{r.rejected}}、离队{{r.abandoned}}</title>
   </rect>
   <text x="205" y="225">独立随机流 · 重复试验序号 →（等待仅含办理样本）</text>
  </svg>
  <p v-if="!chartable.length" class="caption">各重复均无成功办理样本，平均等待不可估计；请查看到去向对账与损失率。</p>
 </div>
</template>
