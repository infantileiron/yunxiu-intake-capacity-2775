import heapq,math

# 事件类型：服务完成（窗口释放）、候位超时离队、样本到达。
# 同一时刻按“先释放窗口、再处理离队、最后接样”的顺序消费，
# 因此类型序号同时充当并列时刻的次级排序键。
_COMPLETION=0
_TIMEOUT=1
_ARRIVAL=2

# 样本最终去向：已办理 / 候位满拒收 / 超时离队。
SERVED="served"
REJECTED="rejected"
ABANDONED="abandoned"


def schedule(arrivals,services,windows,queue_capacity=None,max_wait=None):
 """离散事件调度。

 queue_capacity=None 且 max_wait=None 时为无限候位、不会离队，
 事件序列与字段与历史实现完全一致（旧方案可复现）。

 queue_capacity：候位容量，只统计排队等候的样本，不含正在办理的样本；
   候位满时新到达样本被拒收。None 表示无限候位。
 max_wait：最长等候时间（分钟）；排队样本等待超过该值即离队。
   None 表示不限等候时间。
 """
 if len(arrivals)!=len(services) or windows<1: raise ValueError("到达与服务长度须一致，窗口数须为正")
 if any(not math.isfinite(x) or x<0 for x in arrivals) or any(not math.isfinite(x) or x<=0 for x in services): raise ValueError("到达须有限非负、服务须有限正数")
 if any(a>b for a,b in zip(arrivals,arrivals[1:])): raise ValueError("到达时间须递增")
 if queue_capacity is not None and (not isinstance(queue_capacity,int) or queue_capacity<0): raise ValueError("候位容量须为非负整数或为空")
 if max_wait is not None and (not math.isfinite(max_wait) or max_wait<=0): raise ValueError("最长等候时间须为有限正数或为空")

 finite=queue_capacity is not None or max_wait is not None
 if not finite:
  return _schedule_infinite(arrivals,services,windows)

 events=[]
 # 未来事件堆：(时刻, 类型, 类型内序号, 载荷)。
 # 同刻由类型序号保证恒为“完成→离队→到达”，与入堆先后无关。
 clock=[]
 # 空闲窗口编号堆；窗口在办期间不留在堆中，故候位长度天然不含在办样本。
 free_servers=list(range(1,windows+1));heapq.heapify(free_servers)
 # 候位队列：已接样但尚未开始办理的样本，按到达先后（样本序号）排列。
 waiting=[]
 # 每个候位样本当前有效的超时序号；开始办理或离队后清除，旧事件据此惰性失效。
 active_timeout={}
 completion_seq=timeout_seq=0

 def arm_timeout(job,arrival):
  nonlocal timeout_seq
  if max_wait is None:return
  timeout_seq+=1;active_timeout[job]=timeout_seq
  heapq.heappush(clock,(arrival+max_wait,_TIMEOUT,timeout_seq,job))

 def cancel_timeout(job):
  active_timeout.pop(job,None)

 def start_service(now,job,arrival,service):
  nonlocal completion_seq
  cancel_timeout(job)
  server=heapq.heappop(free_servers)
  start=max(arrival,now);end=start+service
  events.append({"job":job+1,"arrival":arrival,"service":service,"start":start,"end":end,
                 "wait":start-arrival,"server":server,"outcome":SERVED})
  completion_seq+=1
  heapq.heappush(clock,(end,_COMPLETION,completion_seq,server))

 def record_loss(job,arrival,outcome):
  events.append({"job":job+1,"arrival":arrival,"service":services[job],"start":None,"end":None,
                 "wait":None,"server":None,"outcome":outcome})

 # 全部到达事件预先入堆，序号即样本序号；并列时刻由类型序号保证“完成→离队→到达”。
 for job,arrival in enumerate(arrivals):
  heapq.heappush(clock,(arrival,_ARRIVAL,job,job))
 while clock:
  now,kind,seq,payload=heapq.heappop(clock)
  if kind==_COMPLETION:
   # 窗口释放：先腾出窗口，再尝试接走队首样本。
   heapq.heappush(free_servers,payload)
   if waiting and free_servers:
    job=waiting.pop(0)
    start_service(now,job,arrivals[job],services[job])
  elif kind==_TIMEOUT:
   job=payload
   # 句柄失效（样本已开始办理或已被更新）则忽略。
   if active_timeout.get(job)!=seq:continue
   cancel_timeout(job)
   if job in waiting:
    waiting.remove(job)
    record_loss(job,arrivals[job],ABANDONED)
  else:
   # 到达：同刻已先完成窗口释放与离队处理，再决定接样或拒收。
   job=payload
   if free_servers:
    # 有空闲窗口，直接办理，不占候位。
    start_service(now,job,arrivals[job],services[job])
   elif queue_capacity is None or len(waiting)<queue_capacity:
    # 候位未满（或无限候位），接样入队并启动等候计时。
    waiting.append(job);arm_timeout(job,arrivals[job])
   else:
    # 候位满（不含在办样本），拒绝接样。
    record_loss(job,arrivals[job],REJECTED)
 return events


def _schedule_infinite(arrivals,services,windows):
 """无限候位调度：保留历史最小堆实现与字段，保证旧方案逐位复现。"""
 servers=[(0.0,i+1) for i in range(windows)];heapq.heapify(servers);events=[]
 for i,(arrival,service) in enumerate(zip(arrivals,services)):
  free,server=heapq.heappop(servers);start=max(arrival,free);end=start+service
  events.append({"job":i+1,"arrival":arrival,"service":service,"start":start,"end":end,"wait":start-arrival,"server":server,"outcome":SERVED})
  heapq.heappush(servers,(end,server))
 return events
