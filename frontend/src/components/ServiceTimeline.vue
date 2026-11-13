<script setup lang="ts">
import {computed} from 'vue';
import type {Event} from '../types/domain';
const props=defineProps<{events:Event[];windows:number}>();
// 时间轴只绘制成功办理事件；拒收/离队样本没有服务区间，改在图例统计。
const sample=computed(()=>props.events.filter(e=>e.outcome==='served').slice(0,35));
const lossCount=computed(()=>props.events.filter(e=>e.outcome!=='served').length);
const lo=computed(()=>Math.min(...sample.value.map(e=>e.arrival)));
const hi=computed(()=>sample.value.length?Math.max(...sample.value.map(e=>e.end as number),lo.value+1):lo.value+1);
const x=(t:number)=>60+(t-lo.value)/(hi.value-lo.value)*510;
</script>
<template>
 <svg v-if="sample.length" class="timeline" :viewBox="`0 0 600 ${windows*42+60}`" aria-label="窗口服务事件时间轴">
  <g v-for="s in windows" :key="s">
   <text x="5" :y="s*42+5">窗口{{s}}</text>
   <line x1="60" x2="580" :y1="s*42" :y2="s*42"/>
  </g>
  <g v-for="e in sample" :key="e.job">
   <line :x1="x(e.arrival)" :x2="x(e.start as number)" :y1="(e.server as number)*42-9" :y2="(e.server as number)*42-9" class="waiting"/>
   <rect :x="x(e.start as number)" :y="(e.server as number)*42-6" :width="Math.max(1,x(e.end as number)-x(e.start as number))" height="12">
    <title>样本{{e.job}}等待{{(e.wait as number).toFixed(2)}}分钟，服务{{e.service.toFixed(2)}}分钟</title>
   </rect>
  </g>
  <text x="60" :y="windows*42+42">最后一次重复 · 前35个办理事件 · 橙线等待 / 绿块服务<template v-if="lossCount"> · 另有{{lossCount}}个拒收/离队事件无服务区间</template></text>
 </svg>
 <p v-else class="caption">最后一次重复的观测期没有成功办理样本，无法绘制服务时间轴；请查看到去向对账与损失率。</p>
</template>
