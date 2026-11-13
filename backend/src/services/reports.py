import uuid,csv,io
from sqlalchemy import select
from fastapi import HTTPException
from src.models import Report,CapacityReview
from src.services.runs import require_completed
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload,user):
 require_completed(db,payload.run_id)
 review=db.scalar(select(CapacityReview).where(CapacityReview.run_id==payload.run_id).order_by(CapacityReview.created_at.desc()))
 if not review or review.decision!="accepted":raise HTTPException(409,"最新复核须为接受后才能归档")
 if db.scalar(select(Report).where(Report.run_id==payload.run_id)):raise HTTPException(409,"本次运行已归档")
 item=Report(id=str(uuid.uuid4()),published_by=user["email"],created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
def export(db,id):
 report=db.get(Report,id)
 if not report:raise HTTPException(404,"报告不存在")
 result=require_completed(db,report.run_id).result
 sim=result["simulation"]
 columns=["replication","arrivals","served","rejected","abandoned","loss_rate","mean_wait_minutes","p_wait","max_wait_minutes","busy_fraction"]
 buf=io.StringIO();writer=csv.writer(buf)
 cap="无限候位" if sim.get("queue_capacity") is None else f"候位容量{sim['queue_capacity']}"
 mw="不限等候" if sim.get("max_wait_minutes") is None else f"最长等候{sim['max_wait_minutes']:g}分钟"
 writer.writerow([f"# {cap} / {mw} / 观测{sim['duration_minutes']}分钟 / 预热{sim['warmup_minutes']}分钟 / seed {sim['seed']}"])
 # 汇总对账行：办理+拒收+离队=到达，损失率=(拒收+离队)/到达。
 d=sim["disposition"]
 writer.writerow(["# 汇总","到达","办理","拒收","离队","损失率","对账(办理+拒收+离队)"])
 writer.writerow(["# 合计",d["arrivals"],d["served"],d["rejected"],d["abandoned"],f"{d['loss_rate']:.6f}",d["served"]+d["rejected"]+d["abandoned"]])
 writer.writerow(columns)
 dict_writer=csv.DictWriter(buf,columns,extrasaction="ignore")
 for row in sim["replications"]:
  dict_writer.writerow(row)
 return "\ufeff"+buf.getvalue()
