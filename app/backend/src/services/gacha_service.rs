use crate::models::gacha::PlanDrawResult;

/// 连抽规划（匹配前端 algorithms.ts planMultiDraw）
pub fn plan_multi_draw(total_minutes: i64) -> Vec<PlanDrawResult> {
    if total_minutes < 15 {
        return vec![];
    }
    if total_minutes < 25 {
        let n = (total_minutes / 7).max(1);
        return vec![PlanDrawResult { pool: "fragment".into(), count: n }];
    }
    if total_minutes < 90 {
        let n = (total_minutes / 25).max(1).min(4);
        return vec![PlanDrawResult { pool: "tomato".into(), count: n }];
    }
    let deep = (total_minutes / 50).max(1).min(3);
    let remaining = total_minutes - deep * 50;
    let mut plans = vec![PlanDrawResult { pool: "deep".into(), count: deep }];
    if remaining >= 25 {
        plans.push(PlanDrawResult { pool: "tomato".into(), count: 1 });
    } else if remaining >= 7 {
        plans.push(PlanDrawResult { pool: "fragment".into(), count: 1 });
    }
    plans
}

/// 卡池时间范围
pub fn pool_time_range(pool: &str) -> (i64, i64) {
    match pool {
        "fragment" => (0, 15),
        "tomato" => (15, 45),
        "deep" => (45, 999),
        _ => (0, 999),
    }
}
