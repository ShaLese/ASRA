"""
Workflow Runner Module
Handles the execution of research workflow by converting notebooks to scripts
and running them in a controlled environment.
"""

import sys
import os
import json
from pathlib import Path
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import traceback

logger = logging.getLogger(__name__)

class WorkflowRunner:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.script_dir = output_dir / 'scripts'
        self.script_dir.mkdir(exist_ok=True)
        
    def notebook_to_script(self, notebook_path: Path) -> Path:
        """Convert a Jupyter notebook to a Python script."""
        try:
            # Read notebook as JSON
            with open(notebook_path) as f:
                nb = json.load(f)
            
            # Create utils directory in scripts dir
            scripts_utils_dir = self.script_dir / 'utils'
            scripts_utils_dir.mkdir(exist_ok=True)
            
            # Create outputs directory
            outputs_dir = self.script_dir / 'data' / 'outputs'
            outputs_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy utils modules to script directory
            project_utils = Path(__file__).parent
            for module in ['__init__.py', 'config.py', 'helpers.py']:
                src = project_utils / module
                dst = scripts_utils_dir / module
                if src.exists():
                    with open(src, 'r') as f:
                        content = f.read()
                    with open(dst, 'w') as f:
                        f.write(content)
            
            # Extract code cells and fix indentation
            class_cells = []
            main_cells = []
            in_class = False
            
            for cell in nb.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        source = ''.join(source)
                    
                    # Check if this cell contains a class definition
                    if 'class ' in source:
                        in_class = True
                        class_cells.append(source)
                    else:
                        if in_class and not source.strip().startswith('def '):
                            in_class = False
                        if in_class:
                            class_cells.append(source)
                        else:
                            main_cells.append(source)
            
            # Create script content with proper imports and indentation
            imports = [
                "import sys",
                "import os",
                "import json",
                "import logging",
                "import traceback",
                "from pathlib import Path",
                "from datetime import datetime",
                "from typing import Dict, List, Optional",
                "import pandas as pd",
                "import numpy as np",
                "from tqdm import tqdm",
            ]
            
            setup = [
                "",
                "# Setup basic logging first",
                "logging.basicConfig(",
                "    level=logging.INFO,",
                "    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
                ")",
                "logger = logging.getLogger(__name__)",
                "",
                "try:",
                "    # Import local utils modules",
                "    from utils.config import setup_logging, OUTPUTS_DIR, RESEARCH_PAPERS_DIR, EXPERIMENTAL_DATA_DIR, MODEL_CONFIGS, DEEPSEEK_API_KEY",
                "    from utils.helpers import *",
                "    ",
                "    # Setup logging with module name",
                "    logger = setup_logging(__name__)",
                "except Exception as e:",
                "    logger.error(f'Failed to import modules: {e}\\n{traceback.format_exc()}')",
                "    sys.exit(1)",
                "",
            ]
            
            # Add class definitions
            class_code = '\n'.join(class_cells)
            
            # Add main function with proper indentation
            main_code = []
            main_code.append("def main():")
            main_code.append("    try:")
            
            # Indent the main code cells
            main_code.extend('        ' + line if line.strip() else line
                           for code in main_cells
                           for line in code.splitlines())
            
            # Add execution code based on notebook name
            if "orchestrator" in notebook_path.stem:
                main_code.extend([
                    "        # Run orchestrator",
                    "        orchestrator = ResearchOrchestrator()",
                    "        results = orchestrator.run_research_workflow()",
                    "        logger.info(f'Workflow results: {results}')"
                ])
            elif "literature_review" in notebook_path.stem:
                main_code.extend([
                    "        # Run literature review",
                    "        reviewer = LiteratureReviewer()",
                    "        results = reviewer.analyze_papers()",
                    "        logger.info(f'Literature review results: {results}')"
                ])
            elif "hypothesis_generator" in notebook_path.stem:
                main_code.extend([
                    "        # Run hypothesis generation",
                    "        generator = HypothesisGenerator()",
                    "        results = generator.generate_hypotheses()",
                    "        logger.info(f'Generated hypotheses: {results}')"
                ])
            elif "data_analyzer" in notebook_path.stem:
                main_code.extend([
                    "        # Run data analysis",
                    "        analyzer = DataAnalyzer()",
                    "        results = analyzer.analyze_dataset()",  
                    "        logger.info(f'Analysis results: {results}')"
                ])
            elif "visualizer" in notebook_path.stem:
                main_code.extend([
                    "        # Run visualization",
                    "        visualizer = ResearchVisualizer()",
                    "        results = visualizer.create_visualizations()",
                    "        logger.info(f'Visualization results: {results}')"
                ])
            
            footer = [
                "    except Exception as e:",
                "        logger.error(f'Error in {__file__}: {str(e)}\\n{traceback.format_exc()}')",
                "        sys.exit(1)",
                "",
                "if __name__ == '__main__':",
                "    main()"
            ]
            
            # Combine all parts
            script_content = '\n'.join(imports + setup + [class_code] + main_code + footer)
            
            # Save script
            script_path = self.script_dir / f"{notebook_path.stem}.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
                
            return script_path
            
        except Exception as e:
            logger.error(f"Error converting notebook {notebook_path}: {str(e)}")
            raise
    
    def run_script(self, script_path: Path, cwd: Optional[Path] = None) -> Dict:
        """Run a Python script and capture its output."""
        try:
            # Set working directory
            if cwd is None:
                cwd = script_path.parent
                
            # Prepare environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(script_path.parent.parent)
                
            # Run script with proper environment
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                env=env
            )
            
            # Process result
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return {
                'success': success,
                'output': output,
                'script': str(script_path)
            }
            
        except Exception as e:
            error_msg = f"Error running script {script_path}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'success': False,
                'output': error_msg,
                'script': str(script_path)
            }
    
    def run_workflow(self, notebook_paths: List[Path]) -> Dict:
        """Run the entire research workflow by converting and executing notebooks."""
        try:
            results = {}
            
            # Convert notebooks to scripts
            script_paths = []
            for nb_path in notebook_paths:
                try:
                    script_path = self.notebook_to_script(nb_path)
                    script_paths.append(script_path)
                except Exception as e:
                    error_msg = f"Conversion failed: {str(e)}\n{traceback.format_exc()}"
                    results[nb_path.stem] = {
                        'success': False,
                        'output': error_msg,
                        'script': None
                    }
            
            # Run scripts in parallel
            with ThreadPoolExecutor() as executor:
                future_to_script = {
                    executor.submit(self.run_script, script_path): script_path
                    for script_path in script_paths
                }
                
                for future in future_to_script:
                    script_path = future_to_script[future]
                    try:
                        result = future.result()
                        results[script_path.stem] = result
                    except Exception as e:
                        error_msg = f"Execution failed: {str(e)}\n{traceback.format_exc()}"
                        results[script_path.stem] = {
                            'success': False,
                            'output': error_msg,
                            'script': str(script_path)
                        }
            
            return results
            
        except Exception as e:
            error_msg = f"Error running workflow: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
