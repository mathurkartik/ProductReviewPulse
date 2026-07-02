# ProductReviewPulse

ProductReviewPulse is an automated AI agent designed to bridge the gap between public customer feedback and product leadership. It ingests reviews from the Apple App Store and Google Play Store, uses LLMs to distill them into actionable themes, and delivers a premium "Weekly Pulse" report via Google Docs and Gmail.

## Core Features

- **Ingestion & Scrubbing**: Automatically fetches reviews using `itunes-iap` (App Store) and `google-play-scraper` (Play Store). A PII Scrubber removes emails, phone numbers, and sensitive IDs before data is stored in a local SQLite database.
- **Clustering**: Uses local embeddings (bge-small-en-v1.5) to convert review text into vectors, applying UMAP for dimensionality reduction and HDBSCAN for density-based clustering to automatically group similar feedback.
- **LLM Summarization**: Sends the most representative reviews of each cluster to a Groq-hosted Llama 3 model. The LLM generates themes, summaries, and "Action Ideas." A Verbatim Validator ensures any quote included actually exists in the raw data.
- **Rendering**: Uses Jinja2 templates to convert the summaries into Google Docs requests and Gmail HTML/plain-text content.
- **Delivery Engine (MCP)**: Uses the Model Context Protocol (MCP) via a custom FastAPI server to interact with Google Docs and Gmail. This ensures the agent never has direct access to Google credentials. Features include Google Doc caching, section idempotency, and Draft-First email creation.

## Documentation

For a deep dive into the project's design and status, check the `/Docs` directory:
- [Problem Statement](Docs/ProblemStatement.md)
- [Architecture](Docs/Architecture.md)
- [Project Summary](Docs/summary.md)
- [Implementation Plan](Docs/implementationPlan.md)
- [Full Project Review](project_review.md)
