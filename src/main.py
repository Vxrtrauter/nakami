from flask import Flask, jsonify, request
from scrapers.rutracker import scrape_rutracker
from core.models import SearchResponse, Post
import time
import threading

app = Flask(__name__)

debug = False
port = 8080
cache = {}
cache_lock = threading.Lock()
pending_locks = {}  # Per-search-term locks to prevent duplicate fetches



@app.route('/search')
def search():
    search_term = request.args.get("q", "")

    if not search_term:
        err = SearchResponse(success=False, query="", data=[], count=0)
        return jsonify(err.to_dict()), 400

    current_time = time.time()
    
    with cache_lock:
        expired_keys = [key for key, (response, timestamp) in cache.items() if current_time - timestamp >= 300]
        for key in expired_keys:
            del cache[key]
            if key in pending_locks:
                del pending_locks[key]
        
        if search_term in cache:
            response_dict, timestamp = cache[search_term]
            result = response_dict.copy()
            result["cached"] = True
            return jsonify(result), 200
        
        if search_term not in pending_locks:
            pending_locks[search_term] = threading.Lock()
        term_lock = pending_locks[search_term]
    
    with term_lock:
        with cache_lock:
            if search_term in cache:
                response_dict, timestamp = cache[search_term]
                result = response_dict.copy()
                result["cached"] = True
                return jsonify(result), 200
        
        try:
            response = scrape_rutracker(search_term)
            response_dict = response.to_dict()
            with cache_lock:
                cache[search_term] = (response_dict, time.time())
            return jsonify(response_dict), 200
        except RuntimeError as e:
            err = SearchResponse(success=False, query=search_term, data=[], count=0)
            return jsonify(err.to_dict()), 502

# caching was made with help of ai

@app.route("/ping")
def upping():
    return jsonify({"message": "pong"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)