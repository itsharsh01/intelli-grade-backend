#!/usr/bin/env python3
"""
Seed the question bank with sample questions for the Singly Linked List module.
Run from the project root (intelli-grade-backend) with:
  .venv/bin/python scripts/seed_questions.py
Requires PostgreSQL (DATABASE_URL) and the quiz tables to be migrated.
"""
import os
import sys
import uuid

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entities.database import SessionLocal
from entities.models import Question

# Module UUID for "Singly Linked List" (must match frontend course outline)
SINGLY_LINKED_LIST_MODULE_ID = uuid.UUID("c7a49b63-b52d-45c7-9af8-fbfb92a3da29")

QUESTIONS = [
    # MCQ
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "MCQ",
        "difficulty": "easy",
        "question_text": "What is the head of a singly linked list?",
        "options": ["The first node", "The last node", "The middle node", "A null reference"],
        "correct_answer": "The first node",
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "terminology"],
        "weight": 1.0,
    },
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "MCQ",
        "difficulty": "easy",
        "question_text": "In a singly linked list, each node contains:",
        "options": ["Only a value", "A value and a pointer to the next node", "A value and pointers to next and previous", "Only a pointer"],
        "correct_answer": "A value and a pointer to the next node",
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "node structure"],
        "weight": 1.0,
    },
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "MCQ",
        "difficulty": "medium",
        "question_text": "What is the time complexity of finding an element in an unsorted singly linked list of n nodes?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
        "correct_answer": "O(n)",
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "complexity"],
        "weight": 1.0,
    },
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "MCQ",
        "difficulty": "medium",
        "question_text": "Adding a node at the tail of a singly linked list (when you have a tail pointer) is:",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
        "correct_answer": "O(1)",
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "insertion", "complexity"],
        "weight": 1.0,
    },
    # DOUBLE_MCQ
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "DOUBLE_MCQ",
        "difficulty": "medium",
        "question_text": "Which operations on a singly linked list with only a head pointer require traversing the list? (Select all that apply.)",
        "options": ["Insert at head", "Insert at tail", "Delete from head", "Search for a value"],
        "correct_answer": ["Insert at tail", "Search for a value"],
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "traversal"],
        "weight": 1.0,
    },
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "DOUBLE_MCQ",
        "difficulty": "easy",
        "question_text": "Which of the following are true about a singly linked list? (Select all that apply.)",
        "options": ["Nodes are stored in contiguous memory", "Each node points to at most one other node", "Traversal is possible in both directions", "The last node's next pointer is typically null"],
        "correct_answer": ["Each node points to at most one other node", "The last node's next pointer is typically null"],
        "evaluation_rubric": None,
        "concept_tags": ["linked list", "basics"],
        "weight": 1.0,
    },
    # SUBJECTIVE
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "SUBJECTIVE",
        "difficulty": "medium",
        "question_text": "In one or two sentences, explain why deleting a node from the middle of a singly linked list requires a reference to the previous node.",
        "options": None,
        "correct_answer": None,
        "evaluation_rubric": {
            "criteria": [
                "Mentions that we need to update the previous node's next pointer",
                "Mentions that we cannot go backwards from the node to delete",
            ],
            "max_score": 1.0,
        },
        "concept_tags": ["linked list", "deletion"],
        "weight": 1.0,
    },
    {
        "module_id": SINGLY_LINKED_LIST_MODULE_ID,
        "question_type": "SUBJECTIVE",
        "difficulty": "easy",
        "question_text": "What is the main disadvantage of a singly linked list compared to an array for random access by index?",
        "options": None,
        "correct_answer": None,
        "evaluation_rubric": {
            "criteria": [
                "Must access elements sequentially / cannot jump to index directly",
                "O(n) to reach the nth element",
            ],
            "max_score": 1.0,
        },
        "concept_tags": ["linked list", "arrays", "random access"],
        "weight": 1.0,
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Question).filter(Question.module_id == SINGLY_LINKED_LIST_MODULE_ID).count()
        if existing > 0:
            print(f"Found {existing} existing questions for Singly Linked List. Skipping seed (run with --force to add more).")
            if "--force" not in sys.argv:
                return
        added = 0
        for q in QUESTIONS:
            row = Question(
                module_id=q["module_id"],
                question_type=q["question_type"],
                difficulty=q["difficulty"],
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                evaluation_rubric=q["evaluation_rubric"],
                concept_tags=q["concept_tags"],
                weight=q["weight"],
            )
            db.add(row)
            added += 1
        db.commit()
        print(f"Seeded {added} questions for module Singly Linked List ({SINGLY_LINKED_LIST_MODULE_ID}).")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
