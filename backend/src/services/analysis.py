from src.services.erlang import erlang_c
from src.services.simulation import simulate
def analyze(profile,scenario):
 arrival=profile.arrival_rate*scenario.arrival_multiplier;service=profile.service_rate*scenario.service_multiplier
 analytic=erlang_c(arrival,service,scenario.windows)
 simulation=simulate(arrival,service,scenario.windows,scenario.duration_minutes,scenario.warmup_minutes,scenario.replications,scenario.seed,scenario.queue_capacity,scenario.max_wait_minutes)
 finite=simulation["finite_capacity"]
 assumptions=["所有率均为每分钟；μ是每个窗口的服务率。理论要求泊松到达、独立指数服务、同质窗口、无限等候空间及稳态。","观测按时段估计均值；聚合高峰与平峰不保证泊松稳态。CV偏离1提示指数假设可能不符。","仿真从空系统开始，先warmup后统计观测期到达，服务可延续到观察结束之后。warmup只能缓解初态影响，不能保证已收敛；预热期间到达样本仍占用窗口与候位。","rho≥1没有有限稳态均值；有限期仿真仍会给出暂态等待，不能用于证明稳定。","95%区间量化固定模型下重复仿真误差，不含输入率估计误差。"]
 if finite:
  cap="无限" if scenario.queue_capacity is None else str(scenario.queue_capacity)
  mw="不限" if scenario.max_wait_minutes is None else f"{scenario.max_wait_minutes:g}分钟"
  assumptions.append(f"本方案配置候位容量{cap}个（仅计排队样本，不含在办样本）、最长等候{mw}：候位满时新到样本拒收，排队超过限时样本离队；同一时刻先释放窗口、再处理离队、最后接样。等待指标只统计成功办理样本，拒收与离队计入损失率。")
 else:
  assumptions.append("本方案为无限候位、不限等候时间：所有到达最终都会被办理，无拒收与离队，用于复现历史口径。")
 return {"analytic":analytic,"simulation":simulation,"comparison":[erlang_c(arrival,service,c) for c in sorted({2,3,4,scenario.windows})],"profile_statistics":profile.statistics,"assumptions":assumptions}
