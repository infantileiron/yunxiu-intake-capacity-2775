<script setup lang="ts">
import {ref} from 'vue';
import type {Workspace} from '../stores/workspace';
import PageHeading from '../components/common/PageHeading.vue';
import Notice from '../components/common/Notice.vue';
import Status from '../components/common/Status.vue';
import {create} from '../api/scenarios';
import {create as run} from '../api/runs';
import {useAsync} from '../hooks/useAsync';
const props=defineProps<{data:Workspace;canWrite:boolean;refresh:()=>Promise<void>}>();
const emit=defineEmits<{go:[string]}>();
const name=ref(''),profile=ref(''),windows=ref(3),arrival=ref(1),service=ref(1),duration=ref(480),warmup=ref(120),reps=ref(30),seed=ref(2206);
// 候位容量与最长等候留空表示无限候位、不限等候（历史口径，旧方案据此复现）。
const capacityText=ref(''),maxWaitText=ref('');
const {busy,error,execute}=useAsync();
const optionalNumber=(v:string):number|null=>v.trim()===''?null:Number(v);
async function submit(){
 await execute(async()=>{
  await create({name:name.value,profile_id:profile.value||props.data.profiles[0]?.id,windows:windows.value,arrival_multiplier:arrival.value,service_multiplier:service.value,duration_minutes:duration.value,warmup_minutes:warmup.value,replications:reps.value,seed:seed.value,queue_capacity:optionalNumber(capacityText.value),max_wait_minutes:optionalNumber(maxWaitText.value)});
  name.value='';capacityText.value='';maxWaitText.value='';
  await props.refresh();
 });
}
async function launch(id:string){
 await execute(async()=>{await run({scenario_id:id});await props.refresh();emit('go','results')});
}
const capacityLabel=(v:number|null)=>v==null?'无限候位':`候位${v}位`;
const waitLabel=(v:number|null)=>v==null?'不限等候':`等候≤${v}分钟`;
</script>
<template>
 <PageHeading code="04 / COUNTER SCENARIOS" title="窗口数之外，把假设也写下来。" description="到达倍率作用于λ，服务倍率作用于单窗口μ。候位只计排队样本、不含在办样本；满员拒收，超时离队。两项留空即无限候位，按历史口径复现。固定随机种子保证可复现。"/>
 <section v-if="canWrite" class="paper">
  <h2>新建窗口预演</h2>
  <form class="scenario-form" @submit.prevent="submit">
   <label>方案名称<input aria-label="方案名称" v-model="name" required minlength="2"/></label>
   <label>输入剖面<select aria-label="输入剖面" v-model="profile"><option value="" disabled>默认使用最新剖面</option><option v-for="p in data.profiles" :key="p.id" :value="p.id">{{p.name}}</option></select></label>
   <label>窗口数 c<input aria-label="窗口数" type="number" min="1" max="12" v-model.number="windows"/></label>
   <label>到达倍率<input type="number" min=".2" max="3" step=".1" v-model.number="arrival"/></label>
   <label>服务倍率<input type="number" min=".2" max="3" step=".1" v-model.number="service"/></label>
   <label>候位容量 / 个（不含在办，留空无限）<input aria-label="候位容量" type="number" min="0" max="10000" step="1" placeholder="留空＝无限候位" v-model="capacityText"/></label>
   <label>最长等候 / 分钟（留空不限）<input aria-label="最长等候时间" type="number" min="1" step="1" placeholder="留空＝不限等候" v-model="maxWaitText"/></label>
   <label>观测时域 / 分钟<input type="number" min="60" max="1440" v-model.number="duration"/></label>
   <label>预热 / 分钟<input type="number" min="0" max="1440" v-model.number="warmup"/></label>
   <label>重复次数<input aria-label="重复次数" type="number" min="5" max="100" v-model.number="reps"/></label>
   <label>随机种子<input type="number" min="0" v-model.number="seed"/></label>
   <button :disabled="busy">保存窗口方案</button>
  </form>
 </section>
 <Notice v-if="error" error>{{error}}</Notice>
 <section class="paper">
  <h2>已保存方案</h2>
  <article v-for="s in data.scenarios" :key="s.id" class="scenario-row">
   <div class="counter-number">{{s.windows}}<small>WINDOWS</small></div>
   <div class="scenario-detail">
    <h3>{{s.name}}</h3>
    <p>{{data.profiles.find(p=>p.id===s.profile_id)?.name}}</p>
    <small>观测{{s.duration_minutes}}分钟 · 预热{{s.warmup_minutes}}分钟 · {{s.replications}}次重复 · seed {{s.seed}}</small>
    <small class="capacity-tag">{{capacityLabel(s.queue_capacity)}} · {{waitLabel(s.max_wait_minutes)}}<template v-if="s.queue_capacity==null&&s.max_wait_minutes==null">（历史无限候位口径）</template></small>
   </div>
   <button class="secondary" v-if="canWrite" :disabled="busy" @click="launch(s.id)">运行预演　→</button>
  </article>
 </section>
 <section class="paper">
  <h2>运行队列</h2>
  <div class="table-scroll">
   <table>
    <thead><tr><th>窗口方案</th><th>状态</th><th>提交时间</th></tr></thead>
    <tbody>
     <tr v-for="r in data.runs" :key="r.id"><td>{{data.scenarios.find(s=>s.id===r.scenario_id)?.name}}</td><td><Status :value="r.status"/></td><td>{{r.created_at.slice(0,19).replace('T',' ')}}</td></tr>
    </tbody>
   </table>
  </div>
 </section>
</template>
