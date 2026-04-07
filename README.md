# Chinese-Dialogue-Scraper

## Project Overview
This repository contains a high-performance data processing pipeline designed to construct a large-scale **Traditional Chinese Dimensional Sentiment Dialogue Dataset**. The tool focuses on extracting complex multi-turn conversations from social media platforms to support advanced Natural Language Processing (NLP) tasks, specifically in the field of Aspect-Based Sentiment Analysis (ABSA).

## Research Objective
The primary goal of this research is to develop a predictive model capable of identifying sentiment quadruples `(target, aspect, opinion, intensity)` within multi-turn dialogues. Unlike traditional categorical sentiment analysis, this project utilizes **Dimensional Emotion Models** (Valence and Arousal) to provide a more granular understanding of user emotions in a conversational context.

## Technical Architecture: Two-Stage Pipeline
The system implements a rigorous "two-stage" pipeline to transform flat, noisy comment data into structured, high-quality dialogue trees.

### Stage 1: Systematic Data Acquisition
* **Methodology:** Automated extraction of comment threads from curated domain-specific video playlists via the YouTube Data API v3.
* **Heuristic Filtering:** To ensure conversational depth, the system only retains threads with a `totalReplyCount >= 4`, ensuring each sample contains at least 5 distinct utterances.
* **Metadata Management:** Each dialogue is automatically tagged with domain labels (e.g., Electronics, Hospitality) to facilitate cross-domain model evaluation.

### Stage 2: Topology Reconstruction & Linguistic Denoising
* **Dialogue Tree Building:** Implements a dynamic string-matching algorithm to resolve `@username` mentions, recursively mapping reply-to relationships to reconstruct the $n \rightarrow m$ dialogue topology.
* **Advanced Text Cleaning:**
    * **PLM Optimization:** Precision removal of social mentions to prevent attention-mechanism interference in Pre-trained Language Models.
    * **Feature Preservation:** Retains Emojis and punctuation, which serve as critical features for Valence and Arousal estimation.
    * **Span Alignment:** Uses regular expressions to normalize whitespace and line breaks, preventing character-index misalignment during the annotation of Target-Aspect-Opinion spans.
* **Structural Validation:** Utilizes **Depth-First Search (DFS)** algorithms to enforce strict topology standards (Nodes: 5-12, Depth: 3-5, Leaf Nodes $\ge$ 2), discarding low-quality or linear conversations.

## Requirements & Usage
This pipeline is built with Python and utilizes the `google-api-python-client`. It is designed for academic researchers requiring structured conversational data for sentiment and emotion-related NLP tasks.
