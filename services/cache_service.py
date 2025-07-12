"""
Cache service for AI analysis results to prevent redundant processing
"""

import json
import hashlib
import os
from datetime import datetime, timedelta

class AnalysisCache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, resume_text, job_id):
        """Generate cache key from resume content and job ID"""
        content = f"{resume_text}_{job_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key):
        """Get file path for cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get_cached_analysis(self, resume_text, job_id, max_age_hours=24):
        """
        Get cached analysis if available and not expired
        Returns None if cache miss or expired
        """
        try:
            cache_key = self._get_cache_key(resume_text, job_id)
            cache_path = self._get_cache_path(cache_key)
            
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=max_age_hours):
                # Cache expired, remove file
                os.remove(cache_path)
                return None
            
            return cached_data['analysis']
            
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    def cache_analysis(self, resume_text, job_id, analysis_result):
        """Cache analysis result"""
        try:
            cache_key = self._get_cache_key(resume_text, job_id)
            cache_path = self._get_cache_path(cache_key)
            
            cached_data = {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis_result,
                'job_id': job_id,
                'cache_key': cache_key
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Cache write error: {e}")
            return False
    
    def clear_cache(self, older_than_hours=24):
        """Clear cache files older than specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            cleared_count = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                        
                        cached_time = datetime.fromisoformat(cached_data['timestamp'])
                        if cached_time < cutoff_time:
                            os.remove(filepath)
                            cleared_count += 1
                            
                    except Exception:
                        # If file is corrupted, remove it
                        os.remove(filepath)
                        cleared_count += 1
            
            return cleared_count
            
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_size = 0
            
            for filename in cache_files:
                filepath = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(filepath)
            
            return {
                'total_files': len(cache_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': self.cache_dir
            }
            
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {'total_files': 0, 'total_size_mb': 0, 'cache_dir': self.cache_dir}

# Global cache instance
analysis_cache = AnalysisCache()