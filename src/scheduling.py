from typing import List, Dict, Any
from src.config import StudyPlan, StudyWeek, LearnerProfile

def largest_remainder_method(values: List[float], total_target: int, min_value: int = 1) -> List[int]:
    """
    Distributes total_target integer units across list elements proportionally to their float values.
    Ensures that each non-zero element gets at least `min_value` units, and the sum of units equals total_target.
    """
    if not values:
        return []
    
    total_val = sum(values)
    if total_val == 0:
        return [0] * len(values)
    
    # 1. First Pass: Give floor of proportional value
    allocations = []
    remainders = []
    for i, v in enumerate(values):
        if v == 0:
            allocations.append(0)
            remainders.append((0.0, i))
        else:
            exact = (v / total_val) * total_target
            floor_val = max(min_value, int(exact))
            allocations.append(floor_val)
            remainders.append((exact - floor_val, i))
            
    # 2. Check if we allocated too much (due to min_value floors)
    current_sum = sum(allocations)
    if current_sum > total_target:
        # We need to subtract units from elements that exceeded their exact targets the most
        diff = current_sum - total_target
        # Sort by actual allocations vs exact quotas (most over-allocated first)
        over_allocated = []
        for i, v in enumerate(values):
            if allocations[i] > min_value:
                exact = (v / total_val) * total_target
                over_allocated.append((allocations[i] - exact, i))
        over_allocated.sort(reverse=True, key=lambda x: x[0])
        for _, idx in over_allocated[:diff]:
            allocations[idx] -= 1
            
    # 3. Check if we allocated too little
    elif current_sum < total_target:
        diff = total_target - current_sum
        # Sort by remainders descending
        remainders.sort(reverse=True, key=lambda x: x[0])
        for _, idx in remainders[:diff]:
            allocations[idx] += 1
            
    return allocations

def generate_workload_aware_schedule(
    profile: LearnerProfile,
    cert_data: Dict[str, Any],
    weeks: int = 4
) -> StudyPlan:
    """
    Generates a personalized study plan by:
    1. Distributing study hours across weeks according to simulated weekly Work IQ meeting/focus loads.
    2. Distributing hours within each week across exam domains using the Largest Remainder Method.
    """
    # 1. Parse certification domains and weights
    domains = cert_data.get("domains", [])
    domain_names = [d["name"] for d in domains]
    domain_weights = [d["weight"] for d in domains]
    recommended_hours = cert_data.get("recommended_hours", 20)
    
    # Determine base weekly budget
    weekly_budget = profile.weekly_study_budget_hours
    total_requested_hours = weekly_budget * weeks
    
    # Ensure total study hours meets recommended minimum or at least requested
    total_hours = max(recommended_hours, total_requested_hours)
    
    # 2. Simulate weekly workload variations (Work IQ signals)
    # We create a schedule where meeting load varies week-to-week
    # Week 1: Standard load
    # Week 2: High meeting load (triggers reduction)
    # Week 3: Low meeting load (catch up)
    # Week 4: Standard load
    weekly_meetings = [
        profile.meeting_hours_per_week,
        profile.meeting_hours_per_week + 8,  # Busy week
        max(5, profile.meeting_hours_per_week - 8),  # Light week
        profile.meeting_hours_per_week
    ]
    
    # If weeks is different from 4, pad or trim
    if len(weekly_meetings) < weeks:
        weekly_meetings += [profile.meeting_hours_per_week] * (weeks - len(weekly_meetings))
    else:
        weekly_meetings = weekly_meetings[:weeks]
        
    # Calculate weekly focus weights (higher focus hours = more capacity)
    weekly_focus_capacity = []
    weekly_adjustments = []
    
    for w in range(weeks):
        meetings = weekly_meetings[w]
        if meetings > 22:
            # Overloaded week (Work IQ threshold)
            capacity = 0.5  # 50% capacity reduction
            weekly_adjustments.append((capacity, "Meeting overload (>22h meetings). Study budget reduced to prevent burnout."))
        elif meetings < 12:
            # Light week
            capacity = 1.3  # Extra capacity
            weekly_adjustments.append((capacity, "High availability. Study budget boosted to accelerate progress."))
        else:
            capacity = 1.0
            weekly_adjustments.append((capacity, "Standard workload. Default study hours maintained."))
        weekly_focus_capacity.append(capacity)
        
    # Allocate total study hours across weeks using focus capacity weights
    weekly_hour_allocations = largest_remainder_method(weekly_focus_capacity, total_hours, min_value=1)
    
    # 3. Create StudyWeek objects
    schedule = []
    for w in range(weeks):
        week_num = w + 1
        week_hours = weekly_hour_allocations[w]
        capacity, reason = weekly_adjustments[w]
        is_adjusted = capacity != 1.0
        
        # Distribute week_hours across domains using domain weights
        week_domain_allocations = largest_remainder_method(domain_weights, week_hours, min_value=0)
        
        # Filter active domains for this week
        week_domains = []
        for d_idx, d_hours in enumerate(week_domain_allocations):
            if d_hours > 0:
                week_domains.append(f"{domain_names[d_idx]} ({d_hours}h)")
                
        schedule.append(
            StudyWeek(
                week_number=week_num,
                focus_domains=week_domains,
                hours_allocated=week_hours,
                workload_adjusted=is_adjusted,
                adjustment_reason=reason
            )
        )
        
    return StudyPlan(
        learner_id=profile.learner_id,
        certification_target=profile.certification_target,
        total_weeks=weeks,
        total_hours=total_hours,
        schedule=schedule
    )
