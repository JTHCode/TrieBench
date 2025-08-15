# Data Visualization App

## Overview

This is a minimal Streamlit-based data visualization application designed to provide essential components for interactive data analysis and visualization. The app features a multi-page interface with capabilities for data upload, chart generation, and basic data analysis tools. Built with Streamlit as the primary framework, it leverages Plotly for interactive visualizations and pandas/numpy for data processing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses Streamlit as the primary web framework, providing a Python-based approach to building interactive web applications. The architecture follows Streamlit's component-based model with:

- **Single-file application structure** - All functionality contained in `app.py` for simplicity
- **Multi-page navigation** - Sidebar-based page selection system with sections for Home, Data Upload, Sample Charts, and Data Analysis
- **Wide layout configuration** - Optimized for data visualization with expanded sidebar state
- **Responsive column layout** - Uses Streamlit's column system for organized content display

### Data Processing Layer
The application incorporates standard Python data science libraries:

- **Pandas** - Primary data manipulation and analysis library
- **NumPy** - Numerical computing foundation for data operations
- **Data structure handling** - Built to work with CSV files and tabular data formats

### Visualization Engine
Interactive visualization capabilities powered by:

- **Plotly Express** - High-level plotting interface for quick chart generation
- **Plotly Graph Objects** - Low-level plotting for custom visualizations
- **Chart types** - Supports multiple visualization formats including line charts, bar charts, scatter plots, and custom dashboards

### User Interface Components
The interface design emphasizes usability with:

- **Navigation sidebar** - Centralized page selection and quick actions
- **Metric display system** - Dashboard-style key performance indicators
- **Refresh functionality** - Real-time data updates through Streamlit's rerun mechanism
- **Markdown integration** - Rich text formatting for documentation and instructions

## External Dependencies

### Core Libraries
- **Streamlit** - Web application framework and user interface
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing operations
- **Plotly** - Interactive visualization library (both Express and Graph Objects modules)

### Browser Requirements
- Modern web browser with JavaScript support for Plotly interactive features
- No additional external APIs or databases required for basic functionality

### Deployment Considerations
- Python environment with pip package management
- No external database dependencies in current implementation
- Self-contained application suitable for local development or cloud deployment platforms