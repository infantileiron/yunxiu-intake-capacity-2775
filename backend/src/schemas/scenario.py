from pydantic import BaseModel,Field
class ScenarioInput(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 profile_id:str
 windows:int=Field(ge=1,le=12)
 arrival_multiplier:float=Field(default=1,ge=.2,le=3,allow_inf_nan=False)
 service_multiplier:float=Field(default=1,ge=.2,le=3,allow_inf_nan=False)
 duration_minutes:int=Field(default=480,ge=60,le=1440)
 warmup_minutes:int=Field(default=120,ge=0,le=1440)
 replications:int=Field(default=30,ge=5,le=100)
 seed:int=Field(default=2206,ge=0,le=2147483647)
 # 候位容量仅计排队样本、不含在办样本；null表示无限候位（历史口径）。
 queue_capacity:int|None=Field(default=None,ge=0,le=10000)
 # 最长等候时间（分钟）；null表示不限等候时间。
 max_wait_minutes:float|None=Field(default=None,gt=0,le=100000,allow_inf_nan=False)
