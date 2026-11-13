import random,statistics,math
from src.services.scheduler import schedule,SERVED,REJECTED,ABANDONED

def simulate(arrival_rate,service_rate,windows,duration,warmup,replications,seed,queue_capacity=None,max_wait=None):
 if arrival_rate<=0 or service_rate<=0 or windows<1 or duration<=0 or warmup<0 or replications<2:raise ValueError("无效仿真参数")
 if arrival_rate*(duration+warmup)>20000:raise ValueError("预期到达超过20000条，请缩短时域或降低负荷")
 if queue_capacity is not None and (not isinstance(queue_capacity,int) or queue_capacity<0):raise ValueError("候位容量须为非负整数或为空")
 if max_wait is not None and (not math.isfinite(max_wait) or max_wait<=0):raise ValueError("最长等候时间须为有限正数或为空")
 finite=queue_capacity is not None or max_wait is not None
 results=[];last_events=[];end=warmup+duration
 for rep in range(replications):
  rng=random.Random(seed+rep);arrivals=[];services=[];t=0
  while True:
   t+=rng.expovariate(arrival_rate)
   if t>=end:break
   arrivals.append(t);services.append(rng.expovariate(service_rate))
   if len(arrivals)>50000:raise ValueError("单次仿真事件超过50000条")
  events=schedule(arrivals,services,windows,queue_capacity,max_wait)
  # 观测期到达全部追踪到最终去向：办理、拒收、离队。
  observed=[e for e in events if e["arrival"]>=warmup]
  if not observed:raise ValueError("观测时域没有到达，请增大时域")
  n_arrivals=len(observed)
  served=[e for e in observed if e["outcome"]==SERVED]
  n_served=len(served);n_rejected=sum(e["outcome"]==REJECTED for e in observed);n_abandoned=sum(e["outcome"]==ABANDONED for e in observed)
  # 对账：三类去向之和必须等于观测期到达量。
  if n_served+n_rejected+n_abandoned!=n_arrivals:raise ValueError("去向聚合与到达量对账失败")
  # 等待只统计实际办理的样本；被拒收与离队样本不进入等待统计。
  waits=[e["wait"] for e in served]
  # 忙碌比例按实际服务区间与观测期的交集积分，分母为窗口数×观测分钟。
  busy=sum(max(0,min(e["end"],end)-max(e["start"],warmup)) for e in events if e["outcome"]==SERVED)
  row={"replication":rep+1,"arrivals":n_arrivals,"served":n_served,"rejected":n_rejected,
       "abandoned":n_abandoned,"loss_rate":(n_rejected+n_abandoned)/n_arrivals,
       "busy_fraction":busy/(windows*duration)}
  if waits:
   row.update({"mean_wait_minutes":statistics.mean(waits),"p_wait":sum(x>1e-9 for x in waits)/len(waits),"max_wait_minutes":max(waits)})
  else:
   # 观测期没有任何样本成功办理时，等待指标不可估计。
   row.update({"mean_wait_minutes":None,"p_wait":None,"max_wait_minutes":None})
  results.append(row)
  last_events=observed[:80]
 wait_means=[r["mean_wait_minutes"] for r in results if r["mean_wait_minutes"] is not None]
 if wait_means:
  mean=statistics.mean(wait_means)
  se=statistics.stdev(wait_means)/math.sqrt(len(wait_means)) if len(wait_means)>1 else 0.0
  ci=[max(0,mean-1.96*se),mean+1.96*se]
  p_wait=statistics.mean(r["p_wait"] for r in results if r["p_wait"] is not None)
 else:
  mean=None;ci=[None,None];p_wait=None
 total_arrivals=sum(r["arrivals"] for r in results);total_served=sum(r["served"] for r in results)
 total_rejected=sum(r["rejected"] for r in results);total_abandoned=sum(r["abandoned"] for r in results)
 return {"mean_wait_minutes":mean,"mean_wait_ci95":ci,"p_wait":p_wait,
         "busy_fraction":statistics.mean(r["busy_fraction"] for r in results),
         "queue_capacity":queue_capacity,"max_wait_minutes":max_wait,"finite_capacity":finite,
         "disposition":{"arrivals":total_arrivals,"served":total_served,"rejected":total_rejected,
                        "abandoned":total_abandoned,"loss_rate":(total_rejected+total_abandoned)/total_arrivals},
         "replications":results,"timeline":last_events,"duration_minutes":duration,
         "warmup_minutes":warmup,"seed":seed,
         "ci_method":"重复试验均值的正态近似95%区间（1.96×重复均值标准误）；等待仅统计成功办理样本"}
