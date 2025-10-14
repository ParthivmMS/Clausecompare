# services/database.py
from supabase import create_client, Client
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserService:
    """Handle all user database operations"""
    
    @staticmethod
    async def create_user(email: str, password_hash: str) -> Dict[str, Any]:
        """Create a new user"""
        try:
            result = supabase.table("users").insert({
                "email": email,
                "password_hash": password_hash,
                "plan": "free",
                "comparisons_limit": 10,
                "comparisons_used": 0,
                "reset_date": (datetime.now() + timedelta(days=30)).date().isoformat()
            }).execute()
            
            if result.data:
                return result.data[0]
            raise Exception("Failed to create user")
        except Exception as e:
            print(f"Create user error: {e}")
            raise
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            result = supabase.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = supabase.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Get user by ID error: {e}")
            return None
    
    @staticmethod
    async def get_usage(user_id: str) -> Dict[str, Any]:
        """Get user's comparison usage"""
        try:
            result = supabase.table("users").select(
                "comparisons_used, comparisons_limit, plan, reset_date"
            ).eq("id", user_id).execute()
            
            if result.data:
                user = result.data[0]
                
                # Check if reset is needed
                reset_date = datetime.fromisoformat(user["reset_date"]).date()
                if reset_date < datetime.now().date():
                    # Auto-reset usage
                    await UserService.reset_monthly_usage(user_id)
                    return {
                        "used": 0,
                        "limit": user["comparisons_limit"],
                        "remaining": user["comparisons_limit"],
                        "plan": user["plan"]
                    }
                
                return {
                    "used": user["comparisons_used"],
                    "limit": user["comparisons_limit"],
                    "remaining": user["comparisons_limit"] - user["comparisons_used"],
                    "plan": user["plan"],
                    "resets_on": user["reset_date"]
                }
            
            raise Exception("User not found")
        except Exception as e:
            print(f"Get usage error: {e}")
            raise
    
    @staticmethod
    async def increment_usage(user_id: str) -> Dict[str, Any]:
        """Increment user's comparison count"""
        try:
            # Get current usage
            usage = await UserService.get_usage(user_id)
            
            # Increment
            new_count = usage["used"] + 1
            
            result = supabase.table("users").update({
                "comparisons_used": new_count
            }).eq("id", user_id).execute()
            
            if result.data:
                return await UserService.get_usage(user_id)
            
            raise Exception("Failed to increment usage")
        except Exception as e:
            print(f"Increment usage error: {e}")
            raise
    
    @staticmethod
    async def reset_monthly_usage(user_id: str):
        """Reset monthly usage (called automatically on first request after reset date)"""
        try:
            supabase.table("users").update({
                "comparisons_used": 0,
                "reset_date": (datetime.now() + timedelta(days=30)).date().isoformat()
            }).eq("id", user_id).execute()
        except Exception as e:
            print(f"Reset usage error: {e}")
            raise
    
    @staticmethod
    async def upgrade_to_pro(
        user_id: str, 
        stripe_customer_id: str, 
        stripe_subscription_id: str
    ) -> Dict[str, Any]:
        """Upgrade user to Pro plan"""
        try:
            result = supabase.table("users").update({
                "plan": "pro",
                "comparisons_limit": 999999,  # Effectively unlimited
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "upgraded_at": datetime.now().isoformat()
            }).eq("id", user_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Upgrade error: {e}")
            raise
    
    @staticmethod
    async def downgrade_to_free(stripe_customer_id: str) -> Dict[str, Any]:
        """Downgrade user to free plan"""
        try:
            result = supabase.table("users").update({
                "plan": "free",
                "comparisons_limit": 10,
                "stripe_subscription_id": None,
                "downgraded_at": datetime.now().isoformat()
            }).eq("stripe_customer_id", stripe_customer_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Downgrade error: {e}")
            raise


class ReportService:
    """Handle all report database operations"""
    
    @staticmethod
    async def save_report(user_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a comparison report"""
        try:
            result = supabase.table("reports").insert({
                "user_id": user_id,
                "report_id": report_data["reportId"],
                "file_a_name": report_data["metadata"]["fileA"],
                "file_b_name": report_data["metadata"]["fileB"],
                "risk_score": report_data["riskScore"],
                "summary": report_data["summary"],
                "verdict": report_data.get("verdict", ""),
                "risk_report": report_data.get("riskReport", ""),
                "diffs": report_data["diffs"],
                "metadata": report_data["metadata"]
            }).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Save report error: {e}")
            raise
    
    @staticmethod
    async def get_user_reports(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's report history"""
        try:
            result = supabase.table("reports").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Get reports error: {e}")
            return []
    
    @staticmethod
    async def get_report_by_id(report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific report by ID"""
        try:
            result = supabase.table("reports").select("*").eq(
                "report_id", report_id
            ).eq("user_id", user_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Get report by ID error: {e}")
            return None
    
    @staticmethod
    async def delete_report(report_id: str, user_id: str) -> bool:
        """Delete a report"""
        try:
            result = supabase.table("reports").delete().eq(
                "report_id", report_id
            ).eq("user_id", user_id).execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"Delete report error: {e}")
            return False


class FeedbackService:
    """Handle feedback operations"""
    
    @staticmethod
    async def save_feedback(
        report_id: str,
        user_id: str,
        overall_rating: int,
        accuracy_rating: int,
        comments: str
    ) -> Dict[str, Any]:
        """Save user feedback"""
        try:
            # Get report UUID from report_id
            report = await ReportService.get_report_by_id(report_id, user_id)
            if not report:
                raise Exception("Report not found")
            
            result = supabase.table("feedback").insert({
                "report_id": report["id"],
                "user_id": user_id,
                "overall_rating": overall_rating,
                "accuracy_rating": accuracy_rating,
                "comments": comments
            }).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Save feedback error: {e}")
            raise


# Export services
__all__ = ['UserService', 'ReportService', 'FeedbackService', 'supabase']
