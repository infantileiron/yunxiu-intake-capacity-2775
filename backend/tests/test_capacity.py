import os,sys,heapq,random,statistics,unittest
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.services.scheduler import schedule,SERVED,REJECTED,ABANDONED
from src.services.simulation import simulate

def legacy_schedule(arrivals,services,windows):
 servers=[(0.0,i+1) for i in range(windows)];heapq.heapify(servers);events=[]
 for i,(arrival,service) in enumerate(zip(arrivals,services)):
  free,server=heapq.heappop(servers);start=max(arrival,free);end=start+service
  events.append({"job":i+1,"arrival":arrival,"service":service,"start":start,"end":end,"wait":start-arrival,"server":server})
  heapq.heappush(servers,(end,server))
 return events

def gen(rate,srate,end,seed):
 rng=random.Random(seed);arrivals=[];services=[];t=0
 while True:
  t+=rng.expovariate(rate)
  if t>=end:break
  arrivals.append(t);services.append(rng.expovariate(srate))
 return arrivals,services

class SchedulerTests(unittest.TestCase):
 def test_infinite_matches_legacy(self):
  for seed in range(30):
   arrivals,services=gen(0.4,0.2,600,seed)
   new=schedule(arrivals,services,3,None,None)
   old=legacy_schedule(arrivals,services,3)
   self.assertEqual(len(new),len(old))
   for a,b in zip(new,old):
    self.assertEqual(a["job"],b["job"]);self.assertAlmostEqual(a["start"],b["start"])
    self.assertAlmostEqual(a["end"],b["end"]);self.assertAlmostEqual(a["wait"],b["wait"])
    self.assertEqual(a["server"],b["server"]);self.assertEqual(a["outcome"],SERVED)

 def test_capacity_zero_rejects_while_busy(self):
  arrivals=[0,1,2,30];services=[10,10,10,10]
  events=schedule(arrivals,services,1,0,None)
  outcomes=[e["outcome"] for e in events]
  self.assertEqual(outcomes,[SERVED,REJECTED,REJECTED,SERVED])
  self.assertTrue(all(e["wait"] is None for e in events if e["outcome"]!=SERVED))

 def test_capacity_excludes_in_service(self):
  # 1个窗口在办 + 候位容量1：第1个排队，第2个被拒收；在办样本不占候位。
  arrivals=[0,1,2];services=[10,10,10]
  events=schedule(arrivals,services,1,1,None)
  by_job={e["job"]:e["outcome"] for e in events}
  self.assertEqual([by_job[1],by_job[2],by_job[3]],[SERVED,SERVED,REJECTED])

 def test_abandonment_on_timeout(self):
  arrivals=[0,1,1,1];services=[10,10,10,10]
  events=schedule(arrivals,services,1,1,0.5)
  by_job={e["job"]:e["outcome"] for e in events}
  self.assertEqual([by_job[1],by_job[2],by_job[3],by_job[4]],[SERVED,ABANDONED,REJECTED,REJECTED])
  abandoned=[e for e in events if e["outcome"]==ABANDONED][0]
  self.assertIsNone(abandoned["start"]);self.assertIsNone(abandoned["server"])

 def test_same_time_completion_before_arrival(self):
  # 容量0：到达恰好在窗口完成时刻，先释放窗口再接样，应被办理而非拒收。
  arrivals=[0,10];services=[10,5]
  events=schedule(arrivals,services,1,0,None)
  self.assertEqual([e["outcome"] for e in events],[SERVED,SERVED])
  self.assertAlmostEqual(events[1]["wait"],0.0)

 def test_same_time_timeout_before_arrival(self):
  # 队首在t=2超时离队，同时刻新到达：先离队腾出候位，新样本入队并在窗口释放时办理。
  arrivals=[0,1,2];services=[3,3,3]
  events=schedule(arrivals,services,1,1,1.0)
  by_job={e["job"]:e["outcome"] for e in events}
  self.assertEqual([by_job[1],by_job[2],by_job[3]],[SERVED,ABANDONED,SERVED])
  third=[e for e in events if e["job"]==3][0]
  self.assertAlmostEqual(third["start"],3.0);self.assertAlmostEqual(third["wait"],1.0)

 def test_same_time_timeout_and_another_timeout_event(self):
  # 同刻两个超时事件与一个到达共存：类型顺序恒定，到达在全部离队之后处理。
  arrivals=[0,1,1,2];services=[10,10,10,10]
  events=schedule(arrivals,services,1,2,1.0)
  by_job={e["job"]:e["outcome"] for e in events}
  # 窗口被job1占到t=10；job2/job3在t=2同时超时；job4在t=2到达时两候位已空，入队后也将超时。
  self.assertEqual(by_job[1],SERVED);self.assertEqual(by_job[2],ABANDONED)
  self.assertEqual(by_job[3],ABANDONED);self.assertEqual(by_job[4],ABANDONED)

 def test_warmup_occupancy_persists(self):
  # 预热期样本长服务延续到观测期，容量0时观测期到达被其占位拒收。
  arrivals=[0,5];services=[100,5]
  events=schedule(arrivals,services,1,0,None)
  self.assertEqual([e["outcome"] for e in events],[SERVED,REJECTED])

 def test_reconciliation_random(self):
  rng=random.Random(7)
  for cap,mw in [(2,15.0),(0,10.0),(5,None),(None,8.0),(1,3.0)]:
   arrivals,services=gen(0.6,0.25,400,rng.randrange(1<<30))
   events=schedule(arrivals,services,3,cap,mw)
   counts={SERVED:0,REJECTED:0,ABANDONED:0}
   for e in events:counts[e["outcome"]]+=1
   self.assertEqual(sum(counts.values()),len(arrivals))
   served=[e for e in events if e["outcome"]==SERVED]
   if cap is not None:
    # 时间轴不变量：任何时刻在办窗口不超过3、候位不超过容量。
    boundary={0.0}
    for e in served:boundary.update((e["start"],e["end"]))
    for e in events:boundary.add(e["arrival"])
    for t in sorted(boundary):
     busy=sum(1 for s in served if s["start"]<=t<s["end"])
     queued=sum(1 for s in served if s["arrival"]<=t<s["start"])
     self.assertLessEqual(busy,3);self.assertLessEqual(queued,cap)
     # 被拒收时刻：窗口必然全忙；无超时配置时候位必然已满（在办不计入候位）。
    for e in events:
     if e["outcome"]==REJECTED:
      t=e["arrival"]
      busy=sum(1 for s in served if s["start"]<=t<s["end"])
      queued=sum(1 for s in served if s["arrival"]<=t<s["start"])
      self.assertEqual(busy,3)
      if mw is None:self.assertEqual(queued,cap)

class SimulationTests(unittest.TestCase):
 def test_infinite_results_match_legacy_metrics(self):
  out=simulate(0.4,0.2,3,480,120,20,2206)
  legacy_rows=[]
  for rep in range(20):
   rng=random.Random(2206+rep);arrivals=[];services=[];t=0
   while True:
    t+=rng.expovariate(0.4)
    if t>=600:break
    arrivals.append(t);services.append(rng.expovariate(0.2))
   events=legacy_schedule(arrivals,services,3)
   observed=[e for e in events if e["arrival"]>=120]
   waits=[e["wait"] for e in observed]
   legacy_rows.append((len(observed),statistics.mean(waits),max(waits)))
  for row,(n,mw,mx) in zip(out["replications"],legacy_rows):
   self.assertEqual(row["arrivals"],n);self.assertEqual(row["served"],n)
   self.assertEqual(row["rejected"],0);self.assertEqual(row["abandoned"],0)
   self.assertEqual(row["loss_rate"],0.0)
   self.assertAlmostEqual(row["mean_wait_minutes"],mw)
   self.assertAlmostEqual(row["max_wait_minutes"],mx)
  self.assertIsNone(out["queue_capacity"]);self.assertFalse(out["finite_capacity"])

 def test_finite_reconciliation_and_loss(self):
  out=simulate(0.6,0.25,2,480,60,25,2206,queue_capacity=2,max_wait=15)
  self.assertTrue(out["finite_capacity"])
  for r in out["replications"]:
   self.assertEqual(r["served"]+r["rejected"]+r["abandoned"],r["arrivals"])
   self.assertAlmostEqual(r["loss_rate"],(r["rejected"]+r["abandoned"])/r["arrivals"])
   self.assertGreaterEqual(r["rejected"]+r["abandoned"],0)
   self.assertLessEqual(r["busy_fraction"],1.0)
  d=out["disposition"]
  self.assertEqual(d["served"]+d["rejected"]+d["abandoned"],d["arrivals"])
  self.assertGreater(d["loss_rate"],0.0)

 def test_wait_only_counts_served(self):
  # 容量0、高负载：观测期有拒收，等待指标仅来自办理样本且均为0（空系统FCFS）。
  out=simulate(0.8,0.3,1,300,60,10,11,queue_capacity=0)
  for r in out["replications"]:
   self.assertGreater(r["rejected"],0)
   if r["served"]:
    self.assertEqual(r["p_wait"],0.0)

 def test_timeout_only_path(self):
  out=simulate(0.5,0.2,2,400,60,10,5,None,8.0)
  self.assertIsNone(out["queue_capacity"]);self.assertTrue(out["finite_capacity"])
  for r in out["replications"]:
   self.assertEqual(r["rejected"],0)
   self.assertEqual(r["served"]+r["abandoned"],r["arrivals"])

if __name__=="__main__":
 unittest.main(verbosity=2)
