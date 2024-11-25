import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import check_authentication, check_supervisor
from database import get_search_statistics

def supervisor_dashboard():
    check_authentication()
    check_supervisor()
    
    st.title("Supervisor Dashboard")
    
    # Get statistics from database
    stats = get_search_statistics()
    df_stats = pd.DataFrame(stats)
    
    # Overview metrics
    st.header("Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_searches = len(stats) if stats else 0
        st.metric("Total Searches", total_searches)
    
    with col2:
        total_successful = sum(1 for stat in stats if stat.get('result_found', False))
        st.metric("Successful Searches", total_successful)
    
    with col3:
        success_rate = (total_successful / total_searches * 100) if total_searches > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Daily searches chart
    st.header("Daily Search Activity")
    fig_daily = px.line(
        df_stats,
        x='search_day',
        y=['total_searches', 'successful_searches'],
        title='Search Activity Over Time'
    )
    st.plotly_chart(fig_daily, use_container_width=True)
    
    # Success rate chart
    st.header("Success Rate Analysis")
    fig_success = go.Figure()
    fig_success.add_trace(go.Pie(
        labels=['Successful', 'Unsuccessful'],
        values=[total_successful, total_searches - total_successful],
        hole=0.4
    ))
    st.plotly_chart(fig_success, use_container_width=True)
    
    # Export full statistics
    st.header("Export Statistics")
    if st.button("Export Full Statistics"):
        with st.spinner("Preparing export..."):
            # Convert statistics to Excel
            buffer = pd.ExcelWriter('statistics.xlsx', engine='openpyxl')
            df_stats.to_excel(buffer, index=False)
            buffer.close()
            
            with open('statistics.xlsx', 'rb') as f:
                st.download_button(
                    label="Download Statistics",
                    data=f,
                    file_name="search_statistics.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    supervisor_dashboard()
