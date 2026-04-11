# SOFIA-S - Survey Processing & Reporting Platform

## Project Overview

SOFIA-S (short for Sistema de Obtención, Filtrado e Inteligencia Analítica de Sondeos) is a Django web application designed to streamline the full lifecycle of survey data: from form delivery and response collection to data processing and dynamic report generation.

The platform replaces manual workflows by providing a centralized system where surveys are managed, responses are automatically processed, and dashboards update in real time.

## Core Purpose

SOFIA-S simplifies the current manual process where survey responses are collected, compiled, analyzed, and turned into reports.

With SOFIA-S:

- Surveys are displayed directly in the application
- Responses are stored and processed automatically
- Dashboards and reports are generated and updated dynamically as new data arrives

## Key Features

### Survey Management

- Create and manage survey forms
- Display forms to users for submission
- Support for different question types and structures

### Response Handling

- Store and manage submitted answers
- Validate incoming data
- Track submissions over time

### Data Processing

- Transform raw responses into structured data
- Compute aggregates (counts, averages, distributions)
- Prepare data for visualization and reporting

### Dashboards & Reports

- Automatically generated dashboards
- Real-time updates when new responses are submitted
- Overview reports summarizing key insights
- Visualizations for trends and comparisons

### Architecture Overview

#### Backend
- Framework: Django
- Language: Python
- Database: PostgreSQL

#### Frontend
- Templates: Django templates
- Styling: TailwindCSS
- Approach: Server-rendered with dynamic updates where needed

### How It Works

1. A survey is created and published through the platform
2. Users submit responses via the web interface
3. Responses are stored and validated
4. Data is processed and aggregated automatically
5. Dashboards and reports update dynamically

### Development Setup (High-Level)

- Python 3.13
- Django 6.0
- PostgreSQL

### Goal

The primary goal of SOFIA-S is to reduce manual effort, improve accuracy, and provide immediate insights from survey data through automation and real-time reporting.