@router.post("/collect/auto")
def auto_collect_reels(
    hashtags: str = "viral,trending,reels,funny",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Автоматический сбор Reels через API"""
    from app.collectors.auto_collector import AutoReelsCollector

    try:
        collector = AutoReelsCollector()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    hashtag_list = [h.strip() for h in hashtags.split(",")]

    reels_data = collector.collect_trending(
        hashtags=hashtag_list,
        limit=limit
    )

    service = ReelsService(db)
    saved = 0

    for reel_data in reels_data:
        try:
            service.create_or_update_reel(reel_data)
            saved += 1
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")

    db.commit()

    return {
        "status": "success",
        "collected": len(reels_data),
        "saved": saved,
        "hashtags": hashtag_list
    }