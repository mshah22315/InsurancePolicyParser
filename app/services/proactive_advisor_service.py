"""
Proactive Advisor Service for Insurance Policy Analysis

This service analyzes insurance policies to identify risks and opportunities
for proactive recommendations and alerts.
"""

from datetime import date
from typing import List, Dict, Any
from app.models import ProcessedPolicyData
import logging

logger = logging.getLogger(__name__)

class ProactiveAdvisorService:
    """
    Service for proactive analysis of insurance policies.
    
    Analyzes policy data to identify risks, opportunities, and recommendations
    for policyholders and agents.
    """
    
    def __init__(self, policy_data: ProcessedPolicyData):
        """
        Initialize the service with policy data.
        
        Args:
            policy_data: The ProcessedPolicyData object to analyze
        """
        self.policy = policy_data
        self.insights = []
        
    def analyze_for_risks_and_opportunities(self) -> List[Dict[str, Any]]:
        """
        Perform comprehensive analysis of the policy for risks and opportunities.
        
        Returns:
            List of insight dictionaries with analysis results
        """
        logger.info(f"Starting proactive analysis for policy {self.policy.policy_number}")
        
        # Clear previous insights
        self.insights = []
        
        # Run all analysis methods
        self._check_aging_roof_risk()
        self._find_missing_discounts()
        self._check_renewal_timing()
        self._analyze_coverage_gaps()
        self._check_deductible_optimization()
        
        logger.info(f"Analysis complete. Found {len(self.insights)} insights")
        return self.insights
    
    def _check_aging_roof_risk(self):
        """
        Check for aging roof risk (Scenario 1).
        
        Identifies policies with roofs over 15 years old that may need
        replacement and could affect coverage or premiums.
        """
        if self.policy.roof_age_years is None:
            return
        
        if self.policy.roof_age_years > 15:
            insight = {
                'type': 'risk',
                'title': 'Aging Roof Risk',
                'finding': f"Roof is {self.policy.roof_age_years} years old, which exceeds the recommended 15-year threshold.",
                'action': 'Consider roof replacement to maintain coverage and potentially reduce premiums. Contact a roofing contractor for inspection.',
                'priority': 'high',
                'category': 'property_maintenance',
                'estimated_impact': 'High - May affect coverage and increase premiums'
            }
            self.insights.append(insight)
            logger.info(f"Added aging roof risk insight for {self.policy.policy_number}")
    
    def _find_missing_discounts(self):
        """
        Find missing discounts based on property features (Scenario 2).
        
        Analyzes property features to identify potential discounts
        that could be applied to reduce premiums.
        """
        if not self.policy.property_features:
            return
        
        available_features = set(self.policy.property_features)
        potential_discounts = []
        
        # Define discount opportunities based on features
        discount_opportunities = {
            'monitored_alarm': {
                'title': 'Monitored Alarm System Discount',
                'description': 'Security system discount available',
                'potential_savings': '5-10%'
            },
            'sprinkler_system': {
                'title': 'Fire Sprinkler System Discount',
                'description': 'Fire suppression system discount available',
                'potential_savings': '10-15%'
            },
            'impact_resistant_roof': {
                'title': 'Impact Resistant Roof Discount',
                'description': 'Wind-resistant roofing materials discount',
                'potential_savings': '5-8%'
            },
            'new_construction': {
                'title': 'New Construction Discount',
                'description': 'Recently built property discount',
                'potential_savings': '3-7%'
            }
        }
        
        # Check for features that could qualify for discounts
        for feature, discount_info in discount_opportunities.items():
            if feature in available_features:
                potential_discounts.append(discount_info)
        
        if potential_discounts:
            insight = {
                'type': 'opportunity',
                'title': 'Available Discounts',
                'finding': f"Property has {len(potential_discounts)} features that may qualify for discounts.",
                'action': f"Review and apply available discounts: {', '.join([d['title'] for d in potential_discounts])}",
                'priority': 'medium',
                'category': 'cost_optimization',
                'estimated_impact': f"Potential savings: {', '.join([d['potential_savings'] for d in potential_discounts])}",
                'details': potential_discounts
            }
            self.insights.append(insight)
            logger.info(f"Added discount opportunity insight for {self.policy.policy_number}")
    
    def _check_renewal_timing(self):
        """
        Check renewal timing and provide early renewal recommendations.
        """
        if not self.policy.renewal_date:
            return
        
        days_until_renewal = (self.policy.renewal_date - date.today()).days
        
        if days_until_renewal <= 30:
            insight = {
                'type': 'alert',
                'title': 'Renewal Due Soon',
                'finding': f"Policy renewal is due in {days_until_renewal} days.",
                'action': 'Review policy terms and consider any changes needed before renewal.',
                'priority': 'high' if days_until_renewal <= 7 else 'medium',
                'category': 'timing',
                'estimated_impact': 'Critical - Policy may lapse if not renewed'
            }
            self.insights.append(insight)
            logger.info(f"Added renewal timing alert for {self.policy.policy_number}")
    
    def _analyze_coverage_gaps(self):
        """
        Analyze coverage details for potential gaps or insufficient limits.
        """
        if not self.policy.coverage_details:
            return
        
        coverage_gaps = []
        
        # Check for common coverage gaps
        coverage_types = [coverage.get('coverage_type', '').lower() for coverage in self.policy.coverage_details]
        
        # Check for missing liability coverage
        if not any('liability' in coverage_type for coverage_type in coverage_types):
            coverage_gaps.append({
                'type': 'missing_coverage',
                'title': 'Personal Liability Coverage',
                'description': 'No personal liability coverage found',
                'recommendation': 'Consider adding personal liability coverage for protection against lawsuits'
            })
        
        # Check for low dwelling coverage limits
        for coverage in self.policy.coverage_details:
            coverage_type = coverage.get('coverage_type', '').lower()
            limit = coverage.get('limit', 0)
            
            if 'dwelling' in coverage_type and limit:
                try:
                    limit_value = float(limit)
                    if limit_value < 200000:  # Less than $200K
                        coverage_gaps.append({
                            'type': 'low_limit',
                            'title': 'Low Dwelling Coverage',
                            'description': f"Dwelling coverage limit is ${limit_value:,.0f}",
                            'recommendation': 'Consider increasing dwelling coverage to match replacement cost'
                        })
                except (ValueError, TypeError):
                    pass
        
        if coverage_gaps:
            insight = {
                'type': 'risk',
                'title': 'Coverage Gaps Identified',
                'finding': f"Found {len(coverage_gaps)} potential coverage gaps or insufficient limits.",
                'action': 'Review coverage limits and consider additional coverage options.',
                'priority': 'medium',
                'category': 'coverage_analysis',
                'estimated_impact': 'Medium - May leave policyholder underinsured',
                'details': coverage_gaps
            }
            self.insights.append(insight)
            logger.info(f"Added coverage gap insight for {self.policy.policy_number}")
    
    def _check_deductible_optimization(self):
        """
        Analyze deductibles for optimization opportunities.
        """
        if not self.policy.deductibles:
            return
        
        deductible_analysis = []
        
        for deductible in self.policy.deductibles:
            coverage_type = deductible.get('coverage_type', '')
            amount = deductible.get('amount', 0)
            deductible_type = deductible.get('type', '')
            
            try:
                amount_value = float(amount)
                
                # Check for very high deductibles
                if amount_value > 5000:
                    deductible_analysis.append({
                        'type': 'high_deductible',
                        'title': f'High {coverage_type} Deductible',
                        'description': f"Deductible is ${amount_value:,.0f}",
                        'recommendation': 'Consider if this deductible is appropriate for your financial situation'
                    })
                
                # Check for very low deductibles (opportunity to save)
                elif amount_value < 1000:
                    deductible_analysis.append({
                        'type': 'low_deductible',
                        'title': f'Low {coverage_type} Deductible',
                        'description': f"Deductible is ${amount_value:,.0f}",
                        'recommendation': 'Consider increasing deductible to reduce premium costs'
                    })
                    
            except (ValueError, TypeError):
                pass
        
        if deductible_analysis:
            insight = {
                'type': 'opportunity',
                'title': 'Deductible Optimization',
                'finding': f"Found {len(deductible_analysis)} deductible optimization opportunities.",
                'action': 'Review deductible levels and consider adjustments based on risk tolerance and budget.',
                'priority': 'medium',
                'category': 'cost_optimization',
                'estimated_impact': 'Medium - Potential premium savings or better coverage',
                'details': deductible_analysis
            }
            self.insights.append(insight)
            logger.info(f"Added deductible optimization insight for {self.policy.policy_number}")
    
    def get_insights_by_priority(self, priority: str = None) -> List[Dict[str, Any]]:
        """
        Get insights filtered by priority level.
        
        Args:
            priority: Filter by priority ('high', 'medium', 'low')
            
        Returns:
            Filtered list of insights
        """
        if priority:
            return [insight for insight in self.insights if insight.get('priority') == priority]
        return self.insights
    
    def get_insights_by_type(self, insight_type: str = None) -> List[Dict[str, Any]]:
        """
        Get insights filtered by type.
        
        Args:
            insight_type: Filter by type ('risk', 'opportunity', 'alert')
            
        Returns:
            Filtered list of insights
        """
        if insight_type:
            return [insight for insight in self.insights if insight.get('type') == insight_type]
        return self.insights 