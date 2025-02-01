import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import json
import pandas as pd
from PIL import Image
from utils.config import OUTPUTS_DIR, RESEARCH_PAPERS_DIR, EXPERIMENTAL_DATA_DIR
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import logging

# Setup page config
st.set_page_config(
    page_title="ASRA - Autonomous Scientific Research Agent",
    page_icon="🧬",
    layout="wide"
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results():
    """Load the latest results from each component."""
    results = {}
    
    try:
        # Load literature analysis
        lit_path = OUTPUTS_DIR / 'literature_analysis.json'
        if lit_path.exists():
            with open(lit_path) as f:
                results['literature'] = json.load(f)
        
        # Load hypotheses
        hyp_path = OUTPUTS_DIR / 'generated_hypotheses.json'
        if hyp_path.exists():
            with open(hyp_path) as f:
                results['hypotheses'] = json.load(f)
        
        # Load experimental analysis
        exp_path = OUTPUTS_DIR / 'experimental_analysis.json'
        if exp_path.exists():
            with open(exp_path) as f:
                results['experiments'] = json.load(f)
        
        # Load visualizations metadata
        vis_path = OUTPUTS_DIR / 'visualizations' / 'visualization_metadata.json'
        if vis_path.exists():
            with open(vis_path) as f:
                results['visualizations'] = json.load(f)
                
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}")
    
    return results

def run_research_workflow():
    """Execute the research workflow."""
    try:
        # Load orchestrator notebook
        notebook_path = Path(__file__).parent / 'agents' / 'orchestrator.ipynb'
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Execute notebook
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
        
        return True
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        return False

def main():
    st.title("🧬 Autonomous Scientific Research Agent (ASRA)")
    
    # Sidebar
    st.sidebar.title("Controls")
    
    if st.sidebar.button("Run Research Workflow"):
        with st.spinner("Running research workflow..."):
            success = run_research_workflow()
            if success:
                st.success("Research workflow completed!")
            else:
                st.error("Error running research workflow")
    
    # Load results
    results = load_results()
    
    # Main content
    tabs = st.tabs([
        "📚 Literature Review",
        "🤔 Hypotheses",
        "📊 Data Analysis",
        "🎨 Visualizations"
    ])
    
    # Literature Review Tab
    with tabs[0]:
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
            st.info("No literature analysis results available")
    
    # Hypotheses Tab
    with tabs[1]:
        st.header("Generated Hypotheses")
        if 'hypotheses' in results:
            for paper, data in results['hypotheses'].items():
                st.subheader(f"Based on: {paper}")
                st.write(data['generated_hypothesis'])
                st.divider()
        else:
            st.info("No generated hypotheses available")
    
    # Data Analysis Tab
    with tabs[2]:
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
            st.info("No experimental analysis results available")
    
    # Visualizations Tab
    with tabs[3]:
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
                        st.error(f"Error loading image: {str(e)}")
        else:
            st.info("No visualizations available")

if __name__ == "__main__":
    main()
