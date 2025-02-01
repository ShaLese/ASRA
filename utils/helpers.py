import json
from pathlib import Path
from typing import Dict, List, Any, Union
import pandas as pd
from datetime import datetime

def save_json(data: Union[Dict, List], filepath: Union[str, Path], indent: int = 2) -> None:
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

def load_json(filepath: Union[str, Path]) -> Union[Dict, List]:
    """Load data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_experiment_results(
    experiment_name: str,
    results: Dict[str, Any],
    output_dir: Union[str, Path]
) -> Path:
    """Save experimental results with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{experiment_name}_{timestamp}.json"
    output_path = Path(output_dir) / filename
    save_json(results, output_path)
    return output_path

def load_research_papers(papers_dir: Union[str, Path]) -> List[Dict[str, str]]:
    """Load research papers from directory."""
    papers = []
    papers_dir = Path(papers_dir)
    
    for paper_path in papers_dir.glob("*.txt"):
        with open(paper_path, 'r', encoding='utf-8') as f:
            content = f.read()
            papers.append({
                "title": paper_path.stem,
                "content": content,
                "path": str(paper_path)
            })
    
    return papers

def save_dataframe(
    df: pd.DataFrame,
    filename: str,
    output_dir: Union[str, Path],
    format: str = "csv"
) -> Path:
    """Save DataFrame to file."""
    output_dir = Path(output_dir)
    output_path = output_dir / f"{filename}.{format}"
    
    if format == "csv":
        df.to_csv(output_path, index=False)
    elif format == "excel":
        df.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return output_path
