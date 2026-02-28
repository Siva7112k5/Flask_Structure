# utils/smart_search.py
"""
Smart Search Engine for Triowise
Handles fuzzy matching, typo correction, and relevance scoring
"""

import re
from difflib import SequenceMatcher
from collections import Counter
import math

class SmartSearch:
    def __init__(self, products):
        """
        Initialize with list of products
        """
        self.products = products
        self.build_index()
    
    def build_index(self):
        """
        Build search index with product keywords
        """
        self.index = []
        for product in self.products:
            # Combine all searchable fields
            text = f"{product.name} {product.category} {product.brand} {product.short_description}"
            # Convert to lowercase and split into words
            words = re.findall(r'\w+', text.lower())
            
            self.index.append({
                'product': product,
                'words': words,
                'name': product.name.lower(),
                'category': product.category.lower() if product.category else '',
                'brand': product.brand.lower() if product.brand else '',
                'description': product.short_description.lower() if product.short_description else ''
            })
    
    def calculate_word_similarity(self, word1, word2):
        """
        Calculate similarity between two words (handles typos)
        """
        if word1 == word2:
            return 1.0
        return SequenceMatcher(None, word1, word2).ratio()
    
    def search(self, query, threshold=0.3):
        """
        Main search function
        """
        query = query.lower().strip()
        if not query:
            return []
        
        # Split query into words
        query_words = re.findall(r'\w+', query)
        
        results = []
        for item in self.index:
            score = self.calculate_relevance(item, query, query_words)
            if score > threshold:
                results.append((item['product'], score))
        
        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def calculate_relevance(self, item, query, query_words):
        """
        Calculate how relevant a product is to the search query
        """
        score = 0.0
        matched_terms = set()
        
        # 1. Exact match in name (highest priority)
        if query in item['name']:
            score += 3.0
            matched_terms.add('name_exact')
        
        # 2. Word-by-word matching
        for q_word in query_words:
            # Check name words
            for p_word in item['words']:
                similarity = self.calculate_word_similarity(q_word, p_word)
                if similarity > 0.7:  # High similarity threshold
                    score += similarity * 2.0
                    matched_terms.add(f'name_{q_word}')
                    break
            
            # Check category
            if q_word in item['category']:
                score += 1.5
                matched_terms.add('category')
            
            # Check brand
            if q_word in item['brand']:
                score += 1.5
                matched_terms.add('brand')
            
            # Check description
            if q_word in item['description']:
                score += 0.5
                matched_terms.add('description')
        
        # 3. Bonus for matching multiple words
        if len(matched_terms) > 1:
            score += len(matched_terms) * 0.3
        
        # 4. Popularity bonus (higher rated products get slight boost)
        score += item['product'].rating * 0.1
        
        return score
    
    def suggest_corrections(self, query):
        """
        Suggest spelling corrections for mispelled queries
        """
        from difflib import get_close_matches
        
        # Get all unique words from product names
        all_words = set()
        for item in self.index:
            all_words.update(item['words'])
        
        query_words = re.findall(r'\w+', query.lower())
        suggestions = []
        
        for q_word in query_words:
            matches = get_close_matches(q_word, all_words, n=3, cutoff=0.7)
            if matches and matches[0] != q_word:
                suggestions.append(matches[0])
        
        if suggestions:
            corrected = ' '.join(suggestions)
            return corrected
        return None


class SearchHistory:
    """
    Track and learn from user searches
    """
    def __init__(self):
        self.popular_searches = Counter()
        self.search_results = {}  # query -> list of product IDs clicked
    
    def log_search(self, query, results_count):
        """Log a search query"""
        self.popular_searches[query.lower()] += 1
    
    def log_click(self, query, product_id):
        """Log when user clicks on a search result"""
        query = query.lower()
        if query not in self.search_results:
            self.search_results[query] = []
        self.search_results[query].append(product_id)
    
    def get_popular_searches(self, limit=10):
        """Get most popular search queries"""
        return self.popular_searches.most_common(limit)
    
    def get_related_searches(self, query, limit=5):
        """Find related searches based on user behavior"""
        query = query.lower()
        if query not in self.search_results:
            return []
        
        # Products clicked for this query
        clicked_products = set(self.search_results[query])
        
        # Find other queries that led to same products
        related = Counter()
        for other_query, products in self.search_results.items():
            if other_query == query:
                continue
            common = clicked_products.intersection(set(products))
            if common:
                related[other_query] += len(common)
        
        return [q for q, _ in related.most_common(limit)]