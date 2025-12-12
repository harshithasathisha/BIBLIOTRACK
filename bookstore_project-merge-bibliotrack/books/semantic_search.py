import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Q
from .models import Book
import logging

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    def __init__(self):
        self.model = None
        self.book_embeddings = {}
        self.books_data = []
        self._load_model()
        self._precompute_embeddings()

    def _load_model(self):
        """Load the Sentence-BERT model"""
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence-BERT model loaded successfully for semantic search")
        except Exception as e:
            logger.error(f"Failed to load Sentence-BERT model: {e}")
            self.model = None

    def _precompute_embeddings(self):
        """Precompute embeddings for all books"""
        if not self.model:
            return

        try:
            books = Book.objects.all()
            self.books_data = list(books)

            if not self.books_data:
                logger.warning("No books found for semantic search")
                return

            # Create text representations for each book
            book_texts = []
            for book in self.books_data:
                text = f"{book.title} {book.author} {book.description} {book.genre}"
                book_texts.append(text)

            # Compute embeddings
            embeddings = self.model.encode(book_texts, show_progress_bar=False)
            self.book_embeddings = dict(zip([b.id for b in self.books_data], embeddings))

            logger.info(f"Precomputed embeddings for {len(self.books_data)} books")

        except Exception as e:
            logger.error(f"Error precomputing embeddings: {e}")

    def search(self, query, limit=20):
        """Perform semantic search for the given query"""
        if not self.model or not self.book_embeddings:
            # Fallback to basic text search
            return self._fallback_search(query, limit)

        try:
            # Encode the query
            query_embedding = self.model.encode([query])[0]

            # Calculate similarities
            similarities = {}
            for book_id, book_embedding in self.book_embeddings.items():
                similarity = cosine_similarity([query_embedding], [book_embedding])[0][0]
                similarities[book_id] = similarity

            # Sort by similarity and get top results
            sorted_results = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

            results = []
            for book_id, score in sorted_results[:limit]:
                book = next((b for b in self.books_data if b.id == book_id), None)
                if book:
                    results.append({
                        'book': book,
                        'score': float(score),
                        'relevance': self._get_relevance_label(score)
                    })

            return results

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return self._fallback_search(query, limit)

    def _fallback_search(self, query, limit):
        """Fallback to basic text search if semantic search fails"""
        try:
            books = Book.objects.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query) |
                Q(genre__icontains=query)
            )[:limit]

            return [{
                'book': book,
                'score': 0.5,  # Default score for fallback
                'relevance': 'text_match'
            } for book in books]

        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []

    def _get_relevance_label(self, score):
        """Get a human-readable relevance label based on similarity score"""
        if score >= 0.8:
            return 'highly_relevant'
        elif score >= 0.6:
            return 'relevant'
        elif score >= 0.4:
            return 'somewhat_relevant'
        else:
            return 'low_relevance'

    def refresh_embeddings(self):
        """Refresh embeddings when books are added/updated"""
        self._precompute_embeddings()

# Global instance
semantic_search_engine = SemanticSearchEngine()
