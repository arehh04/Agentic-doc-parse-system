import os
from evaluation.evaluator import EvaluationEngine

class EvaluationAgent:
    """
    Agent responsible for running batch performance benchmarks against the ground truth.
    """
    def __init__(self, ground_truth_dir: str):
        self.ground_truth_dir = ground_truth_dir
        
    def evaluate(self, predictions_dir: str, output_report_path: str) -> dict:
        """
        Executes the evaluation engine on a directory of predicted JSONs and saves the report.
        """
        engine = EvaluationEngine(self.ground_truth_dir)
        report = engine.run_evaluation(predictions_dir, output_report_path)
        return report
