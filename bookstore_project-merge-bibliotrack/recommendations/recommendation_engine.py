import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from books.models import Book, Review
from .models import UserInteraction, Recommendation
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class HybridRecommendationEngine:
    def __init__(self):
        self.sentence_model = None
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}")

    def _get_content_similarity(self, target_book, all_books):
        """Calculate content-based similarity using book features"""
        if not self.sentence_model:
            return {}

        # Create text representations
        book_texts = []
        for book in all_books:
            text = f"{book.title} {book.author} {book.description} {book.genre}"
            book_texts.append(text)

        target_text = f"{target_book.title} {target_book.author} {target_book.description} {target_book.genre}"

        # Get embeddings
        try:
            embeddings = self.sentence_model.encode(book_texts + [target_text])
            target_embedding = embeddings[-1]
            book_embeddings = embeddings[:-1]

            # Calculate similarities
            similarities = cosine_similarity([target_embedding], book_embeddings)[0]
            return dict(zip([b.id for b in all_books], similarities))
        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return {}

    def _get_collaborative_filtering(self, user, all_books):
        """Calculate collaborative filtering scores"""
        # Get user's interactions
        user_interactions = UserInteraction.objects.filter(user=user)
        if not user_interactions.exists():
            return {}

        # Get similar users based on interaction patterns
        similar_users = self._find_similar_users(user)
        if not similar_users:
            return {}

        # Calculate scores based on similar users' preferences
        scores = defaultdict(float)
        user_weights = {u['user_id']: u['similarity'] for u in similar_users}

        for interaction in UserInteraction.objects.filter(user_id__in=user_weights.keys()):
            if interaction.book_id not in [i.book_id for i in user_interactions]:
                weight = user_weights[interaction.user_id] * interaction.weight
                scores[interaction.book_id] += weight

        return dict(scores)

    def _find_similar_users(self, user, top_k=10):
        """Find users with similar interaction patterns"""
        # Get all users with interactions
        all_users = User.objects.filter(
            userinteraction__isnull=False
        ).exclude(id=user.id).distinct()

        user_interactions = {i.book_id: i.weight for i in
                           UserInteraction.objects.filter(user=user)}

        similar_users = []

        for other_user in all_users[:50]:  # Limit for performance
            other_interactions = {i.book_id: i.weight for i in
                                UserInteraction.objects.filter(user=other_user)}

            # Calculate cosine similarity between interaction vectors
            common_books = set(user_interactions.keys()) & set(other_interactions.keys())

            if len(common_books) < 3:  # Need minimum overlap
                continue

            user_vector = [user_interactions[book] for book in common_books]
            other_vector = [other_interactions[book] for book in common_books]

            similarity = np.dot(user_vector, other_vector) / (
                np.linalg.norm(user_vector) * np.linalg.norm(other_vector)
            )

            if similarity > 0.1:  # Minimum similarity threshold
                similar_users.append({
                    'user_id': other_user.id,
                    'similarity': similarity
                })

        return sorted(similar_users, key=lambda x: x['similarity'], reverse=True)[:top_k]

    def _get_popularity_scores(self, all_books):
        """Calculate popularity-based scores"""
        scores = {}
        for book in all_books:
            # Combine multiple popularity metrics
            review_score = book.average_rating * book.total_ratings * 0.4
            interaction_score = UserInteraction.objects.filter(book=book).count() * 0.6
            scores[book.id] = review_score + interaction_score
        return scores

    def _get_genre_preferences(self, user):
        """Get user's genre preferences based on interactions"""
        genre_weights = defaultdict(float)

        for interaction in UserInteraction.objects.filter(user=user):
            genre_weights[interaction.book.genre] += interaction.weight

        # Normalize
        total = sum(genre_weights.values())
        if total > 0:
            genre_weights = {k: v/total for k, v in genre_weights.items()}

        return genre_weights

    def generate_recommendations(self, user, top_k=10):
        """Generate hybrid recommendations for a user"""
        # Get all books
        all_books = list(Book.objects.all())
        if not all_books:
            return []

        # Get user's existing interactions to exclude
        user_interactions = set(UserInteraction.objects.filter(user=user)
                              .values_list('book_id', flat=True))

        # Calculate different recommendation scores
        content_scores = {}
        cf_scores = self._get_collaborative_filtering(user, all_books)
        popularity_scores = self._get_popularity_scores(all_books)
        genre_preferences = self._get_genre_preferences(user)

        # Hybrid scoring
        recommendations = []

        for book in all_books:
            if book.id in user_interactions:
                continue

            # Content similarity (if user has interactions)
            content_score = 0
            if user_interactions:
                # Use most interacted book as reference
                reference_book = UserInteraction.objects.filter(user=user)\
                    .order_by('-weight').first().book
                content_similarities = self._get_content_similarity(reference_book, [book])
                content_score = content_similarities.get(book.id, 0)

            # Collaborative filtering score
            cf_score = cf_scores.get(book.id, 0)

            # Popularity score (normalized)
            pop_score = popularity_scores.get(book.id, 0)
            max_pop = max(popularity_scores.values()) if popularity_scores else 1
            normalized_pop = pop_score / max_pop if max_pop > 0 else 0

            # Genre preference score
            genre_score = genre_preferences.get(book.genre, 0.1)  # Default low preference

            # Hybrid score combination
            # Weights: Content (0.3), CF (0.4), Popularity (0.2), Genre (0.1)
            hybrid_score = (
                content_score * 0.3 +
                cf_score * 0.4 +
                normalized_pop * 0.2 +
                genre_score * 0.1
            )

            if hybrid_score > 0.1:  # Minimum threshold
                reason = self._get_recommendation_reason(
                    content_score, cf_score, normalized_pop, genre_score
                )

                recommendations.append({
                    'book': book,
                    'score': hybrid_score,
                    'reason': reason
                })

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:top_k]

    def _get_recommendation_reason(self, content_score, cf_score, pop_score, genre_score):
        """Generate human-readable recommendation reason"""
        reasons = []

        if cf_score > 0.3:
            reasons.append("Similar users liked this")
        if content_score > 0.5:
            reasons.append("Similar to books you've enjoyed")
        if genre_score > 0.3:
            reasons.append("Matches your preferred genres")
        if pop_score > 0.7:
            reasons.append("Popular among readers")

        return " • ".join(reasons) if reasons else "Recommended for you"

    def update_user_interactions(self, user, book, interaction_type):
        """Update or create user interaction"""
        weights = {
            'view': 1.0,
            'wishlist': 2.0,
            'cart': 3.0,
            'review': 4.0,
            'purchase': 5.0,
        }

        interaction, created = UserInteraction.objects.get_or_create(
            user=user,
            book=book,
            interaction_type=interaction_type,
            defaults={'weight': weights.get(interaction_type, 1.0)}
        )

        if not created:
            # Increase weight for repeated interactions
            interaction.weight = min(interaction.weight + 0.5, weights.get(interaction_type, 1.0))
            interaction.save()

    def refresh_recommendations(self, user):
        """Refresh recommendations for a user"""
        # Clear old recommendations
        Recommendation.objects.filter(user=user).delete()

        # Generate new recommendations
        recommendations = self.generate_recommendations(user)

        # Save to database
        for rec in recommendations:
            Recommendation.objects.create(
                user=user,
                book=rec['book'],
                score=rec['score'],
                reason=rec['reason']
            )

# Global instance
recommendation_engine = HybridRecommendationEngine()
