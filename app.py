from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Load the dataset globally
DATASET_PATH = r'sales_data_sample.csv'  # Using a raw string
def load_and_clean_data(): 
    try:
        data = pd.read_csv(DATASET_PATH, encoding='ISO-8859-1')
        
        # Data Cleaning
        data['ORDERDATE'] = pd.to_datetime(data['ORDERDATE'], errors='coerce')
        data['QUANTITYORDERED'] = pd.to_numeric(data['QUANTITYORDERED'], errors='coerce')
        data['PRICEEACH'] = pd.to_numeric(data['PRICEEACH'], errors='coerce')
        data = data.dropna(subset=['ORDERDATE', 'QUANTITYORDERED', 'PRICEEACH'])
        
        # Data Validation
        print(data.head())
        print(data.dtypes)
        print(data.isnull().sum())
        
        return data
    except Exception as e:
        print(f"Error loading or cleaning data: {str(e)}")
        return None

data = load_and_clean_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    try:
        if data is None:
            return render_template('error.html', error="Data not loaded properly")

        # Step 2: Compute Metrics for Each Product
        product_metrics = data.groupby('PRODUCTCODE').agg(
            Total_Revenue=('QUANTITYORDERED', lambda x: (x * data.loc[x.index, 'PRICEEACH']).sum()),
            Total_Units_Sold=('QUANTITYORDERED', 'sum'),
            Average_Price_Per_Unit=('PRICEEACH', 'mean'),
            Total_Orders=('ORDERNUMBER', 'nunique')
        ).reset_index().sort_values(by='Total_Revenue', ascending=False)

        # Step 3: Compute Monthly Metrics
        data['Month'] = data['ORDERDATE'].dt.to_period('M')
        monthly_metrics = data.groupby('Month').agg(
            Total_Revenue=('QUANTITYORDERED', lambda x: (x * data.loc[x.index, 'PRICEEACH']).sum()),
            Total_Units_Sold=('QUANTITYORDERED', 'sum'),
            Average_Price_Per_Unit=('PRICEEACH', 'mean')
        ).reset_index()

        # Plotting the metrics
        plt.figure(figsize=(12, 18))
        
        plt.subplot(3, 1, 1)
        plt.plot(monthly_metrics['Month'].astype(str), monthly_metrics['Total_Revenue'], marker='o')
        plt.title('Total Revenue Over Time')
        plt.xlabel('Month')
        plt.ylabel('Total Revenue')
        plt.xticks(rotation=45)

        plt.subplot(3, 1, 2)
        plt.plot(monthly_metrics['Month'].astype(str), monthly_metrics['Total_Units_Sold'], marker='o', color='orange')
        plt.title('Total Units Sold Over Time')
        plt.xlabel('Month')
        plt.ylabel('Total Units Sold')
        plt.xticks(rotation=45)

        plt.subplot(3, 1, 3)
        plt.plot(monthly_metrics['Month'].astype(str), monthly_metrics['Average_Price_Per_Unit'], marker='o', color='green')
        plt.title('Average Price Per Unit Over Time')
        plt.xlabel('Month')
        plt.ylabel('Average Price Per Unit')
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig('static/metrics_plot.png')  # Save the plot to static folder
        plt.close()

        # Step 4: Identify Top 5 Cities for Sales
        def extract_city(address):
            if isinstance(address, str):
                parts = address.split(',')
                return parts[1].strip() if len(parts) > 1 else 'Unknown'
            return 'Unknown'

        data['City'] = data['ADDRESSLINE1'].apply(extract_city)
        city_sales = data.groupby('CITY').agg(
            Total_Revenue=('QUANTITYORDERED', lambda x: (x * data.loc[x.index, 'PRICEEACH']).sum()),
            Total_Units_Sold=('QUANTITYORDERED', 'sum'),
            Total_Orders=('ORDERNUMBER', 'nunique')
        ).reset_index().sort_values(by='Total_Revenue', ascending=False).head(5)

        return render_template('analysis.html', product_metrics=product_metrics.to_html(classes='data'),
                               monthly_metrics=monthly_metrics.to_html(classes='data'),
                               top_cities=city_sales.to_html(classes='data'))
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=False,port=8000)