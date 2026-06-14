import pandas as pd
import numpy as np
import logging
from sklearn.metrics import confusion_matrix
from typing import Dict, List, Tuple, Any, Optional, Callable
import itertools
import os
from dataclasses import dataclass

logger = logging.getLogger('ethiviz.enhanced')

@dataclass
class TextAnalysisResult:
    # Define your result fields here
    bias_score: float
    diversity_index: float
    western_ethics_score: float
    ubuntu_ethics_score: float
    confucian_ethics_score: float
    islamic_ethics_score: float
    # ...add more as needed

    def to_dict(self):
        return self.__dict__

class HybridTextAnalyzer:
    def __init__(self, traditions, spacy_model="en_core_web_sm", max_tokens=10000):
        self.framework = DualEthicsFramework(ethical_traditions=traditions)
        # ...store other params as needed

    def analyze(self, text_data_input):
        # Example: text_data_input is a list of texts
        # For each text, create a dummy DataFrame and analyze
        results = []
        for text in text_data_input:
            # You would extract features, predictions, etc. here
            # For demonstration, use dummy data
            df = pd.DataFrame({
                "gender": ["Male", "Female", "Male"], # Ensure enough rows for analysis
                "race": ["White", "Black", "Asian"],
                "predicted": [1, 0, 1],
                "actual": [1, 1, 0]
            })
            analysis = self.framework.analyze_dataset(
                dataset=df,
                sensitive_attributes=["gender", "race"],
                prediction_column="predicted",
                actual_column="actual"
            )
            # Convert analysis to your result format
            result = TextAnalysisResult(
                bias_score=0.5,  # Replace with real value
                diversity_index=0.7,  # Replace with real value
                western_ethics_score=0.8,
                ubuntu_ethics_score=0.9,
                confucian_ethics_score=0.85,
                islamic_ethics_score=0.88
            )
            results.append(result)
        return results

# Optionally, do the same for HybridImageAnalyzer

class DualEthicsFramework:
    """
    Enhanced framework for applying multiple ethical perspectives to dataset analysis.
    Includes cultural context sensitivity, intersectional analysis, and integrated metrics.
    """
    
    def __init__(
        self,
        ethical_traditions: List[str] = ["western", "ubuntu", "confucian", "islamic"],
        cultural_context: Dict[str, Any] = None,
        stakeholder_weights: Dict[str, float] = None,
        historical_context: Dict[str, Any] = None
    ):
        self.ethical_traditions = ethical_traditions
        self.cultural_context = cultural_context or {}
        self.stakeholder_weights = stakeholder_weights or self._default_stakeholder_weights()
        self.historical_context = historical_context or {}
        self.metrics = self._initialize_metrics()
        
    def _default_stakeholder_weights(self) -> Dict[str, float]:
        """Default equal weighting for all metrics"""
        return {tradition: 1.0 for tradition in self.ethical_traditions}
    
    def _initialize_metrics(self) -> Dict[str, Dict[str, Callable]]:
        """Initialize metrics for each ethical tradition"""
        metrics = {}
        
        # Western metrics focus on individual fairness and equal treatment
        metrics["western"] = {
            "statistical_parity": self.calculate_statistical_parity,
            "equal_opportunity": self.calculate_equal_opportunity,
            "disparate_impact": self.calculate_disparate_impact
        }
        
        # Ubuntu metrics focus on community harmony and relationships
        metrics["ubuntu"] = {
            "group_harmony": self.calculate_group_harmony,
            "communal_benefit": self.calculate_communal_benefit,
            "relational_impact": self.calculate_relational_impact
        }
        
        # Confucian metrics focus on social harmony and role fulfillment
        metrics["confucian"] = {
            "role_appropriateness": self.calculate_role_appropriateness,
            "social_harmony": self.calculate_social_harmony,
            "hierarchical_fairness": self.calculate_hierarchical_fairness
        }
        
        # Islamic metrics focus on equity and compassion
        metrics["islamic"] = {
            "equitable_treatment": self.calculate_equitable_treatment,
            "harm_prevention": self.calculate_harm_prevention,
            "dignity_preservation": self.calculate_dignity_preservation
        }
        
        # Hybrid/integrated metrics that combine perspectives
        metrics["integrated"] = {
            "cultural_inclusion_index": self.calculate_cultural_inclusion_index,
            "contextual_fairness": self.calculate_contextual_fairness,
            "harmony_equity_balance": self.calculate_harmony_equity_balance
        }
        
        return metrics
    
    def analyze_dataset(
        self,
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        prediction_column: str,
        actual_column: str,
        domain_context: str = None
    ) -> Dict[str, Any]:
        """
        Analyze a dataset using multiple ethical frameworks with context awareness
        
        Parameters:
        -----------
        dataset : pandas.DataFrame
            The dataset to analyze
        sensitive_attributes : List[str]
            List of column names for attributes that may be subject to bias
        prediction_column : str
            Column name containing model predictions or classifications
        actual_column : str
            Column name containing ground truth values
        domain_context : str, optional
            Domain-specific context (e.g., "healthcare", "criminal_justice")
            
        Returns:
        --------
        Dict[str, Any]
            Results from all ethical analyses including integrated perspectives
        """
        # Prepare results structure
        results = {
            "metadata": {
                "dataset_size": len(dataset),
                "attributes_analyzed": sensitive_attributes,
                "domain_context": domain_context
            },
            "tradition_analysis": {},
            "intersectional_analysis": {},
            "integrated_analysis": {},
            "recommendations": {}
        }
        
        # Apply metrics from each ethical tradition
        for tradition in self.ethical_traditions:
            if tradition in self.metrics:
                results["tradition_analysis"][tradition] = {}
                for metric_name, metric_func in self.metrics[tradition].items():
                    # Apply cultural context and historical information
                    results["tradition_analysis"][tradition][metric_name] = metric_func(
                        dataset=dataset,
                        sensitive_attributes=sensitive_attributes,
                        prediction_column=prediction_column,
                        actual_column=actual_column,
                        cultural_context=self.cultural_context.get(tradition, {}),
                        historical_context=self.historical_context,
                        domain_context=domain_context
                    )
        
        # Perform intersectional analysis
        results["intersectional_analysis"] = self.perform_intersectional_analysis(
            dataset=dataset,
            sensitive_attributes=sensitive_attributes,
            prediction_column=prediction_column,
            actual_column=actual_column
        )
        
        # Apply integrated metrics
        for metric_name, metric_func in self.metrics.get("integrated", {}).items():
            results["integrated_analysis"][metric_name] = metric_func(
                dataset=dataset,
                sensitive_attributes=sensitive_attributes,
                prediction_column=prediction_column,
                actual_column=actual_column,
                tradition_results=results["tradition_analysis"],
                stakeholder_weights=self.stakeholder_weights,
                domain_context=domain_context
            )
        
        # Generate recommendations based on findings
        results["recommendations"] = self.generate_recommendations(
            results=results,
            dataset=dataset,
            sensitive_attributes=sensitive_attributes,
            domain_context=domain_context
        )
        
        return results
    
    def perform_intersectional_analysis(
        self,
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        prediction_column: str,
        actual_column: str
    ) -> Dict[str, Any]:
        """
        Analyze intersections of sensitive attributes to identify compounded bias
        """
        intersectional_results = {}
        
        # Only perform intersectional analysis if we have multiple attributes
        if len(sensitive_attributes) <= 1:
            return {"status": "insufficient_attributes"}
        
        # Analyze pairs of attributes (can be extended to more combinations)
        for attr1, attr2 in itertools.combinations(sensitive_attributes, 2):
            # Create intersection groups
            intersection_groups = {}
            for idx, row in dataset.iterrows():
                # Create compound key for intersection
                key = f"{attr1}_{row[attr1]}_{attr2}_{row[attr2]}"
                if key not in intersection_groups:
                    intersection_groups[key] = {
                        "count": 0,
                        "correct_predictions": 0,
                        "positive_predictions": 0,
                        "positive_actuals": 0
                    }
                
                group = intersection_groups[key]
                group["count"] += 1
                group["correct_predictions"] += int(row[prediction_column] == row[actual_column])
                group["positive_predictions"] += int(row[prediction_column] == 1)
                group["positive_actuals"] += int(row[actual_column] == 1)
            
            # Calculate metrics for each intersection
            for key, group in intersection_groups.items():
                if group["count"] > 0:
                    group["accuracy"] = group["correct_predictions"] / group["count"]
                    group["selection_rate"] = group["positive_predictions"] / group["count"]
                    group["base_rate"] = group["positive_actuals"] / group["count"]
            
            # Identify largest disparities
            if intersection_groups:
                accuracy_values = [g["accuracy"] for g in intersection_groups.values() if "accuracy" in g]
                selection_values = [g["selection_rate"] for g in intersection_groups.values() if "selection_rate" in g]
                
                if accuracy_values and selection_values:
                    intersectional_results[f"{attr1}_{attr2}"] = {
                        "max_accuracy_disparity": max(accuracy_values) - min(accuracy_values),
                        "max_selection_disparity": max(selection_values) - min(selection_values),
                        "groups": intersection_groups
                    }
        
        return intersectional_results
    
    def generate_recommendations(
        self,
        results: Dict[str, Any],
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        domain_context: str = None
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on analysis findings
        """
        recommendations = {
            "data_collection": [],
            "model_adjustments": [],
            "evaluation_metrics": [],
            "process_changes": [],
            "priority_issues": []
        }
        
        # Example recommendation logic based on statistical parity
        if "western" in results["tradition_analysis"]:
            western_results = results["tradition_analysis"]["western"]
            if "statistical_parity" in western_results:
                for attr in sensitive_attributes:
                    if f"disparity_{attr}" in western_results["statistical_parity"]:
                        disparity = western_results["statistical_parity"][f"disparity_{attr}"]
                        if disparity > 0.2:  # Threshold for recommendations
                            recommendations["model_adjustments"].append(
                                f"Apply fairness constraints to reduce selection rate disparity for {attr}"
                            )
        
        # Example recommendation based on Ubuntu metrics
        if "ubuntu" in results["tradition_analysis"]:
            ubuntu_results = results["tradition_analysis"]["ubuntu"]
            if "group_harmony" in ubuntu_results:
                for attr in sensitive_attributes:
                    if f"harmony_{attr}" in ubuntu_results["group_harmony"]:
                        harmony = ubuntu_results["group_harmony"][f"harmony_{attr}"]
                        if harmony < 0.7:  # Threshold for recommendations
                            recommendations["data_collection"].append(
                                f"Consider community impact when collecting additional {attr} data"
                            )
        
        # Prioritize issues based on stakeholder weights and severity
        priority_issues = []
        for tradition, metrics in results["tradition_analysis"].items():
            weight = self.stakeholder_weights.get(tradition, 1.0)
            for metric_name, metric_results in metrics.items():
                # This is simplified - would be more sophisticated in practice
                for key, value in metric_results.items():
                    if isinstance(value, (int, float)) and "disparity" in key and value > 0.2:
                        priority_issues.append({
                            "tradition": tradition,
                            "metric": metric_name,
                            "issue": key,
                            "severity": value,
                            "weighted_severity": value * weight
                        })
        
        # Sort issues by weighted severity
        if priority_issues:
            sorted_issues = sorted(priority_issues, key=lambda x: x["weighted_severity"], reverse=True)
            recommendations["priority_issues"] = sorted_issues[:5]  # Top 5 issues
        
        # Add domain-specific recommendations
        if domain_context == "healthcare":
            recommendations["process_changes"].append(
                "Ensure medical expertise from diverse backgrounds is incorporated in label validation"
            )
        elif domain_context == "criminal_justice":
            recommendations["evaluation_metrics"].append(
                "Add community impact assessment before deployment"
            )
        
        return recommendations
    
    #
    # Example implementations of metrics (simplified versions)
    #
    
    def calculate_statistical_parity(
        self,
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        prediction_column: str,
        actual_column: str,
        cultural_context: Dict[str, Any] = None,
        historical_context: Dict[str, Any] = None,
        domain_context: str = None
    ) -> Dict[str, Any]:
        """Western metric: statistical parity (equal selection rates)"""
        results = {}
        
        for attribute in sensitive_attributes:
            # Get unique values for this attribute
            attribute_values = dataset[attribute].unique()
            
            # Calculate selection rate for each attribute value
            selection_rates = {}
            for value in attribute_values:
                group_data = dataset[dataset[attribute] == value]
                if len(group_data) > 0:
                    selection_rate = sum(group_data[prediction_column] == 1) / len(group_data)
                    selection_rates[value] = selection_rate
            
            # Calculate disparities between groups
            if len(selection_rates) > 1:
                max_disparity = max(selection_rates.values()) - min(selection_rates.values())
                results[f"disparity_{attribute}"] = max_disparity
                results[f"selection_rates_{attribute}"] = selection_rates
        
        return results
    
    def calculate_group_harmony(
        self,
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        prediction_column: str,
        actual_column: str, 
        cultural_context: Dict[str, Any] = None,
        historical_context: Dict[str, Any] = None,
        domain_context: str = None
    ) -> Dict[str, Any]:
        """Ubuntu metric: group harmony (impact on group relationships)"""
        results = {}
        
        # Cultural context can modify how we calculate harmony
        harmony_threshold = cultural_context.get("harmony_threshold", 0.8) if cultural_context else 0.8
        
        for attribute in sensitive_attributes:
            attribute_values = dataset[attribute].unique()
            
            # Calculate within-group vs between-group impact
            group_impacts = {}
            for value in attribute_values:
                group_data = dataset[dataset[attribute] == value]
                
                # Calculate errors for this group
                group_fp = sum((group_data[prediction_column] == 1) & 
                              (group_data[actual_column] == 0))
                group_fn = sum((group_data[prediction_column] == 0) & 
                              (group_data[actual_column] == 1))
                
                # Consider historical context if available
                historical_bias = 1.0
                if historical_context and attribute in historical_context:
                    if value in historical_context[attribute]:
                        historical_bias = historical_context[attribute][value]
                
                # Calculate impact scores
                if len(group_data) > 0:
                    internal_error = (group_fp + group_fn) / len(group_data) * historical_bias
                    
                    # Impact on other groups
                    other_groups = dataset[dataset[attribute] != value]
                    if len(other_groups) > 0:
                        external_impact = (group_fp + group_fn) / len(other_groups) * historical_bias
                    else:
                        external_impact = 0
                    
                    group_impacts[value] = {
                        "internal_error": internal_error,
                        "external_impact": external_impact,
                        "historical_factor": historical_bias
                    }
            
            # Calculate harmony score
            if len(group_impacts) > 1:
                internal_values = [impact["internal_error"] for impact in group_impacts.values()]
                external_values = [impact["external_impact"] for impact in group_impacts.values()]
                
                internal_disparity = max(internal_values) - min(internal_values)
                external_disparity = max(external_values) - min(external_values)
                
                # Harmony is higher when disparities are lower
                internal_harmony = max(0, 1 - internal_disparity)
                external_harmony = max(0, 1 - external_disparity)
                
                overall_harmony = (internal_harmony + external_harmony) / 2
                results[f"harmony_{attribute}"] = overall_harmony
                results[f"impact_details_{attribute}"] = group_impacts
                
                # Flag if harmony is below threshold
                if overall_harmony < harmony_threshold:
                    results[f"harmony_alert_{attribute}"] = True
        
        return results
    
    def calculate_cultural_inclusion_index(
        self,
        dataset: pd.DataFrame,
        sensitive_attributes: List[str],
        prediction_column: str,
        actual_column: str,
        tradition_results: Dict[str, Dict[str, Any]],
        stakeholder_weights: Dict[str, float],
        domain_context: str = None
    ) -> Dict[str, float]:
        """
        Integrated metric: combines perspectives from multiple ethical traditions
        to assess overall cultural inclusivity of the dataset and model
        """
        inclusion_scores = {}
        
        for attribute in sensitive_attributes:
            # Gather relevant metrics from different traditions
            metrics_to_combine = {}
            
            # Get statistical parity from Western framework
            if "western" in tradition_results and "statistical_parity" in tradition_results["western"]:
                sp_results = tradition_results["western"]["statistical_parity"]
                if f"disparity_{attribute}" in sp_results:
                    # Convert disparity to inclusion (1 - disparity)
                    metrics_to_combine["western_inclusion"] = 1 - sp_results[f"disparity_{attribute}"]
            
            # Get group harmony from Ubuntu framework
            if "ubuntu" in tradition_results and "group_harmony" in tradition_results["ubuntu"]:
                gh_results = tradition_results["ubuntu"]["group_harmony"]
                if f"harmony_{attribute}" in gh_results:
                    metrics_to_combine["ubuntu_inclusion"] = gh_results[f"harmony_{attribute}"]
            
            # Add other traditions' metrics as available
            # [code for additional traditions would go here]
            
            # Calculate weighted inclusion score
            if metrics_to_combine:
                weighted_sum = 0
                total_weight = 0
                
                for tradition, score in metrics_to_combine.items():
                    tradition_name = tradition.split("_")[0]  # Extract tradition name
                    weight = stakeholder_weights.get(tradition_name, 1.0)
                    weighted_sum += score * weight
                    total_weight += weight
                
                if total_weight > 0:
                    inclusion_scores[f"cultural_inclusion_{attribute}"] = weighted_sum / total_weight
        
        # Overall inclusion score across all attributes
        if inclusion_scores:
            inclusion_scores["overall_inclusion"] = sum(
                score for key, score in inclusion_scores.items() if key.startswith("cultural_inclusion_")
            ) / len(sensitive_attributes)
        
        return inclusion_scores

    # Placeholder methods - would be implemented with specific metrics
    def calculate_equal_opportunity(self, *args, **kwargs): 
        """Western metric focused on equal true positive rates"""
        return {"status": "implementation_needed"}
    
    def calculate_disparate_impact(self, *args, **kwargs):
        """Western metric focused on disparate impact ratios"""
        return {"status": "implementation_needed"}
    
    def calculate_communal_benefit(self, *args, **kwargs):
        """Ubuntu metric focused on community-wide benefits"""
        return {"status": "implementation_needed"}
    
    def calculate_relational_impact(self, *args, **kwargs):
        """Ubuntu metric focused on relationships between groups"""
        return {"status": "implementation_needed"}
    
    def calculate_role_appropriateness(self, *args, **kwargs):
        """Confucian metric focused on appropriate role fulfillment"""
        return {"status": "implementation_needed"}
    
    def calculate_social_harmony(self, *args, **kwargs):
        """Confucian metric focused on social harmony"""
        return {"status": "implementation_needed"}
    
    def calculate_hierarchical_fairness(self, *args, **kwargs):
        """Confucian metric examining fairness within social hierarchies"""
        return {"status": "implementation_needed"}
    
    def calculate_equitable_treatment(self, *args, **kwargs):
        """Islamic metric focused on equitable treatment"""
        return {"status": "implementation_needed"}
    
    def calculate_harm_prevention(self, *args, **kwargs):
        """Islamic metric focused on preventing harm"""
        return {"status": "implementation_needed"}
    
    def calculate_dignity_preservation(self, *args, **kwargs):
        """Islamic metric focused on preserving human dignity"""
        return {"status": "implementation_needed"}
    
    def calculate_contextual_fairness(self, *args, **kwargs):
        """Integrated metric considering context in fairness evaluations"""
        return {"status": "implementation_needed"}
    
    def calculate_harmony_equity_balance(self, *args, **kwargs):
        """Integrated metric balancing harmony and equity considerations"""
        return {"status": "implementation_needed"}

# Example usage
if __name__ == "__main__":
    # Initialize framework with cultural contexts
    cultural_contexts = {
        "ubuntu": {
            "harmony_threshold": 0.7,
            "community_values": ["solidarity", "respect", "compassion"]
        },
        "confucian": {
            "relationship_priorities": ["family", "community", "society"]
        }
    }
    
    # Historical context about past discrimination
    historical_context = {
        "race": {
            "Black": 1.5,  # Higher factor due to historical discrimination
            "Hispanic": 1.3,
            "White": 1.0,
            "Asian": 1.1
        },
        "gender": {
            "Female": 1.3,
            "Male": 1.0,
            "Non-binary": 1.2
        }
    }
    
    # Stakeholder weights based on community input
    stakeholder_weights = {
        "western": 1.0,
        "ubuntu": 1.2,  # Community emphasized Ubuntu principles
        "confucian": 0.8,
        "islamic": 1.0
    }
    
    # Initialize framework
    framework = DualEthicsFramework(
        cultural_context=cultural_contexts,
        historical_context=historical_context,
        stakeholder_weights=stakeholder_weights
    )
    
    # Example dataset (would be loaded from file in practice)
    data = {
        "gender": ["Male", "Female", "Male", "Female", "Non-binary"],
        "race": ["White", "Black", "Asian", "Hispanic", "White"],
        "predicted": [1, 0, 1, 0, 1],
        "actual": [1, 1, 1, 0, 0]
    }
    df = pd.DataFrame(data)
    
    # Analyze dataset
    results = framework.analyze_dataset(
        dataset=df,
        sensitive_attributes=["gender", "race"],
        prediction_column="predicted",
        actual_column="actual",
        domain_context="healthcare"
    )
    
    # Print key findings
    print("Analysis Results:")
    if "priority_issues" in results["recommendations"]:
        print("\nTop Issues:")
        for issue in results["recommendations"]["priority_issues"]:
            print(f"- {issue['tradition']} metric '{issue['metric']}': {issue['issue']} (severity: {issue['severity']:.2f})")
    
    print("\nRecommendations:")
    for category, recs in results["recommendations"].items():
        if category != "priority_issues" and recs:
            print(f"\n{category.replace('_', ' ').title()}:")
            for rec in recs:
                print(f"- {rec}")


# Dummy classes for VisualizationGenerator and ReportGenerator
class VisualizationGenerator:
    def __init__(self, results, output_dir):
        self.results = results
        self.output_dir = output_dir

    def generate_all_visualizations(self):
        print(f"Generating visualizations to {self.output_dir}...")
        # Placeholder for actual visualization generation logic
        return {"example_viz.png": os.path.join(self.output_dir, "example_viz.png")}

class ReportGenerator:
    def __init__(self, results, viz_generator):
        self.results = results
        self.viz_generator = viz_generator

    def generate_report(self, output_path):
        print(f"Generating report to {output_path}...")
        # Placeholder for actual report generation logic
        with open(output_path, "w") as f:
            f.write("Ethical Analysis Report\n")
            f.write(f"Results: {self.results}\n")
            f.write(f"Visualizations: {self.viz_generator.generate_all_visualizations()}\n")


# Dummy classes for image analysis to allow the run_full_analysis_with_visualizations to run
class ImageAnalyzer:
    pass

class ImageVisualizationGenerator:
    def __init__(self, results, output_dir):
        self.results = results
        self.output_dir = output_dir

    def generate_all_visualizations(self):
        print(f"Generating image visualizations to {self.output_dir}...")
        return {"example_image_viz.png": os.path.join(self.output_dir, "example_image_viz.png")}

def run_image_analysis_with_visualizations(*args, **kwargs):
    print("Running dummy image analysis...")
    return {"status": "image_analysis_completed", "results": "dummy_image_results"}

def generate_image_analysis_report(*args, **kwargs):
    print("Generating dummy image analysis report...")
    return "dummy_image_report.html"


def run_full_analysis_with_visualizations(
    dataset_path: str,
    sensitive_attributes: List[str] = None,
    prediction_column: str = None,
    actual_column: str = None,
    domain_context: Optional[str] = None, # Added domain_context to signature
    output_dir: str = "ethical_analysis_output",
    dataset_type: str = "tabular",
    image_column: str = None,
    metadata_columns: List[str] = None,
    feature_extraction_method: str = "color_histogram",
    use_pretrained_models: bool = False
):
    """
    Complete function to run full analysis with visualizations and report
    
    Parameters:
    -----------
    dataset_path : str
        Path to dataset file (CSV for tabular data, folder path or CSV with image paths for image data)
    
    sensitive_attributes : List[str]
        List of sensitive attributes to analyze (for tabular data)
    
    prediction_column : str
        Column with predictions (for tabular data)
    
    actual_column : str
        Column with ground truth (for tabular data)
    
    output_dir : str
        Directory to save results
        
    dataset_type : str
        Type of dataset: "tabular" or "image"
    
    image_column : str
        Column in dataset containing image paths (only used for image data)
        
    metadata_columns : List[str]
        Columns to include as metadata (only used for image data)
        
    feature_extraction_method : str
        Method for feature extraction (only used for image data)
        
    use_pretrained_models : bool
        Whether to use pretrained models when available (only used for image data)
        
    Returns:
    --------
    Dict[str, Any]
        Results from analysis including paths to visualizations and reports
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    if dataset_type.lower() == "tabular":
        # Process tabular data
        return run_tabular_analysis(
            dataset_path=dataset_path,
            sensitive_attributes=sensitive_attributes,
            prediction_column=prediction_column,
            actual_column=actual_column,
            domain_context=domain_context, # Pass domain_context
            output_dir=output_dir
        )
    elif dataset_type.lower() == "image":
        # Process image data
        is_dataset = dataset_path.endswith('.csv') or dataset_path.endswith('.json')
        return run_image_analysis(
            image_path=dataset_path,
            output_dir=output_dir,
            is_dataset=is_dataset,
            image_column=image_column,
            metadata_columns=metadata_columns,
            feature_extraction_method=feature_extraction_method,
            use_pretrained_models=use_pretrained_models
        )
    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}. Use 'tabular' or 'image'.")

def run_tabular_analysis(
    dataset_path: str,
    sensitive_attributes: List[str],
    prediction_column: str,
    actual_column: str,
    domain_context: Optional[str] = None, # Added domain_context to signature
    output_dir: str = "ethical_analysis_output"
):
    """
    Run analysis on tabular data
    """
    viz_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # Load dataset
    dataset = pd.read_csv(dataset_path)
    
    # Initialize framework with cultural contexts
    cultural_contexts = {
        "ubuntu": {
            "harmony_threshold": 0.7,
            "community_values": ["solidarity", "respect", "compassion"]
        },
        "confucian": {
            "relationship_priorities": ["family", "community", "society"]
        }
    }
    
    # Historical context about past discrimination
    historical_context = {
        "race": {
            "Black": 1.5,  # Higher factor due to historical discrimination
            "Hispanic": 1.3,
            "White": 1.0,
            "Asian": 1.1
        },
        "gender": {
            "Female": 1.3,
            "Male": 1.0,
            "Non-binary": 1.2
        }
    }
    
    # Initialize framework
    framework = DualEthicsFramework(
        cultural_context=cultural_contexts,
        historical_context=historical_context
    )
    
    # Run analysis
    results = framework.analyze_dataset(
        dataset=dataset,
        sensitive_attributes=sensitive_attributes,
        prediction_column=prediction_column,
        actual_column=actual_column,
        domain_context=domain_context # Pass domain_context to analyze_dataset
    )
    
    # Generate visualizations
    viz_generator = VisualizationGenerator(results, output_dir=viz_dir)
    visualizations = viz_generator.generate_all_visualizations()
    
    # Generate report
    report_generator = ReportGenerator(results, viz_generator)
    report_path = os.path.join(output_dir, "ethical_analysis_report.pdf")
    report_generator.generate_report(report_path)
    
    return {
        "results": results,
        "visualizations": visualizations,
        "report": report_path
    }

def run_image_analysis(
    image_path: str,
    output_dir: str = "image_analysis_output",
    is_dataset: bool = False,
    image_column: str = None,
    metadata_columns: List[str] = None,
    feature_extraction_method: str = "color_histogram",
    use_pretrained_models: bool = False
):
    """
    Run analysis on image data
    
    Parameters:
    -----------
    image_path : str
        Path to directory with images or dataset file with image paths
    
        output_dir : str
        Directory to save results
        
    is_dataset : bool
        Whether image_path points to a dataset file with image paths
        
    image_column : str
        Column in dataset containing image paths (only used if is_dataset=True)
        
    metadata_columns : List[str]
        Columns to include as metadata (only used if is_dataset=True)
        
    feature_extraction_method : str
        Method for feature extraction (color_histogram, hog, deep_features)
        
    use_pretrained_models : bool
        Whether to use pretrained models when available
        
    Returns:
    --------
    Dict[str, Any]
        Results from analysis including paths to visualizations and reports
    """
    # Import required modules only when needed to avoid loading them for tabular analysis
    from image_analyzer import ImageAnalyzer, run_image_analysis_with_visualizations
    from image_visualization import ImageVisualizationGenerator, generate_image_analysis_report
    
    # Create output directories
    viz_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # Define cultural context for image analysis
    cultural_context = {
        "ubuntu": {
            "harmony_threshold": 0.7,
            "community_values": ["solidarity", "respect", "compassion"]
        },
        "confucian": {
            "relationship_priorities": ["family", "community", "society"]
        },
        "islamic": {
            "dignity_threshold": 0.8,
            "core_values": ["justice", "beneficence", "non-maleficence"]
        },
        "western": {
            "fairness_threshold": 0.2,
            "core_values": ["autonomy", "equity", "transparency"]
        }
    }
    
    # Run image analysis
    analysis_results = run_image_analysis_with_visualizations(
        image_dir_or_dataset=image_path,
        is_dataset=is_dataset,
        image_column=image_column,
        metadata_columns=metadata_columns,
        feature_extraction_method=feature_extraction_method,
        use_pretrained_models=use_pretrained_models,
        cultural_context=cultural_context,
        output_dir=output_dir
    )
    
    # Generate visualizations
    viz_generator = ImageVisualizationGenerator(analysis_results, output_dir=viz_dir)
    visualizations = viz_generator.generate_all_visualizations()
    
    # Generate report
    report_path = os.path.join(output_dir, "image_analysis_report.html")
    generate_image_analysis_report(
        analysis_results=analysis_results,
        visualization_paths=visualizations,
        output_path=report_path
    )
    
    return {
        "results": analysis_results,
        "visualizations": visualizations,
        "report": report_path
    }