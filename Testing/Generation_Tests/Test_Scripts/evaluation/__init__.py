"""Evaluation harness for the v2 AAS generation pipeline.

Measures how accurately each LLM × ablation × equipment configuration produces
an AAS that matches a hand-authored ground-truth manifest. Results are written
to JSONL under `evaluation/results/` and plotted by `plot_results.py`.

Run a single experiment:

    python -m evaluation.run_eval \\
        --equipment ca18clc12bpm1 \\
        --provider claude --model claude-opus-4-5-20251101 \\
        --ablation full \\
        --output evaluation/results/run_2026-04-25.jsonl

Run the full matrix:

    python -m evaluation.run_eval --matrix evaluation/matrix.yaml \\
        --output evaluation/results/run_2026-04-25.jsonl
"""
