from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
import json

logger = get_task_logger(__name__)

FLIGHT_LIST_CACHE_KEY = "flights:list:all"
FLIGHT_DETAIL_CACHE_KEY = "flights:detail:{flight_id}"
CACHE_TTL = 60 * 15  # 15 minutes


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def warm_flight_list_cache(self):
    """Rebuild flight list cache after create/update"""
    from flights.models import Flight
    from flights.serializers import FlightReadSerializer

    queryset = Flight.objects.filter(is_deleted=False).select_related(
        "airline", "route__origin", "route__destination", "aircraft"
    ).prefetch_related("fare_rules").order_by("-id")

    data = FlightReadSerializer(queryset, many=True).data
    cache.set(FLIGHT_LIST_CACHE_KEY, json.dumps(data, cls=DjangoJSONEncoder), CACHE_TTL)

    logger.info("warm_flight_list_cache: cached %d flights", len(data))
    return {"cached_flights": len(data)}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def warm_flight_detail_cache(self, flight_id):
    """Rebuild single flight detail cache after update"""
    from flights.models import Flight
    from flights.serializers import FlightReadSerializer

    try:
        flight = Flight.objects.select_related(
            "airline", "route__origin", "route__destination", "aircraft"
        ).prefetch_related("fare_rules").get(id=flight_id, is_deleted=False)

        data = FlightReadSerializer(flight).data
        cache_key = FLIGHT_DETAIL_CACHE_KEY.format(flight_id=flight_id)
        cache.set(cache_key, json.dumps(data, cls=DjangoJSONEncoder), CACHE_TTL)

        logger.info("warm_flight_detail_cache: cached flight_id=%s", flight_id)
        return {"cached_flight_id": flight_id}

    except Flight.DoesNotExist:
        logger.warning("warm_flight_detail_cache: flight_id=%s not found", flight_id)
        return {"error": "not_found", "flight_id": flight_id}


@shared_task(bind=True)
def invalidate_flight_cache(self, flight_id=None):
    """Clear cache on delete or status change"""
    cache.delete(FLIGHT_LIST_CACHE_KEY)

    if flight_id:
        cache_key = FLIGHT_DETAIL_CACHE_KEY.format(flight_id=flight_id)
        cache.delete(cache_key)

    logger.info("invalidate_flight_cache: cleared for flight_id=%s", flight_id)
    return {"invalidated": True, "flight_id": flight_id}


# --- Existing tasks (keep as-is) ---
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_flight_cache(self, flight_id):
    logger.info("refresh_flight_cache for flight_id=%s", flight_id)
    warm_flight_detail_cache.delay(flight_id)
    warm_flight_list_cache.delay()
    return {"flight_id": flight_id, "status": "refresh_queued"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_flight_fare_rules(self, flight_id):
    logger.info("refresh_flight_fare_rules for flight_id=%s", flight_id)
    return {"flight_id": flight_id, "status": "fare_rules_refreshed"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def create_flight_audit_log(self, flight_id, event_name, meta=None):
    logger.info(
        "create_flight_audit_log flight_id=%s event_name=%s meta=%s",
        flight_id, event_name, meta or {},
    )
    return {"flight_id": flight_id, "event_name": event_name}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def bulk_refresh_flights(self, flight_ids):
    logger.info("bulk_refresh_flights for flight_ids=%s", flight_ids)
    warm_flight_list_cache.delay()
    for flight_id in flight_ids:
        warm_flight_detail_cache.delay(flight_id)
    return {"flight_ids": flight_ids, "status": "bulk_refreshed"}