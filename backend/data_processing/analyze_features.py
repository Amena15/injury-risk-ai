"""
analyze_features.py

Comprehensive feature analysis and visualization for the tennis dataset.
Creates detailed reports and visualizations for model training insights.

Usage:
    python -m data_processing.analyze_features
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FeatureAnalyzer:
    def __init__(self, input_csv='data_processing/enhanced_tennis_dataset.csv', output_dir='data_processing'):
        self.input_csv = input_csv
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """Load the enhanced dataset"""
        df = pd.read_csv(self.input_csv)
        print(f"Loaded dataset: {len(df)} samples, {len(df.columns)} features")
        return df
    
    def generate_comprehensive_report(self, df):
        """Generate comprehensive data quality report"""
        print("\n" + "="*70)
        print("COMPREHENSIVE FEATURE ANALYSIS REPORT")
        print("="*70)
        
        print(f"\n📊 DATASET OVERVIEW:")
        print(f"  Total samples: {len(df)}")
        print(f"  Total features: {len(df.columns)}")
        print(f"  Missing values: {df.isnull().sum().sum()}")
        print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        print(f"\n🎯 RISK DISTRIBUTION:")
        risk_dist = df['risk_level'].value_counts()
        for level, count in risk_dist.items():
            percentage = (count / len(df)) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")
        
        print(f"\n📈 RISK SCORE STATISTICS:")
        print(f"  Mean: {df['risk_score'].mean():.1f}")
        print(f"  Median: {df['risk_score'].median():.1f}")
        print(f"  Std: {df['risk_score'].std():.1f}")
        print(f"  Min: {df['risk_score'].min():.1f}")
        print(f"  Max: {df['risk_score'].max():.1f}")
        print(f"  25th percentile: {df['risk_score'].quantile(0.25):.1f}")
        print(f"  75th percentile: {df['risk_score'].quantile(0.75):.1f}")
        
        print(f"\n📐 JOINT ANGLE STATISTICS:")
        angle_cols = [col for col in df.columns if 'angle' in col and not ('zscore' in col or 'extreme' in col or 'optimal' in col)]
        
        for col in angle_cols:
            print(f"  {col}:")
            print(f"    Mean: {df[col].mean():.1f}° ± {df[col].std():.1f}°")
            print(f"    Range: {df[col].min():.1f}° - {df[col].max():.1f}°")
            print(f"    Median: {df[col].median():.1f}°")
        
        print(f"\n🏃 ACTION DISTRIBUTION:")
        if 'action' in df.columns:
            action_dist = df['action'].value_counts()
            for action, count in action_dist.items():
                percentage = (count / len(df)) * 100
                print(f"  {action}: {count} ({percentage:.1f}%)")
        
        print(f"\n🔍 FEATURE QUALITY CHECKS:")
        # Check for unrealistic values
        for col in angle_cols:
            unrealistic = ((df[col] < 0) | (df[col] > 180)).sum()
            if unrealistic > 0:
                print(f"  ⚠️ {col}: {unrealistic} unrealistic values (<0° or >180°)")
            else:
                print(f"  ✅ {col}: All values in realistic range")
        
        # Check for extreme outliers
        for col in angle_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = ((df[col] < (q1 - 3 * iqr)) | (df[col] > (q3 + 3 * iqr))).sum()
            if outliers > 0:
                print(f"  ⚠️ {col}: {outliers} extreme outliers")
            else:
                print(f"  ✅ {col}: No extreme outliers")
        
        print("="*70)
    
    def create_visualizations(self, df):
        """Create comprehensive visualizations"""
        print("\n📊 Creating visualizations...")
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (15, 10)
        
        # 1. Risk Distribution
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Risk level distribution
        risk_counts = df['risk_level'].value_counts()
        axes[0, 0].pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('Risk Level Distribution')
        
        # Risk score histogram
        axes[0, 1].hist(df['risk_score'], bins=30, edgecolor='black', alpha=0.7)
        axes[0, 1].set_xlabel('Risk Score')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Risk Score Distribution')
        
        # Risk by action
        if 'action' in df.columns:
            action_risk = df.groupby('action')['risk_score'].mean()
            axes[0, 2].bar(action_risk.index, action_risk.values)
            axes[0, 2].set_xlabel('Action')
        axes[0, 2].set_ylabel('Mean Risk Score')
        axes[0, 2].set_title('Average Risk Score by Action')
        axes[0, 2].tick_params(axis='x', rotation=45)
        
        # 2. Joint Angle Distributions
        angle_cols = [col for col in df.columns if 'angle' in col and not ('zscore' in col or 'extreme' in col or 'optimal' in col)]
        
        for i, col in enumerate(angle_cols[:4]):
            row, col_idx = (1, i) if i < 3 else (1, 2)
            if i >= 3:
                break
            
            if i < len(angle_cols):
                axes[row, col_idx].hist(df[angle_cols[i]], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
                axes[row, col_idx].set_xlabel('Angle (degrees)')
                axes[row, col_idx].set_ylabel('Frequency')
                axes[row, col_idx].set_title(f'{angle_cols[i]} Distribution')
        
        plt.tight_layout()
        risk_viz_path = self.output_dir / 'risk_analysis_visualizations.png'
        plt.savefig(risk_viz_path, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved risk analysis visualizations to {risk_viz_path}")
        plt.close()
        
        # 3. Joint Angle Correlation Heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        angle_corr = df[angle_cols].corr()
        sns.heatmap(angle_corr, annot=True, cmap='coolwarm', center=0, 
                    square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        ax.set_title('Joint Angle Correlation Matrix')
        plt.tight_layout()
        corr_path = self.output_dir / 'joint_angle_correlation.png'
        plt.savefig(corr_path, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved correlation heatmap to {corr_path}")
        plt.close()
        
        # 4. Risk Score by Joint Angles
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        for i, col in enumerate(angle_cols[:4]):
            row, col_idx = divmod(i, 2)
            
            # Create bins for angle ranges
            df[f'{col}_bin'] = pd.cut(df[col], bins=10, labels=False)
            bin_risk = df.groupby(f'{col}_bin')['risk_score'].mean()
            
            axes[row, col_idx].plot(bin_risk.index, bin_risk.values, marker='o', linewidth=2)
            axes[row, col_idx].set_xlabel(f'{col} (binned)')
            axes[row, col_idx].set_ylabel('Mean Risk Score')
            axes[row, col_idx].set_title(f'Risk Score vs {col}')
            axes[row, col_idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        angle_risk_path = self.output_dir / 'angle_risk_relationship.png'
        plt.savefig(angle_risk_path, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved angle-risk relationships to {angle_risk_path}")
        plt.close()
        
        # 5. Enhanced Features Analysis
        enhanced_cols = [col for col in df.columns if 'zscore' in col or 'extreme' in col or 'optimal' in col]
        if enhanced_cols:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            # Z-score distributions
            zscore_cols = [col for col in enhanced_cols if 'zscore' in col][:4]
            for i, col in enumerate(zscore_cols):
                row, col_idx = divmod(i, 2)
                axes[row, col_idx].hist(df[col], bins=20, edgecolor='black', alpha=0.7, color='lightcoral')
                axes[row, col_idx].set_xlabel('Z-Score')
                axes[row, col_idx].set_ylabel('Frequency')
                axes[row, col_idx].set_title(f'{col} Distribution')
                axes[row, col_idx].axvline(x=0, color='red', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            enhanced_path = self.output_dir / 'enhanced_features_analysis.png'
            plt.savefig(enhanced_path, dpi=300, bbox_inches='tight')
            print(f"  ✅ Saved enhanced features analysis to {enhanced_path}")
            plt.close()
    
    def analyze_feature_importance(self, df):
        """Analyze and visualize feature importance"""
        print("\n🔍 Analyzing feature importance...")
        
        # Load feature importance if available
        importance_path = self.output_dir / 'feature_importance.csv'
        if importance_path.exists():
            importance_df = pd.read_csv(importance_path)
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 8))
            
            top_features = importance_df.head(15)
            colors = plt.cm.viridis(np.linspace(0, 1, len(top_features)))
            
            bars = ax.barh(top_features['feature'], top_features['importance'], color=colors)
            ax.set_xlabel('Importance Score')
            ax.set_ylabel('Feature')
            ax.set_title('Top 15 Most Important Features')
            ax.invert_yaxis()
            
            # Add value labels
            for i, (bar, value) in enumerate(zip(bars, top_features['importance'])):
                ax.text(value + 0.001, bar.get_y() + bar.get_height()/2, 
                       f'{value:.3f}', va='center', fontsize=9)
            
            plt.tight_layout()
            importance_viz_path = self.output_dir / 'feature_importance_visualization.png'
            plt.savefig(importance_viz_path, dpi=300, bbox_inches='tight')
            print(f"  ✅ Saved feature importance visualization to {importance_viz_path}")
            plt.close()
            
            print("\n📊 TOP 10 MOST IMPORTANT FEATURES:")
            print(top_features.head(10).to_string(index=False))
        else:
            print("  ⚠️ Feature importance file not found. Run enhanced_dataset_processor first.")
    
    def generate_statistical_summary(self, df):
        """Generate detailed statistical summary"""
        print("\n📈 Generating statistical summary...")
        
        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Generate summary statistics
        summary_stats = df[numeric_cols].describe()
        
        # Save to CSV
        summary_path = self.output_dir / 'statistical_summary.csv'
        summary_stats.to_csv(summary_path)
        print(f"  ✅ Saved statistical summary to {summary_path}")
        
        # Print key insights
        print("\n🔑 KEY STATISTICAL INSIGHTS:")
        angle_cols = [col for col in df.columns if 'angle' in col and not ('zscore' in col or 'extreme' in col or 'optimal' in col)]
        
        for col in angle_cols:
            cv = df[col].std() / df[col].mean() * 100  # Coefficient of variation
            skewness = df[col].skew()
            kurtosis = df[col].kurtosis()
            
            print(f"  {col}:")
            print(f"    Coefficient of variation: {cv:.1f}%")
            print(f"    Skewness: {skewness:.2f} ({'right-skewed' if skewness > 0 else 'left-skewed' if skewness < 0 else 'symmetric'})")
            print(f"    Kurtosis: {kurtosis:.2f} ({'heavy-tailed' if kurtosis > 0 else 'light-tailed' if kurtosis < 0 else 'normal'})")
    
    def save_analysis_report(self, df):
        """Save comprehensive analysis report to file"""
        report_path = self.output_dir / 'feature_analysis_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("COMPREHENSIVE FEATURE ANALYSIS REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Dataset Overview:\n")
            f.write(f"  Total samples: {len(df)}\n")
            f.write(f"  Total features: {len(df.columns)}\n")
            f.write(f"  Missing values: {df.isnull().sum().sum()}\n\n")
            
            f.write(f"Risk Distribution:\n")
            risk_dist = df['risk_level'].value_counts()
            for level, count in risk_dist.items():
                percentage = (count / len(df)) * 100
                f.write(f"  {level}: {count} ({percentage:.1f}%)\n")
            
            f.write(f"\nGenerated visualizations:\n")
            f.write(f"  - risk_analysis_visualizations.png\n")
            f.write(f"  - joint_angle_correlation.png\n")
            f.write(f"  - angle_risk_relationship.png\n")
            f.write(f"  - enhanced_features_analysis.png\n")
            f.write(f"  - feature_importance_visualization.png\n")
        
        print(f"  ✅ Saved analysis report to {report_path}")

def main():
    """Main analysis pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze tennis dataset features')
    parser.add_argument('--input', type=str, default='data_processing/enhanced_tennis_dataset.csv', help='Input CSV file')
    parser.add_argument('--output-dir', type=str, default='data_processing', help='Output directory')
    
    args = parser.parse_args()
    
    analyzer = FeatureAnalyzer(input_csv=args.input, output_dir=args.output_dir)
    
    try:
        # Load data
        df = analyzer.load_data()
        
        # Generate comprehensive report
        analyzer.generate_comprehensive_report(df)
        
        # Create visualizations
        analyzer.create_visualizations(df)
        
        # Analyze feature importance
        analyzer.analyze_feature_importance(df)
        
        # Generate statistical summary
        analyzer.generate_statistical_summary(df)
        
        # Save analysis report
        analyzer.save_analysis_report(df)
        
        print(f"\n🎉 Feature analysis complete! All visualizations and reports saved to {args.output_dir}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise

if __name__ == '__main__':
    main()