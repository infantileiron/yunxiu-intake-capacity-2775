<script setup lang="ts">
import {ref,computed} from 'vue';
import type {Workspace} from '../stores/workspace';
import PageHeading from '../components/common/PageHeading.vue';
import Notice from '../components/common/Notice.vue';
import Status from '../components/common/Status.vue';
import Empty from '../components/common/Empty.vue';
import WindowComparison from '../components/WindowComparison.vue';
import ReplicationChart from '../components/ReplicationChart.vue';
import ServiceTimeline from '../components/ServiceTimeline.vue';
import {number,percent} from '../utils/format';
const props=defineProps<{data:Workspace}>();
const selected=ref('');
const run=computed(()=>props.data.runs.find(r=>r.id===selected.value)||props.data.runs[0]);
const waitText=(v:number|null|undefined)=>v==null?'不可估计':number(v);
</script>
<template>
 <PageHeading code="05 / WAITING & LOAD" title="理论给边界，仿真看波动。" description="解析稳态值与有限期仿真分开展示。有限候位下样本会被拒收或超时离队；观测期到达全部追踪到最终去向并与到达量对账。rho≥1时没有有限稳态等待。"/>
 <div class="run-selector">
  <label>运行记录<select aria-label="选择运行记录" :value="run?.id" @change="selected=($event.target as HTMLSelectElement).value"><option v-for="r in data.runs" :key="r.id" :value="r.id">{{data.scenarios.find(s=>s.id===r.scenario_id)?.name}} · {{r.created_at.slice(11,19)}}</option></select></label>
  <Status v-if="run" :value="run.status"/>
 </div>
 <Empty v-if="!run">请前往窗口方案，保存配置后运行后台预演。</Empty>
 <Notice v-else-if="run.status!=='completed'" :error="run.status==='failed'">{{run.status==='failed'?run.error:'预演已进入独立worker队列，结果会自动刷新。'}}</Notice>
 <template v-else>
  <Notice v-if="!run.result.analytic.stable" error>ρ = {{number(run.result.analytic.rho)}} ≥ 1：系统不稳定，无有限稳态平均等待。下方仿真仅为指定有限时域的暂态结果。</Notice>
  <section class="paper">
   <div class="section-heading">
    <h2>本次预演结果</h2>
    <span>λ {{number(run.result.analytic.arrival_rate,3)}} / μ {{number(run.result.analytic.service_rate,3)}} 每分钟</span>
   </div>
   <div class="result-metrics">
    <div><small>理论稳态平均等待</small><b>{{run.result.analytic.stable?number(run.result.analytic.mean_wait_minutes):'无有限值'}}</b><em>{{run.result.analytic.stable?'分钟':'ρ ≥ 1'}}</em></div>
    <div class="featured"><small>有限期仿真平均等待（仅办理样本）</small><b>{{waitText(run.result.simulation.mean_wait_minutes)}}</b><em>分钟</em></div>
    <div><small>重复试验95%区间</small><b class="range">{{run.result.simulation.mean_wait_minutes==null?'不可估计':number(run.result.simulation.mean_wait_ci95[0])+'—'+number(run.result.simulation.mean_wait_ci95[1])}}</b><em>分钟 / 正态近似</em></div>
    <div><small>有限期窗口忙碌比例</small><b>{{percent(run.result.simulation.busy_fraction)}}</b><em>按实际服务区间与观测期交集</em></div>
   </div>
   <WindowComparison :rows="run.result.comparison" :selected="run.result.analytic.windows"/>
  </section>

  <section class="paper">
   <div class="section-heading">
    <h2>样本去向对账</h2>
    <span>观测期到达 → 办理 / 拒收 / 离队</span>
   </div>
   <p v-if="!run.result.simulation.finite_capacity" class="caption">本方案为无限候位、不限等候：所有到达最终都被办理，无拒收与离队，按历史口径复现。</p>
   <div class="disposition-grid">
    <div><small>观测期到达</small><b>{{run.result.simulation.disposition.arrivals}}</b><em>条（全部重复合计）</em></div>
    <div><small>成功办理</small><b class="ok">{{run.result.simulation.disposition.served}}</b><em>等待仅统计这部分</em></div>
    <div><small>候位满拒收</small><b class="loss">{{run.result.simulation.disposition.rejected}}</b><em>容量不含在办样本</em></div>
    <div><small>超时离队</small><b class="loss">{{run.result.simulation.disposition.abandoned}}</b><em>超过最长等候</em></div>
    <div class="featured"><small>损失率</small><b>{{percent(run.result.simulation.disposition.loss_rate)}}</b><em>(拒收+离队)/到达</em></div>
   </div>
   <p class="reconcile">对账：办理 {{run.result.simulation.disposition.served}} ＋ 拒收 {{run.result.simulation.disposition.rejected}} ＋ 离队 {{run.result.simulation.disposition.abandoned}} ＝ {{run.result.simulation.disposition.served+run.result.simulation.disposition.rejected+run.result.simulation.disposition.abandoned}}，与到达 {{run.result.simulation.disposition.arrivals}} 一致。</p>
  </section>

  <div class="result-grid">
   <section class="paper">
    <h2>每次重复，会等多久？</h2>
    <ReplicationChart :rows="run.result.simulation.replications"/>
    <div class="simulation-settings">
     <span>{{run.result.simulation.duration_minutes}}分钟观测</span>
     <span>{{run.result.simulation.warmup_minutes}}分钟预热</span>
     <span>seed {{run.result.simulation.seed}}</span>
     <span v-if="run.result.simulation.finite_capacity">候位{{run.result.simulation.queue_capacity==null?'无限':run.result.simulation.queue_capacity}}位 · 等候{{run.result.simulation.max_wait_minutes==null?'不限':'≤'+run.result.simulation.max_wait_minutes+'分钟'}}</span>
    </div>
   </section>
   <aside class="model-note">
    <span class="eyebrow">MODEL BOUNDARIES</span>
    <h2>区间里，没有输入误差。</h2>
    <p>此区间只反映同一模型下重复随机流的波动，且等待指标仅覆盖成功办理样本；拒收与离队造成的损失见上方对账。到达率估计、峰值变化与服务差异需要另行复核。</p>
    <small>{{run.result.simulation.ci_method}}</small>
   </aside>
  </div>
  <section class="paper">
   <h2>每次重复去向明细</h2>
   <div class="table-scroll">
    <table>
     <thead><tr><th>重复</th><th>到达</th><th>办理</th><th>拒收</th><th>离队</th><th>损失率</th><th>平均等待</th><th>忙碌比例</th></tr></thead>
     <tbody>
      <tr v-for="r in run.result.simulation.replications" :key="r.replication">
       <td><b>#{{r.replication}}</b></td>
       <td>{{r.arrivals}}</td>
       <td>{{r.served}}</td>
       <td :class="{'loss-cell':r.rejected>0}">{{r.rejected}}</td>
       <td :class="{'loss-cell':r.abandoned>0}">{{r.abandoned}}</td>
       <td>{{percent(r.loss_rate)}}</td>
       <td>{{waitText(r.mean_wait_minutes)}}</td>
       <td>{{percent(r.busy_fraction)}}</td>
      </tr>
     </tbody>
    </table>
   </div>
  </section>
  <section class="paper">
   <h2>窗口服务时间轴</h2>
   <ServiceTimeline :events="run.result.simulation.timeline" :windows="run.result.analytic.windows"/>
  </section>
  <section class="paper">
   <h2>假设与适用边界</h2>
   <ol class="assumption-list"><li v-for="a in run.result.assumptions" :key="a">{{a}}</li></ol>
  </section>
 </template>
</template>
