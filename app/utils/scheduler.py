from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.news_fetcher import news_fetcher

scheduler = AsyncIOScheduler()

async def scheduled_news_fetch():
    """Scheduled task to fetch news"""
    print("Running scheduled news fetch...")
    await news_fetcher.fetch_and_store_all_categories()
    await news_fetcher.cleanup_old_articles()

def start_scheduler():
    """Start the background scheduler"""
    # Fetch news every 6 hours
    scheduler.add_job(scheduled_news_fetch, 'interval', hours=6, id='fetch_news')
    
    # Cleanup old articles daily
    scheduler.add_job(news_fetcher.cleanup_old_articles, 'interval', days=1, id='cleanup_articles')
    
    scheduler.start()
    print("Scheduler started")

def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")