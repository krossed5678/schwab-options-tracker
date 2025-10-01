import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class IPOTracker:
    """
    IPO tracking functionality to get upcoming and recent IPOs.
    
    This class provides methods to:
    - Fetch upcoming IPO data
    - Get recent IPO performance
    - Filter IPOs by date range and criteria
    """
    
    def __init__(self):
        """Initialize the IPO tracker."""
        self.base_urls = {
            # We'll use multiple sources for IPO data
            'nasdaq': 'https://api.nasdaq.com/api/ipo/calendar',
            'marketwatch': 'https://www.marketwatch.com/tools/ipo-calendar',
            # Add more sources as needed
        }
        
        # Sample IPO data structure for demonstration
        # In production, you'd integrate with real IPO APIs
        self._sample_ipos = [
            {
                'symbol': 'EXAMPLE1',
                'company_name': 'Example Tech Corp',
                'exchange': 'NASDAQ',
                'shares_offered': '10,000,000',
                'price_range': '$15.00 - $18.00',
                'expected_date': '2025-10-15',
                'status': 'Filed',
                'sector': 'Technology',
                'market_cap_est': '$500M - $600M',
                'underwriters': 'Goldman Sachs, Morgan Stanley',
                'description': 'AI-powered software solutions company'
            },
            {
                'symbol': 'BIOTECH2',
                'company_name': 'BioInnovate Labs',
                'exchange': 'NYSE',
                'shares_offered': '5,000,000',
                'price_range': '$22.00 - $25.00',
                'expected_date': '2025-10-22',
                'status': 'Priced',
                'sector': 'Biotechnology',
                'market_cap_est': '$1.1B - $1.25B',
                'underwriters': 'JPMorgan, Citigroup',
                'description': 'Gene therapy and precision medicine'
            },
            {
                'symbol': 'FINTECH3',
                'company_name': 'PayNext Solutions',
                'exchange': 'NASDAQ',
                'shares_offered': '8,000,000',
                'price_range': '$12.00 - $15.00',
                'expected_date': '2025-11-05',
                'status': 'Filed',
                'sector': 'Financial Technology',
                'market_cap_est': '$400M - $500M',
                'underwriters': 'Credit Suisse, Barclays',
                'description': 'Digital payment processing platform'
            },
            {
                'symbol': 'ENERGY4',
                'company_name': 'GreenPower Dynamics',
                'exchange': 'NYSE',
                'shares_offered': '12,000,000',
                'price_range': '$18.00 - $21.00',
                'expected_date': '2025-11-12',
                'status': 'Withdrawn',
                'sector': 'Clean Energy',
                'market_cap_est': '$800M - $950M',
                'underwriters': 'Bank of America, Wells Fargo',
                'description': 'Renewable energy storage solutions'
            },
            {
                'symbol': 'RETAIL5',
                'company_name': 'EcoStyle Fashion',
                'exchange': 'NASDAQ',
                'shares_offered': '6,000,000',
                'price_range': '$20.00 - $24.00',
                'expected_date': '2025-11-20',
                'status': 'Filed',
                'sector': 'Consumer Retail',
                'market_cap_est': '$600M - $720M',
                'underwriters': 'Deutsche Bank, UBS',
                'description': 'Sustainable fashion and apparel'
            }
        ]
    
    def get_upcoming_ipos(self, days_ahead: int = 90) -> pd.DataFrame:
        """
        Get upcoming IPOs within the specified time range.
        
        Args:
            days_ahead: Number of days ahead to look for IPOs
            
        Returns:
            DataFrame with upcoming IPO information
        """
        try:
            # In production, this would call real IPO APIs
            # For demo purposes, we'll use sample data
            
            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)
            
            # Filter sample IPOs by date range
            upcoming_ipos = []
            for ipo in self._sample_ipos:
                ipo_date = datetime.strptime(ipo['expected_date'], '%Y-%m-%d')
                if today <= ipo_date <= end_date:
                    # Calculate days until IPO
                    days_until = (ipo_date - today).days
                    ipo_copy = ipo.copy()
                    ipo_copy['days_until_ipo'] = days_until
                    upcoming_ipos.append(ipo_copy)
            
            df = pd.DataFrame(upcoming_ipos)
            
            if not df.empty:
                # Sort by expected date
                df['expected_date'] = pd.to_datetime(df['expected_date'])
                df = df.sort_values('expected_date').reset_index(drop=True)
                
                # Add additional calculated fields
                df = self._enhance_ipo_data(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching upcoming IPOs: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_ipos(self, days_back: int = 30) -> pd.DataFrame:
        """
        Get recent IPOs and their performance.
        
        Args:
            days_back: Number of days back to look for recent IPOs
            
        Returns:
            DataFrame with recent IPO information and performance
        """
        try:
            # Sample recent IPOs with performance data
            recent_ipos_data = [
                {
                    'symbol': 'RECENTIPO1',
                    'company_name': 'TechStart Innovations',
                    'ipo_date': '2025-09-15',
                    'ipo_price': 16.00,
                    'current_price': 24.50,
                    'first_day_close': 22.00,
                    'current_return': 53.1,
                    'first_day_return': 37.5,
                    'volume_today': 2500000,
                    'sector': 'Technology',
                    'exchange': 'NASDAQ',
                    'market_cap_current': '850M'
                },
                {
                    'symbol': 'NEWBIO2',
                    'company_name': 'MedAdvance Therapeutics',
                    'ipo_date': '2025-09-22',
                    'ipo_price': 20.00,
                    'current_price': 18.75,
                    'first_day_close': 19.50,
                    'current_return': -6.25,
                    'first_day_return': -2.5,
                    'volume_today': 1200000,
                    'sector': 'Biotechnology',
                    'exchange': 'NYSE',
                    'market_cap_current': '750M'
                },
                {
                    'symbol': 'CLEANTECH3',
                    'company_name': 'SolarMax Energy',
                    'ipo_date': '2025-09-28',
                    'ipo_price': 14.00,
                    'current_price': 17.25,
                    'first_day_close': 15.80,
                    'current_return': 23.2,
                    'first_day_return': 12.9,
                    'volume_today': 1800000,
                    'sector': 'Clean Energy',
                    'exchange': 'NASDAQ',
                    'market_cap_current': '690M'
                }
            ]
            
            today = datetime.now()
            start_date = today - timedelta(days=days_back)
            
            # Filter by date range
            filtered_ipos = []
            for ipo in recent_ipos_data:
                ipo_date = datetime.strptime(ipo['ipo_date'], '%Y-%m-%d')
                if start_date <= ipo_date <= today:
                    days_since_ipo = (today - ipo_date).days
                    ipo_copy = ipo.copy()
                    ipo_copy['days_since_ipo'] = days_since_ipo
                    filtered_ipos.append(ipo_copy)
            
            df = pd.DataFrame(filtered_ipos)
            
            if not df.empty:
                # Sort by IPO date (most recent first)
                df['ipo_date'] = pd.to_datetime(df['ipo_date'])
                df = df.sort_values('ipo_date', ascending=False).reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching recent IPOs: {str(e)}")
            return pd.DataFrame()
    
    def get_ipo_calendar(self, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get IPO calendar for a specific date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with IPO calendar information
        """
        try:
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Combine upcoming and recent IPOs
            upcoming_df = self.get_upcoming_ipos(days_ahead=365)
            recent_df = self.get_recent_ipos(days_back=90)
            
            # Standardize columns for combination
            if not upcoming_df.empty:
                upcoming_df['type'] = 'Upcoming'
            if not recent_df.empty:
                recent_df['type'] = 'Recent'
                # Rename ipo_date to expected_date for consistency
                recent_df = recent_df.rename(columns={'ipo_date': 'expected_date'})
            
            # Combine dataframes
            if not upcoming_df.empty and not recent_df.empty:
                # Find common columns
                common_cols = list(set(upcoming_df.columns) & set(recent_df.columns))
                combined_df = pd.concat([
                    upcoming_df[common_cols],
                    recent_df[common_cols]
                ], ignore_index=True)
            elif not upcoming_df.empty:
                combined_df = upcoming_df
            elif not recent_df.empty:
                combined_df = recent_df
            else:
                combined_df = pd.DataFrame()
            
            if not combined_df.empty:
                # Filter by date range
                combined_df['expected_date'] = pd.to_datetime(combined_df['expected_date'])
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                
                combined_df = combined_df[
                    (combined_df['expected_date'] >= start_dt) & 
                    (combined_df['expected_date'] <= end_dt)
                ].sort_values('expected_date').reset_index(drop=True)
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error fetching IPO calendar: {str(e)}")
            return pd.DataFrame()
    
    def _enhance_ipo_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated fields to IPO data."""
        if df.empty:
            return df
        
        try:
            # Parse price ranges and calculate midpoint estimates
            df['price_midpoint'] = df['price_range'].apply(self._extract_price_midpoint)
            
            # Parse share counts
            df['shares_numeric'] = df['shares_offered'].apply(self._parse_share_count)
            
            # Calculate estimated raise amount
            df['estimated_raise'] = df['price_midpoint'] * df['shares_numeric']
            df['estimated_raise_formatted'] = df['estimated_raise'].apply(self._format_currency_millions)
            
            # Add investment appeal score (simple scoring based on various factors)
            df['appeal_score'] = self._calculate_appeal_score(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error enhancing IPO data: {str(e)}")
            return df
    
    def _extract_price_midpoint(self, price_range: str) -> float:
        """Extract midpoint from price range string."""
        try:
            # Parse "$15.00 - $18.00" format
            prices = price_range.replace('$', '').split(' - ')
            if len(prices) == 2:
                low = float(prices[0])
                high = float(prices[1])
                return (low + high) / 2
            return 0.0
        except:
            return 0.0
    
    def _parse_share_count(self, shares_str: str) -> int:
        """Parse share count from string."""
        try:
            # Handle formats like "10,000,000"
            return int(shares_str.replace(',', ''))
        except:
            return 0
    
    def _format_currency_millions(self, amount: float) -> str:
        """Format currency amount in millions."""
        if amount >= 1_000_000_000:
            return f"${amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        else:
            return f"${amount / 1_000:.1f}K"
    
    def _calculate_appeal_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate a simple investment appeal score."""
        try:
            scores = []
            for _, row in df.iterrows():
                score = 50  # Base score
                
                # Sector bonuses
                if row['sector'] in ['Technology', 'Biotechnology', 'Financial Technology']:
                    score += 15
                elif row['sector'] in ['Clean Energy', 'Healthcare']:
                    score += 10
                
                # Status bonuses
                if row['status'] == 'Priced':
                    score += 10
                elif row['status'] == 'Filed':
                    score += 5
                
                # Size bonus (larger raises often indicate more established companies)
                if hasattr(row, 'estimated_raise') and row['estimated_raise'] > 500_000_000:
                    score += 10
                elif hasattr(row, 'estimated_raise') and row['estimated_raise'] > 100_000_000:
                    score += 5
                
                scores.append(min(100, max(0, score)))  # Cap between 0-100
            
            return pd.Series(scores)
            
        except Exception as e:
            logger.error(f"Error calculating appeal scores: {str(e)}")
            return pd.Series([50] * len(df))  # Return neutral scores on error
    
    def get_ipo_statistics(self) -> Dict[str, Any]:
        """Get summary statistics about IPO market."""
        try:
            upcoming_df = self.get_upcoming_ipos(days_ahead=365)
            recent_df = self.get_recent_ipos(days_back=90)
            
            stats = {
                'upcoming_count': len(upcoming_df),
                'recent_count': len(recent_df),
                'upcoming_sectors': upcoming_df['sector'].value_counts().to_dict() if not upcoming_df.empty else {},
                'recent_performance': {
                    'avg_return': recent_df['current_return'].mean() if not recent_df.empty else 0,
                    'positive_returns': len(recent_df[recent_df['current_return'] > 0]) if not recent_df.empty else 0,
                    'negative_returns': len(recent_df[recent_df['current_return'] < 0]) if not recent_df.empty else 0
                },
                'hot_sectors': self._identify_hot_sectors(upcoming_df, recent_df),
                'market_sentiment': self._assess_market_sentiment(recent_df)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating IPO statistics: {str(e)}")
            return {}
    
    def _identify_hot_sectors(self, upcoming_df: pd.DataFrame, recent_df: pd.DataFrame) -> List[str]:
        """Identify sectors with high IPO activity."""
        try:
            all_sectors = []
            if not upcoming_df.empty:
                all_sectors.extend(upcoming_df['sector'].tolist())
            if not recent_df.empty:
                all_sectors.extend(recent_df['sector'].tolist())
            
            if all_sectors:
                sector_counts = pd.Series(all_sectors).value_counts()
                return sector_counts.head(3).index.tolist()
            return []
            
        except:
            return []
    
    def _assess_market_sentiment(self, recent_df: pd.DataFrame) -> str:
        """Assess overall IPO market sentiment."""
        try:
            if recent_df.empty:
                return "Neutral"
            
            avg_return = recent_df['current_return'].mean()
            positive_ratio = len(recent_df[recent_df['current_return'] > 0]) / len(recent_df)
            
            if avg_return > 15 and positive_ratio > 0.7:
                return "Very Bullish"
            elif avg_return > 5 and positive_ratio > 0.6:
                return "Bullish"
            elif avg_return > -5 and positive_ratio > 0.4:
                return "Neutral"
            elif avg_return > -15 and positive_ratio > 0.3:
                return "Bearish"
            else:
                return "Very Bearish"
                
        except:
            return "Neutral"
