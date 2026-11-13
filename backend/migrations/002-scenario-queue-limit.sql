-- 有限候位与最长等候：两列均可空，NULL 表示无限候位 / 不限等候（历史口径）。
-- 旧方案两列为 NULL，调度仍走无限候位路径，结果可复现。
ALTER TABLE capacity_scenarios
 ADD COLUMN queue_capacity INT NULL,
 ADD COLUMN max_wait_minutes FLOAT NULL;
