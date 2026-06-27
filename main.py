import os
import json
import glob
import time
import threading
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.orchestrator import OrchestratorAgent

stats_lock = threading.Lock()
stats = {
    "total_files": 0,
    "json_success_count": 0,
    "validation_success_count": 0,
    "db_insert_success_count": 0,
    "failed_receipt_count": 0,
    "total_processing_time": 0.0,
    "quality_warnings_count": 0
}

def process_single_file(box_file, output_dir):
    filename = os.path.basename(box_file)
    json_filename = filename.replace('.txt', '.json').replace('.jpg', '.json').replace('.png', '.json')
    output_path = os.path.join(output_dir, json_filename)
    
    print(f"Starting orchestration for {filename}...")
    start_time = time.time()
    
    orchestrator = OrchestratorAgent()
    state = orchestrator.process_file(box_file, filename)
    elapsed_time = time.time() - start_time
    
    with stats_lock:
        stats["total_processing_time"] += elapsed_time
        if state.is_success:
            stats["json_success_count"] += 1
            stats["validation_success_count"] += 1
            stats["db_insert_success_count"] += 1
            if state.quality_report and not state.quality_report.get('is_clean'):
                stats["quality_warnings_count"] += 1
        else:
            stats["failed_receipt_count"] += 1
            
    if state.is_success and state.validated_data:
        output_dict = state.validated_data.model_dump()
        output_dict["processing_time_seconds"] = elapsed_time
        if state.quality_report:
            output_dict["quality_report"] = state.quality_report
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_dict, f, indent=4)


def process_dataset(dataset_path: str, output_dir: str, limit: int = None, use_images: bool = False):
    source_dir = os.path.join(dataset_path, "train", "img" if use_images else "box")
    if not os.path.exists(source_dir):
        print(f"Directory not found at {source_dir}")
        return
        
    ext = "*.jpg" if use_images else "*.txt"
    all_box_files = glob.glob(os.path.join(source_dir, ext))
    
    # Filter out already processed files to allow resuming
    box_files = []
    for bf in all_box_files:
        json_filename = os.path.basename(bf).replace('.txt', '.json').replace('.jpg', '.json').replace('.png', '.json')
        if not os.path.exists(os.path.join(output_dir, json_filename)):
            box_files.append(bf)
            
    if limit:
        box_files = box_files[:limit]
        
    stats["total_files"] = len(box_files)
    if not box_files:
        print("All files already processed! Nothing to do.")
        return
        
    print(f"Found {len(box_files)} remaining receipt files. Processing via Agent Orchestrator with 4 workers to prevent OOM...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_single_file, bf, output_dir) for bf in box_files]
        for future in as_completed(futures):
            pass 
            
    stats["average_processing_time"] = stats["total_processing_time"] / stats["total_files"] if stats["total_files"] > 0 else 0
    stats["validation_success_rate"] = stats["validation_success_count"] / stats["total_files"] if stats["total_files"] > 0 else 0
    stats["json_success_rate"] = stats["json_success_count"] / stats["total_files"] if stats["total_files"] > 0 else 0
    stats["db_insert_success_rate"] = stats["db_insert_success_count"] / stats["total_files"] if stats["total_files"] > 0 else 0
    
    with open(os.path.join(output_dir, "..", "run_stats.json"), "w") as f:
        json.dump(stats, f, indent=4)
        
    print("Agent batch processing complete. Stats saved to run_stats.json")

if __name__ == "__main__":
    load_dotenv()
    dataset_path = r"C:\Users\HP\Desktop\Portfolio\sroie-pipeline\SROIE2019"
    output_directory = os.path.join(os.path.dirname(__file__), "data", "output")
    process_dataset(dataset_path, output_directory, limit=None, use_images=True)
