import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import json
import pandas as pd
from PIL import Image
from utils.config import OUTPUTS_DIR, RESEARCH_PAPERS_DIR, EXPERIMENTAL_DATA_DIR
from utils.workflow_runner import WorkflowRunner
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Union, Tuple
from datetime import datetime
from functools import lru_cache
import hashlib
import traceback

# Setup page config
st.set_page_config(
    page_title="ASRA - Autonomous Scientific Research Agent",
    page_icon="🧬",
    layout="wide"
)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_DIR / 'streamlit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_file_hash(file_content: bytes) -> str:
    """Generate hash for file content to check duplicates."""
    return hashlib.md5(file_content).hexdigest()

def save_uploaded_file(uploaded_file, save_dir: Path) -> Tuple[Path, bool]:
    """Save uploaded file to specified directory with duplicate checking."""
    try:
        content = uploaded_file.getbuffer()
        file_hash = get_file_hash(content)
        
        # Check for duplicates
        existing_files = save_dir.glob("*")
        for existing_file in existing_files:
            if existing_file.is_file() and existing_file.name != ".gitkeep":
                with open(existing_file, "rb") as f:
                    if get_file_hash(f.read()) == file_hash:
                        logger.warning(f"Duplicate file detected: {uploaded_file.name}")
                        return existing_file, False
        
        save_path = save_dir / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(content)
        logger.info(f"Successfully saved file: {save_path}")
        return save_path, True
    except Exception as e:
        logger.error(f"Error saving file {uploaded_file.name}: {str(e)}")
        raise

def process_uploaded_files(files: List, save_dir: Path) -> List[Dict]:
    """Process multiple uploaded files in parallel."""
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(save_uploaded_file, file, save_dir): file 
            for file in files
        }
        
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                save_path, is_new = future.result()
                results.append({
                    'file': file.name,
                    'path': save_path,
                    'is_new': is_new,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'file': file.name,
                    'error': str(e),
                    'success': False
                })
    
    return results

def handle_file_upload():
    """Handle file upload section with parallel processing."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Upload Research Papers")
        uploaded_papers = st.file_uploader(
            "Upload research papers (TXT, PDF)",
            accept_multiple_files=True,
            type=["txt", "pdf"],
            key="paper_uploader"
        )
        
        if uploaded_papers:
            with st.spinner("Processing papers..."):
                results = process_uploaded_files(uploaded_papers, RESEARCH_PAPERS_DIR)
                
                # Use list comprehension for efficient processing
                successes = [r for r in results if r['success']]
                failures = [r for r in results if not r['success']]
                duplicates = [r for r in successes if not r['is_new']]
                
                if successes:
                    st.success(f"Successfully processed {len(successes)} papers" + 
                             (f" ({len(duplicates)} duplicates)" if duplicates else ""))
                if failures:
                    st.error(f"Failed to process {len(failures)} papers")
    
    with col2:
        st.subheader("📊 Upload Experimental Data")
        uploaded_data = st.file_uploader(
            "Upload experimental data (CSV, Excel)",
            accept_multiple_files=True,
            type=["csv", "xlsx"],
            key="data_uploader"
        )
        
        if uploaded_data:
            with st.spinner("Processing data files..."):
                results = process_uploaded_files(uploaded_data, EXPERIMENTAL_DATA_DIR)
                
                # Use list comprehension for efficient processing
                successes = [r for r in results if r['success']]
                failures = [r for r in results if not r['success']]
                duplicates = [r for r in successes if not r['is_new']]
                
                if successes:
                    st.success(f"Successfully processed {len(successes)} data files" +
                             (f" ({len(duplicates)} duplicates)" if duplicates else ""))
                if failures:
                    st.error(f"Failed to process {len(failures)} data files")

@lru_cache(maxsize=32)
def get_file_info(file_path: str) -> Dict:
    """Get cached file information."""
    path = Path(file_path)
    return {
        'name': path.name,
        'size': path.stat().st_size,
        'modified': datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def view_uploaded_files():
    """Display currently uploaded files with caching."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📑 Uploaded Papers")
        papers = [f for f in RESEARCH_PAPERS_DIR.glob("*") if f.name != ".gitkeep"]
        if papers:
            for paper in papers:
                col1_1, col1_2, col1_3 = st.columns([0.6, 0.2, 0.2])
                file_info = get_file_info(str(paper))
                with col1_1:
                    st.text(file_info['name'])
                with col1_2:
                    st.text(f"{file_info['size'] / 1024:.1f} KB")
                with col1_3:
                    if st.button("Delete", key=f"del_paper_{paper.name}"):
                        try:
                            os.remove(paper)
                            get_file_info.cache_clear()  # Clear cache after deletion
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error deleting {paper.name}: {str(e)}")
                            st.error(f"Error deleting file")
        else:
            st.info("No papers uploaded yet")
    
    with col2:
        st.subheader("📈 Uploaded Data")
        data_files = [f for f in EXPERIMENTAL_DATA_DIR.glob("*") if f.name != ".gitkeep"]
        if data_files:
            for data_file in data_files:
                col2_1, col2_2, col2_3 = st.columns([0.6, 0.2, 0.2])
                file_info = get_file_info(str(data_file))
                with col2_1:
                    st.text(file_info['name'])
                with col2_2:
                    st.text(f"{file_info['size'] / 1024:.1f} KB")
                with col2_3:
                    if st.button("Delete", key=f"del_data_{data_file.name}"):
                        try:
                            os.remove(data_file)
                            get_file_info.cache_clear()  # Clear cache after deletion
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error deleting {data_file.name}: {str(e)}")
                            st.error(f"Error deleting file")
        else:
            st.info("No data files uploaded yet")

@lru_cache(maxsize=1)
def load_results() -> Dict:
    """Load and cache the latest results from each component."""
    results = {}
    
    try:
        # Use list comprehension for efficient file loading
        result_files = [
            ('literature', OUTPUTS_DIR / 'literature_analysis.json'),
            ('hypotheses', OUTPUTS_DIR / 'generated_hypotheses.json'),
            ('experiments', OUTPUTS_DIR / 'experimental_analysis.json'),
            ('visualizations', OUTPUTS_DIR / 'visualizations' / 'visualization_metadata.json')
        ]
        
        results = {
            key: json.loads(path.read_text()) 
            for key, path in result_files 
            if path.exists()
        }
                
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}")
    
    return results

def run_research_workflow() -> bool:
    """Execute the research workflow with proper logging."""
    logger.info("Starting research workflow")
    try:
        # Initialize workflow runner with absolute paths
        base_dir = Path(__file__).resolve().parent
        outputs_dir = base_dir / 'data' / 'outputs'
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        runner = WorkflowRunner(outputs_dir)
        
        # Get all notebook paths using absolute paths
        agents_dir = base_dir / 'agents'
        notebook_paths = [
            agents_dir / 'orchestrator.ipynb',
            agents_dir / 'literature_review.ipynb',
            agents_dir / 'hypothesis_generator.ipynb',
            agents_dir / 'data_analyzer.ipynb',
            agents_dir / 'visualizer.ipynb'
        ]
        
        # Ensure all paths exist
        missing_notebooks = [p for p in notebook_paths if not p.exists()]
        if missing_notebooks:
            logger.error(f"Missing notebooks: {missing_notebooks}")
            return False
        
        # Run workflow
        results = runner.run_workflow(notebook_paths)
        
        # Check for errors
        if isinstance(results, dict) and 'error' in results:
            logger.error(f"Workflow failed:\n{results['error']}\n{results.get('traceback', '')}")
            return False
            
        # Log results
        for name, result in results.items():
            if isinstance(result, dict):
                if result.get('success'):
                    logger.info(f"{name} completed successfully")
                else:
                    logger.error(f"{name} failed: {result.get('output', 'Unknown error')}")
        
        # Clear results cache
        load_results.cache_clear()
        
        # Return True if orchestrator succeeded
        return results.get('orchestrator', {}).get('success', False)
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}\n{traceback.format_exc()}")
        return False

def clear_all_data() -> Tuple[bool, str]:
    """Clear all data with proper error handling."""
    try:
        # Use list comprehension for efficient file deletion
        dirs_to_clear = [RESEARCH_PAPERS_DIR, EXPERIMENTAL_DATA_DIR, OUTPUTS_DIR]
        
        for directory in dirs_to_clear:
            [os.remove(f) for f in directory.glob("*") if f.is_file() and f.name != ".gitkeep"]
            [shutil.rmtree(f) for f in directory.glob("*") if f.is_dir()]
        
        # Clear caches
        get_file_info.cache_clear()
        load_results.cache_clear()
        
        logger.info("All data cleared successfully")
        return True, "All data cleared successfully!"
    except Exception as e:
        error_msg = f"Error clearing data: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def main():
    st.title("🧬 Autonomous Scientific Research Agent (ASRA)")
    
    # Sidebar
    st.sidebar.title("Controls")
    
    # Add clear data button
    if st.sidebar.button("Clear All Data"):
        success, message = clear_all_data()
        if success:
            st.sidebar.success(message)
            st.rerun()
        else:
            st.sidebar.error(message)
    
    # Run workflow button
    if st.sidebar.button("Run Research Workflow"):
        if not any(RESEARCH_PAPERS_DIR.glob("*")) and not any(EXPERIMENTAL_DATA_DIR.glob("*")):
            st.sidebar.warning("Please upload some papers or data first!")
        else:
            with st.spinner("Running research workflow..."):
                success = run_research_workflow()
                if success:
                    st.success("Research workflow completed!")
                else:
                    st.error("Error running research workflow")
    
    # Main content
    tabs = st.tabs([
        "📤 Upload Files",
        "📚 Literature Review",
        "🤔 Hypotheses",
        "📊 Data Analysis",
        "🎨 Visualizations"
    ])
    
    # Upload Files Tab
    with tabs[0]:
        st.header("Upload Research Materials")
        handle_file_upload()
        st.divider()
        view_uploaded_files()
    
    # Load results for other tabs
    results = load_results()
    
    # Literature Review Tab
    with tabs[1]:
        st.header("Literature Review")
        if 'literature' in results:
            for paper, analysis in results['literature'].items():
                st.subheader(paper)
                for i, (insight, score) in enumerate(zip(
                    analysis['key_insights'],
                    analysis['importance_scores']
                ), 1):
                    st.write(f"{i}. {insight}")
                    st.progress(score)
        else:
            st.info("No literature analysis results available. Upload papers and run the workflow to see results.")
    
    # Hypotheses Tab
    with tabs[2]:
        st.header("Generated Hypotheses")
        if 'hypotheses' in results:
            for paper, data in results['hypotheses'].items():
                st.subheader(f"Based on: {paper}")
                st.write(data['generated_hypothesis'])
                st.divider()
        else:
            st.info("No generated hypotheses available. Run the workflow to generate hypotheses.")
    
    # Data Analysis Tab
    with tabs[3]:
        st.header("Experimental Analysis")
        if 'experiments' in results:
            for dataset, analysis in results['experiments'].items():
                st.subheader(dataset)
                
                # Feature importance plot
                importance_df = pd.DataFrame({
                    'Feature': [f"Feature {i}" for i in range(len(analysis['feature_importance']))],
                    'Importance': analysis['feature_importance']
                })
                st.bar_chart(importance_df.set_index('Feature'))
                
                # Predictions vs Actual
                if 'predictions' in analysis and 'actual_values' in analysis:
                    comparison_df = pd.DataFrame({
                        'Predicted': analysis['predictions'],
                        'Actual': analysis['actual_values']
                    })
                    st.line_chart(comparison_df)
        else:
            st.info("No experimental analysis results available. Upload data files and run the workflow to see results.")
    
    # Visualizations Tab
    with tabs[4]:
        st.header("Generated Visualizations")
        if 'visualizations' in results:
            cols = st.columns(2)
            for i, (name, path) in enumerate(results['visualizations'].items()):
                with cols[i % 2]:
                    st.subheader(name)
                    try:
                        image = Image.open(path)
                        st.image(image, use_column_width=True)
                    except Exception as e:
                        logger.error(f"Error loading image {path}: {str(e)}")
                        st.error(f"Error loading image")
        else:
            st.info("No visualizations available. Run the workflow to generate visualizations.")

if __name__ == "__main__":
    main()
