import streamlit as st
import pandas as pd

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ReportGenerator:
    def __init__(self, data):
        self.data = data

    def generate_summary(self):
        summary = {
            "Total Cases": len(self.data),
            "Positive Cases": sum(1 for case in self.data if case['is_positive']),
            "Negative Cases": sum(1 for case in self.data if not case['is_positive'])
        }
        return summary

    def generate_charts(self):
        if not MATPLOTLIB_AVAILABLE:
            st.warning("Matplotlib is not available. Charts cannot be generated.")
            return

        # Pie chart for case status
        status_counts = pd.Series([case['status'] for case in self.data]).value_counts()
        plt.figure(figsize=(10, 6))
        plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
        plt.title("Case Status Distribution")
        st.pyplot(plt)

        # Bar chart for cases by month
        df = pd.DataFrame(self.data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        monthly_counts = df.groupby(df['created_at'].dt.to_period("M")).size()
        plt.figure(figsize=(12, 6))
        monthly_counts.plot(kind='bar')
        plt.title("Cases by Month")
        plt.xlabel("Month")
        plt.ylabel("Number of Cases")
        plt.xticks(rotation=45)
        st.pyplot(plt)

    def generate_report(self):
        st.header("Case Report")

        summary = self.generate_summary()
        st.subheader("Summary")
        for key, value in summary.items():
            st.write(f"{key}: {value}")

        st.subheader("Charts")
        self.generate_charts()

        st.subheader("Detailed Case List")
        st.dataframe(pd.DataFrame(self.data))

