from sqlalchemy.orm import Session
from sqlalchemy import func
from entities.models import Score
from .schemas import ScoreCreate, ModuleScoreSummary
from typing import List, Dict
from uuid import UUID

def create_score(db: Session, score_data: ScoreCreate):
    score = Score(
        user_id=score_data.user_id,
        module_content_id=score_data.module_content_id,
        score_type=score_data.score_type,
        weight=score_data.weight,
        correctness=score_data.correctness,
        conceptual_depth=score_data.conceptual_depth,
        reasoning_quality=score_data.reasoning_quality,
        confidence_alignment=score_data.confidence_alignment,
        misconceptions=score_data.misconceptions,
        feedback=score_data.feedback
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score

def get_scores_by_user(db: Session, user_id: int):
    return db.query(Score).filter(Score.user_id == user_id).all()

def calculate_user_module_scores(db: Session, user_id: int) -> List[ModuleScoreSummary]:
    # Group by module_content_id
    query = db.query(
        Score.module_content_id, 
        Score.score_type,
        Score.weight,
        Score.correctness,
        Score.conceptual_depth, 
        Score.reasoning_quality,
        Score.confidence_alignment
    ).filter(Score.user_id == user_id, Score.module_content_id.isnot(None))
    
    scores = query.all()
    
    if not scores:
        return []
        
    module_groups = {}
    
    # Organize scores into groups
    for row in scores:
        mid = row.module_content_id
        if mid not in module_groups:
            module_groups[mid] = {"evaluation": [], "conversation": []}
            
        # Determing group
        # conversation_evaluation & question_depth -> conversation
        # evaluation_engine -> evaluation
        
        # Calculate single mean scalar for the entry
        entry_mean = (row.correctness + row.conceptual_depth + row.reasoning_quality + row.confidence_alignment) / 4.0
        
        # Store (score, weight) tuple
        if row.score_type == "evaluation_engine":
            module_groups[mid]["evaluation"].append((entry_mean, row.weight))
        elif row.score_type in ["conversation_evaluation", "question_depth"]:
            module_groups[mid]["conversation"].append((entry_mean, row.weight))
            
    summary_list = []
    
    # Calculate means and final scores
    for mid, groups in module_groups.items():
        eval_list = groups["evaluation"]
        conv_list = groups["conversation"]
        
        # Calculate Weighted Mean: Sum(score * weight) / Sum(weight)
        if eval_list:
            eval_total = sum(s * w for s, w in eval_list)
            eval_weight_sum = sum(w for _, w in eval_list)
            eval_mean = eval_total / eval_weight_sum if eval_weight_sum > 0 else 0.0
        else:
            eval_mean = 0.0
            
        if conv_list:
            conv_total = sum(s * w for s, w in conv_list)
            conv_weight_sum = sum(w for _, w in conv_list)
            conv_mean = conv_total / conv_weight_sum if conv_weight_sum > 0 else 0.0
        else:
            conv_mean = 0.0
        
        # Weightage:
        # Question Completion: 0.5 (Static Value & Weight logic combined as requested)
        # Evaluation: 0.35 * Mean
        # Conversation: 0.15 * Mean
        
        completion_static = 0.5 
        # Note: 'static 0.5 for question completion' interprets as the Value Contribution is 0.5
        # If the user meant "Weight is 0.5 and Value is calculated separately", then we'd need that logic.
        # But per request: "take the static 0.5 for question completion". 
        # So Final = 0.5 (Static) + (0.35 * eval_mean) + (0.15 * conv_mean)
        # Assuming eval_mean and conv_mean are 0.0-1.0.
        # If no entries, mean is 0.
        
        total_score = completion_static + (0.35 * eval_mean) + (0.15 * conv_mean)
        
        # Color Grading
        if total_score < 0.25:
            color_grade = "yellow"
        elif total_score < 0.50:
            color_grade = "blue"
        elif total_score < 0.75:
            color_grade = "orange"
        else:
            color_grade = "red"
        
        summary = ModuleScoreSummary(
            module_content_id=mid,
            total_score=total_score,
            color_grade=color_grade,
            question_completion_score=completion_static,
            evaluation_score=eval_mean,
            conversation_score=conv_mean,
            evaluation_count=len(eval_list),
            conversation_count=len(conv_list)
        )
        summary_list.append(summary)
        
    return summary_list
