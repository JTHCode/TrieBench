import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="Data Visualization App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("📊 Minimal Data Visualization App")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.selectbox(
        "Choose a section:",
        ["Home", "Data Upload", "Sample Charts", "Data Analysis"]
    )
    
    st.markdown("---")
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Main content area
if page == "Home":
    st.header("Welcome to Your Data Visualization Dashboard")
    
    # Introduction text
    st.markdown("""
    This minimal Streamlit application provides essential components for data visualization and analysis:
    
    **Key Features:**
    - 📁 File upload functionality
    - 📊 Interactive charts and visualizations
    - 📋 Data table display
    - 🔍 Basic data analysis tools
    """)
    
    # Sample metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", "0", "No data loaded")
    
    with col2:
        st.metric("Columns", "0", "No data loaded")
    
    with col3:
        st.metric("Memory Usage", "0 MB", "No data loaded")
    
    with col4:
        st.metric("Last Updated", "Never", "No data loaded")

elif page == "Data Upload":
    st.header("📁 Data Upload")
    
    st.markdown("Upload your data files to get started with analysis:")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file to analyze your data"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            df = pd.read_csv(uploaded_file)
            
            # Store in session state
            st.session_state['data'] = df
            
            st.success(f"✅ File uploaded successfully! Shape: {df.shape}")
            
            # Display basic info
            st.subheader("Dataset Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**First 5 rows:**")
                st.dataframe(df.head())
            
            with col2:
                st.write("**Dataset Info:**")
                st.write(f"- Rows: {df.shape[0]}")
                st.write(f"- Columns: {df.shape[1]}")
                st.write(f"- Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
                
                st.write("**Column Types:**")
                for col, dtype in df.dtypes.items():
                    st.write(f"- {col}: {dtype}")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    else:
        st.info("👆 Please upload a CSV file to begin analysis")

elif page == "Sample Charts":
    st.header("📊 Sample Charts")
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        st.subheader("Interactive Visualizations")
        
        # Get numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Select X-axis:**")
                x_column = st.selectbox("X-axis", numeric_columns, key="x_axis")
            
            with col2:
                st.write("**Select Y-axis:**")
                y_column = st.selectbox("Y-axis", numeric_columns, key="y_axis")
            
            # Chart type selection
            chart_type = st.selectbox(
                "Chart Type",
                ["Scatter Plot", "Line Chart", "Bar Chart", "Histogram"]
            )
            
            # Generate chart based on selection
            if chart_type == "Scatter Plot":
                fig = px.scatter(df, x=x_column, y=y_column, title=f"{y_column} vs {x_column}")
            elif chart_type == "Line Chart":
                fig = px.line(df, x=x_column, y=y_column, title=f"{y_column} over {x_column}")
            elif chart_type == "Bar Chart":
                fig = px.bar(df, x=x_column, y=y_column, title=f"{y_column} by {x_column}")
            elif chart_type == "Histogram":
                fig = px.histogram(df, x=x_column, title=f"Distribution of {x_column}")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Additional chart if categorical columns exist
            if categorical_columns:
                st.subheader("Categorical Analysis")
                cat_column = st.selectbox("Select categorical column", categorical_columns)
                
                if cat_column:
                    value_counts = df[cat_column].value_counts()
                    fig_pie = px.pie(
                        values=value_counts.values,
                        names=value_counts.index,
                        title=f"Distribution of {cat_column}"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
        
        else:
            st.warning("⚠️ No numeric columns found in the dataset for visualization")
    
    else:
        st.info("📁 Please upload data in the 'Data Upload' section first")
        
        # Show sample chart with generated data
        st.subheader("Sample Visualization (Demo)")
        
        # Generate sample data for demonstration
        sample_x = np.linspace(0, 10, 50)
        sample_y = np.sin(sample_x) + np.random.normal(0, 0.1, 50)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sample_x, y=sample_y, mode='markers+lines', name='Sample Data'))
        fig.update_layout(title="Sample Sine Wave with Noise", xaxis_title="X values", yaxis_title="Y values")
        
        st.plotly_chart(fig, use_container_width=True)

elif page == "Data Analysis":
    st.header("🔍 Data Analysis")
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        # Data summary
        st.subheader("Statistical Summary")
        
        tab1, tab2, tab3 = st.tabs(["Descriptive Stats", "Data Types", "Missing Values"])
        
        with tab1:
            st.write("**Descriptive Statistics:**")
            st.dataframe(df.describe())
        
        with tab2:
            st.write("**Data Types:**")
            dtype_df = pd.DataFrame({
                'Column': df.columns,
                'Data Type': df.dtypes.values,
                'Non-Null Count': df.count().values,
                'Null Count': df.isnull().sum().values
            })
            st.dataframe(dtype_df)
        
        with tab3:
            st.write("**Missing Values Analysis:**")
            missing_data = df.isnull().sum()
            missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
            
            if len(missing_data) > 0:
                fig_missing = px.bar(
                    x=missing_data.index,
                    y=missing_data.values,
                    title="Missing Values by Column"
                )
                fig_missing.update_layout(xaxis_title="Columns", yaxis_title="Missing Count")
                st.plotly_chart(fig_missing, use_container_width=True)
            else:
                st.success("✅ No missing values found in the dataset!")
        
        # Data filtering
        st.subheader("Data Filtering")
        
        with st.expander("Filter Data"):
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_columns:
                filter_column = st.selectbox("Select column to filter", numeric_columns)
                
                if filter_column:
                    min_val = float(df[filter_column].min())
                    max_val = float(df[filter_column].max())
                    
                    filter_range = st.slider(
                        f"Filter {filter_column}",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )
                    
                    filtered_df = df[
                        (df[filter_column] >= filter_range[0]) & 
                        (df[filter_column] <= filter_range[1])
                    ]
                    
                    st.write(f"**Filtered Data ({len(filtered_df)} rows):**")
                    st.dataframe(filtered_df)
        
        # Raw data view
        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)
    
    else:
        st.info("📁 Please upload data in the 'Data Upload' section first")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #B0B0B0; padding: 1rem;'>
        Built with Streamlit 🚀 | Minimal Data Visualization App
    </div>
    """,
    unsafe_allow_html=True
)
