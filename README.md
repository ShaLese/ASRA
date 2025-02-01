# Autonomous Scientific Research Agent (ASRA)

An AI-driven system that automates the scientific research process, from hypothesis generation to paper writing, by integrating diverse AI models.

## Components

- **DeepSeek-R1**: Core reasoning, hypothesis generation, and literature synthesis
- **BERT/SPECTER**: Semantic analysis of research papers
- **TabNet**: Structured data analysis
- **Stable Diffusion**: Visualization generation
- **Orchestrator Agent**: Workflow management

## Project Structure

```
ASRA/
├── agents/                    # Agent notebooks
├── data/                     # Data storage
│   ├── research_papers/      # Research paper storage
│   ├── experimental_data/    # Experimental data
│   └── outputs/              # Generated outputs
├── utils/                    # Utility functions
├── requirements.txt          # Dependencies
└── streamlit_app.py         # Frontend interface
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
HUGGINGFACE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

## Usage

1. Place research papers in `data/research_papers/`
2. Run individual agent notebooks in the `agents/` directory
3. Launch the Streamlit interface:
```bash
streamlit run streamlit_app.py
```

## Workflow

1. **Literature Review**: BERT/SPECTER extracts key insights from papers
2. **Hypothesis Generation**: DeepSeek-R1 proposes novel hypotheses
3. **Experimental Design**: DeepSeek-R1 outlines experiments
4. **Data Analysis**: TabNet processes experimental data
5. **Visualization**: Stable Diffusion generates visualizations
6. **Paper Writing**: DeepSeek-R1 drafts the manuscript

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
